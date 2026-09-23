# Exam builder fixes 3: context_fill gets the context-sufficiency rules

Status: **pending, nothing applied.** Patch `research/derived/patches/exam_builder_fixes_3.patch`
applies on top of `exam_equivalence_filter.patch` (patch 1) and `exam_builder_fixes_2.patch` (patch 2)
and touches one file, `scripts/export/build_exam_banks.py`. Measured 2026-09-23 in a scratch tree
(`git archive HEAD` + patches 1 and 2) over an sqlite backup of `db/corpus.sqlite`.

Applying: `git apply` patch 1, patch 2, then patch 3. Rebuild the banks in W18 order (authored,
listening, reading_comp, `build_exam_banks.py` last) and re-run the bank gates. I checked the apply
chain on a fresh `git archive HEAD scripts design`. All three patches apply cleanly and the result is
byte-identical to the measured builder. It compiles, `exam_rules.py`'s self-check passes, and the
chain's builder reproduces all 18 measured banks byte for byte.

## What the patch does

Patch 2 gave `grammar_form` / `text_grammar` a context-sufficiency rule. This patch applies the same rule
to `context_fill` (fix 20 in the builder's header), reusing patch 2's `content_tokens`,
`MIN_STEM_CONTENT`, `stem_key` and bank-sentence set.

| Fix | Rule |
|---|---|
| 20a | A `cf` stem needs `MIN_STEM_CONTENT = 2` content tokens outside the blank. This is patch 2's function and constant, unchanged. If the stem falls short, the builder records drop `stem-too-short` and the sentence tries its next word, as `gf` tries its next point. |
| 20b | A distractor is refused when the filled stem is a sentence in the bank **or `raw_tatoeba_sentence`** (`stem_key` equality). |
| 20c | The same-slot test for words (`word_frames`). A distractor is refused when the bank or Tatoeba shows it between the same neighbours as the blank. The neighbours are the content word before it (with the particles between) and the content word after it (with the particles between), compared by SudachiPy normalized form. The rule only applies when **every** side that has a content word is attested. Single-token distractors only. |
| 20d | The semantic-class test (`open_group`). The Sudachi subclasses that name a semantic group, not just a syntax: **adverbial** (副詞可能 nouns for time, quantity and place; numerals including number + counter; adverbs), **adjectival** (形容詞, 形状詞, 連体詞), **pronoun**, and **counter-noun** (助数詞可能). The group is read for the distractor *in the filled stem*: 千 alone is tagged as a name, while in 千人 it is a numeral. A distractor in the key's group is refused. |
| 20e | `x not in pre + post` (check C), as in patch 2's `admissible`. |

Rejected distractors are replaced from the existing candidate order, the same order and hash tiebreak
as before. If fewer than 3 remain, the item drops with `no-admissible-distractor`. That never happened.

Common nouns (名詞-普通名詞-一般) and verbs have no Sudachi semantic subclass, so 20d leaves them
alone. For those, 20c is the only test.

## Measuring

**N (`MIN_STEM_CONTENT`).** The paper draws 6 / 8 / 11 `context_fill` items (N5 / N4 / N3), so the 3x
floor is 18 / 24 / 33. n4 and n3 fill their 400 cap at every N from the next sentences. n5 has no spare
sentences.

| N | n5 cf | n4 cf | n3 cf |
|---|---|---|---|
| 0 | 155 | 400 | 400 |
| 1 | 150 | 400 | 400 |
| **2** | **112 (18.7x)** | **400 (50.0x)** | **400 (36.4x)** |
| 3 | 56 | 400 | 400 |

N=2 is patch 2's value and it clears every floor, so I did not tune it for `cf`.

**Same-slot tests.** Each variant ran on top of N=2. The "changed" column counts items whose
distractors moved, against HEAD + patches 1 and 2.

| variant | items changed n5 / n4 / n3 | what reading the changes showed |
|---|---|---|
| 20b alone (bank + Tatoeba sentence) | 0 / 0 / 0 | One hit in 955 items, cf:n4:25:389 「（　）です！」 offering 大学生 (大学生です！ is in Tatoeba). The stem has 0 content tokens, so 20a drops the item anyway. Kept because it is one set lookup. |
| 20d with raw Sudachi subclasses | 14 / 31 / 15 | About 4 in 10 refusals remove a real second key. Misses 毎年 against 五つ, 半分 against 九つ, 小さな against 新しい, and ９日 against 今朝. |
| **20d with the four groups (applied)** | 26 / 46 / 30 | Adds the misses above plus 大切 against 遠い (かなり（　）). The rest are harmless refusals. |
| 20c, any attested side (OR); items flagged, not applied | 31 / 99 / 68 | Rejected. About 1 in 4 is a real fit. The rest are local co-occurrences that the whole stem rules out: 「いすが（　）ある」 with 白い is flagged because いすが白い is attested. |
| **20c, every side attested (AND, applied)** | +10 / +34 / +15 | I read 46 of the 59 changed items. About 21 were real second keys and 5 more marginal. The rest are harmless. |
| 20d over every POS (any same subclass) | 62 / 181 / 170 | Rejected. Every noun key gets verb or adjective distractors, and the item becomes a form test. |

## Scratch run

- **Parity.** On this snapshot, HEAD + patches 1 and 2 reproduce HEAD's three `context_fill` banks
  item for item, apart from patch 1's single n4 item. The snapshot has drifted since patch 2 measured
  its own snapshot: n4_text_grammar is 75 here, not 74, and a few `gf` counts differ. That comes from
  the writer chain and does not touch `cf`.
- **Per bank.** The other 15 deterministic banks are byte-identical with and without patch 3.

| bank | HEAD → patch 3 | changed | dropped | added | unchanged | patch 2 → 3, by cause |
|---|---|---|---|---|---|---|
| n5_context_fill | 155 → 112 | 36 | 43 | 0 | 76 | 36 with distractors replaced, 43 dropped as too short |
| n4_context_fill | 400 → 400 | 73 | 55 | 55 | 272 | 72 replaced (+1 from patch 1), 55 dropped as too short, 55 backfilled to the cap |
| n3_context_fill | 400 → 400 | 43 | 19 | 19 | 338 | 43 replaced, 19 dropped as too short, 19 backfilled |

- **Every change is explained (0 unexplained).** The eval script (`scratchpad/cfpatch/eval.py`, not
  committed) re-derives each difference from the rules:
  - All 117 dropped items have a stem under 2 content tokens.
  - Every changed item differs only in `distractors`. The 184 removed distractors break down as 114
    open-group only (77 adverbial, 29 adjectival, 8 counter-noun), 61 frame only, 9 both, and 0 by
    whole sentence.
  - The 74 added items are backfill into capped banks, one per drop.
- **Whole-bank checks on the output:** 0 `cf` stems under N, 0 distractors that 20b to 20e would
  refuse, 0 distractors printed in the stem.
- **Gates** (scratch tree = HEAD `corpus/` and `course/` + the new banks):
  - `validate_exam_level_gate.py`: ALL OK. All 18 deterministic family-levels have 0 inappropriate
    items at ceiling 0. `cf` is at 18.7x / 50.0x / 36.4x.
  - `validate_exam_banks.py`: ALL OK, advisory `okurigana_giveaway` 58 = baseline.
  - `validate_exam_stem_collisions.py`: 0.
- **Concentration.** n5 has 146 distinct distractors over 112 items (was 161 over 155); the top one
  is still 右 ×9. n4 is 445 → 436 with 森 ×11 at the top both times. n3 is 812 → 812 with 母 going
  from ×5 to ×6.
- **Build time** 13 s → 22 s, because Tatoeba (248,705 sentences) is tokenized once for the frame
  index.

## The 123 short stems

- The builder's own counter (`content_tokens` with patch 2's `FUNCTION_POS`) finds **117** at HEAD:
  n5 43, n4 55, n3 19. The brief's 123 (47 / 56 / 20) is reproduced only if 接頭辞, 連体詞 and 接続詞
  also count as function words. Six items have one of those as their second content token.
