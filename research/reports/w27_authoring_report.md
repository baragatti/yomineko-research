# W27 — production card answer keys

`research/derived/pending/card_production_keys.json` (pending; nothing under `corpus/`,
`course/`, `contracts/` or `db/` was touched).

## What the file closes

G1 of `research/reports/readiness/srs_fsrs.md`: the srs declaration in a lesson names a deck,
an item slug and a card type, and stops there. A production card asks pt-BR → Japanese, so it
needs two things nobody had written down — a prompt that picks out exactly one item in the whole
corpus, and the set of Japanese answers a grader must accept. The shapes are borrowed from what
already ships: `answer.accept` of the lesson exercises, and `accepted_variants` of the speak
units, with the same acceptance logic as `scripts/export/build_speaking_practice.py` `variants()`
(orthographic vs phonetic kana, NFKC twins) and `LessonExercises.tsx` `normAnswer`.

## Counts

| | |
|---|---|
| rows (one per lesson × vocab slug) | **2946** |
| pre-N5 | 24 |
| N5 | 684 |
| N4 | 642 |
| N3 | 1596 |
| cards with no key before | 2946 |
| rows carrying a recorded disambiguation (`why`) | 1213 |
| accept-set size, min / max | 1 / 20 |

Every card declared by a lesson's srs block is covered; there are no extra rows and no rows for
a (lesson, vocab) pair the course does not teach.

## Uniqueness pass

The readiness audit counted 883 ambiguous prompts (a shared first pt-BR gloss) and 70 shared
headwords. After authoring, a global pass over `prompt_pt` compared every row against every other
under NFKC + case + whitespace normalization.

- **exact prompt collisions remaining: 0** — no kana qualification had to be added at this stage;
  the collisions were already resolved during authoring, by the sense's own further glosses, a
  part-of-speech marker, a short context cue, or the kana in parentheses as the last resort.
- **40 prompt families are separated only by their parenthetical cue** (85 cards). These are the
  genuine synonym and prefix pairs — お金/金, お風呂/風呂, 兄/お兄さん, 大きな/大きい,
  いいえ/否/ノー, これから/今後 — where the bare gloss is legitimately the same word in
  pt-BR and the cue is the whole disambiguation. They are unique as written.
- **still ambiguous after the pass: 0.**

## Accept sets

Each accept set is the deterministic surface set of the vocab record: headword, orthographic kana,
phonetic kana, every registry form, plus NFKC twins (`1日`/`１日`, `FAX`/`ＦＡＸ`). Nothing from a
different word is ever admitted, and homograph partners (音 おん vs おと, 方 かた vs ほう,
表 おもて vs ひょう) stay in separate cards separated by the prompt, not by a merged accept set.

Deliberate departures from the raw registry surface set, all recorded in the row's `why`:

- 2 rows add a phonetic は→わ twin the registry does not carry — `じつわ` for 実は,
  `それでわ` for それでは — because that is how learners type them.
- 2 rows drop a registry form that is not a reading of the record as taught: `けんぼう`
  (憲法) and `ちゃく` (笛).
- 1 row (兎 coelho) had a variant kanji 兔 restored during assembly; it had been dropped by hand
  with no reason given.

## Repairs made during assembly

- 196 rows carried no `sense_index`; filled from the introducing lesson's `intro_sense_order`
  (0 in every case).
- 2 rows were superseded by later collision fixes and were taken in their revised form:
  恐ろしい (`les:n3-causa-01`) and 調子 (`les:n3-conectores-06`).

## What this does not do

The file is authoring output only. Applying it — writing the keys into the srs declaration /
card contract from W26 — is the W27 apply step, and every row still wants a human pass on the
pt-BR wording before it reaches a learner.
