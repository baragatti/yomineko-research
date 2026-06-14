# CLAUDE.md — Yomineko Corpus Build (project memory)

**This project builds a curated, verifiable, LLM-ready corpus + courseware for a Brazilian-Portuguese
Japanese course covering zero → full N5 → full N4.** This run produces **data and reference material
only** — no app, no backend, no SRS logic.

## Master reference
The authoritative spec is [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). **Read it in
full before acting.** This file restates the non-negotiables; the spec governs when they conflict.
Progress lives in [`STATE.md`](STATE.md) — start every session by reading its `RESUME HERE` marker.

## Language rule (hard)
- **All orchestration, code, commits, internal notes, design docs → English.**
- **ALL learner-facing content → Brazilian Portuguese (pt-BR).** Never pt-PT. (Spec Appendix B.)

## §1 NON-NEGOTIABLES (restated from the spec)

### 1.1 Provenance layers — every record carries a `source` and belongs to exactly one layer
- **Layer A — Authoritative (zero AI):** characters, readings, stroke order, base meanings, POS, radical
  decomposition, raw real-world example sentences. Comes ONLY from the Section 3 open datasets. Ground truth.
- **Layer B — Derived-and-verified (AI, checked against A):** pt-BR translations, per-token glosses,
  sentence dissections. Generated, then **machine-validated** against Layer A (spec §7).
- **Layer C — Pedagogical (AI, research-grounded):** sequencing, explanations, mnemonics, objectives.
  Free-form but grounded in methodology research; **always `needs_review: true`** for human teacher sign-off.

### 1.2 Prefer SELECTION over GENERATION
When a real human-written sentence exists (Tatoeba), **use it**. AI sentence generation is a last resort to
fill coverage gaps; every generated sentence is `ai_generated: true` AND `needs_review: true`.

### 1.3 Separate fact from explanation
Dictionary meaning (fact, A→B) and didactic explanation (pedagogy, C) **never share a field**. A reviewer
must be able to trust A/B blindly and audit C selectively.

### 1.4 LOCAL COURSE MATERIAL — read-only, clean-room, isolated (ZERO TOLERANCE)
Source: `C:\Users\WiseWolf\IdeaProjects\japorongo-back\files` (entry `biblioteca.json` + nested JSONs).
Used ONLY in **Phase L**, isolated, as a structural reference.
- **Never copy** any text, example, explanation, exercise, or phrasing — not verbatim, not lightly reworded.
  Only abstract, non-protectable **ideas / structure / coverage**, re-expressed in our own words at the level
  of method (e.g. "introduces counters right after numbers"), never content.
- **Never record** the course name or any instructor/author name anywhere in this project. Strip all PII.
- If unsure whether something is "idea" vs "expression," treat it as **expression** and do not reproduce it.
- Phase L output (`research/local-course-insights/`) is a **de-identified abstraction only**.
- The raw material **never re-enters context** as a generation source after Phase L. Its only later use is a
  P7 **coverage comparison** (concept-level, naming nothing) to confirm ours is a superset.

### 1.5 "JLPT levels" are NOT official
There is no official JLPT vocab/kanji/grammar list. Level assignment is **consensus-based**: cross-reference
**≥3 independent community lists** and record agreement. **Do NOT trust KANJIDIC2's built-in `jlpt` field**
(old pre-2010 4-level scale). Every level tag carries `level_confidence` + `level_sources`.

### 1.6 Level-agnostic, future-proof schema
The same schema must work N5→N1. `level` is **data, not structure** — adding N3/N2/N1 later is inserting rows,
never a schema change. Populate only N5/N4 now; hardcode no closed set of levels.

### 1.7 Everything is one cross-referenceable graph
kanji ↔ vocab ↔ sentence ↔ grammar ↔ family ↔ module, all bidirectional, addressed by **stable ID**. The
sample cross-cutting queries in spec §1.7 are design tests the finished corpus must answer from stored links.

### 1.8 This plan is a hypothesis — improve it, push back honestly
Phase R stress-tests and rewrites the spec. If a source is thin, a schema weak, a threshold unrealistic, or a
sequencing choice shaky — **say so and fix it**. A fully-autonomous run is NOT the final product: the human
teacher-review loop is mandatory and the corpus must arrive **review-ready**, not review-skipped.

## Two-layer architecture (keep separate)
- **Corpus layer** (`corpus/`, by stable ID): reusable registries (kanji, vocab, grammar) + the dissected
  sentence bank + families. A sentence lives **once**, fully dissected.
- **Courseware layer** (`course/`): the linear Module → Topic → Lesson course. It **references corpus by ID
  and never embeds it.** Lessons/exercises hold sentence **IDs only**.

## Persistence
Everything fetched or derived → saved under `research/`, versioned, never thrown away. Record every dataset's
source URL, version, date, SHA256 in `design/sources.md`. Licenses → `ATTRIBUTION.md` (commercial-use noted).

## Data format — CANONICAL is LLM-readable (owner directive, 2026-06-13)
The durable, committed, source-of-truth artifacts are **JSON + Markdown** under `corpus/` (corpus layer) and
`course/` (courseware layer), because we will heavily use AI to review/improve/validate/implement the content
and will pick a "real" DB later. **`db/corpus.sqlite` is a regenerable working/query index, NOT the source of
truth** — it is git-ignored and rebuildable from the scripts + datasets. **Rule:** after any phase that changes
corpus/courseware data, **re-run the exporter and commit the JSON/MD** so the data always lives durably in
LLM-readable form (never only in the SQLite binary). Keep files modular and consistently schema'd (`INDEX.md`).

## Resumption protocol
- `STATE.md` is the source of truth for progress (phase/topic/lesson statuses + dataset manifest + `RESUME HERE`).
- Scripts are **idempotent**: re-running skips done work.
- **Atomic units:** finish → validate → export → `git commit` → update `STATE.md` → advance. Never leave a
  topic/lesson half-built across a session boundary.
- On any blocker/usage limit: stop at the last completed unit, write `RESUME HERE`, commit. Resume via
  "continue from STATE.md."

## Reasoning effort
Phases L / R and all design / critique / authoring → **maximum reasoning**. Mechanical ingestion (P1/P2) may
use a lighter setting.

## Git scope note
This project has its **own** `.git` (initialized in Phase P-pre). A stray repo exists at `C:\Users\WiseWolf`;
git uses the nearest `.git`, so all commands run from this folder target THIS repo only. Never push without
being asked. Never create branches/worktrees/stashes unsolicited.
