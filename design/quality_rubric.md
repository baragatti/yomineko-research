# Quality Rubric — "paid-grade" yardstick (Phase R5)

> The concrete, checkable definition of "best paid-grade Japanese course in Brazil" used as the **pilot gate
> (P5)** and **final QA (P7)** (spec §10.11). Grounded in the R2 research
> ([curricula](../research/references/curricula_sequencing.md), [SLA](../research/references/sla_evidence.md),
> [BR market](../research/references/brazil_market.md), [BR-PT pedagogy](../research/references/brpt_pedagogy.md)),
> the R3 coverage numbers, and the spec's non-negotiables. **Learner-facing artifacts are pt-BR; this rubric is
> the internal checklist.**

## How to use it
- **Six dimensions**, each scored **0–4**. **Plus hard gates** (pass/fail) that no score can override.
- **Pass bar:** every dimension **≥ 3** *and* **all hard gates pass**. The pilot topic must clear this before
  mass production; every topic must clear it before its commit in P7.
- Score with evidence (cite the lesson/sentence/record id that proves or breaks each line). A dimension scored
  <3 blocks the unit; fix and re-score.

| Score | Meaning |
|------:|---------|
| 0 | Absent / wrong |
| 1 | Present but below free-tier quality |
| 2 | ~ free-tier (Duolingo/YouTube) quality |
| 3 | **Paid-grade** — matches the best Brazilian paid courses |
| 4 | Beats them — best-in-Brazil on this dimension |

---

## HARD GATES (pass/fail — any failure blocks the unit)
- **G1 — No hallucinated Japanese.** Every kanji reading used exists in KANJIDIC2 for that kanji; every token
  `lemma` exists in JMdict. Zero unresolved reading/lemma mismatches (spec §7.1).
- **G2 — Analyzer owns the skeleton.** `surface/lemma/reading/pos` come from SudachiPy and are unaltered by the
  LLM (spec §7.2).
- **G3 — Provenance complete.** Every record has a non-empty `source` and correct layer; every `ai_generated`
  and every Layer C item has `needs_review: true`. No orphan records (spec §7.5).
- **G4 — By-ID rule.** No lesson or exercise embeds sentence text/dissection — IDs only (spec §5.5 hard rule).
- **G5 — Clean-room.** Zero verbatim/lightly-reworded text, examples, or explanations from the local course;
  zero instructor/course names anywhere (spec §1.4, §10.13).
- **G6 — pt-BR + style.** All learner-facing content is Brazilian Portuguese, follows Appendix B (terms
  introduced on first use; romaji as support not crutch; consistent grammar-term glossary).

---

## Dimension 1 — Accuracy & provenance  (weight: critical)
The corpus must be *verifiable, not generated-and-prayed-over*.
- **1a** Layer A facts trace to a named dataset; Layer B validated against Layer A; Layer C flagged for review.
- **1b** pt-BR translations are faithful (round-trip / EN cross-check sane; §7.7) and natural, not literal-MT.
- **1c** Level tags carry `level_confidence` + `level_sources` from **≥3 reconciled lists** (§1.5); KANJIDIC2
  `jlpt` field NOT used as the modern level.
- **1d** Per-reading `introduced_at_level` is correct (kanji taught at N5 with one reading, N4 with another).
- **3 = paid-grade:** everything above holds; **4:** plus pitch accent present and correct on new vocab.

## Dimension 2 — Explanation depth (the real differentiator)
R2 finding: the Brazilian market is grammar-light (Marugoto subordinates grammar; pop-courses lean on
engagement). Explanations are where we win.
- **2a** Each grammar point has an **original** pt-BR `explanation_pt` + `formation_pt` + `nuance_pt`
  (register, when/why, pitfalls) — clear to a true beginner *and* informative mid-course.
- **2b** **"Armadilha/Vantagem PT" callouts** where relevant (SOV hold-the-verb, は vs が as "quanto a…",
  particles-are-postpositions, no articles/agreement, counters, mora/length, ん-not-a-nasal-vowel,
  です/ます devoicing, você→teineigo on-ramp, romaji-≠-português).
- **2c** Grammar terms (partícula, tópico, transitivo…) defined on first use; consistent terminology.
- **2d** Kanji taught component-first with a **pt-BR** mnemonic (not translated from English) + meaning.
- **3:** explanations are deeper and clearer than the paid incumbents; **4:** "como ninguém nunca viu antes" —
  a learner says the *why* finally clicked.

## Dimension 3 — Example richness & dissection quality
- **3a** **≥3 dissected sentences per vocab**, **≥5 per grammar point** (raise per R3 where sources allow).
- **3b** Every sentence follows the §6 dissection standard: every token has an in-context `gloss_pt`, **every
  particle has `function_pt` + `explanation_pt`**, whole-sentence `structure_explanation_pt`.
