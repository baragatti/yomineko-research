# P1-exam-fixes: builder patches applied, auto-built banks rebuilt, six card examples re-derived

Date 2026-09-23. Checkpoint unit (full replay run, section 6). Mechanical: derived only, authored 0.
No lesson body, unlock or exercise moved.

## 1. What was applied

| patch | applies on the current tree | what it does |
|---|---|---|
| `research/derived/patches/exam_equivalence_filter.patch` | yes (hunks 7-9 at +2 lines offset, no fuzz) | `design/exam_equivalents.json` + `exam_rules.interchangeable`: an option as right as the key is refused (the 16 second-answer items) |
| `research/derived/patches/exam_builder_fixes_2.patch` | yes, clean on top of patch 1 | 18a gf blanks on SudachiPy token boundaries; 18b a distractor attested in the same slot (or one that turns the stem into a bank sentence) is refused; 18c `x not in pre + post`; 19 `MIN_STEM_CONTENT = 2` |
| `research/derived/patches/exam_taught_word_rule.patch` | yes, clean on top of 1 + 2 | fix 20: kanji_reading / orthography targets must be a word the exported lessons unlock at or below the level |

The taught-word patch was applied because `research/reports/exam_taught_word_rule.md` shows every
family at or above 3x its paper (lowest: n5 orthography 177 stems for a 15-item floor, 11.8x;
kanji_reading n5 176 for 21). On today's tree it drops nothing (`target-word-not-taught` 0) and every
kanji_reading bank and the n5/n4 orthography banks are byte-identical to HEAD: the rule is pinned, not
exercised. `exam_rules.py`'s self-check passes.

Only `scripts/export/build_exam_banks.py` was rerun (the 18 auto-built banks). The authored banks
(paraphrase, usage, listening, reading_comp) were not rebuilt and did not change.

## 2. Per bank, HEAD to now

| bank | items | changed | dropped | added | unchanged |
|---|---|---|---|---|---|
| n5_grammar_form | 114 -> 75 | 52 | 39 | 0 | 23 |
| n4_grammar_form | 300 -> 300 | 171 | 53 | 53 | 76 |
| n3_grammar_form | 300 -> 300 | 175 | 48 | 48 | 77 |
| n5_text_grammar | 34 -> 34 | 28 | 0 | 0 | 6 |
| n4_text_grammar | 74 -> 75 | 53 | 0 | 1 | 21 |
| n3_text_grammar | 122 -> 122 | 78 | 0 | 0 | 44 |
| n4_context_fill | 400 -> 400 | 1 | 0 | 0 | 399 |
| n3_orthography | 400 -> 400 | 1 | 0 | 0 | 399 |
| the other 10 auto-built banks | unchanged | 0 | 0 | 0 | all |

All banks: 5,141 -> 5,103 items. Drop reasons recorded by the builder on grammar_form:
`stem-too-short` 106, `blank-cuts-a-word` 54 (both new rules; the rest are pre-existing level and
single-occurrence drops); n4/n3 backfill to their 300 cap.

**Split of that diff.** The HEAD builder run on today's tree (scratch, `--out`) differs from the
committed banks in 22 items, before any patch: 17 grammar_form explanations now come from the W08b
survivor's `form_meanings` (W08b's E1 re-pointed `grammar` byte-level but left the loser's
explanation text: e.g. gf:n5:4308 "não é / não está (casual)" -> "não é (coloquial)"), 4 n5
distractors pick up のがじょうず (the merged no-ga-jouzu), and 1 n4 text_grammar item appears
(tg:n4:n4-dar-receber-03-01, 来（てほしい）). Everything else is the patches: n5 gf 50 changed + 39
dropped, n4 gf 167 + 53/53, n3 gf 175 + 48/48, tg 28 / 54 / 78, cf 1, or 1. These match the
measured scratch run in `exam_builder_fixes_2.md` exactly for gf n3/n5 and tg, and within the drift
above for n4 gf.

## 3. The named findings are gone

Checked item by item against `research/derived/pending/exam_equivalent_distractors.json`: "gone"
means the item no longer offers the wrong-but-right option (replaced) or no longer exists (dropped).

| finding | count | replaced | dropped | still present |
|---|---|---|---|---|
| second correct answer (`flagged`) | 16 | 13 | 3 (gf:n4:3845, gf:n5:63, gf:n5:4328: stem too short) | **0** |
| no-context distractor, high confidence | 51 | 34 | 17 | **0** |
| no-context distractor, low confidence | 27 | 22 | 5 | 0 |
| gf blank cuts a word | 10 | 0 | 10 | **0** |

gf:n4:3853 (the residual patch 1 alone created, たらどうですか after 大切にし) now offers
と言ってもいい / ことができる / かもしれない. The 39 "starts mid-token" items: 37 dropped, 2 re-keyed to
the whole form (gf:n4:3414 考え（させる）, gf:n4:3444 借り（られる）).

## 4. Gates on the banks

