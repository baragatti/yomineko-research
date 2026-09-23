# W20 vocab + grammar half: re-run, four rules, apply (C1-W20v, 2026-09-23)

Unit C1-W20v of the writer chain (was U5). Not a checkpoint: gate plus quick replay only.

## 1. What ran

1. `scripts/build_vocab_exercises.py` re-run on the current tree (bank 10,209 sentences, after
   W13 and after W21b moved 276 unlocks), with the four rules from the W20 Fable sample of 40
   (`research/reports/w20_vocab_report.md` §6) built in, plus kanji drills for W21b's pending list.
2. Table moved `research/derived/pending/` -> `research/derived/repairs/practice_vocab_exercises.json`
   (2,283 rows). The 19-pair grammar residue stays in `pending/practice_vocab_residue.json` as a
   work list.
3. `scripts/apply_practice_exercises.py --table research/derived/repairs/practice_vocab_exercises.json`
   (new flag; the default is still the kanji table). DB + `research/derived/lessons/` + one
   `<exercise ref>` node per row. Second run: 0 changes. Kanji table re-run: 0 changes.
4. Replay: `HANDLERS["practice_vocab_exercises.json"] = handle_practice_exercises` in
   `validate_repairs_applied.py`; manifest step **131** (families renumbered 132-134).
5. Exporters (course, corpus, readings, capabilities, review views), contracts, `sync-data`,
   `validate_all.py`.

## 2. The four rules, and what each changed

| rule | implementation | measured on the new table |
|---|---|---|
| 1. every id keeps its level prefix | new ids are always `ex:<lesson slug>-<n>`, numbering continues after the lesson's majority prefix (`ex:causa-01-24` is followed by `ex:n3-causa-01-25`); global uniqueness checked | 0 ids without the lesson slug |
| 2. no distractor whose gloss shares a content word with the key's | `content_words()` over every pt-BR gloss of every sense, parentheticals and stop words dropped, plural -s folded; also applied to the kanji-by-meaning MCQ | 0 recognition rows with an overlapping distractor (audited over the whole table). 深刻 is now a cloze over 深刻な問題だな。 |
| 3. a cloze on a conjugated form blanks the whole form | `whole_form_end()`: a token in a non-final form is carried over its auxiliaries (stops after a final-form one) and over a directly attached て/で/ば | 66 clozes extended: 分からなかった, 乗ります, 消した, 見せて, 聞こえます... |
| 4. no production item for a bound morpheme | `is_bound()` (suf/pref/n-suf/n-pref/aux tags, or a pure counter). Their MCQ may take other bound forms as distractors and asks "Qual destas formas" | 0 production items on bound records; ご and お are now MCQs |

Found along the way and fixed in the same pass:

- **Homograph guard (`sense_fits`).** The bank links なり in 行かなければなりませんか to
  vocab:1611000 (生る, "dar fruto"). A cloze over it would have explained the blank as "dar fruto".
  The token's own pt-BR gloss must now share a content word with the record's glosses; a cloze that
  fails it falls back to the next sentence or to MCQ.
- **Forward-reference guard.** The first apply grew check C5 (same-topic 1 -> 2, same-level 14 -> 47,
  cross-level 160 -> 176): `derive_needs.py` counts a cited sentence's grammar TAGS as uses, and 50
  i+0 sentences (every kanji and word known) carried a tag taught later (e.g. gram:n3-okagede on
  あなたのおかげです。 cited in `les:n5-desu-wa-01`). That apply was reversed in the index and the
  sources (verified: `course/` byte-equal to HEAD again), and `sentence_ok` now also requires every
  reference `derive_needs` expands from the sentence to be taught at or before the lesson. The table
  was regenerated and re-applied: C5 back to 1 / 14 / 160.
- **Split-mode A tokens.** `token_spans()` gave up on any sentence whose dissection lists the
  A-unit parts before the C unit (日本 + 語 + 日本語). It now reads the C layer only, which is what
  tiles the sentence.
- **Applier bug: cited sentences were never written to the index.** `apply_practice_exercises.py`
  inserted the exercise and its texts but not `exercise_sentence`, so the export published
  `sentence_refs: []` and 77 clozes were not credited. The kanji table cites no sentence, which is
  why nobody noticed. The applier now writes (and re-asserts) the rows. The replay handler already
  compares `sentence_refs`, so a regression fails `validate_repairs_applied`.

