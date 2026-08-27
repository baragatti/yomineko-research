# QA sweep — lesson prose, part 1/3 (pre-N5 + N5)

**Slice:** every lesson body under `course/pre-n5/` (41 lessons) and `course/n5/` (84 lessons) = **125 lessons**.
**Method:** each `body` was rendered to plain text with `<vocab>/<grammar>/<kanji>/<sentence>` refs resolved
against `corpus/` exactly as `prototype/app/lib/render-body.server.ts` resolves them (chip text = `vocab.kana`,
`grammar.forms[0].form`, kanji character), so the report reflects what a learner actually sees on the page,
not the raw markup. Every finding below was then re-checked against the raw `body` string.
**Out of scope by instruction:** sentence `structure_explanation` fields, and the open items already listed in
`STATE.md` (vocab disambiguation queue — 何方 どちら/どなた, 様, 側 がわ/そば, 中 ちゅう/なか, exam-bank rebuild,
stroke-entity ids).

Findings are ordered by severity. Class D is the largest single cause of the rest.

---

## D — Vocabulary is allocated to lessons by gojūon row, not by topic (systemic; drives ~half of the rest)

This is the finding I would put in front of the teacher first, because most of the odd vocabulary
in classes C, G and I is a downstream symptom of it.

Across N5, the vocabulary a lesson unlocks is dominated by one kana row, and the rows advance in
gojūon order as the topics advance (あ → か → さ → た → な → は → ま → や → ら). Measured over all 84 N5
lessons (dominant-row share of each lesson's vocab unlocks):

| Topic | Lessons | Dominant row | Example |
|---|---|---|---|
| 07 desu-wa | 01–05 | あ (80–100%) | `les:n5-desu-wa-04`: おにいさん おねえさん おかあさん おとうさん あに おじ おおきな いもうと あね おとうと — **10/10 あ** |
| 08 perguntas | 01–06 | か (90–100%) | `les:n5-perguntas-03`: カップ カメラ カレンダー ギター コート きって きっぷ かみ かびん くるま — **10/10 か** |
| 09 numeros-tempo | 01–09 | さ | `les:n5-numeros-tempo-08`: シャツ シャワー スカート セーター ズボン せっけん さいふ — **7/7 さ** |
| 12 passado | 01–05 | た (100%) | `les:n5-passado-01`: デパート トイレ ドア でぐち としょかん ちかてつ ちず と ところ でんき でんわ でんしゃ — **12/12 た** |
| 14 comparacoes | 02–06 | な | `les:n5-comparacoes-03`: ナイフ ニュース ネクタイ ノート ない なくす にく にもつ のみもの のむ — **10/10 な** |
| 15 te-form | 02–08 | は (88–100%) | `les:n5-te-form-06`: はん はんぶん ひだり はる ばん ばんごはん ひがし ばん — **8/8 は** |
| 17 rotina | 01–04 | ま | `les:n5-rotina-02`: もっと まん まんねんひつ みっつ やっつ むっつ また みぎ もんだい もくようび まだ みな みなさん みどり — **15/16 ま** |
| 18 conectando | 03–07 | ら / や | `les:n5-conectando-06`: りょうしん わかる わすれる りょうり りょこう らいねん らいしゅう れんしゅう — **6/8 ら** |

The lesson prose then has to invent a thematic justification for the bucket, and the justifications are
frequently false or absurd. Concrete, quotable consequences:

**D1 — `les:n5-te-form-05` (permissão e proibição) — three unrelated words justified purely by sound.**
> "O verbo 入る ('entrar') é godan… A leitura はいる reaparece no começo de outras palavras, então vale
> separar bem o que vem depois. Não confunda o verbo com estes dois substantivos: 肺: pulmão / 杯: taça de saquê"

and later

> "Um cenário clássico de proibição é o 灰皿 ('cinzeiro')… A leitura はいざら começa igual a はいる, e só
> diverge a partir da terceira mora… Compare também com: 伯: conde (título de nobreza)"

肺 (pulmão), 杯 (さかずき — which does not even start with はい) and 伯 (conde) have nothing to do with
permission, prohibition, or 入る. **Fix:** drop 肺 / 杯 / 伯 from this lesson and re-place them (or cut them
from N5 entirely); the "don't confuse" note has no pedagogical content.

**D2 — `les:n5-particulas-lugar-07` (あげる/くれる/もらう) — a section that says outright it has no place here.**
> "### Duas palavras de bônus para o seu caderno
> Antes de praticar, guarde dois itens que vão aparecer em textos mais à frente. O caractere 総(そう) quer
> dizer 'total / geral'… E a conjunção formal 而して(しかして) significa 'e então / assim'; é bem literária…"

Both are そ-row items dumped into a lesson about giving and receiving. See also **B1**: 而して is a factual error.

**D3 — `les:n5-te-form-08` — an entire section exists to place one vocabulary item.**
> "### O hiragana como sistema
> Repare que todas essas contrações vivem em ひらがな. O hiragana é o sistema que carrega justamente as
> terminações gramaticais como なくちゃ e なきゃ. Sem dominar o hiragana, essas formas faladas passam despercebidas."

A section explaining what hiragana is, in N5 topic 15, after fifteen pre-N5 hiragana lessons. Its only
function is to render the は-row chip ひらがな. **Fix:** delete the section; move ひらがな's SRS unlock to
`top:pre-n5-hiragana`.

**D4 — `les:n5-perguntas-05` — three obsolete metric-unit kanji, labelled `culture`.**
> "Três palavras desta lista são curiosidades antigas… 瓩: quilograma / 粁: quilômetro / 瓦: grama…
> Hoje quase ninguém os escreve assim"

**D5 — other explicit "it doesn't fit, but here it is" placements:**
- `les:n5-desu-wa-02`, in a list of *lugares*: "**este não é palavra de lugar**; é o mesmo あれ da lição…"
- `les:n5-perguntas-01`, in "Mais lugares para praticar": "ここ: **a escrita em kanji de ここ**"
- `les:n5-comparacoes-05`: "Estes dois últimos descrevem o que um animal ou uma planta faz, **não um desejo
  humano. Guarde-os para reconhecer, mas não os combine com たい**" (鳴く, 生る — な-row)
- `les:n5-verbos-03`: "Você vai ouvir também os verbos 罹る (contrair uma doença), **翔る (planar, voar)** e
  曇る (ficar nublado)" — 翔る is literary; a beginner will not "ouvir" it
- `les:n5-desu-wa-02`: «お|尾|cauda, rabo» offered as an everyday object to point at ("apontar o お dele").
  お as a standalone noun for "tail" is literary; the everyday word is しっぽ, and お collides head-on with the
  honorific prefix お taught three lessons later in `les:n5-desu-wa-05`
- `les:n5-particulas-lugar-01`: «たて|盾|escudo» in a list of household things that "existem em lugares"

**D6 — the seven weekdays are scattered across five topics by kana row, and Thursday is never written.**
`les:n5-particulas-lugar-06` has a section headed **"Os dias da semana"** that teaches only four:
> "月曜日 … 火曜日 … 水曜日 … 金曜日 … Repare que são os mesmos kanji dos elementos: 月 (lua/mês), 火 (fogo),
> 水 (água), 金 (ouro/metal)."

土曜日 lands in `les:n5-passado-02` (た-row), 日曜日 in `les:n5-comparacoes-04` (な-row), and 木曜日 in
`les:n5-rotina-02` (ま-row) — a lesson titled *"もう e まだ: já / ainda"*, whose body **never writes 木曜日 or
もくようび in prose at all**; it appears only as a chip in the closing vocabulary list. A learner who finishes
"Os dias da semana" cannot say Thursday, Saturday or Sunday, and will not meet Thursday for another
eleven lessons. **Fix:** teach all seven in `les:n5-particulas-lugar-06`.

---

## A — Markup that corrupts the rendered Portuguese (verified in the raw `body`)

### A1 — Emphasis/bold spans with a stray space split a Portuguese word in two (22 instances, 13 lessons)

Pattern: `de "ca </text><emphasis>r</emphasis><text> o"` renders as `de "ca r o"`.

| Lesson | Renders as | Should read |
|---|---|---|
| `les:pre-n5-sons-03` | `igual ao r de "ca r o" ou "a r ara"` | caro / arara |
| `les:pre-n5-hiragana-03` | `Lembre-se de uma s aia esvoaçando` · `como um pi ru lito` · `Imagine um se máforo` | saia / pirulito / semáforo |
| `les:pre-n5-hiragana-04` | `um dedo do pé (to e, em inglês)` | toe |
| `les:pre-n5-hiragana-09` | `no ra de "ca ra col"` · `"a ri sco"` · `"ba ru lho"` · `"ca re ca"` · `"ca ro"` | caracol / arisco / barulho / careca / caro |
| `les:pre-n5-katakana-01` | `Imagine um A nzol` | anzol |
| `les:pre-n5-katakana-02` | `imagine uma ca pa de super-herói` · `pense numa ki tchen` | capa / kitchen |
| `les:pre-n5-katakana-03` | `lembra um se máforo torto` | semáforo |
| `les:pre-n5-katakana-07` | `de "ma çã"` · `"mi nha"` · `"mu ro"` · `"me sa"` · `"mo la"` | maçã / minha / muro / mesa / mola |
| `les:pre-n5-katakana-08` | `Imagine um i ate` · `Pense num u tensílio` | iate / utensílio |
| `les:pre-n5-katakana-09` | `uma ra mpa pendurada` · `duas ri scas paralelas` · `uma ro da quadrada` | rampa / riscas / roda |
| `les:pre-n5-katakana-10` | `o começo de "w affle"` | waffle |
| `les:pre-n5-katakana-11` | `seta apontando para n ordeste` | nordeste |
| `les:pre-n5-katakana-14` | `o "nh" abrandado de "ni nha"` | **"ninha" is not a Portuguese word** — `les:pre-n5-hiragana-14` uses "ninho" for the same sound |
| `les:pre-n5-pronuncia-03` | `lemos "advogado" como "a d-i -vogado"` | ad-i-vogado |
| `les:n5-verbos-01` | `見る(mi ru, "ver") e 起きる(oki ru, …)` | mi**ru** / oki**ru** |

**Fix:** move the space out of the emphasised span (`uma <b>s</b>aia`, not `uma<b> s</b>aia`), and change
`les:pre-n5-katakana-14`'s "ni nha" to "ninho".

### A2 — Grammar chips render identical or wrong text, breaking the sentence

- **`les:n5-desu-wa-03`** — two different grammar refs whose `forms[0].form` is both `じゃない`:
  > "A forma casual é **じゃない**; a forma completa e mais formal é **じゃない**."
  The learner is told two forms are different and shown the same string. **Fix:** the second chip must
  render ではない.
- **`les:n5-verbos-03`** — the opening sentence cites `gram:gp` (です) where ます was meant:
  > "Agora que você já sabe montar verbos no **です** polido, vamos sair de casa."
  Factually wrong and contradicted by `les:n5-verbos-01`'s own exercise ("です é só para substantivos e
  adjetivos, não para verbos"). **Fix:** point at `gram:gp-8` (ます).
- **`les:n5-desu-wa-05`** — "Esses prefixos honoríficos são **お**." (the chip drops ご, so the sentence
  announces one prefix and the next heading is "お ou ご?").
- **`les:n5-adjetivos-05`** — "«**になる**» cobre o caso dos substantivos e adjetivos-な, e «**になる**» reúne os
  dois moldes lado a lado."
- **`les:n5-te-form-02`** — "A escolha entre **て** depende do que vem antes" — "a escolha entre X" with one
  item; ungrammatical in Portuguese.
- **`les:n5-numeros-tempo-04`** — two bullets that both render `かい` ("かい conta vezes" / "かい conta andares")
  with nothing on the page distinguishing 回 from 階.

### A3 — Malformed `grammar.forms[0].form` strings reach the page as chips

| Lesson | Chip renders | Sentence becomes |
|---|---|---|
| `les:n5-numeros-tempo-02` | `くらい ①` | "coloque **くらい ①** logo depois do número" — an internal disambiguation marker in learner text |
| `les:n5-adjetivos-03` | `い- くない` | "O molde de hoje é o negativo **い- くない**" |
| `les:n5-adjetivos-04` | `い- くなかった` | idem |
| `les:n5-comparacoes-01` | `よりほうが`, `はより`, `のほうがより`, `よりのほうが` | "a partícula **よりほうが**, que marca o termo de comparação (o nosso 'do que')" — よりほうが is not a particle and does not mark "do que"; より alone does |

### A4 — `<jp>` surface and `reading` disagree, splitting the example sentence

`les:n5-conectando-02`, twice:
```
<jp reading="このカメラはたかいけど、いい">このカメラは高いけど、</jp><vocab ref="vocab:2820690"/>
```
The visible Japanese stops at `このカメラは高いけど、` while the furigana/`data-say` reading contains いい, and
いい appears afterwards as a detached chip. **Fix:** put the whole sentence inside the `<jp>` element.

### A5 — missing space before an opening quote

`les:pre-n5-hiragana-05`: `(em "fim", "bom" o n"some" no nariz)` → should be `o n "some" no nariz`.
Same class in `les:pre-n5-hiragana-03`: `e nunca"si"`.

---

## B — Factual / linguistic errors

**B1 — `les:n5-particulas-lugar-07` teaches そして as an archaic literary word.**
> "E a conjunção formal 而して(しかして) significa 'e então / assim'; é **bem literária**, então você vai lê-la
> mais do que falá-la"

The record cited (`vocab:1006730`) is **そして** — kana `そして`, headword `而して`, gloss "e / e então". そして is
one of the most common conjunctions in the language and the course teaches it properly later, in
`les:n5-conectando-03` ("Encadear ideias: でも, しかし, そして, それから"). **Fix:** either drop the bullet or write
"そして (escrita rara em kanji como 而して)".

**B2 — `les:n5-adjetivos-05` claims 来 means "tornar-se".**
> desc: "O kanji 来 (que também significa 'tornar-se') ancora o tema da mudança."
> body: "«来» significa 'vir' e também 'vindouro / **tornar-se**', o que combina direto com o tema de hoje"

来 does not mean "become"; the lesson's own chip glosses it "vir, chegar, próximo (no tempo)". The claim
exists only to justify placing the kanji in a なる lesson. **Fix:** remove the "tornar-se" gloss.

**B3 — `les:n5-te-form-01`'s godan て-form rule is incomplete.**
> "う・つ・る viram って…; ぬ・ぶ・む viram んで; く vira いて; す vira して."

**ぐ → いで is missing** (泳ぐ → 泳いで), and 泳ぐ was taught in `les:n5-verbos-03`. A learner following this rule
cannot form the て of a verb already in their vocabulary. **Fix:** add "ぐ vira いで".

**B4 — `les:pre-n5-katakana-06` anchors the Japanese /h/ to Portuguese words where h is silent.**
> "ハ(ha): como o ha de '**harpa**' … ヒ(hi): como o hi de '**hiena**' … ヘ(he): como o he de '**hélice**' …
> ホ(ho): como o ho de '**hotel**'"

`les:pre-n5-hiragana-06` gets this right and warns against exactly this: "basta soprar um pouquinho, **em vez
de deixar o 'h' mudo como em 'hora'**". The katakana lesson then models the sound on four words whose h is
mute in pt-BR. **Fix:** reuse hiragana-06's "hello"-style anchor.

**B5 — `les:pre-n5-katakana-05` gives ノ the open vowel the course elsewhere forbids.**
> "ノ(no): como o no de '**nó**'."

`les:pre-n5-hiragana-05` says the opposite, explicitly: "の(no): como o no de 'novo' (com ô fechado, **nunca o
'ó' de 'nó'**)". **Fix:** "como o no de 'novo'".

