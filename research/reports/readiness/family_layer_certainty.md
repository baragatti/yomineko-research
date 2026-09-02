# Family layer — certainty check for owner decision A5

**Written 2026-09-02. Read-only audit: nothing in the repository was changed, no exporter was run.**

Owner ruling on `research/reports/PENDING.md` A5 (2026-09-01) was:

> A5 → only if 100% certain it is a defect — verify first, then fix.

A5's evidence line makes two claims. This report re-derives both **independently of
`family_layer_rebuild.md`** — from `corpus/families/families.json` and the `course/` unlock graph,
not from the earlier report's numbers or its scripts — and then asks whether the defect actually
reaches a learner.

| A5 claim | verdict |
|---|---|
| "74.7% of grammar `function_set` memberships name the WRONG topic (stale snapshot)" | **CONFIRMED, exactly.** Independently re-derived: **272 / 364 = 74.73%** |
| "`family_ids`/`related` were silently dropped from the published contracts" | **CONFIRMED as to effect, imprecise as to mechanism.** Neither field was ever built, so the data-derived contract never declared them. Nothing was deleted. |

**VERDICT: DEFECT CERTAIN** — with one material qualification the owner should hear before
sequencing it: *no shipped surface reads these memberships today*, so this is a latent data defect,
not a live learner-facing one. Detail in §3.4.

---

## 1. What this capability needs from the data

A "family" is the app's *lateral* index — the answer to "what else behaves like this?" Both product
paths need it:

* **JLPT path** — a browse/filter surface ("all godan verbs", "all kanji sharing 言", "all the
  grammar this topic teaches"), and the grouping an SRS leech-handler uses to say *why* two cards
  keep colliding.
* **Speak-fast path** — communicative function sets ("how to ask", "how to request") are the whole
  organizing principle of a speaking syllabus; they cannot be topic order in disguise.

Concretely the layer must supply:

| need | entity / field | contract | validator |
|---|---|---|---|
| a group with a stable address | `family.slug`, `family.type` | `contracts/family.schema.json` | `validate_graph_edges.py` |
| its members, resolvable and ordered | `family.members[].{member_type,slug,ref,intra_order,is_core}` | same | `validate_graph_edges.py` |
| the reverse edge, so a record page can show its groups | `kanji/vocab/grammar.families[]` | the three registry schemas | `validate_graph_edges.py` (bijection) |
| the rule that makes the group a *teachable* group | `family.governing_rule`, `family.description` | declared | none |
| group→group edges (contrast pair, sub-family) | `family.related[]` (spec `group_related`) | **absent** | none |
| topic→family, so a lesson can link its groups | `topic.family_ids[]` | **absent** | none |
| Layer-C provenance, so a teacher can queue it | `layer`, `source`, `created_by`, `needs_review` | **absent from the export** | none (see §4.3) |
| **the invariant that a topic-derived group names the topic that actually teaches its members** | — | — | **none — this is the defect** |

---

## 2. What exists today (verified)

All counts below were recomputed from the committed export. Method is stated so the numbers are
falsifiable; `db/corpus.sqlite` was read only to cross-check, never as the source of truth.

### 2.1 The layer as shipped

`corpus/families/families.json` — **396 families, 2,572 memberships**:

| type | families | memberships (by member type) |
|---|---:|---|
| `conjugation_class` | 6 | vocab 514 |
| `particle_set` | 1 | grammar 7 |
| `contrast_pair` | 2 | grammar 4 |
| `function_set` | 47 | grammar 364, kanji 49, vocab 10 |
| `kanji_component` | 51 | kanji 496 |
| `word_family` | 261 | vocab 728 |
| `semantic_field` | 28 | vocab 400 |
| **total** | **396** | **2,572** |

The 47 `function_set` families are three different things wearing one type name:

* **26** `grp:gram-<topic>` — one per topic that teaches grammar, label `"Gramática: {topic title}"`, **364 grammar members**
* **20** `grp:kanji-topic-<topic>` — kanji stragglers, label `"Kanji do tópico: {topic title}"`, **49 kanji members**
* **1** `grp:counters` — the only hand-curated one, 10 vocab

### 2.2 The course side (the ground truth I measured against)

52 `topic.json` files (`pre-n5` 6, `n5` 14, `n4` 17, `n3` 15), 322 lesson leaves.

* **4,137** distinct unlock refs — vocab 2,946, kanji 634, **grammar 496**, kana-family 57, feature 4.
* **Every grammar point is unlocked by exactly one lesson.** Refs unlocked by more than one lesson: **0**.
  There is therefore no ambiguity about "the topic that introduces this point" — the mapping is total
  and single-valued, and `validate_unlock_ledger.py` is the gate that keeps it that way.
* The 322 standalone `lesson-*.json` leaves and the lesson objects embedded in `topic.json`
  **agree on unlocks in 322 / 322 cases** — so it does not matter which one you read.

### 2.3 What guards the family layer today

`scripts/validate/validate_graph_edges.py::check_family_graph` (registered HARD in
`scripts/validate/validate_all.py`) asserts three things and only three:

1. every `members[].ref` / `.slug` resolves to a live kanji / vocab / grammar record;
2. the `families[]` back-pointer on the record is the **exact inverse** of `family.members`;
3. `spans_levels` ⊇ the levels of the members (and the exporter now *derives* `spans_levels`,
   `scripts/export/export_corpus.py:445`, so it cannot go stale).

I re-ran check (2) by hand: **0 of 496 grammar records** disagree with `families.json`.

That is the reason this defect survives a green gate. **The wrong data is perfectly self-consistent.**
Every membership resolves, every back-pointer matches, every level is covered. Nothing in the
42-entry validator registry compares a family against the topic it is named after — I grepped every
file under `scripts/validate/` for a join between family membership and `introducing_topic` /
`unlocks` and found none.

---

## 3. The measurement

### 3.1 Method

1. Load all 52 `course/*/topic-*/topic.json`; for every lesson, every `unlocks[]` entry of
   `type: "grammar"`, record `(topic_order, lesson_order, topic_id, lesson_id)`.
   Since no ref is unlocked twice (§2.2), this map is exact, not a "first wins" heuristic.
2. Load `corpus/families/families.json`; take every family whose slug starts `grp:gram-`.
   The slug encodes its topic: `grp:gram-<X>` ⇒ `top:<X>`. **All 26 resolve to a live topic**, and
   **25 of 26 labels are the literal string `"Gramática: " + topic.title["pt-BR"]`** — so the
   slug→topic reading is the builder's own, not my inference. (The 26th is discussed in §3.5; it is
   itself evidence.)
