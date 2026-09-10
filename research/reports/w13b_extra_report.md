# W13b extra — Layer-B for the 97 uncovered-target sentences, as one extra batch

The W13b campaign built the Layer-B for the 4,223 mined N3 sentences (batches 01-29,
`research/reports/w13b_assembly_report.md`). The 97 sentences written later for the N3 targets that
the miner left uncovered (`research/derived/n3_mined/generated_uncovered_final.json`: 35 real
Tatoeba rows re-found on a wider search, 62 generated) had no Layer-B at all. This unit produces it
the same way: derive first, put only the residue up for authoring, author the residue, leave the
verdicts to an independent verifier.

Nothing under batches 01-29 was touched, no exporter or ingest ran, and the assembler was not run.
The DB was read from a copy in the scratchpad, never from `db/corpus.sqlite`.

## 1. The derivation is the old one, and it was checked against the old one

`scripts/derive_layerb.py` reads its per-token gloss candidates out of `layerb_residue.json`, a
measurement artifact that covers only the original 4,223. The 97 new sentences have no record there,
so the gloss half of the derivation had to be reproduced from the DB. `scripts/derive_layerb_extra.py`
does that and imports everything else from `derive_layerb` unchanged: the numeral rule, the particle
template, the clause-structure predictor, `sentence_key` and `sentence_slug`.

The reproduction is not asserted, it is measured. `--selfcheck` replays the rebuilt rule over the
4,223 residue records:

| replayed over the original 4,223 | identical | different |
|---|---:|---:|
| token `gloss_pt` + `gloss_source` + `confidence` | **17,057** | 0 |
| token `role_pt_hint` | **17,057** | 0 |
| particle `function_pt` | **10,257** | 0 |

Two details had to be recovered to get there, and both are now written down in the script: the bank
lookup falls back from `(surface, lemma, pos_coarse)` to `(lemma, pos_coarse)` when the inflected
surface is not in the bank (this is what gives 悲し the gloss of 悲しい and ６０ the gloss of 60), and
ties in the modal are broken by `Counter.most_common` fed in `token.id` order.

## 2. What derived, and what was left over

97 sentences, 359 content tokens, 234 particles.

| slot | derived mechanically | left for authoring |
|---|---:|---:|
| token gloss | 354 (50 `unique-accept`, 304 `ambiguous-verify`) | 5 (`author`) |
| particle explanation | 121 (template) | 113 |
| particle `function_pt` | 232 (bank modal) | 2 |
| structure paragraph | 0 (never derived, by design) | 97 |

The 304 `ambiguous-verify` tokens are 175 `(lemma, pos)` pairs, and **161 of those pairs were already
settled by batches 01-29**. A ruling is a decision about a pair and the assembler applies it to every
ambiguous token with that key in every derived batch, batch-30 included, so those 161 pairs are
already answered here: re-ruling them would duplicate the identity and could contradict a decision an
independent verifier already signed. They cover 289 of the 304 tokens and are listed in the work file
under `reused_rulings`, with the text that will actually reach them. Only the remaining **14 pairs
(15 tokens)** were put up for authoring.

Which pairs count as settled is computed with the assembler's own reader (`pair_files`, `_kind`,
`_rows`, `_ident`, `decide` imported from `scripts/assemble_layerb.py`), so the subtraction cannot
drift from the merge: a ruling the assembler would drop counts as not ruled. All 1,563 rulings of
batches 01-29 come back effective, none rejected.

Clause classes predicted for the 97: simple 33, coordinate 23, topic-comment 22, question 12,
imperative 3, conditional 2, cause 1, fragment 1.

## 3. What was authored

| kind | rows | what it is |
|---|---:|---|
| `rulings` | **14** | the `(lemma, pos)` pairs batches 01-29 had not settled; 5 carry a `context_overrides` entry |
| `tokens` | **22** | 5 tokens the derivation could not gloss at all, plus 17 per-token context fixes |
| `particles` | **113** | every particle the template does not cover, explained in its own sentence |
| `paragraphs` | **97** | one structure paragraph per sentence |
| **total** | **246** | |

