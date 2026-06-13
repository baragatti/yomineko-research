# Yomineko — Japanese N5 & N4 Corpus Build Specification

**Audience:** Claude Code (autonomous build agent)
**Author of spec:** project owner (senior dev)
**Goal of this run:** Build a *curated, verifiable, LLM-ready knowledge base* (the "corpus") for a Brazilian-Portuguese Japanese course covering **zero → full N5 → full N4**. This run produces **data and reference material only** — no app, no backend, no SRS scheduling logic yet.

---

## 0. HOW TO USE THIS DOCUMENT

1. Read this entire file before doing anything. Treat it as the master reference.
2. **First action (Phase P-pre):** `git init`, create the folder tree, and write `CLAUDE.md` (points to this spec + restates §1 non-negotiables) and `STATE.md` (the full phase plan with statuses + a `RESUME HERE` marker), then commit. This makes everything after it resumable.
3. **Then Phase L, then Phase R (Section 4)** — before any building. Phase L mines the owner's local paid course in a clean-room, de-identified way (§1.4 — no copying, no names). Phase R research-audits and self-improves this whole plan/schemas, measures whether the sources can deliver, and rewrites weak parts. **Do not start P0 until Phase R is approved by the owner.**
4. Then work **phase by phase, topic by topic**, committing after every completed unit (Section 8). Long runs may span several sessions — the work must be fully resumable.
5. Language rule: **all orchestration, code, commits, and internal notes are in English. ALL learner-facing content is in Brazilian Portuguese (pt-BR).** See Appendix B.
6. Use **maximum reasoning effort** for Phases L/R and all design/critique/authoring work (configure Claude Code to use the strongest available model with a high extended-thinking budget); the mechanical data-ingestion phases can use a lighter setting.

**To run it:** put this file in the project folder, open Claude Code there, and paste the kickoff prompt below.

**To resume after any pause/crash:** reopen Claude Code in the same folder and say *"continue from STATE.md."* `CLAUDE.md` auto-loads and re-reads this spec; `STATE.md` says exactly where it stopped; git holds the last clean checkpoint; scripts are idempotent, so at worst it redoes the single unit that was in flight.

**Kickoff prompt the owner will paste:** *"Read `YOMINEKO_CORPUS_BUILD_SPEC.md` in full. **First**, do Phase P-pre: `git init`, create the folder tree, write `CLAUDE.md` and a `STATE.md` plan (phases P-pre → L → R → P0…P7, with statuses and a RESUME HERE marker), and commit. **Then Phase L**: analyze the local course at `C:\Users\WiseWolf\IdeaProjects\japorongo-back\files` (entry `biblioteca.json`) in an isolated clean-room pass — extract only abstract structure/ideas/gaps into `research/local-course-insights/`, copying no text and recording no names (§1.4). **Then Phase R**: research, audit, and self-improve this entire plan and its schemas against the goal of the best paid-grade Japanese course in Brazil — use maximum thinking. Produce `design/PLAN_REVIEW.md`, `reports/source_coverage.md`, `design/schema_v2.md`, `design/quality_rubric.md`, and a draft `design/course_outline.md`, then STOP and summarize what you changed and recommend before building. After I approve, proceed P0→P7 (build the corpus, then author Module→Topic→Lesson), committing after each topic and keeping STATE.md current. On any blocker or usage limit, leave STATE.md resumable with a RESUME HERE marker."*

---

## 1. OPERATING PRINCIPLES (NON-NEGOTIABLE)

This corpus must be good enough to sell. That means **verifiable, not "generated and prayed over."** Two mistakes are unacceptable: (a) factually wrong Japanese, and (b) content we cannot trace to a source.

### 1.1 Provenance / confidence layers
Every piece of content belongs to exactly one layer, and carries a `source` field naming where it came from.

- **Layer A — Authoritative (zero AI):** characters, readings, stroke order, base meanings, part of speech, radical decomposition, raw real-world example sentences. Comes *only* from the open datasets in Section 3. Treated as ground truth.
- **Layer B — Derived-and-verified (AI, but checked against Layer A):** pt-BR translations of meanings/sentences, per-token glosses, sentence dissections. Generated, then **machine-validated** against Layer A (Section 7).
- **Layer C — Pedagogical (AI, research-grounded):** module sequencing, didactic explanations, mnemonics, learning objectives. Free-form AI, but grounded in the methodology research (Phase P3), and always flagged for human (teacher) review.

### 1.2 Prefer selection over generation
When a real human-written sentence exists in the corpus (Tatoeba), **use it** rather than inventing one. AI generation of new sentences is a *last resort* to fill coverage gaps, and every generated sentence is flagged `ai_generated: true` and `needs_review: true`.

### 1.3 Separate fact from explanation
The *meaning* of 食べる comes from the dictionary (fact, Layer A → B). The *explanation of why the て-form behaves a certain way* is pedagogy (Layer C). Never store them in the same field. A reviewer must be able to trust Layer A/B blindly and audit Layer C selectively.

### 1.4 The local course material (read-only, clean-room, isolated)
The owner grants read-only access to a third-party **paid** PT course on local disk (entry file `biblioteca.json`, with nested per-module JSONs). It is used **only as a structural reference, in an isolated clean-room step (Phase L) that runs before research**, to learn *what topics exist, in what order, at what pacing, and which structural ideas work* — never its expression. **Hard rules, no exceptions:**
- **Never copy** any text, example sentence, explanation, exercise, or phrasing from it into our project — not verbatim, not lightly reworded. Only abstract, non-protectable *ideas, structure, and coverage* may inform us, always re-expressed in our own words at the level of method (e.g., "introduces counters right after numbers"), never content.
- **Never mention** the course's name anywhere in our project, nor any instructor/author names found in it. Strip and never store any identifying information.
- Phase L's **output is a de-identified abstraction only** (an abstract topic/sequence map as data points + a list of pedagogical ideas worth adapting, in our own words + a list of gaps we can beat) — not a copy. Never re-load the raw material into context as a generation source in any later phase.
- Purpose: ours must end up **more complete, more direct, more efficient, and better** than that paid course. Later we compare *coverage* (concepts, which are facts) to confirm ours is a superset — but every word of expression is our own.

### 1.5 The hard accuracy fact about "JLPT levels"
**There is no official JLPT vocabulary/kanji/grammar list.** Since the 2010 revision, the organizers publish no authoritative lists; every "N5 list" online is a community reconstruction, and they disagree (e.g., N5 kanji counts range from ~78 to ~103 across reputable sites). Therefore:
- Level assignment is **consensus-based**, not authoritative. Cross-reference **at least 3 independent lists** per level and record agreement.
- **Do NOT trust the `jlpt` field inside KANJIDIC2** as N1–N5 — that field encodes the *old pre-2010 4-level* JLPT and does not map cleanly to the modern N5–N1 scale. Use dedicated modern N5/N4 lists instead and reconcile (Phase P2).
- Every level tag carries `level_confidence` and `level_sources`.

