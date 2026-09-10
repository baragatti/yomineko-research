# W13b: auditoria das explicações e rótulos de partícula gerados por template

**Escopo.** As 30 levas de `research/derived/mined_layerb_n3/` (4.320 frases já ingeridas). Tudo foi
lido em modo leitura; nada sob `research/derived/n3_mined/` ou `research/derived/mined_layerb_n3/`
foi tocado, o banco não foi aberto e nenhum exportador rodou.

**Entregáveis.**

- `research/derived/pending/particle_template_fixes.json`: tabela de reparo, 275 linhas, chaveada
  por `(key, position)`, para ser aplicada depois como reparo rastreado.
- `scripts/derive_layerb_templates_v2.py`: cópia de `scripts/derive_layerb.py` com as regras
  corrigidas, para que uma rederivação futura não reproduza os mesmos defeitos.
  `python scripts/derive_layerb_templates_v2.py --selftest` roda **91 asserções** sobre os exemplos
  levantados pelo verificador da leva 30 e sobre os casos que **não** podem mudar. Todas passam.

---

## 1. O que foi varrido

| medida | n |
|---|---|
| frases | 4.320 |
| explicações com `explanation_status: template` | 6.987 |
| rótulos `function_pt` ainda idênticos ao modal do par | 8.977 |
| linhas de reparo emitidas | **275** |

As explicações templatizadas se dividem em nove pares: は/binding 2.421, を/case 1.205, の/case
1.030, が/case 931, て/conjunctive 862 e os quatro finais livres de contexto (か 263, よ 198, ね 73,
わ 4).

Um rótulo conta como **templatizado** quando o `function_pt` da leva montada continua byte a byte
igual ao modal do par que a derivação escreveu, **independente do `function_status`**: `bank-modal`
quer dizer que ninguém olhou, `verified` quer dizer que alguém olhou e deixou o modal de pé. Os dois
saíram da mesma regra, e é a regra que está sob auditoria. Esse critério amplia o universo de 7.257
(`bank-modal`) para 8.977, e é justamente na faixa ampliada que estão todos os 24 erros de rótulo
encontrados.

## 2. Regra 1: o trecho citado

`_left_chunk()` da v1 caminhava para a esquerda até achar uma partícula ou pontuação e citava tudo o
que encontrasse. Qualquer coisa adverbial parada na frente do sintagma nominal entrava na citação:
明日雨が降る saía como *"marca 明日雨 como o sujeito"*, sendo que 明日 é advérbio de tempo e o
sujeito é 雨 sozinho.

`chunk_head()` da v2 mantém o núcleo (o token imediatamente à esquerda da partícula) e caminha para a
esquerda **só por modificadores genuínos**. Quem não é modificador encerra o sintagma: a caminhada
para, não pula. O token à direita é o que resolve os casos difíceis. Uma forma flexionada só é
adverbial quando o que vem depois dela é nominal (早く目 vira 目); quando vem outra forma que flexiona,
os dois são um predicado só e ambos ficam (やりたいこと, 引退した後, ぼんやりした表情).

| regra | n | o que sai |
|---|---|---|
| `chunk-adverb-dropped` | 94 | advérbio na frente de nome: ついに彼 → 彼, 少し牛乳 → 牛乳 |
| `chunk-adverbial-noun-dropped` | 64 | nome 副詞可能 fora do núcleo: 明日雨 → 雨, 毎月給料 → 給料 |
| `chunk-adverbial-copula-dropped` | 27 | cópula 連用形 に/で, que é 助動詞 e não 助詞: 急に人 → 人, 非常に損害 → 損害 |
| `chunk-conjunction-dropped` | 11 | conector de frase: そして私 → 私, すなわち彼 → 彼 |
| `chunk-verbal-adverbial-dropped` | 5 | adjetivo-i em 連用形: 早く目 → 目, すごく栄養 → 栄養 |
| **total** | **201** | |

Por par: を/case 77, が/case 73, の/case 26, は/binding 25. Em 29 das 30 levas, de 4 a 17 linhas cada.

O que **não** sai, e por quê:

- 連体詞 e 形状詞 + な 連体形 (きれいな花, 大きな声): modificam o nome de fato.
- 副詞 na frente de outro predicado (より強力な武器, そういう印象): modifica aquele predicado, que
  está dentro do sintagma.
