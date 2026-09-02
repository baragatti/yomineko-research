#!/usr/bin/env python3
"""Give every topic its published ordinal: consecutive 1..N in module order, level by level.

WHY THIS EXISTS (W01)
---------------------
`topic.ord` is not decoration. `export_course.py` writes each topic's directory as
`topic-{ord:02d}-{slug tail}`, so the ordinal is part of the published path of every lesson file
underneath it — `course/n3/topic-38-conectores/lesson-01.json`.

Three scripts create topics, and all three append at `MAX(ord) + 1` over the WHOLE table:
`place_items.py`, `create_n3_topics.py` and `build_exam_kanji_lessons.py`. That is fine while a level
is being built in sequence, and wrong the moment a later step adds a topic that belongs to an EARLIER
level: `build_exam_kanji_lessons.py` creates `top:n5-kanji-exame` and `top:n4-kanji-exame` after the
N3 topics already exist, so the two exam topics land at 51 and 52 — after N3 — instead of at the end
of the levels they teach.

The committed export has them at 20 and 37, inside N5 and N4, with N4 shifted by one and N3 by two.
That renumbering really happened (`scripts/contracts/archive_orphan_topics.py` documents its
consequences: "when those levels were renumbered (n4 by +1, n3 by +2) the old directories stayed on
disk"), but it was applied straight to the database and never written down as a step, so a rebuild from
the tracked scripts produced `topic-36-conectores` where the repo has `topic-38-conectores` — 145 course
files exported under names nobody had ever committed. This is that missing step, and it is not a
transcript of a one-off fix: it states the rule the numbering was always meant to follow, so a topic
added to any level in the future lands in its own level instead of after the last one.

THE RULE. Sort by `(course_module.ord, topic.ord)` and hand out 1..N. Module order is the course order
(pre-n5, n5, n4, n3), and within a module the existing relative order is preserved — which puts an
appended exam-prep topic last inside its own level, exactly where the committed export has it. Run
against the live database it reproduces all 52 committed ordinals with nothing else to do.

Idempotent: a second run finds every topic already at its ordinal and writes nothing.
Usage: renumber_topics.py [--check]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would move; write nothing")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT t.id, t.slug, t.ord, m.level FROM topic t "
        "JOIN course_module m ON m.id = t.module_id ORDER BY m.ord, t.ord"
    ).fetchall()
    if not rows:
        print("[FAIL] no topics in the database — refusing to renumber nothing")
        return 1

    moves = [(tid, slug, old, new, level)
             for new, (tid, slug, old, level) in enumerate(rows, 1) if old != new]

    if not args.check:
        # Two passes: ord carries no UNIQUE constraint today, but parking the moved rows out of the
        # way first keeps this correct if one is ever added.
        for tid, _, _, new, _ in moves:
            con.execute("UPDATE topic SET ord=? WHERE id=?", (-new, tid))
        for tid, _, _, new, _ in moves:
            con.execute("UPDATE topic SET ord=? WHERE id=?", (new, tid))
        con.commit()

    for tid, slug, old, new, level in moves:
        print(f"  {slug:<28} [{level}] {old} -> {new}")
    verb = "would move" if args.check else "moved"
    print(f"renumber_topics: {len(rows)} topic(s) in module order; {verb} {len(moves)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
