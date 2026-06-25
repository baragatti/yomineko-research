#!/usr/bin/env python3
"""Build the N3 sentence-bank dissection input: for every N3 grammar point, select real Tatoeba
sentences (i+1 within the N3 cumulative known-set, Sudachi skeleton, deduped vs the existing bank),
and write group_NNNN.json files in the dissect_batch_workflow format. Deterministic (no AI / no tokens).

Usage: prepare_n3_sentence_batch.py [--per 5] [--group-size 8] [--maxlen 26] [--out research/derived/n3_dissect]
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from i18n_text import get_text  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def search_term(pattern: str) -> str:
    """Longest kana/kanji fragment of a grammar pattern (drop ～/〜 placeholders)."""
    frags = [f for f in pattern.replace("〜", "～").split("～") if f.strip()]
    return max(frags, key=len).strip() if frags else pattern.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=5)
    ap.add_argument("--group-size", type=int, default=8)
    ap.add_argument("--maxlen", type=int, default=26)
    ap.add_argument("--max-new", type=int, default=3)
    ap.add_argument("--pool", type=int, default=400)
    ap.add_argument("--out", default="research/derived/n3_dissect")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    diss = Dissector()
    existing = {r[0] for r in con.execute("SELECT jp FROM sentence")}
    seen = set()
    # N3 content topics in order
    topics = con.execute(
        "SELECT t.id,t.slug,t.ord FROM topic t JOIN course_module m ON m.id=t.module_id "
        "WHERE m.level='n3' AND t.slug NOT LIKE '%revisao%' ORDER BY t.ord").fetchall()

    def gloss_en(vid):
        r = con.execute("SELECT gloss_en FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1",
                        (vid,)).fetchone()
        g = json.loads(r[0]) if r and r[0] else []
        return g[0] if g else None

    batch = []
    for tid, tslug, tord in topics:
        tids = [r[0] for r in con.execute("SELECT id FROM topic WHERE ord<=?", (tord,))]
        q = ",".join("?" * len(tids))
        kv = {r[0] for r in con.execute(f"SELECT id FROM vocab WHERE introducing_topic_id IN ({q})", tids)}
        kk = {r[0] for r in con.execute(f"SELECT id FROM kanji WHERE introducing_topic_id IN ({q})", tids)}
        gcand = [{"key": k, "pattern": p or "", "label": get_text(con, "grammar_point", gid, "label") or ""}
                 for gid, k, p in con.execute(
                     "SELECT id,key,structure_pattern FROM grammar_point WHERE introducing_topic_id=?", (tid,))]
        for gid, key, pattern in con.execute(
                "SELECT id,key,structure_pattern FROM grammar_point WHERE introducing_topic_id=?", (tid,)):
            term = search_term(pattern or "")
            if len(term) < 2:
                continue
            if len(term) >= 3:
                rows = con.execute("SELECT s.id,s.text,s.has_audio FROM raw_tatoeba_fts f "
                                   "JOIN raw_tatoeba_sentence s ON s.id=f.rowid WHERE f.text MATCH ? LIMIT ?",
                                   (f'"{term}"', args.pool)).fetchall()
            else:
                rows = con.execute("SELECT id,text,has_audio FROM raw_tatoeba_sentence WHERE text LIKE ? LIMIT ?",
                                   (f"%{term}%", args.pool)).fetchall()
            cands = []
            for sid, text, audio in rows:
                if len(text) > args.maxlen or text in existing or text in seen:
                    continue
                sk = diss.skeleton(text)
                if any(t["pos_fine"] == "固有名詞" and len(t["surface"]) >= 2 and t["vocab_id"] is None
                       for t in sk["tokens"]):
                    continue
                new = len([v for v in sk["vocab_ids"] if v not in kv]) + \
                    len([k for k in sk["kanji_ids"] if k not in kk])
                if new > args.max_new:
                    continue
                cands.append(((new, len(text), 0 if audio else 1), sid, text, sk))
            cands.sort(key=lambda c: c[0])
            for _s, sid, text, sk in cands[:args.per]:
                seen.add(text)
                en = con.execute("SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' LIMIT 1",
                                 (sid,)).fetchone()
                batch.append({
                    "slug": f"sent:tatoeba-{sid}", "jp": text, "jp_source": f"tatoeba:{sid}",
                    "en": en[0] if en else None, "target": key, "topic": tslug, "level": "n3",
                    "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                                "reading": t["reading"], "pos_coarse": t["pos_coarse"], "pos_fine": t["pos_fine"],
                                "is_particle": t["is_particle"],
                                "gloss_en": gloss_en(t["vocab_id"]) if t["vocab_id"] else None}
                               for t in sk["tokens"]],
                    "particles": [{"position": p["position"], "particle": p["particle"]} for p in sk["particles"]],
                    "grammar_candidates": gcand,
                })
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("group_*.json"):
        old.unlink()
    gs = args.group_size
    ng = (len(batch) + gs - 1) // gs
    for i in range(ng):
        (outdir / f"group_{i:04d}.json").write_text(
            json.dumps(batch[i * gs:(i + 1) * gs], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"N3 sentence batch: {len(batch)} sentences across {len(topics)} topics -> {ng} groups in {args.out}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
