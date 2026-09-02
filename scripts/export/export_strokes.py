#!/usr/bin/env python3
"""Export the kanji_stroke table (Kanji Alive CC BY 4.0, adapted to our format) to durable corpus JSON, split by
level. Shape per kanji: {kanji_id, character, total_strokes, viewbox, transform, steps:[path_d,…], source}.
Re-run after re-ingesting strokes. Usage: export_strokes.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = ROOT / "corpus" / "strokes"


def main() -> int:
    con = sqlite3.connect(DB)
    OUT.mkdir(parents=True, exist_ok=True)
    by_level: dict = {}
    for ch, lvl, tot, vb, tr, steps, src, lic in con.execute(
            "SELECT ks.character, k.level, ks.total_strokes, ks.viewbox, ks.transform, ks.steps, ks.source, "
            "ks.license FROM kanji_stroke ks JOIN kanji k ON k.id=ks.kanji_id "
            "WHERE k.level IN ('n5','n4','n3','n2','n1') ORDER BY k.id"):
        by_level.setdefault(lvl, []).append({
            "character": ch, "total_strokes": tot, "viewbox": vb, "transform": tr,
            "steps": json.loads(steps), "source": src, "license": lic})
    counts = {}
    for lvl, items in by_level.items():
        (OUT / f"{lvl}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        counts[lvl] = len(items)
    # kanji per-stroke CENTERLINES (GlyphWiki KAGE-derived, permissive) — the animation data. Only
    # count-matching kanji (n_strokes == KANJIDIC) are exported; the rest fall back to the outline steps.
    if con.execute("SELECT name FROM sqlite_master WHERE name='kanji_stroke_line'").fetchone():
        by_lvl_lines: dict = {}
        for ch, lvl, strokes in con.execute(
                "SELECT k.character,k.level,ksl.strokes FROM kanji_stroke_line ksl JOIN kanji k ON k.id=ksl.kanji_id "
                "WHERE ksl.count_match=1 AND k.level IN ('n5','n4','n3','n2','n1')"):
            by_lvl_lines.setdefault(lvl, []).append({
                "character": ch, "strokes": json.loads(strokes), "source": "glyphwiki",
                "license": "GlyphWiki-free"})
        for lvl, items in by_lvl_lines.items():
            (OUT / f"lines_{lvl}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            counts[f"lines_{lvl}"] = len(items)
    # kana stroke-order (strokesvg, OFL+MIT) — per-stroke centerlines
    kana = [{"char": ch, "kind": kind, "viewbox": vb, "strokes": json.loads(st),
             "shadows": json.loads(sh) if sh else None, "source": src, "license": lic}
            for ch, kind, vb, st, sh, src, lic in con.execute(
                "SELECT char, kind, viewbox, strokes, shadows, source, license FROM kana_stroke ORDER BY kind, char")]
    if kana:
        (OUT / "kana.json").write_text(json.dumps(kana, ensure_ascii=False), encoding="utf-8")
        counts["kana"] = len(kana)
    (OUT / "INDEX.md").write_text(
        "# corpus/strokes — kanji stroke-order (our format)\n\n"
        "Per-kanji progressive stroke-order data adapted from **Kanji alive (CC BY 4.0)** — see "
        "`research/datasets/kanjialive/MANIFEST.md` + `ATTRIBUTION.md`. Each entry: `{character, total_strokes, "
        "viewbox, transform, steps:[path_d,…]}` where `steps[k]` is the cumulative outline after k strokes "
        "(render progressively to draw the kanji). Source = `kanjialive`, license `CC-BY-4.0` (attribution, NO "
        "ShareAlike).\n\n" + "".join(f"- `{lvl}.json` — {n} kanji\n" for lvl, n in sorted(counts.items())),
        encoding="utf-8")
    con.close()
    print(f"exported strokes -> corpus/strokes/  {counts}  (total {sum(counts.values())})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
