# W37 — Layer/source backfill: the derivation

_Derivation only. Nothing was applied. No repo code, contract, schema, exporter or database was
changed by this unit; `db/corpus.sqlite` was read from a scratch copy. The unit's output is
`research/derived/pending/provenance_backfill.json` (23,930 rows, 5.5 MB) plus the change list in §7._

**Headline.** Every one of the 11,299 backfillable records is derivable, and 23,606 of the 23,930
derived rows (98.6%) are `high` confidence — because for most of them nothing has to be *inferred*.
`db/corpus.sqlite` already stores `layer`, `source` and `created_by` on `kanji`, `vocab`, `topic` and
`course_module`, and `localized_text.layer` already stores the **per-field** layer that APP_PLAN D13
asks for. The exporter drops all of it. G3 is not an authoring problem; it is the same class of defect
W05 fixed for `needs_review` — the working index is more provenance-aware than the artifact
`CLAUDE.md` calls the source of truth. The residue is **one record**.

Two things did have to be judged rather than derived, and they are flagged, not smuggled: what layer a
pt-BR string that is a literal inside a builder belongs to (§6.1), and what shape a per-field layer
takes in the export (§7.1).

---

## 1. The measurement, re-taken

`quality_provenance_review.md` (2026-09-02) measured **11 entities / 11,695 records** carrying no
`layer`, `source`, `needs_review` or `ai_generated`. Re-measured today against the committed export it
is **11 entities / 11,300 records**. The set is not the same set:

| change | records | why |
|---|---:|---|
| audit baseline | 11,695 | 11 entities |
| − `family` | −396 | W05/W06 backfilled it: 707 records now carry `layer` + `source` + `created_by` + `needs_review` |
| + `review_ledger` | +1 | W06 added the approval sidecar as a `content` entity; it carries no provenance and should not |
| **today** | **11,300** | still 11 entities, by coincidence |

Today's 11: `vocab` 7,401 · `kanji` 2,131 · `conjugation` 1,157 · `capability_lesson_map` 266 ·
`kana` 211 · `capability` 74 · `topic` 52 · `course` 4 · `kana_family` 2 · `course_manifest` 1 ·
`review_ledger` 1.

`python scripts/validate/validate_provenance_json.py` → **ALL OK**, 52,527 records, 24 entities. It
passes them for the reason its own docstring gives: the expected field set is *inferred per entity*
from that entity's own data, so an entity that carries nothing is expected to carry nothing.

---

## 2. What the derivation reads (and why it is mechanical)

| source | what it settles |
|---|---|
| **`db/corpus.sqlite` provenance columns** — `kanji`, `vocab`, `topic`, `course_module` each have `source` / `created_by` / `layer` / `needs_review`; `kanji_reading`, `family`, `grammar_point`, `lesson`, `sentence` too | the record-level answer for 9,588 of the 11,299 records. Not inferred — **recovered**. |
| **`localized_text.layer`** (254,443 rows) | the per-field answer D13 asks for. `vocab_sense.gloss` pt-BR = **B** (10,608). `kanji.meanings` pt-BR = **B** (2,131). `kanji_reading.note` pt-BR = **C** (3,679). `kanji.irregular_note` = **C** (99). It is already stored per field and per locale; the export flattens it away. |
| **`research/derived/rebuild_manifest.json`** (122 steps, `writes: [tables]` per step) | which ingest created each table, and therefore which dataset it came from. `kanji`/`kanji_reading` ← step 2 `ingest_all.py` (KANJIDIC2, which writes `source='kanjidic2:<char>'`, `created_by='dataset'`, `layer='A'` at insert). `vocab` ← step 9 `reconcile_levels.py` from `raw_jmdict_entry` (JMdict). `kana`/`kana_family` ← step 8 `build_kana.py`. |
| **the builders' own declared contracts** | `build_conjugations.py`: *"deterministic, Layer A"*. `build_kana.py`: *"Layer A, deterministic"*. `build_capabilities.py`: *"curated, explicit"* (pedagogy). These are written down in the repo, so using them is reading a contract, not guessing. |
| **`dataset_source`** (9 rows) | the licence-bearing dataset identities the `source` prefixes point at. |

