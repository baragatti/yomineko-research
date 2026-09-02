# Readiness: `speak_fast_path` — the speaking-first path (`course/speak/`)

**Audited 2026-09-02.** Every number below was recomputed from the committed export
(`corpus/`, `course/`, `contracts/`), never quoted from a document. Where a design doc and the data
disagree the disagreement is named and adjudicated. `db/corpus.sqlite` was read only to confirm which
fields exist there and not in the export.

Scope: `course/speak/` (12 stages, 72 units), `design/speaking_path.md` R1–R9 / R85–R87,
`contracts/speak_path.schema.json`, `contracts/speak_unit.schema.json`,
`scripts/validate/validate_speaking_path.py`, `scripts/export/build_speaking_path.py`,
`build_speaking_practice.py`, `build_speaking_checkpoints.py`, and the prototype routes
`prototype/app/routes/speak.tsx` / `speakUnit.tsx`.

**Headline:** the *typed* speaking path is structurally finished and genuinely well gated. The *spoken*
one does not exist at any layer — no audio field on a sentence, no assets, no ASR, no pronunciation
model. And the content inside the finished structure is not yet the content a traveller needs: the
path is 62% casual-register, 12% questions, and teaches 4 of 36 canonical survival utterances.

---

## 1. What this capability needs from the data

A "learn to speak as fast as possible" path, as the owner described the product, needs six things from
the corpus. They are listed in dependency order.

**1.1 A situation-ordered index over the corpus.** Stages, units, and per-unit references to sentences,
vocabulary and grammar by stable ID, never embedded. Entities: `speak_path`, `speak_unit`. Links:
`say_now → sent:`, `words → vocab:`, `patterns/patterns_chunked → gram:`, `checkpoint → exam-bank id`.

**1.2 Utterances, not sentences.** A phrase qualifies for `say_now` only if a learner would plausibly
*say* it in that situation. This needs three fields the corpus does not have: a **speech-act** signal
(question / request / statement / narration), a **register** signal (casual / polite / keigo /
written / archaic), and an **appropriateness** flag (the A8 blocklist). Today all three are inferred,
by a lemma match against a seed list, from Layer-A Tatoeba text written for no scenario at all.

**1.3 A production loop the learner can actually close.** `production[]` with `prompt_pt`,
`answer_key`, `accepted_variants` and a grading contract; plus an input modality a pt-BR learner has
(kana IME, romaji, or speech).

**1.4 Audio, both directions.** Model audio per **sentence** (`audio_ref` + `audio_source`, declared in
`design/schema_v2.md` line 128 and absent from the shipped contract), and a learner-attempt channel:
an ASR target, a scoring contract, and a per-attempt record. `design/learning_science.md` R52 already
legislates how ASR feedback must behave, so the rule exists ahead of the data.

**1.5 Memory.** The product is "Duolingo with integrated Anki (FSRS-6)". A speak unit must emit SRS
cards and file them into a deck, the way `course/` lessons emit `srs.introduces_cards`.

**1.6 Assessment.** Per-unit checkpoints (built), plus a stage-level "can you survive this scenario"
test and a path-level placement, since `design/exam_simulator.md` §7 explicitly excludes this path from
the JLPT simulator.

---

## 2. What exists today, verified

### 2.1 The structure, and it is real

`python scripts/validate/validate_speaking_path.py` → **72 units, 432 phrases, 365 checkpoint items,
0 FAIL, 1 warn.** Recomputed independently:

| thing | count | where |
|---|---|---|
| stages / units | 12 / 72 | `course/speak/course.json`, `course/speak/*/unit-*.json` |
| `say_now` refs | 432, all distinct, 0 reused across units | recomputed |
| real vs generated `say_now` | 431 real / 1 generated (`sent:gen-1d921e8b2ad3`, この間は本当にありがとう) | `corpus/sentences/bank.json` provenance |
| vocabulary introduced | 581, each introduced exactly once | recomputed |
| production items | 213 (3 in every unit but `arrival-01`) | recomputed |
| fluency items | 423 across 71 blocks | recomputed |
| drills / patterns kept / chunked | 251 / 251 / 173 | recomputed |
| checkpoint items | 365 — `phrase` 125, `new-word` 196, `review` 44 | recomputed |
| checkpoint formats | `context_fill` 142, `kanji_reading` 142, `sentence_order` 72, `paraphrase` 9 | recomputed |
| `audio` | `"pending"` in 72 of 72 units | recomputed |

`course.json.totals` matches all eleven recomputed counters and `shortfall` is genuinely empty. The
manifest is a true statement about the units on disk.

### 2.2 The rules that hold

