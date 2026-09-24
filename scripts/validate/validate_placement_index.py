#!/usr/bin/env python3
"""Gate (W23): course/item_lesson_index.json is exactly what the rule derives, and covers the banks.

design/assessment.md §5.1. The index is a CACHE (question id -> the lesson that first makes it
answerable), so its one real check is that scripts/export/build_item_lesson_index.py reproduces it
byte for byte from the exported tree. Plus a coverage ratchet: exam items placed may not fall below
EXAM_FLOOR (re-measured on the W18-regenerated banks: 4,970 of 5,141; the 171 left are listening items
with no key and stragglers), and every lesson exercise must be indexed.
Plant proof (research/reports/w23_apply_report.md): an entry pointed at another lesson, and a removed
entry, each FAIL.
Usage: validate_placement_index.py [--root PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "export"))
import build_item_lesson_index as bili  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]
# P1-exam-fixes (2026-09-23), re-recorded with cause: 4970 -> 4932. The builder rules dropped 39
# n5 grammar_form items and the rebuild added 1 n4 text_grammar item (5141 -> 5103 items); the
# unplaced count is unchanged at 171. research/reports/p1_exam_fixes_report.md.
# Q1-exam-fixes-3 (2026-09-23), re-recorded with cause: 4932 -> 4700. context_fill got the
# stem-sufficiency rules and 185 second-key / key-defect items were withdrawn by ledger
# (5103 -> 4871 items); unplaced unchanged at 171. research/reports/q1_exam_fixes_3_report.md.
# Q2-token-links (2026-09-23), re-recorded with cause: 4700 -> 4696. The relinked tokens and the 62
# repair-driven sentence re-levels (research/derived/repairs/token_link_repairs.json) take some items'
# sentences out of their bank's taught set or level, so the rebuilt banks hold 4871 -> 4867 items
# (n5 context_fill 93 -> 91, n5 sentence_order 58 -> 55, n4 context_fill 317 -> 318); unplaced
# unchanged at 171. research/reports/q2_token_links_report.md.
EXAM_FLOOR = 4696
MIN_EXERCISES = 2000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    args = ap.parse_args()
    root = Path(args.root).resolve()
    fails: list[str] = []
    path = root / bili.OUT_REL
    if not path.exists():
        print(f"validate_placement_index: FAIL {bili.OUT_REL} missing")
        return 1
    have = json.loads(path.read_text(encoding="utf-8"))
    want = bili.build(root)
    if path.read_text(encoding="utf-8") != bili.render(want):
        diff = sorted(k for k in set(have) | set(want) if have.get(k) != want.get(k))
        fails.append(f"{bili.OUT_REL} is not what build_item_lesson_index.py derives on this tree: "
                     f"{len(diff)} entr(y|ies) differ, e.g. {diff[:3]}")
    n_ex = sum(1 for v in have.values() if v.get("via") == "exercise")
    n_exam = len(have) - n_ex
    if n_exam < EXAM_FLOOR:
        fails.append(f"exam items placed {n_exam} < floor {EXAM_FLOOR} (coverage may not fall)")
    if n_ex < MIN_EXERCISES:
        fails.append(f"only {n_ex} lesson exercises indexed (floor {MIN_EXERCISES})")
    if n_exam > EXAM_FLOOR:
        print(f"  ADVISORY: exam coverage {n_exam} > floor {EXAM_FLOOR}; raise EXAM_FLOOR")
    for f in fails:
        print(f"  FAIL {f}")
    print(f"\nvalidate_placement_index: {len(have)} questions ({n_ex} exercises, {n_exam} exam items) | "
          f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