Because the index and the ingest are two independent statements of the same fact, they were
cross-checked rather than merged: **rule R1-index+ingest fires only when both agree**, and every
disagreement is reported (§5) instead of being silently resolved.

---

## 3. The derivation rules

| rule | what it means | rows | confidence |
|---|---|---:|---|
| **R1-index+ingest** | the index stores `layer`/`source`/`created_by` for this record **and** the ingest step that created the table independently derives the same `source`. The export just drops them. | 9,532 | high |
| **R1-index-recover** | the index stores it; the record comes from an authored placement table, so there is no dataset ingest to cross-check against (`topic`, `course`). | 56 | high |
| **R2-builder-declared** | no stored provenance: the record is computed by a named builder whose own docstring declares the layer. `source` names what the builder computed *from*. | 1,757 | high |
| **R3-localized-layer** | the per-field layer, read from `localized_text.layer` — which already separates the Layer-B translation and the Layer-C note from the Layer-A record they hang on. **This is D13, already stored.** | 10,297 | high |
| **R4-denormalized-copy** | the field is a verbatim copy of another record's field. It inherits that field's provenance and must **not** enter a review queue a second time. | 2,174 | high |
| **R5-inherit-record** | `localized_text.layer` is NULL for this field, so the layer is inherited from the record's own stored layer. **Medium** — the fix is to backfill `localized_text.layer` (111 rows, §7.3), not to guess harder here. | 111 | medium |
| **R6-single-writer** | exactly one tracked script has ever written this field, and that script writes a layer (`vocab:1928100.notes`, written by `modernize_nurse_term.py` with `layer='B'`). | 1 | high |
| **R7-builder-literal-locale** | the pt-BR string is a **literal in the builder** — not a dataset fact and not a translation of one. See §6.1: this is a ruling, not a derivation. | 2 | medium |

`field: null` is the record root. A field row exists **only** where that field's layer differs from
the root's (D13) or where the value is a denormalized copy. Field paths are **shape** paths, not
indexed (`senses[].gloss`, `readings[].note`): every sub-record of a collection shares its layer, so
stating it once per record replaces 10,608 identical `senses[i].gloss` rows with 7,401.

---

## 4. Counts

### 4.1 Per entity, per layer

| entity | records | record rows | field rows | A | B | C | implied `needs_review: true` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `vocab` | 7,401 | 7,401 | 7,402 | 7,401 | 7,402 | — | 0 |
| `kanji` | 2,131 | 2,131 | 4,686 | 2,131 | 3,957 | 729 | 0 (root A) |
| `conjugation` | 1,157 | 1,157 | 0 | 1,157 | — | — | 0 |
| `capability_lesson_map` | 266 | 266 | 0 | — | — | 266 | 266 |
| `kana` | 211 | 211 | 211 | 211 | — | 211 | 0 (root A) |
| `capability` | 74 | 74 | 74 | — | — | 148 | 74 |
| `topic` | 52 | 52 | 243 | — | — | 295 | 52 |
| `course` | 4 | 4 | 12 | — | — | 16 | 4 |
| `kana_family` | 2 | 2 | 2 | 2 | — | 2 | 0 (root A) |
| `course_manifest` | 1 | 1 | 1 | — | — | 2 | 1 |
| `review_ledger` | 1 | — | — | — | — | — | residue |
| **total** | **11,300** | **11,299** | **12,631** | **10,902** | **11,359** | **1,669** | **397** |

Layer counts are over **rows**, not records: a `kanji` record contributes one A row (the KANJIDIC2
record), one B row (`meanings`) and, for 630 of them, a C row (`readings[].note`).

Behind the shape paths: `vocab.senses[]` = 10,608 sub-records · `kanji.readings[]` = 9,340, of which
**3,679 carry a Layer-C pt-BR note** · `kana_family` = 57 family objects.

### 4.2 Confidence

By `created_by`: `dataset` 9,532 · `ai` 12,520 · `script` **1,878** — a value no schema declares
today (§7.4).

`high` 23,606 (98.6%) · `medium` 324 (1.4%: 211 `kana.family_label`, 111 R5-inherit, 2
`kana_family[].label`). No `low` rows: anything that would have been low is in §6 as a ruling.

### 4.3 What the apply moves

