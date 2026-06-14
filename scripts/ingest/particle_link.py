#!/usr/bin/env python3
"""P5 grammar deepening — deterministic links for fundamental PARTICLE grammar points.

A handful of grammar points are bare particles (は topic, が subject, を object, に, で, と, も, ね, よ, か,
や, の, な, さ, し, へ). Their structure_pattern is a single char, so the selection/agent path can't target
them — yet they occur in hundreds of already-dissected sentences. The token/particle tables (Layer A) already
identified every particle precisely, so we can link these grammar points deterministically. We cap each at
--target clean examples (shortest sentences first), enough to satisfy §10 ≥5 without flooding the graph.
The links are needs_review (teacher confirms topic-vs-contrast は etc.). Idempotent. Run with venv python.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"

# particle surface -> grammar_point.key
PARTICLE_MAP = {
    "は": "wa-topic-marker", "が": "ga", "を": "o-wo", "に": "ni", "で": "de", "と": "to",
    "も": "mo", "ね": "ne", "よ": "yo", "か": "ka", "や": "ya", "の": "no", "な": "na",
    "さ": "sa", "し": "shi", "へ": "gp-27",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=8, help="clean examples to link per particle point")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    cur = con.cursor()
    total = 0
    for surface, key in PARTICLE_MAP.items():
        row = cur.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
        if not row:
            print(f"  {surface}->{key}: (no grammar_point, skip)")
            continue
        gid = row[0]
        have = cur.execute("SELECT count(*) FROM sentence_grammar WHERE grammar_id=?", (gid,)).fetchone()[0]
        need = max(0, args.target - have)
        if need == 0:
            print(f"  {surface}->{key}: already {have}")
            continue
        # shortest sentences containing this particle, not already linked to this grammar point
        cands = cur.execute(
            "SELECT DISTINCT p.sentence_id FROM particle p JOIN sentence s ON s.id=p.sentence_id "
            "WHERE p.particle=? AND p.sentence_id NOT IN "
            "(SELECT sentence_id FROM sentence_grammar WHERE grammar_id=?) "
            "ORDER BY length(s.jp) ASC LIMIT ?", (surface, gid, need)).fetchall()
        for (sid,) in cands:
            cur.execute("INSERT OR IGNORE INTO sentence_grammar (sentence_id,grammar_id,usage_note_pt) "
                        "VALUES (?,?,?)", (sid, gid, None))
            total += 1
        print(f"  {surface}->{key}: had {have}, added {len(cands)} -> {have + len(cands)}")
    con.commit()
    con.close()
    print(f"particle_link: added {total} grammar edges")
    return 0


if __name__ == "__main__":
    sys.exit(main())
