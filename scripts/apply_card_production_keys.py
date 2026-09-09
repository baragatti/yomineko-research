#!/usr/bin/env python3
"""W27 — write the production answer key onto every production card, in both layers.

WHAT WAS WRONG
--------------
`lesson.srs.introduces_cards[]` is derived from the unlock ledger, so it names a deck, an item and a
set of card kinds and says nothing about the card's CONTENT. For a `production` card that is the
whole card: the learner is shown a pt-BR cue and has to write the Japanese. 2,951 vocabulary
production cards had no cue and no answer key — G1 of `research/reports/readiness/srs_fsrs.md`, and
the reason `validate_card_content.py` could not exist. APP_PLAN W27.

WHAT THIS APPLIES
-----------------
`research/derived/repairs/card_production_keys.json`, built by `scripts/build_card_key_table.py`.
THE CONTENT IS IN THE TABLE and this script only places it: nothing here writes, rewrites or repairs
a prompt or an accept set. A row that does not address a card on the current tree is reported and
SKIPPED, never adapted.

2,938 rows are the W27 campaign's own, resolved through `corpus/vocab_redirects.json`; 13 are the
authoring residue the Fable sample asked for (8 records W09 re-pointed after the campaign, 5 unlocks
W11a created). Every row carries `verified: "sampled"` pointing at
`research/reports/w27_sample_report.md` — the claim is about the table (one verifier at authoring
time, then a 100-row sample), never about the individual row, and the teacher queue still owns it.

BOTH LAYERS
-----------
The authoring layer is the tracked table (the decision, exact-match, replayed by
`validate_repairs_applied.py`) plus `research/derived/card_key_residue.json` (the 13 authored rows);
this script writes the index `db/corpus.sqlite` (`card_production_key`, migration 016) and
`scripts/export/export_course.py` republishes `course/*/topic-*/lesson-*.json`, which is canonical.
Nothing here touches a lesson body, an unlock or an exercise: a rendered-text diff of every lesson
against git HEAD must show zero differences, and `srs.introduces_cards[]` gains one optional object
per production card and loses nothing.

WHY THE KEY IS NOT ON THE VOCABULARY RECORD
-------------------------------------------
A card is (lesson, item, kind). The sense a prompt names is the sense the INTRODUCING LESSON teaches
— 中 is "dentro" where `les:n5-comparacoes-02` unlocks it and would be something else in a lesson
that taught ちゅう — so the key belongs to the card, not to the entry. That is also why the table is
keyed (lesson, item) and why a row that loses its card is a failure rather than something to re-home.

A ROW THAT ADDRESSES NO CARD
---------------------------
On `db/corpus.sqlite` that is a stale table and the run refuses: every one of the 2,951 rows was
built from this index's own export. In a from-scratch replay it is not. `item` is a HEADWORD ref in
the authoring layer (`vocab:背`, `vocab:年`) and `export_course._deref` resolves it through the
identity resolver, which reads index state a replay does not reproduce -- so 背 lands on
`vocab:2147990` instead of `vocab:1472650` and 年 on `vocab:2084840` instead of `vocab:1468060` --
and `build_exam_kanji_lessons.py` re-chunks the eight `*-kanji-exame-*` lessons, so
`les:n4-kanji-exame-05` does not unlock 献花 there at all (the cause `apply_lesson_furigana.py`
already records for the same eight lessons). Three rows of 2,951. Off the live index those are
reported per row and skipped, and the other 2,948 are written; what checks a replay is the byte diff
in `validate_index_rebuildable.py`, which holds the three missing keys in its ratchet.

IDEMPOTENT. A card whose key is already the table's is left alone; a second run reports 0 changes.
A key that is present and DIFFERENT is a drift and is reported, not overwritten, unless --replace.

Run `scripts/export/export_course.py` afterwards.
Usage: apply_card_production_keys.py [--check] [--replace]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_SCRIPTS = next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")
_sys.path.append(str(_SCRIPTS))
_sys.path.append(str(_SCRIPTS / "export"))
from dbtarget import db_target  # noqa: E402
# The exporter's own dereferencer, imported rather than re-implemented: "which card does this lesson
# issue" must be the SAME question `export_course.py` answers when it builds `introduces_cards`, or
# the applier and the export disagree about one row and nobody finds out until the replay. A
# headword ref resolves through the identity resolver (level, lesson, printed reading), which a
# headword->slug map cannot reproduce — `vocab:０` alone needs three of those signals.
from export_course import _deref  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
# True only when this run targets db/corpus.sqlite -- the index the table was addressed against.
# See "A ROW THAT ADDRESSES NO CARD" in the docstring.
LIVE_INDEX = Path(DB).resolve() == (ROOT / "db" / "corpus.sqlite").resolve()
# The table is a committed INPUT to the rebuild, so it is read from the repo, never from --out-root.
TABLE = ROOT / "research" / "derived" / "repairs" / "card_production_keys.json"


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--replace", action="store_true",
                    help="rewrite a key that disagrees with the table instead of refusing. The key "
                         "is 100%% table-derived and `validate_repairs_applied.py` re-asserts it "
                         "against the export, so a disagreement is a stale index, never hand-"
                         "authored work to protect.")
    args = ap.parse_args()

    doc = load_table()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT name FROM sqlite_master WHERE name='card_production_key'").fetchone():
        raise SystemExit("card_production_key is absent — run scripts/ingest/init_db.py "
                         "(migration 016) before this applier")
    if not con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0]:
        # W10's rule: an apply script treats an index with nothing to apply INTO as out of scope,
        # so `validate_index_rebuildable --quick` (grammar family only, no lessons) does not abort.
        print("apply_card_production_keys: partial index (no lessons) — out of scope, nothing to do")
        return 0

    lid_by_slug = {s: i for i, s in con.execute("SELECT id,slug FROM lesson")}
    # A card exists only where the lesson unlocks the item, dereferenced exactly as the exporter
    # dereferences it. `sqlite3.Row` because `_deref` reaches back into the connection.
    con.row_factory = sqlite3.Row
    resolved: set[tuple[int, str]] = set()
    for lid, ref in con.execute(
            "SELECT lesson_id, ref FROM lesson_unlocks WHERE unlock_type='vocab'").fetchall():
        resolved.add((lid, _deref(con, ref, lid)))
    con.row_factory = None

    problems: list[str] = []
    unaddressed: list[str] = []
    written = 0
    rewritten = 0
    for r in doc["rows"]:
        lid = lid_by_slug.get(r["lesson"])
        if lid is None:
            problems.append(f"{r['lesson']}: no such lesson in the index")
            continue
        if (lid, r["item"]) not in resolved:
            msg = (f"{r['lesson']} / {r['item']}: the lesson does not unlock this item, so it "
                   f"issues no card for it; SKIPPED")
            (problems if LIVE_INDEX else unaddressed).append(
                msg if LIVE_INDEX else msg + " (precondition NOT ENFORCED -- target is not "
                                            "db/corpus.sqlite, where the table was addressed)")
            continue
        accept = json.dumps(r["accept"], ensure_ascii=False)
        want = (r["prompt"]["pt-BR"], accept, r["sense_index"], r["verified"],
                r["verified_by"], r["why"])
        have = con.execute(
            "SELECT prompt_pt, accept_json, sense_index, verified, verified_by, why "
            "FROM card_production_key WHERE lesson_id=? AND item=?", (lid, r["item"])).fetchone()
        if have is not None and tuple(have) == want:
            continue
        if have is not None and not args.replace:
            problems.append(f"{r['lesson']} / {r['item']}: the index already carries a different "
                            f"key ({have[0]!r} vs {want[0]!r}); pass --replace to overwrite")
            continue
        if have is None:
            written += 1
        else:
            rewritten += 1
        if not args.check:
            con.execute(
                "INSERT INTO card_production_key "
                "(lesson_id,item,prompt_pt,accept_json,sense_index,verified,verified_by,why) "
                "VALUES (?,?,?,?,?,?,?,?) "
                "ON CONFLICT(lesson_id,item) DO UPDATE SET prompt_pt=excluded.prompt_pt, "
                "accept_json=excluded.accept_json, sense_index=excluded.sense_index, "
                "verified=excluded.verified, verified_by=excluded.verified_by, why=excluded.why",
                (lid, r["item"], *want))

    # A key whose card is gone is a stale row, not a spare: it would export nowhere and it would make
    # the exact-match replay disagree with the index. Report it; --replace clears it.
    keys_in_db = {(lid, item) for lid, item in
                  con.execute("SELECT lesson_id, item FROM card_production_key")}
    want_keys = {(lid_by_slug[r["lesson"]], r["item"]) for r in doc["rows"]
                 if r["lesson"] in lid_by_slug}
    orphans = sorted(keys_in_db - want_keys)
    for lid, item in orphans:
        if args.replace:
            if not args.check:
                con.execute("DELETE FROM card_production_key WHERE lesson_id=? AND item=?",
                            (lid, item))
        elif LIVE_INDEX:
            problems.append(f"lesson id {lid} / {item}: the index carries a key this table does not")
        else:
            unaddressed.append(f"lesson id {lid} / {item}: the index carries a key this table does "
                               f"not (precondition NOT ENFORCED off the live index)")

    if not args.check and not problems:
        con.commit()
    con.close()

    verb = "would write" if args.check else "wrote"
    print(f"table: {doc['counts']}")
    print(f"{verb} {written} new key(s) and {rewritten} rewrite(s) over {len(doc['rows'])} row(s); "
          f"{len(orphans)} orphan(s)"
          + (f"; {len(unaddressed)} row(s) address no card on this index" if unaddressed else ""))
    for u in unaddressed[:5]:
        print(f"  [replay] {u}")
    if len(unaddressed) > 5:
        print(f"  [replay] ... and {len(unaddressed) - 5} more row(s) with no card on this index")
    for p in problems[:15]:
        print(f"  ! {p}")
    if len(problems) > 15:
        print(f"  … and {len(problems) - 15} more")
    if problems:
        print("\nNOTHING WAS COMMITTED — a row that does not address a live card is not written.")
        return 2
    return 1 if (args.check and (written or rewritten)) else 0


if __name__ == "__main__":
    sys.exit(main())
