# QA sweep — lesson prose, part 3/3: every lesson body under `course/n3`

**Slice:** all 101 lesson bodies in `course/n3/topic-38-*` … `topic-52-*` (read in full, via a renderer that
resolves `<grammar>/<vocab>/<kanji>` refs the way `prototype/app/lib/render-body.server.ts` does, so the
prose was judged as a learner sees it, not as the `.md` export prints it).
**Out of scope by instruction:** sentence `structure_explanation` fields; the open items already listed in
`STATE.md` (the 14 rows of `course/vocab_disambiguation_review.json` — 上, 柄, 金, 品, 数, 得る, 注ぐ, 額,
後, 何方, 様 — were found by a reading-vs-corpus scan and are **excluded** from every count below).

**Clean results worth stating:** furigana integrity is clean — 0 defects over every `<jp reading="…">` in the
slice (no kanji or latin inside a reading; surface kana always a subsequence of the reading; no
implausibly short readings). XML tag balance is clean — 0 unclosed/stray tags in 101 bodies. Em dashes: 0.
`gp-NN` codes, `sent:`/`les:`/`top:` id leaks, `TODO`/`Retitle`/reviewer instructions in learner text: 0.

---

## A. pt-BR text defects

### A1 — Accent-stripped Portuguese across `topic-38-conectores` lessons 01–04 (systematic)

These four lessons never received the diacritic repair the rest of the tree did. 53 unambiguous stripped
tokens plus a long tail of minimal pairs (`é/e`, `está/esta`, `só/so`, `já/ja`, `dá/da`, `lá/la`) that a
mechanical fixer must not touch blind. Everything from `les:n3-conectores-05` onward is clean.

**`les:n3-conectores-01`** — unambiguous: `classico` `espontaneo` `identicos` `obvio` `mantem` `ate`
`arvore` `mutuo` `cafe` (×2) `cha` (×2) `album` `ja`. Representative lines:

> "Confundir a soma com a escolha **e** o erro **classico** do brasileiro aqui"
> → "…**é** o erro **clássico**…"

> "A imagem literal **e** boa: 上 **e** \"em cima\", então **e** como empilhar um segundo ponto por cima do primeiro."
> → "A imagem literal **é** boa: 上 **é** \"em cima\", então **é** como empilhar…"

> "\"Você vai tomar **cafe**? Ou (então) **cha**?\"" → "…**café**? Ou (então) **chá**?"

> "acrescenta mais um item ou mais uma ação a algo **ja** mencionado … Tem um tom mais falado e **espontaneo**."
> → "…algo **já** mencionado … mais falado e **espontâneo**."

> "«明らか» (あきらか) = \"claro, evidente, **obvio**\". **E** um adjetivo な." → "**óbvio**. **É** um adjetivo な."

> "cada vogal **mantem** seu som **ate** o fim … **e** \"a-i-ro-n\"" → "**mantém** … **até** … **é**"

> "O kanji 相 traz a ideia de \"**mutuo**\" … Em cima **esta** 安 … e embaixo a **arvore**"
> → "\"**mútuo**\" … Em cima **está** 安 … a **árvore**"

> checklist: "Sei que entre substantivos o \"ou\" **e** か, e entre perguntas **e** それとも."
> → "…o \"ou\" **é** か, e entre perguntas **é** それとも."

**`les:n3-conectores-02`** — `classico` `logica` `forca` `inedito` `vestigio` `superficie` `tecnico`, plus
`so`/`e`.

> "**E** a versão coloquial de しかし e だが" → "**É** a versão coloquial…"
> "Dentro de uma mesma frase, normalmente usamos **so** けど" → "**só** けど"
> "\"Este filme **e** longo, mas **e** interessante.\"" → "**é** longo, mas **é** interessante"
> "tirar uma conclusão **logica**" → "**lógica**"; "e mais **tecnico** e formal" → "**técnico**"
> "«勢い» (いきおい) = \"**forca**, vigor, energia\"" → "**força**" (as written it means *gallows*)
> "«新た» (あらた) = \"novo, **inedito**\"" → "**inédito**"; "«跡» (あと, \"**vestigio**\")" → "**vestígio**"
> "O kanji 表 significa \"**superficie**, tabela, expressar\"" → "**superfície**"
> "Esse par **e** um ponto **classico** de confusão" → "**é** um ponto **clássico**"

**`les:n3-conectores-03`** — `estomago` (×2) `medico` (×2) `Saude` `folego` `oleo` `demonio` `Otimo`
`tipico` `esqueca` `le` `demonio` `ABRACADA` `ja`, plus `é/e`, `está/esta`, `só/so`.

> h3 heading: "**なぜなら: isso porque, a razão e que**" → "a razão **é** que" (the h2 has the same problem:
> "Explicando o **porque**" while the lesson title correctly reads "Explicando o **porquê**")
> "\"**Porque** **esta** frio, vamos fechar a janela.\"" → "**Porque está** frio…"
> "não **esqueca** o から … a causa fica **ABRACADA** entre なぜなら … e から"
> → "não **esqueça** … fica **ABRAÇADA**"
> "«胃» (い, \"**estomago**\") … «医師» (いし, \"**medico**, doutor\") … \"Vou ao **medico**, porque o **estomago** doi\""
> → "**estômago** … **médico** … **dói**"
> "«息» (いき, \"respiração, **folego**\")" → "**fôlego**"; "«油» (あぶら, \"**oleo**\")" → "**óleo**"
> "«悪魔» (あくま, \"diabo, **demonio**\")" → "**demônio**"; "**Otimo** para abrir uma recusa" → "**Ótimo**"
> "não confunda com 以外 … que se **le** igual" → "se **lê** igual"
> "**So** o contexto e o kanji separam os dois" → "**Só** o contexto…"

**`les:n3-conectores-04`** — `ate` `cabeca` `pe` `desdem` (×3) `enfatico` `genero` `labios` `otimo`
`seguranca` `serie` `ve` `ja`, plus `só/so`, `lá/la`, `dá/da`.

> h3 heading: "**なんか: coisas como... ou sei la, nem ligo**" → "sei **lá**"
> h3 heading: "**Vocabulário para fechar a serie**" → "a **série**"
> "O marcador «～など» **da** uma lista … os itens citados são **so** alguns" → "**dá** uma lista … **só** alguns"
> "com tom de **desdem**" (×3) → "**desdém**"
> "\"Ele toca **ate** coisas como piano.\"" → "**até**"
> "que **e** mais exclamativo e **enfatico**" → "**é** … **enfático**"
> "Ele **ja** carrega a ideia de \"e coisas do **genero**\"" → "**já** … do **gênero**"
> "A escrita em kanji **e** rara; quase sempre se **ve** em kana" → "**é** rara … se **vê**"
> "«行けない» = \"não pode, **e** proibido, **e** ruim\"" → "**é** proibido, **é** ruim"
> "O う japonês tem **labios** neutros" → "**lábios**"
> "Aparece em 全部 … e em 安全 (\"**seguranca**\")" → "**segurança**"
> "uma pessoa em **pe** e outra de **cabeca** para baixo" → "em **pé** … de **cabeça** para baixo"
> "「最高」 (\"o melhor, **otimo**\")" → "**ótimo**"

