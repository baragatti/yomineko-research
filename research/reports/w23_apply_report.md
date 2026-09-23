# W23 (apply, C10 checkpoint) - assessment: item_refs, topic tests, placement index, attempt contracts

Run 2026-09-23. Applies `design/assessment.md` (W23 design, 2026-09-10) on the post-W18/W20/W29 tree.
Mechanical: derived 4,701 exercise ref sets + 49 topic tests + 9,716 index entries / authored 0.
Placement stays owner decision **D2**: default (c) is marked on `assessment_attempt`, not enforced.

## 1. What landed

| artifact | kind | numbers |
|---|---|---|
| `lesson.exercises[].item_refs[]` | content field, both layers | 4,746 exercises: **4,701 with a target** (5,858 `role: target` refs; mean 1.25, median 1, p90 2, max 22), 24 exempt, **21 residue** |
| `exercise_item_ref` (migration 019) | index table | 5,858 rows, keyed on the exercise slug; `export_course.py` joins it, sorted by (type, ref) |
| `research/derived/repairs/item_refs.json` | exact-match table | 4,701 rows, replay handler `handle_item_refs` (4,701 PASS); manifest step **139** (families 140-142) |
| `course/item_ref_exemptions.json` | exemption file | 24 exercises (orientação 6, sons 9, pronúncia 9) |
| `research/derived/pending/item_refs_residue.json` | work list | 21 exercises (n5 recognition 6, n3 cloze 6, n4 recognition 4, n3 recognition 2, pre-n5 3) |
| `design/unlock_enums.json#item_ref_type` | design enum | vocab, kanji, grammar, kana, conjugation-form, phrase |
| `common.schema.json#/$defs/ItemRef` | shared def | used by `topic_test.pool[].item_refs` |
| `topic_test` / `course/topic_tests.json` | content entity (hand-authored contract, BLUEPRINT set) | **49 tests**, 13,199 pool entries (8,944 lesson exercises + 4,255 exam items), sizes 12-24 |
| `course/test_exemptions.json` | exemption file | 3 topics (orientação, sons, pronúncia) |
| `course/item_lesson_index.json` | generated map | 9,716 questions: 4,746 exercises + **4,970 of 5,141 exam items** (vocab 3,015, grammar 944, sentence 726, reading 285) |
| `exercise_attempt`, `assessment_attempt` | runtime contracts (`contracts/user_state/`) | 9 runtime entities now |
| `mistake_index` | runtime VIEW | executable spec `mistake_index()` (WEAKNESS_V1) in `test_assessment_fixtures.py`; no table, no manifest row |
| `design/api_contract.md` §8.1 | design | the assessment routes, `topic_test` row in §5.2 |

## 2. How item_refs are derived (`scripts/derive_item_refs.py`)

The rule of design §2.2, importing `validate_practice_coverage`'s matchers, plus one rule the design
could not see:

| rule | exercises |
|---|---:|
| 0 `table:practice_vocab_exercises` | 2,283 |
| 0 `table:practice_kanji_exercises` | 899 |
| **0b `authored`** | **553** |
| 2 `answer` | 647 |
| 2+3 `answer` + `prompt-unlocks` | 50 |
| 3 `prompt-unlocks` | 143 |
| 4 `cited-sentence` | 8 |
| 5 `kana` | 118 |

**Finding: the field was not empty.** 556 hand-authored exercises (N5 and N4: 553 resolve, 288 + 265) carried authored
`item_refs` in `research/derived/lessons/` as bare `{type, ref}` (kanji character, grammar key, vocab
headword). `load_lessons.py` loaded them into `exercise_item`; the exporter never emitted them, so the
design, measuring the export, called the field empty. They name what the author asked about: the
causative-passive point of `ex:n4-causativa-03-3` where the matcher sees only the kanji of the stem.
The matchers agree with the author on **391 of 578** authored refs (67.6%), so the author's word wins
(rule 0b), each ref resolved to the one published id inside the lesson's known set. Three name nothing
there (気分 and さっき are taught later than the exercise; one headword has two records in the known set):
they stay verbatim in the authoring source (`authored_unresolved` in the table) and are not exported.

**Honesty check.** Rules 1-6 run blind over the table rows recover **3,172 / 3,373** true targets
(94.0%). The derivation is stable: re-deriving on the post-apply tree reproduces the table byte for byte.

**Exemption rule, tightened.** An exercise is exempt only when its lesson unlocks no item AND is not a
review lesson. The first cut exempted 4 revisão items (their lesson unlocks nothing on purpose; they test
earlier items), which is residue, not metalanguage.

**Practice gate.** `validate_practice_coverage` now also reads an exercise's `role: target` refs as
explicit markup (design §2.7). Grammar absent 19 -> 6 (n5 12 -> 4, n4 6 -> 2, n3 1 -> 0), ceilings
lowered; vocab and kanji unchanged. Practised 99.9% (4,073 / 4,079).

## 3. Topic tests (`scripts/export/build_topic_tests.py`)

