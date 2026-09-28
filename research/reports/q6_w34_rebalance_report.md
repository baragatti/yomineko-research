# Q6-W34: speak strand rebalance applied (checkpoint, final unit of chain v4)

**2026-09-27.** Mechanical (derived 72 unit rows, authored 0). Everything stays Layer C, `needs_review`.
Plan: `research/reports/w34_rebalance_plan.md` (measured 2026-09-23 at `f9de8e2c`, before the W32 ingest).
Table: `research/derived/repairs/w34_rebalance.json` (moved from `pending/`, re-derived).

## 1. What changed

Only `production` and `fluency.items` in `course/speak/*/unit-*.json`. say_now, shadowing, words,
patterns, drills, kanji_recognition and checkpoints are untouched, so input and language-focused
counts do not move.

- `scripts/export/build_speaking_practice.py`: the flat 3 production / 6 fluency per unit become
  per-stage caps, read from the table (`caps`), so the builder and the exact-match check read one copy.
  Selection order is unchanged: the 213 shipped production items stay a prefix of each unit's list
  (the derive script refuses otherwise). Floor rule: production grows toward its stage cap only while
  the fluency block keeps the item count it has at 3/6.
- `scripts/derive_w34_rebalance.py`: writes one row per unit (the exact production and fluency lists,
  the pre-W34 lists, the moves) from a pre-W34 snapshot of `course/speak/` and the rebuilt one.
- `scripts/validate/validate_repairs_applied.py`: `handle_w34_rebalance` exact-matches every row
  against the export. Plants 3/3 (a reordered production list, a dropped fluency item, an unknown
  unit) fail; the 72 real rows pass.
- No DB write, so no rebuild-manifest step (the W24 precedent: a builder-read table).

Every added item is a say_now phrase from an EARLIER unit (R44, R79a), already through `speak_filter`
when placed as say_now and again by the production selector. Production prompts are the sentence's
existing pt-BR translation; `answer_key` / `accepted_variants` come from `variants()`.

## 2. Re-derived on today's path

The builder at the shipped caps reproduced HEAD's `course/speak/` byte for byte, so today's path is
HEAD's (the drift in plan section 6 is gone). The plan's caps on this path left 7 stages 0.2 to 0.9 pt
out of band (5/12 in band; language-focused 35.3 to 35.9), because the W32 ingest changed the say_now
pools. So I re-ran the search on today's path with the plan's rule plus a margin: for each stage,
over P 3-40 and F 6-60 at the builder's own selection, no (stage, strand) may end further from R78's
budget than at 3/6; take the lowest P+F whose worst strand is within 9.5 pt (0.5 pt margin), else
within 10, else (arrival) the lowest worst distance. Stages are independent because a unit's counts
depend only on its prior-phrase pool. The search model predicted every stage's percentages exactly as
`validate_speak_strands.py` then measured them.

| stage | plan caps P/F | today's caps P/F |
|---|---|---|
| arrival | 13/9 | 15/11 |
| shopping | 17/16 | 16/14 |
| eating | 15/21 | 16/23 |
| getting_around | 16/23 | 17/24 |
| lodging | 17/24 | 19/26 |
| about_you | 17/26 | 17/22 |
| time_plans | 15/22 | 17/23 |
| health | 15/20 | 16/22 |
| past_stories | 16/23 | 17/23 |
| politeness | 18/28 | 18/27 |
| opinions | 15/21 | 15/18 |
| real_talk | 17/24 | 18/26 |

Moves: 676 `add_production`, 275 `swap_fluency_to_production`, 1,407 `add_fluency`, 34
`drop_fluency`. Production 213 -> 1,164, fluency 423 -> 1,521.

## 3. Strand bands per stage (R78 budget 15 / 30 / 25 / 30 +-10)

in / out / language-focused / fluency, worst distance:

| stage | before | after |
|---|---|---|
| arrival | 31.4 / 6.6 / 50.2 / 11.8 (25.2) | 26.8 / 17.8 / 42.8 / 12.6 (**17.8, out**) |
| shopping | 27.9 / 7.0 / 51.2 / 14.0 (26.2) | 18.8 / 25.1 / 34.5 / 21.7 (9.5) |
| eating | 25.1 / 6.3 / 56.1 / 12.5 (31.1) | 15.4 / 20.6 / 34.5 / 29.6 (9.5) |
| getting_around | 24.6 / 6.1 / 57.0 / 12.3 (32.0) | 14.8 / 21.0 / 34.4 / 29.7 (9.4) |
| lodging | 23.8 / 5.9 / 58.4 / 11.9 (33.4) | 13.9 / 22.0 / 34.1 / 30.1 (9.1) |
| about_you | 25.2 / 6.3 / 55.9 / 12.6 (30.9) | 15.5 / 21.9 / 34.3 / 28.3 (9.3) |
| time_plans | 24.9 / 6.2 / 56.4 / 12.5 (31.4) | 15.2 / 21.5 / 34.3 / 29.1 (9.3) |
| health | 25.4 / 6.3 / 55.6 / 12.7 (30.6) | 15.7 / 21.0 / 34.5 / 28.8 (9.5) |
| past_stories | 25.0 / 6.2 / 56.2 / 12.5 (31.2) | 15.2 / 21.5 / 34.2 / 29.1 (9.2) |
| politeness | 23.7 / 5.9 / 58.6 / 11.8 (33.6) | 13.8 / 20.8 / 34.2 / 31.2 (9.2) |
| opinions | 27.1 / 6.8 / 52.6 / 13.5 (27.6) | 17.6 / 22.0 / 34.1 / 26.3 (9.1) |
| real_talk | 23.9 / 6.0 / 58.1 / 12.0 (33.1) | 14.1 / 21.1 / 34.2 / 30.5 (9.2) |

