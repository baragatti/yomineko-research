# W38 — teacher tooling: the review views and the flow-back

APP_PLAN **W38**, second half. The queue half (`scripts/review_queue.py`) already existed; what was
missing is everything a named teacher (**D4**) needs to actually *work* N5 while Opus campaigns run
on N3 — readiness findings **G9** ("no human-readable view for corpus registries") and **G12** ("no
path from an approval or a teacher edit into the committed JSON").

**Landed.** Four artifacts, no DB written, no exporter run against the real tree:

| what | where |
|---|---|
| view generator | `scripts/export/build_review_views.py` |
| the N5 views | `research/review/<registry>/<level>.md` (8 files, 5.3 MiB) |
| the flow-back | `scripts/review_apply.py` |
| its tests | `scripts/validate/test_review_apply.py` — 9 cases, 0 FAIL |
| teacher instructions (pt-BR) | `research/review/README.md` |
| a blank sheet to copy | `research/review/sheets/EXEMPLO-n5-grammar.json` |

---

## 1. What existed per registry before this unit, and what exists now

**Nothing under `corpus/` had a review view.** Eleven `INDEX.md` files exist, and every one of them
is a *listing*: one line per record with a headword and a comma-joined gloss, or — for `readings`,
`exam_banks`, `capabilities`, `strokes` — a paragraph of prose plus a file-and-count list. None of
them prints an explanation, a note, a `needs_review` flag, a layer, a content hash or a ledger
verdict, so none of them can be reviewed *from*. Only `course/**/lesson-NN.md` was a real per-record
view, and `validate_md_views.py` was already holding it byte-identical.

| registry | before | now (`research/review/…`) | records | review addresses | `needs_review` in the export |
|---|---|---|--:|--:|--:|
| vocab | `corpus/vocab/INDEX.md` — one line per record (headword, kana, level, gloss) | `vocab/n5.md` | 705 | 1,410 | 0 (flags are DB-only — G4) |
| kanji | `corpus/kanji/INDEX.md` — one line per record | `kanji/n5.md` | 103 | 434 | 0 (DB-only — G4) |
| grammar | `corpus/grammar/INDEX.md` — one line per record, explanation column literally reads `authored` | `grammar/n5.md` | 150 | 1,505 | 150 |
| sentences | `corpus/sentences/INDEX.md` — jp + translation, one line | `sentences/n5.md` | 506 | 5,046 | 506 |
| families | `corpus/families/INDEX.md` — one line per family | `families/n5.md` | 330 | 1,650 | 330 |
| readings | `corpus/readings/INDEX.md` — prose + 3 file counts, **no per-record view at all** | `readings/n5.md` | 43 | 258 | 43 |
| exams | `corpus/exam_banks/INDEX.md` — prose + 26 file counts, **no per-record view at all** | `exams/n5.md` | 1,667 | 2,966 | 383 |
| speak | `course/speak/INDEX.md` — a 12-row stage table | `speak/speak.md` | 72 | 144 | 72 |

**Totals for N5: 3,576 records, 13,413 reviewable (field, locale) addresses.**

Three design points worth recording:

* **The addresses a view offers are exactly the addresses the ledger can honour.** Every hash printed
  is produced by calling `review_ledger.live_anchor(record, field, locale)` — the same function the
  exporter's stamp and `validate_review_ledger.py` call. A field `live_anchor` cannot resolve is
  printed as *context* and never as a target, so this generator cannot manufacture an approval the
  gate would later call **unresolvable**, which is the ledger's one hard failure.
* **Sentences appear in the level of every lesson that shows them,** not only in their own grade —
  `sentences/n5.md` holds 506 records, exactly `review_queue.in_n5_slice`'s N5 count (445 graded n5
  plus 61 an N5 lesson displays). A family appears in each level it spans.
* **Nothing reviewable is truncated.** A view that elides the text being approved turns an approval
  into a signature on unread prose. That is where the 5.3 MiB comes from; it is the corpus text.

Order is course order — module → topic → lesson — with unplaced records last, by id. `--check`
re-renders into memory and diffs against disk; a second run over an unchanged tree rewrites **0
files**, proven with `PYTHONHASHSEED` varied between runs.

