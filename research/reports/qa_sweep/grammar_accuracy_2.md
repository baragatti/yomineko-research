# QA sweep: grammar accuracy, slice 2 of 4

**Scope.** `corpus/grammar/{n5,n4,n3}.json`, concatenated in that order, records where
`index % 4 == 1`. **124 records** (58 n5, 33 n4, 33 n3). Every record was read in full:
`label`, `forms`, `explanation`, `formation`, `formation_steps`, `steps_unavailable`,
`nuance`, `related`, `refs`, `register`/`nuance_tags`, both locales. Each point was then
cross-checked against every sentence in `corpus/sentences/bank.json` whose `grammar` array
carries its key (all of them, not a sample: the slice's points carry 0 to 8 sentences each).

**Explicitly out of scope and not reviewed:** sentence `structure_explanation` fields
(being re-authored elsewhere), sentence `kana`/furigana, sentence `level` assignment,
and translation quality of sentences except where a translation is the evidence that a
sentence does not illustrate the grammar point it is linked to.

**Reading key.** BLOCKER = teaches learners to produce wrong Japanese. HIGH = a
learner-facing field is unusable, empty, or contradicted by every one of its own examples.
MEDIUM = misleading or self-contradictory, needs an edit before teacher sign-off.
LOW = cosmetic or consistency, batch-fixable.

---

## Class F. Formation rules that are factually wrong or unproducible

### F-1. `gram:n3-you-ni-3` (n3) — the na-adjective rule produces a form that is not this pattern. **BLOCKER**

`formation` (pt-BR): `Verbo na forma comum + ように; adjetivo-い + ように; adjetivo-な + に (não leva だ aqui); substantivo + のように.`
`nuance` (pt-BR): `Atenção ao adjetivo-な: ele se liga com に, não com だ.`
(EN carries the same claim: `な-adjective + に (it does not take だ here)`.)

Followed literally, the na-adjective line yields `静か + に` = 静かに, which is the plain
adverbial form of a na-adjective and carries none of this point's meaning. The pattern
requires the attributive な before ように: **静かなように**, 元気なように, 便利なように.
As written the record teaches a learner who wants "so that it is quiet" to write 静かに.

Note the record is internally aware something is off: `formation_steps` emits variants for
`verb`, `i-adjective` and `noun` only, silently omits `na-adjective`, and still sets
`steps_unavailable: null`.

Proposed fix: `adjetivo-な + な + ように (静かなように; nunca 静かだように)`, mirror the same
correction in `nuance`, and add the variant `{base: na-adjective, steps: [to-attributive, append ように], example: 静かなように}`.

### F-2. `gram:gp-102` (n4) — the linked example uses the exact form the record declares ungrammatical. **BLOCKER**

`steps_unavailable` states, correctly: *"the noun half is also animacy-restricted: はない is
the negative of ある, so an animate head noun takes はいない (学生はいない, not the 学生はない
these steps emit)"*.

The sentence bank then carries, tagged `gp-102`:
`sent:gen-a1650baf4ac0` = **この問題が解けない学生はない** ("Não tem estudante que não consiga resolver este problema").

That is the animate head noun + はない the record itself rules out. Modern standard Japanese
requires **この問題が解けない学生はいない**. Four of the five linked sentences use inanimate
heads (物, 歌, 本, 料理) and are fine; this one is the exception and it is the one a learner
will copy.

Proposed fix: repair the sentence to `この問題が解けない学生はいない`, and add the
animate/inanimate split to the record's `formation` prose (it currently lives only in
`steps_unavailable`, which is an engineering note, not learner-facing).

### F-3. `gram:gp-138` (n4) — なければ is called a particle, and the warning is truncated. **MEDIUM**

`nuance` (pt-BR): `... são opostos (não confunda a partícula なければ.)`
`nuance` (en): `... are opposites (don't confuse the なければ particle).`

なければ is not a particle. It is the negative conditional (ば-form of the negative
auxiliary ない), which is exactly what the record's own `formation` derives two lines
earlier. On top of that the warning has no object: confuse it *with what*?

Proposed fix: `... são opostos: 行けばよかった nega nada, 行かなければよかった nega a ação. Não
troque 〜ば (condicional afirmativo) por 〜なければ (condicional negativo).`

### F-4. `gram:douyatte` (n5) — attributes やって to する. **MEDIUM**

`formation` (pt-BR): `Literalmente é どう (como) + やって (forma て de やる/する, 'fazendo')`

やって is the て-form of やる only. The て-form of する is して. A beginner reading this can
reasonably conclude that する → やって, which is wrong and will resurface as ×やって instead
of して in every て-form drill.

Proposed fix: `やって (forma て de やる, "fazer")`. If the near-synonymy with する is worth
keeping, say it separately: `やる é o equivalente coloquial de する, mas só やる produz やって`.

### F-5. `gram:gp-126` (n4) — the loanword ban is contradicted by the record's own example set. **MEDIUM**

`nuance` (pt-BR): `... não se diz 化する com palavras casuais ou empréstimos do dia a dia(para esses usa-se 〜になる/〜にする)`

The first sentence linked to this very record is `sent:gen-0b2679ac5ee0` =
**古い書類をデータ化しています** ("Estou digitalizando documentos antigos"), where 化する is
attached to the katakana loanword データ. The rule as stated is simply false: データ化,
デジタル化, ペーパーレス化, グローバル化 are all standard.

