# The validation gate

`validate_all.py` runs the whole suite and fails if any HARD validator fails. Run it before every
commit; every atomic unit ends with it green. Individual validators run standalone and most accept
`--root PATH` to validate a mutated copy of the tree (that is how their tests work — see
"Falsifiability" below).

```bash
python scripts/validate/validate_all.py
```

## What the suite validates, and where

The committed **exported JSON under `corpus/` and `course/` is the source of truth**
(`db/corpus.sqlite` is a regenerable working index). A validator that reads the DB validates the
wrong artifact — the 2026-08-26/27 review found five hard gates doing exactly that, one of them
pointed at a staging directory that had diverged from the shipped course in 259 of 322 lesson
bodies. Every validator below reads the export unless its row says otherwise.

### Contracts and structure

| validator | enforces |
|---|---|
| `validate_contracts.py` | every record conforms to its `contracts/*.schema.json`; stable ids unique per entity; ~595k cross-references resolve; empty entity globs fail |
| `validate_course_chain.py` | manifest → course → topic → lesson tiers agree (counts, order, ids, paths, stub==leaf); topic summaries and `outline.json` recompute exactly from the lesson leaves; every published JSON is catalogued by an entity or listed in `design/generated_artifacts.json` with a reason; a file inside an entity glob must have that entity's packing (a sidecar in a registry directory poisons every consumer of the glob) |
| `validate_schema_generation_is_current.py` | regenerating `contracts/` reproduces the committed contracts byte-for-byte (hand-written schemas asserted untouched) |
| `audit_manifest.py`, `audit_export_refs.py` | manifest cross-links; every `ref`/`item-ref` in lesson leaves resolves in the export, vocab never by the retired headword scheme |

### Identity and addressing

| validator | enforces |
|---|---|
| `validate_unlock_ledger.py` | in published slug space: every taught-level record unlocked exactly once or exempted in `course/coverage_exemptions.json`; no two refs in one lesson resolving to one record (the collision that once dropped both 得る siblings); cross-level teaching only earlier |
| `validate_stable_addresses.py` | every integer FK (`vocab_id`, `*_ids` lists) sits beside its published slug form; a row number is never the only address (contracts/README.md: it "must never be used as an API key") |
| `validate_level_consensus.py` | spec §1.5 evidence: `level_agreement` well-formed, confidence in range, sources shaped as documented; L4–L6 (agreement↔confidence consistency) run as a frozen ratchet pending the owner's confidence-formula decision — growth fails, the held count is printed |

### Courseware

| validator | enforces |
|---|---|
| `validate_lessons.py` | (reads the DB by design — it is the loader-side gate) body grammar rules, per-type answer shapes, introduce-once **in export space**, ≥1 retrieval + ≥1 production among RENDERED exercises; fails if the DB is empty while `course/` has leaves |
| `validate_lesson_bodies.py` | every body parses balanced; every ref of every kind resolves; `<jp reading>` non-empty kana-only whenever the span has kanji; no markup in plain-text fields |
| `validate_exercise_contracts.py` | `exercises[].id` ↔ body `<exercise ref>` exact bijection; per-type answer contracts graded exactly as `LessonExercises.tsx` grades (same normalization, differential-tested); a lesson with unlocks renders practice or is exempted in `course/practice_exemptions.json`; terminal-punctuation ratchet |
| `validate_lesson_gating.py` | every item ref in a body sits inside that lesson's `cumulative_known_set` (hard); the lesson↔sentence i+1 backlog is frozen in `research/reports/lesson_sentence_baseline.json` and may only shrink; writes the teacher review queue only when its content changes |
| `validate_sentence_manifest.py` | `sentence_refs` is exactly the set of sentences the body renders; exercise `sentence_refs` are provenance and must resolve (display not required) |
| `validate_srs_decks.py` | decks exist in `design/unlock_enums.json`; cards file into the LESSON's level deck (front-loading is legal and filed where it is taught); no duplicate cards |
| `validate_md_views.py` | every generated `.md` view re-renders byte-identical from its `.json` source (reads the DB for sentence resolution — the one sanctioned DB read in a view check) |
| `validate_readings.py` | max_new=0: every kanji and content word of a reading is inside its gating lesson's exported cks, slug space |

### Corpus content

