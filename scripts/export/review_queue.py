#!/usr/bin/env python3
"""P7 — assemble the teacher review queue (acceptance #8): everything needs_review, AI-generated FIRST.
Writes reports/review_queue.md with counts by category in review priority order. Pure SQL."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
c = sqlite3.connect(ROOT / "db" / "corpus.sqlite")


def n(q):
    return c.execute(q).fetchone()[0]


rows = [
    # (priority, category, layer, count, where-to-review)
    (1, "AI-generated sentences", "B",
     n("SELECT count(*) FROM sentence WHERE ai_generated=1 AND needs_review=1"), "corpus/sentences/bank.json"),
    (2, "Grammar explanations (original pt-BR)", "C",
     n("SELECT count(*) FROM grammar_point WHERE needs_review=1"), "corpus/grammar/*.json"),
    (3, "Lessons (dense pt-BR + exercises)", "C",
     n("SELECT count(*) FROM lesson WHERE needs_review=1"), "course/**/lesson-*.md"),
    (4, "Families (groupings + governing rules)", "C",
     n("SELECT count(*) FROM family WHERE needs_review=1"), "corpus/families/families.json"),
    (5, "Sentence dissections (pt translation + glosses)", "B",
     n("SELECT count(*) FROM sentence WHERE ai_generated=0 AND needs_review=1"), "corpus/sentences/bank.json"),
    (6, "Vocab senses (pt-BR meanings)", "B",
     n("SELECT count(*) FROM vocab_sense WHERE needs_review=1"), "corpus/vocab/*.json"),
    (7, "Kanji pt-BR meanings", "B",
     n("SELECT count(*) FROM kanji WHERE level IS NOT NULL AND created_by='ai' AND meanings_pt IS NOT NULL"),
     "corpus/kanji/*.json"),
    (8, "Per-reading tier seeds (heuristic)", "B",
     n("SELECT count(*) FROM kanji_reading WHERE needs_review=1"), "corpus/kanji/*.json"),
]
total = sum(r[3] for r in rows)
out = ["# Teacher review queue (acceptance #8)", "",
       f"_Generated from `db/corpus.sqlite`. **{total:,} items** flagged `needs_review`, in review priority "
       f"order (AI-generated first, then Layer C pedagogy, then Layer B derived). Layer A (dictionary facts) "
       f"is auditable directly against its dataset source and is not in this queue._", "",
       "| # | category | layer | items | review in |",
       "|--:|----------|:-----:|------:|-----------|"]
for pr, cat, layer, cnt, where in rows:
    out.append(f"| {pr} | {cat} | {layer} | {cnt:,} | `{where}` |")
out += ["", "## Review guidance",
        "- **Layer A is trusted** (characters, readings, stroke order, POS, JMdict/KANJIDIC2 facts) — no review.",
        "- **Layer B** (pt-BR translations/glosses/dissections) is machine-validated against Layer A; the teacher",
        "  spot-checks naturalness/accuracy. **Layer C** (grammar explanations, lessons, families) needs full",
        "  pedagogical review.",
        "- Start at priority 1 and work down. Each item carries its `source` for traceability."]
(ROOT / "reports" / "review_queue.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"wrote reports/review_queue.md — {total} items flagged")
c.close()
