# W11c — the review fix-up

**Unit:** APP_PLAN §6 step 1, third pass. **Source:** the independent adversarial review of W11a/W11b
(problems P1–P7). This report closes the must-fix list and the two follow-ups. It was written as the
work landed. Every number in it is re-derivable from the tracked artifacts it names.

| # | item | status |
|---|---|---|
| 1 | `spans_levels` two-layer drift (P3) | **DONE** |
| 2 | `ex:n5-conectando-01-6` teaches a false 何/なん rule (P7) | **DONE** |
| 3 | the fifth wrong ref: 様 @ `les:n4-passiva-02` (P5) | **DONE** |
| 4 | integer-id refs in the lesson authoring sources | **DONE** — with one measured failure of its own acceptance test, §4.3 |
| 5 | manifest replay: step number, `--quick`, the full-mode abort (P1) | **DONE** |
| 6 | report corrections (P2, P5, P6) | **DONE** |

---

## 1. `spans_levels`: the column now has one owner (P3)

**The defect.** `db/corpus.sqlite` said `["n5","n4"]` for `grp:particles-core`, `grp:wa-vs-ga` and
`grp:ni-vs-de`; `corpus/families/families.json` published `["n5"]` for all three. W11b's families
report §9.4 claimed the column "is now written by `recompute()` only so a reader of the index is not
lied to" — false for 3 of 707.

**Why.** `scripts/ingest/fix_contrasts.py` is the one family builder that never went through
`familylib.recompute()`. Its own `fam()` helper wrote the literal `json.dumps(["n5","n4"])` on the
INSERT path and, on the UPDATE path, touched `label_pt`, `governing_rule_pt` and `type` and nothing
else — so the column stayed frozen while the exporter derived the real span from the members.
Nothing in the gate compared the two.

**The fix.** `fam()` now calls `familylib.recompute()` with `familylib.member_levels()`, exactly like
`build_families.py` and `build_families_full.py`. The English label and governing rule moved into the
builder's own table at the same time, because they had been arriving from a translation campaign
whose inputs are `.gitignore`d, so a from-scratch rebuild produced these three with no `en` anchor.

Re-running the builder brings the DB to `["n5"]` for all three. **The export does not move:**
`corpus/families/families.json`, `corpus/families/INDEX.md` and `corpus/grammar/n5.json` are
byte-identical before and after (sha256 checked; the exporter already derived the span).

**The new gate — `validate_families.py` F9.** Two halves:

- the published `spans_levels` **equals** the levels its members carry. `validate_graph_edges.py`
  G10 only asserts *covers*, which a span naming every level in the language would satisfy;
- `family.spans_levels` in `db/corpus.sqlite` says the same as the export.

F9 is the only check in that file that opens the database, and the docstring says why: DB-vs-export
agreement is the one claim you cannot test from a single side. The README's rule ("a validator that
reads the DB validates the wrong artifact") is about validating *content* from the index, which F9
does not do — it validates the index against the export. The DB half prints
`SKIPPED (no db/corpus.sqlite under --root)` when the index is absent, since it is git-ignored and a
fresh checkout has none.

### Plant proof (copied tree, 2026-09-09)

Fixture: `corpus/` + `course/` + `db/corpus.sqlite` + a **copy of the validator itself**, `--root`
pointed at the copy.

| step | result |
|---|---|
| control (pristine copy) | exit 0, `OK every check passed` |
| plant A — the stale `["n5","n4"]` put back in the DB column for `grp:wa-vs-ga` | **CAUGHT** `[F9] grp:wa-vs-ga: db/corpus.sqlite stores spans_levels ['n5', 'n4'], the export publishes ['n5'] — the index and the source of truth disagree about a field a builder is supposed to own` |
| control again | exit 0 |
| plant B — published span widened to `["n5","n4","n3"]` on `grp:ni-vs-de` (still *covers* its members, so G10 stays green) | **CAUGHT** `[F9] grp:ni-vs-de: spans_levels is ['n5', 'n4', 'n3'], its members occupy ['n5'] — the published span is not the derivation it claims to be` |
| control again | exit 0 |

`scripts/validate/README.md`'s `validate_families.py` row now carries F9 and this proof.

---

## 2. The 何/なん rule the exercise taught was wrong (P7)

`ex:n5-conectando-01-6` (`les:n5-conectando-01`, authored by W11a) ended with:

> Antes de で, か e と o 何 quase sempre vira なん.

