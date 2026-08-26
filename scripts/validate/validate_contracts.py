#!/usr/bin/env python3
"""Hard gate: every exported record conforms to its entity's schema, and every ID resolves.

Three checks, in the order a defect matters:

  1. SHAPE   — each record validates against contracts/<entity>.schema.json. Catches a field that
               changed type, an enum that grew a value nobody declared, a required field that went
               missing. This is the check that would have caught `needs_review` being 1 on four
               entities and true on five.
  2. IDENTITY— the stable ID of every record is unique within its entity and carries a declared
               namespace. Two records answering to one address make an API route ambiguous, and
               "everything is addressed by stable ID" (spec §1.7) stops being true.
  3. GRAPH   — every cross-reference resolves to a record that exists. The courseware references the
               corpus by ID and never embeds it, so a dangling reference is a lesson that renders
               empty rather than a lesson that errors.

Exit 0 only when all three pass. Advisory notes print but do not fail.
Usage: validate_contracts.py [--entity NAME] [--verbose]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"

try:
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
except ImportError:
    print("missing dependency: pip install -r requirements.txt", file=sys.stderr)
    raise

MAX_REPORT = 12          # per entity; the rest are counted, not printed
ID_PATTERN = re.compile(r"^([a-z][a-z0-9_]*):")


def load_registry() -> Registry:
    """Make common.schema.json resolvable by its relative filename, the way the schemas $ref it."""
    reg = Registry()
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        res = Resource.from_contents(doc)
        reg = reg.with_resource(uri=path.name, resource=res)
        if "$id" in doc:
            reg = reg.with_resource(uri=doc["$id"], resource=res)
    return reg


def records_of(path: Path, packing: str):
    """Yield (locator, record) pairs. The locator names the record in an error message."""
    data = json.loads(path.read_text(encoding="utf-8"))
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if packing == "single":
        yield rel, data
    elif packing == "map":
        yield rel, data                       # the map as a whole is the validated unit
    else:
        for i, rec in enumerate(data):
            key = rec.get("slug") or rec.get("id") or f"#{i}" if isinstance(rec, dict) else f"#{i}"
            yield f"{rel}[{key}]", rec


def scan(node: object, declared: list[str], refs: list[str], under_id: bool = False) -> None:
    """Split the ID-shaped strings in a record into the ones it DECLARES and the ones it POINTS AT.

    A value sitting under an `id` or `slug` key is that object announcing its own address — including
    nested objects, because a course's stages and a lesson's exercises are addressable records too and
    the rest of the corpus links straight to them. Everything else that looks like an ID is an edge,
    and an edge has to land somewhere.
    """
    if isinstance(node, str):
        if ID_PATTERN.match(node) and len(node) > 3:
            (declared if under_id else refs).append(node)
    elif isinstance(node, list):
        for x in node:
            scan(x, declared, refs, under_id)
    elif isinstance(node, dict):
        for k, v in node.items():
            scan(v, declared, refs, k in ("id", "slug"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    registry = load_registry()
    schemas = sorted(p for p in CONTRACTS.glob("*.schema.json") if p.name != "common.schema.json")
    if not schemas:
        print("no contracts found — run scripts/contracts/build_schemas.py", file=sys.stderr)
        return 2

    fails: list[str] = []
    notes: list[str] = []
    known_ids: dict[str, str] = {}            # stable id -> entity that owns it
    all_refs: list[tuple[str, str, str]] = []  # (entity, locator, referenced id)
    total_records = 0
    summary: list[tuple[str, int, int, int]] = []

    for spath in schemas:
        doc = json.loads(spath.read_text(encoding="utf-8"))
        meta = doc.get("x-yomineko", {})
        entity = meta.get("entity", spath.stem.replace(".schema", ""))
        if args.entity and entity != args.entity:
            continue
        glob, packing = meta.get("glob"), meta.get("packing", "list")
        if not glob:
            notes.append(f"{entity}: schema declares no glob; nothing validated")
            continue

        validator = Draft202012Validator(doc, registry=registry)
        id_field = meta.get("stable_id_field")
        n_rec = n_bad = n_dup = 0
        shown = 0
        seen: dict[str, str] = {}

        for path in sorted(ROOT.glob(glob)):
            for locator, rec in records_of(path, packing):
                n_rec += 1
                errs = sorted(validator.iter_errors(rec), key=lambda e: list(e.path))
                if errs:
                    n_bad += 1
                    for e in errs[:2]:
                        if shown < MAX_REPORT:
                            where = ".".join(str(p) for p in e.path) or "(root)"
                            fails.append(f"{entity}: {locator}: {where}: {e.message[:160]}")
                            shown += 1
                declared: list[str] = []
                refs: list[str] = []
                scan(rec, declared, refs)
                if packing == "map":
                    for k in rec:                      # in a map the KEY is the address
                        known_ids.setdefault(k, entity)
                for d in declared:
                    known_ids.setdefault(d, entity)
                all_refs += [(entity, locator, r) for r in refs]

                # Uniqueness is only meaningful for the record's OWN primary key.
                if packing != "map" and id_field and isinstance(rec, dict):
                    sid = rec.get(id_field)
                    if isinstance(sid, str):
                        if sid in seen:
                            n_dup += 1
                            if shown < MAX_REPORT:
                                fails.append(
                                    f"{entity}: duplicate stable id {sid!r} — {locator} and {seen[sid]}")
                                shown += 1
                        seen[sid] = locator

        total_records += n_rec
        summary.append((entity, n_rec, n_bad, n_dup))
        if (n_bad or n_dup) and shown >= MAX_REPORT:
            fails.append(f"{entity}: ...{n_bad} invalid + {n_dup} duplicate-id record(s) in total")

    # ---- aliases: the second, legitimate way to address a vocab record -------------------------
    # The courseware writes `vocab:<headword>` (vocab:人) while corpus/vocab writes
    # `vocab:<jmdict_id>` (vocab:1580640). Both are real and in use — 678,700 references take the
    # first form and 584 the second — so the graph check has to accept both or it reports the entire
    # course layer as broken. It is still worth knowing about: a headword is NOT a unique address,
    # and the ambiguous ones are reported separately below.
    alias: dict[str, list[str]] = {}
    for path in sorted(ROOT.glob("corpus/vocab/*.json")):
        for r in json.loads(path.read_text(encoding="utf-8")):
            alias.setdefault(f"vocab:{r['headword']}", []).append(r["slug"])
    for a in alias:
        known_ids.setdefault(a, "vocab")

    # ---- graph: do the references resolve? -----------------------------------------------------
    # Only namespaces we actually own are checked. A `tatoeba:` or `deck:` string is a foreign
    # citation, not an internal edge, and demanding it resolve would be a false failure.
    owned = {ID_PATTERN.match(i).group(1) for i in known_ids if ID_PATTERN.match(i)}
    dangling: Counter = Counter()
    examples: dict[str, tuple[str, str]] = {}
    for entity, locator, rid in all_refs:
        m = ID_PATTERN.match(rid)
        if not m or m.group(1) not in owned:
            continue
        if rid not in known_ids:
            dangling[rid] += 1
            examples.setdefault(rid, (entity, locator))

    print("================ CONTRACT GATE ================")
    for entity, n, bad, dup in summary:
        mark = "OK " if not (bad or dup) else "FAIL"
        detail = "".join([f", {bad} invalid" if bad else "",
                          f", {dup} duplicate id" if dup else ""])
        print(f"  [{mark}] {entity:22} {n:>6} records{detail}")
    print(f"  ---- {total_records} records, {len(known_ids)} distinct stable ids, "
          f"{len(all_refs)} references")

    if fails:
        print("\nSHAPE / IDENTITY failures:")
        for f in fails:
            print(f"  ! {f}")

    if dangling:
        print(f"\nGRAPH: {len(dangling)} unresolved reference(s) "
              f"({sum(dangling.values())} occurrences):")
        for rid, n in dangling.most_common(MAX_REPORT):
            ent, loc = examples[rid]
            print(f"  ! {rid}  x{n}  e.g. {loc}")

    # A headword shared by two vocab records cannot be resolved to one of them. This is not a broken
    # reference — it resolves — but which record it resolves to depends on the consumer's index order,
    # so an N5 lesson can end up showing an N1 gloss. Advisory: fixing it means re-keying the course
    # layer onto slugs, which is a migration, not a validation.
    ambiguous = {a: v for a, v in alias.items() if len(v) > 1}
    used = Counter()
    for _, _, rid in all_refs:
        if rid in ambiguous:
            used[rid] += 1
    if used:
        print()
        print(f"  [info] {len(used)} ambiguous headword address(es) in use "
              f"({sum(used.values())} references): a `vocab:<headword>` that matches more than one "
              f"record resolves by luck of index order.")
        for rid, n in used.most_common(6):
            print(f"  [info]   {rid} -> {', '.join(ambiguous[rid])}  ({n} refs)")

    for n in notes:
        print(f"  [info] {n}")

    ok = not fails and not dangling
    print("\n" + ("RESULT: ALL CONTRACTS PASS" if ok else "RESULT: CONTRACT VIOLATIONS ABOVE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
