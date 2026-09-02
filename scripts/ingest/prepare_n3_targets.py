#!/usr/bin/env python3
"""W13 step 1 — the DETERMINISTIC work list for the N3 exemplification campaign (APP_PLAN W13; the
readiness gaps G1, G4, G9 in research/reports/readiness/content_coverage_levels.md).

A target is a taught N3 item that the bank under-exemplifies:
  * vocab   — fewer than 3 bank sentences carry a token linked to its slug   (G1: 1,461 at zero)
  * grammar — fewer than 5 bank sentences tagged with its key                (G4: 17 at zero)

For each target this records the lesson that introduces it (every N3 vocab and grammar record is
unlocked exactly once, by exactly one lesson) and that lesson's `cumulative_known_set` — the i+1
boundary a mined sentence for that target has to respect. The known set is stored ONCE per lesson
under `lessons` and referenced by id; inlining ~2,000 slugs per target would multiply a 4 MB file by
a thousand for no information.

Reads only the committed export (corpus/*.json, course/**/lesson-*.json). It does NOT touch
db/corpus.sqlite: the DB is a regenerable index (CLAUDE.md) and W01 is diffing it.

Output: research/derived/n3_targets.json.  Usage: prepare_n3_targets.py [--batch-size 50]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "derived" / "n3_targets.json"
VOCAB_THRESHOLD = 3
GRAMMAR_THRESHOLD = 5


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lesson_order() -> dict[str, int]:
    """Global position of every topic slug, from course/outline.json (module order, topic order)."""
    pos: dict[str, int] = {}
    for module in sorted(load(ROOT / "course" / "outline.json"), key=lambda m: m["order"]):
        for topic in sorted(module["topics"], key=lambda t: t["order"]):
            pos[topic["slug"]] = len(pos)
    return pos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=50)
    args = ap.parse_args()

    bank = load(ROOT / "corpus" / "sentences" / "bank.json")
    vocab = load(ROOT / "corpus" / "vocab" / "n3.json")
    grammar = load(ROOT / "corpus" / "grammar" / "n3.json")

    # ── coverage, counted the way the readiness audit counts it ───────────────────────────────
    # a sentence counts once for a vocab record however many of its tokens link to that record
    vcount: dict[str, int] = {}
    gcount: dict[str, int] = {}
    for s in bank:
        for slug in {t["vocab"] for t in s["tokens"] if t.get("vocab")}:
            vcount[slug] = vcount.get(slug, 0) + 1
        for key in set(s.get("grammar") or []):
            gcount[key] = gcount.get(key, 0) + 1

    # ── the introducing lesson of every unlocked ref, and each lesson's known set ─────────────
    topic_pos = lesson_order()
    lessons: dict[str, dict] = {}
    introduces: dict[str, str] = {}
    for f in sorted((ROOT / "course").glob("*/topic-*/lesson-*.json")):
        d = load(f)
        lid = d["id"]
        lessons[lid] = {
            "file": f.relative_to(ROOT).as_posix(),
            "level": d["level"],
            "topic": d["topic"],
            "order": d["order"],
            "global_order": (topic_pos.get(d["topic"], 9999), d["order"]),
            "title": d["title"],
            "cumulative_known_set": {
                k: d["cumulative_known_set"].get(k, [])
                for k in ("vocab", "kanji", "grammar")
            },
        }
        for u in d.get("unlocks", []):
            introduces.setdefault(u["ref"], lid)

    # ── targets ──────────────────────────────────────────────────────────────────────────────
    targets: list[dict] = []
    for r in vocab:
        n = vcount.get(r["slug"], 0)
        if n >= VOCAB_THRESHOLD:
            continue
        surfaces: list[str] = []
        for s in [r["headword"], r["kana"]] + [f["form"] for f in r.get("forms") or []]:
            if s and s not in surfaces:
                surfaces.append(s)
        sense = (r.get("senses") or [{}])[0]
        targets.append({
            "target_id": r["slug"],
            "kind": "vocab",
            "headword": r["headword"],
            "kana": r["kana"],
            "romaji": r["romaji"],
            "surfaces": surfaces,
            "pos": sense.get("pos") or [],
            "gloss": {
                "pt-BR": (sense.get("gloss", {}).get("pt-BR") or [])[:3],
                "en": (sense.get("gloss", {}).get("en") or [])[:3],
            },
            "have": n,
            "threshold": VOCAB_THRESHOLD,
            "need": VOCAB_THRESHOLD - n,
            "lesson": introduces.get(r["slug"]),
        })
    for r in grammar:
        n = gcount.get(r["key"], 0)
        if n >= GRAMMAR_THRESHOLD:
            continue
        targets.append({
            "target_id": r["slug"],
            "kind": "grammar",
            "key": r["key"],
            "label": r["label"],
            "structure_pattern": r.get("structure_pattern"),
            "forms": [f["form"] for f in r.get("forms") or [] if f.get("form")],
            "have": n,
            "threshold": GRAMMAR_THRESHOLD,
            "need": GRAMMAR_THRESHOLD - n,
            "lesson": introduces.get(r["slug"]),
        })

    # deterministic order: course position of the introducing lesson, then grammar before its
    # vocabulary (a point is worth more examples), then slug.
    def sort_key(t: dict):
        les = lessons.get(t["lesson"] or "")
        go = tuple(les["global_order"]) if les else (9999, 9999)
        return (go, 0 if t["kind"] == "grammar" else 1, t["target_id"])

    targets.sort(key=sort_key)
    for i, t in enumerate(targets):
        t["batch"] = i // args.batch_size + 1

    used = {t["lesson"] for t in targets if t["lesson"]}
    payload = {
        "generated": date.today().isoformat(),
        "unit": "W13 — N3 exemplification (APP_PLAN §3; gaps G1/G4/G9)",
        "source": "corpus/sentences/bank.json + corpus/vocab/n3.json + corpus/grammar/n3.json + "
                  "course/**/lesson-*.json (committed export; the DB is not read)",
        "method": {
            "vocab": f"N3 registry records with < {VOCAB_THRESHOLD} distinct bank sentences whose "
                     "tokens carry vocab=<slug>",
            "grammar": f"N3 registry records with < {GRAMMAR_THRESHOLD} distinct bank sentences "
                       "whose grammar[] carries the record key",
            "known_set": "the introducing lesson's cumulative_known_set, which already contains the "
                         "target itself; stored once per lesson under `lessons`",
        },
        "thresholds": {"vocab": VOCAB_THRESHOLD, "grammar": GRAMMAR_THRESHOLD},
        "batch_size": args.batch_size,
        "counts": {
            "vocab_targets": sum(1 for t in targets if t["kind"] == "vocab"),
            "vocab_at_zero": sum(1 for t in targets if t["kind"] == "vocab" and t["have"] == 0),
            "grammar_targets": sum(1 for t in targets if t["kind"] == "grammar"),
            "grammar_at_zero": sum(1 for t in targets if t["kind"] == "grammar" and t["have"] == 0),
            "targets": len(targets),
            "batches": (len(targets) + args.batch_size - 1) // args.batch_size,
            "lessons_involved": len(used),
        },
        "lessons": {k: v for k, v in lessons.items() if k in used},
        "targets": targets,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(payload["counts"], indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
