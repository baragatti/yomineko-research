# P5-n3-review: the three N3 review lessons (W22 §3). Applied and committed (finished by F0-P5-finish)

Date: 2026-09-23. Not a checkpoint (gate + quick replay only). Single DB writer for this unit.

**Status: GREEN and committed after F0-P5-finish (section 7 closes both blockers).** Sections 1-6
record the first attempt: applied in both layers, exported, gate RED on two ratchets. The tree
is left as it stands so the next attempt at this unit continues from it (`git status` shows the
modified files listed in section 6). Both blockers need content that this unit may not write: a
reading for 6 spans no rule settles, and a ruling on 3 prompts that follow the house style the
punctuation ratchet counts as debt.

## 1. Input and verdict

- `research/derived/pending/n3_review_lessons.json` (authored, Layer C) and
  `research/derived/pending/n3_review_topic.verdict.json` (the verifier, keyed by stable id).
  The verdict names `n3_review_topic.json`, which never existed; it verified the lessons file.
- 22 verdict keys: **16 ok, 6 corrected, 0 rejected**. Corrected: the 3 lesson bodies (15 body
  edits, each re-applied by the assembler and checked byte for byte against the verifier's full
  body), ex:n3-revisao-01-3 (new sentence, strict-cks), -01-6 (prompt wording), -03-5 (second
  valid order removed by fixing いつか first).
- `scripts/assemble_n3_review_lessons.py` folds them into
  `research/derived/repairs/n3_review_lessons.json` (3 rows + the topic objective) and removed the
  pending lessons file. The verdict stays in pending/.

## 2. What was applied (both layers)