|  | today | after the W37 apply | still missing |
|---|---:|---:|---:|
| records carrying `layer` | 31,029 / 52,527 (59.1%) | 42,328 (80.6%) | **10,199** |
| records carrying `source` | 34,449 / 52,527 (65.6%) | 45,748 (87.1%) | **6,779** |

The remainder is **not** W37's scope and is listed in §8 — it is four more entities, and for three of
them the values are *also* already sitting in the index.

---

## 5. Disagreements with provenance the record already carries

**251 records.** Both kinds are real defects, not derivation noise.

### 5.1 `vocab:1928100` — a `source` that names a JMdict entry the record no longer is (1 record)

```
slug        vocab:1928100        headword 看護師 (かんごし)
jmdict_ref  1928100              source   jmdict:1213870      ← the superseded 看護婦 entry
```

`scripts/ingest/modernize_nurse_term.py` (rebuild step 65) modernises the dated, gendered 看護婦 to
看護師 by rewriting the row in place. It updates `slug`, `jmdict_ref`, `headword`, `kana`, `romaji`,
the pitch, the senses, the forms and three linked sentences — and leaves `source` naming the entry it
replaced. It is the **only** `source`-vs-`jmdict_ref` mismatch in 7,401 vocab records (the eight W09/A9
re-pointed records all have matching pairs), and `kanji` has **zero** mismatches in 2,131.

The backfill writes the derived value (`jmdict:1928100`) and records the conflict. The one-line fix
belongs in the applier, so a rebuild reproduces it.

### 5.2 250 Layer-A kanji records stamped `created_by: "ai"`, with `needs_review` cleared

| `created_by` | `needs_review` | records | has ≥1 unreviewed reading |
|---|---:|---:|---:|
| `ai` | 0 | **250** | 250 |
| `dataset` | 0 | 3 | 3 |
| `dataset` | 1 | 1,878 | 597 |

Commit `19cf804a` *"P5b: pt-BR meanings for kanji (250) + N5 vocab (2249 senses)"* authored the pt-BR
`meanings` for 250 kanji and wrote that fact onto the **record**: `created_by` `dataset → ai`, and
`needs_review` cleared to 0. The KANJIDIC2 record underneath — character, strokes, grade, radical,
readings — was never AI-authored and is still `layer: "A"`.

This is D13's failure mode caught in the wild, and it is the argument for the decision: with no place
to say *"the pt-BR meaning is B"*, a campaign said it about the whole record, and in doing so cleared
the only review flag those 250 records had. The 250 are exactly the ones whose pt-BR meanings were
model-written — the population that most needs the flag.

No tracked script in the repo sets `kanji.created_by = 'ai'` today (`grep` finds it only in
`scripts/familylib.py`, for families). So a rebuild from `rebuild_manifest.json` produces
`created_by='dataset'` for all 2,131 — and `validate_index_rebuildable.py` cannot notice, because it
diffs the **export**, and the export does not carry `created_by` for kanji. **A column the exporter
drops is a column the rebuild gate cannot defend.** Publishing these fields closes that hole as a side
effect.

The backfill writes `created_by: "dataset"` for all 250 (the derived, rebuild-reproducible value) and
moves the AI claim to where it is true: `field: "meanings"`, `layer: "B"`, `created_by: "ai"`.

### 5.3 Adjacent, found while deriving (not in the table)

- **256 `kanji_reading` rows carry `needs_review: true` with no pt-BR note to review** (3,935 flagged,
  3,679 notes). The flag on a reading means "this note is unreviewed"; on those 256 it points at
  nothing. Cheap cleanup, and it inflates any queue built on the nested flags.
- **`conjugation` is Layer A while `exercise_conjugation`, derived from it, is Layer B**
  (`build_conjugation_exercises.py:113`, `source: "conjugations"`). Both are defensible — a rule-
  derived form is a fact, a drill is not — but the corpus now asserts that a deterministic derivation
  from A is B in one place and A in another. Worth one sentence in `contracts/common.schema.json`.

---

## 6. Rulings the derivation cannot make, and the residue

### 6.1 The one open ruling: pt-BR strings that are literals inside a builder

