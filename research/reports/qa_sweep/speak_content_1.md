# QA sweep: `course/speak` content, stages arrival / eating / getting_around / shopping / lodging / health

**Scope:** the 36 unit files under `course/speak/{arrival,eating,getting_around,shopping,lodging,health}/unit-0*.json`,
with every `say_now`, `chunk_phrases`, `drills[].examples`, `production[].sentence` and `fluency.items` ID
resolved against `corpus/sentences/bank.json`, and every `words[]` ID resolved against `corpus/vocab/*.json`.

**Questions asked:** are the selected phrases what a traveler actually needs in that situation; natural spoken
register; correctly translated; well-ordered within the stage; are drill/production prompts natural pt-BR; is
anything bookish or written-register in a speaking path.

**Out of scope by instruction:** sentence `structure_explanation` fields (being re-authored concurrently).

**Authority for pt-BR judgements:** `design/translation_style.md`.

**Read-only run.** Nothing outside this file was modified.

---

## Summary

The six stages are not six curated survival scenarios. They are six buckets of Tatoeba sentences selected by
**keyword and grammar-tag match**, then labelled with a scenario title and a scenario `fluency.prompt_pt` that
the contents cannot deliver. The `coverage:n5` / `coverage:n4` / `mined` / `jec` provenance tags are the visible
fingerprint: **99 of the 216 `say_now` slots** carry one, meaning the phrase was pulled in to cover a vocab or
grammar item, not because a traveler would say it. In `lodging` it is 34 of 36.

Three of the six stages do not contain the single phrase their own title promises:

| Stage | Title / task promised | The phrase is absent |
|---|---|---|
| `shopping` | "Isto, aquilo, quanto custa" / "Pergunte o preço e feche a compra" | no price question anywhere in 36 slots |
| `lodging` | "Dormir e resolver problemas" / "Faça o check-in" | no check-in phrase anywhere in 36 slots |
| `health` | "Emergência e saúde" / "peça ajuda" | no emergency phrase anywhere in 36 slots |

On top of that, `production` and `fluency` are wired to a rolling window of *previously seen* sentences that
crosses stage boundaries, so the scenario prompt and the material handed to the learner are systematically
disjoint (F04). And two items actively train the learner to say something rude (F01, F08).

Findings are ranked. Severity: **S1** = ships something harmful or embarrassing to a learner; **S2** = the stage
fails its own stated objective; **S3** = wrong register / wrong data; **S4** = style and polish.

---

## F01 (S1) `health-06` drills the learner to produce an insult, in the emergency stage

`course/speak/health/unit-06.json` → `production[2]`, and `health-05` → `say_now[3]`
(`sent:tatoeba-5147343`):

```
prompt_pt:   "Se você tivesse metade de um cérebro, seria perigoso!"
answer_key:  お前は脳の半分があったら，危ない!
```

Two separate defects in one item.

**Japanese.** This is a jokey put-down ("if you had half a brain you'd be dangerous"), built on **お前**, a
second person pronoun that is confrontational toward anyone who is not an intimate. The stage is titled
"Emergência e saúde" and its `fluency.prompt_pt` is *"Você não está bem. Explique o que está sentindo e peça
ajuda."* A learner who has been drilled on this line and reaches for a half-remembered phrase in a clinic will
insult the person they are asking for help. Nothing in the unit marks it as an insult: the `words[]` list
introduces only 半分 and 危ない, and 脳 and お前 are not glossed at all.

**pt-BR.** "Se você tivesse metade de um cérebro, seria perigoso!" is a word-for-word calque of the English
idiom. It does not carry the insult in pt-BR; read literally it means the opposite of what is intended, and a
Brazilian learner will not understand that the Japanese is rude. This violates `translation_style.md` §1
(natural pt-BR, not a mirror) and §2 (register mirrors the Japanese; flag offensive items).

**Fix:** remove `sent:tatoeba-5147343` from `health-05.say_now` and from `health-06.production`. Replace the
production slot with a first-person symptom line the stage already needs, e.g. `sent:tatoeba-198568`
(喉がひりひりして、ちょっと熱があるんです) is already in `health-05.say_now` and is the right register. If the
sentence is kept in the bank at all, its `register` must be marked and the pt-BR reworked so the insult reads
as an insult.

Minor, same item: the Japanese uses a full-width Latin comma `，` (U+FF0C) instead of `、`, and all four
`accepted_variants` preserve it.

---

## F02 (S2) The `shopping` stage never teaches a price question

Stage title: **"Isto, aquilo, quanto custa"**. `fluency.prompt_pt` in all six units: *"Você está numa loja com
uma coisa na mão. Pergunte o preço e feche a compra."*

Across all 36 `say_now` slots in `shopping-01..06` there is not one price question, not one purchase phrase, not
one これください. Scanning the 36 Japanese strings for いくら / 円 / ください / お願いします / カード / 袋 /
レシート / 会計 returns exactly one hit, and it is a false positive:

```
sent:tatoeba-229178  いくらお礼を言っても言い切れない。
                     "Por mais que eu agradeça, nunca será o bastante."
```

That is いくら in its "however much" adverbial sense, not the price word.

What the stage teaches instead, in order: あれはキジです ("Aquilo é um faisão."), あれはネコですか,
あれはテーブルです, 問題はお金がないということです, 私はこれは自明のことと思う ("Eu acho que isto é algo
óbvio."), 私たちはそれを公にしようと思う ("Nós pretendemos tornar isso público."), 自分でそれをしなければ
ならない, 彼が郊外に家を買った, これを壊したのはだれですか.

The sentence the stage needs exists in the bank and is deployed everywhere else:

```
sent:tatoeba-5332  いくらですか？  "Quanto custa?"
  used as a gram:da-desu drill example in:
    speak:eating-04, speak:getting_around-06, speak:lodging-05, speak:about_you-05,
    speak:about_you-06, speak:time_plans-05, speak:time_plans-06, speak:health-04,
    speak:health-05, speak:past_stories-02, speak:past_stories-06, speak:opinions-02
  used in speak:shopping-01..06: NEVER
```

Twelve units across eight stages get "Quanto custa?" as filler for a copula drill; the stage named after it gets
none. A learner who stops after stage 2 (which `course/speak/INDEX.md` promises is "um ponto de parada usável")
cannot buy anything.

**Fix:** rebuild `shopping` `say_now` around the transaction: いくらですか / これください / これをください /
カードで払えますか / 袋いりません / もう少し安くなりませんか / 試着してもいいですか. `sent:tatoeba-5332` and
`sent:tatoeba-1484951` (いくらほしい？) are already in the bank. The demonstratives (これ/それ/あれ) are the
grammar vehicle, not the content: keep one あれは何ですか, drop the faisão / gato / mesa series.

---

## F03 (S2) The `health` stage never teaches an emergency phrase, and unit 1 is about other people's doctors

Stage title **"Emergência e saúde"**, `fluency.prompt_pt`: *"Você não está bem. Explique o que está sentindo e
peça ajuda."*

`health-01.say_now` in full:

```
医者にかかるべきだ。               "Você devia consultar um médico."          (advice to someone else)
彼は医者として有名だ。             "Ele é famoso como médico."                (third person)
彼は医者として無能だ。             "Ele é incompetente como médico."          (third person, insulting)
医者に診てもらうべきですよ。       "Você deveria se consultar com um médico"  (advice to someone else)
父は私を医者にしたがっている。     "Meu pai quer fazer de mim um médico."     (career talk)
医者に見てもらうべきだと思う。     "Acho que você deveria ser examinado..."   (advice to someone else)
```

Six of six are about a doctor rather than about the speaker's body. Two of the six (`tatoeba-110065` /
`tatoeba-110066`) are a Tatoeba minimal pair that differs only in 有名/無能 and burn two of the six slots to
teach the learner to call a doctor incompetent. Two more (`tatoeba-190902` / `tatoeba-190894`) differ only in
見/診 and both translate to near-identical pt-BR.

Across all 36 `say_now` slots in the stage there is no 助けて, no 救急車を呼んでください, no
アレルギーがあります, no 病院はどこですか, no 保険証. The first-person symptom reports amount to four lines
(お腹が痛いので今日は休みます, 喉がひりひりして…, 熱が上がった, せきがひどかったので…), and one of those
four is a past-tense narrative.

In a module whose name is "Emergência", the absence of any phrase that summons help is not a taste question.

Two supporting items in the same stage:

- `health-04.say_now[5]` / `health-05.production[0]`: 病院まで１０マイルもある, *"Daqui até o hospital são nada
  menos que dez milhas."* Japan does not use miles. A production drill that trains a Japan-bound traveler to
  state distances in miles is wrong for the target situation regardless of the grammar point (n3-made).
- `health-06.production[1]`: 風邪って人にうつすと治るってほんと？ *"É verdade que, quando você passa o
  resfriado pra outra pessoa, você sara?"* This is a folk myth. Drilling a learner to produce it, unmarked, in
  a health module is the one place the course should not be casual about medical content. The pt-BR itself is
  natural; the problem is that it is a production target in this stage.

**Fix:** re-seed `health-01` and `health-02` with first-person symptom and help-request phrases and push the
"you should see a doctor" advice-to-others cluster to a later unit. Drop `tatoeba-110066` (無能) entirely.
Drop the miles sentence. Move the folk-myth sentence to `real_talk` if it is kept, or mark it.

---

## F04 (S2, systemic) `production` and `fluency` are a rolling window of earlier `say_now`, so the scenario prompt never matches the material

This is the root cause behind most of what follows. For every one of the 36 units I checked, each
`production[].sentence` resolves to a sentence that was in the **immediately preceding unit's** `say_now`, and
`fluency.items` resolve to the `say_now` of the two to four preceding units. The window does not reset at a
stage boundary:

