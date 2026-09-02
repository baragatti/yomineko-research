# Readiness — the JLPT course path (zero → N5 → N4 → N3)

_Area: `jlpt_course_path`. Written 2026-09-02 against the committed export at `3bfecf38`. Every count
below was produced by running a script over `course/` + `corpus/` + `contracts/`, or by running a
validator from `scripts/validate/`. No number here is quoted from a document; where a document and the
data disagree, the disagreement is named._

**Headline.** The spine is real and it holds. 322 authored lessons in a four-tier manifest, 4,137
introduce-once unlocks, a `cumulative_known_set` that is provably the running union of those unlocks,
and a hard gate that no lesson body may reference an item it has not yet taught. A learner can walk
pre-N5 → N5 → N4 → N3 in a defined order and never meet an untaught reference. What is thin is
everything downstream of "the item was introduced": **only 40% of the 2,946 words and 11% of the 634
kanji the course unlocks are ever touched by an exercise in the lesson that unlocks them**, four of the
ten contracted exercise types have zero instances (including both JLPT-graded skills, `listening` and
`reading`), and **the exam simulator that is supposed to certify a finished level draws from banks that
no validator checks for level-appropriateness** — four of nine paper sections cannot fill a
level-appropriate paper at all. N3 additionally ends in a dead end: one review lesson, no
exam-simulator unlock, and no `feat:jlpt-sim-n3` in the enum.

---

## 1. What this capability needs from the data

A Duolingo-shaped JLPT path that ends in a defensible "you are ready for N5/N4/N3" needs seven things
from the corpus, each with data, a contract, and a validator:

| # | Requirement | Concretely |
|---|---|---|
| R1 | **An ordered, gapless tree** | manifest → course → topic → lesson, every tier agreeing, every lesson reachable in exactly one position. |
| R2 | **A monotone knowledge state** | per-lesson `cumulative_known_set` that is the union of all prior `unlocks`, so any consumer can ask "does the learner know X yet" without replaying the course. |
| R3 | **A prerequisite model** | `needs[]`, so the tree is a DAG and not merely a list — the thing that makes branching, skipping and remediation expressible. |
| R4 | **Practice per introduced item** | every unlocked vocab/kanji/grammar item retrieved and produced at least once while it is new, not only enrolled in a card. |
| R5 | **Renderable Japanese at the learner's level** | every kanji the learner cannot read carries a reading; every example sentence inside the i+1 budget. |
| R6 | **Assessment that matches the syllabus** | exam items whose Japanese is inside the level's taught set, in every section the paper spec declares, with enough gated items to resist memorization. |
| R7 | **Progression semantics** | what "complete" means, where the checkpoints are, how a returning or non-beginner learner enters. |

---

## 2. What exists today (verified)

### 2.1 The tree (R1) — complete and gated

`validate_course_chain.py`: **4 courses, 52 topics, 322 lessons, 378 chained files, 0 FAIL** — tiers
agree, topic `unlocks_summary` and `course/outline.json` recompute exactly from the lesson leaves, and
every published JSON under `course/` + `corpus/` (543 files) is catalogued.

| level | topics | lessons | exercises | vocab | kanji | grammar |
|---|---:|---:|---:|---:|---:|---:|
| pre-n5 | 6 | 41 | 96 | 24 | 0 | 0 |
| n5 | 14 | 84 | 427 | 684 | 103 | 151 |
| n4 | 17 | 96 | 470 | 642 | 187 | 213 |
| n3 | 15 | 101 | 567 | 1,596 | 344 | 132 |
| **total** | **52** | **322** | **1,560** | **2,946** | **634** | **496** |

The course teaches **100% of the corpus's own leveled registries**: 103/103 N5 kanji, 177/177 N4,
350/350 N3; 151/151 N5 grammar, 213/213 N4, 132/132 N3; 1,596/1,596 N3 vocab. Nine N5/N4 vocab records
are unlocked by nobody, all nine homograph siblings awaiting a placement decision, each written out in
`course/coverage_exemptions.json`. `validate_unlock_ledger.py`: **4,137 unlocks, 4,137 distinct refs,
ALL OK** — introduce-once holds in published slug space.

