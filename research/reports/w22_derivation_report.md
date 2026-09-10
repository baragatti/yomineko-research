# W22 — the N3 dead end, the never-unlocked features, and conjugation-form gating

_Derivation only, 2026-09-10. Nothing under `course/`, `corpus/`, `design/`, `contracts/` or `scripts/`
was edited; `db/corpus.sqlite` was copied to scratch and read there. The whole output is one file:
**`research/derived/pending/w22_n3_dead_end.json`** (261 KB, four sections, each a table an apply script
consumes and a validator replays). Every number below was produced by a script over the committed export
plus that DB copy._

Source of the finding: `research/reports/readiness/jlpt_course_path.md` **G7** (4 of 16 features ever
unlocked, `feat:jlpt-sim-n3` absent from the enum, `top:n3-revisao` is one lesson) and **G12**
(`conjugation-form` and `phrase` are `required` keys that are empty in all 322 `cumulative_known_set`
records). APP_PLAN row **W22**.

**Apply order is not free: `review_topic` → `features` → `home_lessons` → `form_unlocks`.** The feature
unlock lands on `les:n3-revisao-03`, which does not exist until the review topic is expanded.

---

## 0. Headline numbers

| | |
|---|---:|
| features in the enum / unlocked by a lesson today | 16 / **4** |
| never-unlocked features given a home by a mechanical rule | **9 of 12** |
| never-unlocked features left as residue (all infrastructure-blocked) | **3** |
| enum additions proposed — `feature` | **1** (`jlpt-sim-n3`) |
| N3 review topic: lessons today → proposed | **1 → 3** |
| conjugation forms in the enum today / with a derived home | 20 / **25** |
| enum additions proposed — `conjugation_form` | **6** (+ 1 retirement) |
| lessons that gain a `conj:` unlock | **18 of 322** |
| conjugation drills in the bank | **18,524** |
| drills reachable under the proposed gate | **18,524 (100%)** |
| drills reachable today under a form-checking gate | **0** |
| `cumulative_known_set` keys that shrink anywhere | **0** |
| export vs DB-copy cks disagreements on the five non-vocab keys | **0 of 322** |

---

## 1. `features` — the missing enum sibling and who unlocks it

**The rule, read off the two existing siblings rather than invented (R1).**
`feat:jlpt-sim-<level>` is unlocked by **the last lesson of that level's `top:<level>-revisao` topic** —
N5 by `les:n5-revisao-03` (3 of 3), N4 by `les:n4-revisao-03` (3 of 3). It is *not* the last lesson of
the level: `top:n5-kanji-exame` (order 20) and `top:n4-kanji-exame` (order 37) both come **after** the
review topic and unlock nothing. N3 has no kanji-exame topic, so there the last review lesson is also the
last lesson of the course.

**The sibling scan.** Scanning every enum in `design/unlock_enums.json` for level-suffixed families:
`feature` has exactly one — `jlpt-sim-{n4,n5}`, missing n3. `deck:vocab-*`, `deck:kanji-*` and
`deck:grammar-*` already carry their n3 member. So **`feat:jlpt-sim-n3` is the single missing sibling**;
nothing else in any enum is short an N3 value.

The addition has four mirrors that must move with it, all listed in the table:
`contracts/lesson.schema.json`, `contracts/user_state/feature_state.schema.json`,
`contracts/types.ts` (regenerated), `design/courseware_architecture.md` §5.
It is not a speculative feature: `prototype/app/lib/exam.server.ts` already declares
`LEVELS = ["n5","n4","n3"]` and all 14 N3 banks exist.

---

## 2. `home_lessons` — the 12 never-unlocked features

**The rule.**

