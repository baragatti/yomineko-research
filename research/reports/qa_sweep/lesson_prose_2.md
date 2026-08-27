# QA sweep — lesson prose, part 2/3: every lesson body under `course/n4`

**Slice:** all 96 lesson bodies in `course/n4/topic-21…topic-37` (668,299 chars of `body`), read in full.
**Reference:** `design/translation_style.md`; rendering behaviour verified against
`yomineko-prototype/app/lib/render-body.server.ts` (the learner-facing renderer).
**Out of scope by instruction:** sentence `structure_explanation`; known STATE.md items (the 875 `<jp>`
spans with kanji and no `reading`, the empty `needs[]` model, the i+1 sentence backlog, the
`vocab_disambiguation_review` homographs, listening audio).

**Method note.** Where a finding says "renders as", I resolved the element against the actual renderer:
a `<grammar ref>` chip prints `forms[0].form`, a `<vocab ref>` chip prints the record's **kana**, and any
element with no `case` in `renderBody`'s switch falls through to `default: push(kids())` — i.e. a
self-closing unknown tag prints **nothing**. Findings marked "renders as" were checked that way, not
assumed from the Markdown export (the exporter and the app disagree about chips).

---

## A. Japanese that renders wrong or contradicts its own gloss

### A1. `les:n4-passiva-03` — six example sentences are split around a vocab chip; the visible Japanese loses its negation and says the opposite of the translation
**Current (raw body, `l1-advantage` note):**
```
<jp reading="しごとはあまりつづかない">仕事はあまり</jp><vocab ref="vocab:1405790"/><text> ("o trabalho não dura muito"), </text><jp reading="バスはあまりおくれない">バスはあまり</jp><vocab ref="vocab:1589040"/><text> ("o ônibus não atrasa muito")</text>
```
`vocab:1405790` is 続く/つづく and `vocab:1589040` is 遅れる/おくれる, so the chip prints the **dictionary,
affirmative** form. The learner reads **仕事はあまりつづく** glossed "o trabalho não dura muito" and
**バスはあまりおくれる** glossed "o ônibus não atrasa muito" — the opposite of the gloss, and a direct
violation of the rule this very lesson is teaching ("Os dois **exigem** a negação").
The ruby is also misaligned: the full-sentence reading `しごとはあまりつづかない` sits over the four
characters 仕事はあまり.

Four more in the same lesson, same cause:
- `〔この町は〕(このまちはきんじょのみせがあまりない)«V:近所»〔の店があまりない〕(のみせがあまりない)` — the reading string is emitted twice, once whole and once partial.
- the same again with `ぜんぜんない`.
- `〔この間の〕(このあいだのやくそくをぜんぜんわすれていない)«V:約束»〔をぜんぜん忘れていない〕(をぜんぜんわすれていない)`.
- `〔となりの人はあまり〕(となりのひとはあまりかまわない)«V:構う»〔わない〕(わない)` → renders **となりの人はあまりかまうわない**, which is not Japanese (構う + わない).

**Fix:** write each example as one span and drop the chip from inside the sentence, e.g.
`<jp reading="しごとはあまりつづかない">仕事はあまり続かない</jp>` and
`<jp reading="となりのひとはあまりかまわない">となりの人はあまり構わない</jp>`.

### A2. `les:n4-volitivo-06` — the imperative of 来る renders as bare `い`
**Current:** `<jp reading="く">来</jp><jp>る</jp><text> vira </text><ruby base="来" reading="こ"/><jp>い</jp>`
`ruby` has no `case` in the renderer's switch and is void, so it prints nothing. The learner reads
"…**来る** vira **い**." — the one form the bullet exists to teach (来い/こい) is invisible.
This is the only `<ruby>` in all of n4.
**Fix:** `<jp reading="こい">来い</jp>`.

### A3. `topic-37-kanji-exame` (all 5 lessons) — the entire body renders empty apart from headings
Each lesson is a heading plus eight `<stroke ref="kanji:X"/>` elements. `stroke` also has no `case`
in the renderer, so all 40 stroke diagrams print nothing. The five lessons additionally have
**zero exercises** and **no `<reading>`** — they are the only n4 lessons with neither. What a learner
actually gets is a paragraph, eight kanji chips as headings, and eight empty gaps, followed by eight
checkboxes saying "sei onde conferir suas leituras".
**Fix:** either add a `stroke` case to the renderer, or replace the element with content that renders
(kanji chips + readings inline) and give the lessons at least a recognition exercise each.

