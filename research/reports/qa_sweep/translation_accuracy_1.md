# QA sweep: translation accuracy, part 1/6

**Slice:** `corpus/sentences/bank.json`, records where `index % 6 == 0`.
**Records checked:** 982 of 5889 (every one read in full, not sampled).
**Scope:** `translation["pt-BR"]` fidelity to `jp`; `translation_literal["pt-BR"]` as a structural gloss;
token `gloss`/`role`/`conjugation_note` (pt-BR) against the token's meaning in context.
**Excluded by instruction:** `structure_explanation` (being re-authored elsewhere). Not reviewed, not reported.
**Style authority:** `design/translation_style.md`.

Slice composition: 369 `ai-generated`, 21 `jec:*`, 592 `tatoeba:*`.

Defect density is heavily skewed. The `ai-generated` block (indices 0 to 2210) is 37.6% of the slice but
carries 69 of the 156 flags. The Tatoeba block is 60.3% of the slice and carries 79 flags, **but 59 of those
are the single ingestion defect in Class E**; only 20 Tatoeba records have an actual content defect. Reviewer
effort is best spent on the generated block and on one broken ingestion path.

---

## Clean bill on the things I checked mechanically and found nothing

Reported so the reviewer does not re-spend effort here:

- **pt-PT leakage: zero.** Scanned for `comboio, autocarro, telemóvel, casa de banho, rapariga, ecrã,
  pequeno-almoço, sumo, gelado, apelido, aluguer, equipa, desporto, fato (= terno), estar a + inf, vós, consigo
  (= com você), miúdo, rebuçado` across `translation`, `translation_literal`, token glosses and particle notes.
  Every hit was a pt-BR false positive (`consigo` = "I manage", `fato` = "fact", `papel` = "paper").
- **Em dash (`—`): zero occurrences** anywhere in the pt-BR fields of the slice. Style §4 is being honoured.
- **`translation` never equals `translation_literal`:** 0 records. The two fields are genuinely doing
  different jobs (Style §1).
- **`translation["pt-BR"]` / `translation_literal["pt-BR"]` empty: 0 records.**
- **Generated JP carrying `。` or trailing `、`: 0 records.** Style §3 is being honoured on the generated set.
- **"Quanto a…" leaking into the *natural* translation:** 5 regex hits, all false positives
  (comparative `tanto quanto` / `enquanto`). Style §1 is being honoured.
- **`その` / `あの` mis-rendered as `este/esta`: 0 records** (the demonstrative problem runs one way only, see Class B).

---

## Class A. `translation_literal` applies the は topic scaffold to a chunk that carries no は

**39 records.** The literal field opens (or continues) with `Quanto a X`, the corpus's standard gloss for
topic-は, on a chunk marked `が`, `を`, `に`, `で`, or bare. This is exactly the が/は distinction the literal
field exists to teach, so the scaffold actively misteaches it. In five records the gloss **contradicts itself
inside the same string**, printing the correct case label in parentheses right after the topic scaffold.

Self-contradicting (fix these first):

| id | jp | current `translation_literal["pt-BR"]` |
|---|---|---|
| `sent:gen-08b990158640` | 名前をひらがなで書いてください | `Quanto ao nome (objeto), em hiragana, escreva por favor.` |
| `sent:gen-4bc727e212ae` | 部屋の電灯をつけてください | `Quanto à luz do (の) quarto (を), acenda (てください) por favor.` |
| `sent:gen-bdec0e3d1e59` | この文法がよく分からない | `Quanto a esta gramática (sujeito), bem não compreendo.` |
| `sent:jec-0749` | 自分がそういう扱いを受ける | `Quanto a si mesmo (が), assim dizer (= esse tipo de) tratamento (を) receber.` |
| `sent:gen-e443ac74a70b` | ホテルの予約をしたい | `Quanto ao hotel-de reserva (objeto) fazer quero.` |

`sent:gen-e443ac74a70b` is additionally ungrammatical as Portuguese ("Quanto ao hotel-de reserva … fazer quero").

Remaining 34:

