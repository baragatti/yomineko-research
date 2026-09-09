# W11b — A5 family layer rebuild (stages 0–3)

**Unit:** APP_PLAN §6 step 1, second half. **Source of truth:**
[`family_layer_rebuild.md`](family_layer_rebuild.md) stages 0–3. Stage 4 (authored Layer C) is W39.
**Status: DONE** — stages 0-3 landed on a green gate; the run is in §8.

W11a (homographs) landed first; this unit starts from that post-gate tree.

---

## 0. Stage results

| stage | what it does | result |
|---|---|---|
| 0 | `validate_families.py`, eight checks, nine plants, failing on the old tree | **DONE** — 1,932 problems on the un-rebuilt tree, 277 of them wrong-topic memberships (§1) |
| 1 | builders recompute instead of appending; the layer un-freezes past n5/n4 | **DONE** — 396 → **707** families, 2,568 → **4,969** memberships (§2) |
| 2 | `function_set`→`topic_set`, `semantic_field`→`topic_residual`, redirects | **DONE** — types renamed, slugs unchanged, 52 addresses retired with redirects (§3) |
| 3 | `family.related[]`, `topic.family_ids[]`, Layer-C provenance, D14 | **DONE** — 2 edges including the C3 example, 1,812 topic→family edges, D14 applied (§4) |

Gate: **`RESULT: ALL HARD VALIDATORS PASS`**. No git state touched.

---

## 1. Stage 0 — the validator, and the proof the defect is real

`scripts/validate/validate_families.py` reads the exported `corpus/` + `course/` trees (never
`db/corpus.sqlite`) and asserts five things `validate_graph_edges.py` structurally cannot:

| check | assertion |
|---|---|
| F1 | every member of a topic-derived family (slug ending in a live topic id's suffix) is unlocked by a lesson of **that** topic |
| F2 | every grammar point and every kanji the course unlocks is in **exactly one** topic-derived family, its own |
| F3 | each `conjugation_class` holds exactly the vocab whose JMdict-derived class matches, over the levels `course/manifest.json` declares taught |
| F4 | no empty family, no unresolvable member, no duplicate slug, no member listed twice |
| F5 | `related` present on every family; endpoints resolve; `relation` in enum; `contrast_pair` symmetric, `sub_family` directed and acyclic |

`validate_graph_edges.py` proves a membership *resolves* and that the back-pointer is its inverse —
both of which are true of a membership naming the wrong family. That is why 272 wrong memberships
shipped under a green gate for months.

### 1.1 It FAILS on today's tree (before any rebuild)

Run at the post-W11a state, exit 1, snapshotted to
`research/derived/family_rebuild/validate_families_baseline.txt`:

```
validate_families — the family layer as a derivation
  families                     396
  memberships                  2568
  topic-derived families       74
  unlocked grammar+kanji       1128
  conjugation-eligible vocab   1167
  family_related edges         0
FAIL 1397 problem(s)
  [F1] 277   grp:gram-n5-desu-wa: grammar gram:cha-ikenai-ja-ikenai is taught under top:n5-te-form, not top:n5-desu-wa
             grp:gram-n5-desu-wa: grammar gram:dake is taught under top:n5-particulas-lugar, not top:n5-desu-wa
             ... and 275 more
  [F2] 718   grammar gram:n3-ageru (taught under top:n3-estado) is in no topic-derived family
             ... and 717 more
  [F3] 6     grp:godan: 134 eligible vocab not in the class; grp:suru-irregular: 316 missing, 1 extra; ...
  [F5] 396   every family: no `related` property
```

277 F1 failures against the report's 272: the report counted grammar memberships only, the
validator also counts the kanji members of the `grp:kanji-topic-*` buckets and the vocab members of
`grp:theme-*`, which the rebuild report never measured. The wrong-topic grammar count reproduces
independently at 272 (§1.2).


### 1.2 The 272, reproduced independently

Counting only grammar members of the topic-keyed `function_set` families, against the topic whose
lesson unlocks each point today:

| family type | member type | wrong-topic memberships |
|---|---|---:|
| `function_set` (`grp:gram-*`) | grammar | **272** |
| `function_set` (`grp:kanji-topic-*`) | kanji | 5 |
| | **total F1** | **277** |

That is the report's number, measured from a different direction (the exported course rather than
the index). The defect is real and it is the one the owner ruled certain.

