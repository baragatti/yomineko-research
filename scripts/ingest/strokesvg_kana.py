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
# the strokes group (centerlines), then every <path ... d="..."> inside it, in document (=stroke) order
STROKES_G_RE = re.compile(r'<g data-strokesvg="strokes".*?>(.*?)</g>', re.S)
DATTR_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')
CHAR_RE = re.compile(r'data-strokesvg="([^"]+)"')


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
            sg = STROKES_G_RE.search(svg)
            if not sg:
                continue
            strokes = DATTR_RE.findall(sg.group(1))
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
