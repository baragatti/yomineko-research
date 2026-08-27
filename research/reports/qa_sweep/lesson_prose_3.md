# QA sweep — lesson prose, part 3/3: every lesson body under `course/n3`

**Scope.** All 101 lesson bodies in `course/n3/topic-38-conectores` … `topic-52-revisao`
(15 topics, 644,643 characters of `body`), read in full as a Brazilian learner would read them.
Judged against `design/translation_style.md`.

**Excluded by instruction and honoured:** sentence `structure_explanation` fields (being re-authored
elsewhere); the open items already recorded in `STATE.md` — the 875 `<jp>` spans with kanji and no
`reading` attribute, the homograph-ref queue (上/じょう, 柄/がら, 品/しな, 金/きん) and the 20 headwords
in `course/vocab_disambiguation_review.json`, the i+1 sentence re-selection, the empty `needs[]`
model, the pending listening audio, and the ateji list. Where a defect class overlapped one of those
queues I chose exemplars from **outside** it, so nothing below restates a known item.

Findings are ordered by severity. Every one carries the lesson id, the exact current text, why it is
wrong, and a concrete fix.

---

## Class A — pt-BR prose with the diacritics stripped (4 lessons, ~30 words)

This is the largest single concentration of defects in the slice and it is confined to
**`topic-38-conectores` lessons 01–04**. The rest of n3 (97 lessons) is diacritically clean, so this
is not a corpus-wide condition; it is four lesson bodies that a previous accent pass did not reach.
`fix_accents_lessons.py` and `accent_sweep_localized.py` repaired description/objectives/exercise
fields, but these four **bodies** still carry the damage.

### A1 — `les:n3-conectores-01` (12+ stripped words in the body)

> "Confundir a soma com a escolha **e** o erro **classico** do brasileiro aqui"
> "A imagem literal **e** boa: 上 **e** 'em cima', então **e** como empilhar um segundo ponto"
> "acrescenta mais um item ou mais uma ação a algo **ja** mencionado"
> "Tem um tom mais falado e **espontaneo**."
> "それと **e** o jeito de conversa."
> "Você vai tomar **cafe**? Ou (então) **cha**?"
> "são quase **identicos** na escrita"
> "a escolha entre frases **e** それとも"
> "= 'claro, evidente, **obvio**'. **E** um adjetivo な."
> "(**album**)"
> "cada vogal **mantem** seu som **ate** o fim … **e** 'a-i-ro-n'"
> "traz a ideia de '**mutuo**'"
> "Em cima **esta** 安 … e embaixo a **arvore** (木)"

**Fix:** é / clássico / é boa / é "em cima" / é como / já / espontâneo / é o jeito / café / chá /
idênticos / é それとも / óbvio / É um adjetivo / álbum / mantém / até / é "a-i-ro-n" / mútuo / está /
árvore.

### A2 — `les:n3-conectores-02`

> "だけど / けど: mas, **so** que, mesmo assim"
> "**E** a versão coloquial de しかし"
> "normalmente usamos **so** けど"
> "= 'Este filme **e** longo, mas **e** interessante.'"
> "existe outro けど que **so** SUAVIZA … ('**e** que...')"
> "aqui o sentido **e** sempre de OPOSIÇÃO"
> "**E** o nosso 'ou seja'"
> "tirar uma conclusão **logica** … Ele **e** o termo neutro … すなわち … **e** mais **tecnico** e formal, e 要するに **e** 'resumindo'"
> "**E** uma palavra de transição independente"
> "= 'A propósito, qual **e** a agenda de hoje?'"
> "por isso 'mudando de assunto' **as vezes** traduz melhor … aqui, sozinho no começo da fala, **e** sempre 'a propósito'"
> "o substantivo **e** あらわれ" / "o par transitivo **e** あてる"
> "= 'novo, **inedito**'"
> "= '**forca**, vigor, energia'"
> "= '**vestigio**, marca'"
> "Esse par **e** um ponto **classico** de confusão"
> "significa '**superficie**, tabela, expressar'"
> "O radical da esquerda **e** a joia/rei (王) e **a direita** o ver (見)"

**Fix:** só que / É a versão / só けど / é longo, mas é interessante / só SUAVIZA / "é que..." / é sempre /
É o nosso / lógica / Ele é / é mais técnico / é "resumindo" / É uma palavra / qual é / às vezes /
é sempre / é あらわれ / é あてる / inédito / força / vestígio / é um ponto clássico / superfície /
é a joia/rei … e **à** direita.

### A3 — `les:n3-conectores-03`

Heading: `<heading level="2"><text>Explicando o porque: justificar com clareza e cortesia</text></heading>`
— but the lesson **title** is "Explicando o **porquê**". The h2 and the title disagree on the same word,
and the h2 is the wrong spelling (interrogative "por que" ≠ noun "porquê").

> "de um pedido **e** essencial para soar adulto … Você **ja** conhece o から"
> "a versão educada e **enfatica**" (×3 in body + description)
> "A ordem **e**: primeiro o motivo … **E** a versão formal e ligeiramente mais **enfatica**"
> "= 'Porque **esta** frio, vamos fechar a janela.'"
> "retoma um motivo **ja** dado"
> "なぜなら: isso porque, a razão **e** que"
> "abre uma frase nova dedicada **SO** a justificar"
> "o fechamento com から … **e** quase obrigatório"
> "= 'Hoje não vou. Isso porque **esta** chovendo.'"
> "não **esqueca** o から no fim, mesmo **ja** tendo dito … a gente diz **so** 'porque' … a causa fica **ABRACADA** entre なぜなら … soa formal e **e tipico** de textos escritos"
> "'respiração, **folego**'), い ('**estomago**')" / "**Saude**: いし ('**medico**, doutor'). Combina com causa: 'Vou ao **medico**, porque o **estomago doi**'"
> "'**oleo**'" / "'diabo, **demonio**'" / "**Otimo** para abrir uma recusa educada"
> "que se **le** igual mas se escreve diferente"
> "**So** o contexto **e** o kanji separam os dois"
> "O radical da esquerda **e** a água" / "O radical externo **e** o portão" / "cresce o que **e** real"

**Fix:** porquê (heading) / é essencial / já conhece / enfática / A ordem é / É a versão / está frio /
já dado / a razão é que / SÓ a justificar / é quase obrigatório / está chovendo / esqueça / já tendo /
só "porque" / ABRAÇADA / é típico / fôlego / estômago / Saúde / médico / dói / óleo / demônio / Ótimo /
lê / Só o contexto e o kanji / é a água / é o portão / o que é real.

