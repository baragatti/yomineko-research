#!/usr/bin/env python3
"""W38 — the teacher review queue, built over the EXPORT, with item ids.

Replaces `scripts/export/review_queue.py`, which the readiness audit
(`research/reports/readiness/quality_provenance_review.md`, finding G5) retired for four reasons:

  1. it read `db/corpus.sqlite`, the git-ignored regenerable index, not the committed JSON that
     CLAUDE.md names the source of truth;
  2. it was 2.5 months stale — `reports/review_queue.md` claims 11,034 items while re-running its
     own eight SQL queries against today's DB gives 23,796, and it prints "Lessons … 0" where the
     DB holds 322;
  3. it emitted COUNTS. A teacher cannot work a count. There were no ids, so no one could start,
     stop, or measure progress;
  4. nothing regenerated it, so nothing noticed it rotting.

This file fixes all four. It reads `corpus/` + `course/`, emits one row PER RECORD with its id,
level, layer, provenance, the lessons that use it, and a reason class, and it can SUBTRACT the
W06 approval ledger so the queue shrinks as a teacher works.

WHAT IS IN THE QUEUE
--------------------
Every exported record whose `needs_review` is true, across eight entities:

    sentence            corpus/sentences/bank.json          provenance.needs_review
    grammar_point       corpus/grammar/*.json               needs_review
    reading             corpus/readings/*.json              needs_review
    exam_item           corpus/exam_banks/*.json            needs_review   (removed_items.json skipped)
    lesson              course/**/lesson-*.json             needs_review
    speak_unit          course/speak/**/unit-*.json         needs_review
    speak_course        course/speak/course.json            needs_review
    vocab_disambiguation course/vocab_disambiguation_review.json  items[].needs_review

Records the export marks `needs_review: false` (the 23,882 conjugation and role exercises) are NOT
in the queue: they are re-derivable and the gate re-derives them. Layer A facts are not in the
queue either — they are auditable against their dataset source.

TARGETS: WHY A ROW IS NOT THE UNIT OF APPROVAL
---------------------------------------------
No exported entity carries per-field review flags today, so the queue rows are per record. But an
approval must be per FIELD and per LOCALE, anchored to a content hash (APP_PLAN D4) — otherwise
approving a pt-BR translation would silently bless the en anchor beside it, and re-approving after a
rewrite would be indistinguishable from never having reviewed at all. So each row carries a list of
`targets`, one per (field, locale), each with a sha256 of the exact text:

    {"field": "translation", "locale": "pt-BR", "content_hash": "<sha256 hex>", "preview": "…"}

A row leaves the queue only when EVERY one of its targets is approved. Partial approval shrinks the
row and sets `partially_approved: true`. That is what makes an approval survivable: the ledger
addresses (entity, slug, field, locale, content_hash), and a campaign that rewrites one field
invalidates exactly that field's approval and nothing else.

THE SUBTRACT JOIN (--subtract)
------------------------------
An entry in `research/derived/review_ledger.json` subtracts a target when ALL of:

    entity   — equal, or absent from the entry (an entry may be entity-agnostic)
    slug     — equal, exactly, case-sensitive
    field    — equal, or "*"/absent on the entry (a whole-record approval)
    locale   — equal, or "*"/absent on the entry (a locale-agnostic approval)
    hash     — equal, or one is a hex prefix of the other with >= 8 hex chars, so a ledger that
               stores a short hash and a queue that stores the full sha256 still join
    status   — absent, or one of APPROVING_STATUSES

and, critically:

    an entry with NO content hash NEVER subtracts.

That last rule is the whole point. D4 says approvals are content-hash anchored; an unanchored
approval cannot tell "the teacher read this text" from "the teacher read some earlier text that
lived at this address". Unanchored entries are counted and reported under `unanchored`, never
applied. An entry whose hash does not match the current text is reported under `stale` — that is an
approval a later rewrite invalidated, and it is the single most useful number in the report,
because it names exactly the work a campaign undid.

REASON CLASSES AND PRIORITY
---------------------------
Every row gets exactly one priority band, and may carry several evidence classes:

    1  layer-c-authored     pedagogy someone wrote: lessons, speak units, grammar points, reading
                            passages, exam items, the disambiguation queue
    2  generated            `ai_generated: true` — the spec-1.2 last resort, read the Japanese first
    3  repaired             a text field of this record was rewritten by a campaign under
                            `research/derived/repairs/`; the campaign name is on the row
    4  derived-unverified   the residue: Layer-B dissections of real human sentences

Inside a level the bands run 1 → 4, which is the order APP_PLAN M6 asks for: a named teacher starts
on N5, and inside N5 reads the authored pedagogy before the derived material.

Two further evidence fields ride along and cost nothing: `campaigns` (every repair table that
touched the record, including field-level tables like `sentence_register` that do not move it into
band 3) and `qa_reports` (which of the 29 sweeps under `research/reports/qa_sweep/` name this id).

OUTPUTS
-------
    research/reports/review_queue.json   machine: every row, every target, every hash
    research/reports/review_queue.md     human: totals by entity x level x reason, the subtract
                                         summary, then the N5 slice listed in full with a one-line
                                         preview per item

DB PROJECTION (report only)
---------------------------
G4: `vocab_sense` (10,592), `kanji_reading` (3,970) and `family` (396) are flagged in
`db/corpus.sqlite` and unflagged in the JSON — 14,958 flags the export drops. Those rows cannot be
queued from the export, so this script opens the DB READ-ONLY (`mode=ro`), counts them by level,
and reports what W05 exporting them would ADD. It never writes the DB. `--no-db` skips it.

USAGE
    python scripts/review_queue.py                       # rebuild both artifacts
    python scripts/review_queue.py --subtract research/derived/review_ledger.json
    python scripts/review_queue.py --check               # exit 1 if the export flags nothing
    python scripts/review_queue.py --no-db --no-write    # counts to stdout only

--check exists because a queue over nothing is a broken queue, not a finished corpus: if a schema
change or an exporter regression drops `needs_review` everywhere, this returns 1 and says so. It is
deliberately NOT registered in `scripts/validate/` — this is teacher tooling, not an invariant.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]

# --- levels -------------------------------------------------------------------------------------
# Rank drives sort order and the "N5 first" slice. Level is DATA, not structure (CLAUDE.md 1.6):
# an unknown level sorts last instead of raising.
LEVEL_RANK: dict[str, int] = {"pre-n5": 0, "n5": 1, "n4": 2, "n3": 3, "n2": 4, "n1": 5, "speak": 8}
UNKNOWN_LEVEL = "(unknown)"
N5_SLICE_LEVELS = frozenset({"n5", "pre-n5"})

# --- priority bands -----------------------------------------------------------------------------
BAND_LAYER_C = 1
BAND_GENERATED = 2
BAND_REPAIRED = 3
BAND_DERIVED = 4
BAND_NAME: dict[int, str] = {
    BAND_LAYER_C: "layer-c-authored",
    BAND_GENERATED: "generated",
    BAND_REPAIRED: "repaired",
    BAND_DERIVED: "derived-unverified",
}

# Entities whose records are authored pedagogy. `layer` is missing from most exported entities
# (readiness G3: 11 entities carry no `layer`), so where the export is silent this map supplies the
# layer the DB column holds — grammar_point.layer='C', lesson.layer='C', sentence.layer='B' — and
# the row records `layer_source: "assumed"` so nothing pretends the export said it.
ASSUMED_LAYER: dict[str, str] = {
    "sentence": "B",
    "grammar_point": "C",
    "lesson": "C",
    "vocab_disambiguation": "C",
}
PEDAGOGY_ENTITIES = frozenset(
    {"grammar_point", "reading", "exam_item", "lesson", "speak_unit", "speak_course",
     "vocab_disambiguation"}
)

APPROVING_STATUSES = frozenset({"approved", "accepted", "signed_off", "signed-off", "ok", "done"})
REJECTING_STATUSES = frozenset({"rejected", "pending", "needs_changes", "needs-changes", "open",
                                "escalated", "deferred"})

LOCALE_RE = re.compile(r"^[a-z]{2}(-[A-Za-z]{2,4})?$")
SLUG_RE = re.compile(r"\b(?:sent|gram|les|vocab|kanji|read|fam|speak):[A-Za-z0-9_.\-]+")
PREVIEW_CHARS = 110
TARGET_PREVIEW_CHARS = 60
# Hashes are computed as full sha256 and SERIALISED truncated. 24 hex = 96 bits over ~59,000
# targets: a collision is not going to happen, the artifact loses ~2.3 MB, and `hashes_join`
# accepts a prefix either way, so a ledger that stores what it read here and a ledger that
# recomputes sha256 from the export both join.
SERIALISED_HASH_CHARS = 24


# ==================================================================================================
# small helpers
# ==================================================================================================
def sha(text: str) -> str:
    """Content hash of one reviewable string. NFC first, so a locale-object that round-trips through
    a different normalisation does not read as a rewrite."""
    return hashlib.sha256(unicodedata.normalize("NFC", text).encode("utf-8")).hexdigest()


def sha_json(value: object) -> str:
    """Content hash of an aggregate target (a dissection, a form table, an exam stem+options)."""
    return sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def one_line(text: str, limit: int = PREVIEW_CHARS) -> str:
    flat = re.sub(r"\s+", " ", str(text)).strip()
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def is_locale_object(value: object) -> bool:
    return (
        isinstance(value, dict)
        and bool(value)
        and all(isinstance(k, str) and LOCALE_RE.match(k) for k in value)
    )


def common_dir(paths: Sequence[str]) -> str:
    """Deepest directory every path shares, as `a/b/`. Naming the first file's folder would claim
    all 322 lessons live in whichever topic sorts first."""
    parts = [p.split("/")[:-1] for p in paths]
    shared: list[str] = []
    for segments in zip(*parts):
        if len(set(segments)) != 1:
            break
        shared.append(segments[0])
    return "/".join(shared) + "/" if shared else "./"


def level_rank(level: str) -> int:
    return LEVEL_RANK.get(level, 9)


def level_sort_key(level: str) -> tuple[int, str]:
    """Rank first, then the name. Every level sort in this file runs over a SET, and unranked levels
    (`(unknown)`, the DB projection's synthetic `n5+n4`) all share rank 9 — so ranking alone leaves
    their order to set iteration, which varies with the interpreter's hash seed. That made the
    committed artifact churn a different column order on every run for no change in the data."""
    return (level_rank(level), level)


def level_from_slug(slug: str | None) -> str:
    """`les:n3-perspectiva-01` -> `n3`. Used where a record has no level of its own."""
    if not slug:
        return UNKNOWN_LEVEL
    m = re.search(r":(pre-n5|n[1-5])\b", slug)
    return m.group(1) if m else UNKNOWN_LEVEL


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


# ==================================================================================================
# the row model
# ==================================================================================================
@dataclass
class Target:
    """One reviewable (field, locale) pair — the unit an approval addresses."""
    field: str
    locale: str | None
    content_hash: str
    preview: str = ""
    approved: bool = False
    approved_by: str | None = None
    approved_at: str | None = None

    def to_json(self) -> dict[str, object]:
        out: dict[str, object] = {"field": self.field, "locale": self.locale,
                                  "content_hash": self.content_hash[:SERIALISED_HASH_CHARS]}
        if self.preview:
            out["preview"] = self.preview
        if self.approved:
            out["approved"] = True
            if self.approved_by:
                out["approved_by"] = self.approved_by
            if self.approved_at:
                out["approved_at"] = self.approved_at
        return out


@dataclass
class Row:
    entity: str
    id: str
    level: str
    file: str
    layer: str | None = None
    layer_source: str = "assumed"
    ai_generated: bool | None = None
    source: str | None = None
    preview: str = ""
    targets: list[Target] = dc_field(default_factory=list)
    record_hash: str = ""
    used_by: list[str] = dc_field(default_factory=list)
    used_by_levels: list[str] = dc_field(default_factory=list)
    campaigns: list[str] = dc_field(default_factory=list)
    repaired_fields: list[str] = dc_field(default_factory=list)
    qa_reports: list[str] = dc_field(default_factory=list)
    extra: dict[str, object] = dc_field(default_factory=dict)

    # filled in later
    band: int = BAND_DERIVED
    reason_classes: list[str] = dc_field(default_factory=list)

    @property
    def queue_id(self) -> str:
        return f"{self.entity}/{self.id}"

    @property
    def remaining(self) -> list[Target]:
        return [t for t in self.targets if not t.approved]

    @property
    def fully_approved(self) -> bool:
        return bool(self.targets) and all(t.approved for t in self.targets)

    def to_json(self) -> dict[str, object]:
        out: dict[str, object] = {
            "queue_id": self.queue_id,
            "entity": self.entity,
            "id": self.id,
            "level": self.level,
            "priority_band": self.band,
            "reason": BAND_NAME[self.band],
            "reason_classes": self.reason_classes,
            "layer": self.layer,
            "layer_source": self.layer_source,
            "ai_generated": self.ai_generated,
            "source": self.source,
            "file": self.file,
            "preview": self.preview,
            "record_hash": self.record_hash[:SERIALISED_HASH_CHARS],
            "used_by": self.used_by,
            "used_by_levels": self.used_by_levels,
            "targets_total": len(self.targets),
            "targets_remaining": len(self.remaining),
            "targets": [t.to_json() for t in self.targets],
        }
        if len(self.remaining) != len(self.targets):
            out["partially_approved"] = True
        if self.campaigns:
            out["campaigns"] = self.campaigns
        if self.repaired_fields:
            out["repaired_fields"] = self.repaired_fields
        if self.qa_reports:
            out["qa_reports"] = self.qa_reports
        if self.extra:
            out["notes"] = self.extra
        return out


def add_locale_targets(row: Row, field_name: str, value: object, preview_locale: str = "pt-BR") -> None:
    """A locale-object field becomes one target per locale present. pt-BR carries the preview; the
    other locales carry hash only, which halves the artifact without losing an approval address."""
    if not is_locale_object(value):
        return
    assert isinstance(value, dict)
    for locale, text in value.items():
        if not isinstance(text, str) or not text.strip():
            continue
        row.targets.append(Target(
            field=field_name,
            locale=locale,
            content_hash=sha(text),
            preview=one_line(text, TARGET_PREVIEW_CHARS) if locale == preview_locale else "",
        ))


def add_aggregate_target(row: Row, field_name: str, value: object, locale: str | None,
                         preview: str = "") -> None:
    if value in (None, [], {}, ""):
        return
    row.targets.append(Target(field=field_name, locale=locale, content_hash=sha_json(value),
                              preview=one_line(preview, TARGET_PREVIEW_CHARS) if preview else ""))


# ==================================================================================================
# course reference index — "which lesson would a teacher meet this in?"
# ==================================================================================================
@dataclass
class CourseIndex:
    uses: dict[str, set[str]] = dc_field(default_factory=lambda: collections.defaultdict(set))
    unit_level: dict[str, str] = dc_field(default_factory=dict)

    def record(self, unit_id: str, unit_level: str, refs: Iterable[object]) -> None:
        self.unit_level[unit_id] = unit_level
        for ref in refs:
            if isinstance(ref, str) and ":" in ref:
                self.uses[ref].add(unit_id)

    def for_slug(self, slug: str) -> tuple[list[str], list[str]]:
        units = sorted(self.uses.get(slug, ()))
        levels = sorted({self.unit_level.get(u, UNKNOWN_LEVEL) for u in units}, key=level_sort_key)
        return units, levels


def lesson_refs(lesson: dict[str, Any]) -> Iterator[object]:
    """Deliberately narrow. `cumulative_known_set` is excluded: it is the running union of every
    unlock up to that point, so following it would claim every N5 word is "used by" all 84 N5
    lessons and the teacher's N5 slice would stop meaning anything."""
    for unlock in lesson.get("unlocks") or ():
        if isinstance(unlock, dict):
            yield unlock.get("ref")
    for card in (lesson.get("srs") or {}).get("introduces_cards") or ():
        if isinstance(card, dict):
            yield card.get("item")
    yield from lesson.get("sentence_refs") or ()
    for exercise in lesson.get("exercises") or ():
        if isinstance(exercise, dict):
            yield from exercise.get("sentence_refs") or ()


def speak_refs(unit: dict[str, Any]) -> Iterator[object]:
    for key in ("say_now", "shadowing", "words", "patterns", "patterns_chunked", "chunk_phrases"):
        yield from unit.get(key) or ()
    for drill in unit.get("drills") or ():
        if isinstance(drill, dict):
            yield drill.get("pattern")
            yield from drill.get("examples") or ()
    for prod in unit.get("production") or ():
        if isinstance(prod, dict):
            yield prod.get("sentence")
    yield from (unit.get("fluency") or {}).get("items") or ()


def build_course_index(root: Path) -> CourseIndex:
    index = CourseIndex()
    for path in sorted(root.glob("course/**/lesson-*.json")):
        lesson = load_json(path)
        index.record(lesson.get("id", path.stem), lesson.get("level", UNKNOWN_LEVEL),
                     lesson_refs(lesson))
    for path in sorted(root.glob("course/speak/**/unit-*.json")):
        unit = load_json(path)
        index.record(unit.get("id", path.stem), "speak", speak_refs(unit))
    return index


# ==================================================================================================
# repair-campaign index — which campaign rewrote which (slug, field)
# ==================================================================================================
# Fields a campaign row can name that correspond to a reviewable target. `register`, `forms`,
# `link`/`unlink` and the token-level fields are recorded on the row but do not by themselves move a
# record into band 3, because they are not the learner-facing prose a teacher re-reads.
REPAIR_TEXT_FIELDS = frozenset({
    "translation", "translation_literal", "structure_explanation", "jp", "kana", "romaji",
    "explanation", "formation", "nuance", "label", "title", "body", "description",
})
DISSECTION_REPAIR_FIELDS = frozenset({"gloss", "role", "conjugation_note"})


@dataclass
class RepairIndex:
    by_slug: dict[str, set[str]] = dc_field(default_factory=lambda: collections.defaultdict(set))
    text_touched: dict[str, set[str]] = dc_field(default_factory=lambda: collections.defaultdict(set))
    unreadable: list[str] = dc_field(default_factory=list)
    row_counts: dict[str, int] = dc_field(default_factory=dict)

    def campaigns(self, slug: str) -> list[str]:
        return sorted(self.by_slug.get(slug, ()))

    def repaired_fields(self, slug: str) -> list[str]:
        return sorted(self.text_touched.get(slug, ()))


def build_repair_index(root: Path) -> RepairIndex:
    index = RepairIndex()
    repairs_dir = root / "research" / "derived" / "repairs"
    if not repairs_dir.is_dir():
        return index
    for path in sorted(repairs_dir.glob("*.json")):
        campaign = path.stem
        try:
            payload = load_json(path)
        except (json.JSONDecodeError, OSError):
            # A concurrent campaign may be mid-write. Skip it loudly rather than crash the queue.
            index.unreadable.append(campaign)
            continue
        rows = payload if isinstance(payload, list) else next(
            (v for v in payload.values() if isinstance(v, list)), [])
        index.row_counts[campaign] = len(rows)
        for entry in rows:
            if not isinstance(entry, dict):
                continue
            slugs = {s for s in (entry.get("slug"), entry.get("sentence")) if isinstance(s, str)}
            key = entry.get("key")
            if isinstance(key, str):
                slugs.add(key if ":" in key else f"gram:{key}")
            field_name = entry.get("field")
            for slug in slugs:
                index.by_slug[slug].add(campaign)
                if isinstance(field_name, str):
                    if field_name in REPAIR_TEXT_FIELDS:
                        index.text_touched[slug].add(field_name)
                    elif field_name in DISSECTION_REPAIR_FIELDS:
                        index.text_touched[slug].add("dissection")
    return index


def build_qa_index(root: Path) -> dict[str, set[str]]:
    """Which QA sweep reports name a given id. 29 reports, ~427 numbered findings; the ones that
    were not repaired are exactly the ones a teacher should see first inside their band."""
    out: dict[str, set[str]] = collections.defaultdict(set)
    sweep_dir = root / "research" / "reports" / "qa_sweep"
    if not sweep_dir.is_dir():
        return out
    for path in sorted(sweep_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for slug in set(SLUG_RE.findall(text)):
            out[slug].add(path.name)
    return out


# ==================================================================================================
# collectors — one per exported entity
# ==================================================================================================
def collect_sentences(root: Path) -> Iterator[Row]:
    path = root / "corpus" / "sentences" / "bank.json"
    if not path.is_file():
        return
    for rec in load_json(path):
        prov = rec.get("provenance") or {}
        if not prov.get("needs_review"):
            continue
        generated = bool(prov.get("ai_generated"))
        row = Row(
            entity="sentence",
            id=rec.get("slug", ""),
            level=rec.get("level") or UNKNOWN_LEVEL,
            file="corpus/sentences/bank.json",
            layer=ASSUMED_LAYER["sentence"],
            layer_source="assumed",
            ai_generated=generated,
            source=prov.get("jp_source"),
            preview=one_line(f"{rec.get('jp', '')} — "
                             f"{(rec.get('translation') or {}).get('pt-BR', '')}"),
        )
        row.extra = {k: prov[k] for k in
                     ("pt_source", "pt_validated_against", "translation_confidence")
                     if k in prov}
        if generated:
            # Generated Japanese is the thing spec 1.2 calls a last resort. It is a review target.
            add_aggregate_target(row, "jp", rec.get("jp"), "ja", preview=str(rec.get("jp", "")))
        for fname in ("translation", "translation_literal", "structure_explanation"):
            add_locale_targets(row, fname, rec.get(fname))
        # The per-token glosses and per-particle explanations are 50k+ localized strings across the
        # bank. They are reviewed as one dissection, per locale, so an approval still means
        # something and the artifact stays a file a person can open.
        for locale in ("pt-BR", "en"):
            payload = _dissection_payload(rec, locale)
            if payload:
                add_aggregate_target(row, "dissection", payload, locale)
        row.record_hash = sha_json(rec)
        yield row


def _dissection_payload(rec: dict[str, Any], locale: str) -> list[object]:
    payload: list[object] = []
    for tok in rec.get("tokens") or ():
        if not isinstance(tok, dict):
            continue
        part = {k: (tok.get(k) or {}).get(locale) for k in ("role", "gloss", "conjugation_note")
                if is_locale_object(tok.get(k))}
        if any(part.values()):
            payload.append({"position": tok.get("position"), **part})
    for par in rec.get("particles") or ():
        if not isinstance(par, dict):
            continue
        part = {k: (par.get(k) or {}).get(locale) for k in ("function", "explanation")
                if is_locale_object(par.get(k))}
        if any(part.values()):
            payload.append({"particle": par.get("particle"), **part})
    return payload


def collect_grammar(root: Path) -> Iterator[Row]:
    for path in sorted((root / "corpus" / "grammar").glob("*.json")):
        for rec in load_json(path):
            if not rec.get("needs_review"):
                continue
            row = Row(
                entity="grammar_point",
                id=rec.get("slug", ""),
                level=rec.get("level") or UNKNOWN_LEVEL,
                file=f"corpus/grammar/{path.name}",
                layer=rec.get("layer") or ASSUMED_LAYER["grammar_point"],
                layer_source="declared" if rec.get("layer") else "assumed",
                source=rec.get("source"),
                preview=one_line((rec.get("label") or {}).get("pt-BR", rec.get("key", ""))),
            )
            row.extra = {k: rec[k] for k in ("level_confidence", "level_agreement") if k in rec}
            for fname in ("label", "explanation", "formation", "nuance"):
                add_locale_targets(row, fname, rec.get(fname))
            for locale in ("pt-BR", "en"):
                forms = [{"form": f.get("form"), "meaning": (f.get("meaning") or {}).get(locale)}
                         for f in rec.get("forms") or () if isinstance(f, dict)]
                if any(f["meaning"] for f in forms):
                    add_aggregate_target(row, "forms", forms, locale)
            row.record_hash = sha_json(rec)
            yield row


def collect_readings(root: Path) -> Iterator[Row]:
    for path in sorted((root / "corpus" / "readings").glob("*.json")):
        for rec in load_json(path):
            if not rec.get("needs_review"):
                continue
            row = Row(
                entity="reading",
                id=rec.get("slug", ""),
                level=rec.get("level") or UNKNOWN_LEVEL,
                file=f"corpus/readings/{path.name}",
                layer=rec.get("layer"),
                layer_source="declared" if rec.get("layer") else "assumed",
                ai_generated=rec.get("ai_generated"),
                source=rec.get("source"),
                preview=one_line((rec.get("title") or {}).get("pt-BR", "")
                                 + " — " + str(rec.get("jp", ""))),
            )
            add_aggregate_target(row, "jp", rec.get("jp"), "ja", preview=str(rec.get("jp", "")))
            for fname in ("title", "translation"):
                add_locale_targets(row, fname, rec.get(fname))
            row.record_hash = sha_json(rec)
            row.extra = {"gated_to_lesson": rec["gated_to_lesson"]} if rec.get("gated_to_lesson") else {}
            yield row


EXAM_BOOKKEEPING = frozenset({"id", "level", "layer", "needs_review", "ai_generated", "source",
                              "sentence", "vocab", "vocab_id", "grammar", "grammar_id", "kanji",
                              "kanji_id", "reading_ref"})


def collect_exam_items(root: Path) -> Iterator[Row]:
    for path in sorted((root / "corpus" / "exam_banks").glob("*.json")):
        if path.name == "removed_items.json":
            continue  # the graveyard, not the queue
        payload = load_json(path)
        if not isinstance(payload, list):
            continue
        for rec in payload:
            if not rec.get("needs_review"):
                continue
            row = Row(
                entity="exam_item",
                id=rec.get("id", ""),
                level=rec.get("level") or UNKNOWN_LEVEL,
                file=f"corpus/exam_banks/{path.name}",
                layer=rec.get("layer"),
                layer_source="declared" if rec.get("layer") else "assumed",
                ai_generated=rec.get("ai_generated"),
                source=rec.get("source"),
                preview=one_line(str(rec.get("stem") or rec.get("prompt") or rec.get("script") or "")
                                 + " → " + str(rec.get("correct", ""))),
            )
            # One target for the item as a unit (stem + key + options), plus a target for any
            # locale-object the bank type happens to carry (explanations differ per section).
            add_aggregate_target(
                row, "item",
                {k: v for k, v in rec.items()
                 if k not in EXAM_BOOKKEEPING and not is_locale_object(v)},
                "ja",
                preview=str(rec.get("stem") or ""),
            )
            for key, value in rec.items():
                if is_locale_object(value):
                    add_locale_targets(row, key, value)
            row.record_hash = sha_json(rec)
            if rec.get("sentence"):
                row.extra = {"sentence": rec["sentence"]}
            yield row


def collect_lessons(root: Path) -> Iterator[Row]:
    for path in sorted(root.glob("course/**/lesson-*.json")):
        rec = load_json(path)
        if not rec.get("needs_review"):
            continue
        row = Row(
            entity="lesson",
            id=rec.get("id", path.stem),
            level=rec.get("level") or UNKNOWN_LEVEL,
            file=path.relative_to(root).as_posix(),
            layer=rec.get("layer") or ASSUMED_LAYER["lesson"],
            layer_source="declared" if rec.get("layer") else "assumed",
            source=rec.get("source"),
            preview=one_line((rec.get("title") or {}).get("pt-BR", "")),
        )
        for fname in ("title", "description"):
            add_locale_targets(row, fname, rec.get(fname))
        for locale in ("pt-BR", "en"):
            objectives = [o.get(locale) for o in rec.get("objectives") or ()
                          if isinstance(o, dict) and o.get(locale)]
            if objectives:
                add_aggregate_target(row, "objectives", objectives, locale,
                                     preview=objectives[0] if locale == "pt-BR" else "")
        body = rec.get("body")
        if isinstance(body, str) and body.strip():
            row.targets.append(Target("body", "pt-BR", sha(body), one_line(body, TARGET_PREVIEW_CHARS)))
        # Per-exercise targets: the exercise ids already exist, so a teacher can approve one drill
        # without blessing the four beside it.
        for ex in rec.get("exercises") or ():
            if not isinstance(ex, dict) or not ex.get("id"):
                continue
            payload = {k: ex.get(k) for k in ("type", "prompt", "answer", "explanation",
                                              "sentence_refs")}
            add_aggregate_target(
                row, f"exercise:{ex['id']}", payload, "pt-BR",
                preview=str((ex.get("prompt") or {}).get("pt-BR", ex.get("id", ""))),
            )
        row.record_hash = sha_json(rec)
        yield row


def collect_speak(root: Path) -> Iterator[Row]:
    for path in sorted(root.glob("course/speak/**/unit-*.json")):
        rec = load_json(path)
        if not rec.get("needs_review"):
            continue
        row = Row(
            entity="speak_unit",
            id=rec.get("id", path.stem),
            level="speak",
            file=path.relative_to(root).as_posix(),
            layer=rec.get("layer") or "C",
            layer_source="declared" if rec.get("layer") else "assumed",
            source=rec.get("source"),
            preview=one_line((rec.get("title") or {}).get("pt-BR", rec.get("id", ""))),
        )
        add_locale_targets(row, "title", rec.get("title"))
        production = [{"prompt_pt": p.get("prompt_pt"), "answer_key": p.get("answer_key")}
                      for p in rec.get("production") or () if isinstance(p, dict)]
        if production:
            add_aggregate_target(row, "production", production, "pt-BR",
                                 preview=str(production[0].get("prompt_pt") or ""))
        fluency_prompt = (rec.get("fluency") or {}).get("prompt_pt")
        if isinstance(fluency_prompt, str) and fluency_prompt.strip():
            row.targets.append(Target("fluency", "pt-BR", sha(fluency_prompt),
                                      one_line(fluency_prompt, TARGET_PREVIEW_CHARS)))
        row.record_hash = sha_json(rec)
        row.extra = {"stage": rec.get("stage")} if rec.get("stage") else {}
        yield row

    course_path = root / "course" / "speak" / "course.json"
    if course_path.is_file():
        rec = load_json(course_path)
        if rec.get("needs_review"):
            row = Row(
                entity="speak_course",
                id=rec.get("id", "speak:course"),
                level="speak",
                file="course/speak/course.json",
                layer=rec.get("layer") or "C",
                layer_source="declared" if rec.get("layer") else "assumed",
                preview=one_line((rec.get("title") or {}).get("pt-BR", "speak course")),
            )
            for key, value in rec.items():
                if is_locale_object(value):
                    add_locale_targets(row, key, value)
            row.record_hash = sha_json(rec)
            yield row


def collect_vocab_disambiguation(root: Path) -> Iterator[Row]:
    path = root / "course" / "vocab_disambiguation_review.json"
    if not path.is_file():
        return
    payload = load_json(path)
    items = payload.get("items") if isinstance(payload, dict) else payload
    for i, rec in enumerate(items or ()):
        if not rec.get("needs_review"):
            continue
        lesson = rec.get("lesson")
        row = Row(
            entity="vocab_disambiguation",
            id=f"disamb:{rec.get('chosen', i)}@{lesson or i}",
            level=level_from_slug(lesson),
            file="course/vocab_disambiguation_review.json",
            layer=ASSUMED_LAYER["vocab_disambiguation"],
            layer_source="assumed",
            source=rec.get("how"),
            preview=one_line(f"{rec.get('headword', '')} → {rec.get('chosen', '')} "
                             f"({rec.get('how', '')})"),
        )
        add_aggregate_target(row, "placement", rec, None,
                             preview=str(rec.get("evidence", "")))
        row.record_hash = sha_json(rec)
        row.extra = {"lesson": lesson, "chosen": rec.get("chosen")}
        yield row


COLLECTORS = (collect_sentences, collect_grammar, collect_readings, collect_exam_items,
              collect_lessons, collect_speak, collect_vocab_disambiguation)


# ==================================================================================================
# enrichment: lessons that use it, campaigns that touched it, priority band
# ==================================================================================================
def enrich(rows: list[Row], course: CourseIndex, repairs: RepairIndex,
           qa: dict[str, set[str]]) -> None:
    for row in rows:
        if row.entity in ("lesson", "speak_unit", "speak_course"):
            row.used_by = [row.id]
            row.used_by_levels = [row.level]
        else:
            row.used_by, row.used_by_levels = course.for_slug(row.id)
            gated = row.extra.get("gated_to_lesson") or row.extra.get("lesson")
            if isinstance(gated, str) and gated not in row.used_by:
                row.used_by = sorted({*row.used_by, gated})
                row.used_by_levels = sorted(
                    {*row.used_by_levels, course.unit_level.get(gated, level_from_slug(gated))},
                    key=level_sort_key)

        row.campaigns = repairs.campaigns(row.id)
        row.repaired_fields = repairs.repaired_fields(row.id)
        row.qa_reports = sorted(qa.get(row.id, ()))

        classes: list[str] = []
        if (row.layer or "").upper() == "C" or row.entity in PEDAGOGY_ENTITIES:
            classes.append(BAND_NAME[BAND_LAYER_C])
        if row.ai_generated:
            classes.append(BAND_NAME[BAND_GENERATED])
        if row.repaired_fields:
            classes.append(BAND_NAME[BAND_REPAIRED])
        if row.qa_reports:
            classes.append("qa-flagged")
        if BAND_NAME[BAND_LAYER_C] in classes:
            row.band = BAND_LAYER_C
        elif BAND_NAME[BAND_GENERATED] in classes:
            row.band = BAND_GENERATED
        elif BAND_NAME[BAND_REPAIRED] in classes:
            row.band = BAND_REPAIRED
        else:
            # `qa-flagged` is evidence, not a band: a QA sweep naming a record says a human already
            # looked, not that the record is authored pedagogy. Such a row still lands in the
            # residue, and the residue's name has to appear in its class list or the two tables in
            # the report would not add up.
            row.band = BAND_DERIVED
            classes.insert(0, BAND_NAME[BAND_DERIVED])
        row.reason_classes = classes


def sort_key(row: Row) -> tuple[int, int, str, str]:
    return (level_rank(row.level), row.band, row.entity, row.id)


def in_n5_slice(row: Row) -> bool:
    """The slice the named teacher of APP_PLAN M6 starts on: everything graded N5 (or pre-N5), plus
    anything an N5/pre-N5 lesson puts in front of a learner regardless of its own grade — a bank
    sentence graded n3 that an N5 lesson displays is N5 work."""
    return (row.level in N5_SLICE_LEVELS
            or any(lv in N5_SLICE_LEVELS for lv in row.used_by_levels))


# ==================================================================================================
# the subtract join
# ==================================================================================================
@dataclass
class SubtractReport:
    path: str
    present: bool = False
    entries: int = 0
    applied: int = 0
    rows_cleared: int = 0
    rows_partial: int = 0
    unanchored: int = 0
    stale: int = 0
    unmatched: int = 0
    stale_examples: list[str] = dc_field(default_factory=list)
    note: str = ""


def _entry_get(entry: dict[str, Any], *names: str) -> object:
    for name in names:
        if name in entry and entry[name] not in (None, ""):
            return entry[name]
    return None


def hashes_join(queue_hash: str, ledger_hash: str) -> bool:
    """Equal, or one a hex prefix of the other with at least 8 hex chars — so a ledger that stores a
    12-char short hash still joins a queue that stores the full sha256, and neither side has to
    guess the other's truncation. Anything shorter than 8 is refused: it would be a coincidence."""
    a, b = queue_hash.lower(), str(ledger_hash).lower()
    if ":" in b:
        b = b.rsplit(":", 1)[-1]  # tolerate "sha256:<hex>"
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) < len(b) else (b, a)
    return len(shorter) >= 8 and longer.startswith(shorter)


def apply_subtract(rows: list[Row], ledger_path: Path, root: Path) -> SubtractReport:
    try:
        shown = ledger_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        shown = ledger_path.as_posix()
    report = SubtractReport(path=shown)
    if not ledger_path.is_file():
        report.note = (f"No ledger at `{shown}` — nothing subtracted. W06 has not landed it yet, "
                       "so every row below is unapproved by construction.")
        return report
    report.present = True
    try:
        payload = load_json(ledger_path)
    except (json.JSONDecodeError, OSError) as exc:
        report.note = f"ledger at `{report.path}` could not be read ({exc}); nothing subtracted."
        return report

    entries: Sequence[Any]
    if isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = next((v for k, v in payload.items()
                        if k in ("entries", "approvals", "records", "items")
                        and isinstance(v, list)), [])
    else:
        entries = []
    report.entries = len(entries)

    # index by slug so the join is O(rows + entries), not O(rows x entries)
    by_slug: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        status = _entry_get(entry, "review_status", "status", "verdict")
        if isinstance(status, str) and status.strip().lower() in REJECTING_STATUSES:
            continue
        if isinstance(status, str) and status.strip().lower() not in APPROVING_STATUSES:
            continue  # unknown verdict: refuse to guess it means yes
        slug = _entry_get(entry, "slug", "id", "record_id", "record")
        if not isinstance(slug, str):
            continue
        if _entry_get(entry, "content_hash", "hash", "sha256") is None:
            report.unanchored += 1
            continue
        by_slug[slug].append(entry)

    for row in rows:
        candidates = by_slug.get(row.id)
        if not candidates:
            continue
        matched_any = False
        for target in row.targets:
            # An entry that addresses this target but whose anchor no longer joins is STALE: a
            # rewrite happened after the approval. Collected, not counted, until the target is
            # known to have no valid approval at all — otherwise one bad entry would report a
            # target as stale that a second, current entry legitimately approves.
            stale_anchor: str | None = None
            for entry in candidates:
                ent_entity = _entry_get(entry, "entity", "entity_type")
                if isinstance(ent_entity, str) and ent_entity != row.entity:
                    continue
                ent_field = _entry_get(entry, "field")
                if isinstance(ent_field, str) and ent_field not in ("*", target.field):
                    continue
                ent_locale = _entry_get(entry, "locale", "lang")
                if isinstance(ent_locale, str) and ent_locale not in ("*", str(target.locale)):
                    continue
                ledger_hash = str(_entry_get(entry, "content_hash", "hash", "sha256"))
                if ent_field in (None, "*") and hashes_join(row.record_hash, ledger_hash):
                    pass  # whole-record approval anchored to the record hash
                elif not hashes_join(target.content_hash, ledger_hash):
                    stale_anchor = stale_anchor or ledger_hash
                    continue
                target.approved = True
                by = _entry_get(entry, "reviewed_by", "approved_by", "reviewer")
                at = _entry_get(entry, "approved_at", "reviewed_at", "at")
                target.approved_by = by if isinstance(by, str) else None
                target.approved_at = at if isinstance(at, str) else None
                report.applied += 1
                matched_any = True
                break
            if not target.approved and stale_anchor:
                report.stale += 1
                if len(report.stale_examples) < 12:
                    report.stale_examples.append(
                        f"`{row.queue_id}` · {target.field} [{target.locale}] — approval anchored to "
                        f"`{stale_anchor[:12]}`, text now hashes `{target.content_hash[:12]}`")
        if not matched_any:
            report.unmatched += 1

    report.rows_cleared = sum(1 for r in rows if r.fully_approved)
    report.rows_partial = sum(1 for r in rows
                              if not r.fully_approved and len(r.remaining) != len(r.targets))
    return report


# ==================================================================================================
# DB projection — READ ONLY, report only (G4 / W05)
# ==================================================================================================
DB_PROJECTIONS: tuple[tuple[str, str, str], ...] = (
    ("vocab_sense", "corpus/vocab/*.json",
     "SELECT COALESCE(v.level,'(unknown)') AS lvl, count(*) FROM vocab_sense s "
     "JOIN vocab v ON v.id = s.vocab_id WHERE s.needs_review = 1 GROUP BY 1"),
    ("kanji_reading", "corpus/kanji/*.json",
     "SELECT COALESCE(k.level,'(unknown)') AS lvl, count(*) FROM kanji_reading r "
     "JOIN kanji k ON k.id = r.kanji_id WHERE r.needs_review = 1 GROUP BY 1"),
    ("family", "corpus/families/families.json",
     "SELECT 'n5+n4' AS lvl, count(*) FROM family WHERE needs_review = 1"),
)
LEGACY_QUERIES: tuple[tuple[str, str], ...] = (
    ("AI-generated sentences", "SELECT count(*) FROM sentence WHERE ai_generated=1 AND needs_review=1"),
    ("Grammar explanations", "SELECT count(*) FROM grammar_point WHERE needs_review=1"),
    ("Lessons", "SELECT count(*) FROM lesson WHERE needs_review=1"),
    ("Families", "SELECT count(*) FROM family WHERE needs_review=1"),
    ("Sentence dissections", "SELECT count(*) FROM sentence WHERE ai_generated=0 AND needs_review=1"),
    ("Vocab senses", "SELECT count(*) FROM vocab_sense WHERE needs_review=1"),
    ("Kanji pt-BR meanings",
     "SELECT count(*) FROM localized_text WHERE entity_type='kanji' AND field='meanings'"),
    ("Per-reading tier seeds", "SELECT count(*) FROM kanji_reading WHERE needs_review=1"),
)


@dataclass
class DbProjection:
    available: bool = False
    note: str = ""
    per_table: dict[str, dict[str, int]] = dc_field(default_factory=dict)
    lands_in: dict[str, str] = dc_field(default_factory=dict)
    legacy: list[tuple[str, int]] = dc_field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(sum(v.values()) for v in self.per_table.values())

    @property
    def legacy_total(self) -> int:
        return sum(n for _, n in self.legacy)


def project_db(db_path: Path) -> DbProjection:
    """Counts only. Opened `mode=ro`: this script must never write the working index."""
    proj = DbProjection()
    if not db_path.is_file():
        proj.note = f"`{db_path.as_posix()}` is absent (it is git-ignored and rebuildable)."
        return proj
    uri = "file:" + db_path.as_posix() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        proj.note = f"could not open the index read-only: {exc}"
        return proj
    try:
        for table, lands_in, query in DB_PROJECTIONS:
            proj.per_table[table] = {str(lvl): int(n) for lvl, n in conn.execute(query)}
            proj.lands_in[table] = lands_in
        proj.legacy = [(label, int(conn.execute(q).fetchone()[0])) for label, q in LEGACY_QUERIES]
        proj.available = True
    except sqlite3.Error as exc:
        proj.note = f"the index is present but did not answer: {exc}"
    finally:
        conn.close()
    return proj


# ==================================================================================================
# rendering
# ==================================================================================================
def render_markdown(rows: list[Row], subtract: SubtractReport, proj: DbProjection,
                    repairs: RepairIndex, generated_at: str) -> str:
    open_rows = [r for r in rows if not r.fully_approved]
    n5 = [r for r in open_rows if in_n5_slice(r)]
    open_targets = sum(len(r.remaining) for r in open_rows)

    out: list[str] = []
    add = out.append
    add("# Teacher review queue")
    add("")
    add(f"_Generated by `scripts/review_queue.py` over the committed export "
        f"(`corpus/` + `course/`) on {generated_at}. Regenerate it after any campaign; it is "
        f"derived, never hand-edited._")
    add("")
    add(f"**{len(open_rows):,} records await review**, carrying **{open_targets:,} reviewable "
        f"(field, locale) targets**. Every row below has an id. An approval addresses a target, not "
        f"a row: a record leaves this queue when all of its targets are approved.")
    add("")

    # --- the honest numbers -----------------------------------------------------------------
    add("## What this replaces, and why the totals moved")
    add("")
    add("| figure | value | what it actually counted |")
    add("|---|---:|---|")
    add("| `reports/review_queue.md`, as shipped 2026-06-15 | 11,034 | eight SQL counts against "
        "`db/corpus.sqlite`, frozen 2.5 months ago |")
    if proj.available:
        add(f"| the same eight queries, re-run against today's index | {proj.legacy_total:,} | the "
            "same counts, no longer stale — and still counts, with no ids |")
    else:
        add("| the same eight queries, re-run against today's index | 23,796 | recorded by the "
            "readiness audit; the index was not readable on this run |")
    add(f"| **this queue, over the export** | **{len(open_rows):,}** | records that actually carry "
        "`needs_review: true` in the committed JSON, each with an id |")
    add("")
    add("They are not three answers to one question — each counts a different thing.")
    add("")
    add("- The 11,034 is simply out of date: it prints `Lessons … 0` where the course now holds "
        "322, and `Grammar … 364` where the registry holds 496.")
    if proj.available:
        legacy_map = dict(proj.legacy)
        add(f"- The re-run {proj.legacy_total:,} counts rows in the working index, including "
            f"{legacy_map.get('Vocab senses', 0):,} vocab senses, "
            f"{legacy_map.get('Per-reading tier seeds', 0):,} kanji readings and "
            f"{legacy_map.get('Families', 0):,} families **that the exporter drops** — so most of "
            "it addresses records a teacher cannot open in the shipped artifact. Its "
            "`Kanji pt-BR meanings` query is also mis-written: it counts every `localized_text` "
            "row for kanji meanings, flagged or not.")
    add(f"- This queue counts what the source of truth says. {len(open_rows):,} records, "
        "reachable, addressable, and reviewable today.")
    add("")

    # --- what W05 would add ------------------------------------------------------------------
    add("### What W05 will add to this queue")
    add("")
    if proj.available:
        add(f"Readiness finding **G4**: `{proj.total:,}` review flags live only in "
            "`db/corpus.sqlite` and are dropped at export. Counted read-only from the index, they "
            "would enter this queue as:")
        add("")
        levels = sorted({lvl for t in proj.per_table.values() for lvl in t}, key=level_sort_key)
        add("| table | lands in | " + " | ".join(f"`{lvl}`" for lvl in levels) + " | total |")
        add("|---|---|" + "---:|" * (len(levels) + 1))
        for table, counts in proj.per_table.items():
            cells = " | ".join(f"{counts.get(lvl, 0):,}" for lvl in levels)
            add(f"| `{table}` | `{proj.lands_in[table]}` | {cells} | **{sum(counts.values()):,}** |")
        add("| **total** | | " + " | ".join(
            f"**{sum(t.get(lvl, 0) for t in proj.per_table.values()):,}**" for lvl in levels)
            + f" | **{proj.total:,}** |")
        add("")
        add(f"That is roughly **{proj.total / max(len(open_rows), 1):.1f}x the current queue**. "
            "The pt-BR gloss on every vocab sense and the note on every kanji reading are the "
            "largest unreviewed surface in the corpus, and no queue can see them until the "
            "exporter emits the flag.")
    else:
        add(f"Not computed: {proj.note} The readiness audit recorded 14,958 flags "
            "(`vocab_sense` 10,592, `kanji_reading` 3,970, `family` 396) held only in the index.")
    add("")

    # --- totals -------------------------------------------------------------------------------
    add("## Totals")
    add("")
    add("### By entity")
    add("")
    add("| entity | records | targets | layer | file |")
    add("|---|---:|---:|:---:|---|")
    by_entity: dict[str, list[Row]] = collections.defaultdict(list)
    for row in open_rows:
        by_entity[row.entity].append(row)
    for entity in sorted(by_entity, key=lambda e: -len(by_entity[e])):
        group = by_entity[entity]
        layers = sorted({str(r.layer) for r in group})
        files = sorted({r.file for r in group})
        shown = f"`{files[0]}`" if len(files) == 1 else (
            f"{len(files):,} files under `{common_dir(files)}`")
        add(f"| `{entity}` | {len(group):,} | {sum(len(r.remaining) for r in group):,} | "
            f"{'/'.join(layers)} | {shown} |")
    add(f"| **total** | **{len(open_rows):,}** | **{open_targets:,}** | | |")
    add("")

    add("### By level x reason")
    add("")
    bands = [BAND_LAYER_C, BAND_GENERATED, BAND_REPAIRED, BAND_DERIVED]
    add("| level | " + " | ".join(BAND_NAME[b] for b in bands) + " | total |")
    add("|---|" + "---:|" * (len(bands) + 1))
    grid: dict[tuple[str, int], int] = collections.Counter()
    for row in open_rows:
        grid[(row.level, row.band)] += 1
    for level in sorted({r.level for r in open_rows}, key=level_sort_key):
        cells = [grid.get((level, b), 0) for b in bands]
        marker = " **(teacher starts here)**" if level == "n5" else ""
        add(f"| `{level}`{marker} | " + " | ".join(f"{c:,}" for c in cells)
            + f" | **{sum(cells):,}** |")
    totals = [sum(grid.get((lv, b), 0) for lv in {r.level for r in open_rows}) for b in bands]
    add("| **total** | " + " | ".join(f"**{t:,}**" for t in totals)
        + f" | **{sum(totals):,}** |")
    add("")
    add("Read the bands left to right inside a level: authored pedagogy first (a wrong explanation "
        "mis-teaches every learner who reaches that lesson), then generated Japanese (spec 1.2's "
        "last resort, where the risk is the Japanese itself), then fields a repair campaign "
        "rewrote (a second pair of eyes on an automated edit), then the Layer-B dissections of real "
        "human sentences, which are machine-validated against Layer A and are the safest thing here.")
    add("")

    # --- tagging coverage ---------------------------------------------------------------------
    add("### Reason-class coverage")
    add("")
    class_counts: dict[str, int] = collections.Counter()
    for row in open_rows:
        for cls in row.reason_classes:
            class_counts[cls] += 1
    specific = sum(1 for r in open_rows
                   if any(c != BAND_NAME[BAND_DERIVED] for c in r.reason_classes))
    add(f"Every one of the {len(open_rows):,} rows carries at least one class. "
        f"**{specific:,}** ({specific / max(len(open_rows), 1):.0%}) carry a class stronger than the "
        f"`derived-unverified` default — that is, the queue can say *why* the record is here, not "
        f"just that a flag is set.")
    add("")
    add("| class | records | evidence it comes from |")
    add("|---|---:|---|")
    evidence = {
        BAND_NAME[BAND_LAYER_C]: "declared `layer: C`, or an entity that is authored pedagogy by construction",
        BAND_NAME[BAND_GENERATED]: "`ai_generated: true` in the export",
        BAND_NAME[BAND_REPAIRED]: "a learner-facing text field named in a table under `research/derived/repairs/`",
        "qa-flagged": "the record's id appears in a sweep under `research/reports/qa_sweep/`",
        BAND_NAME[BAND_DERIVED]: "no stronger signal: a Layer-B dissection of a real human sentence",
    }
    for cls, n in sorted(class_counts.items(), key=lambda kv: -kv[1]):
        add(f"| `{cls}` | {n:,} | {evidence.get(cls, '')} |")
    add("")
    if repairs.row_counts:
        add("Campaign tables read (a record may be touched by several):")
        add("")
        add("| campaign | rows | records in this queue |")
        add("|---|---:|---:|")
        camp_hits: dict[str, int] = collections.Counter()
        for row in open_rows:
            for camp in row.campaigns:
                camp_hits[camp] += 1
        for camp in sorted(repairs.row_counts):
            add(f"| `{camp}` | {repairs.row_counts[camp]:,} | {camp_hits.get(camp, 0):,} |")
        add("")
        add("A campaign appearing here does not by itself raise a record's band: "
            "`sentence_register` writes a mechanical enum on all 5,889 sentences and is recorded as "
            "provenance, not as prose a teacher must re-read. Only a rewritten learner-facing text "
            "field moves a record into `repaired`.")
        add("")
    if repairs.unreadable:
        add(f"> Campaign tables that could not be parsed on this run and were skipped: "
            f"{', '.join('`' + c + '`' for c in repairs.unreadable)}.")
        add("")

    # --- subtraction --------------------------------------------------------------------------
    add("## Approvals subtracted")
    add("")
    if not subtract.present:
        add(f"**None.** {subtract.note}")
    else:
        add(f"Ledger: `{subtract.path}` — {subtract.entries:,} entries read, "
            f"{subtract.applied:,} targets subtracted, {subtract.rows_cleared:,} records left the "
            f"queue entirely, {subtract.rows_partial:,} are partly approved and still listed.")
        add("")
        add("| outcome | entries | meaning |")
        add("|---|---:|---|")
        add(f"| applied | {subtract.applied:,} | hash matched the live text; the target is approved |")
        add(f"| stale | {subtract.stale:,} | targets whose only matching approval is anchored to "
            "text that has since been rewritten — the approval does **not** transfer |")
        add(f"| unanchored | {subtract.unanchored:,} | no content hash on the entry; refused, "
            "because an unanchored approval cannot be distinguished from an approval of earlier text |")
        if subtract.stale_examples:
            add("")
            add("Approvals a later rewrite invalidated (first few):")
            add("")
            for line in subtract.stale_examples:
                add(f"- {line}")
    add("")
    add("**Join.** A ledger entry subtracts a target when the entity matches (or the entry names "
        "none), the slug matches exactly, the field matches (or the entry says `*`), the locale "
        "matches (or the entry says `*`), the status is an approving one, **and the content hash "
        "joins** — equal, or one a hex prefix of the other with at least 8 hex characters, so a "
        "short hash and a full sha256 still meet. An entry with no hash never subtracts. That is "
        "the whole guard APP_PLAN D4 asks for: four campaigns rewrote candidate text this session, "
        "and every approval anchored to the pre-rewrite text must reappear as work.")
    add("")

    # --- the N5 slice -------------------------------------------------------------------------
    add(f"## The N5 slice — {len(n5):,} records, listed in full")
    add("")
    add("APP_PLAN M6 puts a named teacher on N5 while campaigns run on N3, so this is the only "
        "slice listed item by item. It is every record graded `n5` or `pre-n5`, **plus** anything "
        "an N5/pre-N5 lesson puts in front of a learner regardless of its own grade — a bank "
        "sentence graded `n3` that an N5 lesson displays is N5 work. Rows run in review order: "
        "authored pedagogy, then generated, then repaired, then derived.")
    add("")
    n5_by_band: dict[int, list[Row]] = collections.defaultdict(list)
    for row in n5:
        n5_by_band[row.band].append(row)
    for band in bands:
        group = sorted(n5_by_band.get(band, []), key=sort_key)
        if not group:
            continue
        add(f"### {band}. {BAND_NAME[band]} — {len(group):,} records")
        add("")
        add("| id | entity | level | targets | used by | preview |")
        add("|---|---|:---:|---:|---|---|")
        for row in group:
            used = ", ".join(f"`{u}`" for u in row.used_by[:2])
            if len(row.used_by) > 2:
                used += f" +{len(row.used_by) - 2}"
            flags = []
            if row.ai_generated:
                flags.append("AI")
            if row.repaired_fields:
                flags.append("repaired:" + ",".join(row.repaired_fields))
            if row.qa_reports:
                flags.append(f"QA×{len(row.qa_reports)}")
            suffix = f" _({'; '.join(flags)})_" if flags else ""
            add(f"| `{row.id}` | {row.entity} | {row.level} | {len(row.remaining)} | "
                f"{used or '—'} | {row.preview}{suffix} |")
        add("")

    add("---")
    add("")
    add("Machine-readable companion, with every target and every hash: "
        "`research/reports/review_queue.json`.")
    return "\n".join(out) + "\n"


def build_json(rows: list[Row], subtract: SubtractReport, proj: DbProjection,
               repairs: RepairIndex, generated_at: str) -> dict[str, object]:
    open_rows = [r for r in rows if not r.fully_approved]
    grid: dict[str, dict[str, int]] = collections.defaultdict(lambda: collections.Counter())
    for row in open_rows:
        grid[row.level][BAND_NAME[row.band]] += 1
    return {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "generated_by": "scripts/review_queue.py",
        "built_over": ["corpus/", "course/"],
        "totals": {
            "records_flagged": len(rows),
            "records_open": len(open_rows),
            "targets_open": sum(len(r.remaining) for r in open_rows),
            "by_entity": dict(collections.Counter(r.entity for r in open_rows)),
            "by_level": dict(collections.Counter(r.level for r in open_rows)),
            "by_level_and_reason": {k: dict(v) for k, v in grid.items()},
            "n5_slice": sum(1 for r in open_rows if in_n5_slice(r)),
        },
        "subtract": {
            "ledger": subtract.path,
            "present": subtract.present,
            "note": subtract.note,
            "entries": subtract.entries,
            "targets_subtracted": subtract.applied,
            "records_cleared": subtract.rows_cleared,
            "records_partial": subtract.rows_partial,
            "stale_targets": subtract.stale,
            "unanchored_approvals": subtract.unanchored,
            "records_with_entries_but_no_match": subtract.unmatched,
            "join": ("entity (or unset) AND slug AND field (or '*') AND locale (or '*') AND an "
                     "approving status AND a joining content hash; an entry with no hash never "
                     "subtracts"),
        },
        "db_projection": {
            "available": proj.available,
            "note": proj.note,
            "flags_held_only_in_db": proj.total,
            "per_table": proj.per_table,
            "lands_in": proj.lands_in,
            "legacy_eight_queries_today": dict(proj.legacy),
            "legacy_total_today": proj.legacy_total,
            "shipped_2026_06_15_total": 11034,
        },
        "campaign_tables": repairs.row_counts,
        "campaign_tables_unreadable": repairs.unreadable,
        "items": [r.to_json() for r in sorted(open_rows, key=sort_key)],
    }


def dump_queue_json(payload: dict[str, object]) -> str:
    """Envelope indented for reading; one item per LINE. 8,328 rows regenerated after every campaign
    would otherwise churn a fully-indented multi-megabyte blob on every commit — this way a changed
    record is one changed line in the diff."""
    items = list(payload["items"])  # type: ignore[arg-type]
    envelope = {k: v for k, v in payload.items() if k != "items"}
    head = json.dumps(envelope, ensure_ascii=False, indent=1)
    assert head.endswith("\n}"), "unexpected json.dumps envelope shape"
    body = ",\n".join(" " + json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                      for item in items)
    return f'{head[:-2]},\n "items": [\n{body}\n ]\n}}\n'


# ==================================================================================================
# main
# ==================================================================================================
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--subtract", type=Path, default=None,
                        help="approval ledger to subtract "
                             "(default: research/derived/review_ledger.json, the W06 path)")
    parser.add_argument("--db", type=Path, default=None,
                        help="working index to project G4's unexported flags from, read-only "
                             "(default: db/corpus.sqlite)")
    parser.add_argument("--no-db", action="store_true", help="skip the read-only DB projection")
    parser.add_argument("--no-write", action="store_true", help="compute and print, write nothing")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the export flags nothing for review")
    args = parser.parse_args(argv)

    root: Path = args.root
    ledger = args.subtract or (root / "research" / "derived" / "review_ledger.json")
    db_path = args.db or (root / "db" / "corpus.sqlite")

    rows: list[Row] = []
    for collector in COLLECTORS:
        rows.extend(collector(root))

    if args.check and not rows:
        print("FAIL: the export carries zero needs_review flags. A queue over nothing is a broken "
              "queue — check the exporter, not the corpus.")
        return 1

    course = build_course_index(root)
    repairs = build_repair_index(root)
    qa = build_qa_index(root)
    enrich(rows, course, repairs, qa)

    subtract = apply_subtract(rows, ledger, root)
    proj = DbProjection(note="skipped (--no-db)") if args.no_db else project_db(db_path)

    generated_at = datetime.date.today().isoformat()
    open_rows = [r for r in rows if not r.fully_approved]

    if not args.no_write:
        reports = root / "research" / "reports"
        reports.mkdir(parents=True, exist_ok=True)
        (reports / "review_queue.json").write_text(
            dump_queue_json(build_json(rows, subtract, proj, repairs, generated_at)),
            encoding="utf-8")
        (reports / "review_queue.md").write_text(
            render_markdown(rows, subtract, proj, repairs, generated_at), encoding="utf-8")

    n5 = sum(1 for r in open_rows if in_n5_slice(r))
    print(f"review queue: {len(open_rows):,} records open, "
          f"{sum(len(r.remaining) for r in open_rows):,} targets, N5 slice {n5:,}")
    print(f"  by entity: " + ", ".join(
        f"{k} {v:,}" for k, v in sorted(collections.Counter(r.entity for r in open_rows).items())))
    if subtract.present:
        print(f"  subtracted {subtract.applied:,} targets from {ledger.as_posix()} "
              f"({subtract.stale:,} stale, {subtract.unanchored:,} unanchored)")
    else:
        print(f"  no ledger at {ledger.as_posix()}; nothing subtracted")
    if proj.available:
        print(f"  W05 would add {proj.total:,} DB-only flags "
              f"(legacy eight queries today: {proj.legacy_total:,}; shipped 2026-06-15: 11,034)")
    if not args.no_write:
        print("  wrote research/reports/review_queue.json + review_queue.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
