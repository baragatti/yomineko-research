# Readiness — quality, provenance and the teacher-review loop

_Area: `quality_provenance_review`. Written 2026-09-02 against the committed export at `48d5459a`.
Every count below was produced by running a script over `corpus/` + `course/` (and, where stated, over
`db/corpus.sqlite` as a cross-check). No number here is quoted from a document._

**Headline.** The provenance gate is green and the provenance *data* does not meet the spec. 11 of 23
entities — 11,695 records, including all 7,401 vocab and all 2,131 kanji — carry no `layer`, no
`source`, no `needs_review` and no `ai_generated` at all, and `validate_provenance_json.py` passes them
because it infers each entity's expected field set from that entity's own data. Separately: **there is
no approval mechanism anywhere.** No record, no schema, no validator and no script has a
`reviewed_by`/`approved_at`/`review_status` field. `needs_review: true` is written once at build time
and nothing in the repository can ever set it to false. The teacher loop is a queue with no exit.

---

## 1. What this capability needs from the data

For "AI-authors now, teachers validate later, we aim as close to 100% as we can" to be operable, the
data has to answer six questions per record, and a validator has to defend each answer:

| # | Question | Concretely |
|---|---|---|
| Q1 | **What is this?** | `layer` ∈ A/B/C on **every** record (spec §1.1), so a reviewer can trust A blindly, spot-check B, and audit C fully (§1.3). |
| Q2 | **Where did it come from?** | non-empty `source` on every record; for generated Japanese, `ai_generated: true` (§1.2). |
| Q3 | **Does it still need a human?** | `needs_review`, meaning what `design/translation_qa.md` §0.1 says it means — "content we believe is already correct, awaiting a human's confirming signature". |
| Q4 | **How risky is it?** | per-record evidence a queue can rank by: real-vs-generated Japanese, what the translation was validated against, level-tag confidence and agreement. |
| Q5 | **Has a human signed it off?** | an approval record: who, when, what exact text they approved, and a verdict. This is the field that does not exist. |
| Q6 | **Did the approval survive the next edit?** | a content hash, so an approval cannot silently carry over onto rewritten text. |

Plus two contract-level requirements: an approval must be **addressable by stable id** (per
`contracts/README.md`, the slug, never the integer `id`), and adding it must not force a change to 23
entity schemas.

---

## 2. What exists today (verified)

### 2.1 The provenance gate passes 52,184 records

`python scripts/validate/validate_provenance_json.py` → `ALL OK`, 52,184 records across 23 entities,
zero failures in every column (`ai&!rev`, `C&!rev`, `non-bool`, `missing`, `derived`).

What it actually enforces is *meaning*, not *presence* — its rules are: `ai_generated ⇒ needs_review`;
`layer C ⇒ needs_review`; both are real JSON booleans; `layer ∈ {A,B,C}`; the exam derivation table
imported live from `scripts/contracts/migrate_exam_banks_p7.py`; and "no record is missing a field its
own entity otherwise carries". That last rule is inferred per entity, pinned only for `exam_item` via
`REQUIRED_PROVENANCE`. `contracts/README.md` states the position plainly: *"The contract enforces the
meaning, not the presence… backfilling the gaps is a data task, and only then can the fields become
`required`."*

### 2.2 Provenance field presence, measured per entity

| entity | records | layer | source | needs_review | ai_generated |
|---|---:|:---:|:---:|:---:|:---:|
| `exam_item` | 6,048 | ✔ | ✔ | ✔ | ✔ |
| `exercise_conjugation` | 18,524 | ✔ | ✔ | ✔ | — |
| `exercise_role` | 5,358 | ✔ | ✔ | ✔ | — |
| `reading` | 286 | ✔ | — | ✔ | ✔ |
| `speak_unit` / `speak_path` | 72 / 1 | ✔ | — | ✔ | — |
| `sentence` | 5,889 | — | — | ✔ (nested) | ✔ (nested) |
| `grammar` | 496 | — | — | ✔ | — |
| `lesson` | 322 | — | — | ✔ | — |
| `stroke_order` / `stroke_lines` / `stroke_kana` | 1,233 / 2,098 / 162 | — | ✔ | — | — |
| `vocab` | 7,401 | — | — | — | — |
| `kanji` | 2,131 | — | — | — | — |
| `conjugation` | 1,157 | — | — | — | — |
| `family` | 396 | — | — | — | — |
| `capability_lesson_map` | 266 | — | — | — | — |
| `kana` | 211 | — | — | — | — |
| `capability` | 74 | — | — | — | — |
| `topic` | 52 | — | — | — | — |
| `course` / `course_manifest` / `kana_family` | 4 / 1 / 2 | — | — | — | — |

