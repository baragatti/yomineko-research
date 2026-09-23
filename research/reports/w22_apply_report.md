# W22 apply: the N3 dead end, the never-unlocked features, conjugation-form unlocks

_C4-W22, 2026-09-23. Checkpoint unit (full replay). Mechanical: derived 35 rows / authored 0.
Source derivation: `research/reports/w22_derivation_report.md` (2026-09-10)._

## What landed

| piece | where |
|---|---|
| re-derivation script (rules F / H1 / R3 contents, `--check` for drift) | `scripts/derive_w22_unlocks.py` |
| apply table, moved out of `pending/` | `research/derived/repairs/w22_n3_dead_end.json` (35 rows) |
| apply script, both layers | `scripts/apply_w22_unlocks.py` (manifest step 134; families now 135-137) |
| replay handler | `validate_repairs_applied.py` `handle_w22_unlocks` (row is in the shipped lesson, no other lesson carries it) |
| enum | `design/unlock_enums.json`: `feature` + `jlpt-sim-n3`; `conjugation_form` + `attributive`, `adverbial`, `negative-te`, `polite`, `polite-negative`, `polite-past`, − `provisional` |
| contract mirrors | `contracts/lesson.schema.json`, `contracts/types.ts` (regenerated), `contracts/user_state/feature_state.schema.json` (hand-authored enum + note), `design/courseware_architecture.md` §5, `design/user_state.md` §9 |
| consumer of the old path | `scripts/derive_forward_refs.py` now reads the table from `repairs/` |

Every row is an additive unlock. No body text, no SRS card (`item_to_deck` maps neither features
nor forms), no `needs` edge.

## Re-derivation against the current tree (the delta)

The 2026-09-10 derivation script was never landed, so it was re-implemented from the report and
**calibrated on the 2026-09-10 tree** (`git archive 6759ccdb^ course corpus`): all 25 form homes, all
9 feature homes and the drill numbers (18,524 / 0 / 18,524 / 2,587 gated by form) reproduce exactly.

Then run on today's tree (after W21b, W14, W20):

| | 2026-09-10 | 2026-09-23 |
|---|---|---|
| form homes unchanged | | 24 of 25 |
| `conj:adverbial` | `les:n5-adjetivos-01` (idx 80) | **`les:n5-passado-03` (idx 77)**, F-a: W21b moved `gram:i-adjectives` (built on `to-adverbial`) there |
| feature homes unchanged | | 8 of 9 |
| `feat:find-correct-kanji` | `les:n5-verbos-01` (idx 61) | **`les:n5-desu-wa-03` (idx 43)**, `ex:n5-desu-wa-03-21` (choices 来/時/何/分) |
| forms built on before any lesson teaches them | 7 | **still 7**: dictionary 17, nai 21, ta 31, te 21, attributive 3, adverbial 4, potential 1 lessons |
| drills gated by the form rather than the word | 2,587 | 2,777 (W21b moved vocab earlier) |
| residue | `provisional` | `provisional` (retired) |

The 7 base forms did **not** move: W21b's W22 rows were analytic only (its own comment: "nothing here
writes a form unlock"), so the gate-sound homes still land on the requiring lesson. The
`teach-true` alternative stays recorded per row (`home_teach_true`).

**F-c had to be tightened, and the tightening is calibrated.** W20 put bare headwords into answer
keys and several homograph siblings share a surface; under the literal 2026-09-10 rule that pulls
`dictionary` 44 → 42, `nai` 61 → 46 (ある's ない inside 来ない) and `conditional-ba` 141 → 72 (いい and
良い both printing よければ once), which would release ば drills 69 lessons before the lesson that
teaches ば. F-c now counts distinct surfaces, guards maximal matches across words, and ignores an
answer key that is a bare headword for the dictionary form. On the 2026-09-10 tree the tightened rule
gives the same 25 homes as the original; only three non-chosen F-c candidates differ.

## Applied

- **§1** `feat:jlpt-sim-n3` → **`les:n3-revisao-01`**. R1 names the last lesson of `top:n3-revisao`;
  today that topic has one lesson. `les:n3-revisao-03` cannot exist without authored prose, so the
  row carries `target_when_authored: les:n3-revisao-03`.
- **§2** 9 features homed by H1 (table above). `feat:handwriting-input` takes the H1 display home
  (`les:n5-kanji-exame-01`) per D5's default (retire the 691 handwriting cards); the cards are still
  exported, so the flag stays open for W20/D5. Residue 3 stays listed: `listening`, `voice-mode`,
  `visual-novel` (no artifact; D3).