3. For each grammar membership, compare the family's topic against the topic that unlocks the point.

### 3.2 Result

```
grammar memberships in grp:gram-* families ........ 364
memberships whose family topic != introducing topic  272
rate ............................................. 74.73%
```

**272 / 364 = 74.73%.** The A5 headline reproduces to the second decimal from an independent
derivation.

Robustness checks:

* **Every one of the 26 families is affected.** None is 0% wrong. Two are 100% wrong:
  `grp:gram-n4-forma-simples` (10/10) and `grp:gram-n4-keigo` (9/9).
* Excluding the two grammar points that decision **A3** proposes to merge away
  (`gram:gp`, `gram:gp-152`): **271 / 362 = 74.86%** — the number does not depend on A3.
* **0 of the 272 cross a JLPT level boundary.** Every misplacement stays inside its own level
  (n5→n5: 111, n4→n4: 161). Level integrity and lesson gating are *not* touched by this defect.

### 3.3 What the correct layer looks like, derived today

Re-running the builder's own rule against today's data:

| | shipped | correct today | delta |
|---|---:|---:|---:|
| `grp:gram-*` families | 26 | **41** | 15 never created |
| grammar memberships | 364 | **496** | 404 missing, 272 extra |
| families that differ at all | — | — | **41 / 41** |

The 132 grammar points in no `grp:gram-*` family at all are **all n3** — the builder's grammar loop
is level-agnostic, but it has not been run since n3 arrived.

**The decisive cross-check.** `db/corpus.sqlite`'s `grammar_point.introducing_topic_id` — the exact
column `scripts/ingest/build_families_full.py:56` reads — agrees with the course unlocks on
**496 / 496 rows, zero disagreements**. So the source the builder queries is *correct today*. The
families are not a disagreement about what "introduces" means, and not a bug in the query. They are a
**frozen snapshot**. Re-deriving from the same column right now yields the right answer.

