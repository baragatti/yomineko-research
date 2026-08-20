#!/usr/bin/env python3
"""Validate corpus/exercises/roles - the role-identification drills (roadmap F consumer).

Every answer is DERIVED from the sentence patterns, so what can rot is the derivation drifting from the
sentence bank: a re-dissection that changes a chunk, or an item whose options stop being answerable.

Checked:
  * the referenced sentence still exists and its `jp` still matches what the item shows;
  * `correct` and every distractor are literal substrings of that sentence, so no option is text the
    learner cannot see on the page;
  * options are DISTINCT and the answer is not repeated among the distractors, which would make the
    item unanswerable;
  * the asked role is never ni-phrase or de-phrase (those are ambiguous by construction and are
    excluded as targets on purpose);
  * ids unique, level matches the file.

Usage: validate_role_exercises.py
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "corpus" / "exercises" / "roles"
SENT = ROOT / "corpus" / "sentences"
BANNED = {"ni-phrase", "de-phrase", "sentence-final"}


def main() -> int:
    if not EX.exists():
        print("validate_role_exercises: bank not built")
        return 0
    jp_of = {}
    for f in sorted(SENT.rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for s in (data if isinstance(data, list) else [data]):
            if isinstance(s, dict) and s.get("slug") and s.get("jp"):
                jp_of[s["slug"]] = s["jp"]

    fails, seen, total = [], set(), 0
    for f in sorted(glob.glob(str(EX / "*.json"))):
        level = Path(f).stem.split("_")[0]
        for it in json.loads(Path(f).read_text(encoding="utf-8")):
            total += 1
            iid = it["id"]
            if iid in seen:
                fails.append(f"{iid}: duplicate id")
            seen.add(iid)
            if it["level"] != level:
                fails.append(f"{iid}: level {it['level']} in {level} file")
            if it["role"] in BANNED:
                fails.append(f"{iid}: role {it['role']} must never be a target")
            jp = jp_of.get(it["sentence"])
            if jp is None:
                fails.append(f"{iid}: sentence {it['sentence']} does not resolve")
                continue
            if jp != it["jp"]:
                fails.append(f"{iid}: stored jp drifted from the sentence bank")
                continue
            opts = [it["correct"], *it.get("distractors", [])]
            if len(set(opts)) != len(opts):
                fails.append(f"{iid}: repeated option {opts}")
            if len(opts) < 3:
                fails.append(f"{iid}: only {len(opts)} options")
            for o in opts:
                if o and o not in jp:
                    fails.append(f"{iid}: option {o!r} is not in the sentence")

    for line in fails[:20]:
        print(f"  [FAIL] {line}")
    if len(fails) > 20:
        print(f"  [FAIL] ... and {len(fails) - 20} more")
    print(f"validate_role_exercises: {total} items, " + ("ALL OK" if not fails else f"{len(fails)} FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
