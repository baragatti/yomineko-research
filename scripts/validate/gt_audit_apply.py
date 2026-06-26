#!/usr/bin/env python3
"""Apply ground-truth field-audit corrections: read research/derived/tr/gt-<key>/_result.json + _sample.json
and write each suggested correction to ALL localized_text rows (pt-BR) of that field-class whose current value
equals the flagged distinct value. Idempotent; keeps needs_review. Usage: gt_audit_apply.py <key> [--severity all|major]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from gt_audit_sample import CONFIG  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
# prose fields (explanations) legitimately use parentheticals like "(ou seja, ...)"; only a leftover
# "X / Y" slash-alternative is an artifact to reject here.
DIRTY = re.compile(r"\S\s+/\s+\S")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", choices=CONFIG)
    ap.add_argument("--severity", choices=["all", "major"], default="all")
    args = ap.parse_args()
    et, field, is_list, *_ = CONFIG[args.key]
    tdir = ROOT / "research" / "derived" / "tr" / ("gt-" + args.key.replace(".", "_"))
    samp = {s["id"]: s for s in json.loads((tdir / "_sample.json").read_text(encoding="utf-8"))}
    res = json.loads((tdir / "_result.json").read_text(encoding="utf-8"))
    flagged = res["flagged"] if isinstance(res, dict) else res
    con = sqlite3.connect(DB)
    applied = skipped = 0
    reasons: dict = {}
    for f in flagged:
        if args.severity == "major" and f.get("severity") != "major":
            continue
        sug = f.get("suggestion")
        s = samp.get(f.get("id"))
        if not s or sug in (None, "", []):
            skipped += 1; reasons["no-suggestion"] = reasons.get("no-suggestion", 0) + 1
            continue
        # normalize suggestion to the field's storage form
        if is_list:
            sug_list = sug if isinstance(sug, list) else [x.strip() for x in re.split(r"[;,/]", str(sug)) if x.strip()]
            new_val = json.dumps(sug_list, ensure_ascii=False)
        else:
            # gloss/label/explanation fields legitimately use "/" (multi-sense) and "(...)" (clarifiers);
            # no artifact filter here (that's only for full sentence translations).
            new_val = "; ".join(sug) if isinstance(sug, list) else sug
        old_val = json.dumps(s["pt"], ensure_ascii=False) if is_list else s["pt"]
        n = con.execute(
            "UPDATE localized_text SET value=? WHERE entity_type=? AND field=? AND locale='pt-BR' AND value=?",
            (new_val, et, field, old_val)).rowcount
        if n:
            applied += n
        else:
            skipped += 1; reasons["value-not-found"] = reasons.get("value-not-found", 0) + 1
    con.commit()
    con.close()
    print(f"{args.key}: applied to {applied} rows; skipped {skipped} {reasons}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
