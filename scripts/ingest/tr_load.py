#!/usr/bin/env python3
"""Translation pipeline — LOAD step. Reads the AI result ({results:[{i,o}]}) + the _map.json from tr_extract,
maps each distinct translation back to all its rows, and upserts localized_text under the task's target locale.
Idempotent (INSERT OR REPLACE on the localized_text PK). Usage: tr_load.py <task>"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    task = sys.argv[1]
    tdir = ROOT / "research" / "derived" / "tr" / task
    mp = json.loads((tdir / "_map.json").read_text(encoding="utf-8"))
    target, occ = mp["target"], mp["occ"]
    res_raw = json.loads((tdir / "_result.json").read_text(encoding="utf-8"))
    results = res_raw["results"] if isinstance(res_raw, dict) else res_raw
    by_idx = {int(r["i"]): r["o"] for r in results if r.get("o") not in (None, "", [])}

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cols = {r[1] for r in con.execute("PRAGMA table_info(localized_text)")}
    has_layer = "layer" in cols
    has_islist = "is_list" in cols
    n = miss = 0
    for idx_s, rows in occ.items():
        idx = int(idx_s)
        out = by_idx.get(idx)
        if out is None:
            miss += 1
            continue
        for et, eid, field, is_list in rows:
            value = json.dumps(out, ensure_ascii=False) if is_list else (out if isinstance(out, str) else json.dumps(out, ensure_ascii=False))
            if has_layer and has_islist:
                cur.execute("INSERT OR REPLACE INTO localized_text (entity_type,entity_id,field,locale,value,"
                            "is_list,layer) VALUES (?,?,?,?,?,?,?)",
                            (et, eid, field, target, value, 1 if is_list else 0, "B"))
            else:
                cur.execute("INSERT OR REPLACE INTO localized_text (entity_type,entity_id,field,locale,value) "
                            "VALUES (?,?,?,?,?)", (et, eid, field, target, value))
            n += 1
    con.commit()
    con.close()
    print(f"task={task}: upserted {n} localized_text rows (locale={target}); distinct missing translation={miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
