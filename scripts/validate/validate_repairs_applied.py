#!/usr/bin/env python3
"""Hard gate: every tracked repair table is REPLAYED against the committed export.

WHY THIS EXISTS
---------------
`research/reports/readiness/quality_provenance_review.md` finding **G7**: *"no gate replays the
repair tables against the export — 16 grammar `form_meanings` repairs silently no-oped and only the
audit noticed."* Seven campaigns wrote 1,499 rows of `old`/`new`/`why` under
`research/derived/repairs/` (the level-evidence table spells the three `old_agreement` /
`new_agreement` / `reason`), every applier is DB-only, and the exporter republishes afterwards.
Between the apply script's "repaired N fields" line and the JSON a learner is served there was no
check at all: a row could match nothing, be shadowed by a Layer-A column, be reverted by a later
campaign, or address a field the exporter does not project — and the suite stayed green while the
campaign ledger claimed the defect was fixed.

This validator closes that gap from the other end. It never reads `db/corpus.sqlite`; it reads the
committed export, walks every row of every tracked table, and asserts the row's `new` value is
what the export actually carries at the address the row names.

WHAT IT CHECKS, TABLE BY TABLE
------------------------------
The eight tables are REGISTERED below with the addressing their applier uses (learned from
`scripts/apply_*.py`). A `.json` file appearing in `research/derived/repairs/` that is not
registered here is itself a FAILURE — a new campaign joins this gate the day it lands, not the day
someone remembers. (That rule is what caught W10's `level_evidence_repairs.json`: the campaign had
applied and exported, every other gate was green, and this one refused the run until the table was
registered with an addressing of its own.)

  * `sentence_text_repairs.json`      {slug, field, locale}      sentence[field][locale] == new
  * `jargon_pass2_repairs.json`       {slug, field, locale}      sentence[field][locale] == new
  * `translation_defect_repairs.json` {entity, slug, field, locale, token_position?}
        entity `sentence` -> sentence[field][locale] == new
        entity `token`    -> some token at `token_position` has [field][locale] == new
        (position is NOT unique — Sudachi's C-mode compound shares it with its A-mode parts, which
        is exactly why `apply_translation_defect_repairs.py` matches across all tokens there)
  * `translation_followups.json`      {store, slug, field, locale?}
        store `localized_text` -> sentence[field][locale] == new
        store `column`         -> sentence[field] == new           (kana / romaji, scalars)
  * `grammar_record_repairs.json`     {key, action}
        `text`   -> grammar[field][locale] carries new. 28 of the campaign's findings quote a
                    distinguishing SPAN rather than a whole field, and `resolve()` in the applier
                    lands those with `current.replace(old, new)`, so the predicate here is
                    CONTAINMENT, matching the applier's own semantics. The mode (exact / span) is
                    reported per failure so a substring pass is never mistaken for an exact one.
                    field `form_meanings` is a JSON map {form: meaning} -> see below.
        `forms`  -> [f["form"] for f in grammar["forms"]] == new (parsed)
        `unlink` -> the grammar key is ABSENT from the sentence's `grammar` list
  * `grammar_followups.json`          {action}
        `link`       -> the grammar key is PRESENT in the sentence's `grammar` list
        `no-link`    -> MARKED SKIP (see below) and still asserted: the sentence carries NO grammar
                        link, which is the judgement the row records
        `str`        -> grammar[structure_pattern|steps_unavailable] == new (new may be null)
        `json`       -> forms_json -> grammar["forms"] form list; references_json -> grammar["refs"];
                        formation_steps_json -> grammar["formation_steps"]; compared PARSED
        `ltext_json` -> form_meanings map, per form
  * `homograph_rulings.json`          {kind, lesson, new, old?}      W11a, owner decision A6
        kind `ref`    -> the lesson body renders `new`; a `change` row also asserts `old` is gone,
                         and an `affects: [unlock]` row asserts the lesson unlocks `new`
        kind `unlock` -> `new` is unlocked by that lesson and only that lesson, has an SRS card, is
                         in the lesson's own cumulative_known_set, is rendered as a chip in its
                         body, and is listed in NEITHER exemption file any more
        kind `practice` -> the lesson declares that exercise, of that type, the body REFERENCES it
                         (the app renders exercises only from <exercise ref=…/>), one of its
                         answer surfaces carries the surface the row says it drills, and the
                         exported `prompt`/`explanation` [pt-BR] are the row's text VERBATIM. An
                         exercise authored for a record and not asking about it is one failure
                         mode; the other is a corrected row that never reaches the learner (W11c)
        kind `hold`   -> the inverse assertion: still listed in coverage_exemptions.json and still
                         unlocked by nothing. A deferred placement that quietly became covered is a
                         failure, so a hold cannot rot
  * `level_evidence_repairs.json`     {address, entity, file, level}
        the levelled record at `address` carries BOTH `new_agreement` and `new_confidence`, and is
        still the record the campaign put to the panel: same entity, same registry file, same level.
        The pair is asserted TOGETHER because the defect W10 fixed was precisely the two halves
        disagreeing — a record whose string says `1/1` while its number says 0.34 passes either
        half-check on its own and is still self-contradictory. This table is DICT-shaped: it carries
        the formula it applied and its class counts alongside the rows, which live under `rows`.

`form_meanings` has no field of its own in the export. `scripts/export/export_corpus.py` builds
`forms` by iterating `forms_json` and looking the meaning up BY FORM STRING, so a meaning keyed on a
form that is not in `forms_json` is invisible to every consumer. That projection is what the 16
no-ops fell through, so a `form_meanings` row is checked per (form, meaning) pair against
`forms[].meaning[locale]`, and a missing form key is reported as its own root-cause class.

MARKED SKIPS — a marking is an assertion, never an excuse
---------------------------------------------------------
Three markings exist, and NONE is taken on trust: each is a claim this validator proves before it
lets the row out of the gate. That is the whole design rule here — a marker that stops being true
becomes a FAILURE, so marking a row can never hide a regression.

  * `grammar_followups.json` `action: "no-link"` (10 rows) — the orphaned sentences that illustrate
    no record in the registry. SKIP, and the judgement is still asserted: the sentence must carry
    ZERO grammar links. Tag one of them and the row fails (`link-still-present`, plant-proved).

  * `superseded_by: {"table": …, "row": N}` (7 rows in `sentence_text_repairs.json`) — a repair that
    landed and was then written over by a LATER campaign. SKIP only after all four of these hold:
    the named table is tracked, the row index is in range and is not this row itself, the successor
    addresses the SAME (slug, field, locale), the successor's `old` is this row's `new`, and the
    export carries the successor's `new`. Any one of them failing is `superseded_by-marker-does-not-
    chain`, a hard failure (plant-proved). Note what that buys: because the last condition compares
    against the export, a marked row still detects a regression — revert the field and the marker
    stops chaining.

The seven marked rows are `translation_literal` [pt-BR], six superseded by
`translation_defect_repairs.json` (rows 5, 1, 132, 76, 185, 15) and one by
`translation_followups.json` row 0; `translation_repairs_skipped.md` predicted exactly this
collision. An UNMARKED row in the same shape is still a failure
(`superseded-by-a-later-tracked-row`): `successor()` finds the chain and the report names the row
that needs the marker, so the marking stays a deliberate act.

  * MERGED AWAY (W08, owner decision A3) — `corpus/grammar_deprecated.json` maps the slug of a
    grammar record that was merged into another to its survivor. A repair row addressing a merged
    loser is neither a pass nor a failure: the record it repaired still exists (nothing is deleted;
    it keeps its row and gains `grammar_point.deprecated_by`) but no longer has a published address,
    so the export cannot carry the row's `new` and `address-does-not-resolve` would be a false
    finding. SKIP, and the redirect is asserted the way `superseded_by` is — against the export, on
    every run: it must not point at itself and its survivor must be a record the export actually
    carries, or the row fails `merged-away-redirect-broken`. The 4 rows this covers today are
    `grammar_record_repairs.json` 19-22 (`gp-152`, merged into `te-hoshii`).

    The claim is retired, NOT transferred. Re-asserting `gp-152`'s repaired explanation against
    `te-hoshii` would be false: `te-hoshii`'s prose was authored independently and never carried the
    build-commentary leak that repair removed. For the same reason the marker is NOT written into
    `grammar_record_repairs.json` as a `superseded_by`: a repair table is the historical record of
    what one campaign changed, and a later migration does not get to edit it. A `link` row is the one
    case that RESOLVES rather than retires — the sentence really does still illustrate the point, at
    the survivor's address, so the row skips only when the sentence carries the survivor.

Every other campaign's deliberate non-changes live in a report (`grammar_repairs_skipped.md`,
`translation_repairs_skipped.md`) or in a `DEFERRED` constant inside the apply script, NOT in the
table. Those rows are ordinary rows here and their failures are real findings.

NO RATCHET
----------
This gate is CLEAN: 2026-09-02, 1,299 rows, **1,282 PASS / 17 SKIP / 0 FAIL**. It carries no frozen
ceiling and no exemption file — any failure exits 1. The 7 rows that were the first run's only
failures now carry proved `superseded_by` markers instead of a ratcheted allowance, which is the
stronger arrangement: a ceiling counts failures, a marker has to keep chaining against the export.

G7's "16 `form_meanings` repairs silently no-oped" does NOT reproduce, and the difference is the
measurement, not the data. The audit tested by substring — it looked for the serialised map
`{"てほしい": "…"}` in the export text, which cannot match because the exporter projects that map
through `forms_json` into `forms[].meaning`. Replayed pair by pair through that projection, all 16
rows are carried by the export (`gp-152`, `gp-101`, `gp-121`, `gp-41`, `no-naka-de-a-ga-ichiban`,
`gp-133`, `gp-148`, `o-kudasai-2`, both locales each): the paired `forms` rows renamed the form keys
and `grammar_followups.json` finished the two records the first campaign could not reach. The
`form-key-absent-from-forms` class stays in the gate because the projection that hid it is still
there — a future rename that misses its meanings map lands in that class immediately (plant-proved).

Reads the exported JSON under `corpus/` (and confirms the `course/` tier is present — no tracked
table addresses a course record, and this gate fails if a repaired field ever starts being copied
into a lesson leaf instead of referenced by id).

Exit 1 on any failure, on an unregistered table, or on empty input.
Usage: validate_repairs_applied.py [--root PATH] [--all] [--table NAME]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

REPO = Path(__file__).resolve().parents[2]

# Floors far below the real counts, so growth never trips them but a vanished input always does.
MIN_TABLES = 10
MIN_ROWS_TOTAL = 1_000
MIN_SENTENCES = 5_000
MIN_GRAMMAR = 400
MIN_COURSE_FILES = 300

MAX_REPORT = 12

LOCALES = ("pt-BR", "en")

# ---------------------------------------------------------------------------------------------
# Root-cause classes. Every failure is classified and the fix for its class is printed with it.
# ---------------------------------------------------------------------------------------------
C_FORM_KEY_ABSENT = "form-key-absent-from-forms"
C_FORM_MEANING = "form-meaning-mismatch"
C_LAYER_A_SHADOW = "layer-a-en-shadows-the-row"
C_SUPERSEDED = "superseded-neither-old-nor-new"
C_SUPERSEDED_CHAIN = "superseded-by-a-later-tracked-row"
C_BAD_MARKER = "superseded_by-marker-does-not-chain"
C_NOT_APPLIED = "not-applied-old-still-present"
C_VALUE_MISMATCH = "value-mismatch"
C_NO_FIELD = "field-absent-from-export"
C_NO_RECORD = "address-does-not-resolve"
C_LINK_PRESENT = "link-still-present"
C_LINK_ABSENT = "link-absent"
C_MERGED_REDIRECT = "merged-away-redirect-broken"
C_LEVEL_EVIDENCE = "level-evidence-mismatch"

FIXES = {
    C_FORM_KEY_ABSENT:
        "export_corpus.py builds `forms` by iterating `forms_json` and looking each meaning up BY "
        "FORM STRING (line ~335), so a form_meanings key that is not in forms_json is projected "
        "nowhere. Either the paired `forms` row must rename the key in forms_json first (the "
        "campaign's own contract), or the exporter must emit the leftover meanings so the loss is "
        "visible. Column: grammar_point.forms_json + localized_text(form_meanings).",
    C_FORM_MEANING:
        "the form key IS in forms_json but forms[].meaning[locale] is not the repaired text — the "
        "localized_text(grammar_point, form_meanings, <locale>) map was never updated for that key.",
    C_LAYER_A_SHADOW:
        "export_corpus.py renders translation/en as `sentence.en or localized_text` (line 512). On "
        "a mined record sentence.en is Layer A and shadows the repaired localized row, so the edit "
        "is invisible by design. Column: sentence.en. Spec §1.1 forbids editing it — the row, not "
        "the exporter, is what has to change.",
    C_SUPERSEDED:
        "the export carries neither `old` nor `new` and no tracked row explains the difference. "
        "Something outside the repair tables rewrote this field — that is the dangerous shape and "
        "it is the one class here with no automatic account of itself.",
    C_SUPERSEDED_CHAIN:
        "the repair DID land and a LATER tracked row then consumed it: the successor's `old` is "
        "this row's `new`, and the export carries the successor's `new`. Nothing in the exporter is "
        "wrong and no column needs changing. Add `superseded_by: {\"table\": …, \"row\": N}` naming "
        "the successor printed below and the row becomes a checked SKIP; the marker is re-proved "
        "against the export on every run, so it cannot outlive the chain it claims.",
    C_BAD_MARKER:
        "a `superseded_by` marker that no longer holds. Either it names a row that is not there, or "
        "addresses a different field, or the successor's `old` is not this row's `new`, or the "
        "export does not carry the successor's `new` (which is what a REGRESSION on a marked row "
        "looks like). Re-derive the chain; never widen the marker to make it fit.",
    C_NOT_APPLIED:
        "the export still carries `old` verbatim — the repair genuinely did not land. Re-run the "
        "applier and re-export, or record why the applier skipped it.",
    C_VALUE_MISMATCH:
        "the field exists and differs from `new` in some other way; read the printed value.",
    C_NO_FIELD:
        "the exporter does not project this field/locale at all for this record.",
    C_NO_RECORD:
        "the slug/key the row addresses is not in the export — a retired or re-pointed identity.",
    C_LINK_PRESENT:
        "an `unlink` row's grammar key is still on the sentence. `apply_grammar_record_repairs.py` "
        "REFUSES an unlink that would leave a record with zero sentences; that refusal is reported "
        "to stdout and to grammar_repairs_skipped.md but is not marked in the table.",
    C_LINK_ABSENT:
        "a `link` row's grammar key is missing from the sentence's `grammar` list.",
    C_MERGED_REDIRECT:
        "the row addresses a grammar key that corpus/grammar_deprecated.json says was merged into "
        "another record, but the redirect does not hold: it names a survivor the export does not "
        "carry, or it points at itself. The redirect is regenerated by export_corpus.py on every "
        "run, so this means the export is half-written — re-export before reading anything else here.",
    C_LEVEL_EVIDENCE:
        "the record's (level_agreement, level_confidence) pair is neither what the row repaired it "
        "TO nor what it repaired it FROM, so something after scripts/apply_level_evidence.py "
        "rewrote the evidence. The pair is not free text: it is produced by "
        "scripts/ingest/reconcile_levels.py :: assign() and restated in design/schema_v2.md — "
        "`n_for/consulted` as a string and the same ratio rounded to 3 places as a number, or one "
        "of the two documented sentinels ('0' with 0.0, 'anchor' with 1.0). Re-run the applier "
        "against db/corpus.sqlite and re-export, or re-derive the row; never edit one half.",
}

# No ratchet, no ceiling, no exemption file: this gate is clean and any failure exits 1. The debt it
# was first measured with (7 superseded rows) is carried by proved `superseded_by` markers instead —
# see MARKED SKIPS in the module docstring for why that is the stronger arrangement.


def die(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


# ---------------------------------------------------------------------------------------------
# Export loading
# ---------------------------------------------------------------------------------------------
def load_export(root: Path) -> tuple[dict, dict, int]:
    bank = root / "corpus" / "sentences" / "bank.json"
    if not bank.exists():
        die(f"sentence bank not found: {bank}")
    sentences = json.loads(bank.read_text(encoding="utf-8"))
    if not isinstance(sentences, list) or len(sentences) < MIN_SENTENCES:
        die(f"sentence bank has {len(sentences)} records, floor is {MIN_SENTENCES} "
            f"(empty or truncated input must never certify a repair table)")
    by_slug = {s["slug"]: s for s in sentences}

    gfiles = sorted((root / "corpus" / "grammar").glob("*.json"))
    grammar: list[dict] = []
    for f in gfiles:
        grammar += json.loads(f.read_text(encoding="utf-8"))
    if len(grammar) < MIN_GRAMMAR:
        die(f"grammar registry has {len(grammar)} records over {len(gfiles)} file(s), floor is "
            f"{MIN_GRAMMAR}")
    by_key = {g["key"]: g for g in grammar}

    # W08. A grammar record merged into another (owner decision A3) leaves the published registry but
    # keeps its row and its repairs. Rows that address it are not failures and are not passes: they
    # are RETIRED, and the redirect is what proves it. Loaded here so the check is data-driven and
    # re-proved on every run, exactly like the `superseded_by` markers.
    #
    # The alternative — writing `superseded_by` into grammar_record_repairs.json — was rejected twice
    # over: a repair table is the historical record of what a campaign changed and a later migration
    # does not get to edit it, and re-asserting `gp-152`'s repaired text against `te-hoshii` would be
    # false, because te-hoshii's prose was authored independently and never carried the defect the
    # repair removed. The redirect retires the claim; it does not transfer it.
    dpath = root / "corpus" / "grammar_deprecated.json"
    if dpath.is_file():
        raw = json.loads(dpath.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            die(f"{dpath.name} is a {type(raw).__name__}, expected an object {{old slug: survivor slug}}")
        REDIRECT.clear()
        REDIRECT.update({k.split(":", 1)[-1]: v.split(":", 1)[-1] for k, v in raw.items()})

    course = list((root / "course").rglob("*.json"))
    if len(course) < MIN_COURSE_FILES:
        die(f"course tier has {len(course)} JSON files, floor is {MIN_COURSE_FILES}")
    return by_slug, by_key, len(course)


# W10 (owner decision A4). address -> (entity, registry file, record), over the three registries that
# carry a level at all. Built once in main() and read by handle_level_evidence, so the handler stays
# 1:1 with its table and no row re-walks the export.
LEVELLED: dict[str, tuple[str, str, dict]] = {}
LEVEL_REGISTRIES = ("grammar", "kanji", "vocab")
# W11c: the vocab registry by published slug, so lesson_ref_addresses.json can assert that a
# rewritten ref still names the SAME word (headword + kana), not merely a record that exists.
VOCAB_BY_SLUG: dict[str, dict] = {}


def load_levelled(root: Path) -> dict[str, tuple[str, str, dict]]:
    """Every levelled record in the export, by published slug, with the file it was found in.

    `level_agreement` / `level_confidence` live at the record root of exactly these three registries
    and nowhere else in the export. The FILE is carried alongside because a level_evidence row names
    one: a record that has since moved to another level's file is not the record the campaign put to
    the consensus panel, and re-asserting the panel's verdict against it would be false.
    """
    out: dict[str, tuple[str, str, dict]] = {}
    for entity in LEVEL_REGISTRIES:
        for path in sorted((root / "corpus" / entity).glob("*.json")):
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                continue
            for rec in records:
                slug = rec.get("slug") if isinstance(rec, dict) else None
                if isinstance(slug, str):
                    out.setdefault(slug, (entity, path.name, rec))
    return out


# W11a (owner decision A6). lesson slug -> the exported lesson leaf, plus the two exemption files
# the homograph rulings shrank. Built once in main(), read by handle_homograph_rulings.
LESSONS: dict[str, dict] = {}
EXEMPT: dict[str, set] = {}
MIN_LESSONS = 300
MIN_VOCAB = 5000


def load_lessons_export(root: Path) -> dict[str, dict]:
    """Every lesson leaf in the export, by lesson id. The homograph rulings are claims about these."""
    out: dict[str, dict] = {}
    for path in (root / "course").rglob("lesson-*.json"):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(rec, dict) and isinstance(rec.get("id"), str):
            out[rec["id"]] = rec
    return out


def load_exempt(root: Path) -> dict[str, set]:
    """The two held-back lists a `hold` row asserts membership of, read from the same files the
    other gates read (scripts/validate/README.md: two validators consuming the same rows consume
    the same file)."""
    cov = root / "course" / "coverage_exemptions.json"
    gat = root / "course" / "gating_exemptions.json"
    out = {"coverage": set(), "gating": set()}
    if cov.is_file():
        doc = json.loads(cov.read_text(encoding="utf-8"))
        out["coverage"] = {e["id"] for e in doc.get("vocab", []) if isinstance(e, dict) and e.get("id")}
    if gat.is_file():
        doc = json.loads(gat.read_text(encoding="utf-8"))
        out["gating"] = {(e.get("lesson"), e.get("ref")) for e in doc.get("item_refs", [])
                         if isinstance(e, dict)}
    return out


def handle_homograph_rulings(rows, sents, gram, table):
    """W11a's A6 homograph rulings, replayed against the exported course tree.

    Three kinds of row, three different claims, and each is checked as the claim it is rather than
    reduced to a common shape — which is the point: a `hold` says a record must still be MISSING
    from every unlock, and a check that only knew how to look things up would certify it by
    accident.

      practice one authored exercise per promoted unlock, checked as content rather than as a diff:
              declared, referenced by the body, and actually asking about the record.
      ref     the lesson body renders `new`. A `change` row additionally asserts `old` is GONE from
              that body: all four of the corrected refs occurred exactly once, so a surviving `old`
              means the export reverted (or a second occurrence appeared that nobody ruled on).
              A row whose `affects` includes "unlock" must also be unlocked there.
      unlock  the lesson unlocks `new` exactly once, carries an SRS card for it, has it in its own
              cumulative_known_set, renders a chip for it in the body, and the record is NOT still
              listed in either exemption file. That last clause is what makes the promotion
              irreversible-by-accident: put the row back in coverage_exemptions.json and this fails.
      hold    the opposite assertion, and it is an assertion: the record is listed in
              coverage_exemptions.json AND no lesson unlocks it. A hold that quietly became covered
              (or quietly lost its exemption) is a failure here, so the four deferred placements
              cannot rot into a silent hole while the file still claims they are held.
    """
    unlocked_by: dict[str, list[str]] = defaultdict(list)
    for lid, rec in LESSONS.items():
        for u in rec.get("unlocks", []):
            if u.get("type") == "vocab":
                unlocked_by[u.get("ref")].append(lid)

    out = []
    for i, r in enumerate(rows):
        kind = r.get("kind")
        if kind == "ref":
            addr = f"{table} row {i}: {r['headword']} @ {r['lesson']} body ref"
            lesson = LESSONS.get(r["lesson"])
            if lesson is None:
                out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
                continue
            body = lesson.get("body") or ""
            if f'"{r["new"]}"' not in body:
                out.append(("fail", C_NOT_APPLIED, addr,
                            f"the body renders no ref to {r['new']} — the ruling did not land "
                            f"(how={r['how']}, printed_reading={r.get('printed_reading')!r})"))
                continue
            if r["verdict"] == "change" and f'"{r["old"]}"' in body:
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            f"the body still renders the pre-ruling ref {r['old']}"))
                continue
            if "unlock" in (r.get("affects") or []) and r["lesson"] not in unlocked_by.get(r["new"], []):
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            f"the row says it affects an unlock, but {r['lesson']} does not unlock "
                            f"{r['new']}"))
                continue
            out.append(("ok", "", addr, "exact"))
        elif kind == "unlock":
            addr = f"{table} row {i}: {r['lesson']} unlocks {r['new']} ({r.get('kana')})"
            lesson = LESSONS.get(r["lesson"])
            if lesson is None:
                out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
                continue
            holders = unlocked_by.get(r["new"], [])
            if holders != [r["lesson"]]:
                out.append(("fail", C_NOT_APPLIED, addr,
                            f"unlocked by {holders or 'nothing'}, not by {r['lesson']} alone"))
                continue
            cards = [c.get("item") for c in lesson.get("srs", {}).get("introduces_cards", [])]
            if r["new"] not in cards:
                out.append(("fail", C_NO_FIELD, addr, "unlocked but no SRS card — it is filed nowhere"))
                continue
            if r["new"] not in (lesson.get("cumulative_known_set", {}).get("vocab") or []):
                out.append(("fail", C_VALUE_MISMATCH, addr, "not in its own cumulative_known_set"))
                continue
            if f'"{r["new"]}"' not in (lesson.get("body") or ""):
                out.append(("fail", C_NOT_APPLIED, addr,
                            "the lesson unlocks it but its body renders no chip for it — an unlock "
                            "nobody teaches is the hole this promotion was meant to close"))
                continue
            if r["new"] in EXEMPT["coverage"]:
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            "still listed in course/coverage_exemptions.json — promoted and held at once"))
                continue
            if (r["lesson"], r["new"]) in EXEMPT["gating"]:
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            "still listed in course/gating_exemptions.json — the body ref is inside "
                            "the lesson's own cks now, so the exemption is stale"))
                continue
            out.append(("ok", "", addr, "exact"))
        elif kind == "practice":
            addr = f"{table} row {i}: {r['lesson']} asks about {r['new']} in {r['exercise']}"
            lesson = LESSONS.get(r["lesson"])
            if lesson is None:
                out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
                continue
            ex = next((e for e in lesson.get("exercises", []) if e.get("id") == r["exercise"]), None)
            if ex is None:
                out.append(("fail", C_NOT_APPLIED, addr, "the lesson declares no such exercise"))
                continue
            if ex.get("type") != r["type"]:
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            f"exercise type is {ex.get('type')!r}, the row authored {r['type']!r}"))
                continue
            if f'<exercise ref="{r["exercise"]}"' not in (lesson.get("body") or ""):
                out.append(("fail", C_NOT_APPLIED, addr,
                            "authored but not referenced by the body — the app renders exercises only "
                            "from <exercise ref=…/> nodes, so this one reaches nobody"))
                continue
            # The answer key is what validate_practice_coverage.py measures, so that is what is
            # asserted here: the surface the row says it drills must be in a string the learner has
            # to produce or pick, not in the prompt or the explanation.
            ans = ex.get("answer") or {}
            surfaces = [ans.get("text"), ans.get("full"), ans.get("correct"),
                        *(ans.get("accept") or []), *(ans.get("order") or [])]
            if not any(isinstance(v, str) and r["answer_surface"] in v for v in surfaces):
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            f"no answer surface carries {r['answer_surface']!r} — the exercise exists "
                            f"but does not ask about the record it was authored for"))
                continue
            # W11c: the learner-facing text is the row's content, so it is asserted verbatim. The
            # review found the ex:n5-conectando-01-6 explanation teaching a false reading rule
            # (何 before か is なに, not なん) and nothing here or in the apply script would have
            # noticed the corrected row failing to reach the export.
            bad_text = next(
                ((fld, (ex.get(fld) or {}).get("pt-BR")) for fld in ("prompt", "explanation")
                 if (ex.get(fld) or {}).get("pt-BR") != r[fld]), None)
            if bad_text:
                fld, got = bad_text
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            f"the exported {fld} [pt-BR] is not the row's text — the table is the "
                            f"source of this exercise's content; export has {str(got)[:90]!r}"))
                continue
            out.append(("ok", "", addr, "exact"))
        elif kind == "hold":
            addr = f"{table} row {i}: {r['new']} ({r.get('kana')}) stays exempt"
            if r["new"] not in EXEMPT["coverage"]:
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            "the row holds this record back, but course/coverage_exemptions.json "
                            "does not list it"))
                continue
            if unlocked_by.get(r["new"]):
                out.append(("fail", C_VALUE_MISMATCH, addr,
                            f"held back, yet {unlocked_by[r['new']]} unlocks it — the hold and the "
                            f"course disagree"))
                continue
            out.append(("ok", "", addr, "exact"))
        else:
            out.append(("fail", C_NO_RECORD, f"{table} row {i}", f"unknown kind {kind!r}"))
    return out


def read_table(path: Path, name: str) -> list[dict]:
    """The rows of one repair table, whichever of the two shapes it is written in.

    Six tables ARE the list. `level_evidence_repairs.json` is an object that keeps the formula it
    applied, the classes it sorted its 200 findings into and a `row_count` in the same file as the
    rows — the campaign's audit trail, which belongs with the rows rather than in a sibling nobody
    would open — and puts the rows under `rows`. Both shapes are read here so the shape stays a
    detail of the table instead of a branch in every consumer.

    A `row_count` that disagrees with the rows it counts FAILS: a header that can drift from its own
    table is a header nobody can cite, and this gate's whole premise is that a campaign's ledger and
    the shipped data have to be re-provable against each other.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(doc, dict):
        rows = doc.get("rows")
        declared = doc.get("row_count")
        if isinstance(declared, int) and isinstance(rows, list) and declared != len(rows):
            die(f"{name}: the header says row_count={declared}, the table holds {len(rows)} rows")
    else:
        rows = doc
    if not isinstance(rows, list) or not rows:
        die(f"{name}: table is empty or not a list")
    if not all(isinstance(r, dict) for r in rows):
        die(f"{name}: every row must be an object")
    return rows


