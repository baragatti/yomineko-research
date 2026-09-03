#!/usr/bin/env python3
"""Hard gate: every item the course TEACHES is exemplified in the sentence bank.

    vocabulary     >= 3 bank sentences whose `tokens[].vocab` names it
    grammar point  >= 5 bank sentences tagged with it

WHY THIS EXISTS
---------------
The two thresholds are spec §6's dissection standard restated as a coverage floor, and they had been
"P5 targets" printed by `scripts/validate/completeness_audit.py` since P5 — as two ADVISORY lines,
over `db/corpus.sqlite`, which is the git-ignored regenerable index rather than the committed JSON
CLAUDE.md names the source of truth. Two lines in an advisory report cannot fail a build, cannot name
the items that are short, and were counting a different artifact from the one that ships. A word can
therefore be unlocked in a lesson, printed on an SRS card, asked about in an exercise, and have not one
sentence in the corpus showing it in use, and every gate stays green.

This is that claim, over the EXPORT, as a gate, with the work list attached. The two advisory lines in
completeness_audit.py now point here and no longer pretend to be the check.

WHAT IS MEASURED, AND AGAINST WHAT
----------------------------------
TAUGHT is the union of `unlocks[]` over the 322 lesson leaves under `course/`, per kind — the same
published slug space `validate_unlock_ledger.py` and `audit_coverage.py` work in. A record the course
never teaches is not this gate's business: the registries carry N1/N2 bank rows no lesson references.

COUNTED is the sentence bank, `corpus/sentences/bank.json`:

  * vocab — DISTINCT sentences with a token whose `vocab` is that slug. The token dissection is the
    only link that survives the export; counting `jp` substrings instead would credit 表 for 表現 and
    い for 寒い, which is the tiling problem validate_practice_coverage.py had to solve and the reason
    this gate refuses to guess.
  * grammar — sentences whose `grammar[]` tags the point. The bank stores the point's KEY ("tte") and
    the registry publishes `gram:tte`, so the join goes through the registry's own `key` field; a tag
    that names no grammar point is a broken edge and FAILS, because a coverage number computed over
    links that do not resolve is fiction.

The LEVEL a shortfall is filed under is the record's OWN level, not the level of the lesson that
teaches it: a word is N3 vocabulary wherever it is front-loaded, and the campaign that fixes it (W12
orthographic relink, W13 N3 exemplification) is organised by the record's level.

THE RATCHET
-----------
1,763 of the 3,442 taught items are short today and 1,562 have no sentence at all, almost all of it
the N3 vocabulary the mined-stage pipeline has not reached (W13). A gate that failed on that would be
switched off within a day, so the per-(level, kind) shortfall is FROZEN in
`scripts/validate/sentence_coverage_baseline.json`: it may shrink, never grow. Teaching one more word
with no example fails the build; fixing one prints the new number and asks for the ceiling to be
lowered. Both counters are held — `below` (under the floor) and `zero` (no sentence at all) — because
they retire on different campaigns and collapsing them would let 40 items at zero hide inside a
shrinking `below`.

A (level, kind) the data produces with no ceiling FAILS, and a ceiling naming a (level, kind) the data
no longer produces FAILS: a ratchet nobody can falsify is a comment.

EMPTY INPUT FAILS
-----------------
Floors far below today's counts (200 lessons, 1,000 sentences, 2,000 vocab, 300 grammar, and taught
sets of 1,500 / 300) so growth never trips them, and a vanished bank, a moved course tree or a glob
that stopped matching fails instead of certifying a corpus of nothing.

Reads:  corpus/{vocab,grammar,sentences}/*.json, course/**/lesson-*.json — the export only.
Writes: research/reports/sentence_coverage_shortfall.json (only when its content changes; it is the
        W12/W13 work list), and sentence_coverage_baseline.json under --record.
Usage:  validate_sentence_coverage.py [--root PATH] [--record] [--list] [--kind vocab|grammar]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).resolve().parent / "sentence_coverage_baseline.json"
REPORT_REL = "research/reports/sentence_coverage_shortfall.json"

# The two thresholds. spec §6 / the P5 acceptance targets, restated as a gate.
FLOOR = {"vocab": 3, "grammar": 5}

# Empty-input floors — an order of magnitude under the real counts, so growth never trips them and a
# tree whose data moved cannot pass by having nothing to check.
MIN_LESSONS = 200
MIN_SENTENCES = 1_000
MIN_VOCAB = 2_000
MIN_GRAMMAR = 300
MIN_TAUGHT = {"vocab": 1_500, "grammar": 300}

MAX_REPORT = 20
LEVEL_ORDER = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]
UNKNOWN_LEVEL = "(unknown)"


def level_key(level: str) -> tuple[int, str]:
    return (LEVEL_ORDER.index(level) if level in LEVEL_ORDER else len(LEVEL_ORDER), level)


def jload(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_registries(root: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """(vocab slug -> level, grammar slug -> level, grammar key -> slug)."""
    vocab_level: dict[str, str] = {}
    for path in sorted(root.glob("corpus/vocab/*.json")):
        for rec in jload(path):
            if isinstance(rec, dict) and isinstance(rec.get("slug"), str):
                vocab_level[rec["slug"]] = rec.get("level") or UNKNOWN_LEVEL
    grammar_level: dict[str, str] = {}
    key_to_slug: dict[str, str] = {}
    for path in sorted(root.glob("corpus/grammar/*.json")):
        for rec in jload(path):
            if not isinstance(rec, dict) or not isinstance(rec.get("slug"), str):
                continue
            grammar_level[rec["slug"]] = rec.get("level") or UNKNOWN_LEVEL
            if isinstance(rec.get("key"), str):
                key_to_slug[rec["key"]] = rec["slug"]
            # A tag may equally be written as the published address; both resolve to one record.
            key_to_slug.setdefault(rec["slug"], rec["slug"])
    return vocab_level, grammar_level, key_to_slug


def count_bank(root: Path, key_to_slug: dict[str, str]) -> tuple[Counter, Counter, int, list[str]]:
    """Sentences per vocab slug and per grammar slug, plus unresolvable grammar tags."""
    bank_path = root / "corpus" / "sentences" / "bank.json"
    if not bank_path.exists():
        return Counter(), Counter(), 0, [f"{bank_path} does not exist"]
    bank = jload(bank_path)
    per_vocab: Counter = Counter()
    per_grammar: Counter = Counter()
    unresolved: Counter = Counter()
    for rec in bank:
        if not isinstance(rec, dict):
            continue
        # DISTINCT per sentence: 日 appearing in four tokens of one sentence is one example, not four.
        for slug in {t.get("vocab") for t in (rec.get("tokens") or [])
                     if isinstance(t, dict) and isinstance(t.get("vocab"), str)}:
            per_vocab[slug] += 1
        for tag in {g for g in (rec.get("grammar") or []) if isinstance(g, str)}:
            slug = key_to_slug.get(tag)
            if slug is None:
                unresolved[tag] += 1
                continue
            per_grammar[slug] += 1
    problems = [f"grammar tag {tag!r} on {n} bank sentence(s) names no grammar point — the edge is "
                f"broken and any coverage number over it is fiction"
                for tag, n in sorted(unresolved.items(), key=lambda kv: (-kv[1], kv[0]))]
    return per_vocab, per_grammar, len(bank), problems


def load_taught(root: Path) -> tuple[dict[str, dict[str, str]], int]:
    """kind -> {ref: the lesson id that unlocks it}. The published slug space, over the leaves."""
    taught: dict[str, dict[str, str]] = {"vocab": {}, "grammar": {}}
    n = 0
    for path in sorted(root.glob("course/**/lesson-*.json")):
        lesson = jload(path)
        if not isinstance(lesson, dict):
            continue
        n += 1
        lid = lesson.get("id") or path.stem
        for unlock in lesson.get("unlocks") or []:
            if not isinstance(unlock, dict):
                continue
            kind, ref = unlock.get("type"), unlock.get("ref")
            if kind in taught and isinstance(ref, str):
                taught[kind].setdefault(ref, str(lid))
    return taught, n


def load_baseline(path: Path) -> dict:
    if not path.exists():
        return {}
    return jload(path)


def write_if_changed(path: Path, payload: dict) -> bool:
    """Rewrite only on a real content change — a work list whose mtime moves every run is noise in
    every diff, and the teacher reading it cannot tell a new item from a re-serialisation."""
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="taught items must be exemplified in the sentence bank")
    ap.add_argument("--root", default=str(REPO), help="tree to validate (default: repo root)")
    ap.add_argument("--record", action="store_true",
                    help="re-record the ratchet after a DELIBERATE change; never to silence a failure")
    ap.add_argument("--list", action="store_true", help="print every shortfall, not the first 20")
    ap.add_argument("--kind", choices=sorted(FLOOR), help="restrict the printed detail to one kind")
    # The ratchet is a property of the PROJECT, not of the data under --root, so it lives beside this
    # script and --root does not move it (the same rule validate_provenance_json.py applies to the
    # exam derivation contract). --baseline exists so the falsifiability proofs can point a run at a
    # mutated ceiling file without editing the committed one.
    ap.add_argument("--baseline", default=str(BASELINE), help=argparse.SUPPRESS)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    baseline_path = Path(args.baseline).resolve()

    fails: list[str] = []

    vocab_level, grammar_level, key_to_slug = load_registries(root)
    per_vocab, per_grammar, n_sentences, bank_problems = count_bank(root, key_to_slug)
    taught, n_lessons = load_taught(root)
    fails.extend(bank_problems)

    # ---- empty input fails -----------------------------------------------------------------------
    if n_lessons < MIN_LESSONS:
        fails.append(f"only {n_lessons} lesson leaves under {root}/course (floor {MIN_LESSONS}) — the "
                     f"course tree moved, and a coverage gate over no course certifies nothing")
    if n_sentences < MIN_SENTENCES:
        fails.append(f"only {n_sentences} sentences in corpus/sentences/bank.json (floor "
                     f"{MIN_SENTENCES}) — the bank is what this gate counts")
    if len(vocab_level) < MIN_VOCAB:
        fails.append(f"only {len(vocab_level)} vocab records under corpus/vocab (floor {MIN_VOCAB})")
    if len(grammar_level) < MIN_GRAMMAR:
        fails.append(f"only {len(grammar_level)} grammar records under corpus/grammar "
                     f"(floor {MIN_GRAMMAR})")
    for kind, floor in sorted(MIN_TAUGHT.items()):
        if len(taught[kind]) < floor:
            fails.append(f"only {len(taught[kind])} taught {kind} refs across the lesson leaves "
                         f"(floor {floor}) — `unlocks[]` stopped being read")

    # ---- the measurement -------------------------------------------------------------------------
    levels = {"vocab": vocab_level, "grammar": grammar_level}
    counts = {"vocab": per_vocab, "grammar": per_grammar}
    observed: dict[str, dict[str, int]] = {}
    shortfall: dict[str, list[dict]] = {"vocab": [], "grammar": []}

    for kind in sorted(FLOOR):
        floor = FLOOR[kind]
        registry, count = levels[kind], counts[kind]
        for ref, lesson_id in sorted(taught[kind].items()):
            if ref not in registry:
                fails.append(f"lesson {lesson_id} unlocks {kind} {ref}, which names no record in "
                             f"corpus/{kind} — its coverage cannot be measured at all")
                continue
            level = registry[ref]
            bucket = observed.setdefault(f"{level}|{kind}", {"taught": 0, "below": 0, "zero": 0})
            bucket["taught"] += 1
            have = count.get(ref, 0)
            if have < floor:
                bucket["below"] += 1
                if have == 0:
                    bucket["zero"] += 1
                shortfall[kind].append({"ref": ref, "level": level, "sentences": have,
                                        "floor": floor, "needs": floor - have,
                                        "first_taught_by": lesson_id})

    # ---- the ratchet -----------------------------------------------------------------------------
    baseline = load_baseline(baseline_path)
    ceilings = baseline.get("ceilings", {}) if isinstance(baseline, dict) else {}
    grew: list[str] = []
    shrank: list[str] = []

    if args.record:
        payload = {
            "note": "W05 ratchet. Per (level, kind): `taught` is context, `below` and `zero` are the "
                    "DEBT and may only shrink. Growth is a hard failure — teaching one more item with "
                    "no example is the regression this gate exists to catch. Re-record with --record "
                    "only after a deliberate change (a level added, a floor changed), never to "
                    "silence a failure you have not explained. Retired by W12 (orthographic relink) "
                    "and W13 (N3 exemplification).",
            "floors": FLOOR,
            "ceilings": {k: dict(v) for k, v in sorted(observed.items())},
        }
        baseline_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"recorded {len(observed)} (level, kind) ceilings -> {baseline_path.name}")
        return 0

    if not ceilings:
        fails.append(f"{baseline_path.name} holds no ceilings — a ratchet with nothing frozen in it cannot "
                     f"fail on growth. Record it with --record.")
    for key in sorted(set(observed) | set(ceilings)):
        got = observed.get(key)
        want = ceilings.get(key)
        if got is None:
            fails.append(f"ratchet {key}: the baseline holds a ceiling for a (level, kind) the data no "
                         f"longer produces — a stale ceiling nothing can falsify. Re-record it.")
            continue
        if want is None:
            fails.append(f"ratchet {key}: {got['below']} of {got['taught']} taught items are under the "
                         f"floor and the baseline has no ceiling for this (level, kind) — new debt "
                         f"cannot arrive unmeasured")
            continue
        for counter in ("below", "zero"):
            now, ceiling = got[counter], int(want.get(counter, 0))
            if now > ceiling:
                grew.append(f"{key} {counter}: {ceiling} -> {now} (+{now - ceiling})")
                fails.append(f"ratchet {key}: `{counter}` grew from {ceiling} to {now}. An item was "
                             f"taught without the examples to teach it with, or links were lost.")
            elif now < ceiling:
                shrank.append(f"{key} {counter}: {ceiling} -> {now} (-{ceiling - now})")

    # ---- the work list ---------------------------------------------------------------------------
    work = {
        "note": "Every taught item under its sentence floor, with how many sentences it still needs. "
                "This is the W12/W13 work list; it is regenerated by "
                "scripts/validate/validate_sentence_coverage.py and rewritten only when it changes.",
        "floors": FLOOR,
        "totals": {k: dict(v) for k, v in sorted(observed.items())},
        "items": {kind: sorted(rows, key=lambda r: (level_key(r["level"]), r["sentences"], r["ref"]))
                  for kind, rows in sorted(shortfall.items())},
    }
    changed = False
    if not fails or all(f.startswith("ratchet ") for f in fails):
        changed = write_if_changed(root / REPORT_REL, work)

    # ---- report ----------------------------------------------------------------------------------
    print("=========== SENTENCE COVERAGE (taught items must be exemplified) ===========")
    print(f"  bank {n_sentences:,} sentences · {n_lessons} lesson leaves · "
          f"floors vocab>={FLOOR['vocab']} grammar>={FLOOR['grammar']}")
    print(f"  {'level':8} {'kind':9} {'taught':>7} {'>=floor':>8} {'below':>7} {'zero':>6} "
          f"{'ceiling':>8}")
    for key in sorted(observed, key=lambda k: (level_key(k.split("|")[0]), k.split("|")[1])):
        level, kind = key.split("|")
        got = observed[key]
        ceiling = ceilings.get(key, {})
        mark = " "
        if got["below"] > int(ceiling.get("below", 0)):
            mark = "!"
        elif got["below"] < int(ceiling.get("below", got["below"])):
            mark = "-"
        print(f" {mark}{level:8} {kind:9} {got['taught']:>7} {got['taught'] - got['below']:>8} "
              f"{got['below']:>7} {got['zero']:>6} {str(ceiling.get('below', '—')):>8}")
    tot_taught = sum(v["taught"] for v in observed.values())
    tot_below = sum(v["below"] for v in observed.values())
    tot_zero = sum(v["zero"] for v in observed.values())
    print(f"  ---- {tot_taught:,} taught · {tot_below:,} under floor · {tot_zero:,} at zero")

    if shrank:
        print("\n  RATCHET SHRANK — lower these ceilings with --record:")
        for line in shrank:
            print(f"    {line}")
    if grew:
        print("\n  RATCHET GREW:")
        for line in grew:
            print(f"    {line}")

    detail = [r for kind in sorted(shortfall) if not args.kind or args.kind == kind
              for r in shortfall[kind]]
    if detail:
        detail.sort(key=lambda r: (level_key(r["level"]), r["sentences"], r["ref"]))
        shown = detail if args.list else detail[:MAX_REPORT]
        print(f"\n  shortfall detail ({len(shown)} of {len(detail)}"
              f"{'' if args.list else ', use --list for all'}):")
        for r in shown:
            print(f"    {r['level']:6} {r['ref']:28} {r['sentences']}/{r['floor']} "
                  f"(needs {r['needs']}) first taught by {r['first_taught_by']}")
    if changed:
        print(f"\n  work list rewritten: {REPORT_REL}")

    if fails:
        print()
        shown_f = fails if args.list else fails[:MAX_REPORT]
        for f in shown_f:
            print("  FAIL", f)
        if len(fails) > len(shown_f):
            print(f"  ... {len(fails) - len(shown_f)} more (use --list)")

    print(f"\nvalidate_sentence_coverage: {tot_taught:,} taught items checked, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK (ratchet held)'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
