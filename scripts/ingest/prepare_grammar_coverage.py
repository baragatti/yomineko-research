#!/usr/bin/env python3
"""P5 grammar deepening — coverage selector for GRAMMAR points (toward §10 ≥5 sentences/grammar).

The vocab coverage selector uses empty grammar candidates, so grammar links stall. This step targets
grammar points of a level that currently have FEWER than --target linked sentences: it derives a searchable
Japanese term from each point's structure_pattern, finds real Tatoeba sentences containing it (within the
level's known-set, i+1 capped), and attaches THAT grammar point as the candidate — the dissection agent then
CONFIRMS whether the pattern is genuinely used (no false-positive pollution) and links it. Points whose
pattern has no searchable ≥2-char Japanese run (e.g. "Verb + て", "受身形") are reported as
selection-unreachable → they need the generation path.

Usage: prepare_grammar_coverage.py --level n5 --target 5 --per-point 6 --max-new 2 --out research/derived/batch_gram_n5.json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LEVEL_ORDER = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
JP_RUN = re.compile(r"[ぁ-んァ-ヶ一-龯]{2,}")


def searchable_term(pattern: str) -> str | None:
    """Longest Japanese (kana/kanji) run ≥2 chars in the structure pattern, ignoring （…）, ASCII, ～〜."""
    if not pattern:
        return None
    p = re.sub(r"（[^）]*）", "", pattern)  # drop reading glosses in full-width parens
    p = p.replace("～", "").replace("〜", "")
    runs = JP_RUN.findall(p)
    return max(runs, key=len) if runs else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)
    ap.add_argument("--target", type=int, default=5, help="desired sentences per grammar point")
    ap.add_argument("--per-point", dest="per_point", type=int, default=6, help="max sentences selected per point")
    ap.add_argument("--max-new", dest="max_new", type=int, default=2)
    ap.add_argument("--maxlen", type=int, default=24)
    ap.add_argument("--pool", type=int, default=400)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    diss = Dissector()
    existing = {r[0] for r in con.execute("SELECT jp FROM sentence")}
    maxlvl = LEVEL_ORDER[args.level]
    keep = [lv for lv, o in LEVEL_ORDER.items() if o <= maxlvl]
    q = ",".join("?" * len(keep))
    kv = {r[0] for r in con.execute(f"SELECT id FROM vocab WHERE level IN ({q})", keep)}
    kk = {r[0] for r in con.execute(f"SELECT id FROM kanji WHERE level IN ({q})", keep)}

    counts = {gid: 0 for (gid,) in con.execute("SELECT id FROM grammar_point WHERE level=?", (args.level,))}
    for (gid,) in con.execute(
            "SELECT sg.grammar_id FROM sentence_grammar sg JOIN grammar_point g ON g.id=sg.grammar_id "
            "WHERE g.level=?", (args.level,)):
        counts[gid] = counts.get(gid, 0) + 1
    under = [(gid, args.target - n) for gid, n in counts.items() if n < args.target]
    print(f"level {args.level}: {len(under)} grammar points undercovered (<{args.target})")

    batch, seen_jp, unreachable = [], set(), []
    for gid, deficit in under:
        key, pat = con.execute("SELECT key, COALESCE(structure_pattern,'') FROM grammar_point WHERE id=?",
                               (gid,)).fetchone()
        term = searchable_term(pat)
        if not term:
            unreachable.append(key)
            continue
        cand = {"key": key, "pattern": pat, "label": get_text(con, "grammar_point", gid, "label") or ""}
        if len(term) >= 3:
            rows = con.execute(
                "SELECT s.id,s.text FROM raw_tatoeba_fts f JOIN raw_tatoeba_sentence s ON s.id=f.rowid "
                "WHERE f.text MATCH ? LIMIT ?", (f'"{term}"', args.pool)).fetchall()
        else:
            rows = con.execute("SELECT id,text FROM raw_tatoeba_sentence WHERE text LIKE ? LIMIT ?",
                               (f"%{term}%", args.pool)).fetchall()
        scored = []
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
            scored.append(((newc, len(text)), sid, text, sk))
        scored.sort(key=lambda c: c[0])
        take = min(args.per_point, max(deficit + 2, 3))  # a couple extra to survive the agent's gate
        for _s, sid, text, sk in scored[:take]:
            seen_jp.add(text)
            en = con.execute("SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' LIMIT 1",
                             (sid,)).fetchone()
            batch.append({
                "slug": f"sent:tatoeba-{sid}", "jp": text, "jp_source": f"tatoeba:{sid}",
                "en": en[0] if en else None, "target": term, "topic": f"grammar:{key}", "level": args.level,
                "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                            "reading": t["reading"], "pos_coarse": t["pos_coarse"], "pos_fine": t["pos_fine"],
                            "is_particle": t["is_particle"], "gloss_en": None} for t in sk["tokens"]],
                "particles": [{"position": p["position"], "particle": p["particle"]} for p in sk["particles"]],
                "grammar_candidates": [cand],
            })
    out = ROOT / args.out
    out.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"grammar batch: {len(batch)} sentences -> {args.out}  "
          f"(selection-unreachable points: {len(unreachable)} -> need generation: {unreachable[:25]})")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
