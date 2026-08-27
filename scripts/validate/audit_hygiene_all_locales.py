#!/usr/bin/env python3
"""Prose-hygiene gate over EVERY learner-facing string in the published corpus and courseware.

WHY THIS FILE EXISTS
--------------------
The suite's only prose-hygiene gate used to be audit_lesson_hygiene.py, and the 13-panel review found
three independent holes in it (findings F5/F6/F7 plus the content-leaks sweep):

  F5  it read research/derived/lessons/*.json — the ingest SEED — not the shipped course leaves that
      contracts/manifest.json calls a lesson. 259 of 322 bodies differed, and the gated copy was
      provably the *damaged* one: the seven lessons whose QA-reviewer instructions had leaked into
      title/description/objectives were still corrupt there while the gate reported "0 FAIL".
  F6  it covered lessons only. 72 em dashes were shipping in speak-unit pt-BR titles and 3 more in
      grammar structure_pattern, against design/translation_style.md's blanket ban. Speak units,
      topics, exam banks, grammar, kanji, vocab and the sentence bank were checked by nothing.
  F7  its accent rule was a hard-coded 30-word regex. It knew `nao` and `licao` but not `reuniao`,
      `amanha`, `memorizacao`, `comissao`, `portao`, `conexoes`, `irmao`, `compaixao`, `opiniao`,
      `padrao`, `questao` or `verao` — 42 accent-stripped words were live in learner prose.

The content-leaks audit added a fourth class: QA-reviewer instructions pasted verbatim into the field
they were written to correct ("Rewrite as learner-facing prose…", 'prompt: "…" AND answer.full: "…"',
"(and update tokens[5].ro from 'ichirei' to 'jup')"), reaching bank.json, corpus/readings, grammar and
live N5/N3 lessons through four separate "apply the QA findings" commits — plus duplicated leading
clauses in grammar explanations and parentheses left unclosed by a truncating applier.

So this validator walks corpus/ + course/ instead of one directory, derives its accent lexicon from the
corpus instead of hard-coding one, and checks the leak/mojibake/duplication classes the old file never
had. It REPLACES audit_lesson_hygiene.py, whose still-valid lesson rules (emoji, backslash, em dash,
empty inline wrappers, run-together tag boundaries, meta-leak, ASCII identifiers) are ported here.

PRECISION
---------
Every detector below was tuned against a human-judged sweep of the live tree, and each exclusion is a
false positive that sweep actually produced — they are documented at their check, not silently applied.
The largest one: an accent lexicon must be built from ã/õ words only. Dropping a tilde never yields a
valid pt-BR word, but dropping a cedilla routinely does (faca/faça, forca/força, louca/louça), and
`maca` is a stretcher as well as a de-accented `maçã`.

Scope: pt-BR strings get every check; `en` strings get only the leak, mojibake and mixed-script checks,
because English is legal there. Reads the exported JSON only — never db/corpus.sqlite.

Exit 1 on any failure. Usage: audit_hygiene_all_locales.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------------------------------
# WHAT COUNTS AS LEARNER-FACING
# --------------------------------------------------------------------------------------------------
# A string is learner-facing if its json-path passes through a `pt-BR` (or `en`) locale key, or if its
# terminal key is one of the locale-less prose fields (lesson `body`, grammar `structure_pattern`).
LEARNER_KEYS = {
    "body", "title", "description", "prompt", "explanation", "label", "nuance", "note", "objectives",
    "gloss", "meaning", "formation", "structure_pattern", "role", "function", "translation",
    "structure_explanation",
}
# Identifier and Japanese-content keys. ASCII identifiers legitimately live in `ref`, romaji in `ro`,
# and the accent/em-dash rules are about pt-BR prose, not about 漢字 or slugs.
EXCLUDE_KEYS = {
    "id", "slug", "path", "ref", "key", "topic", "romaji", "ro", "reading", "kana", "jp", "en",
    "source", "lemma", "surface", "headword", "character", "form", "stem", "correct", "distractors",
    "answer", "pieces", "choices", "target", "wrong", "pattern",
}
# An identifier BY VALUE — 'les:n3-concessao-01', 'deck:grammar-n5', 'topic-07/lesson-01.json'. The
# namespace separator is required: without it a one-word learner-facing value such as the title
# "placeholder" would be waved through as an identifier, and that is precisely a meta-leak.
IDENT_VALUE = re.compile(r"^[A-Za-z0-9_:./#-]*[:/][A-Za-z0-9_:./#-]*$")
# corpus/strokes is stroke geometry (coordinates and SVG path data); it carries no prose at all and is
# 8.6 MB of it, so it is skipped for runtime rather than checked and always passing.
SKIP_DIRS = {"strokes"}

# --------------------------------------------------------------------------------------------------
# TAG HANDLING — bodies are marked-up, and the word rules must not see the markup
# --------------------------------------------------------------------------------------------------
ATTR = re.compile(r"\s[A-Za-z_][\w-]*=\"[^\"]*\"")
TAG = re.compile(r"<[^>]*>")
ROMAJI_SPAN = re.compile(r"<romaji\b[^>]*>.*?</romaji>", re.S)
# A parenthetical romaji gloss right after Japanese — '前に (mae ni)', '始める (hajimeru)'. `mae` is not a
# de-accented `mãe` here, it is the reading of 前. Only ASCII-only parentheticals are blanked, so a
# parenthetical containing real pt-BR prose stays under the accent rule.
ROMAJI_PAREN = re.compile(r"([぀-ヿ㐀-鿿])\s*[(（]([^)）]*)[)）]")


def prose(s: str) -> str:
    """Strip inline markup, tag attributes and <romaji> spans, leaving the text a learner reads."""
    return TAG.sub(" ", ATTR.sub(" ", ROMAJI_SPAN.sub(" ", s)))


def accent_text(s: str) -> str:
    def kill(m: re.Match[str]) -> str:
        return m.group(1) + " " if all(ord(c) < 128 for c in m.group(2)) else m.group(0)
    return ROMAJI_PAREN.sub(kill, prose(s))


WORD = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ]{2,}")


def deaccent(w: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", w) if not unicodedata.combining(c)).lower()


# --------------------------------------------------------------------------------------------------
# DETECTORS
# --------------------------------------------------------------------------------------------------
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF"
                   "\U00002B00-\U00002BFF\U0001F1E6-\U0001F1FF]")
# A pt-BR/en value is Latin+Japanese. A Cyrillic or Greek codepoint means a corrupted paste: the live
# example was '～にとтя' (U+0442 U+0442 U+044F) travelling inside a QA finding's own proposed fix.
MIXED_SCRIPT = re.compile("[Ͱ-ϿЀ-ԯἀ-῿]")
# U+FFFD plus the Latin-1 double-encoding signatures (Ã/Â + a continuation byte, â€).
MOJIBAKE = re.compile("\uFFFD|\u00C3[\u0080-\u00BF]|\u00E2\u20AC|\u00C2[\u00A0-\u00BF]")
EMPTY_TAG = re.compile(r"<(text|emphasis|romaji|term)(?:\s[^>]*)?></\1>")
BOUNDARY = re.compile(r"(\S)(</(?:text|emphasis|jp|romaji|term)>)"
                      r"((?:<(?:text|emphasis|jp|romaji|term)[^>]*>)"
                      r"|(?:<(?:grammar|vocab|kanji|break)\b[^>]*/>))(?=(\S))")
OPEN_PUNCT = set("([{「『“\"¿¡")
CLOSE_PUNCT = set(")]}」』”\",.;:!?…、。）")
# European-Portuguese vocabulary. 'estou a fim de' is perfectly good pt-BR, so the progressive marker
# requires an actual infinitive ('estou a comer'), which is the construction pt-BR does not use.
PT_PT = re.compile(r"(?i)\b(ecrã|autocarro|telemóvel|comboio|casa de banho|rapariga|utilizador|"
                   r"ficheiro|frigorífico|pequeno-almoço)\b"
                   r"|\b(estou|estás|está|estamos|estão) a (?!fim\b)[a-zà-ÿ]{2,}r\b")

# QA-reviewer instruction leaks. Each family is a signal the content-leaks audit confirmed by hand; the
# generic-English-imperative family is pt-BR-only because en explanations legitimately say "replace the
# final い with くても", and '(and also …)' was dropped from the parenthetical family for the same reason.
LEAK_FAMILIES: list[tuple[str, re.Pattern[str], str]] = [
    ("schema-field-name", re.compile(
        r"\b(gloss|expl|explanation|role|label|note|translation|conjugation_note|function|prompt|answer)"
        r"_(pt|en)\b"
        r"|\b(tokens|forms|exercises|particles|objectives|steps|options)\[\d+\]"
        r"|\bposition \d+ \w+_(pt|en)\b"
        r"|\banswer\.(full|text)\b"
        r"|\b(translation_literal|structure_explanation|structure_pattern|accepted_variants)\."
        r"|\b\w+\.(pt-BR|en)\s*(=|:)"), "both"),
    ("edit-order-parenthetical", re.compile(
        r"(?i)\((?:and|e)\s+(en|pt|lit|pt-BR|correspondingly|update|change|strip|drop|apply|fix|remove|"
        r"the parallel)\b|\(leave the\b|\(apply to\b|\(mesma correção"), "both"),
    ("repo-file-path", re.compile(
        r"\b(corpus|course|research|scripts|prototype|db|design|archive)/[\w./-]+"
        r"\.(json|md|py|ts|tsx|sqlite|mjs)\b"), "both"),
    ("locale-label-prefix", re.compile(
        r"^\s*(pt-BR|pt|en|lit|prompt|pattern|title|Title)\s*:\s*[\"'“]"), "both"),
    ("author-imperative", re.compile(
        r"(?:^|[.;:)\]\"'»]\s+)(Rewrite|Retitle|Replace|Drop|Keep|Apply|Fix|Strip|Update|Change|"
        r"Reduce|Do NOT|Do not|Use the|Restore|Revert|Delete)\b"), "pt"),
    ("reviewer-verdict", re.compile(
        r"(?i)\b(can stay|as authored|leave as is|no change needed|needs no change)\b"), "pt"),
    ("markup-in-plain-field", re.compile(
        r"<(heading|checklist|check|note|p|text|emphasis|jp|vocab|kanji|grammar|term|romaji|break"
        r"|list|item)\b"), "nonbody"),
]
# Orchestration chatter that reached title/description/body in earlier phases (ported verbatim).
META = re.compile(r"(?i)(placeholder|Authored lesson|Authored (the |pré|N5|N4)|Polished|"
                  r"returned as structured|reference format|Fixed n[45]-|FIXED\.|matching the lesson)")

# Real pt-BR words that are also the de-accented spelling of a nasal word in this corpus. Without them
# the lexicon rule fires on legitimate prose.
ACCENT_HOMOGRAPHS = {
    "maca", "macas",      # maca/macas = stretcher(s); also the de-accent of maçã/maçãs
    "manha", "manhas",    # manha = guile; also the de-accent of manhã/manhãs
    "crista", "cristas",  # crista = crest; also the de-accent of cristã/cristãs
}
# audit_lesson_hygiene.py's hand-written list. Kept as a floor so the corpus-derived lexicon can only
# ADD to what the old gate caught, never subtract (several of these carry no ã/õ at all).
LEGACY_ACCENT_WORDS = frozenset(
    "nao voce voces licao licoes acao acoes portugues tambem entao comeco familia consequencia "
    "vocabulario mnemonico duvida possivel topico particula reconheco conheco tres consciencia "
    "experiencia japones ingles alem porem conjugacao explicacao descricao oracao suposicao "
    "numeros particulas saudacoes".split())

DUP_WINDOW = 45   # chars; below ~40 parallel constructions ("ちゃ… vem de… / じゃ… vem de…") collide


def duplicated_clause(s: str, window: int = DUP_WINDOW) -> str:
    """Return a run of `window` chars that occurs twice, non-overlapping — a spliced-in clause."""
    t = " ".join(s.split())
    if len(t) < window * 2:
        return ""
    seen: dict[str, int] = {}
    for i in range(len(t) - window + 1):
        g = t[i:i + window]
        j = seen.get(g)
        if j is None:
            seen[g] = i
        elif i - j >= window:
            return g
    return ""


def paren_balance(s: str) -> str:
    """ASCII and full-width parens counted together — the corpus freely mixes （ with )."""
    depth = 0
    for ch in prose(s):
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
            if depth < 0:
                return "closing paren before any opening one"
    return f"{depth} unclosed paren(s)" if depth else ""


def run_together(body: str) -> bool:
    """A space lost between two words when an inline tag closed and the next opened.

    Intra-word emphasis is NOT that defect: the kana lessons bold the first letter of a mnemonic
    ("Imagine um <b>a</b>nzol"), which necessarily joins two Latin runs with no space.
    """
    for m in BOUNDARY.finditer(body):
        a, nxt = m.group(1), m.group(4)
        latin = lambda c: c.isalnum() and ord(c) < 0x3000  # noqa: E731
        if not ((latin(a) or latin(nxt)) and a not in OPEN_PUNCT and nxt not in CLOSE_PUNCT):
            continue
        before = body[:m.start()]
        last_open = max(before.rfind("<text"), before.rfind("<emphasis"))
        open_tag = before[last_open:before.find(">", last_open) + 1] if last_open >= 0 else ""
        styled = ('weight="bold"' in open_tag or open_tag.startswith("<emphasis")
                  or 'weight="bold"' in m.group(3) or m.group(3).startswith("<emphasis"))
        if styled and latin(a) and latin(nxt):
            continue
        return True
    return False


# --------------------------------------------------------------------------------------------------
# `field` is the SEMANTIC field name, which is not the terminal json key: the value of a lesson title
# sits at title/pt-BR, so the terminal key is the locale tag and the field is `title`. Every rule that
# names a field (the META rule, the readings-translation carve-out, "body") needs the latter.
Row = tuple[str, str, str, str, str]  # (file, json-path, field, locale, value)


def collect(root: Path) -> tuple[list[Row], int]:
    files = [p for p in sorted(list(root.glob("corpus/**/*.json")) + list(root.glob("course/**/*.json")))
             if not SKIP_DIRS & set(p.parts)]
    rows: list[Row] = []

    def walk(node: object, path: str, field: str, rel: str, in_pt: bool, in_en: bool) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                sub = field if k in ("pt-BR", "en") else k
                walk(v, f"{path}/{k}", sub, rel, in_pt or k == "pt-BR", in_en or k == "en")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]", field, rel, in_pt, in_en)
        elif isinstance(node, str) and node:
            if in_pt:
                locale = "pt-BR"
            elif in_en:
                locale = "en"
            elif field in EXCLUDE_KEYS or field not in LEARNER_KEYS:
                return
            else:
                locale = "pt-BR"
            if IDENT_VALUE.match(node):
                return
            rows.append((rel, path, field, locale, node))

    for f in files:
        rel = str(f.relative_to(root)).replace("\\", "/")
        walk(json.loads(f.read_text(encoding="utf-8")), "", "", rel, False, False)
    return rows, len(files)


def build_accent_lexicon(rows: list[Row]) -> set[str]:
    """Words the corpus itself writes with ã/õ at least 3 times; their plain spelling is then wrong.

    ã/õ ONLY, deliberately. A word this corpus writes with ç is not safe to flag de-accented: faca,
    forca, louca, caco, peca and maca are all real pt-BR words in their own right.
    """
    nasal: collections.Counter[str] = collections.Counter()
    for _f, _p, _k, locale, s in rows:
        if locale != "pt-BR":
            continue
        for m in WORD.finditer(prose(s)):
            w = m.group(0).lower()
            if "ã" in w or "õ" in w:
                nasal[w] += 1
    derived = {deaccent(w) for w, n in nasal.items() if n >= 3 and deaccent(w) != w}
    return (derived - ACCENT_HOMOGRAPHS) | set(LEGACY_ACCENT_WORDS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    rows, n_files = collect(root)
    if not n_files:
        # A validator that silently passes on an empty tree is not a validator.
        print(f"hygiene (all locales): FAIL — no corpus/ or course/ JSON found under {root}")
        return 1
    bad_words = build_accent_lexicon(rows)

    fails: list[tuple[str, str]] = []          # (check, message)
    per_check: collections.Counter[str] = collections.Counter()

    def fail(check: str, rel: str, path: str, detail: str, value: str) -> None:
        per_check[check] += 1
        snippet = " ".join(value.split())[:90]
        fails.append((check, f"{check}: {rel}{path or '/'} [{detail}] :: {snippet}"))

    for rel, path, field, locale, s in rows:
        # ---- both locales: leaks, mojibake, mixed script ------------------------------------------
        for name, rx, scope in LEAK_FAMILIES:
            if scope == "pt" and locale != "pt-BR":
                continue
            if scope == "nonbody" and field == "body":
                continue
            m = rx.search(s)
            if m:
                fail(f"qa-leak/{name}", rel, path, m.group(0).strip()[:40], s)
        if field in ("title", "description", "body") and META.search(s):
            fail("meta-leak", rel, path, META.search(s).group(0), s)
        m = MIXED_SCRIPT.search(s)
        if m:
            fail("mixed-script", rel, path, f"U+{ord(m.group(0)):04X} {m.group(0)}", s)
        if MOJIBAKE.search(s):
            fail("mojibake", rel, path, "encoding damage", s)
        m = EMOJI.search(s)
        if m:
            fail("emoji", rel, path, m.group(0), s)

        if locale != "pt-BR":
            continue

        # ---- pt-BR only ---------------------------------------------------------------------------
        if "—" in s:
            fail("em-dash", rel, path, "U+2014", s)
        if "\\" in s:
            fail("backslash", rel, path, "literal backslash", s)
        m = PT_PT.search(s)
        if m:
            fail("pt-PT", rel, path, m.group(0).strip(), s)
        for m in WORD.finditer(accent_text(s)):
            w = m.group(0).lower()
            if w == deaccent(w) and w in bad_words:
                fail("accent-stripped", rel, path, w, s)
                break
        b = paren_balance(s)
        if b:
            fail("unbalanced-parens", rel, path, b, s)

        if field == "body":
            m = EMPTY_TAG.search(s)
            if m:
                fail("empty-inline-tag", rel, path, m.group(0), s)
            if run_together(s):
                fail("run-together-boundary", rel, path, "lost space at tag boundary", s)
            # Bodies are exempt from the duplicated-clause rule: every lesson body ends with a
            # <checklist> that deliberately restates the objectives and the prose above it.
            continue
        # corpus/readings translations concatenate one pt-BR sentence per passage sentence, and the
        # passages themselves contain near-identical source sentences on purpose
        # (read:n3-concessao-02-01 pairs 「何の話してるの？」with「何を話してるの？」).
        if rel.startswith("corpus/readings/") and field == "translation":
            continue
        dup = duplicated_clause(s)
        if dup:
            fail("duplicated-clause", rel, path, f"repeats {dup[:40]!r}", s)

    n_pt = sum(1 for r in rows if r[3] == "pt-BR")
    print(f"hygiene (all locales): {n_files} files, {len(rows)} learner-facing strings "
          f"({n_pt} pt-BR, {len(rows) - n_pt} en), accent lexicon {len(bad_words)} words")
    if fails:
        print(f"=== {len(fails)} FAIL ===")
        for _check, msg in (fails if args.list else fails[:15]):
            print(f"  FAIL {msg}")
        if not args.list and len(fails) > 15:
            print(f"  ... {len(fails) - 15} more (use --list)")
        print("  by check: " + ", ".join(f"{k}={v}" for k, v in sorted(per_check.items())))
        return 1
    print("=== 0 FAIL — no em dash / emoji / mojibake / mixed script / QA-instruction leak / "
          "accent-stripping / pt-PT / duplicated clause / unbalanced parens ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
