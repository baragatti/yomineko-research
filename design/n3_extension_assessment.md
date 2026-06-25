# N3 extension assessment

> Engineering plan for extending the corpus + courseware from "zero -> full N5 -> full N4" to include
> full N3. Grounds every recommendation in the existing ingest/reconcile/place/generate/export pipeline.
> Internal prose is English; learner-facing examples are pt-BR. Companion to `sources.md`,
> `STATE.md`, and `YOMINEKO_CORPUS_BUILD_SPEC.md` (especially spec 1.5 consensus rule).

## Verdict

**GO, with two conditions that need explicit owner sign-off before any ingest.** The corpus is
already structurally ready for N3: `level` is data, not structure, and every level-ordering map in
the codebase already enumerates `n3` (e.g. `validate.py` `LEVEL_ORDER` and `integrity_audit.py`
`LV = {pre-n5:1, n5:2, n4:3, n3:4, n2:5, n1:6}`). Adding N3 is inserting rows plus widening a finite
set of hardcoded scope constants, not a schema migration. The data sources exist and are
redistributable for a paid product (with attribution). Example-sentence selection actually gets
*easier* at N3: the in-envelope Tatoeba pool jumps from 16.3% to 52.1% of the Japanese corpus.

The two conditions:

1. **The spec's ">=3 independent community lists" consensus rule (spec 1.5) is not satisfiable from
   open data for N3 vocab or N3 grammar.** Almost every open list traces to one upstream lineage
   (Tanos/Waller). Only N3 *kanji* has a genuine second independent lineage. The rule must be
   formally relaxed for N3 vocab/grammar (downgrade `level_confidence`, force `needs_review`), or a
   proprietary list must be licensed purely as a private third vote (never bundled). This is a
   provenance-contract change, not a silent workaround.

2. **Copyleft exposure widens.** The EDRDG stack (JMdict/KANJIDIC2/Krad/Radk, all CC-BY-SA 4.0) is
   already ingested today at N5/N4, so this risk exists now; N3 only adds more rows. Before bundling
   in a paid product, get a ruling on whether the shipped corpus DB is a ShareAlike "adaptation" and
   keep BY-SA-derived data tables segregated from proprietary Layer-C pedagogy. The candidate new
   source `jkindrix/japanese-language-data` is also CC-BY-SA 4.0 (so avoid it as a data source if you
   want to minimize copyleft, or treat it as reference only).

The N4 -> N3 jump is the single largest per-level kanji jump in the whole JLPT ladder
(+367 kanji, more than doubling cumulative count from 245 to 612), so the *content-authoring* cost
is real and is the dominant line item, not the engineering.

## Scale: what N3 adds

Current corpus scale (N5 + N4): vocab 1359, kanji 253, grammar 364, dissected sentences 4958,
213 lessons. N3 roughly doubles the corpus on the registry side.

| Dimension | N5+N4 now | N3 adds (planned) | Source basis |
|-----------|-----------|-------------------|--------------|
| Kanji | 253 | +367 (-> ~612 cumulative) | davidluzgouveia `jlpt_new` = kanjiapi `jlpt-3`, both 367 (verified identical) |
| Vocab | 1359 | +1800 to +2200 (decision needed) | Tanos lineage: wkei N3=1797, Bluskyo ~1835; migaku target ~3700 cumulative |
| Grammar | 364 | +130 open (compare vs ~180-200 commercial) | jkindrix n3.json=130, hanabira N3=132; JLPTsensei "182", Bunpro 220 (proprietary) |
| Sentences | 4958 | selection-driven; pool of ~89k net-new in-envelope JP | Tatoeba: N3 envelope 52.1% vs N4 16.3% |

Decision required on the N3 vocab target: the open sources disagree by ~20%. Recommend adopting the
**wkei/Tanos new-N3 count (~1797)** as the canonical N3 vocab set (it is the cleanest "new-N3" cut
where N3 < N2, consistent with the test redesign), and explicitly documenting the disagreement rather
than chasing the migaku ~3700-cumulative marketing figure. The open-anki N3=2140 figure is the
old-test Tanos list mechanically split (tagged `JLPT_2 JLPT_3`, producing the implausible N3 > N2)
and should be treated as junk for sizing.

## Open N3 data sources (named, licensed, counted)

All counts verified against the actual repo/file during research. License verdicts are for bundling
in a paid product. "Redistribute" means the data files themselves may be shipped.