Proposed fix: soften to productivity rather than prohibition, e.g. `化する é mais produtivo
com 漢語 (compostos sino-japoneses) e com empréstimos já estabelecidos como termos técnicos
(データ化, デジタル化). Não force 化する sobre gíria ou palavras do dia a dia; nesses casos use
〜になる/〜にする.` (Also missing a space before the parenthesis, see T-7.)

### F-6. `gram:gp-24` (n5) — the counter-example does not illustrate the stated rule. **MEDIUM**

`nuance` (pt-BR): `Outro reflexo a evitar: não coloque です antes do negativo (高くないです está certo, mas 高いじゃない está errado).`

The stated rule is about placing です before the negative; the "wrong" example 高いじゃない
contains no です at all. It is wrong for a different reason (an i-adjective negated with
じゃない), which is the *previous* sentence's point. A learner cannot derive the rule from
the example given.

Proposed fix: split the two: `Não negue um adjetivo-い com じゃない (×高いじゃない). E o です vem
DEPOIS do negativo, nunca antes: 高くないです, nunca ×高いですない.`

### F-7. `gram:n3-ba-hodo` (n3) — the na-adjective line is under-specified and its literal reading fails. **MEDIUM**

`formation` (pt-BR): `Com adjetivo-na: であれば + な-adjetivo + ほど, ou o padrão であればあるほど.`

Read literally, `であれば + 便利 + ほど` gives ×便利であれば便利ほど. The correct forms are
**便利であれば便利なほど** (attributive な required) or **便利であればあるほど**. The verb and
i-adjective lines above it are exact; only this one leaves the connector unstated, and it is
the one slot where a learner cannot guess.

Proposed fix: `Com adjetivo-な: 〜であれば + 〜な + ほど (便利であれば便利なほど), ou o padrão fixo 〜であればあるほど (便利であればあるほど).`

### F-8. `gram:sou-ni-sou-na` (n4) — `formation_steps` emits a form the prose never introduces. **LOW**

`formation_steps` variants 3 and 4: `verb + to-nai-stem + さそうな / さそうに`, examples
**降らなさそうな**, **降らなさそうに**. The `formation` prose covers only affirmative stems
(高い→高そう, 降る→降りそう) plus two lexical exceptions (`いい → よささそう`… actually
`いい → よさそう; ない → なさそう`). It never states a rule for negated verbs, so the emitted
variant is unsourced from the record's own text. Separately, the さ-insertion on a *verb*
negative is the colloquial variant; prescriptive grammar and most JLPT material give
**降らなそう** (さ-insertion belongs to the adjectives ない and よい).

Proposed fix: either add the negative-verb rule to `formation` and note both 降らなそう /
降らなさそう with the register difference, or drop the two variants and record the omission
in `steps_unavailable`.

---

## Class X. Example sentences that do not carry the point they are tagged with

Cross-checking is where this slice is weakest. Below, the ratio is *sentences that do not
demonstrate the documented pattern / total sentences linked to the key*. Ratios are exact
(the whole linked set was read, not a sample). These are corpus-graph defects, but they are
grammar defects in effect: the linked sentence bank is what a lesson or exercise will pull
to illustrate the point.

### X-1. `gram:no-naka-de` (n4) — 5/5 sentences use the sense the nuance forbids. **HIGH**

The record teaches の中で as the **scope of a comparison** ("entre/dentre", used with
superlatives), and `nuance` says outright: `Aqui で marca o escopo da comparação, não "dentro
de" no sentido espacial.`

All five linked sentences are spatial:
| sentence | pt |
|---|---|
| 鳥が木々の中でさえずっている。 | Os pássaros estão cantando entre as árvores. |
| 図書館の中で話をしてはいけない。 | Não se deve conversar dentro da biblioteca. |
| 私は電車の中で読む本がほしい。 | Eu quero um livro para ler no trem. |
| 私の兄は電車の中でスリにあった。 | ... dentro do trem. |
| 雨の中で歌いたい気分だ。 | Estou com vontade de cantar na chuva. |

Not one shows `〜の中で〜が一番〜`. Proposed fix: re-link to the comparison sentences that
already exist under `gram:gp-46` (スポーツの中でサッカーが一番人気です, 一年の中で夏が一番暑い,
クラスの中で彼が一番背が高い) or generate three; drop the spatial five from this key.

### X-2. `gram:n3-ta-tokoro` (n3) — 6/6 sentences belong to a different, existing record. **HIGH**

The record teaches 〜たところ = "ao fazer X, descobri Y" (discovery reading), and `nuance`
says: `Cuidado para não confundir com outros usos de ところ: ～ているところ ... e ～たところだ
(acabar de fazer) têm sentidos diferentes.`

All six linked sentences are 〜たところだ / 〜たところです = "acabar de fazer":
今やっと始めたところです / 銀行へ行ってきたところです / 駅へ行って来たところだ /
バスは今出発したところだ / たった今帰ったところだよ / バスはちょうど出たところだった.

