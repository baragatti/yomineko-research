# W08 merge ledger — owner decision A3, duplicate-identity grammar points

Applied 2026-09-02 by `scripts/migrate_grammar_merge.py --apply` against `db/corpus.sqlite` and
`research/derived/lessons/`. Machine-readable companion: `research/derived/grammar_merge_ledger.json`
(the appended values, the salvaged prose verbatim, and the per-table edge counts). This file is the
reading copy: what was merged, what was refused, and what the numbers actually are.

Two records were merged. Nothing was deleted. The loser keeps its `grammar_point` row with every
field it had and gains `deprecated_by`; `corpus/grammar_deprecated.json` publishes the redirect, so
an address that used to resolve still resolves — to the survivor.

```
gram:gp      {です}      ->  gram:da-desu     (one copula registered twice)
gram:gp-152  {てほしい}   ->  gram:te-hoshii   (same point, same form, same lesson)
```

---

## 1. Triage — all fifteen groups

`research/reports/grammar_identity_merges.md` found seven forms-set collisions (rows A1, A2, U1-U3
and the two KEEP-BOTH pairs); the readiness audit added ten near-duplicate pairs (D1-D10). All
fifteen are triaged here. Evidence per row: whether ONE lesson unlocks both records, whether the
forms sets are a superset/subset relation, and whether the two pt-BR explanations describe the same
rule. `same lesson` is the strongest single signal — it means the course is already issuing two SRS
cards for one pattern.

| # | records | one lesson? | forms | verdict | why |
|---|---|---|---|---|---|
| **A1** | `gp` / `da-desu` | yes, `les:n5-desu-wa-01` | `{です}` ⊂ `{だ, です}` | **MERGED** | `gp` is the です half of `da-desu`. Same topic, same family, all six of `gp`'s sentences already carry `da-desu`. §2.1 |
| **A2** | `gp-152` / `te-hoshii` | yes, `les:n4-dar-receber-03` | `{てほしい}` = `{てほしい}` | **MERGED** | Identical form and rule, one lesson, two cards. §2.4 |
| K1 | `gp-36` / `te-iru` | no | collision only | KEEP BOTH | Relative clause (`Verb[た・ている] + Noun`) vs the ている aspect. The collision is a wrong `forms[0]` on `gp-36`, not one point. §2.2 |
| K2 | `gp-63` / `gp-115` | no | collision only | KEEP BOTH | Passive vs potential. Manufactured by a wrong `gp-115.forms[0]`. §2.3 |
| U1 | `gp-100` / `gp-118` | yes, `les:n4-forma-simples-03` | `{しかない}` = `{しかない}` | duplicate, NOT executed | Same rule (〜しか〜ない), one lesson, two cards. Mechanically the A2 shape. Families disagree (`n4-causativa` vs `n4-aspecto`) and both look wrong, so the winner also inherits a family defect — see §5 |
| U2 | `gp-103` (n4) / `n3-sukoshimo-nai` (n3) | no — different lessons AND levels | `{すこしもない}` / `{すこしも～ない}` | REFUSED | Cross-level. Merging an N4 record into an N3 one moves an item out of the N4 course; that is a curriculum decision, not a migration |
| U3 | `n3-you-ni` / `-2` / `-3` | yes, `les:n3-intencao-03` | all `{～ように}` | REFUSED | Three records, three genuinely different senses in the prose (finalidade / resultado desejado / modo). Needs a sense split before any merge; merging first would destroy the distinction |
| D1 | `gp-50` / `hou-ga-ii` | **no** — `n5-convites-04` vs `n5-conectando-05` | `{たほうがいい}` / `{ほうがいい}` | REFUSED | Two different lessons teach them. 〜たほうがいい (advice, past form) is a narrower point than ほうがいい (comparison). Merging removes a lesson's only unlock |
| D2 | `gp-54` / `no-ga-jouzu` | yes, `les:n5-adjetivos-07` | `{のがじょうずです}` / `{のが上手}` | duplicate, NOT executed | Same rule, same lesson, same family; the forms differ only in kana-vs-kanji spelling of 上手, which is why the forms index missed it |
| D3 | `gp-145` / `nakucha` | yes, `les:n5-te-form-08` | `{なくちゃいけない}` / `{なくちゃ}` | REFUSED | なくちゃ standing alone (ending elided) is a real colloquial variant, not the same surface form. Which of the two is the record and which is a form of it is an authoring call |
| D4 | `gp-47` / `yori-hou-ga` | yes, `les:n5-comparacoes-01` | `{よりのほうが}` / `{よりほうが}` | duplicate, NOT executed | One comparative pattern; the の is optional in the pattern itself. Both family placements are wrong (`n5-desu-wa`, `n5-passado`) |
| D5 | `gp-77` / `gp-154` | yes, `les:n4-suposicao-04` | `{のように, のような}` ⊃ `{のように}` | duplicate, NOT executed | Clean superset, same lesson, same family. The A1 shape exactly, with `gp-77` as survivor |
| D6 | `tara` / `gp-60` | yes, `les:n4-condicionais-01` | `{たら}` / `{ら}` | duplicate, NOT executed | Same point. `gp-60.forms[0]` is `ら`, a broken form — the same defect that manufactured K2, here on top of a real duplicate |
| D7 | `gp-151` / `te-shimau-chau` | yes, `les:n4-aspecto-03` | `{てしまう}` ⊂ `{てしまう, ちゃう}` | duplicate, NOT executed | Superset, same lesson, same family, 4 sentences already shared |
| D8 | `gp-33` / `janai-dewa-nai` | yes, `les:n5-desu-wa-03` | `{じゃない}` ⊂ `{じゃない, ではない}` | duplicate, NOT executed | Superset, same lesson. The A1 shape, one level down |
| D9 | `gp-112` / `itashimasu` | yes, `les:n4-keigo-05` | `{いたす}` / `{いたします}` | duplicate, NOT executed | Dictionary form vs polite form of one humble verb, registered as two points in one lesson |
| D10 | `n3-da-mono-da` / `n3-nda-mon` | yes, `les:n3-causa-04` | `{～(ん)だもの}` ⊃ `{～んだもん}` | duplicate, NOT executed | The survivor's own label already reads `～(ん)だもの / ～だもん` |

