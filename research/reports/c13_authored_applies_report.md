# C13: authored lesson-body applies (W08b bodies, W21b rewrites, furigana residue)

**Unit C13-authored-applies, 2026-09-23. Not a checkpoint: gate + quick replay.** Input: the three
verified tables of the parallel authoring workflow (commit 028b1cfd), each with its verdict:

| table (pending -> repairs) | verdict | applied | held |
|---|---|---|---|
| `w08b_lesson_bodies.json` | 18 checked: 16 ok, 2 corrected | 18 rows, 18 spans, 8 lessons | 0 |
| `w21b_rewrites.json` | 15 checked: 10 ok, 1 corrected, 4 rejected | 10 rows, 11 spans + 8 exercise cites, 10 lessons | 5 (4 rejected, 1 stale) |
| `furigana_residue.json` | 217 checked: 207 ok, 9 corrected, 1 rejected | 216 rows, 263 spans, 106 lessons | 1 (rejected) |

All three tables existed with their verdict files; none was skipped. Mechanical apply: nothing
authored in this unit.

## 1. How the tables were folded

A scratch assembler (script, not agent) read each pending table + verdict, keyed the verdicts by the
row's stable identity (`lesson|old_span`, `lesson|span`), kept ok rows, substituted the verifier's
`corrected` text, and put rejected rows under `held` (never applied, kept with the verifier's
problem). Every row became `{lesson, spans: [{from, to, count}], ...}`; the authored text of a
corrected row stays beside it (`authored_to` / `authored_reading`). The whole set was simulated in
manifest order (W08b, then W21b, then furigana) on BOTH layers before anything was written: every
span occurred exactly `count` times at its turn. The pending tables were removed (`git rm`); their
verdict files stay in `pending/` as the audit trail, as with `w08b_merges.json` in C12.

Two furigana rows need a reading per occurrence (何 in n4-condicionais-08: なに, なん; 人 in
n5-numeros-tempo-02: にん, ひと). Each occurrence became its own span, extended rightwards from the
bare `<jp>` until unique in the body, so the apply stays a literal exact-match replace.

## 2. What was held, and why

W21b (5 rows, the C5 residue they leave is 4 same-level uses):