def course_scalar_values(root: Path) -> set[str]:
    """Every scalar string in the course tier, for the embedded-copy check."""
    out: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, str):
            if len(node) >= 60:
                out.add(node)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    for f in (root / "course").rglob("*.json"):
        walk(json.loads(f.read_text(encoding="utf-8")))
    return out


# ---------------------------------------------------------------------------------------------
# Field readers
# ---------------------------------------------------------------------------------------------
def locale_value(rec: dict, field: str, locale: str):
    v = rec.get(field)
    if isinstance(v, dict):
        return v.get(locale)
    return None


def is_mined(sent: dict) -> bool:
    """A record whose English is a SELECTED source pair (Layer A), not authored text."""
    prov = sent.get("provenance") or {}
    src = str(prov.get("jp_source") or "")
    return not str(sent.get("slug", "")).startswith("sent:gen-") or src.startswith("tatoeba")


def classify_text(current, old, new) -> str:
    if current is None:
        return C_NO_FIELD
    if isinstance(current, str) and isinstance(old, str) and old and old in current:
        return C_NOT_APPLIED
    return C_SUPERSEDED if isinstance(current, str) else C_VALUE_MISMATCH


def check_text(rec, field, locale, old, new, *, span_ok: bool) -> tuple[bool, str, str]:
    """(ok, cls, note). `span_ok` mirrors the applier that accepts a quoted span."""
    cur = locale_value(rec, field, locale) if locale else rec.get(field)
    if cur == new:
        return True, "", "exact"
    if span_ok and isinstance(cur, str) and isinstance(new, str) and new and new in cur:
        return True, "", "span"
    return False, classify_text(cur, old, new), repr(cur)[:220]


