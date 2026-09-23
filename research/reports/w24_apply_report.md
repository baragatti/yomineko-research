# W24 apply: capability kinds, can-do and the exam link

_C5-W24, 2026-09-23. Applies `research/derived/pending/w24_capabilities.json` +
`research/reports/w24_capabilities_report.md` (derived 2026-09-10 at `2626d20c`), re-derived on the
current tree (after W21b, W22 and the W18 bank regeneration). Not a checkpoint unit: gate + quick replay._

## 1. What landed

| | before | after |
|---|---:|---:|
| capabilities | 74 | **125** (grammar 72, vocabulary 44, script 3, exam-readiness 3, phonology 2, study-method 1) |
| lessons in `lesson_map.json` | 266 / 322 | **322 / 322** (caps per lesson: min 1, median 3, max 6) |
| `corpus/capabilities/exemptions.json` entries | 56 | **0** (same commit) |
| capabilities with `can_do` + `can_do_evidence` | 0 | **125** |
| verbatim objective quotes (`can_do_derived_from`) | 0 | **222** |
| capabilities with an `exam_link` | 0 | **118** (767 rows) |

The 74 shipped rows keep `id`, `level` and `grammar_keys` exactly (checked against HEAD); every HEAD
`lesson_map` entry keeps every capability it had. The one field that changed on a shipped row is
`cap:permission`'s name (section 4).

### Where things live

- **Authored half** (Layer C, `ai_generated`, `needs_review`): `research/derived/repairs/w24_capabilities.json`,
  125 rows `{id, kind, level, can_do, can_do_evidence, can_do_derived_from}` plus `name` on the 7 curated
  rows and `lessons` on the 4 curated-mapping rows (phonology x2, romaji, study-method). The pending file
  is removed; the table keeps its kinds, rules and a `rederived` note.
- **Derived half**: `scripts/export/build_capabilities.py` reads the table and derives vocabulary
  capabilities (R-VOCAB), exam-readiness (R-EXAM), `lessons` (inverse map) and `exam_link` from the DB
  and `corpus/exam_banks/`. It refuses to write anything when a derived capability has no authored row,
  an authored row derives nothing, kind/level disagree, a quote names a lesson the capability does not
  claim or is not a verbatim objective, or any lesson maps to nothing.
- **No DB write.** Capabilities are an export-side artifact, so there is no apply script and no
  `rebuild_manifest.json` step; the table is registered in `validate_repairs_applied.py`
  (`handle_w24_capabilities`: the exported registry carries every row's kind, level, can_do, evidence,
  quotes, curated name, and each curated lesson maps to the capability).
- **Contract**: `capability.schema.json` regenerated (kind, can_do, can_do_evidence,
  can_do_derived_from, lessons, exam_link; all required by measurement). Vocabularies registered in
  `build_schemas.py`: `kind` (design, `design/courseware_architecture.md` §5), `can_do_evidence`
  (design, `learning_science.md` R67), `exam_link[].section` (design, `exam_simulator.md` paper table),
  `exam_link[].via` (producer). The kind table is in `design/courseware_architecture.md` §5; R66 marked done.

## 2. Re-derivation delta (W21b / W22 moved unlocks after the 09-10 derivation)

Same 125 ids, names, kinds and levels as the proposal. **63 lessons' capability sets differ** from the
09-10 map, every one explained by an unlock move:

- `cap:kanji-recognition`: 24 lessons out, 23 in (kanji unlocks moved by W21b).
- grammar moves: `cap:i-adjectives` `les:n5-adjetivos-01` -> `les:n5-passado-03`; `cap:topic-subject`
  `n5-verbos-05` + `n5-particulas-lugar-01` -> `n5-verbos-01`; `cap:topic:n5-te-form` `-02` -> `-01`;
  `cap:questions` `n5-desu-wa-03` -> `-01`; `cap:comparison` `n5-conectando-05` -> `n5-convites-04`;
  additions to `cap:te-form` (2), `cap:copula` (1), `cap:adverbs-degree` (1), two topic buckets (1 each).
- vocabulary: `cap:vocab:<topic>` follows the FIRST lesson that unlocks the word (course order). Four
  caps gained a lesson (`n3-desejos`, `n4-experiencia`, `n4-oracoes-relativas`, `n5-adjetivos` x2),
  `n5-adjetivos` lost `n4-forma-simples-04` and `n5-verbos` lost `n4-dar-receber-03`.
- `cap:exam-readiness-n3` still covers only `les:n3-revisao-01`: W22's review -02/-03 are not authored.
  R-EXAM keys off the topic slug, so they join with no edit.

