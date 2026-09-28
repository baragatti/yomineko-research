# Particle functions: classes, usages, explanation templates

**Status:** proposal, 2026-09-27. Nothing in `corpus/` uses these ids yet. The measurement behind the
design and the migration plan are in
[`research/reports/particle_taxonomy_research.md`](../research/reports/particle_taxonomy_research.md).
**Data + schema:** [`particle_functions.json`](particle_functions.json) (JSON Schema 2020-12; the file
validates against itself). **Companion:** [`token_roles.md`](token_roles.md) for the other word-by-word
items.

## 1. Why

A particle row in `corpus/sentences/bank.json` has three fields today:

- `function_type`: a six-value enum. In 24,756 of 24,771 rows it is a copy of Sudachi's `pos_fine`
  (格助詞 → `case`, 係助詞 → `binding` ...). It says which class the particle belongs to, not what it
  means. に as time, に as destination and に as passive agent all carry `case`.
- `function`: free text. 4,970 distinct pt-BR strings. に/case alone has 833 distinct English labels.
- `explanation`: free prose.

You can't build "all に of time point" exercises from that, and a validator can't check it. This file adds
the missing layer, the **usage**: one closed, enumerable id per meaning of a particle. The explanation
text is then **rendered** from the usage, not authored.

## 2. The model

Each particle occurrence carries:

| layer | field | what it is | who sets it |
|---|---|---|---|
| class | `function_type` | grammatical class of the particle *in this use* (§3) | derived: `usages[usage].class` |
| usage | `usage` | the meaning, from the closed enum (§6) | mechanical rule, verified, or ruled (research report §4) |
| role | via `usages[usage].role` | role the particle gives the chunk it closes (`time`, `goal`, `topic` ...), defined in [`token_roles.json`](token_roles.json) | derived |
| text | `explanation` | rendered from `usages[usage].template` + slots | renderer, never authored |
| note | `note` (optional) | free text for what the template cannot say | author, optional |

The per-occurrence shape is `$defs.particle_annotation` in the JSON. Two fields matter most:

- **`position`** (required): the C-mode token position. Today's export drops it, so in 966 sentences
  where the same particle occurs twice, 2,149 rows cannot be tied back to their token. The DB already
  holds the link (`particle.token_id`), so the export only has to publish it.
- **`usage_status`**: how the usage was assigned (`auto`, `cue-only`, `label-only`, `default`, `ruled`,
  `verified`, `tokenization-error`). A consumer that wants only safe rows filters on it.

`function_type` stays for compatibility. After migration it must equal `usages[usage].class`, and the
validator checks that.

## 3. Classes

| id | 学校文法 / 日本語教育 | UniDic pos_fine | is particle | en |
|---|---|---|---|---|
| `case` | 格助詞 | 格助詞 | yes | case particle: marks the relation of a noun phrase to the predicate |
| `binding` | 係助詞・とりたて助詞 | 係助詞 | yes | focus (toritate) particle: topic, contrast, addition, limit |
| `adverbial` | 副助詞 | 副助詞 | yes | adverbial particle: degree, extent, approximation, example |
| `conjunctive` | 接続助詞 | 接続助詞 | yes | conjunctive particle: links a clause to the next |
| `sentence-final` | 終助詞 | 終助詞 | yes | sentence-final particle: speaker attitude toward the listener or the content |
| `nominalizer` | 準体助詞 | 準体助詞 | yes | nominalizer: turns a clause or modifier into a noun phrase |
| `parallel` | 並立助詞 | 格助詞, 副助詞 | yes | parallel particle: joins items of a list (UniDic has no such class; it files と as 格助詞 and や/か as 副助詞) |
| `copula-form` | 助動詞「だ」の連用形 | 格助詞, 接続助詞 | no | NOT a particle: continuative form of the copula だ that tokenizers or authors filed as a particle (静かに, 学生で) |
| `lexicalized` | 語の構成要素 | 格助詞, 係助詞, 副助詞, 接続助詞, 終助詞, 準体助詞 | yes | frozen part of a word or fixed expression (それから, かもしれない); no usage of its own |

Notes on the classes:

- **は / も** are 係助詞 in school grammar (学校文法, the 橋本 tradition) and in UniDic. Japanese-teaching
  grammar calls them とりたて助詞 (focus particles), a group that also takes だけ, しか, さえ, こそ and
  others that UniDic files as 副助詞. The `binding` class keeps UniDic's line for は, も and こそ, so
  `class` stays checkable against `pos_fine`. The とりたて meaning goes into the usage (`focus` role).
- **`parallel`** (並立助詞) has no UniDic class. UniDic files parallel と as 格助詞 and や / か / やら as
  副助詞. The class is a property of the usage (`to.parallel`), not of the token, which is why `class` sits
  on the usage and not on the particle.
- **`copula-form`** is not a particle. It holds rows the tokenizer or the authors filed as a particle but
  that are the continuative of だ: the に of 静かに and the で of ではない. They get an id so the rows are
  not lost, and `is_particle: false` so drills skip them.
- **`lexicalized`** is a particle frozen inside a word or set phrase: the から of それから, the か of
  かもしれない, the も of けれども. It has no meaning of its own, and it gets one id, `lex.fixed`.

## 4. Usage ids

`<key>.<usage>`, for example `ni.time-point`, `de.means`, `ha.contrast`.

