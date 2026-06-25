#!/usr/bin/env python3
"""Remove empty inline tags (<text></text>, <emphasis></emphasis>, ...) from N3 lesson bodies. Idempotent."""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LDIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"
EMPTY = re.compile(r"<(text|emphasis|romaji|term)(?:\s[^>]*)?></\1>")
n = 0
for f in sorted(LDIR.glob("n3-*.json")):
    obj = json.loads(f.read_text(encoding="utf-8"))
    b = obj.get("body", "")
    nb = b
    while EMPTY.search(nb):
        nb = EMPTY.sub("", nb)
    if nb != b:
        obj["body"] = nb
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
print(f"stripped empty inline tags in {n} N3 lessons")
