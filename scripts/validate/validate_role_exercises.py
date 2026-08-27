#!/usr/bin/env python3
"""Validate corpus/exercises/roles - the role-identification drills (roadmap F consumer).

Every answer is DERIVED from the sentence patterns, so what can rot is the derivation drifting from the
sentence bank: a re-dissection that changes a chunk, or an item whose options stop being answerable.

WHY THE RE-DERIVATION WAS ADDED
-------------------------------
The original checks were all SHAPE checks — the options are distinct, they are substrings of the
sentence, the asked role is not one of the banned ones. Every one of them still passes if the answer is
simply WRONG: point `correct` at a different chunk of the same sentence and it is still a distinct
substring, still not banned, still not repeated. The bank was 5,358 items deep with nothing comparing a
single answer to the pattern data it was generated from, which is the same class of defect the project
has just spent a day removing elsewhere — a validator that cannot fail. So this now re-derives each item
from the sentence's own `pattern` array, exactly the way scripts/export/build_role_exercises.py built it:

  * the asked role occurs EXACTLY ONCE in the pattern (two を chunks would mean two defensible answers,
    and the builder skips those — an item asking for a doubled role can only have come from drift);
  * `correct` is the text of THAT chunk, and `particle` is that chunk's particle;
  * every distractor is another chunk of the same sentence, never the answer chunk and never a chunk
    that also carries the asked role;
  * the option count is what the builder emits: min(3, chunks - 1);
  * the sentence has 3..6 chunks (MIN_CHUNKS/MAX_CHUNKS) and the item's level is the sentence's level;
  * the asked role is one of the seven ASKABLE roles. The old BANNED list named three roles that must
    never be targets; the builder's real contract is the closed allowlist, and と in particular used to
    be askable and generated 319 items calling every と "companhia ou par", quotatives included.

Also checked (unchanged):
  * the referenced sentence still exists and its `jp` still matches what the item shows;
  * `correct` and every distractor are literal substrings of that sentence, so no option is text the
    learner cannot see on the page;
  * options are DISTINCT and the answer is not repeated among the distractors;
  * the asked role is never ni-phrase or de-phrase (those are ambiguous by construction);
  * ids unique, level matches the file.

Reads exported JSON only; never db/corpus.sqlite.
Usage: validate_role_exercises.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

MAX_REPORT = 15
BANNED = {"ni-phrase", "de-phrase", "sentence-final"}
# The closed allowlist of roles the builder is willing to ask about (build_role_exercises.ASKABLE).
# A role outside it is not derivable from the (particle, function_type) pair and must never be a target.
ASKABLE = {"topic", "subject", "object", "predicate", "modifier", "from", "direction"}
MIN_CHUNKS, MAX_CHUNKS = 3, 6


def load_sentences(root: Path) -> dict[str, dict]:
    """slug -> sentence record, from the committed export (bank.json plus any sibling shard)."""
    out: dict[str, dict] = {}
    for f in sorted((root / "corpus" / "sentences").rglob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for s in (data if isinstance(data, list) else [data]):
            if isinstance(s, dict) and s.get("slug") and s.get("jp"):
                out[s["slug"]] = s
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                    help="repo root to validate (default: this checkout)")
    ap.add_argument("--list", action="store_true", help="print every failure, not the first 15")
    args = ap.parse_args()
    root = args.root.resolve()
    ex = root / "corpus" / "exercises" / "roles"
    if not ex.exists():
        print("FAIL validate_role_exercises: corpus/exercises/roles is MISSING — a gate whose data vanished must FAIL, not certify nothing")
        return 1

    sentences = load_sentences(root)
    fails: list[str] = []
    seen: set[str] = set()
    total = 0
    derived = 0
    by_role: Counter = Counter()

    for f in sorted(ex.glob("*.json")):
        level = f.stem.split("_")[0]
        for it in json.loads(f.read_text(encoding="utf-8")):
            total += 1
            iid = it["id"]
            if iid in seen:
                fails.append(f"{iid}: duplicate id")
            seen.add(iid)
            if it["level"] != level:
                fails.append(f"{iid}: level {it['level']} in {level} file")
            if it["role"] in BANNED:
                fails.append(f"{iid}: role {it['role']} must never be a target")
            if it["role"] not in ASKABLE:
                fails.append(f"{iid}: role {it['role']} is not one of the seven askable roles")
            by_role[it["role"]] += 1

            sent = sentences.get(it["sentence"])
            if sent is None:
                fails.append(f"{iid}: sentence {it['sentence']} does not resolve")
                continue
            jp = sent["jp"]
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

            # ---- re-derivation from the sentence's own pattern data ----------------------------
            pattern = sent.get("pattern") or []
            if not pattern:
                fails.append(f"{iid}: sentence {it['sentence']} carries no pattern data to derive from")
                continue
            derived += 1
            if not (MIN_CHUNKS <= len(pattern) <= MAX_CHUNKS):
                fails.append(f"{iid}: sentence has {len(pattern)} chunks, outside {MIN_CHUNKS}..{MAX_CHUNKS}")
            if it["level"] != sent.get("level"):
                fails.append(f"{iid}: level {it['level']} but the sentence is {sent.get('level')}")
            role_counts = Counter(p.get("role") for p in pattern)
            n = role_counts.get(it["role"], 0)
            if n != 1:
                fails.append(f"{iid}: role {it['role']} occurs {n}x in the pattern — not exactly one answer")
                continue
            answer = next(p for p in pattern if p.get("role") == it["role"])
            if answer.get("chunk") != it["correct"]:
                fails.append(f"{iid}: correct {it['correct']!r} is not the {it['role']} chunk "
                             f"({answer.get('chunk')!r})")
            if (answer.get("particle") or None) != (it.get("particle") or None):
                fails.append(f"{iid}: particle {it.get('particle')!r} is not the chunk's "
                             f"({answer.get('particle')!r})")
            others = {p.get("chunk") for p in pattern} - {answer.get("chunk")}
            for d in it.get("distractors", []):
                if d not in others:
                    fails.append(f"{iid}: distractor {d!r} is not another chunk of the sentence")
                    continue
                roles = {p.get("role") for p in pattern if p.get("chunk") == d}
                if roles == {it["role"]}:
                    fails.append(f"{iid}: distractor {d!r} also carries the asked role {it['role']}")
            want = min(3, len(pattern) - 1)
            if len(it.get("distractors", [])) != want:
                fails.append(f"{iid}: {len(it.get('distractors', []))} distractors, "
                             f"the pattern supports {want}")

    for line in (fails if args.list else fails[:MAX_REPORT]):
        print(f"  [FAIL] {line}")
    if not args.list and len(fails) > MAX_REPORT:
        print(f"  [FAIL] ... and {len(fails) - MAX_REPORT} more (re-run with --list)")
    print("  by role: " + "  ".join(f"{k}={v}" for k, v in by_role.most_common()))
    print(f"validate_role_exercises: {total} items, {derived} re-derived from pattern data, "
          + ("ALL OK" if not fails else f"{len(fails)} FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
