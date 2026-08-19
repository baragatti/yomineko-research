#!/usr/bin/env python3
"""Apply the RE-AUTHORED Phase-6 lesson findings to research/derived/lessons/<slug>.json.

These are the 399 findings the first mechanical applier skipped, re-authored by a 61-agent pass and
staged in research/derived/phase6_reauthored/batch-*.json. 292 carry verdict "fix"; 141 came back
"no-change" (the complaint did not survive contact with the file) and 3 "needs-human". Only "fix" rows
are applied.

Why a new applier rather than fable5_lessons_apply_source.py: that one reads the ORIGINAL findings file
and its own anchor semantics. These rows carry anchors copied byte-exact out of the lesson files, and
they address fields by path (exercises[3].answer.choices[2]), which the old one cannot express. The
GUARDS are deliberately the same, because each of them caught a real corruption:

  instruction-as-value   a fix containing "->", "should be", "Substituir ..." is refused. This session
                         found two grammar explanations that shipped edit orders TO LEARNERS, so the
                         guard is not theoretical.
  tag balance            for `body`, the open/close tag multiset must be identical before and after.
  tag spans              if the fix contains no markup, every literal <...> span must be byte-identical
                         after the edit. Balance alone once let Portuguese in as a <jp> attribute.
  leaf-only              objectives is a LIST and exercises[i].answer is an OBJECT {choices, correct}.
                         Only the addressed leaf is rewritten, never the container.
  anchor must exist      a missing anchor is a SKIP, never a wholesale overwrite.

Also honours one cross-batch collision the reviewers found: batch-07 and batch-08 both rewrite
les:n3-limites-01 exercises[0].answer. Applied in order, batch-07 invalidates batch-08's choices[3]
anchor while batch-08's choices[2] fix still lands, leaving TWO IDENTICAL DISTRACTORS in one
multiple-choice item. Batch-07's row is dropped; batch-08 resolves both and keeps them distinct.

Run load_lessons.py + validate_all.py afterwards.
Usage: apply_phase6_reauthored.py [--apply]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "research" / "derived" / "phase6_reauthored"
LESSONS = ROOT / "research" / "derived" / "lessons"
INSTRUCTION = re.compile(
    r"^(replace|change|set|update|remove|delete|drop|add|apply|keep|rewrite|fix|minimal|split|trocar|"
    r"corrigir|substituir|no body|just |only )\b|->|→|\bshould be\b|\bmust be\b|Substituir a frase", re.I)
TAGS = re.compile(r"</?([a-zA-Z][\w-]*)[^>]*>")
SPANS = re.compile(r"<[^>]*>")
# (batch, slug, field) rows the reviewers agreed to drop.
COLLISIONS = {(7, "les:n3-limites-01", "exercises[0].answer")}


def leaf(obj, path: str):
    """Walk a dotted/indexed path and return (container, key) so only the LEAF is ever rewritten."""
    cur = obj
    parts = re.findall(r"([A-Za-z_]+)|\[(\d+)\]", path)
    chain = []
    for name, idx in parts:
        chain.append(name if name else int(idx))
    for k in chain[:-1]:
        if isinstance(k, int):
            if not isinstance(cur, list) or k >= len(cur):
                return None, None
            cur = cur[k]
        else:
            if not isinstance(cur, dict) or k not in cur:
                return None, None
            cur = cur[k]
    return cur, chain[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = []
    for p in sorted(STAGE.glob("batch-*.json")):
        b = int(p.stem.split("-")[1])
        for x in json.loads(p.read_text(encoding="utf-8")).get("fixes", []):
            if x.get("verdict") == "fix":
                x["_batch"] = b
                rows.append(x)
    print(f"{len(rows)} fix rows staged")

    applied, skipped = Counter(), []
    by_slug: dict[str, list] = {}
    for x in rows:
        by_slug.setdefault(x["slug"], []).append(x)

    for slug, items in sorted(by_slug.items()):
        fp = LESSONS / (slug.split(":", 1)[1] + ".json")
        if not fp.exists():
            skipped += [(slug, i["field"], "lesson file not found") for i in items]
            continue
        rec = json.loads(fp.read_text(encoding="utf-8"))
        dirty = False
        for x in sorted(items, key=lambda r: r["_batch"]):
            field, cur, fix = x["field"], x.get("current") or "", x.get("fix") or ""
            if (x["_batch"], slug, field) in COLLISIONS:
                skipped.append((slug, field, "dropped: cross-batch collision (reviewers)")); continue
            if not fix or INSTRUCTION.search(fix):
                skipped.append((slug, field, "fix is an instruction, not a value")); continue
            container, key = leaf(rec, field)
            if container is None:
                skipped.append((slug, field, "path does not resolve")); continue
            try:
                stored = container[key]
            except Exception:
                skipped.append((slug, field, "leaf missing")); continue
            if not isinstance(stored, str):
                skipped.append((slug, field, f"leaf is {type(stored).__name__}, not a string")); continue
            if cur and cur not in stored:
                skipped.append((slug, field, "anchor not found")); continue
            new = stored.replace(cur, fix, 1) if cur else fix
            if field.split("[")[0] == "body" or "<" in stored:
                if Counter(TAGS.findall(new)) != Counter(TAGS.findall(stored)):
                    skipped.append((slug, field, "would change markup tag balance")); continue
                if "<" not in fix and Counter(SPANS.findall(new)) != Counter(SPANS.findall(stored)):
                    skipped.append((slug, field, "plain fix would alter a tag's contents")); continue
            container[key] = new
            applied.update([field.split("[")[0]])
            dirty = True
        if dirty and args.apply:
            fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (STAGE / "_apply_skipped.json").write_text(json.dumps(
        {"note": "Rows NOT applied. Nothing was guessed at.",
         "skipped": [{"slug": s, "field": f, "why": w} for s, f, w in skipped]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"apply ({'APPLIED' if args.apply else 'dry-run'}): {sum(applied.values())} fields "
          f"{dict(applied)}")
    print(f"skipped {len(skipped)}: {dict(Counter(w for _, _, w in skipped).most_common(6))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
