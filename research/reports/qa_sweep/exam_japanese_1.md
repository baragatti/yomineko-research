# QA sweep — Japanese quality of exam items (`exam_japanese_1`)

**Scope.** `corpus/exam_banks/n5_*.json` (all 13 banks) + `n4_kanji_reading.json` + `n4_orthography.json`.
**Question asked of every item:** is the Japanese itself natural and unambiguous *as an exam question* —
stem well-formed, exactly one defensible correct option, no distractor that is also arguably correct in
context, options register-consistent?

**Out of scope by instruction:** sentence `structure_explanation` fields (being re-authored concurrently).
pt-BR wording, level assignment, and schema/structural integrity were not the target and are only mentioned
where they produce a *Japanese* defect.

Mechanical pre-screens that came back **clean** (recorded so they are not re-run): no duplicate item ids; no
duplicated options within an item; no `correct` repeated in `distractors`; `pieces` always reassemble to
`answer`; and — importantly — **no orthography distractor is an exact homophone of its stem, and no
kanji-reading distractor is an alternate reading of its stem**, cross-checked against a form→reading map
built from all five `corpus/vocab/*.json` levels plus every n3/n4/n5 reading and orthography bank
(18,388 surface forms). The builder clearly guarded that edge. The defects below are elsewhere.

---

## F1 — Orthography: byte-identical items with contradictory answer keys (37 items) — SEVEREST

Ten n5 stems and eight n4 stems each appear as **two or three separate items whose stem and distractor set
are character-for-character identical, differing only in which kanji is keyed correct**.

```
or:n5:23 | stem=あつい | correct=暑い | D=暗い/上る/車
or:n5:24 | stem=あつい | correct=熱い | D=暗い/上る/車
or:n5:25 | stem=あつい | correct=厚い | D=暗い/上る/車
```
```
or:n4:1140 | stem=たずねる | correct=尋ねる | D=食事/等々/調べる
or:n4:1286 | stem=たずねる | correct=訪ねる | D=食事/等々/調べる
```

Why it is a defect: an orthography item asks "which kanji writes this kana?", and a bare kana headword with
no sentence around it does not select between 暑い / 熱い / 厚い. Each item individually is unanswerable in
principle; taken together the bank asserts three different right answers to the same printed question. If the
simulator samples two of a group into one paper (spec `design/exam_simulator.md` samples randomly per
attempt), the learner sees the same question twice and is marked wrong on one of them. This is the
canonical killer defect for a multiple-choice bank.

Full list — n5 (`or:n5:`), identical distractors unless noted:

| stem | items | keyed answers |
|---|---|---|
| あつい | 23 / 24 / 25 | 暑い / 熱い / 厚い |
| あめ | 36 / 37 | 雨 / 飴 |
| いる | 69 / 70 | 居る / 要る |
| かける | 153 / 154 | 掛ける / 翔る |
| かぜ | 157 / 158 | 風 / 風邪 |
| きる | 204 / 205 | 切る / 着る |
| くらい | 220 / 221 | 暗い / 位 |
| しめる | 299 / 300 | 閉める / 締める |
| かい | 137 / 138 *(distractors differ)* | 回 / 階 |
| ご | 237 / 238 *(distractors differ)* | 五 / 語 |

n4 (`or:n4:`), all with identical distractors: おる 989/712 (居る/折る) · かっこう 1334/1223 (格好/滑降) ·
け 811/1063 (家/毛) · けんか 1359/842 (献花/県下) · こと 887/1350 (事/琴) · たずねる 1140/1286 ·
たてる 756/916 (建てる/立てる) · つく 1352/1221 (付く/点く).

**Fix.** An orthography stem must be a *sentence* with the target word in kana, exactly as JLPT 表記 does it —
`へやが__ですね。` selects 暑い; `このほんは__ですね。` selects 厚い. Every one of these 18 stems already has a
sibling in the sentence bank that could supply the frame (e.g. `us:n5:23` 「今日はとても暑い。」,
`us:n5:25`「この本はとても厚い」). Second-best fix if the bare-word format must stay: keep exactly one item
per kana stem and drop the rest to `removed_items.json`.

---

## F2 — Orthography: the keyed "correct kanji" is a full-width Arabic numeral (4 items)

```
or:n5:59  | stem=いつか   | correct=５日
or:n5:248 | stem=ここのか | correct=９日
or:n5:401 | stem=ついたち | correct=１日
or:n5:440 | stem=とおか   | correct=１０日
```

`５日` is not a kanji spelling of いつか — it is a numeral plus a kanji. In a bank whose whole task is
"pick the kanji form", the keyed answer is not one. It also loses the item's only content: 五日 is the answer
worth teaching. A further 19 n5 items use numeral strings as *distractors* (`or:n5:95` おいしい → distractor
`１日`; `or:n5:110` おそい → `５日`; `or:n5:174` からだ → `２０日`; also 98, 227, 256, 276, 287 …), which a
learner eliminates on sight without reading any Japanese.

**Fix.** Key 五日 / 九日 / 一日 / 十日. Rebuild numeral distractors as kanji forms.

---

## F3 — Orthography n5: 36 items whose keyed answer is a form no one writes (register)

The "correct kanji spelling" is an archaic ateji or a JMdict `rK`/`uk` form:

