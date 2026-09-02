# Readiness — tests & exercises

> Area: in-lesson tests and quizzes, the exercise type system, grading contracts, the standalone drill
> banks (conjugation, roles), kanji/stroke and reading practice, checkpoints, and the assessment surface a
> Duolingo-grade app needs on top of them.
>
> Method: every number below was produced by a script run over the **exported JSON** under `corpus/` and
> `course/` (the source of truth per `CLAUDE.md`), not quoted from a document. Where a document and the data
> disagree, §6 says which is right. Validators were executed, not cited. Written 2026-09-02.
>
> **Readiness: 55%.** The in-lesson quiz layer is finished and genuinely well guarded. The assessment
> *system* around it — placement, topic tests, review sessions, mistake routing, mastery — is close to
> absent, and the practice coverage of taught material is much thinner than the lesson count suggests.

---

## 1. What this capability needs from the data

An app that tests a learner needs six things stored, not computed at render time:

| # | Requirement | Concretely |
|---|---|---|
| R1 | **An item** that can be posed and auto-graded | prompt, typed answer key, a grading rule the app and the data agree on |
| R2 | **A link from the item to what it tests** | `vocab:`/`kanji:`/`gram:`/`cap:` ref, so a wrong answer can reschedule *that* item and a test can be assembled *about* a topic |
| R3 | **A link from the item to when it is legal** | the lesson (or known-set) after which the item is answerable, so nothing untaught is ever shown |
| R4 | **Feedback** | why the right answer is right — not just right/wrong |
| R5 | **A pool per assessment unit** | enough fresh items to build a topic test, a placement probe and a retake without repeating |
| R6 | **A contract + a validator per shape**, so a broken item cannot ship | schema in `contracts/`, gate in `scripts/validate/` |

The learner-visible surfaces that consume these: the in-lesson exercise block, the JLPT exam simulator, the
practice hub (conjugation / roles / kana / particles), the SRS review session, the speaking-path checkpoint,
and — not yet existing — placement, topic tests and mistake-driven practice.

---

## 2. What exists today (verified)

### 2.1 In-lesson exercises — complete, bound, and grader-verified

`course/*/topic-*/lesson-*.json` → `exercises[]`, rendered from the body's `<exercise ref="ex:…"/>` nodes.

- **322 lesson leaves** (pre-n5 41, n5 84, n4 96, n3 101), **1,560 exercises**, mean 4.84 per lesson
  (min 0, max 7). Every one of the 1,560 is referenced exactly once by its body: the id ↔ body-ref
  bijection is green.
- **Six of the ten declared types are used**: `recognition` 532, `production` 308, `cloze` 272,
  `sentence_build` 173, `particle_choice` 144, `matching` 131. **`reading`, `listening`, `handwriting` and
  `ordering` have zero instances** anywhere in the course.
- Shape variety is real, not templated: 72 distinct type sequences; 268 of 314 lessons with exercises use
  4+ distinct types.
- Every exercise record has exactly six fields: `{id, type, prompt, answer, explanation, sentence_refs}`.
  All 1,560 carry a pt-BR `prompt` **and** a pt-BR `explanation` (3,120 prose fields).

**Guarded by** `scripts/validate/validate_exercise_contracts.py` (reads the export), which is the strongest
gate in this area: it re-implements `prototype/app/ui/LessonExercises.tsx` `normAnswer()` character for
character and was differential-tested against the real TSX over all 6,825 answer strings with 0
disagreements. It enforces the id↔body bijection, per-type answer contracts, `answer.correct ∈ choices`,
cloze `text` = filler not blanked sentence, production `answer.text ∈ answer.accept`, `sentence_build`
pieces spelling the displayed answer, matching left-column uniqueness, and "a lesson that unlocks items
renders ≥1 retrieval + ≥1 production or is exempted". Current run: **0 FAIL**, 0 production mismatches.
`validate_lessons.py` (the DB-side loader gate) is also green: 322 lessons, 0 errors, 49 warnings.

