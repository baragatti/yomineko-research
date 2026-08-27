# Grammar duplicate-identity merges — evidence and impact map

**generated 2026-08-27, proposal for owner sign-off, repo unchanged**

Four grammar record pairs claim the same set of surface forms of two characters or more. This report
reads all eight records in full, decides for each pair whether it is one point wearing two identities
or two points sharing a spelling, and — for the merge candidates — enumerates every reference to the
losing slug across the tree with counts per location class, the migration steps, the fate of the
losing record, and the risks.

Nothing in the repository was changed.

---

## 0. How the references were counted

The whole repository was walked (9,948 files), excluding `.git`, `__pycache__`, and
`.claude/worktrees/great-dubinsky-b163a4` — a second full checkout of this repo that carries its own
copy of `course/` (515 lesson files) and would double every number below. Binary and archive payloads
(`.sqlite`, `.bz2`, `.tgz`, `.zip`, `.svg`) were skipped; `db/corpus.sqlite` is git-ignored and
regenerable, so it is out of scope for a reference count but very much in scope for the migration
(§5).

Two kinds of hit were separated:

- **identity edge** — a JSON string that *is* the address: exactly `"gp-152"` (bare key, as in
  `sentence.grammar[]`, `capability.grammar_keys[]`, `exam_item.grammar`) or exactly `"gram:gp-152"`
  (slug, as in `lesson.unlocks[].ref`, `srs.introduces_cards[].item`,
  `cumulative_known_set.grammar[]`, `family.members[].slug`). These break if the slug disappears.
- **prose mention** — the token appearing inside a longer string or a Markdown file. These do not
  break, but they mislead a reader and a future AI pass.

The reviewers measured "~285 refs each" for the copula pair. **Verified and refined:** 283 is the
count inside `course/**/lesson-*.json` for both `gp` and `da-desu`. The whole live tree carries 298
for `gp` and 331 for `da-desu`. The reviewers' figure was the course-lesson slice, not the total.

---

## 1. Verdicts at a glance

| pair | verdict | canonical | loser |
|---|---|---|---|
| `gram:gp` {です} vs `gram:da-desu` {だ,です} | **MERGE** — one copula, two identities, same lesson, same family | `gram:da-desu` | `gram:gp` |
| `gram:gp-36` {た,ている} vs `gram:te-iru` {ている} | **KEEP BOTH** — relative clause vs aspect; fix `gp-36.forms[]`, re-slug, cross-link | — | — |
| `gram:gp-63` vs `gram:gp-115` {れる,られる} | **KEEP BOTH** — passive vs potential; the collision is manufactured by a wrong `forms[0]` on gp-115 | — | — |
| `gram:gp-152` vs `gram:te-hoshii` {てほしい} | **MERGE** — same point, same lesson, and the loser carries leaked authoring commentary in learner-facing pt-BR | `gram:te-hoshii` | `gram:gp-152` |

---

## 2. Pair-by-pair evidence

### 2.1 `gram:gp` vs `gram:da-desu` — MERGE into `gram:da-desu`

**They are the same point.**

| | `gram:gp` (id 15) | `gram:da-desu` (id 2) |
|---|---|---|
| label pt-BR | です (cópula educada) | だ / です (cópula 'ser/estar') |
| forms | です | だ, です |
| structure_pattern | です | だ / です |
| register | polite | plain, polite |
| level agreement | 2/2 (bunpro, tanos) | 2/2 (jlptsensei, bunpro) |
| formation_steps variants | noun/na-adj/i-adj + です (3) | noun/na-adj + です/だ, i-adj + です (5) |
| refs.label_en | です | da / desu |
| refs.also_known_as | `[]` | `["だ", "da / desu"]` |
| family | `grp:gram-n5-desu-wa` (intra_order 5) | `grp:gram-n5-desu-wa` (intra_order 1) |
| capability | `cap:topic:n5-desu-wa` (topic fallback) | `cap:copula` (semantic) |
| unlocked by | `les:n5-desu-wa-01` | `les:n5-desu-wa-01` |
| placement (`design/grammar_placement.json`) | `top:n5-desu-wa`, confidence **high** | `top:n5-desu-wa`, confidence **high** |

