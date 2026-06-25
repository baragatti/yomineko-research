# N2 / N1 kanji + vocab banks — methodology & scope

> **Owner directive (2026-06-25):** add N2 and N1 **to the kanji/vocab banks only** — "the kanjis that make
> sense, not ancient, non-used, non present in exams or life ones." **No sentences, no grammar, no deep
> explanation, no lessons.** Just the minimum bank entries needed for FSRS study. This doc records how the
> "kanjis that make sense" filter was defined and sourced, so the decision is auditable.

Built by `scripts/ingest/ingest_n2_n1.py` (additive + idempotent; never touches N5/N4/N3 rows), exported by
`scripts/export/export_corpus.py` (N2/N1 are **bank-only levels** — kanji + vocab files only).

## The "modern / used / exam-relevant" filter

### Kanji — the Jōyō gate (the decisive filter)
A kanji is eligible **only if it is Jōyō** — KANJIDIC `grade` 1–8 (the official 2,136 *jōyō kanji*, the
Japanese government's 2010 regular-use set: the characters taught in school and used in newspapers, public
signage, and exams). This single gate is what removes exactly what the owner asked to exclude:

| KANJIDIC grade | meaning | decision |
|---|---|---|
| 1–6 | kyōiku (elementary) | **include** (Jōyō) |
| 8 | secondary-school Jōyō | **include** (Jōyō) |
| 9–10 | jinmeiyō (name-only kanji) | **exclude** — used in personal names, not general/exam vocab |
| (none) | not Jōyō, not jinmeiyō | **exclude** — rare / archaic / specialist |

On top of the gate, a kanji must also be listed N2 or N1 by a community JLPT lineage. **4 independent lineages**
vote N2-vs-N1 (same families used for N5–N3, see `sources.md`):
davidluzgouveia `jlpt_new`, AnchorI `jlpt`, kanjiapi.dev `jlpt-2/jlpt-1`, Bluskyo/Tanos.
Level = majority vote (N2 wins ties); `level_confidence` = agreement/4; `level_agreement` = e.g. `4/4`.

**Result:** union of the 4 lists = 1,762 chars → **1,514 pass the Jōyō gate** (380 N2 + 1,134 N1); **248
non-Jōyō excluded** (sampled: 爾蘭凪嘉茜澪旭翔遼桐 — confirmed name/rare kanji). **1,352/1,514 have full 4/4
agreement; 1,417/1,514 carry a newspaper frequency rank** (extra "actually used" signal). Total leveled kanji
across all levels = 2,131 ≈ the full Jōyō set.

### Vocab — JLPT exam lists, JMdict-matched, non-archaic
JLPT N2/N1 vocab lists are **by definition exam vocabulary** (modern, in-use), so the filter is lighter:
union of 3 open lists (jlpt-vocab-api, Bluskyo/Tanos, open-anki) → matched to **JMdict** (the entry supplies
readings, forms, POS, and the English glosses) → **insert only entries not already taught at N5–N3** → **drop
any entry whose *primary* JMdict sense is archaic/obsolete** (misc `arch`/`obs`/`obsc`). Added **1,768 N2 +
2,678 N1** (638 unmatched-in-JMdict, 1,518 already-taught-earlier, 0 archaic — exam lists were already clean).

Per the relaxed spec §1.5 (single open lineage = Tanos/Waller for vocab; consensus-fuzzy N2/N1 boundary for
kanji), **every N2/N1 entry is `needs_review = 1`** with low `level_confidence`.

## Scope — what was and was NOT built
- **Built (Layer A):** kanji (character, strokes, grade, radical, frequency, readings, **English meanings**) and
  vocab (headword, kana, romaji, forms, POS, **English glosses** from JMdict, kanji↔vocab links). Browsable in
  the prototype under the N2/N1 filter chips; ready to seed FSRS cards.
- **Deliberately NOT built:** sentences (no N2/N1 dissected bank), grammar points, lessons/topics/course,
  conjugation tables, mnemonics, or any Layer-C pedagogy. (`SELECT … WHERE level IN ('n2','n1')` on
  `sentence`/`grammar_point` = 0.)
- **pt-BR meanings:** **deferred.** N2/N1 entries currently carry only the Layer-A **English** meaning/gloss
  (in the locale-object `en` key). The prototype browse falls back pt-BR → en, so meanings render today. A
  future AI pass can add pt-BR glosses (tracked in `product_roadmap.md`), consistent with the
  English-preservation plan in [`i18n.md`](i18n.md).

## Reproducibility
Raw lists are git-ignored; URLs + SHA256 + licenses are in `research/datasets/jlpt/MANIFEST.md` and
`design/sources.md`. All sources are MIT or CC-BY-SA (commercial-use OK; see `ATTRIBUTION.md`). Re-run:
`python scripts/ingest/ingest_n2_n1.py && python scripts/export/export_corpus.py`.