- `validate_exam_level_gate.py`: ALL OK. Every deterministic family at ceiling 0 at every level (18
  family-levels, 0 inappropriate items); lowest pool n5_grammar_form 75 items = 8.3x its paper of 9.
  The 175 over-level items are the listening banks, as before (W18b).
- `validate_exam_banks.py`: ALL OK.
- `validate_exam_stem_collisions.py`: 0 items in 0 groups.

## 5. Downstream artifacts re-derived

| artifact | before -> after | note |
|---|---|---|
| `course/item_lesson_index.json` | exam items placed 4,970 / 5,141 -> 4,932 / 5,103 | unplaced unchanged at 171; `validate_placement_index.EXAM_FLOOR` 4970 -> 4932 re-recorded with that cause |
| `course/topic_tests.json` | pool entries 13,199 -> 13,131 | 49 tests, 3 exempt, every mix still satisfiable |
| `corpus/capabilities/registry.json` | exam_link rows -> 772 on 118 caps | re-derived by `build_capabilities.py` on the new banks |
| review views | n5 exams view (+ build stamps) | `build_review_views.py --level n5,speak` after the contracts |
| contracts | `exam_item` records 5,141 -> 5,103 | infer_shapes -> build_schemas -> build_manifest, then `npm run sync-data` |

**Replay gate.** Five W08b `exam-item` rows (E1) addressed items the new rules dropped (gf:n3:5140,
gf:n4:3409, gf:n4:3410, gf:n4:3540, gf:n5:4308). Each row now carries `retired_by: p1-exam-fixes` and
a `retired_why` naming the rule (18a or 19); `handle_w08b_merges` skips an exam-item row only when its
item is absent AND the row carries that marker, and still checks `grammar` if the item exists.
Plant: removing the marker from gf:n5:4308's row fails the gate on that address (caught), restored
passes.

## 6. W28 card examples (C13 open item)

`scripts/derive_card_examples.py` re-run on the current export; table
`research/derived/repairs/card_examples.json` rewritten by it (2,242 -> 2,232 rows) and applied with
`apply_card_examples.py --replace` (5 rewrites, 10 orphans deleted). The six cards C13 named:

| lesson / card | was | now |
|---|---|---|
| les:n5-numeros-tempo-03 kanji:話 | tatoeba-122326 話せる | tatoeba-77200 話 (i+1 within budget) |
| les:n5-numeros-tempo-03 gram:gp-43 | tatoeba-122326 | **no example** (none-passes-display-rule) |
| les:n5-numeros-tempo-03 kanji:語 | tatoeba-122326 日本語 | **no example** (none-passes-display-rule) |
| les:n5-numeros-tempo-03 vocab:1415870 たくさん | tatoeba-122326 | **no example** (none-passes-display-rule) |
| les:n4-condicionais-04 gram:gp-120 | tatoeba-193408 もし | gen-40a736aa4ac8 もし (i+0) |
| les:n3-tempo-02 gram:n3-tabi-ni | tatoeba-11022968 | tatoeba-221453 たびに (i+1 within budget) |

The re-derivation also settled what C12 left in the table: 7 rows for W08b losers' cards (no longer
issued; the live apply refused them) are gone, and two survivors re-rank on the sentences they
inherited (les:n5-desu-wa-03 janai-dewa-nai -> tatoeba-536769, les:n4-forma-simples-03 gp-118 ->
tatoeba-172845 しか). Exported card examples 2,235 -> 2,232. Three cards lost an example because C13
stopped rendering tatoeba-122326 and no other sentence passes the display rule at that lesson: the
no-example ratchet is re-recorded with that cause (vocab 1695 -> 1696, kanji 52 -> 53; gram stays 90).
Getting them back is a lesson render or bank growth at N5, not a card change.

## 7. Lessons did not degrade

Rendered diff of `course/` against HEAD, by JSON leaf: 5 lesson files change, and only under
`srs.introduces_cards[].example` (the section 6 rows). 0 `.md` files, 0 body, unlock, exercise or
needs leaves. `course/item_lesson_index.json` and `course/topic_tests.json` are derived indexes.

## 8. Sample: 20 changed or added items (seeded random over the 8 changed banks)

Read against the Japanese. Before = HEAD, after = now; key first.

