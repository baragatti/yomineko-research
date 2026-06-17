#!/usr/bin/env python3
"""P8 — enforce the standing lesson-hygiene rules (design/quality_rubric.md §P8) as a committed validator.

These rules were previously only enforced by one-off fixer scripts; this is the GUARD that fails CI if any
regress. Checks every authored lesson JSON (research/derived/lessons/*.json) for:
  - emoji anywhere in a string field (cues must come from <note type> blocks)
  - literal backslash (over-escaping artifact)
  - run-together word boundaries (a space lost between adjacent inline tags)
  - accent-stripped pt-BR words (nao/voce/licao/…) in any field
  - meta/orchestration leak in title/description/body ("Authored…","Polished…","placeholder",…)
  - empty inline wrappers (<text></text>, <emphasis></emphasis>, …)
  - banned em dash (U+2014) anywhere
  - identifier fields (slug/topic/refs) must stay ASCII
Read-only; exits non-zero on any failure. Usage: audit_lesson_hygiene.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LESSON_DIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"
BS = chr(92)
EMOJI = re.compile("[" "\U0001F300-\U0001FAFF" "\U00002600-\U000026FF" "\U00002700-\U000027BF"
                   "\U00002B00-\U00002BFF" "\U0001F1E6-\U0001F1FF" "]")
EMPTY = re.compile(r"<(text|emphasis|romaji|term)(?:\s[^>]*)?></\1>")
BOUNDARY = re.compile(r"(\S)(</(?:text|emphasis|jp|romaji|term)>)"
                      r"((?:<(?:text|emphasis|jp|romaji|term)[^>]*>)|(?:<(?:grammar|vocab|kanji|break)\b[^>]*/>))(?=(\S))")
ACCENT_STRIPPED = re.compile(
    r"(?<![0-9A-Za-zÀ-ÿ])(nao|voce|voces|licao|licoes|acao|acoes|portugues|tambem|entao|comeco|familia|"
    r"consequencia|vocabulario|mnemonico|duvida|possivel|topico|particula|reconheco|conheco|tres|"
    r"consciencia|experiencia|japones|ingles|alem|porem|conjugacao|explicacao|descricao|oracao|suposicao|"
    r"numeros|particulas|saudacoes)(?![0-9A-Za-zÀ-ÿ])")
META = re.compile(r"(placeholder|Authored lesson|Authored (the |pré|N5|N4)|Polished|returned as structured|"
                  r"reference format|Fixed n[45]-|FIXED\.|matching the lesson)", re.I)
OPEN_PUNCT = set("([{「『“\"¿¡")
CLOSE_PUNCT = set(")]}」』”\",.;:!?…、。）")


def _latin(c: str) -> bool:
    return c.isalnum() and ord(c) < 0x3000


def _learner_text(d: dict) -> str:
    """Only learner-facing prose — NOT identifier fields (slug/topic/refs) or body tag-attributes."""
    parts = [str(d.get("title", "")), str(d.get("description", ""))]
    parts += [str(o) for o in d.get("objectives", [])]
    for ex in d.get("exercises", []):
        parts += [str(ex.get("prompt", "")), str(ex.get("explanation", ""))]
    # body: only text BETWEEN tags (skip ref="…" attributes which legitimately hold ASCII identifiers)
    parts += re.findall(r">([^<>]+)<", d.get("body", "") or "")
    return "\n".join(parts)


def check(d: dict, stem: str) -> list[str]:
    out: list[str] = []
    blob = _learner_text(d)
    if EMOJI.search(blob):
        out.append("emoji in text")
    if BS in blob:
        out.append("literal backslash")
    if "—" in blob:
        out.append("em dash (U+2014)")
    m = ACCENT_STRIPPED.search(blob)
    if m:
        out.append(f"accent-stripped word '{m.group(1)}'")
    body = d.get("body", "") or ""
    if EMPTY.search(body):
        out.append("empty inline tag")
    for mm in BOUNDARY.finditer(body):
        a, nx = mm.group(1), mm.group(4)
        if (_latin(a) or _latin(nx)) and a not in OPEN_PUNCT and nx not in CLOSE_PUNCT:
            out.append("run-together boundary")
            break
    for fld in ("title", "description", "body"):
        if META.search(str(d.get(fld, ""))):
            out.append(f"meta-leak in {fld}")
    # identifiers must be ASCII
    for key in ("slug", "topic"):
        if any(ord(c) > 127 for c in str(d.get(key, ""))):
            out.append(f"non-ASCII {key}")
    return out


def main() -> int:
    fails: list[str] = []
    n = 0
    for f in sorted(LESSON_DIR.glob("*.json")):
        n += 1
        d = json.loads(f.read_text(encoding="utf-8"))
        for issue in check(d, f.stem):
            fails.append(f"{d.get('slug', f.stem)}: {issue}")
    print(f"lesson-hygiene audit: {n} lessons checked")
    if fails:
        print(f"=== {len(fails)} FAIL ===")
        for x in fails[:50]:
            print(f"  FAIL {x}")
        return 1
    print("=== 0 FAIL — no emoji / backslash / em-dash / accent-stripping / empty-tags / run-together / meta-leak ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
