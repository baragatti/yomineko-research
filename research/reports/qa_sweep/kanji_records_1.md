# QA sweep — kanji records, slice 1

**Assignment:** `corpus/kanji/n5.json` + `corpus/kanji/n4.json` — **280 records checked** (n5 103, n4 177),
covering `meanings` (pt-BR + en), `notes`, `irregular_note`, all **1 812** `readings` rows (type, okurigana,
`common`, `introduced_at_level`, `example_vocab_ids`, `note`) and all **2 193** `example_words` entries
(headword, kana, level fit, gloss).

**Cross-checks run:** every record was diffed against **KANJIDIC2 3.6.2+20260608153333**
(`research/datasets/jmdict/kanjidic2-en-…json.tgz`, unpacked read-only into scratch) and against
`corpus/vocab/{n5,n4,n3,n2,n1}.json` (7 401 records) for level fit and gloss provenance. Contracts consulted:
`design/schema_v2.md`, `design/i18n.md`, `design/translation_style.md`, `design/quality_rubric.md`,
`YOMINEKO_CORPUS_BUILD_SPEC.md`.

---

## Headline

**The Layer-A spine of this slice is flawless.** Across all 280 records, `strokes`, `grade`, `freq_rank`,
`kangxi_radical`, and the complete kun/on/nanori reading sets (with okurigana split points reconstructed)
match KANJIDIC2 **exactly — zero mismatches, in both directions**. Reading *type* assignment is likewise
perfect: no on reading is filed as kun, no kun as on, no nanori carries `common: true`, and all 1 812 rows sit
in contiguous type blocks. Referential integrity is clean too: **0** dangling `example_vocab_ids`, **0**
example words whose headword/kana/slug disagrees with its vocab record, **0** example words that do not
contain the kanji.

The pt-BR prose is also in good shape. Every one of the 47 `irregular_note` texts (22 n5 + 25 n4) is
factually correct — I verified each claimed jukujikun/rendaku/gemination case by hand, including the ones that
lean on the record's own reading list (木/木綿 → も, 文/文字 → も: both readings are genuinely present in the
nanori group). The style contract holds: **0** em dashes, **0** pt-PT forms, **0** "Quanto a"/"Vale
ressaltar" tells, **0** trailing/double whitespace across the whole slice.

**The failures are all on the pedagogical-selection side, not the factual side.** Two records duplicate an
example word verbatim; the example-word chooser systematically reaches past easy words the corpus already
owns and grabs N1/N2 ones instead; and `introduced_at_level` — the field the spec calls "essential" — is
absent or contradictory on 44 records.

---

## F1 — HIGH — two records list the same example word twice, verbatim

- **Records:** `kanji:日` (id 2160, n5) and `kanji:茶` (id 1853, n4)
- **Field:** `example_words[7]` and `example_words[8]` in both cases

`kanji:日`, slots #8 and #9, byte-identical:

> ```json
> { "headword": "日曜日", "kana": "にちようび", "vocab_id": 485, "slug": "vocab:1464900",
>   "gloss": { "pt-BR": ["domingo"], "en": ["Sunday"] } }
> ```

`kanji:茶`, slots #8 and #9, byte-identical:

> ```json
> { "headword": "滅茶苦茶", "kana": "めちゃくちゃ", "vocab_id": 4042, "slug": "vocab:1533000",
>   "gloss": { "pt-BR": ["bagunçado", "caótico", "uma bagunça"], "en": ["a mess", "chaotic", "in disarray"] } }
> ```

- **Why it is wrong:** both records cap out at 10 example words, so a duplicate silently costs the record one
  of its ten teaching slots and renders the same row twice in any UI that walks the array. These are the only
  two exact duplicates in the slice (checked on `(headword, kana)` and on `vocab_id`); every other repeated
  headword is a legitimate different-reading pair (中 なか/ちゅう, 空 そら/から, 悪口 わるぐち/あっこう …).
- **Proposed fix:** drop the second occurrence in each and dedupe on `vocab_id` in the exporter. Both freed
  slots have an obvious in-corpus filler: for 日, `月曜日` (げつようび, n5) or `一日` (いちにち, n5); for 茶,
  **`お茶` (おちゃ, n5)**, which is currently missing from 茶 entirely (see F2).

## F2 — HIGH — `example_words` reaches past easy in-corpus words and picks N1/N2 ones