`gram:ta-tokoro` (n4, label *"acabar de fazer (〜たところだ)"*) is the record these six
actually belong to. Proposed fix: move all six to `ta-tokoro`; author discovery-reading
examples for `n3-ta-tokoro` (聞いたところ、〜だった / 調べたところ、〜が分かった).

### X-3. `gram:n3-to-iu-no` (n3) — 0/5 sentences show the documented pattern. **HIGH**

The record teaches というのだ／というのです (explanatory) and warns:
`não confunda com というのは (que define um termo ...)`.

| sentence | what it actually is |
|---|---|
| 朝の5時だというのに明るい。 | というのに, concessive |
| スペシャルというのはどんな味ですか。 | というのは, the definition use the nuance warns against |
| ＵＮというのは何を表わしていますか。 | というのは |
| あなたがやったというのは本当か。 | というのは |
| この川は何というのですか。 | 何と言う + のですか ("what is it called"), not explanatory というのだ |

Proposed fix: re-link the というのは sentences to the record the nuance names (gid 422) and
supply real というのだ examples (急に休むというのだ / 知らなかったというのです).

### X-4. `gram:n3-ppai` (n3) — 2/2 sentences are the confusion the nuance warns against. **HIGH**

The record teaches 〜でいっぱい (noun + で + いっぱい) and `nuance` says:
`Cuidado para não confundir com o advérbio いっぱい no sentido de 'bastante / um monte'`.

Both linked sentences are exactly that adverb/predicate use, and neither contains で:
車が**いっぱい**でした ("Havia um monte de carros") / こっちは**いっぱい**です.

Proposed fix: link or generate 部屋は荷物でいっぱいだ / 心配でいっぱいです / 頭が仕事のことでいっぱいだ.
See also S-6 on this record's key.

### X-5. `gram:demo` (n5) — the headline sense has no example at all; 3/5 are the で+も confusion. **MEDIUM**

Role (1) in the explanation is the sentence-initial conjunction でも ("mas"). **No linked
sentence shows it.** Of the five:

| sentence | verdict |
|---|---|
| 時間はいくらでも作れる。 | ok (indefinite いくらでも, covered by `formation`) |
| あれ？…パフォーマンスでもやってるのか？ | ok (role 2, "ou algo assim") |
| 万人の友は誰の友でもない。 | not this point: copular で + も + ない |
| 自分でもわかってるくせに。 | not this point: でも "até mesmo", an undocumented third sense |
| 美人でもある。 | not this point: でもある |

The record's own `nuance` says `Não confunda este でも (conjunção) com o で de lugar/meio + も`,
and three of five examples are that confusion.

### X-6. `gram:mo` (n5) — 5/8 do not show the particle も as documented. **MEDIUM**

先日はどう**も** (lexical どうも, not the particle), 雨で**も**行きます (でも), で**も**なんで？
(sentence-initial でも), 誰も来なかった (indefinite + negative, a different point), 美人でもある
(でもある). Only 弟もそうです / 私もそうです / どいつもこいつも carry the documented "também".
Separately, the emphatic **number + も** (三杯も飲んだ), which the `explanation` and
`formation` both foreground, has no example.

### X-7. `gram:to-kiita` (n4) — 3/6 use 聞く in the sense the nuance excludes. **MEDIUM**

`nuance`: `聞く tem dois sentidos (ouvir e perguntar); aqui é "ouvir".`
Half the linked set is "perguntar", and their own pt translations say so:
「花が咲いているか」と聞いた ("**Perguntei** se...") / ある外国人が私に駅がどこにあるかと聞いた
("me **perguntou**") / 彼は僕に外国へ行きたいかどうかと聞いた ("me **perguntou**").

### X-8. `gram:gp-134` (n4) — 4/7 are それ + で, not the conjunction それで. **MEDIUM**

それで十分だよ / それでいいよ / それでいい？ / それで十分？ are all それ ("isso") + instrumental
で = "com isso", not the causal connector the record defines as opening a second sentence.
Only the three generated sentences (おなかがすいた　それでパンを買った etc.) are on point.

### X-9. `gram:gp-42` (n5) — 3/5 are the polite-refusal けっこう, which `forms` does not cover. **MEDIUM**

`forms` and `label` define only the degree adverb ("bastante / razoavelmente"). Three of
five sentences are the second sense (わざわざ電話をかけてくださらなくてけっこうです /
お水だけでけっこうです / いいえ、けっこうです。), which appears in `nuance` as an aside but has
no entry in `forms`. Either add a second `forms` entry with the refusal gloss, or move
those three sentences off this key.

### X-10. `gram:gp-72` (n4) — 3/5 are 〜ているところ, which has its own record. **MEDIUM**

The point is 〜**る**ところだ ("prestes a"). 今、勉強してるところだよ / 夕食を待っているところだ /
上着を今着ているところだ are 〜ているところ, and `gram:teiru-tokoro` (n4) exists for exactly
that. Only バスは発車するところだった and ちょうど出かけるところだ are on point.

### X-11. `gram:te-de` (n5) — one sentence is the verb て-form the formation explicitly excludes. **MEDIUM**

`formation`: `A escolha entre て e で aqui depende do TIPO de palavra ... e não tem a ver com
a forma て dos verbos.` Yet `sent:gen-790b6cf52284` = **今日は晴れて暖かい** is a verb
(晴れる) in the て-form. The other four (小さくてかわいい, 安くておいしい, 静かできれいだ,
学生で〜先生だ) are correct.

