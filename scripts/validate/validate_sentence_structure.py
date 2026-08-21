#!/usr/bin/env python3
"""Gate roadmap F: the `pattern[]` and `clause_structure` now stored on every dissected sentence.

pattern[] is derived from the token array, so it can drift out of agreement with the sentence it
describes the moment either side is edited — and a drill built on a chunk that is not in the sentence is
a question the learner cannot answer. That already happened once: punctuation was skipped rather than
closing a chunk, み えて、返事 became the single chunk みえて返事, and 325 role-drill options were text
that appears nowhere on the page. The reconstruction check below is what caught it, so it runs here on
every build rather than only when someone thinks to look.

CHECKS
  1. clause_structure is in the closed enum, and Layer C means every sentence carrying one is
     needs_review (a human still signs off on the judgement).
  2. pattern chunks + particles reconstruct the sentence minus punctuation. This is I1 for patterns.
  3. every chunk is a literal substring of jp -- implied by (2) but checked separately, because it is
     the property the app actually depends on when it renders options.
  4. pattern and clause_structure cover the same sentences. One without the other is a half-migration.
  5. every `role` is a known value. A typo'd role silently disappears from every drill instead of
     failing, which is the worst kind of quiet.

Usage: validate_sentence_structure.py
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "corpus" / "sentences" / "bank.json"

CLAUSE_ENUM = {"simple", "topic-comment", "relative-clause", "conditional", "quote", "cause",
               "coordinate", "subordinate-time", "question", "imperative", "fragment"}
ROLES = {"topic", "subject", "object", "also", "modifier", "from", "until", "direction", "than",
         "predicate", "phrase", "sentence-final", "nominalizer",
         "ni-phrase", "de-phrase", "to-phrase",
         "ga-clause", "kara-clause", "de-clause", "to-clause", "ni-clause", "te-kara"}
# NOT a character list. The builder's notion of punctuation is `pos_coarse == 補助記号`, which is data
# and cannot be reproduced by guessing at characters: the tokenizer marks a mid-word ー (べーラ) and a
# standalone っ (クソっ) as 補助記号 too. A hardcoded list reported six failures that were all the list's
# fault, so the bare form is rebuilt from the same tokens the builder used.
PUNCT_POS = "補助記号"


def main() -> int:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    fails: list[str] = []
    stats = Counter()

    for s in bank:
        slug, jp = s["slug"], s["jp"]
        cs, pat = s.get("clause_structure"), s.get("pattern")

        if cs is None and pat is None:
            stats["no structure (expected: pattern could not be derived)"] += 1
            continue
        if (cs is None) != (pat is None):
            fails.append(f"{slug}: has {'clause_structure' if cs else 'pattern'} but not the other")
            continue

        if cs not in CLAUSE_ENUM:
            fails.append(f"{slug}: clause_structure {cs!r} not in the closed enum")
        if not s.get("provenance", {}).get("needs_review"):
            fails.append(f"{slug}: carries Layer-C clause_structure but needs_review is false")

        bare = "".join(t["surface"] for t in s["tokens"]
                       if t["split_mode"] == "C" and t["pos_coarse"] != PUNCT_POS)
        joined = "".join(p["chunk"] + (p.get("particle") or "") for p in pat
                         if p["role"] != "sentence-final") + \
                 "".join(p["chunk"] for p in pat if p["role"] == "sentence-final")
        if joined != bare:
            fails.append(f"{slug}: chunks do not reconstruct the sentence\n"
                         f"      got {joined}\n      want {bare}")
        for p in pat:
            if p["role"] not in ROLES:
                fails.append(f"{slug}: unknown role {p['role']!r}")
            if p["chunk"] not in jp:
                # Real, and app-facing: the drill renders this chunk as an option next to `jp`, so a
                # chunk the learner cannot find on the page is unanswerable. Happens where the tokenizer
                # classes a mid-word character as 補助記号 (べーラ -> べラ, クソっ -> クソ).
                fails.append(f"{slug}: chunk {p['chunk']!r} is not a substring of {jp!r}")
        stats[cs] += 1

    total = sum(v for k, v in stats.items() if k in CLAUSE_ENUM)
    print(f"validate_sentence_structure: {total} sentences with pattern + clause_structure, "
          f"{len(fails)} FAIL")
    print("  " + "  ".join(f"{k}={v}" for k, v in stats.most_common() if k in CLAUSE_ENUM))
    skipped = {k: v for k, v in stats.items() if k not in CLAUSE_ENUM}
    if skipped:
        print(f"  {skipped}")
    for f in fails[:25]:
        print(f"  [FAIL] {f}")
    if len(fails) > 25:
        print(f"  ... and {len(fails) - 25} more")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
