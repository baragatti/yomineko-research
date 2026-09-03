# Sources & licenses (provenance)

> Versions + SHA256 live in `research/datasets/*/MANIFEST.md`. This file records **license + commercial-use
> facts** for the owner's decision (PLAN_REVIEW D13 / open question #1). **License interpretation is the owner's
> responsibility — these are the facts to decide on.** Full attributions go in `ATTRIBUTION.md` (P0). Verify
> license currency at build time (§3); captured 2026-06-13.

| Source | Used for | Version fetched | License | Commercial-use note |
|--------|----------|-----------------|---------|---------------------|
| **JMdict** (via jmdict-simplified) | vocab backbone | 3.6.2+20260608 | EDRDG — **CC BY-SA 4.0** | **ShareAlike**: a derived DB may carry SA obligations. Attribution to EDRDG required. ⚠ owner legal review. |
| **KANJIDIC2** (via jmdict-simplified) | kanji backbone | 3.6.2+20260608 | EDRDG — **CC BY-SA 4.0** | Same as JMdict. **Do NOT use its `jlpt` field** as modern level (§1.5). |
| **Kradfile / Radkfile** (via jmdict-simplified) | radical decomposition | 3.6.2+20260608 | EDRDG — **CC BY-SA** | Same family; attribution + SA. |
| jmdict-simplified tooling | JSON conversions | 3.6.2 | MIT | Tooling MIT; the *data* keeps EDRDG terms above. |
| **KanjiVG** | stroke order + components | r20250816 | **CC BY-SA 3.0** | **ShareAlike**: redistributing derivative SVGs carries SA. Storing a per-kanji ref is low-risk; shipping modified SVGs is the concern. ⚠ owner review. |
| **Tatoeba** (jpn/eng/por sentences, links, audio) | example sentences (Japanese = Layer A) | export 2026-06 | sentences **CC BY 2.0 FR**; some audio varies | **Attribution required** (per-sentence credit / Tatoeba). Generally commercial-OK *with* attribution. Audio licenses vary by contributor — check per clip if used. **Biggest real source.** |
| **JEC Basic Sentence Data** (ja+en+zh) | 2nd real example-sentence source (ja = Layer A; en = cross-check) | v1-2 @ 2026-06-15 | **CC BY 3.0 Unported** | Commercial + redistribute OK, **NO share-alike**. Dual attribution: Kurohashi-Kawahara Lab (Kyoto U.) + NICT MASTAR. 4,729 usable. `raw_jec` / `source=jec:#NNNN`. Cleanest permissive sentence source. |
| **Kanji Alive** (`kanjialive/kanji-data-media`) | kanji stroke order — **1,233 shipped records** in `corpus/strokes/n5..n1.json` (`source=kanjialive`) | fetched 2026-06-26, no upstream tag pinned | **CC BY 4.0** — *as recorded, not verified from a bundled licence file* (⚠ see note below) | Commercial + redistribute OK, **NO share-alike**. Attribution + "changes were made" indication required (our records are an adaptation). Replaced CC BY-SA KanjiVG for shipped stroke data (D-LIC-2). |  Upstream licence archived 2026-09-02: `research/datasets/kanjialive/LICENSE.md` (970 bytes, SHA256 `abc0a00defc51659a8b5d58d80aa9a6c443b5bbefed617dd989cf601a0f5f657`), which itself declares CC BY 4.0 — the earlier caveat that the licence was recorded from an unarchived reading is closed.
| **strokesvg / Klee One** (`zhengkyl/strokesvg`) | kana stroke order — **162 shipped records** in `corpus/strokes/kana.json` (`source=strokesvg`, 160 parsed + 2 derived) | fetched 2026-06-26, no upstream tag pinned (`package.json` v1.0.0) | SVG glyph data **SIL OFL 1.1** (from Klee One); all other repo files **MIT** — verified from the bundled `LICENSE` | Commercial-OK; OFL copyleft is **font-scoped, not app-scoped**. May be bundled/sold *with* software, never sold by itself; **each copy must carry the OFL text + both copyright lines** (© 2024 Kyle, MIT; © 2020 The Klee Project Authors, OFL). ⚠ upstream `package.json` wrongly says `ISC`. |
| _(rejected, deep research 2026-06-15)_ JESC / OpenSubtitles / JParaCrawl / KFTT | — | — | JESC **CC BY-SA 4.0** (+ upstream fan-subtitle copyright); OpenSubtitles (no text rights); JParaCrawl (non-commercial); KFTT **CC BY-SA** + encyclopedic register | **Not bundled, not used as AI seeds** (see ATTRIBUTION → SOURCE LICENSING POLICY). Tanaka Corpus = Tatoeba's ancestor → redundant. |
| **kanji.json** (davidluzgouveia/kanji-data) | kanji JLPT levels (1 of ≥3) | master @ fetch | repo license — **verify** | Community reconstruction; confirm repo license before shipping. Level data is consensus, not authoritative (§1.5). |
| **elzup/jlpt-word-list** (n5/n4) | vocab JLPT levels (1 of ≥3) | master @ fetch | repo license — **verify** | Same: verify license; add ≥1 more list in P2 (D2). |
| _(P1/P2 to add)_ pitch-accent data (kanjium/OJAD-derived) | pitch (D6) | — | — | Verify license before ingest. |
| _(P1 to add)_ frequency list (CC-licensed) | sequencing (D8/§3.5) | — | — | Pick a CC/CC0 source; record here. |
| _(P2 to add)_ ≥1 more vocab list + ≥1 more kanji list | level reconciliation (D2) | — | — | For the ≥3-list policy (§1.5). |

