#!/usr/bin/env python3
"""Rebuild db/corpus.sqlite from the datasets and the tracked scripts — the whole chain, in order.

WHY THIS EXISTS
---------------
`db/corpus.sqlite` is git-ignored on purpose: the committed JSON under `corpus/` and `course/` is the
source of truth and the DB is "a regenerable working index" (CLAUDE.md). That claim was never tested.
Every repair campaign wrote the DB through its own apply script and then re-exported, so the export is
only reproducible if the DB is — and the DB existed as exactly one 200 MB file on one machine. If it
had been lost, nobody knew which of the ~90 scripts that have written it needed re-running, in what
order, or with which arguments.

This script is that answer, executable. It reads `research/derived/rebuild_manifest.json` — the durable
inventory of every DB writer, ordered by the order a rebuild must run them, each with the arguments it
needs and the commit it first landed in — and replays it into a fresh database.

`scripts/ingest/replay_all.py` is a step inside this chain, not a parallel one. It already rebuilt the
sentence bank from the saved `*_result.json` files (and wrapped reset_sentences / relink_vocab /
particle_link / repair_glosses / clean_emdash / load_lessons / build_sentence_vocab); it keeps doing
exactly that, in the one place the manifest puts it.

HOW THE REDIRECTION WORKS
-------------------------
Every step used to hardcode `ROOT / "db" / "corpus.sqlite"`. They now resolve their target through
`scripts/dbtarget.db_target()`, which honours `--db PATH` and `$YOMINEKO_DB` and otherwise returns the
same default as before. This runner sets `YOMINEKO_DB` for the whole subprocess chain, so nothing has
to know it is being rebuilt into a scratch file.

The same is true of the FILES the chain writes. A handful of steps rewrite the lesson authoring layer
(`research/derived/lessons/`) that `load_lessons.py` reads back, so a rebuild used to edit 74 tracked
files with output derived from its scratch database — and the next rebuild read that damage and
produced different bytes. Those paths now resolve through `dbtarget.out_root()`; this runner points
`$YOMINEKO_OUT_ROOT` at a work root (`<out>.work`, seeded with a copy of the lessons) so the chain
works on its own copy and the repo is left alone.

USAGE
-----
    rebuild_index.py --out /tmp/rebuilt.sqlite            # full rebuild (slow: minutes)
    rebuild_index.py --out X --to 12                      # stop after step 12
    rebuild_index.py --out X --from 40 --resume           # continue into an existing DB
    rebuild_index.py --out X --manifest other.json        # replay a modified manifest (plant proofs)
    rebuild_index.py --dry-run                            # print the plan, run nothing

Exit 0 when every enabled step succeeded. A step that fails stops the run unless --keep-going.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "derived" / "rebuild_manifest.json"


def interpreter() -> str:
    """Prefer the project venv — dissect.py needs SudachiPy, which the system python does not have."""
    venv = ROOT / ".venv" / "Scripts" / "python.exe"
    if venv.exists():
        return str(venv)
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    steps = data["steps"] if isinstance(data, dict) else data
    # A step commented out for a plant proof is either dropped from the list or flipped to
    # enabled:false — both are honoured here, and both must show up in the diff.
    return steps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="path of the database to build (required unless --dry-run)")
    ap.add_argument("--manifest", default=str(MANIFEST))
    ap.add_argument("--from", dest="start", type=int, default=1, help="first step number to run")
    ap.add_argument("--to", dest="end", type=int, default=10**6, help="last step number to run")
    ap.add_argument("--only", default="", help="comma-separated step numbers")
    ap.add_argument("--resume", action="store_true", help="keep an existing --out database")
    ap.add_argument("--keep-going", action="store_true", help="do not stop at the first failing step")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="one line per step, no step output")
    ap.add_argument("--work-root", help="repo-shaped scratch root for the chain's file writes "
                                        "(default <out>.work); seeded from research/derived/lessons")
    args = ap.parse_args()

    steps = load_manifest(Path(args.manifest))
    only = {int(x) for x in args.only.split(",") if x.strip()}
    todo = [s for s in steps
            if s.get("enabled", True)
            and args.start <= s["n"] <= args.end
            and (not only or s["n"] in only)]

    if args.dry_run:
        for s in todo:
            print(f"  {s['n']:>3} [{s['phase']:<11}] {s['script']} {' '.join(s['args'])}")
        skipped = [s for s in steps if not s.get("enabled", True)]
        print(f"\n{len(todo)} step(s) would run; {len(skipped)} disabled:")
        for s in skipped:
            print(f"  {s['n']:>3} {s['script']:<52} {s['note']}")
        return 0

    if not args.out:
        ap.error("--out is required unless --dry-run")
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not args.resume:
        out.unlink()
    for suffix in ("-wal", "-shm"):
        side = Path(str(out) + suffix)
        if side.exists() and not args.resume:
            side.unlink()

    # A rebuild must not edit the repo. Several steps rewrite the LESSON AUTHORING LAYER —
    # build_exam_kanji_lessons.py re-chunks research/derived/lessons/*-kanji-exame-*.json and
    # build_readings.py rewrites the <reading> block of every lesson it wires — and load_lessons.py
    # reads that same directory back. Pointed at a scratch database those writes are derived from
    # scratch data, so before this existed a rebuild silently rewrote 74 tracked lesson files with
    # its own degraded output, and the SECOND rebuild then read the damage back and produced
    # different bytes than the first. The chain now works on a copy: every one of those scripts
    # resolves the directory through dbtarget.out_root(), which follows $YOMINEKO_OUT_ROOT.
    work = Path(args.work_root).resolve() if args.work_root else Path(str(out) + ".work")
    src = ROOT / "research" / "derived" / "lessons"
    dst = work / "research" / "derived" / "lessons"
    if src.is_dir() and not (args.resume and dst.is_dir()):
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)

    py = interpreter()
    env = {**os.environ, "YOMINEKO_DB": str(out), "YOMINEKO_OUT_ROOT": str(work),
           "PYTHONIOENCODING": "utf-8"}
    log: list[dict] = []
    failures = 0
    t_all = time.time()
    print(f"rebuilding {out}\n  interpreter: {py}\n  manifest:    {args.manifest}\n"
          f"  work root:   {work}\n  steps:       {len(todo)}\n")

    for s in todo:
        cmd = [py, str(ROOT / s["script"]), *s["args"]]
        t0 = time.time()
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        dt = time.time() - t0
        out_txt = (p.stdout or "") + (p.stderr or "")
        tail = next((ln for ln in reversed(out_txt.splitlines()) if ln.strip()), "")
        ok = p.returncode == 0
        failures += 0 if ok else 1
        log.append({"n": s["n"], "script": s["script"], "args": s["args"], "rc": p.returncode,
                    "seconds": round(dt, 1), "tail": tail[:300]})
        print(f"  [{'OK ' if ok else 'FAIL'}] {s['n']:>3} {s['script']:<52} {dt:6.1f}s  {tail[:90]}")
        if not ok:
            if not args.quiet:
                print("\n".join("        " + ln for ln in out_txt.splitlines()[-25:]))
            if not args.keep_going:
                break

    total = time.time() - t_all
    (out.parent / (out.stem + ".rebuild-log.json")).write_text(
        json.dumps({"db": str(out), "seconds": round(total, 1), "failures": failures, "steps": log},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nrebuild finished in {total/60:.1f} min — {len(log)} step(s) run, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