`build_kana.py` writes `"Família do A"`, `"Família do KA"` … for the 57 kana families, and
`build_capabilities.py` writes `"Cópula だ/です e negação"` and 45 more capability names. These are
learner-facing pt-BR prose, they came from no dataset, and they are not translations of one.

- **Layer C** (what the table asserts, `medium` confidence) — they are the course's own naming of a
  pedagogical grouping, which is exactly §1.1's definition of C. Consequence: `needs_review: true` on
  the 74 capabilities and on the kana labels — **76 distinct strings** (30 kana family labels across
  57 family objects, plus 46 curated capability names) for a teacher to read once.
- **Layer A** (the alternative) — the gojūon row structure *is* a linguistic fact and "Família" is
  just its label. Consequence: nobody ever reads them.

The table takes C because the gate's own rule (Layer C ⇒ needs_review) then does the right thing for
60 strings at negligible cost, and because calling authored pt-BR prose "authoritative, zero AI,
trustworthy blind" is the reading that would have to be defended later. **The owner should confirm or
overrule; only the 324 medium rows move.**

`kana.family_label` is a denormalized copy of `kana_family[].label`, so 211 of those 268 records
inherit the ruling and must not be reviewed separately (R4).

### 6.2 Blocked by shape, not by knowledge — 268 records

| entity | records | blocker |
|---|---:|---|
| `capability_lesson_map` | 266 | each map value is a **bare list** of capability ids. There is nowhere to put a field. |
| `kana_family` | 2 | each map value is a **bare list** of family objects. Same. |

Both are worth naming for a second reason: `validate_provenance_json.records_of()` maps a non-dict map
value to `{}`, so **the gate reads all 268 of these as empty records and can never check them**. It
counts them in its total and inspects nothing. Their derived rows are in the table so the apply has
them the day the shape question is answered; the recommendation is in §7.2.

### 6.3 Residue — 1 record

