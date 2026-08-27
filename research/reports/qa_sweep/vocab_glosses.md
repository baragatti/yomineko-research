# QA sweep — `corpus/vocab/n5.json` + `n4.json` (senses, glosses, register, kana/romaji, forms)

**Scope:** 1,358 records / 1,947 senses / 3,737 en+pt-BR gloss strings. Read in full, record by record.
**Method:** every record read against its own `en` gloss; then cross-checked mechanically against three
independent references already in the repo —
`research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip` (all 1,358 `jmdict_ref`s resolved),
the JMdict "common" subset, and the four consensus lists in `research/datasets/jlpt/`
(`openanki_vocab_*.csv` and `jlptvocabapi_*.json` carry an English meaning per entry, so the list's own
intended meaning can be compared against the meaning the corpus ended up with).
**Out of scope per instructions:** sentence `structure_explanation`.
**Style authority:** `design/translation_style.md`.

Findings are ordered by severity. Each one is reproducible from the files named above.

---

## F1 — CRITICAL: ~21 records resolved a kana reading to the *wrong word*; ~13 core N5/N4 words are missing as a result

The source lists are kana-keyed for function words and common verbs (`openanki_vocab_n5.csv` row
`はい,はい,"yes"`). The ingest picked a JMdict entry by **reading alone** and ignored the meaning the list
supplied in the very same row. The result is a vocabulary list that teaches the wrong word under the right
reading, and silently omits the intended one.

Detection: for every record sourced from `openanki`/`jlptvocabapi`, compare the list's `meaning` field with
the record's `en` gloss. 34 records share no content word; hand-triage removes synonym artefacts
(`不便` "inconvenient" vs "inconvenience", `手袋` "gloves" vs "glove") and leaves the table below.
The `bluskyo` cases (kana-only, no meaning column) were confirmed by hand.

| id | level | corpus headword / gloss | what the source list actually meant | collateral damage |
|---|---|---|---|---|
| 502 | n5 | 肺 はい — `"pulmão", "pulmões"` | `openanki`+`api`: **"yes"** | はい "sim" absent from the entire corpus |
| 434 | n5 | 動 どう — `"movimento"` | `openanki`+`api`: **"how, in what way"** | どう absent (どうですか is a week-1 pattern) |
| 479 | n5 | 生る なる — `"dar fruto", "frutificar"` | `openanki`+`api`: **"to become"** | 成る/なる absent; `grep "tornar-se" corpus/vocab/*.json` → 0 hits |
| 334 | n5 | 刷る する — `"imprimir"` | `openanki`: **"to do, to try"** | する at N5 absent; it surfaces only at N4 as 為る (id 1358) |
| 148 | n5 | 罹る かかる — `"pegar (uma doença)"` | `openanki`: **"it takes (amount of time, money)"** | 掛かる (jmdict 1207590) absent from N5+N4 |
| 154 | n5 | 翔る かける — `"voar (pelo céu)", "planar"` | `openanki`: **"to dial/call; to sit down; to put on (glasses)"** | duplicate of id 153 掛ける, which is already present |
| 507 | n5 | 伯 はく — `"conde"` | `openanki`+`api`: **"to put on (items below your waist)"** | 履く/穿く absent |
| 376 | n5 | 盾 たて — `"escudo"` | `openanki`+`api`: **"length, height"** | 縦 absent |
| 355 | n5 | 園 その — `"jardim", "parque"` | `openanki`: **"that"** | the demonstrative その is absent while この (257) and あの (31) are present |
| 1347 | n5 | 報 ほう — `"relatório", "notícia"` | `bluskyo` n5 lists ほう immediately beside より | 方 (ほう) absent, so 〜のほうが〜より cannot be built |
| 349 | n5 | 総 そう — `"total", "geral (prefixo)"` | `openanki`: **"really, (is that) so; yes, right"** | そう absent |
| 1343 | n5 | 本島 ほんとう — `"ilha principal"` | `api`: **"truth"**; `openanki` lists 本当 | duplicate of id 593 本当 |
| 374 | n5 | 立ち たち — `"partida", "saída"` | list entry is bare kana たち | 達 (私たち) absent |
| 503 | n5 | 杯 さかずき — `"cálice de saquê"` | list entry 杯 is the counter **はい** | the counter 杯 absent |
| 1086 | n4 | 侯 こう — `"marquês", "senhor feudal"` | `openanki`+`api`: **"like this, this way"** | こう absent |
| 699 | n4 | 等々 とうとう — `"e assim por diante", "etc."` | `openanki`+`api`: **"finally, at last"** | 到頭 absent |
| 1223 | n4 | 滑降 かっこう — `"descida (esqui)"` | `api`: **"appearance"**; `openanki` lists 格好 | duplicate of id 1334 格好 |
| 1350 | n4 | 琴 こと — `"koto", "cítara japonesa"` | `openanki` lists 事: **"thing(s), matter(s)"** | duplicate of id 887 事 |
| 1359 | n4 | 献花 けんか — `"oferenda de flores"` | `bluskyo` lists bare kana けんか | 喧嘩 absent |
| 842 | n4 | 県下 けんか — `"na província"` | same けんか slot, resolved a second wrong way | — |
| 745 | n4 | 運 うん — `"sorte", "fortuna"` | `openanki`+`api`: **"yes (informal), all right"** | うん absent (運 itself is defensible vocabulary; the list slot was うん) |

