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
| _(rejected, deep research 2026-06-15)_ JESC / OpenSubtitles / JParaCrawl / KFTT | — | — | JESC **CC BY-SA 4.0** (+ upstream fan-subtitle copyright); OpenSubtitles (no text rights); JParaCrawl (non-commercial); KFTT **CC BY-SA** + encyclopedic register | **Not bundled, not used as AI seeds** (see ATTRIBUTION → SOURCE LICENSING POLICY). Tanaka Corpus = Tatoeba's ancestor → redundant. |
| **kanji.json** (davidluzgouveia/kanji-data) | kanji JLPT levels (1 of ≥3) | master @ fetch | repo license — **verify** | Community reconstruction; confirm repo license before shipping. Level data is consensus, not authoritative (§1.5). |
| **elzup/jlpt-word-list** (n5/n4) | vocab JLPT levels (1 of ≥3) | master @ fetch | repo license — **verify** | Same: verify license; add ≥1 more list in P2 (D2). |
| _(P1/P2 to add)_ pitch-accent data (kanjium/OJAD-derived) | pitch (D6) | — | — | Verify license before ingest. |
| _(P1 to add)_ frequency list (CC-licensed) | sequencing (D8/§3.5) | — | — | Pick a CC/CC0 source; record here. |
| _(P2 to add)_ ≥1 more vocab list + ≥1 more kanji list | level reconciliation (D2) | — | — | For the ≥3-list policy (§1.5). |

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
