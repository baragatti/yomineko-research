#!/usr/bin/env python3
"""form_meanings is a dict {form: meaning}; the generic string/list pipeline can't carry it. This handles it:
  extract -> distinct meaning VALUES (strings) as a batch for tr_workflow (TASK='form_meanings') + _vmap.json
  load    -> reassemble each grammar_point's form_meanings dict with EN values -> localized_text en (is_list).
Usage: tr_form_meanings.py extract|load
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
TDIR = ROOT / "research" / "derived" / "tr" / "form_meanings"


def main() -> int:
    mode = sys.argv[1]
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT entity_id, value FROM localized_text WHERE entity_type='grammar_point' "
                       "AND field='form_meanings' AND locale='pt-BR'").fetchall()
    dicts = {eid: json.loads(v) for eid, v in rows if v}

    if mode == "extract":
        distinct: dict[str, int] = {}
        for d in dicts.values():
            for val in d.values():
                s = str(val)
                if s and s not in distinct:
                    distinct[s] = len(distinct)
        TDIR.mkdir(parents=True, exist_ok=True)
        for old in TDIR.glob("batch_*.json"):
            old.unlink()
        items = [{"i": i, "t": s} for s, i in distinct.items()]
        TDIR.joinpath("batch_0000.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        TDIR.joinpath("_vmap.json").write_text(json.dumps(distinct, ensure_ascii=False), encoding="utf-8")
        print(f"form_meanings: {len(items)} distinct values -> 1 batch")
        return 0

    # load
    vmap = json.loads((TDIR / "_vmap.json").read_text(encoding="utf-8"))  # value -> idx
    res = json.loads((TDIR / "_result.json").read_text(encoding="utf-8"))
    results = res["results"] if isinstance(res, dict) else res
    en_by_idx = {int(r["i"]): r["o"] for r in results}
    en_by_val = {val: en_by_idx.get(idx) for val, idx in vmap.items()}
    cur = con.cursor()
    n = 0
    for eid, d in dicts.items():
        en = {}
        for form, val in d.items():
            t = en_by_val.get(str(val))
            if t:
                en[form] = t if isinstance(t, str) else (t[0] if isinstance(t, list) and t else str(t))
        if en:
            cur.execute("INSERT OR REPLACE INTO localized_text (entity_type,entity_id,field,locale,value,"
                        "is_list,layer) VALUES ('grammar_point',?,'form_meanings','en',?,1,'B')",
                        (eid, json.dumps(en, ensure_ascii=False)))
            n += 1
    con.commit()
    con.close()
    print(f"form_meanings: upserted en dicts for {n} grammar points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
