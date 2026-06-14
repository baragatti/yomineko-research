# Corpus layer (LLM-readable, canonical)

_Generated 2026-06-14 by `scripts/export/export_corpus.py` from `db/corpus.sqlite` (a regenerable index). **These JSON/MD files are the source of truth.**_

| entity | files | n5 | n4 |
|--------|-------|---:|---:|
| kanji | `corpus/kanji/<level>.json` + INDEX.md | 80 | 170 |
| vocab | `corpus/vocab/<level>.json` + INDEX.md | 706 | 653 |
| grammar | `corpus/grammar/<level>.json` + INDEX.md | 151 | 213 |
| sentences | `corpus/sentences/bank.json` + INDEX.md | 19 | (dissected) |
| families | `corpus/families/families.json` + INDEX.md | 58 | (cross-level) |

Each record carries `level_confidence`/`level_agreement`/`level_sources` (provenance) and a `source`. pt-BR meanings (`meanings_pt`/`gloss_pt`) are populated in the Layer-B pass.
