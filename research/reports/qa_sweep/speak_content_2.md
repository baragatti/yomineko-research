# QA sweep: `course/speak` content, stages 6 and 7 and 9 through 12

**Slice:** `course/speak/{about_you, opinions, past_stories, politeness, real_talk, time_plans}`, 36 unit files.
**Method:** every authored/selected field cross-referenced against `corpus/sentences/bank.json`,
`corpus/vocab/*.json` and `corpus/exam_banks/*.json`; pt-BR judged against `design/translation_style.md`;
selection behaviour judged against `design/speaking_path.md`.
**Out of scope by instruction:** sentence `structure_explanation` (being re-authored concurrently).

Fields reviewed: `title`, `say_now`, `chunk_phrases`, `production[].prompt_pt` / `.answer_key` /
`.accepted_variants`, `fluency.prompt_pt` / `.items`, `checkpoint[]` and its `distractors`, `drills[]`.

`answer_key` and `prompt_pt` were verified byte-identical to the referenced bank record in all 108
production items (0 mismatches, 0 dangling sentence IDs). Every `say_now`, `fluency.items`, `drills`
and `checkpoint` ID resolves. No em dash, no pt-PT lexicon, no "Quanto a…" crutch, and no AI tell was
found in any of the 36 titles, 36 fluency prompts or 108 production prompts.

12 findings below, most severe first.

---

## F1. 48 of 108 production items reject the correct kana spelling of the answer

**Severity: high. All six stages.**

`accepted_variants` carries the bank's *phonetic* `kana` string, in which the topic/contrast particle
は is transcribed as わ and the direction particle へ as え. The orthographic kana spelling, the one the
learner is taught to write, is present in **zero** of the 48 affected items.

`speak:about_you-01`, production item for `sent:tatoeba-84223`:

```json
"answer_key": "部屋には家具が４点あった。",
"accepted_variants": [
  "へやにわかぐがよんてんあった",
  "へやにわかぐがよんてんあった。",
  "部屋には家具が４点あった",
  "部屋には家具が４点あった。"
]
```

A learner who answers in kana with the spelling every beginner course drills, `へやにはかぐがよんてんあった`,
is marked wrong. `speak:time_plans-06`, `sent:tatoeba-174391`, does the same to へ: it accepts
`ごごわそとえでたくない` and rejects `ごごはそとへでたくない`.

Measured over the slice: 48 production items contain a は/へ token whose `tokens[].pos == "particle"`
and whose `reading` is わ/え; 0 of them carry a kana variant preserving the orthographic character.

**Why it is a defect, not a policy:** the phonetic string is correct as a *pronunciation* record and
belongs in `kana`. As an *input acceptance list* it inverts the rule, punishing correct orthography and
rewarding a spelling that is wrong on paper. This is a meaning-output exercise, so the learner types the
answer.

**Fix:** build the kana variant from `tokens[]` rather than from the `kana` field: concatenate each
token's `reading`, except that a token with `pos == "particle"` keeps its `surface`. Add that string to
`accepted_variants` alongside the existing phonetic one (accept both, teach one).

---

## F2. Seven production items require fullwidth digits or fullwidth Latin, with no halfwidth variant

**Severity: high. about_you (2), opinions (3), real_talk (1), time_plans (1).**

| Unit | `answer_key` | rejected natural input |
|---|---|---|
| `speak:about_you-01` | `部屋には家具が４点あった。` | `…家具が4点あった。` |
| `speak:about_you-03` | `ＳＰの仕事の様子が今日テレビで放送されました` | `SPの仕事の…` |
| `speak:opinions-02` | `列車はあと５分で出発するはずです。` | `…あと5分で…` |
| `speak:opinions-02` | `列車は６時到着のはずだった。` | `…6時到着…` |
| `speak:opinions-06` | `４０近いはずだ。` | `40近いはずだ。` |
| `speak:real_talk-06` | `ＵＮというのは何を表わしていますか。` | `UNというのは…` |
| `speak:time_plans-01` | `夫は大抵８時には仕事に出かけます。` | `…大抵8時には…` |

A Japanese IME in ローマ字 mode emits halfwidth `5` and halfwidth `SP` by default; producing `５` or `ＳＰ`
takes a deliberate mode switch most learners never make. The fullwidth form is an artefact of the Tatoeba
source, not something the exercise is testing.

