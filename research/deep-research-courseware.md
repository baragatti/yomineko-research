# Deep research — courseware design (recovered + synthesized)

**Status:** Recovered from a deep-research run killed mid-flight. The **Fetch** phase completed
(116 extracted claims across ~35 real sources; source file
[`research/derived/deep_research_recovered.json`](derived/deep_research_recovered.json)). The
**Verify** (adversarial) and **Synthesize** phases never ran. This document is the recovered
synthesis. **Confidence is assigned conservatively** to reflect that no adversarial cross-check ran
(see Caveats).

Scope (verbatim from the run): finalize the courseware design for a pt-BR self-study Japanese course
(zero → N5 → N4), delivered later as a Flutter app — strictly **linear** course with a
prerequisite/unlock DAG, tagged-HTML lessons, an **FSRS** engine, built on the existing verifiable
corpus. Four areas: (1) kana pedagogy, (2) FSRS/SRS integration, (3) courseware data architecture,
(4) lesson length & structure.

**Confidence legend:** *high* = ≥2 independent sources OR one primary/authoritative source with no
contradiction; *medium* = single good source, or sources that partly qualify each other; *low* =
single weak/blog source or an internally-contested claim.

**Verdict legend:** ALIGNED (our doc already says this) · REFINE (specific change to a named doc) ·
GAP (something we are missing).

---

## Area 1 — KANA pedagogy

### Recommendation
- **Group by gojūon family (≈5 kana), one family per lesson, vowels-first then K·S·T·N·H·M·Y·R·W·ん.**
  Rows learned first for fluency; dakuten/handakuten/yōon/sokuon/long-vowel layer *on top of* the base
  order as add-on lessons, not a separate ordering. Chunk-then-test: a recall exercise immediately
  after each family.
- **Pace:** ~2 rows (10 kana) per 2–3-day block at ~15 min/day → full base hiragana in ~12 days.
  Hiragana is learnable to a reading level in days-to-a-week with mnemonics + spaced recall; the kana
  topic should be a small number of dense lessons, not a long unit.
- **Mnemonics:** image-per-character is the recommended primary method (kana is visually simple);
  reinforce with row-anchors (A·K·S·T…) + sound-family chunking ("patterns beat isolated symbols").
- **Katakana:** practitioner consensus (Tofugu) teaches it **after** hiragana, sequentially, reusing
  the identical method and skipping pronunciation re-explanation, in batches of ten; use explicit
  contrastive mnemonics for confusables (ソ/ツ, シ/ツ). One blog source instead favors a **light
  parallel "mirror" session** (~2–3 min/day) starting ~day 7 of hiragana. **Net:** hiragana-first is
  firmly supported; full serialization vs. light early interleaving is **contested** (see flag).
- **Handwriting:** genuinely contested in the sources (this is the most important nuance in Area 1):
  - *Pro-handwriting (mechanism + retention):* handwriting engages a broader sensorimotor/visual/
    language brain network than typing and builds the visual-form recognition that reading requires;
    handwriting (vs. digital-only) is associated with better kana retention, and short recurring 5-min
    handwritten output tasks improve retention/fluency in adult beginners.
  - *Anti / defer:* one practitioner source argues handwriting should be **skipped for initial kana
    acquisition** because reading-only is far faster and writing 2–3× the time-to-learn (writing is
    *deferred, not eliminated*).
  - *On-screen stroke-order animation specifically:* a 2026 experiment found animated stroke-order
    while memorizing a novel script **reduces reproduction accuracy** for medium/high-complexity
    characters and is non-significant only for low-complexity forms; for **linear/alphabetic-L1
    learners (= pt-BR)** the negative/null effect is pronounced for novices, with benefits appearing
    mainly at intermediate level. **Implication:** static stroke diagrams + actual handwriting are
    defensible; *auto-playing stroke-order animation for beginners is not* and may hurt. Kana are
    low-complexity, so handwriting them is the low-risk case.
