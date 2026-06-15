#!/usr/bin/env python3
"""Prepare grammar-enrichment input: dump each grammar point's data into group files for the AI pass.

The pass adds a richer `register` enum + offensive-risk `caution` + per-form pt meaning, and humanizes the
existing explanation/formation/nuance prose. Writes research/derived/gram_enrich_groups/group_NNNN.json.
Run with venv python. Usage: prepare_grammar_enrich.py [group_size=30]
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "research" / "derived" / "gram_enrich_groups"


def main() -> int:
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    con = sqlite3.connect(DB)
    items = []
    for gid, key, pat, forms_json, reg, level in con.execute(
            "SELECT id,key,structure_pattern,forms_json,register,level FROM grammar_point ORDER BY id"):
        items.append({
            "key": key, "level": level, "structure_pattern": pat,
            "forms": json.loads(forms_json) if forms_json else [],
            "current_register": reg,
            "label": get_text(con, "grammar_point", gid, "label"),
            "explanation": get_text(con, "grammar_point", gid, "explanation"),
            "formation": get_text(con, "grammar_point", gid, "formation"),
            "nuance": get_text(con, "grammar_point", gid, "nuance"),
        })
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("group_*.json"):
        f.unlink()
    n = 0
    for i in range(0, len(items), k):
        (OUT / f"group_{n:04d}.json").write_text(
            json.dumps(items[i:i + k], ensure_ascii=False, indent=2), encoding="utf-8")
        n += 1
    print(f"prepared {len(items)} grammar points -> {n} groups (size {k}) in {OUT}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