`or:n5:1` ああ→**嗚呼** · `17` あそこ→**彼処** · `22` あちら→**彼方** · `27` あなた→**貴方** · `31` あの→**彼の** ·
`39` ある→**有る** · `46` いかが→**如何** · `48` いくつ→**幾つ** · `58` いつ→**何時** · `83` うるさい→**煩い** ·
`95` おいしい→**美味しい** · `148` かかる→**罹る** · `154` かける→**翔る** · `246` ここ→**此処** ·
`252` こちら→**此方** · `257` この→**此の** · `261` これ→**此れ** · `285` しかし→**然し** · `328` ずつ→**宛** ·
`351` そして→**而して** · `352` そこ→**其処** · `353` そちら→**其方** · `358` それ→**其れ** · `448` とても→**迚も**
(+ 35, 49, 62, 69, 206, 212, 371, 388, 399, 400, 418, 1340).

Two of these are not merely rare but **wrong for the keyed reading**: `or:n5:351` keys 而して for そして, but
而して is standardly read しかして; `or:n5:328` keys 宛 for ずつ, but 宛 standardly reads あて (宛先). And
`or:n5:154` keys 翔る for かける while `or:n5:153` keys 掛ける for the same stem (see F1) — 翔る is a different
verb entirely (to soar).

96 further n5 items carry one of these forms as a *distractor*, plus the obsolete unit ligatures
**粁** (キロメートル, `or:n5:140`, `198`), **瓩** (キログラム), **釦** (ボタン, `or:n5:206`),
**燐寸** (マッチ, `or:n5:133`), **洋杯** (コップ, `or:n5:199`), **洋袴** (ズボン, `or:n5:54`, `203`),
**頁** (ページ, `or:n5:152`). These break option register: three plausible modern kanji plus one Meiji-era
ligature is a giveaway.

**Fix.** Exclude JMdict `uk`/`rK` forms from both the answer key and the distractor pool for orthography.
A word that is normally kana has no orthography item; it belongs in a kana-writing exercise instead.

---

## F4 — Kanji reading: stems with two equally standard readings, including two self-contradictions (23 items)

Presenting a bare single kanji and demanding one reading is only fair when the kanji has one. These do not:

**Self-contradicting pairs (same stem, two items, two keys):**
```
kr:n5:1338 | 背 | correct=せ   | D=ひ/と/ご
kr:n5:336  | 背 | correct=せい | D=むら/がわ/しる
```
```
kr:n4:1219 | 君 | correct=きみ | D=なる/なく/おる
kr:n4:1233 | 君 | correct=くん | D=なる/なく/おる     ← identical distractors
```
Cross-level: `kr:n5:271` 先→さき vs `kr:n4:827` 先→**さっき**; `kr:n5:69` 居る→いる vs `kr:n4:989` 居る→**おる**.
The alternate is never among the distractors, so the item is answerable by elimination — but the printed
question has two right answers and the learner who knows the common one is punished.

**Stems where the keyed reading is not the default reading:**
`kr:n5:283` 時→じ (standalone 時 is とき) · `kr:n5:306` 中→ちゅう (なか is the N5 reading) ·
`kr:n5:355` 園→その (えん) · `kr:n5:370` 丈→だけ (たけ) · `kr:n5:503` 杯→さかずき (はい) ·
`kr:n5:328` 宛→ずつ (あて) · `kr:n5:159` 方→かた (ほう) · `kr:n5:445` 年→とし (ねん) ·
`kr:n5:56` 一日→いちにち (ついたち) · `kr:n5:58` 何時→いつ (なんじ) ·
`kr:n4:811` 家→け (いえ) · `kr:n4:1202` 御→ご (お/おん/み) · `kr:n4:1041` 玩具→おもちゃ (がんぐ) ·
`kr:n4:699` 等々→とうとう (などなど).

**Bound morphemes presented as free stems:** `kr:n4:918` 員→いん, `kr:n4:764` 製→せい,
`kr:n4:1086` 侯→こう (侯 is not an N4 kanji under any list).

**Fix.** JLPT 漢字読み always embeds the word in a sentence with the target underlined, precisely to kill this.
Since the sentence bank already links each vocab id to real sentences, wrap the stem: `せが たかい。` vs
`せいが たかい。` resolve 背 immediately. Failing that, drop stems whose vocab entry has more than one
`kana` value across the registry (318 such forms exist — the check is already written).

---

## F5 — Kanji reading: full-width Arabic numeral stems (4 items)

```
kr:n5:59  | ５日   | correct=いつか
kr:n5:248 | ９日   | correct=ここのか
kr:n5:401 | １日   | correct=ついたち
kr:n5:440 | １０日 | correct=とおか
```
`１日` is read ついたち (date) **or** いちにち (duration) — both standard, and the bank keys 一日→いちにち at
`kr:n5:56`, so it knows. Beyond the ambiguity, a numeral is not a kanji, so these are not kanji-reading items.

**Fix.** Use 五日 / 九日 / 一日 / 十日 in a date frame (`３がつ__に あいましょう。` forces ついたち).

---

## F6 — Kanji reading: katakana-loanword distractors (48 items: 29 n5, 19 n4)

```
kr:n5:76  | 薄い | correct=うすい | D=グラム/ひだり/えいご
kr:n5:97  | 大きい | correct=おおきい | D=ちゃわん/しつもん/コーヒー
kr:n4:1118| 以上 | correct=いじょう | D=かいがん/ほとんど/アメリカ
```
Also マッチ, キログラム, キロメートル, タバコ, メガネ, メートル, カレー, コップ, ズボン, ページ (n5);
ゴミ, ガス, アジア, アフリカ (n4). A katakana loanword can never be the reading of a kanji stem, so it is
eliminated without reading the Japanese, and it is the only katakana string in an otherwise all-hiragana
option set — register-inconsistent on its face. Effective option count drops from 4 to 3.

