# QA sweep — translation accuracy, part 2/6

**Scope:** `corpus/sentences/bank.json`, records with `index % 6 == 1` — **982 records** (indices 1, 7, 13 … 5875).
**Reviewed fields:** `translation["pt-BR"]`, `translation_literal["pt-BR"]`, token `gloss/role/conjugation_note` (pt-BR), particle `function/explanation` (pt-BR).
**Explicitly excluded per assignment:** `structure_explanation` (being re-authored elsewhere). Nothing below touches it.
**Style authority:** `design/translation_style.md`.

Every record in the slice was read in full (JP + kana + both translations + every token + every particle entry). Findings below are only those I can defend with the record's own evidence.

---

## Headline

The slice is in good shape on the things that usually break first. Specifically, these came back **clean**:

- **pt-PT leakage:** zero. No *comboio / telemóvel / autocarro / casa de banho / pequeno-almoço / rapariga*, no `estar a + infinitivo`, no `tu`-conjugations.
- **Register inversion:** zero. No keigo/humble sentence rendered with `cê / valeu / mano / tá`; no plain-form sentence rendered with `vossa / outrossim / queira`. Casual endings (よ / ね / の / わ / なあ) are consistently rendered with pt-BR spoken tags (*viu, né, tá, sabe, hein*), which is exactly what §2 of the style guide asks for.
- **Polarity:** zero dropped negations. Every ない / ません / なくちゃ / しか〜ない / めったに〜ない / 全然〜ない in the slice reaches pt-BR intact.
- **Question / tense marking:** no question rendered as a statement, no past rendered as present (all automated hits were false positives from だ-copula and よ→"viu?").
- **Counters and numbers:** every 〜つ / 〜枚 / 〜冊 / 〜人 / 〜個 / 〜キロ / 〜階 / 〜歳 / 〜杯 in the slice reaches pt-BR with the right number and the right classifier sense.
- **Em dashes:** zero (§4 respected).

What is **not** clean is concentrated in two systematic classes plus a short tail of individual defects. Both classes are mechanical to fix and neither touches the natural translation's meaning — which is why they survived to here.

---

## Class A — `translation_literal` glosses が / を / に as the topic marker ("Quanto a…")

**59 records (6.0 % of the slice).**

`design/translation_style.md` §1 and §5 make `translation_literal` the field that carries the *structural* gloss — "topic markers, particle-by-particle" — and reserves **"quanto a X"** for the topic particle は, precisely so the learner can tell は apart from が/を. In these 59 records the literal opens a constituent with **"Quanto a X"** when X carries **が, を, に or で** and the sentence has **no は at all**. The gloss therefore teaches the learner that が/を mean "quanto a", which is the one thing the field exists to prevent.

**Twelve of them contradict themselves inside the same string** — they print the particle and then mislabel it:

| id | JP | current `translation_literal` (pt-BR) |
|---|---|---|
| `sent:gen-64268ad6f237` | 大臣が記者に接見しました | **Quanto ao ministro (が)**, aos jornalistas (に), concedeu audiência (接見しました). |
| `sent:jec-1133` | 彼が運転サービスのプロを目指します | **Quanto a ele (が, sujeito)**, um profissional do serviço de condução (を) almeja. |
| `sent:jec-1593` | 彼が郊外に家を買った | **Quanto a ele (が, sujeito)**, no subúrbio (に), uma casa (を) comprou. |
| `sent:jec-3088` | 彼が早めに何らかの手を打つ | **Quanto a ele (が)**, cedo (に), alguma (何らかの) providência (手を), toma. |
| `sent:jec-3567` | 私がさっさと用事を済ませる | **Quanto a eu (が)**, rapidamente as tarefas (を) resolver. |
| `sent:jec-0070` | 委員会の人たちが、あいさつ運動をしました | **Quanto às pessoas da comissão (が, sujeito)**, uma campanha de saudação (を) fizeram. |
| `sent:gen-39718c65d144` | 窓を開けました すると風が入ってきました | **Quanto à janela (を)**, abri; e então (すると), o vento (が, sujeito) entrou (vindo). |
| `sent:gen-b54ddf43f241` | 道で警官に道を聞きました | Na rua (で), ao policial (に), **quanto ao caminho (を)**, perguntei. |
| `sent:gen-b7803d312323` | 手紙をポストに入れた | **Quanto à carta (を)**, dentro da caixa de correio (に) coloquei. |
| `sent:gen-be1f54ae2166` | 卵を九つ使った | **Quanto a ovos (objeto)**, nove (unidades) usei. |
| `sent:gen-802fed6cb267` | りんごをなんこ買いますか | **Quanto a maçãs (objeto)**, quantas unidades compra? |
| `sent:gen-cfc9111b4d40` | 夏の暑さが苦手だ | **Quanto ao calor do verão**, (ele) é algo em que sou ruim/não suporto (苦手). |

