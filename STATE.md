# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE
**Next action:** Phase P-pre is being finalized (scaffold + this file + CLAUDE.md). After committing P-pre,
begin **Phase L** — clean-room, isolated analysis of the local course at
`C:\Users\WiseWolf\IdeaProjects\japorongo-back\files` (entry `biblioteca.json`), emitting ONLY the
de-identified abstraction to `research/local-course-insights/` (§1.4 absolute rules).
Then **Phase R** (research/audit/self-improve), then **STOP for owner approval** before P0.

---

## Gate
**P0 → P7 do NOT begin until the owner approves the Phase R output.** L and R gate the build.

---

## Phase plan & status

| Phase | What | Status | Output |
|------|------|--------|--------|
| **P-pre** | git init, folder tree, `CLAUDE.md`, `STATE.md`, `INDEX.md` stub, commit | `in_progress` | scaffold |
| **L** | Clean-room local course analysis (isolated, de-identified) | `pending` | `research/local-course-insights/{topic_sequence,ideas_to_adapt,gaps_to_beat}.md` |
| **R** | Research, audit & self-improvement (MAX thinking) — **gate** | `pending` | see R1–R6 |
| ↳ R1 | Critically audit this spec vs the goal | `pending` | → `design/PLAN_REVIEW.md` |
| ↳ R2 | Research quality bar + methods (curricula, BR market, SLA, BR-PT) | `pending` | `research/references/` notes |
| ↳ R3 | Empirically measure source coverage (real numbers) | `pending` | `reports/source_coverage.md` |
| ↳ R4 | Pressure-test & improve schemas | `pending` | `design/schema_v2.md` |
| ↳ R5 | Define quality rubric | `pending` | `design/quality_rubric.md` |
| ↳ R6 | Self-improve plan + draft outline | `pending` | `design/PLAN_REVIEW.md`, draft `design/course_outline.md` / `module_map.md` |
| **— OWNER APPROVAL GATE —** | summarize & wait | `pending` | — |
| **P0** | Finalize scaffold; write SQLite schema from `schema_v2.md` | `pending` | migrations, `sources.md`, `ATTRIBUTION.md` stubs |
| **P1** | Ingest authoritative datasets → SQLite raw tables | `pending` | populated `db/corpus.sqlite`, `reports/stats.md` |
| **P2** | Level reconciliation (≥3 lists) + per-reading tiering | `pending` | leveled items + confidence |
| **P3** | Methodology & curriculum research synthesis | `pending` | `design/curriculum.md` |
| **P4** | Course outline: Module → Topic → Lesson (family-driven) | `pending` | `design/course_outline.md` |
| **P5** | Sentence corpus: mining + dissection (SudachiPy A+C) | `pending` | dissected sentence bank (by ID) |
| ↳ P5-pilot | ONE complete topic end-to-end, checked vs rubric (gate) | `pending` | pilot topic + critique |
| **P6** | Courseware authoring: lessons (dense pt-BR + exercises) | `pending` | `course/<level>/topic-NN/lesson-MM.{json,md}` |
| **P7** | Validation & QA gates (+ coverage comparison vs Phase L) | `pending` | `reports/validation.md`, `reports/stats.md` |

---

## Dataset manifest (versions + checksums)
_Populated in P1; provenance also recorded in `design/sources.md`. (R3 may pull samples earlier for coverage probing.)_

| Dataset | Version/date | SHA256 | License | Commercial-OK? |
|---------|-------------|--------|---------|----------------|
| jmdict-simplified (JMdict) | — | — | — | — |
| Kanjidic2 (jmdict-simplified) | — | — | — | — |
| Kradfile/Radkfile | — | — | — | — |
| KanjiVG | — | — | — | — |
| Tatoeba (jpn/eng/por + links + audio) | — | — | — | — |
| JLPT lists (≥3, community) | — | — | — | — |
| Frequency list | — | — | — | — |
| Pitch accent (optional) | — | — | — | — |

---

## Validation thresholds (working defaults; may be revised in R3)
- Dissected sentences: **≥3 per vocab**, **≥5 per grammar point**; rich per-topic bank (hundreds where sources allow).
- AI-generated sentences: capped as a % per topic (cap set in R3), always `needs_review`.
- Zero unresolved reading/lemma mismatches against KANJIDIC2 / JMdict.

---

## Session log
- _(P-pre)_ Created dedicated git repo, folder tree, `CLAUDE.md`, `STATE.md`, `.gitignore`, `INDEX.md` stub.
