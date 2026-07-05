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


def _abs_lead(d: str) -> str:
    """A standalone path's leading relative `m` is treated as ABSOLUTE by the SVG spec. When we concatenate
    several path elements into ONE multi-subpath d, that context is lost — uppercase the leading moveto so the
    coordinates stay absolute."""
    d = d.strip()
    return ("M" + d[1:]) if d.startswith("m") else d


def strokes_of(svg: str) -> tuple[list[str], list[str]]:
    """Return (centerlines, shadows): one entry per STROKE, in order. strokesvg's real model: a `shadows`
    group holds the per-stroke OUTLINE shapes (the true Klee One calligraphy) and each centerline in the
    `strokes` group is CLIPPED to its shadow — centerlines intentionally overshoot (construction geometry),
    the clip crops them (e.g. き/ぎ stroke 4). We keep ALL sub-paths per stroke (joined, leading m -> M) plus
    the joined shadow outlines, and the viewer reproduces the clipped rendering."""
    # shadow outlines by id (the strokes' clip-paths reference them via <clipPath><use href="#id">)
    shadow_by_id: dict[str, str] = {}
    m = re.search(r'<g[^>]*data-strokesvg="shadows"[^>]*>(.*?)</g>', svg, re.S)
    if m:
        for pid, d in re.findall(r'<path[^>]*\bid="([^"]+)"[^>]*\bd="([^"]+)"', m.group(1)):
            shadow_by_id[pid] = d.strip()
        for d, pid in re.findall(r'<path[^>]*\bd="([^"]+)"[^>]*\bid="([^"]+)"', m.group(1)):
            shadow_by_id.setdefault(pid, d.strip())
    clip_target = dict(re.findall(r'<clipPath[^>]*id="([^"]+)"[^>]*>\s*<use[^>]*href="#([^"]+)"', svg))

    s = svg.find('<g data-strokesvg="strokes"')
    if s < 0:
        return [], []
    inner_start = svg.find(">", s) + 1
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

    def shadow_of(chunk: str) -> str:
        """Joined shadow outlines for every clip-path reference inside this stroke's markup."""
        outs = []
        for cid in re.findall(r'clip-path="url\(#([^)]+)\)"', chunk):
            d = shadow_by_id.get(clip_target.get(cid, ""), "")
            if d:
                outs.append(d)
        return " ".join(outs)

    strokes: list[str] = []
    shadows: list[str] = []
    p = 0
    while True:
        g, pa = inner.find("<g", p), inner.find("<path", p)
        if g == -1 and pa == -1:
            break
        if pa != -1 and (g == -1 or pa < g):
            end = inner.find("/>", pa) + 2
            chunk = inner[pa:end]
            d = DATTR_RE.search(chunk)
            if d:
                strokes.append(_abs_lead(d.group(1)))
                shadows.append(shadow_of(chunk))
            p = end
        else:
            gend = inner.find("</g>", g) + 4
            chunk = inner[g:gend]
            ds = DATTR_RE.findall(chunk)
            if ds:
                strokes.append(" ".join(_abs_lead(x) for x in ds))  # all sub-paths; clip crops construction
                shadows.append(shadow_of(chunk))
            p = gend
    return strokes, shadows


def main() -> int:
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS kana_stroke (
        char TEXT PRIMARY KEY, kind TEXT, viewbox TEXT, strokes TEXT, source TEXT, license TEXT, layer TEXT DEFAULT 'A')""")
    if "shadows" not in [r[1] for r in con.execute("PRAGMA table_info(kana_stroke)")]:
        con.execute("ALTER TABLE kana_stroke ADD COLUMN shadows TEXT")
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
            strokes, shadows = strokes_of(svg)
            if not strokes:
                continue
            con.execute(
                "INSERT OR REPLACE INTO kana_stroke (char, kind, viewbox, strokes, shadows, source, license, layer) "
                "VALUES (?,?,?,?,?,?,?,'A')",
                (ch, kind, vb.group(1) if vb else "0 0 1024 1024",
                 json.dumps(strokes, ensure_ascii=False),
                 json.dumps(shadows, ensure_ascii=False) if any(shadows) else None,
                 "strokesvg", "OFL-1.1+MIT"))
            n += 1
    # sokuon っ/ッ: strokesvg ships no file for them; same glyph as つ/ツ (rendered smaller) -> derive.
    for src, dst in (("つ", "っ"), ("ツ", "ッ")):
        r = con.execute("SELECT kind,viewbox,strokes,shadows,license FROM kana_stroke WHERE char=?", (src,)).fetchone()
        if r:
            con.execute("INSERT OR REPLACE INTO kana_stroke (char,kind,viewbox,strokes,shadows,source,license) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (dst, r[0], r[1], r[2], r[3], f"strokesvg (derived: same glyph as {src})", r[4]))
    con.commit()
    tot = con.execute("SELECT COUNT(*) FROM kana_stroke").fetchone()[0]
    by = dict(con.execute("SELECT kind, COUNT(*) FROM kana_stroke GROUP BY kind").fetchall())
    con.close()
    print(f"strokesvg kana: ingested {n}; table now {tot} ({by})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
