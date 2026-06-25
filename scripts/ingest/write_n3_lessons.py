#!/usr/bin/env python3
"""Write authored N3 lessons (from the lesson-authoring workflow output) to research/derived/lessons/*.json
in the canonical load_lessons shape, adding the structural fields the agents did not return.
Usage: write_n3_lessons.py <workflow_output.json>"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "derived" / "lessons"
DB = ROOT / "db" / "corpus.sqlite"


def topic_of(slug: str) -> str:
    s = re.sub(r"^les:", "", slug)
    s = re.sub(r"-\d+$", "", s)
    return f"top:{s}"


def main() -> int:
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    r = raw.get("result", raw)
    if isinstance(r, str):
        r = json.loads(r[r.index("{"):])
    lessons = r.get("lessons", [])
    con = sqlite3.connect(DB)
    valid_topics = {row[0] for row in con.execute("SELECT slug FROM topic")}
    con.close()
    written, skipped = 0, []
    for L in lessons:
        slug = L.get("slug", "")
        if not slug.startswith("les:"):
            slug = "les:" + slug
            L["slug"] = slug
        slug = re.sub(r"^les:(pre-n5|n5|n4|n3)(?!-)", r"les:\1-", slug)
        topic = topic_of(slug)
        if topic not in valid_topics and not slug.startswith("les:n3-"):
            slug = "les:n3-" + re.sub(r"^les:", "", slug)  # agent dropped the n3- prefix
            topic = topic_of(slug)
        L["slug"] = slug
        if topic not in valid_topics:
            skipped.append(f"{slug} -> unknown topic {topic}")
            continue
        exs = []
        for e in L.get("exercises", []):
            exs.append({"slug": e["slug"], "type": e["type"], "prompt": e.get("prompt", ""),
                        "answer": e.get("answer", {}), "explanation": e.get("explanation", ""),
                        "sentence_refs": [], "item_refs": []})
        rec = {
            "slug": slug, "topic": topic, "order": L.get("order", 1), "schema_version": "1.0",
            "title": L.get("title", ""), "description": L.get("description", ""),
            "objectives": L.get("objectives", []),
            "needs": [], "unlocks": L.get("unlocks", []), "feature_unlocks": [],
            "sentence_refs": [], "body": L.get("body", ""), "exercises": exs,
        }
        fn = OUT / (re.sub(r"^les:", "", slug) + ".json")
        fn.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
    print(f"wrote {written} N3 lesson files; skipped {len(skipped)}")
    for s in skipped[:20]:
        print("  SKIP", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
