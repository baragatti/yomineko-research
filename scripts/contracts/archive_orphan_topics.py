#!/usr/bin/env python3
"""Move the unreachable pre-renumbering topic directories out of course/ into archive/.

course/n3 and course/n4 each hold two copies of every topic. When those levels were renumbered (n4 by
+1, n3 by +2) the old directories stayed on disk, so 31 topic ids and 192 lesson ids each answer to two
files. That breaks the one rule the whole graph rests on — a record has one stable id (spec §1.7) — and
it is why an API cannot serve `/lessons/les:n3-conectores-01`.

Nothing is deleted. The directories move to archive/, keeping their git history, and the move is
recorded in archive/ARCHIVE.md together with the audit that justified it.

SCOPE IS DELIBERATELY HARD-CODED to n3 and n4. Deriving the unreachable set generically from
`course.json -> topics[].path` returns 43 directories, not 31: the Fala Primeiro path
(course/speak/*) addresses its units through `stages[].unit_ids` and has no `topics` key at all, so a
generic rule reads the entire live Speak course as unreachable and archives it. The check below fails
loudly rather than moving anything if the computed set does not match the audited one.

Usage: archive_orphan_topics.py [--check]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "archive" / "course-pre-renumber-2026-06-26"
LEVELS = ("n3", "n4")            # never "speak" — see the module docstring
EXPECTED = 31


def unreachable() -> list[Path]:
    out: list[Path] = []
    for level in LEVELS:
        root = ROOT / "course" / level / "course.json"
        if not root.exists():
            print(f"  ! {root} missing", file=sys.stderr)
            return []
        referenced = {
            (root.parent / t["path"]).resolve()
            for t in json.loads(root.read_text(encoding="utf-8")).get("topics", [])
        }
        for tj in sorted(root.parent.glob("topic-*/topic.json")):
            if tj.resolve() not in referenced:
                out.append(tj.parent)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    dirs = unreachable()
    if len(dirs) != EXPECTED:
        print(f"ABORT: found {len(dirs)} unreachable directories, expected {EXPECTED}. The tree has "
              f"changed since the audit — re-audit before moving anything.", file=sys.stderr)
        for d in dirs:
            print(f"   {d.relative_to(ROOT)}", file=sys.stderr)
        return 2

    nfiles = sum(1 for d in dirs for _ in d.rglob("*") if _.is_file())
    print(f"{len(dirs)} unreachable topic directories, {nfiles} files")
    for d in dirs:
        print(f"   {str(d.relative_to(ROOT)).replace(chr(92), '/')}")
    if args.check:
        print("\n--check: nothing moved")
        return 0

    DEST.mkdir(parents=True, exist_ok=True)
    moved = 0
    for d in dirs:
        target = DEST / d.parent.name / d.name
        target.parent.mkdir(parents=True, exist_ok=True)
        # git mv keeps the history attached to the files rather than recording a delete plus an add.
        r = subprocess.run(["git", "mv", str(d.relative_to(ROOT)),
                            str(target.relative_to(ROOT))],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode:
            print(f"  ! git mv failed for {d.relative_to(ROOT)}: {r.stderr.strip()}", file=sys.stderr)
            return 1
        moved += 1
    print(f"\nmoved {moved} directories -> {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
