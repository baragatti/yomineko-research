#!/usr/bin/env python3
"""Mine JEC Basic (raw_jec, CC-BY 3.0) for real example sentences — second real source after Tatoeba.

Greedy set-cover like prepare_coverage, but over raw_jec, keeping JEC's manual English as the `en` source
(useful cross-check for our pt-BR). Selects JEC sentences within the level's known-set (i+1 capped) that
cover the most still-undercovered vocab. Output is a normal batch (jp_source="jec:#NNNN", source jec) for
split_groups → dissect → persist_batch (real, ai_generated=0). Usage:
  prepare_jec.py --level n5 --target 3 --max-sentences 120 --max-new 2 --out research/derived/batch_jec_n5.json
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
LV = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)
    ap.add_argument("--target", type=int, default=3)
    ap.add_argument("--max-sentences", dest="max_sentences", type=int, default=120)
    ap.add_argument("--max-new", dest="max_new", type=int, default=2)
    ap.add_argument("--maxlen", type=int, default=30)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    diss = Dissector()
    existing = {r[0] for r in con.execute("SELECT jp FROM sentence")}
    maxlvl = LV[args.level]
    keep = [lv for lv, o in LV.items() if o <= maxlvl]
    q = ",".join("?" * len(keep))
    kv = {r[0] for r in con.execute(f"SELECT id FROM vocab WHERE level IN ({q})", keep)}
    kk = {r[0] for r in con.execute(f"SELECT id FROM kanji WHERE level IN ({q})", keep)}
    cnt = {vid: 0 for (vid,) in con.execute("SELECT id FROM vocab WHERE level=?", (args.level,))}
    for (vid,) in con.execute("SELECT sv.vocab_id FROM sentence_vocab sv JOIN vocab v ON v.id=sv.vocab_id "
                              "WHERE v.level=?", (args.level,)):
        cnt[vid] = cnt.get(vid, 0) + 1
    need = {vid: args.target - n for vid, n in cnt.items() if n < args.target}
    print(f"level {args.level}: {len(need)} vocab undercovered")

    seen, cand = set(), []
    for vid in list(need):
        surf = con.execute("SELECT COALESCE(headword, kana) FROM vocab WHERE id=?", (vid,)).fetchone()[0]
        if not surf:
            continue
        if len(surf) >= 3:
            rows = con.execute("SELECT j.id,j.ja,j.en FROM raw_jec_fts f JOIN raw_jec j ON j.rowid=f.rowid "
                               "WHERE f.ja MATCH ? LIMIT 200", (f'"{surf}"',)).fetchall()
        else:
            rows = con.execute("SELECT id,ja,en FROM raw_jec WHERE ja LIKE ? LIMIT 200",
                               (f"%{surf}%",)).fetchall()
        for jid, ja, en in rows:
            if len(ja) > args.maxlen or ja in existing or ja in seen:
                continue
            sk = diss.skeleton(ja)
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
            seen.add(ja)
            cand.append((jid, ja, en, covers))
    print(f"gathered {len(cand)} JEC candidates")

    remaining = dict(need)
    chosen, pool = [], cand[:]
    while pool and len(chosen) < args.max_sentences:
        pool.sort(key=lambda c: sum(1 for v in c[3] if remaining.get(v, 0) > 0), reverse=True)
        best = pool.pop(0)
        gain = [v for v in best[3] if remaining.get(v, 0) > 0]
        if not gain:
            break
        chosen.append(best)
        for v in gain:
            remaining[v] -= 1
            if remaining[v] <= 0:
                remaining.pop(v, None)

    batch = []
    for jid, ja, en, _ in chosen:
        sk = diss.skeleton(ja)
        batch.append({
            "slug": jid.replace("jec:#", "sent:jec-"), "jp": ja, "jp_source": jid,
            "en": en or None, "target": "jec", "topic": f"jec:{args.level}", "level": args.level,
            "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                        "reading": t["reading"], "pos_coarse": t["pos_coarse"], "pos_fine": t["pos_fine"],
                        "is_particle": t["is_particle"], "gloss_en": None} for t in sk["tokens"]],
            "particles": [{"position": p["position"], "particle": p["particle"]} for p in sk["particles"]],
            "grammar_candidates": [],
        })
    Path(ROOT / args.out).write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JEC batch: {len(batch)} real sentences -> {args.out} ({len(need) - len(remaining)} vocab advanced)")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
