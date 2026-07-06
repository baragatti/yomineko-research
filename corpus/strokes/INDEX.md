# corpus/strokes — kanji stroke-order (our format)

Per-kanji progressive stroke-order data adapted from **Kanji alive (CC BY 4.0)** — see `research/datasets/kanjialive/MANIFEST.md` + `ATTRIBUTION.md`. Each entry: `{character, total_strokes, viewbox, transform, steps:[path_d,…]}` where `steps[k]` is the cumulative outline after k strokes (render progressively to draw the kanji). Source = `kanjialive`, license `CC-BY-4.0` (attribution, NO ShareAlike).

- `kana.json` — 162 kanji
- `lines_n1.json` — 1110 kanji
- `lines_n2.json` — 365 kanji
- `lines_n3.json` — 346 kanji
- `lines_n4.json` — 174 kanji
- `lines_n5.json` — 103 kanji
- `n1.json` — 246 kanji
- `n2.json` — 357 kanji
- `n3.json` — 350 kanji
- `n4.json` — 177 kanji
- `n5.json` — 103 kanji
