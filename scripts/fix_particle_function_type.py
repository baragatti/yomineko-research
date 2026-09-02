#!/usr/bin/env python3
"""Correct `function_type` on the particles where two independent signals agree it is wrong.

FOUND BY the role drill. `build_sentence_patterns.py` derives a chunk's grammatical role from the
(particle, function_type) pair, so a wrong function_type becomes a wrong drill question: the pronominal
の of そのコップは私のです was typed `case`, which made 私 "o MODIFICADOR (a parte ligada por の)" -- but
私の is not modifying anything there, it IS the predicate. Same for 夏は暑いが冬は寒い, where an
adversative が typed `case` made 夏 "o SUJEITO" of a が that marks no subject at all.

HOW THE FIFTEEN WERE FOUND, and why neither signal alone was allowed to decide.

  The authored pt-BR prose alone: 90 candidates, of which about 85 were the audit's own false positives.
  The で of 台風で and the に of 高さに驚いた do mark cause, and the prose says so -- but a cause-marking
  で/に is 格助詞, so `case` is right and the prose agreeing on "causa" is evidence of nothing.

  The token shape alone: no better. "の is a modifier iff a nominal follows it" drops 84 legitimate
  genitives to catch 5 pronominal の. "が is a subject iff a nominal precedes it" drops 51 legitimate
  subjects to catch 1 adversative. Ratios like that are not a rule, they are a coin flip with extra
  steps -- and both were rejected for exactly that reason before this script existed.

  Their INTERSECTION is precise, because the two fail independently: the prose is free text written per
  sentence by an authoring pass, the shape is mechanical and came from the tokenizer. Nothing makes them
  wrong in the same place. Every row below is one where the shape says a sense and a human writing about
  that exact particle in that exact sentence said the same sense.

WHAT IS CORRECTED (15 particles over 15 sentences):
  の  case -> nominalizer   6   pronominal/準体助詞 の -- 別のを, 私のです, あっちのより. Stands in for an
                                elided noun. `nominalizer` is the closest value the closed enum carries.
  に  case -> conjunctive   8   のに, concessive. A 接続助詞 joining two clauses, not a case marker.
  が  case -> conjunctive   1   adversative が -- 暑いが寒い. Joins clauses; marks no subject.

The enum is unchanged (case / conjunctive / sentence-final / adverbial / binding / nominalizer); this
only moves fifteen records to the value already defined for what they are.

Each edit is resolved on the PARSED row by particle id, never by text replacement -- は and に occur
thousands of times and a surface match would rewrite the bank. The DB is the working store and
corpus/sentences/bank.json is exported from it, so run the exporter afterwards (the script says so).

Usage: fix_particle_function_type.py [--apply]
"""
from __future__ import annotations
import argparse, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
NOMINAL = {"名詞", "代名詞", "数詞", "接尾辞"}

# particle, current ft, prose MUST say, prose must NOT say, shape test, corrected ft
CASES = [
    ("の", "case", ("nominaliz", "substitui", "pronome"), (), "no-nominal-after", "nominalizer"),
    ("が", "case", ("adversativ", "concessiv"), ("sujeito",), "no-nominal-before", "conjunctive"),
    ("から", "case", ("causa", "porque", "motivo", "razão"), ("origem", "partida"),
     "no-nominal-before", "conjunctive"),
    ("に", "case", ("concessiv",), (), "preceded-by-no", "conjunctive"),
]


def find(con: sqlite3.Connection) -> list[dict]:
    hits, toks = [], {}
    for part, ft, need, avoid, shape, fixed in CASES:
        rows = con.execute(
            "SELECT p.id, s.slug, s.jp, t.position, t.sentence_id, l.value FROM particle p "
            "JOIN token t ON t.id=p.token_id JOIN sentence s ON s.id=p.sentence_id "
            "JOIN localized_text l ON l.entity_type='particle' AND l.entity_id=p.id "
            "AND l.field='function' AND l.locale='pt-BR' WHERE p.particle=? AND p.function_type=?",
            (part, ft)).fetchall()
        for pid, slug, jp, pos, sid, lab in rows:
            low = (lab or "").lower()
            if not any(n in low for n in need) or any(a in low for a in avoid):
                continue                                    # prose signal absent
            if sid not in toks:
                toks[sid] = con.execute(
                    "SELECT position,surface,pos_coarse FROM token WHERE sentence_id=? AND "
                    "split_mode='C' ORDER BY position", (sid,)).fetchall()
            ts = toks[sid]
            after = next((t for t in ts if t[0] > pos and t[2] != "補助記号"), None)
            before = next((t for t in reversed(ts) if t[0] < pos and t[2] != "補助記号"), None)
            if shape == "no-nominal-after" and (after is None or after[2] in NOMINAL):
                continue                                    # shape signal absent
            if shape == "no-nominal-before" and (before is None or before[2] in NOMINAL):
                continue
            if shape == "preceded-by-no" and (before is None or before[1] != "の"):
                continue
            hits.append({"id": pid, "slug": slug, "jp": jp, "particle": part,
                         "was": ft, "now": fixed, "prose": lab})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    hits = find(con)

    stats = Counter(f"{h['particle']} {h['was']} -> {h['now']}" for h in hits)
    for h in hits:
        print(f"  {h['particle']}  {h['was']} -> {h['now']}   {h['jp']}")
        print(f"      {h['prose']}")
    print(f"\n{len(hits)} particles: " + "  ".join(f"{k} ({v})" for k, v in stats.most_common()))

    if not args.apply:
        print("\npre-flight only. re-run with --apply to write.")
        return 0
    for h in hits:
        # by particle id. A surface match would rewrite thousands of unrelated に and が.
        con.execute("UPDATE particle SET function_type=? WHERE id=?", (h["now"], h["id"]))
    con.commit()
    left = find(con)
    print(f"\napplied {len(hits)}; re-scan now finds {len(left)}")
    print("NEXT: scripts/export/export_corpus.py, then rebuild patterns + role drills.")
    con.close()
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