### 2.2 The knowledge state (R2) — provably correct

I rebuilt the course order from `course/manifest.json` → `course/*/course.json` (topic `order`) →
`topic.json` (lesson `order`) and replayed all 322 `cumulative_known_set` records:

- **0 monotonicity violations** — no set ever shrinks.
- **0 mismatches** against the running union of `unlocks` — the stored set is exactly derivable.
- Final state: vocab 2,946 · kanji 634 · grammar 496 · kana-family 57.

`validate_lesson_gating.py` (hard): **322 lessons, 5,290 item refs, 0 FAIL**; every ref a body renders
is inside that lesson's own `cumulative_known_set`, with 8 held exceptions written out in
`course/gating_exemptions.json` (one forward reference, seven homograph placements).

`validate_srs_decks.py`: **4,133 cards over 322 lessons, 12 decks, 0 FAIL**. Card count equals item
unlock count exactly (2,946 + 634 + 496 + 57), so every introduced item is enrolled for review.

### 2.3 Lesson bodies and exercises

`validate_lesson_bodies.py`: 322 lessons, 7,760 refs, 3,971 furigana spans, 11,800 plain-text fields,
0 FAIL. `validate_exercise_contracts.py`: 1,560 exercises, exact bijection with `<exercise ref>` in the
bodies, per-type answer keys graded exactly as `LessonExercises.tsx` grades them, 0 FAIL.

Objectives are specific and near-unique: 1,074 objective strings, **1,066 distinct** (the only repeats
are 7 instances of "Escrever cada kana da família na ordem correta dos traços" across the kana
families). Bodies are substantial: median 6,698 characters, 25.9–37.2 `<jp>` spans per lesson.

### 2.4 Capabilities

`corpus/capabilities/registry.json` holds 74 capabilities covering **100% of the 496 taught grammar
points** (n5 151/151, n4 213/213, n3 132/132); `lesson_map.json` maps 266 lessons; the 56 unmapped
lessons are itemised in `corpus/capabilities/exemptions.json`. `validate_capabilities.py` and
`validate_graph_edges.py` both gate it.

### 2.5 Exam banks

40 files, **6,048 items**, `validate_exam_banks.py` green: stem/answer agree with the record the item's
slug names, option sets distinct under NFKC + kana folding, blank integrity, every `(level, type)` bank
at least 3× its paper count.

---

## 3. Gaps

### G1. Four of the ten contracted exercise types have zero instances — S/L, AI-authorable (three of four)

`contracts/lesson.schema.json` and `design/lesson_schema.md` both freeze ten `type` values. The data
uses six:

| in use | count | contracted, count 0 |
|---|---:|---|
| recognition | 532 | `reading` |
| production | 308 | `listening` |
| cloze | 272 | `handwriting` |
| sentence_build | 173 | `ordering` |
| particle_choice | 144 | |
| matching | 131 | |

`reading` and `listening` are the two JLPT-graded skills. `handwriting` is worse than absent: the SRS
schedules **691 handwriting card instances** (every kanji and kana card carries the type, per
`design/unlock_enums.json` `deck_registry`), the stroke data exists (1,233 `stroke_order` + 162
`stroke_kana` + 2,098 `stroke_lines` records), and `feat:handwriting-input` is in the feature enum —
but **no lesson ever unlocks it**, so the course schedules reviews for a mode it never turns on.
`ordering` duplicates `sentence_build` in the frozen schema and should probably be retired rather than
filled. **Depends on:** nothing for `reading` and `ordering`; `listening` depends on the audio decision
(owner will AI-generate post-research); `handwriting` depends on an input widget.

### G2. Introduced items get almost no in-lesson practice — L, AI-authorable

For each lesson I took the items it unlocks, expanded each to all its surface forms
(headword/kanji/kana/reading for vocab, the character for kanji, `forms[]` for grammar) and searched
that lesson's own exercise JSON:

| | practiced in its own lesson's exercises |
|---|---|
| **grammar** | 427 / 496 = **86.1%** (n5 84.8, n4 87.8, n3 84.8) |
| **vocab** | 1,175 / 2,946 = **39.9%** (n5 40.5, n4 16.2, n3 48.3) |
| **kanji** | 67 / 634 = **10.6%** (n5 20.4, n4 9.1, n3 8.4) |