- 動詞 em 連用形 na frente de nome (焼き加減, 読み方): é a metade esquerda de um composto; um verbo
  adverbial precisa de て ou de vírgula.
- forma 語幹 (薄暮れ): só encabeça composto.
- nome formal / preso como núcleo (土曜以外, 一人分, 若いころ): não para em pé sozinho, então o
  vizinho da esquerda entra qualquer que seja a classe dele.

## 3. Regra 2: o rótulo `function_pt`

Seis regras de ocorrência, cada uma o teste mais estreito que separa a leitura que o modal nomeia da
leitura que está de fato ali. É lista de exceção, não classificador: o que os testes não alcançam
mantém o modal do par.

| regra | n | teste |
|---|---|---|
| `label-na-emphasis` | 5 | な final depois de だ/です/adjetivo-i/たい é ênfase, não proibição |
| `label-total-negation-mo` | 5 | も depois de interrogativo ou minimizador, em oração negada |
| `label-spatial-made` | 5 | まで em nominal não temporal com verbo de movimento na oração |
| `label-adverbial-ni` | 4 | に em radical de na-adjetivo antes de verbo (本当に, 順番に, 一緒に) |
| `label-copula-de` | 3 | で antes de ない/ある: é a cópula de ではない・でもある |
| `label-comitative-to` | 2 | と entre nominais, antes de 一緒に ou verbo recíproco |
| **total** | **24** | |

**As 24 linhas têm `function_status: verified`. Nenhuma está em `bank-modal`.** Isso não é acaso: a
passagem de verificação já tinha corrigido o rótulo em 88 outras ocorrências das mesmas seis regras.
Fazendo o back-test das seis regras sobre a derivação pré-verificação (onde todo `function_pt` ainda
é o modal cru), elas disparam **112 vezes**; a verificação moveu o rótulo em 88 e deixou o modal de
pé em 24. Nessas 24 o `explanation_pt` verificado costuma **contradizer o próprio rótulo em
palavras**:

> `彼らは敵と戦った。`, rótulo `partícula de citação`; explicação verificada: *"Este と marca 敵 como
> a outra parte do embate… **Não é o と de citação.**"*

> `私の両親はまだ年寄りではない。`, rótulo `partícula de lugar da ação`; explicação verificada:
> *"Este で é o で da cópula: ele abre ではない…"*

> `さあ、ボートから降りて岸まで泳ぎなさい。`, rótulo `limite temporal ('até')`; explicação
> verificada: *"…nadar até a margem e parar ali. **Aqui o limite é de espaço, não de tempo.**"*

Quer dizer: o verificador consertou a explicação e não mexeu no rótulo ao lado. Por isso as 24 linhas
saem marcadas com `overrides_verified: true` na tabela de reparo: aplicá-las sobrescreve um veredito
já dado, e isso é decisão de quem assina, não do script.

## 4. Regra 3: resolução de citação

Duas verificações mecânicas sobre as 6.987 explicações templatizadas:

1. **Template obsoleto.** Recalcular o template da v1 sobre a dissecação atual e comparar byte a byte
   com o texto guardado. **0 divergências**. Nenhuma explicação nomeia um token em posição errada,
   nenhuma ficou para trás de uma redissecação.
2. **Token citado ausente.** Cada corrida de escrita japonesa no texto tem de existir na frase ou ser
   o lema de algum token dela (o template cita lemas de propósito: もらう por もらった). **0
   ausências.**
3. **Alinhamento posição × superfície** entre `particles[].position` e o token do Sudachi naquele
   índice: **0 divergências** em todas as 4.320 frases.

O que a verificação de citação **achou** foi de outra natureza: 50 explicações citam um verbo que não
está fazendo o trabalho que o texto atribui a ele.

**`te-locution-withdraw`, 50 linhas.** として / について / によって / に対して / にとって / に関して
/ に基づいて / AからBにかけて tokenizam como 助詞 + 動詞 + て. O template de conectivo lia isso como
encadeamento de orações e produzia *"て liga とる ao que vem depois (有利)"*. O verbo nomeado não
existe como verbo ali; ele é metade de uma posposição composta. Essas 50 têm o template **retirado**
(`explanation_pt: null`, `explanation_status: author`) e voltam para a fila de autoria; não há texto
mecânico honesto para elas.

