# Readiness — content coverage per level

> Area: `content_coverage_levels`. Written 2026-09-02 against the committed export at `48d5459a`.
> Every number below was recomputed from `corpus/` and `course/` JSON by script, not quoted from a
> document. Where a design doc and the data disagree, the data wins and the disagreement is named.
> `db/corpus.sqlite` was read only to size the un-ingested Tatoeba pool, which lives nowhere else.

**Headline.** N5 and N4 are essentially complete and defensible. N3 has a registry, a grammar set, 101
lessons and 2,260 exam items, but almost no *exemplification*: **135 of its 1,596 vocabulary records
(8.5%) appear in a single sentence anywhere in the corpus**, against 92.6% at N5 and 94.9% at N4. All
286 reading passages — and the 473 exam items built on them — are concatenations of unrelated Tatoeba
sentences. N2 and N1 are bank-only by an explicit owner directive and are correctly scoped as rows,
not schema. The good news is that the N3 hole is a *selection* problem, not an authoring one: 96% of
the under-covered items already have real human-written candidate sentences sitting in the ingested
Tatoeba tables, and the pipeline that would harvest them already exists and has been run before.

---

## 1. What this capability needs from the data

"Content coverage per level" is the promise that a learner who finishes level *L* has met everything
level *L* is supposed to contain, with enough material to actually learn it. Concretely that means:

| Need | Entity / field | Why the learner cares |
|---|---|---|
| A complete inventory per level | `kanji`, `vocab`, `grammar` rows with `level` | The syllabus is the product's core claim |
| Auditable level claims | `level_confidence`, `level_agreement`, `level_sources` (spec §1.5) | There is no official JLPT list; a bare `level` is an assertion |
| Enough examples to induce meaning | ≥3 dissected sentences per vocab, ≥5 per grammar point (spec §7, §10, `STATE.md` thresholds) | One example teaches a collocation, not a word |
| Real language first | `provenance.jp_source` = a Tatoeba/JEC id, not `ai-generated` (spec §1.2) | Generated sentences drift toward textbook Japanese |
| Reachability | lesson `sentence_refs`, `unlocks`, exam `sentence`/`reading` refs | A bank nothing references teaches nobody |
| Extended reading | `corpus/readings/*.json` that are actually connected texts | Reading comprehension is a JLPT section and a real skill |
| Assessment supply | `corpus/exam_banks/*.json` at ≥3× paper counts | A simulator that repeats items measures memory of the app |
| Level-appropriate difficulty | sentence `level` ≤ lesson level; the i+1 budget | Above-level examples are noise, not input |
| Level-agnostic structure | spec §1.6 — adding N2/N1 is inserting rows | Otherwise every new level is a migration |

A level is **complete** only when the data, the contract and a validator for it all exist. That last
clause does most of the work in this report.

---

## 2. What exists today

### 2.1 The registry, by level (verified counts)

| entity | pre-N5 | N5 | N4 | N3 | N2 | N1 | total |
|---|---|---|---|---|---|---|---|
| kanji | — | 103 | 177 | 350 | 368 | 1,133 | **2,131** |
| vocab | — | 705 | 653 | 1,596 | 1,768 | 2,679 | **7,401** |
| grammar | — | 151 | 213 | 132 | — | — | **496** |
| sentences | — | 445 | 2,204 | 1,997 | 722 | 521 | **5,889** |
| readings | — | 43 | 91 | 152 | — | — | **286** |
| conjugation paradigms | — | 213 | 295 | 649 | — | — | **1,157** |
| exam items (live) | — | 1,667 | 2,121 | 2,260 | — | — | **6,048** |
| conjugation drills | — | 3,072 | 4,853 | 10,599 | — | — | **18,524** |
| role drills | — | 239 | 2,409 | 2,710 | — | — | **5,358** |
| stroke orders | — | 103 | 177 | 350 | 357 | 246 | **1,233** |
| topics / lessons | 6 / 41 | 14 / 84 | 17 / 96 | 15 / 101 | — | — | **52 / 322** |

All five brief figures reconcile exactly: kanji 2,131, vocab 7,401, grammar 496, sentences 5,889,
readings 286. Sources: `corpus/*/n*.json`, `corpus/sentences/bank.json`, `course/manifest.json`.

