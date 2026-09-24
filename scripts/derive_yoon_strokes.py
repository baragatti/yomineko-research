"""Derive composite stroke records for the 66 yoon kana (base glyph + small ya/yu/yo) from the
strokesvg-derived records in corpus/strokes/kana.json (read from git HEAD). Files only.
Writes research/derived/pending/yoon_strokes.json; `--svg DIR` also renders 6 inspection SVGs there.
FROZEN (P3-yoon): its output was verified and landed as research/derived/repairs/yoon_strokes.json, applied by
scripts/ingest/strokesvg_kana.py. HEAD now carries the 66 rows, so a re-run stops at its not-in-registry assert."""
from __future__ import annotations
import hashlib, json, re, statistics, subprocess, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = Path(sys.argv[sys.argv.index("--svg") + 1]) if "--svg" in sys.argv else None
OUT = ROOT / "research/derived/pending/yoon_strokes.json"


def head(path: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{path}"], check=True, capture_output=True).stdout


# Path tokenizer + translate live with the tracked DB writer (P3-yoon), one implementation for both.
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
from strokesvg_kana import ARITY, NUM, parse, translate  # noqa: E402


def bbox(d: str) -> tuple[float, float, float, float]:
    """Hull of on-curve + control points (fine for measuring placement/scale)."""
    xs, ys = [], []
    cx = cy = sx = sy = 0.0
    for cmd, args in parse(d):
        u, rel, k = cmd.upper(), cmd.islower(), ARITY[cmd.upper()]
        if u == "Z":
            cx, cy = sx, sy; continue
        f = [float(a) for a in args]
        for g in range(0, len(f), k):
            p = f[g:g + k]
            if u == "H":
                cx = cx + p[0] if rel else p[0]; xs.append(cx); ys.append(cy); continue
            if u == "V":
                cy = cy + p[0] if rel else p[0]; xs.append(cx); ys.append(cy); continue
            pts = [(p[5], p[6])] if u == "A" else [(p[q], p[q + 1]) for q in range(0, k, 2)]
            pts = [(x + cx, y + cy) if rel else (x, y) for x, y in pts]
            for x, y in pts:
                xs.append(x); ys.append(y)
            cx, cy = pts[-1]
            if u == "M" and g == 0:
                sx, sy = cx, cy
    return min(xs), min(ys), max(xs), max(ys)


def ink(rec: dict) -> tuple[float, float, float, float]:
    paths = [p for s in (rec["shadows"] or []) for p in s if p] or rec["strokes"]
    bs = [bbox(p) for p in paths]
    return min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)


# ---------- inputs (git HEAD) ----------
strokes_raw = head("corpus/strokes/kana.json")
REG = {r["char"]: r for r in json.loads(strokes_raw)}
glyphs = json.loads(head("corpus/kana/hiragana.json")) + json.loads(head("corpus/kana/katakana.json"))
yoon = [g for g in glyphs if g["type"] == "yoon"]
assert len(yoon) == 66, len(yoon)

# round-trip self-check of the tokenizer on every path in the registry
for r in REG.values():
    for p in r["strokes"] + [x for s in (r["shadows"] or []) for x in s if x]:
        assert bbox(translate(p, 0, 0)) == bbox(p), (r["char"], p[:40])
        b0, b1 = bbox(p), bbox(translate(p, 1024, 7))
        assert all(abs(a - b) < 1e-6 for a, b in zip((b0[0] + 1024, b0[1] + 7, b0[2] + 1024, b0[3] + 7), b1)), r["char"]

# ---------- measure: small vs full size, and where the font places the small form in its cell ----------
SMALL_FULL = {"ぁ": "あ", "ぃ": "い", "ぅ": "う", "ぇ": "え", "ぉ": "お", "ゃ": "や", "ゅ": "ゆ", "ょ": "よ", "ゎ": "わ",
              "ァ": "ア", "ィ": "イ", "ゥ": "ウ", "ェ": "エ", "ォ": "オ", "ャ": "ヤ", "ュ": "ユ", "ョ": "ヨ", "ヮ": "ワ",
              "ヵ": "カ", "ヶ": "ケ"}
pairs = []
for s, f in SMALL_FULL.items():
    if s in REG and f in REG:
        a, b = ink(REG[s]), ink(REG[f])
        pairs.append({"small": s, "full": f,
                      "w_ratio": round((a[2] - a[0]) / (b[2] - b[0]), 3),
                      "h_ratio": round((a[3] - a[1]) / (b[3] - b[1]), 3),
                      "small_ink_bbox": [round(v) for v in a], "full_ink_bbox": [round(v) for v in b]})