### X-12. `gram:n3-nanka` (n3) — 3/3 sentences use a construction the record does not document. **MEDIUM**

`formation` documents only suffixal なんか (noun/verb/adjective + なんか). All three linked
sentences are clause-initial filler なんか or 〜てなんかない:
なんかフラフラする ("Sei lá, tô meio tonto") / なんかおかしくない？ / びびってなんかないよ.
The filler use is the most frequent one in speech and is missing from the record entirely.

### X-13. `gram:gp-5` (n5) — 0/7 sentences show the よ- paradigm the record exists to teach. **MEDIUM**

The record's whole content is that いい conjugates from よ- (よくない / よかった / よくなかった / よく).
Linked: four 〜てもいい / 〜なくていい permission sentences, one かっこいい, and two attributive
いい + noun (いい天気だ, いい人です). Not one inflected form appears.

### X-14. `gram:dewa-nai-ka` (n4) — 2/5 are ordinary negation, not the rhetorical tag. **LOW**

これは本物のダイヤではないかもしれない is ではない + かもしれない ("might not be");
病気で動かれなくなったのではないかな is のではないか (conjecture). Neither is the
confirmation/emphasis ではないか the record teaches. Also 今夜は一つ語り明かそうではないか is
volitional + ではないか, a shape `formation` does not list (it lists noun, na-adjective,
plain verb, i-adjective).

### X-15. `gram:hajimeru` (5/6) and `gram:tsuzukeru` (5/7) — mostly standalone verb, not the compound. **LOW**

Both labels lead with the compound auxiliary (〜始める / 〜続ける), but only 死に始める for one
and 走り続ける / 歌い続ける for the other actually compound. The rest use the verb on its own
(始めることにしましょう, 勉強を続ける...), a use both records mention in passing. Worth
rebalancing so the compound is the majority of the exemplar set.

---

## Class T. Corrupted, truncated, or malformed learner-facing text

### T-1. `gram:yatto` (n4) — the pt-BR `formation` is truncated to its own footnote. **HIGH**

`formation` pt-BR, complete text:
> `Também acompanha o presente para algo que dá só na medida: やっと間に合う (やっとまにあう) = "chego bem em cima da hora".`

`formation` en, complete text:
> `It is an invariable adverb: you just place it before the verb or the clause, usually at the start or near the verb. やっと + clause, generally with the verb in the past (〜た) for something already achieved: やっと家に着いた ... It also accompanies the present for something that just barely makes it: やっと間に合う ...`

The pt-BR version lost the first two sentences and now opens with "Também" ("Also") with
nothing preceding it. For a pt-BR learner the formation field teaches nothing. The record's
own `steps_unavailable` already noticed: *"The record's formation field is also incomplete,
it opens with 'Também acompanha o presente…' and never states the base rule it is adding to"*.

Proposed fix: restore the pt-BR text as a translation of the full EN field.

### T-2. `gram:gp-134` (n4) — scrambled brackets in the pt-BR formation. **MEDIUM**

pt-BR: `[Frase 1 (causa]。それで、[Frase 2) resultado].`
en: `[Sentence 1 (cause)]。それで、[Sentence 2 (result)].`

The parenthesis and bracket are interleaved wrongly in pt-BR only. Fix:
`[Frase 1 (causa)]。それで、[Frase 2 (resultado)].`

### T-3. `gram:mae-ni` (n5) — stray punctuation plus a duplicated clause in the pt-BR explanation. **MEDIUM**

pt-BR (verbatim excerpt):
> `... (食べる前に手を洗いました = lavei as mãos antes de comer) ;, a um substantivo de tempo com の (授業の前に, 昼ごはんの前に) ou a uma quantidade de tempo, aí sem の (三年前に = três anos atrás) ou a uma quantidade de tempo ("três anos atrás").`

Two defects: the orphan ` ;,` sequence, and `ou a uma quantidade de tempo` appearing twice in
one sentence. The EN field is clean and much shorter. Fix: rewrite the pt-BR from the EN,
keeping the pt-only detail (verb always in dictionary form) as its own sentence.

### T-4. `gram:no-naka-de` (n4) — an unclosed parenthesis swallows the last two sentences. **MEDIUM**

pt-BR: `... ou trocar で por に (fique atento a isso. Para grupos de pessoas/lugares também se usa 〜のうちで. Registro neutro.)`
en (correct): `... (watch out for this). For groups of people/places, 〜のうちで is also used. Neutral register.`

### T-5. Systematic: 17 fields across 12 records end with a parenthesis that swallowed the closing sentence. **LOW**

Same signature as T-4: the final one or two sentences were pulled inside a parenthesis and
the period landed inside it. This looks like fallout from the em-dash removal pass. Full
list (field, locale):