| id | jp | current `translation_literal["pt-BR"]` |
|---|---|---|
| `sent:gen-03cd34ccfb50` | 天気予報が当たらなかった | `Quanto à previsão do tempo, não acertou (no alvo).` |
| `sent:gen-273cffc1f6f8` | 砂糖を百グラム入れます | `Quanto ao açúcar, cem gramas, coloco/coloca.` |
| `sent:gen-2f1479d86cbf` | 入り口がわからない | `Quanto à entrada, (eu) não sei/não entendo.` |
| `sent:gen-326ea97de1a1` | 今日のほうが昨日より暑い | `Quanto a hoje (o lado de hoje), em comparação com ontem, está quente.` |
| `sent:gen-32d8debc75a0` | 電車に忘れ物をしました | `Quanto a (no) trem, uma coisa esquecida fiz.` |
| `sent:gen-341f2978c261` | 家族のなかで母が一番早く起きます | `Quanto a dentro da família, a mãe (sujeito) número um cedo acorda.` |
| `sent:gen-4e408374873b` | お客様がもう来ました | `Quanto ao cliente, já veio.` |
| `sent:gen-55122228375c` | 卵を九つください | `Quanto a ovos, em número de nove, dê (por favor).` |
| `sent:gen-5dd4e7c0e137` | この作文をもう一度書きなおす | `Quanto a esta redação, mais uma vez escrevo-de-novo.` |
| `sent:gen-60242f5d110e` | 椅子が一つ足りない | `Quanto a cadeira(s), uma (delas) não basta / está faltando.` |
| `sent:gen-633db27a84d8` | 日本語の勉強が好きです | `Quanto ao estudo de japonês, (ele) é gostado.` |
| `sent:gen-64fec9fcc687` | 係の者がご案内いたします | `Quanto à pessoa do encargo (sujeito), faz o acompanhamento (humildemente).` |
| `sent:gen-665a24486296` | 肉がちょうどよく焼けた | `Quanto à carne, ela assou exatamente bem.` |
| `sent:gen-6e5337d59331` | 駅の前に自転車がたくさんある | `Quanto à frente da estação, bicicletas em grande quantidade existem.` |
| `sent:gen-717264b0f0fe` | この店のほうがあの店より安い | `Quanto ao lado desta loja, em comparação com aquela loja, é barata.` |
| `sent:gen-7395acd7c279` | 床がぬれていて滑りやすいです | `Quanto ao chão, está molhado e é fácil de escorregar.` |
| `sent:gen-7d04150c6af1` | 西洋の文化に興味があります | `Quanto à cultura do ocidente, há interesse.` |
| `sent:gen-7ff3da2ccb55` | 毎日文法を勉強している | `Quanto a (cada) dia, gramática (objeto) estou estudando.` |
| `sent:gen-87c6cd60970e` | 赤ちゃんがよく寝ている | `Quanto ao bebê, bem está dormindo.` |
| `sent:gen-b76ff6005aca` | 音を小さくしてください | `Quanto ao som, faça-o pequeno, por favor.` |
| `sent:gen-b882bdc9d230` | 外がうるさくて寝られない | `Quanto ao lado de fora ser barulhento, não consigo dormir.` |
| `sent:gen-d4a16635f7bd` | 子供たちの踊りが上手です | `Quanto à dança das crianças, é habilidosa.` |
| `sent:gen-de693fb350bb` | 公園で子どもたちが遊んでいた | `No parque (で), quanto às crianças (が), brincar-estavam (遊んでいた).` |
| `sent:gen-dfb7a333aaae` | 星の光が空に見えます | `Quanto à luz das estrelas, no céu, é visível.` |
| `sent:jec-0174` | 専門業者が工事をします | `Quanto às empresas especializadas, elas fazem a obra.` |
| `sent:jec-1365` | ２つの原因が考えられます | `Quanto a duas causas, (elas) podem ser pensadas/consideradas.` |
| `sent:jec-2121` | すぐに目の色が変わった | `Imediatamente, quanto à cor dos olhos, mudou.` |
| `sent:jec-2441` | 彼がずっとパソコンに向かいます | `Quanto a ele, o tempo todo, ao computador, se volta.` |
| `sent:jec-2739` | 彼が３０日と２２日の２度、会場に足を運びました | `Quanto a ele, nas 2 vezes …` |
| `sent:tatoeba-1187703` | 口の周りにケチャップがべったり付いてるよ。 | `Quanto à volta da boca, o ketchup está grudado bem grudado, viu.` |
| `sent:tatoeba-3496943` | クッキーをお一つどうぞ。 | `Quanto ao biscoito, (pegue) um, por favor.` |
| `sent:tatoeba-80981` | 眠りが浅いんだ。 | `Quanto a (meu) sono, ele é raso, é que (é assim).` |
| `sent:tatoeba-83206` | 歩き方がとてもゆっくりだね。 | `Quanto ao jeito de andar, é muito devagar, né.` |
| `sent:tatoeba-84914` | 布団をはがされた。 | `Quanto ao futon, foi arrancado/descoberto (sobre mim).` |