Verified against the data, not the prose:

- **R86 (punctuation is not a phrase)** — 0 punctuation-normalised duplicate phrases path-wide.
- **R85 (no stage quotes one exercise)** — worst 200-id window now holds 4 phrases (`arrival`,
  `shopping`, `lodging`, `time_plans`, `health`), down from the 25-of-36 `lodging` block the rule was
  written for.
- **Rule 3 (i+1, `MAX_NEW = 3`)** — 0 of 432 phrases exceed the budget. Distribution 0/1/2/3 new words
  = 13 / 229 / 121 / 69. **No validator enforces this**; it holds because the builder is correct.
- **§3a (production/fluency ranking)** — verified exactly as documented: 26 of the 33 stage-opening
  production items are `on-topic`, 12 fluency blocks are honestly labelled `kind: "recap"`, and no two
  consecutive fluency lists are identical (mean overlap 0.04).
- **Kanji is recognition-only** — 204 of 213 production answers contain kanji and **all 204** accept a
  kana-only answer, with the kana matching the bank's own reading.
- **QA findings F1 and F2 are genuinely fixed.** Re-derived the orthographic kana (token readings,
  particle は/へ keeping their surface, `split_mode == "C"` only): **0 of 96** affected items still
  reject the correct spelling. **0 of 12** fullwidth answer keys lack a halfwidth-accepting variant.

### 2.3 What guards it

`scripts/validate/validate_speaking_path.py` is one of the stronger validators in the suite. It gates:
dangling refs in every block; unit id/stage/order agreement; `cumulative_known_vocab` monotonicity;
R44 (production modelled earlier), R45 (graded), R79 (fluency prior-known, prompt, speed target),
R80/R81 (3 examples per pattern or demotion), R77 (histogram sums to 100); the embed allowlist plus
byte equality of `answer_key`/`prompt_pt` against their bank source; kana acceptance; checkpoint
type/level/`via` agreement and distractors drawn from the known set; every manifest counter; orphan
unit files. It reads the export, never the DB.

### 2.4 The app surface

`prototype/app/routes/speakUnit.tsx` renders phrases, words, patterns, drills, production (typed,
server-graded, key never sent to the client), fluency and checkpoint. `gradeProduction` in
`prototype/app/lib/speak.server.ts` accepts `accepted_variants` plus a punctuation-stripped fallback.

---

## 3. Gaps

### G1 — There is no sentence-level `register`, so nothing can tell a polite request from a Bible verse

**Missing.** `contracts/sentence.schema.json` has 16 properties and none of them is `register`;
`provenance` carries 8 keys and none is register either. `vocab.register` exists as an enum
(`archaic|colloquial|familiar|honorific|humble|polite|slang|vulgar`) but is a JMdict-misc word-level
tag, not a sentence-level one. `design/schema_v2.md` never gave the sentence one.

**Why it matters.** This path is 12 units of politeness away from a traveller who will speak almost
exclusively to strangers, and the register mix is the wrong way round. Measured over all 432 phrases:

| | plain/casual | polite (です/ます) | keigo | questions | requests | 3rd-person narration |
|---|---|---|---|---|---|---|
| path-wide | **270 (62.5%)** | 155 | 7 | 53 (12%) | 50 (12%) | 47 |
| `eating` | 26 | 9 | 1 | 6 | 3 | 3 |
| `health` | 26 | 10 | 0 | 3 | 1 | 6 |
| `getting_around` | 22 | 13 | 1 | 10 | 2 | 5 |
| `politeness` | 7 | 27 | 2 | 5 | 25 | 0 |

A learner who finishes `eating` has been modelled 26 casual utterances and 9 polite ones for a
situation that is a transaction with a stranger. Nothing in the data records that, so nothing can warn
the learner, sort for it, or filter on it.

**Size L** (S for the schema, L for populating 5,889 sentences). **Depends on** the owner fixing the
value set in `design/schema_v2.md` — A8 is already decided in principle ("A8 → yes"), the enum is not.
**AI-authorable** once the enum is fixed; JMdict misc tags plus token-level auxiliary analysis
(です/ます/でございます/だ) cover most of it mechanically, and a teacher signs off the boundary cases.

### G2 — R87's survival cores exist for one stage out of twelve

**Missing.** `scripts/export/build_speaking_path.py` defines `SURVIVAL_SEEDS` for **`shopping` only**.
`design/speaking_path.md` §5 says "the per-stage survival cores of R87 live in the builder", which
reads as if all twelve have one. Eleven do not.

