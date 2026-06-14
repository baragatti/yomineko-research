#!/usr/bin/env python3
"""P5 — select real Tatoeba sentences for a target within a topic's cumulative known-set (i+1).

Uses the trigram FTS for a fast substring shortlist, then SudachiPy-dissects each candidate and
scores it by: how many of its linked vocab/kanji are NEW vs the known-set (fewer = better i+1),
length, and PT/audio availability. Prints a ranked shortlist for human pick. Selection-over-
generation: we choose natural human sentences; pt-BR is authored later (Layer B).

Usage: select_candidates.py "てください" --topic top:n5-te-form --limit 15
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def known_sets(con, topic_slug: str):
    ordv = con.execute("SELECT ord FROM topic WHERE slug=?", (topic_slug,)).fetchone()
    if not ordv:
        raise SystemExit(f"unknown topic {topic_slug}")
    cutoff = ordv[0]
    topic_ids = [r[0] for r in con.execute("SELECT id FROM topic WHERE ord<=?", (cutoff,))]
    qmarks = ",".join("?" * len(topic_ids))
    kv = {r[0] for r in con.execute(
        f"SELECT id FROM vocab WHERE introducing_topic_id IN ({qmarks})", topic_ids)}
    kk = {r[0] for r in con.execute(
        f"SELECT id FROM kanji WHERE introducing_topic_id IN ({qmarks})", topic_ids)}
    return kv, kk, cutoff


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("term")
    ap.add_argument("--topic", default="top:n5-te-form")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--pool", type=int, default=600)
    ap.add_argument("--maxlen", type=int, default=22)
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    kv, kk, cutoff = known_sets(con, args.topic)
    diss = Dissector()
    rows = con.execute(
        "SELECT s.id, s.text, s.has_audio FROM raw_tatoeba_fts f "
        "JOIN raw_tatoeba_sentence s ON s.id=f.rowid WHERE f.text MATCH ? LIMIT ?",
        (f'"{args.term}"', args.pool)).fetchall()
    cands = []
    for sid, text, audio in rows:
        if len(text) > args.maxlen:
            continue
        sk = diss.skeleton(text)
        new_v = [v for v in sk["vocab_ids"] if v not in kv]
        new_k = [k for k in sk["kanji_ids"] if k not in kk]
        # require the target term present (FTS already ensures) and few new items
        has_pt = con.execute("SELECT 1 FROM raw_tatoeba_translation WHERE jp_id=? AND lang='por' LIMIT 1",
                             (sid,)).fetchone() is not None
        score = (len(new_v) + len(new_k), len(text), 0 if audio else 1, 0 if has_pt else 1)
        cands.append((score, sid, text, len(new_v), len(new_k), audio, has_pt))
    cands.sort(key=lambda c: c[0])
    print(f"known-set up to {args.topic} (ord≤{cutoff}): {len(kv)} vocab, {len(kk)} kanji")
    print(f"term '{args.term}': {len(rows)} FTS hits, {len(cands)} ≤{args.maxlen} chars. Top {args.limit}:")
    for score, sid, text, nv, nk, audio, has_pt in cands[:args.limit]:
        en = con.execute("SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' LIMIT 1",
                         (sid,)).fetchone()
        print(f"  [{sid}] new_v={nv} new_k={nk} audio={'Y' if audio else '-'} pt={'Y' if has_pt else '-'} "
              f"| {text}  // {en[0] if en else ''}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