The validator with all eight checks, run on the same un-rebuilt tree, is snapshotted to
`research/derived/family_rebuild/validate_families_before_rebuild.txt`: **1,932 problems** —
F1 277, F2 718, F3 6, F5 396, **F6 483** (word families the headwords derive and no family holds),
**F7 52** (no topic carries `family_ids` at all).

---

## 2. Stage 1 — the builders recompute

`scripts/familylib.py` is the new shared spine: `recompute()` (rewrite in place, both locales),
`retire()` / `retire_unbuilt()` (a published slug is redirected, never deleted), `taught_levels()`
(read from `course_module`, never a literal), and `unlock_topic_map()` — the live unlock ledger,
dereferenced through `export_course._deref` so a family and a lesson cannot disagree about which
record a ref names.

| | before | after | expected (rebuild report) |
|---|---:|---:|---|
| families (live) | 396 | **707** | ~751 |
| memberships | 2,568 | **4,969** | ~5,270 |
| retired addresses | 0 | **52** | — |
| `conjugation_class` memberships | 514 | **1,167** | 1,166 |
| grammar `topic_set` families | 26 | **41** | 41 |
| grammar `topic_set` memberships | 363 | **494** | 496 |
| kanji `topic_set` families | 20 | **40** | — |
| kanji `topic_set` memberships | 49 | **634** | — |
| `word_family` | 261 / 725 | **574 / 2,027** | 572 / 2,024 |
| `function_set` (`grp:counters`) | 1 / 10 | **1 / 16** | — |
| `topic_residual` | 28 / 400 | **42 / 620** | — |
| `kanji_component` | 51 / 496 | **0 / 0** (D14) | 126 / 1,982 |
| `family_related` edges | 0 | **2** | — |
| `topic.family_ids` edges | 0 | **1,812** | — |

### 2.1 Every deviation from the report's numbers, with its cause

| item | report | measured | why |
|---|---:|---:|---|
| conjugation memberships | 1,166 | 1,167 | the report counted distinct vocab; ten records carry both a `verb_class` and an `adj_class`, so 1,157 records produce 1,167 memberships. The validator's F3 counts memberships and agrees. |
| grammar `topic_set` memberships | 496 | 494 | W08 (decision A3) merged two duplicate-identity grammar points away — `gram:gp` and `gram:gp-152`. 496 is the registry row count; 494 is the live set, and a merged-away record must not be a family member. |
| `word_family` | 572 / 2,024 | 574 / 2,027 | measured before W09's vocab re-point and W11a's homograph work moved eight records onto the JMdict entry their list slot names; three of them now start with a kanji that has a family. |
| `kanji_component` | 126 / 1,982 | dropped | owner decision **D14**. Not a deviation in measurement — a decision not to rebuild the cache. Measured for the record: at the taught levels the cut would have been min 2 → 155 families, min 3 → 133, **min 4 → 117**, min 5 → 97; the report's 126 predates the N3 level reassignments. |
| total families | ~751 | 707 | 751 assumed the 126 rebuilt component families. 707 = 751 − 126 + 40 kanji `topic_set` families (which the report never counted, because under the old builder they only held the kanji no component family had claimed) + rounding on the residual buckets. |
| `particle_set` derived from `function_type` | 6 families / 73 surfaces | **not done** | out of the stage list this unit was given, and it conflicts with stage 3: replacing the curated `grp:particles-core` with six enum-derived sets removes the endpoint of the one edge `design/schema_v2.md` §C names by hand (`grp:wa-vs-ga` → `grp:particles-core`). Deferred with its reason rather than done half-way. |


### 2.2 What the shape looks like now