**Fix:** for each kanji variant, also push its `unicodedata.normalize("NFKC", v)` twin into
`accepted_variants` (this covers digits and Latin in one rule and is a no-op for the other 101 items).

---

## F3. `speak:politeness-05` requires a legacy squared character the learner cannot type

**Severity: high.**

Production item for `sent:tatoeba-1490062`:

```json
"answer_key": "肉を半㌔ください。",
"accepted_variants": ["にくをはんきろください", "にくをはんきろください。", "肉を半㌔ください", "肉を半㌔ください。"]
```

`㌔` is U+3314 SQUARE KIRO, a CJK-compatibility glyph kept only for round-tripping old encodings. No IME
produces it from `kiro`. The ordinary spelling `肉を半キロください` is rejected, and so is `半きろ`.

**Fix:** add `肉を半キロください` (with and without `。`) to `accepted_variants`, or drop the item; either
way, add a compatibility-character filter (U+3300–U+33FF) to the production-item selector so no further
answer key can require one.

---

## F4. Every stage's unit-01 ships a fluency task whose six items contradict its own prompt

**Severity: high. All six stages.**

`fluency` gives the learner a prompt and six sentences to speak from inside `seconds_target`. In the
first unit of each stage, all six items come from the *previous* stage's pool, because the item filter
is "already known" with no scenario constraint.

`speak:about_you-01`:

```
prompt_pt: "Alguém puxou assunto com você. Diga quem você é, de onde vem e do que gosta."
items:
  部屋の大きさは、これで十分ですか。      O quarto é grande o suficiente para você?
  部屋をいそいでかたづけてほしいの。      Quero que você arrume o quarto rápido.
  部屋を出るときは必ず明かりを消してね。   Quando sair do quarto, não esquece de apagar a luz, tá?
  これはその箱をあける鍵です。          Esta é a chave que abre essa caixa.
  部屋を出た後はドアを閉めなさい。       Feche a porta depois de sair do quarto.
  料金の手ごろなホテルを見つけて下さい。   Por favor, ache um hotel com preço acessível.
```

Six lodging lines. Not one of them lets the learner say who they are, where they are from, or what they
like, which is the entire task.

Same shape elsewhere:

- `speak:opinions-01`, prompt *"Perguntaram sua opinião. Diga o que você acha e por quê."*, items are
  salad, a glass of water, a house visit, steak doneness and a telegram.
- `speak:politeness-01`, prompt *"Você precisa pedir um favor a alguém mais velho. Peça com jeito."*,
  items are curry, a first visit to a shop, the zoo, the purpose of a trip and the seasons.
- `speak:time_plans-01`, prompt *"Um amigo quer marcar alguma coisa. Combine dia e horário."*, items are
  a piano hobby, reading novels, losing a job and class sizes.

Measured overlap between `fluency.items` and the unit's own stage `say_now` pool:

| unit | 01 | 02 | 03 | 04 | 05 | 06 |
|---|---|---|---|---|---|---|
| about_you | **0/6** | 3/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| opinions | **0/6** | 2/6 | 5/6 | 6/6 | 6/6 | 6/6 |
| past_stories | **0/6** | **1/6** | 5/6 | 6/6 | 6/6 | 6/6 |
| politeness | **0/6** | 2/6 | 6/6 | 6/6 | 6/6 | 6/6 |
| real_talk | **0/6** | **1/6** | 4/6 | 6/6 | 6/6 | 6/6 |
| time_plans | **0/6** | 2/6 | 6/6 | 6/6 | 6/6 | 6/6 |

From unit-03 on the problem disappears on its own, so this is a cold-start bug in one filter, not a
design flaw in the fluency block.

**Fix:** intersect the fluency candidate pool with the stage's own seed-lexicon matches before applying
the zero-new-token filter. In a unit-01 the stage pool is exactly that unit's own `say_now`, which is
already known by the time `fluency` runs (it is the last strand in the unit), so draw the six from
there. If that still cannot fill six, emit a short block and record the shortfall in the manifest, as
`design/speaking_path.md` §3.6 requires for every other thin case.

---

## F5. Two units repeat the previous unit's fluency set verbatim

**Severity: medium. about_you, time_plans.**

