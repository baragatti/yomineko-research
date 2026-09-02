# Vocab identity queue — records whose slug points at the wrong JMdict entry

**Status: NOT APPLIED. Owner decision required.**

`vocab:<jmdict_id>` is a published address. Re-pointing a slug is not a field edit — it is a migration that
touches every reference in `db/corpus.sqlite` and in the committed `corpus/` + `course/` exports. This file
records what the evidence says, so the migration can be planned and costed; the accompanying repair pass
(`scripts/apply_vocab_gloss_repairs.py`) deliberately leaves all 22 records below untouched.

Source finding: [`vocab_glosses.md`](vocab_glosses.md) **F1**. Everything here was re-derived independently
against `research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip` and the consensus lists in
`research/datasets/jlpt/` (`openanki_vocab_{n5,n4}.csv`, `jlptvocabapi_{n5,n4}.json`,
`bluskyo_vocab_{n5,n4}.csv`), plus a full sweep of all 7,401 vocab records to confirm the collateral damage.

---

## The defect

The ingest chose a JMdict entry by **reading alone**. Where the source list row was kana-keyed
(`openanki_vocab_n5.csv` row `はい,はい,"yes"`), the list's own `meaning` column was available in the same
row and was ignored. The result is a homophone: the right reading attached to the wrong lemma. The reading
consensus was sound, which is why `level_confidence: 1.0` / `level_agreement: 4/4` sits on eleven of these —
the confidence field is measuring agreement about the *reading*, so on these records it is actively
misleading.

## Confirmed re-pointings

`list says` is the meaning column of the source list row that produced the level tag, quoted verbatim.
`collateral` is what the wrong resolution cost, verified against all 7,401 records.

| id | slug | corpus lemma / gloss | list says | collateral |
|---|---|---|---|---|
| 502 | `vocab:1472870` | 肺 はい — "pulmão" | openanki n5 `はい` = **"yes"** | はい "sim" absent from all 7,401 records (はい resolves only to 肺 n5 and 灰 n3) |
| 434 | `vocab:1451160` | 動 どう — "movimento" | openanki n5 `どう` = **"how, in what way"** | どう absent (どうですか is week-1 material) |
| 479 | `vocab:1611000` | 生る なる — "dar fruto" | openanki n5 `なる` = **"to become"** | 成る sits at **n3** (id 2517); "tornar-se" unreachable at N5 |
| 334 | `vocab:1298670` | 刷る する — "imprimir" | openanki n5 `する` = **"to do, to try; to wear small items"** | する at N5 absent; 為る only at n4 (id 1358) |
| 148 | `vocab:1609500` | 罹る かかる — "pegar (doença)" | openanki n5 `かかる` = **"it takes (amount of time, money)"** | 掛かる sits at **n3** (id 1584) |
| 154 | `vocab:1570710` | 翔る かける — "voar (pelo céu)" | openanki n5 `かける` = **"to dial/call; to sit down"** and `掛ける` = "to put on / to hang" | duplicate reading of id 153 掛ける, already present at n5 |
| 507 | `vocab:1474240` | 伯 はく — "conde" | openanki n5 `はく` = **"to put on (items below your waist)"** | 履く sits at **n3** (id 2581); 穿く absent everywhere |
| 376 | `vocab:1341840` | 盾 たて — "escudo" | openanki n5 `たて` = **"length, height"** | 縦 sits at **n3** (id 2306) |
| 355 | `vocab:1176240` | 園 その — "jardim" | openanki n5 `その` = **"that"** | the demonstrative その is absent while この (257) and あの (31) are present |
| 1347 | `vocab:1515620` | 報 ほう — "relatório" | bluskyo n5 lists bare kana `ほう` beside `より` | 方/ほう sits at **n3** (id 2731), so 〜のほうが〜より cannot be built at N5 |
| 349 | `vocab:1401470` | 総 そう — "total, geral" | openanki n4 `そう` = **"really, (is that) so; yes, right"** | そう absent (2/4 agreement; the record itself is also level-split n5/n4) |
| 1343 | `vocab:1523040` | 本島 ほんとう — "ilha principal" | openanki n5 lists `本当` = **"real, true"** | duplicate reading of id 593 本当, already present at n5 |
| 374 | `vocab:1551240` | 立ち たち — "partida" | list row is bare kana `たち` | **達 does not exist in any of the 7,401 records** (私たち unbuildable) |
| 503 | `vocab:1472630` | 杯 さかずき — "cálice de saquê" | list entry `杯` is the counter **はい** | the counter 杯 absent; note this record also carries 12 `forms` |
| 1086 | `vocab:1272630` | 侯 こう — "marquês" | openanki n4 `こう` = **"like this, this way"** | こう absent |
| 699 | `vocab:1855690` | 等々 とうとう — "e assim por diante" | openanki n4 `とうとう` = **"finally, at last"** | 到頭 absent |
| 1223 | `vocab:1208680` | 滑降 かっこう — "descida (esqui)" | openanki n4 `かっこう` lists **格好** "appearance, manner, shape" | duplicate reading of id 1334 格好, already present at n4 |
| 1350 | `vocab:1241450` | 琴 こと — "koto" | openanki n4 `こと` lists **事** "thing(s), matter(s)" | duplicate reading of id 887 事, already present at n4 |
| 1359 | `vocab:1630770` | 献花 けんか — "oferenda de flores" | bluskyo n4 lists bare kana `けんか` | 喧嘩 sits at **n3** (id 1825) |
| 842 | `vocab:1258830` | 県下 けんか — "na província" | same `けんか` slot, resolved a second wrong way | — (the two records split one list slot between them) |
| 745 | `vocab:1172610` | 運 うん — "sorte" | openanki n4 `うん` = **"yes (informal), all right"** | うん absent. 運 itself is defensible vocabulary; the *slot* was うん |

