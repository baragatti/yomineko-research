# W12 — orthographic relink

> Unit W12 of [`APP_PLAN.md`](APP_PLAN.md) §6 step 2. MECHANICAL: a script, no authoring — nothing in
> Japanese or pt-BR was written, only existing bank sentences linked to existing vocabulary records.
> Run 2026-09-09. Full gate green.

## What the audit claimed, and what is actually there

`readiness/content_coverage_levels.md` §2.4 / G2 measured that **788 of the 1,545 zero-coverage
vocabulary records do occur in the bank** and were never linked to — "an orthography/tokenisation
miss, not missing content" — and that fixing the linking alone lifts **568 records** over the ≥3
floor, N5 to 99.3% and N4 to 99.2%. `readiness/srs_fsrs.md` G3 recorded a second, independent defect:
the exporter publishes `tokens[].vocab` but drops the sentence-level `sentence_vocab` edge, so
**343 carded words lose their example purely in the export**.

Re-derived on today's tree, one of those two numbers survives intact and the other does not.

**The 343 is exact.** Cards with an example went **1,406 → 1,749 of 2,951 (47.6% → 59.3%)**, +343,
of which +60 come from the new token links and +283 from publishing the edge.

**The 568 is measured with a substring test, and a substring test is fiction at this scale.** The
audit counted a record as "present in the bank" when its headword or kana appears *as a substring* of
`jp`. On the pre-W12 tree that rule claims 51 N5 + 38 N4 + 510 N3 = **599** liftable records. But
区/く "occurs" in 1,783 sentences because く ends every adverbial adjective; 家/け in 754; 中/ちゅう in
157 (inside compounds); 下さい/ください in 178 (where the token is an inflection of くださる, a different
entry). That is the tiling problem `validate_practice_coverage.py` had to solve, and the reason
`validate_sentence_coverage.py` counts token dissection and refuses to guess.

Matching on Sudachi's own token boundaries, by **lemma AND reading**, the same records yield
**57 lifted at N5/N4** (36 N5, 21 N4) — not 89 — and 101 more at N3. The rest of the audit's 568 is
substring noise. The direction of its finding was right and the size was not; every record it named
by hand (一つ, 二つ, ５日, 詰らない/つまらない, 許り/ばかり, 其れから/それから, 程) is fixed here.

## 1. Result

| | before | after |
|---|---|---|
| links added (`token.vocab_id` + `sentence_vocab`) | — | **663** over **63** records |
| N5/N4 taught records lifted over the ≥3 floor | — | **57** (36 N5, 21 N4) |
| distinct vocab reachable from a bank token | 1,449 | **1,509** |
| distinct vocab reachable from the published sentence edge | 0 (dropped on export) | **1,793** |
| SRS vocab cards that can show an example | 1,406 (47.6%) | **1,749 (59.3%)** |
| lessons whose rendered sentence list changed | — | **0** |
| sentences removed from a lesson | — | **0** |

### Links by rule

| rule | links | what it matches |
|---|---|---|
| `run-reading` | 364 | 2–5 contiguous C tokens whose concatenated surface **and** reading are a registered form (一+つ, ５+日, お+茶, それ+に) |
| `kana-exact` | 237 | one token whose lemma/surface is a registered form and whose reading is a registered kana form (丈/だけ, 個/こ, 位/くらい) |
| `kana-function-word` | 48 | as above where JMdict files the word `n`/`adv` and Sudachi tags it a particle — allowed only for `uk` entries of ≥2 morae (程/ほど, 宛/ずつ) |
| `run-kana-surface` | 14 | a kana run where the **spelling** carries the identity because は realizes as わ (それでは → 其れでは) |

### What the guards refused (the same run's counters)

