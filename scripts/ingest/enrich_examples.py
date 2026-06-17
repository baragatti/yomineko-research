#!/usr/bin/env python3
"""P8 — raise sentence-bank usage by featuring MORE real example sentences per grammar lesson (prefer sourced).

We dissected ~5k sentences but featured <9%. This adds, to each grammar-teaching lesson that currently has few
featured sentences, a compact "Mais exemplos" block of additional sentences pulled from the bank for that
lesson's grammar points — REAL (ai_generated=0, e.g. Tatoeba/JEC) preferred over AI-generated, shortest-first,
level <= the lesson's module. Cards are compact (mode="card"), so lessons gain examples without heavy prose.
Caps at TARGET_TOTAL featured and MAX_ADD additions so nothing balloons. Idempotent (skips if a "Mais exemplos"
block already exists). Edits only the JSON (sentence_refs + body); load_lessons wires lesson_sentence. Run before
load/validate, then export. Usage: enrich_examples.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSON_DIR = ROOT / "research" / "derived" / "lessons"
LV = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
TARGET_TOTAL = 4   # bring each grammar lesson to ~this many featured sentences
MAX_ADD = 3        # never add more than this per lesson (keep it light)
MARKER = "Mais exemplos"


def _module_level(con, slug: str) -> str | None:
    r = con.execute(
        "SELECT m.level FROM lesson l JOIN topic t ON t.id=l.topic_id "
        "JOIN course_module m ON m.id=t.module_id WHERE l.slug=?", (slug,)).fetchone()
    return r[0] if r else None


def _candidates(con, gram_keys: list[str], maxlv: int, exclude: set[str]) -> list[str]:
    if not gram_keys:
        return []
    qmarks = ",".join("?" * len(gram_keys))
    rows = con.execute(
        f"SELECT DISTINCT s.slug, s.ai_generated, s.level, length(s.jp) AS L "
        f"FROM grammar_point g JOIN sentence_grammar sg ON sg.grammar_id=g.id "
        f"JOIN sentence s ON s.id=sg.sentence_id "
        f"WHERE g.key IN ({qmarks})", gram_keys).fetchall()
    ok = [r for r in rows if LV.get(r[2], 9) <= maxlv and r[0] not in exclude]
    # real (ai_generated=0) first, then shortest jp
    ok.sort(key=lambda r: (r[1], r[3]))
    return [r[0] for r in ok]


def main() -> int:
    con = sqlite3.connect(DB)
    enriched = 0
    added_total = 0
    for f in sorted(LESSON_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        body = d.get("body", "") or ""
        if MARKER in body:
            continue  # already enriched
        gram = [u["ref"].split(":", 1)[1] for u in d.get("unlocks", []) if u.get("type") == "grammar"]
        if not gram:
            continue  # only grammar-teaching lessons get example enrichment
        cur = list(d.get("sentence_refs", []) or [])
        if len(cur) >= TARGET_TOTAL:
            continue
        maxlv = LV.get(_module_level(con, d["slug"]) or "n4", 3)
        need = min(MAX_ADD, TARGET_TOTAL - len(cur))
        cands = _candidates(con, gram, maxlv, set(cur))[:need]
        if not cands:
            continue
        d["sentence_refs"] = cur + cands
        block = ['<heading level="3"><text>Mais exemplos</text></heading>']
        block += [f'<sentence ref="{s}" show="furigana" mode="card"/>' for s in cands]
        section = "\n" + "\n".join(block) + "\n\n"
        idx = body.rfind("<checklist>")
        d["body"] = (body[:idx] + section + body[idx:]) if idx >= 0 else (body + section)
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        enriched += 1
        added_total += len(cands)
    con.close()
    print(f"enriched {enriched} lesson(s) with {added_total} additional real-preferred example sentence(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