Wrong for か: 何か is なにか, not なんか. Replaced with the rule that actually holds:

> A leitura なん vem antes de sons das linhas た, だ e な (何で なんで, 何と なんと, 何の なんの,
> 何です なんです) e antes de contadores (何人 なんにん, 何時 なんじ). Antes de か, 何 continua なに:
> 何か se lê なにか.

Landed in all three layers through the tracked table, not by hand: the `practice` row in
`research/derived/repairs/homograph_rulings.json` (with a `corrected` field saying what was wrong),
`db/corpus.sqlite`, `research/derived/lessons/n5-conectando-01.json`, and — through the exporter —
`course/n5/topic-18-conectando/lesson-01.json`.

**Two scripts had to change for that to be possible, and that is the real finding.**
`apply_homograph_rulings.py` wrote an exercise's prompt/answer/explanation **on creation only**, so
"the table holds the content and the script only places it" was true for exactly one run: correcting
the row would have changed nothing anywhere. It now re-asserts type, answer, prompt and explanation
against the row on every run, in both layers. And `validate_repairs_applied.py`'s `practice` handler
checked the exercise's type, its body reference and its answer surface, but never its text — so a
corrected row that failed to reach the export was invisible. It now asserts the exported
`prompt`/`explanation` [pt-BR] verbatim against the row.

---

## 3. The fifth wrong ref, closed (P5)

`les:n4-passiva-02` rendered `vocab:1605840` (様/よう, the formal noun behind のよう) under the gloss
*"sufixo de respeito, usado depois de nomes de pessoas para soar bem cortês"* — which is
`vocab:1545790` (様/さま). W11a recorded it in §7.2 and left it out of scope.

Closed as a `ref` ruling row (`kind: ref`, `verdict: change`, `how: ruling`, `confidence: certain`)
in the same table, applied by the same script. No body edit: the resolver's `ruling` tier reads the
row and lands on さま at export time. `how: ruling` and not `reading` because the body prints no kana
beside that chip, which is exactly why the reading tier could not see it and why no row ever existed
in `vocab_disambiguation_review.json` (only one record spells 様/よう there, so the queue had nothing
to ask about).

Gating: `vocab:1545790` is unlocked at `les:n4-suposicao-03` (topic ord 31); this lesson is topic ord
32. So the `course/gating_exemptions.json` row that held the old chip open is stale, and
`prune_exemptions()` now drops any gating row whose `(lesson, ref)` a `change` ruling re-points —
the table decides, the file follows, and the two cannot drift. **8 → 4 → 3** body-ref exemptions.
The 様 `hold` row (the *card*, which is a policy call and stays deferred) and the gating header were
both restated so the exemption file and the table say the same thing.

**Rendered diff, chips resolved to the kana the app prints, over all 322 lesson bodies:**

```
== les:n4-passiva-02 (n4/topic-32-passiva/lesson-02.json)
    -«よう» (様) vocab:1605840
    +«さま» (様) vocab:1545790

rendered chip streams differ in 1 of 322 lessons
```

