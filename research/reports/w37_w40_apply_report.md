# C8: W37 provenance backfill + W40 derivable half, applied

_2026-09-23. Single DB writer. Mechanical: derived 23,495 (W37) + 26,365 (W40), authored 0. Not a checkpoint:
gate plus quick replay. Inputs: `research/reports/w37_provenance_report.md` §7, `research/reports/w40_derive_report.md`,
`design/i18n.md`._

## 1. Headline

| | before | after |
|---|---:|---|
| W37 entities publishing `layer` / `source` / `created_by` | 0 of 10 (family aside) | 9 published, `capability_lesson_map` exempt by decision |
| records carrying `layer` / `source` (all content entities) | 31,029 / 34,449 (09-10 count) | 41,230 / 44,650 of 55,749 |
| records stating a per-field layer (`field_layers`) | 0 | 9,800 (kanji 2,131, vocab 7,401, kana 211, kana families 57) |
| Layer-A kanji stamped `created_by: ai` | 250 | 0 (the AI claim now sits in `field_layers.meanings`) |
| reading flags with no note behind them | 291 rows | 0 (`readings[].needs_review` true = 3,679 = the notes) |
| required-scope `en` gap (design/i18n.md) | 57,567 | 31,202 (31,184 ratcheted + 18 named exemptions) |
| `translation_layer` on sentences | absent | A 7,849 / B 2,342 / absent 18 (invariant 1 holds on all 10,209) |
| dead `LocaleText` fields | 3 (7,809 null instances) | 0 |
| bare `prompt_pt` strings in speak units | 284 | 0 (`prompt: {"pt-BR": ...}`) |

Gate: `validate_all.py` green, quick replay green. 25/25 plants (§5).

## 2. W37: re-derived, then applied

The 09-10 table could not be applied as is: capabilities grew 74 -> 125 (W24), the lesson map 266 -> 322, the
kanji reading flags moved. No deriver was tracked, so one is now: `scripts/derive_provenance_backfill.py`
reads the index read-only and writes `research/derived/repairs/provenance_backfill.json` with two halves.

- **`rows` (23,495):** what the export must publish. 11,139 record rows (layer / source / created_by, plus
  needs_review where the entity carries a root flag) and 12,356 field rows, one per `field_layers` entry.
  The 09-10 table's R4 copy rows whose layer equals the root's (topic `lessons[].title`, course
  `topics[].title`, ...) are not rows any more: they state nothing the root does not. Asserted by
  `validate_repairs_applied.handle_provenance_backfill` (23,495 PASS).
- **`index_repairs` (638):** applied by `scripts/apply_provenance_backfill.py`, rebuild step 137,
  exact-match (from or to, else refuse), idempotent (second run: 0 writes).

| repair | rows | why |
|---|---:|---|
| `kanji.created_by` ai -> dataset | 250 | P5b wrote a per-field fact onto the record (§5.2 of the derivation) |
| `vocab.source` jmdict:1213870 -> jmdict:1928100 | 1 | also fixed in `scripts/ingest/modernize_nurse_term.py` (step 65) |
| `localized_text.layer` NULL -> C (topic title/theme/objectives, module title/overview) | 111 | turns the R5 medium rows into stored facts |
| `kanji_reading.needs_review` 1 -> 0 where no note exists | 291 rows (276 groups) | a flag that points at nothing inflates every queue |

**Exporter paths (7):** `export_corpus.export_kanji` / `export_vocab` (three columns already SELECTable,
plus `field_layers` from `localized_text.layer`), `build_conjugations.py` (A / `derived:conjugation-rules` /
script), `build_kana.py` (kana and the 57 family objects: A / `unicode-gojuon` / script, `field_layers`
label C, flagged), `build_capabilities.py` (C / `capability-registry` / ai, flagged), `export_course.py`
(topic and course from the index columns, manifest C / `derived:course-chain` / script).