**Proposed fix (mechanical, whole class):** reserve `Quanto a X` for は. Gloss the others by their own function:

- が (subject) → `X (が, sujeito) …` or simply `X …` — e.g. `sent:gen-64268ad6f237` → *"O ministro (が), aos jornalistas (に), concedeu audiência."*
- を (object) → `X (を, objeto) …` — e.g. `sent:gen-be1f54ae2166` → *"Ovos (を, objeto), nove (unidades) usei."*
- を (path) → `por/pelo X (を, percurso)` — e.g. `sent:gen-79560369fbb2` 箸でご飯を食べる → *"Com hashi, o arroz (を, objeto), (eu) como."*
- に (locative/existential) → `em X (に)` — e.g. `sent:gen-466ade921841` 電話番号にゼロが三つある → *"No número de telefone (に), zeros (が) existem em quantidade de três."*

**Full list of the 59 records** (id | JP | current literal | particles present):

| id | JP | current `translation_literal` | particles |
|---|---|---|---|
| `sent:gen-0e4f08cdd12e` | 窓が開けてある | Quanto à janela, ela está (no estado de) ter sido aberta. | が て |
| `sent:gen-138c8e26cf51` | 背がいたいので病院に行く | Quanto às costas, dói, então, hospital ao vou. | が の に |
| `sent:gen-23140aae7ddb` | シャツの裏が白いです | Quanto ao avesso da camisa, (ele) é branco. | の が |
| `sent:gen-2fae8986ebe2` | もうすぐお湯が沸きます | Logo logo, quanto à água quente, ferve (educado). | が |
| `sent:gen-33199acd7aa9` | 御連絡をお待ちしています | Quanto ao (seu) contato, (eu/nós) o estou(amos) esperando (humildemente). | を て |
| `sent:gen-39718c65d144` | 窓を開けました すると風が入ってきました | Quanto à janela (を), abri; e então (すると), o vento (が, sujeito) entrou (vindo). | を と が て |
| `sent:gen-466ade921841` | 電話番号にゼロが三つある | Quanto ao número de telefone, zeros existem em quantidade de três. | に が |
| `sent:gen-47c527ecd4fb` | 薬を飲んだのにちっともよくならない | Quanto a (eu), apesar de ter tomado o remédio, nem um pouco fico bom/melhor não. | を の に |
| `sent:gen-4f5316c138ae` | りんごが九つあります | Quanto a maçãs, em número de nove, existem. | が |
| `sent:gen-56eab8c9f8b0` | あなたがいると安心する | Quanto a você, se (você) existe/está, (eu) me tranquilizo. | が と |
| `sent:gen-5b0f0ae6501d` | 私いがいみんな来ました | Quanto a [todos] exceto eu, todo mundo veio. | (nenhuma) |
| `sent:gen-5d4921b7f95f` | 海岸を散歩するのが好きだ | Quanto a passear (散歩する) pela costa (海岸を), (isso) é do meu gosto. | を の が |
| `sent:gen-5f60fc0e77c1` | 中ぐらいのサイズをください | Quanto a tamanho médio, dê-me (por favor). | ぐらい の を |
| `sent:gen-64268ad6f237` | 大臣が記者に接見しました | Quanto ao ministro (が), aos jornalistas (に), concedeu audiência (接見しました). | が に |
| `sent:gen-65c29928a685` | 二十歳からお酒が飲める | A partir de vinte anos, quanto à bebida, é possível beber. | から が |
| `sent:gen-67098aef1bd0` | お金をためて、然うして車を買った | Quanto a dinheiro, juntando(-o), e então, quanto a carro, (eu o) comprei. | を て て を |
| `sent:gen-6cdc81c170ce` | シャツのボタンを取り替えてもらった | Quanto ao botão da camisa, recebi o favor de (alguém) trocar. | の を て |
| `sent:gen-6da9d528f71b` | 電車よりバスのほうが安いです | Comparado ao trem, quanto ao lado do ônibus, é mais barato. | より の が |
| `sent:gen-76452db37bcf` | まず手を洗ってください | Antes de tudo, quanto às mãos, lave por favor. | を て |
| `sent:gen-79560369fbb2` | 箸でご飯を食べる | Com hashi, quanto ao arroz, (eu) como. | で を |
| `sent:gen-7f47e7897633` | 部屋の電気が点いている | Quanto à luz do quarto, está estando acesa. | の が て |
| `sent:gen-802fed6cb267` | りんごをなんこ買いますか | Quanto a maçãs (objeto), quantas unidades compra? | を か |
| `sent:gen-92ba23e6738e` | 弟のほうが私より背が高い | Quanto ao lado do meu irmão mais novo, em comparação comigo, a estatura é alta. | の が より が |
| `sent:gen-a31db51cb8d5` | 電話したけれども 誰も出なかった | Quanto a ter ligado, embora (eu) tenha ligado, ninguém também atendeu (não). | けれど も も |
| `sent:gen-a3e4ae19317a` | 庭の草が長くなってきた | Quanto ao mato do jardim, ficou comprido vindo (até agora). | の が て |
| `sent:gen-a7aba7fc3b83` | 猫がすっと外へ出ました | Quanto ao gato, num instante (すっと), para fora (外へ), saiu (出ました). | が と へ |
| `sent:gen-b1c69ef83963` | 毎日勉強して日本語が上手になった | Todo dia, estudando, quanto ao japonês, tornou-se habilidoso. | て が |
| `sent:gen-b249a5f48dc6` | 千円いかの本を買いました | Quanto a um livro de mil ienes ou menos, comprei. | の を |
| `sent:gen-b2e4e4f13151` | 古い自転車をなおして使う | Quanto à bicicleta velha, consertando, uso. | を て |
| `sent:gen-b54ddf43f241` | 道で警官に道を聞きました | Na rua (で), ao policial (に), quanto ao caminho (を), perguntei. | で に を |
| `sent:gen-b7803d312323` | 手紙をポストに入れた | Quanto à carta (を), dentro da caixa de correio (に) coloquei. | を に |
| `sent:gen-be1f54ae2166` | 卵を九つ使った | Quanto a ovos (objeto), nove (unidades) usei. | を |
| `sent:gen-bf2c180a7a87` | 旅行が楽しくなるように祈っている | Quanto à viagem, estou rezando de modo que (ela) fique divertida. | が て |
| `sent:gen-c39fca7e5ee6` | 馬に乗ったことがありますか | Quanto a montar em cavalo, existe a experiência (disso)? | に が か |
| `sent:gen-c9c77d71b5c8` | 音楽を小さくしてください | Quanto à música, faça-a pequena (= baixa), por favor. | を て |
| `sent:gen-cb428ba32298` | こちらが受付でございます | Quanto a isto (este lado), é a recepção (forma humilde-polida). | が |
| `sent:gen-ce9602ca3acc` | 経済のニュースを毎朝読みます | Quanto às notícias de economia, (eu) toda manhã (as) leio. | の を |
| `sent:gen-cfc9111b4d40` | 夏の暑さが苦手だ | Quanto ao calor do verão, (ele) é algo em que sou ruim/não suporto (苦手). | の が |
| `sent:gen-d7f3836d4c7a` | 細かいお金がありますか | Quanto a dinheiro miúdo/trocado, (ele) existe? | が か |
| `sent:gen-f1534c9baa43` | 部屋を明るくする | Quanto ao quarto, torná-lo claro/iluminado (fazê-lo brilhante). | を |
| `sent:gen-f4c05abf2f88` | 今月の電気代が高かった | Quanto a deste mês a conta de luz, (foi) cara. | の が |
| `sent:gen-ff855e0b043c` | パンが黒く焼けてしまった | Quanto ao pão, assou ficando preto (e acabou indo parar nisso). | が て |
| `sent:jec-0070` | 委員会の人たちが、あいさつ運動をしました | Quanto às pessoas da comissão (が, sujeito), uma campanha de saudação (を) fizeram. | の が を |
| `sent:jec-0980` | 彼が必ずチェックを入れます | Quanto a ele, ele sem falta coloca uma verificação. | が を |
| `sent:jec-1133` | 彼が運転サービスのプロを目指します | Quanto a ele (が, sujeito), um profissional do serviço de condução (を) almeja. | が の を |
| `sent:jec-1593` | 彼が郊外に家を買った | Quanto a ele (が, sujeito), no subúrbio (に), uma casa (を) comprou. | が に を |
| `sent:jec-1845` | セロリ、プロセスチーズを１ｃｍ角に切る | Quanto ao aipo (e) ao queijo processado, em cubo de 1 cm, cortar. | を に |
| `sent:jec-2741` | 彼がせっせと彼女の口に水を運んだ | Quanto a ele, diligentemente, à boca dela, água, (ele) levou. | が の に を |
| `sent:jec-3088` | 彼が早めに何らかの手を打つ | Quanto a ele (が), cedo (に), alguma (何らかの) providência (手を), toma. | が か の を |
| `sent:jec-3567` | 私がさっさと用事を済ませる | Quanto a eu (が), rapidamente as tarefas (を) resolver. | が を |
| `sent:jec-4753` | ＳＰの仕事の様子が今日テレビで放送されました | Quanto à situação do trabalho dos SP, hoje na televisão foi transmitida. | の の が で |
| `sent:tatoeba-118274` | 彼のネクタイがほどけた。 | Quanto à gravata dele, desfez-se. | の が |
| `sent:tatoeba-12524635` | 今日中に答えを出してほしい。 | Dentro do dia de hoje, quanto à resposta, [eu] quero que [você a] entregue. | に を て |
| `sent:tatoeba-194622` | めったにないこの機会を利用しさえすれば良い。 | Quanto a esta oportunidade que raramente existe, se você apenas a utilizar, está bom. | を さえ ば |
| `sent:tatoeba-205916` | それから先の話を聞きたい。 | Depois disso, quanto à história do que vem adiante, (eu) quero ouvir. | から の を |
| `sent:tatoeba-222763` | この歌を聞くと私の中学校時代を思い出します。 | Esta música ouvir + quando, quanto a mim, a época da minha escola média (eu) recordo. | を と の を |
| `sent:tatoeba-79019` | 予習を始めた方がいいですよ。 | Quanto a começar a preparação, o lado (de fazer isso) é bom, viu. | を が よ |
| `sent:tatoeba-83696` | 雰囲気がいやだった。 | Quanto à atmosfera, desagradável estava. | が |
| `sent:tatoeba-84132` | 部屋をいそいでかたづけてほしいの。 | Quanto ao quarto, eu quero que você o arrume com pressa. | を で て の |

