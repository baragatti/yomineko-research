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
    ("validate_readings.py", "code"),
    ("validate_display_consistency.py", "code"),
    ("validate_groundtruth.py", "code"),
    ("validate_strokes.py", "code"),
    ("integrity_audit.py", "code"),
    ("audit_coverage.py", "code"),
    ("audit_jlpt_coverage.py", "code"),
    ("validate_exam_banks.py", "code"),
    ("validate_conjugation_exercises.py", "code"),
    ("validate_role_exercises.py", "code"),
    ("validate_sentence_structure.py", "code"),
    ("validate_grammar_formation.py", "code"),
    ("test_kanji_align.py", "code"),
    ("validate_kanji_reading_groups.py", "code"),
    ("validate_speaking_path.py", "code"),
    ("validate_capabilities.py", "code"),
    ("audit_manifest.py", "code"),
    ("audit_export_refs.py", "code"),
    # Schema + identity + graph conformance for every exported artifact, against contracts/*.schema.json.
    ("validate_contracts.py", "code"),
    # ---- 2026-08-27 suite build: 19 validators from the two 13-panel reviews, each landed with a
    # planted-violation proof and adversarially reviewed for cannot-fail patterns. Everything below
    # reads the EXPORTED JSON (the source of truth) unless its docstring says otherwise.
    ("validate_course_chain.py", "code"),        # manifest->course->topic->lesson tiers + catalogue
    ("validate_unlock_ledger.py", "code"),       # slug-space introduce-once + coverage + exemptions
    ("validate_lesson_bodies.py", "code"),       # markup, all ref kinds, furigana, no-markup-in-prose
    ("validate_exercise_contracts.py", "code"),  # body binding, per-type answer keys grade as rendered
    ("validate_srs_decks.py", "code"),           # deck registry + lesson-level filing + no dup cards
    ("validate_lesson_gating.py", "code"),       # item refs inside own cks; i+1 sentence ratchet
    ("validate_sentence_manifest.py", "code"),   # sentence_refs == what the body renders
    ("audit_hygiene_all_locales.py", "code"),    # every pt-BR string, corpus-wide (replaces the
                                                 # deprecated audit_lesson_hygiene.py, which read a
                                                 # stale staging dir — F5/STRUCT-08)
    ("validate_provenance_json.py", "code"),     # layer/source/ai_generated/needs_review semantics
    ("validate_stable_addresses.py", "code"),    # integer FKs always beside their published slug
    ("validate_stroke_integrity.py", "code"),    # stroke coverage + count agreement + exemptions
    ("validate_level_consensus.py", "code"),     # spec-1.5 evidence well-formedness (+L4-L6 ratchet)
    ("validate_graph_edges.py", "code"),         # 550k cross-entity edges + family/capability layers
    ("validate_prototype_sync.py", "code"),      # app/data is the current projection
    ("validate_no_client_leak.py", "code"),      # SSR-only: no corpus content in build/client
    ("validate_md_views.py", "code"),            # .md views re-render identical to their .json
    ("validate_schema_generation_is_current.py", "code"),  # contracts == regenerated contracts
    ("graph_queries.py", "code"),                # spec-1.7 queries verbatim, real pass/fail + waivers
    ("validate.py", "code"),
    ("completeness_audit.py", "advisory"),
    ("detect_ai_tells.py", "advisory"),
    # Was advisory while 49 furigana gaps were open (32 empty reading="" + 17 truncated over 7 lesson
    # records). Those are repaired, so it gates: a regression is now a hard failure.
    ("validate_furigana.py", "code"),
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