`da-desu` is a strict superset: its `forms[]` contains everything `gp` has plus だ, and its
`formation_steps.variants` contains all three of `gp`'s plus the two だ variants. Neither record
carries a fact the other lacks. `gp`'s own explanation already teaches the missing half —
"A versão casual de です é だ" — so the two prose bodies are paraphrases of one another.

The decisive structural evidence is that **one lesson unlocks both**. `les:n5-desu-wa-01` has:

```
unlocks: [ {grammar, gram:da-desu}, {grammar, gram:gp}, {grammar, gram:wa-topic-marker} ]
srs.introduces_cards: gram:da-desu, gram:gp, gram:wa-topic-marker  (3 card types each)
```

The learner meets the copula twice in one lesson and is issued six SRS cards for one fact. Both then
sit in the same family, `grp:gram-n5-desu-wa`, four positions apart.

**Why `da-desu` is canonical, not `gp`.** `gp` is not a name. It is the head of a numeric series —
`gp`, `gp-2`, `gp-3`, `gp-4`, `gp-14`, … `gp-152` — mechanically minted from a numbered source list
during ingestion, and it collides with the project's other, semantic slug stream (`da-desu`,
`te-iru`, `te-hoshii`, `wa-topic-marker`, `nakute-wa-naranai`). Nothing stopped it:
`contracts/grammar.schema.json` types `key` as a bare `{"type": "string"}` with no pattern. The
capability layer already votes the same way — `da-desu` was assigned to the semantic `cap:copula`
alongside `darou`, `deshou`, `janai-dewa-nai`, `ndesu`, while `gp` landed only in the topic-fallback
`cap:topic:n5-desu-wa`.

**Salvage before retiring `gp`.** Two things in `gp` are not in `da-desu` and should be folded in:

1. `gp.nuance` point (3) — the です / ます confusion ("não confunda です (afirmar) com ます (que educa
   verbos de ação)"). `da-desu.nuance` warns about あります／います but not about ます.
2. `gp.nuance` point (2) — that with an い-adjective です adds only politeness and the negation/past
   go on the adjective (たかくないです / たかかったです). `da-desu.formation` states the ×高いだ ban but
   not where negation lands.

---

### 2.2 `gram:gp-36` vs `gram:te-iru` — KEEP BOTH, disambiguate

**These are different points.** `gp-36` is the noun-modifying (attributive / relative) clause;
`te-iru` is the progressive-resultative aspect. The forms sets collide only because `gp-36` lists the
bare morphemes た and ている in `forms[]` instead of the construction it actually teaches.

| | `gram:gp-36` (id 51) | `gram:te-iru` (id 135) |
|---|---|---|
| label | Verbo［forma た / ている］+ substantivo (oração relativa) | estar fazendo / estado contínuo (～ている) |
| structure_pattern | `Verb［た・ている］+ Noun` | `～ている` |
| what it teaches | the modifier precedes the noun; no word for "que"; no です／ます inside the clause; internal subject takes が or の | ている = ongoing action **or** resultant state; 行っている ≠ "is going"; particle before the verb stays を/が |
| formation_steps | both chains end in `{op: to-attributive}` | chains end in `append いる / います / る`; **no** `to-attributive` |
| unlocked by | `les:n5-te-form-04` | `les:n5-te-form-03` |
| placement reason | "Verb (た/ている) directly modifying a noun" | "〜ている (ação em curso/estado) listado explicitamente nos objetivos" |
| level agreement | 1/1 (bunpro) | 3/3 (jlptsensei, bunpro, tanos) |

The `formation_steps` are the cleanest machine-readable proof: `gp-36`'s two variants both terminate
in `to-attributive` and `te-iru`'s three do not. The course agrees — two consecutive but distinct
lessons, `te-form-03` then `te-form-04`, which is the correct pedagogical order (learn ている, then
learn to hang it in front of a noun).

**What to fix instead of merging** (all owner-optional, none load-bearing for the graph):

1. `gp-36.forms[]` — replace the bare `た` / `ている` entries with the pattern actually taught, e.g.
   `た＋Noun` and `ている＋Noun`, or drop `forms[]` and let `structure_pattern` carry it. This alone
   removes the collision.
2. Re-slug `gram:gp-36` to a semantic slug (`gram:noun-modifying-clause` or `gram:rentai-shuushoku`).
   This is a rename with the same blast radius as a merge (256 live refs) and should be batched with
   the two merges if it is done at all.
