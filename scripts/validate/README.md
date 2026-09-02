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
| `validate_practice_coverage.py` | every item a lesson **unlocks** is also **practised** by that same lesson's exercises. "Practised" = an exercise *targets* the item: it appears in an answer surface (`text`/`full`/`correct`/`accept[]`/`order[]`/both columns of `pairs[]`), in `<vocab\|kanji\|grammar ref>` markup in the prompt, or in a sentence the exercise cites through `sentence_refs` (that sentence's token `vocab` slugs, its `grammar[]` tags, its token surfaces for kanji). **Distractors** (`choices` minus `correct`), the `explanation` field and incidental Japanese in the prompt do **not** count. Vocab matches by longest-match tiling against the whole registry surface set — never a bare substring, so い inside 寒いですから and 表 inside ひょうばん are not credited — with two rules a Fable sample forced after tiling alone credited 線 for せん inside できません: an answer string that IS one of its exercise's cited sentences is read through that sentence's token dissection instead of being tiled, and a kana-only surface is credited only when it is the whole run or its span is delimited on both sides by a run edge or a character outside its own kana script (so タクシーで counts, できません does not). Kanji matches by character containment, so a kanji inside the answer word *is* practice of it; grammar matches by pattern segments cut from `forms[]`/`structure_pattern` (1-character segments only on an exact whole-answer match, or の would match everything). Absent counts per (level, kind) are ratcheted in `scripts/validate/practice_coverage_baseline.json`; the per-lesson absent list is the W20 work list, written to `research/reports/practice_coverage_review.json` only when its content changes |
| `validate_lesson_gating.py` | every item ref in a body sits inside that lesson's `cumulative_known_set` (hard); the lesson↔sentence i+1 backlog is frozen in `research/reports/lesson_sentence_baseline.json` and may only shrink; writes the teacher review queue only when its content changes |
| `validate_sentence_manifest.py` | `sentence_refs` is exactly the set of sentences the body renders; exercise `sentence_refs` are provenance and must resolve (display not required) |
| `validate_srs_decks.py` | decks exist in `design/unlock_enums.json`; cards file into the LESSON's level deck (front-loading is legal and filed where it is taught); no duplicate cards |
| `validate_md_views.py` | every generated `.md` view re-renders byte-identical from its `.json` source (reads the DB for sentence resolution — the one sanctioned DB read in a view check) |
| `validate_readings.py` | max_new=0: every kanji and content word of a reading is inside its gating lesson's exported cks, slug space |

### Corpus content

| validator | enforces |
|---|---|
| `audit_hygiene_all_locales.py` | every learner-facing pt-BR string corpus-wide (~245k strings): no em dash, emoji, mojibake/mixed script, QA-instruction leaks, accent-stripping (corpus-derived lexicon of 814 words), pt-PT, duplicated clauses, unbalanced parens. Replaces `audit_lesson_hygiene.py`, which read a stale staging dir. `prompt_pt` joined `LEARNER_KEYS` on 2026-09-02 (readiness G13): the speak units write the learner's instruction as a FLAT `prompt_pt` rather than a `{"pt-BR": …}` object, so the gate saw 86 of the ~370 strings under `course/speak/` and reported 0 FAIL while 5 em dashes shipped in `fluency.prompt_pt` |
| `validate_provenance_json.py` | `layer`/`source`/`ai_generated`/`needs_review` present and meaning one thing everywhere; `ai_generated` ⇒ `needs_review`; exam-item `ai_generated` equals the derivation table in `scripts/contracts/migrate_exam_banks_p7.py` |
| `validate_repairs_applied.py` | all 1,299 rows of the six tracked tables in `research/derived/repairs/` replayed against the export: the row's `new` is what the export carries at the address the row names (link rows: present; `unlink`: absent; `no-link`: still untagged; `superseded_by` rows skip only once the chain to the successor row is proved against the export). Six addressing schemes, one per campaign, read off the `scripts/apply_*.py` that wrote each table. An unregistered `.json` in the repairs directory FAILS; so does an empty directory, a handler that does not check every row 1:1, and a pre-repair value surviving as an embedded copy under `course/`. Clean, no ratchet |
| `validate.py`, `validate_sentence_structure.py`, `validate_grammar_formation.py`, `validate_furigana.py`, `validate_groundtruth.py`, `validate_display_consistency.py`, `test_kanji_align.py`, `validate_kanji_reading_groups.py` | the sentence-bank dissection, grammar formation steps, furigana coverage, Layer-A ground truth (pre-existing gates) |

### Banks and drills