### 2.2 The eight zero-exercise lessons are held, not hidden

`course/practice_exemptions.json` lists 8 lessons (`les:n5-kanji-exame-01..03`, `les:n4-kanji-exame-01..05`),
each with a written reason. Verified consequence: those lessons **unlock 59 kanji and enrol 179 SRS cards
while rendering no practice at all**. The exemption file cannot rot (an entry matching nothing, or a lesson
that has since gained practice, is itself a FAIL).

### 2.3 Standalone drill banks — the best-built data in the area

| Bank | Items | Coverage verified | Gate |
|---|---|---|---|
| `corpus/exercises/conjugation/` | **18,524** (n5 3,072 · n4 4,853 · n3 10,599) | 1,156 of 1,157 inflectable words drilled; 23 of 24 stored forms drilled (`dictionary` is the prompt, never a target); every distractor is another real form of the same word | `validate_conjugation_exercises.py` — every form re-derived, all 18,524 readings re-romanized: ALL OK |
| `corpus/exercises/roles/` | **5,358** (n5 239 · n4 2,409 · n3 2,710) | roles: predicate 1,638, topic 1,283, object 845, subject 780, modifier 647, from 93, direction 72 | `validate_role_exercises.py` — all 5,358 re-derived from the sentences' own pattern data: ALL OK |
| `corpus/conjugations/` (source table) | 1,157 words × 17.1 forms mean | 0 inflectable vocab records missing a conjugation record | `validate_graph_edges.py` |

Both banks are Layer B with derived answer keys, so the answer cannot be wrong unless the source table is.

### 2.4 Exam banks and the simulator — data and picker both real

- **40 banks, 6,048 items**, `corpus/exam_banks/`. `validate_exam_banks.py`: ALL OK, every (level, type)
  bank at least 14× its paper count (median ~30×), with advisory ratchets held at baseline
  (okurigana-solvable 373, orthography shape-solvable 300, etc.).
- The picker in `prototype/app/lib/exam.server.ts` implements `design/exam_simulator.md` faithfully:
  separately-timed parts, seeded reproducible papers, no-repeat window, one question per passage per paper,
  `correct` stripped from the client payload and re-derived server-side at grading.
- **Listening (239 items across 5 subsections) is excluded from every paper** — the scripts exist,
  `audio: "pending"`, and the section joins only when audio lands.

### 2.5 Readings, strokes, checkpoints

- `corpus/readings/` — **286 boxes** (n5 43, n4 91, n3 152), each gated to a lesson, every kanji and content
  word inside that lesson's `cumulative_known_set` (`validate_readings.py`, max_new=0: 0 FAIL). All 286 are
  rendered in lesson bodies via `<reading ref="read:…">`. All 286 titles are now real (STATE's "140/286"
  is stale).
- `corpus/strokes/` — all **630 taught kanji** have `stroke_order`; 7 lack `stroke_lines` (n4 3, n3 4);
  162 kana stroke rows. `validate_stroke_integrity.py`: ALL OK.
- Speaking path — **72 units carry 365 checkpoint items** drawn from the exam banks (context_fill 142,
  kanji_reading 142, sentence_order 72, paraphrase 9), plus 251 drills and 213 production items, all gated
  by `validate_speaking_path.py`. **This is the only place in the product where a "test" sits between
  units.** The JLPT path has no equivalent.
- SRS enrolment — **9,453 cards** derived from lesson unlocks across 11 decks
  (`validate_srs_decks.py`: 0 FAIL). Card types: `recognition` 4,133, `production` 4,133,
  `handwriting` 691, `cloze` 496.

### 2.6 Capability registry (the skill-track routing layer)

74 capabilities, `lesson_map.json` covering 266 of 322 lessons; the other 56 are declared in
`corpus/capabilities/exemptions.json` (14 "principled", **42 "pending-capability-design"** — lessons that
unlock vocabulary only, which the registry cannot express). `validate_capabilities.py`: ALL OK.

---

