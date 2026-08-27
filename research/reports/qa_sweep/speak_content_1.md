# QA sweep: `course/speak` content, stages arrival / eating / getting_around / shopping / lodging / health

**Scope.** The 36 unit files under `course/speak/{arrival,eating,getting_around,shopping,lodging,health}/unit-0*.json`,
with all 403 distinct sentence IDs (`say_now`, `chunk_phrases`, `drills[].examples`, `production[].sentence`,
`fluency.items`) resolved against `corpus/sentences/bank.json`. 216 `say_now` slots, 105 production items,
6 fluency prompts, 111 drill blocks.

**Questions asked.** Are the selected phrases what a traveler actually needs in that situation; natural spoken
register; correctly translated; well ordered inside the stage; are drill and production prompts natural pt-BR;
is anything bookish or written-register in a speaking path.

**Out of scope by instruction.** Sentence `structure_explanation` fields (being re-authored concurrently).

**Authority for pt-BR judgements.** `design/translation_style.md`. Design contract for the path:
`design/speaking_path.md`.

**Read-only run.** Nothing outside this file was modified.

---

## Summary

The path is built by keyword match over the sentence bank, and the six stages are what that match returned,
not six curated survival scenarios. The scenario title and the scenario `fluency.prompt_pt` are then written
on top of contents that cannot deliver them. Three measurements make this concrete:

- **99 of 216 `say_now` sentences carry a `coverage:n5` / `coverage:n4` / `mined` / `jec` tag**, meaning the
  sentence was ingested to close a JLPT vocab or grammar gap, not because a traveler would say it. In
  `lodging` it is **34 of 36**.
- **`speak:shopping` never teaches a price question.** Zero of its 36 phrases contain いくらですか, 円,
  ください, カード, レジ, 会計 or 袋. The stage is titled "Isto, aquilo, quanto custa".
- **Every stage-opening unit drills the previous stage.** In `eating-01`, `getting_around-01`, `shopping-01`,
  `lodging-01` and `health-01`, **0 of 6 fluency items and 0 of 3 production items** come from that stage,
  while the fluency prompt already describes the new scenario.

Provenance is otherwise clean: **0 of 216 `say_now` sentences are `ai_generated`**, so the path's
"432 real / 0 generated" claim in `course/speak/INDEX.md` holds for this slice. The problem is selection
quality, not fabrication.

Fourteen findings below, most severe first. Severity: **S1** blocks the stage from doing its job,
**S2** is a systematic defect a learner will hit repeatedly, **S3** is a localised fix.

---

## S1-1. Every stage-opening unit practises the previous stage under the new stage's prompt

**Where.** `speak:eating-01`, `speak:getting_around-01`, `speak:shopping-01`, `speak:lodging-01`,
`speak:health-01`.

Measured: fluency items from own stage 0/6, production items from own stage 0/3, in all five.

The clearest case, `speak:eating-01`:

```
fluency.prompt_pt: "Você sentou num restaurante. Peça o que quer comer e beber, e diga se está bom."
fluency.items:
  sent:tatoeba-81631    本をたくさん買ったんだ。          "É que eu comprei muitos livros."
  sent:tatoeba-217663   これを壊したのはだれですか。      "Quem foi que quebrou isto?"
  sent:tatoeba-9240812  家を買ったんだってね。            "Soube que você comprou uma casa, né."
  sent:jec-1593         彼が郊外に家を買った              "Ele comprou uma casa no subúrbio."
  sent:tatoeba-76061    自分でもそれをやってみます。      "Eu também vou tentar fazer isso por conta própria."
  sent:tatoeba-149750   自分の力だけでそれをできる。      "Consigo fazer isso só com as minhas próprias forças."
```

Not one item is about eating. The learner is told to sit down in a restaurant and order, and handed six
sentences about buying books and houses. `speak:health-01` is the same shape: prompt
`"Você não está bem. Explique o que está sentindo e peça ajuda."` over six `time_plans` leftovers
(午後には上がるだろうか？, 金曜日の午後はお暇ですか。, 今日の午後に公園へ行きませんか。), and its three
production prompts are `"Quando foi a última vez que você cortou o cabelo?"`,
`"A escola começa às 8h10 da manhã."`, `"Amanhã começa um feriadão de cinco dias..."`.

**Why it is a defect.** `fluency` is declared `zero_new_tokens` and is the unit's only rehearsal of the
situation out loud. At a stage boundary the recycled material comes from the previous stage by construction,
so the prompt is a promise the unit provably cannot keep. `design/speaking_path.md` §2 makes "handles the
situation out loud" the success test for the path.

