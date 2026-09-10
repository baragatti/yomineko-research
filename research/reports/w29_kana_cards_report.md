# W29 (derivation) - kana cards, one glyph per card

Run 2026-09-10. **Derivation only.** This unit produces `research/derived/pending/kana_cards.json`
(211 rows + the 57-row retirement map) and this report. No lesson, contract, validator, exporter or
schema in the repo is edited here; every change the migration needs is written down in §5 as a
proposal for the apply unit, and each one is *proved* on a copied fixture tree in §3.

Decision of record: **D6, kana stays in FSRS, one glyph per card** (`research/reports/APP_PLAN.md`
§4; `design/srs_design.md` §7.2). The 57 family cards become 211 glyph cards. Per §7.2 item 3 this is
a **re-mint, not a rename**: no FSRS state crosses over.

Artifact: `research/derived/pending/kana_cards.json`, 377,623 bytes,
sha256 `d15aff23277f37b18c62d3f229c11f15fe2b20bb6903ef7170aceddcdc121dc0`.

---

## 1. What is on disk today

| measure | value |
|---|---:|
| kana families in `corpus/kana/families.json` | 57 (hiragana 28, katakana 29) |
| glyph records in `corpus/kana/{hiragana,katakana}.json` | 211 (105 + 106) |
| kana cards in `srs.introduces_cards[]` | **57**, one per family, over 30 pre-N5 lessons |
| card *instances* (card x kind) | 171 (57 x recognition/production/handwriting) |
| kana cards carrying a `production_key` | 0 (`UNKEYED_RATCHET["kana"] = 57`) |
| glyphs with stroke data in `corpus/strokes/kana.json` | **145 / 211** |
| glyphs without | **66**, exactly the yoon digraphs |

Checks run on the registry before deriving anything, all clean: every glyph belongs to **exactly one**
family (0 glyphs in two families), the family member list and the two glyph files name the same 211
ids with no drift, and every family is unlocked by exactly one lesson. So the "a glyph taught in two
lessons keeps the first" rule found **nothing to arbitrate**: `contested_families` is empty. The rule
is still implemented (lessons are read in course order, first writer wins) so that a future re-split
of a topic cannot silently double-file a glyph.

The defect this fixes, restated: one FSRS card carries up to five independent memory facts, so the
scheduler cannot tell which glyph the learner missed (`readiness/srs_fsrs.md` G6).

## 2. The derivation

One row per glyph. Nothing is authored per glyph; every field is a lookup or a template substitution
over Layer A, so the table is `layer: "B"`, `ai_generated: false`, `derived: true`.

**Issuing lesson.** The lesson whose *family card* covered the glyph, taken from family membership.
`kana:hiragana-き` therefore issues from `les:pre-n5-hiragana-02`, the lesson that unlocks
`kana:hiragana-ka`. Every one of the 211 resolved; `unresolved_families` is empty.

**`card_types`.** `recognition` and `production` on all 211. `handwriting` only where
`corpus/strokes/kana.json` holds the glyph: **145 yes, 66 no**. A handwriting card for a glyph with no
stroke record is precisely the "card that renders nothing" `validate_card_content` check A exists to
stop, so it is not minted. Each row records `strokes: "direct" | "composite"` and
`dropped_card_types`.

**`production_key`** in the W27 shape (`design/srs_design.md` §8), minus `sense_index`, which is
omitted because a kana record has no `senses[]` (the gate rejects any integer there). `accept` is the
single glyph. Four fixed pt-BR templates, one per glyph `type`:

| template | text | rows |
|---|---|---:|
| `sound` | `Escreva o {script} que se lê {romaji}` | 200 |
| `sound_disambiguated` | `Escreva o {script} que se lê {romaji} (o da família do {ROW})` | 8 |
| `sokuon` | `Escreva o {script} que marca a consoante dobrada (sokuon)` | 2 |
| `long-vowel` | `Escreva o sinal de {script} que alonga a vogal anterior (chouon)` | 1 |

`sound_disambiguated` exists because romaji is **not** a key inside a script: じ/ぢ both read `ji` and
ず/づ both read `zu`, and the same twice in katakana. Eight glyphs. Without the family suffix, two
cards would show the same cue and grade the other one's answer wrong. After it, **0 prompt collisions
inside a deck** (checked, `prompt_collisions` is empty). The three non-phonetic glyphs (っ, ッ, ー)
carry no romaji at all in the registry (`(geminada)`, `(alongamento)`), so they get their own
templates instead of a nonsense cue.

