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
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
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
        # `kanji.meanings_pt` is the pre-i18n column. Since persist_meanings.py started writing through
        # i18n_text.set_text, localized_text is the only thing that gets written and the column is a
        # leftover — populated on this machine, NULL in a database rebuilt from the tracked scripts
        # (W01). Read the fallback from where the exporter reads, and treat both columns as optional.
        loc = con.execute("SELECT value FROM localized_text WHERE entity_type='kanji' AND entity_id=? "
                          "AND field='meanings' AND locale='pt-BR'", (kid,)).fetchone()
        new_en = fields.get("en") or (json.loads(cur_en) if cur_en else [])
        new_pt = fields.get("pt") or (json.loads(cur_pt) if cur_pt else (json.loads(loc[0]) if loc else []))
        if not args.dry_run:
            con.execute("UPDATE kanji SET meanings_en=?, meanings_pt=? WHERE id=?",
                        (json.dumps(new_en, ensure_ascii=False), json.dumps(new_pt, ensure_ascii=False), kid))
            if "pt" in fields:
                # UPDATE alone silently no-ops when the row does not exist yet, which is what a rebuild
                # looks like before the translation pipeline has run; insert the layer-B row instead.
                v = json.dumps(new_pt, ensure_ascii=False)
                if con.execute("UPDATE localized_text SET value=? WHERE entity_type='kanji' AND entity_id=? "
                               "AND field='meanings' AND locale='pt-BR'", (v, kid)).rowcount == 0:
                    con.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,"
                                "is_list,layer) VALUES ('kanji',?,'meanings','pt-BR',?,1,'B')", (kid, v))
        applied += 1
    if not args.dry_run:
        con.commit()
    con.close()
    print(f"fable5 kanji apply ({'dry-run' if args.dry_run else 'applied'}): {applied} kanji updated, {missing} missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