**B6 — `les:pre-n5-katakana-13` calls the Japanese /o/ open.**
> "ピアノ termina num '**o' aberto** e claro (nunca 'pianu')"

Every other lesson teaches the closed ô of "avô" and warns against the open ó of "avó".
**Fix:** "termina num 'o' fechado e limpo".

**B7 — `les:n5-adjetivos-03` says there are no exceptions, one lesson after teaching the exception.**
> "Uma regra única (い → くない) resolve **TODOS** os adjetivos-い, **sem exceções** de gênero ou número."

`les:n5-adjetivos-02` teaches いい → よくない ("Nunca diga いかった nem いくない"). **Fix:** "…sem exceções de
gênero ou número (o único irregular é いい → よくない, que você já viu)".

**B8 — `les:n5-perguntas-01` tells the learner not to say the correct pronunciation.**
> "Cuidado com あそこ: tem três kana (あ・そ・こ), não dois… **Não fale "asoko" engolindo o あ** nem o confunda
> com そこ"

"asoko" *is* the correct reading; the intended warning is against saying "soko". As written it instructs the
learner away from the right answer. **Fix:** "Não fale 'soko', engolindo o あ."

**B9 — the mora rule is stated without the yōon exception, and the lesson's own example breaks it.**
`les:pre-n5-sons-02` checklist: "Conto **cada kana**, o n final e a consoante dobrada como 1 mora, e a vogal
longa como 2 moras." Applied to とうきょう that rule yields 5, but the same lesson teaches "To-o-kyo-o (Tóquio)
tem 4 moras". `les:pre-n5-hiragana-15`'s glossary entry gets it right ("cada kana vale uma mora, **menos os
pequenos ゃ・ゅ・ょ**"), but `les:pre-n5-katakana-15`'s entry — in the lesson that teaches ャ・ュ・ョ — reverts to
the wrong short form: "a unidade de tempo do japonês; cada kana vale uma mora".
**Fix:** use the hiragana-15 wording in both places and in the sons-02 checklist.

