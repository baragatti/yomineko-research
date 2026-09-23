# U1 — second particle table, and the N3 relink over the 97 late sentences

_Status: DONE. DB writer: this run. Gate green, W05 re-recorded, full replay: see §6._

Follows `research/reports/w13_finish_report.md` §8 items 1 and 3. Nothing here authors Japanese or
pt-BR: every string comes from a tracked table that went through an independent verifier.

## 0. Order of work

| # | step | state |
|---|---|---|
| 1 | tracked table from `pending/particle_template_fixes_second.json` (74 rows) | ☑ §1 |
| 2 | `apply_particle_template_fixes.py` extended to a second table; applied, DB + Layer-B | ☑ §1 |
| 3 | sentence 169401 structure paragraph | ☑ §2, not changed (condition not met) |
| 4 | N3 relink over the 97: derive, diff, apply the new rows, hold what breaks a ratchet | ☑ §3 |
| 5 | exports → contracts → sync → gate | ☑ §4 |
| 6 | W05 re-record | ☑ §5 |
| 7 | full-mode replay + `--record` | §6 |

Baseline at `e7ff05cd`: bank 10,209; replay gate 18,468 rows; manifest 129 steps / 93 enabled.

## 1. The second particle table (74 rows)

Tracked table: **`research/derived/repairs/particle_template_fixes_second.json`**. The pending file (removed from `pending/` once applied, in git history)
carries `key`, `position`, old/new label and explanation and the verifier verdict; it was joined by
(key, position) onto `pending/particle_template_fixes.json` for `slug`, `batch`, `surface`,
`function_type` and `rule` (74/74 joined, 0 old-value disagreements), and onto the live DB for
`ordinal` (see the handler below). `pending/particle_template_fixes.json`, `.authored.json` and `.verdict.json` stay: the first tracked table names them as its source.

| kind | rows | changes | verifier |
|---|---|---|---|
| `withdrawn-authored` (て inside a fixed compound postposition: について, として, にとって, によって, から〜にかけて, を通して …) | 50 | explanation AND label | ok / corrected |
| `label-override` (verified rows whose label was still the raw pair modal) | 24 | label only | ok / corrected |
| total | **74** | 50 explanations, 74 labels | 60 ok, 14 corrected |

Applier: `scripts/apply_particle_template_fixes.py` now reads per-field change flags
(`explanation_change`, `function_pt_change`), exact-matches the `old_*` value of every field a row
changes, and sets the Layer-B `explanation_status` / `function_status` from the verifier (ok →
`verified`, corrected → `corrected`). The first table runs through the same code unchanged: `--check`
on it reports 201 already, 0 to do.

| layer | changed | re-run |
|---|---|---|
| `db/corpus.sqlite` `localized_text` (particle, function + explanation, pt-BR) | **74 particles** | 74 already |
| `research/derived/mined_layerb_n3/batch-NN.json` | **74 particles** in 25 files | 74 already |

Export: `particles` changed on exactly **73 sentences / 74 particle entries**, no other field on them.

Replay handler: `handle_particle_template_fixes_second`. The first table's handler proves a row by
"no particle still carries the old text"; a LABEL repeats inside one sentence (6 of the 74 share their
old value with a sibling particle), so this table records `ordinal`, the particle's index in the
exported `particles[]` (particle-id order, which is token order), and the handler checks the C token
at the row's position and the particle at `ordinal`. Plant proof (in memory, nothing written): control
0 FAIL → label reverted on a label-only row `not-applied` → explanation reverted on an authored row
`not-applied` → label edited by one character `value-mismatch` → particles reordered
`address-does-not-resolve` → sentence removed `address-does-not-resolve` → control 0 FAIL. **5/5 caught.**

Ten rows (every tenth), for a human read:

| # | sentence | kind | label before → after | new explanation |
|---|---|---|---|---|
| 0 | 宗教については何の意見も持っていない。 | authored | conectiva (forma て) → locução 〜について | て fecha a locução について (sobre, a respeito de) e prende 宗教 ao resto: religião é o tema em que não há opinião formada. |
| 10 | 彼はその問題について論文を書いた。 | authored | → locução 〜について | … prende その問題 ao resto: o artigo dele tem essa questão como tema. |
| 20 | 姉は大学の先生の助手として働いている。 | authored | → locução 〜として | … prende 助手 a 働いている: é no cargo de assistente que ela trabalha. |
| 30 | 価格は需要によって変わる。 | authored | → locução 〜によって (conforme) | … prende 需要 a 変わる: o preço acompanha a demanda. |
| 40 | 食べ物は生物にとって必要なものです。 | authored | → locução 〜にとって | … prende 生物 ao resto: é para os seres vivos que a comida é necessária. |
| 50 | 彼は教師としては、可もなく不可もなくといったところです。 | authored | → locução 〜として | … o julgamento que vem depois vale para esse papel, o de professor. |
| 60 | 彼らは順番に歌を歌った。 | label | destino/direção → に que forma advérbio | (unchanged) |
| 70 | この記事って何についてなの？ | authored | → locução 〜について | … o que se pergunta é justamente sobre o que a matéria trata. |

## 2. Sentence 169401: structure paragraph NOT changed

The brief: fix it only if the verifier note in `pending/particle_template_fixes.verdict.json` shows
it contradicts the を通して reading. The verdict for `169401#3` is `{"ok": true}` and nothing else: no
problem, no note, no mention of the structure paragraph (the verifier did name a structure paragraph
elsewhere, e.g. the で row it corrected, so the silence is a verdict, not an omission). The condition
is not met, so no repair row was written.

For the reader, the paragraph as it stands:

> A primeira parte 山を通して usa を com 通す na forma て, encadeando a ideia de atravessar a montanha.
> Depois vem o núcleo トンネルを通した, …

