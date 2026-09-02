# `contracts/` — the machine-readable shape of the corpus

Everything under `corpus/` and `course/` is JSON, and until now the only statement of what that JSON
looks like was prose in [`design/schema_v2.md`](../design/schema_v2.md) plus a handful of hand-written
field checks for lesson leaves. Prose does not fail a build. This directory is the same model in a
form a machine can enforce, and that an API server can read to mount its routes.

## What is here

| File | What it is |
|---|---|
| `manifest.json` | The catalogue. One row per entity: where its files are, how records are packed, which field is its public address, which namespace that address uses, how many records exist, which schema validates it. **An API reads this first.** |
| `common.schema.json` | The shared vocabulary — `StableId`, `IdRef`, `LocaleText`, `LocaleTextList`, `Level`, `Locale`, `Layer`, `Provenance`, `LevelTag`, `LevelSources`. **Hand-authored.** Entity schemas `$ref` these instead of restating them, which is also what stops a regeneration narrowing them. |
| `<entity>.schema.json` | One JSON Schema (draft 2020-12) per **content** entity, 23 of them. |
| `user_state/<entity>.schema.json` | One schema per **runtime** entity, 7 of them: `user`, `card`, `review_log`, `lesson_progress`, `exam_attempt`, `skill_state`, `feature_state`. **Hand-authored**, specified by [`design/user_state.md`](../design/user_state.md). |
| `types.ts` | The same contract as TypeScript interfaces, generated from the schemas — content and runtime alike. |
| `_shapes.json` | The measured field inventory the schemas were derived from. Regenerate it, not by hand. Only content entities appear in it. |

### Two entity classes

`manifest.json` labels every entity with a `class`, and the class decides what "healthy" looks like:

| class | `files` | `records` | means |
|---|---|---|---|
| `content` | a glob that matches | an exact count | committed JSON under `corpus/` or `course/`. **23** entities, flat in this directory. An entity whose glob matches zero records is a FAILURE, not an empty entity. |
| `runtime` | **`null`** | **`null`** | minted per learner by the app; no record is committed here and none ever will be. **7** entities, under `user_state/`. |

The class is **declared** in each schema's `x-yomineko.class`, never inferred from a missing glob — a
stopped exporter also produces a missing glob, and the two must not look alike to a validator. Both
directions are gated: a `runtime` entity that declares a glob fails, so a content entity cannot relabel
itself and go quiet; a `content` entity with no glob fails, where it used to pass with a note. A runtime
schema is still checked — it must compile as draft 2020-12 and every `$ref` in it must resolve — and
`build_schemas.py` will never write one, so a regeneration cannot narrow it.

## The rules the contract encodes

**Every record has one stable, prefixed address.** `kanji:食`, `vocab:1580640`, `gram:te-form`,
`sent:tatoeba-83013`, `les:n5-saudacoes-01`. This is what an API route keys on and what a
cross-reference points at, and it never changes once published.

**An integer `id` is not an address.** Four registries (kanji, vocab, grammar, family) also carry an
integer `id`. That is a storage row number in the working index, it is not stable across a rebuild,
and it must never reach an API. On those entities the public address lives in `slug`; the manifest's
`stable_id_field` says which field to use, per entity, and it is not always the same one — on
`exercise_conjugation` the `slug` is the *vocab the drill is about*, a foreign key, and the address is
`id`. One address is currently shared by two entities: a conjugation table is addressed by the vocab
entry it inflects, so `vocab:1000730` answers to both. `common.schema.json → StableId` says so, and the
gate treats conjugation's `slug` as an edge into vocab rather than as a second declaration of the same
address.

**A headword is not an address either.** 93 headwords are shared by 193 vocab records — 人 is both the
N5 "pessoa" and an N1 sense, 仏 is both "Buda" and "França". The courseware used to reference
vocabulary by headword; it now uses the slug. What could not be resolved from evidence is listed in
[`course/vocab_disambiguation_review.json`](../course/vocab_disambiguation_review.json) for a teacher.

**Learner-facing text is a locale object, mechanical values are neutral English.** `LocaleText` for a
single string, `LocaleTextList` where the field is genuinely plural. Enum values (`pos`, `register`,
particle `function_type`, kana family `type`) stay English and locale-neutral, and a `locale` field is
a BCP-47-shaped pattern, never a list of the locales that happen to be authored —
see [`design/i18n.md`](../design/i18n.md).

