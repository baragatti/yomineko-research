#!/usr/bin/env python3
"""Salvage a fable5 sentence-QA wave from a workflow journal.

If a wave workflow is killed (session/usage limit) before returning, every
agent that DID finish already has its result line in the run's
journal.jsonl. This tool reconstructs the wave file in the exact format the
workflow would have returned ({phase, scope, wave, note, summary, findings}),
merging verifier verdicts onto finder findings the same way the workflow
script does (2 votes: both confirm -> confirmed, both refute -> rejected,
split -> disputed, missing -> unverified / partially, 1 vote -> that vote).

Usage:
  python3 scripts/fable5_journal_harvest.py <journal.jsonl> <wave-name> <lo> <hi> [out.json]

<lo> <hi> = inclusive batch index range (e.g. 124 185) — used to map finding
slugs back to batch files for attribution and to report unattributed leftovers.
Verdict-to-finding pairing is BY INDEX within a batch, mirroring the workflow.
Finder vs verifier results are distinguished by shape (findings vs verdicts).
Clean finders (checked>0, zero findings) can't be slug-attributed; they are
counted in summary.clean_finders.
"""
import collections
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_DIR = os.path.join(ROOT, "research", "derived", "fable5_validation", "batches", "sentences")


def batch_slug_map(lo, hi):
    m = {}
    for i in range(lo, hi + 1):
        p = os.path.join(BATCH_DIR, f"sentences-{i:03d}.json")
        for it in json.load(open(p, encoding="utf-8"))["items"]:
            m[it["slug"]] = i
    return m


def main():
    journal, wave = sys.argv[1], sys.argv[2]
    lo, hi = int(sys.argv[3]), int(sys.argv[4])
    out_path = sys.argv[5] if len(sys.argv) > 5 else os.path.join(
        ROOT, "research", "derived", "fable5_validation",
        f"phase3_sentences_{wave}_batches{lo:03d}-{hi:03d}.json")

    slug2batch = batch_slug_map(lo, hi)

    finders = []   # {checked, findings}
    verifiers = []  # {verdicts}
    for line in open(journal, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("type") != "result":
            continue
        res = rec.get("result")
        if not isinstance(res, dict):
            continue
        if "findings" in res:
            finders.append(res)
        elif "verdicts" in res:
            verifiers.append(res)

    # attribute finders/verifiers to batches via their first slug
    def batch_of(slugs):
        for s in slugs:
            if s in slug2batch:
                return slug2batch[s]
        return None

    find_by_batch = {}
    unattributed_finders = 0
    clean_finders = 0
    checked_total = 0
    for f in finders:
        checked_total += f.get("checked") or 0
        fs = f.get("findings") or []
        if not fs:
            clean_finders += 1
            continue
        b = batch_of([x.get("slug") for x in fs])
        if b is None:
            unattributed_finders += 1
            continue
        # keep the largest finding set if a batch somehow appears twice
        if b not in find_by_batch or len(fs) > len(find_by_batch[b]):
            find_by_batch[b] = fs

    ver_by_batch = collections.defaultdict(list)
    unattributed_verifiers = 0
    for v in verifiers:
        vs = v.get("verdicts") or []
        b = batch_of([x.get("slug") for x in vs])
        if b is None:
            unattributed_verifiers += 1
            continue
        ver_by_batch[b].append(vs)

    findings = []
    for b, fs in sorted(find_by_batch.items()):
        votes = ver_by_batch.get(b, [])[:2]
        for idx, f in enumerate(fs):
            vv = [vt[idx] for vt in votes if idx < len(vt)]
            avail = len(vv)
            confirms = sum(1 for x in vv if x.get("verdict") == "confirmed")
            verdict = ("unverified" if avail == 0 else
                       "confirmed" if confirms == avail else
                       "rejected" if confirms == 0 else "disputed")
            fix = next((x.get("fixed_suggestion") for x in vv if x.get("fixed_suggestion")), None) or f.get("suggested")
            notes = [x.get("note") for x in vv if x.get("note")]
            findings.append({**f, "verdict": verdict, "fix": fix, "notes": notes})

    c = collections.Counter(f["verdict"] for f in findings)
    out = {
        "phase": "phase3-sentences",
        "scope": f"batches {lo:03d}-{hi:03d} (15 sentences each)",
        "wave": wave,
        "note": ("JOURNAL SALVAGE — reconstructed from workflow journal.jsonl after an "
                 "interrupted run; batches whose finder never finished are simply absent. "
                 f"clean_finders={clean_finders} finder batches had zero findings (not slug-attributable)."),
        "summary": {
            "batches": hi - lo + 1,
            "batches_done": len(find_by_batch) + clean_finders,
            "checked": checked_total,
            "total_findings": len(findings),
            "confirmed": c.get("confirmed", 0),
            "disputed": c.get("disputed", 0),
            "rejected": c.get("rejected", 0),
            "unverified": c.get("unverified", 0),
            "clean_finders": clean_finders,
            "unattributed_finders": unattributed_finders,
            "unattributed_verifiers": unattributed_verifiers,
        },
        "findings": findings,
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps(out["summary"], ensure_ascii=False))
    print("->", out_path)


if __name__ == "__main__":
    main()
