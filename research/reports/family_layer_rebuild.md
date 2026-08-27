# Family layer rebuild — proposal

**generated 2026-08-27, proposal for owner sign-off, repo unchanged**

Findings G04, G10 and G16 of the graph review say the family layer is a write-only leaf: 396 families
covering n5/n4 only, 51 stale `kanji_component` families, and `family_related` / `topic.family_ids`
never populated. This report re-measures all of it from today's export, adds one staleness class the
review did not report, quotes what `design/schema_v2.md` §B/§C promised against what shipped, and
proposes a staged rebuild — mechanical first, authored later — with validation attached to each
stage.

Nothing in the repository was changed. Every number below was recomputed from `corpus/**.json` and
`course/**.json`, not from `db/corpus.sqlite`.

---

## 1. What the spec promised and what the data delivered

`design/schema_v2.md` §B, *group (family / cluster) + group_member*:

```
group:  id, type, label_pt, description_pt, importance_rank,
        governing_rule_pt, spans_levels[], primary_module_id,
        + provenance (layer=C)
group_related:  group_id, related_group_id, relation   # contrast_pair | sub_family
group_member:   group_id (FK), member_type (kanji|vocab|grammar), member_id,
                intra_order, is_core (bool), note_pt
```

and §B, *Courseware*:

```
topic:  id, module_id (FK), order, title_pt, theme_pt, family_ids[],
        objectives_pt[], prerequisites[] (topic ids), + provenance(C)
```

| promised | delivered (2026-08-27) |
|---|---|
| `description_pt` | **0 / 396** families carry a description |
| `governing_rule_pt` | 322 / 396 — 74 carry `null`, although `contracts/family.schema.json` lists `governing_rule` under `required` |
| `primary_module_id` | **0 / 396**, and the property does **not exist** in `contracts/family.schema.json` |
| `provenance (layer=C)` | absent from every exported family record |
| `group_related` | **0 rows**, not exported, and **not a property** of `contracts/family.schema.json` |
| `topic.family_ids[]` | **0 / 52** topics, and `family_ids` is **not a property** of `contracts/topic.schema.json` |
| `group_member.note_pt` | present as `note`, populated on 0 members sampled |

The contract files are the sharper evidence. `family_ids`, `primary_module_id` and `related` were not
merely left empty — they were dropped from the published contract, so a consumer reading
`contracts/` cannot even know they were ever specified. `contracts/family.schema.json` exposes
exactly: `description, governing_rule, id, importance_rank, label, members, slug, spans_levels, type`.

§C spells out one `group_related` edge concretely, in the C3 stress test:

```
group_related: {grp:wa-vs-ga, grp:particles-core, relation:"sub_family"}
```

Both endpoints exist in the shipped data — `grp:wa-vs-ga` and `grp:particles-core` are live families
today — and the edge between them was never built. C4 makes the multi-membership promise
("`食べる` is a member of TWO groups — exactly the multi-membership §5.6 wants"), which *does* hold.

Finally, §C's own §1.7 feasibility check answers the component query **without** a family:

> *"All members of the 言-component family across N5–N4 by frequency"* →
> `kanji_component(component=言) JOIN kanji ORDER BY freq_rank`. ✔

That is worth holding onto. The 51 materialized `kanji_component` families are a **cache of a table
the design says to query directly**, and nothing keeps the cache warm. That is G10's root cause,
stated by the spec itself.

---

## 2. Measured state

### 2.1 Shape

| type | families | memberships | member sizes (min/med/max) | member types | spans_levels |
|---|---:|---:|---|---|---|
| `conjugation_class` | 6 | 514 | 1 / 90 / 177 | vocab 514 | `["n5","n4"]` ×6 |
| `particle_set` | 1 | 7 | 7 / 7 / 7 | grammar 7 | `["n5","n4"]` |
| `contrast_pair` | 2 | 4 | 2 / 2 / 2 | grammar 4 | `["n5","n4"]` ×2 |
| `function_set` | 47 | 423 | 1 / 6 / 64 | grammar 364, kanji 49, vocab 10 | `["n5","n4"]` ×47 |
| `kanji_component` | 51 | 496 | 4 / 7 / 48 | kanji 496 | `["n5","n4"]` ×51 |
| `word_family` | 261 | 728 | 2 / 2 / 15 | vocab 728 | `["n5","n4"]` ×261 |
| `semantic_field` | 28 | 400 | 1 / 13 / 36 | vocab 400 | `["n5","n4"]` ×28 |
| **total** | **396** | **2,572** | | | **396 / 396 are `["n5","n4"]`** |

