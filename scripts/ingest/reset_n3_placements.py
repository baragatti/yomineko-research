#!/usr/bin/env python3
"""Clear introducing_topic_id for all N3 vocab+kanji so load_lessons re-derives placements from the CURRENT
lesson set (used after re-authoring lessons, since backfill never clears stale placements). N5/N4 untouched.
Usage: reset_n3_placements.py"""
import sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
con = sqlite3.connect(Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite")
v = con.execute("UPDATE vocab SET introducing_topic_id=NULL WHERE level='n3'").rowcount
k = con.execute("UPDATE kanji SET introducing_topic_id=NULL WHERE level='n3'").rowcount
con.commit()
con.close()
print(f"reset introducing_topic_id: vocab={v} kanji={k} (n3 only)")
