# QA sweep — kanji records, slice 1

**Assignment:** `corpus/kanji/n5.json` + `corpus/kanji/n4.json` — **280 records** (n5 103, n4 177), covering
`meanings` (pt-BR + en), `notes`, `irregular_note`, all **1 812** `readings` rows and all **2 193**
`example_words` entries.

**Method.** Every record read in full. Cross-checked mechanically against
`research/datasets/jmdict/kanjidic2-en-3.6.2+20260608153333.json.tgz` (10 384 characters, unpacked read-only
into scratch) and against `corpus/vocab/{n5,n4,n3,n2,n1}.json` for level fit, gloss provenance and written-form
commonness. Style authority: `design/translation_style.md`. Provenance contract: `design/i18n.md`,
`CLAUDE.md` §1.1–1.3. Producer inspected: `scripts/export/export_corpus.py:159-171`.

**Note on this file.** An earlier pass wrote a report to this same path (findings F1–F10). This is an
independent second pass. Everything that pass found is **still present in the exported data** and is
re-confirmed below from my own evidence, marked `[confirmed]`. Four findings are new — three of them fall in
areas the earlier pass explicitly listed as clean, so they are worth reading first.

---

## Headline

The **Layer-A spine is exact**. Against KANJIDIC2, all 280 records match on `strokes`, `grade`, `freq_rank`
and `kangxi_radical` with **zero** mismatches, and the kun/on/nanori reading **sets** (okurigana split points
reconstructed) match **exactly in both directions — 0 missing, 0 extra, across all 1 812 rows**. The 47
`irregular_note` texts are factually correct: every jukujikun, rendaku and gemination claim I checked holds
(真っ二つ ふた→ぷた, 出発 シュツ→しゅっ + ハツ→ぱつ, 木綿 も, 八百屋 お, 真っ赤 あか→か, 扇風機 ふう→ぷう).

**Everything that fails is on the selection-and-labelling side.** The `example_words` chooser has no notion of
level and no notion of which *written form* of a word people actually use; three reading-metadata fields
(`introduced_at_level`, `common`, array order) either contradict the record they sit in or carry no
information at all.

---

## K1 — HIGH — 29 example words teach a written form the corpus itself marks `is_common: false` **[new]**

- **Records:** 24 — 仕 何 先 八 区 土 子 山 左 度 思 所 方 早 時 有 本 洋 目 紙 菜 薬 行 青
- **Field:** `example_words[].headword`

The vocab record stores every surface form with an `is_common` flag. For 29 example words the `headword` the
kanji record renders is the form flagged **`is_common: false`**, while the form flagged common is the kana one.
`kanji:洋` (n4) is the worst: its **first two** example words are ateji nobody writes.

```json
// corpus/kanji/n4.json — kanji:洋, example_words[0] and [1]
{ "headword": "洋杯", "kana": "コップ", "slug": "vocab:1050390", "gloss": {"pt-BR": ["copo"]} },
{ "headword": "洋袴", "kana": "ズボン", "slug": "vocab:1074260", "gloss": {"pt-BR": ["calça", "calças"]} }
```

```json
// corpus/vocab/n5.json — vocab:1074260, the same word
"forms": [ {"form": "洋袴",  "is_kana": false, "is_common": false, "is_primary": true},
           {"form": "段袋",  "is_kana": false, "is_common": false, "is_primary": false},
           {"form": "ズボン", "is_kana": true,  "is_common": true,  "is_primary": false} ]
```

Representative cases (all 29 follow the same shape — rare kanji form as headword, kana form as the only common one):

| record | headword shown | reading | the form marked common | what the learner is being told |
|---|---|---|---|---|
| `kanji:洋` (n4) | 洋杯 / 洋袴 | コップ / ズボン | ズボン, コップ | that ズボン is written 洋袴 |
| `kanji:土` (n5) | 混凝土 | コンクリート | コンクリート | 凝 is N1-and-beyond; 土's 7th example |
| `kanji:子` (n5) | 硝子 | ガラス | ガラス | 硝 is not in the corpus at any level |
| `kanji:目` (n5) | 御目出度う | おめでとう | おめでとう | a greeting written in kana 100% of the time |
| `kanji:左` (n5) | 左様なら | さようなら | さようなら | idem |
| `kanji:青` (n4) | 番瀝青 | ペンキ | ペンキ | 瀝 is not in the corpus at any level |
| `kanji:山` (n5) | 巫山戯る | ふざける | ふざける | 巫 is not in the corpus at any level |
| `kanji:度` (n4) | 屹度 | きっと | きっと | 屹 is not in the corpus at any level |
| `kanji:何` (n5) | 如何して | どうして | どうして | どうして is kana in every textbook |
| `kanji:早` (n4) | お早う | おはよう | おはよう | the single most-used greeting, misspelled |