ratio = statistics.median([(p["w_ratio"] + p["h_ratio"]) / 2 for p in pairs])
for p in pairs:
    print(p)
print("median small/full ratio", ratio)

# ---------- derive ----------
ADV = 1024  # strokesvg em square / advance width: every record's viewbox is 0 0 1024 1024
assert {r["viewbox"] for r in REG.values()} == {"0 0 1024 1024"}
rows, derivation = [], []
for g in yoon:
    base, small = g["char"][0], g["char"][1]
    b, s = REG[base], REG[small]  # KeyError here = a component without stroke data
    assert b["kind"] == s["kind"]
    rows.append({
        "char": g["char"], "kind": b["kind"], "viewbox": f"0 0 {2 * ADV} {ADV}",
        "strokes": b["strokes"] + [translate(p, ADV, 0) for p in s["strokes"]],
        "shadows": (b["shadows"] or [[""] for _ in b["strokes"]])
                   + [[translate(p, ADV, 0) if p else "" for p in sh] for sh in (s["shadows"] or [[""] for _ in s["strokes"]])],
        "source": f"strokesvg (derived: composite of {base} + {small})",
        "license": b["license"],
    })
    assert b["license"] == s["license"] == "OFL-1.1+MIT"
    derivation.append({"char": g["char"], "glyph_id": g["id"], "base": base, "small": small,
                       "base_strokes": len(b["strokes"]), "small_strokes": len(s["strokes"]),
                       "small_offset": [ADV, 0],
                       "base_source_file": f"research/datasets/strokesvg/dist/{b['kind']}/{base}.svg",
                       "small_source_file": f"research/datasets/strokesvg/dist/{s['kind']}/{small}.svg",
                       "base_registry_source": b["source"], "small_registry_source": s["source"]})
rows.sort(key=lambda r: (r["kind"], r["char"]))  # exporter order: ORDER BY kind, char
derivation.sort(key=lambda r: (REG[r["base"]]["kind"], r["char"]))
for r in rows:
    assert len(r["strokes"]) == len(r["shadows"])
    assert list(r) == list(next(iter(REG.values()))), "shape drift"
    assert r["char"] not in REG

small_cells = {c: [round(v) for v in ink(REG[c])] for c in "ゃゅょャュョ"}
doc = {
    "why": "W29 follow-up (research/reports/w29_kana_cards_report.md §5 R2, the 'alternative that removes R2'). "
           "The 66 yoon glyphs have no record in corpus/strokes/kana.json, so W29 drops their handwriting card. "
           "Every yoon is a base glyph plus a small ya/yu/yo, and both components already have strokesvg records. "
           "Composing them gives every kana glyph stroke data, so all 211 glyph cards keep recognition, "
           "production and handwriting.",
    "definition": "One row per yoon glyph, in exactly the corpus/strokes/kana.json record shape "
                  "{char, kind, viewbox, strokes, shadows, source, license}, sorted like the exporter (kind, char). "
                  "Stroke order = the base glyph's strokes in their own order, then the small glyph's. "
                  "The base keeps its coordinates. The small glyph is the registry's own small-form record "
                  "(already drawn by the font at small size, sitting low in its em cell) translated one advance "
                  "(+1024 x, 0 y) into the next cell, which is how a digraph is written: two cells, the small kana "
                  "at the lower right of the base. No scaling is applied, because the small-form data exists "
                  "for all six of ゃゅょャュョ. viewbox is therefore 0 0 2048 1024 (two em cells).",
    "status": "PENDING (derivation only). Nothing in corpus/, db/ or the exporter is written. Apply = (1) land "
              "the composition as a tracked DB writer: extend scripts/ingest/strokesvg_kana.py, where the っ/ッ "
              "derivation already lives, or add a script registered in research/derived/rebuild_manifest.json "
              "after step 6; (2) write the 66 rows into kana_stroke with layer set explicitly, since the column "
              "defaults to 'A' and the っ/ッ derived rows carry 'A' today, so pick one layer policy for all 68 "
              "derived rows; (3) re-export. corpus/strokes/kana.json then goes 162 -> 228 records, and the counts "
              "in ATTRIBUTION.md (strokesvg section) and design/sources.md must read 160 parsed + 68 derived, "
              "with the derived line naming the 66 yoon composites beside っ/ッ.",
    "generated_by": "scripts/derive_yoon_strokes.py (mechanical composition, no AI, no hand edits); the apply "
                    "must land the same composition as a tracked DB writer (status step 1)",
    "layer": "B (deterministic transform over Layer-A strokesvg records; ai_generated false)",
    "provenance": {
        "input": "corpus/strokes/kana.json @ git HEAD",
        "input_sha256": hashlib.sha256(strokes_raw).hexdigest(),
        "glyph_list": "corpus/kana/hiragana.json + corpus/kana/katakana.json @ git HEAD, type == 'yoon'",
        "upstream": "zhengkyl/strokesvg dist/**/*.svg, parsed by scripts/ingest/strokesvg_kana.py",
        "per_row": "derivation[] names both component records and the dist SVG each came from",
    },
    "license": {
        "value": "OFL-1.1+MIT (carried unchanged from both components)",
        "note": "The kana SVGs of strokesvg are derived from the Klee One font and governed by SIL OFL 1.1 "
                "(research/datasets/strokesvg/LICENSE NOTICE; ATTRIBUTION.md 'strokesvg / Klee One'; "
                "research/reports/w42_attribution_report.md §1.1). Under the conservative reading ATTRIBUTION.md "
                "adopts (whether derived centerline data counts as Font Software is an owner legal call), a "
                "composite of two such records is a further Modified Version of the Font Software: OFL condition 5 "
                "keeps it under OFL 1.1, and the shipped app must carry the full OFL text plus both copyright lines "
                "(© 2024 Kyle; © 2020 The Klee Project Authors). No Reserved Font Name is declared, so no renaming "
                "duty. It is never sold by itself (condition 1).",
    },
    "measurements": {
        "small_ink_bbox_in_own_cell": small_cells,
        "small_vs_full_pairs": pairs,
        "median_small_full_ratio": round(ratio, 3),
        "note": "Ink bboxes from shadow outlines (hull incl. control points). They confirm the registry's small "
                "forms are already scaled (~the median ratio) and bottom-placed by the font, so composing them "
                "unscaled reproduces the font's own digraph layout; the ratio would only be needed if a small "
                "record were missing, and none is.",
    },
    "counts": {"rows": len(rows), "hiragana": sum(r["kind"] == "hiragana" for r in rows),
               "katakana": sum(r["kind"] == "katakana" for r in rows),
               "components_missing_stroke_data": 0},
    "derivation": derivation,
    "row_count": len(rows),
    "rows": rows,
}
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", OUT, len(rows))

