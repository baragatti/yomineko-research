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
# handakuten: は-row also geminates to the p-row after っ and ん (ハイ -> ぱい in 一杯, 乾杯).
# Without this the whole は-row on-reading family loses its most common compounds to `irregular`.
PLOSIVE = {"は": "ぱ", "ひ": "ぴ", "ふ": "ぷ", "へ": "ぺ", "ほ": "ぽ"}
KATA = {chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)}


def hira(s: str) -> str:
    return "".join(KATA.get(c, c) for c in s or "")


def bare(reading: str) -> str:
    """KANJIDIC2 decorations: '-び' bound form, '書.く' okurigana split."""
    r = (reading or "").replace("-", "").replace("‐", "")
    if "." in r:
        r = r.split(".", 1)[0]
    return hira(r)


def oku_ok(headword: str, r: dict) -> bool:
    """A reading with okurigana ends the word at the okurigana, not at the reading itself."""
    o = hira(r.get("okurigana") or "")
    return bool(o) and headword.endswith(o)


# Kana rows. A Japanese verb inflects WITHIN its consonant row -- 済ます / 済ませ, 書く / 書か / 書け --
# so when two readings tie, the one whose okurigana diverges into the same row as the word is the one
# that shares its stem. Used ONLY to break ties (see `row_match`), never to filter.
ROWS = ("あいうえお", "かきくけこがぎぐげご", "さしすせそざじずぜぞ", "たちつてとだぢづでど",
        "なにぬねの", "はひふへほばびぶべぼぱぴぷぺぽ", "まみむめも", "やゆよ", "らりるれろ", "わをん")
ROW_OF = {c: i for i, r in enumerate(ROWS) for c in r}


def row_match(word_tail: str, oku: str) -> int:
    """1 when the okurigana diverges from the word into the SAME kana row, else 0.

    This is the tiebreak the 済 family needed. 済ませる scored identically against す.まない and す.ます
    -- both share exactly the one mora ま with the word's tail ませる -- so the winner was whichever
    KANJIDIC2 happened to list first, which was す.まない. That put 済ませる (the transitive partner of
    済ます) under the negative of 済む.

    At the first divergence the word reads せ. ます continues す, same さ-row, because 済ます and 済ませる
    are the same stem. まない continues な, the な-row, because it is a different word's negation.

    Deliberately a tiebreak and not a scoring term: 少.ない legitimately claims 少なくとも, where the
    divergence is く against い and the rows do NOT match. As a filter that grouping would be lost; as a
    tiebreak nothing happens there at all, because 少 has no competing reading to tie with.
    """
    if not oku or not word_tail:
        return 0
    i = 0
    while i < len(oku) and i < len(word_tail) and oku[i] == word_tail[i]:
        i += 1
    if i == 0 or i >= len(oku) or i >= len(word_tail):
        return 0
    a, b = ROW_OF.get(word_tail[i]), ROW_OF.get(oku[i])
    return 1 if a is not None and a == b else 0


