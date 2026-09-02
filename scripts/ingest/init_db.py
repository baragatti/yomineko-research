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

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
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
        # Statement at a time rather than executescript, so a column that a hand-run ALTER already
        # added to the live DB does not abort a migration that legitimately declares it (009). Only
        # the duplicate-column case is swallowed; every other error still stops the run.
        # sqlite3.complete_statement does the splitting, because it knows a ';' inside a comment or a
        # string literal is not the end of anything — the naive split does not.
        buf = ""
        for line in f.read_text(encoding="utf-8").splitlines(keepends=True):
            buf += line
            if not sqlite3.complete_statement(buf):
                continue
            stmt, buf = buf.strip(), ""
            try:
                con.execute(stmt)
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                print(f"    [have] {str(e).split(':')[-1].strip()}")
        if buf.strip():
            raise SystemExit(f"{f.name}: trailing text with no statement terminator")
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
    shown = DB.relative_to(ROOT) if DB.is_relative_to(ROOT) else DB
    print(f"\nDB ready: {shown}  ({len(tables)} tables)")
    print("tables:", ", ".join(tables))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