**Lower confidence, same shape:** **94** `vocab:1485770` 尾 お "cauda" — 2/4 agreement, no list row keyed
by `お` in any of the three lists carried in the repo (the level came from `elzup` + `openanki`, and the
standalone `お` in a beginner list is the honorific prefix). 御/お already sits at **n3** (id 1512) and
御/ご at n4 (id 1202). Treat as a candidate, not a confirmed re-pointing.

## What the migration costs

Reference counts as of this pass. "export refs" counts occurrences of the slug string across the 543
committed JSON files under `corpus/` and `course/` (the large course numbers are the per-lesson
`cumulative_known_set` arrays, which name every previously-unlocked slug).

| id | slug | headword / kana | sentence_vocab | token | lesson_introduces | family_member | export refs (corpus+course) |
|---|---|---|---:|---:|---:|---:|---:|
| 502 | `vocab:1472870` | 肺 / はい | 11 | 4 | 1 | 1 | 238 (10+228) |
| 434 | `vocab:1451160` | 動 / どう | 85 | 86 | 1 | 1 | 366 (118+248) |
| 479 | `vocab:1611000` | 生る / なる | 253 | 263 | 1 | 2 | 590 (356+234) |
| 334 | `vocab:1298670` | 刷る / する | 228 | 60 | 1 | 1 | 463 (199+264) |
| 148 | `vocab:1609500` | 罹る / かかる | 38 | 38 | 1 | 1 | 344 (81+263) |
| 154 | `vocab:1570710` | 翔る / かける | 6 | 3 | 1 | 1 | 289 (26+263) |
| 507 | `vocab:1474240` | 伯 / はく | 7 | 7 | 1 | 1 | 239 (11+228) |
| 376 | `vocab:1341840` | 盾 / たて | 5 | 3 | 1 | 1 | 267 (8+259) |
| 355 | `vocab:1176240` | 園 / その | 150 | 150 | 1 | 1 | 449 (190+259) |
| 1347 | `vocab:1515620` | 報 / ほう | 39 | 39 | 1 | 1 | 270 (56+214) |
| 349 | `vocab:1401470` | 総 / そう | 77 | 77 | 1 | 1 | 352 (99+253) |
| 1343 | `vocab:1523040` | 本島 / ほんとう | 3 | 3 | 1 | 1 | 218 (7+211) |
| 374 | `vocab:1551240` | 立ち / たち | 15 | 0 | 1 | 1 | 267 (10+257) |
| 503 | `vocab:1472630` | 杯 / さかずき | 6 | 6 | 1 | 1 | 242 (13+229) |
| 1086 | `vocab:1272630` | 侯 / こう | 6 | 6 | 1 | 1 | 164 (15+149) |
| 699 | `vocab:1855690` | 等々 / とうとう | 5 | 5 | 1 | 1 | 213 (14+199) |
| 1223 | `vocab:1208680` | 滑降 / かっこう | 5 | 5 | 1 | 2 | 162 (32+130) |
| 1350 | `vocab:1241450` | 琴 / こと | 268 | 3 | 1 | 1 | 167 (47+120) |
| 1359 | `vocab:1630770` | 献花 / けんか | 3 | 2 | 1 | 1 | 134 (28+106) |
| 842 | `vocab:1258830` | 県下 / けんか | 7 | 1 | 1 | 1 | 190 (10+180) |
| 745 | `vocab:1172610` | 運 / うん | 5 | 5 | 1 | 1 | 214 (14+200) |
| 94 | `vocab:1485770` | 尾 / お | 203 | 5 | 1 | 1 | 317 (33+284) |

