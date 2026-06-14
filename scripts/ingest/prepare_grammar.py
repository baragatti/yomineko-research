#!/usr/bin/env python3
"""P6-g step 1 — batch grammar points needing pt-BR explanations into chunks for the grammar Workflow.

Selects grammar_point rows with no explanation_pt (optionally by level), chunks them, writes a
self-contained JSON for the Workflow. Run with venv python.
Usage: prepare_grammar.py --level n5 --chunk 6 --out research/derived/grammar_n5.json
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
    ap.add_argument("--level", choices=["n5", "n4", "all"], default="all")
    ap.add_argument("--chunk", type=int, default=6)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    lvl = "" if args.level == "all" else f" AND level='{args.level}'"
    items = []
    for gid, key, pat, refs, level in con.execute(
        f"SELECT id,key,structure_pattern,references_json,level FROM grammar_point "
        f"WHERE explanation_pt IS NULL{lvl} ORDER BY level,key"):
        r = json.loads(refs) if refs else {}
        items.append({"id": gid, "key": key, "pattern": pat, "level": level,
                      "label_en": r.get("label_en"), "also_known_as": r.get("also_known_as", [])})
    chunks = [items[i:i + args.chunk] for i in range(0, len(items), args.chunk)]
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    print(f"grammar batch: {len(items)} points in {len(chunks)} chunks -> {args.out}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
