#!/usr/bin/env python3
"""Hard gate: nothing in the committed export addresses another record by a storage row number.

WHY THIS EXISTS
---------------
contracts/manifest.json states the rule in its own id_convention: "Some registries also carry an
integer `id`; that is a storage row number, it is NOT stable across a rebuild, and it must never be
used as an API key." contracts/README.md says the same. The export said otherwise, and no gate could
see it — validate_contracts.py's graph check matches strings against `^[a-z][a-z0-9_]*:`, so an
integer foreign key is structurally invisible to it:

  * 3,777 exam items pointed at vocabulary through `vocab_id` alone. `kr:n5:1` carried `vocab_id: 1`,
    which is SQLite row 1 = vocab:1565440 = 嗚呼; `vocab:1` resolves to nothing in the published JSON.
  * 20,490 sentence tokens in corpus/sentences/bank.json carried `vocab_id` and no slug, so the
    sentence->vocab edge of the spec §1.7 graph existed only inside the regenerable index — the one
    artefact the project has already declared non-authoritative.

Both were repaired by emitting the published slug alongside the row number. This gate is what stops
them coming back, and it checks the repair rather than trusting it: the slug has to be there, it has
to resolve in its registry, and it has to be the SAME record the integer names. A slug that merely
exists next to a stale row number is a worse bug than no slug at all, because it looks resolved.

WHAT IT CHECKS, over corpus/**/*.json and course/**/*.json (never db/corpus.sqlite)
  1. SIBLING   — every integer `<ns>_id` has a sibling stable id in the same object: a string under
                 slug / <ns> / <ns>_slug / ref beginning `<ns>:`.
  2. RESOLVES  — that sibling names a record that exists in the <ns> registry.
  3. AGREES    — the registry's own row number for that record equals the integer. This is the check
                 that catches a slug copied next to the wrong id, or an id left behind by a rebuild.
  4. INT-ONLY  — a list of integers under a `*_ids` key is a cross-entity edge with no stable form at
                 all, so it cannot be traversed from the committed JSON. There is nothing to check the
                 sibling of; the field itself is the defect.
  A record's own bare `id` integer is its storage row, not an edge, and is counted but not failed.

Registries are built from contracts/manifest.json, so a new entity with an integer row number is
covered automatically, and an integer FK into a namespace that publishes no registry fails loudly
rather than passing unexamined.

Exit 1 on any failure. Usage: validate_stable_addresses.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO = Path(__file__).resolve().parents[2]

MAX_REPORT = 15
# Where a sibling stable id is accepted. Deliberately a closed list: the point is that the address
# travels WITH the row number in a predictable place, not that one happens to exist somewhere nearby.
SIBLING_KEYS = ("slug", "ref")           # plus `<ns>` and `<ns>_slug`, added per namespace below

# Files that are not published records and are therefore out of scope. Each entry states why; an
# entry that matches no file is itself a failure, so a stale exclusion cannot hide a live one.
SCOPE_EXCLUSIONS: dict[str, str] = {
    "corpus/exam_banks/removed_items.json":
        "A tombstone ledger, not an exported record set: scripts/contracts/migrate_exam_banks_p7.py "
        "copies each removed item VERBATIM as it stood when it was removed, so that nothing is "
        "silently lost. Migrating the copies would rewrite the record of what was removed. The 19 "
        "sibling-less vocab_id values in here are the pre-migration shape, preserved on purpose.",
}


def build_registries(root: Path, manifest: dict) -> dict[str, dict]:
    """namespace -> {'slugs': set, 'row': {int id -> slug}} from every list-packed manifest entity.

    A registry entry exists only where a record publishes BOTH a stable id and an integer `id`; that
    pairing is what makes an integer FK checkable without the database.
    """
    reg: dict[str, dict] = defaultdict(lambda: {"slugs": set(), "row": {}})
    for ent in manifest["entities"]:
        field = ent.get("stable_id_field")
        if ent.get("packing") != "list" or not field:
            continue
        for path in sorted(root.glob(ent["files"])):
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                continue
            for rec in data:
                if not isinstance(rec, dict):
                    continue
                sid = rec.get(field)
                if not isinstance(sid, str) or ":" not in sid:
                    continue
                ns = sid.split(":", 1)[0]
                reg[ns]["slugs"].add(sid)
                row = rec.get("id")
                if isinstance(row, int) and not isinstance(row, bool):
                    reg[ns]["row"].setdefault(row, sid)
    return reg


def family_of(rel: str) -> str:
    parts = rel.split("/")
    return "/".join(parts[:2]) if len(parts) > 1 else rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    manifest_path = root / "contracts" / "manifest.json"
    if not manifest_path.exists():
        print(f"validate_stable_addresses: no contracts/manifest.json under {root}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reg = build_registries(root, manifest)

    fails: list[str] = []
    edges: Counter = Counter()          # (family, key) -> integer FKs seen
    ok_edges: Counter = Counter()       # (family, key) -> fully addressed
    own_rows: Counter = Counter()       # family -> records carrying their own row number
    intonly: Counter = Counter()        # (family, key) -> integers with no stable form at all
    intonly_sites: Counter = Counter()  # (family, key) -> how many records carry the field
    intonly_eg: dict = defaultdict(list)
    excluded_hits: Counter = Counter()

    def walk(node: object, rel: str, fam: str, owner: str) -> None:
        if isinstance(node, dict):
            here = node.get("slug") or node.get("id")
            if isinstance(here, str):
                owner = here
            for k, v in node.items():
                if k == "id" and isinstance(v, int) and not isinstance(v, bool):
                    own_rows[fam] += 1
                elif k.endswith("_ids") and isinstance(v, list) and any(
                        isinstance(x, int) and not isinstance(x, bool) for x in v):
                    n = sum(1 for x in v if isinstance(x, int) and not isinstance(x, bool))
                    # A row-id LIST is addressed the same way a scalar is: by a sibling slug list.
                    # `example_vocab_ids` + `example_vocab` (or `<base>_slugs`) side by side is the
                    # published form of the edge; only a PAIRLESS id list is the defect.
                    base = k[:-4]                          # example_vocab_ids -> example_vocab
                    sib_list = next((node[c] for c in (base, base + "_slugs", base.rsplit("_", 1)[0])
                                     if isinstance(node.get(c), list)
                                     and all(isinstance(x, str) and ":" in x for x in node[c])), None)
                    if sib_list is not None and len(sib_list) >= 1:
                        edges[(fam, k)] += n
                        ok_edges[(fam, k)] += n
                    else:
                        intonly[(fam, k)] += n
                        intonly_sites[(fam, k)] += 1
                        if len(intonly_eg[(fam, k)]) < 3:
                            intonly_eg[(fam, k)].append(f"{owner} in {rel} -> {v[:3]}")
                elif k.endswith("_id") and isinstance(v, int) and not isinstance(v, bool):
                    ns = k[:-3]
                    edges[(fam, k)] += 1
                    accepted = SIBLING_KEYS + (ns, f"{ns}_slug")
                    sib = next((node[s] for s in accepted
                                if isinstance(node.get(s), str)
                                and node[s].startswith(ns + ":")), None)
                    if sib is None:
                        fails.append(f"{rel}: {k}={v} has no sibling {ns}: address "
                                     f"(looked under {', '.join(accepted)}) — "
                                     f"e.g. {json.dumps(node, ensure_ascii=False)[:110]}")
                    elif ns not in reg:
                        fails.append(f"{rel}: {k}={v} points into namespace {ns!r}, which publishes "
                                     f"no registry in contracts/manifest.json — nothing can check it")
                    elif sib not in reg[ns]["slugs"]:
                        fails.append(f"{rel}: {k}={v} carries {sib!r}, which resolves to no "
                                     f"{ns} record")
                    elif reg[ns]["row"].get(v) != sib:
                        fails.append(f"{rel}: {k}={v} is row {reg[ns]['row'].get(v)!r} in the {ns} "
                                     f"registry but sits beside {sib!r} — the row number and the "
                                     f"address name different records")
                    else:
                        ok_edges[(fam, k)] += 1
                walk(v, rel, fam, owner)
        elif isinstance(node, list):
            for x in node:
                walk(x, rel, fam, owner)

    files = sorted(set(root.glob("corpus/**/*.json")) | set(root.glob("course/**/*.json")))
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel in SCOPE_EXCLUSIONS:
            excluded_hits[rel] += 1
            continue
        walk(json.loads(path.read_text(encoding="utf-8")), rel, family_of(rel), rel)

    # One failure per FIELD, not per occurrence: `example_vocab_ids` is one design defect repeated
    # 1,488 times, and 1,488 identical lines would bury every other failure under the report cap.
    for key in sorted(intonly):
        fam, k = key
        fails.append(f"{fam}: {k} carries {intonly[key]} storage row number(s) across "
                     f"{intonly_sites[key]} record(s) with no stable id beside them — this edge "
                     f"cannot be traversed from the committed JSON (manifest id_convention: a row "
                     f"number \"must never be used as an API key\"). e.g. "
                     + "; ".join(intonly_eg[key]))

    for rel in SCOPE_EXCLUSIONS:
        if not excluded_hits[rel]:
            fails.append(f"SCOPE_EXCLUSIONS lists {rel!r}, which matches no file under {root} — "
                         f"an exclusion that excludes nothing hides the rule it was written for")

    print("=========== STABLE ADDRESS GATE ===========")
    print(f"  {'file family':24} {'field':18} {'edges':>7} {'addressed':>10}")
    for key in sorted(set(edges) | set(intonly)):
        fam, k = key
        if key in intonly:
            print(f" !{fam:24} {k:18} {intonly[key]:>7} {'0 (no slug form)':>10}")
        else:
            mark = " " if ok_edges[key] == edges[key] else "!"
            print(f" {mark}{fam:24} {k:18} {edges[key]:>7} {ok_edges[key]:>10}")
    print(f"  ---- {sum(edges.values())} integer foreign keys, "
          f"{sum(ok_edges.values())} fully addressed, {sum(intonly.values())} with no stable form; "
          f"{sum(own_rows.values())} records carry their own row number (not an edge)")
    for rel, why in SCOPE_EXCLUSIONS.items():
        print(f"  [scope] {rel} excluded: {why.split(':')[0]}")

    if fails:
        print()
        shown = fails if args.list else fails[:MAX_REPORT]
        for f in shown:
            print("  FAIL", f)
        if len(fails) > len(shown):
            print(f"  ... {len(fails) - len(shown)} more (use --list)")

    print(f"\nvalidate_stable_addresses: {len(files)} files, {sum(edges.values())} integer FKs, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
