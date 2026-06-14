# PLAN_REVIEW — Phase R critique, decisions & improved-spec addendum

> The Phase R gate document (spec §4 R1+R6). It (1) **audits** the spec honestly against the goal — *"best
> paid-grade Japanese course in Brazil, 0→100% N5 and 0→100% N4, for speaking / living / working in Japan"* —
> (2) records the **decisions** that resolve the weaknesses, and (3) gives an **improved-spec addendum** that
> redirects P0→P7. Evidence: the empirical [`source_coverage.md`](../reports/source_coverage.md), the verified
> R2 notes in [`research/references/`](../research/references/), the de-identified Phase L abstraction, and the
> pressure-tested [`schema_v2.md`](schema_v2.md) / [`quality_rubric.md`](quality_rubric.md).
>
> **Bottom line:** the plan is sound and the open sources *can* deliver a paid-grade N5+N4 corpus — but **five
> assumptions must change** before building (translation provenance, grammar investment, level lists, audio,
> and the "autonomous = final" framing). None is fatal; all are now decided below.

---

## PART 1 — Critical audit (R1): every weakness, named

### A. ⚠ The translation-provenance assumption is wrong (highest-impact finding)
The spec (§1.2 "prefer selection over generation", §3.3) reads as if we will usually *select* Tatoeba sentences
that **already have a Portuguese translation**. The data says otherwise: **only 1.8%** of Japanese Tatoeba
sentences have any PT translation (4,533 / 248,705); English is 93.5%. Requiring existing PT would throw away
98% of natural Japanese. **The pt-BR translation is therefore a generated Layer-B artifact for essentially
every sentence**, not a selected one — which moves the real cost/quality center of the whole build to
machine-validated translation at scale, and means "selection over generation" applies to the **Japanese**
(which must stay natural/correct) while the **translation is always derived-and-verified**. This reframing
touches §1.2, §3.3, §5.4, §7, P5, and acceptance criterion #4.

### B. ⚠ Grammar is the true differentiator and is under-specified
The Brazil market audit is unambiguous: the dominant method (Marugoto/JF) **deliberately subordinates grammar**,
pop-culture courses lean on engagement, and grammar rigor lives only in universities out of consumer reach.
Our single clearest lane to "best in Brazil" is **explicit, deep, plain-pt-BR grammar**. Yet the spec gives
grammar the *weakest* treatment: §3.8 just says "enumerate grammar points" and the §5.3 schema is thin. Grammar
also has **no authoritative open dataset** (unlike kanji/vocab/sentences), so it is the most authoring-heavy,
most teacher-review-dependent layer — and the spec invests least there. This is the biggest *quality* risk.

### C. ⚠ Level lists: only 2 in hand, counts unstable, policy undefined
§1.5 is correct that JLPT lists are unofficial and disagree — and the data proves it: our single kanji list
gives **79 N5 kanji**, the low end of the well-known ~78–103 range. We currently have **2** community lists
(1 kanji, 1 vocab); the spec requires **≥3**, and never defines the *reconciliation policy* (union? intersection?
weighted?). Without a policy, "100% of the reconciled set" (acceptance #1–2) is undefined.

### D. ⚠ "i+1" is under-operationalized and leans on contested theory
The SLA evidence is blunt: Krashen's i+1 is **influential but empirically soft/untestable**; the strong,
replicated mechanisms are **retrieval practice and spacing**. The spec's i+1 validation (§7.4) also needs the
*cumulative known set*, which doesn't exist until the P4 outline — and R3's "simple-sentence" proxy is **not**
true i+1. So i+1 must be re-cast as an *engineered content-difficulty constraint* (≥95% known tokens computed
against the outline), not a theory of acquisition, and the cumulative-known-set machinery must actually be built.

### E. ⚠ Audio is negligible from Tatoeba for a *speaking* course
Only **2.5%** of JP sentences have Tatoeba audio. A course whose entire purpose is speaking/living/working in
Japan cannot source audio from a 2.5% well. The spec lists Tatoeba audio as a source but has no fallback.

### F. ⚠ An autonomous run is not the final product (the spec admits this — we must honor it)
§1.8 already concedes the human teacher-review loop is mandatory. The real failure mode is **over-trusting AI
Layer-B/C at scale**: a thousand plausible-but-wrong translations/explanations look done but aren't. The honest
deliverable of this whole project is a **review-ready corpus**, not a shippable course. Everything must be built
to make the teacher review *fast and safe* (provenance, validation gates, needs_review-first queue), not skipped.

### G. Sentence dissection at scale — throughput vs quality
Hundreds of sentences/topic, each fully dissected (A+C tokens, per-token pt-BR gloss, every particle explained,
structure paragraph, translation, validation) is a very large LLM workload with many failure modes
(hallucinated readings, wrong glosses, unnatural pt). R3 confirms the *Japanese supply* exists; the binding
constraint is **generation + validation effort**, not source coverage. The §7 validation suite is the safeguard
— but it must be built and strict *before* mass dissection, and we likely need **tiered dissection depth**
(full for featured sentences; lighter for extra-coverage sentences) to be realistic.

### H. Vocab normalization was an unmodeled gap (now fixed in schema_v2)
The lists carry `;`-joined variants (足; 脚), affix/counter forms (～円, ～個), and する-verbs (コピーする) that
JMdict stores differently — making coverage *look* ~8% short when it is **~99%**. Without a normalizer we'd
mis-model entries and mis-count completeness.

### I–J. Two declared sources are not actually secured
- **Pitch accent** (§3.7, "optional") — but it's one of our headline differentiators (almost no BR course
  teaches it). It must be **sourced and made non-optional** (kanjium/OJAD-derived data; verify license).
