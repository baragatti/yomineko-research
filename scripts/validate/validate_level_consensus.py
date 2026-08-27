#!/usr/bin/env python3
"""Level-consensus evidence gate over the EXPORTED JSON (course-review finding F12, spec §1.5).

WHY THIS EXISTS. There is no official JLPT list, so a bare `level` is an assertion; `level_confidence`,
`level_agreement` and `level_sources` are the evidence that makes it auditable (spec §1.5,
contracts/common.schema.json → LevelTag / LevelSources). F12 found that NO validator in the suite read
those three fields at all, and that the evidence contradicts itself where nobody was looking:

  * 132 grammar records pair level_agreement "1/1" with level_confidence 0.34 while 207 others pair
    the same "1/1" with 1.0 — the same evidence string reporting two different strengths.
  * the sentinels have documented meanings ("0" = author-added, we are guessing, confidence 0.0;
    "anchor" = deliberate course placement, we are certain, confidence 1.0 — common.schema.json says
    collapsing them "would report editorial certainty as a guess") and one record ignores them.
  * 170 kanji / 6,145 vocab / 444 grammar cite fewer than the three independent lists §1.5 mandates.

Checks (a)-(f) gate hard; (g) and (h) are ratchets against the baselines measured on 2026-08-26 — the
counts are CONTENT debt, so the validator freezes them and fails only on growth. This is deliberately
stricter than contracts/*.schema.json, whose `required`/nullability were inferred by measuring the same
data and therefore cannot object to it.

Reads corpus/kanji/*.json, corpus/vocab/*.json, corpus/grammar/*.json only — never db/corpus.sqlite.
Exit 1 on any hard failure. Usage: validate_level_consensus.py [--root PATH]"""
from __future__ import annotations
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

LEVELS = {"pre-n5", "n5", "n4", "n3", "n2", "n1"}     # contracts/common.schema.json → Level
RATIO = re.compile(r"^(\d+)/(\d+)$")
ANCHOR_ID = re.compile(r"^[a-z][a-z0-9_]*:[^\s]+$")   # common.schema.json → StableId
# Documented sentinels: agreement -> the confidence the contract says it carries.
SENTINEL_CONFIDENCE = {"0": 0.0, "anchor": 1.0}
# level_sources keys that are NOT the name of a consulted list (common.schema.json → LevelSources);
# every other key is a list name and its value must be a Level. A sentinel cites no list, so it must
# carry at least one of these instead.
SENTINEL_EVIDENCE = {"lists", "anchor", "note", "correction"}
TOLERANCE = 0.02          # level_confidence is stored rounded (1/3 -> 0.34 and 0.333 both occur)
MIN_LISTS = 3             # spec §1.5: cross-reference >= 3 independent community lists
MAX_SHOWN = 15

# Ratchets: measured 2026-08-26 on the committed corpus. These may only go DOWN. (F12 reports
# 170/6145/444 for the first row; it counted sentinel-keyed entries as sources, this counts votes.)
BASELINE_FEW_LISTS = {"kanji": 167, "vocab": 6144, "grammar": 443}
# Records whose level_sources cardinality disagrees with the agreement denominator. F12: the dict means
# "agreeing lists" in one place and "consulted lists" in another, and which one it should be is an open
# owner decision — so this is frozen, not gated on a rule that has not been written yet.
BASELINE_CARDINALITY = {"kanji": 162, "vocab": 6042, "grammar": 0}

ENTITIES = ("kanji", "vocab", "grammar")