### Kanji (the only dimension with genuine consensus)

| Source | N3 count | License | Commercial / redistribute | Notes |
|--------|----------|---------|---------------------------|-------|
| davidluzgouveia/kanji-data (`kanji.json`, field `jlpt_new`) | 367 | MIT (c) 2019 D. Gouveia | Yes / yes, attribute | jlpt_new N5=79 N4=166 N3=367 N2=367 N1=1232 (full 13,108-entry file); already this project's kanji-level source |
| kanjiapi.dev (onlyskin/kanjiapi.dev) `/v1/kanji/jlpt-3` | 367 | MIT | Yes / yes, attribute | Fetched live; exact match to davidluzgouveia. Corroborates (same KANJIDIC2 re-leveling lineage) |
| AnchorI/jlpt-kanji-dictionary | 370 | MIT | Yes / yes | Near-identical (N5=80 N4=170 N3=370); re-verify with authenticated GitHub API |
| Bluskyo `n3_kanji.csv` | 367 | MIT (Tanos-derived) | Yes / yes, attribute Waller upstream | Tanos lineage, agrees at 367 |

**Consensus for N3 kanji is real**: the Tanos lineage (367) and the KANJIDIC2/kanjiapi re-leveling
lineage (367) are genuinely independent and agree exactly. This satisfies a relaxed ">=2 independent
lineages" rule. Caveat (spec 1.5): `jlpt_new` is itself an opaque community re-leveling with no
documented methodology, so its provenance must be recorded as
`level_sources = {davidluzgouveia: n3, kanjiapi: n3, bluskyo: n3}` with `level_confidence` reflecting
two-lineage (not three-list) agreement, not presented as multi-source consensus.

### Vocabulary (single open lineage = Tanos/Waller)

| Source | N3 count | License (repo) | Binding upstream | Bundle verdict |
|--------|----------|----------------|------------------|----------------|
| wkei/jlpt-vocab-api | 1797 | none (all-rights-reserved) | Tanos (CC-BY Waller) | Do NOT bundle the repo; the *data* is Tanos -> re-source from a licensed mirror |
| Bluskyo/JLPT_Vocabulary | ~1835 | MIT wrapper | Tanos (CC-BY Waller) | Bundle OK; attribute Waller (upstream binds, not the MIT wrapper) |
| elzup/jlpt-word-list | Tanos-tagged | MIT wrapper | Tanos (CC-BY Waller) | Already used for N5/N4; same lineage; attribute Waller |
| jamsinclair/open-anki-jlpt-decks (`n3`) | 2140 | MIT (c) 2020 J. Sinclair | Tanos (old-test split) | Junk for N3 sizing (N3 > N2); do not use as the canonical set |

Critical: a repo's own MIT/permissive license covers only its packaging. It cannot relicense the
upstream Tanos/Waller CC-BY level data. The binding obligation when bundling any of these is the
**upstream** (Waller CC-BY attribution; JMdict CC-BY-SA if JMdict-derived fields ride along). Plan to
attribute Jonathan Waller (tanos.co.uk, CC-BY) for all N3 vocab level tags.

### Grammar (single open lineage; small open inventories)

| Source | N3 count | License | Bundle verdict | Notes |
|--------|----------|---------|----------------|-------|
| jkindrix/japanese-language-data `grammar-curated/n3.json` | 130 | CC-BY-SA 4.0 per LICENSE text | Avoid as data source (copyleft); reference only | GitHub auto-detect = NOASSERTION (custom LICENSE); copyright 2026, single maintainer; grammar marked `review_status:draft` |
| tristcoil/hanabira.org `grammar_ja_JLPT_N3_0001.json` | 132 | MIT | Bundle OK, attribute | title + short/long explanation per entry |
| JLPTsensei N3 index | "182" | proprietary | NEVER bundle | Private cross-check / upper-bound target only |
| Bunpro N3 deck | 220 | proprietary | NEVER bundle | Private cross-check only |

For this project's open-data reality, plan around **~130 structured N3 grammar points** sourced from
hanabira (MIT, cleanly bundleable). Treat 180-220 as a commercial coverage target to compare against,
not the size you can source openly. The gap (130 open vs 182-220 commercial) is mostly
vocabulary-like expressions and overlapping forms; the corpus can absorb those as vocab/expressions
rather than distinct grammar points, or author additional Layer-C points grounded in the open set.

### The >=3-source consensus plan (relaxed for N3)

