# Pilot review — `top:n5-te-form` (P5/P6 gate)

> Scored against [`design/quality_rubric.md`](../design/quality_rubric.md). Pilot scope: the full
> end-to-end pipeline proven on the て-form topic — **5 real Tatoeba sentences** dissected (Layer A
> skeleton + Layer B pt-BR) and **1 authored lesson** (〜てください). Goal of the gate: confirm the
> *approach* and *quality bar* before mass production.

## What the pilot exercised (the whole chain)
leveled corpus → **selection** of real Tatoeba sentences within the topic's cumulative known-set (i+1,
`select_candidates.py`) → **SudachiPy A+C dissection** (`dissect.py`, particle kana/romaji overrides) →
**Layer-B pt-BR** (translation + per-token gloss + particle explanation + structure, `run_pilot.py`) →
**§7 validation** (`validate.py`) → **persistence** (`persist_dissection.py`) → **lesson authoring**
by-ID (`add_pilot_lesson.py`) → **LLM-readable export** (`corpus/sentences/`, `course/n5/topic-15-te-form/`).

## Hard gates (G1–G6)
| Gate | Result | Evidence |
|------|--------|----------|
| G1 no hallucinated Japanese | ✅ PASS | validate.py: 0 reading/lemma errors; skeleton from analyzer |
| G2 analyzer owns skeleton | ✅ PASS | validate re-derives skeleton from `jp` and matches stored tokens |
| G3 provenance complete | ✅ PASS | every sentence has `source`+`jp_source`+layer; all `needs_review=1` |
| G4 by-ID rule | ✅ PASS | lesson/exercises hold sentence **IDs** only; no embedded text |
| G5 clean-room | ✅ PASS | zero local-course content/names anywhere |
| G6 pt-BR + style | ✅ PASS | learner content pt-BR; terms introduced; Vantagem/Armadilha callouts |

## Dimension scores (0–4; pass bar ≥3)
| Dim | Score | Note |
|-----|------:|------|
| D1 accuracy & provenance | **3** | Validated; full provenance. Fix: compute `sentence.level` from components (3 warns) instead of hardcoding. |
| D2 explanation depth | **4** | Group-by-group て-form rules, the 出る+に nuance, 〜てから, PT callouts — beats incumbents. |
| D3 example richness | **3** | 5 te-form sentences, every token glossed, every particle explained (≥5/grammar met for te-form). Vocab ≥3-each pending full topic. |
| D4 sequencing | **3** | て-form mid-N5, dependency-correct; chunk sizes sane; family-driven. |
| D5 completeness | **2** | Pilot is 1 lesson, not the whole topic — expected; blocks "done" but not the gate. |
| D6 review & navigability | **4** | All artifacts LLM-readable JSON+MD, by-ID graph, needs_review queue ready. |

## Verdict
**Gate PASSED for the approach** — the pipeline produces paid-grade, verifiable, review-ready content,
and schema_v2 held up with no awkward cases. D5=2 only reflects that a *pilot* is one slice, not full
coverage. Proceed to scale, after the punch-list below.

## Punch-list before mass production (cheap to fix now, costly later)
1. **Compute `sentence.level` = max(component levels)** in `persist_dissection.py` (removes the 3 warns;
   correctness).
2. **Add a bare `te-form` grammar anchor** (the registry only has sub-points like `te-kudasai`/`te-aru`);
   gives a clean hub to attach the ~5 dissected examples and to link from lessons.
3. **Scale dissection via a Workflow** (one agent per sentence: skeleton in → Layer-B out → adversarial
   validate) to hit ≥3/vocab, ≥5/grammar across the topic, then all topics. Hand-authoring proved the bar;
   the workflow industrializes it. Keep real-first + flag all `ai_generated`.
3b. **Tokenization guard:** the selector must drop sentences SudachiPy mis-parses (caught 今本→"Imamoto"
    proper-noun merge); add a sanity check (e.g., reject unknown proper-noun tokens in beginner sentences).
4. **Refine P4 placement** (N4 grammar residual 146 → keyword-map more or LLM-assign; raise N4 kanji cap;
   move a few high-frequency kanji like 母 earlier).
5. **Compute & store `cumulative_known_set`** per lesson once lessons are split within topics (P6).
6. **Translation validation pass**: round-trip / EN cross-check scoring for generated pt-BR at scale.

## Artifacts to review
- Dissected bank: [`corpus/sentences/bank.json`](../corpus/sentences/bank.json) · [INDEX](../corpus/sentences/INDEX.md)
- Lesson: [`course/n5/topic-15-te-form/lesson-01.md`](../course/n5/topic-15-te-form/lesson-01.md) (+ `.json`)
