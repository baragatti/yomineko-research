#!/usr/bin/env python3
"""Export the `reading` table (in-lesson reading-practice boxes — design/reading_practice.md) to durable corpus
JSON, split by level. Readings are assembled by SELECTION from the verified sentence bank (real Tatoeba/JEC text,
human EN, our re-authored pt-BR, dissected); each is i+0 for the lesson it is gated to (every kanji + content
vocab already in that lesson's cumulative_known_set). Shape per box:
  {slug, level, gated_to_lesson, title:{pt-BR,en}, jp, tokens:[{s,r,ro,pos}…],
   translation:{pt-BR,en}, length_band, uses:{kanji:[char…],vocab:[headword…]}, source_slugs:[sent:…],
   ai_generated, needs_review, layer}
Re-run after build_readings.py. Usage: export_readings.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUT = ROOT / "corpus" / "readings"


def main() -> int:
    con = sqlite3.connect(DB)
    if not con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reading'").fetchone():
        print("export_readings: no reading table (run build_readings.py first) — nothing to export")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    char_by_kid = {i: ch for i, ch in con.execute("SELECT id,character FROM kanji")}
    hw_by_vid = {i: hw for i, hw in con.execute("SELECT id,headword FROM vocab")}
    by_level: dict = {}
    for (slug, level, lesson, tpt_title, ten_title, jp, tokens, tpt, ten, uses, band, src, ai, nr,
         layer) in con.execute(
            "SELECT slug,level,gated_to_lesson,title_pt,title_en,jp,tokens,translation_pt,translation_en,uses,"
            "length_band,source_slugs,ai_generated,needs_review,layer FROM reading ORDER BY gated_to_lesson,slug"):
        u = json.loads(uses or "{}")
        by_level.setdefault(level, []).append({
            "slug": slug, "level": level, "gated_to_lesson": lesson,
            "title": {"pt-BR": tpt_title or "Leitura", "en": ten_title or "Reading"},
            "jp": jp, "tokens": json.loads(tokens or "[]"),
            "translation": {"pt-BR": tpt or "", "en": ten or ""},
            "length_band": band,
            "uses": {"kanji": [char_by_kid[k] for k in u.get("kanji", []) if k in char_by_kid],
                     "vocab": [hw_by_vid[v] for v in u.get("vocab", []) if v in hw_by_vid]},
            "source_slugs": json.loads(src or "[]"),
            "ai_generated": ai or 0, "needs_review": nr if nr is not None else 1, "layer": layer or "B"})
    counts = {}
    for lvl, items in by_level.items():
        (OUT / f"{lvl}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        counts[lvl] = len(items)
    (OUT / "INDEX.md").write_text(
        "# corpus/readings — in-lesson reading-practice boxes (our format)\n\n"
        "Short reading passages attached to lessons, assembled by **SELECTION** from the verified sentence bank "
        "(no generation): real **Tatoeba (CC BY 2.0 FR)** / **JEC (CC BY 3.0)** Japanese, human EN, our "
        "re-authored pt-BR, fully dissected. Each box is **i+0** for the lesson it is gated to — every kanji and "
        "content word it uses is already in that lesson's `cumulative_known_set` (HARD gate, validated by "
        "`scripts/validate/validate_readings.py`). See `design/reading_practice.md`.\n\n"
        "Per box: `{slug, level, gated_to_lesson, title, jp, tokens:[{s,r,ro,pos}], translation:{pt-BR,en}, "
        "length_band, uses:{kanji,vocab}, source_slugs:[sent:…]}`. `source_slugs` credit the underlying bank "
        "sentences (provenance). Layer **B** (derived-and-verified), `needs_review: 1`.\n\n"
        + "".join(f"- `{lvl}.json` — {n} boxes\n" for lvl, n in sorted(counts.items())),
        encoding="utf-8")
    con.close()
    print(f"exported readings -> corpus/readings/  {counts}  (total {sum(counts.values())})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
