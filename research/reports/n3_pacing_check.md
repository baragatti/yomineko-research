# D11 check: is option B the digestible, no-loss choice for N3 pacing?

_Status: RESEARCH, nothing applied. Input: `research/reports/w25_proposal.md`. Measured 2026-09-27 on a read-only DB
snapshot and the course leaves at git HEAD `529131bf`. Script: session scratchpad `res0927/n3_pacing_check/check_b.py`._

## Recommendation

**Yes, B, with two changes. Call the result B′.**

1. **Placement: teach a word before its first use.** B as written moves words to vocabulary lessons at the end of
   the topic. That makes 634 of the 1,167 moved words appear before they are taught (details below). B′ puts each
   of those 634 words in a short vocabulary lesson **right before the first lesson that uses it**. The other 533
   words, which nothing earlier uses, are grouped by theme. Free words fill spare room in the pre-teach lessons
   before a new theme lesson is opened.
2. **Grouping: by theme, never by semantic set.** A vocabulary lesson may be a scene or theme (駅: 乗り換え, 改札,
   遅れる, 混む). It must not be a set of near-synonyms, antonyms or tight co-hyponyms (all the colors, all the
   family terms, 上がる/上げる). The clustering script flags such pairs mechanically (shared gloss head, same
   category tag, a transitive/intransitive pair) and keeps them at least one lesson apart.

Keep W25's cap of 10 words per lesson, the same number as the deck's `new_per_day`. Everything else in W25 §4
stays as proposed: the notice pack for 情報検索, the band gap sent to D12, and B running before W14/W22/W23.

## 1. What the evidence says

| claim | evidence | consequence for D11 |
|---|---|---|
| Semantic sets slow learning | Tinkham 1997: semantically clustered sets (eye, nose, ear...) took longer to learn; thematic sets (frog, pond, green, hop) were learned faster than unrelated words.<sup>1</sup> Waring 1997 replicated the semantic-set penalty.<sup>2</sup> Nation 2000 reviews this and advises teaching related words apart.<sup>3</sup> | Theme grouping is right. Grouping by semantic set is the one variant to avoid. |
| The penalty is real but narrow | A 2026 multilevel meta-analysis (30 studies) finds a large negative effect in trials-to-criterion designs that does not carry over to immediate posttests. Longer sessions and meaningful context make clustering neutral or helpful.<sup>4</sup> Nakata & Suzuki 2019: related and unrelated words scored the same on posttests, but related words caused more interference errors, and spacing helped either way.<sup>5</sup> | Treat the anti-synonym rule as cheap insurance, not a large gain. Our words always come with bank sentences, which is the "context" moderator. |
| Set size matters less than spacing | Nakata & Webb 2016: with spacing held equal, 4-, 10- and 20-word sets gave about the same learning, and spacing had the larger effect.<sup>6</sup> Kornell 2009: spaced flashcards beat massed for 90% of learners.<sup>7</sup> | The gain from B is not "10 is a magic number". It is that at cap 10 = `new_per_day`, one lesson a day adds no hidden card backlog, so the SRS spacing holds. At 17 words a lesson, 95 lessons overflow the daily cap. |
| Context of first meeting | A word first met in the sentences and grammar that use it gets its first encounters in meaningful context, which is the moderator above (ref. 4). | That argues for placing words before their user lesson (B′), not in a list at the end of the topic. |

The evidence therefore supports B's two main ideas (theme instead of gojuon, lesson size = deck cap). It does not
support the "topic end" placement or any grouping of near-synonyms.

## 2. Does B lose data? No. Does B-as-written break gating? Yes, and B′ fixes it.

Current N3 (it has changed since W25): **103 lessons, 1,593 new words** (W25: 101 / 1,596). K = 8 kept words per
grammar lesson, cap 10.

