# design/speaking_path.md — the speaking-first path (`course/speak/`)

**Status:** design contract for a SECOND ordering over the existing corpus. Owner-requested
(2026-08-05): *"a new course path that instead of following N5→N4→N3 would be focused in zero
japanese to full N3-ish but focused in speak/talking — the most common words, phrases — to learn it
the fastest way possible for a trip, or just without focusing on JLPT."*

Chosen shape (owner selected from options): **frequency + survival scenarios**.

---

## 1. What this is, and what it is not

It is a **re-ordering, not a second corpus.** Every unit references `corpus/` by stable ID exactly
like `course/`, and embeds nothing (CLAUDE.md, two-layer architecture). A sentence still lives once,
dissected once. If a word's gloss is fixed in `corpus/vocab`, both paths get the fix for free.

| | `course/` (JLPT path) | `course/speak/` (this) |
|---|---|---|
| ordering axis | exam syllabus, pre-N5 → N5 → N4 → N3 | what you need to **say** soonest |
| success test | passes the exam | handles the situation out loud |
| kanji | full production, per level | **recognition only**, never written |
| stopping point | mid-level = incomplete | **every stage is meant to be a usable stopping point** |
| grammar order | by level | by whether it lets you vary a phrase you already say |

Both paths stay. This is for the learner with a trip in eight weeks; the JLPT path is for the
learner with an exam in December.

**"Every stage is a usable stopping point" is the goal, not yet a measured property of what ships** —
the same correction §5 already carries about the survival cores. Eleven of the twelve stages declare
no survival core (§5); no stage is inside R78's strand budget (§6a); `arrival` teaches four ways to
apologise for a delay and two ways to say good morning (§6b), and is never said again after week one
(§6c). What the ordering *does* satisfy is the constraint the sentence is really about: no stage
depends on a later one, which is what makes stopping possible. The three sections below measure the
distance from possible to usable, and each now has a gate.

## 2. The two ordering axes

**Primary — scenario need.** Twelve stages, each a situation the learner must survive. Ordered by
when a traveller actually hits them: you greet people and read prices before you discuss opinions.
A learner who stops after stage 4 can still land, eat, buy, and navigate. That property is the whole
point and it is a hard constraint on stage ordering — no stage may depend on a later one.

**Secondary — frequency.** Within and across stages, vocabulary is introduced in ascending
`vocab.freq_rank` (see `scripts/ingest/build_frequency.py`: a Layer-A count over 248,705 CC-BY
Tatoeba sentences, 2.48M tokens). This is what makes the path *fast* rather than merely *thematic*:
early effort goes to words with the highest expected return per minute.

The axes conflict, and scenario wins. 財布 is far rarer than 場合, but you need it at the till and
not in week one of an exam course. Frequency then decides the order *inside* the scenario, and
decides which of two equally-relevant words is taught first.

## 3. Selection rules (mechanical and auditable)

Everything below is computed by `scripts/export/build_speaking_path.py`. No hand-picked lists beyond
the seed lexicons in §5, so the path can be rebuilt and diffed.

Rules 7-9 carry **R-numbers continuing `learning_science.md`'s series** (which ends at R84), so an
auditor grepping for `R85` finds exactly one definition. They are enforced in
`build_speaking_path.py`, not merely described here.

1. **Phrases are real.** A unit's `say_now` phrases are drawn from the sentence bank with
   `ai_generated = 0` (real human-written Tatoeba/JEC text) preferred; generated sentences fill only
   when a scenario is otherwise empty, and stay marked. Spec §1.2, selection over generation.
2. **Scenario match.** A sentence belongs to a stage when one of its tokens carries a term from that
   stage's seed lexicon (§5) as its **lemma**; seeds of 4+ characters may also match as a substring,
   which is how frozen expressions the analyzer shreds (すみません → すみ+ませ+ん) still find their
   sentences.

   Matching anything looser has failed twice, and both failures shipped. Raw substring matching put
   夕食は**いり**ません ("I don't need dinner") in the greetings stage on the seed はい. Matching the
   token **surface** as well as the lemma was the fix for that and was still wrong: it put three
   footwear sentences in greetings (彼は赤いズボンをはいていた, スリッパをはいてください,
   それより他の靴をはいてみたいのですが) because 履く's te-form is written はいて and tokenises to the
   surface はい with the lemma はく. A surface is whatever inflection the sentence happened to use;
   only the lemma says which word it is.
