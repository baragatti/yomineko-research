#!/usr/bin/env python3
"""P7/P8 — strip over-escaped backslash-quote artifacts (\\") from authored lesson string fields.

Some author agents emitted quoted phrases as \\"...\\" in their structured output, so the stored string literally
contains backslash-quote — which renders stray backslashes to the learner (e.g. \\"de contagem\\"). pt-BR and
Japanese learner text never legitimately contain a backslash, so this walks every string field of each lesson and
replaces backslash-quote with a plain quote (and reports any other stray backslash for manual review). Idempotent.
Run before load/validate. Usage:
  fix_escape_artifacts.py            # all research/derived/lessons/*.json
  fix_escape_artifacts.py <slug...>  # only the named lessons
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LESSON_DIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"
BS = chr(92)  # backslash


def _walk(obj, stats):
    if isinstance(obj, str):
        fixed = obj.replace(BS + '"', '"')
        stats["fixed"] += obj.count(BS + '"')
        stray = fixed.count(BS)
        if stray:
            stats["stray"] += stray
        return fixed
    if isinstance(obj, list):
        return [_walk(x, stats) for x in obj]
    if isinstance(obj, dict):
        return {k: _walk(v, stats) for k, v in obj.items()}
    return obj


def main() -> int:
    if len(sys.argv) > 1:
        files = [LESSON_DIR / ((a.split(":", 1)[1] if ":" in a else a) + ".json") for a in sys.argv[1:]]
    else:
        files = sorted(LESSON_DIR.glob("*.json"))
    total = 0
    touched = 0
    stray_files = []
    for f in files:
        if not f.exists():
            print(f"  skip (missing) {f.name}")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        stats = {"fixed": 0, "stray": 0}
        nd = _walk(d, stats)
        if stats["fixed"]:
            f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            total += stats["fixed"]
            touched += 1
        if stats["stray"]:
            stray_files.append((f.name, stats["stray"]))
    print(f"removed {total} backslash-quote artifact(s) across {touched} file(s)")
    if stray_files:
        print("  WARN remaining stray backslashes (manual review):")
        for name, n in stray_files:
            print(f"    {name}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
