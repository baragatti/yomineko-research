# W20 — kanji authoring report

**Campaign:** W20 (kanji, authoring) of `research/reports/APP_PLAN.md`.
**Deliverable:** `research/derived/pending/practice_kanji_exercises.json` (tracked authoring table).
**Applied?** No. Nothing was written to `db/corpus.sqlite`, `research/derived/lessons/`, `course/`, and no exporter
was run. The apply step is `scripts/apply_practice_exercises.py`.

## The debt this campaign consumes

`research/reports/readiness/jlpt_course_path.md` G2 and `readiness/tests_exercises.md` G1 recorded 67 of 634
kanji practised — 89% of the kanji a lesson unlocks get no exercise in the lesson that teaches them.
`research/reports/practice_coverage_review.json` is the per-lesson work list; taking only the entries with
`kind: "kanji"` gives **581 absent (lesson, kanji) pairs across 178 lessons**:

| level | absent kanji | lessons with absent kanji |
|---|---:|---:|
| n5 | 92 | 45 |
| n4 | 173 | 66 |
| n3 | 316 | 67 |
| **total** | **581** | **178** |

## What was authored

**899 exercises across all 178 lessons.** Every lesson on the work list was touched; no lesson was deferred.

| level | exercises | lessons | recognition | production | matching | cloze |
|---|---:|---:|---:|---:|---:|---:|
| n5 | 160 | 45 | 90 | 66 | 2 | 2 |
| n4 | 290 | 66 | 153 | 123 | 10 | 4 |
| n3 | 449 | 67 | 207 | 208 | 26 | 8 |
| **total** | **899** | **178** | **450** | **397** | **38** | **14** |

Exercises per lesson: min 1, max 16, mean 5.05. The heaviest lessons are the ones that unlock a whole block at
once — `les:n3-concessao-04`, `les:n3-relato-04`, and the three 16-item kanji-exam lessons
(`les:n5-kanji-exame-01`, `les:n4-kanji-exame-01`, `les:n4-kanji-exame-04`).

## Kanji covered vs still absent

| level | absent before | targeted by this table | still absent |
|---|---:|---:|---:|
| n5 | 92 | 92 | 0 |
| n4 | 173 | 173 | 0 |
| n3 | 316 | 316 | 0 |
| **total** | **581** | **581** | **0** |

**Every one of the 581 absent kanji is named in the `targets` of at least one authored row**, and in each case
the character reaches an answer surface (`answer.text` / `answer.correct` / `answer.accept` / `answer.full` /
`answer.pairs`) — never only the prompt, which `validate_practice_coverage` explicitly excludes. Fifteen further
kanji appear in `targets` as co-credited passengers of a compound answer (n5 2, n4 5, n3 8); they were already
practised in their own lessons and are listed so the apply step can see what each answer actually credits.

This is the authored claim, not a verified gate result. The coverage gate only moves once
`scripts/apply_practice_exercises.py` runs and `validate_practice_coverage.py` is re-run.

## Skipped and constrained: the reasons, aggregated

These are the constraints the authors recorded in the `why` field. They are not failures — each one is the
reason a *different* exercise shape was chosen. A row can carry more than one.

| constraint | rows | lessons | n5 | n4 | n3 |
|---|---:|---:|---:|---:|---:|
| the obvious cks word was blocked because a co-kanji is outside that lesson's cks | 69 | 59 | 11 | 22 | 36 |
| retrieval-only because the lesson is held in `course/practice_exemptions.json` | 56 | 8 | 26 | 30 | — |
| the kanji has no usable cks word at all, so the bare character is the answer | 34 | 29 | 3 | 12 | 19 |
| a matching grid replaced per-kanji MCQs because the lesson unlocks a whole block | 25 | 21 | 2 | 8 | 15 |
| the word is normally kana, or its reading is irregular / voiced off the record | 9 | 9 | 3 | — | 6 |
| recognition only: a production item was impossible or would repeat another answer key | 8 | 6 | 4 | 1 | 3 |
| a plausible distractor was dropped because it would be a second defensible answer | 7 | 7 | 3 | — | 4 |

