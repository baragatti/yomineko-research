#!/usr/bin/env python3
"""Single validation gate — runs the whole validator suite and fails if any HARD check fails.

Run this before every commit and from CI. HARD validators gate the build (exit non-zero on failure); ADVISORY
validators run + report but never block (their findings are reviewed by a human). Usage:
  validate_all.py            # run everything
  validate_all.py --quiet    # only the summary table
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
HERE = Path(__file__).resolve().parent
PY = Path(sys.executable)
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

# (script, mode) — mode: "code" gate on exit code, "grep-fail" gate if output has [FAIL], "advisory" never gates
SUITE = [
    ("validate_lessons.py", "code"),
    ("integrity_audit.py", "code"),
    ("audit_coverage.py", "code"),
    ("audit_manifest.py", "code"),
    ("audit_export_refs.py", "code"),
    ("audit_lesson_hygiene.py", "code"),
    ("graph_queries.py", "grep-fail"),
    ("validate.py", "code"),
    ("completeness_audit.py", "advisory"),
    ("detect_ai_tells.py", "advisory"),
]


def _summary(out: str) -> str:
    lines = [ln for ln in out.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if re.search(r"(audit:|validated|FAIL|PASS|flagged|0 FAIL|checked)", ln):
            return ln.strip()[:100]
    return lines[-1].strip()[:100] if lines else ""


def main() -> int:
    quiet = "--quiet" in sys.argv
    rows = []
    hard_fail = False
    for script, mode in SUITE:
        p = subprocess.run([str(PY), str(HERE / script)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=ENV)
        out = (p.stdout or "") + (p.returncode and ("\n" + (p.stderr or "")) or "")
        if mode == "code":
            ok = p.returncode == 0
        elif mode == "grep-fail":
            ok = "[FAIL]" not in out and "=== " + "0 FAIL" not in out  # PASS lines only
            ok = "[FAIL]" not in out
        else:  # advisory
            ok = None
        status = "OK " if ok else ("FAIL" if ok is False else "info")
        if ok is False and mode != "advisory":
            hard_fail = True
        rows.append((status, script, _summary(out)))
        if not quiet and p.returncode != 0 and mode != "advisory":
            print(p.stdout)
            if p.stderr:
                print(p.stderr)
    print("\n================ VALIDATION GATE ================")
    for status, script, summ in rows:
        print(f"  [{status}] {script:24} {summ}")
    print("================================================")
    if hard_fail:
        print("RESULT: ❌ GATE FAILED (a hard validator failed)")
        return 1
    print("RESULT: ✅ ALL HARD VALIDATORS PASS (advisory items are human-reviewed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
