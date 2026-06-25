# FSRS integration plan

> Engineering plan for the future SRS layer that consumes this corpus. The corpus build (this repo)
> ships data + courseware only; this document specifies how an app layer will mint review cards from
> corpus items (by stable ID), persist scheduling state, and run FSRS. Internal prose is English;
> learner-facing examples are pt-BR. The corpus was explicitly designed to feed this engine
> (frequency-ordered vocab, dependency-aware sequencing, confusable "families", stable IDs,
> "introduce -> spaced review" intent).

## What FSRS is

FSRS (Free Spaced Repetition Scheduler) is an open-source memory-model scheduler. It models each
card's memory with the **DSR three-component state** (from Wozniak / MaiMemo's DHP model):

- **D = Difficulty** in [1, 10]: how fast stability grows on a successful review (higher = slower).
- **S = Stability** in days: the interval at which retrievability drops to 90% (by definition
  R(t = S) = 0.9).
- **R = Retrievability** in [0, 1]: probability of recall right now.

The current forgetting curve is a **power function** (not exponential):
`R(t, S) = (1 + factor * t/S)^(-w20)` where `factor = 0.9^(-1/w20) - 1` so that R(S, S) = 90% always
holds, and w20 is the trainable decay (FSRS-6).

Scheduling is driven by **one knob: desired retention (DR)**, default **0.90**. Inverting the curve
gives the next interval; by construction interval == S when DR = 0.9. Raising DR shortens all
intervals (more reviews, less forgetting); lowering it lengthens them. DR is a per-deck/global
setting, NOT a trained weight. The Anki manual recommends keeping DR below 97% (above 90% workload
climbs fast; above 97% it can be overwhelming); the FSRS wiki gives 70%-97% as the reasonable range.

Update rules: ratings are **Again=1, Hard=2, Good=3, Easy=4**. Hard/Good/Easy all count as *success*
(only Again is a lapse), so Hard must be used as a passing grade, never as "fail." On success
`S' = S * SInc` with `SInc >= 1`; SInc is larger when reviewing at lower R (the spacing effect),
smaller at higher D or higher S (diminishing returns). On a lapse, S resets to a small post-lapse
value and the interval shrinks sharply. Difficulty mean-reverts toward an anchor each review,
specifically to avoid SM-2's "ease hell."

**Latest version:** FSRS-6 is the current **production** version (21 trainable weights; merged into
Anki 2025-04-25, first shipped in Anki 25.07). Its headline change is the trainable decay w20
(previously hardcoded), constrained roughly to [0.1, 0.8] with most users below 0.2, plus improved
same-day handling via w19. FSRS-7 is the leading *research* variant: an 8-parameter (dual-curve)
forgetting curve with fractional intervals, ~35 total trainable weights, and now scores lower log
loss than FSRS-6 in the live benchmark, but production ports still default to FSRS-6.

**Accuracy:** on the official `srs-benchmark` (349,923,850 reviews from 9,999 Anki collections,
time-series split), FSRS-6 scores Log Loss 0.3460 / RMSE(bins) 0.0653 / AUC 0.7034, ahead of older
heuristics in the same table (Duolingo HLR 0.4694, Ebisu v2 0.4989) and earlier FSRS versions
(FSRS-5 0.3560, FSRS-4.5 0.3624). The expertium benchmark analysis reports 99.6% superiority over
legacy SM-2 (lower log loss for 99.6% of users) and 88.2% over FSRS-5; optimized FSRS-6 beats
default-parameter FSRS-6 for ~84.3% of users. Note the live benchmark table no longer lists SM-2 and
now ranks research models (FSRS-7, RWKV-P, LSTM, GRU) above FSRS-6 on raw log loss; FSRS-6 is the most
accurate *deployable production* scheduler, which is the correct integration target today.

## Recommended library + license

**Target FSRS-6 via a maintained official port (open-spaced-repetition org).** Pick by app language:

| Port | Package | Version | License | Role |
|------|---------|---------|---------|------|
| Python | `fsrs` (py-fsrs) | 6.3.1 | **MIT** (c) 2022 OSR | Scheduler + optional `[optimizer]` extra |
| TypeScript | `ts-fsrs` | 5.4.1 (labels FSRS-v6) | **MIT** | Scheduler; `@open-spaced-repetition/binding` for training |
| Rust | `fsrs-rs` (`fsrs`) | 6.6.1 | **BSD-3-Clause** | Heavyweight: full training (Burn ML) + scheduler; what Anki uses |
| Rust (sched-only) | `rs-fsrs` | 1.2.1 | permissive | Scheduling only, no training |
| Go | `go-fsrs` | v4.0.0-rc1 | MIT | Scheduler |

