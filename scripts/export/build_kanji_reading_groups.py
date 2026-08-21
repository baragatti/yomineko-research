#!/usr/bin/env python3
"""Group each kanji's example words under the READING they actually use. Roadmap item D, step 1.

Have: readings (on/kun/nanori, faithful to KANJIDIC2) and example_words with kana. Gap: nothing connects
them, so a learner looking at 日 sees a flat list of readings and a flat list of words and has to work
out for themselves that 今日 uses none of the listed readings while 日曜日 uses two.

This is the mechanical half, and it works by ALIGNING THE WHOLE WORD (scripts/export/kanji_align.py)
rather than by looking for a reading inside the kana. The difference is the whole point.

Substring matching asks "does this reading appear in the word's kana, somewhere plausible?" -- a
question you can answer without ever looking at the other kanji. Six rounds of patches went into
propping that up (positional start/end anchoring, 促音便, handakuten, an okurigana strict-then-loose
two-pass, a shared-prefix score, a consonant-row tiebreak, prefix/bound hyphen rules) and it still
credited 生 with the う of 誕生日, where 生 plainly sounds じょう.

Alignment asks the question the word actually poses: can every kanji be given a contiguous span of the
kana such that the spans, interleaved with the literal okurigana the headword writes, reconstruct the
reading exactly? That is a constraint over the whole word, so a wrong claim about one kanji fails
because the REST of the word can no longer be accounted for:

    誕生日 / たんじょうび  ->  誕:たん  生:じょう  日:び        (う for 生 leaves んじょうび unaccounted)
    売り切れる / うりきれる ->  売:う [り] 切:き [れる]          (れる for 売 strands うりき)
    硝子 / がらす          ->  no alignment exists              -> `irregular`

A word that cannot be aligned is NOT forced into a group. 今日 (きょう), 明日 (あした), 三味線
(しゃみせん) and 硝子 (がらす) are 熟字訓 or ateji -- whole-word readings belonging to no single
character -- and pretending they use a listed reading would teach a falsehood. They go to `irregular`
so the app can show them as what they are.

Alignment fixes the SPAN. Choosing between readings that share a span (痛い and 痛む both give 痛 the
span いた) is a separate question, answered below by the okurigana the headword actually writes.

Output: research/derived/kanji_reading_groups.json — the grouping plus, for each reading, the slots a
later authoring pass fills (a pt-BR note on what the reading means and when it is used). Nothing is
written into corpus/ here; this file is the input to that pass.

Usage: build_kanji_reading_groups.py
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kanji_align import (Aligner, bare, hira, masu_stem, no_kun_kanji,  # noqa: E402
                         row_of, variants)
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "derived" / "kanji_reading_groups.json"
LEVELS = ("n5", "n4", "n3")
SLOT_NOTE = """Choosing between readings that SHARE a span.

Alignment gives 痛 the span いた in both 痛い and 痛み, so the span alone cannot say which okurigana slot
the word belongs to. What can is the okurigana THE HEADWORD ITSELF WRITES after that kanji, judged
against each candidate reading's own okurigana. Four tests, in priority order:

  UNCHANGED SPAN  the reading matches the span as written, not through a sound change. 子供 gives 供 the
                  span ども, which is -ども exactly and とも only via rendaku, so -ども is the slot.
  EXACT           the word writes the reading's okurigana verbatim.      痛い    -> いた.い
  RELATED         it writes a recognisable INFLECTION of it. Japanese verbs inflect within a consonant
                  row, so 休み is a form of 休む (み and む are both ま-row) but not of 休まる; and the
                  撥音便 ぶ/む/ぬ -> ん makes 飛んだ a form of 飛ぶ.
  SHORTEST        among equals, the most basic form. 売り is 売る, not 売れる; 続き is 続く, not 続ける.

A reading whose okurigana is UNRELATED to what the word writes loses to a reading with no okurigana at
all, because an unrelated okurigana is positive evidence the word is not a form of that verb: 赤ちゃん
is not a form of 赤らめる and belongs on the bare あか, 出来る is not a form of 来す.