**Fix.** Restrict the kanji-reading distractor pool to kana readings of kanji-written words. (`kr:n4:965`
消しゴム→けしゴム is fine: the katakana is in the word itself.)

---

## F7 — Grammar form: distractor is also grammatical and natural in the stem (24 items) — SEVERE

The item template places the blank after a bare verb stem and fills the options with whole grammar-point
labels. Many labels attach to the same stem just as legally as the key does.

The flat-out worst — **the distractor is the key, respelled**:
```
gf:n5:4513 | 何駅（　）のですか。 | correct=に行く | D=にいく / になる / だけど
```
「何駅**にいく**のですか」 and 「何駅**に行く**のですか」 are the same sentence. (The bank is itself
inconsistent: `gf:n5:4286` keys the kana form にいく, `gf:n5:2522` keys the kanji form に行く.)

**Same grammar point offered twice** — `〜んです` keyed, `〜のです` offered:
```
gf:n5:4251 | 本を読んでいる（　）。 | correct=んです | D=つもり / のです / くなる
gf:n5:4506 | 大雨で外出できなかった（　）。 | correct=んです | D=に行く / のです / どんな
```
`〜じゃない` keyed, `〜ではない` offered — and the grammar entry is literally named
`janai-dewa-nai`, i.e. the bank knows they are one point:
```
gf:n5:4311 | 話をつけよう（　）か。 | correct=じゃない | D=のが下手 / ではない / たりする
gf:n5:4428 | 中休みしよう（　）か。 | correct=じゃない | D=ましょう / のが好き / ではない
```
「話をつけよう**ではない**か。」 is correct, formal, and used.

**Distractor simply also fits:**

| id | stem | key | distractor that also works |
|---|---|---|---|
| gf:n5:4591 | 出（　）か。 | てもいいです | **たほうがいい** →「出たほうがいいか。」 |
| gf:n5:4592 | 食べ（　）か？ | てもいいです | **たほうがいい**, **てはいけない** (two) |
| gf:n5:4593 | 入っ（　）か？ | てもいいです | **たことがある** →「入ったことがあるか？」 |
| gf:n5:4595 | 外に出（　）か？ | てもいいです | **てはいけない** |
| gf:n5:4139 | 言っ（　）んだけど。 | ちゃいけない | **たほうがいい** |
| gf:n5:67 | さあ出かけ（　）。 | ましょう | **ませんか** |
| gf:n5:4453 | 今からドライブに行き（　）。 | ませんか | **ましょう** |
| gf:n5:4477 | 行か（　）の？ | ないといけない | **ないほうがいい** |
| gf:n5:4481 | 何で学校に行か（　）の？ | ないといけない | **ないほうがいい** |
| gf:n5:92 | 食べ（　）。 | なきゃ | **ている** →「食べている。」 |
| gf:n5:4205 | 人（　）。 | がいる | **だろう** →「人だろう。」 |
| gf:n5:4208 | さあ、ピザ（　）人ー！ | がいる | **がある** |
| gf:n5:4188 | 何人の子ども（　）か。 | がいます | **がほしい** |
| gf:n5:4328 | （　）くらい？ | どれ | **それ** →「それくらい？」 |
| gf:n5:4331 | （　）くらいかかるのかしら。 | どれ | **その** →「そのくらい…」 |
| gf:n5:4293 | （　）か？ | なぜ | **どれ** →「どれか？」 |
| gf:n5:4292 | （　）？ | なぜ | **ここ** →「ここ？」 |
| gf:n5:4464 | いい（　）。 | なあ | **けど** →「いいけど。」 |
| gf:n5:2422 | （　）人があなたの先生ですか | どの | **この** |

`gf:n5:4292` and `gf:n5:4297` deserve special note: the stem is **literally just `（　）？`**. Any of the four
options that is a standalone utterance is correct.

**Fix.** Two changes. (a) Never draw a distractor from a grammar point that shares a `forms[]` entry, or is a
register variant, of the key — んです/のです, じゃない/ではない, ちゃいけない/じゃいけない, に行く/にいく are one
point each in `corpus/grammar/n5.json` and must be mutually exclusive as options. (b) Reject any item whose
stem is shorter than one clause; the blank has to sit in a sentence that constrains it.

---

## F8 — Grammar form: duplicate stems with contradictory keys (4 items)

```
gf:n5:4292 | （　）？        | correct=なぜ
gf:n5:4297 | （　）？        | correct=なんで
gf:n5:4294 | （　）聞くの？   | correct=なぜ
gf:n5:4299 | （　）聞くの？   | correct=なんで
```
Identical printed questions, and なぜ/なんで are interchangeable in both frames. Whichever the learner picks,
one of the two items marks them wrong.

**Fix.** Merge; keep one item per stem and use a frame that distinguishes register (なんで is casual-only, so
a です／ます frame selects なぜ).

---

## F9 — Grammar form + text grammar: options that are not Japanese strings (37 items)

The option text is a grammar-point *label* with its slots stripped, and in one case with an internal
disambiguation index:

| option string | occurrences | what it should be |
|---|---|---|
| `くらい ①` | 6 | くらい — the ` ①` is a homograph index leaking out of the registry |
| `よりほうが` | 6 | 〜より〜のほうが |
| `たりたり` | 6 | 〜たり〜たり |
| `かか` | 4 | か〜か (traced to `gram:ka-ka`, whose `forms[0].form` is literally `"かか"` while its `structure_pattern` is `"か～か"`) |
| `の中でが一番` | 2 | 〜の中で〜が一番 |
| `のほうがより` | 2 | 〜のほうがより〜 |
| `まだていません` | 2 | まだ〜ていません |
| `のがへたです` / `のがすきです` | 1 each | 〜のが下手です／好きです (and the bank elsewhere writes these `のが下手`, `のが好き` — inconsistent) |

