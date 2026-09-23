# W40: en backfill derivation (the mechanical half)

> **2026-09-23.** Measurement and derivation only. The DB was read from a `sqlite3.backup()` snapshot, and
> every number was produced by script over the committed export (`corpus/`) plus that snapshot. No corpus,
> course, contract, script or DB file was written. No exporter or apply step was run, and git state was not
> changed.
>
> **Concurrency note.** While this unit ran, the DB writer ingested 97 sentences (the batch-30 late-resolved
> set: 10,112 → 10,209) and re-exported at 01:23. The first pass (01:16 snapshot) was discarded. Every number
> below comes from a second snapshot taken after that write. That snapshot matches the export on disk exactly,
> and the reconciliation in §2 is exact on all 13 fields.
>
> Outputs:
> - [`research/derived/pending/en_backfill_derived.json`](../derived/pending/en_backfill_derived.json):
>   26,438 rows
> - [`research/derived/pending/en_backfill_residue.json`](../derived/pending/en_backfill_residue.json):
>   31,129 rows, of which 31,111 are the authoring work list and 18 are the named exemptions, kept as the
>   input to R7
>
> Scripts (scratch, not committed): `derive.py` (measure, derive, back-test) and `finalize.py` (write and
> self-check). The self-checks assert that every export gap maps to exactly one row, that no row appears
> twice, that every derived row is layer B with a non-empty `en`, and that exactly 18 rows are exempt.

---

## 1. Headline

| | design (2026-09-02) | **today** |
|---|---:|---:|
| sentence records | 5,889 | **10,209** |
| required-scope en gap | 10,532 | **57,567** |
| named exemptions (`sentence.translation`) | 18 | **18** (the same 18 slugs; all still resolve and still lack en, so R7 passes) |
| **backfill** | 10,514 | **57,549** |
| derived mechanically (this table) | — | **26,438 (45.9%)**, of which 21,920 high and 4,518 medium |
| residue (authoring work list) | — | **31,111 rows ≈ 20,300 distinct authoring units** |
| content-only / plumbing-first | 6,467 / 4,047 | **53,502 / 4,047** |

**Why the gap grew five-fold.** The 4,223 mined N3 sentences (W13b) and the 97 batch-30 ones got a full pt-BR
Layer B, but no en pass ran afterwards. Their `translation` did get an en: 10,191 of 10,209 carry one. Every
other sentence-level Layer-B field on those records is pt-BR only. The growth is all sentence-side. The
plumbing-first part (4,047) has not moved.

**Is the en already in the index (the W37 question)?** No. For every field, the `localized_text` rows with
`locale='en'` match the export's en count exactly. The only difference is **12 orphan `localized_text` rows**
(token gloss 5, role 5, conjugation_note 2, each with both pt-BR and en) whose `token.id` no longer exists.
That is a hygiene defect for the DB writer and has nothing to do with coverage. The research/derived work
files carry only the sentence translation (`paragraphs[].en`, an authoring input), and a grep for
`*_en` Layer-B keys under `research/derived` finds nothing. There is no hidden en to recover. This is not
W37's dropped-field case.

**`translation_layer` census on today's data** (this replaces the design's 3,529 / 2,342 / 18):
**A 7,849** (`sentence.en` column) + **B 2,342** (`localized_text` en) + **absent 18** = 10,209. The anchor
and derived sets are still disjoint (overlap 0), so the exporter rule and its invariants hold unchanged.
Only the expected numbers need updating: `design/i18n.md` invariant 3, and the plant proof, which becomes
7,848 / 2,342 / 19 and then 7,848 / 2,343 / 18.

---

## 2. Per entity and field (reconciled 1:1 against the export)