| validator | enforces |
|---|---|
| `validate_exam_banks.py` | ground truth from the corpus JSON (rewritten off the DB): kr/or stem/answer agree with the record the item's `vocab` slug names; option sets distinct under NFKC + kana folding; blank integrity (the 93 removed leak items stay out); tg stem == its passage with the blank (what makes not rendering the passage safe); refs resolve; every (level, type) bank ≥3× its paper counts; advisory ratchets for okurigana-solvable and shape-solvable distractors pending the bank regeneration |
| `validate_exam_level_gate.py` | the level gate the banks never had (readiness G3): an item is LEVEL-APPROPRIATE when every kanji, vocabulary item and grammar point its learner-visible Japanese requires — stem, question, options, `pieces`, `target`, the `reading_comp` passage, every listening turn — is inside that level’s taught set (the `cumulative_known_set` of the last lesson of its course module). Kanji from the strings themselves; vocab from the item’s own `vocab` slug plus the `tokens[].vocab` of the sentence its `sentence` ref names; grammar from the item’s own `grammar` key plus that sentence’s `grammar[]` tags. 3,565 of 6,048 items fail today, so the per-(level, family) counts are RATCHETED in `exam_level_baseline.json` — growth fails, shrinkage asks for a lower ceiling, an empty bank fails, a stale ceiling fails. Sufficiency against the paper is printed until a family’s ceiling reaches 0, then it gates. Retired by W17/W18 (the A2 builder does the selection) |
| `validate_conjugation_exercises.py` | every form correct for its class; distractors are real forms of the same word; all 18,524 readings re-romanized and matched |
| `validate_role_exercises.py` | all 5,358 drills re-derived from the sentences' own pattern data; fails on an empty bank |
| `validate_exam_stem_collisions.py` | no two items in one bank print the same stem and key different answers (readiness G12 — `n3_orthography` asks いし and keys 医師, 意思 *and* 意志; n4 たずねる keys 尋ねる *and* 訪ねる). Stem identity = NFKC + the answer blank collapsed to one sentinel (so a blank in another position stays a different stem) + punctuation/separator/control stripping. Scope is the bank file = one (level, section) = the pool one paper draws from; only the 4,469 items carrying both `stem` and `correct` are compared, and `question`-shaped types are deliberately excluded (the same question over two passages is not a contradiction). **Ratcheted per bank** in `research/reports/exam_stem_collision_baseline.json` at today's **94** items over 46 groups — any bank growing FAILS, so the debt cannot move sideways; a shrink prints the new number. Retired by W17/W18 |
| `validate_speaking_path.py` | checkpoint refs resolve with type/level agreement; embedded content derivable from the cited item; kanji answers always accept kana; manifest totals true; two patterns claiming the SAME effective form set never co-taught (equality only — nested sets are different points, see commit 531b47c2) |
| `validate_generated_jp.py`, `run_golden.py` | the §9 gate for GENERATED Japanese, and its regression suite. `validate_generated_jp.py` with no argument runs a **selftest**: Sudachi tokenizes a control string with zero OOV, the kanji registry and reading table clear their floors, the Tatoeba/JEC attestation corpus answers, and two control strings still classify as §9.5 says. `run_golden.py` asserts all 14 rows of `golden_set.json` classify correctly (good ⇒ not rejected, bad ⇒ rejected, unnatural ⇒ not auto-accepted). Neither was in the suite until 2026-09-02, and `run_golden.py` could not even start under the system interpreter — see **Interpreters** below. These two read `db/corpus.sqlite` by design (the gate scores generated text against the kanji/reading registry and the raw FTS corpora, which the export does not carry) |

### Graph and coverage

| validator | enforces |
|---|---|
| `validate_graph_edges.py` | ~550k cross-entity edges over 8 checks: kanji example sentences contain their kanji, families bidirectional via the `families` back-pointers with member-derived `spans_levels`, capability map complete or exempted, conjugation↔vocab coverage |
| `graph_queries.py` | the four spec §1.7 queries VERBATIM against the export, real pass/fail, with an explicit waiver table (a waived query that starts passing is also reported) |
| `validate_stroke_integrity.py` | taught-level stroke coverage both directions + count agreement, exemptions in `corpus/strokes/exemptions.json` |
| `audit_coverage.py` | placement coverage in **published slug space, over the export**: `introduces_refs` in `course/outline.json` vs the `unlocks[]` of the 322 lesson leaves, per kind — placed-but-not-unlocked FAILS, a ref unlocked by more than one lesson FAILS, a ref naming no registry record FAILS, unlocked-but-not-placed WARNs. It read `db/corpus.sqlite` and joined on `headword` until 2026-09-02, which printed `vocab placed=2910 unlocked=2910` where the export carries **2,946**; the 36-record gap was the homograph class, so a homograph coverage hole was structurally invisible. Now 2,946 / 634 / 496 both sides. Floors (200 lessons, 2000/400/300 placements) fail on a vanished tree |
| `audit_jlpt_coverage.py`, `validate_capabilities.py`, `validate_strokes.py` | JLPT bands, capability registry, stroke registry (pre-existing) |

