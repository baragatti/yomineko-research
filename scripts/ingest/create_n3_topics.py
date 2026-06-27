#!/usr/bin/env python3
"""Create the N3 module + topic rows from a curriculum-design JSON (additive; idempotent).
Reads research/_n3_topics.json = [{order,slug,title_pt,theme_pt,grammar_keys}].
Inserts mod:n3 (after mod:n4) + each topic; sets grammar_point.introducing_topic_id for the mapped keys.
Topic global order continues after the last existing topic.

i18n: title/theme are ALSO written to `localized_text` (the single source the exporter reads) — not only the
legacy `*_pt` columns. The one-time `migrate_i18n.py` skips once localized_text is populated, so topics created
afterwards must populate it themselves or they export with an empty title (the N3 breadcrumb bug). This runs on
EVERY invocation (idempotent INSERT OR REPLACE), so it also backfills topics created by older versions.
Usage: create_n3_topics.py"""
import json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text  # noqa: E402
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
backfilled = 0
for t in sorted(topics, key=lambda x: x["order"]):
    row = cur.execute("SELECT id FROM topic WHERE slug=?", (t["slug"],)).fetchone()
    if row:
        tid = row[0]
    else:
        cur.execute("INSERT INTO topic (slug,module_id,ord,source,created_by,layer,needs_review) "
                    "VALUES (?,?,?, 'outline','ai','C',1)", (t["slug"], mod_id, base + t["order"]))
        tid = cur.lastrowid
        created += 1
    # i18n: title + theme into localized_text (the exporter's source). Idempotent.
    set_text(con, "topic", tid, "title", t["title_pt"], layer="C")
    if t.get("theme_pt"):
        set_text(con, "topic", tid, "theme", t["theme_pt"], layer="C")
    if t.get("objectives_pt"):
        set_text(con, "topic", tid, "objectives", t["objectives_pt"], layer="C")
    backfilled += 1
    for k in (t.get("grammar_keys") or []):
        cur.execute("UPDATE grammar_point SET introducing_topic_id=? WHERE key=? AND level='n3'", (tid, k))
con.commit()
print(f"created {created} N3 topics; backfilled i18n for {backfilled}; mapped grammar keys to topics")
con.close()