| object | count | under B / B′ |
|---|---|---|
| N3 vocab unlocks | 1,593, 0 unlocked twice | 1,593 get exactly one destination, 0 without one (426 stay, 1,167 move) |
| kanji / grammar unlocks | unchanged | stay in their grammar lesson |
| `card_example` rows | 1,322, 0 orphans | 610 follow their moved item (key = lesson + item) |
| `card_production_key` rows | 1,593, 0 orphans | 1,167 follow their moved item |
| leaf `srs.introduces_cards` | 2,068 | 1,167 follow their item |
| exercises (DB) | 2,160 | 690 drills stay, 937 move with their target. **12 drills target words in two lessons**: assign them to the later lesson. 521 authored exercises stay |
| `lesson_needs` pointing at a moved word | 0 | none to fix |
| corpus layer (`sentence_vocab`, tokens, glosses) | untouched | a courseware-only change |
| lesson ids | kept | grammar lessons keep their ids, new lessons only add ids. `item_lesson_index` (W23) and the W22 partition are regenerated once, after B |

Nothing is deleted. The risk is **gating**, not loss. With B as written (end-of-topic placement), these would use a
word before it is taught:

| forward reference after B-as-written | count |
|---|---|
| teaching-section `<vocab ref>` to a moved word (grammar lessons use more than 8 words: the K = 8 cap pushes out used words) | **461 refs in 51 lessons** |
| authored exercises touching a word taught later | **155 of 521** |
| `lesson_sentence` rows / leaf sentence refs with such a word | 48 of 140 / 52 of 229 |
| N3 readings to re-gate | 86 of 152 (W25: 84) |

Under B′, every one of the 634 affected words sits in a vocabulary lesson just before its first user. Measured
forward references after that placement: **0**. So the 155 exercises, 100 sentence links, 86 readings and 461
explanation refs need no rework or re-gating. Of the 634 words, 487 are used first by their current home lesson,
so the typical B′ pre-teach lesson is "the words you will meet in the next lesson" (88 lessons receive one, median
7 words, 17 need two blocks).

**Lesson count.** Without packing, B′ is 105 pre-teach + 62 theme = 167 vocabulary lessons (270 N3 lessons, vs 229
for B-as-written). Packing the 533 free words into the 416 spare pre-teach slots first (same topic, theme-compatible)
brings it close to the floor of ⌈1,167 / 10⌉ = 117, so roughly the 126 of B-as-written. The packing step is part
of the same clustering script (W25 cost: M) and adds no authoring.

## 3. Owner answer to "in theory B covers that?"

Mostly. B does what you asked (theme, a digestible size tied to the daily card cap, nothing lost). As written,
though, it would introduce about a third of the moved words *after* lessons that already use them. B′ keeps
everything from B and changes only two rules: **word before first use**, and **theme, not synonym sets**.
Recommended: approve B′ (cap 10, K = 8, pre-teach placement, anti-interference rule, packing), with the rest of
W25 §4 unchanged.

## Sources (accessed 2026-09-27)

1. Tinkham, T. (1997). The effects of semantic and thematic clustering on the learning of second language vocabulary. *Second Language Research* 13(2), 138–163. https://journals.sagepub.com/doi/10.1191/026765897672376469
2. Waring, R. (1997). The negative effects of learning words in semantic sets: a replication. *System* 25(2), 261–274. https://eric.ed.gov/?id=EJ547530
3. Nation, P. (2000). Learning vocabulary in lexical sets: dangers and guidelines. *TESOL Journal* 9, 6–10. https://www.wgtn.ac.nz/lals/resources/paul-nations-resources/paul-nations-publications/publications/documents/2000-Lexical-sets.pdf
4. The effectiveness of semantic clustering on vocabulary learning: a multilevel meta-analysis (2026). *System*. https://www.sciencedirect.com/science/article/pii/S0346251X26001727 (full text returned HTTP 403; findings taken from the abstract as indexed by search, so re-read before quoting it further)
5. Nakata, T., & Suzuki, Y. (2019). Effects of massing and spacing on the learning of semantically related and unrelated words. *SSLA* 41(2), 287–311. https://www.cambridge.org/core/journals/studies-in-second-language-acquisition/article/effects-of-massing-and-spacing-on-the-learning-of-semantically-related-and-unrelated-words/F58BA8D70385603B9C42E408BFCB8A10
6. Nakata, T., & Webb, S. (2016). Does studying vocabulary in smaller sets increase learning? *SSLA* 38(3), 523–552. https://eric.ed.gov/?id=EJ1113915
7. Kornell, N. (2009). Optimising learning using flashcards: spacing is more effective than cramming. *Applied Cognitive Psychology* 23, 1297–1317. https://onlinelibrary.wiley.com/doi/abs/10.1002/acp.1537