- **Bootstrap words during kana:** explicitly endorsed by multiple practitioner sources — as soon as
  a kana family is known, introduce a few **whole words written only in already-taught kana** (あお,
  かお, ほん, ねこ, いぬ, みず; katakana loanwords パン/バス/テレビ) to seed the first SRS reviews.
  Selection heuristic: short (2–3 mora), high-frequency, picturable, fully writable in taught kana.

### Sources
- Avatalks — Kana Order Gojūon (sequence/pacing/row-anchors): https://avatalks.com/blog/kana-order-gojuon/ *(blog)*
- Tofugu — Learn Hiragana (family-of-5, mnemonics, defer-writing): https://www.tofugu.com/japanese/learn-hiragana/ *(blog/practitioner)*
- Tofugu — Learn Katakana (after hiragana, batches of 10, confusable mnemonics, loanword bootstrap): https://www.tofugu.com/japanese/learn-katakana/ *(blog/practitioner)*
- MDPI *Life* / PMC — Neuroscience of handwriting vs typing: https://pmc.ncbi.nlm.nih.gov/articles/PMC11943480/ *(secondary review)*
- CercleS 2024 — Kana retention via handwritten reflection cards: https://www.degruyterbrill.com/document/doi/10.1515/cercles-2024-0107/html *(primary)*
- *Reading and Writing* (Springer) — Motor-sequence/stroke-order × script experience × visual complexity: https://link.springer.com/article/10.1007/s11145-026-10837-x *(primary)*
- Verbacard — 10 common all-hiragana bootstrap words: https://verbacard.com/blogs/news/common-hiragana-words-beginners *(blog)*
- IIFLS — write-a-word-from-known-kana bootstrap pedagogy: https://iifls.com/learn-japanese-script-and-vocabulary/ *(blog)*