**The 14 new rulings.** しれる/verb, いただく/verb, たまる/verb, とんでも/adverb, めった/na-adjective,
パソコン/noun, 左右/noun, 暮れ/noun, 消費/noun, 老い/noun, 表/noun, 要する/verb, 身体/noun, 迫る/verb.
Five of them take a `context_overrides` entry because the pair-level sense and the sense in this
sentence genuinely differ, and the ruling has to stay right for the pair: いただく is "receber
(humilde)" but "comer, beber (humilde)" inside いただきます; たまる is "acumular-se, juntar-se" but
"aguentar" inside 〜てたまらない; 老い is "velhice" but "os velhos" inside 老いも若きも; 表 is おもて
"frente" but ひょう "tabela" inside 下の表; 要する is "exigir, requerer" but "resumir" inside 要するに.
消費 was ruled "consumo, gasto" rather than the registry's sense[0] "consumir; gastar", because the
decision is about the noun.

**The 22 token rows.** Five are the genuine residue: 得手 twice in 誰にでも得手不得手がある (the second
one under 不), 上質 in 上質の綿, and the two adverb heads ざっ and しきり that Sudachi splits off
ざっと and しきりに. The other 17 are context fixes on pairs that batches 01-29 already ruled, where
the settled decision is right for the pair and factually wrong in this sentence. They are written as
`tokens` rows on `(key, position)`, which the assembler applies *before* any ruling, so no settled
identity is disturbed. The list, with what was wrong:

| sentence | token | ruling from 01-29 | authored here |
|---|---|---|---|
| 121394 | 薄 (in 薄暮れ) | fino, rarefeito | fraco, tênue |
| 3430692 | 案 (in いい案) | escrivaninha; carteira (escolar) | ideia, plano |
| 77329 | 若き | se; caso (read as 若し) | os jovens |
| 78322 | 陸 | seis (the formal numeral) | terra firme |
| 83524 | 柄 (in 柄にもない) | cabo; empunhadura | feitio, índole |
| gen-23be841a7d6e | 位 | cerca de; mais ou menos | posição, cargo |
| gen-7ac2a488ddab | 空 (read から) | céu | vazio |
| gen-241636dce7a0 | つける (in 実をつける) | acender, ligar | dar (fruto) |
| gen-03c27c103a89 | 共 (in 共に) | sufixo de plural para pessoas | junto (em 共に) |
| gen-1b63f3193f07 | 実 (in 実に) | fruto | de fato (em 実に) |
| gen-c7134fba488c | 実 (in 実は) | fruto | verdade (em 実は) |
| gen-dab1d936d62f | 方々 (read ほうぼう) | pessoas (formal) | vários lugares |
| gen-5eca9027d7b3 | 市 (in 市が立つ) | cidade, município | feira, mercado |
| gen-9954c1fa54ce | 額 (read ひたい) | quantia, montante | testa |
| gen-09a4a8300a89 | 直 (in 直に) | imediato, logo | direto, pessoalmente |
| gen-4dc48e6d9e51 | なん (in なんでも) | o quê (em なんか) | o quê |
| gen-3b2fee497b46 | なん (in なんで) | o quê (em なんか) | o quê |

**The 113 particles.** The heavy pairs are に/case 26, も/binding 25, で/case 16, か/adverbial 7,
は/binding 6 (the では / ては shapes the template refuses), と/case 5. A large share of the generated
sentences are built around fixed connectives whose pieces Sudachi splits (いつでも, それでも, なんでも,
何とか, かもしれない, 必ずしも, ところで, ですから, なぜなら…), so most explanations name the block
the particle belongs to and say what the block does, rather than pretending the particle carries the
sense alone. Two particles (しも in 必ずしも, twice) had no bank label at all and got a `function_pt`
written alongside the explanation.

**The 97 paragraphs.** One to two sentences each, in the anchors' register: 72 characters at the
shortest, 109 median, 182 longest.

## 4. Coverage after the merge would run

Simulated slot by slot without running the assembler (`ruling` and `tokens` applied by the same
precedence the assembler uses). No slot is left empty:

| slot | filled by | n |
|---|---|---:|
| token | authored row (residue or context fix) | 22 |
| token | ruling written here | 10 |
| token | ruling written here, context override | 5 |
| token | ruling reused from batches 01-29 | 281 |
| token | derived, `unique-accept` | 41 |
| particle | template | 121 |
| particle | authored | 113 |
| paragraph | authored | 97 |

`token` slots 359, `particle` slots 234, `paragraph` slots 97. Holes: none. No `(lemma, pos)` in
`rulings-30.json` collides with a pair from batches 01-29, and no sentence key in `batch-30.json`
collides with a key from batches 01-29.

## 5. One defect left standing, on purpose