### A4. `les:n4-aspecto-03` — the contraction section says a form "turns into" itself
**Current:** `Na conversa do dia a dia,<jp>てしまう</jp> quase sempre vira <grammar ref="gram:te-shimau-chau"/>.`
`gram:te-shimau-chau`'s `forms[0].form` is `てしまう`, so this renders **"てしまう quase sempre vira てしまう."**
under a heading titled `〜ちゃう／〜じゃう: a contração da fala`.
**Fix:** `…quase sempre vira <jp>ちゃう</jp>.`

### A5. `les:n4-condicionais-01` — the formation rule renders as "Para fazer ら, é só acrescentar ら"
**Current:** `Para fazer <grammar ref="gram:gp-60"/>, é só acrescentar <jp>ら</jp> no fim dela.`
`gram:gp-60`'s `forms[0].form` is `ら` (its `structure_pattern` is `～たら`). The sentence is
self-defeating as printed.
**Fix:** point the chip at `gram:tara` (form `たら`), or write `Para fazer <jp>たら</jp>`.

### A6. Malformed grammar-chip forms leaking into the prose (15 chips, 12 lessons)
The chip prints `forms[0].form`, and for these records that field has had its placeholders stripped or
carries an editorial artifact. Each of the following is a sentence a learner reads:

| Lesson | Reads as | Should be |
|---|---|---|
| `les:n4-condicionais-08` | "embutir uma pergunta dentro de outra frase com **-  か**" | 疑問詞 + か |
| `les:n4-condicionais-08` | "comparar dois itens com **とと**" | と〜と、どちらが |
| `les:n4-condicionais-08` | "**以上 ①** (いじょう) significa 'X ou mais'" | 以上 (the ① is a source artifact) |
| `les:n4-experiencia-06` | "**ずっと ①** (o tempo todo / muito mais)" | ずっと |
| `les:n4-experiencia-06` | "a negação branda **くは**" | 〜くはない |
| `les:n4-experiencia-01` | "a mudança acontece sozinha (**く**)" | 〜くなる／〜になる |
| `les:n4-keigo-02` | "**てすみ** é exatamente esse padrão de desculpa em ação" | 〜てすみません |
| `les:n4-oracoes-relativas-06` | "a estrutura **のはだ**" / "use **はの一つだ**" | 〜のは〜だ / 〜は〜の一つだ |
| `les:n4-conectores-05` | "o padrão de tema com contraste **はが… は**" | は〜が…は |
| `les:n4-dar-receber-03` | "entra **ようにてほしい**" | 〜ように〜てほしい |
| `les:n4-conectores-04` | "o padrão repetido **しし**" | し〜し |
| `les:n4-conectores-03` | "**とかとか** = tipo X e Y" | とか〜とか |
| `les:n4-keigo-04` | "**おになる**" / "**おください**" | お〜になる / お〜ください |

**Fix:** repair `forms[0].form` on those grammar records (this is corpus-side), **or** stop relying on
the chip for the pattern name and write it inline as `<jp>`. Either way the lesson prose is what a
reviewer will see failing.

### A7. Katakana words given hiragana furigana (5 spans, 4 lessons)
| Lesson | Surface | Reading given |
|---|---|---|
| `les:n4-forma-simples-04` | さっきのメール | さっきの**めーる** |
| `les:n4-forma-simples-04` | オートバイで行く | **おーとばい**でいく |
| `les:n4-condicionais-06` | 社長が会議室にいない場合はメールを… | …ばあいは**めーる**を… |
| `les:n4-condicionais-06` | この品物はこのビルで買えます | このしなものはこの**びる**でかえます |
| `les:n4-potencial-04` | バスがなかなか来ない | **ばす**がなかなかこない |

The ビル one is the worst: it sits two lines below an `l1-pitfall` that warns the learner to hear
ビル vs ビール, and then writes ビル in hiragana.
**Fix:** keep loanwords in katakana inside the `reading` attribute (`さっきのメール`, `おーとばい`→`オートバイ`, etc.).

### A8. `les:n4-aspecto-07` — a furigana reading with a space inside it
`<jp reading="この じ">この字</jp>` → the ruby prints `この じ` over two characters.
**Fix:** `reading="このじ"` (or mark only 字: `この<jp reading="じ">字</jp>`).

### A9. Redundant ruby and doubled kana (systemic, 215 occurrences)
- **174** `<jp reading="X">X</jp>` where the surface is kana-only and the reading is byte-identical.
  The renderer's fallback puts ruby over the whole run, so the learner sees the same kana stacked on
  itself (e.g. `〔そんなに〕(そんなに)`).