A regra tem duas travas, ambas testadas:

- um auxiliar depois do て desarma a retirada: 必要としている é 必要とする + ている, 事実に基づいて
  いる é 基づく + ている, 位置についていた é 付く + ていた, 脇によってください é 寄る + てください.
  São verbo de verdade com aspecto de verdade. Sem essa trava, 8 linhas seriam retiradas à toa.
- をもって saiu da lista (colide com 持って em 3 frases) e にかけて exige um から antes
  (AからBにかけて é a locução; 礼儀にかけている é 欠ける).

## 5. Trinta amostras para leitura humana

| # | frase | regra | antes | depois |
|---|---|---|---|---|
| 1 | 彼は直に腹を立てる。 | `chunk-adverbial-copula-dropped` | `直に腹` | `腹` |
| 2 | 彼は多少彼女の問題を理解している。 | `chunk-adverbial-noun-dropped` | `多少彼女` | `彼女` |
| 3 | 宗教については何の意見も持っていない。 | `te-locution-withdraw` | `て liga つく ao que vem depois (は)…` | _(volta para autoria)_ |
| 4 | 最近食欲がないんです。 | `chunk-adverbial-noun-dropped` | `最近食欲` | `食欲` |
| 5 | 家族はみな穀物の収穫にでていた。 | `chunk-adverbial-noun-dropped` | `みな穀物` | `穀物` |
| 6 | もうじきクリスマスが来る。 | `chunk-adverbial-noun-dropped` | `もうじきクリスマス` | `クリスマス` |
| 7 | ついに彼は目標を達した。 | `chunk-adverb-dropped` | `ついに彼` | `彼` |
| 8 | たとえ雨が降っても、私は出発する。 | `chunk-adverb-dropped` | `たとえ雨` | `雨` |
| 9 | この結婚は彼の将来にとって有利になるだろう。 | `te-locution-withdraw` | `て liga とる ao que vem depois (有利)…` | _(volta para autoria)_ |
| 10 | 最近面白いドラマが少ない気がする。 | `chunk-adverbial-noun-dropped` | `最近面白いドラマ` | `面白いドラマ` |
| 11 | カナダ人ならそんなこと言うわけがない。 | `chunk-adverbial-copula-dropped` | `カナダ人ならそんなこと言うわけ` | `そんなこと言うわけ` |
| 12 | 彼女はたとえ何を着てもかわいらしい。 | `chunk-adverb-dropped` | `たとえ何` | `何` |
| 13 | 彼は早く目が覚める。 | `chunk-verbal-adverbial-dropped` | `早く目` | `目` |
| 14 | 彼は社会にとって危険人物だ。 | `te-locution-withdraw` | `て liga とる ao que vem depois (危険)…` | _(volta para autoria)_ |
| 15 | 住民たちは騒音に対して苦情を訴えた。 | `te-locution-withdraw` | `て liga 対する ao que vem depois (苦情)…` | _(volta para autoria)_ |
| 16 | 私は昨日彼を訪問した。 | `chunk-adverbial-noun-dropped` | `昨日彼` | `彼` |
| 17 | 瓶には少し牛乳がある。 | `chunk-adverb-dropped` | `少し牛乳` | `牛乳` |
| 18 | 幼い頃はよく病気をしたものです。 | `chunk-adverb-dropped` | `よく病気` | `病気` |
| 19 | 彼は早く出発することを勧めた。 | `chunk-verbal-adverbial-dropped` | `早く出発すること` | `出発すること` |
| 20 | 特にこの場面が好きですねえ。 | `chunk-adverb-dropped` | `特にこの場面` | `この場面` |
| 21 | 確かに彼女は歌はうまいが、演技はだめだ。 | `chunk-adverbial-copula-dropped` | `確かに彼女` | `彼女` |
| 22 | 食べるのにどうしてそんなに手間がかかるのか。 | `chunk-adverbial-copula-dropped` | `そんなに手間` | `手間` |
| 23 | 更に質問がありますか。 | `chunk-conjunction-dropped` | `更に質問` | `質問` |
| 24 | 只より高い物はない。 | `chunk-conjunction-dropped` | `只より高い物` | `より高い物` |
| 25 | これはすごく栄養があります。 | `chunk-verbal-adverbial-dropped` | `すごく栄養` | `栄養` |
| 26 | 二人っきりで話したいな。 | `label-na-emphasis` | partícula final de proibição | partícula final de ênfase |
| 27 | 籠の中には何もない。 | `label-total-negation-mo` | partícula de inclusão ('também') | も de negação total (nada / ninguém / nenhum) |
| 28 | 彼らは敵と戦った。 | `label-comitative-to` | partícula de citação | と de companhia ('com') |
| 29 | 誰も抵抗できない。 | `label-total-negation-mo` | partícula de inclusão ('também') | も de negação total (nada / ninguém / nenhum) |
| 30 | それは意外だな。 | `label-na-emphasis` | partícula final de proibição | partícula final de ênfase |

