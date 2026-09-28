# Q4 — listening re-authoring and small residues applied

Chain v4 unit Q4 (not a checkpoint: gate + quick replay). Date 2026-09-27. Single DB writer.

## 1. What landed

| Part | Input (verified) | Applied | Held |
|---|---|---|---|
| Listening re-authoring (APP_PLAN W18b) | 175 items: 139 ok, 36 verifier-corrected, 0 rejected | 175 | 0 |
| Grammar residue drills (W20) | 19: 12 ok, 7 corrected | 15 | 4 (C5 forward refs) |
| item_refs residue (W23) | 21: 20 targets + 1 exemption, all ok | 19 targets + 1 exemption | 1 (stale) |
| Missing rc question (W18) | 1, corrected | 1 | 0 |

Only verified rows were applied; where the verdict was not ok, the verifier's corrected value was used.

## 2. Listening (W18b listening half)

* **Pairing.** Author batch `listening_authored-work-NN.json` goes with verdict `listening_authored-(NN-1).verdict.json`, as the verifiers noted. Every authored id has exactly one verdict (175/175). No row was rejected.
* **Table.** `scripts/apply_listening_reauthor.py --assemble` folds each author batch and its verdict into `research/derived/repairs/listening_reauthor.json`. Each row holds the journal item before (`old`) and after (`new`), the verdict, the problem text when one was corrected, `changed_tokens` and `source`. The nine author batches moved from `pending/` to `research/derived/repairs/listening_reauthor/` and are kept verbatim. The verdicts stay in `pending/`.
* **Apply.** The same script with no flag writes into the journal the builder reads (`research/derived/reauthor/exam_authored/authored_listen_<level>_<sub>.json`). An item already at `new` is left as done. An item at `old` is rewritten. An item at neither value is drift, and the script refuses it. A second run reports 175 already applied.
* **Banks.** `build_listening_bank.py` rebuilt the 13 banks. Item counts per bank are unchanged, 239 in total. Before the apply, a scratch rebuild matched the committed banks byte for byte, so every change comes from this table.
* **Level gate.** `validate_exam_level_gate.py` counts 0 inappropriate items in all 13 listening families. The ceilings in `scripts/validate/exam_level_baseline.json` went from 21/24/17/17/21/16/9/10/13/8/7/10/2 to 0. All 40 banks now sit at ceiling 0 (4,868 items). Check S (sufficiency) for listening is unchanged: n5 reply has 17 items, 2.8x a paper, marked THIN as an advisory.

### Reply ids: they follow the sentence slug

A reply item's id is `lr:<level>:<sentence slug>`, and the builder derives it. Six reply items were moved to a different real sentence. They now take that sentence's id, and the old id is gone from the banks. Two of the six are the ones the verifiers noted as keeping their old id while pointing at a new sentence.

