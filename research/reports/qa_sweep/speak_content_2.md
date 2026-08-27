# QA sweep: `course/speak` content, batch 2

**Slice:** stages `about_you`, `opinions`, `past_stories`, `politeness`, `real_talk`, `time_plans`
(36 unit files, `course/speak/<stage>/unit-01..06.json`).
**Date:** 2026-08-27. **Mode:** read-only. **Out of scope by instruction:** sentence
`structure_explanation` fields (being re-authored concurrently).

Sentence IDs are resolved against `corpus/sentences/bank.json`; every quotation below is verbatim
from the committed JSON.

## What passed

The mechanical layer of these 36 units is clean. Verified by script, zero defects:

| Check | Result |
|---|---|
| `cumulative_known_vocab` vs accumulated `words` across all 12 stages | exact match, 72/72 units |
| `fluency.zero_new_tokens: true` vs every token's `vocab` in the known set | holds, 36/36 units |
| Referential integrity of `say_now` / `chunk_phrases` / `shadowing` / `drills[].examples` / `production[].sentence` / `fluency.items` | 1,289 ID references, 0 missing from the bank |
| `shadowing` mirrors `say_now` | 36/36 |
| `real_phrases` vs actual `ai_generated == false` count in `say_now` | 36/36 |
| `strands` (%) vs `strand_counts` (n) | consistent, sums to 100 in 36/36 |
| `production[].prompt_pt` / `answer_key` vs the bank record | byte-identical, 108/108 |
| `production[].sentence` previously met as a `say_now` item | 108/108 |
| Duplicate distractors inside one checkpoint item | none in 450 distractors |
| Authored pt-BR (`title`, `fluency.prompt_pt`): pt-PT forms, em dash, "Quanto a", promotional adjectives | none found |

The findings below are all in the assembly layer: which sentence went into which slot, and what
the learner is allowed to type back.

---

## Findings

### 1. Every stage's unit-01 runs the previous stage's material under this stage's prompt

**Severity: high. Affects all 6 stages in this slice (and, by the same measurement, all 12).**

`unit-01` of each stage takes 3/3 `production` sentences and 6/6 `fluency.items` from the
*previous* stage's sentence pool and 0 from its own, while `fluency.prompt_pt` names *this*
stage's scenario. Measured across the whole path:

| Unit | production from own stage | fluency from own stage | source stage |
|---|---|---|---|
| `speak:about_you-01` | 0/3 | 0/6 | `lodging` |
| `speak:time_plans-01` | 0/3 | 0/6 | `about_you` |
| `speak:past_stories-01` | 0/3 | 0/6 | `health` |
| `speak:politeness-01` | 0/3 | 0/6 | `past_stories` |
| `speak:opinions-01` | 0/3 | 0/6 | `politeness` |
| `speak:real_talk-01` | 0/3 | 0/6 | `opinions` |

The rolling window is fine in units 02 to 06, where it mixes old and new. At unit 01 the window
has nothing of its own yet, so the mismatch is total. Worst case, `speak:about_you-01`:

> `"prompt_pt": "Alguém puxou assunto com você. Diga quem você é, de onde vem e do que gosta."`

with these six items to say:

> `部屋の大きさは、これで十分ですか。` ("O quarto é grande o suficiente para você?")
> `部屋をいそいでかたづけてほしいの。` ("Quero que você arrume o quarto rápido.")
> `部屋を出るときは必ず明かりを消してね。` ("Quando sair do quarto, não esquece de apagar a luz, tá?")
> `これはその箱をあける鍵です。` ("Esta é a chave que abre essa caixa.")
> `部屋を出た後はドアを閉めなさい。` ("Feche a porta depois de sair do quarto.")
> `料金の手ごろなホテルを見つけて下さい。` ("Por favor, ache um hotel com preço acessível.")

Six hotel-room sentences for a task that asks the learner to introduce themselves. The same shape
holds for `speak:opinions-01` (prompt `"Perguntaram sua opinião. Diga o que você acha e por quê."`,
items are six polite-request lines: `サラダはご自由にお召し上がりください。`, `コップ１杯の水をください。`,
`ステーキは中位で焼いてください。` …) and for `speak:past_stories-01` (prompt
`"Alguém perguntou como foi seu fim de semana. Conte, no passado."`, items are six `health` lines
about danger, fever and stomach pain).

**Why it is a defect:** `design/speaking_path.md` §2 makes scenario the primary ordering axis and
"every stage is a usable stopping point" a hard constraint. A unit whose only production and
fluency work is the previous scenario, labelled with this scenario's prompt, breaks the labelling
contract the learner is reading.