The courseware teaches **2,946 vocab, 634 kanji, 496 grammar** (`audit_coverage.py`: placed = unlocked,
gap 0, no duplicates). **4,455 vocab and 1,497 kanji rows are registry-only** — almost all N2/N1, plus
nine taught-level vocab held in `course/coverage_exemptions.json` with per-record reasons.

A second path exists alongside the JLPT ladder: `course/speak/` holds **12 stages × 6 units = 72
speaking units** (`design/speaking_path.md`), gated on the vocabulary known set rather than on level.

### 2.2 Sentence provenance — real vs generated

| | N5 | N4 | N3 | N2 | N1 | total |
|---|---|---|---|---|---|---|
| real (Tatoeba 3,549 + JEC 127) | 350 | 1,527 | 1,223 | 302 | 274 | **3,676 (62.4%)** |
| `ai-generated` | 95 | 677 | 774 | 420 | 247 | **2,213 (37.6%)** |

Spec §1.2 ("prefer SELECTION over GENERATION") is being honoured at N5 (79% real) and less so at N4
(69%) and N3 (61%). Every sentence carries `needs_review: true` and `tier: "full"`; `pt_source` is
`ai` on all 5,889, validated against a dictionary (2,684) or the English anchor (3,205). 5,871 of
5,889 carry an English anchor. Guarded by `validate_provenance_json.py` (hard).

The **mined-stage pipeline** is real, documented and proven, but has run exactly once. `scripts/ingest/
mine_tatoeba_stages.py` selects candidates from the 248,705-row `raw_tatoeba_sentence` table under a
stated filter (stage seed, has an English pairing, ≤34 chars, ≤6 kanji, every kanji already taught at
N5–N3, not already in the bank); an authoring plus two-reviewer workflow adds pt-BR; `ingest_mined_
stages.py` dissects and persists with three structural invariants re-checked per row and a documented
dry-run caveat. It produced **324 sentences for exactly three speak stages** (`lodging` 111,
`opinions` 108, `past_stories` 105), all real, all still tagged `mined`. The other nine stages, and
the entire N3 vocabulary gap, have never been put through it.

### 2.3 Level evidence (spec §1.5)

10,028 records carry a level claim. `validate_level_consensus.py` gates presence, range, well-formedness
and source shape, and freezes the rest as ratchets.

| | records | confidence 1.0 | weak (≤0.5) | cites <3 lists |
|---|---|---|---|---|
| kanji | 2,131 | 1,966 | 162 @ 0.25 + 3 sentinels | 167 |
| vocab | 7,401 | 1,352 | 6,042 @ 0.34 | 6,144 |
| grammar | 496 | 353 | 143 | 443 |

Per level the picture is much sharper than the totals suggest:

- **Kanji** is strong everywhere the course teaches: ≥3 agreeing lists on 99.0% of N5, 99.4% of N4,
  98.3% of N3. The 162 weak records are 149 N1 + 13 N2 at agreement `1/4`.
- **Vocab N5/N4** is strong — 644/705 and 606/653 at four-list agreement.
- **Vocab N3 rests on one list.** All 1,596 records carry `level_sources: {"bluskyo": "n3"}`,
  agreement `1/3`, confidence 0.34.
- **Vocab N2/N1 rests on one *collapsed* key.** All 4,446 records carry
  `level_sources: {"jlpt-lists": "n1"|"n2"}`. `jlpt-lists` is not the name of a list; it is the union
  of three, flattened. `contracts/common.schema.json` → `LevelSources` says the shape is
  "{list_name: level} … everything else is a list name and its value is a Level", so this passes the
  validator while defeating the audit the field exists for: you cannot tell which list placed the word
  or whether they disagreed.
- **Grammar N3 rests on one list** (`hanabira`, 132 records).

**The A4 contradiction, precisely located.** Applying the contract's own formula (`level_confidence` is
"derived from level_agreement", numerator over denominator, tolerance 0.02) to all 10,028 records
leaves exactly **132 violations, and they are all of N3 grammar**: agreement `1/1` paired with
confidence 0.34. The other 4 flagged records are documented sentinels. This matters for the fix
direction: PENDING A4 was approved as "restate the formula, recompute", but a naive recompute would
read `1/1` and raise those 132 to **1.0**, converting the single weakest level evidence in the corpus
into a claim of certainty. The intent is legible from the data — 0.34 ≈ 1/3, and
`design/n3_extension_assessment.md` condition 1 says the ≥3-list rule "is not satisfiable from open
data for N3 vocab or N3 grammar". The correct repair is to fix the **agreement string** to `1/3`
(three lineages consulted, one had an opinion) and leave the confidence alone. The 6,042 vocab records
at `1/3` @ 0.34 are already consistent under that reading and need no change.