## 3. Template mix, before and after

Before = the table committed on 2026-09-09 (pre-W13 apply, pre-W21b). After = this apply.

| | rows | cloze | recognition | production |
|---|---:|---:|---:|---:|
| **before** | 2,311 | 185 (8.0%) | **2,111 (91.3%)** | 15 (0.6%) |
| **after** | 2,283 | **618 (27.1%)** | 1,651 (72.3%) | 14 (0.6%) |
| N3 before | 1,187 | 43 (3.6%) | 1,143 (96.3%) | 1 |
| **N3 after** | 1,189 | **461 (38.8%)** | 728 (61.2%) | 0 |
| N4 before / after | 591 / 567 | 101 / 96 | 488 / 468 | 2 / 3 |
| N5 before / after | 529 / 523 | 41 / 61 | 478 / 453 | 10 / 9 |

N3 converted as predicted: 459 of its 461 clozes are over real (Tatoeba) sentences, 565 of 618
overall. The W13 sentences are what made it possible. Recognition is still the majority at N5/N4,
where the known set is too small for an i+0 sentence.

Rows by target: vocab 2,242, grammar 24 (cloze), kanji 17 (recognition 12, cloze 3, production 2).
One grammar pair (gram:ga-arimasu) is closed by its sibling row (gram:ga, same が blank over a
sentence tagged with both) and the row names both targets.

## 4. Pending drills (W21b's 76)

All 76 have a drill in their new home: vocab 49 (the vocab templates), grammar 10 (か and が as
one-particle clozes over tagged sentences; でしょう over an untagged sentence that spells it;
が of があります on a tagged sentence too short to lose the whole form), kanji 17 through a word
written with the kanji (cloze or MCQ with the kanji in the key), a kanji-by-meaning MCQ over the
lesson's kanji known set when no known word carries it (時, 話, 語), or writing the word with the
kanji, kana not accepted (分かる, 来る in `les:n5-desu-wa-02`, whose known set is three kanji).
`pending_drills.items` is now empty and its ceiling 0. The block stays so a future move is named
there again.

## 5. Practice ratchet

`validate_practice_coverage`, exported tree, HEAD -> now:

| level | kind | absent before | absent after |
|---|---|---:|---:|
| pre-n5 | vocab | 4 | **0** |
| n5 | vocab | 497 (461 + 36 pending) | **0** |
| n5 | kanji | 14 (pending) | 0 |
| n5 | grammar | 25 (16 + 9 pending) | 12 |
| n4 | vocab | 560 (550 + 10 pending) | **0** |
| n4 | kanji | 1 (pending) | 0 |
| n4 | grammar | 12 | 6 |
| n3 | vocab | 1,181 (1,178 + 3 pending) | **0** |
| n3 | kanji | 2 (pending) | 0 |
| n3 | grammar | 7 (6 + 1 pending) | 1 |
| **total** | | **2,303 absent, 1,776 practised (43.5%)** | **19 absent, 4,060 practised (99.5%)** |

Ceilings re-frozen with `--write-baseline`. Vocab absent is 0 at every level; pending drills 0. The
19 left are grammar: no tagged or spelled sentence inside the lesson's known set (12), no aligned
form span (4), no probe segment (3). That is the authored residue, one agent's work, listed in
`research/derived/pending/practice_vocab_residue.json`.

Exercises 2,463 -> 4,746. Lessons touched 263; median 9 new exercises per lesson, max 19.

## 6. Lessons did not degrade (rendered diff against HEAD)

Over every changed file under `course/`: 264 lesson JSONs, 263 `.md` views, 30 `topic.json`.
- lesson bodies with the `<exercise ref>` nodes stripped: **0 differences**;
- existing exercises: **0 changed** (every new one is appended);
- every other lesson field (unlocks, cks, sentence_refs, title...): 0 changes, except `needs`;
- rendered `.md`: **0 lines removed**, 11,415 added (the new exercise blocks).