**Kanji root `needs_review`.** New on the kanji root, true on 99: it covers the one root-level Layer-C field
(`irregular_note`). The reading notes keep their own per-reading flag. It is deliberately NOT the DB
`kanji.needs_review` column, whose meaning is muddled (the 250 cleared flags) and whose rebuild value is
unproven; exporting it would have been a replay break waiting for the next checkpoint. Recorded in PENDING
B-W37.

**Contracts.** `common.schema.json`: Provenance description rewritten to state the rule; `created_by` a
curated enum (`dataset | ai | script`); new `$defs` `FieldLayers` and `LocaleLayerMap`.
`build_schemas.py`: `created_by` in `REF_BY_NAME`; `field_layers` and `translation_layer` in
`REF_BY_NAME_WITH_CHILDREN` (open maps, never a measured key list). `build_manifest.ts_type` renders them.
`kana_family.schema.json` is hand-written (`HANDWRITTEN_MAPS`) and gained the five properties by hand.
Regenerated, byte-reproducible (`validate_schema_generation_is_current` OK).

**Gate (`validate_provenance_json.py`), five changes:** (1) 9 entities pinned in `REQUIRED_PROVENANCE`
(A roots: source/layer/created_by; C roots add needs_review); (2) `NO_PROVENANCE` for `review_ledger` and
`capability_lesson_map`, with the reason, asserting they carry none; (3) rule (b) over `field_layers`: a C
field flags its carriers (root field -> the record, `coll[].f` -> each sub-record carrying `f`), values
A/B/C, never the root's own layer, never a field the record lacks; (4) a record the gate cannot read as an
object fails, and a map of object lists is read as its objects (the 57 kana families are now checked, not
counted as 2 empty records); (5) `created_by` in the enum.

## 3. W40: the derivable half

- **Derivation re-run** (`w40_derive_report.md` §7.5, same scripts on a fresh snapshot): 26,365 derived
  (21,902 high / 4,463 medium), 31,184 residue + 18 exempt. Delta vs 09-23 01:29: particle functions
  9,846 -> 9,773 (U1 re-authored 50 て-locution labels, so some pt-BR strings lost their precedent); every
  other field identical. The table moved `pending/` -> `repairs/en_backfill_derived.json`; the residue list
  stays in `pending/` (re-written by the same run).
- **Apply:** `scripts/apply_en_backfill.py`, rebuild step 138. Rows are addressed by sentence slug and the
  exporter's own token / particle order, never by storage id, and refused if the pt-BR they were derived
  from moved. 26,099 `localized_text` en rows, layer B; the 266 kana rows are the `build_kana.py` template
  (chouon stays without en: it is residue). Idempotent. `handle_en_backfill` asserts all 26,365 against the
  export.
- **`translation_layer`** emitted after the `translation` line: `sentence.en` anchor -> A, else a
  localized_text en -> B, else omitted. Census 7,849 / 2,342 / 18 (design/i18n.md invariant 3 updated).
- **`validate_locale_parity.py`** built from design/i18n.md R1-R7, reading the two scope tables and the
  exemption list from that file. Ratchet `research/reports/locale_parity_baseline.json`: 12 fields,
  31,184 misses (particle explanations 11,224, literal + structure 4,650 each, reading notes 3,679, token
  glosses 3,841, particle functions 1,713, roles 895, conjugation notes 430, irregular notes 99, and 1 each
  for the nurse note and the two chouon labels). In `validate_all.py` as a hard gate. en optionality was
  NOT changed (B-W40): `kanji.readings[].note` / `irregular_note` stay required and ratcheted.
- **Scope table maintenance:** four undeclared courseware paths declared optional (`capability.can_do`,
  `exam_item.explanation`, `speak_unit.fluency.prompt`, `speak_unit.production[].prompt`); the "carries en
  today" column refreshed by script; totals, census and plant numbers re-stated.
- **Dead fields deleted** from the exporter and hence the measured contracts: `kanji.notes` (2,131 nulls),
  `family.description` (709), `family.members[].note` (4,969). No consumer read them (grep: none in
  prototype/, scripts/).
