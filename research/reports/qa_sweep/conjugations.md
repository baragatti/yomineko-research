# QA sweep — `corpus/conjugations/*.json`

**Scope:** `corpus/conjugations/n5.json` (212), `n4.json` (295), `n3.json` (649) = 1,156 tables / 19,784
inflected form-rows.
**Assigned sample:** every 3rd table over the concatenated n5→n4→n3 order = **386 tables / 6,644 form-rows**,
each checked field-by-field (`surface`, `kana`, `romaji`, `form`).

**Method.** I did not eyeball-only. I wrote an independent reference conjugator (godan euphonic て/た by
final kana incl. the 行く exception, う→わ a-stem, ichidan, する, 来る, i-adj, na-adj) plus an independent
kana→romaji romanizer, and diffed every sampled form against it. Every surviving diff was then adjudicated
by hand — in most cases *my reference was the naive one and the data was right*. I additionally
cross-checked every record's `class` and `kana` against the Layer-A vocab registry (`corpus/vocab/*.json`,
JMdict POS + readings), and re-ran the reference diff over **all 1,156 tables** so that class-wide errors
outside the 1-in-3 sample would not be missed. Findings surfaced only by the corpus-wide pass are marked
`[out-of-sample]`; the assignment prioritises systematic class errors, so they are reported.

Sentence `structure_explanation` fields were not touched (out of scope, being re-authored).

---

## Headline

**The conjugation engine itself is sound.** Across all 1,156 tables and 19,784 form-rows there is **not one
mis-inflected verb or adjective**. Every godan euphonic change is right (`泳ぐ→泳いで`, `休む→休んで`,
`勝つ→勝って`, `出す→出して`, `死ぬ→死んで`), `行く→行って` is special-cased, う-verbs take わ in the
a-stem (`使う→使わない`), す-godan correctly refuses the causative-passive contraction (`出させられる`),
ichidan potential/passive are the full `られる`, and 来る carries the full three-way reading alternation
(`来ます きます` / `来ない こない` / `来れば くれば`) with correct kana on every row. The irregular tables
that usually break generators are all present and correct: the special polite godan (`なさる→なさいます`,
`くださる→ください`, `おっしゃる→おっしゃいます`), the sa-hen `〜する` verbs (`達する→達します`,
`愛する→愛さない` vs `罰する→罰しない`), and the na-adj attributive exceptions (`同じ→同じ` not ×`同じな`,
`沢山→沢山の`, `本当→本当の`). Class assignment is 100% consistent with JMdict POS (0/1,156 mismatches) and
every dictionary reading matches the vocab registry (0/1,156 mismatches). The u-verb traps are all filed
correctly (`着る`/`居る`/`締める` ichidan; `要る`/`遣る` godan).

Everything below is therefore about **orthography, romaji, form-inventory policy, and pt-BR labels** —
not about wrong Japanese morphology. Two of the nine are, in my judgement, ship-blockers.

---

## C-1 — `良い` (よい): 10 of 11 forms lose the kanji, and two forms silently switch the reading to いい

**Severity: High.** `n5.json[159]` · `vocab_id 42` · `vocab:1605820` · **in-sample**

| form | `surface` | `kana` | should be |
|---|---|---|---|
| `dictionary` | 良い | よい | ✓ |
| `negative` | **よくない** | よくない | 良くない / よくない |
| `past` | **よかった** | よかった | 良かった / よかった |
| `past_negative` | **よくなかった** | よくなかった | 良くなかった |
| `te` | **よくて** | よくて | 良くて |
| `adverbial` | **よく** | よく | 良く |
| `conditional_ba` | **よければ** | よければ | 良ければ |
| `polite` | **いいです** | **いいです** | 良いです / **よいです** |
| `polite_negative` | **よくないです** | よくないです | 良くないです |
| `polite_past` | **よかったです** | よかったです | 良かったです |
| `attributive` | **いい** | **いい** | 良い / **よい** |

Two distinct bugs in one record:

1. **Kanji loss.** The record's `dictionary` surface is `良い`, but every other surface is bare kana. This is
   the only adjective in the corpus that does this (corpus-wide check: 1/272 adjective tables). A learner
   drilling 良い is shown `良い` as the prompt and `よくない` as the answer — the kanji vanishes with no
   explanation. Note this is *not* the defensible `ある→ない` case (C-6), where the negative is a different
   lexeme conventionally written in kana; `良くない` is standard orthography and `良い` is marked
   `is_common: true` in `corpus/vocab/n5.json`.
2. **Reading drift — the harder error.** `polite` and `attributive` carry `kana: いいです` / `kana: いい`
   inside a record whose own `kana` is `よい`. The record now asserts that 良い is read *ii*. It is read
   *yoi*; `いい` is a separate (suppletive) form with **its own table already in the corpus** —
   `n5.json[0]`, `vocab_id 1335`, `vocab:2820690`. The two records have been cross-contaminated.

This is the only reading-drift case in the corpus (corpus-wide scan for form-kana that does not share its
record's stem returns 良い plus the legitimate irregulars 来る/する/ある/〜する).

It has already propagated into the exercise bank: `cj:n5:42:attributive` has `prompt: 良い` with
`correct: いい`, and `cj:n5:42:polite` has `prompt: 良い` with `correct: いいです`.

**Fix.** Give `vocab_id 42` its own regular い-adjective paradigm on the `良` stem —
`良い / 良くない / 良かった / 良くなかった / 良くて / 良く / 良ければ / 良いです / 良くないです /
良かったです / 良い`, with kana `よい / よくない / … / よいです / よい`. Leave `vocab_id 1335` (`いい`) as
it stands; its suppletive よ- stem is correct *there*. The two records must not share a code path.

---

## C-2 — Katakana long vowel ー emitted as a literal ASCII hyphen in `romaji`

**Severity: High.** 8 records, **152 form-rows**. `[out-of-sample]` — every affected record fell outside the
1-in-3 stride; found by the corpus-wide romaji pass.

| location | `vocab_id` | headword | `kana` | `romaji` (as shipped) | should be |
|---|---|---|---|---|---|
| `n5.json[2]` | 259 | コピー | コピーする | `kopi-suru` | `kopiisuru` |
| `n4.json[6]` | 770 | レポート | レポートする | `repo-tosuru` | `repootosuru` |
| `n3.json[13]` | 1873 | コーチ | コーチする | `ko-chisuru` | `koochisuru` |
| `n3.json[14]` | 1877 | ゴール | ゴールする | `go-rusuru` | `goorusuru` |
| `n3.json[16]` | 1916 | サービス | サービスする | `sa-bisusuru` | `saabisusuru` |
| `n3.json[17]` | 2155 | スケート | スケートする | `suke-tosuru` | `sukeetosuru` |
| `n3.json[19]` | 2412 | デート | デートする | `de-tosuru` | `deetosuru` |
| `n3.json[25]` | 2775 | マスター | マスターする | `masuta-suru` | `masutaasuru` |

All 19 forms of each record are affected (19 × 8 = 152).

**Why it is wrong.** `-` is not a romanization of anything. The romanizer maps every kana through a table
and has no entry for the chōonpu `ー`, so the character survives into the output. A Brazilian learner reading
`kopi-suru` gets a hyphen where a long vowel belongs and will say *có-pi-su-ru* instead of *kopī-suru* —
vowel length is phonemic in Japanese, so this is a pronunciation error, not a cosmetic one. It is also
internally inconsistent: the corpus already romanizes long vowels by **vowel doubling** everywhere else
(`大きい → ookii`, `必要 → hitsuyou`, `勉強 → benkyou`), so `ー` is the only long vowel not handled.

**Fix.** In the romanizer, expand `ー` to a repeat of the preceding syllable's vowel, matching the existing
doubling convention (`kopiisuru`, not `kopīsuru` — the corpus does not use macrons anywhere). Then
re-export; the 152 rows also flow into `corpus/exercises/conjugation/*.json`.

---

## C-3 — Hepburn apostrophe dropped in exactly two forms, corrupting the reading

**Severity: Medium.** 7 records, **14 form-rows**. 2 in-sample (`翻訳`, `引用`), 5 `[out-of-sample]`.

Every record whose kana contains an ん + vowel/y juncture carries the disambiguating apostrophe in **17 of
its 19 forms** — and loses it in exactly `past_negative` and `volitional_polite`:

```
n3.json[455]  vocab_id 1746  禁煙 (きんえん)
  negative           きんえんしない        kin'enshinai        ✓
  past               きんえんした          kin'enshita         ✓
  masu               きんえんします        kin'enshimasu       ✓
  past_negative      きんえんしなかった    kinenshinakatta     ✗  (should be kin'enshinakatta)
  volitional_polite  きんえんしましょう    kinenshimashou      ✗  (should be kin'enshimashou)
```

Same pattern, same two forms, all seven records:

| location | `vocab_id` | word | broken `past_negative` | broken `volitional_polite` |
|---|---|---|---|---|
| `n4.json[54]` | 919 | 原因 げんいん | `geninshinakatta` | `geninshimashou` |
| `n4.json[220]` | 1301 | 翻訳 ほんやく | `honyakushinakatta` | `honyakushimashou` |
| `n3.json[10]` | 2761 | ぼんやり | `bonyarishinakatta` | `bonyarishimashou` |
| `n3.json[80]` | 2137 | 信用 しんよう | `shinyoushinakatta` | `shinyoushimashou` |
| `n3.json[196]` | 1913 | 婚約 こんやく | `konyakushinakatta` | `konyakushimashou` |
| `n3.json[243]` | 1471 | 引用 いんよう | `inyoushinakatta` | `inyoushimashou` |
| `n3.json[455]` | 1746 | 禁煙 きんえん | `kinenshinakatta` | `kinenshimashou` |

**Why it matters.** The apostrophe is the only thing separating ん+vowel from a plain syllable.
`kinenshinakatta` parses as き-ね-ん-… (*kinen*, 記念 "comemoração") rather than き-ん-え-ん (*kin'en*,
禁煙 "proibido fumar"). `honyakushimashou` reads *ho-nya-ku* instead of *hon-ya-ku*. The learner is handed a
romaji string that decodes to a different word.

That the same record gets it right in 17 forms and wrong in 2 points at a specific code path: these two
forms are almost certainly built by string-surgery on another form's *romaji* (e.g. `past_negative` from
`negative` by swapping the `nai` tail, `volitional_polite` from `masu`) instead of being re-romanized from
their own kana.

