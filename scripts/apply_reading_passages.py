#!/usr/bin/env python3
"""W15 — put the authored reading passages into the reading boxes, in both layers.

WHAT WAS WRONG
--------------
All 286 in-lesson reading boxes were ASSEMBLED, not written: `build_readings.py` picked i+0
sentences out of the bank and concatenated them, so `read:n5-adjetivos-04-01` printed
"どこに行くところですか。ありがとうございます！" — "Where are you going?" followed by "Thank you!" —
under a heading that calls it a Leitura. `design/reading_practice.md` §5 admitted the trade
("a themed set of true sentences, not a flowing story"); the readiness audit called it what it is,
and APP_PLAN W15 is the fix.

WHAT THIS APPLIES
-----------------
`research/derived/repairs/reading_passages.json`, built by `scripts/build_reading_passage_table.py`
from the 286 authored + independently verified Layer-C passages under `research/derived/passages/`.
Each row names the box, the exact `jp` it is replacing, and the passage that replaces it. A passage
that cannot pass the known-set gate is HELD in that table with the unlock its gating lesson is
missing — held is a W21b work item, never a rewrite of verified text.

BOTH LAYERS
-----------
The authoring layer is `research/derived/passages/*.json` (the text) plus the tracked table (the
decision, exact-match, replayed by `validate_repairs_applied.py`); this script writes the index
`db/corpus.sqlite` and `scripts/export/export_readings.py` republishes `corpus/readings/*.json`,
which is canonical. Nothing here edits a lesson: the `<reading ref>` tags and `reading_refs` that
`build_readings.py` wired into 235 lessons address these boxes by slug and no slug moves, so the
lessons' rendered PROSE is byte-identical afterwards — only the passage inside the box changes.

WHAT ELSE IT SETS
-----------------
  * `tokens` — re-derived from the new `jp` with the same SudachiPy mode-C path every other token
    stream uses (`dissect.Dissector`), and asserted to re-concatenate to `jp`. Never carried in the
    table: a token stream is derived, and a derived value in a repair table is a second source of
    truth waiting to drift.
  * `uses` — a SNAPSHOT of what this passage's own tokenisation resolved to, in row-id space (the
    exporter publishes it as `kanji:<char>` / `vocab:<jmdict_id>`). NOT a recompute from
    `sentence_kanji` / `sentence_vocab`: those link tables grow with every later dissection pass, and
    a full recompute would push already-gated boxes out of their lesson's known set — the same
    reasoning `apply_readings_composition_repairs.py` records for the selection-era boxes.
  * `source` — 'authored:w15-passages' on a replaced box, 'selection:sentence-bank' on one that was
    not replaced. Spec §1.1. Both are written on every run, because
    `validate_provenance_json.py` rule (e) expects a provenance field on ALL records of an entity
    once ANY record carries it.
  * `layer` / `ai_generated` / `needs_review` — an applied passage is Layer C, `ai_generated: true`,
    `needs_review: true`. It is authored Japanese; a teacher signs it off, not this script.
  * `comprehension` — the pointer to the box's own 内容一致 question in
    `corpus/exam_banks/<level>_reading_comp.json`, plus `about_current_text`. The question STRING
    stays in the bank (one source); the flag is false for every box this apply rewrites, because
    that question was authored against the concatenation that is now gone, and the renderer asks a
    question only when the flag is true. W18 regenerates those questions from the new passages, and
    the box picks them up with no second apply.

IDEMPOTENT. A row whose box already holds `new.jp` is recognised as applied. A row whose box holds
neither `old.jp` nor `new.jp` has DRIFTED: it is skipped LOUDLY, nothing is written for it, and the
run reports a non-zero problem count instead of guessing.

Run `scripts/export/export_readings.py` (or `export_corpus.py`) afterwards.
Usage: apply_reading_passages.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_HERE = Path(__file__).resolve()
sys.path.append(str(_HERE.parent))
sys.path.append(str(_HERE.parent / "ingest"))
from dbtarget import db_target                     # noqa: E402
from dissect import Dissector                      # noqa: E402

ROOT = _HERE.parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
# The table and the exam banks are read from the REPO, never from a redirected out-root: they are
# committed inputs to the rebuild, not artefacts a rebuild produces.
TABLE = ROOT / "research" / "derived" / "repairs" / "reading_passages.json"
BANKS = ROOT / "corpus" / "exam_banks"
SOURCE_APPLIED = "authored:w15-passages"
SOURCE_KEPT = "selection:sentence-bank"


TERM, CLOSE = "。！？!?", "」』）)"


def split_sentences(jp: str) -> list[str]:
    """Split on a terminator, taking any closing quote with it. A dialogue box terminates every line
    inside 「…。」, so a plain `split on 。` yields ONE unit for a six-line exchange; the closing
    bracket has to travel with the terminator. Used only for a box W15 did not replace — an authored
    passage carries the segmentation its author wrote."""
    out, start, i = [], 0, 0
    while i < len(jp):
        if jp[i] in TERM:
            j = i + 1
            while j < len(jp) and jp[j] in CLOSE:
                j += 1
            out.append(jp[start:j])
            start = i = j
        else:
            i += 1
    if jp[start:].strip():
        out.append(jp[start:])
    return [s for s in out if s.strip()]


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc


def rc_items() -> dict[str, str]:
    """read: slug -> the id of the authored 内容一致 item that belongs to it."""
    out: dict[str, str] = {}
    for f in sorted(BANKS.glob("*_reading_comp.json")):
        for it in json.loads(f.read_text(encoding="utf-8")):
            if it.get("reading"):
                out[it["reading"]] = it["id"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    doc = load_table()
    rows = {r["slug"]: r for r in doc["rows"]}
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT name FROM sqlite_master WHERE name='reading'").fetchone():
        print("apply_reading_passages: no reading table (build_readings.py has not run) — nothing to do")
        return 0
    cols = {r[1] for r in con.execute("PRAGMA table_info(reading)")}
    for missing in ("source", "comprehension", "sentences"):
        if missing not in cols:
            raise SystemExit(f"reading.{missing} is absent — run scripts/ingest/init_db.py "
                             f"(migrations 014/015) before this applier")

    kid_by_char = {c: i for c, i in con.execute("SELECT character,id FROM kanji")}
    vid_by_slug = {s: i for i, s in con.execute("SELECT id,slug FROM vocab")}
    questions = rc_items()
    d = Dissector(db=Path(DB))

    problems: list[str] = []
    changed_boxes = 0
    stamped = 0
    applied_now = 0
    for slug, level, jp in list(con.execute("SELECT slug,level,jp FROM reading ORDER BY slug")):
        row = rows.get(slug)
        replaced = row is not None
        target_jp = row["new"]["jp"] if replaced else jp
        if replaced and jp not in (row["old"]["jp"], row["new"]["jp"]):
            problems.append(f"{slug}: the box holds neither the table's `old` nor its `new` jp — "
                            f"it drifted after the table was built; SKIPPED")
            continue

        fields: dict = {}
        if replaced:
            n = row["new"]
            # `pos` is the NEUTRAL enum (dissect.POS_MAP), never the raw Sudachi 品詞: that is what
            # the token stream has always carried, what contracts/reading.schema.json's vocabulary is
            # parsed from, and what the renderer reads. `noun` is the fallback for a POS the map does
            # not cover, which is the same default the sentence-side token writer uses.
            toks = [{"s": t["surface"], "r": t["reading"], "ro": t["romaji"],
                     "pos": t["pos"] or "noun"}
                    for t in d.skeleton(target_jp)["tokens"]]
            if "".join(t["s"] for t in toks) != target_jp:
                problems.append(f"{slug}: re-derived tokens do not re-concatenate to jp; SKIPPED")
                continue
            unknown = [s for s in n["uses"]["vocab"] if s not in vid_by_slug]
            if unknown:
                problems.append(f"{slug}: uses names {len(unknown)} vocab slug(s) the index does not "
                                f"carry ({unknown[:3]}); SKIPPED")
                continue
            if "".join(n["jp_sentences"]) != target_jp:
                problems.append(f"{slug}: jp_sentences do not re-concatenate to jp; SKIPPED")
                continue
            fields.update({
                "jp": target_jp,
                "sentences": json.dumps(n["jp_sentences"], ensure_ascii=False),
                "tokens": json.dumps(toks, ensure_ascii=False),
                "translation_pt": n["translation_pt"],
                "translation_en": n["translation_en"],
                "title_pt": n["title_pt"],
                "title_en": n["title_en"],
                "length_band": n["length_band"],
                "uses": json.dumps({
                    "kanji": sorted(kid_by_char[k] for k in n["uses"]["kanji"] if k in kid_by_char),
                    "vocab": sorted(vid_by_slug[s] for s in n["uses"]["vocab"]),
                }, ensure_ascii=False),
                "source_slugs": json.dumps(n["source_slugs"], ensure_ascii=False),
                "ai_generated": 1,
                "needs_review": 1,
                "layer": "C",
                "source": SOURCE_APPLIED,
            })
        else:
            fields["source"] = SOURCE_KEPT
            fields["sentences"] = json.dumps(split_sentences(jp), ensure_ascii=False)

        item = questions.get(slug)
        fields["comprehension"] = json.dumps(
            {"item": item, "about_current_text": not replaced}, ensure_ascii=False)

        have = dict(zip([c[0] for c in con.execute(
            f"SELECT {','.join(fields)} FROM reading WHERE slug=?", (slug,)).description],
            con.execute(f"SELECT {','.join(fields)} FROM reading WHERE slug=?", (slug,)).fetchone()))
        delta = {k: v for k, v in fields.items() if have.get(k) != v}
        if not delta:
            continue
        if "jp" in delta:
            applied_now += 1
        if set(delta) <= {"source", "comprehension", "sentences"}:
            stamped += 1
        else:
            changed_boxes += 1
        if not args.check:
            con.execute(f"UPDATE reading SET {','.join(k + '=?' for k in delta)} WHERE slug=?",
                        (*delta.values(), slug))

    if not args.check and not problems:
        con.commit()
    counts = doc["counts"]
    con.close()

    verb = "would write" if args.check else "wrote"
    print(f"table: {counts}")
    print(f"{verb} {changed_boxes} rewritten box(es) ({applied_now} whose jp moved this run) and "
          f"{stamped} provenance-only stamp(s); {len(doc['held'])} held")
    for h in doc["held"]:
        miss = ", ".join(f"{m['ref']}" + (f" ({m.get('headword')})" if m.get("headword") else "")
                         for m in h["missing_unlocks"]) or "; ".join(h["reasons"])
        print(f"  HELD {h['slug']} -> {h['lesson']} needs {miss}")
    for p in problems[:15]:
        print(f"  ! {p}")
    if len(problems) > 15:
        print(f"  … and {len(problems) - 15} more")
    if problems:
        print("\nNOTHING WAS COMMITTED — a box that does not match the table is not rewritten.")
        return 2
    return 1 if (args.check and (changed_boxes or stamped)) else 0


if __name__ == "__main__":
    sys.exit(main())
