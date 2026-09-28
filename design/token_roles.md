# Token roles: enumerable word-by-word explanation items

**Status:** proposal, 2026-09-27. **Data + schema:** [`token_roles.json`](token_roles.json)
(JSON Schema 2020-12; the file validates against itself). **Companion:**
[`particle_functions.md`](particle_functions.md). The measurements are in
[`research/reports/particle_taxonomy_research.md`](../research/reports/particle_taxonomy_research.md) §6.

## 1. Why

Every C-mode token in `corpus/sentences/bank.json` has a `role` locale object, written as free text:
"núcleo do tópico citado", "verbo principal", "auxiliar de tempo passado". Across the 52,031 content
tokens of the 2026-09-27 bank:

- 24,363 (46.8%) have **no role at all**;
- the remaining 27,668 use **7,496 distinct English strings**, and 5,415 of them occur once.

The strings are nearly all a combination of two things: what the token does inside its chunk (head,
modifier, auxiliary ...) and what the chunk does in the clause (topic, object, destination ...). Both
can be enumerated, and most of both can be derived from data the corpus already has. This file defines
the two enums and the templates that turn them back into text.

## 2. The model

For each C-mode token (`$defs.token_item`):

| field | enum | derived from |
|---|---|---|
| `function` | `token_function` (§4) | `pos`, position in the chunk, lemma |
| `aux_function` | `aux_function` (§5), auxiliaries only | lemma (10,017 of the bank's 10,205 auxiliaries, 98.2%, by lemma alone) |
| `chunk` | index into `pattern[]` | the existing chunker (`scripts/export/build_sentence_patterns.py`) |
| `chunk_role` | `chunk_role` (§3) | the particle **usage** that closes the chunk (particle_functions.json `role`); the trailing verbal run → `predicate`; adverb-only chunk → `adverbial` |
| `form` | reuses `conjugation_form` from design/unlock_enums.json | the predicate run's inflection (the conjugation tables already compute it) |
| `role` | rendered text | template (§6) over `function` + `chunk_role` |
| `gloss` | stays Layer-B text | a meaning in context cannot be an enum |
| `note` | optional free text | author |

Inflection is not redefined. Tokens keep `inflection` / `inflection_type` (UniDic 活用形, already neutral
enums), and a predicate's form is a `conjugation_form` id, so exercises and the conjugation bank use the
same ids.

**Particle tokens** take `function: particle` and are explained only through `particles[]` and
particle_functions.json. Today 2 of the 24,771 particle tokens carry a token `role`. That is correct and
stays that way.

## 3. Chunk roles

| id | 日本語 term | en | pt-BR | genitive (pt-BR) | set by |
|---|---|---|---|---|---|
| `topic` | 主題 | topic | tópico | do tópico | `ha.topic`, `ha.contrast`, `tte.topic`, `nitsuite.about` |
| `subject` | 主語（ガ格） | subject | sujeito | do sujeito | `ga.subject`, `no.subject-in-modifier` |
| `stative-object` | 対象（状態述語） | object of a state predicate | objeto de predicado de estado | do objeto do estado | `ga.stative-object` |
| `object` | 目的語（ヲ格） | direct object | objeto direto | do objeto direto | `wo.object` |
| `recipient` | 相手 | recipient | destinatário | do destinatário | `ni.recipient` |
| `source` | 起点・出どころ | source / starting point | origem / ponto de partida | da origem | `wo.departure`, `ni.source`, `kara.starting-point`, `kara.source`, `yori.starting-point` |
| `goal` | 到達点・方向 | destination / direction | destino / direção | do destino | `ni.goal`, `he.direction` |
| `path` | 経過域 | route | percurso | do percurso | `wo.path` |
| `location` | 存在の場所 | location of existence | lugar onde algo está | do lugar | `ni.location-existence` |
| `location-action` | 動作の場所 | place of the action | lugar da ação | do lugar da ação | `de.location-action` |
| `time` | 時 | time | tempo | da expressão de tempo | `ni.time-point`, `madeni.deadline` |
| `end-point` | 終点・限界 | end point (until / as far as) | limite (até) | do limite | `made.until`, `made.as-far-as` |
| `purpose` | 目的 | purpose | finalidade | da finalidade | `ni.purpose`, `noni.purpose` |
| `result` | 変化の結果 | result of a change | resultado da mudança | do resultado | `ni.result`, `to.result` |
| `agent` | 動作主 | agent (passive, 〜てもらう) | agente (passiva, 〜てもらう) | do agente | `ni.agent` |
| `causee` | 使役の相手 | causee | quem é levado a agir | de quem é levado a agir | `wo.causee`, `ni.causee` |
| `comitative` | 共同者 | companion | companhia | da companhia | `to.comitative` |
| `means` | 手段・道具 | means / instrument | meio / instrumento | do meio | `de.means` |
| `material` | 材料・原料 | material | material | do material | `de.material`, `kara.material` |
| `cause` | 原因・理由 | cause | causa | da causa | `ni.cause`, `de.cause` |
| `scope` | 範囲 | scope | âmbito | do âmbito | `de.scope` |
| `manner` | 様態 | manner | modo | do modo | `de.manner` |
| `quantity` | 数量・割合・限度 | quantity / rate / limit | quantidade / proporção / limite | da quantidade | `ni.frequency`, `de.limit`, `kurai.approximation`, `zutsu.distributive` |
| `standard` | 基準 | standard of comparison or judgment | referência (comparação ou avaliação) | da referência | `ni.standard`, `to.comparison`, `yori.comparison`, `hodo.degree` |
| `target` | 対象（心的態度・働きかけ） | target of an attitude or action | alvo | do alvo | `ni.target` |
| `quote` | 引用・内容 | quoted content | conteúdo citado | da citação | `to.quotative`, `tte.quotative`, `ka.embedded-question` |
| `focus` | とりたて | focused element (also, only, even) | elemento destacado (também, só, até) | do elemento destacado | `made.even`, `mo.also`, `mo.both`, `mo.total-negation`, `mo.emphasis-quantity`, `koso.emphasis` … |
| `parallel-item` | 並立項 | list item | item de lista | do item da lista | `ni.parallel`, `to.parallel`, `ya.partial-list`, `ka.alternative`, `yara.listing` |
| `modifier` | 連体修飾 | noun modifier | modificador do substantivo | do modificador | `no.noun-modifier`, `ka.indefinite`, `toiu.naming` |
| `nominalized-clause` | 名詞節 | nominalized clause | oração substantivada | da oração substantivada | `no.nominalizer`, `no.pronoun` |
| `adverbial` | 連用修飾（副詞的成分） | adverbial (modifies the predicate) | adjunto adverbial | do adjunto adverbial | `ni.adverbial`, `to.adverbial` |
| `predicate` | 述語 | predicate | predicado | do predicado | `de.copula`, `no.explanatory`, `bakari.just-done`, `te.subsidiary`, `te.request` + the trailing verbal run |
| `clause-link` | 接続 | clause link (and, but, because, if) | ligação entre orações | da oração ligada | `ga.contrast`, `ga.preface`, `to.conditional`, `kara.after`, `kara.reason`, `mo.concessive` … |
| `connective` | 接続詞 | sentence connective (それで, でも) | conectivo de frase | do conectivo | pos = conjunction |
| `interjection` | 感動詞・応答 | interjection / response | interjeição / resposta | da interjeição | pos = interjection |
| `sentence-final` | 文末 | sentence-final element | final da frase | do final da frase | `no.final-question`, `no.final-explanation`, `ka.question`, `ka.invitation`, `ka.acknowledgment`, `kana.wondering` … |
| `none` | — | no role of its own (part of a fixed expression) | sem papel próprio (parte de expressão fixa) |  | `lex.fixed` |

`legacy_pattern_role` in the JSON maps today's `pattern[].role` values onto this enum. `phrase`,
`ni-phrase`, `de-phrase` and `to-phrase` map to `null`. They are the non-committal roles
build_sentence_patterns.py falls back to because the corpus has no usage-level data (5,538 of 17,333
chunks, 32.0%). With a particle usage on the closing particle they resolve to a specific role (`time`,
`goal`, `means`, `comitative` ...). A `phrase` chunk that no role-bearing particle closes still needs
the adverb split described in that script's KNOWN LIMITATION before it can get `adverbial`.

## 4. Token functions

| id | rule | en | pt-BR | template |
|---|---|---|---|---|
| `head` | last nominal token of a chunk, before the particle that closes it | head | núcleo | `tpl.role.of` |
| `noun-modifier` | nominal token before the head inside the same chunk (compound or の-less modifier) | modifier | modificador | `tpl.role.of` |
| `determiner` | pos = adnominal (連体詞: この, その, あの, 大きな) | determiner | determinante | `tpl.role.of` |
| `adnominal-predicate` | verb/adjective/auxiliary run directly before a nominal (高い山, 読んだ本) | noun-modifying predicate | predicado que modifica o substantivo | `tpl.role.of` |
| `adverb` | pos = adverb | adverb | advérbio | `tpl.role.self` |
| `predicate-head` | first verb/adjective/na-adjective/noun of the sentence-final predicate run | main predicate | predicado principal | `tpl.role.self` |
| `subsidiary-verb` | verb after the conjunctive て/で whose lemma is in lexicon SUBSID (〜ている, 〜てください) | subsidiary verb | verbo auxiliar (depois de 〜て) | `tpl.role.self` |
| `auxiliary` | pos = auxiliary; sub-function from AUX_FUNCTION by lemma | auxiliary | auxiliar | `tpl.role.aux` |
| `particle` | pos = particle; described by design/particle_functions.json, never by this file | particle | partícula | `particle` |
| `prefix` | pos = prefix (お, ご: politeness) | prefix | prefixo | `tpl.role.self` |
| `suffix` | pos = suffix (さん, たち, counters) | suffix | sufixo | `tpl.role.self` |
| `numeral` | pos_fine = 数詞 | numeral | numeral | `tpl.role.of` |
| `conjunction` | pos = conjunction | conjunction | conjunção | `tpl.role.self` |
| `interjection` | pos = interjection | interjection | interjeição | `tpl.role.self` |
| `punctuation` | pos = punctuation / whitespace (never explained) | punctuation | pontuação | `none` |

## 5. Auxiliary functions

| id | lemmas | en | pt-BR | level |
|---|---|---|---|---|
| `politeness` | ます | politeness | cortesia (〜ます) | N5 |
| `copula` | だ や じゃ なり | copula | cópula (だ) | N5 |
| `copula-polite` | です | polite copula | cópula educada (です) | N5 |
| `negation` | ない ぬ ん ず | negation | negação | N5 |
| `past` | た き けり | past / completion | passado / conclusão | N5 |
| `desire` | たい たがる | desire | desejo (〜たい) | N5 |
| `passive-potential` | れる られる る らる | passive / potential / honorific | passiva / potencial / honorífico | N4 |
| `causative` | せる させる しめる | causative | causativo | N4 |
| `volitional` | う よう む | volitional | volitivo (vamos …) | N4 |
| `evidential` | そう らしい ようだ みたい | evidential / hearsay / resemblance | evidência / boato / aparência | N4 |
| `obligation` | べし | obligation (べき) | obrigação (べき) | N3 |
| `negative-volitional` | まい | negative volitional | volitivo negativo (まい) | N2 |
| `perfective` | り | classical perfective | perfectivo clássico | N1 |
| `comparison` | ごとし | likeness (ごとし) | semelhança (ごとし) | N1 |

Lemmas not in the table (1.8% of the bank's auxiliaries, mostly classical forms in N1/N2 sentences) fall
back to `function: auxiliary` without `aux_function` and keep their authored role text until someone
rules on them.

## 6. Rendering the role text

| template | pt-BR | en | used for |
|---|---|---|---|
| `tpl.role.of` | `{function} {role_of}` | `{function} {role_of}` | chunk members: "núcleo do sujeito", "modificador do objeto direto" |
| `tpl.role.self` | `{function}` | `{function}` | tokens whose function is the whole story: "advérbio", "predicado principal" |
| `tpl.role.aux` | `auxiliar de {aux_function}` | `{aux_function} auxiliary` | "auxiliar de negação" |
| `tpl.role.predicate-in` | `{function} {role_of}` | `{function} {role_of}` | predicate of an embedded clause: "predicado da oração substantivada" |

`role_of` is `chunk_roles[].of`, which carries the pt-BR contraction ("do sujeito", "da causa"), so the
template never has to work out gender or contraction.

Example, 私は七時に起きます:

| token | function | chunk_role | rendered role (pt-BR) |
|---|---|---|---|
| 私 | head | topic | núcleo do tópico |
| は | particle | — | (particles[]: `ha.topic`) |
| 七 | numeral | time | numeral da expressão de tempo |
| 時 | head | time | núcleo da expressão de tempo |
| に | particle | — | (particles[]: `ni.time-point`) |
| 起き | predicate-head | predicate | predicado principal |
| ます | auxiliary / politeness | predicate | auxiliar de cortesia (〜ます) |

## 7. What stays free text

- `gloss`: the in-context meaning. It stays Layer-B text checked against the dictionary (spec §7).
- `note`: an optional addition for anything the templates cannot express. A note never replaces the
  rendered role or explanation. It is appended after it, so a reviewer can trust the enum part without
  reading the prose (spec §1.3).

## Changelog

- 1.0 (2026-09-27): first proposal. 37 chunk roles, 15 token functions, 14 auxiliary functions.
