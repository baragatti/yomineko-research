#!/usr/bin/env python3
"""DEPRECATED — superseded by scripts/validate/audit_hygiene_all_locales.py.

Use audit_hygiene_all_locales.py instead. It is a strict superset of this file: every rule below is
ported there, and the three holes the 13-panel review found in this one are closed.

  * WRONG TREE (F5). This file reads research/derived/lessons/*.json — the ingest SEED that
    load_lessons.py re-authors the DB from — not course/*/topic-*/lesson-*.json, which is what
    contracts/manifest.json calls a lesson and what the app renders. 259 of 322 bodies differed, and
    the gated copy was the damaged one: the seven lessons whose QA-reviewer instructions had leaked
    into title/description/objectives were still corrupt here while this gate printed "0 FAIL".
  * LESSONS ONLY (F6). Speak units, topics, courses, grammar, kanji, vocab, readings, families, the
    exam banks and the sentence bank were checked by nothing — 72 em dashes were live in speak-unit
    pt-BR titles alone.
  * FIXED WORD LIST (F7). The ACCENT_STRIPPED regex below is 30 hand-written words. The replacement
    derives its lexicon from the corpus (any word the corpus writes with ã/õ at least three times has
    a wrong plain spelling), which catches the 42 live cases this list never knew: reuniao, amanha,
    memorizacao, comissao, portao, conexoes, irmao, compaixao, opiniao, padrao, questao, verao…

The replacement additionally checks mojibake, Cyrillic/Greek mixed script, pt-PT vocabulary,
QA-reviewer instruction leaks, duplicated clauses and unbalanced parentheses, and it accepts --root so
it can be pointed at a mutated copy of the tree.

Original docstring follows.
---------------------------------------------------------------------------------------------------
P8 — enforce the standing lesson-hygiene rules (design/quality_rubric.md §P8) as a committed validator.

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
        if not ((_latin(a) or _latin(nx)) and a not in OPEN_PUNCT and nx not in CLOSE_PUNCT):
            continue
        # INTRA-WORD EMPHASIS is not a lost space. The kana lessons bold the first letter of a mnemonic
        # word ("Imagine um <b>a</b>nzol", "<b>ne</b>ne"), which necessarily joins two latin runs with no
        # space. The defect this check exists for is a space lost BETWEEN words; a styling tag that opens
        # or closes mid-word is the intended rendering, and the pre-fix alternative rendered "um a nzol".
        # the styling marker sits on the tag that OPENED this run, i.e. behind mm.start()
        before = body[:mm.start()]
        last_open = max(before.rfind("<text"), before.rfind("<emphasis"))
        open_tag = before[last_open:before.find(">", last_open) + 1] if last_open >= 0 else ""
        styled = 'weight="bold"' in open_tag or open_tag.startswith("<emphasis")             or 'weight="bold"' in mm.group(3) or mm.group(3).startswith("<emphasis")
        if styled and _latin(a) and _latin(nx):
            continue
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
