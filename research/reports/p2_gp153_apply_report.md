# P2-gp153 apply: the ninth W08b merge (D5b) and the n5-comparacoes-01 fixes

**Unit P2-gp153, 2026-09-23. Not a checkpoint: gate + quick replay.** Input: the verified follow-up
to W08b, `research/derived/pending/comparacoes_fixes.json` + `comparacoes_fixes.verdict.json`
(10 checked: 4 ok, 6 corrected, 0 rejected). Mechanical apply: nothing authored in this unit.
Every text that landed is either the author's (ok) or the verifier's `corrected` text.

## 1. What the tables became

The pending file carried two things; they are now two tracked tables under `research/derived/repairs/`
(the pending table is removed, the verdict stays in `pending/` as the audit trail):

| table | rows | applied by | manifest |
|---|---|---|---|
| `gp153_merge.json` | 9: 1 merge, 5 exam-item (4 re-pointed, 1 retired by P1), 3 prose (all verifier-corrected) | `migrate_grammar_merge.py` (MERGES row D5b) + `apply_w08b_merges.py --phase prose --table gp153_merge.json` | 111 (MERGES), 145 (prose) |
| `comparacoes_fixes.json` | 5 span rows over 2 lessons: 2 for les:n4-suposicao-04 (the verifier's SEPARATE-RUN rows), 3 for les:n5-comparacoes-01 (edit 0 verifier-corrected) | `apply_lesson_body_spans.py --table comparacoes_fixes.json` | 146 |

Families renumbered 147-149 (no note referenced their numbers); `step_count` 147 -> 149.

## 2. The merge (gp-153 {のような} -> gp-77 {のように, のような})

Rule check re-read from the verdict: forms subset, same meaning (nuance tags subset), same topic
(top:n4-suposicao), same family, ONE lesson (les:n4-suposicao-04) unlocked all three records. Survivor
gp-77, as D5 chose.

- **`expect` re-measured on today's index** (dry run of `migrate_grammar_merge.py` at HEAD 6d863af1,
  post D5, post P1 banks): all 14 counts equal the derivation's (sentence_grammar 5, exercise_item 1,
  lesson_unlocks/introduces 1 + dup 1, family_member 1 + dup 1, cumulative_known_set 134, the rest 0);
  no precondition failed. `--apply` then `--check`: OK.
- Edges: 5 sentence_grammar re-pointed, 1 exercise_item, 1 exercise_item_ref, the duplicate unlock /
  introduce / family edge dropped, 2 lesson-body addresses re-pointed, 134 stored known sets.
- **Content appended to gp-77** (the verifier's corrected `measured.content`: D5 had already appended
  register `plain`, usage `spoken` and the tanos level source): `refs.also_known_as` += のような and
  one formation variant (clause + ような, 子供が遊んでいるような).
- **E1 re-measured on the P1-rebuilt banks.** The derivation named gf:n4:3535-3539. Four are still in
  `corpus/exam_banks/n4_grammar_form.json` and were re-pointed by `rewrite_exam_banks()` (byte-level,
  count checked against the parsed items). gf:n4:3539 (ど（　）スポーツ, the interrogative どのような)
  is gone: P1's rule 18a dropped it (blank starts inside a token). Its row carries
  `retired_by: p1-exam-fixes` with that reason, which also retires the verifier's out-of-scope note
  about its mis-tag. The みたいな two-answer distractor the verifier saw on 3535/3536 is also gone
  (P1 regenerated the distractors).
- `DECLINED` no longer lists gp-153; the ledger accumulates (11 merges).

### No content lost

Field-by-field audit of the loser on the post-merge index against a backup taken before the unit:

| fields | on survivor | contained | salvaged verbatim (ledger) | gloss keys on survivor + wording salvaged | empty | LOST |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 12 | 2 | 9 | 2 | 6 | **0** |

"Contained": `structure_pattern` ～のような is inside のように・のような, `level_agreement` 1/1 is inside
the survivor's 2/2 (tanos is the loser's source). The kept loser row is byte-identical to its
pre-merge self except `deprecated_by = gram:gp-77`. `corpus/grammar_deprecated.json` 10 -> 11 redirects.

### gp-77 prose (3 rows, all verifier-corrected)

Each row's `old` is D5's verified text as the index held it; `new` is the verifier's corrected text,
which is D5's CORRECTED text plus gp-153's facts (qualifica o substantivo, "um... como" / "do tipo
de" / "igual a", 天使のような人; よう = "aparência, semelhança", な atributiva, [frase] + ような with
子供が遊んでいるような声; no を nor "ser" between the nouns; 〜のごとき). The author's rows would have
undone two W08b corrections (*言ったのように in the explanation, the soft request misattributed to
のように in the nuance) and over-generalised the plain form in the formation; the verifier's text keeps
both W08b fixes and scopes the plain form to verbs. The three D5 rows in `w08b_merges.json` now carry
`superseded_by: {table: gp153_merge.json, row: 6|7|8}`. `en` of gp-77 kept as it was (needs_review),
as for every W08b survivor.

## 3. Lesson bodies

- **les:n4-suposicao-04** (separate-run rows, verifier-authored): the のような chip now reads "A forma
  のような de [gp-77]" (the chip is the whole のよう point after the merge), and the checklist keeps ONE
  row for gp-77 with all three facts. That row consumes W08b row 9's `to`, so
  `w08b_lesson_bodies.json` row 9 carries `superseded_by: {table: comparacoes_fixes.json, row: 1}`.
