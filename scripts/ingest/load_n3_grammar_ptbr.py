#!/usr/bin/env python3
"""Load AI N3 grammar Layer-C (label/explanation/formation/nuance) from a workflow output into localized_text.
Usage: load_n3_grammar_ptbr.py <output.json>"""
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
r = raw.get("result", raw)
if isinstance(r, str):
    r = json.loads(r[r.index("{"):])
items = r.get("items", [])
con = sqlite3.connect(DB); cur = con.cursor()
n = 0
for it in items:
    gid = it["gid"]
    for field in ("label", "explanation", "formation", "nuance"):
        val = (it.get(field) or "").strip()
        if not val:
            continue
        cur.execute("DELETE FROM localized_text WHERE entity_type='grammar_point' AND entity_id=? "
                    "AND field=? AND locale='pt-BR'", (gid, field))
        cur.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
                    "VALUES ('grammar_point',?,?,'pt-BR',?,0,'C')", (gid, field, val))
    n += 1
con.commit()
print(f"loaded grammar Layer-C: {n} points")
con.close()
