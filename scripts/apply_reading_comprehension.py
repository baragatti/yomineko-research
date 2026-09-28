#!/usr/bin/env python3
"""W18: the in-lesson reading boxes ask their own comprehension question again.

W15 replaced 282 reading boxes with real passages and set `reading.comprehension.about_current_text`
to false on every one, because the 内容一致 question each box points at had been written about the
concatenation the box used to print. The renderer asks a question only when that flag is true, so
those boxes have asked nothing since. W18 regenerated `corpus/exam_banks/<level>_reading_comp.json`
from the questions W18b authored over the real passages (one per passage, independent verifier per
batch), gated by `build_reading_comp_bank.py` to each passage's OWN lesson known set, which is the set
the box is shown under. This step flips the flag back for every box whose question is in that bank,
and withdraws the pointer of a box whose question is no longer in any bank (one: the W18b verifier
rejected the new question for read:n4-oracoes-relativas-03-01 and its old one fails the W16 guards),
so no box points at an item that does not exist.

Table: research/derived/repairs/reading_comprehension.json, one row per box that changes:
`{slug, lesson, item, old, new}` with `old` / `new` the exact `comprehension` value before and after
(`new.item` null = withdrawn). The question text is not stored on the reading: `export_readings.py`
resolves it from the bank.

EXACT MATCH ON THE LIVE INDEX ONLY, as in apply_reading_passages.py (see its "`old.jp` IS A DRIFT
CHECK ON THE LIVE INDEX" section): a from-scratch replay builds a different, thinner set of boxes at
step 41, so there a box that is absent is skipped and a box at neither `old` nor `new` is written and
reported; `validate_index_rebuildable.py`'s byte diff is what checks a replay. On db/corpus.sqlite a
box at neither value is DRIFT and is refused.

`--derive` rebuilds the table from the live DB and the committed rc banks (the W18 run did this once;
the table is the committed input a rebuild replays). Idempotent. `--check` writes nothing.
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
from dbtarget import db_target  # noqa: E402

ROOT = _HERE.parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
LIVE_INDEX = Path(DB).resolve() == (ROOT / "db" / "corpus.sqlite").resolve()
TABLE = ROOT / "research" / "derived" / "repairs" / "reading_comprehension.json"
BANKS = ROOT / "corpus" / "exam_banks"


def derive(con: sqlite3.Connection) -> int:
    items = {}
    for f in sorted(BANKS.glob("n*_reading_comp.json")):
        for it in json.loads(f.read_text(encoding="utf-8")):
            items[it["reading"]] = it["id"]
    rows = []
    for slug, lesson, comp in con.execute(
            "SELECT slug, gated_to_lesson, comprehension FROM reading ORDER BY slug"):
        cur = json.loads(comp or "null") or {}
        item = items.get(slug)
        if item:
            if cur.get("about_current_text") is True and cur.get("item") == item:
                continue
            if cur.get("item") != item:
                raise SystemExit(f"{slug}: the box points at {cur.get('item')!r}, the bank's question "
                                 f"is {item!r}; refusing to re-point a box silently")
            rows.append({"slug": slug, "lesson": lesson, "item": item, "old": cur,
                         "new": {"item": item, "about_current_text": True}})
        elif cur.get("item"):
            rows.append({"slug": slug, "lesson": lesson, "item": cur["item"], "old": cur,
                         "new": {"item": None, "about_current_text": False}})
    doc = {"unit": "W18",
           "what": ("reading boxes whose W18b question is in the regenerated rc bank (flag back to true), "
                    "and boxes whose question is in no bank (pointer withdrawn)"),
           "row_count": len(rows), "rows": rows}
    TABLE.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"derived {len(rows)} rows -> {TABLE.relative_to(ROOT)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derive", action="store_true", help="rebuild the table from the DB + rc banks")
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    if args.derive:
        return derive(con)
    rows = json.loads(TABLE.read_text(encoding="utf-8"))["rows"]
    done = written = drift = absent = 0
    for r in rows:
        got = con.execute("SELECT comprehension FROM reading WHERE slug=?", (r["slug"],)).fetchone()
        if got is None:
            if LIVE_INDEX:
                drift += 1
                print(f"DRIFT {r['slug']}: no such box on the live index")
            else:
                absent += 1
            continue
        cur = json.loads(got[0] or "null")
        if cur == r["new"]:
            done += 1
            continue
        # Q4: a row whose `new` was amended by a later unit still accepts the value it wrote before
        # (`amended.was_new`) as a legitimate pre-state on the live index.
        if cur != r["old"] and cur != (r.get("amended") or {}).get("was_new"):
            if LIVE_INDEX:
                drift += 1
                print(f"DRIFT {r['slug']}: comprehension is {cur!r}, neither the row's old nor its new")
                continue
            print(f"  [replay] {r['slug']}: box holds {cur!r}, not the row's old; new value written")
        written += 1
        if not args.check:
            con.execute("UPDATE reading SET comprehension=? WHERE slug=?",
                        (json.dumps(r["new"], ensure_ascii=False), r["slug"]))
    if not args.check:
        con.commit()
    print(f"reading comprehension: {len(rows)} rows, {written} written, {done} already applied, "
          f"{absent} box(es) not built by this index, {drift} drifted"
          f"{' (check only)' if args.check else ''}")
    if drift:
        return 2
    return 1 if (args.check and written) else 0


if __name__ == "__main__":
    sys.exit(main())