3. Add `related` cross-links between them. Only **4 of 496** grammar records have a non-empty
   `related[]`; all eight records in this report have `related: []`. `gp-36` depends on `te-iru` and
   says so in prose; the link should be data.
4. Family mis-file (see the family-layer report): both sit in `grp:gram-n5-particulas-lugar`, a
   *place-particles* family, although both are unlocked under `top:n5-te-form`.

---

### 2.3 `gram:gp-63` vs `gram:gp-115` — KEEP BOTH, distinct points, fix `gp-115.forms[0]`

**These are genuinely distinct grammar points sharing surface forms** — exactly the case the task
flagged.

| | `gram:gp-63` (id 220) | `gram:gp-115` (id 182) |
|---|---|---|
| label | passiva 〜れる・られる (voz passiva) | forma potencial, "poder/conseguir" (〜れる・られる) |
| structure_pattern | `Verb［れる・られる］` | `れる・られる (Potential)` |
| formation op | `to-passive` (example 書かれる) | `to-potential` (example 書ける) |
| particle behaviour | agent takes に (sometimes から); patient takes は/が | direct object switches を → が (パンが食べられる) |
| godan realization | 書く → 書か**れる** | 書く → 書**ける** |
| ichidan realization | 食べる → 食べられる | 食べる → 食べられる |
| unlocked by | `les:n4-passiva-01` (`top:n4-passiva`) | `les:n4-potencial-01` (`top:n4-potencial`) |
| placement confidence | high | high |
| exam items | 4 (`gf:n4:3566`–`3569`) | 1 (`gf:n4:3444`) |

The syncretism is real but **partial**: it holds for ichidan verbs (られる serves passive, potential,
and honorific) and not for godan, where the passive is *-areru* and the potential is *-eru*. Both
records already say so in their own `nuance` — gp-63: "as formas do Grupo 2 (〜られる) coincidem com o
potencial"; gp-115: "nos verbos do grupo 2, 〜られる serve tanto para potencial quanto para
passiva/respeito". Two records that each warn about the other are not one record.

**The collision is manufactured by `gp-115.forms[0]`.** That entry is:

```json
{"form": "れる",
 "meaning": {"pt-BR": "poder/conseguir (potencial dos godan: o -u final vira -eru, como em 話せる, 書ける)"}}
```

The `form` value says れる; the `meaning` value describes *-eru*. れる is the godan **passive**
suffix. This is the open item `STATE.md` has carried since at least the 2026-08-07 entry and repeats
in four session records:

> **Open:** … `gram:gp-115` forms[0] (れる is the godan PASSIVE; registry convention would store a
> form NAME like 可能形 — needs sign-off)

**Recommendation for that sign-off.** Two workable options, both of which collapse the collision from
{れる, られる} to {られる}:

- (a) Follow the stated registry convention and store the form *name*: `可能形` with meaning
  "forma potencial". Consistent with "no kana suffix exists for the potential", but it makes `forms[]`
  heterogeneous — every other record stores a kana string.
- (b) Store the realization pattern instead: `〜える` (or `-eru`), which is a kana string like every
  other entry and is what a learner actually writes. `structure_pattern` already carries the label
  ("れる・られる (Potential)") and would need the same correction.

Either way, add `related` links between gp-63 and gp-115 with a contrast relation, and re-slug both
to semantic slugs (`gram:passive-rareru`, `gram:potential-rareru`) if the numeric series is being
retired generally. Also note the family mis-file: **gp-63, the passive, is a member of
`grp:gram-n4-potencial`.**

---

### 2.4 `gram:gp-152` vs `gram:te-hoshii` — MERGE into `gram:te-hoshii`

**They are the same point**, and one of them is contaminated.

| | `gram:gp-152` (id 212) | `gram:te-hoshii` (id 326) |
|---|---|---|
| label | 〜てほしい (querer que alguém faça) | querer que alguém faça algo (〜てほしい) |
| forms | てほしい | てほしい |
| structure_pattern | `～てほしい` | `てほしい` |
| register / caution | plain / null | casual, colloquial / **rough** |
| level agreement | 1/1 (tanos) | 2/2 (jlptsensei, bunpro) |
| formation_steps | て+ほしい; nai-stem + いでほしい | て+ほしい; て+ほしくない; て+ほしかった |
| family | `grp:gram-n4-volitivo` | `grp:gram-n4-condicionais` |
| capability | `cap:topic:n4-dar-receber` (topic fallback) | `cap:desire` (semantic) |
| unlocked by | `les:n4-dar-receber-03` | `les:n4-dar-receber-03` |
| placement | `top:n4-dar-receber`, confidence medium | `top:n4-dar-receber`, confidence medium |

