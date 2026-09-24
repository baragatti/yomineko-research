# P3-yoon: the 66 yoon composite strokes landed (2026-09-23)

Mechanical (derived 66 / authored 0). This lands the verified table `research/derived/pending/yoon_strokes.json`
(66 rows, 66/66 ok; the verdict corrected 3 header fields: status, generated_by and license) as a tracked DB
writer. The verdict `pending/yoon_strokes.verdict.json` stays in pending/ as the audit trail. No rows were rejected.

## What changed

| Piece | Change |
|---|---|
| `research/derived/repairs/yoon_strokes.json` | Moved from pending/ (git mv). The verdict's corrected `generated_by` and `license` are folded in. `status` = APPLIED + the layer policy, with the verifier-corrected pre-apply status quoted after it. Rows are byte-identical to the verified ones. |
| `scripts/ingest/strokesvg_kana.py` (rebuild step 6) | After the 160 parsed rows and the っ/ッ derivation, `yoon_rows()` re-derives the 66 composites from the parsed rows: the base strokes and shadows, then the small ゃゅょ/ャュョ record translated +1024 x. Every composite must equal its table row before any row is written. On drift it refuses and writes nothing. The path tokenizer and `translate` moved here from `scripts/derive_yoon_strokes.py`, which now imports them and is marked FROZEN. No new manifest step, so no renumbering; step 6's note records the change. |
| Layer policy | **All 68 derived rows (っ/ッ + 66 yoon) = `B`; the 160 parsed rows stay `A`.** Reason: Layer A is dataset-only (spec §1.1), and none of these 68 glyphs is in the strokesvg dataset. They are deterministic transforms of Layer-A rows, with no AI, and are machine-checked against those rows. Before this unit, っ/ッ sat at `A` only because their INSERT left out `layer` and the column default filled it in. kana_stroke: A 160 / B 68 (was A 162). `layer` is not exported, so the JSON does not move for っ/ッ. |
| `research/derived/repairs/kana_cards.json` | The W29 table asserts `card_types` (in `apply_kana_cards.py` on replay and in `handle_kana_cards` in the gate). Its 66 yoon rows therefore now carry handwriting: `card_types`/`card_ids` +handwriting, `strokes: composite-landed`, `dropped_card_types: []`. Counts now read handwriting 145 -> 211 and glyphs without strokes 66 -> 0. In the migration, +66 minted handwriting ids, and handwriting retired without a successor goes 22 -> 0. An `amended` header records this. Production keys are unchanged. `apply_kana_cards.py` on the live index: 0 writes, 211 glyph cards issued, 0 orphans. |
| `scripts/validate/validate_repairs_applied.py` | `handle_yoon_strokes`: every row equals its `corpus/strokes/kana.json` record, all fields, addressed by char. Registered. |
| Exports | `corpus/strokes/kana.json` 162 -> 228 (the 162 existing records are unchanged; the +66 equal the table rows exactly). Also 4 pre-N5 lesson JSON files, contracts (`stroke_kana.schema.json`, `_shapes.json`, `manifest.json`), and prototype `app/data` (kanaStrokes 228). |
| Docs | ATTRIBUTION.md strokesvg "Ships" and design/sources.md now read 228 = 160 parsed + 68 derived (っ/ッ + 66 yoon composites). |

## Proofs

- Idempotent: `strokesvg_kana.py` run twice, table stays at 228 both times.
- Writer drift: a 1-unit shift of ょ's first stroke on an in-memory DB copy makes the writer refuse with
  `yoon きょ: composition != yoon_strokes.json row (component drift); nothing written`.
- Gate handler plant proof on a copied tree (validator + corpus/course/contracts/repairs copied): the control has 0 FAIL. The three plants each give exactly 1 FAIL on the planted row: record removed (きゃ), one shadow altered (ジョ), source altered (りょ). 3/3.

## Cards with handwriting, before / after

Before (HEAD 87310bda): kana cards 211, with handwriting 145, yoon 66 of which 0 with handwriting.
```
les:pre-n5-hiragana-14 {"deck": "deck:kana-hiragana", "item": "kana:hiragana-ちゃ", "card_types": ["recognition", "production"]}
les:pre-n5-hiragana-14 {"deck": "deck:kana-hiragana", "item": "kana:hiragana-ひゃ", "card_types": ["recognition", "production"]}
```
After: kana cards 211, with handwriting 211, yoon 66 of which 66 with handwriting.
```
les:pre-n5-hiragana-14 {"deck": "deck:kana-hiragana", "item": "kana:hiragana-ちゃ", "card_types": ["recognition", "production", "handwriting"]}
les:pre-n5-hiragana-14 {"deck": "deck:kana-hiragana", "item": "kana:hiragana-ひゃ", "card_types": ["recognition", "production", "handwriting"]}
```

## Lessons did not degrade (rendered diff of course/ against HEAD)

4 files, 0 `.md`: `course/pre-n5/topic-03-hiragana/lesson-14.json` (15 cards), `-15` (18),
`topic-04-katakana/lesson-14.json` (15) and `-15` (18). In each, the only top-level field that differs is `srs`, and inside it only `introduces_cards`. The only change is
`card_types` going from `[recognition, production]` to `[recognition, production, handwriting]` on the 66 yoon cards (asserted
per card). Every other card is byte-identical.

## Gate

`validate_all.py`: ALL HARD VALIDATORS PASS. `validate_repairs_applied` replays 79,027 rows clean (yoon_strokes 66/66) and the quick replay (`validate_index_rebuildable --quick`) is OK. The first run flagged only the 8 stale review views; their build-stamp line was re-rendered, and nothing else in them changed. Not a checkpoint, so the full replay was not run.

## Open

- The 11 ょ composites inherit ょ's off-cell lead-in sub-path. The per-sub-path shadow clip is part of the render contract (verdict note). An unclipped consumer would draw it across the base glyph.
- Inherited, not introduced here: み stroke 2 (and ぉ お ず ば ぱ ぼ ぽ む) has an empty shadow, so it draws unclipped.
- `corpus/strokes/INDEX.md` is exporter-generated and labels every count "kanji", kana included ("228 kanji"). This predates the unit and is left for a separate fix.
- Whether derived centerline data counts as OFL Font Software is still the owner's legal call (ATTRIBUTION.md).