- **41** places (in `les:n4-forma-simples-01`, `-06`, `les:n4-aspecto-04`, `les:n4-volitivo-07`,
  `les:n4-conectores-01`, `-04`) where a `<vocab>` chip is immediately followed by its own kana:
  `<vocab ref="vocab:1521400"/>(<jp>ぼく</jp>, "eu")` renders **"ぼく(ぼく, 'eu')"**;
  `<vocab ref="vocab:1066680"/>(<jp reading="どうぐ">どうぐ</jp>)` renders **"どうぐ(どうぐ)"** with ruby on top.
**Fix:** drop the `reading` attribute when the surface is already kana, and drop the parenthetical kana
when a vocab chip precedes it (the chip already prints the kana).

---

## B. Factual errors in the explanation

### B1. `les:n4-volitivo-01` — a warning that gets the grammar backwards
**Current:** `Cuidado para não confundir este <grammar ref="gram:you-da"/> volitivo (vontade) com o <jp>〜ようだ</jp> de "parecer/aparência".`
It renders as "Cuidado para não confundir este **ようだ** volitivo (vontade) com o 〜ようだ de
parecer/aparência" — i.e. it warns the learner not to confuse a form with itself, and asserts that
there is a volitional 〜ようだ. There isn't: the volitional is 〜よう/〜おう (no だ); `gram:you-da`'s own
label is "parece que / aparentemente (〜ようだ)". This lesson also **unlocks** `gram:you-da`, which is the
conjecture pattern properly taught later in `les:n4-suposicao-03`/`-04`.
**Fix:** rewrite as "Não confunda o **〜よう/〜おう** volitivo com **〜ようだ** ('parece que'), que você vê no
tópico de suposição", and move the `gram:you-da` unlock to the suposição topic.

### B2. `les:n4-revisao-02` — contradicts `les:n4-potencial-02` and its own example
**Current:** `A forma com substantivo é <jp reading="～ことができる">〜ことができる</jp>:<jp>日本語を話すことができます</jp>(consigo falar japonês).`
`les:n4-potencial-02` explicitly teaches the opposite: *"o que vem antes de ことができる é sempre um
verbo, nunca um substantivo solto… Com verbo, o こと é obrigatório"*. And the example given here is a
verb (話す), not a noun.
**Fix:** "A alternativa mais formal é [verbo no dicionário] + 〜ことができる: 日本語を話すことができます."

### B3. `les:n4-transitividade-04` — two nouns presented as a transitive/intransitive pair
**Current (`l1-advantage`):** `<vocab ref="vocab:1172830"/> é você <strong>agindo sobre</strong> o veículo (alguém o conduz, transitivo), enquanto o <vocab ref="vocab:1600530"/> é só a coisa que anda.`
運転 ("condução") and 乗り物 ("veículo") are both nouns; neither is a transitive or an intransitive verb.
The note is the lesson's only attempt to tie its vocabulary to the topic, and the tie is a category error.
**Fix:** use a real pair from the lesson's own field, e.g. 車を止める (tr., を) × 車が止まる (intr., が),
or drop the note.

### B4. `les:n4-keigo-01` — 全然 described as carrying negation itself
**Current:** `<jp reading="ぜんぜんわかりません">全然わかりません</jp>= "não entendo nada". É como o nosso "não... nada": a negação aparece duas vezes, no advérbio e no verbo.`
全然 is not a negative word; it is an adverb that **requires** a negative predicate. The negation
appears once, in ません. (`les:n4-passiva-03` states this correctly: "os dois **exigem** a negação".)
**Fix:** "…é como o nosso 'não… nada': o advérbio anuncia a negação lá na frente e o verbo a realiza no fim."

### B5. `les:n4-forma-simples-04` — the culture note contradicts the rule the lesson just taught
The lesson's rule: *"se dá para apontar um número certo… a leitura é ごろ; se é uma fase vaga da vida…
a leitura é ころ"*. Two sections later:
**Current:** `Você vai ouvir muito <jp reading="しょうがつごろ">正月頃</jp> ("lá pela época do Ano-Novo"): tempo aproximado ligado a uma temporada inteira, então a leitura é <em>ごろ</em> por estar preso a um ponto nomeado do ano.`
"ligado a uma temporada inteira, **então** a leitura é ごろ" is exactly the case the lesson assigned to
ころ; the justification arrives only after the "então", and contradicts what precedes it.
**Fix:** "…é ごろ, e não ころ: 正月 é um ponto nomeado do calendário, não uma fase vaga da vida — mesmo
cobrindo vários dias, ele funciona como um marco."

