#!/usr/bin/env python3
"""W28 — write each SRS card's example sentence and cloze span into the index.

Applies `research/derived/repairs/card_examples.json`, derived by `scripts/derive_card_examples.py`
from the exported tree (no authoring). THE CONTENT IS IN THE TABLE and this script only places it in
`card_example` (migration 018); `scripts/export/export_course.py` joins it onto
`srs.introduces_cards[].example`. Nothing here touches a lesson body, an unlock or an exercise, so a
rendered-text diff of every lesson against HEAD shows only the new card field.

A row whose (lesson, item) is not a card the lesson issues is a stale table on the live index and
the run refuses. Off the live index (a replay) it is reported and skipped, as in
`apply_card_production_keys.py`, whose docstring records why a replay can address a card differently.

IDEMPOTENT: a row already in the index is left alone; a different value is a drift and is refused
unless --replace (the table is 100% derived, so the table wins).
Usage: apply_card_examples.py [--check] [--replace]
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
sys.path.append(str(_SCRIPTS / "export"))
from dbtarget import db_target  # noqa: E402
from export_course import _deref  # noqa: E402  (the exporter's own card addressing)

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
LIVE_INDEX = Path(DB).resolve() == (ROOT / "db" / "corpus.sqlite").resolve()
TABLE = ROOT / "research" / "derived" / "repairs" / "card_examples.json"
COLS = ("sentence", "cloze_start", "cloze_end", "cloze_answer", "why")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--replace", action="store_true", help="overwrite a row that differs, drop orphans")
    args = ap.parse_args()

    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT name FROM sqlite_master WHERE name='card_example'").fetchone():
        raise SystemExit("card_example is absent — run scripts/ingest/init_db.py (migration 018) first")
    if not con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0]:
        print("apply_card_examples: partial index (no lessons) — out of scope, nothing to do")
        return 0

    lid_by_slug = {s: i for i, s in con.execute("SELECT id,slug FROM lesson")}
    con.row_factory = sqlite3.Row
    issued = {(lid, _deref(con, ref, lid)) for lid, ref in con.execute(
        "SELECT lesson_id, ref FROM lesson_unlocks").fetchall()}
    con.row_factory = None

    problems: list[str] = []
    skipped: list[str] = []
    written = rewritten = 0
    want_keys: set[tuple[int, str]] = set()
    for r in doc["rows"]:
        lid = lid_by_slug.get(r["lesson"])
        if lid is None or (lid, r["item"]) not in issued:
            msg = f"{r['lesson']} / {r['item']}: the lesson issues no such card"
            (problems if LIVE_INDEX else skipped).append(msg)
            continue
        want_keys.add((lid, r["item"]))
        c = r["cloze"]
        want = (r["sentence"], c["start"], c["end"], c["answer"], r["why"])
        have = con.execute(f"SELECT {','.join(COLS)} FROM card_example WHERE lesson_id=? AND item=?",
                           (lid, r["item"])).fetchone()
        if have is not None and tuple(have) == want:
            continue
        if have is not None and not args.replace:
            problems.append(f"{r['lesson']} / {r['item']}: index carries {have[0]} "
                            f"{have[1]}-{have[2]}, table says {want[0]} {want[1]}-{want[2]}; "
                            f"pass --replace")
            continue
        written += have is None
        rewritten += have is not None
        if not args.check:
            con.execute(
                "INSERT INTO card_example (lesson_id,item,sentence,cloze_start,cloze_end,cloze_answer,why) "
                "VALUES (?,?,?,?,?,?,?) ON CONFLICT(lesson_id,item) DO UPDATE SET "
                "sentence=excluded.sentence, cloze_start=excluded.cloze_start, "
                "cloze_end=excluded.cloze_end, cloze_answer=excluded.cloze_answer, why=excluded.why",
                (lid, r["item"], *want))

    orphans = sorted({(lid, it) for lid, it in con.execute("SELECT lesson_id, item FROM card_example")}
                     - want_keys)
    for lid, item in orphans:
        if args.replace and not args.check:
            con.execute("DELETE FROM card_example WHERE lesson_id=? AND item=?", (lid, item))
        elif not args.replace and LIVE_INDEX:
            problems.append(f"lesson id {lid} / {item}: the index carries an example the table does not")

    if not args.check and not problems:
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"table: {doc['counts']}")
    print(f"{verb} {written} new example(s), {rewritten} rewrite(s) over {len(doc['rows'])} row(s); "
          f"{len(orphans)} orphan(s)" + (f"; {len(skipped)} row(s) address no card on this index"
                                         if skipped else ""))
    for s in skipped[:5]:
        print(f"  [replay] {s}")
    for p in problems[:15]:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS COMMITTED.")
        return 2
    return 1 if (args.check and (written or rewritten)) else 0


if __name__ == "__main__":
    sys.exit(main())