Exporter-level diff over the whole `course/` tree: **3 files** — `n4/topic-32-passiva/lesson-02.json`
(one attribute; the prose beside it was already さま's and is unchanged), and
`n5/topic-18-conectando/lesson-01.json` plus its `.md` (item 2's explanation). Field by field, the
only difference in the passiva lesson is:

```
- <item><vocab ref="vocab:1605840"/><text>: sufixo de respeito, usado depois de nomes de pessoas para soar bem cortês.</text></item>
+ <item><vocab ref="vocab:1545790"/><text>: sufixo de respeito, usado depois de nomes de pessoas para soar bem cortês.</text></item>
```

`course/gating_exemptions.json` also changed, by the apply script rather than by the exporter.

---

## 4. Integer-id refs in the lesson authoring sources

### 4.1 What was there

`contracts/manifest.json`'s own `id_convention` says a storage row number "must never be used as an
API key", and `validate_stable_addresses.py` gates that over the export. The export was clean —
`export_course.py` `_deref` rewrites `vocab:1421` (a row of `db/corpus.sqlite`) and `vocab:人` (a
headword up to three records answer to) to the published slug on the way out. The **authoring layer**
was not, and that is the layer a manifest replay reads:

| kind | rows | occurrences | files |
|---|---:|---:|---|
| `row_id` — `vocab:<row number>` | 31 | 62 | 19 (12 of them in `n3-conectores-05.json` alone; 1 is `vocab:449` in `n5-passado-05.json`, added by W11a) |
| `ambiguous_headword` — `vocab:<headword>` two records answer to | 8 | 16 | 8 |

The review counted 32 row-id refs; the measurement is **31** (62 occurrences: each id appears once
as an `unlocks[].ref` and once as a body chip). 30 pre-existed at HEAD and W11a added one. A 32nd
candidate, `vocab:０` in `n5-verbos-06.json`, is *not* one: ０ is the full-width character and the
real headword of the N5 word for zero, which is why `_deref` tests `ident.isascii()` before treating
a ref as numeric.

Table: `research/derived/repairs/lesson_ref_addresses.json` (39 rows). Apply script:
`scripts/apply_lesson_ref_addresses.py`, idempotent, both layers (the raw authoring file, plus
`lesson_unlocks.ref` and the lesson body in `localized_text`), registered as **step 112** of
`research/derived/rebuild_manifest.json`. It re-derives every mapping from the vocab registry before
it writes, so a renumbered index refuses rather than re-pointing a chip at a different word.

### 4.2 The eight `ambiguous_headword` rows are not a headword sweep

322 lessons still address vocabulary by headword and `vocab_identity.py` settles them on evidence.
These eight are one **measured** class. Nine ambiguous headwords are unlocked by two lessons; for six
of them the two lessons sit at different levels and the resolver's `level` tier separates them — and
`level` is a record field that survives a rebuild. For the other three (中, 何, 止める) plus 側 the two
lessons are at the same level, `level` cannot help, and the decision falls to
`vocab.introducing_topic_id` — a placement column `scripts/ingest/place_items.py` recomputes by
bin-packing `freq_rank`. Both 側 records carry freq 1521 and both 中 records carry 76, so a
from-scratch replay files each pair under one topic, **both** lessons resolve to the same record, and
`familylib.unlock_topic_map()` aborts the rebuild on a ledger that contradicts itself. Writing the
address each lesson means removes the guess. Which tier settles which pair was measured, not assumed:

```
  中    les:n5-numeros-tempo-04   n5 -> vocab:1620400  via introducing_topic   <- converted
  中    les:n5-comparacoes-02     n5 -> vocab:1423310  via introducing_topic   <- converted
  何    les:n5-comparacoes-02     n5 -> vocab:1577100  via introducing_topic   <- converted
  何    les:n5-conectando-01      n5 -> vocab:2846738  via introducing_topic   <- converted
  止める les:n4-oracoes-relativas-01 n4 -> vocab:1310680 via introducing_topic  <- converted
  止める les:n4-condicionais-01      n4 -> vocab:1310670 via introducing_topic  <- converted
  先/家/居る/彼/米/開く  (n5 vs n4 pairs)          via level                     <- left alone
```

### 4.3 Three code paths had to learn the slug form, and the export is NOT byte-identical

Four places treated a numeric identifier as a row number and would have broken, silently, on the
converted refs:

| file | what it did | what it does |
|---|---|---|
| `scripts/ingest/load_lessons.py` `_member_id` / `backfill_introducing_topic` | headword, then row id | published slug, then headword, then row id. Without this `vocab:1189370` would have looked for row 1,189,370, found nothing, and loaded the unlock with a warning and no `lesson_introduces` row |
| `scripts/export/vocab_identity.py` `_claimed` | built the sibling filter's claim set from NUMERIC refs only | a published slug claims too. Without this the set would have emptied and the sibling filter would have stopped firing in every converted lesson — `les:n3-conectores-05` alone has twelve |
| `scripts/apply_homograph_rulings.py` `apply_unlocks` | slug ref → treated as a row id | slug first, then row id, then headword |
| `scripts/validate/validate_lessons.py`, `scripts/validate/audit_jlpt_coverage.py` | resolved refs by headword / bare ident | both accept the slug; the JLPT audit dereferences every ref form to a headword before comparing (it had started reporting 中, 何, 側 and 止める as "tagged but not taught") |

**The acceptance test was "the export must be byte-identical", and it does not hold.** Measured over
the whole `course/` tree, before and after:

```
course/ files                       788
  byte-identical                    497
  JSON: permutation only            283
  Markdown: same items, reordered     8  (10 lines)
  REAL CONTENT DIFFERENCES            0
```

Every difference is a **permutation**: canonicalising each document by sorting every list on its JSON
text makes the 283 JSON files compare equal, and each of the 10 differing Markdown lines holds the
same multiset of items in a different order. No record was added, removed or changed.

The cause is worth naming, because it is the same class of defect this unit is closing.
`lesson_unlocks` has `PRIMARY KEY (lesson_id, unlock_type, ref)`, so SQLite returns it in **raw ref
string** order, and the exporter passes that order straight into three published lists —
`unlocks[]`, `srs.introduces_cards[]` and `cumulative_known_set`. The published order is therefore a
function of how a ref happens to be SPELLED in the authoring layer, not of anything the reader can
see. Rewriting 39 refs re-sorts them; because `cumulative_known_set` is cumulative, a reorder in
`les:n5-perguntas-01` (topic 8) propagates to every later lesson, which is why 283 files move for 21
edited ones.

**Not fixed here, deliberately.** The fix is to order those lists by the address they publish, which
would re-sort nearly every one of the 788 files in a single commit — a drive-by refactor of the whole
courseware export, on a unit whose job was to close a review list. Recorded as the finding it is:
*three published lists are ordered by a storage artefact.* Until that changes, any future ref rewrite
will churn the same way.

### 4.4 The new gate — `validate_stable_addresses.py` check 5

The same rule one layer up, over `research/derived/lessons/*.json`: a `<ns>:<digits>` ref passes only
if it IS a published stable id in that namespace's registry, which is exactly how `vocab:1189370` (a
JMdict id) is told apart from `vocab:449` (a row of the index). Scanned as raw text, because a ref
appears both as a structured field and as an attribute inside the body string.

**Plant proof** (copied tree: `corpus/` + `course/` + `contracts/` + `research/derived/lessons/` + a
copy of the validator; `--root` at the copy):

| step | result |
|---|---|
| control | exit 0, `322 lesson file(s), 66 numeric ref(s), every one a published stable id` |
| plant A — one converted ref put back (`vocab:1454500` → `vocab:1505`) | **CAUGHT**, 2 failures (unlock + body chip), naming the record row 1505 actually holds |
| control again | exit 0 |
| plant B — a numeric ref into a namespace with no registry (`thing:12`) | **CAUGHT** |
| control again | exit 0 |
| plant C — the authoring tree cut to 5 files | **CAUGHT** by the floor: a check that passes on nothing is not a check |
| control again | exit 0 |

The table is also replayed on every run: `validate_repairs_applied.py` gained a
`lesson_ref_addresses.json` handler asserting, per row, that the export renders `new`, that `new`
resolves to a record with the row's headword AND kana (a rewrite landing on a different word is the
only way this table can do damage), and that `old` is gone **from that lesson** — not from the export,
because `vocab:中` is still a legitimate ref in the lessons this table does not touch.

