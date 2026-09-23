#!/usr/bin/env python3
"""W23. course/item_lesson_index.json: for every question, the lesson that first makes it answerable.

Every placement question reduces to this one join (design/assessment.md §5.1), so it is published as a
generated MAP rather than recomputed per request: a probe that has to load 322 lesson files to ask one
question is a probe nobody ships. It is a cache in the same class as course/outline.json and it is
guarded by scripts/validate/validate_placement_index.py, whose real check is that `build()` reproduces
the committed bytes.

    { "<question id>": {"lesson": "les:...", "level": "n5", "via": "<rule>"}, ... }

Resolution, in order (the first that answers wins):
  exercise   a lesson exercise (ex:...) belongs to its own lesson
  vocab      an exam item's `vocab` slug -> the one lesson that unlocks it (the unlock ledger)
  grammar    an exam item's bare `grammar` key -> gram:<key> -> its lesson (the normalization the
             readiness audit's 73.7% was missing)
  reading    an exam item's `reading` -> that passage's `gated_to_lesson`
  sentence   the cited sentence's own dissection (token vocab slugs + grammar tags) -> the LATEST
             lesson among the items it names that the course unlocks at all
An item none of these answers is left out (listening items carry no key; they are excluded from every
paper while audio is pending). Reads the exported tree only. Deterministic.
Usage: build_item_lesson_index.py [--root PATH] [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO = Path(__file__).resolve().parents[2]
OUT_REL = "course/item_lesson_index.json"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def build(root: Path) -> dict[str, dict]:
    manifest = load(root / "course" / "manifest.json")
    lessons: list[dict] = []
    for c in sorted(manifest["courses"], key=lambda c: c["order"]):
        cdir = root / "course" / c["level"]
        for t in load(cdir / "course.json")["topics"]:
            tdoc = load(cdir / t["path"])
            lessons += [load(cdir / s["path"]) for s in sorted(tdoc["lessons"], key=lambda s: s["order"])]
    pos = {les["id"]: i for i, les in enumerate(lessons)}
    level = {les["id"]: les.get("level") for les in lessons}
    home: dict[str, str] = {}
    for les in lessons:
        for u in les.get("unlocks") or []:
            home.setdefault(u["ref"], les["id"])
    gated = {r["slug"]: r.get("gated_to_lesson") for p in sorted(root.glob("corpus/readings/*.json"))
             for r in load(p)}
    sents = {s["slug"]: s for s in load(root / "corpus" / "sentences" / "bank.json")}

    out: dict[str, dict] = {}

    def put(qid: str, lid: str | None, via: str) -> bool:
        if lid in pos:
            out[qid] = {"lesson": lid, "level": level[lid], "via": via}
            return True
        return False

    for les in lessons:
        for ex in les.get("exercises") or []:
            put(ex["id"], les["id"], "exercise")
    for p in sorted((root / "corpus" / "exam_banks").glob("n*_*.json")):
        for it in load(p):
            qid = it["id"]
            if it.get("vocab") and put(qid, home.get(it["vocab"]), "vocab"):
                continue
            if it.get("grammar"):
                g = str(it["grammar"])
                if put(qid, home.get(g if g.startswith("gram:") else f"gram:{g}"), "grammar"):
                    continue
            if it.get("reading") and put(qid, gated.get(it["reading"]), "reading"):
                continue
            s = sents.get(it.get("sentence") or "")
            if s:
                refs = {t["vocab"] for t in s.get("tokens") or [] if t.get("vocab")}
                refs |= {f"gram:{g}" for g in s.get("grammar") or []}
                homes = [home[r] for r in refs if home.get(r) in pos]
                if homes:
                    put(qid, max(homes, key=lambda lid: pos[lid]), "sentence")
    return dict(sorted(out.items()))


def render(index: dict[str, dict]) -> str:
    return json.dumps(index, ensure_ascii=False, indent=1) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    index = build(root)
    vias: dict[str, int] = {}
    for v in index.values():
        vias[v["via"]] = vias.get(v["via"], 0) + 1
    n_exam = sum(len(load(p)) for p in (root / "corpus" / "exam_banks").glob("n*_*.json"))
    print(f"{len(index)} questions indexed {dict(sorted(vias.items()))}; exam items "
          f"{len(index) - vias.get('exercise', 0)} of {n_exam}")
    if not args.check:
        (root / OUT_REL).write_text(render(index), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
