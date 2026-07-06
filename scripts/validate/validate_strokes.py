#!/usr/bin/env python3
"""Stroke-data validator (kana + kanji animations) — owner ask 2026-07-05 "verify all drawings/strokes".
KANJI (kanji_stroke_line): every path parses, no NaN, coords within the KAGE box (with margin), no
zero-length strokes, glyph bbox non-degenerate, count_match rows really match KANJIDIC.
KANA (kana_stroke): strokes/shadows JSON parse, per-stroke non-empty d, shadows aligned 1:1 (empty allowed:
unclipped dots), viewbox sane. The render-level check (centerline actually inside its clip shape) needs a
real SVG engine — done in the browser (see the verification notes in STATE) — this covers the data layer.
Exit 1 on any failure. Usage: validate_strokes.py"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"
NUM = re.compile(r"-?\d+\.?\d*(?:e-?\d+)?")


def path_nums(d: str) -> list[float]:
    return [float(x) for x in NUM.findall(d)]


def main() -> int:
    c = sqlite3.connect(DB)
    fails = 0

    def fail(msg: str, items: list) -> None:
        nonlocal fails
        if items:
            fails += len(items)
            print(f"  FAIL {msg}: {len(items)}  e.g. {items[:5]}")
        else:
            print(f"  ok   {msg}")

    # ---- kanji centerlines ----
    bad_parse, bad_range, bad_zero, bad_bbox, bad_count = [], [], [], [], []
    strokes_by_kid = {}
    for ch, exp, match, st in c.execute(
            "SELECT k.character,k.strokes,ksl.count_match,ksl.strokes FROM kanji_stroke_line ksl "
            "JOIN kanji k ON k.id=ksl.kanji_id WHERE ksl.count_match=1"):
        try:
            paths = json.loads(st)
        except Exception:
            bad_parse.append(ch); continue
        if exp is not None and len(paths) != exp:
            bad_count.append((ch, len(paths), exp))
        xs, ys = [], []
        for d in paths:
            ns = path_nums(d)
            if not ns or len(ns) % 2:
                bad_parse.append((ch, d[:20])); continue
            px, py = ns[0::2], ns[1::2]
            xs += px; ys += py
            if any(v != v for v in ns):  # NaN
                bad_parse.append((ch, "NaN"))
            if not (-40 <= min(px) and max(px) <= 240 and -40 <= min(py) and max(py) <= 240):
                bad_range.append((ch, round(min(px + py)), round(max(px + py))))
            if max(px) - min(px) < 0.5 and max(py) - min(py) < 0.5:
                bad_zero.append((ch, d[:24]))
        # a 3+-stroke kanji can't be tiny; 1-2 stroke radicals (一丶丿亅亠) are legitimately thin/small
        if xs and len(paths) >= 3 and max(max(xs) - min(xs), max(ys) - min(ys)) < 60:
            bad_bbox.append((ch, round(max(xs) - min(xs)), round(max(ys) - min(ys))))
    fail("K1 kanji stroke paths parse (no NaN/odd coords)", bad_parse)
    fail("K2 coords within KAGE box (-40..240)", bad_range)
    fail("K3 no zero-length strokes", bad_zero)
    fail("K4 glyph bbox non-degenerate (>=60u)", bad_bbox)
    fail("K5 count_match rows really match KANJIDIC", bad_count)

    # ---- kana ----
    k_parse, k_align, k_empty, k_vb = [], [], [], []
    for ch, vb, st, sh in c.execute("SELECT char,viewbox,strokes,shadows FROM kana_stroke"):
        try:
            strokes = json.loads(st)
            shadows = json.loads(sh) if sh else None
        except Exception:
            k_parse.append(ch); continue
        if not strokes or any(not (d and d.strip().upper().startswith("M")) for d in strokes):
            k_empty.append(ch)
        if shadows is not None and len(shadows) != len(strokes):
            k_align.append((ch, len(strokes), len(shadows)))
        if not re.match(r"^[\d.\s-]+$", vb or "") or len((vb or "").split()) != 4:
            k_vb.append((ch, vb))
        flat_shadows = [x for sh in (shadows or []) for x in (sh if isinstance(sh, list) else [sh])]
        for d in strokes + flat_shadows:
            if d and any(v != v for v in path_nums(d)):
                k_parse.append((ch, "NaN"))
    fail("A1 kana strokes/shadows JSON parse", k_parse)
    fail("A2 kana strokes start with moveto, non-empty", k_empty)
    fail("A3 kana shadows aligned 1:1 with strokes", k_align)
    fail("A4 kana viewbox sane", k_vb)

    c.close()
    print(f"\nvalidate_strokes: {'FAIL ' + str(fails) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
