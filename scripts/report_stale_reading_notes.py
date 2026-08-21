#!/usr/bin/env python3
"""Find per-reading notes whose text names a compound that is no longer in that reading's group.

The 3,679 pt-BR notes were authored against the grouping produced by the old substring matcher. The
grouping has since been rewritten to align the whole word, which moved ~110 compounds, and a note that
says "esta leitura aparece em 誕生日" is now describing a group 誕生日 has left. The grouping being right
does not make the note right; the note is what the learner reads.

Two ways a note goes stale, and they are mirror images:

  LOST   a multi-character word the note NAMES was in this reading's group before and is not now.
         Naming a word that was never there is not evidence of anything (a note may legitimately
         contrast with a word in a sibling group), which is why this compares against the previous
         grouping rather than just checking membership.
  GAINED the group was EMPTY before and holds compounds now, so a note that truthfully said "nesta
         entrada ela ficou sem exemplos" is now printed directly above the examples it denies. 気's キ
         said exactly that above its seven compounds.
  EMPTIED the mirror of GAINED: the group HAD compounds and now has none, so a note built around
         listing them describes members that are no longer there. Flagged on membership alone rather
         than on the text, because the LOST test cannot catch it: that test asks whether the note says
         where a departed word went, and 気's kun note names キ while discussing 病気, which lets 気持ち
         and 気づく ride along on the same mention even though they left too.

The second was missed on the first pass, which looked only for departures -- the same blind spot that
made three earlier attempts at classifying grouping problems read the empty-slot notes backwards. A
keyword scan for "sem exemplos" is not a substitute: 空's kun note says the reading means "vazio" and
腹's says 空腹 is an empty stomach, and both would be flagged for talking about meaning.

Output: research/derived/kanji_stale_notes.json — the input to a re-authoring pass.
Usage: report_stale_reading_notes.py
"""
from __future__ import annotations
import glob, json, os, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "export"))
from kanji_align import claims_empty, explains_placement, named_compounds  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
NOW = ROOT / "research" / "derived" / "kanji_reading_groups.json"
BEFORE = ROOT / "research" / "derived" / "kanji_reading_groups.pre_alignment.json"
NOTES = ROOT / "research" / "derived" / "kanji_reading_notes"
OUT = ROOT / "research" / "derived" / "kanji_stale_notes.json"
JP = re.compile(r"[一-鿿][一-鿿぀-ヿ]*")


def members(entry: dict) -> dict[str, list[str]]:
    return {f"{r['reading']}.{r['okurigana'] or ''}": [c["headword"] for c in r["compounds"]]
            for r in entry["readings"]}


def main() -> int:
    now = {e["character"]: e for e in json.loads(NOW.read_text(encoding="utf-8"))["entries"]}
    before = {e["character"]: e for e in json.loads(BEFORE.read_text(encoding="utf-8"))["entries"]} \
        if BEFORE.exists() else {}
    rows = []
    for f in sorted(glob.glob(str(NOTES / "batch-*.json"))):
        for e in (json.loads(Path(f).read_text(encoding="utf-8")).get("entries") or []):
            ch = e.get("character")
            if ch not in now:
                continue
            mn = members(now[ch])
            mo = members(before.get(ch, {"readings": []}))
            for r in e.get("readings") or []:
                key = f"{r.get('reading')}.{r.get('okurigana') or ''}"
                note = r.get("note_pt") or ""
                if not note:
                    continue
                cur, was = set(mn.get(key, [])), set(mo.get(key, []))
                if cur == was:
                    continue
                # A note may NAME a departed word legitimately, as a contrast, provided it says where
                # the word now belongs. Only an unplaced mention is stale. Without this the 63 notes
                # already repaired came back flagged, because a good contrast note names the word on
                # purpose.
                oku = (r.get("okurigana") or "").replace("-", "").replace(chr(0x2010), "")
                named = named_compounds(note, was | cur, ch, ch + oku)
                gone = sorted(w for w in named & (was - cur)
                              if not explains_placement(
                                  note, next((k.split(".")[0].replace("-", "")
                                              for k, v in mn.items() if w in v), "(irregular)")))
                # A membership change is not itself staleness -- what matters is whether the note is
                # still WRONG about it. A gained slot is stale only while its note denies having
                # examples; an emptied slot only while its note fails to say the group is empty.
                # Without this the report kept listing notes that had just been repaired, which is a
                # work queue that never empties.
                newly_filled = bool(cur) and not was and claims_empty(note)
                emptied = bool(was) and not cur and not claims_empty(note)
                if not gone and not newly_filled and not emptied:
                    continue
                rows.append({
                    "character": ch, "reading": r.get("reading"),
                    "okurigana": r.get("okurigana"), "slot": key,
                    "batch": os.path.basename(f),
                    "reason": "gained" if newly_filled else ("emptied" if emptied else "lost"),
                    "note_pt": note,
                    "words_no_longer_in_this_group": gone,
                    "group_now": sorted(cur),
                    "group_before": sorted(was),
                    "where_they_went": {w: next((k for k, v in mn.items() if w in v),
                                                "(irregular)") for w in gone},
                })
    OUT.write_text(json.dumps(
        {"note": __doc__.strip(), "count": len(rows), "rows": rows},
        ensure_ascii=False, indent=1), encoding="utf-8")
    by = Counter(r["reason"] for r in rows)
    print(f"stale reading notes: {len(rows)}  " +
          "  ".join(f"{k}={v}" for k, v in sorted(by.items())))
    print(f"-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