**Fix:** re-run the diacritic pass on these four files only, with the minimal pairs decided by hand
(`e→é` wherever it is the copula, `esta→está`, `so→só`, `ja→já`, `da→dá`, `la→lá`, `porque→porquê` in the
h2 of lesson 03).

### A2 — `les:n3-estrutura-02`: a minimal-pair note whose two halves are the same string

> "Note os pares mínimos de duração: **しょう (curto) versus しょう longo** muda a palavra inteira."

The contrast is written with the identical string on both sides, so the note teaches nothing, and the list
below it (上達 じょうたつ / 状態 じょうたい / 症状 しょうじょう / 少々 しょうしょう) is exactly where the
distinction matters. **Fix:** "…**しょ (curto) versus しょう (longo)** muda a palavra inteira".

### A3 — Missing space before an opening parenthesis (3 sites)

- `les:n3-conectores-06`: "«昼食» (ちゅうしょく) - almoço, a refeição do **meio-dia(mais** formal que 昼ごはん)."
- `les:n3-estado-02`, h3: "**Vocabulário do dia(em kana)**"
- `les:n3-estado-03`, h3: "**Vocabulário do dia(em kana)**"

`les:n3-estado-01` and `les:n3-estado-04` write the same heading correctly ("Vocabulário do dia (em kana)"),
so two of the four are wrong. **Fix:** insert the space.

### A4 — Chips run together with the surrounding punctuation (`topic-42-estado`, lessons 01–04)

> `les:n3-estado-01`: "Nesta lição você junta três ferramentas para isso**:«～ている»,«～かけ»** e «～たて»."
> `les:n3-estado-02`: "Três ferramentas**:«～上げる»,«～切れない»** e «～ちゃった»."
> `les:n3-estado-03`: "Três ferramentas**:«～ないで»,«～ずに»** e «～まま»."
> `les:n3-estado-04`: "Três formas de descrever o estado das coisas**:«～っぱなし»** (deixou e largou)**,«～でいっぱい»** (cheio de)…"

Every vocabulary bullet in these four lessons has the same problem: `«価格»(「かかく」)` with no space
between the chip and the parenthesis, against the spaced form used everywhere else in n3.
**Fix:** one space after `:` and after each `,`, and one space before every `(`.

### A5 — `les:n3-desejos-03`: a vulgar Portuguese word inside a pronunciation note

> "Armadilha PT: 「くう」 tem duas vogais, duas batidas: 'ku-u', não um **'cu'** curto."

The note otherwise uses Hepburn (`ku-u`, `ku-ra-u`), then switches to Portuguese spelling for the one
syllable where that spelling is an obscenity. **Fix:** "…não um **'ku'** curto." (keep the romaji register
consistent with the rest of the note).

### A6 — `les:n3-causa-08`: broken Portuguese in the 例 reading note

> "Mas em 例えば ('por exemplo'), que você já viu, **ele lê たと-**. Mesmo kanji, leituras diferentes."

"ele lê" makes the kanji the subject of *reading*; and the trailing hyphen in `たと-` is a dictionary
convention the learner has not been taught. **Fix:** "…em 例えば ('por exemplo'), que você já viu,
**lê-se たと** (例えば)."

### A7 — `les:n3-desejos-01`: a kanji called a "leitura"

> "O kanji «良» significa 'bom, agradável'. É a versão 'séria' de 「いい」: **a leitura 「良」 está dentro de
> 「よかった」**, que você vai usar muito para arrependimentos mais à frente."

良 is a kanji, not a reading, and よかった is written 良かった — the kanji is *the head of* the word, not
"inside" it. **Fix:** "…: é o 良 de **良かった**, que você vai usar muito…"

### A8 — `les:n3-concessao-02`: the くせに formation note points at the wrong item

> "A montagem é **como a do 「の」**: verbo simples + くせに, adjetivo-な + な + くせに, substantivo + の + くせに."

The pattern being echoed is 「のに」 (which the same note contrasts three lines later), not the particle の.
**Fix:** "A montagem é **a mesma de 「のに」**: …".

### A9 — `les:n3-limites-01`: a garbled pronunciation example

> "Vantagem PT: o 「そ」 de 「速度」 tem o 'o' limpo de 'avô', não levante para 'u' **como em 'sôku' que vira
> 'suku'**. Cada vogal mantém sua qualidade até o fim."

`sôku` is not a word in either language and 速度 is そくど, not そく. **Fix:** "…não levante para 'u': é
**so-ku-do**, nunca **su-ku-do**."

### A10 — `les:n3-intencao-06`: "a vogal final" when the whole mora changes

> "Não confunda ところが com ところで. ところが introduz um contraste inesperado…; ところで muda de assunto….
> **A vogal final muda tudo.**"

が → で changes consonant *and* vowel. **Fix:** "**A última sílaba muda tudo.**"

### A11 — `les:n3-concessao-04`: an unusable gloss for 氏

> "«氏» (「し」) = 'senhor/senhora' **(sobrenome formal)**."

氏 is a suffix that attaches to a surname (田中氏); "(sobrenome formal)" reads as if 氏 *were* a surname, and
"senhor/senhora" hides that it is written, not spoken. **Fix:** "«氏» (し) = sufixo formal de tratamento,
colado ao sobrenome (田中氏, 'o Sr. Tanaka'); típico de texto escrito e noticiário."

---

## B. Japanese examples that are wrong, or that do not demonstrate the point

### B1 — `les:n3-concessao-01`: the opening example of ても contains no ても

> "Você já viu o 「ても」 em formas como 「**いいですか**」 ('pode? / tudo bem se?')."

Raw: `<jp reading="いいですか">いいですか</jp>`. 「いいですか」 alone means "is it all right?" and has no ても
at all; the form the learner met at N5 is 「〜てもいいですか」. **Fix:** replace with
`<jp reading="たべてもいいですか">食べてもいいですか</jp>` (or 「〜てもいいですか」 as the pattern).

### B2 — `les:n3-intencao-03`: 空き缶 offered as an example of 空 read から

> "«空» (「から」): 'vazio, estar vazio' (**a lata vazia é 「空き缶」**)."

空き缶 is あきかん — the 空 there is 空く(あく), not から. The bullet proves the opposite of what it claims,
and the same lesson bank already has the correct example (`les:n3-conectores-05` uses 空の箱).
**Fix:** "(a caixa vazia é 「空箱」/「空の箱」, からばこ)" or 「空手」(からて).

### B3 — `les:n3-tempo-03`: 抱く glossed "abraçar" while the record it links to is いだく

> "«抱く» 'abraçar'; «至る» 'chegar a, alcançar'."

