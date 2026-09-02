#!/usr/bin/env python3
"""Merge roadmap E: formation_steps / nuance_tags / usage_contexts onto the grammar points.

WHAT DOES NOT GET MERGED, AND WHY THAT IS THE POINT.

Two independent checkers ran per batch, and the first one was told to EXECUTE each step sequence against
書く / 食べる / する / くる / 高い / 静か / 学生 and write down what came out, rather than judge it by eye.
That is what turned an authoring task into a test, and it worked: 157 problems over 101 of the 495
points, 41 of them critical, meaning the sequence generates something ungrammatical for a base it claims
to accept. A sample of what execution caught that reading would not have:

  gram:ga-arimasu  base "noun" + append があります. Run on 学生 it gives 学生があります -- which is the
                   single error the record exists to prevent ("the classic mistake by Portuguese
                   speakers is to use あります for people and animals"). The animacy split IS the point,
                   and the closed base enum has no animate/inanimate value, so the honest output was
                   steps_unavailable, not a rule that licenses the mistake.
  gram:gp-12/13    the same defect mirrored: 学生がある, and 本がいる -- which additionally parses as
                   本が要る, "I need a book", so a drill generator emits a real sentence with the wrong
                   meaning.
  gram:gp-24       i-adjective replace-ending くない, applied to いい, produces いくない. The record's own
                   formation says in as many words: "いい is irregular, becomes よくない, never いくない."
  gram:gp-41       [to-ta-form, append り] yields 飲んだり and stops. The record's structure_pattern is
                   たり〜たりする and its nuance warns that dropping the する "sounds incomplete".
  gram:gp-7        to-nai-stem is used with the opposite sense from the op enum's own worked example;
                   50 of the 61 to-nai-stem variants in the campaign assume the な-inclusive stem, so
                   this one would generate *書かければいけない.

So the merge WITHHOLDS steps for any point where both checkers raised a problem, or where either raised
a critical one. 50 points. They are written to the review file with the finding attached, and the point
keeps a steps_unavailable reason instead of a rule -- which is exactly what the authoring spec asks for
when a formation cannot be stated safely: "a confidently wrong formation rule is the worst output this
task can produce."

Merging the flagged points and fixing them later is the tempting alternative and is wrong. A formation
rule is consumed by generators; a wrong one does not sit inertly in a file, it manufactures wrong
Japanese for as long as it is there.

Usage: merge_grammar_formation.py [--apply]
"""
from __future__ import annotations
import argparse, collections, glob, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
BATCHES = ROOT / "research" / "derived" / "grammar_formation"
JOURNAL = (Path.home() / ".claude" / "projects"
           / "C--Users-WiseWolf-IdeaProjects-code-yomineko-research"
           / "3753f676-cff8-4755-849b-fab3c4cc0baa" / "subagents" / "workflows"
           / "wf_05e350b5-201" / "journal.jsonl")
PROBLEMS = ROOT / "research" / "derived" / "grammar_formation_problems.json"
REVIEW = ROOT / "research" / "derived" / "grammar_formation_withheld.json"

OPS = {"to-te-form", "to-masu-stem", "to-nai-stem", "to-ta-form", "to-dictionary", "to-volitional",
       "to-potential", "to-passive", "to-causative", "to-conditional-ba", "to-adverbial",
       "to-attributive", "nominalize", "append", "replace-ending", "drop-final-ru", "none"}
BASES = {"verb", "i-adjective", "na-adjective", "noun", "clause", "any"}
NUANCE = {"emphasis", "softening", "conjecture", "obligation", "permission", "prohibition", "hearsay",
          "comparison", "cause", "condition", "concession", "intention", "desire", "request",
          "experience", "change-of-state", "continuation", "completion", "politeness", "humility",
          "honorific"}
CONTEXTS = {"spoken", "written", "business", "casual-friends", "formal-email", "academic",
            "announcement", "literary"}