## 3. Gaps

Ordered by learner impact. "AI-authorable now" means the corpus already contains everything needed and no
owner ruling is pending.

### G1. Most of what a lesson teaches, its own exercises never touch — **L**
The rule `validate_exercise_contracts` enforces is "≥1 retrieval + ≥1 production **exercise**", not "each
taught item is practiced". Measuring by surface containment (headword or kana for vocab, the character for
kanji, any stored `form`/`structure_pattern` for grammar) across each lesson's own exercise block:

| unlock type | taught | appears in its own lesson's exercises | absent |
|---|---:|---:|---:|
| vocab | 2,946 | 1,000 (33.9%) | **1,946** |
| kanji | 634 | 67 (10.6%) | **567** |
| grammar | 496 | 393 (79.2%) | 103 |

Widening to *any* lesson in the course: vocab 1,722 (58.5%), kanji 550 (86.8%). Widening again to include
the exam banks and the conjugation drill, **370 taught words (12.6%) have no retrieval item anywhere in the
corpus** — they are presented in a body, enrolled as two SRS cards, and never asked.

Why it matters: the learner meets 15 new words in a lesson, answers five questions about three of them, and
the SRS then schedules all 15 as if they had been practiced. It is the single largest quality gap between
this course and a Duolingo-grade one, and it is invisible to the gate as written.
*Depends on:* nothing. *AI-authorable:* yes (an authoring campaign, one lesson at a time, with a new
per-item coverage validator written first so the campaign has a target).

### G2. 29,930 auto-graded items ship with no feedback text — **L**
Exam items, conjugation drill items and role drill items have **no `explanation` field at all** (verified
over every key set in all 40 exam banks + both drill banks). The grading path proves it: `gradePaper()`
returns `{prompt, given, expected, correct}` and nothing else. Only the 1,560 lesson exercises explain
themselves. A learner who misses 40 of a 61-item N3 paper is told which 40 and nothing more.
Most of this is derivable rather than authored: conjugation from `class` + `form` + the grammar record's
`formation_steps` (present on 366 of 496 points), roles from the (particle, function_type) pair the answer
was derived from, kanji_reading/orthography/context_fill from the vocab record's own gloss, grammar_form
from the grammar record's `explanation` (present on all 496).
*Depends on:* A2 for the exam banks (do not author explanations onto items that are about to be
regenerated). *AI-authorable:* yes.

### G3. No placement / diagnostic test — **M**
Nothing in `design/`, `contracts/` or the data defines one; `design/learning_science.md` §4.5 specifies a
**per-stage test-out for the speaking path only**. The ingredients are closer than they look: **4,459 of
6,048 exam items (73.7%) already resolve to the lesson that introduces the item they test**, because every
`vocab:`/`gram:` ref is unlocked by exactly one lesson (`validate_unlock_ledger`). The 1,589 that do not are
`sentence_order` 871, `reading_comp` 286, listening 239, `text_grammar` 187, plus **6 items keyed to vocab
no lesson teaches** (the homograph siblings in `coverage_exemptions.json`).
Missing: (a) the stored item→lesson index (today it is a join a consumer must invent), (b) a probe item set
per level band, (c) the policy mapping a score to an entry lesson.
*Depends on:* an owner ruling on (c) — where a partial-knowledge learner is dropped, and whether placing
out seeds SRS cards. *AI-authorable:* (a) and (b) yes; (c) no.

### G4. No topic-level test — **M**
`topic.json` carries `objectives` and `lessons` and nothing else; there is no `test`/`checkpoint` entity
outside the speaking path. The pool exists: `course/outline.json` publishes per-topic `introduces_refs`, and
joining those to the exam banks gives a **median of 82 keyed items per topic**. 11 of 52 topics fall under
8 items — the five pre-N5 kana/method topics (0, correctly: their material is the kana registry), the three
`revisao` topics (0 introduced items by design) and the two `kanji-exame` topics.
*Depends on:* A1/A2 if the test is to draw on `reading_comp`/`text_grammar`. *AI-authorable:* yes.

