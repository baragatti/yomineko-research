#!/usr/bin/env python3
"""Hard gate: provenance in the COMMITTED EXPORT is stated, typed, and internally consistent.

WHY THIS EXISTS
---------------
Spec §1.1 says every record carries a `source` and belongs to exactly one layer, and §1.2 says every
generated artefact is `ai_generated: true` AND `needs_review: true`. Three separate reviews found the
export saying otherwise while every gate reported green:

  * 359 exam items were `ai_generated: true` with no `needs_review` key at all (n4_context_fill 130,
    n5_sentence_order 79, n5_context_fill 77, n3_context_fill 62, n5_grammar_form 11 — e.g.
    cf:n4:1111:1132, so:n5:1126, gf:n5:2348), and 5,275 of 6,166 items carried neither `layer` nor
    `needs_review`. A consumer reading `item.needs_review === true` got `undefined`, which is falsy,
    so unreviewed generated Japanese sorted into the picker's preferred "real" tier.
  * `needs_review` was an integer 1 on four entities and a boolean true on five (repaired 2026-08-26).
  * contracts/exam_item.schema.json could not notice any of it, because build_schemas.py derives
    `required` from measured frequency — the contract was inferred FROM the defect, so it encoded it.
    This validator is deliberately stricter than that schema for exactly that reason.

WHAT IT CHECKS
--------------
The entity list is driven by contracts/manifest.json, so a new entity is covered the day it is
exported rather than the day someone remembers to add it here.

  a) ai_generated true  => needs_review true.
  b) layer 'C'          => needs_review true (Layer C is pedagogy; it always needs teacher sign-off).
  c) needs_review / ai_generated are real JSON booleans — never 0/1, never "true".
  d) layer is one of A / B / C.
  e) no record is missing a provenance field its own entity otherwise carries. The declared set is
     inferred per entity from the data (any field present on ANY record of that entity is expected on
     ALL of them), except where REQUIRED_PROVENANCE pins it explicitly, and except for the documented
     opt-outs in PARTIAL_PROVENANCE. Inference is what catches "5,275 items with no needs_review while
     their siblings in the same directory have one"; the pins are what stop the expectation from
     collapsing the way a measured schema does when a whole bank is missing a field.
  f) EXAM DERIVATION TABLE. An exam item's `ai_generated` is not free-form: it is derived, and the
     derivation is written down in scripts/contracts/migrate_exam_banks_p7.py (FAMILY /
     SENTENCE_DERIVED / ALWAYS_REAL, and the docstring paragraph explaining that `ai_generated` on an
     exam item means "the JAPANESE the learner reads was model-generated"). That module is imported
     here and used as the contract, so the two can never drift:
       - cf / gf / so / pp / us  -> copied from the referenced sentence's provenance.ai_generated;
       - kr / or / tg / rc       -> false (selection or derivation from human-written sources);
       - listening lt/lp/ls/lr/lg-> true (the scripts are generated Japanese);
       - layer per the FAMILY table; an unknown id prefix is a failure, not a default.

Reads the exported JSON only. Never db/corpus.sqlite.
Exit 1 on any failure. Usage: validate_provenance_json.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO = Path(__file__).resolve().parents[2]
MIGRATION = REPO / "scripts" / "contracts" / "migrate_exam_banks_p7.py"

MAX_REPORT = 15
FIELDS = ("layer", "source", "needs_review", "ai_generated")
BOOL_FIELDS = ("needs_review", "ai_generated")
LAYERS = {"A", "B", "C"}

# Entities whose provenance set is PINNED rather than inferred. Pinning matters where a whole file
# could lose a field at once: inference would then read the absence as "this entity does not carry it".
REQUIRED_PROVENANCE: dict[str, tuple[str, ...]] = {
    # Spec §1.1 applied to the exam banks, which is what the 2026-08 migration backfilled.
    "exam_item": ("source", "layer", "ai_generated", "needs_review"),
}

# Entities where a provenance field is legitimately present on some records and absent on others.
# Empty on purpose: today every entity is all-or-nothing, and that is the property worth defending.
# An entry here is a written decision, not a silencer — give the reason in the value.
PARTIAL_PROVENANCE: dict[str, dict[str, str]] = {}


def load_derivation_contract():
    """Import the migration module and use ITS tables, so this gate cannot drift from the rule.

    The contract is code and lives with the code, so it is read from the repo, not from --root
    (--root points at data, which may be a mutated copy of the tree with no scripts/ in it).
    """
    spec = importlib.util.spec_from_file_location("migrate_exam_banks_p7", MIGRATION)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import the derivation contract at {MIGRATION}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FAMILY, mod.SENTENCE_DERIVED, mod.ALWAYS_REAL


def records_of(path: Path, packing: str, rel: str):
    """Yield (locator, record). Mirrors validate_contracts.py's packing rules."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if packing == "single":
        yield rel, data
    elif packing == "map":
        for k, v in data.items():
            yield f"{rel}[{k}]", v if isinstance(v, dict) else {}
    else:
        for i, rec in enumerate(data):
            if not isinstance(rec, dict):
                continue
            key = rec.get("slug") or rec.get("id") or f"#{i}"
            yield f"{rel}[{key}]", rec


