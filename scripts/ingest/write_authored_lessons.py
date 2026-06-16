#!/usr/bin/env python3
"""Write authored lesson records from an authoring-workflow .output into research/derived/lessons/*.json.

The workflow returns an array of lesson records (the canonical authoring shape). This unwraps the result and
writes each by slug, so load_lessons.py can pick them up. Usage:
  write_authored_lessons.py <workflow.output>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
OUTDIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"


def main() -> int:
    d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    recs = d.get("result", d) if isinstance(d, dict) else d
    if isinstance(recs, str):
        recs = json.loads(recs)
    # plan+author workflows return {plan, lessons}; bare authoring workflows return a list
    if isinstance(recs, dict) and isinstance(recs.get("lessons"), list):
        recs = recs["lessons"]
    # multi-topic workflows return a list of {tail, plan, lessons} — flatten to lesson records
    if isinstance(recs, list):
        flat = []
        for r in recs:
            if isinstance(r, dict) and isinstance(r.get("lessons"), list):
                flat.extend(r["lessons"])
            else:
                flat.append(r)
        recs = flat
    OUTDIR.mkdir(parents=True, exist_ok=True)
    wrote = 0
    for rec in recs:
        if not isinstance(rec, dict) or "slug" not in rec:
            continue
        fname = rec["slug"].split(":", 1)[1] + ".json"
        (OUTDIR / fname).write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        wrote += 1
    print(f"wrote {wrote} lesson records -> {OUTDIR.relative_to(Path(__file__).resolve().parents[2])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