3. **i+1 load.** A sentence qualifies only if the number of its words *not* in the cumulative known
   set is **≤ 3** (`MAX_NEW`), and a unit may not stack six such sentences: the budget is recomputed
   against what the unit has already introduced. The known set grows as units are completed, exactly
   like `course/`'s `cumulative_known_set`.

   This section said ≤ 2 and `learning_guidelines.md` D.6 says ≤ 1, while the builder used 3 — three
   numbers for one constant, so an auditor written against either doc failed every unit
   (`learning_science.md` R38). Resolved in favour of 3. D.6 governs **authored** lessons, where the
   sentence is written to fit the budget; this path **selects** real human-written sentences and cannot
   rewrite them, so a tighter budget does not make units gentler, it makes them synthetic. Measured at
   2, the builder exhausted the qualifying real sentences and fell back on generated filler, costing the
   path its 100%-real property and 62 vocabulary items. Selection over generation (§1.2 of the corpus
   spec) outranks the rounder number.
4. **Vocabulary order.** Candidate words for a stage = words appearing in that stage's qualifying
   sentences, sorted by `freq_rank` ascending, `level` ascending as tiebreak.
5. **Grammar.** A grammar point enters a unit only when one of its `forms_json` forms actually
   occurs in that unit's phrases — the learner meets a pattern because they are about to say it,
   never because a syllabus says so. Spoken registers sort first.
6. **Nothing is invented.** If a stage cannot be filled to target from the bank, the builder emits a
   short unit and records the shortfall in the manifest. A thin stage is a visible data gap to fix
   by mining more Tatoeba, not something to paper over with generated sentences.
7. **R85 — no stage quotes one exercise.** At most **4** `say_now` phrases per stage may be selected
   while 4 or more of that stage's existing picks already sit within **±200 consecutive source ids**
   of the candidate. Tatoeba carries whole textbook exercises as consecutive id runs, and one of them
   — `sent:tatoeba-84114`…`84243`, "the room" — supplied **25 of `lodging`'s 36 slots**: 部屋には家具が
   ４点あった, 部屋には何人の少年がいますか, 部屋に入ったらドアを閉めなさい. Third-person descriptions
   and commands to a child; a hotel guest says none of them, and the stage's own seeds 泊まる, トイレ,
   風呂 appeared in zero phrases. Contiguity is the machine-checkable signature of quoting one exercise
   instead of sampling the language. The cap is evaluated per candidate, so a long chain of picks
   spaced just over the window can still cluster slightly above 4; measured worst case after the rule
   is 6 of 36 (`time_plans`), against 25 before.
8. **R86 — punctuation is not a phrase.** Two bank sentences whose Japanese is identical once
   punctuation and spacing are stripped are **one phrase** and compete for **one** slot, path-wide.
   おはよう！ and おはよう。 are the same thing said out loud, and `arrival` spent **8 of its 36 slots**
   teaching four greetings twice over; `politeness-01` taught おめでとうございます。 and
   おめでとうございます！ side by side. The duplication propagated: `arrival-03` shipped two production
   items with the identical prompt "Bom dia!". This path is scored on speech, where the difference is
   inaudible.

   **Status, measured 2026-09-02: R86 holds — 0 punctuation-normalised duplicate groups across all
   432 phrase slots — and it is a hard gate now rather than a builder-only rule
   (`scripts/validate/validate_speak_duplicates.py`).** It is also the weakest possible version of
   its own argument, and §6b measures what it cannot see: 24 pairs of same-stage phrases a listener
   hears as one utterance, 13 of them in `arrival`.
9. **R87 — the survival core outranks frequency.** A stage may declare a small set of **survival
   terms**: the phrases it exists to teach. They sort ahead of the frequency ranking (still behind
   real-over-generated, still under the same i+1 budget), and inside that bucket **shortest first**, so
   the bare canonical act leads the stage. §2 already said scenario beats frequency when they conflict;
   nothing in the code enforced it, so the sort quietly overruled the stage title. `shopping`, titled
   *"Isto, aquilo, quanto custa"*, is the proof: いくらですか？ (`sent:tatoeba-5332`) matched its いくら
   seed from the first build, but 幾ら has `freq_rank` 4100, so it lost all 36 slots to commoner words
   and the stage taught あれはキジです ("that is a pheasant") and **never a price question in 36
   phrases** — while the same sentence served as a grammar drill in four other stages.

   Survival terms are written as **phrases** wherever the bare word is ambiguous. Bare いくら was tried
   and promoted the concessive frame instead (いくらお礼を言っても言い切れない, いくら考えても、わかり
   ません — いくら…ても is a different word wearing the same spelling); 円 was tried and promoted the
   foreign exchange desk (ドルは円に対して下がった). The plain words stay in the seed lexicon, where
   frequency ranks them like anything else.

