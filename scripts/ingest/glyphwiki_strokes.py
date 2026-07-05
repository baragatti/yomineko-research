#!/usr/bin/env python3
"""Per-stroke kanji CENTERLINES from GlyphWiki KAGE data (permissive: GlyphWiki data is free for any use incl.
commercial, no ShareAlike — see research/datasets/glyphwiki/MANIFEST.md). This is what the pen+ball stroke
ANIMATION needs; Kanji Alive (kanji_stroke) only has cumulative filled outlines, which stay as the static/ghost
fallback. Covers ALL kanji in the registry (incl. the 898 N1 tail Kanji Alive lacks) — resolves backlog #6+#11.

KAGE primer: a glyph = '$'-separated lines of 11 ':'-separated numbers
  type:startShape:endShape:x1:y1:x2:y2:x3:y3:x4:y4
  1 line, 2 quad bezier, 3/4 bend (polyline), 6 cubic bezier, 7 line+quad — each = ONE pen stroke.
  99 = reference: place glyph named in field 8 into the box (x1,y1)-(x2,y2) (recursive; canvas is 0..200).
Shape flags (serifs/hooks/stops) are ornamental -> ignored for centerlines. Stroke order = line order.

Per kanji we pick u<hex>-j / u<hex>-jv / u<hex> (Japanese form first), expand references, emit one SVG path per
stroke, and cross-check the stroke COUNT against KANJIDIC (kanji.strokes): only count-matching kanji are marked
usable for animation (the rest keep the outline fallback). Idempotent (rebuilds the table).
Usage: glyphwiki_strokes.py [--dump research/datasets/glyphwiki/dump_newest_only.txt]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
DUMP = ROOT / "research" / "datasets" / "glyphwiki" / "dump_newest_only.txt"

F = lambda v: float(v)


def seg_of(n: list[float]) -> tuple[tuple[float, float], str, tuple[float, float]] | None:
    """One KAGE line -> (start_point, path_tail_without_M, end_point)."""
    t = int(n[0])
    x1, y1, x2, y2, x3, y3, x4, y4 = n[3:11]
    if t == 1:
        return (x1, y1), f"L{x2} {y2}", (x2, y2)
    if t == 2:
        return (x1, y1), f"Q{x2} {y2} {x3} {y3}", (x3, y3)
    if t in (3, 4):  # bend: two legs (centerline approximation of the rounded corner)
        return (x1, y1), f"L{x2} {y2}L{x3} {y3}", (x3, y3)
    if t == 6:
        return (x1, y1), f"C{x2} {y2} {x3} {y3} {x4} {y4}", (x4, y4)
    if t == 7:  # vertical then sweep
        return (x1, y1), f"L{x2} {y2}Q{x3} {y3} {x4} {y4}", (x4, y4)
    return None  # 0/9/other: not a pen stroke


def lines_to_strokes(lines: list[list[float]]) -> list[str]:
    """KAGE lines -> pen strokes. A line whose START point equals the previous line's END point AND whose
    start-flag (field 1) != 0 is the continuation of the SAME pen stroke (corner join, e.g. the ㇕ of 口 =
    horizontal + vertical encoded as two lines). KAGE lines follow stroke order, so joins are adjacent.
    Derived empirically from 口/山/日/木 and gated by the KANJIDIC stroke-count cross-check."""
    strokes: list[str] = []
    cur = ""
    cur_end: tuple[float, float] | None = None
    prev_a3 = 0
    prev_t = 0
    for n in lines:
        s = seg_of(n)
        if not s:
            continue
        (sx, sy), tail, end = s
        near = cur_end is not None and abs(cur_end[0] - sx) + abs(cur_end[1] - sy) <= 40
        corner = cur and cur_end == (sx, sy) and int(n[1]) != 0  # ㇕/∟/㇉ corner continuation
        # curve fold (the ㇜ of 厶): curve ending a3=7 flowing into a curve starting a2=0 right there.
        # a3=7 elsewhere is a HOOK end shape, so keep this narrow (both type 2) or it over-merges.
        fold = cur and prev_a3 == 7 and near and int(n[0]) == 2 and int(n[1]) == 0 and prev_t == 2
        if corner or fold:
            cur += (tail if cur_end == (sx, sy) else f"L{sx} {sy}" + tail)
        else:
            if cur:
                strokes.append(cur)
            cur = f"M{sx} {sy}" + tail
        cur_end = end
        prev_a3 = int(n[2]) if len(n) > 2 else 0
        prev_t = int(n[0])
    if cur:
        strokes.append(cur)
    return strokes


def expand(name: str, glyphs: dict, depth: int = 0) -> list[list[float]]:
    """KAGE lines for glyph `name` with 99-references resolved into absolute 0..200 coords."""
    if depth > 8 or name not in glyphs:
        return []
    out: list[list[float]] = []
    for line in glyphs[name].split("$"):
        p = line.split(":")
        if not p or not p[0].strip():
            continue
        if p[0] == "99":
            ref = p[7].split("@")[0]  # strip version pin
            try:
                bx1, by1, bx2, by2 = F(p[3]), F(p[4]), F(p[5]), F(p[6])
            except (ValueError, IndexError):
                continue
            for sub in expand(ref, glyphs, depth + 1):
                q = sub[:]
                for i in range(3, 11, 2):
                    q[i] = bx1 + q[i] * (bx2 - bx1) / 200.0
                    q[i + 1] = by1 + q[i + 1] * (by2 - by1) / 200.0
                out.append(q)
        else:
            try:
                nums = [F(x) for x in p[:11]] + [0.0] * max(0, 11 - len(p))
            except ValueError:
                continue
            if int(nums[0]) in (1, 2, 3, 4, 6, 7):
                out.append(nums[:11])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=str(DUMP))
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    kanji = {ch: (kid, strokes) for kid, ch, strokes in con.execute("SELECT id,character,strokes FROM kanji")}
    # names we might need: exact glyph names are unknowable upfront (references) -> load the WHOLE dump map.
    glyphs: dict[str, str] = {}
    with open(args.dump, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split("|")
            if len(parts) >= 3:
                glyphs[parts[0].strip()] = parts[2].strip()
    print(f"dump glyphs: {len(glyphs):,}")

    con.execute("""CREATE TABLE IF NOT EXISTS kanji_stroke_line (
        kanji_id INTEGER PRIMARY KEY, glyph TEXT, strokes TEXT, n_strokes INT, count_match INT,
        source TEXT DEFAULT 'glyphwiki', license TEXT DEFAULT 'GlyphWiki-free')""")
    con.execute("DELETE FROM kanji_stroke_line")
    ok = miss = badcount = 0
    for ch, (kid, expected) in kanji.items():
        cp = ord(ch)
        name = next((n for n in (f"u{cp:04x}-j", f"u{cp:04x}-jv", f"u{cp:04x}") if n in glyphs), None)
        if not name:
            miss += 1
            continue
        lines = expand(name, glyphs)
        paths = lines_to_strokes(lines)
        if not paths:
            miss += 1
            continue
        match = 1 if (expected is None or len(paths) == expected) else 0
        ok += match
        badcount += 1 - match
        con.execute("INSERT OR REPLACE INTO kanji_stroke_line (kanji_id,glyph,strokes,n_strokes,count_match) "
                    "VALUES (?,?,?,?,?)", (kid, name, json.dumps(paths), len(paths), match))
    con.commit()
    print(f"kanji: {len(kanji)}  usable(count-match): {ok}  count-mismatch: {badcount}  no-glyph: {miss}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
