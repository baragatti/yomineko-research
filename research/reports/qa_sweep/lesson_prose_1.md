# QA sweep — lesson prose, part 1/3 (pre-N5 + N5)

**Slice:** every lesson `body` under `course/pre-n5/` (41 lessons) and `course/n5/` (84 lessons) = **125 lessons**.
All 125 were read end to end.

**Method (important — it changes what counts as a defect).** The `.md` export prints raw markup: it shows
`<grammar ref>` as its slug (`gp-33`) and `<vocab ref>` as the kanji headword (`彼の`, `洋袴`, `珈琲`). The app
does not. `prototype/app/lib/render-body.server.ts:255` resolves a **vocab chip to `v.kana`**, a **grammar chip
to `forms[0].form`**, and a kanji chip to the character. Every finding below was therefore re-rendered with
those exact rules before being judged, and then re-checked against the raw `body`. Quoted text is **what the
learner sees on the page**.

Three whole classes that look alarming in the `.md` are *export artifacts only* and are **not reported**:
grammar slugs in running prose; rare-ateji headwords (`洋袴`, `珈琲`, `咖哩`, `彼の`, `未だ`, `迚も`, `燐寸`)
— they all render as kana (`ズボン`, `コーヒー`, `カレー`, `あの`, `まだ`, `とても`, `マッチ`); and most
`X (X)` pairs, which render as `kana (kanji)` and are useful.

**Out of scope by instruction:** sentence `structure_explanation`; and the STATE.md open items — furigana
coverage on `<jp>` spans, i+1 sentence re-selection (so I do not report on which sentence sits under
"Mais exemplos"/"Leitura"), the queued ateji list, grammar-identity merges, `needs[]`, listening audio.

---

## A — Prose that is factually wrong or incomplete

### A1. `les:n5-te-form-01` — the て-form rule table is missing the ぐ row

Rendered:

> Verbos godan (う): seguem o som da última sílaba. う・つ・る viram って (のる vira 乗って); ぬ・ぶ・む viram んで; く vira いて; す vira して.
> Exceção: 行く vira 行って (e não 行いて).

**ぐ → いで is absent.** A learner who applies this table to 泳ぐ, 急ぐ, 脱ぐ (脱ぐ is taught in
`les:n5-comparacoes-05`) will produce ×泳いて. This is the single most mechanical rule in N5 and the whole
topic 15 depends on it.
**Fix:** `く vira いて e ぐ vira いで (泳ぐ → 泳いで)`.

### A2. `les:n5-te-form-01` — the same table shows the "before" in kana and the "after" in kanji

Rendered: `食べる vira 食べて, でる vira 出て` · `する vira して; くる vira 来て` · `のる vira 乗って`.

The verbs are `<vocab>` chips (kana) and the derived forms are `<jp>` spans (kanji). In the one lesson where
the learner must *see* る being replaced by て, three of five examples hide the transformation
(`でる → 出て`, `くる → 来て`, `のる → 乗って`).
**Fix:** write both sides in the same script inside this table — `のる → のって`, `でる → でて`, `くる → きて`.

### A3. `les:n5-particulas-lugar-04` — the "destino" section contains no destination

> **に no destino: para onde se vai**
> O segundo uso central: に marca o destino de um movimento, junto com verbos como 行く (ir), 来る (vir) e 帰る (voltar). É o nosso "a / para":
> [frase] Em すぐに行きます, repare em すぐに ("já, na hora"): aqui o に ajuda a marcar o "momento" da ida…

The lesson objective is "Marcar o destino ou o alvo de um movimento com に", and the section's only example
is すぐに行きます — a **time/manner adverb**, explicitly explained as marking "o momento", not a destination.
The learner never sees 学校に行きます under this heading (it appears only later, inside an unrelated pitfall).
**Fix:** lead the section with 学校に行きます / うちに帰ります and move すぐに to the time section above.

### A4. `les:n5-adjetivos-05` — 来 is given a meaning it does not have

> O kanji 来 (leituras: ライ on, く kun como em 来る) significa "vir" e também **"vindouro / tornar-se"**, o que combina direto com o tema de hoje: o que está por vir é o que algo vai virar.

来 means come / next / forthcoming. It does **not** mean "tornar-se". The sentence invents the sense in order
to justify placing 来 in a なる lesson, and the justification is stated as fact.
**Fix:** `significa "vir" e, em compostos, "que vem / próximo" (来週, 来年)` and drop the なる link.

### A5. `les:n5-comparacoes-04` — いくら is answered with 七つ

> **Quantidade: いくら e os números**
> [frase] いくらほしい？ — Quanto você quer?
> Aqui いくら quer dizer "quanto/quantos" … Para responder, vêm a calhar os números. Você já viu o に ("dois"); some o ななつ ("sete coisas"), e dá para dizer 七つほしいです ("quero sete").

いくら asks *how much (money/amount)*; the counting answer 七つ answers いくつ. `les:n5-particulas-lugar-08`
itself teaches the split (`いくつ: quantos? (quantidade)` / `いくら: quanto custa?`), so the course contradicts
itself.
**Fix:** use いくつほしい？ for the counted answer, or keep いくら and answer with a price.

### A6. `les:n5-conectando-01` — 何 is glossed as a way of asking "por quê"

