#!/usr/bin/env python3
"""Gate roadmap E: the machine-usable `formation_steps` now on the grammar points.

These are the highest-consequence field in the corpus. Everything else a learner MISREADS; a formation
rule a learner PRODUCES from, and a generator reading a wrong one manufactures wrong Japanese every time
it runs. The project's failure-mode catalogue calls this F5 and ranks it worst, and the campaign that
produced these steps had 41 critical findings against 495 points, so the risk is measured, not
hypothetical.

CHECKS
  1. every `op` and `base` is from the closed enum, and every nuance tag / usage context likewise. An
     off-enum value is silently ignored by consumers rather than failing, which is the quiet kind of
     wrong.
  2. a point has EITHER steps OR a stated `steps_unavailable` reason -- never neither. "No steps and no
     reason" is indistinguishable from "nobody looked", and the whole design of steps_unavailable is to
     make the negative case explicit.
  3. no point has both steps and a WITHHELD reason. The merge withholds steps for the 50 points whose
     verification failed; if steps ever reappear alongside that reason, something re-merged them.
  4. variants are never flattened: each carries its own `base`, and a variant list with two entries
     sharing a base and identical steps is a duplicate rather than a real alternative.
  5. `append` and `replace-ending` carry a token; the other ops do not need one, but an append with no
     token appends nothing and is a silent no-op step.

Usage: validate_grammar_formation.py
"""
from __future__ import annotations
import json
import re, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LEVELS = ("n5", "n4", "n3")

OPS = {"to-te-form", "to-masu-stem", "to-nai-stem", "to-ta-form", "to-dictionary", "to-volitional",
       "to-potential", "to-passive", "to-causative", "to-conditional-ba", "to-adverbial",
       "to-attributive", "nominalize", "append", "replace-ending", "drop-final-ru", "none"}
BASES = {"verb", "i-adjective", "na-adjective", "noun", "clause", "any"}

# A rule that moves a godan verb's final kana onto the あ-row (causative, passive, negative stem...),
# and the exception every such rule must carry.
AROW_RULE = re.compile(r"linha\s*[〜～]?\s*あ|sílaba final em -u|vogal\s*-u\s*pela linha|por -areru")
U_EXCEPTION = re.compile(r"-?う\s*(viram|vira|→|->)\s*-?わ|買わ")
NUANCE = {"emphasis", "softening", "conjecture", "obligation", "permission", "prohibition", "hearsay",
          "comparison", "cause", "condition", "concession", "intention", "desire", "request",
          "experience", "change-of-state", "continuation", "completion", "politeness", "humility",
          "honorific"}
CONTEXTS = {"spoken", "written", "business", "casual-friends", "formal-email", "academic",
            "announcement", "literary"}
NEEDS_TOKEN = {"append", "replace-ending"}


def main() -> int:
    fails: list[str] = []
    stats = Counter()
    for lv in LEVELS:
        for g in json.loads((ROOT / "corpus" / "grammar" / f"{lv}.json").read_text(encoding="utf-8")):
            key = g.get("key")
            fs = g.get("formation_steps")
            reason = g.get("steps_unavailable")

            # A godan あ-row rule stated WITHOUT the う exception teaches the learner to produce a
            # non-existent form: 買う goes to 買わせる, never to ×買あせる. Four records stated the rule
            # that way while gp-7 stated it correctly and conjugate.py's godan table ("う" -> "わ")
            # had always been right, so the prose and the drill data disagreed and nothing checked.
            # Prose is where the damage is — the machine steps delegate to the conjugator.
            prose = (g.get("formation") or {}).get("pt-BR") or ""
            if AROW_RULE.search(prose) and not U_EXCEPTION.search(prose):
                fails.append(f"{key}: states a godan あ-row formation rule without the う->わ "
                             f"exception, so applying it to a -う verb yields a form that does not "
                             f"exist (buy: 買う -> 買わ..., never 買あ...)")

            for t in g.get("nuance_tags") or []:
                if t not in NUANCE:
                    fails.append(f"{key}: nuance_tag {t!r} not in the closed enum")
            for c in g.get("usage_contexts") or []:
                if c not in CONTEXTS:
                    fails.append(f"{key}: usage_context {c!r} not in the closed enum")

            if not fs:
                if not reason:
                    fails.append(f"{key}: no formation_steps and no steps_unavailable reason")
                    stats["gap"] += 1
                else:
                    stats["withheld" if "WITHHELD" in reason else "steps_unavailable"] += 1
                continue

            if reason and "WITHHELD" in reason:
                fails.append(f"{key}: carries steps AND a WITHHELD reason -- steps were re-merged")

            variants = fs.get("variants") or []
            if not variants:
                fails.append(f"{key}: formation_steps present but has no variants")
                continue
            seen = set()
            for v in variants:
                if v.get("base") not in BASES:
                    fails.append(f"{key}: variant base {v.get('base')!r} not in the closed enum")
                steps = v.get("steps") or []
                if not steps:
                    fails.append(f"{key}: variant for base {v.get('base')!r} has no steps")
                sig = (v.get("base"), json.dumps(steps, ensure_ascii=False, sort_keys=True))
                if sig in seen:
                    fails.append(f"{key}: duplicate variant for base {v.get('base')!r}")
                seen.add(sig)
                for st in steps:
                    op = st.get("op")
                    if op not in OPS:
                        fails.append(f"{key}: op {op!r} not in the closed enum")
                    if op in NEEDS_TOKEN and not (st.get("token") or "").strip():
                        fails.append(f"{key}: {op} step with no token appends nothing")
                    if st.get("base") is not None and st["base"] not in BASES:
                        fails.append(f"{key}: step base {st['base']!r} not in the closed enum")
            stats["with steps"] += 1

    total = sum(stats.values())
    print(f"validate_grammar_formation: {total} grammar points, {len(fails)} FAIL")
    print("  " + "  ".join(f"{k}={v}" for k, v in stats.most_common()))
    for f in fails[:25]:
        print(f"  [FAIL] {f}")
    if len(fails) > 25:
        print(f"  ... and {len(fails) - 25} more")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