Same form, same meaning, same に-marked person, same 〜たい contrast, same 〜ていただけませんか politeness
escape hatch, same topic, and — again — **the same lesson unlocks both**, issuing two SRS cards for
one pattern. The two `reason` strings in `design/grammar_placement.json` are paraphrases of each
other.

**`gp-152` also carries leaked authoring commentary inside learner-facing pt-BR.** Its `forms[0]`:

```json
{"form": "てほしい",
 "meaning": {"pt-BR": "querer que alguém faça (na verdade 〜てほしい; a grafia tem erro de digitação)"}}
```

and its `explanation.pt-BR` ends:

> A grafia "のようてほしい" do material tem um erro de digitação; o ponto real é 〜てほしい.

A note *to the build* about a corrupt source-list entry was written into the content field a learner
reads. This is the same defect class `archive/ARCHIVE.md` records for the seven N3 lessons where
review-finding text was pasted into `title` / `body`, and which
`scripts/apply_phase7_content_repairs.py` swept for elsewhere. Retiring `gp-152` removes two more
instances of it. **Before deleting, check `les:n4-dar-receber-03`'s body** — the reference scan shows
2 prose hits for `gp-152` in lesson JSON bodies and 2 more in the Markdown views; if the "erro de
digitação" phrasing was copied into the lesson, retiring the record will not clean it.

**Salvage before retiring `gp-152`:**

1. The negative-request formation — `〜ないで + ほしい` / 行かないでほしい. `te-hoshii.formation` does not
   have it and `te-hoshii.formation_steps` has no nai-stem variant. **Caveat:** `gp-152`'s own
   variant looks wrong — `{op: to-nai-stem}` then `append "いでほしい"` yields 行か+いでほしい unless
   `to-nai-stem` already emits 行かな. Re-derive rather than copy, and re-run
   `validate_grammar_formation.py`.
2. The third-person desire note — `〜てほしがっている`, absent from `te-hoshii`.
3. Reconcile `register`. `te-hoshii` currently says `["casual","colloquial"]` with
   `caution: "rough"`; `gp-152` says `["plain"]`. 〜てほしい is plain-form, not slang. The merged record
   should keep the directness caution and widen `register` to include `plain` — flag for teacher
   review rather than deciding it here.

---

## 3. Impact map — every reference to the two losing slugs

Counts are **identity edges** unless the row says otherwise. `gram:gp` and `gram:gp-152` are the
merge losers; the other six columns are shown for comparison and for the optional re-slug work.

### 3.1 Live source-of-truth tree (`corpus/`, `course/`, `design/`)

| location class | gp | da-desu | gp-36 | te-iru | gp-63 | gp-115 | gp-152 | te-hoshii |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `course/**/lesson-*.json` — total | **283** | 283 | 227 | 228 | 131 | 177 | **159** | 159 |
| &nbsp;&nbsp;· `cumulative_known_set.grammar[]` | 281 | 281 | 225 | 226 | 129 | 175 | 157 | 157 |
| &nbsp;&nbsp;· `unlocks[].ref` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| &nbsp;&nbsp;· `srs.introduces_cards[].item` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `course/outline.json` | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| `course/**/topic.json` (`lessons[].unlocks[].ref`) | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `course/speak/**/unit-*.json` (`patterns[]`, `patterns_chunked[]`, `drills[].pattern`) | 0 | 26 | 10 | 0 | 0 | 7 | **2** | 0 |
| `corpus/capabilities/registry.json` (`grammar_keys[]`) | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `corpus/families/families.json` (`members[].ref` + `.slug`) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| `corpus/sentences/bank.json` (`grammar[]` + `tags[]`) | 6 | 11 | 10 | 5 | 10 | 11 | **10** | 7 |
| &nbsp;&nbsp;· of which `grammar[]` / `tags[]` | 6/0 | 11/0 | 5/5 | 5/0 | 7/3 | 6/5 | 5/5 | 7/0 |
| `corpus/exam_banks/*.json` (`grammar`) | 0 | 2 | 0 | 0 | 4 | 1 | **0** | 0 |
| `design/grammar_placement.json` (`key`, `prereq`) | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| `corpus/grammar/n*.json` — the record itself (`slug` + `key`) | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| **live subtotal** | **298** | **331** | **256** | **242** | **154** | **205** | **180** | **175** |