### G5. Conjugation and role drills cannot be gated to what the learner has been taught — **M**
`cumulative_known_set` has a `conjugation-form` key on all 322 lessons and it is **empty on every one**;
`conjugation-form` unlocks across the whole course: **0** (the enum declares 20 forms). `phrase` is likewise
empty everywhere. So when a learner opens the conjugation drill, nothing in the data says whether the
causative has been introduced — the drill can only filter by JLPT level, and 10,599 of its items are N3.
The same applies to role drills (no gate field at all). `design/exam_simulator.md` "Study mode" and
`design/srs_design.md` §2 both assume known-set filtering that the data cannot currently support for forms.
*Depends on:* a lesson-metadata pass adding `conjugation-form` unlocks where each form is taught.
*AI-authorable:* yes (mechanical, from grammar unlocks + the form table).

### G6. Nothing supports mistake-driven practice — **M**
An exercise record cannot say what it tests. There is no `vocab`/`kanji`/`grammar`/`capability` ref on any
of the 1,560, and `sentence_refs` — the only structured link — is **empty on 1,246 of them (79.9%)**.
Exam items reference `vocab` (3,737) and `grammar` (728) but **never a kanji**, even though 2,379
kanji_reading + orthography items are precisely kanji tests. So "show me again what I got wrong" has no
index to run against: it would have to substring-match Japanese text.
*Depends on:* a contract edit. `contracts/lesson.schema.json` sets `additionalProperties: false` on the
exercise object and is regenerated from the data, so adding a `tests[]` ref array is a deliberate
design-owned change re-run through `validate_schema_generation_is_current.py`. *AI-authorable:* yes.

### G7. Four of the ten exercise types have no data, and two of them are load-bearing — **M**
`handwriting`: 0 exercises, no canvas or tracing component in the prototype (`KanjiStrokes.tsx` is a static
viewer), the `handwriting-input` feature is never unlocked — and yet **691 handwriting SRS cards are
enrolled** on kanji and kana decks. `listening`: 0 exercises, `listening` is a declared `card_type` with 0
cards, the `listening` feature is never unlocked, and the 239 exam scripts have no audio.
`reading` and `ordering` are simply unused (the reading skill is served by display boxes, ordering by
`sentence_build`). Also idle: `deck:phrases` is declared and holds 0 cards.
*Depends on:* an owner ruling on whether handwriting ships, and on the TTS voicing pass for listening.
*AI-authorable:* no (both are scope decisions, then app work).

### G8. Reading boxes ask nothing — **S**
All 286 boxes render as text + furigana toggle + a "Ver tradução" reveal. **Every one of the 286 already
has a matching `reading_comp` question in the exam bank** (verified: 286/286 mapped by slug; 187 also have
`text_grammar` items). Attaching one comprehension question to each box is a link plus a lesson exercise of
type `reading`, which is a declared type with a defined answer shape and an existing renderer branch.
*Depends on:* A1 (the n5/n3 passage-quality decision touches the same items). *AI-authorable:* yes.

### G9. The capability track cannot route practice for 42 lessons and 14 capabilities — **M**
`design/srs_design.md` §2 routes skill practice by `capability → grammar_keys → exam items`. Only
`grammar_form` (728 items) carries a `grammar` key; `context_fill` and `sentence_order`, which the spec
names as feeds, carry none. **14 of 74 capabilities have zero grammar_form items** (`cap:particles-core`,
`cap:i-adjectives`, `cap:na-adjectives`, `cap:transitivity`, `cap:causative`, `cap:kanji-recognition`,
`cap:kana-reading`, …), and 42 lessons are unmappable because the registry has no vocabulary capability.
Only 214 of 496 taught grammar points have any grammar_form item at all.
*Depends on:* extending the capability registry (a design decision on what a vocabulary capability is).
*AI-authorable:* yes, once the registry shape is agreed.

