#!/usr/bin/env python3
"""Gate (W23): every lesson exercise says what it TESTS, and what it says is true on this tree.

`lesson.exercises[].item_refs[]` (design/assessment.md §2) is what the mistake index, the topic-test
assembler and the placement probe key on. A stale or invented target there silently corrupts all three,
so the field is re-derived here on the tree being validated, the W21 C4 pattern.

Over the EXPORTED JSON (course/, corpus/) plus the two practice tables and the authoring source the
derivation reads. Hard checks:

  A  every `ref` resolves to an exported record of its `type` (vocab / kanji / grammar registries, the
     kana glyph or family records)
  B  every `ref` is inside its lesson's cumulative_known_set (a kana glyph through its family): the
     gating rule, per exercise
  C  every exercise has >= 1 `role: target` entry, or is listed in course/item_ref_exemptions.json
     with a reason, or is authoring residue counted against the ratchet (scripts/validate/
     item_refs_baseline.json, per (level, type); growth FAILS, shrinkage prints the ceiling to lower)
  D  the exemption file cannot rot: an entry naming no exercise, an exempt exercise that has a
     target, a missing reason, all FAIL
  E  re-derivation: scripts/derive_item_refs.py's rule, re-run here, must reproduce every exercise's
     stored array exactly (entries a rule made, in order); an exercise whose refs are `authored` is
     exempt from E by construction and held by A + B
  F  a `table:*` entry replays against its table: the exercise's refs are exactly the row's targets
  G  floors: >= 250 lessons, >= 2,000 exercises, >= 3,000 target refs; the array is sorted by
     (type, ref) with no duplicate

Plant proof (--selftest is not provided; recorded in research/reports/w23_apply_report.md): a ref at a
retired slug (A), a ref at an item the lesson has not taught (B), a blanked array (C), an exemption
for an exercise with refs (D), one derived ref hand-edited to another real item (E).
Usage: validate_item_refs.py [--root PATH] [--list] [--write-baseline]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import derive_item_refs as dir_  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]
BASELINE = HERE / "item_refs_baseline.json"
EXEMPT_REL = "course/item_ref_exemptions.json"
MIN_LESSONS, MIN_EXERCISES, MIN_TARGETS = 250, 2000, 3000
MAX_SHOWN = 20


def registry(root: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    for kind, glob, key in (("vocab", "corpus/vocab/*.json", "slug"), ("kanji", "corpus/kanji/*.json", "slug"),
                            ("grammar", "corpus/grammar/*.json", "slug"),
                            ("kana", "corpus/kana/[hk]*.json", "id")):
        for p in sorted(root.glob(glob)):
            out[kind] |= {r[key] for r in json.loads(p.read_text(encoding="utf-8"))}
    fam = root / "corpus" / "kana" / "families.json"
    if fam.exists():
        for groups in json.loads(fam.read_text(encoding="utf-8")).values():
            out["kana"] |= {g["id"] for g in groups}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    fails: list[str] = []

    lessons = dir_.load_lessons(root)
    ctx = dir_.Context(root)
    reg = registry(root)
    exempt_doc = json.loads((root / EXEMPT_REL).read_text(encoding="utf-8")) \
        if (root / EXEMPT_REL).exists() else None
    if exempt_doc is None:
        fails.append(f"{EXEMPT_REL} missing")
    exempt: dict[str, str] = {}
    for e in (exempt_doc or {}).get("exercises") or []:
        if not (e.get("id") and (e.get("reason") or "").strip()):
            fails.append(f"D {EXEMPT_REL}: entry {e!r} needs an id and a non-empty reason")
            continue
        exempt[e["id"]] = e["reason"]

    n_ex = n_targets = 0
    seen: set[str] = set()
    residue: collections.Counter = collections.Counter()
    for les in lessons:
        cks = {k: set((les.get("cumulative_known_set") or {}).get(k) or []) for k in dir_.ITEM_UNLOCKS}
        for ex in les.get("exercises") or []:
            n_ex += 1
            eid = ex["id"]
            seen.add(eid)
            refs = ex.get("item_refs")
            if not isinstance(refs, list):
                fails.append(f"G {eid}: item_refs missing or not an array")
                continue
            keys = [(e.get("type"), e.get("ref")) for e in refs]
            if keys != sorted(set(keys), key=lambda k: (str(k[0]), str(k[1]))):
                fails.append(f"G {eid}: item_refs not sorted by (type, ref) or duplicated")
            targets = [e for e in refs if e.get("role") == "target"]
            n_targets += len(targets)
            for e in refs:
                t, ref = e.get("type"), e.get("ref") or ""
                if dir_.ref_type(ref) != t or ref not in reg.get(t or "", set()):
                    fails.append(f"A {eid}: {t} {ref} resolves to no exported {t} record")
                elif not dir_._known(ctx, ref, cks):
                    fails.append(f"B {eid}: {ref} is not in {les['id']}'s cumulative_known_set")
            # C / D
            if targets and eid in exempt:
                fails.append(f"D {EXEMPT_REL}: {eid} is exempt but carries a target - delete the entry")
            if not targets and eid not in exempt:
                residue[f"{les.get('level')}|{ex.get('type')}"] += 1
            # E / F
            by = {e.get("derived_by") for e in refs}
            if "authored" in by:
                if by != {"authored"}:
                    fails.append(f"E {eid}: authored refs mixed with rule-made ones {sorted(map(str, by))}")
                continue
            if eid in ctx.tables:
                name, want = ctx.tables[eid]
                if sorted(e["ref"] for e in refs) != sorted(want) or by != {f"table:{name}"}:
                    fails.append(f"F {eid}: refs {sorted(e['ref'] for e in refs)} != {name} targets "
                                 f"{sorted(want)}")
                continue
            again = dir_.derive_exercise(ctx, les, ex)
            if again != refs:
                fails.append(f"E {eid}: stored {[(e['ref'], e.get('derived_by')) for e in refs]} "
                             f"!= re-derived {[(e['ref'], e['derived_by']) for e in again]}")
    for eid in sorted(set(exempt) - seen):
        fails.append(f"D {EXEMPT_REL}: {eid} names no exported exercise - stale entry")

    if len(lessons) < MIN_LESSONS or n_ex < MIN_EXERCISES or n_targets < MIN_TARGETS:
        fails.append(f"G floors: {len(lessons)} lessons / {n_ex} exercises / {n_targets} targets "
                     f"(floors {MIN_LESSONS} / {MIN_EXERCISES} / {MIN_TARGETS})")

    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "_why": "Frozen ceilings for validate_item_refs.py check C: exercises in a lesson that "
                    "teaches items for which no rule of design/assessment.md §2.2 finds a target, per "
                    "(level, type). The authoring residue W23 listed in "
                    "research/derived/pending/item_refs_residue.json. Growth FAILS; shrinkage prints "
                    "the ceiling to lower.",
            "no_target": dict(sorted(residue.items()))}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
    base = json.loads(BASELINE.read_text(encoding="utf-8")).get("no_target", {}) \
        if BASELINE.exists() else None
    drops = []
    if base is None:
        fails.append("item_refs_baseline.json missing - freeze it with --write-baseline")
    else:
        for k in sorted(set(base) | set(residue)):
            now, was = residue.get(k, 0), base.get(k)
            if was is None:
                fails.append(f"C {k}: {now} exercise(s) with no target and no exemption, no ceiling")
            elif now > was:
                fails.append(f"C {k}: exercises with no target GREW {was} -> {now}")
            elif now < was:
                drops.append(f"{k} {was} -> {now}")

    for d in drops:
        print(f"  ADVISORY: residue shrank {d}; lower the ceiling with --write-baseline")
    shown = fails if args.list else fails[:MAX_SHOWN]
    for f in shown:
        print(f"  FAIL {f}")
    if len(fails) > len(shown):
        print(f"  ... and {len(fails) - len(shown)} more (--list)")
    print(f"\nvalidate_item_refs: {len(lessons)} lessons, {n_ex} exercises, {n_targets} target refs, "
          f"{len(exempt)} exempt, {sum(residue.values())} residue | {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
