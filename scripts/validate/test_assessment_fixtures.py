#!/usr/bin/env python3
"""W23 fixture suite: the runtime assessment invariants JSON Schema cannot state (design/assessment.md §4.5).

`exercise_attempt` and `assessment_attempt` are RUNTIME entities: no committed records, so there is
nothing to validate in this repo. What can honestly be enforced is (1) the contracts compile and a
good fixture validates while a malformed one does not, and (2) the cross-record invariants, each
written as a checker over fixture rows and proved by a PLANT the checker must catch. This file is
also the executable spec of the `mistake_index` VIEW (WEAKNESS_V1, §4.3): a view, never a table, so
`mistake_index()` below is the one definition two consumers must not re-invent differently.

Every case asserts both directions: the good fixture passes AND the plant fails. Exit 1 on any miss.
Usage: test_assessment_fixtures.py
"""
from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from jsonschema import Draft202012Validator  # noqa: E402
from referencing import Registry, Resource  # noqa: E402

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"
WEAKNESS_V1 = {"window_days": 90, "half_life_days": 14, "min_evidence": 2.0, "weak_at": 0.34}
CONTEXT_PREFIX = {"lesson": "les:", "topic_test": "asm:", "placement": "asm:", "exam": "att:", "drill": None}
NOW = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- the view, as a spec
def mistake_index(attempts: list[dict], user: str, now: datetime, p: dict = WEAKNESS_V1) -> dict[str, dict]:
    """design/assessment.md §4.3, verbatim: recency-weighted miss rate over `target` refs only."""
    rows: dict[str, dict] = {}
    for a in attempts:
        when = datetime.fromisoformat(a["answered_at"])
        age = (now - when).total_seconds() / 86400
        if a["user_id"] != user or age > p["window_days"]:
            continue
        w = 2 ** (-age / p["half_life_days"])
        for e in a["item_refs"]:
            if e["role"] != "target":
                continue
            r = rows.setdefault(e["ref"], {"attempts": 0, "misses": 0, "evidence": 0.0, "missed_w": 0.0,
                                           "first_missed_at": None, "last_missed_at": None})
            r["attempts"] += 1
            r["evidence"] += w
            if not a["correct"]:
                r["misses"] += 1
                r["missed_w"] += w
                r["first_missed_at"] = min(filter(None, [r["first_missed_at"], a["answered_at"]]))
                r["last_missed_at"] = max(filter(None, [r["last_missed_at"], a["answered_at"]]))
    for r in rows.values():
        r["miss_rate"] = r.pop("missed_w") / r["evidence"] if r["evidence"] else 0.0
        r["state"] = ("unknown" if r["evidence"] < p["min_evidence"]
                      else "weak" if r["miss_rate"] >= p["weak_at"] else "ok")
    return rows


# --------------------------------------------------------------------------- invariant checkers
def context_ok(a: dict) -> bool:
    want = CONTEXT_PREFIX[a["context"]["kind"]]
    ref = a["context"]["ref"]
    return ref is None if want is None else isinstance(ref, str) and ref.startswith(want)


def refs_served(a: dict, question: dict) -> bool:
    served = {e["ref"] for e in question["item_refs"]}
    return all(e["ref"] in served for e in a["item_refs"])


def firewall_ok(card_before: dict, card_after: dict, log_before: list, log_after: list) -> bool:
    """Grading an exercise writes no review_log row and moves no card field but leech_state."""
    if log_after != log_before:
        return False
    return all(card_before.get(k) == card_after.get(k) for k in set(card_before) | set(card_after)
               if k != "leech_state")


def counters_ok(progress: dict, attempts: list[dict]) -> bool:
    mine = [a for a in attempts if a["user_id"] == progress["user_id"]
            and a["context"] == {"kind": "lesson", "ref": progress["lesson"]}]
    return (progress["exercises_attempted"] == len({a["question"] for a in mine})
            and progress["exercises_correct"] == len({a["question"] for a in mine if a["correct"]}))


def exam_stream_ok(exam: dict, attempts: list[dict]) -> bool:
    answered = sum(1 for it in exam["items"] if it.get("answer_given") is not None)
    return sum(1 for a in attempts if a["context"]["ref"] == exam["attempt_id"]) == answered


def minimum_met_ok(att: dict, min_items: int = 3) -> bool:
    return all(v["minimum_met"] is None for v in (att.get("by_kind") or {}).values()
               if v["possible"] < min_items)


