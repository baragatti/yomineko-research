# W09 — Vocab identity re-point (owner decision A9)

_Executed 2026-09-03. Scope: `research/reports/APP_PLAN.md` W09, closing the address half of the
readiness finding behind `research/reports/qa_sweep/vocab_identity_queue.md` — 22 records (plus a
23rd at lower confidence) whose `vocab:<jmdict_id>` slug names a JMdict entry that is **not** the
word the JLPT list slot meant. The owner chose option (a): re-point in place, redirect kept, and
**the lessons must not degrade**._

**Method.** The migration is `scripts/migrate_vocab_repoint.py` (dry run by default, `--apply`,
`--check`, `--db`/`--root` redirectable, idempotent). Every number below was measured on disk in this
run: the reference counts come from the applied ledger `research/derived/vocab_repoint_ledger.json`,
the degradation verdict from a byte-level before/after comparison of a full export on a **copy** of
the tree — the lesson JSON *and* the rendered `lesson-NN.md`, which is where the one real degradation
surfaced (§4.1) — and the validator lines from that same copy. The real tree was **not** exported
here; the orchestrator exports.

---

## 1. What was re-pointed: 8 of 22

Each target was confirmed against the tracked dictionary
(`research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip`, inner file
`jmdict-eng-3.6.2.json`, SHA256 `5fd4dd96…c98ecb`, version 3.6.2, dictDate 2026-06-08) before use.
Seven of the eight targets are also present in the corpus's own Layer-A table `raw_jmdict_entry` and
were byte-compared against it; the eighth (`2019640`) is not flagged *common*, so it is absent from
the common-set tarball the table is built from and is carried verbatim in the migration's
`JMDICT_EXTRA`, then inserted so `source: jmdict:2019640` stays verifiable against the corpus.

| id | old address | new address | old lexeme | new lexeme | the list row that decides it |
|---:|---|---|---|---|---|
| 502 | `vocab:1472870` | `vocab:1010080` | 肺 / はい | はい / はい | n5 `はい,はい,yes` — every n5 row keyed はい is the interjection; 肺 is carried at n1 and n3 |
| 355 | `vocab:1176240` | `vocab:1006830` | 園 / その | 其の / その | n5 `その,その,that` — the demonstrative; 園/その is n1 in bluskyo |
| 349 | `vocab:1401470` | `vocab:2137720` | 総 / そう | 然う / そう | n5 line 359 + n4 line 78, both rows for the adverb そう; 総/そう is n1 |
| 374 | `vocab:1551240` | `vocab:1416220` | 立ち / たち | 達 / たち | n5 `～たち,～たち,plural suffix` — the ～ is stripped by the ingest's own normaliser |
| 503 | `vocab:1472630` | `vocab:2019640` | 杯 / さかずき | 杯 / はい | n5 line 521 `～杯,～はい,counter for cupfuls`; 杯/さかずき is n1 in two lists |
| 1086 | `vocab:1272630` | `vocab:1004310` | 侯 / こう | 斯う / こう | n4 `こう,こう,"like this, this way"`; 侯 is an n1 kanji in no n4 vocabulary list |
| 699 | `vocab:1855690` | `vocab:1449890` | 等々 / とうとう | 到頭 / とうとう | n4 `とうとう,とうとう,"finally, at last"` — 到頭, not 等々 "and so on" |
| 745 | `vocab:1172610` | `vocab:1001090` | 運 / うん | うん / うん | n4 `うん,うん,"yes (informal)"`; every list that carries 運/うん puts it at **n3** |

`vocab:<headword>` is the courseware's other address for a word, so seven headwords moved with the
slug (`vocab:肺` → `vocab:はい`, …). 503 is the exception: 杯 is the first kanji form of the counter
entry too, so its headword ref never moved.