| type | families | memberships |
|---|---:|---:|
| `conjugation_class` | 6 | 1,167 |
| `topic_set` | 81 | 1,128 |
| `topic_residual` | 42 | 620 |
| `word_family` | 574 | 2,027 |
| `function_set` (`grp:counters`) | 1 | 16 |
| `particle_set` | 1 | 7 |
| `contrast_pair` | 2 | 4 |
| **live total** | **707** | **4,969** |
| retired (`corpus/families_deprecated.json`) | 52 | — |

`spans_levels` was `["n5","n4"]` on **396 of 396** families before; it is now derived and spread over
**10** distinct spans (this said 16, which was wrong — corrected in W11c, and the DB agrees with the
export on all ten since `fix_contrasts.py` started going through `recompute()`):

| span | families | | span | families |
|---|---:|---|---|---:|
| `["n3"]` | 159 | | `["n4"]` | 57 |
| `["n4","n3"]` | 157 | | `["n5","n4"]` | 36 |
| `["n5","n3"]` | 117 | | `["n3","n2"]` | 3 |
| `["n5","n4","n3"]` | 102 | | `["n5","n1"]` | 1 |
| `["n5"]` | 74 | | `["n3","n1"]` | 1 |
Coverage: **every** live grammar point (494/494) and every unlocked kanji (634) and unlocked
vocabulary item (2,951) is in at least one family, and in exactly one topic-derived family.

### 2.3 Five members whose record level sits outside the taught set

Not a family defect — the family is right, the level tag is the question. The course unlocks these
five and the topic family therefore holds them:

| member | level | family (topic) |
|---|---|---|
| `vocab:1385390` | n1 | `grp:theme-n5-conectando` |
| `kanji:案` | n1 | `grp:kanji-topic-n3-conectores` |
| `kanji:沈` | n2 | `grp:kanji-topic-n3-conjectura` |
| `kanji:禁` | n2 | `grp:kanji-topic-n3-desejos` |
| `kanji:城` | n2 | `grp:kanji-topic-n3-estrutura` |

Before the rebuild the same class of leak existed and was invisible, because `spans_levels` was
frozen at `["n5","n4"]` for everyone. It is now visible in the export: those families declare a span
that includes n1/n2 because their members do. Whether the level tag or the placement is wrong is a
level-consensus question (spec §1.5), not a family one, and it is left for the owner rather than
quietly repaired here.

---

## 3. Stage 2 — the two names that lied

`function_set` → `topic_set` and `semantic_field` → `topic_residual`, applied **before** anything
links the slugs, exactly as the rebuild report asks.

The slugs did **not** change. `grp:gram-*`, `grp:theme-*` and `grp:kanji-topic-*` are published
addresses in the `grp` namespace, and nothing about the rename makes them wrong — what was wrong was
the type claiming these buckets were communicative-function sets and semantic fields. So the rename
is a type change plus, for the residual buckets, a label change: `"Campo semântico: {tópico}"` became
`"Vocabulário do tópico: {tópico}"`, because a label that says *semantic field* is the same lie one
level down. **No `deprecated_by` redirect was needed for the rename** — the addresses survived it.

Both original names stay in `contracts/family.schema.json`'s enum, instantiated by nothing today, and
`scripts/ingest/migrations/001_init.sql` (the vocabulary owner `build_schemas.py` cites) now says why:
they are reserved for the AUTHORED families of W39. `grp:counters` stays a `function_set` and is the
only member of that type — it is a real functional grouping derived from `vocab.lexeme_type`, with a
real governing rule, and it never claimed to be something else.

### 3.1 Redirects that WERE needed

`corpus/families_deprecated.json`, 52 rows, exported on every run like
`corpus/grammar_deprecated.json`, and registered in `design/generated_artifacts.json`:

| retired | count | redirects to | why |
|---|---:|---|---|
| `grp:kanji-comp-*` | 51 | `kanji.components` | owner decision **D14** |
| `grp:theme-n5-adjetivos` | 1 | `topic.family_ids` | the topic's vocabulary is now entirely claimed by a word family or a conjugation class, so it leaves no residue and the bucket stops existing |