Lower confidence, same pattern: **94** `尾 お "cauda"` (2/4 agreement; the standalone お in a beginner list is
the honorific prefix, and 御/ご is already carried at N4 as id 1202).

Note that `level_agreement` is **4/4 with `level_confidence: 1.0`** on 502, 434, 479, 334, 148, 154, 507, 376,
355, 1086 and 699. The consensus machinery worked: four lists agreed on the *reading*. The failure is
entirely in reading→lemma resolution, so the confidence field is actively misleading here.

**Fix:** re-run lemma resolution scoring JMdict candidates against the list's own `meaning` string (gloss
token overlap), not the reading alone; where a list row carries a written form (`openanki.expression`,
`bluskyo.Kanji`), require the chosen entry to contain that form. Then re-import the ~13 missing headwords.
Until that runs, these 21 records should not reach a learner.

---

## F2 — CRITICAL: あれ is glossed as "aquela pessoa"; the こ／そ／あ set is broken at the あ row

`corpus/vocab/n5.json`, id 41, its only sense:

```
en: "that person (distant from both speaker and listener)", "that"
pt: "aquela pessoa", "aquele (pessoa distante de ambos)"
```

JMdict 1000580 orders the senses `[0] "that, that thing"` → `[1] "that person"`. The corpus dropped sense 0,
promoted sense 1, and then let the parenthetical "(pessoa distante de ambos)" force the person reading onto
the second gloss too — so **no gloss anywhere in the record means "aquilo"**. Its siblings are correct and
make the break obvious:

- id 261 これ → `"isto", "este"`
- id 358 それ → `"isso", "esse"`
- id 41 あれ → `"aquela pessoa", "aquele (pessoa distante de ambos)"`

A learner drilling これ/それ/あれ is taught that あれ refers to a person. **Fix:** restore JMdict sense 0 as
`s0` (`pt: "aquilo", "aquele (ali)"`) and demote the person reading to `s1` (`pt: "aquela pessoa (ali)"`).

---

## F3 — HIGH: 156 records show a kanji headword for entries JMdict marks "usually written in kana"; on 63 of them the headword is a *rare or search-only* spelling

`headword`/`is_primary` was set from JMdict's first kanji form without consulting `misc: uk` or the form's own
tags. Counting only records where JMdict tags **sense 0** `uk` and the corpus headword is kanji: **156**.
Of those, the chosen primary form carries a JMdict rarity tag (`rK` 45, `sK` 5, `ateji+rK` 9, `ok`/`iK`/`io`) on
**63** records:

```
咖哩 (カレー)   珈琲 (コーヒー)   為る (する)      亜米利加 (アメリカ)   阿弗利加 (アフリカ)
燐寸 (マッチ)   洋杯 (コップ)     洋袴 (ズボン)     釦 (ボタン)          硝子 (ガラス)
瓦斯 (ガス)     塵 (ゴミ)         米 (メートル)     瓩 (キログラム)      粁 (キロメートル)
一寸 (ちょっと) 屹度 (きっと)     迚も (とても)     然し (しかし)        吃驚 (びっくり)
此れ (これ)     其れ (それ)       彼処 (あそこ)     御座います (ございます) 為さる (なさる)
```

Plus, from the wider `uk` set: 貴方 (あなた), 下さい (ください), 出来る (できる), 丁度 (ちょうど),
何時 (いつ), 殆ど (ほとんど), 沢山 (たくさん), 美味しい (おいしい), 分かる (わかる), 有る (ある).

