#!/usr/bin/env python3
"""Durable corpus-layer notation fix (the DB counterpart of the task-#41 lesson notation pass).
Applies, in db localized_text learner text, the same anchored transforms so export_corpus emits the
plain-pt-BR versions: technical "not equal" sign -> plain pt-BR; phonetic slash notation /x/ -> 'x'
(single quotes), anchored on som/sons, "= ", " (" so slash-separated word lists are never touched.
Idempotent. Run before export_corpus; safe to re-run after replay_all.
"""
from __future__ import annotations
import re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

DB = db_target(Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite")
P1 = re.compile(r"(\b(?:som|sons)\s)/([a-z]{1,4})/")
P2 = re.compile(r"/([a-z]{1,4})/(\s*=)")
P3 = re.compile(r"/([a-z]{1,4})/(\s*\()")


def t(s: str) -> str:
    s = re.sub(r"\(≠\s*", "(diferente de ", s)
    s = re.sub(r"\s*≠\s*", " não é ", s)
    s = P1.sub(r"\1'\2'", s)
    s = P2.sub(r"'\1'\2", s)
    s = P3.sub(r"'\1'\2", s)
    return s


def main() -> int:
    con = sqlite3.connect(DB); cur = con.cursor()
    rows = cur.execute("SELECT rowid, value FROM localized_text WHERE value LIKE '%≠%' OR value LIKE '%/%'").fetchall()
    changed = 0
    for rid, val in rows:
        nv = t(val)
        if nv != val:
            cur.execute("UPDATE localized_text SET value=? WHERE rowid=?", (nv, rid)); changed += 1
    con.commit()
    print(f"notation fix: {changed} localized_text values updated")
    con.close(); return 0


if __name__ == "__main__":
    sys.exit(main())
