# W13 finish — the 97 late rows, and the mechanical particle-template repair

_Status: DONE. DB writer: this run. Gate green, full replay green and re-recorded. NOT COMMITTED
(this run was told to touch no git state)._

Companion to `research/reports/w13_apply_report.md` (open item 1) and
`research/reports/w13b_template_audit.md` (§7, "Como aplicar"). Nothing here authors Japanese or
pt-BR: every string comes from a tracked table.

## 0. Order of work

| # | step | state |
|---|---|---|
| 1 | register for the 97 late rows, derived by `derive_sentence_register_v2.py`, added to the W31 table | ☑ §1 |
| 2 | second ingest run (`--batches 30`) | ☑ §2 |
| 3 | N3 relink over the new sentences | ☐ NOT DONE, measured — §3 |
| 4 | particle templates: the 201 explanation-replacement rows, DB + Layer-B source | ☑ §4 |
| 5 | exports → contracts → sync → gate | ☑ §5 |
| 6 | W05 re-record | ☑ §6 |
| 7 | full-mode replay + `--record` | ☑ §7 |

Baseline before this run: bank 10,112; register table 10,112 rows (all `set: bank`); gate green
(`validate_all.py`, 62 hard validators); replay gate 18,170 rows clean.

---

## 1. Register for the 97 late rows

`derive_sentence_register_v2.py` read only `accepted.json` and `generated.json`. It gained one
repeatable flag, `--w13-source PATH`, and nothing else about the rules changed:

* the late file is MIXED (real and generated rows in one file), so the key is now decided per row by
  the ingest's own `sentence_key()` rule (`tatoeba-<id>` unless `generated` or no id, then
  `gen-<sha1(jp)[:12]>`) instead of per file. On `accepted.json` (4,197 rows, all `generated: false`
  with an id) and `generated.json` (26, all `generated: true`, no id) that is the same key as before;
* the late rows carry a single `target`, not `targets[]`, so the grammar/vocab signal reads either.

Run 1, before the ingest: `--w13-source research/derived/n3_mined/generated_uncovered_final.json`
→ 10,112 bank rows **byte-for-value identical** to the tracked table (0 diffs) + 97 `set: w13` rows.
That table is what the ingest read. Run 2, after the ingest and the export: `--skip-w13` → all
**10,209** rows `set: bank`, keyed by slug. **0 of the 97 changed value** between the pre-ingest
derivation (authoring targets only) and the post-ingest one (real grammar tags and vocab links).
`apply_sentence_register.py`: 0 written, 10,209 already applied, 0 deferred.

The 97, by register: neutral 61 · polite 18 · casual 13 · formal 2 · archaic 1 · **NULL 2**. By rule:
`plain-predicate` 61, `polite-predicate` 16, `soft-final` 10, `casual-marker` 3, `keigo` 2,
`no-signal` 2, `polite-request` 1, `polite-request-nasai` 1, `bungo-inflection` 1.

## 2. The second ingest run

`ingest_mined_stages.py --apply --source research/derived/n3_mined/generated_uncovered_final.json
--layerb research/derived/mined_layerb_n3 --tag n3-exemplification --provenance-source
w13:n3-exemplification --batches 30` — open item 1's command, unchanged.

| | value |
|---|---|
| pre-flight | clean, 97 rows, 1 batch |
| ingested | **97** (bank 10,112 → **10,209**), 0 rolled back, 0 refused, 0 blocklisted |
| invariant failures (I1/I2/I3, re-checked after the commit as well) | **0** |
| real Tatoeba rows, `ai_generated` 0, `jp_source` tatoeba | **35** (jp byte-equal to `raw_tatoeba_sentence` on all 35) |
| generated rows, `ai_generated` 1, `jp_source` ai-generated, `sent:gen-<hash>` slugs | **62** |
| `needs_review` / `layer` / `created_by` / `tags` / `source` | 1 / B / ai / `["mined","n3-exemplification"]` / `w13:n3-exemplification` on all 97 |
| C tokens / particles / `sentence_vocab` edges | 761 / 234 / 346 |
| particles with an empty explanation | 0 |
| computed `sentence.level` | n3 34 · n4 30 · n5 16 · n1 11 · n2 6 |

**The split is 35 / 62, not the 36 / 61 open item 1 wrote.** The file itself says 35 rows are
`mode: selected, generated: false` with an integer Tatoeba id and 62 are `mode: generated`; the ingest
keys on those fields, and `ai_generated` follows them. The earlier figure was a miscount in the report,
not a different file.

