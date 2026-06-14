#!/usr/bin/env python3
"""P6-g step 3 — persist Workflow-authored grammar explanations (Layer C) into grammar_point.

Reads result (list of {chunk_index, items:[{id,label_pt,explanation_pt,formation_pt,nuance_pt,register}]})
and updates the rows; needs_review stays 1 (Layer C, awaits teacher). Usage: --result <file>
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
    data = json.loads(Path(args.result).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("result", [])
    con = sqlite3.connect(DB)
    cur = con.cursor()
    n = 0
    for chunk in data:
        for it in (chunk.get("items") or []):
            gid = it["id"]
            set_text(con, "grammar_point", gid, "label", it.get("label_pt"), layer="C")
            set_text(con, "grammar_point", gid, "explanation", it.get("explanation_pt"), layer="C")
            set_text(con, "grammar_point", gid, "formation", it.get("formation_pt"), layer="C")
            set_text(con, "grammar_point", gid, "nuance", it.get("nuance_pt"), layer="C")
            cur.execute("UPDATE grammar_point SET register=COALESCE(?,register), needs_review=1 WHERE id=?",
                        (it.get("register"), gid))
            n += 1
    con.commit()
    rem = con.execute("SELECT COUNT(*) FROM grammar_point WHERE id NOT IN "
                      "(SELECT entity_id FROM localized_text WHERE entity_type='grammar_point' "
                      "AND field='explanation')").fetchone()[0]
    print(f"updated {n} grammar points; remaining without explanation_pt={rem}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