def entry_ok(att: dict, needs: dict[str, set[str]], topic_of: dict[str, str], cleared: set[str]) -> bool:
    """§5.2 step 3: no transitive prerequisite of entry_lesson sits in a topic the probe did not clear."""
    seen, stack = set(), [att["placement"]["entry_lesson"]]
    while stack:
        for pre in needs.get(stack.pop(), set()):
            if pre not in seen:
                seen.add(pre)
                stack.append(pre)
    return all(topic_of[p] in cleared for p in seen)


def grade(exercise: dict, answer: str, user: str, lesson: str, log: list) -> dict:
    """The reference grader: appends ONE exercise_attempt; touches neither review_log nor a card."""
    return {"attempt_id": "xat:f1", "user_id": user, "question": exercise["id"],
            "question_form": exercise["type"],
            "item_refs": [{k: e[k] for k in ("type", "ref", "role")} for e in exercise["item_refs"]],
            "context": {"kind": "lesson", "ref": lesson}, "answered_at": NOW.isoformat(),
            "correct": answer == exercise["answer"]["correct"], "answer_given": answer,
            "response_ms": 1200, "graded_by": "client", "client_key": "k1"}


def bad_grade(exercise: dict, answer: str, user: str, lesson: str, log: list) -> dict:
    log.append({"review_id": "rev:x", "card_id": "card:x", "rating": 1})     # the plant
    return grade(exercise, answer, user, lesson, log)