This is arithmetic, not authoring sloppiness: 1,560 exercises cannot cover 4,133 introduced items
(0.38 exercises per item). 47 lessons have exercises that touch none of their own new vocab or kanji at
all. For the learner: 1,771 words and 567 kanji are introduced, enrolled in a card, and never once
retrieved inside the lesson that taught them. Everything rests on the SRS, which is app-side and not
built here. **Size L** — closing it to even one retrieval per item is roughly 2,500 new exercises.
**Depends on:** nothing; the answer keys are derivable from the registries the same way the existing
1,560 were.

### G3. The exam banks are not level-gated, and nothing checks that they are — L, AI-authorable plus one owner call

`validate_exam_banks.py` checks answer keys, distinctness, blank integrity and sufficiency. **It never
checks that an item's Japanese is inside the level's taught set**, and neither does any other of the 39
validators. Measuring every item's visible text (stem + question + correct + distractors + pieces)
against the corpus's own kanji levels:

| section | n5 clean / bank | paper | n4 clean / bank | paper | n3 clean / bank | paper |
|---|---|---:|---|---:|---|---:|
| kanji_reading | 108 / 400 | 7 | 132 / 400 | 7 | 215 / 400 | 8 |
| **orthography** | **3 / 379** | 5 | 7 / 400 | 5 | 40 / 400 | 6 |
| context_fill | 8 / 235 | 6 | 9 / 368 | 8 | 56 / 389 | 11 |
| grammar_form | 99 / 129 | 9 | 250 / 299 | 8 | 272 / 300 | 13 |
| sentence_order | 261 / 273 | 4 | 294 / 298 | 4 | 292 / 300 | 5 |
| **paraphrase** | 3 / 52 | 3 | **1 / 60** | 4 | 28 / 71 | 5 |
| usage | 8 / 52 | 0 | 5 / 60 | 4 | 49 / 71 | 5 |
| text_grammar | 27 / 33 | 2 | 50 / 61 | 3 | 92 / 93 | 4 |
| reading_comp | 22 / 43 | 3 | 45 / 91 | 4 | 134 / 152 | 4 |

Read that as: **N5 orthography (3 clean items, paper needs 5) and N4 paraphrase (1 clean, needs 4)
cannot produce a single level-appropriate paper.** N5 paraphrase, N5/N4 context_fill, N4 orthography and
N4 usage clear 1× but fall below the 3× anti-memorization floor the suite enforces everywhere else.
Concrete examples: `kr:n5:1` tests 嗚呼 (嗚 is not in the kanji registry at all); `or:n5:3` and `pp:n5:3`
test 青, which the registry levels N4; `gf:n5:1087` is 痔（　）。

Two different defects are tangled here and should be separated:

- For `kanji_reading` / `orthography` the kanji **is** the question, so furigana cannot rescue it. These
  banks print the kanji spelling of words the JLPT would write in kana at that level. The fix is
  selection, and it is only possible where enough level-clean words exist — kanji_reading yes
  (108/132/215), orthography no at N5/N4.
- For `context_fill` / `paraphrase` / `usage` / `reading_comp` the above-level kanji is incidental to the
  question, and **full furigana coverage (already approved) neutralizes it**. That reframes those rows
  from "cannot ship" to "ships once furigana is complete".

254 characters used by vocab records have no kanji record at all
(`design/unregistered_kanji_chars.json`, generated and gated by `validate_graph_edges.py`), which is why
some items show unregistered rather than above-level characters.

**Depends on:** the A2 regeneration decision (already GO) — the level gate belongs in the builder and in
a new validator, not in per-item patching. The nine enumerated builder fixes in
`research/reports/exam_bank_regen_review.md` do **not** include a level gate; it must be added to that
list before regeneration bakes the defect back in.

### G4. 286 "reading passages" are concatenated unrelated sentences — L, AI-authorable (Layer C)

Already decided by the owner (`PENDING.md` A1 → option (a), author real passages). Verified scope, since
the decision was taken without a count of the blast radius:

- **286 reading records** (n5 43, n4 91, n3 152), every one a 2–6 sentence concatenation. Example
  `read:n3-causa-01-01`: 木のおかげで雨にぬれずにすんだ。それはわたしのせいではなかった。風が強いのはビル風のせいです。私がいるのは父のおかげです。おかげで元気にしております。 — five unrelated sentences sharing おかげ/せい.
- They are **embedded in 235 of the 322 lessons** via `<reading ref>`, so this is not only an exam
  problem; it is the reading material of 73% of the course.
- **473 exam items** depend on them (n5 43+33, n4 91+61, n3 152+93 across `reading_comp` + `text_grammar`).
- Titles are no longer the problem: all 286 are distinct and authored, 0 generic "Leitura" remain.

The reading_comp questions are answerable from the first sentence alone (`rc:n3:n3-causa-01-01` asks
どうして雨にぬれなかったのか, answered by sentence 1), so the remaining four sentences are pure noise.

### G5. `needs[]` is empty on all 322 lessons — M, AI-authorable

Verified: **0 of 322** lessons carry a non-empty `needs`. `validate_lesson_gating.py` prints
`ADVISORY: 0 'needs' entries across 322 lessons — the prerequisite model is empty, so check C proves
nothing about linearity.` `design/courseware_architecture.md` §3 defines it as the DAG edge set and §4
gives its shape. Without it the tree is a linked list: no skipping, no remediation path, no "you are
missing X before Y", and no way to express the two legitimate cross-strand dependencies the design doc
names (a grammar lesson needing a form from another strand; kana needed to render furigana). Owner has
approved populating it. It is derivable mechanically from the `cumulative_known_set` deltas each lesson
body actually consumes, which is stronger than hand-authoring.

### G6. Furigana: 875 kanji spans carry no reading, and the gate cannot see them — M, AI-authorable

Across the 322 bodies: 10,496 `<jp>` spans, 4,332 containing kanji, 3,457 with `reading=`, **875
without** (n4 422, n5 246, n3 204, pre-n5 3) — 20.2% of kanji spans. In
`scripts/validate/validate_lesson_bodies.py` the furigana check is driven by

```
JPTAG = re.compile(r'<jp\s+reading="([^"]*)"\s*>(.*?)</jp>', re.S)
```

which only matches spans that already carry the attribute, so a kanji span with no reading is invisible
to it. The suite README describes this check as "`<jp reading>` non-empty kana-only **whenever the span
has kanji**", which overstates what the code does. Owner has approved full coverage; the validator needs
a second check (kanji base ⇒ attribute present) landed alongside it, or the gap reopens silently.

### G7. Only 4 of 16 app features are ever unlocked, and `feat:jlpt-sim-n3` does not exist — S, AI-authorable

| lesson | unlocks |
|---|---|
| `les:pre-n5-hiragana-01` | `feat:srs-reviews` |
| `les:n5-te-form-01` | `feat:conjugation-drill` |
| `les:n5-revisao-03` | `feat:jlpt-sim-n5` |
| `les:n4-revisao-03` | `feat:jlpt-sim-n4` |

Never unlocked: `furigana-toggle`, `romaji-toggle`, `kana-input`, `kanji-lookup`, `handwriting-input`,
`particle-drill`, `phrase-builder`, `listening`, `voice-mode`, `find-correct-kanji`,
`find-correct-particle`, `visual-novel`. And `jlpt-sim-n3` is **not in the enum at all**, although
`prototype/app/lib/exam.server.ts` declares `LEVELS = ["n5","n4","n3"]` and all 14 N3 banks exist. So the
N3 path has no completion moment: `top:n3-revisao` is **one lesson with 4 exercises** (against
`top:n5-revisao` 3 lessons / 19 exercises and `top:n4-revisao` 3 / 18) and unlocks no feature. That is
the one true dead end in the tree.

### G8. The N3 load profile inverts — M, needs owner/teacher judgement