**Fix (uniform):** reserve `Quanto a X` for chunks actually marked は (the corpus already does this correctly in
266 records). For the others use the corpus's own case scaffolds, which already exist elsewhere in the same
field: `X (sujeito)` for が, `X (objeto)` for を, `Em/No X` for に/で, bare fronting for adverbials. Examples:
`sent:gen-03cd34ccfb50` to `A previsão do tempo (sujeito) não acertou (no alvo).`;
`sent:gen-08b990158640` to `O nome (objeto), em hiragana, escreva por favor.`;
`sent:gen-7ff3da2ccb55` to `Todo dia, gramática (objeto) estou estudando.`

**Deliberately not flagged** (checked and cleared): `sent:gen-b98b16f88804`, `sent:tatoeba-142578`
(`Quanto a (eu)` / `Quanto a [eu]` glosses a genuinely elided 私は and marks the が separately);
`sent:gen-5412a2ccf468`, `sent:tatoeba-10556983`, `sent:tatoeba-11706794` (って **is** a colloquial topic marker);
`sent:gen-34e4275eaee4` (について genuinely means "quanto a"); `sent:gen-9aa5ef9c9efc`, `sent:gen-d5ceaef195f2`,
`sent:tatoeba-10638045` (borderline, defensible as written).

---

## Class B. `この` rendered as "esse/essa" against the corpus's own convention

**13 records.** In this slice 33 records render `この` as `este/esta` and 13 as `esse/essa`; `その`/`あの` are
never rendered `este/esta` (0 records). So there is a convention (`この`→este, `その`→esse, `あの`→aquele) and
these break it. Several of the affected sentences exist to teach demonstratives, and the token gloss in the
same record usually says `este/esta`.

| id | jp | current `translation["pt-BR"]` |
|---|---|---|
| `sent:gen-011e9f3612bd` | この花はきれいな色だね | `Essa flor tem uma cor bonita, né?` |
| `sent:gen-34e4275eaee4` | この問題について考えましょう | `Vamos pensar sobre esse problema.` |
| `sent:gen-40282ab22e94` | この大きい荷物が邪魔だ | `Essa bagagem grande está atrapalhando.` |
| `sent:gen-4a5e54f140ad` | この番組はとても面白い | `Esse programa é muito interessante.` |
| `sent:gen-7e1666c42c97` | この店に売っていない物はない | `Não tem nada que essa loja não venda.` |
| `sent:gen-8ccaa5707b78` | この空港はとても国際的です | `Esse aeroporto é muito internacional.` |
| `sent:gen-8e746032b6f1` | このテープはよく付く | `Essa fita cola bem.` |
| `sent:gen-a91dc950f66d` | この糸はとても細い | `Esse fio é bem fininho.` |
| `sent:gen-b2484d35484c` | この店は安い　それに料理もおいしい | `Essa loja é barata, e ainda por cima a comida é gostosa.` |
| `sent:gen-c5b1d156f19e` | この歌をすぐに覚えた | `Aprendi essa música rapidinho.` |
| `sent:gen-f61dd9927146` | この町は古いお寺の一つで知られている | `Essa cidade é conhecida por ter um dos templos antigos.` |
| `sent:tatoeba-221479` | この質問は答えにくいな。 | `Essa pergunta é difícil de responder, né.` |
| `sent:tatoeba-74693` | このような仕事で… | `Num trabalho como esse, …` (weakest of the set) |

**Fix:** swap `esse/essa` for `este/esta` in the 12 solid cases. `sent:gen-011e9f3612bd` becomes
`Esta flor tem uma cor bonita, né?`, and so on. `sent:tatoeba-74693` (`como esse`) is idiomatic and can stay
if the reviewer prefers; flagged only for the record.

---

## Class C. `好き` / `上手` / `下手` literal glosses use non-Portuguese words or attach the skill to the wrong noun

**9 records.** Two distinct problems, same grammar point.

**C1: "gostável" / "é gostado" are not Portuguese.** `gostar` is intransitive with `de` and has no passive of
this kind; `gostável` is not a word. A learner-facing field must not coin one.

