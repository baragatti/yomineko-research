#!/usr/bin/env python3
"""Fill cheap derivable gaps found by the completeness audit:
  1. kanji_reading.example_vocab_ids — leveled vocab using each on/kun reading (§5.1, acceptance #1).
  2. grammar_related — populate from contrast_pair families (§5.3 related_point_ids).
Idempotent. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import jaconv

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def hira(s):
    return jaconv.kata2hira(s or "")


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # 1) example_vocab_ids per on/kun reading
    n_ex = 0
    rows = con.execute(
        "SELECT kr.id, kr.reading, kr.okurigana, k.character FROM kanji_reading kr "
        "JOIN kanji k ON k.id=kr.kanji_id WHERE k.level IS NOT NULL AND kr.reading_type!='nanori'")
    for rid, reading, okuri, ch in rows.fetchall():
        frag = hira(reading).strip("-").strip(".") + (hira(okuri).strip("-") if okuri else "")
        if not frag:
            continue
        # leveled vocab containing this kanji whose kana contains the reading fragment
        cand = con.execute(
            "SELECT id, headword, kana FROM vocab WHERE level IN ('n5','n4') AND headword LIKE ? "
            "ORDER BY freq_rank IS NULL, freq_rank", (f"%{ch}%",)).fetchall()
        hits = [vid for vid, hw, kana in cand
                if (len(frag) >= 2 and frag in hira(kana)) or (len(frag) == 1 and hira(kana) == frag)][:4]
        if hits:
            cur.execute("UPDATE kanji_reading SET example_vocab_ids=? WHERE id=?",
                        (json.dumps(hits), rid))
            n_ex += 1

    # 2) grammar_related from contrast_pair families
    n_rel = 0
    for (fid,) in con.execute("SELECT id FROM family WHERE type='contrast_pair'"):
        members = [m[0] for m in con.execute(
            "SELECT member_id FROM family_member WHERE family_id=? AND member_type='grammar'", (fid,))]
        for i in range(len(members)):
            for j in range(len(members)):
                if i != j:
                    cur.execute("INSERT OR IGNORE INTO grammar_related (grammar_id,related_grammar_id,relation) "
                                "VALUES (?,?,?)", (members[i], members[j], "contrast"))
                    n_rel += cur.rowcount
    con.commit()
    print(f"example_vocab_ids set on {n_ex} readings; grammar_related contrast links added: {n_rel}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
