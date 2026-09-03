# ATTRIBUTION

> **Owner directive (2026-06-13):** proceed using these sources, but **annotate provenance meticulously** so we
> can later remove a source or give proper credit. This file is the human-readable attribution record; the
> machine-readable provenance lives in the DB (`dataset_source` table + every content row's `source` column) and
> in `research/datasets/*/MANIFEST.md` (versions + SHA256). License facts: [`design/sources.md`](design/sources.md).
> **License interpretation is the owner's responsibility.** Verify license currency at build time (spec §3).

## How provenance is tracked (so any source can be removed/credited later)
- Every corpus row carries a **`source`** string (e.g. `jmdict:1234`, `kanjidic2:食`, `tatoeba:7421`,
  `ai_generated`) and a **`layer`** (A authoritative / B derived-and-verified / C pedagogy).
- The **`dataset_source`** table records each dataset's name, version, URL, license, commercial note, SHA256.
- Raw downloads are git-ignored; **`research/datasets/<group>/MANIFEST.md`** holds the exact version + checksum.
- → To drop a source later: delete/replace rows whose `source` matches it. To credit it: this file + the
  in-app credits screen cite it.

---

## Required attributions

### EDRDG — JMdict, KANJIDIC2, KRADFILE/RADKFILE
- **What:** vocabulary (JMdict), kanji data (KANJIDIC2), radical decomposition (KRAD/RADK), via the
  `jmdict-simplified` JSON conversions (tooling © Stichoza/scriptin, MIT).
- **Owner:** Electronic Dictionary Research and Development Group (EDRDG), Monash University.
- **License:** **Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0).**
- **Attribution text (to display):** *"This product uses the JMdict, KANJIDIC2 and KRADFILE/RADKFILE
  dictionary files, which are the property of the Electronic Dictionary Research and Development Group, and are
  used in conformance with the Group's licence."* (https://www.edrdg.org/edrdg/licence.html)
- **Commercial note:** ShareAlike. **Owner ruling 2026-06-26 (see `design/license_audit.md`): go fully
  permissive.** We use EDRDG only for **non-copyrightable FACTS** (kanji readings 音/訓, stroke counts, radicals,
  POS, the kanji/word inventory) — kept under this attribution. The copyrightable **definitions** were
  **RE-AUTHORED independently** (kanji `meanings` regenerated from facts + verifier-checked, 2026-06-26; vocab
  `gloss` re-authored 2026-06-26 — all 7,401 vocab), so our shipped glosses are our own work, **not** a derivative of the
  CC BY-SA dictionary text. The **Kangxi radical** is now sourced from the permissive **Unicode Unihan**
  (`kRSUnicode`, Unicode License — see `research/datasets/unihan/MANIFEST.md`). The multi-component
  **decomposition** (`kanji_component`) is uncopyrightable FACT (which sub-parts a character contains) — kept
  under EDRDG attribution; ShareAlike does not bind facts. A fully-independent component set (GlyphWiki/IDS) is
  an optional future enhancement.

### Unicode — Unihan (radical)
- **What:** the Kangxi radical of each kanji (`kRSUnicode`). **License: Unicode License v3** (MIT-style,
  permissive, NO ShareAlike). Attribution: *"Radical data © Unicode, Inc. (Unihan), used under the Unicode
  License."* See `research/datasets/unihan/MANIFEST.md`.

### KanjiVG
- **What:** per-kanji stroke order + component grouping (SVG / XML).
- **Owner:** Ulrich Apel / KanjiVG project.
- **License:** **Creative Commons Attribution-ShareAlike 3.0 (CC BY-SA 3.0).**
- **Attribution text:** *"Stroke order data from the KanjiVG project © Ulrich Apel, licensed CC BY-SA 3.0."*
  (https://kanjivg.tagaini.net/)
- **Commercial note:** ShareAlike applies to redistributed/derivative SVGs. Storing a per-kanji reference is
  low-risk; shipping modified SVGs carries SA obligations. ⚠ owner legal decision.

### Tatoeba
- **What:** human-written Japanese example sentences + translation links + some audio.
- **Owner:** the Tatoeba Project and its contributors.
- **License:** sentences **CC BY 2.0 FR**; audio licenses vary by contributor.
- **Attribution text:** *"Example sentences from the Tatoeba Project (https://tatoeba.org), © its contributors,
  licensed CC BY 2.0 FR."* (Per-sentence author credit is available via Tatoeba and should be preserved where
  feasible.)
- **Commercial note:** generally commercial-OK **with attribution**. Check audio per-clip license before using
  any specific audio. The Japanese sentence text is Layer A; our pt-BR translation of it is our own Layer B.

