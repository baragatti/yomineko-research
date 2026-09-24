# Q1-exam-fixes-3: context_fill stem rules, the second-key withdrawals, the capability join

Date 2026-09-23. Not a checkpoint (gate + quick replay). Mechanical: derived only, authored 0. No DB
write, no lesson changed.

## 1. What was applied

| patch / table | applies on HEAD | what it does |
|---|---|---|
| `research/derived/patches/exam_builder_fixes_3.patch` | clean (index 994bdb5 = HEAD's builder) | fix 21: `cf` stems need 2 content tokens; a word distractor is refused when it makes a Tatoeba/bank sentence, is attested between the blank's own neighbours (`word_frames`), or shares the key's open group (`open_group`) |
| `research/derived/patches/exam_function_word_tweak.patch` | clean on top | the stem counter also treats 接頭辞 / 連体詞 / 接続詞 as function words (`STEM_FUNCTION_POS`); `word_frames` keeps the old set |
| `research/derived/patches/capability_exam_link_join.patch` | clean | `build_capabilities.py` resolves `lesson_unlocks.ref` through `export_course._deref` |
| new: fix 22, the withdrawal ledger | builder change | `build_exam_banks.py` reads `research/derived/reauthor/exam_authored/_flagged_auto.json` by default (`--flagged {}` builds without it), the same way `build_listening_bank.py` reads `_flagged_listen.json` for `lr:n5:tatoeba-213565`. Ids are removed AFTER the bank cap, so a withdrawal shrinks the bank and never backfills an item nobody checked |

`_flagged_auto.json` holds the 185 rows of `research/derived/pending/exam_second_key_flags.json`
(169 `second_key`, 16 `key_defect`), keyed by bank, each with its id, distractor, filled sentence,
reason, `status` and `by: q1-exam-fixes-3`. The pending flags file stays where it is as the review
evidence. Every one of the 185 ids was still built by the patched builder, with the flagged
distractor still offered, so all 185 carry `status: withdrawn` and **0 are `dropped_by_patch`**.

## 2. Per bank, HEAD to now

The 12 other auto-built banks and all authored banks are byte-identical to HEAD.

| bank | HEAD | after patches | withdrawn | now | x paper | changed | dropped by patch | added |
|---|---|---|---|---|---|---|---|---|
| n5_context_fill | 155 | 111 | 18 | **93** | 15.5x (6) | 36 | 47 | 3 |
| n4_context_fill | 400 | 400 | 83 | **317** | 39.6x (8) | 72 | 56 | 56 |
| n3_context_fill | 400 | 400 | 63 | **337** | 30.6x (11) | 43 | 20 | 20 |
| n5_grammar_form | 75 | 72 | 1 | **71** | 7.9x (9) | 0 | 3 | 0 |
| n4_grammar_form | 300 | 300 | 12 | **288** | 36.0x (8) | 4 | 3 | 3 |
| n3_grammar_form | 300 | 300 | 8 | **292** | 22.5x (13) | 0 | 6 | 6 |

All banks: 5,103 -> 5,056 (patches) -> **4,871** (ledger). Builder drop counters: `cf`
stem-too-short 150, withdrawn 164; `gf` stem-too-short 118, withdrawn 21. Every bank stays at or above
3x its paper (lowest n5_grammar_form 7.9x).

The flags were measured on a build with 108 n5 `cf` items; today's has 111. The three extra items come
from W32 sentences banked after that build (P4-w32-ingest). I read them, and none has a second key:
cf:n5:10229:199 （　）もよい天気らしいですね = 今日 (白い / 高い / 先生), cf:n5:10230:58
今（　）か分かりますか = 何時 (八つ / ７日 / 電車), cf:n5:10250:283 １（　）に会いましょう = 時
(川 / 母 / 八).

## 3. Gates

- `validate_exam_level_gate.py`: ALL OK, 4,871 items in 40 banks. Every deterministic family is at
  ceiling 0. The 175 over-level items are listening, as before.
- `validate_exam_banks.py`: ALL OK. `validate_exam_stem_collisions.py`: 0.
- Ledger ids left in any bank: 0.

## 4. Capabilities (`build_capabilities.py`)

| measure | HEAD | HEAD script, new banks | now |
|---|---|---|---|
| bank items linked to nothing | 3,185 / 5,103 | 3,079 / 4,871 | **634 / 4,871** |
| exam_link | 772 rows on 118 caps | 757 rows on 118 caps | **819 rows on 119 caps** |

The 634 left over are the same classes the join report names (listening items without refs,
sentence_order / listening_reply without `sentence_grammar`, 3 n4 revisão reading_comp items).
The four homograph claims unmerge exactly as the join report predicted. Each lesson loses one
`cap:vocab:n5-*` and gains nothing: les:n4-condicionais-01 (n5-verbos), les:n4-condicionais-07 and
les:n4-oracoes-relativas-01 (n5-desu-wa), les:n4-experiencia-04 (n5-rotina).

## 5. Downstream, re-derived

| artifact | before -> after | note |
|---|---|---|
| `course/item_lesson_index.json` | exam items placed 4,932 / 5,103 -> 4,700 / 4,871 | unplaced unchanged at 171; `validate_placement_index.EXAM_FLOOR` 4932 -> 4700 re-recorded with cause |
| `course/topic_tests.json` | pool entries 13,147 -> 13,058 | 49 tests, 3 exempt |
| speaking checkpoints (`build_speaking_checkpoints.py`) | 30 checkpoints pointed at removed items; re-selected | 322 items, per type unchanged (cf 142, kr 141, so 33, pp 6); 35 units, only `checkpoint` leaves; `validate_speaking_path` 0 FAIL |
| `research/derived/repairs/w08b_merges.json` | 3 exam-item rows addressed removed items | `retired_by: q1-exam-fixes-3` + `retired_why`: gf:n4:3413 and gf:n4:3541 (withdrawn: second keys みたいな and だいたい), gf:n5:4309 (dropped by the function-word tweak: 大した is a prenominal, so 大したもの（　） has one content token). The existing P1 mechanism, no validator change |
| contracts, review views (n5, speak), `prototype` sync | regenerated | |
| `design/exam_simulator.md` | 5,141 -> 4,871 items, second ledger described | |

## 6. Lessons did not degrade

Rendered diff of `course/` against HEAD, by JSON leaf: **0 lesson files and 0 `.md` changed**. The only
changed files are the two derived indexes (`item_lesson_index.json`, `topic_tests.json`) and 36
`course/speak/` files, where only `checkpoint` changed.

## 7. Gate

`validate_all.py`: all hard validators pass, including `validate_repairs_applied` (3 new checked skips)
and the quick replay (`validate_index_rebuildable.py --quick`: 4 files held at their recorded bytes).
No full replay, since this is not a checkpoint unit. The banks are not replay steps (no manifest step).

## 8. Open

- Residual second keys among common nouns and verbs (fixes_3 report, residue 1). They are left to the
  teacher loop.
- The withdrawn ids are not re-authored. A future builder rule that removes a whole class of these
  would let their ledger rows go.