`needs` changed on 116 lessons (and its mirror in 30 `topic.json`): `derive_needs.py` reads each
exercise's cited sentences as references, so the new clozes add uses of earlier-taught items and
check C4 required the stored DAG to be re-derived. `build_needs_table.py` ->
`apply_lesson_needs.py --replace` (the recipe `apply_forward_refs.py` documents): 760 -> 741 rows
(derived 716 -> 697; the transitive reduction drops edges that the new ones make redundant), roots
unchanged at 4. `needs[]` is record metadata, not rendered prose.

`validate_exercise_contracts`: 0 FAIL (4,746 exercises; cross-lesson duplicates still the 2 known).

## 7. Twenty sample items (seeded draw, stratified by type and level)

| # | nível | lição / id | tipo | alvo | prompt (pt-BR) | resposta | distratores |
|---|---|---|---|---|---|---|---|
| 1 | n3 | `les:n3-concessao-07` / `ex:n3-concessao-07-16` | cloze | `vocab:1365520` | Complete a frase: 私は自由の＿＿だ。 (Estou livre.) | 身 / 私は自由の身だ。 | - |
| 2 | n3 | `les:n3-estrutura-03` / `ex:n3-estrutura-03-25` | cloze | `vocab:1362730` | Complete a frase: ＿＿な問題だな。 (É um problema sério, hein.) | 深刻 / 深刻な問題だな。 | - |
| 3 | n3 | `les:n3-enfase-04` / `ex:n3-enfase-04-21` | cloze | `vocab:1347830` | Complete a frase: 遠くに＿＿が見えた。 (Dava para ver uma cabana ao longe.) | 小屋 / 遠くに小屋が見えた。 | - |
| 4 | n3 | `les:n3-intencao-01` / `ex:n3-intencao-01-18` | cloze | `vocab:1220570` | Complete a frase: ＿＿しない方がいいよ。 (Melhor não criar expectativa.) | 期待 / 期待しない方がいいよ。 | - |
| 5 | n4 | `les:n4-volitivo-03` / `ex:n4-volitivo-03-12` | cloze | `vocab:1576250` | Complete a frase: ＿＿にたくさん食べないで (Não come tudo de uma vez só.) | 一度 / 一度にたくさん食べないで | - |
| 6 | n4 | `les:n4-volitivo-04` / `ex:n4-volitivo-04-12` | cloze | `vocab:1155060` | Complete a frase: 千円＿＿の本を買いました (Comprei um livro de mil ienes ou menos.) | いか / 千円いかの本を買いました | - |
| 7 | n5 | `les:n5-particulas-lugar-03` / `ex:n5-particulas-lugar-03-9` | cloze | `vocab:1269320` | Complete a frase: また＿＿で。 (Até mais tarde.) | 後 / また後で。 | - |
| 8 | n5 | `les:n5-desu-wa-02` / `ex:n5-desu-wa-02-10` | cloze | `vocab:1577140` | Complete a frase: それが＿＿から来たのか分からなかった。 (Eu não sabia de onde aquilo tinha vindo.) | どこ / それがどこから来たのか分からなかった。 | - |
| 9 | n3 | `les:n3-tempo-07` / `ex:n3-tempo-07-16` | recognition | `vocab:1612920` | Qual destas palavras significa "atropelar"? | ひく | おどろく / おとす / なおる |
| 10 | n3 | `les:n3-deveres-03` / `ex:n3-deveres-03-19` | recognition | `vocab:1219490` | Qual destas palavras significa "estranho, esquisito" (no sentido de peculiar)? | きみょう | きちょう / わがまま / きのどく |
| 11 | n3 | `les:n3-estado-05` / `ex:n3-estado-05-19` | recognition | `vocab:1380760` | Qual destas palavras significa "produto, mercadoria"? | せいひん | れつ / ふくろ / りそう |
| 12 | n4 | `les:n4-experiencia-01` / `ex:n4-experiencia-01-21` | recognition | `vocab:1511790` | Qual destas palavras significa "arrumar, organizar"? | かたづける | よぶ / そだてる / すすむ |
| 13 | n4 | `les:n4-obrigacao-02` / `ex:n4-obrigacao-02-12` | recognition | `vocab:1310260` | Qual destas palavras significa "preparativos, preparação"? | したく | ホテル / ばしょ / かれら |
| 14 | n5 | `les:n5-adjetivos-04` / `ex:n5-adjetivos-04-7` | recognition | `vocab:1580480` | Qual destas palavras significa "resistente, durável"? | じょうぶ | たいせつ / けっこう / だいじょうぶ |
| 15 | n5 | `les:n5-comparacoes-05` / `ex:n5-comparacoes-05-9` | recognition | `vocab:1360010` | Qual destas palavras significa "dormir, ir para a cama"? | ねる | ならぶ / いる / しぬ |
| 16 | n5 | `les:n5-comparacoes-02` / `ex:n5-comparacoes-02-11` | production | `vocab:1582300` | Escreva em japonês a palavra que significa "e coisas assim, etc.". | など (aceita: など) | - |
| 17 | n5 | `les:n5-particulas-lugar-07` / `ex:n5-particulas-lugar-07-8` | production | `vocab:1006730` | Escreva em japonês a palavra que significa "e, e então". | そして (aceita: そして) | - |
| 18 | n5 | `les:n5-perguntas-02` / `ex:n5-perguntas-02-14` | recognition | `kanji:木` | Qual destas palavras significa "árvore"? | 木 | 人 / 新聞 / 千 |
| 19 | n5 | `les:n5-perguntas-03` / `ex:n5-perguntas-03-19` | recognition | `kanji:電` | Qual destas palavras significa "trem, trem elétrico"? | 電車 | 木 / 車 / 先生 |
| 20 | n5 | `les:n5-te-form-03` / `ex:n5-te-form-03-16` | cloze | `gram:te-iru` | Complete a frase: ただ見＿＿だけです。 (Estou só olhando.) | ている / ただ見ているだけです。 | - |

