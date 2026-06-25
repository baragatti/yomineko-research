#!/usr/bin/env python3
"""Apply AI accent-restoration pairs to N3 lesson files (whole-word, case-aware), in body + exercise text.
Usage: apply_accent_pairs.py <workflow_output.json>"""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
r = raw.get("result", raw)
if isinstance(r, str):
    r = json.loads(r[r.index("{"):])
items = r.get("items", [])
BAD = re.compile(r"[—≠\]")


def cap(rep, matched):
    return rep[:1].upper() + rep[1:] if matched[:1].isupper() else rep


def apply_pairs(s, pairs):
    for st, ac in pairs:
        if not st or not ac or st == ac or BAD.search(ac):
            continue
        s = re.sub(r"(?<![0-9A-Za-zÀ-ÿ])" + re.escape(st) + r"(?![0-9A-Za-zÀ-ÿ])",
                   lambda m: cap(ac, m.group(0)), s, flags=re.IGNORECASE)
    return s


def walk(v, pairs):
    if isinstance(v, str):
        return apply_pairs(v, pairs)
    if isinstance(v, list):
        return [walk(x, pairs) for x in v]
    if isinstance(v, dict):
        return {k: (v[k] if k in ("slug", "topic", "type", "ref") else walk(v[k], pairs)) for k in v}
    return v


n = 0
for it in items:
    slug = it["slug"].replace("les:", "")
    pairs = [p for p in it.get("pairs", []) if len(p) == 2]
    if not pairs:
        continue
    f = LDIR / (slug + ".json")
    if not f.exists():
        print("  skip missing", slug); continue
    obj = json.loads(f.read_text(encoding="utf-8"))
    # apply only to learner text: body + exercises (prompt/explanation/answer), title/description/objectives
    for k in ("title", "description", "body"):
        obj[k] = apply_pairs(obj.get(k, ""), pairs)
    obj["objectives"] = [apply_pairs(o, pairs) for o in obj.get("objectives", [])]
    for ex in obj.get("exercises", []):
        ex["prompt"] = apply_pairs(ex.get("prompt", ""), pairs)
        ex["explanation"] = apply_pairs(ex.get("explanation", ""), pairs)
        ex["answer"] = walk(ex.get("answer", {}), pairs)
    f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n += 1
print(f"applied accent pairs to {n} lessons ({sum(len(i.get('pairs',[])) for i in items)} pairs total)")
