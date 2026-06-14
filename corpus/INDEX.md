# Corpus layer (LLM-readable, canonical)

_Generated 2026-06-13 by `scripts/export/export_corpus.py` from `db/corpus.sqlite` (a regenerable index). **These JSON/MD files are the source of truth.**_

| entity | files | n5 | n4 |
|--------|-------|---:|---:|
| kanji | `corpus/kanji/<level>.json` + INDEX.md | 80 | 170 |
| vocab | `corpus/vocab/<level>.json` + INDEX.md | 706 | 653 |
| grammar | _(P4+)_ | — | — |
| sentences | _(P5+)_ | — | — |
| families | _(P4+)_ | — | — |

Each record carries `level_confidence`/`level_agreement`/`level_sources` (provenance) and a `source`. pt-BR meanings (`meanings_pt`/`gloss_pt`) are populated in the Layer-B pass.