**Card ids** are the user-free tail of the composed key in `design/user_state.md` §2,
`{user_id}:{deck}:{item}:{kind}`. Each row carries `card_ids` per kind, e.g.
`deck:kana-hiragana:kana:hiragana-あ:recognition`. It still parses back deterministically: a glyph id
is two colon-separated segments and no glyph contains a colon, so the composed id is still exactly
seven segments.

**Counts.**

| | before | after |
|---|---:|---:|
| kana cards | 57 | **211** |
| card instances (card x kind) | 171 | **567** (211 reco + 211 prod + 145 handwriting) |
| kana production keys | 0 | **211** |
| total cards in the course | 4,136 | **4,290** |

Per-lesson (all 30 lessons; before/after):

| lesson | before | after | | lesson | before | after |
|---|---:|---:|---|---|---:|---:|
| pre-n5-hiragana-01 | 1 | 5 | | pre-n5-katakana-01 | 1 | 5 |
| pre-n5-hiragana-02 | 1 | 5 | | pre-n5-katakana-02 | 1 | 5 |
| pre-n5-hiragana-03 | 1 | 5 | | pre-n5-katakana-03 | 1 | 5 |
| pre-n5-hiragana-04 | 1 | 5 | | pre-n5-katakana-04 | 1 | 5 |
| pre-n5-hiragana-05 | 1 | 5 | | pre-n5-katakana-05 | 1 | 5 |
| pre-n5-hiragana-06 | 1 | 5 | | pre-n5-katakana-06 | 1 | 5 |
| pre-n5-hiragana-07 | 1 | 5 | | pre-n5-katakana-07 | 1 | 5 |
| pre-n5-hiragana-08 | 1 | 3 | | pre-n5-katakana-08 | 1 | 3 |
| pre-n5-hiragana-09 | 1 | 5 | | pre-n5-katakana-09 | 1 | 5 |
| pre-n5-hiragana-10 | 1 | 2 | | pre-n5-katakana-10 | 1 | 2 |
| pre-n5-hiragana-11 | 1 | 1 | | pre-n5-katakana-11 | 1 | 1 |
| pre-n5-hiragana-12 | 2 | 10 | | pre-n5-katakana-12 | 2 | 10 |
| pre-n5-hiragana-13 | 3 | 15 | | pre-n5-katakana-13 | 3 | 15 |
| pre-n5-hiragana-14 | 5 | 15 | | pre-n5-katakana-14 | 5 | 15 |
| pre-n5-hiragana-15 | 7 | 19 | | pre-n5-katakana-15 | 8 | 20 |
| | **57** | **211** | | | | |

The two heaviest lessons already were the heaviest: `hiragana-15` and `katakana-15` each teach seven
or eight families in one sitting. At one card per glyph they issue 19 and 20 new cards. That is a
pacing observation for the teacher review, not a blocker: at `new_per_day = 10`
(`design/unlock_enums.json#_deck_defaults`) those two lessons spill over two days, which is what the
cap is for.