### G10. 17 grammar cloze cards have nothing to build a cloze from — **S**
496 grammar `cloze` SRS cards are enrolled. **17 taught grammar points have zero example sentences in
`corpus/sentences/bank.json`** (`gram:n3-kiri`, `gram:n3-tokoro-ga`, `gram:n3-sa`, `gram:n3-tatoe-temo`, …)
and **52 have fewer than three**, so a card would show the same sentence every review.
*Depends on:* sentence mining or authoring. *AI-authorable:* yes (generation is the last resort per §1.2,
so mining first).

### G11. The 8 exempted kanji lessons — **S**
59 kanji, 179 SRS cards, 0 exercises. The exemption reasons already name the two options: author practice
items, or declare a "reference" lesson role in the schema so the SRS does not enrol from it.
*Depends on:* the owner picking one. *AI-authorable:* yes, after that.

### G12. No state model for streak / mastery / attempts — **M**
There is no `contracts/` schema for `srs_card`, `review_log`, `skill_state` or an exam attempt; the shapes
exist only as prose in `design/srs_design.md` §4. The prototype stores nothing at all (no `localStorage`, no
session, no user). This is correctly an **app problem** — this run ships data — but the data side owes it
three things it does not yet have: stable per-item refs on exercises (G6), the item→lesson index (G3), and a
definition of "mastered" that can be evaluated as a query (learning_science §4.5 proposes one for stages:
"≥90% of the prior stage's words reaching a first successful review at interval ≥1 day").
*Depends on:* G3, G6. *AI-authorable:* yes for the contracts; the engine is app work.

### G13. Learner-facing copy overstates a bank by 553 items — **S**
`prototype/app/routes/practice.tsx:16` tells the learner the role drill has **"5.911 itens reais"**. The
bank has **5,358** (2,710 + 2,409 + 239). No validator looks at prototype copy —
`audit_hygiene_all_locales.py` scans corpus/course strings only. Five of the seven practice-hub tiles
(hiragana, katakana, particles, sentence, numbers) are hardcoded single-question mocks in
`practiceSession.tsx`; only `papeis` and `conjugacao` reach real data.
*Depends on:* nothing. *AI-authorable:* yes.

---

## 4. Quality risks against the near-100% goal

**Q1 — "has practice" is not "practices what it taught".** The gate that certifies 314 lessons as having
retrieval + production says nothing about *what* those items test (G1). A reviewer reading the green gate
will reasonably conclude the course drills its material; it does not. This is the risk most likely to
survive to shipping, because everything about it looks green.

**Q2 — a third of the guess rate is free.** Of 676 multiple-choice items, **493 offer 3 options and 3 offer
2**; only 180 offer the 4 that the JLPT (and the exam banks) use. A 3-option item is a 33% floor. No design
doc states an option-count rule, so nothing is being violated — but the in-lesson quiz is measurably easier
than the exam it prepares for. The 2-option items (`ex:n3-conectores-07-4` 腹/原, `ex:n3-estrutura-05-3`
放した/離した, `ex:n5-adjetivos-01-2` a yes/no) are coin flips.

**Q3 — the answer key is in the page.** Lesson exercises are graded client-side from data the SSR HTML
carries: `data-correct="true"` on the winning radio, `data-accept="[…]"` on every typed input,
`data-correct` on every `sentence_build`. This is deliberate (the quiz works with JS off) and
`validate_no_client_leak.py` does not cover it — that gate checks the built **bundle**, not per-page HTML.
Acceptable for a lesson quiz; not acceptable for anything scored. The exam simulator already does this
correctly (answers stripped, re-derived server-side at grading), so the pattern to copy exists.

**Q4 — two exam sections cannot test what their type tests, and ~1,700 items are queued for regeneration.**
Owner decisions A1 and A2 (`research/reports/PENDING.md`) are taken but unexecuted: `text_grammar` and
`reading_comp` passages at n5/n3 are unrelated Tatoeba sentences concatenated, and the bank regeneration is
GO-after-fixes. Any assessment feature built on those banks now inherits the defect and will need rework.
**Sequencing consequence: do not author explanations, topic tests or placement probes over
`reading_comp` / `text_grammar` / `sentence_order` before A2 lands.**