### B6. `les:n4-oracoes-relativas-01` — the kanji bullet illustrates 立 with a word written 建
**Current:** `<kanji ref="kanji:立"/> "levantar-se, erguer". Imagine uma pessoa de pé sobre o chão (a linha de baixo). Ergue-se a mesma ideia em <jp reading="たてる">建てる</jp> (<vocab ref="vocab:1257330"/>, "construir")`
Every other bullet in the same list gives a word that **contains** the kanji (通 → 通る). Here the
example word contains 建, not 立; a beginner reading a kanji list will take 建てる as proof of 立.
**Fix:** use 立つ(たつ) / 立てる(たてる) written with 立, and move the 建てる aside into a note if the
semantic parallel is wanted.

---

## C. Cross-lesson contradictions in the sequencing prose

| # | Lesson | Text as written | Why it is wrong |
|---|---|---|---|
| C1 | `les:n4-condicionais-04` | "Você já sabe montar condicionais com たら, ば, と e なら." | と and なら are introduced in `les:n4-condicionais-05`, the **next** lesson, whose own opening says "fechamos o quadro dos quatro condicionais com os dois que faltam: と … e なら". |
| C2 | `les:n4-keigo-03` | "Você já viu o teineigo … e as formas humildes **お〜する e いたす**." | Both are introduced in `les:n4-keigo-05`, two lessons later, whose opening says "Agora **começa** a outra metade do keigo: o kenjōgo". |
| C3 | `les:n4-oracoes-relativas-05` | "**Você já sabe que 京** aparece em palavras como Tóquio…" | 京 is a new unlock of this very lesson, which later has a section "### O kanji 京" teaching it from scratch. |
| C4 | `les:n4-conectores-07` | "Chegamos à **última lição do módulo**" | N4 is a single module (`mod:n4`, topics 21–37). Two topics and 8 lessons follow (revisão, kanji do exame). |
| C5 | `les:n4-aspecto-02` | "Na lição passada você marcou **começos e fins** de ação." | `les:n4-aspecto-01` covers only beginnings (〜始める, 〜出す, 〜てくる). Ends arrive in lesson 03, whose own opening correctly says "Você já viu o começo e o meio". |
| C6 | `les:n4-revisao-03` | Body and checklist: "conectores como それで, **そのため**, **ところで** e 〜ように" | Neither そのため nor ところで appears in the n4 cumulative known set (grammar or vocab) at this, the final review lesson. The review asks the learner to tick a box for two connectors the course never taught. |
| C7 | `les:n4-conectores-06` | Checklist: "Diferencio essa concessão … do contraste entre frases inteiras (**でも/しかし**)." | The preceding lesson taught だが/ですが/それでも/は…は. でも and しかし are never taught. |

**Fix (C1–C5, C7):** correct the retrospective sentence to the lesson that actually precedes.
**Fix (C6):** either drop そのため/ところで from the review and checklist, or introduce them in
`topic-35-conectores` first.

---

## D. The same point taught twice as if new

| # | What | Where | Evidence |
|---|---|---|---|
| D1 | さっき | `les:n4-forma-simples-04` §"さっき: o passado bem recente" (objective: "Falar do passado recente com さっき") and again `les:n4-forma-simples-07` §"さっき: há pouco, agora há pouco" (objective: "Usar さっき para apontar um momento recente"), three lessons later in the same topic | Both use the same example 〔さっき何かあった？〕. L04 registers it as vocab (`vocab:1005180` 先/さっき), L07 as grammar (`gram:sakki`). |
| D2 | はず | `les:n4-transitividade-05` §"はず: 'deve ser / é de se esperar'" with objective "Dizer 'deve ser'… com はず" and two worked examples; then `les:n4-suposicao-08` introduces `gram:hazu-da` as new | Topic 26 teaches the pattern in prose; topic 31 unlocks it. |
| D3 | ように (finalidade) | `les:n4-oracoes-relativas-07` §"ように: para que / de modo que (finalidade)"; then `les:n4-conectores-07` §"ように: finalidade e desejo" unlocks `gram:gp-128` | Both derive it from scratch; topic 22 already used 落ちないように. |
| D4 | 6 kanji re-taught | 転 (`experiencia-01`→`-02`), 力 (`oracoes-relativas-01`→`condicionais-01`), 私 (`transitividade-01`→`-03`), 考 (`volitivo-01`→`-02`), 員 (`forma-simples-01`→`volitivo-04`), 重 (`volitivo-03`→`volitivo-06`) | Near-identical mnemonics. 力: "É um braço dobrado, mostrando o músculo" → "imagine um braço dobrado mostrando o músculo". 私: "espiga de arroz (禾) e à direita um gancho que recolhe para si" → "radical de espiga de arroz (禾); à direita, um gancho". 重: "fardos empilhados num eixo" → "caixas empilhadas… espremidas por um eixo no meio". |

