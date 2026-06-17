#!/usr/bin/env python3
"""P8 — remove emoji from learner text in authored lessons (owner directive: no emoji in text).

Semantic cues must come from <note type="..."> blocks (the app renders the icon), NOT inline emoji characters
like 💡/⚠. This strips emoji from every string field of each lesson and tidies the whitespace left behind
(e.g. "💡 Vantagem" -> "Vantagem", "texto 💡 fim" -> "texto fim"). Japanese, pt-BR, romaji are untouched.
Idempotent. Run before load/validate. Usage:
  strip_emoji_lessons.py            # all research/derived/lessons/*.json
  strip_emoji_lessons.py <slug...>  # only the named lessons
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LESSON_DIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"

# emoji / pictograph / dingbat / symbol ranges + variation selector + ZWJ; NOT CJK, NOT chōon ー (U+30FC)
EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"   # misc pictographs, emoticons, transport, supplemental, symbols-and-pictographs-ext
    "\U00002600-\U000026FF"   # miscellaneous symbols (⚠ ☀ ★ …)
    "\U00002700-\U000027BF"   # dingbats (✅ ✏ …)
    "\U00002B00-\U00002BFF"   # arrows/stars block (⭐ …)
    "\U0001F1E6-\U0001F1FF"   # regional indicators
    "\U0000FE00-\U0000FE0F"   # variation selectors
    "\U0000200D"              # zero-width joiner
    "\U000023E9-\U000023FA"   # media symbols
    "]",
)


def _clean(s: str) -> str:
    out = EMOJI.sub("", s)
    # collapse the spaces/orphans an emoji used to occupy, without touching newlines structure
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"(<text[^>]*>) +", r"\1", out)   # leading space inside a text run
    out = re.sub(r" +(</text>)", r"\1", out)        # trailing space inside a text run
    out = re.sub(r"> +([,.;:!?])", r">\1", out)      # space before punctuation right after a tag
    return out


def _walk(o, n):
    if isinstance(o, str):
        c = _clean(o)
        if c != o:
            n[0] += 1
        return c
    if isinstance(o, list):
        return [_walk(x, n) for x in o]
    if isinstance(o, dict):
        return {k: _walk(v, n) for k, v in o.items()}
    return o


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
        n = [0]
        nd = _walk(d, n)
        if n[0]:
            f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total += n[0]
            touched += 1
    print(f"stripped emoji from {total} field(s) across {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