---

## 5. The manifest replay (P1)

### 5.1 (a) the step number

`w11_homographs_report.md` §8 said `apply_homograph_rulings.py` was "step 115". It was **112**; 115
was the last step number in the manifest, not this script's. Corrected there. After W11c inserted
`apply_lesson_ref_addresses.py` at 112 it is **113**, and the manifest is 116 steps / 80 enabled.

### 5.2 (c) the full replay aborted, and it had for six days

Run: `python scripts/validate/validate_index_rebuildable.py` (no `--quick`). The exact failure, at
step 110:

```
  [FAIL] 110 scripts/migrate_grammar_merge.py    0.1s   gp-152: cumulative_known_set is 0, the migration was written against 157

[FAIL] the rebuild itself did not run clean; nothing to diff
```

and, with `--keep-going` to see past it, the full list:

```
  PRECONDITION FAILED: gp-152: lesson_unlocks is 0, the migration was written against 1
  PRECONDITION FAILED: gp-152: lesson_unlocks_dup is 0, the migration was written against 1
  PRECONDITION FAILED: gp-152: lesson_introduces is 0, the migration was written against 1
  PRECONDITION FAILED: gp-152: lesson_introduces_dup is 0, the migration was written against 1
  PRECONDITION FAILED: gp-152: family_member is 0, the migration was written against 1
  PRECONDITION FAILED: gp-152: exercise_item is 0, the migration was written against 1
  PRECONDITION FAILED: gp-152: cumulative_known_set is 0, the migration was written against 157
```

