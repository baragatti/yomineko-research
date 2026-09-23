#!/usr/bin/env python3
"""W23 — write every lesson exercise's `item_refs` into both layers.

Applies `research/derived/repairs/item_refs.json`, derived by `scripts/derive_item_refs.py` from the
exported tree (design/assessment.md §2.2; nothing authored). THE CONTENT IS IN THE TABLE; this script
places it:
  * the index: `exercise_item_ref` (migration 019), keyed on the exercise slug, which
    `scripts/export/export_course.py` joins onto `lesson.exercises[].item_refs`;
  * the authoring source: `research/derived/lessons/<lesson>.json` `exercises[].item_refs`, the field
    `load_lessons.py` has always read and every authoring file carried empty.
An exercise with no row gets `item_refs: []` in the source (exempt or residue, see the derivation).
Nothing touches a body, an unlock, an answer or a prompt.

A row whose exercise is not in the index is a stale table on the live index and the run refuses; off
the live index (a replay) it is reported and skipped, as in `apply_card_examples.py`.

IDEMPOTENT: an exercise whose refs already match is left alone; a different set is a drift and is
refused unless --replace (the table is 100% derived, so the table wins).
Usage: apply_item_refs.py [--check] [--replace]
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
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
LIVE_INDEX = Path(DB).resolve() == (ROOT / "db" / "corpus.sqlite").resolve()
TABLE = ROOT / "research" / "derived" / "repairs" / "item_refs.json"
SRC = out_root(ROOT) / "research" / "derived" / "lessons"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--replace", action="store_true", help="overwrite a set that differs, drop orphans")
    args = ap.parse_args()

    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT name FROM sqlite_master WHERE name='exercise_item_ref'").fetchone():
        raise SystemExit("exercise_item_ref is absent — run scripts/ingest/init_db.py (migration 019) first")
    if not con.execute("SELECT COUNT(*) FROM exercise").fetchone()[0]:
        print("apply_item_refs: partial index (no exercises) — out of scope, nothing to do")
        return 0

    in_index = {s for (s,) in con.execute("SELECT slug FROM exercise")}
    have: dict[str, set[tuple]] = {}
    for ex, t, ref, role, by in con.execute(
            "SELECT exercise, item_type, ref, role, derived_by FROM exercise_item_ref"):
        have.setdefault(ex, set()).add((t, ref, role, by))

    problems: list[str] = []
    skipped: list[str] = []
    want: dict[str, list[dict]] = {}
    written = rewritten = 0
    for r in doc["rows"]:
        if r["exercise"] not in in_index:
            msg = f"{r['exercise']} ({r['lesson']}): no such exercise in the index"
            (problems if LIVE_INDEX else skipped).append(msg)
            continue
        want[r["exercise"]] = r["item_refs"]
        rows = {(e["type"], e["ref"], e["role"], e["derived_by"]) for e in r["item_refs"]}
        cur = have.get(r["exercise"])
        if cur == rows:
            continue
        if cur and not args.replace:
            problems.append(f"{r['exercise']}: index carries {sorted(cur)[:2]}…, table says "
                            f"{sorted(rows)[:2]}…; pass --replace")
            continue
        written += cur is None
        rewritten += cur is not None
        if not args.check:
            con.execute("DELETE FROM exercise_item_ref WHERE exercise=?", (r["exercise"],))
            con.executemany("INSERT INTO exercise_item_ref (exercise,item_type,ref,role,derived_by) "
                            "VALUES (?,?,?,?,?)", [(r["exercise"], *x) for x in sorted(rows)])

    orphans = sorted(set(have) - set(want))
    for ex in orphans:
        if args.replace and not args.check:
            con.execute("DELETE FROM exercise_item_ref WHERE exercise=?", (ex,))
        elif not args.replace and LIVE_INDEX:
            problems.append(f"{ex}: the index carries item refs the table does not")

    # ---- the authoring source ----------------------------------------------------------------
    # Pre-W23 authored refs that resolve to nothing stay in the source verbatim (not exported).
    keep: dict[str, list[dict]] = {}
    for u in doc.get("authored_unresolved") or []:
        keep.setdefault(u["id"], []).append({"type": u["type"], "ref": u["ref"]})
    src_changed = 0
    for f in sorted(SRC.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        dirty = False
        for ex in d.get("exercises") or []:
            refs = want.get(ex.get("slug"), []) + keep.get(ex.get("slug"), [])
            if ex.get("item_refs") != refs:
                ex["item_refs"] = refs
                dirty = True
        if dirty:
            src_changed += 1
            if not args.check and not problems:
                f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not args.check and not problems:
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"table: {json.dumps({k: doc['counts'][k] for k in ('with_target', 'exempt', 'residue', 'target_refs')})}")
    print(f"{verb} {written} new + {rewritten} rewritten exercise ref set(s) over {len(doc['rows'])} "
          f"row(s); {len(orphans)} orphan(s); {src_changed} authoring file(s)"
          + (f"; {len(skipped)} row(s) address no exercise on this index" if skipped else ""))
    for s in skipped[:5]:
        print(f"  [replay] {s}")
    for p in problems[:15]:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS COMMITTED.")
        return 2
    return 1 if (args.check and (written or rewritten or src_changed)) else 0


if __name__ == "__main__":
    sys.exit(main())
