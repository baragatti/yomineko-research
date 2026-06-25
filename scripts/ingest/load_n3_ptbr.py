#!/usr/bin/env python3
"""Load AI-generated N3 pt-BR Layer-B glosses (from a workflow output file) into the DB localized_text.

Usage: load_n3_ptbr.py <kanji|vocab> <workflow_output.json>
  kanji: result.items = [{id, pt:[...]}]            -> localized_text(kanji, <id>, 'meanings', 'pt-BR')
  vocab: result.items = [{id, senses:[{sid, pt}]}]  -> localized_text(vocab_sense, <sid>, 'gloss', 'pt-BR')
Idempotent (delete-then-insert per key). Marks the row needs_review=1 (single-lineage N3 Layer-B).
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"


def load_items(path: str):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    r = raw.get("result", raw)
    if isinstance(r, str):
        r = json.loads(r[r.index("{"):])
    return r.get("items", [])


def setlt(cur, etype, eid, field, value_list):
    cur.execute("DELETE FROM localized_text WHERE entity_type=? AND entity_id=? AND field=? AND locale='pt-BR'",
                (etype, eid, field))
    cur.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
                "VALUES (?,?,?,'pt-BR',?,1,'B')", (etype, eid, field, json.dumps(value_list, ensure_ascii=False)))


def main() -> int:
    mode, path = sys.argv[1], sys.argv[2]
    con = sqlite3.connect(DB); cur = con.cursor()
    items = load_items(path)
    n = 0
    if mode == "kanji":
        for it in items:
            pt = [x for x in (it.get("pt") or []) if x and x.strip()]
            if not pt:
                continue
            setlt(cur, "kanji", it["id"], "meanings", pt)
            cur.execute("UPDATE kanji SET needs_review=1 WHERE id=?", (it["id"],))
            n += 1
    elif mode == "vocab":
        for it in items:
            for s in (it.get("senses") or []):
                pt = [x for x in (s.get("pt") or []) if x and x.strip()]
                if not pt:
                    continue
                setlt(cur, "vocab_sense", s["sid"], "gloss", pt)
                cur.execute("UPDATE vocab_sense SET needs_review=1 WHERE id=?", (s["sid"],))
                n += 1
    else:
        print("unknown mode", mode); return 1
    con.commit()
    print(f"loaded {mode} pt-BR: {n} entries from {len(items)} items")
    con.close(); return 0


if __name__ == "__main__":
    sys.exit(main())