- **Records:** 48 records omit a vocab at or below their own level that exists in `corpus/vocab/` and contains
  the kanji; **31 of those** simultaneously spend a slot on an N1 or N2 word.
- **Field:** `example_words[]`

Distribution across the whole slice, example word level vs. its kanji's level:

| kanji level | ex. words at n5 | n4 | n3 | n2 | n1 | above own level |
|---|---:|---:|---:|---:|---:|---:|
| n5 (103 records) | 266 | 123 | 197 | 124 | 117 | **561 / 827 (68%)** |
| n4 (177 records) | 229 | 195 | 362 | 246 | 334 | **942 / 1 366 (69%)** |

**451 of the 2 193 example words (21%) are N1.** That alone is arguable — a kanji's compounds genuinely run
harder than the kanji. What is not arguable is the 48 records where the easier word *was already in the
corpus* and was passed over. The worst:

| record | N1/N2 words it chose | in-corpus word it skipped |
|---|---|---|
| `kanji:名` (n5) | 名付ける, 名誉, 本名, 名札, **名簿** (n1), 名詞 (n2) — 6 of 10 slots | **平仮名 (ひらがな, n5)**, **片仮名 (カタカナ, n5)** |
| `kanji:茶` (n4) | 喫茶, 無茶, 滅茶苦茶 ×2, 無茶苦茶 — 5 of 10 slots | **お茶 (おちゃ, n5)** |
| `kanji:何` (n5) | 何て, 何と (n1) | どこ, なぜ, どちら, どなた, いつも, いかが, どれ, どの — **8 n5 words** |
| `kanji:不` (n4) | 不可欠, 不在 (n1) | **不便 (ふべん, n4)**, **不味い (まずい, n5)** |
| `kanji:一` (n5) | **一敗 (いっぱい, n1)** | 一日, 一寸, 一昨日, 一昨年, 一月 — 5 n5 words |
| `kanji:場` (n4) | 市場 (しじょう), 農場, 職場 | 会場, 売り場, 飛行場, 駐車場 — 4 n4 words |
| `kanji:書` (n5) | 秘書, 文書, 聖書 (all n1) | **葉書 (はがき, n5)** |
| `kanji:入` (n5) | 入る (いる), 受け入れる, 購入 (all n1) | **入り口 (いりぐち, n5)** |
| `kanji:合` (n4) | 付き合う (n2) | 具合, 割合, 都合 — 3 n4 words |
| `kanji:字` (n4) | 字 (あざ), 赤字, 黒字, 字体, 十字路, 苗字 — 6 of 10 | **字引 (じびき, n5)** |

