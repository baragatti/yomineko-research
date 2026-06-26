#!/usr/bin/env python3
"""Ingest strokesvg (Klee One SIL OFL + MIT) KANA stroke-order into OUR schema. Each dist SVG has a
`<g data-strokesvg="strokes">` group of ordered per-stroke centerline <path d> (animatable via dash-offset).
We extract {char, viewbox, strokes:[d,…]} into a `kana_stroke` table → corpus/strokes/kana.json. Permissive,
attributed; kana-only (no kanji). Idempotent. Usage: strokesvg_kana.py"""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
DIST = ROOT / "research" / "datasets" / "strokesvg" / "dist"
VB_RE = re.compile(r'viewBox="([^"]+)"')
DATTR_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')
CHAR_RE = re.compile(r'<svg[^>]*data-strokesvg="([^"]+)"')


def strokes_of(svg: str) -> list[list[str]]:
    """Return the sub-path `d`(s) per STROKE (list-of-lists). strokesvg's `<g data-strokesvg="strokes">` has one
    direct child per stroke: a `<path>` (single-path stroke -> [d]) OR a `<g style="--i:N">…</g>` wrapping a
    multi-path stroke (e.g. the curl of あ -> [d1, d2]). Sub-paths are kept SEPARATE (not concatenated — joining
    would break their relative-moveto origins); the viewer draws a stroke's sub-paths together as one stroke."""
    s = svg.find('<g data-strokesvg="strokes"')
    if s < 0:
        return []
    inner_start = svg.find(">", s) + 1
    # balance-match the strokes group's own </g> (sub-strokes may nest one <g> level)
    depth, pos, inner_end = 1, inner_start, None
    while pos < len(svg) and depth:
        ng, cg = svg.find("<g", pos), svg.find("</g>", pos)
        if cg < 0:
            break
        if ng != -1 and ng < cg:
            depth += 1; pos = ng + 2
        else:
            depth -= 1
            if depth == 0:
                inner_end = cg
            pos = cg + 4
    inner = svg[inner_start:inner_end if inner_end is not None else len(svg)]
    # walk DIRECT children in order: a top-level <path/> = 1 stroke; a <g>…</g> = 1 multi-path stroke
    strokes, p = [], 0
    while True:
        g, pa = inner.find("<g", p), inner.find("<path", p)
        if g == -1 and pa == -1:
            break
        if pa != -1 and (g == -1 or pa < g):
            end = inner.find("/>", pa) + 2
            d = DATTR_RE.search(inner[pa:end])
            if d:
                strokes.append([d.group(1).strip()])
            p = end
        else:
            gend = inner.find("</g>", g) + 4
            ds = DATTR_RE.findall(inner[g:gend])
            if ds:
                strokes.append([x.strip() for x in ds])
            p = gend
    return strokes


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS kana_stroke (
        char TEXT PRIMARY KEY, kind TEXT, viewbox TEXT, strokes TEXT, source TEXT, license TEXT, layer TEXT DEFAULT 'A')""")
    n = 0
    for kind in ("hiragana", "katakana"):
        d = DIST / kind
        if not d.exists():
            continue
        for svg_path in sorted(d.glob("*.svg")):
            svg = svg_path.read_text(encoding="utf-8")
            cm = CHAR_RE.search(svg)
            ch = cm.group(1) if cm else svg_path.stem
            vb = VB_RE.search(svg)
            strokes = strokes_of(svg)
            if not strokes:
                continue
            con.execute(
                "INSERT OR REPLACE INTO kana_stroke (char, kind, viewbox, strokes, source, license, layer) "
                "VALUES (?,?,?,?,?,?,'A')",
                (ch, kind, vb.group(1) if vb else "0 0 1024 1024",
                 json.dumps(strokes, ensure_ascii=False), "strokesvg", "OFL-1.1+MIT"))
            n += 1
    con.commit()
    tot = con.execute("SELECT COUNT(*) FROM kana_stroke").fetchone()[0]
    by = dict(con.execute("SELECT kind, COUNT(*) FROM kana_stroke GROUP BY kind").fetchall())
    con.close()
    print(f"strokesvg kana: ingested {n}; table now {tot} ({by})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