Exam-bank items by id: `gf:n4:3566`, `gf:n4:3567`, `gf:n4:3568`, `gf:n4:3569` → `gp-63`;
`gf:n4:3444` → `gp-115`; `gf:n5:1053`, `gf:n5:1054` → `da-desu`. **Neither merge loser has any exam
item** — nothing to repoint there.

Capability rows touched by the merges:

```
cap:topic:n5-desu-wa    [n5]  grammar_keys = gp, gp-2, gp-3, gp-33, gp-4          -> drop "gp"
cap:topic:n4-dar-receber[n4]  grammar_keys = gp-106, gp-108, gp-109, gp-152       -> drop "gp-152"
cap:copula              [n5]  grammar_keys = da-desu, darou, deshou, janai-dewa-nai, ndesu   (winner, unchanged)
cap:desire              [n5]  grammar_keys = ga-hoshii, gari, garu-gatteiru, n3-te-hoshii,
                                             n3-to-ii-naa, tagaru, tai, te-hoshii            (winner, unchanged)
```

Family rows touched:

```
grp:gram-n5-desu-wa  (function_set, 64 members)  -> remove member "gp" (intra_order 5); da-desu stays at 1
grp:gram-n4-volitivo (function_set, 30 members)  -> remove member "gp-152" (intra_order 9)
```

Note that the winner `te-hoshii` is in a *different* family (`grp:gram-n4-condicionais`) from the
loser. Both placements are wrong — `te-hoshii` is not a conditional and `gp-152` is not volitional —
but that is the family-layer defect covered in the companion report, not something this merge should
try to fix inline.

### 3.2 Derived / mirrored (regenerated — do not hand-edit)

| location | gp | da-desu | gp-36 | te-iru | gp-63 | gp-115 | gp-152 | te-hoshii |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `prototype/app/data/*.json` | 292 | 325 | 245 | 236 | 145 | 194 | 169 | 169 |

Guarded by `scripts/validate/validate_prototype_sync.py`. `db/corpus.sqlite` is git-ignored and
regenerable but is the store the exporters read — see §5.

### 3.3 Frozen and non-authoritative

| location | gp | da-desu | gp-36 | te-iru | gp-63 | gp-115 | gp-152 | te-hoshii |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `archive/course-pre-renumber-2026-06-26/**` | 192 | 192 | 192 | 192 | 127 | 173 | 155 | 155 |
| `research/**` (working notes, patch queues, QA inputs) | 58 | 63 | 94 | 60 | 98 | 115 | 87 | 87 |
| `scripts/**` (prose/comments only, 0 identity edges) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **grand total incl. all zones** | **840** | **911** | **787** | **730** | **524** | **687** | **591** | **586** |

Prose mentions (non-breaking) across the live tree: `gp` 6 in lesson JSON bodies + 5 in lesson
Markdown; `gp-152` 2 + 2; `gp-115` 5 in `STATE.md`. `reports/coverage_comparison.md` mentions
`da-desu` once.

### 3.4 The rest of the collision class (out of scope, same defect)

The forms-set index over all 496 grammar records finds **seven** collisions on forms of two or more
characters, not four. After the two merges proposed here, five remain:

```
[です]         da-desu/n5      | gp/n5              -> MERGE (this report)
[てほしい]     gp-152/n4       | te-hoshii/n4       -> MERGE (this report)
[ている]       gp-36/n5        | te-iru/n5          -> keep, disambiguate
[られる+れる]  gp-115/n4       | gp-63/n4           -> keep, fix forms[0]
[しかない]     gp-100/n4       | gp-118/n4          -> UNTRIAGED
[すこしもない] gp-103/n4       | n3-sukoshimo-nai/n3 -> UNTRIAGED (cross-level near-duplicate)
[～ように]     n3-you-ni/n3    | n3-you-ni-2/n3     | n3-you-ni-3/n3  -> UNTRIAGED (3-way)
```

