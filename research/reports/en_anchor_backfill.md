# Layer-A English anchor — gap analysis and backfill

> **2026-08-27.** Applied. `scripts/apply_en_anchor_backfill.py` wrote 324 anchors to
> `db/corpus.sqlite` (`sentence.en`). No exporter was run — `corpus/sentences/bank.json` still shows
> the pre-backfill state until the next export. No git operations.

## Headline

| | count |
|---|---:|
| Records exporting with no `translation.en` (the gap) | **342** |
| Backfilled from Tatoeba's own direct pairings | **324** |
| Legitimately anchorless | **18** |

The gap is now 18, and every one of the 18 is anchorless for a reason recorded below. It is not a
residue — it is the correct answer for those records.

`translation.en` is what lets a reviewer or a validator check the Layer-B pt-BR against a Layer-A
source rather than taking the author's word for it (spec §1.1). A record without one is not invalid —
`contracts/common.schema.json`'s `LocaleText` requires only `pt-BR` — but it is unauditable, which is
why the sweep flagged it.

## 1. Which layer the gap was in

Both, and the same 342 records in each. The exporter coalesces two storage locations:

```python
# scripts/export/export_corpus.py:473
"translation": loc(pt=SL.get((sid, "translation")),
                   en=s["en"] or SLen.get((sid, "translation"))),
```

so a record is anchorless only when the `sentence.en` **column** is empty *and* there is no
`localized_text` row for `(sentence, id, 'translation', 'en')`. Before the backfill:

| | rows |
|---|---:|
| `sentence.en` column populated, no `localized_text` en row | 3,205 |
| `localized_text` en row present, column empty | 2,342 |
| **neither — the gap** | **342** |
| total sentences | 5,889 |

The two populated sets are disjoint — and they are not two eras of one field, they are two different
kinds of value (§4). The gap is not a migration artifact: these records never had an `en` in either
place. The set computed from the DB and the set computed from `corpus/sentences/bank.json` are
identical, element for element, so the JSON is a faithful mirror of the DB here and neither layer is
separately damaged.

### Breakdown of the 342

| slug family | source | `ai_generated` | count | verdict |
|---|---|---:|---:|---|
| `sent:tatoeba-*` | `tatoeba` (tags `["mined","stage:"]`) | 0 | **324** | defect — backfilled |
| `sent:tatoeba-*` | `tatoeba:<id>` | 0 | **12** | deliberate — left empty |
| `sent:gen-*` | `generated` | 1 | **6** | no source exists — left empty |

Corpus-wide, the gap was confined to two families: `tatoeba` (3,213 anchored / 336 not) and `gen`
(2,207 / 6). All 127 `jec` records were already anchored.

## 2. Root cause

One dropped dictionary key, in a JSON round-trip through an authoring pass.

`scripts/ingest/mine_tatoeba_stages.py` selects mined candidates and **requires** an English pairing —
`if len(text) > MAX_LEN or rid not in eng: continue` — then writes each candidate to
`research/derived/tatoeba_mined_stages.json` as `{tatoeba_id, jp, en, stage}`. At that point every
candidate has its anchor.

The pt-BR authoring pass that followed used a narrower row shape:

```
{tatoeba_id, jp, pt, pt_literal, register, reject, reject_reason}
```

`en` is not in it, and neither is `stage`. Those authored batches — `research/derived/mined_pt/batch-*.json`,
merged into `_accepted.json` — became the input to ingestion, in place of the mine output. So:

```python
# scripts/ingest/ingest_mined_stages.py:110 (before the fix)
"slug": slug, "jp": jp, "en": r.get("en"),      # r is an _accepted.json row -> always None
```

returned `None` 324 times out of 324, and `persist_dissection.persist()` then recorded the absence as a
fact about the translation:

```python
# scripts/ingest/persist_dissection.py:90
"en" if en else "dict",     # -> pt_validated_against='dict'
```

which is exactly the signature the data shows: all 342 gap records carry `pt_validated_against='dict'`.

**The corroborating detail.** Every one of the 324 is tagged `"stage:"` — the prefix with nothing after
it, from `f"stage:{r.get('stage', '')}"` on the next line. Two independent fields from the same artifact
came out empty in the same way. That rules out a lookup failure and pins the cause on the row shape:
the ingest read a file that never carried either key.

Nothing was corrupted and nothing was mislinked. A value was dropped, and no one downstream noticed,
because a missing optional field is indistinguishable from a field that was never meant to be there.

### The fix

