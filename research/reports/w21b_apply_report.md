# W21b: forward references, applied (unit U2-W21b)

Status: **applied 2026-09-23.** Derivation `scripts/derive_forward_refs.py` (landed from the scratch
script, with the 2026-09-23 rulings), apply `scripts/apply_forward_refs.py`, table
`research/derived/repairs/w21b_forward_refs.json` (moved out of `pending/`; `rows` = the 276 moves,
`ledger` = all 670 decided uses, `u5_drills` = the drill work list). Manifest steps 112
(`--placement-only`) and 130 (full apply); every later step renumbered by one and the notes that
cite them updated; the three family builders are 131-133. Gate green; full replay in section 8.

## 1. The rulings, as applied

| ruling (APP_PLAN W21b, 2026-09-23) | what the code does |
|---|---|
| (1) a moved item's old exercise may stay behind as review | R3/R4 no longer block a move. An exercise whose only target in the old home is the item travels when it asks nothing the new home does not know (R4) and the old home keeps a rendered retrieval+production pair (R5); otherwise it stays as review. **Blocked rows 122 -> 0.** |
| (2) `gram:nasaru` is HELD | `HELD` in the derivation; its row is `C-hold/owner`. |
| (3) re-run homograph resolution after the apply | done, section 4. |
| (4) forward-reference ratchet in the gating validator, plant-proved | check **C5** in `validate_lesson_gating.py`, section 5. |

Three safeguards were added because earlier apply attempts broke real gates or the replay (each
caught before commit; the index was restored from a backup and the sources from HEAD, then
re-derived and re-applied):

- **R7**: an item that is its old home's LAST kanji/grammar/kana unlock does not move. A
  vocabulary-only lesson has no capability (`validate_graph_edges` capability_coverage failed for
  les:n5-numeros-tempo-04/05 when 大 / 日 left). 2 rows become rewrites.
- **Locked by a replayed step** (`C-hold/table`, 12 rows, 5 items): unlocks that a rebuild step
  writes or asserts at the current lesson. `homograph_rulings.json` unlock rows and `ref` rows that
  affect an unlock (何方/どちら 1189360), `lesson_ref_addresses.json` (1577100, 2846738, 1445150), and
  the six hardcoded adds of `apply_missing_homograph_unlocks.py` (彼/かれ 1483070: the replay re-added
  it at les:n4-oracoes-relativas-01). W20 exercises whose id is an `apply_id_remap` target stay put.
- **A slug at the new home for ambiguous headwords** (15 moves): a headword ref is re-resolved at
  the new home, and the resolver's `introducing_topic` tier reads a placement the rebuild does not
  reproduce (in a replay 年 at les:n5-numeros-tempo-02 went to its sibling ねん and the card-key step
  dropped its key). The new home gets the published slug, exact in every tier; it has no chip for
  the item (check B), so the sibling filter the slug feeds cannot re-point one of its chips. The
  `introducing_topic_id` re-placement runs early (step 112) for the same reason.

## 2. Counts (quoted before -> after, measured on the exported tree)

| | before | after |
|---|---:|---:|
| forward uses, **same topic** | 35 | **1** |
| forward uses, **same level** | 461 | **14** |
| forward uses, across levels (i+1 backlog, held) | 160 | 160 |
| forward edges same topic / same level / across | 28 / 431 / 160 | **1 / 14 / 160** |
| check D pairs over the i+1 budget | 148 | **25** |
| check D pairs with a new kanji / a new vocab | 304 / 227 | **164 / 39** |
| check D pairs above lesson level | 178 | 178 |
| cks keys that shrink (322 lessons x 6 kinds, fixture and index) | - | **0** |
| cks memberships gained (vocab / kanji / grammar) | - | 3,632 / 3,975 / 128 |
| `needs[]` rows | 758 | 760 (716 derived + 40 kana + 4 review chain) |
| prerequisite-less lessons held (C2) | 7 | **3** (ratchet 8 -> 3) |
| gating exemptions | 3 | 2 (les:n4-dar-receber-02 / 急行 resolved) |

Decisions over the 670 rows: move 493, hold 174 (161 cross-level, 12 table-locked, 1 owner), rewrite
3 (2 R7: 大 @ n5-desu-wa-03, 日 @ n5-numeros-tempo-03; 1 `conj:masendeshita`, no earlier user).

## 3. What moved

**276 items** (vocab 140, kanji 120, grammar 16), each with its SRS card (derived from the unlock)
and, for 140 vocab, its authored production key (`card_production_key` row and the tracked
`card_production_keys.json` row re-homed). 257 cross a topic boundary; `introducing_topic_id`
follows on 246 records. **81 exercises travelled** (75 of them W20 rows, re-homed in
`practice_kanji_exercises.json`); **156 stayed behind as review**. No move was partial or multi-hop.

**76 moved items have no drill in their new home** (vocab 49, kanji 17, grammar 10). They are the
U5 work list: `u5_drills` in the table and `pending_drills` in
`scripts/validate/practice_coverage_baseline.json`. The practice gate counts them absent, subtracts
them before the ceilings, and gates the list itself (an entry that gains a drill must be deleted;
the list may not pass its ceiling of 76). Ceilings after: n5 vocab 528 -> 461, n5 grammar 17 -> 16,
n4 vocab 586 -> 550, n3 vocab 1185 -> 1178, kanji 0 at every level. Absent in total 2,338 -> 2,303.