- **key** is the Hepburn romaji of the particle's kana *spelling*, so は = `ha`, を = `wo`, へ = `he`,
  わ = `wa`. Using the spelling rather than the pronunciation keeps the key one-to-one with the surface
  (は and わ would otherwise both be `wa`). Keys are internal and never shown to learners.
- Compound usages that span several tokens take the compound's romaji as key: `madeni.deadline` (まで+に),
  `node.reason` (の+で), `noni.concessive` (の+に), `kana.wondering` (か+な), `nitsuite.about`.
- **Allomorphs share one id.** The explanatory ん is `no.explanatory` like の; the voiced で of 読んで is
  `te.*` like て; ぐらい is `kurai.approximation`. The surface stays on the token, and the meaning is the
  same.
- Ids are English and locale-neutral (design/i18n.md). Labels and template text are locale objects.

## 5. Record fields

| field | meaning |
|---|---|
| `id`, `key`, `usage` | the id and its two halves |
| `particle`, `allomorphs` | canonical surface and the other surfaces of the same usage; for a compound, the remaining tokens in order |
| `compound` | the usage spans several tokens; annotations then carry `positions` |
| `class` | particle class in this use (§3) |
| `ja_term` | the term Japanese grammar references use (時, 到達点, 相手 ...), so a teacher can check each row against a reference grammar |
| `label` | short name, pt-BR + en |
| `desc` | the phrase the template inserts as `{desc}` |
| `role` | chunk role the usage assigns (token_roles.json) |
| `level` | level at which the usage is first taught; data, not structure (N1-N3 rows can be added) |
| `pattern` | pattern hint: `N` noun, `V` verb, `A` i-adjective, `Na` na-adjective, `S` clause, `Num` number |
| `cues` | ids of the mechanical context rules that select this usage (§8) |
| `contrasts` | usages a learner confuses with this one; the distractor source for choice drills |
| `interchangeable` | usages that are *also correct* in the same slot (`ni.goal` / `he.direction`, `kara.reason` / `node.reason`); a choice drill must never offer one as a wrong answer |
| `template` | explanation template id (§7) |
| `examples` | at least one short example; may carry a `sent:` slug once a bank sentence is chosen |

## 6. Usages

`in bank*` = occurrences the migration measurement assigned to the usage (any tier except `ruling`) over
the 24,771 particle rows of the 2026-09-27 snapshot. It is an estimate, not ground truth; see the research
report §4. `—` marks a compound the measurement did not count as a unit.