**Grammar tags: 4** — the four `gram:` targets, each resolving EXACTLY on `grammar_point.key`
(`n3-nado`, `n3-moshikasuru-to-kamoshirenai`, `n3-donna-ni-koto-ka`, `n3-you-ni-iu`).
`sentence_grammar` 2,744 → 2,748. They were written by `persist()` itself (`grammar_keys`, exact key
first), so the ingest's idempotent tag pass reports `grammar-tags-written: 0` — it found all four
already there, which is what that pass is for.

Manifest: new **step 124** (this run, `--batches 30`), after 121–123 because that is the order the
live index went through. See §7.

## 3. The N3 relink over the new sentences — NOT applied, measured

`apply_orthographic_relinks.py` has no per-sentence scope: the only way to produce rows for new
sentences is `--derive`, which un-applies the WHOLE `orthographic_relinks_n3.json` table, re-derives
it from the index and rewrites it. That is the case the brief said to note rather than do.

Measured on a throw-away copy of the DB and a scratch copy of the table (nothing tracked touched):
a full `--derive --scope n3` today produces **487 rows = the committed 439 unchanged + 48 new, all
48 on the 97 new sentences**; 0 new rows on older sentences, 0 committed rows lost, the 37 holds
carried. Top records: 何も 4, 必ずしも 2, どんなに 2, 何でも 2, 所で, 共に, 常に, 其れでも.

Why it matters: of the 93 `vocab:` targets among the 97 rows, only **12** are carried by
`tokens[].vocab` today (the per-occurrence claim W05 counts). **42** more would be carried by those
48 relink links, and **39** are carried by neither (16 of them sit on a token the Dissector linked
to a sibling record; 23 are generated rows with no `match` record to inspect). That is why W05 moves
only a little in §6. Applying the 48 is a re-derive + check-D/exam-gate pass of its own.

## 4. Particle templates: the 201 explanation replacements

Tracked table: **`research/derived/repairs/particle_template_fixes.json`** — the 201 rows of
`research/derived/pending/particle_template_fixes.json` with `explanation_change: "replace"`
(and `function_pt_change: "none"`), copied verbatim with a header naming the source and the
selection. The pending file is untouched. **Not applied:** the 50 `withdraw` rows (their authored
replacements are being verified) and the 24 `function_pt` label overrides of verified rows (held
for sign-off).

Applier: **`scripts/apply_particle_template_fixes.py`** (new). Exact match on (slug / Layer-B key,
C-token position, particle surface, `old_explanation`); a value already equal to `new` counts as
applied; anything else is reported and never overwritten. Both layers:

| layer | changed | note |
|---|---|---|
| `db/corpus.sqlite` `localized_text` (particle, explanation, pt-BR) | **201** | 198 on sentences banked by step 121, 3 on batch-30's |
| `research/derived/mined_layerb_n3/batch-NN.json` `explanation_pt` | **201** | 29 files, `git diff` exactly +201 / −201 lines; `explanation_status` stays `template` |

Re-run: `201 already` in both layers, 0 changes. Because the Layer-B source is repaired, a replay's
ingest writes the new text directly and manifest **step 125** (this script) finds all 201 applied.