> - なに: "o quê / que", **para perguntar "por quê?"**.

何 does not ask "why"; the lesson's own topic-mates なぜ/どうして/なんで do (`les:n5-perguntas-04`).
**Fix:** delete the trailing clause, or move 何 out of a motive-vocabulary list.

### A7. `les:n5-adjetivos-05` — あと and うしろ are both glossed "atrás"

> - うしろ = "atrás / parte de trás" (後ろ).
> - あと = "atrás / depois" (後).

あと is temporal ("depois"); glossing it "atrás" beside うしろ, in the same list, invites exactly the error the
pair exists to prevent.
**Fix:** `あと = "depois (no tempo)"`.

### A8. `les:n5-convites-04` — 他 narrowed to "outro lugar"

> - 他 = outro lugar, em outro lugar.

ほか is "other / another (thing, person, option)". The "lugar" reading comes only from the lesson's own
example 他に行った. A learner will read 他の人 as "a pessoa de outro lugar".
**Fix:** `= outro, outra coisa; 他に = "em outro lugar / além disso"`.

### A9. `les:n5-numeros-tempo-04` — 二階 is labelled two ways in one lesson

Body: `一階 (térreo / 1º andar), 二階 (2º andar)`.
Culture note ten lines later: `o 一階 é o nível da rua (o nosso "térreo"), e 二階 é **o primeiro andar de cima**`.
**Fix:** pick one convention; the note's phrasing is the correct one, so the bullet should read
`二階 (o primeiro andar acima da rua)`.

---

## B — Glosses that leave the Japanese untranslated

The commonest defect in the slice. A `<vocab>` chip renders as **kana**, and the authored Portuguese
translation was written around it, so the "translation" contains an untranslated Japanese word and the
learner is given no Portuguese meaning at all at the point of use.

| Lesson | Rendered gloss | Should read |
|---|---|---|
| `les:n5-desu-wa-01` | `これは鍵です = "isto é uma かぎ" (sem "uma")` | "isto é uma chave" |
| `les:n5-desu-wa-01` | `お巡りさんです = "é おまわりさん"` · `"isto é おかね"` · `"aquilo é um え"` · `o は diz "falando de mim" … "sou いしゃ"` | "é policial" / "isto é dinheiro" / "aquilo é um quadro" / "sou médico" |
| `les:n5-numeros-tempo-09` | `此れは自転車です: "isto é uma じてんしゃ"` · `此の自動車: "este じどうしゃ"` · `駅は此方です: "a えき é por aqui"` · `こんなスポーツ: "um スポーツ deste tipo"` | bicicleta / carro / estação / esporte |
| `les:n5-verbos-05` | `先生がいます = "há um(a) せんせい"` · `先生が三人います = "há três せんせい"` | professor |
| `les:n5-verbos-06` | `お茶をください = "me dê おちゃ, por favor"` | chá |
| `les:n5-particulas-lugar-05` | `今年日本へ行きます = "ことし vou para o Japão."` · `"さらいねん vou para o Japão."` · `"No あき volto para o Japão."` | este ano / daqui a dois anos / no outono (あき is never glossed anywhere in the lesson) |
| `les:n5-particulas-lugar-08` | `五分だけ = "só cinco (ご) minutos"` | drop the `(ご)` |
| `les:n5-passado-01` | `"era um でんしゃ"` · `"aqui era a としょかん"` · `"era um ところ tranquilo"` | trem / biblioteca / lugar |
| `les:n5-passado-02` | `"não era どようび"` · `"não era ついたち"` · `"era とおか"` · `使わなかった = "não つかう" (não usei)` | sábado / dia 1º / dia 10 / "não usei" |
| `les:n5-passado-03` | `"esse とけい é caro, né?"` · `"que テレビ nova, né."` · `"olha, amanhã tem テスト, viu?"` · `"a でんき está acesa, viu?"` | relógio / TV / prova / luz |
| `les:n5-passado-04` | `"que てんき bom, hein!"` · `"ah, とり consegue とぶ, hein..."` · `"ah, como eu gosto de どうぶつ..."` · `"とても frio, hein..."` | tempo / pássaro voar / animais / "que frio, hein…" |
| `les:n5-comparacoes-03` | `"que tal esta ネクタイ?"` | gravata |
| `les:n5-comparacoes-04` | `"quero um ねこ"` · `"quero um にわ"` | gato / quintal |
| `les:n5-convites-01` | `"vamos juntos à プール?"` | piscina |
| `les:n5-convites-02` | `No ふゆ trocaríamos a praia por outro lugar, claro.` | see D3 — the sentence should be cut |
| `les:n5-convites-06` | `"já que 雨が降る, é melhor ficar em casa"` | "já que vai chover" |
| `les:n5-rotina-01` | `"Eu sempre bebo みず."` · `"Eu sempre espero na まち."` · `"a みせ de sempre"` · `"Esta みち é bem longa."` · `"A やおや é bem longe."` | água / cidade / loja / rua / quitanda |
| `les:n5-conectando-02` | `"é りっぱ, mas..."` · `"é ゆうめい, mas..."` · `"é りゅうがくせい, mas fala japonês muito bem"` | esplêndido / famoso / estudante de intercâmbio |
| `les:n5-conectando-04` | `"é que vou ao Japão らいげつ"` · `"aquilo deve ser um ラジカセ"` · `"é que eu gosto de レコード"` | mês que vem / rádio-gravador / discos |
| `les:n5-conectando-05` | `"é melhor ler よく (com atenção)"` | "é melhor ler com atenção" |
| `les:n5-conectando-06` | `"pretendo viajar らいねん"` · **`"pretendo aprender りょうりらいしゅう"`** · `"quando você encontra os りょうしん…"` · `"na hora do れんしゅう, entendi bem"` | ano que vem / **"pretendo aprender culinária na semana que vem"** / seus pais / treino |