Median new items per lesson: **n5 8 vocab / 1 kanji / 2 grammar; n4 7 / 2 / 2; n3 18 / 3 / 1** (n3 max
21 vocab in one lesson; `les:n3-deveres-03` introduces 31 items against 6 exercises). N3 introduces
**2.4× the vocabulary per lesson** of N4 while introducing **fewer grammar points in total** (132 vs
213) — at exactly the level where grammar density normally rises. Exercise count does not move with it
(n3 mean 5.6 per lesson vs n4 4.9), so the exercises-per-new-item ratio collapses from ~0.45 at N4 to
~0.25 at N3. N3 is also the only level with **no lesson rendering 4 or more example sentences** (n4: 82
of 96 lessons do; n3: 0 of 101), and 48 of its 101 lessons render none at all. This is a sequencing
decision, not a bug — but it is the shape that makes N3 the level a learner quits on.

### G9. Reading material is thin and partly unlinked — M, AI-authorable

The course renders **624 sentence links / 604 distinct sentences** out of a 5,889-record bank (10.3%).
**116 of 322 lessons render no corpus sentence at all** (pre-n5 41 — structurally fine; n3 48; n5 15;
n4 12). Bodies do carry inline Japanese (10,496 `<jp>` spans), but that text is not a dissected corpus
sentence: no token gloss, no particle roles, no modal, no i+1 accounting. `validate_lesson_gating.py`
also reports **178 of 624 sentence links above their lesson level and 147 over the i+1 budget**, frozen
as a ratchet in `research/reports/lesson_sentence_baseline.json`.

The same disconnection shows in pre-N5: the 24 survival words of `top:pre-n5-saudacoes` are presented as
bare `<jp>ください</jp>` text with **no `<vocab ref>` chip anywhere** — 0 of 24 appear as a chip in the
teaching body (6 appear only in the closing checklist). They are taught and enrolled in SRS, but the app
cannot open a word modal for any of them. Chip coverage elsewhere is good: n3 98.5%, n4 96.0%, n5 94.5%.

### G10. The capability layer has no can-do text and no exam link — M, AI-authorable

`contracts/capability.schema.json` has exactly four fields: `id`, `level`, `name`, `grammar_keys`.
`contracts/manifest.json` describes the entity as "Something a learner can DO once a set of lessons is
complete. **The bridge between the syllabus and the exam**" — there is no field that reaches the exam,
no can-do statement, no lesson list, no assessment criterion. **28 of the 74** capabilities are
auto-derived `cap:topic:*` whose `name` is verbatim the topic title ("Condicionais (たら/ば/と/なら)"),
which is a syllabus label, not a can-do. And 42 of the 56 exemptions are marked
`pending-capability-design` — **34 of them N3 lessons** — because `build_capabilities.py` derives
capabilities from grammar/kanji/kana unlocks only and there is no vocabulary capability, so an N3 lesson
that introduces 18 words maps to nothing.

### G11. No placement, no checkpoints, no mastery, no unit metadata — M/L, needs owner design

Searched `design/`, `contracts/` and `course/`: there is **no placement test**, **no checkpoint
entity**, **no mastery threshold** and **no `duration` / `xp` / `difficulty` field** on any of `lesson`,
`topic`, `course`, `course_manifest` (their schema property lists are, respectively, 17 / 7 / 6 / 4
fields, none of them progression-related). `design/courseware_architecture.md` §6 states the position
explicitly: "we gate by lesson-completion now, mastery-gating is a future option." Review exists only at
end-of-level (3 topics) — a learner crosses 14 N5 topics, then 17 N4 topics, before meeting one.

What a unit/skill tree needs that this linear lesson list lacks:

| missing | why the learner needs it | size |
|---|---|---|
| **Placement** | a learner with prior Japanese must start at hiragana lesson 1 or guess. The data to build it exists (banks + `cumulative_known_set`): a short adaptive probe maps a score onto the deepest lesson whose cks the learner passes. | M |
| **Mid-level checkpoints** | 3 review topics for 52 topics. A checkpoint every 3–4 topics, drawing only from the cks at that point, is the standard shape and is fully derivable from existing data. | M |
| **Mastery gate** | today "complete" means "the page was opened". Exercises are graded client-side and nothing records a score. | L (app-side) |
| **Unit metadata** | no estimated minutes, no item count surfaced, no difficulty — the tree cannot show a learner what a lesson costs. | S |
| **Remediation edges** | with `needs[]` empty (G5) there is no way to say "you failed the て-form checkpoint, go back to `les:n5-te-form-03`". | M, blocked by G5 |