### 2.2 Coverage, now that the records carry `families` back-pointers

The back-pointer G04 asked for exists in today's export. It makes the hole measurable from both ends
for the first time:

| registry | with `families[]` | pre-n5/n5 | n4 | n3 | n2 | n1 |
|---|---:|---|---|---|---|---|
| vocab (7,401) | 1,359 | 705 / 705 | 653 / 653 | **0 / 1,596** | 0 / 1,768 | 1 / 2,679 |
| kanji (2,131) | 250 | 102 / 103 | 140 / 177 | **8 / 350** | 0 / 368 | 0 / 1,133 |
| grammar (496) | 364 | 151 / 151 | 213 / 213 | **0 / 132** | — | — |

n5 and n4 are complete by construction (that was `build_families_full.py`'s acceptance criterion).
n3 is at zero for vocab and grammar. The nine non-zero cells outside n5/n4 — 8 n3 kanji and 1 n1
vocab — are **not coverage, they are leakage**: they are members of families whose own
`spans_levels` says `["n5","n4"]`.

### 2.3 Staleness class 1 — `kanji_component` (G10, confirmed and enlarged)

`kanji.components` is populated on **2,131 / 2,131** kanji and spans 240 distinct components (203 at
taught levels pre-n5..n3). Against that store:

- **0 of 51** families equal the set derived from `kanji.components`.
- **4,868 memberships missing, 0 extra**, over the full registry.
- Restricted to n5/n4 only: **38 of 51 disagree**, 106 missing, 0 extra. (G10 said 35; the small
  difference is the builder's rule that a kanji is not a component of itself — see below. The
  direction and magnitude reproduce.)
- **14 families hold members whose level is outside their own `spans_levels`.**

Worst offenders (`have` = family members, `truth` = kanji whose `components` contain the character):

| component | have | truth | missing |
|---|---:|---:|---:|
| 一 | 48 | 400 | 352 |
| 口 | 33 | 382 | 349 |
| ノ | 28 | 246 | 218 |
| ｜ | 22 | 229 | 207 |
| 日 | 19 | 211 | 192 |
| ハ | 13 | 185 | 172 |

**The root cause is one line.** `scripts/ingest/build_families.py`:

```python
if con.execute("SELECT COUNT(*) FROM family").fetchone()[0] > 0:
    print(f"[skip] families already built (...)")
    return 0
```

The builder is idempotent by *refusing to run*, not by recomputing. It was executed once, before the
n3/n2/n1 registries arrived and before some levels shifted, and it has been a no-op ever since. Note
that its queries are already level-agnostic —
`SELECT ... FROM kanji_component kc JOIN kanji k ON k.id=kc.kanji_id WHERE k.level IS NOT NULL`, with
a `len(members) < 4` cut and a `if comp == ch: continue` self-exclusion — so **a re-run alone would
pick up n3**. The families are not wrongly *designed*; they are wrongly *frozen*.

### 2.4 Staleness class 2 — grammar `function_set` (not reported by the G-series)

The same freeze hit the grammar groupings harder, and no finding names it.

`scripts/ingest/build_families_full.py` builds one `function_set` per introducing topic:

```python
for gid, tid in con.execute("SELECT id,introducing_topic_id FROM grammar_point WHERE introducing_topic_id IS NOT NULL"):
    by_topic_g[tid].append(gid)
...
fid = fam(cur, f"grp:gram-{slug.split(':')[1]}", "function_set", f"Gramática: {title}", rank)
```

That snapshot of `introducing_topic_id` predates the N4/N3 renumbering and the later placement
passes. Measured against the topic whose lesson actually unlocks each point today:

- **272 of 364 grammar `function_set` memberships (74.7%) are in the wrong family.**
- Only **26** grammar `function_set` families exist, for **41** topics that carry grammar.
- Examples: `cha-ikenai-ja-ikenai` sits in `grp:gram-n5-desu-wa` but is unlocked by
  `les:n5-te-form-06`; `dake` sits in `grp:gram-n5-desu-wa` but is unlocked by
  `les:n5-particulas-lugar-08`; `te-iru` and `gp-36` sit in `grp:gram-n5-particulas-lugar` but are
  unlocked by `les:n5-te-form-03` and `-04`; `te-hoshii` sits in `grp:gram-n4-condicionais` but is
  unlocked by `les:n4-dar-receber-03`; `gp-63`, the **passive**, sits in `grp:gram-n4-potencial`.

This is the same failure mode as G10 in a different type, and it is worse in proportion: three
quarters of the memberships are wrong, and unlike `kanji_component` the wrongness is *semantic* — a
learner browsing "Gramática: partículas de lugar" is shown the aspect marker ている.

### 2.5 Not stale — `conjugation_class`

Worth stating plainly, because it changes the plan: the conjugation classes are **exact**.

| family | members | truth (n5+n4) | missing | extra | truth (+n3) |
|---|---:|---:|---:|---:|---:|
| `grp:godan` | 177 | 177 | 0 | 0 | 311 |
| `grp:ichidan` | 90 | 90 | 0 | 0 | 156 |
| `grp:i-adj` | 86 | 86 | 0 | 0 | 105 |
| `grp:na-adj` | 59 | 59 | 0 | 0 | 177 |
| `grp:suru-irregular` | 101 | 100 | 0 | **1 (an n1 vocab)** | 416 |
| `grp:kuru-irregular` | 1 | 1 | 0 | 0 | 1 |

One defect (the n1 member that G10 spotted in the `spans_levels` check) and otherwise correct. These
families are not broken, only under-scoped: `WHERE {col}=? AND level IS NOT NULL` would already pull
n3 on a re-run.

### 2.6 Hardcoded level filters — `word_family`, `semantic_field`

`build_families_full.py` does not derive these level-agnostically; it filters:

```python
for vid, hw, freq in con.execute("SELECT id,headword,freq_rank FROM vocab WHERE level IN ('n5','n4')")
...
con.execute("SELECT id,introducing_topic_id,freq_rank FROM vocab WHERE level IN ('n5','n4') AND ...")
```

So n3's absence from these two types is a literal string in the builder, not a data property.

And `semantic_field` **is not semantic**. It is the residual bucket: vocab that landed in no other
family, grouped by the theme of its introducing topic, labelled `"Campo semântico: {topic title}"`.
Calling it `semantic_field` overstates it by a lot.

---

## 3. Which family types extend to n3, and from what evidence

### Mechanical — Layer-A derivable, zero authoring

| type | Layer-A evidence | now | after rebuild over pre-n5..n3 |
|---|---|---|---|
| `conjugation_class` | `vocab.verb_class` / `vocab.adj_class` (JMdict POS) | 6 fam / 514 mem | 6 fam / **1,166 mem** (+652) |
| `kanji_component` | `kanji.components` (Kradfile), populated 2,131/2,131 | 51 fam / 496 mem | **126 fam / 1,982 mem** at the existing min-4 cut |
| `word_family` | shared leading kanji of `vocab.headword` | 261 fam / 728 mem | **572 fam / 2,024 mem** (+311 fam, +1,296 mem) |
| `particle_set` | `sentence.particles[].function_type`, 14,184 occurrences over 6 classes | 1 fam / 7 mem | **6 fam / 73 particle surfaces** |
| grammar grouping by current topic | `lesson.unlocks[].ref` — the live course | 26 fam / 364 mem, 272 wrong | **41 fam / 496 mem, 0 wrong** |

Sensitivity of the `kanji_component` cut (taught levels only): min 2 → 169 fam / 2,084 mem;
min 3 → 142 / 2,030; **min 4 → 126 / 1,982**; min 5 → 104 / 1,894. Over the whole registry including
n2/n1: 197 fam / 7,955 mem.

`particle_set` today is one hand-picked list of 7
(`wa-topic-marker, ga, o-wo, ni, de, gp-27, mo`). The exporter already publishes a neutral English
`function_type` enum on every particle occurrence: `case` 7,135 (10 distinct surfaces), `binding`
3,002 (4), `conjunctive` 1,854 (16), `sentence-final` 1,171 (17), `adverbial` 580 (24), `nominalizer`
442 (2). Deriving one family per class is mechanical, level-agnostic, and replaces a curated list
with an enum a validator can check.

Caveat on `grp:suru-irregular`: extending it to n3 takes it to **416 members**, mostly noun+する
compounds. A 416-member "family" is an index, not a learner-facing grouping. Either cap it with
`is_core`, split it by the nominal head, or keep it as a class index and exclude it from any
family-browsing UI.

### Authored — Layer C, `needs_review: true`

| type | why it cannot be derived | scope |
|---|---|---|
| `semantic_field` | food / transport / body / time / emotion are meaning judgements, not features of any Layer-A field. The current implementation is a topic residual bucket wearing the name. | n3 has 1,596 vocab; the mechanical `word_family` rule catches 1,105 of them, leaving **491 n3 words** that need a real field. Plus the 2,678 n1 and 1,768 n2 words currently in no family at all, if the bank levels are ever brought in. |
| `contrast_pair` | curated by hand in `CONTRAST_PAIRS`; only 2 survived (`grp:ni-vs-de`, `grp:wa-vs-ga`) because the loop adds a pair only when ≥2 keys resolve exactly | n3's 132 grammar points offer many natural pairs. The duplicate-forms index in the companion merge report is a ready-made candidate generator (`しかない` ×2, `すこしもない` ×2, `ように` ×3, passive vs potential). |
| `function_set` (the real thing) | a communicative function — asking, requesting, comparing, quoting — is a pedagogical grouping independent of topic order | 496 grammar points. Should be a *second* grouping over grammar, not a rename of the topic grouping. |

**Naming recommendation, before anything is rebuilt:** rename the two types that lie about
themselves. The topic-derived grammar grouping becomes `topic_set`; the topic-residual vocab bucket
becomes `topic_residual`. That frees `function_set` and `semantic_field` to mean what they say when
the authored pass arrives, and it stops a future reader from trusting a label the data does not earn.
It is a mechanical rename with no content risk.

---

## 4. How to regenerate `kanji_component` so the staleness class cannot come back

Three options, in increasing order of how much they actually fix.

**(a) Un-freeze the builder.** Delete the `if COUNT(*) > 0: skip` guard and make the derived types a
full recompute keyed on `slug`: rewrite `members` and `spans_levels`, preserve any hand-edited
`label` / `governing_rule` / `importance_rank` by slug. Cheapest, and it turns a one-shot script into
a re-runnable one. Does not stop drift between runs.

**(b) Add the assertion.** A `validate_families.py` registered in `validate_all.py` that fails when a
derived family's member set differs from the store it derives from. Drift then becomes a red gate
instead of silence. This is the load-bearing change — (a) without (b) just re-freezes at a newer
snapshot.

**(c) Stop materializing it.** The spec's own §1.7 feasibility check answers the component query from
`kanji_component` directly, and the export now publishes both `kanji.components` (forward) and
`kanji.families` (back-pointer). A component "family" page can be a view over `kanji.components`
rather than a second copy of it that has to be kept in sync. This removes the class of bug rather
than policing it — at the cost of losing the curated `label` / `governing_rule` on those 51 records
(which are themselves template-generated: *"Kanji que compartilham o componente {comp}"*).

**Recommendation: (a) + (b) now, (c) as an open question for the owner.** The same reasoning applies
to `conjugation_class`, `word_family` and `particle_set`, all of which are pure derivations of a
Layer-A field.

The validator should assert, for every family:

1. derived types — member set **==** the set computed from the source store, at the declared scope;
2. `spans_levels` **⊇** the set of levels of its members (today 14 `kanji_component` families and
   `grp:suru-irregular` violate this);
3. every `members[].ref` / `.slug` resolves to a live record;
4. the record-side back-pointer is the **exact inverse** of `family.members` — 2,572 edges, both
   directions (newly checkable now that `families[]` is exported);
5. no family is empty and none has a single member (today: `conjugation_class` min 1, `function_set`
   min 1, `semantic_field` min 1);
6. `governing_rule` non-null where the contract requires it (74 violations today).

---

## 5. What `family_related` would take

`group_related(group_id, related_group_id, relation)` with `relation ∈ {contrast_pair, sub_family}`
exists today only as columns in `scripts/ingest/migrations/001_init.sql`. Nothing writes it, the
exporter emits no `related` field, and `contracts/family.schema.json` does not declare it. All four
layers must be touched:

1. **ingest** — a writer that populates the table;
2. **export** — `export_corpus.py` emits `related: [{slug, relation}]` on every family, `[]` when
   empty, so the shape is stable from day one;
3. **contract** — the property added to `contracts/family.schema.json` and `contracts/types.ts`;
4. **validator** — both endpoints resolve, `relation` is in the enum, and the declared symmetry rule
   (symmetric for `contrast_pair`, directed for `sub_family`) holds.

Seed set that needs **no authoring**:

- the two `contrast_pair` families → `grp:particles-core` with `sub_family` — this is verbatim the C3
  example, and both endpoints already exist;
- the six `conjugation_class` families → a new parent `grp:conjugation-classes`, `sub_family`;
- each `kanji_component` family → its radical parent where `kanji.kangxi_radical` / `radical_char`
  matches the component.

Everything else is authoring, and it should be done in **one pass with the record-level
`grammar.related[]`**, which is populated on only **4 of 496** grammar records. The same knowledge
answers both — "potential contrasts with passive", "ている contrasts with the relative clause",
"てほしい contrasts with たい" — and splitting it across two passes guarantees they disagree.

**`topic.family_ids`** needs `contracts/topic.schema.json` to gain the property and
`export_course.py` to emit it. The cheapest honest definition is the computed inverse: a topic lists
the families whose members its lessons introduce. That is derivable today from 8,262 lesson unlocks,
it is self-maintaining, and it makes the topic↔family edge of §1.7 exist in both directions without
anyone writing a list by hand.

---

## 6. Staged plan

Mechanical first, authored later. Each stage lands on a green gate and is committed on its own.

### Stage 0 — instrument before changing (~½ day)

Write `scripts/validate/validate_families.py` with the six assertions of §4, register it in
`validate_all.py` as **advisory**. It will report, on today's data: 0/51 `kanji_component` families
exact, 272/364 grammar `function_set` memberships misplaced, 396/396 `spans_levels` = `["n5","n4"]`
with 15 families holding out-of-span members, 74 null `governing_rule`, 2,572 back-pointer edges to
verify. Snapshot that output to `reports/` as the baseline.

*Validation:* the validator runs and its numbers match this report. Nothing else changes.

### Stage 1 — make the builders re-runnable, extend to n3 (~1 day)

Remove the skip guard; split `build_families.py` into a recompute path keyed by slug that preserves
authored fields. Then:

- `conjugation_class` over pre-n5..n3 → 6 families, **1,166 memberships** (from 514); fix
  `spans_levels` to the real member levels; resolve the stray n1 `suru` member.
- `kanji_component` over pre-n5..n3, min 4 → **126 families / 1,982 memberships** (from 51 / 496).
- `word_family` with the level filter widened → **572 families / 2,024 memberships** (from 261 / 728).

Re-export, re-run the gate, then promote `validate_families.py` from advisory to **hard** for these
three types.

*Validation:* assertions 1–5 pass for the three derived types; n3 vocab back-pointer coverage rises
from 0/1,596 to ~1,105/1,596 on `word_family` alone; n3 kanji from 8/350 to ~350/350; no
out-of-`spans_levels` member survives.

### Stage 2 — mechanical particle and topic sets, and `topic.family_ids` (~2–3 days)

- Replace the single 7-member `particle_set` with six derived from
  `sentence.particles[].function_type` (73 distinct surfaces over 14,184 occurrences).
- Rebuild the grammar grouping off the **current** unlocking topic → **41 families / 496
  memberships**, sizes 2 / 10 / 27, repairing all 272 wrong memberships. Rename the type to
  `topic_set`; rename the vocab residual buckets to `topic_residual`. Both renames are mechanical.
- Add `family_ids` to `contracts/topic.schema.json`, emit it from `export_course.py` as the computed
  inverse, populate all 52 topics.

*Validation:* every grammar point belongs to exactly one `topic_set` and that set's topic equals the
topic of the lesson that unlocks it — assert **496/496**; every `topic.family_ids` entry resolves and
no topic is empty — assert **52/52**; every particle surface in the bank belongs to exactly one
`particle_set`.

### Stage 3 — `family_related` plumbing, no authoring (~2 days)

Add the field end to end (ingest → exporter → contract → `types.ts` → validator), populated only with
the mechanically derivable `sub_family` edges of §5. Ship `related: []` everywhere else.

*Validation:* both endpoints of every edge resolve; `relation` in enum; the declared symmetry rule
holds; the C3 example edge (`grp:wa-vs-ga` → `grp:particles-core`) exists — the one concrete promise
the spec made and the data never kept.

### Stage 4 — the authored layer (Layer C, teacher-reviewed, weeks, chunkable)

Only after Stages 0–3, and only after the renames of Stage 2, so nothing authored gets silently mixed
with a residual bucket.

- Real `semantic_field` over the **491 n3 words** the mechanical rules do not catch, then back over
  n5/n4 to replace the residual buckets.
- Authored `contrast_pair` set, seeded from the duplicate-forms collisions and the
  passive-vs-potential / `ように` ×3 cases.
- Authored `function_set` (communicative functions) as a second grouping over the 496 grammar points,
  independent of topic order.
- Authored `family_related` contrast edges **together with** `grammar.related[]` (4/496 today).
- Every record `needs_review: true` per §1.1.

*Validation:* per-level coverage targets (e.g. every n3 vocab in ≥1 `semantic_field`); every authored
family carries a non-null `description` and `governing_rule`; the Stage 0–3 hard assertions still
pass.

### Effort

Stages 0–3 are mechanical and total roughly **one week**: ½ + 1 + 2–3 + 2 days. They take the layer
from 396 families / 2,572 memberships covering n5/n4 to roughly **751 families / ~5,270 memberships**
covering pre-n5 through n3, with 272 wrong grammar memberships repaired, both directions of the
family↔topic edge existing, and drift converted from silence into a red gate.

Stage 4 is the real cost and it is authoring, not engineering. The dominant item is semantic fields
for n3 — 491 words the mechanical rules leave behind, plus whatever replacement is wanted for the 28
residual buckets at n5/n4.

---

## 7. Open questions for the owner

1. **Materialize or view?** Keep `kanji_component` (and the other pure derivations) as family records
   with an equality validator, or delete them and serve the same query from `kanji.components`
   directly, as §1.7's feasibility check already does?
2. **`grp:suru-irregular` at 416 members.** Cap, split, or demote to a non-browsable class index?
3. **Rename `function_set` → `topic_set` and `semantic_field` → `topic_residual`?** Recommended, and
   it must happen before any authored family reuses those names.
4. **Bank levels.** n2 (1,768 vocab, 368 kanji) and n1 (2,679 vocab, 1,133 kanji) are bank-only by
   design. Do they get mechanical families (word_family, kanji_component, conjugation_class extend to
   them for free) or stay outside the layer?
5. **`kanji_component` cut.** Keep min 4 (126 families) or lower to min 2 (169) / raise to min 5
   (104)?
6. **Does `spans_levels` stay?** It is derivable from the members' levels and has been wrong on 15
   families for months. Either derive it and validate it, or drop it as a stored field.