All are MIT/BSD and free for commercial use (still attribute OSR in the credits surface). Anki itself
depends on `fsrs-rs` directly (`rslib` workspace dep), so that crate is the most battle-tested.

**Recommendation:** if the future app backend is Python, ship `py-fsrs` 6.3.1 for scheduling and add
the `[optimizer]` extra server-side for later per-user training. If a TS/Node backend, `ts-fsrs` for
scheduling + the binding for training. Keep the version pinned and treat FSRS-7 as a later
re-optimize, not a rewrite (see "FSRS-6 vs FSRS-7" below).

Minimal API sketch (py-fsrs 6.x):

```python
from fsrs import Scheduler, Card, Rating, ReviewLog

scheduler = Scheduler()                 # ships 21 default FSRS-6 weights, DR = 0.9
card = Card()                           # new card: stability/difficulty None, state Learning
card, log = scheduler.review_card(card, Rating.Good)   # apply grade
card.due                                # next due (UTC datetime)
scheduler.get_card_retrievability(card) # current recall probability

# later, server-side, per-user (pip install "fsrs[optimizer]"):
from fsrs import Optimizer
opt = Optimizer(all_review_logs_for_user)
params = opt.compute_optimal_parameters()
best_dr = opt.compute_optimal_retention(params)
tuned = Scheduler(parameters=params, desired_retention=best_dr)
```

## Persisted schema

FSRS needs exactly two persisted entities per learner: a **CARD** (one per (user, review-item) memory
trace) and an append-only **REVIEW_LOG**. Use the **review_log as the source of truth** and treat
card memory_state (S/D) as a derived cache, so a future FSRS-6 -> 7 reparametrization is a
re-optimize over the logs, not a schema migration.

### CARD (per user, per review item)

```
card_id            TEXT PK     -- our minted card id; embeds the stable corpus ID (see "Minting cards")
user_id            TEXT        -- learner
corpus_ref         TEXT        -- stable corpus ID this card tests (vocab:NNN / kanji:NNN / sentence:NNN / grammar:NNN)
card_kind          TEXT        -- direction/type enum (see minting); NOT an FSRS concept, app metadata
state              INTEGER     -- FSRS State: 1=Learning, 2=Review, 3=Relearning (New = absent/0 before first grade)
step               INTEGER NULL-- learning/relearning step index
stability          REAL NULL   -- S (days); NULL until first grade
difficulty         REAL NULL   -- D in [1,10]; NULL until first grade
due                TIMESTAMP   -- next due (UTC)
last_review        TIMESTAMP NULL
reps               INTEGER     -- optional bookkeeping
lapses             INTEGER     -- optional bookkeeping
fsrs_version       TEXT        -- e.g. "fsrs-6" so memory_state is interpretable per algo version
```

This matches py-fsrs `CardDict` (card_id, state, step, stability, difficulty, due, last_review) plus
our app keys (user_id, corpus_ref, card_kind, fsrs_version). ts-fsrs/go-fsrs carry a few more fields
(scheduled_days, reps, lapses, learning_steps) which are recomputable; keep reps/lapses for UX only.

### REVIEW_LOG (append-only, the durable truth)

```
log_id          TEXT PK
user_id         TEXT
card_id         TEXT        -- FK to CARD
rating          INTEGER     -- 1=Again, 2=Hard, 3=Good, 4=Easy
review_datetime TIMESTAMP   -- ISO, UTC
review_duration INTEGER NULL-- ms (optional; only feeds answer-time-aware models)
```

This is the complete py-fsrs `ReviewLog` schema (card_id, rating, review_datetime, review_duration) —
four fields, version-stable across FSRS versions. It is sufficient to re-derive memory state and to
run the optimizer. **Persist this from day one; without it, retroactive per-user optimization is
impossible.** The optimizer consumes a flat list of these (order does not matter for py-fsrs; fsrs-rs
wants them grouped per card as `FSRSItem { reviews: [{rating, delta_t}] }` with the first review's
delta_t = 0, which is a trivial transform from this log).

## Cold-start strategy

Ship the **21 built-in FSRS-6 default weights** (estimated from ~10k users / hundreds of millions of
reviews) and DR = 0.90. A brand-new learner is fully scheduled from review #1 with zero history:
a new card starts state=New, stability/difficulty unset, and gets real S/D on its first grade. The
default vector is identical across py-fsrs and ts-fsrs:
`[0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796, 1.4835,
0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542]` (last value = decay w20).

**Optimize per-user later, not at launch.** A good personalized fit needs ~1000 reviews (ideally
3000+); Anki's hard floor was ~400, lifted in 24.06+. A new paid learner runs on defaults for
weeks/months, which is fine. Policy:

1. Day 1 -> threshold: shared default 21 weights + DR 0.90.
2. When a user crosses ~1000 logged reviews: run the optimizer server-side over their REVIEW_LOG,
   store the resulting 21 weights + optimal DR on the user, and `reschedule_card` their existing
   cards (re-derive memory_state from logs, do not mutate the log).
3. Optionally, before any single user has enough data, train **one shared param set on aggregate
   pt-BR-learner review data** and ship that as the cohort default (a meaningful upgrade over the
   generic Anki-population defaults for this specific L1=pt-BR audience).

Expose **only DR** as a user-facing knob (default 0.90, clamp to 70-97%). Everything else is internal.

## Minting review cards from corpus items

FSRS is direction-agnostic: it needs a stable card-id and grades, nothing more. Card *type/direction*
is app metadata, not an algorithm concern. Honor the **minimum information principle** (one memory
fact per card): conflating facts corrupts the per-card D/S estimate. So a single corpus item fans out
into multiple cards, each addressed by the stable corpus ID plus a `card_kind` suffix:

| Corpus item (stable ID) | Cards minted (`card_id` = `corpus_ref` + kind) | Direction |
|-------------------------|-----------------------------------------------|-----------|
| Vocab `vocab:NNN` | `vocab:NNN#recognition` (JP form -> pt-BR meaning), `vocab:NNN#production` (pt-BR -> JP form) | L2->L1, L1->L2 |
| Kanji `kanji:NNN` | `kanji:NNN#reading` (kanji -> reading), `kanji:NNN#meaning` (kanji -> pt-BR meaning) | split per standard practice |
| Sentence `sentence:NNN` | `sentence:NNN#cloze:<token>` (one cloze per target token, blank the studied item) | production-in-context |
| Grammar `grammar:NNN` | `grammar:NNN#recognition` (pattern -> usage), optionally a cloze on an example sentence | recognition |

The corpus already holds both directions: it stores the pt-BR meaning (for L2->L1 recognition) and
the Japanese form (for L1->L2 production), so recognition/production asymmetry is just metadata on the
generated card. Cloze cards reuse the already-dissected sentence bank: a sentence lives once, fully
dissected, and each token is addressable, so blanking the studied vocab/grammar token in a real
Tatoeba/JEC sentence is a query, not new content. Recognition and production are scheduled
**separately** (separate cards, separate D/S) because the two directions are genuinely asymmetric.

## Families -> interleaving, frequency/dependency -> seeding

These are **upstream** concerns FSRS deliberately leaves to the host app (FSRS only schedules timing
once an item is already in the system; it has no notion of introduction order, prerequisites, or item
similarity). The corpus already supplies all of them:

- **Interleaving confusable items.** The corpus "families" (e.g. contrast pairs は↔が, に↔で,
  word/semantic fields) are exactly the confusable sets that benefit from interleaving via the
  discriminative-contrast hypothesis (alternating similar items helps learners notice distinguishing
  features — a mechanism distinct from spacing). When building the daily *new-card introduction queue*
  and ordering *due reviews of comparable retrievability*, interleave members of the same family
  rather than blocking them. FSRS picks *when* a card is due; the app picks *which order* same-day
  due/new cards are shown, and that is where family interleaving lives.
- **Frequency / dependency order seeds introduction.** The corpus's frequency-ordered vocab
  (`freq_rank`) and dependency-aware sequencing (the `introducing_topic_id` placement + the i+1
  unlock gates in `place_items.py`) determine the *order new cards enter the system*. FSRS never
  reorders introduction; it takes over only after a card's first grade. So: introduce in
  corpus/courseware order (frequency + dependency + lesson), then let FSRS schedule all subsequent
  reviews by due date. Anki's behavior confirms the handoff: with FSRS on, review order becomes
  "ascending retrievability," superseding any authored sequence for *review* (not for introduction).
- **Same-day introduce -> review.** The lesson flow (introduce then drill in the same session) maps
  to FSRS learning steps (default 1m, 10m). FSRS-6 handles same-day reviews with a crude heuristic
  (the benchmark even excludes same-day reviews from evaluation); if the app leans heavily on
  same-session drilling, validate this empirically and note FSRS-7 as the upgrade that specifically
  improves short-term modeling.

## Integration plan

1. **Persistence first (algorithm-version-agnostic).** Create CARD + REVIEW_LOG tables as above.
   REVIEW_LOG is the immutable source of truth; memory_state is a derived cache tagged with
   `fsrs_version`. This makes FSRS-6 -> 7 a re-optimize, not a migration.
2. **Card-derivation layer (the only real new work).** A generator that walks corpus items by stable
   ID and mints cards per the table above. This is the single gap between corpus and FSRS; the corpus
   already exposes everything else.
