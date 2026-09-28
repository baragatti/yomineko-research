#!/usr/bin/env python3
"""W34 strand rebalance: record, per speaking unit, what the per-stage caps changed.

The durable form of W34 is the builder rule (`scripts/export/build_speaking_practice.py` reads
`caps` from `research/derived/repairs/w34_rebalance.json`). This script derives the table's ROWS: it
compares a snapshot of `course/speak/` built at the pre-W34 caps (3/6, `--before`) with the current
`course/speak/` built at the table's caps, and writes one row per unit with the exact production and
fluency lists the export must carry, plus the moves (add_production, swap_fluency_to_production,
add_fluency, drop_fluency). `validate_repairs_applied.py` (handle_w34_rebalance) exact-matches the
rows against the export. Idempotent: same inputs, same bytes. Refuses when a pre-W34 production
list is not a prefix of the new one (the selection order must not move).

Usage: derive_w34_rebalance.py --before <dir holding a pre-W34 course/speak copy> [--head <sha>]
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "research" / "derived" / "repairs" / "w34_rebalance.json"
SPEAK = ROOT / "course" / "speak"


def units(speak: Path) -> list[tuple[str, str, dict]]:
    course = json.loads((speak / "course.json").read_text(encoding="utf-8"))
    out = []
    for stage in course["stages"]:
        key = stage["slug"].split(":", 1)[1]
        for uid in stage["unit_ids"]:
            n = int(uid.rsplit("-", 1)[1])
            out.append((uid, key, json.loads((speak / key / f"unit-{n:02d}.json").read_text(encoding="utf-8"))))
    return out


def lists(u: dict) -> tuple[list[str], list[str]]:
    return [x["sentence"] for x in u.get("production") or []], list((u.get("fluency") or {}).get("items") or [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--head", default="")
    args = ap.parse_args()
    table = json.loads(TABLE.read_text(encoding="utf-8"))
    before = {uid: lists(u) for uid, _k, u in units(args.before)}
    rows, counts = [], Counter()
    for uid, key, u in units(SPEAK):
        bp, bf = before[uid]
        ap_, af = lists(u)
        if ap_[:len(bp)] != bp:
            sys.exit(f"{uid}: the pre-W34 production list is not a prefix of the new one")
        moves = []
        for s in ap_[len(bp):]:
            moves.append({"op": "swap_fluency_to_production" if s in bf else "add_production", "sentence": s})
        moves += [{"op": "add_fluency", "sentence": s} for s in af if s not in bf]
        moves += [{"op": "drop_fluency", "sentence": s} for s in bf if s not in af and s not in ap_]
        counts.update(m["op"] for m in moves)
        rows.append({"unit": uid, "stage": key, "production": ap_, "fluency": af,
                     "before": {"production": bp, "fluency": bf}, "moves": moves})
    b_prod = sum(len(v[0]) for v in before.values())
    b_flu = sum(len(v[1]) for v in before.values())
    doc = {
        "id": "w34_rebalance",
        "created": table.get("created", "2026-09-23"),
        "re_derived": "2026-09-27",
        "layer": "C",
        "needs_review": True,
        "authored_items": 0,
        "source": {
            "plan": "research/reports/w34_rebalance_plan.md (measured at f9de8e2c, before the W32 ingest)",
            "re_derived_on": args.head or table.get("source", {}).get("re_derived_on", ""),
            "script": "scripts/derive_w34_rebalance.py",
        },
        "builder_rule": {
            "file": "scripts/export/build_speaking_practice.py",
            "change": ("Per-stage caps (`caps`) replace the flat 3/6. Selection order is unchanged, so the "
                       "pre-W34 production items stay a prefix. Floor rule: production grows toward its "
                       "stage cap only while the fluency block keeps the item count it has at 3/6."),
        },
        "caps": table["caps"],
        "caps_rule": table.get("caps_rule", ""),
        "caps_plan_2026_09_23": table.get("caps_plan_2026_09_23", {}),
        "course_totals": {"before": {"production": b_prod, "fluency": b_flu},
                          "after": {"production": sum(len(r["production"]) for r in rows),
                                    "fluency": sum(len(r["fluency"]) for r in rows)}},
        "move_counts": dict(sorted(counts.items())),
        "row_count": len(rows),
        "rows": rows,
    }
    TABLE.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"w34_rebalance: {len(rows)} units, moves {dict(sorted(counts.items()))}, "
          f"production {b_prod} -> {doc['course_totals']['after']['production']}, "
          f"fluency {b_flu} -> {doc['course_totals']['after']['fluency']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