**Q5 — SRS enrols card types nothing can render.** 691 handwriting cards and a declared-but-empty
`listening` card type. When the review session is built, it will either skip them silently (the learner's
kanji decks quietly lose a third of their scheduled work) or fail. No validator asserts that a declared
`card_type` has a renderable source.

**Q6 — advisory ratchets are still holding real defects.** `validate_exam_banks.py` reports 373
okurigana-solvable items, 300 shape-solvable orthography items and 241 long-shot distractors at baseline.
These are items a learner can answer without knowing the answer. They are held, not fixed, pending A2.

**Q7 — 171 exercise prose fields end without terminal punctuation** (ratcheted, may only shrink) and 105
production accept-lists collapse under `normAnswer` (legal, from the punctuation repair). Cosmetic, tracked.

**Q8 — dead prototype UI.** `prototype/app/ui/{App,ReviewApp,SessionApp,StrokeOrder,store}.jsx`,
`audio.js` and a 30-entry `audioManifest.json` are imported by nothing in the React Router app. Harmless
today; a future implementer wiring "the review screen" could easily wire the mock one.

---

## 5. Recommended sequence

Ordered so that nothing is authored twice and nothing lands on top of a bank that is about to be rebuilt.

1. **Write the coverage validator before the campaign it will drive.** A new gate: every item a lesson
   unlocks is referenced by ≥1 exercise in that lesson (or is exempted with a reason). Plant-proved, with a
   ratchet seeded at today's counts (vocab 1,946 / kanji 567 / grammar 103 absent) so the campaign has a
   number that can only fall. *This is the highest-value thing in the area and it is pure data work.*
2. **Add the target-item ref to the exercise contract** (G6). One design-owned edit to
   `design/lesson_schema.md` + `_shapes.json` regeneration; backfill mechanically where the surface already
   matches, author the rest during step 3. Unblocks mistake-driven practice, capability routing and the
   coverage validator's precision.
3. **Run the per-lesson practice campaign** (G1), lesson by lesson, atomic-unit rule, ratchet falling.
   Author 4-option items by default (Q2) and use the two unused-but-defined types where they fit
   (`reading` for the 286 boxes per G8, `ordering` where word order genuinely has one answer).
4. **Publish the item→lesson index** (G3a) as a generated artifact: every exam / drill / lesson item to the
   lesson that first makes it answerable. Mechanical for 73.7% of exam items today; add
   `conjugation-form` unlocks (G5) so the conjugation bank joins it.
5. **Mechanical explanations for the two derived drill banks** (G2, conjugation + roles). Zero-judgement,
   Layer B, ~24k items, no dependency on A2.
6. **Wait for A1/A2**, then: exam-item explanations, topic tests (G4), placement probes (G3b).
7. **Owner rulings then unblock** handwriting (G7 — 691 cards are stranded until it is answered), listening
   audio, and the kanji-exame lesson role (G11).
8. **Housekeeping, any time:** fix the practice-hub count and mark the mock tiles honestly (G13), refresh
   `design/lesson_schema.md` and bump `schema_version` (§6), mine sentences for the 17 grammar points with
   none (G10), delete or quarantine the dead `.jsx` prototype (Q8).

---

## 6. Document vs. data disagreements found

