# W08b apply: eight grammar merges (C12, checkpoint)

**Unit C12-W08b, 2026-09-23.** Input: the W08b derivation and its verdict
(`research/derived/pending/w08b_merges.json` + `.verdict.json`, report `w08b_derive_report.md`).
The table now lives at `research/derived/repairs/w08b_merges.json` (60 rows, four kinds); the pending
copy was removed, its simulation and ordering notes are kept inside the tracked table. Mechanical
apply, nothing authored in this unit: the 24 prose texts are the derivation's, with the verifier's
`corrected` text applied to 9 of them.

| loser | survivor | lesson |
|---|---|---|
| gp-100 | gp-118 | les:n4-forma-simples-03 |
| gp-54 | no-ga-jouzu | les:n5-adjetivos-07 |
| gp-47 | yori-hou-ga | les:n5-comparacoes-01 |
| gp-154 | gp-77 | les:n4-suposicao-04 |
| gp-60 | tara | les:n4-condicionais-01 |
| gp-151 | te-shimau-chau | les:n4-aspecto-03 |
| gp-33 | janai-dewa-nai | les:n5-desu-wa-03 |
| n3-nda-mon | n3-da-mono-da | les:n3-causa-04 |

## 1. Fix-first rows, landed before the merge

| row | where | what |
|---|---|---|
| R1 | table `pre-merge` rows, `scripts/apply_w08b_merges.py --phase pre` (manifest step 110) | gp-60 `forms` ら -> たら, both `form_meanings` keys, `refs.label_en` |
| R2 | same | gp-54 copula out of its form (のがじょうずです -> のがじょうず), `register` / `register_json` polite -> neutral, `structure_pattern`, two formation variants, both glosses |
| G1 | `migrate_grammar_merge.diff_content` | a loser's `steps_unavailable` is salvaged, never copied, when the survivor carries formation steps (fired on gp-47 -> yori-hou-ga) |
| V1 | `validate_repairs_applied.handle_level_evidence` | a merged-away grammar record retires through the redirect (level_evidence row 123, n3-nda-mon: SKIP, not FAIL) |
| V2 | `build_speaking_path.py` (+ the same filter in `build_exam_banks.py`) | merged-away rows are not candidates; a kept loser no longer wins a form tie by key |
| E1 | `migrate_grammar_merge.rewrite_exam_banks()` | re-measured on the regenerated banks: the same 17 items, same ids (`gf:n3:5140`, `gf:n4:3409-3413`, `3532-3534`, `3540-3542`, `3544`, `gf:n5:4308-4311`), byte-level replace checked against the parsed count |

W31's `grammar_register.json` row 0 (no-ga-jouzu) gained `replay_old` = [polite, neutral]: on a
from-scratch replay the merge runs before W31's step and appends gp-54's (repaired) `neutral` to the
survivor's pre-W31 [polite]. Measured on a replay built to step 112: exactly that value; with the row
adjusted, `apply_grammar_register_repairs.py` meets it without a drift line. `old` keeps the historical
value.

## 2. The merge

`MERGES` grew by the eight rows. Every `expect` block was re-measured on today's index before any
write (a read-only run of `plan_edges`): **all eight equal the derivation's**, nothing earlier units did
moved them. Found on the way, all needed for the merge to be complete on today's tree:

- **W23's `exercise_item_ref`** (migration 019) is keyed by slug and was not in the W08 machinery:
  32 rows named a loser; 10 re-pointed, 22 dropped because the exercise already named the survivor.
- **`gram:<key>` item_refs in the authoring source.** W23 writes item refs as published slugs;
  `rewrite_authoring` only knew the bare key and would have died on its own stray check. It now
  re-points both shapes: 19 lesson files (8 unlock drops, 8 bodies, 32 item_refs, the same 10 / 22
  split as the index).
- **`apply_item_refs.py`** (step 141 now) resolves a loser ref through `deprecated_by` at apply time,
  and **`ingest_mined_stages.py`** resolves a target key the same way; both run AFTER the merge on a
  replay and would have re-linked the retired records (n3-nda-mon has 2 W13 mined sentences).
  `apply_item_refs.py --check` on the live index: 0 changes, DB and source agree.