**Fix.** Seed unit 1's `fluency.items` and `production` from that unit's own `say_now` (they are selected
before the fluency block is built, so the material exists), or, if the review-carry-over is deliberate, give
unit 1 a distinct prompt that names the carried-over scenario: `"Antes de entrar no restaurante, revise o que
você já sabe dizer na loja."`

---

## S1-2. `speak:shopping` never teaches the learner to ask a price

**Where.** All six units of `course/speak/shopping/`. Stage title `"Isto, aquilo, quanto custa"`.
Fluency prompt (all six units): `"Você está numa loja com uma coisa na mão. Pergunte o preço e feche a compra."`

Zero of the 36 `say_now` phrases contain いくらですか, 円, ください, カード, レジ, 会計 or 袋.

What the stage teaches instead:

```
speak:shopping-01  sent:tatoeba-229742  あれはキジです。          "Aquilo é um faisão."
speak:shopping-01  sent:tatoeba-229736  あれはテーブルです。      "Aquilo é uma mesa."
speak:shopping-03  sent:tatoeba-160737  私はこれは自明のことと思う。  "Eu acho que isto é algo óbvio."
speak:shopping-03  sent:tatoeba-166326  私たちはそれを公にしようと思う。 "Nós pretendemos tornar isso público."
speak:shopping-05  sent:jec-1593        彼が郊外に家を買った       "Ele comprou uma casa no subúrbio."
speak:shopping-06  sent:tatoeba-159849  私はその本を買ったとたんに後悔した。 "Assim que comprei aquele livro, me arrependi."
```

The stage's only usable till phrases in 36 slots are `sent:tatoeba-199061` なるべく安いほうがいいです。
("De preferência, o mais barato possível.") and the pair それでいい？ / それでいいよ。

**And the missing phrase is already in the bank.** `sent:tatoeba-5332` いくらですか？ "Quanto custa?" is used
as a `gram:da-desu` drill example in `speak:eating-04`, `speak:getting_around-06`, `speak:lodging-05`,
`speak:health-04` and `speak:health-05`. It appears in every stage except the one about prices.

**Why it is a defect.** `design/speaking_path.md` §2 makes "a learner who stops after stage 4 can still land,
eat, buy and navigate" a hard constraint. A learner who completes stage 2 cannot buy anything.

**Fix.** Hard-pin a survival set into `shopping-01`/`-02` before the frequency sort runs: いくらですか,
これください, カードで払えますか, 袋いりません, もう少し安いのはありますか. `sent:tatoeba-5332` is already
audited and available. Drop あれはキジです (a pheasant is not a shopping item) and the 自明 / 公にする pair.

---

## S1-3. `speak:lodging` is 25 of 36 slots from one contiguous Tatoeba example block, and most of it is not a guest speaking

**Where.** `course/speak/lodging/unit-01..06`. IDs `sent:tatoeba-84114` through `sent:tatoeba-84243`, a
consecutive textbook run of "the room" sentences, fill 5 / 4 / 4 / 3 / 5 / 4 of the six `say_now` slots per
unit (25 of 36). 34 of the 36 `say_now` sentences carry a `coverage` / `mined` / `jec` tag.

Phrases the unit teaches a hotel guest to say:

```
speak:lodging-06  sent:tatoeba-84223  部屋には家具が４点あった。      "Havia quatro móveis no quarto."
speak:lodging-03  sent:tatoeba-84224  部屋には何人の少年がいますか。  "Quantos meninos estão no quarto?"
speak:lodging-05  sent:tatoeba-84216  部屋には数人の学生がいた。      "Havia vários estudantes no quarto."
speak:lodging-02  sent:tatoeba-84169  部屋の中に一人づつ入ってください。 "Entrem no quarto um de cada vez, por favor."
speak:lodging-04  sent:tatoeba-84203  部屋に入ったらドアを閉めなさい。 "Feche a porta quando entrar no quarto."
speak:lodging-05  sent:tatoeba-84181  部屋の窓は閉めておくように。    "Deixe as janelas do quarto fechadas."
speak:lodging-04  sent:tatoeba-78606  来年ここに新しいホテルが建てられるだろう。 "Ano que vem devem construir um hotel novo aqui."
```

These are third-person descriptions and instructions given *to* a group (なさい is a command to a child or
subordinate; 〜ように is a written notice register). A guest says none of them.