Its meaning ("atravessar a montanha") agrees with the new particle explanation ("o túnel foi aberto
atravessando a montanha"). Its FRAMING ("encadeando") still describes a て-chain, which the author's
own `why` in `particle_template_fixes.authored.json` rejects ("não é ação separada, é a metade direita
da posposição を通して"). A wording point for the teacher review, not a contradiction the verifier found.

## 3. The N3 relink over the 97 late sentences

**Derivation.** `apply_orthographic_relinks.py --derive --scope n3` on a copy of the DB and a scratch
copy of the table: **487 rows = the committed 439 unchanged + 48 new, 0 lost, 0 changed, the 37 holds
identical**; all 48 new rows sit on the 97 late sentences (42 `run-reading`, 6 `kana-exact`). Same as
w13_finish §3 measured.

**Where they live.** Step 122 applies `orthographic_relinks_n3.json` before the late sentences exist
(they arrive at step 124), so the 48 rows cannot go in that table: a replay would fail on "no such
sentence". They are a third table, **`research/derived/repairs/orthographic_relinks_n3_late.json`**,
applied by a new step 127 with `--table`, registered in `validate_repairs_applied.py` with the same
handler as the other two. Do not `--derive` it on its own; re-derive the N3 table and diff again.

**Check D.** With all 48 applied, `validate_lesson_gating` D stayed at the frozen baseline exactly
(624 pairs, 178 above level, **148 over budget**, 304 new kanji, 227 new vocab). None of the 97
sentences is in a lesson. Nothing had to be held for D.

**The gate held 29 of them anyway: integrity_audit's sentence-level ratchet.** With all 48 in,
`integrity_audit` failed: `sentence.level ≥ component levels — 715 below (ceiling 703)`. Measured
the way the audit measures it, before and after: **688 → 715, +27 sentences, 0 cleared**. Each of the
27 is a late sentence filed n4 or n5 (`sentence.level` is computed once, at ingest, from what the
Dissector linked) that the relink gives an N3 record. 26 of the 27 are generated rows written FOR
that N3 target (所で, 其れでも, どんなに, 何も …), so the stored level is the stale thing, not the link.
But the ceiling is shrink-only and re-deriving sentence levels is a separate reviewed decision (both
`apply_orthographic_relinks.py` and `integrity_audit.py` say so), so the 29 links on those 27
sentences went to the table's `held[]`, each with its reason, and were un-applied with the script's
own `undo()` (58 writes: 29 tokens + 29 `sentence_vocab` rows). Re-measured: 688, unchanged from HEAD.

| | rows |
|---|---|
| derived, new | 48 |
| **applied** | **19** (19 sentences; 共に, 必ずしも ×2, 常に, 実に, これ等, 何でも, 其処で, 行けない, 要するに, こんなに, 堪らない, 何も ×2, 不, 全, 御, 級, 上) |
| **held (level ratchet)** | **29** (27 sentences; 何も ×2, どんなに ×2, 所で, 其れでも, ざっと, 男の人, 今にも, 何で, とんでも無い, 所が, 今に, 何故なら, 思わず, 其れとも, 何時までも, 頻りに, 一度に, 何時でも, 急に, 何とか, 何か, 若しも, 何処か, 別に, 後) |

Releasing the 29 is one decision: re-derive `sentence.level` for those 27 sentences (all would go
to n3), then re-apply this table with `held[]` moved to `rows[]`.

Export: `tokens` and `vocab` changed on exactly the 19 sentences, nothing else.

## 4. Exports, contracts, sync, gate

`export_corpus` → `export_course` → `export_readings` → `infer_shapes` → `build_schemas` →
`build_manifest` → `build_review_views` → `(cd prototype && npm run sync-data)` → `validate_all.py`.

* **Lessons did not move.** Rendered text of all **789** files under `course/` compared with HEAD
  (CRLF-normalised): **0 differ**; `validate_md_views` 322/322 lesson `.md` byte-identical to a fresh
  render; **0** of the 92 touched sentences is referenced by any course file, by slug or by its jp.
* corpus diff: `sentences/bank.json` only (92 sentences: 73 particles, 19 tokens + vocab). contracts:
  `_shapes.json` / `manifest.json` counts (`vocab[].link_rule` present 58,813 → 58,832 and friends).
  prototype: `sentences.json`, `_build.json`. review views: `sentences/n5.md` + date stamps.
* **Gate: ALL HARD VALIDATORS PASS.** `validate_repairs_applied.py` **18,561 rows replayed clean**
  (18,468 + 74 + 19), 21 checked skips, 0 FAIL. `integrity_audit` 0 FAIL (the sentence-level WARN at
  688 ≤ 703); `validate_exam_level_gate` ALL OK; `validate_lesson_gating` D 0 FAIL.

## 5. W05 re-recorded

`validate_sentence_coverage.py --record` with the gate otherwise green:

| (level, kind) | taught | below | zero |
|---|---|---|---|
| **`n3\|vocab`** | 1,596 | **160 → 157** | **51 → 48** |
| everything else | — | unchanged | unchanged |

w13_finish measured 42 targets behind the 48 links; the 29 held links carry most of that.

## 6. Manifest and full replay

**131 steps / 95 enabled** (was 129 / 93). New: **126** `apply_particle_template_fixes.py --data
…_second.json`, **127** `apply_orthographic_relinks.py --scope n3 --table …_n3_late.json`; furigana
126 → **128**, the three family builders → **129–131**, still last. Step 124's note no longer says the
relink is not re-derived for its rows. `scripts/validate/README.md`'s step sentence brought up to date.

**Full-mode replay** (`validate_index_rebuildable.py --keep`, no record first): 790 files compared in
461 s. **One finding: `corpus/sentences/bank.json`, a held entry whose rebuild bytes moved**, which is
this run's own change. Nothing newly stopped rebuilding and nothing started. Replay fidelity was
checked on the kept scratch tree: **74/74** particle rows rebuilt with the new label and explanation,
**19/19** applied relinks present, **29/29** held relinks absent, and **0** of the 92 touched
sentences differ between the rebuilt and the committed export.

**`--record`:** 568 held entries (same count as before), 1 hash moved (`bank.json`). Step 110 rewrote
`research/derived/grammar_merge_ledger.json` again (the replay side effect w13_finish §7.1 describes).
It was restored to HEAD after each replay. A final `validate_all.py` after the record passed:
**ALL HARD VALIDATORS PASS** (quick mode: 4 files held at the recorded bytes).

## 7. Open items

1. **29 held relinks** (§3): release with a scoped `sentence.level` re-derivation for 27 sentences.
   Owner / reviewed decision; W05 `n3|vocab` has most of its remaining N3 movement there.
2. **169401's structure paragraph** frames 山を通して as a て-chain (§2). The verifier did not flag it;
   worth a line in the teacher review.
3. The 24 label corrections replaced labels the verifier had accepted before; the pending note records
   the owner sign-off of 2026-09-23 that this run relied on.