The bullet links `vocab:1584090`, whose headword is 抱く / **いだく**, corpus gloss
`"nutrir (um sentimento)", "alimentar (uma ideia, dúvida)"`. "Abraçar" is だく — a different reading and a
different record. Chip and prose contradict each other, and the block's premise is い-initial words, which
だく would break. **Fix:** "«抱く» (いだく) 'nutrir, alimentar (um sentimento, uma dúvida)'".

### B4 — `les:n3-desejos-07`: ボーイ glossed as "garoto"

> "«ボーイ» (ボーイ) - **garoto, rapaz**."

In Japanese ボーイ is a job title — waiter, bellboy — not "boy" (that is 男の子 / 少年). The corpus record for
this ref glosses it `"garçom; camareiro"`. **Fix:** "«ボーイ» - garçom, camareiro, mensageiro de hotel
(nunca 'menino': isso é 男の子)."

### B5 — `les:n3-conectores-05`: the 上=かみ example only works because the furigana forces it

> `<jp reading="このかわのかみにはちいさなむらがある">この川の上には小さな村がある</jp>`
> "(No curso superior deste rio há um vilarejo pequeno.)"

Read without furigana, a native reads 川の上 as かわのうえ ("above the river"). The whole point of the
section is that the learner should recognise 上 as かみ in the wild, and this sentence gives them no way to.
**Fix:** use the collocation that carries the reading: 「この川の**上流**には小さな村がある」 or
「**川上**には小さな村がある」.

### B6 — `les:n3-conectores-07`: the translation contradicts the gloss two lines above

> "«ハンサム» (ハンサム) - bonito, atraente, charmoso (**geralmente para homens**)."
> "「あの人は母親に似ていて、その上とてもハンサムだ」 (Aquela pessoa é parecida com a mãe e, além disso, é
> muito **bonita**.)"

The lesson states ハンサム is used of men and then renders it with a feminine adjective. **Fix:** "…é muito
**bonito**." (and consider 「あの人」 → 「彼」 so the pt gender has an anchor).

### B7 — `les:n3-causa-05`: the same sentence as `les:n3-causa-01`, respelled in a rare kanji, with no note

> `les:n3-causa-01`: 「雨のせいで試合が中止になった」 = "o jogo foi cancelado por causa da chuva"
> `les:n3-causa-05`: 「雨の**所為**で試合が中止になった」 (Por culpa da chuva, o jogo foi cancelado.)

せい is written in kana in essentially all modern prose; 所為 is an ateji a learner will not meet. Presenting
the *identical* sentence in the rare spelling four lessons later, with no cross-reference and no note that
所為 = せい, teaches a spelling the course itself does not use. **Fix:** keep 所為 as the dictionary headword
but write the example as 「雨のせいで…」 and add one line: "a grafia 所為 é rara; na prática escreve-se せい,
como você viu em ～せいで."

### B8 — `les:n3-tempo-02`: 一時 glossed "uma hora"

> "«一時» '**uma hora**'; «一度に» 'de uma vez'; «一瞬» você já viu na lição anterior."

一時 (いちじ) is "one o'clock" or "temporarily / for a while"; "uma hora" in pt-BR reads first as a
*duration*, which is 一時間. **Fix:** "«一時» 'uma hora (o horário, 1h)' e, como advérbio, 'por um tempo,
temporariamente'".

### B9 — `les:n3-intencao-06`: 得意 leads with its secondary sense

> "«得意» (とくい) - **orgulho, satisfação**; também \"ser bom em algo\"."

The dominant modern use is "one's forte / good at"; the corpus record for this ref leads
`"bom em; habilidoso; forte (em algo)"` and only then `"orgulhoso; triunfante"`. Leading with "orgulho"
inverts the priority a learner needs. **Fix:** "«得意» - ser bom em, ter facilidade com (数学が得意だ); também
'orgulhoso, satisfeito consigo' e 'cliente habitual' (お得意さん)."

### B10 — `les:n3-perspectiva-01`: an example sentence that means nothing in either language

> "[Exemplo] Junte tema e contexto: 「**この映画について会議で訴える**」 (**apelar sobre este filme na reunião**);
> 「宇宙に関する本」 (livro a respeito do universo)."

訴える is "to sue / to appeal to (someone's emotions) / to complain of (pain)"; it does not take an
について topic this way, and the Portuguese "apelar sobre este filme na reunião" is not a sentence a
Brazilian would produce. The second half of the note is fine. **Fix:** replace the first clause with a real
collocation, e.g. 「この映画について会議で話し合う」 ("discutir este filme na reunião").

### B11 — `les:n3-limites-06`: an example that uses untaught grammar and does not cohere

> "「悩むくらいなら怠けない方がいい」 (Se é para ficar remoendo, melhor não enrolar.)"

The lesson opener says the examples reuse "～しかない … e ～くらい (a ponto de)". くらいなら is a distinct N3
point (comparative "rather than…") that this topic never teaches, and the logic does not close: "rather
than agonising, better not to slack off" does not follow from anything. **Fix:** rebuild on the くらい the
lesson actually taught, e.g. 「泣きたいくらい悩んだ」 ("me atormentei a ponto de querer chorar").

### B12 — `les:n3-deveres-05`: an example of ことだ that contradicts the definition given in `les:n3-deveres-02`

> `les:n3-deveres-02`: "É um conselho impessoal e genérico … 「ことだ」 tem um quê de '**a regra de ouro é…**'."
> `les:n3-deveres-05`: 「土曜日にドライブに行く**ことだ**」 (O ideal é ir dar uma volta de carro no sábado.)

A one-off weekend plan is exactly the case the earlier lesson excludes. **Fix:** use a general precept, e.g.
「疲れた時は早く寝ることだ」 ("quando estiver cansado, o melhor é dormir cedo") — and keep ドライブ in a
plain example.

### B13 — `les:n3-conjectura-06`: unnatural pt-BR and a comparison that does not hold

> "「彼女はまるでモデルのように背が伸びた」 (Ela **cresceu de altura** como se fosse uma modelo.)"

"cresceu de altura" is not pt-BR (背が伸びた = "ficou mais alta"), and まるで invites a *figurative* image;
"grew as if she were a model" compares a process to a profession. **Fix:** 「彼女はまるでモデルのように背が高い」
→ "Ela é alta feito uma modelo."

### B14 — `les:n3-tempo-05`: stilted pt and an unmotivated contrast

> "「彼は身長が高いが性格は慎重だ」 (**Ele tem estatura alta**, mas tem temperamento cauteloso.)"

"ter estatura alta" is bureaucratese for "ser alto"; and the が is adversative while being tall and being
cautious are not in tension, so the sentence models a contrast the learner cannot feel. **Fix:**
「彼は身長が高いが性格は慎重だ」 → 「彼は明るいが性格は慎重だ」 = "Ele é alegre, mas de temperamento cauteloso."

### B15 — `les:n3-causa-01`: 助かりました rendered as a reflexive

> "「あなたのおかげで助かりました」 significa \"graças a você, **me salvei**\"."

助かりました here is the fixed thanks formula ("that was a huge help"), not a reflexive escape.
`design/translation_style.md` §1 puts the mirror in `translation_literal`, never in the natural rendering.
**Fix:** "\"graças a você, **me ajudou muito** / **você me salvou**\"."