### 1.6 Level-agnostic, future-proof schema
Design every entity so the **same schema works from N5 through N1**. `level` is *data, not structure* — adding N3/N2/N1 later is just inserting more rows, never a schema change. We populate only N5 and N4 now, but nothing in the model may assume those are the only levels (no logic that hardcodes a closed set of levels and would break on N3+). Build it once, correctly, for the whole JLPT range.

### 1.7 Everything is cross-referenceable (one graph)
The corpus is a **graph**, not isolated lists. Every entity links bidirectionally to every related entity: kanji ↔ vocab ↔ sentence ↔ grammar point ↔ family/group ↔ module. The structure must support arbitrary cross-cutting queries — treat these as design tests the finished corpus must pass:
- "All N5 sentences containing a godan verb from the *daily-routine* family **and** the を particle."
- "Every vocab item using the kun-reading た.べる of 食, with its dissected sentences."
- "All members of the 言-component kanji family across N5–N4, ordered by frequency."
- "Every grammar point that contrasts with は, with example sentences."
If a reasonable query like these can't be answered from stored links, the model is incomplete.

### 1.8 This plan is a hypothesis — improve it, and push back honestly
This document is the *starting* design, not holy writ. Phase R (Section 4) exists to stress-test and rewrite it. Throughout the build, if something here is insufficient to reach paid-grade quality — a thin source, a weak schema, an unrealistic threshold, a shaky sequencing choice — **say so and fix it**; don't silently produce mediocre output just to satisfy the letter of the spec. Honest pushback that improves the result is the goal. Two hard truths to internalize: (1) a fully-autonomous run is **not** trustworthy as the *final* product for something sold — the human teacher-review loop is mandatory, and the corpus must arrive **review-ready**, not review-skipped; (2) "best course in Brazil" is a quality bar to *measure against* (the rubric built in Phase R / used in Section 10), not a slogan — every phase must be checkable against it.

---

## 2. TECH SETUP & REPOSITORY LAYOUT

Recommended stack: **Python** for ingestion/validation (best Japanese NLP ecosystem), **SQLite** as the canonical store, **Markdown + JSON** as the human/LLM-readable export. (The future app is Flutter/Dart; the corpus is framework-neutral and travels fine.)

**Two layers — keep them separate.** The **corpus layer** = reusable registries (kanji, vocab, grammar) + the dissected-sentence bank, all addressed **by stable ID**. The **courseware layer** = the actual linear course as **Module → Topic → Lesson**, which *references* the corpus by ID and **never embeds it**. A sentence lives exactly once, fully dissected, in the corpus; every lesson that uses it stores only its **ID** (because each sentence carries far too much detail to duplicate, and we want a single source of truth pulled at runtime).

**Persist everything useful.** Anything fetched or derived that could help later — datasets, dictionaries, downloaded kanji data, extracted lists, reference notes, the Phase L abstraction, coverage probes — is **saved into `research/`**, versioned, never thrown away. The whole project is organized as **many small, modular files** with consistent schemas and a top-level `INDEX.md`, so an LLM can navigate, analyze, improve, and later implement it.

```
yomineko-research/             # project root (the corpus + courseware live here)
├─ INDEX.md                    # manifest: what every folder/file is — for LLM navigation
├─ CLAUDE.md                   # project memory: non-negotiables + conventions
├─ STATE.md                    # live plan + per-unit status + RESUME HERE
├─ README.md
├─ research/                   # EVERYTHING gathered/derived is persisted here, versioned
│  ├─ datasets/                # raw downloads (JMdict, KANJIDIC2, KanjiVG, Tatoeba, JLPT lists…) + checksums
│  ├─ derived/                 # cleaned/extracted data (per-level kanji/vocab lists, frequency, pitch…)
│  ├─ references/              # research notes + citations (methodology, competitor analysis)
│  ├─ local-course-insights/   # Phase L output ONLY: de-identified abstraction (no copied text, no names)
│  └─ coverage/                # source_coverage.md + probes (Phase R3)
├─ db/
│  └─ corpus.sqlite            # canonical database (all layers; schemas in Section 5)
├─ scripts/
│  ├─ analyze_local/           # Phase L reader: reads local biblioteca.json; emits abstraction ONLY
│  ├─ ingest/
│  ├─ validate/
│  └─ export/
├─ design/
│  ├─ PLAN_REVIEW.md           # Phase R self-improvement output
│  ├─ schema_v2.md             # pressure-tested schemas (Phase R4)
│  ├─ quality_rubric.md        # "paid-grade" yardstick (Phase R5)
│  ├─ curriculum.md            # pedagogy synthesis with citations (Phase P3)
│  ├─ course_outline.md        # Module → Topic → Lesson outline (Phase P4)
│  └─ sources.md               # provenance + license of every source
├─ corpus/                     # CORPUS LAYER export (by-ID, reusable)
│  ├─ kanji/                   # one file per kanji (or sharded) + index
│  ├─ vocab/                   # vocab records + index
│  ├─ grammar/                 # grammar points + index
│  ├─ sentences/               # the dissected-sentence bank (sharded) + index
│  └─ families/                # group/family records
├─ course/                     # COURSEWARE LAYER export (Module → Topic → Lesson)
│  ├─ n5/
│  │  ├─ topic-01-hiragana/
│  │  │  ├─ lesson-01.md  /  lesson-01.json
│  │  │  └─ ...
│  │  └─ topic-02-.../
│  └─ n4/
├─ reports/
│  ├─ validation.md            # QA gate results
│  └─ stats.md                 # counts per topic/lesson/level
└─ ATTRIBUTION.md              # required license attributions
```

Set up a Python venv. Pin dataset versions. Record every downloaded file's source URL, version, date, and SHA256 in `design/sources.md`.

---

## 3. AUTHORITATIVE DATA SOURCES (canonical inputs)