`speak:about_you-04`'s `fluency.items` is identical, same six IDs in the same order, to
`speak:about_you-03`'s; `speak:time_plans-05`'s is identical to `speak:time_plans-04`'s. The
`prompt_pt` is the same too, so those units deliver a fluency block with nothing new in it.

```
speak:time_plans-04 and -05, both:
  私は二時間以上も待った。 / 今日はちょっと頭が痛いの。 / 今日は頭がさえません。 /
  「いつ起きるの？」「朝八時だよ」 / 木村さんという人にパーティーで会ったよ。 / 私は明日死ぬかもしれない。
```

**Fix:** in the fluency selector, exclude the previous unit's item list before ranking; if that empties
the pool, shorten the block rather than repeating it.

---

## F6. `speak:politeness-01` spends two of six `say_now` slots, and both `chunk_phrases`, on the same phrase

**Severity: medium.**

```
sent:tatoeba-4854     おめでとうございます。   "Parabéns!"
sent:tatoeba-8467948  おめでとうございます！   "Parabéns!"
```

Two distinct bank IDs holding the same phrase, differing only in the final punctuation mark, with the
same pt-BR. Both are also the unit's only two `chunk_phrases`. The learner is shown one expression
twice and told it is two.

**Fix:** keep `sent:tatoeba-4854`, backfill the freed `say_now` slot from the politeness pool, and add a
normalized-text dedupe (strip trailing 。！？ before comparing) to the selector so no unit can stack two
IDs of the same string again.

---

## F7. `speak:real_talk-06` teaches two different patterns under one identical translation

**Severity: medium.**

```
sent:tatoeba-77972  両方とも好きなわけではない。      "Não é que eu goste dos dois."
sent:tatoeba-77973  両方とも好きというわけではない。   "Não é que eu goste dos dois."
```

The Japanese differs in exactly the thing the unit exists to teach (`なわけではない` versus
`というわけではない`, plain nominal versus quoted-clause scope), and the pt-BR is byte-identical. The
learner sees two phrases, one meaning, and no signal about what changed.

**Fix:** differentiate the pt so the contrast is visible, for example keep 77972 as
*"Não é que eu goste dos dois."* and render 77973 as *"Não é bem que eu goste dos dois."*; or drop one
and backfill. Note this is a `translation` field on a bank record, so the fix lands in
`corpus/sentences/bank.json` and both paths get it.

---

## F8. Nine checkpoint items have more than one correct answer

**Severity: medium. about_you (1), opinions (4), real_talk (3), time_plans (1).**

`design/speaking_path.md` §7 re-draws distractors from the learner's known set, by frequency, and never
checks that the drawn word actually *fails* in the blank. Nine of the 72 `context_fill` checkpoints in
this slice are therefore unanswerable or double-keyed.

The clearest, `speak:time_plans-01`, `cf:n5:3581:36`:

```
stem:        また（　）だ。
correct:     雨
distractors: 花 / 話 / 夫
```

`また花だ`, `また話だ`, `また夫だ` are all ordinary Japanese. The stem is three characters long and
carries no context whatsoever, so nothing distinguishes the key from any of the three wrong answers.

The rest:

| Unit | Item | Stem | Key | Distractor that also works |
|---|---|---|---|---|
| `real_talk-02` | `cf:n3:5550:1966` | `彼女は（　）らしい。` | 幸せ | `来る` (`彼女は来るらしい` = "it seems she's coming"; らしい takes plain verbs) |
| `real_talk-04` | `cf:n3:5534:1868` | `（　）というのは何ですか。` | 幸福 | `電車`, `休み` |
| `real_talk-04` | `cf:n3:5504:1977` | `（　）は終わったわけではない。` | 事件 | `放送` |
| `opinions-06` | `cf:n3:4385:1571` | `今日は（　）しないほうがいい。` | 外出 | `招待` |
| `opinions-04` | `cf:n3:3488:1571` | `母は私に（　）しないようにいった。` | 外出 | `苦労` (idiomatic) |
| `opinions-03` | `cf:n4:3751:1348` | `（　）かどうかどうでもいいって！` | 金持ち | `買い物`, `女の子`, `小さい` (all three) |
| `opinions-02` | `cf:n3:5046:2453` | `９（　）になってはじめて彼は帰ってきた。` | 時 | `日` |
| `about_you-02` | `cf:n4:1299:1082` | `（　）を一から考えなおす` | 計画 | `生産` |