In `193877` (もしかすると明日雨が降るかもしれない) the が template says "が marca 明日雨 como o sujeito
de 降る". The left chunk it names runs two adjacent nominals together, and here they are not a
compound: 明日 is the time and 雨 is the subject. This is `derive_layerb.particle_template` behaving
as written, the same code that produced the 6,866 templated particles of batches 01-29, so it was
left alone rather than patched for one sentence. It is the only occurrence in the 97: of the 26
templated particles whose left chunk spans two or more content tokens, the other 25 are real
compounds (あのシャツ, 高い物, 大きな声, 美しいもの…). Flagged here for the verifier.

## 6. Files

New, none of them overwriting anything:

| file | what |
|---|---|
| `scripts/derive_layerb_extra.py` | the derivation for one extra input file, with `--selfcheck` |
| `scripts/build_layerb_work_extra.py` | the work list for the extra batch, minus everything already ruled |
| `research/derived/n3_mined/layerb_derived/batch-30.json` | 97 derived sentences, same shape as 01-29 |
| `research/derived/n3_mined/layerb_residue_extra.json` | the residue record for the 97 (surface, pos_coarse, vocab_id, role hint) |
| `research/derived/n3_mined/layerb_work/extra-30.json` | the four work lists in one file, plus `reused_rulings` |
| `research/derived/n3_mined/layerb_out/rulings-30.json` | 14 rows |
| `research/derived/n3_mined/layerb_out/tokens-residue-30.json` | 22 rows |
| `research/derived/n3_mined/layerb_out/particles-30.json` | 113 rows |
| `research/derived/n3_mined/layerb_out/paragraphs-30.json` | 97 rows |

Every authored row carries `verdict: null`. **No verdict file was written**, by instruction: an
independent verifier writes `<name>.json.verdict.json` next to each of the four, and until it does
the assembler will count these 246 rows as `unverified_excluded` and merge none of them. The
assembler has not been run.

Reproduce with:

```
python scripts/derive_layerb_extra.py --db <copy.sqlite> --selfcheck
python scripts/build_layerb_work_extra.py --db <copy.sqlite>
```

## 7. Ten sample sentences, full Layer-B

Seed 3013 over the 97. Origin per row: `derivada` = carried from the mechanical derivation,
`modelo` = the particle template, `regra reaproveitada` = a ruling from batches 01-29,
`regra nova` = a ruling written here, `autorada` = written here for this slot.

### 1. `11530592` (real (Tatoeba)) — 数分はかかります。

*les:n3-perspectiva-04 · alvos: vocab:1580825 · classe prevista: topic-comment*

pt: Vai levar alguns minutos.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | 数 (数) | número, quantidade | regra reaproveitada |
| 1 | 分 (分) | minuto(s) | regra reaproveitada |
| 3 | かかり (かかる) | levar, custar | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 2 | は | partícula de tópico | は apresenta 数分 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | modelo |

**Estrutura** (autorada) — 数分 vem com は como tópico e かかります é o predicado polido: o tempo gasto é o assunto, e o verbo diz apenas que ele será consumido.

### 2. `11814369` (real (Tatoeba)) — 口で息をして。

*les:n3-conectores-03 · alvos: vocab:1404320 · classe prevista: coordinate*

pt: Respira pela boca.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | 口 (口) | boca | regra reaproveitada |
| 2 | 息 (息) | respiração; fôlego | derivada |
| 4 | し (する) | fazer | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 1 | で | partícula de lugar da ação | で marca 口 como o meio pelo qual a respiração acontece: respirar usando a boca. | autorada |
| 3 | を | marcador de objeto direto | を marca 息 como o objeto direto de する, ou seja, aquilo sobre o que a ação recai. | modelo |
| 5 | て | partícula conectiva (forma て) | Este て fecha し e deixa o pedido em suspenso: é a forma curta de してください, o jeito informal de pedir. | autorada |

**Estrutura** (autorada) — 口で marca o meio com で, 息を é o objeto direto e して fecha na forma て, que sozinha funciona como pedido informal.

### 3. `174243` (real (Tatoeba)) — 御返事を御待ちしております。

*les:n3-conectores-05 · alvos: vocab:2826528 · classe prevista: coordinate*

