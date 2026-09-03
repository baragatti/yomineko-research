# APP_PLAN — from corpus to a complete pt-BR Japanese app

Plan of record, 2026-09-01 (v2, reviewed). Sources: the nine readiness audits under
`research/reports/readiness/` (every number produced by a script over the data) and the owner
decisions at the top of `PENDING.md`. STATE.md points here; progress is tracked in §3 by unit id.

**The product (owner):** a full language app, Duolingo-shaped, with integrated Anki-grade
memorization (FSRS-6 or better), tests, exams and JLPT simulations, all in pt-BR. Two paths: the
JLPT-level course (zero → N5 → N4 → N3) and a speak-as-fast-as-possible path. AI-authored now,
teacher-validated later, aiming as close to 100% as possible.

---

## 0. Where we are

| capability | ready | the gap in one line |
|---|---|---|
| JLPT course path | 62% | spine complete and provably gated; practice behind it thin (40% of vocab, 89% of kanji never drilled by their own lesson) |
| Speak-fast path | 45% | typed path finished; spoken layer absent; content 62% casual, 4 of 36 survival utterances |
| SRS / FSRS | 62% | filing done and gated (4,133 cards); no production keys, no audio, 1,545 cards without an example |
| Exams / simulations | 55% | a timed N5/N4/N3 paper runs with scoring; banks not level-gated; 2 of 9 sections on non-passages |
| In-lesson tests | 55% | quiz layer finished; no placement, topic tests, or mistake index |
| Coverage | 67% | N5, N4 essentially complete; N3 barely exemplified (8.5% of its vocab in any sentence) |
| Review loop | 35% | nothing can mark content approved; 22% of records carry no provenance |
| Platform | 55% | content contract exact (51,918 records); user state, release identity, API, audio absent |
| A5 family layer | — | **defect certain** (272/364 wrong-topic memberships, reproduced independently) |

**Solid — do not touch:** the four-tier course chain, the unlock ledger (4,137 introduce-once
unlocks, `cumulative_known_set` derivable with zero violations), the exercise↔body bijection, SRS
enrolment, the exemption files, the content contract, the 39-gate suite.

**The finding that outranks the rest:** every repair writes the git-ignored `db/corpus.sqlite`;
nothing proves the DB can be rebuilt from ingest + the tracked repair scripts, and the exam
regeneration reads that DB. Until W01 lands, the corpus's durability rests on one file on one
machine. Everything else waits behind W01.

---

## 1. How work runs

- **Models.** Fable 5.1 plans, reviews plans and results, and draws random samples for quality.
  Opus 5 does the work: every authoring or repair campaign is an Opus workflow.
- **A campaign is always:** (1) a deterministic work list computed by a script, never by an agent;
  (2) Opus authors from the live record, re-deriving the finding itself; (3) an independent Opus
  verifier per batch, adversarial; (4) one idempotent apply script with an exact-match tracked
  table under `research/derived/repairs/`; (5) **a Fable random sample** — 30 applied rows read
  against the Japanese before commit, or 30 authored items against their source; a sample failure
  stops the commit and widens to 100; (6) the full gate green; (7) one commit; (8) STATE.md.
- **A validator joins the suite only with a plant proof** on a copied tree (validator + its
  `scripts/export` imports copied into the fixture). Ratchets hold known debt and may only shrink.
- **Owner decisions** are in §4. A unit that needs one proceeds with the stated default unless
  overruled; a unit marked BLOCKING waits.
- **Repairs go to both layers** where an authoring layer exists (DB + `research/derived/…`), and the
  exporter republishes; the committed JSON is the source of truth.

---

## 2. Milestones

