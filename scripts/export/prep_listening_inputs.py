#!/usr/bin/env python3
"""Deterministic prep for the listening (聴解) authoring workflow (design/listening.md).
Emits research/derived/reauthor/exam_authored/input_listen_{level}_{sub}.json:
- reply: REAL bank sentences (ai=0, utterance-like, 6-22 chars) used verbatim as prompts — selection over
  generation; deduped across levels (lower level wins).
- task/point/say/gist: per-item seed words stride-sampled from the level's vocab registry (3 distant words
  per item; scenario must use >=1) — keeps authored dialogues in-level, diverse, traceable.
No RNG — stable re-runs. Usage: prep_listening_inputs.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
ORD = {"pre-n5": -1, "n5": 0, "n4": 1, "n3": 2}
BATCHES = [  # (level, sub, count) = 3x the per-paper counts in design/listening.md
    ("n5", "task", 21), ("n5", "point", 18), ("n5", "say", 15), ("n5", "reply", 18),
    ("n4", "task", 24), ("n4", "point", 21), ("n4", "say", 15), ("n4", "reply", 24),
    ("n3", "task", 18), ("n3", "point", 18), ("n3", "gist", 9), ("n3", "say", 12), ("n3", "reply", 27),
]
UTTER_ENDS = ("か。", "ね。", "よ。", "ください。", "ましょう。", "？")


def main() -> int:
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- reply prompts: real, short, utterance-like; dedupe lower-level-first ----
    used: set = set()
    prompts: dict = {}
    for lvl in ("n5", "n4", "n3"):
        cands = [(len(jp), slug, jp) for slug, jp, slvl, ai in con.execute(
            "SELECT slug,jp,level,COALESCE(ai_generated,0) FROM sentence")
            if ai == 0 and slvl in ORD and ORD[slvl] <= ORD[lvl] and 6 <= len(jp) <= 22
            and jp.endswith(UTTER_ENDS) and "「" not in jp and slug not in used]
        cands.sort()
        need = next(c for l2, s, c in BATCHES if l2 == lvl and s == "reply")
        pick = cands[:need]
        used.update(s for _, s, _ in pick)
        prompts[lvl] = [{"slug": s, "jp": jp} for _, s, jp in pick]

    # ---- seed words per level: prefer content lexemes, stride-triples of distant words ----
    lexes = {r[0] for r in con.execute("SELECT DISTINCT lexeme_type FROM vocab")}
    content = {"noun", "verb"} & lexes or lexes
    seeds_by_lvl = {}
    for lvl in ("n5", "n4", "n3"):
        ws = sorted(hw for hw, lex in con.execute(
            "SELECT headword,lexeme_type FROM vocab WHERE level=? AND kana!=''", (lvl,)) if lex in content)
        seeds_by_lvl[lvl] = ws
    cursor = {lvl: 0 for lvl in seeds_by_lvl}

    for lvl, sub, count in BATCHES:
        fp = OUT / f"input_listen_{lvl}_{sub}.json"
        if sub == "reply":
            data = {"sub": sub, "level": lvl, "count": count, "items": prompts[lvl]}
        else:
            ws = seeds_by_lvl[lvl]
            third = len(ws) // 3
            items = []
            for n in range(1, count + 1):
                i = cursor[lvl]
                items.append({"n": n, "seeds": [ws[i % third], ws[(i + third) % len(ws)],
                                                ws[(i + 2 * third) % len(ws)]]})
                cursor[lvl] += 1
            data = {"sub": sub, "level": lvl, "count": count, "items": items}
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{fp.name}: {count} items" + (f" (real prompts: {len(data['items'])})" if sub == "reply" else ""))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
