#!/usr/bin/env python3
"""Enrich sentence↔vocab links by matching CONTIGUOUS TOKEN RUNS against the vocab registry.

The dissector links vocab per single C-token, so multi-token words are missed: お茶 (お+茶), 五つ (五+つ),
お祖父さん (お+祖父+さん), and kana-written/auxiliary forms (ください). This pass slides windows of 1..N
contiguous C-tokens, concatenates their surfaces, and links any run whose surface is a known vocab form —
aligned to token boundaries, so it can't match a partial word (青 inside 青い is one token, not a run). Adds
sentence_vocab edges (INSERT OR IGNORE); never removes. Idempotent. Run after persist / in the batch recipe.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
MAXW = 5  # longest vocab span in tokens (お祖父さん etc.)


def main() -> int:
    diss = Dissector()  # loads vocab_by_form (forms/headword/kana -> vocab_id)
    by_form = diss._vocab_by_form
    con = sqlite3.connect(DB)
    cur = con.cursor()
    added = 0
    for (sid,) in con.execute("SELECT id FROM sentence"):
        toks = [(r[0], r[1]) for r in con.execute(
            "SELECT position, surface FROM token WHERE sentence_id=? AND split_mode='C' ORDER BY position",
            (sid,))]
        surfs = [s for _, s in toks]
        found: set[int] = set()
        n = len(surfs)
        for i in range(n):
            run = ""
            for w in range(MAXW):
                if i + w >= n:
                    break
                run += surfs[i + w]
                vid = by_form.get(run)
                if vid:
                    found.add(vid)
        for vid in found:
            before = cur.rowcount
            cur.execute("INSERT OR IGNORE INTO sentence_vocab (sentence_id, vocab_id) VALUES (?,?)",
                        (sid, vid))
            if cur.rowcount and cur.rowcount != before:
                added += 1
    con.commit()
    con.close()
    print(f"relink_vocab: added {added} sentence↔vocab edges")
    return 0


if __name__ == "__main__":
    sys.exit(main())