**The migration map.** `migration[]`, one row per retired family card, carrying `retires_card_ids`
(the 171 old instance ids), `mints_items`, `mints_card_ids` (the 567 new ones), and, flatly,
`carry_fsrs_state: false` with `review_log_action: "orphan"`. That is `design/srs_design.md` §7.2
item 3 made machine-readable: a family card and a glyph card are different memory facts, so D/S/due
do not transfer, and `design/user_state.md` §3 item 2 keeps the log rows rather than deleting them
(the optimizer's training set is the only asset that cannot be regenerated). Because `card` is a
version-tagged cache replayable from `review_log`, the replay needs exactly this: which card_ids stop
existing, which appear cold, and the explicit instruction not to seed the new ones from the old
history.

**22 of the 57 rows carry `retired_kinds_with_no_successor: ["handwriting"]`** (the 11 yoon families
per script). Their handwriting card retires with no replacement of that kind, because none of their
66 glyphs has stroke data. That is the honest consequence of the rule above and it is recorded per
row rather than hidden in a count.

## 3. What the gates say

Simulated on a **copied tree** under the scratchpad (`corpus/`, `course/`, `design/`, `contracts/`,
plus the validators copied in beside them so they resolve ROOT to the fixture and not to the repo).
The DB was copied too and read only, to confirm the index side (§5 R5). The repo tree was never
written.

**Control (fixture unmodified):** `validate_card_content` OK 4,136 cards / 2,951 keys;
`validate_srs_decks` 0 FAIL; `validate_unlock_ledger` ALL OK.

**Migration applied, gates unchanged: 4 failure classes, 508 failures.**

| gate | rule | n | why |
|---|---|---:|---|
| `validate_card_content` | check C | 211 | a kana record has no `headword`, no `kana` and no `forms[]`, so every key "accepts neither the headword None nor the kana None" |
| `validate_srs_decks` | 5-not-unlocked | 211 | a glyph id is not an unlock ref, and by design never will be (`design/unlock_enums.json#_kana_ref_note`: glyph ids are "NOT independently unlockable") |
| `validate_srs_decks` | 2-card-types | 66 | rule 2 demands `card_types` be *exactly* the deck registry's list; the 66 yoon drop `handwriting` |
| `validate_unlock_ledger` | check F | 30 | `srs.introduces_cards` must mirror the item unlocks one for one |

None of the four is a defect in the derived table. Three of them are the same fact: **the gates assume
one card per unlock ref, and D6 breaks that assumption for kana only.** The fourth (check C) is a gate
that was written when no kana card had a key.

**With the four proposed changes of §5 applied to the fixture's validator copies:**

```
validate_card_content:  [OK] 4290 card(s) over 322 lesson(s); 3162 production key(s) checked
                        unkeyed kana 0 / ratchet 0
validate_srs_decks:     4290 cards over 322 lessons, 12 decks, 0 FAIL by rule {none}
validate_unlock_ledger: 322 lessons, 4140 unlocks, 4140 distinct refs, ALL OK
validate_contracts:     [OK ] lesson  322 records          (after R4, the `verified` enum widening)
```

Adjacent gates, same fixture, also green: `validate_stable_addresses` ALL OK,
`validate_lesson_gating` 0 FAIL, `audit_hygiene_all_locales` **0 FAIL** over 415,591 learner-facing
strings (so the 211 new pt-BR prompts pass the em dash / pt-PT / accent / mixed-script checks).

**Plant proof for the relaxations** (14 plants, each mutating one lesson file in the fixture, then
restored). A relaxed rule that no longer catches anything is worse than the failure it replaced, so
each proposed change was planted against:

| plant | gate | verdict |
|---|---|---|
| drop `handwriting` from a glyph that **has** stroke data | srs_decks | CAUGHT: "drops handwriting but corpus/strokes/kana.json has its stroke order" |
| drop `recognition` from a yoon card | srs_decks | CAUGHT: "drops ['handwriting', 'recognition'] with no reason the corpus can state" |
| empty `card_types` | srs_decks | CAUGHT |
| add a kind the registry lacks (`cloze`) | srs_decks | CAUGHT |
| a **vocab** card drops a kind | srs_decks | CAUGHT (the relaxation is kana-only) |
| glyph card in a lesson that does not teach its family | srs_decks | CAUGHT: "not among the lesson's unlocks (family kana:hiragana-ka)" |
| a made-up glyph id | srs_decks | CAUGHT (4-resolve) |
| key accepts a **different** glyph (`い` for あ) | card_content | CAUGHT (check C) |
| key accepts the romaji instead of the glyph | card_content | CAUGHT (check C) |
| key accepts the glyph **plus** an alien surface (`ア`) | card_content | CAUGHT: "accepts ['ア'], which is not a form of あ/あ" |
| empty prompt | card_content | CAUGHT |
| a NEW unkeyed kana production card | card_content | CAUGHT: "kana: 1 production card(s) with no answer key, ratchet is 0" |
| a family unlock with **no** glyph card | unlock_ledger | CAUGHT (check F) |
| the same glyph carded twice | srs_decks | CAUGHT (7-duplicate) |

14 plants, 14 caught, 0 missed.

## 4. Twenty sample cards

| # | lesson | item | card_types | prompt (pt-BR) | accept | strokes |
|---|---|---|---|---|---|---|
| 1 | hiragana-01 | `kana:hiragana-あ` | reco+prod+hand | Escreva o hiragana que se lê a | `あ` | direct |
| 2 | hiragana-02 | `kana:hiragana-か` | reco+prod+hand | Escreva o hiragana que se lê ka | `か` | direct |
| 3 | hiragana-03 | `kana:hiragana-し` | reco+prod+hand | Escreva o hiragana que se lê shi | `し` | direct |
| 4 | hiragana-04 | `kana:hiragana-つ` | reco+prod+hand | Escreva o hiragana que se lê tsu | `つ` | direct |
| 5 | hiragana-11 | `kana:hiragana-ん` | reco+prod+hand | Escreva o hiragana que se lê n | `ん` | direct |
| 6 | hiragana-10 | `kana:hiragana-を` | reco+prod+hand | Escreva o hiragana que se lê wo | `を` | direct |
| 7 | hiragana-12 | `kana:hiragana-じ` | reco+prod+hand | Escreva o hiragana que se lê ji (o da família do ZA) | `じ` | direct |
| 8 | hiragana-13 | `kana:hiragana-ぢ` | reco+prod+hand | Escreva o hiragana que se lê ji (o da família do DA) | `ぢ` | direct |
| 9 | hiragana-12 | `kana:hiragana-ず` | reco+prod+hand | Escreva o hiragana que se lê zu (o da família do ZA) | `ず` | direct |
| 10 | hiragana-13 | `kana:hiragana-づ` | reco+prod+hand | Escreva o hiragana que se lê zu (o da família do DA) | `づ` | direct |
| 11 | hiragana-13 | `kana:hiragana-ぱ` | reco+prod+hand | Escreva o hiragana que se lê pa | `ぱ` | direct |
| 12 | hiragana-14 | `kana:hiragana-きゃ` | reco+prod | Escreva o hiragana que se lê kya | `きゃ` | composite |
| 13 | hiragana-15 | `kana:hiragana-じゅ` | reco+prod | Escreva o hiragana que se lê ju | `じゅ` | composite |
| 14 | hiragana-15 | `kana:hiragana-っ` | reco+prod+hand | Escreva o hiragana que marca a consoante dobrada (sokuon) | `っ` | direct |
| 15 | katakana-01 | `kana:katakana-ア` | reco+prod+hand | Escreva o katakana que se lê a | `ア` | direct |
| 16 | katakana-04 | `kana:katakana-ツ` | reco+prod+hand | Escreva o katakana que se lê tsu | `ツ` | direct |
| 17 | katakana-10 | `kana:katakana-ヲ` | reco+prod+hand | Escreva o katakana que se lê wo | `ヲ` | direct |
| 18 | katakana-12 | `kana:katakana-ジ` | reco+prod+hand | Escreva o katakana que se lê ji (o da família do ZA) | `ジ` | direct |
| 19 | katakana-15 | `kana:katakana-ー` | reco+prod+hand | Escreva o sinal de katakana que alonga a vogal anterior (chouon) | `ー` | direct |
| 20 | katakana-15 | `kana:katakana-ピョ` | reco+prod | Escreva o katakana que se lê pyo | `ピョ` | composite |

Rows 7 to 10 are the whole point of `sound_disambiguated`; rows 12, 13 and 20 are the yoon that lose
their handwriting card; rows 14 and 19 are the three glyphs with no romaji.

One thing for the teacher, flagged not decided: sample 6, `を`, is cued as `wo` because that is what
the Layer-A registry stores. Brazilian learners meet it as the particle read `o`. The registry value
is a fact and stays; whether the *cue* should say `wo (partícula, lê-se "o")` is a pedagogy call, and
it is a one-row template exception if the answer is yes.

## 5. What the apply unit must change

Five changes. None is in this unit's scope, all five are proved on the fixture, and none loosens a
rule outside kana.

**R1. `scripts/validate/validate_card_content.py`, check C: a kana branch.** A kana record carries no
`headword`, no `kana` and no `forms[]`. Its name **is** its glyph, and that single surface is the only
thing a grader may take. For `ns == "kana"`, set `forms = {rec["char"]}` and treat `char` as both
headword and kana. A *family* record has no `char` at all, so a key on one gets an empty form set and
fails, which is the right answer: a family card is exactly what W29 retires. Also
`UNKEYED_RATCHET["kana"]: 57 -> 0` (the ratchet may only shrink, so this is a tightening).

**R2. `scripts/validate/validate_srs_decks.py`, rule 2: registry list is the deck's MAXIMUM.** Today
`set(ctypes) != want` fails. Change to: empty fails; a kind **outside** the registry list fails; a
missing kind fails **unless** it is exactly `["handwriting"]` on a `kana` deck **and**
`corpus/strokes/kana.json` has no record for that glyph. The check is positive, not an exemption
list: dropping handwriting from a glyph that *does* have strokes still fails. Proved by three plants.

> **Alternative that removes R2 entirely, and is probably the better answer.** All 66 yoon decompose
> into two glyphs that **both already have stroke data** in `corpus/strokes/kana.json` (きゃ = き + ゃ;
> the small kana ぁぃぅぇぉ ゃゅょ ァィゥェォ ャュョ are all present and are the 17 stroke records the
> file holds that no glyph id claims). Verified for all 66, no gaps. If the apply unit lands composite
> stroke records for them, every glyph keeps all three kinds, rule 2 needs no change, `readiness/srs_fsrs.md`
> §4.4 closes, and the 22 orphaned handwriting retirements in `migration[]` disappear. The work is not
> a concatenation, though: the small kana needs a scale-and-offset transform to sit bottom-right of the
> base glyph, so it is a rendering decision plus a data write, which is why W29 derived the table the
> brief asked for and recorded this instead of assuming it.

**R3. `validate_srs_decks` rule 5 and `validate_unlock_ledger` check F: project a glyph onto its
family.** `design/unlock_enums.json#_kana_ref_note` already states that glyph ids are "NOT
independently unlockable. Only families are unlock/need refs." So the fix is not to add 211 unlocks
(that would move the 4,140-row unlock ledger and every `cumulative_known_set`); it is to check the
glyph's **family** against `unlocks[].ref`. The rule's intent, a lesson may not schedule review for
material it does not teach, is preserved exactly: the lesson does teach the glyph, it just does not
address it. Check F compares the same way, after projection, and its duplicate check skips the
fanned-out family ids. Both keep catching a glyph card filed in the wrong lesson and a family unlock
with no card (plants above).

**R4. `scripts/contracts/build_schemas.py`: widen `production_key.verified`.** The generated contract
pins the enum to `["sampled"]` and the field description says the key is "Authored, never derived".
W29's keys are neither: they are a deterministic template substitution over Layer A, with no author
and no sample. Add `"derived"` to the enum and amend the description to name the two ways a key can
be checked. Without it, `validate_contracts` reports 30 invalid lessons. Do it in `build_schemas.py`
and regenerate, not in `contracts/lesson.schema.json` directly, or
`validate_schema_generation_is_current.py` will fire. Calling them `"sampled"` instead would be a
false provenance claim and is not an option.

**R5. `scripts/export/export_course.py::_srs_cards`: fan a `kana-family` unlock out to its glyphs.**
This is where the card set is actually built, so nothing lands until it changes. The index already
holds everything needed and needs **no migration**: `kana(id, char, family_id, ord)` has all 211 rows,
`kana_stroke(char)` joins 145 of them, and `card_production_key(lesson_id, item TEXT, ...)` from
migration 016 takes a glyph id as `item` unchanged (211 new rows beside the existing 2,951). For a
`kana-family` unlock, emit one card per member glyph in `ord` order, `card_types` from the deck
registry minus `handwriting` where the `kana_stroke` join misses, and attach the key by
`(lesson_id, glyph_id)`.

**Ordering note.** R5 without R1 to R4 turns the gate suite red; R1 to R4 without R5 change nothing
observable. They are one commit.

**Not in scope here, but adjacent.** D5 (`APP_PLAN` §4) defaults to retiring the 691 handwriting
cards until a widget exists. If D5 is executed before or after W29, it removes the `handwriting` kind
from both kana decks in the registry, at which point R2 and the composite-stroke alternative both
become moot and the 211 cards carry two kinds each. W29 is written so that either order works: the
`handwriting` decision lives in the deck registry, and the table's `strokes` / `dropped_card_types`
fields record the evidence either way.
