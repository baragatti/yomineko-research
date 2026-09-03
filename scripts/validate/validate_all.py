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

# Some validators need the PROJECT venv, not whatever interpreter launched this file. The scripts
# have said "Run with venv python" in their docstrings since P5, but this runner used sys.executable
# for all of them, so the requirement was documentation only. It bites on the Sudachi gates: the
# system 3.13 carries sudachidict_full but not sudachidict_core, and validate_generated_jp.py builds
# `dictionary.Dictionary()` (which defaults to core), so run_golden.py died with
# `ModuleNotFoundError: Package sudachidict_core does not exist` before its first assertion —
# invisible, because neither script was in the suite. Route them explicitly; a missing venv is a
# hard failure rather than a silent downgrade to an interpreter that cannot run the check.
VENV_PY = HERE.parents[1] / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
NEEDS_VENV = {"run_golden.py", "validate_generated_jp.py"}

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
    ("validate_exam_level_gate.py", "code"),   # item Japanese inside the level's taught set; ratchet
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
    ("validate_practice_coverage.py", "code"),   # every unlocked item asked by its own lesson (ratchet)
    ("validate_srs_decks.py", "code"),           # deck registry + lesson-level filing + no dup cards
    ("validate_lesson_gating.py", "code"),       # item refs inside own cks; i+1 sentence ratchet
    ("validate_sentence_manifest.py", "code"),   # sentence_refs == what the body renders
    ("audit_hygiene_all_locales.py", "code"),    # every pt-BR string, corpus-wide (replaces the
                                                 # deprecated audit_lesson_hygiene.py, which read a
                                                 # stale staging dir — F5/STRUCT-08)
    ("validate_provenance_json.py", "code"),     # layer/source/ai_generated/needs_review semantics
    # W05: the >=3-sentences-per-word / >=5-per-grammar claim, over the EXPORT, as a gate. It was
    # two advisory lines in completeness_audit.py over db/corpus.sqlite for four phases; those two
    # lines now point here. Per-(level, kind) ratchet — growth fails.
    ("validate_sentence_coverage.py", "code"),   # taught items are exemplified (ratchet)
    # W06: the approval ledger and the export agree about who approved what. Empty ledger passes;
    # a review_status no live entry justifies does not.
    ("validate_review_ledger.py", "code"),       # approvals chain, anchors live, no unjustified stamp
    # W02 (G7): replays all six tracked repair tables against the export. Clean, no ratchet; the 7
    # superseded rows carry `superseded_by` markers this validator re-proves on every run.
    ("validate_repairs_applied.py", "code"),     # every repair row's `new` is what the export carries
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
    # ---- W07 gate hygiene (2026-09-02). Two of these existed and were in no suite at all, which is
    # why nobody noticed run_golden.py could not start; both run under the project venv (NEEDS_VENV).
    ("validate_exam_stem_collisions.py", "code"),  # same printed stem, different key (ratchet at 94)
    ("run_golden.py", "code"),                     # §9.5 golden set classifies as specified
    ("validate_generated_jp.py", "code"),          # no-arg selftest: the generation gate can still run
    # ---- W01. Rebuilds the git-ignored index from the datasets + the tracked scripts and diffs the
    # re-export against what is committed, so "the DB is regenerable" stops being an untested claim.
    # --quick does the grammar family only (~2 s), which is what a per-commit gate can afford. The
    # full run — all 75 runnable manifest steps, all 787 exported files, ~90 s — is not in the suite:
    # run it before a release and whenever a step is added to the manifest (see README.md).
    ("validate_index_rebuildable.py --quick", "code"),
    # ---- W34 (readiness G4/G10/G11). Three enforceable rules over `course/speak/` that were
    # enforced by nothing: validate_speaking_path.py checks the strand histogram sums to 100 and
    # never what it sums to, and neither R83 nor anything above R86's punctuation-equality had a
    # gate at all. Each carries its own frozen baseline beside this file and its own --record.
    ("validate_speak_strands.py", "code"),     # R78 budget per stage (ratchet: distance from band)
    ("validate_speak_spiral.py", "code"),      # R83 early seeds reaching stages 7-12 (ratchet: reach)
    ("validate_speak_duplicates.py", "code"),  # R86 hard + semantic near-duplicates (ratchet: pairs)
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
        # A SUITE entry may carry arguments ("validate_index_rebuildable.py --quick"): the file name is
        # the first token, the rest go through to the validator.
        name, *extra = script.split()
        interp = VENV_PY if name in NEEDS_VENV else PY
        if not interp.exists():
            rows.append(("FAIL", script, f"interpreter not found: {interp}"))
            if mode != "advisory":
                hard_fail = True
            if not quiet:
                print(f"{script}: needs the project venv at {interp}, which does not exist")
            continue
        p = subprocess.run([str(interp), str(HERE / name), *extra], capture_output=True, text=True,
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