Meanwhile the stage's own declared seeds 泊まる, トイレ, 風呂 appear in **zero** phrases, and 鍵 appears once,
in `sent:tatoeba-218592` これはその箱をあける鍵です。("Esta é a chave que abre essa caixa.") which is a box
key, not a room key.

**Why it is a defect.** `design/speaking_path.md` §6 already records lodging's real-sentence yield as 18 and
says "the builder emits short units and says so". The builder instead filled all 36 slots by relaxing what
counts as a lodging sentence, which is exactly the papering-over §3.6 forbids.

**Fix.** Do the §6 mining pass for `lodging` (`raw_tatoeba_sentence` holds 248,705 sentences) targeting
チェックイン, 予約, 荷物, 部屋を変えて, お湯が出ない, Wi-Fi, 何時までですか. Until then, emit short units as
the spec says. Independently: cap any single contiguous Tatoeba id-run at about 4 sentences per stage, which
would have caught this block automatically.

---

## S1-4. `speak:health-01` teaches the learner to tell other people to see a doctor, and never to say what hurts

**Where.** `speak:health-01`, all six `say_now`.

```
sent:tatoeba-190906  医者にかかるべきだ。          "Você devia consultar um médico."
sent:tatoeba-110065  彼は医者として有名だ。        "Ele é famoso como médico."
sent:tatoeba-110066  彼は医者として無能だ。        "Ele é incompetente como médico."
sent:tatoeba-190902  医者に診てもらうべきですよ。  "Você deveria se consultar com um médico, viu?"
sent:tatoeba-84479   父は私を医者にしたがっている。 "Meu pai quer fazer de mim um médico."
sent:tatoeba-190894  医者に見てもらうべきだと思う。 "Acho que você deveria ser examinado por um médico."
```

Three of the six are the same advice ("you should see a doctor") in three renderings, and all three are
addressed *to someone else*. 彼は医者として無能だ teaches a beginner to call a doctor incompetent.
父は私を医者にしたがっている is a career sentence.

The self-report phrases the stage does own arrive only in units 5 and 6:
`sent:tatoeba-198568` 喉がひりひりして、ちょっと熱があるんです。, `sent:tatoeba-10587764` お腹が痛いので今日は休みます。,
`sent:tatoeba-121897` 熱が上がった。 The stage prompt from unit 1 onward is
`"Você não está bem. Explique o que está sentindo e peça ajuda."`

**Why it is a defect.** This is the emergency stage. Ordering inside the stage is the one axis the builder
fully controls (`design/speaking_path.md` §3.4), and it has put the least urgent material first.

**Fix.** Reorder: 痛いです / 熱があります / 気分が悪いです / 助けてください in `health-01`; move the 医者に…べき
family to unit 4 or later and keep exactly one of the three; delete 彼は医者として無能だ and
父は私を医者にしたがっている.

---

## S1-5. Classical and written-register sentences used as things to say out loud

**Where.** Six items across four stages. The worst is a production prompt.

```
speak:health-04 say_now / speak:health-05 production
  sent:tatoeba-145552  心熱けれど肉体は弱し。   "O espírito está pronto, mas a carne é fraca."
```

That is classical Japanese (bungo): けれど after a bare noun-adjective stem, and 弱し, the classical terminal
form. It is a scripture quotation, not a sentence any living speaker produces. It reached the health stage
because the tokenizer split 熱 out of 熱けれど and 熱 is a health seed (`surf: 心 熱 けれど 肉体 は 弱し`).
`speak:health-05` then asks the learner to say it aloud from the pt prompt.

```
speak:eating-06 say_now (slot 1)
  sent:tatoeba-191220  以下の通り注文いたします。 "Faço o pedido conforme o que segue abaixo."
```
A business-letter opener (以下の通り + いたします). Nobody says this in a restaurant; it is written on a
purchase order.

```
speak:eating-04 say_now / speak:eating-05 production
  sent:tatoeba-13440729  注文を受けてから作るのが受注生産です。
                         "Produção sob encomenda é fabricar só depois de receber o pedido."
```
A manufacturing-glossary definition, selected because it contains 注文.

```
speak:health-05  sent:tatoeba-145398  新しい市の病院を建てる計画が進行中である。
                 "O plano de construir um novo hospital municipal está em andamento."
```
である is newspaper register, explicitly not spoken.

```
speak:lodging-05 say_now / production
  sent:tatoeba-84181  部屋の窓は閉めておくように。  "Deixe as janelas do quarto fechadas."
```
〜ように as a bare directive is notice-board register.