def load_problems() -> list[dict]:
    if PROBLEMS.exists():
        return json.loads(PROBLEMS.read_text(encoding="utf-8"))["problems"]
    probs: list[dict] = []
    for line in JOURNAL.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "result":
            continue
        v = d.get("value") or d.get("result")
        if isinstance(v, dict) and v.get("problems"):
            probs += v["problems"]
    PROBLEMS.write_text(json.dumps(
        {"note": "Every problem the two per-batch checkers raised against the roadmap-E formation "
                 "steps. The first checker EXECUTES each sequence against 書く/食べる/する/くる/高い/"
                 "静か/学生 rather than judging by eye, which is why `bad_output` carries the actual "
                 "ungrammatical form it generated.",
         "count": len(probs), "problems": probs}, ensure_ascii=False, indent=1), encoding="utf-8")
    return probs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    probs = load_problems()
    by_slug: dict[str, list[dict]] = collections.defaultdict(list)
    for p in probs:
        by_slug[p["slug"]].append(p)
    agreed = {s for s, v in by_slug.items() if len(v) >= 2}
    critical = {s for s, v in by_slug.items() if any(x.get("severity") == "critical" for x in v)}
    withhold = agreed | critical

    points: dict[str, dict] = {}
    for f in sorted(glob.glob(str(BATCHES / "batch-*.json"))):
        for p in json.loads(Path(f).read_text(encoding="utf-8"))["points"]:
            points[p["slug"]] = p

    con = sqlite3.connect(DB)
    known = {s for (s,) in con.execute("SELECT slug FROM grammar_point")}

    stats = collections.Counter()
    writes, withheld = [], []
    for slug, p in points.items():
        if slug not in known:
            stats["slug not in the grammar registry"] += 1
            continue
        variants = p.get("variants") or []
        reason = (p.get("steps_unavailable") or "").strip()

        if slug in withhold:
            found = by_slug[slug]
            worst = "critical" if slug in critical else "agreed"
            why = found[0].get("issue", "")[:400]
            withheld.append({"slug": slug, "verdict": worst,
                             "problems": len(found),
                             "bad_output": next((x.get("bad_output") for x in found
                                                 if x.get("bad_output")), None),
                             "issue": why, "withheld_variants": variants})
            writes.append((slug, None, p.get("nuance_tags"), p.get("usage_contexts"),
                           f"WITHHELD ({worst}): the verification pass found this formation generates "
                           f"a wrong form or contradicts the record's own text. See "
                           f"research/derived/grammar_formation_withheld.json."))
            stats[f"withheld ({worst})"] += 1
            continue

        # enum conformance on what we DO merge
        bad = []
        for v in variants:
            if v.get("base") not in BASES:
                bad.append(f"base {v.get('base')!r}")
            for st in v.get("steps") or []:
                if st.get("op") not in OPS:
                    bad.append(f"op {st.get('op')!r}")
        tags = [t for t in (p.get("nuance_tags") or []) if t in NUANCE]
        ctxs = [c for c in (p.get("usage_contexts") or []) if c in CONTEXTS]
        if bad:
            stats["off-enum, withheld"] += 1
            withheld.append({"slug": slug, "verdict": "off-enum", "problems": 0,
                             "issue": "; ".join(sorted(set(bad))), "withheld_variants": variants})
            writes.append((slug, None, tags, ctxs, "WITHHELD: off-enum values in the steps."))
            continue

        if variants:
            stats["steps merged"] += 1
            writes.append((slug, {"variants": variants}, tags, ctxs, reason or None))
        else:
            stats["no steps (steps_unavailable)"] += 1
            writes.append((slug, None, tags, ctxs,
                           reason or "The record does not state a formation precisely enough to give "
                                     "machine-usable steps."))

    # The campaign ran 33 batches of 15 = 495, and the registry holds 496. The last point was never
    # in anyone's range. Recorded as the coverage gap it is rather than hand-authored here: a formation
    # rule written outside the campaign is a rule no checker ever executed, which is the one thing this
    # whole pipeline exists to prevent.
    unauthored = sorted(known - set(points))
    for slug in unauthored:
        writes.append((slug, None, None, None,
                       "NOT AUTHORED: the roadmap-E campaign covered 495 of the 496 registered points "
                       "(33 batches of 15) and this one fell outside every batch range. This is a "
                       "coverage gap, not a judgement that the record is too vague to state."))
        stats["not authored (coverage gap)"] += 1

    print(f"points authored {len(points)}   problems {len(probs)} over {len(by_slug)} points")
    print(f"  both checkers agreed: {len(agreed)}   any critical: {len(critical)}   "
          f"withhold union: {len(withhold)}")
    for k, v in stats.most_common():
        print(f"  {k}: {v}")

    REVIEW.write_text(json.dumps(
        {"note": "Grammar points whose formation steps were NOT merged. A point lands here when both "
                 "checkers raised a problem, or either raised a critical one -- critical meaning the "
                 "sequence, executed literally, produced an ungrammatical form. They carry a "
                 "steps_unavailable reason in the corpus instead of a rule, because a wrong formation "
                 "rule does not sit inertly in a file: it manufactures wrong Japanese in every "
                 "generator that reads it.",
         "count": len(withheld), "rows": withheld}, ensure_ascii=False, indent=1), encoding="utf-8")

    if not args.apply:
        print("\npre-flight only. re-run with --apply to write.")
        return 0
    for slug, steps, tags, ctxs, reason in writes:
        con.execute(
            "UPDATE grammar_point SET formation_steps_json=?, nuance_tags_json=?, "
            "usage_contexts_json=?, steps_unavailable=?, needs_review=1 WHERE slug=?",
            (json.dumps(steps, ensure_ascii=False) if steps else None,
             json.dumps(tags, ensure_ascii=False) if tags else None,
             json.dumps(ctxs, ensure_ascii=False) if ctxs else None,
             reason, slug))
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM grammar_point WHERE formation_steps_json IS NOT NULL").fetchone()[0]
    u = con.execute("SELECT COUNT(*) FROM grammar_point WHERE steps_unavailable IS NOT NULL").fetchone()[0]
    print(f"\nsteps on {n} points; a stated reason on {u}")
    print("NEXT: scripts/export/export_corpus.py")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