| guard | dropped | why it exists |
|---|---|---|
| run starts on a particle/auxiliary | 40,423 | と+お in 「コーヒーとお茶と…」 otherwise reads as 十/とお and claims the span お茶 needed |
| run is all particles/auxiliaries | 3,893 | で+も, で+は, だ+から are two morphemes; the merged spelling coinciding with a conjunction entry is a coincidence in 47 of 49 でも cases |
| longer match already claimed the span | 656 | longest match wins even when this script cannot use it |
| ambiguous — more than one record matches | 78 runs, 21 tokens | 位/くらい names two entries, あたり names 辺り and 当たり; preferring the under-covered one is bias, not evidence |
| kana run containing an inflected verb | 56 | 嘘をついて is つく+て, not について; そうして is そう+する+て, not the conjunction |
| kana spelling with no "usually kana" signal | 12 | い+た (いる+た) otherwise reads as 板/いた and 64 progressive-past clauses become "board" |
| no free token in the span | 15 | １０日 is １０→一〇 plus 日→日, both already linked; this script never re-points |

The homograph discipline W11 settled is reused, not bypassed: the reading is the discriminator
throughout. Sudachi lemmatises both 行った (いっ) and 行なった (おこなっ) as 行う; only the reading tells
them apart, and only the reading keeps 科/可/課 out of the question particle か.

## 2. The exporter defect

`scripts/export/export_corpus.py::export_sentences` built `tokens[]` from `token.vocab_id` and never
read `sentence_vocab`, so the sentence-level edge existed in the index and in nothing that ships.
That table is not a projection of `token.vocab_id` — `scripts/ingest/build_sentence_vocab.py` argues
this at length — it is the union of three passes (the dissector's per-token links, the 2026-06-15 run
relinker, the 2026-07-05 lemma tagger) and it knows **1,793** distinct records where `tokens[].vocab`
knew 1,449. A word Sudachi cuts in two (お+茶, 一+つ) had no single token to hang a slug on and
vanished from the export entirely.

The fix publishes it as `sentence.vocab[]`, **with provenance** rather than as a bare list:

```json
"vocab": [{"ref": "vocab:1002430", "link_rule": "run", "reading_verified": true}, …]
```

because the three rules are not equally trustworthy — `run` and `lemma` rows were built without
checking the reading, and 20.7% of them disagree with the record's dictionary reading (年 read ねん
linked to 年/とし). A consumer choosing a card example should prefer `reading_verified`; a consumer
counting coverage should keep using `tokens[].vocab`, which is the only per-occurrence claim.
`validate_sentence_coverage.py` is therefore **unchanged** and still counts token dissection only —
the coverage numbers below are earned by real per-token links, not by the exporter fix.

`bank.json` grows 50,999,856 → 55,953,385 bytes.

## 3. Apply and tracking

- Script: `scripts/apply_orthographic_relinks.py` (`--derive` re-derives, `--check` verifies,
  no flag applies). Writes both places `persist_dissection.py` writes: `token.vocab_id` on the
  span's first free token, and `sentence_vocab` with `link_rule='ortho'` and a `reading_verified`
  computed the way `build_sentence_vocab.py` computes it. It never calls `recompute_all_levels()`.
- Table: `research/derived/repairs/orthographic_relinks.json`, 663 rows, one per link, addressed by
  **sentence slug + token span + the span's surfaces and reading** — never by row id. Registered in
  `validate_repairs_applied.py`'s `REGISTRY` with a handler that replays every row against the
  shipped bank (2,208 rows replayed clean across all tables).
- Idempotent: second run reports `0 written, 663 already linked, 0 inserted, 0 write(s)`.
- Rebuild manifest: inserted at **step 114**, after 113's homograph rulings and before the family
  builders (renumbered 115–117; the one prose reference to "step 116" moved with them).

One design point the replay forced: the anchor is chosen **against the tree in hand**, not pinned in
the row. The 県下 span anchors on 県 in this index and on 下 in a manifest replay, because the replay
links 県/けん where nine months of ad-hoc scripts had left it unlinked. Pinning the position produced
44 false failures in the first full replay. What is exact-matched is the span, its surfaces, its
reading and the record; which token of a verified span carries the id is an implementation detail.

## 4. Effect on lessons