```
speak:shopping-01        production <- speak:arrival-06
speak:eating-01          production <- speak:shopping-06
speak:getting_around-01  production <- speak:eating-06
speak:lodging-01         production <- speak:getting_around-06
speak:health-01          production <- speak:time_plans-06
```

Because the `fluency.prompt_pt` is written per stage but the `fluency.items` come from the previous stage, the
first units of every stage pair a scenario instruction with six sentences that have nothing to do with it.

**Worst case, `getting_around-01`:**

```
fluency.prompt_pt: "Você se perdeu perto da estação. Pergunte o caminho e confirme se entendeu."
items:
  以下の通り注文いたします。            "Faço o pedido conforme o que segue abaixo."
  旅行中はほとんど米は食べられなかった。 "Durante a viagem, a gente quase não conseguiu comer arroz."
  お箸で食べるのは難しいですか？        "É difícil comer com hashis (pauzinhos)?"
  ディナーはたいがいコーヒーで終わる。   "O jantar quase sempre termina com um café."
  去年トマトを作ったがとてもおいしかった。"No ano passado eu plantei tomates..."
  注文を受けてから作るのが受注生産です。 "Produção sob encomenda é fabricar só depois de receber o pedido."
```

Six for six from the restaurant stage. The learner is told to ask for directions and handed a purchase order
and a tomato harvest.

The same unit's three `production` prompts are the tail of `eating-06`:

```
"Ele levava água com afinco até a boca dela."          -> 彼がせっせと彼女の口に水を運んだ
"Naquela época, uma xícara de café custava 200 ienes." -> あの頃はコーヒー１杯が２００円だったよ。
"Naquela época, eu não gostava de cerveja."            -> 私は、そのころビールが嫌いだった。
```

**Second worst, `eating-01`:**

```
fluency.prompt_pt: "Você sentou num restaurante. Peça o que quer comer e beber, e diga se está bom."
items: 本をたくさん買ったんだ / これを壊したのはだれですか / 家を買ったんだってね /
       彼が郊外に家を買った / 自分でもそれをやってみます / 自分の力だけでそれをできる
```

All six are the `shopping` stage's book-and-house-buying tail. `eating-02` repeats four of the same six under
the same restaurant prompt.

**Fix:** `fluency.items` must be filtered to the current stage's own scenario pool (still respecting
`zero_new_tokens` by drawing from earlier units *of the same stage*, plus the stage's own unit 1 where needed),
and `production[].sentence` likewise. If the generator cannot fill a slot from in-stage material, that is the
signal that the stage's `say_now` is too thin, not a licence to borrow from the previous stage. Where a stage
genuinely has no earlier in-stage material (unit 1), drop `fluency` for that unit rather than pairing a scenario
prompt with off-scenario items; `arrival-01` already has `fluency: null` and that is the correct shape.

---

## F05 (S3) Written-register and literary sentences in a speaking-first path

`design/speaking_path.md` positions these stages as things the learner says out loud. The following are all
`say_now` (and several are `production` answer keys), and none of them is spoken Japanese.

**`health-04.say_now[4]`, also `health-05.production[1]` (`sent:tatoeba-145552`):**

```
心熱けれど肉体は弱し。   "O espírito está pronto, mas a carne é fraca."
```

This is **Classical Japanese** (bungo): 〜し is the classical terminal form of an adjective, 熱けれど is the
classical concessive. It is a scripture quotation. It is tagged `level: n3` and drilled as a production target
in a survival speaking module. No living Japanese speaker says this sentence.

**`eating-06.say_now[0]`, also `getting_around-01.fluency` (`sent:tatoeba-191220`):**

```
以下の通り注文いたします。  "Faço o pedido conforme o que segue abaixo."
```

以下の通り ("as follows below") is purchase-order and business-letter boilerplate. It is the first item of the
final unit of "Comer e beber fora". A traveler ordering food says すみません、これください, not this.

**`eating-04.say_now[3]`, also `eating-05.production[2]` (`sent:tatoeba-13440729`):**

```
注文を受けてから作るのが受注生産です。
"Produção sob encomenda é fabricar só depois de receber o pedido."
```

受注生産 is manufacturing/supply-chain jargon. The learner is drilled to *produce* a definition of build-to-order
production while sitting in a restaurant.

**`health-05.say_now[2]` (`sent:tatoeba-145398`):**

```
新しい市の病院を建てる計画が進行中である。
"O plano de construir um novo hospital municipal está em andamento."
```

である体 plus 進行中 is newspaper and report register. It cannot be said aloud in a conversation.

**`eating-04.say_now[0]`, also `eating-05` and `eating-06.fluency` (`sent:tatoeba-179391`):**

```
空気と人間との関係は水と魚との関係と同じだ。
"A relação entre o ar e o ser humano é igual à relação entre a água e o peixe."
```

An aphorism, three times in one stage, in "Comer e beber fora".

**`getting_around-06.say_now[1]` (`sent:tatoeba-141046`):**

```
選ぶべき道は自由か死だ。  "O caminho a se escolher é liberdade ou morte."
```

Pulled in to cover 道 in the "get where you want to go" stage. It is a political motto.

