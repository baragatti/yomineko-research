#!/usr/bin/env python3
"""Apply the round-2 pt_literal corrections to the ingested mined sentences.

pt_literal is the structure-revealing gloss: deliberately near-literal and a little awkward, but it must
still be grammatical Portuguese and it must reveal the Japanese structure HONESTLY. A sweep of all 324
found 10 rows where it did not:

  * two more intransitive verbs glossed as passives (聞こえる, 見当たる) — the same defect already fixed
    in the authoring pass for 84152's が, and the reason it matters is that 自動詞/他動詞 pairs are
    exactly what a beginner is trying to sort out;
  * three rows applying the "Quanto a X" formula to a particle that is NOT は (two が, one に with no
    topic at all). That formula is the は gloss, so using it for が teaches the wrong particle in the one
    field whose entire job is to expose particles;
  * one missing crase, one missing reflexive ("consultar" vs "consultar-se com"), one quantifier
    ungrammatical with a count noun, one row carrying editorial parentheses, and one that differed from
    the natural pt by a single synonym and so did no structural work at all.

The other 285 were checked and left alone; 8 near-misses are recorded as deliberate no-change so a later
pass does not re-litigate them.

These sentences are already ingested, so the target is localized_text, not the staging JSON.
Anchors are byte-exact and the natural pt is never touched.

Usage: apply_ptliteral_round2.py [--apply]
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "derived" / "qa_queues" / "round2" / "pt_literal.json"
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = [r for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"] if r["verdict"] == "fix"]
    con = sqlite3.connect(DB)
    sid_of = {s: i for s, i in con.execute("SELECT slug,id FROM sentence")}
    applied, skipped = 0, []

    for r in rows:
        tid = str(r["id"]).strip()
        sid = sid_of.get(f"sent:tatoeba-{tid}")
        if not sid:
            skipped.append((tid, "sentence not in bank")); continue
        row = con.execute("SELECT value FROM localized_text WHERE entity_type='sentence' AND "
                          "entity_id=? AND field='translation_literal' AND locale='pt-BR'",
                          (sid,)).fetchone()
        if not row:
            skipped.append((tid, "no stored pt_literal")); continue
        stored, cur, fix = row[0] or "", r.get("current") or "", r.get("fix") or ""
        if not fix:
            skipped.append((tid, "empty fix")); continue
        if cur and cur not in stored:
            skipped.append((tid, "anchor not found")); continue
        new = stored.replace(cur, fix, 1) if cur else fix
        if args.apply:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type='sentence' AND "
                        "entity_id=? AND field='translation_literal' AND locale='pt-BR'", (new, sid))
        applied += 1

    if args.apply:
        con.commit()
    print(f"pt_literal round2 ({'APPLIED' if args.apply else 'dry-run'}): {applied}/{len(rows)}")
    for t, w in skipped:
        print(f"   skip {t}: {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
