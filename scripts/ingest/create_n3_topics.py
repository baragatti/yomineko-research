#!/usr/bin/env python3
"""Create the N3 module + topic rows from a curriculum-design JSON (additive; idempotent).
Reads research/_n3_topics.json = [{order,slug,title_pt,theme_pt,grammar_keys}].
Inserts mod:n3 (after mod:n4) + each topic; sets grammar_point.introducing_topic_id for the mapped keys.
Topic global order continues after the last existing topic. Usage: create_n3_topics.py"""
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
topics = json.loads((ROOT / "research" / "_n3_topics.json").read_text(encoding="utf-8"))
con = sqlite3.connect(DB); con.execute("PRAGMA foreign_keys = ON;"); cur = con.cursor()
# module
row = cur.execute("SELECT id FROM course_module WHERE slug='mod:n3'").fetchone()
if row:
    mod_id = row[0]; print("mod:n3 exists", mod_id)
else:
    maxord = cur.execute("SELECT MAX(ord) FROM course_module").fetchone()[0] or 0
    cur.execute("INSERT INTO course_module (slug,level,ord,title_pt,source,created_by,layer,needs_review) "
                "VALUES ('mod:n3','n3',?,?, 'outline','ai','C',1)", (maxord + 1, "N3"))
    mod_id = cur.lastrowid; print("created mod:n3", mod_id)
base = cur.execute("SELECT MAX(ord) FROM topic").fetchone()[0] or 0
created = 0
for t in sorted(topics, key=lambda x: x["order"]):
    if cur.execute("SELECT id FROM topic WHERE slug=?", (t["slug"],)).fetchone():
        continue
    cur.execute("INSERT INTO topic (slug,module_id,ord,title_pt,theme_pt,source,created_by,layer,needs_review) "
                "VALUES (?,?,?,?,?, 'outline','ai','C',1)",
                (t["slug"], mod_id, base + t["order"], t["title_pt"], t.get("theme_pt", "")))
    tid = cur.lastrowid
    created += 1
    for k in (t.get("grammar_keys") or []):
        cur.execute("UPDATE grammar_point SET introducing_topic_id=? WHERE key=? AND level='n3'", (tid, k))
con.commit()
print(f"created {created} N3 topics; mapped grammar keys to topics")
con.close()
