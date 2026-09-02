#!/usr/bin/env python3
"""Re-blank text_grammar exam items whose reading passage changed under them.

A text_grammar item is a reading passage with one blank: `stem` == passage with `correct` replaced
by （　） (validate_exam_banks rule I, which is what makes it safe for the app not to render the
passage separately). The readings composition campaign (scripts/apply_readings_composition_repairs.py)
inserted 。 at glued sentence junctions and replaced duplicate sentences in 52 boxes, so 31 tg items
now carry a stem cut from a passage that no longer exists.

For each such item the blank is re-cut from the CURRENT passage:
  - `correct` occurs exactly once in the new passage  -> stem = passage with that occurrence blanked
  - occurs zero times (its sentence was the one replaced) -> the item has no answer; retired into
    corpus/exam_banks/removed_items.json with the reason
  - occurs more than once -> would be a self-revealing stem (the class migrate_exam_banks_p7 removed
    93 of); retired the same way
The banks run 9-68x their paper requirements, so retiring is safe and honest; rebuilding the item
belongs to the regeneration (PENDING.md A2). Reads the EXPORTED passages (corpus/readings/*.json).
Idempotent; --check; loud skips. Usage: apply_text_grammar_restem.py [--check]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
BANKS = ROOT / "corpus" / "exam_banks"
LEDGER = BANKS / "removed_items.json"
BLANK = "（　）"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, data) -> None:
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    passage = {}
    for f in glob.glob(str(ROOT / "corpus" / "readings" / "n[0-9].json")):
        for r in load(Path(f)):
            passage[r["slug"]] = r["jp"]

    ledger = load(LEDGER) if LEDGER.exists() else {"count": 0, "items": []}
    already = {(e["file"], e["item"]["id"]) for e in ledger["items"]}
    restemmed, retired, ok, skipped = 0, [], 0, []

    for path in sorted(BANKS.glob("n[0-9]_text_grammar.json")):
        items = load(path)
        out, touched = [], False
        for it in items:
            ref = it.get("reading") or it.get("passage_ref") or it.get("source_reading")
            if not ref:
                skipped.append(f"{it['id']}: no reading reference field — leaving as is")
                out.append(it); continue
            p = passage.get(ref)
            if p is None:
                skipped.append(f"{it['id']}: passage {ref} not in corpus/readings — leaving as is")
                out.append(it); continue
            correct = it.get("correct", "")
            if not (isinstance(correct, str) and correct and BLANK in it.get("stem", "")):
                out.append(it); continue
            if it["stem"].replace(BLANK, correct, 1) == p:
                ok += 1; out.append(it); continue
            n = p.count(correct)
            if n == 1:
                new_stem = p.replace(correct, BLANK, 1)
                print(f"  {it['id']}: re-cut from current passage")
                it = dict(it, stem=new_stem)
                restemmed += 1; touched = True
                out.append(it)
            else:
                why = ("its answer no longer occurs in the passage (the sentence carrying it was "
                       "replaced by the readings composition repair)" if n == 0 else
                       f"its answer now occurs {n} times in the passage, so the re-cut stem would "
                       f"reveal it (the self-revealing class)")
                print(f"  {it['id']}: retired — {why}")
                if (path.name, it["id"]) not in already:
                    retired.append({"file": path.name, "reason": "text_grammar passage changed; " + why,
                                    "item": it})
                touched = True
        if touched and not args.check:
            dump(path, out)

    if retired and not args.check:
        ledger["items"].extend(retired)
        ledger["count"] = len(ledger["items"])
        dump(LEDGER, ledger)
    verb = "would re-cut" if args.check else "re-cut"
    print(f"\n{verb} {restemmed}; retired {len(retired)}; already consistent {ok}")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and (restemmed or retired)) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