A redirect target is either a surviving `grp:` slug or an exported **field path**, because a retired
family does not always have another family as its successor — D14's answer is a *query*, not a group.
The validator enumerates the legal field paths rather than pattern-matching, so "any string with a
dot in it" can never pass as a redirect.

---

## 4. Stage 3 — the edges, the provenance, and D14

**`family.related[]`** is exported on every family, `[]` where there are none, so the shape is stable
for consumers from the first export rather than appearing the day the first edge lands. Two seed
edges, both mechanical:

```
grp:wa-vs-ga  --sub_family-->  grp:particles-core
grp:ni-vs-de  --sub_family-->  grp:particles-core
```

The first is `design/schema_v2.md` §C's C3 example **verbatim** — the one concrete edge the spec
names, with both endpoints live in the shipped data for months, and which the data had never carried.

The conjugation-class parent the rebuild report also sketches (`grp:conjugation-classes` with six
`sub_family` children) was **not** built. It requires publishing a family with no members of its own,
which `validate_families` F4, `validate_graph_edges` and the prototype all read as a defect, and
inventing a record to exercise a field is a worse trade than shipping the field with two honest
edges. Everything beyond these two is authoring and belongs in one pass with `grammar.related[]`
(4 of 494 populated today) — W39.

**`topic.family_ids[]`** now exists on all 52 topics, 1,812 edges, and is the **computed inverse**
(`lesson.unlocks[]` × `family.members[]`), recomputed on every export. It is deliberately *not* read
from the `topic.family_ids` column that has sat in the index since `006_courseware.sql`: a stored
list is the exact shape that broke this layer once already. F7 asserts the published list equals a
recomputation done from the two published sides alone, so no future change can quietly store a
snapshot of it.

**Layer-C provenance** — `source`, `created_by`, `layer` — is exported on every family beside the
`needs_review` W05 added. Without them a reader could not tell that these labels are template text a
builder owns (`derived` / `ai` / `C`) rather than something a teacher wrote, which is the distinction
spec §1.1 exists to make and the reason the whole layer carries `needs_review`.

**D14** is applied: the 51 materialized `kanji_component` families are gone and the component query
is answered from `kanji.components`, which is populated on 2,131 / 2,131 kanji and exported already.
`validate_graph_edges.py` records `kanji.components[]` as "excluded by design (Kradfile radicals are
not registry records)", which is the same reading.

### 4.1 `governing_rule` is no longer nullable

