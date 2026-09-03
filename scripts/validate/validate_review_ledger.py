#!/usr/bin/env python3
"""Hard gate: the approval ledger and the export agree about who approved what.

The ledger (`research/derived/review_ledger.json`, APP_PLAN decision D4, specified in
`design/review_ledger.md`) is the only place an approval may be asserted. The export carries
`review_status` stamps, but those are a PROJECTION of the ledger written by `export_corpus.py`, not a
second source of truth — and a projection nobody re-derives is how a hand-edited "approved" ships.

WHAT IT CHECKS
--------------
  1  THE LEDGER PARSES. Every entry is well-formed under scripts/review_ledger.py: a prefixed slug, a
     field, a hash of at least 8 hex characters, a status from the two the design owns, a reviewer and
     a date. A malformed entry FAILS rather than being skipped — a ledger that silently drops what it
     cannot read reports fewer approvals than a teacher made, which nobody would notice.

  2  EVERY ENTRY CHAINS. The slug names a record in the export, and the field exists on it. An
     approval of a record or a field nobody can find is unauditable in both directions: it can neither
     be honoured nor retired, so it FAILS. When an entry names an `entity`, it must be the entity the
     record was actually found in.

  3  LIVE vs STALE. The anchor is recomputed from the export with the same functions review_queue.py
     used to build the queue the teacher worked (design/review_ledger.md has the table). A hash that
     still matches is LIVE. A hash that no longer matches is STALE — the reviewer approved real text
     and a later campaign rewrote it — and staleness is COUNTED AND LISTED, NOT FAILED. It is the
     record of work a campaign undid, and it is the number that says what has to be re-reviewed.

  4  NO STAMP WITHOUT A LIVE ENTRY. Every `review_status` in the export must be justified, field for
     field, by a live ledger entry — same status, same reviewer, same date, same anchor. This is the
     check that makes the ledger the source of truth: writing "approved" into a record by hand, or
     leaving a stamp behind after the text was rewritten, fails here and nowhere else.

  5  NO CONTRADICTION. Two entries that address the same (slug, field, locale) with the same anchor
     and different verdicts FAIL: the export cannot stamp both, and picking one would be a coin toss.

An EMPTY ledger passes with 0 entries — that is the correct state before a teacher has started, and
the file existing while empty is what makes "nobody has reviewed this" a checkable claim. The file
NOT existing fails.

Reads:  research/derived/review_ledger.json, contracts/manifest.json, and every entity glob the
        manifest declares. Writes: nothing.
Usage:  validate_review_ledger.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterator

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO = Path(__file__).resolve().parents[2]
# The ledger reader is CODE and lives with the code, so it is imported from the repo rather than from
# --root (which points at data, and may be a mutated copy of the tree with no scripts/ in it) — the
# same rule validate_provenance_json.py follows for the exam derivation contract.
sys.path.insert(0, str(REPO / "scripts"))
from dbtarget import take_flag  # noqa: E402
from review_ledger import (  # noqa: E402
    LEDGER_REL, STAMP_KEY, hashes_join, live_anchor, read_entries,
)

MAX_REPORT = 20
STAMP_FIELDS = ("field", "locale", "status", "reviewed_by", "approved_at", "content_hash")
# The ledger entity itself is a contract over the ledger FILE; it holds no reviewable records.
SKIP_ENTITIES = {"review_ledger"}


def records_of(path: Path, packing: str, rel: str) -> Iterator[tuple[str, dict]]:
    """Yield (locator, record) — the same packing rules validate_contracts.py uses."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if packing == "single":
        if isinstance(data, dict):
            yield rel, data
    elif packing == "map":
        for k, v in (data or {}).items():
            if isinstance(v, dict):
                yield f"{rel}[{k}]", v
    elif isinstance(data, list):
        for i, rec in enumerate(data):
            if isinstance(rec, dict):
                yield f"{rel}[{rec.get('slug') or rec.get('id') or f'#{i}'}]", rec


def address_of(rec: dict) -> str | None:
    """A record's published address, the way review_queue.py addresses it: `slug` where a registry has
    one, `id` where the id IS the address (lessons, speak units, exam items)."""
    for field in ("slug", "id"):
        val = rec.get(field)
        if isinstance(val, str) and ":" in val:
            return val
    return None


def index_export(root: Path) -> tuple[dict[str, tuple[str, str, dict]], list[str], int]:
    """address -> (entity, locator, record), over every entity the manifest declares."""
    manifest_path = root / "contracts" / "manifest.json"
    if not manifest_path.exists():
        return {}, [f"no contracts/manifest.json under {root} — the entity list comes from it"], 0
    entities = json.loads(manifest_path.read_text(encoding="utf-8"))["entities"]
    index: dict[str, tuple[str, str, dict]] = {}
    problems: list[str] = []
    n_files = 0
    for ent in entities:
        glob = ent.get("files")
        entity = ent["entity"]
        if not glob or entity in SKIP_ENTITIES:
            continue
        packing = ent.get("packing") or "list"
        for path in sorted(root.glob(glob)):
            n_files += 1
            rel = path.relative_to(root).as_posix()
            for locator, rec in records_of(path, packing, rel):
                addr = address_of(rec)
                if addr is not None:
                    index.setdefault(addr, (entity, locator, rec))
    return index, problems, n_files