- **All 117 are resolved.** All are dropped as `stem-too-short`. None was re-keyed, because no other
  word in those sentences yields an admissible item. n4 and n3 backfill to 400. n5 has no spare
  sentences, so it goes 155 → 112.
- **The other six are unchanged.** I read them:
  - Three have no second key: お（　）だけでけっこうです (水), あの（　）から出ましょう (出口),
    また話し（　）だ (中).
  - One is marginal: どの（　）が安いですか (店) offers 駅.
  - Two have a fit. そのうち（　）よ (分かる) offers 出来る and 食べる, and verbs have no group.
    あの人形（　）。 (怖い) offers 作家, and あの人形作家 is a phrase.

  Counting those three POS as function words would drop the six, but it would also change fix 19 for
  `gf`. That is left for decision.

## Twelve items, before (HEAD + patches 1 and 2) and after

| id | stem = key | before | after | why |
|---|---|---|---|---|
| cf:n5:2348:548 | （　）だけ来た = 一人 | ５日 / 毎年 / 先月 | dropped | 1 content token; 先月だけ来た is as right (the brief's case) |
| cf:n5:21:97 | （　）ね。 = 大きい | 何時も / 新しい / 小さな | dropped | 0 content tokens |
| cf:n4:25:389 | （　）です！ = 小さい | 別れる / 楽しむ / 大学生 | dropped | 0 content tokens; also the only whole-sentence hit (大学生です！ is in Tatoeba) |
| cf:n5:2805:249 | りんごが（　）ある = 九つ | 六つ / 白い / 四つ | 白い / 来る / 新聞 | 六つ and 四つ are in the key's adverbial group (numeral + counter) |
| cf:n5:2614:61 | りんごを（　）買った = 五つ | お金 / 毎年 / 九つ | お金 / 学校 / 下手 | 九つ and 毎年 are both adverbial; りんごを毎年買った is a sentence |
| cf:n5:74:343 | （　）人くらいの人がいた。 = 千 | 五 / 本 / 木 | 本 / 木 / 年 | 五 is a numeral read in place |
| cf:n5:3151:21 | （　）ボールペンを買いました = 新しい | 小さな / 見せる / 出来る | 見せる / 出来る / １０日 | 連体詞 小さな is in the adjectival group |
| cf:n4:3356:852 | 雨天の（　）は運動会を中止する。 = 場合 | 有名 / 午前 / 話す | 有名 / 話す / 知る | 午前 and 場合 are both 副詞可能 nouns; 雨天の午前は… is a sentence |
| cf:n5:4277:317 | いい（　）だけどイマイチね。 = 人 | 万 / 目 / 男 | 万 / 南 / 口 | frame: いい男 and いい目 are attested (the only side with a content word) |
| cf:n4:644:991 | その（　）は２つのパートに分かれていた。 = 試験 | 試合 / 寒い / 通る | 寒い / 通る / 色々 | frame: その試合 and 試合は２ are both attested |
| cf:n4:3505:429 | （　）すればよかったのに。 = 電話 | 通う / 場合 / 出発 | 通う / 場合 / 八つ | frame: 出発する is attested (nothing precedes the blank) |
| cf:n3:8:1571 | 彼は（　）しています。 = 外出 | 然う / 毎年 / 有名 | 毎年 / 有名 / 会場 | frame: 彼はそう and そうする are both attested; 彼はそうしています is a fit |

## Residue: what the teacher loop still sees

1. **Common nouns and verbs in an open slot.** Neither has a semantic subclass, so only the frame test
   covers them, and only partly. I read all 112 n5 items after the patch: **11 still have a clear second
   key** (25 of the same 112 before). A sample of 50 n4 and 50 n3 items, chosen by sha1 order of ids
   present in both runs, went from 11 to 4 (n4) and from 4 to 3 (n3). Examples:
   - 「あした （　）を かう」 本, with 木 and 花. The spaces of the spaced N5 stem cut the frame, and
     SudachiPy reads the kana かう as こう, not 買う. Skipping the spaces was tried and changed no item.
   - 「めったに来ない（　）だ」 人, with 車 and 母
   - 「何で（　）に行かないといけないの？」 学校, with 後ろ
   - 「テーブルの（　）にコップが四つあります」 上, with 下 and 右. Sudachi puts 上 in 副詞可能 but
     下 and 右 in 一般, so place nouns fall into two classes.
   - 「（　）人もの人がそこにいた」 千, with 何. The pronoun and numeral groups differ.
   - 「そのうち（　）よ」 分かる, with 出来る and 食べる

   Upgrade path: a semantic class for common nouns. The DB has none: `vocab_sense.field_tags` is empty,
   and the families group words by kanji or by topic, not by meaning.
2. **Replacements can draw a new fit.** A refused distractor is replaced from the same ordered pool, and
   the pool can supply another fit, at the same rate as the baseline draws:
   - 「（　）は毎日うちにいます」 母: 今 → 男
   - 「デパートで（　）のカレンダー」 来年: 今月 → 大学
   - 「来月には子どもが（　）んだよ」 生まれる: お母さん → 見つける
   - 「なるべく早く（　）よ」 帰る: 出る → 飲む
3. **Coarse groups over-refuse.** For example, 「（　）からドライブに行きませんか」 (今) lost 日 and 中,
   which never fit. This costs pool, never correctness, and no item was dropped for lack of distractors.
   Tokenization can also merge a distractor with its neighbour: in ざっと（　）人ぐらい, 万 becomes the
   single token 万人. A merged distractor escapes both 20c and 20d.
4. **More items are solvable by form.** A key in an open group now draws distractors from other groups:
   「りんごを（　）買った」 (五つ) now offers お金 / 学校 / 下手. This is patch 2's limit 2 again:
   mechanically, only "does not fit" can be certified.
5. **The snapshot was taken while a writer chain was changing the DB.** After applying, rebuild on the
   live DB and re-run the three gates. Re-measure N only if n5_context_fill falls below 18.
