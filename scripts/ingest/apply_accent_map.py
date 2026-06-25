#!/usr/bin/env python3
"""Apply a vetted unaccented->accented whole-word map (research/derived/_accent_vetted.json) to lesson string
fields, reusing the safe application logic from fix_accents_lessons (word-bounded, case-preserving, only text
between tags, never identifiers/attributes). Entries are unambiguous (-ção/-ões/-ário/-ável/-ência families +
explicit content nouns); ambiguous homographs (tem/têm, esta/está, e/é) are intentionally NOT included.
Usage: apply_accent_map.py"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
MAP = json.loads((ROOT / "research" / "derived" / "_accent_vetted.json").read_text(encoding="utf-8"))
MAP = {k: v for k, v in MAP.items() if k != v}
_KEYS = sorted(MAP, key=len, reverse=True)
_RX = re.compile(r"(?<![0-9A-Za-zÀ-ÿ])(" + "|".join(re.escape(k) for k in _KEYS) + r")(?![0-9A-Za-zÀ-ÿ])", re.IGNORECASE)
_SKIP = {"slug", "topic", "ref"}


def _case(src, repl):
    if src.isupper():
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def _fix(s, c):
    def sub(m):
        repl = MAP.get(m.group(1).lower())
        if repl:
            c[0] += 1
            return _case(m.group(1), repl)
        return m.group(1)
    return _RX.sub(sub, s)


def _fix_body(s, c):
    return re.sub(r">([^<>]+)<", lambda m: ">" + _fix(m.group(1), c) + "<", s)


def _walk(o, c, key=None):
    if isinstance(o, str):
        if key in _SKIP:
            return o
        return _fix_body(o, c) if key == "body" else _fix(o, c)
    if isinstance(o, list):
        return [_walk(x, c, key) for x in o]
    if isinstance(o, dict):
        return {k: _walk(v, c, k) for k, v in o.items()}
    return o


def main() -> int:
    total, touched = 0, 0
    for f in sorted(LDIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        c = [0]
        nd = _walk(d, c)
        if c[0]:
            f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total += c[0]; touched += 1
    print(f"applied vetted accents: {total} word(s) across {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