- **Frequency data** (§3.5) is named only vaguely. We need a concrete CC-licensed Japanese frequency list to do
  the frequency-ordered sequencing the SLA evidence demands.

### K. Family-first vs i+1 vs frequency can pull apart
The spec wants sequencing to be simultaneously **family-driven** (teach all godan verbs together, then the rule),
**i+1** (≤1 new thing at a time), and **frequency-ordered** (high-value first). These three objectives conflict:
you cannot teach a whole family at once *and* introduce one item at a time. The spec never resolves the tension.

### L. ⚠ Licensing / commercial-use is a real, unresolved risk
This corpus "may be used commercially" (§3), but: JMdict/KANJIDIC2 (EDRDG) are **CC BY-SA**, KanjiVG is **CC
BY-SA** — **ShareAlike** can obligate a derivative database to be licensed alike, which is a genuine concern for
a paid product; Tatoeba is **CC BY** (attribution). The community level lists' licenses are unverified. This is
a legal decision for the owner, but the project must surface the facts loudly, not bury them.

### M. Scope realism
Full N5+N4 ≈ **245 kanji, ~1,400 vocab, ~150–200 grammar points, thousands of dissected sentences, dozens of
authored lessons across pre-N5/N5/N4**. This is a large, multi-session effort; the pilot will calibrate true
per-topic cost. Not a flaw — but the timeline must be set with eyes open.

### N. pre-N5 is not dataset-listable
Kana, pronunciation, pitch-intro, survival greetings are pure Layer-C authoring + our BR-PT pronunciation
thread — they have no "reconciled set" to be 100% of. The pre-N5 module needs its **own** completion criteria.

### O. Minor: handwriting/stroke practice unmodeled
The market gap analysis shows incumbents (Marugoto) drop handwriting; KanjiVG gives us ordered strokes, so we
can offer a stroke-practice exercise type — a cheap differentiator the schema should support (it does:
`kanjivg_ref`, `stroke_sequence`).

---

## PART 2 — Decisions (R6)

