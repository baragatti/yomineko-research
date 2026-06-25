#!/usr/bin/env python3
"""Build the verb/adjective CONJUGATION BANK (corpus/conjugations/) — deterministic, Layer A.

For every conjugable vocab item (godan/ichidan/する/来る verbs; い/な adjectives) generates the standard
conjugation set (dictionary, masu*, te, past, negative, potential, passive, causative, volitional,
imperative, conditional…) with surface+kana+romaji. This is the source for conjugation drills/exercises.
Idempotent. Run with venv python after vocab is loaded.
"""
from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from conjugate import conjugate_verb, conjugate_adjective, VERB_FORMS, ADJ_FORMS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "corpus" / "conjugations"
LEVELS = ["n5", "n4", "n3"]


def main() -> int:
    con = sqlite3.connect(DB)
    counts = {}
    index_rows = []
    for lvl in LEVELS:
        records = []
        for vid, slug, hw, kana, vclass, aclass, lex in con.execute(
                "SELECT id,slug,headword,kana,verb_class,adj_class,lexeme_type FROM vocab "
                "WHERE level=? AND (verb_class IS NOT NULL OR adj_class IS NOT NULL) ORDER BY headword",
                (lvl,)):
            if vclass:
                forms = conjugate_verb(hw, kana, vclass)
                kind, order = "verb", VERB_FORMS
            elif aclass:
                forms = conjugate_adjective(hw, kana, aclass)
                kind, order = "adjective", ADJ_FORMS
            else:
                continue
            if not forms:
                continue
            records.append({
                "vocab_id": vid, "slug": slug, "headword": hw, "kana": kana, "level": lvl,
                "kind": kind, "class": vclass or aclass,
                "conjugations": [{"form": k, **forms[k]} for k in order if k in forms],
            })
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{lvl}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        counts[lvl] = len(records)
        index_rows.append((lvl, len(records), sum(1 for r in records if r["kind"] == "verb"),
                           sum(1 for r in records if r["kind"] == "adjective")))
    lines = ["# Corpus — Conjugation bank (deterministic, Layer A)", "",
             f"_Generated {_dt.date.today().isoformat()}. Rule-based conjugations for the exercise bank; "
             f"each form has surface/kana/romaji. Form keys are neutral enums._", "",
             "| level | items | verbs | adjectives |", "|-------|------:|------:|-----------:|"]
    for lvl, n, nv, na in index_rows:
        lines.append(f"| {lvl} | {n} | {nv} | {na} |")
    lines += ["", "**Verb forms:** " + ", ".join(f"`{x}`" for x in VERB_FORMS),
              "", "**Adjective forms:** " + ", ".join(f"`{x}`" for x in ADJ_FORMS)]
    (OUT / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    con.close()
    print(f"conjugation bank: {counts} -> corpus/conjugations/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
