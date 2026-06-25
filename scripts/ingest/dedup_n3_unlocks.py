#!/usr/bin/env python3
"""Enforce introduce-once: drop N3 lesson unlocks already claimed by an earlier lesson (N5/N4, or an
earlier-ordered N3 lesson). Body chips are left intact (they still resolve; the item is just review here).
Idempotent. Usage: dedup_n3_unlocks.py"""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
torder = {t["slug"].replace("top:", ""): t["order"] for t in json.loads((ROOT / "research" / "_n3_topics.json").read_text(encoding="utf-8"))}

seen = set()
# 1) all non-N3 unlocks are already taught earlier (N5/N4/pre-n5)
for f in sorted(LDIR.glob("*.json")):
    if f.name.startswith("n3-"):
        continue
    obj = json.loads(f.read_text(encoding="utf-8"))
    for u in obj.get("unlocks", []):
        seen.add(u["ref"])


def keyf(f):
    m = re.match(r"(n3-[a-z]+)-(\d+)", f.stem)
    topic, num = m.group(1), int(m.group(2))
    return (torder.get(topic, 999), num)


n = 0
for f in sorted(LDIR.glob("n3-*.json"), key=keyf):
    obj = json.loads(f.read_text(encoding="utf-8"))
    keep = []
    for u in obj.get("unlocks", []):
        if u["ref"] in seen:
            continue
        keep.append(u)
        seen.add(u["ref"])
    if len(keep) != len(obj.get("unlocks", [])):
        obj["unlocks"] = keep
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
print(f"deduped unlocks in {n} N3 lessons")
