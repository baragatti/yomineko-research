# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE
> **2026-06-14 (P5 DEEPENING — owner chose "fully deepen to §10"). SESSION LIMIT hit, resets 8:30pm
> America/Sao_Paulo.** **Sentence bank = 1576, 0 validation errors.** Coverage:
> `n5: vocab ≥1 78% ≥3 60% | grammar ≥1 76% ≥5 51%` · `n4: vocab ≥1 67% ≥3 41% | grammar ≥1 30% ≥5 0%`.
> Vocab coverage (prepare_coverage rounds a–d both levels) + N5 grammar coverage (chunks 0–3 done, **chunk 4
> partial** 11/20) DONE. **N4 grammar chunks NOT yet run** (partitioned + ready).
>
> **RESUME QUEUE (ONE workflow at a time; recipe = split_groups→Workflow `scripts/ingest/dissect_batch_workflow.js`
> {dir,count}→read .output `.result`→`persist_batch --batch <batchfile>`→`repair_glosses`→`validate`→
> `export_corpus`→commit):**
> 1. **Re-run N5 grammar chunk 4** (fills 9 failed): `{dir:".../research/derived/gram_n5_4_groups",count:20}`,
>    persist `--batch batch_gram_n5_4.json` (idempotent).
> 2. **N4 grammar chunks 0–7** (ALL split + ready): each `{dir:".../research/derived/gram_n4_<i>_groups",
>    count:20}`, persist `--batch batch_gram_n4_<i>.json`. This is the biggest remaining lift (N4 grammar ≥5 = 0%).
> 3. ~~Deterministic particle-link~~ **DONE** (`particle_link.py`, +91 edges; fundamental particles ~8 ex;
>    N5 grammar ≥5 now 59%). Re-run after more sentences land to top up や/さ/し (currently <8).
> 4. **More vocab deepening** rounds (`prepare_coverage.py --level n5|n4 --target 3 …`) until ≥3 plateaus,
>    then RAISE to `--target 5` where wanted.
> 5. **GENERATION** for residual tail selection can't reach (build: agent writes i+1 sentences from a topic's
>    known-set, flagged `ai_generated`; tokenize → dissect same engine). Spec §1.2: selection first.
> 6. Then **P6 lessons** + **P7** QA. Coverage snippet: see prior turns (`Counter(sentence_vocab.vocab_id)` /
>    `sentence_grammar.grammar_id`, % ≥1/≥3/≥5 per level).
>
> **(milestone) P5 first-pass seeding COMPLETE.** All 35 content topics seeded via the precise batched engine
> (v2). Engine, coverage selector, self-heal all built and proven (see recipe block below).
>
> **Coverage vs §10 (≥3 sent/vocab, ≥5/grammar) — the remaining heavy lift:**
> `n5: vocab 706 → ≥1:186 (26%) ≥3:70 (9%) | grammar 151 → ≥5:10`
> `n4: vocab 653 → ≥1:36 (5%)  ≥3:15 (2%) | grammar 213 → ≥5:1`
> First-pass seeded each topic's grammar + key vocab; the long tail is thin. **Deepening** (engine below):
> `prepare_coverage.py` greedily selects Tatoeba covering the most undercovered vocab — BUT each batch advances
> ~1 vocab/sentence because rare vocab seldom occur in known-set-pure Tatoeba (max-new≤2). **CONCLUSION: the
> rare tail needs the GENERATION path (still TODO)**, not just more selection. Full §10 is many more workflows.
>
> **Strategic fork for the next session (owner may choose):**
> 1. **Deepen P5 coverage** to §10 — many selection batches (mid-freq vocab) + build & run a GENERATION
>    workflow for the rare tail (agent writes i+1 sentences from a topic's known-set, flagged `ai_generated`).
> 2. **Start P6 lessons now** — every topic already has seed examples; author rich-format lessons
>    (`design/lesson_format.md`) referencing existing sentence IDs, deepen the bank lazily as lessons demand.
> 3. Hybrid: ensure **≥1 sentence for every taught item** first (cheaper than ≥3), then P6.
>
> **✅ Done earlier:** foundation+content (meanings 100%, grammar 364/364, families, pitch 89.8%); P7 groundwork
> (§1.7 graph queries PASS, review queue, L+ superset, objectives/overviews); **PRE-P5 i18n** (localized_text
> live, 6,937 rows → pt-BR, neutral fields). **Run ONE workflow at a time** (concurrency → rate-limits).

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

### P5 status (engine v2 — batched + precise grammar linking): rebuilding bank from saved results.
**Engine v2 (current; run ONE workflow at a time):**
1. `prepare_batch.py --topic <slug> --targets <term:count …> --out research/derived/batch_<t>.json` — selects
   real Tatoeba within the i+1 known-set AND attaches the topic's `grammar_candidates` (key/pattern/label) to
   each item. (FTS5 is **trigram** → it can't match <3-char terms; prepare auto-falls back to LIKE for short
   targets like たい/一番/たり.)
2. (multi-topic) concat batches → `batch_all.json` (dedup by slug).
3. `split_groups.py <batch.json> <out_dir> 5` — K=5 sentences per GROUP file (slug-keyed, ~5× cheaper than
   1/agent, dodges the array-index bug).
4. Workflow **`scripts/ingest/dissect_batch_workflow.js`** (`yomineko-dissect-grp`), args
   `{dir, count=<#groups>}` → returns flat `[{layerB,verdict}]`. Each agent authors translation + literal +
   structure + per-token gloss/role/conjugation + particle function/explanation, AND returns
   **`grammar_keys`** = the candidate keys the sentence GENUINELY uses (strict, by meaning not substring →
   no 冷たい≠〜たい false-positives; picks affirmative/negative variant; multi-key OK).
5. Result envelope is `{summary,…,result:[…]}` — locate the `result` list (it has `layerB`), write bare array
   to `..._result.json`. `persist_batch.py --batch … --result …` (links grammar via agent keys; vocab/kanji
   from Layer-A tokenization).
6. `repair_glosses.py` (auto-fills any content token the agent skipped: from its vocab pt-gloss, else a
   closed-class dict; reports unresolved). Then `validate.py` (must be 0 errors), `export_corpus.py`, commit.
**Rebuild-from-results property:** the durable AI output is the saved `*_result.json` files. After any
persist/linking-logic change, `reset_sentences.py` + re-`persist_batch` from saved results rebuilds the bank
deterministically with NO new agent calls (only re-run the workflow if the agent's *output schema* changed).
**Still TODO in P5:** (a) raise per-topic counts to acceptance (≥3 sent/vocab, ≥5/grammar) — current batches
are seed-sized; (b) **sentence GENERATION path** for cold-start early topics (greetings/desu-wa/numbers: tiny
known-set → few Tatoeba hits) — generate i+1 JP flagged `ai_generated` then dissect same way; (c) P6
rich-lesson schema (`design/lesson_format.md`) finalized from real authored content.
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