### B16 — `les:n3-causa-07`: a construction Brazilians do not use

> "「子供が無事に帰ってきたおかげで、安心した」 (**Graças a meu filho ter voltado em segurança**, fiquei aliviado.)"

Two problems: "Graças a [alguém] ter [feito]" is not natural pt-BR, and 子供 is generic ("a criança"), so
"meu filho" adds a possessive the Japanese does not have. **Fix:** "**Fiquei aliviado porque a criança
voltou bem.**"

### B17 — `les:n3-conectores-06`: いい調子？ presented as the colloquial "Como vai?"

> "'Como vai?' coloquial em japonês é **いい調子？** (está em bom ritmo?)."

「いい調子」 is a statement of state ("going well"); the colloquial greeting built on 調子 is 「調子はどう？」 /
「調子どう？」. **Fix:** "'Como vai?' coloquial em japonês é 「**調子はどう？**」 — e 「いい調子だね」 é a
resposta ('tá indo bem')."

---

## C. Structural defects a learner sees on the page

### C1 — `les:n3-deveres-02`: a vocabulary bullet with no headword at all

Raw: `<item><text> (</text><jp>きじゅん</jp><text>) = 'critério, padrão de referência'.</text></item>`
There is no `<vocab ref>` — the item renders as:

> "- **(きじゅん)** = 'critério, padrão de referência'."

The word 基準 never appears. Every other bullet in the same list carries its chip. **Fix:** restore
`<vocab ref="…"/>` for 基準 before the parenthesis.

### C2 — `les:n3-deveres-03`: a kanji paragraph with no kanji

Raw: `<p><text>O kanji </text><text> ('comércio, negociar') aparece em …` — renders as:

> "O kanji **(**'comércio, negociar'**)** aparece em 商人 ('comerciante') e 商品 ('mercadoria'). Pense numa
> boca (口) que pechincha embaixo da barraca."

The `<kanji ref>` for 商 was dropped. **Fix:** restore the chip. (See also **D3** — this paragraph is a
near-duplicate of one in `les:n3-deveres-04`, which *does* carry the chip.)

### C3 — `les:n3-desejos-03`: a second dropped headword

Raw: `…= 'comer' (informal, masculino). </text><text> (</text><jp>くらう</jp><text>) = 'devorar, levar (uma
porrada)'.` — renders as:

> "«食う» (くう) = 'comer' (informal, masculino).  **(くらう)** = 'devorar, levar (uma porrada)'."

食らう is missing. **Fix:** restore the `<vocab ref>` (and remove the resulting double space).

### C4 — Vocabulary bullets render as "kana (kana)" — the kanji headword never reaches the page

`chip("vocab", …)` sets `text = v?.kana || id`, so `<vocab ref>` renders the **kana**. The n3 bodies were
written assuming it renders the **headword**, and then repeat the same kana in a parenthesis:

| written | rendered by the app |
|---|---|
| `«愛» (「あい」) = "amor, afeto"` (`les:n3-conectores-01`) | **あい (あい) = "amor, afeto"** |
| `«昼食» (ちゅうしょく) - almoço…` (`les:n3-conectores-06`) | **ちゅうしょく (ちゅうしょく) - almoço…** |
| `«クラシック» (クラシック) - música clássica` (`les:n3-conectores-05`) | **クラシック (クラシック) - música clássica** |
| `«通過» (つうか) - passagem…` (`les:n3-conectores-06`) | **つうか (つうか) - passagem…** |

**1,396 occurrences across 88 of the 101 n3 lessons.** It is heavily n3-specific — the same scan finds 108
in n5 (23/84 lessons) and 117 in n4 (23/96). The cost is not cosmetic: `les:n3-conectores-06`'s objective is
"Distinguir os compostos com 通 (通過, 通学, 通行, 通信)" and, as rendered, not one of those four kanji
compounds appears in the list the learner studies — only in the h3 above it.

**Fix (two viable, pick one and apply consistently):** either drop the redundant parenthesis and have
`chip("vocab")` render `v.headword` with the kana as its tooltip/reading (matches what the `.md` export
already prints, and what these bodies were authored for); or keep the kana chip and change the parenthesis
to the kanji headword. This one needs a decision before it is edited, since it touches 88 files.

### C5 — `topic-39-tempo` lessons 01–04: one sentence split across three block elements (18 sites)

Raw pattern: `</p><jp …>…</jp><p><text> …`. Example from `les:n3-tempo-01`:

> **Armadilha PT.** A forma negativa
> 雨が降らないうちに
> ` traduz-se por 'antes que comece a chover', e não 'enquanto não chove'.`

The `<p>` closes before the `<jp>` and a new `<p>` opens after it, so a single sentence becomes three
stacked blocks, the third beginning with a leading space and a lowercase letter. Counts: `les:n3-tempo-01` 6,
`les:n3-tempo-02` 4, `les:n3-tempo-03` 2, `les:n3-tempo-04` 6. Nowhere else in n3.
**Fix:** move the `<jp>` inside the surrounding `<p>` (every other n3 lesson already does this).

### C6 — `topic-39-tempo` lessons 01–04: the sentence bank lands *inside* "Hora de praticar"

`les:n3-tempo-01` body order: `## Hora de praticar` → intro paragraph → 5 `<exercise>` → **2 `<sentence>`
cards** → `### Leitura`. The two dissected bank sentences sit after the exercises, under a heading that
promises practice, with no lead-in. Every lesson in `topic-38`, `topic-40`, `topic-41`, `topic-42` puts them
under their own `### Exemplos do banco` heading *before* practice. Same defect in tempo-02, tempo-03,
tempo-04. **Fix:** move the `<sentence>` refs under an `### Exemplos do banco` heading placed before
"Hora de praticar", matching the rest of n3.

Related, same four lessons: "Palavras novas", "Kanji do bloco" and "Hora de praticar" are `<heading level="2">`
while their sibling "Leitura" is `level="3"` — the only place in n3 where the section levels disagree
within one lesson.

### C7 — 43 notes repeat their own rendered label (35 lessons)

`render-body.server.ts` prints the note head from its `type`: `l1-pitfall` → **"Cuidado"**, `tip` → **"Dica"**,
`warning` → **"Atenção"**, `culture` → **"Cultura"**, `l1-advantage` → **"Vantagem para você"**. 43 note
bodies then open with that same word:

> **Cuidado** · "**Cuidado:** 優秀 (ゆうしゅう, excelente) e 優勝…" (`les:n3-conectores-08`)
> **Dica** · "**Dica:** つまり serve tanto para resumir…" (`les:n3-conectores-02`)
> **Cultura** · "**Cultura.** Ao começar a comer, diz-se 頂きます…" (`les:n3-tempo-04`)
> **Vantagem para você** · "**Vantagem PT:** ずに e ないで são intercambiáveis…" (`les:n3-estado-03`)

