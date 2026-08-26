#!/usr/bin/env python3
"""One-shot migration: make every true/false field an actual JSON boolean, under one name.

Two spellings of the same fact had drifted into the exported corpus:

  * `needs_review` was `true`/`false` on grammar, lesson, sentence, speak_* and `1`/`0` on exam items,
    conjugation drills, role drills and readings. A client that writes `if (r.needs_review === true)`
    reads the integer form as false and silently ships unreviewed Layer-C material as approved.
  * "this was AI-generated" was spelled three ways: `ai` (int) on exam items, `ai_generated` (int) on
    readings, `ai_generated` (bool) on sentences.

The producers are fixed at the source (`build_*.py`, `export_readings.py`), so re-running an exporter
now emits booleans. The exam banks are the exception: `db/corpus.sqlite` currently holds a thinner
`sentence_vocab` than the one those banks were built from — regenerating them drops n3_context_fill
from 400 items to 97 — so they must be edited in place until that index is repaired. This script does
exactly that edit and nothing else.

Idempotent: a second run reports 0 changes. Key order is preserved so the diff stays legible.
Usage: normalize_booleans.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]

# name -> canonical name. `ai` is renamed as well as retyped.
BOOL_FIELDS = {"needs_review": "needs_review", "ai_generated": "ai_generated", "ai": "ai_generated"}
TARGETS = ["corpus/**/*.json", "course/**/*.json"]


def fix(node: object, tally: Counter) -> object:
    """Rewrite in place, depth-first, preserving key insertion order."""
    if isinstance(node, list):
        return [fix(x, tally) for x in node]
    if not isinstance(node, dict):
        return node
    out: dict = {}
    for k, v in node.items():
        canon = BOOL_FIELDS.get(k)
        if canon is None:
            out[k] = fix(v, tally)
            continue
        # bool is a subclass of int, so the isinstance order matters: check bool first.
        if isinstance(v, bool):
            new = v
        elif isinstance(v, int) and v in (0, 1):
            new = bool(v)
            tally[f"{k} int -> bool"] += 1
        else:
            out[k] = v  # not a 0/1 int and not a bool: leave it and let the schema flag it
            continue
        if k != canon:
            tally[f"{k} -> {canon}"] += 1
        out[canon] = new
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if anything would change")
    args = ap.parse_args()

    total, touched = Counter(), []
    for pattern in TARGETS:
        for path in sorted(ROOT.glob(pattern)):
            raw = path.read_text(encoding="utf-8")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(f"  ! {path.relative_to(ROOT)}: {exc}")
                return 2
            tally: Counter = Counter()
            fixed = fix(data, tally)
            if not tally:
                continue
            total.update(tally)
            rel = str(path.relative_to(ROOT)).replace("\\", "/")
            touched.append((rel, sum(tally.values())))
            if not args.check:
                # Match the exporters' own format exactly, so this migration is the only thing the diff shows.
                path.write_text(json.dumps(fixed, ensure_ascii=False), encoding="utf-8")

    verb = "would change" if args.check else "changed"
    for rel, n in touched:
        print(f"  {verb:13} {n:>6}  {rel}")
    print(f"\n{len(touched)} file(s), {sum(total.values())} field(s) {verb}")
    for k, n in total.most_common():
        print(f"   {k:28} {n}")
    return 1 if (args.check and touched) else 0


if __name__ == "__main__":
    sys.exit(main())
