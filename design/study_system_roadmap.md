# Study-system & exam-prep roadmap (PLAN ONLY, 2026-06-27)

> **Ordering:** everything here comes **AFTER** the JLPT exam-alignment ([`design/jlpt_alignment_plan.md`]) is
> done **and checked** (level tags + course/topics/lessons aligned to N5/N4/N3 expectations). None of this is to
> be executed now — this is the detailed plan. Owner-requested 2026-06-27.

Four workstreams: **A** stroke animation · **B** exam simulator + exercise banks · **C** lesson capability
tagging · **D** daily study system (FSRS + a complementary skill-SRS). A/B/C are buildable once alignment lands;
**D's implementation waits on its own research spec** (the research itself is deferred — only the agenda is here).

---

## A. Stroke-order ANIMATION — kana + kanji (deferred until after alignment)
We already have the stroke **data** (kanji: **Kanji Alive** CC BY 4.0 in `corpus/strokes/`; kana: **strokesvg**
OFL+MIT) and **static** viewers (`KanjiStrokes.tsx`, `KanaStrokes.tsx`). What's pending is the **animation**:
- A moving **guide "ball"/dot that traces each stroke in order**, plus **start-point markers + stroke-order
  numbers** (the "symbols"), for **hiragana, katakana, AND kanji**.
- Controls: play / pause / replay, per-stroke step, speed; honor `prefers-reduced-motion` (fall back to the
  static progressive outline we already render).
- Tech: SVG path animation — reveal each stroke via `stroke-dasharray`/`stroke-dashoffset`, and move the ball
  along the path with `getPointAtLength()` (or CSS `offset-path`/motion-path). Pure **client island**: the
  stroke paths are public, attributed data already shipped to the client for the draw — **no paid corpus
  involved**, so no-leak is unaffected.
- Acceptance: every kana and every kanji-with-stroke-data animates stroke-by-stroke with order indicators; the
  898 N2/N1 kanji without stroke paths keep the decomposition fallback (per D-LIC-3).

---

## B. Exercise BANKS + EXAM SIMULATOR (N5 / N4 / N3)
**Goal:** an exam simulator that *feels like the real JLPT* — multiple-choice etc., **randomized from our banks
every attempt**, with **≥2–3 variations per item** so retaking is never "memorize the answers" — a genuine
study/learning tool, not a memory test.

**Architecture:**
- A reusable **exercise bank per question TYPE** (e.g. `corpus/exercise_banks/<type>.json`). Each entry is a
  **template** that **points to corpus data by ID** (sentence / vocab / kanji / grammar) — reuse, never embed.
- An exam-simulator layer assembles a paper by sampling templates per section, respecting level.

**JLPT question types to model** (structure/format is a non-copyrightable fact; research the real section
layout + timing first):
- *Vocabulary (Language Knowledge):* kanji→reading, orthography (kana→kanji), word-formation, contextual usage,
  paraphrase/synonym.
- *Grammar:* form selection (fill the particle/ending), sentence composition (word-ordering / "star" slot),
  text-grammar cloze in a short passage.
- *Reading:* short / medium / longer passages + info-retrieval — **reuse the reading bank** (`corpus/readings/`).
- *Listening:* **deferred** (needs audio; note as a later track).

**Randomization & variations (the anti-memorization core):**
- Each template samples random **eligible items** from the bank: in **study mode**, restricted to the user's
  known-set/level; in **exam mode**, the full level.
- **2–3 item variations** + **2–3 distractor-generation strategies** per template so each run differs.
- **Distractors authored by RULE, not hand-picked** (so they scale + vary): pull plausible wrong answers from
  related corpus items — same POS, near-homophone reading, same grammar family, same semantic field. Always
  exactly one correct option; shuffle deterministically per-attempt (seeded) for stable SSR.

**Modes:** (1) **Exam simulator** — timed, full-level, real section structure, scored. (2) **Practice** —
untimed, pick a section/type.

**IP / licensing (HARD — per §1.4 + `design/license_audit.md`):** real JLPT papers and official sample
questions are **© Japan Foundation / JEES — copyrighted**. Use them **only** as *structural/format* reference
(which question types exist, section order, timing, answer-sheet style) — **never copy or lightly reword a real
question**. All items are **authored clean-room from our own corpus**. A 3rd-party question source may be used
as *content* **only if verifiably public-domain or permissive**, and then recorded in `sources.md` +
`ATTRIBUTION.md` + `dataset_source`. When unsure, treat as expression and don't reproduce.

**Acceptance:** every level covers all (non-listening) question types; ≥2–3 variations per template; zero copied
real-exam text; output randomized each attempt; exam mode mirrors the real section structure + timing.