Affected: conectores-02/03/06/08, tempo-02/03/04/06/07/08, perspectiva-05/06/07, causa-08, estado-03/06/08,
deveres-04, desejos-01, limites-01/03/07, enfase-03/04, concessao-03/06, conjectura-02, relato-03/05/06,
estrutura-01/04/05/06, revisao-01. (n5 has 21, n4 has 9 — so this is disproportionately an n3 habit.)
**Fix:** delete the leading label word from the note body; the component already supplies it.

### C8 — `culture` notes whose content is not cultural (3 sites)

- `les:n3-deveres-01`: "**Cultura** — Repare como vários destes kanji compartilham o radical da pessoa 「イ」
  à esquerda (働, 伝): é uma pista de que o significado envolve gente." → this is a `tip`.
- `les:n3-deveres-03`: "**Cultura** — Veja como 観 e 察 se unem em 観察 ('observação'): 'ver' mais 'deduzir'
  é justamente observar com atenção." → `tip`.
- `les:n3-conjectura-04`: "**Cultura** — O 君 (きみ) é um 'você' informal… Como o japonês é pró-drop, evite
  encher a frase de 君 ou あなた…" → the pro-drop half is a usage `tip`, not a culture note.

**Fix:** change `type="culture"` to `type="tip"` on these three.

---

## D. Content duplicated, or promised and not delivered

### D1 — Two pairs of lessons share the same title; one pair also shares the same h2

| title | lessons |
|---|---|
| **"Relato, citação e definição"** | `les:n3-relato-05` **and** `les:n3-relato-06` — and both open with the identical `<heading level="2">Relato, citação e definição</heading>` |
| **"Nominalização, explicação e voz passiva"** | `les:n3-estrutura-04` **and** `les:n3-estrutura-05` |

Two consecutive entries in the same topic list are indistinguishable to a learner. The bodies are
different: relato-05 is a 地/単 vocabulary block, relato-06 is a は-line block; estrutura-04 is 地球/知識/中学,
estrutura-05 is 発見/発達/離す. **Fix:** retitle to the actual content, e.g. relato-06 →
"Pessoas, ações e objetos: vocabulário da linha は"; estrutura-04 → "Lugar, conhecimento e rotina"; and
estrutura-05 already has the right h2 ("Descoberta, crescimento e divulgação") — promote it to the title.

### D2 — `les:n3-intencao-05`: the same sentence twice, eight lines apart

Section lead-in, immediately under `### Responsabilidade e julgamento`:

> "Quem foge da 責任 acaba sendo culpado (責められる) por todos."

and the closing line of the `l1-pitfall` note in the same section:

> "…enquanto 責める é um verbo (você 'culpa' alguém). **Quem foge da 責任 acaba sendo culpado (責められる) por
> todos.**"

Verbatim. The lead-in also uses 責任 and 責められる before the bullets that introduce them.
**Fix:** delete the lead-in paragraph (the note is the better home for the line) and let the bullets open
the section.

### D3 — `les:n3-deveres-03` / `les:n3-deveres-04`: the same 商 paragraph, twice

> deveres-03: "O kanji [chip missing] ('comércio, negociar') aparece em 商人 ('comerciante') e 商品
> ('mercadoria'). **Pense numa boca (口) que pechincha embaixo da barraca.**"
> deveres-04: "O kanji «商» ('comércio, negociar, comerciante') aparece em 商人 ('comerciante') e 商品
> ('mercadoria'). **Imagine uma boca que pechincha embaixo da barraca da feira.**"

Same kanji, same two compounds, same mnemonic, adjacent lessons — and the first copy is the one missing its
chip (**C2**). **Fix:** keep the deveres-04 paragraph, remove it from deveres-03.

### D4 — Eight grammar points taught in full, then re-taught as a vocabulary bullet

Each of these had a dedicated h3 section (or, in one case, an entire lesson) and later reappears as a plain
vocabulary line with no back-reference, as if new:

| point | taught as grammar in | re-taught as vocab in |
|---|---|---|
| ですから | `les:n3-conectores-03` (own h3 + 2 notes) | `les:n3-causa-06` — "«ですから» - portanto, por isso (versão polida de だから)" + its own l1-pitfall |
| ところで | `les:n3-conectores-02` (own h3 + l1-pitfall) | `les:n3-intencao-06` — "«所で» (ところで) - a propósito, mudando de assunto" |
| なぜなら | `les:n3-conectores-03` (own h3 + l1-pitfall) | `les:n3-limites-06` — "«何故なら» (なぜなら) - porque, a razão é que" |
| それとも | `les:n3-conectores-01` (own h3 + l1-pitfall) | `les:n3-desejos-05` — "«其れとも» (それとも) - ou, ou então", with a near-copy of the original example (conectores-01 「コーヒーを飲む？それとも紅茶を飲む？」 vs desejos-05 「コーヒーにする？それとも紅茶にする？」) |
| だけど | `les:n3-conectores-02` (own h3) | `les:n3-concessao-05` — "«だけど» - mas, porém, só que (bem coloquial)" |
| 最中に | `les:n3-tempo-01` (own h3 + formation) | `les:n3-concessao-03` — "«最中» (さいちゅう) = 'no auge de, em pleno'" |
| たとえ〜ても | `les:n3-concessao-01` (own h3) | `les:n3-concessao-05` — "«仮令» (たとえ) - mesmo que, ainda que, por mais que" |
| **めったに〜ない** | **an entire lesson**, `les:n3-enfase-04` | `les:n3-conjectura-07` — "«滅多に» (めったに) - raramente, quase nunca (sempre com verbo negativo)" **plus a pitfall note that restates the whole lesson**: "滅多に só funciona com verbo negativo: 滅多に行かない… Não diga 滅多に行く." |

**Fix:** in each vocabulary bullet, replace the standalone explanation with a one-line back-reference
("você já viu em [lição]") so the learner is not asked to learn the same point twice; or drop the bullet.

### D5 — Four near-identical boilerplate notes about mnemonics and spaced repetition

> `les:n3-intencao-01`: "Os mnemônicos acima são só uma rampa de entrada. Você fixa de verdade revendo esses
> kanji nas próximas lições e nos exercícios espaçados, não relendo a explicação."
> `les:n3-relato-01`: "Os mnemônicos acima são só uma rampa de entrada. Você vai fixar de verdade revendo
> esses kanji nas próximas lições e nos exercícios espaçados, não relendo a explicação."
> `les:n3-relato-02`: "Os mnemônicos são só a porta de entrada. A fixação real vem de reencontrar esses
> kanji nos exercícios e nas próximas lições, em intervalos crescentes."
> `les:n3-relato-04`: "São muitos kanji de uma vez, então não tente decorar todos agora. Eles vão voltar nos
> exercícios e nas revisões espaçadas das próximas lições; o reconhecimento se consolida na repetição, não
> na primeira leitura."

Four statements of the same study advice, two of them word-for-word. **Fix:** keep one (the first time it
appears) and delete the other three.

### D6 — 七転び八起き used as a culture note twice

