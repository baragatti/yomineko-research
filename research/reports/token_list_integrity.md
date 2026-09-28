# Token-list integrity: word-by-word panel shows sub-tokens

Unit `token_list_integrity`, 2026-09-27. Findings only; nothing applied. Sweep data:
[`research/derived/pending/token_list_integrity_sweep.json`](../derived/pending/token_list_integrity_sweep.json).
Inputs: `corpus/sentences/bank.json` at git `529131bf`, plus a read-only backup of `db/corpus.sqlite`.

## 1. Symptom

For `sent:tatoeba-5078` 「おいくつですか？」 the prototype's "Palavra por palavra" panel shows
**いく / つ / お / いくつ / です / か**. It should show **お / いくつ / です / か**, with 「？」 dropped by the
panel's punctuation filter.

## 2. Root cause

The corpus data is correct. The export flattens two different things into one list, and no contract
or validator stops it.

| # | Where | What happens |
|---|---|---|
| 1 | `scripts/ingest/dissect.py:231-265` (`skeleton`) | The sentence is tokenized twice, in Sudachi mode C and mode A. Each A morpheme is attached to the C token whose character span contains it (`parent_position`). A morphemes identical to their parent are dropped. The C tokens get `begin`/`end` offsets, but these are never persisted. |
| 2 | `scripts/ingest/persist_dissection.py:131-137` | The A sub-units go into the **same `token` table** with `split_mode='A'`, `parent_token_id` = the parent's row, and `position` = **the parent's position**. So `position` means "index in the sentence" on a C row and "index of my parent" on an A row. |
| 3 | `scripts/export/export_corpus.py:671-689` | `SELECT … FROM token WHERE sentence_id=? ORDER BY split_mode, position` selects **both modes** and drops `parent_token_id`. Since `'A' < 'C'`, every sub-unit is emitted **before** all C tokens, carrying a duplicate `position` and `pos: null`. The only thing that tells them apart is `split_mode`. |
| 4 | `contracts/sentence.schema.json` `tokens.items` | `split_mode` is allowed to be `A|B|C` and nothing is `required`. The contract permits a mixed, unordered list. |
| 5 | prototype `scripts/sync-data.mjs:115` (`slimToken`) | Keeps `{s,r,ro,pos,gloss,role}` and **drops `split_mode`**, so the app can't filter the sub-units even if it tried. |
| 6 | prototype `app/ui/SentenceCards.tsx:16-33`, `app/lib/render-body.server.ts:139-160` | Both render the whole list in order, filtering only punctuation. `spacedRomaji` (`sync-data.mjs:106`) also joins the romaji of every row. |
| 7 | Gate | `validate_display_consistency.py` check 1 proves `concat(C surfaces) == jp` **in the DB**, and that holds everywhere. Nothing checks the **published** list, which is what consumers read. |

## 3. Sweep (all 10,271 bank sentences)

| Class | Sentences | Notes |
|---|---:|---|
| `rendered_subtokens`: `tokens[]` carries A rows | **903** | 1,938 A rows under 957 parents. Parents have 2 parts (936), 3 (19), 4 (1) or 5 (1). |
| `rendered_ne_c`: the panel differs from the C tokens | **903** | Same set. Every affected sentence is wrong in the panel. |
| `a_carries_payload`: an A row has romaji | 3 | 看護師 → 師 `shi` (`gen-01e31222a647`, `gen-358d6c011e6c`, `gen-c058146d69ad`). The prototype romaji line starts with a stray `shi`. |
| `c_concat_ne_jp`, `c_positions_gap`, `c_positions_dup`, `c_export_out_of_order`, `no_tokens` | 0 | The C layer tiles every sentence exactly. |
| `a_orphan`, `a_partial_cover`, `a_same_as_parent`, `a_export_order_ne_id` | 0 | Every A row links to the right parent, and the parts re-concatenate to it. |
| `particle_unanchored` (DB `particle.token_id`) | 0 | 24,771 particles. All are anchored in the DB, but the export drops the anchor (§4). |

