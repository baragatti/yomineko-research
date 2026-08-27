#!/usr/bin/env python3
"""Gate: a lesson never puts in front of the learner something the course has not taught yet.

Two defects motivated this file.

(1) Nothing checked the lesson BODY against the lesson's own `cumulative_known_set`. The course
    review found 9 item references rendered to a learner who had never met the item — eight
    homograph siblings the disambiguation dropped, and one word used two lessons before the lesson
    that unlocks it (vocab:1228690 in les:n4-dar-receber-02, unlocked by les:n4-dar-receber-04).
    `validate_lessons.py` looked like it covered this, but it read db/corpus.sqlite in the retired
    `vocab:<headword>` namespace and never touched the `body` string — so the shipped artifact, the
    exported JSON that CLAUDE.md names the source of truth, was never the thing being tested.

(2) The i+1 property was asserted in the design docs and enforced nowhere for lessons. 178 of 624
    lesson->sentence display links show a sentence graded ABOVE the lesson's level, and 147 exceed
    the per-level budget of new kanji + new vocab. That backlog is CONTENT work for a teacher, not
    something a validator can fix, so this script does not pretend it is clean: it FREEZES the
    numbers in research/reports/lesson_sentence_baseline.json and hard-fails only when they GROW,
    and it writes the full offender list to research/reports/lesson_sentence_review.json for the
    teacher to work top-down.

Checks, in order:
  A  HARD      cumulative_known_set == the running union of unlocks up to and including that lesson,
               per kind, walking the course in (course.order, topic.order, lesson.order).
  B  HARD      every item reference a body renders — <vocab ref>, <kanji ref>, <grammar ref>,
               <stroke ref="kanji:…">, <check item-ref> — is a member of that lesson's
               cumulative_known_set for its kind, or is listed in course/gating_exemptions.json
               with a reason. An exemption that matches nothing is itself a failure.
  C  HARD      every `needs` prerequisite resolves to a lesson strictly earlier in course order;
               plus a loud ADVISORY when the whole course declares zero prerequisites, so an empty
               model can never be mistaken for a passing linearity gate.
  D  FROZEN    sentence level fit + i+1 budget, compared against the checked-in baseline.

Scope note: the readings half of the i+0 rule (corpus/readings/*.json `uses` vs `gated_to_lesson`)
is already a hard gate over the same exported JSON in validate_readings.py and is deliberately not
duplicated here — one source of truth per invariant.

Exit 1 on any HARD failure or on growth past the baseline.
Usage: validate_lesson_gating.py [--root PATH] [--write-baseline] [--no-report]
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]

KINDS = ("kana-family", "vocab", "kanji", "grammar", "conjugation-form", "phrase")
# namespace prefix -> cumulative_known_set kind
NS_KIND = {"kana": "kana-family", "vocab": "vocab", "kanji": "kanji", "gram": "grammar"}
# level ordering: the manifest's course.order, with the levels this corpus does not teach appended
LEVEL_ORDER = ("pre-n5", "n5", "n4", "n3", "n2", "n1")
# i+1 allowance: how many unknown kanji + unknown vocab a displayed sentence may carry.
# Changing this table invalidates the frozen baseline on purpose — the baseline records it.
BUDGET = {"pre-n5": 0, "n5": 1, "n4": 2, "n3": 2}

ITEM_TAG = re.compile(r"<(vocab|kanji|grammar|stroke|check)\b([^>]*)>")
ITEM_ATTR = re.compile(r'\b(item-ref|ref)="([^"]+)"')
SENT_REF = re.compile(r'<sentence\s+[^>]*ref="([^"]+)"')

BASELINE_REL = "research/reports/lesson_sentence_baseline.json"
REVIEW_REL = "research/reports/lesson_sentence_review.json"
EXEMPT_REL = "course/gating_exemptions.json"


def load_course(root: Path) -> list[dict]:
    """Every lesson leaf, in true course order."""
    man = json.loads((root / "course" / "manifest.json").read_text(encoding="utf-8"))
    corder = {c["level"]: c["order"] for c in man["courses"]}
    topic_pos: dict[str, tuple[int, int]] = {}
    for cf in sorted(root.glob("course/*/course.json")):
        c = json.loads(cf.read_text(encoding="utf-8"))
        for t in c.get("topics") or []:
            topic_pos[t["id"]] = (corder.get(c["level"], 99), t["order"])
    lessons = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted(root.glob("course/*/topic-*/lesson-*.json"))]
    lessons.sort(key=lambda d: topic_pos.get(d.get("topic", ""), (99, 99)) + (d.get("order", 0),))
    return lessons


def body_item_refs(body: str) -> list[tuple[str, str]]:
    """[(tag, ref)] for every teachable-item reference the body renders."""
    out = []
    for m in ITEM_TAG.finditer(body or ""):
        tag, attrs = m.group(1), m.group(2)
        for _, ref in ITEM_ATTR.findall(attrs):
            out.append((tag, ref))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--write-baseline", action="store_true",
                    help="re-freeze research/reports/lesson_sentence_baseline.json from this tree")
    ap.add_argument("--no-report", action="store_true", help="do not write the teacher review file")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    lessons = load_course(root)
    pos = {d["id"]: i for i, d in enumerate(lessons)}
    fails: list[str] = []

    # ---- exemptions ------------------------------------------------------------------
    exempt: dict[tuple[str, str], str] = {}
    ef = root / EXEMPT_REL
    if ef.exists():
        ex = json.loads(ef.read_text(encoding="utf-8"))
        for i, e in enumerate(ex.get("item_refs") or []):
            if not (e.get("lesson") and e.get("ref") and (e.get("reason") or "").strip()):
                fails.append(f"{EXEMPT_REL}[{i}]: entry needs lesson, ref and a non-empty reason")
                continue
            exempt[(e["lesson"], e["ref"])] = e["reason"]
    used_exempt: set[tuple[str, str]] = set()

    # ---- A: cumulative_known_set is the running union of unlocks -----------------------
    run: dict[str, set[str]] = {k: set() for k in KINDS}
    a_fails = 0
    for d in lessons:
        for u in d.get("unlocks") or []:
            if u.get("type") in run:
                run[u["type"]].add(u["ref"])
        cks = d.get("cumulative_known_set") or {}
        for k in KINDS:
            got, want = set(cks.get(k) or []), run[k]
            if got != want:
                a_fails += 1
                extra, gone = sorted(got - want)[:3], sorted(want - got)[:3]
                fails.append(f"{d['id']} cumulative_known_set.{k} != running union of unlocks "
                             f"(+{len(got - want)} {extra} / -{len(want - got)} {gone})")

    # ---- B: every rendered item ref is inside the known set ---------------------------
    b_checked = b_fails = 0
    for d in lessons:
        cks = d.get("cumulative_known_set") or {}
        sets = {k: set(cks.get(k) or []) for k in KINDS}
        for tag, ref in body_item_refs(d.get("body") or ""):
            b_checked += 1
            kind = NS_KIND.get(ref.split(":", 1)[0])
            if kind is None:
                b_fails += 1
                fails.append(f"{d['id']} <{tag}> ref={ref!r}: unknown namespace")
                continue
            if ref in sets[kind]:
                continue
            if (d["id"], ref) in exempt:
                used_exempt.add((d["id"], ref))
                continue
            b_fails += 1
            later = [x["id"] for x in lessons
                     if any(u.get("ref") == ref for u in (x.get("unlocks") or []))]
            where = (f"unlocked later by {later[0]} (position {pos[later[0]]} vs {pos[d['id']]})"
                     if later else "never unlocked by any lesson")
            fails.append(f"{d['id']} <{tag}> {ref} not in cumulative_known_set.{kind} — {where}")

    for key, reason in exempt.items():
        if key not in used_exempt:
            fails.append(f"{EXEMPT_REL}: exemption {key[0]} / {key[1]} matches nothing "
                         f"(reason was {reason[:60]!r}) — delete it")

    # ---- C: prerequisites resolve and are strictly earlier ----------------------------
    needs_total = c_fails = 0
    for d in lessons:
        for n in d.get("needs") or []:
            needs_total += 1
            ref = n.get("ref") if isinstance(n, dict) else n
            if ref not in pos:
                c_fails += 1
                fails.append(f"{d['id']} needs {ref!r}: not an exported lesson")
            elif pos[ref] >= pos[d["id"]]:
                c_fails += 1
                fails.append(f"{d['id']} needs {ref}: not strictly earlier "
                             f"(position {pos[ref]} vs {pos[d['id']]})")

    # ---- D: sentence level fit + i+1 budget (frozen, not clean) -----------------------
    bank = {s["slug"]: s for s in
            json.loads((root / "corpus/sentences/bank.json").read_text(encoding="utf-8"))}
    kanji_chars = set()
    for kf in sorted(root.glob("corpus/kanji/*.json")):
        for k in json.loads(kf.read_text(encoding="utf-8")):
            kanji_chars.add(k["character"])
    vocab: dict[str, dict] = {}
    vid2slug: dict[int, str] = {}
    for vf in sorted(root.glob("corpus/vocab/*.json")):
        for v in json.loads(vf.read_text(encoding="utf-8")):
            vocab[v["slug"]] = v
            vid2slug[v["id"]] = v["slug"]

    pairs = 0
    above_buckets: dict[str, int] = {}
    over_by_level: dict[str, int] = {}
    n_above = n_over = n_new_kanji = n_new_vocab = 0
    offenders: list[dict] = []
    for d in lessons:
        cks = d.get("cumulative_known_set") or {}
        known_k = {x.split(":", 1)[1] for x in cks.get("kanji") or []}
        known_v = set(cks.get("vocab") or [])
        llv = d.get("level", "n5")
        budget = BUDGET.get(llv, 2)
        shown = sorted(set(SENT_REF.findall(d.get("body") or "")) | set(d.get("sentence_refs") or []))
        for sref in shown:
            pairs += 1
            s = bank.get(sref)
            if s is None:            # ref integrity is validate_sentence_manifest's gate; note and skip
                continue
            slv = s.get("level", "n5")
            above = (slv in LEVEL_ORDER and llv in LEVEL_ORDER
                     and LEVEL_ORDER.index(slv) > LEVEL_ORDER.index(llv))
            new_k = sorted({c for c in s["jp"] if c in kanji_chars and c not in known_k})
            new_v: set[str] = set()
            for t in s.get("tokens") or []:
                if t.get("split_mode") != "C":
                    continue
                slug = t.get("vocab") or vid2slug.get(t.get("vocab_id"))  # type: ignore[arg-type]
                if slug and slug not in known_v:
                    new_v.add(slug)
            load = len(new_k) + len(new_v)
            if above:
                n_above += 1
                above_buckets[f"{llv}<-{slv}"] = above_buckets.get(f"{llv}<-{slv}", 0) + 1
            if new_k:
                n_new_kanji += 1
            if new_v:
                n_new_vocab += 1
            if load > budget:
                n_over += 1
                over_by_level[llv] = over_by_level.get(llv, 0) + 1
            if above or load > budget:
                offenders.append({
                    "lesson": d["id"], "lesson_level": llv, "topic": d.get("topic"),
                    "sentence": sref, "sentence_level": slv, "jp": s["jp"],
                    "above_lesson_level": above, "budget": budget, "load": load,
                    "new_kanji": new_k,
                    "new_vocab": [{"slug": v, "headword": (vocab.get(v) or {}).get("headword"),
                                   "kana": (vocab.get(v) or {}).get("kana")} for v in sorted(new_v)],
                })
    offenders.sort(key=lambda o: (-o["load"], o["lesson"], o["sentence"]))

    current = {
        "pairs_total": pairs,
        "pairs_above_level": n_above,
        "pairs_over_budget": n_over,
        "pairs_with_new_kanji": n_new_kanji,
        "pairs_with_new_vocab": n_new_vocab,
        "above_level_buckets": dict(sorted(above_buckets.items())),
        "over_budget_by_level": dict(sorted(over_by_level.items())),
    }
    GATED = ("pairs_above_level", "pairs_over_budget", "pairs_with_new_kanji", "pairs_with_new_vocab")

    if not args.no_report:
        rp = root / REVIEW_REL
        rp.parent.mkdir(parents=True, exist_ok=True)
        _payload = json.dumps({
            "why": "Lesson->sentence display links that break i+1: the sentence is graded above the "
                   "lesson's level, or it carries more unknown kanji+vocab than the level's budget. "
                   "Teacher-facing re-selection queue, worst first. Regenerated by "
                   "scripts/validate/validate_lesson_gating.py; the counts are frozen in "
                   + BASELINE_REL + " and may not grow.",
            "budgets": BUDGET, "summary": current, "count": len(offenders), "items": offenders,
        }, ensure_ascii=False, indent=2) + "\n"
        # a validator must not dirty the tree it validates: write only on real change
        if not rp.exists() or rp.read_text(encoding="utf-8") != _payload:
            rp.write_text(_payload, encoding="utf-8")

    bp = root / BASELINE_REL
    if args.write_baseline:
        bp.parent.mkdir(parents=True, exist_ok=True)
        bp.write_text(json.dumps({
            "why": "Frozen advisory ceiling for the lesson<->sentence i+1 backlog. These are known "
                   "CONTENT defects awaiting sentence re-selection, not passing checks: "
                   "validate_lesson_gating.py fails when any counter EXCEEDS the value here, and "
                   "says so when one drops so the baseline can be lowered. `budgets` must match the "
                   "BUDGET table in the validator, or the baseline is stale.",
            "budgets": BUDGET, **current,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {BASELINE_REL} (frozen at {n_above} above-level, {n_over} over-budget)")

    d_fails = 0
    drops: list[str] = []
    if not bp.exists():
        d_fails += 1
        fails.append(f"{BASELINE_REL} missing — re-freeze it with --write-baseline")
    else:
        base = json.loads(bp.read_text(encoding="utf-8"))
        if base.get("budgets") != BUDGET:
            d_fails += 1
            fails.append(f"{BASELINE_REL}: budgets {base.get('budgets')} != validator BUDGET "
                         f"{BUDGET} — the table moved, re-freeze the baseline")
        for key in GATED:
            b, c = base.get(key), current[key]
            if b is None:
                d_fails += 1
                fails.append(f"{BASELINE_REL}: no baseline for {key}")
            elif c > b:
                d_fails += 1
                fails.append(f"i+1 backlog GREW: {key} {b} -> {c}")
            elif c < b:
                drops.append(f"{key} {b} -> {c}")
        for name, cur in (("above_level_buckets", above_buckets), ("over_budget_by_level", over_by_level)):
            bb = base.get(name) or {}
            for key, c in sorted(cur.items()):
                b = bb.get(key, 0)
                if c > b:
                    d_fails += 1
                    fails.append(f"i+1 backlog GREW: {name}[{key}] {b} -> {c}")

    # ---- report -----------------------------------------------------------------------
    for line in fails[:15]:
        print(f"  FAIL {line}")
    if len(fails) > 15:
        print(f"  … and {len(fails) - 15} more")
    if needs_total == 0:
        print(f"  ADVISORY: 0 `needs` entries across {len(lessons)} lessons — the prerequisite model "
              f"is empty, so check C proves nothing about linearity.")
    print(f"  ADVISORY: sentence fit {n_above}/{pairs} above lesson level, {n_over}/{pairs} over the "
          f"i+1 budget ({n_new_kanji} with new kanji, {n_new_vocab} with new vocab) — "
          f"{len(offenders)} pairs queued in {REVIEW_REL}")
    for drop in drops:
        print(f"  ADVISORY: backlog shrank — {drop}; lower the baseline with --write-baseline")

    print(f"\nvalidate_lesson_gating: {len(lessons)} lessons, {b_checked} item refs, {pairs} sentence "
          f"links | A {a_fails} FAIL, B {b_fails} FAIL ({len(used_exempt)} exempt), C {c_fails} FAIL, "
          f"D {d_fails} FAIL | {len(fails)} FAIL total")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
