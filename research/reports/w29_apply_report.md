# W29 (apply, C7 checkpoint) - kana cards, one glyph per card

Run 2026-09-23. Applies the W29 derivation (`research/reports/w29_kana_cards_report.md`, table now at
`research/derived/repairs/kana_cards.json`) under decision D6. Mechanical: derived 211 / authored 0.
The composite yoon stroke alternative (report §5, R2 note) was NOT taken here; the 66 yoon glyphs
ship with recognition + production only.

## 1. What changed

| | before | after |
|---|---:|---:|
| kana cards | 57 (family) | **211** (glyph) |
| kana card instances (card x kind) | 171 | **567** (211 reco + 211 prod + 145 handwriting) |
| kana production keys | 0 | **211** (`verified: "derived"`) |
| cards in the course | 4,136 | **4,290** |
| production keys in the course | 2,951 | **3,162** |
| lessons touched | | 30 pre-N5 (hiragana 15, katakana 15) |

The retirement map (`migration[]`, 57 rows) ships unchanged in the table: 57 family card ids retire,
567 glyph card ids start cold, `carry_fsrs_state: false`, `review_log_action: "orphan"`. 22 rows (the
11 yoon families per script) retire a handwriting card with no successor of that kind.

## 2. How (the five changes of the derivation report §5, plus one it could not foresee)

| # | where | change |
|---|---|---|
| R5 | `scripts/export/export_course.py::_srs_cards` | a `kana-family` unlock fans out to its member glyphs in `kana.ord` order; `card_types` = deck registry minus `handwriting` where `kana_stroke` has no row for the glyph. The family stays the unlock ref (no unlock ledger row moved: 4,175 unlocks before and after). `_production_keys` omits `sense_index` when NULL. |
| (apply) | `scripts/apply_kana_cards.py` (new, manifest step 136) | writes the 211 keys into `card_production_key` (migration 016, no new migration), keyed (lesson, glyph id), `why` = template name. Refuses if a row's glyph is not in a family its lesson unlocks, or if the row's `card_types` differ from the fan-out the exporter will build. Idempotent (second run: 0 writes). Kana orphans are its own; `apply_card_production_keys.py` now scopes its orphan check to non-kana items so re-running W27 on the live index stays clean (checked: 0 changes, 0 orphans). |
| R1 | `validate_card_content.py` check C | kana branch: a glyph key's form set is exactly `{char}`; a family record has no `char`, so a key on a family card fails. `UNKEYED_RATCHET["kana"]` 57 -> 0. |
| R2 | `validate_srs_decks.py` rule 2 | the registry list is the deck's maximum. Empty fails, a kind outside it fails, a missing kind fails unless it is exactly `handwriting` on a kana glyph with no record in `corpus/strokes/kana.json` (positive check, not an exemption list). |
| R3 | `validate_srs_decks.py` rule 5, `validate_unlock_ledger.py` check F | a glyph card is checked through its family (`corpus/kana/families.json`). Check F also gained a completeness test the derivation did not have: a family unlock whose glyph set is short by even one card fails. The duplicate test runs on glyph ids before projection. |
| R4 | `scripts/contracts/build_schemas.py` | `production_key.verified` enum `["sampled"]` -> `["sampled", "derived"]`, description names both; contracts regenerated (not hand-edited). `design/srs_design.md` §8 row and a §7.2 "applied" note. |
| R6 (new) | `validate_card_content.py` check F ratchet | W28 landed after the derivation and put kana 57 in `NO_EXAMPLE_RATCHET`. 211 glyph cards would read as a regression, but a kana card can never carry an example (check F rejects one), so kana is no longer counted in that ratchet rather than raising the number. |

Exact-match replay: `validate_repairs_applied.py` registers `kana_cards.json` with
`handle_kana_cards` (one card per row with the row's deck, kinds and key; the family card gone from
the lesson): 211 / 211 PASS.

## 3. Plant proof

Fixture: `corpus/`, `course/`, `design/`, `research/derived/repairs/` copied to the scratchpad with
the four validators copied in beside them (so ROOT is the fixture). Control on the fixture: decks 0
FAIL, content OK 4,290 cards / 3,162 keys, ledger ALL OK, `kana_cards.json` 211 PASS / 0 FAIL. Each
plant mutates one or two lesson files, runs one gate, and restores.