Grammar moves for owner eyes (the card now precedes its explanation by N lessons): ka 2, gp-30 6,
gp-31 5, ga 4, ga-arimasu 6, ga-imasu 6, gp-13 1, **naide 30**, i-adjectives 3, **temo-ii-desu 17**,
**deshou 31**, gp-26 1, hou-ga-ii 11, tte 1, tara-ii-desu-ka 1, n3-metta-ni-nai-2 3. Long legal
moves over 70 lessons: 新 +76, 好 +85, 合 +75, 分かる +75, vocab:1228560 +75, vocab:1352290 +73, 雪 +73.
All go to the first same-level lesson that already shows the item.

W15: 間 (-> n4-oracoes-relativas-03), 関する (-> n3-perspectiva-01), 対する (-> n3-limites-05) moved,
so their three held passages are now gate-clean; applying them is a separate step (open item). 読み
stays held (cross-level). W22: the 7 base forms and ました are confirmed at their gate-sound homes as
analytic rows; no `conj:` unlock was written (the W22 apply owns that).

## 4. Homograph re-resolution (ruling 3)

15 moved headwords are ambiguous (居る 人 何れ 位 先 年 時 下 上 後 日 間 音 字 君; 彼 is now held). After
the apply the whole course was re-exported and every resolved ref compared with HEAD:

- unlock differences: exactly the 276 moves (552 expected diffs, 0 unexpected, 0 missing);
- body chip refs: **0 resolution flips** across 322 lessons;
- `course/vocab_disambiguation_review.json`: 0 -> **1 row**, 君 @ les:n4-passiva-02 (body chip).
  It resolves to the SAME record as before (vocab:1247250 きみ), now by corpus frequency (71 vs 2)
  instead of the introducing-topic tier, because 君 is now introduced by n4-suposicao-03. A teacher
  confirms it; nothing changed for the learner.

## 5. The ratchets

`validate_lesson_gating.py` **C5** counts forward (lesson, item) uses and lesson->lesson edges by tier
with `derive_needs`' own channels, frozen in `research/reports/lesson_sentence_baseline.json` at
1 / 14 / 160 (uses and edges). Growth fails; a drop prints an advisory. Plant proof on a copied tree
(validator, `derive_needs.py`, `build_needs_table.py` and the registries copied): control clean; one
exercise `sentence_refs` plant per tier (the channel B and D do not read): **3/3 caught**.
The practice gate's `pending_drills` list: **3/3 caught** (dropped entry -> ceiling growth, stale
entry, list over its ceiling).

## 6. Lessons do not degrade (rendered diff against HEAD)

On the exporter's rendered view (`lesson-NN.md`) of all 322 lessons: header text 0 differences,
**body text 0 differences**, the `Introduz` line differs in 185 lessons (all touched by a move),
exercise blocks 2,463 before and after with an identical global multiset, 96 lessons whose exercise
list changed with 81 blocks out and 81 in (the 81 travelling exercises).

## 7. Side effects, all derived

Families rebuilt from the live ledger (the family builders run on the index; topic-bound
memberships follow the moves). Capabilities: gp-30/gp-31 fall into the desu-wa topic bucket. Review
views are ordered by the introducing lesson, so their diffs are large and mechanical.

## 8. Gate

Exporters (corpus, course, readings, capabilities, review views) -> contracts -> sync-data ->
`validate_all.py`: ALL HARD VALIDATORS PASS; `validate_repairs_applied` 18,839 rows clean + 21
checked skips, the new table 276/276.

Full `validate_index_rebuildable.py`: the replay runs every step clean (including 112 and 130) and
compares 790 exported files: 219 byte-identical (222 at HEAD), 571 held. 474 held files changed
bytes, all under their existing causes: lesson JSON differs from the commit only in
`cumulative_known_set` (268 lessons), `body` (15) and the eight re-chunked kanji-exame lessons'
`unlocks`/`srs`/`objectives`; no lesson differs in `exercises` or `needs`. Three `.md` files are new
to the baseline (n3 concessao-07, conjectura-07, relato-07): one replay of `build_readings.py` no
longer builds their second reading box, so the rebuilt view prints the box slug; cause key
`readings-accumulated`. Re-recorded with `--record`.

## 9. Open items

- U5: author one drill per `u5_drills` row (76), deleting each `pending_drills` entry as it lands.
- Apply the three W15 passages the moves freed (n4-oracoes-relativas-03, n3-perspectiva-01,
  n3-limites-05).
- Residue for authoring/re-selection: 14 same-level + 1 same-topic uses (12 table-locked rows need a
  homograph/address ruling first; 大 and 日 need a non-vocab unlock left in their lesson or a
  re-selected sentence); `conj:masendeshita` needs a verb-past lesson (W25).
- Owner glance: the 16 grammar moves above (naide +30, deshou +31, temo-ii-desu +17).
- `item_refs` on exercises (the plan row's other half) is not populated by this unit.