The mirror-image failure also occurs: in `speak:about_you-01` `cf:n4:3790:754`
(`（　）は、いつ会うことができる？`, key `今度`) all three distractors are plain-form verbs (`読む` / `急ぐ` /
`聞く`), so `読むは` is ungrammatical and the item is solvable without knowing 今度 at all.

**Fix:** after the frequency re-draw, apply two cheap filters before accepting a distractor: (a) it must
share the key's coarse POS from `corpus/vocab` (this alone kills the `読む` case and 6 of the 9 above);
(b) reject any suru-noun distractor when the character following the blank in the stem is し or す
(kills 招待, 苦労, 放送). For stems shorter than about eight characters with no lexical anchor
(`また（　）だ。`), drop the item from the path rather than patch it.

---

## F9. Nine distractors are printed in rare kanji spellings the corpus itself marks uncommon

**Severity: medium. about_you (1), politeness (2), real_talk (3), time_plans (3).**

The distractor renderer prints the vocab entry's `headword`. For a family of JMdict entries the
headword is an ateji form that `corpus/vocab` explicitly flags `is_common: false` while flagging the
kana form `is_common: true`.

| Unit | Item | Printed | Corpus says | Learner knows it as |
|---|---|---|---|---|
| `real_talk-02` | `cf:n3:5550:1966` | `珈琲` | `("珈琲", is_common:false)`, `("コーヒー", is_common:true)` | コーヒー |
| `real_talk-02` | `cf:n3:1277:1966` | `咖哩` | `("咖哩", false)`, `("カレー", true)` | カレー |
| `real_talk-03` | `cf:n3:5538:1980` | `洋杯` | `("洋杯", false)`, `("コップ", true)` | コップ |
| `time_plans-04` | `cf:n5:4163:426` | `洋袴` | `("洋袴", false)`, `("ズボン", true)` | ズボン |
| `time_plans-06` | `cf:n4:3700:848` | `漸と` | `("漸と", false)`, `("やっと", true)` | やっと |
| `about_you-04` | `cf:n5:3595:307` | `此の` | `("此の", false)`, `("この", true)` | この |
| `politeness-04`, `time_plans-04` | `cf:n4:5250:1257`, `cf:n4:3427:859` | `何時` | kana form common | いつ |
| `politeness-02` | `pp:n4:717` | `為さる` | `("為さる", false)`, `("なさる", true)` | なさる |

Two independent contracts break here. `design/speaking_path.md` §4 caps `kanji_recognition` at six per
unit and states the path is recognition-only, so 咖哩 and 洋袴 are outside anything the learner has been
shown. And §7 requires distractors to come from the learner's *known set*, which these are not: the
learner knows the word, never that spelling, so the option is eliminated on sight as unfamiliar, which
is precisely the failure §7 says the re-draw exists to prevent.

**Fix:** when rendering a distractor, pick the entry's first `is_common: true` form rather than
`headword`, falling back to `headword` only when no common form exists.

---

## F10. `speak:past_stories-01` puts a classical-Japanese Bible verse in the fluency set

**Severity: medium.**

```
prompt_pt: "Alguém perguntou como foi seu fim de semana. Conte, no passado."
item: sent:tatoeba-145552  心熱けれど肉体は弱し。  "O espírito está pronto, mas a carne é fraca."
```

`熱けれ` and `弱し` are 文語 (classical) adjective forms, not modern Japanese; the sentence is the
standard Japanese rendering of Matthew 26:41. The learner is asked to say it aloud, within a 48-second
target, in a unit about last weekend. Nothing in the sentence is usable, and the `弱し` 終止形 actively
teaches a form that is wrong in every sentence they will otherwise produce.

**Fix:** drop the item from `speak:past_stories-01.fluency.items` and backfill from the same unit's
`say_now`; add a bungo filter (terminal `〜し` on an i-adjective stem, 已然形 `〜けれ`) to the speaking
path's selectable pool, since the same forms will surface again as the bank grows.

---

## F11. Death and suicide lines are placed in the casual-conversation and scheduling units

**Severity: medium. real_talk, time_plans, about_you.**

`say_now` is defined in `design/speaking_path.md` §4 as *"the things you can use today, out loud."*

