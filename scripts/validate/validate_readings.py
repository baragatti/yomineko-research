#!/usr/bin/env python3
"""§3 readability gate for reading-practice boxes (design/reading_practice.md): a reading attached to
lesson L is valid ONLY if every kanji and every content vocab it uses is already in
L.cumulative_known_set (HARD gate, max_new=0) — proving "only what the learner can already fully read".
Plus hygiene: translation present (pt+en), tokens present, no em-dash.

Validates the EXPORTED JSON — corpus/readings/*.json against course/**/lesson-*.json — not the working
index. An audit (readings-gate-reads-db-not-export) found the old version read db/corpus.sqlite's
stored cumulative_known_set in retired headword space, so the shipped artifact was never the thing
being tested; the DB is regenerable state and can lag the export. `uses.vocab` and the exported
cumulative_known_set both speak `vocab:<jmdict_id>` slug space now, so the comparison is exact —
no headword collapsing, no row ids.

Exit 1 on any failure. Usage: validate_readings.py
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    reading_files = sorted((ROOT / "corpus" / "readings").glob("n*.json"))
    if not reading_files:
        print("validate_readings: no exported readings (nothing to check)")
        return 0

    # gating lesson -> its exported cumulative_known_set, from the courseware leaves
    known: dict = {}
    for lf in ROOT.glob("course/*/topic-*/lesson-*.json"):
        d = json.loads(lf.read_text(encoding="utf-8"))
        cks = d.get("cumulative_known_set") or {}
        known[d["id"]] = (
            {x.split(":", 1)[1] for x in cks.get("kanji") or []},   # kanji:<char> -> char
            set(cks.get("vocab") or []),                            # vocab:<jmdict_id> slugs
        )

    fails = total = 0
    EM = re.compile(r"—")
    # NB: no Latin-in-JP check here — readings come from the verified real bank where Latin loanwords
    # (OK, DVD, Tシャツ…) are legitimate; the romaji-garble check is only for GENERATED text.
    for rf in reading_files:
        for r in json.loads(rf.read_text(encoding="utf-8")):
            total += 1
            slug, lesson = r["slug"], r["gated_to_lesson"]
            probs = []
            if lesson not in known:
                probs.append(f"gated_to_lesson {lesson!r} is not an exported lesson")
                kk, vv = set(), set()
            else:
                kk, vv = known[lesson]
            u = r.get("uses") or {}
            bad_k = [k for k in u.get("kanji", []) if k not in kk]
            bad_v = [v for v in u.get("vocab", []) if v not in vv]
            if bad_k:
                probs.append(f"{len(bad_k)} out-of-known kanji ({' '.join(bad_k[:4])})")
            if bad_v:
                probs.append(f"{len(bad_v)} out-of-known vocab ({', '.join(bad_v[:4])})")
            tr = r.get("translation") or {}
            if not (tr.get("pt-BR") or "").strip():
                probs.append("missing pt translation")
            if not (tr.get("en") or "").strip():
                probs.append("missing en translation")
            if not r.get("tokens"):
                probs.append("no tokens")
            if EM.search((r.get("jp") or "") + (tr.get("pt-BR") or "")):
                probs.append("em-dash")
            if probs:
                fails += 1
                if fails <= 15:
                    print(f"  FAIL {slug} ({lesson}): {', '.join(probs)}")

    print(f"\nvalidate_readings: {total} readings, {fails} FAIL (exported JSON, slug space)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
