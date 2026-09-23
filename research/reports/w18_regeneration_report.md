# W18 — all 40 exam banks regenerated (chain unit C2-W18, checkpoint)

Written 2026-09-23. The W17 builder patch is applied, every bank is rebuilt from the index and the
authoring journal, and the nine non-listening families are level-clean: every item's Japanese is
inside the taught set at the end of its level (ceiling 0, check S now a hard failure for them). The
in-lesson reading boxes ask their comprehension question again: 285 of 286 (4 before).

## 1. What ran, in order

1. `git apply research/derived/patches/w17_builder.patch`: clean at HEAD. W16's token-boundary
   blanks survive untouched (`token_spans` / `boundary_occurrence` are still what cuts a
   `text_grammar` blank; `test_exam_builders.py` 9/9 and the new `test_exam_builders_w17.py` 28/28).
2. The three decisions below, before any builder ran.
3. `export_course.py` first (0 files changed; the builders read the exported `cumulative_known_set`).
4. `build_authored_banks.py`, `build_listening_bank.py`, `build_reading_comp_bank.py`, then
   `build_exam_banks.py` LAST, because its INDEX is a glob over every bank file.
5. `apply_reading_comprehension.py` (new, manifest step 132) flips the reading boxes.
6. `build_speaking_checkpoints.py` re-selects the speaking-unit checkpoints (221 of 366 pointed at ids
   the regeneration retired), then the exporters, contracts, review views and `sync-data`.

## 2. The three decisions (W17 §6, APP_PLAN W18 row)

**(1) Three in-place repairs journaled, not reverted.** The authoring journal under
`research/derived/reauthor/exam_authored/` was git-ignored (the whole `reauthor/` tree is scratch), so
"one source of truth" was a local file. It is tracked now (`.gitignore` un-ignores `exam_authored/`,
77 files, 1.1 MB), and the three committed repairs were back-ported into it before regenerating:

| id | journal had | committed bank (kept) |
|---|---|---|
| `lp:n3:008` | 7時半 is the next showing, then a 7時 showing appears with free seats (contradiction) | 7時の回も満席で, then a cancellation frees a 7時 seat |
| `lr:n3:tatoeba-11510681` | key うん、見たいな。 (does not answer the prompt) | key さあ、本人に聞いてみたら？, distractor 見たことはあるよ。 |
| `lt:n5:004` | お兄さん for the student's own brother, speaking to a teacher | 兄 (in-group), script and the option 兄に電話する |

W17's table printed the third arrow backwards; the data and `readiness/exams_simulations.md` agree
that 兄 is the repair. All 239 listening items regenerate byte-for-byte equal in content.

**(2) Withdrawals are tracked tables, read by default.** `build_listening_bank.py` now reads
`_flagged_listen.json` unless `--flagged` overrides it (the same fix W17 made for paraphrase/usage),
and `lr:n5:tatoeba-213565` (そこを何とか。) is withdrawn there with its reason: a fixed plea whose
difficulty the word-level gate cannot see. The rebuild skips exactly that one item.

**(3) The ledger holds 129 ids, not 118.** Every entry in `corpus/exam_banks/removed_items.json` now
carries a `w18` field: **66 returned repaired** (62 answer leaks that now blank a single occurrence,
2 homophone-group survivors, 1 duplicate survivor, 1 re-cut text_grammar blank; 64 differ in stem or
key from the withdrawn copy, 2 return with the same content and pass every check) and **63 stay out**,
kept out by builder rules, not by the file. `design/exam_simulator.md` said 118 withdrawn and 6,048
items; it now says 129 and 5,141.

## 3. What else the regeneration needed (found on the way)

* **Contradictory stems.** The regenerated `context_fill` banks printed the same question with two
  keys (どのくらい（　） keyed 大きい and 高い; 32 items in 16 groups, three banks over their ratchet).
  `cf`/`gf` now keep one item per normalized printed stem, using the collision gate's own `normalize`;
  18 candidates skipped (13 cf, 5 gf). Collisions **94 → 0**, baseline re-frozen at 0.
