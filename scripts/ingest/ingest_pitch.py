#!/usr/bin/env python3
"""P2b — ingest pitch-accent data (kanjium) into vocab_pitch (data only; audio deferred).

accents.txt format: word \t reading(hiragana) \t accent-positions (comma-separated mora indices;
0 = heiban/no drop). Matches our vocab by (surface form, kana reading) and stores accent positions.
Stdlib only. Run with venv python.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import jaconv

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
SRC = ROOT / "research" / "datasets" / "pitch" / "accents.txt"
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def hira(s: str) -> str:
    return jaconv.kata2hira(s or "")


def main() -> int:
    if not SRC.exists():
        print("accents.txt not present"); return 1
    # (word, reading) -> [accent positions]
    acc: dict[tuple[str, str], list[int]] = {}
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 3:
                continue
            word, reading, a = p[0], hira(p[1]), p[2]
            try:
                positions = [int(x) for x in a.split(",") if x.strip().lstrip("-").isdigit()]
            except ValueError:
                continue
            if positions:
                acc.setdefault((word, reading), positions)
                acc.setdefault((reading, reading), positions)  # kana-only fallback

    con = sqlite3.connect(DB)
    if con.execute("SELECT COUNT(*) FROM vocab_pitch").fetchone()[0] > 0:
        print("[skip] vocab_pitch already populated"); return 0
    cur = con.cursor()
    matched = 0
    for vid, headword, kana in con.execute("SELECT id,headword,kana FROM vocab WHERE level IN ('n5','n4')"):
        rd = hira(kana)
        forms = [headword] + [r[0] for r in con.execute(
            "SELECT form FROM vocab_form WHERE vocab_id=?", (vid,))]
        positions = None
        for fcand in forms:
            if (fcand, rd) in acc:
                positions = acc[(fcand, rd)]
                break
        if positions is None and (rd, rd) in acc:
            positions = acc[(rd, rd)]
        if positions is not None:
            cur.execute("INSERT INTO vocab_pitch (vocab_id,reading,accent_positions,source) "
                        "VALUES (?,?,?,?)", (vid, kana, json.dumps(positions), "kanjium"))
            matched += 1
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM vocab WHERE level IN ('n5','n4')").fetchone()[0]
    print(f"pitch matched: {matched}/{total} vocab ({round(100*matched/total,1)}%)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