**Fix.** Derive `romaji` for every form from that form's own `kana` through the single romanizer, never by
mutating a sibling form's romaji string. A cheap regression guard: assert that
`romaji == romanize(kana)` for all 19 forms of every record.

---

## C-4 — 17 tables are rendered end-to-end in an orthography the corpus's own Layer-A data marks uncommon

**Severity: Medium.** 16 tables (6 in-sample), out of 17 records where the primary and common written forms
disagree — the 17th (`為る`) is handled correctly and is the proof the fix is cheap, see below.

The generator takes `surface` from the vocab record's `is_primary` form and ignores `is_common`. Where those
disagree, every surface in the table is written in a form the corpus itself flags as not-common while a
common form exists in the same record:

```
n3.json[102]  vocab_id 2000  凝乎と (じっと)   forms: [('凝乎と', primary, NOT common), ('じっと', common)]
  surface: 凝乎とする 凝乎とします 凝乎としません … 凝乎としろ 凝乎とすれば
  kana:    じっとする じっとします じっとしません … じっとしろ じっとすれば
```

`凝乎と` is ateji that essentially never appears in modern text; the whole `surface` column is unreadable
for the exact learner it is aimed at. Full list:

| location | `vocab_id` | headword (shipped `surface` stem) | common form per `corpus/vocab` | in sample |
|---|---|---|---|---|
| `n5.json[66]` | 69 | 居る | いる | ✔ |
| `n5.json[189]` | 653 | 遣る | やる | ✔ |
| `n4.json[26]` | 875 | 仕舞う | しまう | |
| `n4.json[61]` | 911 | 可笑しい | おかしい | ✔ |
| `n4.json[63]` | 1073 | 吃驚 | びっくり | |
| `n4.json[90]` | 759 | 居らっしゃる | いらっしゃる | |
| `n4.json[172]` | 886 | 為さる → `為さいます`, `為さい` | なさる | ✔ |
| `n4.json[204]` | 702 | 確り | しっかり | |
| `n4.json[294]` | 1144 | **ＦＡＸ** → `ＦＡＸします` | ファックス / ファクス | |
| `n3.json[7]` | 2492 | とんでも無い → `とんでも無くなかった` | とんでもない | |
| `n3.json[102]` | 2000 | 凝乎と | じっと | ✔ |
| `n3.json[144]` | 1628 | 可也 → `可也な`, `可也に` | かなり | ✔ |
| `n3.json[170]` | 1474 | 嗽 → `嗽する` | うがい | |
| `n3.json[250]` | 1381 | 彼方此方 | あちこち | |
| `n3.json[289]` | 2696 | 打つ (ぶつ) | ぶつ | |
| `n3.json[500]` | 1413 | 行けない | いけない | |