**B10 — `les:n5-verbos-03`: the 中 paragraph gives a gloss where the example word should be.**
> "Kun なか('dentro'); on ちゅう, **que aparece em palavras como "durante / em andamento"**."

Compare the parallel sentence for 行 in the same paragraph: "on こう, que reaparece em palavras como **旅行**
(viagem)." The 中 sentence has the meaning but no word. **Fix:** "…como 使用中 ('em uso') ou 工事中 ('em obras')".

**B11 — `les:n5-numeros-tempo-09` writes the demonstratives in a kanji form the course tells learners to ignore.**
All eight Japanese examples in the body use 此れ / 此の / 此方:
> "此れは自転車です: 'isto é uma bicicleta'" · "此の自動車: 'este carro'" · "此の駅" · "駅は此方です"
> · "此れは自動車です" · "此方です"

`les:n5-perguntas-01` says of the same family: "ここ também se escreve com kanji, 此処, mas no dia a dia
aparece **quase sempre em kana**, então não se preocupe em memorizar esse kanji por enquanto", and
`les:n5-desu-wa-02` says "**Escreva sempre em kana**: o kanji desta entrada é raro". The lesson's own
exercises then use これ/この in kana (only the `accept` list carries 此方). A learner is asked to read a form
the course has told them is not worth learning. **Fix:** render these eight examples as これ / この / こちら.

