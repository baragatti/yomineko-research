# `user_state` — the logical contract for everything the learner owns

Authored 2026-09-02 for **W26** of [`research/reports/APP_PLAN.md`](../research/reports/APP_PLAN.md).
Closes readiness gaps **G1** (`platform_contract_i18n`: no user-state contract), **G5** and **G10**
(`srs_fsrs`: no card entity, review-log schema is prose only) and **G12** (`tests_exercises`: no state
model for streak / mastery / attempts).

This file is the **authority** for the seven runtime entities. The schemas under
[`contracts/user_state/`](../contracts/user_state/) are hand-authored against it and every `enum` in
them carries `x-vocabulary: {"owner": "design", "source": "design/user_state.md#…"}`, so a value set
here can only widen by an edit to this document — the same rule the corpus contracts follow
([`contracts/README.md`](../contracts/README.md) → *Where an `enum` is allowed to come from*).

**Logical, not physical.** Field names, types, keys and cardinalities are decided here. Table layout,
indexes, partitioning and the database product wait on owner decision **D8** (`APP_PLAN` §4, delivered
by W43). Nothing below assumes a relational store; it assumes documents with primary keys, which every
candidate can express.

**The corpus owes none of this.** No record under `corpus/` or `course/` changes because of this file.
These entities carry **no committed records** — they are minted at runtime, per learner — which is why
they enter `contracts/manifest.json` as a new entity **class**, `runtime` (§9).

---

## 1. The seven entities at a glance

| entity | one row per | primary key | grows with |
|---|---|---|---|
| `user` | account | `user_id` | learners |
| `card` | (user, unlocked item, card kind) | `card_id` | learners × 9,453 card instances |
| `review_log` | one graded answer | `log_id` | reviews — append-only, never mutated |
| `lesson_progress` | (user, lesson) | `(user_id, lesson)` | learners × 322 lessons |
| `exam_attempt` | (user, level, attempt no.) | `attempt_id` | simulated papers sat |
| `feature_state` | (user, feature) | `(user_id, feature)` | learners × 16 features |
| `skill_state` | (user, capability) | `(user_id, capability)` | learners × 74 capabilities |

`card` is derived state and rebuildable; `review_log` is the durable truth. That split is deliberate
and §3 says why.

## 2. Addressing

Runtime ids follow the corpus rule — a lowercase namespace, a colon, an identifier with no whitespace
(`common.schema.json#/$defs/StableId`) — and add three namespaces the corpus does not use:

| namespace | shape | owns |
|---|---|---|
| `usr` | `usr:<opaque>` | one account. Opaque on purpose: never an email, never a name. |
| `att` | `att:<user opaque>-<level>-<attempt no.>` | one exam attempt. |
| `rev` | `rev:<opaque>` | one review-log row. |

`card` has no namespace of its own. Its id is **composed** of the ids that already exist, so no counter
and no server round-trip is needed to name a card:

```
card_id = f"{user_id}:{deck}:{item}:{kind}"

  usr:7f3a91:deck:vocab-n5:vocab:1580640:recognition
  usr:7f3a91:deck:kana-hiragana:kana:hiragana-a:handwriting
  usr:7f3a91:deck:grammar-n4:gram:te-hoshii:cloze
```

**It parses back deterministically**: exactly seven colon-separated segments, because `user_id`, `deck`
and `item` are each exactly two segments and `kind` is one. No corpus stable id contains a second colon
(verified across `corpus/**` — 0 of 51,918 records), and the schema forbids a colon inside `<opaque>`
and inside `kind`, so the split is total: `usr`, opaque, `deck`, deck key, item namespace, item id,
kind.

**The cost of putting `deck` in the key, stated once.** Deck filing follows the *lesson's* level, not
the item's, and 23 cards already sit in a deck whose level differs from the item's own corpus level
(`srs_fsrs` §2.3). If a card were ever refiled — a lesson moving between levels — its `card_id` would
change and its FSRS history would be orphaned. Refiling is therefore a **migration**, not an edit:
rewrite the `card_id` on the card *and* on every `review_log` row that points at it, in one
transaction. The alternative (`{user}:{item}:{kind}`, with `deck` as a mutable column) makes refiling
free but loses the property that a card's queue, caps and learner-facing surface are all readable from
its address alone. W26 takes the composed key on the owner's instruction; this paragraph is the record
of what it buys and what it costs.

