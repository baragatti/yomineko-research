#!/usr/bin/env python3
"""P8 — surface-match fallback enrichment for grammar lessons the sentence_grammar links don't cover.

enrich_examples.py only used sentence_grammar links; many grammar points (esp. N4) have no linked bank sentences.
This fallback finds REAL (ai_generated=0) bank sentences whose text CONTAINS the grammar's surface form, for
grammar lessons that still have <2 example cards. It is conservative: surface must be >=3 Japanese chars
(skips ultra-generic 2-char forms like する/この/へ), sentence level <= the lesson's module, sentence jp length
<= MAXLEN (short = simpler = level-appropriate), real only, max ADD per lesson. Surface match is lower-confidence
than a grammar link (a string can match a homograph), so these are example cards for HUMAN REVIEW — logged.
Idempotent (skips lessons already carrying a "Mais exemplos" block). Usage: enrich_examples_surface.py
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSON_DIR = ROOT / "research" / "derived" / "lessons"
LV = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}
MIN_TOTAL = 2     # only enrich grammar lessons that have fewer than this many cards
ADD = 2           # add at most this many surface-matched cards
MAXLEN = 24       # only short sentences (chars) — keeps examples simple/level-appropriate
MIN_SURFACE = 3   # surface form must be >=3 Japanese chars (skip generic 2-char particles/verbs)
JP_RUN = re.compile(r"[ぁ-んァ-ヶ一-鿿]{%d,}" % MIN_SURFACE)


def main() -> int:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    enriched = 0
    added = 0
    log: list[str] = []
    for f in sorted(LESSON_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "Mais exemplos" in (d.get("body", "") or ""):
            continue
        cur = list(d.get("sentence_refs", []) or [])
        if len(cur) >= MIN_TOTAL:
            continue
        gks = [u["ref"].split(":", 1)[1] for u in d.get("unlocks", []) if u.get("type") == "grammar"]
        if not gks:
            continue
        r = con.execute(
            "SELECT m.level FROM lesson l JOIN topic t ON t.id=l.topic_id "
            "JOIN course_module m ON m.id=t.module_id WHERE l.slug=?", (d["slug"],)).fetchone()
        maxlv = LV.get(r[0] if r else "n4", 3)
        picks: list[str] = []
        for gk in gks:
            row = con.execute("SELECT structure_pattern FROM grammar_point WHERE key=?", (gk,)).fetchone()
            runs = JP_RUN.findall((row[0] or "") if row else "")
            if not runs:
                continue
            surface = max(runs, key=len)
            for s in con.execute(
                    "SELECT slug, jp, level FROM sentence WHERE ai_generated=0 AND jp LIKE ? "
                    "ORDER BY length(jp)", ("%" + surface + "%",)):
                if LV.get(s["level"], 9) <= maxlv and len(s["jp"]) <= MAXLEN \
                        and s["slug"] not in cur and s["slug"] not in picks:
                    picks.append(s["slug"])
                    log.append(f"{d['slug']}: +{s['slug']} (surface '{surface}', {len(s['jp'])} chars)")
                    break  # one per grammar key
            if len(picks) >= ADD:
                break
        if not picks:
            continue
        d["sentence_refs"] = cur + picks
        block = ['<heading level="3"><text>Mais exemplos</text></heading>']
        block += [f'<sentence ref="{s}" show="furigana" mode="card"/>' for s in picks]
        body = d.get("body", "")
        idx = body.rfind("<checklist>")
        d["body"] = (body[:idx] + "\n" + "\n".join(block) + "\n\n" + body[idx:]) if idx >= 0 \
            else body + "\n" + "\n".join(block) + "\n"
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        enriched += 1
        added += len(picks)
    con.close()
    print(f"surface-enriched {enriched} lesson(s) with {added} real example card(s) [LOWER-CONFIDENCE, review]")
    for line in log:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