`les:n5-conectando-06` is the worst case: 料理 and 来週 collide into `りょうりらいしゅう`, a word that does not
exist, inside what is presented as the Portuguese translation of 来週料理を習うつもりです.

**Fix (systemic):** in an authored translation, never reference the word by chip — write the Portuguese.
Keep the chip in the *Japanese* half of the line only.

---

## C — Headings that do not match their content

### C1. `les:n5-particulas-lugar-06` — "Os dias da semana" never says which days

Rendered list, verbatim:

> - 月曜日: げつようび
> - 火曜日: かようび
> - 水曜日: すいようび
> - 金曜日: きんようび

The gloss slot holds the **reading**, not the meaning. The lesson objective is
"Nomear os dias da semana em japonês", and "segunda / terça / quarta / sexta" appear nowhere in the body —
only inside exercise 3's prompt. Same paragraph: `誕生日 (たんじょうび)` is introduced and never glossed
("aniversário").
**Fix:** `月曜日 (げつようび): segunda-feira`, etc.

### C2. `les:n5-particulas-lugar-05` — a "par lado a lado" list where half the pairs have no meaning

> Repare como o 先 traz a ideia de "anterior" e o 今 a de "este", e veja cada par lado a lado:
> - 先月 (mês passado) e 今月 (este mês)
> - **先週 (せんしゅう) e 今週 (こんしゅう)**
> - **去年 (きょねん)** e 今年 (este ano)
> - **一昨年 (おととし)**: o "ano retrasado" …

Rows 2 and 3 give readings where rows 1 and 4 give meanings. The section's entire purpose is the contrast.
**Fix:** `先週 (semana passada) e 今週 (esta semana)` · `去年 (ano passado) e 今年 (este ano)`.

### C3. `les:n5-rotina-01` — "Exemplos reais com けっこう" shows only the meaning the lesson told you not to use

The lesson teaches けっこう = "bastante", and warns: *"Existe um segundo uso de けっこう que NÃO é o advérbio:
けっこうです é uma recusa educada"*. The section headed **"Exemplos reais com けっこう"** then gives two
examples, and **both are the refusal** (`お水だけでけっこうです`, `いいえ、けっこうです`). The adverb the
lesson actually teaches gets no real example.
**Fix:** rename the heading to "けっこうです: a recusa educada", or add a real adverbial example.

### C4. `les:n5-revisao-02` — the minutes section shows no minutes

> Use 〜じ para a hora e **〜ふん／〜ぷん para os minutos**. Ex.: 七時半 (sete e meia), 十二時 (meio-dia/meia-noite).

Neither example contains 分.
**Fix:** `Ex.: 十時五分 (dez e cinco), 三時半 (três e meia)`.

### C5. `les:n5-particulas-lugar-08` — "Mais **um** item para o seu repertório", followed by two

> #### Mais um item para o seu repertório
> - いくつ: quantos? (quantidade).
> - いくら: quanto custa? / quanto?.

(`les:n5-passado-02` uses the same heading correctly, with one item.)
**Fix:** "Mais dois itens…".

### C6. `les:n5-rotina-04` — "medidas, cores e cotidiano" has no colours

The list is みっか, メートル, メガネ, マッチ, みなみ.
**Fix:** drop "cores" from the heading.

### C7. `les:n5-te-form-07` — words promised "nos exercícios" appear in none

> **[example]** Mais algumas palavras úteis que vão aparecer nos exercícios:
> - ひくい: baixo — ひゃく: cem — ひき: contador para animais pequenos

I checked all five exercises of `ex:n5-te-form-07-1..5`: they use 病院, 飛行機, バス, 行く, 乗る. None of the
three words occurs.
**Fix:** remove the promise, or move the words into an exercise.

### C8. `les:n5-conectando-06` — "Dois verbos novos", then four bullets

> #### Dois verbos novos para essas frases
> - わかる: entender… — わすれる: esquecer. — 練習のとき、よく分かりました = … — 名前を忘れたことがあります = …

Two example sentences are formatted as if they were vocabulary entries in the same list.
**Fix:** split the examples out of the bullet list.

---

## D — Build-process and data commentary left in learner-facing prose

These read as notes the author wrote to themselves. Several are also **self-contradictory once rendered**,
because they describe the kanji headword while the page shows kana.

### D1. `les:n5-perguntas-01` — a vocabulary entry whose meaning is a note about itself

Rendered, inside "Mais lugares para praticar" (alongside げんかん, くに, かわ):

> - **ここ: a escrita em kanji de ここ**
>
> Note que ここ também se escreve com kanji, 此処, mas no dia a dia aparece quase sempre em kana, então não se preocupe em memorizar esse kanji por enquanto.