**Four quotes broke** (they named a lesson the capability no longer claims) and were re-derived in the table:
dropped `cap:topic-subject` <- `n5-verbos-05`, `n5-particulas-lugar-01`; `cap:i-adjectives` <-
`n5-adjetivos-01`; `cap:topic:n5-te-form` <- `n5-te-form-02`. Added `cap:topic-subject` <-
`n5-desu-wa-01` ("Usar a partícula は para marcar o tópico ..."). **`cap:i-adjectives` now has no quote**:
the one lesson that unlocks `gram:i-adjectives` (`les:n5-passado-03`) teaches ね / よ, not い-adjectives.
That is W21b residue (the unlock sits in a lesson whose objectives do not teach it; same for `ga` /
`ga-arimasu` / `ga-imasu` at `les:n5-verbos-01`), carried as an open item, not papered over with a
quote from a lesson the capability does not claim.

## 3. exam_link on the regenerated banks

Re-derived against the 40 banks W18 regenerated (5,141 items, was 6,081): **767 rows on 118
capabilities** (was 851). Item rule, in order: `grammar` -> owning capability; `vocab` -> `cap:vocab:<topic>`
(+ `cap:kanji-recognition` in kanji_reading / orthography); `reading` -> every capability of its
`gated_to_lesson`; else `sentence` -> `sentence_grammar` keys. Exam-readiness capabilities carry the
whole paper instead (`via: paper`, `items` = per-paper count; N5 12 sections, N4 13, N3 14).
3,185 items reach no capability (listening scripts carry no ref by design; the rest name words no lesson
unlocks).

Unassessed: `cap:kana-reading`, `cap:romaji-reading`, `cap:phonology-segments`, `cap:phonology-mora`,
`cap:study-method` (expected, the JLPT has no section) and two real gaps, unchanged from the proposal:
**`cap:vocab:pre-n5-saudacoes`** and **`cap:vocab:n4-kanji-exame`**.

Level-gate probe, re-measured: kanji_reading + orthography items whose `vocab` is a taught word
**72 / 1,953 = 3.7%** (was 26 / 2,373 = 1.1%); per bank n5 11/176 + 13/177, n4 12/400 + 15/400,
n3 8/400 + 13/400. The regeneration fixed the level ceiling, not attribution: 96% of the 文字・語彙 half
still tests words no lesson teaches (G3, W18 follow-up).

## 4. cap:permission

`temo-ii-desu` is listed in both `te-form` and `permission`; `setdefault` gives it to `te-form`, so
`cap:permission` owns only `to-ittemo-ii` (と言ってもいい). The proposal's minimal fix is applied: the name
is now "Atenuação com と言ってもいい" (the can_do already said so), grammar_keys unchanged. Moving
`temo-ii-desu` out of `te-form` changes two shipped capabilities' keys and stays an owner call.

## 5. Validator checks (a)-(e), plant-proved

`scripts/validate/validate_capabilities.py`: (a) kind in the enum; (b) can_do['pt-BR'] non-empty, no em
dash, evidence in the enum; (c) quotes resolve, belong to the capability's `lessons`, verbatim objective;
(d) every lesson is a key of lesson_map and `lessons` is exactly its inverse; (e) exam_link bank exists for
(level, section), section in the paper table, `via: paper` only on exam-readiness with a non-zero paper
count, items > 0. `validate_graph_edges.check_capability_coverage` is unchanged and now reads 0 exemptions.

Fixture tree with its own copies of the validator, `build_capabilities.py` and `dbtarget.py`
(plant-proof-root rule), `--db` at the real DB:

```
(A) clean fixture: rc 0 | validate_capabilities: 125 caps, 322 lessons, ALL OK
    kind missing / kind not in enum / can_do blank / can_do em dash / evidence not in enum /
    quote from an unclaimed lesson / objective not verbatim / lesson maps to nothing /
    lessons[] not inverse / bank missing / via=paper on a grammar cap / unknown section
(B) 12 / 12 plants caught (rc 1 each)
replay handler: can_do edited / curated lesson dropped / evidence flipped -> 3 / 3 FAIL
```

## 6. Gate

`python scripts/validate/validate_all.py`: **ALL HARD VALIDATORS PASS** (quick replay included;
`validate_capabilities` 125 caps / 322 lessons ALL OK, `validate_repairs_applied` 21,664 rows clean incl.
the 125 W24 rows). The first run failed only `validate_review_views` on the 8 views' build stamp
(`contracts/manifest.json` git_head moved); re-rendered with `build_review_views.py --level n5,speak`,
a one-line stamp diff per file. Lessons:
`git diff --stat -- course/` against HEAD is empty, so the rendered lesson text diff is empty; W24 touches
no lesson.

## 7. Open

- `cap:i-adjectives` quote + the W21b unlock/objective mismatch behind it (`i-adjectives` at
  `les:n5-passado-03`, `ga*` at `les:n5-verbos-01`): an objectives or unlock decision, not W24's.
- Two unassessed vocabulary capabilities (`pre-n5-saudacoes`, `n4-kanji-exame`).
- 3.7% attribution of the kanji/orthography banks: feed to the W18 level gate as a hard ratchet.
- `temo-ii-desu` ownership (owner call). All 125 can_do rows await teacher review (Layer C).
