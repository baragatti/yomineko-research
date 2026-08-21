#!/usr/bin/env python3
"""Report every `grouping_problem` the note-authoring pass flagged, against the CURRENT alignment.

Roadmap D step 2 asked each authoring agent to write a note per reading AND to flag it when the
mechanical grouping underneath looked wrong. 46 readings came back flagged. Several rounds of alignment
fixes have landed since — positional alignment, 促音便, handakuten, exact-match preference, the
okurigana shared-prefix score, the consonant-row tiebreak, and the prefix/bound hyphen rules — so an
unknown number are already resolved.

This does NOT try to decide which. Two attempts at classifying them automatically both failed, in
instructive ways worth recording so a third is not attempted the same way:

  * "the flagged word is still in the flagged group" reads the wrong direction for the minority of notes
    that complain a slot is wrongly EMPTY. Those resolve when the word ARRIVES, so the check reported
    合's -あい and 共's -ども as broken at the exact moment they were fixed.
  * keying off the word the note names fails whenever the note names only the kanji itself
    (共's note is about the single-character word 共), which the word extractor must exclude to avoid
    matching every entry.

So this emits the flag together with what the group actually holds now, and leaves the judgement to a
reader. That is the honest output: the classification is the hard part, and a wrong count of "known
remaining problems" is worse than no count.

Output: research/derived/kanji_grouping_review.json
Usage: report_kanji_grouping_problems.py
"""
from __future__ import annotations
import glob, json, os, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
GROUPS = ROOT / "research" / "derived" / "kanji_reading_groups.json"
NOTES = ROOT / "research" / "derived" / "kanji_reading_notes"
OUT = ROOT / "research" / "derived" / "kanji_grouping_review.json"
JP = re.compile(r"[一-鿿][一-鿿぀-ゟ゠-ヿ]*")


def main() -> int:
    groups = {e["character"]: e for e in
              json.loads(GROUPS.read_text(encoding="utf-8"))["entries"]}
    rows = []
    for f in sorted(glob.glob(str(NOTES / "batch-*.json"))):
        for e in (json.loads(Path(f).read_text(encoding="utf-8")).get("entries") or []):
            ch = e.get("character")
            for r in e.get("readings") or []:
                gp = (r.get("grouping_problem") or "").strip()
                if not gp:
                    continue
                key = f"{r.get('reading')}.{r.get('okurigana') or ''}"
                ent, cur, irregular = groups.get(ch), [], []
                if ent:
                    for rr in ent["readings"]:
                        if f"{rr['reading']}.{rr['okurigana'] or ''}" == key:
                            cur = [c["headword"] for c in rr["compounds"]]
                    irregular = [c["headword"] for c in ent["irregular"]]
                named = sorted({w for w in JP.findall(gp) if len(w) > 1 and w != ch})
                rows.append({
                    "character": ch, "reading": key, "batch": os.path.basename(f),
                    "problem": gp,
                    "words_the_note_names": named,
                    "group_holds_now": cur,
                    "still_present": [w for w in named if w in cur],
                    "kanji_irregular_list_now": irregular,
                })

    OUT.write_text(json.dumps(
        {"note": __doc__.strip(), "count": len(rows), "rows": rows},
        ensure_ascii=False, indent=1), encoding="utf-8")
    still = sum(1 for r in rows if r["still_present"])
    print(f"kanji grouping problems flagged by the authoring pass: {len(rows)}")
    print(f"  a word the note names is still in the flagged group: {still}")
    print(f"  (indicative only -- see the module docstring for why this is not a resolved/unresolved split)")
    print(f"-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
