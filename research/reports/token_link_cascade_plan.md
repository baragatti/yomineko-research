# Token-link apply: cascade plan (measurement only)

> Nothing here was applied. No DB, export, course file or baseline in the repo was written; the only repo
> file this unit writes is this report. Everything was measured on scratch copies:
>
> - the export tree at **git HEAD `96ac5fd7`** (`corpus/ course/ scripts/ contracts/ design/ research/reports/
>   research/derived/repairs/`, pulled with `git archive`, so the in-flight writer chain's working-tree edits are not in it);
> - a **sqlite3 backup-API snapshot of `db/corpus.sqlite`** (10,271 sentences: the writer chain has already added
>   62 sentences the HEAD bank does not have yet, and 17,205 `sentence_vocab` rows with `link_rule` NULL);
> - `research/derived/pending/token_link_audit.json` (4,004 rows) and
>   `research/derived/pending/token_link_mechanical_sample.json` (its `exclude_patterns`).
>
> Scratch scripts: `scratchpad/tlr/{sim,cascade,scenD,runval.sh}` (session scratchpad, not in the repo).
> The real gates were run from **copies of the HEAD scripts inside each scratch tree** (`--root .`), so no
> validator could read the real repo by accident.

## 0. Answer

| what moves | number |
|---|---:|
| rows applied (relink 3,224 + unlink 209); review 530 not applied; 41 excluded by the sample | **3,433** |
| sentences touched | **2,879** |
| **sentences whose computed level changes** (edge-exact, variant B) | **271** |
| same, insert-only edges (variant A, what the audit's `replay` text literally says) | 266 |
| stored `sentence.level` values that would change if the touched sentences were re-levelled | 397 |
| `integrity_audit` sentence-level ratchet (ceiling 703) | 688 → **948 FAIL** (A and B); 556 if re-levelled |
| lesson↔sentence display pairs carrying a touched sentence | 154 of 761 |
| check D: `pairs_with_new_vocab` / `pairs_over_budget` / `pairs_above_level` | 25→**103** / 19→**29** / 150→**192** (re-levelled only) |
| lesson exercises citing a touched sentence / whose own-unlock credit changes | 240 / 15 |
| SRS cards whose example is a touched sentence / broken by the relink | 592 / 4 (37 if re-levelled) |
| exam items on a touched sentence / the builder would now reject (vocab dimension) | 471 / **249** |
| W05 ratchet (`below`) | n5 18→**19 FAIL**, n4 19→**21 FAIL**, n3 157→153 (zero 48→43) |

The apply cannot land as a link repair alone. **The course teaches the wrong sibling**: 8 of the most
relinked "old" records are lesson unlocks with SRS cards, in lessons whose text uses the other word (刷る
"imprimir" in `les:n5-verbos-02`, 生る "dar fruto" in `les:n5-verbos-03`, 暮れる "escurecer" in
`les:n4-volitivo-01`, 用 in the ように lesson, 動 in the どうやって lesson, 報 in the ほうが lesson, 罹る, 池).
彼/あれ and 九 are also unlocked, but those really are あれ and "nine" and stay above the floor.
The unlock went through the same written-form lookup the tokens did. Relink the tokens and those words
disappear from the bank (刷る 902 sentences → 0, 暮れる 101 → 0, 報 47 → 0). The words the lessons actually
show (為る, 成る, 呉れる, 様, 方, 掛かる) are then **unknown** in every lesson and exam before the lesson
that unlocks them: N4 at the earliest, N3 or N1 for most. Almost every downstream failure below comes
from that, plus four target records whose registry level belongs to their mislinked sibling (§2.3). Scenario D (§4)
lets the course follow the relink. It clears the exam level gate, check D and the topic-test content failures
completely.

## 1. What was simulated

| step | rows |
|---|---:|
| audit rows | 4,004 |
| `review` (need a human ruling, not applied) | 530 |
| relink + unlink | 3,474 |
| excluded by `token_link_mechanical_sample.json` `exclude_patterns` | 41 |
| of which `aux-sou-to-然う` 21, `census-singletons` 7, `karada-written-身体` 3, `kakaru-disease` 3, `tsuku-lie-and-post` 3, `yoru-drop-by` 3, `doushite-progressive` 1 | |
| **applied** | **3,433** (relink 3,224, unlink 209) |
| refused by the replay guard (token at (slug, position) no longer carries `old_vocab`/`surface`) | 0 on the HEAD bank; 0 of 3,433 on the DB snapshot |

The excluded rows were dropped, not converted. Their `apply_instead` (21 そう rows → unlink, 3 よっ → 寄る,
2 つく → 吐く, 1 → 就く, 2 singletons → unlink) was not simulated. They move 30 more tokens, and none of
them changes the conclusions.

**Two edge variants**, because the audit's `replay` step (4) ("then run `build_sentence_vocab.py`") is not
enough on its own:

- **A, insert-only.** `build_sentence_vocab.py` is `INSERT OR IGNORE` and never deletes. After a relink the
  stale `(sentence, old_vocab)` edge survives in `sentence_vocab`, and so in the exported `sentence.vocab[]`.
  On the snapshot: 3,433 token updates, **2,745 edges inserted, 0 deleted**.
- **B, edge-exact.** The old edge is deleted unless another rule still produces it. **1,195 deleted** (old
  record n5 1,091, n4 81, n3 17, n2 5, n1 1). **2,176 survive** because R2 (the run rule, gated n5/n4) produces
  them again from the same surface. 刷る/する is n5 and owns the form する, so every literal する token keeps a
  刷る edge whatever the token says. 2 survive because another token in the sentence still carries the record.
  This is R2's documented multi-valued design, not a bug in this apply, but it means `sentence.vocab[]`
  never loses the wrong sibling while R2 is gated on the sibling's level.

A and B barely differ on level (266 vs 271), because the deleted edges are almost all to a *lower*-level
record than the one that replaces them. They differ on `sentence.vocab[]` content, which the card-example
and exam builders read.

## 2. Sentence levels

### 2.1 Computed level (from `sentence.vocab[]` edges plus the kanji in `jp`, same rule as `persist_dissection.computed_level`)

| transition | A | B |
|---|---:|---:|
| n5→n4 | 3 | 3 |
| n5→n3 | 21 | 21 |
| n5→n2 | 1 | 1 |
| n4→n3 | 126 | 126 |
| n4→n2 | 10 | 10 |
| n4→n1 | 28 | 28 |
| n3→n2 | 20 | 20 |
| n3→n1 | 40 | 40 |
| n2→n1 | 17 | 17 |
| n2→n3 (down) | — | 4 |
| n1→n3 (down) | — | 1 |
| **total** | **266** | **271** |

Cross-check against the audit's own `sentence_level_if_applied` (334 rows carry it): 325 of the 326 rows
that were applied agree with B exactly.

### 2.2 What drives it (B, row counts on sentences whose level moved)

| old → new | direction | rows |
|---|---|---:|
| 生る/なる n5 → 成る/なる **n3** | up | 105 |
| 暮れる/くれる n4 → 呉れる/くれる **n1** | up | 80 |
| 報/ほう n5 → 方/ほう **n3** | up | 23 |
| 夜/よる n5 → 依る/よる **n2** | up | 20 |
| 罹る/かかる n5 → 掛かる/かかる **n3** | up | 17 |
| 刷る/する n5 → 為る/する **n4** | up | 14 |
| 彼/あれ n5 → 彼/かれ n4 | up | 7 |
| 不利 n3 → 振り n2, 池 → 行けない n3, 其れ → 逸れる n2, … | up | 5, 5, 3, … |
| 乞う n2 → 斯う n4, 共/ども n1 → unlink | down | 4, 1 |

### 2.3 Most of the rise is a registry level fault, not a harder sentence

The audit's replay note says it: several targets carry the level of their mislinked sibling. する, なる,
くれる and かれ are N5/N4 words. Their JLPT consensus level sits on the rare homograph (刷る, 生る, 暮れる,
彼/あれ) because the level was resolved by reading, like the tokens were. **Variant C** keeps B's edges but
lets the level move with the word for the four pairs with ≥50 rows and an inverted level (成る n3→n5,
呉れる n1→n4, 為る n4→n5, 彼/かれ n4→n5). Computed-level changes fall **271 → 88**. The rest is 方 n3, 掛かる n3,
依る n2, 振り n2 and genuinely harder sentences. Variant C is a level-evidence decision for
`apply_level_evidence.py` / `level_evidence_repairs.json`, backed by the ≥3-list consensus rule (§1.5). It is
not something this apply may decide.

### 2.4 Stored level and the integrity ratchet

`sentence.level` is not recomputed by a link repair (build_sentence_vocab.py, apply_orthographic_relinks.py
and integrity_audit.py all forbid it). So the stored level stays and `integrity_audit` counts the gap:

| | stored < component level | gate (ceiling 703) |
|---|---:|---|
| HEAD bank / DB snapshot | 688 | WARN |
| A (bank and snapshot, `integrity_audit.py` run on `snapA.sqlite`) | 948 | **FAIL** |
| B (snapshot `snapB.sqlite`) | 948 | **FAIL** |
| B, touched sentences re-levelled | 556 | WARN |

Re-levelling the 2,879 touched sentences would rewrite 397 stored levels, not 271: 132 touched sentences were
already stale before this apply. Transitions if re-levelled: n4→n3 236, n3→n1 35, n4→n1 33, n5→n3 34,
n3→n2 20, n2→n1 17, n4→n2 9, n5→n4 6, n2→n3 4, n5→n2 2, n1→n3 1.

## 3. Downstream, per consumer (real gates on the scratch trees)

`before` = HEAD tree: every gate below passes. `A` = relinked tokens, insert-only edges, stored levels
frozen. `B` = relinked tokens, edge-exact edges, touched sentences re-levelled.

| gate | before | A | B |
|---|---|---|---|
| `validate_lesson_gating` | 0 FAIL | **20** (C4 15, D 4) | **27** (C4 15, D 11) |
| `validate_exam_level_gate` | ALL OK | **19** (R 16, S 3) | **19** |
| `validate_topic_tests` | 0 | **204** (E) | 204 |
| `validate_sentence_coverage` (W05) | ratchet held | **2** | 2 |
| `validate_practice_coverage` | 0 | **1** ((n5, vocab) absent 0→2) | 1 |
| `validate_card_content` | 0 | **4** (check F) | **37** |
| `validate_item_refs` | 0 | **2** | 2 |
| `validate_placement_index` | 0 | **1** (73 index entries differ) | 1 |
| `validate_speaking_path` | 0 | **1** | 1 |
| `validate_role_exercises` | ALL OK | ALL OK | **377** |
| `integrity_audit` (DB snapshot) | WARN 688 | **FAIL 948** | FAIL 948 |
| `validate_exam_banks`, `validate_srs_decks`, `validate_graph_edges`, `validate_conjugation_exercises`, `validate_exam_stem_collisions` | OK | OK | OK |

(`validate_display_consistency` reads the DB at `--root/db` and did not run on the export-only trees.)

### 3.1 Lessons: cumulative known sets and i+1 (check C4, check D)

- **154** of the 761 lesson↔sentence display pairs show a touched sentence.
- **D, links only (A):** 78 pairs gain an unknown word (`pairs_with_new_vocab` 25 → 103), 10 go over the
  i+1 budget (19 → 29; n4 2 → 6, the rest n5). The unknown words are the relink targets the lesson has not
  unlocked yet: する, なる, くれる, ほう, この中 and so on, in N5 lessons that unlock the wrong sibling.
- **D, re-levelled (B):** another **42 pairs go above the lesson's level** (150 → 192). By lesson level: n5
  10 (大人になりたい, もっと休みをとったほうがいい, 行かないといけないの？ …), n4 25 (〜になる ×13,
  〜てくれる ×4, 〜なければいけない ×4, お茶のような…), n3 7 (〜によれば, 〜てくれ ×3, 知らぬふり).
  The full list is in `scratchpad/tlr/cascade.json`, `lesson_pair_changes_B`.
- **C4 (needs):** `derive_needs` reads the token links, so 14 stored needs are no longer derived, 8 derived
  needs are not stored, and one stored note names the wrong word ("…as palavras 行く (いく) e 生る (なる)…").
- **C5 forward references:** unchanged (19 / 174).

### 3.2 Practice coverage (exercises whose cited token changes item)

- **240** exercise↔sentence citations in lessons point at a touched sentence. **15** of them change which of
  the lesson's own unlocks the exercise credits. 10 only lose one (用 in `n4-oracoes-relativas-07`, 暮れる in
  `n4-volitivo-01`, 動 ×2 in `n5-perguntas-05`, 生る ×2 in `n5-verbos-03`, 報 ×4 in `n5-comparacoes-01`), 1
  swaps (九 → 此処 in `n5-perguntas-01`) and 4 only gain one (中/なか in `n5-comparacoes-02`). 3 exercises' `item_refs` name a record that leaves the
  sentence.
- The gate: **(n5, vocab) absent 0 → 2**. 動 and 報 are left with no drill in their own lessons.
- `validate_item_refs`: `ex:n4-condicionais-03-4` (九 → 此処) and `ex:n5-conectando-05-1` (報 drops out) no
  longer match what `derive_item_refs` derives.
- Corpus exercises: 542 role items (n3 246, n4 269, n5 27) and 163 conjugation items cite a touched sentence.
  Their text does not change and both gates pass under A. Under re-levelling, **377 role items fail**
  ("level n3 but the sentence is n1"): `build_role_exercises.py` files items by sentence level.

### 3.3 SRS card examples

- **592** cards use a touched sentence as their example (vocab 382, kanji 133, grammar 77).
- A: **4 cloze spans no longer hold the card's own token.** These cards teach the wrong sibling: いらっしゃい
  (`n3-tempo-04`), 用 (`n4-oracoes-relativas-07`), 暮れる (`n4-volitivo-01`), 動 (`n5-perguntas-05`).
- B: 37 check-F failures. The same 4 plus 33 whose example sentence is now graded above the lesson that
  issues the card. 73 card examples in all go above their lesson's level if the touched sentences are re-levelled.
- Content finding for the teacher, not caused by this apply: the N5 decks carry cards for 刷る "imprimir",
  生る "dar frutos", 罹る, 報, 動 and 池, with production keys that accept the kana (する, なる, かかる…).
  Those cards exist because the unlock resolved to the wrong sibling.

### 3.4 Exam banks (which items the builder would drop or change)

`exam_rules.TaughtSets` was applied to each item on a touched sentence: its own `vocab` plus every
`tokens[].vocab` of its source sentence must be in the level's taught vocab. That is the selection rule
`build_exam_banks.py` enforces and the rule `validate_exam_level_gate` measures.

| bank | items on a touched sentence | level-clean → dirty (builder drops) | sentence goes above bank level if re-levelled |
|---|---:|---:|---:|
| n5_context_fill | 31 | 17 | 17 |
| n5_grammar_form | 11 | 7 | 7 |
| n5_sentence_order | 20 | 10 | 11 |
| n5_paraphrase | 2 | 1 | 1 |
| n5_usage | 2 | 1 | 1 |
| n4_context_fill | 76 | 52 | 47 |
| n4_grammar_form | 71 | 43 | 40 |
| n4_sentence_order | 76 | 53 | 44 |
| n4_paraphrase | 6 | 5 | 4 |
| n4_usage | 5 | 4 | 4 |
| n3_context_fill | 49 | 7 | 3 |
| n3_grammar_form | 75 | 39 | 22 |
| n3_sentence_order | 36 | 4 | 2 |
| n3_paraphrase | 4 | 2 | — |
| n3_usage | 6 | 3 | — |
| n3_listening_reply | 1 | 1 | 1 |
| **total** | **471** | **249** (n5 36, n4 157, n3 56) | 204 |

- The untaught words responsible: 成る 76 items, 様/よう 75 (plus 2 alongside 依る/逸れる), 方 28, 呉れる 23,
  掛かる 20, 依る 8, 行けない 6, 振り 3, 為る 2, 否 1, 逸れる 1, … 様/よう is taught nowhere. The auxiliary
  よう that 173 rows move from 用 to 様 has no lesson unlock under either record.
- No item names a relinked-away record as its own `vocab` (0 items change their word under test). The
  change comes entirely from the source sentence's token links.
- Gate result (A): 16 R growths (the counts above) plus **3 S sufficiency failures that a rebuild cannot
  refill**: n5_paraphrase 8 usable vs 3 per paper, n4_paraphrase 10 vs 4, n4_usage 10 vs 4 (floor 3×).
  Those are authored banks (`build_authored_banks.py`), so replacing the dropped items means authoring.
- **Topic tests:** 204 E failures (grammar_form and similar items drawn into topic-test pools now use
  untaught Japanese): n4-revisao 51, n3-revisao 44, n3-intencao 17, n4-suposicao 15, n5-revisao 12, …
- **Speaking path:** checkpoint `cf:n3:116:884` in `speak:lodging-02` goes to 4 unknown words (budget 3).
  270 references in `course/speak/*` point at touched sentences. The builder has its own `link_ok` guard
  against exactly these homograph mislinks (build_speaking_path.py:253-282), so a rebuild is needed before
  anyone can tell what really changes.
- `course/item_lesson_index.json`: 73 entries differ from what `build_item_lesson_index.py` derives.
- The exam context_fill builder reads `(sentence, vocab)` pairs from `sentence_vocab`. Under A the 2,745 new
  pairs become candidates and none disappear. Under B 1,195 old pairs disappear. No committed cf item is
  keyed on a disappearing pair (see the "own vocab" line above).

### 3.5 W05 sentence coverage ratchet, per level

| (level, kind) | taught | below: HEAD → A | zero: HEAD → A | gate |
|---|---:|---|---|---|
| n5 \| vocab | 703 | 18 → **19** | 14 → 14 | **FAIL** |
| n4 \| vocab | 651 | 19 → **21** | 10 → 10 | **FAIL** |
| n3 \| vocab | 1,596 | 157 → 153 | 48 → 43 | would lower |
| grammar (all levels) | — | unchanged | unchanged | — |

(B has the same token links, so W05 is identical.)

Records that cross the ≥3 floor (distinct sentences, HEAD → A):

- **fall below:** 刷る 902→0, 生る 387→2, 動 133→1, 池 59→2, 報 47→0, 伯 8→0, 八つ 4→0, 杯 3→0 (n5);
  用 175→2, 暮れる 101→0, 家内 3→1 (n4); 不利 7→1, 輪 3→2 (n3).
- **rise over:** 此処 2→99, 如何して 0→20, 門 0→12, 零 0→9, 中/ちゅう 0→6, １日/ついたち 0→6, ３日 2→3 (n5);
  裏 0→11 (n4); 方 0→47, 或る 2→7, 息 0→5, 詩 0→5, 案 0→4, 否 2→4 (n3).

Each record that falls is a taught wrong sibling: the course unlocks a word the bank does not actually
contain. The ratchet is right to fail, and the fix belongs to the course (§4), not to the ceiling.

## 4. Scenario D: the course follows the relink

On the A tree, every relink target was added to the unlocks of each lesson that unlocks its old record, and
to every `cumulative_known_set` holding the old record (53 unlocks added, 6,912 cks entries, 281 lessons).
This is an upper bound, and it adds rather than replaces:

| gate | A | D |
|---|---|---|
| `validate_exam_level_gate` | FAIL 19 | **ALL OK** |
| check D | 4 FAIL (over 29, new vocab 103) | **0 FAIL** (over 15, new vocab 19, both under baseline) |
| `validate_topic_tests` | 204 E | 0 E; 29 B (topic scope, `build_topic_tests.py` re-derives it) |
| `validate_practice_coverage` | (n5, vocab) absent 2 | n5 26, n4 7: the new unlocks have no drill yet |
| W05 | n5 +1, n4 +2 | same, plus n1\|vocab and n2\|vocab rows with no ceiling (呉れる, 依る, 振り… become taught) |

The right shape is therefore a **repoint, not an addition**: the lesson that unlocks 刷る "imprimir" is teaching
する. Moving that unlock, its cks entries and its SRS card from the wrong sibling to the right one retires the
W05 fallers and the practice gap together. It is a migration of published addresses in the
`scripts/migrate_vocab_repoint.py` sense (whose REFUSED list already names 成る at n3 as a collision), and it
needs an owner ruling per record. Candidates are the taught old records that fall to <3 sentences after the
relink: 刷る→為る, 生る→成る, 暮れる→呉れる, 用→様, 報→方, 罹る→掛かる, 動→(どう has no record), 池→行けない, 伯,
八つ, 杯, 家内. It should be combined with the level transfer in §2.3. Without it, 呉れる (n1) and 依る (n2)
become taught N4/N5 words filed at N1/N2.

## 5. Run order for the apply (DB writer, single chain)

Prerequisites, each its own reviewed unit:

- **P1. Fix the resolver first.** Put the reading and the normalized form into `scripts/ingest/dissect.py`'s
  form lookup, with `token_link_audit.json` as its regression check. The audit shows the 2026-08-19 homophone
  repoint was undone by a later re-dissection. A table replayed onto a resolver that still resolves by
  written form alone gets undone again on the next replay.
- **P2. Owner rulings:** the level transfer (§2.3), the course repoint (§4), and whether touched sentences are
  re-levelled (§2.4). The integrity ceiling fails at 948 without one of them.

The apply itself:

1. **New `scripts/apply_token_link_audit.py`** (tracked table in `research/derived/repairs/`, rows minus
   `exclude_patterns`, with the `apply_instead` conversions). Guard per the audit's `replay` (2). Write
   `token.vocab_id`, then do the edge work **edge-exact**: insert the new pair and delete the old pair only
   when no token, run (R2) or lemma (R3) rule and no `ortho` row still produces it. Do not rely on
   `build_sentence_vocab.py` to remove anything; it never deletes.
2. `scripts/ingest/build_sentence_vocab.py`: idempotency check only, expect `+0`.
3. If ruled: `scripts/apply_level_evidence.py` with the level-transfer rows, then a scoped re-level of the
   touched sentences (a new step, never `recompute_all_levels()` corpus-wide).
4. If ruled: the course repoint (a `migrate_vocab_repoint.py`-style unit over unlocks, cks and cards).
5. `scripts/export/export_corpus.py` → `scripts/export/export_course.py` → `scripts/export/export_readings.py`
6. `scripts/build_needs_table.py` → `scripts/apply_lesson_needs.py` (C4; the needs note naming 生る)
7. `scripts/derive_item_refs.py` → `scripts/apply_item_refs.py`
8. `scripts/build_vocab_exercises.py` / `scripts/apply_practice_exercises.py` (W20 drills for the repointed unlocks)
9. `scripts/derive_card_examples.py` → `scripts/apply_card_examples.py` (4 or 37 cards; plus cards moved by 4.)
10. `scripts/derive_lesson_sentences.py` (W14 re-selection review for the 42 above-level / 10 over-budget pairs;
    apply only on a teacher ruling)
11. `scripts/export/build_role_exercises.py` (re-files by sentence level if step 3 ran)
12. `scripts/export/build_exam_banks.py` → `scripts/export/build_authored_banks.py` (drops 249; the 3 S
    shortfalls need authored items) → `scripts/export/build_topic_tests.py`
13. `scripts/export/build_speaking_path.py` → `scripts/export/build_speaking_checkpoints.py` →
    `scripts/export/build_speaking_practice.py`
14. `scripts/export/build_capabilities.py` → `scripts/export/build_item_lesson_index.py`
15. `scripts/contracts/infer_shapes.py` → `scripts/contracts/build_schemas.py` → `scripts/contracts/build_manifest.py`
    → `scripts/export/build_review_views.py` → `(cd prototype && npm run sync-data)`
16. Gate: `scripts/validate/validate_all.py`. Then `validate_repairs_applied.py` needs a REGISTRY handler for the
    new table, and `research/derived/rebuild_manifest.json` a new step **after step 130** (the last
    `apply_orthographic_relinks.py`, which anchors on *unlinked* tokens and would claim the tokens this apply
    unlinks if it ran later) and **before step 131** (`apply_lesson_furigana.py`), ahead of every table that
    reads token links (135 lesson sentences, 137 card examples, 141 item refs).
17. Ratchets, only after the gate is green and only where they shrink: `validate_sentence_coverage.py --record`
    (n3 vocab 157→153 / 48→43), `validate_lesson_gating.py --write-baseline`, integrity ceiling in
    `integrity_audit.py`, `validate_exam_level_gate` baseline, then `validate_index_rebuildable.py --full`
    and `--record`.

## 6. Not measured

- The per-token Layer-B `gloss`/`role` of relinked tokens is not re-derived by any step above. Some glosses
  were written for the wrong sibling. That is a follow-up for a translation pass, not this apply.
- The 530 `review` rows, and the `apply_instead` variants of the 41 excluded rows.
- Re-running the builders themselves (exam, card, speaking) to see what they select *instead*. The numbers
  above are what the selection rules reject, not what replaces it.
- The 62 sentences the writer chain has added to the DB since HEAD. The snapshot integrity numbers include
  them, and they equal the bank numbers.