**Fix:** keep the first occurrence as the teaching pass and turn the second into an explicit callback
("você já viu X em …"), or merge them.

---

## E. Headings that do not match their own content

### E1. "N kanji" claims that contradict the lesson's new-kanji set (10 lessons)
| Lesson | Heading / lead text | New kanji actually unlocked |
|---|---|---|
| `les:n4-forma-simples-03` | "**Dois kanji novos**" (地 + 新) | 1 — 新 was already known |
| `les:n4-potencial-03` | "**Três kanji** que aparecem em palavras de paisagem" (野, 多, 安) | 1 — 多, 安 already known |
| `les:n4-transitividade-03` | "**Dois kanji entram aqui**" (私, 死) | 1 — 私 taught in `transitividade-01` |
| `les:n4-dar-receber-01` | "**Quatro kanji de hoje**" (真, 少, 口, 町) | 2 — 少, 口 already known |
| `les:n4-experiencia-01` | "**Seis kanji** que aparecem em palavras de mudança" | 4 — 足, 店 already known |
| `les:n4-aspecto-02` | "**Dois kanji** ligados a rotina" (歌, 週) | 1 — 週 already known |
| `les:n4-suposicao-02` | "**Três kanji** ligados à natureza" (春, 秋, 花) | 2 — 花 already known |
| `les:n4-passiva-02` | "**Quatro kanji desta vez**" (習, 堂, 肉, 飲) | 3 — 飲 already known |
| `les:n4-causativa-03` | "**Quatro kanji novos**" (冬, 昼, 魚, 犬) | 3 — 魚 already known |
| `les:n4-forma-simples-01` | "**Kanji do dia: 会, 員, 者, 方**" | 3 — 会 already known; the lesson's own summary line reads "kanji [員 方 者]" |

### E2. Two lessons have a kanji section and **zero** kanji unlocks
- `les:n4-volitivo-06` — "### Kanji da lição: 重", a full mnemonic paragraph for 重, which was unlocked
  in `les:n4-volitivo-03`.
- `les:n4-aspecto-06` — "### Kanji da lição" teaching 古 and 買, both already known.

**Fix for E1/E2:** state the count from the unlocks, and put review kanji under a different label
("Reencontrando 少 e 口") so "novo" keeps meaning something.

### E3. Section framing that does not describe the list under it
- `les:n4-obrigacao-05`: "palavras variadas que combinam com a ideia de **dispensa e de quantidade**"
  → list is ハンバーグ, レジ, 講堂, 吃驚, and **侯 (こう, "marquês")**.
- `les:n4-passiva-04`: "Os substantivos de hoje trazem contextos de **saúde, transporte e eventos**"
  → list includes 数学 (matemática), 億 (cem milhões), 沖 (alto-mar), 滑降 (descida no esqui).
- `les:n4-conectores-03`: "Itens que já cabem nas suas **listas de exemplos**" → includes 掏摸 (すり,
  "batedor de carteiras") and 家内 (かない, "minha esposa", a dated term worth a register note at least).
- `les:n4-keigo-06`: "### Fechando o vocabulário do tópico" → a single unrelated adjective, 憎い
  ("odioso"), closing the keigo topic.

**Fix:** either re-frame the heading to what the list is ("Mais vocabulário do nível"), or move the
off-theme items to a lesson where they fit.

### E4. `les:n4-forma-simples-03` — the same chip presented as two different patterns
**Current:** the general pattern is introduced as `<grammar ref="gram:gp-118"/>` and then the numeric
use as *"isso é tão comum que tem até um nome próprio, `<grammar ref="gram:gp-100"/>`"*. Both records'
`forms[0].form` is **しかない**, so the learner reads "tem até um nome próprio, **しかない**" — the same
string they saw two sections earlier.
**Fix:** name the second pattern in the prose ("[quantidade] + しか〜ない") instead of leaning on a chip
that prints the same text, and consider merging the two records (same identity class as the
grammar_identity_merges queue).

---

## F. Meta-text about the app inside learner prose (12 lessons)

The body tells the learner about the UI rather than about Japanese:

| Lesson | Text |
|---|---|
| `les:n4-condicionais-04` | "Guarde estas palavras (**cada chip já mostra a leitura em kana**):" |
| `les:n4-condicionais-07` | "A leitura em kana **já aparece na própria ficha de cada palavra**:" |
| `les:n4-potencial-02` | "**O vocabulário já mostra a leitura em kana**; aqui vai o significado de cada palavra." |
| `les:n4-experiencia-02` | "A leitura em kana **aparece no próprio cartão de cada palavra**." |
| `les:n4-aspecto-05` | "junte estas palavras (**a leitura em kana já aparece no próprio cartão**):" |
| `les:n4-suposicao-04` | "**O chip de cada palavra já mostra a leitura em kana**, então foque no sentido:" |
| `les:n4-passiva-03` | "**O som em kana já aparece no próprio cartão de cada palavra**; aqui damos o sentido em português." |
| `les:n4-keigo-04` | "Estas palavras ajudam a montar cenas reais (**lembre que a leitura já vem na própria palavra**):" |
| `les:n4-keigo-05` | "Mais vocabulário … (**a leitura já vem na própria palavra**)." |
| `les:n4-kanji-exame-01…05` | "…na página de cada kanji (**toque no kanji para abrir**)" — and `-05` adds "**toque para ver leituras e exemplos**" |

Three separate problems: it names implementation ("chip", "ficha", "cartão"); it assumes a touch
device ("toque"); and `les:n4-kanji-exame-05` goes further and comments on the corpus itself —
"Palavra extra deste tópico, **fora da lista básica do N4**" — which tells the learner the item is
filler.
**Fix:** delete these clauses. The lists work without them.

---

## G. Structure: material after the practice block, and broken outlines

| # | Finding | Count / lessons |
|---|---|---|
| G1 | A "### Mais exemplos" section with **new** example sentences placed **after** "Hora de praticar" — the learner meets the sentence only after answering the exercises, breaking concept → example → practice | **24 lessons**: `condicionais-01, -03`, `potencial-01, -02, -04`, `volitivo-05`, `obrigacao-01…-05`, `suposicao-01, -02, -03, -05, -06`, `passiva-02`, `causativa-01, -02, -03`, `keigo-02, -03, -04, -06` (plus `passiva-03` and `suposicao-07`, which have the same section but no practice heading at all — see G3) |
| G2 | An orphan "### Mais um item para o seu repertório" after the exercises: a single bullet with no example and no practice | 4 lessons — `condicionais-08` (〔の次に〕), `obrigacao-05` (〔市〕), `aspecto-06` (〔そろそろ〕), `keigo-04` (〔参る〕). `obrigacao-05`'s bullet re-lists **市**, already taught as a kanji in `obrigacao-01` of the same topic |
| G3 | Exercises emitted with **no** practice heading at all — they follow straight on from a content section | 3 lessons — `volitivo-07`, `suposicao-07`, `passiva-04` |
| G4 | Sub-sections written at `level="2"`, so they sit as siblings of the lesson title while every other lesson uses `level="3"` — the outline (and the in-page nav) breaks | 5 lessons — `forma-simples-06` (4 headings), `volitivo-06` ("Pratique"), `aspecto-04` (6), `aspecto-07` (3), `passiva-04` (3) |
| G5 | The practice heading is inconsistent across the level: "Hora de praticar" (85), "Pratique" (2 — `volitivo-06`, `aspecto-07`), "Praticando" (1 — `forma-simples-06`), none (3 — see G3) | 3 lessons off-pattern |

**Fix:** move "Mais exemplos" above "Hora de praticar" (or fold the sentence into the section it
illustrates); fold the orphan bullets into the relevant vocabulary section; normalise heading levels
and the practice-heading wording.

---

## H. Register, clarity and AI-tells (`design/translation_style.md` §4)

### H1. Japanese vocab chips used as Portuguese content words — 48 occurrences, 25 lessons
Because a `<vocab>` chip prints the record's **kana**, sentences built this way come out as
Portuguese with kana dropped in where a Portuguese noun belongs. Representative (24 lessons carry at least one):
- `les:n4-transitividade-04`: "Vamos passar por um **もり**, descer até o **かいがん**, dormir num
  **りょかん** e pegar um **のりもの**."
- `les:n4-dar-receber-02`: "o **てんいん** me deu o **おつり**"; "recebi ajuda do amigo para **ひっこす**"
  (a verb chip standing in for a Portuguese verb).
- `les:n4-obrigacao-01`: "preciso de **サンダル**", "preciso de **でんとう**", "preciso de **したぎ**".
- `les:n4-aspecto-06`: "Os **しみん** só falam de **せいじ**"; "As regras de **ゆにゅう** enfim foram definidas".
- `les:n4-suposicao-05`: "**わらう** com cara de feliz".

For a beginner this is unreadable in both languages, and it hides the written form the lesson is
supposed to be teaching. Full list reproducible with the scan in the count table below.
**Fix:** write the Portuguese word in the sentence and put the Japanese beside it in parentheses
(`dormir numa pousada tradicional (旅館)`), instead of substituting the chip for the noun.