28 of 129 `n5_grammar_form` items and 9 of 33 `n5_text_grammar` items carry at least one. A learner reading
`よりほうが` sees a non-word and eliminates it instantly.

**Fix.** Options must be rendered from `forms[].form`, never from a pattern label, and the template slots have
to be filled or the point excluded from the distractor pool. `gram:ka-ka`'s `forms[0].form` should be fixed at
source (`corpus/grammar/n5.json`) — it is the root cause of `かか`.

---

## F10 — Context fill: stem carries no disambiguating context, so several options fit (36 items) — SEVERE

The worst cases have a stem consisting of the blank plus a copula:
```
cf:n5:25:389 | （　）です！ | correct=小さい | D=郵便局 / お弁当 / 可愛い
```
「郵便局です！」「お弁当です！」「可愛いです！」 are all natural. **All four options are correct.** Likewise:
```
cf:n5:24:389 | （　）！        | correct=小さい | D=欲しい / 女の子 / 答える
cf:n5:21:97  | （　）ね。      | correct=大きい | D=図書館 / 食べ物 / 起きる
cf:n5:1069:58| （　）ですか。   | correct=何時   | D=結婚 / 今月 / 三つ
cf:n5:1081:58| （　）ですか？   | correct=何時   | D=多分 / 昨日 / 家族
```

Longer stems where one specific distractor is equally natural:

| id | stem | key | distractor that also works |
|---|---|---|---|
| cf:n5:22:97 | とても（　）ね。 | 大きい | **可愛い** |
| cf:n5:23:97 | どのくらい（　）？ | 大きい | **食べる** |
| cf:n5:4189:74 | いすの（　）にねこがいます。 | 上 | **中** |
| cf:n5:2437:306 | かばんの（　）に何かありますか | 中 | **上** |
| cf:n5:3370:214 | （　）を出すな。 | 口 | **車**, **絵** |
| cf:n5:4307:47 | （　）んじゃない。 | 行く | **会う**, **死ぬ** |
| cf:n5:3413:47 | 一人で（　）しかない。 | 行く | **聞く** |
| cf:n5:4312:188 | （　）んじゃなかった。 | 聞く | **歩く** |
| cf:n5:4250:184 | （　）にぶつかったんです。 | 木 | **門** |
| cf:n5:4595:354 | （　）に出てもいいですか？ | 外 | **庭** |
| cf:n5:4186:383 | 何か（　）ものがほしい。 | 食べる | **面白い** |
| cf:n5:4310:225 | なんかいい（　）じゃない。 | 車 | **物**, **絵** |
| cf:n5:2490:21 | （　）本をまだ読んでいません | 新しい | **楽しい** |
| cf:n5:2501:102 | もう（　）がありません | お金 | **料理** |
| cf:n5:1391:286 | もう（　）がないじゃないか | 時間 | **荷物** |
| cf:n5:5013:525 | （　）は毎日うちにいます。 | 母 | **兄** |
| cf:n5:2602:37 | 子どもに（　）をあげた | 飴 | **薬** |
| cf:n5:2548:475 | ノートに（　）が書いてある | 名前 | **手紙** |
| cf:n5:3047:36 | （　）でも行きます | 雨 | **私** |
| cf:n5:5446:346 | （　）といってもいろいろある。 | 先生 | **家庭** |
| cf:n5:3556:270 | （　）がいいのですが。 | 魚 | **声** |
| cf:n5:14:115 | あの（　）ももう上がったりだ。 | 男 | **人**, **家** |
| cf:n5:4277:317 | いい（　）だけどイマイチね。 | 人 | **町** |
| cf:n5:3268:55 | 中サイズのコーヒーを（　）つ | 一 | **九** |
| cf:n5:4414:326 | （　）休んだほうがいい。 | 少し | **３日** |
| cf:n5:2618:61 | かばんの中にペンが（　）ある | 五つ | **沢山** |
| cf:n5:4889:36 | （　）らしい。 | 雨 | **車** |
| cf:n5:708:672 | デパートで（　）のカレンダーを買いました。 | 来年 | **部屋** |
| cf:n5:4336:473 | あれ（　）？ | 何 | **箱**, **歌** |
| cf:n5:62:473 | （　）でもけっこうです。 | 何 | **今** |

And the date pair, which is unanswerable by construction:
```
cf:n5:3029:401 | 来月の（　）に会いましょう | correct=１日 | D=貸す / 走る / ２日
```
「来月の**２日**に会いましょう」 is exactly as correct as 「来月の**１日**に…」.

**Fix.** A context-fill distractor must be checked for *fit*, not only for being a different lexeme. Cheap
mechanical guard: reject any distractor of the same POS and semantic class as the key when the stem contains
no other content word; reject stems under ~8 characters outright.

---

## F11 — Context fill: identical stems, different keys (4 items)

```
cf:n5:2964:196 | りんごが（　）つあります | correct=九
cf:n5:3065:291 | りんごが（　）つあります | correct=七
```
Nothing in the stem determines the number. Same problem across `cf:n5:23:97` / `cf:n5:72:369`
(「どのくらい（　）？」 keyed 大きい vs 高い) and `cf:n5:1069:58` / `cf:n5:1081:58`.

---

## F12 — Context fill: malformed stems (6 items)