| # | Claim | Reality | Which is right |
|---|---|---|---|
| D1 | `design/lesson_schema.md` (FROZEN v1) lists the block elements and `ref` namespaces the validator enforces; it has no `<reading>` element and no `read:` prefix | 286 `read:` refs live in lesson bodies and `validate_lessons.py:65` has `reading` in `BLOCK` | **Data + validator.** The doc is stale, and its own governance rule ("Refine → re-freeze → bump version") was not applied: all 322 lessons still stamp `schema_version: "1.0"` after the grammar widened |
| D2 | `design/reading_practice.md` §106: "Lessons gain `reading_refs: […]`" | No lesson has that field (0 of 322); the contract does not declare it | **Data.** The doc promises a field that was never built; the body ref is the manifest |
| D3 | `design/exam_simulator.md` header: "4,359 items"; `design/srs_design.md`: "5,013+ typed items" | 6,048 in 40 banks | **Data.** Both docs predate the paraphrase/usage/text_grammar/reading_comp/listening authoring |
| D4 | `prototype/app/lib/exam.server.ts:4`: "the 6,166-item bank" | 6,048 (118 are in `removed_items.json`) | **Data.** Comment only |
| D5 | `prototype/app/routes/practice.tsx:16` shows the learner "5.911 itens reais" | 5,358 role items | **Data.** Learner-facing overclaim, ungated (G13) |
| D6 | `design/study_system_roadmap.md` §C acceptance: "`cumulative_known_set` is extended to carry capabilities" | The set has 6 keys and none is capabilities | **Data.** An unmet plan, not a defect — but §C is not "done" |
| D7 | `design/srs_design.md` §2: skill items come from "grammar_form, context_fill, sentence_order" filtered by capability | Only `grammar_form` carries a `grammar` key; the other two carry none | **Data.** The spec is unbuildable as written (G9) |
| D8 | `design/exam_simulator.md` Study mode: "filter items to the learner's cumulative known-set" | Possible for 4,459 of 6,048 items; impossible as stored for sentence_order / reading_comp / text_grammar / listening | **Data.** The filter needs the index in step 4 |
| D9 | `STATE.md` (ag): readings "140/286 real titles, the rest still show 'Leitura'" | 286 of 286 have real pt-BR + en titles | **Data.** STATE is behind the campaign that finished |

Also worth recording: the `feature` enum in `design/unlock_enums.json` declares 16 features and the course
unlocks **4** (`srs-reviews`, `conjugation-drill`, `jlpt-sim-n5`, `jlpt-sim-n4`). There is no
`jlpt-sim-n3` in the enum although the simulator builds N3 papers, and no feature for the role drill
although it ships with 5,358 items. Feature gating is therefore not yet a usable app contract.

---

## 7. Files that matter for this area

- Data: `course/*/topic-*/lesson-*.json` (`exercises[]`), `course/practice_exemptions.json`,
  `course/outline.json`, `corpus/exam_banks/*.json`, `corpus/exercises/conjugation/*.json`,
  `corpus/exercises/roles/*.json`, `corpus/readings/*.json`, `corpus/strokes/*.json`,
  `corpus/capabilities/{registry,lesson_map,exemptions}.json`, `course/speak/*/unit-*.json`
- Contracts: `contracts/lesson.schema.json` (exercise object, `additionalProperties: false`, no `required`),
  `contracts/exam_item.schema.json`, `contracts/exercise_conjugation.schema.json`,
  `contracts/exercise_role.schema.json`, `contracts/reading.schema.json`, `contracts/speak_unit.schema.json`
- Rules: `design/lesson_schema.md`, `design/exam_simulator.md`, `design/srs_design.md`,
  `design/study_system_roadmap.md`, `design/learning_science.md` §4.5, `design/unlock_enums.json`
- Gates: `scripts/validate/validate_exercise_contracts.py`, `validate_lessons.py`,
  `validate_conjugation_exercises.py`, `validate_role_exercises.py`, `validate_exam_banks.py`,
  `validate_readings.py`, `validate_stroke_integrity.py`, `validate_srs_decks.py`,
  `validate_capabilities.py`, `validate_speaking_path.py`
- App: `prototype/app/ui/LessonExercises.tsx` (the grader of record),
  `prototype/app/lib/render-body.server.ts` (`renderExercise`), `prototype/app/lib/exam.server.ts`,
  `prototype/app/routes/{practice,practiceSession,review,exam,examPaper,conjugationDrill,roleDrill}.tsx`