**B12 — `les:n5-te-form-03` conflates 早い and 速い.**
> "«はやい|早い|cedo»: **cedo, rápido**."

`les:n5-adjetivos-05` teaches 速い = "rápido" separately (速い → 速く, 速く走る). Glossing 早い as "cedo, rápido"
erases the distinction the course makes elsewhere. **Fix:** "cedo (no tempo); para 'rápido (de velocidade)'
é 速い".

---

## C — Chip gloss contradicts the lesson's own label (wrong vocabulary record)

**C1 — `les:n5-perguntas-01`** — "«かた|方|**pessoa (formal), senhor/senhora**»: **direção / sentido**".
The lesson wants 方 read ほう ("direction"); it cites the かた record ("person, polite"). The tooltip and the
label say opposite things.

**C2 — `les:n5-numeros-tempo-04`** — "«ちゅう|中|**durante/no meio de/em processo de, ao longo de/por todo**»(**médio**)…
Num cardápio você vê 大 para a porção grande e 中 para a média."
The lesson teaches 中 = "medium size"; the chip glosses it "during / in progress". (Related to but distinct
from the known 中 ちゅう/なか homograph item in `STATE.md` — the defect here is the prose/gloss contradiction.)

**C3 — `les:n5-conectando-04`** — "«せ|背|**altura (de uma pessoa), estatura**»: **costas**" (`vocab:2147990`).

**C4 — `les:n5-conectando-04`** — two homograph mis-picks in the same three-item list:
- "«ほんとう|**本島**|ilha principal»: ilha principal" (`vocab:1523040`) — ほんとう is 本当 "verdade" everywhere
  else in the course (`les:n5-convites-06` teaches it that way), with no note distinguishing them.
- "«せっけん|**接見**|entrevista (oficial), audiência, recepção»: audiência ou entrevista oficial"
  (`vocab:1385390`, **level `n1`**) — せっけん is 石鹸 "sabonete" in `les:n5-numeros-tempo-08`.
  An N1 legal-register word taught in an N5 lesson about でしょう, under the heading "E mais três palavras
  úteis para variar os exemplos".

