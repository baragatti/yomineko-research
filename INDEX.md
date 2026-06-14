# INDEX.md — project manifest (for LLM + human navigation)

> Stub created in Phase P-pre. **Kept current as the project grows** (spec §9, acceptance criterion 14).
> This is the map an LLM reads first to navigate, analyze, improve, and later implement the project.

## Top-level files
| Path | What it is |
|------|-----------|
| [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md) | **Master spec.** Governs everything. |
| [`CLAUDE.md`](CLAUDE.md) | Project memory: §1 non-negotiables + conventions. |
| [`STATE.md`](STATE.md) | Live plan, per-unit status, `RESUME HERE`. |
| [`INDEX.md`](INDEX.md) | This manifest. |
| [`README.md`](README.md) | How the project is organized + how to consume each layer. |
| `ATTRIBUTION.md` | _(P0)_ Required license attributions. |

## Folders
| Path | Layer | What it holds | Populated in |
|------|-------|---------------|--------------|
| `research/datasets/` | sources | Raw downloads + checksums (git-ignored; manifest tracked) | P1 (samples R3) |
| `research/derived/` | sources | Cleaned/extracted data (per-level lists, frequency, pitch) | P2+ |
| `research/references/` | research | Research notes + citations (methodology, competitors) | R2, P3 |
| `research/local-course-insights/` | research | **Phase L only:** de-identified abstraction (no copied text, no names) | L |
| `research/coverage/` | research | Source coverage probes | R3 |
| `db/corpus.sqlite` | canonical | The SQLite store (all layers); git-ignored, regenerable | P0/P1 |
| `scripts/analyze_local/` | code | Phase L reader (emits abstraction only) | L |
| `scripts/ingest/` | code | Dataset ingestion | P1 |
| `scripts/validate/` | code | Validation suite (spec §7) | P5+ |
| `scripts/export/` | code | DB → corpus/ + course/ exporters | P6 |
| `design/` | design | `PLAN_REVIEW`, `schema_v2`, `quality_rubric`, `curriculum`, `course_outline`, `sources` | R, P0, P3, P4 |
| `corpus/` | CORPUS | By-ID reusable: kanji, vocab, grammar, sentences, families + indexes | P5/P6 |
| `course/` | COURSEWARE | Module→Topic→Lesson: pre-n5/, n5/, n4/ | P6 |
| `reports/` | QA | `validation.md`, `stats.md`, `source_coverage.md` | R3, P5+ |

## Current state (2026-06-14)
**Foundation complete & verified** (`reports/completeness.md`); only P5 sentence-bank + P6 lessons remain (volume).

**Corpus layer** (`corpus/`, canonical LLM-readable JSON+MD; `db/corpus.sqlite` is a regenerable index):
| Registry | Count | Content |
|----------|------:|---------|
| [`corpus/kanji/`](corpus/kanji/) | 250 | meanings_pt, readings (tiered)+example_vocab, strokes, KanjiVG, components |
| [`corpus/vocab/`](corpus/vocab/) | 1,359 | gloss_pt (4,061 senses), romaji, pos, forms, pitch (90%), kanji links |
| [`corpus/grammar/`](corpus/grammar/) | 364 | label/explanation/formation/nuance (pt-BR), related, level provenance |
| [`corpus/families/`](corpus/families/) | 396 | every item ∈ ≥1 family; importance_rank + is_core |
| [`corpus/sentences/`](corpus/sentences/) | 19 | full §6 dissection (P5 scales this) |
| [`course/`](course/INDEX.md) | 35 topics, 1 lesson | outline + objectives; P6 authors lessons |

**Design** (`design/`): PLAN_REVIEW, schema_v2, quality_rubric, curriculum, course_outline, sources.
**Reports** (`reports/`): completeness, gaps_audit, source_coverage, pilot_review, validation, stats,
graph_query_tests (§1.7 ✓), review_queue (6,193 items), coverage_comparison (superset vs L+).
**Pipeline** (`scripts/`): fetch_datasets · ingest_all · reconcile_levels · place_items · build_families(+_full) ·
dissect · select_candidates · prepare_batch/persist_batch · prepare_meanings/persist_meanings ·
prepare_grammar/persist_grammar · ingest_pitch · validate · completeness_audit · graph_queries · export_corpus/export_course.
**Research** (`research/`): datasets (provenance), references (4 cited notes), local-course-insights (L+ abstraction), coverage.

## Conventions
- **By-ID linking:** corpus entities have stable IDs; courseware references them by ID, never embeds.
- **Provenance:** every record has `source` + a Layer (A/B/C); Layer B/C carry `needs_review` where required.
- **Language:** code/notes English; learner-facing pt-BR.
