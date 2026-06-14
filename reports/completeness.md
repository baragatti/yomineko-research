# Completeness check — is the foundation done? (2026-06-14)

> Verification before mass production, so **P5 onward is pure scaling**. Run
> `scripts/validate/completeness_audit.py` to regenerate the numbers. **Verdict: the foundation +
> dissection template + all per-item content are COMPLETE.** What remains is volume (sentence bank +
> lessons) and QA, not missing capability.

## ✅ Complete & verified

### Dissection standard (§6) — verified on all 19 existing sentences
Every sentence carries the full §6 model, and the **Workflow-produced batch dissections are as complete as
the hand-authored pilot** (so scaling reproduces a complete template):
- `pt`, `pt_literal`, `kana`, `romaji`, `structure_explanation_pt` — 100%
- **Every content token** (名詞/動詞/形容詞/…) has `gloss_pt` **and** `role_pt` — 66/66
- **Every particle** has `function_pt` **and** `explanation_pt` — 48/48 (the "what/why/how" the owner asked for)
- Verb tokens have `conjugation_note_pt` (e.g. "forma て de 行く") — 39/39
- `sentence_vocab` / `sentence_kanji` / `sentence_grammar` links — 100%
- Mode-C tokens always; **mode-A subtokens stored only when they differ from C** (correct — simple sentences
  have A==C, so no duplicate rows; this is by design, not a gap)

### Per-item content — all populated
- **Kanji (250):** `meanings_pt`, `strokes`, `kanjivg_ref`, radicals/components, ≥1 reading, level
  confidence/sources — all 100%. Per-reading `introduced_at_level` seeded (heuristic) on on/kun readings that
  appear in leveled vocab; **`example_vocab_ids` now filled** (438 readings).
- **Vocab (1,359):** `gloss_pt` on **all 4,061 senses**, `romaji`, `pos`, ≥1 `form`, level conf/sources —
  100%; **pitch accent on 1,221 (90%)**.
- **Grammar (364):** `label_pt` + `explanation_pt` + `formation_pt` + `nuance_pt` (with PT-speaker pitfalls) —
  **364/364**; `register` 100%; `grammar_related` contrast links populated.
- **Families (395):** every vocab/kanji/grammar item ∈ ≥1 family; `importance_rank` + `is_core` set.
- **Provenance:** `source` on every row; `needs_review` on all Layer-B (senses, sentences) and Layer-C
  (grammar) content.
- **Outline:** 35 topics across pre-N5/N5/N4; every reconciled item has an introducing topic.

## ⏳ PENDING (the explicit to-do for P5 → P7)

### P5 — sentence bank (the bulk; engine proven on te-form)
- [ ] Dissect to **≥3 sentences per vocab** (now 5/1,359) and **≥5 per grammar point** (now 2/364), across all
      35 topics, within each topic's i+1 known-set. Real Tatoeba first; AI-generate to fill, all flagged.
      Recipe in `STATE.md`. This is the large multi-session grind.

### P6 — courseware
- [ ] Author **lessons per topic** (now 1) — dense pt-BR + structured exercises, sentence refs BY ID.
- [ ] `topic.objectives_pt` (0/35) and `course_module.overview_pt` (0/3) — authored with the lessons.
- [ ] `lesson.cumulative_known_set` materialization (for i+1 verification).

### P7 — QA & acceptance
- [ ] Full `validate.py` run over the whole bank; finalize `reports/validation.md` + `reports/stats.md`.
- [ ] **Coverage comparison vs the Phase L+ `concept_inventory.md`** (confirm superset; #13).
- [ ] **§1.7 cross-cutting query tests** (the 4 sample graph queries return correct results; #10).
- [ ] Assemble the **needs_review queue** (AI-generated first) for teacher sign-off (#8).
- [ ] `ATTRIBUTION.md` commercial-use sign-off (owner decision; ShareAlike sources) (#7).

### Quality improvements (non-blocking; can run during/after P5)
- [ ] Per-reading `introduced_at_level` beyond the 42% heuristic seed — P5's SudachiPy *realized* readings per
      token can refine which reading each kanji takes at each level.
- [ ] Semantic-field families currently use a topic-theme fallback; enrich with real semantic themes (food,
      family, body, transport…) via a classification pass (optional).
- [ ] A dedicated CC-licensed **frequency list** (sequencing currently uses KANJIDIC2 `freq` + JMdict common
      markers; a fuller freq list would refine ordering — optional, §3.5).

## How to proceed with confidence
The dissection function, validation suite, level/provenance model, and all per-item Layer-B/C content are
done and verified. P5/P6 is **repeated application** of the proven `prepare_batch → Workflow → persist_batch`
(sentences) and lesson-authoring pipelines, one topic at a time (one workflow at a time to avoid rate-limits).