**`eating-01.say_now[5]`, also `eating-02.production[0]` (`sent:tatoeba-171644`):**

```
今日は魚の食いが悪い。  "Hoje os peixes não estão mordendo a isca."
```

食いが悪い here is angling jargon. It was selected to cover 魚 in the eating-out stage, and then promoted to a
production prompt: the learner is asked to say a fishing report while ordering dinner.

**Fix:** add a hard register filter to the `say_now` selector. A sentence is eligible only if a private
individual could plausibly say it aloud to another person in the stage's situation. Concretely, exclude
`である` predicates, classical inflections (terminal 〜し, 〜けれど on adjectives), and sentences whose tokens
carry technical/business `field` tags. The `coverage:*` tag should never be sufficient on its own to place a
sentence in `say_now`; coverage-only sentences belong in reading input, not in a speaking slot.

---

## F06 (S2) The `lodging` stage is a keyword dump of 部屋 sentences, mostly said *to* a guest, not *by* one

The stage promises check-in and problem-solving. What the 36 slots contain is nearly every Tatoeba sentence
that has 部屋 in it, in whatever speaker role it happened to come in.

Things a guest cannot say, all in `say_now`:

```
lodging-02  部屋の中に入ってください。          "Entre no quarto, por favor."
lodging-02  部屋の中に一人づつ入ってください。  "Entrem no quarto um de cada vez, por favor."
lodging-02  部屋にはノックなしで入らないでください。 "Por favor, não entre no quarto sem bater."
lodging-04  部屋に入ったらドアを閉めなさい。    "Feche a porta quando entrar no quarto."
lodging-05  部屋を出た後はドアを閉めなさい。    "Feche a porta depois de sair do quarto."
lodging-04  部屋の窓は閉めておくように。        "Deixe as janelas do quarto fechadas."
lodging-06  部屋の大きさは、これで十分ですか。  "O quarto é grande o suficiente para você?"
```

These are the receptionist's, the landlord's or the notice board's lines. 〜なさい and the bare 〜ように
imperative are what an adult says to a child or a written notice says to a reader; a traveler using them on
hotel staff is rude. Two of them (`tatoeba-84181`, `tatoeba-84203`) are `production` answer keys, so the course
is actively training that.

Pure narration, also in `say_now`:

```
lodging-01  部屋は真っ暗だった。          lodging-01  部屋には家具がない。
lodging-01  彼は一日中ベッドで寝てばかりいた。  lodging-03  部屋には子ども達が少しいた。
lodging-05  部屋には数人の学生がいた。    lodging-06  部屋には家具が４点あった。
lodging-04  来年ここに新しいホテルが建てられるだろう。
```

