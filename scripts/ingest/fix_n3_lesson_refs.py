#!/usr/bin/env python3
"""Fix N3 lesson ref issues from authoring: (1) exercise slugs missing the 'ex:' prefix; (2) unlocks whose
ref does not resolve to the registry; (3) body chips (<vocab/grammar/kanji ref>) that do not resolve.
Idempotent. Usage: fix_n3_lesson_refs.py"""
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
LDIR = ROOT / "research" / "derived" / "lessons"
con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
VOCAB = {r[0] for r in con.execute("SELECT headword FROM vocab")} | {str(r[0]) for r in con.execute("SELECT id FROM vocab")}
KANJI = {r[0] for r in con.execute("SELECT character FROM kanji")}
GRAM = {r[0] for r in con.execute("SELECT key FROM grammar_point")}
con.close()


def resolves(ref):
    if ":" not in ref:
        return False
    ns, ident = ref.split(":", 1)
    return (ns == "vocab" and ident in VOCAB) or (ns == "kanji" and ident in KANJI) or (ns == "gram" and ident in GRAM)


nfix = 0
for f in sorted(LDIR.glob("n3-*.json")):
    obj = json.loads(f.read_text(encoding="utf-8"))
    changed = False
    # 1) exercise slugs need ex: prefix
    for e in obj.get("exercises", []):
        if not e["slug"].startswith("ex:"):
            e["slug"] = "ex:" + e["slug"]; changed = True
    # 2) unlocks must resolve
    keep = []
    for u in obj.get("unlocks", []):
        if u["type"] == "grammar" and u["ref"] in ("gram:" + k for k in GRAM):
            keep.append(u)
        elif u["type"] in ("vocab", "kanji") and resolves(u["ref"]):
            keep.append(u)
        else:
            changed = True
    obj["unlocks"] = keep
    # 3) drop non-resolving body chips
    def chip_ok(m):
        return m.group(0) if resolves(m.group(2)) else ""
    nb = re.sub(r'<(vocab|grammar|kanji) ref="([^"]*)"\s*/>', chip_ok, obj.get("body", ""))
    if nb != obj.get("body", ""):
        obj["body"] = nb; changed = True
    if changed:
        f.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        nfix += 1
print(f"fixed refs in {nfix} N3 lessons")
