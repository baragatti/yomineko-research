# JLPT scoring model — what the real test reports, and what we are allowed to claim

Authored 2026-09-02 for **W19** of [`research/reports/APP_PLAN.md`](../research/reports/APP_PLAN.md);
settles decision **D-scoring**. Closes readiness gap G4 of
[`readiness/exams_simulations.md`](../research/reports/readiness/exams_simulations.md) — *"No JLPT
scoring model"*.

Companion to [`exam_simulator.md`](exam_simulator.md) (the paper spec, which owns section counts and
timing) and [`user_state.md`](user_state.md) §7 (`exam_attempt`, whose `scaled` field this fills).

Held to the standard the timing table set: **two independent checks, dated, with the uncertainty
stated.** §3 is that record, and §3.5 says plainly which parts of it are weaker than the timing note's.

---

## 1. The structure: 得点区分 (scoring sections)

The JLPT does not report one number. It reports a **total** plus a small number of **scoring
sections** (得点区分), and the number of them changes at N3.

| Level | Scoring sections | Range |
|---|---|---|
| N1 / N2 / N3 | 言語知識（文字・語彙・文法） Language Knowledge (Vocabulary/Grammar) | 0–60 |
| | 読解 Reading | 0–60 |
| | 聴解 Listening | 0–60 |
| | **総合得点 Total** | **0–180** |
| N4 / N5 | 言語知識（文字・語彙・文法）・読解 Language Knowledge (Vocabulary/Grammar) + Reading | 0–120 |
| | 聴解 Listening | 0–60 |
| | **総合得点 Total** | **0–180** |

Two things this table is easy to get wrong, and both matter to us:

* **Scoring sections are not test sections.** The paper is sat in separately-timed *test sections*
  (文字・語彙 / 文法・読解 / 聴解 at N3–N5); the *scoring* sections are a different partition of the same
  questions. At N4/N5 the first two test sections collapse into ONE 0–120 scoring section. At N3 they
  are re-cut the other way: the 文法 大問 score into Language Knowledge, and only 読解 scores into
  Reading — even though 文法 and 読解 were sat together in one booklet.
* **N4/N5 merge Language Knowledge with Reading on purpose.** The official reason is pedagogical: at
  the foundation levels the two abilities overlap and are not yet clearly separable, so reporting them
  together fits the stage of learning better than splitting them.

## 2. The pass rule

Passing requires **both** of:

1. **総合得点 ≥ 合格点** — the total is at or above the level's *overall pass mark*; and
2. **every 得点区分 ≥ 基準点** — each scoring section is at or above its *sectional pass mark*.

A candidate who misses even one sectional minimum **fails, however high the total.** That is the whole
reason a percentage cannot express a JLPT verdict, and the reason G4 called this the largest
"is it really a simulation" gap after listening.

| Level | Overall pass mark | LK (Vocab/Grammar) | Reading | Listening |
|---|---|---|---|---|
| N1 | 100 / 180 | 19 / 60 | 19 / 60 | 19 / 60 |
| N2 | 90 / 180 | 19 / 60 | 19 / 60 | 19 / 60 |
| N3 | 95 / 180 | 19 / 60 | 19 / 60 | 19 / 60 |

| Level | Overall pass mark | LK (Vocab/Grammar) + Reading | Listening |
|---|---|---|---|
| N4 | 90 / 180 | 38 / 120 | 19 / 60 |
| N5 | 80 / 180 | 38 / 120 | 19 / 60 |

N1/N2 are listed because the structure is level-agnostic (spec §1.6) and the table is cheaper to hold
whole than to re-source later; we ship N5/N4/N3 today.

**In force since:** these criteria applied from the 2010 first sitting (July), and for N4/N5 from the
2010 second sitting (December) — the levels' first administration. They have not changed since.

**A missed test section is not a low score, it is no score.** The official rule is that a candidate
who does not sit every required test section is failed and no results are issued — and the Hong Kong
body states the consequence more sharply than the English pages do (§3.3): the candidate is sent a
result notice, but **no score is printed for any subject, including the ones they did sit.** §6 is
where that becomes our `incomplete` verdict rather than a fabricated total.

## 3. Sourcing

### 3.1 Check A — jlpt.jp, the official site (Japan Foundation + JEES), read 2026-09-02

