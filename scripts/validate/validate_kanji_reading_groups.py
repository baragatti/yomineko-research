#!/usr/bin/env python3
"""Gate the per-reading kanji grouping: every compound must be under a reading it plausibly uses.

The grouping decides what a learner is shown as an example OF a reading, so a word in the wrong group
is not a cosmetic filing error -- it is the page telling them 生 sounds う in 誕生日, where it sounds
じょう. That exact claim shipped, which is why this runs on every build.

The checks are DELIBERATELY INDEPENDENT of the aligner that produced the grouping. Re-running the
aligner and comparing would only prove the file was written by the aligner, which nobody doubts; it
would pass just as happily if the aligner were wrong. So these test properties the grouping must have
whatever produced it:

  1. COVERAGE. No example word is filed under two readings at once -- that shows it to the learner as
     an example of both. A word in NO group is the irregular case (熟字訓, ateji, or a reading the
     registry does not hold) and is expected; 今日 belongs to no single reading of 日.
  2. THE READING IS IN THE KANA. For a word filed under a reading, that reading -- allowing rendaku,
     handakuten, gemination and okurigana absorption -- must occur in the word's kana. This is weaker
     than alignment on purpose: it is a different, simpler question, and a grouping that fails it is
     wrong under any theory.
  3. POSITION. A kanji that OPENS the word must own the start of the kana, and one that CLOSES it must
     own the end (unless the headword writes okurigana after it, which pushes the end back). This is
     what catches 一人 filed under 人's ひと, where ひと is in the kana but belongs to 一.
  4. NANORI HOLD NOTHING. Name readings never group ordinary vocabulary. 日's あ nanori swallowing
     明日 (あした) is how that rule was learned.
  5. NOTES DO NOT PRESENT ABSENT WORDS AS EXAMPLES. A note is Layer C prose a learner reads. Naming a
     compound filed under a DIFFERENT reading is fine and often the clearest thing the note can do
     ("em 病気, 天気 e 元気 quem aparece e a leitura sino-japonesa キ"), so what fails is naming one
     WITHOUT saying where it belongs. That is failure mode F1 -- a general claim the entry's own
     examples contradict -- and it is the defect this corpus produces most.
  6. NOTES DO NOT NAME WORDS THE RECORD NEVER SHOWS. Rule 5 asks WHICH READING a named word sits
     under, so it can only see words that are on the record at all: it matches the note against the
     kanji's own example words, and a word that is nowhere in that list is invisible to it. The
     example-word selector was later re-ranked, which dropped words off records without touching the
     prose, and nine notes were left pointing at 年寄り, 勇気, 書物, 物語, 論議, 一定, 取り扱う, 正常
     /正解/訂正 and 仲直り -- words a learner cannot find anywhere on the page they are reading. Rule 5
     passed all nine. So this one reads the note the other way round: pull every Japanese word OUT of
     the text and require the record to display it.

     There is no "but the note says it is irregular" escape hatch, and that is deliberate. The two
     cases where naming an absent word is legitimate both resolve to a word that IS displayed: the
     irregular bucket is printed on the record (物's 果物 sits there, and the note may say so), and a
     note declaring its own group empty names nothing it does not have. Exempting a whole note on the
     EMPTY_CLAIMS / 熟字訓 phrasing would have re-opened the hole for two of the nine defects above --
     年's とし note ends "a leitura pertence à palavra inteira" and 物's もの note says 果物 "fica entre
     os irregulares", so both would have been waved through while still citing a phantom.

Usage: validate_kanji_reading_groups.py [--list]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "export"))
from kanji_align import (hira, bare, variants, masu_stem, explains_placement,  # noqa: E402
                         named_compounds, claims_empty)
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LEVELS = ("n5", "n4", "n3")
# A Japanese word as it is written inside pt-BR prose: opens on a kanji, then runs through kanji, kana,
# 々 (踊り字: 色々, 時々) and ー. Both 々 and ー sit outside the CJK and kana blocks, so without them the
# run stops early and 色々 comes out as the bare 色.
JP = re.compile(r"[一-鿿][一-鿿぀-ヿ々ー]*")
# 「」 is the corpus's own quoting for a cited word; a quoted span is scanned the same way, so a note
# that writes 「年寄り」 is read as naming it exactly like a bare 年寄り.
QUOTED = re.compile(r"「([^」]+)」")


def cited_words(note: str, character: str, citation: str, shown: set[str]) -> set[str]:
    """Every word a note WRITES OUT that is a claim about this kanji, for rule 6.

    The mirror image of kanji_align.named_compounds: that one starts from the words the record holds
    and asks which the note mentions, which is blind to a word the record does not hold. This starts
    from the text.

    Three things are not claims and are dropped:
      * a single character, which is the kanji being talked about rather than a word built on it, and
        anything that does not contain this kanji at all (a note may mention a neighbouring word while
        explaining a contrast);
      * the reading's own CITATION FORM (kanji + okurigana) -- 回's -まわ.る note writes 回る as the
        NAME of the reading, not as a member of the group. Same exemption rule 5 makes;
      * a fragment cut out of a longer word the note also writes. The regex anchors on a kanji, so
        お菓子 yields 菓子, もう一度 yields 一度 and お待たせしました yields 待たせしました -- 21 of them
        across the corpus, every one a prefix the anchor could not reach back over. A candidate that
        only ever occurs inside a longer word the record DOES display is that word, not a new claim.
    """
    cands = set(JP.findall(note))
    for q in QUOTED.findall(note):
        cands |= set(JP.findall(q))
    cands = {c for c in cands if len(c) >= 2 and character in c and c != citation}
    return {c for c in cands if not any(w != c and c in w and w in note for w in shown)}


def forms(reading: str, okurigana: str) -> list[str]:
    """Every span the reading could legitimately take in a compound."""
    b = bare(reading)
    if not b:
        return []
    oku = hira(okurigana or "").replace("-", "").replace("‐", "")
    out = list(variants(b))
    for extra in (oku, masu_stem(oku)):
        if extra:
            out += variants(b + extra)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    stats = Counter()
    for lv in LEVELS:
        for k in json.loads((ROOT / "corpus" / "kanji" / f"{lv}.json").read_text(encoding="utf-8")):
            ch = k["character"]
            words = k.get("example_words") or []
            # Identity is the VOCAB ID, never the headword. 日 is two different entries -- ひ (sun/day)
            # and にち (the day counter) -- sharing one spelling, and keying by headword collapses them,
            # so the same word appears to be filed under two readings at once and its kana appears not
            # to contain either. That produced 122 failures against a grouping with nothing wrong in it.
            expected = {w["vocab_id"] for w in words if w.get("vocab_id")}
            kana_of = {w["vocab_id"]: hira(w.get("kana") or "") for w in words if w.get("vocab_id")}
            hw_of = {w["vocab_id"]: w.get("headword") for w in words if w.get("vocab_id")}
            seen: Counter = Counter()
            grouped: set[int] = set()
            # headword -> the reading slot it is actually filed under, for the note check below.
            home: dict[tuple[str, str], str] = {}
            for rr in k.get("readings") or []:
                for vid in (rr.get("example_vocab_ids") or []):
                    if vid in hw_of:
                        home[(ch, hw_of[vid])] = (
                            f"{rr.get('reading')}.{rr.get('okurigana') or ''}"
                            .replace("-", "").replace(chr(0x2010), ""))
            for vid in expected:
                home.setdefault((ch, hw_of[vid]), "(irregular)")

            for r in k.get("readings") or []:
                rd, oku = r.get("reading"), r.get("okurigana")
                slot = f"{rd}.{oku or ''}"
                members = []
                for vid in (r.get("example_vocab_ids") or []):
                    if vid not in hw_of:
                        fails.append(f"{ch} {slot}: cites vocab id {vid}, which is not an example word "
                                     f"of this kanji")
                        continue
                    members.append(vid)
                seen.update(members)
                grouped.update(members)
                is_nanori = (r.get("type") or "").lower() == "nanori"
                if is_nanori and members:
                    fails.append(f"{ch} {slot}: nanori reading holds {members}")

                cand = forms(rd, oku)
                for vid in members:
                    hw, kana = hw_of[vid], kana_of.get(vid, "")
                    if not kana or not hw:
                        continue
                    hit = [v for v in cand if v and v in kana]
                    if not hit:
                        fails.append(f"{ch} {slot}: {hw} ({kana}) does not contain the reading")
                        continue
                    idx = hw.find(ch)
                    if idx == 0 and not any(kana.startswith(v) for v in hit):
                        fails.append(f"{ch} {slot}: {hw} ({kana}) opens with {ch} but not with the reading")
                    # A kanji that closes the word owns the end -- unless the headword writes okurigana
                    # after it, in which case the end belongs to that okurigana.
                    if idx == len(hw) - 1 and idx > 0 and not any(kana.endswith(v) for v in hit):
                        fails.append(f"{ch} {slot}: {hw} ({kana}) ends with {ch} but not with the reading")
                    stats["compounds checked"] += 1

                note = ((r.get("note") or {}).get("pt-BR") or "")
                if note:
                    stats["notes checked"] += 1
                    # Only words that are example_words of THIS kanji are claims about this group; a
                    # note may legitimately mention an unrelated word while explaining the reading.
                    here = {hw_of[v] for v in members}
                    all_hw = {hw_of[v] for v in expected if hw_of[v]}
                    citation = ch + (hira(oku or "").replace("-", "").replace(chr(0x2010), ""))
                    named = named_compounds(note, all_hw, ch, citation)
                    absent = sorted(w for w in named if w not in here)
                    # Naming a compound that is NOT in this group is fine when the note says where it
                    # DOES belong; that is a contrast, and often the clearest thing the note can say.
                    # Only an unplaced mention is the F1 defect. See kanji_align.explains_placement.
                    slot_key = slot.replace("-", "").replace(chr(0x2010), "")
                    unplaced = [w for w in absent
                                if not explains_placement(note, home.get((ch, w), ""), slot_key)]
                    # A group holding only the single-character word is not "a compound", so a note
                    # saying it appears in none is accurate. 頭 holds only 頭, 共 only 共.
                    if members and {hw_of[v] for v in members} != {ch} and claims_empty(note):
                        fails.append(f"{ch} {slot}: note says the group is empty, but it holds "
                                     f"{sorted(hw_of[v] for v in members)}")
                    if unplaced:
                        fails.append(f"{ch} {slot}: note names {unplaced} as examples of this reading "
                                     f"without saying where they belong")
                    # Rule 6: the same prose, read from the text side, so a word the record dropped
                    # entirely cannot hide from the membership question by not being a member.
                    # `all_hw` is every word the record prints for this kanji -- all the reading
                    # groups plus the irregular bucket -- which is exactly what a learner can find.
                    phantom = sorted(w for w in cited_words(note, ch, citation, all_hw)
                                     if w not in all_hw)
                    if phantom:
                        fails.append(f"{ch} {slot}: note names {phantom}, which this record does not "
                                     f"show under any reading nor among its irregular words")

            dupes = sorted(hw_of[v] for v, n in seen.items() if n > 1)
            if dupes:
                fails.append(f"{ch}: filed under more than one reading: {dupes}")
            # Words in no group are the IRREGULAR set (熟字訓 / ateji / a reading we do not hold). They
            # are expected and counted, not failed: 今日 belongs to no single reading of 日.
            stats["irregular"] += len(expected - grouped)
            stats["kanji"] += 1

    print(f"validate_kanji_reading_groups: {stats['kanji']} kanji, "
          f"{stats['compounds checked']} compounds, {stats['notes checked']} notes, "
          f"{len(fails)} FAIL")
    for f in fails[: (len(fails) if args.list else 25)]:
        print(f"  [FAIL] {f}")
    if not args.list and len(fails) > 25:
        print(f"  ... and {len(fails) - 25} more (--list for all)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
