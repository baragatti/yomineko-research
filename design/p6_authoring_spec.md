# P6 — Courseware authoring contract (lessons)

> Rules P6 (lesson authoring) and P7 (verification) MUST follow. Captures the owner's directives
> (2026-06-14). Most are already enforced by `schema_v2`; this makes the rest explicit so nothing slips.

## 1. Linear, i+1 progression
- Lessons are ordered within a topic; a lesson's `prerequisites` are earlier lessons.
- Aim ≤1 new grammar point per lesson; prior items spiral in later lessons by reference.
- `lesson.cumulative_known_set` = union of all `lesson_introduces` up to and including that lesson — this is
  both the i+1 "known set" used to filter dissected sentences and the learner's active set.

## 2. Single source of truth for phrases — NO duplication (enforced)
- Every dissected sentence lives **once** in `sentence` (fully dissected, §6).
- Lessons/exercises hold **sentence IDs only** (`lesson_sentence`, `exercise_sentence`; M:N — one sentence
  serves many lessons from many angles).
- ∴ Editing a sentence (fixing a gloss, translation, audio) **propagates to every lesson** that references it.
  No phrase text is ever copied into a lesson (rubric hard gate **G4**).

## 3. FSRS auto-enrollment contract (data-only; app implements scheduling)
- A lesson's **`lesson_introduces`** (the kanji/vocab/grammar **first taught** there) is **exactly the set
  that auto-enters the FSRS scheduler when the learner completes that lesson.**
- Therefore: **introduce-once** — every reconciled item is introduced in **exactly ONE** lesson; later lessons
  reuse it by reference only (never re-introduce).
- Items are chunked/tagged so the future app's FSRS can schedule them; SRS *logic* itself is out of scope for
  this corpus run (spec §0), but the data contract above makes enrollment trivial.

## 4. 100% coverage — pass the JLPT level AND communicate
- The N5 module must **introduce and practice 100% of the reconciled N5 kanji/vocab/grammar** (N4 module → N4).
- Guaranteed path: every item already has an introducing **topic** (0 unplaced); P6 splits topics → lessons
  preserving this, so every item gets an introducing **lesson**.
- Each item must also be **used** in ≥ its sentence threshold (kanji ≥M, vocab ≥3, grammar ≥5 dissected
  sentences — acceptance #1/#2/#3), so the learner actually *sees and produces* it.
- **P7 verifies:** 0 items without an introducing lesson; 0 N5 kanji unused in any lesson's sentences.

## 5. Kanji literacy strand — per-kanji (or per-batch) lessons  *(owner idea — adopted as an option)*
- The kanji strand MAY include a dedicated lesson **per kanji** (or per small batch), scheduled **after** the
  learner has met that kanji's **components** and the grammar its example sentences need.
- A per-kanji lesson contains (all by ID / from the registries): meaning(s) pt-BR, readings tagged by tier,
  component breakdown (with the component family), KanjiVG stroke order, its vocab, ≥M dissected sentences,
  and production/**handwriting** exercises. It complements — does not replace — the communicative topic
  lessons. Completing it enrolls the kanji (and its taught vocab) into FSRS (rule §3).

## 6. Exercises
- Typed + structured (recognition · cloze · particle_choice · sentence_build · reading · listening ·
  production · handwriting · matching), referencing the corpus **by ID**, with structured answer keys
  (schema in place). ≥1 retrieval + ≥1 production exercise per lesson (rubric pedagogy-fit).

## 7. Rich, interactive lesson format
- Lessons are authored as **rich HTML with a constrained set of custom elements** (the front-end renders them:
  phrase rich-modals, kanji hover/click modals, inline exercises, media). Full plan + initial component
  vocabulary: **[`design/lesson_format.md`](lesson_format.md)** (schema finalized in P6).
- Every interactive block **references the corpus by ID** (consistent with rule §2) — no embedded content.
- P7 validates: only allowed elements; all `ref` ids resolve; learner text pt-BR.

---
_Status: rules 1, 2, 4, 6 already enforced by schema + placement; rules 3 (FSRS contract), 5 (per-kanji
lessons), 7 (rich format → `lesson_format.md`) recorded here for P6. P7 adds the coverage/enrollment/
HTML-integrity verification checks above._
