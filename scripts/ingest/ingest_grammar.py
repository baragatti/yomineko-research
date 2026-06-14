#!/usr/bin/env python3
"""P4 prerequisite — ingest the reconciled N5/N4 grammar-point ENUMERATION into grammar_point.

Reads research/datasets/grammar/grammar_points.json (compiled from >=3 reputable sources;
membership is factual, explanations are authored later in Layer C). Stores the point list with
level + confidence/agreement/sources; explanation_pt/formation_pt/nuance_pt stay NULL until P6
authoring. Idempotent. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research" / "datasets" / "grammar" / "grammar_points.json"
DB = ROOT / "db" / "corpus.sqlite"


def slugify(key: str) -> str:
    s = "".join(c if (c.isalnum() or c in "-_") else "-" for c in (key or "").strip().lower())
    return "gram:" + (s.strip("-") or "x")


def main() -> int:
    if not SRC.exists():
        print(f"[wait] {SRC.relative_to(ROOT)} not present yet (grammar agent still running?)")
        return 1
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    if con.execute("SELECT COUNT(*) FROM grammar_point").fetchone()[0] > 0:
        print(f"[skip] grammar_point already populated "
              f"({con.execute('SELECT COUNT(*) FROM grammar_point').fetchone()[0]})")
        return 0
    points = json.loads(SRC.read_text(encoding="utf-8"))
    cur = con.cursor()
    seen: set[str] = set()
    n = 0
    for p in points:
        key = (p.get("key") or p.get("pattern") or "").strip()
        if not key:
            continue
        slug = slugify(key)
        if slug in seen:  # de-dupe
            continue
        seen.add(slug)
        lvl_sources = p.get("level_sources") or {}
        level = (p.get("level") or "").strip().lower() or None
        if level is None and lvl_sources:
            level = "n5" if "n5" in lvl_sources.values() else "n4"
        if lvl_sources:
            n_for = sum(1 for v in lvl_sources.values() if v == level)
            total = len(lvl_sources)
            conf, agree = round(n_for / total, 3), f"{n_for}/{total}"
        else:
            conf, agree = None, None
        refs = json.dumps({"label_en": p.get("label"), "also_known_as": p.get("also_known_as", []),
                           "level_sources": lvl_sources}, ensure_ascii=False)
        cur.execute(
            "INSERT INTO grammar_point (slug,key,label_pt,structure_pattern,register,explanation_pt,"
            "formation_pt,nuance_pt,references_json,level,level_confidence,level_agreement,level_sources,"
            "source,created_by,layer,needs_review) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (slug, key, None, p.get("pattern"), None, None, None, None, refs,
             level, conf, agree, json.dumps(lvl_sources, ensure_ascii=False),
             "community-grammar-lists", "ai", "C", 1))
        n += 1
    con.commit()
    by_lvl = dict(con.execute("SELECT level, COUNT(*) FROM grammar_point GROUP BY level"))
    print(f"grammar points ingested: {n} (by level {by_lvl})")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
