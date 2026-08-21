#!/usr/bin/env python3
"""Fold re-authored per-reading notes back into the canonical authoring batches.

The notes live in research/derived/kanji_reading_notes/batch-NN.json, and merge_kanji_reading_notes.py
reads them from there into the corpus. A repair pass writes its output somewhere else, so this puts the
new text back where the merge will find it rather than adding a second source the merge has to know
about. One place a note can live, one path into the corpus.

REFUSALS, so a bad repair batch cannot reach the corpus:
  * a note for a (character, slot) that does not exist in the authoring batches is dropped, not guessed;
  * a note is refused if it names a compound that is NOT in this slot's group WITHOUT saying where that
    compound actually belongs. Naming a departed word is legitimate and often the most useful thing a
    note can do: 気's kun き is far clearer for saying "em 病気, 天気 e 元気 quem aparece e a leitura
    sino-japonesa キ" than for pretending those words are unrelated. What is NOT legitimate is listing
    it as an example of THIS reading, which is failure mode F1. The two are told apart mechanically --
    a named-but-absent compound passes only when the note also names the reading it now sits under, or
    says it is irregular. Refusing every mention outright rejected 35 of 63 notes, including every one
    that correctly explained where a word had gone;
  * a note is refused if it is empty, contains an em dash, or contains no Latin letters at all (a pt-BR
    note written entirely in kana is not a pt-BR note).

Usage: apply_reauthored_reading_notes.py [--apply]
"""
from __future__ import annotations
import argparse, glob, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "export"))
from kanji_align import claims_empty, explains_placement, named_compounds  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "research" / "derived" / "kanji_reading_notes"
REPAIR = ROOT / "research" / "derived" / "kanji_note_reauthor"
GROUPS = ROOT / "research" / "derived" / "kanji_reading_groups.json"
JP = re.compile(r"[一-鿿][一-鿿぀-ヿ]*")
LATIN = re.compile(r"[A-Za-zÀ-ÿ]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    groups = {e["character"]: e for e in json.loads(GROUPS.read_text(encoding="utf-8"))["entries"]}
    members: dict[tuple[str, str], set[str]] = {}
    # Where each compound actually sits now, so a note that names one can be checked for saying so.
    home: dict[tuple[str, str], str] = {}
    all_words: dict[str, set[str]] = {}
    for ch, e in groups.items():
        all_words[ch] = {c["headword"] for r in e["readings"] for c in r["compounds"]} | \
                        {c["headword"] for c in e["irregular"]}
        for r in e["readings"]:
            members[(ch, f"{r['reading']}.{r['okurigana'] or ''}")] = {
                c["headword"] for c in r["compounds"]}
            for c in r["compounds"]:
                home[(ch, c["headword"])] = (
                    f"{r['reading']}.{r['okurigana'] or ''}".replace("-", "").replace(chr(0x2010), ""))
        for c in e["irregular"]:
            home[(ch, c["headword"])] = "(irregular)"

    repairs: dict[tuple[str, str], str] = {}
    # Every batch file in the repair directory, whatever a given pass named them, sorted so a later
    # pass overrides an earlier one for the same slot. The first pass wrote batch-NN, the second v2-NN;
    # globbing only "batch-*" silently ignored the second and reported nothing to do.
    for f in sorted(glob.glob(str(REPAIR / "*.json"))):
        for n in json.loads(Path(f).read_text(encoding="utf-8")).get("notes") or []:
            repairs[(n["character"], n["slot"])] = (n.get("note_pt") or "").strip()

    stats, refused, applied = Counter(), [], {}
    for (ch, slot), text in repairs.items():
        if (ch, slot) not in members:
            refused.append((ch, slot, "no such reading slot"))
            stats["no such slot"] += 1
            continue
        if not text:
            refused.append((ch, slot, "empty note"))
            stats["empty"] += 1
            continue
        if "—" in text or "–" in text:
            refused.append((ch, slot, "contains an em/en dash"))
            stats["dash"] += 1
            continue
        if not LATIN.search(text):
            refused.append((ch, slot, "no Latin letters -- not pt-BR prose"))
            stats["not prose"] += 1
            continue
        here = members[(ch, slot)]
        # A note must not deny the examples printed directly beneath it, nor claim examples an empty
        # group does not have. Both shipped: 亡's な.い said "Nenhum vocabulário desta lista ficou
        # agrupado nela" above 亡くなる and 亡くす, and its sibling な.き- presented those same two words
        # as ITS examples while holding nothing.
        # A group whose only member is the single-character word is not "a compound", so a note
        # saying "não aparece dentro de nenhum composto" is telling the truth about it. 頭 holds
        # only 頭 and 共 only 共.
        if here and set(here) != {ch} and claims_empty(text):
            refused.append((ch, slot, f"says the group is empty, but it holds {sorted(here)}"))
            stats["denies its own examples"] += 1
            continue
        if not here and not claims_empty(text):
            # The converse, and it needs stating outright rather than inferring from which words the
            # note mentions. 重's bare おも holds nothing, and its note opened "O exemplo desta lista é
            # 重たい" -- 重たい is in おも.い, and the note even says so about 重い in the next clause, so
            # every word-placement test passed while the first sentence was still false.
            refused.append((ch, slot, "the group is empty and the note does not say so"))
            stats["empty group not declared"] += 1
            continue
        citation = ch + slot.split(".", 1)[1] if "." in slot else ch
        named = named_compounds(text, all_words[ch], ch, citation)
        absent = sorted(w for w in named if w not in here)
        unexplained = []
        for w in absent:
            dest = home.get((ch, w), "")
            if not explains_placement(text, dest, slot):
                unexplained.append(f"{w} (belongs to {dest or '?'})")
        if unexplained:
            refused.append((ch, slot, "names " + ", ".join(unexplained) +
                            " without saying where they belong"))
            stats["names an absent compound without placing it (F1)"] += 1
            continue
        if absent:
            stats["accepted, with an explained contrast"] += 1
        applied[(ch, slot)] = text
        stats["accepted"] += 1

    touched = Counter()
    for f in sorted(glob.glob(str(NOTES / "batch-*.json"))):
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        changed = False
        for e in data.get("entries") or []:
            ch = e.get("character")
            for r in e.get("readings") or []:
                key = (ch, f"{r.get('reading')}.{r.get('okurigana') or ''}")
                if key in applied and r.get("note_pt") != applied[key]:
                    if args.apply:
                        r["note_pt"] = applied[key]
                        # The grouping complaint that prompted the rewrite is resolved by the rewrite.
                        r["grouping_problem"] = ""
                    changed = True
                    touched[Path(f).name] += 1
        if changed and args.apply:
            Path(f).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"re-authored notes offered: {len(repairs)}")
    for k, v in stats.most_common():
        print(f"  {k}: {v}")
    for ch, slot, why in refused:
        print(f"  [REFUSED] {ch} {slot}: {why}")
    print(f"notes that would change: {sum(touched.values())} across {len(touched)} batches")
    if not args.apply:
        print("\npre-flight only. re-run with --apply to write.")
        return 0
    print("NEXT: merge_kanji_reading_notes.py --apply, then export_corpus.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
