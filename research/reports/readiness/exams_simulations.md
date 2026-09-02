# Readiness — exams & JLPT simulations

> **Scope.** The exam/simulation capability of the app: `corpus/exam_banks/` (40 banks), the paper spec
> `design/exam_simulator.md` + `design/listening.md`, the contract `contracts/exam_item.schema.json`, the
> gate `scripts/validate/validate_exam_banks.py`, and the reference implementation
> `prototype/app/lib/exam.server.ts` + `prototype/app/routes/exam.tsx` / `examPaper.tsx`.
>
> **Method.** Every number below was recomputed from the exported JSON in this working tree, not quoted from
> a document. Where a document and the data disagree, the disagreement is called out and adjudicated.
> `db/corpus.sqlite` was not used as evidence. Nothing in the repo was modified except this file.
>
> **Headline.** The app can run a full timed N5/N4/N3 paper with scoring **today** — but it is a *two-part*
> paper, not the real three-part exam, and two of its nine sections (`text_grammar`, `reading_comp`) are
> built on passages that are not passages. N2/N1 have **zero** exam material and, per the standing owner
> directive, zero of the corpus layers an exam needs.

---

## 1. What this capability needs from the data

A JLPT simulation is not a quiz. To feel like the exam and to be trustworthy as a score, it needs six things
from the data layer:

| # | Requirement | Concretely |
|---|---|---|
| R1 | **Item banks per (level, section)** | one record per question, with a stem/prompt, an answer key, a distractor set of the section's own option count (4, or 3 for 発話表現/即時応答), and enough items that a retake is not a rerun. |
| R2 | **A paper structure** | the 大問 list per level with per-section item counts, grouped into the exam's separately-timed **parts**, with each part's official duration. |
| R3 | **Passage entities** | 読解 and 文章の文法 hang off a text. That text must be a *text* (one topic, 3–6 connected sentences), addressed by a stable slug, resolvable independently of the item. |
| R4 | **Audio entities** | 聴解 is a third of the real paper. Scripts with speaker-tagged turns are the authoring artifact; a per-item audio asset is the shippable one. |
| R5 | **Provenance and gating** | every item carries `layer` / `source` / `ai_generated` / `needs_review` so the picker's real-first rule and the teacher-review queue both work, and every item resolves to a corpus record so "you also meet this in a lesson" is true. |
| R6 | **A scoring model** | per-item marks, per-section rollup, and — for a *simulation* — the exam's own verdict rules (section score bands and the pass mark), not just a raw percentage. |

Plus two runtime needs that the corpus feeds but does not own: an **attempt record** (for the no-repeat window
and for score history) and a **capability signal** (per-type right/wrong routed into the capability tracker).

---

## 2. What exists today — verified

### 2.1 Banks

**6,048 items in 40 bank files**, recomputed from `corpus/exam_banks/n[0-9]_*.json`:

| | n5 | n4 | n3 | total |
|---|---:|---:|---:|---:|
| items | 1,667 | 2,121 | 2,260 | **6,048** |

By id prefix: `kr` 1,200 · `or` 1,179 · `cf` 992 · `so` 871 · `gf` 728 · `rc` 286 · `pp` 183 · `us` 183 ·
`tg` 187 · `lr` 68 · `lt` 63 · `lp` 57 · `ls` 42 · `lg` 9.
Layer B 5,157 / Layer C 891. `ai_generated` true 638. `needs_review` true 1,248 — **none of them reviewed**.
Zero duplicate ids across all 40 banks. `corpus/exam_banks/INDEX.md` now matches the data file-for-file
(0 mismatches; the three stale N4 counts and two stale N3 counts named in the QA sweeps are fixed).

`corpus/exam_banks/removed_items.json` holds **118** items withdrawn from the banks in full, with reasons:
93 answer-leak items, 21 n5 homophone-group items, 2 changed-passage `tg` items, 2 exact `so` duplicates.
(`scripts/validate/README.md` still describes this ledger as "the 93 removed leak items" — it is 118 now.)

### 2.2 Paper structure and capacity