- **§4** 25 `conj:` unlocks over 18 lessons, 6 enum additions, `provisional` retired.
- **§3** nothing written to lessons. The authoring brief in the table was re-read from the tree:
  lesson counts 31/35/34 and anchors unchanged, all 14 anchors and 132 retest refs resolve, and the
  malformed `gram:gram:<key>` refs of the 2026-09-10 file are corrected. Left `to_author`:
  - `les:n3-revisao-01` rewritten to block 1 (title, description, objectives, body, 6 exercises per
    `exercise_plan`);
  - `les:n3-revisao-02` and `-03` created; on creation `feat:jlpt-sim-n3` moves to `-03`;
  - the `top:n3-revisao` objective;
  - the needs chain (lands with the lessons through `build_needs_table.py`'s review-chain rule;
    `needs` is fully derived and C4 re-derives it, so it is not hand-added);
  - owner: the 4 N3 vocab unlocks on `les:n3-revisao-01`.

## Numbers

| | before | after |
|---|---:|---:|
| features unlocked by a lesson | 4 of 16 | **14 of 17** |
| `conjugation_form` enum values | 20 | 25 |
| lessons with a `conj:` unlock | 0 | 18 |
| final `cumulative_known_set["conjugation-form"]` | 0 | 25 |
| conjugation drills reachable (word and form both in some cks) | **0** of 18,524 | **18,524** of 18,524 |
| cks keys that shrink | | 0 |

## Lessons do not degrade

Rendered diff of `course/` against HEAD: 302 JSON files change and in every one the only differing
keys are `unlocks`, `feature_unlocks` and `cumulative_known_set`; 0 lesson Markdown files change;
0 body, title, objective or exercise changes.

## Gate

`validate_all.py`: **ALL HARD VALIDATORS PASS** (quick replay included). The first run failed on two
things, both fixed at the root:

- `validate_unlock_ledger.py` had never seen a `conj:` unlock and resolved its namespace to the empty
  string (25 FAIL A). `conjugation-form` is now a non-item type (namespace `conj`, members from
  `design/unlock_enums.json#conjugation_form`), so check A validates the value and check C enforces
  introduce-once. Plant on a copied tree: `conj:bogus` and a second `conj:te` holder, **2/2 caught**.
- the eight `research/review/` views carry the contracts build id, which the contract rebuild moved;
  re-rendered with `build_review_views.py --level n5,speak`.

`validate_repairs_applied.py`: `w22_n3_dead_end.json` 35/35 PASS. `derive_w22_unlocks.py --check`:
the table still matches the re-derivation on the applied tree.

## Full replay (checkpoint)

The rebuild runs clean and **all 35 W22 rows are in the rebuilt export** (step 134 re-adds the
handwriting feature to the kanji-exame lesson step 33 regenerates). 790 files compared: **0 new
divergences, 0 healed, 372 held files whose rebuilt bytes moved**:

| files | cause |
|---:|---|
| 51 | lesson `.md`: C3-W14 (`c63f47a3`, step 133 + the authoring sources it rewrote), which committed with the quick replay only. W22 changes no Markdown. |
| 108 | lesson / topic `.json` touched by both C3-W14 and W22 step 134. |
| 213 | `.json` touched only by W22 in the committed tree (185 committed, 28 rebuild-only kanji-exame lessons). Stripping W22's rows from the rebuilt file is exact on the committed tree (302/302), and on the rebuilt one it leaves only `cumulative_known_set.vocab` off the recorded bytes: the course-identity resolver, not W22 (W22 writes no vocab row; a replay with step 133 disabled leaves it unchanged; the only other commit since the last record is C3-W14). |

This is not a replay break (the rebuild ran every step clean, nothing new diverges), so nothing was
fixed in an earlier unit. `--record` re-pinned the 372 hashes and each entry's cause carries the
line above. Re-run: **790 exported files, 571 held at the recorded bytes, 0 wrong** (manifest
137 steps / 101 enabled).

## Open

- §3 prose (`to_author` list above); `feat:jlpt-sim-n3` moves to `les:n3-revisao-03` when it exists.
- Residue: `listening`, `voice-mode`, `visual-novel` (D3); the 691 handwriting cards (D5).
- `ました` / `ませんでした` / polite past still first unlock in a review lesson (`les:n5-revisao-02`):
  no verb-past lesson exists (W25 territory).
- Side effect seen during this unit's validation runs: `research/derived/vocab_repoint_ledger.json`
  was rewritten in the repo (its `exam_banks` section dropped), although the replay is meant to write
  nothing into the repo. Restored to HEAD, not committed; the writer is most likely step 111
  (`migrate_vocab_repoint.py --apply`) in a replay. Worth a look by the next replay unit.