| id | jp | current `translation_literal["pt-BR"]` | proposed |
|---|---|---|---|
| `sent:gen-2cb3eb5c2174` | 妹はチェックのスカートが好きです | `… saia xadrez é gostável.` | `… a saia xadrez (が) é do agrado dela.` |
| `sent:gen-633db27a84d8` | 日本語の勉強が好きです | `… (ele) é gostado.` | `O estudo de japonês (が) me agrada.` |
| `sent:gen-ac667d984f26` | どんな果物が好きですか | `Que tipo de fruta (が, sujeito), gostável é (か, pergunta)?` | `Que tipo de fruta (が, sujeito) lhe agrada (か, pergunta)?` |
| `sent:tatoeba-98744` | 彼らがみんな好きだ。 | `Eles todos (são) gostáveis.` | `Eles todos (が) me agradam.` |

**C2: `上手` glossed as "habilidoso" attached to the thing, not the person.** A koto, a dance and a composition
cannot be "habilidosos"; the skill belongs to the person. This is a real semantic error, not just clumsy style.

| id | jp | current `translation_literal["pt-BR"]` | proposed |
|---|---|---|---|
| `sent:gen-25add39dbdc9` | 母は琴がとても上手だ | `Quanto à mãe, o koto é muito habilidoso.` | `Quanto à mãe, no koto (が) ela é muito boa.` |
| `sent:gen-d4a16635f7bd` | 子供たちの踊りが上手です | `Quanto à dança das crianças, é habilidosa.` | `A dança das crianças (が) é bem feita.` |
| `sent:gen-3193f52197b2` | この作文はとても上手です | `Quanto a esta redação, é muito habilidosa/boa.` | `Quanto a esta redação, está muito bem feita.` |
| `sent:gen-1ea65c87d885` | あねは うたを うたうのが じょうずです | `… o ato de cantar canções é habilidoso (nela).` | `… no ato de cantar canções (が) ela é habilidosa.` |
| `sent:gen-4ec770164246` | かれは サッカーを するのが じょうずです | `… o ato de jogar futebol é (algo em que ele é) habilidoso.` | `… no ato de jogar futebol (が) ele é habilidoso.` |

The last two already carry a repair in parentheses, which is evidence the author noticed the problem and
patched it rather than restructuring.

---

## Class D. Plain non-past declarative rendered as a bare infinitive

**5 records.** `translation` is not a sentence; it is a dictionary citation. The corpus renders the identical
JP form (plain non-past, no imperative marker, no ください) three different ways, so this is an internal
inconsistency, not a house style.

| id | jp | current `translation["pt-BR"]` | `translation["en"]` in the same record |
|---|---|---|---|
| `sent:gen-30b970cffa4a` | テープで箱を閉じる | `Fechar a caixa com fita.` | `Close the box with tape.` (imperative) |
| `sent:gen-56d495bbcf16` | 電話で席を予約する | `Reservar a mesa por telefone.` | `Reserving the table by phone.` (gerund) |
| `sent:gen-7ea63d9fd0ad` | コップに水を入れる | `Pôr água no copo.` | `Pour water into the glass.` (imperative) |
| `sent:gen-c19dfc37c744` | 壁にポスターを張る | `Colar um pôster na parede.` | `Stick a poster on the wall.` (imperative) |
| `sent:gen-db21e4d29aa3` | 紅茶にミルクを入れる | `Colocar leite no chá preto.` | `Put milk in the tea.` (imperative) |

The same JP shape is rendered elsewhere as 1st-person present (`sent:gen-13fbaa8b7ba5` `Toda manhã eu faço
exercício.`; `sent:gen-b8f8abb7b718` `Lavo as mãos antes de comer.`; `sent:gen-d8fc7b3bed50` `Compro marmita
na lojinha de conveniência.`) and as an imperative (`sent:gen-c43da4e362a6` `Coloca os pratos na mesa.`;
`sent:gen-f1adee2c6681` `Vou esquentar a sopa.`).

**Fix:** pick one and apply it. The 1st-person present is the majority behaviour and the only one that does not
invent a mood the JP does not carry: `Fecho a caixa com fita.`, `Reservo a mesa por telefone.`,
`Ponho água no copo.`, `Colo um pôster na parede.`, `Coloco leite no chá preto.`

Related single record, same root cause but the other direction: `sent:gen-273cffc1f6f8` 砂糖を百グラム入れます
is rendered `Coloque cem gramas de açúcar.` A polite declarative (`入れます`, no `てください`) is turned into a
directive. The record's own literal hedges (`coloco/coloca`), which shows the ambiguity was noticed.
Proposed: `Coloco cem gramas de açúcar.`