* **Em dash in learner text.** The W17 explanation templates joined with an em dash
  (`学校（がっこう）— escola`); they now read `学校（がっこう）: escola`, `ふるい escreve-se 古い (velho)`,
  `ばかり: só/apenas...`. One authored rc explanation carried one and was fixed in the table. 0 of
  5,141 items carry an em dash.
* **Speaking checkpoints.** Re-selected from the new banks: 366 → 364 items (context_fill 142 → 142,
  kanji_reading 142 → 141, sentence_order 73 → 74, paraphrase 9 → 7), no other unit field changed.
  The builder now keeps `strand_counts` in step with what it writes (stale histograms 37 → 0 after
  the first run showed the drift). The strand ratchet was re-recorded with that cause: 18 (stage,
  strand) distances moved 0.1-0.7 points, the rest shrank.
* **One box loses its question.** `read:n4-oracoes-relativas-03-01` is one of W15's four held
  concatenations. W18b's verifier rejected its new question (scannable) and its old one fails P1 and
  P2/P3 under the W16 guards, so it has no item. Its pointer is withdrawn in the same table (the
  contract gate refuses a reference to a missing item). Open: re-author it or replace the passage.

## 4. Per-bank item counts, before → after

| bank | before | after | added | dropped | identical |
|---|---:|---:|---:|---:|---:|
| `n5_kanji_reading` | 398 | 176 | 70 | 292 | 0 |
| `n5_orthography` | 377 | 177 | 73 | 273 | 0 |
| `n5_context_fill` | 235 | 155 | 28 | 108 | 0 |
| `n5_grammar_form` | 129 | 114 | 0 | 15 | 0 |
| `n5_sentence_order` | 273 | 58 | 16 | 231 | 0 |
| `n5_text_grammar` | 37 | 34 | 0 | 3 | 0 |
| `n5_reading_comp` | 43 | 43 | 0 | 0 | 0 |
| `n5_paraphrase` | 52 | 9 | 7 | 50 | 2 |
| `n5_usage` | 52 | 8 | 7 | 51 | 1 |
| `n4_kanji_reading` | 398 | 400 | 262 | 260 | 0 |
| `n4_orthography` | 398 | 400 | 263 | 261 | 0 |
| `n4_context_fill` | 367 | 400 | 361 | 328 | 0 |
| `n4_grammar_form` | 299 | 300 | 56 | 55 | 0 |
| `n4_sentence_order` | 298 | 300 | 137 | 135 | 0 |
| `n4_text_grammar` | 72 | 74 | 3 | 1 | 0 |
| `n4_reading_comp` | 91 | 90 | 0 | 1 | 0 |
| `n4_paraphrase` | 59 | 15 | 14 | 58 | 1 |
| `n4_usage` | 59 | 14 | 14 | 59 | 0 |
| `n3_kanji_reading` | 400 | 400 | 225 | 225 | 0 |
| `n3_orthography` | 400 | 400 | 224 | 224 | 0 |
| `n3_context_fill` | 389 | 400 | 397 | 386 | 0 |
| `n3_grammar_form` | 300 | 300 | 21 | 21 | 0 |
| `n3_sentence_order` | 300 | 300 | 118 | 118 | 0 |
| `n3_text_grammar` | 122 | 122 | 0 | 0 | 0 |
| `n3_reading_comp` | 152 | 152 | 0 | 0 | 0 |
| `n3_paraphrase` | 71 | 28 | 0 | 43 | 28 |
| `n3_usage` | 71 | 33 | 0 | 38 | 33 |
| 13 listening banks | 239 | 239 | 0 | 0 | 239 |
| **total** | **6,081** | **5,141** | | | |

"Identical" is on every field; the deterministic items all gain `explanation` (and `accepted` on
`sentence_order`), so none is byte-identical. reading_comp keeps its ids (one per passage) but every
question is the new W18b one. The N5 drops are the level rule doing its job: 292 of the 398 N5
kanji_reading items failed it (the old ceiling), and the level-clean N5 pool holds 176 headwords.

