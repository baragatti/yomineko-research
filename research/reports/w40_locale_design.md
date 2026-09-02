# W40 — locale scope table and the `en_layer` shape (design half)

> **2026-09-02.** Design and measurement only. No corpus, course, contract or exporter file was written and
> no exporter was run. Deliverables landed in [`design/i18n.md`](../../design/i18n.md) (the locale scope
> table, the `en_layer` decision, the exporter rule, the validator spec) and
> [`design/schema_v2.md`](../../design/schema_v2.md) (a data-model addendum). This report is the measurement
> record and the reconciliation against the readiness audit.
>
> Every number here was produced by script over the committed export (`corpus/`, `course/`) and a read-only
> copy of `db/corpus.sqlite`. `contracts/manifest.json` supplied the entity → file mapping, so nothing is
> hardcoded and the whole table is reproducible.

---

## 1. Headline

| | |
|---|---:|
| locale objects in the export | **175,119** |
| carrying `en` | **134,910** (77.0%) |
| distinct key sets in use | **2** — `{pt-BR}` and `{pt-BR, en}`, zero others |
| locale-object field paths | **44** |
| field paths where `en` is **required** | 25 |
| field paths where `en` is **optional** (courseware policy) | 20 |
| **required-scope parity** | **134,910 / 145,442 = 92.8%** |
| required-scope gap | **10,532**, of which **18** are named exemptions → **10,514 to backfill** |
| optional-scope | 0 / 29,677, by policy, none of them failures |
| field paths that **mix** Layer A and Layer B | **1** — `sentence.translation` |

---

## 2. Parity by entity (measured)

| entity | records | locale objects | with `en` | parity | scope |
|---|---:|---:|---:|---:|---|
| sentence | 5,889 | 116,912 | 110,427 | 94.5% | required |
| kanji | 2,131 | 13,992 | 10,214 | 73.0% | required |
| vocab | 7,401 | 10,593 | 10,592 | **99.99%** | required |
| grammar | 496 | 2,387 | 2,387 | 100% | required |
| family | 396 | 718 | 718 | 100% | required |
| reading | 286 | 572 | 572 | 100% | required |
| kana | 211 | 211 | 0 | 0% | required |
| kana_family | 57 | 57 | 0 | 0% | required |
| **required subtotal** | | **145,442** | **134,910** | **92.8%** | |
| exercise_conjugation | 18,524 | 18,524 | 0 | 0% | optional |
| exercise_role | 5,358 | 5,358 | 0 | 0% | optional |
| lesson | 322 | 4,838 | 0 | 0% | optional |
| topic | 52 | 733 | 0 | 0% | optional |
| capability | 74 | 74 | 0 | 0% | optional |
| speak_unit | 72 | 72 | 0 | 0% | optional |
| course | 4 | 60 | 0 | 0% | optional |
| speak_path | 1 | 14 | 0 | 0% | optional |
| course_manifest | 1 | 4 | 0 | 0% | optional |
| **optional subtotal** | | **29,677** | **0** | 0% | |
| conjugation, exam_item, stroke_order, stroke_lines, stroke_kana, capability_lesson_map | 10,698 | 0 | — | — | no locale objects at all |
| **TOTAL** | | **175,119** | **134,910** | **77.0%** | |

The per-field table (all 44 paths, with the `en_layer` constant and the backfill route for each) is in
`design/i18n.md`. It is the normative copy and the validator's input; it is not restated here, so there is
one source of truth.

---

## 3. What the required-en gap is actually made of

The 10,514 backfill splits cleanly in two, and the split changes how the campaign has to be run.

| bucket | count | what is blocking it |
|---|---:|---|
| **content only** — the exporter already has an `en=` argument, the `localized_text` rows simply do not exist | **6,467** | `sentence.tokens[].role` 1796, `.gloss` 1580, `.conjugation_note` 435; `sentence.particles[].function` 998, `.explanation` 998; `sentence.translation_literal` 330, `.structure_explanation` 330 |
| **plumbing first** — the exporter/builder call site has **no `en` argument at all**, so writing the rows would change nothing | **4,047** | `kanji.readings[].note` 3679 (`export_corpus.py:190`, `loc(pt=r[5])`), `kanji.irregular_note` 99 (`:231`), `vocab.notes` 1 (`:294`), `kana.family_label` 211 (`build_kana.py:113`, a `{"pt-BR": label}` literal), `kana_family.label` 57 (same builder) |

The readiness audit called the whole 10.7k "an incomplete pass, not a policy". Half right: it is an
incomplete pass **and** for 38% of it the exporter has no code path to carry the result. **The backfill
campaign must patch those call sites before its rows can appear in the JSON**, or it will write 4,047 rows
into `localized_text`, re-export, and measure no change.