---

## Class E. Layer-A English missing on 59 records (342 across the whole bank)

**59 of 982 records (6.0%) have `translation["en"]` empty or null**, and 57 also have
`translation_literal["en"]` empty. Inside those records, **267 token glosses carry a pt-BR meaning with an
empty `en`**.

This is not a cosmetic gap. Per `CLAUDE.md` §1.1 and the export contract, `en` is the Layer-A source the pt-BR
is machine-validated against (spec §7). Where it is absent there is nothing to validate the pt-BR against,
and a human reviewer has no anchor either. Every record in the slice with `provenance.pt_source = "ai"` and no
`en` is effectively an unverifiable AI translation.

Precise correlation:

- **57 of the 59** carry `tags: ["mined", "stage:"]`, `src = "tatoeba"` with **no Tatoeba id**, and
  `translation_confidence = 0.8` (the rest of the corpus uses 0.85). Every `mined` record in the slice
  (57/57) lacks `en`. So the defect tracks the `mined` ingestion path, not individual records.
- **2 are ordinary Tatoeba records that simply lost their `en`:** `sent:tatoeba-203508`
  (`たとえ家を出る事になっても事業は続ける。`, tags `top:n4-potencial,続ける`, `translation_literal["en"]` **is**
  present) and `sent:tatoeba-77973` (`両方とも好きというわけではない。`, tags `top:n3-conjectura,n3-wake-dewa-nai`).
  These two are recoverable one-off fixes and should not be lumped with the `mined` batch.

Index range in the slice: 4062 to 5592, i.e. the entire tail of the Tatoeba block.

**Fix:** re-run the `mined` ingestion with English capture enabled, or backfill `en` from the Tatoeba pairs;
until then these 342 records should not be treated as machine-validated. The two non-`mined` records can be
patched individually.

---

## Class F. Explanatory parentheses inside the *natural* translation

**13 records.** Style §5 assigns explanation to other fields; `translation` must read like something a
Brazilian would actually say, and a parenthetical gloss does not. In several cases the parenthesis carries
content that is not in the JP at all.

| id | jp | current `translation["pt-BR"]` | note |
|---|---|---|---|
| `sent:gen-044427f1a26f` | 今日は大勢の客が来た | `Hoje veio muita gente (muitos clientes).` | gloss of 客, not speech |
| `sent:gen-e12e2080fb55` | 社長はこの本をお読みになりますか | `O senhor (presidente) vai ler este livro?` | gloss of 社長 |
| `sent:gen-ea5b2165dd9a` | 彼は私の二年先輩だ | `Ele é meu veterano, dois anos à minha frente (na escola/trabalho).` | encyclopedic note on 先輩 |
| `sent:tatoeba-11149258` | 手袋が濡れちゃった。 | `Minhas luvas ficaram molhadas (que pena).` | ちゃった nuance parked in a parenthesis |
| `sent:tatoeba-123440` | 特別料理がございますが。 | `Nós temos um prato especial (para o senhor)…` | "para o senhor" is in the en, not the jp |
| `sent:tatoeba-147830` | 縮小コピーを撮ってくるよ。 | `Vou tirar umas cópias reduzidas (e já volto).` | てくる nuance parked in a parenthesis |
| `sent:tatoeba-4835` | バカな質問があるんだ。 | `Tem uma pergunta boba (que eu quero fazer).` | added content |
| `sent:tatoeba-76813` | …すぐに車を出してください。 | `… por favor saia (arranque) imediatamente.` | synonym pair |
| `sent:tatoeba-77775` | …うるさくていらいらする。 | `O rádio da casa do vizinho é barulhento e (isso) me irrita.` | pronoun in parentheses |
| `sent:tatoeba-84658` | 父はまもなく元気になるだろう。 | `Meu pai logo vai melhorar (ficar bom de saúde).` | synonym pair |
| `sent:tatoeba-84914` | 布団をはがされた。 | `Tiraram o meu futon (o cobertor/colchão) de mim.` | gloss of 布団 |
| `sent:tatoeba-8775094` | お箸で食べるのは難しいですか？ | `É difícil comer com hashis (pauzinhos)?` | gloss of 箸 |
| `sent:tatoeba-993622` | 私はタルティーヌはジャムを塗って食べる。 | `Eu como a tartine passando geleia (nela).` | pronoun in parentheses |

