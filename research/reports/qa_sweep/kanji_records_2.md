# QA sweep — kanji records, slice 2

**Assignment:** `corpus/kanji/n3.json` — **350 records**, covering `meanings` (pt-BR + en), `notes`,
`irregular_note`, all **1 867** `readings` rows (including every pt-BR reading `note`), all **2 547**
`example_words` entries, the level-tag block and the graph links.

**Method.** Every record read in full. Cross-checked mechanically against
`research/datasets/jmdict/kanjidic2-en-3.6.2+20260608153333.json.tgz` (10 384 characters), against
`research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip` (217 425 entries, 226 898 written
surfaces) for every furigana pair quoted in authored prose, against
`research/datasets/unihan/Unihan.zip` (`kRSUnicode`) and `research/datasets/kanjialive/ka_data.csv` for the
radical claims, and against `corpus/vocab/{n5,n4,n3,n2,n1}.json` (7 401 records) for level fit, gloss
provenance and written-form commonness. Graph edges resolved against `corpus/sentences/` (5 889) and
`corpus/families/` (396). Producers inspected: `scripts/export/export_corpus.py:115-207`,
`scripts/ingest/unihan_radical.py`, `scripts/fable5_kanji_apply.py`. Contract:
`contracts/kanji.schema.json`, `contracts/common.schema.json`. Style authority:
`design/translation_style.md`. Provenance contract: `CLAUDE.md` §1.1–1.5, `design/i18n.md`.

**Relation to slice 1.** `research/reports/qa_sweep/kanji_records_1.md` covered n5+n4. Where a defect it
found also lives at n3 I re-derived it from my own evidence and marked it `[confirmed]` with n3 numbers;
where n3 makes it materially worse I say so. Six findings are `[new]` — including the two I would fix first.

---

## Headline

The **facts and the authored Japanese are in very good shape.** Against KANJIDIC2 all 350 records match on
`strokes`, `grade`, `freq_rank` and `unicode`, and the kun/on/nanori reading **sets** (okurigana split
points reconstructed) match **exactly in both directions — 0 missing, 0 extra across all 1 867 rows**. Every
one of the **456 `word (furigana)` pairs** quoted in the 1 867 reading notes and 52 `irregular_note` texts
resolves in JMdict; not one Japanese word cited in a note fails to contain the kanji it is filed under; every
rendaku, gemination and vowel-shortening claim I could check by hand holds (発表 はっぴょう, 経済 ざい,
定規 じょうぎ, 平等 びょうどう vs 同等 どうとう, 客観 きゃっかん, 草履 ぞうり, 虫歯 むしば, 突破 とっぱ).
All 52 `irregular_note` texts are factually correct.

**What fails is the metadata around that content.** Two level-tag fields state, in the record's own numbers,
something the record contradicts; the example-word chooser still has no notion of level or of which written
form people use; and one Layer-A field is now AI-authored while three places in the repo still call it
Layer A.

---

## K1 — HIGH — 8 records report unanimous list agreement for a level they are not filed at `[new]`

- **Records:** `kanji:通` `kanji:公` `kanji:正` `kanji:歩` (4/4) · `kanji:的` `kanji:無` `kanji:可` `kanji:身` (1/1)
- **Fields:** `level_agreement`, `level_confidence`

```json
// corpus/kanji/n3.json — kanji:通
{ "level": "n3",
  "level_confidence": 1.0,
  "level_agreement": "4/4",
  "level_sources": { "davidluzgouveia": "n4", "kanjiapi": "n4", "anchori": "n4", "bluskyo": "n4",
                     "anchor": "jlpt_anchor:not-in-n5n4" } }
```

`contracts/common.schema.json` defines both fields against `level`, not against some other level:

> `level_confidence` — "How strongly the consulted lists agree, as a fraction: **1.0 when every list placed
> the item at `level`**, 0.0 when none did."
> `level_agreement` — "**\"4/4\" means all four lists placed the item at this level**"