**C5 — `les:n5-particulas-lugar-02`** — "«その|園|jardim, parque»: jardim, parque" listed among place words.
その is the demonstrative "that (near you)" the course teaches in `les:n5-perguntas-02`; 園 read その alone is
archaic. Teaching その = "jardim" at N5 actively damages the demonstrative the learner just acquired.

**C6 — `les:n5-conectando-01`** — "«ほう|報|relatório, notícia, informação»: 'informação, notícia'".
報 is a bound morpheme, and ほう was taught two topics earlier as 方 "lado/opção" (`les:n5-comparacoes-01`,
ほうが). Same reading, incompatible meaning, no warning.

---

## E — Whole lessons and kanji taught twice

**E1 — `les:n5-adjetivos-08` re-teaches `les:n5-adjetivos-07` with no new material.**
`-07` objectives already include "Dizer que se é bom (じょうず) ou ruim (へた) em uma atividade com 〜のが上手/下手です",
and its body gives "Para o oposto, é só pôr 下手 no lugar: 料理を作るのが下手です". `-08` then spends a full lesson
on 下手 with the same example. Its only unlocks are `gram:gp-53` and `gram:no-ga-heta` — duplicates of the
`-07` pair. **Fix:** merge into `-07`, or give `-08` real new content.

**E2 — `les:n5-conectando-07` re-teaches `les:n5-rotina-04` (〜たり〜たりする).**
Both derive たり from the casual past, both stress "cada item leva たり", both close with する/します, both use
本を読んだり. **Fix:** cut the たり half of conectando-07 and keep only 方（かた）.

