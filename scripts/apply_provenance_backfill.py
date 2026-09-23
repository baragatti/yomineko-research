#!/usr/bin/env python3
"""W37 — apply the index half of the provenance backfill.

Reads `index_repairs` from `research/derived/repairs/provenance_backfill.json` (derived by
scripts/derive_provenance_backfill.py; nothing authored) and makes the four index writes the export's
provenance depends on (research/reports/w37_provenance_report.md §7.3):

  kanji.created_by            250 Layer-A KANJIDIC2 records stamped `ai` by the pt-BR meanings
                              campaign -> `dataset` (the AI claim moves to field_layers.meanings)
  vocab.source                vocab:1928100 still named the superseded 看護婦 entry
  localized_text.layer        NULL per-field layers on topic / course_module text -> the record's layer
  kanji_reading.needs_review  a reading flag whose note no longer exists -> 0

The exporters then publish `layer` / `source` / `created_by` / `field_layers` from the index; the
`rows` half of the same table is what scripts/validate/validate_repairs_applied.py asserts.

EXACT MATCH: each row's current value must be its `from` (written) or its `to` (already applied, left
alone); anything else refuses and nothing is committed. A partial index (no kanji) is out of scope.
Usage: apply_provenance_backfill.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_SCRIPTS = next(p for p in Path(__file__).resolve().parents if p.name == "scripts")
sys.path.append(str(_SCRIPTS))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
TABLE = ROOT / "research" / "derived" / "repairs" / "provenance_backfill.json"
NOTE_EXISTS = ("EXISTS (SELECT 1 FROM localized_text l WHERE l.entity_type='kanji_reading' "
               "AND l.entity_id=kanji_reading.id AND l.field='note')")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT COUNT(*) FROM kanji").fetchone()[0]:
        print("apply_provenance_backfill: partial index (no kanji) - out of scope, nothing to do")
        return 0

    problems: list[str] = []
    written = done = 0
    for r in doc["index_repairs"]:
        k = r["kind"]
        if k == "kanji.created_by":
            sel = ("SELECT created_by FROM kanji WHERE slug=?", (r["slug"],))
            upd = ("UPDATE kanji SET created_by=? WHERE slug=?", (r["to"], r["slug"]))
        elif k == "vocab.source":
            sel = ("SELECT source FROM vocab WHERE slug=?", (r["slug"],))
            upd = ("UPDATE vocab SET source=? WHERE slug=?", (r["to"], r["slug"]))
        elif k == "localized_text.layer":
            where = (f"entity_type=? AND locale='pt-BR' AND field=? AND entity_id="
                     f"(SELECT id FROM {r['entity_type']} WHERE slug=?)")
            args_ = (r["entity_type"], r["field"], r["slug"])
            sel = (f"SELECT layer FROM localized_text WHERE {where}", args_)
            upd = (f"UPDATE localized_text SET layer=? WHERE {where}", (r["to"], *args_))
        elif k == "kanji_reading.needs_review":
            # Only the note-less rows of this (kanji, reading, type): a noted twin keeps its flag.
            where = (f"kanji_id=(SELECT id FROM kanji WHERE slug=?) AND reading=? AND reading_type=? "
                     f"AND NOT {NOTE_EXISTS}")
            args_ = (r["slug"], r["reading"], r["reading_type"])
            got = [v for (v,) in con.execute(f"SELECT needs_review FROM kanji_reading WHERE {where}", args_)]
            flagged = sum(1 for v in got if v == r["from"])
            if flagged == 0 and got:
                done += 1
            elif flagged == r["rows"]:
                written += 1
                if not args.check:
                    con.execute(f"UPDATE kanji_reading SET needs_review=? WHERE {where}", (r["to"], *args_))
            else:
                problems.append(f"{k} {r['slug']} {r['reading']}: {flagged} flagged note-less row(s) of "
                                f"{len(got)}, table says {r['rows']}")
            continue
        else:
            problems.append(f"unknown repair kind {k!r}")
            continue
        got = con.execute(*sel).fetchall()
        if len(got) != 1:
            problems.append(f"{k} {r['slug']}: {len(got)} index row(s), expected 1")
        elif got[0][0] == r["to"]:
            done += 1
        elif got[0][0] == r["from"]:
            written += 1
            if not args.check:
                con.execute(*upd)
        else:
            problems.append(f"{k} {r['slug']}: index holds {got[0][0]!r}, table says from {r['from']!r}")

    if not args.check and not problems:
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"apply_provenance_backfill: {len(doc['index_repairs'])} index repair(s): {verb} {written}, "
          f"{done} already applied; {len(doc['rows'])} export row(s) for the validator")
    for p in problems[:15]:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS COMMITTED.")
        return 2
    return 1 if (args.check and written) else 0


if __name__ == "__main__":
    sys.exit(main())
