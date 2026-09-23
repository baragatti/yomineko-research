# Exam taught-word rule: kanji_reading / orthography test a word a lesson teaches

Status: **pending, nothing applied.** Patch `research/derived/patches/exam_taught_word_rule.patch`
applies after `exam_equivalence_filter.patch` and `exam_builder_fixes_2.patch` (checked in that order
on a `git archive HEAD` tree) and touches `scripts/export/build_exam_banks.py` (fix 20) and
`scripts/export/exam_rules.py` (`TaughtSets.words`, `TaughtSets.word_taught`). Measured 2026-09-23 on
HEAD's banks and course export plus an sqlite backup of `db/corpus.sqlite`.

## Finding: the 3.7% is a join artifact, not a bank defect

W24 (`w24_apply_report.md` §3) counted 72 of 1,953 kanji_reading + orthography items whose `vocab`
names a word the course teaches. That count comes from `build_capabilities.py`, which reads
`lesson_unlocks.ref` straight from the DB and matches it against the item's `vocab:<jmdict_id>`.
In the DB, 2,896 of 2,951 vocab unlock refs are still `vocab:<headword>` (`vocab:いい`,
`vocab:お兄さん`); only 55 are numeric. Resolving those refs to `vocab:<jmdict_id>` is the
exporter's job, and `build_capabilities.py` never does it. The 72 are the items whose word happens to
have a numeric ref. HEAD's `corpus/capabilities/registry.json` shows those same 72 vocab-capability hits
on these two sections (n5 11 + 13, n4 12 + 15, n3 8 + 13).

Against the exported course, which is what the builder and the level gate both read:

| bank | items | word unlocked by a lesson at or below the level |
|---|---|---|
| n5_kanji_reading | 176 | 176 |
| n5_orthography | 177 | 177 |
| n4_kanji_reading | 400 | 400 |
| n4_orthography | 400 | 400 |
| n3_kanji_reading | 400 | 400 |
| n3_orthography | 400 | 400 |
| **total** | **1,953** | **1,953 (100%)** |

This is structural. Every level's cks vocab is exactly the cumulative union of the lessons' `vocab`
unlocks, 712 / 1,355 / 2,951 words for n5 / n4 / n3. The builder has drawn its target pool from the
cks vocab since W17 fix 13 (`clean_pool`), so the taught-word rule has been in force since the W18
regeneration. The kanji being taught while the word is not does not happen in HEAD's banks.

## Pool if the builder requires a taught word

Kanji-clean records with kanji in the headword (the builder's `clean_pool`), all of them taught.
Stems are distinct headwords (kanji_reading) or distinct kana (orthography) after the homograph /
homophone dedupe. Paper sizes come from `design/exam_simulator.md` (kanji_reading 7 / 7 / 8,
orthography 5 / 5 / 6).

| level | clean records | taught | own-level taught | kr stems | kr 3x paper | or stems | or 3x paper |
|---|---|---|---|---|---|---|---|
| n5 | 178 | 178 | 178 | 176 | 21 | 177 | 15 |
| n4 | 532 | 532 | 181 | 524 | 21 | 523 | 15 |
| n3 | 1,719 | 1,719 | 839 | 1,682 | 24 | 1,631 | 18 |

Every family is between 8x and 90x its 3x floor. n4 and n3 stay at the 400 cap. **No family falls
below 3x its paper, so no fallback is needed.** If the cks ever widens past the unlocks, the fallback
to reach for first is "taught word, or a JMdict-`common` word of the level list with a freq_rank
inside the level's taught median". Nothing today makes it necessary.

## Builder change and its effect

Fix 20 adds `TaughtSets.words[lvl]`, the cumulative `vocab` unlocks of the exported lessons up to the
level. The kanji_reading and orthography loops then skip any target record outside it, recording the
drop reason `target-word-not-taught`. Distractors still come from the whole level-clean pool, which
is what the learner may meet.

Run on the DB snapshot with `--root` set to HEAD's course export:

- base (HEAD + patch 1 + patch 2) and base + this patch give **byte-identical output on all 18
  generated banks**. Items changed: 0. Items dropped: 0. `target-word-not-taught` drops: 0.
- base vs HEAD's committed banks, for comparison: one item differs, `or:n3:1553` (おん). Its
  distractor 御 becomes 楽, which is patch 1's fix 17. The taught-word rule plays no part in it.

The patch pins the rule so that a future change to the cks cannot quietly put an untaught word under
test. It does not change a single item today.

## What should change instead (outside this patch's files)

- `scripts/export/build_capabilities.py` should resolve unlock refs the way the exporter does, or
  read `unlocks` from the exported lesson JSON the way `exam_rules.TaughtSets` does. After that,
  the ~1,881 kanji_reading / orthography items that reach no `cap:vocab:*` today get their link. The
  "3,185 items reach no capability" count in W24 shrinks by the same amount.
- W24's recommendation to make "3.7% taught" a hard ratchet on the level gate would lock in the
  artifact. The assertion to add is "100% of kanji_reading / orthography `vocab` are in the level's
  exported unlocks". It holds today.
