# QA sweep — kanji records, slice 1

**Assignment:** `corpus/kanji/n5.json` + `corpus/kanji/n4.json` — **280 records** (n5 103, n4 177): `meanings`
pt-BR vs the `en`/KANJIDIC source, `notes` / `irregular_note` accuracy, `example_words` level fit and glossing,
and whether `readings` are grouped sanely across kun / on / nanori. All **1 812** reading rows and all
**2 193** `example_words` entries were checked.

**Method.** Every record read in full. Mechanically cross-checked against
`research/datasets/jmdict/kanjidic2-en-3.6.2+20260608153333.json.tgz` (10 384 characters) and
`research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip` (217 425 entries), both unpacked read-only
into scratch, plus `corpus/vocab/{n5..n1}.json` (7 401 records) for level, gloss and written-form checks.
Style authority: `design/translation_style.md`. Provenance contract: `CLAUDE.md` §1.1–1.3, `design/i18n.md`.

**Note on this file.** This is an independent pass over the same slice. Findings the earlier pass on this path
had already raised are marked `[confirmed]` and are re-stated from my own measurements, because every one of
them is still present in the exported data. Findings marked **[new]** were not in that report; the first four
below are all new, and **K1–K3 are a single family the earlier pass did not touch at all** — the record's own
prose disagreeing with the record's own grouping.

---

## Headline

**Layer A is exact.** Against KANJIDIC2 all 280 records match on `strokes`, `grade`, `freq_rank` and
`kangxi_radical` with zero mismatches, and the kun/on/nanori reading sets match **exactly in both directions —
0 missing, 0 extra, across all 1 812 rows**, with every row filed under the right type. The 47
`irregular_note` texts that exist are factually correct: every jukujikun, rendaku, gemination and ateji claim I
spot-checked holds (真っ二つ ふた→ぷた, 出発 シュツ→しゅっ + ハツ→ぱつ, 木綿 も as nanori, 八百屋 お, 真っ赤 あか→か,
扇風機 ふう→ぷう, 悪化 あく→あっ). The pt-BR is clean of the usual tells: **0 em dashes, 0 pt-PT forms, 0
"Quanto a", 0 "Vale ressaltar"** across 7 296 pt-BR strings, and the ~1 876 example-word glosses read like
Portuguese a Brazilian teacher would write.

**What fails is the connective tissue.** Three fields that are supposed to describe the same record disagree
with each other: `irregular_note` says a word is unexplained when it is grouped, and stays silent when it
isn't; a reading note points at an irregular list that is `null`; `introduced_at_level` is set on readings with
no evidence and null on readings with plenty. And the `example_words` chooser still has no notion of level or
of which spelling people actually write.

---

## K1 — HIGH — 16 example words belong to no reading group and no `irregular_note` explains them **[new]**

An `example_words` entry is shown to the learner under the kanji. If it is not referenced by any
`readings[].example_vocab_ids`, nothing in the UI highlights which reading it uses — so the record must say why
in `irregular_note`. **78 entries are ungrouped; 16 of them are covered by nothing.** Nine of the affected
records have `irregular_note: null` outright.

| record | ungrouped, unexplained | why it is ungrouped | record has `irregular_note` |
|---|---|---|---|
| `kanji:子` (n5) | 息子 (むすこ), **硝子 (ガラス)** | 硝子 is pure ateji; 子 contributes nothing | **no** |
| `kanji:八` (n5) | **八百屋 (やおや)** | 百 = お is irregular | **no** |
| `kanji:屋` (n4) | **部屋 (へや)**, 八百屋 (やおや) | grouping gap: 屋 = や *is* a listed kun with 5 other examples | **no** |
| `kanji:明` (n4) | 明日 (あした), 明後日 (あさって) | jukujikun | **no** |
| `kanji:真` (n4) | 真っ赤 (まっか), 真面目 (まじめ), 真似 (まね) | まっ / ateji / grouping gap | **no** |
| `kanji:物` (n4) | 果物 (くだもの) | jukujikun | **no** |
| `kanji:親` (n4) | 親父 (おやじ) | grouping gap: おや is a listed kun | **no** |
| `kanji:仕` (n4) | 仕様がない (しょうがない) | 仕様 しよう contracts to しょう | **no** |
| `kanji:図` (n4) | 図々しい (ずうずうしい) | explained, but in the ズ **reading** note, not here | **no** |
| `kanji:土` (n5) | **混凝土 (コンクリート)** | ateji | yes — covers only 土産 / お土産 |
| `kanji:風` (n4) | **風邪 (かぜ)** | jukujikun (邪 is silent) | yes — covers only 扇風機 |