**Provenance travels with the record where the record carries it.** `layer` (A authoritative / B
derived-and-verified / C pedagogy), `source`, `needs_review`, `ai_generated` mean one thing wherever
they appear, and `needs_review`/`ai_generated` are **booleans** — they were once integers on four
entities, which meant a consumer testing `=== true` read unreviewed Layer-C material as approved. What
is *not* true is that every entity carries them: most registries carry none of the four at the record
root, `sentence` nests two of them under its own `provenance` object, and `lesson` carries only
`needs_review`. `manifest.json` lists what each entity actually has. The contract enforces the meaning,
not the presence; backfilling the gaps is a data task, and only then can the fields become `required`.

**A level claim carries its evidence.** There is no official JLPT list (spec §1.5), so `level` alone is
an assertion. `level_confidence` (a number in 0–1), `level_agreement` (`"4/4"`, or the sentinels `"0"`
for author-added and `"anchor"` for a deliberate course placement) and `level_sources` are what make it
auditable. `level_sources` is an **open map**: its keys are whichever community lists were consulted,
and consulting one more is the operation §1.5 is built around, so it can never be a closed key list.

**A level is a level wherever it appears.** Adding N2 is adding rows, never a schema change (spec §1.6).
Every level-valued field points at `common#/$defs/Level` — `family.spans_levels[]`, a reading's
`introduced_at_level`, each `level_sources.<list>` value — and the composite `approx_band` on the
speaking path is a Level-pair *pattern* for the same reason.

## Where an `enum` is allowed to come from

This is the rule the 2026-08-26 contract audit produced, and it is the most important thing in this
directory. The generator measures the data, but **a value set is never measured**.

|  | Measured from the data | Comes from a source a human owns |
|---|---|---|
| types, nesting, array-ness | yes | — |
| `required` (a field on 100% of records) | yes | — |
| numeric range (`minimum: 0`) | yes | — |
| **every `enum`** | **no** | design document, producing code, or curated here |

The asymmetry is not stylistic. A measured `required` can only ever be broken by **deleting** a field,
which is exactly the drift a contract exists to catch. A measured `enum` is broken by **adding** a
value, so it fails on the first legitimate new record — and the documented remedy, regeneration, just
re-measures whatever the data now says. See the note on the regeneration tautology below.

Every `enum` in a generated schema carries an `x-vocabulary` block naming its owner:

- **`design`** — the taxonomy is declared in a document and the *document* is the authority.
  [`design/unlock_enums.json`](../design/unlock_enums.json) (unlock types, features, decks — its own
  `_doc` says "adding a value is a deliberate, documented change"),
  [`design/lesson_schema.md`](../design/lesson_schema.md) (the ten exercise types),
  [`design/schema_v2.md`](../design/schema_v2.md) (vocab/grammar `register`, `caution`, `lexeme_type`,
  `verb_class`, `adj_class`, sentence `pt_source`), [`design/listening.md`](../design/listening.md)
  (speaker slots), [`design/exam_simulator.md`](../design/exam_simulator.md) (exam sections),
  [`design/reading_practice.md`](../design/reading_practice.md) (`length_band`),
  [`design/learning_science.md`](../design/learning_science.md) (the four strands).
  The check that matters here runs in the *other* direction: the gate fails when the DATA contains a
  value the DOCUMENT does not list.
- **`producer`** — parsed straight out of the code that emits the value, so the contract can never be
  narrower than the pipeline feeding it: `dissect.py`'s `POS_MAP` / `INFLECTION_MAP` /
  `PARTICLE_FUNCTION_MAP`, `conjugate.py`'s `VERB_FORMS` + `ADJ_FORMS`, `build_role_exercises.py`'s
  `ASKABLE`, `validate_grammar_formation.py`'s `BASES`. The old schemas were built from the sample
  instead, and forbade `symbol`, `numeral`, `filler`, `ku-form` and `parallel` — all of which the
  dissection pipeline can emit from an ordinary Tatoeba sentence.
- **`curated`** — genuinely closed, owned by no document, written out in `build_schemas.py` with its
  source named (kana group types, KANJIDIC reading classes, the `family.type` column comment in
  `001_init.sql`).
