#!/usr/bin/env python3
"""Flag AI-tell patterns in authored pt-BR prose so the humanizer pass targets only what needs it.

Scans localized_text for the essay-like fields (sentence structure_explanation, token gloss/role,
particle function/explanation) and reports which entities trip common pt-BR AI-writing tells. Cheap,
deterministic, no AI — used to scope the humanizer workflow (fix the flagged subset, not everything).
"""
from __future__ import annotations

import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"

TELLS = {
    "quanto-a-mim-translation": re.compile(r"^\s*quanto a (mim|isso|ele|ela)", re.I),
    "vale-ressaltar": re.compile(r"vale (a pena )?(ressaltar|destacar|mencionar|notar|lembrar)", re.I),
    "e-importante-notar": re.compile(r"é importante (notar|ressaltar|lembrar|destacar)", re.I),
    "em-resumo": re.compile(r"\b(em resumo|em suma|por assim dizer|em outras palavras)\b", re.I),
    "neg-parallel": re.compile(r"não (apenas|só)\b.*\bmas também\b", re.I),
    "plays-role": re.compile(r"desempenha (um )?papel", re.I),
    "emdash-overuse": re.compile(r"—.*—"),  # 2+ em dashes
    "rich-tapestry": re.compile(r"\b(rica tapeçaria|um mundo de|verdadeira (joia|riqueza))\b", re.I),
}


def main() -> int:
    con = sqlite3.connect(DB)
    flagged = {}  # (entity_type, field, entity_id) -> [tells]
    tell_counts = Counter()
    # translation tell checked only on the natural translation field; others on explanation-like fields
    rows = con.execute(
        "SELECT entity_type, entity_id, field, value FROM localized_text "
        "WHERE entity_type IN ('sentence','token','particle') AND value IS NOT NULL AND value!=''")
    for et, eid, field, val in rows:
        if not isinstance(val, str):
            continue
        for name, rx in TELLS.items():
            if name == "quanto-a-mim-translation" and field != "translation":
                continue
            if name != "quanto-a-mim-translation" and field == "translation":
                continue  # natural translations: only the quanto-a tell applies
            if rx.search(val):
                flagged.setdefault((et, field, eid), []).append(name)
                tell_counts[name] += 1
    sent_ids = {eid for (et, f, eid) in flagged if et == "sentence"}
    print(f"flagged texts: {len(flagged)} across {len(sent_ids)} sentences")
    print("tell breakdown:", dict(tell_counts.most_common()))
    # sample
    for (et, field, eid), tells in list(flagged.items())[:8]:
        v = con.execute("SELECT value FROM localized_text WHERE entity_type=? AND entity_id=? AND field=?",
                        (et, eid, field)).fetchone()[0]
        print(f"  {et}/{field}#{eid} {tells}: {v[:120]}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