def check_form_meanings(rec, locale, new) -> tuple[str, str]:
    """("", "") when every (form, meaning) pair of `new` is carried by forms[]; else (class, note).

    `form_meanings` has no field of its own in the export: export_corpus.py iterates `forms_json`
    and looks each meaning up BY FORM STRING, so this walks the map the row wrote and asks the
    projection for it, pair by pair. A naive substring search for the serialised map (which is how
    the readiness audit measured it) cannot see through that projection and reports every row as a
    no-op — which is why G7 counted 16.
    """
    if isinstance(new, str):
        new = json.loads(new)
    if not isinstance(new, dict) or not new:
        return C_VALUE_MISMATCH, f"`new` is not a non-empty form->meaning map: {new!r}"[:200]
    index = {f.get("form"): f for f in (rec.get("forms") or []) if isinstance(f, dict)}
    notes: list[str] = []
    cls = ""
    for form, meaning in new.items():
        entry = index.get(form)
        if entry is None:
            cls = cls or C_FORM_KEY_ABSENT
            notes.append(f"form {form!r} is not in forms[] (forms carry {sorted(index)!r}), so the "
                         f"meaning is projected nowhere")
        else:
            got = (entry.get("meaning") or {}).get(locale)
            if got != meaning:
                cls = cls or C_FORM_MEANING
                notes.append(f"forms[{form!r}].meaning[{locale}] = {got!r}"[:200])
    return (cls, "; ".join(notes)) if cls else ("", "")