| # | Topic | Decision | Why |
|---|-------|----------|-----|
| D1 | **Level-membership policy** | **Weighted union across ≥3 lists.** Item is in-scope at a level if it appears in ≥1 reputable list; `level_confidence = agreeing/checked`; on N5-vs-N4 disagreement assign the **earlier** level for *introduction* but record `level_agreement`. Teach the high-confidence core first; low-confidence items still included, flagged. | §1.5; avoids both the over-narrow intersection and an unprioritized blob; matches "consensus, recorded." |
| D2 | **Add lists** | P2 must add **≥1 more vocab list** (e.g. Tango N5/N4, JLPT Sensei, jpdb, Jisho tags) and **≥1 more kanji list** (Jisho tags / a second reconstruction) → ≥3 each. | We have only 2 today; 79 N5 kanji is suspiciously low. |
| D3 | **Translation** | **Select the Japanese (Layer A); generate the pt-BR (Layer B)** validated against EN (when present, 93.5%) + dictionary token glosses + a round-trip spot-check; store `translation_confidence`; low-confidence → `needs_review`. Existing PT (1.8%) used as a free cross-check. | R3 §4. The plan's biggest correction. |
| D4 | **Sentence thresholds + AI cap** | Keep **≥3 dissected/vocab, ≥5/grammar** (R3 shows realistic). **Backfill generation per *item*** to reach threshold; soft cap **≤25% generated per topic**, overridable per-item with justification; every generated sentence `ai_generated`+`needs_review`. | R3 §5: supply is abundant; tail (~15% N5, more low-freq N4) needs generation. |
| D5 | **Dissection depth** | **Two tiers:** *full* dissection (every token gloss + every particle + structure paragraph) for **featured** sentences (those a lesson actually teaches/drills); *lite* (tokens A+C skeleton + translation + links, no prose) for extra-coverage bank sentences. Upgrade lite→full on demand. | Throughput realism (audit G) without sacrificing the teaching set's quality. |
| D6 | **Audio** | **TTS-primary** (record engine/voice in `audio_source`); Tatoeba native audio used where present; **pitch accent annotated** from kanjium/OJAD-derived data. | R3 §4 (2.5%); speaking goal. |
| D7 | **Grammar quality** | Enumerate N5/N4 grammar by reconciling **≥3 reputable references** (JLPT Sensei, Bunpro paths, Tae Kim, Imabi); model **Bunpro's dependency micro-ordering**; author **original** pt-BR `explanation_pt`+`formation_pt`+`nuance_pt`+**PT-trap callout**+contrast links+**≥5 dissected examples**; all `needs_review`. **Invest most effort here.** | Audit B; market is grammar-light; this is the differentiator. |
| D8 | **Sequencing** | **Register-explicit, ます-default + dictionary-form-early**; particles front-loaded over units 1–3 (は/も/の → を/が → で/に/へ/と/から/まで); **て-form mid-N5**; **katakana right after hiragana**; romaji weaned by ~unit 3; chunks **3–5 grammar / 15–25 vocab / 5–10 kanji** per lesson; **recognition→drill→production→can-do** ladder. | R2 curricula §10–12. |
| D9 | **Family vs i+1 vs frequency** | **Families organize and govern; i+1/frequency drive *introduction order*.** A family is introduced **incrementally** (its core member enters when due by frequency; its governing rule is taught the first time a member needs it; remaining members spiral in later). **Where they conflict, i+1 wins for introduction, families win for grouping/review.** | Resolves audit K explicitly so P4 is buildable. |
| D10 | **BR-PT pedagogy** | Ship the transfer map as a **named feature** ("Vantagens / Armadilhas do português"); pronunciation thread follows the phonology priority list (mora+length → even-moras → u-epenthesis/[ɯ] → ん-as-mora → です/ます devoicing → っ); **pitch present in audio from day 1, systematic pitch deferred to N4+ but high-freq minimal pairs flagged early**; **você→teineigo** on-ramp; "ler romaji ≠ português" one-pager; loanword hook lesson. | R2 BR-PT note (corrected). |
| D11 | **SLA engine** | Build **SRS-ready** (chunked, tagged, cumulative-known-set computed); exercises **retrieval/production-first** (≥1 recall + ≥1 production per lesson, with feedback); mnemonics **authored in pt-BR**, wrapped in spacing; kanji **component-first leading with semantic radicals**, phonetic hints secondary. | R2 SLA note (corrected). |
| D12 | **Review-readiness** | Deliverable = **review-ready corpus, not shippable course.** Validation suite built first; `needs_review`-first queue; **mandatory pilot gate** (one topic vs the rubric) before scaling; teacher sign-off required before any sale. | §1.8; audit F. |
| D13 | **Licensing** | Treat **ShareAlike (JMdict/KANJIDIC2/KanjiVG) + attribution (Tatoeba)** as an explicit owner legal decision; verify community-list licenses; record all in `ATTRIBUTION.md` with a clear commercial-use risk note. **Do not assume commercial compatibility.** | §3, audit L; acceptance #7. |
| D14 | **Schemas** | P0 uses **`schema_v2.md`**, not the §5 draft. | R4. |

---

## PART 3 — Improved-spec addendum (what changes in P0→P7)