| validator | enforces |
|---|---|
| `audit_hygiene_all_locales.py` | every learner-facing pt-BR string corpus-wide (~244k strings): no em dash, emoji, mojibake/mixed script, QA-instruction leaks, accent-stripping (corpus-derived lexicon of 815 words), pt-PT, duplicated clauses, unbalanced parens. Replaces `audit_lesson_hygiene.py`, which read a stale staging dir |
| `validate_provenance_json.py` | `layer`/`source`/`ai_generated`/`needs_review` present and meaning one thing everywhere; `ai_generated` ⇒ `needs_review`; exam-item `ai_generated` equals the derivation table in `scripts/contracts/migrate_exam_banks_p7.py` |
| `validate.py`, `validate_sentence_structure.py`, `validate_grammar_formation.py`, `validate_furigana.py`, `validate_groundtruth.py`, `validate_display_consistency.py`, `test_kanji_align.py`, `validate_kanji_reading_groups.py` | the sentence-bank dissection, grammar formation steps, furigana coverage, Layer-A ground truth (pre-existing gates) |

### Banks and drills

| validator | enforces |
|---|---|
| `validate_exam_banks.py` | ground truth from the corpus JSON (rewritten off the DB): kr/or stem/answer agree with the record the item's `vocab` slug names; option sets distinct under NFKC + kana folding; blank integrity (the 93 removed leak items stay out); tg stem == its passage with the blank (what makes not rendering the passage safe); refs resolve; every (level, type) bank ≥3× its paper counts; advisory ratchets for okurigana-solvable and shape-solvable distractors pending the bank regeneration |
| `validate_conjugation_exercises.py` | every form correct for its class; distractors are real forms of the same word; all 18,524 readings re-romanized and matched |
| `validate_role_exercises.py` | all 5,358 drills re-derived from the sentences' own pattern data; fails on an empty bank |
| `validate_speaking_path.py` | checkpoint refs resolve with type/level agreement; embedded content derivable from the cited item; kanji answers always accept kana; manifest totals true; two patterns claiming the SAME effective form set never co-taught (equality only — nested sets are different points, see commit 531b47c2) |

### Graph and coverage

| validator | enforces |
|---|---|
| `validate_graph_edges.py` | ~550k cross-entity edges over 8 checks: kanji example sentences contain their kanji, families bidirectional via the `families` back-pointers with member-derived `spans_levels`, capability map complete or exempted, conjugation↔vocab coverage |
| `graph_queries.py` | the four spec §1.7 queries VERBATIM against the export, real pass/fail, with an explicit waiver table (a waived query that starts passing is also reported) |
| `validate_stroke_integrity.py` | taught-level stroke coverage both directions + count agreement, exemptions in `corpus/strokes/exemptions.json` |
| `audit_coverage.py`, `audit_jlpt_coverage.py`, `validate_capabilities.py`, `validate_strokes.py` | placement coverage, JLPT bands, capability registry (pre-existing) |

### Prototype

| validator | enforces |
|---|---|
| `validate_prototype_sync.py` | `prototype/app/data` is the current projection of the export; a missing data dir FAILS |
| `validate_no_client_leak.py` | the built client bundle contains no corpus content (the SSR-only guarantee); missing build prints SKIP |

## Conventions

**Falsifiability is the entry requirement.** Every validator added in the 2026-08-27 build landed
with a planted-violation proof: a mutated copy of the tree, one plant per major check, all caught
(~120 plants total), then three independent reviewers hunted cannot-fail patterns — hardcoded
passes, results compared to nothing, empty-input exit-0, swallowed exceptions. That review is why
several older checks were reclassified `[info]`: an unconditional PASS is an information line
wearing a check's costume.

**Empty input fails.** A gate whose data vanished (moved, renamed, shadowed by a sidecar) must fail,
not certify nothing. Validators carry floors far below real counts (322 lessons, 40 banks) so growth
never trips them.

**Exemption files can only shrink.** `course/coverage_exemptions.json`,
`course/practice_exemptions.json`, `corpus/strokes/exemptions.json`,
`corpus/capabilities/exemptions.json`, `design/generated_artifacts.json`: every entry carries a
reason, an entry matching nothing is itself a failure, and two validators consuming the same rows
consume the same file (learned the hard way when stroke exemptions and the graph check disagreed
about 17 kana).

**Ratchets hold known content debt without hiding it.** Frozen counters (i+1 sentence backlog,
terminal punctuation, L4–L6 level-consensus, okurigana-solvable distractors) fail on growth and
report when they shrink so the ceiling gets lowered. Each names the owner decision or content work
that retires it.

**Advisory ≠ decorative.** `completeness_audit.py` and `detect_ai_tells.py` report for human review
and never gate; everything else gates on exit code.