> `les:n3-enfase-04`: "Um provérbio (諺) famoso usa essa ideia de raridade ao contrário: 「七転び八起き」,
> '**sete quedas, oito vezes de pé**', ou seja, não desista nunca."
> `les:n3-concessao-01`: "A persistência apesar das dificuldades … resumido no ditado 「七転び八起き」
> ('**caiu sete vezes, levanta oito**')."

Same proverb, same function (culture note), two topics apart, two different translations of the same phrase.
**Fix:** keep the concessao-01 one (it is on-theme for ても) and cut or repoint the enfase-04 note.

### D7 — `les:n3-estado-05`: a contrast the intro promises and the body never makes

> intro: "…com destaque para os **pares 成人 / 青年 e 生物 / 製品**."
> objective: "Distinguir 成人 (adulto) de 青年 (jovem) **e 生物 (ser vivo) de 製品 (produto)**."

成人/青年 gets a full `tip` note. 生物 and 製品 sit in *different* h3 sections ("Fases da vida e seres vivos"
and "Produção, sistemas e governo") with no note and nothing comparing them. **Fix:** add the second tip
(生 "o que vive/nasce" vs 製 "o que se fabrica"), or drop the pair from the intro and the objective.

### D8 — `les:n3-estado-06`: the objective names three items, the body distinguishes two

> objective + checklist: "Distinguir **同一 / 同時 / 同様** ao falar de igualdade e simultaneidade."
> body, the entire explanation: "同一 serve para identidade total; 「同様」 aceita 'parecido', não precisa ser
> idêntico."

同時 gets one gloss line and is never contrasted, even though it is the one whose *sense* (simultaneity, not
sameness) sits apart from the other two. 同化, also in the list, gets nothing. **Fix:** extend the sentence:
"…；「同時」 não é sobre ser igual, e sim sobre **acontecer ao mesmo tempo** (同時に出発する)."

### D9 — `les:n3-revisao-01`: the "mapa completo" leaves out a whole topic and claims a point never taught

> h2: "**Revisão do N3: o mapa completo**" · "### O que você domina agora"
> - Conectar e organizar: その上, それと/それとも, つまり, ところで.
> - Situar no tempo: うちに, 最中に, たびに, たところ.
> - Causa e resultado: おかげで, せいで, ために, によって.
> - Conjectura e relato: はずだ, みたいだ, らしい, ということだ.
> - Concessão e ênfase: **のに**, くせに, こそ, さえ.

Two problems.
(a) **`topic-51-estrutura` is missing entirely** — the particle の (estrutura-01), the nominalizer こと and
ことができる (estrutura-02) and the past passive 〜られた (estrutura-03) are the last grammar block of the
level and appear in no bullet, while the checklist below repeats the same five headings.
(b) **のに is listed as mastered but never taught.** It appears in n3 only as a *contrast* inside other
lessons ("Para um 'apesar de' neutro, use 「のに」", `les:n3-concessao-02`; ば〜のに in `les:n3-desejos-04`).
It has no section of its own anywhere in `course/n3`.

**Fix:** add a sixth bullet — "Estruturar a frase: の, こと / ことができる, a passiva 〜られた" — and add the
matching checklist line; replace のに with a point the level actually taught (ても or ことは〜が).

### D10 — Two titles promise content the lesson does not contain

- `les:n3-perspectiva-07`, title: "Folga e ganho: **do orçamento** à compreensão". The lesson has 予報
  (previsão) and 予防 (prevenção); 予算 ("orçamento") is not in it — it belongs to `les:n3-tempo-08`.
  **Fix:** "Folga e ganho: **da margem** à compreensão".
- `les:n3-deveres-04`, title: "Falando de competições, **números** e máquinas: vocabulário sobre grupos e
  crescimento". The eighteen items are 全国/全体/先日/前者/選手/選択/前進/センター/増加/相当/操作/装置/速度/
  想像/相続/騒音/象/底 — nothing numeric. **Fix:** "Grupos, competições e crescimento" (the h2 already says
  exactly that, and it is accurate).

### D11 — `les:n3-tempo-06`: the title announces grammar the lesson does not have

> title: "**Tempo, simultaneidade e sequência**"
> description: "Lição de expansão de vocabulário: dezoito palavras que começam com o som tsu … **Sem
> gramática nova.**"
> h2: "Palavras da continuidade: o que se prende, se sucede e se acumula"

"Simultaneidade" names a grammar concept (〜ながら, 〜間に) that this lesson does not teach; the h2 and the
description agree with each other and disagree with the title. **Fix:** promote the h2 to the title.

### D12 — `les:n3-desejos-07`: an English word in learner-facing pt-BR, and the title disagrees with it

> title: "Corpo, natureza e cotidiano: **o bloco ほ**"
> h2: "Lar, corpo e natureza: **o batch ho**"

"batch" is untranslated English in the learner's first line; every other lesson of this shape says "bloco"
or "lote" (`les:n3-causa-05` "o bloco せい", `les:n3-perspectiva-04` "o bloco す"). The two also name
different things ("Corpo, natureza e cotidiano" vs "Lar, corpo e natureza"). **Fix:** h2 → "Lar, corpo e
natureza: o bloco ほ", and align the title to it.

---

## E. Section headings that do not cover their contents

### E1 — `les:n3-causa-05`: a "bloco せい" that is half す

> title: "Personalidade, precisão e impostos: **o bloco せい**"
> intro: "**Muitas palavras de N3 começam com せい**, então vale aprendê-las em conjunto…"

Nine of the eighteen items are す-, not せい-: 頭痛 (ずつう), ずっと, 既に (すでに), 全て (すべて), 鋭い
(するどい), 即ち (すなわち), 素敵 (すてき), スピーチ, 済ませる (すませる). The intro's grouping claim is the
learner's whole memory hook, and it does not hold for half the list. **Fix:** either retitle to "o bloco
せい/す" and say so in the intro, or move the す- items into `les:n3-perspectiva-04` ("o bloco す").

Same lesson, smaller: `«生» (なま) - cru, fresco` is filed under the h3 "**Caráter, exatidão e os homófonos
せい**" while its reading is なま, and the intro lists 生 among "leituras curtas isoladas (正, 性, 生)",
implying せい. **Fix:** move 生/なま out of the せい homophone group, or state explicitly that the entry is
the *other* reading of a kanji whose せい reading the learner already knows (学生).

### E2 — `les:n3-limites-05`: "Corpo, saúde e estadia" contains two abstract nouns

> h3 "**Corpo, saúde e estadia**" → 体育, 体温, 大気, 滞在, 退屈, **存在** (existência), **尊重** (respeito).

存在 and 尊重 belong to neither body, health nor staying. **Fix:** move them to a "Existência e respeito"
group or fold them into the following section.

### E3 — `les:n3-enfase-05`: "Maioria e proporção" contains a war and a reciprocal

> h3 "**Maioria e proporção**" · lead "Quanto é a maior parte de algo." → 大半, 大部分, **互い** (um ao
> outro), **大戦** (grande guerra).

