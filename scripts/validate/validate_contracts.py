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

Plus one structural check: an entity whose glob matches nothing is a FAILURE, not a quiet `0 records`.
A stopped exporter and a moved directory both look like a passing gate otherwise.

ENTITY CLASSES, AND THE ONE ENTITY THAT IS ALLOWED TO HAVE NO DATA
------------------------------------------------------------------
`content` entities are committed JSON under corpus/ or course/ and the paragraph above governs them.
`runtime` entities (contracts/user_state/, specified by design/user_state.md) are the user-state
contracts: `card`, `review_log`, `lesson_progress`, `exam_attempt`, `feature_state`, `skill_state`,
`user`. They have a contract and no committed records — a card row exists only once a learner has one
— so zero records is CORRECT and must not fail.

The exemption is keyed on the DECLARED class in x-yomineko plus the absence of a glob, never on the
absence of a glob alone, and it is checked in both directions:

  * a `runtime` entity that also declares a glob falls through into the content path and fails on its
    0 matches, so a content entity whose exporter stopped cannot relabel itself `runtime` and go quiet;
  * a `content` entity with no glob now FAILS, where it used to print an advisory note and pass;
  * a `runtime` entity is still checked — its schema must compile as Draft 2020-12 and every `$ref` in
    it must resolve — because a contract nobody can validate against records is exactly the kind that
    rots unnoticed.

WHAT DECLARES AN ADDRESS, AND WHAT POINTS AT ONE
------------------------------------------------
This used to be decided by the key name: any id-shaped string under a key called `id` or `slug` was
read as the record announcing its own address. That silently swallowed 20,570 foreign keys — a drill's
`slug` naming the vocab it drills, a checkpoint's `id` naming an exam item, a topic's `lessons[].id`
naming a lesson leaf — and, worse, a BROKEN one minted itself as a new address instead of being
reported as dangling. The rule is now structural:

  * the record root's `stable_id_field` (from the schema's x-yomineko block) declares;
  * a map file's KEYS declare;
  * plus the handful of nested paths in DECLARATIONS below, which genuinely own an address that exists
    nowhere else (a lesson's own exercises, the speaking path's stages, the kana chart's groups);
  * everything else that is id-shaped is an EDGE and has to land somewhere.

Exit 0 only when all of it passes. Advisory notes print but do not fail.
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

# Nested paths that genuinely DECLARE an address — the record they name exists in no other file, so
# there is nothing for the graph check to resolve them against. Paths are dotted, `[]` descends into an
# array element, and `*` is a map key. Anything not listed here is a reference.
DECLARATIONS: dict[str, set[str]] = {
    # A lesson's exercises live inside the lesson; `<exercise ref="ex:…">` in the body points back here.
    "lesson": {"exercises[].id"},
    # The speaking path declares its own stages; speak_unit.stage points at one.
    "speak_path": {"stages[].slug"},
    # Group ids (kana:hiragana-a) exist only in the chart. Member ids do NOT — every one of them is a
    # record in corpus/kana/, so members[].id stays a reference and gets resolved.
    "kana_family": {"*[].id"},
}

# An entity whose stable_id_field is really a FOREIGN key. A conjugation table is addressed by the vocab
# entry it inflects, so `vocab:1000730` is one address answered by two records. Registering it here as a
# declaration would hide that; treating it as an edge both resolves it and keeps the ambiguity visible
# (see contracts/common.schema.json → StableId). Uniqueness is still checked: one paradigm per word.
ROOT_ID_IS_FOREIGN = {"conjugation": "slug"}


def collect_refs(node: object, acc: set[str] | None = None) -> set[str]:
    """Every `$ref` string anywhere in a schema document."""
    acc = set() if acc is None else acc
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            acc.add(ref)
        for v in node.values():
            collect_refs(v, acc)
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, acc)
    return acc


def all_schemas() -> list[Path]:
    """Every entity contract: the content ones flat in contracts/, the runtime ones one level down in
    contracts/user_state/. Sorted by relative POSIX path so the report order is stable everywhere."""
    found = [*CONTRACTS.glob("*.schema.json"), *CONTRACTS.glob("*/*.schema.json")]
    return sorted(found, key=lambda p: p.relative_to(CONTRACTS).as_posix())


