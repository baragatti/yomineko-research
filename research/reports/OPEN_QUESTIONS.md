# Open questions for the owner

_Written 2026-09-27. Status measured from `APP_PLAN.md` §3 and `PENDING.md` at commit `eb11721f`.
Each question gives what it blocks, the options, and a recommendation. Answer by id, e.g. "D11: B"._

## Where the project stands

| measure | value |
|---|---|
| Plan units done | 35 of 48 (73%) |
| Plan units partly done | 6 |
| Plan units open | 7, of which 6 wait on a decision below |
| AI-doable content base (course, practice, SRS, exams, typed speak path) | about 92% |
| Whole product as planned (adds audio, voice mode, teacher review, hosting, N2/N1) | about 75% |

The remaining AI work needs no decision from you. It is four writer-chain units already queued:
stored token readings, listening + small residues, empty-lesson examples and the speak strand
rebalance. After them come one follow-up unit and the audio schema (W33). The percentages above
are estimates built from unit counts and the per-area gaps, not a single metric.

---

## 1. Blocking decisions (work cannot start without them)

### D11 — N3 pacing
**Blocks:** W25 (N3 rebalance and the two missing N3 reading sections).
**Finding:** N3 vocabulary was dealt to lessons in gojuon order, not by theme or grammar. The words
of a real sentence sit a median 32 lessons apart, so only 304 of 1,596 N3 words have three readable
examples at the lesson that teaches them. Median 17 new words per lesson (N4: 7).
**Options:** A keep as is · **B** grammar lessons keep at most 8 words they actually use, the other
~1,170 are regrouped by theme into vocabulary lessons of at most 10 · C raise the cap and split
heavy lessons.
**Recommendation:** B. Close only the part of the ~750-word band gap the 情報検索 section needs.
Detail: `w25_proposal.md`.

### D3 — Audio and voice
**Blocks:** W35 (audio assets), W36 (voice play mode), the playable listening sections of every
exam paper, and the speak path's spoken layer.
**Questions:** which TTS engine and voice, and is its output licensed for a paid app? Which ASR
engine for voice mode? Is romaji accepted as a correct production answer?
**Recommendation:** pick a TTS whose licence explicitly allows commercial redistribution of the
generated audio. Do not accept romaji as a correct answer past pre-N5.

### D4 — A named reviewer
**Blocks:** W39 (a teacher approving N5 through the ledger).
**Ready:** the review views, the review sheet format, the ledger and the teacher README in pt-BR
(`research/review/`). Every AI-authored record is marked `needs_review`.
**Question:** who reviews, and under which handle (`reviewed_by`)?

### D8 — Database and hosting
**Blocks:** W43 (physical schema for the user-state contracts).
**Ready:** logical contracts for all 7 runtime entities, the API contract and the release manifest.

### D1 — N2 and N1
**Blocks:** W44.
**Question:** do N2/N1 stay as exam-bank-only content, or become full course levels?
**Recommendation:** stay bank-only until N3 is rebalanced (D11) and reviewed (D4).

### D2 — Lesson completion and placement
**Blocks:** placement only (W23 is otherwise applied).
**Options:** (a) placing out does not seed cards · **(c)** place at topic granularity, mark
skipped lessons `completed` with `mastery: unknown`, and seed their cards tagged `placed-out`.
**Recommendation:** (c), already marked as the default in the contract. Either answer is a
re-run, not a migration.

### D9 — Attribution rulings
**Blocks:** W42 closing.
**Questions:** can the KanjiVG flag close? The only shipped field is the kanji's own codepoint, with
no geometry. Is bulk Tatoeba credit enough, or do you want per-sentence author names? Per-sentence
names need a new dump. Also, do you accept the conservative reading that derived stroke data is
covered by OFL?

### D12 — Level evidence for N3 and above
**Question:** add a third independent level source for N3+, or formally relax spec §1.5 (at least
three lists) for those levels?

---

## 2. Quick calls (a recommendation is ready; the work is already prepared)

| id | question | recommendation | what happens on yes |
|---|---|---|---|
| **B-W28** | SRS card examples: how far above the card's level may the sentence be? | **A**: up to one level above (vocab cards with an example 1,256 → 1,810) | table ready, one apply |
| **B-W40** | Author ~20,300 English strings for pedagogy now? | **(b)**: no; English stays where it derives (done), `en` optional for pedagogy fields, residue kept as a work list | contract change only |
| **A9b** | 8 vocab records still address the wrong JMdict entry (掛ける, 履く, 縦, 本当, 格好, 事, 喧嘩, 御) | decide pair by pair with the reviewer; nothing ships inconsistent today | per-pair merge or deprecation |
| **B-W21b** | 4 forward-reference rewrites the verifier rejected (they would remove an item's only practice) | move those unlocks back to their earlier home (n5-perguntas-04 for gp-31) | one small unit |
| **B-W11 (1)** | `grp:suru-irregular` lists 416 する-verbs as a "family" | demote to a class flag on the vocab record | one small unit |
| **B-W11 (2)** | practice ratchet counts absolutes, so promoting an exemption looks like a regression | hold it as a rate per level and kind | validator change |
| **B-W37** | 250 Layer-A kanji were stamped AI-created by an old script; reset to `dataset`. Should their pt-BR meanings return to "needs review"? | yes: the meanings are Layer B | one flag flip |
| **D5** | handwriting cards | keep them: every kana now has stroke data; retire only if the app ships no handwriting widget | none |
| **Translation style** | 9 natural translations use gender-inclusive "(a)"; 5 subject-less sentences chose a person | pick one gender only where the Japanese implies it; otherwise keep "(a)" | small repair table |

---

## 3. Defaults already applied (no action unless you want to overrule)

D4 approval semantics (per record, per locale, hash-anchored, no expiry) · D6 kana in FSRS, one
glyph per card · D7 register value set · D10 speak phrases deck · D13 per-field layer
(`field_layers`) · D14 kanji-component families dropped · D-scoring JLPT score bands (sourced, with
uncertainty stated) · A10 speak patterns not capped at the stage band (the label shows the level).

## 4. Not decisions: the teacher review queue

These wait for the reviewer, not for you: about 7 exam items where a distractor still fits after
inflection; the 家/け unlock in n4-condicionais-07; 530 token links decided by AI rulings; every
record marked `needs_review`. The review views under `research/review/` list them in course order.