**0 lessons changed their rendered sentence list, and no sentence was removed from any lesson.** The
premise that a re-export re-selects examples from the known set does not hold for this exporter:
`export_course.py` derives `sentence_refs` from the stored lesson **body** (`<sentence ref="…"/>`),
not from a selection over the corpus, so `git status course/` is empty after a full re-export. Only
`corpus/sentences/bank.json` moved.

What the new links *do* touch is `validate_lesson_gating.py`'s check D, which counts the unknown
vocabulary a displayed sentence carries. Its result, quoted:

```
validate_lesson_gating: 322 lessons, 5291 item refs, 624 sentence links
  | A 0 FAIL, B 0 FAIL (3 exempt), C 0 FAIL, D 0 FAIL | 0 FAIL total
  ADVISORY: sentence fit 178/624 above lesson level, 148/624 over the i+1 budget
            (304 with new kanji, 227 with new vocab) — 248 pairs queued in
            research/reports/lesson_sentence_review.json
```

Two counters moved and the frozen baseline was re-recorded, which is a ratchet **loosening on one
counter** and needs to be seen:

| counter | baseline | now | cause |
|---|---|---|---|
| `pairs_above_level` | 178 | 178 | — |
| `pairs_with_new_kanji` | 304 | 304 | — |
| `pairs_with_new_vocab` | 228 | **227** | shrank (−4 pre-existing, +3 from W12) |
| `pairs_over_budget` | 147 | **148** | **grew by one** |
| `over_budget_by_level[n5]` | 101 | **102** | the same pair |

The single new over-budget pair is `les:n5-perguntas-03` × `sent:tatoeba-5675047` 「どれくらい？」,
load 2 against an N5 budget of 1, because 位/くらい is now linked there and `les:n5-perguntas-05`
teaches it two lessons later. Three more pairs gained a known-late word without exceeding budget:
`les:n4-oracoes-relativas-05` × 「そんなに金は出せない。」 and 「そんなに待ちたくない。」 (そんなに), and
`les:n4-potencial-01` × 「二週間ほど借りられるかい。」 (程). **None of these is new debt** — the sentence
always contained the word; the missing link was hiding it, which is exactly the under-count W12
exists to fix. All four are now queued for the teacher in `lesson_sentence_review.json`. No lesson
prose was touched.

## 5. W05 ratchet — before and after

Re-recorded only after the rest of the gate was green. Nothing grew.

| level \| kind | below (before → after) | zero (before → after) |
|---|---|---|
| n5 \| vocab | 55 → **19** (−36) | 51 → **14** (−37) |
| n4 \| vocab | 40 → **19** (−21) | 33 → **10** (−23) |
| n5 \| grammar | 15 → 15 | 0 → 0 |
| n4 \| grammar | 16 → 16 | 0 → 0 |
| n3 \| grammar | 67 → 67 | 17 → 17 |
| n3 \| vocab | 1,571 → 1,571 | 1,461 → 1,461 |
| n1 \| vocab | 0 → 0 | 0 → 0 |

N5 taught vocabulary at or above the floor: 648/703 → **684/703 (97.3%)**. N4: 611/651 →
**632/651 (97.1%)**. The audit projected 99.3% / 99.2% from the substring measure; the honest token
measure lands 2 points lower, and §6 says what is left.

## 6. Rebuildability

```
--quick : [OK] 4 exported file(s) checked, 4 held by rebuild_baseline.json at the recorded bytes
--full  : compared 790 exported file(s) in 87s
          [OK] 790 exported file(s) checked, 643 held by rebuild_baseline.json at the recorded bytes
```

**147 of 790 byte-identical — unchanged from the 147/790 recorded on 2026-09-09.** One baseline entry
was re-recorded: `corpus/sentences/bank.json`, whose rebuilt bytes moved because it now carries the
sentence-level edge and the new token links. Its cause key is unchanged. Every other file rebuilt to
the bytes already recorded, which is what proves the new step did not disturb the chain.

## 7. What is left, and why

38 taught N5/N4 records are still under the floor. They fall into five kinds, and none of them is
reachable by a rule that stays honest about token boundaries:

1. **The bank holds no token of the word.** `でも`, `では`, `だから` (conjunctions): every occurrence
   in the bank is the particle sequence で+も / で+は / だ+から. `下さい/ください` is always the
   inflected くださる. `就いて/ついて` is always つく+て. Real content work, not linking.
2. **Homograph siblings that read alike.** `此処/ここ`, `様/さま`, `白/しろ`, `匹/ひき`, `製/せい`,
   `献花/けんか` — a second registry record shares surface and reading and nothing here can choose.
   Some are at 2/3 and need one more sentence, not a rule.
3. **Counters whose span is fully consumed.** `１０日/とおか`, `８日/ようか`, `１日/ついたち`,
   `４日/よっか`, `９日/ここのか`, `２０日/はつか` — the tokens are １０ + 日, both already linked to
   十 and 日. Linking the compound would mean re-pointing, which is a migration, not a relink.
4. **Single-mora readings inside longer words.** `区/く`, `家/け`, `員/いん`, `中/ちゅう`, `零/れい`,
   `門/もん`, `裏/うら`, `米/こめ` — the substring measure counted these in the hundreds and every one
   of them is a piece of another word.
5. **Words the bank genuinely lacks.** `この間`, `この頃`, `ご覧になる`, `御座います`, `開く/ひらく`,
   `居る/おる`, `一月/ひとつき`. These need sentences.

Kinds 1 and 5 (about 20 records) are supply work for a W13-shaped mining pass; kind 2 is a handful of
sentences; kind 3 needs a decision about compound-span links that this unit deliberately did not take.

## 8. Deferred: the same rules at N3

Measured, not applied: the identical derivation scoped to N3 finds **1,694 links over 334 records**
and would lift **101** of them over the floor. It is left to W13, whose plan row already says it
re-runs this relink, for one reason: at N3 the pass links every で token to `vocab:2028980` (779 of
them — the particle record the course files at N3), and that pushes **33 more lesson↔sentence pairs
over the i+1 budget** and 74 more into "carries new vocab". That is a real curriculum finding — N5
lessons showing a word the course only teaches at N3 — and it belongs to the campaign that fixes N3,
not to a mechanical relink that would have had to loosen the frozen baseline by a third to land it.

## 9. Precision, measured rather than assumed

Two records carry links a human should overrule, found by reading every occurrence of the two riskiest:

- `其れに/それに` — 16 of 19 correct; 3 are 「それについて…」, where それ+に is followed by ついて and the
  conjunction reading is wrong. The record clears the floor on the other 16.
- `其れで/それで` — 12 links after the longest-match fix took 「それでは」 to its own record
  (`vocab:1406050`, which the fix lifted from 0 to 6) and 「それでも」 out of scope.

`然うして/そうして` keeps one link (the kanji-spelled occurrence, which is right) and `知らせる` one.
Neither reaches the floor, so neither depends on the judgement.

## Files

| file | change |
|---|---|
| `scripts/apply_orthographic_relinks.py` | new — derive + apply, the rules and every guard documented |
| `research/derived/repairs/orthographic_relinks.json` | new — 663 tracked rows |
| `scripts/export/export_corpus.py` | publishes `sentence.vocab[]` with provenance |
| `scripts/validate/validate_repairs_applied.py` | `handle_orthographic_relinks` + REGISTRY entry |
| `research/derived/rebuild_manifest.json` | step 114 inserted; families renumbered 115–117 |
| `scripts/validate/sentence_coverage_baseline.json` | W05 ratchet lowered (§5) |
| `research/reports/lesson_sentence_baseline.json` | check D re-frozen (§4) |
| `scripts/validate/rebuild_baseline.json` | `bank.json` bytes re-recorded (§6) |
| `corpus/`, `course/`, `contracts/`, `prototype/app/data/` | regenerated |

## Appendix — 20 sample links for a human read

