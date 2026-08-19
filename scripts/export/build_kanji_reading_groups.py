#!/usr/bin/env python3
"""Group each kanji's example words under the READING they actually use. Roadmap item D, step 1.

Have: readings (on/kun/nanori, faithful to KANJIDIC2) and example_words with kana. Gap: nothing connects
them, so a learner looking at 日 sees a flat list of readings and a flat list of words and has to work
out for themselves that 今日 uses none of the listed readings while 日曜日 uses two.

This is the mechanical half. It aligns by READING SUBSTRING, which is a heuristic and is treated as one:
  * a kun reading is stripped of its okurigana marker (書-く -> か) and of the leading hyphen KANJIDIC2
    uses for bound forms (-び -> び);
  * on readings are matched in hiragana, since example_words carry hiragana kana;
  * rendaku is handled by also testing the voiced form of a reading's first mora (ひ -> び, か -> が),
    which is why -び and -か already appear as separate KANJIDIC2 entries for 日 and why matching only
    the literal form would mis-group 三日 and 日曜日;
  * the LONGEST matching reading wins, so にち beats に.

A word that matches no reading is NOT forced into a group. 今日 (きょう) is the standard example: it is
a 熟字訓, a whole-word reading that belongs to no single character, and pretending it uses a listed
reading of 日 would teach a falsehood. Those are emitted under `irregular` so the app can show them as
what they are.

Output: research/derived/kanji_reading_groups.json — the grouping plus, for each reading, the slots a
later authoring pass fills (a pt-BR note on what the reading means and when it is used). Nothing is
written into corpus/ here; this file is the input to that pass.

Usage: build_kanji_reading_groups.py
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "derived" / "kanji_reading_groups.json"
LEVELS = ("n5", "n4", "n3")
VOICED = {"か": "が", "き": "ぎ", "く": "ぐ", "け": "げ", "こ": "ご", "さ": "ざ", "し": "じ",
          "す": "ず", "せ": "ぜ", "そ": "ぞ", "た": "だ", "ち": "ぢ", "つ": "づ", "て": "で",
          "と": "ど", "は": "ば", "ひ": "び", "ふ": "ぶ", "へ": "べ", "ほ": "ぼ"}
KATA = {chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)}


def hira(s: str) -> str:
    return "".join(KATA.get(c, c) for c in s or "")


def bare(reading: str) -> str:
    """KANJIDIC2 decorations: '-び' bound form, '書.く' okurigana split."""
    r = (reading or "").replace("-", "").replace("‐", "")
    if "." in r:
        r = r.split(".", 1)[0]
    return hira(r)


def variants(r: str) -> list[str]:
    out = [r]
    if r and r[0] in VOICED:
        out.append(VOICED[r[0]] + r[1:])          # rendaku on the first mora
    return [x for x in out if x]


def main() -> int:
    entries = []
    for lv in LEVELS:
        entries += json.loads((ROOT / "corpus" / "kanji" / f"{lv}.json").read_text(encoding="utf-8"))

    out, stats = [], Counter()
    for k in entries:
        reads = k.get("readings") or []
        words = k.get("example_words") or []
        groups: dict[str, list] = {}
        irregular = []
        for w in words:
            kana = hira(w.get("kana") or "")
            best, best_len = None, 0
            for r in reads:
                # NANORI are name-readings. Letting them group ordinary words is actively wrong: the
                # あ nanori of 日 swallowed 明日 (あした), which is a 熟字訓 like 今日 and belongs in
                # `irregular`. Only on/kun readings group words.
                if (r.get("type") or "").lower() == "nanori":
                    continue
                b = bare(r.get("reading"))
                if not b:
                    continue
                if not any(v in kana for v in variants(b)):
                    continue
                # A kun reading with OKURIGANA (生.きる, 生.かす, 生.ける) must match the word's own
                # okurigana, or all three collapse to い and every one of them claims 生きる, printing
                # the same compound list three times under three different readings.
                oku = hira(r.get("okurigana") or "")
                if oku and not (w.get("headword") or "").endswith(oku):
                    continue
                score = len(b) + (len(oku) * 2)      # an okurigana match is stronger evidence
                if score > best_len:
                    best, best_len = f"{r.get('reading')}|{r.get('okurigana') or ''}", score
            if best:
                groups.setdefault(best, []).append(
                    {"headword": w.get("headword"), "kana": w.get("kana"),
                     "vocab_id": w.get("vocab_id"),
                     "gloss_pt": (w.get("gloss") or {}).get("pt-BR")})
                stats["grouped"] += 1
            else:
                irregular.append({"headword": w.get("headword"), "kana": w.get("kana"),
                                  "vocab_id": w.get("vocab_id"),
                                  "gloss_pt": (w.get("gloss") or {}).get("pt-BR")})
                stats["irregular"] += 1

        rows = []
        for r in reads:
            rd = f"{r.get('reading')}|{r.get('okurigana') or ''}"
            rows.append({"reading": r.get("reading"), "okurigana": r.get("okurigana"),
                         "type": r.get("type"), "common": r.get("common"),
                         "compounds": groups.get(rd, []),
                         "note_pt": None})            # <- filled by the authoring pass
            stats["readings"] += 1
            if groups.get(rd):
                stats["readings_with_examples"] += 1
        out.append({"character": k["character"], "slug": k["slug"], "level": k["level"],
                    "meanings_pt": (k.get("meanings") or {}).get("pt-BR"),
                    "readings": rows, "irregular": irregular})

    OUT.write_text(json.dumps(
        {"note": "Roadmap D step 1. Example words grouped under the reading they use, by reading-"
                 "substring alignment with rendaku handling. Words matching no reading are listed as "
                 "`irregular` rather than forced into a group: 今日 (きょう) is a 熟字訓, a whole-word "
                 "reading belonging to no single character. `note_pt` is the slot for the authoring "
                 "pass and is null here.",
         "kanji": len(out), **{k: v for k, v in stats.items()}, "entries": out},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"kanji reading groups: {len(out)} kanji, {stats['readings']} readings "
          f"({stats['readings_with_examples']} with at least one example word)")
    print(f"  example words grouped: {stats['grouped']}   irregular (熟字訓 etc.): {stats['irregular']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