- **H1** — the home is the **first lesson in course order whose own published JSON already uses the
  feature**, decided by a one-line detector per feature over body + exercises + unlocks. This is the rule
  `design/courseware_architecture.md` §5 already states in prose ("turns on at the first lesson that uses
  it"); W22 only makes it computable. Every row carries its detector and the exact span/exercise id that
  fired, so a validator replays it.
- **H2** — else the first lesson of the topic the feature registry names. **H2 fires for nothing.**
  Neither `design/unlock_enums.json#feature`, nor `courseware_architecture.md` §5, nor
  `product_roadmap.md` §A names a topic for any feature — the branch has no input. It is kept in the
  written rule so a later registry that does name topics slots in without a rule change.
- **H3** — else residue for the owner.

**Result: 9 by H1, 0 by H2, 3 residue.**

Two features that a naive reading would collapse are kept apart by the artifact each one consumes:
`feat:particle-drill` is the standalone trainer over `grp:particles-core` (homed where the cks first holds
**two** of its seven members — a discrimination drill needs something to discriminate against), while
`feat:find-correct-particle` is the shipped `particle_choice` item.

**Residue (3), all blocked by infrastructure, not by data:**

| feature | why | owner decision |
|---|---|---|
| `feat:listening` | 0 `listening` exercises and 0 `<audio>` elements in 322 lessons; the only audio marker anywhere is a single stray `audio="true"` on one `<sentence>` in `les:n5-te-form-01` | D3 (TTS engine/voice/licence) |
| `feat:voice-mode` | no ASR-facing artifact exists | D3 |
| `feat:visual-novel` | no VN artifact exists | — |

**One flagged row.** `feat:handwriting-input`: H1 fires at course index 122 (`les:n5-kanji-exame-01`) on a
`<stroke ref>` — but that is stroke-order **display**, not handwriting **input**, and there are **0
handwriting exercises** in the course. Meanwhile the SRS starts scheduling handwriting cards at index 5
(`les:pre-n5-hiragana-01`, `kana:hiragana-a`) and still exports **691 handwriting card instances** — 117
lessons before the feature would turn on. APP_PLAN D5's default is to retire those cards; if they stay,
the home has to be index 5 or the course keeps scheduling reviews for a mode it never turns on. Both
candidates are in the table.

---

## 3. `review_topic` — a real N3 review

**The shape, read off `top:n5-revisao` and `top:n4-revisao`, which are structurally identical (R3).**
3 lessons · each recapitulating one **contiguous block** of the level's teaching topics, in order (n5:
7–8 / 9–13 / 14–18; n4: 21–23 / 24–30 / 31–35) · `needs` a straight chain (lesson 1 needs the level's last
teaching lesson, 2 needs 1, 3 needs 2) · **zero item unlocks** on any of the three · the third and last
unlocks `feat:jlpt-sim-<level>` · **6 exercises** typed
`[recognition, recognition, cloze, cloze, sentence_build, production]` (n5-revisao-01 carries 7, swapping
the two cloze for two `particle_choice`) · 4–5 objectives · body 5.9k–8.3k chars · and the bodies render
**no `<vocab>/<kanji>/<grammar>` chips at all** — every Japanese example is a bare `<jp>` span, which is
why they pass gating with an empty unlock set.

Today `top:n3-revisao` is 1 lesson, 2,444 chars, 4 exercises, 2 objectives, 4 vocab unlocks, no feature.

**What is honestly *not* mechanical:** which topics fall in which block is a thematic choice in both
existing levels (n5 splits 2/5/5 topics, n4 splits 3/7/5 — neither is an equal third by topics, lessons,
grammar points or exercises). So the proposed boundary uses the one mechanical criterion available — the
3-way contiguous partition of N3's 14 teaching topics that **minimises the spread of lesson counts** — and
is flagged for the owner to override thematically. It comes out well-balanced and thematically coherent:

| lesson | block | topics | lessons | grammar re-tested |
|---|---|---|---:|---:|
| `les:n3-revisao-01` | discourse → time → perspective → cause | conectores, tempo, perspectiva, causa | 31 | 38 |
| `les:n3-revisao-02` | state → intention → duty → desire → limits | estado, intencao, deveres, desejos, limites | 35 | 52 |
| `les:n3-revisao-03` | emphasis → concession → conjecture → report → structure | enfase, concessao, conjectura, relato, estrutura | 34 | 42 |

Contents are given **as references, never as prose**: `retest_topics`, the full `retest_grammar_refs` for
the block, the `retest_grammar_anchor_refs` (the `is_core` member of each `grp:gram-n3-<topic>` family —
one anchor per topic, which is what the family layer already designates), `needs`, `unlocks`,
`feature_unlocks`, and an `exercise_plan` of 6 rows each naming its type and the anchor ref it targets,
cycling through the block's topics in order. Title, description, objectives, body and exercise
prompts/answers are listed in `to_author` and left empty.

Two apply-safety fields are on every row, because the existing lesson must not be flattened:
`needs_are_additive` (W21 already derived 4 `needs` edges on `les:n3-revisao-01`; add, never replace) and
`keep_existing_unlocks`.

**Residue.** `les:n3-revisao-01` is the only review lesson in the course that unlocks items — 4 N3 vocab
(`ピン`, `便`, `停留所`, `郵便`: transport/mail words with nothing to do with review). This derivation
**leaves them there**, because moving them changes published unlock ownership and the introduce-once
ledger, which is not W22's to change. Owner call: relocate to a topic that teaches them, or accept it.

