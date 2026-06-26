#!/usr/bin/env python3
"""Ingest Kanji Alive (CC BY 4.0) stroke-order data into OUR schema (license_audit.md D-LIC-2). The raw data is
cumulative filled-outline step SVGs ({kname}_{N}.svg, N=1..strokes) named by romaji `kname`; ka_data.csv maps
kname→kanji + radical. We adapt it into a `kanji_stroke` row per kanji: {total_strokes, viewbox, transform,
steps[path_d]} — our own re-expressed format, attributed to Kanji Alive (provenance in `source`). Idempotent.
Usage: kanjialive_strokes.py"""
from __future__ import annotations
import csv, json, re, sqlite3, sys, zipfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
KA = ROOT / "research" / "datasets" / "kanjialive"
PATH_RE = re.compile(r'<path[^>]*\bd="([^"]+)"', re.S)
VB_RE = re.compile(r'viewBox="([^"]+)"')
TR_RE = re.compile(r'<g[^>]*transform="([^"]+)"')


def main() -> int:
    rows = list(csv.DictReader((KA / "ka_data.csv").open(encoding="utf-8")))
    zf = zipfile.ZipFile(KA / "kanji_strokes.zip")
    names = set(zf.namelist())
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS kanji_stroke (
        kanji_id INTEGER PRIMARY KEY, character TEXT, total_strokes INTEGER, viewbox TEXT, transform TEXT,
        steps TEXT, source TEXT, license TEXT, layer TEXT DEFAULT 'A')""")
    kid_of = {ch: kid for ch, kid in con.execute("SELECT character, id FROM kanji")}
    ingested = skipped = missing = 0
    for r in rows:
        ch = r["kanji"]
        kid = kid_of.get(ch)
        if kid is None:
            skipped += 1            # Kanji Alive kanji not in our registry
            continue
        kname = r["kname"]
        try:
            n = int(r["kstroke"])
        except ValueError:
            n = 0
        steps, viewbox, transform = [], None, None
        ok = True
        for i in range(1, n + 1):
            fn = f"kanji_strokes/{kname}_{i}.svg"
            if fn not in names:
                ok = False
                break
            svg = zf.read(fn).decode("utf-8", "ignore")
            m = PATH_RE.search(svg)
            if not m:
                ok = False
                break
            steps.append(m.group(1).strip())
            if viewbox is None:
                vb, tr = VB_RE.search(svg), TR_RE.search(svg)
                viewbox = vb.group(1) if vb else "0 0 248 248"
                transform = tr.group(1) if tr else ""
        if not ok or not steps:
            missing += 1
            continue
        con.execute(
            "INSERT OR REPLACE INTO kanji_stroke (kanji_id, character, total_strokes, viewbox, transform, steps, "
            "source, license, layer) VALUES (?,?,?,?,?,?,?,?,'A')",
            (kid, ch, len(steps), viewbox, transform, json.dumps(steps, ensure_ascii=False),
             "kanjialive", "CC-BY-4.0"))
        ingested += 1
    con.commit()
    tot = con.execute("SELECT COUNT(*) FROM kanji_stroke").fetchone()[0]
    con.close()
    print(f"kanjialive strokes: ingested {ingested}, skipped(not in registry) {skipped}, "
          f"missing-files {missing}; table now {tot} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
