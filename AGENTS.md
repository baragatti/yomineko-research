# AGENTS.md — Yomineko Corpus Build (project memory)

**This project builds curated, verifiable, LLM-ready corpus + courseware for Brazilian-Portuguese
Japanese course covering zero → full N5 → full N4.** This run produces **data and reference material
only** — no app, no backend, no SRS logic.

## Master reference
 authoritative spec is [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). **Read it in
full before acting.** This file restates non-negotiables; spec governs when they conflict.
Progress lives in [`STATE.md`](STATE.md) — start every session by reading its `RESUME HERE` marker.

## Language rule (hard)
- **All orchestration, code, commits, internal notes, design docs → English.**
- **ALL learner-facing content → Brazilian Portuguese (pt-BR).** Never pt-PT. (Spec Appendix B.)
- **Internals are language-AGNOSTIC.** Schema identifiers, file/dir names, keys, and **enum/type values** are
  English + locale-neutral (e.g. `<note type="l1-pitfall">`never `armadilha-pt`). Only *content* (text,
  names, descriptions, translations, html text) is localized. **pt-BR is locale module** — only one for
  now, expandable later with no structural change. See [`design/i18n.md`](design/i18n.md). Exports use
  **locale-objects** `{"pt-BR":…,"en":…}` (en = Layer-A source); mechanical enums (pos / inflection / particle
  `function_type` / vocab `register`) are neutral English. **Authoring tone is contract:**
  [`design/translation_style.md`](design/translation_style.md) — natural pt-BR (never literal "Quanto mim"
  mirror; that goes in `translation_literal`), register-aware, drop 。 in GENERATED jp, run `humanizer`
  skill on AI prose.

## §1 NON-NEGOTIABLES (restated from the spec)

### 1.1 Provenance layers — every record carries a `source` and belongs to exactly one layer
- **Layer — Authoritative (zero AI):** characters, readings, stroke order, base meanings, POS, radical
  decomposition, raw real-world example sentences. Comes ONLY from Section 3 open datasets. Ground truth.
- **Layer B — Derived-and-verified (AI, checked against A):** pt-BR translations, per-token glosses,
  sentence dissections. Generated, then **machine-validated** against Layer (spec §7).
- **Layer C — Pedagogical (AI, research-grounded):** sequencing, explanations, mnemonics, objectives.
  Free-form but grounded in methodology research; **always `needs_review: true`** for human teacher sign-off.

### 1.2 Prefer SELECTION over GENERATION
When real human-written sentence exists (Tatoeba), **use it**. AI sentence generation is last resort to
fill coverage gaps; every generated sentence is `ai_generated: true`  `needs_review: true`.

### 1.3 Separate fact from explanation
Dictionary meaning (fact, A→B) and didactic explanation (pedagogy, C) **never share field**. reviewer
must be able to trust A/B blindly and audit C selectively.

### 1.4 LOCAL COURSE MATERIAL — read-only, clean-room, isolated (ZERO TOLERANCE)
Source: `C:\Users\WiseWolf\IdeaProjects\japorongo-back\files` (entry `biblioteca.json` + nested JSONs).
Used ONLY in **Phase L**, isolated, as structural reference.
- **Never copy** any text, example, explanation, exercise, or phrasing — not verbatim, not lightly reworded.
  Only abstract, non-protectable **ideas / structure / coverage**, re-expressed in our own words at level
  of method (e.g. "introduces counters right after numbers"), never content.
- **Never record** course name or any instructor/author name anywhere in this project. Strip all PII.
- If unsure whether something is "idea" vs "expression," treat it as **expression** and do not reproduce it.
- Phase L output (`research/local-course-insights/`) is **de-identified abstraction only**.
-  raw material **never re-enters context** as generation source after Phase L. Its only later use is
  P7 **coverage comparison** (concept-level, naming nothing) to confirm ours is superset.

### 1.5 "JLPT levels" are NOT official
There is no official JLPT vocab/kanji/grammar list. Level assignment is **consensus-based**: cross-reference
**≥3 independent community lists** and record agreement. **Do NOT trust KANJIDIC2's built-in `jlpt` field**
(old pre-2010 4-level scale). Every level tag carries `level_confidence` + `level_sources`.

### 1.6 Level-agnostic, future-proof schema
 same schema must work N5→N1. `level` is **data, not structure** — adding N3/N2/N1 later is inserting rows,
never schema change. Populate only N5/N4 now; hardcode no closed set of levels.

### 1.7 Everything is one cross-referenceable graph
kanji ↔ vocab ↔ sentence ↔ grammar ↔ family ↔ module, all bidirectional, addressed by **stable ID**.
sample cross-cutting queries in spec §1.7 are design tests finished corpus must answer from stored links.

### 1.8 This plan is a hypothesis — improve it, push back honestly
Phase R stress-tests and rewrites spec. If source is thin, schema weak, threshold unrealistic,
sequencing choice shaky — **say so and fix it**. fully-autonomous run is NOT final product: human
teacher-review loop is mandatory and corpus must arrive **review-ready**, not review-skipped.

## Two-layer architecture (keep separate)
- **Corpus layer** (`corpus/`by stable ID): reusable registries (kanji, vocab, grammar) + dissected
  sentence bank + families. sentence lives **once**, fully dissected.
- **Courseware layer** (`course/`): linear Module → Topic → Lesson course. It **references corpus by ID
  and never embeds it.** Lessons/exercises hold sentence **IDs only**.

## Persistence
Everything fetched or derived → saved under `research/`versioned, never thrown away. Record every dataset's
source URL, version, date, SHA256 in `design/sources.md`. Licenses → `ATTRIBUTION.md` (commercial-use noted).

## Data format — CANONICAL is LLM-readable (owner directive, 2026-06-13)
 durable, committed, source-of-truth artifacts are **JSON + Markdown** under `corpus/` (corpus layer)
`course/` (courseware layer), because we will heavily use AI to review/improve/validate/implement content
and will pick "real" DB later. **`db/corpus.sqlite` is regenerable working/query index, NOT source of
truth** — it is git-ignored and rebuildable from scripts + datasets. **Rule:** after any phase that changes
corpus/courseware data, **re-run exporter and commit JSON/MD** so data always lives durably in
LLM-readable form (never only in SQLite binary). Keep files modular and consistently schema'd (`INDEX.md`).

## Resumption protocol
- `STATE.md` is source of truth for progress (phase/topic/lesson statuses + dataset manifest + `RESUME HERE`).
- Scripts are **idempotent**: re-running skips done work.
- **Atomic units:** finish → validate → export → `git commit` → update `STATE.md` → advance. Never leave
  topic/lesson half-built across session boundary.
- On any blocker/usage limit: stop at last completed unit, write `RESUME HERE`commit. Resume via
  "continue from STATE.md."

## Reasoning effort
Phases L / R and all design / critique / authoring → **maximum reasoning**. Mechanical ingestion (P1/P2) may
use lighter setting.

## Git scope note
This project has its **own** `.git` (initialized in Phase P-pre). stray repo exists at `C:\Users\WiseWolf`
git uses nearest `.git`so all commands run from this folder target THIS repo only. Never push without
being asked. Never create branches/worktrees/stashes unsolicited.

