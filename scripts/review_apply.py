#!/usr/bin/env python3
"""W38 — the flow-back: a teacher's review sheet becomes ledger entries and a tracked repair table.

APP_PLAN readiness finding **G12**: *"no path from an approval or a teacher edit into the committed
JSON"*. W06 built the ledger and W38's first half built the views; this is the hinge between them.
A named teacher (D4) reads `research/review/<registry>/<level>.md`, writes a small sheet, and runs:

    python scripts/review_apply.py --sheet research/review/sheets/n5-vocab-01.json

WHAT THE SHEET LOOKS LIKE
-------------------------
JSON (or YAML, when PyYAML is installed — same keys, same rules):

    {
      "schema_version": "1.0",
      "sheet_id": "n5-vocab-01",
      "reviewed_by": "teacher:ana",
      "reviewed_at": "2026-09-09",
      "records": [
        {"id": "gram:da-desu",
         "record_hash": "e0f3c35765c5",
         "approve": ["explanation@pt-BR", "label@pt-BR"],
         "edit":    {"formation@pt-BR": "Substantivo + です／だ …"},
         "reject":  {"nuance@pt-BR": "confunde だ com である; reescrever"},
         "note":    "opcional, fica no ledger"}
      ]
    }

`record_hash` is the hash the view printed beside `### \\`*\\``, and it is the **staleness anchor of
the whole sheet**. An address is `field` or `field@locale`, copied from the view's own headings.
A field may appear in exactly one of `approve` / `edit` / `reject`.

THE FIVE THINGS THIS SCRIPT DOES, AND THE ONE IT REFUSES TO DO
-------------------------------------------------------------
(a) **Refuses a stale sheet, whole.** If any record's `record_hash` no longer joins the live record,
    the sheet is rejected and NOTHING is written — not the good records either. A campaign rewrote
    the corpus under the teacher, so every verdict on that sheet was formed against text that may
    no longer be there; partial acceptance would silently convert "I read this" into "I read an
    earlier version of some of this". The teacher regenerates the view and re-reads.
(b) **Approvals and rejections become ledger entries**, anchored by `review_ledger.live_anchor` —
    the same function the exporter's stamp and `validate_review_ledger.py` call, so an entry written
    here is live by construction and can never be *unresolvable* (the ledger's one hard failure).
    Idempotent: re-running the same sheet adds nothing.
(c) **Edits become an exact-match tracked repair table** under
    `research/derived/pending/<sheet_id>.json`, in the `{entity, slug, field, locale, old,
    new, why}` shape every applier in this repo already reads (`apply_sentence_text_repairs.py`
    consumes it verbatim). It is **NOT applied**: applying is a DB-writer step, and this script
    never opens `db/corpus.sqlite`. The apply command is printed instead.
    It lands in `research/derived/pending/` rather than `research/derived/repairs/` on purpose:
    `validate_repairs_applied.py` FAILS on any unregistered `*.json` directly under `repairs/`, and
    it asserts every row's `new` is already in the export. An unapplied table in that directory
    would break the suite the moment it was written. `pending/` is where this project already keeps
    authored-but-unapplied tables (STATE aj: "pending (not-yet-applied) tables live in
    research/derived/pending/, never in repairs/ — the replay gate owns repairs/"), and W38's own
    report named the original `repairs/pending/` as the thing to fix. Promoting a table — move the
    file into `repairs/` and register it in `validate_repairs_applied.py` — is the last step of the
    apply, not the first step of the review.
(d) **It never writes prose.** Every `new`, every `why`, every `note` comes from the sheet. The
    script writes structure, hashes and provenance; the words are the teacher's.
(e) Unknown id, unresolvable address, a field claimed twice, an edit on a non-string field, a
    missing `reviewed_by` — each refuses the sheet with the reason. A verdict this script cannot
    address exactly is a verdict it will not guess at.

ALSO
    --template REGISTRY LEVEL   writes a pre-addressed blank sheet (ids + record hashes + the list
                                of addresses each record offers) so nothing is hand-copied.
    --check                     parse, validate and report; write nothing.

Reads:  corpus/**, course/**, contracts/manifest.json, the ledger.
Writes: the ledger, and research/derived/pending/<sheet_id>.json. NEVER the database,
        never an exporter output.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "export"))

from dbtarget import take_flag  # noqa: E402
from review_ledger import (  # noqa: E402
    hashes_join, ledger_path, live_anchor, read_entries,
)
import build_review_views as views  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PENDING_REL = "research/derived/pending"
SHEETS_REL = "research/review/sheets"
SHEET_SCHEMA_VERSION = "1.0"
VERDICT_KEYS = ("approve", "edit", "reject")


class SheetError(Exception):
    """A refusal. Every message names the record and says what the teacher should do next."""


# ==================================================================================================
# the export, indexed by published address
# ==================================================================================================
def index_export(root: Path) -> dict[str, tuple[str, dict[str, Any], str]]:
    """address -> (entity, record, registry name). Built from the same registry table the views use,
    so a sheet can only ever address something a view could have shown."""
    index: dict[str, tuple[str, dict[str, Any], str]] = {}
    for registry in views.REGISTRIES:
        for rec in registry.records(root):
            addr = views.address_of(rec)
            if addr:
                index.setdefault(addr, (registry.entity, rec, registry.name))
    return index


def split_address(raw: str) -> tuple[str, str | None]:
    """`explanation@pt-BR` -> ('explanation', 'pt-BR'); `senses` -> ('senses', None)."""
    text = str(raw).strip()
    if "@" in text:
        field, locale = text.split("@", 1)
        field, locale = field.strip(), locale.strip()
        return field, (None if locale in ("", "*") else locale)
    return text, None


def current_text(rec: dict[str, Any], field: str, locale: str | None) -> str | None:
    """The exact string an edit would replace, or None when the address is not a plain string.

    An `edit` may only target a string. `senses`, `readings` and `forms` are aggregates whose anchor
    is canonical JSON: a teacher retyping one in a sheet would be authoring a data structure, and
    the first typo would be indistinguishable from a decision. Those are `reject` + a reason, which
    is what routes them to a campaign that can rebuild them properly.
    """
    if field == "*" or field == "dissection":
        return None
    value = rec.get(field)
    if locale is not None and views.is_locale_object(value):
        text = value.get(locale)
        return text if isinstance(text, str) else None
    return value if isinstance(value, str) else None


# ==================================================================================================
# reading a sheet
# ==================================================================================================
def load_sheet(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise SheetError(f"{path.name} is YAML but PyYAML is not installed ({exc}). "
                             f"Save the sheet as .json instead — the keys are identical.") from exc
        payload = yaml.safe_load(text)
    else:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SheetError(f"{path.name} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SheetError(f"{path.name}: the top level must be an object with `records`")
    return payload


class Verdict:
    def __init__(self, slug: str, entity: str, field: str, locale: str | None, kind: str,
                 anchor: str, payload: str, note: str) -> None:
        self.slug = slug
        self.entity = entity
        self.field = field
        self.locale = locale
        self.kind = kind          # approve | reject | edit
        self.anchor = anchor
        self.payload = payload    # the new text (edit) or the reason (reject)
        self.note = note

    @property
    def address(self) -> str:
        return f"{self.slug} · {self.field}" + (f"@{self.locale}" if self.locale else "")


def parse_sheet(payload: dict[str, Any], index: dict[str, tuple[str, dict[str, Any], str]],
                sheet_name: str) -> tuple[dict[str, Any], list[Verdict], list[str]]:
    """Every refusal reason is collected before any is raised: a teacher fixing a sheet should see
    all of its problems once, not one per run."""
    problems: list[str] = []
    meta = {
        "sheet_id": str(payload.get("sheet_id") or sheet_name),
        "reviewed_by": payload.get("reviewed_by"),
        "reviewed_at": payload.get("reviewed_at"),
        "registry": payload.get("registry"),
        "level": payload.get("level"),
    }
    if not isinstance(meta["reviewed_by"], str) or not meta["reviewed_by"].strip():
        problems.append("`reviewed_by` is required — an anonymous approval is not a review (D4)")
    if not isinstance(meta["reviewed_at"], str) or not meta["reviewed_at"].strip():
        problems.append("`reviewed_at` is required (YYYY-MM-DD): it is the provenance of the verdict")

    records = payload.get("records")
    if not isinstance(records, list) or not records:
        problems.append("`records` must be a non-empty array")
        return meta, [], problems

    verdicts: list[Verdict] = []
    for i, row in enumerate(records):
        where = f"records[{i}]"
        if not isinstance(row, dict):
            problems.append(f"{where}: expected an object")
            continue
        slug = row.get("id")
        if not isinstance(slug, str) or ":" not in slug:
            problems.append(f"{where}: `id` {slug!r} is not a published stable id")
            continue
        found = index.get(slug)
        if found is None:
            problems.append(f"{where} ({slug}): no record in the export has this address. "
                            f"Check the id against the view, or the record was renamed.")
            continue
        entity, rec, _registry = found

        claimed = row.get("record_hash")
        record_anchor, _how = live_anchor(rec, "*", None)
        if not isinstance(claimed, str) or not claimed.strip():
            problems.append(f"{where} ({slug}): `record_hash` is required — it is what proves the "
                            f"record has not changed since the view was generated")
            continue
        if not record_anchor or not hashes_join(record_anchor, claimed):
            problems.append(
                f"{where} ({slug}): STALE — the sheet was written against `{claimed[:12]}`, the "
                f"record now hashes `{(record_anchor or '')[:12]}`. Something rewrote it after the "
                f"view was generated. Regenerate the view and read it again; nothing on this sheet "
                f"was recorded.")
            continue

        note = row.get("note") if isinstance(row.get("note"), str) else ""
        seen: dict[tuple[str, str | None], str] = {}
        unknown = [k for k in row if k not in ("id", "record_hash", "note", *VERDICT_KEYS)]
        if unknown:
            problems.append(f"{where} ({slug}): unknown key(s) {sorted(unknown)}")

        for kind in VERDICT_KEYS:
            block = row.get(kind)
            if block in (None, [], {}):
                continue
            if kind == "approve":
                if not isinstance(block, list):
                    problems.append(f"{where} ({slug}): `approve` must be a list of addresses")
                    continue
                items: list[tuple[str, str]] = [(str(a), "") for a in block]
            else:
                if not isinstance(block, dict):
                    problems.append(f"{where} ({slug}): `{kind}` must be an object "
                                    f"{{address: {'texto novo' if kind == 'edit' else 'motivo'}}}")
                    continue
                items = [(str(a), str(v)) for a, v in block.items()]

            for raw_addr, value in items:
                field, locale = split_address(raw_addr)
                key = (field, locale)
                if key in seen:
                    problems.append(f"{where} ({slug}): address `{raw_addr}` appears in both "
                                    f"`{seen[key]}` and `{kind}` — one verdict per address")
                    continue
                seen[key] = kind
                anchor, how = live_anchor(rec, field, locale)
                if anchor is None:
                    problems.append(f"{where} ({slug}): address `{raw_addr}` — {how}. Copy the "
                                    f"heading from the view exactly; only the addresses it prints "
                                    f"can be recorded.")
                    continue
                if kind == "edit":
                    old = current_text(rec, field, locale)
                    if old is None:
                        problems.append(
                            f"{where} ({slug}): `{raw_addr}` is not a plain text field, so it "
                            f"cannot be edited from a sheet. Use `reject` with a reason and let a "
                            f"campaign rebuild it.")
                        continue
                    if not isinstance(value, str) or not value.strip():
                        problems.append(f"{where} ({slug}): the edit for `{raw_addr}` is empty")
                        continue
                    if value == old:
                        problems.append(f"{where} ({slug}): the edit for `{raw_addr}` is identical "
                                        f"to the current text")
                        continue
                elif kind == "reject" and (not isinstance(value, str) or not value.strip()):
                    problems.append(f"{where} ({slug}): `reject` for `{raw_addr}` needs a reason")
                    continue
                verdicts.append(Verdict(slug, entity, field, locale, kind, anchor, value, note))

    return meta, verdicts, problems


# ==================================================================================================
# writing the two outputs
# ==================================================================================================
def ledger_entry(v: Verdict, meta: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "slug": v.slug,
        "entity": v.entity,
        "field": v.field,
        "content_hash": v.anchor,
        "status": "approved" if v.kind == "approve" else "rejected",
        "reviewed_by": str(meta["reviewed_by"]),
        "approved_at": str(meta["reviewed_at"]),
    }
    if v.locale:
        entry["locale"] = v.locale
    note = v.payload if v.kind == "reject" else v.note
    if note:
        entry["note"] = note
    return entry


def entry_identity(entry: dict[str, Any]) -> tuple:
    return (entry.get("slug"), entry.get("field"), entry.get("locale"), entry.get("status"),
            entry.get("content_hash"), entry.get("reviewed_by"))


def write_ledger(path: Path, new_entries: list[dict[str, Any]]) -> tuple[int, int]:
    """Append, never rewrite. Returns (added, already_present)."""
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            payload = {"entries": payload}
    else:
        payload = {"schema_version": "1.0", "entries": []}
    existing = payload.get("entries")
    if not isinstance(existing, list):
        raise SheetError(f"{path.as_posix()}: top-level object has no `entries` array")

    known = {entry_identity(e) for e in existing if isinstance(e, dict)}
    added = 0
    already = 0
    for entry in new_entries:
        if entry_identity(entry) in known:
            already += 1
            continue
        existing.append(entry)
        known.add(entry_identity(entry))
        added += 1
    payload["entries"] = existing
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    return added, already


def repair_rows(edits: list[Verdict], rec_of: dict[str, dict[str, Any]],
                meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for v in sorted(edits, key=lambda e: (e.slug, e.field, e.locale or "")):
        old = current_text(rec_of[v.slug], v.field, v.locale)
        rows.append({
            "entity": v.entity,
            "slug": v.slug,
            "field": v.field,
            "locale": v.locale,
            "old": old,
            "new": v.payload,
            "why": v.note or f"teacher edit recorded on review sheet {meta['sheet_id']}",
            "reviewed_by": str(meta["reviewed_by"]),
            "reviewed_at": str(meta["reviewed_at"]),
            "source_sheet": meta["sheet_id"],
            "old_hash": v.anchor,
        })
    return rows


def apply_hint(rows: list[dict[str, Any]], table: Path) -> list[str]:
    """What to run next. Named exactly, or honestly not named at all."""
    reach = {("sentence", "structure_explanation"), ("sentence", "translation_literal")}
    inside = [r for r in rows if (r["entity"], r["field"]) in reach]
    outside = sorted({f"{r['entity']}.{r['field']}" for r in rows
                      if (r["entity"], r["field"]) not in reach})
    out = ["", "Nada foi aplicado: escrever no banco é outro passo, e este script não abre o banco.",
           f"Tabela de edições: {table.as_posix()} ({len(rows)} linha(s))", "", "Para aplicar:"]
    if inside:
        out += [f"  python scripts/apply_sentence_text_repairs.py --data {table.as_posix()} --check",
                f"  python scripts/apply_sentence_text_repairs.py --data {table.as_posix()}",
                "  python scripts/export/export_corpus.py"]
    if outside:
        out += [f"  # {len(rows) - len(inside)} linha(s) fora do alcance daquele applier "
                f"({', '.join(outside)}):",
                "  # escreva o applier desta tabela seguindo scripts/apply_sentence_text_repairs.py"]
    out += ["",
            "Depois de aplicar e exportar: mova a tabela para research/derived/repairs/ e registre-a",
            "em scripts/validate/validate_repairs_applied.py (REGISTRY) — o gate exige as duas coisas."]
    return out


# ==================================================================================================
# --template
# ==================================================================================================
def build_template(root: Path, registry_name: str, level: str, limit: int,
                   only_flagged: bool) -> dict[str, Any]:
    registry = views.REGISTRY_BY_NAME.get(registry_name)
    if registry is None:
        raise SheetError(f"unknown registry {registry_name!r} "
                         f"({', '.join(r.name for r in views.REGISTRIES)})")
    order = views.build_course_order(root)
    records = [rec for rec in registry.records(root)
               if level in views.levels_of(registry, rec, order)
               and (not only_flagged or views.needs_review_of(rec))]
    records.sort(key=lambda r: views.sort_key(registry, r, order))
    if limit:
        records = records[:limit]

    rows: list[dict[str, Any]] = []
    for rec in records:
        anchor, _how = live_anchor(rec, "*", None)
        # `*` stays last: approving the whole record in one line is the throughput case M6 needs,
        # and it must not be the first thing the eye lands on.
        addresses = [f"{f}@{lc}" if lc else f
                     for f, lc, _a, _v in views.targets_of(registry, rec)]
        rows.append({
            "id": views.address_of(rec),
            "record_hash": (anchor or "")[:16],
            "_addresses": addresses,
            "approve": [],
            "edit": {},
            "reject": {},
        })
    return {
        "schema_version": SHEET_SCHEMA_VERSION,
        "sheet_id": f"{level}-{registry_name}",
        "registry": registry_name,
        "level": level,
        "reviewed_by": "",
        "reviewed_at": "",
        "_leia": (f"Ficha de revisão gerada de research/review/{registry_name}/{level}.md. "
                  f"Preencha `reviewed_by` e `reviewed_at`, e em cada registro use `approve` "
                  f"(lista de endereços), `edit` (endereço → texto novo) ou `reject` "
                  f"(endereço → motivo). `_addresses` é só a lista do que dá para avaliar; "
                  f"apague o que não usar. Instruções: research/review/README.md"),
        "records": rows,
    }


# ==================================================================================================
# main
# ==================================================================================================
def run_sheet(root: Path, sheet_path: Path, ledger_file: Path, check: bool) -> int:
    payload = load_sheet(sheet_path)
    index = index_export(root)
    meta, verdicts, problems = parse_sheet(payload, index, sheet_path.stem)

    if problems:
        print(f"RECUSADA: {sheet_path.as_posix()} — {len(problems)} problema(s). "
              f"Nada foi gravado.\n")
        for line in problems:
            print(f"  - {line}")
        return 2

    approvals = [v for v in verdicts if v.kind in ("approve", "reject")]
    edits = [v for v in verdicts if v.kind == "edit"]
    rec_of = {v.slug: index[v.slug][1] for v in verdicts}

    entries = [ledger_entry(v, meta) for v in
               sorted(approvals, key=lambda e: (e.slug, e.field, e.locale or "", e.kind))]
    rows = repair_rows(edits, rec_of, meta)
    table = root / PENDING_REL / f"{meta['sheet_id']}.json"

    n_ok = sum(1 for v in approvals if v.kind == "approve")
    n_no = len(approvals) - n_ok
    print(f"ficha {meta['sheet_id']} · {meta['reviewed_by']} · {meta['reviewed_at']}")
    print(f"  {len(payload.get('records') or [])} registro(s) lido(s) · "
          f"{n_ok} aprovação(ões) · {n_no} rejeição(ões) · {len(rows)} edição(ões)")

    if check:
        print("  --check: nada gravado")
        for v in verdicts:
            print(f"    [{v.kind}] {v.address}  hash {v.anchor[:12]}")
        return 0

    added, already = (0, 0)
    if entries:
        added, already = write_ledger(ledger_file, entries)
        print(f"  ledger {ledger_file.as_posix()}: +{added} entrada(s), "
              f"{already} já existia(m)")
        reparsed, errors = read_entries(ledger_file)
        if errors:
            for err in errors:
                print(f"  ledger NÃO analisa: {err}", file=sys.stderr)
            return 3
        print(f"  ledger reanalisado: {len(reparsed)} entrada(s) válida(s)")
    else:
        print("  nenhuma aprovação/rejeição nesta ficha; ledger intocado")

    if rows:
        table.parent.mkdir(parents=True, exist_ok=True)
        table.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8", newline="\n")
        for line in apply_hint(rows, table):
            print(line)
    else:
        print("  nenhuma edição nesta ficha; nenhuma tabela escrita")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ledger_override = take_flag("--review-ledger") or os.environ.get("YOMINEKO_REVIEW_LEDGER")
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--sheet", type=Path, default=None, help="the filled review sheet")
    parser.add_argument("--check", action="store_true", help="validate and report; write nothing")
    parser.add_argument("--template", nargs=2, metavar=("REGISTRY", "LEVEL"), default=None,
                        help="write a blank pre-addressed sheet instead of applying one")
    parser.add_argument("--out", type=Path, default=None, help="where --template writes")
    parser.add_argument("--limit", type=int, default=0, help="--template: first N records only")
    parser.add_argument("--only-flagged", action="store_true",
                        help="--template: only records the export marks needs_review")
    args = parser.parse_args(argv)

    root: Path = args.root
    ledger_file = Path(ledger_override) if ledger_override else ledger_path(root)

    try:
        if args.template:
            registry_name, level = args.template
            sheet = build_template(root, registry_name, level, args.limit, args.only_flagged)
            out = args.out or (root / SHEETS_REL / f"{sheet['sheet_id']}.json")
            if args.check:
                print(json.dumps(sheet, ensure_ascii=False, indent=2))
                return 0
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
            print(f"ficha em branco: {out.as_posix()} ({len(sheet['records'])} registro(s))")
            return 0
        if not args.sheet:
            parser.error("give --sheet PATH, or --template REGISTRY LEVEL")
        if not args.sheet.is_file():
            print(f"ficha não encontrada: {args.sheet.as_posix()}", file=sys.stderr)
            return 2
        return run_sheet(root, args.sheet, ledger_file, args.check)
    except SheetError as exc:
        print(f"RECUSADA: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