| id | before | after | read |
|---|---|---|---|
| gf:n3:5036 | この写真を見る（　）、父を思い出す。 = たびに / くらい / 上げる / ないと | = たびに / 上げる / ないと / つまり | ok |
| gf:n3:5156 | 間に人を入れ（　）解決しよう。 = ずに / など / ても / こと | = ずに / など / こと / きり | ok (入れても dropped) |
| gf:n3:5350 | 彼は四ペソ（　）んだ。 = しかない / 切れない / なぜなら / に関して | = しかない / 切れない / なぜなら / たとたん | ok |
| gf:n3:5366 | 彼はぐち（　）こぼしている。 = ばかり / かなあ / たびに / ないと | = ばかり / かなあ / たびに / べきだ | ok |
| gf:n3:5479 | 早く週末にならない（　）。 = かなあ / うちに / 最中に / べきだ | = かなあ / てみる / ないと / だけど | ok (ならないうちに fitted) |
| gf:n3:5484 | パターンがある（　）。 = はずだ / ばかり / せいで / ことだ | = はずだ / その上 / なんか / 上げる | ok (あることだ fitted) |
| tg:n3:n3-conectores-06-01 | 通学し（　）。 = ている / その上 / という / てみる | = ている / その上 / とおり / 上げる | ok |
| tg:n3:n3-tempo-07-02 | こわかった（　）に気がついた。 = こと / まで / さえ / きり | = こと / さえ / ても / たて | ok |
| gf:n4:3356 | 雨天の（　）運動会を中止する。 = 場合は / ところ / ごとに / ですが | = 場合は / ごとに / にくい / がする | ok |
| gf:n4:3793 | きつい仕事という（　）。 = ことになる / がっている / ばよかった / ようになる | = ことになる / がっている / ばよかった / からできる | ok |
| gf:n4:3835 | お茶（　）いかがでしょう。 = など / かい / まず / ぜひ | = など / まず / ぜひ / れば | ok |
| gf:n4:3899 | ロッジはひぎめでかり（　）。 = られる / てくる / なさる / みたい | = られる / なさる / みたい / ごとに | ok (かりてくる fitted) |
| gf:n4:3903 | (new) | 自分一人で生き（　）人はいない。 = られる / こんな / ように / にする | ok |
| gf:n4:4000 | (new) | この歌は私を楽しませ（　）。 = てくれる / みたいに / に見える / んですが | ok |
| tg:n4:n4-oracoes-relativas-07-01 | 母がよく話し（　）先生でした。 = ていた / それに / にする / やすい | = ていた / それに / にする / かかる | ok (話しやすい先生 fitted) |
| tg:n4:n4-volitivo-02-01 | いい店だと思うと言っ（　）。 = ていた / てみる / ごとに / ておく | = ていた / ごとに / こんな / がする | ok |
| gf:n5:4310 | なんかいい車（　）。 = じゃない / どうして / がいます / たくさん | = じゃない / たくさん / ましょう / けっこう | ok |
| gf:n5:4382 | もっと休みをとっ（　）。 = たほうがいい / けっこうです / てもいいです / じゃなかった | = たほうがいい / けっこうです / じゃなかった / のがじょうず | ok (とってもいいです fitted) |
| tg:n5:n5-comparacoes-04-01 | （　）、おとうさんはねこより… = でも / まで / する / どこ | = でも / まで / なあ / くる | ok |
| tg:n5:n5-conectando-07-01 | まだむずかしいです（　）、とてもおもしろいです。 = けど / なあ / どこ / あれ | = けど / どこ / あれ / する | ok |

20 of 20: no new distractor fits its stem. Seven of the 20 had a removed distractor that did fit
(noted). As the builder report says, the surviving distractors are more often wrong by form than by
meaning (limit 2 in `exam_builder_fixes_2.md`); the ~7 lemma-level residual fits it lists stay for the
teacher loop.

## 9. Full replay (checkpoint)

`validate_index_rebuildable.py` (full mode, 790 exported files): **0 new, 0 healed, 460 held with
unchanged bytes, 111 held entries whose rebuilt bytes moved.** All 111 are files C13 changed
(4ffc753a -> ead12d29); 4 of them are also this unit's card-example lessons. Every one already carries
the `course-identity` diagnosis. What moved is C13's manifest steps 142-144 (lesson body spans,
furigana residue), which committed on the quick replay only and are replayed here for the first time.

Do they reproduce? For each moved file, the leaves (JSON) or lines (`.md`) C13 changed were checked
against the places where the rebuild still differs from the committed file: 144 C13 changes, and
every one reproduces except one checklist line in `course/n4/topic-37-kanji-exame/lesson-01.json`.
That line lists different kanji in the replay (不 / 世 instead of 乗 / 低), which is the known
kanji-exame divergence of `course-identity`, so C13's furigana on 乗 has no line to land on. Card
examples reproduce in all 5 lessons this unit touched; the only card difference in
les:n5-numeros-tempo-03 is an existing homograph resolution (vocab:2147990 vs 1472650). The
baseline was re-recorded with `--record`. Each of the 111 causes keeps its diagnosis and gets a
dated re-pin note.

## 10. Open

- Three N5 cards without an example (section 6): a render or bank growth at les:n5-numeros-tempo-03.
- `build_capabilities.py` still reads unlock refs from the DB unresolved (the taught-word report's
  finding: 3,185 bank items reach no capability, ~1,881 of them kanji_reading / orthography).
- Residual lemma-level fits (~7 items, under 1% of gf/tg) and distractor concentration: teacher loop.
- Fable sample 30 on the W18 banks is still owed; this report's 20 is the read for this unit.