### Prototype

| validator | enforces |
|---|---|
| `validate_prototype_sync.py` | `prototype/app/data` is the current projection of the export; a missing data dir FAILS |
| `validate_no_client_leak.py` | the built client bundle contains no corpus content (the SSR-only guarantee); missing build prints SKIP |

### Rebuildability of the index

| validator | enforces |
|---|---|
| `validate_index_rebuildable.py` | the git-ignored `db/corpus.sqlite` really is regenerable: replays `research/derived/rebuild_manifest.json` into a scratch DB, re-exports, and diffs the result against the committed `corpus/` and `course/` trees byte for byte |

This is the only validator that builds a database instead of reading the export, because the claim it
tests is about the database. `research/derived/rebuild_manifest.json` is the durable half: 111 steps —
every script that has ever written the DB — in the order a rebuild must run them, each with its
arguments, the commit it first landed in, the tables it writes, and (for the 36 that cannot run
today) why not. `scripts/rebuild_index.py` executes it; `scripts/ingest/replay_all.py` is a step
inside that chain, not a second one beside it.

**Two modes.**

```bash
python scripts/validate/validate_index_rebuildable.py --quick  # ~2 s: the grammar family only
python scripts/validate/validate_index_rebuildable.py          # ~90 s: rebuild, export, diff everything
python scripts/validate/validate_index_rebuildable.py --keep   # same, leaving the scratch tree to inspect
```

`--quick` replays the thirteen steps `corpus/grammar/*.json` passes through that do not need the
sentence bank, exports, and diffs that family — a couple of seconds, which is what a per-commit gate
can afford, and it is the form registered in `validate_all.py`. The full run replays all 75 runnable
steps into a scratch DB (about a minute, most of it `replay_all.py` re-dissecting the bank), runs
`export_corpus.py`, `export_course.py` and `export_readings.py` against it, and diffs the 787 files
they write. Run it before a release and whenever a step is added to the manifest. The bank and drill
builders are deliberately not run: exam banks, conjugations, the speaking path, exercises,
capabilities and strokes take authored inputs of their own, and `migrate_exam_banks_p7.py` states
outright that the exam banks cannot be regenerated yet (W17/W18).

**A rebuild does not touch the repo.** Several steps rewrite the lesson authoring layer —
`build_exam_kanji_lessons.py` re-chunks `research/derived/lessons/*-kanji-exame-*.json`,
`build_readings.py` rewrites the `<reading>` block of every lesson it wires — and `load_lessons.py`
reads that same directory back. Pointed at a scratch database those writes carry scratch data, so the
first full run rewrote 74 tracked lesson files with its own degraded output and the second run read
the damage back and produced different bytes: the ratchet caught exactly that, on twelve files. Those
paths now resolve through `dbtarget.out_root()` and `rebuild_index.py` points `$YOMINEKO_OUT_ROOT` at
a work root seeded with a copy of the lessons. Two consecutive full runs now produce identical trees
and leave `git status` unchanged. **Any new step that writes a file the repo tracks must do the
same** — read from `ROOT`, write through `out_root(ROOT)`.

**What the first full run found, and it is not a clean bill of health.** 650 of the 787 exported files
differ from what is committed. The causes are recorded per file in `rebuild_baseline.json` and
summarised in its `_causes` block; the short version is that the database is a nine-month
accumulation and the manifest is a single ordered pass over today's scripts, which are not the same
thing. Nine steps cannot run because their inputs are `.gitignore`d (`research/derived/tr/`,
`research/derived/reauthor/`) and three because their inputs were never written to disk at all; nine
repair steps then refuse every row because they exact-match text those steps wrote. `build_families_full.py`
is scoped to "every N5/N4 item" but now runs after the N2/N1 bank ingest, so it families 10,187 items
the committed export never had. `db/corpus.sqlite` holds 286 reading rows accumulated across every
historical run of `build_readings.py`; one replay builds 130.