Scope `own` 46 topics, `range` 3 revisão topics (the level's topics since the previous review), `none`
3. Kana families expanded to glyphs; conjugation-form / phrase unlocks out of scope (nothing targets one
yet). Size `clamp(floor(n/8 + 0.5), 12, 24)`; mix proportional with floor 1. Pool = the scope lessons'
exercises whose targets meet the scope, then exam items (no listening) keyed to the scope and inside
the topic's last lesson's known set by `validate_exam_level_gate`'s own predicate. Every mix is
satisfiable without minting.

Deviations from the design, each forced by the tree:
- **Form floors.** Five topics (hiragana, katakana, saudações, the two kanji-exame) teach no cloze or
  sentence_build, so `min_constructed` is 0 there (1 where the pool has one). The contract allows 0.
- **One file.** `course/topic_tests.json` rather than `course/tests/*.json`:
  `validate_course_chain.check_filesystem` fails any non-level directory under `course/`.
- **Size.** The revisão pools are large (n3 3,116 entries); the file is 3.4 MB. Fine for sync.

## 4. Storage deviation

Design §2.5 proposed two columns on `exercise_item`. That table keys a member by registry ROW id
(kanji / vocab / grammar only), so it cannot hold a `kana:` glyph, and `load_lessons.py` renumbers
`exercise.id` on every reload. `exercise_item_ref` keys on published addresses, like `card_example`.

## 5. Gates and plant proof

New in `validate_all.py`: `validate_item_refs.py` (A-G + residue ratchet `item_refs_baseline.json`),
`validate_topic_tests.py` (A-H), `validate_placement_index.py` (byte-identical + exam floor 4,970),
`test_assessment_fixtures.py` (13 cases). Also: `validate_repairs_applied` registers `item_refs.json`;
`design/i18n.md` scope row `topic_test.title`; `design/generated_artifacts.json` lists the index and the
two exemption files.

Plant proof on a copied tree (`corpus/`, `course/`, `research/derived/lessons/`, the three tables, the
validators and their imports copied beside them). Controls green before and after.

| plant | gate | verdict |
|---|---|---|
| a ref at a retired grammar slug | item_refs A | CAUGHT |
| a ref at an N3 word in `les:n5-desu-wa-01` | item_refs B | CAUGHT |
| one exercise's array blanked | item_refs C | CAUGHT (n3 recognition 2 -> 3) |
| an exemption for an exercise with refs | item_refs D | CAUGHT |
| a derived ref hand-edited to another taught word | item_refs E | CAUGHT |
| a pool entry at an out-of-scope item | topic_tests C | CAUGHT |
| a `by_kind` count shrunk | topic_tests D | CAUGHT |
| an N3 exam item in the N5 desu-wa pool | topic_tests E | CAUGHT |
| `total` 0.6 under TOPIC_PASS_V1 | topic_tests F | CAUGHT |
| an index entry moved to another lesson | placement | CAUGHT |
| an index entry removed | placement | CAUGHT |
| an exported ref differs from the table | repairs replay | CAUGHT (value-mismatch 1) |

12 / 12, plus the fixture suite's 13 good/plant pairs (schema x3, context prefix, served refs, FSRS
firewall x2, counters, exam answer stream, WEAKNESS_V1 x2, minimum_met, placement walk-back).

## 6. Lessons did not degrade

Rendered diff of `course/` against HEAD: 322 lesson JSON changed, **0 `.md`**, 4 new files; with
`exercises[].item_refs` stripped, **0 of 322** differ. Authoring layer: 314 files, 0 differ beyond
`item_refs`. Review views re-rendered (build stamp line only).

## 7. Full replay (checkpoint)

**The replay was broken, by C8-W37W40, and is fixed here.** The first full run stopped at step 137:
`apply_provenance_backfill.py` refused 73 `localized_text.layer` rows whose topic-text row a replay
never writes (the rebuild sets objectives on 35 of 52 topics), and step 138 `apply_en_backfill.py`
refused two rows whose pt-BR anchor sits on a re-dissected generated sentence (`sent:gen-cb6562f41e17`,
`sent:gen-8cc2f196d1e9`). C8 committed on the quick replay only, so nothing had run them against a
rebuild. Both now skip an ABSENT anchor off the live index (reported, the `apply_card_examples.py`
rule); a present row with the wrong value still refuses, and on the live index both still refuse
(checked: 0 writes, 638 / 26,099 already applied).

**Two replay side effects on tracked files, fixed.** Every full run rewrote `reports/validation.md`
(`reconcile_levels.py`, step 9) and `research/derived/grammar_merge_ledger.json`
(`migrate_grammar_merge.py`, step 110) from the scratch DB. Both now write only on the live index, the
rule `migrate_vocab_repoint.py` got in C7-W29; the verification replays leave both byte-identical.

**Result.** 142 steps / 106 enabled, all clean (step 139 writes 4,701 ref sets on the rebuild).
790 files compared: **0 new divergences, 0 healed, 324 held files whose rebuilt bytes moved**:

| files | cause |
|---:|---|
| 269 | lessons moved by W23 (`exercises[].item_refs`); the other 53 lessons W23 changed match the rebuild exactly |
| 55 | corpus / course files moved by C8-W37W40 (`f2d88686`, steps 137-138), committed on the quick replay only |

`--record` re-pinned the 324 hashes; each keeps its `_causes` key and gains a dated re-pin note naming
the unit. A verification replay after the record: `[OK] 790 exported file(s) checked, 571 held by
rebuild_baseline.json at the recorded bytes`, and `git status` unchanged by it. `validate_all.py` green
(with the quick replay).

## 8. Open

- **Residue 21** (`pending/item_refs_residue.json`): conjugated cloze fillers, review / contrast items
  whose target is an earlier lesson's; one agent + one verifier.
- **Fable sample 30** of `answer` / `prompt-unlocks` rows read against the rendered exercise (design
  §2.4) and of the 553 authored resolutions.
- `exam_item.item_refs` (design §2.6) was not emitted by W18; the topic-test assembler and the index use
  the read-time join.
- `user_state.md` §3 still does not name `leech_state` beside suspend/bury (design §4.2).
- D2 (owner): placement policy; the queue builder's ranking rule (D8).