**Executed: A1 and A2 only.** They are the two the report proved, with a written verdict behind each
and hand-measured preconditions in `MERGES[].expect`.

The eight rows marked *duplicate, NOT executed* (U1, D2, D4, D5, D6, D7, D8, D10) carry the same
defect and are mechanically ready — `MERGES` is a data table and each is one row plus its measured
`expect` block. They were not executed here because each one additionally decides **which of two
independently authored pt-BR explanations a learner sees**, and that is authoring, not migration
(CLAUDE.md 1.8: the teacher-review loop is mandatory). Two of them (D4, D6) also need a family or a
`forms[0]` fix first, or the survivor inherits the loser's defect. This needs an owner call before a
follow-up unit runs; it is not a gap that closes itself.

---

## 2. Content merged into each survivor

Every loser field and JSON column was diffed against the survivor's. What the survivor lacked was
appended; what it already had was reported as covered; free prose was salvaged verbatim rather than
concatenated, and both survivors were put back into the review queue (`needs_review = 1`).

### `gram:gp` -> `gram:da-desu`

| column | action |
|---|---|
| `usage_contexts_json` | appended `business` -> `[spoken, written, casual-friends, business]` |
| `level_sources` | merged `tanos: n5` -> 3 sources; `level_agreement` **2/2 -> 3/3**, confidence 1.0 |
| `references_json` | `also_known_as += ["です"]`, `level_sources += {tanos: n5}` |
| `forms_json` | nothing to add: `{です}` ⊂ `{だ, です}` |
| `register_json` | nothing to add: `{polite}` ⊂ `{plain, polite}` |
| `nuance_tags_json` | nothing to add: `{politeness}` already carried |
| `formation_steps_json` | nothing to add: every loser variant matches a survivor variant on (base, step chain) |
| `structure_pattern` | `です` is already inside `だ / です` (compared with `～` and spaces normalised away) |
| `register` | `polite` is carried by the survivor's `register_json` list |

Salvaged, not written (10 fields, verbatim in the JSON ledger): `label`, `explanation`, `formation`,
`nuance` and `form_meanings`, each in pt-BR and en. `gp`'s explanation and the copula-specific nuance
block ("です não é verbo de ação…") are the substantive ones — a teacher folds them in.