```
speak:getting_around-04 say_now / speak:getting_around-05 production
  sent:tatoeba-4939  「以前にどこかで会ったことがありませんか」とその学生はたずねた。
                     "\"Será que já não nos encontramos em algum lugar antes?\", perguntou o estudante."
```
Narrative prose with a reporting verb. The production prompt is 79 characters of reported speech, which the
learner is asked to say aloud.

**Why it is a defect.** `design/speaking_path.md` §1 sets the success test as "handles the situation out
loud", and §3.5 sorts spoken registers first. None of these six is speakable material.

**Fix.** Add a register filter to the selection pass that rejects a sentence whose final predicate is
`である`, a classical terminal (`〜し` / `〜けれど` on a stem), a bare 〜ように directive, or a quotation closed
by a reporting verb (`」と…た`). Replace the eating slots from the same patterns: for 注文, use
`注文をお願いします` / `これをください` if present, otherwise mine them.

---

## S1-6. Offensive, insulting and unusable sentences used as drill and production material

**Where.** Five distinct sentences, several reused across stages.

```
speak:shopping-01  drill gram:da-desu
  sent:tatoeba-75188  どいつもこいつもばかばっかりだ。
                      "Não tem um que preste, é tudo idiota."   (bank EN: "I'm surrounded by fuckwits!")
```
Unit 1 of stage 2, alongside `sent:tatoeba-120747` 彼がばかだなんてとんでもない。 in the same three-item drill.

```
speak:lodging-02  drill gram:te-kudasai
  sent:tatoeba-74723  「どいてください」「やんのか？あんちゃん」
                      "\"Saia da frente, por favor.\" \"Quer brigar, garotão?\""
```
A street-fight taunt used to teach 〜てください in a hotel unit.

```
speak:health-05 say_now / speak:health-06 production
  sent:tatoeba-5147343  お前は脳の半分があったら，危ない!
                        "Se você tivesse metade de um cérebro, seria perigoso!"
```
An insult built on お前, asked of the learner as a production item. The Japanese is also broken (a literal
calque of "if you had half a brain"; natural Japanese would not use 〜があったら here), and it carries a
full-width `，` mid-sentence.

```
speak:eating-04  drill gram:totemo
  sent:tatoeba-4947  ドイツ人はとてもずる賢い。  "Os alemães são muito astutos."
```
A national stereotype presented as a とても example, next to `sent:tatoeba-5074` 彼はとてもセクシーだ。

```
speak:getting_around-06, speak:lodging-01, speak:health-03  drill gram:gp-8 / gram:ga-imasu
  sent:tatoeba-150175  痔があります。  "Tenho hemorroidas."
```
Used three times as an ある/いる example, including inside a navigation unit.

**Why it is a defect.** These are drill and production items, so the learner is asked to repeat and produce
them. Nothing in the pipeline screens Tatoeba's content, and Tatoeba contains this material by design.

**Fix.** Add a denylist pass over drill/production candidates before the frequency sort: slurs and insults
(ばか, あほ, お前 as a second person, けんか taunts), national and ethnic generalisations, and shock-value
medical items. A ~40-entry stoplist plus a check on the bank's own EN field would catch all five.

---

## S2-7. Seed matching keeps putting the wrong scenario's sentences in a stage

**Where.** All six stages. `scripts/export/build_speaking_path.py` matches a seed against a token
surface or lemma exactly, with a substring fallback for seeds of 4+ characters. The header comment records
that raw substring matching was already fixed once (夕食はいりません in greetings via はい). Exact token
matching does not fix it, because the offending forms are whole tokens.

Verified token evidence:

| Stage | Seed | Sentence | Why it is wrong |
|---|---|---|---|
| arrival | はい | `sent:tatoeba-103106` 彼は赤いズボンをはいていた。 "Ele estava usando uma calça vermelha." | surface tokens `彼 は 赤い ズボン を はい て い た`; はい is 履く's te-form stem, not the answer はい |
| arrival | はい | `sent:tatoeba-214119` スリッパをはいてください。 | same, `スリッパ を はい て ください` |
| arrival | はい | `sent:tatoeba-204778` それより他の靴をはいてみたいのですが。 | same. Three footwear/trousers sentences in the greetings stage |
| arrival | お願いします | `sent:tatoeba-78964` 予約係をお願いします。 "O setor de reservas, por favor." | 4+ char substring fallback; this is a hotel phone-transfer line, it belongs in `lodging` |
| shopping | いくら | `sent:tatoeba-229178` いくらお礼を言っても言い切れない。 "Por mais que eu agradeça, nunca será o bastante." | the concessive いくら…ても, not the price いくら |
| health | 熱 | `sent:tatoeba-145552` 心熱けれど肉体は弱し。 | 熱 split out of classical 熱けれど (see S1-5) |
| getting_around | 近く | `sent:jec-0673` あっという間に４０度近くまで熱が出た "Num piscar de olhos, a febre subiu para quase 40 graus." | 近く = "approximately", and this is a `health` sentence |
| getting_around | 近く | `sent:tatoeba-141381` 川の近くにテントを張った。 "Armamos a barraca perto do rio." | camping, not navigation |
| getting_around | 道 | `sent:tatoeba-141046` 選ぶべき道は自由か死だ。 "O caminho a se escolher é liberdade ou morte." | 道 metaphorical; a political slogan in the wayfinding stage |
| getting_around | 左 | `sent:tatoeba-10263746` 左の足が痛いです。 "Meu pé esquerdo está doendo." | a `health` sentence, and it opens the last navigation unit |
| eating | 水 / 魚 | `sent:tatoeba-179391` 空気と人間との関係は水と魚との関係と同じだ。 | a proverb about air and man |
| eating | 魚 | `sent:tatoeba-171644` 今日は魚の食いが悪い。 "Hoje os peixes não estão mordendo a isca." | a fishing idiom, and it is a `speak:eating-02` production prompt and a `speak:eating-03` fluency item under the restaurant prompt |
| eating | 水 | `sent:tatoeba-137747` 大きなカヌーが水をきって進んでいた。 "Uma grande canoa avançava cortando a água." | a canoe, in a restaurant stage; production prompt in `speak:eating-06` |
| eating | 食べる | `sent:tatoeba-182409` 救出されてはじめて、彼女は食べた。 "Só depois de ser resgatada é que ela comeu." | the **first phrase of the whole eating stage** is an N1 passive rescue narrative |

**Fix.** Two cheap guards, both mechanical:
1. Reject a seed match when the matched token's **lemma** is not the seed's lemma. `はい`/`履く`,
   `熱`/`熱し` and `近く`/`近い`(approx.) all fail this test and disappear.
2. Per-stage frame stoplist for idiom frames that swallow a seed: `いくら…ても`, `〜の食いが悪い`,
   `〜との関係は…と同じ`, metaphorical 道 (`選ぶべき道`, `道が開ける`).

The 予約係 case needs a third: a 4+ char substring fallback should still require the match to be a token
boundary, otherwise お願いします matches inside any polite request.

---

## S2-8. `speak:arrival` spends 8 of its 36 phrase slots on punctuation-only duplicates, and the duplication propagates into drills and production

**Where.** Eight pairs where the two `say_now` entries are the same sentence differing only in final
punctuation:

```
speak:arrival-01  おはよう          sent:tatoeba-1598216 / sent:tatoeba-3553332
speak:arrival-01  こんにちは        sent:tatoeba-373351  / sent:tatoeba-3480287
speak:arrival-01  ありがとう        sent:tatoeba-1532832 / sent:tatoeba-1531875
speak:arrival-02  さようなら        sent:tatoeba-426889  / sent:tatoeba-640569
speak:arrival-02  すみません        sent:tatoeba-408301  / sent:tatoeba-13174949
speak:arrival-02  おはようございます sent:tatoeba-335372  / sent:tatoeba-1576172
speak:arrival-03  ありがとうございます sent:tatoeba-4971  / sent:tatoeba-9559301
speak:arrival-04  聞いてくれてありがとう sent:tatoeba-10355885 / sent:tatoeba-11858059
```

`speak:arrival-01` and `-02` therefore teach three expressions each, not six. Downstream:

- **`speak:arrival-03` has two production items with the identical prompt** `"Bom dia!"`, answer keys
  おはようございます！ and おはようございます。, and overlapping `accepted_variants` (both accept the bare
  おはようございます). The two items are indistinguishable to the learner and to the grader.
- **`speak:arrival-05` production items 2 and 3 are the same sentence**, 聞いてくれてありがとう！ and
  聞いてくれてありがとう。
- **`speak:arrival-05` drill `gram:gp-108` lists that same pair** as two of its three examples.
- **`speak:getting_around-04` drill `gram:ta-tokoro`** lists `sent:tatoeba-11545589` 今着いたところよ。 and
  `sent:tatoeba-12440070` 今、着いたところよ。 (one comma apart) as two of three examples.
