# W13 apply — the mined N3 sentences enter the bank

_Status: DONE. DB writer: this run. Gate green, full replay green and re-recorded. NOT COMMITTED (this run was told to touch no git state)._

4,197 real Tatoeba rows + 26 generated, with the W13b Layer-B (batches 01–29: token glosses,
particle explanations, structure paragraphs, every slot filled and verified), are now bank
sentences. The bank went **5,889 → 10,112**.

Nothing here authored Japanese or pt-BR. Every string came from a tracked table:
`research/derived/n3_mined/{accepted,generated}.json` (Layer-A jp/en + Layer-B pt),
`research/derived/mined_layerb_n3/batch-*.json` (the dissection content) and
`research/derived/repairs/sentence_register.json` (register + rule per key).

## 0. Order of work

| # | step | state |
|---|---|---|
| 1 | trial ingest of one Layer-B batch on a DB copy, `validate.py` + the sentence gates | ☑ §1 |
| 2 | real ingest, batch by batch, atomic | ☑ §2 |
| 3 | `sentence_grammar` tags for every `gram:` target | ☑ §3 |
| 4 | the deferred N3 orthographic relink, with the function-word rule fix | ☑ §4 |
| 5 | W05 ratchet re-record | ☑ §5 |
| 6 | W28 mechanical half (card examples) | ☑ §6 — measured, apply left with a reason |
| 7 | exports → contracts → sync → gate → full replay | ☑ §7 |
| 8 | 30 rendered sentences for the Fable read | ☑ §8 |

---

## 1. The trial, and the four things it broke

One batch (`batch-01.json`, 150 rows) on a copy of `db/corpus.sqlite`. It failed, which is the
point of running it. Each fix below is quoted with what it cost to find.