**Why it matters.** R87 was written because `shopping` "never asked a price in 36 phrases". The fix
worked *for shopping* — `shopping-01` now opens with いくらですか？ and それをください. Every other
stage still sorts by frequency alone, and it shows: `health` opens with 医者なら誰でも君に禁煙するように言うだろう
("any doctor will tell you to quit smoking") and 彼は医者として無能だ ("he is incompetent as a doctor")
and never teaches 助けて or 救急車を呼んでください.

**Size M.** **Depends on** nothing (a builder edit plus a rebuild). **AI-authorable** — the frames are
mechanical; a teacher should review the list once.

### G3 — 320 of the 752 sentences the learner reads never pass through any selection rule

**Missing.** The path exposes **752 distinct sentences** in 1,821 exposures. Only the 432 `say_now`
phrases go through seed matching, R85, R86, R87, the i+1 budget and real-over-generated. `production`
and `fluency` are constrained to prior `say_now` (validator-enforced, 0 leaks). **`drills[].examples`
are not**: 361 distinct drill sentences, **320 of which are never modelled as a phrase**, drawn straight
from the corpus by known-set membership. **52 of those 320 are AI-generated**, against the path's
advertised 431/432-real property.

This is where the A8 content lives. `痔があります。` ("I have hemorrhoids") is a drill example in
`shopping-01`, `lodging-01`, `lodging-04` and `past_stories-02`. `どいつもこいつもばかばっかりだ。`
("every last one of them is an idiot") drills in `arrival-06` and `shopping-01`.
`彼女は殺されたという話しだ。` drills in `getting_around-06`.

**Why it matters.** Any content policy applied only to `say_now` will miss 43% of what ships.

**Size S** (extend the filter to the drill selector). **Depends on** G1 and the blocklist. **AI-authorable.**

### G4 — The mining pass closed the wrong stages; the real thin stages are now `arrival` and `health`

**Verified.** `design/speaking_path.md` §6 names `lodging` (18 real candidates) and `health` (38) as
the too-thin stages and says the fix is "queued". The mining pass *ran* — `corpus/sentences/bank.json`
holds 324 sentences tagged `mined`, tagged `stage:lodging` (111), `stage:past_stories` (105),
`stage:opinions` (108). **`health` was not mined and received 1 mined sentence incidentally.**

Recomputing the yield against today's bank and today's seed lists:

| stage | real candidates | generated candidates | slots | §6 (2026-08-05) |
|---|---|---|---|---|
| **arrival** | **48** | 9 | 36 | 136 |
| **health** | **50** | 41 | 36 | 38 |
| past_stories | 90 | 36 | 36 | — |
| opinions | 82 | 4 | 36 | — |
| politeness | 87 | 112 | 36 | — |
| about_you | 99 | 133 | 36 | 115 |
| eating | 115 | 164 | 36 | 97 |
| getting_around | 129 | 119 | 36 | 148 |
| real_talk | 131 | 23 | 36 | — |
| lodging | 140 | 71 | 36 | 18 |
| time_plans | 263 | 160 | 36 | 368 |
| shopping | 277 | 221 | 36 | 209 |

**The design doc is wrong and the data is right.** `lodging` went from 18 to 140 because it was mined.
`arrival` went from 136 to 48 because the seed list tightened (`お願いします` replaced `お願い`) and
matching became lemma-only after the はい/履く failure. `arrival` — the **first stage**, the one every
learner sees — now has the worst take rate on the path: 36 slots from 48 candidates, 75%.

**Why it matters.** A 75% take rate is what near-duplication looks like. `arrival` units 3 and 4 teach
**four** ways to apologise for a delay (長い事お待たせしてすみません / 長くお待たせしてすみませんでした /
こんなに長い間待たせてすみません / 長い間、お待たせしてすみませんでした — three of them share the identical
pt-BR prompt "Desculpe por tê-lo feito esperar tanto tempo") and **four** 〜てくれてありがとう variants,
while never teaching はじめまして or よろしくお願いします. Measured: 24 in-stage phrase pairs at
SequenceMatcher ≥ 0.72, **12 of them in `arrival`**. R86 catches punctuation-identical strings only.

**Size L.** **Depends on** the mining + Layer-B authoring pipeline, which is already proven at 324
sentences (`scripts/ingest/mine_tatoeba_stages.py` → `ingest_mined_stages.py`), and on the 248,705-row
`raw_tatoeba_sentence` / 285,215-row `raw_tatoeba_translation` pools that are still there.
**AI-authorable.**

### G5 — The survival frames a traveller needs are largely absent from the corpus, and where they exist the path passes them over

Thirty-six canonical utterances, checked for presence in `corpus/sentences/bank.json` and in the path:

| need | in bank | in path | note |
|---|---|---|---|
| はじめまして / お名前は / これをください / お勘定 / 助けて / 救急車 / チェックイン / 荷物を預ける / 道に迷う / ベジタリアン / おすすめ / 何と言いますか / 気分が悪い / 〜まで行きたい / 試着 / Wi-Fi | **0** | 0 | not in the corpus at all |
| 〜はどこですか | 9 (6 real) | **0** | エスカレーター / 南ターミナル / リムジン / ランドリー / シャワー / 上りのエスカレーター — all real, all N4, all unused |
| 乗り換え | 3 | 0 | どこで乗り換えればいいですか exists, generated |
| 切符 | 4 | 0 | all generated |
| 警察 | 4 | 0 | 困ったときは警察に電話してください exists, generated |
| もう一度 / わかりません | 6 / 3 | 0 / 0 | 失礼ですが、もう一度おっしゃって下さい exists, real, unused |
| アレルギー | 1 | 0 | ハウスダストにアレルギーがあります |
| 予約しています / 痛いです / ゆっくり / 何時 | 1 / 2 / 6 / 17 | **1 / 1 / 1 / 1** | the four that made it |

**4 of 36.** Two distinct causes, and they need different fixes:

- **Absent from the corpus** (16 of 36). Only new authoring or new mining closes this.
- **Present and passed over** (the rest). `〜はどこですか` is the single highest-value frame in the whole
  path and six real examples sit in the bank unused, because they attach to escalators and limousine
  buses rather than to 駅 or トイレ, so the i+1 budget and the frequency sort both reject them. The
  generic frame with a useful noun exists **only as `gen-`** (お手洗いはどこですか, 出口はどこですか,
  地下鉄の駅はどこですか), and §3 rule 1 plus the path's advertised 431/432-real property structurally
  excludes generated sentences from `say_now`.

**This is the central tension in the area.** The path's proudest property — 100% real human-written
phrases — is what stops it teaching the phrases it exists to teach. It cannot be resolved inside the
builder; it is an owner decision about whether a *scenario-authored, teacher-reviewed* sentence is
allowed to lead a stage.

**Size L.** **Depends on** an owner ruling on generated `say_now` for survival frames, then G1.
**AI-authorable** with mandatory teacher sign-off (Layer C, `needs_review: true`).

### G6 — The learner reads material the stage is not about, in the stage's own six-phrase budget

Not a schema gap; a selection-quality gap, and the largest remaining content risk. Every one of the 432
phrases matches a seed as a lemma, so the matcher works; the seeds themselves select topics rather than
scenarios. Verified examples, all shipped today:

| stage | phrase | what it actually is |
|---|---|---|
| `getting_around-06` | あっという間に４０度近くまで熱が出た | a **fever**, matched on 近く |
| `getting_around-06` | ＦＡＸで地図を送っていただけませんか | a fax request |
| `eating-02` | 今日は魚の食いが悪い | the fish are not biting; 魚 |
| `eating-05` | 注文を受けてから作るのが受注生産です | build-to-order **manufacturing**; 注文 |
| `eating-05` | 大きなカヌーが水をきって進んでいた | a canoe; 水 |
| `eating-04` | 空気と人間との関係は水と魚との関係と同じだ | a philosophical simile |
| `health-04` | 心熱けれど肉体は弱し | classical Japanese, a Bible verse |
| `health-06` | お前は脳の半分があったら，危ない! | an insult; 危ない |
| `health-06` | 病院まで１０マイルもある | **miles** |
| `shopping-03` | あれはキジです | "that is a pheasant" — the exact sentence `design/speaking_path.md` §3.9 cites as the failure R87 fixed, **still shipped** |
| `shopping-04` | いくらお礼を言っても言い切れない | the いくら…ても concessive the same section says was rejected, **still shipped** |
| `shopping-06` | 彼が郊外に家を買った | buying a house; 買う |
| `arrival-04` | いいえ、あまり降りません | rainfall; いいえ |
| `arrival-05/06` | 予約係をお願いします / 明日の夜のディナーの予約をお願いします | hotel switchboard and restaurant booking, in the greetings stage |

And the defects propagate. A bad `say_now` phrase becomes a production `answer_key` in a later unit and
a fluency item after that: 心熱けれど肉体は弱し appears in **four** blocks across two stages
(`health-04` say_now → `health-05` production → `health-06` fluency → `past_stories-02` fluency);
あれはキジです appears in three; 彼は医者として無能だ in two. **118 of the 432 phrases reappear in two or
more other block types**, so one bad pick costs roughly three learner exposures.