### JEC Basic Sentence Data (second real sentence source — added 2026-06-15)
- **What:** 5,304 basic Japanese sentences with **manual** English + Chinese translations (we load ja+en;
  4,729 after dropping X/Y/〜 placeholder templates). Stored in `raw_jec`; `source` = `jec:#NNNN`.
- **Owner:** Kyoto University **Kurohashi-Kawahara Lab** (Japanese) + **NICT MASTAR** Multilingual Translation
  Lab (English/Chinese translations).
- **License:** **CC BY 3.0 Unported** — commercial use AND redistribution permitted with attribution, **no
  share-alike**. (Cleanest permissive sentence source we use.)
- **Attribution text:** *"Basic sentences from the JEC Basic Sentence Data, © Kurohashi-Kawahara Lab (Kyoto
  University) and NICT MASTAR Project, licensed CC BY 3.0."* (https://nlp.ist.i.kyoto-u.ac.jp/EN/)
- **Commercial note:** commercial-OK with the dual attribution above. Basic (non-conversational) register; we
  mine i+1 sentences within the known-set. JEC's English is kept as the `en` cross-check; our pt-BR is Layer B.

### SOURCE LICENSING POLICY (sentence text — owner decision 2026-06-15)
We **bundle only permissive real text**: **CC BY / CC0** sources (Tatoeba CC BY 2.0 FR; JEC Basic CC BY 3.0),
always with attribution. We do **NOT** bundle **CC BY-SA** sentence corpora or copyright-murky/upstream
material (JESC, OpenSubtitles, KFTT, JParaCrawl…) — **and do NOT use them even as AI generation seeds**, since
a close AI paraphrase is still a derivative work and does not reliably clear share-alike or upstream copyright.
**AI-generated sentences are clean-room**: composed from our own known-set (the permissive registries), never
derived from a restricted text. (Note: JMdict/KANJIDIC/KanjiVG/kanjium are CC BY-SA but are *dictionary facts*,
not bundled prose — their SA handling is the separate owner legal call noted above.)

### Community JLPT level lists (consensus level tags — §1.5)
P2 added the extra lists for the ≥3-list reconciliation; all are recorded with URL + SHA256 + license in
[`research/datasets/jlpt/MANIFEST.md`](research/datasets/jlpt/MANIFEST.md). Full set actually used in the data:

**VOCAB level lists (4 independent):**
- **elzup/jlpt-word-list** — N5/N4 vocabulary CSVs.
- **wkjagt/jlpt-vocab-api** — JLPT Vocab API (N5=662, N4=632). **MIT.**
- **jamsinclair/open-anki-jlpt-decks** — Open Anki JLPT decks (N5=718, N4=668). **MIT.**
- **Bluskyo/JLPT_Vocabulary** — parsed vocab CSVs (N5=700, N4=649). **MIT**; upstream data from
  **tanos.co.uk (Jonathan Waller's JLPT Resources)**.

**KANJI level lists (4 independent):**
- **davidluzgouveia/kanji-data** — kanji + reconstructed `jlpt_new` levels. **MIT.**
- **kanjiapi.dev** — `/v1/kanji/jlpt-5|jlpt-4` endpoints (N5=79, N4=166). **CC BY-SA 4.0** (built on
  JMdict/KANJIDIC — same EDRDG SA family).
- **AnchorI/jlpt-kanji-dictionary** — `jlpt` field per kanji. **MIT.**
- **Bluskyo/JLPT_Vocabulary** — parsed kanji CSVs (N5=79, N4=166). **MIT**; upstream tanos.co.uk / J. Waller.

- **Note:** JLPT publishes no official lists; all level tags are community consensus, carried with
  `level_confidence` / `level_agreement` / `level_sources`. Not authoritative. The KANJIDIC2 built-in `jlpt`
  field is NOT used (old pre-2010 scale, §1.5).

### Tooling / libraries (no content, but recorded)
- `jmdict-simplified` (MIT) — JSON conversion tooling.
- **SudachiPy** + **SudachiDict** (Apache-2.0) — morphological analysis (P5).
- **jaconv** (MIT) — kana↔romaji conversion (romaji population).

### Pitch accent — kanjium
- **What:** word pitch-accent positions (mora indices), ingested into `vocab_pitch` (data only; audio deferred).
- **Owner:** mifunetoshiro/kanjium project.
- **License:** **CC BY-SA 4.0** (ShareAlike — same commercial note as the other SA sources). Source file:
  `data/source_files/raw/accents.txt`. URL: https://github.com/mifunetoshiro/kanjium
- **Attribution text:** *"Pitch-accent data from the kanjium project (© its contributors), CC BY-SA 4.0."*
- Matched 1,221/1,359 N5+N4 vocab (89.8%).
- **Owner ruling 2026-06-26 (D-LIC-3, see `design/license_audit.md`):** a word's pitch-accent pattern (mora
  index where the pitch drops) is a **non-copyrightable linguistic FACT** — same class as a reading or stroke
  count. We therefore **keep `vocab_pitch` under this attribution** (ShareAlike does not bind facts); no
  re-source needed. No clearly-permissive bulk pitch source exists (OJAD research-use, NHK proprietary), so
  re-sourcing would trade one credited fact-source for none.

