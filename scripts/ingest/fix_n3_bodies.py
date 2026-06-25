#!/usr/bin/env python3
"""Repair regular tag bugs in N3 lesson bodies from the re-author pass:
 1) pull inline chips placed right after </heading> back INSIDE the heading (heading accepts inline);
 2) wrap bare leading heading text in <text>;
 3) fix mis-slashed opening term tag </term define=...> -> <term define=...>.
Idempotent; only touches malformed spots. Usage: fix_n3_bodies.py"""
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
LDIR = Path(__file__).resolve().parents[2] / "research" / "derived" / "lessons"
CHIP = r'(?:<(?:grammar|vocab|kanji) ref="[^"]*"\s*/>)'
move_chip = re.compile(r'</heading>((?:' + CHIP + r')+)')
wrap_head = re.compile(r'(<heading level="\d">)([^<]+)')
term_open = re.compile(r'</term (define=)')
n = 0
for f in sorted(LDIR.glob("n3-*.json")):
    obj = json.loads(f.read_text(encoding="utf-8"))
    b = obj.get("body", "")
    nb = move_chip.sub(lambda m: m.group(1) + "</heading>", b)
    nb = wrap_head.sub(lambda m: m.group(1) + "<text>" + m.group(2) + "</text>", nb)
    nb = term_open.sub(r"<term \1", nb)
    if nb != b:
        obj["body"] = nb
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
print(f"fixed bodies in {n} N3 lessons")