def prov_view(rec: dict) -> dict[str, tuple[str, object]]:
    """Flatten a record's provenance into {field: (qualified_name, value)}.

    A record may state provenance at its root (exam items, exercises, lessons) or inside a
    `provenance` object (sentences). Both are the same claim and both are checked the same way.
    """
    view: dict[str, tuple[str, object]] = {}
    nested = rec.get("provenance")
    if isinstance(nested, dict):
        for f in FIELDS:
            if f in nested:
                view[f] = (f"provenance.{f}", nested[f])
    for f in FIELDS:
        if f in rec:
            view[f] = (f, rec[f])
    return view


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    manifest_path = root / "contracts" / "manifest.json"
    if not manifest_path.exists():
        print(f"validate_provenance_json: no contracts/manifest.json under {root}", file=sys.stderr)
        return 2
    entities = json.loads(manifest_path.read_text(encoding="utf-8"))["entities"]
    family_layer, sentence_derived, always_real = load_derivation_contract()

    # Sentence provenance is the ground truth the sentence-derived exam families copy from.
    sent_ai: dict[str, bool] = {}
    bank = root / "corpus" / "sentences" / "bank.json"
    if bank.exists():
        for r in json.loads(bank.read_text(encoding="utf-8")):
            sent_ai[r["slug"]] = bool(r.get("provenance", {}).get("ai_generated"))

    fails: list[str] = []
    rows: list[tuple[str, int, int, int, int, int, int]] = []
    total_records = 0

    for ent in entities:
        entity, packing, glob = ent["entity"], ent.get("packing", "list"), ent["files"]
        if not glob:
            # A `runtime` entity (W26: user-state contracts such as card / review_log) has a schema
            # and no committed records by contract — there is no provenance to check. Content
            # entities without a glob are validate_contracts' failure, not ours.
            continue
        seen: list[tuple[str, dict]] = []
        declared: set[str] = set()
        for path in sorted(root.glob(glob)):
            rel = path.relative_to(root).as_posix()
            for locator, rec in records_of(path, packing, rel):
                view = prov_view(rec)
                seen.append((locator, rec))
                declared |= {q for q, _ in view.values()}
        if not seen:
            continue

        pinned = REQUIRED_PROVENANCE.get(entity)
        expected = set(pinned) if pinned else {q.split(".")[-1] for q in declared}
        expected -= set(PARTIAL_PROVENANCE.get(entity, {}))
        # Keep the qualified form so a nested-provenance entity reports `provenance.needs_review`.
        qualify = {q.split(".")[-1]: q for q in declared}

        n_ai = n_c = n_type = n_missing = n_layer = n_deriv = 0
        for locator, rec in seen:
            view = prov_view(rec)
            get = {f: v for f, (_, v) in view.items()}

            for f in BOOL_FIELDS:
                if f in get and not isinstance(get[f], bool):
                    n_type += 1
                    fails.append(f"{entity}: {locator}: {view[f][0]} is "
                                 f"{type(get[f]).__name__} {get[f]!r}, must be a JSON boolean")
            if get.get("ai_generated") is True and get.get("needs_review") is not True:
                n_ai += 1
                fails.append(f"{entity}: {locator}: ai_generated true but needs_review is "
                             f"{get.get('needs_review')!r} (spec §1.2: generated => needs a teacher)")
            if get.get("layer") == "C" and get.get("needs_review") is not True:
                n_c += 1
                fails.append(f"{entity}: {locator}: layer C but needs_review is "
                             f"{get.get('needs_review')!r} (Layer C always needs review)")
            if "layer" in get and get["layer"] not in LAYERS:
                n_layer += 1
                fails.append(f"{entity}: {locator}: layer {get['layer']!r} is not one of A/B/C")
            for f in sorted(expected - set(get)):
                n_missing += 1
                where = qualify.get(f, f)
                why = ("pinned by REQUIRED_PROVENANCE" if pinned
                       else f"other {entity} records carry it")
                fails.append(f"{entity}: {locator}: missing {where} ({why})")

            # ---- f) the exam derivation table ----------------------------------------------------
            if entity == "exam_item":
                fam = str(rec.get("id", "")).split(":", 1)[0]
                if fam not in family_layer:
                    n_deriv += 1
                    fails.append(f"{entity}: {locator}: id prefix {fam!r} is in no family of "
                                 f"migrate_exam_banks_p7.FAMILY — provenance cannot be derived")
                    continue
                want_layer = family_layer[fam][0]
                if get.get("layer") != want_layer:
                    n_deriv += 1
                    fails.append(f"{entity}: {locator}: layer {get.get('layer')!r}, "
                                 f"derivation table says {want_layer!r} for family {fam!r}")
                if fam in sentence_derived:
                    sref = rec.get("sentence")
                    if sref not in sent_ai:
                        n_deriv += 1
                        fails.append(f"{entity}: {locator}: family {fam!r} derives ai_generated from "
                                     f"its sentence, but {sref!r} is not in corpus/sentences/bank.json")
                    elif bool(get.get("ai_generated")) != sent_ai[sref]:
                        n_deriv += 1
                        fails.append(f"{entity}: {locator}: ai_generated "
                                     f"{get.get('ai_generated')!r} != {sent_ai[sref]!r} on its source "
                                     f"sentence {sref} (family {fam!r} copies it)")
                elif fam in always_real:
                    if get.get("ai_generated") is not False:
                        n_deriv += 1
                        fails.append(f"{entity}: {locator}: family {fam!r} is always-real Japanese, "
                                     f"ai_generated must be false, got {get.get('ai_generated')!r}")
                else:
                    if get.get("ai_generated") is not True:
                        n_deriv += 1
                        fails.append(f"{entity}: {locator}: listening family {fam!r} has generated "
                                     f"Japanese, ai_generated must be true, "
                                     f"got {get.get('ai_generated')!r}")

        total_records += len(seen)
        rows.append((entity, len(seen), n_ai, n_c, n_type, n_missing, n_layer + n_deriv))

    # An exemption that matches nothing is itself a failure — it hides a rule that no longer applies.
    for entity, optouts in PARTIAL_PROVENANCE.items():
        if entity not in {r[0] for r in rows}:
            fails.append(f"PARTIAL_PROVENANCE names entity {entity!r}, which exported no records")

    print("============== PROVENANCE GATE ==============")
    print(f"  {'entity':22} {'records':>7} {'ai&!rev':>8} {'C&!rev':>7} {'non-bool':>9} "
          f"{'missing':>8} {'derived':>8}")
    for entity, n, a, c, t, m, d in rows:
        mark = " " if not (a or c or t or m or d) else "!"
        print(f" {mark}{entity:22} {n:>7} {a:>8} {c:>7} {t:>9} {m:>8} {d:>8}")
    print(f"  ---- {total_records} records across {len(rows)} entities")

    if fails:
        print()
        shown = fails if args.list else fails[:MAX_REPORT]
        for f in shown:
            print("  FAIL", f)
        if len(fails) > len(shown):
            print(f"  ... {len(fails) - len(shown)} more (use --list)")

    print(f"\nvalidate_provenance_json: {total_records} records, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
