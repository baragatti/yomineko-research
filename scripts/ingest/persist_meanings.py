#!/usr/bin/env python3
"""P5b step 3 — persist Workflow-translated pt-BR meanings back into the corpus.

Reads the meanings result (list of {chunk_index, items:[{id,type,pt:[...]}]}) and writes
kanji.meanings_pt / vocab_sense.gloss_pt (JSON arrays). Layer B → kanji.needs_review left as-is
(facts); vocab_sense.needs_review set to 1 for the pt gloss. Usage: --result <file>
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
    nk = ns = 0
    for chunk in data:
        for it in (chunk.get("items") or []):
            pt = it.get("pt") or []
            if not pt:
                continue
            if it["type"] == "kanji":
                set_text(con, "kanji", it["id"], "meanings", pt, layer="B")
                nk += 1
            elif it["type"] == "sense":
                set_text(con, "vocab_sense", it["id"], "gloss", pt, layer="B")
                cur.execute("UPDATE vocab_sense SET needs_review=1 WHERE id=?", (it["id"],))
                ns += 1
    con.commit()
    rem_k = con.execute("SELECT COUNT(*) FROM kanji WHERE level IS NOT NULL AND id NOT IN "
                        "(SELECT entity_id FROM localized_text WHERE entity_type='kanji' AND field='meanings')"
                        ).fetchone()[0]
    rem_s = con.execute("SELECT COUNT(*) FROM vocab_sense WHERE id NOT IN "
                        "(SELECT entity_id FROM localized_text WHERE entity_type='vocab_sense' AND field='gloss')"
                        ).fetchone()[0]
    print(f"updated kanji={nk}, senses={ns}; remaining untranslated kanji={rem_k}, senses={rem_s}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