- `speak:real_talk-06` `say_now` carries `sent:tatoeba-95365` `彼女が自殺したというのは本当か。`
  ("Será que é verdade que ela se suicidou?"). The same unit's checkpoint `cf:n3:5522:1979` has 自殺 as
  its correct answer, so the topic is both spoken and tested.
- `speak:time_plans-02` `say_now` carries `sent:tatoeba-152614` `私は明日死ぬかもしれない。`
  ("Eu talvez morra amanhã."), which then recurs as a fluency item in `time_plans-03`, `-04` and `-05`,
  all under the prompt *"Um amigo quer marcar alguma coisa. Combine dia e horário."* It is off-task as
  well as morbid.
- `speak:about_you-06` `say_now` carries `sent:tatoeba-789591` `悲しいことに多くの日本人が亡くなりました。`,
  which is then the `time_plans-01` production key and a `time_plans-02` fluency item.

Each pattern involved (`というのは`, `かもしれない`, `ことに`) has dozens of neutral carriers in the same
bank, so nothing is lost by swapping. `real_talk-06` already contains
`sent:tatoeba-10050266 彼女が嘘をつくわけがない。` two units earlier as a ready replacement shape.

**Fix:** swap those three IDs for neutral carriers of the same pattern and add a content filter
(自殺 / 死ぬ / 亡くなる and the like) to the speaking-path selector, flagged in the manifest so the
exclusion is auditable rather than silent.

---

## F12. `speak:past_stories-04` asks the learner to produce a malformed request form

**Severity: low.**

Production item for `sent:tatoeba-214558`:

```json
"prompt_pt": "Por favor, tenha uma refeição maravilhosa.",
"answer_key": "すばらしい食事を経験下さい。"
```

`経験` is a suru-noun. The polite request built on a suru-noun takes either the honorific prefix
(`ご経験ください`) or the te-form (`経験してください`). Bare noun + `下さい`, with neither ご nor して, is not
well-formed; the corpus's own tokenisation confirms the shape, splitting it as noun `経験` + verb
`下さい` with no intervening element. The English gloss on the bank record
("Have a wonderful eating experience.") shows this is Tatoeba translationese rather than natural
Japanese.

This is `strand: meaning-output`, so the learner types the string exactly and is rewarded for it.

**Fix:** drop the item. The same unit already uses `jec-0319` and `jec-0071` for 経験, so coverage of
the word is unaffected. (The sentence itself is Layer A and must not be edited; excluding it from
production is the correct remedy.)

---

## Counts

| Stage | Content items checked | Findings touching the stage |
|---|---|---|
| `about_you` | 161 | F1, F2 (2), F4, F5, F8 (1), F9 (1), F11 |
| `opinions` | 161 | F1, F2 (3), F4, F8 (4) |
| `past_stories` | 161 | F1, F4, F10, F12 |
| `politeness` | 163 | F1, F3, F4, F6, F9 (2) |
| `real_talk` | 160 | F1, F2 (1), F4, F7, F8 (3), F9 (3), F11 |
| `time_plans` | 160 | F1, F2 (1), F4, F5, F8 (1), F9 (3), F11 |
| **Total** | **966** | **12 distinct findings** |

Checked = 36 titles + 216 `say_now` refs + 2 `chunk_phrases` + 108 production items (each judged across
`prompt_pt`, `answer_key` and its `accepted_variants`, 418 variant strings in all) + 36 fluency prompts
+ 216 fluency items + 177 checkpoint entries with their 450 distractors + 177 drill blocks covering 531
example refs.

Flagged = 12 findings, affecting 48 production items (F1), 7 (F2), 1 (F3), 12 fluency blocks (F4),
2 fluency blocks (F5), 1 unit (F6), 1 phrase pair (F7), 9 checkpoints (F8), 9 distractor slots (F9),
1 fluency item (F10), 3 sentence placements (F11), 1 production item (F12).

Clean on: ID resolution (0 dangling refs across 1,455 corpus references), `answer_key` and `prompt_pt`
fidelity to the bank (108/108 exact), pt-BR register and style in all 180 authored strings, duplicate
`say_now` IDs within a stage (0), repeated production sentences within a stage (0), duplicate or
self-answering distractor sets (0 cases of the key appearing among its own distractors).