**Fix:** move the parenthetical content to the token `gloss` (for word explanations: 客, 先輩, 布団, 箸) or to
`translation_literal` (for grammatical nuance: ちゃった, てくる), and let `translation` stand alone.
`sent:gen-044427f1a26f` becomes `Hoje veio muito cliente.`; `sent:tatoeba-11149258` becomes
`Acabei molhando as luvas.`

**Cleared, not defects:** `sent:tatoeba-9524565` (`preocupado(a)`) and `sent:tatoeba-9559301` (`obrigado(a)`)
use parentheses for gender agreement, which is standard pt-BR. `sent:tatoeba-124653`, `sent:tatoeba-212580`,
`sent:tatoeba-188217` put real JP content (`切らずに`, `そのまま`, `たまま`) in parentheses; style-questionable
but not a fidelity defect.

---

## Individual findings

### High (meaning is wrong or the taught point is lost)

**1. `sent:gen-68abf4e67d15` — "reservar o restaurante" means renting the whole venue**
- jp: `レストランを予約した` / pt: `Reservei o restaurante.` / en: `I made a reservation at the restaurant.`
- In pt-BR, "reservar o restaurante" means booking out the establishment. `予約する` here is booking a table.
  The record's own `en` says "made a reservation **at** the restaurant".
- Fix: `Fiz uma reserva no restaurante.`

**2. `sent:gen-960d7cee0887` — causal direction of 〜とみえて is inverted**
- jp: `彼は忙しいとみえて、返事が来ない` / pt: `Pelo visto ele está ocupado, porque não responde.`
- `〜とみえて` states an inference and then its **consequence**: he must be busy, *so* no reply comes. The pt
  reverses it into evidence ("porque não responde"). The record's own particle note says the opposite of the
  pt: "て liga みえる à oração seguinte, com sentido de causa: 'pelo visto está ocupado, **e por isso**…'".
- Fix: `Pelo visto ele está ocupado, por isso não responde.`

**3. `sent:gen-4b2b56124299` — 立派 flattened to "bonita"**
- jp: `立派な家ですね` / pt: `Que casa bonita, né?` / literal: `É uma casa magnífica, não é?`
- The record is tagged `generated:vocab,674`, i.e. it exists to teach 立派. Its own token gloss reads
  `magnífico, imponente, esplêndido`. `bonita` is 綺麗/かわいい territory and erases the distinction the
  sentence was built to teach.
- Fix: `Que casa imponente, né?`

**4. `sent:gen-0e477e8bae8f` — 非常に flattened to "muito"**
- jp: `この料理は非常においしいです` / pt: `Esta comida está muito gostosa.` / literal: `… extremamente (非常に) …`
- Tagged `generated:vocab,731`, i.e. built to teach 非常に. Token gloss: `extremo; (com に) extremamente, muito`.
  As rendered, the sentence is indistinguishable from a とても sentence.
- Fix: `Esta comida está extremamente gostosa.`

**5. `sent:gen-5d9d75f5cfc5` — 〜にくい rendered as "desconfortável", and unidiomatic pt**
- jp: `硬い椅子は座りにくいです` / pt: `Cadeira dura é desconfortável de sentar.` / literal: `… é difícil de sentar.`
- Token gloss for にくい: `difícil de (fazer)`. The translation swaps in `desconfortável`, which is a different
  claim, and `desconfortável de sentar` is not a pt-BR collocation (pt takes `para sentar` or `de sentar` only
  with `ruim`/`bom`).
- Fix: `Cadeira dura é ruim de sentar.`

**6. `sent:tatoeba-79687` — token gloss holds a role description instead of a meaning**
- jp: `夜食にインスタントラーメンを食べた。`
- Token `夜食` (noun) has `gloss["pt-BR"] = "papel em que a comida entrou"` and
  `role["pt-BR"] = "função do que se comeu"`. The gloss field is repeating the role, so the learner is never
  told what 夜食 means.
- Fix: `gloss["pt-BR"] = "ceia; refeição da madrugada"`, leaving the role as is.
  (I scanned all content-word tokens in the slice for this pattern; this is the only genuine instance.)

**7. `sent:tatoeba-74893` — かかれ mistranslated**
- jp: `クソっ。かかれ！` / pt: `Droga! Pega logo!` / literal: `Droga. Comece(m) logo!` / en: `Start, dammit!`
- `かかれ` is the imperative of `かかる` = set about it, get going. `Pega` in pt-BR means grab/catch and points
  at an object that does not exist here. The record's own literal and en both say "start".
