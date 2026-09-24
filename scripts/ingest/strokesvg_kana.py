#!/usr/bin/env python3
"""Ingest strokesvg (Klee One SIL OFL + MIT) KANA stroke-order into OUR schema. Each dist SVG has a
`<g data-strokesvg="strokes">` group of ordered per-stroke centerline <path d> (animatable via dash-offset).
We extract {char, viewbox, strokes:[d,…]} into a `kana_stroke` table → corpus/strokes/kana.json. Permissive,
attributed; kana-only (no kanji). Idempotent. Usage: strokesvg_kana.py
Derived rows (layer 'B'): っ/ッ (same glyph as つ/ツ) and, P3-yoon, the 66 yoon composites, re-derived from
the parsed rows and exact-matched against research/derived/repairs/yoon_strokes.json before any write."""
from __future__ import annotations
import json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
DIST = ROOT / "research" / "datasets" / "strokesvg" / "dist"
VB_RE = re.compile(r'viewBox="([^"]+)"')
DATTR_RE = re.compile(r'<path[^>]*\bd="([^"]+)"')
CHAR_RE = re.compile(r'<svg[^>]*data-strokesvg="([^"]+)"')


def _abs_lead(d: str) -> str:
    """A standalone path's leading relative `m` is treated as ABSOLUTE by the SVG spec; when concatenating
    path elements that context is lost. Convert `m x y …` to `M x y …` — BUT implicit pairs after `m` are
    RELATIVE linetos while after `M` they'd become absolute, so the remainder must gain an explicit `l`
    (e.g. `m142 394 538-121` -> `M142 394l538-121`)."""
    d = d.strip()
    if not d.startswith("m"):
        return d
    m = re.match(r"m\s*(-?[\d.]+)[\s,]+(-?[\d.]+)\s*(.*)", d, re.S)
    if not m:
        return "M" + d[1:]
    x, y, rest = m.group(1), m.group(2), m.group(3).strip()
    if rest and not rest[0].isalpha():
        rest = "l" + rest  # implicit pairs after a moveto stay RELATIVE linetos
    return f"M{x} {y}{rest}"


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

    def shadow_of_path(path_markup: str) -> str:
        """Shadow outline for ONE sub-path's clip reference ('' if unclipped, e.g. dots)."""
        m2 = re.search(r'clip-path="url\(#([^)]+)\)"', path_markup)
        if not m2:
            return ""
        d = shadow_by_id.get(clip_target.get(m2.group(1), ""), "")
        return _abs_lead(d) if d else ""

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
                shadows.append([shadow_of_path(chunk)])
            p = end
        else:
            gend = inner.find("</g>", g) + 4
            chunk = inner[g:gend]
            # PER SUB-PATH: each piece keeps ITS OWN shadow clip (joining them lets the fat pen band paint a
            # DISTANT region of the same stroke early — め's loop "irradiated" at the stroke start).
            subs = re.findall(r"<path[^>]*/>", chunk)
            ds = [DATTR_RE.search(s) for s in subs]
            if any(ds):
                strokes.append(" ".join(_abs_lead(m2.group(1)) for m2 in ds if m2))
                shadows.append([shadow_of_path(s) for s, m2 in zip(subs, ds) if m2])
            p = gend
    return strokes, shadows


# ---------- minimal SVG path tokenizer + translate (all commands, compact arc flags) ----------
NUM = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
ARITY = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "A": 7, "Z": 0}


def parse(d: str) -> list[tuple[str, list[str]]]:
    segs: list[tuple[str, list[str]]] = []
    i, n = 0, len(d)
    while i < n:
        c = d[i]
        if c in " ,\t\n\r":
            i += 1; continue
        if not c.isalpha():
            raise ValueError(f"expected command at {i}: {d[i:i+20]!r}")
        cmd, i, args = c, i + 1, []
        k = ARITY[cmd.upper()]
        while True:
            while i < n and d[i] in " ,\t\n\r":
                i += 1
            if i >= n or d[i].isalpha():
                break
            if cmd in "Aa" and len(args) % 7 in (3, 4):
                if d[i] not in "01":
                    raise ValueError(f"bad arc flag at {i}")
                args.append(d[i]); i += 1; continue
            m = NUM.match(d, i)
            if not m:
                raise ValueError(f"bad number at {i}: {d[i:i+20]!r}")
            args.append(m.group()); i = m.end()
        if k == 0:
            assert not args, d
        elif not args or len(args) % k:
            raise ValueError(f"{cmd} with {len(args)} args")
        segs.append((cmd, args))
    return segs