| record | field | locale | tail |
|---|---|---|---|
| `gp-140` | formation | pt-BR, en | `(a comparação está toda na estrutura, e o adjetivo fica na forma normal.)` |
| `gp-5` | nuance | en | `(every inflection uses the stem よ-. Think of ... in its own ending.)` |
| `naa` | nuance | en | `(it's the sentence's 'sigh.' Portuguese speakers tend to underuse it; ... expressive.)` |
| `toki` | formation | pt-BR, en | `(note o の.)` / `(note the の.)` |
| `toki` | nuance | en | `(don't use a 'bare' とき as in Portuguese. The verb within the clause ... final verb.)` |
| `gp-118` | nuance | pt-BR | `(está errado; tem que ser 千円しかない.)` |
| `gp-122` | nuance | pt-BR | `(em português dizemos "de" nos dois casos ... deixe o contexto guiar.)` |
| `gp-138` | nuance | pt-BR | `(não confunda a partícula なければ.)` |
| `gp-92` | nuance | pt-BR, en | `..., de uso diferente.)` |
| `koto` | nuance | pt-BR | `(a nominalização com こと faz esse papel.)` |
| `mitai-ni` | formation | pt-BR, en | `(é a mesma diferença de に vs な dos adjetivos-な.)` |
| `nakereba-ikenai` | nuance | pt-BR | `(evite em contexto formal.)` |
| `no-naka-de` | nuance | pt-BR | see T-4 |

Note `gp-5` and `naa` (en) and `toki` (en) are the worst of these: the opening parenthesis
is in one clause and the closing one two sentences later, so the parenthetical reads as if
the whole passage were an aside.

### T-6. Stripped diacritics in three n3 records. **MEDIUM**

| record | field | verbatim | should be |
|---|---|---|---|
| `n3-to-ii-naa` | nuance pt-BR | `E coloquial e cheio de sentimento; em fala mais neutra usa-se so といい` … `o と aqui não e o 'e' de junção` | `É coloquial` … `usa-se só` … `não é o 'e'` |
| `n3-ni-yoreba` | nuance pt-BR | `Como a informação e de segunda mão, e natural fechar a frase` | `é de segunda mão, é natural` |
| `n3-to-iu-no` | nuance pt-BR | `Soa explicativo e levemente enfatico` … `aqui o foco e justificar um motivo` | `enfático` … `o foco é justificar` |

These three are the only records in the slice with this defect, which suggests a single bad
authoring pass rather than a global encoding problem.

### T-7. Minor pt-BR typography. **LOW**

- `gram:te-morau` nuance pt-BR: `quem PRÁTICA a ação leva に` → `quem PRATICA a ação`.
- `gram:gp-126` nuance pt-BR: `empréstimos do dia a dia(para esses usa-se ...)` → missing space before `(`.
- `gram:n3-koso` explanation pt-BR: same missing-space-before-paren pattern.
- `gram:n3-tsumari`: `forms[0].form` is `～つまり` while `structure_pattern` is `つまり`. The
  leading `～` asserts that something attaches before it, which the record explicitly denies
  ("Costuma vir no começo da segunda frase"). Drop the tilde.

### T-8. `gram:gp-28` (n5) — locale parity break in `explanation`. **MEDIUM**

The EN explanation carries two sentences the pt-BR one does not:
> `Before に the verb goes in the ます-stem (the ます form minus ます): 食べに行く "go eat"; never 食べるに行く. A noun that names an activity also works: 買い物に行く "go shopping".`

The pt-BR learner loses the `×食べるに行く` warning at the explanation level (it survives in
`formation`/`nuance`, so this is parity, not a content loss). Related, in the same record:
`formation` files 勉強しに行く under the *second* formation ("substantivo de ação + に行く"),
but 勉強しに行く is the *first* formation (masu-stem of 勉強する). Only 買い物に行く and
勉強に行く belong to formation two.

---

## Class L. Internal pipeline vocabulary leaking into learner-facing fields

### L-1. `gram:n3-kanaa` (n3) — "seed formation" in the EN nuance. **MEDIUM**

en: `PT trap: **the seed formation that suggests** だかなあ sounds forced in real speech; ...`
pt-BR (clean): `Armadilha PT: a construção だかなあ soa forçada na fala real; ...`

"Seed formation" is build-pipeline vocabulary and means nothing to a reader. Fix the EN to
match the pt-BR: `PT trap: the construction だかなあ sounds forced in real speech; ...`

### L-2. `gram:n3-to-iu-no` (n3) — a raw numeric id in both locales. **MEDIUM**

pt-BR: `não confunda com というのは (que define um termo, **gid 422**)`
en: `don't confuse it with というのは (which defines a term, **gid 422**)`

Internal record id exposed to the learner. Fix: drop `gid 422` from the prose and put the
link in `related` (which is empty, see S-3).

### L-3. `gram:n3-nado` (n3) — positional cross-reference in a random-access corpus. **MEDIUM**

pt-BR: `a versão coloquial e mais informal é なんか (**veja o ponto seguinte**)`

"The next point" is meaningless once records are addressed by id, filtered, or shown one at
a time in an app. The target (`gram:n3-nanka`) exists, but `related` is empty on both.
Fix: `... é なんか` plus `related: ["gram:n3-nanka"]`.

### L-4. `gram:te-kudasai` (n5) — a dangling reference that is also ambiguous. **MEDIUM**

`formation` pt-BR: `A formação da forma-て está **no ponto 〜ている**.`

Two records own that pattern (`gram:te-iru`, n5, and `gram:n3-te-iru`, n3), `related` is
empty, and the て-form formation is not actually in either record's `formation` field. A
learner following this pointer lands nowhere. Fix: point at the conjugation tables in
`corpus/conjugations/` or at the record that really derives the て-form, and populate
`related`.

