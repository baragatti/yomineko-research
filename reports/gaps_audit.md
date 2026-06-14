# Build gaps audit (2026-06-14)

> Triggered by the owner spotting empty `explanation_pt`/`formation_pt`/`nuance_pt`/`label_pt` in
> `corpus/grammar/*.json`. A full pass over what the spec's acceptance criteria (§10) require vs. what is
> actually populated in `db/corpus.sqlite`. **Conclusion:** the corpus *registries* (kanji/vocab/grammar/
> families skeleton) + the dissection *pipeline* are done, but the **content layers (Layer-B pt-BR meanings,
> Layer-C grammar explanations), pitch data, and full family coverage were implied but never scheduled as
> runnable steps.** They are now added to STATE (see new sub-phases).

## Measured state (counts from the DB)
| Field / criterion | Populated | Total | Acceptance |
|---|---:|---:|---|
| `vocab_sense.gloss_pt` (pt-BR vocab meanings) | **0** | 4,061 | #2 |
| `kanji.meanings_pt` (pt-BR kanji meanings) | **0** | 250 | #1 |
| `grammar_point.label_pt` | 1 | 364 | #3 |
| `grammar_point.explanation_pt` | **0** | 364 | #3 |
| `grammar_point.formation_pt` | **0** | 364 | #3 |
| `grammar_point.nuance_pt` | **0** | 364 | #3 |
| `vocab_pitch` rows (pitch accent) | **0** | — | owner directive |
| vocab in ≥1 family | 518 | 1,359 | #9 |
| kanji in ≥1 family | 201 | 250 | #9 |
| grammar in ≥1 family | **0** | 364 | #9 |
| `kanji_reading.example_vocab_ids` | 0 | — | #1 ("≥N example words") |
| `topic.objectives_pt` | 0 | 35 | #6/#12 |
| `course_module.overview_pt` | 0 | 3 | #6 |
| `lesson.cumulative_known_set` | 0 | 1 | i+1 (#10) |
| vocab with ≥3 dissected sentences | 5 | 1,359 | #4 (scaling — already planned) |

## What WAS planned & on track
- Corpus registries (kanji/vocab/grammar leveled + linked) ✔
- Sentence dissection pipeline + Workflow scaling ✔ (te-form: 19 sentences, proven)
- Course outline (35 topics) + introducing-topic placement ✔
- Structural families (conjugation/adjective/counter/kanji-component) ✔

## Gaps now ADDED to the plan (new STATE sub-phases)
1. **P2b — Pitch accent ingestion.** Source a CC-licensed pitch dataset (kanjium/OJAD-derived), ingest →
   `vocab_pitch` (match by reading). _Data only; audio still deferred._ (owner directive)
2. **P4b — Full family coverage.** Add the missing family types so **every** N5/N4 item is in ≥1 family:
   `semantic_field` (vocab by theme), `word_family` (derivational), `particle_set` + `contrast_pair`
   (grammar: は↔が, に↔で, あげる/くれる/もらう…), `function_set`. (#9)
3. **P5b — Layer-B meanings (pt-BR).** Translate `vocab_sense.gloss_en → gloss_pt` (4,061 senses) and
   `kanji.meanings_en → meanings_pt` (250), via the batch→Workflow→validate pattern. Also populate
   `kanji_reading.example_vocab_ids` (derivable). (#1, #2) **Foundational — lessons/dissections depend on it.**
4. **P6-grammar — Layer-C grammar explanations.** Author `label_pt` + `explanation_pt` + `formation_pt` +
   `nuance_pt` (pitfalls for PT speakers) for every taught grammar point, via Workflow (research-grounded,
   needs_review). (#3) ← the owner's flag.
5. **P6 (existing) — topic objectives + module overviews** authored alongside lessons.
6. **P7 (existing) — cumulative_known_set materialization**, superset comparison vs L+ `concept_inventory`,
   §1.7 query tests, review queue.

## Execution order (dependency-aware)
P5b (meanings) → P6-grammar (explanations) → P4b (families) → P2b (pitch) → resume topic-by-topic
dissection + lessons (P5/P6) → P7. Meanings come first because glosses, lessons, and exercises reference them.