| plant | gate | verdict |
|---|---|---|
| drop handwriting from a glyph WITH strokes (あ) | decks | CAUGHT: "drops handwriting but corpus/strokes/kana.json has its stroke order" |
| drop recognition from a yoon card (ちゃ) | decks | CAUGHT: "drops ['handwriting', 'recognition'] with no reason the corpus can state" |
| empty card_types | decks | CAUGHT (2-card-types) |
| add a kind the registry lacks (cloze) | decks | CAUGHT (2-card-types) |
| a vocab card drops a kind | decks | CAUGHT: "drops ['production'] with no reason the corpus can state" |
| glyph card moved to a lesson that does not teach its family | decks | CAUGHT: "not among the lesson's unlocks (family kana:hiragana-a)" |
| same move, ledger view | ledger | CAUGHT: "kana family unlocked but glyph card(s) missing" |
| a made-up glyph id | decks | CAUGHT (4-resolve) |
| key accepts a different glyph (い for あ) | content | CAUGHT: "accepts neither the headword 'あ' nor the kana 'あ'" |
| key accepts the romaji | content | CAUGHT (check C) |
| key accepts the glyph plus an alien (ア) | content | CAUGHT: "accepts ['ア'], which is not a form of あ/あ" |
| empty prompt | content | CAUGHT |
| a new unkeyed kana production card | content | CAUGHT: "kana: 1 production card(s) with no answer key, ratchet is 0" |
| the family card comes back | content | CAUGHT (same ratchet) |
| a kana card carries an example | content | CAUGHT: "a kana card carries an example: a glyph, not a word" |
| a family unlock with no glyph card | ledger | CAUGHT (check F) |
| one glyph of five missing (お) | ledger | CAUGHT (check F, the new completeness test) |
| the same glyph carded twice | decks | CAUGHT (7-duplicate) |
| key prompt drifts from the table | repairs | CAUGHT: FAIL 1 value-mismatch |
| family card issued beside the glyphs | repairs | CAUGHT: FAIL 5 not-applied |

20 plants, 20 caught, 0 missed. (`--table` runs of the repairs gate always exit 2 by design, so
those two are judged by their FAIL count against the control's 0.)

## 4. Lessons did not degrade

Rendered diff of `course/` against HEAD: 30 files changed, all `course/pre-n5/topic-0{3,4}-*/lesson-*.json`,
**0 `.md`**. The only top-level field that differs is `srs` (30 / 30); every non-kana card in those
files is byte-identical; cards 57 -> 211, instances 171 -> 567. No body, unlock, need, exercise or
known set moved. Review views re-rendered: build stamp line only.

## 5. Gates

`validate_all.py` green (the first run flagged only the stale review-view build stamp, re-rendered).

**Full replay (checkpoint).** The rebuild runs every step clean, step 136 included. 790 files
compared: **0 new divergences, 0 healed, 251 held files whose rebuilt bytes moved**:

| files | cause |
|---:|---|
| 250 | touched only by C6-W28 (`dec85dc8`, step 135 `card_example`), which committed on the quick replay only; no other commit since the last full record (C4-W22) touches them |
| 1 | `course/pre-n5/topic-03-hiragana/lesson-15.json`, already held (course-identity), moved with W29 |

The other 29 pre-N5 lessons W29 rewrote are reproduced byte for byte by the rebuild, so the glyph
fan-out and the step 136 keys replay exactly. Not a replay break: `--record` re-pinned the 251
hashes, each cause keeps its `_causes` key and gains a dated re-pin note naming the unit.

**Replay side effect fixed.** C4-W22 reported that a replay rewrote the committed
`research/derived/vocab_repoint_ledger.json` (its `exam_banks` section dropped). The writer is
`scripts/migrate_vocab_repoint.py --apply` (manifest step 111): on a scratch DB it re-runs the
re-points against the already-migrated tree, finds nothing left in the exam banks, and overwrote the
ledger. Both ledger writes are now skipped off the live index (`LIVE_INDEX`, the flag the script
already computes). The file this unit's own replays had rewritten was restored to its committed
bytes, and the verification replay left it untouched.

## 6. Open

- Composite yoon strokes (66 glyphs, all decomposable into stroked components) would return
  handwriting to the yoon cards and make R2's allowance unused; a rendering decision plus a data
  write, not done here. D5 (retire handwriting until a widget exists) would make it moot.
- `を` is cued `wo` (the Layer-A registry value); whether the cue should mention the particle
  reading is a teacher call (derivation report §4).
- `hiragana-15` / `katakana-15` issue 19 and 20 new cards; `new_per_day = 10` spreads them over two
  days. A pacing note for the teacher review.
