#!/usr/bin/env python3
"""Revert numeric vocab/kanji id-refs in N3 lessons back to headword/character refs (body chips) and drop the
numeric unlocks. Resets to a clean headword-only state before a single authoritative homograph pass.
Idempotent. Usage: revert_n3_id_refs.py"""
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
v2hw = {str(r[0]): r[1] for r in con.execute("SELECT id,headword FROM vocab")}
k2ch = {str(r[0]): r[1] for r in con.execute("SELECT id,character FROM kanji")}
con.close()

NUM = re.compile(r'<(vocab|kanji) ref="(vocab|kanji):(\d+)"\s*/>')


def repl(m):
    typ, ns, vid = m.group(1), m.group(2), m.group(3)
    table = v2hw if ns == "vocab" else k2ch
    ident = table.get(vid)
    return f'<{typ} ref="{ns}:{ident}"/>' if ident else m.group(0)


n = 0
for f in sorted(LDIR.glob("n3-*.json")):
    obj = json.loads(f.read_text(encoding="utf-8"))
    body = obj.get("body", "")
    nb = NUM.sub(repl, body)
    unl = [u for u in obj.get("unlocks", []) if not re.fullmatch(r"(vocab|kanji):\d+", u.get("ref", ""))]
    if nb != body or len(unl) != len(obj.get("unlocks", [])):
        obj["body"] = nb
        obj["unlocks"] = unl
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
print(f"reverted id-refs to headword in {n} N3 lessons")
