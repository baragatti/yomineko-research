#!/usr/bin/env python3
"""Apply the Fable 5 phase-1 confirmed kanji-meaning fixes (reports/fable5_validation.md).
Same write pattern as scripts/validate/reauthor_kanji_apply.py: en -> kanji.meanings_en,
pt -> kanji.meanings_pt + localized_text(kanji, meanings, pt-BR). Facts untouched. Idempotent.
Patch source: research/derived/fable5_validation/phase1_kanji_patch.json (slug -> changed fields only).
Usage: fable5_kanji_apply.py [--dry-run]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
PATCH = ROOT / "research" / "derived" / "fable5_validation" / "phase1_kanji_patch.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    patch: dict[str, dict[str, list[str]]] = json.loads(PATCH.read_text(encoding="utf-8"))["patch"]
    con = sqlite3.connect(DB)
    applied = missing = 0
    for slug, fields in patch.items():
        ch = slug.split(":", 1)[1]
        row = con.execute("SELECT id, meanings_en, meanings_pt FROM kanji WHERE character=?", (ch,)).fetchone()
        if not row:
            print(f"MISSING in DB: {slug}")
            missing += 1
            continue
        kid, cur_en, cur_pt = row
        new_en = fields.get("en") or json.loads(cur_en)
        new_pt = fields.get("pt") or json.loads(cur_pt)
        if not args.dry_run:
            con.execute("UPDATE kanji SET meanings_en=?, meanings_pt=? WHERE id=?",
                        (json.dumps(new_en, ensure_ascii=False), json.dumps(new_pt, ensure_ascii=False), kid))
            if "pt" in fields:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='kanji' AND entity_id=? "
                            "AND field='meanings' AND locale='pt-BR'",
                            (json.dumps(new_pt, ensure_ascii=False), kid))
        applied += 1
    if not args.dry_run:
        con.commit()
    con.close()
    print(f"fable5 kanji apply ({'dry-run' if args.dry_run else 'applied'}): {applied} kanji updated, {missing} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
