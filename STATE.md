# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE
**Next action:** **SCALE P5/P6** (pilot gate PASSED — see `reports/pilot_review.md`). Do the punch-list first
(compute `sentence.level` from components; add a `te-form` grammar anchor; selector tokenization guard), then
**industrialize dissection with a Workflow** (one agent per selected sentence: SudachiPy skeleton in → Layer-B
pt-BR out → adversarial validate) to hit ≥3 sentences/vocab + ≥5/grammar across `top:n5-te-form`, then topic by
topic (pre-N5 → N5 → N4), authoring lessons (dense pt-BR + exercises, by-ID) and re-exporting + committing after
each topic. Refine P4 placement (N4 grammar residual, kanji cap). Then **P7** QA + coverage comparison vs the
L+ `concept_inventory.md`. Pipeline scripts: `dissect.py`, `select_candidates.py`, `persist_dissection.py`,
`validate.py`, `add_pilot_lesson.py`, exporters.
**Older detail (kept):** SudachiPy A+C dissection works (kana caveat は→わ,へ→え,を→o); real Tatoeba PT 1.8%
→ generate pt-BR Layer B (EN-pivot 93.5%); generous AI backfill all flagged; store kana+romaji; pitch data only.
Recommend pilot = **`top:n5-te-form`** (mid-N5; rich Tatoeba supply; known-set = items introduced in topics
order≤15). Steps: (1) **build the §7 validation suite first** (`scripts/validate/`); (2) write the SudachiPy
A+C **dissection pipeline** (kana caveat: は→わ, へ→え, を→お) emitting the §6 shape uniformly; (3) **select**
Tatoeba sentences via `raw_tatoeba_fts` whose tokens are within the topic's cumulative-known-set (i+1),
preferring those with EN/audio; (4) **Layer-B pt-BR**: generate translation + pt_literal + per-token gloss +
particle explanation, validate readings/lemmas vs KANJIDIC2/JMdict; persist to `sentence`/`token`/`particle`;
(5) author the topic's **lessons** (dense pt-BR + structured exercises, sentence refs BY ID); (6) export
`corpus/sentences/` + `course/n5/top-...`; **score vs `design/quality_rubric.md`** (all dims ≥3, gates pass);
fix; commit. Cumulative-known-set helper: items with `introducing_topic_id` whose topic.ord ≤ pilot topic.ord.
**DONE:** P-pre,L(+L+),R(approved),P0,P1,P2,P3,P4(1st-pass placement). Corpus (kanji 250 / vocab 1,359 /
grammar 363 / families 58) + course outline (35 topics) all exported to `corpus/`+`course/` as canonical
LLM-readable JSON+MD; SQLite is a regenerable index.
**Reminder:** real Tatoeba PT is 1.8% → generate pt-BR (Layer B, EN-pivot 93.5%); generous AI backfill (all
flagged); store kana+romaji; pitch data only (audio deferred). `sudachidict-full` installed.
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
| **P4** | Course outline: Module → Topic → Lesson (family-driven) | `done (1st pass)` | 3 modules, 35 topics; all 1,359 vocab + 250 kanji + 363 grammar placed at an introducing topic; `course/` exported. Refine in P6: N4 grammar residual (146) + N4 kanji cap. |
| **P5** | Sentence corpus: mining + dissection (SudachiPy A+C) | `in_progress` | pipeline built (dissect/select/persist/validate); 5 te-form sentences dissected → `corpus/sentences/` |
| ↳ P5-pilot | ONE complete topic end-to-end, checked vs rubric (gate) | `✅ gate PASSED` | `reports/pilot_review.md` (gates pass; D2/D6=4); punch-list before scaling |
| **P6** | Courseware authoring: lessons (dense pt-BR + exercises) | `in_progress` | pilot lesson `course/n5/topic-15-te-form/lesson-01.{json,md}` (5 exercises, by-ID) |
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