# ---------- inspection renders ----------
COLORS = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b", "#e377c2", "#17becf"]
SUB = re.compile(r"(?=M)")


def render(rec: dict) -> str:
    vb = rec["viewbox"]
    w, h = map(int, vb.split()[2:])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w // 4}" height="{h // 4}">',
             f'<rect width="{w}" height="{h}" fill="#fff"/>',
             f'<line x1="{ADV}" y1="0" x2="{ADV}" y2="{h}" stroke="#ccc" stroke-dasharray="16 16" stroke-width="4"/>',
             "<defs>"]
    body = []
    for i, (st, sh) in enumerate(zip(rec["strokes"], rec["shadows"])):
        subs = [p.strip() for p in SUB.split(st) if p.strip()]
        col = COLORS[i % len(COLORS)]
        for j, sp in enumerate(subs):
            shadow = sh[j] if j < len(sh) else ""
            if shadow:
                parts.append(f'<clipPath id="c{i}_{j}"><path d="{shadow}"/></clipPath>')
                body.append(f'<path d="{shadow}" fill="#e6e6e6"/>')
            clip = f' clip-path="url(#c{i}_{j})"' if shadow else ""
            body.append(f'<path d="{sp}" fill="none" stroke="{col}" stroke-width="90" stroke-linecap="round" '
                        f'stroke-linejoin="round" opacity="0.75"{clip}/>')
        x, y = (float(v) for v in NUM.findall(subs[0])[:2])
        body.append(f'<circle cx="{x}" cy="{y}" r="34" fill="{col}"/><text x="{x}" y="{y + 16}" font-size="46" '
                    f'text-anchor="middle" fill="#fff" font-family="sans-serif">{i + 1}</text>')
    parts.append("</defs>")
    return "\n".join(parts + body + ["</svg>"])


PICK = {"きゃ": "kya_hira", "しゅ": "shu_hira", "ちょ": "cho_hira", "ぴゃ": "pya_hira", "キュ": "kyu_kata", "ジョ": "jo_kata"}
if SVG_DIR:
    by = {r["char"]: r for r in rows}
    for ch, name in PICK.items():
        (SVG_DIR / f"{name}.svg").write_text(render(by[ch]), encoding="utf-8")
    print("rendered", list(PICK))
