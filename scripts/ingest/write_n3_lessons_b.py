#!/usr/bin/env python3
"""Merge Tranche-3 authored lessons (workflow output) with their specs and write canonical
research/derived/lessons/*.json records. Unlocks are derived from what the BODY actually references
(intersected with the spec's assigned vocab/kanji) so body-refs subset unlocks holds by construction;
any assigned item the author failed to introduce is reported as still-unplaced.
Usage: write_n3_lessons_b.py <workflow_output.json>"""
from __future__ import annotations
import html, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "derived" / "lessons"
SPECS = ROOT / "research" / "_n3_lesson_inputs_b.json"

VREF = re.compile(r'<vocab ref="vocab:([^"]+)"')
KREF = re.compile(r'<kanji ref="kanji:([^"]+)"')


def main() -> int:
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    r = raw.get("result", raw)
    if isinstance(r, str):
        r = json.loads(r[r.index("{"):])
    authored = {L["slug"]: L for L in r.get("lessons", [])}
    specs = {s["slug"]: s for s in json.loads(SPECS.read_text(encoding="utf-8"))}

    global_unlocked: set[str] = set()
    written = 0
    missing_lessons = []
    offspec: list = []
    unplaced_v: list[str] = []
    unplaced_k: list[str] = []
    for slug, spec in specs.items():
        L = authored.get(slug)
        if not L:
            missing_lessons.append(slug)
            continue
        body = html.unescape(L.get("body", ""))
        assigned_v = {v["hw"] for v in spec["vocab"]}
        assigned_k = {k["k"] for k in spec["kanji"]}
        all_body_v = VREF.findall(body)
        all_body_k = KREF.findall(body)
        off_v = [h for h in all_body_v if h not in assigned_v]
        off_k = [c for c in all_body_k if c not in assigned_k]
        if off_v or off_k:
            offspec.append((slug, off_v, off_k))
        body_v = [h for h in all_body_v if h in assigned_v]
        body_k = [c for c in all_body_k if c in assigned_k]
        unlocks = []
        for h in dict.fromkeys(body_v):                      # dedup, keep order
            ref = f"vocab:{h}"
            if ref not in global_unlocked:
                unlocks.append({"type": "vocab", "ref": ref}); global_unlocked.add(ref)
        for c in dict.fromkeys(body_k):
            ref = f"kanji:{c}"
            if ref not in global_unlocked:
                unlocks.append({"type": "kanji", "ref": ref}); global_unlocked.add(ref)
        unplaced_v += [h for h in assigned_v if h not in set(body_v)]
        unplaced_k += [c for c in assigned_k if c not in set(body_k)]
        def uesc(x):
            if isinstance(x, str):
                return html.unescape(x)
            if isinstance(x, list):
                return [uesc(i) for i in x]
            if isinstance(x, dict):
                return {k: uesc(v) for k, v in x.items()}
            return x
        exs = []
        for e in L.get("exercises", []):
            exs.append({"slug": e["slug"], "type": e["type"], "prompt": uesc(e.get("prompt", "")),
                        "answer": uesc(e.get("answer", {})), "explanation": uesc(e.get("explanation", "")),
                        "sentence_refs": [], "item_refs": []})
        rec = {
            "slug": slug, "topic": spec["topic"], "order": spec["order"], "schema_version": "1.0",
            "title": uesc(L.get("title", "")), "description": uesc(L.get("description", "")),
            "objectives": uesc(L.get("objectives", [])),
            "needs": [], "unlocks": unlocks, "feature_unlocks": [],
            "sentence_refs": [], "body": body, "exercises": exs,
        }
        fn = OUT / (re.sub(r"^les:", "", slug) + ".json")
        fn.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
    print(f"wrote {written}/{len(specs)} lessons; missing lessons={len(missing_lessons)}")
    if missing_lessons:
        print("  MISSING:", ", ".join(missing_lessons[:20]))
    print(f"unplaced after pass: vocab={len(set(unplaced_v))} kanji={len(set(unplaced_k))}")
    if unplaced_v:
        print("  unplaced vocab sample:", ", ".join(sorted(set(unplaced_v))[:25]))
    if unplaced_k:
        print("  unplaced kanji:", ", ".join(sorted(set(unplaced_k))))
    if offspec:
        print(f"off-spec body refs in {len(offspec)} lessons (will be checked by fixers):")
        for slug, ov, ok in offspec[:15]:
            print(f"  {slug}: vocab{ov} kanji{ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
