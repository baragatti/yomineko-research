#!/usr/bin/env python3
"""W23. One `topic_test` blueprint per topic (design/assessment.md §3), built from the exported tree.

A blueprint, not a paper: the POOL a sitting draws from, the SIZE and MIX the draw obeys and the PASS
rule. Layer C (size, mix and pass mark are pedagogy), `needs_review: true` on every record.

THE RULE (§3.3; every number below is re-measured on the tree it runs against)
------------------------------------------------------------------------------
scope   the items the test may ask about: vocab / kanji / grammar unlocks, and kana families expanded
        to their GLYPHS (a kana question targets one glyph). `own` = the topic's own lessons; `range`
        for a review topic (`*-revisao`) = every topic of its level after the previous review topic
        (or the level's first topic) up to and including it. A topic whose scope is empty gets no
        record and is listed in course/test_exemptions.json. `conjugation-form` / `phrase` unlocks are
        not in scope: no exercise or exam item targets one yet, so a mix slot for them could never be
        filled (the 18,524 conjugation drills are their own entity).
size    clamp(floor(|scope| / 8 + 0.5), 12, 24)
mix     n(kind) = max(1, floor(size * |scope(kind)| / |scope| + 0.5)), then trimmed from the largest
        count (never below 1) or padded to the largest share until it sums to `size`; plus >= 1
        production and >= 1 constructed (cloze / sentence_build) form WHERE THE POOL HAS ONE. Five
        topics teach no constructed form at all (the two kana scripts, saudações, the two kanji-exame
        topics: their lessons carry no cloze or sentence_build), so their floor is 0, recorded on
        the record, not invented by minting.
pool    in priority order, selection only (spec §1.2):
          1. lesson exercises of the scope's lessons whose `role: target` refs meet the scope
             (lesson.exercises[].item_refs, W23 §2);
          2. exam-bank items (never listening: no audio) whose key meets the scope - `vocab` slug,
             `gram:` + the bank's bare `grammar` key, and for kanji_reading / orthography the kanji of
             `target` or of the vocab headword - and that pass the exam level gate's predicate AT the
             topic's last lesson (validate_exam_level_gate: every kanji the learner sees, the item's
             word and the source sentence's token words, its grammar and the sentence's tags, all
             inside that lesson's cumulative_known_set; a passage item needs its passage).
        §3.3 source 3 (minted cloze) is not built: the pool satisfies every mix without it (the
        validator's check D is what would say otherwise).
pass    TOPIC_PASS_V1 = {total 0.70, per_kind_minimum 0.50, min_items_per_kind_for_minimum 3}.

Writes course/topic_tests.json (list) + course/test_exemptions.json. Deterministic: the validator's
check G re-runs `build()` and compares bytes.
Usage: build_topic_tests.py [--root PATH] [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "validate"))
from validate_exam_banks import BANK_RE, PASSAGE_TYPES  # noqa: E402
from validate_exam_level_gate import KANJI_RE, gram_slug, visible_jp  # noqa: E402

REPO = _HERE.parents[1]
LOC = "pt-BR"
SCOPE_KINDS = ("vocab", "kanji", "grammar", "kana")
PASS_RULE = {"criterion": "TOPIC_PASS_V1", "total": 0.7, "per_kind_minimum": 0.5,
             "min_items_per_kind_for_minimum": 3}
CONSTRUCTED = ("cloze", "sentence_build")
SECTION_FORM = {"kanji_reading": "recognition", "orthography": "recognition",
                "context_fill": "cloze", "grammar_form": "cloze", "text_grammar": "cloze",
                "sentence_order": "ordering", "paraphrase": "recognition", "usage": "recognition",
                "reading_comp": "reading"}
EXEMPT_REASON = ("The topic unlocks no vocab, kanji, grammar or kana item: it teaches course method or "
                 "phonology, so a test would be a quiz about the course (design/assessment.md §3.3, "
                 "scope `none`).")


def half_up(x: float) -> int:
    return int(x + 0.5)


def kind_of(ref: str) -> str | None:
    return {"vocab": "vocab", "kanji": "kanji", "gram": "grammar", "kana": "kana"}.get(ref.split(":", 1)[0])


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def course_topics(root: Path) -> list[dict]:
    """Every topic in course order, with its lessons (full records) and level."""
    out = []
    for c in sorted(load(root / "course" / "manifest.json")["courses"], key=lambda c: c["order"]):
        cdir = root / "course" / c["level"]
        for t in load(cdir / "course.json")["topics"]:
            tdoc = load(cdir / t["path"])
            lessons = [load(cdir / s["path"]) for s in sorted(tdoc["lessons"], key=lambda s: s["order"])]
            out.append({"id": tdoc["id"], "level": c["level"], "title": tdoc["title"], "lessons": lessons})
    return out


def mix(size: int, counts: dict[str, int]) -> dict[str, int]:
    total = sum(counts.values())
    n = {k: max(1, half_up(size * c / total)) for k, c in counts.items()}
    by_share = sorted(counts, key=lambda k: (-counts[k], k))
    while sum(n.values()) > size:
        k = max((k for k in n if n[k] > 1), key=lambda k: (n[k], counts[k], k))
        n[k] -= 1
    while sum(n.values()) < size:
        n[by_share[0]] += 1
    return dict(sorted(n.items()))


class Corpus:
    """The registries the builder and its validator both read, loaded once per tree."""

    def __init__(self, root: Path):
        self.topics = course_topics(root)
        self.glyphs: dict[str, list[str]] = {}
        for script in ("hiragana", "katakana"):
            p = root / "corpus" / "kana" / f"{script}.json"
            for rec in (load(p) if p.exists() else []):
                self.glyphs.setdefault(rec["family"], []).append(rec["id"])
        self.head = {v["slug"]: v.get("headword") or "" for p in sorted(root.glob("corpus/vocab/*.json"))
                     for v in load(p)}
        self.sentences = {s["slug"]: s for s in load(root / "corpus" / "sentences" / "bank.json")}
        self.read_jp = {r["slug"]: r.get("jp", "") for p in sorted(root.glob("corpus/readings/*.json"))
                        for r in load(p)}
        self.banks: list[tuple[str, str, dict]] = []        # (level, section, item)
        for p in sorted((root / "corpus" / "exam_banks").glob("*.json")):
            m = BANK_RE.match(p.name)
            if m and m.group(2) in SECTION_FORM:
                self.banks += [(m.group(1), m.group(2), it) for it in load(p)]
        self.levels = [c["level"] for c in sorted(load(root / "course" / "manifest.json")["courses"],
                                                  key=lambda c: c["order"])]

    def scope_of(self, lessons: list[dict]) -> list[str]:
        out: list[str] = []
        for les in lessons:
            for u in les.get("unlocks") or []:
                refs = self.glyphs.get(u["ref"], []) if u["type"] == "kana-family" else [u["ref"]]
                out += [r for r in refs if kind_of(r) and r not in out]
        return out

    def exam_keys(self, section: str, it: dict) -> set[str]:
        keys = {it["vocab"]} if it.get("vocab") else set()
        if it.get("grammar"):
            keys.add(gram_slug(str(it["grammar"])))
        if section in ("kanji_reading", "orthography"):
            src = it.get("target") or self.head.get(it.get("vocab") or "", "")
            keys |= {f"kanji:{c}" for c in KANJI_RE.findall(src)}
        return keys

    def inside(self, section: str, it: dict, cks: dict[str, set[str]]) -> bool:
        """validate_exam_level_gate's per-item predicate, at one lesson's known set."""
        for s in visible_jp(it, section, self.read_jp):
            if any(f"kanji:{c}" not in cks["kanji"] for c in KANJI_RE.findall(s)):
                return False
        src = self.sentences.get(it.get("sentence") or "")
        if it.get("sentence") and src is None:
            return False
        vocab = ({it["vocab"]} if it.get("vocab") else set()) | {
            t["vocab"] for t in (src or {}).get("tokens") or [] if t.get("vocab")}
        gram = ({gram_slug(str(it["grammar"]))} if it.get("grammar") else set()) | {
            gram_slug(str(g)) for g in (src or {}).get("grammar") or []}
        if not vocab <= cks["vocab"] or not gram <= cks["grammar"]:
            return False
        return section not in PASSAGE_TYPES or bool(it.get("reading")) and it["reading"] in self.read_jp


def last_cks(topic: dict) -> dict[str, set[str]]:
    last = topic["lessons"][-1]
    return {k: set((last.get("cumulative_known_set") or {}).get(k) or [])
            for k in ("vocab", "kanji", "grammar")}


def build(root: Path, corpus: Corpus | None = None) -> tuple[list[dict], list[dict]]:
    c = corpus or Corpus(root)
    topics, banks, levels = c.topics, c.banks, c.levels
    scope_of, exam_keys, inside = c.scope_of, c.exam_keys, c.inside
    records, exempt = [], []
    for i, t in enumerate(topics):
        tail = t["id"].split(":", 1)[1]
        lessons = t["lessons"]
        kind, from_topic = "own", None
        if tail.endswith("-revisao"):
            start = i
            while start > 0 and topics[start - 1]["level"] == t["level"] \
                    and not topics[start - 1]["id"].endswith("-revisao"):
                start -= 1
            kind, from_topic = "range", topics[start]["id"]
            lessons = [les for tt in topics[start:i + 1] for les in tt["lessons"]]
        scope = scope_of(lessons)
        if not scope:
            exempt.append({"id": t["id"], "reason": EXEMPT_REASON})
            continue
        in_scope = set(scope)
        counts = {k: sum(1 for r in scope if kind_of(r) == k) for k in SCOPE_KINDS}
        counts = {k: c for k, c in counts.items() if c}
        size = min(24, max(12, half_up(len(scope) / 8)))
        cks = last_cks(t)
        pool: list[dict] = []
        for les in lessons:
            for ex in les.get("exercises") or []:
                refs = sorted({e["ref"] for e in ex.get("item_refs") or []
                               if e.get("role") == "target"} & in_scope)
                if refs:
                    pool.append({"ref": ex["id"], "source": "lesson_exercise", "form": ex["type"],
                                 "item_refs": [{"type": kind_of(r), "ref": r, "role": "target"}
                                               for r in refs]})
        top = levels.index(t["level"]) if t["level"] in levels else -1
        for lv, section, it in banks:
            if lv not in levels or levels.index(lv) > top:
                continue
            refs = sorted(exam_keys(section, it) & in_scope)
            if refs and inside(section, it, cks):
                pool.append({"ref": it["id"], "source": "exam_bank", "form": SECTION_FORM[section],
                             "item_refs": [{"type": kind_of(r), "ref": r, "role": "target"}
                                           for r in refs]})
        title = (t["title"] or {}).get(LOC) if isinstance(t["title"], dict) else t["title"]
        records.append({
            "slug": f"test:{tail}", "topic": t["id"], "level": t["level"],
            "title": {LOC: f"Teste do tópico: {title}"},
            "scope": {"kind": kind, "from_topic": from_topic, "items": scope},
            "size": size,
            "mix": {"by_kind": mix(size, counts),
                    "min_production": int(any(p["form"] == "production" for p in pool)),
                    "min_constructed": int(any(p["form"] in CONSTRUCTED for p in pool))},
            "pool": pool,
            "pass_rule": dict(PASS_RULE),
            "layer": "C", "needs_review": True,
        })
    return records, exempt


def render(records: list[dict], exempt: list[dict]) -> tuple[str, str]:
    tests = json.dumps(records, ensure_ascii=False, indent=1) + "\n"
    ex = json.dumps({
        "why": "Topics with no topic_test record, each with its reason (design/assessment.md §3.3, scope "
               "`none`). Read by scripts/validate/validate_topic_tests.py check A: an entry naming no "
               "topic, or a topic here that now teaches items, FAILS. Written by "
               "scripts/export/build_topic_tests.py.",
        "topics": exempt}, ensure_ascii=False, indent=2) + "\n"
    return tests, ex


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--check", action="store_true", help="measure only; write nothing")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    records, exempt = build(root)
    tests, ex = render(records, exempt)
    pools = [len(r["pool"]) for r in records]
    print(f"{len(records)} topic tests, {len(exempt)} exempt; pool entries {sum(pools)} "
          f"(min {min(pools)}, max {max(pools)}); sizes "
          f"{sorted({r['size'] for r in records})}")
    if not args.check:
        (root / "course" / "topic_tests.json").write_text(tests, encoding="utf-8")
        (root / "course" / "test_exemptions.json").write_text(ex, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