`review_ledger` (`research/derived/review_ledger.json`). It records human verdicts *about* other
records. It is not corpus content and has no layer of its own; inventing one would make the approval
mechanism claim to be the thing it audits. **Exempt it explicitly** rather than backfill it — either
`PARTIAL_PROVENANCE` in the gate with the reason as its value (the file's own convention: "an entry
here is a written decision, not a silencer"), or reclassify it out of `content` in
`contracts/manifest.json`.

Nothing else is residue. Every other record of the 11 entities has a derived layer and source.

---

## 7. Proposed change list for the apply

Field and enum names below are **neutral English**, per CLAUDE.md — only content is localised.

### 7.1 The shape question: how a per-field layer is published

D13 says "per field where a record mixes layers". **9,745 records mix** (7,401 vocab, 2,131 kanji, 211
kana, 2 kana_family). Two shapes are available:

- **(a) `field_layers` — a map on the record.** `{"meanings": "B", "readings[].note": "C"}` beside a
  root `layer: "A"`. Present only on records that mix; absent means "the root layer is the whole
  truth". **This is the recommendation.** It has a direct precedent: APP_PLAN **D-shape** already
  settled `translation_layer: {"en": "A"|"B"}` on `sentence` as *a map, not a scalar, so pt-BR's layer
  and a future es-LA fit without a second field*. One key per mixing field, ~1.3 keys per record.
- **(b) a `layer` on every sub-record.** Rejected: it writes a constant onto 10,608 `senses[]` and
  9,340 `readings[]` sub-records, it cannot express a mixing field that is not inside a collection
  (`kanji.meanings`, `kana.family_label`), and it trips the gate's nested inference — a `layer` on the
  630 noted readings would demand one on all 9,340.

`translation_layer` and `field_layers` should be reconciled in the same pass (W40 owns the first);
they answer the same question and one name should win.

### 7.2 Exporters — where the fields have to be emitted

| script | function / output | change |
|---|---|---|
| `scripts/export/export_corpus.py` | `export_kanji()` (`rec = {…}`, ~line 240) | add `layer`, `source`, `created_by` from the `kanji` row already SELECTed; add `field_layers`. Widen the SELECT by three columns. |
| `scripts/export/export_corpus.py` | `export_vocab()` (~line 315) | same, from the `vocab` row. |
| `scripts/export/build_conjugations.py` | `corpus/conjugations/*.json` | add the three constants (`A` / `derived:conjugation-rules` / `script`). |
| `scripts/ingest/build_kana.py` | `corpus/kana/{hiragana,katakana}.json` | add the three; add `field_layers` for `family_label` once §6.1 is ruled. |
| `scripts/ingest/build_kana.py` | `corpus/kana/families.json` | **shape**: put provenance on each of the 57 family objects (they are already objects), not on the two bare lists. |
| `scripts/export/build_capabilities.py` | `registry.json` | add the three; `cap:topic:*` (28) and the curated 46 get different `source` values. |
| `scripts/export/build_capabilities.py` | `lesson_map.json` | **shape or exemption.** It is a pure join of two records that will both carry provenance. Recommendation: leave the shape alone and declare it a derived projection in `design/generated_artifacts.json`, then exempt it in the gate — duplicating provenance onto a join adds noise, not truth. |
| `scripts/export/export_course.py` | `course/*/course.json` (~line 533), `topic.json` (~line 526), `manifest.json` (~line 550) | add the three from the `course_module` / `topic` rows already SELECTed; `manifest.json` is a projection (`derived:course-chain` / `script`). |

### 7.3 Index-side repairs the apply should carry (so a rebuild reproduces the export)

1. `vocab:1928100.source` → `jmdict:1928100`, fixed inside `modernize_nurse_term.py` (§5.1).
2. 250 `kanji.created_by` → `dataset`, and stop writing per-field facts onto the record (§5.2). The B
   claim moves to `field_layers`. Whether the 250 records' `needs_review` returns to 1 is the same
   question as §6.1 and should be answered with it.
3. Backfill the **111 NULL `localized_text.layer` rows in scope** — `topic.{title,theme,objectives}`
   ×35 and `course_module.{title,overview}` ×3 — which turns every R5 row into R3 and drains the
   medium bucket. Out of scope but the same cleanup: `family.label` (759), `family.governing_rule`
   (758) and `grammar_point.label` (364) pt-BR are also NULL-layer.
4. 256 stray `kanji_reading.needs_review` flags with no note (§5.3).

### 7.4 Contracts

1. **`contracts/common.schema.json` — `Provenance`.** Its description currently *documents the
   non-adoption* by name: *"most entities carry none of them at the record root (kanji, vocab, family,
   conjugation, kana, capability, course, topic and the stroke sets do not)"*. `family` already makes
   that sentence false, and the apply makes the rest false. Rewrite it to state the rule instead of
   the exception — this is the line `quality_provenance_review.md` §2.2 flags as the reason no gate
   fires.
2. **Add `created_by` to `Provenance`** with a curated enum, and add it to
   `build_schemas.REF_BY_NAME`. This is load-bearing: `created_by` is currently a **measured** enum
   `["ai"]` on `family.schema.json` only. Left measured, `kanji.created_by` would be inferred as
   `["dataset"]` and the first `ai` row would be a build failure — the exact trap
   `SHAPE_BY_NAME`/`review_status` exist to avoid. Proposed values, neutral English:
   `dataset` (an open dataset wrote it), `ai` (a model authored it), `script` (a deterministic builder
   computed it). `script` is new; **1,878** rows need it and no existing value is honest for them.
3. **Declare `field_layers`** — `ALWAYS_PROPERTIES` if it is optional on every entity, or let it be
   measured if only the four mixing entities get it. Values `$ref` `Layer`; keys are field paths.
4. **Regenerate** `infer_shapes.py → build_schemas.py → build_manifest.py` and commit;
   `validate_schema_generation_is_current.py` requires byte-for-byte reproduction. Every record root
   is `additionalProperties: false`, so this step is mandatory, not optional.

### 7.5 The gate

`scripts/validate/validate_provenance_json.py`:

1. **Pin the 10 backfilled entities in `REQUIRED_PROVENANCE`** — `("source", "layer", "created_by")`,
   plus `needs_review` for the five C-rooted ones. Pinning is the whole point: it is what stops the
   inference hole from re-opening if an exporter path goes quiet, which is the failure the file's own
   docstring was written about.
