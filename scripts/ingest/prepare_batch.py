#!/usr/bin/env python3
"""P5 scaling step 1 — prepare a dissection batch for a topic's targets.

For each target term, selects real Tatoeba sentences within the topic's cumulative known-set
(i+1, tokenization-guarded, deduped vs already-persisted), generates the SudachiPy skeleton, and
attaches EN translation + per-token dictionary gloss hints. Writes a self-contained batch JSON
that the dissection Workflow consumes as `args` (agents need no DB access). Run with venv python.

Usage: prepare_batch.py --topic top:n5-te-form --targets てください:4 ています:4 てから:2 --out research/derived/batch_te-form.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def known_sets(con, topic_slug):
    cutoff = con.execute("SELECT ord FROM topic WHERE slug=?", (topic_slug,)).fetchone()[0]
    tids = [r[0] for r in con.execute("SELECT id FROM topic WHERE ord<=?", (cutoff,))]
    q = ",".join("?" * len(tids))
    kv = {r[0] for r in con.execute(f"SELECT id FROM vocab WHERE introducing_topic_id IN ({q})", tids)}
    kk = {r[0] for r in con.execute(f"SELECT id FROM kanji WHERE introducing_topic_id IN ({q})", tids)}
    return kv, kk


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="top:n5-te-form")
    ap.add_argument("--targets", nargs="+", required=True, help="term:count ...")
    ap.add_argument("--out", required=True)
    ap.add_argument("--maxlen", type=int, default=24)
    ap.add_argument("--pool", type=int, default=600)
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    kv, kk = known_sets(con, args.topic)
    diss = Dissector()
    existing = {r[0] for r in con.execute("SELECT jp FROM sentence")}
    gloss_cache = {}

    def gloss_en(vid):
        if vid not in gloss_cache:
            r = con.execute("SELECT gloss_en FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1",
                            (vid,)).fetchone()
            g = json.loads(r[0]) if r and r[0] else []
            gloss_cache[vid] = g[0] if g else None
        return gloss_cache[vid]

    batch, seen_jp = [], set()
    for spec in args.targets:
        term, _, cnt = spec.partition(":")
        cnt = int(cnt or 5)
        rows = con.execute(
            "SELECT s.id,s.text,s.has_audio FROM raw_tatoeba_fts f JOIN raw_tatoeba_sentence s "
            "ON s.id=f.rowid WHERE f.text MATCH ? LIMIT ?", (f'"{term}"', args.pool)).fetchall()
        cands = []
        for sid, text, audio in rows:
            if len(text) > args.maxlen or text in existing or text in seen_jp:
                continue
            sk = diss.skeleton(text)
            if any(t["pos_fine"] == "固有名詞" and len(t["surface"]) >= 2 and t["vocab_id"] is None
                   for t in sk["tokens"]):
                continue
            new = len([v for v in sk["vocab_ids"] if v not in kv]) + \
                len([k for k in sk["kanji_ids"] if k not in kk])
            has_pt = con.execute("SELECT 1 FROM raw_tatoeba_translation WHERE jp_id=? AND lang='por' LIMIT 1",
                                 (sid,)).fetchone() is not None
            cands.append(((new, len(text), 0 if audio else 1), sid, text, sk))
        cands.sort(key=lambda c: c[0])
        for _score, sid, text, sk in cands[:cnt]:
            seen_jp.add(text)
            en = con.execute("SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' LIMIT 1",
                             (sid,)).fetchone()
            batch.append({
                "slug": f"sent:tatoeba-{sid}", "jp": text, "jp_source": f"tatoeba:{sid}",
                "en": en[0] if en else None, "target": term,
                "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                            "reading": t["reading"], "pos_coarse": t["pos_coarse"],
                            "pos_fine": t["pos_fine"], "is_particle": t["is_particle"],
                            "gloss_en": gloss_en(t["vocab_id"]) if t["vocab_id"] else None}
                           for t in sk["tokens"]],
                "particles": [{"position": p["position"], "particle": p["particle"]}
                              for p in sk["particles"]],
                # grammar link = the target term (resolved to a grammar_point if it matches); topic-level
                # grammar anchors are attached separately (avoids hardcoding one point).
                "grammar_keys": [term],
            })
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    by_t = {}
    for b in batch:
        by_t[b["target"]] = by_t.get(b["target"], 0) + 1
    print(f"batch: {len(batch)} sentences -> {args.out}  ({by_t})")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