| lesson | item | why held |
|---|---|---|
| les:n5-desu-wa-03 | kanji:大 (tatoeba-536769) | rejected: emptying ex-3's cite removes the only practice credit for もの / ない, which W21b moved in because this card was their first user. Owner call: keep the cite, or move both unlocks back |
| les:n5-desu-wa-04 | vocab:2846738 なんで ("Mais exemplos" drop) | rejected: orphans gram:gp-31, which W21b homed here for these two cards. Fix: return gp-31 to les:n5-perguntas-04 |
| les:n5-perguntas-06 | vocab:1189360 どちら | rejected: removes the only practice credit for いい. Owner call: the 何方/どちら homograph ruling, or move いい to les:n5-passado-04 |
| les:n5-perguntas-06 | vocab:1577100 何 | rejected: ex-1 is the 何か exercise; emptying its cite leaves gram:gp-48 (the lesson's own point), 食 and 食べる unpractised. Owner call: the なに address ruling, or re-author ex-1 |
| les:n5-particulas-lugar-08 | vocab:1577100 | **stale**: neither the old nor the new span is in the body (source or index). W14 (c63f47a3) already removed that block; C5 no longer lists the use (13 same-level at HEAD, not the 14 the table was measured on). Nothing to apply |

Furigana (1 row): 来 in les:n5-verbos-03. The sentence says the reading of 来 varies (ku / ki / ko), so
any single ruby contradicts it; the verifier asks for an exemption instead of a reading. It stays the
one span the ratchet holds.

## 3. Mechanism

- `scripts/apply_lesson_body_spans.py --table <name>` (new, one script for all three): dry pass over
  both layers, then writes `research/derived/lessons/<slug>.json` (body, the lesson's own
  `sentence_refs`, `exercises[].sentence_refs`) and `db/corpus.sqlite` (`localized_text` pt-BR body,
  `lesson_sentence`, `exercise_sentence`). Drift on the live index refuses the whole table; off it (a
  replay that regenerates the kanji-exame sources) it is reported and skipped. Idempotent: a second
  run of each table reports 0 changes (checked).
- Manifest steps 142 / 143 / 144 (one per table, after item_refs 141); families renumbered 145-147.
  No note referenced the old family numbers.
- `validate_repairs_applied.py`: the three tables registered on one handler
  (`handle_lesson_body_spans`): every `from` gone from the shipped body, every non-empty `to` present,
  every exercise edit equal to the shipped `sentence_refs`.
- `validate_lesson_bodies.FURIGANA_RESIDUE_RATCHET` 264 -> 1.
- `validate_lesson_gating --write-baseline`: C5 and the sentence-fit backlog shrank (below).
- needs[] re-derived (`build_needs_table.py` -> `apply_lesson_needs.py --replace`): 2 edges changed
  (les:n5-desu-wa-03's note loses 彼/あれ; les:n5-numeros-tempo-03 now needs les:n5-perguntas-01 for
  人 instead of les:n5-perguntas-04 for 本), 1 channel list shortened; 736 edges, count unchanged.

## 4. Numbers

| measure | before | after |
|---|---|---|
| C5 forward uses same-topic / same-level / cross-level | 1 / 13 / 151 | 0 / 4 / 148 |
| sentence pairs above level / over budget / new kanji / new vocab | 152 / 20 / 140 / 34 | 150 / 19 / 137 / 25 |
| kanji `<jp>` spans with no reading (lesson bodies) | 264 | 1 |
| practice coverage (absent) | 6 | 6 (unchanged) |
| lesson bodies with a W08b two-points-as-one defect | 8 | 0 |

## 5. Lessons did not degrade (rendered diff of `course/` against HEAD)

134 files: 115 lesson JSON, 17 `.md` views, 2 `topic.json` (the two re-derived needs notes).
- Lesson JSON fields that moved: `body` 115, `sentence_refs` 10, `exercises[].sentence_refs` 8,
  `needs` 2. Nothing else (no unlock, card, exercise text or item_refs moved).
- Every changed body equals the HEAD body with the table spans applied, byte for byte (115 / 115).
- Tag-stripped text changed in exactly 17 lessons = the 8 W08b lessons + the 10 W21b lessons (one
  shared: les:n5-desu-wa-03). The other 98 lessons changed by an attribute only (`reading`); their
  rendered text is identical. The 17 `.md` views are those 17 lessons.

## 6. Gate

`python scripts/validate/validate_all.py`: green, quick replay included. The first run failed only
`validate_review_views` (8 n5/speak views): the exam and sentence views print where an item enters the
course through a lesson's sentences, and tatoeba-229628 left les:n5-desu-wa-02 / -03, so one exam
item (`cf:n5:4336:473`) lost its course placement line and the numbering after it shifted. Views
regenerated with `build_review_views.py --level n5,speak` (plus the build-stamp line); no address or
hash moved otherwise. `validate_repairs_applied`: the three new tables replay clean (244 rows).
Not a checkpoint, so no full replay was run: steps 142-144 carry quick_family null and are first
exercised by the next checkpoint's full replay.

Also measured: `validate_card_content` still passes (2,235 examples). Six W28 card examples cite a
sentence one of these lessons stopped rendering (les:n5-numeros-tempo-03: gp-43, 話, 語, たくさん on
tatoeba-122326; les:n4-condicionais-04: gp-120 on tatoeba-193408; les:n3-tempo-02: n3-tabi-ni on
tatoeba-11022968). None is above its lesson's level, so check F holds; their `why` ("rendered by the
lesson") is now historical and a W28 re-derivation would pick again.

## 7. Open

- The four rejected W21b rows need the owner calls listed in section 2 (the address / homograph
  rulings would fix three of them without touching prose).
- 来 in les:n5-verbos-03: an exemption mechanism for a span whose point is that the reading varies.
- `lesson_furigana.json`'s own `residue` list (W21) still lists the 217 rows as build output; the
  applied truth is `repairs/furigana_residue.json` and the ratchet.
- Pre-existing, unrelated: les:n4-forma-simples-06's source body and index body disagree on the
  うん item (source 運 "sorte", index うん "sim"); not touched here.
- Out of scope, reported by the verifiers: les:n5-comparacoes-01 still claims Japanese has no
  standalone "mais" (もっと is N5), and says のほうが appears in every mold (not in は…より…です);
  les:n5-adjetivos-07 teaches no-ga-suki / gp-23 as one construction under two keys (a ninth
  duplicate pair); gp-153 のような beside gp-77.