| id | particle | class | 日本語 term | en | pt-BR | role | level | in bank* | example |
|---|---|---|---|---|---|---|---|---|---|
| `ga.subject` | が | case | 主格（主体） | subject | sujeito | subject | N5 | 2089 | 雨が降っている |
| `ga.stative-object` | が | case | 対象（状態述語） | object of a state predicate (like, can, want, understand) | objeto de predicado de estado (gostar, saber, querer, entender) | stative-object | N5 | 210 | 猫が好きです |
| `ga.contrast` | が | conjunctive | 逆接 | but (contrast between clauses) | mas (contraste entre orações) | clause-link | N5 | 37 | 高いですが、買います |
| `ga.preface` | が | conjunctive | 前置き | softening preface before a request or question | introdução que suaviza um pedido ou pergunta | clause-link | N4 | 28 | すみませんが、駅はどこですか |
| `wo.object` | を | case | 対象（目的語） | direct object | objeto direto | object | N5 | 2719 | パンを食べる |
| `wo.path` | を | case | 経過域 | route or space moved through | percurso (por onde se passa) | path | N4 | 49 | 公園を散歩する |
| `wo.departure` | を | case | 起点 | point left behind (leave, get off, graduate) | ponto de onde se sai | source | N4 | 21 | 七時に家を出る |
| `wo.causee` | を | case | 使役の相手 | person made or let to act (causative of an intransitive verb) | pessoa levada a agir (causativo de verbo intransitivo) | causee | N4 | 21 | 子どもを遊ばせる |
| `ni.location-existence` | に | case | 存在の場所 | place where something is | lugar onde algo está | location | N5 | 376 | 机の上に本がある |
| `ni.time-point` | に | case | 時 | point in time | momento (quando) | time | N5 | 256 | 七時に起きる |
| `ni.goal` | に | case | 到達点・帰着点 | destination or arrival point | destino (aonde se vai ou chega) | goal | N5 | 376 | 駅に着いた |
| `ni.purpose` | に | case | 移動の目的 | purpose of going or coming | finalidade de ir ou vir | purpose | N5 | 63 | 映画を見に行く |
| `ni.recipient` | に | case | 相手（授与・伝達） | recipient or addressee (give, tell, meet) | destinatário (quem recebe, ouve ou é encontrado) | recipient | N5 | 166 | 友達にプレゼントをあげる |
| `ni.source` | に | case | 相手（受け取りの起点） | person something is received from (もらう, 借りる, 習う) | pessoa de quem se recebe (もらう, 借りる, 習う) | source | N4 | 7 | 先生に辞書を借りた |
| `ni.agent` | に | case | 受身・「〜てもらう」の動作主 | agent of a passive or of 〜てもらう | quem pratica a ação na voz passiva ou em 〜てもらう | agent | N4 | 98 | 先生に褒められた |
| `ni.causee` | に | case | 使役の相手 | person made or let to do something (causative) | pessoa levada ou autorizada a fazer algo (causativo) | causee | N4 | 4 | 子どもに野菜を食べさせる |
| `ni.result` | に | case | 変化の結果 | result of a change (なる, する) | resultado de uma mudança (なる, する) | result | N5 | 296 | 医者になりたい |
| `ni.frequency` | に | case | 割合 | rate (per) | proporção (por) | quantity | N4 | 1 | 一週間に二回泳ぐ |
| `ni.standard` | に | case | 状態・評価の基準 | reference point of a state or judgment (近い, いい, 似る) | ponto de referência de um estado ou avaliação (近い, いい, 似る) | standard | N4 | 48 | 駅に近い |
| `ni.target` | に | case | 心的態度・働きかけの対象 | target of an attitude or action (慣れる, 気をつける, 反対する) | alvo de uma atitude ou ação (慣れる, 気をつける, 反対する) | target | N4 | 132 | 車に気をつけて |
| `ni.cause` | に | case | 原因・理由 | cause of a feeling or state | causa de um sentimento ou estado | cause | N3 | 16 | その知らせに驚いた |
| `ni.parallel` | に | parallel | 並列・添加 | listing by addition (A に B) | enumeração por acréscimo | parallel-item | N2 | 0 | パンに牛乳を買った |
| `ni.adverbial` | に | copula-form | 連用形（副詞的） | adverb-forming に after a na-adjective | に que forma advérbio depois de adjetivo-na | adverbial | N5 | 60 | 静かに話す |
| `he.direction` | へ | case | 方向 | direction (toward) | direção (rumo a) | goal | N5 | 124 | 日本へ行く |
| `to.comitative` | と | case | 共同者・相互動作の相手 | companion or partner in a mutual action | companhia ou parceiro de uma ação mútua | comitative | N5 | 36 | 友達と映画を見た |
| `to.parallel` | と | parallel | 並立（全部列挙） | and (complete list of nouns) | e (lista completa) | parallel-item | N5 | 96 | パンと牛乳を買った |
| `to.quotative` | と | case | 引用 | quotation: content of saying or thinking | citação: o que se diz ou pensa | quote | N4 | 189 | 明日は雨だと思う |
| `to.comparison` | と | case | 比較の基準 | standard of comparison (同じ, 違う, 比べる) | referência de comparação (同じ, 違う, 比べる) | standard | N4 | 13 | これはそれと同じだ |
| `to.result` | と | case | 変化の結果（書き言葉） | result of a change (written, となる) | resultado de mudança (escrito, となる) | result | N3 | 39 | 会議は中止となった |
| `to.conditional` | と | conjunctive | 条件（自然の帰結） | when / whenever (natural consequence) | quando / sempre que (consequência natural) | clause-link | N4 | 103 | 春になると暖かくなる |
| `de.location-action` | で | case | 動作の場所 | place where an action happens | lugar onde a ação acontece | location-action | N5 | 513 | 図書館で勉強する |
| `de.means` | で | case | 手段・道具・方法 | means, tool, or language | meio, instrumento ou língua | means | N5 | 169 | バスで行く |
| `de.material` | で | case | 材料 | material something is made of | material de que algo é feito | material | N4 | 24 | 木で机を作る |
| `de.cause` | で | case | 原因・理由 | cause or reason | causa ou motivo | cause | N4 | 53 | 風邪で休んだ |
| `de.scope` | で | case | 範囲・領域 | scope (in, among) | âmbito (em, entre) | scope | N4 | 33 | クラスで一番背が高い |
| `de.limit` | で | case | 限度（時間・数量） | limit of time or amount (in, for) | limite de tempo ou quantidade (em, por) | quantity | N4 | 12 | 三つで百円です |
| `de.manner` | で | case | 様態・主体の状態 | manner or state of the doer (alone, all together) | modo ou estado de quem age (sozinho, todos juntos) | manner | N5 | 24 | 一人で行く |
| `de.copula` | で | copula-form | 「だ」の連用形 | continuative of the copula (ではない, 学生で、…) | forma contínua da cópula (ではない, 学生で、…) | predicate | N5 | 24 | 学生ではない |
| `kara.starting-point` | から | case | 起点（空間・時間） | starting point in space or time (from) | ponto de partida no espaço ou no tempo (de, a partir de) | source | N5 | 182 | 九時から働く |
| `kara.source` | から | case | 出どころ・相手 | person or place something comes from | de quem ou de onde algo vem | source | N4 | 4 | 母から手紙が来た |
| `kara.material` | から | case | 原料 | raw material (made from) | matéria-prima (feito de) | material | N4 | 17 | ワインはぶどうから作る |
| `kara.after` | から | case | 継起（〜てから） | after doing (〜てから) | depois de fazer (〜てから) | clause-link | N5 | 12 | 食べてから出かける |
| `kara.reason` | から | conjunctive | 理由 | because (reason) | porque (motivo) | clause-link | N5 | 79 | 暑いから窓を開けた |
| `made.until` | まで | adverbial | 終点（時間） | until (end point in time) | até (limite no tempo) | end-point | N5 | 42 | 五時まで働く |
| `made.as-far-as` | まで | adverbial | 終点（空間・範囲） | as far as (end point in space or range) | até (limite no espaço ou num intervalo) | end-point | N5 | 25 | 駅まで歩く |
| `made.even` | まで | adverbial | 極端な例（意外） | even (extreme example) | até (mesmo) (exemplo extremo) | focus | N3 | 0 | 子どもまで知っている |
| `madeni.deadline` | まで + に | adverbial | 期限 | by (deadline) | até (prazo) | time | N4 | 12 | 五時までに帰る |
| `yori.comparison` | より | case | 比較の基準 | than (standard of comparison) | (do) que (termo de comparação) | standard | N5 | 92 | 今日は昨日より暑い |
| `yori.starting-point` | より | case | 起点（書き言葉） | from (formal starting point) | a partir de (formal) | source | N3 | 0 | 十時より開始します |
| `no.noun-modifier` | の | case | 連体修飾（所有・所属・属性） | noun-to-noun link (possession, affiliation, attribute) | liga substantivos (posse, pertença, atributo) | modifier | N5 | 2158 | 私の本 |
| `no.subject-in-modifier` | の | case | 主格（連体修飾節内） | subject inside a noun-modifying clause (が → の) | sujeito dentro de oração que modifica um substantivo (が → の) | subject | N4 | 87 | 私の好きな本 |
| `no.nominalizer` | の / ん | nominalizer | 準体（名詞化） | turns a clause into a noun (〜のが好き) | transforma a oração em substantivo (〜のが好き) | nominalized-clause | N5 | 218 | 泳ぐのが好きだ |
| `no.pronoun` | の | nominalizer | 準体（代名詞的） | the one (stands for a noun) | o/a (substitui um substantivo) | nominalized-clause | N4 | 6 | 赤いのがいい |
| `no.explanatory` | の / ん | nominalizer | 説明（のだ・んです） | explanatory (のだ / んです) | explicativo (のだ / んです) | predicate | N5 | 321 | 頭が痛いんです |
| `no.final-question` | の | sentence-final | 質問（くだけた） | casual question | pergunta informal | sentence-final | N4 | 122 | どこに行くの？ |
| `no.final-explanation` | の | sentence-final | 説明（くだけた） | casual explanation or emphasis | explicação ou ênfase informal | sentence-final | N4 | 13 | 今日は行かないの |
| `ha.topic` | は | binding | 主題 | topic | tópico | topic | N5 | 4628 | 私は学生です |
| `ha.contrast` | は | binding | 対比 | contrast | contraste | topic | N5 | 594 | 肉は食べるが、魚は食べない |
| `mo.also` | も | binding | 累加・同類 | also, too | também | focus | N5 | 204 | 私も行く |
| `mo.both` | も | binding | 並列（AもBも） | both … and / neither … nor | tanto … quanto / nem … nem | focus | N5 | 40 | 肉も魚も食べる |
| `mo.total-negation` | も | binding | 全否定 | total negation (nothing, nobody) | negação total (nada, ninguém) | focus | N5 | 79 | 何も食べない |
| `mo.emphasis-quantity` | も | binding | 数量の強調 | as many/much as (quantity felt as large) | nada menos que (quantidade vista como grande) | focus | N4 | 28 | 三時間も待った |
| `mo.concessive` | も | binding | 逆接仮定（〜ても） | even if (〜ても) | mesmo que (〜ても) | clause-link | N4 | 225 | 雨が降っても行く |
| `koso.emphasis` | こそ | binding | 際立ち | precisely, the very (emphasis) | justamente, é que (ênfase) | focus | N3 | 6 | 今年こそ合格したい |
| `dake.only` | だけ | adverbial | 限定 | only, just | só, apenas | focus | N5 | 54 | 水だけ飲む |
| `shika.only-negative` | しか | adverbial | 限定（否定と呼応） | nothing but (with a negative) | só (com verbo negativo) | focus | N4 | 31 | 百円しかない |
| `bakari.only` | ばかり / ばっかり | adverbial | 限定（〜ばかり） | nothing but, always | só, sempre (em excesso) | focus | N4 | 24 | 甘いものばかり食べる |
| `bakari.just-done` | ばかり / ばっかり | adverbial | 直後（〜たばかり） | have just done | acabar de fazer | predicate | N4 | 7 | 今着いたばかりだ |
| `hodo.degree` | ほど / 程 | adverbial | 程度・比較 | to the extent of; (not) as … as | tanto quanto; (não) tão … quanto | standard | N4 | 37 | 今年は去年ほど寒くない |
| `kurai.approximation` | くらい / ぐらい | adverbial | 概数・程度 | about, approximately; to the degree that | cerca de, mais ou menos; a ponto de | quantity | N5 | 71 | 一時間くらいかかる |
| `nado.examples` | など / なんか / なんて | adverbial | 例示・評価 | things like, and so on | coisas como, entre outros | focus | N4 | 30 | りんごやみかんなどを買った |
| `zutsu.distributive` | ずつ / づつ | adverbial | 配分 | each, at a time | cada, de … em … | quantity | N4 | 10 | 一人二つずつ取る |
| `sae.even` | さえ / すら | adverbial | 極端な例 | even | até (mesmo) | focus | N3 | 9 | 名前さえ書けない |
| `tte.quotative` | って | adverbial | 引用（くだけた） | casual quotation or hearsay (= と / そうだ) | citação ou boato informal (= と / そうだ) | quote | N4 | 24 | 明日休みだって |
| `tte.topic` | って | adverbial | 主題（くだけた） | casual topic (= は / というのは) | tópico informal (= は / というのは) | topic | N4 | 41 | 日本語って難しいね |
| `ya.partial-list` | や | parallel | 並立（例示） | and (partial list, among others) | e (lista parcial, entre outros) | parallel-item | N5 | 23 | りんごやバナナを買った |
| `ka.alternative` | か | parallel | 並立（選択） | or (choice between items) | ou (escolha entre itens) | parallel-item | N4 | 14 | コーヒーか紅茶を飲む |
| `ka.indefinite` | か | adverbial | 不定 | some- (何か, 誰か, どこか) | algum (何か, 誰か, どこか) | modifier | N5 | 88 | 何か食べたい |
| `ka.embedded-question` | か | adverbial | 間接疑問 | embedded question (whether, what) | pergunta indireta (se, o que) | quote | N4 | 71 | 彼が来るか分からない |
| `tari.representative` | たり / だり | adverbial | 例示列挙（〜たり〜たり） | doing things like … and … | fazer coisas como … e … | clause-link | N4 | 23 | 本を読んだり音楽を聞いたりする |
| `demo.example` | で + も | adverbial | 例示（〜でも） | … or something (soft suggestion) | … ou algo assim (sugestão suave) | focus | N4 | — | お茶でも飲みませんか |
| `demo.even` | で + も | adverbial | 極端な例（〜でも） | even (N でも) | até (mesmo) | focus | N4 | — | 子どもでも分かる |
| `te.sequence` | て / で | conjunctive | 継起 | and then (sequence) | e depois (sequência) | clause-link | N5 | 436 | 朝起きて、顔を洗う |
| `te.manner` | て / で | conjunctive | 付帯状況・手段 | manner or means (by doing, while in a state) | modo ou meio (fazendo, no estado de) | clause-link | N4 | 2 | 歩いて学校に行く |
| `te.cause` | て / で | conjunctive | 原因・理由 | because (cause of a feeling or state) | porque (causa de sentimento ou estado) | clause-link | N4 | 23 | 遅れてすみません |
| `te.parallel` | て / で | conjunctive | 並列 | and (joining adjectives or clauses) | e (juntando adjetivos ou orações) | clause-link | N5 | 35 | 安くておいしい |
| `te.subsidiary` | て / で | conjunctive | 補助動詞への接続 | link to a subsidiary verb (〜ている, 〜てください, 〜てみる) | ligação a um verbo auxiliar (〜ている, 〜てください, 〜てみる) | predicate | N5 | 1597 | 本を読んでいる |
| `te.request` | て / で | conjunctive | 依頼（文末） | casual request (sentence-final 〜て) | pedido informal (〜て no fim) | predicate | N4 | 88 | ちょっと待って |
| `teha.condition` | ては / ちゃ / じゃ | conjunctive | 条件（否定的評価） | if (with a negative judgment: 〜てはいけない) | se (com avaliação negativa: 〜てはいけない) | clause-link | N4 | 76 | ここで写真を撮ってはいけない |
| `ba.conditional` | ば | conjunctive | 仮定条件 | if (conditional) | se (condição) | clause-link | N4 | 141 | 安ければ買う |
| `kedo.contrast` | けど / けれど / けれども | conjunctive | 逆接 | but, although | mas, embora | clause-link | N4 | 24 | 高いけど、買う |
| `kedo.softening` | けど / けれど / けれども | conjunctive | 言いさし・前置き | trailing but (softens the sentence) | mas… (suaviza a frase, deixando-a em aberto) | clause-link | N4 | 28 | ちょっと聞きたいんですけど |
| `node.reason` | の + で | conjunctive | 理由（〜ので） | because (softer, explanatory) | porque (mais suave, explicativo) | clause-link | N4 | — | 雨なので、行かない |
| `noni.concessive` | の + に | conjunctive | 逆接（〜のに） | even though (with surprise or regret) | apesar de (com surpresa ou frustração) | clause-link | N4 | — | 勉強したのに、落ちた |
| `noni.purpose` | の + に | case | 用途・目的（〜のに） | for (purpose: 〜のに使う/いい) | para (finalidade: 〜のに使う/いい) | purpose | N4 | 1 | これは野菜を切るのに使う |
| `nagara.simultaneous` | ながら | conjunctive | 同時動作 | while (two actions at once) | enquanto (duas ações ao mesmo tempo) | clause-link | N4 | 9 | 音楽を聞きながら勉強する |
| `shi.listing-reasons` | し | conjunctive | 並列・理由の列挙 | and also (listing reasons) | e além disso (lista de motivos) | clause-link | N4 | 17 | 安いし、おいしいし、この店が好きだ |
| `tatte.concessive` | たって / だって | conjunctive | 逆接仮定（くだけた） | even if (casual) | mesmo que (informal) | clause-link | N3 | 2 | 今から行ったって間に合わない |
| `tsutsu.simultaneous` | つつ | conjunctive | 同時・逆接（書き言葉） | while (written); even while | enquanto (escrito); embora | clause-link | N2 | 3 | 悪いと知りつつ、やってしまった |
| `ka.question` | か | sentence-final | 疑問 | question | pergunta | sentence-final | N5 | 678 | 学生ですか |
| `ka.invitation` | か | sentence-final | 勧誘（〜ませんか） | invitation (〜ませんか) | convite (〜ませんか) | sentence-final | N5 | 33 | 一緒に行きませんか |
| `ka.acknowledgment` | か | sentence-final | 納得・確認（そうですか） | acknowledging new information (そうですか) | recebe uma informação nova (そうですか) | sentence-final | N5 | 1 | そうですか |
| `kana.wondering` | か + な | sentence-final | 疑い・自問（〜かな） | I wonder | será que | sentence-final | N4 | 21 | 明日晴れるかな |
| `kashira.wondering` | かしら | sentence-final | 疑い・自問 | I wonder (soft) | será que (suave) | sentence-final | N3 | 12 | 雨が降るかしら |
| `yo.assertion` | よ | sentence-final | 告知・主張 | informs or asserts to the listener | informa ou afirma ao ouvinte | sentence-final | N5 | 449 | この店、おいしいよ |
| `yo.urging` | よ | sentence-final | 勧め・促し | urging (〜ましょうよ, 〜てよ) | insistência (vamos!, faça!) | sentence-final | N4 | 34 | 早く行こうよ |
| `ne.confirmation` | ね / ねえ / ねぇ | sentence-final | 確認・同意要求 | seeks agreement or confirmation | busca concordância ou confirmação | sentence-final | N5 | 177 | いい天気ですね |
| `na.prohibition` | な | sentence-final | 禁止 | don't (blunt prohibition) | não (proibição direta) | sentence-final | N4 | 80 | ここで泳ぐな |
| `na.emotive` | な / なあ / なぁ | sentence-final | 詠嘆・感嘆 | exclamation or musing | exclamação ou reflexão | sentence-final | N4 | 89 | いいなあ |
| `na.soft-command` | な | sentence-final | 命令（〜な = なさい） | soft order (V-stem な = なさい) | ordem suave (= なさい) | sentence-final | N3 | 0 | 早く寝な |
| `wa.emphasis` | わ | sentence-final | 詠嘆・軽い主張 | soft emphasis (feminine or Kansai) | ênfase suave (feminina ou de Kansai) | sentence-final | N3 | 26 | もう帰るわ |
| `zo.emphasis` | ぞ / ぜ | sentence-final | 強い主張 | strong assertion (masculine, casual) | afirmação forte (masculina, informal) | sentence-final | N3 | 13 | 行くぞ |
| `sa.assertion` | さ | sentence-final | 軽い主張 | light assertion (casual) | afirmação leve (informal) | sentence-final | N3 | 7 | 大丈夫さ |
| `kke.recall` | っけ | sentence-final | 想起・確認 | trying to recall (what was it again?) | tentando lembrar (como era mesmo?) | sentence-final | N3 | 8 | 名前、何だっけ |
| `mono.justification` | もの / もん | sentence-final | 理由・言い訳 | because, you see (justifying) | é que… (justificativa) | sentence-final | N3 | 5 | だって、眠いもん |
| `jan.confirmation` | じゃん | sentence-final | 確認（くだけた） | isn't it (casual confirmation) | não é? (confirmação informal) | sentence-final | N3 | 1 | いいじゃん |
| `nitsuite.about` | に + つい + て | case | 複合格助詞（〜について） | about, concerning | sobre, a respeito de | topic | N4 | — | 日本の文化について話す |
| `toiu.naming` | と + いう | case | 引用・命名（〜という） | called, named (N という N) | chamado (N という N) | modifier | N4 | 26 | 田中という人 |
| `to.adverbial` | と | case | 副詞の一部（様態の「と」） | adverb marker (ゆっくりと, 高々と) | marca de advérbio (ゆっくりと, 高々と) | adverbial | N4 | 22 | ゆっくりと歩く |
| `kai.question` | か + い | sentence-final | 疑問（くだけた・男性的） | casual question (かい) | pergunta informal (かい) | sentence-final | N3 | 8 | 用意はいいかい |
| `nomi.only` | のみ | adverbial | 限定（書き言葉） | only (formal) | somente (formal) | focus | N2 | 3 | 会員のみ入れる |
| `yara.listing` | やら | parallel | 並立（例示・不確か） | and … and such (uncertain listing) | e … e tal (lista incerta) | parallel-item | N2 | 5 | 風やら雨やらで大変だった |
| `lex.fixed` | * | lexicalized | 語の構成要素 | part of a fixed word or expression | parte de uma palavra ou expressão fixa | none | N5 | 606 | それから、家に帰った |