pt: Fico no aguardo da sua resposta.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 1 | 返事 (返事) | resposta | regra reaproveitada |
| 4 | 待ち (待つ) | esperar, aguardar | regra reaproveitada |
| 5 | し (する) | fazer | regra reaproveitada |
| 7 | おり (おる) | estar (humilde) | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 2 | を | marcador de objeto direto | を marca 御返事 como o objeto direto de 待つ, ou seja, aquilo sobre o que a ação recai. | modelo |
| 6 | て | partícula conectiva (forma て) | て liga する ao que vem depois (おる) e encadeia os dois dentro da mesma frase. | modelo |

**Estrutura** (autorada) — 御返事を é o objeto direto e o predicado é 御待ちしております: o prefixo 御, o radical do verbo e しております montam a forma humilde e polida de quem aguarda.

### 4. `193877` (real (Tatoeba)) — もしかすると明日雨が降るかもしれない。

*les:n3-conjectura-01 · alvos: gram:n3-moshikasuru-to-kamoshirenai · classe prevista: coordinate*

pt: Pode ser que chova amanhã.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | もし (もし) | se, caso | regra reaproveitada |
| 2 | する (する) | fazer | regra reaproveitada |
| 4 | 明日 (明日) | amanhã | derivada |
| 5 | 雨 (雨) | chuva | derivada |
| 7 | 降る (降る) | cair (chuva, neve) | regra reaproveitada |
| 10 | しれ (しれる) | saber (dentro de かもしれない) | regra nova |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 1 | か | partícula de indefinição | か se prende a もし e abre もしかすると: deixa a hipótese no ar, sem afirmar nada ainda. | autorada |
| 3 | と | conjunção condicional (quando/sempre que) | と fecha する e completa もしかすると: apresenta o que vem depois como o caso que pode acontecer. | autorada |
| 6 | が | partícula de sujeito | が marca 明日雨 como o sujeito de 降る, isto é, quem faz ou de quem se diz o que o predicado exprime. | modelo |
| 8 | か | partícula de indefinição | か se apoia em 降る e abre かもしれない: transforma o 'vai chover' numa possibilidade. | autorada |
| 9 | も | partícula de inclusão ('também') | も entra entre o か e o しれない e completa かもしれない: é peça fixa da conjectura, não soma nada por conta própria. | autorada |

**Estrutura** (autorada) — もしかすると abre a frase avisando que vem uma hipótese. O núcleo é 雨が降る, com が marcando a chuva como sujeito, e かもしれない fecha reduzindo tudo a uma possibilidade.

### 5. `231320` (real (Tatoeba)) — あのシャツを着てみなさい。上質の綿でできています。

*les:n3-estado-08 · alvos: vocab:1533340 · classe prevista: imperative*

pt: Experimenta aquela camisa. Ela é de algodão de boa qualidade.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | あの (あの) | aquele | regra reaproveitada |
| 1 | シャツ (シャツ) | camisa | regra reaproveitada |
| 3 | 着 (着る) | vestir, usar (roupa) | regra reaproveitada |
| 5 | み (みる) | experimentar, tentar | regra reaproveitada |
| 6 | なさい (なさる) | faça (ordem educada) | regra reaproveitada |
| 8 | 上質 (上質) | boa qualidade | autorada (residue) |
| 10 | 綿 (綿) | algodão | derivada |
| 12 | でき (できる) | poder, conseguir | regra reaproveitada |
| 14 | い (いる) | estar | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 2 | を | marcador de objeto direto | を marca あのシャツ como o objeto direto de 着る, ou seja, aquilo sobre o que a ação recai. | modelo |
| 4 | て | partícula conectiva (forma て) | て liga 着る ao que vem depois (みる) e encadeia os dois dentro da mesma frase. | modelo |
| 9 | の | partícula de ligação/posse | の liga 上質 a 綿 e junta os dois num bloco só, em que 綿 é o núcleo e 上質 o modificador. | modelo |
| 11 | で | partícula de lugar da ação | で marca 綿 como o material de que a camisa é feita: com できている, で diz do que a coisa é feita. | autorada |
| 13 | て | partícula conectiva (forma て) | て liga できる ao que vem depois (いる) e encadeia os dois dentro da mesma frase. | modelo |

**Estrutura** (autorada) — Na primeira frase, あのシャツを é o objeto direto e 着てみなさい junta てみる, de tentativa, com なさい, de ordem branda. Na segunda, 上質の綿で marca o material com で e できています diz do que a camisa é feita.

### 6. `gen-1b63f3193f07` (gerada) — 実におもしろい話だ

*les:n3-conjectura-01 · alvos: vocab:2820720 · classe prevista: simple*

