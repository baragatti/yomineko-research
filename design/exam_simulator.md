# JLPT exam simulator — picker algorithm spec (v1, 2026-07-05)

> Data = `corpus/exam_banks/{level}_{type}.json` (4,359 items, all derived from verified corpus facts,
> validated by `validate_exam_banks.py`). The APP implements this picker at runtime; the corpus run ships
> data + this spec only. Real JLPT papers are © JEES — this mirrors only the (non-copyrightable) FORMAT.

## Paper structure (per attempt)
Mirror the real Language-Knowledge sections (listening deferred). Item counts follow the real exams:

| Section (type) | N5 | N4 | N3 |
|---|---|---|---|
| kanji_reading (漢字読み) | 7 | 7 | 8 |
| orthography (表記) | 5 | 5 | 6 |
| context_fill (文脈規定) | 6 | 8 | 11 |
| grammar_form (文法形式) | 9 | 8 | 13 |
| sentence_order (並べ替え) | 4 | 4 | 5 |
| paraphrase (言い換え類義) | 3 | 4 | 5 |
| usage (用法) | 0* | 4 | 5 |
| text_grammar (文章の文法) | 2 | 3 | 4 |
| reading_comp (読解・短文) | 3 | 4 | 4 |
| listening_task (課題理解) | 7 | 8 | 6 |
| listening_point (ポイント理解) | 6 | 7 | 6 |
| listening_gist (概要理解) | 0* | 0* | 3 |
| listening_say (発話表現) | 5 | 5 | 4 |
| listening_reply (即時応答) | 6 | 8 | 9 |
(*section absent in the real exam at that level — N5 has no 用法; 概要理解 starts at N3.)

## Timing (verified 2026-08-21 against jlpt.jp + JEES + LTTC, two independent checks)
The exam is separately-timed PARTS, not one sitting, and the app mirrors that: you cannot carry time
from vocabulary into reading, and a part that runs out is collected as-is.

| Part | N5 | N4 | N3 |
|---|---|---|---|
| ① 言語知識（文字・語彙） | 20 | 25 | 30 |
| ② 言語知識（文法）・読解 | 40 | 55 | 70 |
| ③ 聴解 (not run — audio pending) | 30 | 35 | 40 |

Two corrections to what this doc previously said. The N4/N5 shortening took effect **December 2020**,
not 2022 (N4 30→25 and 60→55; N5 25→20 and 50→40). The only December-2022 change was N1 聴解 60→55;
**N3 was never shortened** — 30/70/40 are its original post-2010 durations.

**There is no official JLPT break.** jlpt.jp publishes durations only: no clock schedule, no break, and
the word 休憩 appears nowhere in the JEES timetable. Each administering body sets its own, and they
disagree — Japan schedules a 20-minute gap after ① (unlabelled), Taiwan 25 (15 of it labelled rest),
Korea 5. That gap is also not free time: JEES footnote ※2(4) says candidates cannot leave for about 20
minutes while papers are collected. The app therefore simulates the **Japan-domestic scheduled gap**,
names it as such, and lets the learner skip it. Do not restate it as "the JLPT break", and do not invent
a rest figure — none is published. reading_comp items carry a `reading` slug; the app renders the passage from
`corpus/readings` above the question (several items may share a passage across attempts, never within one
paper — enforce one item per passage per attempt). listening_* items are TEXT scripts until voiced
(`audio: "pending"`); playback order per subsection + TTS pipeline: `design/listening.md`. Listening
sections enter a paper only once their items have audio.

## Sampling rules
1. **Uniform random without replacement** within each section's bank for the level.
2. **No-repeat window:** exclude items answered in the user's last 3 attempts of that level (fall back to full
   bank if it would starve the section). This + bank sizes (≥240 per choice-type at N5/N4) makes every retake
   feel fresh — the anti-memorization requirement.
3. **Option shuffle:** per attempt, shuffle [correct + 3 distractors] with the attempt seed. For
   sentence_order, shuffle `pieces` (reshuffle if identity order).
4. **Real-first:** items carry an `ai` flag (0 = real bank sentence). Prefer `ai=0` when a section has enough;
   verified-generated items (§9-gated, needs_review) fill the rest.
5. **Seeded:** seed = (userId, level, attemptNo) → reproducible papers for support/review.
6. **Scoring:** 1 point/item; section + total percentages; per-type breakdown feeds the capability tracker
   (roadmap D) as right/wrong signals.

## Study mode
Same banks, untimed, immediate feedback; filter items to the learner's cumulative known-set
(lesson.cumulative_known_set) so practice never shows untaught material.

## Known gaps (backlog)
- DONE 2026-07-06: N3 link-enrichment landed — all deterministic banks full (context_fill 400, grammar_form 300).
- DONE 2026-07-06: paraphrase + usage banks authored + adversarially verified (366 items; layer C,
  needs_review). Usage items keep the REAL bank sentence as the correct option.
- DONE 2026-07-06: text_grammar (262 deterministic items over reading passages) + reading_comp (286 items,
  one 内容一致 question per verified passage; authored + adversarially verified against the pt ground truth;
  flagged items fixed per verifier reasons and re-checked). All Phase 2c non-audio types shipped.
- Mid/long passages (中文・長文) + info-retrieval (情報検索) reading items — future authoring phase; current
  reading_comp covers 短文-style single-question passages only.
- DONE 2026-07-06: listening SCRIPTS authored + adversarially verified (239 items = 3× paper counts minus one
  above-level real prompt; five subsections mirroring the real 聴解; spec `design/listening.md`). AUDIO is
  pending — the owner voices the scripts with a local TTS/voice model; items carry `audio: "pending"` and the
  simulator excludes listening sections until audio lands.
