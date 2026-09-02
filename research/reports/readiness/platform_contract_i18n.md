# Readiness — platform contract, IDs, i18n, delivery

> Area: `platform_contract_i18n`. Written 2026-09-02 against the committed export, `contracts/`,
> `design/*.md`, `prototype/`, and `db/corpus.sqlite` (read only, as a cross-check). Every count below
> was produced by running a script over the data; where a document and the data disagree, the
> disagreement is called out and adjudicated.
>
> **Headline.** The *content* contract is close to production-grade and is the strongest single asset
> in this repo. The *platform* contract — how the app gets that content, who the learner is, what
> version they are on, and what language the product speaks — does not exist yet. Nothing in
> `contracts/` describes a user, a review, a progress record, an audio asset, or a content release.
> The one consumer that exists (`prototype/`) does not read `contracts/manifest.json` at all; it
> re-keys the corpus into a second, undocumented address space and ships 59 MB of JSON inside the
> server bundle.

---

## 1. What this capability needs from the data

For "a full language app, like Duolingo but with integrated Anki (FSRS-6), tests, exams, simulations,
all in Portuguese", the data contract has to answer six questions a client and a server both ask:

1. **Addressing.** One durable public id per record; a route can be mounted from it; a cross-reference
   always resolves; a storage row number never leaks into a URL or a card key.
2. **Shape.** A machine-checkable schema per entity, so a client can be typed and a server can reject
   bad content at ingest rather than at render time.
3. **Catalogue.** One index that says what entities exist, where they live, how they are packed, and
   which field is the address — so an API mounts its routes from data, not from hand-written glue.
4. **Locale.** Learner-facing text addressed by locale, mechanical values locale-neutral, so adding
   `es-LA` is adding rows and translation work — never a schema change, never a code change in the
   consumer.
5. **Delivery.** A content *release*: a version, a hash, a size budget, a way to ship a delta and a
   way to invalidate a cache. A learner's progress has to be pinned to the content revision it was
   earned against.
6. **User state.** The half of the product the corpus does not contain: accounts, entitlement, FSRS
   cards and review logs, lesson completion, exam attempts, feature unlock state. This is where a
   real DB is chosen (`CLAUDE.md`: "we will pick a 'real' DB later"), and it has to key off the
   corpus's stable ids without embedding corpus content.

Plus two things the product needs that are content-shaped but not yet content: **audio assets** (the
owner will AI-generate) and **attribution/licensing** that survives a paid launch.

---

## 2. What exists today (verified)

### 2.1 The contract layer is real and it is enforced

`contracts/` holds 24 JSON Schema files (23 entity + `common.schema.json`), a catalogue
(`manifest.json`), a generated TypeScript view (`types.ts`, 19.8 KB), and the measured field
inventory (`_shapes.json`).

I re-derived every count in `contracts/manifest.json` from the files each entity's glob matches.
**All 21 declared record counts match the data exactly** — zero drift:

| entity | manifest | measured | files | MB |
|---|---:|---:|---:|---:|
| capability | 74 | 74 | 1 | 0.02 |
| conjugation | 1157 | 1157 | 3 | 3.46 |
| course | 4 | 4 | 4 | 0.02 |
| course_manifest | 1 | 1 | 1 | 0.00 |
| exam_item | 6048 | 6048 | 40 | 2.01 |
| exercise_conjugation | 18524 | 18524 | 3 | 10.60 |
| exercise_role | 5358 | 5358 | 3 | 2.47 |
| family | 396 | 396 | 1 | 0.72 |
| grammar | 496 | 496 | 3 | 2.13 |
| kana | 211 | 211 | 2 | 0.04 |
| kanji | 2131 | 2131 | 5 | 8.18 |
| lesson | 322 | 322 | 322 | 16.98 |
| reading | 286 | 286 | 3 | 1.22 |
| **sentence** | **5889** | **5889** | 1 | **51.00** |
| speak_path | 1 | 1 | 1 | 0.01 |
| speak_unit | 72 | 72 | 72 | 0.39 |
| stroke_kana | 162 | 162 | 1 | 0.15 |
| stroke_lines | 2098 | 2098 | 5 | 1.03 |
| stroke_order | 1233 | 1233 | 5 | 7.47 |
| topic | 52 | 52 | 52 | 0.55 |
| vocab | 7401 | 7401 | 5 | 11.37 |