---

## 4. `form_unlocks` — the rule, the 25 forms, the drill gate

### 4.1 The rule

For each conjugation form, compute up to **four** candidate lessons over the published export and take the
**earliest**; that lesson unlocks `conj:<form>` (introduce-once), and every later lesson inherits it
through the running union, so no `cumulative_known_set` can shrink by construction.

| channel | what it is | why it is trustworthy |
|---|---|---|
| **F-a** required-as-base | earliest lesson unlocking a grammar point whose `formation_steps` carries `op:"to-<form>"` — the point is **built on** the form | Layer-A structured data; 494 grammar records carry 12 distinct `to-*` ops. This is a hard **gating deadline**, the same semantics `validate_lesson_gating` already enforces for vocab/kanji/grammar refs |
| **F-b** identity anchor | earliest lesson unlocking a point that **is** the form, matched by a 15-row `form_anchor_table` against `structure_pattern` (命令形, 受身形, 意向形, 〜たら, 〜ば, …) | the table ships inside the output file, so a validator replays every match |
| **F-c** corroborated surface | earliest lesson whose body prints, inside a `<jp>` span, the **deterministic conjugation-bank** surface of the form for **≥3 distinct words already in that lesson's own cks** (or ≥2 such words inside its exercise answer keys) | the bank is rule-generated Layer B from W11's verb classes, so the surface is a fact, not a guess |
| **F-d** metadata citation | earliest lesson whose own pt-BR title/description/objectives cite the form | the lesson's own claim about what it teaches |

Two thresholds are load-bearing and were set by measuring the failure, not by taste:

- **F-c needs ≥3 words, not ≥1.** At ≥1 the imperative lands on `les:n5-verbos-02` because one body
  prints 閉めろ once. ≥3 is what separates "this lesson teaches the form" from "this lesson happened to
  print one word that is in it".
- **F-c needs a maximal-match guard.** A short surface is often a strict prefix of a longer one
  (遊べ ⊂ 遊べば, 止め ⊂ 止めば). Without the guard the imperative claimed `les:n4-condicionais-01` off
  ば-forms. With it, the imperative lands on `les:n4-volitivo-06`, the lesson whose grammar point *is*
  命令形.

Verb/adjective class comes from W11's `conjugation_class` families — `grp:godan` 311, `grp:ichidan` 156,
`grp:suru-irregular` 416, `grp:kuru-irregular` 1, `grp:i-adj` 105, `grp:na-adj` 178 — and the conjugation
bank carries the same class on every one of its 1,157 entries, which is what makes the F-c surfaces
deterministic.

### 4.2 Two enum changes the drill bank forces

The bank and the 18,524-item drill set use **23** form keys; the enum has **20** values. The crosswalk
(`bank_form_to_enum`, `formation_op_to_enum`) is published in the file. Six bank keys have no enum value,
so **2,140 drills (11.6%) could never be gated at all**:

`attributive` 168 · `adverbial` 272 · `negative_te` 884 · `polite` 272 · `polite_negative` 272 ·
`polite_past` 272.

`to-attributive` (85 formation steps) and `to-adverbial` (24) are likewise unmappable without them.
→ **proposed addition of 6 values to `conjugation_form`** (owner decision; the enum doc says adding a
value is a deliberate, documented change).

Conversely **`provisional` is the one enum value with zero producers** — 仮定形 *is* the ば form, already
in the enum as `conditional-ba`; no grammar point, no bank entry and no lesson distinguishes them.
→ **proposed retirement.** It is the only F-residue.

### 4.3 Result

