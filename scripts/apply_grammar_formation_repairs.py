#!/usr/bin/env python3
"""Apply the repair pass to the 50 withheld roadmap-E formation points.

Those 50 were withheld because a verification pass EXECUTED their step sequences and found they either
generate an ungrammatical form or contradict the record's own text. A repair pass re-authored each with
the finding in hand, and two fresh checkers re-executed the results. Outcome:

    fixed        20   the defect was expressible and is now expressed
    partial      14   the safe bases are encoded and the unsafe ones named in steps_unavailable
    unavailable  16   the restriction is real and the closed enums cannot carry it

The 16 `unavailable` are not failures. The clearest are があります / がいます / gp-12 / gp-13, whose entire
content is an ANIMACY split (学生がいます but 本があります) that the base enum -- verb, i-adjective,
na-adjective, noun, clause, any -- has no value for. Any noun-accepting rule licenses the exact error
those records exist to prevent, so a stated reason is the correct output and the spec says so.

ONE REPAIR IS CORRECTED HERE RATHER THAN MERGED AS WRITTEN.

gram:gp-24 (the negative of an i-adjective) was withheld because the general rule `replace-ending くない`
generates いくない from いい, which the record explicitly forbids ("いい é irregular, vira よくない, nunca
いくない"). The repair added a second variant, `replace-ending いい→よくない`, and both checkers rejected
it -- correctly, and for a reason worth recording:

    An arrow token in this corpus is a SUFFIX rewrite. Every arrow already merged is a single kana and
    therefore suffix-safe (い→さ, て→ちゃ, で→じゃ, て→とく, て→ちゃう). いい is the first two-kana arrow,
    and it is not: executed on 可愛い / かわいい -- an n5 entry in this very corpus -- it strips the いい
    and emits *かわよくない. The withheld rule it replaces produced かわいくない, which is correct. So the
    repair removed one bad form and introduced another.

The fix, which both checkers converged on, is to drop the exception variant entirely and let
`to-adverbial` carry it. That op is lexicon-mediated everywhere else in the campaign -- to-nai-stem
carries 買う→買わない and くる→こない, to-ta-form carries 行く→行った -- so to-adverbial returns よく for
いい, and variant 1 alone yields よくない. gram:i-adjectives, gp-35, gp-62 and gp-81 all encode the stem
that way already.

Usage: apply_grammar_formation_repairs.py [--apply]
"""
from __future__ import annotations
import argparse, collections, glob, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
REPAIRS = ROOT / "research" / "derived" / "grammar_formation_repair"
WITHHELD = ROOT / "research" / "derived" / "grammar_formation_withheld.json"

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

# An arrow token is a SUFFIX rewrite, so a multi-kana left side fires on any word ending that way.
# Refused outright rather than merged: this is how gp-24's repair turned 可愛い into *かわよくない.
MAX_ARROW_LHS = 1


def correct_gp24(p: dict) -> tuple[dict, str | None]:
    """Drop the いい→よくない exception variant; see the module docstring."""
    keep = [v for v in (p.get("variants") or [])
            if not any("いい→" in (st.get("token") or "") for st in (v.get("steps") or []))]
    if len(keep) == len(p.get("variants") or []):
        return p, None
    p = {**p, "variants": keep}
    return p, ("The いい exception is carried by to-adverbial, which is lexicon-mediated (いい -> よく) "
               "as it is throughout this campaign, rather than by an arrow token: `replace-ending` "
               "arrows are SUFFIX rewrites, and いい→よくない fires on any adjective ending in いい, "
               "turning 可愛い into かわよくない.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    repairs: dict[str, dict] = {}
    for f in sorted(glob.glob(str(REPAIRS / "batch-*.json"))):
        for p in json.loads(Path(f).read_text(encoding="utf-8"))["points"]:
            repairs[p["slug"]] = p
    withheld = {r["slug"] for r in json.loads(WITHHELD.read_text(encoding="utf-8"))["rows"]}
    con = sqlite3.connect(DB)
    known = {s for (s,) in con.execute("SELECT slug FROM grammar_point")}

    stats, writes, refused = collections.Counter(), [], []
    for slug, p in sorted(repairs.items()):
        if slug not in known:
            stats["slug not in the registry"] += 1
            continue
        if slug not in withheld:
            stats["not a withheld point -- skipped"] += 1
            continue
        note = None
        if slug == "gram:gp-24":
            p, note = correct_gp24(p)
            if note:
                stats["corrected before merge"] += 1

        variants = p.get("variants") or []
        problems = []
        for v in variants:
            if v.get("base") not in BASES:
                problems.append(f"base {v.get('base')!r}")
            for st in v.get("steps") or []:
                if st.get("op") not in OPS:
                    problems.append(f"op {st.get('op')!r}")
                tok = st.get("token") or ""
                if "→" in tok and len(tok.split("→")[0]) > MAX_ARROW_LHS:
                    # The gp-24 defect, generalised into a gate so it cannot recur silently.
                    problems.append(f"multi-kana arrow {tok!r} is a suffix rewrite")
        if problems:
            refused.append({"slug": slug, "why": "; ".join(sorted(set(problems))),
                            "variants": variants})
            stats["REFUSED (enum or arrow)"] += 1
            continue

        reason = (p.get("steps_unavailable") or "").strip() or None
        if note:
            reason = (reason + " " if reason else "") + note
        tags = [t for t in (p.get("nuance_tags") or []) if t in NUANCE]
        ctxs = [c for c in (p.get("usage_contexts") or []) if c in CONTEXTS]
        if not variants and not reason:
            reason = ("The record does not state a formation precisely enough to give machine-usable "
                      "steps.")
        writes.append((slug, {"variants": variants} if variants else None, tags, ctxs, reason))
        stats[p.get("resolution", "?")] += 1

    print(f"repairs on disk {len(repairs)}; withheld points {len(withheld)}")
    for k, v in stats.most_common():
        print(f"  {k}: {v}")
    for r in refused:
        print(f"  [REFUSED] {r['slug']}: {r['why']}")

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
    n = con.execute("SELECT COUNT(*) FROM grammar_point "
                    "WHERE formation_steps_json IS NOT NULL").fetchone()[0]
    w = con.execute("SELECT COUNT(*) FROM grammar_point "
                    "WHERE steps_unavailable LIKE 'WITHHELD%'").fetchone()[0]
    print(f"\nsteps now on {n} points; still marked WITHHELD: {w}")
    print("NEXT: scripts/export/export_corpus.py")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
