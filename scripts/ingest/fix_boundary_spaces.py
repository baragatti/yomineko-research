#!/usr/bin/env python3
"""P8 — repair word-separating spaces lost at inline-tag boundaries.

A buggy earlier emoji-strip pass trimmed the single spaces that authors place INSIDE <text> runs to separate
words across adjacent inline tags, so e.g. `<text>você </text><text weight="bold">consegue</text>` became
`<text>você</text><text weight="bold">consegue</text>` and renders "vocêconsegue". This re-inserts a space at
every inline boundary `</A><B>` whose two touching characters need one: it acts only when at least one touching
char is a Latin letter/digit (so pt↔pt and pt↔Japanese get a space, but Japanese↔Japanese like 食べ+ます do
NOT), and never around bracketing/trailing punctuation. The space is placed INSIDE a <text> run when possible
(so it renders regardless of how inter-tag whitespace is handled). Idempotent. Usage:
  fix_boundary_spaces.py            # all
  fix_boundary_spaces.py <slug...>  # only named
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LESSON_DIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"
INLINE = "text|emphasis|jp|romaji|term"
CHIP = r"grammar|vocab|kanji|break"
# (1) inline close -> inline open: g1=last char of A; close; open; (lookahead) g4=first char of B
P_ELEM = re.compile(r"(\S)(</(?:" + INLINE + r")>)(<(?:" + INLINE + r")[^>]*>)(?=(\S))")
# (2) inline close -> self-closing chip: g1=last char of A; close; chip
P_CHIP_R = re.compile(r"(\S)(</(?:" + INLINE + r")>)(<(?:" + CHIP + r")\b[^>]*/>)")
# (3) self-closing chip -> inline open: chip; open; (lookahead) g3=first char of B
P_CHIP_L = re.compile(r"(<(?:" + CHIP + r")\b[^>]*/>)(<(?:" + INLINE + r")[^>]*>)(?=(\S))")
OPEN_PUNCT = set("([{「『“\"'¿¡")
CLOSE_PUNCT = set(")]}」』”\"',.;:!?…、。）")


def _latin(c: str) -> bool:
    # a Latin-script word char (ASCII + accented pt-BR like é/ã/ç), excluding CJK (kana/kanji >= U+3000)
    return c.isalnum() and ord(c) < 0x3000


def fix_body(body: str) -> tuple[str, int]:
    n = [0]

    def repl_elem(m):
        a, close, open_, b = m.group(1), m.group(2), m.group(3), m.group(4)
        if not (_latin(a) or _latin(b)) or a in OPEN_PUNCT or b in CLOSE_PUNCT:
            return m.group(0)
        n[0] += 1
        if open_.startswith("<text"):
            return f"{a}{close}{open_} "
        if close == "</text>":
            return f"{a} {close}{open_}"
        return f"{a}{close} {open_}"

    def repl_chip_r(m):  # text…A</text><chip/>  -> A </text><chip/>  (chip renders a word)
        a, close, chip = m.group(1), m.group(2), m.group(3)
        if not _latin(a) or a in OPEN_PUNCT:
            return m.group(0)
        n[0] += 1
        return f"{a} {close}{chip}" if close == "</text>" else f"{a}{close} {chip}"

    def repl_chip_l(m):  # <chip/><text>Bfoo -> <chip/><text> Bfoo
        chip, open_, b = m.group(1), m.group(2), m.group(3)
        if not _latin(b) or b in CLOSE_PUNCT:
            return m.group(0)
        n[0] += 1
        return f"{chip}{open_} " if open_.startswith("<text") else f"{chip} {open_}"

    body = P_ELEM.sub(repl_elem, body)
    body = P_CHIP_R.sub(repl_chip_r, body)
    body = P_CHIP_L.sub(repl_chip_l, body)
    return body, n[0]


def main() -> int:
    if len(sys.argv) > 1:
        files = [LESSON_DIR / ((a.split(":", 1)[1] if ":" in a else a) + ".json") for a in sys.argv[1:]]
    else:
        files = sorted(LESSON_DIR.glob("*.json"))
    total = 0
    touched = 0
    for f in files:
        if not f.exists():
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        nb, n = fix_body(d.get("body", "") or "")
        if n:
            d["body"] = nb
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total += n
            touched += 1
    print(f"re-inserted {total} boundary space(s) across {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
