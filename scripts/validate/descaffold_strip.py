#!/usr/bin/env python3
"""TIER-1 deterministic de-scaffolder (translation_qa.md §0.1 feedback loop). Removes the regular, safely-
deletable internal-scaffolding annotations that the generator wove into learner-facing prose, leaving natural
grammatical text. Operates on localized_text prose fields (sentence.structure_explanation, particle.explanation,
token.role) in BOTH pt-BR and en. Only removes PARENTHETICAL metadata whose content is itself an artifact, and
the inline ", candidato …" / quoted 'target' tells — never touches legitimate parentheticals (e.g. "('fazer')",
"(passado de いる)"). The harder WOVEN cases (do candidato gp-44:, bare sentence-IDs, corruption) are left for
the grounded rewrite pass. Idempotent. Usage: descaffold_strip.py [--apply]"""
from __future__ import annotations
import re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
FIELDS = [("sentence", "structure_explanation"), ("particle", "explanation"), ("token", "role")]

# parenthetical whose CONTENT begins with an artifact token -> delete the whole parenthetical
PAREN = re.compile(
    r"\s*[（(]\s*(?:target\b[^)）]*|gp-\d+|candidat[oae]s?\b[^)）]*|posi[çc][ãa]o\s*\d+|位置\s*\d+|jec)\s*[)）]",
    re.I)
# inline ", candidato gp-NN" / ", target …" tucked inside another (legit) parenthetical
INLINE = re.compile(r"\s*,\s*candidat[oae]s?\b[^,)）]*", re.I)
# quoted 'target' / "target" as a bare word
QUOTED = re.compile(r"['\"”’]\s*target\s*['\"“‘]", re.I)
LEAK = re.compile(r"gp-\d+|candidat[oae]s?\b|candidate\b|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])"
                  r"|\btarget\b|\bjec\b|位置\s*\d|posi[çc][ãa]o\s*\d", re.I)


def _alvo(m: "re.Match[str]") -> str:
    w = m.group(0)
    return "Alvo" if w[:1].isupper() else "alvo"


def clean(s: str, loc: str = "pt-BR") -> str:
    s = PAREN.sub("", s)
    s = INLINE.sub("", s)
    s = QUOTED.sub("", s)
    if loc == "pt-BR":
        # in pt-BR prose the bare English word "target" is a leak -> "alvo" (in en it is legitimate English)
        s = re.sub(r"\btarget\b", _alvo, s)
    s = re.sub(r"[（(]\s*[)）]", "", s)           # empty parens left behind
    s = re.sub(r"\s{2,}", " ", s)                # collapse double spaces
    s = re.sub(r"\s+([,.;:!?）)])", r"\1", s)     # space before punctuation
    s = re.sub(r"([（(])\s+", r"\1", s)           # space after open paren
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main() -> int:
    apply = "--apply" in sys.argv
    con = sqlite3.connect(DB)
    changed = still = 0
    examples = []
    for et, field in FIELDS:
        for loc in ("pt-BR", "en"):
            for eid, v in con.execute(
                    "SELECT entity_id, value FROM localized_text WHERE entity_type=? AND field=? AND locale=?",
                    (et, field, loc)).fetchall():
                if not v:
                    continue
                nv = clean(v, loc)
                if nv != v:
                    changed += 1
                    if LEAK.search(nv):
                        still += 1
                    elif len(examples) < 6 and loc == "pt-BR":
                        examples.append((eid, v, nv))
                    if apply:
                        con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? "
                                    "AND field=? AND locale=?", (nv, et, eid, field, loc))
    if apply:
        con.commit()
    print(f"descaffold-strip ({'applied' if apply else 'dry-run'}): changed {changed} field-values; "
          f"{still} STILL contain a woven artifact (-> grounded rewrite)")
    for eid, a, b in examples:
        print(f"  e{eid}\n    -  {a[:120]}\n    +  {b[:120]}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