## Stroke-order sources — URLs, dates, SHA256 (added W42, 2026-09-02)
The table above has no checksum column; these are the two stroke datasets' exact figures, **measured on disk
2026-09-02**, not copied from a manifest. Full attribution text: `ATTRIBUTION.md`.

- **Kanji Alive** — https://kanjialive.com · https://github.com/kanjialive/kanji-data-media · fetched 2026-06-26
  - `kanji_strokes.zip` — 12,977,338 bytes · `ad1327b57ded0db7a4d325b83d63bbd4f5af6379f22db5e2b020ea869b1deb71`
  - `ka_data.csv` — 765,855 bytes · `7e7f7098609bff4c26c01772157ea507c9bc09669ce777dbd62bc21d3e135d80`
  - ⚠ **Licence evidence gap:** no upstream licence text is archived in this repo — no licence file under
    `research/datasets/kanjialive/`, none among the 11,933 members of `kanji_strokes.zip`. The CC BY 4.0 claim
    rests only on our own `MANIFEST.md` ("Verified from repo `LICENSE.md`, 2026-06-26"), the `license` value the
    ingest script stamps on each row, and `design/license_audit.md` D-LIC-2. **Close it by archiving the
    upstream `LICENSE.md` beside the dump with its SHA256.**
- **strokesvg / Klee One** — https://github.com/zhengkyl/strokesvg · fetched 2026-06-26
  - `dist/**/*.svg` — 160 files (79 hiragana + 81 katakana) · aggregate SHA256 over sorted `relpath + bytes`
    `7d1deb8f32d8f4b3856bbab6f10a073293f223b3bebfe9e29096a25eef78b27c` (no per-file checksums were ever recorded)
  - `LICENSE` — 5,799 bytes · `034fbffd797849ae2717ae2f167315a59b0fc65b5c8339771e100341223fb881` — carries the
    NOTICE, the MIT text (© 2024 Kyle) and the full SIL OFL 1.1 text (© 2020 The Klee Project Authors,
    https://github.com/fontworks-fonts/Klee). **No Reserved Font Name is declared.**

> **KanjiVG status (2026-09-02):** the CC BY-SA 3.0 row above is now the *only* SA stroke source, and nothing
> derived from it ships except the `kanjivg_ref` id. See the open D9 block in
> `research/reports/w42_attribution_report.md`.

## N2 / N1 bank lists (added 2026-06-25)
Bank-only N2/N1 kanji+vocab extension (`design/n2_n1_bank.md`). **Same source repos already used for N5–N3**,
extended to the N2/N1 levels — no new licenses introduced:
- KANJI: davidluzgouveia/kanji-data (MIT), AnchorI/jlpt-kanji-dictionary (MIT), kanjiapi.dev (CC-BY-SA-4.0,
  EDRDG-derived), Bluskyo/JLPT_Vocabulary (MIT; tanos.co.uk/J.Waller). "Modern/used" gate = KANJIDIC **Jōyō
  grade 1–8** (excludes jinmeiyō + rare/archaic). Level facts are consensus, `needs_review` (§1.5 relaxed).
- VOCAB: wkjagt/jlpt-vocab-api (MIT), Bluskyo/Tanos (MIT), jamsinclair/open-anki-jlpt-decks (MIT); matched to
  **JMdict** (readings/forms/POS/English glosses; EDRDG CC-BY-SA). Archaic/obsolete primary senses dropped.

URLs + SHA256: `research/datasets/jlpt/MANIFEST.md`. Commercial-use posture unchanged from N5–N3 (see below).

## Headline for the owner
The two **ShareAlike** sources (EDRDG JMdict/KANJIDIC2/Krad/Radk and KanjiVG) are the only real commercial-use
question. Tatoeba is fine with attribution. A common strategy: keep the derived linguistic **database**
shareable (honoring SA) while the **courseware/app** (original pt-BR lessons, exercises, UI) is your own product
— but this is a legal call for you to confirm. See PLAN_REVIEW open question #1.