---

## 2. The sheet format

JSON (YAML accepted when PyYAML is importable; identical keys). One record per entry, one verdict
per address:

```json
{
  "schema_version": "1.0",
  "sheet_id": "n5-grammar-01",
  "reviewed_by": "teacher:ana",
  "reviewed_at": "2026-09-09",
  "records": [
    {"id": "gram:da-desu",
     "record_hash": "214761a689ba9caf",
     "approve": ["explanation@pt-BR", "label@pt-BR"],
     "edit":    {"formation@pt-BR": "Substantivo + です／だ: 先生です／先生だ. …"},
     "reject":  {"nuance@pt-BR": "mistura だ com である; precisa ser reescrito"},
     "note":    "opcional; vai para o ledger"}
  ]
}
```

* An **address** is `field` or `field@locale`, copied verbatim from the view's own `###` headings.
  `*` is the whole record.
* **`record_hash`** is the anchor of the whole sheet, taken from the view's `*` block.
  `python scripts/review_apply.py --template <registry> <level>` writes a blank sheet with the ids,
  the hashes and each record's address list already filled in, so nothing is hand-copied.
* A field may appear in **exactly one** of `approve` / `edit` / `reject`.

What the script does with it:

| input | output |
|---|---|
| `approve` / `reject` | one ledger entry each, anchored by `live_anchor`, appended to `research/derived/review_ledger.json`. Re-running the same sheet adds nothing. |
| `edit` | one row in `research/derived/repairs/pending/<sheet_id>.json`, shape `{entity, slug, field, locale, old, new, why, reviewed_by, reviewed_at, source_sheet, old_hash}` — `old` is the **exact** live text. **Not applied**; the apply command is printed. |
| a stale `record_hash` | the **whole sheet** is refused, exit 2, nothing written — including the records that were still current. A campaign rewrote the corpus under the teacher, so every verdict on that sheet was formed against text that may no longer be there. |
| an unknown id, an unresolvable address, a field claimed twice, a missing `reviewed_by`, an edit on a non-string field | refused with the reason, nothing written |

**Why `repairs/pending/` and not `repairs/`.** `validate_repairs_applied.py` FAILS on any
unregistered `*.json` directly under `research/derived/repairs/` *and* asserts every row's `new` is
already in the export. An unapplied table there would break the suite the moment a teacher wrote it.
The subdirectory is invisible to that gate (`rdir.glob("*.json")` is not recursive). Promoting a
table — move it up one level, register it in `REGISTRY` — is the last step of the apply, not the
first step of the review.

**The script never opens a database.** Test case 8 points `$YOMINEKO_DB` at a path that does not
exist and asserts it was never created, and checks `db/corpus.sqlite`'s size and mtime across the
run. Applying an edit table is a separate, DB-writing step; for `sentence.structure_explanation` and
`sentence.translation_literal` the existing `scripts/apply_sentence_text_repairs.py --data <table>`
consumes our rows verbatim, and the script prints that command. For anything else it says plainly
that an applier has to be written, rather than naming one that does not exist.

**It never writes prose.** Every `new`, `why` and `note` in both outputs comes from the sheet.

Tests (`scripts/validate/test_review_apply.py`, all against a fixture tree in a temp dir built from
real records, with `--root` and `--review-ledger` redirected): template, approve, idempotent
re-run, edit, reject, stale hash, unknown id, no-DB, and — case 9 — `validate_review_ledger.py
--root <fixture>` green over what the sheets wrote, which is the end-to-end proof that an entry this
script produces is live and locatable.

---

## 3. Suite registration to add later

`scripts/validate/validate_all.py` and `scripts/validate/README.md` are being edited by another unit,
so nothing was registered from here. Two lines to add, both in the `# --- W38 teacher tooling ---`
group near `validate_review_ledger.py`:

```python
    ("test_review_apply.py", "code"),            # sheet -> ledger + repair table, 9 behaviour cases
    ("validate_review_views.py", "code"),        # views byte-identical; every sheet applied or listed
```