**Size L.** **Depends on** G1, G2, G3 and the A8 blocklist. **AI-authorable** for the filter; the list
itself is the owner's per A8.

### G7 — No audio anywhere, and no place to put it

- 72 of 72 units carry `audio: "pending"`. **Zero audio files exist in the repository** (no `.mp3`,
  `.m4a`, `.ogg`, `.wav`, `.opus`).
- `contracts/sentence.schema.json` has **no `audio_ref` and no `audio_source`**, and `provenance` has
  no audio axis, even though `design/schema_v2.md` line 128 declares
  `audio_ref, audio_source, # tatoeba:<audioId> | tts:<voice> | none` and its §5 rationale calls audio
  provenance a separate axis. **The design doc is right and the contract never implemented it.**
- `speak_unit.audio` is **one string for a whole unit**, but `shadowing` is per-sentence and
  `production`/`fluency` need per-item playback. The field cannot address what the app must play.
- `design/listening.md` §7 defines the voice-over pipeline for **exam listening items only**; nothing
  maps it onto `course/speak/`.

**Size L.** **Depends on** the owner's TTS/voice choice (VOICEVOX / Style-Bert-VITS2 / local voice LLM,
per `design/listening.md`). **Not AI-authorable** — the schema is, the assets are not.

### G8 — A voice play mode has no data model at all

Beyond G7's model audio, a play mode needs a learner-attempt channel: an ASR target string, a scoring
contract, a per-attempt record, and a hint policy. What exists:

- `design/learning_science.md` **R52** already legislates ASR behaviour (`hint_target = null` whenever
  the signal is a whole-utterance score; always for pitch/mora/っ/ん) and **R53** caps the correction
  loop at one retry. The rules are written ahead of any data.
- `design/unlock_enums.json` `feature` includes **`voice-mode`** and **`listening`**. Neither is
  produced by anything; `corpus/capabilities/lesson_map.json` has **0 speak references**.
- `card_type` includes `listening` — 0 such cards exist.
- Pitch-accent data, which R52 names as the thing ASR is worst at: **1,221 of 7,401 vocab records
  (16.5%)** carry `pitch`.
- `prototype/app/routes/speakUnit.tsx` renders no audio element, no microphone, and does not render
  `shadowing` at all — the one block whose entire purpose is speaking aloud.
- Production is typed. **0 of 213 items accept a romaji answer.** A pt-BR learner without a Japanese
  IME cannot answer a single production item on the speaking path.

**Size L.** **Depends on** G7. **Not AI-authorable** — needs an owner decision on the ASR engine and on
whether romaji counts.

### G9 — The speaking path is outside the SRS entirely

`design/unlock_enums.json` states that "SRS cards are ALWAYS derived from item unlocks (a lesson's
`srs.introduces_cards` is computed from its unlocks)". Recomputed over `course/`:

- **322 lessons emit 4,133 SRS cards** across 11 decks (`deck:vocab-n5` 708, `deck:vocab-n3` 1,596, …).
- **`deck:phrases` is declared in the registry and holds 0 cards.**
- `contracts/speak_unit.schema.json` has **no `unlocks` and no `srs` property**. The 72 speak units
  emit **0 cards**.
- `design/srs_design.md`, `design/fsrs_integration.md`, `design/study_system_roadmap.md` and
  `design/product_roadmap.md` mention `speak` **zero times**.

A learner who takes the speaking path gets no spaced repetition, in a product defined as "Duolingo but
with integrated Anki (FSRS-6 or better)". Its 581 vocabulary items and 432 phrases are reviewed only by
whatever a later unit happens to reuse.

**Size M.** **Depends on** a design ruling: do speak units file into the existing level decks (the
words are the same `vocab:` records), or into `deck:phrases` plus a new `deck:speak-*` family?
**AI-authorable** once that is decided.

### G10 — R78's strand budget is declared, violated by every stage, and checked by nothing

`design/learning_science.md` **R78** declares the speaking path's budget as **15/30/25/30**
(meaning-input / meaning-output / language-focused / fluency), each stage held **within ±10 points**.
Recomputed from `strand_counts`:

| stage | input | **output** | lang-focused | fluency |
|---|---|---|---|---|
| budget | 15 | **30** | 25 | 30 |
| arrival | 33.6 | **7.0** | 46.7 | 12.6 |
| shopping | 33.0 | **8.3** | 42.2 | 16.5 |
| eating | 28.6 | **7.1** | 50.0 | 14.3 |
| getting_around | 28.3 | **7.1** | 50.4 | 14.2 |
| lodging | 26.8 | **6.7** | 53.2 | 13.4 |
| about_you | 27.4 | **6.8** | 52.1 | 13.7 |
| time_plans | 30.1 | **7.5** | 47.3 | 15.1 |
| health | 29.0 | **7.3** | 49.2 | 14.5 |
| past_stories | 28.5 | **7.1** | 50.2 | 14.2 |
| politeness | 25.7 | **6.4** | 55.0 | 12.9 |
| opinions | 28.1 | **7.0** | 50.8 | 14.1 |
| real_talk | 27.8 | **6.9** | 51.4 | 13.9 |
| **path-wide** | **28.8** | **7.1** | **50.1** | **14.1** |

**12 of 12 stages are outside the ±10 band on every strand.** Meaning-output runs at a quarter of
budget; language-focused runs at double. R77's own diagnostic in the same file says "Duolingo is ~80%
language-focused" — this path is at 50% and the rule that was written to prevent that is unenforced.
`validate_speaking_path.py` checks only that the histogram sums to 100 (`abs(sum - 100) > 2`), never
that it matches the budget.

The mechanical cause: every unit gets exactly 3 production items (71 × 3 = 213) against 6 phrases,
6 fluency items and 2–5 drills with 3 examples each.

**Size S** for the validator, **L** for the data. **Depends on** the production builder being able to
emit more than 3 items per unit, which needs more prior-known material per stage (G4).
**AI-authorable.**

### G11 — R83's spiral is declared, and `arrival` is never revisited

R83: "every stage 1-6 seed lexicon must reappear in at least one stage 7-12 unit". Measured over the
216 phrases in stages 7–12:

| stage 1–6 | phrases in stages 7–12 carrying one of its seeds |
|---|---|
| **arrival** | **0** |
| shopping | 11 |
| eating | 5 |
| getting_around | 4 |
| lodging | 3 |
| about_you | 4 |

The greeting/thanks/apology lexicon — the most reusable material on the path — is met in week one and
never retrieved again. Nothing checks R83.

**Size S** (validator) + **M** (fix by seeding late stages). **Depends on** nothing. **AI-authorable.**

### G12 — The path is not registered where the app looks for courses

- **`course/manifest.json` mentions `speak` zero times.** It lists four courses (`mod:pre-n5`, `mod:n5`,
  `mod:n4`, `mod:n3`), each with `level` and `path`. The speaking path is a sibling directory
  discoverable only through the *entity* registry in `contracts/manifest.json`.
  `validate_course_chain.py` walks manifest → course → topic → lesson and therefore never sees it.
- **`corpus/capabilities/lesson_map.json` has 0 speak entries.** The 45-capability registry — the layer
  that answers "what can this learner now do" — does not cover the path whose entire premise is
  capability.

For a product with "two paths", the two are not siblings in the data model.

**Size S.** **Depends on** widening `contracts/course_manifest.schema.json` (`level`/`path` are shaped
for the JLPT tree). **AI-authorable.**

### G13 — The corpus-wide hygiene gate does not see the speak path's prompts

`scripts/validate/audit_hygiene_all_locales.py` claims "every learner-facing pt-BR string corpus-wide
(~244k strings)". Replaying its own `collect()` over the tree: it picks up **86 strings from
`course/speak/`** — 85 `title` values and 1 `description`. Its `LEARNER_KEYS` set contains `prompt`
but **not `prompt_pt`**, and `prompt_pt` is a flat field rather than a `{"pt-BR": …}` locale object, so
all **284** learner-facing prompt strings (213 production + 71 fluency) are invisible to it.