- **`measured`** — a field that survived every filter below. There are currently **two**, both in
  `speak_unit.schema.json`: `fluency.kind` → `["recap", "situation"]` and `production[].kind` →
  `["on-topic", "review", "same-stage"]`. They are the only enums in the contracts carrying no
  "Vocabulary owner:" line, which is how you find them. Both are in fact **builder-owned**:
  `scripts/export/build_speaking_practice.py` writes them literally (`"kind": "recap" if is_recap else
  "situation"`, and `"same-stage" / "on-topic" / "review"`), so they belong under `producer` — the
  generator simply does not parse that builder, so the values were derived from the data instead. Until
  it does, treat them as closed only for as long as that one file says they are. (This section said
  "there are currently none" until 2026-09-02, when the readiness sweep counted them.)

A field with no such source gets a plain `string`. That is deliberate: `nuance_tags`, `usage_contexts`,
`pattern[].role`, `clause_structure`, `theme`, `pos_coarse`/`pos_fine` (third-party analyzer output the
project does not own) and JMdict `misc` tags all look closed in today's corpus and are not. **A field
with no declared vocabulary is honest; a field with a measured one is a trap.**

Even where a measured enum would be allowed, it is skipped when any of these hold — each one is a probe
from the audit that a legitimate future record failed:

- the entity has fewer than 50 records (`course_manifest` and `speak_path` have exactly one, so *every*
  scalar in them looked closed: `generated` became the enum `["2026-08-26"]`, `totals.units` `[72]`);
- any value is longer than 40 characters, or contains a space or a slash (prose, a path, a ratio);
- any value looks like a stable id (that is a foreign-key column — it becomes `IdRef` instead);
- the field name is a date, a version, a path or an asset slot (`generated` → `format: date`,
  `schema_version` → `^\d+\.\d+$`, `audio` → `pending` or a real filename).

**Integers and booleans are never a vocabulary.** `infer_shapes.py` no longer even collects their value
sets. A count, an ordinal and a stroke number are quantities: the 24-value enum on `kanji.strokes` made
every 24-, 25-, 26-, 27- and 28-stroke kanji illegal, and `stroke_order.total_strokes` literally skipped
21. They get `{"type": "integer", "minimum": 0}`.

**A field that is null on every record is not pinned to null.** `kanji.notes`, `family.description` and
`family.members[].note` were typed `{"type": "null"}` *and* listed as `required`, so writing the
Layer-C prose they exist for would have failed the build. They are now `anyOf: [LocaleText, null]` and
not required.

## Discriminated shapes: `exam_item`

Fourteen question shapes share `corpus/exam_banks/`, and one schema over all of them enforced almost
nothing — `{"id": "kr:n5-0001", "level": "n5"}` validated, as did a kanji-reading item with no correct
answer. The section lives in the id prefix, so the schema now carries `allOf` if/then branches keyed on
that prefix: `kr`/`or` need a stem and options, `cf`/`gf` add the sentence, `so` needs pieces and an
answer, `tg`/`rc` hang off a reading passage, `pp`, `us` and the five listening sections each have their
own shape. Option arrays get `minItems: 2` and `uniqueItems: true`.

The **branches are hand-declared** in `build_schemas.py` (`EXAM_BRANCHES`) — which prefixes share a
shape, and the floor each must carry. The **`required` list inside a branch is measured** at 100%
presence for that prefix, which is safe for the reason in the table above. If a hand-declared floor ever
stops being universally present, generation **fails** rather than quietly emitting a weaker contract;
so does an id prefix that matches no declared branch.

## Regenerating

Run in this order after any change to the exported data or the exporters:

```bash
python scripts/contracts/infer_shapes.py && python scripts/contracts/build_schemas.py && python scripts/contracts/build_manifest.py
```

`infer_shapes.py` measures what the data actually is; `build_schemas.py` turns that into schemas,
taking types/`required` from the measurement and every vocabulary from the tables described above;
`build_manifest.py` writes the catalogue and the TypeScript.

Two schemas are **hand-authored** and are not regenerated: `capability_lesson_map.schema.json` and
`kana_family.schema.json`. Both are keyed collections rather than record lists, they disagree with each
other about what their keys mean, and a generated shape for them would be wrong in both cases.
`build_schemas.py` asserts that set at startup and refuses to run if a new map-packed entity appears
without a hand-written contract — otherwise it would silently produce no schema at all, and an entity
with no schema is invisible to both the gate and the manifest, which glob `contracts/*.schema.json`.
`common.schema.json` is hand-authored too.