- Fix: `Droga! Começa logo!`

### Medium

**8. `sent:gen-4cace4963888` — 晴れ reduced to "bom", with no subject**
- jp: `今日は朝から晴れだ` / pt: `Hoje está bom desde cedo.`
- Tagged `generated:vocab,529` (晴れ). `晴れ` is specifically clear/sunny weather, and "Hoje está bom" leaves
  the predicate dangling (bom o quê?). Compare `sent:gen-d08314bec23d`, same vocab item, correctly rendered
  `Amanhã vai fazer sol.`
- Fix: `Hoje está ensolarado desde cedo.`

**9. `sent:gen-d27ebc70782f` — "desde de manhã" is a doubled preposition**
- jp: `今日は朝から曇っています` / pt: `Hoje está nublado desde de manhã.`
- `desde de` is not standard pt-BR (`de manhã` is a fixed adverbial; `desde` takes `a manhã` or `cedo`).
- Fix: `Hoje está nublado desde cedo.`
- Same error in prose: `sent:gen-4cace4963888`, particle note for から, `"desde de manhã"`. Fix to
  `"desde a manhã"`.

**10 and 11. "com a voz X" should be "em voz X"**
- `sent:gen-3d94abdc83f1` — jp `大きな声で話してください` / pt `Por favor, fale com a voz bem alta.`
- `sent:gen-f10be59e4b88` — jp `彼は小さい声で謝った` / pt `Ele pediu desculpas com a voz baixinha.`
- The pt-BR collocation is `em voz alta` / `em voz baixa`; the definite article turns it into "the voice",
  which reads as a specific voice rather than a manner.
- Fix: `Por favor, fale em voz alta.` and `Ele pediu desculpas em voz baixa.`

**12. `sent:gen-a793b5185326` — 〜てみる rendered as "tentar" (attempt)**
- jp: `アフリカに行ってみたいです` / pt: `Quero tentar ir à África.` / literal: `… quero experimentar ir.`
- `〜てみる` is "do and see how it is", not "attempt". `tentar ir` implies going is difficult and one may fail,
  which the JP does not say.
- Fix: `Queria conhecer a África.`

**13. `sent:gen-3cf2fa13658a` — 困っています rendered as "me dando trabalho"**
- jp: `お金がなくて困っています` / pt: `Estou sem dinheiro e isso está me dando trabalho.` / literal: `… estou em apuros.`
- `困る` is being at a loss / in difficulty; `dar trabalho` in pt-BR is "be a hassle, require effort", a much
  weaker and different claim. The record's own literal has it right.
- Fix: `Estou sem dinheiro e isso está me deixando numa situação difícil.`

**14. `sent:gen-7c51b9c978a2` — causal 〜くて flattened to "e"**
- jp: `駅が遠くて、とても不便です` / pt: `A estação é longe e bem inconveniente.`
- The record's own particle note: "て anexado a 遠く … conectando 'é longe' à oração seguinte **com sentido de
  causa**", and its `translation_literal["en"]` reads "Because the station is far, it is very inconvenient."
  As rendered, the pt also predicates 不便 of the station itself rather than of the situation.
- Fix: `A estação fica longe, então é bem inconveniente.`

**15. `sent:gen-a2e2f06f2fce` — おいしい applied to a restaurant**
- jp: `あのレストランはおいしいです それに静かです` / pt: `Aquele restaurante é gostoso, e ainda por cima é tranquilo.`
- `あのレストランはおいしい` is idiomatic Japanese; the pt calque is not. In pt-BR "um restaurante gostoso"
  reads as cosy/pleasant (or worse), never as "the food is good".
- Fix: `A comida daquele restaurante é gostosa, e ainda por cima o lugar é tranquilo.`

**16. `sent:jec-0281` — stray "assim" plus weakened なかなか**
- jp: `なかなか機会が有りませんでした` / pt: `Não tive muitas oportunidades assim.`
- `assim` renders nothing in the JP and makes the sentence read as "opportunities *like this one*".
  `なかなか + negative` is "hardly ever / just never came up", stronger than "não muitas".
- Fix: `Quase não apareceu oportunidade.`