def _axis(cmd: str, j: int, k: int) -> str | None:
    """'x' / 'y' / None for arg j of an (absolute) command with arity k."""
    u, p = cmd.upper(), j % k
    if u == "H": return "x"
    if u == "V": return "y"
    if u == "A": return {5: "x", 6: "y"}.get(p)
    return "x" if p % 2 == 0 else "y"


def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:.3f}".rstrip("0")


def translate(d: str, dx: float, dy: float) -> str:
    """Shift a path's ABSOLUTE coordinates by (dx, dy); relative segments are untouched."""
    out = []
    for cmd, args in parse(d):
        k = ARITY[cmd.upper()]
        if cmd.isupper() and k:
            args = [_fmt(float(a) + (dx if _axis(cmd, j, k) == "x" else dy)) if _axis(cmd, j, k) else a
                    for j, a in enumerate(args)]
        out.append(cmd + " ".join(args))
    return "".join(out)


# P3-yoon: the 66 yoon composites (base glyph + small ya/yu/yo one em cell to the right), verified in
# research/derived/pending/yoon_strokes.verdict.json. The tracked table is the exact-match contract:
# the composition is re-derived here from the rows just parsed and must reproduce every table row.
YOON_TABLE = ROOT / "research" / "derived" / "repairs" / "yoon_strokes.json"
ADV = 1024  # strokesvg em square: every parsed record's viewbox is 0 0 1024 1024
# Layer policy for ALL derived rows (っ/ッ + the 66 yoon): 'B'. They are not in the strokesvg dataset
# (Layer A is dataset-only, spec §1.1); they are deterministic transforms of Layer-A rows, no AI,
# machine-checked against those rows (the table's exact match). Parsed rows stay 'A'.
DERIVED_LAYER = "B"
COLS = ("char", "kind", "viewbox", "strokes", "shadows", "source", "license")


def yoon_rows(con: sqlite3.Connection) -> list[dict]:
    """Compose the table's 66 rows from the live kana_stroke records; raise on any drift."""
    table = json.loads(YOON_TABLE.read_text(encoding="utf-8"))
    rec = {r[0]: dict(zip(COLS, r)) for r in con.execute(f"SELECT {','.join(COLS)} FROM kana_stroke")}
    for r in rec.values():
        r["strokes"] = json.loads(r["strokes"])
        r["shadows"] = json.loads(r["shadows"]) if r["shadows"] else None
    want = {r["char"]: r for r in table["rows"]}
    assert len(want) == table["row_count"] == len(table["derivation"]) == 66, "yoon table shape"
    out = []
    for d in table["derivation"]:
        b, s = rec[d["base"]], rec[d["small"]]  # KeyError = a component lost its stroke data
        assert b["viewbox"] == s["viewbox"] == f"0 0 {ADV} {ADV}" and b["kind"] == s["kind"], d["char"]
        row = {
            "char": d["char"], "kind": b["kind"], "viewbox": f"0 0 {2 * ADV} {ADV}",
            "strokes": b["strokes"] + [translate(p, ADV, 0) for p in s["strokes"]],
            "shadows": (b["shadows"] or [[""] for _ in b["strokes"]])
                       + [[translate(p, ADV, 0) if p else "" for p in sh]
                          for sh in (s["shadows"] or [[""] for _ in s["strokes"]])],
            "source": f"strokesvg (derived: composite of {d['base']} + {d['small']})",
            "license": b["license"],
        }
        if row != want.get(d["char"]):
            raise SystemExit(f"yoon {d['char']}: composition != {YOON_TABLE.name} row (component drift); nothing written")
        out.append(row)
    return out


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
            con.execute("INSERT OR REPLACE INTO kana_stroke (char,kind,viewbox,strokes,shadows,source,license,layer) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (dst, r[0], r[1], r[2], r[3], f"strokesvg (derived: same glyph as {src})", r[4], DERIVED_LAYER))
    yoon = yoon_rows(con)  # all 66 verified before any is written
    for y in yoon:
        con.execute("INSERT OR REPLACE INTO kana_stroke (char,kind,viewbox,strokes,shadows,source,license,layer) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (y["char"], y["kind"], y["viewbox"], json.dumps(y["strokes"], ensure_ascii=False),
                     json.dumps(y["shadows"], ensure_ascii=False), y["source"], y["license"], DERIVED_LAYER))
    print(f"strokesvg kana: 2 sokuon + {len(yoon)} yoon derived (layer {DERIVED_LAYER})")
    con.commit()
    tot = con.execute("SELECT COUNT(*) FROM kana_stroke").fetchone()[0]
    by = dict(con.execute("SELECT kind, COUNT(*) FROM kana_stroke GROUP BY kind").fetchall())
    con.close()
    print(f"strokesvg kana: ingested {n}; table now {tot} ({by})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
