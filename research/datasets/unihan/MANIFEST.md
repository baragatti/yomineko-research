# Unihan — dataset manifest (provenance)

- **Source:** Unicode Character Database — **Unihan** (https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip),
  file `Unihan_IRGSources.txt`, field **`kRSUnicode`** (Kangxi radical + residual stroke count).
- **Used for:** the authoritative, PERMISSIVE **Kangxi radical** of each kanji (replaces reliance on CC BY-SA
  KRADFILE for the radical — see `design/license_audit.md` D-LIC-2).
- **License:** **Unicode License v3** — an OSI-approved, MIT-style permissive licence: use/copy/modify/
  distribute **and sell** without restriction, **NO ShareAlike / NO copyleft / NO NonCommercial**. Attribution
  via the standard Unicode data-files notice.
- **Attribution text (to display):** *"Radical data © Unicode, Inc., from the Unicode Character Database
  (Unihan), used under the Unicode License."*
- **Files fetched (2026-06-26):** `Unihan.zip` (raw, gitignored). `kRSUnicode` covers 2,130/2,131 of our
  leveled kanji; agrees with our existing `kangxi_radical` on 2,118/2,130 (we adopt Unihan's value as the
  authoritative permissive source).
- **NOTE:** Unihan has **no full IDS / multi-component** decomposition (only the radical). Full component
  decomposition stays as uncopyrightable FACTS (credited to EDRDG/KRADFILE); a fully-independent permissive
  component set would come from GlyphWiki (KAGE) — optional enhancement, see STATE backlog.