| old id | new id | new prompt |
|---|---|---|
| lr:n5:tatoeba-11831595 | lr:n5:tatoeba-187375 | 何人の子どもがいますか。 |
| lr:n5:tatoeba-2063347 | lr:n5:tatoeba-182711 | 休みたいですか。 (verifier) |
| lr:n5:tatoeba-4789 | lr:n5:tatoeba-201153 | どうやって学校に来たの？ (verifier) |
| lr:n4:tatoeba-10059669 | lr:n4:tatoeba-137941 | 待ってあげる。 |
| lr:n4:tatoeba-173462 | lr:n4:tatoeba-3957479 | 考えさせてください。 (verifier: the author's pick was already a live N4 prompt) |
| lr:n4:tatoeba-2552450 | lr:n4:tatoeba-10914902 | さっき何かあった？ (verifier: the author's pick was a live N3 prompt) |

Each new prompt is the bank sentence verbatim, and its `{slug, jp}` was added to `input_listen_<level>_reply.json`, which the builder's verbatim check reads.

Two N4 replies were **edited**, because their Tatoeba sentence uses a form above N4. `lr:n4:tatoeba-10049455` used the 〜とく contraction; the edit spells out 〜ておく. `lr:n4:tatoeba-11270411`'s sentence carries the 〜っけ tag. Neither item cites a sentence any more. Both keep their id and record the sentence they came from in `adapted_from`. `build_listening_bank.py` now takes a reply journal row with `slug: null` + `id` + `adapted_from`: it skips the verbatim check and writes no `sentence`.

`course/item_lesson_index.json` was regenerated: the 6 new ids are placed and the 6 old ids are gone. The two edited replies cannot be placed, because a listening item is placed only through its sentence. The placement floor was re-recorded with its cause, 4,696 -> 4,695. Exam items went from 4,867 to 4,868 and unplaced items from 171 to 173.

## 3. Small residues

Source: `research/derived/repairs/small_residues/small_residues.json`, moved from pending and kept verbatim, plus its verdict in pending (41 checked, 33 ok, 8 corrected). `scripts/assemble_small_residues.py` folds the verified rows into the tables that already have apply steps:

### Drills: 15 applied, 4 held

* The table is `research/derived/repairs/practice_grammar_residue.json`, in the W20 row shape. It is applied by `apply_practice_exercises.py --table …` at **manifest step 155**; the families moved to 156-158. Each exercise carries its authored `item_refs`. The applier now writes them together with the exercise (`exercise_item_ref` + authoring source), because on a replay step 145 (`apply_item_refs.py`) runs before the exercise exists. Each drill gets exactly one body node. Every id was checked free and continues its lesson's numbering on today's tree.
* **Held (verified, not applied):** each of these four would grow `validate_lesson_gating` C5, a shrink-only ratchet. With them applied, same-level goes 10 -> 12 and cross-level 146 -> 148. The reason is that `derive_needs` reads a cited sentence's token links, and each cited sentence is linked to a record that a later lesson unlocks:
  * `ex:n5-perguntas-04-16`: sent:tatoeba-201561. Its し inside どうして is linked to 為る (vocab:1157170, les:n5-verbos-02). This is a link defect.
  * `ex:n5-particulas-lugar-07-9`: sent:gen-382544683343. もらい is linked to 貰う (vocab:1535910, les:n4-volitivo-05).
  * `ex:n5-te-form-05-13`: sent:tatoeba-184859. いけない is linked to the N3 行けない (vocab:1000730, les:n3-conectores-04). The link is arguably right, but the level of the record is inconsistent with N5 〜てはいけない.
  * `ex:n4-condicionais-08-10`: sent:gen-b249a5f48dc6. いか is linked to 以下 (vocab:1155060, les:n4-volitivo-04).
  They are listed in the table's `held` block. Two follow-ups are open: the v5 token-link unit (し, いけない) and an owner call on the level of 貰う / 以下.
* **Needs.** The drill `ex:n4-volitivo-01-23` cites sent:tatoeba-74772, whose 様 (よう) is unlocked in les:n4-oracoes-relativas-07. `build_needs_table.py` re-derived the table, and one lesson's edges moved: les:n4-volitivo-01 now needs -06 (歌) and -07 (様) instead of -04 (作) and -06. `apply_lesson_needs.py --replace` wrote the change to both layers (`repairs/lesson_needs.json`, 743 edges, unchanged count).
* **Practice coverage.** Grammar pairs absent went from 6 to 2: n5 4 -> 2 (the two left are the held N5 drills' pairs, どうして and 〜てはいけない), n4 2 -> 0. The ceilings were lowered with `--write-baseline`.

### item_refs: residue 20 -> 0

* The 19 target rows were added to `repairs/item_refs.json` with `derived_by: authored` and applied by `apply_item_refs.py`. `derive_item_refs.py` re-derives the whole table from the tree and reproduces it exactly (4,754 rows, 0 differences), because rule 0b reads the authored refs back from the source. The 15 applied drills' refs show up as `authored` rows the same way.
* The exemption `ex:pre-n5-katakana-01-2` covers course metalanguage about katakana. It went into `course/item_ref_exemptions.json` with `derived_by: authored`. `derive_item_refs.py` now keeps authored exemptions while the exercise has no target, instead of overwriting the file.
* **Held as stale:** `ex:n3-revisao-01-3`. P5 rewrote that exercise, and it already carries `gram:n3-ni-kanshite` (authored). The residue row described the old exercise.
* Residue went from 20 to 0, and `item_refs_baseline.json` is now `{}`. 25 exercises are exempt.

### rc question for read:n4-oracoes-relativas-03-01

The verifier-corrected row is appended to the W18b journal `rc_questions_w18b.json`. In the corrected version, three options share the passage's かもしれない, so a learner cannot find the key by string matching. `build_reading_comp_bank.py` accepts it under every guard (P1-P4, 0 skipped): rc n4 goes 90 -> 91 and the total 285 -> 286. The box's pointer is restored. The existing row in `repairs/reading_comprehension.json` has an amended `new`, and the old value is kept in `amended.was_new`. `apply_reading_comprehension.py` accepts that old value as a legitimate pre-state on the live index. All 286 reading boxes now ask a question, so `reading.schema.json` measures `comprehension` as required. The verifier's residual note still applies: かもしれない is outside the lesson's grammar set. Replacing the passage (W18b) remains the real fix.

## 4. Gates

* `validate_all.py`: **ALL HARD VALIDATORS PASS**, including the quick replay.
* `validate_repairs_applied.py` has 2 new registrations. `listening_reauthor.json` gets a new handler, `handle_listening_reauthor`: the shipped item must equal the row's journal item, and a renamed reply's old id must not ship. A plant proof on the real banks caught both plants: a changed key and a re-added old id each FAIL, and the file is clean again after restore. `practice_grammar_residue.json` uses the existing practice handler. Totals: 175/175, 15/15, item_refs 4,754/4,754, reading_comprehension 283/283.
* Downstream artifacts were regenerated from the tree: `course/item_lesson_index.json`, `course/topic_tests.json` (pool 13,118), `corpus/capabilities/registry.json` (exam_link follows the listening ids), the n5 and speak review views, contracts, and prototype data.
* Rendered lesson diff against HEAD: 13 `.md` files changed, **0 lines removed**, only the added drill blocks. The lesson JSON leaves also changed in `exercises[].item_refs` (the 19 residue exercises and the 15 drills) and in one lesson's `needs`.

## 5. Not done / open

* The 4 held drills (section 3) and the 2 remaining absent grammar pairs (n5 どうして, n5 〜てはいけない).
* `research/reports/review_queue.json/.md` still lists the 8 old listening ids. It was last regenerated on 2026-09-23 and is not maintained per unit.
* The two edited replies are unplaced. Placing a script-only listening item would need a new rule in `build_item_lesson_index.py`.
* Fable sample 30 on the applied rows is owed. Every row passed one independent verifier.
