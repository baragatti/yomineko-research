# GlyphWiki dump — kanji KAGE glyph data (per-stroke centerlines)

- **Source URL:** https://glyphwiki.org/dump.tar.gz
- **Fetched:** 2026-07-04
- **SHA256 (dump.tar.gz, first 32 hex):** d2eefb3543043bfd8d2766e181c9c975
- **Contents used:** `dump_newest_only.txt` (name | related | KAGE data; 2,465,254 glyphs)
- **License:** bundled `LICENSE.txt` (© 2009 GlyphWiki Project): *"Unlimited permission is hereby granted to
  use, copy, and distribute these files, with or without modification, either commercially or
  non-commercially."* — permissive, NO ShareAlike, attribution not required (we credit voluntarily in
  `/creditos` + `ATTRIBUTION.md`).
- **Used by:** `scripts/ingest/glyphwiki_strokes.py` → `kanji_stroke_line` table → `corpus/strokes/lines_*.json`
  (per-stroke centerlines for the pen+ball stroke animation). Only kanji whose derived stroke count matches
  KANJIDIC (`count_match=1`) are exported; the rest keep the Kanji Alive outline fallback.
- Raw files are git-ignored; this MANIFEST is the tracked record.