Two more near-duplicates escape the index only because of a `～` prefix: `n3-te-iru` (forms
`["～ている"]`) against `te-iru`, and `n3-te-hoshii` (forms `["～てほしい"]`) against `te-hoshii`. Both
are already co-listed inside the same capability (`cap:aspect-teiru` holds `te-iru` **and**
`n3-te-iru`; `cap:desire` holds `te-hoshii` **and** `n3-te-hoshii`), so if they are N3 extensions of
the N5/N4 point that is defensible — but it is untriaged and should be decided in the same pass.

---

## 4. Canonical-slug decisions, restated

| loser | winner | why the winner |
|---|---|---|
| `gram:gp` | `gram:da-desu` | superset forms and formation_steps; real name in `refs` (`also_known_as: ["だ","da / desu"]` vs `[]`); semantic capability `cap:copula` vs topic fallback; `gp` is the head of the mechanical `gp-N` ingestion series |
| `gram:gp-152` | `gram:te-hoshii` | 2/2 level agreement vs 1/1; semantic capability `cap:desire` vs topic fallback; loser's pt-BR content is contaminated with build commentary; loser's second formation variant is likely wrong |

Both winners are on the semantic slug stream, which is the convention the rest of the registry
(`wa-topic-marker`, `nakute-wa-naranai`, `n3-kara-ni-kakete`, …) already follows.

---

## 5. Migration steps

**The exported JSON is not the place to edit.** `scripts/export/export_corpus.py` and
`export_course.py` both read `db/corpus.sqlite` and write `corpus/` and `course/`. A merge applied to
the JSON alone is undone by the next export. Worse, `archive/ARCHIVE.md` records exactly this failure
in reverse: a repair script that wrote only `db/corpus.sqlite` left nine corrupt values alive in the
tracked authoring source under `research/derived/lessons/`, where "one loader+export cycle would have
reintroduced them". **Both layers must be written.**

Proposed sequence:

0. **Baseline.** Run `scripts/validate/validate_all.py` and `validate_contracts.py`; record green.
   Commit nothing yet.

1. **Write a one-shot, idempotent migration** under `scripts/`, following the existing
   `apply_*.py` convention (`apply_qa_instruction_leaks.py` is the model: it records exact
   before/after and the reasoning for every field it touches).

2. **Salvage fields into the winners** (§2.1 and §2.4 lists). For `te-hoshii`, re-derive the
   `〜ないでほしい` variant rather than copying `gp-152`'s, then re-run
   `validate_grammar_formation.py`.

3. **Rewrite the edges**, DB side and authoring-source side:

   | edge | action | count |
   |---|---|---|
   | `lesson_introduces` / `unlocks[]` | delete the loser row — the winner is already unlocked in the *same* lesson, so this is pure deletion, no re-pointing and no ordering change | 1 + 1 |
   | `srs.introduces_cards[]` | delete the loser card (same lesson) | 1 + 1 |
   | `cumulative_known_set.grammar[]` | **do not hand-edit** — schema_v2 §B declares it `(computed json)`; the 281 + 157 entries fall out on re-export | 281 + 157 |
   | `capability.grammar_keys[]` | drop `gp` from `cap:topic:n5-desu-wa`, `gp-152` from `cap:topic:n4-dar-receber`; `build_capabilities.py` derives from unlocks, so verify this is automatic before editing by hand | 1 + 1 |
   | `family.members[]` | drop the loser member from `grp:gram-n5-desu-wa` / `grp:gram-n4-volitivo`; renumber `intra_order` | 1 + 1 |
   | `sentence.grammar[]` | repoint to the winner, **dropping duplicates** where the sentence already carries the winner | 6 + 5 |
   | `sentence.tags[]` | repoint; `gp` has 0, `gp-152` has 5 | 0 + 5 |
   | `exam_item.grammar` | nothing — neither loser has an item | 0 + 0 |
   | `course/speak/**` `patterns[]` / `drills[].pattern` | `gp` 0; `gp-152` 2 (`course/speak/lodging/unit-06.json`) → repoint to `te-hoshii` | 0 + 2 |
   | `course/outline.json`, `topic.json` | regenerated by `export_course.py` | 2+1 each |
   | `design/grammar_placement.json` | hand-maintained design input — delete the loser's row and note why in the file | 1 + 1 |
   | `research/derived/lessons/**` and the other authoring queues | must be rewritten or the next loader run reintroduces the loser | 58 + 87 |
   | `prototype/app/data/**` | regenerated; `validate_prototype_sync.py` must pass after | 292 + 169 |
   | `archive/**` | **do not touch** — see §6 | 192 + 155 |

