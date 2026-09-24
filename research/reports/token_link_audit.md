# Token to vocab link audit

> Derivation only. Nothing was applied: the DB, the exports and the bank are untouched. Rows are in
> [`research/derived/pending/token_link_audit.json`](../derived/pending/token_link_audit.json).
> Input: `corpus/sentences/bank.json` at HEAD `87310bda` plus a backup snapshot of `db/corpus.sqlite`
> (bank and snapshot token links are identical: 87,232 of 87,232 tokens agree).

## Why

The W20 generator hit a bank token whose link was plainly wrong: the なり of なりません pointed at
生る "dar fruto" instead of 成る. That is not one bad row. The dissector resolves a token through a
form table keyed on the written form alone (the same defect `scripts/fix_homophone_vocab_links.py`
documented), so wherever several records share a kana spelling it can land on the rare one. This
audit re-reads every linked token and lists every link the evidence contradicts.

## Result

**38,764 linked tokens audited, 4,004 flagged** (10.3%). Actions: relink 3,262, unlink 212, review 530.

| class | relink | unlink | review | total |
|---|---:|---:|---:|---:|
| `wrong_homograph` | 1,606 | 0 | 3 | 1,609 |
| `wrong_reading` | 999 | 30 | 520 | 1,549 |
| `wrong_pos` | 463 | 182 | 7 | 652 |
| `auxiliary_as_lexical` | 194 | 0 | 0 | 194 |
| **total** | 3,262 | 212 | 530 | 4,004 |

**The 2026-08-19 homophone repoint did not hold.** `scripts/fix_homophone_vocab_links.py` (commit 294fe90)
moved 刷る, 九, 彼/あれ, 背/せい, 様/さま and 最も links to the right sibling. At HEAD the wrong sides carry 刷る/する 932, 彼/あれ 748, 九/きゅう 362, 背/せい 9 tokens again, so a later rebuild or replay
re-dissected them through the same written-form lookup in `scripts/ingest/dissect.py`. A token repoint
that the next rebuild undoes is not a repair: the resolution belongs in the dissector (reading and
normalized form must enter the decision), with this table as its regression check.

What the classes mean:

- `wrong_homograph`: spelling and reading fit, but Sudachi's normalized form names a sibling record. なる
  normalizes to 成る, not 生る; する to 為る, not 刷る; くれる to 呉れる, not 暮れる; かかる to 掛かる, not 罹る;
  ほう to 方, not 報; わけ to 訳, not 理由.
- `wrong_reading`: the record's registered readings do not contain the word's reading in this sentence.
  中 read なか linked to 内/うち, 前 read まえ linked to 先/さき, 彼 read かれ linked to 彼/あれ.
- `wrong_pos`: the record cannot be this part of speech. この and ここ linked to 九 (a numeral), the いけ
  of いけない linked to 池 "lagoa", the adverb どう linked to 動 "movimento", よって linked to 夜.
- `auxiliary_as_lexical`: an auxiliary stem (Sudachi `助動詞語幹`: the よう of ような, the そう of
  高そう/だそう) linked to a content noun (用 "uso", 琴 "koto"). Relinked to the grammatical record
  (様/よう, 然う).
- `form_mismatch`: no registered form of the record matches the token or any run through it.