`corpus/vocab/INDEX.md` and every downstream flashcard/lesson reference addresses these by `headword`, so an
N5 learner's first exposure to "curry" is 咖哩. **Fix:** when JMdict's sense 0 is `uk`, or when every kanji
form is tagged `rK`/`sK`/`ateji`/`oK`, set `headword` and `is_primary` to the common kana form; keep the kanji
in `forms` (tagged, see F6) as reference-only.

---

## F4 — HIGH: JMdict `misc` tags are dropped almost entirely, against the field's own contract

`contracts/vocab.schema.json` defines `senses[].misc` as *"JMdict misc tags for this sense, verbatim (`uk`,
`hum`, `col`, …)"*. Actual state: **1 of 1,947 senses** carries a `misc` value (id 989 居る/おる, `["hum"]`).
Tags JMdict supplies for these same 1,358 entries and the corpus discards:

| tag | records | tag | records | tag | records |
|---|---|---|---|---|---|
| `uk` | 200 | `abbr` | 63 | `col` | 51 |
| `arch` | 44 | `hon` | 27 | `pol` | 16 |
| `hum` | 15 | `sl` | 12 | `fam` | 10 |
| `on-mim` | 9 | `dated` | 9 | `hist` | 6 |

The field is not "sparsely populated", it is empty — which is why F3 and F5 exist at all: the downstream
consumers of `uk`/`hon`/`pol` had nothing to read. **Fix:** carry `misc` verbatim in the exporter, then
re-derive `headword` (F3) and `register` (F5) from it.

---

## F5 — HIGH: `register` is null on 51 of the 52 keigo records, though `design/translation_style.md` §2 depends on it

`design/translation_style.md` §2: *"Use the vocab/grammar `register` enum (colloquial/slang/vulgar/honorific/
humble/polite…) to gauge tone"*. JMdict tags 52 of these records `hon`, `hum` or `pol`. Exactly one
(id 989 居る/おる) carries `register: ["humble"]`. The other 51 are `register: null` — including every verb
whose own pt gloss already says so in prose:

```
796  致す いたす      pt "fazer (humilde)"                     register: null   (JMdict hum)
921  頂く いただく    pt "receber (humilde)"                   register: null   (JMdict hum, pol)
714  伺う うかがう    pt "visitar (humilde)"                   register: null   (JMdict hum)
1234 仰る おっしゃる  pt "dizer (honorífico)"                  register: null   (JMdict hon)
759  いらっしゃる     pt "estar/ir/vir (forma honorífica)"     register: null   (JMdict hon)
1196 召し上がる       pt "comer (forma respeitosa)"            register: null   (JMdict hon)
735  ございます       pt "há | existe (forma polida)"          register: null   (JMdict pol)
1020 差し上げる       pt "dar (humilde, a um superior)"        register: null   (JMdict hum)
990  申す もうす      pt "dizer (humilde)"                     register: null   (JMdict hum)
886  為さる なさる    pt "fazer (forma honorífica ... de する)" register: null   (JMdict hon)
```

The politeness level is therefore encoded only inside free pt-BR prose — unqueryable, and invisible to any
UI or exercise generator that filters on `register`. Also affected: 先生, 奥さん, お母さん, お父さん,
お兄さん, お姉さん, 皆さん, どなた, 母, 父 (`hum`), 様, 御, ご存知, ご覧になる, 下さる, 参る, 拝見, 宜しい,
家内, 申し上げる.

**Fix:** map JMdict `hon`→`honorific`, `hum`→`humble`, `pol`→`polite`, `col`→`colloquial`, `sl`→`slang`,
`vulg`→`vulgar`, `fam`→`familiar`, `arch`→`archaic` at both record and sense level. The mapping is
mechanical and the enum already exists in `contracts/vocab.schema.json`.

---

## F6 — MEDIUM: `forms` lists carry 485 search-only spellings that JMdict marks "never display"

Tag counts across all corpus `forms` entries, resolved against JMdict:

```
rK 330   sK 328   sk 157   ok 60   ateji 38   oK 35   gikun 31   io 19   ik 8   rk 5   iK 4
```

`sK`/`sk` are JMdict's *search-only* forms: they exist so a lookup succeeds, and the spec says they are not
to be shown. 485 of them sit in `forms` with no tag carried, indistinguishable from real spellings. Examples:

- id 295 死ぬ → form `ﾀﾋぬ` (half-width katakana internet slang, `is_kana: true`)
- id 1025 凄い → `すごーい`, `すご〜い`, `すっごーい`, `スゴーイ`
- id 1 ああ → 20 forms including `於乎`, `於戯`, `嗟乎`, `吁`, `ああぁ`, `あ〜あ`
- id 805 思う → `想う 憶う 念う 懐う 惟う 意う` (all rare)
- id 110 遅い → `おっそーい`, `おせー`, `おっせぇ`, `おっせえ`

**Fix:** carry each form's JMdict tags into the `forms` objects (the shape already has room), drop `sK`/`sk`
from the export entirely, and mark `rK`/`ok`/`ateji`/`ik` so a UI can hide them behind a "outras grafias"
toggle. This is also the prerequisite for fixing `is_primary` in F3.

---

## F7 — MEDIUM: 嫌い and 欲しい are glossed as passive participles, inverting the structure the learner must produce

```
203  嫌い  s0  en "disliked | distasteful | disagreeable"
             pt "detestado" | "que se detesta" | "desagradável"
586  欲しい s0 en "wanted | desired (wanting something)"
             pt "desejado" | "que se quer (ter)"
```

JMdict's "disliked"/"wanted" phrasing is a lexicographer's device for describing a Japanese が-marked
adjective in English. Translated straight into pt-BR it produces the wrong argument structure: 野菜が嫌いです
is "não gosto de verdura", not "verdura é detestada"; 水が欲しい is "quero água", not "água é desejada". The
neighbouring record shows the correct treatment already exists in the file — id 322 好き renders the same
construction as `"gostar de"`, not "gostado".

**Fix:** id 203 → `pt: "que não gosta (de)", "detestável", "desagradável"`; id 586 → `pt: "querer (ter)",
"desejar"`, keeping `s1` "querer que (alguém faça)" as is.

---

## F8 — MEDIUM: どの and どれ receive the identical pt gloss, erasing the distinction they exist to teach

```
451  何の どの  en "which (of three or more)"     pt "qual (entre vários)"
460  何れ どれ  en "which one (of three or more)" pt "qual (entre vários)"
```

