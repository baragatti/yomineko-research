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
| kanji | full production, per level | **recognition only**, and only signage kanji |
| stopping point | mid-level = incomplete | **every stage is a usable stopping point** |
| grammar order | by level | by whether it lets you vary a phrase you already say |

Both paths stay. This is for the learner with a trip in eight weeks; the JLPT path is for the
learner with an exam in December.

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

1. **Phrases are real.** A unit's `say_now` phrases are drawn from the sentence bank with
   `ai_generated = 0` (real human-written Tatoeba/JEC text) preferred; generated sentences fill only
   when a scenario is otherwise empty, and stay marked. Spec §1.2, selection over generation.
2. **Scenario match.** A sentence belongs to a stage when it contains a term from that stage's seed
   lexicon (§5). Seeds are Japanese surface forms, so the match is checkable by eye.
3. **i+1 load.** A sentence qualifies only if the number of its words *not* in the cumulative known
   set is ≤ 2. The known set grows as units are completed, exactly like `course/`'s
   `cumulative_known_set`.
4. **Vocabulary order.** Candidate words for a stage = words appearing in that stage's qualifying
   sentences, sorted by `freq_rank` ascending, `level` ascending as tiebreak.
5. **Grammar.** A grammar point enters a unit only when one of its `forms_json` forms actually
   occurs in that unit's phrases — the learner meets a pattern because they are about to say it,
   never because a syllabus says so. Spoken registers sort first.
6. **Nothing is invented.** If a stage cannot be filled to target from the bank, the builder emits a
   short unit and records the shortfall in the manifest. A thin stage is a visible data gap to fix
   by mining more Tatoeba, not something to paper over with generated sentences.

## 4. Unit shape

A unit is deliberately small — one sitting, speech-first:

```
say_now        5–8 sentence IDs. The things you can use today, out loud.
words          vocab IDs introduced here, frequency-ordered.
patterns       grammar IDs whose forms occur in say_now.
drills         substitution drills DERIVED from say_now: one slot swapped for other
               known vocab. Generated mechanically from the dissection, so every
               variant is guaranteed to be inside the known set.
shadowing      the same sentence IDs, flagged for audio (audio: "pending" until the
               owner's voice-over pass — see design/listening.md).
signage        kanji IDs for recognition only (入口 出口 男 女 駅 円 …), never production.
```

`needs_review: true` on every unit: sequencing is Layer C.

## 5. The twelve stages

Approximate JLPT bands are shown for orientation only — **the path never gates on them.**

| # | Stage | Slug | Seeds (excerpt) | ≈band |
|---|---|---|---|---|
| 1 | Chegar e cumprimentar | `arrival` | こんにちは ありがとう すみません はい いいえ お願い はじめまして | pre-N5 |
| 2 | Isto, aquilo, quanto custa | `shopping` | いくら 買う 円 ください 店 これ 安い 高い お金 | pre-N5/N5 |
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

Full seed lexicons live in the builder, not here, so they stay executable rather than drifting from
the prose.

## 6. Known gaps (measured 2026-08-05, before the first build)

Real-sentence yield in the current 5,565-sentence bank (3,352 real):

```
arrival 136   shopping 209   eating 97   getting_around 148
lodging  18   about_you 115  health 38   time_plans 368
```

`lodging` (18) and `health` (38) are too thin for five units each. The fix is **selection, not
generation**: `raw_tatoeba_sentence` holds 248,705 sentences already ingested and licensed, and
`raw_tatoeba_translation` holds 285,215 translations to pair them with. Mining those two stages up
to parity is the follow-up task; it needs a pt-BR authoring pass (Layer B) per new sentence, which
is why it is queued rather than done inline. Until then the builder emits short units and says so.

## 7. Relationship to the exam simulator

None, deliberately. `design/exam_simulator.md` samples JLPT-format papers; this path does not feed
it and is not scored by it. A learner on the speaking path who later wants the certificate switches
to `course/` with most of the vocabulary already known.
