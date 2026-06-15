#!/usr/bin/env python3
"""Persist the grammar-enrichment result: register[] + caution + per-form pt meaning + humanized prose.

Usage: persist_grammar_enrich.py --result <result.json>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    args = ap.parse_args()
    results = json.loads(Path(args.result).read_text(encoding="utf-8"))
    con = sqlite3.connect(DB)
    cur = con.cursor()
    done, missing = 0, []
    for r in results:
        row = cur.execute("SELECT id FROM grammar_point WHERE key=?", (r.get("key"),)).fetchone()
        if not row:
            missing.append(r.get("key"))
            continue
        gid = row[0]
        reg = r.get("register") or []
        caution = r.get("caution")
        cur.execute("UPDATE grammar_point SET register_json=?, caution=? WHERE id=?",
                    (json.dumps(reg, ensure_ascii=False), None if caution in (None, "none") else caution, gid))
        for f in ("explanation", "formation", "nuance"):
            if r.get(f):
                set_text(con, "grammar_point", gid, f, r[f], layer="C")
        fm = {x["form"]: x["meaning"] for x in r.get("forms", []) if x.get("form") and x.get("meaning")}
        if fm:
            set_text(con, "grammar_point", gid, "form_meanings", fm, layer="B")
        done += 1
    con.commit()
    con.close()
    print(f"grammar-enrich persisted: {done}; missing keys: {len(missing)} {missing[:20]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