### L-5. Stale "record is corrupted" notes in `steps_unavailable`. **LOW**

Two records claim a corruption that no longer exists in the data:

- `gram:n3-kurai-wa-nai`: *"this record's structure_pattern and forms[0].form are corrupted
  with an editing instruction in place of the pattern (failure mode F6)"*.
  Actual values today: `structure_pattern = "～くらいは～ない"`, `forms[0].form = "～くらいは～ない"`. Clean.
- `gram:n3-tatoe-temo`: *"(Record defect noted separately: this point's structure_pattern
  field contains an editing instruction instead of a value.)"*
  Actual value today: `structure_pattern = "たとえ～ても"`. Clean.

The corruption was evidently repaired without clearing the notes. As written they will send
a human reviewer looking for a defect that is not there. Fix: delete the two parenthetical
claims. (A corpus-wide scan for the same signature found no remaining editing-instruction
leakage; the 16 `structure_pattern` values containing Latin text are all deliberate
metalanguage such as `い-Adjectives くない`, `Verb［た・ている］+ Noun`, `Question-phrase + か`.)

---

## Class N. `nuance` contradicting `explanation` or itself

### N-1. `gram:n3-ni-kawatte` (n3) — the nuance tells the learner not to confuse the point with itself. **MEDIUM**

`nuance` pt-BR: `... sentido totalmente diferente de "em vez de". **Não confunda também com にかわって (substituir alguém)** e にかわり no sentido de revezamento.`

にかわって *is* this record (`structure_pattern: ～にかわって`, "substituir alguém" is its own
gloss). The sentence instructs the reader to distinguish 〜にかわって from 〜にかわって. The EN
repeats the error verbatim. Probably one of the two strings was meant to be a different
form (に代わり? にかわりまして? に変わって, already covered by the preceding sentence).

Proposed fix: `Armadilha PT: existe um に変わって (de 変わる, "transformar-se em") que soa
igual mas significa outra coisa. E a variante にかわり／に代わり é a mesma ideia em registro
mais formal, não um ponto novo.`

### N-2. `gram:gp-31` (n5) — explanation and nuance disagree about なんで = "com o quê". **LOW**

`explanation`: `Cuidado: dependendo do contexto e da entonação, なんで também **pode**
significar "por meio de quê / com o quê" (instrumento), mas no N5 o uso central é "por quê".`
`nuance`: `なんで **não é** "com o quê" no sentido neutro, é "por quê".`

The nuance flatly denies what the explanation conceded one field earlier. Both are
defensible in isolation; together they read as an error. Fix: make the nuance
register-scoped, e.g. `Na fala casual, なんで é lido como "por quê" por padrão; para "com o
quê" (instrumento) o japonês prefere 何で (nanide) ou 何を使って, justamente para evitar a
ambiguidade.`

### N-3. `gram:node` (n5) — the sentence-final ban is undercut by the record's own formation. **LOW**

`nuance`: `Não use ので no fim de uma frase isolada como justificativa seca; para isso existe から.`
`formation`: `Em registro mais formal, também aparece depois de です/ます (行きますので).`

〜ますので trailing off is precisely the polite, sentence-final justification the nuance
forbids (お先に失礼します、用事がありますので。). The nuance is right that から is the natural
answer to a bare なんで？ question, but as stated it is too absolute. Fix: scope it to the
Q&A answer position rather than to "sentence-final" generally.

---

## Class S. Structural and coverage defects

### S-1. Seven points in this slice have zero example sentences; three more have exactly one. **HIGH**

Zero (`bank.json` contains no sentence whose `grammar` array names the key):
`n3-kurai-wa-nai`, `n3-moshi-temo`, `n3-ni-kawatte`, `n3-ni-shitemo`, `n3-sa`,
`n3-tatoe-temo`, `n3-tokorode`.

Exactly one: `n3-ba-hodo`, `n3-to-ii-naa`, `n3-to-shitara`.

A point with no dissected sentence cannot be taught, drilled, or exercised, and cannot be
validated by any downstream check. Note that four of the seven (`n3-moshi-temo`,
`n3-ni-shitemo`, `n3-tatoe-temo`, `n3-tokorode`) are common, high-yield N3 patterns.

### S-2. All 33 n3 records in the slice have `forms[].meaning: null`. **HIGH**

Shape in n5/n4:
```json
{"form": "だ", "meaning": {"pt-BR": "ser/estar (casual)", "en": "to be (casual)"}}
```
Shape in every n3 record of this slice:
```json
{"form": "～ば～ほど", "meaning": null}
```
`forms[].meaning` is the per-form learner-facing gloss. It is empty for the whole n3 block,
so any UI or exercise generator that reads `forms` gets a bare pattern string with no
meaning attached. Affected keys: all 33 `n3-*` records in this slice (`n3-ba-hodo` …
`n3-you-to-omou`).

### S-3. `related` is empty on 124/124 records in this slice, and on 492/496 corpus-wide. **HIGH**

Spec 1.7 requires the corpus to be one bidirectionally cross-referenced graph. `related` is
the grammar-to-grammar edge and it is essentially unpopulated. Concrete consequences already
visible in this slice: L-2, L-3 and L-4 all had to encode a cross-reference as free prose
because the field was unavailable, and S-5's duplicate pairs are invisible to any consumer.

