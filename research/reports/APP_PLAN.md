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
| W01 | **DB rebuildability.** `scripts/rebuild_index.py` = ingest from datasets + `replay_all.py` extended to replay every tracked repair script in commit order. `validate_index_rebuildable.py` rebuilds into a temp DB, exports, diffs against committed JSON: byte-identical or FAIL. | Opus agent | validator green, plant-proved (drop one repair → diff ≠ 0) | — | ☐ |
| W02 | **Repair-replay gate.** Every table under `research/derived/repairs/` replayed against the export; a row whose `new` is absent fails (16 form_meanings repairs no-oped silently). | Opus agent | `validate_repairs_applied.py` | — | ☐ |
| W03 | **Exam level gate.** Every item's Japanese inside its level's taught set; ratcheted at today's counts (N5 orthography 3 clean of 379; N4 paraphrase 1 of 60). | Opus agent | `validate_exam_level_gate.py` | — | ☐ |
| W04 | **Practice-coverage gate.** Every unlocked item drilled by its own lesson; ratchet at 1,946 vocab / 567 kanji / 103 grammar absent. | Opus agent | `validate_practice_coverage.py` | — | ☐ |
| W05 | **Sentence-coverage gate.** ≥3 sentences per taught vocab, ≥5 per grammar, hard, over the export (advisory over SQLite today). Plus: export the 14,958 `needs_review` flags the DB holds on vocab_sense/kanji_reading/family. | Opus agent | `validate_sentence_coverage.py`; provenance gate counts them | — | ☐ |
| W06 | **Approval ledger.** `review_status` per record and per locale, anchored to a content hash (an approval must not transfer onto rewritten text — four campaigns rewrote candidate text this session); `reviewed_by`, `approved_at`; exported; `validate_review_ledger.py`. Release identity in the manifest (build date, per-entity content hash) lands with it. | Opus agent | ledger validator green; one record approvable end to end | D4 default | ☐ |
| W07 | Gate hygiene: `audit_coverage.py` over the export; `run_golden.py` + `validate_generated_jp.py` into the suite (install `sudachidict_core`); `prompt_pt` into hygiene; stem-collision gate (92, ratcheted); doc numbers (exam_simulator.md, exam.server.ts, prototype/README, contracts/README "no measured enums", speaking_path.md). | Opus agent | suite | — | ☐ |

### Lane 1 — M1: identity settled (sequential; each ends with a Fable sample)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W08 | **A3 grammar merges** gp→da-desu (840 refs), gp-152→te-hoshii (591): every loser field diffed against the survivor and merged in if the survivor lacks it; `deprecated_by` redirect kept; the 3 untriaged collisions and 10 duplicate pairs triaged, only the certain merged. | Opus campaign | contracts + ledger gates; merge ledger; Fable sample of both survivors | W01 | ☐ |
| W09 | **A9 vocab re-point** (22 records, 5,955 occurrences): one migration across every export, lesson, family, bank and speak unit; redirect table. Lesson-degradation check: every lesson's rendered body, exercises and cks byte-compared before/after modulo the slug. | Opus agent | `validate_stable_addresses`; migration ledger; diff report = slug-only | W01, W08 | ☐ |
| W10 | **A4 level evidence.** Direction per the audit: the 132 N3 grammar records at '1/1'/0.34 have the agreement string wrong (one list of three → '1/3'), not the confidence; formula restated in `schema_v2.md`; `vocab:1385390` sentinel; L4–L6 ratchet retired. | Opus agent | `validate_level_consensus` unheld | — | ☐ |
| W11 | **A6 homographs**: 4 wrong refs corrected; resolver reads the `<jp>reading</jp>` beside a ref; 5 certain exemption placements. Then **A5 family rebuild** (certain): `validate_families.py` first; builders recompute not append (26→41 grammar families, 364→496 memberships; conjugation 514→1,166); rename `function_set→topic_set`, `semantic_field→topic_residual` before anything links the slugs; `family.related[]` + `topic.family_ids[]` end to end; export the Layer-C provenance. Authored families are a teacher unit (W39). | Opus campaign | families validator, graph gate | W08; D14 default | ☐ |

