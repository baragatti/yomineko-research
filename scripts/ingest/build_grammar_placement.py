#!/usr/bin/env python3
"""P6a — assemble the durable design/grammar_placement.json from the classification + rebalance passes.

Merge order (later wins): grammar_assign_v1.json (classify + verify) -> rebalance .output (the 91 catch-all
members) -> MANUAL (stragglers the workflow missed/misplaced). Then DETERMINISTICALLY validate: full coverage
of all 364 keys, valid same-level topics, the て-form dependency gate (て-based -> topic order ≥15), and
per-topic balance. Writes the reviewable map only if clean. Usage: build_grammar_placement.py <rebalance.output>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "research" / "derived"
OUT = ROOT / "design" / "grammar_placement.json"

# Stragglers: 2 keys the classifier dropped + te-de (a て-based connector the classifier put in adjetivos@13,
# violating the て-form gate). Placed by hand into their correct topic.
MANUAL = {
    "you-ni-naru": "top:n4-experiencia",   # 〜ようになる = passar a (mudança de estado/capacidade)
    "you-ni-suru": "top:n4-volitivo",      # 〜ようにする = fazer questão de / criar o hábito (intenção)
    "te-de": "top:n5-te-form",             # て-form connective "e/por meio de" — depends on て-form (topic 15)
}


def load_result(p: str) -> dict:
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    r = d.get("result", d) if isinstance(d, dict) else d
    if isinstance(r, str):
        r = json.loads(r)
    return r


def main() -> int:
    v1 = json.loads((DERIVED / "grammar_assign_v1.json").read_text(encoding="utf-8"))
    rebal = {a["key"]: a["topic"] for a in load_result(sys.argv[1]).get("assignments", [])}
    grammar = json.loads((DERIVED / "grammar_to_place.json").read_text(encoding="utf-8"))
    topics = json.loads((DERIVED / "topics_ref.json").read_text(encoding="utf-8"))
    tlevel = {t["slug"]: t["level"] for t in topics}
    torder = {t["slug"]: t["order"] for t in topics}

    def topic_for(key):
        if key in MANUAL:
            return MANUAL[key], "manual"
        if key in rebal:
            return rebal[key], "rebalance"
        if key in v1:
            return v1[key]["topic"], "classify"
        return None, None

    recs, problems, missing = [], [], []
    for g in grammar:
        k = g["key"]
        slug, src = topic_for(k)
        if slug is None:
            missing.append(k)
            continue
        if slug not in tlevel:
            problems.append(f"{k}: invalid topic '{slug}'")
            continue
        if tlevel[slug] != g["level"]:
            problems.append(f"{k}: level mismatch (grammar {g['level']} -> {slug}@{tlevel[slug]})")
        te_dep = k.startswith("te-") or (g["pattern"] or "").lstrip("〜～").startswith("て")
        if te_dep and torder.get(slug, 99) < 15:
            problems.append(f"{k}: て-dependent before topic 15 ({slug}@{torder[slug]})")
        v1rec = v1.get(k, {})
        recs.append({"key": k, "topic": slug, "level": g["level"], "source": src,
                     "confidence": v1rec.get("confidence", ""), "reason": v1rec.get("reason", ""),
                     "prereq": v1rec.get("prereq", "")})

    cnt = Counter(x["topic"] for x in recs)
    print(f"records={len(recs)} (rebalance applied to {len(rebal)}, manual {len(MANUAL)})")
    print(f"missing keys: {len(missing)} {missing[:12]}")
    print(f"problems: {len(problems)}")
    for p in problems[:40]:
        print("  PROBLEM", p)
    print("per-topic grammar counts (flag >24):")
    for t in topics:
        c = cnt.get(t["slug"], 0)
        print(f"  {t['order']:2} {t['slug']:26} {c}{'  <== heavy' if c > 24 else ''}")
    if missing or problems:
        print("\n!! NOT writing — resolve the above first.")
        return 1
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {len(recs)} -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