### S-4. All 33 n3 records have `refs: null`. **MEDIUM**

n5/n4 records carry `refs: {label_en, also_known_as, level_sources}`; every n3 record in the
slice has `refs: null`. `level_sources` survives at the top level
(`{"hanabira": "n3"}`, `level_confidence: 0.34`, `level_agreement: "1/1"`), so this is a
shape inconsistency rather than data loss, but `label_en` and `also_known_as` are simply
absent for the whole n3 block, which will hurt search and alias matching.

### S-5. Duplicate and near-duplicate points, unmerged and unlinked. **HIGH**

Corpus-wide there are 23 `structure_pattern` collisions. Fourteen involve a record in this
slice; three more are duplicates by content rather than by pattern string. None of the pairs
cross-reference each other (`related` empty on both sides, see S-3).

| pattern / point | records | note |
|---|---|---|
| ように | `gp-128` (n4), `n3-you-ni` (n3), `n3-you-ni-2` (n3), **`n3-you-ni-3`** (n3) | four records, identical `structure_pattern`; the `-2`/`-3` suffixes are the only thing telling them apart, and `-3` is the one with the wrong na-adjective rule (F-1) |
| めったにない | `n3-metta-ni-nai`, **`n3-metta-ni-nai-2`** | `sent:tatoeba-7704572` is tagged with **both** keys at once |
| のがへた / のが下手 | **`gp-53`** (n5), **`no-ga-heta`** (n5) | same point, near-identical `explanation`, different sentence sets, both n5 |
| みたいに・みたいな | **`gp-76`** (n4), **`mitai-ni`** (n4), `mitai-na` (n4) | `gp-76` covers what the other two split |
| がる / たがる | **`garu-gatteiru`** (n4), `gp-75` (n4), **`tagaru`** (n4) | `garu-gatteiru`'s `formation_steps` emit 食べたがる, i.e. `tagaru`'s whole content |
| たところ | `ta-tokoro` (n4), **`n3-ta-tokoro`** (n3) | see X-2 |
| ている | `te-iru` (n5), **`n3-te-iru`** (n3) | see L-4; also a level conflict, n5 vs n3 for the same pattern |
| こと | **`koto`** (n4), `n3-koto` (n3) | |
| さ | `sa` (n4), **`n3-sa`** (n3) | |
| しかない | **`gp-118`** (n4), `n3-shika-nai` (n3) | |
| など | `nado` (n4), **`n3-nado`** (n3) | L-3's "next point" reference sits on the n3 copy |
| ばかり | **`bakari`** (n4), `n3-bakari` (n3) | |
| ばよかった | **`gp-138`** (n4), `n3-ba-yokatta` (n3) | |
| まま | **`mama`** (n4), `n3-mama` (n3) | |
| らしい | **`rashii`** (n4), `n3-rashii` (n3) | |
| たら | **`gp-60`** (n4), `tara` (n4) | both n4, same pattern |

(Bold = in this slice. The remaining collisions, `すこしもない`, `てすみません`, `てほしい`,
`てみる`, `ても`, `という`, `ないで`, `ないと`, `の`, `まで`, fall outside this slice but share
the same n4-vs-n3 duplication signature and should be handled in the same pass.)

The practical damage is not only redundancy: sentences get split across the duplicates
(`n3-ta-tokoro` holds six sentences that belong to `ta-tokoro`, X-2), and levels conflict
(ている is n5 in one record and n3 in the other), so any level-gated lesson build will
disagree with itself.

### S-6. `gram:n3-ppai` — the key does not identify the record's content. **MEDIUM**

`key`/`slug` read as 〜っぽい ("-ish, tends to"), a real and distinct N3 point. The record's
entire content is 〜でいっぱい ("full of"): `structure_pattern: ～でいっぱい`,
`label: cheio de / lotado de (〜でいっぱい)`. A corpus-wide scan finds no record for 〜っぽい at
all, so this is not a collision, but the identifier is actively misleading and violates the
"stable, meaningful ID" contract. Rename to `n3-de-ippai` (with a slug-history note), and
log 〜っぽい as an n3 coverage gap if n3 is meant to be complete.

### S-7. `steps_unavailable: null` while `formation` documents constructions the steps cannot emit. **MEDIUM**

The campaign's convention elsewhere is scrupulous: `demo`, `shikashi`, `gp-134`, `amari-nai`,
`gp-68` and others carry long, precise `steps_unavailable` notes explaining exactly what was
withheld and why. These five records break that convention by asserting full coverage:

| record | `formation_steps` emits | `formation` also documents, unencoded |
|---|---|---|
| `gp-57` (もらう) | only `to-te-form + もらう` (教えてもらう) | the main-verb frame `[receiver]は [giver]に [thing]を もらう`, which is what **all six** of its linked sentences use (ちちに とけいを もらいました …) |
| `naa` | only `i-adjective + なあ` (寒いなあ) | nothing for noun / na-adjective + だ + なあ, though its own sentences need it (タフだなあ, いい天気だなあ) |
| `n3-nanka` | only `noun + なんか` | "também a verbos e adjetivos na forma simples" |
| `n3-dakedo` | clause-final けど / だけど | the sentence-initial connective だけど (`Frase 1. だけど、Frase 2.`) |
| `n3-you-ni-3` | verb / i-adjective / noun | na-adjective (and see F-1: the prose rule for it is wrong anyway) |