Usages with zero hits are kept on purpose. N5/N4 materials teach them, or they are the contrast pair of
a usage that does occur. `ka.acknowledgment` (そうですか) is one example: it has one sentence in the bank
and belongs to N5.

## 7. Explanation templates

The explanation is `templates[usage.template][locale].format(desc=usage.desc[locale], **slots)`, plus an
optional `note`. The slots come from the tokens:

- `particle`: the token surface
- `chunk`: the chunk the particle closes, using `chunk_head()` from `scripts/derive_layerb_templates_v2.py`
  (head plus genuine modifiers only; the W13b audit fixed it)
- `left`: the clause a conjunctive particle or nominalizer closes
- `expression`: the compound or fixed expression

| id | slots | pt-BR | en |
|---|---|---|---|
| `tpl.compound` | expression, desc | {expression} funciona como uma unidade só: {desc}. | {expression} works as a single unit: {desc}. |
| `tpl.copula-form` | particle, chunk, desc | Aqui {particle} não é partícula: é a cópula だ na forma contínua depois de {chunk}, {desc}. | Here {particle} is not a particle: it is the copula だ in its continuative form after {chunk}, {desc}. |
| `tpl.focus` | particle, chunk, desc | {particle} destaca {chunk}: {desc}. | {particle} highlights {chunk}: {desc}. |
| `tpl.lexicalized` | particle, expression | {particle} faz parte da expressão fixa {expression} e não tem função própria aqui. | {particle} is part of the fixed expression {expression} and has no function of its own here. |
| `tpl.links-clauses` | particle, left, desc | {particle} liga {left} ao que vem depois, com sentido de {desc}. | {particle} links {left} to what follows, meaning {desc}. |
| `tpl.lists` | particle, chunk, desc | {particle} junta {chunk} ao próximo item da lista: {desc}. | {particle} joins {chunk} to the next item of the list: {desc}. |
| `tpl.marks-chunk` | particle, chunk, desc | {particle} marca {chunk} como {desc}. | {particle} marks {chunk} as {desc}. |
| `tpl.nominalizes` | particle, left, desc | {particle} transforma {left} em substantivo: {desc}. | {particle} turns {left} into a noun: {desc}. |
| `tpl.sentence-final` | particle, desc | {particle} no fim da frase {desc}. | {particle} at the end of the sentence {desc}. |

