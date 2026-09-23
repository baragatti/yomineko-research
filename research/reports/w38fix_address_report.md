# C11-W38fix: the queue and the ledger agree on every review address

APP_PLAN **W38**, the open item from `w38_tooling_report.md` §3. No DB write, no corpus or course
data changed. Code only, plus the regenerated queue artifact.

## The defect

`scripts/review_queue.py` hands a teacher a target list with a content hash per (field, locale).
`scripts/review_ledger.live_anchor` recomputes that hash when an approval comes back. Over the
current export the two disagreed on **6,977 of 88,149 targets**:

| entity · target | targets | what `live_anchor` did |
|---|---:|---|
| lesson `exercise:<id>` | 4,746 | unresolvable (no such field): a quoted approval is a hard FAIL of the ledger gate |
| exam_item `item` | 725 | unresolvable, same |
| grammar_point `forms` [pt-BR / en] | 720 | hashed the whole stored table; the queue hashed a per-locale slice, so the approval is born stale |
| lesson `objectives` [pt-BR] | 322 | same (whole list vs per-locale list) |
| lesson `body` [pt-BR] | 322 | not in the §3 finding: the queue used `sha(text)`, the ledger `sha_json(text)` |
| speak_unit `production` [pt-BR] | 71 | whole list vs projected list |
| speak_unit `fluency` [pt-BR] | 71 | not in the §3 finding: the queue hashed the prompt text, the ledger the whole `fluency` object |

## The fix (one place)

`review_queue.py` now owns every payload that is not a stored value hashed as-is:
`projection(rec, field, locale)` plus `is_projected(field, locale)`, backed by one `PROJECTORS`
table (`dissection`, `item`, `forms`, `objectives`, `production`, `fluency`) and the
`exercise:<id>` prefix. The collectors call it to build the target; `live_anchor` calls it to
re-anchor. Nobody restates a payload, so the two can no longer drift.

* **Virtual** (`dissection`, `item`, `exercise:<id>`): always projected.
* **Stored** (`forms`, `objectives`, `production`, `fluency`): projected only when the address names
  a locale. Without one, `live_anchor` still hashes the whole stored field, which is the `forms`
  address `build_review_views.py` prints. So no view address or hash moved: the 8 views differ from HEAD only in the manifest build-stamp line.
* Lesson `body` is now built by `add_aggregate_target`, i.e. `sha_json`, like every plain field.
* `EXAM_BOOKKEEPING` gained `review_status`, so an exported stamp can never invalidate the `item`
  approval that caused it (same rule `sha_record` already follows). No hash moved today: the ledger is
  empty and nothing is stamped.

Hashes that changed: `body` (322) and `fluency` (71). No ledger entry or sheet quoted either (ledger
empty, the only sheet is a blank template), so nothing was invalidated.

## The check left behind

`scripts/validate/validate_review_ledger.py` **check 6**: every target the queue offers on a record
the export can address must re-anchor through `live_anchor` to the queue's own hash. Today: 88,148 /
88,148. Plant proof with the code copied into a fixture tree and data read via `--root`
(memory: validator-plant-proof-root): clean PASS, (a) `forms` un-projected on the ledger side FAIL,
(b) `body` hashed raw again FAIL, (c) `exercise:` addresses unresolvable FAIL, restored PASS. A plant
inside the shared projector moves both sides at once and correctly passes: that is the point.

## Numbers

* Queue regenerated: 12,110 records / 88,149 targets. The committed artifact was stale since
  2026-09-02 (8,328 / 58,765), so most of its diff is three weeks of corpus work, not this unit.
* `test_review_apply.py` 9/9, `validate_review_views.py` OK, `validate_all.py` green (quick replay included).
* Rendered `course/` diff against HEAD: empty (no course data touched).

## Residue (advisory, not failed)

One `vocab_disambiguation` row (`disamb:<chosen>@<lesson>`) has no address in the export: the items
in `course/vocab_disambiguation_review.json` carry no slug, so an approval of it cannot chain. Check 6
prints it as advisory. Fixing it means giving those items a published id in the exporter, which is a
data change for its own unit.