Replay gate: `validate_repairs_applied.py` gained `handle_particle_template_fixes`. The export
publishes `particles[]` without a position, so the handler re-proves the address from the token
side (the C token at the row's position is still that particle), then asserts a particle of that
surface carries `new_explanation` verbatim and no particle still carries `old_explanation`.
Plant proof (the handler called on the real export with one sentence altered in memory; nothing
written): control 0 FAIL → a row reverted to `old` caught `not-applied-old-still-present` → the new
text edited by one character caught `value-mismatch` → the particle's token surface moved caught
`address-does-not-resolve` → the sentence removed caught `address-does-not-resolve` → control 0
FAIL. 4 plants, 4 caught.

Export check: HEAD vs now, `particles` is the ONLY field that changed on any pre-existing sentence
(197 sentences, 198 particle entries); the other 3 rows are on new sentences.

### 4.1 Ten of the 201, before / after, for a human read

Every 20th row of the table (rows 0, 20, …, 180).

| # | sentence | rule | before | after |
|---|---|---|---|---|
| 0 | 彼は直に腹を立てる。 | `chunk-adverbial-copula-dropped` | を marca **直に腹** como o objeto direto de 立てる, ou seja, aquilo sobre o que a ação recai. | を marca **腹** como o objeto direto de 立てる, … |
| 20 | 食べるのにどうしてそんなに手間がかかるのか。 | `chunk-adverbial-copula-dropped` | が marca **そんなに手間** como o sujeito de かかる, isto é, quem faz ou de quem se diz o que o predicado exprime. | が marca **手間** como o sujeito de かかる, … |
| 40 | 彼の家族はかなり生活が苦しい。 | `chunk-adverb-dropped` | が marca **かなり生活** como o sujeito de 苦しい, … | が marca **生活** como o sujeito de 苦しい, … |
| 60 | ちょうど今はオフィスに誰もいない。 | `chunk-adverb-dropped` | は apresenta **ちょうど今** como o tópico da frase, … | は apresenta **今** como o tópico da frase, … |
| 80 | そして私はここにいて今なお生きています。 | `chunk-conjunction-dropped` | は apresenta **そして私** como o tópico da frase, … | は apresenta **私** como o tópico da frase, … |
| 100 | 僕はふと足を止めた。 | `chunk-adverb-dropped` | を marca **ふと足** como o objeto direto de 止める, … | を marca **足** como o objeto direto de 止める, … |
| 120 | 彼は年中喫煙をしている。 | `chunk-adverbial-noun-dropped` | を marca **年中喫煙** como o objeto direto de する, … | を marca **喫煙** como o objeto direto de する, … |
| 140 | 急に心臓が痛くなった。 | `chunk-adverbial-copula-dropped` | が marca **急に心臓** como o sujeito de 痛い, … | が marca **心臓** como o sujeito de 痛い, … |
| 160 | この部屋は良く日が当たる。 | `chunk-verbal-adverbial-dropped` | が marca **良く日** como o sujeito de 当たる, … | が marca **日** como o sujeito de 当たる, … |
| 180 | そして歴史は永久に変わった。 | `chunk-conjunction-dropped` | は apresenta **そして歴史** como o tópico da frase, … | は apresenta **歴史** como o tópico da frase, … |

The tail of each sentence ("…") is unchanged; only the quoted chunk moves. One for the reader to
weigh: **row 60** — ちょうど arguably modifies 今 itself (ちょうど今, "right now"), so the new quote is
narrower than the phrase rather than wrong; it is the audit's "shorter and still true" choice (§6 of
the audit report).

## 5. Exports, contracts, sync, gate

`export_corpus` → `export_course` → `export_readings` → `infer_shapes` → `build_schemas` →
`build_manifest` → `build_review_views` → `(cd prototype && npm run sync-data)` → `validate_all.py`.

* **Lessons did not move.** `git diff course/`: 7 files, 1 line each, every one a generated-date stamp
  (`2026-09-10` → `2026-09-23`); `validate_md_views`: 322/322 lesson `.md` byte-identical to a fresh
  render.
* corpus diff: `sentences/bank.json` (+97 sentences, 198 particle explanations), `sentences/INDEX.md`,
  `kanji/n1..n4.json` (example lists drawn from the larger bank), INDEX date stamps. contracts: record
  counts only (`sentence.schema.json` `records` 10,112 → 10,209). prototype: `sentences.json`,
  `kanji.json`, `_build.json`.
* **Gate: ALL HARD VALIDATORS PASS.** `validate.py` 10,209 sentences, 0 errors (1,643 warns, the
  pre-existing JMdict-common class). `validate_repairs_applied.py` **18,468 rows replayed clean**
  (18,170 + 97 register + 201 template), 21 checked skips, 0 FAIL. `validate_exam_level_gate` ALL OK;
  `integrity_audit` 0 FAIL; `validate_lesson_gating` unchanged; `validate_sentence_coverage` held.

### 5.1 Ratchets moved, each with its cause

| ratchet | movement | cause |
|---|---|---|
| `sentence_register_baseline.json` (register residue, shrink-only) | total 130 → **132**; **n4 29 → 31**, every other level unchanged | the two late rows with no register signal on their final bunsetsu, `register: null`, rule `no-signal`, carried from the derivation, never rounded up: `sent:gen-7f7950a6349b` どんなに会いたかったことか and `sent:tatoeba-10157623` ママはどこ？ (both computed n4) |
| `rebuild_baseline.json` quick | `corpus/grammar/INDEX.md` hash only | the recurring calendar reason: the re-export stamps `_Generated 2026-09-23` where the recorded bytes said 2026-09-10; the quick rebuild pins the build date to the committed file |
| `sentence_coverage_baseline.json` (W05) | §6 | re-recorded with the gate otherwise green |

## 6. W05 re-recorded

`validate_sentence_coverage.py --record`, after a green gate.

| (level, kind) | taught | below before → after | zero before → after |
|---|---|---|---|
| **`n3\|vocab`** | 1,596 | **162 → 160** | **57 → 51** |
| **`n3\|grammar`** | 132 | **35 → 34** | **1 → 0** |
| n5/n4 vocab, n5/n4 grammar, n1 vocab | — | unchanged | unchanged |

