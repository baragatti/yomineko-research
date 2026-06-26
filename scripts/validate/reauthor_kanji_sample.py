#!/usr/bin/env python3
"""Re-authoring sampler for kanji meanings (license_audit.md D-LIC-1: replace verbatim-KANJIDIC2 meanings with
our OWN independently-authored glosses to remove CC BY-SA dependence). For each kanji it gathers ONLY facts +
disambiguators — character, readings (on/kun), stroke count, radical, and up to 4 example words that use it
(headword + kana, NO glosses) — and DELIBERATELY omits the current KANJIDIC meanings, so the generation agent
must write its own definitions from knowledge, not copy the dictionary's selection/wording. Facts stay; the
copyrightable compilation is re-authored. Writes research/derived/reauthor/kanji/batch_*.json.
Usage: reauthor_kanji_sample.py [--batch 60]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=60)
    args = ap.parse_args()
    c = sqlite3.connect(DB)
    # readings per kanji
    rd: dict = {}
    for kid, rdg, rtype, oku in c.execute(
            "SELECT kanji_id, reading, reading_type, okurigana FROM kanji_reading"):
        d = rd.setdefault(kid, {"on": [], "kun": []})
        if rtype == "on":
            d["on"].append(rdg)
        else:
            d["kun"].append(rdg + ("." + oku if oku else ""))
    sample = []
    for kid, ch, strokes, radical, level in c.execute(
            "SELECT id, character, strokes, kangxi_radical, level FROM kanji "
            "WHERE level IN ('n5','n4','n3','n2','n1') ORDER BY id"):
        ex = [{"w": w, "kana": k} for w, k in c.execute(
            "SELECT headword, kana FROM vocab WHERE headword LIKE '%'||?||'%' "
            "ORDER BY (freq_rank IS NULL), freq_rank LIMIT 4", (ch,))]
        r = rd.get(kid, {"on": [], "kun": []})
        sample.append({"id": kid, "character": ch, "level": level, "strokes": strokes,
                       "radical": radical, "on": r["on"][:6], "kun": r["kun"][:6], "examples": ex})
    outdir = ROOT / "research" / "derived" / "reauthor" / "kanji"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_sample.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    print(f"reauthor kanji: {len(sample)} kanji -> {nb} batches (batch={args.batch})  dir={outdir}")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