### 3.4 Does the defect reach anyone? (impact check)

I traced every consumer. This is where the honest qualification lives.

| consumer | reads family memberships? |
|---|---|
| `prototype/app/**` (26 routes) | **No.** The only `families` reference in the whole app source is `prototype/app/lib/corpus.server.ts:103`, the **kana** syllabary chart — a different file (`corpus/kana/families.json`). No route renders `family` or the `families[]` back-pointer. |
| `course/**` lessons and exercises | **No.** No lesson body, exercise, or `srs.introduces_cards` entry references a `grp:` slug. Only `corpus/**` files contain `grp:` strings. |
| `scripts/validate/validate_graph_edges.py` | Yes — structurally only (§2.3). Passes on the wrong data. |
| `scripts/validate/graph_queries.py` | Yes — the spec §1.7 acceptance queries. Q1 joins `grp:godan` × a `semantic_field`; Q3 joins a `kanji_component` family. **Neither touches a `grp:gram-*` family**, so the §1.7 gate is blind to this. |
| `scripts/export/review_queue.py` | Reads `family.needs_review` **from the DB**, not the export. |
| `scripts/contracts/infer_shapes.py` | Shape inference only. |

So: **the corrupt memberships are published in the source-of-truth artifact and in
`prototype/app/data/grammar.json`, but nothing renders them.** Blast radius today is zero; blast
radius the day someone builds the "related grammar" or "browse by topic" surface — which both
product paths need — is three quarters of that surface.

That is exactly why this is worth fixing *now* rather than later: it is free to fix while nothing
depends on it, and it is a silent trap for whoever builds on it next.

### 3.5 Root cause, verified in the builder

`scripts/ingest/build_families_full.py` is **append-only**, in two independent ways:

```python
def fam(cur, slug, ftype, label, rank, rule=None, desc=None):
    row = cur.execute("SELECT id FROM family WHERE slug=?", (slug,)).fetchone()
    if row:
        return row[0]                      # existing slug -> label/rank/spans_levels FROZEN
    ...
def add_members(cur, fid, members):
        cur.execute("INSERT OR IGNORE INTO family_member (...)")   # never DELETEs
```

**Two consequences the A5 plan must account for:**

1. A plain re-run **cannot fix this.** `INSERT OR IGNORE` would add the 404 missing memberships and
   leave all 272 wrong ones in place — every relocated point would then sit in *two* families, and
   `check_family_graph`'s back-pointer bijection would still pass. The rebuild must **delete** the
   derived memberships before re-deriving.
2. A family's **label** is frozen at first creation. `family_layer_rebuild.md` attributes the freeze
   to the `if COUNT(*) > 0: return` guard at `scripts/ingest/build_families.py:66` — that guard is
   real, but it governs `kanji_component` / `conjugation_class`. The grammar `function_set` freeze is
   this slug-skip, in a different script with no such guard. Worth correcting in the plan, because
   the two need different fixes.

**Direct in-repo proof of the freeze**, and the reason the 26th label did not match:

| record | title snapshot |
|---|---|
| `grp:gram-n5-desu-wa` (built earlier) | `Gramática: Frases básicas: o tópico は e **a cópula** です` |
| `grp:theme-n5-desu-wa` (built later, same script) | `Campo semântico: Frases básicas: o tópico は e **o copula** です` |
| `course/n5/topic-07-desu-wa/topic.json` today | `Frases básicas: o tópico は e **o copula** です` |

Two families named after the same topic carry two different snapshots of its title. That is the
freeze, visible without running anything.

*(Side finding, not part of A5: the current topic title `"o copula です"` is wrong pt-BR — **cópula**
is feminine and accented. It is wrong in `course/n5/topic-07-desu-wa/topic.json`,
`course/n5/course.json` and `course/outline.json`. The accent lexicon in
`scripts/validate/audit_hygiene_all_locales.py` does not carry this word. The frozen family label
has the correct form.)*

### 3.6 Ten concrete examples

Every row: the grammar record, the family it sits in, and the lesson that actually introduces it.

