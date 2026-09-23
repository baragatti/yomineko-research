#!/usr/bin/env python3
"""Gate (W23): the topic_test blueprints (course/topic_tests.json) are what the rule builds, and sittable.

design/assessment.md §3. Hard checks, over the exported tree:

  A  one record per topic not in course/test_exemptions.json; every exemption names a real topic with
     a reason; an exempt topic whose scope is no longer empty FAILS
  B  `scope.items` recomputes exactly from the topic's unlocks (`own`) or the range's (`range`)
  C  every pool `ref` resolves (a lesson exercise of the scope's lessons, or an exam-bank item); every
     pool `item_refs[].ref` is inside `scope.items`
  D  `size` equals the formula; `mix.by_kind` sums to `size`; the pool can satisfy the mix (enough
     entries per kind, and the production / constructed floors)
  E  every pool item is inside the topic's last lesson's cumulative_known_set: a lesson exercise's
     target refs, and for an exam item the level gate's own predicate at that lesson
  F  `pass_rule` is the named block TOPIC_PASS_V1 with its exact parameters
  G  regeneration-stable: scripts/export/build_topic_tests.py reproduces both files byte for byte
  H  floors: >= 40 records, >= 900 pool entries

Plant proof (research/reports/w23_apply_report.md): a pool entry at an out-of-scope item (C), a shrunk
`by_kind` count (D), an above-level exam item in a pool (E), a changed `total` (F).
Usage: validate_topic_tests.py [--root PATH] [--list]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "export"))
import build_topic_tests as btt  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]
MIN_RECORDS, MIN_POOL = 40, 900
MAX_SHOWN = 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    fails: list[str] = []

    tests_p, ex_p = root / "course" / "topic_tests.json", root / "course" / "test_exemptions.json"
    if not tests_p.exists() or not ex_p.exists():
        print("validate_topic_tests: FAIL course/topic_tests.json or course/test_exemptions.json missing")
        return 1
    records = json.loads(tests_p.read_text(encoding="utf-8"))
    exempt = json.loads(ex_p.read_text(encoding="utf-8")).get("topics") or []
    corpus = btt.Corpus(root)
    topics = {t["id"]: t for t in corpus.topics}
    want_recs, want_ex = btt.build(root, corpus)
    want_by = {r["topic"]: r for r in want_recs}
    bank_items = {it["id"]: (lv, sec, it) for lv, sec, it in corpus.banks}
    exercises = {ex["id"]: ex for tt in corpus.topics for les in tt["lessons"]
                 for ex in les.get("exercises") or []}

    # A
    got_topics = [r["topic"] for r in records]
    ex_ids = {e.get("id") for e in exempt}
    for e in exempt:
        if e.get("id") not in topics or not (e.get("reason") or "").strip():
            fails.append(f"A test_exemptions: {e!r} names no topic or gives no reason")
        elif e["id"] in want_by:
            fails.append(f"A test_exemptions: {e['id']} teaches items now - it needs a test")
    for tid in topics:
        if tid not in ex_ids and got_topics.count(tid) != 1:
            fails.append(f"A {tid}: {got_topics.count(tid)} record(s), expected 1")

    n_pool = 0
    for r in records:
        tid, slug = r.get("topic"), r.get("slug")
        t, want = topics.get(tid), want_by.get(tid)
        if t is None or want is None:
            fails.append(f"A {slug}: topic {tid} is not a tested topic")
            continue
        scope = r["scope"]["items"]
        in_scope = set(scope)
        # B
        if r["scope"] != want["scope"]:
            fails.append(f"B {slug}: scope differs from the recomputation "
                         f"({len(scope)} vs {len(want['scope']['items'])} items)")
        # C + E
        cks = btt.last_cks(t)
        per_kind: collections.Counter = collections.Counter()
        forms: collections.Counter = collections.Counter()
        for p in r["pool"]:
            n_pool += 1
            refs = [e["ref"] for e in p["item_refs"]]
            if not set(refs) <= in_scope:
                fails.append(f"C {slug}: pool {p['ref']} names {sorted(set(refs) - in_scope)[:3]} outside scope")
            if p["source"] == "lesson_exercise":
                ex = exercises.get(p["ref"])
                if ex is None:
                    fails.append(f"C {slug}: pool {p['ref']} is no lesson exercise")
                    continue
                outside = [x for x in refs if btt.kind_of(x) in ("vocab", "kanji", "grammar")
                           and x not in cks[btt.kind_of(x)]]
                if outside:
                    fails.append(f"E {slug}: {p['ref']} targets {outside[:3]}, untaught at the topic's end")
            elif p["source"] == "exam_bank":
                hit = bank_items.get(p["ref"])
                if hit is None:
                    fails.append(f"C {slug}: pool {p['ref']} is no exam-bank item")
                    continue
                if not corpus.inside(hit[1], hit[2], cks):
                    fails.append(f"E {slug}: {p['ref']} uses Japanese untaught by {t['lessons'][-1]['id']}")
            else:
                fails.append(f"C {slug}: pool {p['ref']} has source {p['source']!r}, which no builder writes")
            for k in {btt.kind_of(x) for x in refs}:
                per_kind[k] += 1
            forms[p["form"]] += 1
        # D
        if r["size"] != min(24, max(12, btt.half_up(len(scope) / 8))):
            fails.append(f"D {slug}: size {r['size']} != the formula over {len(scope)} items")
        by_kind = r["mix"]["by_kind"]
        if sum(by_kind.values()) != r["size"]:
            fails.append(f"D {slug}: mix sums to {sum(by_kind.values())}, size is {r['size']}")
        for k, n in by_kind.items():
            if per_kind[k] < n:
                fails.append(f"D {slug}: mix wants {n} {k} question(s), the pool has {per_kind[k]}")
        if r["mix"] != want["mix"]:
            fails.append(f"D {slug}: mix {r['mix']} != recomputed {want['mix']}")
        if forms["production"] < r["mix"]["min_production"] or \
                sum(forms[f] for f in btt.CONSTRUCTED) < r["mix"]["min_constructed"]:
            fails.append(f"D {slug}: pool cannot meet the production / constructed floors")
        # F
        if r["pass_rule"] != btt.PASS_RULE:
            fails.append(f"F {slug}: pass_rule {r['pass_rule']} is not the TOPIC_PASS_V1 block")

    # G
    tests, ex = btt.render(want_recs, want_ex)
    if tests_p.read_text(encoding="utf-8") != tests:
        fails.append("G course/topic_tests.json is not what build_topic_tests.py builds on this tree")
    if ex_p.read_text(encoding="utf-8") != ex:
        fails.append("G course/test_exemptions.json is not what build_topic_tests.py builds on this tree")
    # H
    if len(records) < MIN_RECORDS or n_pool < MIN_POOL:
        fails.append(f"H floors: {len(records)} records / {n_pool} pool entries "
                     f"(floors {MIN_RECORDS} / {MIN_POOL})")

    shown = fails if args.list else fails[:MAX_SHOWN]
    for f in shown:
        print(f"  FAIL {f}")
    if len(fails) > len(shown):
        print(f"  ... and {len(fails) - len(shown)} more (--list)")
    print(f"\nvalidate_topic_tests: {len(records)} tests, {len(exempt)} exempt topics, {n_pool} pool "
          f"entries | {len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