**Diagnosis, and the review's hypothesis was right.** `expect` is a drift check measured on the LIVE
index on 2026-09-02. A from-scratch replay is already post-migration on the referencing side before
this step runs: `rewrite_authoring()` re-pointed `research/derived/lessons/*.json` when W08 landed and
that rewrite is **committed**, so `load_lessons.py` rebuilds `lesson_unlocks`, `lesson_introduces`,
`exercise_item` and `cumulative_known_set` already naming the survivor. Every lesson-side count is 0
*because there is nothing left to move*. `family_member` is 0 for a second reason W11b created: the
family builders now run at the END of the manifest, so no family exists at step 110.

Four steps had to be fixed before the replay reached the end. Each fix is a statement, not a mute
skip:

| # | step | why it failed in a replay | fix |
|---|---|---|---|
| 1 | `migrate_grammar_merge.py` | the above | `expect` is enforced against `db/corpus.sqlite` only. On any other database the measured-vs-expected lines are **printed** (`precondition (NOT ENFORCED — target is …)`), not swallowed. What checks a replay is `validate_index_rebuildable.py`'s byte-for-byte diff, which is strictly stronger than a row count |
| 2 | `migrate_vocab_repoint.py` | same class, 30 preconditions: W09's authoring rewrite is committed too, `family_dropped` is 0 for the same ordering reason, `reading_uses_dropped` differs because the live index has 286 reading rows and a replay builds 130, and the exam banks the plan reads live under the repo, not the work root | same rule, same wording |
| 3 | `apply_homograph_rulings.py` | `FileNotFoundError` on `<work>/course/coverage_exemptions.json`. A replay redirects `$YOMINEKO_OUT_ROOT` to a work root seeded with the lesson layer only. The manifest note already called this part "a no-op re-proof on a rebuild"; the code did not | skips the exemption prune with a printed reason when the files are not under the out-root |
| 4 | `build_families_full.py` | `familylib: kanji kanji:一 is unlocked under two topics (9 and 51)` — `build_exam_kanji_lessons.py` re-chunks the kanji exam lessons from scratch in a replay and produces **221** kanji that two lessons unlock. `rebuild_baseline.json` already records that as a rebuild-fidelity gap with its cause | against `db/corpus.sqlite` this stays a hard refusal (0 such items there). Against a scratch rebuild it warns and takes the EARLIEST unlocking lesson in course order — the same rule `load_lessons.backfill_introducing_topic()` already uses for "which topic introduces this". The assertion is not lost: `validate_unlock_ledger.py` is hard, in the suite, and reads the export |

The 側 / 中 double-unlock that also aborted the run is fixed by §4, not by a relaxation: those refs
now name records, so the replay resolves them the way the export does.

**Result.** `rebuild finished in 1.4 min — 80 step(s) run, 0 failed`, and:

```
compared 790 exported file(s) in 85s (mode full, build date pinned to 2026-09-09)
[OK] 790 exported file(s) checked, 643 held by rebuild_baseline.json at the recorded bytes
```

### 5.3 The re-recorded full baseline

| | before (2026-09-02) | after |
|---|---:|---:|
| files compared | 787 | 790 |
| held by the baseline (differ from the committed export, with a cause) | 650 | 643 |
| **rebuild byte-identically** | **137** | **147** |

**The eight that moved, and why.** All eight are the lessons the address rewrite fixed:
`course/n5/topic-08-perguntas/lesson-0{1..6}.json` and
`course/n5/topic-09-numeros-tempo/lesson-0{1,2}.json`. Topic 8 is where `vocab:側` was unlocked and
topic 9 where `vocab:中` was; in a replay both resolved to the wrong sibling, so those files could
never match. They match now, and because `cumulative_known_set` is cumulative the correction lands
first on the lessons immediately after each fix point.

**The one that was added.** `corpus/families_deprecated.json` — a file W11b's exporter created, which
did not exist when the 2026-09-02 baseline was recorded. The replay writes 4 bytes (`[]`-shaped)
against the committed 2,400, because the 52 retirements come from builders that need a graph the
replay does not fully reproduce.

**Why 790 and not 787.** The rebuild's own tree, not the committed one: it writes
`corpus/families_deprecated.json` plus extra `course/n4/topic-37-kanji-exame/lesson-*.json` leaves,
because `build_exam_kanji_lessons.py` re-chunks that topic from scratch. That is the same
rebuild-fidelity gap as item 4 in the table above, and it is baselined with its cause.

Re-running after `--record` is clean and stable: `[OK] 790 exported file(s) checked, 643 held`.

