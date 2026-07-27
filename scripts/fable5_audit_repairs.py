#!/usr/bin/env python3
"""Turn the diff-audit objections into supplemental repair ops (the fix half of the audit loop).

Audit round 2 left 562 objections, 481 of them carrying a concrete corrected value. Most are not new
defects but INCOMPLETE applications of a confirmed fix:
  * partial-locale  — the op named both locales, only one was written, so en and pt now contradict
                      (role.en still "predicative" while role.pt-BR says "atributivo");
  * incomplete cascade — a verb sense corrected in the parenthetical gloss but left stale in the clause
                      before it, so one explanation teaches both senses;
  * stale literal   — translation_literal.* still offering the reading the fix rejected.
Each auditor supplied the replacement text, so these are applied as ordinary replace ops on top of the
patch rather than re-authored.

Only unambiguous suggestions are taken: a single resolvable field path, a value that is not itself prose
instructions, and (for locale-less token paths) a suggestion that is valid JSON for both locales. Anything
else is left for a human/agent pass and listed in the `skipped` block. The renderer's INSTRUCTION_RE and
I7/I8 result guards still police whatever comes through here.

Usage: fable5_audit_repairs.py [--round 2]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"

SENT_FIELD = re.compile(r"^(jp|kana|romaji)$")
TEXT_FIELD = re.compile(r"^(?:texts\.)?(translation|translation_literal|structure_explanation)\.(en|pt-BR)$")
TOKEN_FIELD = re.compile(r"^tokens\[(\d+)\]\.(r|reading|romaji|role|gloss|note|conjugation_note)"
                         r"(?:\.(en|pt-BR))?$")
TOKEN_ATTR = {"r": "reading", "reading": "reading", "romaji": "romaji", "role": "role",
              "gloss": "gloss", "note": "conjugation_note", "conjugation_note": "conjugation_note"}
# a suggestion that describes an edit instead of being one
PROSE = re.compile(r"^(replace|change|set|update|remove|delete|merge|apply|add)\b|"
                   r"\bwith\b.*\bin both\b|->|→|;\s*(en|pt-BR)\s*:", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", default="2")
    args = ap.parse_args()
    src = FD / f"phase3_diff_audit_round{args.round}.json"
    objections = json.loads(src.read_text(encoding="utf-8"))["objections"]

    by_slug, skipped = {}, []
    for o in objections:
        sug = (o.get("suggested") or "").strip()
        field = (o.get("field") or "").strip()
        if not sug or "/" in field or "\n" in sug or PROSE.match(sug):
            skipped.append({"slug": o["slug"], "field": field, "severity": o["severity"],
                            "why": "no concrete single-field value", "reason": o["reason"][:200]})
            continue
        op = None
        if SENT_FIELD.match(field):
            op = {"mode": "replace", "path": [field], "fix": sug}
        elif (m := TEXT_FIELD.match(field)):
            op = {"mode": "replace", "path": [m.group(1), m.group(2)], "fix": sug}
        elif (m := TOKEN_FIELD.match(field)):
            idx, attr, loc = int(m.group(1)), TOKEN_ATTR[m.group(2)], m.group(3)
            if attr in ("reading", "romaji"):
                op = {"mode": "replace", "path": ["tokens", idx, attr], "fix": sug}
            elif loc:
                op = {"mode": "replace", "path": ["tokens", idx, attr, loc], "fix": sug}
            elif sug.startswith("{"):
                try:
                    d = json.loads(sug)
                    if isinstance(d, dict) and {"en", "pt-BR"} & set(d):
                        op = {"mode": "locale_note", "path": ["tokens", idx, attr], "fix": d}
                except json.JSONDecodeError:
                    pass
        if not op:
            skipped.append({"slug": o["slug"], "field": field, "severity": o["severity"],
                            "why": "unresolvable field path", "reason": o["reason"][:200]})
            continue
        op.update({"field": field, "severity": o["severity"], "issue": o["reason"][:400],
                   "src_round": args.round})
        by_slug.setdefault(o["slug"], []).append(op)

    out = [{"slug": s, "ops": ops} for s, ops in sorted(by_slug.items())]
    (FD / "phase3_audit_repairs.json").write_text(json.dumps(
        {"note": f"Supplemental repair ops distilled from diff-audit round {args.round}. These finish "
                 f"partially-applied fixes (locale halves, stale clauses, stale literals) using the value "
                 f"each auditor supplied. Applied on TOP of the base patch by the renderer.",
         "sentences": out, "skipped": skipped}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"repair ops: {sum(len(s['ops']) for s in out)} over {len(out)} sentences")
    print(f"skipped (need authoring): {len(skipped)}  "
          f"{dict(Counter(s['severity'] for s in skipped))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
