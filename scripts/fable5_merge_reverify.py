#!/usr/bin/env python3
"""Merge a reverify workflow's verdicts into its Phase-3 wave file (STATE runbook step 3).

Join is BY (slug, field) — never by index — so verifier reordering cannot misalign verdicts.
Only `unverified` findings are updated (already-confirmed pairs from the original run are left alone);
`fix`/`notes` are overwritten only when the verifier returned non-null values. Recounts the summary and
drops the salvage note. Idempotent: re-running with the same output changes nothing.

Usage: fable5_merge_reverify.py <wave-number> <workflow-output.json>
  e.g. fable5_merge_reverify.py 3 "%TEMP%/.../tasks/wj285jj3r.output"
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    wave_no, out_path = sys.argv[1], Path(sys.argv[2])
    matches = sorted(FD.glob(f"phase3_sentences_wave{wave_no}_batches*.json"))
    if len(matches) != 1:
        print(f"expected exactly 1 wave{wave_no} file, found {len(matches)}")
        return 1
    wf = matches[0]

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    result = payload.get("result", payload)
    verdicts = {(v["slug"], v["field"]): v for v in result["verdicts"]}
    print(f"verifier verdicts: {len(verdicts)}  ({dict(Counter(v['verdict'] for v in verdicts.values()))})")

    wave = json.loads(wf.read_text(encoding="utf-8"))
    merged = still = 0
    for f in wave["findings"]:
        if f.get("verdict") != "unverified":
            continue
        v = verdicts.get((f["slug"], f["field"]))
        if not v:
            still += 1
            continue
        f["verdict"] = v["verdict"]
        if v.get("fix"):
            f["fix"] = v["fix"]
        if v.get("notes"):
            f["notes"] = v["notes"]
        merged += 1

    counts = Counter(f["verdict"] for f in wave["findings"])
    wave["summary"] = {**wave.get("summary", {}), **counts,
                       "total_findings": len(wave["findings"])}
    if not still:
        wave["note"] = (f"Wave {wave_no} COMPLETE: all finders + full 2-verifier verification "
                        f"(salvaged findings re-verified via fable5_sentences_reverify_workflow.js). "
                        f"confirmed = 2-vote unanimous; disputed -> teacher queue; rejected -> dropped.")
    wf.write_text(json.dumps(wave, ensure_ascii=False, indent=1), encoding="utf-8")

    sev = Counter(f["severity"] for f in wave["findings"] if f["verdict"] == "confirmed")
    print(f"{wf.name}: merged {merged}, still unverified {still}")
    print(f"  verdicts: {dict(counts)}")
    print(f"  confirmed by severity: {dict(sev)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