### 2.4 Sentence coverage against the spec thresholds

**Vocabulary — ≥3 dissected sentences (spec §7 / §10):**

| level | taught | ≥3 sentences | below 3 | zero | of which link-gap | of which truly absent |
|---|---|---|---|---|---|---|
| N5 | 699 | **644 (92.1%)** | 55 | 51 | 49 | 2 |
| N4 | 650 | **611 (94.0%)** | 39 | 33 | 32 | 1 |
| N3 | 1,596 | **25 (1.6%)** | 1,571 | 1,461 | 707 | 754 |
| **total** | 2,946 | 1,281 (43.5%) | 1,665 | 1,545 | 788 | 757 |

"Link-gap" means the word's surface or kana **does occur** in a bank sentence but no token was linked
to that record — an orthography/tokenisation miss, not missing content. Nearly the whole N5/N4
shortfall is of this kind: 49 of 51 and 32 of 33. The offenders are counters and okurigana variants
(一つ, 二つ, ９日, 詰らない/つまらない, 許り/ばかり, 其れから/それから) and function words (でも, では, だから, 程).

Seen from the other side: **only 1,449 distinct vocab records are linked in the entire 5,889-sentence
bank** — 653 N5, 620 N4, **135 N3**, 18 N2, 23 N1.

**Grammar — ≥5 dissected sentences:**

| level | points | ≥5 sentences | below 5 | zero |
|---|---|---|---|---|
| N5 | 151 | **136 (90.1%)** | 15 | 0 |
| N4 | 213 | **197 (92.5%)** | 16 | 0 |
| N3 | 132 | **65 (49.2%)** | 67 | **17** |

The 17 with nothing at all are all N3: `n3-kara-ni-kakete`, `n3-kiri`, `n3-koto-da`, `n3-koto-wa-ga`,
`n3-kurai-wa-nai`, `n3-mattaku-nai`, `n3-moshi-tanara`, `n3-moshi-temo`,
`n3-moshikasuru-to-kamoshirenai`, `n3-ni-kawatte`, `n3-ni-shitemo`, `n3-sa`, `n3-sore-to`,
`n3-sukoshimo-nai`, `n3-tatoe-temo`, `n3-tokoro-ga`, `n3-tokorode`.

**Kanji:** 40 of 634 taught kanji have zero `example_sentences` (39 N3, 1 N2); 454 have the full six.

**Why N3 specifically.** Classifying the 1,997 N3-level sentences by the tag that caused them to be
built: 338 selected for a grammar topic, 247 generated for grammar coverage, 400 selected for
coverage, 526 generated for *vocab* coverage — but those 526 carry `coverage:n4`/`coverage:n5` tags.
They were built to exemplify **N5 and N4** words and merely graded N3 because they contain one harder
word. **No vocabulary-coverage campaign was ever run for N3.** That single omission is the whole gap.

### 2.5 Reachability

91.5% of the bank (5,386 of 5,889) is referenced by something a learner can reach: exercises 3,449,
kanji examples 2,593, exam banks 1,934, readings 1,314, speak 752, lessons 605. **503 sentences are
orphans** (252 N4, 149 N3, 57 N2, 34 N1, 11 N5; 329 of them AI-generated).

Lessons are the thin surface: **624 sentence links across 322 lessons, and 116 lessons display no
sentence at all** — 41 pre-N5 (kana and phonetics, legitimately), 15 N5, 12 N4, and **48 of 101 N3**.
N3 lessons carry 96 sentence links between them, fewer than one each.

Of those 624 links, **178 point at a sentence graded above the lesson's own level** and 147 exceed the
per-level i+1 budget — exactly the frozen counts in `research/reports/lesson_sentence_baseline.json`.
Six N5 lessons show N1 sentences (`嵐のきざしがある。` in an N5 particles lesson; `諦めないで。`).

### 2.6 Readings, and the exam sections built on them