`test_review_apply.py` **exists and passes today** — it builds its own fixture, needs no arguments,
exits 1 on failure, and touches nothing outside a temp directory.

`validate_review_views.py` still has to be written. It is two assertions and ~60 lines:

1. **Views are current.** `build_review_views.main(["--check", "--level", <every level with a file
   on disk>])`, or the same comparison inline: re-render each `research/review/<registry>/<level>.md`
   and require **byte** equality. Deriving the level list from the files present is what keeps the
   gate honest when N4 and N3 views are generated later. `research/review/README.md` and
   `research/review/sheets/**` are hand-written and must be skipped.
2. **No sheet is stranded.** For every `research/review/sheets/*.json` that carries at least one
   verdict (a blank `--template` output carries none and is not a sheet yet): either every
   `approve`/`reject` address of it is present in the ledger, or every `edit` address of it appears
   in a table under `research/derived/repairs/pending/` or in an applied table under
   `research/derived/repairs/`. Otherwise the sheet is listed as **unprocessed** and the gate fails.
   That is the check that stops a teacher's afternoon from evaporating because nobody ran
   `review_apply.py`.

**Plant proof required before registration** (APP_PLAN §1): copy the validator plus its
`scripts/export` imports into a fixture tree, then (a) hand-edit one byte of a view and assert
FAIL, (b) drop a filled sheet with no matching ledger entry and assert FAIL, (c) restore and assert
PASS. Copying the imports into the fixture is not optional — a validator left importing the real
repo reads the real tree and passes falsely (memory: `validator-plant-proof-root`).

**One finding for whoever writes it.** `review_queue.py` and `review_ledger.py` do not agree on
every aggregate address. The queue emits targets the ledger cannot recompute — exam `item` and
lesson `exercise:<id>` are synthetic names `live_anchor` resolves to *nothing* (a hard FAILURE if a
teacher ever quotes one back), and `objectives`, `forms`, `production` are hashed by the queue over
a per-locale projection but by the ledger over the whole stored field, so an approval copied from
the queue lands as permanently **stale**. The views sidestep this by deriving every address from
`live_anchor` itself, but the queue is what a teacher reads first. Fixing it means either teaching
`live_anchor` those virtual fields (the `dissection` precedent) or narrowing the queue's targets —
a small unit, and it belongs before a named teacher starts quoting queue hashes.

---

## 4. What W39 still needs from the owner

W39 is **D4-BLOCKING** and the block is one sentence long: **a named reviewer.**

* **The handle.** `reviewed_by` is required on every entry and the W39 correction-rate metric is per
  reviewer. It must be a stable handle, not a mailbox — `teacher:ana`, decided once, used forever.
  Everything else is built: the views, the sheets, the ledger, the gate, the queue's `--subtract`.
* **The starting slice.** N5 is generated. 3,576 records / 13,413 addresses is more than one person
  reads; the plan's own priority is layer **C** first (grammar 1,505 addresses, readings 258, speak
  144, the 383 authored exam items), which is ~2,300 addresses and a realistic first pass. A ruling
  on whether the teacher signs whole records (`*`) or single fields changes that number by roughly
  4×, and the tooling supports both.
* **Two decisions the tooling exposes and cannot make.**
  * **`vocab.senses` and `kanji.readings` are approvable only as a whole.** They are the finest
    addresses `live_anchor` resolves, so one verdict covers every sense of a word. Worse, the
    aggregate hash includes each sub-record's own `needs_review` bookkeeping, so W05 exporting those
    flags will invalidate every approval made against them. If per-sense approval matters, it is a
    virtual field (`glosses`) in `review_ledger.py`, exactly like `dissection` — cheap now,
    expensive after a teacher has worked a thousand words.
  * **vocab and kanji carry no `needs_review` in the export at all** (G4: 14,958 flags held only in
    `db/corpus.sqlite`). The views say so per record rather than printing a false "não". Until W05
    exports them, a teacher working vocab is reading an unprioritised list.
* **What is NOT blocked.** The ledger, the views and the flow-back all work with an empty ledger and
  no named reviewer. Nothing here waits on the owner; only the reviewing does.
