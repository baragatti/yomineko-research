# Corpus layer (LLM-readable, canonical)

_Generated 2026-06-16 from `db/corpus.sqlite` (regenerable index). **These JSON/MD files are the source of truth.** Localized content uses locale-objects keyed by `pt-BR` (+ `en` source); mechanical enums are neutral. See `design/i18n.md`._

| entity | files | n5 | n4 |
|--------|-------|---:|---:|
| kanji | `corpus/kanji/<level>.json` | 80 | 170 |
| vocab | `corpus/vocab/<level>.json` | 706 | 653 |
| grammar | `corpus/grammar/<level>.json` | 151 | 213 |
| sentences | `corpus/sentences/bank.json` | 4959 | (dissected) |
| families | `corpus/families/families.json` | 396 | (cross-level) |
| conjugations | `corpus/conjugations/<level>.json` | 213 | 295 |
| kana _(hira/kata families)_ | `corpus/kana/<script>.json` | 28 | 29 |
