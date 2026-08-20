#!/usr/bin/env python3
"""Apply the reviewer-agreed corrections to the v3 kanji reading notes, before they are merged.

The v3 pass carried design/authoring_failure_modes.md in its prompt and the effect is measurable
against v1, which did not: problems raised 221 -> 148, agreed 40 -> 27, grouping problems 142 -> 91.
F1 (a general rule the entry's own examples contradict) is still the dominant class at 21 of 27, which
is the point of naming it.

The six MAJOR ones are all the same shape, and all would make a learner produce something wrong:

  水 スイ   "...fecha alguns: 香水 (こうすい) e 洪水 (こうずい), onde ela sonoriza e vira ずい" - the
            relative clause trails a coordinated pair so it reads as covering both, but 香水 is こうすい
            with no rendaku. Taken literally the rule produces *こうずい.
  西 サイ   identical shape: 関西 (かんさい) keeps さい, only 東西 sonorizes. Produces *かんざい.
  説 セツ   "abre 説明 e 説得 (aí vira せっ)" - 説明 is せつめい, not せっめい, and it is a very
            high-frequency word to get wrong.

Only problems BOTH checkers raised for the same (character, reading) are applied; a single dissenting
reviewer is noise. Each carries replacement text, so nothing is re-authored here.

Also fixes one mechanical defect the review found across batches: "hifen" written without its accent in
7 notes, where 16 of the other batches spell "hífen" correctly. It is learner-facing text, so the
accent matters.

Usage: apply_kanji_note_review.py [--apply]
"""
from __future__ import annotations
import argparse, glob, json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "research" / "derived" / "kanji_reading_notes"
REVIEW = NOTES / "_review_v3.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    raw = json.loads(REVIEW.read_text(encoding="utf-8"))
    agreed = (raw.get("result") or raw).get("agreed") or []
    print(f"{len(agreed)} reviewer-agreed corrections")

    files = {p: json.loads(p.read_text(encoding="utf-8"))
             for p in sorted(NOTES.glob("batch-*.json"))}
    index = {}
    for p, d in files.items():
        for e in d.get("entries", []):
            for r in e.get("readings", []):
                index[(e["character"], r["reading"])] = r

    applied, skipped = Counter(), []
    for a in agreed:
        key = (a.get("character"), a.get("reading"))
        sug = (a.get("suggested") or "").strip()
        if not sug:
            skipped.append((key, "no replacement text")); continue
        row = index.get(key)
        if not row:
            skipped.append((key, "no such (character, reading) in the notes")); continue
        # Reviewers sometimes label the field; strip the label and keep the value.
        for pre in ("note_pt:", "Note:", "nota:"):
            if sug.startswith(pre):
                sug = sug[len(pre):].strip().strip('"').strip()
        row["note_pt"] = sug
        applied.update([a.get("failure_mode") or "other"])

    # Mechanical: the accent on "hífen". Learner-facing, and the rest of the corpus spells it correctly.
    accents = 0
    for d in files.values():
        for e in d.get("entries", []):
            for r in e.get("readings", []):
                n = r.get("note_pt") or ""
                if "hifen" in n:
                    r["note_pt"] = n.replace("hifen", "hífen")
                    accents += 1

    if args.apply:
        for p, d in files.items():
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"note review ({'APPLIED' if args.apply else 'dry-run'}): "
          f"{sum(applied.values())} notes rewritten {dict(applied)}; {accents} accent fixes")
    for k, w in skipped:
        print(f"   skip {k}: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