| sentence | linked surface | record | rule |
|---|---|---|---|
| りんごやみかんなどを買いました | **など** (など) | `vocab:1582300` 等 / など | kana-exact |
| ７日に友だちと会う | **７日** (なのか) | `vocab:1579630` ７日 / なのか | run-reading |
| ゆきちゃんはとても元気です | **ちゃん** (ちゃん) | `vocab:1007660` ちゃん / ちゃん | kana-exact |
| そうなさるのもごもっともです。 | **ご** (ご) | `vocab:1270190` 御 / ご | kana-exact |
| 千円くらいかかりました | **くらい** (くらい) | `vocab:1154340` 位 / くらい | kana-exact |
| なれすぎはあなどりを生む。 | **すぎ** (すぎ) | `vocab:1195960` 過ぎ / すぎ | kana-exact |
| 今日は１月５日だ | **５日** (いつか) | `vocab:1268570` ５日 / いつか | run-reading |
| 彼らはもう家に帰った | **彼ら** (かれら) | `vocab:1483090` 彼ら / かれら | run-reading |
| 雨が降った、それで試合は中止になった | **それで** (それで) | `vocab:1007000` 其れで / それで | run-reading |
| この映画はそれほど面白くなかった | **それほど** (それほど) | `vocab:1007060` それ程 / それほど | run-reading |
| 部屋の中に一人づつ入ってください。 | **づつ** (づつ) | `vocab:2006560` 宛 / ずつ | kana-function-word |
| そんなに急かすなよ。 | **そんなに** (そんなに) | `vocab:2008740` そんなに / そんなに | run-reading |
| 学生達は校長に呼ばれてあつまった。 | **達** (たち) | `vocab:1416220` 達 / たち | kana-exact |
| 彼はいつも文句ばかり言う | **ばかり** (ばかり) | `vocab:1010240` 許り / ばかり | kana-exact |
| この映画はそれ程面白くなかったです | **それ程** (それほど) | `vocab:1007060` それ程 / それほど | run-reading |
| これは旅行のお土産です | **お土産** (おみやげ) | `vocab:1002500` お土産 / おみやげ | run-reading |
| 彼がホテルを朝、４時過ぎに出発する | **過ぎ** (すぎ) | `vocab:1195960` 過ぎ / すぎ | kana-exact |
| 私はすぐに帰ってくる。 | **すぐに** (すぐに) | `vocab:1430620` 直ぐに / すぐに | run-reading |
| 毎日少しずつ勉強する | **ずつ** (ずつ) | `vocab:2006560` 宛 / ずつ | kana-function-word |
| その先生は大学を出たばかりだ。 | **ばかり** (ばかり) | `vocab:1010240` 許り / ばかり | kana-exact |

## Appendix — every record the relink touched (63)

