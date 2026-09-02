#!/usr/bin/env python3
"""Strip corpus-build metadata out of learner-facing sentence explanations (confirmed Phase-3 class).

The authoring pass left notes about WHY a sentence was included inside `structure_explanation`, which the
learner reads: "Target is N4 coverage.", "O alvo é cobertura N4.", "Being N4 coverage only, no specific
grammar point to validate." QA confirmed this class repeatedly; it affects 472 fields (231 en / 241 pt-BR),
far more than the 112 that happened to be inside the sentence patch.

The occurrences come in TWO shapes and must NOT be treated alike:

  DROP  — the whole sentence is build/QA speak and carries no teaching content:
          "Target is N4 coverage."  /  "O alvo é cobertura N4."
          "Being N4 coverage only, no specific grammar point to validate."
  TRIM  — the metadata is a parenthetical inside a sentence that DOES teach something; only the
          parenthetical goes, the sentence stays:
          "Focus (N4 coverage) is the compound 集め始めた: the ren'youkei of 集める joins 始める..."
       -> "Focus is the compound 集め始めた: the ren'youkei of 集める joins 始める..."

Blindly deleting every sentence containing "coverage" would destroy real grammar explanations; blindly
deleting the word alone would leave "Target is ." fragments. So each occurrence is classified, and anything
that does not clearly fall into DROP or TRIM is left alone and reported for review.

Emits research/derived/fable5_validation/phase3_metadata_strip.json (a patch, in the same op shape as the
sentence pipeline) plus a full before/after listing. Applies nothing. Usage:
  fable5_strip_build_metadata.py [--show N]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"

META = re.compile(r"\b(coverage|cobertura)\b", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
# a parenthetical that is purely a level/coverage tag: "(N4 coverage)", "(cobertura N4)", "(coverage)"
PAREN = re.compile(r"\s*\((?:[Nn][1-5]\s+)?(?:coverage|cobertura)(?:\s+[Nn][1-5])?\)", re.I)
# a whole sentence whose only job is declaring the record's purpose / QA status
DROP_SENT = re.compile(
    r"^(the\s+)?target\s+(here\s+)?is\b.*\b(coverage|cobertura)\b|"
    r"^o\s+alvo\s+(aqui\s+)?é\b.*\b(coverage|cobertura)\b|"
    r"^being\b.*\b(coverage|cobertura)\b.*\bno specific grammar\b|"
    r"^(sendo|é)\b.*\b(coverage|cobertura)\b.*\bnenhum ponto\b|"
    r"^\s*(target|alvo)\b[^.]*\b(coverage|cobertura)\b[^.]*$|"
    # 'focus/foco' framing: same build note, different wording
    r"^(the\s+)?focus\s+is\s+(just\s+|only\s+|merely\s+)?(the\s+)?(coverage|cobertura)\b[^:]*$|"
    r"^o\s+foco\s+é\s+(apenas\s+|só\s+)?(a\s+)?(coverage|cobertura)\b[^:]*$",
    re.I)
# The metadata word sometimes only QUALIFIES a sentence that does teach something. Demote it in place
# rather than deleting the sentence: "a coverage sentence focused on X" still explains X.
DEMOTE = [
    (re.compile(r"\b(a|the)\s+coverage\s+sentence\b", re.I), r"\1 sentence"),
    (re.compile(r"\bthe\s+coverage\s+focus\b", re.I), "the focus"),
    (re.compile(r"\bcoverage\s+focus\b", re.I), "focus"),
    (re.compile(r"\b(uma|a)\s+frase\s+de\s+cobertura\b", re.I), r"\1 frase"),
    (re.compile(r"\bsó\s+cobertura\s*\(coverage\)\s*(do|da|de)\b", re.I), r"\1"),
    (re.compile(r"\b(apenas|só)\s+(a\s+)?cobertura\s+(do|da|de)\b", re.I), r"\3"),
]


def clean(text: str):
    """Return (new_text, actions) or (text, []) when nothing safe to do."""
    parts = SENT_SPLIT.split(text)
    out, actions = [], []
    for p in parts:
        s = p.strip()
        if not s:
            continue
        if not META.search(s):
            out.append(s)
            continue
        if DROP_SENT.match(s):
            # A purpose sentence often CARRIES teaching content after a colon:
            #   "O alvo é cobertura de vocabulário N4: 事故を起こした é a expressão fixa 'causar um acidente'."
            # Dropping it whole would delete that explanation, so keep the substantive tail.
            head, sep, tail = s.partition(":")
            if sep and len(tail.strip()) > 20 and not META.search(tail):
                tail = tail.strip()
                tail = tail[0].upper() + tail[1:] if tail[:1].isalpha() else tail
                out.append(tail)
                actions.append(("trim_prefix", s))
                continue
            actions.append(("drop", s))
            continue
        trimmed = PAREN.sub("", s)
        if trimmed != s and not META.search(trimmed):
            # the sentence still teaches something once the tag is gone
            trimmed = re.sub(r"\s{2,}", " ", trimmed).strip()
            if len(trimmed) > 12:
                out.append(trimmed)
                actions.append(("trim", s))
                continue
        demoted = s
        for rx, rep in DEMOTE:
            demoted = rx.sub(rep, demoted)
        if demoted != s and not META.search(demoted):
            demoted = re.sub(r"\s{2,}", " ", demoted).strip()
            out.append(demoted)
            actions.append(("demote", s))
            continue
        actions.append(("review", s))   # unclassified - keep the sentence untouched
        out.append(s)
    return " ".join(out).strip(), actions


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", type=int, default=6)
    args = ap.parse_args()
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    slug_of = {sid: slug for sid, slug in con.execute("SELECT id, slug FROM sentence")}

    by_slug, samples, stats = {}, [], Counter()
    for eid, field, locale, value in con.execute(
            "SELECT entity_id, field, locale, value FROM localized_text "
            "WHERE entity_type='sentence' AND field='structure_explanation'"):
        if not value or not META.search(value):
            continue
        new, actions = clean(value)
        stats.update(a for a, _ in actions)
        if not actions or new == value:
            continue
        if META.search(new):
            stats["still_dirty"] += 1
        if len(new) < 25:                      # never leave an explanation gutted
            stats["skipped_too_short"] += 1
            continue
        by_slug.setdefault(slug_of[eid], []).append(
            {"mode": "replace", "path": ["structure_explanation", locale], "current": value, "fix": new,
             "field": f"structure_explanation.{locale}", "severity": "major",
             "issue": "corpus-build metadata in learner-facing explanation"})
        if len(samples) < args.show:
            samples.append({"slug": slug_of[eid], "locale": locale, "before": value, "after": new})
    con.close()

    (FD / "phase3_metadata_strip.json").write_text(json.dumps(
        {"note": "Deterministic removal of build metadata from structure_explanation. DROP = whole "
                 "purpose/QA sentence; TRIM = level tag parenthetical only, teaching content kept. "
                 "Occurrences that fit neither are left untouched and counted as 'review'.",
         "stats": dict(stats),
         "sentences": [{"slug": s, "ops": ops} for s, ops in sorted(by_slug.items())]},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"metadata strip: {sum(len(v) for v in by_slug.values())} field edits over {len(by_slug)} sentences")
    print("actions:", dict(stats))
    for s in samples:
        print(f"\n--- {s['slug']} [{s['locale']}]\n  BEFORE: {s['before'][:150]}\n  AFTER : {s['after'][:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