**The eight new headwords are what the corpus's own ingest rule produces** (`headword = first kanji
form`, `scripts/ingest/reconcile_levels.py`), which is why four of them are the rare kanji spelling
of a `uk` word (其の, 然う, 斯う, 到頭). Changing that rule is a headword-shape decision and is not
W09's to take — it is exactly the decision the refusal of 434 動 (§3) is waiting on.

### 1.1 What the re-point costs, stated plainly

The vocab **row** survives, so every `vocab_id` foreign key, family membership, lesson slot and SRS
card survives; its **identity** is replaced. The old lexeme therefore leaves the corpus — it is not
retired to an archive row, it is overwritten. That is inherent to option (a). The complete
pre-migration record (row, forms, senses, both locales, pitch, kanji edges, level evidence) is
written to `research/derived/vocab_repoint_ledger.json` before anything is touched, and the old
address stays resolvable through `vocab.repointed_from` → `corpus/vocab_redirects.json`.

Two of the overwritten lexemes are attested elsewhere by the same lists and should be re-ingested
there: **運/うん at n3** (all four lists) and **園/その at n1** (bluskyo). The ledger says so per
record; neither is at that level today.

Three Layer-A facts move rather than survive:

- **senses** — replaced wholesale by the target entry's, with pt-BR re-authored from the target's own
  JMdict glosses (Layer B, `needs_review: 1`). There is no survivor to salvage into: 「pulmão」 is not
  a meaning of はい, and an empty locale object is not publishable (`contracts/vocab.schema.json`).
  Everything dropped is in the ledger's `content_loss`.
- **freq_rank** — **re-derived** for the new written form from
  `research/derived/frequency/tatoeba_lemma_freq.json`, by `build_frequency.py`'s own rule. Carrying
  the number over would be exactly the stale fact this migration exists to remove: 8158 ranks the
  written form 肺, and the record is about to stop being 肺. Changes: 502 8158→1000, 355
  11700→11609, 349 10050→∅, 374 13665→365, 503 1199→1199, 1086 ∅→∅, 699 1768→∅, 745 1712→1104.
- **misc/field tags** — written empty, matching 10,591 of the corpus's 10,592 senses. The target
  entries carry `uk` on six senses, and `register` is derived from misc by `export_corpus.REGISTER_MAP`
  (`uk` → `usually-kana`), a value **not** in the enum `contracts/vocab.schema.json` publishes —
  widening it "is an edit there, never a side effect". Storing them would make these eight the only
  records with misc *and* fail the contract. The dropped tags are recorded in the ledger.

`level`, `level_confidence`, `level_agreement`, `level_sources` and `introducing_topic_id` are
carried unchanged **on purpose**: the whole argument of the queue is that the level evidence was
always evidence about the *intended* word. 502's `4/4 n5` was agreement about はい, not about 肺.

A fourth thing moves that is not Layer A at all — the **authored pt-BR prose** sitting beside a moved
chip in six lesson bodies. That is §4.1, and it is the one place where "re-point the address" was not
enough.

---

## 2. Every reference, re-verified rather than assumed

`sentence_vocab` and `token.vocab_id` links were made by surface/reading matching, so most of them
are links to the word the record was *meant* to be — most, not all. Each link is re-checked here
against the target entry's own forms and reading (token evidence outranking a bare surface hit), and
a link that only fits the retired lexeme is dropped.

| id | sentence_vocab (queue) | kept/dropped | token (queue) | kept/dropped | unlocks | bodies | cks | family kept/dropped | reading.uses | kanji examples | pitch |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 502 | 11 | 10 / 1 | 4 | 3 / 1 | 1 | 1 | 224 | 1 / 0 | 0 | 0 | 0 |
| 355 | 150 | 150 / 0 | 150 | 150 / 0 | 1 | 1 | 254 | 1 / 0 | 0 | 1 | 0 |
| 349 | 77 | 77 / 0 | 77 | 77 / 0 | 1 | 0 | 249 | 1 / 0 | 0 | 0 | 0 |
| 374 | 15 | 13 / 2 | 0 | 0 / 0 | 1 | 1 | 253 | 0 / 1 | 1 | 1 | 0 |
| 503 | 6 | 3 / 3 | 6 | 3 / 3 | 0 | 0 | 0 | 1 / 0 | 0 | 1 | 1 |
| 1086 | 6 | 6 / 0 | 6 | 6 / 0 | 1 | 1 | 145 | 1 / 0 | 0 | 0 | 0 |
| 699 | 5 | 5 / 0 | 5 | 5 / 0 | 1 | 1 | 195 | 0 / 1 | 0 | 1 | 0 |
| 745 | 5 | 1 / 4 | 5 | 1 / 4 | 1 | 1 | 196 | 0 / 1 | 0 | 1 | 0 |
| **total** | **275** | **265 / 10** | **253** | **245 / 8** | **7** | **6** | **1,516** | **5 / 3** | **1** | **5** | **1** |

The measured totals reproduce the queue's mapped counts for these eight records **exactly** (275
`sentence_vocab`, 253 `token`). The queue's whole-set totals — 1,415 `sentence_vocab`, 766 `token`,
22 `lesson_unlocks`, 24 `family_member`, 5,955 slug occurrences — span all 23 candidates; the 14 the
migration refuses (§3) carry the remainder.

**The ten dropped links, each one named.** 502: たばこは肺によくない (the only 肺 in the corpus's
sentence bank, a lung sentence). 374: 立ちなさい。 and 私は立ちっぱなしだった。 (surface hits on 立ち
that are not the suffix 達). 503: 父に杯を渡した / 小さな杯でお酒を飲む / テーブルの上に杯が並んでいる
— 杯 read さかずき is present in the text but is not the counter read はい, and that is precisely the
link this migration must not keep. 745: 運悪く…, 運よく…, 本当に運が良かった, ケイちゃんは…運がいいのよ
(all four are 運 "luck", not the interjection うん).

**The eight reference sites that moved.** `sentence_vocab`; `token.vocab_id` (dropped links are
nulled, never deleted); `lesson_unlocks.ref` (7 rows, one lesson each, no lesson already claimed the
new ref); lesson `body` in `localized_text` — the `<vocab ref="…"/>` chips, every locale (6);
`lesson.cumulative_known_set` (1,516 lesson rows); `family_member` (a `word_family` keyed on a kanji
the new headword lacks is dropped — 立/等/運 lose one member each, going 4→3, 2→1, 5→4; the
`semantic_field` memberships are kept); `reading.uses.vocab` (1: `read:n4-volitivo-06-01` no longer
contains the word); `kanji_reading.example_vocab_ids` (5, see below).

**The kanji-example rule had to be tightened, and containment was not enough.** Four edges go
because the new headword no longer carries the kanji (園/その, 立/た, 等/トウ, 運/ウン). The fifth is
503: it *keeps* the headword 杯, so a containment test passes it, but the record now reads はい while
the edge it sits on is 杯's **kun** reading さかずき — it would have told a learner that 杯 read
さかずき is exemplified by a word read はい. The rule is now: the headword must contain the kanji
**and**, for a one-kanji word, the record's kana must BE that reading (for a compound, containment
stays the only claim the edge makes). The migration re-runs this rule over every already re-pointed
record on each invocation, so a rule tightened after a migration landed still reaches the rows it
landed on.

**Three sites that correctly need nothing**, listed so the silence is deliberate: `lesson_introduces`
and `exercise_item` address a word by `member_id` (the row id, which survives); and
`corpus/conjugations/*.json` is exporter output derived from `verb_class`/`adj_class` — none of the
eight is a verb or adjective before or after, so no conjugation slug moves.

**Two sites no exporter regenerates**, edited in step:

- `corpus/exam_banks/*.json` — 17 items across 7 banks. **6 rewritten** (the `kanji_reading` and
  `orthography` items are stem/answer projections of the record, so they are re-derived from it:
  `kr:n4:699`, `or:n4:699`, `kr:n5:503`, `or:n5:503`, `kr:n5:374`, `or:n5:374`). **11 quarantined**
  into `corpus/exam_banks/removed_items.json` (18 → 29 items), each with its reason: three because
  the item's Japanese was selected for the retired lexeme 運 (`cf:n4:530:745`, `pp:n4:745`,
  `us:n4:745`); two because the record is now kana-only (`kr:n4:745` has no kanji to read,
  `or:n4:745` has headword == kana); six because the new headword ends in okurigana that only the
  answer carries, which the bank's **own** `okurigana_giveaway` rule counts as solvable by shape
  (`kr`/`or` for 1086 斯う, 349 然う, 355 其の).
- `course/speak/**/*.json` — 5 actions across 4 units. Two slug moves in `eating/unit-06.json`'s
  `words[]`, and one distractor surface 園 → 其の in each of `health/unit-01`, `health/unit-06`,
  `politeness/unit-01`. That substitution is **required**, not cosmetic:
  `build_speaking_checkpoints.py` re-draws every wrong answer from the learner's known set, and
  `validate_speaking_path.py` fails any option that is not a known surface — leaving 園 would name a
  word the corpus no longer holds.

And the authoring source, so the next loader+export cycle cannot reintroduce the old address:
`research/derived/lessons/*.json` — 12 actions across 7 files (7 `unlocks` refs + 5 body refs).

The redirect itself is emitted by `export_corpus.py` at `corpus/vocab_redirects.json` from the new
`vocab.repointed_from` column, on **every** export (empty object when nothing was re-pointed, so its
absence always means "not exported yet"). It is registered in `design/generated_artifacts.json`;
`corpus/vocab/INDEX.md` gains a one-line pointer to it.

---

## 3. Refused, with the number that decides each one

The queue's PENDING.md entry for A9 states: *"Collateral checked: none of the intended targets
already exists as a duplicate record."* **That premise is false for 13 of the 22.** Re-derived here
against the same JMdict and the same consensus lists, thirteen intended entries are already the
published address of another vocab record. A re-point onto a taken slug is not a re-point: it is a
**MERGE**, and by the W08 precedent a merge that spans two lessons or two levels is refused, not
guessed. All 14 refusals below were re-measured against the live index in this run.

| record | intended target | why it is refused |
|---|---|---|
| 479 `vocab:1611000` 生る/なる | 成る `1375610` | MERGE — taken by record 2517 成る at **n3** (`les:n3-limites-06`) while 479 is unlocked by `les:n5-comparacoes-05`. Cross-level **and** two lessons: both W08 conditions. 253 sv + 263 token = 516 edges, the largest burden of the thirteen |
| 334 `vocab:1298670` 刷る/する | 為る `1157170` | MERGE — record 1358 為る at **n4** (`les:n4-conectores-01`), 729 sv + 738 token of its own; 334 is n5 |
| 148 `vocab:1609500` 罹る/かかる | 掛かる `1207590` | MERGE — record 1584 掛かる at **n3** (`les:n3-estado-01`). The n5 evidence is real, so the fix is a level move plus dropping the n3 unlock: a course-placement decision |
| 154 `vocab:1570710` 翔る/かける | 掛ける `1207610` | MERGE — record 153 掛ける already at n5 with 29 sentences, unlocked by `les:n5-verbos-01` while 154 is unlocked by `les:n5-verbos-03`. Two lessons, one word |
| 507 `vocab:1474240` 伯/はく | 履く `1607260` | MERGE — record 2581 履く at **n3** (`les:n3-relato-06`) |
| 376 `vocab:1341840` 盾/たて | 縦 `1335640` | MERGE — record 2306 縦 at **n3** (`les:n3-concessao-05`) |
| 1347 `vocab:1515620` 報/ほう | 方 `1516930` | MERGE — record 2731 方 is n3 but **already unlocked by `les:n5-perguntas-01`**, so the n5 course teaches it through another ref; a second n5 unlock is a duplicate card |
| 1343 `vocab:1523040` 本島/ほんとう | 本当 `1523060` | MERGE — record 593 本当 already at n5 (`les:n5-convites-06`) while 1343 is unlocked by `les:n5-conectando-04`. Two lessons, one word |
| 1223 `vocab:1208680` 滑降/かっこう | 格好 `1590480` | MERGE — record 1334 格好 already at n4 (`les:n4-conectores-01`) |
| 1350 `vocab:1241450` 琴/こと | 事 `1313580` | MERGE — record 887 事 already at n4 with 206 sentence links; 1350 carries 268 of its own, the largest sentence-link reconciliation of the thirteen |
| 1359 `vocab:1630770` 献花/けんか | 喧嘩 `1257040` | MERGE — record 1825 喧嘩 at **n3** (`les:n3-limites-02`) |
| 842 `vocab:1258830` 県下/けんか | 喧嘩 `1257040` | MERGE, **and a collision with 1359** — both records were resolved out of the same けんか slot and both name the same target, so at most one could ever be re-pointed onto it |
| 94 `vocab:1485770` 尾/お | 御 `2826528` | REFUSED ON THE EVIDENCE, and a merge anyway — no list row carried in the repo is keyed by a bare お (2/4, from elzup + openanki), so there is **no slot to re-point into**; and 2826528 is already record 1512 御 at n3 |
| 434 `vocab:1451160` 動/どう | 如何 `1008910` | REFUSED ON THE LESSON-DEGRADATION CONDITION — the slug is free, but under the ingest rule its headword is 如何, **already the published headword of record 46** (n5). 239 lessons carry both `vocab:動` and `vocab:如何` in their stored `cumulative_known_set`; after the rewrite those 239 lists would hold one ref twice and lose the other word. A9 forbids exactly that. It needs a headword-shape decision first (a kana headword beside kanji forms is a shape 0 of 7,401 records have today), or the row-id ref form |

The migration prints this list on every run, so the residue stays visible rather than becoming
folklore.

---

## 4. The lesson-degradation check: one real degradation, found and fixed

Measured on a full copy of the tree (`db/corpus.sqlite` taken through the SQLite backup API, so a
concurrent writer could not hand over a torn page). On the copy: export → snapshot → apply → export →
regenerate contracts → snapshot → compare. Every one of the 322 lessons was compared field by field,
**modulo the address substitution** (`vocab:<old jmdict id>` → new, and the seven headword refs),
with list order neutralised so a re-sort cannot hide a change.

### 4.1 The degradation the JSON diff could not see

The first pass came back clean: 254 `cumulative_known_set`, 7 `srs`, 7 `unlocks` and 6 `body` fields
changed, and every change was the address moving. That verdict was **wrong**, and the rendered
`course/**/lesson-NN.md` is where it showed:

```
- 肺: pulmão                →  - はい: pulmão
- 等々: etc., e assim por diante  →  - 到頭: etc., e assim por diante
- 侯(こう) = "marquês"       →  - 斯う(こう) = "marquês"
- 運(うん): sorte, fortuna.  →  - うん(うん): sorte, fortuna.
- 園: jardim, parque         →  - 其の: jardim, parque
… O substantivo 立ち ("partida, início") vem do mesmo verbo. → … O substantivo 達 ("partida, início") vem do mesmo verbo.
```

A lesson body stores `<vocab ref="vocab:肺"/><text>: pulmão</text>`: the chip is an **address** and
the gloss beside it is **authored pt-BR**. Moving the address alone leaves a true address carrying a
false sentence — six lessons would have shipped 「はい: pulmão」, 「到頭: etc.」, 「斯う: marquês」 — and
a JSON diff of the body cannot see it, because the only thing that changed there *is* the ref. This
is exactly the degradation A9 forbids, and it was invisible until the markdown rendering was compared.

The migration now carries a `BODY_FIXES` table: nine exact-substring rewrites over six lesson bodies,
each of which must match once or the migration refuses rather than guess at prose. It touches the DB
`localized_text` and the matching `research/derived/lessons/*.json`, and sets `needs_review = 1` on
every lesson it edits — this is Layer-C text and a teacher signs it off. The pass is keyed on the
text, not on `repointed_from`, so it is idempotent and reaches an index an earlier version of the
script had already migrated. The re-authored lines:

| lesson | was | now |
|---|---|---|
| `les:n5-te-form-05` | "Não confunda o verbo com estes dois substantivos:" | "…com estas duas palavras, que se leem só はい:" |
| `les:n5-te-form-05` | はい: pulmão | はい: sim, isso mesmo (a resposta) |
| `les:n5-te-form-05` | 杯: taça de saquê | 杯: contador de copos e tigelas (一杯, 二杯…) |
| `les:n5-particulas-lugar-02` | 其の: jardim, parque | 其の: esse, essa (aquilo que está perto de quem ouve) |
| `les:n5-particulas-lugar-03` | "O substantivo 達 ('partida, início') vem do mesmo verbo." | "Não confunda com o sufixo 達, que marca plural de pessoas ('nós', 'vocês') e não vem desse verbo." |
| `les:n4-obrigacao-05` | 斯う(こう) = "marquês" (título de nobreza). | 斯う(こう) = "assim, deste jeito". |
| `les:n4-forma-simples-03` | 到頭: etc., e assim por diante | 到頭: finalmente, afinal (depois de muita espera) |
| `les:n4-forma-simples-06` | "…palavras de movimento, sorte e ações:" | "…palavras de movimento, conversa e ações:" |
| `les:n4-forma-simples-06` | うん(うん): sorte, fortuna. | うん(うん): sim, é (resposta informal, entre amigos). |

The homophone list in `les:n5-te-form-05` is the one that got *better*: it used to contrast はいる
with 肺 and さかずき, and now contrasts it with two words that really are read はい.

`research/derived/lessons/n4-forma-simples-06.json` took only one of its two fixes: that authoring
file's body diverged from the DB body long before W09, so the chip anchor is not in it. The
divergence is pre-existing and is not W09's to close; the DB body — the one the export publishes —
carries both fixes.

### 4.2 The verdict after the fix

```
lessons before=322 after=322  missing=[]  new=[]
lesson fields changed by the ADDRESS alone: {cumulative_known_set: 254, srs: 7, unlocks: 7}
lesson fields also carrying a DECLARED prose fix: {body: 6}
LESSON DEGRADATIONS (anything else): 0
cumulative_known_set totals  before == after  (vocab 355,373 / kanji 68,312 / grammar 75,257 / kana-family 17,068)
duplicated cks entries after: 0
exercises 1560->1560; sentence_refs 624->624; unlocks 4135->4135; body chars 2,071,438->2,071,583

rendered lesson .md: 8 of 322 changed; differing lines that are NOT the generated
**Introduz:** line: 18 — exactly the nine declared fixes, removed and added.
```

The known sets did not shrink and gained no duplicate; exercise, sentence-ref and unlock counts are
unchanged; every body difference is either the eight chips or one of the nine declared prose fixes
(+145 characters, the length of the re-authoring).

Beyond the lessons, 217 published files are byte-identical, 7 changed by the substitution alone, and
27 carry a real content change — every one of them a consequence the re-point is *supposed* to have,
and each accounted for:

- `corpus/vocab/n4.json`, `n5.json`, `INDEX.md` — the eight records' new identity and glosses.
- `corpus/sentences/bank.json` — exactly 8 tokens lose their `vocab`/`vocab_id` (the 8 dropped token
  links: 502×1, 503×3, 745×4).
- `corpus/families/families.json` + `INDEX.md` — the three word families lose the member whose
  headword no longer carries their kanji (4→3, 2→1, 5→4).
- `corpus/kanji/n1..n5.json` — kanji pages drop example words that no longer contain the kanji (肺,
  侯, 総, 運, 立ち) and, where the pool allows, gain a replacement (運 → 運河, 立 → 立ち止まる, and 到頭
  entering the 到/頭 pages). The `example_words` ordering also reflects the re-derived `freq_rank`.
- `corpus/readings/n4.json` — one `uses.vocab` entry removed.
- `corpus/exam_banks/*` — the 6 rewrites and 11 quarantines of §2.
- `course/outline.json`, `course/n4/INDEX.md`, `course/n5/INDEX.md` — the eight headwords under their
  new names, in their new sort positions.
- `course/speak/**` — the 5 actions of §2.

### 4.3 The twelve gates, on the migrated copy

```
rc=0  validate_contracts          :: RESULT: ALL CONTRACTS PASS
rc=0  validate_stable_addresses   :: 545 files, 56542 integer FKs, ALL OK
rc=0  validate_unlock_ledger      :: 322 lessons, 4135 unlocks, 4135 distinct refs, ALL OK
rc=0  validate_srs_decks          :: 4131 cards over 322 lessons, 12 decks, 10026 corpus records + 268 kana ids, 0 FAIL
rc=0  validate_graph_edges        :: 554918 edges over 8 checks, ALL OK
rc=0  validate_repairs_applied    :: PASS — 1478 rows replayed clean, 21 checked skips, 0 FAIL
rc=0  validate_exam_banks         :: 6037 items in 40 banks, ALL OK
rc=0  validate_exam_level_gate    :: 6037 items in 40 banks, ALL OK
rc=0  validate_speaking_path      :: 72 units, 432 phrases, 365 checkpoint items, 0 FAIL, 1 warn
rc=0  validate_readings           :: 286 readings, 0 FAIL (exported JSON, slug space)
rc=0  validate_course_chain       :: 0 FAIL — chain tiers agree, derived summaries recompute, every artifact catalogued
rc=0  validate_practice_coverage  :: 322 lessons (278 teaching), 1560 exercises, 4074 unlocked items, 0 FAIL
```

`validate_speaking_path`'s single warn (`speak:arrival-02`: fluency block has 3 items, want 6) is
pre-existing and unrelated. `validate_repairs_applied` reports **no** row addressing a re-pointed
slug: none of the seven repair tables in `research/derived/` keys a row on one of the eight old
addresses, so no row needed to resolve through the redirect and none was marked. Four further gates
were run for insurance and are also green: `validate_lessons`, `audit_export_refs` (0 FAIL — every
ref resolves in the export), `audit_manifest`, `validate_capabilities`, `integrity_audit`.

`validate_course_chain` is the gate that was failing before this run: `corpus/vocab_redirects.json`
was pre-registered in `design/generated_artifacts.json` while nothing produced it. The export on the
copy produced it at that exact path, and the gate passes.

---

## 5. What landed, and what the orchestrator's export will change

Applied to the real tree by `python scripts/migrate_vocab_repoint.py --apply` (re-run is a no-op:
eight `SKIP … already applied`, and `--check` prints `OK: every re-point is applied`). **The real
tree was not exported.**

Written directly by the migration: `db/corpus.sqlite` (new column `vocab.repointed_from`);
`corpus/exam_banks/` ×8 files; `course/speak/` ×4 files; `research/derived/lessons/` ×8 files;
`research/derived/vocab_repoint_ledger.json` (new — it records the complete pre-migration record for
each of the eight, the fourteen refusals, the nine prose fixes and the kanji-example rule).

Also updated: `research/derived/rebuild_manifest.json` — step **114**
`scripts/migrate_vocab_repoint.py --apply`, enabled, runs last (it consumes the finished graph, and
step 111 `build_sentence_vocab` would otherwise rebuild the links this step corrects); its note now
records the `freq_rank` re-derivation and the speak-unit edits.

The orchestrator's export will change **293** files under `corpus/` and `course/` relative to the
tree as it stands now (the exam banks, speak units and authoring source are already changed on disk,
by the migration rather than by the export):

- **279 because of W09** — 254 `lesson-NN.json` and 8 `lesson-NN.md` (almost all of them the
  `cumulative_known_set` chip; the 8 markdown files are the six re-authored bodies plus two whose
  generated **Introduz:** line names a moved headword), 4 `topic.json`, 5 `corpus/kanji/*.json`, 3
  `corpus/readings/*.json`, 2 `corpus/vocab/*.json`, and one each of `course/outline.json`,
  `corpus/sentences/bank.json`, `corpus/families/families.json`.
- **5 both drifted and changed by W09** — `corpus/vocab/INDEX.md`, `corpus/families/INDEX.md`,
  `course/n4/INDEX.md`, `course/n5/INDEX.md`, and `corpus/vocab_redirects.json` (which the export
  turns from an empty object into the eight-entry map).
- **9 pre-existing drift, not W09** — `corpus/INDEX.md`, `corpus/grammar/INDEX.md`,
  `corpus/kanji/INDEX.md`, `corpus/sentences/INDEX.md`, `course/INDEX.md`, `course/n3/INDEX.md`,
  `course/pre-n5/INDEX.md`, `course/manifest.json`, `course/vocab_disambiguation_review.json`. These
  differ only in the build date the exporters stamp.

Two working-tree changes W09 depends on and does not own the commit of: the redirect emission in
`scripts/export/export_corpus.py`, and the `corpus/vocab_redirects.json` entry in
`design/generated_artifacts.json`.

---

## 6. What W09 leaves open

1. **Fourteen records still hold the wrong lexeme** (§3). Thirteen need a merge decision of the W08
   shape (which record survives, at which level, unlocked by which lesson); one (434 動) needs the
   headword-shape decision.
2. **Two retired lexemes should be re-ingested at their attested level** — 運/うん at n3 (four lists)
   and 園/その at n1 (bluskyo). Both are absent from the corpus now.
3. **Eleven exam items were quarantined, not replaced.** `corpus/exam_banks/` is still not
   regenerable (W17/W18 owe that); until it is, the banks are 11 items lighter at n4/n5 rather than
   re-drawn.
4. **Eight records carry `needs_review: 1` with re-authored pt-BR**, and so do the **six lessons**
   whose prose §4.1 re-authored — all of it awaits the teacher loop. The four `uk` headwords (其の,
   然う, 斯う, 到頭) will read oddly to a learner until the headword-shape decision in (1) settles what
   a usually-kana word publishes as its headword; the re-authored lines print those headwords.
5. **The chip-plus-prose failure mode is general, not W09's alone.** Any future migration that moves
   a `<vocab ref=…/>` address past authored text has the same blind spot, and nothing in the gate
   suite catches it: the JSON diff sees only the ref, and only a rendered-markdown comparison
   against a pre-migration snapshot exposed it here. A gate that asserts a chip's rendered surface
   is consistent with the gloss beside it would close the class.