The bullet's gloss is circular and false — no kanji is displayed. The point is then made again, correctly,
in the very next sentence. `此処` is also one of only two places in the whole slice where an archaic ateji is
hard-coded in a `<jp>` span rather than a chip.
**Fix:** delete the bullet; keep the sentence.

### D2. `les:n5-desu-wa-02` — a list of place words containing "this isn't a place word"

Introduced as *"Aqui estão os 'primos' dos demonstrativos no mundo dos lugares"*:

> - あそこ: ali, lá …
> - あちら: por ali, naquela direção …
> - **あれ: este não é palavra de lugar; é o mesmo あれ da lição, aqui apontando uma pessoa distante dos dois ("aquela pessoa"). Escreva sempre em kana: o kanji desta entrada é raro e, na leitura comum, quer dizer "ele" (você o vê no N4).**

Three problems in one bullet: the list is defined as place words and this one announces it is not; the
instruction "Escreva sempre em kana" is meaningless because the page already shows kana; and the note about
"o kanji desta entrada" is about the JMdict record, not about Japanese.
**Fix:** remove the bullet entirely.

### D3. `les:n5-convites-02` — a sentence that exists only to place a vocabulary item

Mid-explanation of ましょう, between the ビーチに行きましょう example and the どこに行きましょう question:

> **No ふゆ trocaríamos a praia por outro lugar, claro.**

A non sequitur whose only function is to make 冬 appear in the body. The same lesson does it again in a
kanji mnemonic: *"Uma ベッド antiga, por exemplo, era feita de 木 (madeira)."*
**Fix:** cut both sentences; 冬 and ベッド are already in the vocabulary list below.

### D4. `les:n5-numeros-tempo-05` — the corpus is named to the learner

> **[warning]** Essa frase, **como aparece no corpus**, repete o まえ (一年前くらい前に), o que soa redundante. A forma natural seria 一年前くらいに来ました.

"o corpus" is build vocabulary; a learner has no referent for it.
**Fix:** *"Esta frase, tirada de um banco de frases reais, repete o まえ…"*.

### D5. `les:n5-adjetivos-07` — the grammar registry is described to the learner

> É o mesmo padrão que aparece **registrado como のが好き nas listas de gramática: as duas chaves descrevem exatamente a mesma construção**.
> A construção のがじょうず, **registrada também como のがじょうず**, segue a mesma fórmula…

"as duas chaves", "registrado nas listas de gramática" — and after rendering, the second sentence says a
construction is *also registered as itself*.
**Fix:** delete both clauses; the molde is already stated.

### D6. `les:n5-comparacoes-01` — the lesson apologises for having four records for three patterns

> #### Quatro moldes, três ordens
> Quatro moldes cobrem "A é mais X que B", mas em apenas três ordens: **o segundo e o quarto repetem a mesma ordem, com usos diferentes.**
> … Essa é **a ordem do alvo** より…のほうが. … Essa é **a ordem do alvo** のほうが…より.

"o alvo" is build vocabulary for *target grammar point*. And the learner is being told to hold four labels
for three word orders, which is a fact about the registry, not about Japanese.
**Fix:** present three orders; mention the preference reading of より…のほうが as a note.

### D7. `les:n5-numeros-tempo-02` — a note explaining an inconsistency that is no longer visible

> - 1 ひとつ, 2 ふたつ, 3 みっつ, 4 よっつ
> - 5 **いつつ (いつつ)**, 6 むっつ, 7 ななつ, 8 やっつ
> - 9 **ここのつ (ここのつ)**, e 10 とお …
> Repare que いつつ (いつつ, cinco) e ここのつ (ここのつ, nove) **escrevem o número em kanji (五, 九)** e fecham com つ … Por isso, aqui você se guia pelo kana.

Two items print their own reading twice, and the note then describes kanji that the page does not show.
**Fix:** write the whole series in plain kana and delete the note.

### D8. `les:n5-adjetivos-07` — a tip needed only because the example was written in bare kana

> [frase] ははは りょうりを つくるのが じょうずです
> Decompondo: 母 é "(minha) mãe" e leva o tópico は (por isso aparece o trio ははは: はは mais a partícula は)
> **[tip]** Atenção ao ler ははは em voz alta: os dois primeiros は são da palavra 母 e soam "ha-ha", mas o terceiro は … lê-se "wa". Ou seja: "haha-wa", não "ha-ha-ha".

The difficulty is entirely self-inflicted: exercise 4 of the same lesson writes it 母は料理を作るのが上手です,
where the problem does not arise.
**Fix:** use the kanji form in the body and drop the tip.

### D9. `les:n5-te-form-05` — a homophone warning whose second word is not a homophone

> O verbo はいる ("entrar") é godan … Não confunda o verbo com estes dois substantivos:
> - はい: pulmão
> - **さかずき: taça de saquê**
>
> Um cenário clássico de proibição é o はいざら ("cinzeiro") … Compare também com:
> - **はく: conde (título de nobreza)**

