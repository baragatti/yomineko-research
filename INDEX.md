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

## Phase R deliverables (present now — the approval gate)
| File | What |
|------|------|
| [`design/PLAN_REVIEW.md`](design/PLAN_REVIEW.md) | Audit + 14 decisions + improved-spec addendum + owner questions |
| [`reports/source_coverage.md`](reports/source_coverage.md) | Empirical source coverage (R3) |
| [`research/coverage/r3_probe_results.json`](research/coverage/r3_probe_results.json) | Raw R3 numbers |
| [`design/schema_v2.md`](design/schema_v2.md) | Pressure-tested data model (6 hard examples) |
| [`design/quality_rubric.md`](design/quality_rubric.md) | Paid-grade yardstick + pilot gate |
| [`design/course_outline.md`](design/course_outline.md) | Draft Module→Topic→Lesson (R6 module map) |
| [`design/sources.md`](design/sources.md) | Source versions + license/commercial-use facts |
| [`research/references/`](research/references/) | 4 cited research notes (curricula, BR market, SLA, BR-PT), verified |
| [`research/local-course-insights/`](research/local-course-insights/) | Phase L de-identified abstraction |
| [`scripts/ingest/fetch_datasets.py`](scripts/ingest/fetch_datasets.py) · [`scripts/validate/r3_coverage_probe.py`](scripts/validate/r3_coverage_probe.py) | R3 tooling (idempotent) |

## Conventions
- **By-ID linking:** corpus entities have stable IDs; courseware references them by ID, never embeds.
- **Provenance:** every record has `source` + a Layer (A/B/C); Layer B/C carry `needs_review` where required.
- **Language:** code/notes English; learner-facing pt-BR.