**25 forms homed, 1 residue, 18 lessons gain an unlock**, final cks holds 25 forms (0 at end of pre-N5,
18 at end of N5, 25 at end of N4, unchanged through N3 — N3 introduces no new inflection, which is itself
consistent with G8's finding that N3 is vocabulary-heavy and grammar-light).

**A named cost of the rule.** F-a is a *deadline*, not a teaching. For **7 forms** the course builds a
grammar point on the form before any lesson teaches or names it, so the unlock lands on the requiring
lesson:

| form | required as a base at | first actually taught at | gap |
|---|---|---|---:|
| `dictionary` | `les:n5-desu-wa-04` | `les:n5-verbos-01` | 17 |
| `nai` | `les:n5-verbos-01` | `les:n5-adjetivos-02` | 20 |
| `ta` | `les:n5-verbos-01` | `les:n5-te-form-04` | 36 |
| `te` | `les:n5-particulas-lugar-07` | `les:n5-te-form-01` | 21 |
| `attributive` | `les:n5-particulas-lugar-08` | `les:n5-adjetivos-02` | 7 |
| `adverbial` | `les:n5-adjetivos-01` | `les:n5-adjetivos-05` | 4 |
| `potential` | `les:n4-oracoes-relativas-07` | `les:n4-condicionais-01` | 1 |

The file therefore carries **both** homes on every row and an explicit `mode` switch:

- **`gate-sound` (chosen, what `rows` and `per_lesson` hold)** — earliest candidate. Preserves the
  invariant the gate already enforces: no lesson consumes an item it has not been given.
- **`teach-true`** (`home_teach_true` on every row) — earliest teaching candidate. Pedagogically cleaner,
  but it opens exactly 7 new gating violations, which means moving those grammar points or their lessons
  first. That is W21b's forward-reference campaign, not a field flip.

A related content gap the derivation surfaced and did not paper over: **`top:n5-passado` teaches the past
of the *copula*** (でした / だった / じゃなかった), not the verb past. Nothing before `les:n5-revisao-02`
teaches 〜ました or 〜ませんでした, so those two forms — and `polite-past` — are first unlocked in a
**review** lesson. Real debt, worth an owner look alongside W25.

### 4.4 Simulation on the DB copy

| check | result |
|---|---|
| lessons in the DB copy / in the export | 322 / 322 |
| `cumulative_known_set` keys that shrink anywhere (all 6 keys, all 322 lessons) | **0** |
| `conjugation-form` monotonicity along course order | **0 violations** |
| export vs DB copy, on `kanji` / `grammar` / `kana-family` / `conjugation-form` / `phrase` | **0 disagreements in 322 lessons** |
| the `vocab` key | excluded by design — the DB holds authoring refs (`vocab:さあ`), the export holds published JMdict slugs (`vocab:1005110`), exactly as `design/lesson_schema.md` documents; they differ in all 284 lessons that have vocab |
| DB lessons with a non-empty `conjugation-form` cks today | **0** — the apply must write both layers |
| conjugation drills in the bank | **18,524** |
| drills reachable under the proposed gate (vocab ∈ cks **and** form ∈ cks) | **18,524 = 100%**, 0 unreachable |
| drills whose gate is set by the **form** rather than the word | 2,587 (14%) — these become available later than the word, which is the point of the gate |
| conjugation-bank words the course never unlocks | **0 of 1,157** |
| new FSRS cards created | **0** — `item_to_deck` maps no deck for `conjugation-form`, so `srs.introduces_cards` is unchanged on all 322 lessons |
| new `needs` edges | **0** — `validate_lesson_gating` check C is untouched |

**No drill loses gating** because none has any today: all 322 `cumulative_known_set["conjugation-form"]`
lists are empty, so a gate that checks the form admits 0 of 18,524 drills and the app can only serve them
ungated. The proposal takes that from 0 to 18,524 reachable, with none stranded.

---

## 5. Twenty sample rows

**§1 features (1)**

| # | row |
|---|---|
| 1 | `feat:jlpt-sim-n3` → `les:n3-revisao-03`, rule R1 (last lesson of `top:<level>-revisao`); evidence: n5 `les:n5-revisao-03` 3/3, n4 `les:n4-revisao-03` 3/3, n3 1/1 with no holder |

**§2 home_lessons (9 homed + 1 flag)**

| # | feature | home lesson | detector that fired | evidence |
|---|---|---|---|---|
| 2 | `feat:romaji-toggle` | `les:pre-n5-orientacao-01` (idx 0) | a `<romaji>` element in the body | `<romaji>a</romaji>` |
| 3 | `feat:furigana-toggle` | `les:pre-n5-sons-03` (idx 4) | a `<jp reading>` span over a kanji base | `<jp reading="はし">箸</jp>` |
| 4 | `feat:kana-input` | `les:pre-n5-hiragana-01` (idx 5) | a `production` exercise whose answer key is kana-only | `ex:pre-n5-hiragana-01-4` → お |
| 5 | `feat:find-correct-particle` | `les:n5-desu-wa-01` (idx 41) | a `particle_choice` exercise | `ex:n5-desu-wa-01-2` |
| 6 | `feat:phrase-builder` | `les:n5-desu-wa-01` (idx 41) | a `sentence_build` exercise | `ex:n5-desu-wa-01-4` |
| 7 | `feat:particle-drill` | `les:n5-desu-wa-04` (idx 44) | cks holds ≥2 of `grp:particles-core` | `gram:wa-topic-marker`, `gram:mo` |
| 8 | `feat:kanji-lookup` | `les:n5-numeros-tempo-01` (idx 52) | a `<kanji ref>` chip | `kanji:一` |
| 9 | `feat:find-correct-kanji` | `les:n5-verbos-01` (idx 61) | an MCQ whose choices are all single kanji | `ex:n5-verbos-01-6` |
| 10 | `feat:handwriting-input` | **flagged** — H1 `les:n5-kanji-exame-01` (idx 122, `<stroke ref="kanji:会">`, display only) vs card-based `les:pre-n5-hiragana-01` (idx 5, `kana:hiragana-a`) | — | D5 |

**§3 review_topic (3)**

| # | lesson | re-tests | needs | unlocks |
|---|---|---|---|---|
| 11 | `les:n3-revisao-01` | conectores + tempo + perspectiva + causa (31 lessons, 38 grammar; anchors `gram:n3-sono-ue`, `gram:n3-made`, `gram:n3-ni-kanshite`, `gram:n3-okagede`) | + `les:n3-estrutura-06` | keeps its 4 existing vocab |
| 12 | `les:n3-revisao-02` | estado + intencao + deveres + desejos + limites (35, 52; anchors `gram:n3-kake`, `gram:n3-uto-shita`, `gram:n3-te-goran`, `gram:n3-masu-you-ni`, `gram:n3-kurai`) | `les:n3-revisao-01` | — |
| 13 | `les:n3-revisao-03` | enfase + concessao + conjectura + relato + estrutura (34, 42; anchors `gram:n3-koso`, `gram:n3-donna-ni-temo`, `gram:n3-kanaa`, `gram:n3-to-iu`, `gram:n3-no`) | `les:n3-revisao-02` | **`feat:jlpt-sim-n3`** |

**§4 form_unlocks (7 of 25)**

| # | form | home lesson | rule | evidence | drills |
|---|---|---|---|---|---:|
| 14 | `conj:masu` | `les:n5-verbos-01` | F-b | `gram:gp-8`, `structure_pattern` ます | 884 |
| 15 | `conj:ta` | `les:n5-verbos-01` | F-a | `gram:gp-6` is built on it (`to-ta-form`; 52 points carry it) | 1,156 |
| 16 | `conj:te` | `les:n5-particulas-lugar-07` | F-a | `gram:gp-55` is built on it (`to-te-form`; 58 points) — taught 21 lessons later at `les:n5-te-form-01` | 1,156 |
| 17 | `conj:nakatta` | `les:n5-passado-02` | F-c | body prints 使う→使わなかった + ≥2 more cks words | 1,156 |
| 18 | `conj:volitional` | `les:n5-convites-02` | F-c | body prints 行く→行きましょう, 食べる→食べましょう and the answer keys repeat them | 1,768 |
| 19 | `conj:imperative` | `les:n4-volitivo-06` | F-b | `gram:gp-127`, `structure_pattern` 命令形 | 884 |
| 20 | `conj:causative-passive` | `les:n4-causativa-03` | F-b | `gram:saserareru`, `structure_pattern` ～させられる | 884 |

---

## 6. Residues and owner decisions, in one list

1. **`feat:listening`, `feat:voice-mode`, `feat:visual-novel`** — no home; blocked by D3 (TTS/ASR) and by
   the absence of any VN artifact.
2. **`feat:handwriting-input`** — display home (idx 122) vs card home (idx 5); resolves with D5.
3. **`conjugation_form` +6 / −1** — add `attributive`, `adverbial`, `negative-te`, `polite`,
   `polite-negative`, `polite-past` (without them 2,140 drills can never gate); retire `provisional` as a
   duplicate of `conditional-ba`.
4. **N3 review block boundary** — mechanically balanced 31/35/34 lessons; the owner may re-cut it
   thematically, as N5 and N4 were.
5. **The 4 transport/mail vocab on `les:n3-revisao-01`** — left in place; relocating them is an unlock-
   ownership change.
6. **`mashita` / `masendeshita` / `polite-past` first unlocked in `les:n5-revisao-02`** — because
   `top:n5-passado` teaches the copula past, not the verb past. Content debt, not a derivation artefact.
7. **`mode: gate-sound` vs `teach-true`** — 7 forms are required as a base before they are taught; the
   chosen mode keeps the gate sound and hands the 7 to W21b.
8. Noted in passing, out of W22's scope: `srs-deck` is in `unlock_type` and **no lesson unlocks any deck**
   (decks are created by their first card, per `courseware_architecture.md` §6), and `phrase` is still
   empty in all 322 cks alongside the now-fillable `conjugation-form` (G12's `deck:phrases` row).
