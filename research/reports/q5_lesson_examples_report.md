# Q5-lesson-examples: review-lesson examples applied, the rest of the W14 residue sorted

**Unit Q5-lesson-examples, 2026-09-27, not a checkpoint (gate + quick replay).** Input:
`research/derived/pending/lesson_examples_gap.json` (the W14 residue, worked: picks for the 14 N5/N4
lessons that rendered no sentence, and a fix for each of the 154 held links) with its independent
verdict `lesson_examples_gap.verdict.json` (200 verdicts: picks 25 ok / 14 corrected, held links 133 ok /
21 corrected, 2 lesson-level additions, findings 1 ok / 4 corrected). Only verified values were used:
ok as written, ok false as the verifier's `corrected`.

## 1. Lessons rendering zero sentences (N5/N4), before and after

| | before (HEAD) | after |
|---|---|---|
| n5 | 12: numeros-tempo-01, -03, -04, -06, -07, -08, -09, convites-06, conectando-07, revisao-01, -02, -03 | **9**: numeros-tempo-01, -03, -04, -06, -07, -08, -09, convites-06, conectando-07 |
| n4 | 3: revisao-01, -02, -03 | **0** |
| sentence links (course) | 761 | **779** |

All 52 remaining zero lessons: n5 9, n3 2, pre-n5 41 (kana strand + greetings, no i+0 sentence exists).
`les:n5-numeros-tempo-03` is new since W14 (it was not in the gap table; it lost its only link after
W14, cause not traced here) and needs its own pick.

## 2. What landed

`scripts/assemble_lesson_examples.py` (new) folds pending table + verdict into
`research/derived/repairs/lesson_examples.json`, re-checking every bank pick against the W14 rule on
today's export (level <= lesson, i+0 load, `build_vocab_exercises.sentence_ok`, model-text register,
not already rendered, picked once), not trusting the table's proof. `scripts/apply_lesson_sentences.py`
gained `--table` and applies it to both layers (DB body + `lesson_sentence`, and
`research/derived/lessons/`). Second run: 0 changes.

6 `add` rows, 18 real Tatoeba sentences (12 as picked, 6 verifier-corrected), one `Mais exemplos`
block before `Hora de praticar` in each review lesson:

| lesson | sentences |
|---|---|
| n5-revisao-01 | いくらですか？ / なぜ聞くの？ / あそこのカウンターです。 |
| n5-revisao-02 | あそこに先生がいます。 / あまり出かけたくなかった。 / 時間がありますか。 |
| n5-revisao-03 | りんごがほしいですか？ / さっさと行ったほうがいい。 / もう行かなきゃ！ |
| n4-revisao-01 | もう終わったかい？ / もう何をしたらいいか分からない。 / 明日雨ならば行きません。 |
| n4-revisao-02 | ここにいようと思う。 / 来てくれてありがとう。 / 今、勉強してるところだよ。 |
| n4-revisao-03 | 明日は雨かもしれない。 / 水道の水が止められた。 / 考えさせてください。 |

**Needs follow-up (C4).** The new sentences derive needs of their own, which made the three N5 reviews
lose their review-chain edge (n5-revisao-01 would have needed only n5-perguntas-01 instead of the end of
the block it reviews). `build_needs_table.py` rule 2 now keeps the chain edge for every `-revisao-`
lesson beside its derived needs (C4 imports the same builder, so the rule stays single-sourced).
`lesson_needs.json` 743 -> 754 rows (derived 700 -> 705, review_chain 3 -> 9): the N5 reviews keep
their chain edge and gain 1 derived edge each; n4-revisao-02/-03 gain 1 derived edge each; all six
N4/N3 reviews gain the chain edge they lacked. Additive only; no existing need was removed.

## 3. Residue (not applied), in the table's `residue` with reasons