- **3c** **Selection over generation** for the *Japanese*: real Tatoeba sentences preferred; `ai_generated`
  minimized, within the per-item cap, always flagged + `needs_review`. (R3: PT is generated as Layer B even for
  selected sentences — that's expected; the *Japanese* must be real wherever possible.)
- **3d** **i+1 discipline:** sentences introduce ≤1 item beyond the lesson's cumulative known set; low-`new_items`
  preferred.
- **3e** Both SudachiPy split modes (A+C) present; mode-A subunits linked to their mode-C word.
- **3:** every item meets thresholds with natural sentences; **4:** rich bank (hundreds/topic) + audio present.

## Dimension 4 — Sequencing soundness
- **4a** **Dependency-correct** (no て-clauses before て-form, no relative clauses before plain past, no
  comparatives before adjectives). [R2 curricula]
- **4b** **i+1 pacing:** ideally ≤1 new grammar point per lesson; prior items spiral into later lessons.
- **4c** **Chunk sizes** within evidence-based bands: ~3–5 new grammar / ~15–25 new vocab / ~5–10 new kanji
  per lesson. [R2 §12]
- **4d** **Family-driven:** core member first (`is_core`), then variations by `intra_order`; governing rule
  taught when its family needs it; families importance-ranked.
- **4e** Register-explicit, **ます-default + dictionary-form-early** (beats Minna's late plain form). [R2 §10]
- **4f** Katakana introduced right after hiragana; romaji weaned by ~unit 3. [R2, BR-market romaji-crutch gap]
- **3:** order is defensible against the best curricula; **4:** demonstrably better-ordered than incumbents.

## Dimension 5 — Completeness & coverage
- **5a** 100% of reconciled N5+N4 kanji/vocab present to acceptance §10.1–2; every grammar point enumerated.
- **5b** Every reconciled item has exactly one **introducing lesson** (may recur).
- **5c** **Superset of the Phase L concept map** — our coverage ≥ the local course's, reorganized/improved
  (§10.13), with the gaps-to-beat addressed (pitch accent, JLPT mapping, katakana/adjective/time-vocab
  sequencing, casual↔polite integration).
- **5d** **Functional/Japan-life coverage**: self-intro, numbers/time/dates, shopping/money, food, directions/
  transport, daily routine, family, work basics, forms/signs — useful for living/working in Japan.
- **5e** Pre-N5 from absolute zero (kana, pronunciation, pitch intro, survival greetings).
- **3:** complete to spec; **4:** plus functional contexts richer than any incumbent.

## Dimension 6 — Review-readiness & LLM-navigability
- **6a** `needs_review` queue assembled, **AI-generated first** (§7); a Japanese teacher could sign off directly.
- **6b** `INDEX.md` accurate; project modular (many small, consistently-schema'd files) (§10.14).
- **6c** The **§1.7 cross-cutting queries** all return correct results from stored links; schema level-agnostic.
- **6d** Each lesson exports both `.json` (app/LLM-ready) and `.md` (human review).
- **3:** review-ready & navigable; **4:** a new LLM/teacher can extend it with zero hand-holding.

---

## Pedagogy-fit checklist (SLA engine — derived from [sla_evidence](../research/references/sla_evidence.md))
These are *design presence* checks (the corpus must *enable* them even though SRS logic is out of scope now):
- [ ] **Retrieval-first:** exercises require *production/recall*, not just re-recognition (≥1 recall + ≥1
  production exercise per lesson). [strong evidence]
- [ ] **Spacing-ready:** items chunked & tagged so a later SRS can schedule them (introduce → ~D1 → D3 → D7 …).
- [ ] **Frequency-ordered vocab**; texts kept at ≥95% known-token coverage.
- [ ] **Pushed output:** ≥1 speaking/sentence-construction task per lesson with an answer key + explanation.
- [ ] **Interleaving hooks:** confusable sets (は/が, transitive/intransitive, look-alike kanji, counters,
  length minimal pairs) grouped as families for mixed review.
- [ ] **Dual coding / mnemonic:** vocab/kanji carry an image hook + pt-BR mnemonic where useful.
- [ ] **Pitch/prosody:** new vocab carry pitch where available; pronunciation thread present (selective, N5).

---

## Pilot-topic acceptance (P5 gate) — concrete yes/no
1. Is every Japanese sentence correct and natural (spot-check by reading)?  Y/N
2. Do the dissections genuinely teach (token glosses + particle explanations useful, not mechanical)?  Y/N
3. Are the lesson texts paid-grade (deeper/clearer than incumbents), in good pt-BR?  Y/N
4. Did schema v2 hold up with no awkward/lossy cases (else log a schema revision)?  Y/N
5. Was Tatoeba coverage as predicted in R3 (and was generation within cap)?  Y/N
6. Do all hard gates G1–G6 pass on the pilot?  Y/N
7. Does the pilot score ≥3 on all six dimensions?  Y/N
→ All "Y" required before scaling beyond the pilot.

## Scoring sheet (copy per unit into `reports/validation.md`)
```
unit: <topic/lesson id>
D1 accuracy/provenance: _/4   evidence:
D2 explanation depth:   _/4   evidence:
D3 example richness:    _/4   evidence:
D4 sequencing:          _/4   evidence:
D5 completeness:        _/4   evidence:
D6 review/navigability: _/4   evidence:
hard gates G1..G6:      PASS/FAIL each
pedagogy-fit checklist: n/7 present
VERDICT: PASS (all dims>=3 & all gates pass) | BLOCK (list fixes)
```

---

## P8 — Post-authoring quality pass: standing rules + findings (2026-06-17)

A full quality review of all 213 authored lessons (one reviewer per slice) plus corpus-wide audits produced
these **standing authoring rules** (enforce in every future author/polish prompt) and **findings**.

### Standing authoring rules (hard)
1. **NO emoji in learner text.** Never put `💡`/`⚠`/`✅`/etc. inside `<text>`, `<heading>`, `<check>`, exercise
   prompts, or explanations. Semantic cues come from the BLOCK TYPE only:
   `<note type="l1-advantage|l1-pitfall|tip|warning|culture|example">` (the app renders any icon). Enforced by
   `scripts/ingest/strip_emoji_lessons.py`.
2. **Brazilian pt-BR with correct diacritics, always.** Accent-stripped prose (`nao`/`voce`/`licao`) is a defect.
   Audit: every lesson with >300 latin chars must have a diacritic ratio ≥1.5% (corpus median ~4%).
3. **No meta/orchestration text in any learner field.** Never `"Authored lesson…"`, `"Polished…"`,
   `"placeholder"`, `"reference format"`, `"returned as structured output"`, `"Fixed…"`. The `body`/`description`
   are what the learner reads, never a note to the developer. A content lesson's `body` must be the full tagged
   lesson (≈3000+ chars).
4. **No over-escaped quotes.** Quoted phrases use plain `"…"`, never backslash-quote. Enforced by
   `scripts/ingest/fix_escape_artifacts.py`.
5. **Examples: PREFER REAL (sourced) over AI-generated.** When featuring example sentences (and when an exercise
   reuses a sentence), prefer `ai_generated=0` (Tatoeba/JEC) over AI-generated; AI is the fallback only.
   Selection order: real first, then shortest, level ≤ the lesson's module. Implemented in
   `scripts/ingest/enrich_examples.py`.
6. **Enough practice, but lessons stay LIGHT.** Target ~4–6 exercises (mix retrieval + production) and ~3–5
   featured example sentences per content lesson; recap/kana lessons can have fewer. Do NOT pad prose; content
   lessons cluster ~2.0k pt-BR chars. Example richness comes from compact `<sentence mode="card">` bank cards,
   not longer prose.

### Findings (this pass)
- **Kanji coverage is correct + balanced.** All 80 N5-consensus kanji are taught inside the N5 course and all
  170 N4-consensus kanji inside the N4 course; 0 level/module mismatches; max 6 kanji/lesson (mean 2.2). Three
  kanji (米 / 港 / 市) are taught but have consensus level NULL (author-added) — cosmetic.
- **Sentence-bank usage is constrained by linkage, not by will.** Bank = 4,959 dissected (2,745 real Tatoeba +
  2,214 AI). Only ~2,007 are linked to a PLACED grammar point (1,337 real); ~2,952 have no grammar link, so they
  cannot surface as grammar examples. We feature 511 (~2.4/lesson), already real-leaning (~68% real). Enrichment
  added 63 real sentences to 51 lessons; many N4 grammar points have few/no bank sentences. **Backlog to raise
  usage:** (a) link more bank sentences to N4 grammar points (a tagger pass); (b) surface vocab-example sentences,
  not only grammar; (c) re-mine real N4-grammar sentences (JEC/Tatoeba) before falling back to AI generation.
- **Volume vs. incumbent:** see `research/local-course-insights/course_volume_comparison.md` — we exceed total
  text ~2.7x and the typical lesson is denser; the remaining gap is depth on ~12 flagship topics + Japanese
  example density (partly addressed by enrichment). Audio is an out-of-scope product-roadmap item.

### Tooling safety rules (learned the hard way, 2026-06-17)
Mechanical text fixers run over EVERY string field, so they must be **key-aware**:
7. **Never rewrite identifier fields.** `slug`, `topic`, any `ref` (unlocks/needs/sentence_refs/item_refs/exercise
   slugs/body `ref="…"`) must stay ASCII. An accent fixer that walked all fields once turned `n5-numeros-tempo`
   into `n5-números-tempo` and broke loading. Fixers skip `{slug, topic, ref}` and, inside `body`, only touch text
   BETWEEN tags (never attribute values). Guard: `audit` scans for non-ASCII in identifiers + accented filenames.
8. **Never trim word-separating spaces at tag boundaries.** Authors put the single space that separates two
   adjacent inline tags INSIDE a `<text>` run; trimming `(<text>) +` / ` +(</text>)` runs words together
   ("você consegue" → "vocêconsegue"). Emoji/whitespace cleanup may only collapse 2+ spaces to 1.
   `scripts/ingest/fix_boundary_spaces.py` repairs damage; the run-together scan guards against regressions.