74 of 396 families carried `null` while the contract listed the property as required. All 707 now
carry one in both locales, so `contracts/family.schema.json` regenerated from `LocaleText | null` to
`LocaleText` — the contract tightened by itself because the data stopped violating it. The three new
template rules say what the grouping IS ("os pontos de gramática que este tópico apresenta, na ordem
em que as lições os introduzem"), never what a teacher would say about it; the pedagogy is W39's.


---

## 5. Three things this unit had to fix that were not on the list

**5.1 The rebuild order was wrong the moment the derivation changed.** The family builders sat at
manifest steps 37-39, and `lesson_unlocks` is not populated until `replay_all.py` (step 37 in the new
numbering) runs `load_lessons.py`, after which steps 90, 110, 111 and 112 correct it. Deriving the
topic families from the live ledger therefore made three steps depend on a table that does not exist
when they run: a from-scratch replay would have built every topic-bound family from an empty ledger
and produced a family layer that cannot reproduce the committed export. The three steps moved to the
end of the manifest (113-115, renumbered to **114-116** when W11c inserted
`apply_lesson_ref_addresses.py` at 112) and every step-number reference inside the other notes was
renumbered with them. `fix_derived.py` stayed where it is; its contrast links are re-derived by
`fix_contrasts.py` at the end anyway.

**5.2 `en` was never a registered locale, and 30,000+ rows were violating the foreign key.**
`004_i18n.sql` declares `localized_text.locale REFERENCES locale(code)` and seeds exactly one row,
`pt-BR`. Every `en` row ever written violates that constraint; nothing noticed because the writers
ran without `PRAGMA foreign_keys = ON`. The new family builder runs with enforcement on, and its
first `set_text(..., locale="en")` failed with `FOREIGN KEY constraint failed` while 322 identical
rows already sat in the table. `012_locale_en.sql` registers it. This is a declaration catching up
with the data: no column, no value and no exported byte changes.

**5.3 Template text in a builder had drifted from the export it produces.** `build_families.py`'s
`grp:kuru-irregular` rule carried an em dash, which `clean_emdash.py` had been silently repairing in
the index on every replay; a recompute reintroduced it and `integrity_audit.py` caught it. Four other
strings (the i-adj and na-adj en rules, the counters en rule) had drifted from the committed export
in wording. All five are now byte-identical to what ships, so a rebuild reproduces the export instead
of asking a cleanup pass to reproduce it afterwards. Worth stating plainly: a builder that only ever
ran once cannot be caught drifting from its own output, and four of these five had been wrong since
the day the export was first generated.

---

## 6. Falsifiability

`scripts/validate/validate_families.py` is plant-proved on a **copied tree that carries a copy of the
validator itself**, so a plant cannot be read around by resolving `ROOT` back to the real repository.
The pristine copy is run first and must PASS, or no plant means anything. **Nine plants, nine
caught**; the run is pasted into the validator's docstring and summarised in
`scripts/validate/README.md`:

| plant | check | caught |
|---|---|---|
| one grammar membership moved into another topic's family | F1 | yes |
| `families.json` emptied to `[]` | F2 (1,128 failures) | yes |
| one word dropped from a `word_family` | F6 | yes |
| one topic's `family_ids` emptied | F7 | yes |
| one `conjugation_class` member removed | F3 | yes |
| a live family also listed as retired | F8 | yes |
| a `related` edge pointing at a family that does not exist | F5 | yes |
| a member ref that resolves to no record | F4 | yes |
| a topic-derived family whose suffix names no live topic | F4 | yes |

The validator is **hard** in `validate_all.py` — it landed advisory on the un-rebuilt tree and was
promoted at the end of stage 3, which is what the plan asked for.

One assertion the rebuild report drafted was deliberately **not** implemented: "no family has a
single member". `grp:kuru-irregular` has exactly one because 来る is the only kuru-irregular verb in
the language, and `grp:kanji-topic-n4-keigo` has one because that topic introduces one kanji. That
assertion would fail on a correct derivation. EMPTY fails; one is fine, and the docstring says so.

---

## 7. Lessons did not degrade — the rendered proof

A byte diff of lesson JSON is not enough (W09 shipped six wrong glosses past one), so the course
delta was measured by re-exporting the whole tree **twice**: once with the `family_ids` emission
disabled, once with it on, then diffing the two exports.

```
files that differ:  52 x  <level>/topic-NN-*/topic.json
lines removed:      0
lines added:        only "family_ids": [ ... ] arrays of grp: slugs
```

**Zero lesson files, zero deletions, zero other fields.** Independently: `validate_md_views.py`
re-renders all **322 lesson `.md` byte-identically**, and the only five rendered lessons that differ
from `HEAD` are W11a's, matching its five modified authoring sources under
`research/derived/lessons/`. The family layer is referenced by ID and embedded nowhere, which is the
two-layer separation CLAUDE.md requires, and this is what proves it held.

---

## 8. Idempotence, and the chain that was run

Chain, in order: `init_db.py` (applies 011 and the new 012), `build_families.py`,
`build_families_full.py`, `fix_contrasts.py`, `export_corpus.py`, `export_course.py`,
`infer_shapes.py`, `build_schemas.py`, `build_manifest.py`, `npm run sync-data`,
`validate_all.py`.

**`RESULT: ALL HARD VALIDATORS PASS`** — `validate_families.py` reports `OK every check passed`.

Running the builders and both exporters a **second** time reproduces `corpus/families/families.json`,
`corpus/families_deprecated.json` and the topic files byte for byte. That is the property the old
guard only pretended to have: it was idempotent by refusing to run, which is how a derivation stops
tracking its source in silence.

### 8.1 One baseline was re-recorded, and exactly why

`validate_index_rebuildable.py --quick` failed on `corpus/grammar/INDEX.md`. The cause is the export
date, not the data: the file's only volatile line is `_Generated <date>`, W11a re-ran only
`export_course.py`, and this unit's `export_corpus.py` run moved it from 2026-09-03 to 2026-09-09.
Proved rather than assumed — taking the newly rebuilt file and substituting the old date back
reproduces the recorded hash exactly:

```
sha256(rebuilt file with 2026-09-03) = 004abefda140b46215291c4f83a8589065d0e64ccfe144ed2847d934b41d5f4b
recorded baseline                    = 004abefda140b46215291c4f83a8589065d0e64ccfe144ed2847d934b41d5f4b
```

so `--quick --record` was run. The baseline did not grow: 4 entries before, 4 after, one hash
changed, no entry added. The **full** mode was not re-recorded and is not in the suite.

**W11c did run it, and it did not run.** The full mode had been aborting at
`scripts/migrate_grammar_merge.py` — reproducible under HEAD's manifest too, so not a W11b
regression, but W11b moved the three family builders from 37-39 (where a full replay DID reach
them) to the end (where it never got), and this section should have said so. W11c fixed the abort,
re-recorded the full baseline (650 of 787 -> 643 of 790; byte-identical 137 -> 147) and wrote down
what replays these steps: the FULL mode only. `--quick` reconstructs the grammar family alone and
its scratch index has no lessons and no vocabulary, so the three builders complete there with 7
families and 0 memberships — measured, not assumed. See `w11_fixup_report.md` §5.

---

## 9. What a reader should push back on

**1. `topic_residual` is honest, and it is still a bucket.** 42 families and 620 words grouped by
"the topic that introduced them, once nothing else claimed them". Renaming it stopped the lie; it did
not make the grouping pedagogically useful. Q1 of spec §1.7 — *a godan verb from the daily-routine
family* — still returns 0 rows and is still waived, and the waiver's reason is unchanged after a full
rebuild: a residual bucket cannot contain a verb, because every verb is already in a conjugation
class. That waiver dies when W39 authors a real semantic field, and not before. The rebuild did not
fix Q1 and this report does not claim it did.

**2. Two derived types are asserted by equality; three are not.** F3 and F6 recompute
`conjugation_class` and `word_family` from the Layer-A field and compare sets, so those two cannot
drift. `topic_set` and `topic_residual` are asserted through F1/F2 (right topic, complete coverage),
which is equivalent for `topic_set` but weaker for `topic_residual`: F1 proves every member belongs
to that topic, and nothing proves a word that *should* have fallen through to the bucket is in it.
Closing that means restating the "in no other family" rule inside the validator, which duplicates the
builder's logic — a trade worth an explicit decision rather than a silent one.

**3. `grp:suru-irregular` is now 416 members.** The rebuild report flagged this and the owner has not
answered (its question 2). A 416-member "family" is a class index, not a learner-facing grouping, and
it now ships as one. Nothing here caps, splits or demotes it: that is a pedagogical call, and
guessing it inside a mechanical rebuild is how this layer acquired its first set of lies.

**4. The `spans_levels` question is still open.** It is derived at export, and **10** distinct spans
now ship where 396 families once all claimed `["n5","n4"]` (this section said 16; corrected in W11c).
The rebuild report asked whether the stored column should exist at all (its question 6). It still
does, and deleting it is a schema change nobody has authorised. Two claims here were wrong and are
corrected in `w11_fixup_report.md` §1: it was NOT "validated only indirectly" any more than it had
to be — `validate_families.py` F9 now asserts the published span EQUALS its members' levels and that
`db/corpus.sqlite` agrees; and it was NOT "written by `recompute()` only", because
`fix_contrasts.py` wrote it outside `recompute()` and left three families saying `["n5","n4"]` in
the index while the export published `["n5"]`. That builder goes through `recompute()` now.

**5. The five out-of-scope members of §2.3 were left alone.** Four kanji and one word that the course
teaches carry an n1/n2 level tag. The family layer now makes that visible instead of hiding it behind
a frozen `spans_levels`. Whether the tag or the placement is wrong is a §1.5 level-consensus
question, and repairing it inside a family rebuild would be exactly the kind of drive-by the plan
warns against.

---

## 10. Artifacts

| path | what |
|---|---|
| `scripts/familylib.py` | **new.** `recompute` / `retire` / `retire_unbuilt` / `taught_levels` / `member_levels` / `unlock_topic_map` / `unlock_order` — the shared spine, and the one place the unlock ledger is dereferenced (through `export_course._deref`, so the family layer and the course cannot disagree about which record a ref names) |
| `scripts/ingest/build_families.py` | recomputes the six classes + counters over the taught levels; retires the 51 component caches (D14) |
| `scripts/ingest/build_families_full.py` | recomputes `topic_set` / `word_family` / `topic_residual` from the live ledger; the type rename lands here |
| `scripts/ingest/fix_contrasts.py` | plus the `family_related` seed (recomputed; both endpoints must be live families) |
| `scripts/ingest/migrations/011_family_deprecation.sql` | `family.deprecated_by`; already applied and recorded, idempotent through `init_db.py`'s duplicate-column handling; registered by manifest step 1, which globs `migrations/*.sql`. `family.needs_review` was already present from `001_init.sql` and needed no migration |
| `scripts/ingest/migrations/012_locale_en.sql` | **new.** registers `en` in the `locale` table (§5.2) |
| `scripts/ingest/migrations/001_init.sql` | comment only: `family.type` gains `topic_set` / `topic_residual` with the reason, and `family_related.relation` gains its symmetry and direction rule. This file is the vocabulary owner `build_schemas.py` cites |
| `scripts/export/export_corpus.py` | `related[]`, `source`/`created_by`/`layer`, retired families excluded from the registry **and** from the back-pointers, `corpus/families_deprecated.json` |
| `scripts/export/export_course.py` | `_topic_family_ids()` and `family_ids` on every `topic.json` |
| `scripts/contracts/build_schemas.py` | the two new `family.type` values, the `related[].relation` vocabulary, `StableId` on `topic.family_ids[]` and `family.related[].slug` |
| `scripts/validate/validate_families.py` | F1-F8, hard in the suite, nine plants |
| `scripts/validate/graph_queries.py` | Q1 resolves the "daily-routine family" over `semantic_field` **or** `topic_residual`, so the rename cannot turn a documented waiver into "the family does not exist"; the waiver text now names what actually fixes it (W39) |
| `scripts/validate/validate_all.py`, `scripts/validate/README.md` | `validate_families.py` advisory to **code**, with the eight checks written out |
| `scripts/validate/rebuild_baseline.json` | one quick-mode hash re-recorded (§8.1) |
| `research/derived/rebuild_manifest.json` | the three family steps moved to the end with their reasons (113-115, then 115-117 after W11c inserted step 112, and 117-119 after W21 inserted 115-116); cross-references renumbered |
| `design/schema_v2.md` | §B records what shipped against what the section promised, including the two fields still deliberately empty |
| `design/generated_artifacts.json` | `corpus/families_deprecated.json` registered |
| `corpus/families/families.json`, `corpus/families_deprecated.json`, `corpus/families/INDEX.md`, the registries' `families[]` back-pointers, 52 `topic.json` | the export |
| `research/derived/family_rebuild/validate_families_baseline.txt` | the stage-0 validator on the un-rebuilt tree (1,397 problems) |
| `research/derived/family_rebuild/validate_families_before_rebuild.txt` | the final eight-check validator on the un-rebuilt tree (1,932 problems) — the proof the defect was real |

**Status: DONE.** Stages 0-3 landed, gate green, no git state touched. Stage 4 (authored
`semantic_field`, authored `contrast_pair`, authored communicative `function_set`, and authored
`family_related` contrast edges together with `grammar.related[]`) is W39.
