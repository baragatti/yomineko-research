# §1.7 cross-cutting graph query tests

_Acceptance #10. The four spec queries are run VERBATIM — every clause of the spec sentence is applied — against the exported JSON under `corpus/` (never `db/corpus.sqlite`). A query that returns zero rows FAILS. A query listed in the WAIVERS table of `scripts/validate/graph_queries.py` is allowed to fail with its reason recorded; if it starts returning rows, the gate fails so the waiver is removed._

## Q1 — All N5 sentences containing a godan verb from the *daily-routine* family **and** the を particle.

**0 rows.**

**WAIVED** — 0 rows is the CORRECT answer today, and it is the defect: the 28 semantic_field families hold no verbs, so (grp:godan ∩ daily-routine) is empty by construction — build_families_full.py fills a semantic field only with vocab left over after the conjugation_class assignment, and every verb is already in a conjugation class. Finding G03/G04; STATE.md line 1927 'P4b — full families' owns the rebuild of the family layer over n5–n3. Delete this waiver once a semantic field can contain a verb.

## Q2 — Every vocab item using the kun-reading た.べる of 食, with its dissected sentences.

**2 rows.**
- 食べる (vocab:1358280) — 101 dissected sentences
- 食べ物 (vocab:1358340) — 5 dissected sentences

PASS

## Q3 — All members of the 言-component kanji family across N5–N4, ordered by frequency.

**7 rows.**
- 言 (n5, freq 83)
- 話 (n5, freq 134)
- 計 (n4, freq 228)
- 語 (n5, freq 301)
- 説 (n4, freq 326)
- 試 (n4, freq 392)
- 読 (n5, freq 618)

PASS

## Q4 — Every grammar point that contrasts with は, with example sentences.

**0 rows.**

**WAIVED** — The relation TYPE is not exported. grammar.related is a bare list of keys (wa-topic-marker -> ['ga']) with no 'contrast'/'synonym'/'confusable' label, and db/corpus.sqlite's grammar_related.relation is not carried into corpus/grammar/*.json, so the §1.7 clause 'that contrasts with は' cannot be evaluated — every candidate is filtered out for having no relation at all. Finding G04 (family/relation edges are write-only). Delete this waiver once export_corpus.py emits the relation.