## Enforcing

```bash
python scripts/validate/validate_contracts.py
```

Three checks — **shape** (every record validates against its schema), **identity** (stable ids and map
keys are unique within their entity), **graph** (every cross-reference resolves) — plus a structural
one: an entity whose glob matches **zero** records is a failure, not a quiet `[OK ] 0 records`. It runs
as part of `scripts/validate/validate_all.py` and gates on exit code.

**What declares an address, and what points at one.** This used to be decided by the key name: any
id-shaped string under a key called `id` or `slug` was read as a record announcing its own address.
That swallowed ~20,000 real foreign keys — a drill's `slug` naming the vocab it drills, a checkpoint's
`id` naming an exam item, a topic's `lessons[].id` naming a lesson leaf — and, worse, a *broken* one
minted itself as a new address instead of being reported as dangling. The rule is now structural: the
record root's `stable_id_field` declares, a map file's keys declare, plus a short explicit list of
nested paths that genuinely own an address (a lesson's own exercises, the speaking path's stages, the
kana chart's group rows). Everything else that is id-shaped is an edge and has to land somewhere.

## What regeneration can and cannot catch

Regeneration absorbs a change to the data's **shape**. That is what it is for, and
`additionalProperties: false` at the record root is what makes a new field visible instead of silent.

Regeneration can never catch a change to the data's **vocabulary** — and the first version of this
layer was built as though it could. That is the regeneration tautology: a measured enum rejects the
first record carrying a new value *because it is new*, the documented fix is "regenerate the contract",
and the regeneration then redefines the contract to include it. The gate therefore fires exactly once,
on a legitimate record, and teaches whoever hit it that the honest response to a red gate is to re-run
the generator. It could not ever have caught the case it existed for — a value nobody declared showing
up in the corpus — because the same command that clears the failure also blesses the value.

That is why vocabularies now live outside the generator. A regeneration can add a field, widen a range
or relax a `required`; it cannot widen an `enum`, because no enum is derived from the data. Widening one
means editing `design/unlock_enums.json`, a design document, the producing code, or `build_schemas.py`
— all of them reviewable diffs a person had to intend. "The corpus grew a value nobody declared" is now
a failure someone has to answer for, which is the check this layer was built to provide.

Two things it still does not catch, and neither is fixed here:

- **Nested objects are only enumerated three levels deep**, so `additionalProperties: false` is set at
  the record root and one level in, and left open below that. Deeper drift is not caught.
- **Lesson `body` is one string.** The 7,700-odd `<vocab ref="…">`-style chips inside lesson bodies are
  learner-facing links and the graph check cannot see them: `ID_PATTERN` is anchored at the start of a
  string, and a body starts with `<heading`. `scripts/validate/audit_export_refs.py` covers most of
  them; `<check item-ref>`, `<exercise ref>` and `<stroke ref>` are covered by nothing.

## Known gaps

- **Three stroke entities have no stable id.** `stroke_order`, `stroke_lines` and `stroke_kana` are
  addressed by the character they draw (`natural_key` in the manifest). They can be routed to, but
  nothing in the graph can link to them the way it links to a kanji or a sentence.
- **`level_agreement` is a string ratio.** `"4/4"` is not sortable. It is text on purpose — a single
  float would discard the sample size, and `"1/1"` and `"4/4"` are not equally good evidence — but a
  consumer that wants to rank by it has to parse it.
- **`types.ts` does not know every shared definition.** `build_manifest.py`'s `ts_type()` maps a fixed
  list of `$ref` tails to TypeScript; `Locale` and `IdRef` are not in it, so `provenance.locale`,
  `speak_unit.stage` and `chunk_phrases` come out as `unknown`. The JSON Schema is the contract and it
  is right; the TypeScript view is one line short.
- **`needs` and `unlocks[].ref` are still untyped item schemas.** `design/unlock_enums.json` defines
  `need_type` and the per-type ref namespaces, and no lesson carries a `needs` entry yet, so there is
  nothing to measure and the item schema was left open rather than invented.