**Fix:** in the builder, for `order == 1`, either seed the window from this unit's own `say_now`
(the six phrases are already selected before `production`/`fluency` are drawn), or carry the
previous stage's `fluency.prompt_pt` forward for that unit so the label matches what is on screen.

---

### 2. `accepted_variants` spell the topic particle は as わ, rejecting the correct kana answer

**Severity: high. 48 of the 108 production items in this slice.**

The kana form in `accepted_variants` is a phonetic transcription, so は becomes わ:

- `speak:opinions-02`: `"answer_key": "列車はあと５分で出発するはずです。"`,
  variants `["れっしゃわあとごふんでしゅっぱつするはずです", …]`
- `speak:about_you-01`: `"answer_key": "今夜は早めに寝ようと思う。"`,
  variants `["こんやわはやめにねようとおもう", …]`
- `speak:time_plans-06`: `"answer_key": "午後は外へ出たくない。"`,
  variants `["ごごわそとえでたくない", …]` (here へ also becomes え)

A learner typing the answer in kana on any IME or kana keyboard types `れっしゃはあとごふんで…`,
which is not in the list, so a correct answer is marked wrong. Nothing in the list accepts the
orthographic kana spelling.

The transcription is also internally inconsistent: を is pronounced *o* but is never converted
(28 of 28 answer_keys containing を keep it in the kana variant, e.g. `speak:politeness-05`
`にくをはんきろください`), while は and へ are. So the field is neither a usable input list nor a
consistent phonetic rendering.

**Fix:** add the orthographic kana form (は/へ/を preserved) as an additional variant, or replace
the phonetic one with it. If the phonetic form is wanted for a pronunciation hint, that belongs in
the sentence's `kana` field (where it already lives), not in the answer whitelist. Root cause is
upstream: `accepted_variants` are derived from `bank.json`'s `kana`, so the fix is one change in
`scripts/export/build_speaking_path.py`, not 48 edits.

---

### 3. Full-width characters in `answer_key` with no half-width accepted variant

**Severity: high. 13 production items in this slice.**

| Unit | `answer_key` | full-width chars | ASCII variant offered |
|---|---|---|---|
| `speak:about_you-01` | `部屋には家具が４点あった。` | `４` | no |
| `speak:about_you-03` | `ＳＰの仕事の様子が今日テレビで放送されました` | `ＳＰ` | no |
| `speak:about_you-04` | `「辛いものって、好き？」「大好き」` | `？` | no |
| `speak:time_plans-01` | `夫は大抵８時には仕事に出かけます。` | `８` | no |
| `speak:time_plans-03` | `「いつ起きるの？」「朝八時だよ」` | `？` | no |
| `speak:time_plans-06` | `午後には上がるだろうか？` | `？` | no |
| `speak:past_stories-03` | `元気？旅行は良かった？` | `？？` | no |
| `speak:politeness-02` | `もっとゆっくり話してください！` | `！` | no |
| `speak:politeness-03` | `頼みたいことがあります。ちょっとお願いしてもよろしいでしょうか？` | `？` | no |
| `speak:opinions-02` | `列車はあと５分で出発するはずです。` | `５` | no |
| `speak:opinions-02` | `列車は６時到着のはずだった。` | `６` | no |
| `speak:opinions-06` | `４０近いはずだ。` | `４０` | no |
| `speak:real_talk-06` | `ＵＮというのは何を表わしていますか。` | `ＵＮ` | no |

A Japanese IME in half-width mode produces `5分`, `40`, `UN`, `?` and `!`. All of those are
rejected. The kana variants make this visible and unfixable by the learner: `speak:opinions-06`
offers only `よんじゅうちかいはずだ`, so there is no way to answer `４０近いはずだ` with digits at all
(`40近いはずだ` and `四十近いはずだ` are both absent).

**Fix:** NFKC-normalize both the stored variants and the learner's input before comparison, or emit
half-width variants alongside the full-width ones.

---

### 4. `speak:politeness-05` requires a character that cannot be typed

**Severity: high. One item, but it is unanswerable.**

> `"answer_key": "肉を半㌔ください。"`
> `"accepted_variants": ["にくをはんきろください", "にくをはんきろください。", "肉を半㌔ください", "肉を半㌔ください。"]`

`㌔` is U+3314 SQUARE KIRO, a CJK compatibility ligature. No standard IME emits it; `キロ` and `kg`
do. The only reachable answer is the all-kana form, and `肉を半キロください` is not accepted. The
sentence also carries into `speak:politeness-04` `say_now` and `speak:politeness-06` `fluency`,
where it is shadowed and read aloud, so the compatibility glyph is also what the learner sees as a
model of written Japanese.

