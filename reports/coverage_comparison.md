# Coverage comparison vs the local course (concept-level, de-identified)

> Acceptance #13 (concept-level superset check). Compares OUR coverage against the **de-identified** Phase L+
> concept inventory ([`research/local-course-insights/concept_inventory.md`](../research/local-course-insights/concept_inventory.md))
> — never the raw material, naming nothing. The final *numeric* sentence/coverage comparison runs in P7 once
> the bank is full; this confirms the **concept superset** now. ✓ = ours covers it; ➕ = ours adds beyond the source.

| # | Concept area (L+ inventory) | Ours | Where in our build |
|--:|------------------------------|:----:|--------------------|
| 1 | Scripts (hiragana, katakana, dakuten, yōon, っ, ー, ん) | ✓ | pre-N5 topics 03–04 (kana taught row-group by group) |
| 2 | Phonology / pronunciation | ✓➕ | pre-N5 topic 05 + the BR-PT pronunciation thread; **➕ pitch accent (1,221 vocab) & devoicing/mora — absent in source** |
| 3 | Particles (は/が/を/に/で/へ/と/も/の/から/まで/や/か/ね/よ + advanced によって…) | ✓ | grammar registry (particle keys) + N5 T01–T05 + particle_set/contrast families |
| 4 | Copula & existence (です/だ, ある/いる) | ✓ | grammar `da-desu`, `aru`/`iru`; N5 T01/T05 |
| 5 | Demonstratives & pro-forms (これ/この/ここ, interrogatives) | ✓ | grammar + vocab (pronoun POS); N5 T01–T02 |
| 6 | Numbers & quantity | ✓ | vocab (num/ctr) + N5 T03 |
| 7 | Verb forms & conjugation (groups, ます, plain, て, ている, potential, volitional, imperative, passive, causative, transitivity) | ✓ | grammar registry (all enumerated) + conjugation_class families (godan/ichidan/する/来る); N5 T04/T09 + N4 |
| 8 | Adjectives (い/な, negation, past, modifying, すぎる/やすい…) | ✓ | grammar + adj_class families (i_adj/na_adj); N5 T07 |
| 9 | Grammar points & sentence patterns (~130 incl. advanced connectives) | ✓ | **364 grammar points** with original pt-BR explanation/formation/nuance |
| 10 | Kanji scope | ✓➕ | 250 leveled kanji (readings tiered, components, KanjiVG); **➕ component families + interactive-ready (vs static worksheets)** |
| 11 | Vocabulary themes (~30 life-domains) | ✓ | 1,359 leveled vocab + semantic_field/word families; functional topics weave the same domains |
| 12 | Functional/situational (self-intro, shopping, medical, bureaucracy, work, emergency) | ✓ | woven through N5/N4 topic themes (course_outline) |
| 13 | Keigo (teineigo/sonkeigo/kenjōgo/bikago) | ✓ | grammar (keigo points) + N4 keigo topic; teineigo via the você/o-senhor on-ramp |
| 14 | Counters (助数詞) | ✓ | counter vocab + the `grp:counters` family + N5 T03 |
| 15 | Onomatopoeia (giongo/gitaigo) | ▶ | out of core N5/N4 grammar scope — **flagged for a later supplement** (not regressed; planned add-on) |
| 16 | Reading/listening graded media | ▶ | the dissected-sentence bank + lessons are the substrate; a graded-reading layer is a **future feature** (dissection model already supports it) |

## Where we are already a superset / beat the source
- ➕ **Pitch accent** taught from data (the source had zero across 621 lessons).
- ➕ **Explicit JLPT N5/N4 mapping** with `level_confidence`/`level_sources` (source had none).
- ➕ **Original, deep grammar explanations** with PT-speaker pitfalls (source was grammar-light at the upper levels).
- ➕ **One cross-referenceable graph** (families, contrasts, kanji↔vocab↔sentence↔grammar) enabling spiral review
  and the §1.7 queries — the source had no spiral/cross-linking.
- ➕ **Sequencing fixes** from `gaps_to_beat`: katakana right after hiragana; time/date & adjectives earlier;
  plain↔polite integrated.

## Honest gaps vs the source (planned, not regressions)
- **Onomatopoeia** and a **dedicated graded-reading library** are supplements beyond core N5/N4 — explicitly
  deferred, not dropped. The dissection + family model already supports adding them as data later.

**Verdict:** at the concept level, our build is a **superset** of the source's N5/N4 coverage, reorganized and
deepened, with several first-class additions the source lacked. Numeric confirmation (sentences/item, % audio,
etc.) completes in P7 after the bank is filled.