Rendered examples (they are assertions in the generator):

- `ni.time-point`, chunk 七時 → "に marca 七時 como o momento em que a ação acontece."
- `ka.question` → "か no fim da frase transforma a frase em pergunta."
- `ga.contrast`, left 高いです → "が liga 高いです ao que vem depois, com sentido de contraste ('mas')."
- `madeni.deadline` → "までに funciona como uma unidade só: o prazo máximo ('até', 'no máximo')."

The `desc` strings follow design/translation_style.md: natural pt-BR, no literal mirroring. They are
AI-authored like all Layer-C text, so they go through the `humanizer` pass and teacher review before they
are treated as final.

## 8. Cues and lexicons

A **cue** is a context rule over the C-mode tokens: lemma, POS, inflection and neighbours, with no
free text involved. Example: `next.naru-suru` means the next token's lemma is なる / する / 変わる /
変える, which selects `ni.result`. The lemma sets the cues use are in `cue_lexicons`. A cue is evidence.
It is not the definition of the usage. The research report measures how often cues and labels agree, and
the spot check found cue-only assignments right 21 times out of 25. That is why cue-only rows are
`usage_status: cue-only` until a verifier confirms them.

| cue | definition |
|---|---|
| `aux.causative` | the first predicate of the clause is followed by the auxiliary せる/させる |
| `aux.passive` | the first predicate of the clause is followed by the auxiliary れる/られる |
| `clause-final` | the particle is followed by nothing, a period, or a sentence-final particle |
| `clause.ichiban` | the clause contains 一番 / 最も |
| `clause.negative` | a negation (ない, ぬ, ず, ん, ません) occurs before the next comma or period |
| `next.case-particle` | next token is a particle (が, を, は, に, で ...) |
| `next.comparison` | first predicate of the clause has a lemma in lexicon COMPAR (同じ, 違う, 比べる ...) |
| `next.copula` | next token is だ / です / でしょう / じゃ / な (のだ, んです) |
| `next.emotion` | next token lemma is in lexicon EMO or is すみません / ありがとう / 嬉しい / 残念 |
| `next.issho` | next token lemma is 一緒 or 共 |
| `next.motion-verb` | next token lemma is 行く / 来る / 帰る / 出かける / 戻る |
| `next.nai-aru` | next token (skipping は/も) is ない / ある as adjective, verb or auxiliary |
| `next.naru-suru` | next token lemma is なる / する / 変わる / 変える |
| `next.not-saying-verb` | next predicate is NOT a verb of saying (tells topic って from quotative って) |
| `next.noun` | next token is nominal (名詞, 代名詞, 数詞, 接尾辞, 接頭辞) |
| `next.predicate` | next token is a verb, adjective or na-adjective (the の sits inside a noun-modifying clause) |
| `next.question-mark` | next token is ？ or ? |
| `next.standard-predicate` | first predicate of the clause has a lemma in lexicon STANDARD (近い, いい, 似る ...) |
| `next.start-verb` | first predicate of the clause is 始まる / 開始 / 始める (formal より) |
| `next.stative-predicate` | first predicate of the clause is a stative predicate (好き, 分かる, できる, 欲しい ...) or is followed by たい |
| `next.subsidiary` | next token is a verb/adjective/auxiliary whose lemma is in lexicon SUBSID (いる, おく, しまう, みる, ください ...) |
| `next.temorau` | the first predicate of the clause is followed by て + もらう/いただく |
| `next.use-evaluate` | first predicate of the clause is 使う / 便利 / いい / 必要 / 役立つ |
| `not.clause-final` | the particle is followed by more of the sentence |
| `prev.adjective` | previous token is an i-adjective (形容詞) |
| `prev.adjective-or-noun` | previous token is an i-adjective or a nominal |
| `prev.adverb` | previous token is an adverb (副詞) or a タリ-type 形状詞 |
| `prev.cause-noun` | previous token lemma is in lexicon CAUSE_N (病気, 風邪, 事故 ...) |
| `prev.continuative` | previous token is a verb in the continuative (連用形) inflection |
| `prev.interrogative` | previous token lemma is in lexicon INTERROG (何, 誰, どこ, いつ, and minimizers 一つ, 少し ...) |
| `prev.manner-noun` | previous token lemma is in lexicon MANNER (一人, みんな, 自分 ...) |
| `prev.masen` | the two previous tokens are ませ + ん |
| `prev.means-noun` | previous token lemma is in lexicon MEANS, or is a noun ending in 語 (a language) |
| `prev.na-stem` | previous token is 形状詞 (na-adjective stem), or a noun whose third POS field is 形状詞可能 |
| `prev.noun-next.noun` | previous and next tokens are both nominal |
| `prev.number` | previous token is a numeral (数詞), or a counter suffix right after a numeral |
| `prev.particle` | previous token is itself a particle (には, では, とは, からは ...) |
| `prev.period-next.number` | previous token is a period noun (日, 週, 週間, 月, 年, 時間) and the next token is a numeral |
| `prev.predicate` | previous token is a verb, adjective, na-adjective or auxiliary (the particle closes a clause) |
| `prev.preface-lemma` | one of the two previous tokens has a lemma in lexicon PREFACE (すみません, 失礼, 悪い ...) |
| `prev.sou-desu` | the two previous tokens are そう + です |
| `prev.ta` | previous token is the auxiliary た |
| `prev.te` | previous token is the conjunctive particle て/で |
| `prev.time-noun` | previous token lemma is in lexicon TIME, or is a time counter (時, 分, 日, 月, 年, 曜日) |
| `prev.verb-terminal` | previous token is a verb in terminal/attributive form (the two are homophonous before a 終助詞) |
| `prev.volitional-or-te` | previous token is the volitional う/よう, an imperative, or て/で |
| `sentence.two-ha` | the sentence contains two or more は |
| `sentence.two-mo` | the sentence contains two or more も |
| `verb.departure` | first predicate of the clause has a lemma in lexicon DEPART |
| `verb.emotion-cause` | first predicate of the clause has a lemma in lexicon EMO |
| `verb.existence` | first predicate of the clause has a lemma in lexicon EXIST |
| `verb.giving-telling` | first predicate of the clause has a lemma in lexicon GIVE |
| `verb.make` | first predicate of the clause has a lemma in lexicon MAKE |
| `verb.motion` | first predicate of the clause has a lemma in lexicon MOTION |
| `verb.path` | first predicate of the clause has a lemma in lexicon PATH |
| `verb.receiving` | first predicate of the clause has a lemma in lexicon RECEIVE |
| `verb.reciprocal` | first predicate of the clause has a lemma in lexicon RECIP |
| `verb.saying` | first predicate of the clause has a lemma in lexicon SAYING |
| `verb.target` | first predicate of the clause has a lemma in lexicon TARGET |

