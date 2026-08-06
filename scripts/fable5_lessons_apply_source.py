#!/usr/bin/env python3
"""Apply the Phase-6 lesson patch to the DURABLE SOURCE (research/derived/lessons/<slug>.json).

The first attempt wrote these fixes into the DB. That was the wrong layer: load_lessons.py re-authors every
lesson from these JSON files, so DB edits are wiped on the next load and never reach the committed
artifact. It also corrupted structured fields, because `objectives` is a LIST, `answer` is an OBJECT
({choices, correct}) and `body` is custom-element markup - a blind substring replace broke all three
(133 lesson errors, one unparseable JSON list, nested <jp>, stray </text>).

This applier is structure-aware per field:
    body                     markup string; substring replace, then a TAG-BALANCE check that compares the
                             open/close tag multiset before and after. Any change in balance = reject.
    title | description      plain string; substring replace.
    objectives[i]            list; the element is located BY CONTENT (the one containing `current`), never
                             by the finding's index, which refers to the finder's own numbering.
    exercises[i].prompt      string on the exercise object, located by ord.
    exercises[i].explanation string.
    exercises[i].answer      OBJECT: the anchor is matched against answer["correct"] or an element of
                             answer["choices"], and only that leaf is rewritten. The dict shape is never
                             replaced wholesale.

Plus the guards every earlier phase needed: instruction-shaped fixes are refused, em-dash rationales are
truncated, and a missing anchor is a skip rather than a wholesale overwrite.

Writes the JSON files in place; run load_lessons.py + validate_lessons.py afterwards.
Usage: fable5_lessons_apply_source.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"
LESSONS = ROOT / "research" / "derived" / "lessons"
INSTRUCTION = re.compile(
    r"^(replace|change|set|update|remove|delete|drop|add|apply|keep|rewrite|fix|minimal|split|trocar|"
    r"corrigir|no body|just |only )\b|->|→|\bshould be\b|\bmust be\b", re.I)
TAG = re.compile(r"</?([a-zA-Z][\w-]*)")


def tag_balance(s: str) -> Counter:
    return Counter(re.findall(r"</?([a-zA-Z][\w-]*)[^>]*>", s))


def tag_spans(s: str) -> Counter:
    """Every literal <...> span. Balance alone is not enough: a replacement can leave the tag COUNT
    unchanged while injecting prose INSIDE a tag, which is how Portuguese ended up as <jp> attributes
    ("unknown attribute 'período'"). If the fix contains no markup, every tag span must be untouched."""
    return Counter(re.findall(r"<[^>]*>", s))


def clean(fix: str):
    fix = (fix or "").strip()
    if not fix or INSTRUCTION.search(fix):
        return None, "fix is an instruction, not a value"
    if "—" in fix:
        fix = fix.split("—")[0].rstrip()
        if not fix:
            return None, "fix was only an em-dash rationale"
    return fix, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    conf = [f for f in json.loads((FD / "phase6_lessons_partial.json").read_text(encoding="utf-8"))["findings"]
            if f["verdict"] == "confirmed" and f.get("kind") == "lesson"]
    by_slug: dict = {}
    for f in conf:
        by_slug.setdefault(f["slug"], []).append(f)

    applied, skipped = Counter(), []
    for slug, findings in sorted(by_slug.items()):
        fp = LESSONS / (slug.split(":", 1)[1] + ".json")
        if not fp.exists():
            skipped += [(slug, f["field"], "lesson file not found") for f in findings]
            continue
        rec = json.loads(fp.read_text(encoding="utf-8"))
        dirty = False
        for f in findings:
            field, cur = f["field"], (f.get("current") or "")
            fix, why = clean(f.get("fix"))
            if why:
                skipped.append((slug, field, why)); continue
            base = field.split("[")[0]

            if base in ("title", "description") and "[" not in field:
                stored = rec.get(base) or ""
                if cur and cur not in stored:
                    skipped.append((slug, field, "anchor not found")); continue
                rec[base] = stored.replace(cur, fix, 1) if cur else fix
                applied.update([base]); dirty = True

            elif base == "body":
                stored = rec.get("body") or ""
                if not cur or cur not in stored:
                    skipped.append((slug, field, "anchor not found")); continue
                new = stored.replace(cur, fix, 1)
                if tag_balance(new) != tag_balance(stored):
                    skipped.append((slug, field, "would change markup tag balance")); continue
                if "<" not in fix and tag_spans(new) != tag_spans(stored):
                    skipped.append((slug, field, "plain-text fix would alter a tag's contents")); continue
                rec["body"] = new
                applied.update(["body"]); dirty = True

            elif base == "objectives":
                objs = rec.get("objectives") or []
                # locate BY CONTENT: the finder's index is its own numbering, not necessarily ours
                hit = next((k for k, o in enumerate(objs) if cur and cur in o), None)
                if hit is None:
                    skipped.append((slug, field, "objective anchor not found")); continue
                objs[hit] = objs[hit].replace(cur, fix, 1)
                applied.update(["objectives"]); dirty = True

            elif base == "exercises":
                m = re.match(r"exercises\[(\d+)\]\.(prompt|explanation|answer)$", field)
                if not m:
                    skipped.append((slug, field, "unmapped exercise sub-field")); continue
                idx, sub = int(m.group(1)), m.group(2)
                exs = rec.get("exercises") or []
                if idx >= len(exs):
                    skipped.append((slug, field, f"no exercise at index {idx}")); continue
                ex = exs[idx]
                if sub in ("prompt", "explanation"):
                    stored = ex.get(sub) or ""
                    if cur and cur not in stored:
                        skipped.append((slug, field, "anchor not found")); continue
                    ex[sub] = stored.replace(cur, fix, 1) if cur else fix
                    applied.update([f"exercise.{sub}"]); dirty = True
                else:
                    ans = ex.get("answer")
                    if not isinstance(ans, dict):
                        skipped.append((slug, field, "answer is not an object")); continue
                    # rewrite only the matching LEAF, never the dict
                    if cur and isinstance(ans.get("correct"), str) and cur in ans["correct"]:
                        ans["correct"] = ans["correct"].replace(cur, fix, 1)
                    elif cur and isinstance(ans.get("choices"), list) and \
                            any(isinstance(c, str) and cur in c for c in ans["choices"]):
                        ans["choices"] = [c.replace(cur, fix, 1) if isinstance(c, str) and cur in c else c
                                          for c in ans["choices"]]
                    else:
                        skipped.append((slug, field, "answer anchor not found in correct/choices")); continue
                    applied.update(["exercise.answer"]); dirty = True
            else:
                skipped.append((slug, field, "unmapped lesson field"))

        if dirty and not args.dry_run:
            fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (FD / "phase6_source_skipped.json").write_text(json.dumps(
        {"note": "Phase-6 lesson findings NOT applied to the JSON source; each needs an authoring pass.",
         "skipped": [{"slug": s, "field": f, "why": w} for s, f, w in skipped]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"lesson SOURCE apply ({'dry-run' if args.dry_run else 'APPLIED'}): "
          f"{sum(applied.values())} fields {dict(applied)}")
    print(f"skipped: {len(skipped)} {dict(Counter(w for _, _, w in skipped).most_common(6))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