- **Why it is wrong.** The earlier pass checked commonness at the *record* level ("`example_words` backed by a
  JMdict-uncommon vocab — 0") and it is right that all 29 words are common words. The defect is one level down:
  the **spelling being taught** is the rare one. Six of these headwords (混凝土, 硝子, 番瀝青, 巫山戯る, 屹度,
  彼方此方) use kanji that do not appear anywhere in `corpus/kanji/{n5..n1}.json`, so an N5 learner is shown a
  character the corpus never plans to teach. This directly violates the assignment's "appropriate for level"
  bar and CLAUDE.md §1.2's preference for what real writers actually produce.
- **Root cause.** The vocab record's `headword` is `forms[is_primary]`, and JMdict's first kanji form is
  primary even when tagged rare (`rK`); `export_corpus.py:161` then copies `v.headword` straight through.
- **Proposed fix.** In the example-word projection, render the first form with `is_common: true` (which is the
  kana form for all 29), keeping the rare kanji form available as a secondary field if it is wanted at all. As
  a data-side alternative, exclude a candidate whose only kanji spelling is `is_common: false` when the record
  has other candidates — 洋 has 洋服 / 西洋 / 東洋 / 海洋 / 洋風 waiting, and 目 has 目上 / 目印 in the bank.

## K2 — HIGH — two records list the same example word twice, byte-identical `[confirmed]`

- **Records:** `kanji:日` (n5), `kanji:茶` (n4) — `example_words[7]` and `[8]` in both

`kanji:日` repeats `{"headword": "日曜日", "kana": "にちようび", "vocab_id": 485, "slug": "vocab:1464900"}`;
`kanji:茶` repeats `{"headword": "滅茶苦茶", "kana": "めちゃくちゃ", "slug": "vocab:1533000"}`. These are the
only two exact duplicates in the slice (checked on `slug` and on `(headword, kana)`); every other repeated
headword is a legitimate different-reading pair (中 なか/ちゅう, 悪口 わるぐち/あっこう, 寒気 かんき/さむけ).

- **Why it is wrong.** Both records are at the 10-slot cap, so a duplicate costs a real teaching slot and
  renders twice in any UI that walks the array. `お茶` (おちゃ, n5, `vocab:111`) — the first 茶 word anyone
  learns — is absent from `kanji:茶` while 滅茶苦茶 holds two slots.
- **Diagnosis note.** Both duplicated headwords contain the record's kanji **twice** (日曜**日**, 滅**茶**苦**茶**),
  which points at a per-occurrence row in the `vocab_kanji` join feeding
  `export_corpus.py:160-163`. It is not consistent, though: 彼方此方 (方 twice, under `kanji:方`) and 無茶苦茶
  (茶 twice, under `kanji:茶`) each appear only once. So dedupe on `slug` in the exporter rather than assuming
  the join is uniform.
- **Proposed fix.** `SELECT DISTINCT` / dedupe on `v.id` in the example-word query, then re-export. Freed slots:
  `お茶` for 茶, `月曜日` or `一日` for 日.

## K3 — HIGH — `example_words` selection is level-blind, and its tiebreak is arbitrary `[confirmed, root cause new]`

- **Scope:** **1 503 of 2 193 example words (69%) sit above their own record's level** — 451 of them N1.

| kanji level | above own level |
|---|---|
| n5 (103 records, 827 words) | 561 |
| n4 (177 records, 1 366 words) | 942 |
| **total** | **1 503 (n3 559, n2 370, n1 451, n4-over-n5 123)** |

Three records have **zero** example words at or below their own level: `kanji:京`, `kanji:主`, `kanji:不`.
Two of the three could be fixed from the existing bank:

| record | what it shows | in-corpus word at level it skipped |
|---|---|---|
| `kanji:不` (n4) | 不可欠 (n1), 不在 (n1), + 8 × n3 | **不便 (ふべん, n4, `vocab:1060`)** |
| `kanji:主` (n4) | 主人公 (n1), 主 ×3 (n1/n1/n2), + 6 × n2/n3 | **ご主人 (ごしゅじん, n4, `vocab:953`)** |
| `kanji:社` (n5) | 出社 (n1), 社交 (n1), 社説 (n2), 商社 (n2) — 4 of 10 slots | — |
| `kanji:見` (n5) | 見込み (n1), 見かける (n1), 見つめる (n2) | — |

- **Root cause (new).** `export_corpus.py:162` is
  `ORDER BY v.common DESC, v.freq_rank IS NULL, v.freq_rank LIMIT 10`. There is no level term at all — and for
  the records above the sort **degenerates entirely**: every candidate for 不 and for 主 has `common = true` and
  `freq_rank = null`, so both keys tie on all rows and the LIMIT 10 cut falls on undefined row order. 不便 and
  ご主人 are not losing on merit; they are losing on row id. This makes the field non-reproducible across a
  rebuild as well.
- **Proposed fix.** Add a level term and a stable tiebreak:
  `ORDER BY (level_order >= kanji_level_order) DESC, v.common DESC, v.freq_rank IS NULL, v.freq_rank, v.slug`.
  Everything needed is already in the corpus; no vocab additions required for 不 or 主.

## K4 — HIGH — `introduced_at_level` is null or contradicts the same record's example list `[confirmed]`

- **Scope:** 43 non-nanori readings carry `null` despite having an example word at or below the kanji's level;
  **43 readings on n5 kanji are tagged `n4`**; **15 records have no reading tagged at all**
  (不 京 仕 以 医 午 図 土 地 意 理 田 自 試 野).

`design/schema_v2.md` defines the field as derived from the example vocab, so these are all determinable.
The self-contradictions are the sharpest, because both halves live inside one record:

| record | reading | tagged | its own `example_vocab_ids` resolve to |
|---|---|---|---|
| `kanji:子` (n5) | kun こ | **n4** | 子供 (n5), 女の子 (n5), 男の子 (n5) |
| `kanji:子` (n5) | on シ | **null** | 帽子 (n5), お菓子 (n5), 調子 (n3) |
| `kanji:気` (n5) | on キ | **n4** | 病気 (n5), 天気 (n5), 元気 (n5) |
| `kanji:火` (n5) | on カ | **null** | 火曜日 (n5), 火事 (n4) |
| `kanji:午` (n5) | on ゴ | **null** | 午前 (n5), 午後 (n5) |
| `kanji:自` (n4) | on ジ | **null** | 自分, 自転車, 自動車 (all n5) |

`kanji:子` ends up with **no reading tagged n5 at all**, though it is an n5 kanji whose n5 words 子供 and
女の子 are sitting in its own reading rows.

- **Proposed fix.** Re-derive as documented — for each non-nanori reading,
  `introduced_at_level = max(level_order)` over `example_vocab_ids` (the *easiest* word that uses it), leave
  null only where the reading genuinely has no example, and re-export. Do not patch values individually: the
  seeding rule that produced the current ones is not the documented rule.

## K5 — MEDIUM — `common` on a reading carries no information, and the record's own notes say so **[new]**

- **Scope:** `common: true` on **698 of 698** kun readings and **426 of 426** on readings; `false` on
  **688 of 688** nanori. The field is a verbatim restatement of `type != 'nanori'`.

The corpus notices this itself. Five reading notes in the slice read, verbatim:

> "Segunda leitura sino-japonesa (on) **marcada como comum, mas nenhuma palavra desta entrada a usa**."

…attached to rows that carry `"common": true`:

```json
// corpus/kanji/n5.json — kanji:来
{ "reading": "タイ", "type": "on", "common": true, "example_vocab_ids": null, "note": {"pt-BR": "Segunda leitura sino-japonesa (on) marcada como comum, mas nenhuma palavra desta entrada a usa."} }
// corpus/kanji/n5.json — kanji:気
{ "reading": "ケ",  "type": "on", "common": true, "example_vocab_ids": null, "note": {"pt-BR": "Segunda leitura sino-japonesa (on) marcada como comum, mas nenhuma palavra desta entrada a usa."} }
```

- **Why it is wrong.** A consumer filtering `readings[].common` to show "the readings that matter" gets 気 ケ
  ranked equal to 気 キ, 来 タイ equal to 来 ライ, and 日 -か equal to 日 ニチ. `corpus/kanji/INDEX.md` documents
  the flag as "`common` (nanori=false)", so the current behaviour matches the doc — but a boolean named
  `common` that can only ever mirror `type` is a field a reviewer will trust wrongly, and the authored prose in
  the same record already contradicts it. This one is not visible from the "no nanori carries `common: true`"
  check the earlier pass ran, which only tests one direction.
- **Proposed fix.** Either derive it for real — `common = example_vocab_ids IS NOT NULL` is already computed
  and would separate キ from ケ (426 on rows split roughly 173/253 by whether they have any example) — or drop
  the field and let consumers read `type`. Whichever is chosen, fix `INDEX.md` to describe it accurately, and
  delete the five notes that argue with it.

## K6 — MEDIUM — the nanori block sits between kun and on `[confirmed]`

- **Scope:** 182 of 280 records order `kun → nanori → on`; 11 more `nanori → on`. Never `kun → on → nanori`.

| record | nanori rows before the first on row | on reading buried |
|---|---:|---|
| `kanji:生` (n5) | 25 (first on at index **43 of 45**) | セイ, ショウ |
| `kanji:上` (n5) | 10 (first on at index 25 of 28) | ジョウ, ショウ |
| `kanji:理` (n4) | 16 (of 18) | リ — the only on reading, needed for 料理, 理由, 無理 |
| `kanji:真` (n4) | 15 (of 19) | シン — needed for 写真 |
| `kanji:日` (n5) | 12 (of 17) | ニチ, ジツ |

- **Root cause.** `export_corpus.py:151` is `ORDER BY kr.reading_type` — a plain string sort, and
  `kun < nanori < on` alphabetically. The order is an accident of the enum spelling, not a decision.
- **Why it is wrong.** The nanori notes themselves say the group is "não no vocabulário comum" with no
  examples; a group the record labels irrelevant should not separate the two relevant ones.
- **Proposed fix.** Sort by an explicit ordinal — kun(0), on(1), nanori(2) — in the exporter and re-export.
  Presentation only; no data edits.

## K7 — MEDIUM — `kanji:屋` drops "telhado" from pt-BR while its own example word teaches it `[confirmed]`

```json
"meanings": { "pt-BR": ["loja", "estabelecimento", "prédio", "-eiro"],
              "en":    ["roof", "shop", "store", "building", "-dealer"] }
```

KANJIDIC2 for 屋 is `['roof', 'house', 'shop', 'dealer', 'seller']` — **roof is first**. `en` keeps it; pt-BR
has no *telhado* anywhere. Then `example_words[1]` is **屋根 (やね) — "telhado"** and `example_words[4]` is
屋上 ("terraço, cobertura de prédio"). The learner is handed the word and given nothing in the meaning list to
hang it on. This is the only pt-BR meaning list in the slice that drops a concept its own example words teach.

- **Proposed fix.** `"pt-BR": ["telhado", "loja", "estabelecimento", "prédio", "-eiro"]`, which also restores
  index parity with `en`.

## K8 — MEDIUM — `meanings.en` is not the KANJIDIC source `design/i18n.md` claims `[confirmed]`

- **Scope:** **170 of 280 records (61%)** contain at least one `en` gloss that is not a KANJIDIC2 meaning for
  that character.

`design/i18n.md:60-62`: *"the `en` key already preserves the authoritative English source wherever one exists:
kanji **meanings** → `en` from KANJIDIC"*. Measured:

| record | `meanings.en` | KANJIDIC2 |
|---|---|---|
| `kanji:金` | gold, **money**, **metal** | gold |
| `kanji:屋` | roof, shop, **store**, **building**, **-dealer** | roof, house, shop, dealer, seller |
| `kanji:生` | life, **be born**, **live**, **raw** | life, genuine, birth |
| `kanji:真` | true, real, **pure** | true, reality, Buddhist sect |
| `kanji:安` | cheap, **safe**, **peace** | relax, cheap, low, quiet, rested, contented, peaceful |

- **Why it matters.** The curated list is *better teaching material* than raw KANJIDIC and should stay. The
  defect is the provenance label: CLAUDE.md §1.1 defines Layer A as ground truth a reviewer may trust blindly,
  and pt-BR is validated *against* `en`, so today both sides of the locale object are authored with no
  untouched source between them.
- **Proposed fix.** Amend `design/i18n.md` to describe kanji `meanings.en` as a curated, KANJIDIC-grounded
  Layer-B list (cheapest), or add a sibling `meanings_source.en` carrying the untouched KANJIDIC array so the
  Layer-A claim becomes true.

## K9 — LOW — 17 example-word `en` glosses are one string with embedded semicolons **[new]**

- **Records:** 16 — 出 土 火 意 用 以 思 心 産 海 料 乗 森 館 色 旅

The pt-BR side is split into a proper list; the `en` side is a single unsplit string:

```json
// kanji:思 / kanji:出 — example_words, 思い出す
"gloss": { "pt-BR": ["lembrar", "recordar", "vir à memória"],
           "en":    ["to remember; to recall; to call to mind"] }   // 3 items on one side, 1 on the other
```

Others: 心 `["heart; mind"]`, 火 `["fire; flame"]`, 用意 `["preparation; arrangements"]`, 以内
`["within; inside (a limit); less than"]`, 景色 `["scenery; landscape; view"]`, 旅館
`["traditional Japanese inn; ryokan"]`, 乗り物 `["vehicle; means of transport; ride"]`.

- **Why it is wrong.** `common.schema.json#/$defs/LocaleTextList` types this as a list of glosses; a consumer
  joining with ", " renders `heart; mind` where every other record renders `heart, mind`, and any gloss-count
  check against pt-BR reports a false mismatch. It also breaks the "gloss vs vocab sense-0 is byte-identical"
  invariant's usefulness — the divergence is upstream in `corpus/vocab/*.json` senses, so both layers carry it.
- **Proposed fix.** Split on `; ` at ingest for these 17 sense rows in the vocab layer, then re-export the
  kanji layer.

## K10 — LOW — English-dictionary abbreviations survive untranslated into pt-BR learner text **[extends prior F7]**

Six learner-facing pt-BR strings carry conventions from the English source rather than pt-BR prose:

| record | field | text |
|---|---|---|
| `kanji:台` | `meanings["pt-BR"][2]` | contador (sufixo **p/** máquinas e veículos) |
| `kanji:車` | gloss of 汽車 | trem (**esp.** a vapor) |
| `kanji:花` | gloss of 花見 | contemplação das flores (**esp.** de cerejeira) |
| `kanji:漢` | gloss of 漢和 | sino-japonês (**esp.** dicionário de kanji) |
| `kanji:英` | gloss of 和英 | japonês-inglês (**ex.:** dicionário) |
| `kanji:貸` | gloss of 貸出 | empréstimo (de livro **etc.**) |

`esp.` is a direct carry-over of JMdict's "especially" and is not a standard pt-BR abbreviation; `p/` is
texting shorthand. `corpus/vocab/n5.json` already writes the 台 concept out in full as *"contador para máquinas
e veículos"*, so the abbreviated form is inconsistent with the corpus's own phrasing.
`design/translation_style.md` §4 asks for direct, beginner-clear pt-BR.

- **Proposed fix.** `p/` → `para`; `esp.` → `especialmente`; `ex.:` → `por exemplo,`; `etc.` → `e outros`.

## K11 — LOW (cross-layer) — `kanji:京` has two example words, both above level, and 東京 is not in the bank `[confirmed]`

`kanji:京` (n4), meanings "capital, Quioto", has exactly two example words: 上京 (じょうきょう, **n3**) and
帰京 (ききょう, **n1**) — paraphrases of each other, both about travelling to and from Tokyo, while 東京 itself
never appears. It is absent from all five `corpus/vocab/*.json` files, so the kanji layer has nothing to link.
`YOMINEKO_CORPUS_BUILD_SPEC.md` skips proper names "unless useful"; 東京 is the reason 京 is on the N4 list.

- **Proposed fix.** Admit 東京 (and 京都) under the "unless useful" clause, link them from `kanji:京`, and tag
  its on キョウ `introduced_at_level: n4` (currently null, see K4).

---

## What I checked and found clean

| Check | Rows | Result |
|---|---:|---|
| `strokes` / `grade` / `freq_rank` / `kangxi_radical` vs KANJIDIC2 | 280 each | 0 mismatches |
| kun/on/nanori reading **sets** vs KANJIDIC2, okurigana reconstructed, both directions | 1 812 | 0 missing, 0 extra |
| Reading `type` filed correctly (no on-as-kun, no kun-as-on) | 1 812 | 0 errors |
| Reading types contiguous within the array (no interleaving) | 280 | 0 split blocks |
| Duplicate `(type, reading, okurigana)` within a record | 1 812 | 0 |
| `common: false` on every nanori | 688 | 0 violations |
| Reading `note` present, non-empty, pt-BR | 1 812 | 0 missing |
| `irregular_note` factual accuracy (jukujikun / rendaku / gemination / ateji) | 47 | 47 correct |
| `notes` field null on every record | 280 | consistent with the contract's own description |
| `example_words` headword actually contains the kanji | 2 193 | 0 violations |
| `example_words` headword/kana/slug vs its vocab record | 2 193 | 0 mismatches |
| `example_words` gloss vs the vocab record's sense-0 gloss | 2 193 | 0 divergences |
| `example_vocab_ids` resolve to a real vocab record | 671 | 0 dangling |
| pt-BR meanings/glosses/notes: em dash (—) | all | 0 |
| pt-BR meanings/glosses/notes: pt-PT forms, "Quanto a", "Vale ressaltar" | all | 0 |
| pt-BR gloss left untranslated (identical to `en`) | 2 193 | 0 real cases (動物 "animal", 病院 "hospital" are true cognates) |

Thin `example_words` lists — 駅, 犬, 秋 have 1; 九, 六, 七, 川, 千, 右, 魚, 耳, 町, 銀, 春, 森, 冬, 勉, 菜, 暑
have 2 — are **not** defects: for each, `corpus/vocab/` holds no further word using that kanji. The lists are
as full as the vocab layer allows.

---

## Counts

| Finding | Severity | Status | Records |
|---|---|---|---:|
| K1 example word teaches an `is_common: false` written form | HIGH | **new** | 24 (29 entries) |
| K2 duplicate `example_words` entry | HIGH | confirmed | 2 |
| K3 example-word selection level-blind; tiebreak degenerate | HIGH | confirmed (root cause new) | 1 503 of 2 193 entries; 3 records at 0/10 |
| K4 `introduced_at_level` null or self-contradictory | HIGH | confirmed | 44 |
| K5 `common` on readings restates `type`; notes contradict it | MEDIUM | **new** | 280 (1 124 rows) |
| K6 nanori block ordered between kun and on | MEDIUM | confirmed | 193 |
| K7 `kanji:屋` pt-BR drops "telhado" | MEDIUM | confirmed | 1 |
| K8 `meanings.en` mislabelled as raw KANJIDIC | MEDIUM | confirmed | 170 (1 doc edit) |
| K9 `en` gloss unsplit on `;` | LOW | **new** | 16 (17 entries) |
| K10 English abbreviations in pt-BR text | LOW | **extends prior F7** | 6 |
| K11 `kanji:京` no in-level example word; 東京 absent | LOW | confirmed | 1 (+`kanji:主`, `kanji:不`) |

| Scope | Count |
|---|---:|
| Records assigned / read in full | 280 / 280 |
| n5 / n4 | 103 / 177 |
| `readings[]` rows checked | 1 812 |
| `example_words[]` entries checked | 2 193 |
| `irregular_note` texts verified by hand | 47 |
| Vocab records loaded for level / gloss / form cross-check | 7 401 |
| KANJIDIC2 characters loaded | 10 384 |
| **Findings** | **11 (4 HIGH, 4 MEDIUM, 3 LOW)** |

**Priority.** K2 is a two-minute exporter fix that also frees the slot `お茶` needs. K1 and K3 are the same
query in `export_corpus.py:160-163` and should be fixed together — add the `is_common` form preference and the
level term in one edit, then re-export; between them they change what 24 records *show* and reorder what 1 503
entries *are*, with no vocab additions needed. K4 and K5 are both reading-metadata derivations that the corpus
already has the inputs for. K8 is a one-line documentation correction and should not be skipped: it is the
difference between a reviewer trusting `meanings.en` blindly and knowing to spot-check it.