Download these in Phase P1. Verify each URL/license is still current at build time (do not assume; check). Capture license terms for each in `ATTRIBUTION.md` — this corpus may be used commercially, so attribution and commercial-use compatibility must be confirmed. (License interpretation is the owner's responsibility; record the facts so they can decide.)

### 3.1 Core dictionaries — `jmdict-simplified` (JSON)
`https://github.com/scriptin/jmdict-simplified/releases` — actively maintained (weekly releases), MIT-licensed tooling, JSON conversions of the EDRDG dictionaries. Pull:
- **JMdict** (`jmdict-eng` full + a `common-only` variant) → vocabulary: headwords, kana readings, senses, parts of speech, common-ness markers. This is the **vocabulary backbone**.
- **Kanjidic2** → kanji: on/kun readings, meanings, stroke count, grade, radicals. The **kanji backbone**. (Ignore its built-in `jlpt` field per §1.5.)
- **Kradfile/Radkfile** → kanji↔radical/component decomposition (for "what parts make up this kanji"). Memory-friendly, load fully.
- Optional: **JMnedict** (proper names) — not needed for N5/N4, skip unless useful.
- Note: JMdict has non-English gloss variants, but English coverage is the most complete. Use **English as the pivot** and translate to pt-BR in Layer B; do not assume a complete PT gloss set exists.

### 3.2 Stroke order — KanjiVG
`https://github.com/KanjiVG/kanjivg` — per-character SVG where **each stroke is ordered and numbered**, plus component grouping. License: CC BY-SA (note the **ShareAlike** — record it; storing a stroke-order reference per kanji is fine, but redistribution of derivative SVGs carries SA obligations). This resolves the "how to draw it" requirement **exactly**, not approximately. Store a per-kanji reference (filename / KanjiVG id) and, if useful, extract the stroke sequence.

### 3.3 Real example sentences — Tatoeba
`https://tatoeba.org/en/downloads` — community sentence corpus, **human-written**, with sentence↔translation links and some audio. License: CC BY 2.0 FR (record attribution requirement). Pull the Japanese (`jpn`) sentences, their **English** (`eng`) and **Portuguese** (`por`) translation links, and audio availability. This is the gold mine: it lets us **select** natural sentences containing target vocab/grammar instead of generating them — eliminating the single biggest AI error source (unnatural Japanese). PT translations exist but are sparser than EN; where PT is missing, translate from JP (cross-checking the EN) in Layer B.

### 3.4 Modern JLPT level lists (community, reconcile ≥3)
No official source exists (§1.5). Gather and cross-reference multiple, e.g.: JLPT Sensei, Jonathan Waller's lists (tanos.co.uk), Jisho's `#jlpt-n5`/`#jlpt-n4` tags, jpdb level decks, and well-known Anki decks (Tango N5/N4) for ordering. Use these to (a) decide membership of N5/N4 sets and (b) get a frequency/teaching-order signal. Record per-item which lists include it.

### 3.5 Frequency data (for sequencing)
For ordering by usefulness (so the learner gets high-value words first): a Japanese frequency list (e.g., a corpus-derived frequency such as those bundled with jpdb / common subtitle or web corpora). Used only to **rank** within a level, never to decide correctness.

### 3.6 Morphological analyzer — SudachiPy (CRITICAL anti-error tool)
Use **SudachiPy** + **SudachiDict-full** — the modern, production-grade Japanese analyzer (pin versions). Optionally `jamdict` for JMdict/KANJIDIC2 lookups. Per token it returns **surface form, dictionary form (lemma), reading, and part-of-speech**, and it supports **three split modes**: A (short units, finest granularity), B (middle), C (longest / named-entity). Store **both A and C**: parse each sentence in **mode C for the natural word boundaries** and in **mode A to expose the smallest teachable sub-units**, so a dissection can show "this is one word, built from these parts" — which directly feeds the *families* model (Section 5.6) and the "part-by-part" teaching the owner wants. We use SudachiPy — **not the LLM** — to produce the structural skeleton of every dissection; the LLM only adds the *pt-BR gloss-in-context* and the *explanation*. This is what makes the sentence bank trustworthy at scale.

### 3.7 Pronunciation / pitch accent (recommended, since the course targets speaking)
A pitch-accent dataset (e.g., the kanjium/OJAD-derived pitch accent data) to annotate words with accent pattern. Optional for N5/N4 but a real differentiator for "actually learning to speak."

### 3.8 Grammar points (no single open dataset)
Grammar has no clean authoritative dataset. **Enumerate** the canonical N5 and N4 grammar-point *lists* by cross-referencing multiple reputable references (e.g., JLPT Sensei grammar lists, Bunpro level paths, Tae Kim, Imabi). Use them to build the **list of grammar points per level** (this is the factual part — which points belong to N5/N4). Then write **original** pt-BR explanations (Layer C) and attach dissected examples drawn from Tatoeba. Do not copy explanations from any source.

---

## 4. THE BUILD PIPELINE (PHASES)

Build `STATE.md` from this. Each phase has a clear output and a checkpoint commit. **Phase P-pre runs first, then Phase L, then Phase R; L and R gate the build.** P1–P2 are mechanical (run unattended). P3–P4 are research/design. P5 builds the dissected-sentence corpus; P6 authors the Module→Topic→Lesson courseware. P7 is QA.

### Phase P-pre — Pre-flight scaffold (RUN FIRST, before anything else)
The point of this tiny phase is to make **every later phase — including the research in L and R — resumable from the very first moment.** Do this before reading the local course or searching the web:
- `git init` the project; create the folder tree from Section 2 (at least `research/`, `design/`, `reports/`, `scripts/`).
- Create `CLAUDE.md` pointing to this spec and restating the §1 non-negotiables (so future sessions auto-load the rules and re-read the spec).
- Create `STATE.md` containing the **full phase plan (P-pre → L → R → P0 → … → P7)** with a status field per phase/topic/lesson (`pending` / `in_progress` / `done` / `needs_review`) and a top **`RESUME HERE`** marker.
- Create `INDEX.md` (stub, updated as the project grows).
- Commit ("P-pre: scaffold + STATE + CLAUDE"). *(Do not write the SQLite schema yet — that waits for P0, after Phase R may revise it.)*

### Phase L — Local course analysis (clean-room, isolated; before research)
A standalone step to mine *structure and ideas* from the owner's local paid course **without copying or identifying it** (read §1.4 first — those rules are absolute). Run it isolated, before any web research, so its insights can inform Phase R.
- **Input:** read `C:\Users\WiseWolf\IdeaProjects\japorongo-back\files\biblioteca.json` and follow the nested per-module JSONs it references. Read-only.
- **Extract — ONLY abstract, non-protectable signal**, re-expressed in our own words: the list of modules/topics and their **order**; granularity and **pacing** (how much per lesson); which concepts are introduced together; structural ideas that look effective; and **gaps/weaknesses** we can beat (where it's thin, slow, or unclear).
- **Forbidden in the output (zero tolerance):** any verbatim or lightly-reworded text, any example sentence, any explanation, any exercise, and the course's name or any instructor/author name. Strip all identifying data. If unsure whether something is "idea" vs "expression," treat it as expression and do not reproduce it.
- **Output:** `research/local-course-insights/` with `topic_sequence.md` (an abstract ordered map, as data points), `ideas_to_adapt.md` (pedagogical approaches worth adapting, in our words), and `gaps_to_beat.md`. Commit. This **abstraction — not the raw material —** is what later phases may read.
- The raw material never re-enters context as a generation source after Phase L. Its only later use is a **coverage comparison** in P7, to confirm our course is a superset of its concepts and more complete.

### Phase R — Research, audit & self-improvement (RUN AFTER L; gate before any build)
The purpose of Phase R is to make sure this plan can actually produce a course at or above Brazilian paid-course level *before* committing hours to building. It consumes the Phase L abstraction. Run it with **maximum reasoning effort** (strongest model, high thinking budget). Nothing in P0+ starts until R is done and the owner approves the result.

**R1 — Critically audit this spec.** With deep thinking, write an honest critique of this document against the goal "best paid-grade Japanese course in Brazil, 0→100% N5 and 0→100% N4, for speaking / living / working in Japan." Name every weakness, gap, unrealistic assumption, and failure mode — be specific (e.g., grammar explanations are the real differentiator and are under-specified; Tatoeba in-level coverage is unmeasured; BR-PT pedagogy is thin).

**R2 — Research the quality bar and the methods.** Web-research, then synthesize originally (cite sources; copy nothing):
- How the **best curricula** sequence N5/N4: Genki, Minna no Nihongo, Tobira, Marugoto (JF Standard), Tae Kim, Imabi, Bunpro, WaniKani, major JLPT prep series. Extract their ordering logic and scaffolding patterns.
- The **competitive bar in Brazil**: what existing Brazilian Japanese courses (paid and free) offer and where they fall short, so we can define how we beat them — include Nikkei-community and university (e.g., USP) teaching resources/traditions.
- **SLA evidence** (deepen Appendix A): comprehensible input / i+1, retrieval practice, spacing, frequency-based vocab, output hypothesis, interleaving, mnemonics, component-based kanji, pitch accent.
- **Brazilian-Portuguese-specific** pedagogy: phonology transfer, false friends, where PT intuition helps/hurts — and flag honestly where little prior material exists and we are pioneering.

**R3 — Measure whether the sources can deliver (empirical, not assumed).** Actually probe the datasets and report real numbers in `reports/source_coverage.md`:
- How many reconciled N5/N4 kanji & vocab have complete JMdict / KANJIDIC2 / KanjiVG data (find the gaps).
- For a representative set of N5/N4 grammar points and target words: **how many Tatoeba sentences stay within the module's known set (i+1)?** What % already have Portuguese translations? Audio?
- Conclusion: are the thresholds (≥200–300 dissected sentences/module, "mostly real") realistic, or must they be adjusted and the AI-generation cap raised for some modules? Decide and record. If Tatoeba is thin, identify and vet supplementary open sentence sources (e.g., Tanaka corpus, other CC-licensed example sets).

**R4 — Pressure-test and improve the data schemas.** Represent hard real examples in the Section 5 schemas: a kanji with readings split across N5/N4; a sentence with stacked particles and a contracted verb form; a contrast pair (は vs が) as a family; a derivational word family; a counter; an irregular verb (する/来る). Wherever the schema is awkward or lossy, **revise it** and record the change in `design/schema_v2.md`, so the DB is genuinely complete, explained, detailed, and ready for an LLM to consume later.

**R5 — Define the quality rubric.** Write `design/quality_rubric.md`: concrete, checkable criteria for "paid-grade" across accuracy, explanation depth, example richness, sequencing soundness, completeness, and review-readiness. This rubric is the yardstick for the pilot (P5 gate) and final QA (P7).

**R6 — Self-improve the plan.** Produce `design/PLAN_REVIEW.md`: the critique (R1), the decisions made (level-membership policy — union/intersection/weighted; thresholds; source priorities; grammar-quality approach; BR-PT stance), an **improved-spec addendum**, and a first-draft `design/module_map.md` skeleton. **Then STOP and present a summary to the owner for approval before building.**

Output of Phase R: `PLAN_REVIEW.md`, `source_coverage.md`, `schema_v2.md`, `quality_rubric.md`, draft `module_map.md`. Commit. **Gate: owner approves before P0 begins.**

### P0 — Finalize scaffold & write schema (after R approval)
- The tracking scaffold (git, `CLAUDE.md`, `STATE.md`, folders) already exists from Phase P-pre. Here, finalize the rest: venv, `design/sources.md`, `ATTRIBUTION.md` stubs, and any remaining folders.
- Write the SQLite schema as migrations, using the **pressure-tested schemas from Phase R** (`design/schema_v2.md`), not the un-revised Section 5 draft.
- Output: structured project ready for ingestion, committed.

### P1 — Ingest authoritative data (unattended)
- Download all Section 3 datasets; record versions + checksums in `design/sources.md`.
- Parse JMdict, Kanjidic2, Kradfile/Radkfile, KanjiVG index, Tatoeba (jpn + eng/por links + audio) into SQLite raw tables.
- Build full-text/index on Tatoeba so sentences can be queried by contained lemma.
- Output: `corpus.sqlite` populated with raw authoritative data; a `stats.md` of row counts. Commit.

### P2 — Level reconciliation (unattended + brief review)
- Load the ≥3 community N5/N4 lists. Reconcile into a canonical `kanji.level`, `vocab.level`, `grammar.level` with `level_confidence` and `level_sources`.
- Flag disagreements (item in some lists but not others) in `reports/validation.md` for owner review.
- For each kanji, determine **which readings/meanings are introduced at N5 vs N4** (a kanji can appear at N5 with one reading and gain another at N4) — see §5.1. Seed this from the vocab that uses each reading at each level; mark uncertain cases `needs_review`.
- Output: every target item tagged with a reconciled level + confidence. Commit.

### P3 — Methodology & curriculum research (interactive/iterative)
Use web search to ground the pedagogy. **This research informs original design; nothing is copied.** Produce `design/curriculum.md` as an original synthesis **with citations**. Investigate (seed queries in Appendix A):
- Comprehensible input and the **i+1** principle (introduce ~one new item at a time).
- **Retrieval practice / testing effect** and the **spacing effect** (why SRS works; informs how material should be chunked for later SRS).
- **Frequency-based** vocabulary acquisition and the lexical approach (teach high-value words first).
- **Output hypothesis** (production, not just recognition — central, since the course targets speaking/working in Japan).
- **Interleaving** and **dual coding**; mnemonic/keyword methods for vocab and component-based methods for kanji.
- Sequencing specifics **for Portuguese speakers** learning Japanese (false friends, phonological hurdles, where PT intuition helps/hurts).
- The role of **pitch accent** and natural prosody for comprehensibility.
Output: `design/curriculum.md` (principles → concrete sequencing rules → chunk sizes → production goals per module), with sources. Commit.

### P4 — Course outline: Module → Topic → Lesson (design)
Turn the research + reconciled item sets + Phase L abstraction into a complete **course outline** in `design/course_outline.md`, structured as **Module (level) → Topic → Lesson**:
- **Module** = a JLPT level container: pre-N5, N5, N4.
- **Topic** = an ordered teachable unit within a module (e.g., Hiragana, Katakana, Greetings, Numbers & Time, Particles は/が, Verb て-form, Shopping). Topics carry the family/sequencing logic below.
- **Lesson** = an authored unit within a topic — the smallest learn-by unit, with dense pt-BR teaching text, exercises, and sentence references (Section 5.5).

**Family-driven sequencing (build the families first).** Organize teaching around *families* (Section 5.6), introduced in order of importance, taught part-by-part, then their governing rules — "famílias, depois as regras, depois as partículas," exactly as intended. Concretely:
- Build the family set first: semantic fields, kanji-component families, phonetic series, derivational word families, verb/adjective conjugation classes, particle/contrast sets, function sets. Assign every N5/N4 kanji, vocab, and grammar item to ≥1 family.
- Rank families by `importance_rank` (frequency + foundational value).
- Within a family, teach the **core member first** (`is_core`), then its **variations/derivations** by `intra_order` (e.g., 食べる → 食べ物 → 食事; or the godan rule taught once via `governing_rule_pt`, then drilled across the whole godan family).
- Introduce the **governing rule** (conjugation class, particle) at the moment its family needs it.
- A topic typically maps to one family (or a slice of a large one); families **spiral** — revisited in later topics/lessons in new contexts.
- Families are **cross-level** (`spans_levels`): a kanji-component family may include N5, N4, and N3 members; teach the in-level members now, keep the full structure so N3+ slots in later with no rework.

**Coverage requirements for the outline:**
- **Pre-N5 module (from absolute zero):** hiragana, katakana, pronunciation, intro to pitch accent, basic writing/stroke principles, survival greetings — as its own topics/lessons. Someone who knows *nothing* starts here and feels at home.
- **N5 then N4 modules:** sequence topics by a blend of (frequency × grammar dependency × functional theme). Weave functional contexts so it's useful for living/working in Japan: self-introduction, numbers/time/dates, shopping & money, food & restaurants, directions & transport, daily routine, family, work basics, etc. Apply **i+1**: ideally ≤1 new grammar point per lesson; spiral prior items.
- Every reconciled N5/N4 item is assigned to exactly one **introducing lesson** (and may recur later). For each module/topic/lesson define: objectives, prerequisites, the items it introduces, and **production goals** ("ao final, o aluno consegue …").
- Sanity-check ordering against the **Phase L abstraction only** (`research/local-course-insights/`) — never the raw material — and ensure our outline is at least a superset of its concept coverage, reorganized and improved in our own design.
- Output: complete `design/course_outline.md` (full Module→Topic→Lesson tree for pre-N5 + N5 + N4, every item placed). Commit.

### P5 — Sentence corpus: mining & dissection (the reusable bank)
Build the dissected-sentence bank (the reusable core — Section 6) so that **every target item in the course outline is richly covered**. The bank is global and **by-ID**; lessons reference it. Exact targets come from the rubric and the R3 coverage findings — aim for a **rich bank per topic** (on the order of hundreds of dissected sentences where the source material supports it) and at minimum **≥3 dissected sentences per vocab item and ≥5 per grammar point**.

**Pilot first (mandatory gate).** Before mass-producing, build **one complete topic end-to-end** — its sentence bank (this P5) *and* its authored lessons (P6) — then critique it hard against `design/quality_rubric.md`: is the Japanese correct, are the dissections genuinely useful, are the lesson texts and exercises paid-grade, did the schemas hold up, was Tatoeba coverage as predicted in R3? Fix the approach (and schema if needed), present the pilot topic to the owner, and only then scale. A flaw caught in topic 1 is cheap; the same flaw across the whole course is not.

For each target vocab item / grammar point:
1. **Select** real Tatoeba sentences that contain it *and* stay within (or just one step beyond) the learner's cumulative known set at that point in the outline (i+1). Prefer sentences with existing PT and/or audio.
2. If coverage is insufficient, **generate** minimal additional sentences (flagged `ai_generated`, within the per-topic cap from R3).
3. **Tokenize** each sentence with SudachiPy (§3.6, modes A+C) → structural skeleton (surface/lemma/reading/POS per token).
4. **Dissect** (Layer B): pt-BR natural translation + literal gloss; per-token context gloss in pt-BR; particle functions; link tokens to vocab/kanji/grammar registries; note conjugation forms.
5. **Validate** (Section 7) before saving. Save to DB.
- Work **topic by topic** following the outline; commit after each topic. Keeps long runs resumable (§8).

### P6 — Courseware authoring: Module → Topic → Lesson (the actual course)
For each topic, author its **lessons** — this is where the corpus becomes a course. Per lesson (Section 5.5):
- **Dense, rich pt-BR teaching text** (Layer C): explain the lesson's grammar/vocab/kanji clearly and deeply — the "como ninguém nunca viu antes" bar — written for both a true beginner and someone joining mid-course. Original prose; reference nothing from the local course.
- **Exercises** (typed: recognition, cloze/fill-the-blank, particle choice, sentence assembly, reading, production), defined as **structured data** so the future app can render and auto-grade them. Exercises reference corpus items and sentences **by ID**.
- **Sentence references**: lessons cite dissected sentences from the corpus **by ID only** (`sentence_refs[]`) — never embed sentence text or its dissection. The app pulls the full record from the bank at runtime.
- Plus objectives, prerequisites, new-items, and family/topic links.
Export each lesson to `course/<level>/topic-NN-<slug>/lesson-MM.{json,md}` (JSON = LLM/app-ready; MD = readable view for the owner to evaluate quality today). Also export the corpus layer to `corpus/...` (sharded by-ID files + indexes). Commit after each topic.

### P7 — Validation & QA gates (final + continuous)
Run the full validation suite (Section 7); write `reports/validation.md` and `reports/stats.md` (counts per lesson/topic/level). Run the **coverage comparison** against the Phase L abstraction to confirm our course is a **superset** of its concepts and more complete/direct/efficient (record the comparison; cite no raw material, name nothing). Verify the project is LLM-navigable (`INDEX.md` complete and accurate; files modular and consistently schema'd). The build is **done** only when acceptance criteria (Section 10) pass. Commit.

---

## 5. DATA SCHEMAS (canonical records)

Store in SQLite; mirror to JSON on export. Every record has: `id`, `source`, `level`, `level_confidence`, `level_sources`, `created_by` (`dataset` | `ai`), `needs_review` (bool). Use stable IDs so everything can be cross-linked (a sentence links to vocab links to kanji, etc.). Kanji, vocab, and grammar records additionally carry `group_ids[]` linking them to the families/groups they belong to (Section 5.6). Below are the **required fields** (extend as needed, never remove).

### 5.1 `kanji`
```
id
character                # 食
strokes                  # int (KANJIDIC2)
radicals[]               # components (Kradfile)
kanjivg_ref              # stroke-order reference (KanjiVG id/filename)
stroke_sequence[]        # optional ordered stroke data
meanings_pt[]            # pt-BR meanings (Layer B; from EN gloss)
readings:                # IMPORTANT: tagged by level of introduction
  - reading              # e.g., た.べる / ショク / く.う
    type                 # on | kun
    introduced_at_level  # N5 | N4 | later   (a kanji's readings split across tiers)
    example_vocab_ids[]  # vocab that uses this reading at that level
level                    # tier where the kanji itself is first introduced
notes_pt                 # pedagogical note (Layer C, optional)
```
The per-reading `introduced_at_level` is essential: the same character is taught at different depths across N5/N4. The kanji record must expose *which* readings/meanings belong to *which* tier.

### 5.2 `vocab` (lexeme)
```
id
headword                 # 食べる (kanji form if any)
kana                     # たべる
romaji                   # optional
pos[]                    # part(s) of speech (JMdict)
meanings_pt[]            # pt-BR senses (Layer B), each tied to the relevant JMdict sense
common                   # bool (JMdict common marker)
pitch_accent             # optional (§3.7)
kanji_ids[]              # kanji used in the headword
jmdict_ref               # source entry id
level / confidence / sources
example_sentence_ids[]   # dissected sentences featuring this word
notes_pt                 # usage note (Layer C, optional)
```

### 5.3 `grammar_point`
```
id
key                      # e.g., "te-form", "~たい", "~なければならない"
label_pt                 # short pt-BR name
level / confidence / sources
explanation_pt           # ORIGINAL pt-BR explanation (Layer C) — never copied
formation_pt             # how it's formed (with patterns)
nuance_pt                # when/why to use, register, pitfalls for PT speakers
related_point_ids[]      # contrasts/links (e.g., は vs が)
example_sentence_ids[]   # dissected examples
references[]             # sources consulted (for the owner, not for copying)
needs_review             # true by default for grammar (Layer C)
```

### 5.4 `sentence` (the dissection unit — see Section 6 for the full standard)
```
id
jp                       # 私はパンを食べます。
kana                     # わたしはパンをたべます。
romaji                   # optional
pt                       # natural pt-BR translation (Layer B)
pt_literal               # literal/gloss-level pt-BR
en                       # original EN (if from Tatoeba) — kept as cross-check
level                    # = max(level of component items)
module_id                # where introduced/used
audio_ref                # Tatoeba audio id if available
source                   # tatoeba:<id> | ai_generated
tokens[]                 # see §6
particles[]              # see §6
grammar_point_ids[]      # grammar used here (+ per-link usage note)
vocab_ids[]              # vocab used here
kanji_ids[]              # kanji used here
structure_explanation_pt # prose: how the whole sentence is built (Layer C)
new_items[]              # items NEW vs the lesson's known set (for i+1 tracking)
difficulty               # numeric score (length, rare items, grammar load)
tags[]                   # theme: greetings | shopping | work | ...
flags: ai_generated, needs_review, verified
```

### 5.5 Courseware hierarchy — `course_module`, `topic`, `lesson`
The authored course. It **references** the corpus by ID and never embeds it. Three nested entities:

**`course_module`** (a JLPT level container)
```
id
level                    # pre-n5 | n5 | n4
order                    # int
title_pt
overview_pt              # what this level covers + production goals (Layer C)
topic_ids[]              # ordered
```

**`topic`** (a teachable unit within a module — e.g., Hiragana, Particles は/が)
```
id
module_id
order                    # int (position within the module)
title_pt                 # e.g., "Partículas は e が"
theme_pt                 # functional context, if any
family_ids[]             # the family/families this topic teaches (Section 5.6)
objectives_pt[]
prerequisites[]          # topic ids
lesson_ids[]             # ordered
```

**`lesson`** (the smallest learn-by unit — dense text + exercises + sentence refs)
```
id
topic_id
order                    # int (position within the topic)
title_pt
objectives_pt[]
prerequisites[]          # lesson ids
introduces:              # the items FIRST taught in this lesson
  kanji_ids[]  vocab_ids[]  grammar_ids[]
body_pt                  # DENSE, rich pt-BR teaching text (Layer C) — the core lesson;
                         #   original prose, beginner-and-mid-course friendly, references nothing from the local course
exercises[]:             # structured, app-renderable + auto-gradable
  - id
    type                 # recognition | cloze | particle_choice | sentence_build |
                         #   reading | listening | production | matching
    prompt_pt
    sentence_refs[]      # dissected sentences used, BY ID (never embedded)
    item_refs[]          # kanji/vocab/grammar used, BY ID
    answer               # structured answer key
    explanation_pt       # why the answer is right (Layer C)
sentence_refs[]          # dissected sentences featured in the lesson, BY ID ONLY
cumulative_known_set     # computed: everything known by end of this lesson (for i+1)
needs_review             # true (Layer C content) until teacher sign-off
```
**Hard rule:** lessons and exercises hold sentence **IDs only**. The full dissected sentence lives once in the corpus (`sentence`, §5.4) and is pulled at runtime — never copied into a lesson. This keeps a single source of truth and lets one sentence serve many lessons/exercises from many angles.

### 5.6 `group` (family / cluster — the modular grouping layer)
A generic, typed, ordered cluster that bundles related items so they can be taught together "part by part, then the rule." Cross-level and cross-type. This is what makes the course modular in the way the owner described.
```
id
type                     # semantic_field | kanji_component | phonetic_series |
                         #   word_family (derivational) | conjugation_class |
                         #   particle_set | contrast_pair | function_set
label_pt                 # e.g., "Família: expressões de tempo", "Verbos godan"
description_pt           # what unifies this family + the rule it teaches (Layer C)
importance_rank          # int — order in which families are introduced (freq + foundational value)
governing_rule_pt        # the rule the family teaches, if any (e.g., godan conjugation, を usage)
members[]:               # ordered; members may be kanji, vocab, OR grammar
  - member_id
    member_type          # kanji | vocab | grammar
    intra_order          # int — order WITHIN the family
    is_core              # bool — core member vs variation/derivation
    note_pt              # why this member, how it varies from the core
related_group_ids[]      # e.g., contrast pair links (は-family ↔ が-family)
spans_levels[]           # e.g., [n5, n4, n3] — families are cross-level
primary_module_id        # module where the family is first taught (it may spiral across more)
```
Examples: a **semantic_field** "time expressions"; a **kanji_component** family for the 言 radical (話/語/読/説…); a **word_family** 食べる→食べ物→食事; a **conjugation_class** "godan verbs" whose `governing_rule_pt` is taught once then drilled across all members; a **contrast_pair** は↔が. A given item (e.g., 食べる) can belong to several groups at once (word family *and* ichidan class) — that's expected and is the point of `group_ids[]`.

---

## 6. THE SENTENCE DISSECTION STANDARD (reusable core)

**Every sentence in the entire system — now and in every future feature — follows this exact model.** This is what lets one sentence be reused from many angles: read it in a lesson, drill its particles, blank out a word for cloze, or have the learner assemble it from tokens. Build it once, correctly, and everything downstream is generated from it.

**Per sentence, produce:**

1. **Surface layer:** `jp`, full `kana` reading, optional `romaji`, natural `pt` translation, `pt_literal` literal gloss, original `en` (if Tatoeba), `audio_ref`.

2. **Token breakdown** (skeleton from the morphological analyzer, glosses from the LLM). For **each token**:
   - `surface` (as it appears), `lemma` (dictionary form), `reading` (kana), optional `romaji`
   - `pos` (coarse + fine, e.g., verb / ichidan; particle / case-marking)
   - `role` in this sentence (topic marker, subject, direct object, main verb, etc.)
   - `gloss_pt` — meaning **in this context** (not the generic dictionary gloss)
   - `vocab_id` (link; null for pure particles/inflections)
   - `conjugation_note_pt` (e.g., "forma ます de 食べる (taberu)")

3. **Particles** — for every particle in the sentence: `{ particle, function_pt, explanation_pt }`. Explain *why this particle here* and *how it works*, in pt-BR (e.g., を marks the direct object of 食べる; は marks the topic, contrasting with が which would mark the subject). This is the raw material for particle drills.

4. **Links:** `grammar_point_ids[]` (each with a short note on how it's used here), `vocab_ids[]`, `kanji_ids[]`.

5. **Whole-sentence explanation** (`structure_explanation_pt`, Layer C): a short pt-BR paragraph walking through how the sentence is constructed and why — readable by a beginner *and* informative for someone mid-course.

6. **Metadata:** `level`, `module_id`, `new_items[]` (what's new vs the module's known set — enforces i+1), `difficulty`, `tags[]`, flags.

**Worked example (target shape, illustrative):**
- `jp`: 私はパンを食べます。 / `kana`: わたしはパンをたべます。 / `pt`: "Eu como pão." / `pt_literal`: "Eu (tópico) pão (objeto) como."
- tokens: 私 (lemma 私, わたし, pronoun, "eu") · は (particle, topic marker, function "marca o tópico") · パン (noun, "pão") · を (particle, direct-object marker) · 食べます (lemma 食べる, verb ichidan, "comer", note "forma ます/polida") · 。(punctuation)
- particles: は → topic; を → direct object of the verb
- grammar: polite non-past ます-form; basic 〜は〜を〜verb word order (SOV)
- structure_explanation_pt: brief pt-BR note on topic-comment + SOV + politeness.

Build a **single dissection function** that always emits this shape, so the corpus is uniform and any feature can consume it.

---

## 7. VALIDATION RULES (the anti-error machine)

Run these automatically; a sentence/record is not saved until it passes (or is explicitly quarantined with a flag). Write results to `reports/validation.md`.

1. **Reading integrity:** every kanji reading used in a dissection must exist in KANJIDIC2 for that kanji; every token `lemma` must exist in JMdict. If the LLM emits a reading/lemma not backed by the dictionaries → reject and re-derive from the analyzer. (Catches hallucinated readings — the classic failure.)
2. **Tokenization agreement:** the token skeleton comes from the analyzer, not the LLM. The LLM may add glosses but may not alter `surface`/`lemma`/`reading`/`pos`.
3. **Coverage:** every target kanji, vocab item, and grammar point in a module has ≥ the minimum number of dissected example sentences (set thresholds in `STATE.md`, e.g., vocab ≥3, grammar ≥5). Report gaps.
4. **i+1 discipline:** flag sentences that introduce more than one item beyond the module's cumulative known set; prefer lower-`new_items` sentences.
5. **Provenance completeness:** every record has a non-empty `source`; every `ai_generated`/Layer C item has `needs_review: true`. No orphan records.
6. **Level consistency:** a sentence's `level` ≥ the max level of its components; a module never *introduces* an item whose prerequisites aren't already in the cumulative known set.
7. **Translation sanity (spot/round-trip):** for a sample, back-translate JP→PT independently and compare to stored `pt`; large divergences → `needs_review`.
8. **Duplicate/near-duplicate control:** dedupe sentences; avoid over-representing one pattern.
9. **Naturalness preference:** generated (non-Tatoeba) sentences are capped as a % of each topic and always reviewable.

The teacher reviewer's queue = everything with `needs_review: true`, **AI-generated content first**. Everything else is auditable directly against its dataset source.

---

## 8. RESUMPTION PROTOCOL (multi-session, hours-long runs)

Long runs will span sessions and may hit usage limits. The work must always be resumable with zero context loss.

- **Resumable from the first moment.** Because Phase P-pre creates git + `CLAUDE.md` + `STATE.md` before anything else, even the long research in Phases L and R is tracked and resumable — not just the build phases. Within L and R, save partial outputs to disk and update `STATE.md` as you go, so a crash mid-research loses at most the current sub-step.

- **`STATE.md` is the source of truth for progress.** It contains: the full phase / topic / lesson TODO; each unit's status (`pending` / `in_progress` / `done` / `needs_review`); a dataset manifest (versions + checksums); and a top **`RESUME HERE`** marker pointing to the exact next action.
- **Idempotent scripts:** every ingestion/build script checks what's already done and skips it. Re-running is always safe.
- **Atomic units:** never leave a topic/lesson half-built across a session boundary. Finish → validate → export → **git commit** → update `STATE.md` → then advance. If interrupted mid-unit, mark it `in_progress` with a note on exactly where it stopped.
- **Commit discipline:** descriptive commits after every topic and every phase (e.g., `P5: dissected sentence bank for n5/topic-03-particles (247 sentences, all validated)`).
- **On hitting a limit:** stop cleanly at the last completed unit, write `RESUME HERE`, commit. The owner restarts and says "continue from STATE.md."

---

## 9. OUTPUT & DELIVERABLES

- `db/corpus.sqlite` — canonical store, all layers, fully linked.
- `corpus/` — CORPUS LAYER: by-ID, sharded files for kanji, vocab, grammar, the dissected-sentence bank, and families, each with an index (JSON = app/LLM-ready; MD = readable).
- `course/<level>/topic-NN-<slug>/lesson-MM.{json,md}` — COURSEWARE LAYER: the Module→Topic→Lesson course (JSON = app/LLM-ready; MD = human quality review).
- `research/` — everything gathered/derived, persisted and versioned (datasets, derived lists, references, coverage probes, and the de-identified `local-course-insights/`).
- `design/` — `PLAN_REVIEW.md`, `schema_v2.md`, `quality_rubric.md`, `curriculum.md`, `course_outline.md`, `sources.md`.
- `reports/validation.md` + `reports/stats.md` — QA results and counts (per lesson/topic/level).
- `INDEX.md` — project manifest for LLM navigation.
- `ATTRIBUTION.md` — required attributions (EDRDG/JMdict-KANJIDIC2, KanjiVG, Tatoeba, etc.).
- `README.md` — how the project is organized and how to consume each layer.

---

## 10. ACCEPTANCE CRITERIA (definition of done)

The run is complete only when **all** hold and `reports/validation.md` shows them green:

1. **Kanji:** 100% of the reconciled N5 + N4 kanji set present, each with on/kun readings **tagged by tier of introduction**, pt-BR meanings, stroke count, KanjiVG stroke-order reference, radical decomposition, ≥ N example words, and ≥ M dissected example sentences.
2. **Vocabulary:** 100% of the reconciled N5 + N4 vocab set present, each with reading, pt-BR sense(s), POS, common-ness, level + confidence, and ≥ 3 dissected sentences.
3. **Grammar:** every N5 and N4 grammar point enumerated, each with an **original** pt-BR explanation, formation, nuance/pitfalls for PT speakers, and ≥ 5 dissected examples.
4. **Sentence bank:** rich per-topic coverage at the R3 targets (minimum ≥3 dissected sentences/vocab, ≥5/grammar), **every token glossed in pt-BR, every particle explained**, all passing validation; generated sentences within the per-topic cap and flagged.
5. **Provenance:** every record traceable; all Layer B/C content validated or flagged; **zero unresolved reading/lemma mismatches**.
6. **Course outline:** a complete Module→Topic→Lesson outline from absolute zero → 100% N5 → 100% N4, each level/topic/lesson with objectives and production goals; comfortable for both a true beginner and someone joining mid-way.
7. **Licensing:** `ATTRIBUTION.md` complete; commercial-use compatibility of each source recorded for the owner's decision.
8. **Reviewability:** `needs_review` queue assembled, AI-generated first, ready to hand to a Japanese teacher for sign-off.
9. **Families:** every N5/N4 kanji, vocab, and grammar item belongs to ≥1 family/group; families are importance-ranked, intra-family order set (core → variations), governing rules attached where they apply, and mapped onto the module sequence.
10. **Cross-reference graph:** the sample cross-cutting queries in §1.7 all return correct results from stored links; the schema is level-agnostic (§1.6) so N3–N1 can be added later as data only, with no structural change.
11. **Quality rubric met:** the corpus passes `design/quality_rubric.md` (built in Phase R) on accuracy, explanation depth, example richness, sequencing soundness, completeness, and review-readiness — and the pilot topic cleared the rubric before mass production began.
12. **Courseware:** every topic has authored lessons with dense pt-BR teaching text, structured (app-gradable) exercises, and sentence references **by ID** (never embedded); every reconciled N5/N4 item has an introducing lesson.
13. **Clean-room local course:** the project contains **zero** verbatim or lightly-reworded text, examples, or explanations from the local course, and **zero** instructor/course names anywhere — only the de-identified abstraction exists; a recorded coverage comparison shows ours is a superset and more complete, direct, and efficient.
14. **Persistence & LLM-navigability:** every dataset/derived artifact used is saved under `research/` with provenance; the project is modular (many small, consistently-schema'd files) with an accurate `INDEX.md`, so an LLM can navigate, analyze, improve, and later implement it.

---

## APPENDIX A — Seed research queries (Phase P3)
Run these (and follow-ups) with web search; synthesize originally into `design/curriculum.md` with citations. Do not copy text from sources.
- "comprehensible input i+1 second language acquisition evidence"
- "testing effect retrieval practice vocabulary retention study"
- "spacing effect optimal review language learning research"
- "frequency-based vocabulary acquisition most common words coverage Japanese"
- "output hypothesis speaking production second language acquisition"
- "interleaving vs blocking practice language learning"
- "keyword mnemonic method vocabulary acquisition effectiveness"
- "kanji learning component radical method vs rote research"
- "Japanese pitch accent comprehensibility importance for learners"
- "teaching Japanese to Portuguese speakers common difficulties false friends"
- "order of introducing Japanese particles grammar beginners"

## APPENDIX B — Portuguese (pt-BR) style guide for learner-facing content
- All translations, glosses, explanations, objectives, and notes in **Brazilian Portuguese**.
- Clear and friendly, but precise; explain grammar terms the first time (partícula, tópico, transitivo, etc.).
- Keep Japanese terms in Japanese (with kana reading + pt-BR gloss); use romaji only as a support, never as a crutch.
- A beginner who knows nothing and a learner mid-course should both feel addressed: lead with the plain explanation, then add the deeper note.
- Be consistent in terminology across the whole corpus (maintain a small pt-BR glossary of grammar terms in `design/curriculum.md`).

---

## APPENDIX C — Notes on Claude Code execution
- Put the non-negotiables (Section 1) into `CLAUDE.md` so they persist across sessions.
- Use a written plan/TODO and keep `STATE.md` updated continuously.
- Parallelizable work (e.g., dissecting batches of sentences, translating gloss sets) can be delegated to sub-tasks; the morphological skeleton + validation must still gate every result.
- Verify the live status of each dataset URL/license at build time rather than trusting this document — sources move.
- Never ingest the owner's local course text as a generation source (§1.4); it's ordering-reference only, in Phase P4.