Worst two for a beginner course: **`ＦＡＸ`** ships full-width Latin as the drill answer
(`ＦＡＸします`, `ＦＡＸさせられる`) where the reading is ファックス — a learner cannot type that, and it is
neither the kanji nor the kana they will meet; and **`可也`** (n3, na-adj) drills `可也だ / 可也な / 可也に`
for a word written かなり in effectively all modern text.

**This is fixable with machinery that already exists.** `n4.json[173]` (`為る`, `vocab_id 1358`) is the same
situation — primary form `為る`, common form `する` — and it is handled correctly: every surface is emitted
in kana (`する`, `します`, `して`, …). The rule is implemented; it just is not applied to the other 17.

**Fix.** When selecting the surface orthography, prefer a `forms[]` entry with `is_common: true` over
`is_primary: true` when the primary is `is_common: false`, exactly as `為る` already does.

---

## C-5 — `打つ` produces two tables with identical surfaces and different readings

**Severity: Medium.** `n4.json[116]` (`vocab_id 1044`, うつ) and `n3.json[289]` (`vocab_id 2696`, ぶつ).
`[out-of-sample]`

Both records emit the same `surface` column, character for character:

```
n4  vocab_id 1044  打つ (うつ):  打つ 打ちます … 打って 打った    kana: うつ うちます … うって うった
n3  vocab_id 2696  打つ (ぶつ):  打つ 打ちます … 打って 打った    kana: ぶつ ぶちます … ぶって ぶった
```

In the exercise bank this becomes two items with the same prompt and the same correct answer but
contradictory readings:

```
cj:n4:1044:masu   prompt 打つ  →  打ちます  うちます  uchimasu
cj:n3:2696:masu   prompt 打つ  →  打ちます  ぶちます  buchimasu
```

The learner is shown `打つ`, answers `打ちます`, and is told the reading is *buchimasu* or *uchimasu*
depending on which of two indistinguishable cards came up. `ぶつ` is also a C-4 case — `corpus/vocab`
marks the kanji surface `打つ` as `is_common: false` for `vocab_id 2696`, with `ぶつ` as the common form.

**Fix.** Applying C-4 resolves this by itself: `vocab_id 2696` renders as `ぶつ / ぶちます / ぶって`, which
both matches real orthography and removes the collision. Separately, worth adding a corpus-wide assertion
that no two conjugation records share an identical `surface` set.

---

## C-6 — Form-inventory suppression is applied inconsistently

**Severity: Medium.** `n5.json[32]` (`vocab_id 418`, 出来る) and `n5.json[102]` (`vocab_id 39`, 有る).
`有る` in-sample.