**E3 — `les:n5-conectando-05` re-teaches `les:n5-convites-04` (〜たほうがいい).**
Both explain ほう = "lado/opção", both give 行ったほうがいい, both carry the same pitfall ("é o verbo no passado
(た), nunca 行くほうがいい"), and both cite `sent:tatoeba-216787` さっさと行ったほうがいい. **Fix:** convites-04 should
keep the affirmative; conectando-05 should open at ないほうがいい.

**E4 — 雨 is "o kanji da lição" twice in topic 18, with two incompatible mnemonics.**
- `les:n5-conectando-01`: "imagine uma **janela (a moldura ao redor)** com quatro gotinhas de chuva caindo lá dentro"
- `les:n5-conectando-04`: "imagine uma janela: o **traço de cima é o céu, a linha vertical no meio é a moldura**"

`les:n5-conectando-04` does not unlock `kanji:雨` (it is unlocked by `-01`), so the second block is a
re-presentation. **Fix:** delete the `-04` kanji section.

**E5 — grammar points introduced ahead of their own lesson, then taught again as new:**
- 一番 as superlative: taught in `les:n5-adjetivos-04` ("一番高い = 'o mais caro'"), then introduced as new in
  `les:n5-comparacoes-02` ("O superlativo: 一番").
- ほしい: the whole subject of `les:n5-comparacoes-04`, re-introduced in `les:n5-convites-06`
  ("«ほしい|欲しい» = querer (ter algo)… 水が欲しい").
- へた: the whole subject of `les:n5-adjetivos-08`, re-listed as new vocabulary in `les:n5-convites-04`.
- くらい: the whole subject of `les:n5-numeros-tempo-02`, listed as new vocabulary in `les:n5-perguntas-05`.

---

## F — Un-annotated "Mais exemplos" blocks that teach the wrong thing

The "Mais exemplos" sections carry no commentary — just the Japanese, the pt-BR and the romaji. Where the
sentence does not contain the lesson's target, the learner has no way to know.

**F1 — `les:n5-particulas-lugar-03` (a partícula で de lugar da ação) — neither example contains that で.**
> 【tatoeba-1057336】でもなんで？ // Mas por quê?
> 【tatoeba-125387】諦めないで。 // Não desiste! *(corpus level: n1)*

The first でも is the conjunction "mas"; the second is the negative-request ないで, taught only in
`les:n5-te-form-06`. The lesson body itself warns "Não confunda os dois で", then the block right after the
exercises supplies two of the wrong で with no warning at all.

**F2 — `les:n5-conectando-03` (でも, しかし, そして, それから)** — 【tatoeba-85538】美人でもある。("Ela também é
bonita.") Here でも is で + も, not the conjunction でも the lesson teaches. *(corpus level: n3)*

**F3 — `les:n5-desu-wa-04` (の e も)** — 【tatoeba-1057336】でもなんで？ — でも here is neither の nor も, and なんで
is not taught until `les:n5-perguntas-04`.

**F4 — `les:n5-comparacoes-02` (o superlativo 一番)** — 【tatoeba-203016】チェスを一番どうですか。("Que tal uma
partida de xadrez?") *(corpus level: n3)*. The 一番 here means "one round", not "the most". As a "more
examples" item under a superlative lesson it teaches a different word; the Japanese itself is also dubious.

**F5 — `les:n5-verbos-01`** — 【tatoeba-150175】痔があります。("Tenho hemorroidas.") The same sentence is used
again in `les:n5-verbos-05`, this time *with* commentary: "mostrando que 'existir' também serve para algo que
a pessoa tem no corpo, como uma condição de saúde." Also in that block: 【tatoeba-11795596】8人孫がいます。
*(corpus level: n2)*, whose word order (8人孫が…) is marked; the natural form is 孫が8人います。

**F6 — `les:n5-te-form-01` (pedidos **educados**)** — 【tatoeba-74924】よし、かかってこい！("Beleza, pode vir!").
こい is the blunt imperative of 来る, well beyond N5 and the opposite register of the lesson. Reused in
`les:n5-te-form-02`. Also in the -01 block: 【tatoeba-85522】鼻がつまっています。*(n2)*, which is `-03`'s target.

**F7 — `les:n5-perguntas-02`** — 【tatoeba-74036】この新聞はロハだ。ロハ is obscure period slang for "free of
charge"; nothing in the lesson prepares it. Also 【tatoeba-80099】木はその実で分かる。 — a proverb in which その
is anaphoric "its", not the by-distance demonstrative being taught.

**F8 — `les:n5-perguntas-03` (どれ vs どの)** — 【tatoeba-5675047】どれくらい？ — どれくらい is a fixed expression
("how much"); it does not illustrate どれ "which one".

**F9 — `les:n5-numeros-tempo-02`** — 【tatoeba-190227】一年前くらい前に来ました。 — the sentence repeats 前
(一年**前**くらい**前**に). `les:n5-numeros-tempo-05` uses the same sentence and *does* flag it; numeros-tempo-02
serves it with no warning.

**F10 — `les:n5-particulas-lugar-08` (と, や, だけ, まで)** — 【tatoeba-187788】何とかしろ！ and
【tatoeba-139686】何とか入れた。 — 何とか is a fixed idiom whose と is not the listing と, and しろ is a plain
imperative.

**F11 — `les:n5-adjetivos-03`, in the body (not the Mais-exemplos block)** —
> 【tatoeba-135763】ちくしょう！わるくないなあ！ // Droga! Não é nada mau!

ちくしょう is coarse ("damn it / son of a bitch"). It is the headline example of the negative-adjective lesson,
with no register warning; the note that follows only comments on the なあ.

**Fix (all of F):** either add a one-line gloss to each "Mais exemplos" item saying what to look at, or
replace the sentences with ones whose target is the lesson's target.

---

## G — Meta-text and authoring notes leaking into learner prose

**G1 — `les:n5-numeros-tempo-05`:**
> "Essa frase, **como aparece no corpus**, repete o まえ (一年前くらい前に), o que soa redundante."

"o corpus" is an internal artefact name. **Fix:** "Essa frase, como foi registrada, repete o まえ…".

**G2 — `les:n5-adjetivos-07`** — the author explains duplicate grammar records to the learner, twice:
> "É o mesmo padrão que aparece registrado como «のがすきです» **nas listas de gramática: as duas chaves
> descrevem exatamente a mesma construção**."
> "A construção «のが上手», **registrada também como** «のがじょうずです», segue a mesma fórmula"

**Fix:** delete both clauses; deduplicate the grammar records instead.

**G3 — `les:n5-comparacoes-01`:**
> "### Quatro moldes, três ordens
> Quatro moldes cobrem 'A é mais X que B', mas em apenas três ordens: **o segundo e o quarto repetem a mesma
> ordem, com usos diferentes**."

This is the author narrating four near-duplicate corpus records. The fourth bullet then promises a
preference reading ("agora para **preferir**… 'prefiro B a A'") and illustrates it with a plain price
comparison (電車よりバスのほうが安い = "O ônibus é mais barato que o trem"), which shows no preference at all.

**G4 — `les:pre-n5-hiragana-07`:** "usando o diagrama numerado **estático**" — every other lesson says just
"o diagrama numerado"; "estático" is an implementation detail.

**G5 — `les:pre-n5-katakana-01`:**
> "イ(i): o som i de 'ilha'. São dois traços inclinados, como duas perninhas (**o i tem dois pontinhos? aqui
> são dois riscos**)."

The Portuguese "i" has one dot; the parenthetical is garbled and teaches nothing. **Fix:** delete it.

**G6 — `les:n5-particulas-lugar-08`, "### Ponte: o que existe na lista"** — a section with no new content and
no example:
> "…**Agora imagine** encher esse 'o que existe' com uma lista de や, como na frase da mesa lá em cima, e você
> junta as duas ideias da lição."

It restates があります (topic 11 lesson 01) and asks the learner to imagine the example instead of showing one.

**G7 — post-exercise vocabulary dumps with no context**, headed "Mais um item para o seu repertório":
`les:n5-particulas-lugar-08` (幾つ, 幾ら — in rare kanji, and both already used in `les:n5-desu-wa-01`),
`les:n5-passado-02` (点ける).

---

## H — Consistency and terminology

**H1 — three romanization systems, sometimes for the same word.**
The dominant system is doubled vowels (`sukii`, `soosu`, `gakkou`, `gyuunyuu`, `koohii`, `juusu`, `seetaa`,
`shawaa`, `yooyoo`), but macrons appear in `les:pre-n5-katakana-01/04/06/09` and `les:pre-n5-katakana-14`
(`kōhī`, `kōto`, `sūtsu`, `takushī`, `nōto`, `hītā`, `karē`, `rāmen`, `jūsu`, `shawā`), and a circumflex in
`les:n5-numeros-tempo-06` (`shôyu`). The clearest collisions:
- コーヒー = **kōhī** in `les:pre-n5-katakana-01` and `-06`, but **koohii** in `les:pre-n5-katakana-15`.
- ジュース = **jūsu** in `les:pre-n5-katakana-14`, but **juusu** in `les:pre-n5-katakana-15` — adjacent lessons.
- シャワー = **shawā** in `-14`, **shawaa** in `les:n5-numeros-tempo-08`.

**Fix:** pick one (the doubled-vowel system, which matches the kana and the mora teaching) and normalise.

**H2 — three `<term define>` glossary entries are wrong.**
- `les:pre-n5-katakana-07`, term **hiragana** → *"contraparte em hiragana do mesmo som"* — circular and wrong.
  The correct definition is used in `les:pre-n5-hiragana-01/06`: "o primeiro dos dois silabários do japonês;
  cada símbolo representa uma sílaba".
- `les:pre-n5-katakana-13`, term **vozeamento** → *"As duas marquinhas (゛) que vozeiam um kana…"* — that is
  the definition of *dakuten*, not of *vozeamento* (the process). **Fix:** "tornar sonora uma consoante surda
  (a garganta passa a vibrar); no kana, marcado pelo ゛".
- `les:pre-n5-katakana-15`, term **mora** → see **B9**.

**H3 — `<note type="culture">` used for non-cultural content** (7 of 42 culture notes). Examples:
`les:pre-n5-sons-01` (a preview of the kana あ), `les:pre-n5-hiragana-10` (why を is read "o"),
`les:pre-n5-katakana-07` (what katakana is for), `les:n5-desu-wa-04` ("**Bônus de vocabulário**: 大きな…"),
`les:n5-perguntas-04` (that かぜ has two kanji), `les:n5-verbos-04` (which verb goes with which garment),
`les:n5-comparacoes-06` (the irregular reading なのか). If the UI badges these as "cultura", the badge is
wrong. **Fix:** retag as `tip` / `warning`.

**H4 — `les:pre-n5-katakana-11` and `les:pre-n5-katakana-14` describe シ/ツ in opposite terms.**
- `-11` (correct): "no シ os pinguinhos ficam **empilhados na vertical**… No ツ os pinguinhos ficam **lado a
  lado na horizontal**"
- `-14`: "O シ tem os tracinhos **mais na horizontal** e… o ツ tem os tracinhos **mais na vertical**"

`-14` means stroke *direction* and `-11` means dot *arrangement*, but nothing on the page says so, and read
literally they contradict. **Fix:** use `-11`'s wording ("empilhados na vertical" / "lado a lado") everywhere.

**H5 — `les:pre-n5-katakana-09` objective and checklist put the Japanese r "between r and l".**
> objective: "Lembrar que a Família do RA usa o mesmo 'r' suave do japonês (**entre 'r' e 'l'**)"
> checklist: "Faço o 'r' japonês suave, **entre 'r' e 'l'**."

`les:pre-n5-hiragana-09` says the opposite: "**E não troque por L também**: ら nunca é 'la'". The lesson's own
body also says only "toque rápido da ponta da língua". **Fix:** drop "entre 'r' e 'l'".

**H6 — "o" modelled on a word whose final o is [u].**
`les:pre-n5-sons-01` ("o como em 'bolo'") and `les:pre-n5-hiragana-01` ("お(o): como o o de 'bolo' (**nunca vira
'u'**)") use *bolo*, whose final o is pronounced [u] in pt-BR — the exact reduction the sentence forbids.
`les:pre-n5-orientacao-02` gets it right with an unambiguous anchor ("como o ô de 'avô'… não o 'ó' aberto de
'avó'"). **Fix:** use "avô" consistently.

**H7 — `les:pre-n5-hiragana-02`: "こ(ko): como co de 'copo'; vogal cheia, nunca vira '**cu**'."**
Standing alone in quotes, "cu" is vulgar in pt-BR; the parallel note four lines later already uses the neutral
romaji form ("こ é sempre ko, não 'ku'"). **Fix:** use "ku" in both places.

**H8 — slash-notation phonemes in beginner text.** `les:pre-n5-hiragana-13` mixes `"d"` with `/b/` and `/p/`
in one sentence; `les:pre-n5-hiragana-11`'s exercises use `/n/ silábico = ん`. The notation is never
introduced. **Fix:** plain quotes throughout.

**H9 — `les:n5-te-form-03` uses "okaasan" for the lesson's own はは.**
> "…você já pode montar uma cena inteira: '**a okaasan** passou manteiga no pão e está pronto'"

The lesson teaches はは (母, one's own mother), and `les:n5-desu-wa-04` teaches the はは / お母さん split.
Romaji "okaasan" in the middle of Portuguese prose contradicts both. **Fix:** "a はは (mãe)".

---

## I — Coverage / gating

**I1 — `les:pre-n5-hiragana-06`'s description promises content the body never delivers.**
> desc: "…e **は ganha leitura especial ao virar partícula**."

The body covers the /h/ sound, the five kana, ふ, and the は/ほ/へ shapes; the particle reading of は appears
nowhere in it (nor in the objectives, nor in the exercises). **Fix:** either add the note or cut the promise
from the description.

**I2 — `les:pre-n5-katakana-10` uses two kana it has not taught, under a sentence that says it doesn't.**
> "Usando o katakana **que você já aprendeu**, leia estas palavrinhas em voz alta: ワイン… ハワイ…
> **ワイシャツ**(waishatsu, camisa social) e キウイ"

ン is introduced in the next lesson (the tip above the list acknowledges this), but **シャ is not introduced
until `les:pre-n5-katakana-14`** and is not acknowledged anywhere. **Fix:** replace ワイシャツ with a word inside
the taught set.

**I3 — weekdays:** see **D6**.

**I4 — `les:n5-particulas-lugar-04`: the "destination" section has no destination.**
> "### に no destino: para onde se vai
> …【gen-9e1f6fa2353f】すぐに行きます // Já vou agora mesmo.
> Em すぐに行きます, repare em すぐに ('já, na hora'): aqui o に ajuda a marcar **o 'momento' da ida**"

The only example under a heading about destination contains no destination, and the prose says so. **Fix:**
use 学校に行きます (which the lesson already cites two paragraphs later) as the example.

---

## Minor (recorded, not urgent)

- `les:n5-numeros-tempo-01`: "«漢十|dez» significa dez, lê-se じゅう e **aparece na palavra じゅう**" — circular.
- `les:n5-numeros-tempo-01`: the `culture` note calls きゅう an *alternative* reading for 9 ("leituras
  alternativas: よん para 4, **きゅう para 9**"), but the lesson's own list already gives 9 = きゅう as the main one.
- `les:n5-numeros-tempo-01` objective: "Lembrar os números com **som duplo** (4・し, 7・しち, 9・きゅう)" — the body
  section is "Os que costumam confundir" and explains shared onsets and a long vowel, not "som duplo".
- `les:pre-n5-saudacoes-03`: "どうして(dōshite) = **por quê; como**" then "Serve para perguntar o motivo de
  algo" — the "como" gloss is not supported by the paragraph it opens.
- `les:pre-n5-saudacoes-03`: the bullet defines ついて alone, while the objective, the tip and the production
  exercise all use について.
- `les:n5-desu-wa-05`: "Para a SUA própria avó ou esposa, **em situação humilde**" — a literal rendering of
  "humble register"; in pt-BR "em situação humilde" reads as "in poor circumstances".
  **Fix:** "ao falar com humildade da sua própria família".
- `les:n5-desu-wa-02`: the それ section is headed "**No meio do caminho: それ**" (それ is near the *listener*,
  not midway) and is illustrated by 【tatoeba-4802】それがどこから来たのか分からなかった, whose pt-BR translation
  renders それ as "**aquilo**" — the word the same lesson assigns to あれ.
- `les:n5-revisao-01/02/03` titles use a semicolon where a colon is meant ("Revisão N5; Fundamentos: …").
- Section order: 62 of 125 lessons place "Mais exemplos" and/or "Leitura" **after** "Hora de praticar", so new
  input follows the practice block. That is a template decision rather than a per-lesson defect, but combined
  with class F it means the least-supervised material sits last.

---

## Count table

| Class | What | Lessons touched | Findings |
|---|---|---|---|
| **D** | Vocabulary allocated by gojūon row, not topic (systemic) | 84 N5 lessons measured; 8 quoted | 6 |
| **A** | Markup corrupting rendered Portuguese | 20 | 5 (A1 covers 22 instances / 15 lessons) |
| **B** | Factual / linguistic errors | 12 | 12 |
| **C** | Chip gloss contradicts lesson label (wrong vocab record) | 6 | 6 |
| **E** | Duplicate lessons / re-taught grammar & kanji | 12 | 5 |
| **F** | Unsuitable example sentences in un-annotated blocks | 11 | 11 |
| **G** | Meta-text / authoring notes in learner prose | 8 | 7 |
| **H** | Consistency and terminology | 17 | 9 |
| **I** | Coverage / gating gaps | 4 | 4 |
| **Minor** | Recorded, not urgent | 9 | 9 |
| | | | |
| **Checked** | lesson bodies read in full (41 pre-N5 + 84 N5) | | **125** |
| **Flagged** | distinct findings | | **74** |
| **Lessons carrying at least one finding** | | | **92 of 125** |
| **Lessons with zero findings** | | | **33 of 125** |

The 33 lessons where I found nothing to report:
`les:pre-n5-orientacao-01`, `les:pre-n5-hiragana-08`, `les:pre-n5-hiragana-12`, `les:pre-n5-katakana-04`,
`les:pre-n5-katakana-12`, `les:pre-n5-pronuncia-01`, `les:pre-n5-pronuncia-02`, `les:pre-n5-saudacoes-01`,
`les:pre-n5-saudacoes-02`, `les:n5-perguntas-06`, `les:n5-numeros-tempo-03`, `les:n5-numeros-tempo-07`,
`les:n5-verbos-02`, `les:n5-verbos-06`, `les:n5-particulas-lugar-05`, `les:n5-passado-03`,
`les:n5-passado-04`, `les:n5-passado-05`, `les:n5-adjetivos-01`, `les:n5-adjetivos-06`,
`les:n5-te-form-04`, `les:n5-te-form-07`, `les:n5-convites-01`, `les:n5-convites-02`,
`les:n5-convites-03`, `les:n5-convites-05`, `les:n5-rotina-01`, `les:n5-rotina-03`,
`les:n5-revisao-02`, `les:n5-revisao-03`, and the three `top:n5-kanji-exame` lessons
(`-01`, `-02`, `-03` — bare kanji reference pages, already held in `course/practice_exemptions.json`;
nothing to add beyond that known item).

Note on counting: class D is one systemic problem with six quoted instances, and classes C, G and I are
largely downstream of it. If D is fixed at the curriculum level, roughly twenty of the individual findings
below it disappear with it.