A linha 24 é a mais fraca da leva e está aqui de propósito: em 只より高い物はない o Sudachi marca 只
como 接続詞 em vez de nome, então a regra derruba a metade errada e o trecho fica `より高い物`. Sai de
uma citação ruim para outra citação ruim; nenhuma das duas é falsa, e a v2 pelo menos tira o padrão
de comparação de dentro do sujeito.

## 6. O que **não** dá para consertar mecanicamente

| item | n | por quê |
|---|---|---|
| は de tópico × は de contraste | 2.421 | O template diz *"apresenta X como o tópico da frase"* em todos os は/binding templatizados. O は contrastivo (彼は来たが、私は来なかった) se prende a nominal exatamente igual ao temático. Nada na dissecação separa os dois; separar exige ler a frase inteira. As guardas atuais já excluem では / には / とは. **Decisão de autoria, não de regra.** |
| て antes de auxiliar de aspecto ou benefativo | 546 | 63% dos 862 て/conjunctive templatizados vêm antes de いる (418), くる (37), くれる (29), みる, しまう, おく, あげる, もらう. O texto *"liga X ao que vem depois (いる) e encadeia os dois dentro da mesma frase"* é literalmente verdadeiro mas pedagogicamente raso: ている não é encadeamento de orações, é aspecto. Consertar exige **texto novo de template**, ou seja, autoria, está fora do que esta unidade pode escrever. Fica registrado com a contagem. |
| nome 副詞可能 que também forma composto lexical | ~10 dentro das 64 | 現代芸術 → 芸術, 去年私が設計した庭 → 私, 今晩泊まる宿 → 泊まる宿. O Sudachi corta 現代芸術 exatamente como corta 明日雨; nem o modo A nem o modo C nem o dicionário distinguem os dois. A regra escolhe **estreitar**: o trecho fica mais curto e continua verdadeiro, em vez de mais longo e às vezes falso. |
| contador de duração antes de nome | 1 | もう一年仕事を続ける → `一年仕事`. 年 vem como 助数詞可能, não 副詞可能, então escapa do teste de nome adverbial. Uma regra de contador atingiria 五人家族 e 三年生 junto; não vale por uma linha. |
| erro de etiquetagem do Sudachi | 1 identificada | 只 como 接続詞 (linha 24 acima). Só se resolve com lista de exceção lexical, que não é regra. |
| まで temporal × de escopo | não medido | クリスマスまで (tempo) e 第二次大戦まで (escopo) são idênticos a um analisador. A regra espacial só dispara com verbo de movimento e fica calada no resto, em vez de chutar. |

## 7. Como aplicar

`research/derived/pending/particle_template_fixes.json` traz `how_to_apply` embutido. Em resumo,
casando em `(key, position)`:

- `explanation_change: "replace"` (201): `explanation_pt` vira `new_explanation`;
  `explanation_status` continua `template`.
- `explanation_change: "withdraw"` (50): `explanation_pt` vira `null` e `explanation_status` vira
  `author`; a linha volta para a fila de autoria.
- `function_pt_change: "replace"` (24): `function_pt` vira `new_function_pt` e `function_status`
  vira `occurrence-rule`. **Todas as 24 carregam `overrides_verified: true`**; segurar para
  assinatura antes de aplicar.

Nenhuma linha altera `key`, `position`, `particle` ou `function_type`. O arquivo está com
`needs_review: true`.