These are the only two verbs in the corpus with a 17-form table instead of 19: `potential` and `passive` were
deliberately dropped, which is the right call (できる *is* the potential of する; ある has no passive). But the
same tables retain forms that are just as non-occurring:

```
n5.json[32]  出来る (できる)
  imperative         出来ろ        できろ          ← not used
  causative          出来させる    できさせる      ← not used ("make able to" is できるようにさせる)
  causative_passive  出来させられる できさせられる  ← not used

n5.json[102]  有る (ある)
  causative          有らせる      あらせる        ← archaic; survives only in honorific あらせられる
```

If the generator knows できる is non-volitional enough to suppress the potential, the volitional-only forms
(`imperative`, `causative`, `causative_passive`) should go with them. All of these are live in the exercise
bank as correct answers — `cj:n5:418:imperative → 出来ろ`, `cj:n5:418:causative → 出来させる`.

Two secondary notes on the same records, both **not** defects: `ある`'s `negative` / `past_negative` /
`negative_te` correctly give `ない / なかった / なくて` in kana (a genuinely suppletive form conventionally
written in kana — unlike C-1), and `出来る` keeps its kanji legitimately since `corpus/vocab` marks both
`出来る` and `できる` as common.

**Fix.** Extend the existing per-lexeme suppression list for `vocab_id 418` to also drop `imperative`,
`causative`, `causative_passive`, and for `vocab_id 39` to drop `causative` / `causative_passive`. The
mechanism is already there — only the entries need widening.

---

## C-7 — Four form labels ship the raw English enum key to pt-BR learners

**Severity: Medium.** 2,312 rows. Cross-file: the conjugation bank itself carries no labels (form keys are
neutral enums, which is correct per `design/i18n.md`); the pt-BR labels live in
`corpus/exercises/conjugation/{n5,n4,n3}_conjugation.json`. Reported here because the assignment covers form
labels and the defect is keyed by these form enums.

Every other form is properly localized (`masu` → `"forma ます (polida)"`, `causative_passive` →
`"causativa passiva"`, `conditional_tara` → `"condicional たら"`). These four are not translated at all —
`form_label["pt-BR"]` is byte-identical to the English enum:

| kind | `form` | shipped `form_label["pt-BR"]` | rows | example id |
|---|---|---|---|---|
| verb | `negative_te` | `"negative_te"` | 884 | `cj:n5:2:negative_te` |
| verb | `volitional_polite` | `"volitional_polite"` | 884 | `cj:n5:2:volitional_polite` |
| adjective | `polite_negative` | `"polite_negative"` | 272 | `cj:n5:4:polite_negative` |
| adjective | `polite_past` | `"polite_past"` | 272 | `cj:n5:4:polite_past` |

This violates the project's hard language rule (`CLAUDE.md`: all learner-facing content is pt-BR; only
internal enums stay English). A Brazilian beginner is shown the instruction "volitional_polite".

**Fix.** Following the register and the ば/たら parenthetical convention already used by the neighbouring
labels: `negative_te` → `"forma て negativa (なくて)"`; `volitional_polite` → `"volitiva polida (ましょう)"`;
`polite_negative` → `"negativa polida"`; `polite_past` → `"passado polido"`.

*(Not a defect: adjective `adverbial` → `"adverbial"` is also byte-identical to the enum, but "adverbial" is
a correct pt-BR word — `forma adverbial` — so it reads fine. Excluded from the 2,312.)*

---

## C-8 — na-adjective `conditional_ba` is uniformly `なら`, under a label that says ば

**Severity: Low.** All 167 na-adjective tables.

Corpus-wide, the na-adj `conditional_ba` suffix is `なら` in 167/167 records — `静かなら`, `簡単なら`,
`大切なら`. The pt-BR label for that enum in the exercise bank is `"condicional ば"`. There is no ば in the
answer.

The label is right for い-adjectives under the same enum (`高ければ`, `良ければ`) and for verbs
(`行けば`), so a learner comparing the three tables sees the label contradicted in exactly one of them.