---

## C. Lesson CAPABILITY tagging — "language features", not just words
**Grade every lesson for what it UNLOCKS beyond vocab/kanji:** the actual skills / ways / quirks. Examples:
masu-form, te-form, plain/casual, past, negative (ない), particles (は が を に で へ と も から まで…), counters,
i-adj vs na-adj conjugation, question formation (か), です/だ, comparatives, conditionals (と/ば/たら/なら), keigo
(尊敬/謙譲/丁寧), transitivity pairs, giving/receiving (あげる/くれる/もらう), potential, volitional, etc.

- Define a **FIXED, versioned CAPABILITY registry** (`corpus/capabilities/` + a `capability` table): stable
  `id`, neutral `key` + pt-BR name/description, `level`, and `prerequisite` capability ids (a DAG).
- Extend `lesson_unlocks` with a `capability` unlock type (alongside kanji/vocab/grammar). Tag each lesson with
  the capabilities it **introduces** and **reinforces** — derive mostly from existing grammar unlocks, plus a
  content pass for the implicit ones (particles/conjugations a lesson actually drills).
- This fixed "unlocked capabilities" set is the input to the daily **skill track** (section D).
- Acceptance: every lesson tagged; capability DAG has no cycle/orphan; `cumulative_known_set` is extended to
  carry capabilities so "what the learner can do" is queryable at any lesson.

---

## D. Daily study system — FSRS (memory) + capability-SRS (skills) — RESEARCH AGENDA (do later)
**Two tracks run together each day:**
1. **Memory track (PRIMARY, battle-tested): FSRS** over unlocked **words + kanji** (readings/meanings). This is
   the canonical core; keep it the focus.
2. **Skill track (SECONDARY, lighter): a separate scheduler over the CAPABILITY list (§C)** — short,
   time-boxed brain exercises from the **existing banks** (drag-drop, multiple-choice, particle-choice,
   conjugation, an exam question…). The signal is **right/wrong PER CAPABILITY**, NOT exact-item recall. Show
   **more** of the capabilities the user struggles with and **less (never zero)** the ones they ace — an
   SM-2/FSRS-style ease maintained **per capability**. Purpose: keep **reading / phrase-forming** ability sharp
   (what separates *teaching* from *memorizing*), not just flashcard memory. Examples: random verb conjugation,
   a particle choice, a question lifted (clean-room) from the exam bank.

**Daily flow:**
- Build the day's queue **once per day** — ideally computed **fast at the user's first login of the day**, and
  **refreshed after they study more lessons** (since they then go straight to SRS). Must be cheap enough to run
  per-user at login + incrementally after lessons.
- **Queue = mostly FSRS-due cards + a SMALL, time-boxed set of skill exercises.** The skill quantity is bounded
  by a **studied time-budget algorithm** so total session length is short + predictable and the two tracks
  interleave without bloating the day.

**Research to do LATER (document → `design/srs_design.md` BEFORE any implementation):**
- **FSRS** (latest, v4/v5/v6): scheduling math, parameters + optimizer, new-card seeding, retention target,
  load management; reference open implementations + **confirm license** (FSRS core is open/MIT — verify before
  use; do NOT bundle anything copyleft/SA into shipped code without the owner ruling).
- **Complementary algorithms to combine for the SKILL track:** SM-2 (Anki), Half-Life Regression (Duolingo),
  Leitner; FSRS-vs-SM-2 tradeoffs. The skill track needs a **per-capability** ease (not per-item) — likely a
  lightweight FSRS/SM-2 instance per capability. Pick what pairs cleanly with the memory track.
- **Balance & time-budget:** how much skill work to add per day without diluting FSRS; target session length;
  interleaving (FSRS-first vs mixed); backlog handling so a missed day doesn't explode. The explicit owner
  requirement: **main focus stays the battle-tested FSRS; the skill track is a controlled, bounded extra.**
- **Performance/data model:** indexing for fast due-queue computation; incremental update after lessons;
  per-user once-per-day caching.
- **Important boundary:** this run produces **data + courseware + reference material only** (CLAUDE.md). The
  daily algorithm is **app/runtime logic** — so D is **design/spec only here**; the FSRS/skill engine is built
  in the actual app, grounded on this spec. What this corpus run must provide *for* it: the capability registry
  (§C), the typed exercise banks (§B), and stable IDs so the engine can schedule against them.

---

## Where this is tracked
STATE.md backlog → items added pointing here. Build order after alignment: **A** (quick, self-contained) and
**C** (enables D) first; **B** next (reuses C's types + the reading bank); **D** last, gated on its research
spec. Nothing here blocks the corpus/courseware data work.