### `gram:gp-152` -> `gram:te-hoshii`

| column | action |
|---|---|
| `register_json` | appended `plain` -> `[casual, colloquial, plain]` |
| `level_sources` | merged `tanos: n4` -> 3 sources; `level_agreement` **2/2 -> 3/3**, confidence 1.0 |
| `references_json` | `also_known_as += ["てほしい"]`, `level_sources += {tanos: n4}` |
| `formation_steps_json` | **appended 1 variant** — the negative build `行かないでほしい`, which `te-hoshii` did not carry |
| `forms_json` / `usage_contexts_json` / `nuance_tags_json` | nothing to add |
| `structure_pattern` | `～てほしい` is already inside `てほしい` |

Salvaged, not written (11 fields): the same four prose fields in both locales, `form_meanings` in
both locales, and the scalar `register = neutral` (the survivor's own value is different and picking
between them is authoring).

`refused` is empty for both merges: nothing was declined for widening an enum or for tripping
`validate_grammar_formation`.

---

## 3. Reference counts re-pointed, against the analyst's 840 / 591

The 840 and 591 in `APP_PLAN.md` are `grammar_identity_merges.md` §3.3's grand totals across all
zones. They break down like this, with what W08 actually moved:

| zone | `gp` | `gp-152` | moved by W08? |
|---|---:|---:|---|
| live source-of-truth (`corpus/`, `course/`, `design/`) | 298 | 180 | **yes, all but 1** |
| `prototype/app/data/*.json` (mirror) | 292 | 169 | no — re-synced separately, see §5 |
| `archive/course-pre-renumber-2026-06-26/**` | 192 | 155 | no — frozen by design |
| `research/**` (notes, patch queues, QA inputs) | 58 | 87 | authoring source only (2 + 2 edges); the rest is history |
| **grand total** | **840** | **591** | |

Measured on the export produced from the migrated DB, against a control export from an unmigrated
copy of the same DB (identity edges only, counted the way §0 of the report counts them):

| zone | `gp` | `gp-152` | `da-desu` | `te-hoshii` |
|---|---|---|---|---|
| `course/**/lesson-*.json` | 283 -> **0** | 159 -> **0** | 283 -> 283 | 159 -> 159 |
| `course/**/topic.json` | 1 -> 0 | 1 -> 0 | 1 -> 1 | 1 -> 1 |
| `course/outline.json` + manifest | 2 -> 0 | 2 -> 0 | 2 -> 2 | 2 -> 2 |
| `corpus/grammar/n*.json` (the record itself) | 2 -> 0 | 2 -> 0 | 2 -> 2 | 2 -> 2 |
| `corpus/capabilities/registry.json` | 1 -> 0 | 1 -> 0 | 1 -> 1 | 1 -> 1 |
| `corpus/families/families.json` | 2 -> 0 | 2 -> 0 | 2 -> 2 | 2 -> **4** |
| `corpus/sentences/bank.json` | 6 -> 0 | 10 -> 0 | 11 -> 11 | 7 -> **17** |
| `design/grammar_placement.json` | 1 -> **1** | 1 -> **1** | 1 -> 1 | 1 -> 1 |
| `corpus/grammar_deprecated.json` (new) | 0 -> 1 | 0 -> 1 | 0 -> 1 | 0 -> 1 |
| `research/derived/lessons/*.json` | 2 -> 0 | 2 -> 0 | 1 -> 2 | 3 -> 4 |
| `research/derived/repairs/*.json` | 0 -> 0 | 4 -> **4** | 0 -> 0 | 0 -> 0 |

`gp`'s live subtotal reproduces the report exactly: 283+1+2+2+1+2+6+1 = **298**. `gp-152` measures
**178**, not the report's 180: the two `course/speak/**` pattern references the report counted are
not in today's tree — the speaking layer was rebuilt since it was written.