def stamp_key(stamp: dict) -> tuple:
    return tuple(stamp.get(f) for f in STAMP_FIELDS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 20")
    # Consumed BEFORE argparse (scripts/dbtarget.take_flag), so the falsifiability proofs can point
    # this gate and the exporter at the same mutated ledger without editing the committed one. The
    # default never moves: no flag, no env, and it is root/research/derived/review_ledger.json.
    redirect = take_flag("--review-ledger") or os.environ.get("YOMINEKO_REVIEW_LEDGER")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    ledger = Path(redirect) if redirect else root / LEDGER_REL
    shown_ledger = ledger.as_posix() if redirect else LEDGER_REL

    fails: list[str] = []
    entries, errors = read_entries(ledger)
    fails.extend(errors)

    index, problems, n_files = index_export(root)
    fails.extend(problems)
    if not index and not problems:
        fails.append(f"the export under {root} holds no addressable record — nothing could be checked, "
                     f"which is a broken tree, not a clean ledger")

    live: list[tuple] = []                       # justified stamps, as stamp_key tuples per address
    live_by_address: dict[str, set[tuple]] = defaultdict(set)
    stale: list[str] = []
    by_target: dict[tuple, list] = defaultdict(list)
    per_entity: Counter = Counter()

    for entry in entries:
        found = index.get(entry.slug)
        if found is None:
            fails.append(f"{shown_ledger}[{entry.index}]: {entry.address} — no record in the export has "
                         f"the address {entry.slug!r}. An approval nobody can locate can neither be "
                         f"honoured nor retired.")
            continue
        entity, locator, rec = found
        if entry.entity and entry.entity != entity:
            fails.append(f"{shown_ledger}[{entry.index}]: {entry.address} — the entry says entity "
                         f"{entry.entity!r}, but {entry.slug} is a {entity} ({locator})")
        anchor, how = live_anchor(rec, entry.field, entry.locale)
        if anchor is None:
            fails.append(f"{shown_ledger}[{entry.index}]: {entry.address} — {how}. The approval "
                         f"addresses something the record does not have, so it can never be checked.")
            continue
        by_target[(entry.slug, entry.field, entry.locale, anchor)].append(entry)
        if not hashes_join(anchor, entry.content_hash):
            stale.append(f"{entry.address} ({entity}) — approved `{entry.content_hash[:12]}`, the "
                         f"{how} now hashes `{anchor[:12]}`")
            continue
        per_entity[entity] += 1
        live.append((entry.slug, entry.field, entry.locale))
        live_by_address[entry.slug].add(stamp_key(entry.stamp()))

    # ---- 5: two live verdicts over the same anchor may not disagree -------------------------------
    for (slug, field, locale, _anchor), group in sorted(by_target.items()):
        verdicts = {e.status for e in group}
        if len(verdicts) > 1:
            fails.append(f"{shown_ledger}: {slug} · {field} [{locale or '*'}] carries "
                         f"{sorted(verdicts)} over the SAME content hash — the export cannot stamp "
                         f"both, and choosing one would be a coin toss")

    # ---- 4: every stamp in the export is justified by a live entry --------------------------------
    stamped_records = 0
    stamped_total = 0
    for addr, (entity, locator, rec) in sorted(index.items()):
        stamps = rec.get(STAMP_KEY)
        if stamps is None:
            continue
        stamped_records += 1
        if not isinstance(stamps, list):
            fails.append(f"{locator}: `{STAMP_KEY}` is {type(stamps).__name__}, expected a list of "
                         f"verdicts (contracts/*.schema.json, design/review_ledger.md)")
            continue
        justified = live_by_address.get(addr, set())
        for stamp in stamps:
            stamped_total += 1
            if not isinstance(stamp, dict):
                fails.append(f"{locator}: a `{STAMP_KEY}` entry is {type(stamp).__name__}, "
                             f"expected an object")
                continue
            if stamp_key(stamp) not in justified:
                fails.append(
                    f"{locator}: `{STAMP_KEY}` claims {stamp.get('status')!r} on field "
                    f"{stamp.get('field')!r} [{stamp.get('locale') or '*'}] by "
                    f"{stamp.get('reviewed_by')!r}, and NO LIVE ENTRY in {shown_ledger} says so. Either "
                    f"it was written by hand, or the text was rewritten after the review and the "
                    f"export was not regenerated. The ledger is the source of truth; the export is a "
                    f"projection of it.")

    # ---- report ----------------------------------------------------------------------------------
    print("============== REVIEW LEDGER GATE ==============")
    print(f"  ledger: {shown_ledger} — {len(entries)} entr(y/ies) over {len(index):,} addressable "
          f"records in {n_files} file(s)")
    print(f"  live {len(live)} · stale {len(stale)} · stamps in the export {stamped_total} on "
          f"{stamped_records} record(s)")
    if per_entity:
        print("  live verdicts by entity: "
              + ", ".join(f"{k} {v}" for k, v in sorted(per_entity.items())))
    if not entries:
        print("  the ledger is EMPTY, which is the correct state before a teacher has started: the "
              "file exists, so 'nobody has reviewed this' is a checkable claim rather than an absence")
    if stale:
        print(f"\n  STALE — approved, then rewritten. Not a failure; this is the re-review list "
              f"({len(stale)}):")
        for line in (stale if args.list else stale[:MAX_REPORT]):
            print(f"    {line}")
        if len(stale) > MAX_REPORT and not args.list:
            print(f"    ... {len(stale) - MAX_REPORT} more (use --list)")

    if fails:
        print()
        shown = fails if args.list else fails[:MAX_REPORT]
        for f in shown:
            print("  FAIL", f)
        if len(fails) > len(shown):
            print(f"  ... {len(fails) - len(shown)} more (use --list)")

    print(f"\nvalidate_review_ledger: {len(entries)} entries, {len(live)} live, {len(stale)} stale, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