### 3a. Ranking the already-known material (`production`, `fluency`)

Not new rules — this is how `build_speaking_practice.py` chooses **among** the material R44 and R79
already permit, and it is written down because the obvious shortcut is wrong in a way that has now
been tried twice.

`production` and `fluency` may only use phrases modelled in an **earlier** unit. At a stage's opening
unit that means nothing from the new stage exists yet, so both blocks fill from the previous scenario:
`health-01` told the learner to explain what hurts and then asked them to produce *"Quando foi a última
vez que você cortou o cabelo?"*. Own-stage share was 0/6 fluency and 0/3 production in **every**
non-first stage.

**The tempting fix — letting the unit's own `say_now` in — is wrong for both blocks.** R79(a) wants
already-known material, and a sentence met sixty seconds ago is still being acquired; R44 forbids
production being an item's first retrieval and fixes the order model → recognition/checkpoint →
production, while the unit template schedules `production` *before* `checkpoint`, so a same-unit item
is exactly the first retrieval R44 names. `validate_speaking_path.py` rejects both, and it is right to
(commit 92b833c5).

So the rule holds and what moves is everything around it:

- **`fluency`** keeps strictly prior-known items, and the **prompt** stops lying: a block with nothing
  from its own stage is `kind: "recap"` and says so, instead of presenting the new stage's situation.
  A unit also may not reopen with its predecessor's list in the same order — the previous unit's items
  go to the back of the queue, never out of it, since starving a block below six would break R79(d) to
  fix the smaller problem.
- **`production`** keeps strictly prior-known items and re-ranks them by **relevance to the situation
  the learner is now in**: own-stage phrases, then earlier phrases carrying one of this stage's seeds,
  then the rest by recency. Each item records which it is (`kind`: `same-stage` / `on-topic` /
  `review`) so the app can label a carried-over item as review. `health-01` now produces
  今日はちょっと頭が痛いの; 26 of the 33 stage-opening items are on-topic, against 0 before.

## 4. Unit shape

A unit is deliberately small — one sitting, speech-first:

```
say_now        5–8 sentence IDs. The things you can use today, out loud.
chunk_phrases  the subset of say_now taught whole (see §3 note on set expressions).
words          vocab IDs introduced here, frequency-ordered.
patterns       grammar IDs whose forms occur in say_now.
checkpoint     exam-bank item IDs, with distractors re-drawn from the known set.
               See §7 — this is how the JLPT bank feeds the speaking path.
shadowing      the same sentence IDs, flagged for audio (audio: "pending" until the
               owner's voice-over pass — see design/listening.md).
production      pt-BR prompt → Japanese answer, drawn ONLY from prior units (R44) and
               string-gradeable (R45). Each carries `kind` — same-stage / on-topic /
               review — see §3a.
fluency        ≥6 already-known sentence IDs under a situational prompt with a speed
               target (R79). `kind: "recap"` when nothing in it comes from this stage.
drills         per surviving `pattern`, 3 known-set example IDs (R80/R81); a pattern
               that cannot find 3 is demoted to `patterns_chunked`.
kanji_recognition  every kanji appearing in the unit's phrases, capped at 6. RECOGNITION
               ONLY — this path never asks the learner to write kanji. It was named
               `signage_kanji` and described here as "入口 出口 男 女 駅 円 …", which was
               untrue: the field holds 227 distinct kanji across the path (counted over the
               72 exported units, 2026-09-02; this said 212), of which about 18 are classic
               signage. Renamed to say what it contains.
```

`production`, `fluency` and `drills` were added by `build_speaking_practice.py` after this section was
first written; the paragraph that used to stand here said `drills` had never been generated, which
stopped being true. `drills` is not the substitution drill originally sketched (one slot of a `say_now`
phrase swapped for other known vocab): it is R80's pattern test — a pattern that cannot show 3 distinct
known-set examples is not a pattern in this unit and moves to `patterns_chunked`. A genuine substitution
drill, the only component that would make the learner produce a *novel* sentence aloud, is still unbuilt.