- **P0:** write SQLite migrations from `schema_v2.md` (per-reading tiering, vocab_form/normalization, 3-axis
  sentence provenance, A+C tokens, full graph link tables, FTS5). Stub `sources.md` + `ATTRIBUTION.md` with the
  ShareAlike/attribution risk note (D13).
- **P1 (added sources):** also fetch **pitch-accent** data + a **frequency list** + **≥1 more vocab list** +
  **≥1 more kanji list** (D2, D6, I/J). Build **`normalize_vocab.py`** (split variants, strip ～, split する,
  route grammar-like entries to the grammar registry) (H). Keep the version/checksum manifest discipline.
- **P2:** apply the **weighted-union level policy** (D1) with `level_confidence`/`level_agreement`; derive
  **per-reading `introduced_at_level`** from leveled vocab (schema_v2 C1); flag disagreements for review.
- **P3 (`curriculum.md`):** encode D8/D9/D10/D11 as concrete sequencing rules + a **pt-BR grammar-term
  glossary**; cite the (now verified/corrected) R2 notes; keep nothing copied.
- **P4 (`course_outline.md`):** satisfy the **i+1 ⊕ frequency ⊕ family** reconciliation (D9); define the
  **pre-N5** module with its own criteria (N); weave functional contexts (self-intro, time/money, food,
  directions, daily routine, family, work, forms/signs); ensure a **superset of the Phase L concept map** and
  fix its gaps (pitch, JLPT mapping, katakana/adjective/time-vocab order, casual↔polite integration).
- **P5:** build the **validation suite first** (§7), then the **pilot topic end-to-end** and score it against
  `quality_rubric.md` before scaling; **tiered dissection** (D5); **generate+validate translations** (D3);
  per-item generation cap (D4); SudachiPy A+C skeleton gates every dissection.
- **P6:** author lessons to the rubric; exercise types include **production, listening, handwriting/stroke**
  (KanjiVG), particle-choice, cloze, sentence-build; **by-ID only** (G4); pt-BR throughout.
- **P7:** coverage comparison vs the Phase L abstraction (concept-level, naming nothing); **license report**;
  run the **§1.7 cross-cutting query tests**; assemble the `needs_review`-first queue.
- **Acceptance criteria deltas:** #4 reworded — sentences require natural **Japanese** + **generated-and-
  validated pt-BR** (not pre-existing PT); add **audio_source present** + **pitch accent on N5/N4 vocab**;
  add **license compatibility explicitly recorded** (already #7) as a *blocking* sign-off, not a footnote.

---

## PART 4 — What Phase R produced (in hand now)
- [`reports/source_coverage.md`](../reports/source_coverage.md) + [`research/coverage/r3_probe_results.json`](../research/coverage/r3_probe_results.json) — empirical coverage (R3).
- [`design/schema_v2.md`](schema_v2.md) — pressure-tested model, 6 hard examples pass (R4).
- [`design/quality_rubric.md`](quality_rubric.md) — the paid-grade yardstick + pilot gate (R5).
- [`research/references/`](../research/references/) — 4 cited research notes, adversarially verified & corrected (R2).
- [`research/local-course-insights/`](../research/local-course-insights/) — de-identified Phase L abstraction.
- [`design/course_outline.md`](course_outline.md) — **draft** Module→Topic→Lesson skeleton (this is also the R6 `module_map`).

## PART 5 — Open questions for the owner (decide before / during P0)
1. **Commercial licensing (D13):** are you comfortable with the **ShareAlike** obligations of JMdict/KANJIDIC2/
   KanjiVG for a paid product, or should we plan a license-compatibility strategy (e.g. keep derived DB
   shareable, sell the courseware/app layer)? *This gates "may be used commercially."*
2. **Pitch accent (D6):** confirm we include it for N5/N4 (recommended — headline differentiator) — accept the
   extra sourcing/annotation work?
3. **Romaji policy:** kana-first with a fast romaji wean (recommended), or fully romaji-free from day one given
   the strong BP spelling-reflex risk?
4. **ID style (schema E1):** opaque surrogate IDs + slug (recommended) vs human-readable composite IDs?
5. **Scope/pace (audit M):** build order — pre-N5 → N5 → N4, pilot first (recommended). Any priority reorder?
6. **AI-generation appetite (D4):** is ≤25%/topic (per-item backfill) acceptable, or stricter (more "real-only")?
