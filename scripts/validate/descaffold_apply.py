#!/usr/bin/env python3
"""Apply de-scaffold rewrites: read research/derived/tr/descaffold/_result.json (the workflow's returned
{items:[{id, pt, en}]}) + _sample.json (maps id -> entity_type/entity_id), and write each cleaned pt + en back
to localized_text BY entity_id (prose is unique, so direct per-entity update). Refuses to write a value that
still contains an internal artifact (safety). Keeps needs_review. Usage: descaffold_apply.py [--dry-run]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
# locale-aware guard: in pt-BR "target"/"candidato" are leaks; in en they are legitimate English words
PT_LEAK = re.compile(r"gp-\d+|candidat[oae]s?\b|candidate\b|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])"
                     r"|\btarget\b|\bjec\b|位置\s*\d|posi[çc][ãa]o\s*\d", re.I)
EN_LEAK = re.compile(r"gp-\d+|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])|\bjec\b|位置\s*\d", re.I)
LEAKS = {"pt-BR": PT_LEAK, "en": EN_LEAK}
FIELD = {"sentence": "structure_explanation", "particle": "explanation", "token": "role"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    tdir = ROOT / "research" / "derived" / "tr" / "descaffold"
    samp = {s["id"]: s for s in json.loads((tdir / "_sample.json").read_text(encoding="utf-8"))}
    res = json.loads((tdir / "_result.json").read_text(encoding="utf-8"))
    items = res["items"] if isinstance(res, dict) and "items" in res else res
    con = sqlite3.connect(DB)
    applied = skipped = dirty = 0
    for it in items:
        s = samp.get(it.get("id"))
        if not s:
            skipped += 1; continue
        et, eid = s["entity_type"], s["entity_id"]
        field = FIELD[et]
        for loc, val in (("pt-BR", it.get("pt")), ("en", it.get("en"))):
            if not val or not val.strip():
                skipped += 1; continue
            if LEAKS[loc].search(val):
                dirty += 1; continue  # still has an artifact -> refuse (will be handled in 2nd pass)
            if not args.dry_run:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND field=? AND locale=?",
                            (val, et, eid, field, loc))
            applied += 1
    if not args.dry_run:
        con.commit()
    con.close()
    print(f"descaffold apply ({'dry-run' if args.dry_run else 'applied'}): wrote {applied}; "
          f"refused-dirty {dirty}; skipped {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