`scripts/ingest/ingest_mined_stages.py` now reads the anchor from Layer A instead of trusting it to
survive the authoring round-trip:

```python
anchor = r.get("en") or (con.execute(
    "SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' "
    "ORDER BY trans_id LIMIT 1", (tid,)).fetchone() or (None,))[0]
```

The English belongs to the Japanese id, so the jp id is the right thing to key on — an intermediate
file is not. Re-running the patched ingest is a clean no-op (`{'already-banked': 324}`).

## 3. Where the backfilled English came from

Not from this session, and not from a model. `research/derived/tatoeba_mined_stages.json` still holds
the exact pairing the miner recorded before the authoring pass dropped it, so the repair replays a value
this project already had.

That matters for one specific reason: **63 of the 324 have more than one English row directly linked to
them upstream**, and the artifact says which one the pipeline chose. There was no tie to break and no
judgement call to make.

| direct English pairs upstream | records |
|---:|---:|
| 1 | 261 |
| 2 | 45 |
| 3 | 13 |
| 4 | 3 |
| 5 | 2 |

### Verification

Every value was checked twice, the second time against the compressed dumps themselves rather than the
ingested copy in SQLite — `jpn_sentences.tsv.bz2`, `links.tar.bz2` and `eng_sentences.tsv.bz2` under
`research/datasets/tatoeba/`, streamed directly:

| check | result |
|---|---|
| stored `jp` byte-identical to `jpn_sentences.tsv` | 324 / 324 |
| stored `jp` byte-identical to `raw_tatoeba_sentence` | 324 / 324 |
| backfilled `en` appears verbatim among that jp id's **direct** links in `links.csv` | 324 / 324 |
| `raw_tatoeba_translation` English set == raw dump English set, per record | 324 / 324 |

Every anchor is therefore a human-written English sentence that Tatoeba links directly to that exact
Japanese sentence id. No pivot, no translation of a translation, nothing authored.

The script enforces this independently at write time rather than relying on the artifact being right: it
refuses any value that is not present in `raw_tatoeba_translation` for that exact `jp_id` with
`lang='eng'`, refuses any record whose stored `jp` has drifted from the raw row, and re-asserts the
"currently empty" precondition inside the `UPDATE ... WHERE en IS NULL` itself.

## 4. The 18 that are legitimately anchorless

### 12 — a verified audit removed the pairing on purpose

These are the `source='tatoeba:<id>'` rows, and they are in the gap because they were **fixed**, not
because they were missed. `research/derived/qa_queues/round3/layer_a_pairing_verified.json` is a
two-round verified queue in which a reviewer confirmed, record by record, that the upstream Tatoeba
English does not say what the Japanese says, and that no better upstream row exists.
`scripts/apply_layer_a_pairing.py` then ran `UPDATE sentence SET en=NULL, pt_validated_against='dict'`
on each.