- **The ledger** was rewritten from the last run's merges alone, which would have erased W08's two
  entries. It now accumulates (10 merges) and is written with LF.
- **W24 capability quote.** gp-151 was a topic-fallback key of `cap:topic:n4-aspecto`; once it merged
  into te-shimau-chau (cap:aspect-preparation), les:n4-aspecto-03 no longer claims that capability and
  `build_capabilities.py` refused its quote. The quote (the 〜終わる objective) was dropped from
  `repairs/w24_capabilities.json`, noted under `rederived_w08b`, as C5 did for W21b.
- `DECLINED` updated: gp-100/gp-118 is merged; gp-153 (のような, the third record in n4-suposicao-04)
  and no-ga-suki / gp-23 (found by the lesson-body pass) are listed as untriaged.

Order in the manifest: 110 `apply_w08b_merges.py --phase pre`, 111 `migrate_grammar_merge.py --apply`,
112 `apply_w08b_merges.py --phase prose`; everything after moved by two, families are 142-144.

## 3. No content lost (field-by-field, live index)

Audit of every loser field (grammar_point columns + localized_text) on the post-merge index against the
pre-merge backup, R1/R2 accounted for:

| loser -> survivor | fields | on survivor | contained | salvaged verbatim | gloss keys on survivor + wording salvaged | empty | LOST | kept loser row vs pre-merge |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `gp-100 -> gp-118` | 25 | 6 | 0 | 10 | 2 | 6 | 0 | identical |
| `gp-54 -> no-ga-jouzu` | 25 | 8 | 1 | 8 | 0 | 7 | 0 | identical |
| `gp-47 -> yori-hou-ga` | 25 | 8 | 0 | 10 | 0 | 6 | 0 | identical |
| `gp-154 -> gp-77` | 25 | 6 | 1 | 9 | 2 | 6 | 0 | identical |
| `gp-60 -> tara` | 25 | 8 | 0 | 8 | 2 | 6 | 0 | identical |
| `gp-151 -> te-shimau-chau` | 25 | 7 | 1 | 8 | 2 | 6 | 0 | identical |
| `gp-33 -> janai-dewa-nai` | 25 | 7 | 1 | 8 | 2 | 6 | 0 | identical |
| `n3-nda-mon -> n3-da-mono-da` | 23 | 7 | 0 | 9 | 0 | 7 | 0 | identical |

198 fields, **0 lost**. Each loser row is byte-identical to its pre-merge self except `deprecated_by`
and the R1/R2 cells; the salvage texts are in `research/derived/grammar_merge_ledger.json`.
`corpus/grammar_deprecated.json`: 2 -> 10 redirects.

## 4. Survivors

All eight carry `needs_review: true`. pt-BR explanation / formation / nuance = the reconciled text (24
rows; `validate_repairs_applied` replays them exactly, and rows 105 / 210 of
grammar_record_repairs.json still pass as spans). **`en` kept as it was, not re-derived** (checked
unchanged against the pre-merge backup): gp-118, no-ga-jouzu, yori-hou-ga, gp-77, tara,
te-shimau-chau, janai-dewa-nai, n3-da-mono-da, explanation / formation / nuance each. Forms after the
merge: no-ga-jouzu {のが上手, のがじょうず}, yori-hou-ga {よりほうが, よりのほうが}, n3-da-mono-da
{～(ん)だもの, ～んだもん}, the rest unchanged; no-ga-jouzu's register stays [neutral] (R2).

## 5. Rendered diff of `course/` against HEAD

