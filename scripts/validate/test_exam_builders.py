#!/usr/bin/env python3
"""W16 — unit tests for the two exam-builder rules that read the real passage.

RULE 1: a text_grammar blank is cut at SudachiPy token boundaries, never inside a word.
`build_exam_banks.py` used to blank a grammar form with `jp.replace(form, "（　）", 1)`, which cuts
wherever the characters line up. Measured on the 286 current passages, that cut INSIDE a word in 59
of them: `ても` out of とても (「子どもはと（　）よろこんでくれた」), `せいで` out of れいせいで,
`こと` out of ことば, `かけ` out of 出かけた. A stem blanked mid-word is not a grammar question — the
learner is being asked to repair a typo, and none of the whole-form distractors can fit the hole.

RULE 2: a reading_comp item is checked AGAINST ITS PASSAGE. The old builder never read one: it
confirmed the `read:` slug resolved and shipped. P1 requires a content word of the question to occur
in the passage; P2/P3 require every option to be readable inside the gating lesson's known set; P4
rejects an item whose correct answer is the only option printed verbatim in the passage (answerable
by string search).

Exit 1 on any failure. Usage: test_exam_builders.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "scripts" / "export"))
sys.path.append(str(ROOT / "scripts" / "ingest"))
import build_exam_banks as beb                                        # noqa: E402
from build_reading_comp_bank import option_problems, question_is_about  # noqa: E402
from known_set import KnownSet, PassageGate                            # noqa: E402


def main() -> int:
    fails: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")
        if not cond:
            fails.append(name)

    tok = beb._tok()
    mode = beb._MODE_C

    # ---- RULE 1 ----------------------------------------------------------------------------
    jp = "子どもはとてもよろこんでくれた。"
    starts, ends = beb.token_spans(tok, mode, jp)
    check("R1a ても inside とても is refused",
          beb.boundary_occurrence(jp, "ても", starts, ends) == -1
          and jp.find("ても") != -1,
          f"plain find at {jp.find('ても')}, boundary search "
          f"{beb.boundary_occurrence(jp, 'ても', starts, ends)}")

    jp2 = "土曜の朝、父とドライブに出かけた。"
    s2, e2 = beb.token_spans(tok, mode, jp2)
    check("R1b かけ inside 出かけた is refused (it is okurigana, not a form)",
          beb.boundary_occurrence(jp2, "かけ", s2, e2) == -1)

    jp3 = "雨がふるかもしれない。"
    s3, e3 = beb.token_spans(tok, mode, jp3)
    at = beb.boundary_occurrence(jp3, "かもしれない", s3, e3)
    check("R1c a real token-aligned form IS found, at the right offset",
          at == jp3.find("かもしれない") and at > 0,
          f"at={at} find={jp3.find('かもしれない')}")
    check("R1d the blank replaces exactly that span",
          jp3[:at] + "（　）" + jp3[at + len("かもしれない"):] == "雨がふる（　）。")

    jp4 = "ことばがとてもていねいだ。"
    s4, e4 = beb.token_spans(tok, mode, jp4)
    check("R1e こと inside ことば is refused",
          beb.boundary_occurrence(jp4, "こと", s4, e4) == -1)

    # ---- RULE 2 ----------------------------------------------------------------------------
    gate = PassageGate()
    passage = "きのう、ともだちとえいがを見ました。えいがはおもしろくありませんでした。"
    check("R2a a question sharing a content word with the passage is 'about' it",
          question_is_about("えいがはどうでしたか。", passage, gate) != [])
    check("R2b a question sharing nothing with the passage is not",
          question_is_about("この人は何を買いましたか。", passage, gate) == [],
          str(question_is_about("この人は何を買いましたか。", passage, gate)))

    # P2/P3: 橋 (vocab:1237410, N5) taught, 箸 (vocab:1476410) not
    ks_ok = KnownSet("les:t", frozenset("橋見"), frozenset({"vocab:1237410"}), frozenset())
    ks_no = KnownSet("les:t", frozenset("見"), frozenset({"vocab:1237410"}), frozenset())
    check("R2c an option whose kanji the lesson teaches passes",
          option_problems(["橋"], ks_ok, gate) == "", option_problems(["橋"], ks_ok, gate))
    check("R2d an option with an untaught kanji is rejected, and says which",
          "untaught kanji 橋" in option_problems(["橋"], ks_no, gate),
          option_problems(["橋"], ks_no, gate))
    ks_word = KnownSet("les:t", frozenset("橋箸"), frozenset({"vocab:1237410"}), frozenset())
    check("R2e an option whose WORD the lesson has not taught is rejected",
          "untaught word" in option_problems(["箸"], ks_word, gate),
          option_problems(["箸"], ks_word, gate))

    print(f"\ntest_exam_builders: 9 checks, {len(fails)} FAIL")
    for f in fails:
        print(f"  ! {f}")
    if fails:
        return 1
    print("test_exam_builders: ALL OK — the blank lands on a word boundary and an exam item is "
          "checked against the passage it is printed under")
    return 0


if __name__ == "__main__":
    sys.exit(main())