- `speak:getting_around-03` `say_now` opens with two "I left my umbrella on the train" sentences,
  `sent:tatoeba-4786026` and `sent:tatoeba-10899657`.
- `speak:arrival-05` carries three renderings of the same apology (`sent:tatoeba-125944`,
  `sent:tatoeba-125913`, `sent:tatoeba-125967`) with **one identical pt string**, and `speak:arrival-06` adds
  a fourth (`sent:tatoeba-231454`).

**Why it is a defect.** In a speaking path the difference between おはよう。 and おはよう！ does not exist:
it is punctuation on a written source, inaudible when spoken and unproducible when the learner answers aloud.
Eight of arrival's 36 slots buy nothing.

**Fix.** Dedupe on `jp.rstrip("。！？!?、")` before filling `say_now`, `drills[].examples` and `production`, and
spend the freed slots on the missing arrival material (はじめまして, 失礼します, お世話になります, よろしく
お願いします are all seeds that never appear).

---

## S2-9. The same set expression gets contradictory pt-BR inside one unit

**Where.** `speak:arrival-01`, `speak:arrival-02`.

```
speak:arrival-01  sent:tatoeba-373351   こんにちは。   "Boa tarde."
speak:arrival-01  sent:tatoeba-3480287  こんにちは！   "Olá!"

speak:arrival-02  sent:tatoeba-426889   さようなら！   "Adeus!"
speak:arrival-02  sent:tatoeba-640569   さようなら。   "Até logo."
```

**Why it is a defect.** The learner meets one Japanese word twice in one sitting with two pt readings and no
note explaining that they are the same word. The さようなら pair is worse than cosmetic: in pt-BR "Adeus"
reads as a final farewell and "Até logo" as see-you-soon, so the two cards teach opposite things about when
to use it (the truth is closer to "Adeus", which makes "Até logo" the wrong one).

The すみません pair in the same stage (`sent:tatoeba-408301` "Desculpe." / `sent:tatoeba-13174949`
"Com licença!") is the one case where the two glosses are both correct and worth teaching, but nothing in the
unit says so, so it reads as the same inconsistency.

**Fix.** One canonical pt per set expression across the path (こんにちは → "Olá.", さようなら → "Adeus."),
and where an expression genuinely has two uses, teach the second as an explicit note on the single card
rather than as a second phrase.

---

## S2-10. 44 of 105 production items accept a misspelled kana answer and reject the correct one

**Where.** Across all six stages. The all-kana entries in `accepted_variants` are generated from the
sentence's phonetic `kana` field, so the particle は is spelled わ and へ is spelled え.

```
speak:eating-01
  answer_key:         ぼくはこれだけしか知らない。
  accepted_variants:  ["ぼくはこれだけしか知らない", "ぼくはこれだけしか知らない。",
                       "ぼくわこれだけしかしらない", "ぼくわこれだけしかしらない。"]
```

The correct kana spelling ぼくはこれだけしかしらない is **not** accepted; the incorrect ぼくわ… is.
`speak:getting_around-03` is the compound case, accepting `えきえわどのようにいけばよいですか`
(both は→わ and へ→え) for 駅へはどのように行けばよいですか。

Full count: 44 of 105 production items. Worst-affected stages: `lodging` 10, `getting_around` 8, `eating` 6.

**Why it is a defect.** A beginner who has correctly learned that the topic particle is written は and
pronounced *wa* types the right answer and is marked wrong. A beginner who copies the accepted form learns to
spell particles phonetically, which is the single most common kana error and the hardest to unlearn.

**Fix.** Build the kana variant from an orthographic-kana source rather than `sentence.kana` (which is
correctly phonetic and should stay that way), or post-process the variant by restoring は/へ/を at every token
position whose `pos` is `particle`. The token data needed is already in the bank.

---

## S3-11. "Desculpe por tê-lo feito esperar tanto tempo" is written pt-BR, and the learner says it four times

**Where.**

```
speak:arrival-05  sent:tatoeba-125944  長い事お待たせしてすみません。      "Desculpe por tê-lo feito esperar tanto tempo."
speak:arrival-05  sent:tatoeba-125913  長くお待たせしてすみませんでした。  "Desculpe por tê-lo feito esperar tanto tempo."
speak:arrival-05  sent:tatoeba-125967  長い間、お待たせしてすみませんでした。 "Desculpe por tê-lo feito esperar tanto tempo."
speak:arrival-06  sent:tatoeba-231454  こんなに長い間待たせてすみません。   "Desculpe por tê-lo feito esperar por tanto tempo."
```