My own read of the 20: all answerable and correct. Worth a reviewer's eye: #6 is a real sentence
that writes 以下 in kana (いか), so the key is kana; #10 puts きちょう next to きみょう (legal, since
the glosses differ, but the two look alike); #16 and #17 are production because these early lessons
have no three same-POS distractors (など is a particle but not tagged bound, and in an N5 lesson
it is taught as a word).

The pending-drill items that needed new templates, verbatim:
- `les:n5-desu-wa-01` gram:ka: いくらです＿＿？ (Quanto custa?) -> か
- `les:n5-verbos-01` gram:ga + gram:ga-arimasu: 痔＿＿あります。 (Tenho hemorroidas.) -> が. The
  lesson already renders this sentence; the choice is odd but it is the lesson's own.
- `les:n5-adjetivos-05` gram:deshou: 分かった＿＿？ (Entendeu, né?) -> でしょう
- `les:n5-desu-wa-03` kanji:時: "Qual destes kanji significa "tempo, hora"?" 来 / 時 / 何 / 分
- `les:n5-desu-wa-02` kanji:分 / 来: "Escreva com kanji a palavra que significa "entender,
  compreender"." -> 分かる (kana not accepted), same for 来る
- `les:n4-passiva-02` ご: "Qual destas formas significa "prefixo honorífico (antes de
  substantivos)"?" ご among さま / はず / せんぱい

## 8. Gate

`validate_all.py`: ALL HARD VALIDATORS PASS, including the quick replay. `validate_repairs_applied`:
21,124 rows, 21,103 PASS + 21 checked skips, 0 FAIL; the new table 2,283/2,283.
`validate_lesson_gating`: 0 FAIL, C5 forward uses/edges 1/14/160 (unchanged). Not a checkpoint: the
full replay was not run.

## 9. Open

- **Fable sample of 30 on the applied rows** (APP_PLAN §1 step 5) is still owed. §7 is my own
  stratified read, not that sample.
- **Grammar residue 19**: one agent's authoring.
- **Per-exercise provenance** in the export is still all-or-nothing (2,463 -> 4,746 exercises); the
  claim lives in the table's `provenance` header and `needs_review = 1` on every row.
- The bank's homograph link なり -> 生る ("dar fruto") in 行かなければなりませんか is a data defect the
  generator now steps around; the link itself is not fixed here.
- 19 new items in one lesson (`les:n3-desejos-01` class) is still a teacher's call.