**Deliberately NOT flagged** (checked and judged correct): records where "quanto a" glosses a *zero-marked* or *non-は* topic — `sent:tatoeba-11294867` ("Quanto a (isto)", zero topic), `sent:tatoeba-187193` / `sent:tatoeba-3596318` (って as colloquial topic marker), `sent:tatoeba-217273` (なら, "Quanto a computador (se for)"), `sent:tatoeba-75187` (comma-elided topic), `sent:gen-d338f63d2a25` (bare temporal topic), `sent:gen-2008c11580bb` (も), `sent:gen-74bce4b40079` (は present but merged into the ははは token), and `sent:gen-ebf2bd2e2955` where "quanto à viagem" is the **correct** gloss of について.

### A.1 — Six of the 59 are additionally broken as Portuguese

These need rewriting, not just a particle relabel:

| id | JP | current `translation_literal` | why it's wrong | proposed |
|---|---|---|---|---|
| `sent:gen-7f47e7897633` | 部屋の電気が点いている | *Quanto à luz do quarto, **está estando acesa**.* | "está estando" is not Portuguese — `estar` has no progressive of itself. | *A luz do quarto (が) está acesa (estado resultante de 点く).* |
| `sent:gen-f4c05abf2f88` | 今月の電気代が高かった | ***Quanto a deste mês a conta de luz**, (foi) cara.* | broken word order; "a deste mês a conta" is unparseable. | *A conta de luz deste mês (が) foi cara.* |
| `sent:jec-3567` | 私がさっさと用事を済ませる | ***Quanto a eu (が)**, rapidamente as tarefas (を) resolver.* | pt requires the oblique pronoun after `a`: "a **mim**", never "a eu". | *Eu (が), rapidamente, as tarefas (を) resolvo.* |
| `sent:gen-47c527ecd4fb` | 薬を飲んだのにちっともよくならない | ***Quanto a (eu)**, apesar de ter tomado o remédio, …* | same "a eu" problem, plus the topic is invented (no は in the sentence). | *O remédio (を), apesar de (eu) tê-lo tomado, nem um pouco fico bom.* |
| `sent:gen-5b0f0ae6501d` | 私いがいみんな来ました | *Quanto a **[todos] exceto eu, todo mundo** veio.* | 私以外 modifies みんな; the gloss invents a topic and then states the subject twice. | *Exceto eu (私いがい), todo mundo (みんな) veio.* |
| `sent:gen-a31db51cb8d5` | 電話したけれども 誰も出なかった | *Quanto a ter ligado, **embora (eu) tenha ligado**, ninguém também atendeu (não).* | states the calling twice, and "ninguém também atendeu (não)" is not parseable pt. | *(Eu) liguei, mas (けれども), ninguém (誰も) atendeu (não).* |