### G12. Small, mechanical — S each

- **12 lessons unlock nothing**: 8 pre-N5 (orientation, sounds, pronunciation — legitimate method
  lessons), plus `les:n5-revisao-01/02` and `les:n4-revisao-01/02`. Legitimate; but `top:n3-revisao`
  introduces 4 new words in its single review lesson, which is an odd place to introduce vocabulary.
- **8 lessons with zero exercises**, all `top:n5-kanji-exame` / `top:n4-kanji-exame`, each unlocking 5–8
  kanji and enrolling their cards. Held with per-lesson reasons in `course/practice_exemptions.json`.
- **Choice counts do not match the exam.** MCQ histogram: {2 choices: 3, 3: 493, 4: 180}. The JLPT uses
  4 options throughout; 493 of 676 in-lesson MCQs offer 3, and 3 offer 2 (a 50% guess:
  `ex:n3-conectores-07-4` 腹/原, `ex:n3-estrutura-05-3` 放した/離した, `ex:n5-adjetivos-01-2`).
- **`deck:phrases` is declared and empty** — 0 `phrase` unlocks exist course-wide, and both
  `conjugation-form` and `phrase` keys are empty in all 322 `cumulative_known_set` records despite being
  `required` by `contracts/lesson.schema.json`. Either populate or retire.
- **2 duplicate exercise triples** (same type + prompt + answer) across lessons; already counted by
  `validate_exercise_contracts.py` as an advisory.
- **Single locale.** All 4,838 locale objects across lesson titles, descriptions, objectives, prompts and
  explanations carry only `pt-BR`. That is correct per `design/i18n.md` (Layer C is authored in pt-BR),
  but it means a second locale is a 4,838-string + 322-body authoring project, not a data move.

### G13. N2/N1 absence is a documented decision, not a gap

`design/n2_n1_bank.md` records the owner directive of 2026-06-25: N2/N1 are **bank-only levels** (kanji +
vocab for FSRS study, no sentences, no grammar, no lessons). The data matches exactly — 368 N2 + 1,133
N1 kanji and 1,768 N2 + 2,679 N1 vocab exist; grammar records exist only for n5/n4/n3 (151/213/132) and
no course topic references N2/N1. Because `level` is data and not structure (spec §1.6), extending the
path later is inserting rows. Nothing to fix; listed so the absence is not re-raised as a defect.

---

## 4. Quality risks against the near-100% goal

**Q1 — A learner can "complete N5" and then fail the simulator on unteachable items.** G3 is the risk
with the sharpest edge, because the exam is the product's own claim of readiness. 274 of 400 N5
`kanji_reading` items and 258 of 379 N5 `orthography` items contain kanji the N5 path never teaches.
Today's paper draws 7 + 5 of them at random. No validator will ever tell you.

**Q2 — 73% of lessons contain reading material that is not text.** G4 is decided but not done. Until it
is, the app teaches 読解 with five unrelated sentences under a title describing only the first one. A
teacher reviewing lesson-by-lesson will hit this in 235 of 322 lessons.

**Q3 — Advisory ratchets are real content debt, and one of them is learner-visible every session.** 178
of 624 in-lesson sentences are above their lesson's level, 147 over the i+1 budget. The ratchet keeps it
from growing; it does not make the sentences readable. Combined with the 875 unread kanji spans (G6), a
learner regularly meets Japanese they cannot decode inside the lesson that is supposed to be their level.

**Q4 — The SRS is doing work the lessons are not, and the SRS is not built here.** 9,453 scheduled card
instances (recognition 4,133, production 4,133, handwriting 691, cloze 496) against 1,560 lesson
exercises. If the FSRS layer slips, 60% of vocabulary and 89% of kanji have no practice at all. The
handwriting slice (691) has no exercise type, no unlocked feature and no input widget anywhere.