**Stages in band 0/12 -> 11/12.** Path-wide 25.5 / 6.3 / 55.7 / 12.5 -> 15.9 / 21.4 / 34.7 / 28.0 over
3,388 -> 5,437 components. All 48 (stage, strand) distances shrink; the strand baseline was
re-recorded DOWN only (checked cell by cell) with a `q6w34_cause`, earlier cause keys kept.

**arrival** stays out: unit 01 has no prior phrases and units 02-04 draw only on arrival's own few
zero-new-token phrases (pool-limited: arrival-01 0/0, -02 3/3, -03 4/6, -04 11/6, -05 15/8 against caps
15/11; shopping-01 fluency 13/14). Closing it needs more short, fully-known arrival phrases taught in
units 01-03, or a rule decision for stage 1 (PENDING B-W34).

## 4. Spiral R83 (reach into stages 7-12)

| early stage | say_now | fluency before -> after | drills | late units before -> after |
|---|---|---|---|---|
| arrival | 2 | 0 -> 0 | 27 | 18 -> 18 |
| shopping | 16 | 15 -> 66 | 39 | 28 -> 34 |
| eating | 1 | 2 -> 6 | 9 | 10 -> 12 |
| getting_around | 7 | 7 -> 41 | 9 | 16 -> 27 |
| lodging | 1 | 0 -> 66 | 0 | 1 -> 8 |
| about_you | 5 | 16 -> 118 | 10 | 17 -> 30 |

Late-stage fluency slots 216 -> 834. Floors re-recorded UP only (`q6w34_cause`).

## 5. Near-duplicates and other costs

- **say_now gate (R86 / section 6b):** 17 pairs before and after (say_now untouched; no re-record).
- **Inside one production list or fluency block** (same metric and 0.72 threshold, not gated):
  **6 -> 60 pairs.**
- **Unit size** 47.1 -> 75.5 components on average (max 55 -> 90). The balance comes from adding
  retrieval; none of the language-focused load comes off.
- **Repetition:** on average 61.6% of a unit's production list repeats the previous unit's list in the
  same stage (0% before, when three items rotated). Production kinds after: 803 same-stage, 153
  on-topic, 208 review.
- Register census over say_now + production: 1,544 items, 0 marked registers.

These are the plan's section 4 costs, now measured on today's path. Whether R78 should count
components or time on task is an owner question (PENDING B-W34).

## 6. Checks

- Rendered diff of `course/` against HEAD: 71 files, all under `course/speak/` (70 units + course.json;
  arrival-01 and arrival-02 unchanged); **0 lesson files, 0 `.md`**.
- `validate_speaking_path.py`: 0 FAIL, 1 warn (arrival-02 fluency 3 < 6, R79d, same as before).
- deck:phrases cards key off say_now: unchanged (432).
- Exporters, contracts (infer_shapes -> build_schemas -> build_manifest; `speak_path` / `speak_unit`
  hashes moved), `sync-data` (speakPath 72), review views re-rendered, `validate_all.py` green.
- Full replay: section 7.

## 7. Full replay (checkpoint)

The first full run broke at **step 153** (`scripts/apply_token_reading_repairs.py`, Q3, never
full-replayed: Q3-Q5 were not checkpoints): 12 guard failures, nothing written. Two replay-only
differences, both fixed in the step's guards (the live index re-applies with 0 writes):

- 11 sentences: the romaji of a punctuation token is `.` / `,` on a replay and `。` / `、` on 4,361 of
  7,295 live `。` tokens (the live index is mixed). The rebuilt-vs-table proof now compares romaji
  modulo punctuation (NFKC, `。`->`.`, `、`->`,`).
- `sent:gen-9f80f08cc644` (この味噌はちょっと辛いです): the live sentence row already carried からい while
  its token read つらい (I2 false before Q3); a replay's row agrees with its pre-repair tokens. The
  sentence guard now accepts either old state: the table's `kana_old`/`romaji_old` or the concat of the
  pre-repair tokens.

Second run: the rebuild runs clean through every step. Result before re-recording: **0 new, 0 healed,
53 re-pinned** (held files whose rebuilt bytes moved: `corpus/sentences/bank.json`, 51 files under
`course/` (n4 22, n5 18, n3 11: lessons, their `.md` and topic files, all touched by the Q3-Q5 reading
and example edits) and `course/vocab_disambiguation_review.json`). Every entry
keeps its existing cause; `--record` rewrote the 53 sha pins and `recorded_at` only.

The mixed punctuation romaji in the live index (`。` vs `.`) is a Layer-A consistency item for a later
unit; nothing here depends on it.

## 8. Open

- arrival out of band (new short arrival phrases, or a stage-1 rule): PENDING B-W34.
- R78 as component count vs time on task, and the 6 -> 60 look-alikes inside blocks: PENDING B-W34.
- Fable sample of the added production prompts not drawn (they are existing Layer-B translations).
- Live-index punctuation romaji mixed (`。` 4,361 / `.` 2,934 tokens): normalise in a Layer-A unit.