(`capability_lesson_map` 266 keys and `kana_family` 2 keys are map-packed and carry `records: null`
by design.) Total catalogued: **119.88 MB**; `corpus/` is 99 MB and `course/` 22 MB on disk.

`python scripts/validate/validate_contracts.py` runs green: **51,918 records, 56,195 distinct stable
ids, 633,136 references resolved**, and it reports `0` vocab references still using the retired
headword scheme. `validate_schema_generation_is_current.py` additionally asserts that regenerating
`contracts/` reproduces the committed files byte-for-byte, so the schemas cannot silently drift from
the generator.

**The enum-vocabulary rule is the best idea in this repo.** 46 enums across the schemas, each
carrying an `x-vocabulary` owner: `design` 20, `producer` 14, `curated` 5, `measured` 2. Five enums
carry no owner block and all five are in the two hand-authored files (`common.schema.json`'s
`IdNamespace`/`Level`/`Layer`, `kana_family`'s two), which is correct. `additionalProperties: false`
appears 56 times, at the record root and one level in.

### 2.2 Addressing holds up under adversarial probing

- Every `stable_id_field` is unique within its entity (verified independently of the validator).
- The only cross-entity address collision is the documented one: **1,157 `vocab:<jmdict_id>` slugs
  answer to both a vocab record and its conjugation table.** `common.schema.json` names this and
  proposes the fix (`conj:<jmdict_id>`).
- 29 namespace prefixes are in use across declared addresses (`vocab` 8,558 — 7,401 vocab + 1,157
  conjugation; `cj` 18,524; `sent` 5,889; `rl` 5,358; `kanji` 2,131; …).
- `validate_stable_addresses.py` gates that every integer FK sits beside its published slug form, so
  a row number is never the only address. The integer `id`/`vocab_id` fields **are still exported**
  (0.18 MB of `vocab_id` inside `bank.json` alone), which is defensible as an internal join hint but
  is dead weight in a wire payload.
- 93 headwords are shared by 193 vocab records (100 records would be lost to a headword-keyed index);
  the courseware no longer references vocabulary that way, and
  `course/vocab_disambiguation_review.json` holds what could not be resolved from evidence.

### 2.3 Locale objects: shape is right, coverage is not uniform, nothing gates it

Across the whole export there are **175,119 locale objects**, of which **134,910 (77.0%) carry `en`**
alongside `pt-BR`. The key set is clean — only two distinct shapes exist (`{pt-BR, en}` and
`{pt-BR}`), and **zero** locale objects carry a key that is not one of those two.

| entity | locale objects | with `en` |
|---|---:|---:|
| family | 718 | 100.0% |
| grammar | 2387 | 100.0% |
| reading | 572 | 100.0% |
| vocab | 10593 | 100.0% |
| sentence | 116912 | 94.5% |
| kanji | 13992 | 73.0% |
| capability, kana, speak_*, course, topic, lesson, exercises | 26 945 | 0.0% |

Course/topic/lesson/exercise text being pt-BR-only is **policy** (`design/i18n.md`: "Excluded:
course, topic, lesson, exercise text"). The rest is not. Restricting to corpus-layer entities that
the policy says should be bilingual, **10,692 locale fields have no `en`**, concentrated in:

| field | count |
|---|---:|
| `kanji[].readings[].note` | 3679 |
| `sentence[].tokens[].role` | 1796 |
| `sentence[].tokens[].gloss` | 1580 |
| `sentence[].particles[].function` / `.explanation` | 998 each |
| `sentence[].tokens[].conjugation_note` | 435 |
| `sentence[].translation_literal` / `.structure_explanation` | 330 each |
| `kana[].family_label` | 211 |
| `kanji[].irregular_note` | 99 |
| `capability[].name` | 74 |
| `speak_unit.title` | 72 |
| `sentence[].translation` | 18 |

The 18 anchorless sentence translations are the explained residual from
`research/reports/en_anchor_backfill.md` (12 deliberate, 6 generated) — those are correct. The other
10,674 are an incomplete pass, not a policy. `kanji[].readings[].note` (the largest bucket) was never
in the i18n scope statement at all.

**No validator asserts locale parity.** `audit_hygiene_all_locales.py` walks both locales for
*quality* (leaks, mojibake, mixed script, accent-stripping over ~244k strings) but never for
*presence*. The user's own global pre-commit checklist lists "Locale parity — same keys across all
locale files"; the corpus has no such gate.

### 2.4 The `en_layer` field the owner approved does not exist yet

`grep -rn "en_layer"` over the whole repo returns **exactly one hit**: the proposal itself, in
`research/reports/PENDING.md:96`. It is approved (A7, "OK to all three") and unimplemented.

The measurement behind it, re-derived: `sentence.en` column (the Tatoeba/JEC Layer-A anchor) covers
**3,529** records; `localized_text` locale `en` (Layer-B derived) covers **2,342**; the two sets are
**disjoint** and their union is 5,871 — exactly the number of `translation.en` keys in `bank.json`.

The important part is that **`jp_source` is not a usable proxy** for it:

| `provenance.jp_source` | Layer-A anchor | Layer-B derived |
|---|---:|---:|
| `tatoeba` | 3402 | **135** |
| `jec` | 127 | 0 |
| `ai-generated` | 0 | 2207 |

135 Tatoeba-sourced sentences carry a *generated* English. A consumer that inferred "tatoeba ⇒ the
English is authoritative" would be wrong 135 times, and a validator that used `translation.en` as
ground truth for the pt-BR would be checking derived English against derived Portuguese.

The information already exists: `localized_text` has a **`layer` column** (109,976 `en` rows all
layer `B`; 109,941 `pt-BR` layer `B`; 29,913 layer `C`; 1,193 with layer `NULL`). The exporter simply
does not carry it into the locale object. This is a plumbing job, not a research job.

### 2.5 Audio: zero assets, and the slots are honest about it

- **311 records carry `audio: "pending"`** — 239 exam listening items (`lt`/`lp`/`ls`/`lr`/`lg`) and
  72 `speak_unit` records. There is no other audio field anywhere in the export, and no asset
  directory.
- The listening scripts are structured and ready for TTS: **855 script lines across the 239 items**,
  with speaker slots `F1` 342, `M1` 328, `N` 171, `F2` 8, `M2` 6.
- The schemas are already written so the first real filename will not fail the build
  (`exam_item.schema.json:26`, `speak_unit.schema.json:20`: "the literal `pending` … The first real
  filename must not fail the build") — so the contract is ahead of the assets, which is the right
  order.
- The SRS taxonomy declares a `listening` card type (`design/unlock_enums.json`) and **zero cards use
  it**: the 4,133 seed rows expand to 9,453 (item, card_type) pairs — `recognition` 4,133,
  `production` 4,133, `handwriting` 691, `cloze` 496, `listening` 0. `deck:phrases` is declared and
  has zero cards.
- Per-vocab and per-sentence pronunciation audio — the thing an Anki-style app actually needs most —
  has no slot in any schema at all.

### 2.6 Delivery: no API, one consumer, and it ignores the contract

`prototype/` is an SSR-only React Router 7 app. The SSR-only guarantee is genuinely enforced:
`validate_no_client_leak.py` runs 605 content probes plus size nets over `build/client` and passes —
**45 files / 538,286 bytes, no corpus content**. `validate_prototype_sync.py` re-derives all 16
`app/data/*.json` files in Python (a line-by-line port of `sync-data.mjs`) and deep-compares; it also
passes.

What those two green gates do **not** cover:

- **`prototype/scripts/sync-data.mjs` never reads `contracts/manifest.json`.** It hardcodes
  directory names, file-name regexes, and packing assumptions. Grepping for consumers of the
  manifest returns only Python (`scripts/contracts/*`, `scripts/export/export_course.py`, eight
  validators). The document that says "**An API reads this first**" (`contracts/README.md:12`) has
  no non-Python reader.
- **`contracts/types.ts` is imported by nothing.** The prototype carries **64 `any` annotations
  across 15 files** and declares its own inline shapes.
- **The prototype invents a second address space.** `sync-data.mjs` re-keys: kanji by `character`,
  grammar by `key`, vocab by the bare identifier after the colon, strokes by `character`, and the
  routes follow (`/kanji/:char`, `/vocabulario/:id`, `/gramatica/:key`). I checked all four for
  collisions and today there are **none** (kanji 2131/2131 distinct characters, grammar 496/496
  distinct keys, vocab 7401/7401 distinct identifiers). So it works — but it is an undocumented,
  unvalidated parallel key space, and the moment a homograph kanji or a duplicated grammar key
  appears it silently drops a record, exactly the way headword keying dropped 100 vocab.
- **Delivery is "bundle everything".** `prototype/app/data` is **59 MB of committed JSON**
  (deliberately, per `prototype/.gitignore`), and `build/server` is **62 MB**. Every deploy ships the
  whole corpus in the server image. There is no API, no pagination, no delta, no CDN story.
- **The prototype README is materially stale** against the data: it claims "213 lessons" (actual
  322), "reference-filtered snapshot … ~2 MB instead of ~21 MB" (actual: the whole slimmed bank,
  `sentences.json` 14.9 MB, `app/data` 59 MB), "build/client ~465 KB" (538 KB), "build/server
  ~10.8 MB" (62 MB), and lists `revisar`/`pratica` as placeholders when `routes.ts` now has real
  review, practice, drill, exam and speak routes.

**Payload composition of the 51 MB `bank.json`** (serialized values, 36.86 MB of content before
whitespace), because this is what any wire format has to fight:

| field | MB | share |
|---|---:|---:|
| `tokens` | 21.06 | 57.1% |
| `particles` | 5.49 | 14.9% |
| `structure_explanation` | 4.39 | 11.9% |
| `provenance` | 1.13 | 3.1% |
| `pattern` | 1.00 | 2.7% |
| everything else | 3.79 | 10.3% |

Inside `tokens` (49,756 of them, 16 keys each), the *values* account for only 7.86 MB of the 21.06 MB
— **roughly 13 MB of `bank.json` is repeated JSON key names and punctuation**. Separately, the `en`
half of every locale object is **6.33 MB, 17.2% of the bank**, and `common.schema.json` says `en` is
"kept for auditing, not for display". A production read model that dropped `en`, the integer
`vocab_id`, and `pos_coarse`/`pos_fine` from the client-facing projection would shed a third of the
sentence payload without losing a single learner-visible field.

### 2.7 Feature gating exists as a taxonomy and is 25% wired

`design/unlock_enums.json` declares **16 app features**. Across all 322 lessons there are exactly
**4 feature unlocks**: `feat:srs-reviews`, `feat:conjugation-drill`, `feat:jlpt-sim-n5`,
`feat:jlpt-sim-n4`. The other twelve — `kana-input`, `furigana-toggle`, `romaji-toggle`,
`kanji-lookup`, `handwriting-input`, `particle-drill`, `phrase-builder`, `listening`, `voice-mode`,
`find-correct-kanji`, `find-correct-particle`, `visual-novel` — are never turned on by any lesson.
`needs[]` is present on all 322 lessons and **non-empty on zero** of them, so the prerequisite half
of the unlock graph is declared and unpopulated (this is A7 in `PENDING.md`).

### 2.8 User state: designed in prose, absent from the contract

`design/fsrs_integration.md` specifies CARD and REVIEW_LOG tables properly (review log as source of
truth, memory state as a derived cache tagged with `fsrs_version`, FSRS-6 defaults + DR 0.90,
optimize at ~1000 reviews). None of it is in `contracts/`: the manifest's 23 entities are all
content. There is no schema for a user, an entitlement, a lesson completion, an exam attempt, or a
feature-unlock state, and `validate_contracts.py` therefore cannot check any of it.

Two small mismatches between that doc and the shipped address space, worth fixing before code is
written against it: the card-minting table writes `sentence:NNN` and `grammar:NNN` where the corpus
uses `sent:` and `gram:`, and `kanji:NNN` where the corpus uses the character (`kanji:食`). And the
doc's kanji card kinds (`#reading`, `#meaning`) do not match the seeds actually exported
(`recognition`, `production`, `handwriting`).

### 2.9 Attribution and licensing for a paid app

The prose record (`ATTRIBUTION.md`), the machine record (`dataset_source` in the SQLite), and the
in-app credits screen (`prototype/app/routes/creditos.tsx`) **disagree with each other**, and nothing
validates any of them.

Sources that appear as a `source` value on shipped records:

| shipped `source` | records | in `ATTRIBUTION.md`? | in `dataset_source`? | on the credits page? |
|---|---:|---|---|---|
| `kanjialive` (stroke_order) | 1233 | **no section** | **no** | yes (CC BY 4.0) |
| `glyphwiki` (stroke_lines) | 2098 | yes | **no** | yes |
| `strokesvg` (stroke_kana) | 162 | **no section** | **no** | yes (MIT + OFL) |
| Unicode Unihan (radical) | all kanji | yes | **no** | yes |

Conversely, **KanjiVG** has a full section in `ATTRIBUTION.md`, a row in `dataset_source`, and the
open ShareAlike legal flag in `design/sources.md` — but the only thing shipped from it is
`kanjivg_ref`, an id pointer that `design/license_audit.md` itself classifies as a non-copyrightable
fact. The attribution record describes a source whose creative output we no longer ship, and omits
two whose output we do.

`dataset_source` has **9 rows**, four of them with `license: 'verify'` and seven with no SHA256, and
it lives in `db/corpus.sqlite`, which is **git-ignored**. So the artifact `ATTRIBUTION.md` calls "the
machine-readable provenance" is not a committed artifact and is missing SudachiDict, jaconv,
GlyphWiki, Kanji Alive, strokesvg, Unihan, and six of the eight JLPT consensus lists. `STATE.md`'s
own "Dataset manifest (versions + checksums)" table is entirely empty (`—` in every cell).

One substantive licensing gap: **Tatoeba is CC BY 2.0 FR and per-sentence contributor credit is not
preserved.** `ATTRIBUTION.md` says it "should be preserved where feasible"; `raw_tatoeba_sentence`
has columns `(id, text, has_audio)` and no author, so it is not recoverable from what we stored.
3,549 shipped sentences come from Tatoeba. The bulk-attribution line on the credits page is the
common industry reading and is probably defensible, but it is an owner call that has not been
recorded as taken.

### 2.10 Two documented facts the data contradicts

Both are small, both are the kind of thing that erodes trust in an otherwise excellent document:

- **`contracts/README.md:104`** states that `measured` enums "There are currently **none**." There
  are **two**, both in `speak_unit.schema.json`: `fluency.kind` → `["recap","situation"]` and
  `production[].kind` → `["on-topic","review","same-stage"]`. `speak_unit` has 72 records, above the
  generator's 50-record floor, so the filter let them through. By the README's own argument these are
  traps: the next legitimate `kind` fails the gate, and the documented remedy (regenerate) re-blesses
  it — the exact tautology the layer was built to eliminate. The fix is trivial and the owner already
  exists: both values are emitted by `scripts/export/build_speaking_practice.py:259` and `:309` and
  documented in `design/speaking_path.md:151,169,172`, so they should be reclassified `producer` or
  `design`, not left `measured`.
- **`STATE.md` says "39 hard validators."** `validate_all.py`'s `SUITE` has **42 entries, 40 gating
  and 2 advisory** (`completeness_audit.py`, `detect_ai_tells.py`) — `validate_furigana.py` was
  promoted from advisory to gating and the count was not updated. The data is right; the state file
  is one behind.

Also: `contracts/` — the layer an API is supposed to mount from — is referenced **zero times** in
`INDEX.md`, `CLAUDE.md` and `README.md`, the three documents that exist to be read first.
`research/reports/APP_PLAN.md`, cited from `PENDING.md`, does not exist.

---

## 3. Gaps

Ordered by what blocks the most downstream work.

### G1. No user-state contract (M) — blocks everything interactive
**Missing.** Schemas + manifest rows for `user`, `card`, `review_log`, `lesson_progress`,
`exam_attempt`, `feature_state`, keyed by the corpus's stable ids. `design/fsrs_integration.md` has
the CARD/REVIEW_LOG shape in prose; nothing turns it into an enforced contract, and
`validate_contracts.py`'s three checks (shape / identity / graph) cannot reach it.
**Why it matters.** Without it there is no FSRS, no progress, no "continue where you left off", no
entitlement, no exams that count. It is the half of the product the corpus deliberately does not
contain.
**Depends on.** Nothing in the data. It needs the owner's DB choice only for the physical schema; the
*logical* contract can and should land first, as `contracts/*.schema.json` files like every other
entity.
**AI-authorable now?** Yes for the schemas, the id conventions and the card-minting rules. The DB
choice and the hosting model are owner decisions.

### G2. No content release identity (S) — blocks safe shipping
**Missing.** A corpus version, a per-entity content hash, and a build timestamp in
`contracts/manifest.json`. Today only `course/manifest.json` carries `generated: "2026-09-02"`;
`contracts/manifest.json` has `schema_version: "1.0"` and no date, no hash. No record carries a
revision or `updated_at`.
**Why it matters.** A learner's FSRS card is a memory trace attached to `vocab:1385390`. When that
record is re-pointed (A9 in `PENDING.md` migrates 22 vocab slugs across 5,955 occurrences), the app
has to know which content revision the card was earned against and what changed. Without release
identity there is no cache invalidation, no delta update, no rollback, and no way to answer "why did
this lesson change under me".
**Depends on.** Nothing. It is additive to the manifest and the exporter.
**AI-authorable now?** Yes, fully.

### G3. `en_layer` on locale objects (S) — approved, unbuilt
**Missing.** The per-string provenance the DB already stores (`localized_text.layer`) is dropped at
export, and the Layer-A anchor lives in a different storage location (`sentence.en`) from the
Layer-B derived English, with nothing in the JSON distinguishing them.
**Why it matters.** 3,529 anchors vs 2,342 derived, and `jp_source` mis-classifies 135 of them. Any
future validator that checks pt-BR against the English — the whole point of keeping `en` — has to
know which English is evidence and which is a sibling guess.
**Depends on.** Nothing; the data exists in `db/corpus.sqlite` today.
**AI-authorable now?** Yes. The only question needing the owner is the field name/shape (per-locale
`{value, layer}` vs a sibling `en_layer` map), and A7 already approved the direction.

### G4. Locale parity is unmeasured and unenforced (S data, M to backfill)
**Missing.** (a) A validator that asserts, per field, whether `en` is required, and fails on a
regression. (b) The 10,674 unexplained missing `en` values, `kanji[].readings[].note` (3,679) first.
(c) A written scope table — `design/i18n.md` names grammar, families, sentences, tokens, particles
and excludes course/lesson/exercise, but says nothing about kanji reading notes, kana family labels,
capabilities or the speaking path.
**Why it matters.** "pt-BR is a locale module, expandable with no structural change" is the project's
own claim. It is currently true of the *schema* and false of the *content*: 77% coverage with no gate
means the next locale starts from an unknown baseline.
**Depends on.** The scope table (a decision) before the backfill (a campaign).
**AI-authorable now?** The validator and the backfill, yes. The scope table is a 15-minute owner call.

### G5. No API contract, and the one consumer bypasses the one we have (M)
**Missing.** An API surface derived from `contracts/manifest.json`: route shapes, a read model per
entity, pagination, and a projection that strips audit-only fields. Plus the reverse: make
`sync-data.mjs` (or its successor) *read* the manifest instead of hardcoding globs, and make the
prototype import `contracts/types.ts` instead of 64 `any`s.
**Why it matters.** Right now the contract and the consumer agree by luck and by
`validate_prototype_sync.py`, which pins the projection but does not derive it. The prototype's
second address space (`/kanji/:char`, `/vocabulario/:id`, `/gramatica/:key`) is collision-free today
and unguarded against tomorrow. And "bundle 59 MB into the server image" does not survive contact
with a paid app that ships content updates.
**Depends on.** G2 (release identity) to be useful; G1 to be complete.
**AI-authorable now?** Yes.

### G6. Audio strategy: 311 pending slots, and the slots that matter do not exist (L)
**Missing.** (a) The assets: 855 listening script lines across 239 exam items, 72 speak units. (b) An
`audio` slot on `vocab` and `sentence` — an Anki-style app needs per-word and per-sentence audio and
there is nowhere to put it. (c) An asset contract: storage layout, naming from the stable id, format,
voice/speaker registry (`F1`/`M1`/`N`/`F2`/`M2` are used but defined only in `design/listening.md`),
licence of the TTS output, and a validator that every non-`pending` filename resolves.
**Why it matters.** No audio means no listening section (5 of the exam's sections, 239 items), no
shadowing, no `listening` SRS cards (declared, zero authored), and no `voice-mode` feature. Also a
verification problem: AI-generated Japanese TTS gets pitch accent and long vowels wrong often enough
that unreviewed audio would teach wrong pronunciation — and the corpus already carries the pitch data
(kanjium, 1,221/1,359 N5+N4) that a check could use.
**Depends on.** The owner's TTS vendor choice (licence of the output matters for a paid app).
**AI-authorable now?** The schema, the naming convention, the validator and the generation pipeline,
yes. The voice choice and the QA sign-off are the owner's.

### G7. Attribution record is behind the shipped data (S)
**Missing.** Sections for Kanji Alive and strokesvg in `ATTRIBUTION.md`; `dataset_source` rows for
Unihan, GlyphWiki, Kanji Alive, strokesvg, SudachiDict, jaconv and the six unlisted JLPT lists;
licences and SHA256 for the four `'verify'` rows; a decision recorded on KanjiVG (we ship only
`kanjivg_ref`, so the CC BY-SA 3.0 flag may be closable); a recorded owner ruling on bulk-vs-per-sentence
Tatoeba credit; a committed home for the machine-readable record (it currently lives only in the
git-ignored SQLite); and `STATE.md`'s empty dataset manifest table filled in.
**Why it matters.** This is a paid product. The credits page is the most complete of the three
records and it is the one nobody validates. A licence claim that does not match what ships is the
cheapest possible legal exposure to avoid.
**Depends on.** Nothing mechanical. The KanjiVG and Tatoeba-credit calls are the owner's.
**AI-authorable now?** The reconciliation and the validator, yes; the two rulings, no.

### G8. Reclassify the two `measured` enums and fix the README claim (S)
**Missing.** `speak_unit.fluency.kind` and `speak_unit.production[].kind` need
`x-vocabulary.owner: "producer"` pointing at `build_speaking_practice.py`, and
`contracts/README.md:104` needs to stop claiming there are none.
**Why it matters.** Small, but it is the one place the contract layer violates its own central rule,
and the rule is the reason to trust the layer.
**AI-authorable now?** Yes, in minutes.

### G9. Feature-unlock and `needs[]` graph is 25% / 0% populated (M)
**Missing.** 12 of 16 declared features are never unlocked; `needs[]` is empty on all 322 lessons.
**Why it matters.** The app cannot know when to enable kana input, furigana toggles, handwriting,
listening or the drills; and without `needs[]` the dependency graph is inferred from lesson order
rather than declared, so a non-linear path (the speaking track, a placement test) has nothing to
check against.
**Depends on.** A7 in `PENDING.md` — the owner has approved deciding it, not the shape.
**AI-authorable now?** Yes, derivable from `cumulative_known_set` deltas and from which lesson first
renders each exercise type; needs owner sign-off on the resulting placement.

### G10. Documentation integrity (S)
`prototype/README.md` (five verifiably wrong numbers), `INDEX.md`'s "Current state (2026-06-14)"
block (250 kanji, 1 lesson — the file `CLAUDE.md` calls "the map an LLM reads first"), `contracts/`
absent from all three index documents, `STATE.md`'s 39-vs-40 validator count, and the missing
`research/reports/APP_PLAN.md`.
**AI-authorable now?** Yes.

---

## 4. Quality risks against the near-100% goal

1. **The contract certifies conformance, not correctness — and it is easy to read it as the latter.**
   `validate_contracts.py` proving 633,136 references resolve says nothing about whether
   `sent:tatoeba-83013` is the *right* sentence for that lesson. Green gates in a repo this
   well-instrumented invite exactly that conflation. Every open item in `PENDING.md` section A and B
   is a correctness defect that the contract layer passes clean.
2. **Two consumers of one dataset, one of them unvalidated by shape.** `app/data` is guarded by a
   deep-compare against a Python port of the sync script, which is strong; but nothing checks that
   the *projection* is still the right projection after a schema change, and the projection is where
   the locale collapse happens (`slimToken` reduces `gloss`/`role` to a bare pt-BR string). A new
   locale silently does not reach the app.
3. **`pt-BR` is compiled in, not configured.** `corpus.server.ts` has `export const PT = "pt-BR"` as a
   module constant, the routes are Portuguese URLs (`/licao`, `/vocabulario`, `/gramatica`,
   `/simulado`, `/creditos`), and there are ~250 hardcoded accented literals across 36 files with no
   i18n library. The *data* is locale-ready; the *product* is not, and the gap will only get more
   expensive.
4. **Audit-only data is shipped to the learner's device.** 6.33 MB of `en` in the sentence bank
   alone, plus integer row ids, plus third-party analyzer fields (`pos_coarse`/`pos_fine`) the UI
   never renders. It is not a leak — SSR keeps it server-side — but it is a third of the payload of
   the single largest artifact, and it also means a future client-side cache would carry the audit
   trail.
5. **A licence claim that does not match what ships.** Two shipped sources have no attribution
   section; one attributed source ships nothing copyrightable; the machine-readable record is
   git-ignored and 60% incomplete. This is the only risk in this area that is not fixable after
   launch.
6. **Address churn is coming and there is no redirect layer.** A9 re-points 22 vocab slugs across
   5,955 export occurrences; A3 merges two grammar records (1,431 refs). `contracts/README.md`
   promises a stable id "never changes once published". Both migrations are correct and should
   happen — but they must happen **before** any external consumer or any learner's FSRS card holds
   the old id, and there is no alias/redirect table in the contract to soften it if they do not.
7. **`needs_review: true` is universal and therefore uninformative.** All 5,889 sentences carry it;
   322 lessons carry it. A reviewer cannot triage by it. For a "teachers validate later" model, the
   review queue needs a priority signal the data does not currently carry.

---

## 5. Recommended sequence

Cheap and unblocking first; nothing here waits on the exam or content campaigns.

1. **G8 + G10 + the `STATE.md` count** (hours). Fix the two `measured` enums, the README claim, the
   stale prototype README numbers, and add `contracts/` to `INDEX.md`. Restores the documents to
   being trustworthy before anyone builds on them.
2. **G2 — release identity** (hours). Add `generated`, `corpus_version` and a per-entity content hash
   to `contracts/manifest.json`; teach `validate_schema_generation_is_current.py` to check them.
   Everything downstream (caching, deltas, progress pinning, migration safety) needs this to exist
   first, and it is additive.
3. **G3 — `en_layer`** (hours to a day). Carry `localized_text.layer` into the export and split the
   `sentence.en` anchor from the derived English. It is approved, the data exists, and it unblocks
   any pt-BR-vs-English verification pass.
4. **G4a — the locale-parity validator + the scope table** (a day, one short owner call). Land the
   gate *before* the backfill so the backfill has a target and a regression is impossible afterwards.
5. **G7 — attribution reconciliation** (a day, two owner rulings). Bring `ATTRIBUTION.md`,
   `dataset_source` (moved to a committed JSON under `design/` or `contracts/`) and the credits page
   into agreement, and add a validator that fails when a `source` value on a shipped record has no
   attribution entry. Do this before launch, not after.
6. **G1 — the user-state contract** (a week). Author `user`, `card`, `review_log`, `lesson_progress`,
   `exam_attempt` and `feature_state` as `contracts/*.schema.json` with manifest rows, keyed off
   stable ids, following `design/fsrs_integration.md` and fixing its three namespace mismatches
   (`sent:`/`gram:`/`kanji:<char>`, and the kanji card kinds). Ship the logical contract before the
   DB choice; the DB then implements a contract rather than inventing one.
7. **G5 — API surface from the manifest** (a week+). Define the read model per entity (drop `en`,
   integer ids and analyzer fields from the learner projection), make the consumer read the manifest,
   and adopt `contracts/types.ts` in the prototype. Then the 59 MB bundle becomes a served corpus and
   the second address space becomes either documented or retired.
8. **G9 — feature unlocks and `needs[]`** (in parallel with 6–7, after the A7 decision).
9. **G6 — audio** (parallel track, longest lead time). Land the asset contract and the `vocab`/
   `sentence` audio slots first, so generation has somewhere to write; then the 855 exam lines and 72
   speak units; then per-vocab pronunciation. Treat pitch-accent verification against `vocab_pitch`
   as part of the pipeline, not as post-hoc QA.

The address migrations already approved (A9's 22 vocab, A3's two grammar merges) should be sequenced
**after step 2** — so the release identity records the break — and **before** step 6, so no card ever
holds a slug that is about to move.