### H2. `les:n4-obrigacao-04` — a tip that contradicts itself, then illustrates itself with a fourth word
**Current (`tip`):** "Para organizar a fala, alguns advérbios caem muito bem aqui: まず / **ぜひ** / とくに"
— and the ぜひ bullet immediately says *"Combina com vontade e convite … **não com obrigação**."* in a
lesson whose entire subject is obligation. The note then closes:
`Por exemplo: <jp reading="かならずあしたまでにやらないと">必ずあしたまでにやらないと</jp> ("preciso fazer até amanhã sem falta").`
The example uses **必ず**, which is none of the three adverbs just listed.
**Fix:** drop ぜひ from the list and change the example to まず or 必ず→ add 必ず to the list.

### H3. `les:n4-potencial-02` — a `warning` that invents a confusion
**Current:** `Não confunda <jp>世界</jp> ("mundo", せかい) com <jp>線</jp> ("linha", せん) … E <jp>戦争</jp> ("guerra", せんそう) começa igual a <jp>線</jp>, mas é outra palavra.`
Nothing about 世界 / 線 / 戦争 is confusable: different kanji, different lengths, different meanings.
Sharing an initial mora is not a pitfall, and the note manufactures one. It is also the only
`warning` in the lesson, so it occupies the slot a real caution would use.
**Fix:** delete, or replace with a real trap from the same set (e.g. 世界 せかい vs 世紀 せいき).

### H4. `les:n4-causativa-02` — an example that admits it is not the lesson's pattern
**Current (`example` note):** `<jp reading="けんきゅうしつをみせてください">研究室を見せてください</jp> seria "mostre-me o <vocab .../>" (aqui o pedido é com <jp>見せて</jp>, **mas observe como o vocabulário de lugares entra nesses contextos formais**).`
In a lesson about させてください, the "useful situations" note offers a sentence that is 見せてください and
flags in its own parenthesis that it does not use the pattern. It exists only to place a vocab word.
**Fix:** `研究室を見せていただけませんか` is not this lesson either — use the pattern:
`研究室を見学させてください` ("deixe-me visitar o laboratório").

### H5. `les:n4-volitivo-06` — an authoring aside left in the learner text
**Current:** `Até agora você sugeriu ("vamos!"), contou intenções ("pretendo...") e pediu com jeitinho (<grammar ref="gram:nasai"/> ainda não, calma).`
Renders as "…pediu com jeitinho (**なさい ainda não, calma**)." — a note-to-self about pacing, addressed
to nobody, in the opening paragraph.
**Fix:** "…e pediu com jeitinho com 〜てください."

### H6. `les:n4-volitivo-07` — announces two items and names one
**Current:** `…e dois usos mais avançados,<grammar ref="gram:gp-83"/>, que cobrem recusa firme (〜まい) e comparação (〜のように).`
Renders as "…e dois usos mais avançados, **〜まい**, que cobrem recusa firme (〜まい) e comparação
(〜のように)." — the second item has no reference of its own, and 〜まい is repeated immediately.
`〜のように` is also not among this lesson's unlocks (it belongs to `suposicao-04`).
**Fix:** "…e dois usos mais avançados: 〜まい (recusa firme) e 〜のように (comparação)."

### H7. `les:n4-potencial-02` — a vocabulary non-sequitur mid-explanation
**Current:** after explaining 私はやっと休むことができる — `O <vocab ref="vocab:1382370"/> ("antigamente") você encontra na lista de vocabulário desta lição.`
昔 has nothing to do with the sentence being explained; the clause exists to name a vocab item.
**Fix:** delete; 昔 is already in the vocabulary list below.

---

## I. Two topics whose lessons leave the topic

### I1. `topic-26-transitividade` — 3 of 5 lessons have no connection to transitivity
Lessons 03 ("Pessoas, papéis e ocasiões sociais"), 04 ("Viagem, lugares e transporte") and 05
("Planos, trabalho e expressões de certeza") unlock **zero grammar** between them and teach social
vocabulary, travel vocabulary and はず. None of their objectives mentions 他動詞/自動詞. The topic's own
`unlocks_summary` shows `grammar: 2` across five lessons. Lesson 04's single attempt to bridge is the
category error in **B3** above; lesson 05 introduces はず, later re-introduced in `suposicao-08` (**D2**).