`design/exam_simulator.md` and `prototype/app/lib/exam.server.ts` `SECTIONS` agree, and
`validate_exam_banks.py` hardcodes the same table as `PAPER_COUNTS` on purpose so the two cannot drift.
Papers actually built: **N5 39 questions, N4 47, N3 61** (non-listening).

Every non-listening section clears the gate's `MIN_RATIO = 3` comfortably — measured lowest ratios:

| thinnest banks | items (passages for `rc`/`tg`) | paper | ratio |
|---|---:|---:|---:|
| n3_reading_comp | 152 passages | 4 | 38.0× |
| n5_reading_comp | 43 passages | 3 | 14.3× |
| n3_paraphrase / n3_usage | 71 | 5 | 14.2× |
| n5_grammar_form | 129 | 9 | **14.3×** |
| n5_text_grammar | 33 passages | 2 | 16.5× |

I ran the picker's own algorithm over **500 seeds per level**: every section filled to its exact count on
every seed (n5 39/39, n4 47/47, n3 61/61 — 1,500 papers, zero short sections). Expected item overlap between
two independently-seeded papers is **1.5 of 39 (n5), 1.5 of 47 (n4), 2.2 of 61 (n3)** — about 3.5% either way.

> **Doc vs data — `design/exam_simulator.md` is wrong twice.** Its header says the banks hold **"4,359
> items"** (they hold 6,048), and sampling rule 2 justifies freshness with **"bank sizes (≥240 per
> choice-type at N5/N4)"**. That is false for nine (level, type) banks: n5 `grammar_form` 129,
> `paraphrase` 52, `usage` 52, `reading_comp` 43, `text_grammar` 33; n4 `paraphrase` 60, `usage` 60,
> `text_grammar` 61, `reading_comp` 91. The *data* is right and the paper still fills — the ≥3× ratio, which
> the validator actually enforces, is the true invariant. The prose is stale; delete the 240 claim.
> `prototype/app/lib/exam.server.ts:4` likewise says "the 6,166-item bank" — also stale (6,048).

### 2.3 Passages

`corpus/readings/{n5,n4,n3}.json` — **286 passages** (n5 43, n4 91, n3 152). Every one of the 286 `reading`
slugs referenced by an exam item resolves; **all 286 passages are consumed by `reading_comp`** (1 item per
passage) and 187 of them additionally by `text_grammar`. Layer B, `ai_generated: false`,
`needs_review: true` on all 286.

They are **not passages**. Each is a concatenation of unrelated bank sentences — `source_slugs` is 2–3
sentences at N5, 4 at N4, 5–6 at N3. Verbatim from the current export:

```
read:n5-adjetivos-04-01  どこに行くところですか。ありがとうございます！
read:n5-adjetivos-05-01  ただ見ているだけです。どこから出るんですか。
```

This is A1 in `research/reports/PENDING.md`; the owner **decided (a): author real passages, keep the
sections**. That decision is recorded and **not yet executed** — the data above is the current shipped state.

### 2.4 Listening

**239 scripts**, every one `audio: "pending"` (verified: the only value present in the field across all
listening items). Bank sizes hit exactly 3× the paper counts everywhere except **`n5_listening_reply`, which
is 17 against a paper count of 6 — 2.83×**, the "3× minus one above-level real prompt" the design notes.
`design/listening.md` says the bank is 240 scripts; it is 239.

**Listening is absent from `PAPER_COUNTS` in `validate_exam_banks.py`,** so the ≥3× capacity gate does not
cover it. When audio lands, that shortfall ships ungated.

### 2.5 Provenance, contract, and the gate

`contracts/exam_item.schema.json` is a real contract, not a shape dump: it branches per id prefix and
requires the right fields per section family (word-level MC, in-sentence MC, ordering, passage MC,
paraphrase, usage, listening). `scripts/contracts/migrate_exam_banks_p7.py` documents the derivation of
`layer`/`ai_generated`/`needs_review` per family and is asserted by `validate_provenance_json.py`.