**297 of 298** live references to `gp` and **177 of 178** to `gp-152` now resolve to the survivor.
The one that stays in each case is `design/grammar_placement.json` (§5). Everything the two records
carried is now on the survivors: `te-hoshii` went from 7 to 17 sentence edges and from 1 to 2
families, `da-desu` kept its 11 (all six of `gp`'s were already shared).

Edges moved inside the index:

| table | `gp` -> `da-desu` | `gp-152` -> `te-hoshii` |
|---|---|---|
| `sentence_grammar` | 0 re-pointed, 6 dropped as duplicate | 5 re-pointed, 0 dropped |
| `sentence.tags` | 0 | 5 rewritten |
| `lesson_unlocks` | 1 dropped (same lesson already unlocked the survivor) | 1 dropped |
| `lesson_introduces` | 1 dropped | 1 dropped |
| `family_member` | 1 dropped (`grp:gram-n5-desu-wa`, survivor already a member) | 1 re-pointed (`grp:gram-n4-volitivo`) |
| `exercise_item` | 1 re-pointed | 1 re-pointed |
| `grammar_related` | 0 | 0 |
| lesson body addresses (`localized_text`) | 6 across 3 lessons | 2 in `les:n4-dar-receber-03` |
| `lesson.cumulative_known_set` | 281 lessons | 157 lessons |

`cumulative_known_set` is re-derived by `export_course.py`, so the published course was never at
risk; the stored column is fixed because `ingest/build_readings.py` and `ingest/mine_n3_targets.py`
gate their candidate selection on it, and a retired address sitting there would let a later builder
count it as known.

Authoring source (`research/derived/lessons/`, 4 files, 7 insertions / 15 deletions):

```
n4-dar-receber-03.json   unlocks: dropped duplicate gram:gp-152 (gram:te-hoshii already there)
                         exercises[1].item_refs: gp-152 -> te-hoshii
                         body: 2x ref="gram:gp-152" -> "gram:te-hoshii"
n5-desu-wa-01.json       unlocks: dropped duplicate gram:gp (gram:da-desu already there)
                         exercises[2].item_refs: gp -> da-desu
                         body: 3x ref="gram:gp" -> "gram:da-desu"
n5-adjetivos-03.json     body: 2x ref="gram:gp" -> "gram:da-desu"
n5-verbos-03.json        body: 1x ref="gram:gp" -> "gram:da-desu"
```

Only addresses moved. Blank every grammar address in both the committed and the rewritten file and
the two are byte-identical, in all four files — no prose, structure or non-grammar reference was
touched, and the files keep their own indent and LF endings.

---

## 4. Gates, on a copy

The whole thing was applied to a copy of the repository and its index first, exported there, and
gated. Nothing was exported in the real tree.

```
validate_contracts        FAIL (not W08 — see §5)
validate_unlock_ledger    OK   322 lessons, 4135 unlocks, 4135 distinct refs
validate_srs_decks        OK   4131 cards over 322 lessons, 12 decks, 0 FAIL
validate_graph_edges      OK   554956 edges over 8 checks
validate_stable_addresses OK   544 files, 56568 integer FKs
validate_speaking_path    OK   72 units, 432 phrases, 0 FAIL, 1 pre-existing warn
validate_exam_banks       OK   6048 items in 40 banks
validate_repairs_applied  OK   1478 rows replayed clean, 21 checked skips, 0 FAIL
validate_course_chain     OK   544 published JSON, 9 generated-not-schema'd, 0 FAIL
```

`validate_repairs_applied` gained a third marked skip class. `grammar_record_repairs.json` rows
19-22 address `gp-152`, whose address the export no longer carries; they are now **retired**, and the
retirement is asserted, not assumed — `corpus/grammar_deprecated.json` must not point the key at
itself and its survivor must be a record the export actually carries, or the row fails
`merged-away-redirect-broken`. The claim is retired rather than transferred: `te-hoshii`'s prose was
authored separately and never carried the build-commentary leak that repair removed, so re-asserting
the repaired text against the survivor would be false. Skips went 17 -> 21.

---

## 5. What did NOT move, and why

* **`design/grammar_placement.json`** keeps both rows. It is a hand-maintained design input naming
  the topic a grammar KEY is placed in, and the record still exists — deprecated, but present, and
  still placed in that topic. Deleting the row would make `ingest/place_items.py` leave the record
  unplaced on a rebuild: a different corpus, not a cleaner one.
* **`research/derived/repairs/*.json`** keeps its four `gp-152` rows. A repair table is the
  historical record of what one campaign changed and a later migration does not get to rewrite it.
  The redirect retires the claim instead (§4).
* **`corpus/**` and `course/**`** were not hand-edited. They are regenerated by the exporters, and
  CLAUDE.md's data-format rule forbids editing them here.
* **`prototype/app/data/*.json`** (292 / 169 references) is a mirror, guarded by
  `validate_prototype_sync.py`. It has to be re-synced after the export; W08 did not touch it.
* **`archive/**`** (192 / 155) is frozen by convention.
* **`validate_contracts` fails, and not because of this merge.** Re-exporting surfaces 36
  `Additional properties are not allowed ('needs_review' was unexpected)` violations on `family`,
  `kanji` and `vocab` — the in-flight W05/W06 `needs_review` / `review_status` work in
  `export_corpus.py`, whose schemas have not landed. Proved by a control: an export from an
  **unmigrated** copy of the same index produces a byte-identical failure list. `grammar` (494
  records), `capability`, `sentence`, `lesson`, `topic` and `course` all pass.
* **Eight more duplicate pairs are ready and were not merged** (§1). That is a deliberate stop, not
  an oversight.

---

## 6. What the orchestrator's export will change

The merge is in the index and in the authoring source; `corpus/` and `course/` are still pre-merge.
Isolating W08's share by diffing an export from the migrated index against one from an unmigrated
copy of it, the next export will rewrite:

**`corpus/` — 9 files changed, 1 added**

```
corpus/grammar/n5.json                  150 records (gp dropped)
corpus/grammar/n4.json                  212 records (gp-152 dropped) — grammar total 496 -> 494
corpus/grammar/INDEX.md                 index rows + the deprecated count line
corpus/grammar_deprecated.json          NEW  {"gram:gp": "gram:da-desu", "gram:gp-152": "gram:te-hoshii"}
corpus/sentences/bank.json              11 sentence rows re-tagged / re-linked
corpus/families/families.json           grp:gram-n5-desu-wa loses a member; grp:gram-n4-volitivo swaps one
corpus/families/INDEX.md                membership counts
corpus/capabilities/registry.json       cap:topic:n5-desu-wa drops "gp"; cap:topic:n4-dar-receber drops "gp-152"
corpus/capabilities/lesson_map.json     the two lessons' capability sets
corpus/INDEX.md                         counts
```

**`course/` — 293 files**: 285 `lesson-*.json` (`cumulative_known_set.grammar[]`, plus `unlocks[]`,
`srs.introduces_cards[]` and the rendered body in the two introducing lessons),
`n5/topic-07-desu-wa/topic.json`, `n4/topic-27-dar-receber/topic.json`, `n5/course.json`,
`n4/course.json`, `course/outline.json`, and three `INDEX.md`.

`corpus/grammar_deprecated.json` is registered in `design/generated_artifacts.json`, and
`validate_course_chain` reads that registration as a promise: **until the export runs it reports one
failure**, `lists corpus/grammar_deprecated.json, which is not published — a stale exemption is a
failure`. That is the intended hand-off shape, and it clears on the first export.

The same export will also rewrite the `kanji/` and `vocab/` registries for the other lanes in
flight; those changes are not W08's.

---

## 7. Reproducing and re-proving

```
scripts/migrate_grammar_merge.py            dry run — the whole plan, writes nothing
scripts/migrate_grammar_merge.py --check    verifies the merge IS applied (DB + authoring source)
scripts/migrate_grammar_merge.py --apply    idempotent; a second run reads deprecated_by and stops
scripts/migrate_grammar_merge.py --db PATH --root PATH    target a scratch index / checkout
```

Registered as step 113 of `research/derived/rebuild_manifest.json`, enabled, last in the chain:
every earlier step that writes `grammar_point`, `sentence_grammar`, `family_member` or a lesson body
would otherwise re-introduce the loser's edges after the merge. `MERGES[].expect` is an exact
precondition measured against whatever graph the rebuild produced — 6 sentence links and 281
cumulative sets for `gp`, 5 and 157 for `gp-152`, and so on — so a rebuild that produced a different
shape refuses here instead of merging blind.