---

## Class B — explanatory parentheses inside `translation.pt-BR`

**19 records.** §1 and §5 of the style guide make `translation` the *natural* pt-BR rendering ("something a Brazilian would actually say") and put structural/explanatory material in `translation_literal` / `structure_explanation`. In these 19 the natural-translation field carries a parenthetical gloss, an alternative wording, or an outright explanation — so it no longer reads as natural speech.

| id | JP | current `translation.pt-BR` | what the parenthesis is doing |
|---|---|---|---|
| `sent:gen-537ce93c20eb` | 弟に私のケーキを食べられた | Meu irmão mais novo comeu o meu bolo **(e eu fiquei chateado)**. | explains the adversative passive |
| `sent:gen-8adf6d2b2a1f` | 新しいテープを買ってきた | Comprei uma fita nova **(e trouxe)**. | explains 〜てくる |
| `sent:gen-ff855e0b043c` | パンが黒く焼けてしまった | O pão acabou ficando queimado **(preto)**. | redundant gloss of 黒く |
| `sent:jec-4753` | ＳＰの仕事の様子が… | …o trabalho dos seguranças **(SP)**. | keeps the JP acronym |
| `sent:tatoeba-11022928` | お湯、沸かしといて。 | Deixa a água fervendo **(já)**, tá? | dangling adverb |
| `sent:tatoeba-1138405` | 部長はオンとオフがはっきりしている。 | …separa bem o trabalho do lazer **(sabe quando ligar e quando desligar)**. | full explanation of オン/オフ |
| `sent:tatoeba-124654` | 電話を切らずにおいてください。 | Por favor, não desligue o telefone **(fique na linha)**. | alternative rendering |
| `sent:tatoeba-1323453` | お会いできるといいですね。 | Tomara que eu possa vê-lo **(de novo)**, né? | **adds meaning** — see C.4 |
| `sent:tatoeba-198230` | バスが止まるまで降りるな。 | Não desça **(do ônibus)** até o ônibus parar. | clarification |
| `sent:tatoeba-201239` | とうとうガタがきたようだ。 | Parece que finalmente começou a dar problema **(a quebrar)**. | gloss |
| `sent:tatoeba-215751` | ジャムを上の棚から降ろしてくれ。 | Tira a geleia da prateleira de cima **(para mim)**. | explains 〜てくれ |
| `sent:tatoeba-220506` | この町は西も東も分かりません。 | …nem onde é o leste **(estou completamente perdido)**. | full explanation |
| `sent:tatoeba-225298` | ケーキを食べてしまったら手に残らない。 | Depois que você comer **(todo)** o bolo… | gloss of 〜てしまう |
| `sent:tatoeba-229425` | …いつか覚えなければ。 | Algum dia preciso aprender **(isso)**. | filler object |
| `sent:tatoeba-235706` | １日おきに買い物に行く。 | …dia sim, dia não **(a cada dois dias)**. | restates the same thing |
| `sent:tatoeba-76604` | それはこっちのセリフですよ。 | Essa é a minha fala **(sou eu quem deveria dizer isso)**. | full explanation |
| `sent:tatoeba-79019` | 予習を始めた方がいいですよ。 | …estudar a matéria antes **(da aula)**, viu? | clarification |
| `sent:tatoeba-80308` | 明日行くからそのつもりで。 | …então já fique sabendo **(conte com isso)**. | alternative rendering |
| `sent:tatoeba-83013` | 母は外出しています。 | Minha mãe saiu **(está fora)**. | alternative rendering |