### A4 — `les:n3-conectores-04`

> "**da** uma lista de exemplos que NÃO **e** completa: os itens citados são **so** alguns"
> "Ele **ja** carrega a ideia de 'e coisas do **genero**' … など **e** neutro"
> "なんか: coisas como... ou sei **la**, nem ligo"
> "**e** a versão coloquial de など … com tom de **desdem**. O contexto **e** a entonação decidem qual dos dois **e**."
> "= 'Ele toca **ate** coisas como piano.'"
> "vira 'que nada', 'nem ligo para', 'sei **la**' ou um 'isso de' carregado de **desdem**. なんか **e** bem informal … onde など **e** a escolha segura. E não confunda com なんて, que **e** mais exclamativo e **enfatico**."
> "**Otima** para o sentido oposto de など"
> "A escrita em kanji **e** rara; quase sempre se **ve** em kana"
> "o oposto **e** 帰り" / "'não pode, **e** proibido, **e** ruim'"
> "O う japonês tem **labios** neutros"
> "'**seguranca**'" / "**E** um sufixo muito produtivo" / "uma pessoa em **pe** e outra de **cabeca** para baixo"
> "'o melhor, **otimo**'" / "O radical da esquerda **e** o fio"
> "Vocabulário para fechar a **serie**"
> Checklist: "Sei que なんか **e** a versão coloquial de など **e** pode carregar **desdem**."

**Fix:** dá / não é completa / só alguns / já carrega / gênero / é neutro / sei lá / é a versão /
desdém / O contexto e a entonação decidem qual dos dois é / até / é bem informal / é a escolha /
é mais exclamativo e enfático / Ótima / é rara / se vê / é 帰り / é proibido, é ruim / lábios /
segurança / É um sufixo / pé / cabeça / ótimo / é o fio / série / é a versão … e pode carregar desdém.

---

## Class B — broken or missing markup that reaches the learner's screen

### B1 — `les:n3-deveres-02`: a vocabulary entry with **no headword**

Raw body:

```
<item><text> (</text><jp>きじゅん</jp><text>) = 'critério, padrão de referência'.</text></item>
```

Every sibling item in that list opens with `<vocab ref="vocab:…"/>`. This one does not, so the learner
reads a bullet that literally begins with a space and an open parenthesis: " (きじゅん) = 'critério,
padrão de referência'." — the word 基準 is never shown.

The lesson's eighteen `unlocks` are all accounted for by the other eighteen bullets, so this is a
nineteenth, orphaned row. The corpus record is `vocab:1591210` (基準, きじゅん) — but it is levelled
**n2**, which is probably why it was never wired in.
**Fix (teacher call):** either delete the orphaned row, or add `<vocab ref="vocab:1591210"/>` **and**
the matching `unlocks` entry — the second option pulls an n2 word into an n3 lesson, so it needs a
level decision, not a silent patch.

### B2 — `les:n3-deveres-03`: a kanji introduced without the kanji, duplicated from the next lesson

Raw body, first paragraph under `<heading level="3"><text>Kanji novos</text></heading>`:

```
<p><text>O kanji </text><text> ('comércio, negociar') aparece em </text><jp reading="しょうにん">商人</jp>…
```

The `<kanji ref="kanji:商"/>` is missing, so the page reads **"O kanji ('comércio, negociar') aparece
em 商人…"**. 商 is also **not** in this lesson's `unlocks`. The paragraph is a stranded near-copy of the
one that legitimately introduces 商 in the *next* lesson, `les:n3-deveres-04`:

> deveres-03: "Pense numa boca (口) que pechincha embaixo da barraca."
> deveres-04: "Imagine uma boca que pechincha embaixo da barraca da feira."

**Fix:** delete the orphaned paragraph from deveres-03 (deveres-04 already teaches 商 correctly and
unlocks it). deveres-03's kanji section then matches its 10 unlocked kanji exactly.

### B3 — `les:n3-desejos-03`: a second vocabulary entry with no headword

```
<item><vocab ref="vocab:1592100"/><text> (</text><jp>くう</jp><text>) = 'comer' (informal, masculino).
</text><text> (</text><jp>くらう</jp><text>) = 'devorar, levar (uma porrada)'.</text></item>
```

食らう has no `<vocab ref>`; the learner sees " (くらう) = 'devorar, levar (uma porrada)'." with a blank
where the word should be. There is **no vocab record for 食らう anywhere in `corpus/vocab/`**, and the
lesson does not unlock it, so this is a dangling fragment rather than a lost ref.
**Fix:** rewrite it as plain prose attached to the 食う row, spelling the word out —
"食う (くう) = 'comer' (informal, masculino); a variante 食らう (くらう) é ainda mais bruta: 'devorar,
levar (uma porrada)'." — or delete the fragment.

### B4 — `topic-39-tempo` 01–04: 7 sentences broken across three block elements

Pattern (from `les:n3-tempo-01`):

```
<note type="l1-pitfall"><p><text weight="bold">Armadilha PT.</text><text> A forma negativa </text></p>
<jp reading="あめがふらないうちに">雨が降らないうちに</jp><p><text> traduz-se por 'antes que comece a chover'…
```

The `<jp>` sits **outside** the `<p>`, so one sentence renders as three separate blocks: "Armadilha PT.
A forma negativa" / 雨が降らないうちに / "traduz-se por…". Seven occurrences, all in tempo-01 (3),
tempo-02 (2), tempo-03 (1), tempo-04 (1); no other n3 lesson does this.
**Fix:** move the `<jp>` inside the surrounding `<p>` so each note is a single paragraph.

### B5 — `les:n3-perspectiva-05`: a katakana word written in hiragana inside a `reading`

```
<jp reading="あしたまでにれぽーとをていしゅつしてください">明日までにレポートを提出してください</jp>
```

`れぽーと` is malformed kana (a chōonpu after hiragana) and will misalign the furigana over レポート.
Every other lesson keeps katakana as katakana in the reading — e.g. `les:n3-estado-02` correctly writes
`いちにちでレポートをかきあげた`.
**Fix:** `あしたまでにレポートをていしゅつしてください`.

### B6 — `les:n3-intencao-02`: same defect, second instance

```
<jp reading="ここでたばこをすわないことになっている">ここでタバコを吸わないことになっている</jp>
```
**Fix:** `ここでタバコをすわないことになっている`.

