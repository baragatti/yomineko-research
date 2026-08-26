# `contracts/` — the machine-readable shape of the corpus

Everything under `corpus/` and `course/` is JSON, and until now the only statement of what that JSON
looks like was prose in [`design/schema_v2.md`](../design/schema_v2.md) plus a handful of hand-written
field checks for lesson leaves. Prose does not fail a build. This directory is the same model in a
form a machine can enforce, and that an API server can read to mount its routes.

## What is here

| File | What it is |
|---|---|
| `manifest.json` | The catalogue. One row per entity: where its files are, how records are packed, which field is its public address, which namespace that address uses, how many records exist, which schema validates it. **An API reads this first.** |
| `common.schema.json` | The shared vocabulary — `StableId`, `LocaleText`, `LocaleTextList`, `Level`, `Layer`, `Provenance`, `LevelTag`. Entity schemas `$ref` these instead of restating them. |
| `<entity>.schema.json` | One JSON Schema (draft 2020-12) per entity, 23 of them. |
| `types.ts` | The same contract as TypeScript interfaces, generated from the schemas. |
| `_shapes.json` | The measured field inventory the schemas were derived from. Regenerate it, not by hand. |

## The rules the contract encodes

**Every record has one stable, prefixed address.** `kanji:食`, `vocab:1580640`, `gram:te-form`,
`sent:tatoeba-83013`, `les:n5-saudacoes-01`. This is what an API route keys on and what a
cross-reference points at, and it never changes once published.

**An integer `id` is not an address.** Four registries (kanji, vocab, grammar, family) also carry an
integer `id`. That is a storage row number in the working index, it is not stable across a rebuild,
and it must never reach an API. On those entities the public address lives in `slug`; the manifest's
`stable_id_field` says which field to use, per entity, and it is not always the same one — on
`exercise_conjugation` the `slug` is the *vocab the drill is about*, a foreign key, and the address is
`id`.

**A headword is not an address either.** 93 headwords are shared by 193 vocab records — 人 is both the
N5 "pessoa" and an N1 sense, 仏 is both "Buda" and "França". The courseware used to reference
vocabulary by headword; it now uses the slug. What could not be resolved from evidence is listed in
[`course/vocab_disambiguation_review.json`](../course/vocab_disambiguation_review.json) for a teacher.

**Learner-facing text is a locale object, mechanical values are neutral English.** `LocaleText` for a
single string, `LocaleTextList` where the field is genuinely plural. Enum values (`pos`, `register`,
particle `function_type`, kana family `type`) stay English and locale-neutral —
see [`design/i18n.md`](../design/i18n.md).

**Provenance travels with the record.** `layer` (A authoritative / B derived-and-verified / C
pedagogy), `source`, `needs_review`, `ai_generated`. `needs_review` and `ai_generated` are **booleans**
— they were once integers on four entities, which meant a consumer testing `=== true` read unreviewed
Layer-C material as approved.

**A level claim carries its evidence.** There is no official JLPT list (spec §1.5), so `level` alone is
an assertion. `level_confidence` (a number in 0–1), `level_agreement` (`"4/4"`, or the sentinels `"0"`
for author-added and `"anchor"` for a deliberate course placement) and `level_sources` are what make it
auditable.

## Regenerating

Run in this order after any change to the exported data or the exporters:

```bash
python scripts/contracts/infer_shapes.py && python scripts/contracts/build_schemas.py && python scripts/contracts/build_manifest.py
```

`infer_shapes.py` measures what the data actually is; `build_schemas.py` turns that into schemas,
taking `required` from the measurement and the semantics from its own tables; `build_manifest.py`
writes the catalogue and the TypeScript.

Two schemas are **hand-authored** and are not regenerated: `capability_lesson_map.schema.json` and
`kana_family.schema.json`. Both are keyed collections rather than record lists, they disagree with each
other about what their keys mean, and a generated shape for them would be wrong in both cases.

## Enforcing

```bash
python scripts/validate/validate_contracts.py
```

Three checks — **shape** (every record validates against its schema), **identity** (stable ids are
unique within their entity), **graph** (every cross-reference resolves). It runs as part of
`scripts/validate/validate_all.py` and gates on exit code, so a field that changes type or an id that
starts pointing at nothing fails the build instead of reaching the app.

If a new field is legitimately added, the gate will reject it until the contract is regenerated. That
is deliberate: `additionalProperties: false` at the record root is what makes silent drift impossible.

## Known gaps

- **Three stroke entities have no stable id.** `stroke_order`, `stroke_lines` and `stroke_kana` are
  addressed by the character they draw (`natural_key` in the manifest). They can be routed to, but
  nothing in the graph can link to them the way it links to a kanji or a sentence.
- **`level_agreement` is a string ratio.** `"4/4"` is not sortable. It is text on purpose — a single
  float would discard the sample size, and `"1/1"` and `"4/4"` are not equally good evidence — but a
  consumer that wants to rank by it has to parse it.
- **Nested objects are only enumerated three levels deep**, so `additionalProperties: false` is set at
  the record root and one level in, and left open below that. Deeper drift is not caught.