The sharpest case is a flat self-contradiction. `kanji:八` has `irregular_note: null`, and its own kun や note
reads:

```json
// corpus/kanji/n5.json — kanji:八, readings[0]
{ "reading": "や", "type": "kun", "example_vocab_ids": null,
  "note": {"pt-BR": "Leitura nativa (kun) や, usada sem okurigana. Nenhum vocabulário desta lista ficou agrupado nela: 八百屋 (やおや), quitanda, está na lista de leituras irregulares, porque やおや não se reparte de forma regular entre os três kanji."} }
```

The list it sends the learner to does not exist. 八百屋 is `example_words[3]` of the same record.

- **Why it is wrong.** These are exactly the words a beginner most needs the note for: 部屋, 明日, 果物, 風邪,
  八百屋 are among the first hundred words of any N5 course. Shown under the kanji with no reading highlighted
  and no note, they teach that the character is unpredictable rather than that *this word* is.
- **Proposed fix.** Make the two fields complementary by construction: after grouping, any `example_words`
  entry with no `example_vocab_ids` referent must appear in `irregular_note`, and the export should fail
  otherwise. Nine records need a note written; 部屋 / 親父 / 真似 need the grouping fixed instead (屋 = や,
  親 = おや, 真 = ま are all already listed readings with other examples attached).

## K2 — MEDIUM — 6 `irregular_note` texts claim a word is ungrouped that the same record groups **[new]**

The inverse of K1. Six records assert in `irregular_note` that a word "ficou fora dos grupos" / "não bate com
nenhuma leitura", while `readings[].example_vocab_ids` in that same record attaches it to a reading — and in
four cases that reading's own note explains the word correctly.

| record | `irregular_note` says | but the record attaches it to |
|---|---|---|
| `kanji:二` | 真っ二つ "não bate com nenhuma leitura da lista" | kun **ふた.つ**, whose note says "em 真っ二つ ela vira ぷた" |
| `kanji:語` | 物語 "ficou fora dos grupos" | kun **かた.る** |
| `kanji:発` | 出発 "ficou fora dos grupos" | on **ハツ**, whose note says "vira ぱつ em 出発 (しゅっぱつ)" |
| `kanji:引` | 取引 "ficou nos irregulares" | kun **ひ.く** |
| `kanji:服` | 軍服 — and then explains it uses "a mesma leitura フク", i.e. not irregular at all | on **フク**, whose note repeats the same sentence |
| `kanji:足` | 裸足 "o 足 não aparece com nenhuma das leituras acima" | kun **た.す** — see below |

`kanji:足` is a real mis-grouping on top of the contradiction:

```json
// corpus/kanji/n5.json — kanji:足
"irregular_note": {"pt-BR": "Em 裸足 (はだし, descalço) o 足 não aparece com nenhuma das leituras acima. A palavra tem leitura própria e se aprende inteira."}
// …and, in readings[]:
{ "reading": "た", "okurigana": "す", "type": "kun", "example_vocab_ids": [ …裸足… ],
  "note": {"pt-BR": "Leitura nativa た com o okurigana す: 足す, \"somar, adicionar\", ou seja, o sentido de acrescentar."} }
```

はだし's 足 is し. Filing 裸足 under 足す ("to add") puts *barefoot* in the arithmetic group. The
`irregular_note` is the half that is right.

- **Proposed fix.** Detach 裸足 from た.す. For the other five, the reading grouping is correct and the
  `irregular_note` is stale — delete those five notes (the reading notes already carry the content) or reword
  them to "listed under X, with this adjustment", which is what they actually describe.

## K3 — MEDIUM — two reading notes contradict their own `example_vocab_ids` **[new]**

```json
// corpus/kanji/n5.json — kanji:生, on ショウ
{ "reading": "ショウ", "type": "on", "example_vocab_ids": [753, 387],
  "example_vocab": ["vocab:1164010", "vocab:1419110"],
  "note": {"pt-BR": "segunda leitura sino-japonesa, bem mais rara; aqui ela aparece só em 一生懸命 (いっしょうけんめい)."} }
```