4. **Retire the loser records.** `archive/ARCHIVE.md` sets the convention: nothing is deleted, nothing
   moves without an independent audit recorded in that file, and restoring anything means re-running
   the full gate. There is no directory to move for a single record, so:
   - write `archive/grammar-merged-2026-08-27/gram-gp.json` and `gram-gp-152.json` holding the
     complete pre-merge records;
   - add an `ARCHIVE.md` section with the audit table (reachability, nothing-unique-lost, content
     comparison, inbound references, git status) in the same shape as the existing entry;
   - add a permanent alias map, `corpus/grammar/retired_slugs.json`:
     `{"gram:gp": "gram:da-desu", "gram:gp-152": "gram:te-hoshii"}`. §1.7 rests on stable IDs, and a
     merge deletes an ID that 298 and 180 live places once used. Precedent already exists in
     `corpus/exam_banks/removed_items.json`.

5. **Re-export and commit the JSON/MD** (CLAUDE.md: after any phase that changes corpus/courseware
   data, re-run the exporter and commit). Order: `export_corpus.py` → `export_course.py` →
   `build_capabilities.py` → prototype sync.

6. **Gate.** `validate_all.py` + `validate_contracts.py`, watching in particular
   `audit_export_refs.py`, `validate_stable_addresses.py`, `validate_unlock_ledger.py`,
   `validate_graph_edges.py`, `validate_capabilities.py`, `validate_lesson_gating.py`,
   `validate_course_chain.py`, `validate_srs_decks.py`, `validate_prototype_sync.py`.

7. **Add the validator that prevents recurrence.** A hard check that no two grammar records share an
   identical set of `forms[].form` values of length ≥ 2. It fails on today's data with 7 collisions;
   after these two merges it fails with 5, so land it *with* the triage of §3.4, not before.
   Optionally also give `contracts/grammar.schema.json` a `key` pattern so the `gp-N` stream cannot
   be minted again.

---

## 6. Risks

1. **Editing one layer only.** The single most likely failure, and the one this repo has already
   made once. `db/corpus.sqlite` + `research/derived/` + the exports must move together.
2. **`archive/` must stay frozen.** It holds 192 (`gp`) and 155 (`gp-152`) identity edges. Rewriting
   a snapshot to match a later decision destroys the snapshot's only property. Record the mapping in
   `ARCHIVE.md`; leave the files alone.
3. **Two SRS cards vanish from a shipped deck.** `deck:grammar-n5` loses `gram:gp`,
   `deck:grammar-n4` loses `gram:gp-152`. No learner data exists yet, so the cost is zero today and
   unbounded later — the alias map in step 4 is what makes it recoverable either way.
4. **The prototype ships its own copy** (292 / 169 refs). Skipping the re-sync leaves dead links in
   the running app; `validate_prototype_sync.py` is the guard.
5. **`cumulative_known_set` is stored, not computed at read time,** in the exported JSON. Any consumer
   diffing the shipped set will see 281 + 157 removals in one commit. Expected, and the point.
6. **Contaminated text may already be downstream of `gp-152`.** Two prose hits in lesson JSON bodies
   and two in the Markdown views. Deleting the record does not clean a lesson that quoted it — check
   `les:n4-dar-receber-03` first.
7. **`gp-152`'s `〜ないでほしい` formation variant is probably broken.** Copying it into the winner
   would import a defect while removing one.
8. **The string `"gp"` becomes free.** Nothing should ever reuse it; the retired-slug map is the
   record that says so.
9. **Scope creep.** The re-slugging of `gp-36`, `gp-63`, `gp-115` (§2.2, §2.3) has the same blast
   radius as a merge — 256, 154, 205 live refs — but zero semantic content. If it happens, batch it
   with the merges so the tree is rewritten once, not four times.
10. **`gp-115.forms[0]` is a separate, already-open decision.** It is not a merge, it needs an owner
    answer (§2.3 options a/b), and until it is answered the `[られる+れる]` collision stays in the data
    and the new validator of step 7 cannot be made hard.