Genuine source independence for N3 reduces to ~2 lineages:

- **Lineage 1 = Tanos/Waller** (covers vocab + kanji + grammar; all the "open JLPT" repos repackage
  this single upstream, so they are NOT independent votes).
- **Lineage 2 = KANJIDIC2/kanjiapi re-leveling** (covers KANJI ONLY).

| Dimension | Independent lineages available | Plan |
|-----------|-------------------------------|------|
| N3 kanji | 2 (Tanos 367 == KANJIDIC2/kanjiapi 367) | Keep multi-source consensus; record both lineages |
| N3 vocab | 1 (Tanos only) | Relax rule: single-lineage + `level_confidence` downgraded + `needs_review:true`; optionally license a proprietary list as a private third vote |
| N3 grammar | 1 (Tanos/hanabira) | Same relaxation; all N3 grammar is Layer C `needs_review:true` anyway |

**Owner decision A:** approve relaxing spec 1.5 to ">=2 independent lineages where they exist; else
single-lineage with explicit low `level_confidence` + `needs_review`," OR budget to license a
commercial inventory (Bunpro/JLPTsensei) as a private, never-bundled cross-check. Do not ship
single-source N3 vocab/grammar tagged as if it had multi-list consensus.

## Concrete pipeline changes

The friction is a finite set of hardcoded scope constants, plus new reconcile inputs. Inventory of
every place `n5/n4` is hardcoded (verified by grep):

| File | Construct | Change |
|------|-----------|--------|
| `scripts/export/export_corpus.py` | `LEVELS = ["n5", "n4"]` | `["n5","n4","n3"]` (drives 4 `for lvl in LEVELS` loops) |
| `scripts/export/build_conjugations.py` | `LEVELS = ["n5", "n4"]` | add `"n3"` |
| `scripts/export/export_course.py` | `for lvl in ("pre-n5","n5","n4")` summary | add `"n3"` |
| `scripts/ingest/place_items.py` | `level IN ('n5','n4')` x4; `MODULES`, `TOPICS`, `first_order`, `last_topic`, `KANJI_START/CAP` | add `mod:n3` + N3 topic rows; `level IN ('n5','n4','n3')`; N3 placement caps |
| `scripts/ingest/build_families_full.py` | `level IN ('n5','n4')` x4; `json.dumps(["n5","n4"])` x2 | add `"n3"` |
| `scripts/ingest/fix_derived.py` | `level IN ('n5','n4')` | add `"n3"` |
| `scripts/ingest/ingest_pitch.py` | `level IN ('n5','n4')` x2 | add `"n3"` |
| `scripts/ingest/prepare_coverage.py`, `prepare_generated.py`, `prepare_grammar_coverage.py`, `prepare_jec.py` | `level IN ({q})` with `keep=("n5","n4")` | add `"n3"` to keep-set |
| `scripts/ingest/prep_grammar_placement_data.py` | `level IN ('n5','n4')` x2 | add `"n3"` |
| `scripts/validate/integrity_audit.py` | `for lvl in ("n5","n4")` x2 | add `"n3"` (LV map already has n3) |
| `scripts/validate/r3_coverage_probe.py` | `for lvl in ("n5","n4")` | add `"n3"` |

Recommendation: replace the scattered literals with a single shared `LEVELS_IN_SCOPE` constant
(e.g. in `scripts/ingest/enums.py`) imported everywhere, so future N2/N1 is a one-line change. This
is a small refactor worth doing as the first N3 task; it removes the whole class of "missed a
hardcode" bugs.

New reconcile inputs (`scripts/ingest/reconcile_levels.py`): the `kanji_lists()` and `vocab_lists()`
loaders already filter to `(4,5)` / `n5,n4`. Extend them to include N3:

- `kanji_lists()`: change `if v.get("jlpt_new") in (4,5)` to include `3`; add `kanjiapi_kanji_n3.json`,
  `bluskyo_kanji_n3.csv`. The `assign()` "earliest level wins" logic already generalizes (it just
  needs `n3` in the precedence chain after `n4`).
- `vocab_lists()`: add the N3 CSVs/JSON from Bluskyo + elzup + (licensed) jlpt-vocab mirror.
- `assign()`: extend the earliest-level precedence from `n5 -> n4 -> other` to `n5 -> n4 -> n3 -> other`.

