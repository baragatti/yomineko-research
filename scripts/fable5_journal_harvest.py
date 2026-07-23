#!/usr/bin/env python3
"""Salvage / drive fable5 sentence-QA waves from workflow journals.

Workflow agents persist every finished result to their run's journal.jsonl.
This tool scans ALL journals (default: every journal.jsonl under this
session's workflows dir), attributes finder/verifier results to batch
indices via finding slugs (batch files are the slug source of truth), and
either reports coverage (--status) or writes a wave file in the exact
format the live workflow returns.

Coverage rules per batch:
  complete    = finder + >=2 verifier verdict-sets (full 2-vote quality)
  finder_only = finder present, <2 verifier sets (findings salvageable but
                unverified/1-vote — re-run for full quality unless salvaging)
  missing     = no attributable finder result
Clean finders (checked>0, zero findings) carry no slugs and cannot be
attributed; they are counted but their batches stay in `missing` (re-running
a clean batch is cheap and harmless — the driver loop stays convergent).

Usage:
  status:  fable5_journal_harvest.py --status <lo> <hi>
  write:   fable5_journal_harvest.py <wave-name> <lo> <hi> [--out FILE] [--salvage]
           (write refuses unless every batch is `complete`; --salvage writes
            whatever exists, marking 1-vote/0-vote findings accordingly)
Driver loop (any number of interruptions):
  while status.missing or status.finder_only:
      relaunch fable5_sentences_workflow.js with args = those indices
  then write the wave file, commit, push.
"""
import argparse
import collections
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_DIR = os.path.join(ROOT, "research", "derived", "fable5_validation", "batches", "sentences")
SESSION_WF = os.path.expanduser(
    "~/.claude/projects/-home-lucas-WebstormProjects-yomineko-research/"
    "ab306cd7-a53c-4c26-aee3-5d3c5a28ef3b/subagents/workflows")


def batch_slug_map(lo, hi):
    m = {}
    for i in range(lo, hi + 1):
        p = os.path.join(BATCH_DIR, f"sentences-{i:03d}.json")
        for it in json.load(open(p, encoding="utf-8"))["items"]:
            m[it["slug"]] = i
    return m


def gather(journal_glob):
    finders, verifiers = [], []
    clean = 0
    for jf in sorted(glob.glob(journal_glob)):
        for line in open(jf, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "result":
                continue
            res = rec.get("result")
            if not isinstance(res, dict):
                continue
            if "findings" in res:
                if res.get("findings"):
                    finders.append(res)
                else:
                    clean += 1
            elif "verdicts" in res and res.get("verdicts"):
                verifiers.append(res)
    return finders, verifiers, clean


def coverage(lo, hi, journal_glob):
    slug2batch = batch_slug_map(lo, hi)

    def batch_of(slugs):
        for s in slugs:
            if s in slug2batch:
                return slug2batch[s]
        return None

    finders, verifiers, clean = gather(journal_glob)
    find_by_batch = {}
    for f in finders:
        b = batch_of([x.get("slug") for x in f["findings"]])
        if b is None:
            continue
        if b not in find_by_batch or len(f["findings"]) > len(find_by_batch[b]["findings"]):
            find_by_batch[b] = f
    ver_by_batch = collections.defaultdict(list)
    for v in verifiers:
        b = batch_of([x.get("slug") for x in v["verdicts"]])
        if b is not None:
            ver_by_batch[b].append(v["verdicts"])
    # prefer the verdict sets that match the finder's finding count
    for b, sets in ver_by_batch.items():
        want = len(find_by_batch[b]["findings"]) if b in find_by_batch else None
        sets.sort(key=lambda s: (len(s) != want, -len(s)))
    complete = sorted(b for b in find_by_batch if len(ver_by_batch.get(b, [])) >= 2)
    finder_only = sorted(b for b in find_by_batch if b not in complete)
    missing = sorted(set(range(lo, hi + 1)) - set(find_by_batch))
    return {
        "complete": complete, "finder_only": finder_only, "missing": missing,
        "clean_finders_unattributed": clean,
        "find_by_batch": find_by_batch, "ver_by_batch": ver_by_batch,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("args", nargs="+", help="--status LO HI | WAVE LO HI")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--salvage", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--journals", default=os.path.join(SESSION_WF, "*", "journal.jsonl"))
    a = ap.parse_args()

    if a.status:
        lo, hi = int(a.args[0]), int(a.args[1])
        cov = coverage(lo, hi, a.journals)
        print(json.dumps({
            "range": [lo, hi],
            "complete": cov["complete"],
            "finder_only": cov["finder_only"],
            "missing": cov["missing"],
            "todo": cov["finder_only"] + cov["missing"],
            "clean_finders_unattributed": cov["clean_finders_unattributed"],
        }))
        return

    wave, lo, hi = a.args[0], int(a.args[1]), int(a.args[2])
    out_path = a.out or os.path.join(
        ROOT, "research", "derived", "fable5_validation",
        f"phase3_sentences_{wave}_batches{lo:03d}-{hi:03d}.json")
    cov = coverage(lo, hi, a.journals)
    if (cov["finder_only"] or cov["missing"]) and not a.salvage:
        raise SystemExit(f"incomplete coverage (finder_only={cov['finder_only']} "
                         f"missing={cov['missing']}); use --salvage to write anyway")

    findings = []
    checked_total = 0
    for b in sorted(cov["find_by_batch"]):
        f = cov["find_by_batch"][b]
        checked_total += f.get("checked") or 0
        votes = cov["ver_by_batch"].get(b, [])[:2]
        for idx, fd in enumerate(f["findings"]):
            vv = [vt[idx] for vt in votes if idx < len(vt)]
            avail = len(vv)
            confirms = sum(1 for x in vv if x.get("verdict") == "confirmed")
            verdict = ("unverified" if avail == 0 else
                       "confirmed" if confirms == avail else
                       "rejected" if confirms == 0 else "disputed")
            fix = next((x.get("fixed_suggestion") for x in vv if x.get("fixed_suggestion")), None) or fd.get("suggested")
            notes = [x.get("note") for x in vv if x.get("note")]
            findings.append({**fd, "verdict": verdict, "fix": fix, "notes": notes})

    c = collections.Counter(f["verdict"] for f in findings)
    n_batches = hi - lo + 1
    out = {
        "phase": "phase3-sentences",
        "scope": f"batches {lo:03d}-{hi:03d} (15 sentences each)",
        "wave": wave,
        "note": ("Assembled from workflow journals by fable5_journal_harvest.py "
                 "(2-vote verdict merge identical to the live workflow). "
                 + ("SALVAGE MODE — coverage incomplete: "
                    f"finder_only={cov['finder_only']} missing={cov['missing']}. "
                    if (cov["finder_only"] or cov["missing"]) else "Full coverage. ")
                 + f"clean_finders_unattributed={cov['clean_finders_unattributed']}."),
        "summary": {
            "batches": n_batches,
            "batches_done": len(cov["find_by_batch"]),
            "checked": checked_total,
            "total_findings": len(findings),
            "confirmed": c.get("confirmed", 0),
            "disputed": c.get("disputed", 0),
            "rejected": c.get("rejected", 0),
            "unverified": c.get("unverified", 0),
        },
        "findings": findings,
    }
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps(out["summary"], ensure_ascii=False))
    print("->", out_path)


if __name__ == "__main__":
    main()