### I2. `topic-32-passiva` — 2 of 4 lessons are about negation adverbs
Lessons 03 ("Advérbios de negação: あまり, ぜんぜん, 全然") and 04 ("Negação enfática e litotes: すこしも,
すくなくない, 〜ない〜はない") have nothing to do with the passive voice; neither body mentions 受身 after the
first two lessons.

**Fix (I1/I2):** this is a sequencing decision for the teacher, not a text edit — either rename the
topics to what they contain, or move the off-topic lessons into the vocabulary/negation topics they
belong to. Flagged here because the mismatch is visible in the prose (each lesson opens with "Na
lição anterior você viu…" and then cannot connect).

---

## J. Typography

`les:n4-revisao-01`, `-02`, `-03` — all three titles use a semicolon where the rest of the level uses
a colon: "Revisão N4**;** Forma simples, orações relativas e condicionais". The body H2 of `-02` and
`-03` uses a colon, so the two disagree on the same page.
**Fix:** `Revisão N4: …`.

---

## Count table

| Class | Checked | Flagged |
|---|---|---|
| Lesson bodies read in full | 96 | — |
| **A. Renders wrong / contradicts its own gloss** | | |
| A1 split sentences losing their negation (`passiva-03`) | 96 lessons scanned | **6 spans, 1 lesson** |
| A2 unsupported `<ruby>` element | 96 | **1** |
| A3 unsupported `<stroke>` element (whole body invisible, no exercises, no reading) | 96 | **5 lessons / 40 elements** |
| A4–A5 chip that defeats its own sentence | 96 | **2** |
| A6 malformed grammar-chip forms surfacing in prose | 315 chip uses / 205 distinct refs | **15 chips / 12 lessons** |
| A7 katakana surface with hiragana furigana | 1,534 `<jp reading>` spans | **5** |
| A8 furigana reading containing a space | 1,534 | **1** (+3 full-sentence spans, benign) |
| A9 redundant ruby / doubled kana | 3,504 `<jp>` spans + all vocab chips | **215** (174 + 41) |
| **B. Factual errors in explanation** | 96 | **6** |
| **C. Cross-lesson sequencing contradictions** | 96 | **7** |
| **D. Taught twice as new** | 96 | **3 grammar/vocab + 6 kanji** |
| **E. Heading ≠ content** | | |
| E1 kanji count claims | 24 kanji sections with counts | **10** |
| E2 kanji section with zero kanji unlocks | 96 | **2** |
| E3 vocabulary framing ≠ list | 96 | **4** |
| E4 same chip sold as two patterns | 96 | **1** |
| **F. App meta-text in learner prose** | 96 | **12 lessons / 14 clauses** |
| **G. Structure** | | |
| G1 new examples after the exercises | 96 | **24** |
| G2 orphan bullet after the exercises | 96 | **4** |
| G3 exercises with no practice heading | 96 | **3** |
| G4 level-2 sub-headings breaking the outline | 96 | **5** |
| G5 practice-heading wording off-pattern | 96 | **3** |
| **H. Register / clarity / AI-tells** | | |
| H1 vocab chip used as the pt-BR content word | 96 | **48 occurrences / 24 lessons** |
| H2–H7 individual prose defects | 96 | **6** |
| **I. Topic drift** | 17 topics | **2 topics / 5 lessons** |
| **J. Typography** | 96 titles | **3** |
| **Total distinct findings** | | **~117 occurrences across 24 classes; 60 of the 96 lessons touched** |

## Checked and clean

The following were scanned across all 96 bodies and produced **no** findings, which is worth recording
as a positive result:

- **pt-PT leakage** — no "comboio / autocarro / telemóvel / ecrã"; "você", "celular", "ônibus", "trem"
  used throughout.
- **The em dash (—)** — zero occurrences in authored body text (style rule §4 holds).
- **"Vale ressaltar / Vale destacar / Por assim dizer / Quanto a mim"** — zero occurrences.
- **Glued words across adjacent text nodes** — zero (`X</text><text…>Y` never joins two letters).
- **Readings containing kanji or Latin characters** — zero.
- **Empty `<text></text>` nodes and stray double spaces** — zero.
- **Kanji taught in a body but never unlocked anywhere** — zero (every "extra" kanji in E1/E2 was
  already in the cumulative known set; nothing is taught off-graph).
- **Title vs. body H2 divergence (17 lessons)** — deliberately **not** flagged: `renderBody`'s
  `dedupeTitle` drops the first heading only when it matches the title, so a differing H2 is the
  designed behaviour, not a defect.

The grammar and pedagogy of the core patterns is, on the whole, accurate and well explained; the
l1-pitfall notes in particular are the strongest part of the level. Almost everything above is either
a rendering contract that the prose does not know about (A, F), a retrospective sentence that was not
updated when lessons moved (C, D), or a count/label that drifted from the unlocks (E).
