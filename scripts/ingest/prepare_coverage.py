#!/usr/bin/env python3
"""P5 deepening — coverage-driven batch selector (greedy set-cover toward §10 ≥N sentences/vocab).

First-pass batches seed each topic's grammar + key vocab. This step closes the long tail: it finds vocab
of a given level that currently have FEWER than --target dissected sentences, then greedily selects real
Tatoeba sentences (within the level's known-set, i+1 capped) that each cover the MOST still-undercovered
vocab — so one sentence advances several items at once. Output is a normal batch (grammar_candidates omitted;
these are vocab-coverage fillers), consumed by split_groups → dissect workflow → persist_batch like any other.

Usage: prepare_coverage.py --level n5 --target 3 --max-sentences 60 --max-new 2 --out research/derived/batch_cov_n5.json
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
LEVEL_ORDER = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True, help="vocab level to deepen (e.g. n5, n4)")
    ap.add_argument("--target", type=int, default=3, help="desired sentences per vocab")
    ap.add_argument("--max-sentences", dest="max_sentences", type=int, default=60)
    ap.add_argument("--max-new", dest="max_new", type=int, default=2)
    ap.add_argument("--maxlen", type=int, default=22)
    ap.add_argument("--pool", type=int, default=300, help="Tatoeba candidates scanned per undercovered vocab")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    diss = Dissector()
    existing = {r[0] for r in con.execute("SELECT jp FROM sentence")}
    # known-set = everything at or below this level (so fillers stay in-level / review-clean)
    maxlvl = LEVEL_ORDER[args.level]
    keep = [lv for lv, o in LEVEL_ORDER.items() if o <= maxlvl]
    q = ",".join("?" * len(keep))
    kv = {r[0] for r in con.execute(f"SELECT id FROM vocab WHERE level IN ({q})", keep)}
    kk = {r[0] for r in con.execute(f"SELECT id FROM kanji WHERE level IN ({q})", keep)}

    # current per-vocab sentence counts → undercovered set for THIS level
    counts = {vid: 0 for (vid,) in con.execute("SELECT id FROM vocab WHERE level=?", (args.level,))}
    for (vid,) in con.execute(
            "SELECT sv.vocab_id FROM sentence_vocab sv JOIN vocab v ON v.id=sv.vocab_id WHERE v.level=?",
            (args.level,)):
        counts[vid] = counts.get(vid, 0) + 1
    need = {vid: args.target - n for vid, n in counts.items() if n < args.target}
    print(f"level {args.level}: {len(need)} vocab undercovered (<{args.target} sentences)")

    # gather candidate sentences: search Tatoeba for each undercovered vocab's surface, tokenize once
    seen_jp: set[str] = set()
    cand: list[tuple[str, int, list[int]]] = []  # (jp, sid, undercovered_vocab_ids_covered)
    for vid in list(need):
        surf = con.execute("SELECT COALESCE(headword, kana) FROM vocab WHERE id=?", (vid,)).fetchone()[0]
        if not surf:
            continue
        if len(surf) >= 3:
            rows = con.execute(
                "SELECT s.id,s.text FROM raw_tatoeba_fts f JOIN raw_tatoeba_sentence s ON s.id=f.rowid "
                "WHERE f.text MATCH ? LIMIT ?", (f'"{surf}"', args.pool)).fetchall()
        else:
            rows = con.execute("SELECT id,text FROM raw_tatoeba_sentence WHERE text LIKE ? LIMIT ?",
                               (f"%{surf}%", args.pool)).fetchall()
        for sid, text in rows:
            if len(text) > args.maxlen or text in existing or text in seen_jp:
                continue
            sk = diss.skeleton(text)
            if any(t["pos_fine"] == "固有名詞" and len(t["surface"]) >= 2 and t["vocab_id"] is None
                   for t in sk["tokens"]):
                continue
            newc = len([v for v in sk["vocab_ids"] if v not in kv]) + \
                len([k for k in sk["kanji_ids"] if k not in kk])
            if newc > args.max_new:
                continue
            covers = [v for v in sk["vocab_ids"] if v in need]
            if not covers:
                continue
            seen_jp.add(text)
            cand.append((text, sid, covers))
    print(f"gathered {len(cand)} candidate sentences")

    # greedy set-cover: repeatedly take the sentence covering the most still-needed vocab
    remaining = dict(need)
    chosen: list[tuple[str, int]] = []
    pool = cand[:]
    while pool and len(chosen) < args.max_sentences:
        pool.sort(key=lambda c: sum(1 for v in c[2] if remaining.get(v, 0) > 0), reverse=True)
        best = pool.pop(0)
        gain = [v for v in best[2] if remaining.get(v, 0) > 0]
        if not gain:
            break
        chosen.append((best[0], best[1]))
        for v in gain:
            remaining[v] -= 1
            if remaining[v] <= 0:
                remaining.pop(v, None)

    batch = []
    for text, sid in chosen:
        sk = diss.skeleton(text)
        en = con.execute("SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' LIMIT 1",
                         (sid,)).fetchone()
        batch.append({
            "slug": f"sent:tatoeba-{sid}", "jp": text, "jp_source": f"tatoeba:{sid}",
            "en": en[0] if en else None, "target": "coverage", "topic": f"coverage:{args.level}",
            "level": args.level,
            "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                        "reading": t["reading"], "pos_coarse": t["pos_coarse"], "pos_fine": t["pos_fine"],
                        "is_particle": t["is_particle"], "gloss_en": None} for t in sk["tokens"]],
            "particles": [{"position": p["position"], "particle": p["particle"]} for p in sk["particles"]],
            "grammar_candidates": [],
        })
    out = ROOT / args.out
    out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"coverage batch: {len(batch)} sentences -> {args.out}  ({len(need) - len(remaining)} vocab advanced)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