Affected sentences by level: n5 29, n4 201, n3 364, n2 151, n1 158. The most common splits are
お金→お|金 (61), 私たち→私|たち (41), 日本語→日本|語 (38), 出かけ→出|かけ (24), 日曜日→日曜|日 (21) and
いくつ→いく|つ (10).

Two consumer-side effects outside the prototype:

- **Speaking validators disagree with the speaking builder on 59 seed hits.** The builders
  (`build_speaking_path.py`, `build_speaking_practice.py`) read the DB with `split_mode='C'`.
  `scripts/validate/speak_path_common.py:133` (`seed_hit`), used by `validate_speak_spiral.py`,
  `validate_speak_duplicates.py` and `validate_speak_strands.py`, builds its lemma set from **every**
  exported row. So 高さ→高い, 喫茶店→店 and 食べすぎる→食べる count as seed reappearances that the builder
  itself would never count. All 59 are listed in the sweep file.
- `scripts/derive_forward_refs.py:374` pairs adjacent `tokens[i], tokens[i+1]` (まし+た). The A rows come
  first, so the pair at the A/C boundary is not a real sentence neighbour. I found no false hit today,
  but it is latent.

## 4. Proposed structure (export contract)

The rule: `tokens[]` is the sentence, and nothing else is. Sub-units are nested under their parent. Every
unit carries its own offsets, so any consumer can check its slice against `jp`.

```json
"tokens": [
  {"position": 0, "split_mode": "C", "begin": 0, "end": 1, "surface": "お", "pos": "prefix", "...": "..."},
  {"position": 1, "split_mode": "C", "begin": 1, "end": 4, "surface": "いくつ", "vocab": "vocab:1219960", "...": "...",
   "parts": [
     {"begin": 1, "end": 3, "surface": "いく", "lemma": "いく", "reading": "いく", "pos_coarse": "名詞", "pos_fine": "数詞"},
     {"begin": 3, "end": 4, "surface": "つ",   "lemma": "つ",   "reading": "つ",   "pos_coarse": "接尾辞", "pos_fine": "名詞的"}]},
  {"position": 2, "split_mode": "C", "begin": 4, "end": 6, "surface": "です", "...": "..."},
  {"position": 3, "split_mode": "C", "begin": 6, "end": 7, "surface": "か", "...": "..."},
  {"position": 4, "split_mode": "C", "begin": 7, "end": 8, "surface": "？", "...": "..."}
],
"particles": [{"particle": "か", "token_position": 3, "function_type": "sentence-final", "...": "..."}]
```

Rules:

1. `tokens[]` contains **C units only**, in `position` order, with `position == list index`.
2. `begin`/`end` are **Unicode code-point** offsets into `jp`, half-open. Sudachi's `Morpheme.begin()/end()`
   are indices into the input text ([SudachiPy API](https://worksapplications.github.io/sudachi.rs/python/api/sudachipy.html),
   read 2026-09-27). No bank sentence contains a character outside the BMP (checked: 0), so JS UTF-16
   indices equal code points today. The validator should still fail on a non-BMP `jp` until a consumer
   needs one.
3. Tokens are contiguous: `begin[0] == 0`, `end[i] == begin[i+1]`, `end[last] == len(jp)`, and
   `jp[begin:end] == surface`. Together these give `concat == jp`.
4. `parts[]` is present only when the unit has ≥2 mode-A sub-units. The parts are contiguous and cover the
   parent exactly. A part carries only `surface, lemma, reading, pos_coarse, pos_fine, begin, end`: no
   `position`, `vocab`, `gloss`, `role` or `romaji`. That removes the 3 stray 師 romaji rows by
   construction. Parts are Layer A only. A part that ever needs a gloss becomes its own record, never a
   field on the part.
5. **Keep `split_mode: "C"` on every token for now, as a constant.** At least ten consumers filter with
   `t.get("split_mode") != "C"` or `== "A"`. Some of them skip every token when the field is missing:
   `derive_lesson_sentences.py:137`, `validate_lesson_gating.py:343`, `validate_speaking_path.py:184`,
   `derive_n3_review_furigana.py:87`, `derive_sentence_register.py:256`, `validate_repairs_applied.py:1632/1670/2291`.
   Removing the field would silently empty those checks. It can go in a later unit, once the filters are
   deleted.
6. `particles[]` gains `token_position`, taken from the DB `particle.token_id` (24,771 of 24,771 resolve,
   and the surfaces match). The export's particle `SELECT` (`export_corpus.py:691`) has no `ORDER BY`, so
   add `ORDER BY id`. This anchor is also what the particle-usage enum work needs: an exercise can then
   point at the exact particle occurrence in the sentence.

Split modes as documented upstream: A = shortest units (UniDic short unit), B = middle, C = longest /
named entities. The README example is 選挙/管理/委員/会 → 選挙/管理/委員会 → 選挙管理委員会
([Sudachi README](https://github.com/WorksApplications/Sudachi), read 2026-09-27).

### Producer changes

- `export_corpus.py:671-689`: select C rows `ORDER BY position`. Select A rows `ORDER BY id` and nest them
  under `parent_token_id`. Compute `begin`/`end` as cumulative surface lengths; this is safe because the C
  layer tiles `jp` in all 10,271 sentences, and the validator re-checks every slice. Compute part offsets
  cumulatively from the parent's `begin`. No DB migration is needed.
- `dissect.py:256-265` (hardening, optional): replace the second full A tokenization and span matching
  with `c_morph.split(SplitMode.A)`. A sub-unit that crosses a C boundary is then impossible by
  construction. Today the two-pass alignment silently drops such a unit. Checked on SudachiPy 0.6.11
  over the whole bank: `split(A)` gives **identical** parts in 10,271/10,271 sentences, and **0** A
  morphemes cross a C boundary. On 0.6.11, `split(A)` returns an empty list for an unsplittable
  morpheme (seen on お), so treat both "empty" and "length 1" as "no parts". `persist_dissection.py`
  does not change: it already writes `parent_token_id`.
- `contracts/sentence.schema.json` via `scripts/contracts/build_schemas.py:586`: narrow
  `sentence.tokens[].split_mode` to `["C"]`. Make `position, split_mode, begin, end, surface` required,
  add `parts` (item schema from rule 4, `additionalProperties: false`, `minItems: 2`), and make
  `particles[].token_position` required. Mention the change in `contracts/README.md`.

## 5. Hard validator: `scripts/validate/validate_token_list.py` (export side)

Reads `corpus/sentences/bank.json` under `--root`. Wire it into `validate_all.py` next to
`validate_display_consistency.py`.

| Check | Rule |
|---|---|
| T0 | floor: ≥ 5,000 sentences |
| T1 | every sentence has ≥ 1 token |
| T2 | `position == list index` for every token (catches swaps, drops, duplicates and interleaved sub-units) |
| T3 | offsets contiguous from 0 to `len(jp)`, and `jp[begin:end] == surface` (catches NFKC twins like ？/?) |
| T4 | no top-level token with `split_mode != "C"` (the bug in this report) |
| T5 | `parts`: ≥ 2, contiguous, cover the parent exactly, allowed keys only (no orphan, no single part equal to its parent, no payload) |
| T6 | every particle has `token_position` in range, and `tokens[token_position].surface == particle` |

**Plant proof (scratch prototype, not repo code).** The export was reshaped from the HEAD bank and DB
snapshot as in §4, then validated:

- current export: T4 fails on the 903 sentences. T3 and T6 fail everywhere, because offsets and anchors
  don't exist yet.
- proposed shape: **0 failures on 10,271 sentences**.
- 13 plants, **13 caught**, control green: an A row put back at top level (T4), two tokens swapped (T2),
  a token dropped (T2), a token duplicated (T2), ？→? (T3), `begin` off by one (T3), a part dropped (T5),
  a single part equal to its parent (T5), a part carrying `vocab` (T5), a particle anchored to the wrong
  token (T6), a particle with no anchor (T6), the bank cut to 10 (T0), and tokens emptied (T1).

The real validator must repeat these on a copied tree that carries a copy of the validator and of
`export_corpus.py`'s imports. Otherwise the plant reads the real repo and passes falsely.

## 6. Consumers

**Must change in code**

| Consumer | Change |
|---|---|
| `scripts/export/export_corpus.py:671-696` | producer (§4) |
| `contracts/sentence.schema.json`, `scripts/contracts/build_schemas.py:586` | contract (§4) |
| prototype `scripts/sync-data.mjs:115-121` | No change is needed for the fix: the list becomes C-only. To show sub-units, ship `parts` as `p: [{s,r}]` and `b`/`e` offsets. |
| prototype `app/lib/corpus.server.ts:135` (`BdToken`), `app/ui/SentenceCards.tsx:16-33`, `app/lib/render-body.server.ts:139-160` | Word panel. It's correct once the export is fixed. Optionally render `parts` as a sub-line under the parent (いくつ = いく + つ). Never render them as siblings. |
| `scripts/validate/validate_prototype_sync.py:205-247` (`_spaced_romaji`, `_slim_token`) | mirror whatever `slimToken` becomes |
| `scripts/export/build_exam_banks.py:454-468` (exam builder) | Reads the DB with both modes for the vocab dimension, and its comment claims this is "exactly as bank.json publishes them". Make it read C rows plus parts, or C only. A rows carry no vocab (0 of 1,938), so the output doesn't change. |

**Behaviour changes by themselves (re-run and diff)**

| Consumer | Expected change |
|---|---|
| `scripts/validate/speak_path_common.py:133` → `validate_speak_spiral.py`, `validate_speak_duplicates.py`, `validate_speak_strands.py` (speak validators) | −59 seed hits. They now agree with the builders, which already read C only. A spiral or strand check that only passed through a sub-unit lemma will fail, which is correct. |
| `scripts/derive_forward_refs.py:374` | adjacency only sees real neighbours. Expected diff: 0. |
| `scripts/validate/validate_practice_coverage.py:244`, `scripts/derive_needs.py:119` | concat / kanji set lose the duplicated sub-unit text. No verdict change is expected. |

**Unaffected** (these already filter C, or read only fields A rows never carry):
- `build_vocab_exercises.py:377/442` (exercises), `validate_card_content.py:158`, `derive_lesson_sentences.py:136`
- `validate_lesson_gating.py:342`, `validate_sentence_structure.py:65`, `validate_speaking_path.py:182/202`
- `validate_repairs_applied.py` (the at-position lookups at 831/1119 become unambiguous)
- `derive_sentence_register*.py`, `derive_n3_review_furigana.py`, `graph_queries.py`, `validate_graph_edges.py:552`, `validate_exam_level_gate.py:309`
- `build_item_lesson_index.py`, `build_topic_tests.py`, `build_authored_banks.py`, `validate_sentence_coverage.py`
- `review_queue.py:626` and `build_review_views.py:780`: A rows have no Layer-B, so dissection anchors don't change. The review ledger is empty (0 entries), so whole-record anchors going stale costs nothing today.
- DB-side builders that already query `split_mode='C'`: `build_speaking_path.py`, `build_speaking_practice.py`, `build_speaking_checkpoints.py`, `build_sentence_patterns.py`, and the exam-bank stem path (`toks_c`).
- Exercises, exam banks and the speaking course hold sentence **IDs** only, so no stored data changes. They only need the normal rebuild.

## 7. Recommendation and order

One writer unit:

1. `export_corpus.py` nests parts, adds offsets and `token_position`, and orders particles.
2. Contract regenerated from `build_schemas.py`.
3. New `validate_token_list.py`, plant-proved on a copied tree, wired into `validate_all.py`.
4. Re-export and commit the JSON.
5. Re-sync the prototype, update the `validate_prototype_sync.py` mirror, and diff the three speak validators (expect −59 hits).

The `dissect.py` `split(A)` hardening can ship in the same unit; it changes no data today. Keeping
`split_mode: "C"` constant is deliberate. Deleting it is a follow-up, after the ten C-filters are removed.
