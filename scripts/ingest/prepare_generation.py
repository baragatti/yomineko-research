#!/usr/bin/env python3
"""P5 GENERATION step 1 — find undercovered targets and write generation input groups.

Spec §1.2: generation is the LAST resort after selection. For vocab with <--min dissected sentences (or
grammar points with <--min links), emit the target (with its pt meaning / forms) so the generation workflow
can write i+1 sentences featuring it. Generated sentences are flagged ai_generated + needs_review downstream.
Usage: prepare_generation.py --level n5 --kind vocab --min 3 --out-dir research/derived/gen_n5_vocab [--limit 120]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)
    ap.add_argument("--kind", choices=["vocab", "grammar"], required=True)
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--limit", type=int, default=120, help="max targets per run")
    ap.add_argument("--group", type=int, default=10, help="targets per agent group")
    ap.add_argument("--out-dir", dest="out_dir", required=True)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    targets = []
    if args.kind == "vocab":
        cnt = Counter(r[0] for r in con.execute("SELECT vocab_id FROM sentence_vocab"))
        for vid, hw, kana, vclass in con.execute(
                "SELECT id,headword,kana,verb_class FROM vocab WHERE level=? ORDER BY common DESC, "
                "freq_rank IS NULL, freq_rank", (args.level,)):
            if cnt.get(vid, 0) >= args.min:
                continue
            sid = con.execute("SELECT id FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1",
                              (vid,)).fetchone()
            gloss = get_text(con, "vocab_sense", sid[0], "gloss") if sid else None
            targets.append({"kind": "vocab", "vocab_id": vid, "word": hw, "kana": kana,
                            "verb_class": vclass, "meaning": gloss, "need": args.min - cnt.get(vid, 0)})
            if len(targets) >= args.limit:
                break
    else:
        cnt = Counter(r[0] for r in con.execute("SELECT grammar_id FROM sentence_grammar"))
        for gid, key, pat, forms in con.execute(
                "SELECT id,key,structure_pattern,forms_json FROM grammar_point WHERE level=? ORDER BY key",
                (args.level,)):
            if cnt.get(gid, 0) >= args.min:
                continue
            targets.append({"kind": "grammar", "grammar_id": gid, "key": key, "pattern": pat,
                            "forms": json.loads(forms) if forms else [],
                            "label": get_text(con, "grammar_point", gid, "label"),
                            "need": args.min - cnt.get(gid, 0)})
            if len(targets) >= args.limit:
                break
    out = ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("group_*.json"):
        f.unlink()
    n = 0
    for i in range(0, len(targets), args.group):
        (out / f"group_{n:04d}.json").write_text(
            json.dumps(targets[i:i + args.group], ensure_ascii=False, indent=2), encoding="utf-8")
        n += 1
    print(f"generation targets: {len(targets)} ({args.kind} {args.level}, <{args.min}) -> {n} groups in {out}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
