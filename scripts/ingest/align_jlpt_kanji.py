#!/usr/bin/env python3
"""JLPT exam-alignment — KANJI level re-tag (design/jlpt_alignment_plan.md §3, owner-approved 2026-07-05).

Anchor-priority rule: a kanji's level is N5 if it is in the old-official-derived N5 anchor list (103, from
nihongoichiban's old-4kyuu table + 二 recovered from a parse edge), else N4 if in the N4 anchor (177 new, from
Wikibooks JLPT Guide N4), else its current level — except kanji currently tagged n5/n4 that are in NO anchor,
which fall to n3 (they are beyond the exam's N5/N4 sets). Level membership is a non-copyrightable consensus
FACT (spec §1.5); sources recorded in level_sources with an `anchor` marker + MANIFEST.

Also recomputes sentence.level (= max level of linked kanji/vocab) so §7.6 stays consistent.
Idempotent. Usage: align_jlpt_kanji.py [--dry-run]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
ANCHOR = ROOT / "research" / "datasets" / "jlpt_anchor" / "anchor_kanji.json"
ORDER = {"n5": 0, "n4": 1, "n3": 2, "n2": 3, "n1": 4}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    A = json.loads(ANCHOR.read_text(encoding="utf-8"))
    A5, A4 = set(A["n5"]) | {"二"}, set(A["n4"]) - {"二"}
    con = sqlite3.connect(DB)
    moves = []
    for kid, ch, lvl, lsrc in con.execute("SELECT id,character,level,level_sources FROM kanji"):
        tgt = "n5" if ch in A5 else ("n4" if ch in A4 else ("n3" if lvl in ("n5", "n4") else lvl))
        if tgt != lvl:
            moves.append((ch, lvl, tgt))
            src = json.loads(lsrc) if lsrc else {}
            if not isinstance(src, dict):
                src = {"lists": src}
            src["anchor"] = f"jlpt_anchor:{tgt}" if tgt in ("n5", "n4") else "jlpt_anchor:not-in-n5n4"
            if not args.dry_run:
                con.execute("UPDATE kanji SET level=?, level_sources=? WHERE id=?",
                            (tgt, json.dumps(src, ensure_ascii=False), kid))
    # sentence.level = max(level of linked kanji, level of linked vocab) — keeps §7.6 green after moves
    n_sent = 0
    if not args.dry_run:
        klv = dict(con.execute("SELECT id,level FROM kanji"))
        vlv = dict(con.execute("SELECT id,level FROM vocab"))
        sk: dict = {}
        for sid, kid in con.execute("SELECT sentence_id,kanji_id FROM sentence_kanji"):
            sk.setdefault(sid, []).append(klv.get(kid))
        for sid, vid in con.execute("SELECT sentence_id,vocab_id FROM sentence_vocab"):
            sk.setdefault(sid, []).append(vlv.get(vid))
        for sid, lvl in con.execute("SELECT id,level FROM sentence"):
            lv = [x for x in sk.get(sid, []) if x in ORDER]
            new = max(lv, key=lambda x: ORDER[x]) if lv else lvl
            if new != lvl:
                con.execute("UPDATE sentence SET level=? WHERE id=?", (new, sid))
                n_sent += 1
        con.commit()
    from collections import Counter
    mc = Counter(f"{a}->{b}" for _, a, b in moves)
    print(f"kanji re-tag ({'dry-run' if args.dry_run else 'APPLIED'}): {len(moves)} moves {dict(mc)}; "
          f"sentence.level updated: {n_sent}")
    cnt = dict(con.execute("SELECT level, COUNT(*) FROM kanji GROUP BY level"))
    print("levels now:", {k: cnt.get(k, 0) for k in ["n5", "n4", "n3", "n2", "n1"]})
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