**All 286 readings are byte-exact concatenations of their `source_slugs`.** I reconstructed each
reading by joining its source sentences and comparing after punctuation stripping: 286 of 286 match
exactly, 0 partial. Example `read:n3-causa-01-01`, titled *"A árvore me salvou da chuva"*:

> 木のおかげで雨にぬれずにすんだ。それはわたしのせいではなかった。風が強いのはビル風のせいです。私がいるのは父のおかげです。おかげで元気にしております。

Five unrelated Tatoeba sentences whose only common property is おかげで/せいで. The title describes the
first clause and misdescribes the other four. `read:n5-adjetivos-04-01` is 「どこに行くところですか。
ありがとうございます！」 — a question and an unrelated thank-you, titled "Aonde você está indo".

This is the same defect PENDING A1 raises for exam passages, and it is **larger than A1 states**,
because it is the readings corpus itself and everything downstream inherits it:

- **286 readings** — the entire reading-practice feature.
- **286 `reading_comp` exam items**, exactly one per reading (43 / 91 / 152, a 1:1 map), each with an
  authored question and three distractors about a text that has no discourse.
- **187 `text_grammar` exam items**, whose `stem` is the same concatenation with one blank cut into it:
  `外は（　）明るくなっていく。カメラは持っていくのですか。町を通っていく。試していく。`

`validate_exam_banks.py` also reports that **187 of the 286 passages serve both sections**, so one
simulated paper can show a learner the same text twice.

`validate_readings.py` is a hard gate, and it is a *readability* gate: every kanji and content word
must sit inside the gating lesson's cumulative known set (max_new = 0), plus translation and em-dash
hygiene. Nothing checks that a reading is a text. 265 of 286 are built purely from real sentences, 19
mix in AI-generated ones and 2 are entirely generated, yet all 286 record `ai_generated: false`.

### 2.7 What guards what

| claim | validator | gate |
|---|---|---|
| placement = unlocks, no gaps/dupes | `audit_coverage.py` | hard |
| per-level counts inside sanity bands | `audit_jlpt_coverage.py` | hard (N5/N4/N3 only) |
| level evidence shape and consistency | `validate_level_consensus.py` | hard, L4–L6 frozen |
| exam banks ≥3× paper counts, keys sound | `validate_exam_banks.py` | hard |
| readings inside the known set | `validate_readings.py` | hard |
| lesson→sentence i+1 budget | `validate_lesson_gating.py` | **frozen ratchet** |
| taught-level stroke coverage | `validate_stroke_integrity.py` | hard |
| ~555k graph edges | `validate_graph_edges.py` | hard |
| spec §1.7 queries | `graph_queries.py` | hard, Q1 and Q4 waived |
| **≥3 sentences/vocab, ≥5/grammar** | `completeness_audit.py` | **advisory — never gates** |

That last row is the structural finding. The acceptance thresholds this whole area is measured against
have **no hard validator**, and the one script that measures them reads `db/corpus.sqlite` — which
`CLAUDE.md` explicitly designates a regenerable index rather than the source of truth. Its own output
(`vocab w/ >=3 dissected sentences: 1467/7401`) has been printing the problem into an advisory
column for the whole build.

### 2.8 Where documents disagree with the data

1. **`design/n2_n1_bank.md`** states N2/N1 pt-BR meanings are "deferred … currently carry only the
   Layer-A English meaning". **False now:** 100% of vocab senses at every level carry a non-empty
   `gloss["pt-BR"]` (n2 2,379/2,379; n1 3,923/3,923), and 100% of kanji carry `meanings["pt-BR"]`
   (368/368 and 1,133/1,133). The backfill landed; the doc did not.
2. **The same doc** states "`SELECT … WHERE level IN ('n2','n1')` on `sentence`/`grammar_point` = 0".
   Grammar is still 0, but **1,243 sentences carry level n2 or n1** (722 + 521). They are by-product
   classifications, not N2/N1 teaching material — 394 are tagged `coverage`, 268 `coverage:n4`, 126
   `coverage:n5` — i.e. sentences built for N5/N4 that graded up because of one hard word. That is
   itself the mechanism behind the 178 above-level lesson links in §2.5.