- **les:n5-comparacoes-01**: edit 0 (verifier's text: the winner takes は in the first mold and
  のほうが in the other two, which differ only by where the sentence starts), edit 1 ("a comparação não
  precisa de uma palavra para 'mais'"), edit 2 (the checklist restatement).

### Rendered diff of course/ against HEAD

143 files. 133 lesson JSON change ONLY `cumulative_known_set`, and in each the only difference is
`gram:gp-153` leaving (asserted per file). les:n4-suposicao-04 changes body, known set, unlocks (the
duplicate unlock), srs (the gp-153 card; gp-77's card keeps its example) and exercises (item_refs
re-pointed); les:n5-comparacoes-01 changes body only. **Both bodies equal HEAD's body + the address
rewrite + the table spans, byte for byte.** Rollups: course/INDEX.md, n4/INDEX.md, n4/course.json,
topic-31 topic.json, outline.json, topic_tests.json (rebuilt by `build_topic_tests.py`). Lesson .md:
only the two lessons, and only these lines move:

- n4-suposicao-04: `Introduz` gramática [gp-153, gp-77] -> [gp-77]; "A forma gp-153 qualifica..." ->
  "A forma のような de gp-77 qualifica..."; two checklist lines -> one line with the same three facts.
- n5-comparacoes-01: "o japonês não tem uma palavra solta para 'mais'" -> "a comparação não precisa de
  uma palavra para 'mais'"; the lead of the three molds (は in the first, のほうが in the other two); the
  checklist line.

No example, jp span or fact left either lesson.

## 4. Code

- `migrate_grammar_merge.py`: MERGES row D5b after D5; the gp-153 DECLINED entry removed.
- `apply_w08b_merges.py`: `--table w08b_merges.json|gp153_merge.json`; on the live index a row with
  `superseded_by` is counted as applied (on a replay the chain runs in order).
- `apply_lesson_body_spans.py`: `comparacoes_fixes.json` registered; a row with `superseded_by` is
  skipped.
- `validate_repairs_applied.py`: both tables registered; the `prose` branch of `handle_w08b_merges` goes
  through `marker_gate` (the existing five-condition chain proof); `handle_lesson_body_spans` gets
  `span_marker_gate`: the named row must be another tracked row on the same lesson whose first `from`
  equals this row's `to` with merged-away `gram:` addresses resolved through the published redirect,
  and the shipped body must carry the successor's `to`.

**Plant proof** on a copied tree (corpus, course, contracts, repairs + the validator itself), 6/6
caught, clean before and after: gp-77 explanation reverted to D5's text (gp153 prose row
`not-applied` AND the D5 marker `does-not-chain`); gf:n4:3535 back to gp-153; row 9's marker removed;
row 9's marker pointed at the wrong row; the n4-suposicao-04 checklist reverted (comparacoes row 1
fails AND row 9's marker stops chaining); n5-comparacoes-01 edit 0 reverted.

## 5. Gates

| gate | before | after |
|---|---:|---:|
| grammar registry (formation, level consensus, contracts) | 486 | 485 |
| grammar redirects | 10 | 11 |
| unlock ledger | 4,167 | 4,166 |
| SRS cards (lesson) | 4,282 | 4,281 |
| practice coverage, unlocked items | 4,071 | 4,070 |
| sentence coverage, taught items | 3,437 | 3,436 |
| exam banks | 5,103 OK | 5,103 OK |
| repairs replay | 0 FAIL | 79,007 rows, 0 FAIL (gp153_merge 8 PASS + 1 retired skip; comparacoes_fixes 5 PASS; w08b_merges +3 superseded skips; w08b_lesson_bodies +1 superseded skip) |

`validate_all.py`: **ALL HARD VALIDATORS PASS** (quick replay included). Regenerated: export_corpus,
export_course, export_readings, build_capabilities (cap:topic:n4-suposicao no longer lists gp-153),
build_topic_tests, contracts (infer_shapes -> build_schemas -> build_manifest), prototype sync-data,
review views (build stamp only).

**Quick replay.** corpus/grammar/INDEX.md and n4.json are held files; their replayed bytes moved, so
the quick baseline was re-recorded with a written cause. Checked on the kept scratch tree first: the
replayed gp-77 equals the committed export in every pt-BR text (explanation, formation, nuance) and
every structural field (forms, refs, formation_steps, register, usage, nuance tags, levels); the file
differs only by the held causes (no `en`, no family back-pointers, the em-dash cleanup). Full replay
not run (not a checkpoint): the new steps 145/146 have not yet been replayed from scratch.

## 6. Open, not this unit's

- les:n5-comparacoes-01: W08b row 5's heading "Três moldes, três ordens" / "um para cada ordem" still
  counts three orders where the lesson's own definition gives two (verifier found_not_in_scope[0]);
  the opening paragraph still says より + ほうが resolve every comparison, and the l1-advantage note calls
  のほうが a particle. Layer-C authoring.
- gp-77 `en` explanation / formation / nuance not re-derived from the new pt-BR (same open item as the
  eight W08b survivors).
- `research/derived/pending/reading_comp/work-*.json` still name gp-153 inside known-set snapshots;
  they resolve through the redirect when read (the W08b ordering rule).
- The derived `card_examples.json` and `item_refs.json` still carry one gp-153 row each; the gate
  retires / resolves them through the redirect. They drop on the next re-derivation.
