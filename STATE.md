# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE
**Next action:** finish **P4 item→lesson placement**, then the **P5 pilot**. Concretely:
1. **P4 remaining:** persist `course_module`/`topic`/`lesson` rows from `design/course_outline.md`; build the
   remaining families (semantic_field, derivational word_family) + refine `importance_rank`; **assign each
   leveled item to exactly ONE introducing lesson** in i+1 order (D9: families organize, frequency/i+1 drive
   introduction); compute each lesson's `cumulative_known_set`; export `course/` (LLM-readable). Use the L+
   `concept_inventory.md` as the **superset check**.
2. **P5 pilot (mandatory gate):** pick ONE topic (a mid-N5 topic with a real known-set gives better Tatoeba
   i+1 coverage than T01); **build the §7 validation suite FIRST**; SudachiPy (A+C) dissection (kana caveat:
   は→わ,へ→え,を→お) + Layer-B pt-BR translation (generate, validate vs EN 93.5% + dict) + token glosses +
   particle explanations; select Tatoeba via FTS within the known-set; author lessons (dense pt-BR + exercises,
   by-ID); **score vs `design/quality_rubric.md`**; fix; then scale.
**DONE so far:** P-pre,L(+L+ deep),R(approved),P0,P1,P2,P3 + grammar registry (363) + structural families (58).
Corpus layer (kanji 250 / vocab 1,359 / grammar 363 / families 58) is leveled, linked, and exported to
`corpus/` as **canonical LLM-readable JSON+MD**; `db/corpus.sqlite` is a regenerable index.
**Reminder:** real Tatoeba PT is 1.8% → generate pt-BR (Layer B, EN-pivot); generous AI backfill, all flagged;
store kana+romaji; pitch data only (audio deferred). `sudachidict-full` installed.
**P5 dissection notes (verified):** `sudachidict-full` installed + SudachiPy A+C tokenization works. CAVEAT —
Sudachi `reading_form()` returns the *dictionary* reading, so override contextual particle kana in the
dissection: は→わ, へ→え, を→お (topic/direction/object particles). Build the §7 validation suite first; the
single dissection function must emit the §6 shape uniformly.

---

## Gate
**P0 → P7 do NOT begin until the owner approves the Phase R output.** L and R gate the build.

---

## Phase plan & status

| Phase | What | Status | Output |
|------|------|--------|--------|
| **P-pre** | git init, folder tree, `CLAUDE.md`, `STATE.md`, `INDEX.md` stub, commit | `done` | scaffold |
| **L** | Clean-room local course analysis (isolated, de-identified) | `done` | `research/local-course-insights/{topic_sequence,ideas_to_adapt,gaps_to_beat}.md` |
| **R** | Research, audit & self-improvement (MAX thinking) — **gate** | `done` | see R1–R6 |
| ↳ R1 | Critically audit this spec vs the goal | `done` | `design/PLAN_REVIEW.md` Part 1 |
| ↳ R2 | Research quality bar + methods (curricula, BR market, SLA, BR-PT) | `done` | 4 `research/references/` notes (adversarially verified + corrected) |
| ↳ R3 | Empirically measure source coverage (real numbers) | `done` | `reports/source_coverage.md` + `research/coverage/r3_probe_results.json` |
| ↳ R4 | Pressure-test & improve schemas | `done` | `design/schema_v2.md` |
| ↳ R5 | Define quality rubric | `done` | `design/quality_rubric.md` |
| ↳ R6 | Self-improve plan + draft outline | `done` | `design/PLAN_REVIEW.md` + draft `design/course_outline.md` |
| **— OWNER APPROVAL GATE —** | summarize & wait | ✅ `done` | **approved 2026-06-13** (decisions: PLAN_REVIEW Part 6) |
| **P0** | Finalize scaffold; write SQLite schema from `schema_v2.md` | `done` | venv, `001_init.sql` (29 tables), `init_db.py`, `ATTRIBUTION.md`, `sources.md` |
| **P1** | Ingest authoritative datasets → SQLite raw tables | `done` | `db/corpus.sqlite` (kanji inventory, JMdict raw, Tatoeba raw+FTS), `reports/stats.md` |
| **P2** | Level reconciliation (≥3 lists) + per-reading tiering | `done` | 250 kanji + 1,359 vocab leveled; `reports/validation.md` |
| **P3** | Methodology & curriculum research synthesis | `done` | `design/curriculum.md` (rules + pt-BR glossary) |
| **P4** | Course outline: Module → Topic → Lesson (family-driven) | `pending` | finalize `design/course_outline.md` + DB rows |
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
- _(L)_ Clean-room analysis via isolated subagent (raw material never entered main context). Found a library
  of 11 courses / 73 modules / 621 lessons (beginner→intermediate→advanced spine + 8 supplements). Output:
  3 de-identified abstraction files, verified clean (no names, no verbatim/reworded text). Key gaps to beat:
  no pitch accent, no JLPT scaffolding, katakana/adjectives/time-vocab mis-sequenced, hard difficulty cliff.
- _(R3)_ Probed real datasets: kanji 100% covered (245), vocab ~99% after normalization, Tatoeba PT only 1.8%
  (→ generate pt-BR Layer B, EN-pivot 93.5%), audio 2.5% (→ TTS), ≥3/vocab & ≥5/grammar thresholds realistic.
- _(R2)_ Workflow: 4 cited research notes + adversarial verify (8 agents). Curricula/SLA/BR-market = solid;
  BR-PT = minor issues → 4 factual overstatements corrected at source (vowel "1:1", length 2.5–3x, /u/ "spread",
  ち/じ dialect) + SLA phonetic-component softening. Verification traces added to the notes.
- _(R1/R4/R5/R6)_ Wrote PLAN_REVIEW (audit + 14 decisions + improved-spec addendum), schema_v2 (6 hard examples
  pass), quality_rubric (6 dims + hard gates + pilot gate), course_outline draft (pre-N5/N5/N4), sources.md.
  **STOPPED at the approval gate per the kickoff instruction.**
