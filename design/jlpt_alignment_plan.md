# JLPT exam-alignment plan — level tags + course (N5/N4/N3) (PLAN ONLY, 2026-06-27)

> **Owner goal:** a learner who finishes our **N5** course should be able to pass the **N5 exam** (and likewise
> N4, N3). Today our level tags are stricter than the exam consensus (N5 kanji = 80 vs ~103), so a graduate is
> short of the exam's expected set. This plan aligns **classifications (level tags) AND the course
> (modules/topics/lessons)** to JLPT exam expectations. **No implementation yet — this is the plan + research.**

## 0. Research — what the exams actually expect
The Japan Foundation publishes **no official kanji/vocab/grammar lists** since the 2010 redesign (confirmed on
[jlpt.jp](https://www.jlpt.jp/e/about/levelsummary.html)). The stable, widely-used consensus (anchored to the
pre-2010 **official** Level-4/3 lists where they exist, plus past-exam analysis) is:

| Level | Kanji NEW | Kanji cumulative | Vocab cumulative | Grammar (≈) | Anchor |
|---|---|---|---|---|---|
| **N5** | ~103 | **~103** | **~800** | ~80–100 | old **Level 4** (official, public-domain) |
| **N4** | ~167 | **~270–300** | **~1,500** | ~150 new (~250 cum) | old **Level 3** (official) |
| **N3** | ~370 | **~650** | **~3,700** | ~200 new (~400 cum) | community only (N3 is post-2010, no old anchor) |

Sources: counts — [japanese-kanji.com](http://www.japanese-kanji.com/levels-jlpt.htm),
[migaku grammar](https://migaku.com/blog/japanese/jlpt-grammar-points); N5=103 list —
[Kanjidon](https://kanjidon.com/blog/jlpt-n5-kanji-list/),
[nihongoichiban](https://nihongoichiban.com/2011/04/10/complete-list-of-kanji-for-jlpt-n5/); N4=167 / N3=370 —
[JLPTsensei N4](https://jlptsensei.com/jlpt-n4-kanji-list/),
[Rocket JLPT N3 (370)](https://www.rocketjlpt.com/jlpt/n3/kanji); canonical free per-level lists (kanji+vocab+
grammar) — **[tanos.co.uk / Jonathan Waller](http://www.tanos.co.uk/jlpt/)**. There is real variance
(N5 kanji 79↔103↔112↔120); we adopt the **~103 / ~300 / ~650** cumulative kanji anchor as the target.

## 1. Current state vs target (the gap)
Corpus today (DB): kanji N5=80 / N4=173 / N3=364; vocab N5≈706 / N4=653 / N3=1596; grammar N5=151 / N4=213 / N3=132.

| Axis | Cum now (N5 / N4 / N3) | Cum target | Gap (N5 / N4 / N3) |
|---|---|---|---|
| **Kanji** | 80 / 253 / 617 | 103 / 300 / 650 | **+23 / +47 / +33** |
| **Vocab** | 706 / 1,359 / 2,955 | 800 / 1,500 / 3,700 | +94 / +141 / **+745** |
| **Grammar** | 151 / 364 / 496 | ~100 / ~250 / ~400 | over / over / ≈ok |

Key reads:
- **Kanji** — every level modestly short; the dominant, owner-flagged gap. Mostly a **re-tag** problem.
- **Vocab** — N5/N4 close; **N3 short by ~745**. Likely re-tag (pull from N2) not new authoring — see §3.
- **Grammar** — at/above target everywhere (we split finely); **no expansion needed**, possibly re-tag only.
- **We already own enough material:** total corpus kanji=2,131 and vocab=7,301 (both >> the N3 cumulative
  targets), so this is **redistribution by re-tagging, not new sourcing**. Quality question is *which* specific
  items match each exam level (§2), not whether we have enough.

## 2. Sourcing the exam-anchor lists (Layer A facts; §1.5 + owner ruling)
Level membership is a **non-copyrightable consensus fact** (which we already treat via §1.5: cross-reference
≥3 lists + record agreement). We currently use 4 kanji lists that cluster on the strict 79–80 N5 set
(kanjiapi=79, bluskyo=79, davidluzgouveia, anchori). Add **exam-anchored** lists so the consensus reflects the
~103/300/650 target:
- **N5 ← old JLPT Level-4 official kanji list** (public-domain test spec; hosted at tanos.co.uk) = the 103 anchor.
- **N4 ← old JLPT Level-3 official list** (tanos) minus N5.
- **N3 ← a modern community list** (no old anchor): tanos N3 and/or JLPTsensei N3 (~370) — ingest ≥2 for consensus.
- **Vocab + grammar:** the matching tanos/JLPTsensei per-level **vocab** and **grammar** lists, for the same
  re-leveling of vocab (esp. N3) and an audit of grammar.
- **License:** lists are facts/consensus → keep + credit (record each in `design/sources.md` + `dataset_source`
  + `research/datasets/jlpt/MANIFEST.md` with URL+SHA256+license; tanos old-official lists are public test
  specs). Do NOT copy any prose; only the (kanji/word ↔ level) mapping. Consistent with `design/license_audit.md`.

## 3. Reconciliation rule change (`reconcile_levels.py`)
Today: simple majority across the 4 lists → strict 79–80. New rule (the design decision):
1. **Exam-anchor priority:** if the old-official Level-4/3 list assigns a kanji to a level, that anchor **wins**
   (it is the closest thing to "what the exam expects"); community lists set `level_confidence` + agreement.
2. For N3 (no official anchor): **majority of the modern community lists** (≥3), as today.
3. Record `level_sources` (per-list votes), `level_agreement`, `level_confidence`, and a new
   `level_anchor` flag (old-official vs community) on every kanji/vocab row — so each tag is auditable and a
   reviewer can see *why* it landed at that level.
4. **Monotonic cumulative target:** after re-tag, assert cumulative counts land in the target bands (±10%):
   kanji 103/300/650, vocab 800/1500/3700. Log any level that misses its band.
5. **Vocab kanji-safety:** a vocab's level must be ≥ the level of the kanji it's written with (don't put a word
   at N5 if it needs an N4 kanji) — or the word is shown in kana at that level. Enforce in the re-tag.

## 4. The cascade (ordered; each step is the next phase's input)
Re-tagging is the easy 20%; **re-sequencing the course is the hard 80%** because the linear i+1 known-set must
still hold after items move between levels.
1. **Ingest** exam-anchor lists (§2) → `research/datasets/jlpt/` (+ MANIFEST/sources/attribution).
2. **Re-tag** kanji/vocab/grammar via the new `reconcile_levels.py` (§3); write `level`, `level_*` fields.
3. **Re-export corpus** (`export_corpus.py`) + re-run integrity/coverage audits on the new counts.
4. **Course re-org (the big one):** every item promoted *into* a level must be *taught* in that level's course,
   in i+1 order. Concretely:
   - The ~23 kanji promoted **N4→N5** (already in the corpus) must move from N4 lessons to N5 lessons; same for
     promoted vocab. Removed-from-N4 items must not leave an N4 lesson dangling.
   - Choose per item: (a) **slot into an existing N5 topic** that fits thematically, or (b) **add N5
     lesson(s)/a topic** for the promoted batch. Prefer (a); use (b) when a coherent group arrives.
   - Preserve **prerequisite order**: never introduce a kanji before its taught components / a word before its
     kanji. Re-run the placement/sequencing logic (`build_grammar_placement.py` analog for kanji/vocab).
5. **Re-gate:** `load_lessons` (recompute `cumulative_known_set`) → `validate_lessons` (i+1) → re-gate
   **readings** (i+0; some may need re-selection as known-sets shift) → `validate_readings`.
6. **NEW coverage gate:** add `audit_jlpt_coverage.py` — for each level, assert
   *course-taught set ⊇ exam-target set* (kanji/vocab/grammar) and counts are within target bands. This is the
   acceptance test for "a graduate can pass the exam".
7. **Full gate** (`validate_all`) → `export_course` → `export_readings` → prototype `sync-data` → `build` →
   no-leak grep → commit research → copy to standalone → commit → push both.

## 5. Acceptance criteria (definition of done)
- Per level L ∈ {N5,N4,N3}: cumulative kanji/vocab within target band; **course-taught(L) ⊇ exam-anchor(L)** for
  kanji (hard), vocab (≥90%), grammar (≥90%); `audit_jlpt_coverage.py` green.
- Linear i+1 still holds (validate_lessons 0 errors); readings still i+0 (validate_readings 0 fail).
- Every re-leveled row carries `level_anchor` + `level_sources` + `level_confidence`; `needs_review` where the
  anchor and community lists disagree (teacher confirms borderline cases).
- Full validation gate green; no-leak holds; both repos pushed.

## 6. Risks / open decisions for the owner
- **Anchor source:** confirm **tanos.co.uk old-official Level-4/3** as the N5/N4 kanji anchor (recommended) +
  a modern list for N3. (Alternatives: JLPTsensei for all three — consistent but community-only.)
- **Target counts:** confirm **103 / 300 / 650** kanji and **800 / 1,500 / 3,700** vocab. (Variance is real;
  these are the mainstream picks.)
- **Course growth:** promoting items into N5/N4 will **lengthen** those courses (more lessons). Acceptable?
- **N3 vocab +745:** biggest content move; verify it's re-tag-from-N2 (cheap) vs needs new sentence coverage.
- **Scope:** N2/N1 left as-is for now (out of the stated zero→N3 focus), but the same method applies later.

## 7. Effort estimate (rough)
Ingest+re-tag+audit script work: small/medium (1 pass). Course re-sequencing + reading re-gate: **large**
(touches most N5/N4 lessons + the placement logic). Recommend executing as discrete atomic phases (§4 steps),
committing after each, per the resumption protocol.
