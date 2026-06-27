# strokesvg — dataset manifest (provenance)

- **Source:** `zhengkyl/strokesvg` (https://github.com/zhengkyl/strokesvg), `dist/` optimized SVGs.
- **Used for:** **kana stroke-order** drawing data (hiragana + katakana) — clean per-stroke centerline paths
  (animatable), NOT kanji (strokesvg has no kanji).
- **License (PERMISSIVE, no CC BY-SA / no copyleft on our app):**
  - The kana SVG glyph data is **derived from the Klee One font, SIL Open Font License (OFL)** — commercial use,
    bundling, and redistribution permitted; copyleft applies only to the *font/derivative-font*, not to our app
    (we bundle the resulting stroke SVGs like a font, attributed).
  - All other files: **MIT**.
  - Verified from repo `LICENSE` (2026-06-26).
- **Attribution text (to display):** *"Kana stroke-order from strokesvg (© Kyle), glyphs based on the Klee One
  font (SIL OFL); MIT."*
- **Coverage:** 79 hiragana + 81 katakana (incl. dakuten/handakuten/combos).
- **Format adaptation:** we parse each SVG's `<g data-strokesvg="strokes">` per-stroke centerline `<path d>`
  (ordered by `--i`) + viewBox into OUR schema (`kana_stroke` table → `corpus/strokes/kana.json`), rendered with
  a dash-offset pen-draw animation. We ship our re-expressed stroke data, not the raw files.
- **NOTE:** strokesvg is KANA-only — it does NOT fill the 898-kanji stroke tail (that needs GlyphWiki).
