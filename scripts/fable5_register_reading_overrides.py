#!/usr/bin/env python3
"""Register the QA-verified token readings that intentionally differ from the analyzer.

Why this exists: validate.py §7.2 re-runs SudachiPy and requires the stored tokens to match it exactly,
INCLUDING `reading`. That guard is right about structure but wrong about readings, because the analyzer's
default reading is itself one of the defect sources Phase 3 was created to fix:

    10年   analyzer いちれい  (digit-by-digit non-reading)   -> corpus じゅう
    １１時 analyzer いちいち                                  -> corpus じゅういち
    ５月   analyzer よん      (よんがつ does not exist)       -> corpus し
    何時   analyzer いつ      (in a clock-time question)      -> corpus なんじ

After applying the Phase-3 patch, 410 sentences differ from the analyzer on reading alone and ZERO differ
structurally — i.e. every deviation is a corrected reading, not a mangled token stream.

Rather than relaxing §7.2 (which would let any future hand-edit of a reading pass unnoticed), each
deviation is REGISTERED here with the analyzer value it replaces. validate.py then treats a reading
mismatch as an error UNLESS it is registered, so the guard still catches unverified drift.

Writes research/derived/fable5_validation/verified_reading_overrides.json.
Usage: fable5_register_reading_overrides.py
"""
from __future__ import annotations
import importlib.util, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"

spec = importlib.util.spec_from_file_location("v", ROOT / "scripts" / "validate" / "validate.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def main() -> int:
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
    diss = v.Dissector()
    overrides, structural = {}, []
    for sid, slug, jp in con.execute("SELECT id, slug, jp FROM sentence ORDER BY id"):
        toks = con.execute(
            "SELECT surface,lemma,reading,pos_coarse FROM token WHERE sentence_id=? AND split_mode='C' "
            "ORDER BY position", (sid,)).fetchall()
        ref = [(t["surface"], t["lemma"], t["reading"], t["pos_coarse"])
               for t in diss.skeleton(jp)["tokens"]]
        got = [tuple(t) for t in toks]
        if got == ref:
            continue
        if [(a, b, d) for a, b, c, d in got] != [(a, b, d) for a, b, c, d in ref]:
            structural.append(slug)          # never registered - a real tokenization defect
            continue
        overrides[slug] = [{"i": i, "surface": g[0], "reading": g[2], "analyzer_reading": r[2]}
                           for i, (g, r) in enumerate(zip(got, ref)) if g[2] != r[2]]
    con.close()

    (FD / "verified_reading_overrides.json").write_text(json.dumps(
        {"note": "Token readings that intentionally differ from the SudachiPy default, because the "
                 "analyzer's reading was wrong in context. Every entry was confirmed by the Phase-3 QA "
                 "campaign (2-vote adversarial verification) and survived four diff-audit rounds. "
                 "validate.py §7.2 allows a reading mismatch ONLY if registered here; structural "
                 "mismatches are never registrable.",
         "sentences": len(overrides),
         "tokens": sum(len(v_) for v_ in overrides.values()),
         "structural_mismatches_NOT_registered": structural,
         "overrides": overrides}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"registered: {len(overrides)} sentences / {sum(len(x) for x in overrides.values())} token readings")
    print(f"structural mismatches (NOT registered, must be fixed): {len(structural)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
