#!/usr/bin/env python3
"""JLPT exam-coverage gate (design/jlpt_alignment_plan.md §5): for each level, the course must TEACH (via
lesson unlocks, cumulatively) every kanji in that level's exam-anchor set, and the tag counts must sit in the
expected bands. Exit 1 on any failure. Usage: audit_jlpt_coverage.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
ANCHOR = ROOT / "research" / "datasets" / "jlpt_anchor" / "anchor_kanji.json"
BANDS = {"n5": (95, 115), "n4": (160, 200)}  # tag-count sanity bands


def taught(con, prefixes) -> set:
    q = " OR ".join("l.slug LIKE ?" for _ in prefixes)
    return {r[0].split(":", 1)[1] for r in con.execute(
        f"SELECT u.ref FROM lesson_unlocks u JOIN lesson l ON l.id=u.lesson_id "
        f"WHERE u.unlock_type='kanji' AND ({q})", tuple(f"les:{p}-%" for p in prefixes))}


def main() -> int:
    if not ANCHOR.exists():
        print("audit_jlpt_coverage: no anchor lists (skip)")
        return 0
    A = json.loads(ANCHOR.read_text(encoding="utf-8"))
    A5, A4 = set(A["n5"]) | {"二"}, set(A["n4"]) - {"二"}
    con = sqlite3.connect(DB)
    fails = 0
    t5 = taught(con, ("pre-n5", "n5"))
    t4 = t5 | taught(con, ("n4",))
    for name, anchor, tset in (("N5", A5, t5), ("N4(cum)", A5 | A4, t4)):
        miss = anchor - tset
        if miss:
            fails += 1
            print(f"  FAIL {name}: {len(miss)} anchor kanji NOT taught: {sorted(miss)[:12]}")
        else:
            print(f"  ok   {name}: all {len(anchor)} anchor kanji taught (course teaches {len(tset)})")
    for lvl, (lo, hi) in BANDS.items():
        n = con.execute("SELECT COUNT(*) FROM kanji WHERE level=?", (lvl,)).fetchone()[0]
        if not (lo <= n <= hi):
            fails += 1
            print(f"  FAIL {lvl} tag count {n} outside band [{lo},{hi}]")
        else:
            print(f"  ok   {lvl} tag count {n} in band [{lo},{hi}]")

    # VOCAB: cumulative course-taught must cover every tagged word; cumulative counts within bands of the
    # OLD-OFFICIAL anchors (4kyuu=728, 3kyuu=1409; N3 = community consensus range). Our tags already merge
    # every legitimate list inclusively (min-level rule), so bands — not padding — are the correct check.
    VBANDS = {"n5": (650, 830), "n4": (1250, 1560), "n3": (2600, 3800)}
    def vtaught(prefixes):
        q = " OR ".join("l.slug LIKE ?" for _ in prefixes)
        return {r[0].split(":", 1)[1] for r in con.execute(
            f"SELECT u.ref FROM lesson_unlocks u JOIN lesson l ON l.id=u.lesson_id "
            f"WHERE u.unlock_type='vocab' AND ({q})", tuple(f"les:{p}-%" for p in prefixes))}
    cumsets = {"n5": ("n5",), "n4": ("n5", "n4"), "n3": ("n5", "n4", "n3")}
    prefixes = {"n5": ("pre-n5", "n5"), "n4": ("pre-n5", "n5", "n4"), "n3": ("pre-n5", "n5", "n4", "n3")}
    for lvl, (lo, hi) in VBANDS.items():
        tagged = {r[0] for r in con.execute(
            f"SELECT headword FROM vocab WHERE level IN ({','.join('?'*len(cumsets[lvl]))})", cumsets[lvl])}
        ts = vtaught(prefixes[lvl])
        miss = tagged - ts
        if miss:
            fails += 1
            print(f"  FAIL vocab {lvl}: {len(miss)} tagged words not taught: {sorted(miss)[:8]}")
        elif not (lo <= len(tagged) <= hi):
            fails += 1
            print(f"  FAIL vocab {lvl} cum count {len(tagged)} outside band [{lo},{hi}]")
        else:
            print(f"  ok   vocab {lvl}: cum {len(tagged)} in band [{lo},{hi}], all taught")
    con.close()
    print(f"\naudit_jlpt_coverage: {'FAIL ' + str(fails) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