**1.1 `persist()` committed per sentence, so "rollback" was a word with nothing behind it.**
`ingest_mined_stages.py` already documented this ("the first *dry run* of this script wrote all 324
rows") but had only worked around it with a pre-flight. `persist_dissection.persist()` now takes
`commit: bool = True`; the ingest passes `commit=False` and owns the transaction, so a Layer-B batch
is ONE transaction. The default is unchanged, so `apply_escalated_sentences.py` and every other
caller keep the old semantics. The trial proved it: batch-01 aborted on one sentence and printed
`ROLLED BACK batch-01.json (149 rows discarded)` — 149 written rows discarded, not left behind.

**1.2 The Dissector spelled the same っ two ways, and invariant I3 caught it.**
`sent:tatoeba-11912828` 可哀想なことに、事故で足を折っちゃったんだ。 failed `I3 romaji != concat(token
romaji)`: the sentence line said `…ashiooc**ch**attanda`, the tokens said `…ashioo**tch**attanda`.
Cause: `dissect._GEMINATE_FIRST = {"c": "t"}` implemented traditional Hepburn's っち = "tchi" for a
っ that ENDS a token, while the sentence-level romanizer (jaconv over the whole corrected kana) and a
token-INTERNAL っち both say "cch". The corpus already had a convention and it was jaconv's — 30 bank
sentences carry "cch" (めっちゃ, サンドイッチ) and all five pre-existing っ|ch token boundaries are
stored `…c` + `ch…`, which means the remap was also making a replay REWRITE those five tokens. The
map is now empty; the two romanizations agree, no stored romaji changes, and replay fidelity is
restored for the five. **3 of the 4,223 rows hit this**; a pre-flight over all 4,223 now reports
I1 0 / I2 0 / I3 0. Whether the whole corpus should move to "tchi" is a romaji-convention decision
for its own unit, not something to settle inside a sentence ingest.

**1.3 `validate.py --db <copy>` was silently validating the REAL corpus.**
The trial's first `validate.py --db trial.sqlite` reported 5,889 sentences — the copy had 6,039.
`scripts/dbtarget.take_flag()` REMOVES `--db` from `argv` so a script's own argparse never sees it;
`validate.py` imports `dissect`, which resolves `db_target()` at module import and consumed the flag,
so validate.py's own `db_target()` found nothing and fell back to the default. A trial run that
cannot fail is worse than no trial run. `take_flag` now caches the value per flag, so every
`db_target()` / `out_root()` in one process answers the same way — which is what every caller already
assumed. Re-run: 6,039 sentences, 0 errors.

**1.4 The ingest had no way to read the register, tag grammar, or record the campaign.** Four flags
added, documented in the script's own docstring:

| flag | why |
|---|---|
| `--register-table PATH` | W31 filed these 4,223 rows' `register`/`register_rule` as **asserted deferrals** before they were banked. The ingest reads that table; a row with no entry is **refused, not defaulted** — a defaulted `neutral` passes the speaking-path filter silently, which is the failure the field exists to prevent. Lookup is by SLUG, so it reads either generation of the table (pre-ingest `tatoeba-<id>` keys, post-ingest `sent:` slugs). |
| `--provenance-source NAME` | `sentence.source` is the campaign (`w13:n3-exemplification`); `jp_source` stays the Layer-A origin (`tatoeba` / `ai-generated`). |
| `--batches 1,2,3` | ingest a subset — how the trial ran, and how a stopped run resumes. |
| grammar targets | a row whose `targets[]` names `gram:<key>` gets a `sentence_grammar` row. Resolution is EXACT on `grammar_point.key`: `persist_dissection.find_grammar()`'s `LIKE` fallback would tag `n3-koto-da` for `n3-koto`. |

A **pre-flight over every row runs before any write**: jp-vs-raw-Tatoeba, a Layer-B batch exists,
a register row exists, every `gram:` target resolves. Any failure refuses the whole run.

**Trial result on the copy** (batch-01, 150 sentences):

| gate | result |
|---|---|
| `validate.py --db <copy>` | 6,039 sentences, **0 errors**, 1,291 warns (+8, all `lemma not in JMdict-common`) |
| `validate_sentence_coverage.py --root <fixture>` | 3,445 taught items, **ALL OK (ratchet held)** |
| `validate_sentence_register.py --root <fixture>` | derivation **0 mismatches**; only the residue ratchet grew (n1 4→5, n3 18→19) — the 2 `no-signal` rows in this batch |
| `validate_lesson_gating.py --root <fixture>` check D | 148/624 over the i+1 budget — **unchanged** |

---

## 2. The real ingest

`ingest_mined_stages.py --apply --source accepted.json --source generated.json --layerb
research/derived/mined_layerb_n3 --tag n3-exemplification --provenance-source w13:n3-exemplification`

Pre-flight clean on all 4,223 rows. **29 batches, 28 × 150 + 1 × 23, 4,223 ingested, 0 invariant
failures, 0 rollbacks, 0 blocklisted, 0 refused.**

| | value |
|---|---|
| sentences | 5,889 → **10,112** |
| C tokens written | 36,282 |
| particles written | 10,257 (exactly W13b's count) |
| `sentence_vocab` edges | 16,702 |
| `ai_generated` | 0 on 4,197 Tatoeba rows, 1 on 26 generated |
| `needs_review` | 1 on all 4,223 |
| `layer` / `created_by` | `B` / `ai` on all |
| `tags` | `["mined", "n3-exemplification"]` |
| `source` | `w13:n3-exemplification` |

**Register, taken from the table, never derived here:** neutral 2,538 · polite 1,069 · casual 491 ·
formal 70 · archaic 1 · **NULL 54** (rule `no-signal`, `needs_review`) — identical to the table's own
counts, row for row.

**Level is computed, not asserted.** `persist_dissection.computed_level()` files a sentence at the
maximum level of the vocab and kanji it contains, so the mined "N3" set lands **n3 2,045 · n1 1,280 ·
n2 865 · n4 21 · n5 12**: a sentence mined to exemplify an N3 word is filed N1 when it also contains
one N1 word. That is the rule every other bank sentence already obeys and this unit did not change
it, but it is why the register residue ratchet moves at n1 and n2 as well as n3 (§5).

---

## 3. Grammar targets

128 `gram:` targets over 117 accepted rows and 11 generated ones, across **63 distinct grammar
points**. All 63 resolve EXACTLY against `grammar_point.key`; none is deprecated. Written as
`sentence_grammar (sentence_id, grammar_id, NULL)` — the shape the existing tagger uses
(`usage_note_pt` is NULL on all 2,616 pre-existing rows). Table total **2,616 → 2,744**.

The tag pass is idempotent and re-runs over rows that were already banked, so a re-run repairs a
partial ingest instead of skipping it.

**One consequence, and it is the reason a re-derivation was needed (§7).** `register` is derived in
part from the grammar points a sentence is tagged with. Before the ingest the W13 rows had no
`sentence_grammar` edges, so the derivation saw no grammar signal for any of them (0 of 4,223 carry
rule `grammar-register`; 58 of the 5,889 bank rows do). After the tagging, three sentences tagged
`n3-nanka` (a point the registry files `casual`/`colloquial`) derive `casual` / `grammar-register`
where the table said `neutral` / `plain-predicate`:

| slug | jp | was | now |
|---|---|---|---|
| `sent:tatoeba-1490034` | 雪なんか嫌いだ！ | neutral/plain-predicate | casual/grammar-register |
| `sent:tatoeba-202028` | テレビなんかなくてすむ。 | neutral/plain-predicate | casual/grammar-register |
| `sent:tatoeba-3507379` | 悲しくなんかない。 | neutral/plain-predicate | casual/grammar-register |

The derivation is the authority (`validate_sentence_register.py` check B re-derives the whole bank on
every gate run), so the table was regenerated and the three re-applied — see §7.1.

---

## 4. The N3 orthographic relink (W12's deferred half)

W12 measured 1,694 N3 links over 334 records and deferred them, "mostly from linking every で to the
N3 particle record". Re-derived on today's tree — **after** the ingest, because the derivation reads
current coverage to decide which records are short — the honest number is much smaller, for two
reasons that both matter:

* the 4,223 new sentences already exemplify most of what was short, so far fewer N3 records are under
  the ≥3 floor at all;
* the fifth guard (below) refuses the で class by rule.

**`apply_orthographic_relinks.py` gained `--scope` and `--table`** rather than being forked: one
rule, two tables. Two tables because the REPLAY order needs them apart — the N5/N4 table applies at
manifest step 114, and the N3 table cannot, since none of its sentences exist at that point.

### 4.1 The rule fix: no bare one-kana function word

> A SINGLE token Sudachi tags a particle or an auxiliary is claimed only when the kana form it
> matches on is **two kana or more**.

This is the measure the `kana-function-word` rule already applied to a POS-mismatched link, extended
to the single-token `kana-exact` rule. It separates the two cases that look alike:

* **kept** — だけ (43 links), くらい (48), ばかり (29), ほど (21), など (15), ずつ (9): words a learner
  meets AS words, 2–4 kana, all of them in the applied N5/N4 table and all wanted;
* **refused** — で, one kana, the plain case particle `vocab:2028980`, which the course files at N3.

A one-kana particle spelled で is not an ORTHOGRAPHIC variant of anything: it is spelled exactly as
the record is, and the reason the dissector never linked it is that its per-token linker deliberately
leaves case particles alone. Re-linking it is a decision about whether particle occurrences count
towards a vocabulary floor at all, which belongs to whoever sets the floor.

**The guard is a strict no-op on the applied N5/N4 table** — 0 of its 663 rows match it, and
`--check` re-verifies all 663 against the post-ingest index with 0 writes. It was NOT extended to
`prefix`/`suffix`, because that measure would also drop 24 applied N5/N4 rows (個/こ the counter,
ご/御) which are legitimate.

**Honest note on falsifiability:** the guard fired **0 times** in this derivation, because で now has
exactly 3 sentences from `token.vocab_id` and is therefore no longer under the floor — it is not a
target, so the run never reaches the guard. The guard is what stops it coming back the day that count
moves; it is not what removed で today.

### 4.2 What was applied

| | value |
|---|---|
| derived | **476** links over **47** records |
| held (§4.3) | **37** rows / 36 (sentence, vocab) keys |
| **applied** | **439** links (`run-reading` 256, `kana-exact` 183) over **46** records — `token.vocab_id` 439 written, `sentence_vocab` 412 inserted |
| N3 records lifted over the ≥3 floor | **29** |
| lessons whose rendered sentence list changed | **0** |

### 4.3 The hold list: check D must not grow, so 37 links did not land

Check D freezes FOUR counters, not one, and applying all 476 moved two of them: pairs over the i+1
budget **148 → 159** (+11) and pairs carrying any unknown vocabulary **227 → 253** (+26). A link is
not free: a bank sentence that gains a vocabulary edge gains it for every lesson that RENDERS that
sentence. Raising a frozen curriculum ceiling to make a mechanical relink fit would spend a
guarantee on a link nobody asked for, so **every link behind either movement is held**, listed with
the pair it would break, in the table's own `held[]` — 37 rows over 36 (sentence, vocab) keys:

* **9 keys / 10 rows** put a rendered pair over its budget (the table below);
* **27 keys** put the FIRST unknown vocabulary item into a pair that had none.

A hold is addressed by (sentence slug, vocab slug) and survives `--derive`, which re-reads `held[]`
before it un-applies anything, so a re-derivation cannot quietly re-admit one. That mechanism had to
be fixed mid-run: the first version rebuilt `held[]` only from the rows the derivation produced that
day, and a `--derive` over a half-applied index found 206 candidates instead of 476 and silently cut
a 37-entry hold list down to 6. Holds are now carried forward whether or not today's derivation
reproduces them.

| held link | breaks |
|---|---|
| `sent:tatoeba-9974818` お → `vocab:2826528` 御 | les:n4-dar-receber-04, budget 2 → load 3 |
| `sent:tatoeba-236843` お → `vocab:2826528` 御 (×2 occurrences) | les:n4-keigo-02, budget 2, load 2→3 |
| `sent:gen-59401317dba3` お → `vocab:2826528` 御 | les:n4-keigo-05, budget 2, load 2→3 |
| `sent:tatoeba-5078` お → `vocab:2826528` 御 | les:n5-desu-wa-01, budget 1 → load 2 |
| `sent:tatoeba-182472` 急に → `vocab:2269050` 急に | les:n4-forma-simples-07, budget 2 → load 3 |
| `sent:gen-d3bba30db3a5` 少しも → `vocab:1348900` 少しも | les:n4-passiva-04, budget 2, load 2→3 |
| `sent:tatoeba-82538` 行けない → `vocab:1000730` 行けない | les:n5-conectando-01, budget 1, load 1→2 |
| `sent:tatoeba-1057336` なんで → `vocab:1611020` 何で | les:n5-desu-wa-04 + les:n5-particulas-lugar-03, budget 1 → load 2 |
| `sent:tatoeba-778974` なんで → `vocab:1611020` 何で | les:n5-particulas-lugar-03 + les:n5-perguntas-04, budget 1 → load 2 |

The 27 backlog holds are spread over the same small set of records: 御/お 11, 行けない 7, 何で 5,
何か 5, 少しも 2, それでは 2, and one each of 何とか, 急に, どんなに, それとも, ずいぶん.

With every hold applied, check D reads **178 above level · 148/624 over the i+1 budget · 304 with
new kanji · 227 with new vocab — all four counters exactly at the frozen baseline, `D 0 FAIL`.**
The 37 held links are the W14 lesson-sentence re-selection's business: W14 decides which sentence a
lesson shows, and once a lesson stops rendering these sentences the links can land.

---


---

## 5. W05 — the ratchet re-recorded

`validate_sentence_coverage.py --record`, run with the gate otherwise green. Per (level, kind),
`below` = under the floor (vocab ≥ 3 sentences, grammar ≥ 5), `zero` = no sentence at all:

| (level, kind) | taught | below before → after | zero before → after |
|---|---|---|---|
| `n3\|vocab` | 1,596 | 1,571 → **162** (−1,409) | 1,461 → **57** (−1,404) |
| `n3\|grammar` | 132 | 67 → **35** (−32) | 17 → **1** (−16) |
| `n5\|vocab` | 703 | 19 → **18** (−1) | 14 → 14 |
| `n4\|vocab` | 651 | 19 → 19 | 10 → 10 |
| `n4\|grammar` | 212 | 16 → 16 | 0 → 0 |
| `n5\|grammar` | 150 | 15 → 15 | 0 → 0 |
| `n1\|vocab` | 1 | 0 → 0 | 0 → 0 |

**N3 vocabulary goes from 1.6% at the floor to 89.8%, and from 8.5% exemplified at all to 96.4%.**
N3 grammar goes from 17 points with no sentence to **one**. Nothing grew anywhere.

The other two ratchets this unit had to move, each re-recorded with its cause in the file itself:

* **`sentence_register_baseline.json` residue 76 → 130** (n1 4→16, n2 6→15, n3 18→51; n4 and n5
  unchanged). These are the 54 mined sentences whose final bunsetsu carries no predicate and no
  lexical or grammatical marker — `register: null`, rule `no-signal`, `needs_review` — carried in
  from the tracked table, never rounded up to `neutral`. They spread across n1/n2/n3 because
  `sentence.level` is the max level of the words a sentence contains (§2).
* **`integrity_audit.SENTENCE_LEVEL_FALLBACK_CEILING` 585 → 703.** `sentence.level` is computed once
  at persist time from what the Dissector linked; a link added afterwards (the relink, or
  `build_sentence_vocab`'s lemma pass) can name a higher-level record and leave the stored level
  below it. Re-deriving every sentence level is a separate reviewed decision with its own export
  diff — both `apply_orthographic_relinks.py` and `build_sentence_vocab.py` say so at length — and
  not a side effect of a sentence ingest.

### 5.1 The exam ceilings, and the measurement that names their cause

`validate_exam_level_gate.py` grew by **40 items over five families** (n4_grammar_form 50→70,
n4_sentence_order 7→18, n5_context_fill 229→230, n5_grammar_form 35→40, n5_sentence_order 90→104).

The cause was measured, not guessed. The gate reads `tokens[].vocab` and `grammar[]` of the bank
sentence an item's stem comes from. Rebuilding the same export with the 439 relink links **stripped
from `bank.json` and nothing else changed**, the gate is **ALL OK** — so none of the growth comes
from the 4,223 ingested sentences or from their 128 grammar tags (the grammar dimension reads 174
either way). It is the relink, and the links are correct: the sentence really does contain 御/お,
何か, 急に, 何で, 行けない, 何も, どんなに.

What the gate is reporting is therefore a real curriculum fact it could not see before — an N5 exam
item built on a sentence that carries an N3 word — and the repair is the one
`exam_level_baseline.json`'s own `_why` already names: **W18's builder regeneration from level-clean
material**, whose plan row depends on the W13 apply for exactly this reason. The ceilings are raised
with that written into the file, plus the work list: 御/お 23 items, 何か 21, 為る 20, 急に 12,
何で 11, 行けない 10.

**Why these were not held the way the check-D links were.** Check D is a curriculum guarantee about
what a learner is shown in a lesson, and 24 links were held to keep it frozen (§4.3). The exam
ceilings are debt counters over banks that W18 regenerates wholesale in the next unit; holding
another ~40 links to protect a number that is about to be rebuilt would trade real coverage for a
number with a week to live. Both calls are recorded so either can be reversed.

## 6. W28's mechanical half — measured, and the apply is NOT cheap

| | before | after |
|---|---|---|
| vocabulary SRS cards that can show an example | 1,749 / 2,951 (59.3%) | **2,901 / 2,951 (98.3%)** |
| distinct vocabulary records reachable from a bank sentence | 1,793 | **3,056** |

By level after: pre-N5 24/24, N5 684/688, N4 641/643, **N3 1,552/1,596 (97.2%, was ~8%)**.

**But nothing was written for W28, and that is the finding.** "A card can show an example" is a
MEASURE over the bank, not a stored field: `srs.introduces_cards[]` carries `deck`, `item`,
`card_types` and (since W27) `production_key`, and no example slot at all. So the mechanical half
this unit was asked to do "if cheap" is already done by the data — the number moved by 1,152 with
no script — while the half that remains is a new field on the card contract, its schema, its
generation rule (which sentence, and the cloze span), an extension to `validate_card_content.py`,
and the renderer. That is a unit, not a side errand, and it is left as one.

## 7. Exports, contracts, sync, gate, replay

Order run, and it matters: `export_corpus` → `export_course` → `infer_shapes` → `build_schemas` →
`build_manifest` → `build_review_views` (which must come after `build_manifest`, W38's finding) →
`prototype && npm run sync-data` → the gate.

### 7.1 The register table was regenerated, and the deferrals are gone

`derive_sentence_register_v2.py --skip-w13` over the new tree re-emits all **10,112 sentences as
`set: bank`, keyed by slug**; `counts.w13` is 0 and `apply_sentence_register.py` reports **0
deferred**. This is what the deferral was designed to become: `validate_repairs_applied.py`'s
handler says "the moment that slug appears in the export it stops being deferred and is asserted
like any other row", and it now asserts all 10,112.

Three rows changed value on regeneration — the `n3-nanka` sentences of §3 — and were re-applied.
`validate_sentence_register.py` re-derives the whole bank on every gate run and now agrees on every
sentence: neutral 5,411 · polite 3,044 · casual 1,342 · formal 172 · null 130 · archaic 7 · slang 4
· vulgar 1 · dialect 1.

The generator's own `what_this_is` was updated to say so, and to warn that running it **without**
`--skip-w13` now emits every mined sentence twice (once as its bank slug, once as its pre-ingest
w13 key) and that the two rows can disagree, because the bank row carries the sentence's real
grammar tags and vocab links while the w13 row only ever had its authoring targets.

### 7.2 Lessons did not move

**0 lesson `.md` files changed** (`validate_md_views`: 322/322 byte-identical to a fresh render).
Four lesson JSONs and three `topic.json` files changed and the diff is `needs[]` only — the W21
prerequisite edges, which check C4 requires to be EXACTLY what `build_needs_table.py` derives from
the tree. The relink gave two lessons a new backward edge (御/お, どんなに) and moved one, so the
table was re-derived and re-applied; without that the gate fails by contract. `sentence_refs` come
from the stored bodies and are untouched — W14 re-selects.

### 7.3 The gate

**`validate_all.py`: ALL HARD VALIDATORS PASS.** `validate.py` reads **10,112 sentences, 0 errors**
(1,635 warns, all the pre-existing `lemma not in JMdict-common` class).

Two validators were corrected rather than baselined:

* **`audit_hygiene_all_locales.py`** flagged seven strings. Four were false positives on `duvida`,
  which is the 3rd-person present of *duvidar* ("quem fala já duvida que…", "você duvida de mim") as
  well as the de-accent of the noun *dúvida* — the gate was demanding an edit that makes the
  Portuguese wrong. `duvida`/`duvidas` join `maca`/`manha`/`crista` in `ACCENT_HOMOGRAPHS`, and that
  set now wins over the legacy word list rather than losing to it, because a word genuinely spelt
  both ways cannot be a hard failure whichever list it came from.
* **Three were real** and are repaired through the existing applier and a tracked exact-match table,
  `research/derived/repairs/w13_text_repairs.json` (manifest step 123, registered in the replay
  gate). Diacritics only — no word, order or register changed — and each row's own
  `translation_literal` already spelt the word correctly, so the defect is one string's, not the
  record's:

  | slug | was | now |
  |---|---|---|
  | `sent:tatoeba-101293` | Ele **e** alto, mas o **irmao** mais velho **e** ainda mais alto. | Ele é alto, mas o irmão mais velho é ainda mais alto. |
  | `sent:tatoeba-10367178` | **Nao** existem **demonios** neste mundo. | Não existem demônios neste mundo. |
  | `sent:tatoeba-4793166` | Por favor, analise a **questao** com boa vontade. | Por favor, analise a questão com boa vontade. |

  This is the one place the unit touched authored learner text, and it is recorded row by row.
  `apply_sentence_text_repairs.py` was taught to accept the `translation` field alongside
  `structure_explanation` and `translation_literal`.

`validate_display_consistency.py` gained **6 soft-baseline entries** with their own cause: mined
Layer-B explanations that teach by CONTRAST and so name a form the sentence does not contain
(困ったことに beside 幸いなことに; the dictionary お願いする behind よろしく). Same class as the 52
already there, queued with them for the content re-authoring pass, and deliberately not repaired —
repairing it means rewriting learner prose, and this unit authors none.

### 7.4 The manifest and the full replay

Three steps added after 120, families still last, everything renumbered (**127 steps, 91 enabled**):

| n | step |
|---|---|
| 121 | `ingest_mined_stages.py --apply --source accepted --source generated --layerb mined_layerb_n3 --tag n3-exemplification --provenance-source w13:n3-exemplification` |
| 122 | `apply_orthographic_relinks.py --scope n3` |
| 123 | `apply_sentence_text_repairs.py --data research/derived/repairs/w13_text_repairs.json` |
| 124 | furigana (was 121) |
| 125-127 | the three family builders (were 122-124) |

Two new tables registered in `validate_repairs_applied.py`: `orthographic_relinks_n3.json` (same
handler as the N5/N4 one) and `w13_text_repairs.json`. The gate replays **18,170 rows clean**.

**Full-mode `validate_index_rebuildable.py`: green, and re-recorded.** 790 files compared, **568
held, 222 byte-identical — all three unchanged from W31's record.** No file newly stopped
rebuilding and none started; **14 held entries' rebuild bytes moved**, each for a reason this unit
created:

* `corpus/sentences/bank.json` + `corpus/sentences/INDEX.md` — 4,223 more sentences;
* `corpus/kanji/n1..n5.json` — kanji example lists drawn from the larger bank;
* `corpus/readings/n3.json`, `corpus/INDEX.md` — the same, plus counts;
* the four N3 lesson JSONs — the `needs[]` edges of §7.2;
* `course/vocab_disambiguation_review.json` — the relink changed the disambiguation input.

Two tracked side-effect files also moved, and both are replay artefacts rather than decisions:
`research/derived/romaji_reading_disputes.json` **shrank 11 → 10** (manifest step 80 writes it
REPO-relative; the entry that left is 「あ、またコンピューターが固まっちゃったよ。」, a っ|ち boundary,
which is §1.2's fix showing up in the replay), and `research/derived/grammar_merge_ledger.json`
(step 110, same REPO-relative habit). A manifest step writing a tracked file out of a SCRATCH
rebuild is a small defect of its own and is listed in §9.

## 8. Thirty ingested sentences, rendered from the DB

Every field below is read back out of `db/corpus.sqlite` — the Japanese, the kana the Dissector
built, the pt-BR translation and literal, each content token with its authored gloss, each particle
with its `function_type` and explanation, the structure paragraph, the register and the rule that
decided it, and the grammar edges. Sampled every 141st row of the 4,223 by slug order, so the
selection is deterministic and covers all 29 batches.

| # | slug | level | register (rule) | ai |
|---|---|---|---|---|
| 1 | `sent:gen-0aa582b8744f` | n4 | neutral (`plain-predicate`) | yes |
| 2 | `sent:tatoeba-102246` | n3 | polite (`polite-predicate`) | no |
| 3 | `sent:tatoeba-105342` | n1 | neutral (`plain-predicate`) | no |
| 4 | `sent:tatoeba-10784568` | n3 | casual (`soft-final`) | no |
| 5 | `sent:tatoeba-11029674` | n2 | neutral (`plain-predicate`) | no |
| 6 | `sent:tatoeba-11365399` | n1 | neutral (`plain-predicate`) | no |
| 7 | `sent:tatoeba-117697` | n3 | neutral (`plain-predicate`) | no |
| 8 | `sent:tatoeba-12118863` | n2 | casual (`casual-marker`) | no |
| 9 | `sent:tatoeba-125466` | n1 | polite (`polite-predicate`) | no |
| 10 | `sent:tatoeba-137807` | n2 | neutral (`plain-predicate`) | no |
| 11 | `sent:tatoeba-143974` | n1 | neutral (`plain-predicate`) | no |
| 12 | `sent:tatoeba-148935` | n2 | neutral (`plain-predicate`) | no |
| 13 | `sent:tatoeba-155780` | n3 | neutral (`plain-predicate`) | no |
| 14 | `sent:tatoeba-162459` | n3 | casual (`casual-marker`) | no |
| 15 | `sent:tatoeba-170837` | n3 | polite (`polite-predicate`) | no |
| 16 | `sent:tatoeba-176199` | n1 | neutral (`plain-predicate`) | no |
| 17 | `sent:tatoeba-184414` | n3 | polite (`polite-predicate`) | no |
| 18 | `sent:tatoeba-190270` | n3 | neutral (`plain-predicate`) | no |
| 19 | `sent:tatoeba-200379` | n3 | polite (`polite-predicate`) | no |
| 20 | `sent:tatoeba-207400` | n1 | polite (`polite-predicate`) | no |
| 21 | `sent:tatoeba-213213` | n1 | polite (`polite-predicate`) | no |
| 22 | `sent:tatoeba-220458` | n3 | neutral (`plain-predicate`) | no |
| 23 | `sent:tatoeba-2244257` | n3 | neutral (`plain-predicate`) | no |
| 24 | `sent:tatoeba-231717` | n1 | polite (`polite-predicate`) | no |
| 25 | `sent:tatoeba-354160` | n3 | neutral (`plain-predicate`) | no |
| 26 | `sent:tatoeba-75362` | n3 | polite (`polite-predicate`) | no |
| 27 | `sent:tatoeba-82089` | n1 | neutral (`plain-predicate`) | no |
| 28 | `sent:tatoeba-8657782` | n1 | neutral (`plain-predicate`) | no |
| 29 | `sent:tatoeba-9001470` | n3 | casual (`soft-final`) | no |
| 30 | `sent:tatoeba-96042` | n3 | neutral (`plain-predicate`) | no |

### 1. 今日はすこしも寒くない
`sent:gen-0aa582b8744f` · n4 · **neutral** (`plain-predicate`) · GENERATED (ai_generated) · kana きょうわすこしもさむくない

- **pt-BR:** Hoje não está nem um pouco frio.
- **literal:** Quanto a hoje (は, tópico), nem um pouco frio não está.
- **tokens:** 今日 (今日) = hoje · すこし (すこし) = um pouco; um pouquinho · 寒く (寒い) = frio · ない (ない) = não (negação)
- **partícula** **は** [binding] partícula de tópico — は apresenta 今日 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **も** [binding] partícula que forma すこしも ('nem um pouco', com verbo negado) — も se prende a すこし e, com a negativa, forma すこしも寒くない: nem um pouquinho de frio.
- **estrutura:** O alvo aparece em すこしも…ない: すこし ganha も e puxa a negativa lá no fim, dando o sentido de 'nem um pouco'. 今日 é o tópico com は e o predicado é 寒くない, a negativa do adjetivo い 寒い.
- **grammar:** n3-sukoshimo-nai

### 2. 彼は知事と長年の付き合いです。
`sent:tatoeba-102246` · n3 · **polite** (`polite-predicate`) · Tatoeba · kana かれわちじとながねんのつきあいです。

- **pt-BR:** Ele conhece o governador há muitos anos.
- **literal:** Quanto a ele (は = tema), com o governador (と = com quem) (é) uma convivência de longos anos.
- **tokens:** 彼 (彼) = ele · 知事 (知事) = governador (de província) · 長年 (長年) = muitos anos · 付き合い (付き合い) = convívio; relacionamento
- **partícula** **は** [binding] partícula de tópico — は apresenta 彼 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **と** [case] partícula de companhia ('com') — と marca 知事 como a outra parte da convivência: é com o governador que ele tem esses longos anos.
- **partícula** **の** [case] partícula de ligação/posse — の liga 長年 a 付き合い e junta os dois num bloco só, em que 付き合い é o núcleo e 長年 o modificador.
- **estrutura:** 彼 é o tópico com は e o predicado é 長年の付き合いです, em que の liga 長年 a 付き合い. 知事 leva と como a outra parte dessa convivência.

### 3. 彼は事態を知らなかった。
`sent:tatoeba-105342` · n1 · **neutral** (`plain-predicate`) · Tatoeba · kana かれわじたいをしらなかった。

- **pt-BR:** Ele não sabia da situação.
- **literal:** Quanto a ele, a situação (を objeto) não sabia.
- **tokens:** 彼 (彼) = ele · 事態 (事態) = situação, estado das coisas · 知ら (知る) = saber, conhecer
- **partícula** **は** [binding] partícula de tópico — は apresenta 彼 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **を** [case] marcador de objeto direto — を marca 事態 como o objeto direto de 知る, ou seja, aquilo sobre o que a ação recai.
- **estrutura:** 彼 é o tópico com は e o verbo é 知らなかった, passado negativo de 知る (saber). 事態 é o objeto com を, e a frase descreve um estado de desconhecimento: em japonês não saber de algo se diz negando o verbo saber.

### 4. ここはホコリだらけだな。
`sent:tatoeba-10784568` · n3 · **casual** (`soft-final`) · Tatoeba · kana ここわほこりだらけだな。

- **pt-BR:** Aqui está cheio de poeira, hein.
- **literal:** Quanto a aqui, é cheio de poeira, né.
- **tokens:** ここ (ここ) = aqui · ホコリ (ホコリ) = poeira; pó
- **partícula** **は** [binding] partícula de tópico — は apresenta ここ como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **な** [sentence-final] partícula final de constatação — な no fim é o comentário meio para si mesmo, meio buscando concordância: 'está cheio de poeira aqui, hein'.
- **estrutura:** ここ é o tópico com は e o predicado é ホコリだらけ, fechado por だ: だらけ grudado no substantivo diz que o lugar está tomado daquilo. な no fim procura a reação de quem ouve.

### 5. 希望を失った。
`sent:tatoeba-11029674` · n2 · **neutral** (`plain-predicate`) · Tatoeba · kana きぼうをうしなった。

- **pt-BR:** A gente perdeu a esperança.
- **literal:** Esperança (を objeto), perdemos.
- **tokens:** 希望 (希望) = esperança; desejo · 失っ (失う) = perder
- **partícula** **を** [case] marcador de objeto direto — を marca 希望 como o objeto direto de 失う, ou seja, aquilo sobre o que a ação recai.
- **estrutura:** 希望を é o objeto com を e 失った é o passado de 失う. Quem perdeu não aparece, fica subentendido pelo contexto.

### 6. 一緒に釣りに行く？
`sent:tatoeba-11365399` · n1 · **neutral** (`plain-predicate`) · Tatoeba · kana いっしょにつりにいく?

- **pt-BR:** Vamos pescar juntos?
- **literal:** Juntos, para a pescaria (に finalidade), você vai?
- **tokens:** 一緒 (一緒) = junto, juntos · 釣り (釣り) = pesca, pescaria · 行く (行く) = ir
- **partícula** **に** [case] partícula que forma advérbio (dentro de 一緒に) — に fecha 一緒 e o transforma em advérbio: a pescaria seria feita em companhia.
- **partícula** **に** [case] partícula de finalidade (com verbo de deslocamento) — に marca 釣り como o objetivo da ida; com 行く, o に diz a que se vai.
- **estrutura:** As duas partículas に fazem trabalhos diferentes: a primeira monta o advérbio 一緒に ('juntos') e a segunda marca 釣り como a finalidade da ida, no molde 〜に行く. O predicado é 行く na forma de dicionário, e a pergunta fica na entonação (？).

### 7. 彼の欠席で事が面倒になる。
`sent:tatoeba-117697` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana かれのけっせきでことがめんどうになる。

- **pt-BR:** A ausência dele complica as coisas.
- **literal:** Com a falta dele, a coisa fica trabalhosa.
- **tokens:** 彼 (彼) = ele · 欠席 (欠席) = falta; ausência · 事 (事) = coisa, assunto · 面倒 (面倒) = incômodo; complicação; (～をみる) cuidar de · なる (なる) = tornar-se, ficar
- **partícula** **の** [case] partícula de ligação/posse — の liga 彼 a 欠席 e junta os dois num bloco só, em que 欠席 é o núcleo e 彼 o modificador.
- **partícula** **で** [case] partícula de causa/motivo — Aqui で aponta 彼の欠席 como a causa da complicação: é a falta dele que embola tudo.
- **partícula** **が** [case] partícula de sujeito — が marca 事 como o sujeito de なる, isto é, quem faz ou de quem se diz o que o predicado exprime.
- **estrutura:** 彼の欠席で dá a causa com で, com の ligando 彼 a 欠席. 事が é o sujeito com が e 面倒になる é o par に mais なる, dizendo em que a coisa se transforma.

### 8. 腰が痛いんだ。
`sent:tatoeba-12118863` · n2 · **casual** (`casual-marker`) · Tatoeba · kana こしがいたいんだ。

- **pt-BR:** Minha lombar tá doendo.
- **literal:** A lombar (が sujeito) dói, sabe.
- **tokens:** 腰 (腰) = cintura, lombar (parte da expressão idiomática) · 痛い (痛い) = dolorido, que dói
- **partícula** **が** [case] partícula de sujeito — が marca 腰 como o sujeito de 痛い, isto é, quem faz ou de quem se diz o que o predicado exprime.
- **partícula** **ん** [nominalizer] nominalizador explicativo (ん = の) — ん fecha 腰が痛い e dá o tom de quem está explicando o próprio estado a alguém.
- **estrutura:** が marca 腰 como aquilo que dói, porque com adjetivos de sensação o japonês usa が e não を. O predicado é o adjetivo い 痛い, e o んだ do fim (ん = の + だ) dá o ar de quem está explicando o motivo de alguma coisa.

### 9. 弟が描きました。
`sent:tatoeba-125466` · n1 · **polite** (`polite-predicate`) · Tatoeba · kana おとうとがえがきました。

- **pt-BR:** Quem desenhou foi o meu irmão mais novo.
- **literal:** O irmão mais novo (が = sujeito) desenhou.
- **tokens:** 弟 (弟) = irmão mais novo · 描き (描く) = desenhar, pintar
- **partícula** **が** [case] partícula de sujeito — が marca 弟 como o sujeito de 描く, isto é, quem faz ou de quem se diz o que o predicado exprime.
- **estrutura:** 弟が é o sujeito com が, e aqui が faz mais do que marcar: aponta quem foi, entre outros possíveis. 描きました é o passado polido de 描く.

### 10. 台風でひどい被害を受けた。
`sent:tatoeba-137807` · n2 · **neutral** (`plain-predicate`) · Tatoeba · kana たいふうでひどいひがいをうけた。

- **pt-BR:** A gente sofreu um estrago sério por causa do tufão.
- **literal:** Por causa do tufão (で causa), recebemos um dano terrível (を objeto).
- **tokens:** 台風 (台風) = tufão · ひどい (ひどい) = horrível / cruel · 被害 (被害) = dano; prejuízo; estrago · 受け (受ける) = receber, sofrer
- **partícula** **で** [case] partícula de lugar da ação — Este で marca 台風 como a causa do estrago.
- **partícula** **を** [case] marcador de objeto direto — を marca ひどい被害 como o objeto direto de 受ける, ou seja, aquilo sobre o que a ação recai.
- **estrutura:** で marca 台風 como causa, e não como lugar. ひどい qualifica 被害 direto, esse bloco é o objeto com を, e 受けた é o verbo de sempre para quem sofre um dano.

### 11. 人生は冒険に満ちている。
`sent:tatoeba-143974` · n1 · **neutral** (`plain-predicate`) · Tatoeba · kana じんせいわぼうけんにみちている。

- **pt-BR:** A vida é cheia de aventura.
- **literal:** Quanto à vida, de aventura (に de conteúdo) está cheia.
- **tokens:** 人生 (人生) = vida (humana) · 冒険 (冒険) = aventura · 満ち (満ちる) = estar cheio; encher-se · いる (いる) = estar
- **partícula** **は** [binding] partícula de tópico — は apresenta 人生 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **に** [case] partícula de destino/direção — Este に marca 冒険 como aquilo de que a vida está cheia; 〜に満ちている pede に no conteúdo.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga 満ちる ao que vem depois (いる) e encadeia os dois dentro da mesma frase.
- **estrutura:** は marca 人生 como tópico e 冒険に usa に para aquilo de que a vida se enche, porque 満ちる pede に. 満ちている é a forma ている, o estado de estar cheia.

### 12. 車を買うために貯金をしている。
`sent:tatoeba-148935` · n2 · **neutral** (`plain-predicate`) · Tatoeba · kana くるまをかうためにちょきんをしている。

- **pt-BR:** Estou juntando dinheiro para comprar um carro.
- **literal:** Para comprar um carro (ため finalidade), estou fazendo poupança (を objeto).
- **tokens:** 車 (車) = carro · 買う (買う) = comprar · ため (ため) = para, por causa de · 貯金 (貯金) = poupança; economias · し (する) = fazer · いる (いる) = estar
- **partícula** **を** [case] marcador de objeto direto — を marca 車 como o objeto direto de 買う, ou seja, aquilo sobre o que a ação recai.
- **partícula** **に** [case] に dentro de ために (finalidade) — Este に fecha ため e forma ために, que dá a finalidade da poupança: comprar um carro.
- **partícula** **を** [case] marcador de objeto direto — を marca 貯金 como o objeto direto de する, ou seja, aquilo sobre o que a ação recai.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga する ao que vem depois (いる) e encadeia os dois dentro da mesma frase.
- **estrutura:** A finalidade vem primeiro: 車を買う é uma oração inteira, com を marcando 車 como objeto de 買う, e ために converte tudo isso em 'para comprar um carro'. O predicado é 貯金をしている, o substantivo 貯金 com を mais する na forma て e いる, que mostra a ação em andamento; quem junta o dinheiro fica subentendido.

### 13. 私は食欲がある。
`sent:tatoeba-155780` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana わたしわしょくよくがある。

- **pt-BR:** Estou com apetite.
- **literal:** quanto a mim: apetite [suj.] existe
- **tokens:** 私 (私) = eu · 食欲 (食欲) = apetite · ある (ある) = existir, haver
- **partícula** **は** [binding] partícula de tópico — は apresenta 私 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **が** [case] partícula de sujeito — が marca 食欲 como o sujeito de ある, isto é, quem faz ou de quem se diz o que o predicado exprime.
- **estrutura:** 私 é o tópico com は e o sujeito do comentário é 食欲, marcado por が. ある é o verbo de existência: o japonês não diz que eu tenho apetite, e sim que o apetite existe, com 私 apenas dando o âmbito.

### 14. 私の立場になってくれ。
`sent:tatoeba-162459` · n3 · **casual** (`casual-marker`) · Tatoeba · kana わたしのたちばになってくれ。

- **pt-BR:** Se põe no meu lugar.
- **literal:** Na minha posição (の; に resultado), torne-se (くれ, imperativo de favor).
- **tokens:** 私 (私) = eu · 立場 (立場) = posição; ponto de vista · なっ (なる) = tornar-se, ficar · くれ (くれる) = fazer para mim (favor)
- **partícula** **の** [case] partícula de ligação/posse — の liga 私 a 立場 e junta os dois num bloco só, em que 立場 é o núcleo e 私 o modificador.
- **partícula** **に** [case] partícula de destino/direção — に marca 私の立場 como o lugar em que o outro deve se colocar; aqui 〜になる não é mudança física, é assumir a posição de alguém.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga なる ao que vem depois (くれる) e encadeia os dois dentro da mesma frase.
- **estrutura:** 私の立場 usa の para dizer de quem é a posição, e に marca esse ponto como o estado em que o ouvinte deve se colocar, junto com なる. O predicado é なってくれ, forma て mais くれ no imperativo, que pede o favor para quem fala.

### 15. 座席の背を倒してもいいですか。
`sent:tatoeba-170837` · n3 · **polite** (`polite-predicate`) · Tatoeba · kana ざせきのせをたおしてもいいですか。

- **pt-BR:** Posso reclinar o encosto do assento?
- **literal:** O encosto do assento, mesmo derrubando, está bom?
- **tokens:** 座席 (座席) = assento; lugar (sentado) · 背 (背) = estatura, altura · 倒し (倒す) = reclinar, abaixar · いい (いい) = bom
- **partícula** **の** [case] partícula de ligação/posse — の liga 座席 a 背 e junta os dois num bloco só, em que 背 é o núcleo e 座席 o modificador.
- **partícula** **を** [case] marcador de objeto direto — を marca 背 como o objeto direto de 倒す, ou seja, aquilo sobre o que a ação recai.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga 倒す ao que vem depois (も) e encadeia os dois dentro da mesma frase.
- **partícula** **も** [binding] も de permissão (〜てもいい) — Este も se junta ao て de 倒して e forma 倒してもいい, a fórmula de pedir permissão: 'mesmo que eu recline, tudo bem?'.
- **partícula** **か** [sentence-final] partícula interrogativa — か no fim transforma a frase em pergunta.
- **estrutura:** の liga 座席 a 背 ('o encosto do assento') e を marca esse bloco como objeto de 倒す. A forma て mais も dá o sentido de 'mesmo que', e 〜てもいい fecha o molde de pedir permissão, aqui com ですか em tom polido.

### 16. 警察は強盗を逮捕した。
`sent:tatoeba-176199` · n1 · **neutral** (`plain-predicate`) · Tatoeba · kana けいさつわごうとうをたいほした。

- **pt-BR:** A polícia prendeu o assaltante.
- **literal:** Quanto à polícia, o assaltante prendeu.
- **tokens:** 警察 (警察) = polícia · 強盗 (強盗) = assaltante; roubo; assalto · 逮捕 (逮捕) = prisão; detenção · し (する) = fazer
- **partícula** **は** [binding] partícula de tópico — は apresenta 警察 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **を** [case] marcador de objeto direto — を marca 強盗 como o objeto direto de する, ou seja, aquilo sobre o que a ação recai.
- **estrutura:** 警察 é o tópico com は e 強盗 é o objeto marcado por を. O verbo é 逮捕する no passado, 逮捕した, formado do substantivo 逮捕 mais する.

### 17. 学校はうちの向かいにあります。
`sent:tatoeba-184414` · n3 · **polite** (`polite-predicate`) · Tatoeba · kana がっこうわうちのむかいにあります。

- **pt-BR:** A escola fica em frente à minha casa.
- **literal:** Quanto à escola(は, tópico), em frente(に, lugar) da(の) nossa casa, existe.
- **tokens:** 学校 (学校) = escola · うち (うち) = casa · 向かい (向かい) = o lado oposto; em frente; do outro lado · あり (ある) = existir, haver
- **partícula** **は** [binding] partícula de tópico — は apresenta 学校 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **の** [case] partícula de ligação/posse — の liga うち a 向かい e junta os dois num bloco só, em que 向かい é o núcleo e うち o modificador.
- **partícula** **に** [case] partícula de destino/direção — に marca うちの向かい como o lugar onde a escola fica; com あります, o lugar vem com に.
- **estrutura:** 学校 é o tópico com は e うちの向かい é montado com の ligando うち a 向かい, com に marcando esse ponto como o lugar onde algo existe. あります é o verbo de existência para coisas, na forma polida.

### 18. 一日の大半を読書して過ごした。
`sent:tatoeba-190270` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana いちにちのたいはんをどくしょしてすごした。

- **pt-BR:** Passei a maior parte do dia lendo.
- **literal:** Passei a maior parte do dia (の posse, を objeto) lendo.
- **tokens:** 一 (一) = um · 日 (日) = dia · 大半 (大半) = maioria; grande parte; a maior parte · 読書 (読書) = leitura · し (する) = fazer · 過ごし (過ごす) = passar (o tempo)
- **partícula** **の** [case] partícula de ligação/posse — の liga 一日 a 大半 e junta os dois num bloco só, em que 大半 é o núcleo e 一日 o modificador.
- **partícula** **を** [case] marcador de objeto direto — を marca 大半 como o objeto direto de する, ou seja, aquilo sobre o que a ação recai.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga する ao que vem depois (過ごす) e encadeia os dois dentro da mesma frase.
- **estrutura:** 一日の大半を é o objeto, com の ligando 一日 a 大半 e を marcando o tempo gasto. 読書して é a forma て de 読書する e diz no que o tempo foi gasto; o núcleo é 過ごした, passado de 過ごす, e o sujeito 'eu' fica subentendido.

### 19. どのホームで乗ればいいですか。
`sent:tatoeba-200379` · n3 · **polite** (`polite-predicate`) · Tatoeba · kana どのほーむでのればいいですか。

- **pt-BR:** Em qual plataforma eu devo embarcar?
- **literal:** Em qual plataforma (で, lugar da ação) se eu subir, está bom?
- **tokens:** どの (どの) = qual · ホーム (ホーム) = plataforma (de estação) · 乗れ (乗る) = pegar (transporte), embarcar · いい (いい) = bom
- **partícula** **で** [case] partícula de lugar da ação — で marca どのホーム como o lugar onde o embarque acontece.
- **partícula** **ば** [conjunctive] partícula condicional — ば põe 乗る na condicional e monta 乗ればいい, o jeito de perguntar o que convém fazer.
- **partícula** **か** [sentence-final] partícula interrogativa — か no fim transforma a frase em pergunta.
- **estrutura:** どのホーム pergunta a plataforma e で marca o lugar onde a ação se dá. 乗れば é a forma condicional de 乗る, e o molde 〜ばいい ('se fizer assim, está bom') é a maneira comum de pedir orientação; ですか fecha em polido.

### 20. その謎を解いてみましょう。
`sent:tatoeba-207400` · n1 · **polite** (`polite-predicate`) · Tatoeba · kana そのなぞをといてみましょう。

- **pt-BR:** Vamos tentar resolver esse enigma.
- **literal:** Vamos experimentar resolver esse enigma (を objeto, てみる tentativa, ましょう convite).
- **tokens:** その (その) = esse, aquele · 謎 (謎) = enigma; mistério; charada · 解い (解く) = resolver; solucionar · み (みる) = experimentar, tentar
- **partícula** **を** [case] marcador de objeto direto — を marca その謎 como o objeto direto de 解く, ou seja, aquilo sobre o que a ação recai.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga 解く ao que vem depois (みる) e encadeia os dois dentro da mesma frase.
- **estrutura:** その謎を marca o enigma como objeto. O verbo 解く vem na forma て presa a みる (解いてみる), combinação que significa tentar e ver no que dá, e ましょう transforma o conjunto em convite: vamos tentar.

### 21. そのコートはちょうど僕が探していたスタイルのものです。
`sent:tatoeba-213213` · n1 · **polite** (`polite-predicate`) · Tatoeba · kana そのこーとわちょうどぼくがさがしていたすたいるのものです。

- **pt-BR:** Esse casaco é exatamente o estilo que eu estava procurando.
- **literal:** Quanto àquele casaco, é a peça do estilo (の) que eu (が sujeito) procurava.
- **tokens:** その (その) = esse, aquele · コート (コート) = casaco, sobretudo · ちょうど (ちょうど) = exatamente; justamente · 僕 (僕) = eu (masculino, informal) · 探し (探す) = procurar · い (いる) = estar · スタイル (スタイル) = estilo, moda; silhueta, corpo · もの (もの) = coisa
- **partícula** **は** [binding] partícula de tópico — は apresenta そのコート como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **が** [case] partícula de sujeito — が marca ちょうど僕 como o sujeito de 探す, isto é, quem faz ou de quem se diz o que o predicado exprime.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga 探す ao que vem depois (いる) e encadeia os dois dentro da mesma frase.
- **partícula** **の** [case] partícula de ligação/posse — の liga いたスタイル a もの e junta os dois num bloco só, em que もの é o núcleo e いたスタイル o modificador.
- **estrutura:** そのコート é o tópico, com は, e 僕が探していた é uma oração que qualifica スタイル, com 僕 marcado por が dentro dela e の ligando esse estilo a もの. ちょうど reforça que é exatamente aquilo, e です fecha o predicado nominal.

### 22. この庭の美しさは自然より人工のおかげだ。
`sent:tatoeba-220458` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana このにわのうつくしさわしぜんよりじんこうのおかげだ。

- **pt-BR:** A beleza deste jardim vem mais da mão humana do que da natureza.
- **literal:** Quanto à beleza deste jardim (の posse, は tópico), mais que a natureza (より comparação), é graças à obra humana (の posse).
- **tokens:** この (この) = este, esse · 庭 (庭) = jardim, quintal · 美し (美しい) = belo, bonito · 自然 (自然) = natureza; mundo natural · 人工 (人工) = artificial; feito pelo homem · おかげ (おかげ) = graças a, mérito de
- **partícula** **の** [case] partícula de ligação/posse — の liga この庭 a 美しさ: a beleza de que se fala é a deste jardim.
- **partícula** **は** [binding] partícula de tópico — は apresenta 美しさ como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **より** [case] partícula de comparação ('do que') — より marca 自然 como o termo de comparação: mais do que a natureza, o mérito é da mão humana.
- **partícula** **の** [case] partícula de ligação/posse — の liga 人工 a おかげ e junta os dois num bloco só, em que おかげ é o núcleo e 人工 o modificador.
- **estrutura:** O tópico é この庭の美しさ, onde o adjetivo 美しい vira o substantivo 美しさ (beleza) e の o prende ao jardim. No comentário, より marca 自然 como o termo de comparação, e o predicado é 人工のおかげだ: mais do que da natureza, a beleza vem por causa da mão humana.

### 23. その質問は予期していなかった。
`sent:tatoeba-2244257` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana そのしつもんわよきしていなかった。

- **pt-BR:** Eu não esperava essa pergunta.
- **literal:** Quanto àquela pergunta (は tópico), eu não estava prevendo.
- **tokens:** その (その) = esse, aquele · 質問 (質問) = pergunta · 予期 (予期) = esperar, prever · し (する) = fazer · い (いる) = estar
- **partícula** **は** [binding] partícula de tópico — は apresenta その質問 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga する ao que vem depois (いる) e encadeia os dois dentro da mesma frase.
- **estrutura:** その質問 vem como tópico, com は, mesmo sendo aquilo que 予期する toma como objeto; é comum o falante puxar o assunto para a frente assim. O predicado é 予期していなかった, a forma 〜ている no passado negativo: não era algo que quem fala vinha esperando.

### 24. あなたは徹底した人間嫌いですね。
`sent:tatoeba-231717` · n1 · **polite** (`polite-predicate`) · Tatoeba · kana あなたわてっていしたにんげんきらいですね。

- **pt-BR:** Você não suporta gente mesmo, né?
- **literal:** Quanto a você (は tópico), é um detestador de gente levado ao extremo, não é?
- **tokens:** あなた (あなた) = você · 徹底 (徹底) = fazer a fundo, ser completo · し (する) = fazer · 人間 (人間) = ser humano, pessoa · 嫌い (嫌い) = detestável; que não se gosta
- **partícula** **は** [binding] partícula de tópico — は apresenta あなた como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **ね** [sentence-final] partícula final de concordância — ね no fim suaviza a afirmação e pede a concordância de quem ouve, como o nosso 'né?'.
- **estrutura:** あなた é o tópico com は e o predicado é nominal: 人間嫌いです. Na frente dele vem 徹底した, uma oração que o qualifica e leva a característica ao extremo, e ね no fim busca a concordância do interlocutor.

### 25. 君は人間だ。
`sent:tatoeba-354160` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana きみわにんげんだ。

- **pt-BR:** Você é um ser humano.
- **literal:** Quanto a você, é ser humano.
- **tokens:** 君 (君) = você (informal) · 人間 (人間) = ser humano, pessoa
- **partícula** **は** [binding] partícula de tópico — は apresenta 君 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **estrutura:** 君 é o tópico com は e 人間 é o predicado, fechado por だ. É o molde básico de identificação: aponta-se alguém e diz-se o que ele é.

### 26. このうち大事なのは後者の方です。
`sent:tatoeba-75362` · n3 · **polite** (`polite-predicate`) · Tatoeba · kana このうちだいじなのわこうしゃのほうです。

- **pt-BR:** Destes aqui, o importante é o segundo.
- **literal:** Dentre estes, o que é importante é o lado do último.
- **tokens:** この (この) = este, esse · うち (うち) = dentro de, casa · 大事 (大事) = importante; valioso · 後者 (後者) = o último (de dois); este último · 方 (方) = lado, direção
- **partícula** **の** [nominalizer] nominalizador — の substantiva 大事な e forma 大事なの ('o que é importante'), um bloco que は pode tomar como assunto.
- **partícula** **は** [binding] partícula de tópico — は apresenta 大事なの como assunto, e a frase responde qual é ele: 後者の方.
- **partícula** **の** [case] partícula de ligação/posse — の liga 後者 a 方 e junta os dois num bloco só, em que 方 é o núcleo e 後者 o modificador.
- **estrutura:** このうち abre a frase delimitando o conjunto de onde se escolhe. 大事な mais の formam um substantivo, 'o que é importante', e は o transforma em tópico; o predicado é 後者の方です, com の ligando 後者 a 方.

### 27. 僕はじっと考えた。
`sent:tatoeba-82089` · n1 · **neutral** (`plain-predicate`) · Tatoeba · kana ぼくわじっとかんがえた。

- **pt-BR:** Fiquei pensando com toda a atenção.
- **literal:** Quanto a mim (は, tópico), fixamente pensei.
- **tokens:** 僕 (僕) = eu (masculino, informal) · じっと (じっと) = fixamente, imóvel, sem desviar o olhar · 考え (考える) = pensar, refletir
- **partícula** **は** [binding] partícula de tópico — は apresenta 僕 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **estrutura:** 僕 vem marcado por は na função de tópico e 考えた é o predicado, sem objeto nenhum. O advérbio じっと vem antes do verbo e passa a ideia de ficar parado, concentrado no que se pensa.

### 28. 彼は私の手をしっかりと握った。
`sent:tatoeba-8657782` · n1 · **neutral** (`plain-predicate`) · Tatoeba · kana かれわわたしのてをしっかりとにぎった。

- **pt-BR:** Ele apertou firme a minha mão.
- **literal:** quanto a ele: a minha mão [obj.] com firmeza apertou
- **tokens:** 彼 (彼) = ele · 私 (私) = eu · 手 (手) = mão · しっかり (しっかり) = firmemente, com firmeza · 握っ (握る) = segurar; apertar (na mão)
- **partícula** **は** [binding] partícula de tópico — は apresenta 彼 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **の** [case] partícula de ligação/posse — の liga 私 a 手 e junta os dois num bloco só, em que 手 é o núcleo e 私 o modificador.
- **partícula** **を** [case] marcador de objeto direto — を marca 手 como o objeto direto de 握る, ou seja, aquilo sobre o que a ação recai.
- **partícula** **と** [case] partícula que forma advérbio de modo (しっかりと) — と se prende a しっかり e forma しっかりと, reforçando o modo do aperto: foi firme mesmo.
- **estrutura:** 彼 é o tópico com は e 握った é o verbo. を marca o bloco 私の手, ligado por の, como o que foi apertado, e しっかりと funciona como advérbio de modo, com と fixando o jeito da ação.

### 29. ゲームしようよ。
`sent:tatoeba-9001470` · n3 · **casual** (`soft-final`) · Tatoeba · kana げーむしようよ。

- **pt-BR:** Bora jogar.
- **literal:** Vamos fazer um jogo (よ ênfase).
- **tokens:** ゲーム (ゲーム) = jogo · しよう (する) = fazer
- **partícula** **よ** [sentence-final] partícula final de ênfase — よ no fim passa a informação ao ouvinte com ênfase, como quem diz 'olha' ou 'viu'.
- **estrutura:** ゲーム é o objeto de する, mas aparece sem を, coisa comum na fala. O verbo está em しよう, a forma volitiva de する, que convida a fazer junto, e よ dá o empurrão no convite.

### 30. 彼らは流れに乗って川を下った。
`sent:tatoeba-96042` · n3 · **neutral** (`plain-predicate`) · Tatoeba · kana かれらわながれにのってかわをくだった。

- **pt-BR:** Eles desceram o rio levados pela correnteza.
- **literal:** Quanto a eles (は = tópico), montando na (に乗って) corrente, o rio (を = percurso) desceram.
- **tokens:** 彼 (彼) = ele · 流れ (流れ) = fluxo; corrente · 乗っ (乗る) = embarcar, subir em · 川 (川) = rio · 下っ (下る) = descer
- **partícula** **は** [binding] partícula de tópico — は apresenta 彼ら como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte.
- **partícula** **に** [case] partícula de destino/direção — に marca 流れ como aquilo em que eles montaram. 乗る pede に para o que se pega.
- **partícula** **て** [conjunctive] partícula conectiva (forma て) — て liga 乗る ao que vem depois (川) e encadeia os dois dentro da mesma frase.
- **partícula** **を** [case] marcador de objeto direto — を marca 川 como o objeto direto de 下る, ou seja, aquilo sobre o que a ação recai.
- **estrutura:** 彼ら é o tópico, com は. 流れに乗って usa に com 乗る (entrar na correnteza) e a forma て para encadear, e 川 leva を marcando o percurso percorrido; o predicado é 下った, passado de 下る.


---

## 9. Open items, handed on

1. **The 97 uncovered-target rows are NOT in.** `research/derived/mined_layerb_n3/batch-30.json`
   did not exist when this run reached its ingest step; it exists now and is complete (97 sentences,
   0 empty slots). It needs **a second run of the same script** and one thing before it: **0 of the
   97 keys have a row in `research/derived/repairs/sentence_register.json`**, because
   `derive_sentence_register_v2.py` reads only `accepted.json` and `generated.json`. The ingest
   refuses a row with no register rather than defaulting one, so all 97 would be refused today. The
   fix is one line — add `generated_uncovered_final.json` as a third W13 source to the derivation,
   re-derive, then run
   `ingest_mined_stages.py --apply --source research/derived/n3_mined/generated_uncovered_final.json
   --layerb research/derived/mined_layerb_n3 --tag n3-exemplification --provenance-source
   w13:n3-exemplification --batches 30`, then the relink `--derive --scope n3` again, then the
   exports. 36 of the 97 are real Tatoeba rows and 61 are generated.
2. **The 37 held relink links** (`held[]` in `research/derived/repairs/orthographic_relinks_n3.json`,
   each with the lesson↔sentence pair it would break) are W14's. Once W14 re-selects which sentence
   a lesson renders, most of them can land; the hold survives `--derive` so they cannot be
   re-admitted by accident.
3. **W18 owes the exam ceilings.** §5.1 raised five of them by 40 items with the work list attached.
   W18 regenerates all 40 banks from level-clean material and should zero them, not inherit them.
4. **`sentence.level` is stale by construction.** 703 sentences are filed below a component's level
   because the level is computed once at persist time. `recompute_all_levels()` exists; running it
   is a reviewed decision with an export diff, and it is now the largest single number in
   `integrity_audit`.
5. **Is the honorific prefix a vocabulary occurrence?** `vocab:2826528` 御/お took 163 of the 476
   derived links, is behind 4 of the 9 budget holds and 23 of the 40 exam items. The link is
   mechanically true and consistent with the already-applied N5/N4 table (ご/御 → `vocab:1270190`),
   so it was kept — but whether a bound morpheme's occurrences should count toward a vocabulary
   coverage floor at all is an owner/teacher call, not a linker's. The same question covers
   後/ご (`vocab:2147630`) and で (`vocab:2028980`, which guard 5 now refuses by rule).
6. **Romaji convention.** `dissect._GEMINATE_FIRST` is now empty, so っ before ち romanizes jaconv's
   way ("cch") everywhere, which is what the corpus already did in 30 sentences and 5 token
   boundaries. Traditional Hepburn says "tch". Moving the whole corpus is a convention decision with
   an export diff on every affected romaji field — its own unit.
7. **A manifest step writes tracked files out of a scratch rebuild.** Steps 80
   (`fix_stale_token_romaji.py`) and 110 (`migrate_grammar_merge.py`) write
   `research/derived/romaji_reading_disputes.json` and `research/derived/grammar_merge_ledger.json`
   REPO-relative, so a full replay dirties two tracked files with the SCRATCH tree's numbers. Both
   moved in this run. They should honour `--out-root` like the exporters do.
8. **Three particle rows have no `function_pt`** among the 10,257 ingested (the field is optional —
   `validate.py` requires the explanation, not the label — so nothing fails, but the slot is empty).
9. **`dbtarget.take_flag` was silently mis-targeting.** §1.3 fixed it for `--db`. Any other script
   that resolves `db_target()` after importing a module that already did was reading the live index
   while believing it had been redirected; worth a sweep.