### 5.4 (b) `--quick` replays none of 112–116, and cannot

Measured rather than asserted. `--quick` selects the steps tagged `quick_family: "grammar"`, so its
scratch index has no `lesson` and no `vocab` rows. Running the five new steps under that step set:

```
  [FAIL] 112 scripts/apply_lesson_ref_addresses.py   NOTHING WAS COMMITTED — an address that does not re-derive is not written.
  [FAIL] 113 scripts/apply_homograph_rulings.py      NOTHING WAS COMMITTED — a ruling that does not reproduce is not applied.
  [OK  ] 114 scripts/ingest/build_families.py        families live: 7 (deprecated 0); memberships now: 0
  [OK  ] 115 scripts/ingest/build_families_full.py   families live: 7; memberships: 0
  [OK  ] 116 scripts/ingest/fix_contrasts.py         ok
```

112 and 113 refuse every row (they consume the course). 114–116 "succeed" and derive **7 families
with 0 memberships** against the 707 / 4,969 that ship — recording that as a baseline would pin a
family layer that is not the one in the export, which is worse than not replaying them at all.

**So: what replays steps 112–116 is `validate_index_rebuildable.py` in FULL mode** (`python
scripts/validate/validate_index_rebuildable.py`, ~85 s + export), which since this unit runs to the
end. `--quick`, the form registered in `validate_all.py`, reaches none of them and never will without
becoming the full run. Written into `scripts/validate/README.md` so the next reader does not have to
re-derive it.

---

## 6. Report corrections

| report | claim | correction |
|---|---|---|
| families §2.2, §9.4 | "16 distinct spans" | **10**, listed as a table in §2.2: `["n3"]` 159, `["n4","n3"]` 157, `["n5","n3"]` 117, `["n5","n4","n3"]` 102, `["n5"]` 74, `["n4"]` 57, `["n5","n4"]` 36, `["n3","n2"]` 3, `["n5","n1"]` 1, `["n3","n1"]` 1. The DB agrees with the export on all ten since §1 |
| families §9.4 | `spans_levels` "is now written by `recompute()` only" | false for 3 of 707 — see §1. Restated, and the claim that it is "validated only indirectly" is now false in the other direction: F9 asserts it in both layers |
| families §8.1 | "the full mode was not re-recorded … belongs to whoever next runs full mode" | it also could not RUN. §5 says so, fixes it, and records the new baseline |
| families §5.1, §10 | family steps at "113-115" | 114-116 since W11c inserted step 112 |
| homographs §1 | "body refs pointing at the wrong homograph 4 → 0" | scoped to the four the owner enumerated, with the fifth (§7.2) added as its own row and marked closed here |
| homographs §1 | practice-coverage debt "2,941 → 2,937" | before column is **2,937**, the frozen baseline. 2,941 was a mid-unit number — after the five promotions, before the four exercises. The unit put the debt back where it found it |
| homographs §7.2 | "there is a fifth provably wrong ref, and it was left alone" | marked closed, pointing at §3 |
| homographs §8 | `apply_homograph_rulings.py` "step 115" | **112** at the time, **113** now, with the sentence the review asked for: the full mode replays it, `--quick` cannot |

---

## 7. What a reader should push back on

**1. The export is not byte-identical, and I did not fix the reason.** §4.3. Three published lists —
`unlocks[]`, `srs.introduces_cards[]`, `cumulative_known_set` — are ordered by SQLite's PRIMARY KEY
order over the raw authoring ref, so their order is a function of how a ref is spelled rather than of
anything published. I proved the diff is a pure permutation and left the ordering alone, because
fixing it re-sorts nearly all 788 course files in one commit. That is a deferral, not a resolution,
and the next ref rewrite will churn the same way.

**2. "Preconditions are enforced against the live index only" is a real weakening.** Two migrations
now print, rather than refuse, when their `expect` block does not match a scratch database. The
argument is that a replay is checked harder — `validate_index_rebuildable.py` diffs the rebuilt
export byte for byte against the committed tree, and 643 files are pinned at recorded bytes. The
counter-argument is that a genuine drift introduced in a scratch context would be reported as a
baseline difference rather than as a precondition failure, which is quieter. I think the trade is
right; someone should disagree with it out loud if they think otherwise.