```
cf:n5:4357:55 | （　）年前くらい前に来ました。 | correct=一
```
「一年前くらい**前**に」 — 前 twice; the source sentence is broken and no completion makes it grammatical.
(The same broken sentence is also `so:n5:4357`.)

Five stems carry stray ASCII/ideographic spaces in the middle of the Japanese, in a bank where the other 230
have none: `cf:n5:2459:283`「あさ 六（　）に おきる」 · `2461:627`「まいにち テレビを （　）」 ·
`2465:591` · `2468:47` · `3046:369`「（　）ですね でも買います」 (the space stands where 。or 、should be).
Numeral width is also inconsistent — 4 stems use half-width (`10ヶ国語`, `2時間`, `2月`), 7 use full-width
(`２０分`, `７月`, `５日`).

---

## F13 — Sentence order: every answer string has all punctuation stripped (273/273)

Not one of the 273 `answer` values contains 。, 、, ？ or ！. The assembled "correct sentence" is therefore
never well-formed written Japanese:

```
so:n5:4347 | いいえけっこうです見ているだけですから    ← two sentences, no boundary
so:n5:3348 | ごめんなさい時間があまりないんです        ← 、missing
so:n5:4407 | あれあなたまだここにいたのね              ← 「あれ、あなた…」
so:n5:83   | 話してもいいですか                        ← ？missing
so:n5:4180 | 二三デメリットがありますね                ← 「二、三」; without the 、, 二三 reads にさん
```

**Fix.** Punctuation is not a reorderable piece — it belongs in the rendered answer. Restore the source
sentence's punctuation in `answer` while keeping `pieces` punctuation-free.

---

## F14 — Sentence order: the same pieces assemble into a second, equally correct sentence (23 items) — SEVERE

Japanese scrambling makes this the structural risk of the format, and the bank does not guard it.

**Argument-order swaps** (both readings natural, same pieces, each used once):

| id | keyed answer | equally valid alternative |
|---|---|---|
| so:n5:4189 | いすの上にねこがいます | ねこがいすの上にいます |
| so:n5:4178 | 木の下にベンチがあります | ベンチが木の下にあります |
| so:n5:4187 | あそこに先生がいます | 先生があそこにいます |
| so:n5:1089 | ポーチにスカンクがいます | スカンクがポーチにいます |
| so:n5:4207 | 学校に人がいる | 人が学校にいる |
| so:n5:4283 | ここにいくつかのバッグがあります | いくつかのバッグがここにあります |
| so:n5:3594 | ２０分ごとにバスがある | バスが２０分ごとにある |

**Adverbial-fronting swaps:**

| id | keyed answer | equally valid alternative |
|---|---|---|
| so:n5:708 | デパートで来年のカレンダーを買いました | 来年のカレンダーをデパートで買いました |
| so:n5:15 | オフィスに時間ぴったりについた | 時間ぴったりにオフィスについた |
| so:n5:827 | 駅までタクシーで２０分かかるでしょう | タクシーで駅まで２０分かかるでしょう |
| so:n5:4174 | どうやって学校に来たの | 学校にどうやって来たの |
| so:n5:4355 | 本をたくさん買ったんだ | たくさん本を買ったんだ |
| so:n5:4406 | 毎年ここに来なきゃ | ここに毎年来なきゃ |
| so:n5:1312 | 三時ごろに駅で会おう | 駅で三時ごろに会おう |
| so:n5:5462 | ７月にしては今日はすずしい | 今日は７月にしてはすずしい |

**Symmetrical-coordination swaps** — the alternative is grammatically identical, only the meaning flips, and
nothing in the item says which meaning is wanted:

| id | keyed answer | equally valid alternative |
|---|---|---|
| so:n5:2359 | この店のほうがあの店より安い | あの店のほうがこの店より安い |
| so:n5:2430 | 電車よりバスのほうが安いです | バスより電車のほうが安いです |
| so:n5:1262 | 電車でもバスでも駅に行ける | バスでも電車でも駅に行ける |
| so:n5:3531 | 話上手もいれば聞き上手もいる | 聞き上手もいれば話上手もいる |
| so:n5:3062 | りんごやみかんなどを買いました | みかんやりんごなどを買いました |
| so:n5:1506 | りんごとかバナナとかをよく買う | バナナとかりんごとかをよく買う |
| so:n5:4968 | １３って言ったそれとも３０ | ３０って言ったそれとも１３ |
| so:n5:4969 | 男の子ですかそれとも女の子 | 女の子ですかそれとも男の子 |