| what | where |
|---|---|
| les:n3-revisao-01 rewritten (block 1: conectores, tempo, perspectiva, causa), -02 and -03 created | `scripts/apply_n3_review_lessons.py` (new, manifest step 133) |
| top:n3-revisao objective "Consolidar o N3 e checar os can-do" | same step |
| feat:jlpt-sim-n3 moved from -01 to -03 | `w22_n3_dead_end.json` rows[0] (`moved_from`, `moved_by`) |
| the 3 W20 vocab drills on -01 renumbered -5/-6/-7 to -7/-8/-9 (the verifier's APPLY BLOCKER) | `practice_vocab_exercises.json` rows + `id_fixes` |
| 停留所 (vocab:1435080) lost its only drill with the old -4, so a new one was generated: `build_vocab_exercises.py` re-run into a scratch out-root, its work list held exactly this 1 vocab pair, the row appended verbatim as ex:n3-revisao-01-10 (V-RECOG) | `practice_vocab_exercises.json` `appended_rows`, 2,283 to 2,284 |
| the W14 "Mais exemplos" block on -01 kept (its anchor heading is in the new body) | `lesson_sentences.json` row 122, unchanged |
| needs re-derived: +7 rows (-01 +conjectura-05; -02 desejos-01, limites-01; -03 concessao-01, estrutura-01, estrutura-02, relato-04). -02/-03 derive real needs, so the review-chain rule does not fire (same as n4-revisao) | `lesson_needs.json` 736 to 743 |
| item_refs re-derived: the 18 authored anchors (`derived_by: authored`), the renumbered drills and the new -10 (22 revisao rows), and 33 stale rows on other lessons from the W08b / gp-153 merges that the table still named (gp-100, gp-60, gp-153/154, gp-33, gp-47, gp-54, gp-151, n3-nda-mon) now match the export | `item_refs.json` 4,716 to 4,717 rows; `pending/item_refs_residue.json` 21 to 20 |
| 2 capability quotes re-pointed (C5-W24 pattern, dated `rederived_p5_n3_review` block): exam-readiness-n3 now quotes the new -01 connector objective, its self-assessment quote dropped; vocab:n3-revisao left with no quote | `w24_capabilities.json` |
| readings for 85 of 91 bare kanji `<jp>` spans | `scripts/derive_n3_review_furigana.py` to `n3_review_furigana.json` (78 rows), applied by `apply_lesson_body_spans.py` (manifest step 148) |

The -01 vocab unlocks stay as the source writes them (headword refs, the same 4 records). The
kept reading passage and the 4 unlocks remain owner decisions (verdict `unresolved`).

Manifest: 150 to 152 steps; families now 150-152. `validate_repairs_applied.py` registers
`n3_review_lessons.json` (new handler: titles, objectives, exercises, unlock counts, and the body
once the later tables' additions are taken back out) and `n3_review_furigana.json`
(`handle_lesson_body_spans`). Replayed clean: n3_review_lessons 3/3, w22 35/35,
practice_vocab 2,284/2,284, lesson_sentences 123/123, item_refs, lesson_needs 743/743,
w24 125/125, card_examples and card_production_keys unchanged.

Chain idempotence checked: re-running step 133 then the drills and W14 steps leaves the -01 source
byte-identical and the DB exercise list unchanged.

## 3. Rendered diff of course/ against HEAD

12 course files: -01 json/md, -02 and -03 new (json + md), topic.json, course.json, outline.json,
manifest.json, topic_tests.json, item_lesson_index.json. **No other lesson file changed**
(n3-revisao is the last topic, and -01's unlocks are unchanged, so no cumulative_known_set moves).
Tag-stripped body text changed only in les:n3-revisao-01, the verified rewrite.

## 4. Gate: RED, two blockers

`validate_all.py`: everything passes except:

1. **validate_lesson_bodies [furigana]: bare kanji `<jp>` spans 1 to 7.** The authored bodies carry
   no `reading`. 85 of 91 were settled by rules (builder rules i/ii 51, bank sentence dissection 26,
   token run 1; every reading kana-only, covering, and aligned against the kanji registry). 6 are
   left, all failing alignment or a registry disagreement, so they need an authored + verified
   reading (the C13 `furigana_residue.json` path). Candidates for the verifier, from the dissection
   and the registry:
   - -01 私はあんたのお姉ちゃんだもん。: わたしはあんたのおねえちゃんだもん。 (姉 = ねえ not a registry reading; お姉ちゃん has no vocab row)
   - -02 彼らは不平ばかり言う。: かれらはふへいばかりいう。 (dissection says ゆう)
   - -02 真実を言うべきだ。: しんじつをいうべきだ。 (dissection says ゆう)
   - -03 もしかすると明日雨が降るかもしれない。: dissection あす, registry primary あした (jukujikun, does not align)
   - -03 ように言う: ようにいう (Sudachi ゆう, registry いう)
   - -03 ７月にしては今日はすずしい。: しちがつにしてはきょうはすずしい。 (今日 jukujikun)
2. **validate_exercise_contracts: prose without terminal punctuation 174 > ceiling 171.** The 3 new
   sentence_build prompts (ex:n3-revisao-01-5, -02-5, -03-5) end with the piece list `[...]`, the
   house style: 166 of the 174 unterminated fields are sentence_build prompts ending in `]`. Either
   a verifier-corrected prompt (for example a closing period) or an owner ruling that a trailing
   piece list is terminal (the ratchet would then drop to about 8).

The quick replay and every other validator pass. validate_review_views was stale and is regenerated
(build stamps, plus sent:gen-3a480b34e861 now listed in the n5 sentences view because -02-6 cites it).

## 5. To finish (next attempt of this unit)

1. Author + verify the 6 readings, fold them into `n3_review_furigana.json` (or a sibling residue
   table on the same applier) and apply.
2. Resolve the 3 prompts per the ruling above.
3. Export, contracts, sync-data, `validate_all.py` green, update the W22 row in APP_PLAN.md and
   STATE.md, commit.

Open, not this unit's: the 4 vocab unlocks on -01 and the reading passage that targets -02/-03
grammar (owner); `derive_item_refs.py` keys practice rows on the authored id and ignores
`apply_id_remap` (6 kanji drills in practice_kanji_exercises.json credit the wrong exercise; chip
filed).

## 6. Files in the tree (uncommitted)

New: `scripts/assemble_n3_review_lessons.py`, `scripts/apply_n3_review_lessons.py`,
`scripts/derive_n3_review_furigana.py`, `research/derived/repairs/n3_review_lessons.json`,
`research/derived/repairs/n3_review_furigana.json`, `research/derived/lessons/n3-revisao-02.json`,
`-03.json`, `course/n3/topic-52-revisao/lesson-02.*`, `lesson-03.*`, this report.
Modified: `research/derived/lessons/n3-revisao-01.json`, the repairs tables named in section 2,
`research/derived/rebuild_manifest.json`, `scripts/apply_lesson_body_spans.py`,
`scripts/validate/validate_repairs_applied.py`, the course/corpus/contracts exports, prototype
data, `research/review/*` views. Deleted: `research/derived/pending/n3_review_lessons.json`.

## 7. F0-P5-finish (2026-09-23): both blockers closed, gate green, committed

1. **The 6 residue readings**, supplied and checked by the reviewing session, went into
   `scripts/derive_n3_review_furigana.py` as `REVIEWED` (rule `reviewed`): a span no rule settles takes
   its reviewed reading, which must still be kana-only and cover the span's own kana; only the registry
   alignment (the check they failed: 姉 as ねえ, 明日 / 今日 jukujikun, 言う dissected as ゆう) is waived.
   Whole-span `reading` attribute, the form `validate_lesson_bodies` checks (the C13 residue did the
   same for 明日 / 風邪 / 下手). Table re-derived: 91/91 spans written (furigana-ii 49, bank-sentence 26,
   reviewed 6, furigana-i 2, token-run 1), residue 0; `apply_lesson_body_spans.py --table
   n3_review_furigana.json` changed 6 spans in each layer. Bare kanji `<jp>` spans 7 -> 1 (the ratchet).
   - -01 私はあんたのお姉ちゃんだもん。 わたしはあんたのおねえちゃんだもん。
   - -02 彼らは不平ばかり言う。 かれらはふへいばかりいう。 / 真実を言うべきだ。 しんじつをいうべきだ。
   - -03 もしかすると明日雨が降るかもしれない。 もしかするとあしたあめがふるかもしれない。 / ように言う
     ようにいう / ７月にしては今日はすずしい。 しちがつにしてはきょうはすずしい。
2. **Ruling: a sentence_build prompt ending with its bracketed piece list is terminated.**
   `validate_exercise_contracts.py` `PIECE_LIST_END` (`\[[^\[\]]+\]$`), sentence_build prompts only.
   Unterminated prose 174 -> 8; `NO_TERMINAL_CEILING` 171 -> 8 with the cause in the comment. Plant 3/3
   on a copied course/ tree with the validator copied beside it: a sentence_build prompt with text after
   its list, a recognition prompt ending in `[...]`, and a sentence_build explanation ending in `[...]`
   each push the count to 9 and FAIL; baseline passes.
3. Export (`export_course.py`), contracts, `sync-data`, `validate_all.py` green (quick replay included).
   Rendered diff of course/ vs HEAD: text changed only in les:n3-revisao-01 (the verified rewrite);
   -02/-03 new; no other lesson changed.