Byte-identical pt. どの is prenominal (`どの本` = "qual livro"); どれ is a pronoun (`どれですか` = "qual
deles?"). A learner comparing the two cards is given no way to tell them apart, and any exercise generator
matching on gloss text will treat them as interchangeable. The same file distinguishes この/これ and その/それ
correctly, so this is an isolated slip.

**Fix:** 451 → `pt: "qual (+ substantivo)", "que (livro/pessoa etc.)"`; 460 → `pt: "qual deles", "qual (entre vários)"`.

---

## F9 — MEDIUM: the romaji convention for long vowels is applied three different ways

48 records contain a chōonpu (ー) in `kana`. 47 of them render it as a literal hyphen, which is neither
Hepburn nor consistent with the 48th:

```
30   アパート      → "apa-to"      (expected "apāto" or "apaato")
91   エレベーター  → "erebe-ta-"
501  パーティー    → "paatii"      ← vowel-doubling, the only record that does this
1183 あっ          → "axtsu"       ← wapuro/IME notation for the small っ, not romaji at all
```

Meanwhile the file gets the hard cases right elsewhere — `macchi` (マッチ), `sandoicchi` (サンドイッチ),
`gen'in` (原因), `ten'in` (店員), `hon'yaku` (翻訳) — so the transliterator is sound apart from these two
edge cases: chōonpu, and a word-final っ. Full list of the 47 hyphen records reproducible with a Hepburn
diff over `kana` vs `romaji`.

**Fix:** pick one convention (recommend vowel-doubling to match `paatii`, `isshoukenmei`, `okujou`), apply it
to the 47 hyphen records, and special-case word-final っ (`あっ` → `a` or `at`, never `axtsu`).

---

## F10 — MEDIUM: 15 headwords are full-width digits or Latin letters, with the real spelling demoted to `forms`

```
59  ５日   (五日 in forms)      401 １日   (一日)      440 １０日 (十日)      566 ２日 (二日)
520 ２０日 (二十日)             621 ３日   (三日)      664 ４日  (四日)       629 ６日 (六日)
474 ７日  (七日)                660 ８日   (八日)      248 ９日  (九日)       342 ０    (〇, 零)
517 ２０歳 (二十歳)             686 Ｙシャツ (ワイシャツ)  1144 ＦＡＸ (ファックス)
```

These are the strings a lesson card renders. `五日` is what a learner will meet in text; `５日` is a JMdict
convenience form. `ＦＡＸ` and `Ｙシャツ` also break the "kana headword for kana words" expectation.

**Fix:** prefer the non-full-width common form as `headword`/`is_primary` (`五日`, `二十歳`, `ファックス`,
`ワイシャツ`, `ゼロ`), keeping the full-width variants in `forms`.

---

## F11 — LOW/MEDIUM: two gloss-list conventions coexist in the same field

The overwhelming majority of senses put one gloss per array element. But **36 records** comma-join multiple
glosses inside a single string and **50 en glosses** semicolon-join them:

```
1261 優しい  en ["kind, gentle, nice"]                pt ["gentil, bondoso, amável"]     ← 1 element
1268 勝つ    en ["to win"], ["to beat, to defeat"]    pt ["vencer, ganhar"]              ← 1 element
956  公務員  en ["civil servant; public official; government employee"]                  ← 1 element
973  乗り物  en ["vehicle; means of transport; ride"]                                    ← 1 element

733  柔らかい en ["soft", "tender"]                    pt ["macio", "mole", "tenro"]      ← normal form
```

Any renderer that draws one chip/line per gloss shows 優しい as a single blob while its neighbour shows three.
It also breaks gloss-level matching in exercise generation. The clustering by id range (1255–1300 for the
comma style, 930–990 for the semicolon style) suggests two authoring batches that never got normalized.

**Fix:** split on bare `,` / `;` (outside parentheses) into separate array elements in both locales.

---

## F12 — LOW: 11 records repeat an identical pt gloss across two different senses

```
347  洗濯    s0 "lavar roupa | lavagem de roupa"   s1 "lavar roupa | fazer a lavagem"
649  休み    s0 "descanso | folga | pausa"          s1 "folga | dia de folga | férias"
869  寝坊    s0 "dormir demais | preguiça..."       s1 "dormir demais | perder a hora"
630  向こう  s0 "o outro lado | lá | além"          s1 "a outra parte | o outro lado"
```

also 556 広い ("amplo"), 230 消す ("apagar"), 177 軽い ("leve"), 620 道 ("caminho"),
839 恥ずかしい ("envergonhado"), 784 深い ("profundo"), 1103 遠く ("longe").

In 347/869 the two senses are the noun and the する-verb reading, so the repeated string defeats the split
entirely. **Fix:** give the verbal sense a distinct pt form (347 s0 `"lavagem de roupa"` / s1 `"lavar roupa"`)
or merge the senses.

---

## F13 — LOW: 336 背(せい) and 1338 背(せ) are near-duplicate records with byte-identical pt

```
336  背 せい   s0 pt "altura (de uma pessoa)", "estatura"
1338 背 せ     s0 pt "altura (de uma pessoa)", "estatura"   (+ s1 "costas", "dorso")
```

Both are real JMdict entries (1472650 / 2147990) and both are legitimately N5, but presented side by side with
identical text a learner cannot tell why there are two cards. **Fix:** add a distinguishing note (せ is the
older/idiomatic reading, 背が高い) or fold 336 into 1338 as an alternate reading.

---

## F14 — LOW: pt glosses that add or drop meaning relative to their own `en`

| id | en | pt | problem |
|---|---|---|---|
| 1011 踊り | `"dance", "dancing"` | `"dança", "dança (tradicional)"` | invents a restriction to traditional dance that 踊り does not carry, and the two glosses are otherwise the same word. Fix: `"dança", "o ato de dançar"` |
| 749 失礼 | `"rude", "impolite", "discourtesy"` | `"grosseria", "falta de educação", "descortesia"` | `adj_class: na_adj`, en leads with two adjectives, pt gives only nouns. A learner cannot form 失礼な人. Fix: add `"grosseiro"`, `"mal-educado"` |
| 823 残念 | `"disappointing", "too bad"` | `"que pena", "infelizmente"` | "infelizmente" is an adverb; 残念 is `adj-na`/`n`. Fix: `"decepcionante"`, `"uma pena"` |
| 1198 注射 | `"injection", "shot"` | `"injeção", "picada (vacina)"` | in pt-BR "picada" reads as an insect bite. Fix: `"injeção", "aplicação (de vacina)"` |
| 329 ストーブ | `"heater", "stove (heating)"` | `"aquecedor", "estufa"` | "estufa" in pt-BR is a greenhouse. Fix: drop it, or `"aquecedor a gás/querosene"` |
| 1249 移る s1 | `"to spread (illness)", "to be passed on"` | `"pegar (doença)", "ser transmitido"` | 移る is `vi` with the illness as subject (風邪がうつる); "pegar (doença)" flips the subject to the person and reads as transitive. Fix: `"ser transmitida (doença)", "passar (de alguém para outro)"` |
| 1049 女性 / 1037 男性 | `"woman"` / `"man"` | `"mulher", "indivíduo do sexo feminino"` / `"homem", "indivíduo do sexo masculino"` | clinical register; `translation_style.md` §4 asks for "direct, concrete, friendly, beginner-clear". Fix: `"mulher", "pessoa do sexo feminino"` |
| 798 赤ちゃん / 910 赤ん坊 | both `"baby", "infant"` | `"bebê, neném"` / `"bebê, nenê"` | same word spelled two ways across neighbouring records. Pick one. |

---

## F15 — LOW: sense-order inversion on 夢

```
1055 夢  s0 en "dream (aspiration, goal)"   pt "sonho | aspiração"
         s1 en "dream (while sleeping)"     pt "sonho (durante o sono)"
```

JMdict orders the sleeping-dream sense first, and that is the sense an N4 learner meets first
(夢を見る). Low impact because both senses are present. **Fix:** swap `order`.

---

## What is clean

Worth recording, since these were checked and held up:

- **pt-BR locale purity.** Zero pt-PT lexical markers across all 3,737 gloss strings (`comboio`, `autocarro`,
  `telemóvel`, `ecrã`, `casa de banho`, `rapariga`, `frigorífico`, `pequeno-almoço`, `sanita`, `talho`).
  Vocabulary is consistently Brazilian: "ônibus", "trem", "geladeira", "celular" contexts, "banheiro",
  "café da manhã", "quitanda", "carteira", "mangá".
- **No em dashes** (`—`/`–`) anywhere in the pt glosses — `translation_style.md` §4 respected.
- **No empty or untranslated senses.** Every sense has both an `en` and a `pt-BR` list; the 45 records where a
  pt string equals its en string are genuine cognates (hotel, hospital, animal, piano, zero, software).
- **kana ↔ forms integrity:** all 1,358 `kana` values appear in the record's own `forms`; all 1,358 headwords
  are the single `is_primary` form; no duplicate forms; no record lacking a kana form; exactly one
  `is_kana` mismatch (id 295, half-width `ﾀﾋぬ`, itself a symptom of F6).
- **`lexeme_type`** is coherent: all 10 `counter` records carry `ctr` in a sense `pos`, and no non-counter
  record does.
- **No duplicate `jmdict_ref`** across the 1,358 records; all 1,358 refs resolve in JMdict 3.6.2 and all sit
  in the JMdict "common" subset.
- **Gloss faithfulness in the bulk of the file is genuinely good.** Nuanced senses land well: 適当
  ("adequado" / "feito de qualquer jeito"), 全然 (negative + colloquial affirmative), 無理 (three senses),
  結構 (three, including the polite refusal), 貸す vs 借りる kept distinct, 割合 / 都合 / 具合 all sensible,
  and idiomatic pt-BR where it counts ("dar uma mão", "aguentar firme", "dar o braço a torcer",
  "fazer baldeação", "brinquedo (de parque)" for 乗り物, "quitanda" for 八百屋).

---

## Counts

| | |
|---|---|
| Records checked | 1,358 (n5: 705, n4: 653) |
| Senses checked | 1,947 |
| Gloss strings checked (en + pt-BR) | 3,737 |
| **Findings flagged** | **15** |
| — critical | 2 (F1, F2) |
| — high | 3 (F3, F4, F5) |
| — medium | 4 (F6, F7, F8, F9) + F10 |
| — low | 5 (F11–F15) |
| Individual records implicated | ~21 (F1) + 1 (F2) + 156 (F3) + 1,946 senses (F4) + 51 (F5) + 485 forms (F6) + 2 (F7) + 2 (F8) + 48 (F9) + 15 (F10) + 86 (F11) + 11 (F12) + 2 (F13) + 9 (F14) + 1 (F15) |

**Blocking for learner release:** F1 and F2. F3, F4 and F5 are blocking for any UI that renders headwords or
filters on politeness.