Totals over the 52,184 records in `contracts/manifest.json`:

- carries `layer`: **30,289 (58.0%)** — 21,895 records do not
- carries `source`: **33,423 (64.0%)** — 18,761 records do not
- carries `needs_review`: **36,996 (70.9%)** — 15,188 records do not
- **carries none of the four: 11,695 records (22.4%)** across 11 entities

Both `YOMINEKO_CORPUS_BUILD_SPEC.md` §1.1 ("every record carries a `source` and belongs to exactly one
layer") and `design/quality_rubric.md` **hard gate G3** ("Every record has a non-empty `source` and
correct layer") are unmet. Where the spec, the rubric and the data disagree, **the data is wrong and the
spec is right** — `contracts/common.schema.json` (line 72) was amended to *describe* the non-adoption
rather than the data being brought up to the contract. That description is honest, and it is also the
reason no gate fires.

This is not a cosmetic gap. A `vocab` record holds AI-authored pt-BR glosses
(`senses[].gloss["pt-BR"]`), a `kanji` record holds AI-authored pt-BR `meanings` plus per-reading
`note`s, and a `family` record holds an authored pt-BR `governing_rule` — Layer B and Layer C content
respectively, and none of it is labelled as either.

### 2.3 The review flags that are published carry almost no information

`needs_review: true` on **8,314 records (15.9%)**:

| entity | true | of | note |
|---|---:|---:|---|
| `sentence` | 5,889 | 5,889 | constant |
| `exam_item` | 1,248 | 6,048 | **the only entity where the flag discriminates** |
| `grammar` | 496 | 496 | constant |
| `lesson` | 322 | 322 | constant |
| `reading` | 286 | 286 | constant |
| `speak_unit` + `speak_path` | 73 | 73 | constant |
| `exercise_conjugation` + `exercise_role` | 0 | 23,882 | constant `false` |

On six of the seven entities that publish it the field is a constant. Sorting a queue by `needs_review`
therefore partitions by entity type, not by risk. The two exercise banks being born `false` is
defensible — `validate_conjugation_exercises.py` re-derives all 18,524 readings and
`validate_role_exercises.py` re-derives all 5,358 drills from the sentences' own pattern data — but it
means 23,882 records assert "no human needed" with no reviewer ever having said so.

`ai_generated: true` on **2,851 records**: 2,213 sentences (37.6% of the bank) and 638 exam items.

### 2.4 The review flags the working index holds and the export throws away

`db/corpus.sqlite` carries `needs_review` on tables the exporter never emits it for:

| table | rows | `needs_review = 1` | reaches the export? |
|---|---:|---:|:---:|
| `vocab_sense` | 10,592 | 10,592 | **no** |
| `kanji_reading` | 33,785 | 3,970 | **no** |
| `family` | 396 | 396 | **no** |
| `grammar_point` | 496 | 496 | yes (`export_corpus.py:361`) |
| `sentence` | 5,889 | 5,889 | yes (`export_corpus.py:519`) |
| `lesson` | 322 | 322 | yes (course exporter) |

**14,958 review flags exist in the index and are dropped at export.** The source of truth is
*less* review-aware than the regenerable artifact.

### 2.5 Evidence fields that DO discriminate (and no queue reads)

Inside `sentence.provenance`, four keys the provenance validator does not even look at
(its `FIELDS` tuple is only `layer`/`source`/`needs_review`/`ai_generated`):

| key | distribution (n=5,889) |
|---|---|
| `jp_source` | `tatoeba` 3,549 · `ai-generated` 2,207 · `jec` 127 · `generated` 6 |
| `pt_source` | **`ai` on all 5,889** — no pt-BR translation in the bank has a human author |
| `pt_validated_against` | `en` 3,205 · **`dict` 2,684** |
| `translation_confidence` | 0.85 (5,556) · 0.8 (330) · 0.6 (3) |
| `tier` | `full` on all 5,889 — constant |

`pt_validated_against: "dict"` on 2,684 records is a real, already-stored risk ranking (those
translations were checked against a dictionary, not against a trusted English anchor; STATE (ag)
confirms re-validation against the restored anchors is "queued, not claimed"). Nothing consumes it.
`translation_confidence` takes three values and `tier` takes one — the §9.4 composite trust score was
designed and never computed.

### 2.6 Tooling for a teacher: one stale counts-only markdown table

`scripts/export/review_queue.py` is the only artifact in the repo that addresses a teacher. It is
~50 lines of SQL against `db/corpus.sqlite` that writes `reports/review_queue.md`. Problems, all
verified:

- **It reads the regenerable index, not the source of truth** — precisely the class of defect
  `scripts/validate/README.md` says cost five hard gates in the 2026-08-26/27 review.
- **It is 2.5 months stale.** `reports/review_queue.md` is dated 2026-06-15 and claims 11,034 items.
  Re-running its own eight queries against today's DB gives **23,796**. It prints
  "Lessons … **0**" where the DB now has 322, and "Grammar … 364" where it has 496.
- **It lists counts, not items.** There are no ids, so it cannot be worked through.
- It is in no validator suite, so nothing notices it rotting.

`research/reports/lesson_sentence_review.json` is better: `validate_lesson_gating.py` regenerates it
(247 worst-first items with lesson, sentence, level, budget, load, new kanji and new vocab) and freezes
its counts in `research/reports/lesson_sentence_baseline.json` so the backlog can only shrink. It is
the one working example of "queue a teacher can act on, ratcheted by a gate" — and it covers one
invariant.

`course/vocab_disambiguation_review.json` is the second: 14 homograph placements with `chosen`, `how`,
`evidence`, `candidates` and a per-row `needs_review: true`, awaiting a teacher.

### 2.7 There is no approval mechanism at all

```
grep -rlE '"(reviewed_by|reviewed_at|review_status|approved_by|approved_at|verified_by|
             teacher_review|review_state|sign_off|signoff)"' corpus/ course/ contracts/
→ (no matches)
```

Zero hits across the export and all 23 schemas. Consequences:

- No record can be marked approved. There is no `false` transition for `needs_review` anywhere —
  the two exercise banks are *born* false.
- No reviewer identity, timestamp, verdict or scope is representable.
- Nothing distinguishes "a teacher read this and signed it" from "the builder wrote true".
- **No consumer surfaces it.** The prototype reads `ai_generated` only, and only for exam items
  (`prototype/app/lib/exam.server.ts:268-275`, to prefer real Japanese in the picker). It never reads
  `needs_review` or `layer`. `validate_no_client_leak.py` guarantees the corpus stays server-side; it
  does not guarantee unreviewed material is labelled.

### 2.8 What the QA sweeps produced, and what remains open

29 files under `research/reports/qa_sweep/`: 20 auditor reports plus `grammar_repairs_skipped.md`,
`translation_repairs_skipped.md` and `vocab_identity_queue.md` (written 2026-09-01/02). **At least 427
numbered findings** carry `##`/`###` headings; eight reports present findings in tables instead and are
not in that count.

Four repair tables are tracked under `research/derived/repairs/` with `old`/`new`/`why` per row — a
genuine, auditable trail. I verified each row against the export by substring:

| table | rows | applied in the export | not applied |
|---|---:|---:|---|
| `translation_defect_repairs.json` | 231 | **231** | — |
| `jargon_pass2_repairs.json` | 221 | **221** | — |
| `sentence_text_repairs.json` | 496 | **489** | 7 `translation_literal` rows superseded by the later translation campaign (the skipped report predicts exactly this) |
| `grammar_record_repairs.json` | 255 (170 text, 8 forms, 77 unlink) | **146** text rows | 8 ambiguous (old *and* new both present in the record); **16 `form_meanings` rows silently no-oped** — the export has no `form_meanings` field, the data lives at `forms[].meaning` |

**Nothing gates that a repair table applied.** The 16 no-ops were found by this audit, not by the suite.

Open and named:

- **`vocab_identity_queue.md` — 22 vocab records point at the wrong JMdict entry.** `vocab:<jmdict_id>`
  is the published address, so this is a migration (5,955 slug occurrences across 543 export files).
  Eleven of the 22 carry `level_confidence: 1.0` / `level_agreement: "4/4"` because the confidence is
  measuring agreement about the *reading* — the evidence field is most confident exactly where the
  record is wrong. Owner decision A9 (decided: re-point in place; not executed).
- **`grammar_repairs_skipped.md`** — records where every carrier illustrates the excluded sense, so
  unlinking would empty the record; re-tagging is outside the action set.
- **`translation_repairs_skipped.md`** — 7 defects in `particles[].explanation` unreachable by the
  repair schema; 3 literal siblings now disagreeing with the repaired natural field; 1 reading-override
  row that needs 2-vote verification before it can be added to
  `research/derived/fable5_validation/verified_reading_overrides.json` (410 sentences / 508 tokens, the
  sanctioned escape hatch that `validate.py` §7.2 honours).
- **All of `research/reports/PENDING.md` §A1–A10** — decided by the owner 2026-09-01, none executed.

**Collateral no gate watches.** The grammar campaign's 77 `unlink` actions can delete a link but not
move one; the skipped report says 62 sentences ended with zero grammar tags. Measured today:
**3,466 of 5,889 sentences (58.9%) have no grammar link at all** (identical in export and DB), so the
grammar-example pool is 2,423 sentences. `validate.py` does not check grammar coverage.

### 2.9 The style / humanizer contract

`design/translation_style.md` (42 lines) is the authoring contract: natural pt-BR in `translation`, the
literal mirror only in `translation_literal`, register mirrors the Japanese, no 。 on generated JP, no
em dash, run the `humanizer` skill on authored prose. `design/quality_rubric.md` adds six 0–4 dimensions
and hard gates G1–G6. `design/authoring_failure_modes.md` names seven concrete AI failure modes (F1–F7)
and is carried in authoring prompts — `scripts/apply_kanji_note_review.py` records the measured effect
of adding it: problems 221→148, agreed 40→27.

What is machine-enforced:

- **Hard** — `audit_hygiene_all_locales.py` over all 244,389 learner-facing pt-BR strings in 531 files:
  em dash, emoji, mojibake, mixed script, QA-instruction leaks, accent-stripping (against a lexicon
  derived from the corpus's own ã/õ words), pt-PT, duplicated clauses, unbalanced parens.
- **Advisory** — `detect_ai_tells.py`. Run today it flags **1 field corpus-wide** (`vale-ressaltar`, in
  one `sentence.structure_explanation`). Its own header documents dropping patterns that
  false-positived; 1-in-244,389 is a recall problem, not a clean bill of health.
- **Not enforced at all** — everything else in the style contract. "Reads like something a Brazilian
  would actually say" is checked by five high-precision regexes on `translation` only. The `humanizer`
  skill is a prompt-time instruction; nothing verifies it ran.

### 2.10 The generated-Japanese gate is designed, built, and not wired in

`design/translation_qa.md` §9 specifies a deterministic battery for generated Japanese (§9.1), a
composite trust score with quarantine (§9.4) and a golden regression set (§9.5).
`scripts/validate/validate_generated_jp.py`, `golden_set.json` and `run_golden.py` all exist.

**Neither `validate_generated_jp.py` nor `run_golden.py` is in `validate_all.py`.** The SUITE has 42
entries: 40 gating and 2 advisory (`completeness_audit.py`, `detect_ai_tells.py`) — note `STATE.md` and
`PENDING.md` both say "39 hard validators", one behind. `run_golden.py` does not currently execute in
this environment (`sudachidict_core` is not installed). `golden_set.json` holds 14 sentences (7 good,
5 bad, 2 unnatural). So the 2,213 AI-generated sentences are defended on every commit by the generic
sentence gates, and by neither the battery written for them nor the regression set written to keep that
battery honest.

### 2.11 The edit path runs through an untracked binary

Every content applier writes `db/corpus.sqlite` and nothing else, by explicit design —
`scripts/apply_translation_defect_repairs.py:29-30` and `scripts/apply_grammar_record_repairs.py:36-37`
both say *"DB ONLY … exported from the DB by the orchestrator afterwards — do not run an exporter from
here."* `db/corpus.sqlite` is git-ignored (`.gitignore:12`) and is 200 MB. No script reads the committed
JSON back into the DB.

So the artifact `CLAUDE.md` names the source of truth is, operationally, write-only output, and a
teacher's correction has no path into it that does not pass through an untracked binary. This is a
process risk for the review loop specifically: an approval workflow built on the JSON cannot be applied
by any existing tool.

---

## 3. Gaps

**G1 — No approval representation. (M · depends on: an owner ruling on what an approval asserts · AI-authorable once ruled)**
Nothing can be marked teacher-approved. Without it the review loop cannot start, cannot report progress,
and cannot stop a second reviewer redoing the first one's work. *Learner impact:* the app cannot hide or
label unreviewed material, so every learner sees Layer C pedagogy and AI Japanese with no signal.

**G2 — No approval durability. (S · depends on: G1 · AI)**
An approval that is not anchored to the exact approved text silently transfers to whatever a later
repair campaign rewrites. Given that four campaigns rewrote 1,203 fields in the last two weeks, this is
not hypothetical. *Learner impact:* material stamped "teacher-approved" that no teacher saw.

**G3 — `layer`/`source` missing on 11 entities (11,695 records; 21,895 missing `layer` in total). (M · depends on: an owner ruling on per-record vs per-field layer · AI-authorable after)**
`kanji` mixes Layer-A readings, Layer-B pt-BR meanings and Layer-C reading notes in one record, so a
single record-level `layer` is a lie for two thirds of it. That ruling is the blocker; the backfill
itself is mechanical. *Learner impact:* §1.3's promise — trust A blindly, audit C selectively — is not
executable, so a reviewer must audit everything or nothing.

**G4 — 14,958 review flags dropped at export. (S · depends on: G3 · AI)**
`vocab_sense` (10,592), `kanji_reading` (3,970) and `family` (396) are flagged in the DB and unflagged
in the JSON. Two lines of exporter each. *Learner impact:* the 24,030 vocab and 27,972 kanji pt-BR
strings are invisible to any queue built on the export.

**G5 — `review_queue.py` reads the wrong artifact, is stale, and emits counts. (S · depends on: G1 for the subtraction, nothing for the rewrite · AI)**
Rewrite off the export, emit per-item rows carrying the evidence already stored (`jp_source`,
`pt_validated_against`, `ai_generated`, `level_confidence`, `level_agreement`), subtract approved rows,
report coverage. *Learner impact:* indirect — no one can see how much of the corpus is reviewed.

**G6 — `validate_generated_jp.py` and `run_golden.py` are not in the gate. (S · depends on: installing `sudachidict_core` · AI)**
Also grow `golden_set.json` past 14 cases. *Learner impact:* 2,213 generated Japanese sentences ship
without the battery designed for exactly them.

**G7 — Nothing gates that a repair table applied. (S · none · AI)**
16 `form_meanings` rows no-oped in silence. A validator that replays every table in
`research/derived/repairs/` against the export and fails on a row whose `new` is absent while its `old`
is present would have caught it. *Learner impact:* a defect the campaign reported as fixed is still live.

**G8 — 3,466 sentences (58.9%) carry no grammar link, and nothing watches it. (M · none · AI)**
The unlink actions can only shrink the pool. A frozen-baseline gate in the style of
`lesson_sentence_baseline.json` would let it shrink only deliberately. *Learner impact:* grammar points
are illustrated from a pool 41% the size of the bank; several N4/N3 points have few or no carriers.

**G9 — No human-readable view for corpus registries. (L · depends on: G1, G5 · AI)**
`validate_md_views.py` guarantees byte-identical `.md` views for all 322 lessons. `corpus/` gets
`INDEX.md` only — a teacher reviewing a vocab gloss or a kanji note reads raw JSON. *Learner impact:*
review throughput, which is the whole bottleneck.

**G10 — No correction-rate metric. (S · depends on: G1 · AI to build, teacher to feed)**
`design/translation_qa.md` §0.1 names it the health metric and binds the whole plan to it ("a rising
correction rate blocks shipping"). It cannot be computed without approval records.

**G11 — Evidence corrupted where it matters most. (M · depends on: PENDING A9 and A4 · owner decided, not executed)**
22 vocab records resolve to the wrong JMdict entry, eleven of them carrying `level_confidence: 1.0`.
339 grammar records pair `level_agreement: "1/1"` with contradictory confidences (132 at 0.34, 207 at
1.0), held by the frozen L4–L6 ratchet. *Learner impact:* はい/"sim", どう, する, なる and その are
absent or misplaced at N5 — week-one material.

**G12 — No path from an approval or a teacher edit into the committed JSON. (L · depends on: an owner ruling on which artifact is operationally authoritative · AI-authorable after)**
Every applier is DB-only and no importer reads the JSON back. *Learner impact:* none directly; it is
the reason the loop cannot close.

---

## 4. Quality risks against the near-100% goal

1. **"Green gate" reads as "verified corpus" and is not.** The provenance gate certifies the *meaning*
   of four fields on the records that carry them. 22.4% of records carry none of them and pass.
2. **`needs_review` is not a risk signal.** Six of seven entities publish it as a constant. Any
   risk-first ordering must be recomputed from `jp_source` / `pt_validated_against` / `ai_generated` /
   `level_confidence`, none of which a queue reads today.
3. **100% of the bank's pt-BR is model-authored** (`pt_source: "ai"`, 5,889/5,889) and 2,684 of those
   translations were validated against a dictionary rather than a trusted English anchor. That is the
   single largest concentration of unverified learner-facing prose in the corpus.
4. **Layer C is unlabelled where it is densest.** 496 grammar records, 322 lessons and 396 families
   carry authored pedagogy and no `layer`. A reviewer cannot filter "needs full pedagogical sign-off"
   from "needs a spot-check" without knowing the entity taxonomy by heart.
5. **Approvals will rot on contact with the next campaign** unless G2 lands with G1. Four campaigns
   rewrote 1,203 fields in two weeks.
6. **The naturalness contract is effectively unenforced.** 1 flagged field in 244,389 strings is not a
   measurement. The `humanizer` is prompt-time only and nothing records that it ran.
7. **A repair reported as landed may not have landed** (16 confirmed instances) and no gate would say so.
8. **The whole edit path depends on a 200 MB untracked SQLite.** Losing it does not lose the data, but
   it does lose every applier's ability to write.
9. **Every "verification" to date is AI-on-AI.** The two-vote adversarial protocol is real and
   documented (`apply_kanji_note_review.py`: "Only problems BOTH checkers raised … are applied"), but
   no human has signed anything, and `design/translation_qa.md` §9.4's human-review floor — a fixed
   percentage sampled into the teacher queue regardless of score, so the automated gate is itself
   audited — does not exist.

---

## 5. Minimum review workflow with no schema change

**The constraint.** `additionalProperties: false` sits at every record root (contracts/README.md, "What
regeneration can and cannot catch"), and `validate_schema_generation_is_current.py` requires the
committed contracts to reproduce byte-for-byte from `infer_shapes → build_schemas → build_manifest`. So
adding `reviewed_by` to a record is a contract change by construction, on 23 schemas.

**The escape hatch already exists and already names this use case.**
`design/generated_artifacts.json`'s own `why` reads: *"a derived projection, **a review queue** or a
quarantine log qualifies; a registry does not."* `validate_course_chain.py` fails on any published JSON
that is neither matched by an entity glob nor listed there, and on a listing that matches no file — so
the ledger is gated the day it is added. Two live precedents:
`course/vocab_disambiguation_review.json` (14-row teacher queue with `evidence` and per-row
`needs_review`) and `corpus/exam_banks/removed_items.json` (118-item quarantine log with per-item
`reason`).

**The minimum, in order:**

1. **`review/ledger.json`** — one sidecar, outside every entity glob, listed in
   `design/generated_artifacts.json` with its reason. Rows:

   ```json
   { "target": "vocab:1472870", "scope": "senses[0].gloss.pt-BR",
     "verdict": "approved", "reviewer": "<initials or role>",
     "reviewed_at": "2026-09-05", "text_sha256": "…", "note": "" }
   ```

   `verdict ∈ {approved, rejected, changes_requested}`. `scope` is a field path or the literal
   `"record"`. `target` is a **stable id** — never the integer `id`, per contracts/README.md.

2. **`scripts/validate/validate_review_ledger.py`**, hard, plant-proved per the suite's entry
   requirement:
   - every `target` resolves in the export (reuse `validate_contracts.py`'s resolver);
   - every `scope` path exists on that record;
   - **`text_sha256` still equals the hash of the live text** — a record edited after approval
     reverts to unreviewed automatically, which is G2 solved in one check;
   - a row matching nothing is a failure (the exemption-file convention, README "Conventions");
   - the ledger may only grow, and the *unapproved* count may only shrink (the ratchet convention).

3. **Rewrite `scripts/export/review_queue.py` off the export.** Per-item rows, not counts; carry the
   evidence already stored (`jp_source`, `pt_source`, `pt_validated_against`, `ai_generated`,
   `level_confidence`, `level_agreement`) so the reviewer confirms against shown evidence rather than
   re-deriving it (`translation_qa.md` §0.1); subtract ledger-approved rows; print coverage per entity.
   Put it in the SUITE as advisory so it cannot go stale again.

4. **"Teacher-approved" becomes a derived predicate, not a stored field:**
   `needs_review == true ∧ ledger[target, scope].verdict == "approved" ∧ hash matches`.
   No entity schema changes, no data migration, no contract regeneration. One new gate.

5. **Correction rate falls out for free** — `rejected + changes_requested` over total reviewed, per
   entity and per source class, which is `translation_qa.md` §0.1's health metric.

**What this does not solve, and cannot without a contract change:** G3. Backfilling `layer`/`source`
onto the 11 provenance-less entities *is* a schema change (regenerate and commit the contracts, then
pin those entities in `REQUIRED_PROVENANCE` so the inference hole closes). It is worth doing and it is
the only item here that touches the contracts.

---

## 6. Recommended sequence

| # | Step | Size | Why here |
|---|---|:--:|---|
| 1 | **Owner ruling:** what an approval asserts, at what granularity (record vs field), who signs, and whether `layer` is per-record or per-field on mixed registries | S | Blocks G1 and G3; everything else is mechanical once these two sentences exist |
| 2 | `review/ledger.json` + `validate_review_ledger.py` (hash-anchored, plant-proved) + the `generated_artifacts.json` entry | M | The loop cannot start without an exit; the hash check must ship *with* it, not after |
| 3 | Export the 14,958 flags the DB already holds (`vocab_sense`, `kanji_reading`, `family`) | S | Two lines per entity; without it the queue is blind to 51,000+ pt-BR strings |
| 4 | Rewrite `review_queue.py` off the export, per-item, evidence-carrying, ledger-subtracting | S | First moment anyone can see how much of the corpus is reviewed |
| 5 | Backfill `layer` + `source` on the 11 entities; regenerate contracts; pin them in `REQUIRED_PROVENANCE` | M | Closes the inference hole so the gate stops certifying absence; needs step 1's ruling |
| 6 | Wire `validate_generated_jp.py` + `run_golden.py` into `validate_all.py`; install `sudachidict_core`; grow `golden_set.json` well past 14 cases | S | Cheap, and it is the gate the 2,213 generated sentences were supposed to have |
| 7 | Repair-table replay gate (G7) and the zero-grammar-link baseline (G8) | S+M | Both are frozen-baseline gates in the shape the suite already uses; each closes a class of silent regression |
| 8 | Execute PENDING A9 (vocab identity migration) and A4 (level-confidence formula) | M | Until these land, the evidence a reviewer would rank by is wrong exactly where the records are wrong |
| 9 | Human-readable `.md` views for the corpus registries (G9), then the §9.4 sampled human-review floor | L | Throughput and self-audit; only worth building once 1–4 exist |
| 10 | Owner ruling + build: how an approval or a teacher edit reaches the committed JSON (G12) | L | The loop is open until this closes; deferrable while the reviewer count is zero |

**Cited files:** `scripts/validate/validate_provenance_json.py`, `scripts/validate/validate_all.py`,
`scripts/validate/README.md`, `scripts/validate/audit_hygiene_all_locales.py`,
`scripts/validate/detect_ai_tells.py`, `scripts/validate/validate_lesson_gating.py`,
`scripts/validate/validate_generated_jp.py`, `scripts/validate/run_golden.py`,
`scripts/validate/golden_set.json`, `scripts/export/review_queue.py`,
`scripts/export/export_corpus.py`, `scripts/apply_translation_defect_repairs.py`,
`scripts/apply_grammar_record_repairs.py`, `scripts/apply_kanji_note_review.py`,
`contracts/README.md`, `contracts/common.schema.json`, `contracts/manifest.json`,
`design/generated_artifacts.json`, `design/translation_style.md`, `design/translation_qa.md`,
`design/quality_rubric.md`, `design/authoring_failure_modes.md`,
`course/vocab_disambiguation_review.json`, `corpus/exam_banks/removed_items.json`,
`research/derived/fable5_validation/verified_reading_overrides.json`,
`research/derived/repairs/*.json`, `research/reports/qa_sweep/*.md`,
`research/reports/lesson_sentence_review.json`, `research/reports/PENDING.md`,
`reports/review_queue.md`, `prototype/app/lib/exam.server.ts`.