# ---------------------------------------------------------------------------------------------
# Per-table handlers. Each returns rows of (status, cls, address, detail).
# status: "ok" | "fail" | "skip"
# ---------------------------------------------------------------------------------------------
# (slug, field, locale) -> [(table, row_index, old, new)] across EVERY tracked table, so a row that
# a later campaign consumed can be told apart from a row that was simply lost. Built once in main().
CHAINS: dict[tuple, list[tuple]] = {}
# table name -> its rows, for resolving `superseded_by`. Built once in main().
TABLES: dict[str, list[dict]] = {}
# W08: merged-away grammar key -> survivor key, read from the published redirect by load_export().
# Keyed on the bare key (`gp-152`), which is how every repair table addresses a grammar record.
REDIRECT: dict[str, str] = {}


def redirect_target(key: str, gram: dict) -> tuple[str, str]:
    """("", "") when `key` is live; ("", survivor) when its redirect holds; (class, note) when not."""
    survivor = REDIRECT.get(key)
    if survivor is None:
        return "", ""
    if survivor == key:
        return C_MERGED_REDIRECT, f"corpus/grammar_deprecated.json points {key!r} at itself"
    if survivor not in gram:
        return C_MERGED_REDIRECT, (f"corpus/grammar_deprecated.json redirects {key!r} to {survivor!r}, "
                                   f"which the exported grammar registry does not carry")
    return "", survivor


def retired_gate(key: str, gram: dict, addr: str) -> tuple | None:
    """None when `key` still has a published address; otherwise this row's final result.

    Checked, not trusted: the redirect has to resolve against THIS export or the row fails. Same
    contract as `marker_gate` — a marking that stops being true becomes a failure.
    """
    cls, note = redirect_target(key, gram)
    if cls:
        return ("fail", cls, addr, note)
    if not note:
        return None
    return ("skip", "", addr,
            f"retired: merged into {note!r} (corpus/grammar_deprecated.json; the survivor is in the "
            f"export). The repair landed on a record that keeps its row and loses its published "
            f"address; the claim is retired, not transferred to {note!r}")


def retired_link_gate(key: str, links: list, gram: dict, addr: str) -> tuple | None:
    """A `link` row whose grammar key was merged away RESOLVES through the redirect.

    Unlike a text repair, the claim survives the merge: the sentence still illustrates the point, at
    the survivor's address. So the redirect must not merely hold — the sentence has to carry the
    survivor, or the link really is gone and the row fails.
    """
    cls, note = redirect_target(key, gram)
    if cls:
        return ("fail", cls, addr, note)
    if not note:
        return None
    if note in links:
        return ("skip", "", addr, f"resolved through the redirect: {key!r} merged into {note!r} and "
                                  f"the sentence carries {note!r}")
    return ("fail", C_LINK_ABSENT, addr,
            f"{key!r} was merged into {note!r} and the sentence carries neither; "
            f"sentence.grammar = {links!r:.160}")


def row_address(r) -> tuple:
    """The (entity, field, locale) a `superseded_by` marker must agree with on both ends."""
    return (r.get("slug") or r.get("key"), r.get("field"), r.get("locale"))


def check_marker(r, table, i, current) -> tuple[str, str]:
    """("", note) when a `superseded_by` marker chains; (class, note) when it does not.

    Five conditions, all of them necessary. The last one is what keeps a marked row honest: it
    compares against the EXPORT, so reverting the field breaks the marker instead of hiding behind
    it. `no-link` works the same way — a marking here is an assertion, not an excuse.
    """
    m = r["superseded_by"]
    if not isinstance(m, dict) or set(m) != {"table", "row"}:
        return C_BAD_MARKER, f"`superseded_by` must be {{table, row}}, got {m!r}"[:200]
    t, j = m["table"], m["row"]
    rows = TABLES.get(t)
    if rows is None:
        return C_BAD_MARKER, f"names table {t!r}, which is not a tracked repair table"
    if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j < len(rows):
        return C_BAD_MARKER, f"names {t} row {j!r}, out of range 0..{len(rows) - 1}"
    if (t, j) == (table, i):
        return C_BAD_MARKER, "points at itself"
    succ = rows[j]
    if row_address(succ) != row_address(r):
        return C_BAD_MARKER, (f"names {t} row {j}, which addresses {row_address(succ)} — not this "
                              f"row's address {row_address(r)}")
    if succ.get("old") != r["new"]:
        return C_BAD_MARKER, (f"{t} row {j} does not continue the chain: its `old` is not this "
                              f"row's `new`")
    if current != succ.get("new"):
        return C_BAD_MARKER, (f"{t} row {j} chains, but the export carries neither its `new` nor "
                              f"anything this chain explains; export carries {current!r}")[:240]
    return "", (f"superseded by {t} row {j} (chain proved: successor `old` == this `new`, export == "
                f"successor `new`)")


