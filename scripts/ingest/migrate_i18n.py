#!/usr/bin/env python3
"""Pre-P5 i18n migration: copy existing *_pt content into localized_text (locale pt-BR), then NULL the
legacy columns so localized_text is the single source. Idempotent. Run with venv python."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import FIELD_MAP, set_text  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    if con.execute("SELECT COUNT(*) FROM localized_text").fetchone()[0] > 0:
        print(f"[skip] localized_text already populated "
              f"({con.execute('SELECT COUNT(*) FROM localized_text').fetchone()[0]})")
        return 0
    total = 0
    for etype, fields in FIELD_MAP.items():
        cols = [c for c, _, _ in fields]
        rows = con.execute(f"SELECT id,{','.join(cols)} FROM {etype}").fetchall()
        n = 0
        for row in rows:
            eid = row[0]
            for (col, neutral, is_list), val in zip(fields, row[1:]):
                if val is None:
                    continue
                value = json.loads(val) if is_list else val
                set_text(con, etype, eid, neutral, value)
                n += 1
        # NULL the legacy columns (single source = localized_text)
        for col, _, _ in fields:
            cur.execute(f"UPDATE {etype} SET {col}=NULL")
        total += n
        print(f"  {etype}: migrated {n} field-values ({len(rows)} rows)")
    con.commit()
    lt = con.execute("SELECT COUNT(*) FROM localized_text").fetchone()[0]
    by = dict(con.execute("SELECT entity_type, COUNT(*) FROM localized_text GROUP BY entity_type"))
    print(f"localized_text rows: {lt} (migrated {total}); by entity: {by}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