# --------------------------------------------------------------------------- fixtures
def validator(name: str) -> Draft202012Validator:
    reg = Registry()
    for p in [*CONTRACTS.glob("*.schema.json"), *CONTRACTS.glob("*/*.schema.json")]:
        doc = json.loads(p.read_text(encoding="utf-8"))
        res = Resource.from_contents(doc)
        reg = reg.with_resource(uri=p.name, resource=res).with_resource(uri=doc["$id"], resource=res)
    doc = json.loads((CONTRACTS / "user_state" / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(doc)
    return Draft202012Validator(doc, registry=reg)


EXERCISE = {"id": "ex:n5-verbos-06-3", "type": "recognition",
            "answer": {"choices": ["ください", "ます"], "correct": "ください"},
            "item_refs": [{"type": "grammar", "ref": "gram:o-kudasai", "role": "target", "derived_by": "authored"}]}


def attempt(correct: bool, days_ago: float, ref: str = "gram:o-kudasai", q: str = "ex:a") -> dict:
    return {"attempt_id": f"xat:{q[3:]}{days_ago}".replace(".", "-"), "user_id": "usr:u1", "question": q,
            "question_form": "recognition", "item_refs": [{"type": "grammar", "ref": ref, "role": "target"}],
            "context": {"kind": "lesson", "ref": "les:n5-verbos-06"},
            "answered_at": (NOW - timedelta(days=days_ago)).isoformat(), "correct": correct,
            "answer_given": "x", "response_ms": 900, "graded_by": "client", "client_key": None}


TOPIC_SITTING = {"attempt_id": "asm:7f3a91-1", "user_id": "usr:u1", "kind": "topic_test",
                 "blueprint": "test:n5-verbos", "seed": "usr:u1|test:n5-verbos|1", "seed_algorithm": "test-v1",
                 "started_at": NOW.isoformat(), "submitted_at": NOW.isoformat(),
                 "items": ["ex:n5-verbos-06-3"], "raw": 9, "possible": 12,
                 "by_kind": {"vocab": {"raw": 7, "possible": 10, "minimum_met": True},
                             "grammar": {"raw": 2, "possible": 2, "minimum_met": None}},
                 "criterion": "TOPIC_PASS_V1", "passed": True, "placement": None}
PLACEMENT = {"attempt_id": "asm:7f3a91-2", "user_id": "usr:u1", "kind": "placement", "blueprint": None,
             "seed": "usr:u1|probe|2", "seed_algorithm": "probe-v1", "started_at": NOW.isoformat(),
             "submitted_at": NOW.isoformat(), "items": [], "raw": None, "possible": None, "by_kind": None,
             "criterion": None, "passed": None,
             "placement": {"cleared_topic": "top:n5-desu-wa", "entry_lesson": "les:c-1", "skipped_lessons": 41,
                           "cards_seeded": True, "policy": "PLACEMENT_V1"}}


def main() -> int:
    results: list[tuple[str, bool]] = []

    def case(name: str, good: bool, plant: bool) -> None:
        results.append((name, good and not plant))
        print(f"  {'PASS' if good and not plant else 'FAIL'}  {name}  (good={good}, plant caught={not plant})")

    xv, av = validator("exercise_attempt"), validator("assessment_attempt")
    good_att = grade(EXERCISE, "ください", "usr:u1", "les:n5-verbos-06", [])
    bad = copy.deepcopy(good_att)
    bad["item_refs"][0]["derived_by"] = "authored"
    case("schema: exercise_attempt validates; a copied derived_by is refused", xv.is_valid(good_att), xv.is_valid(bad))
    case("schema: topic_test sitting validates; a null blueprint is refused",
         av.is_valid(TOPIC_SITTING), av.is_valid({**TOPIC_SITTING, "blueprint": None}))
    case("schema: placement validates; `passed: true` on a placement is refused",
         av.is_valid(PLACEMENT), av.is_valid({**PLACEMENT, "passed": True}))

    case("context.ref prefix matches context.kind", context_ok(good_att),
         context_ok({**good_att, "context": {"kind": "lesson", "ref": "asm:7f3a91-1"}}))
    case("attempt refs are the served question's refs", refs_served(good_att, EXERCISE),
         refs_served({**good_att, "item_refs": [{"type": "vocab", "ref": "vocab:1", "role": "target"}]}, EXERCISE))

    card = {"card_id": "card:1", "state": "review", "stability": 3.1, "difficulty": 5.0, "due": "2026-09-25",
            "step": 0, "reps": 4, "lapses": 0, "leech_state": "none"}
    log: list = []
    after = copy.deepcopy(card)
    grade(EXERCISE, "ます", "usr:u1", "les:n5-verbos-06", log)
    fw_good = firewall_ok(card, after, [], log)
    log2: list = []
    bad_grade(EXERCISE, "ます", "usr:u1", "les:n5-verbos-06", log2)
    fw_plant = firewall_ok(card, after, [], log2)
    moved = {**card, "due": "2026-09-24"}
    case("FSRS firewall: grading writes no review_log row", fw_good, fw_plant)
    case("FSRS firewall: no scheduling field moves (leech_state may)",
         firewall_ok(card, {**card, "leech_state": "flagged"}, [], []), firewall_ok(card, moved, [], []))

    atts = [attempt(True, 1, q="ex:a"), attempt(False, 2, q="ex:b"), attempt(False, 3, q="ex:b")]
    prog = {"user_id": "usr:u1", "lesson": "les:n5-verbos-06", "exercises_attempted": 2, "exercises_correct": 1}
    case("lesson_progress counters are a GROUP BY over exercise_attempt", counters_ok(prog, atts),
         counters_ok({**prog, "exercises_attempted": 3}, atts))

    exam = {"attempt_id": "att:7f3a91-n5-1", "items": [{"answer_given": "a"}, {"answer_given": None}]}
    stream = [{**attempt(True, 0), "context": {"kind": "exam", "ref": "att:7f3a91-n5-1"}}]
    case("a submitted paper has its answer stream", exam_stream_ok(exam, stream), exam_stream_ok(exam, []))

    one_miss = mistake_index([attempt(False, 0)], "usr:u1", NOW)["gram:o-kudasai"]
    many = mistake_index([attempt(False, 0), attempt(False, 1), attempt(True, 2)], "usr:u1", NOW)["gram:o-kudasai"]
    case("WEAKNESS_V1: one miss is `unknown`, never `weak`; enough misses are `weak`",
         one_miss["state"] == "unknown" and many["state"] == "weak" and many["attempts"] == 3,
         one_miss["state"] == "weak")
    old = mistake_index([attempt(False, 120), attempt(False, 100)], "usr:u1", NOW)
    case("WEAKNESS_V1: attempts outside the 90-day window are not evidence", old == {}, bool(old))

    case("minimum_met is null on a kind with fewer than 3 questions", minimum_met_ok(TOPIC_SITTING),
         minimum_met_ok({**TOPIC_SITTING, "by_kind": {"grammar": {"raw": 2, "possible": 2, "minimum_met": True}}}))
    needs = {"les:c-1": {"les:b-2"}, "les:b-2": {"les:a-1"}}
    topic_of = {"les:a-1": "top:a", "les:b-2": "top:b", "les:c-1": "top:c"}
    case("entry_lesson has no uncleared prerequisite", entry_ok(PLACEMENT, needs, topic_of, {"top:a", "top:b"}),
         entry_ok(PLACEMENT, needs, topic_of, {"top:a"}))

    bad_n = sum(1 for _n, ok in results if not ok)
    print(f"\ntest_assessment_fixtures: {len(results)} cases, {len(results) - bad_n} PASS, {bad_n} FAIL")
    return 1 if bad_n else 0


if __name__ == "__main__":
    sys.exit(main())