---

## 4. Recommendation on the shape: **(a), the sibling map**

**Adopt `translation_layer: {"en": "A" | "B"}`** — a sibling of `translation` on the `sentence` record,
values `$ref`ing the existing `Layer` enum, emitted only where `translation` has an `en` key.

**The reason is a measurement, not a preference.** Of the 44 locale-object field paths in the export,
**exactly one mixes Layer A and Layer B**:

- Every `localized_text` row with `locale='en'` is `layer='B'` — all 15 `(entity_type, field)` pairs,
  109,976 rows, **zero exceptions**.
- The three Layer-A registry fields (`kanji.meanings`, `vocab.senses[].gloss`,
  `kanji.example_words[].gloss`) are 100% A **by construction**: the exporter reads `kanji.meanings_en` /
  `vocab_sense.gloss_en` with no `localized_text` fallback, so no derived value can enter them.
- `sentence.translation` is the only exporter line that coalesces two sources —
  `export_corpus.py:517`, `en=s["en"] or SLen.get((sid, "translation"))`. It resolves to
  **3,529 Layer A + 2,342 Layer B, overlap 0**, union 5,871, plus 18 anchorless.

So every other `en` in the corpus has a layer that is **constant per field path**. Option (b) would change
the type of `LocaleText` and `LocaleTextList` — and therefore all 175,119 locale objects,
`contracts/types.ts`, the prototype's renderers, the 39-gate suite, `audit_hygiene_all_locales.py`'s ~244k
string walk, `scripts/ingest/i18n_text.py` and every future exporter — to express a distinction that is real
in 1 of 44 paths. (a) adds one optional key to one entity and one `$defs` entry.

**Is there anything (b) can express that (a) cannot?** Three candidates were checked and all three fail:

| candidate | verdict |
|---|---|
| `pt-BR` and `en` having different layers on the same string — the real case here (pt-BR is B, en is A) | (a) handles it: the map is keyed by locale, so `{"pt-BR": "B", "en": "A"}` is legal. Not a discriminator. |
| a third locale later | the map takes another key. Not a discriminator. |
| per-item layer inside a `LocaleTextList` | genuinely out of reach — for **both** shapes, since (b) is also per-locale, not per-item. And measured: no such mixing exists (`meanings_en` is one column value per record, 100% KANJIDIC). Not a discriminator. |

**No concrete reason for (b) was found. Recommend (a).**

**One correction to APP_PLAN's shorthand.** W40's row writes the default as `en_layer: "A"|"B"`, a bare
scalar. Adopt the **map** under the name `translation_layer`. The scalar cannot say what layer `pt-BR` is and
needs a second field the day `es-LA` arrives; the map costs nine characters more today and nothing later.
Decision A7 is unchanged, only its spelling.

**Where it appears:** `sentence.translation` and nowhere else. The layer of every other en-carrying field is
recorded **once**, as the `en_layer` column of the scope table, rather than as 134,904 identical constants
inside the JSON. If a future field starts mixing, changing that column from a constant to `per-record` is
what authorizes a new sibling — never the reverse.

**Enum owner: design.** `contracts/common.schema.json#/$defs/Layer`, already defined and already used by
`reading`, `exam_item`, `exercise_*` and `speak_*`. W40 creates no new enum. It adds one container `$defs`,
`LocaleLayerMap`. `"C"` is legal in the type but rejected for a translation by validator rule R6.

### Exporter rule (spec for the apply step, not implemented)

`scripts/export/export_corpus.py`, sentence loop, immediately after the `translation` line at `:517`. Read
the two storage locations separately instead of coalescing them, and leave the existing `translation` line
untouched so no consumer breaks:

```
anchor  := sentence.en column, non-NULL and non-empty after strip
derived := localized_text row (entity_type='sentence', entity_id=sid, field='translation', locale='en')

if anchor:      translation_layer = {"en": "A"}
elif derived:   translation_layer = {"en": "B"}
else:           omit the key entirely
```

Invariants, each checkable: emitted **iff** `translation` has an `en`; `translation` byte-identical before
and after; expected census **3,529 A + 2,342 B + 18 absent = 5,889**; `"A"` wins if a future record somehow
has both, and the validator reports that as a defect; `pt-BR` gets no key; no other entity gains a sibling.

Plant proof: null one anchored `sentence.en` that has no `localized_text` en row → that record loses both
`translation.en` and `translation_layer`, census 3,528 / 2,342 / 19. Null one that *has* such a row → it
flips to `{"en":"B"}`, census 3,528 / 2,343 / 18.

---

## 5. `validate_locale_parity.py` (spec for the apply step)