**Fix:** add `肉を半キロください`(`。`) to the variants, or drop `sent:tatoeba-1490062` from the path
in favour of an equivalent that spells キロ normally.

---

### 5. `speak:about_you-03` production prompt reads as São Paulo in pt-BR

**Severity: medium-high. One item, learner-facing pt-BR.**

> `"prompt_pt": "Hoje passou na TV uma reportagem sobre o trabalho dos seguranças (SP)."`
> `"answer_key": "ＳＰの仕事の様子が今日テレビで放送されました"`

The bank's own token gloss for `ＳＰ` is "SP (security police, guarda-costas/segurança de
autoridades)", so the parenthesis is meant to carry that abbreviation. To a Brazilian reader,
`seguranças (SP)` reads as security guards *in São Paulo*: `(SP)` after a noun phrase is the state
abbreviation, and nothing in the prompt signals otherwise. The learner then has to guess that the
target string is the Japanese loan `ＳＰ`, which the prompt never asks for.

**Fix:** rewrite the prompt so the abbreviation is the thing being named, for example
`"Hoje passou na TV uma reportagem sobre o trabalho dos SP (seguranças de autoridades, no Japão)."`
Note this prompt is copied verbatim from `sent:jec-4753`'s `translation["pt-BR"]`, so fixing the
bank record fixes the prompt.

---

### 6. Fluency prompts name a speech act the item set does not supply

**Severity: medium. Two stages, quantified.**

Distinct from finding 1: these are units 02 to 06, where the window does contain this stage's own
material and the mismatch is in what was selected.

**`past_stories`.** The prompt is the same in all six units:
`"Alguém perguntou como foi seu fim de semana. Conte, no passado."` Past-tense items per unit:
1/6, 3/6, 2/6, 1/6, 1/6, 1/6, so **9 of 36 fluency slots across the stage are in the past**.
`speak:past_stories-03` supplies:

> `今年のファッションは去年とはまったく違う。` (present) · `旅行は楽しい。` (present) ·
> `とても楽しい。` (present) · `人生は楽しい。` (present) · `昔の思い出が急に心に浮かんだ。` (past) ·
> `熱が上がった。` (past)

Four of six are present-tense adjectives; the drill is supposed to be a past-tense retell.

**`time_plans`.** Prompt: `"Um amigo quer marcar alguma coisa. Combine dia e horário."`
`speak:time_plans-06` supplies:

