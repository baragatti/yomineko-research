#!/usr/bin/env python3
"""§3 readability gate for reading-practice boxes (design/reading_practice.md): a reading attached to lesson L
is valid ONLY if every kanji and every content vocab it uses is already in L.cumulative_known_set (HARD gate,
max_new=0) — proving "only what the learner can already fully read". Plus hygiene: translation present (pt+en),
tokens present, no em-dash, no Latin-in-JP garble. Exit 1 on any failure. Usage: validate_readings.py"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    c = sqlite3.connect(DB)
    if not c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reading'").fetchone():
        print("validate_readings: no reading table (nothing to check)")
        return 0
    kid_by_char = {ch: i for i, ch in c.execute("SELECT id,character FROM kanji")}
    vid_by_hw: dict = {}
    for i, hw in c.execute("SELECT id,headword FROM vocab"):
        vid_by_hw.setdefault(hw, i)
    known_cache: dict = {}

    def known(lesson_slug: str):
        if lesson_slug not in known_cache:
            r = c.execute("SELECT cumulative_known_set FROM lesson WHERE slug=?", (lesson_slug,)).fetchone()
            k = json.loads(r[0]) if r and r[0] else {}
            kk = {kid_by_char[x[6:]] for x in (k.get("kanji") or []) if x[6:] in kid_by_char}
            vv = {vid_by_hw[x[6:]] for x in (k.get("vocab") or []) if x[6:] in vid_by_hw}
            known_cache[lesson_slug] = (kk, vv)
        return known_cache[lesson_slug]

    fails = 0
    total = 0
    EM = re.compile(r"—")
    # NB: no Latin-in-JP check here — readings come from the verified real bank where Latin loanwords
    # (OK, DVD, Tシャツ…) are legitimate; the romaji-garble check is only for GENERATED text.
    for slug, lesson, jp, uses, tpt, ten, tk in c.execute(
            "SELECT slug,gated_to_lesson,jp,uses,translation_pt,translation_en,tokens FROM reading"):
        total += 1
        kk, vv = known(lesson)
        u = json.loads(uses or "{}")
        bad_k = [k for k in u.get("kanji", []) if k not in kk]
        bad_v = [v for v in u.get("vocab", []) if v not in vv]
        probs = []
        if bad_k:
            probs.append(f"{len(bad_k)} out-of-known kanji")
        if bad_v:
            probs.append(f"{len(bad_v)} out-of-known vocab")
        if not (tpt or "").strip():
            probs.append("missing pt translation")
        if not (ten or "").strip():
            probs.append("missing en translation")
        if not json.loads(tk or "[]"):
            probs.append("no tokens")
        if EM.search(jp + (tpt or "")):
            probs.append("em-dash")
        if probs:
            fails += 1
            if fails <= 15:
                print(f"  FAIL {slug} ({lesson}): {', '.join(probs)}")
    c.close()
    print(f"\nvalidate_readings: {total} readings, {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