## 3. What FSRS-6 actually needs, and why `card` is a cache

FSRS-6 is a 21-parameter DSR model. Its two runtime types, in both reference implementations
([`py-fsrs`](https://github.com/open-spaced-repetition/py-fsrs),
[`ts-fsrs`](https://github.com/open-spaced-repetition/ts-fsrs), MIT), are:

* **`Card`** — `card_id`, `state`, `step`, `stability`, `difficulty`, `due`, `last_review`.
* **`ReviewLog`** — `card_id`, `rating`, `review_datetime`, `review_duration`.

`Scheduler.review_card(card, rating, review_datetime)` returns the next `Card` plus one `ReviewLog`.
The optimizer trains on nothing but the per-card review history — the ordered
`(rating, Δt_since_previous_review)` sequence — and emits a weight vector.

So, per card, **the algorithm needs a stable id and a history and nothing else**. It has no notion of
level, deck, frequency, prerequisite, lesson, or item content; nothing in either library's models
reaches into corpus content. Everything else on `card` below exists for the *app* — queue building,
caps, the learner-facing "N4 kanji" surface, leech triage — not for the scheduler.

Two consequences the schemas encode:

1. **`review_log` is the durable truth; `card` is a version-tagged derived cache.** Every field of
   `card` except its id, its deck/item/kind and the learner's own suspend/bury flags can be recomputed
   by replaying that card's log through a scheduler. Storing `fsrs_version` and `params_version` on the
   card is what turns *FSRS-6 → FSRS-7*, or a re-optimized weight vector, into a **replay** rather than
   a schema migration.
2. **`review_log` is append-only.** Never updated, never deleted. A card can be deleted (content
   retired); its log rows are kept and marked orphaned rather than removed, because the optimizer's
   training set is the only asset here that cannot be regenerated.

## 4. `user`

One row per account. The scheduler settings live **inside** `user` rather than in a separate
`user_scheduler` row (as `srs_fsrs` §5 sketched): they are one-to-one with the account, they are read
on every queue build, and a second table buys nothing at this size.

| field | type | notes |
|---|---|---|
| `user_id` | `usr:<opaque>` | The only identifier that appears anywhere else in this model. |
| `created_at` | timestamp (UTC) | |
| `locale` | `Locale` | Interface language. `pt-BR` is the only one authored (`design/i18n.md`). |
| `timezone` | IANA tz name | The daily queue rolls over on the learner's local day, not on UTC. |
| `display_name` | string, optional | Learner-set. Not an identity. |
| `scheduler.desired_retention` | number, default **0.90** | Band **0.80–0.95** — `design/unlock_enums.json#_deck_defaults.retention_band`, which is the authority. `srs_fsrs` §5 proposed 0.70–0.97; rejected, see §10.2. |
| `scheduler.params` | 21 numbers, or null | The learner's optimized FSRS-6 weights. `null` = ship defaults. Optimize offline, monthly, once the learner has ≳400 reviews. |
| `scheduler.params_trained_at` | timestamp, nullable | |
| `scheduler.reviews_at_training` | integer, nullable | The sample size behind `params`. A weight vector with no sample size cannot be audited. |
| `scheduler.fsrs_version` | `fsrs-6` | Vocabulary owner: this document. |
| `scheduler.learning_steps` | minutes[], optional | |
| `scheduler.daily_new_cap` | integer, default **10** | `unlock_enums.json#_deck_defaults.new_per_day`. See §10.1 — `srs_design.md` §1 said 15 and was wrong. |
| `scheduler.daily_review_cap` | integer, default **120** | Overflow spills to tomorrow; FSRS handles late reviews natively. |
| `session.target_minutes` | integer, default **15**, range 5–30 | `srs_design.md` §3. |
| `entitlement` | enum `free` \| `paid` \| `trial` \| `comp` | The corpus is private paid content. Vocabulary owner: this document. |

## 5. `card`

**One row per (user, unlocked item, card kind).** A card is minted when the lesson that unlocks its
item is completed (§6), from that lesson's `srs.introduces_cards[]` entry — `{deck, item, card_types}`
— fanned out one row per entry in `card_types`. The derivation is total and mechanical: 4,133 cards
over 322 lessons, 9,453 card instances, no item enrolled twice anywhere (`srs_fsrs` §2.1–2.2).

| field | type | notes |
|---|---|---|
| `card_id` | see §2 | |
| `user_id` | `usr:` id | Redundant with the key's first two segments, stored for indexing. |
| `deck` | `deck:` id | `design/unlock_enums.json#deck`. A deck's `level` is a **curriculum position, not a JLPT claim** about its contents. |
| `item` | corpus `StableId` | `vocab:` / `kanji:` / `gram:` / `kana:` today; `sent:` when `deck:phrases` is populated (W30). |
| `kind` | `recognition` \| `production` \| `listening` \| `handwriting` \| `cloze` | `design/unlock_enums.json#card_type`. |
| `cloze_target` | `<sentence id>#<token index>`, required when `kind = cloze` | **Required, not optional.** Re-picking the sentence at review time silently changes the fact being tested, and a card whose content moves is not one memory fact — its difficulty and stability estimates become noise. 496 cloze cards exist; 17 grammar points have no sentence to blank and must be authored before those cards can render (W28). |
| `introduced_by` | `les:` id | Which lesson minted it. The route a leech takes back to remediation. |
| `state` | `new` \| `learning` \| `review` \| `relearning` | FSRS-6 card state. Neutral English; the learner-facing labels are pt-BR content, not enum values. |
| `step` | integer, nullable | Position in the learning/relearning steps. Null outside those states. |
| `stability` | number > 0, nullable | *S*, in days. Null while `state = new`. |
| `difficulty` | number in [1, 10], nullable | *D*. Null while `state = new`. |
| `due` | timestamp | |
| `last_review` | timestamp, nullable | |
| `reps` | integer ≥ 0 | UX only — not an FSRS input. |
| `lapses` | integer ≥ 0 | UX only, plus it drives the R33 furigana fade. |
| `suspended_at` | timestamp, nullable | Learner or leech rule took it out of the queue indefinitely. |
| `buried_until` | timestamp, nullable | Out of the queue for a bounded time (sibling burying). |
| `leech_state` | `none` \| `flagged` \| `suspended` | The Anki-grade retention hook. Absent from every prior design doc; `srs_design.md` §6 leaves leeches as an open question and this is the field that answers it. |
| `tags` | string[] | Corpus card tags (W28) plus learner-added. What a learner filters, suspends and buries by. |
| `fsrs_version` | `fsrs-6` | Which algorithm produced the cached D/S/due. |
| `params_version` | string | Which weight vector produced them. A card whose `params_version` is behind the user's is stale, not wrong — recompute lazily on next review. |

`state`, `step`, `stability`, `difficulty`, `due` and `last_review` are the FSRS `Card` (§3). Everything
above and below that block is app state.

## 6. `lesson_progress`

One row per (user, lesson). 322 lessons.

| field | type | notes |
|---|---|---|
| `user_id`, `lesson` | key | `lesson` is a `les:` id. |
| `status` | `not_started` \| `opened` \| `completed` | `opened_at` and `completed_at` carry the timestamps; the enum is what a query filters on. |
| `opened_at`, `completed_at` | timestamps, nullable | |
| `exercises_total`, `exercises_correct`, `exercises_attempted` | integers | Straight counts over the lesson's own exercise set. |
| `score` | number in [0, 1], nullable | `exercises_correct / exercises_attempted` at completion. Null until then. |
| `attempts` | integer ≥ 1 | A lesson may be re-sat. |
| `cards_seeded` | boolean | Whether completion minted this lesson's cards. **False after a successful test-out** — passing a test-out marks the words known *without* seeding them as new FSRS cards (`learning_science.md` §4.5). Without this flag, "completed" and "carded" are indistinguishable and the daily new-card cap is spent on material the learner already knew. |
| `mastery` | object, see below | |

### 6.1 `mastery` — one evaluated verdict plus the parameters that produced it

```
mastery = {
  state:        "unknown" | "not_met" | "met",
  evaluated_at: timestamp | null,
  criterion:    "MASTERY_V1",          # names the parameter block below
  observed:     number | null          # the measured fraction, so a verdict is auditable
}
```

The **threshold is a parameter, not a constant baked into a query**, and it is **PENDING owner
decision D2** ("what 'lesson complete' means; placement policy"). Until D2 lands, `MASTERY_V1` is the
default and it is the only proposal with a citation behind it — `learning_science.md` §4.5, taken from
LingoDeer's test-out and WaniKani's mastery-gated unlocking, expressed against FSRS state as a query
rather than as new machinery:

| parameter | default | source |
|---|---|---|
| `retrieval_threshold` | **0.90** | `learning_science.md` §4.5 — "≥90% of the prior stage's words" |
| `min_interval_days` | **1** | ibid. — "reaching a first successful review at interval ≥1 day" |
| `scope` | `prior_stage_items` | ibid. The unit evaluated is the *stage's* items, not one lesson's. |
| `counts_kinds` | `["recognition"]` | Open. Whether production must also pass is exactly the recognition-vs-production question D6 settles for kana and D2 leaves open here. |

Three things D2 must decide, listed so nobody has to reconstruct them: (a) whether `completed`
requires `mastery.state = met` or the two stay independent (this contract keeps them independent —
`status` records what the learner did, `mastery` records what the data says); (b) whether placement
seeds cards (`cards_seeded` is the field that would record either answer); (c) whether the threshold
is global or per level. Changing any of them is a new `criterion` value — `MASTERY_V2` — and rows
carrying `MASTERY_V1` stay readable and comparable. That is the whole reason `criterion` is stored on
the row instead of assumed by the reader.

## 7. `exam_attempt`

One row per (user, level, attempt no.). **The seed is that triple**, per `design/exam_simulator.md` §5
— the same learner asking for the same attempt number at the same level gets the same paper, which is
what makes a support request answerable.

| field | type | notes |
|---|---|---|
| `attempt_id` | `att:<user opaque>-<level>-<attempt no.>` | Derivable from the seed; no counter needed. |
| `user_id`, `level`, `attempt_no` | key parts | `level` is `common#/$defs/Level`. `attempt_no` ≥ 1. |
| `seed` | string | The canonical serialization of `(user_id, level, attempt_no)` handed to the RNG. Stored rather than recomputed so a change to the serialization is visible instead of silently regenerating a different paper under an old attempt. |
| `seed_algorithm` | string, e.g. `paper-v1` | Item selection, option shuffle and section fill are all seeded (`exam_simulator.md` §5, items 1–3). When any of them changes, this value changes and old attempts stay reproducible under the old rule. |
| `started_at`, `submitted_at` | timestamps | `submitted_at` null = in progress. |
| `mode` | `full` \| `section` \| `study` | `study` is the known-set-filtered practice mode; its scores must never be reported as a paper. |
| `time_limit_seconds`, `elapsed_seconds` | integers | Against the verified timing table in `exam_simulator.md`. |
| `items[]` | see below | One entry per presented item, in presentation order. |
| `sections[]` | see below | One entry per section the paper contained. |
| `total_raw`, `total_possible` | integers | 1 point per item (`exam_simulator.md` §6). |
| `scaled` | object, nullable | `{score, max, pass_mark, sectional_minima_met}` — the scoring model landed in **W19** (`design/exam_scoring.md`) and fills this. It is a HOUSE APPROXIMATION, not a JLPT score: real scaled scores come from an unpublished IRT model and cannot be reproduced outside JEES, so what is stored is a linear map of raw section percent onto the official range. Still nullable, for an attempt that is in progress. |
| `passed` | boolean, nullable | Null until `scaled` exists, **and still null when a whole 得点区分 went untested** — a paper missing a scoring section has no pass/fail to report (`exam_scoring.md` §6). Pass is *both* the total pass mark and every sectional minimum. |

**`items[]`** — `{item: <exam item StableId>, section, position, presented_options[], answer_given, correct, correct_answer, response_ms}`. `presented_options[]` records the *shuffled* order actually shown, because
"the seed reproduces it" is a claim that should be checkable against what the learner saw.

**`sections[]`** — `{section, raw, possible, minimum_met}`. `section` is one of the fourteen declared in
`exam_simulator.md` (`kanji_reading`, `orthography`, `context_fill`, `grammar_form`, `sentence_order`,
`paraphrase`, `usage`, `text_grammar`, `reading_comp`, `listening_task`, `listening_point`,
`listening_gist`, `listening_say`, `listening_reply`) — the same fourteen the exam-bank id prefixes
name (`kr or cf gf so pp us tg rc lt lp lg ls lr`). Vocabulary owner: `design/exam_simulator.md`.
The five listening sections cannot appear in a paper until their items have audio.

The per-type breakdown feeds the capability tracker (`skill_state`, §8) weighted 1:1 with in-app
practice, per `srs_design.md` §2.

## 8. `skill_state`

One row per (user, capability). 74 capabilities in `corpus/capabilities/registry.json`. This is the
**skill track**, deliberately not FSRS: its signal is binary and capability-level, so a 21-parameter
model would fit noise (`srs_design.md` §5).

| field | type | notes |
|---|---|---|
| `user_id`, `capability` | key | `capability` is a `cap:` id. |
| `ease` | number in **[1.3, 3.0]**, start **2.2** | Right → `+0.06` (cap 3.0). Wrong → `−0.25` (floor 1.3). |
| `streak` | integer ≥ 0 | Right → `+1`, interval `round(ease^streak)` days, capped at 21. Wrong → `0`, interval 1 day. |
| `due_at` | timestamp | Never zeroed: even an ease-3.0 capability resurfaces at least every 21 days. |
| `last_result` | `correct` \| `incorrect` \| null | |
| `last_reviewed_at` | timestamp, nullable | |
| `reps`, `correct` | integers ≥ 0 | The denominator behind any "you are weak at X" claim. |
| `recent_items` | `StableId[]`, ≤ 10 | The no-repeat window: an item picked for this capability may not return for 10 sessions (`srs_design.md` §2). Bounded, so it is state and not a log. |

## 9. `feature_state`

One row per (user, feature). Sixteen features are declared in `design/unlock_enums.json#feature`, and
that document remains the vocabulary owner.

| field | type | notes |
|---|---|---|
| `user_id`, `feature` | key | `feature` is a `feat:` id. |
| `unlocked` | boolean | |
| `unlocked_at` | timestamp, nullable | |
| `unlocked_by` | `les:` id, or null | The lesson whose `feature_unlocks` granted it. Null when `source` is not `lesson`. |
| `source` | `lesson` \| `default` \| `entitlement` \| `admin` | Vocabulary owner: this document. |
| `enabled` | boolean | The learner's own toggle, separate from the unlock. `furigana-toggle` and `romaji-toggle` are settings; being *allowed* to toggle and being *toggled on* are different facts and one boolean cannot hold both. |

`source` is not decoration. **Only 4 of the 16 features are unlocked by any lesson today** —
`srs-reviews`, `conjugation-drill`, `jlpt-sim-n5`, `jlpt-sim-n4`, one lesson each; the other twelve are
reachable by no path in the course (readiness `platform_contract_i18n` G9, and `needs[]` is empty on all
322 lessons). A model with only `lesson` as a source would make those twelve permanently unreachable
and would encode today's gap as the contract. W-unit **G9** backfills the unlock graph; until it does,
`default` is how a feature can be on.

## 10. Reconciling `srs_design.md` and `learning_science.md` R75 against the exported data — decision D6

The two design docs and the shipped data disagreed. `srs_fsrs` G6/G10 found it, and W26 resolves it
under the owner's **D6 default: keep kana in FSRS, one glyph per card** (`APP_PLAN` §4).

**The decision, in one line:** *kana cards stay FSRS cards, and W29 splits the 57 family cards into 211
one-glyph cards; production cards ship at launch, not in phase 2.* The text below is recorded verbatim
as a dated entry in **both** `design/srs_design.md` §7 and `design/learning_science.md` §7.1 item 9 —
the stale claims are struck through and annotated, not deleted, so a reader who remembers the old rule
finds out what happened to it.

### 10.1 What the data says, measured

| claim | where | what the export holds | verdict |
|---|---|---|---|
| "Kana handled by the skill track, **not FSRS cards**" | `srs_design.md` §1 | **57 kana cards**: `deck:kana-hiragana` 28 + `deck:kana-katakana` 29, each with `recognition` + `production` + `handwriting`. Exported, and hard-gated by `validate_srs_decks`. | **doc stale** |
| "recognition-only at launch; production cards are phase 2" | `srs_design.md` §6 | **All 4,133 cards declare `production`.** Also 4,133 `recognition`, 691 `handwriting`, 496 `cloze`, 0 `listening`. | **doc stale** |
| "`srs_design.md` ships no FSRS cards for kana (skill track) and no production cards at launch" | `learning_science.md` R75, *Why* | Repeats both stale claims as a premise. R75's own rule — reward decay past the first correct retrieval, and a 20% cap on reward from items with retrievability > 0.95 — is **unaffected** and stands. | **premise stale, rule stands** |
| "Cards: derived from lesson unlocks: **vocab** and **kanji**" | `srs_design.md` §1 | vocab 2,946 · kanji 634 · **grammar 496** · **kana 57**. Grammar decks exist at all three levels. | **doc incomplete** |
| "Stable refs: `vocab:<headword>`, `kanji:<char>`, `cap:<key>`" | `srs_design.md` §4 | Every card `item` is a published slug: `vocab:1580640`, not `vocab:人`. A headword is **not** an address — 93 headwords are shared by 193 records (`contracts/README.md`). | **doc stale and dangerous** |
| "`review_log(user, ref, grade, elapsed, ts)`" keyed on the *item* | `srs_design.md` §4 | Each item fans out to up to 5 kinds; 4,133 items → **9,453 card instances**. An item-keyed log merges a recognition answer with a handwriting answer into one memory trace. | **wrong granularity** |
| "daily new-card cap default 15" | `srs_design.md` §1 | `design/unlock_enums.json#_deck_defaults.new_per_day` = **10**. Two design docs, two numbers. | **conflict → 10 wins** |
| retention band 0.80–0.95 | `srs_design.md` §1, `unlock_enums.json` | Agree. `srs_fsrs` §5 proposed widening to 0.70–0.97. | **rejected, band stays 0.80–0.95** |

The rule applied throughout: **the data is right and the docs are stale.** The card set is exported,
gated by `validate_srs_decks`, and derived with zero drift from the unlock ledger; the two design docs
are prose that nothing checks. Where the two disagree, the checked artifact wins. The one exception is
`new_per_day`, where both sources are prose — there `unlock_enums.json` wins because it is the file the
loader and the validators already import.

### 10.2 What follows for this contract

1. `card.kind` keeps all five values including `production` and `listening`; nothing in the schema
   marks production as phase 2.
2. `card.item` accepts `kana:` ids at **either** granularity — the family form `kana:hiragana-a` (57
   cards today) and the glyph form `kana:hiragana-あ` (211 glyph records already exist in
   `corpus/kana/`, and `validate_srs_decks` already accepts them as legal targets). W29 migrates 57 →
   211. The contract must validate both, because it has to hold across that migration; the *target
   state* is one glyph per card, and it is stated here rather than encoded as a pattern the migration
   would have to fight.
3. The migration is a **re-mint, not a rename**: `kana:hiragana-a` and `kana:hiragana-あ` are different
   memory facts, so the old card's history does not transfer to any of the five new cards. Splitting a
   conflated card is the one card-set change that must discard FSRS state rather than carry it, and
   pretending otherwise would poison D/S for 57 × 3 cards. Kana is the reason the minimum information
   principle is in `design/fsrs_integration.md` at all.
4. `desired_retention` band stays **0.80–0.95** (`unlock_enums.json`). The `srs_fsrs` §5 proposal of
   0.70–0.97 is rejected: 0.97 is above the point FSRS's own guidance calls counterproductive, and
   `unlock_enums.json` already says ">0.97 retention discouraged" — a band should not reach a value its
   own defaults block warns against.
5. `daily_new_cap` default is **10**.
6. `review_log` is keyed on `card_id`, never on the item.

**What is still the teacher's call, and is not settled here.** Whether kana *should* be in FSRS is a
pedagogy question; D6 is the owner's engineering default so that W29 can proceed and the app is not
blocked on it. If the teacher review reverses it, the change is deleting rows from
`srs.introduces_cards[]` for two decks — a content edit, not a schema change. Nothing in
`contracts/user_state/` has to move either way, which is the point of recording the decision here
instead of encoding it in the schema.

## 11. Retention, deletion, and what a runtime entity may not hold

* No entity here stores an email address, a password, a password hash, an IP, or any third-party
  identifier. `user_id` is opaque; `display_name` is learner-set and is not an identity. Authentication
  lives outside this contract and D8 decides where.
* `review_log` is append-only and survives card deletion (§3). It is the only training set for the
  optimizer and it cannot be regenerated.
* Deleting an account deletes `user`, `card`, `lesson_progress`, `exam_attempt`, `feature_state` and
  `skill_state` rows, and **anonymizes** `review_log` by dropping `user_id` and rewriting `card_id` to
  its non-user segments — the scheduling signal is kept, the person is not.
* Nothing here is exported, committed or shipped with the corpus. §12 is what enforces that.

## 12. Why these are `runtime` entities in the manifest

`contracts/manifest.json` catalogues an entity by where its records live. These seven have **no records
on disk and never will** — a `card` row exists only once a learner has one. Before W26 the manifest had
no way to say that: `validate_contracts.py` fails an entity whose glob matches zero records (correctly
— a stopped exporter and a moved directory both look like `0 records`), and
`validate_schema_generation_is_current.py` fails an entity that declares no glob at all.

So the manifest gains an entity **class**:

| class | `files` | `records` | means |
|---|---|---|---|
| `content` | a glob that matches | an exact count | committed JSON under `corpus/` or `course/`. 23 entities. |
| `runtime` | **`null`** | **`null`** | minted per learner at runtime. Contract only. 7 entities. |

The class is **declared** in each schema's `x-yomineko.class`, not inferred from an absent glob, and
the validators check the two against each other in both directions:

* a `runtime` entity that declares a `files` glob **fails** — in `validate_contracts.py` (its glob
  matches 0 records, the normal content failure) and in `validate_schema_generation_is_current.py`
  (class/glob contradiction), so a content entity whose exporter stopped cannot relabel itself
  `runtime` and go quiet;
* a `content` entity with no glob **fails**, where it used to print an advisory note and pass;
* a `runtime` entity is still schema-checked: it must compile as Draft 2020-12 and every `$ref` in it
  must resolve, which is what stops a contract nobody can validate against records from rotting
  unnoticed.

`build_schemas.py` never writes these files — all seven are in its `HANDWRITTEN` set, so a regeneration
cannot narrow them — and it fails if any of the seven is missing from `contracts/user_state/`, or if
one of their names ever appears in `contracts/_shapes.json` (which would mean records had been
committed for an entity that is contracted not to have any).

## 13. What W26 does not deliver

* **Physical schema** — tables, indexes, partitioning, the database product: **D8**, W43.
* **The mastery threshold as a settled number** — **D2** (§6.1). The parameter block is named and
  defaulted so that the app can be built and the decision can still be made.
* **Scaled JLPT scoring** — landed in W19; the model and its sourcing are `design/exam_scoring.md`.
  `exam_attempt.scaled` is filled, and labelled an approximation wherever it is shown. It stays
  nullable: an in-progress attempt has no score yet.
* **`listening` cards and listening sections** — blocked on audio (W35). The `kind` and the sections
  are in the contract; zero rows can legally exist.
* **Per-card tags and answer keys in the corpus** — W27/W28. `card.tags` is contracted; what fills it
  is a content campaign.
* **A validator over runtime records.** There are none to validate. What is enforced today is that the
  contracts exist, compile, resolve, and are honestly catalogued.
* **A `deck` entity.** W26's line in `APP_PLAN` §3 asks for "card and deck" as manifest entities; only
  `card` became one, deliberately. A deck is not learner state and it is not exported content either:
  the twelve decks are a **closed registry inside `design/unlock_enums.json`** (`deck`, `deck_registry`,
  `item_to_deck`, `_deck_defaults`), which is the file the loader and the validators already import, and
  `card.deck` is an enum generated from it and gated by `validate_srs_decks`. Cataloguing it as a
  `content` entity would be a lie — no glob under `corpus/` or `course/` matches it — and as a `runtime`
  entity it would be a per-learner table with the same twelve rows for every learner. The one genuinely
  per-learner deck fact, the scheduler settings, is on `user.scheduler` (§4). If decks ever become
  learner-editable (custom decks, per-deck FSRS presets), that is the moment a `deck` runtime entity is
  warranted; today it would be a row nobody writes.
