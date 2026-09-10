# W13b - the 101 uncovered N3 targets: re-check first, generate only what is left

Every target left uncovered by W13 (`research/derived/n3_mined/residue.json` :: `uncovered_targets`)
was re-checked against real Tatoeba text **before** anything was generated, because the W13 miner
resolved each token through the Dissector's vocab-form map (first-writer-wins), which silently hands a
shared surface to one record only. The re-check widened that: a token counts for the target when its
surface **or** its lemma is one of the record's registry surfaces, the token's own reading agrees with
the record's kana, and the token's SudachiPy POS is compatible with the record's JMdict POS. Pool:
219,990 sentences of 6-40 characters that carry a directly linked English pair and are not already
banked, mined or generated.

Output: [`research/derived/n3_mined/generated_uncovered.json`](../derived/n3_mined/generated_uncovered.json)
(101 rows, one per target). Nothing was written to `db/corpus.sqlite`; the search ran on a scratch copy.

## Counts

| | |
|---|---|
| uncovered targets carried in | 101 (97 vocab, 4 grammar) |
| **selected** (a real Tatoeba sentence did exist) | **36** (34 vocab, 2 grammar) |
| **generated** (no real candidate survives) | **65** (63 vocab, 2 grammar) |
| still uncovered after this run | 0 |
| generated rows at `unknown_count` 0 | 65 / 65 |
| generated rows carrying a kanji outside the lesson set (target's own kanji excluded) | 0 / 65 |
| generated sentence length | 6-17 characters |
| selected rows at 0 / 1 unknown content token | 29 / 7 |
| register | neutral 55, casual 25, polite 19, formal 2 |

Every row is `needs_review: true`. The 36 selected rows keep Layer-A `jp`/`en` byte-exact from
`raw_tatoeba_sentence` / `raw_tatoeba_translation` and are `ai_generated: false` (only `pt`,
`pt_literal` and `register` are authored here). The 65 generated rows are `ai_generated: true`,
`tatoeba_id: ""`, keyed `gen-<sha1(jp)[:12]>`, with the trailing 。 dropped per
`design/translation_style.md`.

## Why 36 targets turned out to have a real sentence after all

The miner's form map, not the pool, was the blocker. Three recoveries dominate:

1. **A shared surface already owned by another record.** 案, 息, 詩, 谷, 陸, 表, 左右, 身体, 文明, 発表,
   消費, 前進, 不平 all sit under a form the map had assigned elsewhere.
2. **A suffix or prefix that only ever appears bound.** 後(ご) in ３日後, 上(じょう) in 地図上, 数(すう) in
   数分, 級 in ４級, 全 in 全学生, 御 in 御返事, 不 in 不得手 are real SudachiPy tokens once the reading is
   checked instead of the map.
3. **Reading disambiguation the map could not do.** 方 as ほう (赤の方が好き) versus かた (次の方), 金 as きん
   (金の時計) versus かね, 他 as た.

Three targets the loose search *appeared* to cover were rejected on sense and generated instead:
**位** (all 8 pool rows use it as くらい 'about', never the record's rank/digit), **市** (the numeral いち
inside いちど) and **灯** (the kana ひ of おひさま / ひま).

## The cks proof, per row

`u` is the number of content tokens (SudachiPy full dict, SplitMode.C; particles, auxiliaries and
numerals excluded) that do **not** resolve to a vocab slug inside the introducing lesson's
`cumulative_known_set`. The target's own character span is masked first, because the target is a
lexical unit and not always one token: いけない cuts to いけ+ない, とんでもない to とんでも+ない, 要するに to
要する+に, and scoring those fragments against the map produces a false unknown. The per-token verdict
for every generated row is stored in the artifact under `cks_proof.content_tokens`.

| target | word / pattern | mode | lesson | len | u | sentence |
|---|---|---|---|---|---|---|
| `vocab:1420020` | 男の人 | generated | `causa-01` | 10 | 0 | あの男の人は先生です |
| `vocab:1309460` | 思わず | generated | `causa-02` | 10 | 0 | 思わず大きな声が出た |
| `vocab:1008430` | ですから | generated | `causa-06` | 13 | 0 | ですから、早く行きましょう |
| `vocab:1004890` | こんなに | generated | `concessao-01` | 12 | 0 | こんなに寒い日は初めてだ |
| `vocab:1005390` | ざっと | generated | `concessao-03` | 10 | 0 | ざっと百人ぐらい来た |
| `vocab:1007370` | だけど | generated | `concessao-05` | 11 | 0 | だけど、まだ間に合うよ |
| `vocab:2643970` | だって | generated | `concessao-05` | 11 | 0 | だって、お金がないんだ |
| `vocab:1320810` | 実 | generated | `concessao-07` | 11 | 0 | この木は秋に実をつける |
| `vocab:1000730` | 行けない | generated | `conectores-04` | 14 | 0 | そんなことを言ってはいけない |
| `vocab:1578790` | 行き | generated | `conectores-04` | 11 | 0 | 駅行きのバスに乗ります |
| `vocab:1155400` | 位 | generated | `conectores-05` | 13 | 0 | あの人は会社で高い位にいる |
| `vocab:1245280` | 空 | generated | `conectores-05` | 10 | 0 | かばんの中は空だった |
| `vocab:1308080` | 市 | generated | `conectores-05` | 8 | 0 | 日曜日に市が立つ |
| `vocab:1352150` | 上 | generated | `conectores-05` | 11 | 0 | 川の上から下まで歩いた |
| `vocab:1582290` | 灯 | generated | `conectores-07` | 11 | 0 | 町の灯がきれいに見える |
| `vocab:1320830` | 実は | generated | `conjectura-01` | 11 | 0 | 実は、まだ話していない |
| `vocab:2820720` | 実に | generated | `conjectura-01` | 9 | 0 | 実におもしろい話だ |
| `vocab:1005480` | 頻りに | generated | `conjectura-03` | 11 | 0 | しきりに時計を見ている |
| `vocab:1005600` | 仕舞った | generated | `conjectura-03` | 10 | 0 | しまった、時間がない |
| `vocab:1430690` | 直に | generated | `conjectura-03` | 8 | 0 | 先生に直に話した |
| `vocab:1211340` | 堪らない | generated | `conjectura-05` | 8 | 0 | 暑くてたまらない |
| `vocab:1612000` | 滅多に | generated | `conjectura-07` | 9 | 0 | めったに来ない人だ |
| `vocab:1252050` | 計 | generated | `desejos-02` | 8 | 0 | 計五人が来ました |
| `vocab:1006930` | その内 | generated | `desejos-05` | 8 | 0 | そのうち分かるよ |
| `vocab:1007010` | 其れとも | generated | `desejos-05` | 12 | 0 | 行く？それとも行かない？ |
| `vocab:1406060` | 其れでも | generated | `desejos-05` | 10 | 0 | それでも私は行きたい |
| `vocab:1406090` | 其処で | generated | `desejos-05` | 12 | 0 | そこで、私は考えを変えた |
| `vocab:1008790` | とんでも無い | generated | `desejos-06` | 17 | 0 | とんでもない、私は何もしていません |
| `vocab:1009340` | どんなに | generated | `desejos-06` | 13 | 0 | どんなに待っても来なかった |
| `vocab:1584105` | 方々 | generated | `desejos-07` | 10 | 0 | 方々に花がさいている |
| `vocab:1221740` | 気に入る | generated | `deveres-01` | 11 | 0 | この服が気に入りました |
| `vocab:2269050` | 急に | generated | `deveres-02` | 9 | 0 | 急に人が多くなった |
| `vocab:1234260` | 共に | generated | `deveres-05` | 10 | 0 | みんなと共に働きたい |
| `vocab:1509480` | 別に | generated | `deveres-06` | 9 | 0 | 別に、何でもないよ |
| `vocab:1004830` | これ等 | generated | `enfase-04` | 11 | 0 | これらの本は全部読んだ |
| `vocab:2055530` | だが | generated | `enfase-05` | 12 | 0 | だが、それは本当ではない |
| `vocab:1487410` | 必ずしも | generated | `estado-04` | 16 | 0 | 高い物が必ずしもいいものではない |
| `vocab:1466950` | 如何しても | generated | `estado-06` | 12 | 0 | どうしても行きたいんです |
| `vocab:1538100` | 約 | generated | `estrutura-06` | 11 | 0 | 駅まで約十分かかります |
| `vocab:1002970` | かも知れない | generated | `intencao-01` | 10 | 0 | 明日は雨かもしれない |
| `vocab:1008570` | 所が | generated | `intencao-06` | 13 | 0 | ところが、だれもいなかった |
| `vocab:1189000` | 何処か | generated | `intencao-06` | 10 | 0 | どこかで会いましたか |
| `vocab:1343110` | 所で | generated | `intencao-06` | 13 | 0 | ところで、仕事はどうですか |
| `gram:n3-donna-ni-koto-ka` | n3-donna-ni-koto-ka | generated | `limites-04` | 13 | 0 | どんなに会いたかったことか |
| `vocab:1009410` | 何故なら | generated | `limites-06` | 13 | 0 | なぜなら、時間がないからだ |
| `vocab:1188270` | 何か | generated | `limites-06` | 11 | 0 | 何か飲み物はありますか |
| `vocab:1188420` | 何とか | generated | `limites-06` | 10 | 0 | 何とか間に合いました |
| `vocab:1188490` | 何も | generated | `limites-06` | 10 | 0 | 今日は何もしたくない |
| `vocab:1611020` | 何で | generated | `limites-06` | 10 | 0 | なんで来なかったの？ |
| `vocab:1611030` | 何でも | generated | `limites-06` | 12 | 0 | なんでも好きな物を選んで |
| `vocab:1348900` | 少しも | generated | `perspectiva-04` | 7 | 0 | 少しも寒くない |
| `vocab:2648780` | 品 | generated | `perspectiva-06` | 9 | 0 | この店には品が多い |
| `vocab:1547710` | 来 | generated | `perspectiva-07` | 9 | 0 | 来年の春に国へ帰る |
| `gram:n3-you-ni-iu` | n3-you-ni-iu | generated | `relato-02` | 11 | 0 | 弟に早く帰るように言う |
| `vocab:1610740` | 違いない | generated | `relato-05` | 12 | 0 | 彼は知っているに違いない |
| `vocab:1612050` | 若しも | generated | `relato-07` | 13 | 0 | もしも雨だったらどうする？ |
| `vocab:1288940` | 今に | generated | `tempo-01` | 6 | 0 | 今に分かるよ |
| `vocab:1288950` | 今にも | generated | `tempo-01` | 8 | 0 | 今にも電車が来る |
| `vocab:1609210` | 一度に | generated | `tempo-02` | 12 | 0 | 一度にたくさん食べないで |
| `vocab:1188880` | 何時までも | generated | `tempo-04` | 11 | 0 | いつまでも元気でいてね |
| `vocab:1410800` | 頂きます | generated | `tempo-04` | 9 | 0 | では、いただきます |
| `vocab:1577130` | 何時でも | generated | `tempo-04` | 9 | 0 | いつでも来ていいよ |
| `vocab:1355970` | 常に | generated | `tempo-06` | 9 | 0 | あの人は常に元気だ |
| `vocab:1207510` | 額 | generated | `tempo-07` | 9 | 0 | 額に手を当ててみた |
| `vocab:1546620` | 要するに | generated | `tempo-08` | 12 | 0 | 要するに、時間がないんだ |
| `vocab:1922780` | 不 | selected | `causa-07` | 13 | 1 | 誰にでも得手不得手がある。 |
| `vocab:1290810` | 左右 | selected | `concessao-04` | 8 | 0 | 彼は左右を見た。 |
| `vocab:1150450` | 愛する | selected | `conectores-01` | 8 | 0 | 親は子を愛する。 |
| `vocab:1154770` | 案 | selected | `conectores-01` | 9 | 0 | いい案があるかも。 |
| `vocab:1404320` | 息 | selected | `conectores-03` | 7 | 0 | 口で息をして。 |
| `gram:n3-nado` | n3-nado | selected | `conectores-04` | 19 | 0 | レストランで働いたことなど一度もない。 |
| `vocab:1242600` | 金 | selected | `conectores-05` | 17 | 1 | 彼は報酬として金の時計をもらった。 |
| `vocab:1454500` | 得る | selected | `conectores-05` | 13 | 0 | あり得るけど、多分ないな。 |
| `vocab:1508300` | 柄 | selected | `conectores-05` | 12 | 0 | 柄にもないことを言うな。 |
| `vocab:2147630` | 後 | selected | `conectores-05` | 11 | 0 | ３日後に来てください。 |
| `vocab:2826528` | 御 | selected | `conectores-05` | 14 | 0 | 御返事を御待ちしております。 |
| `vocab:2859161` | 音 | selected | `conectores-05` | 24 | 1 | 自分のパソコンから警告音が鳴ってるの、聞こえた？ |
| `gram:n3-moshikasuru-to-kamoshirenai` | n3-moshikasuru-to-kamoshirenai | selected | `conjectura-01` | 19 | 1 | もしかすると明日雨が降るかもしれない。 |
| `vocab:1929950` | 詩 | selected | `conjectura-01` | 8 | 0 | この詩、いいね。 |
| `vocab:1581590` | 谷 | selected | `conjectura-05` | 12 | 0 | 谷の間を川が流れている。 |
| `vocab:1531950` | 命じる | selected | `conjectura-07` | 8 | 1 | 回れ右を命じる。 |
| `vocab:1514950` | 暮れ | selected | `desejos-01` | 8 | 1 | 薄暮れが迫った。 |
| `vocab:1919590` | 級 | selected | `deveres-03` | 18 | 0 | ４級の漢字をどれだけ覚えていますか。 |
| `vocab:1393350` | 前進 | selected | `deveres-04` | 11 | 0 | 彼らは川まで前進した。 |
| `vocab:1516930` | 方 | selected | `deveres-06` | 7 | 0 | 赤の方が好き。 |
| `vocab:2083100` | 日 | selected | `enfase-06` | 8 | 0 | 一日が終わった。 |
| `vocab:1129240` | ママ | selected | `enfase-07` | 6 | 0 | ママはどこ？ |
| `vocab:1494790` | 不平 | selected | `estado-07` | 13 | 0 | 不平を言う理由は何も無い。 |
| `vocab:1533340` | 綿 | selected | `estado-08` | 25 | 1 | あのシャツを着てみなさい。上質の綿でできています。 |
| `vocab:1350290` | 消費 | selected | `estrutura-01` | 25 | 0 | 収入が増えれば増えるほど、消費もいっそう多くなる。 |
| `vocab:1477840` | 発表 | selected | `estrutura-05` | 11 | 0 | ２人は婚約を発表した。 |
| `vocab:1394250` | 善 | selected | `intencao-05` | 16 | 0 | 美しいものは必ずしも善ではない。 |
| `vocab:1394770` | 全 | selected | `intencao-05` | 20 | 0 | 全学生はみんな図書館に入ることができる。 |
| `vocab:1505650` | 文明 | selected | `intencao-07` | 12 | 0 | 文明の進歩がとても速い。 |
| `vocab:1949190` | 他 | selected | `limites-05` | 11 | 0 | 私は他に何もできない。 |
| `vocab:1643510` | 老い | selected | `perspectiva-03` | 13 | 0 | 老いも若きも戦争にいった。 |
| `vocab:1580825` | 数 | selected | `perspectiva-04` | 9 | 0 | 数分はかかります。 |
| `vocab:1489350` | 表 | selected | `perspectiva-06` | 19 | 0 | この点を見るために、下の表を見なさい。 |
| `vocab:1550980` | 陸 | selected | `perspectiva-07` | 8 | 0 | 陸が見えてきた。 |
| `vocab:1352170` | 上 | selected | `tempo-05` | 17 | 0 | この地図上では僕はどこにいますか？ |
| `vocab:2830705` | 身体 | selected | `tempo-05` | 7 | 0 | 身体は洗った？ |

All 65 generated rows sit at `u = 0`. The 7 selected rows at `u = 1` spend the single i+1 slot the
selection rule allows: 金 (報酬), 音 (警告), 不 (得手), 綿 (上質), 暮れ (迫る), n3-moshikasuru-to-kamoshirenai (しれる), 命じる (回れ右).

## 20 sample rows

**`vocab:1006930` - その内** &middot; generated &middot; `les:n3-desejos-05` &middot; casual &middot; `gen-ac706d716c7e`

- jp: そのうち分かるよ
- en: You'll find out before long.
- pt: Uma hora você descobre.
- pt_literal: Dentro em breve (そのうち), entende (よ ênfase informativa).
- cks proof, unknown = 0: **その** (target), **うち** (target), 分かる -> `vocab:1606560`

**`vocab:1008790` - とんでも無い** &middot; generated &middot; `les:n3-desejos-06` &middot; polite &middot; `gen-3cffd9cadbe7`

- jp: とんでもない、私は何もしていません
- en: Not at all, I haven't done anything.
- pt: Imagina, eu não fiz nada.
- pt_literal: De jeito nenhum (とんでもない, aqui como resposta), quanto a mim (は tópico), nada (何も) não estou fazendo.
- cks proof, unknown = 0: **とんでも** (target), **ない** (target), 私 -> `vocab:1311110`, 何 -> `vocab:1577100`, し -> `vocab:1298670`, い -> `vocab:1577980`

**`vocab:1188420` - 何とか** &middot; generated &middot; `les:n3-limites-06` &middot; polite &middot; `gen-c1dc4ac04cc7`

- jp: 何とか間に合いました
- en: I made it in time somehow.
- pt: Deu para chegar a tempo, de algum jeito.
- pt_literal: De um jeito ou de outro (何とか), consegui chegar na hora (間に合う).
- cks proof, unknown = 0: **何** (target), **と** (target), **か** (target), 間に合い -> `vocab:1215260`

**`vocab:1430690` - 直に** &middot; generated &middot; `les:n3-conjectura-03` &middot; neutral &middot; `gen-09a4a8300a89`

- jp: 先生に直に話した
- en: I spoke to the teacher in person.
- pt: Eu falei diretamente com o professor.
- pt_literal: Ao professor (に destino), pessoalmente (直に), falei.
- cks proof, unknown = 0: 先生 -> `vocab:1387990`, **直** (target), **に** (target), 話し -> `vocab:1562350`

**`vocab:1610740` - 違いない** &middot; generated &middot; `les:n3-relato-05` &middot; neutral &middot; `gen-3beb5841ff28`

- jp: 彼は知っているに違いない
- en: He must know.
- pt: Ele com certeza sabe.
- pt_literal: Quanto a ele (は tópico), está sabendo, não há como ser diferente (に違いない certeza).
- cks proof, unknown = 0: 彼 -> `vocab:1000580`, 知っ -> `vocab:1420470`, いる -> `vocab:1577980`, **違い** (target), **ない** (target)

**`vocab:1007370` - だけど** &middot; generated &middot; `les:n3-concessao-05` &middot; casual &middot; `gen-178322709097`

- jp: だけど、まだ間に合うよ
- en: But there's still time.
- pt: Mas ainda dá tempo.
- pt_literal: Só que (だけど), ainda (まだ) dá para chegar na hora (よ ênfase).
- cks proof, unknown = 0: **だ** (target), **けど** (target), まだ -> `vocab:1527110`, 間に合う -> `vocab:1215260`

**`vocab:1320830` - 実は** &middot; generated &middot; `les:n3-conjectura-01` &middot; neutral &middot; `gen-c7134fba488c`

- jp: 実は、まだ話していない
- en: Actually, I haven't told them yet.
- pt: Na verdade, eu ainda não contei.
- pt_literal: A verdade é que (実は), ainda (まだ) não estou tendo falado.
- cks proof, unknown = 0: **実** (target), **は** (target), まだ -> `vocab:1527110`, 話し -> `vocab:1562350`, い -> `vocab:1577980`

**`vocab:1005480` - 頻りに** &middot; generated &middot; `les:n3-conjectura-03` &middot; neutral &middot; `gen-95ea64271abc`

- jp: しきりに時計を見ている
- en: He keeps looking at the clock.
- pt: Ele fica olhando o relógio sem parar.
- pt_literal: Insistentemente (しきりに), o relógio (を objeto direto) está olhando.
- cks proof, unknown = 0: **しきり** (target), **に** (target), 時計 -> `vocab:1316140`, 見 -> `vocab:1259290`, いる -> `vocab:1577980`

**`vocab:1410800` - 頂きます** &middot; generated &middot; `les:n3-tempo-04` &middot; polite &middot; `gen-baf1ae13c6ee`

- jp: では、いただきます
- en: Well then, thank you for the meal.
- pt: Então tá, bom apetite.
- pt_literal: Sendo assim (では), recebo humildemente (いただきます, fórmula dita antes de comer).
- cks proof, unknown = 0: **いただき** (target), **ます** (target)

**`vocab:1009410` - 何故なら** &middot; generated &middot; `les:n3-limites-06` &middot; neutral &middot; `gen-6238f7249749`

- jp: なぜなら、時間がないからだ
- en: That's because there is no time.
- pt: Isso porque não tem tempo.
- pt_literal: Isso porque (なぜなら, abre a razão), tempo (が sujeito) não existe, é por isso (からだ fecha a razão).
- cks proof, unknown = 0: **なぜ** (target), **なら** (target), 時間 -> `vocab:1315920`, ない -> `vocab:1529520`

**`vocab:1207510` - 額** &middot; generated &middot; `les:n3-tempo-07` &middot; neutral &middot; `gen-9954c1fa54ce`

- jp: 額に手を当ててみた
- en: I tried putting my hand on my forehead.
- pt: Eu experimentei pôr a mão na testa.
- pt_literal: Na testa (額 + に ponto de contato), a mão (を objeto direto) encostei e vi (てみる tentativa).
- cks proof, unknown = 0: **額** (target), 手 -> `vocab:1327190`, 当て -> `vocab:1448860`, み -> `vocab:1259290`

**`vocab:1188270` - 何か** &middot; generated &middot; `les:n3-limites-06` &middot; polite &middot; `gen-de2b7516143c`

- jp: 何か飲み物はありますか
- en: Is there something to drink?
- pt: Tem alguma coisa para beber?
- pt_literal: Alguma coisa (何か), quanto a bebida (は tópico), existe?
- cks proof, unknown = 0: **何** (target), **か** (target), 飲み物 -> `vocab:1600430`, あり -> `vocab:1296400`

**`vocab:1609210` - 一度に** &middot; generated &middot; `les:n3-tempo-02` &middot; casual &middot; `gen-9ede389506d7`

- jp: 一度にたくさん食べないで
- en: Don't eat a lot all at once.
- pt: Não come tudo de uma vez só.
- pt_literal: De uma só vez (一度に), muito (たくさん) não coma (ないで pedido negativo brando).
- cks proof, unknown = 0: **一度** (target), **に** (target), たくさん -> `vocab:1415870`, 食べ -> `vocab:1358280`

**`gram:n3-you-ni-iu` - n3-you-ni-iu** &middot; generated &middot; `les:n3-relato-02` &middot; neutral &middot; `gen-700a574fb45f`

- jp: 弟に早く帰るように言う
- en: I tell my younger brother to come home early.
- pt: Eu mando meu irmão mais novo voltar cedo para casa.
- pt_literal: Ao irmão mais novo (に pessoa a quem se fala), voltar cedo, nesse sentido (ように) digo.
- cks proof, unknown = 0: 弟 -> `vocab:1581930`, 早く -> `vocab:1404975`, 帰る -> `vocab:1221270`, **よう** (target), **に** (target), **言う** (target)

**`vocab:2830705` - 身体** &middot; selected &middot; `les:n3-tempo-05` &middot; casual &middot; tatoeba 12439920

- jp: 身体は洗った？
- en: Did you wash yourself?
- pt: Você lavou o corpo?
- pt_literal: Quanto ao corpo (は tópico), lavou?
- Layer-A match: 身体 / しんたい / 名詞/普通名詞

**`vocab:2826528` - 御** &middot; selected &middot; `les:n3-conectores-05` &middot; polite &middot; tatoeba 174243

- jp: 御返事を御待ちしております。
- en: I'm looking forward to your reply.
- pt: Fico no aguardo da sua resposta.
- pt_literal: A sua resposta (御 prefixo honorífico + を objeto direto), estou esperando (お + radical + しております, humilde e polido).
- Layer-A match: 御 / お / 接頭辞/*

**`vocab:1242600` - 金** &middot; selected &middot; `les:n3-conectores-05` &middot; neutral &middot; tatoeba 100054

- jp: 彼は報酬として金の時計をもらった。
- en: He was given a gold watch as a reward.
- pt: Ele ganhou um relógio de ouro como recompensa.
- pt_literal: Quanto a ele (は tópico), como recompensa (として papel/função), um relógio de ouro (の modificador + を objeto direto) recebeu.
- Layer-A match: 金 / きん / 名詞/普通名詞

**`vocab:1580825` - 数** &middot; selected &middot; `les:n3-perspectiva-04` &middot; polite &middot; tatoeba 11530592

- jp: 数分はかかります。
- en: It's going to take a few minutes.
- pt: Vai levar alguns minutos.
- pt_literal: Quanto a alguns minutos (数 prefixo 'alguns' + は tópico), leva.
- Layer-A match: 数 / すう / 名詞/数詞

**`vocab:1533340` - 綿** &middot; selected &middot; `les:n3-estado-08` &middot; polite &middot; tatoeba 231320

- jp: あのシャツを着てみなさい。上質の綿でできています。
- en: Try on that shirt. It's made of fine cotton.
- pt: Experimenta aquela camisa. Ela é de algodão de boa qualidade.
- pt_literal: Aquela camisa (を objeto direto), veste e vê (てみる tentativa + なさい ordem branda). De algodão de boa qualidade (で material) está feita.
- Layer-A match: 綿 / わた / 名詞/普通名詞

**`vocab:1150450` - 愛する** &middot; selected &middot; `les:n3-conectores-01` &middot; neutral &middot; tatoeba 144817

- jp: 親は子を愛する。
- en: Parents love their children.
- pt: Os pais amam os filhos.
- pt_literal: Quanto aos pais (は tópico), os filhos (を objeto direto) amam.
- Layer-A match: 愛する / あいする / 動詞/一般

## What still needs a human

- **Four generated rows introduce a kanji the course has not taught yet, and in each case it is the
  target's own** (位, 灯, 常, 額). That is unavoidable when the target *is* the new kanji; furigana covers
  it, and 70% of the 4,197 W13 rows already accepted carry untaught kanji too. Nothing else in any
  generated row leaves the known set.
- **上(かみ) is the one reading a generated row cannot force.** `川の上から下まで歩いた` pairs 上 with 下 to
  push the かみ/しも reading, but a teacher should confirm the furigana before it ships.
- **`register` uses four values** (neutral / polite / casual / formal) and treats plain-form written
  narrative as *neutral*, per finding 1 of `w13_authoring_report.md`. The sentence-level `register`
  field does not exist yet (A8 / W31); normalize at apply time.
- **Layer-B dissection is still owed.** As with the 4,223 W13 rows, `ingest_mined_stages.py` wants
  per-token glosses, particle explanations and a structure paragraph; this run authored `pt` and
  `pt_literal` only. The 65 generated rows need the separate ingest path anyway, since they have no
  raw Tatoeba row behind them.