### Kanji Alive — kanji stroke order (static step outlines)

Upstream licence archived 2026-09-02: `research/datasets/kanjialive/LICENSE.md` (970 bytes, SHA256 `abc0a00defc51659a8b5d58d80aa9a6c443b5bbefed617dd989cf601a0f5f657`), which itself declares CC BY 4.0 — the earlier caveat that the licence was recorded from an unarchived reading is closed.
- **What:** per-kanji stroke-order drawing data. Raw source = cumulative filled-outline step SVGs
  (`kanji_strokes.zip`, `{kname}_{N}.svg`) + `ka_data.csv` (kanji↔kname, stroke count, radical). Adapted into
  our own schema (`kanji_stroke` → `corpus/strokes/n5..n1.json`) as `{viewbox, transform, steps:[path_d,…]}`.
  **We do not ship the raw Kanji Alive files.**
- **Ships:** **1,233 records** measured over `corpus/strokes/` — N5 103, N4 177, N3 350, N2 357, N1 246; every
  one carries `source: "kanjialive"`, `license: "CC-BY-4.0"`.
- **Owner:** Kanji alive (https://kanjialive.com), repo `kanjialive/kanji-data-media`.
- **License (as recorded, see the evidence caveat below):** **Creative Commons Attribution 4.0 International
  (CC BY 4.0)** — attribution required, **NO ShareAlike**. (The separate *Japanese Radicals* font is Apache 2.0
  and is **not** used.)
- **Attribution text (to display):** *"Kanji stroke-order data © Kanji alive (https://kanjialive.com),
  licensed CC BY 4.0."*
- **Commercial note:** **commercial-OK with attribution, no share-alike, no copyleft on our app.** CC BY 4.0
  permits redistribution of adapted material provided the credit above, a licence link, and an indication that
  changes were made are given — our records ARE an adaptation (re-expressed format), so the credits screen must
  say so, not merely name the source. This is the source that made the stroke layer proprietary-safe (D-LIC-2,
  `design/license_audit.md`); it replaced CC BY-SA KanjiVG for shipped stroke data.
- **⚠ Evidence caveat (W42, 2026-09-02):** **no upstream licence text is archived in this repo** — there is no
  `LICENSE`/`COPYING` file under `research/datasets/kanjialive/`, none inside `kanji_strokes.zip` (11,933
  members, zero licence-named entries), and none anywhere else in the tree. The CC BY 4.0 claim rests on three
  *second-hand, in-repo* records: `research/datasets/kanjialive/MANIFEST.md` ("Verified from repo `LICENSE.md`
  (2026-06-26)"), the `license` value the ingest script stamps on every row
  (`scripts/ingest/kanjialive_strokes.py`), and the D-LIC-2 ruling in `design/license_audit.md`. **To close:**
  archive the upstream `LICENSE.md` beside the dump and record its SHA256.
- **Version / date / checksums (re-verified 2026-09-02):** fetched **2026-06-26**; no upstream commit or tag is
  pinned on disk.
  - `kanji_strokes.zip` — 12,977,338 bytes, SHA256 `ad1327b57ded0db7a4d325b83d63bbd4f5af6379f22db5e2b020ea869b1deb71`
  - `ka_data.csv` — 765,855 bytes, SHA256 `7e7f7098609bff4c26c01772157ea507c9bc09669ce777dbd62bc21d3e135d80`
  - `MANIFEST.md` — SHA256 `2d3d6e3ae373a9f795c3f3444235d7dc96477676e6727b298772b0ebfd5a74bc`

### strokesvg / Klee One — kana stroke order
- **What:** hiragana + katakana stroke-order data. Raw source = `dist/**/*.svg`, whose
  `<g data-strokesvg="strokes">` group holds ordered per-stroke centerline `<path d>` clipped to per-stroke
  shadow outlines. Parsed into our own schema (`kana_stroke` → `corpus/strokes/kana.json`) as
  `{char, viewbox, strokes[], shadows[]}` and animated with a dash-offset pen draw. **We do not ship the raw
  strokesvg files.** Kana only — strokesvg carries no kanji.
- **Ships:** **162 records** measured over `corpus/strokes/kana.json` — 160 parsed from the 160 dist SVGs
  (79 hiragana + 81 katakana) plus **2 derived** (っ and ッ, reusing the つ/ツ glyph, `source` records the
  derivation); all carry `license: "OFL-1.1+MIT"`.
- **Owner:** `zhengkyl/strokesvg` (https://github.com/zhengkyl/strokesvg) — **Copyright (c) 2024 Kyle**; the
  glyph shapes derive from the **Klee One** font, **Copyright 2020 The Klee Project Authors**
  (https://github.com/fontworks-fonts/Klee).
- **License (verified from the bundled `research/datasets/strokesvg/LICENSE`, 5,799 bytes, SHA256
  `034fbffd797849ae2717ae2f167315a59b0fc65b5c8339771e100341223fb881`):** its NOTICE splits the repo in two —
  *"The hiragana/katakana SVG files are derived from the Klee One font which is licensed under the SIL Open
  Font License"* (full **OFL 1.1** text included in that file), and *"All other files are under MIT license"*
  (MIT text included, © 2024 Kyle). **The files we ingested are exactly the SVG half → OFL 1.1 governs our
  kana stroke data**; MIT covers only the build tooling we did not use. **No Reserved Font Name is declared**
  in the bundled OFL copyright line.
- **Attribution text (to display):** *"Kana stroke-order from strokesvg (© 2024 Kyle, MIT), glyph shapes
  derived from the Klee One font © 2020 The Klee Project Authors, licensed under the SIL Open Font License 1.1."*
- **Commercial note:** **commercial-OK, and OFL's copyleft is font-scoped — it does not reach our app.** OFL §2
  permits bundling, redistributing and *selling* the (modified) Font Software **with** software, on condition
  that **each copy carries the copyright notice and the licence text**. OFL §1 forbids selling it *by itself*
  (we don't), and §5 requires modified Font Software to stay under OFL. Since our kana records are a
  re-expression of Klee-One-derived glyph outlines, the conservative reading is that they are a **Modified
  Version of the Font Software**: the practical obligation is that the shipped app **carry the full OFL 1.1
  text plus both copyright lines**, not just a one-line credit — a credits-screen bullet alone does not satisfy
  §2. ⚠ Whether our derived centerline data counts as Font Software is an owner legal call; complying is cheap
  either way. Also note an **upstream inconsistency**: `package.json` declares `"license": "ISC"`, which
  contradicts the repo's own `LICENSE`; the NOTICE is the specific and later statement about the SVG files and
  is what we rely on.
- **Version / date / checksums (measured 2026-09-02):** fetched **2026-06-26**; no upstream commit or tag is
  pinned on disk (`package.json` says `version: 1.0.0`).
  - `dist/**/*.svg` — 160 files (79 hiragana + 81 katakana), aggregate SHA256 over sorted `relpath + bytes` =
    `7d1deb8f32d8f4b3856bbab6f10a073293f223b3bebfe9e29096a25eef78b27c`
  - `LICENSE` — 5,799 bytes, SHA256 `034fbffd797849ae2717ae2f167315a59b0fc65b5c8339771e100341223fb881`
  - `README.md` — SHA256 `108d3b423118519768f9e0a83bb4243ce5d0ec6115fdb595fa7870a80be37cbd`;
    `MANIFEST.md` — SHA256 `db61b8b10efd9e56e83352d3cbd03206a8a09117b0713a1123fd88fe066d65ce`

### GlyphWiki — kanji per-stroke centerlines (stroke animation)
- **What:** per-stroke centerline paths for ALL registry kanji, derived from GlyphWiki **KAGE** glyph data
  (`kanji_stroke_line` → `corpus/strokes/lines_*.json`); powers the pen+ball stroke animation. Kanji Alive
  outlines remain the static fallback.
- **Owner:** GlyphWiki project (glyphwiki.org) and its contributors.
- **License:** GlyphWiki data is **free for any use including commercial, redistribution and modification, no
  ShareAlike** (see https://glyphwiki.org/wiki/GlyphWiki:License — verify currency at build time). Attribution
  not required; we credit voluntarily.
- **Attribution text (voluntary):** *"Kanji stroke-order animation derived from GlyphWiki glyph data
  (glyphwiki.org)."*

### Frequency (still to add if used)
- A CC-licensed frequency list — license to be verified and recorded here + in `dataset_source` before ingest.

---

_Last updated: W42 (2026-09-02) — Kanji Alive and strokesvg/Klee One sections added, record counts measured over
`corpus/strokes/`, checksums re-verified on disk. Previously: P0 (2026-06-13). Update this file whenever a source
is added, removed, or its license confirmed._
