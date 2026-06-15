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
from persist_dissection import recompute_all_levels  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
MAXW = 5  # longest vocab span in tokens (お祖父さん etc.)


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    # MULTI-VALUED form -> {vocab_ids}: every vocab sharing a written form links (此処 & ここ both carry the
    # form ここ; ９日 carries 九日 + ここのか). A single-valued map would link only the first claimant.
    by_form: dict[str, set[int]] = {}
    for q in ("SELECT form, vocab_id FROM vocab_form", "SELECT headword, id FROM vocab",
              "SELECT kana, id FROM vocab"):
        for form, vid in con.execute(q):
            if form:
                by_form.setdefault(form, set()).add(vid)
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
                found.update(by_form.get(run, ()))
        for vid in found:
            before = cur.rowcount
            cur.execute("INSERT OR IGNORE INTO sentence_vocab (sentence_id, vocab_id) VALUES (?,?)",
                        (sid, vid))
            if cur.rowcount and cur.rowcount != before:
                added += 1
    con.commit()
    relev = recompute_all_levels(con)  # new links can raise a sentence's level
    con.close()
    print(f"relink_vocab: added {added} sentence↔vocab edges; recomputed {relev} sentence levels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