`sent:tatoeba-125967` is also the third production prompt of `speak:arrival-06`.

**Why it is a defect.** The enclitic "tê-lo" plus the periphrastic "feito esperar" is formal written
Portuguese; no Brazilian says it out loud. `design/translation_style.md` §2 requires the pt register to mirror
the Japanese, and the Japanese here (お待たせしてすみません) is ordinary spoken politeness, not written
formality. §1 keeps structural mirrors in `translation_literal`, not `translation`.

**Fix.** Keep one of the four Japanese variants in the stage and translate it
`"Desculpa a demora."` (or `"Desculpa te deixar esperando tanto."` where the length matters). Move the
particle-by-particle version to `translation_literal`.

---

## S3-12. Other over-literal or unspeakable pt in learner-facing prompts

```
speak:eating-06  drill gram:itashimasu  sent:tatoeba-10982402  お知らせいたします。  "Eu o(a) informarei."
```
Synthetic future plus the "o(a)" clitic is written pt. Natural pt-BR: `"Eu aviso."` / `"Vou te avisar."`

```
speak:eating-03  sent:tatoeba-179074  君が飲むついでに、僕の分も入れてくれないかな。
                 "Quando você for tomar, será que aproveita e faz a minha porção também?"
```
"faz a minha porção" is not pt-BR. 分 here is "one for me", and 入れる with a drink is "pour/brew".
Natural: `"já faz uma pra mim também?"`

```
speak:getting_around-02  production prompt_pt:  "De onde (ele/isso) parte?"
                         (sent:tatoeba-201017  どこから出るんですか。)
```
A translator's disambiguation parenthesis used as the text the learner reads and speaks. Either commit to
`"De onde ele sai?"` or state the referent in the prompt.

```
speak:shopping-01  production prompt_pt:  "Eu gostaria de experimentar outros sapatos diferentes desses."
                   (sent:tatoeba-204778  それより他の靴をはいてみたいのですが。)
```
"outros ... diferentes desses" says the same thing twice. Natural: `"Queria experimentar outros sapatos, não
esses."`

```
speak:arrival-03/-05  sent:tatoeba-4971 / sent:tatoeba-9559301  "Muito obrigado(a)!" / "Muito obrigado(a)."
```
The inline "(a)" is unspeakable in a path whose whole point is saying the line out loud. Pick one form and
note the other once.

**Fix.** Re-author the five strings above; all are `translation` fields on Layer-B records, so the fix is
local and the JP is untouched.

---

## S3-13. Em dash in every `arrival` fluency prompt, against the project's explicit ban

**Where.** `speak:arrival-02` through `speak:arrival-06`, 5 occurrences of the same string:

```
"Você acabou de desembarcar. Cumprimente, agradeça e peça licença — em voz alta, sem ler."
```

`design/translation_style.md` §4: "**Never use the — (em dash) character** anywhere in authored text". The
other five stages' prompts are clean, so this is a single authored string to fix.

**Fix.** `"Você acabou de desembarcar. Cumprimente, agradeça e peça licença, em voz alta e sem ler."`

---

## S3-14. `speak:arrival-01` asks the learner to produce nothing, and four sentences are stale or wrong for the setting

**`speak:arrival-01`** has `production: []` and an empty `fluency` (`prompt_pt: null`, no items,
`seconds_target: null`). Unit 1 of a speaking-first path contains no speaking task. `speak:arrival-02`'s
fluency then runs 3 items / 24 s against 6 items / 48 s everywhere else. The material for a production item
already exists in the unit (おはよう, こんにちは, ありがとう are all `chunk_phrases`).

**Four sentences that should be replaced outright:**

```
speak:getting_around-05  sent:tatoeba-234850  ＦＡＸで地図を送っていただけませんか。
                         "Você poderia me enviar o mapa por fax?"
```
Fax, in a travel course. Also reused in `speak:getting_around-06` and `speak:lodging-01` fluency.
The pattern (`gram:te-itadakemasen-ka`) is well served by the unit's own drill examples
少し待っていただけませんか / 電話を貸していただけませんか.

```
speak:health-03 say_now / speak:health-04 production  sent:tatoeba-85328  病院まで１０マイルもある。
                         "Daqui até o hospital são nada menos que dez milhas."
```
Miles, for a Brazilian learner in Japan. Both countries are metric.