- **`prompt_pt` -> `prompt` (284):** `build_speaking_practice.py` emits the locale object; consumers updated
  (`prototype/app/lib/speak.server.ts`, `review_queue.py`, which keeps its aggregate's internal key so a
  prior content hash still matches, `build_review_views.py`, `validate_speaking_path.py`). The committed units
  were rewritten by key rename only (see §6).

## 4. Decisions taken by default (reversible)

- B-W37 (a): builder-literal pt-BR labels are Layer C (kana labels in `field_layers`, capabilities C-rooted).
- B-W37 (b): per-field layer as a `field_layers` map. `translation_layer` stays a separate, per-locale map:
  it answers a different question (which layer is the `en` of ONE field, per record) and the two do not
  collide; `field_layers` states the layer of a field's authored (pt-BR) content.
- The 250 kanji's DB `needs_review` stays 0 (owner's call, PENDING B-W37 note added).

## 5. Plant proofs (copied tree, validators + `migrate_exam_banks_p7.py` + `dbtarget.py` copied in)

| plant | caught by |
|---|---|
| pinned `created_by` removed (kanji) | missing, pinned |
| `created_by: human` | enum |
| `field_layers` value `D` / repeats the root / names a missing field | h) |
| kanji `irregular_note` C with root unflagged | rule (b) root |
| reading note C with its reading unflagged | rule (b) collection |
| kana `family_label` C with the record unflagged | rule (b) |
| kana_family value replaced by a bare list | unreadable record |
| review_ledger grows `layer` | NO_PROVENANCE |
| topic loses `needs_review` | pinned |
| grammar.label loses en | R1 |
| scope row `kanji.fictional_field` | R3 |
| scope row `sentence.particles[].function` deleted | R4 |
| `pt-PT` key | R5 |
| `translation_layer {"en": "C"}` / on a record with no en | R6 x2 |
| `sent:tatoeba-77972` removed from the exemptions | R1 |
| en written onto exempt `sent:tatoeba-4766` | R7 |
| token gloss misses +1 | ratchet |
| baseline `vocab.notes` lowered to 0 | ratchet |

Baseline green before, 21/21 plants caught, green after restore: 25/25.

## 6. Rendered diff of `course/` against HEAD

Lessons: **0 changed** (no lesson JSON or MD touched). Changes are additive provenance and the speak
rename only:

| class | files | change |
|---|---:|---|
| topic.json | 52 | + `source`, `created_by`, `layer`, `needs_review` |
| course.json | 4 | same four keys |
| manifest.json | 1 | same four keys |
| speak units | 72 | 213 `production[].prompt_pt` -> `prompt.pt-BR`, 71 `fluency.prompt_pt` -> `fluency.prompt.pt-BR`, same text |

Re-running `build_speaking_practice.py` on its own re-derived strand counts and totals (drills 251 -> 253)
that the committed units got from the full speak chain, and failed the strand and spiral ratchets. That
output was discarded: the units were restored from HEAD and only the key rename applied
(`course/speak/course.json` unchanged). The builder emits the same shape on the next full speak rebuild.

## 7. Open items

1. **Replay:** steps 137-138 are new (families now 139-141). Not a checkpoint unit, so no full replay ran;
   the next checkpoint's full replay is the proof that a rebuild reproduces the four index repairs and the
   26,099 en rows (both scripts refuse loudly if it does not).
2. **W37b:** sentence, grammar, lesson, strokes, speak_* still unpinned (values mostly in the index).
3. **B-W40:** 31,184 en misses held by the ratchet; the six W13b particle templates close 6,449 of them.
4. `audit_hygiene_all_locales.LEARNER_KEYS` still lists `prompt_pt` (harmless, no field carries it now).
5. `prototype` typecheck (`tsc`) runs out of memory on the data imports; the `speak.server.ts` change is a
   type rename checked by reading, not by the compiler.
6. The 12 orphan `localized_text` token rows W40's derivation found are untouched.