`needs_review: true` on every unit: sequencing is Layer C.

## 5. The twelve stages

Approximate JLPT bands are shown for orientation only — **the path never gates on them.**

| # | Stage | Slug | Seeds (excerpt) | ≈band |
|---|---|---|---|---|
| 1 | Chegar e cumprimentar | `arrival` | こんにちは ありがとう すみません はい いいえ お願い はじめまして | pre-N5 |
| 2 | Isto, aquilo, quanto custa | `shopping` | いくら 買う 円 店 これ 安い 高い お金 をください 会計 レジ | pre-N5/N5 |
| 3 | Comer e beber fora | `eating` | 食べる 飲む おいしい レストラン 注文 水 お茶 ご飯 | N5 |
| 4 | Chegar aonde você quer | `getting_around` | どこ 駅 行く 左 右 近く 道 電車 バス | N5 |
| 5 | Dormir e resolver problemas | `lodging` | ホテル 部屋 泊まる 鍵 予約 トイレ 風呂 | N5 |
| 6 | Falar de você | `about_you` | 名前 出身 仕事 住む 好き 趣味 家族 | N5 |
| 7 | Quando, que horas, combinar | `time_plans` | 明日 今日 時 曜日 約束 会う いつ 分 | N5/N4 |
| 8 | Emergência e saúde | `health` | 痛い 病院 薬 医者 熱 大丈夫 助ける | N4 |
| 9 | Contar o que aconteceu | `past_stories` | 昨日 行った 見た 楽しかった 初めて 経験 | N4 |
| 10 | Pedir, oferecer, agradecer com jeito | `politeness` | いただく くださる よろしい 申し訳 恐れ入り | N4 |
| 11 | Dizer o que você acha | `opinions` | と思う から でも たぶん かもしれない 方が | N4/N3 |
| 12 | Conversa de verdade | `real_talk` | らしい そうです ば たら のに ながら わけ | N3 |

Full seed lexicons live in the builder, not here, so they stay executable rather than drifting from the
prose. **The survival cores of R87 do not exist per stage yet.** `SURVIVAL_SEEDS` in
`scripts/export/build_speaking_path.py` holds exactly **one** entry — `shopping`, with 8 terms
(いくらですか / いくらぐらい / これをください / それをください / あれをください / 値段 / 会計 / レジ)
— and the other **eleven stages have none**, so in those eleven the frequency axis still decides the
whole stage, which is the failure R87 was written to stop. Reading this section as "each stage declares
its core, the list just lives in code" is wrong; writing the eleven missing cores is a queued unit
(readiness G2). The R87 example itself is only half-fixed: `shopping` now leads with a price question,
but あれはキジです (`sent:tatoeba-229742`, "that is a pheasant") is **still shipped** in
`speak:shopping-03` (checked in the export, 2026-09-02).

**`ください` vs `をください`.** Bare `ください` was a `shopping` seed once and filled the whole stage with
〜てください drills ("close the door", "wait here") — the polite imperative on a *verb*, which is not
shopping. `をください` is the other construction entirely: ask for an **object**, それをください. A seed
that appears in every other sentence selects for the seed, not the theme; the same mistake put
obligation forms in `getting_around` via 行く.

## 6. Known gaps (re-measured 2026-09-02 against the exported bank)

Real-sentence yield per stage — sentences in `corpus/sentences` with `ai_generated: false` whose token
lemmas hit one of the stage's seeds (or whose Japanese contains a 4+ character seed), i.e. the same
`seed_hit` rule the builder uses, run over the **5,889-sentence bank (3,676 real)**:

```
arrival  48   shopping 277   eating 115   getting_around 129
lodging 140   about_you 99   health  50   time_plans     263
past_stories 90   politeness 87   opinions 82   real_talk 131
```

Every figure in this block moved. It previously read "the current 5,565-sentence bank (3,352 real)"
with `lodging 18` and `health 38` named as the thin stages, and said the mining fix was "queued rather
than done". **The mining happened**: 324 sentences carry the `mined` tag and are stage-tagged
`lodging` 111, `opinions` 108, `past_stories` 105, which is what took `lodging` from 18 to 140.