2. **`review_ledger` → `PARTIAL_PROVENANCE`** (or out of `content`), with the reason as the value.
3. **Extend rule (b) to `field_layers`:** a record naming a Layer-C field must carry
   `needs_review: true` (or its sub-records must). Without this, 630 kanji and 211 kana carrying
   Layer-C pt-BR prose sit under a root `layer: "A"` and the gate says nothing — which is the same
   blindness the nested check (rule g) was added to close.
4. **Fail on a map-packed entity whose records read as `{}`** — today `capability_lesson_map` (266)
   and `kana_family` (2) are counted and never inspected. A gate that silently checks nothing on 268
   records is the defect this whole area exists to stop.
5. Check `created_by` against the declared value set.

### 7.6 Order

The apply is one unit: (1) exporter edits + index repairs → (2) re-run the exporters → (3) regenerate
contracts → (4) pin the gate → (5) full suite → (6) one commit. Steps 3 and 4 cannot precede 2 (the
schemas are measured from the data), and step 1's index repairs must land in the tracked scripts, not
only in the binary, or `validate_index_rebuildable.py` fails on the next rebuild.

---

## 8. What W37 does not cover

After the apply, **10,199 records still carry no `layer`** and **6,779 no `source`**. None of them are
in W37's 11, and for three of the four the values are *also* already in the index:

| entity | records | missing | already in `db/corpus.sqlite`? |
|---|---:|---|---|
| `sentence` | 5,889 | `layer`, `source` | **yes** — `layer='B'` on all 5,889, `source='tatoeba:*'` / `ai-generated` / `jec:*`, `created_by='ai'` |
| `stroke_order` / `stroke_lines` / `stroke_kana` | 3,493 | `layer` | no columns — but `source` (`kanjialive` / `glyphwiki` / `strokesvg`) is already exported and the layer is A by construction |
| `grammar` | 494 | `layer`, `source` | **yes** — `layer='C'`, `source='community-grammar-lists'` (363) / `hanabira-mit'` (132) / `course-anchor'` (1) |
| `lesson` | 322 | `layer`, `source` | **yes** — `layer='C'`, `source='ai'`, `created_by='ai'` |
| `speak_path` / `speak_unit` | 73 | `source` | no columns; `layer='C'` is already exported |

That is a **W37b** of the same shape and roughly a fifth of the size: four exporter paths, no new
rules, no new rulings. Doing it in the same pass is what makes "pin every content entity in
`REQUIRED_PROVENANCE`" possible, and a partial pin is a gate that still infers.

---

## 9. Thirty sample rows

One row per distinct `(entity, field, rule)` shape the table produces — a random member of each group,
seed 37. These are the rows a human should read to accept or reject the derivation; the full set of 33
shapes is reproducible from the table.

