#!/usr/bin/env python3
"""Pilot punch-list: add a bare `te-form` grammar anchor, link the te-form sentences + pilot
lesson to it, and recompute every sentence.level from its components. Idempotent."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from persist_dissection import recompute_all_levels  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    te_topic = cur.execute("SELECT id FROM topic WHERE slug='top:n5-te-form'").fetchone()[0]

    # 1) te-form grammar anchor
    row = cur.execute("SELECT id FROM grammar_point WHERE key='te-form'").fetchone()
    if row:
        gid = row[0]
        print(f"[skip] te-form anchor exists (id {gid})")
    else:
        cur.execute(
            "INSERT INTO grammar_point (slug,key,label_pt,structure_pattern,register,level,"
            "level_confidence,level_agreement,level_sources,references_json,source,created_by,layer,"
            "introducing_topic_id,needs_review) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("gram:te-form", "te-form", "forma て (conectiva)", "〜て", "neutral", "n5", 1.0, "anchor",
             json.dumps({"note": "course anchor for the て-form hub"}, ensure_ascii=False),
             json.dumps({"label_en": "te-form (connective)"}, ensure_ascii=False),
             "course-anchor", "ai", "C", te_topic, 1))
        gid = cur.lastrowid
        print(f"added te-form anchor (id {gid})")

    # 2) link all sentences that use a て connective particle to the anchor
    linked = 0
    for (sid,) in con.execute("SELECT id FROM sentence"):
        has_te = con.execute(
            "SELECT 1 FROM token WHERE sentence_id=? AND surface='て' AND pos_coarse='助詞' LIMIT 1",
            (sid,)).fetchone()
        if has_te:
            cur.execute("INSERT OR IGNORE INTO sentence_grammar (sentence_id,grammar_id,usage_note_pt) "
                        "VALUES (?,?,?)", (sid, gid, None))
            linked += cur.rowcount
    # link pilot lesson introduces -> te-form
    lid = con.execute("SELECT id FROM lesson WHERE slug='les:n5-te-form-01'").fetchone()
    if lid:
        cur.execute("INSERT OR IGNORE INTO lesson_introduces (lesson_id,member_type,member_id) "
                    "VALUES (?,?,?)", (lid[0], "grammar", gid))

    # 3) recompute sentence levels from components
    con.commit()
    n = recompute_all_levels(con)
    bylvl = dict(con.execute("SELECT level, COUNT(*) FROM sentence GROUP BY level"))
    print(f"te-form sentence links: {linked}; recomputed levels for {n} sentences -> {bylvl}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
