#!/usr/bin/env python3
"""W34 / readiness G10 — R78's strand budget, per stage of `course/speak/`, as a gate.

THE RULE, VERBATIM (design/learning_science.md §2.13):

    R78 [enforceable] DO declare the strand budget as a constant and hold each stage within ±10
    points: speaking path 15/30/25/30 (input/output/language-focused/fluency), JLPT path 25/25/35/20.

and the clause above it that this file also enforces:

    R77 [enforceable] DO tag every unit component with `strand ∈ {meaning-input, meaning-output,
    language-focused, fluency}` and emit a per-unit and per-stage histogram into the manifest; fail
    if any strand is 0% across a stage.

WHY THIS IS A SECOND FILE AND NOT A CHECK INSIDE validate_speaking_path.py
--------------------------------------------------------------------------
`validate_speaking_path.py` checks exactly one thing about the histogram — that it sums to 100
(`abs(sum - 100) > 2`) — and nothing about what it sums to. So the budget R78 declares as a constant
was enforced by nothing while all twelve stages sat outside it, which is finding G10 of
`research/reports/readiness/speak_fast_path.md`. This file is the gate that was missing; it is
separate because it carries its own frozen baseline and its own `--record`, and a ratchet buried
inside a 630-line clean validator is a ratchet nobody can point a plant at.

WHAT IS MEASURED, AND WHY IT IS RECOMPUTED RATHER THAN READ
-----------------------------------------------------------
The strand of a component is fixed by `scripts/export/build_speaking_practice.py::STRAND`, mirrored
in `COMPONENTS` below:

    meaning-input     say_now + shadowing
    meaning-output    production
    language-focused  words + patterns + kanji_recognition + checkpoint + drills
    fluency           fluency.items

Every unit also SHIPS the answer, in `strand_counts`. This gate does not trust it, for two reasons.
A ratchet that reads a number the tree under test writes is a ratchet a one-line edit to that number
defeats — the plant proof for this file is exactly that edit. And the shipped number is in fact
wrong today: `build_speaking_practice.py` computes `strand_counts` including `len(u["checkpoint"])`,
but it runs BEFORE `build_speaking_checkpoints.py` writes any checkpoints, so 71 of 72 units ship a
`language-focused` count that is short by exactly that unit's checkpoint items — 365 components the
declared histogram does not know about. That is why the percentages here differ from the ones G10
printed (path-wide meaning-output 6.3% recomputed against G10's 7.1% declared): G10 summed the field,
this sums the components. The disagreement is itself ratcheted below (`stale_histograms`), so the
rebalance half of W34 has a counter to drive to zero.

WHAT GATES HARD, TODAY
-----------------------
  * R77's own clause: a strand that is 0% across a whole stage FAILS. All four are non-zero in all
    twelve stages today, so this gates without failing — it is the wall that stops a rebalance from
    deleting a strand rather than balancing it.
  * A component carrying a `strand` tag that disagrees with the taxonomy FAILS (0 today).
  * Floors: fewer than 12 stages, 60 units or 2,000 components is a vanished or shadowed tree, not a
    balanced one.

WHAT IS RATCHETED
-----------------
Per (stage, strand), the DISTANCE from budget in percentage points, frozen in
`speak_strand_baseline.json` at today's measurement. **A stage moving FURTHER from band on any
strand is a hard failure** — the rebalance may not make a stage worse to make another better.
Moving closer prints "lower the ceiling". 12 of 12 stages are out of band on 3 or 4 of the 4 strands
today; when a stage's four distances all reach ≤ 10 it is reported as in-band so R78 can gate it
hard and the ratchet row can go.

FALSIFIABILITY (2026-09-02, seven plants on a copied tree, all caught)
----------------------------------------------------------------------
The fixture is a copy of `course/speak`, `corpus/sentences`, this file, `speak_path_common.py`, the
baseline, `scripts/export/{build_speaking_path,pattern_forms}.py` and `scripts/dbtarget.py`; the
COPIED validator is run with `--root <fixture>`, so nothing resolves back into the real repo. The
unmutated copy reports 0 FAIL.

  shopping loses 2 of 3 production items per unit  -> ratchet shopping|language-focused: the stage
                                                      moved FURTHER from budget, 25.0 -> 27.5
  strand_counts of arrival-01 hand-edited in-band  -> ratchet stale_histograms: 71 -> 72, and the
                                                      per-stage percentages do not move at all
  lodging loses every production item              -> lodging: strand meaning-output is 0% across
                                                      the whole stage (R77)
  one drill re-tagged strand="fluency"             -> speak:eating-02: drill tagged strand='fluency'
  course/speak removed                             -> the speaking path could not be read, 1 FAIL
  a declared unit file deleted                     -> speak:health-04 is declared and missing
  baseline ceilings emptied                        -> 49 FAIL: nothing frozen, nothing falsifiable

Reads exported JSON only; never db/corpus.sqlite.
Usage: validate_speak_strands.py [--root PATH] [--record] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from speak_path_common import (  # noqa: E402
    REPO, STRANDS, iter_units, jload, load_course,
)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

BASELINE = Path(__file__).resolve().parent / "speak_strand_baseline.json"
MAX_REPORT = 20

# design/learning_science.md R78, speaking path. Percentage points.
BUDGET = {"meaning-input": 15, "meaning-output": 30, "language-focused": 25, "fluency": 30}
TOLERANCE = 10.0        # R78: "hold each stage within ±10 points"
# Float noise guard: distances are compared at the precision they are stored (0.1 pt).
EPS = 0.05

# Floors. Far below the real path (12 stages / 72 units / 3,378 components) so growth never trips
# them, high enough that a walk over an empty or shadowed tree cannot pass.
FLOOR_STAGES, FLOOR_UNITS, FLOOR_COMPONENTS = 12, 60, 2000

# build_speaking_practice.py::STRAND, as (strand -> the unit fields that count toward it).
COMPONENTS: dict[str, tuple[str, ...]] = {
    "meaning-input": ("say_now", "shadowing"),
    "meaning-output": ("production",),
    "language-focused": ("words", "patterns", "kanji_recognition", "checkpoint", "drills"),
    "fluency": ("fluency",),
}
# The strand each component-level `strand` tag must carry, for the components that carry one.
TAGGED = {"production": "meaning-output", "drills": "language-focused", "fluency": "fluency"}

NOTE = ("W34 ratchet (readiness G10). Per (stage, strand): `pct` is context, `dist` is the DEBT — "
        "the distance in percentage points from R78's 15/30/25/30 speaking-path budget — and may "
        "only shrink. A stage moving further from band is a hard failure: the rebalance may not "
        "make one stage worse to improve another. `stale_histograms` counts units whose shipped "
        "`strand_counts` disagrees with the components they actually hold (today: every unit that "
        "has checkpoints, because build_speaking_practice.py computes the field before "
        "build_speaking_checkpoints.py writes them). Re-record with --record only after a "
        "deliberate rebalance, never to silence a failure you have not explained. Retired when all "
        "twelve stages are inside ±10 on all four strands and R78 gates hard.")


def unit_counts(u: dict) -> dict[str, int]:
    """The four strand counts of one unit, recomputed from the components it actually holds."""
    out = {s: 0 for s in STRANDS}
    for strand, fields in COMPONENTS.items():
        for f in fields:
            v = u.get(f)
            if f == "fluency":
                out[strand] += len((v or {}).get("items", []))
            else:
                out[strand] += len(v or [])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="R78 strand budget per speaking-path stage")
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--record", action="store_true",
                    help="re-freeze the ratchet after a DELIBERATE rebalance; never to hide a failure")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 20")
    # The ratchet is a property of the PROJECT, so it sits beside this script and --root does not
    # move it. --baseline exists so a falsifiability proof can point a run at a mutated ceiling file.
    ap.add_argument("--baseline", default=str(BASELINE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    baseline_path = Path(args.baseline).resolve()

    fails: list[str] = []
    try:
        course = load_course(root)
        units = iter_units(root, course)
    except (FileNotFoundError, ValueError) as exc:
        print(f"  [FAIL] {exc}")
        print("validate_speak_strands: the speaking path could not be read — 1 FAIL")
        return 1

    observed: dict[str, dict] = {}
    per_stage: dict[str, dict[str, int]] = {}
    stale_histograms = 0
    total_components = 0

    for row in units:
        u = row["unit"]
        counts = unit_counts(u)
        total_components += sum(counts.values())
        agg = per_stage.setdefault(row["stage"], {s: 0 for s in STRANDS})
        for s in STRANDS:
            agg[s] += counts[s]

        declared = u.get("strand_counts")
        if not isinstance(declared, dict) or set(declared) != set(STRANDS):
            fails.append(f"{row['id']}: strand_counts is {declared!r}, not the four R77 strands")
        elif {k: int(v) for k, v in declared.items()} != counts:
            stale_histograms += 1

        # R77: every component that carries a `strand` tag must carry the right one.
        for pr in u.get("production") or []:
            if pr.get("strand") != TAGGED["production"]:
                fails.append(f"{row['id']}: production item tagged strand={pr.get('strand')!r}, "
                             f"not {TAGGED['production']!r} (R77)")
        for dr in u.get("drills") or []:
            if dr.get("strand") != TAGGED["drills"]:
                fails.append(f"{row['id']}: drill tagged strand={dr.get('strand')!r}, "
                             f"not {TAGGED['drills']!r} (R77)")
        fl = u.get("fluency")
        if fl and fl.get("strand") != TAGGED["fluency"]:
            fails.append(f"{row['id']}: fluency block tagged strand={fl.get('strand')!r}, "
                         f"not {TAGGED['fluency']!r} (R77)")

    # ---- floors: an empty or shadowed tree must fail, not certify a perfect balance --------------
    if len(per_stage) < FLOOR_STAGES:
        fails.append(f"{len(per_stage)} stages walked, floor is {FLOOR_STAGES} — the path is missing "
                     f"or the stage list was shadowed")
    if len(units) < FLOOR_UNITS:
        fails.append(f"{len(units)} units walked, floor is {FLOOR_UNITS}")
    if total_components < FLOOR_COMPONENTS:
        fails.append(f"{total_components} strand-bearing components, floor is {FLOOR_COMPONENTS} — a "
                     f"histogram over nothing is not a balanced histogram")

    # ---- the measurement -------------------------------------------------------------------------
    in_band: list[str] = []
    path_wide = {s: 0 for s in STRANDS}
    for stage, agg in per_stage.items():
        total = sum(agg.values())
        for s in STRANDS:
            path_wide[s] += agg[s]
        if total == 0:
            fails.append(f"{stage}: no strand-bearing components at all")
            continue
        pct = {s: round(100 * agg[s] / total, 1) for s in STRANDS}
        for s in STRANDS:
            # R77's own clause, and the wall a rebalance must not walk through.
            if agg[s] == 0:
                fails.append(f"{stage}: strand {s} is 0% across the whole stage (R77)")
            observed[f"{stage}|{s}"] = {"n": agg[s], "pct": pct[s],
                                        "dist": round(abs(pct[s] - BUDGET[s]), 1)}
        if all(observed[f"{stage}|{s}"]["dist"] <= TOLERANCE for s in STRANDS):
            in_band.append(stage)

    # ---- the ratchet ------------------------------------------------------------------------------
    if args.record:
        payload = {"note": NOTE, "budget": BUDGET, "tolerance": TOLERANCE,
                   "stale_histograms": stale_histograms,
                   "ceilings": {k: observed[k] for k in sorted(observed)}}
        baseline_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"recorded {len(observed)} (stage, strand) ceilings and stale_histograms="
              f"{stale_histograms} -> {baseline_path.name}")
        return 0

    base = jload(baseline_path) if baseline_path.exists() else {}
    ceilings = base.get("ceilings", {}) if isinstance(base, dict) else {}
    if not ceilings:
        fails.append(f"{baseline_path.name} holds no ceilings — a ratchet with nothing frozen in it "
                     f"cannot fail on growth. Record it with --record.")
    if isinstance(base, dict) and base.get("budget") not in (None, BUDGET):
        fails.append(f"{baseline_path.name} was frozen against budget {base.get('budget')}, this run "
                     f"measures against R78's {BUDGET} — re-record deliberately")

    grew: list[str] = []
    shrank: list[str] = []
    for key in sorted(set(observed) | set(ceilings)):
        got, want = observed.get(key), ceilings.get(key)
        if got is None:
            fails.append(f"ratchet {key}: the baseline freezes a (stage, strand) the tree no longer "
                         f"produces — a stale ceiling nothing can falsify. Re-record it.")
            continue
        if want is None:
            fails.append(f"ratchet {key}: measured {got['dist']} points from budget and the baseline "
                         f"has no ceiling for it — a stage cannot arrive unmeasured")
            continue
        ceiling = float(want.get("dist", 0.0))
        if got["dist"] > ceiling + EPS:
            grew.append(f"{key}: {ceiling} -> {got['dist']}")
            fails.append(f"ratchet {key}: the stage moved FURTHER from R78's budget of "
                         f"{BUDGET[key.split('|')[1]]}% — {ceiling} points off, now {got['dist']} "
                         f"({got['pct']}%, {got['n']} components)")
        elif got["dist"] < ceiling - EPS:
            shrank.append(f"{key}: {ceiling} -> {got['dist']}")

    frozen_stale = base.get("stale_histograms") if isinstance(base, dict) else None
    if frozen_stale is None:
        fails.append(f"{baseline_path.name} freezes no `stale_histograms` count — record it")
    elif stale_histograms > int(frozen_stale):
        fails.append(f"ratchet stale_histograms: {frozen_stale} -> {stale_histograms}. More units now "
                     f"ship a `strand_counts` that disagrees with the components they hold.")
    elif stale_histograms < int(frozen_stale):
        shrank.append(f"stale_histograms: {frozen_stale} -> {stale_histograms}")

    # ---- report -----------------------------------------------------------------------------------
    total = sum(path_wide.values()) or 1
    print(f"  [adv]  budget (R78) {'/'.join(str(BUDGET[s]) for s in STRANDS)} ±{TOLERANCE:g}; "
          f"path-wide "
          f"{'/'.join(f'{100 * path_wide[s] / total:.1f}' for s in STRANDS)} over {total} components")
    for stage in per_stage:
        cells = " ".join(f"{observed[f'{stage}|{s}']['pct']:5.1f}" for s in STRANDS)
        dists = [observed[f"{stage}|{s}"]["dist"] for s in STRANDS]
        oob = sum(1 for d in dists if d > TOLERANCE)
        print(f"  [adv]  {stage:15} {cells}   worst {max(dists):4.1f} pt, {oob}/4 strands out of band")
    if in_band:
        print(f"  [adv]  IN BAND on all four strands: {', '.join(in_band)} — R78 can gate these hard "
              f"and their ratchet rows can go")
    print(f"  [adv]  {stale_histograms} of {len(units)} units ship a stale `strand_counts` "
          f"(build_speaking_practice.py counts checkpoints it runs before)")
    if shrank:
        print("\n  RATCHET SHRANK — lower these ceilings with --record:")
        for line in shrank[:MAX_REPORT]:
            print(f"    {line}")
    for line in (fails if args.list else fails[:MAX_REPORT]):
        print(f"  [FAIL] {line}")
    if not args.list and len(fails) > MAX_REPORT:
        print(f"  [FAIL] … and {len(fails) - MAX_REPORT} more (re-run with --list)")
    print(f"validate_speak_strands: {len(per_stage)} stages, {len(units)} units, {total} components, "
          f"{len(per_stage) - len(in_band)}/{len(per_stage)} stages out of band, {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