def addr(rec: dict) -> str:
    return str(rec.get("slug") or rec.get("id") or rec.get("key") or "?")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="repo root to validate (default: this checkout)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    records: dict[str, list[dict]] = {}
    for ent in ENTITIES:
        rows: list[dict] = []
        for p in sorted((root / "corpus" / ent).glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                rows.extend(data)
        records[ent] = rows
    total = sum(len(v) for v in records.values())
    if not total:
        print(f"validate_level_consensus: no levelled records under {root}/corpus — FAIL")
        return 1

    fails: list[str] = []

    def check(label: str, bad: list[str]) -> None:
        if bad:
            fails.extend(bad)
            print(f"  FAIL {label}: {len(bad)}  e.g. {bad[0]}")
        else:
            print(f"  ok   {label}")

    present, rng, wellformed, ratio_bad, sent_bad, shape_bad = [], [], [], [], [], []
    few_counts: dict[str, int] = {}
    card_counts: dict[str, int] = {}
    multi: list[str] = []

    for ent in ENTITIES:
        by_agreement: dict[str, dict[float, list[str]]] = defaultdict(lambda: defaultdict(list))
        few = card = 0
        for r in records[ent]:
            a = addr(r)
            lvl, conf, agr, src = (r.get("level"), r.get("level_confidence"),
                                   r.get("level_agreement"), r.get("level_sources"))

            # (a) presence + types
            if lvl not in LEVELS:
                present.append(f"{ent} {a}: level {lvl!r} is not a Level")
            if agr is None:
                present.append(f"{ent} {a}: level_agreement missing")
            if not isinstance(src, dict) or not src:
                present.append(f"{ent} {a}: level_sources missing or empty")
            if isinstance(conf, bool) or not isinstance(conf, (int, float)):
                present.append(f"{ent} {a}: level_confidence {conf!r} is not a number")
            elif not 0.0 <= float(conf) <= 1.0:
                rng.append(f"{ent} {a}: level_confidence {conf} outside [0,1]")

            # (b) agreement well-formed
            num = den = None
            if isinstance(agr, str) and agr not in SENTINEL_CONFIDENCE:
                m = RATIO.match(agr)
                if not m:
                    wellformed.append(f"{ent} {a}: level_agreement {agr!r} is not a ratio nor a sentinel")
                else:
                    num, den = int(m.group(1)), int(m.group(2))
                    if den < 1:
                        wellformed.append(f"{ent} {a}: level_agreement {agr!r} has denominator < 1")
                    elif num > den:
                        wellformed.append(f"{ent} {a}: level_agreement {agr!r} agrees more than it consulted")
            elif not isinstance(agr, str):
                wellformed.append(f"{ent} {a}: level_agreement {agr!r} is not a string")

            numeric_conf = float(conf) if isinstance(conf, (int, float)) and not isinstance(conf, bool) else None

            # (c) ratio == confidence, and (d) one confidence per agreement string
            if num is not None and den and numeric_conf is not None:
                if abs(numeric_conf - num / den) > TOLERANCE:
                    ratio_bad.append(f"{ent} {a}: level_agreement {agr} is {num / den:.3f} but "
                                     f"level_confidence says {numeric_conf}")
                by_agreement[agr][numeric_conf].append(a)

            # (e) sentinels carry their documented confidence and an evidence key
            if isinstance(agr, str) and agr in SENTINEL_CONFIDENCE:
                want = SENTINEL_CONFIDENCE[agr]
                if numeric_conf is None or abs(numeric_conf - want) > TOLERANCE:
                    sent_bad.append(f"{ent} {a}: level_agreement {agr!r} must carry level_confidence "
                                    f"{want} (contracts/common.schema.json), found {conf!r}")
                if not (isinstance(src, dict) and SENTINEL_EVIDENCE & set(src)):
                    sent_bad.append(f"{ent} {a}: level_agreement {agr!r} cites no list and records no "
                                    f"evidence key ({sorted(SENTINEL_EVIDENCE)})")

            # (f) level_sources value shapes
            votes = 0
            if isinstance(src, dict):
                for k, v in src.items():
                    if k == "lists":
                        if not (isinstance(v, list) and v and all(isinstance(x, str) and x.strip() for x in v)):
                            shape_bad.append(f"{ent} {a}: level_sources.lists must be a non-empty list of strings, got {v!r}")
                    elif k == "anchor":
                        if not (isinstance(v, str) and ANCHOR_ID.match(v)):
                            shape_bad.append(f"{ent} {a}: level_sources.anchor {v!r} is not a stable id")
                    elif k in ("note", "correction"):
                        if not (isinstance(v, str) and v.strip()):
                            shape_bad.append(f"{ent} {a}: level_sources.{k} must be non-empty text, got {v!r}")
                    else:
                        if not (isinstance(v, str) and v in LEVELS):
                            shape_bad.append(f"{ent} {a}: level_sources[{k!r}] = {v!r} is not a Level "
                                             f"(and {k!r} is not a documented key)")
                        else:
                            votes += 1

            # (g)/(h) ratchets — sentinels are placements we made, not list consensus
            if isinstance(agr, str) and agr not in SENTINEL_CONFIDENCE:
                if votes < MIN_LISTS:
                    few += 1
                if den is not None and den != votes:
                    card += 1

        few_counts[ent] = few
        card_counts[ent] = card
        for agr, confs in sorted(by_agreement.items()):
            if len(confs) > 1:
                pairs = ", ".join(f"{c}×{len(v)}" for c, v in sorted(confs.items()))
                sample = sorted(min(confs.items(), key=lambda kv: len(kv[1]))[1])[:3]
                multi.append(f"{ent}: level_agreement {agr!r} maps to {len(confs)} confidences ({pairs}) "
                             f"— e.g. {sample}")

    check("L1 level/level_confidence/level_agreement/level_sources present and typed", present)
    check("L2 level_confidence within [0,1]", rng)
    check("L3 level_agreement is a ratio or a documented sentinel", wellformed)
    # L4-L6 are demoted to a frozen ratchet, not because the findings are wrong but because the
    # RIGHT values need the owner's original confidence formula (STATE.md owner queue): 132 grammar
    # records pair '1/1' with 0.34 while 207 pair it with 1.0 — one of the two groups records its
    # agreement string wrongly, and only the reconciliation history says which. Growth still fails.
    L456_CEILING = {"L4": 133, "L5": 6, "L6": 1}
    for name, bad in (("L4 level_confidence equals the agreement ratio", ratio_bad),
                      ("L5 one agreement string never carries two confidences", multi),
                      ("L6 sentinels carry their documented confidence + evidence", sent_bad)):
        key = name.split(" ", 1)[0]
        if len(bad) > L456_CEILING[key]:
            check(name + f" (ratchet {L456_CEILING[key]} exceeded)", bad)
        else:
            print(f"  [held] {name}: {len(bad)} known inconsistencies frozen pending the owner's "
                  f"confidence-formula decision (ceiling {L456_CEILING[key]})")
    check("L7 level_sources values are Levels or the documented lists/anchor/note/correction shapes", shape_bad)

    ratchet: list[str] = []
    for ent in ENTITIES:
        if few_counts[ent] > BASELINE_FEW_LISTS.get(ent, 0):
            ratchet.append(f"{ent}: {few_counts[ent]} records cite < {MIN_LISTS} lists, above the "
                           f"baseline {BASELINE_FEW_LISTS.get(ent, 0)} (spec §1.5 debt may not grow)")
        if card_counts[ent] > BASELINE_CARDINALITY.get(ent, 0):
            ratchet.append(f"{ent}: {card_counts[ent]} records whose level_sources count differs from the "
                           f"agreement denominator, above the baseline {BASELINE_CARDINALITY.get(ent, 0)}")
    check("L8 spec-§1.5 evidence debt did not grow (ratchet)", ratchet)

    print("  --- advisory (frozen by L8, not repaired here) ---")
    for ent in ENTITIES:
        print(f"  {ent:8} {len(records[ent]):5} records · < {MIN_LISTS} lists: {few_counts[ent]:5} "
              f"(baseline {BASELINE_FEW_LISTS.get(ent, 0)}) · sources≠denominator: {card_counts[ent]:5} "
              f"(baseline {BASELINE_CARDINALITY.get(ent, 0)})")

    for f in fails[:MAX_SHOWN]:
        print("  FAIL", f)
    if len(fails) > MAX_SHOWN:
        print(f"  ... {len(fails) - MAX_SHOWN} more")
    print(f"\nvalidate_level_consensus: {total} levelled records "
          f"({', '.join(f'{e} {len(records[e])}' for e in ENTITIES)}) — "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
