#!/usr/bin/env python3
"""W34 / readiness G11 — R83's scenario spiral over `course/speak/`, as a gate.

THE RULE, VERBATIM (design/learning_science.md §2.13):

    R83 [enforceable] DO spiral the scenarios: every stage 1-6 seed lexicon must reappear in at least
    one stage 7-12 unit.

    *Why:* the 12 stages are currently visited once each, so `arrival` is learned in week one and
    never retrieved again, which violates the spacing rule the course already holds. Marugoto's 15
    recurring topics are the reference implementation.

WHAT "REAPPEAR" IS MEASURED OVER, AND WHY THE ANSWER IS THREE NUMBERS
----------------------------------------------------------------------
A late unit can re-present early material in three places, and they are not worth the same to the
learner, so they are counted and frozen separately rather than summed:

  * `say_now`   — the phrases the learner is told to say in this unit. 216 slots across stages 7-12.
  * `fluency`   — R79's already-known retrieval block. 216 slots.
  * `drills`    — R80's pattern examples: 468 example slots. A phrase here is evidence for a GRAMMAR
                  point and the learner reads it; it is the weakest of the three and it is the only
                  one `arrival` scores on.

Summing them would hide exactly the thing G11 found. `arrival` — greetings, thanks, apologies, the
most reusable lexicon on the path — reaches **0 of 216 late `say_now` slots and 0 of 216 late
`fluency` slots**, and appears only as 11 drill examples. Read as one total it looks like coverage;
read per surface it is the failure R83 was written to stop.

A seed "reappears" under the builder's own scenario-match rule (`speak_path_common.seed_hit`,
`design/speaking_path.md` §3.2: whole-token LEMMA, or substring for seeds of 4+ characters), applied
to the export. That rule is not retyped here — the seed lexicons come out of
`scripts/export/build_speaking_path.py::STAGES`, because §5 of the design says they live in the
builder so they stay executable rather than drifting from the prose.

WHAT GATES HARD, TODAY
-----------------------
R83's literal clause: every early stage's seed lexicon must reach **at least one** late unit, on any
surface. All six do (`lodging` is the thinnest at 5 late units), so this gates without failing —
which is the point of writing it down: the rule has been in the file unenforced, and the first
regeneration that drops a stage out of the late path now fails instead of shipping.

Floors reject a vanished tree: fewer than 4 early stages, 4 late stages, 100 late `say_now` slots or
100 late `fluency` slots is a path that was moved or shadowed, and an empty denominator would make
every count vacuously "not decreased".

WHAT IS RATCHETED — AND THE POLARITY IS INVERTED
-------------------------------------------------
The other two W34 gates freeze DEBT and fail on growth. This one freezes REACH, so it is a floor:
`speak_spiral_baseline.json` holds today's per-(early stage, surface) counts and **a decrease is a
hard failure**. An increase prints "raise the floor" — the same discipline, pointing the other way.
The frozen denominators are checked too: a count that holds while the denominator shrinks is not the
same reach, so a shrunk denominator fails as well.

FALSIFIABILITY (2026-09-02, five plants on a copied tree, all caught)
---------------------------------------------------------------------
Fixture as in `validate_speak_strands.py`: the COPIED validator run with `--root <fixture>`, so the
seed lexicons and the baseline resolve inside the fixture and never back into the real repo. The
unmutated copy reports 0 FAIL.

  one late say_now carrying a shopping seed swapped
  for a seedless phrase (denominator unchanged)     -> ratchet shopping|say_now: the spiral SHRANK,
                                                       11 -> 10
  every arrival-seeded drill example pulled out of
  stages 7-12                                       -> R83: stage arrival's seed lexicon reaches
                                                       ZERO of the 36 late-stage units
  one late say_now slot deleted                     -> late-stage say_now slots shrank 216 -> 215,
                                                       the counts are not comparable
  corpus/sentences emptied                          -> empty sentence bank, 1 FAIL (every seed match
                                                       would otherwise be vacuously false)
  baseline floors emptied                           -> 7 FAIL: nothing frozen, nothing falsifiable

Reads exported JSON only; never db/corpus.sqlite.
Usage: validate_speak_spiral.py [--root PATH] [--record] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from speak_path_common import (  # noqa: E402
    REPO, iter_units, jload, load_course, load_sentences, seed_hit, stage_seeds,
)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

BASELINE = Path(__file__).resolve().parent / "speak_spiral_baseline.json"
MAX_REPORT = 20

# R83 names stages 1-6 and 7-12 by ordinal; the split is read off `course.json`'s own stage `order`
# so a path with a different stage count still splits where the rule says it does.
EARLY_MAX = 6
SURFACES = ("say_now", "fluency", "drills")

FLOOR_EARLY, FLOOR_LATE = 4, 4
FLOOR_LATE_SLOTS = {"say_now": 100, "fluency": 100, "drills": 100}

NOTE = ("W34 ratchet (readiness G11), INVERTED POLARITY. Per (early stage, surface): the number of "
        "late-stage (7-12) slots carrying one of that stage's seeds. This is REACH, not debt, so it "
        "is a FLOOR: a decrease is a hard failure and an increase asks for the floor to be raised. "
        "`denominators` freezes the late-slot counts the reach is measured against, because a count "
        "that holds while its denominator shrinks is not the same reach. Re-record with --record "
        "only after deliberately reseeding the late stages, never to silence a failure. Retired when "
        "every early stage reaches the late path on say_now and fluency, not only on drills.")


def main() -> int:
    ap = argparse.ArgumentParser(description="R83 scenario spiral across the speaking path")
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--record", action="store_true",
                    help="re-freeze the ratchet after a DELIBERATE reseed; never to hide a failure")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 20")
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
        print("validate_speak_spiral: the speaking path could not be read — 1 FAIL")
        return 1

    sentences = load_sentences(root)
    if not sentences:
        print("  [FAIL] corpus/sentences holds no sentences — the seed match would be vacuously false")
        print("validate_speak_spiral: empty sentence bank — 1 FAIL")
        return 1
    seeds = stage_seeds()

    early = [s for s in {r["stage"]: r["order"] for r in units}.items() if s[1] <= EARLY_MAX]
    early_stages = [s for s, _ in sorted(early, key=lambda x: x[1])]
    late_units = [r for r in units if r["order"] > EARLY_MAX]
    late_stages = sorted({r["stage"] for r in late_units})

    for s in early_stages:
        if s not in seeds:
            fails.append(f"{s}: the builder's STAGES table declares no seed lexicon for this stage, "
                         f"so R83 has nothing to look for")
    if len(early_stages) < FLOOR_EARLY:
        fails.append(f"{len(early_stages)} early stages (order ≤ {EARLY_MAX}), floor is {FLOOR_EARLY}")
    if len(late_stages) < FLOOR_LATE:
        fails.append(f"{len(late_stages)} late stages (order > {EARLY_MAX}), floor is {FLOOR_LATE}")

    # ---- denominators: the late slots the reach is measured against -------------------------------
    den = {k: 0 for k in SURFACES}
    for r in late_units:
        u = r["unit"]
        den["say_now"] += len(u.get("say_now") or [])
        den["fluency"] += len((u.get("fluency") or {}).get("items", []))
        den["drills"] += sum(len(d.get("examples") or []) for d in (u.get("drills") or []))
    for k, floor in FLOOR_LATE_SLOTS.items():
        if den[k] < floor:
            fails.append(f"{den[k]} late-stage {k} slots, floor is {floor} — with no slots every "
                         f"reach count is vacuously unchanged")

    # ---- the measurement ---------------------------------------------------------------------------
    observed: dict[str, dict] = {}
    for stage in early_stages:
        terms = seeds.get(stage, ())
        cnt = {k: 0 for k in SURFACES}
        hit_units: set[str] = set()
        for r in late_units:
            u = r["unit"]
            before = dict(cnt)
            for ref in u.get("say_now") or []:
                if seed_hit(sentences.get(ref), terms):
                    cnt["say_now"] += 1
            for ref in (u.get("fluency") or {}).get("items", []):
                if seed_hit(sentences.get(ref), terms):
                    cnt["fluency"] += 1
            for d in u.get("drills") or []:
                for ref in d.get("examples") or []:
                    if seed_hit(sentences.get(ref), terms):
                        cnt["drills"] += 1
            if cnt != before:
                hit_units.add(r["id"])
        observed[stage] = {**cnt, "late_units": len(hit_units)}
        # R83's own clause, verbatim: "must reappear in at least one stage 7-12 unit".
        if not hit_units:
            fails.append(f"R83: stage {stage}'s seed lexicon reaches ZERO of the {len(late_units)} "
                         f"late-stage units — it is taught once and never retrieved")

    # ---- the ratchet (a FLOOR: reach may not shrink) ------------------------------------------------
    if args.record:
        payload = {"note": NOTE, "early_max": EARLY_MAX, "denominators": den,
                   "floors": {k: observed[k] for k in sorted(observed)}}
        baseline_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"recorded reach floors for {len(observed)} early stages against {den} "
              f"-> {baseline_path.name}")
        return 0

    base = jload(baseline_path) if baseline_path.exists() else {}
    floors = base.get("floors", {}) if isinstance(base, dict) else {}
    frozen_den = base.get("denominators", {}) if isinstance(base, dict) else {}
    if not floors:
        fails.append(f"{baseline_path.name} holds no floors — a ratchet with nothing frozen in it "
                     f"cannot fail on a regression. Record it with --record.")
    for k in SURFACES:
        was = frozen_den.get(k)
        if was is None:
            fails.append(f"{baseline_path.name} freezes no denominator for {k} — record it")
        elif den[k] < int(was):
            fails.append(f"late-stage {k} slots shrank {was} -> {den[k]}: the reach counts below are "
                         f"measured against a smaller path and are not comparable")

    rose: list[str] = []
    for stage in sorted(set(observed) | set(floors)):
        got, want = observed.get(stage), floors.get(stage)
        if got is None:
            fails.append(f"ratchet {stage}: the baseline freezes an early stage this tree no longer "
                         f"has — a stale floor nothing can falsify. Re-record it.")
            continue
        if want is None:
            fails.append(f"ratchet {stage}: an early stage with no frozen reach — a stage cannot "
                         f"arrive unmeasured")
            continue
        for k in (*SURFACES, "late_units"):
            now, floor = got[k], int(want.get(k, 0))
            if now < floor:
                fails.append(f"ratchet {stage}|{k}: the spiral SHRANK, {floor} -> {now}. Early "
                             f"material is being retrieved less often in stages 7-12, which is the "
                             f"regression R83 exists to catch.")
            elif now > floor:
                rose.append(f"{stage}|{k}: {floor} -> {now}")

    # ---- report --------------------------------------------------------------------------------------
    print(f"  [adv]  late stages {', '.join(late_stages)} — {len(late_units)} units, "
          f"{den['say_now']} say_now / {den['fluency']} fluency / {den['drills']} drill slots")
    print(f"  [adv]  {'early stage':16}{'say_now':>9}{'fluency':>9}{'drills':>9}{'late units':>12}")
    for stage in early_stages:
        o = observed[stage]
        print(f"  [adv]  {stage:16}{o['say_now']:9}{o['fluency']:9}{o['drills']:9}"
              f"{o['late_units']:12}")
    dead = [s for s in early_stages
            if observed[s]["say_now"] == 0 and observed[s]["fluency"] == 0]
    if dead:
        print(f"  [adv]  reaches the late path ONLY through drill examples, never as a phrase the "
              f"learner says or retrieves: {', '.join(dead)}")
    if rose:
        print("\n  RATCHET ROSE — raise these floors with --record:")
        for line in rose[:MAX_REPORT]:
            print(f"    {line}")
    for line in (fails if args.list else fails[:MAX_REPORT]):
        print(f"  [FAIL] {line}")
    if not args.list and len(fails) > MAX_REPORT:
        print(f"  [FAIL] … and {len(fails) - MAX_REPORT} more (re-run with --list)")
    print(f"validate_speak_spiral: {len(early_stages)} early stages spiralled into {len(late_units)} "
          f"late units, {len(dead)} reaching phrase slots not at all, {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