| # | grammar point | sits in family (label) | actually introduced by | correct family |
|---|---|---|---|---|
| 1 | `gram:cha-ikenai-ja-ikenai` — *não pode / é proibido (〜ちゃいけない)* | `grp:gram-n5-desu-wa` — *Gramática: Frases básicas: o tópico は e a cópula です* | `les:n5-te-form-06` (`top:n5-te-form`, order 15.6) | `grp:gram-n5-te-form` |
| 2 | `gram:dake` — *だけ (apenas, só)* | `grp:gram-n5-desu-wa` | `les:n5-particulas-lugar-08` (order 11.8) | `grp:gram-n5-particulas-lugar` |
| 3 | `gram:te-iru` — *estar fazendo / estado contínuo* | `grp:gram-n5-particulas-lugar` — *Gramática: Lugar, tempo e direção: で/に/へ/と* | `les:n5-te-form-03` (order 15.3) | `grp:gram-n5-te-form` |
| 4 | `gram:gp-36` — *V[た/ている] + substantivo (oração relativa)* | `grp:gram-n5-particulas-lugar` | `les:n5-te-form-04` (order 15.4) | `grp:gram-n5-te-form` |
| 5 | `gram:te-hoshii` — *querer que alguém faça algo* | `grp:gram-n4-condicionais` — *Gramática: Condicionais (たら/ば/と/なら)* | `les:n4-dar-receber-03` (order 27.3) | `grp:gram-n4-dar-receber` |
| 6 | `gram:gp-63` — *passiva 〜れる・られる* | `grp:gram-n4-potencial` — *Gramática: Potencial* | `les:n4-passiva-01` (order 32.1) | `grp:gram-n4-passiva` |
| 7 | `gram:darou` — *だろう (suposição casual)* | `grp:gram-n5-desu-wa` | `les:n5-conectando-04` (order 18.4) | `grp:gram-n5-conectando` |
| 8 | `gram:demo` — *でも (mas / porém)* | `grp:gram-n5-desu-wa` | `les:n5-conectando-03` (order 18.3) | `grp:gram-n5-conectando` |
| 9 | `gram:gp-2` — *これ (isto)* | `grp:gram-n5-perguntas` — *Gramática: Perguntas e demonstrativos* | `les:n5-desu-wa-02` (order 7.2) | `grp:gram-n5-desu-wa` |
| 10 | `gram:gp-22` — *きらい (não gostar de)* | `grp:gram-n5-perguntas` | `les:n5-adjetivos-06` (order 13.6) | `grp:gram-n5-adjetivos` |
| 11 | `gram:ga-arimasu` — *〜があります* | `grp:gram-n5-verbos` — *Gramática: Verbos: dicionário + ます* | `les:n5-particulas-lugar-01` (order 11.1) | `grp:gram-n5-particulas-lugar` |
| 12 | `gram:ga-imasu` — *〜がいます* | `grp:gram-n5-verbos` | `les:n5-particulas-lugar-01` (order 11.1) | `grp:gram-n5-particulas-lugar` |

Rows 1–6 are the five examples `family_layer_rebuild.md` named plus the passive; all six check out
verbatim. Rows 7–12 are new, and show the pattern is not cherry-picked: `grp:gram-n5-desu-wa`, the
first grammar topic in the course, has become a **64-member dumping ground that is 89% wrong** —
it currently claims だけ, だろう, でも and the prohibition form as things "Frases básicas: o tópico は
e a cópula です" teaches.

### 3.7 Scope: this staleness class is specific, not universal

I measured the other two topic-derived family types the same way. They are **not** the same story,
which is itself evidence that the grammar number is real rather than a modelling artefact:

| family type | wrong / total | rate |
|---|---:|---|
| grammar `function_set` (`grp:gram-*`) | **272 / 364** | **74.7%** |
| kanji `function_set` (`grp:kanji-topic-*`) | 5 / 49 | 10.2% |
| `semantic_field` (`grp:theme-*`, matched by label title) | 0 / 387 | 0.0% |

If my slug→topic reading or my "introducing topic" definition were wrong, all three would be wrong
together. They are not. Vocab placement has been stable since the families were built; grammar
placement was re-done. (One `semantic_field` family's label names a topic title that no longer
exists — `"Campo semântico: Saudações e frases de sobrevivência"` — the same freeze, one record.)

