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
  `gloss` re-authoring in progress), so our shipped glosses are our own work, **not** a derivative of the
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

### Frequency (still to add if used)
- A CC-licensed frequency list — license to be verified and recorded here + in `dataset_source` before ingest.

---

_Last updated: P0 (2026-06-13). Update this file whenever a source is added, removed, or its license confirmed._