Fix: either encode the missing variants or write the `steps_unavailable` note, matching the
convention the rest of the batch follows.

---

## What is clean

The following were checked and found correct on every axis reviewed (explanation factual in
both locales, formation producing the listed forms, `formation_steps` chains resolving to
their stated examples, nuance consistent, examples on point). Listing them so the review
queue does not re-litigate them:

`da-desu`, `ga-imasu`, `gp-12`, `gp-140` (content; see T-5 for typography), `gp-144`,
`gp-17`, `gp-20`, `gp-28` (content; see T-8), `gp-35`, `gp-39`, `gp-46`, `gp-9`, `issho-ni`,
`ka-ka`, `keredo-mo`, `naku-temo-ii`, `naru`, `ni-e`, `shikashi`, `ta-koto-ga-aru`,
`te-kudasai` (rules; see L-4), `toki` (rules; see T-5), `wa-dou-desu-ka`, `yo`, `amari-nai`,
`bakari`, `garu-gatteiru`, `gp-106`, `gp-110`, `gp-114`, `gp-118`, `gp-122`, `gp-130`,
`gp-149`, `gp-153`, `gp-60`, `gp-64`, `gp-68`, `gp-76`, `gp-80`, `gp-84`, `gp-88`, `gp-92`,
`gp-96`, `ikou-kei-volitional-form`, `ka-dou-ka`, `kana`, `koto`, `koto-ni-suru`, `mama`,
`mitai-ni`, `nakereba-ikenai`, `nasaru`, `o-ni-naru`, `rashii`, `saseru`, `sonna-ni`,
`tagaru`, `te-ageru`, `te-itadakemasen-ka`, `te-morau`, `te-yaru`, `to-ittemo-ii`,
`tsuzukeru`, `you-ni-naru`, `zehi`, `n3-beki-da`, `n3-dakedo`, `n3-furi-wo-suru`,
`n3-kanaa`, `n3-kesshite-nai`, `n3-koso`, `n3-koto-ni-shite-iru`, `n3-maru-de-you`,
`n3-metta-ni-nai-2`, `n3-moshi-temo`, `n3-nado`, `n3-ni-shitemo`, `n3-ni-yoreba`,
`n3-sete-kudasai`, `n3-sono-ue`, `n3-te-iru`, `n3-to-shitara`, `n3-tokorode`, `n3-tsumari`,
`n3-wa-mochiron-mo`, `n3-wake-ni-wa-ikanai`, `n3-you-to-omou`.

Every `formation_steps` chain in the slice was executed by hand against its own `example`
field and all of them resolve (including the non-obvious ones: `to-nai-stem` conventions
such as 行かな + くてもいい, 書かな + いでください, 高くな + ければいけない; the two-transform chain
`to-masu-stem + たがる + to-te-form + いる` = 食べたがっている; `to-causative + to-te-form +
ください` = 帰らせてください). Fifteen distinct `op` values are used, all consistently.

---

## Counts

**Records checked: 124** (58 n5, 33 n4, 33 n3).
**Records with at least one record-specific finding: 66.**
**Findings: 53** (individual) plus 3 corpus-wide systematic (S-2, S-3, S-4).

| class | findings | severity spread | records touched |
|---|---|---|---|
| F. Formation factually wrong / unproducible | 8 | 2 BLOCKER, 4 MEDIUM, 2 LOW | 8 |
| X. Example sentences do not carry the point | 15 | 4 HIGH, 8 MEDIUM, 3 LOW | 17 |
| T. Corrupted / truncated / malformed text | 8 | 1 HIGH, 4 MEDIUM, 3 LOW | 21 |
| L. Pipeline vocabulary leaking to learners | 5 | 4 MEDIUM, 1 LOW | 6 |
| N. Nuance contradicting explanation | 3 | 1 MEDIUM, 2 LOW | 3 |
| S. Structural / coverage | 7 | 4 HIGH, 3 MEDIUM | 124 (S-3), 33 (S-2, S-4), 10 (S-1), 20 (S-5), 5 (S-7), 1 (S-6) |
| **total** | **46 record-level + 7 structural** | **2 BLOCKER, 9 HIGH, 25 MEDIUM, 11 LOW** | **66 distinct** |

### Suggested triage order

1. **F-1, F-2** (BLOCKER). Both make a learner produce ungrammatical Japanese.
2. **T-1** (pt-BR `formation` of `yatto` is unusable) and **S-2** (n3 `forms[].meaning` empty
   for 33 records). Both are empty learner-facing fields, cheap to fix, high blast radius.
3. **X-1 to X-4** (HIGH). Four points whose entire example set illustrates something else,
   including one (`n3-ta-tokoro`) where the correct destination record already exists.
4. **S-5** (duplicates) and **S-3** (`related` empty). Doing S-5 without S-3 will just
   recreate the problem; the merge pass should populate `related` as it goes.
5. **S-1**. Seven points with no example sentence at all.
6. Everything else in class order; T-5 and T-7 are a single mechanical pass.