`lodging-04.production[1]` asks the learner to produce **部屋には何人の少年がいますか** ("Quantos meninos estão
no quarto?"). Set aside that it is useless at a hotel desk: an adult traveler asking a stranger how many boys
are in a room is a sentence the course should not put in a learner's mouth.

`lodging-06.say_now[1]`: 部屋をいそいでかたづけてほしいの ("Quero que você arrume o quarto rápido."). The
casual 〜てほしいの with the soft-casual sentence-final の, aimed at service staff, is a politeness hazard the
unit does not flag.

Genuinely useful, and there are only three in the whole stage: 部屋の電気がつかない, 部屋を見せていただけますか,
朝、シャワーを使ってもいいですか. There is no チェックインお願いします, no 予約した〇〇です, no
部屋を変えてもらえますか, no お湯が出ません, no Wi-Fiのパスワードを教えてください.

Minor data point inside the stage: `lodging-02.say_now[1]` uses **一人づつ**. Modern standard orthography is
ずつ; づつ is a pre-1946 spelling. It should not be a model form in a `say_now` slot.

**Fix:** select `lodging` `say_now` by speaker role, not by the 部屋 keyword. Guest-side check-in and complaint
phrases first, then room description. Drop every 〜なさい / 〜ように instruction sentence from `say_now` and
`production`.

---

## F07 (S3) `arrival` drills the learner to produce the shop clerk's apology, four times

`arrival-05.say_now` spends three of six slots on the same phrase, and all three carry an identical pt-BR
translation, so nothing distinguishes them for the learner:

```
sent:tatoeba-125944  長い事お待たせしてすみません。      "Desculpe por tê-lo feito esperar tanto tempo."
sent:tatoeba-125913  長くお待たせしてすみませんでした。  "Desculpe por tê-lo feito esperar tanto tempo."
sent:tatoeba-125967  長い間、お待たせしてすみませんでした。"Desculpe por tê-lo feito esperar tanto tempo."
```

`arrival-06.say_now[2]` adds a fourth variant (こんなに長い間待たせてすみません, "Desculpe por tê-lo feito
esperar por tanto tempo."), and `arrival-06.production[2]` makes `tatoeba-125967` a production target. Four of
the twelve `say_now` slots in the stage's last two units are the same sentence.

Beyond the redundancy, the phrase is the wrong side of the counter. **お待たせする** is 謙譲語 (お + stem +
する): the humble form used by the person who provides a service toward the person who waited. It is what the
shop, the restaurant and the hotel desk say to *you*. A traveler in "Chegar e cumprimentar" needs すみません,
お待たせしました at most, and mostly needs to *recognise* お待たせしてすみません when it is said to them, not
produce it.

The pt-BR is a second problem. **"Desculpe por tê-lo feito esperar tanto tempo."** uses the proclitic-infinitive
construction *tê-lo feito*, which is written, formal, near-Lusitanian pt-BR. No Brazilian says it aloud. Natural
pt-BR for this apology is *"Desculpa a demora."* or *"Foi mal te deixar esperando tanto."* This is exactly the
"never a literal mirror, register-aware, natural pt-BR" contract in `translation_style.md` §1 and §2, and it is
being used as a `production.prompt_pt`, which means it is the text the learner reads and has to translate.

**Fix:** keep at most one お待たせ sentence, move it to a recognition-only slot, and re-translate as
"Desculpa a demora." Free the three freed slots for arrival phrases the stage lacks (よろしくお願いします,
はじめまして, 日本語がわかりません).

---

## F08 (S3) Drill example sets contain rude, startling and off-domain sentences

`drills[].examples` are shadowed and repeated aloud. These are what the selector chose by grammar tag alone.

**痔があります ("Tenho hemorroidas.")** as the `gram:gp-8` (polite ます) example, in three units of three
different stages: `getting_around-06`, `lodging-01`, `health-03`. Alongside どこに行きますか and 兄がいます.

**`lodging-02`, `gram:te-kudasai` (`sent:tatoeba-74723`):**

```
「どいてください」「やんのか？あんちゃん」
"Saia da frente, por favor." "Quer brigar, garotão?"
```

A street-confrontation exchange as the example of "please do X", in the hotel stage. やんのか is aggressive
slang.

**`shopping-01`, `gram:da-desu`,** i.e. the copula drill in the very first unit of stage 2, at
`cumulative_known_vocab = 43`:

```
彼がばかだなんてとんでもない。      "Que ele é bobo?! De jeito nenhum."
どいつもこいつもばかばっかりだ。    "Não tem um que preste, é tudo idiota."
```

どいつもこいつも is derogatory. Two of the three examples of "how to say X is Y" are insults.

**こいつは悪いウサギだった ("Esse aí era um coelho mau.")** as a `gram:gp-32` example in four units
(`arrival-05`, `eating-06`, `lodging-01`, `lodging-03`). こいつ is a rough pronoun; the sentence is also
meaningless out of its source context.

**`health-05`, `gram:gp-12` (がある):** 富には翼がある ("A riqueza tem asas.", a proverb, n1) and
嵐のきざしがある ("Há sinais de tempestade.", n1) as beginner existence-verb examples.

**`getting_around-06` and `lodging-05`, `gram:da-desu`:** トピずれです。すみません。 ("É off-topic (fora do
assunto). Desculpe.") Internet-forum jargon as a です model.

**Fix:** the drill selector needs the same register filter as F05, plus an explicit block list for
pejorative pronouns (こいつ / どいつ / お前) and for body/medical content outside the health stage.

---

## F09 (S3) Drill examples repeat to the point that "drill" means nothing

Counting distinct sentences used as `drills[].examples` across the 291 drill-example slots in my six stages:

```
x9  sent:tatoeba-4856   家に来ませんか。      "Não quer vir até a minha casa?"
x8  sent:tatoeba-83623  聞こえませんよ。      "Não dá para ouvir, viu."
x7  sent:tatoeba-5057   ありがとう、それだけだよ。 "Obrigado, é só isso."
x7  sent:tatoeba-77812  力が出ません。        "Não tenho forças."
x5  sent:tatoeba-5332   いくらですか？        "Quanto custa?"
x4  sent:tatoeba-4714   こいつは悪いウサギだった。
x4  sent:tatoeba-85319  病気だったんだよ。
x4  sent:tatoeba-83696  雰囲気がいやだった。
```

Whole example triples repeat verbatim across units and stages:

```
gram:gp-149  [力が出ません。 家に来ませんか。 聞こえませんよ。]
             getting_around-04, getting_around-05, lodging-06, health-06
gram:da-desu [いくらですか？ トピずれです。すみません。 ありがとう、それだけだよ。]
             getting_around-06, lodging-05, health-04, health-05
gram:gp-32   [こいつは悪いウサギだった。 病気だったんだよ。 雰囲気がいやだった。]
             eating-06, lodging-01, lodging-03
gram:masen-ka[お茶を飲みませんか 一緒に昼ご飯を食べませんか 今からドライブに行きませんか。]
             getting_around-04, getting_around-05, lodging-03
```

`getting_around-04` and `getting_around-05` are consecutive units and share two identical drill blocks. A
learner meets 家に来ませんか nine times in six stages while never meeting a single check-in or price phrase
(F02, F06).

**Fix:** deduplicate at build time. A pattern re-drilled in a later unit should draw fresh examples, and
examples should be preferred from the current stage's own domain.

---

## F10 (S3) Declared stage bands do not match the level of the phrases

`course/speak/course.json` declares an `approx_band` per stage. Actual distribution of `say_now` levels
(36 slots per stage, from `bank.json.level`):

| Stage | declared band | n5 | n4 | n3 | n2 | n1 | at or above n3 |
|---|---|---|---|---|---|---|---|
| arrival | pre-n5 | 13 | 15 | 8 | 0 | 0 | 8/36 (22%) |
| shopping | pre-n5/n5 | 4 | 25 | 4 | 1 | 2 | 7/36 (19%) |
| eating | n5 | 3 | 18 | 10 | 1 | 4 | 15/36 (42%) |
| getting_around | n5 | 2 | 16 | 14 | 1 | 3 | 18/36 (50%) |
| **lodging** | **n5** | 0 | 3 | 30 | 2 | 1 | **33/36 (92%)** |
| **health** | **n4** | 0 | 11 | 11 | 5 | 9 | **25/36 (69%)** |

`lodging` is declared n5 and is 92% n3-or-harder. `health` is declared n4 and puts 14 n2/n1 sentences in front
of the learner, including 心熱けれど肉体は弱し (F05) and the お前 insult (F01).

Concrete jumps inside a stage, not just across it. `arrival-03` is the third unit of the pre-n5 opening stage,
at `cumulative_known_vocab = 8`, and its `say_now` includes:

```
sent:tatoeba-103106  彼は赤いズボンをはいていた。  n3, tags coverage:n5
sent:tatoeba-229458  いいえ、けっこうです。見ているだけですから。  n5
```

`arrival-04`, at `cumulative_known_vocab = 19`, opens with いいえ、知らないです。いつか覚えなければ。 (n3) and
closes with 今晩お会いできなくてすみません。 (n3, 謙譲語 お会いする + potential + negative て-form).

**Fix:** either the band labels or the selection has to move. Given F02/F03/F06, the selection is what should
move; the band labels are the honest description of what a "fala primeiro" path should contain.

---

## F11 (S3) Five units introduce a `words[]` entry whose sense contradicts the sentence it came from

In each case the bank's own token gloss for that sentence disagrees with the vocab record the unit teaches.

| Unit | `words[]` entry taught | Sentence | Token in that sentence |
|---|---|---|---|
| `eating-05` | `vocab:1132570` 米/**メートル** = "metro (unidade de comprimento)" | 旅行中はほとんど**米**は食べられなかった | 米 / **こめ** / gloss "arroz" |
| `eating-06` | `vocab:1472630` 杯/**さかずき** = "cálice de saquê, taça para bebidas alcoólicas" | あの頃はコーヒー１**杯**が２００円だった | 杯 / **ぱい** / gloss "xícara (contador de copos/xícaras)" |
| `eating-03` | `vocab:1502840` 分/**ふん** = "minuto" | 僕の**分**も入れてくれないかな | 分 / **ぶん** / gloss "porção / parte" |
| `shopping-06` | `vocab:1176240` 園/**その** = "jardim, parque" | 私は**その**本を買ったとたんに後悔した | その / adnominal / gloss "aquele / esse" |
| `shopping-05` | `vocab:2020680` 時/**じ** = "hora (sufixo), ...horas" | それが高1の**時**だから | 時 / **とき** / gloss "época; tempo" |

The `shopping-06` case is the clearest: the sentence contains the demonstrative その and the unit introduces the
noun 園 ("garden"). The `eating-05` case is the most damaging in context: in the eating stage, the learner is
taught that 米 means "metre".

These are homograph collisions from the vocab linker, and every one of them lands in a unit's "new words" list,
which is the surface the learner studies.

**Fix:** the `words[]` builder should resolve through the token's `reading`, not through the surface form.
All five sentences already carry the correct reading and gloss on the token, so the data to fix this is present.

---

## F12 (S3) Several `production.prompt_pt` strings are literary or technical pt-BR, not something anyone would be asked to say

The prompt is the text the learner reads and renders into Japanese, so it has to be plain spoken pt-BR.

```
getting_around-01  "Ele levava água com afinco até a boca dela."
eating-06          "Uma grande canoa avançava cortando a água."
eating-05          "Produção sob encomenda é fabricar só depois de receber o pedido."
health-05          "O espírito está pronto, mas a carne é fraca."
arrival-06         "Desculpe por tê-lo feito esperar tanto tempo."
health-05          "\"Como você está se sentindo?\", ele perguntou."
getting_around-05  "\"Será que já não nos encontramos em algum lugar antes?\", perguntou o estudante."
```

"com afinco" is a stiff literary adverbial no Brazilian uses in speech. "avançava cortando a água" is narrative
prose. The last two are *reported speech with a narrative tag*: asking a learner in a speaking course to produce
「気分はどうですか」と彼は尋ねた means producing the quotation frame と…尋ねた, which is a written-narration
device, not something said aloud. The useful half of those two sentences (気分はどうですか /
以前にどこかで会ったことがありませんか) is buried inside the quotation.

**Fix:** production targets should be the bare utterance. Where a bank sentence wraps a useful utterance in a
narrative frame, either exclude it or add an unwrapped generated variant.

---

## F13 (S4) `arrival` violates the em-dash prohibition, and two units carry identical or self-cancelling prompts

**Em dash.** `translation_style.md` §4: *"Never use the — (em dash) character anywhere in authored text."*
One authored string breaks it, replicated across five units (`arrival-02` through `arrival-06`):

```
fluency.prompt_pt: "Você acabou de desembarcar. Cumprimente, agradeça e peça licença — em voz alta, sem ler."
```

The other five stages' fluency prompts are clean. Fix: replace ` — ` with a comma or parentheses:
`"...e peça licença, em voz alta, sem ler."`

**Identical prompt twice in one production list.** `arrival-03.production` contains:

```
[0] prompt_pt "Bom dia!"  -> answer_key おはようございます！
[1] prompt_pt "Bom dia!"  -> answer_key おはようございます。
```

The same prompt with two different answer keys. Nothing in the prompt tells the learner which is wanted, and the
`accepted_variants` of item [0] already include the unpunctuated form, so the two items are not separable. The
same prompt is also ambiguous against おはよう, which `arrival-01` taught as "Bom dia."

Related: `arrival-02.production` is "Obrigado!" / "Obrigado." as two separate items, differing only in final
punctuation.

**Fix:** deduplicate `production` on `prompt_pt` at build time. Where two register variants of a phrase must be
distinguished (おはよう vs おはようございます), the prompt has to carry the register cue, e.g.
"Bom dia! (formal, para um desconhecido)".

---

## F14 (S3) Same Japanese phrase, two different pt-BR translations shown side by side

Within a single unit, sentences that differ only in final punctuation get different pt-BR, so the learner sees
one phrase claiming two meanings:

| Unit | Japanese | pt-BR shown |
|---|---|---|
| `arrival-01` | こんにちは | "Boa tarde." and "Olá!" |
| `arrival-02` | さようなら | "Adeus!" and "Até logo." |
| `arrival-02` | すみません | "Desculpe." and "Com licença!" |
| `arrival-01` | おはよう | "Bom dia." and "Bom dia!" |
| `arrival-01` | ありがとう | "Obrigado." and "Obrigado!" |

For こんにちは and すみません the two glosses are both correct and the split is arguably useful, but presenting
them as two undifferentiated `say_now` entries teaches nothing about *when* each applies.

**さようなら → "Até logo." is a mistranslation.** さようなら carries finality; Japanese speakers do not use it
for ordinary daily partings. "Até logo" in pt-BR means the opposite: see you shortly. The pair also contradicts
itself within one unit ("Adeus!" vs "Até logo."). A traveler taught さようなら as the default goodbye will use it
wrongly; the phrases they actually need (じゃあね, また, 失礼します) are absent from the stage.

**Fix:** collapse each punctuation-only pair into one `say_now` entry with one translation. Re-translate
`sent:tatoeba-640569` (さようなら。) as "Adeus." and add じゃあね / また明日 to `arrival`.

---

## F15 (S3) Four `arrival` slots are shopping or telephone phrases

`arrival` is "Chegar e cumprimentar", `approx_band` pre-n5. It contains:

```
arrival-03  いいえ、けっこうです。見ているだけですから。 "Não, obrigado. É que estou só olhando."
arrival-06  それより他の靴をはいてみたいのですが。       "Eu gostaria de experimentar outros sapatos..."
arrival-06  予約係をお願いします。                      "O setor de reservas, por favor."
arrival-03  彼は赤いズボンをはいていた。                "Ele estava usando uma calça vermelha."
```

The first two are shop-browsing and shoe-fitting lines that belong in `shopping` (which, per F02, badly needs
them and instead gets 予約係をお願いします and それより他の靴… as its unit-01 production carryover). 予約係を
お願いします is a telephone transfer request ("reservations desk, please") and 予約係 is dated office
vocabulary. 彼は赤いズボンをはいていた is pure vocab coverage for 赤い/ズボン and has no arrival function at
all.

**Fix:** move the two shopping lines to `shopping-01`. Drop the calça sentence and the 予約係 line.

Provenance note, not a content judgement but visible from the same records: `sent:tatoeba-78964` and a further
17 sentences used in these six stages carry `tags: ["mined", "stage:"]` with an empty `stage:` value and a bare
`jp_source: "tatoeba"` with no ID. Whoever owns provenance QA should see whether that truncated tag indicates an
incomplete mining record.

---

## F16 (S4, flagged with a caveat) `accepted_variants` kana forms spell the topic particle は as わ

37 of the 105 `production` items in these six stages offer kana `accepted_variants` that render the topic
particle は phonetically as わ, and offer no orthographically correct kana alternative:

```
shopping-02  answer_key これはあれよりも小さい。
             accepted_variants kana: これわあれよりもちいさい / これわあれよりもちいさい。
shopping-04  answer_key 私たちはそれを公にしようと思う。
             accepted_variants kana: わたしたちわそれをおおやけにしようとおもう
eating-04    answer_key 私は友達とビールを飲みに行った。
             accepted_variants kana: わたしわともだちとびーるをのみにいった
```

これわ is not valid Japanese orthography. A learner who types the correct kana これは matches none of the four
variants.

**Caveat:** this follows mechanically from the bank's `kana` field, which is phonetic throughout
(あのみせわやすいってきいた for あの店は安いって聞いた), so it is probably a deliberate reading field rather
than a spelling field. If the grader normalises は/わ before comparing, this is a non-issue. I could not
determine that from the data, so I am flagging it rather than asserting it: if the grader does a literal string
match, every kana-typed answer to these 37 items is scored wrong. Worth one check by whoever owns the grading
path.

---

## F17 (S4) Two `production` items force a male-gendered pronoun with no alternative

`eating-01.production[0]` and `[1]`:

```
prompt_pt "Eu só sei isto."        answer_key ぼくはこれだけしか知らない。
prompt_pt "Eu preciso de dinheiro." answer_key ぼくはお金がいる。
accepted_variants: only ぼく forms
```

**ぼく** is glossed correctly in `corpus/vocab` as "eu (informal, masculino)", but the pt-BR prompt is the
neutral "Eu", and no 私 variant is accepted. A female learner producing 私はお金がいる is marked wrong for
giving the more appropriate answer. (Both sentences are also off-domain for the eating stage, per F04.)

**Fix:** add 私/わたし forms to `accepted_variants` wherever the answer key uses a gendered pronoun that the
pt-BR prompt does not specify, or prefer bank sentences with 私.

---

## Counts

"Flagged" counts slots named in a finding above, or mechanically identified by the checks the findings rest on.
Where a number is mechanical, the rule is stated.

| Item | Reviewed | Flagged | Basis for the flagged count |
|---|---|---|---|
| Units (6 stages x 6) | 36 | 36 | every unit appears in at least one finding (`arrival-01` via F14) |
| `say_now` phrase slots | 216 | 99 | slots whose sentence carries a `coverage:*`, `mined` or `jec` tag, i.e. selected to cover an item rather than for the scenario |
| `production` items | 105 | 105 | all 105 resolve to the immediately preceding unit's `say_now` (F04); 37 also hit F16 |
| `fluency` blocks | 35 | 35 | every block draws items from preceding units; in 14 blocks those units are in a preceding *stage* (F04) |
| `drills[].examples` slots | 291 | 34 | slots filled by the 8 over-repeated or off-register sentences listed in F08/F09 |
| Distinct corpus sentences resolved | 403 | 41 | sentences quoted in a finding |
| `words[]` vocab links checked for sense | 216 | 5 | unit teaches a reading the sentence's own token contradicts (F11) |
| **Distinct defects reported** | | **17** | S1 x1, S2 x4, S3 x8, S4 x4 |

Per-stage `say_now` coverage-tag density, which tracks how closely a stage's contents match its scenario:

| Stage | coverage/mined/jec `say_now` slots (of 36) |
|---|---|
| arrival | 6 |
| shopping | 3 |
| eating | 18 |
| getting_around | 18 |
| health | 20 |
| **lodging** | **34** |

## Checked and found clean

- `shadowing` equals `say_now` in all 36 units. Consistent and intentional.
- `chunk_phrases` is used exactly where `INDEX.md` says it is: `arrival-01`, `arrival-02` and the ありがとう
  ございます pair in `arrival-03`, i.e. the set expressions the analyser mis-lemmatises. No misuse found.
- `real_phrases: 6` matches `len(say_now)` in all 36 units; `audio: "pending"` and `needs_review: true`
  throughout, as documented.
- `fluency.zero_new_tokens` is `true` on every fluency block, and the items are drawn from already-seen
  sentences, so the no-new-vocabulary constraint holds even though the *scenario* match does not (F04).
- The AI-generated drill examples (`sent:gen-*`) are, as a group, the best-fitting material in these stages:
  お茶を飲みませんか, 一緒に昼ご飯を食べませんか, わたしは日本語が少し話せます, 頭が痛いんです,
  この服似合うかな all read as natural spoken Japanese with natural pt-BR. Where a stage needs a phrase the
  Tatoeba bank cannot supply cleanly (F02, F03, F06), generation is demonstrably capable of filling it.
- pt-BR is pt-BR throughout: "você", "ônibus", "trem", "celular"-class vocabulary, "a gente", "tá", "né", "viu"
  used naturally and register-appropriately in the casual translations. No pt-PT leakage found. No "Quanto a
  mim" crutch in any `translation` field in these six stages (it appears only in `translation_literal`, which is
  where `translation_style.md` §5 puts it).
- Apart from the single `arrival` fluency string (F13), no em dash appears in any authored prompt in these six
  stages.
