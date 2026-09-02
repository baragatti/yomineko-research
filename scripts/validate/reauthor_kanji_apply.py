#!/usr/bin/env python3
"""Apply re-authored kanji meanings (license_audit.md D-LIC-1). Replaces the verbatim-KANJIDIC2 (CC BY-SA)
meanings with our independently-authored, verifier-checked glosses: pt-BR -> localized_text(kanji,meanings,pt-BR)
[what the exporter ships as pt], en -> kanji.meanings_en column [what the exporter ships as en] + meanings_pt
column for consistency. Facts (readings/strokes/radical) are untouched and stay KANJIDIC-attributed. Idempotent.
Usage: reauthor_kanji_apply.py [--dry-run]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
RES = ROOT / "research" / "derived" / "reauthor" / "kanji" / "_result.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    items = json.loads(RES.read_text(encoding="utf-8"))["items"]
    con = sqlite3.connect(DB)
    leveled = {r[0] for r in con.execute("SELECT id FROM kanji WHERE level IN ('n5','n4','n3','n2','n1')")}
    applied = skipped = 0
    for it in items:
        kid, en, pt = it.get("id"), it.get("en"), it.get("pt")
        if kid not in leveled or not en or not pt or any(not str(x).strip() for x in en + pt):
            skipped += 1
            continue
        if not args.dry_run:
            con.execute("UPDATE kanji SET meanings_en=?, meanings_pt=? WHERE id=?",
                        (json.dumps(en, ensure_ascii=False), json.dumps(pt, ensure_ascii=False), kid))
            con.execute("UPDATE localized_text SET value=?, layer='B' WHERE entity_type='kanji' AND entity_id=? "
                        "AND field='meanings' AND locale='pt-BR'", (json.dumps(pt, ensure_ascii=False), kid))
        applied += 1
    if not args.dry_run:
        con.commit()
    con.close()
    print(f"reauthor-kanji apply ({'dry-run' if args.dry_run else 'applied'}): {applied} kanji meanings replaced "
          f"(SA-free), {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