| entity.field | gap | derived | residue | derivable | plumbing? |
|---|---:|---:|---:|---:|---|
| sentence.tokens[].gloss | 18,996 | 15,155 | 3,841 | **79.8%** | no |
| sentence.tokens[].role | 1,796 | 901 | 895 | 50.2% | no |
| sentence.tokens[].conjugation_note | 435 | 5 | 430 | 1.1% | no |
| sentence.particles[].function | 11,486 | 9,846 | 1,640 | **85.7%** | no |
| sentence.particles[].explanation | 11,489 | 265 | 11,224 | 2.3% | no |
| sentence.translation_literal | 4,650 | 0 | 4,650 | 0% | no |
| sentence.structure_explanation | 4,650 | 0 | 4,650 | 0% | no |
| sentence.translation | 18 | — | — (18 exempt) | n/a | no |
| **sentence** | **53,520** | **26,172** | **27,330** | **48.9%** | |
| kanji.readings[].note | 3,679 | 0 | 3,679 | 0% | **yes** |
| kanji.irregular_note | 99 | 0 | 99 | 0% | **yes** |
| **kanji** | **3,778** | **0** | **3,778** | 0% | |
| vocab.notes (`vocab:1928100`) | 1 | 0 | 1 | 0% | **yes** |
| kana.family_label | 211 | 210 | 1 | 99.5% | **yes** |
| kana_family.label | 57 | 56 | 1 | 98.2% | **yes** |
| **total** | **57,567** | **26,438** | **31,111** + 18 exempt | **45.9%** | |

The registry fields whose en is Layer A (`kanji.meanings`, `kanji.example_words[].gloss`,
`vocab.senses[].gloss`) have **0 gaps**, and so do grammar, family and reading. The rules the brief listed
for them (KANJIDIC2, JMdict by sense, grammar/family labels from the index) therefore have nothing to fill
there. JMdict turns out to be useful one level down, for **token** glosses (§3).

**All 26,438 derived rows are layer B.** No gap sits on a field whose `en_layer` is A. A token gloss copied
from JMdict is still a per-token gloss, and CLAUDE.md §1.1 files those under Layer B, so `row.layer = "B"`
and the scope table's `B (const)` for `tokens[].gloss` stays true. The JMdict origin is recorded in `source`.

Row addressing: `entity` / `id` / `field` / `locator` name the export locale object. The locator follows the
exporter's own order: tokens `ORDER BY split_mode, position`, particles by rowid, kanji readings kun → on →
nanori. `db` names the `localized_text` row the apply writes. The kana rows have `db: null` because they are
builder literals.

---

## 3. Rules and their leave-one-out back-test

Each rule was re-run on every instance that already has an en, with that instance's own en removed from the
memory. "exact" means the same string. "overlap" means the two share a `;`/`,`/`/`-separated item.

| field | rule | conf | fired | exact | overlap | rows derived |
|---|---|---|---:|---:|---:|---:|
| tokens[].gloss | `tm-lemma`: index en for the identical pt-BR on the same lemma | high | 15,410 | 99.9% | 99.9% | 8,746 |
| | | medium | 3,205 | 98.6% | 99.6% | 2,732 |
| | `jmdict-sense-join`: pt-BR is exactly one vocab sense's pt-BR glosses joined with `; ` (the W13b "registry" origin); en = that JMdict sense's first three English glosses | high | 82 | 41.5% | 87.8% | 3,144 |
| | `jmdict-sense-element`: pt-BR equals one gloss of exactly one sense | medium | 144 | 4.2% | 84.7% | 343 |
| | `tm-pt`: bare pt-BR string, capped at medium | medium | 486 | 98.1% | 98.8% | 190 |
| tokens[].role | `tm-pos` | high | 18,380 | 100.0% | 100.0% | 798 |
| | | medium | 2,439 | 99.6% | 99.6% | 86 |
| | `tm-pt` | medium | 256 | 99.6% | 99.6% | 17 |
| tokens[].conjugation_note | `tm-lemma` | high / medium | 2,121 / 1,315 | 100.0% / 99.7% | | 1 / 4 |
| particles[].function | `tm-particle` on (particle, function_type, pt-BR) | high | 8,830 | 99.9% | 99.9% | 8,700 |
| | | medium | 1,557 | 99.1% | 99.2% | 1,136 |
| | `tm-pt` | medium | 79 | 100% | 100% | 10 |
| particles[].explanation | `tm-particle` on (particle, pt-BR) | high / medium | 166 / 206 | 100% / 100% | | 265 / 0 |
| kana.family_label, kana_family.label | `kana-family-template`: "Família do X" → "X family" | high | — | — | — | 262 |
| | `kana-label-identity`: "っ (Sokuon)" has no Portuguese in it, so en is the same string | high | — | — | — | 4 |

