#!/usr/bin/env python3
"""Merge roadmap F into the corpus: pattern[] and clause_structure onto every sentence record.

Until now roadmap F lived entirely in research/derived — the mechanical patterns from
build_sentence_patterns.py and the clause classification from the sentence-clause-structure workflow.
Neither reached corpus/, so nothing could consume them but the role-drill builder. This writes both onto
the sentence row (migration 007) so the exporter carries them into corpus/sentences/bank.json.

  pattern_json      Layer B. Mechanical, regenerable, no AI: chunks from the token array, roles from
                    the (particle, function_type) pair closing each chunk.
  clause_structure  Layer C. One closed-enum value per sentence, judged from the Japanese by the
                    classification pass and checked by an adversarial pass.

THE THIRTEEN DISPUTES. One checker ran per batch, so the project's usual "act only on what two
independent checkers both raise" rule had nothing to lean on. What these disputes offered instead was
better: each argued from CONSISTENCY, naming other sentences in the same corpus that carry a different
tag for the same construction. That is a factual claim, so each was checked against the data rather than
weighed as an opinion. Ten survived, three did not:

  APPLIED (10)
    tatoeba-83446    coordinate     -> topic-comment   音をたてて is manner-adverbial, not a 2nd clause
    tatoeba-82850    topic-comment  -> quote           〜ように言った reports an utterance
    tatoeba-156847   topic-comment  -> quote           same construction as 82850; both move together
    tatoeba-3224399  simple         -> coordinate      て-linked predicates; `simple` says "one clause"
    gen-befc3de4a763 topic-comment  -> coordinate      いそがしくて + 来られません, two predications
    tatoeba-10073519 cause          -> simple          から+な is sentence-final; there is no consequent
    tatoeba-11268120 simple         -> topic-comment   これからは is a topicalized frame, so not "no topic"
    tatoeba-79947    simple         -> imperative      〜のよ softened command
    tatoeba-126322   cause          -> simple          医学研究のために is a purpose PP, not a reason clause
    tatoeba-149179   cause          -> topic-comment   会議のために likewise; 社長は…集めた governs

  The last two were the interesting ones. Their cited siblings scored 0/1 by naive citation-counting,
  because the checker cited them as CONTRAST ("that one is a real ため clause, unlike this") and a script
  that reads every citation as support gets those exactly backwards. Surveying the construction across
  all 5,825 rows settled it: noun-anchored ために is tagged simple/topic-comment 6 times against cause
  twice, and both cause rows are these two.

  NOT APPLIED (3) — recorded in research/derived/clause_structure_review.json
    tatoeba-151104   conditional -> simple           〜ないといけない is a fossilised obligation ending, so
                     the `conditional` tag is wrong -- but 通るには blurs whether the replacement is
                     `simple` (defined as "no topic marker") or topic-comment. A convention call.
    gen-cfad03e05b7b simple -> subordinate-time      The dispute claimed the corpus "applies the opposite
    gen-61a8f1420692 simple -> subordinate-time      rule everywhere else". It does not: 8 of 9
                     noun-anchored あと rows are NOT subordinate-time, and noun-anchored 前 splits
                     13 simple / 5 topic-comment / 3 imperative / 2 subordinate-time, confounded by the
                     spatial 前 of 駅の前 sharing a surface with the temporal 前 of ごはんの前. There IS
                     a real inconsistency here (夕飯の後で is subordinate-time while 事故のあと is
                     simple), but it is a convention to decide, not a fact to apply, and inventing one
                     now would split the 〜あとで drill pool on a coin flip.

Usage: merge_sentence_structure.py [--apply]
"""
from __future__ import annotations
import argparse, glob, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
PATTERNS = ROOT / "research" / "derived" / "sentence_patterns.json"
BATCHES = ROOT / "research" / "derived" / "clause_structure"
REVIEW = ROOT / "research" / "derived" / "clause_structure_review.json"

ENUM = {"simple", "topic-comment", "relative-clause", "conditional", "quote", "cause",
        "coordinate", "subordinate-time", "question", "imperative", "fragment"}