| # | entity | id | field | L | source | created_by | rule | conf |
|---:|---|---|---|:-:|---|---|---|---|
| 1 | `kanji` | `kanji:併` | _(record)_ | A | `kanjidic2:併` | dataset | R1-index+ingest | high |
| 2 | `kanji` | `kanji:驚` | `meanings` | B | `translated:kanjidic2-meanings` | ai | R3-localized-layer | high |
| 3 | `kanji` | `kanji:新` | `readings[].note` | C | `authored:kanji-reading-notes` | ai | R3-localized-layer | high |
| 4 | `kanji` | `kanji:発` | `irregular_note` | C | `authored:kanji-irregular-notes` | ai | R3-localized-layer | high |
| 5 | `kanji` | `kanji:端` | `example_words[].gloss` | B | `copy:vocab.senses[0].gloss` | ai | R4-denormalized-copy | high |
| 6 | `vocab` | `vocab:1356870` | _(record)_ | A | `jmdict:1356870` | dataset | R1-index+ingest | high |
| 7 | `vocab` | `vocab:1591160` | `senses[].gloss` | B | `translated:jmdict-gloss` | ai | R3-localized-layer | high |
| 8 | `vocab` | `vocab:1928100` | `notes` | B | `repair:modernize-nurse-term` | ai | R6-single-writer | high |
| 9 | `conjugation` | `vocab:1233630` | _(record)_ | A | `derived:conjugation-rules` | script | R2-builder-declared | high |
| 10 | `kana` | `kana:katakana-ヒャ` | _(record)_ | A | `unicode-gojuon` | script | R2-builder-declared | high |
| 11 | `kana` | `kana:katakana-エ` | `family_label` | C | `copy:kana_family.label` | script | R4-denormalized-copy | **medium** |
| 12 | `kana_family` | `katakana` | _(record)_ | A | `unicode-gojuon` | script | R2-builder-declared | high |
| 13 | `kana_family` | `hiragana` | `[].label` | C | `authored:kana-family-labels` | script | R7-builder-literal-locale | **medium** |
| 14 | `capability` | `cap:aspect-teiru` | _(record)_ | C | `capability-registry` | ai | R2-builder-declared | high |
| 15 | `capability` | `cap:aspect-phase` | `name` | C | `capability-registry` | ai | R2-builder-declared | high |
| 16 | `capability` | `cap:topic:n5-numeros-tempo` | `name` | C | `copy:topic.title` | ai | R4-denormalized-copy | high |
| 17 | `capability_lesson_map` | `les:pre-n5-katakana-13` | _(record)_ | C | `derived:lesson-unlocks+capability-registry` | script | R2-builder-declared | high |
| 18 | `topic` | `top:n4-potencial` | _(record)_ | C | `outline` | ai | R1-index-recover | high |
| 19 | `topic` | `top:n5-kanji-exame` | `title` | C | `jlpt-align` | ai | R3-localized-layer | high |
| 20 | `topic` | `top:n4-keigo` | `title` | C | `outline` | ai | R5-inherit-record | **medium** |
| 21 | `topic` | `top:n3-conjectura` | `theme` | C | `outline` | ai | R3-localized-layer | high |
| 22 | `topic` | `top:n5-conectando` | `objectives` | C | `outline` | ai | R5-inherit-record | **medium** |
| 23 | `topic` | `top:n5-convites` | `lessons[].title` | C | `copy:lesson.title` | ai | R4-denormalized-copy | high |
| 24 | `topic` | `top:n4-obrigacao` | `lessons[].description` | C | `copy:lesson.description` | ai | R4-denormalized-copy | high |
| 25 | `course` | `mod:n5` | _(record)_ | C | `outline` | ai | R1-index-recover | high |
| 26 | `course` | `mod:n3` | `title` | C | `outline` | ai | R3-localized-layer | high |
| 27 | `course` | `mod:pre-n5` | `overview` | C | `outline` | ai | R5-inherit-record | **medium** |
| 28 | `course` | `mod:pre-n5` | `topics[].title` | C | `copy:topic.title` | ai | R4-denormalized-copy | high |
| 29 | `course_manifest` | `course/manifest.json` | _(record)_ | C | `derived:course-chain` | script | R2-builder-declared | high |
| 30 | `course_manifest` | `course/manifest.json` | `courses[].title` | C | `copy:course.title` | ai | R4-denormalized-copy | high |

Rows 11, 13, 20, 22 and 27 are the medium ones and the only places a reviewer's answer changes the
table: 11 and 13 turn on the §6.1 ruling; 20, 22 and 27 turn into `high` the moment
`localized_text.layer` is backfilled (§7.3, item 3).

---

**Files read:** `contracts/manifest.json`, `contracts/common.schema.json`, `contracts/kanji.schema.json`,
`contracts/family.schema.json`, `contracts/_shapes.json`, `scripts/validate/validate_provenance_json.py`,
`scripts/contracts/build_schemas.py`, `scripts/export/export_corpus.py`, `scripts/export/export_course.py`,
`scripts/export/build_conjugations.py`, `scripts/export/build_capabilities.py`,
`scripts/export/build_conjugation_exercises.py`, `scripts/export/build_role_exercises.py`,
`scripts/ingest/build_kana.py`, `scripts/ingest/ingest_all.py`, `scripts/ingest/modernize_nurse_term.py`,
`scripts/ingest/replay_all.py`, `research/derived/rebuild_manifest.json`,
`research/derived/review_ledger.json`, `research/reports/APP_PLAN.md`,
`research/reports/readiness/quality_provenance_review.md`, `design/review_ledger.md`,
the committed `corpus/` and `course/` trees, and a scratch copy of `db/corpus.sqlite`.

**Files written:** `research/derived/pending/provenance_backfill.json` (23,930 rows) and this report.
