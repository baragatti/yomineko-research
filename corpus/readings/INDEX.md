# corpus/readings — in-lesson reading-practice boxes (our format)

Short reading passages attached to lessons, assembled by **SELECTION** from the verified sentence bank (no generation): real **Tatoeba (CC BY 2.0 FR)** / **JEC (CC BY 3.0)** Japanese, human EN, our re-authored pt-BR, fully dissected. Each box is **i+0** for the lesson it is gated to — every kanji and content word it uses is already in that lesson's `cumulative_known_set` (HARD gate, validated by `scripts/validate/validate_readings.py`). See `design/reading_practice.md`.

Per box: `{slug, level, gated_to_lesson, title, jp, tokens:[{s,r,ro,pos}], translation:{pt-BR,en}, length_band, uses:{kanji,vocab}, source_slugs:[sent:…]}`. `source_slugs` credit the underlying bank sentences (provenance). Layer **B** (derived-and-verified), `needs_review: 1`.

- `n3.json` — 152 boxes
- `n4.json` — 91 boxes
- `n5.json` — 43 boxes