**Fix:** move 互い and 大戦 out; 互い fits "Representação e liderança" poorly too, so a small "Reciprocidade
e conflito" group or the "Mundo natural e objetos" section is the better home.

### E4 — `les:n3-concessao-06`: "O campo e a agricultura" opens with two words about talent

> h3 "**O campo e a agricultura**" · lead "Agora um grupo ligado ao **trabalho rural**. Note que três
> palavras compartilham o kanji de 'agricultura'…" → **能** (talento), **能力** (capacidade), 農業, 農家,
> 農民, ノー.

The two leading items and ノー are not rural; the promised trio (農業/農家/農民) is items 3–5. **Fix:** move
能/能力/ノー into their own group and let the section open on 農業.

### E5 — `les:n3-desejos-02`: "Vocabulário de dinheiro e economia" is half not that

> h3 "**Vocabulário de dinheiro e economia**" · lead "Hipóteses ('se eu tivesse dinheiro…') combinam com
> este campo. Note como o kanji 「金」 … aparece em vários." → 金額, 金銭, 金融, 金庫, 金属, 銀, 景気, 経営,
> 金曜, 近代, **偶然**, **具体**, **区別**, **句**, **計**, **敬意**, **位**.

Seven of seventeen have nothing to do with money, and 金曜 (Friday) and 近代 (modern era) only share the
sound. **Fix:** split into "Dinheiro e economia" (金額…経営) and "Outras palavras do bloco き/く/け".

### E6 — `les:n3-estrutura-06`: "Três palavras" followed by four, the fourth unrelated

> "Três palavras parecidas no som, mas com sentidos distintos:" → 役 (やく), 役割 (やくわり), 約 (やく),
> **文句** (もんく).

文句 is neither one of the three nor similar in sound. **Fix:** move 文句 to the "Coisas, sons e histórias"
group (it is a も- word) and leave the trio intact.

### E7 — `les:n3-limites-07`: two headings that misclassify their own items

> h3 "**Verbos do dia a dia**" → 任せる, 増す, **マスター** (a noun; the verb is マスターする)
> h3 "**Adjetivos e advérbios de grau**" → 貧しい, **負け** (a noun), 正に, 真逆, ぼんやり, まあ

**Fix:** move マスター and 負け into the "Gente, lugares e coisas concretas" group.

### E8 — `les:n3-enfase-03`: 国民 listed twice, the second time in a malformed bullet

> "- «国民» (「こくみん」) = 'povo, cidadãos de um país'."
> …four bullets later…
> "- **«国民» aparece muito em notícias, ao lado de «克服» (「こくふく」) = 'superação, vencer uma dificuldade'.**"

The second bullet is a duplicate entry that exists only to smuggle 克服 into the list, and it reads as a
sentence, not a glossary line. **Fix:** delete the duplicate and give 克服 its own bullet:
"- «克服» (こくふく) = 'superação, vencer uma dificuldade'."

---

## F. Vague, filler, or manufactured pedagogy

### F1 — Two kanji entries that name no word (`les:n3-perspectiva-01`, `les:n3-perspectiva-02`)

Every other bullet in these two "Kanji do dia" lists ends in a concrete compound. These two do not:

> "«予» (de antemão, previamente). **Aparece em palavras de planejamento, como adiar algo previsto.**"
> "«参» (participar, tomar parte, visitar). **Aparece no verbo de participar, como em uma reunião.**"

The learner is told a compound exists but not which one. **Fix:** "«予» … Aparece em 「予定」 ('agenda'),
「予約」 ('reserva') e 「予習」 ('estudo prévio')." / "«参» … Aparece em 「参加する」 ('participar') e
「参考」 ('referência')."

### F2 — The tail of each kanji section is a run-on dump (9 lessons)

The established pattern inside a "kanji novos" section is one paragraph per kanji, with a component
breakdown and a compound. The last paragraph of the section then abandons it and crams the remainder into a
single sentence with no mnemonic:

> `les:n3-enfase-01`: "O kanji «亡» significa 'falecido, perecer'. O kanji «舞» significa 'dança, rodopiar'…
> O kanji «婦» tem o radical da mulher… E o kanji «寄» significa 'aproximar-se, reunir'…" (4 in one paragraph)
> `les:n3-desejos-04`: "**Mais cinco para a sua coleção:** «横»…; «深»…; «光»…; «路»…; e «太»…" followed by
> "**E quatro do mundo do estudo e do clima:** «科»…; «師»…; «客»…; e «候»…" (9 across two sentences)
> `les:n3-conjectura-04`, worst case: heading "**Kanji de ação e emoção (um grande bloco de revisão)**" then
> **14 kanji** in four paragraphs, including the parenthetical "(só 遠 e 逃 trazem o radical 辶; 戻 vem de 戸,
> porta, e 越 vem de 走, correr)"
> `les:n3-relato-04`: **14 kanji** as a flat bullet list, one of which opens "«晴»… **já vimos**; aqui entra
> o parente «雪»…" — a bullet whose head kanji is not what it teaches

