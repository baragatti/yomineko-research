# corpus/strokes — kanji stroke-order (our format)

Per-kanji progressive stroke-order data adapted from **Kanji alive (CC BY 4.0)** — see `research/datasets/kanjialive/MANIFEST.md` + `ATTRIBUTION.md`. Each entry: `{character, total_strokes, viewbox, transform, steps:[path_d,…]}` where `steps[k]` is the cumulative outline after k strokes (render progressively to draw the kanji). Source = `kanjialive`, license `CC-BY-4.0` (attribution, NO ShareAlike).

- `n1.json` — 247 kanji
- `n2.json` — 369 kanji
- `n3.json` — 364 kanji
- `n4.json` — 173 kanji
- `n5.json` — 80 kanji