| id | milestone | done when |
|---|---|---|
| M0 | **Durable and measurable** | the DB rebuilds byte-identically from JSON + scripts (W01); every campaign has a ratchet (W02–W05); the approval ledger exists (W06) |
| M1 | **Identity settled** | A3, A9, A4, A6, A5 landed; no published slug will change again (W07–W11) |
| M2 | **N5 and N4 app-complete** | every unlocked item practised in its lesson; real passages; level-gated banks regenerated; needs[] and furigana complete; N3 dead end closed (W12–W24) |
| M3 | **N3 app-complete** | N3 exemplified (≥3 sentences per word, ≥5 per point), rebalanced, its passages and paper sections real (W13, W21, W25) |
| M4 | **Memorization real** | every card renders and grades; user-state contracts published; speak path emits cards (W26–W30) |
| M5 | **Speaking path v1** | register field live and filtered, survival cores in every stage, audio schema and assets, voice mode contract (W31–W36) |
| M6 | **Review loop live** | a named teacher approving N5 through the ledger while campaigns run on N3 (W06, W37–W39) |
| M7 | Platform for a real app | user state, release identity, API contract, audio pipeline, attribution (W40–W44) |

M0 and M1 are sequential. After M1, lanes A (course), B (SRS), C (speak), D (platform/review) run
in parallel wherever they do not share files; the gate catches the interactions.

---

## 3. Work units

Columns: **runner** = Opus campaign / Opus agent / Fable / owner. **done** = the gate or artifact
that proves it. **needs** = dependencies and decisions. Status column is the live tracker.