3. **`STATE.md` (entry `ac033368`)** says 140 of 286 readings have real titles and "the rest still show
   'Leitura'". **Stale:** grep finds zero occurrences of `"Leitura"` across `corpus/readings/*.json`;
   all 286 have authored titles. Commit `f8ea9647` finished it and STATE was not updated.
4. **`design/jlpt_alignment_plan.md`** records current state as kanji N5=80/N4=173/N3=364. The re-tag
   has since executed: the data is 103/177/350. The plan reads as pending work that is in fact done.

---

## 3. Gaps

### G1 — N3 vocabulary has no example sentences · **L** · depends on: nothing · AI-authorable now
1,461 of 1,596 taught N3 vocab have zero linked sentences; 1,571 are below the ≥3 threshold; only 135
appear anywhere in the bank. **Learner impact:** an N3 lesson unlocks a word, issues an FSRS card, and
can show the learner no sentence containing it. Half the N3 lessons show no sentence at all. This is
the difference between a syllabus and a course.
**Why it is smaller than it looks:** I measured the supply. Of the 1,665 under-covered items,
**568 reach ≥3 by re-linking sentences already in the bank** (§2.4), and of the 1,097 that genuinely
need new sentences, **673 have ≥3 candidates already in `raw_tatoeba_sentence`** under the existing
strict miner filter (pool: 112,723 unused rows that pass it; 229,173 with an English pairing overall).
So the split is roughly 568 mechanical / 673 selection / 424 harder. Spec §1.2 is satisfiable.

### G2 — Orthographic link gaps suppress N5/N4 coverage · **S** · depends on: nothing · AI-authorable
788 of the 1,545 zero-coverage records occur in the bank text but were never linked — counters,
okurigana variants, function words. Fixing the linking alone lifts **568 records** over the ≥3
threshold: N5 from 644/699 to 694/699 (99.3%) and N4 from 611/650 to 645/650 (99.2%). **Learner
impact:** small per word, but it is the cheapest coverage in the project and it also unblocks honest
measurement of G1. Do this first, then re-measure, or G1 will be sized against a false baseline.

### G3 — All 286 readings are concatenations, not passages · **L** · depends on: owner A1 (decided) · AI-authorable, teacher-validated
Includes the 286 `reading_comp` and 187 `text_grammar` exam items built on them, and the 187 passages
double-served across both sections. **Learner impact:** the reading-comprehension feature and two exam
sections cannot test what they claim to; a learner who can parse every sentence still cannot answer a
discourse question, and will conclude the fault is theirs. A1 is already decided in favour of authoring
real passages, so this is execution: ~286 short Layer C texts written from each gating lesson's known
set, `needs_review: true`, with the exam items regenerated against them.

### G4 — 17 N3 grammar points have no example; 67 are below ≥5 · **M** · depends on: G1 pipeline · AI-authorable
Same campaign as G1, different target list. N5 (90.1%) and N4 (92.5%) are already at threshold; N3 sits
at 49.2%. **Learner impact:** a grammar point with fewer than five examples teaches a template, not a
pattern; with zero it teaches nothing but its own name.

### G5 — N3/N2/N1 level tags rest on a single list · **M** · depends on: owner source decision · needs owner
1,596 N3 vocab on `bluskyo` alone; 4,446 N2/N1 vocab on the collapsed `jlpt-lists` key; 132 N3 grammar
on `hanabira`. Spec §1.5 mandates ≥3 independent lists. `design/n3_extension_assessment.md` raised this
as condition 1 for the N3 GO and it was never formally closed. **Learner impact:** a word taught at the
wrong level is either wasted effort or a cliff, and today nothing would detect it. The collapsed
`jlpt-lists` key is the sharper problem: it passes `validate_level_consensus.py` while making the
per-record evidence unauditable, which is precisely what the field exists to prevent. Either license a
genuinely independent third lineage, or formally relax §1.5 for these levels in
`design/schema_v2.md` — but write it down either way.

### G6 — 132 N3 grammar records carry a contradictory confidence pair · **S** · depends on: G5 wording · needs owner sign-off on direction
Approved as A4. The repair is one script, but the **direction is load-bearing**: fix the agreement
string to `1/3`, do not recompute confidence from `1/1`. See §2.3. Retires the L4 ratchet.