---

## 4. The contracts claim

### 4.1 What the design promised

`design/schema_v2.md` §B:

```
group:  id, type, label_pt, description_pt, importance_rank,
        governing_rule_pt, spans_levels[], primary_module_id,
        + provenance (layer=C)
group_related:  group_id, related_group_id, relation   # contrast_pair | sub_family
topic:  id, module_id (FK), order, title_pt, theme_pt, family_ids[],
        objectives_pt[], prerequisites[] (topic ids), + provenance(C)
```

### 4.2 What the contracts declare

`contracts/family.schema.json` — exactly nine properties, `additionalProperties: false`:
`description, governing_rule, id, importance_rank, label, members, slug, spans_levels, type`.
`contracts/topic.schema.json` — exactly seven: `id, lessons, level, objectives, order, theme, title`.
Both match the shipped records field-for-field (I diffed the schemas against the actual key sets).

| promised | in contract | in data |
|---|---|---|
| `group.primary_module_id` | **no** | no |
| `group` provenance (`layer`/`source`/`created_by`/`needs_review`) | **no** | **no** |
| `group_related` / `family.related[]` | **no** | no |
| `topic.family_ids[]` | **no** | no |
| `topic.prerequisites[]` | **no** | no |
| `group.description_pt` | yes | null on **396 / 396** |
| `group.governing_rule_pt` | yes, and in `required` | null on **74 / 396** |
| `group_member.note_pt` | yes (as `note`) | null on **2,572 / 2,572** |

**A5's wording — "silently dropped from the published contracts" — is right about the outcome and
wrong about the mechanism, and the mechanism matters.** `contracts/family.schema.json` carries
`generated_by: scripts/contracts/build_schemas.py from contracts/_shapes.json` and a
`vocabulary_policy` reading *"Types, nesting and `required` are measured from the data."* The
contract is a faithful description of what shipped. Nobody removed the fields; **the fields were
never built, and because the contract is generated from the data, an unbuilt field is an undeclared
field.** The published interface therefore silently narrowed to whatever the builder happened to
emit — which is a real and serious property of this pipeline, just not a deletion.
`scripts/validate/validate_schema_generation_is_current.py` then freezes that narrowing
byte-for-byte.

(History was not consulted: `git` was out of scope for this audit, so I can state only that the
fields are absent from the current contracts and the current data, never that they once appeared
there.)

### 4.3 The sharpest form of the same problem: provenance

`db/corpus.sqlite`'s `family` table **does** carry the fields:

```
primary_module_id  -> NULL on 396/396
source             -> 'derived' on 396/396
created_by         -> 'ai'      on 396/396
layer              -> 'C'       on 396/396
needs_review       ->  1        on 396/396
```