def successor(r, current) -> str | None:
    """The later tracked row that consumed this one, if any.

    Campaigns run in sequence and several of them touch the same fields. When a later row's `old` is
    this row's `new` and the export carries that later row's `new`, the repair DID land and was then
    improved — a completely different situation from a repair that never landed, and the report has
    to say which.
    """
    key = (r.get("slug"), r.get("field"), r.get("locale"))
    for table, i, old, new in CHAINS.get(key, []):
        if old == r["new"] and current == new:
            return f"{table} row {i}"
    return None


def marker_gate(r, table, i, current, addr) -> tuple | None:
    """None when the row carries no `superseded_by`; otherwise its final result tuple.

    Checked BEFORE the ordinary value comparison, so a marker on a row that is in fact still live
    (or on a field that regressed) fails instead of quietly passing as a skip.
    """
    if r.get("superseded_by") is None:
        return None
    cls, note = check_marker(r, table, i, current)
    return ("fail", cls, addr, note) if cls else ("skip", "", addr, note)


def _sentence_field(r, sents, table, i) -> tuple:
    """One localized (or scalar-column) field on a sentence. Exactly one result tuple."""
    slug, field, locale = r["slug"], r["field"], r.get("locale")
    addr = f"{table} row {i}: {slug}.{field}" + (f"[{locale}]" if locale else " (column)")
    s = sents.get(slug)
    if s is None:
        return "fail", C_NO_RECORD, addr, "no such sentence in the export"
    cur = locale_value(s, field, locale) if locale else s.get(field)
    marked = marker_gate(r, table, i, cur, addr)
    if marked:
        return marked
    ok, cls, note = check_text(s, field, locale, r["old"], r["new"], span_ok=False)
    if ok:
        return "ok", "", addr, note
    nxt = successor(r, cur)
    if nxt:
        return ("fail", C_SUPERSEDED_CHAIN, addr,
                f"`new` landed and was then consumed by {nxt} — add `superseded_by` naming it; "
                f"export carries {note}")
    if field == "translation" and locale == "en" and is_mined(s):
        return "fail", C_LAYER_A_SHADOW, addr, f"export carries {note}"
    return "fail", cls, addr, f"export carries {note}"


def handle_sentence_text_repairs(rows, sents, gram, table):
    return [_sentence_field(r, sents, table, i) for i, r in enumerate(rows)]


def handle_jargon_pass2(rows, sents, gram, table):
    return [_sentence_field(r, sents, table, i) for i, r in enumerate(rows)]


def handle_translation_followups(rows, sents, gram, table):
    return [_sentence_field(r, sents, table, i) for i, r in enumerate(rows)]


def handle_translation_defect(rows, sents, gram, table):
    out = []
    for i, r in enumerate(rows):
        if r["entity"] == "sentence":
            out.append(_sentence_field(r, sents, table, i))
            continue
        slug, field, locale = r["slug"], r["field"], r["locale"]
        pos = r["token_position"]
        addr = f"{table} row {i}: {slug} token[{pos}].{field}[{locale}]"
        s = sents.get(slug)
        if s is None:
            out.append(("fail", C_NO_RECORD, addr, "no such sentence in the export"))
            continue
        at = [t for t in (s.get("tokens") or []) if t.get("position") == pos]
        if not at:
            out.append(("fail", C_NO_RECORD, addr, f"no token at position {pos}"))
            continue
        # `position` is not unique (C-mode compound + its A-mode parts), so the applier matched
        # across every token there and so does this.
        got = [locale_value(t, field, locale) for t in at]
        if r["new"] in got:
            out.append(("ok", "", addr, "exact"))
        else:
            cls = classify_text(next((g for g in got if g is not None), None), r["old"], r["new"])
            out.append(("fail", cls, addr, f"tokens at that position carry {got!r}"[:240]))
    return out


def handle_grammar_record_repairs(rows, sents, gram, table):
    out = []
    for i, r in enumerate(rows):
        key, act = r["key"], r["action"]
        g = gram.get(key)
        if g is None:
            gate = retired_gate(key, gram, f"{table} row {i}: {key} [{act}]")
            if gate:
                out.append(gate)
                continue
        if act == "unlink":
            addr = f"{table} row {i}: unlink {r['sentence']} -/-> {key}"
            s = sents.get(r["sentence"])
            if s is None:
                out.append(("fail", C_NO_RECORD, addr, "no such sentence in the export"))
            elif key in (s.get("grammar") or []):
                out.append(("fail", C_LINK_PRESENT, addr,
                            f"sentence.grammar = {(s.get('grammar') or [])!r:.160}"))
            else:
                out.append(("ok", "", addr, "link absent"))
            continue
        if g is None:
            out.append(("fail", C_NO_RECORD, f"{table} row {i}: {key}",
                        "no such grammar point in the export"))
            continue
        if act == "forms":
            addr = f"{table} row {i}: {key}.forms"
            want = json.loads(r["new"]) if isinstance(r["new"], str) else r["new"]
            got = [f.get("form") for f in (g.get("forms") or [])]
            out.append(("ok", "", addr, "exact") if got == want
                       else ("fail", C_VALUE_MISMATCH, addr, f"forms[] = {got!r}"[:220]))
            continue
        # act == "text"
        field, locale = r["field"], r["locale"]
        addr = f"{table} row {i}: {key}.{field}[{locale}]"
        if field == "form_meanings":
            cls, note = check_form_meanings(g, locale, r["new"])
            out.append(("ok", "", addr, "exact") if not cls else ("fail", cls, addr, note))
            continue
        marked = marker_gate(r, table, i, locale_value(g, field, locale), addr)
        if marked:
            out.append(marked)
            continue
        ok, cls, note = check_text(g, field, locale, r["old"], r["new"], span_ok=True)
        out.append(("ok", "", addr, note) if ok
                   else ("fail", cls, addr, f"export carries {note}"))
    return out


JSON_COLUMN_TO_EXPORT = {
    "references_json": "refs",
    "formation_steps_json": "formation_steps",
}


def handle_grammar_followups(rows, sents, gram, table):
    out = []
    for i, r in enumerate(rows):
        act = r["action"]
        if act in ("link", "no-link"):
            slug = r["sentence"]
            key = r.get("key")
            addr = (f"{table} row {i}: link {slug} -> {key}" if act == "link"
                    else f"{table} row {i}: no-link {slug}")
            s = sents.get(slug)
            if s is None:
                out.append(("fail", C_NO_RECORD, addr, "no such sentence in the export"))
                continue
            links = s.get("grammar") or []
            if act == "link":
                if key in links:
                    out.append(("ok", "", addr, "link present"))
                else:
                    out.append(retired_link_gate(key, links, gram, addr)
                               or ("fail", C_LINK_ABSENT, addr,
                                   f"sentence.grammar = {links!r:.160}"))
            else:
                # MARKED SKIP: the applier never writes these. The judgement is still asserted.
                out.append(("skip", "", addr, "marked no-link; sentence untagged as recorded")
                           if not links
                           else ("fail", C_LINK_PRESENT, addr,
                                 f"recorded as illustrating no record but carries {links!r:.160}"))
            continue
        key = r["key"]
        g = gram.get(key)
        if g is None:
            gate = retired_gate(key, gram, f"{table} row {i}: {key} [{act}]")
            out.append(gate or ("fail", C_NO_RECORD, f"{table} row {i}: {key}",
                                "no such grammar point in the export"))
            continue
        if act == "str":
            col = r["column"]
            addr = f"{table} row {i}: {key}.{col}"
            got = g.get(col)
            out.append(("ok", "", addr, "exact") if got == r["new"]
                       else ("fail", C_VALUE_MISMATCH, addr, f"export carries {got!r:.200}"))
            continue
        if act == "json":
            col = r["column"]
            if col == "forms_json":
                addr = f"{table} row {i}: {key}.forms_json -> forms[]"
                got = [f.get("form") for f in (g.get("forms") or [])]
                out.append(("ok", "", addr, "exact") if got == r["new"]
                           else ("fail", C_VALUE_MISMATCH, addr, f"forms[] = {got!r:.200}"))
            else:
                dest = JSON_COLUMN_TO_EXPORT[col]
                addr = f"{table} row {i}: {key}.{col} -> {dest}"
                got = g.get(dest)
                out.append(("ok", "", addr, "exact") if got == r["new"]
                           else ("fail", C_VALUE_MISMATCH, addr, f"export carries {got!r:.200}"))
            continue
        # act == "ltext_json" (form_meanings)
        locale = r["locale"]
        addr = f"{table} row {i}: {key}.form_meanings[{locale}]"
        cls, note = check_form_meanings(g, locale, r["new"])
        out.append(("ok", "", addr, "exact") if not cls else ("fail", cls, addr, note))
    return out


