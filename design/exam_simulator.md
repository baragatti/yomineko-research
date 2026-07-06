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
(*N5 has no 用法 section in the real exam.) Timing: N5 ≈ 40 min, N4 ≈ 55 min, N3 ≈ 70 min for these sections (guideline).

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
  needs_review). Usage items keep the REAL bank sentence as the correct option. Remaining authored types:
  text-grammar cloze + reading-comprehension question sets — Phase 2c.
- Listening — deferred (needs audio).