### B7 — 43 `reading` attributes containing spaces (6 lessons)

`les:n3-conjectura-01` (8), `-02` (6), `-03` (11), `-04` (6), `-06` (5), `les:n3-relato-06` (7).
Examples:

> `<jp reading="かれ は もう ついた はず だ">彼はもう着いたはずだ</jp>`
> `<jp reading="おこって いる みたい だ">怒っているみたいだ</jp>`
> `<jp reading="かれは このぶんやの はかせ だという ことだ">彼はこの分野の博士だということだ</jp>`

The other ~95 lessons never put spaces in a reading. A furigana aligner will either fail or emit the
spaces over the kanji. **Fix:** strip all whitespace from the `reading` attribute in those 43 spans.

### B8 — `les:n3-relato-01`: a `<vocab ref>` embedded inside the Portuguese translation

```
常識というのは、みんなが知っているはずのことです = "<vocab ref="vocab:1356000"/> (bom senso), ou seja,
é aquilo que todo mundo deveria saber".
主義とは、ある考え方のことです = "<vocab ref="vocab:1325260"/> (doutrina) é uma certa maneira de pensar".
```

The Portuguese gloss renders as **"常識 (bom senso), ou seja, é aquilo que…"** — a Japanese headword
inside the pt-BR translation line. Every other example in the slice gives a clean pt-BR translation.
**Fix:** "Senso comum, ou seja, é aquilo que todo mundo deveria saber." / "Doutrina é uma certa maneira
de pensar."

---

## Class C — the lesson introduces material it never teaches

### C1 — `topic-41-causa` lessons 01–04: **25 kanji unlocked, zero kanji taught**

| lesson | kanji unlocked (SRS cards created) | kanji section in body |
|---|---|---|
| `les:n3-causa-01` | 官 昨 次 求 論 | none |
| `les:n3-causa-02` | 係 増 変 情 感 投 示 | none |
| `les:n3-causa-03` | 両 容 式 打 果 直 確 | none |
| `les:n3-causa-04` | 争 必 歳 演 能 談 | none |

Verified: `les:n3-causa-01` `srs.introduces_cards` contains `deck:kanji-n3` entries for all five, and
the body contains **no `<kanji ref>` at all**. Every other n3 grammar lesson has a "Kanji novos" /
"Kanji do dia" / "Kanji do bloco" section. A learner finishing causa-01 gets five kanji flashcards for
characters the lesson never showed, explained, or decomposed.

Downstream consequence, already visible: `les:n3-relato-01` introduces 示 as a **new** kanji
("O kanji 示 significa 'mostrar, indicar'… Aparece em 示す e 展示") — but causa-02 silently unlocked it
~30 lessons earlier.

**Fix:** author the four missing kanji sections in causa-01…04 following the pattern of
`les:n3-estado-01`/`-02` (component decomposition + two example compounds each); then relato-01's
"Kanji novos" heading for 示 becomes correct as a review reference instead of a first introduction.

### C2 — `les:n3-estado-05`: a promised contrast that never arrives

Intro: *"Sem gramática nova: o foco é o vocabulário, com destaque para os pares **成人 / 青年** e
**生物 / 製品**."*
Objective and checklist repeat it: *"Distinguir 成人 (adulto) de 青年 (jovem) e **生物 (ser vivo) de
製品 (produto)**."*

The body delivers only the first pair (a `tip` note on 成 vs 青). 生物 and 製品 sit in two different
sections with no comparison anywhere. They are also not a confusable pair (せいぶつ vs せいひん), so
the promise is both unkept and ill-chosen.
**Fix:** either add the note, or replace the promised pair with a real one from the lesson —
**製造 / 製品** (せいぞう "fabricar" vs せいひん "o produto fabricado") is the natural candidate and
sits in the same list.

### C3 — `les:n3-estado-06`: the checklist claims a verb the lesson never uses

Objective and checklist: *"Empregar どうしても e **通す** em frases sobre persistência e estado das
coisas."*
The list glosses 通す ("deixar passar, dar passagem; também 'levar até o fim'"), but the only example
in that section is:

> 「その道路は高い塔の前を**通る**」 reading 「そのどうろはたかいとうのまえを**とおる**」
> (Aquela estrada passa em frente a uma torre alta.)

That is 通る (intransitive), a different verb — and the difference is never flagged. So the lesson
asserts a skill it does not demonstrate and quietly swaps the transitive twin for the intransitive one.
**Fix:** add a 通す example (e.g. 「客を部屋に通す」 "fazer o visitante entrar na sala") and a one-line
transitive/intransitive note, matching how the same topic handles 隠す/隠れる in `les:n3-estado-02`.

Same lesson: the objective also says *"Distinguir 同一 / 同時 / 同様"*, but the body's paragraph only
contrasts 同一 with 同様 — 同時 is listed and never discussed.

### C4 — 注ぐ is unlocked in one lesson and taught in another

`les:n3-tempo-06` unlocks **both** `vocab:2145240` (注ぐ / つぐ) and `vocab:1581730` (注ぐ / そそぐ),
but teaches only つぐ, and its pitfall states flatly:

> "つぐ 注ぐ é despejar um líquido"

そそぐ — the commoner reading — is never mentioned. Five topics later, `les:n3-desejos-05` teaches it
as a fresh item ("そそぐ - despejar, servir um líquido") **without** unlocking it.
**Fix:** move `vocab:1581730` to desejos-05's `unlocks`, and add "(também lido そそぐ)" to tempo-06's
pitfall so the two readings are not presented as one word.

The same split affects 数 (`vocab:1580820` かず unlocked by `les:n3-perspectiva-04`, which teaches only
`vocab:1580825` すう; かず is then taught as new in `les:n3-estado-03`).

### C5 — `les:n3-deveres-06`: a highlight pointing at nothing

> "Repare em 弁当, parte essencial do dia japonês, e em **冒険** para histórias."

Two example sentences follow, using 弁当 and 宝石. 冒険 appears in the list and in no example.
**Fix:** either add a 冒険 sentence or drop it from the "Repare em" line.

### C6 — `les:n3-conectores-05`: the description promises a word the lesson never covers

> DESC: "Esta lição ensina palavras N3 ligadas a discurso e referência, como いずれ, さて e **そのまま**"

そのまま is not in conectores-05's body or unlocks; it is taught in `les:n3-desejos-05`.
**Fix:** replace そのまま in the description with a word the lesson actually teaches (こんにちは or
あるいは), or move it here.

