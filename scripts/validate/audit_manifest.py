#!/usr/bin/env python3
"""P7 — audit the exported 4-tier courseware manifest for cross-link + count integrity.

Walks manifest.json -> course.json -> topic.json -> lesson leaf, asserting every referenced `path` resolves to a
file, counts agree at each tier, lesson leaves carry a body + cumulative_known_set, and every sentence_ref in a
lesson resolves to a corpus sentence. Read-only. Exit non-zero on any FAIL. Usage: audit_manifest.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
COURSE = ROOT / "course"
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    fails: list[str] = []
    con = sqlite3.connect(DB)
    sent_slugs = {r[0] for r in con.execute("SELECT slug FROM sentence")}
    con.close()

    man = json.loads((COURSE / "manifest.json").read_text(encoding="utf-8"))
    total_lessons = 0
    total_topics = 0
    for c in man["courses"]:
        cpath = COURSE / c["path"]
        if not cpath.exists():
            fails.append(f"manifest course path missing: {c['path']}")
            continue
        cd = json.loads(cpath.read_text(encoding="utf-8"))
        topics = cd.get("topics", [])
        if len(topics) != c.get("topic_count"):
            fails.append(f"{c['id']}: topic_count {c.get('topic_count')} != {len(topics)} topics in course.json")
        total_topics += len(topics)
        course_lessons = 0
        for t in topics:
            tpath = cpath.parent / t["path"]
            if not tpath.exists():
                fails.append(f"{t['id']}: topic path missing: {t['path']}")
                continue
            td = json.loads(tpath.read_text(encoding="utf-8"))
            lessons = td.get("lessons", [])
            if len(lessons) != t.get("lesson_count"):
                fails.append(f"{t['id']}: lesson_count {t.get('lesson_count')} != {len(lessons)} in topic.json")
            course_lessons += len(lessons)
            for L in lessons:
                # lesson `path` is relative to the LEVEL dir (cpath.parent), e.g. "topic-01-orientacao/lesson-01.json"
                lp = L.get("path") or f"{t['path'].split('/')[0]}/lesson-{int(L.get('order', 0)):02d}.json"
                lpath = cpath.parent / lp
                if not lpath.exists():
                    fails.append(f"{L['id']}: lesson leaf missing: {lp}")
                    continue
                ld = json.loads(lpath.read_text(encoding="utf-8"))
                if not ld.get("body"):
                    fails.append(f"{L['id']}: empty body in leaf")
                if "cumulative_known_set" not in ld:
                    fails.append(f"{L['id']}: missing cumulative_known_set")
                for sref in ld.get("sentence_refs", []) or []:
                    if sref not in sent_slugs:
                        fails.append(f"{L['id']}: sentence_ref {sref} does not resolve")
        total_lessons += course_lessons
        if course_lessons != c.get("lesson_count"):
            fails.append(f"{c['id']}: lesson_count {c.get('lesson_count')} != {course_lessons} summed from topics")

    print(f"manifest audit: {total_topics} topics, {total_lessons} lessons across {len(man['courses'])} courses")
    if fails:
        print(f"=== {len(fails)} FAIL ===")
        for f in fails[:40]:
            print(f"  FAIL {f}")
        return 1
    print("=== 0 FAIL — manifest cross-links + counts consistent ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