* 得点区分 and ranges, EN: <https://www.jlpt.jp/e/guideline/results.html> §1, and the test-section →
  scoring-section correspondence in its §2 (this is what §1's second bullet above is built on).
* Pass rule and both pass-mark tables, EN: same page §3; also restated in the FAQ,
  <https://www.jlpt.jp/e/faq/index.html> §5.
* Japanese original, separately maintained page: <https://www.jlpt.jp/guideline/results.html>
  §1 and §3. It agrees figure-for-figure with the English and carries one thing the English page
  omits — the 適用 note giving the in-force dates quoted in §2.
* The pedagogical reason for the N4/N5 merge: <https://www.jlpt.jp/faq/index.html> §5.

The EN and JA pages share a publisher, so they are **one source read twice**, not two sources. The
JA page's extra in-force note is the only figure here that rests on a single page.

### 3.2 Check B — AATJ, the United States administering body, read 2026-09-02

<https://www.aatj.org/jlpt/jlpt-faq/> — an independent publisher (the American Association of
Teachers of Japanese, not the Japan Foundation and not JEES). It independently states the property
this whole document's uncertainty rests on: JLPT scores are **scaled scores computed from each
candidate's pattern of answers, not from the number of questions answered correctly**, which is why a
reported score can differ from what a candidate expects. It also confirms the missed-section rule
(a paper with any section missing is recorded as not completed and no results are issued).

AATJ does **not** republish the pass-mark table, so Check B corroborates §2's *rule* and §4's
*uncertainty*, and not the *numbers*.

### 3.3 Check C — 香港日本語教育研究会, the Hong Kong administering body, read 2026-09-02

<https://www.japanese-edu.org.hk/jp/jlpt/jlpt.html> — the Hong Kong Japanese Language Education
Research Society, the body that runs the test in Hong Kong and Macau. A different organisation from
the Japan Foundation and from JEES, publishing its own page in Japanese, and the only non-official
publisher found that republishes the **figures** rather than only the rule. It carries, on that one
page:

* the 得点区分 table with the ranges — N1–N3 as three 0–60 sections, N4/N5 as 0–120 + 0–60, total
  0–180 at every level;
* the 合否判定 rule in two numbered conditions, with the sentence our §2 rests on: 「一つでも基準点に
  達していない得点区分がある場合は、総合得点がどんなに高くても不合格になります」;
* the missed-section rule, and more sharply than the English pages state it — 「ひとつでも受験しない
  試験科目があると不合格になります」, and no scores are issued **for any subject**, including the ones
  that were sat;
* both pass-mark tables, agreeing figure for figure with Check A: N1 100 / N2 90 / N3 95 with 19 in
  each of the three sections, and N4 90 / N5 80 with 38 out of 120 and 19 out of 60.

**The caveat, and it is the same one AATJ carries.** The page says outright that Hong Kong runs the
test 「国際交流基金に協力させていただいて」 — in cooperation with the Japan Foundation. Every local
administering body stands in that relationship, so no second publisher of these figures is ever going
to be independent of the test's own organisation. What Check C establishes is that the table was
transcribed correctly by a second organisation with its own reason to get it right, not that a second
body derived the numbers. The page has no last-updated stamp; it is current at least through 2025,
which it names in its timing section.

### 3.4 Check D — English Wikipedia, "Japanese-Language Proficiency Test" § Scoring, revision
`1356864178` of 2026-05-30, read 2026-09-02

Transcribes the same overall and sectional pass marks, and adds two facts we use: that the sectional
minima work out to **31.67%** of each section's range (19/60, and 38/120 — the same fraction, which is
why the two-section and three-section levels are consistent), and that the only raw-score information
a real score report carries is a coarse band in its "Reference Information" — whether raw performance
on a question group was **≥67%, 34–66%, or <34%**.

Wikipedia cites the same jlpt.jp page. So this is a **transcription check** — it proves we copied the
table correctly — and not independent evidence for the figures.

### 3.5 What we could not get, stated rather than hidden

Attempted 2026-09-02 and yielding nothing:

* **LTTC (Taiwan)**, the body the timing note used as its third check: `jlpt.tw` publishes registration,
  timetable and score-report-delivery pages, but **no pass-mark or 得点区分 table** (About / ScoreReport /
  FAQ / ExamInfo all read; two candidate score pages returned HTTP 500).
* **JEES** (`info.jees-jlpt.jp`) — FAQ index reachable, no results/scoring page found.
* **JLPT Korea** (`jlpt.or.kr`) — HTTP 403 / empty body.
* **JLPT USA** (`jlptusa.org`) — domain no longer resolves; AATJ has taken over that content (Check B).
* **CBLJ / jlpt.org.br** (the Brazilian administering body, the one our learners actually sit under) —
  publishes dates, fees and the registration manual; **no scoring information at all.**
* **The official scaled-score explanation PDF** (`jlpt.jp/e/about/pdf/scaledscore_e.pdf`, linked from
  both jlpt.jp and AATJ) — fetched, but it is a scanned/binary PDF that did not extract to text here.
  Its *existence and what it is linked as* is itself corroboration of §4; its contents are unread.

Two more that did not pan out: the guessed national-body domains `jlpt.org.sg`, `jlptmalaysia.com`,
`jlpt.org.uk`, `jlptindia.com` and `jlptthailand.org` do not resolve at all, and `jlpt.ph` served a
certificate this machine could not verify. Whatever those bodies publish, they do not publish it there.

**Honest summary of the sourcing standard reached.** Every claim in §1 and §2 — the 得点区分 structure,
the two-condition pass rule, the missed-section rule and **the figures themselves** — now rests on two
publishers that are separate organisations: jlpt.jp (Check A) and 香港日本語教育研究会 (Check C), read the
same day and agreeing figure for figure. AATJ (Check B) is a third organisation and independently
carries the rule and the scaled-score uncertainty, though not the numbers; Wikipedia (Check D) is a
transcription check that proves we copied the table correctly and nothing more.

**What is still weaker than the timing table, and stated rather than hidden.** The timing note's three
publishers were meaningfully independent of each other. Here they are not: both AATJ and the Hong Kong
society administer the test *in cooperation with the Japan Foundation*, and every local body does, so
"a second publisher independent of the test's own organisation" is not a thing that exists to be
found. What §3 establishes is that the table is transcribed identically by more than one organisation
with a stake in getting it right — a corroboration of the transcription, not of the derivation. The
one figure still resting on a single page is the 適用 in-force date in §2, which only the Japanese
jlpt.jp page carries.

## 4. The uncertainty: scaled scores are not computable from a raw count

The JLPT reports **scaled scores** produced by an **item-response-theory** model. Equivalent ability
yields the same scaled score across different sittings and different question difficulty, which is the
point of the design — but it means:

* the mapping from *number correct* to *scaled score* is **not published**, is **not linear**, and
  **changes per sitting** with the difficulty of the questions actually used;
* two candidates with the same raw count can receive different scaled scores, because the model reads
  *which* items were answered correctly, not *how many*;
* raw scores are not reported at all, beyond the coarse ≥67 / 34–66 / <34 percent bands in the score
  report's Reference Information (§3.4).

**Therefore no scaled JLPT score can be reproduced by this app, or by anyone outside JEES.** Anything
we print in the 0–180 space is our own estimate wearing the JLPT's units. The rest of this document is
about being explicit that that is what it is.

## 5. The house approximation

**Definition.** For each scoring section `s` that the paper actually contained:

```
scaled(s) = round( max(s) × right(s) / of(s) )
```

where `right(s)` is the number of correct answers in that scoring section, `of(s)` is the number of
questions the paper put in it, and `max(s)` is 120 or 60 per §1. The estimated total is the sum of
`scaled(s)` over the sections present; the verdict applies §2's rule to those numbers.

**It is a linear map of raw section percent onto the official scaled range, and nothing more.** It is
labelled an approximation everywhere it is shown, in the data (`approximation: true` on the report
object) and in the pt-BR the learner reads ("pontuação estimada", never "sua nota JLPT").

**Why linear.** Every alternative needs calibration data that does not exist publicly. An IRT model
needs item difficulty parameters we have never estimated (and could only estimate from response data
we do not yet collect); an anchored raw→scaled table needs released papers with their scaled outcomes,
which JEES does not publish. A linear map is the only transformation whose error we can describe
honestly: it is **monotonic and unbiased in direction but wrong in magnitude**, and wrong by an amount
nobody outside JEES can quantify.

