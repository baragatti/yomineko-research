"""Matching a grammar point's `forms[]` against real Japanese text.

A form is written the way a textbook writes it: `たり～たりする`, `お～ください`, `の中で[A]が一番`,
`～(ん)だもの`. The tilde (～ or 〜) and a bracketed label stand for the variable slot; a
parenthesised element is optional. 135 of the registry's 536 forms carry a placeholder — every N3
record does — so a matcher that tests `form in text` has never matched an N3 pattern at all, and
broke outright when eight N5/N4 records were moved onto the same convention (their old forms were
glued fragments like `たりたりする` and `しし`, which no sentence contains either).

The rule here: strip optional groups to their minimal form, split on placeholders, and require
every remaining piece to occur in the text IN ORDER. The whole of `たり～たりする` is therefore found
in 食べたり見たりする, and `～てすみません` in 遅れてすみません. Both the speaking-path builder and its
validator use this one function, so they cannot disagree about what a form matches.

Deliberately NOT handled: sound changes. `たり～たりする` does not match 食べたり飲んだりする, because
飲む takes rendaku (だり) and the form says たり. That is the grammar record's business — a point
whose surface alternates lists the alternate as a second form — not the matcher's, which must stay
literal so a match means what it says.
"""
from __future__ import annotations

import re

_OPTIONAL = re.compile(r"[（(][^)）]*[)）]")
_PLACEHOLDER = re.compile(r"[～〜]|\[[^\]]*\]")


def form_pieces(form: str) -> list[str]:
    """The literal pieces a form requires, in order; empty for a form that is all placeholder."""
    minimal = _OPTIONAL.sub("", form or "")
    return [p for p in _PLACEHOLDER.split(minimal) if p]


def form_key(form: str) -> str:
    """The form with placeholders and optional groups removed — what two records must share to be
    claiming the same surface pattern (used by the same-point-twice check)."""
    return "".join(form_pieces(form))


def form_in(form: str, text: str) -> bool:
    """True when every literal piece of `form` occurs in `text`, in order, non-overlapping."""
    pieces = form_pieces(form)
    if not pieces:
        return False
    pos = 0
    for p in pieces:
        i = text.find(p, pos)
        if i < 0:
            return False
        pos = i + len(p)
    return True


def matched_length(form: str, text: str) -> int:
    """Total literal characters a matching form pins in the text (0 when it does not match) — the
    builder ranks candidate patterns by how much of the phrase they account for."""
    return sum(len(p) for p in form_pieces(form)) if form_in(form, text) else 0


if __name__ == "__main__":  # a runnable proof, not a test framework
    import sys
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    cases = [
        ("たり～たりする", "食べたり見たりする", True),
        ("たり～たりする", "食べたり飲んだりする", False),  # rendaku: だり is not たり (see docstring)
        ("～てすみません", "遅れてすみません。", True),
        ("お～ください", "お待ちください", True),
        ("の中で[A]が一番", "季節の中で春が一番好きだ", True),
        ("～(ん)だもの", "行きたくないんだもの", True),
        ("～(ん)だもの", "行きたくないだもの", True),
        ("たり～たりする", "たりする", False),          # first piece must precede the second
        ("しし", "おいしいし安い", False),               # the OLD glued fragment never matched
        ("し～し", "おいしいし安いし", True),
        ("～さ", "寒さ", True),
    ]
    bad = [(f, t, want) for f, t, want in cases if form_in(f, t) != want]
    print("pattern_forms: all cases pass" if not bad else f"pattern_forms: FAILED {bad}")
    raise SystemExit(1 if bad else 0)