### Lane 0 — M0: durable and measurable (sequential, first)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W01 | **DB rebuildability** — DONE, and the answer was NO: 137 of 787 export files reproduce from ingest + the 111-step manifest (`research/derived/rebuild_manifest.json`); the other 650 are ratcheted with a diagnosed cause each. Root causes FIXED: the 2026-06-26 topic renumbering had been applied by hand and never scripted (145 course files exported under paths nobody committed — now `scripts/ingest/renumber_topics.py`); the rebuild wrote into `research/derived/lessons/` and read its own damage back (non-deterministic — paths now resolve through `dbtarget.out_root()`, two consecutive runs identical); a step-order defect; a crash on a vestigial column. Recorded, not fixable here: `research/derived/tr/` (48 MB) and `reauthor/` (9.7 MB) are gitignored so 9 steps cannot run and 9 repair steps refuse every row (**D16**); families builder scoped N5/N4 now runs after N2/N1 ingest; 286 reading rows accumulated over history vs 130 from one replay. Full run 91 s, quick 2 s; plant-proved both modes; empty input fails. | Opus agent | validator green, plant-proved (drop one repair → diff ≠ 0) | — | ☑ (650 held) |
| W02 | **Repair-replay gate.** Every table under `research/derived/repairs/` replayed against the export; a row whose `new` is absent fails (16 form_meanings repairs no-oped silently). | Opus agent | `validate_repairs_applied.py` | — | ☑ |
| W03 | **Exam level gate.** Every item's Japanese inside its level's taught set; ratcheted at today's counts (N5 orthography 3 clean of 379; N4 paraphrase 1 of 60). | Opus agent | `validate_exam_level_gate.py` | — | ☑ |
| W04 | **Practice-coverage gate.** Every unlocked item drilled by its own lesson; ratchet at 1,946 vocab / 567 kanji / 103 grammar absent. | Opus agent | `validate_practice_coverage.py` | — | ☑ |
| W05 | **Sentence-coverage gate** — DONE: `validate_sentence_coverage.py` over the export, per-(level,kind) ratchet holding `below` and `zero` separately (3,442 taught; 1,763 under floor, 1,562 at zero — N3 vocab 1,571 of 1,596 under floor); work list `research/reports/sentence_coverage_shortfall.json`. The 14,958 DB-only `needs_review` flags now export (vocab senses[], kanji readings[], family root; 14,923 reach a published level) and the provenance gate counts them. **Sequencing rule:** after any export, regenerate contracts before `validate_contracts` — the new fields are additional properties the previous contracts reject. | Opus agent | `validate_sentence_coverage.py`; provenance gate counts them | — | ☑ |
| W06 | **Approval ledger** — DONE: `contracts/review_ledger.schema.json` + `design/review_ledger.md` + `scripts/review_ledger.py` (one hash implementation shared with the review queue; the record hash excludes the exporter's own stamp so an approval cannot invalidate itself); `research/derived/review_ledger.json` starts empty and valid; the exporter stamps `review_status` only from a LIVE entry (hash match); `validate_review_ledger.py` reports stale entries as the re-review list and FAILS any stamp with no live entry behind it — plant-proved end to end (one record approved, rewritten → stale, never exported as approved). Release identity: `manifest.build` {date, git_head, per-entity sha256}; schema-currency redacts only date and head. | Opus agent | ledger validator green; one record approvable end to end | D4 default | ☑ |
| W07 | Gate hygiene: `audit_coverage.py` over the export; `run_golden.py` + `validate_generated_jp.py` into the suite (install `sudachidict_core`); `prompt_pt` into hygiene; stem-collision gate (92, ratcheted); doc numbers (exam_simulator.md, exam.server.ts, prototype/README, contracts/README "no measured enums", speaking_path.md). | Opus agent | suite | — | ☑ |

### Lane 1 — M1: identity settled (sequential; each ends with a Fable sample)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W08 | **A3 grammar merges** — DONE: gp→da-desu and gp-152→te-hoshii via `scripts/migrate_grammar_merge.py` (step 113 of the rebuild manifest): every loser field diffed and salvaged verbatim into the survivor (never glued), 297/298 and 177/178 live references re-pointed (the one left in each is `design/grammar_placement.json`, deliberately), the stored `cumulative_known_set` of 281/157 lessons re-pointed, losers kept as `deprecated_by` redirects and published in `corpus/grammar_deprecated.json` (active grammar 496 → 494); the replay gate learned a `merged-away` marker that must chain through the redirect. Ledger: `research/reports/w08_merge_ledger.md`. Refused with reasons: U2 (cross-level), U3 (needs a sense split), D1 (two lessons), D3 (なくちゃ is a real variant). | Opus campaign | contracts + ledger gates; merge ledger; Fable sample of both survivors | W01 | ☑ |
| W08b | **Eight more certain duplicates** (U1 gp-100/gp-118, D2, D4, D5, D6, D7, D8, D10): each has ONE lesson unlocking both records — two SRS cards for one pattern. Not merged in W08 because each also decides which of two independently authored pt-BR explanations the learner reads (authoring), and two need a family or `forms[0]` fix first or the survivor inherits the defect. Mechanically each is one MERGES row + a measured `expect` block; the salvage rule keeps both explanations until an authoring pass reconciles them. | Opus agent | same gates as W08 | W08 | ☐ |
| W09 | **A9 vocab re-point** (22 records, 5,955 occurrences): one migration across every export, lesson, family, bank and speak unit; redirect table. Lesson-degradation check: every lesson's rendered body, exercises and cks byte-compared before/after modulo the slug. | Opus agent | `validate_stable_addresses`; migration ledger; diff report = slug-only | W01, W08 | ☐ |
| W10 | **A4 level evidence** — DONE. Formula recovered from `reconcile_levels.py::assign()` and restated in schema_v2.md (agreement = agreeing/consulted; denominator is the PANEL, not the survivors; sentinels '0' → 0.0, 'anchor' → 1.0). 200 repairs, both layers, no confidence recomputed: 132 N3 grammar '1/1' → '1/3'; 67 kanji whose tally belonged to the level the lists chose before the JLPT re-tag moved to the `anchor` sentinel they already cited; `vocab:1385390` '0'/0.5 → 0.0. L4–L6 ratchet RETIRED (ceilings deleted); new hard check L9 (numerator must tally the recorded votes) plant-proved with five plants. Left for D12: single-lineage N3 evidence, the collapsed `jlpt-lists` key on 4,446 N2/N1 vocab. | Opus agent | `validate_level_consensus` unheld | — | ☑ |
| W11 | **A6 homographs**: 4 wrong refs corrected; resolver reads the `<jp>reading</jp>` beside a ref; 5 certain exemption placements. Then **A5 family rebuild** (certain): `validate_families.py` first; builders recompute not append (26→41 grammar families, 364→496 memberships; conjugation 514→1,166); rename `function_set→topic_set`, `semantic_field→topic_residual` before anything links the slugs; `family.related[]` + `topic.family_ids[]` end to end; export the Layer-C provenance. Authored families are a teacher unit (W39). | Opus campaign | families validator, graph gate | W08; D14 default | ☐ |

### Lane A — the JLPT course becomes an app (M2, M3)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W12 | **Orthographic relink** — cheapest coverage in the project: lifts 568 N5/N4 records over ≥3 (N5 → 99.3%, N4 → 99.2%); the exporter fix restoring sentence_vocab recovers 343 cards' examples. | Opus agent | W05 ratchet drops | W05 | ☐ |
| W13 | **N3 exemplification** via the mined-stage pipeline: 1,461 of 1,596 N3 vocab at zero sentences; 17 grammar points at zero, 67 under five; 43 with no real candidate go to generation as the spec-1.2 last resort. | Opus campaign | W05 floor reached for N3; Fable sample 30 | W05, W10 | ☐ |
| W14 | Lesson sentence re-selection: 116 lessons render none; 178 above-level links, 147 i+1 breaches (baseline frozen); pre-N5 survival words get `<vocab ref>` chips; orphan sweep (503 sentences). | Opus campaign | gating ratchet shrinks | W12, W13 | ☐ |
| W15 | **A1 real passages**: 286 Layer-C passages, 3–6 connected sentences, level-gated to the gating lesson's known set, register-appropriate, independently verified; a coherence check (one topic, tense/pronoun continuity) becomes a validator. Embedded in 235 lessons. **Authoring ◐:** 286 written under research/derived/passages/, verifiers fixed 163 in place; ~13 fail max_new=0 for a reason that is NOT the passage — the gating lesson's grammar target is built on a word the lesson never unlocks (なる in n5-adjetivos-05, こと in n4-oracoes-relativas-02, 間 in n4-oracoes-relativas-03, なかなか in n4-potencial-04, 関する in n3-perspectiva-01, これ/それ in n5-desu-wa-04, and the ください→下さる lemma trap that makes てください unusable in every N5 passage). Those are course-data gaps for W21b (move/add the unlock in the teaching lesson) and one dissector rule (a surface-known word must not resolve to an unknown lemma). Apply step: Sudachi tokens, reading.tokens/uses rebuilt, then W16. | Opus campaign | `validate_readings` max_new=0, coherence gate; Fable sample 30 | W09 | ◐ authored |
| W16 | Re-derive 286 `reading_comp` questions and re-blank `text_grammar` at token boundaries over the new passages; in-lesson reading boxes ask the comprehension question they already have; `reading.uses` documented as a snapshot. | Opus agent | exam rule I | W15 | ☐ |
| W17 | **A2 builder fixes**: the nine + n3 linker reading match (135 items) + bunsetsu sentence_order (45) + homophone-set dedupe + level gate (W03) + 4 options + explanations on auto-graded items. Prototype diff vs current banks: zero unexplained changes. **Level rule (from W03):** select against the last lesson's cks — every kanji in stem/options/passage/script, the item's vocab, the source sentence's token vocab and grammar tags. W03 measured that 93% of today's 3,565 inappropriate items fail on kanji alone and that the level-clean pool is 10–100× the paper at every level (N5 orthography IS buildable: 177 level-clean words vs a floor of 15). **Design point to settle in W17, not silently:** the real JLPT prints furigana on above-level kanji at N5/N4; the builder may either select level-clean Japanese or emit a ruby form for untaught kanji, but then the item must CARRY that form and the gate must accept an item only when every untaught kanji is ruby-covered. Default: level-clean where the pool allows (all families per W03), ruby only for reading_comp passages. Then every ceiling in `exam_level_baseline.json` goes to 0 in the same commit, which turns sufficiency into a hard failure. | Opus campaign | W03 green at ceiling 0 on the regenerated banks; diff report; Fable sample 30 | W01, W03, W09, W16 | ☐ |
| W18 | **Regenerate all 40 banks**; 118 removed items stay out; INDEX rewritten. | Opus agent | full gate | W17 | ☐ |
| W19 | Simulator — DONE (prototype + design/exam_scoring.md): 得点区分 scoring with the house approximation labelled as such (linear map of raw section percent onto the official range; `scaled: null` and verdict `incomplete` for an unsat section, never 0); pass marks and sectional minima sourced to jlpt.jp + the HK administering body (read 2026-09-02) with the stated caveat that no publisher outside the administering network exists; `present()` for the 110 empty-question listening items; listening sections gated behind audio-present; study mode over the banks filtered to a lesson's cks (365 / 1,567 / 3,430 eligible items at the N5/N4/N3 end-of-level lessons); `sentence_order` accepts `accepted[]` when present; `ExamAttempt` in snake_case matching `exam_attempt.schema.json`. Typecheck, build, no-client-leak all clean; smoke-tested N5 and N3 papers. Capability routing and persistence remain with W26/D8. | Opus agent | prototype runs a scored paper; contracts | W18; D-scoring | ☑ |
| W20 | **Per-item practice campaign**, kanji first (567 kanji, 1,946 vocab, 103 grammar absent from their own lesson); 4-option MCQs (493 of 676 offer 3); `reading` and `ordering` exercise types populated; handwriting per D5. **Kanji half authored ◐:** 899 verified exercises over 178 lessons in `research/derived/pending/practice_kanji_exercises.json` (the assembler consumed the workflow's verified list and excluded the 93 unverified — the behaviour W27's assembly lacked); schema-checked against the exercise contract; a simulated apply on a copy takes kanji absent to **0 at every level** (92/173/316 → 0) and practised overall 27.9% → 42.6% under `validate_practice_coverage`'s own rule. Apply step (after W09): insert into the DB exercise table + `research/derived/lessons/` + one `<exercise ref>` node per item in each body; drop five practice exemptions, keep three; then the vocab half (2,321 absent) and grammar (35). | Opus campaign | W04 ratchet → floor; Fable sample 30 | W04, W09 | ◐ kanji authored + simulated |
| W21 | **A7 needs[]** — derivation DONE (`scripts/derive_needs.py`, `research/derived/needs_edges.json`): 7,912 raw → 700 direct edges, true transitive reduction, acyclic, 60 roots each with a reason. Apply step: write `needs[]` (lesson-typed, `{type:"lesson", ref, note}`) into the DB + authoring source and re-export; hand-author the pre-N5 kana chain (41 lessons have no derivable edge — the strand references only its own family); treat a depth-0 root deep in the course (11 review/kanji-exame lessons) as unplaceable in D2. **A7 furigana** on all 875 kanji `<jp>` spans with the validator's regex made kanji-implies-attribute. | Opus agent | course chain + lesson bodies gates | W09 | ◐ derived |
| W21b | **Forward references (course-order debt).** 601 lesson→item uses point at an item taught LATER (kanji 360, vocab 251, grammar 27): 27 same-topic (move the unlock or the reference), 426 same-level cross-topic, 148 across levels (the frozen i+1 backlog). Ledger in `research/reports/w21_needs_report.md`. Campaign: fix by moving the unlock earlier where the earlier lesson can carry it, else rewrite the reference; the gating ratchet (check C/D) must shrink to 0 for same-topic and same-level. Also: `item_refs` on exercises exists in the authoring source and is empty everywhere — populating it is what makes W23's mistake index and W04's answer channel real. | Opus campaign | gating ratchet → 0 for same-topic/same-level | W09, W21 | ☐ |
| W22 | N3 dead end and features: `feat:jlpt-sim-n3` in the enum; a real N3 review topic; the 12 never-unlocked features given home lessons; conjugation-form unlocks so drills gate (0 of 322 cks carry any). | Opus agent | unlock ledger | W21 | ☐ |
| W23 | Assessment: target-item refs on exercises (design-owned schema edit) for a mistake index; topic-level test entity (median 82 keyed items/topic); placement test over the item→lesson index. | Opus agent | contracts | W18, W20; D2 for placement | ☐ |
| W24 | Capability layer: a vocabulary capability kind (34 N3 lessons map to nothing); can-do text and exam link on the schema. | Opus agent | `validate_capabilities` | W22 | ☐ |
| W25 | N3 rebalance (median 18 new words/lesson vs 7; 0 of 101 lessons with 4+ examples) and N3 中文・長文 / 情報検索 sections. | Opus campaign | course + exam gates | W13, W15, W20; D11 | ☐ |

### Lane B — memorization (M4)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W26 | **User-state contracts** (logical) — DONE: seven runtime entities (`user` added: the scheduler block is per account), `card` (a version-tagged cache replayable from `review_log`), `review_log` keyed on card_id never the item, `lesson_progress`, `exam_attempt` ((user, level, attempt_no) is the seed), `skill_state`, `feature_state`; a declared `runtime` class in the manifest (`x-yomineko.class`), gated both ways and plant-proved; `build_manifest.ts_type` now resolves local `$defs` (two fields had silently become `unknown` in types.ts); D6 written as a dated decision in both design docs with the stale claims struck through, not deleted. No `deck` entity by design (a closed registry). Six srs_design.md claims contradicted by the data are listed in design/user_state.md. `validate_card_content.py` (W28) still to come. | Opus agent | contracts + `validate_card_content.py` | D6 default; D8 later | ☑ (cards gate pending) |
| W27 | **Production answer keys** on every card (883 of 2,946 prompts ambiguous); the sense a card tests is its lesson's introducing sense; the 70 shared headwords to the teacher queue. **Authored ◐:** 2,946 rows in `research/derived/pending/card_production_keys.json` (0 still-ambiguous prompts, accept sets validated against the registry) — but the assembly was rebuilt from author files and the index-keyed verifier verdicts could be paired to only 5 of 30 batches, so every row is marked AUTHORED, not verified. **W27v:** a fresh verification pass keyed by (lesson, vocab) that applies corrections and sets `verified` per row; then the apply. | Opus campaign | card-content gate; Fable sample 30 | W08, W09, W26 | ◐ authored, re-verify pending |
| W28 | Example sentence and cloze on every card (1,545 lack one; 343 from W12, rest from W13); per-card `card_types`; per-card tags; leech hook. | Opus agent | card-content gate | W12, W13, W26 | ☐ |
| W29 | Kana cards one glyph per card (57 family cards for 211 glyphs today); listening cards after audio. | Opus agent | card-content gate | D6; W35 for listening | ☐ |
| W30 | Speak-path cards into `deck:phrases` (72 units emit 0 today). | Opus agent | srs decks gate | D10 default; W27 | ☐ |

### Lane C — speaking path (M5)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W31 | **A8 register**: field on `sentence` with the D7 value set; populate 5,889 (JMdict misc where present, authored elsewhere, `needs_review`); filter in the speak builder + blocklist mechanism (list is the owner's), applied to `drills[].examples` too. **Lessons untouched, proven by a byte-diff of course/**. | Opus campaign | register validator; course/ diff = 0; Fable sample 30 | D7 default | ☐ |
| W32 | R87 survival cores for the 11 stages without one; mine `arrival` (48 real candidates for 36 slots) and `health` (50) to parity; the ~16 canonical survival frames absent from the corpus, authored under D10. | Opus campaign | speak gate; Fable sample | W31; D10 default | ☐ |
| W33 | Audio schema now: `audio_ref`/`audio_source` on sentence and per-sentence in speak_unit (schema_v2.md line 128 always specified it). | Opus agent | contracts | — | ☐ |
| W34 | R78 strand validator (12/12 stages out of band) and rebalance; R83 spiral; semantic near-duplicate rule above R86; `vocab.freq_rank` exported; the path in `course/manifest.json` + the capability map; stage checkpoints. | Opus agent | new checks green | W32 | ☐ |
| W35 | Audio assets: 855 exam listening lines + 72 speak units + vocab; pronunciation QA. | owner pipeline + Opus QA | audio-present gates | **D3 BLOCKING** | ☐ |
| W36 | Voice play mode contract: ASR target, scoring, per-attempt record, shadowing rendered. | Opus agent | contracts; prototype | **D3 BLOCKING** | ☐ |

### Lane D — platform and the review loop (M6, M7)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W37 | Layer/source backfill on the 11 entities (11,695 records) carrying none; per-field layer for mixed registries. | Opus agent | provenance gate with required fields | D13 default | ☐ |
| W38 | Teacher tooling: `.md` views for corpus registries; `review_queue.py` over the export with item ids; approvals and teacher edits flow back as replayable tracked scripts (W01's path). **Queue half DONE:** `scripts/review_queue.py` over the export — 8,328 flagged records / 58,765 targets with ids, N5 slice (1,209) listed in full, reason classes on 66.8% (83% in N5), `--subtract <ledger>` joining on (slug, field, locale, content hash) proven against six ledgers, `--check`; the old DB exporter and its June report retired. The 14,958 DB-only flags would add ~1.8× once W05 exports them. | Opus agent | md-views gate extended | W06 | ◐ queue done |
| W39 | Named teacher approving N5 through the ledger; correction-rate metric; the §9.4 sampled human-review floor; authored Layer-C families and the 70 headword rulings. | **owner/teacher** | ledger shows approvals | **D4 BLOCKING** | ☐ |
| W40 | **A7 en_layer + locale parity.** Design half DONE (design/i18n.md scope table, `translation_layer` map spec, parity-validator spec R1–R7; research/reports/w40_locale_design.md). Apply half: emit `translation_layer` on sentences (exporter rule: `sentence.en` column → A, localized_text en → B); build `validate_locale_parity.py` from the spec; backfill the 10,514 required-scope `en` gaps — 6,467 are content-only, 4,047 need exporter plumbing first (`export_corpus.py` kanji/kana paths pass no `en=`); delete or populate the 3 dead LocaleText fields (`kanji.notes`, `family.description`, `family.members[].note`, null in 100%); convert the 284 bare `prompt_pt` strings in speak units to locale objects (an i18n principle-1 violation that survived the 2026-06-14 migration); note `lesson.body` is a bare string — the largest learner-facing text — so a second locale is not structure-free there. | Opus agent | parity gate green at ceiling; contracts | W01; D15 | ◐ design done, awaiting apply |
| W41 | API contract from the manifest; `sync-data.mjs` reads the manifest, not hardcoded globs — DONE. `design/api_contract.md`: 23 content-entity route families (stable id, level filters only where records carry `level`), the four spec §1.7 cross-reference queries as routes over stored edges, `/v1/me/...` user-state families (storage = D8), per-entity ETags from `build.entities`, locale fallback pt-BR → en, `deprecated_by` served as 301 + redirect body, exam/drill items never served with keys. `sync-data.mjs` rewritten over the manifest (glob, packing, stable id, count; runtime skipped by class; empty glob or count mismatch is a hard error); maps keyed by full stable id; `app/data/_build.json` carries the build hashes; `validate_prototype_sync` re-derives the projection from the same manifest and checks the hashes (plant-proved: flipped hash, stale sync, dropped record). Typecheck/build/leak/sync all green; every record count identical to before. | Opus agent | prototype sync gate | W06 | ☑ |
| W42 | Attribution: kanjialive (1,233) and strokesvg (162) sections + dataset rows — DONE for the sections (ATTRIBUTION.md, design/sources.md, checksums recorded). Findings: strokesvg kana SVGs are **OFL 1.1** (Klee One), whose §2 requires the full licence text and both copyright lines in each copy — a credits bullet does not comply; Kanji Alive's CC BY 4.0 was recorded from a 2026-06-26 reading and no upstream licence file was archived (now fetched into research/datasets/kanjialive/ if the fetch succeeded — see the report). **D9 evidence measured:** (a) KanjiVG — the only shipped field is `kanjivg_ref`, 2,131 values all equal to the kanji's own codepoint, zero geometry, so the CC BY-SA flag can close once the raw XML leaves the working tree; (b) Tatoeba usernames were never stored (only ids; `users_sentences.csv` never fetched), while every Tatoeba sentence keeps its id in its slug, so per-sentence *linking* is free and per-sentence *author naming* needs a new dump — ATTRIBUTION.md currently promises the latter "where feasible". | Fable | ATTRIBUTION.md | **D9 BLOCKING** for the two rulings | ◐ sections done; rulings open |
| W43 | Physical DB / hosting schema for W26. | Opus agent | — | **D8 BLOCKING** | ☐ |
| W44 | N2/N1 beyond bank-only. | — | — | **D1 BLOCKING** | ☐ |

---

## 4. Decisions

**Defaults I proceed with unless overruled** (each named by the unit that consumes it):

| id | question | default |
|---|---|---|
| D4 | approval semantics | per record and per locale, content-hash anchored, `reviewed_by` + `approved_at`, no expiry (W06) |
| D5 | handwriting | retire the 691 cards until a widget exists (W20) |
| D6 | kana in FSRS | keep; one glyph per card (W29) |
| D7 | register value set | `neutral / polite / casual / formal / vulgar / archaic / epistolary / dialect / slang` in schema_v2.md (W31) |
| D10 | speak SRS decks; authored sentence leading a stage | `deck:phrases`; yes, `ai_generated + needs_review`, ≤1 of 6 per unit (W30, W32) |
| D11 | N3 pacing and the ~750-word band gap | decide with W20's budget visible (W25) |
| D13 | layer per record vs per field | per field where a record mixes layers (W37) |
| D14 | kanji_component families | drop the cache; answer from `kanji.components` as the design says (W11) |
| D-shape | en_layer shape | **settled by W40 design:** `translation_layer: {"en": "A"\|"B"}` on `sentence` only — the one field path that mixes layers (all 109,976 derived en rows are B; the three Layer-A registry fields are A by construction); a map, not a scalar, so pt-BR's layer and a future es-LA fit without a second field |
| D15 | Are `kanji.readings[].note` (3,679) and `irregular_note` (99) REQUIRED to carry `en`? They are Layer-C pedagogy on a corpus registry; W40 chose "registry ⇒ required". Flipping to optional drops the en backfill from 10,514 to 6,736 fields. | default **required** (the registry rule); worth an explicit answer before W40's apply step |
| D-scoring | JLPT score bands | sourced with the timing table's standard: two independent checks, dated, uncertainty stated (W19) |

**Blocking — only the owner can answer:**

| id | question | blocks |
|---|---|---|
| D1 | N2/N1 stay bank-only, or full levels? | W44 |
| D2 | what "lesson complete" means; placement policy (score→entry; does placing out seed cards?). **Inputs now measured by W21:** max prerequisite depth 52, a learner placing into a lesson skips 74 lessons on average, the early-N5 core is the hub (`n5-desu-wa-02` has 252 dependents); 11 review/kanji-exame lessons deep in the course have zero ancestors and must be treated as unplaceable, not free. | W23 placement only |
| D3 | TTS engine, voice, output licence for a paid app; ASR engine; is romaji a correct production answer? | W35, W36 |
| D4 | a named reviewer | W39 (the ledger itself does not wait) |
| D8 | real DB / hosting | W43 (logical contracts do not wait) |
| D9 | KanjiVG flag closable? bulk vs per-sentence Tatoeba credit? | W42 |
| D12 | a third independent level source for N3+, or relax spec 1.5 formally | the level-evidence claim on N3 |

---

## 5. What "as close to 100%" means

By machine the corpus can reach *verified and review-ready* everywhere: Layer-A anchored where an
anchor exists, adversarially checked AI-on-AI, sampled by Fable, held by the gate. It reaches
*approved* only through D4. W06 is deliberately in M0 so a teacher can start on N5 while Opus is
still working on N3.

## 6. Next five

W01 → W02 → W03/W04/W05 (parallel) → W06 → W07, then Lane 1 in order. Each lands as its own commit
with the gate green and this table updated.