New fetch entries (`scripts/ingest/fetch_datasets.py` + `research/datasets/jlpt/`): N3 kanji/vocab
CSVs + the hanabira N3 grammar JSON, each recorded in `MANIFEST.md` with URL, version, date, SHA256
(per the persistence rule), and added to `sources.md` + `ATTRIBUTION.md`.

Cross-source ID reconciliation is the largest hidden cost. davidluzgouveia keys kanji by character
(trivial), but vocab lists key by expression+reading with no JMdict `ent_seq`. The existing
`reconcile_vocab()` already solves this: `norm_candidates()` + `match_entry()` map list entries to
JMdict via `raw_jmdict_form` and prefer the kana-matching, common entry. This machinery is fully
reusable for N3. Expect more homograph/kana-only collisions at N3 (more abstract vocab); the
`unmatched` report path already exists to route misses to manual review.

## Phased roadmap (rough effort; reuse vs new)

Effort is relative engineering+authoring days, not calendar. "Reuse" = existing script runs as-is
after the constant widen; "New" = net-new content or logic.

| Phase | Work | Effort | Reuse vs new |
|-------|------|--------|--------------|
| 0. Decisions | Sign off rule relaxation (Decision A) + copyleft ruling (Decision B) + N3 vocab target (~1797) | 1-2 (owner) | n/a |
| 1. Sources | Fetch N3 kanji/vocab/grammar lists; MANIFEST SHA256; update sources.md + ATTRIBUTION.md | 1-2 | mostly reuse `fetch_datasets.py` |
| 2. Constants | Introduce shared `LEVELS_IN_SCOPE`; replace ~20 hardcodes | 1 | refactor |
| 3. Reconcile | Extend `reconcile_levels.py` loaders + `assign()`; run; review disagreements/unmatched | 2-3 | high reuse; new = N3 inputs + relaxed confidence |
| 4. Ingest/place | Add `mod:n3` + N3 topic rows + caps in `place_items.py`; run conjugation + family builders | 4-6 | placement machinery reused; new = N3 topic design + caps |
| 5. Generate Layer B | AI pt-BR meanings/glosses for ~1800 vocab + dissections for selected N3 sentences; machine-validate vs Layer A | 8-12 | pipeline reused (`prepare_*`/`persist_*`); cost scales with item count |
| 6. Sentence selection | Run selection over the ~89k in-envelope N3 Tatoeba pool; fill gaps via AI generation (`ai_generated` + `needs_review`) | 4-6 | `select_candidates.py` reused; new = N3 envelope, more PT generation |
| 7. Author courseware | ~14-18 N3 topics -> lessons (the qualitative jump: multi-pattern sentences, inference) | 12-18 | lesson tooling reused; this is the dominant new cost |
| 8. Guidelines/phonetics pass | Apply `learning_guidelines.md` + `phonetics_pt_ja.md` across N3 lessons | 2-3 | reuse existing pass scripts |
| 9. Validate/export | Run full validator suite; re-export JSON+MD; commit | 1-2 | reuse `validate_all.py` + exporters |

Roughly **60-70% of the engineering is reuse** (schema, reconcile/match, placement, conjugation,
family, export, validators all generalize). The **new cost concentrates in Layer-B generation and
courseware authoring** (phases 5 and 7), which scale linearly with the ~+367 kanji / ~+1800 vocab /
~+130 grammar.

## Example-sentence coverage outlook for N3

This is the bright spot. Verified empirically by intersecting every Japanese Tatoeba sentence's kanji
against the level-tagged kanji envelopes (Tatoeba JP total = 248,758 sentences, verified):

- N4 cumulative envelope: 40,472 sentences (16.3%).
- N3 cumulative envelope: 129,622 sentences (52.1%).
- Net-new unlocked by going N4 -> N3: **89,150 sentences (35.8% of the entire JP corpus)**.

So **SELECTION (spec 1.2) becomes far more viable at N3** for the Japanese side: there is a large pool
of real human-written sentences within the N3 kanji envelope, dramatically reducing reliance on AI
generation for Japanese. The constraint is the pt-BR side, not the Japanese side.

**The pt-BR bottleneck remains.** Of the 248,758 JP sentences, only ~4,537 (1.8%) have *any*
Portuguese translation (vs ~232,783 with English). N3-filtered, the pt-translated subset is a few
hundred at most. Therefore: select real Japanese N3 sentences from Tatoeba, but expect ~100% of the
pt-BR translations to be **Layer-B AI-generated + machine-validated against Layer A + `needs_review`**.
Budget the human-review burden on the pt-BR translations of selected sentences (not on sourcing the
Japanese). Record the Tatoeba export date + SHA256 so the bundled count is reproducible and
attribution points to a specific dated export (and, per EDRDG, if any web dictionary surface ships,
honor the monthly-refresh obligation).

