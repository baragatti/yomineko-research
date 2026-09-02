#!/usr/bin/env python3
"""P7 — lesson coverage of the corpus, in the PUBLISHED SLUG NAMESPACE, read from the export.

Every item the courseware PLACES in a topic must be UNLOCKED by exactly one lesson, and every ref on
either side must resolve to a real registry record.

WHY THIS READS THE EXPORT AND NOT db/corpus.sqlite
--------------------------------------------------
It used to open `db/corpus.sqlite` and compare `SELECT headword FROM vocab WHERE
introducing_topic_id IS NOT NULL` against `lesson_unlocks.ref`, mapping integer refs back through
`headword`. That de-duplicates by authoring headword: it printed `vocab placed=2910 unlocked=2910`
where the export carries **2,946** distinct vocab unlock refs. The 36-record difference is exactly
the homograph class (米/こめ vs 米/メートル — the STRUCT-03 defect `validate_unlock_ledger.py`
documents), so a homograph coverage gap was structurally invisible to this gate. It also violated the
suite's own rule, stated at the top of `scripts/validate/README.md`: the committed JSON under
`corpus/` and `course/` is the source of truth, `db/corpus.sqlite` is a regenerable working index,
and every validator reads the export unless its row says otherwise — this one's row did not.

So both sides are now read from the export and keyed by the stable slug ref, the same namespace
`validate_unlock_ledger.py` works in:

  placed    = the union of `introduces_refs` over every topic in `course/outline.json` — the
              published statement of what each topic introduces
  unlocked  = the union of `unlocks[]` over every `course/*/topic-*/lesson-*.json` leaf

Checks, per kind (vocab / kanji / grammar):
  A  placed-but-NOT-unlocked  — a placed item no lesson teaches                            -> FAIL
  B  unlocked more than once across the lesson leaves (introduce-once)                     -> FAIL
  C  a placed or unlocked ref that resolves to no registry record                          -> FAIL
     (impossible to check in headword space: a headword is not an address, which is how the
     de-duplication hid the gap in the first place)
  D  unlocked-but-NOT-placed — taught without a topic placement (cosmetic metadata)         -> WARN

Empty input fails: a missing/empty outline, no lesson leaves, an empty registry, or a per-kind count
under its floor is a FAIL, not a silent pass. Floors sit far below the live counts so growth never
trips them.

Read-only. Exits non-zero on any FAIL. Usage: audit_coverage.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
MAX_SHOWN = 20

# unlock type -> (registry glob, floor on the placed count). Floors are ~2/3 of the live counts
# (2,946 vocab / 634 kanji / 496 grammar at the 2026-09-02 export) so real growth never trips them
# while a vanished, renamed or sidecar-shadowed directory does.
KINDS: dict[str, tuple[str, int]] = {
    "vocab": ("corpus/vocab/*.json", 2000),
    "kanji": ("corpus/kanji/*.json", 400),
    "grammar": ("corpus/grammar/*.json", 300),
}
MIN_LESSONS = 200  # 322 today


def load_registry_slugs(root: Path, glob_pat: str) -> set[str]:
    """Every stable slug in a registry glob, as it is addressed in an unlock ref ('vocab:1234567')."""
    slugs: set[str] = set()
    for path in sorted(root.glob(glob_pat)):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            slugs.add(rec["slug"])
    return slugs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to audit (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every offender, not the first 20")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    shown = None if args.list else MAX_SHOWN
    fails = 0
    warns = 0

    # ---- placed: the published topic statement ----------------------------------------------------
    outline_path = root / "course" / "outline.json"
    if not outline_path.exists():
        print(f"FAIL: no course/outline.json under {root} — nothing to audit")
        return 1
    outline = json.loads(outline_path.read_text(encoding="utf-8"))
    placed: dict[str, set[str]] = {k: set() for k in KINDS}
    n_topics = 0
    for module in outline:
        for topic in module.get("topics", []):
            n_topics += 1
            for kind, refs in (topic.get("introduces_refs") or {}).items():
                if kind in placed:
                    placed[kind].update(refs)

    # ---- unlocked: the lesson leaves --------------------------------------------------------------
    leaves = sorted(root.glob("course/*/topic-*/lesson-*.json"))
    if len(leaves) < MIN_LESSONS:
        print(f"FAIL: {len(leaves)} lesson leaves under {root}/course (floor {MIN_LESSONS}) — "
              "the courseware is missing, moved or shadowed")
        return 1
    unlocked_count: dict[str, Counter[str]] = {k: Counter() for k in KINDS}
    for leaf in leaves:
        data = json.loads(leaf.read_text(encoding="utf-8"))
        for unlock in data.get("unlocks", []):
            kind = unlock.get("type")
            if kind in unlocked_count:
                unlocked_count[kind][unlock["ref"]] += 1

    print(f"source: export ({n_topics} topics in course/outline.json, {len(leaves)} lesson leaves) — "
          "slug space, no db/corpus.sqlite")

    for kind, (glob_pat, floor) in KINDS.items():
        registry = load_registry_slugs(root, glob_pat)
        if not registry:
            print(f"FAIL: registry {glob_pat} is empty under {root} — cannot audit {kind} coverage")
            fails += 1
            continue
        place = placed[kind]
        counts = unlocked_count[kind]
        unlocked = set(counts)
        gap = place - unlocked
        extra = unlocked - place
        dup = {ref: n for ref, n in counts.items() if n > 1}
        unresolved = sorted({r for r in (place | unlocked) if r not in registry})

        print(f"== {kind} ==  registry={len(registry)} placed={len(place)} unlocked={len(unlocked)} "
              f"gap={len(gap)} unplaced={len(extra)} dup={len(dup)} unresolved={len(unresolved)}")
        if len(place) < floor:
            fails += 1
            print(f"   FAIL placed={len(place)} is under the floor {floor} — placements vanished")
        if gap:
            fails += 1
            print(f"   FAIL placed-but-not-unlocked: {sorted(gap)[:shown]}")
        if dup:
            fails += 1
            print(f"   FAIL introduce-once (unlocked by >1 lesson): "
                  f"{dict(sorted(dup.items())[:shown])}")
        if unresolved:
            fails += 1
            print(f"   FAIL ref resolves to no {kind} record: {unresolved[:shown]}")
        if extra:
            warns += 1
            print(f"   WARN unlocked-but-not-placed (taught w/o placement): {sorted(extra)[:shown]}")

    print(f"=== coverage audit: {fails} FAIL, {warns} WARN ===")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
