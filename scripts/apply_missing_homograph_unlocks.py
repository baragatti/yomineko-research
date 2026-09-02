#!/usr/bin/env python3
"""Unlock the six vocabulary records their lessons already teach in prose.

The headword-collapse era hid a class of curriculum hole: when a homograph pair existed, only one
sibling could ever be addressed, so six N4 lessons TEACH a word in their body — a heading, a section,
inline chips — that no lesson ever unlocks. The learner sees the word and can never be scheduled to
review it (it is outside every cumulative_known_set and every SRS deck). The slug migration made the
holes visible (audit finding body-refs-now-outside-own-cks; all six confirmed against the body text):

    les:n4-forma-simples-04     先  (さっき, vocab:1005180)  — section "さっき: o passado bem recente"
    les:n4-oracoes-relativas-01 彼  (かれ,   vocab:1483070)
    les:n4-condicionais-01      開く (ひらく, vocab:1202440)  — conjugated 開いたら/ひらいたら in the body
    les:n4-condicionais-07      家  (け,    vocab:1191750)
    les:n4-dar-receber-03       居る (おる,  vocab:1577985)  — glossed "estar (humilde)"
    les:n4-experiencia-04       米  (こめ,  vocab:1508750)  — section "O kanji 米 … lê-se こめ"

The unlock ref is written in the authoring layer's own vocabulary — the HEADWORD — in both layers
(research/derived/lessons/<slug>.json and db lesson_unlocks). At export the identity resolver settles
it: each of these lessons is N4 and exactly one candidate record is N4, so the level rule picks the
intended record deterministically, with no review row. The expected slug is asserted below anyway; if
resolution ever stops matching, this script's own verification fails rather than trusting the rule.

Idempotent. Run export_course.py afterwards. Usage: apply_missing_homograph_unlocks.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
# W01: the lesson authoring layer is both read and rewritten by the rebuild chain, so it
# follows --out-root / $YOMINEKO_OUT_ROOT: a redirected rebuild works on its own copy and
# never edits the repo's tracked lessons. Unset, this is the same path it always was.
SRC = out_root(ROOT) / "research" / "derived" / "lessons"

# (lesson slug, headword ref, expected resolved slug, expected level)
ADDS = [
    ("les:n4-forma-simples-04", "vocab:先", "vocab:1005180", "n4"),
    ("les:n4-oracoes-relativas-01", "vocab:彼", "vocab:1483070", "n4"),
    ("les:n4-condicionais-01", "vocab:開く", "vocab:1202440", "n4"),
    ("les:n4-condicionais-07", "vocab:家", "vocab:1191750", "n4"),
    ("les:n4-dar-receber-03", "vocab:居る", "vocab:1577985", "n4"),
    ("les:n4-experiencia-04", "vocab:米", "vocab:1508750", "n4"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed, skipped = 0, []
    for lslug, ref, expect_slug, expect_level in ADDS:
        hw = ref.split(":", 1)[1]
        # Pre-verify the level rule really is unambiguous for this pair before writing anything.
        cands = con.execute("SELECT slug, level FROM vocab WHERE headword=?", (hw,)).fetchall()
        at_level = [c for c in cands if c[1] == expect_level]
        if len(at_level) != 1 or at_level[0][0] != expect_slug:
            skipped.append(f"{lslug}: {ref} does not resolve uniquely to {expect_slug} at "
                           f"{expect_level} (candidates: {cands}) — not touching it")
            continue

        lid_row = con.execute("SELECT id FROM lesson WHERE slug=?", (lslug,)).fetchone()
        if not lid_row:
            skipped.append(f"{lslug}: no such lesson")
            continue
        lid = lid_row[0]

        # DB layer
        have = con.execute("SELECT 1 FROM lesson_unlocks WHERE lesson_id=? AND unlock_type='vocab' "
                           "AND ref=?", (lid, ref)).fetchone()
        if not have:
            print(f"  {lslug}: +unlock {ref} -> {expect_slug} (db)")
            if not args.check:
                con.execute("INSERT OR IGNORE INTO lesson_unlocks (lesson_id, unlock_type, ref) "
                            "VALUES (?, 'vocab', ?)", (lid, ref))
            changed += 1

        # Source layer
        f = SRC / f"{lslug.split(':', 1)[1]}.json"
        if not f.exists():
            skipped.append(f"{lslug}: authoring source {f.name} missing")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not any(u.get("type") == "vocab" and u.get("ref") == ref for u in d.get("unlocks", [])):
            print(f"  {lslug}: +unlock {ref} (source)")
            if not args.check:
                d.setdefault("unlocks", []).append({"type": "vocab", "ref": ref})
                f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            changed += 1

    if not args.check:
        con.commit()
    con.close()
    verb = "would add" if args.check else "added"
    print(f"\n{verb} {changed} unlock entries across both layers")
    for s in skipped:
        print(f"  ! {s}")
    return 2 if skipped else (1 if (args.check and changed) else 0)


if __name__ == "__main__":
    sys.exit(main())
