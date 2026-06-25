#!/usr/bin/env python3
"""Insert up to 2 <sentence ref> cards into each N3 lesson body, choosing real N3 bank sentences linked
to the grammar that lesson unlocks (parity with N4 lessons' dissected-sentence cards). Inserts before the
'Hora de praticar' exercise section (or before the checklist). Idempotent (skips if lesson already has refs).
"""
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
# grammar key -> list of n3 sentence slugs (linked), shortest first
g2s = {}
for key, slug, jp in con.execute(
    "SELECT g.key, s.slug, s.jp FROM grammar_point g JOIN sentence_grammar sg ON sg.grammar_id=g.id "
    "JOIN sentence s ON s.id=sg.sentence_id WHERE s.level='n3' ORDER BY LENGTH(s.jp)"):
    g2s.setdefault(key, []).append(slug)
con.close()
used = set()
n = 0
for f in sorted(LDIR.glob("n3-*.json")):
    obj = json.loads(f.read_text(encoding="utf-8"))
    body = obj.get("body", "")
    if "<sentence ref" in body:
        continue
    gkeys = [u["ref"].split(":", 1)[1] for u in obj.get("unlocks", []) if u["type"] == "grammar"]
    picks = []
    for k in gkeys:
        for slug in g2s.get(k, []):
            if slug not in used and slug not in picks:
                picks.append(slug); used.add(slug); break
        if len(picks) >= 2:
            break
    if not picks:
        continue
    cards = "\n" + "".join(f'<sentence ref="{s}" show="furigana" mode="card"/>\n' for s in picks)
    anchor = '<heading level="3"><text>Hora de praticar</text></heading>'
    if anchor in body:
        nb = body.replace(anchor, '<heading level="3"><text>Exemplos do banco</text></heading>' + cards + anchor, 1)
    else:
        nb = re.sub(r'(<checklist>)', cards + r'\1', body, count=1)
    if nb != body:
        obj["body"] = nb
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
print(f"wired sentence cards into {n} N3 lessons ({len(used)} sentences featured)")