def _conf_eq(got, want) -> bool:
    """`level_confidence` is a ratio rounded to 3 places, so compare it as one.

    `0.34` in the export and `0.34` in the table are the same claim; a float `==` that happened to
    disagree in the 17th decimal would report a repair as lost when nothing had moved. A bool is
    rejected outright — `True` is not a confidence, and Python would otherwise read it as 1.
    """
    if isinstance(got, bool) or not isinstance(got, (int, float)):
        return False
    if isinstance(want, bool) or not isinstance(want, (int, float)):
        return False
    return round(float(got), 3) == round(float(want), 3)


def handle_level_evidence(rows, sents, gram, table):
    """W10's level-evidence repairs (owner decision A4), replayed against the export.

    A row here is a claim about EVIDENCE rather than about prose. `level_agreement` is the string
    that says how many of the consulted community lists placed the record at the level it is taught
    at, and `level_confidence` is that same ratio as a number; §1.5 makes the pair the whole of what
    a level tag is allowed to assert, because there is no official JLPT list to appeal to. The
    campaign found 200 records where the two halves disagreed with the formula that produced them
    and restated the string (or the documented sentinel).

    Both halves are asserted TOGETHER. A record whose string reads `1/1` while its number reads 0.34
    satisfies either half-check alone and is still self-contradictory, which is the exact defect the
    campaign existed to remove — so a run that checked one field would certify the thing it was
    written to catch.

    The `entity`, `file` and `level` a row names are asserted too. They are not decoration: they
    identify WHICH panel the ratio came from, and a record that has since moved level (or moved to
    another registry file) is a different record from the one that was put to it.
    """
    out = []
    for i, r in enumerate(rows):
        address = r["address"]
        addr = f"{table} row {i}: {address}.level_agreement+level_confidence"
        found = LEVELLED.get(address)
        if found is None:
            out.append(("fail", C_NO_RECORD, addr,
                        f"no levelled record in the export has the address {address!r} "
                        f"(the row files it under {r.get('entity')}/{r.get('file')})"))
            continue
        entity, fname, rec = found
        if entity != r.get("entity") or fname != r.get("file"):
            out.append(("fail", C_NO_RECORD, addr,
                        f"the row addresses {r.get('entity')}/{r.get('file')}, but {address} is "
                        f"published in corpus/{entity}/{fname} — the record moved, so the panel "
                        f"this row quotes is not the panel that levelled it"))
            continue
        if rec.get("level") != r.get("level"):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"the row's evidence is for level {r.get('level')!r}; the export teaches "
                        f"this record at {rec.get('level')!r}"))
            continue
        got_a, got_c = rec.get("level_agreement"), rec.get("level_confidence")
        if got_a is None or got_c is None:
            out.append(("fail", C_NO_FIELD, addr,
                        f"level_agreement={got_a!r}, level_confidence={got_c!r} — the exporter is "
                        f"not projecting the evidence pair for this record at all"))
            continue
        if got_a == r["new_agreement"] and _conf_eq(got_c, r["new_confidence"]):
            out.append(("ok", "", addr, "exact"))
            continue
        reverted = got_a == r["old_agreement"] and _conf_eq(got_c, r["old_confidence"])
        out.append(("fail", C_NOT_APPLIED if reverted else C_LEVEL_EVIDENCE, addr,
                    f"export carries ({got_a!r}, {got_c!r}); the row repaired "
                    f"({r['old_agreement']!r}, {r['old_confidence']!r}) -> "
                    f"({r['new_agreement']!r}, {r['new_confidence']!r})"))
    return out


# name -> (handler, required keys per row)
def handle_lesson_ref_addresses(rows, sents, gram, table):
    """W11c's address rewrite, replayed against the EXPORTED course tree.

    Each row says: this lesson used to address a record by `old` (a storage row number, or a
    headword two records answer to) and now addresses it by `new`, the published slug — and the
    record is the SAME one. Three claims, checked as three:

      1. the lesson's export renders `new` — in an `unlocks[].ref` or in the body, whichever the
         row's occurrence count implies (both, for every row here);
      2. `new` resolves in the vocab registry, and to a record whose headword and kana are the ones
         the row recorded. A rewrite that landed on a different word is the only way this table can
         do damage, so it is the check that matters most;
      3. `old` is GONE from that lesson. Not from the export as a whole — `vocab:中` is still a
         legitimate ref in the lessons this table does not touch — but from this one, because
         leaving it would mean the rewrite half-landed and the resolver is still guessing there.
    """
    out = []
    for i, r in enumerate(rows):
        addr = f"{table} row {i}: {r['lesson']} addresses {r['headword']}/{r['kana']} as {r['new']}"
        lesson = LESSONS.get(r["lesson"])
        if lesson is None:
            out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
            continue
        rec = VOCAB_BY_SLUG.get(r["new"])
        if rec is None:
            out.append(("fail", C_NO_RECORD, addr, f"{r['new']} resolves to no vocab record"))
            continue
        if (rec.get("headword"), rec.get("kana")) != (r["headword"], r["kana"]):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"{r['new']} is {rec.get('headword')}/{rec.get('kana')} in the registry, "
                        f"the row recorded {r['headword']}/{r['kana']} — the rewrite landed on a "
                        f"different word"))
            continue
        body = lesson.get("body") or ""
        refs = {u.get("ref") for u in lesson.get("unlocks", []) if u.get("type") == "vocab"}
        if r["new"] not in refs and f'"{r["new"]}"' not in body:
            out.append(("fail", C_NOT_APPLIED, addr,
                        "neither the unlock list nor the body carries the published address"))
            continue
        if f'"{r["old"]}"' in body or r["old"] in refs:
            out.append(("fail", C_NOT_APPLIED, addr,
                        f"the lesson still addresses the record as {r['old']} — a row number or an "
                        f"ambiguous headword is not an address (contracts/manifest.json "
                        f"id_convention)"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


def handle_orthographic_relinks(rows: list[dict], sents: dict, gram: dict, table: str) -> list[tuple]:
    """W12. Every relink must be visible in the SHIPPED bank as `tokens[].vocab` on its anchor.

    The row addresses a token SPAN by sentence slug and position, so the replay re-proves three things
    and not just the presence of a slug: the span still holds the surfaces the row matched (a
    re-dissection that moved the boundaries invalidates the match, it does not silently inherit it),
    the anchor token carries the record, and the record is still the headword/kana the row named. The
    sentence-level `vocab` edge is deliberately NOT what is asserted: it is a union of three
    historical passes and would pass for links this campaign never made.
    """
    out = []
    for i, r in enumerate(rows):
        addr = (f"{table} row {i}: {r['sentence']} @{r['anchor_position']} "
                f"{r['surface']} -> {r['vocab']}")
        s = sents.get(r["sentence"])
        if s is None:
            out.append(("fail", C_NO_RECORD, addr, "the export carries no such sentence"))
            continue
        at_pos = {t.get("position"): t for t in (s.get("tokens") or [])
                  if t.get("split_mode") == "C"}
        span = [at_pos.get(p) for p in r["span"]]
        if any(t is None for t in span):
            out.append(("fail", C_NO_RECORD, addr,
                        f"positions {r['span']} are not all C tokens of this sentence"))
            continue
        if [t.get("surface") for t in span] != r["span_surfaces"]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"the span now reads {[t.get('surface') for t in span]!r}, the row matched "
                        f"{r['span_surfaces']!r} — the dissection moved under the link"))
            continue
        anchor = at_pos[r["anchor_position"]]
        if anchor.get("vocab") != r["vocab"]:
            out.append(("fail", C_LINK_ABSENT, addr,
                        f"the anchor token carries {anchor.get('vocab')!r}, not {r['vocab']!r}"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


def handle_lesson_needs(rows, sents, gram, table):
    """W21. Every prerequisite edge must be in the SHIPPED lesson record, with its own note.

    Three claims per row and all three matter: the edge is stored (a `needs` entry whose ref is the
    row's), the note the learner reads is the one the fixed pt-BR template produced (a hand-edited
    note is drift, and drift is what this table exists to prevent), and the edge points STRICTLY
    BACKWARDS in course order. The last one duplicates validate_lesson_gating C1 on purpose: this
    gate replays the table against the export without loading the derivation at all, so it stays
    honest even if the derivation itself is what breaks.
    """
    out = []
    order = list(LESSONS.keys())
    pos = {lid: i for i, lid in enumerate(order)}
    for i, r in enumerate(rows):
        addr = f"{table} row {i}: {r['lesson']} needs {r['ref']} ({r['origin']})"
        lesson = LESSONS.get(r["lesson"])
        if lesson is None:
            out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
            continue
        got = [n for n in (lesson.get("needs") or [])
               if isinstance(n, dict) and n.get("ref") == r["ref"]]
        if not got:
            out.append(("fail", C_NOT_APPLIED, addr, "the exported lesson stores no such need"))
            continue
        if got[0].get("note") != r["note"]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"the exported note is {got[0].get('note')!r}, the row says {r['note']!r}"))
            continue
        if r["ref"] not in pos:
            out.append(("fail", C_NO_RECORD, addr, f"{r['ref']} is not an exported lesson"))
            continue
        if pos[r["ref"]] >= pos[r["lesson"]]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"{r['ref']} is at position {pos[r['ref']]}, not before "
                        f"{pos[r['lesson']]} — a prerequisite that comes later is not one"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