314 files. Lesson JSON 279: `cumulative_known_set` on all 279 (the loser keys leave), `unlocks` +
`srs` on the 8 merge lessons (one duplicate unlock and one duplicate card each), `exercises[].item_refs`
on 19, `body` on 8. **Every body change is a pure loser -> survivor ref re-point** (checked by
rewriting HEAD's bodies with the eight replacements: identical). Lesson `.md` views: 8 lessons, only the
`Introduz` line and the chips. Plus the INDEX / course.json / topic.json rollups (counts and grammar
lists), outline, topic_tests, and 10 speak units (V2: getting_around-06 drills n3-da-mono-da where it chunked
n3-nda-mon, time_plans-03 drills gp-77 and gp-67, real_talk-01/05 drop gp-33 for their next pattern;
six units re-pick janai-dewa-nai's drill examples now that it carries gp-33's sentences).

**Known, and not this unit's to fix:** the chip re-point makes five bodies say one record twice
(n5-desu-wa-03 "A forma casual é [janai-dewa-nai]; a forma completa ... é [janai-dewa-nai]",
n5-adjetivos-07 "registrada também como [no-ga-jouzu]", n3-causa-04, n4-forma-simples-03,
n4-aspecto-03). That is what the verified `pending/w08b_lesson_bodies.json` fixes, and it is C13's (a).
Checked read-only here: **all 18 spans occur exactly once, in order, in the post-merge bodies**, and the
authoring source equals the DB for all eight lessons, so C13 can apply as written.

## 6. Gates

| gate | before | after |
|---|---:|---:|
| grammar registry (formation, level consensus) | 494 | 486 |
| unlock ledger | 4,175 | 4,167 |
| SRS cards (lesson) | 4,290 | 4,282 |
| card examples | 2,242 | 2,235 (7 retired rows skip) |
| practice coverage, unlocked items | 4,079 | 4,071 |
| sentence coverage, taught items | 3,445 | 3,437 |
| item_refs target refs | 5,858 | 5,836 |
| exam banks | 5,141 OK | 5,141 OK |
| repairs replay | 0 FAIL | 78,717 PASS, 42 skip, 0 FAIL (new table: 49 PASS + 11 retired pre-merge skips; +7 card_examples and +1 level_evidence retired skips) |

`validate_all.py`: **ALL HARD VALIDATORS PASS**. Two ratchets re-recorded with a written cause:
`speak_strand_baseline.json` (`w08b_cause`; 5 distances grew 0.1 to 0.6 points, 2 shrank; the record
drops the older `w18_cause` / `w32_cause`, restored) and the quick replay baseline (below). Review
views regenerated (build stamp plus the merged records).

Plant proof of the new handler and guards on a copied tree (corpus, course, contracts, repairs): clean
copy PASS; a survivor's prose reverted, an exam item set back to its loser, the gp-60 redirect dropped,
an exported item_ref set back to its loser: **4 / 4 caught**.

## 7. Full replay (checkpoint)

`validate_index_rebuildable.py` (full, 102 s): 790 files compared; before the record 324 held files
moved and nothing else (0 new, 0 healed). 296 of them are files this unit changed in the committed
export, moved the same way; the other 28 are the not-committed kanji-exame lessons of the replay, whose
replayed known set lost the loser keys. Re-pinned with that cause appended, then re-run:
`[OK] 790 exported file(s) checked, 571 held`. Quick mode: 4 held, re-pinned the same way; the replayed
pt-BR of all eight survivors equals the committed export. No earlier unit's step broke the replay.
`git status` unchanged by the replay (the migration now follows `$YOMINEKO_OUT_ROOT`).

## 8. Open

1. **C13 (a)**: the 18 lesson-body spans (verified, measured still valid above).
2. The survivors' `en` is the survivor's own and does not say everything the reconciled pt-BR says;
   re-derive it from the pt-BR (needs_review is set).
3. Post-merge review items carried in the table: gp-118 register [plain, polite] (polite from gp-100)
   against W31's own-forms rule; gp-77 register [formal, written, plain]; orthographic formation twins
   on no-ga-jouzu and janai-dewa-nai; `emphasis` nuance tag on janai-dewa-nai and n3-da-mono-da.
4. Untriaged duplicates: gp-153 / gp-77 {のような}; no-ga-suki / gp-23.
5. The 24 prose rows had one independent verifier (9 corrected); the Fable sample of the spend rules
   was not drawn in this unit.
6. `pending/reading_comp/work-*.json` known_sets still name losers: resolve through the redirect when
   read.