The list holds **two** words: 一生懸命 and **誕生日 (たんじょうび)**. The record itself knows this — its kun -う
note says "em 誕生日 (たんじょうび) o 生 soa じょう, da leitura sino-japonesa ショウ". 誕生日 is an N5 word and the
reason an N5 learner meets ショウ at all, and the note tells them it isn't there.

```json
// corpus/kanji/n4.json — kanji:合, kun あい-
{ "reading": "あい-", "type": "kun", "example_vocab_ids": null, "example_vocab": [],
  "note": {"pt-BR": "Leitura nativa あい registrada como forma de começo de palavra (o hífen depois marca essa posição). Os dois vocábulos anexados aqui, 試合 e 場合, trazem 合 no fim da palavra, então nenhum deles é exemplo desse encaixe."} }
```

"Os dois vocábulos anexados aqui" describes an empty list; 試合 and 場合 are attached to the **next** row,
`-あい`. The note was written against a grouping that no longer exists.

- **Proposed fix.** 生 ショウ: "…aparece em 一生懸命 e, sonorizada como じょう, em 誕生日." 合 あい-: drop the
  reference and use the same wording as its four sibling rows ("A lista desta leitura está vazia…").
- **Note for whoever fixes this.** These two are the only contradictions of this shape I could find
  mechanically (numeric claims and exclusivity claims cross-checked against `example_vocab_ids` on all 1 124
  non-nanori rows), so this is a small, closed fix — not a systemic re-authoring.

## K4 — HIGH — `kanji:行` teaches a form JMdict marks never-display, with a sense JMdict does not have **[new]**

```json
// corpus/kanji/n5.json — kanji:行, example_words[1]
{ "headword": "行けない", "kana": "いけない", "slug": "vocab:1000730",
  "gloss": {"pt-BR": ["não poder ir"], "en": ["cannot go"]} }
```

JMdict entry 1000730 tags the kanji form `行けない` as **`sK`** — *search-only*, a form the dictionary states
should not be rendered — and its seven senses are `bad; wrong; naughty` / `must not (do, be)` / `useless; no
good` / `hopeless` / `unfortunate; a pity` / `unable to drink (alcohol)` / `so as not to …`. **"Cannot go" is
not among them.** いけない is a fixed expression meaning *não pode / não deve*; the potential-negative reading
"não poder ir" is a conjugation of 行く, not this lexical item. `corpus/vocab/n3.json` carries the invented
sense as sense 0 and the real one as sense 1, and the kanji layer copies sense 0.

The `kanji:行` kun い.く note repeats the error: *"O mesmo い continua em 行けない (いけない), não poder ir."*

`kanji:青`'s `番瀝青 (ペンキ)` is the only other `sK` headword in the slice.

- **Why it is wrong.** An N5 learner opening 行 is told that 行けない is a dictionary word spelled with kanji
  and meaning "cannot go". All three claims are wrong, and the one slot it occupies is a slot 出口 (でぐち, n5)
  is not getting (see K6).
- **Proposed fix.** Drop 行けない from `kanji:行` (a conjugated form does not belong in a kanji's word list at
  all), and fix `vocab:1000730` sense 0 to JMdict's own first sense. Filter `sK`-tagged forms out of
  `example_words` generally — it is a two-item list today.

## K5 — HIGH — `introduced_at_level` is unsupported in every direction `[confirmed, re-measured]`

Of **1 124** non-nanori reading rows:

| state | rows | what it means |
|---|---:|---|
| tag set, **zero** example words | **65** | nothing in the record could have derived it |
| tag set, contradicts its examples | **24** | both directions — see below |
| **null**, but has example words | **254** | derivable and not derived |
| tag set and consistent | 163 | |
| null and no examples | 618 | correct |

`design/schema_v2.md` derives the field from the example vocab, so 343 of the 506 determinable rows are wrong
or missing. Self-contradictions inside a single record are the clearest:

| record | reading | tagged | its own `example_vocab` resolves to |
|---|---|---|---|
| `kanji:子` (n5) | kun こ | **n4** | 子供 (n5), 女の子 (n5), 男の子 (n5) |
| `kanji:気` (n5) | on キ | **n4** | 病気 (n5), 天気 (n5), 元気 (n5) |
| `kanji:生` (n5) | on ショウ | **n4** | 誕生日 (n5), 一生懸命 (n4) |
| `kanji:入` (n5) | kun い | **n5** | 入る いる (n1) — the only example |
| `kanji:高` (n5) | kun たか | **n5** | 高 (n2) — the only example |
| `kanji:安` (n5) | kun やす | **n5** | 目安 (n2) — the only example |
| `kanji:早` (n4) | kun はや | **n5** | 早口 (n2), 最早 (n1) |

`kanji:子` ends up with **no reading tagged n5** despite being an n5 kanji whose n5 words 子供 and 女の子 sit in
its own reading rows. **15 records have no reading tagged at all** (不 京 仕 以 医 午 図 土 地 意 理 田 自 試 野),
and **43 readings on n5 kanji carry an `n4` tag**.

- **Proposed fix.** Re-derive as documented: for each non-nanori reading,
  `introduced_at_level = min(level_order)` over `example_vocab_ids` (the *easiest* word that uses it), `null`
  where there is no example. Do not patch values one by one — the rule that produced them is not the
  documented rule.

## K6 — HIGH — `example_words` selection ignores level, and skips words the corpus already has `[confirmed, evidence extended]`

**1 503 of 2 193 entries (69%) sit above their own record's level** — 451 of them N1.

| kanji level | entries | above own level |
|---|---:|---:|
| n5 (103 records) | 827 | 561 |
| n4 (177 records) | 1 366 | 942 |
| | | **1 503** (n3 559, n2 370, n1 451, n4-over-n5 123) |

Three records have **zero** at-or-below-level example words: `kanji:京`, `kanji:主`, `kanji:不`. More usefully,
**47 records show an above-level word while skipping an at-or-below-level word that already exists in
`corpus/vocab/` in its common written form** — so no vocab authoring is needed to fix them:

| record | skipped (all at or below the record's level) | shown instead |
|---|---|---|
| `kanji:日` (n5) | 月曜日, 火曜日, 水曜日, 木曜日, 土曜日, 一日, 明後日, 一昨日 | 日曜日 **twice** (K7) |
| `kanji:何` (n5) | 何処 (どこ), 何故 (なぜ), 何時も (いつも), 如何 (いかが) | 何て (n1), 何で (n3), 何も (n3) |
| `kanji:手` (n5) | 切手 (きって), 下手 (へた), お手洗い | 選手 (n3), 相手 (n3), 歌手 (n3) |
| `kanji:大` (n5) | **大人 (おとな)**, 大使館, 大勢 | 偉大 (n3), 大統領 (n3) |
| `kanji:物` (n4) | 着物, 乗り物, 品物, 見物, 忘れ物, 動物園, 贈り物 | 物語 (n3), 植物 (n3) |
| `kanji:場` (n4) | 会場, 売り場, 駐車場, 飛行場 | 市場 (n3) ×2, 立場 (n3) |
| `kanji:茶` (n4) | **お茶 (おちゃ, n5)** | 滅茶苦茶 **twice** (K7), 無茶苦茶, 喫茶 (n1) |
| `kanji:気` (n5) | 電気 (でんき) | 勇気 (n3), 人気 (n3) |
| `kanji:出` (n5) | 出口 (でぐち) | 行けない-adjacent slots; see K4 |
| `kanji:不` (n4) | **不便 (ふべん)** | 10/10 above level |
| `kanji:主` (n4) | **ご主人 (ごしゅじん)** | 10/10 above level |

- **Root cause.** `scripts/export/export_corpus.py:162` sorts `ORDER BY v.common DESC, v.freq_rank IS NULL,
  v.freq_rank LIMIT 10`, with no level term. For 不 and 主 every candidate ties on both keys
  (`common = true`, `freq_rank = null`), so the LIMIT 10 cut falls on undefined row order — 不便 and ご主人 lose
  on row id, and the field is not reproducible across a rebuild.
- **Proposed fix.** `ORDER BY (level_order <= kanji_level_order) DESC, v.common DESC, v.freq_rank IS NULL,
  v.freq_rank, v.slug`.

## K7 — HIGH — 29 example words teach the written form the corpus itself marks `is_common: false` `[confirmed]`

24 records render a `headword` whose `forms[].is_common` is `false` while the kana form is the one flagged
common. **17 of the 29 are tagged `rK` (rare kanji form) by JMdict**, and 2 are `sK` (K4).

| record | headword shown | reading | the form marked common |
|---|---|---|---|
| `kanji:洋` (n4) | 洋杯 / 洋袴 — `example_words[0]` and `[1]` | コップ / ズボン | ズボン, コップ |
| `kanji:早` (n4) | お早う | おはよう | おはよう |
| `kanji:左` (n5) | 左様なら | さようなら | さようなら |
| `kanji:目` (n5) | 御目出度う | おめでとう | おめでとう |
| `kanji:何` (n5) | 如何して | どうして | どうして |
| `kanji:度` (n4) | 屹度 | きっと | きっと |
| `kanji:子` (n5) | 硝子 | ガラス | ガラス |
| `kanji:土` (n5) | 混凝土 | コンクリート | コンクリート |
| `kanji:山` (n5) | 巫山戯る | ふざける | ふざける |
| `kanji:青` (n4) | 番瀝青 | ペンキ | ペンキ |

Six of these headwords (混凝土, 硝子, 番瀝青, 巫山戯る, 屹度, 彼方此方) use characters that appear nowhere in
`corpus/kanji/{n5..n1}.json`, so the record shows an N5 learner a kanji the course never plans to teach.

- **Root cause.** `v.headword` is `forms[is_primary]`, and JMdict's first kanji form is primary even when
  tagged `rK`; `export_corpus.py:161` copies it through.
- **Proposed fix.** Render the first form with `is_common: true`, or drop the candidate entirely when its only
  kanji spelling is rare and the record has alternatives — 洋 has 洋服 / 西洋 / 東洋 / 海洋 / 洋風 waiting.

## K8 — MEDIUM — two records list the same example word twice, byte-identical `[confirmed]`

`kanji:日` (n5) repeats `{"headword": "日曜日", "kana": "にちようび", "slug": "vocab:1464900"}` at
`example_words[7]` and `[8]`; `kanji:茶` (n4) repeats `滅茶苦茶 (めちゃくちゃ, vocab:1533000)`. These are the only
two exact duplicates in 2 193 entries (checked on `slug` and on `(headword, kana)`); every other repeated
headword is a legitimate different-reading pair (中 なか/ちゅう, 悪口 わるぐち/あっこう, 寒気 かんき/さむけ).

Both records sit at the 10-slot cap, so the duplicate costs a real slot — and per K6 the words it displaces are
月曜日 and **お茶**. Both duplicated headwords contain the record's kanji twice (日曜**日**, 滅**茶**苦**茶**),
pointing at a per-occurrence row in the `vocab_kanji` join, though 彼方此方 and 無茶苦茶 do not duplicate, so
dedupe on `slug` rather than assuming the join is uniform.

## K9 — MEDIUM — the nanori block sits between kun and on `[confirmed]`

182 of 280 records order `kun → nanori → on`; 11 more `nanori → on`. **Never** `kun → on → nanori`.

| record | nanori rows before the first on row | on reading buried |
|---|---:|---|
| `kanji:生` (n5) | 25 (first on at index **43 of 45**) | セイ, ショウ |
| `kanji:上` (n5) | 10 (first on at index 25 of 28) | ジョウ, ショウ |
| `kanji:理` (n4) | 16 (of 18) | リ — the only on reading, needed for 料理, 理由, 無理 |
| `kanji:真` (n4) | 15 (of 19) | シン — needed for 写真 |
| `kanji:日` (n5) | 12 (of 17) | ニチ, ジツ |

`export_corpus.py:151` is `ORDER BY kr.reading_type`, a plain string sort, and `kun < nanori < on`
alphabetically. The order is an accident of the enum spelling. The nanori notes themselves say the group has no
common vocabulary; a group the record labels irrelevant should not separate the two relevant ones.

- **Proposed fix.** Sort by an explicit ordinal — kun(0), on(1), nanori(2). Presentation only; no data edits.

## K10 — MEDIUM — `common` on a reading carries no information, and five notes say so `[confirmed]`

`common: true` on **698 of 698** kun rows and **426 of 426** on rows; `false` on **688 of 688** nanori. The
field is a verbatim restatement of `type != 'nanori'`. Six reading notes argue with it:

```json
// corpus/kanji/n5.json — kanji:来 and kanji:気
{ "reading": "タイ", "type": "on", "common": true, "example_vocab_ids": null,
  "note": {"pt-BR": "Segunda leitura sino-japonesa (on) marcada como comum, mas nenhuma palavra desta entrada a usa."} }
{ "reading": "ケ", "type": "on", "common": true, "example_vocab_ids": null,
  "note": {"pt-BR": "Segunda leitura sino-japonesa (on) marcada como comum, mas nenhuma palavra desta entrada a usa."} }
```

(also 山 セン, 女 ニョ, 百 ビャク, 聞 モン). A consumer filtering `readings[].common` to show "the readings that
matter" gets 気 ケ ranked equal to 気 キ and 日 -か equal to 日 ニチ.

- **Proposed fix.** Derive it for real — `common = example_vocab_ids IS NOT NULL` is already computed and
  splits the 426 on rows meaningfully — or drop the field and let consumers read `type`. Either way, correct
  `corpus/kanji/INDEX.md` (which documents it as "`common` (nanori=false)") and delete the six notes.

## K11 — MEDIUM — `kanji:屋` drops "telhado" from pt-BR while its own example word teaches it `[confirmed]`

```json
"meanings": { "pt-BR": ["loja", "estabelecimento", "prédio", "-eiro"],
              "en":    ["roof", "shop", "store", "building", "-dealer"] }
```

KANJIDIC2 for 屋 is `['roof', 'house', 'shop', 'dealer', 'seller']` — roof first. `en` keeps it; pt-BR has no
*telhado* anywhere. Then `example_words[1]` is **屋根 (やね) — "telhado"** and `example_words[4]` is 屋上
("terraço / cobertura de prédio"). Across all 280 records this is the only pt-BR meaning list that drops a
concept its own example words teach: I compared every pt-BR list against its `en` sibling and against KANJIDIC,
and found no other omission and no mistranslation.

- **Proposed fix.** `"pt-BR": ["telhado", "loja", "estabelecimento", "prédio", "-eiro"]`, which also restores
  index parity with `en`.

## K12 — MEDIUM — `meanings.en` is a curated list, not the KANJIDIC source `design/i18n.md` claims `[confirmed]`

**170 of 280 records (61%)** contain at least one `en` gloss that is not a KANJIDIC2 meaning for that character.

| record | `meanings.en` | KANJIDIC2 |
|---|---|---|
| `kanji:金` | gold, **money**, **metal** | gold |
| `kanji:生` | life, **be born**, **live**, **raw** | life, genuine, birth |
| `kanji:安` | cheap, **safe**, **peace** | relax, cheap, low, quiet, rested, contented, peaceful |
| `kanji:病` | **illness**, **sickness**, **disease** | ill, sick |
| `kanji:道` | **road**, **path**, **way** | road-way, street, district, journey, course, moral, teachings |

`design/i18n.md:60-62` states *"the `en` key already preserves the authoritative English source wherever one
exists: kanji **meanings** → `en` from KANJIDIC"*. I checked all 170 divergences by hand and **every one is a
defensible curation** (病 "illness" for KANJIDIC's adjectival "ill"; 京 "Kyoto"; 明 "next (day)"; 服 "dose") —
none is an error. The defect is the provenance label: CLAUDE.md §1.1 defines Layer A as ground truth a reviewer
may trust blindly, and pt-BR is validated *against* `en`, so today both sides of the locale object are authored
with no untouched source between them.

- **Proposed fix.** Amend `design/i18n.md` to describe kanji `meanings.en` as a curated, KANJIDIC-grounded
  Layer-B list, or add a sibling `meanings_source.en` carrying the untouched KANJIDIC array.

## K13 — LOW — pt-BR and gloss-list micro-defects `[partly confirmed, partly new]`

Small, individually cheap, all in learner-facing text.

**a. English-dictionary abbreviations in pt-BR prose** (6 strings, `[confirmed]`):

| record | field | text | fix |
|---|---|---|---|
| `kanji:台` | `meanings["pt-BR"][2]` | contador (sufixo **p/** máquinas e veículos) | `para` |
| `kanji:車` | gloss of 汽車 | trem (**esp.** a vapor) | `especialmente` |
| `kanji:花` | gloss of 花見 | contemplação das flores (**esp.** de cerejeira) | `especialmente` |
| `kanji:漢` | gloss of 漢和 | sino-japonês (**esp.** dicionário de kanji) | `especialmente` |
| `kanji:英` | gloss of 和英 | japonês-inglês (**ex.:** dicionário) | `por exemplo,` |
| `kanji:貸` | gloss of 貸出 | empréstimo (de livro **etc.**) | `e outros` |

`corpus/vocab/n5.json` already writes the 台 concept out in full as *"contador para máquinas e veículos"*, so
the abbreviated form contradicts the corpus's own phrasing.

**b. Glosses that are one string where the schema wants a list** (`common.schema.json#/$defs/LocaleTextList`).
13 `en` glosses keep JMdict's `;` unsplit — 思い出す `["to remember; to recall; to call to mind"]`, 心
`["heart; mind"]`, 火 `["fire; flame"]`, 以内, 用意, 景色, 旅館, 乗り物, 海岸, 森, 用, お土産, 食料品. **[new]**
the pt-BR side is not immune either: 9 pt glosses pack several senses into one comma-joined string — 両方
`["ambos, os dois"]`, 別れる, 動く, 役に立つ, 急ぐ, 特別, 研究, 途中, 間に合う. Worst on both sides is
`kanji:中` / 中 (ちゅう), where two list items each carry three slash-joined glosses:
`["durante/no meio de/em processo de", "ao longo de/por todo"]`. A consumer joining with ", " renders
`heart; mind` where every neighbour renders `heart, mind`.

**c. pt-BR wording** **[new]**, all single occurrences:

- `kanji:山` / 巫山戯る → **"palhaçar"**. Not a pt-BR verb; the form is *fazer palhaçada*.
- `kanji:映` / 映る → **"se refletir", "se espelhar"**. The only two glosses in the slice that open with a
  proclitic pronoun; the corpus writes the enclitic form 67 times elsewhere (espalhar-se, separar-se,
  vender-se, esgotar-se). Should be *refletir-se / espelhar-se*.
- `kanji:赤` spells the same word two ways in adjacent entries: 赤ちゃん → "bebê / **neném**", 赤ん坊 → "bebê /
  **nenê**".
- `kanji:飯` / 飯 (めし) → "arroz cozido / refeição / comida", with no register cue, though JMdict tags the
  entry `male` (rough/masculine speech). The slice flags the other rough entries correctly — 食う "comer
  (**informal**)", 親父 "pai (**informal**)", お前 "você (**informal/rude**)" — so this one is the outlier.

**d. `kanji:文`'s `irregular_note` is imprecise** **[new]**: *"o も de 文字 está listado como leitura deste
kanji"* — も appears only in the **nanori** block, which the record elsewhere describes as names-only, so the
learner cannot find it among the readings they were taught. The parallel note on `kanji:木` gets it right:
*"forma que esta entrada só registra entre as leituras de nome próprio (nanori)"*. Use that wording. (This is
also the only one of the 47 notes that starts lowercase.)

---

## What I checked and found clean

| Check | Rows | Result |
|---|---:|---|
| `strokes` / `grade` / `freq_rank` / `kangxi_radical` vs KANJIDIC2 | 280 each | 0 mismatches |
| kun/on/nanori reading **sets** vs KANJIDIC2, okurigana split reconstructed, both directions | 1 812 | 0 missing, 0 extra |
| Reading `type` filed correctly (no on-as-kun, no kun-as-on, no nanori misfiled) | 1 812 | 0 errors |
| Reading types contiguous within the array (no interleaving) | 280 | 0 split blocks |
| Duplicate `(type, reading, okurigana)` rows within a record | 1 812 | 0 |
| `common: false` on every nanori; `introduced_at_level` null on every nanori | 688 | 0 violations |
| Reading `note` present, non-empty, pt-BR | 1 812 | 0 missing |
| Reading notes: numeric and exclusivity claims vs `example_vocab_ids` | 1 124 | 2 wrong (K3), 55 correct |
| `irregular_note` factual accuracy (jukujikun / rendaku / gemination / ateji) | 47 | 47 correct |
| `irregular_note` naming a word absent from `example_words` | 47 | 0 dangling |
| `notes` (record-level) null everywhere | 280 | consistent |
| pt-BR `meanings` vs `en` sibling and vs KANJIDIC (semantic check, by hand) | 280 | 1 omission (K11), 0 mistranslations |
| `example_words` headword actually contains the record's kanji | 2 193 | 0 violations |
| `example_words` headword / kana / slug vs its vocab record | 2 193 | 0 mismatches |
| `example_words` gloss vs the vocab record's sense-0 gloss | 2 193 | 0 divergences |
| `example_vocab_ids` resolve to a real vocab record | 671 | 0 dangling |
| `readings[].example_vocab` ⊆ `example_words` | 671 | 0 leaks |
| Example vocab attached to a reading whose sound is absent from the word | 671 | 1 (裸足, K2) |
| pt-BR strings: em dash, en dash, pt-PT forms, "Quanto a", "Vale ressaltar", "Por assim dizer", i.e./e.g./lit. | 7 296 | 0 |
| pt-BR gloss left untranslated (identical to `en`) | 2 193 | 0 real cases (動物 "animal", 病院 "hospital" are true cognates) |
| Vulgar / offensive example words | 2 193 | 0 |

Thin `example_words` lists — 駅, 犬, 秋 have 1; 九, 六, 七, 川, 千, 右, 魚, 耳, 町, 銀, 春, 森, 冬, 勉, 菜, 暑
have 2 — are **not** defects: for each, `corpus/vocab/` holds no further word using that kanji.

---

## Counts

| Finding | Severity | Status | Scope |
|---|---|---|---|
| K1 ungrouped example words no `irregular_note` covers | HIGH | **new** | 16 entries, 11 records (9 with no note at all) |
| K2 `irregular_note` contradicts its own reading grouping | MEDIUM | **new** | 6 records; 1 real mis-grouping (裸足) |
| K3 reading note contradicts its own `example_vocab_ids` | MEDIUM | **new** | 2 readings |
| K4 `行けない` — `sK` form + sense JMdict does not have | HIGH | **new** | 1 entry (+1 other `sK`: 番瀝青) |
| K5 `introduced_at_level` unsupported or contradictory | HIGH | confirmed | 343 of 506 determinable rows; 15 records untagged |
| K6 example-word selection level-blind, tiebreak degenerate | HIGH | confirmed (47-record evidence new) | 1 503 of 2 193 entries; 3 records at 0/10 |
| K7 headword is an `is_common: false` written form | HIGH | confirmed | 29 entries, 24 records (17 JMdict `rK`) |
| K8 duplicate `example_words` entry | MEDIUM | confirmed | 2 records |
| K9 nanori block ordered between kun and on | MEDIUM | confirmed | 193 records |
| K10 `common` on readings restates `type`; notes contradict it | MEDIUM | confirmed | 1 124 rows; 6 notes |
| K11 `kanji:屋` pt-BR drops "telhado" | MEDIUM | confirmed | 1 record |
| K12 `meanings.en` mislabelled as raw KANJIDIC | MEDIUM | confirmed | 170 records (1 doc edit) |
| K13 pt-BR and gloss-list micro-defects | LOW | mixed | 6 + 22 + 5 + 1 strings |

| Scope | Count |
|---|---:|
| Records assigned / read in full | 280 / 280 |
| n5 / n4 | 103 / 177 |
| `readings[]` rows checked | 1 812 (kun 698, on 426, nanori 688) |
| `example_words[]` entries checked | 2 193 (1 876 distinct words) |
| pt-BR strings style-checked | 7 296 |
| `irregular_note` texts verified by hand | 47 |
| KANJIDIC2 characters / JMdict entries loaded | 10 384 / 217 425 |
| Vocab records loaded for level, gloss and form cross-check | 7 401 |
| **Findings** | **13 — 5 HIGH, 7 MEDIUM, 1 LOW (4 of them new)** |

**Priority.** K8 is a two-minute exporter fix that frees the slot お茶 needs. K6 and K7 are the same query in
`export_corpus.py:160-163` and should be fixed in one edit, then re-exported; between them they change what 24
records *show* and reorder what 1 503 entries *are*, with no vocab authoring required. K1–K3 are the family a
reviewer will trip on hardest, because the record argues with itself in prose a learner reads: fix the grouping
first, then regenerate `irregular_note` from "which example words ended up ungrouped" so the two fields can no
longer drift apart. K4 is one bad row but it is on 行, an N5 kanji, and it also needs the vocab layer touched.
K12 is a one-line documentation correction and should not be skipped: it is the difference between a reviewer
trusting `meanings.en` blindly and knowing to spot-check it.