3. **Wire the scheduler.** On lesson completion, create cards (state New). On each grade, call
   `review_card` / `next`, append a REVIEW_LOG row, update the CARD cache.
4. **Build the daily queue.** New cards in corpus introduction order (freq + dependency + lesson),
   interleaving family members; due reviews by ascending retrievability, interleaving confusables.
5. **Cold-start now, optimize later.** Ship 21 defaults + DR 0.90; trigger per-user optimization at
   ~1000 reviews; optionally pre-train a pt-BR cohort default.
6. **Expose only DR** (default 0.90, clamp 70-97%).

## What the corpus must additionally expose

Almost nothing — by design. FSRS needs only a stable per-card id, prompt/answer content, and (for
queue building) family/confusable relations, all of which the corpus already provides. It does NOT
need frequency or dependency data for *scheduling* (those serve introduction order, which the app
owns). Concretely the corpus already exposes: stable IDs for vocab/kanji/grammar/sentence; both
directions (pt-BR meaning + Japanese form) for recognition/production; per-token dissection for cloze;
families for interleaving; `freq_rank` + `introducing_topic_id` for introduction order. The only
*new* artifact is the app-side **card-derivation layer** (step 2) — no corpus schema change required.

## FSRS vs SM-2 (and version note)

FSRS-6 dominates SM-2 (99.6% of users have lower log loss under FSRS-6 per the expertium analysis) and
needs roughly 20-30% fewer reviews than SM-2 for the same retention. SM-2 was never designed to output
recall probabilities (extra conversion formulas were bolted on for the comparison), and its lack of a
difficulty mean-reversion causes "ease hell"; FSRS's per-review D mean-reversion fixes this. Against
SuperMemo's modern SM-17, FSRS-6 still wins on an apples-to-apples online comparison (~83% superiority
on the SM-17 dataset). Second-language spacing has strong independent backing (Kim & Webb 2022
meta-analysis: medium-to-large effect on L2 learning; equal and expanding spacing statistically
equivalent), so FSRS's spacing-based engine is the right SLA fit.

**FSRS-6 vs FSRS-7 decision.** Build against **FSRS-6 now** (all stable ports default to it;
py-fsrs 6.3.1 MIT / ts-fsrs 5.4.1 MIT / fsrs-rs 6.6.1 BSD), and treat FSRS-7 (35-weight, dual-curve,
still stabilizing) as a later upgrade. Because REVIEW_LOG (4 fields) is version-stable and
memory_state is a version-tagged derived cache, the FSRS-7 migration is a re-optimize over existing
logs, not a schema change — and FSRS-7's better same-day modeling directly addresses the one weak spot
relevant to this app's "introduce -> same-day review" flow.

## Sources

- open-spaced-repetition: free-spaced-repetition-scheduler (MIT, DSR/DHP); py-fsrs README + LICENSE +
  scheduler.py / card.py / review_log.py / state.py / rating.py (6.3.1, MIT, 21 defaults, 4-field
  log); fsrs-rs README + Cargo.toml + dataset.rs (6.6.1, BSD-3, FSRSItem/FSRSReview, training);
  ts-fsrs README + models.ts + constant.ts (5.4.1 MIT, FSRS-v6); go-fsrs models.go (v4 MIT).
- srs-benchmark README (349,923,850 reviews / 9,999 collections; FSRS-6 0.3460/0.0653/0.7034; HLR,
  Ebisu, GRU, RWKV baselines); expertium Benchmark.html (99.6% vs SM-2, 88.2% vs FSRS-5, 84.3%
  optimized-vs-default); fsrs-vs-sm17 README (~83% vs SM-17).
- awesome-fsrs wiki (The Algorithm; ABC-of-FSRS: power curve, SInc, post-lapse, D mean-reversion,
  per-card independence, ascending-retrievability); expertium Algorithm.html (FSRS-6 formulas, same-
  day heuristic, w17-w20).
- Anki: rslib Cargo.toml + memory_state.rs + params.rs (fsrs-rs as engine; revlog -> FSRSReview;
  ~400/1000+ optimization threshold); deck-options manual (DR 0.90, <97%, ascending retrievability);
  PR #3929 (FSRS-6 merged 2025-04-25; shipped Anki 25.07).
- supermemo.guru minimum information principle; Chen/Paas/Sweller 2021 (discriminative-contrast
  hypothesis); Kim & Webb 2022 Language Learning (L2 spacing meta-analysis).
- This repo: `place_items.py` (freq + i+1 dependency gates, `introducing_topic_id`),
  `build_families_full.py` (contrast pairs / families), corpus stable-ID + dissected-sentence design.