- **Why it is wrong:** `kanji:名` is the sharpest case. It is an **n5** kanji; a learner meeting it has just
  finished the kana syllabaries, and the two words that would land hardest — 平仮名 and 片仮名, both **n5**,
  both already sitting in `corpus/vocab/n5.json` — are absent, while `名簿` ("lista de nomes, registro,
  cadastro", n1) takes a slot. `kanji:茶` is nearly as bad: `お茶` is the first and most useful 茶 word in the
  language and it is not there, while `滅茶苦茶` occupies **two** slots (F1) and `無茶苦茶` a third.
  `kanji:一` — the very first kanji in `n5.json` — spends a slot on `一敗` ("uma derrota", n1), a scorekeeping
  term, which additionally collides in kana with `一杯` (いっぱい) two rows below it, so the learner sees the
  same reading twice with unrelated meanings and no note explaining the collision.
- **Proposed fix:** make the selector level-aware rather than frequency-only — sort candidates by
  `(level_order DESC, freq)` and take the top N, so a word at or below the kanji's level always outranks one
  above it. Then re-export. The 48 affected records are recoverable without adding any vocab: the replacement
  words are already in the corpus.

## F3 — HIGH — `introduced_at_level` is unpopulated or self-contradictory on 44 records

- **Records:** 44 (40 with a null-but-derivable reading, 15 with **no** reading tagged at all, 3 n5 records
  with no reading tagged `n5`; the sets overlap)
- **Field:** `readings[].introduced_at_level`

`design/schema_v2.md:51` defines the field as `n5|n4|n3|... derived from example vocab`, and
`schema_v2.md:14` calls it the whole reason `kanji_reading` is a first-class table. `design/quality_rubric.md`
item **1d** requires it to be *correct*. `YOMINEKO_CORPUS_BUILD_SPEC.md:304` calls it "essential."

**(a) 43 non-nanori readings carry `null` despite having an example word at or below the kanji's own level.**
Under the documented derivation rule these are all determinable. Worst offenders:

| record | reading | tagged | example vocab that forces the tag |
|---|---|---|---|
| `kanji:午` (n5) | on ゴ | `null` | 午前 (n5), 午後 (n5) |
| `kanji:土` (n5) | on ド | `null` | 土曜日 (n5) |
| `kanji:火` (n5) | on カ | `null` | 火曜日 (n5) |
| `kanji:意` (n4) | on イ | `null` | 意味 (n5), 意見/注意/用意 (n4) |
| `kanji:以` (n4) | on イ | `null` | 以上/以外/以内/以下 (all n4) |
| `kanji:図` (n4) | on ズ / on ト | `null` / `null` | 地図 (n5) / 図書館 (n5) |
| `kanji:自` (n4) | on ジ | `null` | 自分, 自転車, 自動車 (all n5) |
| `kanji:仕` (n4) | on シ | `null` | 仕事 (n5) |
| `kanji:医` (n4) | on イ | `null` | 医者 (n5) |
| `kanji:理` (n4) | on リ | `null` | 料理 (n5) |
| `kanji:野` (n4) | on ヤ | `null` | 野菜 (n5) |

**(b) 15 records have not a single reading tagged:** 不, 京, 仕, 以, 医, 午, 図, 土, 地, 意, 理, 田, 自, 試, 野.
For `kanji:午` this is total: the record has exactly two readings (kun うま, on ゴ), ゴ is the only one a
learner will ever need, and the record never says so.

**(c) 3 n5 records have no reading tagged `n5`, and the tag they do carry contradicts their own example
list:**

- `kanji:子` (n5): kun こ is tagged **`n4`**, but its own `example_vocab_ids` resolve to 子供 (n5), 女の子
  (n5), 男の子 (n5). Its on シ (帽子, お菓子 — both n5) is `null`. So the n5 kanji 子 has no n5 reading.
- `kanji:気` (n5): both き and キ are tagged **`n4`**, but キ's examples include 病気 (n5) and 天気 (n5).
- `kanji:火` (n5): kun ひ tagged `n4`; the on カ that 火曜日 (n5) needs is `null`.

- **Why it is wrong:** this is the field that answers the spec's own design question ("*which* readings belong
  to *which* tier"). With it null on 午/以/図/仕/医, a lesson planner asking "which reading of 以 do I teach at
  N4?" gets no answer from the corpus at all; with it wrong on 子/気, it gets an answer that is off by a level
  and contradicted by the same record's example list.
- **Proposed fix:** re-run the derivation as documented — for each non-nanori reading,
  `introduced_at_level = max(level_order)` over `example_vocab_ids`, i.e. the easiest word that uses it — then
  flag `needs_review` on rows where the result disagrees with the current value (278 of the 671 readings that
  have examples currently disagree, so the field is not merely incomplete; the seeding rule that produced it
  is not the documented one and should be replaced, not patched).

## F4 — MEDIUM — `kanji:屋` drops "telhado" from pt-BR while its own example word and reading note teach it

- **Record:** `kanji:屋` (id 204, n4)
- **Field:** `meanings`

> ```json
> "meanings": {
>   "pt-BR": ["loja", "estabelecimento", "prédio", "-eiro"],
>   "en":    ["roof", "shop", "store", "building", "-dealer"]
> }
> ```

- **Why it is wrong:** `en` opens with **roof**; `pt-BR` has no **telhado** anywhere. KANJIDIC2 gives
  `['roof', 'house', 'shop', 'dealer', 'seller']` — roof is the *first* meaning. The record then contradicts
  its own meaning list twice over: `example_words[1]` is **屋根 (やね) — "telhado"**, and the note on the kun
  reading や says, verbatim:
  > "…abre 屋根 (telhado) e 屋敷 (mansão)."

  So the pt-BR learner is shown "loja, estabelecimento, prédio" (and only the first three, in
  `corpus/kanji/INDEX.md:245`), then immediately handed 屋根 = telhado with nothing in the meaning list to
  hang it on. Every other locale-object in the slice is drop-free on the pt-BR side except this one and F9.
- **Proposed fix:** `"pt-BR": ["telhado", "loja", "estabelecimento", "prédio", "-eiro"]` — restoring index
  parity with `en` at the same time.

## F5 — MEDIUM — `meanings.en` is not the KANJIDIC source `design/i18n.md` says it is

- **Records:** 170 of 280 (61%)
- **Field:** `meanings.en`

`design/i18n.md:60-62` states the contract:

> "The export's locale-object shape is `{"pt-BR": <ours>, "en": <Layer-A source>}`; the `en` key already
> preserves the authoritative English source wherever one exists: kanji **meanings** → `en` from KANJIDIC…"

- **Why it is wrong:** for 170 records `en` contains glosses that are **not in KANJIDIC2 at all**, and it
  drops KANJIDIC glosses that are. Only 110 records have an `en` list that is a subset of KANJIDIC's, and only
  75 are a clean prefix of it. Examples:

  | record | `meanings.en` | KANJIDIC2 |
  |---|---|---|
  | `kanji:車` | car, **vehicle**, **wheel** | car |
  | `kanji:火` | fire, **Tuesday** | fire |
  | `kanji:金` | gold, **money**, **metal** | gold |
  | `kanji:文` | **writing**, sentence, **text**, literature | sentence, literature, style, art, decoration, figures, plan, literary radical (no. 67) |
  | `kanji:首` | neck, **head**, **chief** | neck, counter for songs and poems |

  The curation is *better teaching material* than raw KANJIDIC — I am not asking for it to be reverted. The
  defect is the **provenance label**. CLAUDE.md §1.1 defines Layer A as "zero AI… ground truth" and §1.3
  requires fact and explanation never to share a field. A reviewer told that `en` is KANJIDIC will trust it
  blindly (that is the stated point of Layer A) and will be wrong 61% of the time.
- **Proposed fix:** either (a) amend `design/i18n.md` to say kanji `meanings.en` is a **curated, KANJIDIC-
  grounded** list (Layer B), not the raw source, and note that the verbatim source stays reachable via
  `research/datasets/jmdict/kanjidic2-en-*.tgz`; or (b) add a sibling `meanings_source.en` holding the
  untouched KANJIDIC array so the Layer-A claim becomes true. (a) is cheaper and matches what the data
  actually is.

## F6 — MEDIUM — nanori readings are ordered *between* kun and on, burying the reading that matters

- **Records:** 193 of 280
- **Field:** `readings[]` array order

All 280 records order reading types contiguously — but the order is **kun → nanori → on** (182 records) or
**nanori → on** (11), never kun → on → nanori.

| record | nanori rows before the first on row | on reading thus buried |
|---|---:|---|
| `kanji:理` (n4) | 16 (of 18 total rows) | **リ** — the only on reading; needed for 料理, 理由, 無理 |
| `kanji:生` (n5) | 25 (of 45) | セイ, ショウ |
| `kanji:真` (n4) | 15 (of 19) | シン — needed for 写真 |
| `kanji:海` (n4) | 15 (of 17) | カイ |
| `kanji:三` (n5) | 15 (of 20) | サン |
| `kanji:日` (n5) | 12 (of 17) | ニチ, ジツ |

- **Why it is wrong:** the file argues against its own ordering. Every one of the 108+ nanori notes says some
  variant of:
  > "Leitura de nome próprio (nanori): usada em nomes de pessoas e lugares, **não no vocabulário comum**.
  > Nenhum vocábulo desta entrada ficou agrupado nela."

  A group the record itself labels "not in common vocabulary, no examples here" should not sit between the two
  groups that *are* common vocabulary. For `kanji:理` a learner scrolls 16 example-less name readings (あや,
  おさむ, さと, さとる, ただ, ただし, とおる, に, のり, ひ, まこと, まさ, まさし, まろ, みち, よし) to reach
  リ, the single reading 料理 needs.
- **Proposed fix:** emit `ORDER BY reading_type` with the ordinal kun(0) → on(1) → nanori(2) in the exporter,
  then re-export. Pure presentation change; no data edits.

## F7 — LOW — `kanji:台` uses the abbreviation "p/" in a learner-facing meaning

- **Record:** `kanji:台` (id 1762, n4)
- **Field:** `meanings["pt-BR"][2]`

> "contador (sufixo **p/** máquinas e veículos)"

- **Why it is wrong:** it is the **only** `p/` in `corpus/kanji/{n5,n4}.json` and `corpus/vocab/{n5,n4}.json`
  combined (grep count: 1, 0, 0, 0). `corpus/vocab/n5.json` already writes the identical concept out in full —
  **"contador para máquinas e veículos"** — so the abbreviation is both unique and inconsistent with the
  corpus's own established phrasing. `design/translation_style.md` §4 asks for direct, beginner-clear pt-BR;
  a clipped `p/` in a beginner gloss is neither.
- **Proposed fix:** `"contador (sufixo para máquinas e veículos)"`.

## F8 — LOW — `kanji:文`'s irregular_note starts lowercase and undersells the irregularity

- **Record:** `kanji:文` (id 2468, n4)
- **Field:** `irregular_note["pt-BR"]`

> "o único irregular é 文字 (もじ), e ele não é tão irregular assim: o も de 文字 está listado como leitura
> deste kanji."

- **Why it is wrong:** two defects in one line. (1) It is the only one of the 47 `irregular_note` texts in the
  slice that opens lowercase; all 46 others open with a capital or a kanji. (2) The reassurance is misleading:
  も *is* listed for 文 — as a **nanori**, i.e. a name-only reading (`readings[]` for 文: nanori = かざり, ふ,
  も). A name reading turning up inside an ordinary noun like 文字 is precisely what makes it irregular. The
  corpus already handles the identical situation correctly one file over, in `kanji:木`:
  > "木綿 (もめん), "algodão", ficou fora dos grupos porque nele 木 soa como も, forma que esta entrada **só
  > registra entre as leituras de nome próprio (nanori)**."
- **Proposed fix:** mirror the 木 wording —
  > "O único irregular é 文字 (もじ): ali 文 soa como も, forma que esta entrada só registra entre as leituras
  > de nome próprio (nanori). Por isso a palavra fica fora dos grupos de leitura."

## F9 — LOW — `kanji:少`'s pt-BR meanings split a redundant pair and misalign with `en`

- **Record:** `kanji:少` (id 1331, n5)
- **Field:** `meanings`

> `"pt-BR": ["pouco", "escasso", "poucos"]` / `"en": ["few", "little", "scarce"]`

- **Why it is wrong:** index-paired, this reads pouco↔few, **escasso↔little**, **poucos↔scarce** — the last
  two are swapped. Rendered as a flat list (which is what `corpus/kanji/INDEX.md` does), "pouco, escasso,
  poucos" puts an unrelated word between two forms of the same word, which reads like an authoring slip.
- **Proposed fix:** `"pt-BR": ["poucos", "pouco", "escasso"]`, matching `en` position for position.

## F10 — LOW (cross-layer) — `kanji:京` is taught with no word at or below its own level

- **Record:** `kanji:京` (id 564, n4)
- **Field:** `example_words[]` (root cause is in `corpus/vocab/`)

> `"meanings": {"pt-BR": ["capital", "Quioto"], "en": ["capital", "Kyoto"]}`
> `example_words`: 上京 (じょうきょう, **n3**) "ir a Tóquio"; 帰京 (ききょう, **n1**) "volta à capital (Tóquio)"

- **Why it is wrong:** 京 is one of only two records in the slice with **zero** example words at or below its
  own level (the other is 主, see below), and the two it has are a paraphrase of each other. Neither **東京**
  nor **京都** appears — `grep -c 東京 corpus/vocab/*.json` returns 0 across all five files, so the kanji
  layer cannot link them. A learner is told 京 means "capital, Quioto" and then shown two words about going to
  and coming back from Tokyo, with the word 東京 itself never appearing.
- **Root cause and why it is worth revisiting:** `YOMINEKO_CORPUS_BUILD_SPEC.md:138` says of JMnedict, "proper
  names — **not needed for N5/N4, skip unless useful**." The escape hatch was written for exactly this. 東京
  is not an obscure toponym; it is the reason 京 is on the N4 list at all.
- **Proposed fix:** admit 東京 (とうきょう) and 京都 (きょうと) to `corpus/vocab/n5.json`/`n4.json` under the
  spec's "unless useful" clause, link them from `kanji:京`, and tag its on キョウ `introduced_at_level: n4`
  (currently `null`, see F3b). Related: `kanji:主` (n4) also has 0/10 at-or-below-level, and spends **three**
  of its ten slots on single-character 主 entries (おも n2, ぬし n1, しゅ n1) while `ご主人` (n4) sits unused.

---

## What I checked and found clean

| Check | Records/rows | Result |
|---|---:|---|
| `strokes` vs KANJIDIC2 | 280 | 0 mismatches |
| `grade` vs KANJIDIC2 | 280 | 0 mismatches |
| `freq_rank` vs KANJIDIC2 | 280 | 0 mismatches |
| `kangxi_radical` vs KANJIDIC2 | 280 | 0 mismatches |
| kun/on/nanori reading **sets**, okurigana reconstructed, both directions | 1 812 rows | 0 missing, 0 extra |
| Reading **type** filed correctly (no on-as-kun etc.) | 1 812 | 0 errors |
| `common: false` on every nanori | 1 812 | 0 violations |
| Reading types contiguous within the array | 280 | 0 split blocks |
| Reading `note` present and non-empty | 1 812 | 0 missing |
| Reading note vs `example_vocab_ids` ("no examples" claims) | 1 812 | 0 contradictions |
| `irregular_note` factual accuracy (jukujikun / rendaku / gemination) | 47 | 47 correct |
| `notes` field | 280 | all `null` (consistent) |
| `example_vocab_ids` resolve to a real vocab record | 671 rows | 0 dangling |
| `example_vocab_ids` also present in the record's `example_words` | 671 rows | 0 orphans |
| `example_words` headword/kana/slug vs its vocab record | 2 193 | 0 mismatches |
| `example_words` gloss vs vocab sense-0 gloss | 2 193 | 0 divergences (byte-identical) |
| `example_words` headword actually contains the kanji | 2 193 | 0 violations |
| `example_words` backed by a JMdict-uncommon vocab | 2 193 | 0 |
| Em dash (—) in any authored pt-BR text | all | 0 |
| pt-PT forms / "Quanto a" / "Vale ressaltar" tells | all | 0 |
| Trailing or doubled whitespace | all | 0 |

Thin `example_words` lists (駅 and 犬 and 秋 have exactly 1; 九, 六, 七, 川, 千, 右, 魚, 耳, 町, 銀, 春, 森, 冬,
勉, 菜, 暑 have 2) were checked and **are not defects**: for every one of them, `corpus/vocab/` contains no
other word using that kanji. The lists are as full as the vocab layer allows.

---

## Counts

| Finding | Severity | Records affected |
|---|---|---:|
| F1 duplicate `example_words` entry | HIGH | 2 |
| F2 example words skip easier in-corpus words | HIGH | 48 (31 also spend a slot on N1/N2) |
| F3 `introduced_at_level` null or contradictory | HIGH | 44 |
| F4 `kanji:屋` pt-BR drops "telhado" | MEDIUM | 1 |
| F5 `meanings.en` mislabelled as raw KANJIDIC | MEDIUM | 170 (contract/doc fix, 1 edit) |
| F6 nanori ordered between kun and on | MEDIUM | 193 (exporter fix, 1 edit) |
| F7 `kanji:台` "p/" abbreviation | LOW | 1 |
| F8 `kanji:文` irregular_note casing + framing | LOW | 1 |
| F9 `kanji:少` meaning order | LOW | 1 |
| F10 `kanji:京` no in-level example word | LOW | 1 (+`kanji:主`) |
| **Total** | **10 findings** | **75 records carry a record-specific finding; 205 clean** |

| Scope | Count |
|---|---:|
| Records assigned | 280 |
| Records read in full | 280 |
| n5 / n4 | 103 / 177 |
| `readings[]` rows checked | 1 812 |
| `example_words[]` entries checked | 2 193 |
| `irregular_note` texts verified by hand | 47 |
| Vocab records loaded for level/gloss cross-check | 7 401 |

**Priority for the teacher review queue:** F1 first (two-minute fix, and it frees the slot `お茶` needs), then
F2 and F3 together — both are exporter/selector logic, both are recoverable from data the corpus already
holds, and between them they account for 73 of the 75 flagged records, so a single re-export closes almost
the whole list. F5 is a one-line documentation correction but should not be skipped: it is the difference
between a reviewer trusting `meanings.en` blindly and knowing to spot-check it.
