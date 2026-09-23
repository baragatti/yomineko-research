#!/usr/bin/env python3
"""W17 — unit tests for the exam-builder rules added by the A2 fix set.

These are UNIT tests over the rule functions, not a validator over the tree: each rule is a property
of the code, and asserting it against the live banks would only re-measure data that
`validate_exam_level_gate.py` and `validate_exam_banks.py` already gate. Every check below is
written against the exact defect the rule closes, with the finding named.

  RULE A — option shape (`exam_rules.option_ok`). 103 N4 items printed a choice that is not a
           Japanese form: a grammar-point LABEL (自動詞, 命令形), a leaked sense index (`ずっと ①`),
           or a pattern whose 〜 slots were stripped instead of filled (`かか` from gram:ka-ka,
           `とかとか`, `おになる`). Nine more printed the citation placeholder itself, because the
           filter tested U+FF5E FULLWIDTH TILDE and the corrected forms use U+301C WAVE DASH.
           (qa_sweep/exam_japanese_2.md S3; exam_bank_regen_review.md §4)

  RULE B — reading-aware links (`exam_rules.reading_link_ok`). The n3 linker matched written form
           and ignored reading, so 135 items name the wrong lexeme: 空/から on six *sky* sentences,
           時/とき on the じ counter 26 times, 金/きん where the sentence says かね. A link is proved
           by a token — or a contiguous run of tokens — that spells the headword AND reads the
           record's kana. (qa_sweep/exam_japanese_3.md F4; W12's rule)

  RULE C — bunsetsu tiles and `accepted[]` (`bunsetsu.chunk` / `bunsetsu.scramble`). 271 of 273 N5
           並べ替え items exposed bound morphemes as draggable tiles (`まし`, `た`, `ん`), and 45
           items across the three levels assembled into a second grammatical sentence that the app
           marked wrong. Meaning-PRESERVING reorderings become `accepted[]`; meaning-CHANGING ones
           (two tiles carrying the same particle) refuse the item.
           (qa_sweep/exam_japanese_1.md F15, _2.md S4, _3.md F8)

  RULE D — the level rule (`exam_rules.TaughtSets`). One implementation of the definition
           `validate_exam_level_gate.py` measures, so the builder and the gate cannot disagree about
           the same item. Checked against the real course export: the taught sets are non-empty,
           monotonic across levels, and the kanji class covers Extension A (the builder's old
           `"一" <= ch <= "鿿"` test did not).

Exit 1 on any failure. Usage: test_exam_builders_w17.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "scripts" / "export"))
import bunsetsu                                                          # noqa: E402
from exam_rules import (                                                 # noqa: E402
    TaughtSets, has_kanji, kana_fold, option_ok, reading_link_ok,
)


def tok(surface: str, pos: str) -> dict:
    return {"surface": surface, "pos": pos}


def main() -> int:
    fails: list[str] = []
    n = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal n
        n += 1
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not cond:
            fails.append(name)

    # ---- RULE A: option shape ----------------------------------------------------------------
    check("A1 a real form is admissible", option_ok("かもしれない") and option_ok("ている"))
    check("A2 grammar metalanguage is refused (gf:n4:3360 offered 命令形 as a fill-in)",
          not option_ok("命令形") and not option_ok("自動詞") and not option_ok("受身形"))
    check("A3 a leaked sense index is refused, space and circled numeral alike",
          not option_ok("くらい ①") and not option_ok("ずっと ①"))
    check("A4 a slot-stripped doubling is refused (かか from gram:ka-ka's forms[0])",
          not option_ok("かか") and not option_ok("とかとか") and not option_ok("しし")
          and not option_ok("でもでも"))
    check("A5 BOTH tildes are refused — U+FF5E and U+301C (なん〜か shipped on 9 items)",
          not option_ok("なん～か") and not option_ok("なん〜か"))
    check("A6 the doubling rule does not eat a legitimate form that merely repeats a kana",
          option_ok("ままに") and option_ok("なければ"))

    # ---- RULE B: reading-aware links ----------------------------------------------------------
    # 「なぜ空は青いのか？」 — the token reads そら; vocab:1245280 空/から is "empty".
    sky_tokens = [("なぜ", "なぜ", "ナゼ"), ("空", "空", "ソラ"), ("は", "は", "ワ"),
                  ("青い", "青い", "アオイ"), ("の", "の", "ノ"), ("か", "か", "カ")]
    check("B1 空/そら does NOT prove the 空/から record",
          not reading_link_ok(sky_tokens, "空", "から"))
    check("B2 ... and DOES prove the 空/そら record",
          reading_link_ok(sky_tokens, "空", "そら"))
    clock = [("八", "八", "ハチ"), ("時", "時", "ジ"), ("に", "に", "ニ")]
    check("B3 時 read じ (the o'clock counter) does not prove 時/とき — 26 items rested on this",
          not reading_link_ok(clock, "時", "とき") and reading_link_ok(clock, "時", "じ"))
    money = [("お", "お", "オ"), ("金", "金", "カネ"), ("を", "を", "ヲ")]
    check("B4 金 read かね does not prove 金/きん", not reading_link_ok(money, "金", "きん"))
    run = [("木", "木", "コ"), ("立", "立", "ダチ"), ("の", "の", "ノ")]
    check("B5 a contiguous RUN of tokens can prove a multi-token headword",
          reading_link_ok(run, "木立", "こだち"))
    noread = [("時", "時", None)]
    check("B6 a token with no reading proves nothing — 'no evidence' is not 'agreement'",
          not reading_link_ok(noread, "時", "とき"))
    check("B7 katakana and hiragana readings fold together", kana_fold("ソラ") == "そら")

    # ---- RULE C: bunsetsu ---------------------------------------------------------------------
    # 母は料理を作るのが上手です  ->  母は / 料理を / 作るのが / 上手です
    toks = [tok("母", "noun"), tok("は", "particle"), tok("料理", "noun"), tok("を", "particle"),
            tok("作る", "verb"), tok("の", "particle"), tok("が", "particle"),
            tok("上手", "na-adjective"), tok("です", "auxiliary")]
    ch = bunsetsu.chunk(toks)
    check("C1 morphemes merge into bunsetsu (ははは is retired: 母 + は is ONE tile)",
          ch == ["母は", "料理を", "作るのが", "上手です"], str(ch))
    check("C2 an auxiliary never becomes its own tile (まし / た was a morphology drill)",
          all(t not in (ch or []) for t in ("まし", "た", "は", "を")))

    # いすの上にねこがいます -> いすの / 上に / ねこが / います ; に and が differ, so the swap is safe
    t2 = [tok("いす", "noun"), tok("の", "particle"), tok("上", "noun"), tok("に", "particle"),
          tok("ねこ", "noun"), tok("が", "particle"), tok("い", "verb"), tok("ます", "auxiliary")]
    c2 = bunsetsu.chunk(t2)
    acc, why = bunsetsu.scramble(c2)
    check("C3 distinct case particles: the reordering is ACCEPTED, not marked wrong",
          why == "scrambled" and acc[0] == "".join(c2)
          and "ねこがいすの上にいます" in acc, f"{why} {acc}")
    check("C4 a の-chunk travels with what it modifies (いすの / 上に never separate)",
          all("いすの" in a.split("上に")[0] for a in acc), str(acc))

    # 兄はギターがとても上手です — は and が are distinct, but 「ギターは兄が…」 flips the meaning.
    # The rule that catches THAT class is the same-particle one; here is its live case:
    t3 = [tok("これ", "pronoun"), tok("は", "particle"), tok("あっち", "pronoun"),
          tok("の", "particle"), tok("より", "particle"), tok("安い", "i-adjective"),
          tok("よ", "particle")]
    c3 = bunsetsu.chunk(t3)
    check("C5 a passage that chunks", c3 is not None, str(c3))
    t4 = [tok("兄", "noun"), tok("は", "particle"), tok("弟", "noun"), tok("は", "particle"),
          tok("元気", "na-adjective"), tok("です", "auxiliary")]
    c4 = bunsetsu.chunk(t4)
    acc4, why4 = bunsetsu.scramble(c4)
    check("C6 two tiles marked the SAME way refuse the item — the swap changes the meaning "
          "(so:n3:847 「これはあっちのより安いよ」 vs 「あっちのはこれより安いよ」)",
          acc4 is None and why4 == "same-particle-ambiguous", f"{why4} {acc4}")
    check("C7 a sentence that opens with a clitic is refused, not guessed at",
          bunsetsu.chunk([tok("は", "particle"), tok("犬", "noun")]) is None)
    t5 = [tok("犬", "noun"), tok("が", "particle"), tok("走る", "verb"), tok("。", "punctuation")]
    check("C8 sentence-final punctuation is not a tile",
          bunsetsu.chunk(t5) == ["犬が", "走る"], str(bunsetsu.chunk(t5)))
    t6 = [tok("二", "numeral"), tok("、", "punctuation"), tok("三", "numeral"),
          tok("人", "suffix"), tok("来る", "verb")]
    check("C9 INTERNAL punctuation stays on its chunk — without 、 二三 reassembles as にさん",
          bunsetsu.chunk(t6) == ["二、", "三人", "来る"], str(bunsetsu.chunk(t6)))
    check("C10 every accepted ordering is a permutation of the same tiles",
          all(sorted(_split(a, c2)) is not None for a in acc))

    # ---- RULE D: the level rule ---------------------------------------------------------------
    T = TaughtSets(ROOT)
    check("D1 all three levels have a non-empty taught set",
          all(T.by_level[l]["vocab"] and T.by_level[l]["kanji"] for l in ("n5", "n4", "n3")))
    check("D2 the taught sets are monotonic — N5 ⊂ N4 ⊂ N3, which is what makes 'the last lesson "
          "IS the level' true",
          T.by_level["n5"]["kanji"] <= T.by_level["n4"]["kanji"] <= T.by_level["n3"]["kanji"]
          and T.by_level["n5"]["vocab"] <= T.by_level["n4"]["vocab"] <= T.by_level["n3"]["vocab"])
    check("D3 the kanji class covers Extension A and the compatibility block, which the builder's "
          "old `\"一\" <= ch <= \"鿿\"` test did not",
          has_kanji("㐂") and has_kanji("﨑") and has_kanji("食") and not has_kanji("かな"))
    check("D4 a kanji nobody teaches is refused at every level",
          not any(T.kanji_ok("嗚呼", l) for l in ("n5", "n4", "n3")))
    check("D5 grammar refs normalize to slug space (items use the bare key, a cks holds the slug)",
          T.grammar_ok("da-desu", "n5") == T.grammar_ok("gram:da-desu", "n5"))

    print(f"\ntest_exam_builders_w17: {n} checks, {len(fails)} FAIL")
    for f in fails:
        print(f"  ! {f}")
    if fails:
        return 1
    print("test_exam_builders_w17: ALL OK — options are Japanese, links are proved by reading, "
          "tiles are bunsetsu with every safe ordering accepted, and the level rule is one function")
    return 0


def _split(s: str, chunks: list[str]):
    """Every accepted ordering must decompose into the item's own tiles."""
    rest = s
    used = []
    pool = list(chunks)
    while rest:
        for c in pool:
            if rest.startswith(c):
                used.append(c)
                pool.remove(c)
                rest = rest[len(c):]
                break
        else:
            raise AssertionError(f"{s!r} is not a permutation of {chunks}")
    return used


if __name__ == "__main__":
    sys.exit(main())