**Fix.** Grade by *acceptability*, not string equality: store an `accepted[]` list, or mark the item
single-answer only after a parse check. The symmetrical-coordination set (bottom block) cannot be repaired —
lock one element into the prompt (JLPT's ★-slot format does exactly this) or remove the items.

---

## F15 — Sentence order: pieces that are not words (7 items + a systemic note)

```
so:n5:2448 | ははは / りょうり / を / つくる / の / が / じょうず / です
           | A=はははりょうりをつくるのがじょうずです
```
`ははは` is 母は tokenized as one all-hiragana blob; concatenated, the answer opens with "hahaha" and is
unreadable. Also: `so:n5:1378` splits 何人 into `なんに` + `ん`; `so:n5:2683` splits おばあさん into
`お`/`ばあ`/`さん`; `so:n5:4770` has three separate `・` pieces (and `・・・` should be `……`);
`so:n5:4208` has a bare `ー` as a draggable piece; `so:n5:1061` and `so:n5:3046` split でも into `で`+`も`.

Systemically, **271 of 273 items expose bound morphemes as draggable pieces** (`まし`, `た`, `ん`, `が`, `を`,
`ませ`, `でし`). Real 文の組み立て gives four *bunsetsu*. Dragging `まし` and `た` apart is not a Japanese task.

**Fix.** Chunk at bunsetsu boundaries (content word + trailing particles/auxiliaries), which also removes most
of F14's swaps by making the pieces larger and more constrained.

---

## F16 — Off-register / off-level source Japanese in learner-facing stems (~18 items)

Vulgar or rough:
```
tg:n5:n5-verbos-05-01 | クリップってある？クソっ。（　）れ！        ← クソっ = "shit"
rc:n5:n5-verbos-05-01 | passage: クリップってある？クソっ。かかれ！
so:n5:4821            | お前らわがままだな                          ← お前ら
tg / rc :n5-particulas-lugar-04-01 | さあ、ピザがいる人ー！お前ら、わがままだな。
```
Slang / criminal argot / dialect:
```
so:n5:3712 | なんだってずらからねえんだ   ← ずらかる is thieves' slang
so:n5:5009 | びびってなんかないよ
rc:n5:n5-particulas-lugar-07-01 | かっけー！おはようございます   ← かっけー slang, and no final 。
rc:n5:n5-perguntas-06-01 | おやすみ。おおきに！              ← おおきに is Kansai dialect
```
Archaic / literary registers a beginner must not imitate: `cf:n5:955:523`「さあ（　）したまえ。」 (〜したまえ),
`so:n5:14` / `cf:n5:14:115`「上がったり」 (商売が上がったり idiom), `cf:n5:4816:373`「やぶへびを出すな」,
`cf:n5:4817:373`「おくびにも出すな」, `so:n5:2707` / `cf:n5:2707:74`「大きな鷲が山の上を翔る」 (鷲, 翔る),
`so:n5:1061` / `tg:n5:n5-comparacoes-05-01`「でももヘチマもないわ」 (garbled: the 〜もヘチマもない idiom needs a
noun before the first も; as written the string is not parseable).

Content note, not a Japanese defect but flagged for the review loop: `gf:n5:1087`「痔（　）。」 keys
「痔があります。」 — a hemorrhoids item in a beginner bank, with a kanji far outside N5.

---

## F17 — Text grammar: the blank cuts a word in half (7 of 33 items)

```
tg:n5:n5-adjetivos-06-01   | よし、（　）ってこい！…            | correct=かか
tg:n5:n5-adjetivos-08-01   | どのくら（　）たの？…              | correct=いい
tg:n5:n5-comparacoes-04-01 | …長く（　）るんでしょうか。         | correct=かか
tg:n5:n5-rotina-03-01      | …ちょっと時間（　）るかも。         | correct=かか
tg:n5:n5-verbos-05-01      | …クソっ。（　）れ！                 | correct=かか
tg:n5:n5-te-form-06-01     | 人を（　）かわないで。…            | correct=から
tg:n5:n5-conectando-06-01  | 車が（　）ばそこへ行ける。…        | correct=あれ
```
None of `かか`, `いい`, `から`(here a fragment of からかう), `あれ`(a fragment of あれば) is the grammar point
being tested — the blank was placed by character offset, not by morpheme boundary. `から` is especially bad:
the same option string is the *particle* から in `tg:n5:n5-adjetivos-05-01` and `-07-01`, so one option string
means two different things across the bank.

**Fix.** Anchor the blank to a token boundary from the reading's own `tokens[]` array (already present in
`corpus/readings/n5.json`).

---

## F18 — Text grammar + reading comp: the "passages" are unrelated sentences bolted together (76 items)

Every `n5_text_grammar` (33) and `n5_reading_comp` (43) item draws on a `read:` slug whose `jp` is two or
three sentences with no discourse relation:

```
read:n5-perguntas-04-01   | ネズミでした。こんにちは。
read:n5-conectando-04-01  | 木にぶつかったんです。人気があるんですか？
read:n5-adjetivos-04-01   | どこに行くところですか。ありがとうございます！
read:n5-adjetivos-07-01   | どこから来ましたか？外に出ようとしない。どのくらい大きい？
read:n5-desu-wa-04-01     | おはようございます！あなたのおかげです。
```
This is fatal for both types by definition. 文章の文法 tests a blank *determined by the surrounding
discourse*; 読解 tests comprehension *of a text*. With no discourse there is nothing to test, and the
questions degenerate into "copy the noun from sentence 1" (`rc:n5:n5-perguntas-04-01`: passage says
ネズミでした, question asks それは何でしたか, answer ネズミ).

It also manufactures ambiguity. `rc:n5:n5-te-form-03-01`:
```
passage: いすの上にねこがいます。あそこのカウンターです。
Q: ねこはどこにいますか。   ANS=いすの上です   D=…/カウンターの上です
```
Because sentence 2 is unrelated, a reader who tries to connect them lands on カウンターの上です — which the
passage neither supports nor excludes. `rc:n5:n5-conectando-05-01` has the same shape: passage
「何人の子どもがいますか。千人もの人がそこにいた。」 keys そこにたくさんの人がいた while offering
子どもが千人いた, which the juxtaposition invites.

Two more keyed answers do not follow from their passage:
- `rc:n5:n5-rotina-03-01` — passage 「クッキーをお一つどうぞ。」 (= *have* one cookie); keyed
  「クッキーは一つです」 (= there *is* one cookie). Different claim.
- `rc:n5:n5-passado-04-01` — passage 「タフだなあ。キツイなあ。」; keyed つよいと思っている. 「キツイ」 says the
  *situation* is hard; nothing fixes タフ as describing a person.