## 9. Changing the enum

Adding a usage means adding a row. Nothing about the schema changes (spec §1.6). Steps:

1. Add the row in `particle_functions.json`: id, class, `ja_term`, labels, `desc`, role, level, pattern,
   at least one example, contrasts.
2. If a cue can select it, add the cue definition and any lexicon entries.
3. Re-run the usage derivation and the validator. The validator checks that every
   `particles[].usage` is in the enum, that `function_type == usages[usage].class`, that the token at
   `position` has the particle surface, and that the rendered `explanation` equals the template output.
4. Record the change in this file's changelog.

Retiring a usage works the same way: rename rows to the replacement id first, then drop the row. An id
that is in use is never deleted.

## 10. How exercises use it

The research report (§7) has the detail. In short:

- **Per-usage drills:** "choose the particle" over sentences with `usage = X`. The distractors are the
  particles of `contrasts`, minus anything listed in `interchangeable` (に and へ are both right in 駅に行く
  / 駅へ行く).
- **Same particle, different meaning:** show two sentences with に and ask whether each is a time or a
  destination. This works because the answer key is an enum value, not prose.
- **Role questions:** ask "which part is the destination?" by reading `role` through the particle usage.
  This replaces today's non-committal `ni-phrase` / `de-phrase` / `to-phrase` chunks.
- **Search:** every sentence with `wo.path`, every N5 usage of で, every sentence that contrasts
  `ni.location-existence` and `de.location-action`.

## 11. Sources

See the research report §2. The main references are the TUFS grammar module on 格助詞; NINJAL's
dialect-grammar survey guide chapter 格助詞 (小林隆, 2003), whose seventeen-usage list for に is the backbone
of the `ni.*` rows; 日本語記述文法研究会『現代日本語文法2』(くろしお出版, 2009), as summarised by 日本語教育ナビ;
庵功雄 (2001) on とりたて助詞; and Makino & Tsutsui, *A Dictionary of Basic Japanese Grammar* (The Japan
Times, 1986) for the learner-facing split of meanings.

## Changelog

- 1.0 (2026-09-27): first proposal. 9 classes, 123 usages, 9 templates, 59 cues.