### C7 — `les:n3-revisao-01`: the level's capstone under-delivers on its own map

The body lists five blocks the learner "domina agora":

> "Conectar e organizar … Situar no tempo … Causa e resultado … Conjectura e relato … Concessão e ênfase."

The self-assessment checklist has **two** items, covering only the first two blocks:

> "[x] Escolho o conector certo para somar, contrastar ou concluir.
>  [x] Sei situar uma ação numa janela de tempo (うちに, 最中に)."

Causa, conjectura/relato and concessão/ênfase get no checkpoint, although the objective is explicitly
*"Autoavaliar o domínio dos blocos de gramática do N3."*

The same lesson also **introduces four brand-new words** (郵便, 便, 停留所, ピン) under
*"Vocabulário avulso para fechar"*, in a lesson its own description calls *"um mapa de revisão e
autoavaliação"*. New vocabulary in the review capstone contradicts the framing, and the four words have
no thematic link to anything in the lesson.

Two smaller inaccuracies in the same recap list: **ために** and **のに** are listed as N3 achievements,
but both are N4 material — the N3 points actually taught are そのために (causa-02) and くせに /
ことは〜が / にしては / にしても / わりには (concessão).

**Fix:** extend the checklist to one item per block; move the four words into a vocabulary lesson;
replace ために/のに with そのために and くせに.

---

## Class D — numeric claims that do not match what the lesson introduces

Each of these is a learner-facing count, in an objective or a checklist, that is wrong. Verified
against each lesson's `unlocks`.

| lesson | claim | actual | the extra item(s) |
|---|---|---|---|
| `les:n3-tempo-02` | "Reconhecer **14 palavras novas e 7 kanji**" (obj + 2 checklist items) | 13 vocab, 6 kanji | 市 (`vocab:1308080`, taught in conectores-05) and 都 (unlocked earlier) are counted as new. 一瞬 is correctly flagged "você já viu"; 市 is not. |
| `les:n3-tempo-03` | "Reconhecer 14 palavras novas e **6 kanji**" | 5 kanji | 進 was already unlocked. |
| `les:n3-tempo-04` | "Reconhecer **14 palavras novas** e **6 kanji**" | 12 vocab, 5 kanji | いずれ (`vocab:1566210`, taught in conectores-05) is re-listed unflagged; 産 already unlocked. |
| `les:n3-limites-04` | "Reconheço a leitura dos sete kanji e dos **treze** vocábulos novos" | 12 | 後/ご (`vocab:2147630`, taught in conectores-05) is re-listed unflagged. |

### D5 — `les:n3-deveres-01`: three already-taught kanji under "Kanji novos"