| record | headword / kana | level | sentences before → after |
|---|---|---|---|
| `vocab:1154340` | 位 / くらい | n5 | 0 → 56 |
| `vocab:1007340` | 丈 / だけ | n5 | 0 → 43 |
| `vocab:1483090` | 彼ら / かれら | n4 | 0 → 34 |
| `vocab:1010240` | 許り / ばかり | n4 | 0 → 30 |
| `vocab:1002430` | お茶 / おちゃ | n5 | 0 → 29 |
| `vocab:1430620` | 直ぐに / すぐに | n5 | 0 → 27 |
| `vocab:1436510` | 程 / ほど | n4 | 0 → 21 |
| `vocab:1461160` | 二つ / ふたつ | n5 | 0 → 21 |
| `vocab:1007040` | 其れに / それに | n4 | 0 → 19 |
| `vocab:1270190` | 御 / ご | n4 | 0 → 18 |
| `vocab:1156990` | 易い / やすい | n4 | 0 → 17 |
| `vocab:1160820` | 一つ / ひとつ | n5 | 0 → 17 |
| `vocab:2008740` | そんなに / そんなに | n4 | 0 → 17 |
| `vocab:1416220` | 達 / たち | n5 | 0 → 15 |
| `vocab:1582300` | 等 / など | n5 | 0 → 15 |
| `vocab:1294940` | 歳 / さい | n5 | 1 → 13 |
| `vocab:1007000` | 其れで / それで | n4 | 0 → 12 |
| `vocab:1299740` | 三つ / みっつ | n5 | 0 → 10 |
| `vocab:2006560` | 宛 / ずつ | n5 | 0 → 10 |
| `vocab:1298520` | 冊 / さつ | n5 | 1 → 10 |
| `vocab:1001710` | お菓子 / おかし | n5 | 0 → 9 |
| `vocab:1006280` | すると / すると | n4 | 0 → 9 |
| `vocab:1006980` | 其れから / それから | n5 | 0 → 9 |
| `vocab:1195960` | 過ぎ / すぎ | n5 | 0 → 9 |
| `vocab:1009000` | どうも / どうも | n5 | 0 → 8 |
| `vocab:1243600` | 九つ / ここのつ | n5 | 0 → 8 |
| `vocab:1268070` | 五つ / いつつ | n5 | 0 → 8 |
| `vocab:1524990` | 又は / または | n4 | 0 → 8 |
| `vocab:2220600` | お風呂 / おふろ | n5 | 0 → 8 |
| `vocab:1002320` | お祖父さん / おじいさん | n5 | 0 → 7 |
| `vocab:1002330` | お祖母さん / おばあさん | n5 | 0 → 7 |
| `vocab:1002500` | お土産 / おみやげ | n4 | 0 → 7 |
| `vocab:1007660` | ちゃん / ちゃん | n4 | 0 → 7 |
| `vocab:1270390` | ご主人 / ごしゅじん | n4 | 0 → 7 |
| `vocab:1416840` | 誰か / だれか | n5 | 0 → 7 |
| `vocab:1513065` | お弁当 / おべんとう | n5 | 0 → 7 |
| `vocab:1006140` | すっと / すっと | n4 | 0 → 6 |
| `vocab:1007060` | それ程 / それほど | n4 | 0 → 6 |
| `vocab:1258830` | 県下 / けんか | n4 | 1 → 7 |
| `vocab:1264740` | 個 / こ | n5 | 0 → 6 |
| `vocab:1268570` | ５日 / いつか | n5 | 0 → 6 |
| `vocab:1406050` | 其れでは / それでは | n5 | 0 → 6 |
| `vocab:1484930` | 非常に / ひじょうに | n4 | 0 → 6 |
| `vocab:2429350` | お金持ち / おかねもち | n4 | 0 → 6 |
| `vocab:1004790` | 此れから / これから | n4 | 0 → 5 |
| `vocab:1537980` | 役に立つ / やくにたつ | n4 | 0 → 5 |
| `vocab:1307040` | 四つ / よっつ | n5 | 0 → 4 |
| `vocab:1462900` | ２日 / ふつか | n5 | 0 → 4 |
| `vocab:1579630` | ７日 / なのか | n5 | 0 → 4 |
| `vocab:1583630` | 付き / つき | n4 | 0 → 4 |
| `vocab:1631750` | がる / がる | n5 | 0 → 4 |
| `vocab:1008190` | 詰らない / つまらない | n5 | 0 → 3 |
| `vocab:1202170` | 皆さん / みなさん | n5 | 0 → 3 |
| `vocab:1319220` | 七つ / ななつ | n5 | 0 → 3 |
| `vocab:1524610` | 枚 / まい | n5 | 0 → 3 |
| `vocab:1561470` | ６日 / むいか | n5 | 0 → 3 |
| `vocab:1585315` | 六つ / むっつ | n5 | 0 → 3 |
| `vocab:1301330` | ３日 / みっか | n5 | 0 → 2 |
| `vocab:1380580` | 製 / せい | n4 | 0 → 2 |
| `vocab:1545790` | 様 / さま | n4 | 0 → 2 |
| `vocab:1583370` | 匹 / ひき | n5 | 0 → 2 |
| `vocab:1420410` | 知らせる / しらせる | n4 | 0 → 1 |
| `vocab:1612860` | 然うして / そうして | n5 | 0 → 1 |
