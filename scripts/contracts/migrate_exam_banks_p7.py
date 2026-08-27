#!/usr/bin/env python3
"""One-shot migration of the committed exam banks: explicit provenance, published vocab slugs, and
removal of self-revealing stems.

The banks cannot yet be regenerated (regeneration is a deliberate future migration: even with the
sentence_vocab index repaired, ~100 non-context_fill items differ for reasons that need item-level
review — see STATE.md), so the three defects the review confirmed are fixed in place:

  1. PROVENANCE (spec 1.1/1.2): 5,275 of 6,166 items carried no layer and no needs_review, 359
     ai_generated items had no needs_review, and paraphrase/usage items had no ai_generated at all —
     which the exam picker's real-first rule read as "real". Every item now carries source, layer,
     ai_generated and needs_review explicitly:
       - kanji_reading / orthography: derived straight off Layer-A vocab -> layer B, ai_generated
         false, needs_review false.
       - context_fill / grammar_form / sentence_order: mechanical derivations of ONE sentence ->
         layer B; ai_generated copied from that sentence's provenance; needs_review true exactly when
         the underlying sentence is generated.
       - text_grammar: mechanical blanking of a reading passage (passages are selections of real bank
         sentences) -> layer B, ai_generated false, needs_review false.
       - reading_comp / paraphrase / usage / listening_*: AI-authored question apparatus ->
         layer C, needs_review true. ai_generated on an exam item means "the JAPANESE the learner
         reads was model-generated rather than selected from a real source" — that is what the exam
         picker's real-first rule keys on — so paraphrase/usage copy it from their stem sentence's
         provenance (42 of 366 are true), reading_comp is false (passages are selections of real
         bank sentences), and listening stays true (the scripts are generated Japanese). The
         AUTHOREDNESS of the question is already expressed by layer C + needs_review; giving
         ai_generated a second meaning would erase the real-vs-generated distinction inside the
         authored banks, which is the exact defect EB-04 confirmed.
  2. ADDRESSES: 3,777 items referenced vocabulary only by `vocab_id`, a storage row number that
     contracts/README.md forbids as an address. Every such item gains `vocab`: the published
     vocab:<jmdict_id> slug. vocab_id stays for compatibility.
  3. ANSWER LEAKS: 93 items' stems contain their own `correct` string outside the blank (the builder
     blanks only the first occurrence). The banks run 9x-68x their paper requirements, so the items
     are REMOVED rather than patched; corpus/exam_banks/removed_items.json records every removed item
     in full, with the reason, so nothing is silently lost. The builder-side guard (skip candidates
     whose target occurs more than once) is a separate change for the future regeneration.

Idempotent: a second run changes nothing. INDEX.md counts are rewritten to match.
Usage: migrate_exam_banks_p7.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "corpus" / "exam_banks"
DB = ROOT / "db" / "corpus.sqlite"

BLANK = "（　）"

# id prefix -> (layer, authored?)  — authored means the QUESTION text is AI-written (Layer C).
FAMILY = {
    "kr": ("B", False), "or": ("B", False),
    "cf": ("B", False), "gf": ("B", False), "so": ("B", False), "tg": ("B", False),
    "rc": ("C", True), "pp": ("C", True), "us": ("C", True),
    "lt": ("C", True), "lp": ("C", True), "ls": ("C", True), "lr": ("C", True), "lg": ("C", True),
}
# Families whose ai_generated comes from the referenced sentence rather than the family default.
SENTENCE_DERIVED = {"cf", "gf", "so", "pp", "us"}
# Families whose Japanese is always real (selection/derivation from human-written sources).
ALWAYS_REAL = {"kr", "or", "tg", "rc"}
# source fill-ins for families whose builder never wrote one (checked against the data at run time).
DEFAULT_SOURCE = {"kr": "vocab", "or": "vocab", "tg": "reading+grammar",
                  # authored listening scripts wrapped around bank sentences (design/listening.md);
                  # the five listening families were the only 239 items with no source at all
                  "lt": "listening-script", "lp": "listening-script", "ls": "listening-script",
                  "lr": "listening-script", "lg": "listening-script"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    slug_of_vid = {vid: slug for vid, slug in con.execute("SELECT id, slug FROM vocab")}
    con.close()
    bank = json.loads((ROOT / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))
    sent_ai = {r["slug"]: bool(r.get("provenance", {}).get("ai_generated")) for r in bank}

    changed_fields = 0
    removed: list = []
    new_counts: dict = {}
    for path in sorted(BANKS.glob("*.json")):
        if path.name == "removed_items.json":
            continue
        items = json.loads(path.read_text(encoding="utf-8"))
        out = []
        touched = False
        for it in items:
            fam = it["id"].split(":", 1)[0]
            layer, authored = FAMILY.get(fam, ("B", False))

            # ---- 3. answer leaks: stem still contains `correct` after the blank is removed -------
            stem, correct = it.get("stem"), it.get("correct")
            if isinstance(stem, str) and isinstance(correct, str) and BLANK in stem and correct:
                if correct in stem.replace(BLANK, ""):
                    removed.append({"file": path.name, "reason": "stem contains its own answer "
                                    "outside the blank (builder blanked only the first occurrence)",
                                    "item": it})
                    touched = True
                    continue

            rec = dict(it)

            # ---- 2. published vocab slug ---------------------------------------------------------
            if isinstance(rec.get("vocab_id"), int) and "vocab" not in rec:
                slug = slug_of_vid.get(rec["vocab_id"])
                if slug:
                    rec["vocab"] = slug

            # ---- 1. explicit provenance ----------------------------------------------------------
            if "layer" not in rec:
                rec["layer"] = layer
            if "source" not in rec and fam in DEFAULT_SOURCE:
                rec["source"] = DEFAULT_SOURCE[fam]
            # ai_generated is fully DERIVED (except listening, whose builder writes it), so the
            # rule can be re-run and always lands on the same value. needs_review is never lowered.
            if fam in SENTENCE_DERIVED:
                rec["ai_generated"] = sent_ai.get(rec.get("sentence"), False)
            elif fam in ALWAYS_REAL:
                rec["ai_generated"] = False
            elif "ai_generated" not in rec:
                rec["ai_generated"] = True          # listening scripts are generated Japanese
            if rec.get("ai_generated") and rec.get("needs_review") is not True:
                rec["needs_review"] = True          # spec 1.2: generated => needs a teacher
            if "needs_review" not in rec:
                rec["needs_review"] = bool(authored)

            if rec != it:
                changed_fields += sum(1 for k in rec if rec.get(k) != it.get(k))
                touched = True
            out.append(rec)

        new_counts[path.stem] = len(out)
        if touched and not args.check:
            path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    # ---- removed-items ledger + INDEX counts ----------------------------------------------------
    if removed and not args.check:
        ledger_path = BANKS / "removed_items.json"
        prior = []
        if ledger_path.exists():
            prior = json.loads(ledger_path.read_text(encoding="utf-8")).get("items", [])
        known = {(r["file"], r["item"]["id"]) for r in prior}
        prior += [r for r in removed if (r["file"], r["item"]["id"]) not in known]
        ledger_path.write_text(json.dumps(
            {"why": "Items removed from the committed banks by scripts/contracts/"
                    "migrate_exam_banks_p7.py, kept here in full so nothing is silently lost. "
                    "They are eligible to return when the banks are regenerated with the fixed "
                    "builder.",
             "count": len(prior), "items": prior}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")

    index = BANKS / "INDEX.md"
    if index.exists() and not args.check:
        text = index.read_text(encoding="utf-8")
        for stem, cnt in new_counts.items():
            text = re.sub(rf"(`{re.escape(stem)}\.json`[^|\n]*\|\s*)(\d+)", rf"\g<1>{cnt}", text)
            text = re.sub(rf"(\|\s*)(\d+)(\s*\|[^|\n]*`{re.escape(stem)}\.json`)", rf"\g<1>{cnt}\g<3>", text)
        total = sum(new_counts.values())
        text = re.sub(r"\b6,?166\b", f"{total:,}", text)
        index.write_text(text, encoding="utf-8")

    verb = "would change" if args.check else "changed"
    print(f"{verb}: {changed_fields} field additions across banks; removed {len(removed)} "
          f"self-revealing items; totals now {sum(new_counts.values())}")
    by_file: dict = {}
    for r in removed:
        by_file[r["file"]] = by_file.get(r["file"], 0) + 1
    for f, c in sorted(by_file.items()):
        print(f"   -{c:>3}  {f}")
    return 1 if (args.check and (changed_fields or removed)) else 0


if __name__ == "__main__":
    sys.exit(main())