The section presents 働, 好, 形, 種, 頭, 葉, 伝 — but the lesson unlocks only 伝, 形, 種, 葉.
**働** (first presented in `les:n4-kanji-exame-01`), **好** (`les:n4-kanji-exame-02`) and **頭**
(`les:n4-kanji-exame-05`) are given full first-introduction treatment ("O kanji 働 ('trabalhar') junta a
pessoa (イ) com 'mover' (動)…") under a heading that says they are new.
**Fix:** move 働/好/頭 into a short "já vistos, agora em contexto" line, or retitle the section
"Kanji desta lição" and mark the three as revision.

Two n3-internal repeats of the same shape: `les:n3-limites-02` presents 単 under "Kanji do bloco" one
lesson after `les:n3-limites-01` introduced it (the lesson does flag it — "(revisão)" and a tip — so
this one is deliberate and fine); `les:n3-relato-04` presents 晴 the lesson after `les:n3-relato-03`
introduced it, and there the bullet is malformed (see G7).

---

## Class E — material the learner already has, presented as new

### E1 — Days of the week and 日本, taught as new N3 vocabulary in seven lessons

| lesson | item | gloss as printed | where the learner already met it |
|---|---|---|---|
| `les:n3-tempo-08` | `vocab:1545770` 曜日 | "dia da semana" | body of `les:n5-particulas-lugar-04`, `les:n5-comparacoes-04`, `les:n4-forma-simples-05` |
| `les:n3-intencao-02` | `vocab:1194280` 火曜 | "terça-feira" | `les:n5-conectando-07`, `les:n4-transitividade-02` |
| `les:n3-deveres-05` | `vocab:1445580` 土曜 | "sábado" | `les:n5-passado-02`, `les:n5-convites-02`, `les:n4-passiva-01` |
| `les:n3-desejos-02` | `vocab:1243310` 金曜 | "sexta-feira" | `les:n5-particulas-lugar-06`, `les:n5-passado-04`, `les:n4-volitivo-04`, `les:n4-obrigacao-04` |
| `les:n3-limites-02` | `vocab:1255880` 月曜 | "segunda-feira" | as above |
| `les:n3-enfase-06` | `vocab:1464880` 日曜 | "domingo" | as above |
| `les:n3-relato-07` | `vocab:1534880` 木曜 | "quinta-feira (forma curta de 木曜日)" | as above |
| `les:n3-enfase-06` | `vocab:1582710` **日本** | "Japão" | appears in **22** pre-N5/N5/N4 lesson bodies |

The 日本 case is the sharpest: a learner three quarters of the way through N3 is shown 日本 as a new
word, in a list headed *"Dias e luz do sol"*. Three more of the same shape: `vocab:1333450` 週
("semana") in `les:n3-relato-03`; `vocab:1156800` 意味 ("significado, sentido") in `les:n3-relato-01`
— 意味 was first unlocked in `les:n5-verbos-04`; `vocab:1441870` 伝える in `les:n3-relato-02`, first
unlocked in `les:n4-aspecto-01`.

**Fix (prose level, no corpus change needed):** these words are being pulled in because they sit in a
kana-run block (かよう, どよう, きんよう…). Reframe each as a reading note rather than a new word —
e.g. in `les:n3-relato-07`, replace the bullet with a parenthetical inside the もく group:
"(o mesmo もく de 木曜日, que você já usa)". That preserves the sound-grouping pedagogy without telling
an N3 learner that "sábado" is new.

### E2 — Grammar points re-taught as bare vocabulary entries

Nine cases where a structure that got a full section (heading + examples + pitfall) in an earlier
lesson reappears later as a one-line vocabulary bullet, with no "você já viu isto" marker:

| re-listed in | item | originally taught in |
|---|---|---|
| `les:n3-tempo-06` | つまり (`vocab:1610430`) "ou seja, isto é, quer dizer" | `les:n3-conectores-02`, `gram:n3-tsumari`, full section |
| `les:n3-causa-06` | ですから (`vocab:1008430`) "portanto, por isso (versão polida de だから)" + a fresh l1-pitfall repeating the same だから contrast | `les:n3-conectores-03`, `gram:n3-desu-kara`, full section |
| `les:n3-desejos-05` | それとも (`vocab:1007010`) | `les:n3-conectores-01`, `gram:n3-sore-tomo` |
| `les:n3-limites-06` | なぜなら (`vocab:1009410`) | `les:n3-conectores-03`, `gram:n3-nazenara` |
| `les:n3-intencao-06` | ところで (`vocab:1343110`) and ところが (`vocab:1008570`) | ところで: `les:n3-conectores-02`; ところが is then formally introduced *later*, in `les:n3-concessao-03` |
| `les:n3-concessao-05` | だけど (`vocab:1007370`) and **たとえ** (`vocab:1597125`) "mesmo que, ainda que, por mais que" | だけど: `les:n3-conectores-02`; **たとえ: `les:n3-concessao-01`, four lessons earlier in the same topic** |
| `les:n3-conjectura-07` | めったに (`vocab:1612000`) "raramente, quase nunca (sempre com verbo negativo)" + a pitfall repeating the negative-verb rule | `les:n3-enfase-04` — an entire lesson devoted to めったに〜ない, with two sections and a frequency scale |
| `les:n3-deveres-05` | 途端 (`vocab:1610870`) "no instante exato em que" + a pitfall on 〜た途端 | `les:n3-tempo-03`, `gram:n3-ta-totan` |
| `les:n3-enfase-05` | だが (`vocab:2055530`), in a section with exactly one item | mentioned in `les:n3-conectores-02` |

`les:n3-causa-06` is internally contradictory about this: its own intro says *"nos exemplos você revê
padrões já vistos, como **ですから** e その結果"* — and then lists ですから in the new-vocabulary block.

**Fix:** keep the entry (the SRS card is legitimate) but add the marker the corpus already uses
elsewhere — `les:n3-tempo-02` writes "você já viu na lição anterior", `les:n3-tempo-03` writes
"você já viu". One clause per row.

### E3 — The same word listed twice as new

Seven clean cases (homograph-queue items deliberately excluded):

- `les:n3-conectores-04`: `vocab:1586840` 或る — "(ある) = 'um certo, algum'. Como em 'um certo dia'."
  `les:n3-conectores-02` had already listed it with the identical gloss: "(ある) = 'um certo, algum'."
- `les:n3-conectores-03`: `vocab:1156410` 意外 "(いがい) = 'inesperado'" — listed in
  `les:n3-conectores-01` as "(いがい) = 'inesperado, surpreendente'".
- `les:n3-tempo-02`: 市 (`vocab:1308080`) — from `les:n3-conectores-05`.
- `les:n3-tempo-04`: いずれ (`vocab:1566210`) — from `les:n3-conectores-05`.
- `les:n3-perspectiva-03`: 御/お (`vocab:2826528`) "prefixo honorífico" — `les:n3-conectores-05` had
  "prefixo honorífico, o mesmo お de おちゃ e おみず".
- `les:n3-causa-03`: 音/おん (`vocab:2859161`) "som, ruído" — from `les:n3-conectores-05`.
- `les:n3-intencao-03`: 空/から (`vocab:1245280`) — from `les:n3-conectores-05`, which even gave it a
  dedicated l1-pitfall.

**Fix:** same as E2 — one "já visto" clause, or drop the repeat row.

### E4 — `les:n3-enfase-03`: the same vocab ref twice inside one list

```
<item>… <vocab ref="vocab:1287070"/> (こくみん) = "povo, cidadãos de um país".</item>
…
<item><vocab ref="vocab:1287070"/><text> aparece muito em notícias, ao lado de </text>
      <vocab ref="vocab:1285790"/><text> (こくふく) = "superação…"</text></item>
```

国民 occupies two of the fifteen bullets in a single list. The second bullet reads as if it were
introducing a new word and instead re-announces the first.
**Fix:** fold the 克服 entry into its own bullet and delete the duplicate 国民 anchor.

---

## Class F — verbatim duplication inside one lesson

### F1 — `les:n3-intencao-05`: the same sentence twice, ~200 characters apart

Paragraph opening the section:

> "Quem foge da 責任 acaba sendo culpado (責められる) por todos."

`l1-pitfall` closing the same section:

> "…enquanto 責める é um verbo (você 'culpa' alguém). **Quem foge da 責任 acaba sendo culpado
> (責められる) por todos.**"

Identical string. **Fix:** delete the standalone lead paragraph; the pitfall already carries the line
and gives it context.

### F2 — the 商 paragraph shared by deveres-03 and deveres-04

Covered in B2.

### F3 — the mnemonic boilerplate, three times

> `les:n3-intencao-01`: "Os mnemônicos acima são só uma rampa de entrada. Você fixa de verdade revendo
> esses kanji nas próximas lições e nos exercícios espaçados, não relendo a explicação."
> `les:n3-relato-01`: "Os mnemônicos acima são só uma rampa de entrada. Você **vai fixar** de verdade
> revendo esses kanji nas próximas lições e nos exercícios espaçados, não relendo a explicação."
> `les:n3-relato-02`: "Os mnemônicos são só a porta de entrada. A fixação real vem de reencontrar esses
> kanji nos exercícios e nas próximas lições, em intervalos crescentes."

Two are near-verbatim. It is also meta-commentary about the course's own SRS mechanics inside learner
prose, which no other tip in the slice does.
**Fix:** keep at most one instance (the relato-02 wording is the least mechanical), delete the others.

---

## Class G — headings that do not describe their contents

### G1 — Two pairs of lessons share a title; one pair shares its h2 as well

- `les:n3-relato-05` and `les:n3-relato-06` are both titled **"Relato, citação e definição"** *and*
  both open with `<heading level="2"><text>Relato, citação e definição</text></heading>` in relato-06
  (relato-05's h2 differs). In the topic index the learner sees the same entry twice in a row.
- `les:n3-estrutura-04` and `les:n3-estrutura-05` are both titled
  **"Nominalização, explicação e voz passiva"**.

**Fix:** retitle from each lesson's actual content — relato-06 is a は-row vocabulary batch
("Doutores, aplausos e o par はく"); estrutura-05 is descoberta/desenvolvimento/divulgação
("Descoberta, crescimento e divulgação", which is already its own h2).

### G2 — `les:n3-relato-07`: 木曜 filed under "Objetivos e metas"

```
### Objetivos e metas
Duas palavras muito próximas que vale separar:
 - 目的 (もくてき) - objetivo, propósito
 - 目標 (もくひょう) - meta, alvo concreto
 - 木曜 (もくよう) - quinta-feira (forma curta de 木曜日)
```

The heading announces two words and a contrast; a weekday is appended purely because it starts with
もく. **Fix:** move 木曜 out (see E1) and let the section be the two-word contrast it advertises.

### G3 — `les:n3-perspectiva-01`: "animais, sons e objetos" that are neither

> "Agora mais um grupo do cotidiano, com **animais, sons e objetos do dia a dia**:"
> atirar · gemer, resmungar · gargarejo · boi · cavalo · coelho · **curso superior de um rio** · uísque

上/かみ ("curso superior de um rio") is not an animal, a sound or an object — and it was already taught
in `les:n3-conectores-05`. ウイスキー is not a sound or an animal either. The real organizing principle
is the initial う, which the prose never states — unlike `les:n3-perspectiva-02`, which does say
*"Note como vários compartilham a leitura えい"*.
**Fix:** state the sound grouping ("palavras que começam com う") and drop the 上 repeat.

### G4 — `les:n3-perspectiva-03`: a false claim about which kanji writes the sound

> "Repare que vários nomes começam com o som えん, **escrito com o kanji 演** (apresentar-se, executar)"

Of the ten items that follow, 演技/演説/演奏 use 演; but **援助** uses 援, **エンジン** is katakana, and
**横断** is おうだん, not えん at all. 王/王様/王子 and 大家 are covered by the second half of the
sentence or not at all.
**Fix:** "vários começam com o som えん — em 演技, 演説 e 演奏 escrito com 演, em 援助 com 援 — e outros
giram em torno de 王 (rei)."

### G5 — `les:n3-perspectiva-07`: two headings that do not cover their lists

> "### Proveito, razão e esperteza" — contains 利益, 利口, 理解 (fits) **plus** 読み ("a leitura de um
> texto ou de um kanji") and よろしく ("manda lembranças").
> "### Previsão, sociedade e relações" — contains 予報, 予防, 世の中, 離婚, 嫁 (fits) **plus** 陸
> ("terra firme"), 来 (prefixo "que vem"), ライター ("escritor") and ラケット ("raquete").

The second is effectively a catch-all with a specific-sounding title.
**Fix:** split off "Palavras avulsas do bloco り/ら" for the four leftovers, as
`les:n3-conjectura-07` does with its "Mais palavras úteis" section.

### G6 — `les:n3-relato-05`: an item that admits it does not belong

> "- チーズ (queijo, do inglês 'cheese'). **Não tem nada a ver com 地**, mas é a hora de guardar mais um
> empréstimo do dia a dia."

The section is headed *"Lugar, posição e região"* and introduced as *"a família do kanji 地"*. The
author states in the item itself that it does not fit and includes it anyway.
**Fix:** move チーズ to a "Empréstimos do bloco ち" bullet outside the 地-family section, so the family
section stays coherent.

### G7 — `les:n3-relato-04`: a kanji bullet anchored on an already-taught kanji

> "- 晴… já vimos; aqui entra o parente **雪** 'neve': em cima o radical da chuva (雨): a chuva que vira
> gelo. 雪 = 'neve'."

Every sibling bullet in that list opens with the new kanji it teaches. This one opens with 晴, taught
in the immediately preceding lesson (`les:n3-relato-03`), and buries 雪 mid-sentence — so the list's
visual anchor is wrong and 雪 has no bullet of its own.
**Fix:** "- 雪 'neve': em cima o radical da chuva (雨)… parente de 晴, que você viu na lição passada."

### G8 — Three more mis-filed items

- `les:n3-intencao-02`: 火曜 ("terça-feira") sits in *"Vocabulário de empresa, regra e sociedade"*,
  alongside 企業, 管理, 議会, 環境.
- `les:n3-enfase-05`: *"Maioria e proporção"* contains 互い ("um ao outro") and 大戦 ("grande guerra"),
  neither of which is about majority or proportion; and *"Conectivos de contraste"* is a section with
  a single entry (だが).
- `les:n3-causa-07`: *"Sentimentos e impressões"* contains 無事 ("estar são e salvo"), which is a state,
  not a sentiment.

### G9 — `les:n3-conectores-06`: the title names two sound families, the lesson has three

> TITLE: "Do almoço à comunicação: palavras com **ちゅう e つう**"

The middle block is entirely ちょ/ちょう — 調査, 調子, 貯金, 長期, 長大, 頂上, 著者, 直接 — plus 遂に
(ついに). The description gets it right; the title does not.
**Fix:** "palavras com ちゅう, ちょう e つう".

### G10 — `les:n3-conjectura-04`: 13 new kanji under a heading that calls them revision

> "### Kanji de ação e emoção (**um grande bloco de revisão**)"

The lesson unlocks 13 of the 14 kanji presented (抱 息 恐 痛 欲 探 束 戻 越 逃 犯 君 閉 — only 遠 is
older). Calling a first introduction "revisão" tells the learner not to study them.
**Fix:** "Kanji de ação e emoção (bloco grande — volte a ele nas revisões)".

### G11 — `les:n3-perspectiva-05`: an N5 particle taught as filler, plus a build artifact

> "### Partícula で e itens restantes
> Falta apresentar uma palavra-ferramenta e fechar o vocabulário da lição.
> - で - em, no, na (marca o lugar onde uma ação acontece).
> …
> Repare que で aqui marca *onde* a ação acontece (no mar), e a frase ainda usa 釣り, a pescaria.
> **Com isso, você já viu as dezessete palavras desta lição.**"

Three problems in one section: (a) the heading "itens restantes" and the line "Falta apresentar…"
describe the lesson's own construction, not its content; (b) で marking location is N5 material, given
a dedicated section at N3; (c) *"Com isso, você já viu as dezessete palavras desta lição"* is a
word-count bookkeeping note addressed to the author, not the learner.
**Fix:** delete the section; fold で into the 釣り example as a one-clause reminder, and drop the
counting sentence.

---

## Class H — explanations that are wrong or unusable as written

### H1 — `les:n3-concessao-01`: the opening example contains no ても

Raw body, first paragraph:

```
<p><text>Você já viu o </text><jp>ても</jp><text> em formas como </text>
<jp reading="いいですか">いいですか</jp><text> ('pode? / tudo bem se?')…
```

いいですか by itself is "está bom?" and contains no ても. The form the learner met at N4 is
**〜てもいいですか**. As printed, the lesson's very first sentence makes a false claim about the pattern
it is introducing.
**Fix:** `<jp reading="てもいいですか">〜てもいいですか</jp>`.

### H2 — `les:n3-concessao-02`: an incomplete formation rule pointing at the wrong particle

> "A montagem é como a do **の**: verbo simples + くせに, adjetivo-な + な + くせに, substantivo + の +
> くせに."

Two defects: (a) "como a do の" is meaningless — the intended comparison is **のに**, the neutral
"apesar de" the same note contrasts くせに with two sentences later; (b) the rule omits the
い-adjective (高いくせに), which the learner will need.
**Fix:** "A montagem é a mesma de のに: verbo simples + くせに, adjetivo-い + くせに, adjetivo-な + な +
くせに, substantivo + の + くせに."

### H3 — `les:n3-estrutura-02`: a "minimal pair" made of the same string twice

```
<p><text>こと combina bem com palavras de aprendizado e de estado. Note os pares mínimos de duração:
しょう (curto) versus しょう longo muda a palavra inteira.</text></p>
```

The identical string しょう is labelled both "curto" and "longo". Nothing is being contrasted, the
sentence has no working predicate ("versus しょう longo **muda** a palavra inteira"), and the learner
is pointed at a distinction that is not on the page. The list that follows does contain a real
duration pair — **上達 (じょうたつ)** vs **状態 (じょうたい)** share じょう, and **症状 (しょうじょう)**
vs **少々 (しょうしょう)** are a genuine しょ/しょう contrast.
**Fix:** "Note o par de duração: 少々 (しょうしょう, 'um pouco') tem quatro moras longas, enquanto
処理 (しょり) tem só duas curtas — a vogal longa muda a palavra inteira."

### H4 — `les:n3-conectores-03`: 相 in 首相 glossed as "mútuo"

> "Aparece em 首相 ('primeiro-ministro', a '**cabeça mútua**' do governo, com o 相 que você já viu)."

The 相 of 首相 (and of 外相, 蔵相) is the "minister / aide" sense, not the 相 = "mútuo" the same lesson
family taught in conectores-01. Presenting 首相 as "cabeça mútua" teaches a wrong reading of the
compound, and the cross-reference makes the error look authoritative.
**Fix:** "Aparece em 首相 ('primeiro-ministro'): 首 é 'cabeça' e este 相 tem o sentido de 'ministro,
auxiliar' — outro uso do kanji que você viu como 'mútuo' em 相手."

### H5 — `les:n3-causa-05`: the same example sentence, respelt into a hyōgai kanji

`les:n3-causa-01` teaches せいで with:

> 「雨の**せい**で試合が中止になった」 — "o jogo foi cancelado por causa da chuva"

`les:n3-causa-05` reprints the identical sentence as:

> `<jp reading="あめのせいでしあいがちゅうしになった">雨の**所為**で試合が中止になった</jp>`
> (Por culpa da chuva, o jogo foi cancelado.)

所為 is a rare ateji form that essentially never appears in modern writing; the learner who memorised
かな four lessons ago now meets the same sentence in a spelling nobody uses, with no note explaining
the change.
**Fix:** print 雨のせいで in the example and, if the 所為 form is worth showing, mention it in the gloss
line for `vocab:1610040` ("escreve-se quase sempre em kana; a grafia 所為 é rara").

### H6 — `les:n3-conectores-05`: two examples printed in kanji forms nobody writes

> 「**偖**、次の話に移りましょう」 (Pois bem, vamos passar ao próximo assunto.)
> 「**何れ**にしても決定は明日だ」 (De qualquer forma, a decisão fica para amanhã.)

偖 is a hyōgai kanji for さて; 何れ for いずれ is likewise almost always written in kana. The same
lesson explicitly warns about exactly this for こんにちは — *"É a saudação clássica e escreve-se quase
sempre em hiragana; a grafia 今日は é rara"* — but then prints 偖 and 何れ without the equivalent note.
**Fix:** write さて and いずれ in kana in the examples, keeping the kanji forms (if wanted) in the gloss
line with the same "grafia rara" caveat already used for 今日は.

### H7 — `les:n3-causa-07`: a generated example that stacks two synonyms

> 「明日の試験が**心配**で、**不安**で眠れなかった」
> (Preocupado com a prova de amanhã, não consegui dormir de tanta ansiedade.)

心配 and 不安 mean the same thing here, and chaining two て-form causes on one predicate is not how a
native would build the sentence. The lesson is teaching 不安, so the first clause is redundant padding.
**Fix:** 「明日の試験が不安で眠れなかった」 — "Fiquei sem dormir de ansiedade por causa da prova de
amanhã."

---

## Class I — register and locale slips in learner-facing pt-BR

### I1 — `les:n3-desejos-03`: an unfortunate collision in a pronunciation note

> "Armadilha PT: くう tem duas vogais, duas batidas: 'ku-u', não um '**cu**' curto."

In pt-BR, *cu* is a vulgar word for anus. Printing it in quotation marks in a learner-facing
pronunciation note is a register failure specific to this locale, and `design/translation_style.md`
asks that genuinely vulgar items be flagged rather than produced. Every other mora note in the slice
uses the hyphenated romanisation without a Portuguese sound-alike.
**Fix:** "くう tem duas vogais, duas batidas: 'ku-u'. Não colapse as duas num só tempo; segure a
segunda batida."

### I2 — `les:n3-desejos-07`: English "batch" in the lesson's own h2

> `<heading level="2"><text>Lar, corpo e natureza: o **batch** ho</text></heading>`

The title says "o bloco ほ", the description says "leitura ho", and the h2 says "o batch ho". Three
labels for one thing, one of them an untranslated English word in the largest heading on the page.
**Fix:** "Lar, corpo e natureza: o bloco ほ" (matching the title).

### I3 — `les:n3-tempo-08`: "Vamos por clusters"

> "No meio ainda entram algumas palavras do dia a dia. **Vamos por clusters.**"

The corpus's own idiom for this move is Portuguese: `les:n3-conectores-06` writes *"Vamos por blocos
para facilitar"*, `les:n3-concessao-07` and `les:n3-estado-08` write *"Vamos por grupos"*.
**Fix:** "Vamos por blocos."

### I4 — `les:n3-estado-02`: an untranslated English gloss

> "Aparece em 放送 ('transmissão, **broadcast**')."

**Fix:** "('transmissão, radiodifusão')" or "('transmissão de rádio ou TV')".

### I5 — Missing space before an opening parenthesis (3 occurrences)

- `les:n3-conectores-06`: "almoço, a refeição do meio-**dia(mais** formal que 昼ごはん)"
- `les:n3-estado-02`: heading "Vocabulário do **dia(em** kana)"
- `les:n3-estado-03`: heading "Vocabulário do **dia(em** kana)"

`les:n3-estado-01` and `-04` get the same heading right ("Vocabulário do dia (em kana)").
**Fix:** insert the space.

---

## Class J — pedagogy: uneven treatment inside a single lesson

### J1 — `topic-46-limites` 01–04: vocabulary lists with no readings, next to instructions that need them

`les:n3-limites-01` presents its fourteen new words as bare glosses:

> "Pratique a leitura em voz alta, batendo uma palma por mora:
>  - tendência, propensão. · aviso, advertência. · cálculo, conta. · aviso, cartaz (afixado). …"

No kana anywhere. The learner is told to clap one beat per mora for words whose readings the page does
not show, and the checklist then asserts *"Reconheço a leitura dos sete kanji e dos quatorze vocábulos
novos."* The same shape recurs in limites-02 (*"Muitos termos de hoje começam com けつ ou けっ; preste
atenção ao っ"* — with no readings to check that against), limites-03 (*"Repare em quantos termos
começam com 現 ou 検"*, plus a tip naming a けんとう pair the list never spells) and limites-04
(*"Vários termos de hoje se leem こうか"*).

Contrast the house style used everywhere else in n3 — `les:n3-estado-01`, `les:n3-intencao-01`,
`les:n3-tempo-05`, `les:n3-conjectura-05` all print "(kana) = gloss" per row.
**Fix:** add the kana to the four limites lists, matching the sibling lessons; the sound-grouping
claims and the clap-per-mora instruction only work once the readings are visible.

### J2 — Kanji dumped without treatment at the end of a section

A recurring shape: the first two or three kanji in a section get a component decomposition and an
example compound; the remainder are chained into one run-on sentence with a meaning and nothing else.

- `les:n3-enfase-01`: "O kanji 亡 significa 'falecido, perecer'. O kanji 舞 significa 'dança'… O kanji
  婦 … E o kanji 寄 …" — **亡 gets no example word at all**, four kanji in one paragraph after three
  full treatments.
- `les:n3-desejos-04`: **nine** of fourteen kanji dispatched in two sentences — "Mais cinco para a sua
  coleção: 横…; 深…; 光…; 路…; e 太…. E quatro do mundo do estudo e do clima: 科…; 師…; 客…; e 候…."
- `les:n3-concessao-01`: the tail four are strung on a manufactured semantic link — "O 倒 …, o 押 …, O
  散 … e o 欠 … completam a leva: **por mais que se empurre ou se espalhe, algo sempre pode faltar.**"
  That sentence invents a relationship between 倒/押/散/欠 that does not exist and will mislead anyone
  who tries to use it as a mnemonic.
- Also `les:n3-enfase-03` (妻, 背, 険, 頼), `les:n3-enfase-04` (途, 許, 便),
  `les:n3-perspectiva-01` (予: "Aparece em palavras de planejamento, como adiar algo previsto" — no
  component, no example word), `les:n3-estado-01` (局: meaning + one compound, no decomposition),
  `les:n3-intencao-01` (声: "a voz com que a gente diz o que pensa. Em 声 ('voz')" — the example word
  is the kanji itself).

**Fix:** give every kanji in a "Kanji novos" section the same minimum the majority already get — one
component observation plus one example compound — and drop the invented connective in concessao-01.

---

## Count table

**Checked:** 101 lesson bodies (all of `course/n3`), 644,643 characters.

| Class | What | Lessons affected | Findings |
|---|---|---:|---:|
| A | pt-BR diacritics stripped in body prose | 4 | 4 |
| B | Broken / missing markup reaching the learner | 12 | 8 |
| C | Lesson introduces material it never teaches | 12 | 7 |
| D | Numeric claims contradicted by `unlocks` | 5 | 5 |
| E | Already-taught material presented as new | 26 | 4 |
| F | Verbatim duplication inside a lesson | 5 | 3 |
| G | Headings that do not describe their contents | 15 | 11 |
| H | Explanations wrong or unusable as written | 7 | 7 |
| I | Register / locale slips in pt-BR | 7 | 5 |
| J | Uneven pedagogical treatment inside a lesson | 12 | 2 |
| **Total** | | **≈62 distinct lessons** | **56** |

Counts in the "Findings" column are numbered items; several items (E1, E2, E3, D1–D4, G8, I5, J1, J2)
aggregate a table of instances, so the number of individual repair sites is higher — roughly 190,
of which ~120 are the Class A diacritic restorations in four lessons.

**Highest-value repairs, in order:**

1. **C1** — the 25 untaught kanji in `topic-41-causa` 01–04. This is the only finding in the slice
   where the learner receives SRS cards for material that has no teaching at all anywhere in the
   course, and it silently breaks `les:n3-relato-01`'s introduction of 示 downstream.
2. **Class A** — four lessons of accent-stripped prose, at the very start of n3, i.e. the first thing
   an N3 learner reads. Mechanical to fix and highly visible.
3. **B1/B2/B3** — three places where a headword or kanji simply does not render.
4. **E1** — 日本, 週, 意味 and seven weekday words taught as new N3 vocabulary.
5. **H1/H2/H3** — three explanations that are false or empty as written, each in the opening move of
   its section.

**Not defects, checked and cleared** (recorded so the next pass does not re-open them): no em dashes
anywhere in n3 bodies; no pt-PT forms; no backslashes, mojibake, HTML entities misuse, or smart-quote
mixing; no QA-instruction leaks; `gram:n3-mo` is a badly named slug but its `label` renders correctly
as "não só… como também (ばかりか… も)"; `vocab:1610340` (長大) is glossed correctly in
`les:n3-conectores-06`; the "Repare em … " glue in `les:n3-deveres-06` and `les:n3-limites-01` is a
rendering artefact of the review tooling, not of the corpus.