### G7 — 116 of 322 lessons display no sentence · **M** · depends on: G1, G2 · AI-authorable
48 N3, 15 N5, 12 N4 (the 41 pre-N5 are legitimate). **Learner impact:** a lesson that explains a
pattern and then shows nobody using it is a grammar reference, not a lesson. Purely downstream of
supply: re-run the lesson sentence selector once G1/G2 land.

### G8 — 178 lesson→sentence links are above level; 147 breach the i+1 budget · **M** · depends on: G1, G2 · AI-authorable
Frozen in `lesson_sentence_baseline.json`; offender list already written to
`lesson_sentence_review.json`. **Learner impact:** above-level input is noise. Cannot be repaired by
re-selection until there is a wider pool to re-select from, which is G1.

### G9 — 43 taught vocab have no real candidate sentence anywhere · **S** · depends on: G1 · AI-authorable
39 N3, 3 N4, 1 N5 return zero candidates from 229,173 Tatoeba rows. These are the legitimate
generation cases under spec §1.2's last-resort clause: author i+1 Japanese, flag
`ai_generated`/`needs_review`, dissect through the same path.

### G10 — N2/N1 are bank-only; 2,072 inflecting words have no paradigm · **L** if promoted, **S** if scope holds · depends on: owner scope decision · needs owner
Today N2/N1 have kanji, vocab, pt-BR meanings, and partial strokes — no grammar, no conjugations, no
readings, no exams, no lessons, no sentences of their own. That matches the 2026-06-25 directive
exactly, so it is not a defect. But the product statement says "zero -> N5 -> N4 -> N3 ...", and
`validate_graph_edges.py` already prints the consequence: *2,072 inflecting words at levels the bank
does not cover*. **What N2/N1 would need is rows, not schema** — spec §1.6 holds up under inspection:
`Level` already enumerates n2/n1, every export path emits them, 4,447 vocab and 1,501 kanji rows are
already there with pt-BR. The missing rows are roughly: ~400 grammar points, ~2,000 conjugation
paradigms, ~2,500 kanji-example links, a sentence bank sized to ≥3/word, ~200 readings, ~4,000 exam
items, and the courseware. Also **887 of 1,133 N1 kanji lack stroke order** (advisory today because
they are untaught; a hard failure the day one is taught).

### G11 — Cumulative vocab sits at the floor of its own band · **M** · depends on: G5 · needs owner/teacher
`design/jlpt_alignment_plan.md` targets cumulative vocab of ~800 / ~1,500 / ~3,700. Actual: 705 /
1,358 / 2,954. `audit_jlpt_coverage.py` passes because `VBANDS` for N3 is `[2600, 3800]` — its own
cumulative count of 2,909 sits 309 above the floor and 891 below the ceiling. The gate is green and the plan's own stated gap
(+745 at N3) is unclosed. Not a defect; a decision that has been deferred by band width.

### G12 — No hard validator for the coverage thresholds · **S** · depends on: nothing · AI-authorable
The ≥3/vocab and ≥5/grammar acceptance criteria are measured only by `completeness_audit.py`, which is
advisory and reads the SQLite index rather than the export. Every other invariant in this project has a
hard gate over `corpus/`. Write `validate_sentence_coverage.py` over the exported JSON as a **frozen
ratchet** (like `validate_lesson_gating.py`): today's counts are the ceiling, growth fails, shrinkage
lowers the baseline. Do this *before* G1, so the campaign has a scoreboard it cannot game.

### G13 — 503 orphan sentences · **S** · depends on: nothing · AI-authorable
Referenced by no lesson, exercise, exam, reading or speak unit; 329 are AI-generated. Either wire them
into the selectors (many will serve G1 directly) or retire them, but they should not sit in a bank
that reports 5,889 while delivering 5,386.

---

## 4. Quality risks against the near-100% goal

**R1 — N5/N4 coverage is measured, N3 coverage is asserted.** The gate is green at N3 and the data is
not there. Nothing in the hard suite would have told you; `audit_jlpt_coverage.py` checks that taught
items exist, not that they are exemplified. Anything that reports "N3 complete" today is reporting
placement, not teachability.

**R2 — A green gate has been read as a green product.** Four documents in this repo disagree with the
data they describe (§2.8) and all four disagree in the *pessimistic* direction except one. Two describe
finished work as pending; one describes a shipped defect as absent. Cheap to fix, but it means
document-derived status reports are unreliable and this report's method — recompute everything — should
be the default for the remaining readiness audits.