- **needs-ingest, 23** (22 picks for the 8 item lessons: 11 raw Tatoeba, 11 generated; 13 ok, 7
  corrected, 2 verifier-added; plus the generated replacement for n5-te-form-04). None is in the bank.
  `scripts/derive_lesson_examples_layerb.py` (new, W32 path, read-only on a DB copy) derived their
  Layer-B mechanically: tokens 20 unique-accept + 48 verified rulings, particles 37 by template.
  Left to author: 23 structure paragraphs, 23 translation_literal, 9 particle explanations, 3
  ambiguous + 2 unglossed tokens, and **5 dissector links that disagree with the verified proof**
  (この -> 九 vocab:1578150 in 4 sentences, あめ -> 雨 instead of 飴). Ingest-ready: 0 of 23
  (`research/derived/pending/lesson_examples_layerb_derived.json`). Not authored here, by rule.
- **rule-refuses-today, 1**: sent:tatoeba-5066 シャワーはどこですか。 for n5-numeros-tempo-08, graded
  n4 only through the spurious run links 葉/歯; its verified `needs_fix` is a link repair.
- **card-example, 4**: n3-tempo-03 (verified removal of 家に着いたとたん嵐になった。) and three
  verified swaps (n5-particulas-lugar-07, n5-adjetivos-05, n5-adjetivos-08). An SRS card of each lesson
  cites the old sentence as its example; `validate_card_content` F allows that only while the lesson
  renders it (the first attempt applied the removal and F failed). The card example must be
  re-derived first. The lugar-07 and adjetivos-08 replacements are also n4 through run links.
- **link-lane, 11**: ください -> 下さい relinks (143718, 124708, 146189), level recomputes, つもり/こと
  unlocks in n5-conectando-06, 中 of 休み中, くれる. Measured today: する is already n5 and unlocked in
  n5-verbos-02, 呉れる is n4 and unlocked in n5-particulas-lugar-07 (Q2), so the verifier's
  "unlock + regrade する" halves are done; the sentence levels were never recomputed.
- **gloss, 63** (48 lessons, 51 ok, 12 corrected): verified pt-BR glosses for kept links. No markup
  carries a gloss on a `<sentence>` card, and inserting prose between a sentence and the paragraph that
  explains it is a placement judgement, so they wait for a renderer/design call (a `gloss` on the card).
- keep-no-gloss / keep-with-gloss without a gloss: nothing to do (the link stays, as ruled).

## 4. Checks

- Rendered diff of `course/` against HEAD: 6 lesson `.md` + 9 lesson JSON (the 3 N3 reviews: `needs`
  only); `.md` lines removed = 6, each the empty `Frases (por ID...): —` line now listing the IDs; 0
  prose lines removed. JSON: `body`, `sentence_refs`, `needs`; 3 `topic.json` needs mirrors;
  `manifest` / INDEX build stamps.
- `validate_lesson_gating`: 0 FAIL, 779 links; ceilings unchanged (above-level 160, new kanji 137, C5
  10/146), baseline left at HEAD. Corpus untouched (the date-only INDEX restamp was reverted: the quick
  replay pins its build date from the committed corpus).
- Replay: `lesson_examples.json` registered with `handle_lesson_sentences`; manifest step **156**
  (families 157-159). Plant: dropping one added sentence from n5-revisao-01 FAILs row 0; restored
  byte-identical, 6/6 PASS.
- Contracts (infer_shapes -> build_schemas -> build_manifest), review views (n5, speak), prototype
  sync. `validate_all.py`: ALL HARD VALIDATORS PASS, quick replay 4/4 held.

## 5. Open

- The 23 new sentences: author the residue (paragraph, literal, 9 particle explanations, 5 tokens),
  verify, fix the 5 links in the dissection, derive register, ingest by the W32 path, then re-run the
  assembler with `--out` and apply the delta. That closes the 8 item lessons.
- Link lane: 5066 / 178709 / gen-100750b3cf00 run links, the ください relinks, level recompute.
- Card examples for the 4 card-bound links, then their removal / swaps.
- Gloss markup decision, then the 63 glosses.
- n5-numeros-tempo-03 pick. Fable sample 30 on the 18 applied rows.
