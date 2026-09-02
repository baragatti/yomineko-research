#!/usr/bin/env python3
"""Prove the git-ignored index really is regenerable: rebuild it, re-export, diff against what is committed.

THE CLAIM UNDER TEST
--------------------
CLAUDE.md says `db/corpus.sqlite` is "a regenerable working/query index, NOT the source of truth —
git-ignored and rebuildable from the scripts + datasets". Nothing checked that. Six repair campaigns
wrote that one 200 MB file through their own apply scripts and re-exported; if it had been lost, the
committed JSON would have been all that survived, and nobody knew whether the ninety-odd scripts that
had written it could put it back.

This validator runs the experiment. It replays `research/derived/rebuild_manifest.json` into a scratch
database through `scripts/rebuild_index.py`, runs the exporters against THAT database into a scratch
tree, and compares every file they produce, byte for byte, with the committed one.

WHAT IT ASSERTS
---------------
1. The rebuild runs clean — every enabled manifest step exits 0.
2. Every exported file is byte-identical to the committed one, EXCEPT the files listed in
   `rebuild_baseline.json`, which are today's known unreproducible set, each with its cause.
3. Every baselined file still rebuilds to the exact bytes recorded in the baseline. This is what keeps
   the ratchet honest: a file may be excused for differing from the committed export, but it may not
   drift. Drop a repair step from the manifest and the bytes it wrote change, so the check fails and
   names the file — which is the whole point of the exercise.
4. A baselined file that has started matching the committed export is reported, so the entry is deleted.
   The baseline may only shrink.

WHAT THE FIRST FULL RUN SAID, 2026-09-02
----------------------------------------
137 of 787 exported files rebuild byte-identically; 650 do not, and the honest reading is that the
answer to "is the index regenerable" is *not yet*. The causes are in `rebuild_baseline.json` under
`_causes`, keyed per file. Twelve manifest steps cannot run at all because their inputs are
`.gitignore`d or were never written to disk; nine repair steps then refuse every row because they
exact-match text those steps wrote. Beyond that the database is a nine-month accumulation and this is
one ordered pass: `build_readings.py` has 286 reading rows on this machine and builds 130 in a replay,
`build_families_full.py` is scoped to N5/N4 but now runs after the N2/N1 ingest. The ratchet holds
that debt at today's bytes so it can only shrink, and the run is fast enough (90 s) to check often.

The one wall-clock stamp the exporters used to write (`_Generated <today>`) is pinned via
`$YOMINEKO_BUILD_DATE`, set here to the date already committed, so the diff measures the data and not
the calendar.

Only what the three exporters write is compared: `export_corpus.py` (kanji, vocab, grammar, families,
sentences), `export_course.py` (the course tree, manifest, outline) and `export_readings.py`. The bank
and drill builders — exam banks, conjugations, speaking path, exercises, capabilities, strokes — take
authored inputs of their own and belong to their own gates; `migrate_exam_banks_p7.py` says outright
that the exam banks cannot be regenerated yet (W17/W18).

MODES
-----
    validate_index_rebuildable.py --quick    # grammar family only, ~2s — this is what the suite runs
    validate_index_rebuildable.py            # everything, ~90s — run before a release
    validate_index_rebuildable.py --manifest PATH   # replay a modified manifest (plant proofs)
    validate_index_rebuildable.py --record   # rewrite this mode's baseline from the current rebuild
    validate_index_rebuildable.py --keep     # leave the scratch tree for inspection

Exit 0 = ALL OK. Exit 1 = FAIL, listing the first 20 offending files with a one-line reason each.

The rebuild writes nothing into the repo: `rebuild_index.py` gives the chain a work root and the steps
that rewrite `research/derived/lessons/` follow it (see its docstring). Two consecutive full runs
produce identical trees and leave `git status` unchanged — which is itself checked, by running it twice.

PLANT PROOF (recorded 2026-09-02, per scripts/validate/README.md)
------------------------------------------------------------------
QUICK — drop one repair step from a copy of the manifest.

  $ python scripts/validate/validate_index_rebuildable.py --quick
    compared 4 exported file(s) in 1s (mode quick, build date pinned to 2026-09-02)
    [OK] 4 exported file(s) checked, 4 held by rebuild_baseline.json at the recorded bytes

  # step 91, scripts/apply_grammar_formation_repairs.py, flipped to "enabled": false in a copy
  $ python scripts/validate/validate_index_rebuildable.py --quick --manifest <copy>
    compared 4 exported file(s) in 2s (mode quick, build date pinned to 2026-09-02)
    [FAIL] 3 file(s) wrong
      corpus/grammar/n3.json   held by the baseline, but the rebuild no longer produces the recorded
                               bytes (a manifest step that used to write it is gone or changed)
      corpus/grammar/n4.json   held by the baseline, but the rebuild no longer produces the recorded
                               bytes (a manifest step that used to write it is gone or changed)
      corpus/grammar/n5.json   held by the baseline, but the rebuild no longer produces the recorded
                               bytes (a manifest step that used to write it is gone or changed)

  $ python scripts/validate/validate_index_rebuildable.py --quick
    [OK] 4 exported file(s) checked, 4 held by rebuild_baseline.json at the recorded bytes

FULL — drop the topic renumbering, which is what decides every course directory name.

  $ python scripts/validate/validate_index_rebuildable.py
    compared 787 exported file(s) in 91s (mode full, build date pinned to 2026-09-02)
    [OK] 787 exported file(s) checked, 650 held by rebuild_baseline.json at the recorded bytes

  # step 34, scripts/ingest/renumber_topics.py, flipped to "enabled": false in a copy
  $ python scripts/validate/validate_index_rebuildable.py --manifest <copy>
    compared 789 exported file(s) in 92s (mode full, build date pinned to 2026-09-02)
    [FAIL] 500 file(s) wrong
      corpus/readings/n4.json                       rebuilt 79,055 bytes vs committed 288,555; first
                                                    difference at byte 19
      course/n3/course.json                         held by the baseline, but the rebuild no longer
                                                    produces the recorded bytes
      course/n3/topic-36-conectores/lesson-01.json  the rebuild produced a file that is not committed
      … 497 more — every N3 and N4 lesson lands one or two directories off its published path

  $ python scripts/validate/validate_index_rebuildable.py
    [OK] 787 exported file(s) checked, 650 held by rebuild_baseline.json at the recorded bytes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = HERE / "rebuild_baseline.json"
STAMP_RX = re.compile(r"_(?:Generated|Gerado) (\d{4}-\d{2}-\d{2})")
QUICK_PATHS = ("corpus/grammar/",)
# Empty input must fail, not certify nothing (scripts/validate/README.md, Conventions). An export that
# produced no files, or a manifest whose steps were quietly dropped, would otherwise walk an empty tree
# and print OK. Floors sit well below today's counts (4 and 787) so growth never trips them.
FLOOR = {"quick": 4, "full": 700}


def run(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def committed_build_date() -> str:
    """The date already stamped in the committed export — what a faithful rebuild must reproduce."""
    for rel in ("corpus/INDEX.md", "corpus/grammar/INDEX.md", "course/INDEX.md"):
        f = ROOT / rel
        if f.exists():
            m = STAMP_RX.search(f.read_text(encoding="utf-8"))
            if m:
                return m.group(1)
    return ""


def quick_steps(manifest: Path) -> list[int]:
    """The manifest's own answer to 'what does corpus/grammar pass through without the bank?'."""
    steps = json.loads(manifest.read_text(encoding="utf-8"))["steps"]
    return [s["n"] for s in steps if s.get("enabled", True) and s.get("quick_family") == "grammar"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="grammar family only; what the suite runs")
    ap.add_argument("--manifest", default=str(ROOT / "research" / "derived" / "rebuild_manifest.json"))
    ap.add_argument("--record", action="store_true", help="rewrite this mode's baseline from this run")
    ap.add_argument("--keep", action="store_true", help="leave the scratch tree behind")
    args = ap.parse_args()
    mode = "quick" if args.quick else "full"

    manifest = Path(args.manifest)
    if not manifest.exists():
        print(f"[FAIL] no manifest at {manifest}")
        return 1

    work = Path(tempfile.mkdtemp(prefix="yomineko-rebuild-"))
    db, tree = work / "corpus.sqlite", work / "tree"
    t0 = time.time()
    try:
        cmd = [sys.executable, str(ROOT / "scripts" / "rebuild_index.py"),
               "--out", str(db), "--manifest", str(manifest), "--quiet"]
        if args.quick:
            steps = quick_steps(manifest)
            if not steps:
                print("[FAIL] --quick found no grammar-family steps in the manifest")
                return 1
            cmd += ["--only", ",".join(str(n) for n in steps)]
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        p = run(cmd, env)
        if p.returncode != 0:
            print(p.stdout)
            print((p.stderr or "")[-2000:])
            print("[FAIL] the rebuild itself did not run clean; nothing to diff")
            return 1

        stamp = committed_build_date()
        exp_env = {**env, "YOMINEKO_DB": str(db), "YOMINEKO_OUT_ROOT": str(tree),
                   "YOMINEKO_BUILD_DATE": stamp}
        exporters = ["export_corpus.py"] if args.quick else [
            "export_corpus.py", "export_course.py", "export_readings.py"]
        for e in exporters:
            r = run([sys.executable, str(ROOT / "scripts" / "export" / e)], exp_env)
            if r.returncode != 0:
                print(((r.stdout or "") + (r.stderr or ""))[-2500:])
                print(f"[FAIL] {e} could not export the rebuilt database")
                return 1

        base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}
        known: dict[str, dict] = base.get(mode, {}).get("known", {})

        checked = 0
        matches: set[str] = set()          # rebuilt == committed
        held: list[str] = []               # differs, baselined, bytes unchanged
        bad: list[tuple[str, str]] = []    # everything else
        recorded: dict[str, dict] = {}

        for f in sorted(tree.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(tree).as_posix()
            if args.quick and not rel.startswith(QUICK_PATHS):
                continue
            checked += 1
            a = f.read_bytes()
            target = ROOT / rel
            b = target.read_bytes() if target.exists() else None
            if b is not None and a == b:
                matches.add(rel)
                continue
            entry = known.get(rel)
            reason = ("the rebuild produced a file that is not committed" if b is None else
                      (f"rebuilt {len(a):,} bytes vs committed {len(b):,}" if len(a) != len(b)
                       else f"same length ({len(a):,} bytes), content differs"))
            if b is not None:
                at = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                reason += f"; first difference at byte {at:,}"
            recorded[rel] = {"rebuilt_sha256": sha(a), "cause": (entry or {}).get("cause", reason)}
            if entry is None:
                bad.append((rel, reason))
            elif entry.get("rebuilt_sha256") != sha(a):
                bad.append((rel, "held by the baseline, but the rebuild no longer produces the "
                                 "recorded bytes (a manifest step that used to write it is gone or changed)"))
            else:
                held.append(rel)

        healed = [r for r in known if r in matches]

        if checked < FLOOR[mode]:
            print(f"compared {checked} exported file(s) (mode {mode})")
            print(f"[FAIL] only {checked} file(s) to compare, floor for mode '{mode}' is "
                  f"{FLOOR[mode]} — the export produced nothing to check, so nothing was checked")
            return 1

        if args.record:
            base.setdefault(mode, {})["known"] = dict(sorted(recorded.items()))
            base.setdefault(mode, {})["recorded_at"] = time.strftime("%Y-%m-%d")
            base["_why"] = ("Files the rebuild does not reproduce byte-for-byte yet, per mode, each "
                            "pinned to the bytes the rebuild currently produces. An entry may be "
                            "deleted when the file starts matching; adding one needs a written cause. "
                            "Each cause starts with a key from _causes — the diagnosis — followed by "
                            "the measured difference for that file; a re-record keeps the cause an "
                            "entry already carries, so those keys survive.")
            BASELINE.write_text(json.dumps(base, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(f"recorded {len(recorded)} baseline entr(y|ies) for mode '{mode}' -> {BASELINE.name}")
            return 0

        print(f"compared {checked} exported file(s) in {time.time()-t0:.0f}s "
              f"(mode {mode}, build date pinned to {stamp or 'today'})")
        for rel in healed:
            print(f"  [ratchet] {rel} now matches the committed export — delete its baseline entry")
        if healed:
            bad += [(r, "matches the committed export now; its rebuild_baseline.json entry must go")
                    for r in healed]
        if not bad:
            extra = f", {len(held)} held by rebuild_baseline.json at the recorded bytes" if held else ""
            print(f"[OK] {checked} exported file(s) checked{extra}")
            return 0
        print(f"[FAIL] {len(bad)} file(s) wrong")
        for rel, why in bad[:20]:
            print(f"  {rel:<48} {why}")
        if len(bad) > 20:
            print(f"  … and {len(bad)-20} more")
        return 1
    finally:
        if args.keep:
            print(f"scratch kept at {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
