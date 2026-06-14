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
- **Commercial note:** ShareAlike — a derivative database may need to be shared under the same licence. ⚠ owner
  legal decision (PLAN_REVIEW open Q1 / D13). Keep the derived DB layer shareable; sell the original courseware.

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

### Community JLPT level lists (consensus level tags — §1.5)
- **kanji.json** — `davidluzgouveia/kanji-data` (kanji + reconstructed `jlpt_new` levels). License: **verify on
  the repo before shipping.**
- **elzup/jlpt-word-list** — N5/N4 vocabulary lists. License: **verify on the repo before shipping.**
- _(P2 will add ≥1 more vocab list and ≥1 more kanji list for the ≥3-list reconciliation.)_
- **Note:** JLPT publishes no official lists; all level tags are community consensus, carried with
  `level_confidence` / `level_agreement` / `level_sources`. Not authoritative.

### Tooling / libraries (no content, but recorded)
- `jmdict-simplified` (MIT) — JSON conversion tooling.
- **SudachiPy** + **SudachiDict** (Apache-2.0) — morphological analysis (P5).
- **jaconv** (MIT) — kana↔romaji conversion (romaji population).

### Pitch accent & frequency (to be added in P1/P2)
- Pitch-accent dataset (kanjium/OJAD-derived) and a CC-licensed frequency list — **license to be verified and
  recorded here + in `dataset_source` before ingest.**

---

_Last updated: P0 (2026-06-13). Update this file whenever a source is added, removed, or its license confirmed._