N3 grammar now has **no point without a sentence**. N3 vocabulary moved less than 97 rows suggest;
§3 has the reason and the measured size of the rest (42 targets behind the un-applied relink, 39
behind the Dissector's sibling choice).

## 7. Manifest and full replay

**129 steps / 93 enabled** (was 127 / 91). New: **124** the batch-30 ingest, **125**
`apply_particle_template_fixes.py`; furigana 124 → **126**, the three family builders 125–127 →
**127–129**, still last. Both tables registered in `validate_repairs_applied.py`
(`sentence_register.json` was already; `particle_template_fixes.json` is new).
`scripts/validate/README.md`'s step-number sentence brought up to date (it still said furigana 121,
families 122–124).

### 7.1 Full-mode replay

`validate_index_rebuildable.py --keep` (no record first, so a newly-broken file could not be
recorded away): **ran clean to the end, 790 files compared in 768 s**. It now takes ~13 minutes, up
from W13's ~90 s estimate in the README; the harness's 600 s command wrapper killed the shell but
not the Python, which finished. Result: **no file newly stopped rebuilding and none started**; the
only findings are **18 held entries whose rebuild bytes moved**, each for a reason this run created:

* `corpus/sentences/bank.json`, `corpus/sentences/INDEX.md` — the 97 sentences and the 201 fixed
  explanations;
* `corpus/kanji/n1..n4.json` — kanji example lists drawn from the larger bank;
* `corpus/INDEX.md`, `corpus/{families,grammar,kanji,vocab}/INDEX.md`, `course/INDEX.md`,
  `course/{n3,n4,n5,pre-n5}/INDEX.md`, `course/manifest.json`,
  `course/vocab_disambiguation_review.json` — the generated-date stamp (2026-09-10 → 2026-09-23),
  the recurring calendar reason.

**Replay fidelity for THIS run's changes, checked on the kept scratch tree:** the rebuilt
`bank.json` carries all 97 new sentences with **0 fields differing** from the committed export, and
**all 201** fixed explanations. (The rest of the bank differs on older sentences for the pre-existing
reasons the baseline already holds, `tr-untracked` and friends — unchanged by this run.)

Side effect, as W13 open item 7 predicted: step 110 (`migrate_grammar_merge.py`) rewrote the tracked
`research/derived/grammar_merge_ledger.json` with the scratch tree's values. It is a replay artefact,
not a decision, and was restored to its HEAD content after the replays.

**`--record`: re-recorded.** 790 compared, **568 held / 222 byte-identical — both unchanged**; 0
entries added, 0 dropped, 0 causes changed, 18 hashes moved (the list above). Quick mode: 1 hash
moved (`corpus/grammar/INDEX.md`, calendar). A final `validate_all.py` after both records: **ALL
HARD VALIDATORS PASS**.

---

## 8. Not done, handed on

1. **The N3 relink over the 97 (§3).** The script cannot scope to new sentences; a full
   `--derive --scope n3` is measured to add exactly 48 links, all on the new sentences, and to leave
   the 439 applied links and 37 holds untouched. It needs its own check-D / exam-gate pass before it
   lands, and it is where most of the remaining W05 N3 movement is (42 of the 93 targets).
2. **39 of the 93 vocab targets are not carried at token level** by the Dissector (16 on a token
   linked to a sibling record). The verifier proved the word is in the sentence; the per-token
   linker disagrees about which record it is. A homograph/link unit, not an ingest defect.
3. **The 50 `withdraw` rows and the 24 verified-label overrides** of
   `research/derived/pending/particle_template_fixes.json` stay in `pending/`, as instructed.
4. **The two new residue sentences** (どんなに会いたかったことか, ママはどこ？) join the register
   authoring queue (`residue` in the register table), excluded from the speaking path meanwhile.
5. **The full replay now takes ~13 minutes** (768 s measured), not the README's ~90 s. Anything that
   runs it under a 10-minute command timeout will be killed mid-run and look like a failure.
6. **STATE.md was not touched** by this run.

## 9. Files

New: `scripts/apply_particle_template_fixes.py`, `research/derived/repairs/particle_template_fixes.json`,
this report. Changed: `scripts/derive_sentence_register_v2.py` (`--w13-source`),
`scripts/validate/validate_repairs_applied.py` (handler + registry), `scripts/validate/README.md`
(step numbers), `research/derived/rebuild_manifest.json` (steps 124–125, renumbered),
`research/derived/repairs/sentence_register.json` (10,209 rows),
`research/derived/mined_layerb_n3/batch-01..28,30.json` (201 `explanation_pt`), the three ratchets
(`sentence_register_baseline.json`, `sentence_coverage_baseline.json`, `rebuild_baseline.json`),
and the regenerated `corpus/`, `course/` (date stamps only), `contracts/`, `research/review/`,
`prototype/app/data/`. Nothing under `research/derived/pending/` was modified.