Every one of those tests was put here by a specific wrong grouping. Without SHORTEST, 休み went to
やす.まる and 見つける to み.える. Without RELATED, 済ませる went to す.まない -- the negative of a
different verb -- and 楽しみ to the adjective たの.しい instead of the verb たの.しむ it is the stem-noun
of. Without UNCHANGED SPAN, the bound forms -ども, -ぎわ, -がた, -ぶか and -ぐみ all lost their own
compounds to the unvoiced readings they are derived from.
"""
NASAL = {"ぶ": "ん", "む": "ん", "ぬ": "ん"}   # 撥音便: ぶ/む/ぬ -> ん


def oku_related(word_oku: str, oku: str) -> tuple[int, int]:
    """(shared prefix length, 1 if the first divergence is a plausible inflection else 0)."""
    if not word_oku or not oku:
        return (0, 0)
    shared = 0
    for a, b in zip(word_oku, oku):
        if a != b:
            break
        shared += 1
    if shared >= len(oku) or shared >= len(word_oku):
        return (shared, 1 if shared else 0)
    # Two i-adjective shapes the row test alone misses, both flagged by the verification pass:
    #   SUFFIX     the word's okurigana ENDS with the reading's. 煙たい is a form of 煙い (けむ.い), and
    #              たい ends in い; without this it fell to けむ.る, a different verb entirely.
    #   ADVERBIAL  い -> く. 亡くなる and 亡くす are built on the く-form of 亡い (な.い); the row test
    #              matched く against the き of な.き- instead, which is a bound okurigana the words
    #              do not write.
    # Both shapes are specific to the い-adjective ending, and the test has to say so. Written as the
    # general "word_oku ends with oku" it also fired on ね.る for 寝かせる -- かせる does end in る --
    # and pulled 寝かせる out of ね.かす, which is the slot it had just been fixed into.
    if oku == "い" and (word_oku.endswith("い") or word_oku.startswith("く")):
        return (shared, 2)
    a, b = word_oku[shared], oku[shared]
    ra, rb = row_of(a), row_of(b)
    if ra is not None and ra == rb:
        return (shared, 1)                       # same consonant row: 休み / 休む
    if NASAL.get(b) == a:
        return (shared, 1)                       # 撥音便: 飛んだ / 飛ぶ
    return (shared, 0)


def slot_score(word_oku: str, r: dict, span: str, unchanged: bool,
               chosen: bool = False, as_written: bool = True) -> tuple:
    """Rank one reading as the slot for a span. See SLOT_NOTE for why each term is here.

    `chosen` means the ALIGNER picked this very reading row when it solved the word, and it carries
    information nothing here can reconstruct: the aligner weighs 音訓 consistency across the whole
    compound, which is the only thing separating 気's real ON キ from the look-alike kun き our KANJIDIC
    import also lists. Both give 病気 the span き and neither has okurigana, so without this the tie fell
    to whichever was listed first, and all ten 気 compounds landed on the kun.

    `as_written` separates an okurigana absorbed verbatim from one absorbed in its masu-stem. 押入れ
    gives 押 the span おし, which is お.し- as written but お.す only after す -> し, so the first is the
    slot."""
    oku = hira(r.get("okurigana") or "").replace("-", "").replace("‐", "")
    if not word_oku:
        # The word writes no okurigana after this kanji, so a reading that demands some is the wrong
        # slot: 青白い gives 青 the bare span あお and belongs under あお, not あお.い.
        return (1 if unchanged else 0, 3 if not oku else 0, 0, 0,
                1 if as_written else 0, 1 if chosen else 0, 0)
    shared, related = oku_related(word_oku, oku)
    if word_oku == oku:
        kind = 4
    elif related >= 2:
        kind = 35 / 10          # between "related" and "exact": a recognised adjective form
    elif shared or related:
        # A shared leading run is evidence on its own, not only a divergence in the same row: 下さい
        # shares さ with くだ.さる, and judging only the divergence (い vs る) sent it to くだ.す.
        kind = 3
    elif not oku:
        kind = 2                                  # bare beats an UNRELATED okurigana
    else:
        kind = 1
    # An EXACT okurigana outranks an unchanged span. 役立つ writes つ, which is た.つ exactly, and the
    # bound -だ.て matches the rendaku'd span だ as written but carries the wrong okurigana; the word is
    # 立つ, so the okurigana is the stronger evidence. Below exact, the unchanged span still decides,
    # which is what keeps 子供 on -ども rather than on とも-via-rendaku.
    return (1 if kind == 4 else 0, 1 if unchanged else 0, kind, shared,
            1 if as_written else 0, 1 if chosen else 0, related, -len(oku))


def pick_slot(k: dict, span: str, word_oku: str, at_start: bool, at_end: bool,
              chosen: dict | None = None) -> dict | None:
    """The reading row whose span matches and whose okurigana best fits what the word writes."""
    whole = at_start and at_end
    ckey = (chosen or {}).get("reading")
    cands = []
    for r in k.get("readings") or []:
        if (r.get("type") or "").lower() == "nanori":
            continue
        b = bare(r.get("reading"))
        if not b:
            continue
        oku = hira(r.get("okurigana") or "").replace("-", "").replace("‐", "")
        # The span is the reading itself, or the reading with its okurigana absorbed (送り仮名の省略:
        # 立ち場 -> 立場, so 立's span たち is still the た.ち slot).
        # Mirror the aligner's absorption forms exactly. It accepts the okurigana both as written and
        # in its masu-stem (受け付け -> 受付, 待ち合い室 -> 待合室), so a slot lookup that only knew the
        # written form found nothing for spans the aligner had just resolved, and the word fell to
        # `irregular` having aligned perfectly well.
        stem = masu_stem(oku) if oku else ""
        absorbed = (variants(b + oku) if oku else []) + (variants(b + stem) if stem else [])
        plain = variants(b)
        if span not in plain and span not in absorbed:
            continue
        unchanged = span == b or (bool(oku) and span in (b + oku, b + stem))
        rd = (r.get("reading") or "").strip()
        # A LEADING hyphen marks a bound form, used only when the kanji is not word-initial (出's -で
        # must not claim 出会う); a TRAILING hyphen is its mirror, a prefix form. Neither restriction can
        # be meant for a one-character word, where the kanji is simultaneously initial and final.
        #
        # An EXACT okurigana match overrides the leading-hyphen hint, because it is direct evidence
        # about THIS word while the hyphen is a general claim about where the reading occurs.
        # KANJIDIC lists 持's もち as bound (-も.ち), yet 持ち writes 持 first and its ち verbatim;
        # honouring the hyphen sent it to も.つ, whose つ the word does not write at all.
        # POSITION IS NOT NEGOTIABLE. An earlier version let an exact okurigana match override the
        # leading hyphen, to pull 持ち into -も.ち. That was wrong twice over: the hyphen states WHERE
        # the reading occurs, and an okurigana says nothing about position, so the override let every
        # word-initial word into a suffix slot -- 読み, 読み上げる, 飲み物, 飲み込む, 行き, 回り, 通り,
        # 向き and more, filling -よ.み and -の.み entirely with counterexamples while よ.む and の.む
        # showed only their dictionary forms. 持ち belongs with も.つ for the same reason 痛み belongs
        # with いた.む: it is the 連用形 of the verb, and the suffix slot is for 気持ち and 金持ち.
        if rd.startswith(("-", "‐")) and at_start and not whole:
            continue
        if rd.endswith(("-", "‐")) and at_end and not whole:
            continue
        as_written = span in plain or (bool(oku) and span in variants(b + oku))
        sc = slot_score(word_oku, r, span, unchanged,
                        chosen=(ckey is not None and r.get("reading") == ckey),
                        as_written=as_written)
        if (r.get("type") or "").lower() == "kun" and k["character"] in no_kun_kanji():
            # Second source says this kanji has no kun reading at all; see kanji_align.no_kun_kanji.
            sc = (-1,) + sc
        else:
            sc = (0,) + sc
        cands.append((sc, r))
    if not cands:
        return None
    cands.sort(key=lambda t: t[0], reverse=True)
    return cands[0][1]


def main() -> int:
    entries = []
    for lv in LEVELS:
        entries += json.loads((ROOT / "corpus" / "kanji" / f"{lv}.json").read_text(encoding="utf-8"))
    aligner = Aligner()

    out, stats = [], Counter()
    for k in entries:
        reads = k.get("readings") or []
        words = k.get("example_words") or []
        ch = k["character"]
        groups: dict[str, list] = {}
        irregular = []
        for w in words:
            hw = w.get("headword") or ""
            got = aligner.span_of(hw, w.get("kana") or "", ch)
            if got is None:
                # No assignment of spans reconstructs the reading -> 熟字訓 / ateji / a reading we do
                # not hold. Recorded as irregular rather than forced into a group.
                irregular.append({"headword": hw, "kana": w.get("kana"),
                                  "vocab_id": w.get("vocab_id"),
                                  "gloss_pt": (w.get("gloss") or {}).get("pt-BR")})
                stats["irregular"] += 1
                continue
            idx = hw.find(ch)
            r = pick_slot(k, got["span"], got["okurigana"], idx == 0, idx == len(hw) - 1,
                          chosen=got.get("reading"))
            if r is None:
                irregular.append({"headword": hw, "kana": w.get("kana"),
                                  "vocab_id": w.get("vocab_id"),
                                  "gloss_pt": (w.get("gloss") or {}).get("pt-BR")})
                stats["aligned but no slot"] += 1
                continue
            key = f"{r.get('reading')}|{r.get('okurigana') or ''}"
            bucket = groups.setdefault(key, [])
            # example_words can list the same compound twice (日曜日 under ニチ); dedupe by headword.
            if any(c["headword"] == hw for c in bucket):
                continue
            bucket.append({"headword": hw, "kana": w.get("kana"), "vocab_id": w.get("vocab_id"),
                           "gloss_pt": (w.get("gloss") or {}).get("pt-BR")})
            stats["grouped"] += 1

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