Here all four lists placed 通 at **n4** and the record is filed **n3**. A reviewer or a UI reading
`4/4 · confidence 1.0` next to `level: n3` concludes four independent lists agreed on n3. None did.
`kanji:的`, `kanji:無`, `kanji:可`, `kanji:身` are the same failure at `"1/1"` — a single source, saying n4,
reported as perfect agreement.

The placements themselves look deliberate and defensible: all eight carry `anchor:
"jlpt_anchor:not-in-n5n4"`, i.e. they were pulled out of the N5/N4 course scope on purpose. The contract
already has the vocabulary for that and it is not being used. From the same file:

> "Two sentinels cover the placements we made ourselves rather than read off a list… `"anchor"` is a
> deliberate course placement… (confidence 1.0, we are certain, there is simply no list to cite)."

**Proposed fix.** For these eight set `level_agreement: "anchor"` and keep `level_confidence: 1.0` (the
sentinel's own definition), and move the list values under `level_sources.correction` — the field
`common.schema.json` documents as "Why a list's placement was overridden" — so the n4 evidence is preserved
as evidence instead of masquerading as agreement. §1.5 of `CLAUDE.md` makes level tags auditable; today
these eight audit false.

**Scope note (outside this slice, same bug).** The identical pattern appears **67 times corpus-wide**: 23 at
n5 (会 社 新 立 手 目 言 多 安 道 口 少 空 足 店 古 買 週 花 駅 飲 魚 耳), 36 at n4 (区 県 村 低 門 森 林 短
軽 池 弱 菜 暑 …), 8 here. Worth one query and one migration, not 67 hand edits.

---

## K2 — HIGH — `introduced_at_level` cannot say "n3", and contradicts the row it sits in `[confirmed, extended]`

- **Rows:** 1 867 · **523** carry example vocab with `introduced_at_level: null` · **35** carry a level with
  no example vocab · **0** say `n3` · **129 records** have the field null on every single reading
- **Records affected:** 291 of 350

Across the **whole** kanji corpus (2 131 records, 8 340 reading rows) `introduced_at_level` only ever takes
`"n5"`, `"n4"` or `null`. It was derived once from the N5/N4 vocabulary and never re-derived when the n3/n2/n1
banks landed, so in an n3 file it is structurally incapable of describing the level the file is about.

Worse, within a record it points the wrong way. `kanji:表`:

```
reading      okurigana  introduced_at_level  example_vocab
おもて        —          "n4"                 表 (n4)
-おもて       —          "n4"                 (none)
あらわ        す          null                表す (n3)
ヒョウ        —          null                表現 発表 表情 表面 代表 表 (all n3) + 時刻表 表紙
```

The on-reading that carries eight compounds, six of them n3, is `null`; the hyphen variant with zero
compounds is tagged. `kanji:付` is the same shape: `-つき`, `-つ.け`, `-づ.け` (zero examples each) are all
`"n4"`, while `つ.ける` — whose example is 付ける — is `null`.

**Consequence.** Any "which readings does this level introduce?" query returns nothing for 129 of these 350
kanji, and for the rest returns the rows with the least evidence.

**Proposed fix.** Re-derive the field from `example_vocab` in the same pass that groups it:
`introduced_at_level = min(level of the vocab in example_vocab)`, floored at the kanji's own `level`; leave
`null` only where `example_vocab` is genuinely empty. That inverts the current situation with no new data.
(Slice 1 filed this as K4 on 44 n5/n4 records; the n3 slice shows the cause is not 44 bad rows but a
level-capped derivation.)

---

## K3 — HIGH — 58 example words teach a written form the corpus itself marks `is_common: false` `[confirmed]`

- **Records:** 35 · **Entries:** 58 · **11 of them sit in slot 0**, the first word the learner sees
- **Field:** `example_words[].headword`

The vocab record stores each surface with an `is_common` flag. For 58 entries the `headword` rendered is the
form flagged `is_common: false` while the common form is the kana one. `kanji:彼` is the worst — six of its
ten example words are ateji nobody writes, and the very first one displaces the word that actually matters:

```json
// corpus/kanji/n3.json — kanji:彼, example_words[0] and [1]
{ "headword": "彼", "kana": "あれ", "slug": "vocab:1000580", "gloss": {"pt-BR": ["aquela pessoa", …]} },
{ "headword": "彼", "kana": "かれ", "slug": "vocab:1483070", "gloss": {"pt-BR": ["ele"]} }
```

```json
// corpus/vocab/n5.json — vocab:1000580.forms
[ {"form":"彼","is_kana":false,"is_common":false,"is_primary":true},
  {"form":"彼れ","is_kana":false,"is_common":false,"is_primary":false},
  {"form":"あれ","is_kana":true,"is_common":true,"is_primary":false}, … ]
```

So slot 0 of 彼 renders 彼/あれ, a form the record beside it calls uncommon, ahead of 彼/かれ. Then 彼処/あそこ,
彼方/あちら, 彼是/あれこれ, 彼方此方/あちこち follow. Other clusters: `kanji:処` (何処か 其処で 彼処 此処),
`kanji:若` (若し 若しかして 若しかしたら 若しかすると), `kanji:舞` (仕舞う 仕舞った お仕舞い 振舞う).
Slot-0 offenders: 米 加 利 可 積 処 彼 舞 許 居 御.

This also produces the one apparent duplicate in the file: `kanji:位` shows "位 くらい" twice (vocab:1154340
"cerca de" and vocab:1155400 "posição"). They are genuinely different words, but the first only reaches the
list because 位 is accepted as a written form of the adverb くらい, which its own record marks
`is_common: false`.

**Proposed fix.** In `export_corpus.py:160-163`, prefer the `is_common` form: join `vocab_form` and select
the primary common surface; where the only common surface is kana, render the kana (or drop the word if the
kanji is not actually written).

---

## K4 — HIGH — example-word selection is level-blind; 53 % of the words shown are n1/n2 `[confirmed]`

- **Entries:** 1 345 of 2 547 above the record's level (n1 860, n2 485) · **Records affected:** 329 of 350
- **Producer:** `scripts/export/export_corpus.py:160-163`

```sql
SELECT v.headword,v.kana,v.id,v.slug FROM vocab_kanji vk JOIN vocab v ON v.id=vk.vocab_id
WHERE vk.kanji_id=? ORDER BY v.common DESC, v.freq_rank IS NULL, v.freq_rank LIMIT 10
```

No level term. Thirty records hit the `LIMIT 10` cap **while in-level words exist and are excluded** — 48
words hidden in total:

| record | shown (level) | hidden |
|---|---|---|
| `kanji:原` | 原因 n4, 原稿 n2, 原則 n1, 原文 n1, 原子 n1, 原料 n2, 原書 n1, 原作 n1, 原爆 n1, 原理 n2 | 原 (はら) n3 |
| `kanji:点` | 観点 n1, 利点 n1, 満点 n2, 点数 n2, 弱点 n2, 地点 n2 … | 点ける (つける) **n5**, 点く **n4** |
| `kanji:当` | 当て n1, 当てはまる n2, 当たり前 n2 … | お弁当 **n5**, 適当 n4, 担当 n3 |
| `kanji:直` | 直面 n1, 率直 n2, 仲直り n2, 素直 n2 … | 真っ直ぐ **n5**, 直る n4, 直 n3 |
| `kanji:交` | 交渉 n1, 交わす n1, 交代 n2, 交互 n1, 交流 n2 … | 交番 **n5**, 外交 n3 |

`kanji:浮` is the extreme: **all four** of its example words are n1/n2 (浮かぶ, 浮かべる, 浮気, 浮く), so a
learner meeting 浮 at n3 is shown nothing at or below their level.

**Proposed fix.** Add a level term to the ORDER BY — `ORDER BY (level_rank(v.level) > level_rank(?)),
v.common DESC, v.freq_rank …` — so in-level words fill the ten slots first and harder compounds fill the
remainder. Same edit site as K3; do them together and re-export once.

---

## K5 — MEDIUM — the radical is wrong on two records, and one of them contradicts its own `components` `[new]`

- **Records:** `kanji:最`, `kanji:変` · **Fields:** `kangxi_radical`, `radical_char`

```json
{ "slug": "kanji:最", "kangxi_radical": 13, "radical_char": "冂",
  "components": ["一", "又", "日", "耳"], "strokes": 12 }
{ "slug": "kanji:変", "kangxi_radical": 35, "radical_char": "夊",
  "components": ["亠", "夂"], "strokes": 9 }
```

Every other source in this repo disagrees:

| record | stored | KANJIDIC2 classical | KANJIDIC2 nelson_c | kanjialive `radical` |
|---|---|---|---|---|
| 最 | 13 (冂) | 73 (曰) | 72 (日) | ⽇ = 72 (日, "ひ") |
| 変 | 35 (夊) | 34 (夂) | 8 | ⼡ = 34 (夂, "のまた") |

For 最 the stored radical 冂 does not appear in the record's own `components` and is not a plausible lookup
head under any standard — a learner told to find 最 under 冂 will not find it. For 変 the stored character
夊 (U+590A) and the component 夂 (U+5902) are **two different characters** sitting in the same record.

**Root cause.** `scripts/ingest/unihan_radical.py:33` reads `RS_RE.match(val.split()[0])` — the *first* of
Unihan's possibly-many `kRSUnicode` analyses. For 最 the field is `"13.10 73.8"`: the pipeline takes the
Unicode radical-stroke sort-order analysis and drops the traditional one. 変 is single-valued in Unihan
(`"35.6"`) and simply disagrees with both other sources here.

The Unihan choice is deliberate and documented (license audit D-LIC-2, avoiding CC BY-SA KRADFILE) — so the
fix is not "go back to KANJIDIC" but "pick the right value from Unihan and reconcile the outliers".

**Proposed fix.** Where `kRSUnicode` has multiple values, prefer the one that is consistent with the record's
own `components` (or with KANJIDIC's `classical`, used as a cross-check rather than as the stored source),
falling back to `[0]`. That resolves 最 to 73/曰. Then hand-review the residue: across all five levels only
**12** records diverge from KANJIDIC classical (最 変 章 蒸 視 舎 巡 曽 黙 舗 粛 墨), so this is a 12-row
reconciliation, not a re-ingest.

---

## K6 — MEDIUM — `readings[].common` restates `type`, and 47 rows contradict their own note `[confirmed]`

- **Rows:** 1 867 — kun 904 all `true`, on 486 all `true`, nanori 477 all `false`. Zero exceptions.

```python
# scripts/export/export_corpus.py:141
"common": r[1] != "nanori",
```

The field carries no information a consumer cannot get from `type`, so a UI that de-emphasises
`common: false` de-emphasises exactly the nanori block and nothing else. Meanwhile **47 rows** are marked
`common: true` while the pt-BR note in the same object calls the reading rare:

```json
// kanji:関, readings[]
{ "reading": "からくり", "type": "kun", "common": true,
  "note": {"pt-BR": "Leitura nativa からくり, rara. Nenhum composto desta entrada a usa."} }
```

Others: 政/まん, 内/ダイ, 回/もとお, 回/か, 回/エ, 選/え, 選/よ, 米/よね, 実/みち, 実/シツ, 関/かんぬき,
戦/おのの, 戦/そよ, 戦/わなな, 経/たていと, 経/はか, 経/のり, 経/キン, 通/ツ …

**Proposed fix.** Either derive `common` from real evidence (`example_vocab` non-empty, or KANJIDIC group
membership) so it means something, or drop it from the export and let consumers read `type`. The current
value is worse than either: it looks like an independent judgement and is not one.

---

## K7 — MEDIUM — `kanji:雪` teaches ぶき in prose while filing it as an untaught name reading `[new]`

- **Record:** `kanji:雪` · **Fields:** `readings[].type`, `readings[].note`, `irregular_note`

```json
{ "reading": "ぶき", "type": "nanori", "common": false,
  "example_vocab": [],
  "note": {"pt-BR": "Leitura secundária registrada para este kanji, fora do padrão ゆき.
                     Nenhum vocábulo desta entrada ficou agrupado nela."} }
```

```json
"irregular_note": {"pt-BR": "吹雪 e 雪崩 não saem de ゆき nem de セツ. … já 吹雪 usa a leitura ぶき,
                             que está listada nesta mesma entrada."}
```

```json
"example_words": [ …, {"headword": "吹雪", "kana": "ふぶき", "slug": "vocab:1370780", …}, … ]
```

Three fields of one record disagree. `contracts/kanji.schema.json` states of the `type` enum: "`nanori`
readings are **name-only and are not taught**". The `irregular_note` teaches this one, pointing the learner
at a row whose own note says no word here uses it — while 吹雪 sits four fields down in `example_words`.
ふぶき is not a name reading at all: it is 吹く + 雪 with rendaku, an ordinary N3 word.

Corroborating detail: this is the **only one of the 477 nanori notes in the file** that never says "nanori"
or "nome próprio". Whoever wrote it knew it was not a name reading and worked around the classification.

**Proposed fix.** Either re-type ぶき as `kun` (KANJIDIC files it under nanori, so this is an editorial
override and should carry a note saying so), or leave the type and rewrite the `irregular_note` to stop
citing it — "吹雪 (ふぶき) sonoriza ゆき em ぶき depois de 吹" — and link 吹雪 into `example_vocab` for
whichever row ends up owning it.

---

## K8 — MEDIUM — `meanings.en` is AI-authored, and three places still call it Layer A `[confirmed, extended]`

- **Records:** **340 of 350** diverge from KANJIDIC2's English meaning list (slice 1: 170 of 280)

```
kanji:回  en = ["turn", "rotate", "times (count)"]
          KANJIDIC2 = ["-times", "round", "game", "revolve", "counter for occurrences"]
kanji:部  en = ["part", "section", "department"]
          KANJIDIC2 = ["section", "bureau", "dept", "class", "copy", "part", "portion", …]
```

Three committed places assert the opposite:

- `contracts/kanji.schema.json:5` — "One kanji character: readings, meanings, radical decomposition and the
  level it is taught at. **Layer A apart from the pt-BR meanings.**"
- `design/i18n.md` — "the `en` key already preserves the authoritative English source wherever one exists:
  kanji **meanings** → `en` from KANJIDIC"
- `scripts/ingest/migrations/001_init.sql:23` — `meanings_en TEXT, -- JSON [] (Layer A cross-check)`

`scripts/fable5_kanji_apply.py:35` overwrites `kanji.meanings_en` from an AI review patch. The rewrites are
mostly *improvements* — the trimmed 回/部 lists are better teaching English than KANJIDIC's — so the defect
is not the content, it is the label. Under `CLAUDE.md` §1.1/§1.3 a reviewer is told to trust A blindly and
audit C selectively; today `meanings.en` is in the "trust blindly" bucket and should not be.

**Proposed fix.** One doc edit and one schema edit: change the contract description to "Layer A apart from
`meanings` (both locales, AI-authored from the KANJIDIC list and human-reviewable)", correct the i18n.md
bullet, and fix the SQL comment. Optionally keep the untouched KANJIDIC list in a `meanings_source_en`
column so the cross-check the comment promises actually exists.

---

## K9 — MEDIUM — the nanori block sits between kun and on in 180 of 350 records `[confirmed]`

```python
# scripts/export/export_corpus.py:151
"FROM kanji_reading kr WHERE kr.kanji_id=? ORDER BY kr.reading_type"
```

Alphabetical on the enum: `kun` < `nanori` < `on`. So on 180 records the untaught name readings are rendered
between the two taught blocks. `kanji:和` is the extreme — 25 rows, 17 of them nanori, all of them ahead of
the on readings a learner is there for. `kanji:政` shows it in miniature: まつりごと, まん, **ただ, まさ**,
セイ, ショウ.

**Proposed fix.** `ORDER BY CASE kr.reading_type WHEN 'kun' THEN 0 WHEN 'on' THEN 1 ELSE 2 END, kr.id`.

---

## K10 — LOW — 87 reading notes start with a lowercase letter `[new]`

- **Records:** 16 · on **12** of them *every* note is affected

```json
// kanji:深, readings[0]
{ "reading": "ふか", "okurigana": "い", "introduced_at_level": "n4",
  "note": {"pt-BR": "leitura nativa; com o okurigana い ela forma o adjetivo 深い (ふかい), fundo, profundo."} }
```

| record | lowercase / total |
|---|---|
| 抜 押 暮 更 杯 歩 深 申 破 貧 敗 存 | 10/10, 9/9, 6/6, 5/5, 2/2, 8/8, 6/6, 4/4, 4/4, 3/3, 2/2, 8/8 |
| 払 苦 晴 列 | 6/7, 6/7, 6/8, 2/3 |

The other 1 780 notes in the file are sentence-cased, so this is an authoring-batch artifact, not a
convention. The 12 all-lowercase records make the boundary obvious.

**Proposed fix.** Uppercase the first character of `localized_text` where
`entity_type='kanji_reading' AND field='note'` and the value starts lowercase — the affected strings all
begin with a plain word (`leitura`, `variante`, `mesma`, `a mesma`), so there is no risk of capitalising a
kana or a `-` prefix.

---

## K11 — LOW — `kanji:共` `-ども` says it has no words while holding one `[new]`

```json
{ "reading": "-ども", "type": "kun", "common": true,
  "example_vocab_ids": [6355], "example_vocab": ["vocab:1234250"],
  "note": {"pt-BR": "Variante sonorizada usada como sufixo, presa ao fim de outra palavra
                     (é o que o hífen marca). Nenhuma palavra ficou listada neste grupo."} }
```

`vocab:1234250` is 共 (ども), the pluralising suffix — exactly what the note describes and then denies. This
is the **only** contradiction of its kind in 1 867 rows (I checked every note carrying a negation against its
`example_vocab`), so it is a single stale sentence, presumably written before the grouping pass linked the
word.

**Proposed fix.** Replace the last sentence with the example it already has: "…(é o que o hífen marca), como
em 共 (ども), o sufixo que forma plurais."

---

## K12 — LOW — three pt-BR meaning items that a Brazilian beginner will read wrong `[new]`

```json
"kanji:危" → {"pt-BR": ["perigoso", "arriscado", "periculoso"], "en": ["dangerous", "risky", "perilous"]}
"kanji:米" → {"pt-BR": ["arroz", "América", "metro"],           "en": ["rice", "America", "meter"]}
"kanji:性" → {"pt-BR": ["natureza", "sexo", "qualidade", "caráter"],
              "en":    ["nature", "gender", "quality", "-ness"]}
```

- **危 "periculoso"** — not current pt-BR. Brazilians have "periculosidade" (the noun, mostly legal/labour
  register) but the adjective is "perigoso", which is already slot 0. Slot 2 is therefore both archaic and
  redundant. Fix: `["perigoso", "arriscado", "ameaçador"]`, or drop the third item.
- **米 "América"** — 米 abbreviates 亜米利加 and means **the United States** (米国, 日米, 米ドル). To a
  Brazilian reader "América" is the continent they live on, so this teaches the wrong referent. KANJIDIC
  itself says "USA"; the AI-authored `en` loosened it to "America" and the pt-BR followed. Fix:
  `["arroz", "Estados Unidos", "metro"]`.
- **性 "caráter"** — the `en` slot is the suffix `-ness`, and this file has a clear convention for suffixes:
  `kanji:的` → `"-ico (sufixo adjetival)"`, `kanji:化` → `"-ização"`, `kanji:達` → `"sufixo de plural"`.
  性 breaks it, and the suffix is the use a learner meets first (可能性, 安全性, 重要性). Fix:
  `"-idade (sufixo)"`.

---

## K13 — LOW — two `irregular_note` texts that do not stand on their own `[new]`

**`kanji:葉` opens with a dangling reference.**

```json
"irregular_note": {"pt-BR": "O mesmo 紅葉 também se lê もみじ. Nessa leitura o par de kanji vale como uma
                             palavra inteira e não se divide entre os dois caracteres."}
```

"O mesmo 紅葉" has no antecedent inside the field. 紅葉/こうよう is mentioned in `example_words[2]` and in the
ヨウ reading note, but `irregular_note` is a separate field that a UI will render on its own. The other 51
irregular notes all name their subject in the first clause; this is the only one that points outside itself.
Fix: "紅葉 (こうよう, folhagem de outono) tem uma segunda leitura, もみじ; nela o par de kanji vale como uma
palavra inteira…"

**`kanji:歳` uses the fullwidth-numeral form in prose.**

```json
"irregular_note": {"pt-BR": "２０歳 (はたち) não usa nenhuma das leituras acima; é uma forma fixa para vinte
                             anos de idade."}
"example_words": [ …, {"headword": "２０歳", "kana": "はたち", "slug": "vocab:1600790", …} ]
```

`vocab:1600790.forms` marks `２０歳` `is_common: false` and `二十歳` `is_common: true`. The example word is a
K3 instance and a K3 fix will repair it, but the **prose** carries the same form independently and will
survive that fix. Fix: write 二十歳 in both places.

---

## What I checked and found clean

| Check | Rows | Result |
|---|---:|---|
| `strokes` / `grade` / `freq_rank` / `unicode` / `kanjivg_ref` vs KANJIDIC2 | 350 each | 0 mismatches |
| kun/on/nanori reading **sets** vs KANJIDIC2, okurigana reconstructed, both directions | 1 867 | 0 missing, 0 extra |
| Reading `type` filed correctly (on in katakana, kun in hiragana) | 1 867 | 0 errors |
| Duplicate `(type, reading, okurigana)` within a record | 1 867 | 0 |
| Reading types contiguous within the array (no interleaving) | 350 | 0 split blocks |
| `common: false` on every nanori; no nanori carries `example_vocab` | 477 | 0 violations |
| Reading `note` present, non-empty, pt-BR, terminally punctuated | 1 867 | 0 missing |
| **Every `word (furigana)` pair quoted in a note or irregular_note, vs JMdict** | **456** | **0 wrong** |
| Every Japanese word cited in a note actually contains the record's kanji | 1 867 notes | 0 violations |
| "abre / fecha / no meio" position claims in notes | 701 word-mentions | 0 wrong (50 flagged, all my clause-splitter) |
| Rendaku / gemination / vowel-shortening claims spot-checked by hand | 45 of 124 | 45 correct |
| `irregular_note` factual accuracy (jukujikun / rendaku / gemination / ateji) | 52 | 52 correct |
| Note claiming "no examples" vs a non-empty `example_vocab` | 1 867 | 1 (K11) |
| `notes` field null on every record | 350 | consistent with the contract's own description |
| `example_words` headword actually contains the kanji | 2 547 | 0 violations |
| `example_words` headword / kana / `vocab_id` / `slug` vs its vocab record | 2 547 | 0 mismatches |
| `example_words` gloss vs the vocab record's sense-0 gloss, both locales | 2 547 | 0 divergences |
| `example_words` empty gloss, duplicate gloss entries | 2 547 | 0 |
| `example_vocab_ids` ↔ `example_vocab` slugs, same length, same records | 1 867 rows | 0 dangling, 0 mismatched |
| `example_sentences` resolve, and each sentence contains the kanji | 1 498 | 0 dangling, 0 wrong |
| `families` backlinks resolve | 18 | 0 dangling |
| `meanings` duplicate pt-BR entries, empty lists, over-long items | 350 | 0 |
| `en` gloss unsplit on `;` (slice-1 K9) | 350 | 0 — not present at n3 |
| pt-BR text: em dash / en dash | 9 027 units | 0 |
| pt-BR text: "Quanto a", "Vale ressaltar/destacar", "Por assim dizer" | 9 027 units | 0 |
| pt-BR text: pt-PT lexis and orthography, `vós`/`está a fazer` | 9 027 units | 0 |
| pt-BR text: English/latin abbreviations (e.g., i.e., cf., lit.) | 1 867 notes | 0 |
| pt-BR text: double/edge whitespace | 1 867 notes | 0 |
| pt-BR meaning identical to its `en` counterpart | 350 | 13 found, all true cognates (crime, normal, volume, item…) — not defects |

**Not defects, for the record.** (a) `radical_char` differs from every listed `component` on 127 records —
that is KRADFILE's variant glyphs (汁 for 氵, 込 for 辶, 攵 for 攴, 扎 for 扌, 忙 for 忄, 阡 for 阝) against
Unihan's canonical Kangxi form; only 最 and 変 (K5) are wrong *values*. (b) 123 readings carry KANJIDIC's
`-` prefix/suffix marker inside `reading` (`-まわ`, `ふな-`); the note explains the direction correctly in
every case I checked, so this is undocumented but not incorrect — worth a line in
`contracts/kanji.schema.json` if the field is ever used as a lookup key. (c) `kanji:米` and `kanji:港` carry
`level_agreement: "0"` with `level_confidence: 0.0` and a prose reason under `level_sources.lists`: that is
the contract's documented author-added sentinel, used correctly. (d) 39 records have no
`example_sentences` and 342 have no `families` — thin, but the corpus layer has nothing to link.

---

## Counts

| Finding | Severity | Status | Records | Rows/entries |
|---|---|---|---:|---:|
| K1 unanimous agreement reported for a level the record is not filed at | HIGH | **new** | 8 | 8 |
| K2 `introduced_at_level` cannot say n3; contradicts its own row | HIGH | confirmed, extended | 291 | 558 of 1 867 |
| K3 example word teaches an `is_common: false` written form | HIGH | confirmed | 35 | 58 of 2 547 |
| K4 example-word selection level-blind; 30 records hide in-level words | HIGH | confirmed | 329 | 1 345 of 2 547 |
| K5 radical wrong; one contradicts its own `components` | MEDIUM | **new** | 2 | 2 |
| K6 `common` restates `type`; 47 rows contradict their own note | MEDIUM | confirmed | 350 | 1 867 (47 explicit) |
| K7 `kanji:雪` teaches a `nanori` the contract says is not taught | MEDIUM | **new** | 1 | 1 |
| K8 `meanings.en` AI-authored but labelled Layer A in 3 places | MEDIUM | confirmed, extended | 340 | 3 doc/schema edits |
| K9 nanori block ordered between kun and on | MEDIUM | confirmed | 180 | — |
| K10 reading notes starting with a lowercase letter | LOW | **new** | 16 | 87 of 1 867 |
| K11 `kanji:共` `-ども` note denies the example it holds | LOW | **new** | 1 | 1 |
| K12 pt-BR meaning items that mislead (危, 米, 性) | LOW | **new** | 3 | 3 |
| K13 `irregular_note` prose: dangling anaphor (葉), fullwidth form (歳) | LOW | **new** | 2 | 2 |

| Scope | Count |
|---|---:|
| Records assigned / read in full | 350 / 350 |
| `readings[]` rows checked | 1 867 |
| pt-BR reading `note` texts read | 1 867 (1 428 distinct) |
| `example_words[]` entries checked | 2 547 |
| `irregular_note` texts verified by hand | 52 |
| `word (furigana)` pairs verified against JMdict | 456 |
| pt-BR text units style-scanned | 9 027 |
| Vocab records loaded for level / gloss / form cross-check | 7 401 |
| KANJIDIC2 characters / JMdict entries loaded | 10 384 / 217 425 |
| **Findings** | **13 (4 HIGH, 5 MEDIUM, 4 LOW)** |

**Priority.** K3 and K4 are the same `SELECT` in `export_corpus.py:160-163`; fix both, re-export once, and
2 547 example words are re-chosen with no new data. K1 is eight rows plus a migration that also cleans 59
records outside this slice, and it is the finding most likely to mislead a human reviewer, because the
numbers look authoritative. K2 is a derivation the corpus already has the inputs for. K5 is twelve rows
corpus-wide. K8 is three lines of documentation and should not be skipped: it is the difference between a
reviewer trusting `meanings.en` blindly and knowing to spot-check it. K7 and K11 are single records but both
are the record contradicting itself in adjacent fields, which is the class of defect a machine validator
should be catching.
