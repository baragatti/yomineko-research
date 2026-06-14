#!/usr/bin/env python3
"""P5b step 1 — batch untranslated meanings (EN→pt-BR) into chunks for the meanings Workflow.

Collects kanji.meanings_en (where meanings_pt is null) and vocab_sense.gloss_en (where gloss_pt is
null), chunks them, and writes a self-contained JSON the Workflow consumes as args. Run with venv python.
Usage: prepare_meanings.py --scope both --level all --chunk 50 --out research/derived/meanings_batch.json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["kanji", "vocab", "both"], default="both")
    ap.add_argument("--level", choices=["n5", "n4", "all"], default="all")
    ap.add_argument("--chunk", type=int, default=50)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    lvl = "" if args.level == "all" else f" AND level='{args.level}'"
    items = []
    if args.scope in ("kanji", "both"):
        for kid, ch, men in con.execute(
            f"SELECT id,character,meanings_en FROM kanji WHERE level IS NOT NULL{lvl} "
            f"AND meanings_pt IS NULL"):
            items.append({"type": "kanji", "id": kid, "character": ch,
                          "meanings_en": json.loads(men) if men else []})
    if args.scope in ("vocab", "both"):
        lvlv = "" if args.level == "all" else f" AND v.level='{args.level}'"
        for sid, hw, kana, pos, gen in con.execute(
            f"SELECT s.id,v.headword,v.kana,s.pos,s.gloss_en FROM vocab_sense s "
            f"JOIN vocab v ON v.id=s.vocab_id WHERE s.gloss_pt IS NULL{lvlv}"):
            items.append({"type": "sense", "id": sid, "headword": hw, "kana": kana,
                          "pos": json.loads(pos) if pos else [],
                          "gloss_en": json.loads(gen) if gen else []})
    chunks = [items[i:i + args.chunk] for i in range(0, len(items), args.chunk)]
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    print(f"meanings batch: {len(items)} items in {len(chunks)} chunks -> {args.out}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
