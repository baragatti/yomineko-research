#!/usr/bin/env python3
"""§9.5 golden regression runner. Asserts the generation gate (validate_generated_jp) classifies the golden set
correctly: 'good' must NOT be rejected, 'bad' MUST be rejected, 'unnatural' must NOT auto-accept (reject or
quarantine). Re-run on every gate/prompt/model change — a regression here blocks the change. Exit 1 on any miss.
Usage: run_golden.py"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from validate_generated_jp import validate_jp  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden_set.json"
# (bucket, predicate on verdict, human description)
RULES = {
    "good": (lambda v: v != "reject", "must NOT be rejected"),
    "bad": (lambda v: v == "reject", "MUST be rejected"),
    "unnatural": (lambda v: v != "accept", "must NOT auto-accept"),
}


def main() -> int:
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    miss = 0
    total = 0
    for bucket, (ok, desc) in RULES.items():
        for text in data.get(bucket, []):
            total += 1
            r = validate_jp(text)
            good = ok(r["verdict"])
            if not good:
                miss += 1
            mark = "PASS" if good else "**MISS**"
            print(f"[{mark}] {bucket:9} ({desc}) -> verdict={r['verdict']} trust={r['trust']:.2f}  {text}")
            if not good:
                for f in r["hard_fail"]:
                    print(f"          ✗ {f}")
                for w in r["warn"]:
                    print(f"          ⚠ {w}")
    acc = (total - miss) / total if total else 1.0
    print(f"\nGOLDEN: {total - miss}/{total} correct ({acc:.0%}) — {'PASS' if miss == 0 else str(miss) + ' MISCLASSIFIED'}")
    return 1 if miss else 0


if __name__ == "__main__":
    sys.exit(main())