| slug | why the pairing was cut |
|---|---|
| `sent:tatoeba-77972` | JP is a partial negation on ～わけではない (denies liking *both*); EN denies liking *either*. Called out in the queue as the most consequential one. |
| `sent:tatoeba-77973` | Same defect, the ～というわけではない variant. |
| `sent:tatoeba-84279` | JP: becoming a failure is not permissible (～わけにはいかない, the record's own grammar target); EN states an inability. |
| `sent:tatoeba-4766` | JP verb means to punish/discipline (～てやる, the target); EN describes shooting someone. |
| `sent:tatoeba-233703` | JP ～てほしい on the verb for *meeting*; EN says *go* — the target verb itself. |
| `sent:tatoeba-203508` | JP concessive is about leaving home; EN says selling a house. |
| `sent:tatoeba-219421` | JP counts three problems; EN counts three opinions. |
| `sent:tatoeba-227760` | JP is the humble formula for the speaker keeping well; EN reports a plural third party. |
| `sent:tatoeba-187583` | JP asks what the listener intends to do (honorific verb, the target); EN is the idiom for what they are implying. |
| `sent:tatoeba-175272` | JP: dogs can tell black from white (fixed expression); EN asserts something else. |
| `sent:tatoeba-195360` | JP is the set idiom for being completely at a loss; EN shares no content with it. |
| `sent:tatoeba-9454297` | Confirmed mismatch **and** confirmed absence of any re-link target. |

Re-linking these from the same upstream data would undo a human-verified correction and put the exact
defect back. The backfill script refuses them **by slug, loudly, with the reviewer's reason printed on
every run**, rather than filtering them out quietly — the reasoning has to stay visible, because the
next person to look at "12 records still missing an anchor" will otherwise try to fix it again.

This is also why the number to remember is 324 and not 336. The two sets are indistinguishable by shape:
all 336 are `sent:tatoeba-<id>` slugs, all 336 have at least one directly linked English row upstream,
and all 336 would have backfilled cleanly. Only the audit trail separates them.

### 6 — AI-generated Japanese, so no human English exists

`sent:gen-686faf1ec51d`, `sent:gen-aef805c4840d`, `sent:gen-cb6562f41e17`, `sent:gen-b2ed6e8bb267`,
`sent:gen-8cc2f196d1e9`, `sent:gen-b7b28dfc0928` — all `ai_generated=1`, all tagged `reauthored`.

There is no Layer-A English to point at, because the Japanese itself is not Layer A. Writing English
into the anchor slot would launder model output as authoritative source data, which is the defect class
`apply_layer_a_pairing.py`'s docstring names as the worst one in this project. The contract makes `en`
optional precisely so this case has a correct representation, and empty is it.

The other 2,207 `sent:gen-*` records do export an `en`, but it is **not** an anchor — see below. Its
presence there is not evidence that these six are missing anything.

### The export conflates two different kinds of `en`

Worth stating, because it changes how the headline number should be read. The two storage locations the
exporter coalesces are not two eras of the same thing — they hold different *kinds* of value, and the
split is perfectly clean:

| where | what it is | rows |
|---|---|---:|
| `sentence.en` column | **Layer-A anchor** — verbatim upstream English | 3,529 |
| `localized_text` (`layer='B'`) | **Layer-B sibling** — derived English, an output not a source | 2,342 |
| neither | | 18 |

There is **zero** overlap, and the column is 100% non-AI in origin: 3,402 Tatoeba + 127 JEC, `ai_generated=0`
on every one. The `localized_text` side is 2,207 AI-generated sentences plus 135 Tatoeba-sourced ones.

Those 135 look at first like a second gap — real Japanese, but the only English is derived. They are not.
Every one of the 135 is a Tatoeba sentence with **no English pairing upstream at all** (0 of 135 have any
`lang='eng'` row for their jp id), which is precisely the "Tatoeba links with no en pair" case: not
anchorable, correctly carrying a derived English marked `layer='B'`, and correctly *not* claiming to be
Layer A. Nothing to repair.

The practical consequence is for consumers, not for the data: in `bank.json` both kinds arrive as
`translation.en` with nothing to tell them apart, so anything treating `translation.en` as ground truth
is right about 3,529 records and wrong about 2,342. The provenance is intact in the DB; it is the export
shape that loses it.

## 5. What was deliberately not changed

**`pt_validated_against` stays `'dict'` on all 324.** The field records what the pt-BR was actually
checked against. These translations were authored from the Japanese and reviewed by two independent
checkers who never saw this English (`_accepted.json`: *"adversarially verified by 2 independent
checkers per batch"*). Flipping it to `'en'` because an anchor now exists would assert a validation that
did not happen. The anchor makes that validation possible; it is not the validation. If someone wants
`'en'` on these records, the honest route is to run the pt↔en check and set the field as its output.

**`localized_text` was not touched.** The count of `(sentence, translation, en)` rows is 2,342 before
and after. The backfill writes `sentence.en`, which is the column the exporter reads first and the
column `persist_dissection.persist()` would have filled had the value survived — the minimal change that
puts the value where the broken code path was supposed to put it.

**The empty `stage:` tag was left alone.** Out of scope for this task, but worth recording: all 324 are
tagged `"stage:"` with no value, from the same dropped-key defect. The mine artifact still has it
(`lodging` 111, `opinions` 108, `past_stories` 105), so it is fully recoverable the same way, and the
patched ingest line does not fix it. It is a separate repair.

## 6. Files

| path | what |
|---|---|
| `scripts/apply_en_anchor_backfill.py` | the backfill. `--check` reports without writing; idempotent; DB only. |
| `scripts/ingest/ingest_mined_stages.py` | patched so the anchor is read from Layer A, not from the authoring artifact. |
| `research/derived/tatoeba_mined_stages.json` | the miner's own record of the pairing — the source the backfill replays. |
| `research/derived/qa_queues/round3/layer_a_pairing_verified.json` | the verified unlink decisions the backfill refuses to override. |

Re-running `apply_en_anchor_backfill.py` reports `backfilled 0` and `18 record(s) currently export with
no translation.en`, exit 0.

**Next step for the orchestrator:** re-run the corpus exporter so `corpus/sentences/bank.json` carries
the 324 anchors.