**Q5 — "Complete" is unmeasured.** Nothing in the data records whether a learner answered anything
correctly. Every readiness claim the product makes about a learner is currently a claim about pages
opened. This also strands the capability tracker described in `design/exam_simulator.md` §6 ("feeds the
capability tracker as right/wrong signals") — there is no field to write into.

**Q6 — One hard gate reads the wrong artifact.** `audit_coverage.py` is listed HARD in
`scripts/validate/validate_all.py` (line 30) and reads `db/corpus.sqlite`, de-duplicating by authoring
headword: it reports `vocab placed=2910 unlocked=2910` where the export has **2,946** distinct vocab
refs. `scripts/validate/README.md` states "Every validator below reads the export unless its row says
otherwise", and `audit_coverage`'s row does not say otherwise. The 36-record difference is exactly the
homograph class this project has been fighting all session, so this gate is structurally unable to see a
homograph coverage gap.

**Q7 — Documents drift from data.** `design/exam_simulator.md` opens with "4,359 items"; the banks hold
**6,048** (`contracts/manifest.json` agrees with the data). Where the spec, a design doc and the data
disagree in this area, **the data is right** — it is what the 39 validators actually read, and
`validate_course_chain.py` recomputes every derived summary from the leaves. The stale doc figures
should be corrected, not trusted.

---

## 5. Recommended sequence

Ordered so each step unblocks the next and nothing has to be redone.

1. **Add the level gate to the exam-bank builder and land a validator for it — before the A2
   regeneration runs.** (G3, blocks Q1.) One new hard check: every item's visible Japanese ⊆ the level's
   end-of-level `cumulative_known_set`, planted-violation proved. Add it to the nine fixes in
   `research/reports/exam_bank_regen_review.md`. Without this, regeneration bakes in 1,000+ ungated
   items and the simulator's claim stays false.
2. **Complete furigana coverage (875 spans) and extend `validate_lesson_bodies.py` to require the
   attribute, not merely validate it.** (G6.) Cheap, already approved, and it is what turns four of the
   nine exam sections in G3 from "cannot ship" into "ships".
3. **Author the reading passages.** (G4, owner-decided.) ~40–60 Layer C passages per level built from the
   level's known set, replacing all 286 records; 473 exam items and 235 lesson bodies re-point to them.
   Sequence this with step 1 where possible, since `reading_comp` and `text_grammar` are rebuilt from
   whatever the passages are.
4. **Populate `needs[]`.** (G5.) Derive from the body's actual consumed-item set minus the immediately
   preceding lesson's cks, then hand-check the cross-strand cases the design doc names. This unblocks
   remediation edges, checkpoints and placement, so it belongs before any of them.
5. **Close the N3 dead end.** (G7.) Add `jlpt-sim-n3` to `design/unlock_enums.json`, expand
   `top:n3-revisao` from 1 lesson to 3 mirroring `top:n4-revisao`, and unlock the feature there. Small,
   and it is the difference between the path ending and the path stopping.
6. **Author the practice deficit, kanji first.** (G2.) 567 kanji and 1,771 words have no in-lesson
   retrieval. Kanji is the smaller and higher-value half; the answer keys are derivable from the same
   registries that produced the existing 1,560 exercises. Do it against a per-lesson budget (every
   unlocked item appears in at least one exercise of its own lesson) so a validator can hold it after.
7. **Add the exercise types that need no new infrastructure**: `reading` (comprehension items over the
   step-3 passages), and retire `ordering` from the frozen schema as a duplicate of `sentence_build`.
   Hold `listening` and `handwriting` behind their infrastructure decisions.
8. **Design the progression layer.** (G11.) In order: mid-level checkpoints (derivable from the cks at
   each boundary), then placement (a probe over the banks mapping a score to a lesson), then the
   mastery/score fields both need. This step requires the owner, because it defines what "complete" means.
9. **Rebalance N3.** (G8.) Either split the 1,596-word load across more lessons or lower the per-lesson
   introduction cap to the N4 figure and accept a longer N3. Teacher judgement; do it after step 6, so
   the decision is made with the practice budget visible.
10. **Repoint `audit_coverage.py` at the export** (Q6) and correct the stale figures in
    `design/exam_simulator.md` (Q7).

**What is already good enough to leave alone:** the four-tier chain, the unlock ledger, the
`cumulative_known_set` derivation, the exercise↔body bijection, the SRS enrolment, the exemption files
and the objectives. Those are the parts a Duolingo-shaped app is hardest to retrofit, and they are done.