The thin stages are now **`arrival` (48)** and **`health` (50)** — both below the next-thinnest by a
wide margin, and `arrival` is the *first* stage a learner meets. Mining them to parity is the same
`raw_tatoeba_sentence` / `raw_tatoeba_translation` pass (248,705 sentences and 285,215 translations
already ingested and licensed) that produced the 324, and it still needs a pt-BR authoring pass
(Layer B) per new sentence. All twelve stages currently fill all 36 `say_now` slots, so the shortfall
no longer shows up as short units — it shows up as thinner choice behind the same slot count.

**This gap did not stay visible, which is why R85 exists.** The builder filled all 36 `lodging` slots
anyway, 25 of them from one contiguous "the room" id-run — a thin stage papered over with a textbook
exercise instead of reported as thin. R85 caps that at source; the honest remedy is still the mining
pass, and the remaining `lodging` phrases still lean on `coverage`/`mined` tags rather than on things a
guest says. Content quality inside a stage is a review queue, not something selection alone can fix.

### 6a. R78's strand budget: no stage is inside it (`validate_speak_strands.py`)

`learning_science.md` **R78** declares the budget as a constant and requires each stage to sit within
**±10 points of 15/30/25/30** (meaning-input / meaning-output / language-focused / fluency). Nothing
enforced it until W34: `validate_speaking_path.py` checked that the histogram sums to 100 and never
what it summed to. Recomputed 2026-09-02 from the components each unit actually holds (`say_now` +
`shadowing` / `production` / `words` + `patterns` + `kanji_recognition` + `checkpoint` + `drills` /
`fluency.items`), 3,378 components over 72 units:

```
stage             input  output   lang    flu    worst    out of band
budget               15      30     25     30        —              —
arrival            29.8     6.2   52.9   11.2   27.9pt          4 of 4
shopping           28.6     7.1   50.0   14.3   25.0pt          4 of 4
eating             25.4     6.4   55.5   12.7   30.5pt          4 of 4
getting_around     25.0     6.2   56.2   12.5   31.2pt          3 of 4
lodging            24.1     6.0   57.9   12.0   32.9pt          3 of 4
about_you          24.8     6.2   56.6   12.4   31.6pt          3 of 4
time_plans         26.7     6.7   53.3   13.3   28.3pt          4 of 4
health             25.4     6.3   55.6   12.7   30.6pt          4 of 4
past_stories       25.4     6.3   55.6   12.7   30.6pt          4 of 4
politeness         22.9     5.7   59.9   11.5   34.9pt          3 of 4
opinions           25.4     6.3   55.6   12.7   30.6pt          4 of 4
real_talk          25.0     6.2   56.2   12.5   31.2pt          3 of 4
path-wide          25.6     6.3   55.6   12.5
```

**Twelve of twelve stages are out of band, on three or four of the four strands.** Meaning-output —
the learner opening their mouth, which is the entire premise of this path — runs at **6.3% against a
budget of 30**, and language-focused runs at 55.6% against 25. R77's own diagnostic in the same file
says "Duolingo is ~80% language-focused" as a reason to distrust a product; this path is at 55.6%.
The mechanical cause is that every unit gets exactly 3 production items against 6 phrases, 6 fluency
items and 2-5 drills of 3 examples each, so the fix is upstream of the histogram: more prior-known
material per stage (§6, the mining pass) is what lets `build_speaking_practice.py` emit more than 3.

Two numbers here differ from the readiness audit's, and the difference is the finding. The audit read
each unit's shipped `strand_counts` and got a path-wide meaning-output of 7.1%; recomputing from the
components gives 6.3%, because `build_speaking_practice.py` includes `len(u["checkpoint"])` in the
field it writes but runs **before** `build_speaking_checkpoints.py` writes any checkpoints. **71 of
the 72 units therefore ship a `language-focused` count short by exactly their own checkpoint items —
365 components the manifest histogram does not know about.** The validator recomputes rather than
reads, and ratchets that disagreement at 71 so the rebalance has a counter to drive to zero.

### 6b. Near-duplicates above R86: 24 pairs, 13 of them in `arrival` (`validate_speak_duplicates.py`)

R86 (§3.8) holds at zero and cannot see this class. Two `say_now` phrases in the same stage are
counted as near-duplicates when

    mean( ratio(jp_a, jp_b), ratio(pt_a, pt_b) )  >=  0.72

