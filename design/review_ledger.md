# The approval ledger

**Decision D4 of [`research/reports/APP_PLAN.md`](../research/reports/APP_PLAN.md), taken as the
default.** An approval is recorded **per record and per locale**, **anchored to a content hash**, and
carries **`reviewed_by`** and **`approved_at`**. **It never expires.**

| file | what it is |
|---|---|
| `research/derived/review_ledger.json` | the entries. Starts empty, and empty is valid |
| `contracts/review_ledger.schema.json` | the hand-authored contract (in `build_schemas.LEDGER`, so nothing regenerates it) |
| `scripts/review_ledger.py` | the reader: parsing, addressing, anchoring. Imported by the exporter and by the gate |
| `scripts/validate/validate_review_ledger.py` | the gate |
| `scripts/review_queue.py` | the other end — the queue a teacher works, and `--subtract <ledger>` |

## Why each half of D4 is there

**Per record.** A count is not reviewable. `review_queue.py` already emits one row per record with its
id, and an approval has to be able to point back at that row, or a teacher cannot start, stop or
measure progress.

**Per locale.** `translation` is `{"pt-BR": …, "en": …}` where `en` is the Layer-A source and `pt-BR`
is ours. Approving the record would bless both, and the two were produced by different processes with
different trust. The locale is part of the address for the same reason the field is.

**Hash-anchored.** This is the half that had to be argued for, and the argument is a fact about this
session: four campaigns rewrote candidate text while the corpus was being built. An approval keyed
only on `(slug, field, locale)` would have transferred, intact and invisible, onto text no human ever
read. The anchor is what makes an approval a statement about *content* rather than about an *address*.
An entry with no `content_hash` is refused outright — not counted as a weaker approval, refused —
because an unanchored approval cannot tell "the teacher read this" from "the teacher read whatever
used to be here".

**`reviewed_by` / `approved_at`.** Required. The correction-rate metric (W39) is per reviewer, and an
anonymous approval is not a review. `approved_at` is provenance and ordering; **nothing reads it to
decide whether an approval still holds.**

**No expiry.** Time does not invalidate a review — a rewrite does, and the hash already catches that
exactly. A TTL would add a second, weaker invalidation rule that fires when nothing has changed, and
would silently un-approve a corpus nobody had touched.

## Addressing

```json
{"slug": "sent:tatoeba-83013", "field": "translation", "locale": "pt-BR",
 "content_hash": "9f2c…", "status": "approved",
 "reviewed_by": "teacher:ana", "approved_at": "2026-09-02", "note": "…"}
```

* `slug` — the published address. The integer `id` some registries carry is a storage row number and
  must never appear here (`contracts/README.md`).
* `field` — the reviewed field, or `"*"` for the whole record. `dissection` is a **virtual field**:
  the per-token glosses and particle explanations, reviewed as one artefact per locale, exactly as the
  queue presents them.
* `locale` — absent or `"*"` means locale-agnostic. Correct for a mechanical field, wrong for prose.
* `status` — `approved` | `rejected`. **Two values.** `review_queue.py` accepts a wider historical set
  on *read*, because it was proven against six differently-shaped ledgers; this is the shape we
  *write*, and a writer with six spellings of "yes" is a writer nobody can audit. This file owns that
  vocabulary (`x-vocabulary.owner: design`).

## The anchor is computed in exactly one place

`scripts/review_ledger.py` imports the hash functions from `scripts/review_queue.py` rather than
restating them, so the queue's `--subtract` join and the exporter's stamp can never drift apart:

| what is approved | the anchor |
|---|---|
| one locale of a locale-object field | `sha(text)` — NFC, then sha256 |
| an aggregate (`jp`, `dissection`, a form table) | `sha_json(value)` — canonical JSON, then sha256 |
| the whole record (`field: "*"`) | `sha_record(record)` |

`sha_record` hashes the record **minus its own `review_status` stamp**. Without that exclusion, writing
an approval into a record would change the hash the approval quotes, and the next export would report
every approval it had just made as stale.

A ledger may store a truncated digest: 8 hex characters or more join a full sha256 either way
(`hashes_join`), which is what lets a teacher paste the queue's 24-character short hash straight back.

## Live, stale, unresolvable — and which of the three is a failure

| state | meaning | export | gate |
|---|---|---|---|
| **live** | the anchor still matches what the record says today | `review_status` is stamped onto the record | counted |
| **stale** | the anchor no longer matches: a campaign rewrote the text after the review | **nothing is exported** | counted and listed, **not a failure** |
| **unresolvable** | the slug or the field does not exist in the export | nothing | **FAILURE** |

Stale is not an error. It is the record of work a campaign undid, and it is the single most useful
number in the report: it names exactly what has to be re-reviewed. Unresolvable *is* an error, because
an approval nobody can locate is unauditable in both directions — it can neither be honoured nor
retired.

The fourth case is the one that matters most: **a `review_status` in the export that no live entry
justifies is a hard failure.** That is what stops an approval being written into the data by hand, and
it is what makes the ledger — not the export — the source of truth about who approved what.

## What the exporter writes

Only onto records the ledger actually covers, and only while the anchor holds:

```json
"review_status": [
  {"field": "translation", "locale": "pt-BR", "status": "approved",
   "reviewed_by": "teacher:ana", "approved_at": "2026-09-02", "content_hash": "9f2c…"}
]
```

A record with no live verdict carries **no key at all**, so an empty ledger leaves the export
byte-identical. `review_status` is declared as an optional property on **every** generated entity
schema (`build_schemas.ALWAYS_PROPERTIES`) rather than measured from the data, so the first approval
in the project's history does not fail `validate_contracts.py` against an
`additionalProperties: false` record root.

## The build the approval was made against

An approval is anchored per record. `contracts/manifest.json` carries the build-level companion,
written by `scripts/contracts/build_manifest.py`:

```json
"build": {"date": "2026-09-02", "git_head": "8028ed2d…",
          "entities": {"vocab": "<sha256 over corpus/vocab/*.json>", "…": "…"}}
```

The catalogue used to say *what* exists and never *which version* of it: two exports taken mid-campaign
are the same 23 entities with the same record counts and different content, and nothing in `contracts/`
could tell them apart, so a bug report, a prototype sync or a teacher's session had no build to name.
Each entity hash folds every file its glob matches — the file's own digest under its repo-relative
path, in glob order — so a rename is a change and a reordering is not.

`validate_schema_generation_is_current.py` compares the whole manifest against a fresh regeneration
and exempts exactly two scalars, `build.date` and `build.git_head`: those differ tomorrow, or on
another commit, for reasons that have nothing to do with the contract. **`build.entities` is compared
exactly** — a hash that moved means the DATA moved and the committed catalogue is stale. Which is why
`build_manifest.py` runs after every export, not before.

## Working the loop

```bash
python scripts/review_queue.py --subtract research/derived/review_ledger.json   # what is left to do
# … a teacher records verdicts in research/derived/review_ledger.json …
python scripts/validate/validate_review_ledger.py                              # the gate
python scripts/export/export_corpus.py                                         # stamps the live ones
```

`review_queue.py --subtract` and `validate_review_ledger.py` answer two different questions on purpose:
the queue asks *what is still unreviewed*, the gate asks *is every claim in and about the ledger true*.
