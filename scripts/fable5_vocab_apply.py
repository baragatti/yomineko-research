#!/usr/bin/env python3
"""Apply the Phase-2 confirmed vocab-gloss fixes (reports/fable5_validation.md Phase 2; owner go-ahead
2026-07-09). Patch source: research/derived/fable5_validation/phase2_vocab_patch.json — full NEW senses
array (+ optional romaji) per vocab slug, generated + human-reviewed via fable5_vocab_patch_gen.py.
Write pattern mirrors reauthor_vocab_apply.py: delete old vocab_sense rows (+ their localized_text gloss),
insert the new senses (per-sense pos/field/misc preserved), localized_text pt-BR mirror per sense.
Idempotent. Usage: fable5_vocab_apply.py [--dry-run]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
PATCH = ROOT / "research" / "derived" / "fable5_validation" / "phase2_vocab_patch.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    patch = json.loads(PATCH.read_text(encoding="utf-8"))["patch"]
    con = sqlite3.connect(DB)
    applied = senses_written = romaji_set = 0
    for slug, entry in patch.items():
        row = con.execute("SELECT id FROM vocab WHERE slug=?", (slug,)).fetchone()
        if not row:
            print(f"MISSING in DB: {slug}")
            return 1
        vid = row[0]
        if args.dry_run:
            applied += 1; senses_written += len(entry["senses"]); continue
        old = con.execute("SELECT id FROM vocab_sense WHERE vocab_id=?", (vid,)).fetchall()
        for (oid,) in old:
            con.execute("DELETE FROM localized_text WHERE entity_type='vocab_sense' AND entity_id=? "
                        "AND field='gloss'", (oid,))
        con.execute("DELETE FROM vocab_sense WHERE vocab_id=?", (vid,))
        for i, s in enumerate(entry["senses"]):
            cur = con.execute(
                "INSERT INTO vocab_sense (vocab_id, sense_order, pos, field_tags, misc_tags, gloss_en, "
                "gloss_pt, needs_review) VALUES (?,?,?,?,?,?,?,1)",
                (vid, i, json.dumps(s["pos"], ensure_ascii=False),
                 json.dumps(s.get("field", []), ensure_ascii=False),
                 json.dumps(s.get("misc", []), ensure_ascii=False),
                 json.dumps(s["en"], ensure_ascii=False), json.dumps(s["pt"], ensure_ascii=False)))
            con.execute("INSERT INTO localized_text (entity_type, entity_id, field, locale, value, is_list, "
                        "layer) VALUES ('vocab_sense', ?, 'gloss', 'pt-BR', ?, 1, 'B')",
                        (cur.lastrowid, json.dumps(s["pt"], ensure_ascii=False)))
            senses_written += 1
        if entry.get("romaji"):
            con.execute("UPDATE vocab SET romaji=? WHERE id=?", (entry["romaji"], vid))
            romaji_set += 1
        applied += 1
    if not args.dry_run:
        con.commit()
    con.close()
    print(f"fable5 vocab apply ({'dry-run' if args.dry_run else 'applied'}): {applied} vocab re-sensed "
          f"({senses_written} senses), {romaji_set} romaji updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
