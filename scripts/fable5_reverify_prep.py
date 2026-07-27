#!/usr/bin/env python3
"""Build reverify group files for a sentence-QA wave (wave-1 pattern).

Reads phase3_sentences_<wave>_batches<lo>-<hi>.json, takes findings whose
verdict == 'unverified', groups them by their batch (slug -> batch file), and
writes research/derived/fable5_validation/phase3_reverify/<wave>/<KEY>.json
as {path, findings:[raw finding fields]} — exactly what
fable5_sentences_reverify_workflow.js expects (args = {wave, keys:[KEY,...]}).

After the reverify workflow returns {verdicts:[{slug,field,verdict,fix,notes}]},
merge them into the wave file BY (slug, field): overwrite verdict, and fix/notes
when non-null, then recount the summary — same join wave 1 used.

Usage: fable5_reverify_prep.py <wave> <lo> <hi>   (e.g. wave3 124 185)
Requires the git-ignored batch files (regenerate with fable5_split_batches.py).
Prints the keys array to pass as workflow args.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAL = os.path.join(ROOT, "research", "derived", "fable5_validation")
BATCH_DIR = os.path.join(VAL, "batches", "sentences")
RAW_FIELDS = ["slug", "field", "severity", "issue", "current", "suggested", "confidence"]


def main():
    wave, lo, hi = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    wf = os.path.join(VAL, f"phase3_sentences_{wave}_batches{lo:03d}-{hi:03d}.json")
    data = json.load(open(wf, encoding="utf-8"))

    slug2batch = {}
    for i in range(lo, hi + 1):
        p = os.path.join(BATCH_DIR, f"sentences-{i:03d}.json")
        for it in json.load(open(p, encoding="utf-8"))["items"]:
            slug2batch[it["slug"]] = i

    groups = {}
    skipped = 0
    for f in data["findings"]:
        if f.get("verdict") != "unverified":
            continue
        b = slug2batch.get(f["slug"])
        if b is None:
            skipped += 1
            continue
        groups.setdefault(b, []).append({k: f.get(k) for k in RAW_FIELDS})

    outdir = os.path.join(VAL, "phase3_reverify", wave)
    os.makedirs(outdir, exist_ok=True)
    keys = []
    for b in sorted(groups):
        key = f"{b:03d}"
        keys.append(key)
        rel = f"research/derived/fable5_validation/batches/sentences/sentences-{key}.json"
        with open(os.path.join(outdir, f"{key}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"path": rel, "findings": groups[b]}, fh, ensure_ascii=False, indent=1)

    print(json.dumps({"wave": wave, "groups": len(keys),
                      "unverified_findings": sum(len(v) for v in groups.values()),
                      "skipped_unmappable": skipped, "keys": keys}, ensure_ascii=False))


if __name__ == "__main__":
    main()
