# Learning science — the second-order ruleset (extends `learning_guidelines.md`)

> Adversarially verified 2026-08-06. Every claim below was taken to primary sources and stress-tested;
> claims that did not survive are recorded in §6 so nobody re-adds them. Internal prose is English; every
> learner-facing example is pt-BR per `translation_style.md`. Rules are numbered R1..R84 so code comments,
> the builder and the auditor can cite them by ID.

## 1. What this governs, and how it differs from `learning_guidelines.md`

`learning_guidelines.md` is the SLA contract: retrieval, spacing, coverage, output, interleaving, dual
coding, mnemonics, component-kanji, pitch, motivation, plus 24 auditor checks. It answers *which
mechanisms are real*. This file answers three questions it does not:

1. **Placement.** Where inside a unit a mechanism may fire, and what it may not be applied to. Most of
   the failures found in verification were not "wrong mechanism" but "right mechanism, wrong slot".
2. **Predicates.** The guidelines say "use spaced retrieval" and "cap new load". This file says what
   field the builder reads, what integer it compares, and what makes the build exit non-zero.
3. **The speaking path.** `speaking_path.md` (66 units, 396 real phrases, 552 words, 8-week trip
   horizon) is a low-repetition, production-scored, kanji-recognition-only route. Several guidelines
   rules were written for the JLPT path and change sign here. Those are marked.

**Refinements to existing rules.** Where a rule here modifies one already in force, it says so inline
in the form *(refines A/Mnemonics line 45)* or *(refines auditor D.3)*. Six existing rules are refined
and one is contradicted outright; see §7.1.

**Confidence vocabulary.** `high` = ≥2 independent primary sources, no live contradiction. `medium` =
one good primary source, or a contested literature with a clear direction. `low` = single study,
unreplicated, or extrapolated across populations. `design choice` = no research establishes the
parameter; we picked it and say so, matching the convention at `learning_guidelines.md` line 59.

**Provenance.** Rules here are Layer C. Everything they touch in `corpus/` stays Layer A/B. A rule that
would make a corpus field depend on courseware or runtime state is invalid by construction (CLAUDE.md
two-layer architecture); R2 exists because the first draft of this ruleset broke that.

---

## 2. The ruleset

### 2.1 Encoding aids (mnemonics)

*(This block refines `learning_guidelines.md` A/Mnemonics and auditor items D.9, D.10.)*

- **R1 [enforceable] DO** keep a mnemonic as optional metadata on a `corpus/vocab` or `corpus/kanji`
  record, never as a lesson objective and never as its own SRS card; the card retrieves meaning or
  reading, never the mnemonic.
  *Why:* retrieval practice matches or beats keyword mnemonics as a standalone technique (Fritz et al.
  2007, via [Dunlosky et al. 2013](https://iverson.cm.utexas.edu/courses/310M/Handouts/Dunlosky%20et%20al.%20-%202013%20-%20Improving%20Students%E2%80%99%20Learning%20With%20Effective%20Learni.pdf));
  confidence high. Already in force; restated only because R2-R5 depend on it.

- **R2 [enforceable] DON'T** strip or condition a mnemonic at export on courseware or runtime
  scheduling state; enforce the schedule in the course layer instead (fail the LESSON if an item it
  introduces has fewer than 2 scheduled review slots in the next 7 days).
  *Why:* a corpus field that changes depending on which path scheduled it breaks "a word lives once"
  (CLAUDE.md two-layer architecture), and FSRS scheduling is not knowable at export time
  (`srs_design.md` §1). Confidence high (architectural, not empirical). The lesson-side predicate is
  already guaranteed by the D1/D3/D7 spacing rule, so treat R2 as a regression guard on spacing.

- **R3 [enforceable] DON'T** attach a `mnemonic.type = "keyword"` to a vocab item unless BOTH booleans
  are recorded true on the record: (i) the pt-BR gloss names a concrete picturable referent, (ii) a real
  pt-BR word or phrase matches the Japanese form's first two morae. Auto-reject when any sense POS is in
  `{adv, conj, prt, aux, aux-v, aux-adj, pn, cop, cop-da, int, exp, suf, pref, ctr, num}` (424 of 2,954
  N5-N3 records, 14%) or the headword is a light verb / formal noun (する なる ある いる やる こと もの
  ため よう わけ はず つもり 場合). Rejected items get a contrastive minimal pair instead.
  *Why:* the keyword benefit is limited to keyword-friendly materials, and "the vast majority of the
  research on the keyword mnemonic has involved materials that afforded its use" (Dunlosky et al. 2013
  §5.4); pt-BR keyword availability is an independent binding constraint the literature never isolates.
  Confidence: imageability limit high, keyword-availability clause design choice.

- **R4 [enforceable] DON'T** apply R3 to kanji component mnemonics. *(Refines auditor D.9, which
  REQUIRES a pt-BR mnemonic on every kanji; add an explicit exemption line there.)*
  *Why:* kanji component mnemonics are semantic decomposition of an orthographic form, a different
  mechanism with its own positive base (Flores d'Arcais; Toyoda; Mori 1998, already in
  `research/references/sla_evidence.md` §9). A crude abstract-gloss scan flags 88/630 N5-N3 characters
  (14%) including 意 感 決 変 対 関 続, exactly where decomposition helps most; without this exemption
  D.9 and R3 are jointly unsatisfiable. Confidence high.

- **R5 [authoring] DO** ship ONE integrated interactive image where a keyword mnemonic is kept (pt-BR
  keyword and referent depicted interacting), never two separate pictures; a text-only interactive-image
  description is acceptable for adult self-study.
  *Why:* Atkinson & Raugh's manipulation is a single image of "the keyword interacting with the
  translation" (Dunlosky's description); two images break `learning_guidelines.md` D.10 ("ONE relevant
  image hook") and add a meaning-irrelevant picture (coherence/redundancy). The supplied-picture
  requirement (Pressley & Levin 1978) is specific to young learners who cannot generate imagery.
  Confidence medium.

- **R6 [authoring] DO** record four caveats wherever mnemonic durability is discussed, and mark any
  pt-BR-specific durability statement `needs_review: true`.
  *Why:* (a) the "keyword forgets faster than rote" result (Wang, Thomas & Ouellette 1992) equated
  immediate performance by giving the rote group MORE practice, and the pre-1992 studies showing a
  keyword advantage at delay were discounted because every item was tested immediately AND at delay,
  which is exactly how an SRS app works; (b) Dunlosky's LOW-utility rating is driven substantially by
  keyword-generation labour a pre-authored app removes, and he lists foreign-language vocabulary first
  among domains where the benefit generalises; (c) no immediate benefit was found for first/second-year
  high-school language learners (Levin et al. 1979) or college elementary French (Willerman & Melvin
  1979); (d) no study in this base uses Portuguese-L1 learners or Japanese as L2, and the pt-BR/Japanese
  sound-alike channel (open CV syllables, 5 vowels, pan/パン capa/カッパ copo/コップ botão/ボタン) is an
  untested moderator in both directions. Confidence high that the caveats are needed.