# Verified disputes, applied. slug -> corrected value.
APPLY = {
    "sent:tatoeba-83446": "topic-comment",
    "sent:tatoeba-82850": "quote",
    "sent:tatoeba-156847": "quote",
    "sent:tatoeba-3224399": "coordinate",
    "sent:gen-befc3de4a763": "coordinate",
    "sent:tatoeba-10073519": "simple",
    "sent:tatoeba-11268120": "topic-comment",
    "sent:tatoeba-79947": "imperative",
    "sent:tatoeba-126322": "simple",
    "sent:tatoeba-149179": "topic-comment",
}
# Raised, not applied — a convention decision rather than a fact. Kept as data, not dropped.
HOLD = {
    "sent:tatoeba-151104": ("conditional", "simple",
                            "〜ないといけない is a fossilised obligation ending, so `conditional` is "
                            "wrong; but 通るには leaves simple-vs-topic-comment undecided."),
    "sent:gen-cfad03e05b7b": ("simple", "subordinate-time",
                              "noun+のあと: corpus splits 8-to-1 AGAINST subordinate-time, so the "
                              "dispute's premise is false, but 夕飯の後で is tagged subordinate-time "
                              "and the two disagree. Needs one convention."),
    "sent:gen-61a8f1420692": ("simple", "subordinate-time",
                              "noun+の前に: 13 simple / 5 topic-comment / 3 imperative / 2 "
                              "subordinate-time, confounded by spatial 前 sharing the surface."),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    known = {slug for (slug,) in con.execute("SELECT slug FROM sentence")}

    clause: dict[str, str] = {}
    for f in sorted(glob.glob(str(BATCHES / "batch-*.json"))):
        for r in json.loads(Path(f).read_text(encoding="utf-8"))["rows"]:
            clause[r["slug"]] = r["clause_structure"]
    patterns = {s["slug"]: s["pattern"]
                for s in json.loads(PATTERNS.read_text(encoding="utf-8"))["sentences"]}

    bad = {s: v for s, v in clause.items() if v not in ENUM}
    missing = {s for s in clause if s not in known} | {s for s in patterns if s not in known}
    for slug, fixed in APPLY.items():
        if slug not in clause:
            print(f"  WARN {slug}: dispute target not in the classification"); continue
        clause[slug] = fixed

    print(f"clause_structure : {len(clause)} sentences   pattern: {len(patterns)}")
    print(f"  applied disputes: {len(APPLY)}   held for review: {len(HOLD)}")
    print("  " + "  ".join(f"{k}={v}" for k, v in Counter(clause.values()).most_common()))
    if bad:
        print(f"  ERROR off-enum values: {bad}")
        return 1
    if missing:
        print(f"  ERROR {len(missing)} slugs not in the bank: {list(missing)[:5]}")
        return 1

    REVIEW.write_text(json.dumps(
        {"note": "clause_structure disputes RAISED by the adversarial pass and deliberately NOT "
                 "applied: each is a convention to decide, not a fact to apply. Kept as data so the "
                 "decision is made once, on purpose, rather than rediscovered.",
         "count": len(HOLD),
         "rows": [{"slug": s, "assigned": a, "proposed": p, "why": w} for s, (a, p, w) in HOLD.items()]},
        ensure_ascii=False, indent=1), encoding="utf-8")

    if not args.apply:
        print("\npre-flight only. re-run with --apply to write.")
        return 0
    for slug, pat in patterns.items():
        con.execute("UPDATE sentence SET pattern_json=? WHERE slug=?",
                    (json.dumps(pat, ensure_ascii=False), slug))
    for slug, cs in clause.items():
        con.execute("UPDATE sentence SET clause_structure=? WHERE slug=?", (cs, slug))
    con.commit()
    n_p = con.execute("SELECT COUNT(*) FROM sentence WHERE pattern_json IS NOT NULL").fetchone()[0]
    n_c = con.execute("SELECT COUNT(*) FROM sentence WHERE clause_structure IS NOT NULL").fetchone()[0]
    print(f"\nwrote pattern_json on {n_p}, clause_structure on {n_c}")
    print("NEXT: scripts/export/export_corpus.py")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
