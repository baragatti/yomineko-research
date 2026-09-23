# W32 + W30 apply: survival cores (partial) and speak-path SRS cards

**Unit C9-W32W30, 2026-09-23.** Inputs: `research/derived/pending/speak_survival_cores.json` (W32, 71
rows) and `research/reports/w32_authoring_report.md`. No DB write, no manifest step: the ingest this
unit was meant to run is blocked by Layer-B residue (section 1), and everything that did land is builder
code, validators, design text and the rebuilt `course/speak/`.

| | before (HEAD) | after |
|---|---|---|
| stages with a live survival core (R87) | 1 (`shopping`) | **9** |
| stages whose opening unit carries a survival phrase | 1 | **9 / 9 declared** (hard gate) |
| W32 sentences banked | 9 of 71 (7 selected + 2 the W13 ingest banked since) | 9 (ingest blocked, 62 listed) |
| `deck:phrases` cards | 0 | **432** (every say_now phrase, 72 units) |
| lesson files changed under `course/` | | **0** |

## 1. The ingest: derived, not ingestable, residue listed

`scripts/derive_w32_layerb.py` runs the W13b mechanical-first derivation over the rows the bank does not
hold: `derive_layerb_extra.Bank` for glosses (bank modal, then registry sense 0), the numeral rule, the
W13b verified rulings reused by `(lemma, pos)` from `research/derived/mined_layerb_n3/` (a pair an
independent verifier already ruled is not re-ruled), `derive_layerb_templates_v2` for particle function
and explanation (the repaired v2 rules). Output: `research/derived/pending/w32_layerb_derived.json`,
in the shape `ingest_mined_stages.py` reads, with a `residue` list per sentence.

| | count |
|---|---|
| rows in the table | 71 |
| already banked (skipped) | 9 (7 bank selections; `tatoeba-5060` and `tatoeba-1039551` arrived with the W13 N3 ingest) |
| derived | 62 (61 mined + 1 generated, 薬をください) |
| content tokens glossed | 158: 120 by a reused verified ruling, 29 unique-accept, **9 ambiguous-verify** |
| particles | 96: 71 templated, **25 need an authored explanation** |
| structure paragraph | **62 of 62 residue** (never derived: 10,209 distinct paragraphs, no precedent) |
| `translation_literal` | **62 of 62 residue** (the W32 table carries `pt` only) |
| ingest-ready | **0** |

Every bank sentence is `dissection_tier: "full"`, and `validate.py` reads that as a hard promise of a
gloss on every content token, an explanation on every particle, a literal translation and a structure
paragraph. A row with any residue fails the gate, so no row was ingested and nothing was authored. The
authoring pass needs: 62 structure paragraphs, 62 literal translations, 25 particle explanations and 9
gloss rulings, then `ingest_mined_stages.py --source <rows> --layerb <dir> --tag survival-core` with
the register table extended (below).

**Register re-check against today's filter.** `derive_sentence_register_v2.py --w13-source` over the
62 rows (scratch output, the tracked table untouched) plus the stored value for the 9 banked:
**71 / 71 agree with the W32 table** (66 polite, 5 neutral) and **71 / 71 pass `speak_filter`**
(register, `polite-request-nasai` rule, blocklist). The values are in `register_check` of the derived
file, so the ingest can read them.

## 2. R87: which terms went live, and why not all 71

A term goes live in `SURVIVAL_SEEDS` only when its **own** sentence is banked, because a term without
its row promotes whatever else carries it. Measured with all 71 terms live on today's index:
near-duplicate pairs 24 -> 35 (real_talk 1 -> 8 on `みたいですね` / `らしいですね` look-alikes), the R83
spiral shrank in 9 places, 24 R78 strand ratchets moved the wrong way, and `real_talk` came out with 0
units (its opening picks taught no new word and hit the exhaustion break).

Live now (9 stages): `shopping` unchanged (8 terms), `eating` お水をください, `getting_around`
どのくらいかかり, `about_you` ご出身は, `time_plans` は火曜日です, `health` 助けてください, `politeness`
お願いできますか, `opinions` ないと思います, `real_talk` ながら話し + ばよかったのに. Four of them needed
the W32 `seeds` extension to be candidates at all (は火曜日です, お願いできますか, ないと思います,
ばよかったのに), and they carry it. `arrival`, `lodging`, `past_stories` have no banked row: their
cores wait for the ingest.

Two builder changes came with it, both in `scripts/export/build_speaking_path.py`:

- **One phrase per survival term per stage.** Once a phrase carrying a term is placed, later sentences
  with the same term rank like anything else. Without it `ながら話し` placed お茶を飲みながら話しましょう
  next to お茶を飲みながら話しませんか in real_talk-01.
- **A survival phrase is not padding.** A late stage can open on survival phrases built from known
  words only; the exhaustion break no longer fires on them. `validate_speaking_path.py`'s padding rule
  accepts them for the same reason.

Two authored terms cannot fire under the builder's matcher and are recorded for the ingest, not changed
in the table: `今何時` and `お勘定` are 3 characters (lemma match only) and Sudachi splits them
(今|何時, お|勘定); `今何時か` and the lemma `勘定` reach their rows.

