# V1-W45: the published token list is the sentence (checkpoint)

**2026-09-27.** Mechanical, export-side only: no DB write, no repair table, no manifest step (the
index already stores everything; only the exporter's projection was wrong). Research and design:
[`token_list_integrity.md`](token_list_integrity.md). Owner standard: `design/product_notes.md`
("Word by word must match the sentence exactly").

## 1. What changed

| file | change |
|---|---|
| `scripts/export/export_corpus.py` | `tokens[]` = mode-C rows only, `ORDER BY position`, each with half-open code-point `begin`/`end` into `jp` (cumulative surface lengths). Mode-A rows (`ORDER BY id`) nest under `parent_token_id` as `parts[]` (only when ≥ 2), keys `surface, lemma, reading, pos_coarse, pos_fine, begin, end`. Particles: `ORDER BY id` and `token_position` from `particle.token_id`. `split_mode: "C"` kept as a constant. |
| `scripts/contracts/build_schemas.py` | `tokens[].split_mode` vocabulary narrowed to `["C"]`; declared (not measured) item shapes: `tokens[]` requires `begin, end, position, split_mode, surface`; `parts` `minItems: 2`, items require all seven keys, `additionalProperties: false`; `particles[]` requires `particle, token_position`. Part `pos_coarse`/`pos_fine` are plain strings (third-party analyzer output, like the token's). `contracts/README.md` states the rule. |
| `scripts/validate/validate_token_list.py` (new, hard) | T0-T6 of the research report on `corpus/sentences/bank.json`; also fails a non-BMP `jp`. Wired into `validate_all.py` after `validate_display_consistency.py`. |
| `scripts/export/build_exam_banks.py` | the vocab-dimension read is now `split_mode='C'` (it read both modes "as bank.json publishes them"). A rows carry no vocab, so no bank item changed. |
| `prototype/scripts/sync-data.mjs`, `scripts/validate/validate_prototype_sync.py` | `slimToken` ships sub-units as `p: [surface…]`; the Python mirror matches. New W45 check on the app's own `sentences.json`: every word list concatenates to `jp`, every `p` to its token. |
| `prototype/app/ui/SentenceCards.tsx`, `prototype/app/lib/render-body.server.ts`, `corpus.server.ts`, `styles/lesson.css` | Word-by-word panel renders every token in order (punctuation now included, without a reading line, so the list is exactly the sentence); sub-units show nested under their word (`いく + つ`), never as siblings. `BdToken` gains `p?: string[]`; the touched map is typed (no new `any`). |
| `scripts/validate/validate_repairs_applied.py` | `handle_en_backfill`: the table's `tokens[i]` locators were written in the pre-W45 frame (A rows first, the same order `apply_en_backfill.py` still uses in the DB), so the index shifts by the sentence's sub-unit count. Without it 974 rows failed (446 unresolved, 383 value mismatch, 145 not applied); with it all 26,365 pass. |

Skipped: the optional `dissect.py` `split(A)` hardening (changes no data today; the research
measured identical parts on 10,271/10,271); removing `split_mode` and the ~10 C-filters (a later unit).

## 2. Export, measured against HEAD's bank

- Every non-token field identical on 10,271 sentences; every C token identical apart from the two
  added keys; the 1,938 A rows reappear exactly as parts under 957 parents in 903 sentences; particle
  lists identical in order, plus `token_position` (24,771/24,771 anchored, T6 green).
- Tokens in `tokens[]`: 87,632 → 85,694. The three stray 師 `shi` romaji rows are gone by construction.
- **Word lists that do not reproduce the sentence: 903 → 0 of 10,271** (bank.json and the app's
  `prototype/app/data/sentences.json` both).
- Contracts: `sentence` schema and `_shapes.json`, `manifest.json` / `types.ts` hashes moved.

## 3. Validator plant proofs (copied trees)

- `validate_token_list.py` (validator copied alone into a fixture root; it imports nothing from
  `scripts/export`): control green, **13/13 caught**: A row back at top level (T4), two tokens swapped,
  a token dropped, a token duplicated (T2), ？→? and `begin` off by one (T3), a part dropped, a single
  part equal to its parent, a part carrying `vocab` (T5), a particle anchored to the wrong token and one
  with no anchor (T6), the bank cut to 10 (T0), tokens emptied (T1).
- `validate_prototype_sync.py` W45 check (validator + `contracts/`, `corpus/`, `course/`,
  `prototype/app/data/` copied): control green, 2/2 caught: a sub-unit put back as a sibling word, and
  sub-units that no longer spell their token (made consistent in bank and app data, so only the new
  check can see it).

## 4. Consumers

- **Speak validators** (`speak_path_common.seed_hit` over the export): seed hits over every bank
  sentence × stage seeds **3,907 → 3,848: −59, exactly the 59 the sweep listed**, 0 gained (shopping 7,
  eating 5, getting_around 4, lodging 9, about_you 3, time_plans 6, health 13, past_stories 11,
  opinions 1). Cause: those hits existed only through a sub-unit lemma (高さ→高い, 喫茶店→店,
  食べすぎる→食べる), which the builders never counted because they read `split_mode='C'`. No verdict
  moved: `validate_speak_spiral` / `_duplicates` / `_strands` / `validate_speaking_path` print the same
  tables as Q6 (0 FAIL; arrival still the 1/12 stage out of band; 17 say_now pairs).
- Exam banks rebuilt: no item changed. `corpus/exam_banks/INDEX.md` regenerates `n4_reading_comp` from 90
  to 91 items, a stale count the Q4 residue left (the committed bank already has 91).
- Review views re-rendered (`build_review_views.py --level n5,speak`): the build line on 8 views, and
  537 n5 sentence whole-record hashes (the records gained offsets). The ledger is empty, so no anchor
  goes stale.
- `derive_forward_refs.py` (a W21b campaign tool, not in the gate) was not re-run; its adjacency now
  only sees real neighbours, and the research found no false pair.
- Unaffected, as the research predicted: exercises, lesson gating, card content, graph queries, the
  DB-side builders.

## 5. Checks

- Rendered diff of `course/` against HEAD: **0 files** (no lesson, no `.md`).
- `infer_shapes → build_schemas → build_manifest`, `npm run sync-data` (sentences 10,271), prototype
  `typecheck` and `build` pass (both need `NODE_OPTIONS=--max-old-space-size=12288`; tsc runs out of
  the default heap on the synced data, independent of this change).
- `validate_all.py`: ALL HARD VALIDATORS PASS.
- Browser preview (`yomineko-ssr`, `/licao/les:n5-desu-wa-01`): `sent:tatoeba-5078` おいくつですか？
  renders **お / いくつ (いく + つ) / です / か / ？**, read back from the DOM and seen in a screenshot.

## 6. Full replay (checkpoint)

First run (113 s): the rebuild runs clean through every step; **0 new, 0 healed, 1 re-pinned**:
`corpus/sentences/bank.json`, whose rebuilt bytes moved with the new export shape (the replayed index
is unchanged). `--record` rewrote that one sha; its cause keeps `tr-untracked` and gains a dated
V1-W45 note. The other 578 entries are byte-identical (cause and sha). Second run after recording
(107 s): `[OK] 794 exported file(s) checked, 579 held by rebuild_baseline.json at the recorded bytes`.

## 7. Open

- Delete the ~10 `split_mode` filters, then the constant (follow-up unit).
- W46 can now anchor usage ids to an exact occurrence through `particles[].token_position`.