**Input: the two scope tables in `design/i18n.md`, parsed from that file** — not a generated sidecar. Two
files means drift, and drift in the file that defines what "complete" means is the failure mode this
validator exists to prevent. Entity → file resolution comes from `contracts/manifest.json`. A parse failure
is a validator failure, never a skip.

| id | rule | fires today? |
|---|---|---|
| **R1** | required row, any instance with no non-empty `en` → FAIL (suppressed for ids in that row's exemption list) | yes — 10,514, held by the ratchet |
| **R2** | optional row never fails, whatever the coverage; reported as INFO with the measured percentage | n/a |
| **R3** | **stale scope row**: a row whose field path yields **zero non-null instances** → FAIL | **yes — 3 rows**, see §6 |
| **R4** | **undeclared field**: a locale object at a path with no row in either table → FAIL | no |
| **R5** | **shape**: key set ⊆ `{pt-BR, en}`, `pt-BR` present | no — only two key sets exist |
| **R6** | **`en_layer` integrity**: where the row says `per-record`, every instance with an `en` carries the sibling, its keys ⊆ the instance's locale keys, values in `Layer`, `"C"` rejected; every instance without an `en` must not carry it; where the row states a constant, the sibling must be absent | n/a until the exporter rule lands |
| **R7** | **exemption liveness**: every exempted id must still resolve and must still lack `en` | no |

**Ratchet.** `research/reports/locale_parity_baseline.json` holds per-field allowed-miss counts; R1 fails
only when a count rises. Per APP_PLAN §1 it may only shrink, and a baseline entry for a field at 0 misses is
itself a failure (stale ratchet row, same class as R3 and R7). R3 through R7 are hard from day one.

**Plant proof** (ten plants, each must fail and each must go green when removed) is specified in
`design/i18n.md`.

---

## 6. Reconciliation with the readiness audit

### Confirmed exactly

Every number in `platform_contract_i18n.md` §2.3's field table reproduces to the unit:

| audit claim | measured | verdict |
|---|---:|---|
| 175,119 locale objects | 175,119 | confirmed, exact |
| 134,910 carry `en` (77.0%) | 134,910 (77.04%) | confirmed, exact |
| only two key sets, zero others | `{pt-BR}` 32 paths, `{pt-BR,en}` 20 paths | confirmed |
| `kanji[].readings[].note` 3679 | 3679 | confirmed |
| `sentence[].tokens[].role` 1796 | 1796 | confirmed |
| `sentence[].tokens[].gloss` 1580 | 1580 | confirmed |
| `sentence[].particles[].function` / `.explanation` 998 each | 998 / 998 | confirmed (denominators differ by 2: 14,182 vs 14,184) |
| `sentence[].tokens[].conjugation_note` 435 | 435 | confirmed |
| `sentence[].translation_literal` / `.structure_explanation` 330 each | 330 / 330 | confirmed |
| `kana[].family_label` 211 | 211 | confirmed |
| `kanji[].irregular_note` 99 | 99 | confirmed |
| `capability[].name` 74 | 74 | confirmed |
| `speak_unit.title` 72 | 72 | confirmed |
| `sentence[].translation` 18 | 18 | confirmed |
| §2.4: 3,529 anchors / 2,342 derived / disjoint / union 5,871 | identical | confirmed |
| §2.4: `jp_source` mis-classifies 135 | 135 Tatoeba-sourced records whose only English is derived | confirmed |
| **G4(c)**: `design/i18n.md` "says nothing about kanji reading notes, kana family labels, capabilities or the speaking path" | all four were genuinely outside the scope statement | **confirmed — and now addressed** |

### Refuted, corrected, or extended by measurement

| # | finding | detail |
|---|---|---|
| 1 | **`vocab` is not 100%** | the audit reports 100.0%; measured **10,592 / 10,593 = 99.99%**. One record, `vocab:1294`, has a pt-BR-only `notes` (`localized_text` layer B). Rounding concealed a required-en miss. |
| 2 | **The zero-en bucket is 29,945, not 26,945** | an arithmetic slip of exactly 3,000. Components: exercise_conjugation 18,524 + exercise_role 5,358 + lesson 4,838 + topic 733 + kana 211 + capability 74 + speak_unit 72 + course 60 + kana_family 57 + speak_path 14 + course_manifest 4. The audit's own grand total of 175,119 only closes with 29,945. |
| 3 | **"kana family labels" is two fields, not one** | `kana.family_label` (211) is the one the audit names. `kana_family.label` (57) is a **separate entity's own field**, and `kana_family` is missing from the audit's entity table entirely. Both are 0% and both are in the required scope. |
| 4 | **10,692 could not be reproduced under any scope** | the reproducible figures are **10,264** (strict corpus registries), **10,532** (the scope W40 recommends: plus kana and kana_family), or **10,678** (plus capability and speak_unit). The audit's own itemization sums to 10,620. Use 10,532, of which 10,514 is the backfill. |
| 5 | **284 learner-facing pt-BR strings are invisible to any locale-object census** | `speak_unit.fluency.prompt_pt` (71) and `speak_unit.production[].prompt_pt` (213) are **bare strings with PT-suffixed names**, built at `build_speaking_practice.py:310` and `:258`. They violate `design/i18n.md` principle 1 (identifiers and keys are English and neutral) and survived the 2026-06-14 `localized_text` migration untouched. Not in the audit. |
| 6 | **`lesson.body` is a bare `{"type": "string"}`** | 322 records, ~2.07M characters — the largest learner-facing text in the project, and structurally not a locale object. pt-BR-only is policy, so it is not a parity failure, but "adding a language adds rows, never structure" is **false for it**. Not in the audit. |
| 7 | **Three declared `LocaleText` fields are dead** | `kanji.notes` (null on 2131/2131), `family.description` (396/396), `family.members[].note` (2572/2572). Declared in the contracts, emitted by the exporter, and no `localized_text` field of that name exists in the DB. These are R3 failures and the apply step must delete either the fields or the rows. Not in the audit. |
| 8 | **`reading`'s 100% is partly manufactured** | `export_readings.py:43,45` builds the locale object inline with `or "Leitura"` / `or "Reading"` fallbacks, so a record with no authored title still reports bilingual. Passes the parity gate; should not pass a content audit. |
| 9 | **"an incomplete pass, not a policy" is half right** | for **4,047 of the 10,514** the exporter/builder call site has no `en` argument at all — `export_corpus.py:190, :231, :294` and `build_kana.py:113`. Rows alone will not surface. See §3. |
| 10 | **`exam_item` carries zero locale objects, and that is correct** | its 6,048 records' `stem` / `question` / `answer` / `correct` / `distractors[]` / `wrong[]` / `pieces[]` / `script[].text` are target-language Japanese — the material under test, locale-invariant by nature. **But W17 adds pt-BR explanations to auto-graded items, and that new field must land as a `LocaleText` marked optional**, or it opens a second PT-bound surface. Recorded in the scope table so W17 inherits the constraint. |

---

## 7. Judgement calls for the owner

Three scope rows are defensible either way. Each is a one-word edit to the `en required` column of the table
in `design/i18n.md` plus a validator rerun.

1. **`kanji.readings[].note` (3,679) and `kanji.irregular_note` (99) → marked REQUIRED.** They are
   `localized_text` layer **C** — pedagogy, which the rule makes optional. But they sit on a corpus registry,
   which the rule makes required, and together they are the largest single gap in the audit. The registry
   test won. **If the owner prefers the layer test, the backfill drops from 10,514 to 6,736** and the biggest
   item on the W40 work list disappears, so this is the one worth a deliberate answer.
2. **`capability.name` (74) → marked OPTIONAL.** Filed under `corpus/capabilities/`, but the content is a
   syllabus label built from a grammar cluster in `build_capabilities.py`. Course semantics, so it follows
   the courseware exclusion. Reading "filed under `corpus/`" as decisive makes it required and adds 74.
3. **`kana.family_label` (211) and `kana_family.label` (57) → marked REQUIRED.** Corpus registries, and the
   backfill is a one-line template ("Família do A" from `row='a'`), so requiring them costs almost nothing.
   Optional would make the kana registry the only corpus registry a second locale module cannot be built
   from.

Two items are not judgement calls but do need an owner decision before the apply step can go green:

- **The three dead `LocaleText` fields** (§6.7) must be deleted from the contracts, or their scope rows must
  be deleted. R3 fails until one of the two happens.
- **`speak_unit.*.prompt_pt`** (§6.5) is a contract violation with 284 instances. It is outside W40's stated
  scope, so it is recorded rather than fixed, but it should get a unit.

---

## 8. Files

| path | what changed |
|---|---|
| `design/i18n.md` | + locale scope table (required / optional / not-a-locale-object / dead rows), the 18 exemptions, the judgement calls, the `en_layer` decision with the (a)-vs-(b) analysis, the exporter rule, the `validate_locale_parity.py` spec with rules R1–R7, the ratchet and the ten plants |
| `design/schema_v2.md` | + W40 addendum: `translation_layer` on `sentence`, `LocaleLayerMap`, and why no other entity gets a sibling |
| `research/reports/w40_locale_design.md` | this report |

Nothing under `corpus/`, `course/`, `contracts/`, `scripts/` or `db/` was written, and no exporter was run.
