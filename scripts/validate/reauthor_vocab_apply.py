#!/usr/bin/env python3
"""Apply re-authored vocab senses (license_audit.md D-LIC-1). For each vocab, REPLACE its JMdict-derived senses
with our independently-authored core senses: delete old vocab_sense rows (+ their localized_text gloss), insert
the new senses carrying the word's POS. Writes gloss_en column (exporter's en) + gloss_pt column + localized_text
pt-BR (exporter's pt). Nothing references senses by id, so this is safe. Idempotent on re-run (replaces again).
Usage: reauthor_vocab_apply.py [--dry-run]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
RES = ROOT / "research" / "derived" / "reauthor" / "vocab" / "_result.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    items = json.loads(RES.read_text(encoding="utf-8"))["items"]
    con = sqlite3.connect(DB)
    vocab_ids = {r[0] for r in con.execute("SELECT id FROM vocab")}
    applied = skipped = newsenses = 0
    for it in items:
        vid, senses = it.get("id"), it.get("senses") or []
        senses = [s for s in senses if s.get("en") and s.get("pt")
                  and not any(not str(x).strip() for x in s["en"] + s["pt"])]
        if vid not in vocab_ids or not senses:
            skipped += 1
            continue
        if args.dry_run:
            applied += 1; newsenses += len(senses); continue
        old = con.execute("SELECT id, pos FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order", (vid,)).fetchall()
        pos = old[0][1] if old else "[]"
        for oid, _ in old:
            con.execute("DELETE FROM localized_text WHERE entity_type='vocab_sense' AND entity_id=? AND field='gloss'", (oid,))
        con.execute("DELETE FROM vocab_sense WHERE vocab_id=?", (vid,))
        for i, s in enumerate(senses):
            en, pt = s["en"], s["pt"]
            cur = con.execute(
                "INSERT INTO vocab_sense (vocab_id, sense_order, pos, field_tags, misc_tags, gloss_en, gloss_pt, "
                "needs_review) VALUES (?,?,?,'[]','[]',?,?,1)",
                (vid, i, pos, json.dumps(en, ensure_ascii=False), json.dumps(pt, ensure_ascii=False)))
            con.execute("INSERT INTO localized_text (entity_type, entity_id, field, locale, value, is_list, layer) "
                        "VALUES ('vocab_sense', ?, 'gloss', 'pt-BR', ?, 1, 'B')",
                        (cur.lastrowid, json.dumps(pt, ensure_ascii=False)))
            newsenses += 1
        applied += 1
    if not args.dry_run:
        con.commit()
    con.close()
    print(f"reauthor-vocab apply ({'dry-run' if args.dry_run else 'applied'}): {applied} vocab re-sensed "
          f"({newsenses} new senses), {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