Proof it matters: **five em dashes ship in `fluency.prompt_pt`** (`arrival` units 02–06: "Cumprimente,
agradeça e peça licença — em voz alta, sem ler"), against the project's explicit ban, and
`audit_hygiene_all_locales.py` reports 0 FAIL.

**Size S.** **Depends on** nothing. **AI-authorable.**

### G14 — `vocab.freq_rank`, the path's secondary ordering axis, is not in the source of truth

`design/speaking_path.md` §2, §3.4 and §3.9 all order on `vocab.freq_rank`. Measured:
**0 of 7,401** exported vocab records carry it (`contracts/vocab.schema.json` has no such property);
**7,255 of 7,401** rows in `db/corpus.sqlite` do. Per CLAUDE.md the export is the source of truth and
the SQLite index is regenerable, so the path's ordering is currently reproducible only from a
git-ignored artifact and cannot be audited from the committed corpus.

**Size S.** **Depends on** nothing (`export_corpus.py` already reads the column). **AI-authorable.**

### G15 — No stage assessment, no path-level placement

Per-unit checkpoints exist (365 items). There is no stage-completion test and no entry placement, and
`design/exam_simulator.md` §7 deliberately excludes this path from the simulator. The path's headline
promise — "every stage is a usable stopping point" — has no instrument that tells the learner whether
they reached it.

**Size M.** **Depends on** the A2 exam-bank regeneration. **AI-authorable.**

### G16 — Load and support numbers that a beginner path should probably not have

Not defects against any written rule, but worth an owner ruling:

- **62 of 72 units introduce more than 6 new words**; the maximum is **14 new words for 6 phrases**.
- The path shows **414 distinct kanji** in `say_now`; `kanji_recognition` lists **227**. In **26 of 72
  units** the learner meets more than 6 new kanji and the field's cap is 6.
- Sentence `level` per stage bears little relation to the stage's `approx_band`: `arrival` (pre-n5) is
  2 N1 / 12 N3 / 13 N4 / 9 N5 and **zero pre-N5**; `lodging` (n5) is 30 of 36 at N3 or above; `health`
  (n4) carries 10 N1 sentences. A10 already decided not to cap *patterns* by band; the same question
  for *phrases* has not been asked.
- `fluency.seconds_target` is the constant **48** in 70 of 71 blocks. R79(c) allows a fixed cap, but
  "derived from the learner's own prior attempt" needs an attempt record that does not exist.
- Only **13 distinct fluency prompts** serve 71 blocks.

**Size S** to measure and expose, **M** to act on. **Depends on** an owner ruling. **AI-authorable.**

### G17 — `design/speaking_path.md` carries numbers the data no longer supports

| doc claim | actual | verdict |
|---|---|---|
| §6 "the current 5,565-sentence bank (3,352 real)" | 5,889 / 3,676 real | doc stale |
| §6 thin stages `lodging` 18, `health` 38 | lodging 140 (mined), health 50, **arrival 48** | doc stale and misdirects the fix |
| §6 "the fix … is the follow-up task … queued rather than done" | 324 sentences mined and ingested; `shortfall` is empty | doc stale |
| §4 `kanji_recognition` "holds 212 distinct kanji" | 227 | doc stale |
| §7 link counts `phrase` 120 / `new-word` 177 / `review` 24 | 125 / 196 / 44 | doc stale |
| §3.7 "measured worst case after the rule is 6 of 36 (`time_plans`)" | max 4 in any 200-id window, in five stages | doc stale |
| §5 "the per-stage survival cores of R87 live in the builder" | one stage has one | **doc misleads** (see G2) |
| §3.9 あれはキジです cited as the failure R87 fixed | still shipped in `shopping-03` | **doc misleads** |
| §3a "26 of the 33 stage-opening items are on-topic" | 26 of 33 | doc correct |
| §2 "248,705 CC-BY Tatoeba sentences" | 248,705 rows | doc correct |

**Size S.** **AI-authorable.**

---

## 4. Quality risks against the near-100% goal

**R1. Register is the biggest shippable error, and it is silent.** 62.5% of what this path models is
casual form. A Brazilian learner who lands in Japan and says 食べながら話しちゃダメだよ to a waiter, or
opens with a plain-form request at a hotel desk, will be understood and will be rude. Nothing in the
data, the contract, the validator or the app marks a phrase's register, so the error is invisible to
every gate we have and will only surface with a human reviewer or a user.

**R2. Defects triple.** 118 of 432 phrases reappear in two or more other block types. Anything wrong in
a `say_now` pick becomes a production answer key and a fluency item. Per-item repair on this path costs
about 3× what the say_now count suggests, and any repair pass must follow the propagation.

**R3. The path advertises a property it does not have.** "431 of 432 phrases real" is true of `say_now`
and false of what the learner reads: 752 distinct sentences, 52 of them AI-generated, arriving through
the drill selector. `course.json.totals.real_phrases` counts the former and is validated against it, so
the manifest is *technically* true and *practically* misleading.

**R4. Approved content policy is blocked on a schema, and the content is live.** A8 was decided
("yes; must not impact the lessons") and cannot be executed because there is no `register` field.
Meanwhile `心熱けれど肉体は弱し`, `痔があります`, `お前は脳の半分があったら，危ない!`, `彼は医者として無能だ`
and `どいつもこいつもばかばっかりだ` are all reachable in the shipped path today. The blocker is one
schema field plus a population pass.

**R5. Two enforceable rules are enforced by nothing.** R78 (12/12 stages out of band) and R83 (`arrival`
never revisited) are `[enforceable]` in `design/learning_science.md`, are violated in the data, and no
validator mentions either. Per `scripts/validate/README.md`'s own standard — "an unconditional PASS is
an information line wearing a check's costume" — these are worse: they are rules with no costume at all.
The same is true of Rule 3 (i+1 `MAX_NEW`), which currently holds by builder correctness alone.

**R6. The gate's coverage claim is wider than its reach.** `audit_hygiene_all_locales.py` says
"corpus-wide" and sees 86 of the ~370 learner-facing strings in `course/speak/`. Five em dashes prove
the hole. Any other prose defect class in `prompt_pt` is equally unmeasured.

**R7. A speaking path with no speech is a naming risk, not just a feature gap.** As shipped, the only
output modality is typing Japanese script, the only input modality the app offers is a Japanese IME
(0 of 213 items accept romaji), and `shadowing` — the one block that exists to be spoken — is not
rendered. Calling this "Fala Primeiro" to a learner is a claim the data does not support yet.

**R8. Stopping points are asserted, not tested.** "A learner who stops after stage 4 can still land,
eat, buy and navigate" is the path's core promise. Against 36 canonical utterances, 4 are taught. There
is no stage exam that would have caught this.

---

## 5. Recommended sequence

Ordered so that each step unblocks the next and nothing is authored twice.

**Phase 0 — make the invisible visible (S, all AI-authorable, no owner input needed).**

1. Publish `freq_rank` in the vocab export (G14) — the path's ordering axis becomes auditable.
2. Add `prompt_pt` to `LEARNER_KEYS` in `audit_hygiene_all_locales.py`, fix the 5 em dashes (G13).
3. Add three checks to `validate_speaking_path.py`: R78 strand budget per stage, R83 spiral, and the
   i+1 `MAX_NEW` recomputation (G10, G11, §2.2). Land them as **ratchets** — they fail today, so freeze
   the current counters and let them only shrink, per the suite's own convention.
4. Add a semantic near-duplicate check above R86 (SequenceMatcher ≥ 0.72 within a stage) — freezes the
   24 pairs and stops new ones (G4).
5. Refresh `design/speaking_path.md` with the recomputed numbers, and correct §5's implication that
   every stage has a survival core (G17).

**Phase 1 — the register schema, which everything downstream waits on.**

6. **Owner/teacher decision:** the sentence-level `register` value set, written into
   `design/schema_v2.md`. This is the single blocking decision in this area.
7. Add `register` to `contracts/sentence.schema.json`; populate mechanically from token auxiliaries
   (です/ます/でございます/だ/plain) plus JMdict misc, leave the residue `null` and reviewable; a
   validator asserts every `say_now` phrase carries one (G1).

**Phase 2 — content policy, now executable (A8).**

8. Owner supplies the blocklist. Apply the register filter **and** the blocklist to `say_now`,
   `production`, `fluency` **and `drills[].examples`** (G3, G6). Add the per-stage idiom stoplist that
   `PENDING.md` B-followups already asked for (いくら…ても).
9. Write survival cores for the eleven stages that lack them (G2), and rebuild.

**Phase 3 — the content the path is missing.**

10. Mine `arrival` and `health` to parity, the same pipeline that produced the 324
    lodging/past_stories/opinions sentences (G4). This is the largest single win: it is what stops
    `arrival` teaching four apologies for lateness.
11. **Owner decision:** may a scenario-authored, teacher-reviewed sentence lead a stage when the corpus
    has no real one? If yes, author the ~16 missing survival frames (G5) as Layer C with
    `needs_review: true`, and the 〜はどこですか family stops being unteachable.
12. Re-run and re-check the strand balance; production per unit should rise from 3 as prior-known
    material grows (G10).

**Phase 4 — make it a course the app can find and remember.**

13. Register the path in `course/manifest.json` and map its stages into
    `corpus/capabilities/lesson_map.json` (G12).
14. **Design decision** on decks, then emit `srs.introduces_cards` from speak units and fill
    `deck:phrases` (G9). Without this the speak path is outside the product's stated core mechanic.
15. Stage-completion checkpoints, after the A2 bank regeneration (G15).

**Phase 5 — voice, which is a project of its own.**

16. Add `audio_ref` / `audio_source` to the sentence contract as `design/schema_v2.md` always specified,
    and make `speak_unit.audio` per-sentence rather than per-unit (G7).
17. **Owner:** TTS engine choice and the voice-over run; then `shadowing` renders and plays.
18. **Owner:** ASR engine and the romaji-acceptance ruling; then the attempt/scoring contract that
    R52 and R53 already legislate against (G8).

Phases 0–2 are roughly two focused sessions and remove every silent-failure class in the area.
Phase 3 is the content project. Phases 4–5 are product decisions that no amount of authoring
substitutes for.
