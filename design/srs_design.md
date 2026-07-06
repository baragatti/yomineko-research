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
- **Cards:** derived from lesson unlocks (existing derivation): vocab (recognition: JP→pt; later production)
  and kanji (character→reading/meaning). Kana handled by the skill track, not FSRS cards.
- **Settings:** desired retention 0.90 (learner-adjustable 0.80–0.95); new-card seeding = lesson completion
  (cards enter the queue when their lesson is finished); daily new-card cap default 15; review cap default 120
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
- `srs_card(user, item_ref, fsrs_state: stability, difficulty, due, last_review, reps, lapses)`
- `skill_state(user, capability_id, ease, streak, due_at, last_result)`
- `review_log(user, ref, grade, elapsed, ts)` — the FSRS optimizer's input; append-only.
- Stable refs: `vocab:<headword>`, `kanji:<char>`, `cap:<key>` — all already stable corpus IDs.

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
- Production cards (pt→JP typing) — phase 2 of the app; recognition-only at launch.