def handle_lesson_furigana(rows, sents, gram, table):
    """W21. Every derived reading must be on the span in the SHIPPED body, and the bare form gone.

    The row is (lesson, surface) -> reading. The replay asserts the annotated span is present as
    many times as the row counted and that no bare `<jp>surface</jp>` survives in that lesson: a
    half-applied substitution would leave some occurrences silent, which is exactly the state this
    campaign was built to end.
    """
    out = []
    for i, r in enumerate(rows):
        addr = f"{table} row {i}: {r['lesson']} <jp>{r['surface']}</jp> -> {r['reading']}"
        lesson = LESSONS.get(r["lesson"])
        if lesson is None:
            out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
            continue
        body = lesson.get("body") or ""
        want = f'<jp reading="{r["reading"]}">{r["surface"]}</jp>'
        n = body.count(want)
        # `occurrences` counts the spans that were BARE when the table was built; a lesson may also
        # have printed the same base with the same reading already, so the assertion is "at least
        # that many, and none left bare" rather than an equality that would fail on the lesson's own
        # earlier annotations.
        if n < r["occurrences"]:
            out.append(("fail", C_NOT_APPLIED, addr,
                        f"the exported body carries {n} annotated span(s), the row derived "
                        f"{r['occurrences']}"))
            continue
        if f"<jp>{r['surface']}</jp>" in body:
            out.append(("fail", C_NOT_APPLIED, addr,
                        "a bare <jp> span with the same base survives — the reading landed on "
                        "some occurrences and not others"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


READINGS: dict[str, dict] = {}
MIN_READINGS = 250


def load_readings_export(root: Path) -> dict[str, dict]:
    """Every exported reading box, by slug. The W15 rows are claims about these."""
    out: dict[str, dict] = {}
    for path in sorted((root / "corpus" / "readings").glob("n*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            out[rec["slug"]] = rec
    return out


def handle_reading_passages(rows, sents, gram, table):
    """W15. Every authored passage must BE the reading box the row names, in the shipped export.

    Six claims per row, because a passage apply can fail in six different ways and five of them are
    silent: the box prints the authored Japanese (`jp`), its segmentation still concatenates to it,
    its translations are the authored ones, `uses` is exactly the snapshot the gate computed (an
    apply that quietly recomputed it from the link tables would drift out of the known set — the
    failure mode `apply_readings_composition_repairs.py` records), the box is Layer C /
    `ai_generated` / `needs_review` (authored Japanese a teacher has not signed off), and `source`
    names the campaign. The `old` value is asserted GONE: a run that wrote nothing would otherwise
    pass every "is the new value there" check on a box that still holds the concatenation.
    """
    out = []
    for i, r in enumerate(rows):
        addr = f"{table} row {i}: {r['slug']} ({r['lesson']})"
        rec = READINGS.get(r["slug"])
        n = r["new"]
        if rec is None:
            out.append(("fail", C_NO_RECORD, addr, f"no exported reading {r['slug']}"))
            continue
        if rec.get("jp") != n["jp"]:
            same_as_old = rec.get("jp") == r["old"]["jp"]
            out.append(("fail", C_NOT_APPLIED if same_as_old else C_VALUE_MISMATCH, addr,
                        "the box still holds the pre-W15 concatenation" if same_as_old
                        else "the box holds neither the row's `old` nor its `new` jp"))
            continue
        if "".join(rec.get("sentences") or []) != n["jp"]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        "`sentences` does not re-concatenate to the passage"))
            continue
        tr = rec.get("translation") or {}
        if tr.get("pt-BR") != n["translation_pt"] or tr.get("en") != n["translation_en"]:
            out.append(("fail", C_VALUE_MISMATCH, addr, "a translation is not the authored one"))
            continue
        u = rec.get("uses") or {}
        if sorted(u.get("kanji") or []) != sorted(n["uses"]["kanji"]) or \
                sorted(u.get("vocab") or []) != sorted(n["uses"]["vocab"]):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"`uses` is {len(u.get('kanji') or [])}k/{len(u.get('vocab') or [])}v, the "
                        f"row's snapshot is {len(n['uses']['kanji'])}k/{len(n['uses']['vocab'])}v"))
            continue
        if not (rec.get("layer") == "C" and rec.get("ai_generated") is True
                and rec.get("needs_review") is True and rec.get("source") == n["source"]):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"provenance is layer={rec.get('layer')} ai={rec.get('ai_generated')} "
                        f"nr={rec.get('needs_review')} source={rec.get('source')!r}"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


def handle_practice_exercises(rows, sents, gram, table):
    """W20. Every authored kanji exercise must BE in the lesson that unlocks the kanji, and rendered.

    The row is addressed by CONTENT, not by id: `{lesson, exercise}` where `exercise` is a whole
    lesson-schema exercise object. Content addressing is deliberate — three lessons gained an
    exercise between authoring and apply, so six ids were shifted by one to keep continuing their
    lesson's numbering (`apply_id_remap` in the table), and a replay keyed on the authored id would
    fail on a renumber that is correct. Prompt + answer is unique within a lesson by
    `validate_exercise_contracts.py` check 4, so the match is exactly one exercise or it is a
    failure.

    Four claims per row, and the last one is the one that is silent when it breaks: the exported
    lesson holds an exercise with this type, this prompt, this answer key and this explanation; the
    match is unique; the lesson BODY references it exactly once (the app renders exercises only from
    `<exercise ref>` nodes, so an exercise nobody references is authored practice the learner never
    sees); and its `sentence_refs` are the row's.
    """
    out = []
    for i, r in enumerate(rows):
        want = r["exercise"]
        addr = (f"{table} row {i}: {r['lesson']} {want['id']} ({want['type']}, "
                f"targets {' '.join(r.get('targets') or []) or '-'})")
        lesson = LESSONS.get(r["lesson"])
        if lesson is None:
            out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
            continue
        hit = [e for e in (lesson.get("exercises") or [])
               if e.get("type") == want["type"] and e.get("prompt") == want.get("prompt")
               and e.get("answer") == want.get("answer")]
        if not hit:
            same_prompt = [e["id"] for e in (lesson.get("exercises") or [])
                           if e.get("prompt") == want.get("prompt")]
            out.append(("fail", C_NOT_APPLIED, addr,
                        "the exported lesson carries no exercise with this type, prompt and answer"
                        + (f" (same prompt, different type/answer: {same_prompt})" if same_prompt else "")))
            continue
        if len(hit) > 1:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"{len(hit)} exported exercises share this prompt and answer: "
                        f"{[e['id'] for e in hit]}"))
            continue
        got = hit[0]
        if got.get("explanation") != want.get("explanation"):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"{got['id']}: the exported explanation is {got.get('explanation')!r}, the "
                        f"row's is {want.get('explanation')!r}"))
            continue
        if list(got.get("sentence_refs") or []) != list(want.get("sentence_refs") or []):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"{got['id']}: sentence_refs are {got.get('sentence_refs')!r}, the row's are "
                        f"{want.get('sentence_refs')!r}"))
            continue
        n = (lesson.get("body") or "").count(f'<exercise ref="{got["id"]}"/>')
        if n != 1:
            out.append(("fail", C_NOT_APPLIED, addr,
                        f"the lesson body references {got['id']} {n} time(s) — the app renders an "
                        f"exercise only from an <exercise ref> node"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


def handle_card_production_keys(rows, sents, gram, table):
    """W27. Every production card must carry EXACTLY the key the table names, in the shipped export.

    Four claims per row, and three of them fail silently if the apply half-lands: the lesson exists
    and declares a card for this item, that card is a `production` card at all (a key on a card the
    learner is never asked to produce is a key nobody reads), it carries a `production_key`, and the
    prompt, the accept set (ORDER included — the table is exact-match, and a reordered set means the
    export was built from something other than this table), the sense index and the `verified` /
    `verified_by` stamps are the row's.

    The accept set is checked as a list rather than a set on purpose. It is derived, in a fixed
    order, from the record's `forms[]` minus the JMdict-tag strip; a difference in order can only
    come from a different derivation, and the point of an exact-match table is to catch that.
    """
    out = []
    for i, r in enumerate(rows):
        addr = f"{table} row {i}: {r['lesson']} / {r['item']}"
        lesson = LESSONS.get(r["lesson"])
        if lesson is None:
            out.append(("fail", C_NO_RECORD, addr, f"no lesson {r['lesson']} in the export"))
            continue
        cards = [c for c in (lesson.get("srs") or {}).get("introduces_cards") or []
                 if c.get("item") == r["item"]]
        if len(cards) != 1:
            out.append(("fail", C_NO_RECORD, addr,
                        f"the lesson declares {len(cards)} card(s) for {r['item']}, expected 1"))
            continue
        card = cards[0]
        if "production" not in (card.get("card_types") or []):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"card_types are {card.get('card_types')!r}: not a production card, so an "
                        f"answer key on it is unreachable"))
            continue
        key = card.get("production_key")
        if not key:
            out.append(("fail", C_NOT_APPLIED, addr, "the card carries no production_key"))
            continue
        if (key.get("prompt") or {}).get("pt-BR") != r["prompt"]["pt-BR"]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"prompt is {(key.get('prompt') or {}).get('pt-BR')!r}, the row's is "
                        f"{r['prompt']['pt-BR']!r}"))
            continue
        if list(key.get("accept") or []) != list(r["accept"]):
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"accept is {key.get('accept')!r}, the row's is {r['accept']!r}"))
            continue
        if key.get("sense_index") != r["sense_index"]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"sense_index is {key.get('sense_index')!r}, the row's is "
                        f"{r['sense_index']!r}"))
            continue
        if key.get("verified") != r["verified"] or key.get("verified_by") != r["verified_by"]:
            out.append(("fail", C_VALUE_MISMATCH, addr,
                        f"verified is {key.get('verified')!r}/{key.get('verified_by')!r}, the "
                        f"row's is {r['verified']!r}/{r['verified_by']!r}"))
            continue
        out.append(("ok", "", addr, "exact"))
    return out