`scripts/validate/validate_exam_banks.py` is the section gate and it **passes green on the current tree**:

```
validate_exam_banks: 6048 items in 40 banks, ALL OK
advisory  okurigana_giveaway 373 (baseline 373) · orthography_longshot_distractors 241 (241)
          orthography_shape_solvable 300 (304) · reading_comp_string_match 32 (32)
          sentence_order_ambiguous 1 (1)
```

It re-derives ground truth from `corpus/vocab`, `corpus/sentences`, `corpus/readings`, `corpus/grammar` —
never the SQLite index — checks blank integrity, option-set distinctness under NFKC + kana folding, `so`
reassembly, ref resolution, that `tg` stems equal their passage-with-blank (which is what makes not
rendering the passage safe), that the 118 withdrawn items stay out, and the ≥3× capacity of every
(level, type) the paper draws. Four quality counters are frozen as ratchets in
`scripts/validate/exam_banks_baseline.json` — they may shrink, never grow.

### 2.6 The app

`prototype/app/lib/exam.server.ts` implements the picker and is the strongest piece of this area:

- Deterministic paper from `(level, seed)` via mulberry32; grading **rebuilds the paper server-side** and
  never trusts an id or an answer key echoed by the client. `correct` is stripped from the loader payload.
- Real-first ordering keys on the explicit `ai_generated` boolean.
- **Paper-wide** one-item-per-passage guard (`seenPassage`), which is the correct scope — `tg` and `rc` draw
  from the same pool.
- `PARTS` models the exam as separately-timed parts: ① 言語知識（文字・語彙） 20/25/30 min,
  ② 言語知識（文法）・読解 40/55/70 min, with a 20-minute scheduled gap after ①. The timing table carries a
  dated two-source verification and an unusually honest note that JEES publishes no 休憩 at all — the app
  names the Japan-domestic scheduled gap as such and lets the learner skip it.
- `examPaper.tsx` runs the clock, collects a part when its time expires (the part cannot be reopened), keeps
  every part mounted so earlier answers still post, and renders a per-section + total result with a
  question-by-question review.
- A section that matched no part would silently change the scoring denominator, so `buildPaper` throws
  instead.

`prototype/app/data/examBanks.json` is item-for-item current with the corpus (6,048), guarded by
`validate_prototype_sync.py`.

### 2.7 Verdict on the brief's question

**Can the app run a full timed N5/N4/N3 simulation with scoring today? Partly — and the honest answer is
"two of three parts".** It runs 9 sections, both Language-Knowledge parts, real per-part clocks, the gap, an
uncarryable time budget, deterministic sampling, server-side grading, and a per-section score. It does **not**
run 聴解 (a third part, 24–28 questions/level), it does **not** produce a JLPT verdict, and two of its nine
sections rest on stitched non-passages. The exam picker page says as much to the learner, which is the right
call.

---

## 3. Gaps

Ordered by what blocks the most. **S** ≈ hours, **M** ≈ days, **L** ≈ a campaign.

### G1 — Reading passages are not passages (L · decided, unexecuted · AI-authorable)
**Missing.** 286 real short passages, 3–6 connected sentences on one topic, level-gated to each level's
cumulative known set, replacing the current concatenations. Owner decision A1 = (a), author them.
**Why it matters.** 文章の文法 tests a blank *the surrounding discourse* determines; 読解 tests comprehension
*of a text*. With no discourse there is nothing to test, and the questions degenerate — `rc:n5:n5-te-form-03-01`
asks where the cat is over a passage whose second sentence is unrelated, so a reader who connects them lands
on a wrong answer the passage neither supports nor excludes. This affects **473 items (187 `tg` + 286 `rc`) —
7.8% of the bank** and two of nine sections in every paper.
**Depends on.** Nothing. It is the *first* thing, because A2 (regeneration) must not bake the defect in.
**Who.** AI authors as Layer C `needs_review: true`; a teacher signs off before the section is called done.