And one straight double-correct in text grammar:
```
tg:n5:n5-convites-05-01 | 学校へ行くところ（　）。千人くらいの人がいた。 | correct=でした | D=もらう/だった/とても
```
「学校へ行くところ**だった**。」 is fully grammatical — and, since the following sentence is plain-form 「いた」,
arguably the more consistent choice.

**Fix.** These two banks need real short passages (3–5 sentences on one topic). Until then they should not
ship as exam types; `n5_reading_comp` in particular cannot be salvaged item-by-item.

---

## F19 — Usage: the correct sentence is identifiable from punctuation alone (6 of 52)

In six items the keyed sentence has **no** sentence-final punctuation while all three wrong sentences do:

```
us:n5:25 [厚い] OK: この本はとても厚い       NG: …まどを開けます。 | …気をつけてください。 | …人が厚いです。
us:n5:61 [五つ] OK: りんごを五つ買った
us:n5:73 [色々] OK: 色々な人がこのブログを見ているようです
us:n5:94 [尾]   OK: あの犬は尾が長い
us:n5:95 [美味しい] OK: 母が作るハンバーグは美味しいです
us:n5:96 [多い] OK: 厳しい意見が多い
```
11.5% of the bank is answerable without reading any Japanese. (The asymmetry is an artefact: the correct
sentence comes verbatim from the sentence bank, the wrong ones were authored with 。)

**Fix.** Normalize terminal punctuation across all four options of every usage item.

---

## F20 — Usage: distractors that are wrong only about the world, not about the word (6 items)

用法 items must be wrong in *usage*. These are not:
```
us:n5:8 [秋]  NG: 秋になって、桜がさきました。
```
Grammatically and collocationally flawless use of 秋; wrong only because cherry blossoms are a spring thing.
A learner who has the word right still cannot reject it on language grounds. Same shape:
`us:n5:19` NG「今日は暖かいので、雪がふります。」 · `us:n5:42` NG「このぎゅうにゅうは古くて良い。」 ·
`us:n5:63` NG「この犬は英語を上手に話す。」

Two are arguably not wrong at all:
```
us:n5:28 [兄] NG: 田中さんの兄は先生です。
us:n5:29 [姉] NG: 山田さんの姉は医者です。
```
「田中さんの兄」 is ordinary neutral/written Japanese for a third party's older brother. The rule the item is
reaching for (兄 for one's own, お兄さん for another's) governs *direct address and in-group/out-group speech*,
not attributive reference. Marking it wrong teaches a rule that does not hold — and the bank breaks its own
version of that rule in F23 below.

---

## F21 — Usage: the correct sentence does not exercise the target (3 items)

```
us:n5:79 [内] OK: 工場内での火事のニュースは世間を騒がせた。
```
The target 内 is keyed うち in `kr:n5:79`, but here it appears as the bound suffix **ない** in 工場内 — a
different morpheme. The item never shows うち. (The distractor 「箱の内に本を入れた。」 is, incidentally, the
one option that *does* use うち, and is acceptable formal Japanese.)

```
us:n5:55 [一] OK: 願いは一つだけ。   NG: 先生が一つ来ました。 | うちに犬が一ついます。
```
Target is 一; every option uses 一つ. The item tests a different lexeme than it names.

```
us:n5:5 [赤] OK: このはこの外は緑だが中は赤である。
```
「このはこの外は」 written without 、 or kanji for はこ is a garden path — この葉／この外 vs この箱／の外.
`pp:n5:5` reuses the same string.

---

## F22 — Paraphrase: the option cannot be substituted into the stem (7 items)

言い換え類義 works by substitution. These do not substitute:
```
pp:n5:90 [駅] 何駅に行くのですか。      ANS=電車にのるところ   → *何電車にのるところに行くのですか
pp:n5:92 [円] １万円でたりる？          ANS=日本のお金         → *１万日本のお金でたりる？
pp:n5:59 [５日] …６月５日の朝７時に…    ANS=六日の前の日       → *…６月六日の前の日の朝７時に…
pp:n5:55 [一] 願いは一つだけ。          ANS=いっこ             → 願いをいっこ counts 願い with 個
pp:n5:48 [幾つ] 弟さんって、お幾つですか？ ANS=何歳            → *お何歳ですか
pp:n5:4  [青い] なぜ空は青いのか？       ANS=青色だ            → *青色だのか (needs 青色なのか)
pp:n5:26 [後] また後で。                ANS=少ししてから       → *また少ししてからで。
```
The target is inside a compound (何駅, １万円, ６月５日) or the substituted form has the wrong inflection
class. Every one yields ungrammatical Japanese when the swap is made.

**Fix.** Reject any paraphrase item whose target is not a free-standing token in the stem, and require the
option's part of speech / inflection class to match the target's.

---

## F23 — Paraphrase: option sets that give the key away by form (18 items)

In a well-built 言い換え item all four options are the same shape. Here the key is routinely a multi-word
gloss and the distractors are single words:
```
pp:n5:28 [兄] ANS=年上の男のきょうだい   D=姉 / 弟 / 妹
pp:n5:16 [明日] ANS=今日の次の日         D=昨日 / 明後日 / 今晩
pp:n5:96 [多い] ANS=たくさんある         D=少しある / ぜんぜんない / 一つだけある   ← this one IS well formed
```
Pick-the-longest wins on `pp:n5:14, 16, 20, 21, 23, 24, 25, 26, 28, 29, 51, 57, 64, 66, 67, 74` (16 items).

One is inflection-class-inconsistent, which is worse:
```
pp:n5:98 [大きな] 大きな音をたてた。 ANS=うるさい  D=小さな / きれいな / しずかな
```
Three な-adjectives and one い-adjective — the odd one out is the answer.