What the actions mean: `relink` has one record the evidence names, and it is mechanical. `unlink` means
the current record is wrong and no record in the registry is the word (どう "como" has no record: the
registry holds 動/銅/同/胴 read どう and 如何 read いかが, but not JMdict's どう), or the run the token belongs
to already carries the right compound on its neighbour (いけ+ない already links 行けない on ない, 一+つ
already links 一つ on つ), so this token's own link is the stray. `review` needs a human: the evidence
is reading-only, or several records remain.

### Not flagged (and why)

| bucket | tokens | meaning |
|---|---:|---|
| `confirmed` | 32,470 | Sudachi's normalized form or the text's kanji lemma names the linked record, reading consistent |
| `confirmed_reading_disputed` | 899 | confirmed, and one of the two reading witnesses disagrees with the record (Sudachi reads 私 as わたくし; the stored reading わたし agrees with the record) |
| `run_anchor` | 648 | the token anchors a multi-token record (W12 run: 一+つ, それ+に, いけ+ない) |
| `unconfirmed_consistent` | 459 | no identity signal either way, but form, reading and POS all fit and no other record qualifies |
| `kana_ambiguous` | 248 | kana text, the record's own primary reading, a common record, POS fits; Sudachi's kana normalized form carries no identity, so nothing contradicts (書く for かく, 橋 for はし) |
| `numeral` | 36 | a digit token linked to its numeral word (１０ to 十) |

## Method

Every bank sentence with a linked token is re-tokenized with SudachiPy 0.6.11 (full dictionary, mode C) and
aligned to the stored tokens by character span (38,764 of 38,764 linked tokens aligned). For each link:

1. **Form.** The Sudachi lemma, the Sudachi normalized form, or a lexicalised inflected surface (ください
   for 下さい) must be a registered form of the record, using the same inventory W12 used
   (`apply_orthographic_relinks.Registry`: headword, kana, `vocab_form`, raw JMdict elements). A
   contiguous run of 2 to 5 tokens that spells the record also passes (the W12 anchors).
2. **Reading.** The dictionary-form reading is rebuilt from the realized one (行っ/いっ + 行く gives いく) and
   must be a registered kana reading. There are two witnesses, Sudachi's reading and the stored token
   reading, and the link fails only when both miss. Sudachi's default reading of a bare kanji is a guess
   (私 as わたくし, 箱 as ばこ); the stored reading was corrected by earlier passes.
3. **Identity.** Sudachi's normalized form confirms the record that owns it (なり to 成る). A kana
   normalized form confirms only a usually-kana record, and the text's own kanji lemma confirms the
   record that owns that spelling (点いた confirms 点く even though Sudachi normalizes it to 付く).
4. **POS.** The `TOK2JM` veto W12 uses, plus Sudachi's own lexicon for kana tokens: if Sudachi files the
   record's headword at the record's reading only under other coarse POS, the kana token is a different
   word (動/どう is only a noun there; the token どう is an adverb).
5. **Target.** Candidates must pass the same form, reading and identity tests. Ties break on the stored
   reading, then a headword equal to the normalized form, then the printed-reading tier of
   `scripts/export/vocab_identity.py` (the one record whose kana is the reading in the text). Runs
   follow the W12 guards (no run starts on a particle or auxiliary, no all-function-word run, a kana run
   names a kanji record only when kana is its normal spelling).

Three demotions to `review` keep the mechanical rows honest:

- **Same spelling, reading-only evidence.** When the old and the proposed record share the spelling in the
  text (開く あく/ひらく, 何 なに/なん, 金 かね/きん), only the analyzer's reading separates them. On the rows
  read by eye it is right roughly 60% of the time: ドアが開く is あく, 何もしていません is なにも, 実をつける
  is み, 知らぬが仏 is ほとけ, 味噌が辛い is からい. These go to review, grouped by pair below, except the pairs
  `fix_homophone_vocab_links.py` already ruled (彼 あれ to かれ, 背 せい to せ, 様 さま to よう).
- **Reading miss with no alternative.** Both witnesses share the dissector's lineage, and many are the
  analyzer's error (縁 read えん, 町 read ちょう in 数日町を離れます, 体 read たい in 体中). Review, not unlink.
- **Space-separated kana sentences** (よる おそく ねる): Sudachi's segmentation is unreliable there.

## 30 samples

One row per distinct (class, action, old record, new record) pattern, most frequent first, round-robin over
classes. `n` is how many rows share the pattern.

| # | class | action | n | sentence | token | lemma / normalized / reading | linked | should be |
|---:|---|---|---:|---|---|---|---|---|
| 1 | `wrong_homograph` | relink | 932 | 先生のもとで勉強しました (`sent:gen-2fedb7d1cfa1`) | し@5 | する / 為る / する | 刷る/する (n5) | 為る/する (n4) |
| 2 | `wrong_reading` | relink | 748 | 彼は知っているに違いない (`sent:gen-3beb5841ff28`) | 彼@0 | 彼 / 彼 / かれ | 彼/あれ (n5) | 彼/かれ (n4) |
| 3 | `wrong_pos` | relink | 265 | この木は秋に実をつける (`sent:gen-241636dce7a0`) | この@0 | この / 此の / この | 九/きゅう (n5) | 此の/この (n5) |
| 4 | `auxiliary_as_lexical` | relink | 173 | 夢のような一日だった (`sent:gen-03b6d82b6425`) | よう@2 | よう / よう / よう | 用/よう (n4) | 様/よう (n4) |
| 5 | `wrong_homograph` | relink | 397 | 雨が降った、それで試合は中止になった (`sent:gen-0236d58af76f`) | なっ@11 | なる / 成る / なる | 生る/なる (n5) | 成る/なる (n3) |
| 6 | `wrong_reading` | review | 177 | 肉いがいは何でも食べます (`sent:gen-2d4d2149594f`) | 何@3 | 何 / 何 / なん | 何/なに (n5) | review: 何/なん |
| 7 | `wrong_pos` | unlink | 108 | ところで、仕事はどうですか (`sent:gen-03ac75285d31`) | どう@5 | どう / どう / どう | 動/どう (n5) | unlink |
| 8 | `auxiliary_as_lexical` | relink | 21 | 彼は先月以来病気だそうです。 (`sent:tatoeba-103067`) | そう@6 | そう / そう / そう | 琴/こと (n4) | 然う/そう (n5) |
| 9 | `wrong_homograph` | relink | 101 | 君、ちょっと手伝ってくれる (`sent:gen-0f4c597575c9`) | くれる@5 | くれる / 呉れる / くれる | 暮れる/くれる (n4) | 呉れる/くれる (n1) |
| 10 | `wrong_reading` | relink | 90 | ペンは引き出しの中にあります (`sent:gen-0af0907e1414`) | 中@4 | 中 / 中 / なか | 内/うち (n5) | 中/なか (n5) |
| 11 | `wrong_pos` | relink | 97 | ここに名前を書いてください (`sent:gen-126c406f1124`) | ここ@0 | ここ / 此処 / ここ | 九/きゅう (n5) | 此処/ここ (n5) |
| 12 | `wrong_homograph` | relink | 51 | 朝は支度に時間がかかります (`sent:gen-01348b4a6b3b`) | かかり@6 | かかる / 掛かる / かかる | 罹る/かかる (n5) | 掛かる/かかる (n3) |
| 13 | `wrong_reading` | relink | 68 | ポストは駅の前にある (`sent:gen-03cb7d78a3dc`) | 前@4 | 前 / 前 / まえ | 先/さき (n5) | 前/まえ (n5) |
| 14 | `wrong_pos` | unlink | 51 | 弱い人を苛めてはいけない (`sent:gen-1ab712f1023e`) | いけ@6 | いける / 行く / いける | 池/いけ (n5) | unlink |
| 15 | `wrong_homograph` | relink | 47 | 肉より魚のほうが好きです (`sent:gen-15f024acc430`) | ほう@4 | ほう / 方 / ほう | 報/ほう (n5) | 方/ほう (n3) |
| 16 | `wrong_reading` | review | 47 | 私は十年この店に勤めた (`sent:gen-0a4b3bbcc83e`) | 年@3 | 年 / 年 / ねん | 年/とし (n5) | review: 年/ねん |
| 17 | `wrong_pos` | relink | 32 | 天気予報によると明日は雨だそうです (`sent:gen-1ec31af439b5`) | よる@2 | よる / よる / よる | 夜/よる (n5) | 依る/よる (n2) |
| 18 | `wrong_homograph` | relink | 32 | 服に犬の毛がついている (`sent:gen-16f904158589`) | つい@6 | つく / 付く / つく | 着く/つく (n5) | 付く/つく (n4) |
| 19 | `wrong_reading` | review | 32 | 魚は沖の方にいるらしい (`sent:gen-0b452aff306a`) | 方@4 | 方 / 方 / ほう | 方/かた (n5) | review: 方/ほう |
| 20 | `wrong_pos` | relink | 21 | どうしてそんなに早いの (`sent:gen-12158caf703e`) | どう@0 | どう / どう / どう | 動/どう (n5) | 如何して/どうして (n5) |
| 21 | `wrong_homograph` | relink | 26 | 今日は日曜日だから、店が閉まっているわけだ (`sent:gen-482d7dfc9c92`) | わけ@11 | わけ / 訳 / わけ | 理由/りゆう (n4) | 訳/わけ (n4) |
| 22 | `wrong_reading` | review | 32 | 薬を飲む時はアルコールを飲まない (`sent:gen-21882c0b07f8`) | 時@3 | 時 / 時 / とき | 時/じ (n5) | review: 時/とき |
| 23 | `wrong_pos` | unlink | 8 | 茶色の靴をはいている (`sent:gen-184539bcd1c1`) | はい@4 | はく / はく / はく | 伯/はく (n5) | unlink |
| 24 | `wrong_homograph` | relink | 6 | 彼は単に読むふりをしていたとわかった。 (`sent:tatoeba-102276`) | ふり@4 | ふり / 振り / ふり | 不利/ふり (n3) | 振り/ふり (n2) |
| 25 | `wrong_reading` | review | 29 | 今日は１月５日だ (`sent:gen-099cd0de9ac8`) | 月@3 | 月 / 月 / がつ | 月/つき (n5) | review: no record carries the analyzer's reading |
| 26 | `wrong_pos` | relink | 8 | 田中氏がそう言いました (`sent:gen-e6318f8e6b33`) | そう@3 | そう / そう / そう | 琴/こと (n4) | 然う/そう (n5) |
| 27 | `wrong_homograph` | relink | 4 | アイス買ってきてよ、カップ系のやつ。 (`sent:tatoeba-11045343`) | やつ@10 | やつ / 奴 / やつ | 八つ/やっつ (n5) | 奴/やつ (n1) |
| 28 | `wrong_reading` | review | 27 | 薬を一日二回飲む (`sent:gen-0314332f3d50`) | 日@3 | 日 / 日 / にち | 日/ひ (n5) | review: 日/にち |
| 29 | `wrong_pos` | relink | 6 | 行かないといけないの？ (`sent:tatoeba-10510923`) | いけ@3 | いける / 行く / いける | 池/いけ (n5) | 行けない/いけない (n3) |
| 30 | `wrong_homograph` | relink | 3 | 彼の援助をあてにするな。 (`sent:tatoeba-118082`) | あて@4 | あて / 当て / あて | 父/ちち (n5) | 当て/あて (n1) |

## Review queue, grouped by pair

A ruling per pair settles every row in it (the `homograph_rulings.json` pattern).

| class | linked | proposed | rows |
|---|---|---|---:|
| `wrong_reading` | 何/なに (n5) | 何/なん | 177 |
| `wrong_reading` | 年/とし (n5) | 年/ねん | 47 |
| `wrong_reading` | 方/かた (n5) | 方/ほう | 32 |
| `wrong_reading` | 時/じ (n5) | 時/とき | 32 |
| `wrong_reading` | 月/つき (n5) | (none) | 29 |
| `wrong_reading` | 日/ひ (n5) | 日/にち | 27 |
| `wrong_reading` | 開く/あく (n5) | 開く/ひらく | 27 |
| `wrong_reading` | 米/メートル (n5) | 米/こめ | 19 |
| `wrong_reading` | 止める/やめる (n4) | 止める/とめる | 12 |
| `wrong_reading` | 金/かね (n3) | 金/きん | 9 |
| `wrong_reading` | 昨夜/ゆうべ (n5) | (none) | 8 |
| `wrong_reading` | 米/メートル (n5) | (none) | 8 |
| `wrong_reading` | 実/み (n3) | 実/じつ | 6 |
| `wrong_reading` | 間/あいだ (n4) | 間/ま | 6 |
| `wrong_reading` | 数/かず (n3) | 数/すう | 6 |
| `wrong_reading` | 市場/いちば (n3) | 市場/しじょう | 6 |
| `wrong_reading` | 分/ふん (n5) | 分/ぶん | 5 |
| `wrong_reading` | 種/たね (n3) | (none) | 5 |
| `wrong_reading` | 辛い/からい (n5) | 辛い/つらい | 3 |
| `wrong_reading` | 下/した (n5) | 下/もと | 3 |
| `wrong_reading` | 深い/ふかい (n4) | (none) | 3 |
| `wrong_reading` | 球/きゅう (n3) | 玉/たま | 3 |
| `wrong_reading` | 世/よ (n4) | (none) | 3 |
| `wrong_reading` | 仏/ほとけ (n3) | 仏/ふつ | 3 |
| `wrong_reading` | 盛り/さかり (n3) | (none) | 3 |
| `wrong_reading` | 名/な (n3) | (none) | 3 |
| `wrong_pos` | 父/ちち (n5) | (none) | 2 |
| `wrong_reading` | 直/じき (n3) | (none) | 2 |
| `wrong_pos` | 絵/え (n5) | (none) | 2 |
| `wrong_reading` | 柄/え (n3) | 柄/がら | 2 |
| `wrong_reading` | 縁/ふち (n3) | (none) | 2 |
| `wrong_reading` | 得る/える (n3) | 得る/うる | 2 |
| `wrong_reading` | 否/いや (n3) | 否/いな | 2 |
| `wrong_reading` | 綿/めん (n3) | 綿/わた | 2 |
| `wrong_reading` | 他/ほか (n5) | 他/た | 2 |
| `wrong_reading` | 下ろす/おろす (n3) | (none) | 2 |
| `wrong_reading` | 箱/はこ (n5) | (none) | 2 |
| `wrong_homograph` | 着く/つく (n5) | 付く/つく | 1 |
| `wrong_reading` | ２０歳/はたち (n5) | (none) | 1 |
| `wrong_pos` | 本/ほん (n5) | (none) | 1 |
| `wrong_homograph` | 寝る/ねる (n5) | 練る/ねる | 1 |
| `wrong_pos` | 買う/かう (n5) | (none) | 1 |
| `wrong_reading` | 局/きょく (n3) | (none) | 1 |
| `wrong_homograph` | 生る/なる (n5) | 成る/なる | 1 |
| `wrong_reading` | 角/かど (n5) | 角/かく | 1 |
| `wrong_reading` | 等/など (n5) | (none) | 1 |
| `wrong_reading` | 一日/いちにち (n5) | １日/ついたち | 1 |
| `wrong_reading` | 町/まち (n5) | (none) | 1 |
| `wrong_reading` | 風/かぜ (n5) | 風/ふう | 1 |
| `wrong_pos` | 幕/まく (n3) | 撒く/まく, 蒔く/まく | 1 |
| `wrong_reading` | 体/からだ (n5) | (none) | 1 |
| `wrong_reading` | 鳥/とり (n5) | (none) | 1 |
| `wrong_reading` | 管/くだ (n3) | 管/かん | 1 |
| `wrong_reading` | 足/あし (n5) | (none) | 1 |
| `wrong_reading` | 玩具/おもちゃ (n4) | (none) | 1 |
| `wrong_reading` | 表/おもて (n4) | 表/ひょう | 1 |
| `wrong_reading` | 後/のち (n3) | (none) | 1 |
| `wrong_reading` | 若し/もし (n4) | (none) | 1 |
| `wrong_reading` | 歳/さい (n5) | 年/とし | 1 |
| `wrong_reading` | 音/おと (n4) | 音/おん | 1 |

## Effect on sentence levels

Applying the relink and unlink rows touches **2,910 sentences**. Recomputed the way
`persist_dissection.recompute_all_levels()` does (max level over `sentence_vocab` and `sentence_kanji`),
dropping an old edge only when no other token of the sentence still links it and adding the new one,
**278 sentences change computed level**:

| move | sentences |
|---|---:|
| n4->n3 | 128 |
| n3->n1 | 40 |
| n4->n1 | 28 |
| n5->n3 | 22 |
| n3->n2 | 21 |
| n2->n1 | 17 |
| n4->n2 | 12 |
| n2->n3 | 4 |
| n5->n4 | 3 |
| n5->n2 | 2 |
| n1->n3 | 1 |

Old `sentence_vocab` edges that would lose their only token: 1,101 with `link_rule='token'` and 2,311 legacy rows with no rule.

**The moves are almost all upward, and that is a finding, not a side effect.** The level evidence sits on
the wrong sibling. The community lists name なる, くれる, ほう, かかる at N5/N4; the level pass attached that
level to whichever record the kana matched, so 生る "dar fruto" is N5 while 成る is N3, 暮れる is N4 while
呉れる is N1. Relinking the token to the right record without moving the level would push ordinary N5
sentences to N3 or N1. The level repair must precede or accompany the relink. Relink pairs whose target
is higher than the record it replaces:

| linked (level) | should be (level) | rows |
|---|---|---:|
| 刷る/する (n5) | 為る/する (n4) | 932 |
| 彼/あれ (n5) | 彼/かれ (n4) | 748 |
| 生る/なる (n5) | 成る/なる (n3) | 397 |
| 暮れる/くれる (n4) | 呉れる/くれる (n1) | 101 |
| 罹る/かかる (n5) | 掛かる/かかる (n3) | 51 |
| 報/ほう (n5) | 方/ほう (n3) | 47 |
| 着く/つく (n5) | 付く/つく (n4) | 32 |
| 夜/よる (n5) | 依る/よる (n2) | 32 |
| 内/うち (n5) | 裏/うら (n4) | 12 |
| 不利/ふり (n3) | 振り/ふり (n2) | 6 |
| 池/いけ (n5) | 行けない/いけない (n3) | 6 |
| 有る/ある (n5) | 或る/ある (n3) | 6 |
| 息子/むすこ (n4) | 息/いき (n3) | 5 |
| 歌/うた (n5) | 詩/し (n3) | 5 |
| 机/つくえ (n5) | 案/あん (n3) | 4 |
| 八つ/やっつ (n5) | 奴/やつ (n1) | 4 |
| 杯/はい (n5) | 一杯/いっぱい (n4) | 3 |
| 父/ちち (n5) | 当て/あて (n1) | 3 |
| 体/からだ (n5) | 身体/しんたい (n3) | 3 |
| 下がる/さがる (n4) | 下る/くだる (n2) | 3 |
| 其れ/それ (n5) | 逸れる/それる (n2) | 3 |
| 二/に (n5) | 蓋/ふた (n2) | 2 |
| 割れる/われる (n4) | 破れる/やぶれる (n2) | 2 |
| 六/ろく (n5) | 陸/りく (n3) | 2 |
| 嫌/いや (n5) | 否/いや (n3) | 2 |

## Effect on exam and exercise items

Items that cite an affected sentence: **2,239**. Items that cite the affected
token itself (the item names the old or the new record, or its stem/answer contains the token surface):
**795**, of which
exam_banks 430, exercises 231, course-lessons 134.

Items citing an affected sentence, by file:

| file | items |
|---|---:|
| corpus/exercises | 1406 |
| course/n3 lessons | 191 |
| exam_banks/n3_grammar_form.json | 87 |
| exam_banks/n4_sentence_order.json | 85 |
| exam_banks/n4_context_fill.json | 82 |
| exam_banks/n4_grammar_form.json | 80 |
| exam_banks/n3_context_fill.json | 66 |
| course/n4 lessons | 55 |
| exam_banks/n3_sentence_order.json | 47 |
| exam_banks/n5_context_fill.json | 39 |
| exam_banks/n5_sentence_order.json | 23 |
| course/n5 lessons | 23 |
| exam_banks/n5_grammar_form.json | 13 |
| exam_banks/n3_usage.json | 9 |
| exam_banks/n4_paraphrase.json | 6 |
| exam_banks/removed_items.json (already retired) | 6 |
| exam_banks/n3_paraphrase.json | 5 |
| exam_banks/n4_usage.json | 5 |
| exam_banks/n3_listening_reply.json | 3 |
| exam_banks/n5_paraphrase.json | 3 |
| exam_banks/n5_usage.json | 3 |
| exam_banks/n4_listening_reply.json | 1 |
| exam_banks/n5_listening_reply.json | 1 |

Each pending row lists its citing items in `cited_by`, so an apply can re-check exactly those. A relink
changes no item text; what can change is an item whose target or explanation was derived from the old
record (a vocab exercise built on 生る because the sentence carried it) and every derived count that
reads token links (sentence levels, card examples, practice coverage).

## Limits

- `kana_ambiguous` (248 tokens) passes on purpose: a kana token whose record is
  common and read that way has nothing against it. Some are still wrong: the つい of について linked to
  着く, せい linked to 背/せい where the sentence means 所為, おり in しておりました linked to 折る. They need
  a lexical rule (について is an expression) or a ruling, not this audit's evidence. Top patterns:

  - つい linked to 着く/つく (alternatives: 点く|吐く): 33
  - すみ linked to 住む/すむ: 19
  - せい linked to 背/せい (alternatives: 所為): 10
  - おり linked to 折る/おる (alternatives: 居る): 7
  - ぬれ linked to 濡れる/ぬれる: 6
  - おじ linked to 叔父/おじ: 6
  - かわり linked to 代わり/かわり: 5
  - ひか linked to 引く/ひく (alternatives: 轢く): 5
  - いか linked to 以下/いか: 4
  - かさ linked to 傘/かさ: 4
  - なおす linked to 直す/なおす: 4
  - じゃあ linked to じゃあ/じゃあ: 4

- The registry lacks some words the bank needs (どう "como", 行ける, 溜める). Those links become `unlink`;
  adding the records is a separate decision.
- Split-mode A tokens carry no links, so they were not audited.
- Sudachi and the stored reading share a lineage, so a reading both get wrong goes undetected when the
  wrong reading happens to be registered on the linked record.
