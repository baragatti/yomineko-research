# Kanji Alive — dataset manifest (provenance)

- **Source:** Kanji alive (https://kanjialive.com) — repo `kanjialive/kanji-data-media`
  (https://github.com/kanjialive/kanji-data-media).
- **Used for:** per-kanji **stroke-order** drawing data (`kanji-strokes/kanji_strokes.zip`) +
  `language-data/ka_data.csv` (kanji↔kname mapping, stroke count, radical char/name/position).
- **License:** **Creative Commons Attribution 4.0 International (CC BY 4.0)** — commercial use + redistribution
  permitted, attribution required, **NO ShareAlike**. (The separate *Japanese Radicals* font is Apache 2.0.)
  Verified from repo `LICENSE.md` (2026-06-26).
- **Attribution text (to display):** *"Kanji stroke-order data © Kanji alive (https://kanjialive.com),
  licensed CC BY 4.0."*
- **Files fetched (2026-06-26):**
  - `kanji_strokes.zip` — SHA256 `ad1327b57ded0db7a4d325b83d63bbd4f5af6379f22db5e2b020ea869b1deb71`
    (12,977,338 bytes; 11,933 SVGs; cumulative filled-outline step SVGs `{kname}_{N}.svg`, N = 1..stroke_count).
  - `ka_data.csv` — 1,235 kanji rows.
- **Coverage:** 1,235 kanji; matches **1,233** of our 2,131 leveled kanji (N5–N1). The remaining **898** (mostly
  rarer N1) have no Kanji Alive stroke data → shown via permissive **decomposition** (Unihan radical + IDS components).
- **Format adaptation:** the raw cumulative-step SVGs are adapted into OUR schema (`kanji_stroke` table →
  `corpus/strokes/`), storing only `{viewbox, transform, steps:[path_d,…]}` per kanji. We do not ship the raw
  Kanji Alive files; we ship our re-expressed stroke data with attribution above.
- **NOT used:** `kanji-animations/animations-mp4.zip` (raster video, against the no-PNG/SVG-only preference).
