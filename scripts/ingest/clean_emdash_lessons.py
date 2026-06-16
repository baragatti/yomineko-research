#!/usr/bin/env python3
"""P6b — strip the banned em dash (U+2014 '—') from ALL learner-text fields of authored lesson JSON.

The em dash is banned in every learner-facing string (spec / CLAUDE.md), not just the body: it also creeps into
`description`, `objectives`, and exercise `prompt`/`explanation`. This walks each lesson record recursively and
replaces every U+2014 in any string with a readable pt-BR separator (spaced -> "; ", otherwise "-"). The chōon
'ー' (U+30FC) used inside <jp>/readings is a DIFFERENT codepoint and is left untouched. Idempotent. Run after
authoring, before validate/export. Usage:
  clean_emdash_lessons.py            # all research/derived/lessons/*.json
  clean_emdash_lessons.py <slug...>  # only the named lessons
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LESSON_DIR = ROOT / "research" / "derived" / "lessons"
EM = "—"


def _clean(s: str) -> str:
    return (s.replace(f" {EM} ", "; ").replace(f" {EM}", ";")
             .replace(f"{EM} ", "; ").replace(EM, "-"))


def _walk(obj):
    """Recursively clean every string; return (new_obj, count)."""
    if isinstance(obj, str):
        new = _clean(obj)
        return new, (1 if new != obj else 0)
    if isinstance(obj, list):
        out, n = [], 0
        for x in obj:
            nx, c = _walk(x)
            out.append(nx); n += c
        return out, n
    if isinstance(obj, dict):
        out, n = {}, 0
        for k, v in obj.items():
            nv, c = _walk(v)
            out[k] = nv; n += c
        return out, n
    return obj, 0


def main() -> int:
    if len(sys.argv) > 1:
        files = [LESSON_DIR / ((a.split(":", 1)[1] if ":" in a else a) + ".json") for a in sys.argv[1:]]
    else:
        files = sorted(LESSON_DIR.glob("*.json"))
    total = 0
    touched = 0
    for f in files:
        if not f.exists():
            print(f"  skip (missing) {f.name}")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        nd, n = _walk(d)
        if n:
            f.write_text(json.dumps(nd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  {nd.get('slug', f.stem)}: cleaned {n} em-dash field(s)")
            total += n; touched += 1
    print(f"cleaned em dashes in {total} field(s) across {touched} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