杯 renders as さかずき, which shares nothing with はいる — the stated reason for the bullet evaporates on the
page. 伯 ("conde") in an N5 permission/prohibition lesson is not defensible on any reading. Four of this
lesson's eight vocabulary items (肺, 杯, 灰皿, 伯) exist only to be adjacent to はい.
**Fix:** cut 杯, 伯 and 肺 from the lesson and delete both "não confunda" notes.

### D10. `les:n5-te-form-08` and `les:n5-conectando-07` — sections that exist to justify a vocabulary item

`les:n5-te-form-08` has a whole section **"O hiragana como sistema"** whose content is
*"Repare que todas essas contrações vivem em ひらがな"* — written so that 平仮名 can be in the unlock list of a
なくちゃ/なきゃ lesson. `les:n5-comparacoes-06` does the same for 七日: a culture note invents a trip
negotiation so that ７日 can appear in a すぎる lesson (`Introduz: vocabulário [７日]` is the lesson's *only*
vocabulary).
**Fix:** move these words to a lesson where they belong.

### D11. Romaji and stray Japanese inside Portuguese prose

- `les:n5-rotina-02`: *"O kanji 万 … **lê-se man**"* and *"Já 毎 … **lê-se mai**"* — readings in **romaji**, in a
  course that drops romaji after `top:pre-n5-sons`. Everywhere else readings are kana.
  **Fix:** `lê-se マン` / `lê-se マイ`.
- `les:n5-particulas-lugar-07`: a tip opens *"**同じ場面** (a mesma cena!): …"* — a Japanese phrase used as
  Portuguese, then translated. **Fix:** *"É a mesma cena: …"*.