**The gate** (`validate_speaking_path.py`, hard): each stage publishes `survival_core` in
`course/speak/course.json`; a stage with no core fails unless it is in `SURVIVAL_CORE_PENDING`
(`arrival`, `lodging`, `past_stories`; a listed stage that gains a core also fails, so the list only
shrinks); every declared core must have a phrase in the stage's opening unit. Today 9 / 9, every one of
them with the W32 row itself in unit 01 (お水をください。, バスでどのくらいかかりますか。,
ご出身はどちらですか。, 明後日は火曜日です。, 助けてください。, 予約をお願いできますか。,
彼は来ないと思います。, 電話すればよかったのに。 + 歩きながら話しましょう。; shopping keeps いくらですか？).

## 3. W30: deck:phrases

Each unit gets `srs.introduces_cards`, the lesson shape: `{deck: "deck:phrases", item: sent:…,
card_types: ["production"]}` for every say_now phrase with a pt-BR translation (all 432 have one).
`listening` is left out while the unit's `audio` is `"pending"`: a listening card with no recording
renders nothing (the same reasoning as W29's handwriting on stroke-less kana). `introduced_by` for these
cards is the `speak:` unit id; `contracts/user_state/card.schema.json` and `design/user_state.md` now
accept it. `validate_srs_decks.py` reads the speak units too: rule 5 checks against say_now, rule 2
allows the missing `listening` only while audio is pending, rule 7 forbids one sentence carded twice on
the path, new rule 8 requires a card for every translated phrase. 4,290 -> 4,722 cards, 0 FAIL.

## 4. Speak ratchets, quoted

The committed path predated the W13 ingest (bank 5,889 -> 10,209): 71 of 72 units differ from what the
HEAD builder produces on today's index. So the rebuild carries two effects, measured apart (HEAD builder
on today's index = "drift only"):

| gate | HEAD export | drift only | this unit |
|---|---|---|---|
| near-duplicate pairs (R86 / §6b) | 24 | 26, 4 FAIL | **21**, 3 FAIL before re-record |
| spiral R83 FAILs | 0 | 13 | **12** before re-record |
| strand R78 FAILs | 0 | 28 | **25** before re-record |
| speak_path FAILs | 0 | 9 (no core declared) | **0** |
| checkpoint items | 364 | 331 | 329 |
| vocab introduced | 580 | 706 | 700 |

Near-duplicates per stage after: arrival 16, shopping 1, health 1, politeness 1, opinions 1, real_talk 1
(before: arrival 14, shopping 4, eating/getting_around/time_plans/health/past_stories/real_talk 1).
Spiral reach (say_now / fluency / drills / late units): arrival 2/1/16/16 -> 1/0/8/6, shopping
12/9/39/28 -> 14/20/38/29, eating 5/8/20/21 -> 2/5/4/8, getting_around 4/5/10/13 -> 4/4/10/13, lodging
3/1/1/4 -> 2/0/1/3, about_you 3/12/11/13 -> 6/18/8/16. Strands: 12 / 12 stages still out of band, worst
distance per stage 25.2 to 34.6 before, 26.7 to 34.6 after. All three ratchets were re-recorded with a
`w32_cause` key (the strand file keeps `w18_cause`).

Phrase churn: 205 of 432 say_now phrases changed; 207 change with the HEAD builder alone. 170 of the
432 now come from the W13 N3-exemplification set, which the path had never been rebuilt against (174
with the HEAD builder). That is a finding for the owner, not something this unit changed: the speak
builder does not distinguish them. `あれはキジです` (§5's pheasant) is still in `speak:shopping-03`.

## 5. Checks

- Plants, 7 / 7 caught: core removed, pending stage gaining a core, a core that never reaches unit 1,
  a phrase card dropped, a card for a phrase the unit does not teach, `listening` dropped with audio
  present, one phrase carded in two units. Tree restored byte for byte.
- One fix the rebuild forced: `kanji_recognition` listed 鞄, 喧 and 嘩 (from W13 sentences), which the
  export does not carry (only the 2,131 levelled kanji are exported), and `validate_graph_edges` failed
  on them. The builder now draws recognition kanji from levelled kanji only.
- Rendered diff of `course/`: **0 files outside `course/speak/`**; inside it, only speak units,
  course.json and INDEX.md.
- Exporters re-run (no diff), contracts regenerated, prototype synced, `validate_all.py` green with the
  quick replay.

## 6. Open

- **W32 authoring residue** (62 paragraphs, 62 literals, 25 particle explanations, 9 rulings), then the
  ingest, then the remaining 62 terms and 16 seed extensions go live and `SURVIVAL_CORE_PENDING`
  empties.
- The 8 blocked frames stay blocked on missing vocab records (救急車, チェックイン, アレルギー, 日本語,
  迷う, パスワード, おすすめ, ベジタリアン); unchanged from the authoring report §1.
- `今何時` / `お勘定` need the 4-character / lemma spelling when they go live.
- Speak path vs the N3 exemplification set: 170 phrases (owner call whether the path should draw on it).
- `listening` phrase cards wait for audio (W35 / G7).