**The exporters' one wall-clock stamp is pinned.** `_Generated <today>` in the INDEX.md headers and
`"generated"` in `course/manifest.json` used to come from `date.today()`, which meant the export
stopped reproducing at midnight for a reason that has nothing to do with the data. They now read
`build_date()`, which honours `$YOMINEKO_BUILD_DATE`; the validator sets it to the date already
committed. Unset, the behaviour is what it always was.

**`rebuild_baseline.json` holds two things at once, and only one of them is an excuse.** A file listed
there is excused for *differing from the committed export* — with the cause written down — because the
rebuild does not reproduce everything yet. It is *not* excused from producing the same bytes it
produced when the entry was recorded: each entry pins a `rebuilt_sha256`, and a mismatch is a hard
failure naming the file. That is what makes the ratchet falsifiable rather than a mute list. A file
that starts matching the committed export is reported so its entry gets deleted; the list may only
shrink. Re-record a mode's entries with `--record` after a deliberate change, never to silence a
failure you have not explained.

Both modes are plant-proved and the runs are pasted into the validator's own docstring: drop
`apply_grammar_formation_repairs.py` from a copy of the manifest and `--quick` fails naming the three
grammar files; drop `renumber_topics.py` and the full run fails on 500. Empty input fails in both —
`--quick` refuses a manifest with no grammar-family steps, the full run refuses an export it cannot
make, and a floor (4 / 700 files) catches a walk over an empty tree.

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
terminal punctuation, L4–L6 level-consensus, okurigana-solvable distractors, per-item practice
coverage, exam level-appropriateness) fail on growth and report when they shrink so the ceiling gets
lowered. Each names the owner decision or content work that retires it.

**A repair table is a claim, and the export is what settles it.** `validate_repairs_applied.py`
(W02, readiness finding G7) replays every tracked table in `research/derived/repairs/` against the
committed JSON, because every applier is DB-only and nothing used to check that the exporter carried
the edit through. It runs **clean — 1,282 PASS / 17 checked skips / 0 FAIL over 1,299 rows** — with
no ratchet and no exemption file.

**A marking is an assertion, not an excuse.** Two markings let a row skip the value comparison, and
neither is taken on trust. `grammar_followups.json`'s `action: "no-link"` (10 rows) still asserts the
sentence carries zero grammar links. `superseded_by: {"table", "row"}` (7 rows in
`sentence_text_repairs.json`, the ones a *later* campaign wrote over) skips only after the chain is
proved: the named table is tracked, the row is in range and is not itself, the successor addresses
the same (slug, field, locale), the successor's `old` is this row's `new`, and **the export carries
the successor's `new`**. That last clause is what makes the marker regression-proof — revert the
field and the marker stops chaining (plant-proved, along with a marker naming an untracked table, a
wrong address, a self-reference, a broken `old`, and an unmarked supersession, which is its own
failure class naming the row that needs the marker). Prefer this shape over a counter: a ceiling
counts failures, a marker has to keep being true.

G7's "16 `form_meanings` no-ops" do **not** reproduce: the audit searched for the serialised
`{form: meaning}` map as a substring, and `export_corpus.py` projects that map through `forms_json`
into `forms[].meaning`, so the string can never appear. Replayed through the projection, all 16 are
carried. The class stays gated (and is plant-proved) because the projection that hid them is still
there.

**An exemption file exempts one named rule, not a topic.** `course/practice_exemptions.json` holds
the eight kanji-reinforcement lessons that render no practice at all; it exempts them from
`validate_exercise_contracts.py`'s "≥1 retrieval + ≥1 production exercise" rule and from nothing
else. `validate_practice_coverage.py` reads the same file, checks its entries still name real
lessons, and still counts those lessons' 60 unlocked items as unpractised — which is exactly the
debt each exemption reason describes.

**Advisory ≠ decorative.** `completeness_audit.py` and `detect_ai_tells.py` report for human review
and never gate; everything else gates on exit code.

**Interpreters.** `validate_all.py` runs each validator with the interpreter that launched it, except
for the names in its `NEEDS_VENV` set (`run_golden.py`, `validate_generated_jp.py`), which are routed
to `.venv/Scripts/python.exe`. Several scripts have said "Run with venv python" in their docstrings
since P5 and nothing enforced it; the Sudachi gates are where it bites, because `C:\Python313` carries
`sudachidict_full` but not `sudachidict_core` and `validate_generated_jp.py` builds
`dictionary.Dictionary()`, which defaults to core — so `run_golden.py` raised `ModuleNotFoundError:
Package sudachidict_core does not exist` before its first assertion. A missing venv is reported as a
hard FAIL rather than silently downgraded to an interpreter that cannot run the check. If you add a
validator that imports Sudachi, put its name in `NEEDS_VENV`.
