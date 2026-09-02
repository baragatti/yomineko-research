# Daily study system — FSRS memory track + capability skill track (SPEC, 2026-07-06)

> Roadmap D research spec (design/study_system_roadmap.md §D). **Design only** — this corpus run ships data;
> the engine is app-side. The corpus artifacts it consumes already exist: `corpus/capabilities/registry.json`
> + `lesson_map.json` (74 capabilities), `corpus/exam_banks/` (5,013+ typed items), lesson
> `cumulative_known_set`, and the SRS-card derivation from lesson unlocks.

## 1. Memory track (PRIMARY) — FSRS v6
- **Algorithm:** FSRS v6 (21-parameter DSR-family model), MIT-licensed, maintained by
  [open-spaced-repetition](https://github.com/open-spaced-repetition/awesome-fsrs). Use
  [`ts-fsrs`](https://github.com/open-spaced-repetition/ts-fsrs) (TypeScript, MIT — fits the React Router
  app; runtime scheduling only). Parameter optimization (`@open-spaced-repetition/binding` / fsrs-rs) is an
  OFFLINE batch job — run monthly per user once they have ≥ ~400 reviews; default parameters until then.
- **Cards:** derived from lesson unlocks (existing derivation): ~~vocab (recognition: JP→pt; later production)
  and kanji (character→reading/meaning). Kana handled by the skill track, not FSRS cards.~~
  **[stale — corrected 2026-09-02, see §7]** Four sources ship, not two: vocab 2,946 · kanji 634 ·
  grammar 496 · kana 57. Kana **is** an FSRS card.
- **Settings:** desired retention 0.90 (learner-adjustable 0.80–0.95); new-card seeding = lesson completion
  (cards enter the queue when their lesson is finished); ~~daily new-card cap default 15~~
  **[stale — corrected 2026-09-02, see §7: the default is 10]**; review cap default 120
  with overflow spill to tomorrow (FSRS tolerates late reviews natively via its stability/retrievability math).
- **Grades:** Again / Hard / Good / Easy (standard FSRS 4-grade input).

## 2. Skill track (SECONDARY, bounded) — per-capability ease
Purpose (owner): keep reading/phrase-forming sharp — *teaching, not memorizing*. Not per-item memory:
**per-capability proficiency** over the 74 registry capabilities.
- **State per (user, capability):** `ease` in [1.3, 3.0] (start 2.2), `due_at`, `streak`.
- **Update (SM-2-flavored, right/wrong only):** right → ease += 0.06 (cap 3.0), interval = round(ease^streak)
  days (cap 21), streak += 1. wrong → ease −= 0.25 (floor 1.3), streak = 0, interval = 1 day. Never zeroed:
  even ease-3.0 capabilities resurface ≤ every 21 days.
- **Exercise source:** existing banks filtered by capability→grammar_keys → exam-bank items (grammar_form,
  context_fill, sentence_order) + lesson exercise types (particle_choice, cloze, matching) + conjugation drills
  (conjugation table). Item picked uniformly at random within the capability, respecting the user's
  `cumulative_known_set` (study-mode filter) and a per-item no-repeat window of 10 sessions.
- **Signal:** binary right/wrong per capability (also fed by exam-simulator section results, weighted 1:1).

## 3. Daily queue (built at first login; refreshed after lessons)
1. `due_memory` = FSRS due cards (overdue first, then by retrievability ascending).
2. `due_skills` = capabilities with due_at ≤ today, ordered by ease ascending (weakest first).
3. **Time budget:** target session = 15 min default (user-set 5–30). Estimate 6 s/review card, 25 s/skill
   exercise. Fill: memory first until min(cards, 80% of budget), then skills into the remaining 20%
   (minimum 2, maximum 8 skill exercises/day). Leftover skills roll to tomorrow (they have intervals anyway).
4. **Refresh triggers:** first login of the local day (cheap: two indexed queries + in-memory sort — O(due)
   per user, no batch job needed) and after completing a lesson (new cards + possibly new capabilities).
5. **Order within session:** interleave — blocks of ~10 memory cards, then 1–2 skill exercises (interleaving
   sustains attention; skill items act as active breaks).

## 4. Data model (app-side)
> **Superseded 2026-09-02.** This sketch is kept for the record; the binding contract is
> [`design/user_state.md`](user_state.md) and the schemas under `contracts/user_state/`. The two lines
> struck through below are not merely imprecise, they are wrong — see §7.

- `srs_card(user, item_ref, fsrs_state: stability, difficulty, due, last_review, reps, lapses)`
- `skill_state(user, capability_id, ease, streak, due_at, last_result)`
- ~~`review_log(user, ref, grade, elapsed, ts)`~~ — the FSRS optimizer's input; append-only.
  **[wrong granularity — corrected 2026-09-02, see §7]** The log is keyed on `card_id`, never on the
  item: one item fans out to up to five card kinds (4,133 items → 9,453 card instances), so an
  item-keyed log merges a recognition answer with a handwriting answer into one memory trace.
- ~~Stable refs: `vocab:<headword>`, `kanji:<char>`, `cap:<key>` — all already stable corpus IDs.~~
  **[stale and dangerous — corrected 2026-09-02, see §7]** A headword is not an address: 93 headwords
  are shared by 193 records. Every card `item` is a published slug — `vocab:1580640`, not `vocab:人`.

## 5. Why this balance (research notes)
- FSRS is the battle-tested memory scheduler (outperforms SM-2 on log-loss/calibration in published
  benchmarks; native handling of late/early reviews; per-user optimization path). Keeping the skill track
  SM-2-flavored is deliberate: its signal is coarse (binary, capability-level), so a 21-parameter model would
  overfit noise; a bounded-ease ladder is robust, explainable, and cheap.
- Alternatives considered: Half-Life Regression (Duolingo) — needs rich per-feature logs we don't have at
  day 1; Leitner — too coarse for memory but its spirit survives in the skill ladder; pure-FSRS-for-skills —
  rejected (wrong granularity: capabilities aren't memories, they're skills; the exam feed would double-count).
- The 80/20 budget keeps the owner's constraint: FSRS remains the main course; skills are a controlled extra
  that can never crowd out reviews (hard caps both ways).

## 6. Open decisions (owner, at app-build time)
- Retention default 0.90 vs 0.85 for a hobbyist audience (lower = fewer reviews/day).
- Whether exam-simulator results also create FSRS cards for MISSED vocab (recommended: yes, as "leeches").
- ~~Production cards (pt→JP typing) — phase 2 of the app; recognition-only at launch.~~
  **[stale — closed 2026-09-02, see §7]** All 4,133 cards already declare `production`. It ships at
  launch; it is not a phase-2 decision any more.

---

## 7. Decision D6 and the 2026-09-02 reconciliation against the export

Dated entry, **2026-09-02**, authored for **W26** of `research/reports/APP_PLAN.md`. Nothing above is
deleted; the claims this entry overturns are struck through in place so a reader who remembers the old
rule finds out what happened to it. The binding contract is [`design/user_state.md`](user_state.md);
the same entry is recorded in [`design/learning_science.md`](learning_science.md) §7.1 item 9.

**Owner decision D6 — kana in FSRS:** *keep*; **one glyph per card** (`APP_PLAN` §4).

**The decision, in one line:** kana cards stay FSRS cards, and W29 splits the 57 family cards into 211
one-glyph cards; production cards ship at launch, not in phase 2.

### 7.1 What the data says, measured

| claim | where | what the export holds | verdict |
|---|---|---|---|
| "Kana handled by the skill track, **not FSRS cards**" | §1 above | **57 kana cards**: `deck:kana-hiragana` 28 + `deck:kana-katakana` 29, each with `recognition` + `production` + `handwriting`. Exported, and hard-gated by `validate_srs_decks`. | **doc stale** |
| "recognition-only at launch; production cards are phase 2" | §6 above | **All 4,133 cards declare `production`.** Also 4,133 `recognition`, 691 `handwriting`, 496 `cloze`, 0 `listening`. | **doc stale** |
| "ships no FSRS cards for kana (skill track) and no production cards at launch" | `learning_science.md` R75, *Why* | Repeats both stale claims as a premise. R75's own rule — reward decay past the first correct retrieval, and a 20% cap on reward from items with retrievability > 0.95 — is **unaffected** and stands. | **premise stale, rule stands** |
| "Cards: derived from lesson unlocks: **vocab** and **kanji**" | §1 above | vocab 2,946 · kanji 634 · **grammar 496** · **kana 57**. Grammar decks exist at all three levels. | **doc incomplete** |
| "Stable refs: `vocab:<headword>`, `kanji:<char>`, `cap:<key>`" | §4 above | Every card `item` is a published slug: `vocab:1580640`, not `vocab:人`. A headword is **not** an address — 93 headwords are shared by 193 records (`contracts/README.md`). | **doc stale and dangerous** |
| "`review_log(user, ref, grade, elapsed, ts)`" keyed on the *item* | §4 above | Each item fans out to up to 5 kinds; 4,133 items → **9,453 card instances**. An item-keyed log merges a recognition answer with a handwriting answer into one memory trace. | **wrong granularity** |
| "daily new-card cap default 15" | §1 above | `design/unlock_enums.json#_deck_defaults.new_per_day` = **10**. Two design docs, two numbers. | **conflict → 10 wins** |
| retention band 0.80–0.95 | §1 above, `unlock_enums.json` | Agree. `srs_fsrs` §5 proposed widening to 0.70–0.97. | **rejected, band stays 0.80–0.95** |

The rule applied throughout: **the data is right and the docs are stale.** The card set is exported,
gated by `validate_srs_decks`, and derived with zero drift from the unlock ledger; the two design docs
are prose that nothing checks. Where the two disagree, the checked artifact wins. The one exception is
`new_per_day`, where both sources are prose — there `unlock_enums.json` wins because it is the file the
loader and the validators already import.

### 7.2 What follows

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
