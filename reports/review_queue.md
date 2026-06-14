# Teacher review queue (acceptance #8)

_Generated from `db/corpus.sqlite`. **6,399 items** flagged `needs_review`, in review priority order (AI-generated first, then Layer C pedagogy, then Layer B derived). Layer A (dictionary facts) is auditable directly against its dataset source and is not in this queue._

| # | category | layer | items | review in |
|--:|----------|:-----:|------:|-----------|
| 1 | AI-generated sentences | B | 0 | `corpus/sentences/bank.json` |
| 2 | Grammar explanations (original pt-BR) | C | 364 | `corpus/grammar/*.json` |
| 3 | Lessons (dense pt-BR + exercises) | C | 0 | `course/**/lesson-*.md` |
| 4 | Families (groupings + governing rules) | C | 396 | `corpus/families/families.json` |
| 5 | Sentence dissections (pt translation + glosses) | B | 226 | `corpus/sentences/bank.json` |
| 6 | Vocab senses (pt-BR meanings) | B | 4,061 | `corpus/vocab/*.json` |
| 7 | Kanji pt-BR meanings | B | 250 | `corpus/kanji/*.json` |
| 8 | Per-reading tier seeds (heuristic) | B | 1,102 | `corpus/kanji/*.json` |

## Review guidance
- **Layer A is trusted** (characters, readings, stroke order, POS, JMdict/KANJIDIC2 facts) — no review.
- **Layer B** (pt-BR translations/glosses/dissections) is machine-validated against Layer A; the teacher
  spot-checks naturalness/accuracy. **Layer C** (grammar explanations, lessons, families) needs full
  pedagogical review.
- Start at priority 1 and work down. Each item carries its `source` for traceability.