Totals: 1,415 `sentence_vocab` links, 766 `token.vocab_id` links, 22 `lesson_introduces` rows,
24 `family_member` rows, 22 `lesson_unlocks` rows, 5,955 slug occurrences across the exports.

`sentence_vocab` is the number that decides the shape of the migration. 479 生る (253), 1350 琴 (268),
355 園 (150) and 94 尾 (203) are wired into hundreds of dissected sentences. Those links were made by
surface/reading matching, so most of them are almost certainly links to the *intended* word
(なる "to become", こと "matter", その "that") rather than to the lemma the record actually holds — which
means re-pointing the slug will make the majority of those links correct rather than breaking them. That has
to be checked per link, not assumed.

## Two ways to migrate — the choice is the owner's

1. **Re-point in place.** Keep `vocab.id`, change `slug` / `jmdict_ref` / `headword` / `kana` / forms /
   senses to the intended entry. Cheapest for the graph (every `vocab_id` FK survives) but the published
   `vocab:<jmdict_id>` address changes meaning under anyone who already stored it, and `sentence_vocab` /
   `token` links must be re-verified one by one.
2. **Deprecate and add.** Leave the existing record where it is (correctly describing 肺, 動, 運 …) at
   whatever level it belongs to, and ingest the intended word as a new record. No address changes; costs a
   level re-tag on the old record and a full ingest for ~13 new headwords (はい, どう, 成る, する, 掛かる,
   履く, 縦, その, 方, そう, 達, 杯 (counter), こう, 到頭, 喧嘩, うん — and 掛ける / 本当 / 格好 / 事 already
   exist, so 154, 1343, 1223 and 1350 are pure deletions or level moves rather than additions).

Either way the prerequisite is the same and is stated in F1: **re-run lemma resolution scoring JMdict
candidates against the list's own `meaning` string**, and where the list row carries a written form
(`openanki.expression`, `bluskyo.Kanji`), require the chosen entry to contain that form.

## Level tags are a separate owner decision

Not touched here either. `level_confidence: 1.0` / `level_agreement: 4/4` on eleven of these records is
wrong in substance but right by the formula — the four lists genuinely agreed on the reading. Fixing that
means changing what the confidence formula measures (reading agreement vs lemma agreement), which is a
change to `design/` and to `validate_level_consensus.py`, not a per-record edit.

---

## Also deferred by the same pass — not identity, still not per-record

Recorded here so the queue is the single place to look. None of these were applied.

- **F3 (156 records) and F10 (15 records) — `headword` re-derivation.** Not applied because `headword` is
  itself an address: `lesson_unlocks.ref` is `vocab:<headword>` (all 1,343 distinct n5/n4 headwords appear
  there, verified), `validate_groundtruth.py` F2 asserts `vocab_kanji` edges equal the kanji in `headword`,
  and `vocab_form.is_primary` must stay the single form equal to `headword`. Changing 咖哩→カレー or ５日→五日
  therefore rewrites the unlock ledger and the kanji↔vocab graph as well as the record. Same class of
  migration as the table above.
- **F4 (1,946 senses) and F5 (51 records) — `misc_tags` / `register`.** `register` is not stored; the
  exporter derives it from `vocab_sense.misc_tags` (`REGISTER_MAP` in `scripts/export/export_corpus.py`), so
  F5 is entirely downstream of F4 and the report's own prescribed fix is an exporter/ingest change. Filling
  `misc` per record needs a corpus-sense → JMdict-sense alignment that does not currently exist: the corpus
  `gloss_en` are condensed paraphrases, not verbatim JMdict, and a gloss-overlap match leaves **451 of the
  1,947 senses** with no confident JMdict sense at all. A partial fill would also be worse than none — it
  would make an empty `misc` ambiguous between "JMdict has no tags" and "we did not carry them".
- **F6 (485 forms) — `sK`/`sk` search-only spellings in `forms`.** `vocab_form` has no tag column and the
  exporter emits `{form, is_kana, is_common, is_primary}`. Carrying JMdict form tags is a schema migration
  plus a contract change, not a data edit.
- **F9 (48 records) — romaji for ー and word-final っ.** The `-` for chōonpu and `xtsu` for a solitary っ are
  the corpus's *stated* convention, implemented in the shared `kana2romaji` of
  `scripts/validate/validate_groundtruth.py` and mirrored in `validate_conjugation_exercises.py`. Vocab
  romaji, token romaji, sentence romaji and the conjugation banks all use it. Changing it is a
  project-wide convention decision; changing only the 48 vocab records would desync them from the banks.
