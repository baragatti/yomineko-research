# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE
> **2026-06-14 (resumed; limit cleared).** Content-gap fill in progress. **Status:** meanings — kanji 250/250 ✓,
> N5 vocab 2249/2249 ✓, N4 vocab **1320/1812** (492 left). grammar explanations — **250/364** (N5 **151/151 ✓**,
> N4 99/213; 114 left). Use **per-chunk files** for grammar (robust) and run **ONE workflow at a time** (concurrent
> runs cause transient server rate-limits). Engines all built.
>
> **✅ Foundation + content COMPLETE & verified** (`reports/completeness.md`): meanings 100%, grammar 364/364,
> families cover all items, pitch 89.8%, dissection template fully met. **✅ P7 groundwork done (low-token pass
> 2026-06-14):** §1.7 graph queries all PASS (`reports/graph_query_tests.md`, acceptance #10); review queue
> assembled (`reports/review_queue.md`, 6,193 items, #8); coverage-comparison vs L+ confirms superset
> (`reports/coverage_comparison.md`, #13); topic objectives 35/35 + module overviews 3/3; example_vocab_ids +
> grammar_related contrast links fixed.
>
> **PRE-P5 task (do FIRST when resuming, low-token):** make the data model **locale-agnostic** — migrate the
> `_pt` columns to a locale form (PT = first locale module), per [`design/i18n.md`](design/i18n.md), so the
> bulk lands locale-aware. Identifiers/enums/files stay English; only content is locale-scoped.
>
> **THE ONLY token-heavy work left = P5 (sentence bank) + P6 (lessons), topic-by-topic.** Recipe below.
> **Run ONE workflow at a time** (concurrency → server rate-limits). Result extraction: read the workflow
> `.output`, take its `.result` array (wrapped in `{summary,…,result}`), rewrite as bare array, then persist.
> Final P7 after the bank fills: full `validate.py` run + numeric coverage (sentences/item) + final stats.

**Plan (revised after 2026-06-14 gaps audit — see `reports/gaps_audit.md`):** content layers were
missing from the plan. Execute the ADDED steps in dependency order, THEN resume topic dissection:
1. **P5b — Layer-B pt-BR meanings (FOUNDATIONAL, do first):** translate `vocab_sense.gloss_en→gloss_pt`
   (4,061) + `kanji.meanings_en→meanings_pt` (250) via batch→Workflow→validate; populate
   `kanji_reading.example_vocab_ids`. Everything (lessons, glosses) depends on this.
2. **P6-grammar — Layer-C grammar explanations:** author `label_pt`+`explanation_pt`+`formation_pt`+
   `nuance_pt` per taught grammar point (Workflow, needs_review). ← owner flag.
3. **P4b — full families:** semantic_field / word_family / particle_set / contrast_pair so every item ∈ ≥1 family.
4. **P2b — pitch accent data:** source kanjium/OJAD-derived → `vocab_pitch` (data only; audio deferred).
5. **Then resume** mass dissection + lesson authoring topic-by-topic (recipe below), then **P7** QA.

### Topic dissection recipe (P5/P6 mass-production — proven on te-form, 19 sentences/0 errors)
1. `prepare_batch.py --topic <slug> --targets <term:count …> --out research/derived/batch_<slug>.json`
   (targets = the topic's grammar sub-points to ≥5 + its key vocab to ≥3).
2. Launch the **dissection Workflow** (inline script in session, or saved) with
   `args={batch_path, count}` → author+verify (15/15 faithful last run). **Note:** pass `count` AND keep the
   `N = A.count || <n>` fallback (args binding was flaky once).
3. Copy the workflow `.output`, extract its `.result` array → `..._result.json`,
   `persist_batch.py --batch … --result …`, then `validate.py`.
4. Author the topic's lessons (pattern: `add_pilot_lesson.py` → generalize), `export_corpus.py` +
   `export_course.py`, commit.
Then **P7**: full validation, `reports/stats.md`, coverage comparison vs L+ `concept_inventory.md` (superset),
§1.7 cross-cutting query tests, assemble needs_review queue.
**Pipeline scripts:** dissect / select_candidates / prepare_batch / persist_dissection / persist_batch /
validate / add_pilot_lesson / export_corpus / export_course. Kana caveat は→わ,へ→え,を→o; pt-BR generated
Layer-B (EN-pivot); generous AI backfill all flagged; store kana+romaji; pitch data only (audio deferred).
**Scale reminder:** this is the multi-session bulk (~all topics × dissection + lessons).
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
| **P2b** | Pitch accent ingestion (data only; audio deferred) | `done` | kanjium → `vocab_pitch` 1,221/1,359 (89.8%) |
| **P4b** | Full family coverage (semantic/word/particle/contrast) | `done` | every item ∈ ≥1 family (vocab 1359/kanji 250/grammar 364); 395 families (#9) |
| **P5b** | Layer-B pt-BR meanings (vocab senses + kanji) | `done` | kanji 250/250, vocab 4061/4061 senses ✓ (#1,#2) — _example_vocab_ids still TODO_ |
| **P6-g** | Layer-C grammar explanations (label/expl/formation/nuance) | `done` | 364/364 (#3) — owner flag resolved |
| **P5** | Sentence corpus: mining + dissection (SudachiPy A+C) | `in_progress` | pipeline PROVEN incl. Workflow scaling (author+verify); **19 te-form sentences** dissected, 0 errors → `corpus/sentences/`. Remaining: run batches across all topics. |
| ↳ P5-pilot | ONE complete topic end-to-end, checked vs rubric (gate) | `✅ gate PASSED` | `reports/pilot_review.md` (gates pass; D2/D6=4); punch-list before scaling |
| **P6** | Courseware authoring: lessons (rich HTML + exercises) | `in_progress` | pilot lesson done. **Follow [`design/p6_authoring_spec.md`](design/p6_authoring_spec.md)** + **rich format [`design/lesson_format.md`](design/lesson_format.md)** (custom-element HTML, refs by ID, phrase/kanji modals, inline exercises): by-ID no-dup, introduce-once → FSRS-enroll, 100% coverage, optional per-kanji lessons |
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
