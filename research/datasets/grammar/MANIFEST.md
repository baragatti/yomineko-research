# Grammar Points Dataset — Provenance Manifest

**File:** `grammar_points.json`
**Built:** 2026-06-13 via `_build_grammar_points.mjs` (self-contained fetch + parse + reconcile)
**Scope:** JLPT **N5** and **N4** grammar-point membership (which point belongs to which level).

## What was recorded vs. what was NOT

- **Recorded (factual membership only):** grammar-point names/patterns (Japanese form, e.g. `〜てください`, `たい`, `なければならない`), short romaji/English labels, and which source lists each point at which level.
- **NOT recorded / NOT copied:** prose explanations, grammatical descriptions, example sentences, exercises, or any other expressive content from any source. Grammar-point names and level membership are short factual labels and list facts, not protected expression. All explanations for the course are authored independently.

## Reconciliation method

1. Each source's N5 and N4 grammar list was fetched and the **point name/pattern** extracted (HTML table cells for JLPT Sensei; grammar-card titles for Bunpro; decoded PDF text for Tanos).
2. Each pattern was normalized to a canonical match-key (strip `〜`/`～`/`・`/`/`, furigana parentheses, conjugation scaffolding like "Verb +", circled-number variants `①②③`, and trailing polite endings `です`/`ます`/`だ`; a small kanji→kana alias map merges e.g. `前に`↔`まえに`).
3. Equivalent points across sources were merged into ONE entry with a combined `level_sources` map.
4. `level` = the **earliest** (lowest-difficulty) JLPT level any source assigns the point. N5 is earlier than N4, so if any source lists a point at N5 it is recorded as N5.

Note on granularity: Bunpro decomposes some single grammar points into multiple sub-steps (e.g. `ている①②③`, separate verb-conjugation atoms, demonstratives これ/それ/あれ), so the deduplicated union is larger than any single source's count. This is the intended "capture the union, deduplicated" behavior.

## Sources cross-referenced (≥3)

| Source | URL | License / provenance note |
|---|---|---|
| **JLPT Sensei — N5 grammar list** | https://jlptsensei.com/jlpt-n5-grammar-list/ | Educational reference site. Only grammar-point names + level membership extracted (table cells). No explanations or examples copied. © JLPTsensei.com; used as a factual membership reference only. |
| **JLPT Sensei — N4 grammar list** | https://jlptsensei.com/jlpt-n4-grammar-list/ | As above. |
| **Bunpro — Grammar library (JLPT5 view)** | https://bunpro.jp/grammar_points?level=JLPT5 | Single page enumerates all levels with per-card N5/N4 lesson tags; we filtered to N5- and N4-tagged cards and took only the card title (the point name). No paid/SRS content, explanations, or examples copied. © Bunpro; used as a factual membership reference only. |
| **Bunpro — Grammar library (JLPT4 view)** | https://bunpro.jp/grammar_points?level=JLPT4 | Same underlying catalog page as the JLPT5 view; listed for completeness. |
| **Tanos / Jonathan Waller — JLPT N5 grammar list (PDF)** | http://www.tanos.co.uk/jlpt/jlpt5/grammar/GrammarList.N5.pdf | Long-standing community JLPT resource by Jonathan Waller (tanos.co.uk). PDF text decoded (FlateDecode + ToUnicode CMap); only the grammar-pattern names extracted. No explanatory content present/copied. Free community reference; used for factual membership cross-check. |
| **Tanos / Jonathan Waller — JLPT N4 grammar list (PDF)** | http://www.tanos.co.uk/jlpt/jlpt4/grammar/GrammarList.N4.pdf | As above. |

### Cross-check sources (canonical naming/coverage, not enumerated into the dataset)

- **Tae Kim — Guide to Japanese Grammar:** https://guidetojapanese.org/learn/grammar — used informally to sanity-check canonical pattern naming and coverage.
- **Imabi:** https://imabi.org/ — used informally for the same cross-check.

## Field schema (`grammar_points.json`)

Each array element:

```json
{
  "key": "te-form",
  "pattern": "〜て",
  "label": "te-form (connective)",
  "level": "n5",
  "level_sources": { "jlptsensei": "n5", "bunpro": "n5", "tanos": "n5" },
  "also_known_as": ["te form", "-te form"]
}
```

- `key` — stable slug (romaji-derived).
- `pattern` — the Japanese pattern/form (tilde-marked variant preferred when available).
- `label` — short English/romaji label.
- `level` — reconciled earliest level (`n5` | `n4`).
- `level_sources` — per-source level as listed by that source.
- `also_known_as` — alternate spellings/romaji collected during the merge.

## Counts (as built 2026-06-13)

- **Total points:** 363 — **N5:** 150, **N4:** 213.
- **Per-source raw counts:** JLPT Sensei N5 84 / N4 132; Bunpro N5 124 / N4 183; Tanos N5 42 / N4 53.
- **Agreed by ≥2 sources:** 156. **Single-source:** 207 (mostly Bunpro fine-grained sub-points).
- **Cross-source level disagreements:** 11, each resolved to the earliest (N5) level — see below.

## Known level disagreements (point listed N5 in one source, N4 in another → recorded as N5)

`でも`, `〜がほしい`, `方 (かた)`, `な` (sentence-ending), `〜ないで`, `〜なくてもいい`, `〜にする`, `〜てある`, `て/で` (te-form), `とき`, `って` — all reconciled to **n5** (earliest source wins).