> **Direction correction.** `learning_guidelines.md` line 45 says keyword learners "can forget FASTER
> than rote at delay (up to ~2× items lost)". That figure is unverified (the accessible source reports a
> 1-week delay, not 2 days) and the causal framing is contradicted by the primary sources: under ~2
> retrievals per item, retrieval practice ALONE does not beat restudy at 1 week and only keyword+retrieval
> does ([Qu, Liu, Qiao & Wang 2024, Heliyon, N=110](https://www.sciencedirect.com/science/article/pii/S240584402401243X)),
> and at 1 week keyword+retrieval beats keyword alone
> ([Miyatsu & McDaniel 2019, Exps 2-3, "catalytic view"](https://link.springer.com/article/10.3758/s13421-019-00936-2)).
> The mnemonic is therefore worth MORE on the sparse-repetition speaking path, not less. Soften or source
> line 45 before it is cited again.

### 2.2 Elaboration timing (TOPRA)

- **R7 [enforceable] DON'T** set a task that requires producing a NOVEL target's surface form FROM
  MEMORY *and* composing novel surrounding language. Auditable predicate, both conditions required: the
  target's surface form is ABSENT from the prompt AND the learner must generate novel surrounding
  language AND the form's kana/kanji string first appears in this unit.
  *Why:* free composition around a brand-new form depresses productive written form recall
  ([Barcroft 2004, SLR 20:303-334](https://journals.sagepub.com/doi/10.1191/0267658304sr233oa);
  Barcroft 2009, TESOL Q 43:79-103, N=114; Wong & Pyun 2012, CMLR 68:164-189). Confidence medium and
  contested: [Yanagisawa & Webb 2021](https://onlinelibrary.wiley.com/doi/10.1111/lang.12444)
  (398 effect sizes, 42 studies, N=4,628) found the EVALUATION component, maximal for original-sentence
  production, contributed most to learning, and Zou 2016/17 (LTR 21(1):54-75) found sentence-writing beat
  cloze. Ship as a design heuristic with `needs_review: true`, not as a settled finding.

- **R8 [authoring] DO** allow, at first encounter, substitution drills where the target form stays
  VISIBLE in the frame, and self-referential slot fills (seu nome, sua cidade) inside such a frame.
  *Why:* the form is supplied, so nothing is generated from memory; this is the repeated-exposure
  condition that won every Barcroft experiment. Self-reference is superior to semantic encoding, not
  inferior ([Symons & Johnson 1997](https://pubmed.ncbi.nlm.nih.gov/9136641/), d≈0.45), and banning
  personalisation would remove the main autonomy/relatedness lever `learning_guidelines.md` line 62
  requires. Confidence medium.

- **R9 [enforceable] DON'T** let an added elaborative task reduce an item's encounter count within the
  unit; exposures are never traded for elaboration.
  *Why:* Barcroft 2004 Exp.1 confounded task type with encounter count (4 reps × 6 s vs 1 rep × 48 s),
  and Yanagisawa & Webb 2021 found frequency of encounters outweighed time on task. Confidence high.

- **R10 [authoring] DO** defer free composition over brand-new kana/kanji specifically.
  *Why:* Wong & Pyun found the penalty larger for Korean than French and attributed it to L1-L2
  orthographic distance; pt-BR to Japanese is maximally distant, so this is the highest-risk case. Where
  the item is a SPOKEN chunk the learner never writes (most of `say_now`), the evidence does not apply at
  all: every TOPRA study measured written productive recall. Confidence medium.

### 2.3 Generation, pretesting, and the first attempt

- **R11 [enforceable] DO** require a drill whose expected answer is a Japanese surface form to satisfy
  one of: (a) its lemma is in the unit's POST-introduction known set (`known` evaluated AFTER
  `known.update(local)`, `build_speaking_path.py:247`), or (b) it is rule-derived (inflection, katakana
  transliteration, transparent compound) with all base morphemes in that set AND the generating rule
  present in the unit's `patterns`. Violations exit non-zero.
  *Why:* the generation effect (d≈0.40 overall, [Bertsch et al. 2007](https://link.springer.com/article/10.3758/BF03193441),
  445 effect sizes) does not occur for novel meaningless forms (McElroy & Slamecka 1982; Mulligan 2002;
  Lutz, Briggs & Cain 2003, 6 experiments). Confidence high. Note the snapshot: `known` currently means
  two different things inside the same loop (line 208 excludes the unit's new words, line 247 includes
  them); `speaking_path.md` §4 must name which one. Clause (b) exists because レストラン, ホテル and 入口
  are rule-derivable and were blocked by the naive version of this rule.

- **R12 [enforceable] DO** permit at most ONE drill per unit whose answer fails R11, tagged
  `mode: "pretest"`, answer key rendered immediately after the attempt, never scored.
  *Why:* errorful generation followed by feedback beats reading even for novel foreign vocabulary
  ([Potts & Shanks 2014, JEP:General](https://psycnet.apa.org/record/2009-14440-005), 4 experiments), and
  the benefit requires anticipation (Potts, Davies & Shanks 2019: generating AFTER seeing the answer gave
  nothing). Confidence medium; already implied by `learning_guidelines.md` line 14.

- **R13 [enforceable] DO** pair a unit whose drills exceed N substitution items with at least one
  whole-sentence shadowing or order-reconstruction item over the same phrase.
  *Why:* generation enhances item memory but DISRUPTS order memory even for known items (Mulligan 2002,
  Mem&Cog: "generation enhanced item memory... but disrupted performance on the order-reconstruction
  test"). A course whose target is SOV order and particle placement is training exactly what generation
  degrades. Confidence medium.

- **R14 [enforceable] DON'T** apply any known-set precondition to exam-mode papers.
  *Why:* `context_fill` is 4-option recognition (`exam_simulator.md`:39) and `sentence_order` is
  order-reconstruction over given `pieces` (line 40); neither is a generation task. The existing
  study-mode filter (lines 47-49) is correct and sufficient, and a mock paper that contains only studied
  items stops predicting the exam. Confidence high.

- **R15 [enforceable] DO** restrict unit-opening pretests to items carrying a pre-existing semantic
  bridge: (a) the item has its one relevant image and the pretest runs word→image or image→word, or
  (b) it is a gairaigo / Portuguese-origin loan transparently related to a known pt-BR word, or (c) it is
  a kanji compound whose semantic radical or both components are already in the cumulative known set.
  Items failing all three get NO pretest.
  *Why:* the pretesting effect is real (g=0.54 specific, k=97, [St Hilaire, Chan & Ahn 2024,
  Psychon Bull Rev](https://link.springer.com/article/10.3758/s13423-024-02500-9)) but nulls or reverses
  on arbitrary form-meaning pairs: Seabrooke et al. 2019 (J. Memory & Language, five experiments, study
  time EQUATED, Potts & Shanks's own materials) found "no significant benefit of generating errors over
  studying", and in Exp 5 guessing IMPAIRED cued recall. An FSRS vocab card is `recognition: JP→pt`,
  i.e. cued recall of an arbitrary pair. The positive ecological result (Chua & Pan 2026, Cognitive
  Research, d=0.18-0.40) used word-image formats. Confidence medium.

- **R16 [enforceable] DO** cap pretests at 5 items per unit, comprehension direction only (JA→pt-BR or
  image→word), free generation or multiple choice WITH the image; bare 2-alternative choice on a kana
  form is forbidden. Feedback on the same screen, and the feedback step is generative (learner restates
  the meaning in their own pt-BR before advancing).
  *Why:* g=0.54 is the SPECIFIC effect; the general effect on non-pretested material is g=0.04 (St
  Hilaire et al. 2024), so pretesting everything buys nothing spillover. Potts & Shanks 2014 found
  choice-with-feedback did NOT beat reading, and 50% success makes 2AFC a graded retrieval in disguise.
  Immediate beats delayed feedback (Mera, Dianova & Marin-Garcia 2025, J. Cognition, 58.2% vs 50.9%).
  The generative-feedback clause is from Khin & Pan 2026 (preprint, flag as preliminary). Confidence
  medium; the cap of 5 is a design choice.

- **R17 [app] DON'T** write pretest attempts to `review_log`, and DON'T count a pretest as an item's
  first FSRS retrieval.
  *Why:* `srs_design.md` §1 seeds cards at lesson completion, so a unit-opening pretest precedes card
  existence; §4 makes `review_log` the monthly optimizer's append-only input, and forced-wrong guesses
  would feed FSRS a 0%-success first review and inflate difficulty. Confidence high (architectural).

- **R18 [enforceable] DO** amend auditor D.3 to read "the first GRADED retrieval of each new item is
  supported enough to succeed (~70%+); a `pretest` exercise is exempt and does not count as that first
  retrieval." *(Refines auditor D.3.)*
  *Why:* a pre-instruction guess precedes support by construction, so without this amendment every unit
  adopting R15 fails D.3. Confidence high (internal consistency).

- **R19 [app] DO** correct the metacognitive illusion with more than copy: pt-BR text stating the guess
  is supposed to be wrong, PLUS a delayed judgment-of-learning prompt rather than item-by-item, PLUS a
  one-screen pretested-vs-read performance comparison after the unit's items have been reviewed.
  *Why:* pre-informing learners only "partly countered" the miscalibration and they remained unaware when
  making item-by-item JOLs (Yang, Potts & Shanks 2017 Exp 4); delayed JOLs (Exp 5) and performance
  feedback (Pan & Rivers 2023) worked. Confidence medium.

> **Expectation setting.** Budget d≈0.2-0.4 on cued recall for the vocabulary pretest case, not g=0.54.
> Record the mechanism as CONTESTED: attention (St Hilaire 2024), curiosity/feedback processing (Potts,
> Davies & Shanks 2019), elaborative encoding (Seabrooke et al. 2022, which explicitly rejects
> error-correction).

### 2.4 Desirable difficulty: what may be made harder

*(This block gives the auditor an explicit whitelist/blacklist. The axis is VARIABILITY vs DEGRADATION,
not stimulus vs retrieval.)*

- **R20 [authoring] DO** treat these as legitimate difficulties: expanding-lag scheduling; recall over
  recognition; spoken production over selection; varied scenario context; interleaving of
  already-blocked confusables; generation before presentation; multi-talker audio; speech rate varied up
  to natural rate; varied kana/kanji exemplars (print, handwritten, signage) AFTER the character is
  reliably recognised in one canonical form.
  *Why:* Bjork & Bjork's own canon includes contextual variation, and multi-talker training yields word
  forms whose advantage GROWS as signal-to-noise drops
  ([Sommers & Barcroft 2011, Applied Psycholinguistics](https://doi.org/10.1017/s0142716410000469), Exp 2);
  the benefit is representational (indexical detail), not effort, since a nasal harder-to-encode voice
  produced WORSE learning (Exp 1). This carve-out is required for consistency with the HVPT rule already
  at `learning_guidelines.md` line 56. Confidence high.

- **R21 [enforceable] DON'T** raise difficulty by degrading the stimulus: disfluent or
  stylised-for-difficulty typefaces, muffled/nasal/clipped audio, added babble as a difficulty device, or
  any audio below the learner's measured comprehension floor. Automatic fail.
  *Why:* [Taylor, Sanson, Burnell, Wade & Garry 2020, Memory](https://www.tandfonline.com/doi/full/10.1080/09658211.2020.1758726)
  ("Disfluent difficulties are not desirable difficulties", four experiments): Sans Forgetica "led to
  equivalent memory performance, and sometimes even impaired it". State the justification honestly: the
  disfluency effect is MODERATED by working-memory capacity (Lehmann, Goussios & Seufert, Metacog Learn
  11(1):89-105), a variable this app cannot observe at runtime, so we cannot condition on it. Do NOT
  write "it doesn't work": Xie/Zhou/Liu 2018's null is robust for transfer but its recall moderation was
  faulted by Weissgerber, Brunmair & Rummer 2021 (EPR 33(3):1221-1247). Confidence medium.

- **R22 [app] DO** gate any desirable difficulty on the learner being ≥80% correct over the last ≥5
  exposures of that item or contrast; DON'T gate on `srs_design.md` §2 `ease`.
  *Why:* desirability is conditional on prior knowledge (Bjork & Bjork 2023, verbatim: "If, however, the
  learner does not have the background knowledge or skills to respond to them successfully, they become
  undesirable difficulties"). `ease` is per-capability over 74 capabilities on a deliberately coarse
  binary signal, one granularity above the item, and start 2.2 / +0.06 per success means ~13 consecutive
  correct answers to reach ceiling. The 80% floor is a DESIGN CHOICE; no study establishes a threshold.

- **R23 [app] DO** sequence audio as a ladder: clean single-talker at introduction → multi-talker →
  natural rate → mild ambient noise, each step gated on R22 for that item.
  *Why:* replaces a blanket audio ban that would have made the 8-week trip goal (station announcements,
  konbini counters) unreachable, while keeping the degradation blacklist intact. Confidence medium.

- **R24 [enforceable] DON'T** list "delayed feedback within a session" as a permitted difficulty.
  *Why:* it contradicts `learning_guidelines.md` A ("DO give immediate corrective feedback on every
  recall attempt") and auditor D.2. The literature is genuinely split (Metcalfe, Kornell & Finn 2009,
  Mem&Cog 37(8):1077-1087 is pro-delay; the Karpicke line is pro-immediate) and is recorded here as
  UNRESOLVED. Do not ship both; the standing rule wins until resolved.

- **R25 [enforceable] DON'T** file scaffold removal or feedback withholding under "stimulus difficulty".
  Unglossed unknown tokens belong to auditor D.6 (i+1 coverage), romaji weaning to guidelines B / auditor
  D.15, answer-key availability to auditor D.2. One defect, one place it fires.
  *Why:* taxonomic hygiene; the duplicate rules would double-fire and the romaji item is one line from
  reading as "keep romaji", inverting guidelines B. Confidence high.

### 2.5 Cognitive load

- **R26 [enforceable] DO** score exactly two load quantities, both expressed as element interactivity
  relative to the learner's CUMULATIVE KNOWN SET at that unit, never learner-independent.
  *Why:* element interactivity "underpins both intrinsic and extraneous cognitive loads" (Chen, Paas &
  Sweller 2023, [EPR](https://link.springer.com/article/10.1007/s10648-023-09782-w)), so scoring one as a
  count and the other as a format checklist splits one currency into two. The same paper concedes element
  interactivity "is not a precise measure of complexity", so record intrinsic as an estimate with its
  stated knowledge assumption. Confidence medium.

- **R27 [enforceable] DO** make redundancy expertise-indexed: a support channel is a violation only
  AFTER the learner can decode the primary channel unaided. Encode each channel with a computed EXPIRY
  UNIT: romaji expires at the kana-mastery gate (~unit 3, auditor D.15); furigana on a kanji expires once
  that kanji is in the cumulative known set with N spaced reviews logged; an L1 gloss expires once the
  word passes its retention check. Before expiry, pass (scaffolding). After, fail.
  *Why:* expertise reversal; Sweller's own ESL writing says novice translations should be integrated then
  "eliminated entirely once it becomes redundant", and novice-suitable design "may become dysfunctional
  for more expert learners". A static checklist would flag unit-1 romaji+kana while passing unit-60
  furigana on long-mastered kanji. Confidence high.

- **R28 [enforceable] DO** fail split attention unconditionally: a gloss or translation must be adjacent
  to, or click-revealed on, its token; and fail a decorative image with no referent in the unit's item set.
  *Why:* Sweller's ESL article endorses exactly this L2-glossing form (translations "close to the
  original", or "appear by clicking on the relevant word"). Confidence high.

- **R29 [authoring] DO** require every load rationale in a design doc or authoring prompt to name a
  mechanism already governed by `learning_guidelines.md` (retrieval, spacing, interleaving-by-similarity,
  variability, self-explanation, task repetition, dual coding) and cite that rule; a rationale naming no
  mechanism fails, including one that says "reduces extraneous load" with no identified format violation.
  DON'T ban the string "germane load".
  *Why:* a mechanism-naming requirement is strictly stronger than a vocabulary ban and does not
  accidentally reject Mayer's generative-processing principles the course already imports (guidelines
  lines 39-41). State germane's status honestly: Sweller 2010 / Kalyuga 2011 reformulated it as
  non-additive WM resources devoted to intrinsic load, but validated three-factor instruments exist and
  are current (Leppink 2013; DeLeeuw & Mayer 2008; Klepsch 2017; Krieglstein et al. 2023). The real
  reason not to score it is psychometric weakness (Klepsch 2017: germane d=0.35 vs intrinsic 0.73,
  extraneous 0.94), not nonexistence. Confidence high.

### 2.6 Scaffold fading

- **R30 [app] DO** split support into three independently faded channels, each gated by a card measuring
  the SAME skill: `gloss_support` (pt-BR meaning, gated by the vocab JP→pt card), `reading_support`
  (furigana, gated only by a reading-specific card), `structure_support` (token dissection, gated by the
  grammar capability's skill-track state). Auditor test: no channel may be driven by a card whose
  prompt-response direction differs from the skill it scaffolds.
  *Why:* high retrievability on a meaning-recognition card is evidence the learner maps written form to
  meaning; it is NOT evidence they can produce the READING, which is what furigana scaffolds. Kalyuga's
  adaptive method requires a rapid diagnostic of the same schema. Confidence high.

- **R31 [app] DON'T** fade `reading_support` until reading/production cards ship (`srs_design.md` §6
  lists them as phase 2), and NEVER fade it on the speaking path.
  *Why:* `speaking_path.md` §1 makes kanji recognition-only and signage-only, and `say_now` items are
  speaking targets; stripping the reading from a token whose meaning card matured leaves a learner who
  cannot say the phrase. Confidence high.

- **R32 [enforceable] DO** treat the TOKEN, not the kanji, as furigana's unit. Add a mechanical Layer-A
  boolean `reading_irregular` (computed from per-kanji registry readings plus rendaku/sokuon/long-vowel
  variants; no valid segmentation ⇒ true). A build-time validator FAILS if any renderer emits per-kanji
  ruby for a `reading_irregular` token.
  *Why:* measured over 6,426 kanji-bearing vocab entries, 214 (3.3%) admit no per-kanji segmentation, and
  the rate is worst where the course starts (69/604 N5 kanji-words, 11.4%): 今日 明日 昨日 今年 今朝 大人
  部屋 下手 果物 時計 眼鏡 建物 八百屋, お母さん お父さん, and the native day series ついたち through
  はつか. 504 of 5,565 dissected sentences (9.1%) contain at least one such token. The schema also stores
  reading at TOKEN level only. Confidence high.

- **R33 [app] DO** fade on STABILITY, not retrievability, and monotonically: full while reps < 4
  successful reviews; partial while stability < 21 days OR lapses > 0; none only when stability ≥ 21 days
  AND lapses == 0. Only a lapse restores support, and it restores to partial, not full.
  *Why:* `srs_design.md` §1 sets desired retention 0.90, so "retrievability < 0.9" is a test for OVERDUE,
  not for novice; gating on it makes scaffolding oscillate with time-since-review. Thresholds are a
  design choice; the monotone-function-of-durable-knowledge requirement is not.

- **R34 [enforceable] DO** include one "cold" block per unit: ≥1 already-mature sentence rendered with
  ALL support off regardless of per-item state, plus a reveal.
  *Why:* per-item adaptive fading never yields a clean unsupported text, because at any moment some token
  is still in learning, so the learner never practises the criterion task. Expertise-reversal studies fade
  TOWARD the criterion task. Confidence high (structural).

- **R35 [authoring] DO** bias LATE when the fade gate is ambiguous.
  *Why:* the expertise reversal is asymmetric (assistance-to-novices d=0.505 vs withholding-from-experts
  d=-0.428) and language learning is the domain where it is weakest
  ([Tetzlaff, Simonsmeier, Peters & Brod 2025, Learning and Instruction 98:102142](https://doi.org/10.1016/j.learninstruc.2025.102142),
  176 effect sizes, 60 experiments, N=5,924). The L2 gloss literature specifically shows no harm at higher
  proficiency: glossed reading beat non-glossed on both immediate (45.3% vs 26.6%) and delayed (33.4% vs
  19.8%) posttests ([Yanagisawa, Webb & Uchihara 2020, SSLA 42(2):411-438](https://doi.org/10.1017/S0272263119000615),
  359 effect sizes, N=3,802). Confidence high.

### 2.7 Coverage and load thresholds

- **R36 [enforceable] DON'T** gate anything on a coverage PERCENTAGE; express every gate as an integer
  unknown-vocab count, and never write a coverage percentage into learner-facing copy.
  *Why:* on this corpus ≥95%, ≥98% and zero-unknown select the SAME 26 of 396 phrases (median 8 content
  tokens per selected phrase), so the percentage is spurious precision over a binary. And the only
  coverage level current replications can separate is 100%: Webb, Pellicer-Sanchez & Wang 2025 (Reading
  in a Foreign Language 37(1):1-21, N=94) found NO significant differences among 90%, 95% and 98%.
  Confidence high.

- **R37 [enforceable] DO** gate by support mode, using counts. GLOSSED (lesson body, `say_now` with
  dissection visible): `unknown_vocab <= MAX_NEW`. SHADOWING: not gated on unknown count, gated instead
  on the item having appeared glossed in the same unit. UNSUPPORTED-COMPREHENSION (listening items where
  the score depends on understanding): `unknown_vocab == 0`. EXAM STEMS: exempt, with the reason recorded.
  *Why:* spoken input tolerates LOWER coverage than reading (van Zeeland & Schmitt 2013; Durbahn et al.
  2020), frozen chunks are learned holistically and are already exempt in code (`words = []` when
  `s["chunk"]`), and a 95% floor on shadowing would delete 370/396 items and leave 54 of 66 units with no
  shadowable audio. Confidence high.

- **R38 [enforceable] DO** reconcile the i+1 constant to ONE number read from the builder.
  *Why:* three files currently disagree: `build_speaking_path.py:36` `MAX_NEW = 3`, `speaking_path.md`
  §3.3 says ≤2, `learning_guidelines.md` auditor D.6 says ≤1. Any auditor written against the doc will
  fail every unit the builder emits. Confidence high (this is a live defect, not a research claim).

- **R39 [enforceable] DO** define "known word" ONCE in the exporter and name it. Today `token.vocab_id +
  link_ok` and the `sentence_vocab` table disagree on 36 of 396 phrases. Treat "no vocab-linked tokens"
  as UNMEASURED, never as fully known (14 of 20 chunk phrases currently score 100% coverage only because
  data is missing).
  *Why:* a metric with two live definitions cannot support a gate. Confidence high.

- **R40 [enforceable] DO** enforce coverage scenario-locally: for each unit, the cumulative known set must
  cover ≥95% of tokens in that unit's own `say_now` phrases; stage-level, ≥95% across the stage's phrase
  set.
  *Why:* this is computable today, reuses the existing i+1 machinery, and imports no English word-family
  figures. Confidence: design choice, but the only coverage assertion in this file that is both
  meaningful and enforceable.

- **R41 [authoring] DON'T** state a terminal vocabulary-size target for the speaking path; state
  scenario completion, and state the measured number.
  *Why:* `speaking_path.md` §1 states the terminal condition as "the path is complete when all 12 stages
  are survivable out loud; there is no vocabulary-size finish line, because every stage is a valid
  stopping point". The honest measured figure is that the 513-word terminal set covers 78.9% of tokens in
  the project frequency table. English word-family figures (Nation 2006's 6,000-7,000 for spoken 98%) do
  not translate: on `research/derived/frequency/tatoeba_lemma_freq.json` (44,692 lemmas, 2,560,920
  tokens) 95% needs 5,590 LEMMAS and 98% needs 14,108, roughly 2× the English family counts, and the
  entire 7,401-entry corpus reaches only 96.07%. Nation's own conclusion also runs the other way
  ("coverage greater than 98% may be needed to cope effectively with the transitory nature of spoken
  language"). Confidence high.

- **R42 [authoring] DON'T** use the speaking path's known set as a reading-readiness signal.
  *Why:* (i) that path teaches kanji for recognition only and only signage kanji, so a completer is
  blocked orthographically regardless of vocabulary size, and (ii) JLPT passages are level-controlled
  text, so authentic-reading coverage thresholds do not apply in either direction. Record this in
  `exam_simulator.md` where it describes switching paths. Confidence high.

### 2.8 Production and skill specificity

- **R43 [enforceable] DO** enforce pattern production debt path-wide: every id in `patterns` must appear
  in ≥1 pt-BR→JA production item within 3 units AFTER the unit that introduces it. The introducing unit
  is exempt.
  *Why:* comprehension practice transfers to production ACCURACY (Shintani, Li & Ellis 2013, 30 studies:
  both instruction types had large effects on productive knowledge; Shintani 2015, 33 studies: input-only
  Processing Instruction equalled production-based instruction on production measures) but NOT to
  production SPEED (DeKeyser 1997; de Jong 2005; S. Li & Taguchi 2014, where accuracy transferred and
  speed did not). The speaking path is scored on fluency, so it needs production practice; because the
  failure is about speed, the practice must be repeated and paced rather than merely present. Confidence
  high. Do NOT restate this as "comprehension practice does not teach production" — it teaches accuracy fine.

- **R44 [enforceable] DON'T** let a production item be the first retrieval of any item it targets.
  Required order per item: model in `say_now` → recognition/checkpoint → production. Auditor test: every
  targeted word/pattern id must be in a PRIOR unit's `words`/`patterns` or in `cumulative_known_vocab`.
  *Why:* `learning_guidelines.md` line 13 (~70% first-retrieval success); a production item on a word
  introduced minutes earlier will fail well below that, and failed unfed retrieval ≈ restudy. Confidence
  high.

- **R45 [enforceable] DO** count a production item toward any quota only if it carries `answer_key` plus
  `accepted_variants` (or an ASR/IME-checkable target); a unit whose only production items are ungraded
  FAILS.
  *Why:* `srs_design.md` §6 ships recognition-only at launch and `speaking_path.md` marks audio
  "pending"; mandated free production would ship UNGRADED, violating auditor D.2, and an ungraded
  production attempt is strictly worse than a fed-back recognition item. Confidence high.

- **R46 [enforceable] DO** require `repetitions >= 3` on every production item, with at least one paced
  or timed repetition; DON'T rely on one-shot production.
  *Why:* proceduralization is essentially complete after the first ~16-item block and automatization is
  the long flat tail (DeKeyser & Suzuki 2025), so a "once per item" quota is a checkbox that cannot move
  the construct. Repetition of a spoken task improves fluency robustly. Confidence high for the direction;
  the number 3 is a design choice, and the specific "flat by 5, wasted past 6" curve is NOT supported
  (see §6).

- **R47 [app] DO** make vocab production an SRS card duty, not a unit duty: every vocab id acquires a
  pt-BR→JA production card once its recognition card graduates. DON'T impose a per-unit vocabulary
  production quota.
  *Why:* unblocks `srs_design.md` §6 by making production a phase-2 card type rather than a launch-time
  unit gate; if production cards slip, R43 still guarantees pattern-level production coverage. Confidence
  high (architectural).

- **R48 [enforceable] DO** count HVPT-style forced-choice PERCEPTION drills with trial-by-trial feedback
  toward the production goal for pronunciation, minimal-pair and pitch targets, keeping the ~80%
  discrimination gate before pushing production of a contrast.
  *Why:* perception-only training improved rated PRODUCTION of English /r/-/l/ by Japanese listeners,
  retained at 3 months (Bradlow, Pisoni, Akahane-Yamada & Tohkura 1997; Bradlow et al. 1999). A blanket
  "recognition never counts" would contradict `learning_guidelines.md` line 56. Confidence high.

- **R49 [enforceable] DO** count production items INSIDE the ~4-6 exercises-per-unit cap (auditor D.5),
  not in addition to it. Fail at `len(checkpoint) + len(production) > 6`.
  *Why:* measured over the 66 built units, a naive per-item production quota (patterns mean 5.8, words
  mean 7.8, checkpoint mean 4.9) would breach D.5 in 64 of 66 units. Confidence high.

### 2.9 Corrective feedback

- **R50 [enforceable] DO** require `feedback.model` (a `sentence_id`) and `feedback.retry: true` on every
  `production` and `sentence_build` exercise. A model with no hint is legal; a hint with no model is not.
  *Why:* the active ingredient is the RETRY, not withholding the model. Implicit/model feedback is better
  MAINTAINED over time ([Li 2010, Language Learning 60:309-365](https://eric.ed.gov/?id=EJ883422)), recasts
  are strong (g=0.70, 95% CI [0.48, 0.93], and specifically strong in FOREIGN-language contexts, which is
  ours: [Rassaei 2022, Language Learning Journal 52(1):16-36](https://doi.org/10.1080/09571736.2022.2097298)),
  and machine-delivered EXPLICIT feedback beats indirect (g=0.69,
  [Ngo, Chen & Lai 2023, ReCALL](https://doi.org/10.1017/s0958344023000113), 15 studies). Confidence high.

- **R51 [enforceable] DO** allow hint-before-model ONLY when `hint_target != null` AND the target form
  has been in the cumulative known set for ≥1 prior unit (`hint_when: "review"`); on an item's FIRST
  production, model first, then retry.
  *Why:* prompts consolidate acquired knowledge; whether corrective feedback initiates NEW knowledge is
  unresolved (Lyster, Saito & Sato 2012, Language Teaching 46:1-40). Lyster & Saito's own age moderator
  runs against older learners, and Alzi'abi 2026 (N=132) found prompts produced far higher UPTAKE (86.1%
  vs 43.7%) with NO significant between-group difference in accuracy gains, i.e. the visible metric is
  dissociated from durable development. Confidence medium.

- **R52 [enforceable] DO** force `hint_target = null` (model + retry) whenever the runtime signal is a
  whole-utterance score rather than a localised error, and ALWAYS for pronunciation and suprasegmental
  targets (mora length, っ, ん, pitch).
  *Why:* ASR feedback is large on segmentals but SMALL on suprasegmentals (Ngo et al. 2023), and a FALSE
  hint is strictly worse than a model; recasts, not prompts, moved Japanese learners' production at
  spontaneous-speech level (Saito & Lyster 2012, Language Learning 62:595-633). Confidence high.

- **R53 [app] DO** cap the correction loop at ONE retry, then model and move on; no repeat-until-correct.
  *Why:* high-anxiety learners gained nothing from corrective feedback and the benefit ran through
  modified output, not feedback type (Sheen 2008, Language Learning 58:835-874);
  `learning_guidelines.md` line 64 flags anxiety as acute for solo self-learners. Confidence medium.

- **R54 [enforceable] DO** require ≥60% of a unit's production exercises to carry a non-null `hint` with
  a `hint_target` from the enum `{particle, verb_form, counter, word_order, mora_length, pitch}`, and
  100% to carry `model` + `retry`.
  *Why:* a presence-only check on every item is satisfied by boilerplate; a coverage ratio plus a
  constrained enum forces the hint to name a real error class. Note the field is `hint`, not `prompt`:
  `prompt` is already the question stem on all 2,537 corpus exercises. Confidence: design choice.

### 2.10 Shadowing and pronunciation routing

- **R55 [enforceable] DO** tag every unit's shadowing slot `target ∈ {prosody, fluency,
  comprehensibility, mora_timing}`, and treat mora_timing (ん, っ, long vowels, even-mora rhythm) as a
  LEGITIMATE shadowing target.
  *Why:* the only systematic review (Whitworth & Rose 2025, Research Synthesis in Applied Linguistics
  1(2):239-269 = the 2024 Oxford MSc thesis; cite as ONE source) found all 8 fluency studies positive,
  11 prosody studies generally positive including Japanese pitch, and 7 of 9 global studies positive.
  Moraic and durational features are temporal-prosodic, which is where the positive evidence lives, and
  they are the #1 BP→JA transfer problem (`learning_guidelines.md` lines 79, 83, 84). Confidence medium.

- **R56 [enforceable] DON'T** route true segmental contrasts (つ vs す, ら-row, /u/ quality, し/ち) to
  shadowing, and DON'T attribute segmental accuracy gains to shadowing in any learner-facing text.
  *Why:* the segmental evidence is k=4 (2 positive, 2 mixed, 0 negative), verdict "inconclusive". Read
  that as UNDERSTUDIED, not null: there is no meta-analysis and no pooled effect size. Confidence medium.

- **R57 [enforceable] DO** give every segmental contrast an articulatory production slot (model plus
  record-and-compare, minimal-pair production), not an ID drill alone.
  *Why:* HVPT as specified at `learning_guidelines.md` line 56 is perception-only and the doc itself
  concedes gains are only "partly generalizable"; Saito & Plonsky 2019 (k=77) find instruction most
  effective when it targets "learners' monitored production of specific segmental/suprasegmental
  features". Routing all segmental work to a perception drill would leave segmental PRODUCTION with no
  vehicle. Confidence high.

- **R58 [enforceable] DO** give each unit BOTH speaking check modes, scored on separate scales and never
  averaged: (a) a controlled read-aloud of a shadowed sentence, which MAY serve as the first retrieval,
  and (b) a text-free situation prompt, scheduled at the unit's first SPACED review. Fail if a unit has
  only one mode, if the scores are merged, or if a text-free prompt is the FIRST retrieval of a
  same-unit sentence.
  *Why:* Saito & Plonsky (2019, Language Learning 69:652-708) argue controlled and spontaneous
  performance are distinct phenomena that must be assessed SEPARATELY, which is an argument for measuring
  both, not for deleting the controlled measure. A text-free prompt as the only check in
  `arrival/unit-01` (`cumulative_known_vocab: 0`) is a designed-to-fail first retrieval against
  guidelines line 13. Confidence high.

### 2.11 Japanese-specific data and rendering

- **R59 [enforceable] DO** keep pitch accent Layer A in the EXISTING shape
  `vocab.pitch[] = {reading, accent_positions[]}` (mora index of the drop, 0 = heiban); DON'T add a
  heiban/atamadaka/nakadaka/odaka enum.
  *Why:* `schema_v2.md` decision #9 already mandates per-reading arrays because words have multiple
  accepted accents; 93 vocab records already carry two positions (久しぶり [0,5], 会議 [1,3], 両方 [3,0],
  乗り換える [4,3]) which an enum cannot represent, and "nakadaka" does not say which mora drops.
  Confidence high.

- **R60 [enforceable] DO** ingest accent only from kanjium (CC BY-SA 4.0), never NHK (proprietary) or
  OJAD (research-use only), never AI-generated; and DON'T gate content on missing accent data.
  *Why:* `license_audit.md` D-LIC-3 (2026-06-26) already ruled out NHK and OJAD for this commercial
  project. A "no accent ⇒ not in the speaking path" gate blocks 66 of 513 path words (12.9%) and 23/23
  (100%) of its N3 words (pitch coverage is N5 90.4%, N4 89.3%, N3 0.0%), and the blocked list is
  dominated by the highest-survival katakana words (バス タクシー レストラン コーヒー パン アパート テレビ)
  plus いいえ. Emit `pitch_coverage` per unit and stage into the manifest and fail only on REGRESSION.
  Confidence high.

- **R61 [enforceable] DO** require `accent_positions` on BOTH members of any pitch minimal pair a unit
  teaches, both already in `cumulative_known_vocab`; and author `say_now` audio at the accent-PHRASE
  level, not assembled from per-word fields.
  *Why:* pitch accent correlates with rated comprehensibility in L2 Japanese
  ([Saito & Akiyama 2017, JSLP 3(2):199-217](https://doi.org/10.1075/jslp.3.2.02sai)) alongside speech
  rate, lexical variation and lexical appropriateness; but that study measured COMPREHENSIBILITY (rated
  ease of understanding), not intelligibility, and connected-speech accent is not concatenated dictionary
  accent (downstep, compound-accent relocation), which is why OJAD ships a sentence-level predictor.
  Confidence medium. For beginners, spend the prosody budget on speech RATE and lexical appropriateness
  first (Saito, Trofimovich & Isaacs 2015/2016, N=120: segmentals matter from intermediate up).

- **R62 [enforceable] DON'T** render romaji as a learning surface: no Latin-script reading in an exercise
  stem, in any answer option, or as the PRIMARY form of a vocab or phrase card. DO keep the `romaji`
  FIELD in corpus data. *(Refines guidelines B and auditor D.15: the rule is default-off-and-measured,
  not prohibited.)*
  *Why:* the warrant is the redundancy effect (auditor D.10) plus pt-BR grapheme interference
  (`phonetics_pt_ja.md`): romaji "neko" invites BP final-vowel raising to [ˈneku], "u" invites BP
  rounding, "tsu" invites "tu", and doubled consonants in "kitte" do not cue the っ mora hold. It is NOT
  Okuyama (2007), which is a single unreplicated n=61 study with a minimum detectable effect of d≈0.73:
  it found no LARGE romaji effect, which is a null, not evidence of harm. Romaji is load-bearing for kana
  instruction (211 occurrences in `kana.json` as the pronunciation key), IME typed input, search and
  screen readers; banning the DATA is not the same as banning the SURFACE. Confidence medium.

- **R63 [app] DO** treat audio coverage as a build METRIC, not a completion gate, and drive replay by
  affordance (autoplay on reveal, ≥44px replay control, loop/shadow toggle, playback surviving card
  advance) rather than by a logged compliance counter.
  *Why:* there are currently ZERO audio files in the project and 239 corpus items carry
  `audio: "pending"`, so a per-item replay gate would make all 66 speaking units uncompletable; and the
  Okuyama audio finding is a within-experiment CORRELATION over voluntary use, where the correlate was
  INTENSIVE use, so a "≥1 replay" gate enforces the low end of the distribution and adds the controlled
  motivator guidelines line 63 rules against. Log replay counts as telemetry to test the correlation in
  our own data. Confidence medium.

- **R64 [enforceable] DO** render a phrase word-spaced iff it has ≥3 word-level units AND its longest
  uninterrupted kana run is ≥6 characters, spacing at BUNSETSU boundaries (わたしは がくせいです, never
  わたし は がくせい です); spacing is a DISPLAY toggle that fades like furigana and is always OFF in
  production and recall items.
  *Why:* interword spacing facilitates word identification and eye guidance in syllabic script but not in
  mixed kanji-hiragana ([Sainio, Hyönä, Bingushi & Bertram 2007, Vision Research 47(20):2575-2584](https://pubmed.ncbi.nlm.nih.gov/17697693/)),
  measured on NATIVE readers. A naive "zero kanji ⇒ spaced" test misfires here: only 22/396 phrases have
  zero kanji and 8 of those are single-token interjections, while 191 of the 374 "unspaced" phrases
  (51.1%) are under 25% kanji, i.e. long kana runs the rule would miss. Prerequisite: a clean bunsetsu
  layer must be generated first, because `bank.json`'s `tokens` mixes SudachiPy A and C split modes
  (おはようございます。 surfaces concatenate to a duplicated string) and renders すみません as すみ/ませ/ん,
  which the corpus itself glosses as "expressão fixa". Confidence medium.

### 2.12 Progress, motivation and reward

- **R65 [enforceable] DO** name at least one observable act in pt-BR on every unit and stage completion
  screen; a screen whose only content is a counter FAILS.
  *Why:* ground this in goal specificity and the reciprocal achievement→motivation finding (Alamer &
  Alrabai 2023, RI-CLPM, 226 learners, 17 weeks), NOT in Al-Hoorie 2018, which measures questionnaires
  and says nothing about learner-facing displays. Confidence medium.

- **R66 [enforceable] DO** fix the source of can-do statements before R65 ships: `corpus/capabilities/
  registry.json` has 74 records with keys `{id, name, level, grammar_keys}` whose pt-BR names are grammar
  labels ("Cópula だ/です e negação"), and zero contain "consegue". Either add a `can_do: {"pt-BR": …}`
  field per capability (Layer C, `needs_review: true`) or point at `speaking_path.md` stages, which are
  already can-do framed.
  *Why:* the rule as first drafted cited a file that cannot supply its own example. Confidence high.

- **R67 [enforceable] DON'T** surface an unqualified "você já consegue…" unless backed by ≥1 PRODUCTION
  event; recognition-only FSRS state licenses only "você já reconhece…". Auditor test:
  `assert_can_do` requires `production_evidence >= 1`.
  *Why:* `srs_design.md` §6 is recognition-only at launch, so an unqualified can-do claim manufactures
  the illusion of mastery guidelines line 15 warns against. Confidence high.

- **R68 [app] DON'T** use self-reported INTENDED EFFORT as a success criterion anywhere, and DON'T make
  any counter (XP, dias seguidos, minutos estudados) the HEADLINE progress figure. DO keep objective
  behavioural KPIs internal: retention/dropout, reviews completed, time on task, on-time review rate,
  production completion.
  *Why:* ideal L2 self → intended effort r=.611 but → achievement r=.202 (k=13, N=3,551), ought-to →
  achievement r=-.048 ([Al-Hoorie 2018, SSLLT](https://files.eric.ed.gov/fulltext/EJ1202469.pdf)). But
  Al-Hoorie explicitly asks the field to ADD objective behavioural measures, so "no counter exists" is
  the wrong reading; "self-report is never the criterion, and no counter is the headline" is the right
  one. Note the achievement estimates rest on k=7-13 with I²≈86-91% and two of three go non-significant
  after publication-bias correction. Confidence medium.

- **R69 [app] DO** keep a short self-report instrument for ANXIETY and ENJOYMENT only.
  *Why:* it is the only valid channel for that construct, and without it `learning_guidelines.md` line 64
  is unauditable. Confidence high.

- **R70 [authoring] DO** state the streak position honestly: controlled motivation is UNRELATED to L2
  achievement (r=-.03, p=.24) but positively related to anxiety (introjected r=.23, external r=.12,
  global r=.16 — [Alamer, Robat, Shirvan & Ryan 2025, EPR 37:59](https://link.springer.com/article/10.1007/s10648-025-10038-y),
  21 studies, N=24,470). Streak-guilt mechanics are avoided for the ANXIETY cost, not because they reduce
  achievement. Broken-streak guilt is textbook introjected regulation.
  *Why:* claiming streaks harm learning is not established, and shipping an overclaim invites a correct
  rebuttal that takes the real objection down with it. Confidence high.

- **R71 [app] DO** tie any counter to the DUE QUEUE, never to the cheapest action: it advances when the
  day's due FSRS + skill queue is cleared, or when nothing is due and one `course/speak/` unit is
  completed. No code path may tick it while `due_memory` is non-empty.
  *Why:* FSRS is the primary track (`srs_design.md` §1); a bar satisfiable by a 5-minute speaking unit
  lets backlog compound behind a green number against the 120/day cap. Confidence high (architectural).
  Note the arithmetic: 66 units at 1/day is 66 days against `speaking_path.md`'s 56-day trip horizon, so
  the default plan must be a weekly stage-paced target (~9 units/week), not a daily quota of 1. Assert
  `ceil(unit_count / default_units_per_day) <= trip_horizon_days`.

- **R72 [app] DO** make streak breakage cheap: one silent free auto-repair per rolling 7 days, the
  stage-completion map at least as prominent as the counter, and no loss-framed copy
  ("você vai perder sua sequência" is banned).
  *Why:* the only RCT evidence (Aulagnon, Cristia, Cueto & Malamud 2025, Econ. of Educ. Review 109,
  ~60,000 Peruvian 4th-6th graders) shows streak highlighting raises PLATFORM USE over an active control,
  but its achievement result rests on 1,500 of 60,000 (2.5%) with attrition running in the treatment's
  direction and no significant difference from the other message arms. The same RCT found personalised
  reminders better on the EXTENSIVE margin, which is the abandonment risk that actually threatens a solo
  8-week product. Confidence low for the mechanic, high for the caution.

- **R73 [enforceable] DO** make the reward ledger MONOTONE: no event may decrement a learner-visible
  balance, tier or possession. This bans hearts/lives/energy, streak wagers, loot-box losses and league
  demotion in one predicate. Auditor test: replay the reward event log and assert every balance series is
  non-decreasing. Protective loss-framing (streak freeze) is permitted because it only ever adds.
  *Why:* a checkable invariant that does not depend on whether loss aversion is universal (it is
  contested in both directions: λ≈1.955, 95% CI [1.820, 2.102] in Brown, Imai, Vieider & Camerer 2024,
  JEL 62(2), 607 estimates; Gal & Rucker 2018's scope critique is not dead). Confidence high.

- **R74 [enforceable] DO** guarantee the access invariant: no mechanic may remove access to content, to a
  retry, or to corrective feedback as a consequence of an error. Test: for every exercise state,
  `feedback_available == true` regardless of prior error count, and no reachable state requires payment
  or a timer to attempt a due or unlocked item.
  *Why:* the rationale is internal, not behavioural-economic: `learning_guidelines.md` A and auditor D.2
  require feedback on every recall attempt, and line 64 notes anxiety suppresses output. A mechanic that
  withdraws access as a consequence of an error punishes the exact error→feedback event that produces
  learning. Confidence high.

- **R75 [enforceable] DO** make repeating mastered content UNPROFITABLE rather than impossible:
  `reward(event) = f(novelty, retrieval difficulty, production depth)` with within-session decay past the
  first correct retrieval of an item, and a cap where total reward from items with FSRS retrievability
  > 0.95 may not exceed 20% of session reward. Test: simulate 50 repetitions of one mastered item and
  assert total reward < the reward of one new-item production exercise. DO give production and
  skill-track exercises a reward path keyed on exercise type and `capability_id`, not only on FSRS
  due-ness.
  *Why:* a hard "refuse to emit for anything not new or due" rule would zero out task repetition
  (guidelines line 31), the speaking path's `drills` and `shadowing` blocks (known by construction), and
  successive relearning to criterion (Rawson, Vaughn, Walsh & Dunlosky 2018, d≈1.52-4.19); and
  `srs_design.md` ships no FSRS cards for kana (skill track) and no production cards at launch.
  Confidence high.

- **R76 [app] DO** offer if-then implementation-intention planning at the FIRST LAPSE (≥2 consecutive
  missed days), never as an onboarding gate; gate it on a captured goal-commitment rating; require ≥1
  rehearsal step; store it as a STRUCTURED PAIR (`cue.type ∈ {event_anchor, time_and_place}`, non-empty
  `cue`, non-empty `action`, `goal_commitment`, `rehearsed_at`), not a free string; deliver as a ±90 min
  window, never an instant; cap re-surfacing at 2-3 lapse-triggered check-ins.
  *Why:* the effect is real (94 tests, d=0.65, Gollwitzer & Sheeran 2006; 642 tests, .27≤d≤.66,
  [Sheeran, Listrom & Gollwitzer 2024, ERSP 36(1):162-194](https://www.tandfonline.com/doi/abs/10.1080/10463283.2024.2334563))
  with format, motivation and rehearsal as the verified moderators — cue TYPE is not among them. But the
  closest analogue is null on the outcome we care about: plan-making moved course completion by
  β=0.19pp, p=.670 across ~250,000 learners in 247 online courses
  ([Kizilcec et al. 2020, PNAS 117](https://www.pnas.org/doi/10.1073/pnas.1921417117)). And unmotivated
  users produce inadequate plans "even when asked to do" (Gollwitzer & Sheeran), so a non-empty-string
  auditor check is satisfied by `if_then_plan = "x"`. Beshears et al. (2021, Mgmt Science) rules out a
  NARROW ENFORCED WINDOW WITH A PENALTY, not clock times as such. Budget ~0-1pp on completion, not an
  adherence backbone. Confidence medium.

### 2.13 Strands, unit budget and the fluency gap

- **R77 [enforceable] DO** tag every unit component with `strand ∈ {meaning-input, meaning-output,
  language-focused, fluency}` and emit a per-unit and per-stage histogram into the manifest; fail if any
  strand is 0% across a stage.
  *Why:* [Nation 2007, *The Four Strands*](https://roycross.blog/wp-content/uploads/2024/08/2007-four-strands-paul-nation.pdf)
  is an audit instrument rather than a method, and the histogram is the cheapest defect detector we have:
  run it against incumbents and Duolingo is ~80% language-focused, Anki-only is ~100%, Michel Thomas has
  ZERO meaning-input, ALG is 100% meaning-input. Confidence high for the taxonomy.

- **R78 [enforceable] DO** declare the strand budget as a constant and hold each stage within ±10 points:
  speaking path 15/30/25/30 (input/output/language-focused/fluency), JLPT path 25/25/35/20.
  *Why:* Nation's 25/25/25/25 is described BY NATION in the same paper as "an arbitrary decision", so
  deviating deviates from a heuristic, not a finding. He also concedes the efficiency asymmetry that cuts
  against his own split: deliberate vocabulary study ≈35 words/hour vs ≈4 words per 56 minutes of graded
  reading (Waring & Takaki 2003), roughly 9× in favour of deliberate study. For an 8-week horizon the
  breadth argument for the balanced split is weak. Confidence: design choice, explicitly labelled.

- **R79 [enforceable] DO** give every unit a `fluency` block satisfying Nation's four conditions, each
  machine-checked: (a) `fluency_items ⊆ cumulative_known_set` with ZERO new tokens, patterns or kanji;
  (b) the prompt is a situation, not a form; (c) a speed target is attached (seconds-to-first-token, or a
  per-utterance cap derived from the learner's own prior attempt); (d) ≥6 productions.
  *Why:* this is the highest-leverage rule in the file. Fluency development is the strand essentially
  every self-study product omits, because it looks like nothing is being taught, and it costs us no new
  content: "material the learner already knows" is exactly what `cumulative_known_vocab` is. Confidence
  high that the gap is real; the numbers are design choices.

- **R80 [enforceable] DO** require a new `pattern` to be exercised against ≥3 DISTINCT slot-fillers drawn
  from `cumulative_known_set` in the same unit, or be demoted to `chunk_phrases`.
  *Why:* a pattern that appears in exactly one frozen phrase is a chunk, not a pattern, and calling it a
  pattern makes the `patterns` field a lie the auditor then measures. This also matches the one part of
  the Michel Thomas method that survives the loss of cognate arbitrage (which pt-BR→Japanese does not
  have). Confidence high (definitional).

- **R81 [enforceable] DO** require every grammar id reachable in the path to have ≥3 distinct example
  sentence ids at or below the unit that introduces it, and never review an item twice in a row against
  the same sentence.
  *Why:* Bunpro's "progressive sentences" is anti-overfitting engineering: it prevents memorising one
  sentence instead of one pattern. Free for us (the dissected bank is keyed to grammar ids); anything
  short of 3 is a data gap to mine, exactly like the `lodging`/`health` shortfall. Confidence: design
  choice with a clear mechanism.

- **R82 [enforceable] DO** schedule an Assimil-style ACTIVE PASS: every unit N gets
  `active_pass_unit = N + K`, where K is a builder constant sized as a proportion of the horizon
  (~6-10 for the 66-unit / 8-week path, never Assimil's hardcoded half-course), re-presenting the same
  `say_now` ids pt-BR→JA, production direction only. Test: every unit id with `n ≤ 66 - K` appears in
  exactly one later unit's `active_pass` list.
  *Why:* pure scheduling structure that instantiates a long fixed spacing lag plus a
  recognition→production direction switch; productive knowledge is harder and later-acquired than
  receptive (Webb 2005). Sizing the gap as a proportion of the horizon is already the Cepeda 2008 rule at
  guidelines line 20. Confidence medium.

- **R83 [enforceable] DO** spiral the scenarios: every stage 1-6 seed lexicon must reappear in at least
  one stage 7-12 unit.
  *Why:* the 12 stages are currently visited once each, so `arrival` is learned in week one and never
  retrieved again, which violates the spacing rule the course already holds. Marugoto's 15 recurring
  topics are the reference implementation. Confidence high (internal consistency).

- **R84 [enforceable] DO** cap verbatim repetition of the same utterance at 3 consecutive reps; the 4th
  and beyond must vary at least one slot or be preceded by a corrective model. DON'T author any exercise
  that requires a partner.
  *Why:* high verbatim repetition automatizes errors (Thai & Boers 2015, TESOL Quarterly; Boers 2014,
  RELC 45:221-235), which is Glossika's unaddressed failure mode; and Minna no Nihongo's 練習 and half of
  Genki's Practice sections are unusable solo, which is the gap this product exists to fill. Confidence
  medium.

---

## 3. Applying the ruleset to the speaking-path unit shape

`speaking_path.md` §4 defines the fields. This is what each must contain under R1-R84, and which rules
change the current builder output.

| Field | Must contain | Rules | Change from today |
|---|---|---|---|
| `can_do` | NEW. One pt-BR first-person testable act, derivable from ≥1 `say_now` sentence, using only `cumulative_known_vocab ∪ words` | R65, R66 | field does not exist |
| `say_now` | 5-8 real sentence ids, `unknown_vocab <= MAX_NEW` against the pre-unit known set, model-first presentation | R37, R38, R44 | MAX_NEW must be reconciled across three files |
| `chunk_phrases` | subset taught whole; exempt from the new-word count (already true in code); never split by R64 spacing | R37, R64, R80 | patterns occurring only here demote INTO this field |
| `words` | frequency-ordered vocab ids; mnemonics optional metadata gated by R3; no production quota | R1, R3, R47 | no `ceil(len(words)/3)` production quota |
| `patterns` | grammar ids whose forms occur in `say_now` AND which are exercised against ≥3 distinct known fillers | R80, R81, R43 | currently truncated at `[:6]` by a slice constant, with substring false positives (`ような` matched inside さようなら); needs the curated `sentence_grammar` table (2,648 rows) instead of raw substring matching |
| `production` | NEW, replaces the deferred `drills`. Each item: `answer_key`, `accepted_variants`, `repetitions >= 3`, `targets`, `feedback: {model, retry, hint, hint_target, hint_when}` | R11, R43-R46, R50-R54 | `drills` exists in 0 of 66 units; no rule referencing it can be enabled until the builder emits this |
| `fluency` | NEW. Zero new items, situational prompt, speed target, ≥6 productions | R79 | field does not exist |
| `shadowing` | same sentence ids, `target ∈ {prosody, fluency, comprehensibility, mora_timing}`, tagged `strand: meaning-input` | R55, R56, R77 | currently untagged and implicitly counted as output |
| `signage_kanji` | recognition-only; components introduced in the unit containing the first word that uses them; `reading_support` never fades here | R31, R32 | 216 distinct kanji already emitted, only 18 classic signage: `speaking_path.md` §1's "only signage kanji" is stale prose and should be corrected to match the builder |
| `checkpoint` | exam-bank ids per §4 below; counts inside the ≤6 exercise cap with `production` | R49, §4 | cap not currently enforced |
| `active_pass` | NEW. Unit ids from N-K whose `say_now` is re-presented pt-BR→JA | R82 | field does not exist |
| `strand_histogram` | NEW, manifest-level | R77, R78 | does not exist |
| `pitch_coverage` | NEW, manifest-level per unit and stage | R60 | does not exist |

**Ordering inside a unit** (fixed template, from R44 + R58 + R15):
`pretest (≤5, gated by R15)` → `say_now` model → `shadowing` (listen/decode) → dissection and
`patterns` notes rendered inline adjacent to the phrase that instantiates them → `words` →
`production` (form-supported first) → `checkpoint` → `fluency` → controlled read-aloud check.
The text-free situation check (R58b) is scheduled at the unit's first spaced review, not here.

**Two unit-shape defects R43-R49 depend on and cannot work around.** The builder emits no `production`
key at all, and `known` means two different things inside the same loop (`build_speaking_path.py:208`
excludes the unit's new words during phrase selection, line 247 includes them). Both must be fixed before
any of the production rules can be turned on; until then they are authoring guidance, not checks.

---

## 4. Using the 6,166-item exam bank without becoming a JLPT course

The bank is 6,166 items across 40 files. `speaking_path.md` §7 already reuses it for `checkpoint` and
already re-draws distractors from the known set. Four constraints keep it a retrieval instrument rather
than a syllabus.

**4.1 Direction of authority.** The bank never chooses what a unit teaches. A unit's content comes from
`say_now`, and items are selected to match it (`phrase` 120, `new-word` 177, `review` 24 links today).
A stage that cannot be covered by the bank emits fewer checkpoint items and records the shortfall; it
never pulls in an item to fill a slot. This is the same selection-over-generation posture as
`speaking_path.md` §3.6.

**4.2 i+1 filtering, integer not percentage** (R36, R37). Checkpoint stems obey the GLOSSED gate:
`unknown_vocab <= MAX_NEW` against the cumulative known set, with distractors re-drawn from that set.
Exam-MODE papers are exempt (R14): a mock paper that contains only studied items stops predicting the
exam, and `exam_simulator.md` lines 47-49 already scopes the known-set filter correctly to study mode.
Do not extend it.

**4.3 Format variety, and what each format actually measures.**

| Bank type | What it is | Speaking-path use |
|---|---|---|
| `sentence_order` | order-reconstruction over given `pieces` | KEEP, first. It is Mulligan's order-memory measure, which is exactly what substitution drilling degrades (R13) |
| `context_fill` | 4-option recognition | KEEP, second. Not a generation task; no known-set precondition beyond the stem filter |
| `grammar_form` | pattern selection | KEEP, feeds the skill track per `srs_design.md` §2 |
| `kanji_reading` | character → reading | KEEP for signage kanji only, recognition direction |
| `paraphrase`, `usage` | meaning equivalence | KEEP, capped |
| `orthography` | produce the kanji | EXCLUDE. This path is recognition-only |
| `reading_comp`, `text_grammar` | passage comprehension | EXCLUDE. Different skill, different strand |
| `listening_*` | scripts, `audio: "pending"` | DEFER until audio lands, then they become the R23 audio ladder's top rungs |

Cap at two items per format per unit (already the rule) so no unit is monotonous, and order
production-first. A checkpoint composed entirely of 4-option recognition is a `strand: language-focused`
block and must not be counted toward the meaning-output budget (R77, R78).

**4.4 Cadence and what the score is for.** Target roughly one real assessment per two units
(JapanesePod101's "Can Do" pathway ships 130 lessons to 65 assessments; the cadence is cheap for us since
the bank already exists). The checkpoint's output is a right/wrong signal into the capability tracker,
never a JLPT level estimate shown to the learner. A speaking-path learner is never told they are "at N4":
`speaking_path.md` §5 shows JLPT bands "for orientation only" and the path never gates on them, and R42
forbids reading the known set as a readiness signal in either direction.

**4.5 Test-out.** Each stage may open with an optional test-out of ≥8 items drawn from that stage's
linked bank items, distractors from the cumulative known set. Passing marks the stage's `words` known
without seeding them as NEW FSRS cards. This is LingoDeer's best structural idea and it is what makes a
linear path non-punitive for a learner with partial prior knowledge. Gate stage unlocking on mastery
(≥90% of the prior stage's words reaching a first successful review at interval ≥1 day), not on tapping
Next: that is WaniKani's mechanism, expressed against FSRS state as a query rather than new machinery.

---

## 5. Competitor teardown summary

| Course / tool | Core mechanism | What we take | What we reject |
|---|---|---|---|
| Duolingo | linear Path, HLR scheduling, can-do unit labels, hearts + streaks + leagues | can-do unit labels as the unit's primary key (R65); habit scaffolding | hearts/energy metering the error (R74); streak as the spine (R70-R72); receptive-only efficacy standard; open-ended "chat about anything" AI |
| Busuu | bite-size CEFR lessons + asynchronous HUMAN correction | the shape of the obligation: a unit is not done until the learner produced something and got a correction (R45, R50) | paywalling the mechanism (grammar, SRS, conversation all gated) |
| Memrise | user "mems" (deleted 2022, partly restored 2026), native-speaker video clips | multi-speaker authentic audio (R20, R23) | building the course layer on user-generated content; mnemonics as the product |
| LingoDeer | grammar-first, teacher-written, handwriting drill, TEST OUT every 8-10 units | test-out gate (§4.5); handwriting; grammar notes inline at point of use (R28) | its syllabus order: て-form ~unit 55 before dictionary form ~unit 62, and Direction at ~unit 57 for a traveller |
| Rosetta Stone | Dynamic Immersion, no L1 ever | picture+audio pairing (already Mayer, guidelines line 39) | the translation ban: L1 glosses BEAT L2 glosses (Yanagisawa et al. 2020) and would delete every Vantagem PT / Armadilha PT callout |
| Speak / AI-conversation | scripted instruction → drilled repetition → open AI conversation | goal-oriented, form-focused, system-guided task with recast feedback (d=0.58 configuration, Bibauw et al. 2022) | unconstrained free chat, the weakest cell in that meta-analysis's own moderator table |
| Falou (pt-BR incumbent) | speaking-first, AI pronunciation scoring, ~$9.99/mo | nothing structural; it sets the price ceiling | 29+ languages on a shared pipeline means no Japanese-specific depth: that is our defensible ground |
| WaniKani | radical→kanji→vocab DAG, mastery-gated unlocking | mastery-gated unlocking expressed as SRS state (§4.5); bidirectional component id arrays | "forget about individual strokes" (guidelines B keeps handwriting); invented radical names; fixed global ordering |
| Bunpro | grammar SRS, typed cloze, progressive sentences, progressive hints | progressive sentences (R81); the hint ladder as worked-example fading (R30-R33) | authored-for-the-point Japanese that "can be a bit strange" |
| Kaishi 1.5k / Anki | union of decks re-sorted by frequency, word highlighted inside its sentence | word-highlighted-in-sentence as the canonical card front; radical introduction indexed to first vocabulary encounter | vocabulary-only, no scenario axis; Core 2k's ~8% inherited defect rate is our calibration for what imports cost |
| Genki | four-part lessons, two physically separate tracks (conversation/grammar vs reading/writing) | two-clock pacing as an explicit contract, not an accident | partner-dependent Practice sections (R84) |
| Minna no Nihongo | direct method, L1 exiled to a separate 15-language booklet, 練習 A/B/C fading ladder | the L1-in-a-separate-file architecture (already `i18n.md`); 練習B substitution drills as the highest-output-per-authoring-effort exercise | teacher dependency; salaryman-in-a-vacuum register; syllabus-driven ordering |
| Tae Kim | structure-first, hardest conjugations first, casual-first | the derivational-correctness argument: every grammar point reachable by derivation from an already-taught form (already guidelines B) | casual-first register, and zero exercises (a reference is not a course) |
| Marugoto / JF Standard | can-do sequencing, 15 spiralled topics, Katsudoo/Rikai split, romaji at A1 with a 60% kana target | can-do as the unit's primary key (R65); topic spiral (R83); phrase index as a first-class artifact (already `chunk_phrases`) | grammar thinness (Rikai exists because Katsudoo alone does not generalize); classroom shape |
| Satori Reader | same text, per-learner orthography rendering | orthography as a per-learner render setting, not a content property (R30-R33, R64) | fully-authored content (spec §1.2 prefers real sentences) |
| Pimsleur | anticipation principle + fixed graduated-interval ladder | prompt-before-reveal with a mandatory answer gap and a mandatory model (R12, R16) | the 1967 ladder: performance-blind, no outcome study, FSRS dominates it at every scale ≥1 day |
| Assimil | passive wave then active wave at a 50-lesson lag | the active pass (R82) | the hardcoded half-course lag |
| Refold / MIA | immersion-first, 1T1R sentence mining, hour logging | 1T1R at CARD granularity (stricter than the unit's ≤3); time accounting by activity type | "monolingual only"; output deferred to phase 4; the hour mythology |
| ALG | ~800h silent period, no notes, early output causes permanent damage | perception-before-production for specific phonemic contrasts (already guidelines line 59) | everything else; there is no controlled study, and the theory is built so any failure is a protocol violation |

---

## 6. What we deliberately do NOT do

### 6.1 Popular but not supported

- **Learning styles / the meshing hypothesis.** No learner-type selector, no "visual learner" mode.
  Pashler, McDaniel, Rohrer & Bjork 2008 found the evidence base absent. Dual coding (word + relevant
  image, for everyone) is a different and supported thing and is already guidelines line 39.
- **The 10,000-hour rule.** Deliberate practice explains 26% of variance in games, 21% music, 18% sports,
  **4% in education**, <1% in professions (Macnamara, Hambrick & Oswald 2014). No hours-to-fluency
  progress bar. Log time by strand because it is diagnostic (R77); never present hours as a promise.
- **Input-only absolutism and silent-period thresholds.** Comprehensible input is necessary and not
  sufficient; the immersion literature (Swain) shows persistent production errors after years of rich
  input, which is precisely what the input-only position predicts should not happen. No rule of the form
  "no output before N hours".
- **Streaks as the motivational core.** See R70-R72. The published lifts are engagement (+1.7% D7,
  +0.38% DAU); the "3.6× more likely to complete" figure is correlational.
- **"X hours = one semester" efficacy claims.** The same two statisticians produced 55h (Rosetta Stone
  2009), 34h (Duolingo 2012) and 22.5h (Busuu 2016) on the same instrument. That is a study-design curve,
  not a technology curve. If we publish anything it names instrument, skills measured, N enrolled, N
  completed, hours and funding (R77 in §2.12 is the internal half of this).

### 6.2 Claims that failed verification and must not be re-added

Each of these was proposed, taken to primary sources, and refuted. They are recorded with the refutation
so the next research pass does not re-derive them.

- **"Interleaving beats blocking only across sessions; within a session it is neutral or worse."**
  REFUTED. Pan et al. 2019's winning arm ran the blocked-to-interleaved transition INSIDE the introducing
  session. Suzuki, Yokosawa & Aline 2020 (LTR, n=60, one session) and Nakata & Suzuki 2019 (MLJ, n=115)
  both found interleaving beat blocking at 1-week delay after a SINGLE session. And the learner-side
  boundary is inverted: lower-pretest participants benefited MORE from interleaving. Adopting the rule
  would have outlawed the HVPT minimal-pair drills and the はし pitch pair guidelines lines 56-57 already
  mandate. The real boundary is PHASE-level (do not interleave during initial presentation), not
  session-level.
- **"A picture without a gloss produces a metacognitive illusion; picture+gloss beats either alone
  (g≈0.33-0.35)."** REFUTED as stated. The g values are IMMEDIATE-test only; the same meta-analysis
  (Zhang, Sala & Gobet 2025, Educational Research Review) reports "no significant differences emerged
  between conditions on delayed vocabulary tests". Worse, the proposed carve-out is backwards: van den
  Broek et al. 2021 (JEP, three classroom experiments) found images that help retrieve the answer WEAKEN
  posttest recall and inflate confidence, so the illusion lives at the RETRIEVAL step the rule would have
  legalised. Morett 2019 found images beat glosses for beginners on concrete words, and Carpenter &
  Geller 2019 showed the illusion is belief-driven, not fluency-driven, so printing a gloss beside the
  image does not remove it. What survives: an image must never be the sole meaning carrier, as a
  data-completeness requirement.
- **"Confusable pairs must be taught in separate units unless a contrastive cue names the differing
  feature."** REFUTED. Chang et al. 2022 had no separate-teaching condition and no
  simultaneous-vs-sequential manipulation at all; its cost was immediate-writing-only and gone at one
  week. Li, Shi & Wang 2025 (N=183 true beginners) concludes the opposite ("support using paired
  character presentation"). Brunmair & Richter 2019 and Firth, Rivers & Boyle 2021 both find interleaving
  strongest where differences are SUBTLE, with effects extending to delayed tests. The rule would have
  made the auditor self-contradictory against guidelines lines 34-36 and auditor D.8.
- **"Three timed repetitions capture most of the fluency gain; more than ~6 is wasted."** REFUTED.
  Lambert, Kormos & Minn 2016 (SSLA, misattributed in the original claim to "Hanzawa & Suzuki") found
  clause-final pauses drop by rep 2, mid-clause pauses by rep 4, and SELF-REPAIRS only after rep 4, so a
  cap of 3 harvests the cheapest component. Thai & Boers 2015 concludes the 4/3/2 shrinking-clock
  implementation "is not the most judicious choice", and Suzuki & Hanzawa 2021 is titled "Massed task
  repetition is a double-edged sword": massing degraded articulation rate and increased verbatim
  repetition. What survives is R46 (≥3 reps) and R84 (cap verbatim at 3).
- **"Drills must hold the frame constant and swap the content slot, never the reverse."** REFUTED. de
  Jong & Perfetti 2011 excluded function words from its analysis BY CONSTRUCTION ("Only lexical words...
  were included"), so it cannot support a claim about clause skeletons and particles; the frame
  interpretation is the authors' flagged speculation. No group did a substitution drill; the winning
  condition repeated the whole speech verbatim. "Never the reverse" would forbid conjugation drills,
  which are the highest-value beginner production skill and already shipped in `srs_design.md` §2.
- **"For fluency, blocked repetition beats interleaved."** REFUTED. Suzuki 2021's two headline effects
  are non-significant (articulation rate d=0.66, p=.07; mid-clause pause d=-0.60, p=.12), the "blocked
  won 6 of 9" figure is acquisition-phase performance (the definitional signature of contextual
  interference, cited as if it were learning), there is no delayed post-test beyond 1 day, and the
  "blocked" arm is also the no-spacing arm.
- **"Massing buys pause reduction, spacing buys speed, so do both."** REFUTED. The citation is
  misattributed (the paper is Kakitani & Kormos 2024, SSLA 46(3):770-794, not "Suzuki & Hanzawa 2024")
  and its actual result is a NULL: 1-day vs 7-day spacing produced "comparable fluency gains" at 7 and 28
  days. No study cited had a massed-then-spaced arm.
- **"Correction during fluency repetitions costs fluency, so defer it to after the last rep."** REFUTED.
  No cited study manipulated feedback TIMING; Tran & Saito contrasted presence vs absence of accuracy
  enhancement, and the "costs fluency" reading compares p=.003 against p=.028 across two groups with no
  interaction test. The condition the rule would ban (4/3/2 + accuracy enhancement) is the only one that
  produced accuracy learning. What survives: do not interrupt mid-utterance while a clock runs.
- **"Cap per-lesson load at 2 interacting grammar patterns; exempt vocabulary."** REFUTED. The audited
  field is a build artifact: `patterns` is produced by substring-matching 496 grammar forms against a
  concatenated phrase string, truncated at `[:6]`, so 58 of 66 units are truncated and `arrival/unit-02`'s
  six "patterns" are all substring artifacts of three frozen greetings. The audit arithmetic was also
  wrong (2 units exceed 5, not 4; the proposed cap fails 30 of 66 units), and Morra et al. 2024 argues
  the WM number is method-dependent rather than 4. What survives is the direction, already in auditor D.5.
- **"Larger new-vocabulary sets beat smaller ones because they force within-session spacing."** REFUTED.
  Nakata & Webb 2016 tested exactly the 4-item set with spacing equated and found "as long as spacing is
  equivalent, the part-whole distinction has little effect"; Kornell 2009 never varied new-items-per-
  session, and its large effects confound stack size with between-session review. Given the daily queue
  in `srs_design.md` §3 already supplies spacing, set size is decoupled. No unit in the built path reaches
  15 words, so importing the 15-25 band as a FLOOR fails all 66.
- **"Japanese has a structurally worse frequency-coverage curve (top-1,000 = 60% vs English 80%)."**
  REFUTED on this repo's own data: top-1,000 coverage is 85.0% all-tokens / 72.4% content-only over
  248,705 Tatoeba sentences. The apparent gap is a counting-unit artifact (English word FAMILIES vs
  Japanese short-unit words), and the cited source's own comparison figures put English at 72-78%. Keep
  the ban on "com 1.000 palavras você entende 80% do japonês", on the correct warrant: coverage is not
  comprehension.
- **"Over half of all tokens are closed-class grammar, so the word budget cannot deliver coverage."**
  REFUTED as stated: 助詞 33.77% + 助動詞 13.82% = 47.58%, under half, and the headline needed pronouns to
  clear 50% while `vocab` already classifies pronouns as vocabulary. The ordering premise is also false
  (は/の/た/に/を/だ are not in `vocab` at all), and the proposed top-50 assertion would force N4 passive,
  causative and ば into stage 6, plus three pure tokenizer artifacts (ぬ, ん, てる).
- **"Points for showing up reduce intrinsic motivation."** REFUTED by its own source: Deci, Koestner &
  Ryan code "showing up" as TASK-NONCONTINGENT, free-choice d=-0.14, non-significant and homogeneous, and
  conclude such rewards "tend not to affect intrinsic motivation". The proposed replacement (points only
  for correct answers) is performance-contingent-less-than-maximum, d=-0.80, which the same paper calls
  "by far the most detrimental type of rewards". It would also punish desirable difficulty and corrupt
  FSRS's self-graded input.
- **"Unearned initial progress raises completion."** REFUTED for our case. Four of the five proposed
  seed words do not exist as corpus records and the fifth is not on the path, so the meter moves by
  exactly 0; 5/513 words is under 1% against Nunes & Drèze's 20% endowment; and marking those five
  "known" means the learner never gets the Armadilha PT correction that コップ is three moras, converting
  a documented false-friend trap (guidelines line 88) into unremediated prior knowledge.
- **"BP speakers re-encode Japanese vowel length as stress."** REFUTED as a mechanism. Richter &
  Agostinho 2017 is a lexicographic loanword study with no listeners and no acoustic measurement, its own
  lead hypothesis is vowel QUALITY (unreduced final vowels heard as stressed) rather than duration, and
  its corpus contains oxytone adaptations with zero duration cue (caratê, taiko, seppuku, bonsai). The
  derived auditor check is also vacuous: measured over 112,619 special-mora tokens in the kanjium data,
  the target mora is the accented mora in 0.83% of long vowels, 0.02% of geminates and 0.01% of moraic ん.
  What survives is already guidelines line 74: length is drilled as its own skill.
- **"The long vowel is the hardest special mora for BP learners, and they detect length only when it
  coincides with a pitch fall."** REFUTED. The pitch finding is ONE token ([seːraː]) with position and
  phrase-final lengthening perfectly confounded, from an N=4 unpublished 1987 MA thesis in the
  Contrastive Analysis framework; the production data in the same thesis shows geminate deletion
  (zassi→zasi, kootja→kotja). The derived freebie filter would delete 35.4% of classifiable long-vowel
  items including よろしい (a stage-10 seed) and the whole accented -しい class, and っ appears in 22% of
  the path's real phrases, front-loaded, so any strict ordering of the three morae is unimplementable.
- **"BP segmental errors disappear on their own; budget spent on segments past the first units is
  wasted."** REFUTED. The "advanced" group is one semester further on, the comparison is cross-modality
  (romaji dictation vs immediate imitation) and cross-population, and every informant was in a course
  actively teaching pronunciation, so the parsimonious reading is that early segmental instruction
  WORKED. The source's own persistent-difficulty list is headed by pitch accent, which the proposed rule
  omitted, and it documents ら as structurally hard in /rj/ contexts that first appear at unit 31.
- **"There is a BP confusion set English materials never mention, and Japanese question intonation
  transfers free."** REFUTED, and inverted: Joko's own contrastive section says the DECLARATIVE contours
  are the similar ones and the INTERROGATIVE contours differ (the Japanese rise is confined to the final
  mora; the BP interrogative melody rises from the start). Shipping a "Vantagem PT" telling learners
  their questions already sound right would give a false competence signal on the hardest BP→JA skill.
- **"Explicit pitch-PATTERN training pays off specifically for non-tonal L1s."** REFUTED. The
  F(1,24)=10.09 figure is a between-subjects test collapsed across time points including pre-test; the
  three-way Time × Group × L1 interaction is F(2,48)=0.97, p=.388. Training gains were IDENTICAL across
  L1s (+7.00 vs +6.82); the interaction lives in the control condition and rests on n=3. The derived
  4-way pattern item is also formally impossible for 2-mora words (nakadaka needs ≥3 morae) and
  unanswerable for heiban vs odaka in citation form. What survives is PALP's transplantable mechanics:
  withhold the audio until after the answer, and re-queue a missed item within the same session.
- **"Missing a day does not damage habit formation; planned slack raises return rate."** REFUTED. The
  cited study manipulated TIME OF DAY, not skip days (both arms were daily), and its own mechanism is
  that the flexible arm simply exercised MORE, i.e. repetition count drives persistence and skip tokens
  delete repetitions. Two skip days per week also stretches the 66-unit path to 92 days against the
  56-day trip window.
- **"Vendor-authored efficacy evidence must cap at confidence: medium."** REFUTED as an authorship rule.
  What over-claimed in the canonical case was Duolingo's marketing page, not Vesselinov & Grego's report,
  which disclosed its own attrition, dispersion and unfavourable median. An authorship cap would also
  force a silent downgrade of FSRS (whose evidence is SuperMemo/MaiMemo-derived and open-source-
  benchmarked), which is worse than no rule. The surviving version is R74-R77 in §2.12: cite the primary
  report, never mix outcome types, publish denominators.

---

## 7. Open questions and what would change our mind

### 7.1 Live contradictions with `learning_guidelines.md` (resolve before the next auditor build)

1. **Line 45, mnemonic durability.** "keyword learners can forget FASTER than rote at delay (up to ~2×
   items lost)" is unverified at 2 days (the accessible source reports 1 week) and its direction is wrong
   for a low-repetition path. See the note after R6. ACTION: soften or source.
2. **Line 31, task repetition citation.** The source list maps "Sato 2023, large speech-rate gains across
   the first 3-5 immediate repetitions" to
   [doi 10.1177/13621688231167573](https://journals.sagepub.com/doi/10.1177/13621688231167573), which is
   Boers & Faez (2023), a TBLT meta-analysis skeptical enough to conclude the field "is not ripe yet for a
   meaningful meta-analysis". ACTION: replace with Lambert, Kormos & Minn 2016 (SSLA).
3. **Auditor D.6 vs `speaking_path.md` §3.3 vs `build_speaking_path.py:36`.** ≤1 vs ≤2 vs `MAX_NEW = 3`.
   ACTION: R38, pick one and read it from the builder constant.
4. **Auditor D.9 vs any mnemonic imageability veto.** D.9 requires a pt-BR mnemonic on every kanji; 88 of
   630 N5-N3 characters have abstract glosses. ACTION: R4, add the exemption line to D.9.
5. **Auditor D.3 wording.** "first encounter... first retrieval" must become "first GRADED retrieval" for
   pretests to be legal. ACTION: R18.
6. **`speaking_path.md` §1 "only signage kanji".** The builder emits 216 distinct kanji, only 18 of them
   classic signage. ACTION: correct the prose to match the builder, or change the builder.
7. **`speaking_path.md` §4 shadowing.** Shadowing reuses the `say_now` ids, so any rule of the form
   "the check must not read aloud a shadowed sentence" is a blanket ban on controlled read-aloud checks.
   ACTION: R58 replaces that predicate; also tag shadowing `meaning-input` (R77) so it stops implicitly
   satisfying the output requirement.
8. **Line 68, "wean romaji by ~unit 3".** Marugoto (the Japan Foundation's own reference implementation)
   ships romaji at A1 with an explicit 60%-kana target. That does not overturn our rule, but it makes it a
   choice with a cost rather than an inherited default. ACTION: R62 makes it default-off-and-measured; log
   the reveal rate and revisit with our own data.

### 7.2 What would change our mind

| Question | What we would need to see | What we would change |
|---|---|---|
| Does the sparse-retrieval mnemonic advantage hold for pt-BR→Japanese? | Any study with Portuguese-L1 learners and Japanese targets, or our own A/B on the 8-week cohort | R3's keyword-availability clause becomes evidence-based rather than a design choice; the §2.1 direction note becomes a finding |
| Is the 80% desirable-difficulty gate (R22) the right floor? | A dose-response curve from our own review logs relating pre-difficulty accuracy to post-difficulty retention | replace the design-choice number with a fitted one |
| Immediate vs delayed feedback within a session (R24, UNRESOLVED) | Metcalfe, Kornell & Finn 2009 read in full against the Karpicke line, or an in-app A/B | either R24 stands or "delayed feedback within a session" joins R20 |
| Does pretesting help at all for arbitrary JP→pt-BR pairs? | A replication of Seabrooke et al. 2019 with SRS-style repeated testing rather than single-shot | if it does, R15's semantic-bridge gate relaxes and the cap in R16 rises |
| Is the strand budget (R78) right for an 8-week horizon? | Completion and per-stage can-do pass rates by strand mix across two cohorts | re-weight; the taxonomy stays either way |
| Does the 4/3/2-style paced repetition help or fossilize in an app with no interlocutor and no ASR? | Our own recordings scored for mora timing before and after | R46's paced-repetition clause, and whether R84's cap of 3 is too high |
| Does furigana fading (R30-R33) help once reading cards exist? | A reading-specific card type shipped, then a fade-on vs fade-off comparison | R31's blanket "never fade on the speaking path" could relax to the JLPT path's schedule |
| Does the streak counter tied to the due queue (R71) beat a personalised reminder? | An A/B; the only RCT evidence found personalised reminders better on the extensive margin | drop or demote the counter |
| Is pitch accent worth authoring at scale? | N3 pitch coverage extended from 0% via kanjium, then a comprehensibility rating comparison | R61 could become a broader authoring mandate rather than a minimal-pair-only requirement |

### 7.3 Data prerequisites (nothing above enforces until these land)

- `production` field emitted by `build_speaking_path.py` (blocks R43-R46, R50-R54).
- `known` snapshot disambiguated at lines 208 vs 247 (blocks R11).
- `patterns` sourced from `sentence_grammar` rather than substring matching (blocks R80, R81).
- `reading_irregular` boolean computed and stored (blocks R32).
- A bunsetsu layer over `bank.json` tokens (blocks R64).
- `can_do` on capabilities or stages (blocks R65, R66).
- Audio assets with `speaker_id` (blocks R23, R55, R63).
- `research/citations.md` with `outcome_type` and denominators (blocks R74-R77 in §2.12; ~63 incumbent
  references across 8 design docs need back-filling).