with `difflib.SequenceMatcher`, the Japanese stripped by R86's own punctuation class and the pt-BR
NFKD-folded, lowercased, accent-dropped and reduced to `[a-z0-9]`. Both halves are needed, and this
corpus shows why either alone fails: おはよう vs おはようございます scores 0.615 on Japanese with an
*identical* pt-BR prompt, while 教えてくれてありがとう vs 来てくれてありがとう scores 0.857 on
Japanese with translations that differ by a verb.

```
arrival 13   shopping 4   health 2   eating 1   getting_around 1
time_plans 1   past_stories 1   real_talk 1   (lodging, about_you, politeness, opinions: 0)
```

`arrival`'s 13 are two clusters and nothing else: four ways to apologise for a delay (長い事お待たせ
してすみません / 長くお待たせしてすみませんでした / こんなに長い間待たせてすみません / 長い間、お待
たせしてすみませんでした — three sharing the identical pt-BR prompt) and four 〜てくれてありがとう
variants. Meanwhile the stage teaches neither はじめまして nor よろしくお願いします, neither of which
is in the bank at all (readiness G5). This is a 75% take rate — 36 slots drawn from 48 candidates —
showing up as redundancy rather than as a shortfall, which is the same failure mode R85 was written
for. The remedy is the `arrival`/`health` mining pass, not a tighter selection rule; the pair list is
the work list at `research/reports/speak_near_duplicates.json`.

### 6c. R83's spiral: `arrival` is met in week one and never said again (`validate_speak_spiral.py`)

**R83** — "every stage 1-6 seed lexicon must reappear in at least one stage 7-12 unit". Measured over
the three surfaces a late unit can re-present early material on (216 `say_now` slots, 216 `fluency`
slots, 468 `drills` example slots across stages 7-12):

| stage 1-6 | `say_now` | `fluency` | `drills` | late units reached |
|---|---|---|---|---|
| **arrival** | **0** | **0** | 11 | 7 |
| shopping | 11 | 8 | 31 | 27 |
| eating | 5 | 8 | 22 | 20 |
| getting_around | 4 | 1 | 12 | 12 |
| lodging | 3 | 2 | 1 | 5 |
| about_you | 4 | 13 | 10 | 15 |

R83 as written is satisfied by all six, `arrival` included — 11 drill examples is "at least one stage
7-12 unit". Read per surface it plainly is not: **the greeting, thanks and apology lexicon, the most
reusable material on the path, reaches 0 of 216 late phrase slots and 0 of 216 late fluency slots**,
and survives only as grammar evidence the learner reads. That is why the three counts are frozen
separately rather than summed — summing them turns the finding into coverage. Seeding the late stages
is Size M and depends on nothing.

## 7. How the exam bank feeds this path

The path does not feed the **simulator** (`design/exam_simulator.md` samples whole JLPT papers and is
not part of this route), but it does reuse the **bank**. Bank items carry the same corpus IDs the path
does, so they join without any new authoring:

Counts below are `checkpoint[].via` over the 72 exported units, recounted 2026-09-02 (the table read
120 / 177 / 24 before, from an earlier build):

| Link | Meaning | Count |
|---|---|---|
| `phrase` | the item is built from a phrase this unit just practised | 125 |
| `new-word` | the item tests a word this unit introduces | 196 |
| `review` | spaced review of a word from the cumulative known set | 44 |
| | **total checkpoint items** | **365** |

Type selection follows what the path is for, not what the bank offers. `orthography` is excluded
outright: it asks the learner to produce kanji, and this path is recognition-only. `reading_comp` and
`text_grammar` are excluded as a different skill. `listening_*` waits for audio. What remains is
ordered production-first, `sentence_order` before `context_fill` before recognition formats, capped at
two per format so no unit is monotonous.

**Distractors are re-drawn from the learner's known set**, not taken from the bank. Two reasons. The
bank draws wrong answers from the whole level, so requiring them to be known yielded 134 usable items
against a 396 target and left 11 units with none. And it is the better question: a distractor the
learner has never seen is eliminated on sight as unfamiliar, so the item ends up testing novelty
detection rather than meaning. The stem and the correct answer still come from the audited bank item.

A learner who later wants the certificate switches to `course/` with most of the vocabulary already
known, and the bank items they have already seen are the same ones the simulator draws from.
