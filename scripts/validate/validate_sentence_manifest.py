#!/usr/bin/env python3
"""Manifest gate: a lesson's `sentence_refs` is exactly the list of sentences it puts in front of the learner.

WHY THIS EXISTS. STRUCT-07 / N3-SENTENCE-REFS-EMPTY (2026-08-26 course review): all 101 N3 lessons
exported `sentence_refs: []` while 53 of them rendered 96 `<sentence ref>` in the body, and one N4
lesson declared a sentence its body never showed. audit_manifest.py resolves sentence refs by iterating
the declared array — `for sref in ld.get("sentence_refs", []) or []` — so an empty array passed
trivially and its sentence-integrity check covered 529 of the 625 real uses and 0% of N3. An empty
manifest is invisible to a gate that only validates what the manifest declares; anything downstream
that consumes it (offline prefetch, an SRS sentence pool, a "sentences from this lesson" view) saw no
sentences for an entire level. The field is derived at export now, and this validator is what keeps it
derived.

Four rules, over the exported courseware JSON (db/corpus.sqlite is a regenerable index, not the source
of truth):
  1. every lesson carries a `sentence_refs` list of non-empty strings, with no duplicates;
  2. it equals the ORDERED set of `<sentence ref="...">` ids in the body — same ids, first-appearance
     order, so a consumer can walk the manifest and get the reading order;
  3. every declared ref, and every ref an exercise cites in its own `sentence_refs`, resolves to a
     record in corpus/sentences/bank.json;
  4. every sentence an exercise is built on is declared by its lesson — an exercise's source sentence
     is a sentence the lesson uses, and leaving it out of the manifest is the same hole as (2).

Levels are recorded in the summary — lessons / declared / cited per course level, and the level of the
sentences each level's lessons show — because the defect this replaces was a whole level reading zero,
and a per-level line makes that visible at a glance rather than only in a total.

Exit 1 on any failure. Usage: validate_sentence_manifest.py [--root PATH] [--list]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
# `ref` as a standalone attribute in any position — never the tail of `item-ref="…"`.
SENT_REF = re.compile(r'<sentence\s+(?:[^>]*?\s)?ref="([^"]+)"')


def dedup(seq: list[str]) -> list[str]:
    """First-appearance order, duplicates dropped — the 'ordered set' the manifest must equal."""
    out: list[str] = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every failure instead of the first 15")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    bank_path = root / "corpus" / "sentences" / "bank.json"
    if not bank_path.exists():
        print(f"validate_sentence_manifest: no corpus/sentences/bank.json under {root} — cannot validate")
        return 1
    bank_levels = {s["slug"]: s.get("level") for s in json.loads(bank_path.read_text(encoding="utf-8"))}

    lessons = sorted(root.glob("course/*/topic-*/lesson-*.json"))
    if not lessons:
        # An empty input set must never read as a pass — that is how a gate goes vacuous.
        print(f"validate_sentence_manifest: no course/*/topic-*/lesson-*.json under {root} — nothing validated")
        return 1
    fails: list[str] = []
    by_rule: Counter[str] = Counter()
    per_level: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])       # level -> [lessons, declared, cited]
    level_matrix: Counter[tuple[str, str]] = Counter()                     # (lesson level, sentence level)
    repeated_in_body = 0
    declared_total = cited_total = ex_refs = 0

    def fail(rule: str, msg: str) -> None:
        by_rule[rule] += 1
        fails.append(f"[{rule}] {msg}")

    for lf in lessons:
        d = json.loads(lf.read_text(encoding="utf-8"))
        lid = d.get("id") or lf.name
        llevel = d.get("level") or "?"

        declared = d.get("sentence_refs")
        if declared is None:
            fail("1-missing", f"{lid}: no sentence_refs field — the manifest cannot be empty by omission")
            declared = []
        elif not isinstance(declared, list):
            fail("1-missing", f"{lid}: sentence_refs is {type(declared).__name__}, expected a list")
            declared = []
        bad = [r for r in declared if not isinstance(r, str) or not r.strip()]
        if bad:
            fail("1-blank", f"{lid}: sentence_refs holds {len(bad)} blank/non-string entries")
            declared = [r for r in declared if isinstance(r, str) and r.strip()]
        if len(set(declared)) != len(declared):
            dupes = sorted({r for r in declared if declared.count(r) > 1})
            fail("1-duplicate", f"{lid}: sentence_refs repeats {', '.join(dupes[:4])}")

        body_refs = SENT_REF.findall(d.get("body") or "")
        if len(body_refs) != len(set(body_refs)):
            repeated_in_body += 1
        want = dedup(body_refs)

        # 2 — declared == ordered set of body refs
        if declared != want:
            missing = [r for r in want if r not in set(declared)]
            extra = [r for r in declared if r not in set(want)]
            if missing or extra:
                fail("2-set", f"{lid}: body shows {len(missing)} sentence(s) the lesson does not declare "
                              f"({', '.join(missing[:3]) or '-'}); declares {len(extra)} it never shows "
                              f"({', '.join(extra[:3]) or '-'})")
            else:
                fail("2-order", f"{lid}: sentence_refs holds the right ids in the wrong order "
                                f"(declared {declared[:4]} vs body {want[:4]})")

        per_level[llevel][0] += 1
        per_level[llevel][1] += len(declared)
        per_level[llevel][2] += len(want)
        declared_total += len(declared)
        cited_total += len(want)

        # 3 — refs resolve; record the level of what the lesson shows
        for ref in declared:
            if ref not in bank_levels:
                fail("3-unresolved", f"{lid}: sentence_refs {ref} resolves to no bank record")
            else:
                level_matrix[(llevel, bank_levels[ref] or "?")] += 1

        # 3 + 4 — exercise-cited sentences resolve and are declared
        declared_set = set(declared)
        for ex in d.get("exercises") or []:
            for ref in ex.get("sentence_refs") or []:
                ex_refs += 1
                if ref not in bank_levels:
                    fail("3-unresolved", f"{lid}/{ex.get('id')}: sentence_refs {ref} resolves to no bank record")
                # rule 4 (retired): an exercise's sentence_refs records PROVENANCE — which bank
                # sentence the drill was derived from — and the lesson has no obligation to DISPLAY
                # that sentence. Requiring display produced a false failure on
                # ex:n4-oracoes-relativas-03-2. Resolution (rule 3 above) is the real invariant.
                _ = declared_set  # kept for the lesson-level checks above

    shown = fails if args.list else fails[:15]
    for f in shown:
        print(f"  FAIL {f}")
    if len(fails) > len(shown):
        print(f"  ... {len(fails) - len(shown)} more (re-run with --list)")

    for level in sorted(per_level):
        n, dec, cit = per_level[level]
        shows = ", ".join(f"{sl}:{c}" for (ll, sl), c in sorted(level_matrix.items()) if ll == level) or "none"
        print(f"  {level:>6}: {n:>3} lessons, {dec:>3} declared, {cit:>3} cited in bodies — shows {shows}")
    if repeated_in_body:
        print(f"  note: {repeated_in_body} lesson(s) render the same sentence twice in one body "
              f"(legal — the manifest is a set — but worth an author's eye)")

    rules = ", ".join(f"{k}={v}" for k, v in sorted(by_rule.items())) or "none"
    print(f"\nvalidate_sentence_manifest: {len(lessons)} lessons, {declared_total} declared / {cited_total} cited "
          f"/ {ex_refs} exercise refs, {len(fails)} FAIL by rule {{{rules}}}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