Both of the 14-kanji cases carry a note that effectively apologises for the dump ("São muitos kanji de uma
vez, então não tente decorar todos agora"), which is the tell. Also in enfase-02, enfase-03, enfase-04,
concessao-01, concessao-04. **Fix:** cap a kanji section at what fits the one-per-paragraph pattern and push
the overflow into the next lesson, or give the overflow its own sub-heading with the same treatment.

### F3 — `les:n3-concessao-07`: a manufactured pitfall between two words nobody confuses

> "E **ミス (erro) não tem nada a ver com 妙 (みょう, 'estranho')**: a primeira vem do inglês, a segunda é
> palavra japonesa de origem chinesa."

みす and みょう are not homophones, near-homophones, or semantically adjacent; the note warns against a
confusion it has to invent. **Fix:** delete the second half of the note (the first half, 魅力 vs 魅力的, is
a real distinction and should stay).

### F4 — `les:n3-perspectiva-05`: a culture note that ends on a non-sequitur

> "**Cultura** — O 梅雨 (つゆ) é uma estação bem marcada no calendário japonês: chove quase todos os dias
> entre o fim de maio e meados de julho… O nome se escreve com os kanji de 'ameixa' e 'chuva', porque
> coincide com o amadurecimento das ameixas. É um período tão úmido que tudo parece encharcado, **mas a
> palavra 「積もる」 vale mesmo para o que se empilha, como neve, poeira e trabalho.**"

The final clause is about a different word, joined by an adversative ("mas") that carries no contrast — the
note reads as if two notes were merged. **Fix:** end the culture note at "…amadurecimento das ameixas." and
move the 積もる line into the bullet for 積もる, without "mas".

### F5 — `les:n3-perspectiva-05`: an N5 particle presented as N3 vocabulary, to hit a count

> "### **Partícula で e itens restantes**
> Falta apresentar uma palavra-ferramenta e fechar o vocabulário da lição.
> - «で» (で) - em, no, na (marca o lugar onde uma ação acontece).
> 「海で釣りをするのが好きだ」 (Gosto de pescar no mar.)
> Repare que 「で」 aqui marca *onde* a ação acontece (no mar), e a frase ainda usa 「釣り」, a pescaria.
> **Com isso, você já viu as dezessete palavras desta lição.**"

The particle で is N5 material and the heading itself ("itens restantes") admits the section exists to
close a tally; the closing sentence states the tally out loud, which is bookkeeping addressed to the
curriculum, not to the learner. **Fix:** drop the section, fold 釣り into "Clima, sensações e
acontecimentos", and delete the count sentence.

### F6 — `les:n3-conjectura-02`: the contrast note reuses the phrase it assigned to the other item

> h3: "**わけがない: não tem como, é impossível**"
> note: "Não confunda com 「はずがない」. O 「わけがない」 nega por raciocínio lógico ('é absurdo pensar isso');
> 「はずがない」 nega a possibilidade com base no que se sabe (**'não tem como ser assim'**)."

"Não tem como" is the heading's own gloss for わけがない and is then handed to はずがない as its distinguishing
translation, so the pair the note is separating collapses back together. **Fix:** give はずがない a different
Portuguese anchor: "…('**não era para ser assim**', pelo que se sabe)".

### F7 — `les:n3-tempo-07`: a homophone warning that never names the homophones

> objective: "Distinguir palavras parecidas: 額 … e **os verbos que soam ひく**, como 轢く (atropelar)."
> note: "E o verbo 轢く (ひく, atropelar) **soa idêntico a outros verbos do dia a dia**; é o contexto, e não o
> som, que diz qual é qual."

The two verbs in question — 引く (puxar) and 弾く (tocar um instrumento) — are never named, and 引っ張る
(puxar) is introduced in the very same lesson, so the learner has the raw material and is denied the link.
**Fix:** "…soa idêntico a **引く** ('puxar', o mesmo 引 de 引っ張る) e a **弾く** ('tocar piano/violão'); só o
kanji e o contexto separam os três."

### F8 — `les:n3-limites-03`: 富士山 used to illustrate 富 = "riqueza"

> "- «富» riqueza, abundância: 「**富士山**」, 'monte Fuji'."

In 富士山 the kanji are ateji for a pre-existing name; 富 carries none of "wealth" there, so the example
undoes the gloss it is meant to support. Every other bullet in the same list uses a transparent compound
(速→速度, 給→給料). **Fix:** "«富» riqueza, abundância: 「豊富」, 'abundante'" (which the course already
teaches, in `les:n3-deveres-06`).

### F9 — `les:n3-tempo-06`: an example that uses the pattern the course just told the learner to avoid confusing

> `les:n3-tempo-03` warning: "Não confunda com ～ているところ (estar no meio de algo) **nem com ～たところだ
> (acabar de fazer)**."
> `les:n3-tempo-06` intro: "…usamos só padrões que você já conhece, como 「うちに」, 「きり」 e 「**たところ**」…"
> `les:n3-tempo-06` example: "「泥棒が警察に**捕まったところだ**」 (O ladrão **acabou de** ser pego pela polícia.)"

The example is 〜たところ**だ**, i.e. exactly the form flagged three lessons earlier as the thing *not* to
confuse with the 〜たところ this lesson claims to be reusing — and no note marks the switch. (The lesson's
other example, 「机の上を見たところ大きな包みがあった」, uses the intended pattern correctly.)
**Fix:** either change the example to the discovery 〜たところ (「警察が来たところ泥棒は逃げていた」) or add
one line naming the difference.

### F10 — Kanji entries whose only example is the kanji itself (4 sites)

> `les:n3-intencao-01`: "«声» ('voz'): a voz com que a gente diz o que pensa. **Em 「声」 ('voz').**"
> `les:n3-intencao-03`: "«石» ('pedra'): um penhasco com uma pedra embaixo. **Em 「石」 ('pedra').**"
> `les:n3-intencao-03`: "«神» ('deus'): à esquerda o radical de 'altar/divino'. **Em 「神」 ('deus')** e 「神道」."
> `les:n3-deveres-01`: "«頭» ('cabeça'): tem o radical de 'página/rosto' (頁) à direita. **Aparece em 「頭」
> ('cabeça').**"

The "aparece em" slot is supposed to show the kanji at work in a word; here it restates the entry.
**Fix:** 声 → 「声を出す」/「大声」; 石 → 「石段」/「宝石」 (the course teaches 宝石 in `les:n3-deveres-06`);
神 → keep only 「神道」; 頭 → 「頭痛」 (taught in `les:n3-causa-05`).

---

## Count table

| Class | Checked | Flagged |
|---|---:|---:|
| **A. pt-BR text defects** | 101 lesson bodies | **11** (A1 covers 4 lessons / 53 unambiguous stripped tokens + minimal-pair tail) |
| **B. Japanese examples wrong or off-point** | ~640 inline JP examples | **17** |
| **C. Structural defects on the page** | 101 bodies, 1,332 vocab items, 715 notes | **8** (C4 = 1,396 sites / 88 lessons; C5 = 18 sites / 4 lessons; C7 = 43 notes / 35 lessons) |
| **D. Duplicated / promised-not-delivered** | 101 titles, 101 h2, all `<p>` ≥70 chars | **12** |
| **E. Headings vs contents** | ~430 h3 sections | **8** |
| **F. Vague / filler / manufactured pedagogy** | 101 bodies | **10** |
| **TOTAL** | **101 lessons** | **66 defects** |

### Clean, and stated as such

| Check | Result |
|---|---:|
| Furigana integrity (`<jp reading>` vs surface) | **0** |
| XML tag balance in `body` | **0** |
| Em dash (—) in authored prose | **0** |
| `gp-NN` codes / `sent:`/`les:`/`top:` id leaks in learner text | **0** |
| Reviewer instructions, TODO/FIXME/placeholder text | **0** |
| `<term>` without `define` | **0** |
| Lesson bodies in `topic-38` lessons 05–08, `topic-40`, `topic-43`, `topic-44`, `topic-45`, `topic-47` grammar lessons | no A-class (accent) defects |

**Excluded by instruction (STATE.md open items):** 4 reading-vs-corpus mismatches found by scan
(`les:n3-intencao-03` 柄 がら, `les:n3-deveres-03` 金 きん, `les:n3-conjectura-03` 品 ひん,
`les:n3-relato-04` 上 じょう) all resolve to rows already sitting in
`course/vocab_disambiguation_review.json` and are **not** counted above.

### Suggested triage order for the teacher queue

1. **C1, C2, C3** — three lessons currently render a word or a kanji as nothing. Smallest fix, worst symptom.
2. **B1, B2, B3, B4** — four statements that are simply wrong (a ても example with no ても; 空き缶 as から;
   抱く as "abraçar" against its own linked record; ボーイ as "garoto").
3. **A1** — the four accent-stripped lessons; mechanical except for the minimal pairs.
4. **D1** — two pairs of same-titled lessons; a naming decision, then a one-line edit each.
5. **C4** — needs a decision (renderer vs prose) before anyone edits 88 files.
6. Everything else.