Confidence for the translation-memory rules: unanimous with n ≥ 2 → high; n = 1, or a ≥ 80% majority with
n ≥ 3 → medium. A context key with conflicting en does **not** fall back to the broader key; the row goes to
the residue as `ambiguous-precedent` with up to three candidates (266 rows).

**How to read these numbers.**
- **The TM rules score about 99% by construction.** The 2026-06-25 en pass translated each distinct pt-BR
  string once (`design/i18n.md`), so reusing the en of an identical string reproduces exactly what that
  pipeline would have written. The back-test shows the rule is faithful to the pipeline. It does not show
  the pipeline was right in every context. That risk is the same as for the ~27k token glosses already
  shipped.
- **JMdict scores low on "exact" only because of style.** The existing en is a translation of the pt-BR, not
  of JMdict. I read 25 of the 32 zero-overlap cases by hand. Most are paraphrase-equivalent: 背 "back" vs
  "back (of the body)"; 渡す "to deliver" vs "to hand over; to pass; to give". Two are real sense misses, and
  both come from `jmdict-sense-element`: 先 ponta → "ahead; front", and 良い bem → "good; fine; nice". The
  cause is that taking the first three en glosses can drop the element's own meaning. That is why the rule
  is medium.
- **Rejected rule:** `literal-equals-natural` (when the pt-BR literal equals the pt-BR natural translation,
  en literal := en translation). It scored 5 of 8 exact, 62.5%, too weak even for the 2 rows it would have
  filled. Those 2 rows stay in the residue.

**Suggested verification** (Opus author/verify split per project memory): spot-check the high rows. Verify
the 4,518 medium rows and the 3,144 `jmdict-sense-join` rows, since the JMdict English is a different style
from its neighbors in the same sentence.

---

## 4. The residue: 31,111 rows, about 20,300 distinct authoring units

| field | rows | distinct pt-BR | class |
|---|---:|---:|---|
| particles[].explanation (W13b templates) | 6,449 | **6 templates** | `template-author-once` |
| particles[].explanation (other) | 4,775 | 4,492 | `no-precedent` |
| translation_literal | 4,650 | 4,650 | `no-precedent` |
| structure_explanation | 4,650 | 4,650 | `pedagogy-prose` |
| tokens[].gloss | 3,841 | 1,672 | `no-precedent` 3,578 + `ambiguous-precedent` 263 |
| kanji.readings[].note | 3,679 | 2,609 | `pedagogy-prose` 2,482 + `pedagogy-template` 1,197 (a pt-BR string that recurs) |
| particles[].function | 1,640 | 1,077 | `no-precedent` |
| tokens[].role | 895 | 650 | `no-precedent` 892 + `ambiguous-precedent` 3 |
| tokens[].conjugation_note | 430 | 389 | `no-precedent` |
| kanji.irregular_note | 99 | 99 | `pedagogy-prose` |
| vocab.notes | 1 | 1 | `pedagogy-prose` |
| kana (ー "Vogal longa") | 2 | 1 | `no-precedent` |

