#!/usr/bin/env python3
"""Apply SQLite migrations idempotently to db/corpus.sqlite.

Reads scripts/ingest/migrations/*.sql in filename order; each file is applied once
and recorded in the schema_migration table. Re-running is safe. Stdlib only.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
MIG = ROOT / "scripts" / "ingest" / "migrations"


def main() -> int:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    con.execute(
        "CREATE TABLE IF NOT EXISTS schema_migration "
        "(filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL);"
    )
    applied = {r[0] for r in con.execute("SELECT filename FROM schema_migration")}
    files = sorted(MIG.glob("*.sql"))
    if not files:
        print("no migrations found", flush=True)
        return 1
    for f in files:
        if f.name in applied:
            print(f"  [skip] {f.name}")
            continue
        print(f"  [apply] {f.name}")
        con.executescript(f.read_text(encoding="utf-8"))
        con.execute(
            "INSERT INTO schema_migration(filename, applied_at) VALUES (?, ?)",
            (f.name, _dt.datetime.now().isoformat(timespec="seconds")),
        )
        con.commit()
    tables = [
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    print(f"\nDB ready: {DB.relative_to(ROOT)}  ({len(tables)} tables)")
    print("tables:", ", ".join(tables))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
