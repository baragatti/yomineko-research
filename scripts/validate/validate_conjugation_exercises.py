#!/usr/bin/env python3
"""Validate corpus/exercises/conjugation — the form-discrimination drill bank (roadmap item C).

Every answer here is DERIVED from corpus/conjugations, so the thing that can rot is the derivation
drifting from its source: a rebuild of the conjugation bank that changes a surface, or an item whose
options stop being answerable.

Checked:
  * every item's `correct` still matches the conjugation bank for that (vocab_id, form). This is the
    check that matters: it is what makes the bank Layer B rather than a frozen copy.
  * four DISTINCT option strings. Forms coincide for some words (na-adjective attributive vs terminal,
    and for ichidan verbs the potential and passive are the same surface), and a duplicated option is
    an unanswerable item.
  * `correct` is never equal to `prompt`, which would not be a question.
  * ids unique; level matches the file; `example`, where present, resolves to a real sentence AND that
    sentence actually contains the answer surface. An example that does not contain the form it is
    illustrating is worse than none.

Usage: validate_conjugation_exercises.py
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
EX = ROOT / "corpus" / "exercises" / "conjugation"
CONJ = ROOT / "corpus" / "conjugations"
SENT = ROOT / "corpus" / "sentences"


def main() -> int:
    if not EX.exists():
        print("validate_conjugation_exercises: bank not built - run build_conjugation_exercises.py")
        return 0

    key = {}
    for f in sorted(glob.glob(str(CONJ / "*.json"))):
        for e in json.loads(Path(f).read_text(encoding="utf-8")):
            for x in e["conjugations"]:
                key[(e["vocab_id"], x["form"])] = x.get("surface")

    jp_of = {}
    for f in sorted(SENT.rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for s in (data if isinstance(data, list) else [data]):
            if isinstance(s, dict) and s.get("slug") and s.get("jp"):
                jp_of[s["slug"]] = s["jp"]

    fails: list[str] = []
    seen: set[str] = set()
    total = 0
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
            want = key.get((it["vocab_id"], it["form"]))
            if want is None:
                fails.append(f"{iid}: no such (vocab_id, form) in the conjugation bank")
            elif want != it["correct"]:
                fails.append(f"{iid}: answer drifted from the bank ({it['correct']!r} vs {want!r})")
            opts = [it["correct"], *it.get("distractors", [])]
            if len(opts) != 4 or len(set(opts)) != 4:
                fails.append(f"{iid}: options are not 4 distinct strings: {opts}")
            if it["correct"] == it["prompt"]:
                fails.append(f"{iid}: answer equals the prompt")
            ex = it.get("example")
            if ex:
                if ex not in jp_of:
                    fails.append(f"{iid}: example {ex} does not resolve")
                elif it["correct"] not in jp_of[ex]:
                    fails.append(f"{iid}: example {ex} does not contain the answer surface")

    for line in fails[:20]:
        print(f"  [FAIL] {line}")
    if len(fails) > 20:
        print(f"  [FAIL] ... and {len(fails) - 20} more")
    print(f"validate_conjugation_exercises: {total} items, "
          + ("ALL OK" if not fails else f"{len(fails)} FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