- `les:n5-te-form-03`: *"a **okaasan** passou manteiga no pão e está pronto"* — romaji, and the wrong word
  (the lesson's vocabulary is 母 / はは, not お母さん). No Japanese sentence is ever given for the promised
  てある example. **Fix:** write the sentence — `母がパンにバターを塗ってあります`.
- `les:n5-te-form-08`: *"Imagine o **otoko** que põe a força no arrozal: 男 tem que trabalhar, 働かなきゃ."*
  Romaji, plus a gender stereotype in a mnemonic. **Fix:** *"Imagine alguém pondo a força no arrozal."*

### D12. Vacuous "X aparece em X" sentences

The `<kanji>` chip shows the character and the `<vocab>` chip shows its kana, so these collapse:

| Lesson | Rendered | Fix |
|---|---|---|
| `les:n5-numeros-tempo-01` | `十 significa dez, lê-se じゅう **e aparece na palavra じゅう**.` | drop the clause |
| `les:n5-rotina-02` | `**Aparece em まん** ("dez mil") e em まんねんひつ ("caneta-tinteiro"…)` | `Aparece em 万年筆 ("caneta-tinteiro")` |
| `les:n5-conectando-05` | `右 … **Aparece em 右** ("a direita, o lado direito").` and `左 … **Aparece em 左**` | `Aparece em 右手 ("mão direita")` / `左手` |
| `les:n5-numeros-tempo-04` | `Você o encontra em 大 (tamanho grande)` | `em 大学, 大人` |

---

## E — Material taught twice as if it were new

Five pairs. In each case the second lesson opens as an introduction, re-derives the same rule and repeats the
same pitfall, and never says the learner has seen it. This is a courseware-sequencing question for the
teacher, distinct from the registry-level duplicates already in `research/reports/grammar_identity_merges.md`.

| First taught | Re-taught as new | Evidence |
|---|---|---|
| `les:n5-adjetivos-07` — `のが好き / のが上手 / のが下手` (already states *"Para o oposto, é só pôr 下手 no lugar: 料理を作るのが下手です"*) | `les:n5-adjetivos-08` — a whole lesson on のが下手 | adjetivos-08 declares `vocabulário [—]`, `kanji [—]`; it re-explains の nominalisation, the が rule and the 上/下手 "mão em cima / mão embaixo" mnemonic verbatim |
| `les:n5-convites-04` — "Recomendar com 〜たほうがいい" | `les:n5-conectando-05` — "Aconselhar e citar: ほうがいい…" | both re-derive ほう = "lado/opção", both give the *"é 行ったほうがいい, nunca 行くほうがいい"* pitfall, and **both cite the same sentence** `sent:tatoeba-216787` |
| `les:n5-rotina-04` — "Listar atividades: 〜たり〜たり する" | `les:n5-conectando-07` — "Listar exemplos…: ～たり～たりする e 方" | same formation rule, same 読む/休む examples, same "não é ordem fixa" pitfall |
| `les:n5-verbos-05` — ある/いる + が, incl. *"ある tem um negativo irregular … ない, e não あらない"* | `les:n5-particulas-lugar-02` — "Existência na fala casual: ある e いる", presenting *"O negativo de ある é irregular: não é 'あらない', e sim ない"* as new | `les:n5-particulas-lugar-01` sits between them teaching あります/います with the same "se move por vontade própria" rule |
| `les:n5-comparacoes-04` — a full lesson on 〜がほしい (が not を, "não é bem um verbo") | `les:n5-convites-06` — `ほしい = querer (ter algo)… **É um adjetivo, não um verbo**: 水が欲しい` | convites-06 lists it as new vocabulary with the same explanation |

Smaller repeats worth the teacher's eye: **雨** is "o kanji da lição" in *both* `les:n5-conectando-01` and
`les:n5-conectando-04`, with the same "janela com gotas" mnemonic, three lessons apart — and
`les:n5-conectando-04` declares `kanji [—]` while carrying a "#### Kanji da lição: 雨" section. **右** is
introduced in `les:n5-te-form-06` and again in `les:n5-conectando-05`; **左** likewise. **背** is glossed
"altura, estatura" in `les:n5-numeros-tempo-03` and "costas" in `les:n5-conectando-04`. The 四/死 culture note
appears in `les:n5-numeros-tempo-01` and again in `les:n5-passado-02`.

---

## F — Lessons with no teachable content

### F1. `les:n5-kanji-exame-01`, `-02`, `-03` — the last three lessons of N5 are empty shells

All three: **0 exercises, 0 sentence refs**, and a body that is (a) one boilerplate paragraph, **identical
word for word in all three**, (b) seven or eight `### <kanji>` headings each containing only the kanji chip
and no prose whatsoever, (c) a checklist of seven or eight copies of one line:

> Estes kanji fazem parte do conjunto esperado no exame deste nível. Alguns você já viu dentro de palavras; aqui cada um ganha um momento próprio: observe o traçado, as leituras e as palavras de exemplo na página de cada kanji (toque no kanji para abrir).
>
> #### 会 · #### 口 · #### 古 · #### 多 · #### 安 · #### 少 · #### 店 · #### 手
>
> - Reconheço o kanji 会 e **sei onde conferir suas leituras**.
> - Reconheço o kanji 口 e sei onde conferir suas leituras. …

23 kanji are "taught" this way, immediately before the JLPT N5 mock. "Sei onde conferir suas leituras" is not
a learning objective. "toque no kanji" also assumes a touchscreen.
**Fix:** either give each kanji two lines (meaning, the two readings, one word the learner already knows) and
add recognition exercises, or fold the 23 kanji into the topics where their words already appear.

### F2. Vocabulary-only lessons inside grammar topics

`les:n5-convites-05` ("Vocabulário do dia a dia: tempo e números") and `les:n5-convites-06` — both declare
`gramática [—]`, both have `Frases: —`, and `les:n5-convites-05` says so itself: *"Esta lição não traz
gramática nova"*. Its "Juntando tudo" section produces **no Japanese sentence at all**:

> Pense num convite real: "Toda semana (毎週) eu vou nadar; nós dois (二人) podemos ir juntos, são uns dez minutos (分) de caminhada, e eu já tenho duas entradas (枚) para o dia 2 (２日)."

A vocabulary lesson that never models the words in Japanese. Also, 二つ (already in `les:n5-numeros-tempo-02`)
and 分 (already in `les:n5-particulas-lugar-04`) are re-introduced.
**Fix:** write the Japanese sentence, and cut the repeated items.

### F3. `les:n5-particulas-lugar-08` — a section that teaches nothing

> #### Ponte: o que existe na lista
> Listas e existência andam juntas … A peça-chave é があります ("há / existe"): が marca o que existe e あります é a forma polida de ある. **Agora imagine encher esse "o que existe" com uma lista de や … e você junta as duas ideias da lição.**

It restates があります (taught in `les:n5-particulas-lugar-01`) and then asks the learner to imagine the
example instead of giving it.
**Fix:** give the sentence — `机の上に本やペンがあります` — or delete the section.

---

## G — Internal contradictions in the pre-N5 phonetics

The pre-N5 topics state three rules and then break them in later lessons.

### G1. The "o é sempre fechado" rule, broken three times

`les:pre-n5-hiragana-01/-03/-05` and `les:pre-n5-katakana-10` all insist the Japanese o is the **closed ô of
"avô", never the open ó of "avó"**. `les:pre-n5-hiragana-05` even uses "nó" as the counter-example:
*"の é 'no' (com o fechado, o 'ô' de 'avô', nunca o 'ó' de 'nó')"*. Then:

| Lesson | Text | Problem |
|---|---|---|
| `les:pre-n5-katakana-05` | `- ノ(no): como o no de **"nó"**.` | the exact word hiragana-05 forbids |
| `les:pre-n5-hiragana-14` and `les:pre-n5-katakana-14` | `しょ … como o cho de **"chove"**` | "chove" is [ˈʃɔvi] — open |
| `les:pre-n5-katakana-13` | `ピアノ termina num **"o" aberto** e claro (nunca "pianu")` | states the opposite of the rule |

**Fix:** `ノ … como o "no" de "novo"`; `ショ … como o "cho" de "chocolate"`; `ピアノ termina num "o" fechado e
limpo (o "ô" de "avô"), nunca "pianu"`.

### G2. `les:pre-n5-katakana-06` — the whole HA family modelled on silent-h Portuguese words

`les:pre-n5-hiragana-06` is careful: *"O h japonês é um sopro leve, igual ao h do inglês em 'hello' … em vez de
deixar o 'h' mudo como em 'hora'"*. The katakana lesson then models every kana on a Portuguese word whose h is
**silent**:

> - ハ(ha): como o ha de "harpa". - ヒ(hi): como o hi de "hiena". - ヘ(he): como o he de "hélice". - ホ(ho): como o ho de "hotel".

A learner following this will produce "arpa", "iena", "élice", "otel".
**Fix:** repeat the hiragana-06 framing — *"o mesmo sopro leve de 'hello', antes de cada vogal"* — and drop the
Portuguese h-words.

### G3. `les:pre-n5-katakana-09` — the objective contradicts the taught sound

Objective and checklist: *"Lembrar que a Família do RA usa o mesmo 'r' suave do japonês **(entre 'r' e 'l')**"*
/ *"Faço o 'r' japonês suave, entre 'r' e 'l'."* But `les:pre-n5-hiragana-09` says explicitly: *"E não troque
por L também: ら nunca é 'la'"*, and this lesson's own body says only *"um toque rápido da ponta da língua"*.
The "between r and l" framing is an English-speaker's crutch and is wrong for a Brazilian, who already has the
exact tap.
**Fix:** replace with *"o mesmo r batido de 'caro'"* in the objective and the checklist.

### G4. `les:pre-n5-katakana-11` vs `-03`/`-04`/`-12`/`-14` — シ/ツ described in opposite terms

| Lesson | Text |
|---|---|
| `les:pre-n5-katakana-03` | `No シ os dois traços de cima ficam **quase horizontais**` |
| `les:pre-n5-katakana-12` | `No シ os tracinhos de cima ficam **quase deitados**; no ツ os tracinhos ficam **em pé**` |
| `les:pre-n5-katakana-14` | `O シ tem os tracinhos mais na **horizontal**; o ツ … mais na **vertical**` |
| `les:pre-n5-katakana-11` | `no シ os pinguinhos ficam **empilhados na vertical**` … `No ツ os pinguinhos ficam **lado a lado na horizontal**` |

Both descriptions are true of different things — 03/12/14 describe the *direction each dash points*, 11
describes *how the pair is arranged* — but the course never distinguishes them, so lesson 11 reads as a flat
reversal of lessons 3 and 4.
**Fix:** use one vocabulary throughout, e.g. *"no シ os dois tracinhos ficam empilhados (um sobre o outro) e
apontam para a direita; no ツ ficam lado a lado no topo e apontam para baixo"*.

### G5. `les:pre-n5-katakana-08`/`-09`/`-11`/`-15` vs `-01`/`-04`/`-06` — two romanisation systems

Macrons in one lesson, doubled vowels in the next, **for the same word**:

- コーヒー is `kōhī` in `les:pre-n5-katakana-01` and `-06`, but `koohii` in `-15`.
- ジュース is `jūsu` in `les:pre-n5-katakana-14`, but `juusu` in `-15`.
- `-04` `kōto, sūtsu, takushī` · `-09` `karē, rāmen` vs `-03` `sukii, shiisoo, soosu` · `-08` `yuniiku,
  mayoneezu, yooyoo` · `-15` `sakkaa, supootsu`.

**Fix:** pick one (the macron style already dominates) and normalise the topic.

### G6. Broken words in the mnemonics (emphasis spans swallow the space)

`<emphasis>`/`<text weight="bold">` spans carry the space *inside* them, so the word splits on the page:

| Lesson | Rendered | Intended |
|---|---|---|
| `les:pre-n5-sons-03` | `o r de "ca r o" ou "a r ara"` | caro / arara |
| `les:pre-n5-hiragana-03` | `uma s aia esvoaçando` · `como um pi ru lito` · `um se máforo` | saia / pirulito / semáforo |
| `les:pre-n5-hiragana-04` | `um dedo do pé (to e, em inglês)` | toe |
| `les:pre-n5-hiragana-09` | `o ra de "ca ra col"` · `"a ri sco"` · `"ba ru lho"` · `"ca re ca"` · `"ca ro"` | caracol / arisco / barulho / careca / caro |
| `les:pre-n5-katakana-01` | `Imagine um A nzol` | anzol |
| `les:pre-n5-katakana-02` | `uma ca pa de super-herói` · `numa ki tchen` | capa / kitchen |
| `les:pre-n5-katakana-03` | `lembra um se máforo torto` | semáforo |
| `les:pre-n5-katakana-07` | `o ma de "ma çã"` · `"mi nha"` · `"mu ro"` · `"me sa"` · `"mo la"` | maçã / minha / muro / mesa / mola |
| `les:pre-n5-katakana-08` | `um i ate` · `num u tensílio` · `"ia te"` · `"io gurte"` | iate / utensílio / iogurte |
| `les:pre-n5-katakana-09` | `uma ra mpa` · `duas ri scas` · `uma ro da quadrada` | rampa / riscas / roda |
| `les:pre-n5-katakana-10` | `o começo de "w affle"` | waffle |
| `les:pre-n5-katakana-11` | `uma seta apontando para n ordeste` | nordeste |
| `les:pre-n5-katakana-14` | `o "nh" abrandado de "ni nha"` | "ninha" is not a word — the l1-advantage below uses **"ninho"** |

**Fix (mechanical):** move the space outside the span — `uma <b>s</b>aia`, not `uma<b> s</b>aia`.

### G7. Two small pre-N5 items

- `les:pre-n5-orientacao-01`: the reassuring paragraph *"O melhor de tudo: o app agenda as revisões para você…"*
  is in a **`warning`** box. Nothing about it is a warning. **Fix:** `tip`.
- `les:pre-n5-katakana-01`: `- イ(i): … São dois traços inclinados, como duas perninhas **(o i tem dois
  pontinhos? aqui são dois riscos)**.` The parenthetical is incoherent (the lowercase i has one dot) and reads
  as an unfinished authoring note. **Fix:** delete it.
- `les:pre-n5-hiragana-02` and `les:pre-n5-katakana-02`: `く(ku): como **cu** de "cuca"` and `こ é sempre ko,
  nunca vira "**cu**"` — in pt-BR this is unambiguously vulgar and will land as a joke in a beginner lesson.
  **Fix:** *"く(ku): o som ku, como no começo de 'cuca'"* and *"こ é sempre ko, nunca 'ku'"*.

---

## H — Typography and consistency

- **Missing space after punctuation before a chip — 70 occurrences.** e.g. `les:n5-perguntas-04`
  `…prefira なぜ ou どうして; com amigos,なんで cai bem`; `les:n5-rotina-01` `Ações:みる(ver, olhar,
  assistir),みせる(mostrar),まつ(esperar)`; `les:n5-desu-wa-04` `Bônus de vocabulário:おねえさん`.
  **Fix:** one exporter-side or authoring-side pass; the space belongs before `<vocab|grammar|kanji ref>`.
- **Missing space before an opening quote — 4 occurrences.** `les:pre-n5-hiragana-03` and
  `les:pre-n5-katakana-03`: `e nunca"si"`; `les:pre-n5-hiragana-05`: `o n"some" no nariz`;
  `les:n5-adjetivos-06`: `em japonês, "gostar"não é um verbo`.
- **`X= gloss` vs `X = gloss` — inconsistent across 34 lessons (186 hits).** `les:n5-adjetivos-05` alone has
  20 (`うえ= "em cima"`), while `les:n5-numeros-tempo-03` writes `人 = ひと`. Pick one.
- `les:n5-te-form-04`: `- **書;** significa escrever` and `- **名;** significa nome` — a semicolon where a colon
  or dash belongs.
- `les:n5-particulas-lugar-07`: the H2 is `あげる,くれる e もらう: dar e receber` — no space after the comma.

---

## I — Titles

- **`top:n5-desu-wa` title: `Frases básicas: o tópico は e o *copula* です`.** "cópula" is feminine and
  accented in Portuguese; every lesson body in the topic writes "a cópula" correctly. This is the topic
  heading a learner sees above five lessons. **Fix:** `a cópula です`.
- **`top:n5-passado` = "Passado polido e nuances" covers three lessons that are not about the past.**
  `les:n5-passado-03` (ね/よ), `-04` (なあ) and `-05` (proibição com な + ênfase masculina) are sentence-final
  particles. "Polido" is also inaccurate: `-02` teaches the casual じゃなかった. **Fix:** retitle the topic
  ("Passado e partículas finais") or move 03–05 into a particles topic.
- **`top:n5-convites` = "Convites, sugestões e habilidade"** — no lesson in the topic teaches habilidade
  (じょうず/へた are `top:n5-adjetivos`). **Fix:** "Convites, sugestões e conselhos".
- **The three revisão titles use a semicolon as a separator:** `Revisão N5; Fundamentos: kana, です e
  demonstrativos`, `Revisão N5; Verbos, adjetivos e lugar/tempo`, `Revisão N5; Forma て, convites e ponte para
  o N4`. **Fix:** `Revisão N5 — Fundamentos: …` is barred by the no-em-dash rule, so use a colon or a comma:
  `Revisão N5: fundamentos (kana, です e demonstrativos)`.
- Nine lesson titles differ from their own H2 in ways worth a glance, most benignly. The one worth acting on:
  `les:pre-n5-katakana-01` is titled *"Katakana: a Família do A (アイウエオ) e para que serve o katakana"* but its
  H2 drops the second half, which is a third of the lesson.

---

## Count table

| Class | What it is | Lessons touched | Items flagged |
|---|---|---|---|
| A | Prose factually wrong or incomplete | 9 | 9 |
| B | Portuguese gloss leaves the word untranslated | 20 | 45 |
| C | Heading does not match its content | 8 | 8 |
| D | Build/data commentary in learner prose | 17 | 20 |
| E | Material re-taught as new | 15 | 5 lesson pairs + 6 smaller repeats |
| F | Lessons with no teachable content | 6 | 3 |
| G | pre-N5 phonetics contradictions + broken mnemonic words | 21 | 7 |
| H | Typography / consistency | 40 | 5 classes (≈265 occurrences) |
| I | Titles | 4 topics + 4 lessons | 5 |
| **Total** | | **125 checked** | **107 flagged** |

**Checked:** 125 lesson bodies (41 pre-N5 + 84 N5), each rendered as the app renders it and re-read against
the raw markup.
**Flagged:** 107 items in 9 classes.
**Not flagged, deliberately:** grammar slugs and ateji headwords visible only in the `.md` export (3 classes,
~150 apparent hits) — verified as export artifacts, invisible to the learner; and everything already open in
`STATE.md`.

The two findings I would put in front of the teacher first are **B** (the largest, most mechanical, and the
one that most directly costs a beginner comprehension) and **F1** (the last three lessons before the N5 mock
exam contain no teaching at all).