REGISTRY = {
    "orthographic_relinks.json": handle_orthographic_relinks,
    "lesson_ref_addresses.json": handle_lesson_ref_addresses,
    "sentence_text_repairs.json": handle_sentence_text_repairs,
    "jargon_pass2_repairs.json": handle_jargon_pass2,
    "translation_defect_repairs.json": handle_translation_defect,
    "translation_followups.json": handle_translation_followups,
    "grammar_record_repairs.json": handle_grammar_record_repairs,
    "grammar_followups.json": handle_grammar_followups,
    "level_evidence_repairs.json": handle_level_evidence,
    "homograph_rulings.json": handle_homograph_rulings,
    "lesson_needs.json": handle_lesson_needs,
    "lesson_furigana.json": handle_lesson_furigana,
    "reading_passages.json": handle_reading_passages,
    "practice_kanji_exercises.json": handle_practice_exercises,
    "card_production_keys.json": handle_card_production_keys,
}


# ---------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO,
                    help="tree to validate (corpus/, course/, research/derived/repairs/)")
    ap.add_argument("--all", action="store_true", help="print every failure, not the first "
                                                       f"{MAX_REPORT} per class")
    ap.add_argument("--table", help="restrict to one table (diagnostics; never use in the gate)")
    args = ap.parse_args()
    root: Path = args.root.resolve()

    rdir = root / "research" / "derived" / "repairs"
    if not rdir.is_dir():
        die(f"repair table directory not found: {rdir}")
    present = sorted(p.name for p in rdir.glob("*.json"))
    if not present:
        die(f"{rdir} contains no repair tables — an empty table directory must never pass")
    unregistered = [n for n in present if n not in REGISTRY]
    if unregistered:
        die(f"unregistered repair table(s) {unregistered}: a new campaign's table must be "
            f"registered in REGISTRY with its addressing before it can be replayed")
    missing = [n for n in REGISTRY if n not in present]
    if missing:
        die(f"registered repair table(s) missing from {rdir}: {missing}")
    if len(present) < MIN_TABLES:
        die(f"{len(present)} repair tables, floor is {MIN_TABLES}")

    sents, gram, ncourse = load_export(root)
    print(f"export: {len(sents)} sentences, {len(gram)} grammar points, {ncourse} course files "
          f"(root {root})")

    LESSONS.update(load_lessons_export(root))
    EXEMPT.update(load_exempt(root))
    if len(LESSONS) < MIN_LESSONS:
        die(f"{len(LESSONS)} lesson leaves under {root}/course, floor is {MIN_LESSONS} — the "
            f"homograph rulings cannot be replayed against a course tree that is not there")
    print(f"        {len(LESSONS)} lesson leaves, {len(EXEMPT['coverage'])} coverage + "
          f"{len(EXEMPT['gating'])} gating exemptions (homograph-ruling replay)")

    READINGS.update(load_readings_export(root))
    if len(READINGS) < MIN_READINGS:
        die(f"{len(READINGS)} reading boxes under {root}/corpus/readings, floor is {MIN_READINGS} — "
            f"the W15 passages cannot be replayed against a registry that is not there")
    print(f"        {len(READINGS)} reading boxes (W15 passage replay)")

    VOCAB_BY_SLUG.update({slug: rec for slug, (ent, _f, rec) in load_levelled(root).items()
                          if ent == "vocab"})
    if len(VOCAB_BY_SLUG) < MIN_VOCAB:
        die(f"{len(VOCAB_BY_SLUG)} vocab records under {root}/corpus/vocab, floor is {MIN_VOCAB} — "
            f"the address rewrites cannot be replayed against a registry that is not there")

    LEVELLED.update(load_levelled(root))
    print(f"        {len(LEVELLED)} levelled records across "
          f"corpus/{{{','.join(LEVEL_REGISTRIES)}}} (level-evidence replay)")
    if not LEVELLED:
        die(f"no levelled record found under {root}/corpus/{{{','.join(LEVEL_REGISTRIES)}}} — the "
            f"level-evidence table cannot be replayed against a registry that is not there")

    tables: dict[str, list[dict]] = {name: read_table(rdir / name, name) for name in present}
    total_rows = sum(len(v) for v in tables.values())
    if total_rows < MIN_ROWS_TOTAL:
        die(f"{total_rows} repair rows across {len(tables)} tables, floor is {MIN_ROWS_TOTAL}")

    # The course tier addresses the corpus by id, with ONE sanctioned exception: the speaking units
    # embed the pt-BR translation of the sentence they cite (validate_speaking_path.py: "embedded
    # content derivable from the cited item"). An embedded copy is a second home for a repaired
    # string, so a repair that landed in `corpus/` and not in that copy leaves the course teaching
    # the defect. Assert the pre-repair text survives NOWHERE in the course tier.
    cvals = course_scalar_values(root)
    stale = []
    for name, rows in tables.items():
        for i, r in enumerate(rows):
            v = r.get("old")
            if isinstance(v, str) and len(v) >= 60 and v in cvals and v != r.get("new"):
                stale.append(f"{name} row {i} ({r.get('slug') or r.get('key')}): the PRE-repair "
                             f"`old` text is still a scalar in the course tier")
    if stale:
        for s in stale[:MAX_REPORT]:
            print(f"  [FAIL] {s}")
        die(f"{len(stale)} pre-repair value(s) survive as embedded copies under course/; the "
            f"repair reached corpus/ only")

    TABLES.update(tables)          # so `superseded_by` can resolve across campaigns

    # Cross-table chain index (see successor()). Sentence-addressed rows only: those are the ones
    # several campaigns collide on.
    for name, rows in tables.items():
        for i, r in enumerate(rows):
            if r.get("slug") and isinstance(r.get("old"), str) and isinstance(r.get("new"), str):
                CHAINS.setdefault((r["slug"], r["field"], r.get("locale")), []).append(
                    (name, i, r["old"], r["new"]))

    print()
    results: dict[str, list[tuple]] = {}
    for name in sorted(tables):
        if args.table and args.table not in name:
            continue
        results[name] = REGISTRY[name](tables[name], sents, gram, name)

    grand_ok = grand_fail = grand_skip = 0
    all_classes: Counter = Counter()
    samples: dict[str, list[str]] = defaultdict(list)

    for name in sorted(results):
        rows = results[name]
        # 1:1 with the table. A handler that silently dropped rows would certify them; this is the
        # empty-input rule applied per table.
        if len(rows) != len(tables[name]):
            die(f"{name}: handler produced {len(rows)} results for {len(tables[name])} rows — every "
                f"row must be checked exactly once")
        ok = sum(1 for s, *_ in rows if s == "ok")
        span = sum(1 for s, _, _, note in rows if s == "ok" and note == "span")
        skip = sum(1 for s, *_ in rows if s == "skip")
        bad = [r for r in rows if r[0] == "fail"]
        classes = Counter(c for _, c, _, _ in bad)
        all_classes.update(classes)
        for _, c, addr, detail in bad:
            samples[c].append(f"{addr}\n        {detail}")
        grand_ok += ok
        grand_fail += len(bad)
        grand_skip += skip
        cls_txt = ", ".join(f"{c}={n}" for c, n in sorted(classes.items())) or "-"
        print(f"  {name:34} rows={len(tables[name]):4}  PASS={ok:4} (span {span:3})  "
              f"SKIP={skip:2}  FAIL={len(bad):3}  [{cls_txt}]")

    print(f"\n  TOTAL rows={total_rows}  checks={grand_ok + grand_fail + grand_skip}  "
          f"PASS={grand_ok}  SKIP={grand_skip}  FAIL={grand_fail}")

    if all_classes:
        print("\n--- failures by root cause ---")
        for c, n in all_classes.most_common():
            print(f"\n  [{c}] × {n}")
            print(f"      fix: {FIXES.get(c, '(unclassified)')}")
            shown = samples[c] if args.all else samples[c][:MAX_REPORT]
            for s in shown:
                print(f"      - {s}")
            if len(samples[c]) > len(shown):
                print(f"      … {len(samples[c]) - len(shown)} more (--all)")

    if args.table:
        # Deliberately NOT exit 0: a partial run must never be mistakable for a green gate, in CI
        # or in a scrollback. --table is for reading one campaign, nothing else.
        print("\n[info] --table given: partial run, not the gate. Exit 2.")
        return 2

    if grand_fail:
        print(f"\nRESULT: FAIL — {grand_fail} repair row(s) the export does not carry, across "
              f"{len(all_classes)} root-cause class(es)")
        return 1

    print(f"\nRESULT: PASS — {grand_ok} rows replayed clean, {grand_skip} checked skips "
          f"(no-link + superseded_by + merged-away), 0 FAIL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