**Proposed fix:** delete the parenthesis from `translation`; where the information is genuinely pedagogical, it already belongs to `translation_literal` (which in most of these records already carries it — e.g. `sent:gen-537ce93c20eb`'s literal already says *"Pelo meu irmão mais novo, o meu bolo foi comido"*, so the natural translation only needs *"Meu irmão mais novo comeu o meu bolo."*).

**Separate, lower-priority observation (not counted as flagged):** five records use inline gender-agreement parentheses in `translation` — `sent:gen-c63e16ea70fa` ("o(a) cliente"), `sent:gen-f59f9d5195cc` ("o senhor (a senhora)"), `sent:tatoeba-174355` ("o(a) senhor(a)"), `sent:tatoeba-4971` ("obrigado(a)"), `sent:tatoeba-79103` ("convidado(a)"). That is a house-style decision for the teacher to make, not a translation defect — but it is inconsistent, since the rest of the slice picks one gender freely.

---

## Class C — individual defects

### C.1 pt-BR orthography (3 records)

| id | field | current text | fix |
|---|---|---|---|
| `sent:gen-12a28127409c` | `translation.pt-BR` | **Eu prático esportes**, por exemplo futebol e tênis. | `prático` (adjective, "practical") → **`pratico`** (1sg of *praticar*). |
| `sent:gen-3ecabce0d070` | `particles[0].explanation.pt-BR` (が) | …が marca 「わたし」como o sujeito que **prática** a ação 住んでいる… | → **`pratica`**. |
| `sent:gen-f1b038704e1c` | `particles[0].explanation.pt-BR` (が) | が marca 雨 como o sujeito que **prática** a ação 降った (a chuva caiu). | → **`pratica`**. |

(`sent:gen-12a28127409c` also carries the same slip in its particle explanation — *"prática-se 'o quê?'"* → *"pratica-se"* — and in `structure_explanation`, which is out of scope here.)

### C.2 `sent:tatoeba-3179644` — 着てくる rendered as "bring", not "wear"

- **JP:** コート着てくればよかった。
- **current PT:** *Eu devia ter **trazido** um casaco.*
- **why wrong:** 着てくる is "to come **wearing** (it)" (着る + てくる), not 持ってくる "to bring". The record's own `translation_literal` says *"Casaco **vestir**-vir…"* and the record's own EN pair says *"I should have **worn** a coat."* The natural translation is the only place that says "trazido", so it contradicts the rest of the record and teaches the wrong verb.
- **proposed:** *Eu devia ter vindo de casaco.* (or *Eu devia ter posto um casaco.*)
- **note:** the token `gloss` for くれ propagates the same slip — *"vir (**trazer** vestido)"* → should be *"vir (já vestido)"*.

### C.3 `sent:tatoeba-144581` — the literal teaches the wrong reading of よく見える

- **JP:** 人の物はよく見える。
- **current PT:** *As coisas dos outros sempre parecem melhores.* ✅ (correct — it is the "grass is greener" proverb)
- **current LIT:** *Quanto às coisas das pessoas, **bem se veem**.*
- **why wrong:** the literal reads よく見える as "are clearly visible", which is a different (and here wrong) sense, and it flatly contradicts the natural translation directly above it. A learner comparing the two fields gets two incompatible meanings. The token gloss already has it right (*"parecem (boas) / veem-se bem"*).
- **proposed:** *Quanto às coisas dos outros, (elas) parecem boas.*

### C.4 `sent:tatoeba-1323453` — "de novo" is not in the source

- **JP:** お会いできるといいですね。
- **current PT:** *Tomara que eu possa vê-lo **(de novo)**, né?*
- **why wrong:** nothing in the JP (nor in the record's own `translation_literal`, *"Se (eu) puder (humildemente) encontrá-lo, (seria) bom, né"*, nor in the EN, *"I hope to see you"*) says "again". また / もう一度 are absent.
- **proposed:** *Tomara que a gente possa se ver, né?*

### C.5 `sent:tatoeba-176220` — literal says "perigosa", translation says "roubada"

- **JP:** 警察はそれがやばい品物なのを知ってたんだよ。
- **current PT:** *A polícia sabia que aquilo era mercadoria **roubada**.*
- **current LIT:** *A polícia quanto a, aquilo (sujeito) ser mercadoria **perigosa** (objeto) sabia, viu.*
- **why wrong:** the two fields disagree on what やばい means here, and the record's own token gloss settles it against the literal: *"perigoso, suspeito, 'encrenca' (gíria, **aqui: roubado/ilegal**)"*.
- **proposed:** align the literal — *"A polícia (は), aquilo (が) ser mercadoria ilegal/'quente' (品物), sabia, viu."*

### C.6 `sent:tatoeba-113910` — 会場 rendered as "palco"

- **JP:** 彼はクラスを代表して会場に出た。
- **current PT:** *Ele saiu ao **palco** representando a turma.*
- **why wrong:** 会場 is the *venue / hall* (the record's own token gloss: *"local do evento / salão"*; its own literal: *"saiu para o **local do evento**"*). "Palco" is 舞台. The natural translation narrows the noun to something the source does not say, and contradicts the two other pt-BR fields in the same record.
- **proposed:** *Ele foi até o salão representando a turma.*

### C.7 `sent:tatoeba-78959` — 余り〜ない collapsed to a flat negation

- **JP:** 余りよい考えではないと思いますが。
- **current PT:** *Eu acho que **não é uma boa ideia**.*
- **why wrong:** 余り〜ない is a hedge ("not *very*"), not a flat negative — and it is a taught pattern in this very corpus (`amari-nai` appears as a `grammar` tag on sibling records). The record's own literal keeps it: *"**Muito** boa ideia não é, eu acho, **mas…**"*. The trailing softening が is dropped too.
- **proposed:** *Acho que não é uma ideia lá muito boa, mas…*

### C.8 `sent:tatoeba-426889` — さようなら as "Adeus"

- **JP:** さようなら！
- **current PT:** *Adeus!*  (and `translation_literal` is the identical string)
- **why wrong:** in pt-BR *"Adeus"* carries finality — it is what you say when you do not expect to meet again. さようなら is the neutral everyday goodbye an N5 learner is taught to use at school or leaving a shop. Rendering it as *"Adeus"* will make learners produce a farewell that sounds far heavier than the Japanese. This is the only greeting in the slice with this problem: `おはよう→Bom dia!`, `こんにちは→Olá!`, `また後で→Até mais tarde.`, `来週までごきげんよう→Até a semana que vem, passe bem!` are all right.
- **proposed:** `translation` → *Tchau!* (or *Até logo!*); `translation_literal` → *Adeus / até a próxima (despedida formal).*

### C.9 `sent:tatoeba-11733143` — authoring commentary leaked into a learner-facing field

- **JP:** もしできるとしたら、どうする？
- **current `tokens[3].conjugation_note.pt-BR`** (し): *"し é する; junto com たら forma としたら 'supondo que' **(a glosa 'to print' está errada)**"*
- **current `tokens[6].conjugation_note.pt-BR`** (どう): ***"a glosa 'motion' está errada;** どう significa 'como'"*
- **why wrong:** these are editor-to-editor notes about a *previous* English gloss that no longer exists anywhere in the record. A pt-BR learner reads a note telling them that an invisible gloss is wrong. `conjugation_note` is learner-facing per §5.
- **proposed:** strip the meta-comment. `し` → *"し é する; junto com たら forma としたら ('supondo que')."*; `どう` → *"どう significa 'como, de que jeito'."*
- **related but NOT flagged:** four records legitimately warn the learner about a tokenizer split (`sent:gen-52e853b5eb16`, `sent:tatoeba-1057336`, `sent:tatoeba-74743`, `sent:tatoeba-74954`). Those are useful. They do use the words *"o tokenizador" / "o analisador"*, which a beginner will not recognise — worth softening to *"a segmentação automática"*, but that is a wording preference, not a defect.

### C.10 `sent:tatoeba-125943` — person disagreement between the two translations

- **JP:** 長い時間歩いたので疲れきった。 (subjectless)
- **current PT:** *Como **caminhamos** por muito tempo, **ficamos** exaustos.* (1pl)
- **current LIT:** *Longo tempo **caminhei** porque, cansar-completamente.* (1sg)
- **why wrong:** the two pt-BR fields pick different subjects for the same subjectless sentence. Whichever is chosen, they must match, or the learner cannot use the literal to decode the natural translation.
- **proposed:** keep 1pl (it matches the EN pair *"We were tired out…"*) and fix the literal → *"Longo tempo (nós) caminhamos, por isso, ficamos completamente exaustos."*

---

## Judged and deliberately not flagged

Recorded so the human reviewer does not re-litigate them:

- **`ははは` in `sent:gen-74bce4b40079`** — the token merges はは + は; the record's `conjugation_note` already explains it. Not a translation defect.
- **`sent:tatoeba-10768339`** — `translation.en` ("It's an embarrassing question") does not match 答えづらい質問, but the **pt-BR is correct**. The `en` mismatch is outside this assignment's lane.
- **`sent:tatoeba-1160677`, `sent:tatoeba-198230`** and similar — `en` carries extra material from the Tatoeba pair; pt-BR follows the JP correctly.
- **`translation` == `translation_literal`** in four one-word records (`ありがとう`, `おはよう`, `一、二、三…`, `さようなら`). For a bare interjection or a number list there is no structure to gloss, so identity is defensible. Only `さようなら` is flagged, and for its word choice (C.8), not for the identity.
- **"Quanto às coisas das pessoas" style word-order-preserving literals** (`sent:tatoeba-106287`, `sent:tatoeba-145398`, `sent:tatoeba-2633439`, `sent:tatoeba-10124175`, `sent:tatoeba-10181266`) — clunky, but a *consistent* annotation style across the tatoeba subset, not an error.
- **`sent:jec-0980`** ("Ele sempre confere tudo direitinho" for 必ずチェックを入れます) — "tudo direitinho" is idiomatic expansion, within the latitude §1 grants the natural translation.

---

## Counts

| Class | What | Records |
|---|---|---|
| **A** | `translation_literal` glosses が / を / に as topic "Quanto a…" (no は in sentence) | **59** |
| A.1 | …of which also broken as Portuguese ("está estando", "Quanto a eu", broken word order, doubled subject) | *6 (subset of A)* |
| **B** | Explanatory / alternative parenthesis inside `translation.pt-BR` | **19** *(3 also in A)* |
| **C.1** | pt-BR orthography — `prático`/`prática` used as a verb | **3** |
| **C.2–C.7** | Mistranslation or meaning shift (着てくる, よく見える, "de novo", やばい, 会場, 余り〜ない) | **6** *(1 also in B)* |
| **C.8** | Register / word choice (さようなら → "Adeus") | **1** |
| **C.9** | Editorial commentary leaked into a learner-facing field | **1** |
| **C.10** | Person disagreement between `translation` and `translation_literal` | **1** |
| | **Distinct records flagged** | **86** |
| | **Records checked** | **982** |
| | Flag rate | **8.8 %** |

| Clean dimensions (0 findings across all 982) |
|---|
| pt-PT leakage |
| Register inversion (keigo↔casual) |
| Dropped or added negation |
| Question / statement mismatch |
| Tense mismatch |
| Counter / numeral errors |
| Em dash (—) usage |

**Nothing in this report touches `structure_explanation`.**