### Lane A — the JLPT course becomes an app (M2, M3)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W12 | **Orthographic relink** — cheapest coverage in the project: lifts 568 N5/N4 records over ≥3 (N5 → 99.3%, N4 → 99.2%); the exporter fix restoring sentence_vocab recovers 343 cards' examples. | Opus agent | W05 ratchet drops | W05 | ☐ |
| W13 | **N3 exemplification** via the mined-stage pipeline: 1,461 of 1,596 N3 vocab at zero sentences; 17 grammar points at zero, 67 under five; 43 with no real candidate go to generation as the spec-1.2 last resort. | Opus campaign | W05 floor reached for N3; Fable sample 30 | W05, W10 | ☐ |
| W14 | Lesson sentence re-selection: 116 lessons render none; 178 above-level links, 147 i+1 breaches (baseline frozen); pre-N5 survival words get `<vocab ref>` chips; orphan sweep (503 sentences). | Opus campaign | gating ratchet shrinks | W12, W13 | ☐ |
| W15 | **A1 real passages**: 286 Layer-C passages, 3–6 connected sentences, level-gated to the gating lesson's known set, register-appropriate, independently verified; a coherence check (one topic, tense/pronoun continuity) becomes a validator. Embedded in 235 lessons. | Opus campaign | `validate_readings` max_new=0, coherence gate; Fable sample 30 | W09 | ☐ |
| W16 | Re-derive 286 `reading_comp` questions and re-blank `text_grammar` at token boundaries over the new passages; in-lesson reading boxes ask the comprehension question they already have; `reading.uses` documented as a snapshot. | Opus agent | exam rule I | W15 | ☐ |
| W17 | **A2 builder fixes**: the nine + n3 linker reading match (135 items) + bunsetsu sentence_order (45) + homophone-set dedupe + level gate (W03) + 4 options + explanations on auto-graded items. Prototype diff vs current banks: zero unexplained changes. | Opus campaign | W03 green on the regenerated banks; diff report; Fable sample 30 | W01, W03, W09, W16 | ☐ |
| W18 | **Regenerate all 40 banks**; 118 removed items stay out; INDEX rewritten. | Opus agent | full gate | W17 | ☐ |
| W19 | Simulator: JLPT scoring model (scaled scores, sectional minima, pass mark — sourced to the timing table's standard); `present()` for 110 empty-question listening items; listening sections behind an audio-present check; study mode filtered to the learner's cks; sentence_order acceptability grading; `exam_attempt` contract + capability routing (logical; physical waits on D8). | Opus agent | prototype runs a scored paper; contracts | W18; D-scoring | ☐ |
| W20 | **Per-item practice campaign**, kanji first (567 kanji, 1,946 vocab, 103 grammar absent from their own lesson); 4-option MCQs (493 of 676 offer 3); `reading` and `ordering` exercise types populated; handwriting per D5. | Opus campaign | W04 ratchet → floor; Fable sample 30 | W04, W09 | ☐ |
| W21 | **A7 needs[]** derived from cks deltas, acyclic, published; **A7 furigana** on all 875 kanji `<jp>` spans with the validator's regex made kanji-implies-attribute. | Opus agent | course chain + lesson bodies gates | W09 | ☐ |
| W22 | N3 dead end and features: `feat:jlpt-sim-n3` in the enum; a real N3 review topic; the 12 never-unlocked features given home lessons; conjugation-form unlocks so drills gate (0 of 322 cks carry any). | Opus agent | unlock ledger | W21 | ☐ |
| W23 | Assessment: target-item refs on exercises (design-owned schema edit) for a mistake index; topic-level test entity (median 82 keyed items/topic); placement test over the item→lesson index. | Opus agent | contracts | W18, W20; D2 for placement | ☐ |
| W24 | Capability layer: a vocabulary capability kind (34 N3 lessons map to nothing); can-do text and exam link on the schema. | Opus agent | `validate_capabilities` | W22 | ☐ |
| W25 | N3 rebalance (median 18 new words/lesson vs 7; 0 of 101 lessons with 4+ examples) and N3 中文・長文 / 情報検索 sections. | Opus campaign | course + exam gates | W13, W15, W20; D11 | ☐ |

### Lane B — memorization (M4)

| id | unit | runner | done | needs | status |
|---|---|---|---|---|---|
| W26 | **User-state contracts** (logical): `card`, `review_log` (rating, elapsed, scheduled, state, stability/difficulty snapshot), `lesson_progress`, `exam_attempt`, `feature_state`, `skill_state`; card and deck become manifest entities; srs_design vs learning_science reconciled. FSRS-6 needs nothing per card beyond a stable id and history — verified. | Opus agent | contracts + `validate_card_content.py` | D6 default; D8 later | ☐ |
| W27 | **Production answer keys** on every card (883 of 2,946 prompts ambiguous); the sense a card tests is its lesson's introducing sense; the 70 shared headwords to the teacher queue. | Opus campaign | card-content gate; Fable sample 30 | W08, W09, W26 | ☐ |
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
| W38 | Teacher tooling: `.md` views for corpus registries; `review_queue.py` over the export with item ids; approvals and teacher edits flow back as replayable tracked scripts (W01's path). | Opus agent | md-views gate extended | W06 | ☐ |
| W39 | Named teacher approving N5 through the ledger; correction-rate metric; the §9.4 sampled human-review floor; authored Layer-C families and the 70 headword rulings. | **owner/teacher** | ledger shows approvals | **D4 BLOCKING** | ☐ |
| W40 | **A7 en_layer** (default sibling `en_layer: "A"|"B"` — 3,529 anchors vs 2,342 derived must be distinguishable without changing `translation.en`'s type); locale scope table, then the 10,692-field `en` backfill; `validate_locale_parity.py`. | Opus agent | parity gate | — | ☐ |
| W41 | API contract from the manifest; `sync-data.mjs` reads the manifest, not hardcoded globs. | Opus agent | prototype sync gate | W06 | ☐ |
| W42 | Attribution: kanjialive (1,233) and strokesvg (162) sections + dataset rows. | Fable | ATTRIBUTION.md | **D9 BLOCKING** for the two rulings | ☐ |
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
| D-shape | en_layer shape | sibling map (W40) |
| D-scoring | JLPT score bands | sourced with the timing table's standard: two independent checks, dated, uncertainty stated (W19) |

**Blocking — only the owner can answer:**

| id | question | blocks |
|---|---|---|
| D1 | N2/N1 stay bank-only, or full levels? | W44 |
| D2 | what "lesson complete" means; placement policy (score→entry; does placing out seed cards?) | W23 placement only |
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
