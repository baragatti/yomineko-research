#!/usr/bin/env python3
"""Regression cases for the kanji/kana aligner. Every one of these was a real defect.

The alignment rules interact — rendaku, gemination, okurigana absorption, the masu-stem, the iteration
mark, the plausible-truncation cap, the Kanji Alive kun cross-check — and each was added to fix a
specific wrong grouping. Adding the next rule has twice re-broken an earlier case (the exact-okurigana
override put word-initial words into suffix slots; partial alignment rescued 明日 from `irregular`), so
the cases live here rather than in a commit message.

Each row is (headword, kana, kanji, expected span or None for irregular, why it is here).

Usage: test_kanji_align.py   — exits non-zero on any mismatch.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "export"))
from kanji_align import Aligner  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

CASES = [
    # word, kana, kanji, expected span (None = must not align, i.e. irregular), reason
    ("誕生日", "たんじょうび", "生", "じょう", "whole-word alignment: 生 is じょう, not the う a substring match found"),
    ("誕生日", "たんじょうび", "日", "び", "rendaku on the final element"),
    ("日曜日", "にちようび", "日", "にち", "same kanji twice, different spans"),
    ("一人", "ひとり", "人", "り", "ひと belongs to 一, not to 人"),
    ("三味線", "しゃみせん", "三", None, "熟字訓: み belongs to 味, and 三 is しゃ, which it does not have"),
    ("今日", "きょう", "日", None, "熟字訓: belongs to no single character"),
    ("明日", "あした", "明", None, "熟字訓: partial alignment must NOT rescue this via 明=あ"),
    ("硝子", "がらす", "子", None, "ateji: す is a listed reading of 子, but がら fails for 硝"),
    ("日本", "にほん", "本", "ほん", "one unresolved kanji is allowed: 日's に is nanori-only here"),
    ("日本", "にほん", "日", None, "...and the unresolved kanji itself still gets no group"),
    ("立場", "たちば", "立", "たち", "送り仮名の省略: 立ち場 -> 立場, so 立 carries the ち"),
    ("押入れ", "おしいれ", "押", "おし", "same, with the し absorbed"),
    ("割引", "わりびき", "割", "わり", "absorbed okurigana in MASU-STEM form (割り引き -> 割引)"),
    ("受付", "うけつけ", "受", "うけ", "masu-stem absorption on an ichidan verb"),
    ("持ち", "もち", "持", "も", "the ち is written, so it is okurigana and NOT absorbed"),
    ("売り切れる", "うりきれる", "売", "う", "the れる is 切れる's; 売 owns only う"),
    ("切手", "きって", "切", "きっ", "gemination ADDED after the reading, not substituted for its last mora"),
    ("出発", "しゅっぱつ", "出", "しゅっ", "促音便: シュツ -> しゅっ"),
    ("一杯", "いっぱい", "杯", "ぱい", "handakuten after っ"),
    ("時々", "ときどき", "時", "とき", "iteration mark repeats the previous kanji"),
    ("様々", "さまざま", "様", "さま", "...and the repeat voices"),
    ("ヶ月", "かげつ", "月", "げつ", "small ヶ is an abbreviation of 箇 reading か, not kana"),
    ("図書館", "としょかん", "館", "かん", "plain multi-kanji on-compound"),
    ("青白い", "あおじろい", "青", "あお", "the い belongs to 白い, so 青 takes a bare span"),
    ("人質", "ひとじち", "質", "じち", "シチ voiced, not the チ a substring match found"),
]


def main() -> int:
    a = Aligner()
    fails = []
    for hw, kana, ch, want, why in CASES:
        got = a.span_of(hw, kana, ch)
        span = got["span"] if got else None
        if span != want:
            fails.append(f"{hw} ({kana}) / {ch}: expected {want!r}, got {span!r}  -- {why}")
    print(f"test_kanji_align: {len(CASES)} cases, {len(fails)} FAIL")
    for f in fails:
        print(f"  [FAIL] {f}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
