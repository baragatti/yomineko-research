#!/usr/bin/env python3
"""P7 — audit lesson coverage of the corpus: every PLACED item unlocked by exactly one lesson, no over-reach.

For vocab / kanji / grammar, compares the set of items PLACED in a topic (introducing_topic_id set) against the
set UNLOCKED by some lesson (lesson_unlocks). Reports, per kind:
  - placed-but-NOT-unlocked  = coverage gap (a placed item no lesson teaches) -> FAIL
  - unlocked-but-NOT-placed  = an item taught without a topic placement (cosmetic metadata) -> WARN
Also flags any item unlocked by MORE than one lesson (introduce-once violation) -> FAIL. Read-only; exits
non-zero on any FAIL. Usage: audit_coverage.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
KINDS = [("vocab", "vocab", "headword"), ("kanji", "kanji", "character"), ("grammar", "grammar_point", "key")]


def main() -> int:
    con = sqlite3.connect(DB)
    fails = 0
    warns = 0
    for kind, tbl, col in KINDS:
        placed = {r[0] for r in con.execute(
            f"SELECT {col} FROM {tbl} WHERE introducing_topic_id IS NOT NULL")}
        unlock_rows = [r[0] for r in con.execute(
            "SELECT ref FROM lesson_unlocks WHERE unlock_type=?", (kind,))]
        unlocked = set()
        for r in unlock_rows:
            ident = r.split(":", 1)[1] if ":" in r else r
            if ident.isdigit():  # numeric ref -> map to col value (headword/character/key) so it matches `placed`
                row = con.execute(f"SELECT {col} FROM {tbl} WHERE id=?", (int(ident),)).fetchone()
                if row:
                    ident = row[0]
            unlocked.add(ident)
        # introduce-once in EXPORT space: DB refs are authoring headwords, and one headword can
        # legitimately be unlocked by two lessons that mean different homograph records; the exported
        # slug is the identity. (Slug-space uniqueness is the rule the export itself now enforces with
        # a hard SystemExit on within-lesson duplicates.)
        per_ref = Counter()
        for lf in (ROOT / "course").glob("*/topic-*/lesson-*.json"):
            dd = json.loads(lf.read_text(encoding="utf-8"))
            for uu in dd.get("unlocks", []):
                if uu["type"] == kind:
                    per_ref[uu["ref"]] += 1
        dup = {r: n for r, n in per_ref.items() if n > 1}
        gap = placed - unlocked
        extra = unlocked - placed
        print(f"== {kind} ==  placed={len(placed)} unlocked={len(unlocked)} "
              f"gap={len(gap)} unplaced={len(extra)} dup={len(dup)}")
        if gap:
            fails += 1
            print(f"   FAIL placed-but-not-unlocked: {sorted(gap)[:20]}")
        if dup:
            fails += 1
            print(f"   FAIL introduce-once (unlocked by >1 lesson): {dict(list(dup.items())[:20])}")
        if extra:
            warns += 1
            print(f"   WARN unlocked-but-not-placed (taught w/o placement): {sorted(extra)[:20]}")
    con.close()
    print(f"=== coverage audit: {fails} FAIL, {warns} WARN ===")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