**17. `sent:tatoeba-10362694` — はっきり rendered as "logo"**
- jp: `はっきり言ってよ。` / pt: `Fala logo o que você quer dizer.` / literal: `Diga claramente, vai.`
- `はっきり` is "clearly, plainly", an adverb of manner; `logo` is an adverb of time. The record's own literal
  and token gloss both say `claramente`.
- Fix: `Fala sem rodeios, vai.`

**18. `sent:tatoeba-126408` — 見えない rendered with a bookish passive**
- jp: `昼間は星は見えない。` / pt: `Durante o dia, as estrelas não são vistas.`
- The corpus renders 見える/見られる/聞こえる idiomatically everywhere else in this slice: `sent:gen-3cf2fa13658a`
  region `dá para ver bem as estrelas`, `sent:gen-66dd5aa6e8dc` `Dá pra ver uma escola`, `sent:tatoeba-11588173`
  `Dá para ouvir passos`, `sent:tatoeba-347548` `Dá pra ouvir tudo perfeitamente`. This one is the outlier and
  reads like translated prose, not speech (Style §1).
- Fix: `Durante o dia não dá para ver as estrelas.`

### Low (naturalness; a pt-BR editor would change these, meaning survives)

**19. `sent:gen-0b3e305b0cc0`** — jp `おばあさんは元気です` / pt `A minha avó está com saúde.`
`元気です` is "is well / is in good spirits"; "estar com saúde" is not how a Brazilian states it, and the
literal already has the better wording (`está bem de saúde`). Fix: `Minha avó está bem de saúde.`

**20. `sent:gen-27c082e69523`** — jp `誕生日のお祝いをしました` / pt `A gente fez a comemoração de aniversário.`
Calque of noun+する; "fazer a comemoração" reads as officialese. Fix: `A gente comemorou o aniversário.`

**21. `sent:gen-74762640fb10`** — jp `多くの市民が会議に集まった` / pt `Muitos cidadãos se reuniram na reunião.`
`reunir` + `reunião` is a cacophonous repetition. Fix: `Muitos cidadãos compareceram à reunião.`

**22. `sent:jec-1839`** — jp `さらに長さを半分に切る` / pt `Depois corte o comprimento ao meio.`
"Cortar o comprimento" is a calque; in pt you cut the object, not the measurement.
Fix: `Depois corte ao meio, no sentido do comprimento.`

**23. `sent:tatoeba-225292`** — jp `ケーキ作りに失敗した。` / pt `Fracassei ao fazer um bolo.`
`fracassar` is a heavy, formal verb; disproportionate for a cake and out of register for the casual
plain-past JP. Fix: `Meu bolo deu errado.`

---

## Count table

| Class | What | Records flagged | Severity |
|---|---|---|---|
| A | `translation_literal`: は topic scaffold on a non-は chunk | 39 | medium (misteaches が/は) |
| B | `この` rendered "esse/essa" against corpus convention | 13 | low |
| C | 好き/上手/下手 literal gloss: coined word or wrong noun | 9 | medium |
| D | plain non-past rendered as bare infinitive (+1 declarative to imperative) | 6 | medium |
| E | Layer-A `translation["en"]` missing | 59 | high (blocks validation) |
| F | explanatory parentheses inside `translation` | 13 | low |
| I-high | individual: meaning wrong or taught point lost | 7 | high |
| I-med | individual | 11 | medium |
| I-low | individual: naturalness | 5 | low |
| | **sum of class rows** | **162** | |

Six records carry two classes each, so the class rows sum to more than the record count:
`sent:gen-273cffc1f6f8` (A + D), `sent:gen-633db27a84d8` (A + C), `sent:gen-d4a16635f7bd` (A + C),
`sent:tatoeba-74693` (B + E), `sent:tatoeba-79687` (E + I-high), `sent:tatoeba-84914` (A + F).

**Checked: 982. Distinct records flagged: 156 (15.9%). Clean: 826 (84.1%).**

Flags by source block:

| block | records in slice | flagged | flagged excluding Class E |
|---|---|---|---|
| `ai-generated` | 369 | 69 (18.7%) | 69 |
| `jec:*` | 21 | 8 (38.1%) | 8 |
| `tatoeba:*` | 592 | 79 (13.3%) | **20 (3.4%)** |

Triage guidance: the 59 Class-E records are one ingestion bug, not 59 authoring errors, and should be fixed at
the pipeline level rather than in the review queue. Excluding them, the human review queue from this slice is
**97 records**, concentrated in the generated and `jec` blocks. The Tatoeba block is genuinely clean at 3.4%.
