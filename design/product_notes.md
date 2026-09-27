# Product notes — decisions and standards for the app built on this corpus

Owner decisions and product intentions that shape the data, kept here so a future session (or the
API/app project) does not have to rediscover them. Dated; newest first. The plan of record is
`research/reports/APP_PLAN.md`; open questions are in `research/reports/OPEN_QUESTIONS.md`.

## The product

- A full Japanese-learning app for Brazilian Portuguese speakers, Duolingo-shaped, with integrated
  Anki-grade memorization (FSRS-6 or better), in-lesson tests, exams and JLPT simulations.
  Everything learner-facing is pt-BR (never pt-PT).
- Two paths: the JLPT course (zero → N5 → N4 → N3) and a speak-as-fast-as-possible path.
- The quality bar is "a very high quality product for study": when in doubt, the more correct and
  better-grounded option wins over the cheaper one.

## Decisions of 2026-09-27

| topic | decision |
|---|---|
| Teacher review (D4) | The first MVP ships **without** teacher review; a teacher reviews after the MVP. Until then every AI-authored record stays `needs_review`, everything that can be standardized is standardized, and the error margin is kept as low as possible (author + independent verifier + sampling + hard validators). |
| API / database (D8) | This repository is the **research and data** project. It produces fully standardized, contract-checked exports (`corpus/`, `course/`, `contracts/`). The API and the physical database are built later **from these exports**; no API work happens here. |
| N1 / N2 (D1) | Not supported now and nothing is added for them, but nothing may block them: level stays data, never structure. |
| Placement (D2) | Place at topic granularity; skipped lessons are `completed` with `mastery: unknown`; their cards are seeded tagged `placed-out` under a separate admission cap. |
| N3 pacing (D11) | Choose the option that makes lessons digestible and that learners actually learn from, **losing no data** (expected: option B of `w25_proposal.md`, confirmed by a small research first). |
| Level evidence (D12) | Add a third independent level source for N3 and above if the task is not giant. |
| Strokes (D9) | Stroke order and drawing/completion data must be as complete as possible for **all** characters, kana and kanji. |
| Quick calls | All accepted as recommended (card examples up to one level above; English for pedagogy deferred; see OPEN_QUESTIONS §2). |

## Audio (D3)

- Engine to start with: **Chatterbox Multilingual** (the owner names it "V3 Multilingual"), run
  **locally** on the owner's GPU (AMD Radeon RX 9070 XT, 16 GB) to voice all Japanese and the
  pt-BR lesson text. The exact install path is researched in `design/audio_pipeline.md`.
- **Content-addressed audio.** Every clip is identified by a hash of its normalized text plus
  language, voice, model version and synthesis parameters. The same content always maps to the same
  file, so there are **never duplicates**; generation is **incremental** (only new or changed
  content); unreferenced files are **pruned**. File names are URL-safe and short enough to avoid
  path problems. The files live outside git; a tracked manifest maps hash → text and consumers, so
  hosting later is a copy of the store plus the manifest.

## Content standards

- **Word by word must match the sentence exactly.** The token list shown to the learner is the
  sentence, in order, with nothing missing, duplicated or extra; sub-word pieces are nested under
  their token, never mixed into the list.
- **Particles and explanations are enumerable.** Each particle occurrence carries a usage id from a
  closed enum (by Japanese grammar: class and usage, e.g. に as point in time, destination, agent),
  defined in a JSON schema with Markdown documentation; explanations are generated from templates
  keyed by the enum, with free text only as an addition. This makes exercises per particle usage
  mechanical and searchable.
- Selection over generation (spec §1.2); every generated sentence is `ai_generated` + `needs_review`.
- Every repair lands in both layers through a tracked, replayable table; the index can be rebuilt.