**The largest single saving is 6 strings.** The six W13b particle-explanation templates (`wa-topic` 2,421,
`wo-object` 1,205, `no-link` 1,030, `ga-subject-of` 868, `te-link` 862, `ga-subject` 63) have **no en
precedent at all**: 0 matches among the existing en explanations, so no template can be learned from the
index. Their slots are Japanese chunks and lemmas, which do not change between locales. **Author 6 en
templates once and fill the slots mechanically, and 6,449 rows close.** Each residue row carries `template`
and `slots` for this. Authoring the template is authoring; filling it is not. It should be a one-page review
item.

**D15.** If `kanji.readings[].note` and `irregular_note` flip to optional, the residue drops by 3,778 rows
(2,708 distinct strings) and the plumbing work drops to kana plus one vocab note. The recurring nanori notes
come in at least six near-duplicate phrasings of one idea, and those six alone account for 466 rows. That is
a pt-BR consistency defect worth normalizing *before* translating.

---

## 5. Exporter plumbing each derived or residue field needs (4,047 rows, unchanged)

Line numbers are from today's tree; the design report's numbers have drifted.

| field | rows | call site today | change needed |
|---|---:|---|---|
| kanji.readings[].note | 3,679 | `scripts/export/export_corpus.py:201` `"note": loc(pt=r[5]) if r[5] else None`; the subselect at `:210-211` reads `locale='pt-BR'` only | add a second subselect for `locale='en'` and pass `en=` |
| kanji.irregular_note | 99 | `export_corpus.py:215-217` (query, pt-BR only) and `:248` `loc(pt=irr_note[0])` | fetch the en row and pass `en=` |
| vocab.notes | 1 | `export_corpus.py:316` `loc(pt=VL.get((vid,"notes")))` | add a `VLen` map (the grammar/family pattern, `get_all(con, …, "en")`) and pass `en=` |
| kana.family_label | 211 | `scripts/ingest/build_kana.py:113` `{"pt-BR": label}` literal | builder literal: emit `"en"` beside it from the same template (`f"{lbl} family"` for base/dakuten/handakuten/yoon; identity for sokuon; chouon needs its one authored string) |
| kana_family.label | 57 | `build_kana.py:115` `{"pt-BR": label}` literal | same. The DB `kana_family` has only `label_pt`, so either add `localized_text` rows or keep it a builder literal (W37's builder-literal ruling covers this) |

Every sentence-side field already passes `en=`: `export_corpus.py:639-641` (tokens), `:648-649`
(particles), `:657-658`, `:665`. For those 53,502 rows, applying the table is `localized_text` inserts plus a
re-export. `build_kana.py` truncates and rebuilds `kana` / `kana_family` in the DB, so it runs under the
single DB writer.

The `translation_layer` exporter rule now belongs after **`:657`** (the design says `:517`).

---

## 6. The three dead `LocaleText` fields: still dead, recommend **delete**

| field | instances today | null | any data anywhere? |
|---|---:|---:|---|
| kanji.notes | 2,131 | 2,131 (100%) | `kanji.notes_pt` 0 non-null; no `localized_text` `(kanji, notes)` |
| family.description | 707 (was 396) | 707 (100%) | `family.description_pt` 0 non-null; no `localized_text` `(family, description)` |
| family.members[].note | 4,969 (was 2,572) | 4,969 (100%) | `family_member.note_pt` 0 non-null |

There is nothing to populate from. Populating would mean new Layer-C authoring on 3 fields that no consumer
has asked for. **Recommend deleting them**: `export_corpus.py:247` (`"notes"`), `:534` (`"description"`),
`:530` (`"note": loc(pt=note)`), the `notes` / `description` / `members[].note` properties in
`contracts/kanji.schema.json` and `contracts/family.schema.json`, and `types.ts`, and remove their scope rows
so R3 goes green. Not done here (proposal only).

**`speak_unit.*.prompt_pt`: still 284** (fluency 71 + production 213), built at
`scripts/export/build_speaking_practice.py:272` and `:324` (the design said `:258` / `:310`). This is
optional-scope courseware, so it adds no en work, only the rename to a `LocaleText` `prompt`.

---

## 7. Proposed follow-ups (not done: contracts and design are read-only for this unit)

1. `design/i18n.md`: refresh the "carries en today" column and the totals (145,442 / 10,532 are stale), the
   `translation_layer` census (§1), and the moved line numbers. The **ratchet baseline** for
   `validate_locale_parity.py` must be built from the per-field misses at apply time (§2), not from 10,514.
2. DB writer: delete the 12 orphan token `localized_text` rows.
3. Normalize the near-duplicate nanori note phrasings (§4) before any en pass on kanji notes.
4. Apply order: plumbing (5 call sites) → insert derived rows (layer B) → re-export → the parity validator
   then shows 31,111 remaining. Close the 6 templates next (−6,449).
5. The table is keyed by DB ids (`db.entity_id`) and export locators, both taken from the 01:2x snapshot.
   If more sentences are ingested before apply, re-run `derive.py`. It takes about 5 s after the snapshot and
   is idempotent.

---

## 8. Twenty sample rows (stratified by field × rule)

| id | locator.field | pt-BR | en | rule | conf |
|---|---|---|---|---|---|
| sent:tatoeba-136695 | tokens[3].gloss | felicidade | happiness | tm-lemma | medium (n=1) |
| sent:tatoeba-10224902 | tokens[0].gloss | estado, condição (de saúde) | state, condition (of health) | tm-lemma | medium |
| sent:tatoeba-202670 | tokens[5].gloss | fazer | to do | tm-lemma | high (n=311) |
| sent:tatoeba-80376 | tokens[7].gloss | bom | good | tm-lemma | high (n=7) |
| sent:tatoeba-213503 | tokens[5].gloss | estar | to be | tm-lemma | medium |
| sent:tatoeba-87578 | tokens[0].gloss | ela | she | tm-lemma | high (n=106) |
| sent:tatoeba-192778 | tokens[12].gloss | decidir, resolver | to decide, to resolve | tm-lemma | medium |
| sent:tatoeba-88015 | tokens[13].gloss | ferimento, machucado | injury, wound | tm-lemma | medium |
| sent:tatoeba-192778 | tokens[5].gloss | eu | I | tm-lemma | high (n=229) |
| sent:tatoeba-104736 | particles[1].function | marcador de objeto direto | direct-object marker | tm-particle | high (n=461) |
| sent:tatoeba-3496836 | particles[0].function | partícula de tópico | topic particle | tm-particle | high (n=789) |
| sent:tatoeba-81274 | particles[2].function | partícula de ligação/posse | linking/possession particle | tm-particle | high |
| sent:tatoeba-192727 | particles[0].function | partícula de tópico | topic particle | tm-particle | high |
| sent:tatoeba-188968 | particles[1].function | partícula de destino/direção | destination/direction particle | tm-particle | high |
| sent:tatoeba-80417 | particles[2].function | partícula de citação | quotative particle | tm-particle | high |
| sent:tatoeba-124894 | particles[2].function | partícula conectiva (forma て) | connective particle (て form) | tm-particle | medium (98.6%) |
| sent:tatoeba-109068 | tokens[5].gloss | posição; status; cargo | position; status; standing | jmdict-sense-join (jmdict:1420780 s0) | high |
| sent:tatoeba-11127313 | tokens[2].gloss | evitar; esquivar-se de; fugir de | to avoid; to evade; to keep away from | jmdict-sense-join (jmdict:1583260 s0) | high |
| sent:tatoeba-78986 | tokens[2].role | núcleo do tópico | head of the topic | tm-pos | high (n=38) |
| sent:tatoeba-2325060 | tokens[2].gloss | ação (de empresa) | share; stock | jmdict-sense-element (jmdict:1208920 s0) | medium |

Kana rows look like `kana:katakana-rya` label "Família do RYA" → "RYA family" (template, high).
