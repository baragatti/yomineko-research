#!/usr/bin/env python3
"""W06 — the approval ledger: how a teacher's sign-off is addressed, anchored, and spent.

APP_PLAN decision D4, taken as the default: an approval is **per record and per locale**, anchored to
a **content hash**, carries `reviewed_by` and `approved_at`, and **never expires**. There is no TTL
because time is not what invalidates a review — a REWRITE is. Four campaigns rewrote candidate text
in a single session; an approval that survived that would certify text no human ever read.

WHERE IT LIVES
    research/derived/review_ledger.json      the entries (starts as `{"entries": []}`, which is valid)
    contracts/review_ledger.schema.json      the hand-authored contract for that file
    design/review_ledger.md                  the decision, the addressing rules, the failure modes

ONE ENTRY
    {"slug": "sent:tatoeba-83013",       # the record's published address
     "field": "translation",             # "*" = the whole record
     "locale": "pt-BR",                  # omit or "*" for a locale-agnostic approval
     "content_hash": "<sha256 hex>",     # what the reviewer actually read
     "status": "approved",               # approved | rejected
     "reviewed_by": "teacher:ana",
     "approved_at": "2026-09-02",
     "note": "..."}                      # optional, internal (never learner-facing)

THE ANCHOR, AND WHY IT IS COMPUTED HERE AND NOWHERE ELSE
-------------------------------------------------------
`scripts/review_queue.py` hands a teacher a queue whose every target already carries the sha256 of the
exact text. An approval quotes that hash back. For the join to be exact, the exporter and the gate must
recompute the anchor the SAME way the queue computed it, so this module imports the queue's own hash
functions rather than restating them:

    field "*"                     -> sha_record(record)  - the record minus its own review_status stamp
    locale-object field + locale  -> sha(text)           - matches add_locale_targets()
    anything else                 -> sha_json(value)     - matches add_aggregate_target()
    "dissection"                  -> sha_json(the per-locale dissection payload the queue builds)

`sha_record` excludes the exporter's `review_status` stamp on purpose. Without that exclusion a
whole-record approval would invalidate itself the moment the exporter wrote the approval into the
record, and the second export would report every approval it had just made as stale.

WHAT "STALE" MEANS
------------------
An entry whose anchor no longer matches the live value is STALE, not wrong: the reviewer really did
approve something, and a later campaign rewrote it. A stale entry exports NOTHING and is reported by
`scripts/validate/validate_review_ledger.py` and by `review_queue.py --subtract`. It is never an error
to hold one — it is the record of work a campaign undid — so the gate counts stale entries and does
not fail on them. What the gate DOES fail on is an entry that cannot be checked at all (a slug or a
field that does not exist) and a `review_status` in the export that no live entry justifies.

Reads:  research/derived/review_ledger.json. Writes: nothing.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any, Iterable

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from dbtarget import take_flag  # noqa: E402
from review_queue import (  # noqa: E402
    APPROVING_STATUSES,
    REJECTING_STATUSES,
    dissection_payload,
    hashes_join,
    is_locale_object,
    sha,
    sha_json,
    sha_record,
)

LEDGER_REL = "research/derived/review_ledger.json"
STAMP_KEY = "review_status"
RECORD_FIELD = "*"
# The two verdicts a teacher may record. Deliberately narrower than review_queue.py's tolerant
# APPROVING_STATUSES / REJECTING_STATUSES sets: those exist so the queue can read six historical
# ledger shapes it was tested against, while this is the shape we WRITE, and a writer with six
# spellings of "yes" is a writer nobody can audit. design/review_ledger.md owns this vocabulary.
STATUSES = ("approved", "rejected")
# Fields the queue offers as review targets that are not stored under that name on the record. The
# dissection is 50k+ localized strings reviewed as one artefact, per locale (review_queue.py).
VIRTUAL_FIELDS = ("dissection",)
HEX = frozenset("0123456789abcdefABCDEF")


def ledger_path(root: Path) -> Path:
    """Which ledger this process reads: `root/research/derived/review_ledger.json`, unless
    `--review-ledger PATH` or `$YOMINEKO_REVIEW_LEDGER` redirects it.

    The same rule scripts/dbtarget.py applies to the database, for the same reason: **the default
    never moves**, and the falsifiability proofs have to be able to point the exporter and the gate
    at a ledger that is not the committed one without editing the committed one. argv wins over the
    environment, because a human typing a path means it. `--review-ledger` is CONSUMED here, so a
    caller's own argparse never sees an argument it does not declare.
    """
    val = take_flag("--review-ledger")
    if val:
        return Path(val)
    env = os.environ.get("YOMINEKO_REVIEW_LEDGER")
    return Path(env) if env else root / LEDGER_REL


@dataclass
class Entry:
    index: int
    slug: str
    field: str
    locale: str | None
    content_hash: str
    status: str
    reviewed_by: str
    approved_at: str
    note: str | None = None
    entity: str | None = None

    @property
    def address(self) -> str:
        return f"{self.slug} - {self.field} [{self.locale or '*'}]"

    def stamp(self) -> dict[str, Any]:
        """What the exporter writes onto the record. The hash travels with the stamp so a reader can
        tell WHICH text was approved without going back to the ledger."""
        return {"field": self.field, "locale": self.locale, "status": self.status,
                "reviewed_by": self.reviewed_by, "approved_at": self.approved_at,
                "content_hash": self.content_hash}


@dataclass
class LedgerReport:
    path: str = LEDGER_REL
    present: bool = False
    entries: int = 0
    live: int = 0
    stale: int = 0
    stamped_records: int = 0
    errors: list[str] = dc_field(default_factory=list)
    stale_examples: list[str] = dc_field(default_factory=list)


def read_entries(path: Path) -> tuple[list[Entry], list[str]]:
    """Parse the ledger. Returns (entries, errors); a malformed entry is an ERROR, never a skip.

    A ledger that silently drops the entries it cannot parse reports fewer approvals than a teacher
    made, which is the one failure mode nobody would notice.
    """
    if not path.is_file():
        return [], [f'{path.as_posix()} is missing - the ledger file must exist; empty is fine '
                    f'({{"entries": []}})']
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [], [f"{LEDGER_REL} is not readable JSON: {exc}"]

    if isinstance(payload, dict):
        raw = payload.get("entries")
        if not isinstance(raw, list):
            return [], [f"{LEDGER_REL}: top-level object has no `entries` array"]
    elif isinstance(payload, list):
        raw = payload
    else:
        return [], [f"{LEDGER_REL}: top level is {type(payload).__name__}, expected an object with "
                    f"`entries` or a bare array"]

    errors: list[str] = []
    entries: list[Entry] = []
    for i, item in enumerate(raw):
        where = f"{LEDGER_REL}[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: entry is {type(item).__name__}, expected an object")
            continue
        slug = item.get("slug")
        if not isinstance(slug, str) or ":" not in slug:
            errors.append(f"{where}: `slug` {slug!r} is not a prefixed stable id")
            continue
        fld = item.get("field", RECORD_FIELD)
        if not isinstance(fld, str) or not fld:
            errors.append(f"{where}: `field` {fld!r} must be a non-empty string ('*' = whole record)")
            continue
        locale = item.get("locale")
        if locale is not None and not isinstance(locale, str):
            errors.append(f"{where}: `locale` {locale!r} must be a string or absent")
            continue
        chash = item.get("content_hash")
        tail = chash.rsplit(":", 1)[-1] if isinstance(chash, str) else ""
        if not isinstance(chash, str) or len(tail) < 8 or not set(tail) <= HEX:
            errors.append(f"{where}: `content_hash` {chash!r} must be at least 8 hex characters - an "
                          f"unanchored approval cannot tell 'the teacher read this text' from 'the "
                          f"teacher read whatever used to be here' (D4)")
            continue
        status = item.get("status")
        if status not in STATUSES:
            errors.append(f"{where}: `status` {status!r} is not one of {list(STATUSES)}")
            continue
        by = item.get("reviewed_by")
        if not isinstance(by, str) or not by.strip():
            errors.append(f"{where}: `reviewed_by` is required - an anonymous approval is not a review")
            continue
        at = item.get("approved_at")
        if not isinstance(at, str) or not at.strip():
            errors.append(f"{where}: `approved_at` is required")
            continue
        note = item.get("note")
        if note is not None and not isinstance(note, str):
            errors.append(f"{where}: `note` must be a string when present")
            continue
        entity = item.get("entity")
        if entity is not None and not isinstance(entity, str):
            errors.append(f"{where}: `entity` must be a string when present")
            continue
        entries.append(Entry(index=i, slug=slug, field=fld,
                             locale=None if locale in (None, "*") else locale,
                             content_hash=chash, status=status, reviewed_by=by, approved_at=at,
                             note=note, entity=entity))
    return entries, errors


def live_anchor(record: dict[str, Any], field: str, locale: str | None) -> tuple[str | None, str]:
    """The hash of what the record says TODAY at (field, locale), plus how it was computed.

    Returns (None, reason) when the address does not exist on this record - which is a ledger ERROR,
    not a stale approval: an approval of a field nobody can find is unauditable in both directions.
    """
    if field == RECORD_FIELD:
        return sha_record(record), "record"
    if field == "dissection":
        payload = dissection_payload(record, locale or "pt-BR")
        if not payload:
            return None, f"the record has no dissection in locale {locale or 'pt-BR'!r}"
        return sha_json(payload), "dissection"
    if field not in record:
        return None, f"the record has no field {field!r}"
    value = record[field]
    if locale is not None and is_locale_object(value):
        if locale not in value:
            return None, f"field {field!r} carries no locale {locale!r}"
        text = value[locale]
        return (sha(text) if isinstance(text, str) else sha_json(text)), "locale-object"
    if value in (None, [], {}, ""):
        return None, f"field {field!r} is empty"
    return sha_json(value), "aggregate"


class Ledger:
    """The ledger, indexed by slug, ready to stamp records as an exporter writes them."""

    def __init__(self, entries: Iterable[Entry], report: LedgerReport | None = None) -> None:
        self.by_slug: dict[str, list[Entry]] = {}
        for e in entries:
            self.by_slug.setdefault(e.slug, []).append(e)
        self.report = report or LedgerReport()

    @classmethod
    def load(cls, root: Path, strict: bool = True) -> "Ledger":
        path = ledger_path(root)
        entries, errors = read_entries(path)
        report = LedgerReport(path=path.as_posix(), present=path.is_file(),
                              entries=len(entries), errors=errors)
        if errors and strict:
            for err in errors:
                print(f"review_ledger: {err}", file=sys.stderr)
            raise SystemExit(f"review_ledger: {len(errors)} malformed entr(y/ies) in {LEDGER_REL} - "
                             f"refusing to export a stamp derived from a ledger that does not parse")
        return cls(entries, report)

    def __len__(self) -> int:
        return sum(len(v) for v in self.by_slug.values())

    def stamps_for(self, record: dict[str, Any]) -> list[dict[str, Any]]:
        """Every LIVE verdict covering this record, sorted. Stale and unresolvable entries return
        nothing at all - that is the whole point of anchoring."""
        slug = record.get("slug") if isinstance(record.get("slug"), str) else record.get("id")
        if not isinstance(slug, str):
            return []
        candidates = self.by_slug.get(slug)
        if not candidates:
            return []
        out: list[dict[str, Any]] = []
        for entry in candidates:
            anchor, _how = live_anchor(record, entry.field, entry.locale)
            if anchor is None:
                continue
            if not hashes_join(anchor, entry.content_hash):
                self.report.stale += 1
                if len(self.report.stale_examples) < 12:
                    self.report.stale_examples.append(
                        f"{entry.address} - approved `{entry.content_hash[:12]}`, live `{anchor[:12]}`")
                continue
            self.report.live += 1
            out.append(entry.stamp())
        out.sort(key=lambda s: (str(s["field"]), str(s["locale"] or ""), str(s["status"])))
        return out

    def apply(self, record: dict[str, Any]) -> dict[str, Any]:
        """Stamp the record in place (and return it). A record with no live verdict keeps NO key, so
        an empty ledger leaves the export byte-identical."""
        if not self.by_slug or not isinstance(record, dict):
            return record
        stamps = self.stamps_for(record)
        if stamps:
            record[STAMP_KEY] = stamps
            self.report.stamped_records += 1
        return record

    def apply_all(self, records: Any) -> Any:
        if not self.by_slug:
            return records
        if isinstance(records, list):
            for rec in records:
                if isinstance(rec, dict):
                    self.apply(rec)
        elif isinstance(records, dict):
            self.apply(records)
        return records


__all__ = ["APPROVING_STATUSES", "Entry", "LEDGER_REL", "Ledger", "LedgerReport", "RECORD_FIELD",
           "REJECTING_STATUSES", "STAMP_KEY", "STATUSES", "VIRTUAL_FIELDS", "hashes_join",
           "ledger_path", "live_anchor", "read_entries", "sha", "sha_json", "sha_record"]
