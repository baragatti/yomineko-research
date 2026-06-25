#!/usr/bin/env python3
"""Place homograph 'loser' N3 vocab. When two vocab share a headword (上=かみ vs 上=じょう), the ambiguous
ref vocab:<headword> resolves to only one id; the other stays unplaced. The lesson body still references it
as vocab:<headword> right before its distinguishing kana reading "(かみ)". This converts THAT occurrence to
the unambiguous vocab:<id> ref and adds the matching unlock, so the alternate reading gets taught/placed.
Idempotent. Usage: fix_n3_homograph_refs.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
unplaced = {r[0]: (r[1], r[2]) for r in con.execute(
    "SELECT id,headword,kana FROM vocab WHERE level='n3' AND introducing_topic_id IS NULL")}
con.close()

done: set[int] = set()
nfix = 0
for f in sorted(LDIR.glob("n3-*.json")):
    obj = json.loads(f.read_text(encoding="utf-8"))
    body = obj.get("body", "")
    have = {u["ref"] for u in obj.get("unlocks", [])}
    changed = False
    for vid, (hw, kana) in unplaced.items():
        if vid in done or not kana:
            continue
        pat = f'<vocab ref="vocab:{hw}"/>'
        idpat = f'<vocab ref="vocab:{vid}"/>'
        start = 0
        while True:
            i = body.find(pat, start)
            if i < 0:
                break
            seg = body[i + len(pat): i + len(pat) + 30]
            if f"({kana})" in seg:
                body = body[:i] + idpat + body[i + len(pat):]
                ref = f"vocab:{vid}"
                if ref not in have:
                    obj.setdefault("unlocks", []).append({"type": "vocab", "ref": ref})
                    have.add(ref)
                done.add(vid)
                changed = True
                break
            start = i + len(pat)
    if changed:
        obj["body"] = body
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        nfix += 1
print(f"converted homograph refs in {nfix} lessons; placed {len(done)}/{len(unplaced)} orphans by id")
still = [f"{v[0]}({v[1]},id{k})" for k, v in unplaced.items() if k not in done]
if still:
    print("  still unplaced:", ", ".join(still))