Register-inconsistent keys: `pp:n5:63` 犬→**ワンちゃん** (baby talk) against neutral ねこ/とり/うま;
`pp:n5:97` 大きい→**でかい** (rough) against neutral 小さい/みじかい/まるい. Both are identifiable as "the
one that doesn't sound like the others".

Near-synonym distractor: `pp:n5:23` 暑い→気温が高い offers **暖かい**, which for many speakers paraphrases
暑い acceptably in 「今日はとても…」.

And one key that is not a paraphrase at all:
```
pp:n5:36 [雨] また雨だ。  ANS=いやな天気   D=雪 / 風 / くもり
```
雨 means *rain*, not *unpleasant weather*. Substituting gives a different proposition, while 雪/風/くもり are
the same category as the target — so the option set signals that one of *those* is meant.

Two stems are themselves obscure: `pp:n5:72`「色の上がりがよい。」 (printing jargon) and
`pp:n5:5` (the garden path from F21).

---

## F24 — Listening: in-group/out-group error in a script (1 item)

```
lt:n5:004  N: 学校で先生と男の学生が話しています。
           M1(学生): 先生、お兄さんの辞書をなくしました。
           …
           M1(学生): お兄さんに電話しましょうか。
           ANS=事務所へ行く  D=お兄さんに電話する / …
```
A student speaking **to a teacher** about **his own** older brother must say 兄, not お兄さん. As written the
line means "I lost *your* brother's dictionary". The error is also in the distractor text. It contradicts the
very rule this corpus tests in `us:n5:28`/`us:n5:29`.

**Fix.** 「先生、兄の辞書をなくしました。」 / 「兄に電話しましょうか。」 / distractor 「兄に電話する」.

---

## What came back clean

Worth recording, because it is most of the listening bank and it is good work:

- **`n5_listening_task` (21), `n5_listening_point` (18), `n5_listening_say` (15), `n5_listening_reply` (17)**
  read like real JLPT items: single unambiguous target, distractors each explicitly ruled out by a line of
  the script, correction-and-revision structure handled cleanly (`lp:n5:005` 10→12→11人,
  `lp:n5:011` 3→5→7番, `lt:n5:014` 牛肉→鶏肉), register consistent within and across speakers. Only
  `lt:n5:004` (F24) has a Japanese defect. Two cosmetic notes: the 店の人 role is tagged `M1` in
  `lt:n5:003` but `M2` in `lt:n5:015`/`019`; and elliptical questions are punctuated with 。not ？
  (`lt:n5:011`「おばあさんは。」, `lt:n5:021`「日曜日の買い物は。」).
- **`n5_usage` distractor construction** is otherwise sound — the 暑い/熱い/厚い triad (`us:n5:23/24/25`) is
  a genuinely well-made set of mutually-eliminating wrong sentences.
- **`pp:n5:59`** (six日の前の日 / 六日の次の日 / 四日の前の日 / 三日の次の日) is the one paraphrase item with a
  fully form-consistent option set — use it as the template for the rest.
- The **homophone guard** described at the top: zero violations across 1,600 kanji-reading and orthography
  items. Whatever check produced that should be kept and extended to cover F1 (same-stem answer conflicts),
  which it currently does not.

---

## Priority order for repair

1. **F1** (orthography contradictory keys) and **F7/F8** (grammar-form double-correct) — these mark correct
   answers wrong today.
2. **F18** (text-grammar / reading-comp have no passages) — 76 items that cannot function as their type.
3. **F13/F14/F15** (sentence order) — 273 items produce unpunctuated output; 23 have a second right answer.
4. **F10/F11** (context fill without context) — 39 items.
5. **F9, F17** (non-Japanese option strings, blanks inside words) — ~44 items, mechanical fixes at the
   generator level.
6. **F2–F6** (numeral/ateji/katakana/ambiguous-stem hygiene in the reading and orthography banks).
7. **F19–F23** (usage and paraphrase option-set hygiene), **F16** (register), **F24** (one script line).

---

## Counts

| bank | items checked | items flagged |
|---|---:|---:|
| `n5_kanji_reading` | 400 | 45 |
| `n5_orthography` | 400 | 59 |
| `n5_context_fill` | 235 | 45 |
| `n5_grammar_form` | 129 | 50 |
| `n5_sentence_order` | 273 | 273 |
| `n5_text_grammar` | 33 | 33 |
| `n5_paraphrase` | 52 | 28 |
| `n5_usage` | 52 | 15 |
| `n5_reading_comp` | 43 | 43 |
| `n5_listening_point` | 18 | 0 |
| `n5_listening_reply` | 17 | 0 |
| `n5_listening_say` | 15 | 0 |
| `n5_listening_task` | 21 | 1 |
| `n4_kanji_reading` | 400 | 27 |
| `n4_orthography` | 400 | 16 |
| **total** | **2488** | **635** |

Flagged = distinct item ids named in F1–F24 (an item cited under two findings is counted once).
`n5_sentence_order`, `n5_text_grammar` and `n5_reading_comp` are flagged bank-wide because F13 and F18 are
properties of every item in them, not of a selected subset.

**Aside, outside this assignment's scope but noticed while loading files:** `corpus/exam_banks/INDEX.md`
overstates two of the banks I read — it lists `n5_context_fill.json` at 241 items (file has 235) and
`n5_text_grammar.json` at 37 (file has 33). Whoever owns bank-structure QA should confirm whether items were
moved to `removed_items.json` without regenerating the index.
