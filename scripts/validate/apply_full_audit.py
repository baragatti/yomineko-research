#!/usr/bin/env python3
"""Apply the full-sentence-audit fixes: read research/derived/tr/full/_result.json (the workflow's flagged
list) + _sample.json, and write each suggested correction to the right localized_text field
(natural -> 'translation', literal -> 'translation_literal'), pt-BR. Idempotent; keeps needs_review.
Skips entries without a usable suggestion or whose suggestion still contains an artifact. Prints a summary +
the affected slugs (for re-export). Usage: apply_full_audit.py [--severity major|all]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text, get_text  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
TDIR = ROOT / "research" / "derived" / "tr" / "full"
DIRTY = re.compile(r"\S\s+/\s+\S|\((ou |isto é|i\.e\.|do tipo |a saber)", re.I)
FIELD = {"natural": "translation", "literal": "translation_literal"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--severity", choices=["major", "all"], default="all")
    args = ap.parse_args()
    samp = {s["id"]: s for s in json.loads((TDIR / "_sample.json").read_text(encoding="utf-8"))}
    res = json.loads((TDIR / "_result.json").read_text(encoding="utf-8"))
    flagged = res["flagged"] if isinstance(res, dict) else res
    con = sqlite3.connect(DB)
    applied = skipped = 0
    skip_reasons: dict = {}
    touched_slugs = set()
    for f in flagged:
        if args.severity == "major" and f.get("severity") != "major":
            continue
        sug = (f.get("suggestion") or "").strip()
        fld = FIELD.get(f.get("field", ""))
        s = samp.get(f.get("id"))
        if not (sug and fld and s):
            skipped += 1; skip_reasons["no-suggestion/field"] = skip_reasons.get("no-suggestion/field", 0) + 1
            continue
        if DIRTY.search(sug):
            skipped += 1; skip_reasons["suggestion-still-dirty"] = skip_reasons.get("suggestion-still-dirty", 0) + 1
            continue
        sid = con.execute("SELECT id FROM sentence WHERE slug=?", (s["slug"],)).fetchone()
        if not sid:
            skipped += 1; continue
        cur = get_text(con, "sentence", sid[0], fld)
        if cur == sug:
            skipped += 1; skip_reasons["no-change"] = skip_reasons.get("no-change", 0) + 1
            continue
        set_text(con, "sentence", sid[0], fld, sug, "pt-BR", "B")
        applied += 1
        touched_slugs.add(s["slug"])
    con.commit()
    con.close()
    print(f"applied {applied}; skipped {skipped} {skip_reasons}")
    print(f"touched {len(touched_slugs)} sentences")
    (TDIR / "_applied_slugs.json").write_text(json.dumps(sorted(touched_slugs), ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