**R3 — Generated Japanese is 37.6% of the bank and concentrated where the learner is weakest.** N3 is
39% generated, N2 58%, N1 47%. Every one is `needs_review: true`, so the flag is honest, but no teacher
has cleared them and the AI-generated share rises exactly as the language gets subtle enough for
generation to go wrong unnoticeably. If G1 is executed by generation rather than mining, this gets
worse; executed by mining, it improves.

**R4 — The readings defect is self-concealing.** Each individual sentence is real, correct, and inside
the known set, so every hard gate passes and a spot-check of any single line looks fine. The defect
only appears when you read the whole passage. 759 learner-facing artifacts inherit it. Assume other
"composed" artifacts have the same shape and check them by composition, not by element.

**R5 — `ai_generated: false` is doing two jobs.** On exam items it means "the Japanese the learner
reads was not machine-authored", which `scripts/contracts/migrate_exam_banks_p7.py` documents
deliberately. But a `reading_comp` item's question and three distractors *are* machine-authored
Japanese that the learner reads, and the item still records `false`. The 21 readings built partly or
wholly from AI-generated sentences record `false` too. `layer: C` and `needs_review: true` carry the
warning, so nothing is hidden, but a consumer filtering on `ai_generated` gets the wrong set.

**R6 — The i+1 property is frozen, not held.** 147 breaches sit under a ratchet that only prevents
growth. Six N5 lessons currently show N1 sentences. A beginner meeting 嵐のきざしがある in lesson three
is the exact failure mode `design/learning_science.md` exists to prevent.

**R7 — Level tags for 6,042 records cannot be re-derived.** With `level_sources` collapsed to one key,
a future disagreement between lists is unresolvable without re-ingesting the raw lists. Whatever G5
decides, preserve the per-list votes this time.

**R8 — The exam simulator can repeat itself.** 187 of 286 passages serve both `text_grammar` and
`reading_comp`; a learner sitting two mock papers will recognise passages rather than read them,
inflating the score the product uses to tell them they are ready.

---

## 5. Recommended sequence

Ordered so that each step is measurable when the next begins, and so nothing is authored before the
thing that measures it exists.

1. **G12 — write `validate_sentence_coverage.py` as a frozen ratchet over `corpus/`.** Half a day.
   Nothing else in this list can be verified without it, and every later step gets a scoreboard.
2. **G2 — the orthographic relink.** Mechanical, no new content, moves 568 records over threshold and
   takes N5/N4 to ~99%. Re-run G12's baseline afterwards; this is what makes G1's true size visible.
3. **G6 — the A4 repair, in the corrected direction** (agreement `1/1` → `1/3` on the 132 N3 grammar
   records), and **G5's wording decision alongside it**, since both edit the same paragraph of
   `design/schema_v2.md`. Retires the L4–L6 ratchets. Get the owner to confirm the direction first;
   the naive recompute is worse than the status quo.
4. **G1 + G4 + G9 — the N3 exemplification campaign**, through the existing mined-stage pipeline
   pointed at the vocab/grammar gap instead of speak stages: mine → author pt-BR → two-reviewer verify
   → `persist_batch` → `repair_glosses` → validate → export. Selection for the 673 with supply,
   generation only for the 43 with none. This is the single largest item and the one that changes what
   N3 *is*.
5. **G7 + G8 — re-run lesson sentence selection** now that the pool is wide enough, and lower the
   `lesson_sentence_baseline.json` counters rather than freezing them again.
6. **G3 — author the 286 reading passages**, then regenerate `reading_comp` and `text_grammar` against
   them, splitting the passage pools so no text serves both sections (R8). Sequence after step 4 so
   the passages can be built from a known set that now has real coverage behind it.
7. **G13 — resolve the 503 orphans**, most of which step 4 will have consumed.
8. **G11 and G10 — the two scope decisions**, once the ladder through N3 is genuinely complete: whether
   to close the ~750-word N3 vocab gap to the plan's target, and whether N2/N1 stay bank-only or become
   full levels. Both are owner calls, both are rows rather than schema, and neither should start before
   N3 is real.

Steps 1–3 are days. Step 4 is the project. Steps 5–7 are downstream of it and cheap. Steps 8 are
decisions, not work.