> `今日はけっこう風が強いね。` (weather) · `世界はいつ終わるのだろうか。` ("Quando será que o mundo
> vai acabar?") · `私は二時間以上も待った。` · `今日はちょっと頭が痛いの。` · `今日は頭がさえません。` ·
> `「いつ起きるの？」「朝八時だよ」`

One of six is about arranging a time. `speak:time_plans-05` has the same 1/6 ratio.

**Fix:** add a per-stage predicate to the fluency selector. For `past_stories`, require a past
inflection (the data is already there: `tokens[].inflection`). For `time_plans`, require a token
from the stage seed lexicon (`design/speaking_path.md` §5) rather than accepting any
already-known sentence.

---

### 7. `私は明日死ぬかもしれない` is a `say_now` phrase in the scheduling stage, and repeats 9 times

**Severity: medium.**

`sent:tatoeba-152614` ("Eu talvez morra amanhã") is one of the six `say_now` and `shadowing`
phrases of `speak:time_plans-02`, a unit titled `"Quando, que horas, combinar, parte 2"`. It then
returns in the `fluency.items` of `time_plans-03`, `-04` and `-05`, and as a `gram:kamo-shirenai`
drill example in `opinions-01`, `-03`, `-04`, `-05` and `-06`. Nine appearances across this slice.

`design/speaking_path.md` §4 defines `say_now` as "the things you can use today, out loud", and
`shadowing` means repeating it aloud. Neither the scenario (making plans) nor the register makes
this a phrase to hand a beginner and have them repeat.

**Fix:** the same `gram:kamo-shirenai` drill set already carries `明日は雨かもしれない。` and
`何か起きたかもしれない。`; either is a drop-in replacement for both the `say_now` slot and the drill
examples.

---

### 8. `speak:real_talk-06` puts a suicide sentence in `say_now` / `shadowing`

**Severity: medium.**

> `sent:tatoeba-95365` · `彼女が自殺したというのは本当か。` · "Será que é verdade que ela se suicidou?"

One of six phrases the unit asks the learner to say and shadow. It is there because it carries
`という`, one of the unit's five target patterns; the same unit's `say_now` already carries
`両方とも好きというわけではない。` for that pattern, and the bank holds many more (`speak:real_talk-05`
alone uses three: `ＵＮというのは何を表わしていますか。`, `スペシャルというのはどんな味ですか。`,
`雪が青いというのは誤りだ。`). `corpus/vocab`'s `register` enum exists to flag sensitive items, but no
such gate is applied when `say_now` is filled.

**Fix:** exclude the sentence from the path, or add a content gate to the `say_now` selector before
the frequency sort. Related, lower priority: `speak:about_you-06` `say_now` carries
`悲しいことに多くの日本人が亡くなりました。` ("Infelizmente, muitos japoneses morreram") in the "Falar de
você" stage, and it becomes `speak:time_plans-01`'s production target.

---

### 9. `speak:past_stories-04` asks the learner to produce a malformed honorific

**Severity: medium.**

> `"prompt_pt": "Por favor, tenha uma refeição maravilhosa."`
> `"answer_key": "すばらしい食事を経験下さい。"`

Two problems in one item. First, an invitation to enjoy a meal is not "contar o que aconteceu";
the sentence has no past tense at all, in the past-narration stage. Second, `経験下さい` is defective
as an honorific request: the form is `ご経験ください` (or plainly `経験してください`), and the analyzer
confirms the reading is broken, tokenizing `下さい` as the verb "(me) dê, por favor" attached to the
noun `経験` (the bank's English gloss, "Have a wonderful eating experience", shows this is a
translated ad line, not natural Japanese). It is one of only three `meaning-output` items in the
unit, so the learner is asked to type it out.

The sentence also sits in `past_stories-03` `say_now` and in the `fluency.items` of `-05` and `-06`.

**Fix:** drop `sent:tatoeba-214558` from the path. If a `経験` carrier is wanted, the same unit
already uses `こういう場合には経験が物を言う。` and `誰もが経験をする`.

---

### 10. Two of six phrase slots spent on a duplicate

**Severity: medium. Two units.**

`speak:politeness-01` puts both of these in `say_now` and again in `chunk_phrases`:

> `sent:tatoeba-4854` · `おめでとうございます。` · "Parabéns!"
> `sent:tatoeba-8467948` · `おめでとうございます！` · "Parabéns!"

Identical Japanese apart from the final punctuation, identical pt-BR. The unit therefore teaches
five phrases, not six, and its `chunk_phrases` list (the set expressions taught whole) is one item
presented twice. The pair travels together into the `fluency.items` of `politeness-02` and
`politeness-03`, costing those sets a slot each as well.

`speak:real_talk-06` does the same with:

> `sent:tatoeba-77972` · `両方とも好きなわけではない。` · "Não é que eu goste dos dois."
> `sent:tatoeba-77973` · `両方とも好きというわけではない。` · "Não é que eu goste dos dois."

Here the two are a genuine `わけではない` / `というわけではない` minimal pair, which could be a teaching
point, but nothing in the unit says so and both carry the same translation, so on screen they are
the same phrase twice.

**Fix:** dedupe candidates on punctuation-stripped `jp` and on identical `translation["pt-BR"]`
before filling `say_now`, `chunk_phrases` and `fluency.items`.

---

### 11. Production items that require reproducing a two-speaker dialogue

**Severity: medium. Three items.**

- `speak:about_you-04`: prompt `'"Comida picante, você gosta?" "Adoro."'`,
  answer `「辛いものって、好き？」「大好き」`
- `speak:time_plans-03`: prompt `'"Quando você acorda?" "Às oito da manhã."'`,
  answer `「いつ起きるの？」「朝八時だよ」`
- `speak:past_stories-03`: prompt `'Tudo bem? A viagem foi boa?'`, answer `元気？旅行は良かった？`

The `meaning-output` strand asks for one produced utterance. These ask for two turns plus the
quote brackets, and the variant lists require the brackets: `speak:time_plans-03` accepts only
`「いつおきるの?」「あさはちじだよ」` and the kanji original, so a learner who types the two turns without
`「」` is wrong. The pt-BR prompt renders the turns with straight double quotes, which gives no cue
that Japanese corner brackets are expected.

**Fix:** exclude sentences containing `「` from the `production` candidate pool (they remain fine as
`say_now` and `fluency` material), or strip brackets before comparison and add a bracket-free
variant.

---

### 12. Generated drill examples with off-standard orthography

**Severity: low-medium. Two drill sets, five examples.**

`speak:time_plans-03`, drill for `gram:gp-93`, all three examples write 以下 in hiragana:

> `五十点いかは合格できません` · `三歳いかの子供は無料です` · `今日の気温は十度いかです`

以下 is written in kanji in normal Japanese, and bare `いか` is ambiguous (以下 / 医科 / 烏賊). The same
unit lists `以` in its `kanji_recognition` array, so the unit asks the learner to recognise a kanji
its own examples avoid.

`speak:time_plans-06`, drill for `gram:kara`, two of three examples are space-separated:

> `あたまが いたいから かえります` · `さむいから まどを しめてください`

No other sentence in the path uses spaces; the third example in the same set
(`今のはノーカンだからね。`) is written normally, as is the whole `gram:node` set in the same unit. All
five are `ai_generated: true` records, so this is a generation artifact that survived into the units.

**Fix:** rewrite the five bank records (`gen-a81f2084ea99`, `gen-e1c2cfd5e350`, `gen-0877b1b2f764`,
`gen-061ed9aa1785`, `gen-5b9e3ecfbcaf`) with standard orthography; the unit files need no change.

---

### 13. `speak:past_stories-01` fluency includes a classical-Japanese proverb

**Severity: low-medium. One item.**

> `sent:tatoeba-145552` · `心熱けれど肉体は弱し。` · "O espírito está pronto, mas a carne é fraca."

`熱けれど` and the predicative `弱し` are 文語 (classical) forms. The learner cannot use, vary or
conjugate them, and the fluency strand is a timed speak-aloud drill on material the learner is
supposed to already own. It is one of six items in that unit's set.

**Fix:** exclude `し`-final classical predicates and `けれど`-attached classical adjectives from
`fluency.items` and `say_now`. The pattern is detectable from the analyzer output
(`inflection_type` on the final predicate).

---

### 14. `seconds_target` is the same constant for item sets that differ 2x in length

**Severity: low.**

`fluency.seconds_target` is `48` in all 36 units. The six items total between 69 and 135 kana:

| Unit | total kana in `fluency.items` | implied pace at 48 s |
|---|---|---|
| `speak:politeness-03` | 69 | 1.4 kana/s |
| `speak:past_stories-03` | 83 | 1.7 kana/s |
| `speak:time_plans-01` | 127 | 2.6 kana/s |
| `speak:about_you-06` | 135 | 2.8 kana/s |

The same number therefore encodes two different tasks, and in the lightest unit it leaves about
half the window unused. As a fluency target (the strand exists to push automaticity, per the unit's
own `strand: "fluency"`) a constant that is loose in some units and tight in others is not
measuring the same thing twice.

**Fix:** derive it, for example `ceil(total_kana / target_rate)` with one documented rate, and keep
the value in the unit so it stays diffable.

---

### 15. `speak:past_stories-02` production drills one frame three times

**Severity: low.**

All three `meaning-output` items of the unit share the predicate and the frame:

> `旅行は楽しい。` ("Viajar é divertido.") · `とても楽しい。` ("É muito divertido.") ·
> `人生は楽しい。` ("A vida é divertida.")

Noun + は + 楽しい, twice, plus the adverbial variant. The unit's entire production budget produces
one adjective in one pattern, in a stage whose point is narrating past events.

**Fix:** require distinct final predicates across a unit's three `production` items when the
candidate pool allows it; this unit's own `say_now` offers `私は昨日生まれたわけではない。` and
`このお金は夏の旅行にとっておこう。` as alternatives.

---

## Counts

| | |
|---|---|
| Unit files reviewed | 36 |
| Content elements inspected | 3,078 |
| of which: `say_now` + `chunk_phrases` IDs | 218 |
| of which: `production` items (prompt / answer / variants) | 108 items, 418 variants |
| of which: `fluency` blocks / items | 36 / 216 |
| of which: `drills` sets / examples | 177 / 531 |
| of which: `checkpoint` items / distractors | 177 / 450 |
| of which: `kanji_recognition` / `words` / `patterns` entries | 215 / 288 / 208 |
| (subset of the above) authored pt-BR strings: `title`, `fluency.prompt_pt` | 72 |
| **Findings** | **15** |
| high | 4 |
| medium-high | 1 |
| medium | 6 |
| low-medium | 2 |
| low | 2 |

Nine of the fifteen (1, 2, 3, 6, 10, 11, 12, 13, 14) are single changes in
`scripts/export/build_speaking_path.py` or in five bank records, not per-unit edits.