def variants(r: str) -> list[str]:
    """The sound changes a reading undergoes inside a compound."""
    out = [r]
    if r and r[0] in VOICED:
        out.append(VOICED[r[0]] + r[1:])          # rendaku: ひ -> び in 誕生日
    if r and r[0] in PLOSIVE:
        out.append(PLOSIVE[r[0]] + r[1:])         # handakuten: ハイ -> ぱい in 一杯
    if r.endswith(("つ", "ち", "く", "き")):
        # 促音便: an on-reading ending in つ/ち/く/き geminates before a voiceless consonant.
        # Without this, シュツ loses 出発 / 出席 / 出身 (all しゅっ-) to `irregular`.
        out.append(r[:-1] + "っ")
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
            best, best_len = None, (0, 0)
            # Two passes. STRICT requires the word to end with the reading's own okurigana, which is what
            # separates 生.きる from 生.かす. But it is too strong on its own: a nominalised or compound
            # verb ends with something else entirely (遊び does not end in ぶ, 逃げ出す does not end in
            # げる, 備え付ける does not end in え), and those fell into `irregular` — 135 of them, all
            # flagged by the authoring pass. So fall back to reading-only matching when nothing strict
            # matches, rather than discarding the word.
            for strict in (True, False):
              if best:
                break
              for r in reads:
                # NANORI are name-readings. Letting them group ordinary words is actively wrong: the
                # あ nanori of 日 swallowed 明日 (あした), which is a 熟字訓 like 今日 and belongs in
                # `irregular`. Only on/kun readings group words.
                if (r.get("type") or "").lower() == "nanori":
                    continue
                b = bare(r.get("reading"))
                if not b:
                    continue
                # POSITIONAL alignment. Matching the reading anywhere in the kana was wrong and the
                # authoring pass caught it 142 times: 一人 (ひとり) landed under 人's ひと although that
                # ひと is 一's reading and 人 sounds り; 三味線 (しゃみせん) landed under 三's み although
                # 三 sounds しゃ there and the み belongs to 味. A kanji that opens the word must own the
                # START of the kana, and one that closes it must own the END.
                hw = w.get("headword") or ""
                idx = hw.find(k["character"])
                at_start, at_end = idx == 0, idx == len(hw) - 1
                if not any(v in kana for v in variants(b)):
                    continue
                if at_start and not any(kana.startswith(v) for v in variants(b)):
                    continue
                if at_end and not oku_ok(hw, r) and not any(kana.endswith(v) for v in variants(b)):
                    continue
                # A leading hyphen marks a BOUND form, used only when the kanji is not word-initial
                # (出's -で should not claim 出会う).
                # A TRAILING hyphen is the mirror: a PREFIX form, used only when the kanji opens the
                # word. 59 readings carry one and nothing enforced it, so 合's あい- (prefix) claimed
                # 場合 and 試合 -- both of which have 合 at the END -- while the -あい listed for exactly
                # that position sat empty.
                #
                # Both tests exclude the ONE-CHARACTER word, where the kanji is simultaneously initial
                # and final and neither restriction can be meant: 御 alone reads ご and 幾 alone reads
                # いく, and a naive at_end test threw both out of their own prefix reading.
                rd = (r.get("reading") or "").strip()
                whole_word = at_start and at_end
                if rd.startswith(("-", "‐")) and at_start and not whole_word:
                    continue
                if rd.endswith(("-", "‐")) and at_end and not whole_word:
                    continue
                # A kun reading with OKURIGANA (生.きる, 生.かす, 生.ける) must match the word's own
                # okurigana, or all three collapse to い and every one of them claims 生きる, printing
                # the same compound list three times under three different readings.
                oku = hira(r.get("okurigana") or "")
                oku_exact = bool(oku) and (w.get("headword") or "").endswith(oku)
                if oku and not oku_exact and strict:
                    continue
                # An UNCHANGED reading beats one that only matched through rendaku or handakuten. Both
                # ソン and ゾン are listed for 存, and without this the ぞん compounds (保存, 依存, 生存)
                # matched ソN through rendaku and won on length, landing in the wrong group.
                exact = any(kana.startswith(b) or kana.endswith(b) or b in kana for b in [b]) and (
                    b in kana)
                unchanged = b in kana
                # In the LOOSE pass nothing has exact okurigana, so slots tie and the winner is
                # arbitrary: 暮らし went to く+る instead of く+らす, 寝かせる to ね+る instead of ね+かす.
                # Score the shared prefix between the word's tail and the reading's okurigana.
                tail = hw[idx + 1:] if idx >= 0 else ""
                shared = 0
                for a, c2 in zip(hira(tail), oku):
                    if a != c2:
                        break
                    shared += 1
                score = (len(b) + (len(oku) * 2 if oku_exact else 0)
                         + shared * 3 + (2 if unchanged else 0))
                # Compared as a TUPLE, so the row match decides only among equal scores and cannot
                # outrank any of the real signals above it.
                rank = (score, row_match(hira(tail), oku))
                if rank > best_len:
                    best, best_len = f"{r.get('reading')}|{r.get('okurigana') or ''}", rank
            if best:
                # example_words can list the same compound twice (日曜日 under ニチ); dedupe by headword.
                bucket = groups.setdefault(best, [])
                if any(c["headword"] == w.get("headword") for c in bucket):
                    continue
                bucket.append(
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
