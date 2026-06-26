#!/usr/bin/env python3
"""Flag literal-mirror translations + AI-tell prose across ALL learner-facing pt-BR fields, so the
humanizer/fix pass targets only what needs it (translation_qa.md §3.3, §0.1). Cheap, deterministic, no AI.

Two tell families, applied to the right fields:
  * LITERAL-MIRROR — only on NATURAL translation fields (sentence.translation): catches the は=「quanto a mim」
    calque etc. ("私は学生です" -> "Quanto a mim, sou estudante" instead of "Eu sou estudante"). The literal
    mirror is CORRECT in `translation_literal`, so that field is exempt.
  * AI-TELL / non-human prose — on essay/explanation fields (grammar, sentence structure_explanation, particle
    explanation, lesson body, exercise prompt/explanation, families, token role/gloss/conjugation_note).
Word-list fields (kanji meanings, vocab gloss) are correctness-checked elsewhere (ground-truth), not here.
Writes reports/ai_tells.md for triage. Usage: detect_ai_tells.py [--sample N]
"""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
REPORT = ROOT / "reports" / "ai_tells.md"

# Literal-mirror tells — apply ONLY to natural-translation fields. High precision (these are almost always the
# JP-particle calque, not natural pt-BR).
# NOTE: these are CANDIDATE scopers for the AI/human naturalness audit, not auto-fix triggers — "quanto a X"
# can legitimately translate explicit について/に関して ("about/regarding X"). The dropped `pronoun-comma`
# pattern false-positived on natural pt-BR appositives ("Ela, naturalmente, ..."); a natural translation
# is detected by the AI audit, not a regex. Keep only the high-precision sentence-initial topic calques.
LITERAL = {
    "quanto-a-inicial (wa-calque)": re.compile(r"^\s*quanto a (mim|voc[êe]|ti|ele|ela|n[óo]s)\b", re.I),
    "no-que-diz-respeito (wa-calque)": re.compile(r"^\s*no que diz respeito a\b", re.I),
    "falando-de (topic calque)": re.compile(r"^\s*(falando (de|sobre)|em rela[çc][ãa]o a (mim|voc[êe]|ele|ela))\b", re.I),
    # authoring artifacts: a finished translation must commit to ONE rendering, not show alternatives
    "slash-alternative": re.compile(r"\S\s+/\s+\S"),
    "parenthetical-alt": re.compile(r"\((ou |isto é|i\.e\.|do tipo |a saber)", re.I),
}
# AI-tell / non-human prose tells — apply to essay/explanation fields. NOTE: on a JLPT grammar corpus,
# "em outras palavras/em resumo" (= the grammar point つまり) and "não só A, mas também B" (= 〜だけでなく/〜も)
# are legitimate TAUGHT CONTENT, not essay-filler — they were ~100% false positives, so they are NOT included
# here. Keep only genuine AI-filler/hedge patterns that have no business in pedagogical prose.
PROSE = {
    "vale-ressaltar": re.compile(r"vale (a pena )?(ressaltar|destacar|mencionar|notar|lembrar)", re.I),
    "e-importante-notar": re.compile(r"é (importante|interessante) (notar|ressaltar|lembrar|destacar|observar)", re.I),
    "por-um-lado": re.compile(r"\bpor um lado\b[^.]*\bpor outro( lado)?\b", re.I),
    "plays-role": re.compile(r"desempenha (um )?papel", re.I),
    "emdash-overuse": re.compile(r"—.*—"),
    "rich-tapestry": re.compile(r"\b(rica tapeçaria|um mundo de|verdadeira (joia|riqueza))\b", re.I),
}

NATURAL_TRANS = {("sentence", "translation")}
EXEMPT = {("sentence", "translation_literal")}          # literal by design — never flag
PROSE_FIELDS = {
    ("sentence", "structure_explanation"), ("particle", "explanation"),
    ("grammar_point", "explanation"), ("grammar_point", "nuance"), ("grammar_point", "formation"),
    ("grammar_point", "label"), ("family", "governing_rule"), ("family", "label"),
    ("token", "role"), ("token", "gloss"), ("token", "conjugation_note"),
    ("lesson", "body"), ("lesson", "objectives"), ("exercise", "prompt"), ("exercise", "explanation"),
}
TAG_TEXT = re.compile(r">([^<>]+)<")


def textof(field: str, val) -> str:
    if isinstance(val, list):
        val = " ".join(str(x) for x in val)
    if not isinstance(val, str):
        return ""
    if field in ("body",):  # XML-ish lesson body -> text between tags only
        segs = TAG_TEXT.findall(val)
        return " ".join(segs) if segs else val
    return val


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=10)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    flagged: dict = {}            # (et, field, eid) -> [tells]
    counts = Counter()
    by_field = Counter()
    for et, eid, field, val in con.execute(
            "SELECT entity_type, entity_id, field, value FROM localized_text "
            "WHERE locale='pt-BR' AND value IS NOT NULL AND value!=''"):
        key2 = (et, field)
        if key2 in EXEMPT:
            continue
        is_natural = key2 in NATURAL_TRANS
        is_prose = key2 in PROSE_FIELDS
        if not (is_natural or is_prose):
            continue
        text = textof(field, val)
        if not text:
            continue
        hits = []
        if is_natural:
            for name, rx in LITERAL.items():
                if rx.search(text):
                    hits.append(name)
        if is_prose:
            for name, rx in PROSE.items():
                if rx.search(text):
                    hits.append(name)
        if hits:
            flagged[(et, field, eid)] = hits
            by_field[f"{et}.{field}"] += 1
            for h in hits:
                counts[h] += 1
    # report
    lines = ["# AI-tell / literal-mirror report", "",
             f"Flagged **{len(flagged)}** pt-BR fields.", "",
             "## By tell", ""]
    for name, n in counts.most_common():
        lines.append(f"- `{name}` — {n}")
    lines += ["", "## By field", ""]
    for f, n in by_field.most_common():
        lines.append(f"- {f} — {n}")
    lines += ["", "## Samples", ""]
    samples = defaultdict(list)
    for (et, field, eid), tells in flagged.items():
        if len(samples[tuple(sorted(tells))]) < 3:
            v = con.execute("SELECT value FROM localized_text WHERE entity_type=? AND entity_id=? AND field=? "
                            "AND locale='pt-BR'", (et, eid, field)).fetchone()[0]
            samples[tuple(sorted(tells))].append(f"  - {et}/{field}#{eid} {list(tells)}: {textof(field, v)[:160]}")
    for tells, exs in samples.items():
        lines += exs
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"flagged {len(flagged)} pt-BR fields")
    print("by tell:", dict(counts.most_common()))
    print("by field:", dict(by_field.most_common()))
    print(f"report -> {REPORT.relative_to(ROOT)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