**What it is good for.** Ranking your own attempts against each other; noticing that one section is
dragging you under its minimum; converting "I got 62% of the grammar right" into the shape the real
report uses. **What it is not good for:** predicting a real result. In particular, near a boundary the
estimate says nothing — a learner estimated at 81/180 at N5 has not "passed", they have landed inside
the band where our error dominates.

**Known bias.** The real exam's raw→scaled curve is regressive at the extremes (very low and very high
raw scores compress). A linear map therefore **overstates the range**: it hands out 0s and 180s that
the real model does not produce. We do not correct for this, because any correction constant would be
invented. It is recorded here so nobody later mistakes the linearity for a modelling claim.

## 6. Mapping our 大問 onto the 得点区分

The paper spec's fourteen section types map onto scoring sections as follows. This is the app's
`SCORING_MODEL` table, and the reason it is per-level.

| Our section type | N5 / N4 scoring section | N3 scoring section |
|---|---|---|
| `kanji_reading` 漢字読み | LK+Reading (0–120) | Language Knowledge (0–60) |
| `orthography` 表記 | LK+Reading | Language Knowledge |
| `context_fill` 文脈規定 | LK+Reading | Language Knowledge |
| `paraphrase` 言い換え類義 | LK+Reading | Language Knowledge |
| `usage` 用法 | LK+Reading | Language Knowledge |
| `grammar_form` 文法形式 | LK+Reading | Language Knowledge |
| `sentence_order` 並べ替え | LK+Reading | Language Knowledge |
| `text_grammar` 文章の文法 | LK+Reading | Language Knowledge |
| `reading_comp` 読解 | LK+Reading | **Reading (0–60)** |
| `listening_*` 聴解 (5 types) | Listening (0–60) | Listening (0–60) |

The N3 column is the one that is easy to get wrong: 文章の文法 is sat inside the 文法・読解 booklet but
scores as **grammar**, not as reading (§1, and the correspondence table cited in §3.1).

**Incomplete papers.** Listening does not enter a paper until its items have audio
(`exam_simulator.md`; audio is W35). While that is true, every paper we run is missing a whole 得点区分,
and the real rule for a missing test section is failure with no results issued (§2, §3.2). So:

* a scoring section with no questions is reported as **not attempted**, `scaled: null`;
* the verdict is **`incomplete`** — never `pass`, never `fail`, and never a total that silently
  pretends 180 points were available when only 120 were;
* the UI says which section is missing and why. A learner must not read "aprovado" off a paper that
  never tested listening.

## 7. What the app implements

`scorePaper()` in `prototype/app/lib/exam.server.ts` grades a paper and returns, per scoring section:
raw right/of, raw percent, the approximated scaled score, the sectional minimum, and whether it was
met; plus the estimated total, the level's pass mark, whether it was reached, and the verdict
(`pass` | `fail` | `incomplete`).

`gradePaper()` is untouched and still returns raw right/total/percent per §6 of the paper spec, so
existing callers and the 1-point-per-item contract in `user_state.md` §7 (`total_raw`,
`total_possible`) are unaffected. The scaled model is **additive**, not a replacement: `exam_attempt`
stores both, exactly as its table says.

`exam_attempt.scaled` (`user_state.md` §7) is filled as
`{score, max, pass_mark, sectional_minima_met}` from this report, and `passed` is set only when the
verdict is `pass` or `fail` — it stays null while the verdict is `incomplete`.

## 8. What would make this better, in order

1. **Audio (W35).** Until listening exists, every verdict is `incomplete` and the model is exercised
   but never conclusive.
2. **Real response data.** With enough attempts we could fit item difficulties and replace the linear
   map with a calibrated one — still ours, still not JEES's, but with measurable error instead of
   unmeasurable error.
3. **A publisher of the §2 figures that is not a JLPT administering body.** Check C closed the
   "one publisher" gap (§3.3), but every body that republishes the table runs the test in cooperation
   with the Japan Foundation, so the figures are still corroborated only *inside* the test's own
   network of organisations. A textbook, a standards body or a peer-reviewed paper citing them would
   be the real upgrade.