**3. `familylib` no longer aborts a scratch rebuild on a contradictory ledger.** It takes the
earliest unlocking lesson and warns. The guard that matters (`validate_unlock_ledger.py`) is hard and
runs on every gate over the export — but it does not run inside a replay, so a replay can now build a
family layer from a ledger that contradicts itself and only the byte diff will notice. Against
`db/corpus.sqlite` the hard refusal is unchanged.

**4. The eight `ambiguous_headword` conversions are a precedent.** They say: when a lesson ref's
identity depends on a column a rebuild recomputes, write the address. Sixty-seven other ambiguous
headword refs are unlocked by exactly one lesson and six more are separated by `level`; none of them
was touched. If the rule is right, those are also worth converting one day, and it should be a
decision rather than an accumulation of exceptions.

---

## 8. Artifacts

Only the files W11c touched. Everything else in the working tree is W11a/W11b.

| path | what W11c did |
|---|---|
| `research/derived/repairs/lesson_ref_addresses.json` | **new.** 39 rows: 31 `row_id`, 8 `ambiguous_headword`, each with its evidence |
| `scripts/apply_lesson_ref_addresses.py` | **new.** Idempotent, both layers, re-derives every address from the registry before writing. Manifest step 112 |
| `scripts/ingest/fix_contrasts.py` | goes through `familylib.recompute()`; `spans_levels` is member-derived; both locales in the builder's own table |
| `scripts/validate/validate_families.py` | **F9** — the published span equals its members' levels, and `db/corpus.sqlite` agrees. Plant-proved, two plants |
| `scripts/validate/validate_stable_addresses.py` | **check 5** — no row-number ref in `research/derived/lessons/*.json`. Plant-proved, three plants including a floor |
| `scripts/validate/validate_repairs_applied.py` | `lesson_ref_addresses.json` registered with its own addressing; the `practice` handler now asserts the exported `prompt`/`explanation` verbatim |
| `scripts/apply_homograph_rulings.py` | re-asserts an existing exercise's content from the table; drops a gating exemption a `change` ruling makes stale; accepts a slug unlock ref; skips the exemption prune when the out-root has no `course/` |
| `research/derived/repairs/homograph_rulings.json` | 27 → 28 rows: the 様 `ref` ruling; the corrected 何/なん explanation; four `ref_written` values moved to the slug form; the 様 hold and the gating header restated |
| `course/gating_exemptions.json` | 4 → 3 |
| `scripts/migrate_grammar_merge.py`, `scripts/migrate_vocab_repoint.py` | `expect` enforced against `db/corpus.sqlite` only; printed, not swallowed, elsewhere |
| `scripts/familylib.py` | `unlock_topic_map()` warns and takes the earliest unlocking lesson on a scratch rebuild; hard refusal unchanged against the live index |
| `scripts/ingest/load_lessons.py` | `_member_id` / `backfill_introducing_topic` resolve the published slug first |
| `scripts/export/vocab_identity.py` | the sibling filter's claim set accepts a slug ref |
| `scripts/validate/validate_lessons.py`, `scripts/validate/audit_jlpt_coverage.py` | accept the slug form; the JLPT audit dereferences every ref form to a headword |
| `research/derived/rebuild_manifest.json` | step 112 inserted, 112-115 renumbered to 113-116, cross-references updated. 116 steps, 80 enabled |
| `scripts/validate/rebuild_baseline.json` | full mode re-recorded: 650 of 787 → 643 of 790 |
| `scripts/validate/validate_index_rebuildable.py`, `scripts/validate/README.md` | the real numbers, and what replays steps 112-116 |
| `research/reports/w11_homographs_report.md`, `research/reports/w11_families_report.md` | §6 |

## 9. The run

```
apply_lesson_ref_addresses.py -> apply_homograph_rulings.py -> fix_contrasts.py
  -> export_corpus.py -> export_course.py -> export_readings.py
  -> infer_shapes.py -> build_schemas.py -> build_manifest.py
  -> (cd prototype && npm run sync-data)
  -> validate_all.py
```

Last line:

```
RESULT: ✅ ALL HARD VALIDATORS PASS (advisory items are human-reviewed)
```

Re-running both apply scripts reports 0 changes; re-running all three exporters reproduces `corpus/`
and `course/` byte for byte. `validate_index_rebuildable.py --quick` `[OK] 4 files`; full mode
`[OK] 790 exported file(s) checked, 643 held by rebuild_baseline.json at the recorded bytes`. No git
state was touched: still on `main` at `a6283ba2`, no commit, no branch, no stash.