## Top risks

1. **Consensus rule not satisfiable for N3 vocab/grammar (provenance contract).** Only ~1 open
   lineage (Tanos) exists. Mitigation: formal rule relaxation (Decision A) with downgraded
   `level_confidence` + `needs_review`; do not fake multi-list agreement.
2. **Copyleft contamination for a paid product.** EDRDG (already ingested) and jkindrix are
   CC-BY-SA 4.0; ShareAlike can force the redistributed-data portion to stay BY-SA. Mitigation:
   legal ruling on "adaptation vs collection"; segregate BY-SA data tables from proprietary Layer-C;
   prefer MIT/CC-BY sources (hanabira for grammar) over jkindrix; honor EDRDG flow-through
   (About/Sources acknowledgment screen, project links, monthly refresh, no-copyright-claim).
3. **N3 vocab count instability (~20% spread).** wkei 1797 vs open-anki 2140 vs migaku ~3700-cum.
   Mitigation: pick ~1797 (Tanos new-N3) as canonical, document the disagreement; do not size Layer-B
   generation off the marketing 3700.
4. **Authoring cost of the N4 -> N3 qualitative jump.** Largest kanji jump in the ladder (+367,
   doubling cumulative); reading shifts to inference, sentences integrate multiple grammar patterns.
   Mitigation: phase-7 authoring is the dominant budget line; staff it accordingly; lean on the large
   selectable JP sentence pool to anchor authentic multi-pattern examples.
5. **pt-BR translation review burden.** ~100% of N3 sentence translations are AI-generated Layer B
   needing human sign-off. Mitigation: quantify against selected-sentence count, not the 89k pool;
   gate by `needs_review`; reuse the existing machine-validation harness.
6. **Cross-source ID reconciliation collisions.** Homographs / kana-only N3 entries will collide on
   expression+reading -> JMdict `ent_seq`. Mitigation: the existing `match_entry()` + `unmatched`
   report already handle and surface this; budget manual disambiguation time.
7. **Attribution completeness voids licenses if missed.** MIT and CC-BY both require attribution.
   Mitigation: maintain a user-visible credits/About surface naming Waller (tanos.co.uk),
   D. Gouveia, EDRDG/Jim Breen, Tatoeba contributors, hanabira; keep ATTRIBUTION.md current.

## Sources

- davidluzgouveia/kanji-data README + LICENSE + kanji.json / kanji-jouyou.json (`jlpt_new` counts).
- kanjiapi.dev `/v1/kanji/jlpt-3` (fetched live, 367); onlyskin/kanjiapi.dev README (MIT).
- AnchorI/jlpt-kanji-dictionary; Bluskyo n3_kanji.csv (Tanos).
- wkei/jlpt-vocab-api (N3=1797, no license); Bluskyo/JLPT_Vocabulary (MIT wrapper, Tanos);
  elzup/jlpt-word-list (MIT, Tanos); jamsinclair/open-anki-jlpt-decks (MIT, old-test split N3=2140).
- stephenmk/yomitan-jlpt-vocab + Bluskyo READMEs (confirm Tanos/Waller CC-BY upstream).
- jkindrix/japanese-language-data n3.json (130, CC-BY-SA per LICENSE, GitHub NOASSERTION);
  tristcoil/hanabira.org N3 grammar JSON (132, MIT).
- JLPTsensei "182", Bunpro 220 (proprietary, cross-check only); migaku ~3700-cum vocab target.
- Tatoeba jpn export (248,758 JP; N4 envelope 16.3%, N3 envelope 52.1%, 89,150 net-new; pt links
  ~4,537), CC-BY 2.0 FR.
- JLPT official level summary + FAQ (no official content list); old-test Level 3 ~300 kanji / ~1500
  words (community-rounded; precise 284/1409 unverified).
- Repo scope-constant inventory: `export_corpus.py`, `build_conjugations.py`, `place_items.py`,
  `build_families_full.py`, `reconcile_levels.py`, `integrity_audit.py`, `validate.py`,
  `r3_coverage_probe.py` (grep-verified in this repo).