def load_registry() -> Registry:
    """Make common.schema.json resolvable by its relative filename, the way the schemas $ref it.

    The runtime contracts sit a directory down and $ref `../common.schema.json`; that resolves against
    their own `$id` to the same absolute URI common.schema.json declares, so registering every document
    under its `$id` is what makes the subdirectory work at all."""
    reg = Registry()
    for path in all_schemas():
        doc = json.loads(path.read_text(encoding="utf-8"))
        res = Resource.from_contents(doc)
        reg = reg.with_resource(uri=path.name, resource=res)
        reg = reg.with_resource(uri=path.relative_to(CONTRACTS).as_posix(), resource=res)
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


def scan(node: object, path: str, decl_paths: set[str], root_id: str | None,
         declared: list[str], refs: list[str]) -> None:
    """Split the ID-shaped strings in a record into the ones it DECLARES and the ones it POINTS AT.

    `path` is the position inside the record: `""` at the root, `checkpoint[].id` for a checkpoint's id,
    `*[].members[].id` inside a map file. A string declares only when its path is the entity's own
    stable_id_field at the root, or one of the explicitly declarable nested paths (see DECLARATIONS).
    Everything else that looks like an ID is an edge, and an edge has to land somewhere.
    """
    if isinstance(node, str):
        if ID_PATTERN.match(node) and len(node) > 3:
            is_decl = (path and path == root_id) or path in decl_paths
            (declared if is_decl else refs).append(node)
    elif isinstance(node, list):
        for x in node:
            scan(x, path + "[]", decl_paths, root_id, declared, refs)
    elif isinstance(node, dict):
        for k, v in node.items():
            child = k if not path else f"{path}.{k}"
            scan(v, child, decl_paths, root_id, declared, refs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    registry = load_registry()
    schemas = [p for p in all_schemas() if p.name != "common.schema.json"]
    if not schemas:
        print("no contracts found — run scripts/contracts/build_schemas.py", file=sys.stderr)
        return 2

    fails: list[str] = []
    notes: list[str] = []
    runtime: list[str] = []
    # Entities whose FAILURE is structural rather than per-record: nothing validated, a class that
    # contradicts its glob, a contract that does not compile. Without this the summary table printed
    # [OK ] beside an entity the gate had just failed, because its per-record counters were zero.
    structural: set[str] = set()
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
        cls = meta.get("class", "content")

        # ---- the runtime class ------------------------------------------------------------------
        # A runtime entity (design/user_state.md §12) has a contract and NO committed records: a card
        # row exists only once a learner has one. Zero records is CORRECT for it, so the zero-record
        # failure below must not fire — but the exemption is keyed on the DECLARED class *and* the
        # absence of a glob, never on the absence of a glob alone. A runtime entity that declares a
        # glob falls straight through into the content path, where its 0 matches fail exactly as a
        # stopped exporter would: a content entity must not be able to hide as runtime.
        if cls == "runtime" and not glob:
            # There is nothing to shape-check, so check the CONTRACT instead: it must be a legal
            # Draft 2020-12 schema and every $ref in it must resolve. That is what stops a contract
            # nobody can validate against records from rotting unnoticed for the year before the app
            # exists.
            try:
                Draft202012Validator.check_schema(doc)
            except Exception as e:                              # noqa: BLE001
                fails.append(f"{entity}: runtime contract is not a legal Draft 2020-12 schema — "
                             f"{str(e).splitlines()[0][:160]}")
                structural.add(entity)
            resolver = registry.resolver(base_uri=doc.get("$id", ""))
            for ref in sorted(collect_refs(doc)):
                try:
                    resolver.lookup(ref)
                except Exception as e:                          # noqa: BLE001
                    fails.append(f"{entity}: unresolvable $ref {ref!r} — "
                                 f"{str(e).splitlines()[0][:120]}")
                    structural.add(entity)
            runtime.append(entity)
            summary.append((entity, 0, 0, 0))
            continue
        if cls == "runtime":
            fails.append(f"{entity}: declared class 'runtime' but also declares a files glob {glob!r} "
                         f"— a runtime entity holds no committed records. Either drop the glob, or the "
                         f"entity is content and must say so.")
            structural.add(entity)
        if not glob:
            fails.append(f"{entity}: class {cls!r} declares no glob, so nothing was validated. Only a "
                         f"'runtime' entity may have no data; anything else with no glob is an entity "
                         f"the catalogue cannot locate.")
            structural.add(entity)
            summary.append((entity, 0, 0, 0))
            continue

        validator = Draft202012Validator(doc, registry=registry)
        id_field = meta.get("stable_id_field")
        root_id = None if entity in ROOT_ID_IS_FOREIGN else id_field
        decl_paths = DECLARATIONS.get(entity, set())
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
                if packing == "map" and isinstance(rec, dict):
                    # In a map the KEY is the address, and the values sit under a `*` path so one
                    # DECLARATIONS entry covers every key.
                    for k, v in rec.items():
                        if k in seen:
                            n_dup += 1
                            if shown < MAX_REPORT:
                                fails.append(f"{entity}: duplicate key {k!r} — {locator} and {seen[k]}")
                                shown += 1
                        seen[k] = locator
                        if ID_PATTERN.match(k):
                            known_ids.setdefault(k, entity)
                        scan(v, "*", decl_paths, root_id, declared, refs)
                else:
                    scan(rec, "", decl_paths, root_id, declared, refs)
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
        # An entity that validates nothing is not a passing entity. A moved directory, a renamed file
        # or a stopped exporter all read as `0 records` and used to print [OK ].
        if n_rec == 0:
            fails.append(f"{entity}: glob {glob!r} matched 0 records — the data moved, the exporter "
                         f"stopped, or the glob is wrong. Nothing was validated.")
            structural.add(entity)

    # ---- aliases: the second, legacy way to address a vocab record -----------------------------
    # corpus/vocab publishes `vocab:<jmdict_id>` (vocab:1580640), and after the vocab_identity migration
    # that is the form of every vocab reference this check can SEE — the count printed below says how
    # many of each, and it is the evidence for that claim rather than a comment asserting it. The table
    # stays because the headword form is not gone from the tree: it survives inside lesson-body markup
    # (`<check item-ref="vocab:人">`), which this scanner does not parse — ID_PATTERN is anchored at the
    # start of a string and a body starts with `<heading` — and in corpus/readings, which addresses
    # vocabulary by bare headword with no namespace at all. The moment either is wired into the graph
    # check, dropping the alias would report legitimate legacy references as broken.
    # A headword is NOT a unique address; the ambiguous ones in use are reported separately.
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

    runtime_set = set(runtime)
    print("================ CONTRACT GATE ================")
    for entity, n, bad, dup in summary:
        mark = "OK " if not (bad or dup or entity in structural) else "FAIL"
        if entity in runtime_set:
            print(f"  [{mark}] {entity:22} {'runtime':>6}  no committed records by contract; "
                  f"schema compiles and every $ref resolves")
            continue
        detail = "".join([f", {bad} invalid" if bad else "",
                          f", {dup} duplicate id" if dup else ""])
        print(f"  [{mark}] {entity:22} {n:>6} records{detail}")
    print(f"  ---- {total_records} records, {len(known_ids)} distinct stable ids, "
          f"{len(all_refs)} references, {len(runtime)} runtime contracts")

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
    by_form = Counter()
    for _, _, rid in all_refs:
        if rid.startswith("vocab:"):
            by_form["slug" if rid.split(":", 1)[1].isascii()
                    and rid.split(":", 1)[1].isdigit() else "headword"] += 1
        if rid in ambiguous:
            used[rid] += 1
    if by_form:
        print()
        print(f"  [info] vocab references: {by_form['slug']} by published slug, "
              f"{by_form['headword']} still by headword (the alias table below covers those).")
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