**Fix.** Either emit `ならば` (the actual ば-conditional) as the value, or — better, since `なら` is what is
actually taught and used — give the na-adj branch its own label, `"condicional なら"`. The label map is
already per-`kind` (verb and adjective labels differ for `negative`), so this needs no schema change.

---

## C-9 — `死ね` ships as a drill answer

**Severity: Low (content, not correctness).** `n5.json[111]` · `vocab_id 295` · **in-sample**

The morphology is correct — `死ぬ` is a regular ぬ-godan and `死ね` is its imperative. But in the exercise
bank this surfaces as:

```
cj:n5:295:imperative   prompt 死ぬ  →  correct: 死ね   しね   shine
                       distractors: ['死ぬ', '死ねば', '死んで']
```

`死ね` is not a neutral imperative in Japanese; it functions as a slur. A beginner course asking a learner to
*produce* it as the correct answer is a product risk that has nothing to do with grammar. The rest of the
`死ぬ` table (`死にます`, `死んで`, `死んだ`) is unproblematic and worth keeping.

**Fix.** Suppress `imperative` for `vocab_id 295` in the exercise bank (the table itself can retain the form
for reference). This is the same per-lexeme suppression mechanism as C-6.

---

## Verified clean (no findings)

- **Godan euphony**, all nine endings, sampled and corpus-wide: う/つ/る→って, む/ぶ/ぬ→んで, く→いて,
  ぐ→いで, す→して; `行く→行って` special-cased; ある/なさる/くださる/おっしゃる all correct.
- **a-stem, e-stem, o-stem derivations**: negative う→わ, potential, imperative, `conditional_ba`,
  volitional — 0 errors.
- **Ichidan**: potential and passive both `られる` (textbook form, no ら抜き) — consistent, 0 errors.
- **する / 来る / sa-hen `〜する`**: 来る's three-way reading alternation correct on every row; `愛さない` vs
  `罰しない` distinguished; `潜在 potential → できる` for compounds vs `〜せる` for sa-hen.
- **i-adjective and na-adjective paradigms**, incl. the exception table (`同じ→同じ`, `沢山→沢山の`,
  `本当→本当の`, `沢山` adverbial with no に).
- **Class assignment vs JMdict POS**: 0 mismatches / 1,156. u-verb traps all filed right.
- **Dictionary readings vs `corpus/vocab`**: 0 mismatches / 1,156.
- **`kana` field purity**: 0 records with kanji leaking into `kana`.
- **Romaji** outside C-2/C-3: correct throughout, including `tsu`/`shi`/`chi`/`fu`/`ji`, っ gemination
  (`gatte`, `nesshin`), yōon (`shimashou`, `nyuugaku`), and ん+vowel apostrophes in 17 of 19 forms.
- **Schema**: uniform key set across all 1,156 records; only 3 distinct form-sequences, all accounted for.

---

## Counts

| | |
|---|---:|
| Tables in assignment scope | 1,156 |
| **Tables checked in full (every 3rd, as assigned)** | **386** |
| Form-rows checked in full | 6,644 |
| Tables additionally scanned corpus-wide for class-level errors | 1,156 |
| Form-rows scanned corpus-wide | 19,784 |
| **Findings flagged** | **9** |
| — High | 2 (C-1, C-2) |
| — Medium | 5 (C-3, C-4, C-5, C-6, C-7) |
| — Low | 2 (C-8, C-9) |
| Findings inside the 1-in-3 sample | 5 (C-1, C-4 partial, C-3 partial, C-6 partial, C-9) |
| Findings surfaced only by the corpus-wide pass | 4 (C-2, C-5, and the majority of C-3 / C-4) |
| Mis-inflected forms found (wrong Japanese morphology) | **0** |
| Affected form-rows, C-2 | 152 |
| Affected form-rows, C-3 | 14 |
| Affected tables, C-4 | 16 |
| Affected exercise rows, C-7 | 2,312 |
