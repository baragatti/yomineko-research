#!/usr/bin/env python3
"""P6a — dump the grammar registry + topic reference for the placement-classification workflow.

Writes research/derived/grammar_to_place.json (every n5/n4 grammar point: key, level, pattern, label,
explanation snippet) + research/derived/topics_ref.json (the themed topic buckets, ordered). The workflow
agents Read these to classify each grammar point into the best dependency-respecting topic.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUTG = ROOT / "research" / "derived" / "grammar_to_place.json"
OUTT = ROOT / "research" / "derived" / "topics_ref.json"


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    grammar = []
    for g in con.execute(
            "SELECT id, key, level, structure_pattern FROM grammar_point WHERE level IN ('n5','n4') "
            "ORDER BY level, key"):
        expl = get_text(con, "grammar_point", g["id"], "explanation") or ""
        grammar.append({"key": g["key"], "level": g["level"], "pattern": g["structure_pattern"] or "",
                        "explanation": (expl[:200] + "…") if len(expl) > 200 else expl})
    topics = []
    for t in con.execute(
            "SELECT t.id, t.slug, t.ord, m.level FROM topic t JOIN course_module m ON m.id=t.module_id "
            "WHERE m.level IN ('n5','n4') AND t.slug NOT LIKE '%revisao' ORDER BY t.ord"):
        topics.append({"slug": t["slug"], "order": t["ord"], "level": t["level"],
                       "title": get_text(con, "topic", t["id"], "title"),
                       "theme": get_text(con, "topic", t["id"], "theme"),
                       "objectives": get_text(con, "topic", t["id"], "objectives") or []})
    OUTG.parent.mkdir(parents=True, exist_ok=True)
    OUTG.write_text(json.dumps(grammar, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTT.write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(grammar)} grammar -> {OUTG.name}; {len(topics)} content topics -> {OUTT.name}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