The two dominant reasons are the same constraint seen from either side: the cumulative known set is the hard
boundary. Where a compound would have shown an untaught character, the item fell back either to a different cks
word (69 rows) or to the bare character with its registry reading in `accept` (34 rows).

## Notes the apply step must not lose

These are carried in the `why` field of the rows concerned and repeated here so they are visible before
`scripts/apply_practice_exercises.py` runs.

1. **Body `<exercise ref="…"/>` nodes.** Every inserted exercise needs a matching node in the lesson body or
   `validate_exercise_contracts` fails the id↔body bijection. Flagged explicitly on 14 lessons; it applies to
   all 178. `les:n4-kanji-exame-05` has no exercise block at all — the nodes go before the closing `<checklist>`.

2. **Stale practice exemptions must be dropped** on the four lessons that now render both a retrieval and a
   production item: `les:n5-kanji-exame-01`, `les:n5-kanji-exame-03`, `les:n4-kanji-exame-01`,
   `les:n4-kanji-exame-03`. `course/practice_exemptions.json` fails on an entry whose lesson has since gained
   practice.

3. **Three exemptions must stay**, and their lessons were deliberately authored retrieval-only so the entry does
   not turn into the opposite failure: `les:n5-kanji-exame-02` (9 retrieval, 0 production),
   `les:n4-kanji-exame-02` (9/0), `les:n4-kanji-exame-05` (4/0).

   | exempt lesson | authored rows | retrieval | production | exemption |
   |---|---:|---:|---:|---|
   | les:n5-kanji-exame-01 | 16 | 8 | 8 | drop |
   | les:n5-kanji-exame-02 | 9 | 9 | 0 | keep |
   | les:n5-kanji-exame-03 | 10 | 7 | 3 | drop |
   | les:n4-kanji-exame-01 | 16 | 8 | 8 | drop |
   | les:n4-kanji-exame-02 | 9 | 9 | 0 | keep |
   | les:n4-kanji-exame-03 | 11 | 8 | 3 | drop |
   | les:n4-kanji-exame-04 | 16 | 8 | 8 | drop |
   | les:n4-kanji-exame-05 | 4 | 4 | 0 | keep |

   `les:n4-kanji-exame-04` is the fifth lesson whose exemption must be dropped; its rows carry the note in the
   `why` of `ex:n4-kanji-exame-04-1`.

4. **Non-standard exercise-id prefixes.** Seven lessons do not use the canonical `ex:<lesson-key>-<n>` shape and
   the authored ids follow the lesson's own pattern instead: `les:n3-tempo-01` and `les:n3-tempo-04`
   (`ex:tempo-0N-…`), `les:n3-causa-01`, `les:n3-causa-02`, `les:n3-causa-03` (`ex:causa-0N-…`),
   `les:n3-limites-03` (`ex:n3limites-03-…`), `les:n3-limites-04` (`ex:n3limites-04-…`).

## Id assignment

Ids continue each lesson's own numbering (max existing + 1, contiguous) and are unique within the lesson and
across the table: **899 rows, 899 distinct ids, zero collisions with the 322 lessons already in `course/`.**

One prefix was realigned during assembly and is recorded in the table's `id_fixes` block:
`les:n3-limites-04` was authored as `ex:n3-limites-04-6/7/8` while the lesson's own five exercises read
`ex:n3limites-04-N` (no hyphen after `n3`). The authoring note left the choice to the apply step; assembly took
the lesson's existing pattern, so the rows now read `ex:n3limites-04-6/7/8`. No other row changed.

## Shape of the table

`research/derived/pending/practice_kanji_exercises.json`:

- header: `why`, `definition`, `generated_by`, `apply`
- `id_fixes`: the id realignments made at assembly (3 entries)
- `rows`: 899 × `{lesson, targets, exercise, why}`

Each `exercise` is a complete `contracts/lesson.schema.json` exercise object and carries exactly the fields that
schema allows (`additionalProperties: false`): `id`, `type`, `prompt`, `answer`, `explanation`, `sentence_refs`.
All MCQ items use four options. `sentence_refs` is empty on every row: these items are built from kanji and
vocab records, not from the sentence bank.