pt: É realmente uma história interessante.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | 実 (実) | de fato (em 実に) | autorada (context-fix) |
| 2 | おもしろい (おもしろい) | interessante, divertido | regra reaproveitada |
| 3 | 話 (話) | conversa, história | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 1 | に | partícula de destino/direção | に fecha 実 e forma 実に: reforça o que vem depois, 'realmente'. | autorada |

**Estrutura** (autorada) — 実に intensifica o que vem depois, おもしろい qualifica 話 e 話だ é o predicado nominal com a cópula casual.

### 7. `gen-40417a6920af` (gerada) — どんなに待っても来なかった

*les:n3-desejos-06 · alvos: vocab:1009340 · classe prevista: coordinate*

pt: Por mais que eu esperasse, não veio.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | どんな (どんな) | quão, o quanto | regra reaproveitada |
| 2 | 待っ (待つ) | esperar, aguardar | regra reaproveitada |
| 5 | 来 (来る) | vir, chegar | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 3 | て | partícula conectiva (forma て) | て liga 待つ ao que vem depois (も) e encadeia os dois dentro da mesma frase. | modelo |
| 4 | も | partícula de inclusão ('também') | も se junta ao て de 待って e forma ても: admite a espera e diz que, ainda assim, nada mudou. | autorada |

**Estrutura** (autorada) — どんなに待っても é a oração concessiva, montada com ても: por mais que se esperasse. A oração principal, 来なかった, diz que nada disso adiantou.

### 8. `gen-41f4c5632b0a` (gerada) — 町の灯がきれいに見える

*les:n3-conectores-07 · alvos: vocab:1582290 · classe prevista: simple*

pt: As luzes da cidade ficam lindas de ver.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | 町 (町) | cidade, vila | regra reaproveitada |
| 2 | 灯 (灯) | luz; claridade | derivada |
| 4 | きれい (きれい) | bonito, limpo | regra reaproveitada |
| 6 | 見える (見える) | ser visível, parecer | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 1 | の | partícula de ligação/posse | の liga 町 a 灯 e junta os dois num bloco só, em que 灯 é o núcleo e 町 o modificador. | modelo |
| 3 | が | partícula de sujeito | が marca 灯 como o sujeito de きれい, isto é, quem faz ou de quem se diz o que o predicado exprime. | modelo |

**Estrutura** (autorada) — 町の灯, ligado por の, é o sujeito com が; きれいに é o modo, com に transformando o adjetivo em advérbio, e 見える fecha.

### 9. `gen-85971f5e6f20` (gerada) — 行く？それとも行かない？

*les:n3-desejos-05 · alvos: vocab:1007010 · classe prevista: question*

pt: Você vai? Ou não vai?

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | 行く (行く) | ir | regra reaproveitada |
| 2 | それ (それ) | isso | regra reaproveitada |
| 5 | 行か (行く) | ir | regra reaproveitada |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 3 | と | partícula de citação | と se apoia em それ e, com o も seguinte, monta それとも: liga as duas perguntas como alternativas. | autorada |
| 4 | も | partícula de inclusão ('também') | も fecha それと e completa それとも: apresenta a segunda opção, 'ou então'. | autorada |

**Estrutura** (autorada) — Duas perguntas curtas emendadas por それとも, que apresenta a segunda como alternativa da primeira: a mesma raiz 行く aparece afirmada e negada.

### 10. `gen-c0358ac90d32` (gerada) — 明日は雨かもしれない

*les:n3-intencao-01 · alvos: vocab:1002970 · classe prevista: topic-comment*

pt: Amanhã pode ser que chova.

| pos | lema | glosa pt-BR | origem |
|---:|---|---|---|
| 0 | 明日 (明日) | amanhã | derivada |
| 2 | 雨 (雨) | chuva | derivada |
| 5 | しれ (しれる) | saber (dentro de かもしれない) | regra nova |

| pos | partícula | função | explicação | origem |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 明日 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | modelo |
| 3 | か | partícula de indefinição | か se apoia em 雨 e abre かもしれない: deixa a chuva como possibilidade, não como certeza. | autorada |
| 4 | も | partícula de inclusão ('também') | も entra entre o か e o しれない e completa かもしれない: é peça fixa da conjectura. | autorada |

**Estrutura** (autorada) — 明日 é o tópico com は e 雨 é o predicado nominal; かもしれない fecha reduzindo a chuva a uma possibilidade.