`scripts/export/export_corpus.py` (the family record dict, ~line 439-449) emits none of them. So
**396 AI-authored Layer-C records ship in the source-of-truth artifact with no `layer`, no `source`,
and no `needs_review` flag** — against `CLAUDE.md` §1.1 ("Layer C … **always `needs_review: true`**
for human teacher sign-off").

And `scripts/validate/validate_provenance_json.py` cannot catch it: it infers the expected
provenance set *per entity from the data* (its own comment, line 74: *"today every entity is
all-or-nothing, and that is the property worth defending"*). `family` is in
`contracts/manifest.json`'s 23 entities, carries **zero** provenance fields, so its expected set is
empty and it passes vacuously. `review_queue.py` counts the 396 from the DB, so the teacher queue is
right while the shipped data is silent. **A whole Layer-C entity is exempt from the provenance gate
by construction.**

---

## 5. Quality risks against the near-100% goal

1. **Self-consistent wrongness passes every gate.** This is the transferable lesson. `check_family_graph`
   validates the graph's *internal* coherence and the exporter *derives* `spans_levels` so it cannot
   drift — both good — and neither can see that the whole grouping is keyed to a course that has since
   been rewritten. Any derived artifact needs an assertion against **its source**, not only against
   itself. `kanji_component` (0/51 families matching `kanji.components`) is the same failure in a
   different type.
2. **Append-only builders masquerading as idempotent.** Both family builders say "idempotent" in their
   docstrings and mean "will not overwrite". Re-running them to fix drift makes the layer *worse*
   (duplicate memberships) rather than better. Any other script with `INSERT OR IGNORE` over derived
   rows deserves the same look.
3. **Data-derived contracts silently ratify omissions.** A field that is never built is never declared,
   and `validate_schema_generation_is_current.py` then locks the omission in. The design document is the
   only place the promise still exists, and nothing compares the two. Worth a small gate:
   `design/schema_v2.md` §B fields present in the DB but absent from the export.
4. **Layer-C provenance is exemptible by omission.** Any future entity that ships with no provenance at
   all inherits `family`'s free pass. The fix is a declared floor per entity, not inference.
5. **Two type names lie about their content.** `function_set` is topic order, `semantic_field` is a
   topic-residual bucket. Once a browse UI exists, "Campo semântico" pages will be topic leftovers and
   "função" pages will be lesson order. Renaming is free today and expensive after anything links to
   the slugs.
6. **A rebuild will move slugs.** 15 new `grp:gram-*` families appear and every existing one changes
   membership. Nothing references them today (§3.4) — this is the cheapest moment in the project's life
   to do it, and the cost rises the day the first surface ships.
7. **A5 is still blocked by A3.** `gram:gp`/`gram:da-desu` and `gram:gp-152`/`gram:te-hoshii` all four
   still exist in the export, so the merges have not landed. Rebuilding first means rebuilding twice
   (the effect is small — 2 memberships — but the ordering in PENDING.md is right).

---

## 6. Recommended sequence for this area

0. **Land A3 first** (it is the declared blocker, and it is 2 memberships' worth of rework).
1. **Write the validator before the fix.** A `validate_families.py` in the HARD registry that asserts,
   for every *derived* family type, member set **==** the set recomputed from its source store at the
   declared scope — grammar/kanji `function_set` against the **course unlock graph** (not
   `introducing_topic_id`, so the check is independent of the DB), `conjugation_class` against
   `vocab.verb_class`/`adj_class`, `kanji_component` against `kanji.components`, `word_family` against
   the headword rule. Land it **red**, with today's 272 as a frozen baseline in the style of
   `research/reports/lesson_sentence_baseline.json`, so the number can only shrink. *S, mechanical.*
2. **Make the builders recompute rather than append.** Delete-then-insert the derived memberships keyed
   on `slug`; refresh the label from the topic's current title; preserve hand-edited
   `governing_rule` / `importance_rank`. Remove `build_families.py`'s `COUNT(*)` guard. *M, mechanical.*
3. **Rebuild the derived types level-agnostically** (drop the `level IN ('n5','n4')` literals): grammar
   `function_set` 26→41 families / 364→496 memberships, `conjugation_class` 514→1,166, `kanji_component`
   51→126, `word_family` 261→572. Validator from step 1 goes green and the baseline is deleted. *M, mechanical.*
4. **Export the provenance the DB already holds** (`layer`, `source`, `created_by`, `needs_review`) and
   give `validate_provenance_json.py` a *declared* floor per entity instead of an inferred one. Regenerate
   contracts. *S, mechanical — and it is a `CLAUDE.md` §1.1 compliance fix, not a nice-to-have.*
5. **Rename before anything links to the slugs:** topic-derived grammar/kanji grouping → `topic_set`;
   topic-residual vocab bucket → `topic_residual`. Frees `function_set` and `semantic_field` for the
   authored pass. *S, mechanical, zero content risk — but it is a slug change, so it must precede any UI.*
6. **Add `family.related[]` and `topic.family_ids[]`** end to end (ingest → export → contract →
   validator), emitted as `[]` when empty so the shape is stable from day one. Seed `related` from the
   two existing `contrast_pair` families and the `design/schema_v2.md` §C example edge
   (`grp:wa-vs-ga` → `grp:particles-core`, `sub_family`). *M; the plumbing is mechanical, the edges are authored.*
7. **Authored Layer C, last and separately:** real communicative `function_set`s over the 496 grammar
   points, real `semantic_field`s over vocab, curated `contrast_pair`s. `needs_review: true`, teacher
   sign-off. AI can draft; a teacher must accept. *L.*

Steps 1–5 are safe to run autonomously and are best run **now**, precisely because §3.4 shows nothing
consumes the layer yet.