```
speak:getting_around-03 say_now / speak:getting_around-04 production
  sent:tatoeba-75827  二本の道はそこでクロスしている。  "As duas estradas se cruzam ali."
```
クロスする for "intersect" is not idiomatic; 交差している is. The path teaches 交差点 two units later
(`speak:getting_around-05`, `sent:tatoeba-222010`), so it contradicts itself.

```
speak:health-04  sent:tatoeba-74743  右よ～し、左よ～し・・・、よし。大丈夫。
                 "Direita, liberado~; esquerda, liberado~...; pronto. Tudo certo."
```
A Japanese railway/driver pointing-and-calling safety chant, used to teach 大丈夫. Unusable as a phrase, and
the "~" tildes are carried straight into the pt.

**Fix.** Give `arrival-01` three production items from its own chunk phrases and a fluency block matching
`arrival-02`'s. Drop the four sentences above and refill from the same grammar points.

---

## Notable non-findings

Recorded so a later pass does not re-litigate them.

- **Provenance is clean.** 0 of 216 `say_now` sentences are `ai_generated`. The `INDEX.md` claim of
  "432 real / 0 generated" holds for this slice. AI-generated sentences appear only as drill examples
  (`gram:masen-ka`, `gram:kana`, `gram:gp-115` and others), which `design/speaking_path.md` permits.
- **`speak:getting_around` units 1 to 4 are the strongest work in the slice.** 駅へはどのように行けばよいですか,
  どこから出るんですか, バスは１５分ごとにでます, どこに座ったらいいですか, やっと着いた, 歩いていく？それとも
  バスで行く？ are exactly right, and `sent:tatoeba-192503` リムジンはどこですか。 glossed
  "Onde fica o ônibus do aeroporto?" is a genuinely good contextual translation, not a literal one.
- **`speak:lodging-03`'s 朝、シャワーを使ってもいいですか。 and `speak:lodging-06`'s 部屋を見せていただけますか。**
  are the two phrases in the stage a guest really says. Keep them and build the stage around them.
- **`speak:health-06`'s 風邪をひきませんように。 "Tomara que você não pegue um resfriado."** is well chosen and
  well translated.
- **The repeated per-stage `fluency.prompt_pt`** (one string reused across all six units of a stage) is not
  itself a defect; the defect is unit 1's items not matching it (S1-1).
- **38 `say_now` sentences have `translation.en == null`.** That is a Layer-A/B completeness matter for the
  translation sweep, not a speaking-content defect, and it is not counted below.
- **`structure_explanation`** was not read, per instruction.

---

## Counts

| Stage | Units checked | `say_now` checked | Production items checked | Findings touching this stage |
|---|---|---|---|---|
| arrival | 6 | 36 | 15 | 7 (S1-1 partial, S1-5, S2-7, S2-8, S2-9, S2-10, S3-11, S3-12, S3-13, S3-14) |
| eating | 6 | 36 | 18 | 6 (S1-1, S1-5, S1-6, S2-7, S2-10, S3-12) |
| getting_around | 6 | 36 | 18 | 6 (S1-1, S1-5, S2-7, S2-8, S2-10, S3-12, S3-14) |
| shopping | 6 | 36 | 18 | 5 (S1-1, S1-2, S1-6, S2-7, S2-10, S3-12) |
| lodging | 6 | 36 | 18 | 6 (S1-1, S1-3, S1-5, S1-6, S2-7, S2-10) |
| health | 6 | 36 | 18 | 6 (S1-1, S1-4, S1-5, S1-6, S2-7, S2-10, S3-14) |
| **Total** | **36** | **216** | **105** | **14 distinct findings** |

| Severity | Count | Findings |
|---|---|---|
| S1 (stage cannot do its job) | 6 | S1-1 stage-opening mismatch, S1-2 no price question, S1-3 lodging room block, S1-4 health-01 ordering, S1-5 written register, S1-6 offensive drill material |
| S2 (systematic, repeated) | 4 | S2-7 seed false positives, S2-8 punctuation duplicates, S2-9 contradictory set-expression gloss, S2-10 kana particle in `accepted_variants` |
| S3 (localised) | 4 | S3-11 "tê-lo feito esperar", S3-12 over-literal pt, S3-13 em dash, S3-14 arrival-01 empty + 4 stale sentences |

**Checked:** 36 units, 216 `say_now` slots, 403 distinct sentence records, 105 production items,
111 drill blocks, 6 fluency prompts.
**Flagged:** 14 findings.