### G2 — Bank regeneration on the fixed builder (L · owner said GO · AI-authorable)
**Missing.** The nine builder fixes enumerated in `research/reports/exam_bank_regen_review.md` §5.1, plus the
three the QA waves added (n3 linker matches written form and ignores reading — 135 items; `sentence_order`
chunked at bunsetsu not morpheme — 45 items admit a second ordering; homophone-set dedupe), then the
regeneration itself on **Option B**, then the four proposed validators (EB-V2 leak gate, EB-V3 okurigana,
provenance census, sufficiency).
**Why it matters.** ~1,700 flagged items ride on this and in-place patching does not scale. Measured on the
prototype builder: leaks 95→0, affix-solvable kanji-reading items 373→58, orthography length-mismatched
distractors 55%→2%, 9 placeholder distractors never ship. Regenerating *without* the fixes is a regression —
it strips `layer`/`needs_review` from all 5,182 deterministic items, drops 3,392 vocab slugs, and returns all
93 answer leaks.
**Depends on.** G1 (decided before regen), and a rebuildable `db/corpus.sqlite` — see Blockers.
**Who.** AI writes the builder and runs it; a teacher eyeballs the ~130 lost / ~210 gained / 35 answer-word
changes named in §5.2 step 9.

### G3 — Listening audio, and the picker's inability to render half the listening bank (M+S · blocked · mixed)
**Missing.** (a) 239 audio assets. (b) The section entries in `SECTIONS`/`PARTS` and a third timed part
(N5 30 / N4 35 / N3 40 min). (c) A fix to `present()`.
**Why it matters, concretely.** `present()` in `exam.server.ts` does `const prompt = it.question || it.stem ||
""; if (!prompt) return null;`. **110 of the 239 listening items — every `listening_say` (42) and every
`listening_reply` (68) — carry `question: ""` by design** (`design/listening.md`: "`question` is empty for
`ls:`/`lr:` — the format IS the question"). The day audio lands, those two whole 大問 return null, the
sections come out empty, `if (!questions.length) continue` drops them, and the paper is silently shorter with
a silently different denominator. The `placed !== total` guard does not catch a section that never entered
`sections`. This is a latent, verified, one-line-cause bug.
**Also.** No ≥3× gate covers listening; `n5_listening_reply` is 2.83× today and nothing fails.
**Depends on.** Owner voicing (see Blockers). (b) and (c) can land before the audio does.
**Who.** (a) owner. (b) and (c) AI.

### G4 — No JLPT scoring model (M · AI-authorable after an owner source decision)
**Missing.** Scaled scores per 得点区分, the sectional minimum bands, the overall pass mark, and a
pass/fail verdict. Today `gradePaper` returns raw right/total and a percentage — `design/exam_simulator.md`
rule 6 says "1 point/item; section + total percentages" and that is exactly what ships.
**Why it matters.** A learner preparing for a real sitting needs to know whether they would have *passed*,
and the JLPT can fail a candidate who clears the total but misses one section band. A percentage cannot
express that. This is the single largest "is it really a simulation" gap after listening.
**Depends on.** An owner call on the source, held to the same standard the timing note set (two independent
checks, dated, with the uncertainty stated).
**Who.** AI implements once the figures are agreed; the figures themselves are a sourcing decision.

### G5 — No attempt record: rules 2 and 5 of the picker are unimplemented (M · AI-authorable)
**Missing.** User identity, a stored attempt, and the two design rules that need it. `examPaper.tsx` calls
`buildPaper(level, seed)` and `gradePaper(level, seed, answers)` with **no `exclude` set** — the no-repeat
window (design rule 2) exists in the function signature and is never used. The seed is
`String(Date.now() % 100000)`, not `(userId, level, attemptNo)` (rule 5), so papers are neither user-scoped
nor collision-free. Results are ephemeral: `login.tsx` is a marketing page, and the only browser storage in
the prototype is the theme.
**Why it matters.** Less than it sounds for freshness — measured overlap between two independent papers is
~3.5% — but it means no score history, no progress curve, no "you have already seen this", and no way to
reproduce a learner's paper for support, which rule 5 exists to provide.
**Depends on.** The app backend (out of this repo's scope).
**Who.** AI.

### G6 — Results do not feed the capability tracker (M · AI-authorable)
**Missing.** A per-capability signal out of a graded paper. `corpus/capabilities/registry.json` holds 74
capabilities keyed by `grammar_keys`, and `lesson_map.json` maps 266 lessons; **nothing maps an exam item or
exam section to a capability.** The links exist to build it: every `gf` item carries a `grammar` key (all 728
resolve to taught grammar), every `kr`/`or`/`cf`/`pp`/`us` item carries a `vocab` slug, `so`/`lr` carry a
`sentence`, `rc`/`tg` carry a `reading`. Design rule 6 promises this feed ("feeds the capability tracker
(roadmap D) as right/wrong signals") and it is not wired.
**Depends on.** G5.

### G7 — No study mode over the exam banks (M · AI-authorable)
**Missing.** The untimed, immediate-feedback mode filtered to `lesson.cumulative_known_set` that
`design/exam_simulator.md` specifies. Nothing in `prototype/app/routes/` reads the exam banks except the two
simulator routes. The gating data is already there — every lesson carries a `cumulative_known_set` and 6,042
of 6,048 items resolve to a corpus record the course teaches (only **6** items, all `kr`/`or` at n5/n4, name a
vocab slug the course never unlocks).

### G8 — 264 mechanically-provable defects still in shipped items (M · mostly folded into G2)
Measured over the current export, four classes a script can prove:

| class | items | where |
|---|---:|---|
| same printed stem, **different keyed answer** (one of the two marks a right answer wrong) | **92** | n3_orthography 44, n4_orthography 16, n3_kanji_reading 6, n5/n4/n3 `cf`/`gf` 14, n5_kanji_reading 4, n4_kanji_reading 2, n4_paraphrase 2 |
| an option that is not a Japanese string (grammar-point label, leaked homograph index `①`, wave dash) | **54** | n5_grammar_form 27, n4_grammar_form 15, n5_text_grammar 9, n4_text_grammar 3 — strings `かか`, `よりほうが`, `たりたり`, `くらい ①`, `ずっと ①`, `以上 ①`, `てすみ`, `の中でが一番`, `のほうがより`, `まだていません`, `のがへたです`, `のがすきです` |
| `usage` where only the **key** lacks final punctuation (answerable without reading Japanese) | **34** | n3 19, n4 9, n5 6 |
| `paraphrase` where the key is strictly the **longest** option | **86** | n4 33, n5 28, n3 25 |
| **distinct items with ≥1 of the above** | **264 (4.4% of 6,048)** | |

The n5 orthography homophone groups the QA sweep named *were* repaired (21 items withdrawn) — **the same
defect class was left live at n4 and n3.** Examples still shipping: `n3_orthography` いし → keyed 医師 *and*
意志 *and* 意思 over an identical option set; n4 たずねる → 尋ねる *and* 訪ねる; n5 side 得る → うる *and* える.
Each of these is unanswerable in principle, and if two members of a group land in one paper the learner is
marked wrong on one of them.
**Also fixed and worth recording:** `lt:n5:004`'s in-group error is repaired (the script now reads 兄, not
お兄さん), and `INDEX.md` no longer lies about any count.

### G9 — `sentence_order` is graded by exact string equality (M · needs a teacher for the edge cases)
Grading is `norm(given) === norm(expected)` with whitespace stripped. Japanese scrambling means a second
ordering is often equally correct — the QA sweeps proved 23 such items at n5, 15 at n4, 7 at n3, and the
frozen advisory `sentence_order_ambiguous` counts only the narrower case where the *same chip order* respells
the answer (1 item). Additionally, all 871 `answer` strings have punctuation stripped, so the "correct
sentence" the learner is shown at review is never well-formed written Japanese. Bunsetsu chunking (G2)
removes most of the ambiguity; the symmetrical-coordination set (「電車よりバスのほうが安い」 ↔ its mirror)
cannot be repaired by chunking and needs either a locked ★-slot prompt or removal.
**One live duplicate:** `n3_sentence_order` still holds two items with identical `pieces` and `answer`
(今月あのスーパーは水曜日が休みです). The two n4 duplicates were withdrawn; this one was not.

### G10 — Two sections of the real reading paper do not exist at all (L · AI-authorable)
Mid/long passages (中文・長文) and information retrieval (情報検索) are in every real N3+ paper and in no bank.
`design/exam_simulator.md` lists them under "known gaps"; current `reading_comp` is 短文-style
single-question passages only. Passage token counts confirm the ceiling: n3 passages median 62 tokens, max 91.

### G11 — Provenance semantics: two defensible readings of `ai_generated`, and one real leak (S · AI-authorable)
`contracts/common.schema.json` defines `ai_generated` as "the content itself was produced by a model rather
than selected from a human-written source." All 286 `reading_comp` items carry `ai_generated: false` while
their questions and distractors are model-authored (QA sweep 3 F11, 266 items). **The migration is right and
the contract text is wrong-by-omission:** `migrate_exam_banks_p7.py` documents the operational meaning — "the
JAPANESE the learner reads was model-generated" — and the picker's real-first rule depends on exactly that;
overloading the field would erase the real-vs-generated distinction inside the authored banks. Fix the
*description*, or split into `jp_generated` + `authored`.
**The actual leak, separately:** all 286 passages are `needs_review: true`, but the **187 `text_grammar`
items built on them are `needs_review: false`** (Layer B, mechanical blanking). An unreviewed passage
produces an item the review queue treats as signed off. That is a contract gap worth a gate.

### G12 — No validator forbids two items with the same printed question and different keys (S · AI-authorable)
`validate_exam_banks.py` checks option-set distinctness *within* an item; nothing checks contradiction
*across* items. G8's 92 items would have been caught at build time by a five-line check. Add it as a hard
gate with the current count as a shrinking ratchet.

### G13 — Address inconsistency on `grammar` refs (S · AI-authorable)
Exam items reference grammar by the bare `key` (`"tai"`), while the rest of the corpus publishes
`gram:tai`. The validator accepts both deliberately, so nothing is broken — but a consumer must know to try
two forms, which is the class of thing `validate_stable_addresses.py` exists to prevent for integer FKs.

### G14 — N2 / N1: nothing (L · reverses a standing owner directive)
**What exists.** Bank-only kanji and vocab: **kanji n2 368 / n1 1,133**, **vocab n2 1,768 / n1 2,679**, every
record `needs_review: true` with low `level_confidence`, and **pt-BR glosses deferred — English only**
(`design/n2_n1_bank.md`). There are also **1,243 fully-dissected N2/N1 sentences** in
`corpus/sentences/bank.json` (n2 722, n1 521, all with tokens and pt-BR translations) — more than
`design/n2_n1_bank.md` claims, which says `SELECT … WHERE level IN ('n2','n1')` on `sentence` returns 0. **The
data is right; that line in the doc is stale.**

**What is missing, per exam section:**

| section | what it needs | N2/N1 status |
|---|---|---|
| `kanji_reading`, `orthography` | vocab records with readings/forms | **have it** — buildable today |
| `context_fill`, `sentence_order` | dissected bank sentences at level | **partial** — 1,243 sentences vs 445–2,204 per shipped level; thin, and never level-curated |
| `grammar_form`, `text_grammar` | a grammar registry | **zero** — `corpus/grammar/` has only n5/n4/n3 (151/213/132 records) |
| `reading_comp`, `text_grammar` | passages | **zero** — `corpus/readings/` has only n5/n4/n3 |
| `paraphrase`, `usage` | authored Layer-C items | **zero** |
| all five `listening_*` | authored scripts + audio | **zero** |
| paper structure | N1/N2 **merge** 文字・語彙 and 文法・読解 into one part — `PARTS` in `exam.server.ts` stops at N3 for exactly this reason, and `LEVELS`/`ORD` in `build_exam_banks.py` are `("n5","n4","n3")` | **zero** |
| course linkage | "you also meet this in a lesson" | **zero** — `course/` has pre-n5, n5, n4, n3 only |

The blocking item is not effort, it is scope: the owner directive of 2026-06-25 recorded in
`design/n2_n1_bank.md` says N2/N1 are **"kanji/vocab banks only — no sentences, no grammar, no deep
explanation, no lessons."** An N2/N1 simulation requires reversing that. Two of the nine sections
(`kanji_reading`, `orthography`) could be built inside the existing directive; the other seven cannot.

---

## 4. Quality risks against the near-100% goal

These are things that could still be **wrong in shipped material**, ranked by how likely a learner is to hit
them and how much damage each does.

1. **The QA waves flagged 1,757 of 5,898 items checked (29.8%), and almost none of it has been repaired.**
   Reconciled per report: `exam_japanese_1.md` 2,488 checked / 635 flagged (all n5 + n4 `kr`/`or`);
   `exam_japanese_2.md` 1,149 / 230 (n4 `cf`/`gf`/`so`/`tg`/`pp`/`us`); `exam_japanese_3.md` 2,261 / 892
   (all n3). The three slices sum to 5,898 of the 6,073-item snapshot they ran against — the 175 items never
   swept are `n4_reading_comp` (91) and the four `n4_listening_*` banks (84). Those 175 are an unaudited
   surface, and `n4_reading_comp` inherits the G1 non-passage defect by construction.
2. **Items that mark a correct answer wrong.** The 92 contradictory-key items (G8) are the worst class in a
   multiple-choice bank: not "a bit easy", but *the learner is right and the app says no*. Probability that
   one paper draws two members of the same group is small — 0.47% at n3 orthography (21 groups, 25
   within-group pairs, 6 items drawn from 400) — but **every single draw from a group is an unanswerable
   question**, and 44 of that bank's 400 items sit in one.
3. **Answerable-without-Japanese items.** The frozen advisories quantify a known population that is
   *individually correct but gameable*: 373 okurigana-shape-solvable `kanji_reading` items, 300+241
   orthography shape/length giveaways, 32 `reading_comp` items answerable by scanning for the verbatim
   string. Add the 34 punctuation-keyed `usage` items and 86 longest-option `paraphrase` items from G8. A
   score inflated by shortcuts is worse than a low score, because it is acted on.
4. **Non-Japanese strings printed to learners.** 54 items show an option like `よりほうが` or `くらい ①`. These
   are not merely eliminable — they teach a non-word, and they are the visible tip of a builder bug (options
   rendered from a pattern label rather than `forms[].form`).
5. **Register and content.** `exam_japanese_1.md` F16 names slang, thieves' argot, Kansai dialect, お前ら, a
   vulgar interjection, and a hemorrhoids item inside a beginner bank — none of it filtered, because
   selection is mechanical and there is **no sentence-level `register` field in the corpus** (PENDING A8's
   own update says the filter "cannot be built yet" for exactly this reason). Whatever is in the sentence
   bank can surface in an exam.
6. **1,248 `needs_review: true` items have never been reviewed by a teacher**, including all 891 Layer-C
   items (the entire `paraphrase`, `usage`, `reading_comp` and `listening_*` surface). Spec §1.1 makes that
   review mandatory, not optional. "AI-authored now, teachers validate later" is the plan; the queue is
   currently 1,248 deep with no reviewer assigned.
7. **The paper structure's item counts are asserted, not sourced.** The timing table carries a dated,
   two-source verification and an admirable note about what JEES does *not* publish. The **section item
   counts** in the same document carry no such note — they are stated as "Item counts follow the real exams"
   with no source and no date. Given how carefully the timing was handled, the counts are the weaker claim in
   the same table and should be held to the same standard before the app calls a score a JLPT estimate.
8. **Regeneration risk.** `build_exam_banks.py` reads `db/corpus.sqlite` — 202 MB, git-ignored, absent from a
   fresh clone. The whole G2 campaign, and any future rebuild, depends on that index being reproducible from
   the committed JSON, and **no validator asserts it can be**.
9. **A silent shortening path exists in the picker.** `if (!questions.length) continue;` drops a whole
   section without failing. Today no non-listening section can hit it; G3 shows it fires for two listening
   sections the moment they are enabled. It should throw, like the orphan-section guard four lines below it
   already does.
10. **Cosmetic but real:** `shuffle(p.pieces, rand)` has no identity-reshuffle guard, though
    `design/exam_simulator.md` rule 3 requires one ("reshuffle if identity order"). Measured exposure is
    small — P(a paper contains a pre-solved ordering item) = 1.1% at n5, 0.7% n4, 0.5% n3 — but it is a
    stated rule the code does not implement.

---

## 5. Recommended sequence

The ordering constraint that matters: **G1 before G2**, because regeneration bakes the passage defect in, and
both before any further per-item repair, because ~1,700 flagged items are downstream of the builder.

| # | Work | Size | Why here |
|---|---|---|---|
| 1 | **G1 — author 286 real passages** (Layer C, `needs_review`, level-gated to each level's cumulative known set). Re-derive `rc` questions and re-blank `tg` at token boundaries over the new texts. | L | Decided; blocks G2; unblocks the only two structurally-invalid sections. |
| 2 | **G12 + the G8 quick wins** — land the cross-item contradiction gate (ratchet at 92) and the non-Japanese-option gate (ratchet at 54) *before* the regen, so the rebuild has to beat them rather than re-argue them. | S | Cheap, and turns two QA findings into gates instead of prose. |
| 3 | **Prove `db/corpus.sqlite` is rebuildable from the committed JSON**, and add a validator for it. | S | Silent prerequisite of everything in G2. |
| 4 | **G2 — the twelve builder fixes, then regenerate on Option B**, then the four proposed validators, then re-export the prototype bank. One atomic commit, per §5.2 of the regen review. | L | Clears the largest repair queue in the project. |
| 5 | **G3(b)(c) — wire listening into `SECTIONS`/`PARTS` behind an audio-present check, fix `present()` for the 110 empty-`question` items, extend `PAPER_COUNTS` to the listening banks, and make an empty section throw.** | S | Do it *before* the audio exists, so the day audio lands nothing is silently short. |
| 6 | **G4 — the JLPT scoring model.** Source the bands and the pass mark to the same standard as the timing note; implement scaled scoring, sectional verdicts, and a pass/fail result. | M | Biggest remaining "is this a simulation" gap that does not need audio. |
| 7 | **G3(a) — voice the 239 scripts** and flip `audio: "pending"`. Fix the `n5_listening_reply` shortfall (17 → 18) in the same pass. | M | Owner-gated; everything else is ready for it. |
| 8 | **G5 → G6 → G7** — attempt record, then the capability feed, then study mode. | M each | Each needs the one before it; none blocks exam correctness. |
| 9 | **Teacher review of the 1,248 `needs_review` items**, starting with the 891 Layer C. | L | The spec makes this mandatory; it is the only step that can move this area from "verified by machine" to "signed off". |
| 10 | **G9 (acceptability grading), G10 (中文・長文・情報検索), G13, and the doc corrections** (4,359 → 6,048; delete the ≥240 claim; 6,166 → 6,048; the 93 → 118 removed-items line in the validator README; the stale N2/N1-sentences line in `n2_n1_bank.md`). | S–L | Cleanup and coverage, once the structural work has landed. |
| 11 | **G14 — N2/N1**, only after an explicit owner reversal of the bank-only directive. Buildable inside the current directive: `kanji_reading` + `orthography` at N2/N1 (~2 sections of 14). Everything else needs a grammar registry, passages, curated sentences, listening scripts, and the merged N1/N2 paper structure — i.e. it is a level-sized project, not an exam-sized one. | L | Correctly last; the shipped levels are not finished. |

---

*Every count in this report was recomputed from the export on 2026-09-02 with read-only scripts under the
session scratchpad. `validate_exam_banks.py` was run unmodified and reported `6048 items in 40 banks, ALL OK`.*