### Confidence
- Family-of-5 grouping, vowels-first, hiragana-first, chunk-then-test → **high** (multiple corroborating practitioner sources + matches universal practice).
- Mnemonics-as-primary, fast-kana pacing → **medium** (consistent but blog-sourced).
- Bootstrap-words practice → **high** (3 independent practitioner sources converge).
- Handwriting value for kana → **medium** (one primary + one secondary support it; one blog disputes for the *initial* phase — they are reconcilable: do handwriting, just don't gate reading speed on it).
- Stroke-order *animation* harms novice linear-L1 learners → **medium** (single recent primary study; plausible and specific to our L1, but unverified and not yet corroborated). **Flagged.**

### Verdict
- Family-per-lesson, vowels-first, dense/fast kana topic, bootstrap words: **ALIGNED.** `design/kana.md`
  §2–§4 and `courseware_architecture.md` §3 already encode all of this (one family = one lesson;
  bootstrap words = the only allowed ahead-of-grammar content, kana-only deps, enrolled as kana-reading
  vocab cards). Our base-family taxonomy and the bootstrap examples (あお/かお/ほん…) match the sources.
- Katakana timing: **REFINE (small).** `curriculum.md` §2 and `kana.md` §3 say "katakana right after
  hiragana" (sequential) — well-supported by Tofugu, so keep it. But add one sentence in `kana.md` §3
  noting an evidence-backed *optional* light early katakana exposure (~mid-hiragana) is also viable, so
  the sequencing is a deliberate choice rather than an unexamined default. Low urgency.
- Stroke-order animation: **REFINE.** `kana.md` §1 already says "handwriting practice can start from
  static stroke diagrams." Add an explicit caution: prefer **static** stroke diagrams over
  **auto-playing stroke-order animation** for beginner kana, citing the linear-L1 reproduction-accuracy
  finding. This protects against a tempting but evidence-contradicted UI default.
- Bootstrap-word *selection rule*: **ALIGNED**; `kana.md` §4 already states the exact heuristic
  (already-taught kana, 2–3 mora, concrete/high-frequency, prefer real N5 vocab).

---

## Area 2 — FSRS / SRS course integration

### Recommendation
- **Per-deck-preset parameters, not global.** FSRS parameters + desired retention are **preset-specific**;
  only the FSRS on/off toggle is global. Similar material shares a preset; subjectively different
  subjects get separate presets. Decks are bundled into reusable presets that propagate on change.
- **Desired retention is the master knob.** Default **90%** balances retention vs. workload; usable
  range 80–95% (Anki extends to 0.70–0.99); **>97% is overwhelming** and undermines spacing. There is
  **no universal optimum** — FSRS can compute a per-user minimum-workload retention (CMRR, ~5-year
  horizon for language learners). Don't ship one fixed global parameter set; learn per-preset once
  review history accrues (default median params are fine until then).
- **New-cards/day is the primary load lever, ~10×.** 20 new/day → ~200 reviews/day. Anki defaults:
  New cards/day = 20, Max reviews/day = 200. Because our course gates new cards by **lesson completion**
  (not a daily faucet), the flood is structurally avoided; the per-deck new/day cap is a **safety
  ceiling**, not the throttle.
- **Unlock-on-completion is FSRS-safe.** FSRS treats early/late reviews as first-class (no penalty), so
  a linear, unlock-gated course can release cards on lesson completion without breaking the scheduler.
  WaniKani's lesson→Apprentice-1 (4h first review) is the canonical "lesson completion enters the review
  cycle" pattern; its 9-stage / 5-tier table (Apprentice→Guru→Master→Enlightened→Burned) and
  **Guru = the unlock threshold** show mastery-gated downstream unlocking.
- **Card types per skill.** recognition / production / listening / handwriting (+ cloze). Bunpro uses
  typed **cloze-deletion** for grammar (production recall beats recognition for long-term retention)
  and self-grading for vocab; it deliberately **combines grammar+vocab in one deck** (textbook-mapped).
  HVPT evidence (Area 1/phonology) supports folding **listening-discrimination** cards into the FSRS
  schedule (not one-off), with multiple talkers per card for transfer.
- **Interleaving new vs review is configurable, and order matters for beginners.** Anki's gather/sort
  order puts new cards **last** so reviews are never buried; New/Review Order is a setting. A 2025 SLA
  study qualifies "always interleave": interleaving is a desirable difficulty **only after initial
  blocked practice** consolidates a new item — for beginners, block a new item first, then interleave.
- **Overload mitigation:** lower new-cards/day; Bunpro's "SRS strictness" + "ghosts" soften wrong
  answers (partial demotion instead of a full reset to stage 1) — a gentler model than Anki's hard reset.
- **Engine fit:** FSRS runs **fully local** with official Dart/Android scheduler implementations —
  directly embeddable in an offline Flutter app. Store **DSR** (Difficulty, Stability, Retrievability)
  per card; stability saturates so mature cards cost progressively less review budget (bounds long-term
  load in a growing course).

### Sources
- FSRS4Anki Tutorial (per-preset params, retention range, re-optimize cadence, CMRR): https://github.com/open-spaced-repetition/fsrs4anki/blob/main/docs/tutorial.md *(primary)*
- FSRS4Anki Wiki — The Optimal Retention (workload-minimum, per-user optimum, CMRR/Brent's method): https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Optimal-Retention *(primary)*
- free-spaced-repetition-scheduler repo (DSR model, local, Dart/Android impls): https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler *(primary)*
- Expertium — A Technical Explanation of FSRS (S/R definitions, review-when-R-low, per-preset gradient-descent fit): https://expertium.github.io/Algorithm.html *(primary/blog-expert)*
- WaniKani — SRS Stages (9 stages, intervals, Guru unlock threshold): https://knowledge.wanikani.com/wanikani/srs-stages/ *(primary)*
- Anki Manual — Deck Options (90% default, new=20/max=200, gather order new-last, New/Review Order): https://docs.ankiweb.net/deck-options.html *(primary)*
- AnkiWeb FAQ on FSRS (per-preset vs global toggle, new/day default, overload knobs): https://faqs.ankiweb.net/frequently-asked-questions-about-fsrs.html *(primary)*
- Tofugu — Bunpro review (parallel access layers, combined grammar+vocab deck, cloze card, ghosts/strictness): https://www.tofugu.com/reviews/bunpro/ *(blog/practitioner)*
- *Language Learning* 2025 — Undesirable Difficulty of Interleaved Practice (block-then-interleave): https://onlinelibrary.wiley.com/doi/10.1111/lang.12659 *(primary)*

### Confidence
- Per-preset params; 90% default + >97% overwhelming; new-cards/day as load lever; gather-order new-last; local/Dart FSRS → **high** (multiple official/primary sources agree).
- DSR model, review-when-R-low, stability saturation → **high** (primary algorithm sources).
- WaniKani stage/interval/Guru-unlock specifics → **high** (official).
- Cloze-for-grammar + combined deck (Bunpro) → **medium** (single practitioner source; product-specific, not a general law).
- Block-then-interleave for beginners → **medium** (single primary SLA study, plausible and decision-relevant; unverified). **Flagged.**

### Verdict
- Decks separated by skill type, per-deck FSRS knobs, unlock-on-completion enrollment, deck-created-on-
  first-card, new/day as a safety ceiling: **ALIGNED.** `courseware_architecture.md` §6 already states all
  of this almost verbatim, and `unlock_enums.json` already carries `card_type: [recognition, production,
  listening, handwriting, cloze]` and the per-skill deck list. Strong match.
- Bunpro **combined grammar+vocab deck**: **GAP / decision to record.** Our model is strictly
  skill-separated decks (`deck:grammar-n5`, `deck:vocab-n5`…). The research shows a credible alternative
  (textbook-mapped mixed decks). We should keep skill-separation (it matches the WaniKani/Anki
  per-skill-tuning rationale, which is better-sourced) but **note the alternative + the rationale for
  rejecting it** in `courseware_architecture.md` §6 so the choice is documented, not accidental.
- **Block-then-interleave** for new vs review: **REFINE (GAP-ish).** §6 "Pacing" says the flood is
  avoided but says nothing about *new-vs-review ordering within a session*. Add a one-line policy: when
  a lesson unlocks cards, let the new item get an initial blocked exposure before it interleaves with the
  backlog (matches Anki "new last" + the SLA finding). Cheap, evidence-backed, currently unstated.
- **Wrong-answer softening (ghosts/strictness):** **GAP (note only).** Our data-only run doesn't run the
  scheduler, but §6 could note that the app should prefer partial-demotion over hard-reset on lapse
  (Bunpro/FSRS behavior). Optional, low priority.
- **CMRR / desired-retention guidance:** **REFINE (minor).** §6 says "desired retention … overridable
  by the app/user." Add the concrete numbers (90% default, 80–95% band, >97% discouraged, per-preset)
  so the deck-registry defaults are evidence-anchored rather than arbitrary.

---

## Area 3 — Courseware data architecture

### Recommendation
- **Layered manifest hierarchy is the right shape.** Common Cartridge validates splitting a light
  **navigation/index layer** (the `<organization>` tree of nested `<item>`s, leaf items referencing
  resources by id) from the **resource/content payload** — only learner-facing resources appear in the
  nav tree. cmi5 (xAPI profile) similarly governs "Course Structure" with a deliberately **minimal** data
  model and supports **Content-as-a-Service** (content hosted separately from the index) — a precedent
  for our corpus-layer-by-reference design.
- **Model the prerequisite graph as a DAG, but express edges via competencies/objectives, not raw
  lesson→lesson links where possible.** The Curriculum Prerequisite Network paper formalizes courses as
  DAG nodes with directed prerequisite edges and verifies acyclicity (+ centrality/"cruciality"/blocking-
  factor metrics for finding foundational bottleneck nodes). LRMI's competency model gives the cleanest
  *taxonomy* of edges: a resource can **Require** (prerequisite), **Teach**, or **Assess** a competency —
  which maps directly onto our `needs` (Require) vs `unlocks` (Teach). LRMI deliberately attaches these
  as *properties on generic content* rather than inventing a closed "lesson" type — matching a
  level-agnostic, additive schema.
- **Caution on standard "dependency" elements:** Common Cartridge's `<dependency>` is **only**
  file/asset dependency, **not** pedagogical prerequisite; CC has **no** native conditional-release /
  unlock mechanism (it dropped IMS Simple Sequencing). So borrow CC's manifest *layering*, not its
  dependency semantics — our own `needs`/`unlocks` enum is the right call.
- **Unlock mechanics: copy WaniKani's directional dependency encoding.** Prerequisites are
  component/amalgamation ID arrays (`component_subject_ids` must be "passed" before a subject unlocks;
  `amalgamation_subject_ids` is the inverse). Unlock is gated by **both** mastery (all components reached
  SRS stage 5 / "passed") **and** linear level position. The **Assignment** object carries the lifecycle
  timestamps to model directly: `started_at` (= lesson completed → card enters review), `available_at`
  (next due), `passed_at` (first stage 5), `burned_at` (stage 9). Level advancement is a **90% pass-rate
  gate**, not mere completion. SRS is stored as a configurable per-system stage table (position/interval/
  interval_unit; anchors starting=1, passing=5, burning=9) — encode intervals as data, not hardcoded.
- **Linear-with-prerequisites beats a wide tree (industry precedent).** Duolingo migrated from the old
  branching skill tree (many parallel unlockable skills) to a strictly **linear Path** (one unit at a
  time) — a real-world data point favoring our linear-course-over-a-DAG design.
- **Unlock taxonomy + feature enum:** a closed, versioned enum of unlockable types + app features is
  consistent with LRMI's "Intended Use" controlled vocabulary (Exposition / Interactive / Lesson Plan /
  Assessment) and CC's resource-type restriction — controlled enums are standard practice.

### Sources
- 1EdTech Common Cartridge v1.3 Implementation (single rooted org tree, nav/resource split, `<dependency>` = asset-only, no conditional release): https://www.imsglobal.org/cc/ccv1p3/imscc_Implementation-v1p3.html *(primary)*
- cmi5 Spec (xAPI profile; Course Structure; minimal data model; CaaS): https://aicc.github.io/CMI-5_Spec_Current/ *(primary)*
- LRMI / schema.org educational vocab (Require/Teach/Assess; Intended Use; properties-on-generic-content): https://schema.org/docs/kickoff-workshop/sw1109_Vocabulary_LRMI.pdf *(primary)*
- WaniKani API v2 — Subjects/Assignments/Level Progressions (component/amalgamation arrays, dual gate, lifecycle timestamps, 90% level gate, stage table): https://docs.api.wanikani.com/20170710/ *(primary)*
- The Curriculum Prerequisite Network (DAG formalization + bottleneck metrics): https://arxiv.org/pdf/1408.5340 *(primary)*
- Duolingo — How we learn how you learn (skill tree → linear Path): https://blog.duolingo.com/how-we-learn-how-you-learn/ *(primary/industry blog)*

### Confidence
- Manifest nav/resource layering; CC `<dependency>` ≠ prerequisite; CC has no conditional release → **high** (primary spec).
- WaniKani encoding (component/amalgamation, dual gate, timestamps, 90% gate, stage-as-data) → **high** (official API).
- DAG formalization + acyclicity → **high** (primary paper) and matches our existing model.
- LRMI Require/Teach/Assess mapping to needs/unlocks → **high** (primary) — a strong external validation of our exact split.
- Duolingo linear-Path precedent → **medium** (industry blog, but directly on point and well-known).

### Verdict
- Four-tier manifest (manifest→course→topic→lesson), required-layer-first + lazy bodies, content-by-
  reference (corpus separate from courseware), needs/unlocks as `{type, ref}` arrays over a **closed
  versioned enum**, DAG over a strictly linear sequence, introduce-once unlocks, feature-gating: **ALIGNED.**
  `courseware_architecture.md` §2–§5 + `unlock_enums.json` + `lesson_schema.md` already implement every one
  of these, and the external standards (CC layering, LRMI Require/Teach, WaniKani timestamps, the DAG
  paper, Duolingo's linear pivot) **independently validate** our design. This is the most fully-confirmed
  area.
- **`needs` via competency/objective IDs (LRMI), not only raw lesson/item IDs:** **REFINE (optional,
  higher-effort).** Our `need_type` is item/lesson-keyed. LRMI argues prerequisites are cleaner as
  *competency* edges (Require X where another lesson Teaches X). We already approximate this (most needs
  are auto-satisfied by `cumulative_known_set`; explicit needs are item-keyed). Worth a short note in §3/§5
  acknowledging the competency-edge model as the formal backing for our needs/unlocks split (LRMI =
  citable provenance) and as a future option if item-level needs get unwieldy. Documentation, not a
  schema change.
- **Mastery-gated level advancement (WaniKani 90% pass-rate), not just lesson completion:** **GAP (note).**
  Our linearity gate is lesson completion + `cumulative_known_set`. WaniKani also gates *level* progression
  on a mastery threshold (90% of items passed). Since this run is data-only (no scheduler), this is an
  app-behavior note: record in §3 or §6 that topic/level advancement *may* later add a mastery gate
  (SRS-stage-based), with WaniKani as the precedent. Low priority for the corpus run.
- **Stage table as configurable data:** **ALIGNED.** We already keep SRS logic in the app and treat decks/
  card-types as data; the WaniKani "intervals as a per-system stage table" pattern matches our intent.

---

## Area 4 — LESSON length & structure

### Recommendation
- **Short, single-objective micro-lessons.** Microlearning = targeted, bite-sized, single-objective,
  delivered in a very short timeframe; scope each lesson to **1–2 objectives + 4–5 key takeaways**.
  Common practitioner time target: keep modules ~**2–5 min** (most under 10; typical 5–10).
  **Caveat:** a 2024 systematic review states there is **no settled consensus** on optimal micro-lesson
  duration — treat any specific minute target as a **design heuristic, not an evidence-backed constant.**
- **Chunking/segmentation aids retention + completion.** Grounded in Cognitive Load Theory (limited
  working memory). Reported figures (single practitioner source, treat as indicative not proven):
  microlearning ~80% completion vs ~20% long-form; ~17% more efficient; +25–60% retention; 65% of
  learners say typical modules overload them, 58% engage more with shorter segments. The
  *direction* (chunking helps) is well-supported across sources; the *exact percentages* are weak.
- **Worked examples → faded → practice is the right internal structure.** Studying worked examples
  reduces extraneous load and beats unguided problem-solving for novices (start each lesson with worked,
  dissected examples before production). Use **example–problem pairs** and **fading** (progressively
  remove solution steps); **completion problems** (partially-worked) are as effective as fully-worked and
  are an efficient middle rung. **Expertise-reversal:** fade examples as items become familiar → heavy
  explanation/dissection early, shifting to retrieval/production (SRS) later. Keep explanation **inline**
  with the example (avoid split-attention).
- **Don't over-optimize explanation-vs-practice ORDER.** A 2025 randomized experiment (N=156) found the
  *order* of examples vs problems had **no significant effect** on learning or cognitive load; prior
  WE-first vs PS-first evidence is inconclusive and may depend on prior knowledge. **Treat ordering and
  the explanation:example:practice ratio as a tunable parameter conditioned on content type** (mechanical
  kana drill vs conceptual grammar), not a fixed template.

### Sources
- eLearning Industry — Microlearning statistics (2–5 min target, 1–2 objectives/4–5 takeaways, completion/efficiency/overload figures): https://elearningindustry.com/microlearning-statistics-facts-and-trends *(secondary, marketing-leaning)*
- ScienceDirect 2024 — Microlearning systematic review (single-objective definition, CLT grounding, **no duration consensus**, 6 design principles): https://www.sciencedirect.com/science/article/pii/S2405844024174440 *(primary)*
- Wikipedia — Worked-example effect (Sweller & Cooper; example-problem pairs; fading; expertise reversal; completion problems; split-attention): https://en.wikipedia.org/wiki/Worked-example_effect *(secondary)*
- Instructional Science 2025 — Fading worked examples & example/problem order (N=156, order no effect; effect depends on knowledge type): https://link.springer.com/article/10.1007/s11251-025-09750-7 *(primary)*
- Mayer, *Multimedia Learning* Ch. 9 — The Segmenting Principle (segment to manage load): https://www.cambridge.org/core/books/abs/multimedia-learning/segmenting-principle/37240877DDA0362355ADB39936027982 *(primary; FETCH FAILED — see Caveats, but corroborated)*
- Segmentation effects on cognitive load / vocab learning / retention (PMC): https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10759450/ *(primary, surfaced in search; corroborates segmenting)*

### Confidence
- Short single-objective lessons + chunking aids retention/completion (direction) → **high** (primary review + secondary + CLT grounding + Mayer segmenting, mutually corroborating).
- Worked-example → faded → practice; completion problems; inline (no split-attention); expertise-reversal → **high** (classic, multi-source).
- Explanation/practice **order doesn't matter much**; ratio is content-dependent → **medium-high** (one strong primary RCT + inconclusive prior literature; this *limits* how prescriptive we should be).
- Specific minute target (2–5 min) and the % figures (80/20, 17%, 25–60%) → **low** (single marketing-leaning source; explicitly contradicted on "optimal duration" by the systematic review). **Flagged.**

### Verdict
- Single-objective, ≤1 core new grammar/lesson, chunking, spiral, worked-examples-then-practice ladder,
  retrieval→production exercise requirement, "split if it exceeds the band," SRS owns long-tail
  reinforcement: **ALIGNED.** `courseware_architecture.md` §7, `curriculum.md` §3 (ladder), and
  `lesson_schema.md` rule 6 (≥1 retrieval + ≥1 production) already encode the worked-example ladder, the
  one-objective cap, the spiral, and the split rule.
- **Length numbers — REFINE (the one substantive Area-4 change).** §7 sets **~300–700 words / 8–15 min**.
  The research's practitioner target is **2–5 min**, and the systematic review says **there is no
  consensus on optimal duration.** Our 8–15 min is *longer* than the microlearning band — but our lessons
  are "teach + explain the why," not pure micro-nuggets, so the gap is partly definitional. **Action:**
  in §7, (a) explicitly **mark the word/time band as a design heuristic, not evidence-backed** (cite the
  no-consensus finding), and (b) reconcile with the microlearning band — either justify why ours runs
  longer (richer worked-example pedagogy) or consider trimming the lower bound. Do **not** adopt the
  2–5 min figure as a hard target (weak source). This is honesty-of-provenance, per CLAUDE.md §1.5/§1.8.
- **Explanation:examples:practice RATIO — REFINE (minor).** §7's shape is good but implies a fixed flow.
  Add: the **order/ratio is tunable by content type** and fine-grained explanation-vs-practice ordering
  is **not** worth over-optimizing (cite the N=156 RCT). Prevents over-prescription in the lesson rubric.
- **Fading / completion problems / expertise-reversal — GAP (small, worth adding).** Our ladder is
  recognition→production but doesn't name **faded/completion exercises** as the efficient middle rung, nor
  the early-explanation→later-retrieval *shift across the course*. Add a line to `curriculum.md` §3 or
  `courseware_architecture.md` §7: include completion/faded-example exercises, and let worked-dissection
  dominate early lessons while later lessons lean on SRS retrieval (expertise-reversal). Well-sourced.

---

## Caveats (read before acting on this)

1. **The adversarial Verify phase never ran.** No claim here was independently fact-checked against a
   contradicting source by the harness. Confidence ratings above are *my* conservative estimate from
   source quality + cross-source corroboration, **not** a verified result. Anything marked **low** or
   **flagged** (the 2–5 min duration + % stats; stroke-order-animation harm; block-then-interleave;
   Bunpro cloze/combined-deck specifics) should be treated as a hypothesis pending a real check before
   it drives a hard design rule.
2. **Single-source / dubious claims explicitly flagged:**
   - Microlearning %s (80/20 completion, 17% efficiency, 25–60% retention) and the 2–5 min target —
     **one** marketing-leaning source, contradicted on "optimal duration" by the systematic review.
   - Stroke-order *animation* hurts novice linear-L1 reproduction — **one** 2026 primary study, uncorroborated.
   - Block-then-interleave for beginners — **one** 2025 SLA study, uncorroborated.
   - Bunpro's combined grammar+vocab deck + cloze-card superiority — **one** practitioner review (product-specific).
3. **Lost / failed sources (2 of ~35):**
   - **1 source lost:** one fetch returned **zero claims and was flagged `unreliable`** by the agent
     (entry #6 in the recovered JSON) — its URL/title did not survive; content unrecoverable.
   - **1 source paywalled/failed but corroborated:** Mayer's *Multimedia Learning* Ch. 9 "Segmenting
     Principle" (entry #25, primary, 2009) fetched **zero claims** (Cambridge book chapter, likely
     paywalled). The construct it would supply (segment to manage cognitive load) **is independently
     corroborated** by the PMC segmentation study and the microlearning sources, so the Area-4 conclusion
     does not depend on it.
4. **Provenance fit (CLAUDE.md):** all four areas are **Layer C (pedagogical)** recommendations —
   research-grounded but `needs_review: true`. None alters Layer-A/B corpus facts. The only changes
   recommended below are to **design docs**, not to corpus data.

---

## Concrete change list (summary)

| # | File | Change | Why | Confidence |
|---|------|--------|-----|------------|
| 1 | `courseware_architecture.md` §7 | Mark the 300–700 word / 8–15 min band as a **heuristic, not evidence-backed**; reconcile vs the microlearning 2–5 min band (justify longer or trim lower bound) | No research consensus on duration; our band is longer than microlearning and currently presented as if settled | high (that it's unsettled) |
| 2 | `courseware_architecture.md` §6 | Add a **block-then-interleave** new-vs-review ordering policy + concrete FSRS retention defaults (90%, 80–95%, >97% discouraged, per-preset) | Currently unstated; both are evidence-backed and make deck defaults non-arbitrary | medium / high |
| 3 | `kana.md` §1/§3 | Prefer **static stroke diagrams over auto-playing stroke-order animation** for beginner kana; note optional light early katakana exposure as a deliberate alternative | Animation hurts novice linear-L1 reproduction (flagged single study); document the katakana-timing choice | medium |
| 4 | `curriculum.md` §3 / `courseware_architecture.md` §7 | Name **faded/completion-problem** exercises + the early-worked-dissection→later-SRS-retrieval shift (expertise reversal); state explanation:practice **order/ratio is tunable by content type** | Well-sourced internal-structure refinement; prevents over-prescription | high / medium-high |
| 5 | `courseware_architecture.md` §3/§6 | Note (docs only) the LRMI **Require/Teach/Assess** competency-edge model as provenance for our needs/unlocks split, and WaniKani's **mastery-gated level advancement** as a future option | External validation + a recorded future option; no schema change now | high |
| 6 | `courseware_architecture.md` §6 | Record the **Bunpro combined grammar+vocab deck** alternative and why we keep skill-separated decks | Make the deck-separation choice documented, not accidental | medium |