Builder drop counters (`build_exam_banks.py --stats`): context_fill sentence grammar above level 102,
vocab 75, reading disagrees 45, kanji 33, leak guard 20, duplicate stem 13; grammar_form no
single-occurrence form 164, grammar above level 106, vocab 64, kanji 16, duplicate stem 5;
sentence_order chunk count outside 4-6 783, grammar 106, vocab 91, same-particle ambiguous 65,
kanji 33; text_grammar no token-aligned single form 55; homograph / homophone groups 45 / 85.

**paraphrase / usage.** The 42 W18b rows (`pp_us_w18b.json`, moved out of `pending/`) replace their
ids or join the bank with their pt-BR explanation, then the level rule withholds every item whose
Japanese is untaught (299 withheld across the three levels; they stay in the journal). This is the
replacement W18b sized: N5 pp 9 (3.0x a paper), N4 pp 15 (3.8x), N4 us 14 (3.5x), N3 pp 28 / us 33.

**reading_comp.** The 285 W18b questions (`rc_questions_w18b.json`, moved out of `pending/`) are the
only source. All 285 pass the rc builder's guards against each passage's OWN lesson known set (the
stricter of the two, because the same question is shown in that lesson's box): P1 about the passage,
P2/P3 readable, P4 not scannable. The pre-W15 `authored_rc_*.json` stay as history, unread.

## 5. Level gate per family (inappropriate items / ceiling)

| family | N5 | N4 | N3 |
|---|---|---|---|
| kanji_reading | 0 (was 292) | 0 (261) | 0 (182) |
| orthography | 0 (376) | 0 (393) | 0 (360) |
| context_fill | 0 (230) | 0 (357) | 0 (332) |
| grammar_form | 0 (40) | 0 (70) | 0 (32) |
| sentence_order | 0 (104) | 0 (18) | 0 (11) |
| text_grammar | 0 (6) | 0 (8) | 0 (1) |
| reading_comp | 0 (21) | 0 (25) | 0 (18) |
| paraphrase | 0 (50) | 0 (59) | 0 (43) |
| usage | 0 (51) | 0 (60) | 0 (38) |
| listening_task | 21 (21) | 24 (24) | 17 (17) |
| listening_point | 17 (17) | 21 (21) | 16 (16) |
| listening_gist | n/a | n/a | 9 (9) |
| listening_say | 10 (10) | 13 (13) | 8 (8) |
| listening_reply | **7 (9)** | 10 (10) | **2 (3)** |

27 ceilings go to 0 and two listening ceilings shrink. Every section draws a level-clean paper at 3x
or better (lowest: N5 paraphrase 9 vs 3 per paper). The 175 listening items still over the line are
W18b's listening re-authoring (173 on an untaught kanji). Advisories lowered in the same commit:
okurigana_giveaway 373 → 58, orthography_longshot 241 → 1, orthography_shape_solvable 304 → 3,
reading_comp_string_match 32 → 0, sentence_order_ambiguous 1 → 0.

## 6. The reading boxes

`reading.comprehension.about_current_text` goes back to true on the 282 boxes W15 replaced (their
W18b question is in the bank), in the DB and through a tracked table,
`research/derived/repairs/reading_comprehension.json` (283 rows: 282 flips + 1 pointer withdrawn),
applied by `scripts/apply_reading_comprehension.py` (manifest step 132; families 133-135). Exact
match on the live index; in a replay a box the thinner step-41 selection did not build is skipped,
as `apply_reading_passages.py` already does. Replay handler `handle_reading_comprehension` in
`validate_repairs_applied.py`: 283/283. Plant proof on a copied tree: control 282 PASS / 0 FAIL;
flag set back to false, item re-pointed, question missing: each caught (3/3).

Boxes that ask a question: **4 → 285** of 286.

## 7. Lessons do not degrade

Rendered diff of `course/` against HEAD: **0 lesson files changed** (every `course/n*/` and
`course/pre-n5/` `.json` and `.md` is byte-identical). The only course files that change are the 72
speaking units and `course/speak/course.json`, on `checkpoint` and `strand_counts` only (section 3).

## 8. Gate and replay

Exporters → contracts (`infer_shapes` → `build_schemas` → `build_manifest`) → review views →
`sync-data` → `validate_all.py`: **ALL HARD VALIDATORS PASS** (quick replay included;
`validate_repairs_applied` 21,386 rows clean + 21 checked skips, the new table 283/283; contracts
pass with 0 unresolved references). `test_exam_builders_w17.py` joins the suite (28 checks). The
first gate run failed three validators, each fixed at its cause rather than silenced: review views
rendered before the contracts manifest (re-rendered in order), the dangling rc pointer (withdrawn,
section 3), and stale speak histograms (builder fix, section 3). Full replay: section 9.

## 9. Full replay (checkpoint)

The first full replay failed at the new step, and that is the finding it exists for: a from-scratch
rebuild builds a thinner set of reading boxes at step 41, so 172 of the 282 rows had no box to
match. The applier now does what `apply_reading_passages.py` does: exact match on the live index,
skip-and-report off it. The replay then showed **419 held files whose rebuilt bytes had moved, 0 new
and 0 healed**:

| files | cause |
|---:|---|
| 418 | `course/n5` 106, `course/n4` 182, `course/n3` 130 lesson `.json`/`.md`: C1-W20v's step 131 (2,283 practice exercises into 263 lessons, `d875570f`), which committed with the quick replay only. W18 writes no lesson data (a fresh `export_course.py` after the flip changes 0 lesson files). |
| 1 | `corpus/readings/n3.json` (readings-accumulated): this unit's step 132 plus the new rc questions `export_readings.py` resolves. `n4.json` and `n5.json` rebuild **byte-exact** with the same step, which is the positive proof that the flip replays. |

`--record` re-pinned the 419 hashes and each entry's cause now carries the line above. The re-run
is green: **790 exported files, 571 held at the recorded bytes, 0 wrong** (manifest 135 steps / 99
enabled).

## 10. Twenty regenerated items

| # | bank | id | stem / tiles | options (key first) | key | explanation (pt-BR) |
|---|---|---|---|---|---|---|
| 1 | n5_kanji_reading | `kr:n5:317` | 人 | ひと · みぎ · いま · はん | **ひと** | 人（ひと）: pessoa |
| 2 | n4_kanji_reading | `kr:n4:214` | 口 | くち · かお · ひく · あく | **くち** | 口（くち）: boca |
| 3 | n5_orthography | `or:n5:570` | ふるい | 古い · 多分 · ５日 · 来月 | **古い** | ふるい escreve-se 古い (velho) |
| 4 | n3_orthography | `or:n3:1664` | かんせい | 完成 · 中古 · 都市 · 特急 | **完成** | かんせい escreve-se 完成 (conclusão) |
| 5 | n5_context_fill | `cf:n5:4278:523` | ちょっと（　）があるんだけど。 | 話 · 空 · 下 · 花 | **話** | 話（はなし）: conversa |
| 6 | n4_context_fill | `cf:n4:3494:1302` | 明日、（　）でもどう？ | 食事 · 野菜 · 買う · 屋上 | **食事** | 食事（しょくじ）: refeição |
| 7 | n3_context_fill | `cf:n3:726:136` | かわいい花のワッペンをつけた（　）を見た。 | 女の子 · 見送り · 代わり · 求める | **女の子** | 女の子（おんなのこ）: menina |
| 8 | n5_grammar_form | `gf:n5:48` | りんご（　）? | がほしい · たくさん · ませんか · なくちゃ | **がほしい** | がほしい: querer (uma coisa) |
| 9 | n4_grammar_form | `gf:n4:3363` | 私は今着いた（　）だ。 | ばかり · さっき · ごとに · ちゃう | **ばかり** | ばかり: só/apenas (excesso) / acabou de |
| 10 | n5_sentence_order | `so:n5:5013` | 母は / 毎日 / うちに / います | (accepted: 2) | **母は毎日うちにいます** | Minha mãe fica em casa todos os dias. |
| 11 | n3_sentence_order | `so:n3:723` | ピーマンは / 半分に / 切り / ヘタを / 取って / おく | (accepted: 6) | **ピーマンは半分に切りヘタを取っておく** | Corte os pimentões ao meio e tire o cabinho (deixando pronto). |
| 12 | n4_text_grammar | `tg:n4:n4-passiva-02-01` | …大切だと言われた。わたしも、しょうらいこの気持ちをわすれない（　）したい。… | ように · なさい · ような · られる | **ように** | ように: para que / de modo que; tomara que |
| 13 | n5_reading_comp | `rc:n5:n5-te-form-04-01` | 学生は、どの人ですか。 | そこにすわっている人 · 今、話している人 · 外へ出た人 · 名前を書いた人 | **そこにすわっている人** | A terceira frase identifica como estudante quem está sentado ali; quem fala é o professor, quem saiu já foi embora e quem escreveu o nome são cinco pessoas, sem |
| 14 | n4_reading_comp | `rc:n4:n4-potencial-02-01` | 来年、この人はどんなことができるようになると思っていますか。 | 日本語でてがみを書くこと · 新聞を読むこと · 電話で話すこと · 世界の人と話すこと | **日本語でてがみを書くこと** | A última frase é a que fala do ano que vem: escrever uma carta em japonês. Ler jornal ele já consegue hoje, falar ao telefone continua fora do alcance, e conver |
| 15 | n3_reading_comp | `rc:n3:n3-estrutura-05-02` | 来月から、この町では何が変わりますか。 | バスの数が多くなる · 新聞が安くなる · 案内所がなくなる · 駅の前に新しい駅ができる | **バスの数が多くなる** | A última frase diz que, a partir do mês que vem, o número de ônibus também aumenta. O posto de informações está sendo construído e não fechando, e o texto não f |
| 16 | n5_paraphrase | `pp:n5:286` | 時間がありますか。 | ひま · お金 · 天気 · 電話 | **ひま** | Perguntar 時間がありますか é perguntar se a pessoa tem um tempo livre, e ひま é exatamente esse tempo livre. |
| 17 | n4_paraphrase | `pp:n4:788` | 出来るだけ手紙書くようにするよ。 | なるべく · ぜんぜん · たまに · やっと | **なるべく** |  |
| 18 | n4_usage | `us:n4:958` | (uso de 用意) | 旅行にいく用意をしなさい。 · 用意を着て出かけました。 · 山の上に古い用意が見えます。 · 毎朝、用意を飲んでから学校へ行きます。 | **旅行にいく用意をしなさい。** | Só a frase correta usa 用意 como preparativo; nas outras ele vira roupa, construção e bebida. |
| 19 | n3_text_grammar | `tg:n3:n3-perspectiva-05-02` | …つゆに入って、毎日雨がふっ（　）。私にとって、この雨の毎日は少しつらい。それでも今日は… | ている · べきだ · ように · たびに | **ている** | ている: estar fazendo / estar em certo estado (～ている) |
| 20 | n5_listening_task | `lt:n5:004` | M1: 先生、兄の辞書をなくしました。 F1: そうですか。辞書に名前を書きましたか。教室は見ましたか。 … 男の学生はこのあと何をしますか。 | 事務所へ行く · 兄に電話する · 辞書に名前を書く · 教室を見る | **事務所へ行く** | (roteiro; a correção 兄 ficou no diário de autoria) |

## 11. Open

* `read:n4-oracoes-relativas-03-01` has no comprehension question (section 3).
* Listening: 13 banks, 175 items over the level line; W18b's listening half.
* W17 §9 residue unchanged in kind: digit-keyed vocab (`５日`) still prints in some orthography
  options; short context_fill stems.
* Fable sample 30 on the regenerated banks (APP_PLAN §1 step 5) is for the planner; the 20 items
  above are the unit's own read.
