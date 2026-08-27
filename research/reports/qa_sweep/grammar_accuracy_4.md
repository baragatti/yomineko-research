# QA sweep: grammar accuracy, part 4/4

**Slice:** `corpus/grammar/{n5,n4,n3}.json`, records where `(index in concatenated n5+n4+n3 order) % 4 == 3`.
**Size:** 124 records (n5 37, n4 54, n3 33), from `gram:darou` (idx 3) to `gram:n3-zu-ni` (idx 495).
**Scope:** explanation (pt-BR + en), formation, formation_steps, forms, nuance, caution, related/refs, and a
cross-check of every point against the sentences in `corpus/sentences/bank.json` that carry its key.
**Excluded by instruction:** sentence `structure_explanation` fields.

Every record in the slice was read in full. Findings below are only those I can defend with the exact stored
text; each carries the id, the current text, why it is wrong, and a concrete fix.

---

## Result that matters most: formation rules are sound

The assignment flags formation errors as highest severity because a wrong rule teaches learners to PRODUCE
wrong Japanese. I traced every `formation_steps` variant in the slice by hand against its own `example` and
against the prose in `formation`. Step ops used: `append` (86 records), `to-dictionary` (27), `to-te-form`
(17), `to-nai-stem` (13), `to-ta-form` (11), `to-attributive` (8), `to-masu-stem` (8), `none` (6),
`to-adverbial` (5), `to-potential` (4), `replace-ending` (3).

**Zero step chains in the slice emit a wrong surface form.** One prose rule is wrong (F-01 below); the
machine-readable steps are clean.

One note for the consumer, not a defect: `to-nai-stem` means *the ない-form minus its final い* (書く →
書かな), not the mizenkei 書か. Confirmed by every example that uses it (`書かない` = to-nai-stem + `い`,
`書かなくて` = + `くて`, `行かなければよかった` = + `ければよかった`). I checked all 496 records corpus-wide:
0 uses contradict this reading. A consumer that implements `to-nai-stem` as the mizenkei will emit
`書かい`, `書かくて`, `行かければよかった` for 13 records in this slice alone. Worth an explicit line in the
op contract.

---

## Severity 1: factual errors in the taught rule

### F-01 `gram:toka-toka` (n4) formation states a rule that generates ungrammatical Japanese

`formation.pt-BR`: "Muitas vezes o último とか é seguido de um verbo ou de **な** que resume a lista."
`formation.en`: "Often the last とか is followed by a verb or by **な** that sums up the list."

とか is never followed by な. As written the rule licenses ×`りんごとかバナナとかな果物`. The two real
continuations are (a) の before a modified noun (`りんごとかバナナとかの果物`) and (b) する / だ as the
summarizing predicate (`本を読むとか映画を見るとかする`, which is exactly what the record's own example
`sent:gen-09f7ea57423c` does). `な` is almost certainly a typo for `の`.

**Fix:** "Muitas vezes o último とか é seguido de する (ou de outro verbo) que fecha a lista; antes de um
substantivo, usa-se の: りんごとかバナナとかの果物."

### F-02 `gram:wa-ga-wa` (n4) conflates two different grammar points, and its EN explanation is spliced

Three separate problems in one record:

1. **`explanation.en` is textually damaged.** It opens `"It is a pattern that This is the CONTRAST
   pattern: ..."`, runs a complete description of the は…が…は contrast frame, then ends
   `"...which is a different structure. to talk about ONE theme and, within it, contrast two things.
   The typical structure is 'Topic は A が [quality], B は [opposite quality].' Classic example: 象は鼻が長い..."`.
   Two drafts are welded together mid-sentence with a lowercase fragment. `explanation.pt-BR` is clean
   (568 chars vs 1086 in en).
2. **`explanation` and `formation` give incompatible analyses of the same が.** The explanation says
   "o が liga as duas partes com o sentido de 'mas'; **não é o が de sujeito**". The formation says
   "Tema/tópico + は, seguido de **subsujeito + が** e seu predicado", schema
   `[X]は [Y]が [predicado1]、[Z]は [predicado2]`. Those are two distinct constructions
   (contrastive は with conjunctive が vs. the 象は鼻が長い topic/sub-subject frame).
3. **The formation schema does not generate the record's own examples.** `日本語は話せるが英語は話せない`,
   `コーヒーは飲むがお茶は飲まない` and `肉は好きだが魚は嫌いだ` have no `[Y]が` sub-subject slot at all.
   Only `兄は背が高いが弟は低い` fits, and only because it happens to contain both structures.

The record's own `steps_unavailable` already documents part of this ("The record's own explanation field is
additionally damaged... the point needs human repair before steps can be derived"), so this is a known open
item that has not been repaired.

**Fix:** split into two points, or scope this record to the contrastive frame only. Rewrite `explanation.en`
from the clean pt-BR text; change `formation` to `[X]は [predicado1]、(が、)[Z]は [predicado2]` and drop the
sub-subject slot; move 象は鼻が長い to a `nuance` contrast note (where the record already mentions it).

### F-03 `gram:sasuga` (n4) explanation asserts a tone the record itself contradicts

`explanation.pt-BR` ends: "**Sempre tem tom positivo e elogioso.**" (`en`: "It always has a positive,
complimentary tone.")

Contradicted three times inside the same record:
- its own `formation`: "A forma さすがに também pode significar 'mesmo assim / até certo ponto', introduzindo
  uma ressalva (さすがに疲れた)";
- its own `nuance`: "Atenção à dupla função de さすがに, que em outros contextos vira 'mesmo assim/afinal',
  sentido bem diferente do elogio";
- 2 of its 5 example sentences are that non-complimentary use: `sent:tatoeba-10993926`
  さすがにそれはやりすぎだ ("Convenhamos, isso é exagero") and `sent:tatoeba-11022996`
  これはさすがにヤバすぎる.

**Fix:** replace the final sentence with "Na forma さすが (+ nome) o tom é sempre elogioso; a forma さすがに
tem também um segundo uso de ressalva ('convenhamos', 'mesmo assim'), que não é elogio."

### F-04 `gram:n3-nda-mon` and `gram:n3-da-mono-da` (both n3, both in this slice) contradict each other on gender register

- `n3-nda-mon.formation.pt-BR`: "Variantes: **もの (mais formal/feminina)** e **もん (mais coloquial)**."
- `n3-da-mono-da.nuance.pt-BR`: "a variante **だもん** soa ainda mais coloquial e é **típica da fala feminina
  e infantil**."

Both cannot be the feminine variant. The standard description is the first one: もの/だもの carries the
feminine-childish colouring, もん is the general contracted colloquial form used by all speakers. Two records
covering the same point (see F-28) give a learner opposite advice about when to use each.

**Fix:** align on もの = feminine/childish colouring, もん = general contraction; edit
`n3-da-mono-da.nuance` accordingly. Better: merge the two records (F-28).

### F-05 `gram:i-adjectives` (n5) lists a correct form among the wrong ones, then recommends it

`nuance.pt-BR`: "NÃO use です para formar passado ou negativo. 高いでした e **高くないです** como passado
estão errados; ... e a negação educada é **高くないです** ou 高くありません."
`nuance.en` has the same shape.

Read strictly it is not false (高くないです is not a past form), but the paragraph puts a perfectly correct
form in a list of errors and endorses it two sentences later, and it never names the error learners actually
make: ×高くないでした. A beginner scanning this will avoid 高くないです.

**Fix:** "高いでした e 高くないでした estão errados; o passado é 高かった (educado: 高かったです) e o passado
negativo é 高くなかった (educado: 高くなかったです)."

---

## Severity 2: example sets that contradict the point they illustrate

These are the cross-checks the assignment asked for. A learner who reads the explanation and then studies the
attached sentences builds the wrong model. Counts are over the full set carried by that `grammar` key, not a
sample.

### F-06 `gram:owaru` (n4) 5/5 examples show the wrong 終わる

The record teaches the **auxiliary**: "Verbo auxiliar que se prende a outro verbo", `formation` =
masu-stem + 終わる (食べ終わる, 読み終わる). All five carriers use 終わる as an independent intransitive verb:
`学校は何時に終わるの？` / `三月が終わる。` / `学校は三時半に終わる。` / `いつ終わるの？` / `もうすぐ終わる？`.
Not one is a compound. **Fix:** retag these to a plain-verb entry and select or generate 読み終わる /
食べ終わる / 話し終わる sentences.

### F-07 `gram:gp-62` (n4, 〜なくて) 5/5 examples show 〜なくてもいい instead

The record teaches the linking negative て-form ("liga a negativa ... geralmente indicando causa/motivo",
example お金がなくて、買えませんでした). All five carriers are the *permission-not-to* pattern:
`入院しなくてもいいです。` / `言わなくてもわかりますよ。` / `言わなくていいよ。` / `急がなくてもいいよ。` /
`気にしなくていいんですよ。` Zero show causal なくて. **Fix:** retag all five to the 〜なくてもいい point and
attach causal examples (お金がなくて…, 時間がなくて…).

### F-08 `gram:gp-98` (n4, 何+contador+か) 5/5 examples show the か the record warns against

The record teaches indefinite quantity ("何人か来ました = vieram algumas pessoas") and its `nuance` says
explicitly: "Não confunda este か (que forma quantidade vaga) com o か de fim de frase (pergunta)". All five
carriers are sentence-final or embedded interrogative か: `ビールをなんばい飲みましたか` /
`りんごをなんこ買いますか` / `本をなんさつ借りましたか` / `なんかい電話しましたか` /
`なんにん来るか分かりません`. **Fix:** generate 何人か来ました / 何回か行ったことがあります /
何日か休みました and retag the current five to a counter-question point.

### F-09 `gram:n3-koto-wa-nai` 5/5 examples show the sense the record forbids

The record teaches modal "no need to" and its `nuance` says "Não confunda com ことがない, que significa
'nunca fiz/nunca aconteceu' (experiência)". All five carriers are existential [clause こと] + は + ない:
`止まることはない。` / `何も言うことはないの？` / `何かすることはないの？` / `もはや言うことはない。` and,
worst, `見たことはないよ。` ("Nunca vi isso"), which is precisely the 〜たことがない experience pattern the
nuance warns about. **Fix:** replace with 心配することはない / 急ぐことはない / わざわざ行くことはない.

### F-10 `gram:gp-132` (n4, 〜が見られる) 5/5 examples show the reading the nuance excludes

`register: [formal, written]`, `usage_contexts: [written, academic]`, and `nuance.pt-BR` says "aqui が見られる
**não significa 'alguém consegue olhar'**...; o foco é o fenômeno que se apresenta/se constata". All five
generated carriers are exactly "someone can see", and all five pt-BR translations say "dá pra ver":
`祭りでは美しい花火が見られる` / `夜は星がよく見られる` / `山の上から海が見られる` / `公園で桜が見られる` /
`この町では古いお寺が見られる`. None is the expository "この傾向が見られる" register the record declares.
**Fix:** generate expository examples (最近この傾向が見られる / データに変化が見られた /
若者の間に新しい習慣が見られる) and move the five "dá pra ver" sentences to the potential-form point.

### F-11 `gram:janai-dewa-nai` (n5) 5/5 examples skip the basic pattern

The record teaches noun/な-adj + じゃない (学生じゃない). All five carriers are idiomatic derivatives:
`中休みしようじゃないか。` (volitional + じゃないか) / `雨になっちゃうんじゃないかなあ。` /
`おいそれと金はできるものじゃない。` / `ウスターソースがいいんじゃない？` / `いい人みたいじゃないか。`
An N5 learner never sees 学生じゃない / 先生じゃない. **Fix:** attach the basic-pattern examples (the sibling
record `gram:gp-33` already has them: `あの人は先生じゃない`, `これはわたしのかばんじゃない`), which is
another argument for merging the two (F-28).

### F-12 `gram:n3-da-mono-da` 4/4 examples show 〜たものだ, not だもの

The record teaches the whiny reason marker ("é que...", "afinal..."). All four carriers are past-habitual or
nominal ものだ: `人々は彼女が死んだものだと思った。` / `私はここで毎日泳いだものだ。` (used to swim) /
`私たちはよく映画に行って楽しんだものだ。` / `彼らは死んだものだとあきらめた。` The key looks to have been
assigned by surface string match on 〜んだものだ. **Fix:** retag all four to a past-habitual ものだ point;
`sent:tatoeba-10107238` 私はあんたのお姉ちゃんだもん (currently on `n3-nda-mon`) is the only correct example
in the bank for this point.

### F-13 `gram:gp-128` (n4, ように purpose/wish) 4/5 examples show other senses

Record covers only (1) purpose and (2) wish/prayer. Carriers: `またいつか風のように走るんだ。` (simile ように,
a sense the record does not cover) / `面白いように思います。` (〜ように思う) / `無理をしないように。` (correct) /
`母は私に外出しないようにいった。` (that is `gp-124` 〜ように言う) / `父はついてくるように私をせきたてた。`
(indirect command). Nothing illustrates the 〜ますように prayer branch that the record's own
`formation_steps` encodes (`治りますように`). **Fix:** move the simile ones to `gram:you-ni-you-na`, the
言う ones to `gram:gp-124`, and attach 風邪が早く治りますように / 忘れないように / 聞こえるように.

### F-14 `gram:n3-donna-ni-koto-ka` 3/3 examples lack ことか

The pattern is どんなに〜**ことか**. Carriers: `これが自動化されたらどんなにいいか。` (どんなに…か, no ことか) /
`どんなに愛してるか、分かってる？` (embedded question, and it *is* a real question, contradicting the
record's "não é uma pergunta de verdade") / `彼はどんなに苦しんだことだろう。` (ことだろう). **Fix:** attach or
generate どんなに疲れたことか / どんなに心配したことか, or widen the record to どんなに〜ことか・ことだろう
and say so in `formation`.

### F-15 `gram:ni-mieru` (n4) 3/5 examples show a different construction

Record: [noun/な-adj]に見える, [い-adj]く見える. Carriers: `動物はでたらめに動くように見える。` and
`学がないように見えるね。` are clause + ように見える; `人生には目に見える以上のものがある。` is literal
"visible to the eye". Only `そんなことしたらばかに見えるよ。` and `私にはどれも同じに見えるけど。` fit.
No example shows the い-adjective く見える branch, which is the record's own stated trap ("O brasileiro tende
a colocar に depois de adjetivo-い"). **Fix:** attach 若く見える / 高く見える / 元気に見える.

### F-16 `gram:n3-moshimo-nara` 3/5 examples have no もしも

The record's `steps_unavailable` argues, correctly, that emitting the bare なら tail "would ... label the
generic なら conditional as this point". Its example set does exactly that: `あなたなら、どうする？` /
`あなたなら、これをどう考えますか。` / `あなたなら、どうしますか？` contain no もしも. Only
`もしも私が生まれ変わるなら、鳥になりたい。` is a real instance. **Fix:** retag the three あなたなら sentences
to `gram:nara` and generate もしも examples.

### F-17 `gram:n3-to-iu-to` 2/2 examples are a different fixed idiom

Both carriers are どちらかというと ("if anything / relatively speaking"), a frozen expression, not the
"speaking of X" topic use the record teaches: `彼は、どちらかというと、分別のある人だ。` and
`私の好みはどちらかというと牛肉ですね。` **Fix:** attach 日本料理というと寿司 / 京都というとお寺 type
examples; keep どちらかというと as a separate lexical entry.

### F-18 `gram:n3-sono-kekka` 2/3 examples use 結果 as a plain noun

`その結果はどうなのか。` and `その結果はどうなったのか。` are 結果 + は ("as for the result"), not the
sentence-initial connective その結果、the record describes ("[situação 1]。その結果、[resultado]").
Only `その結果何が起こったのか。` is close. **Fix:** attach two-sentence examples that show the connective.

### F-19 `gram:ni-suru` (n5) 2/7 examples show XをYにする, not "decide on"

Record teaches choice/decision (コーヒーにします). `パンダはささをえさにする。` ("Os pandas se alimentam de
bambu-anão") and `テレビをつけっぱなしにするな！` are the three-place "make X into Y" use, which the
`formation` field never introduces. A learner reading "decidir-se por / escolher" and seeing the panda
sentence gets no usable signal. **Fix:** retag those two, or add the XをYにする sense to `formation` and
`forms`.

### F-20 Four single mis-tagged carriers

| point | sentence | why it does not belong |
|---|---|---|
| `gram:gp-139` (〜てはいけません, prohibition) | `sent:tatoeba-173416` 行かなくてはいけません。("Tenho que ir") | this is 〜なくてはいけない, obligation, the mirror point `gram:nakute-wa-ikenai`; it is the record's own "não confunda" trap sitting in its example list |
| `gram:tara-dou` (suggestion 〜たらどう？) | `sent:tatoeba-81125` 万一病気になったらどうする？ | a genuine question "what would you do if", not the fixed suggestion |
| `gram:kitto` | `sent:tatoeba-226013` きっと手紙くださいね。("Não deixe de me escrever") | this is the "sem falta" reading the record's own nuance assigns to 必ず, not to きっと |
| `gram:n3-you-ni-natta` | `sent:tatoeba-180353` 教育のおかげで私は今日のようになった。 | 〜のように + なる (simile), not the ようになった "came to be able to" pattern |

---

## Severity 3: learner-facing text integrity

### F-21 `gram:yotei-da` (n4) pt-BR formation is truncated; three rules exist only in English

- `formation.pt-BR` (87 chars): "Verbo na forma de dicionário (presente/futuro) + 予定だ／予定です: 行く予定です (tenho planos de ir)."
- `formation.en` (313 chars): same, **plus** "It also appears with noun + の: 会議は3時の予定です... For the past
  or cancellation, 予定だった is used... Negative: 行かない予定です ... or, more commonly, 行く予定はありません."

pt-BR is the learner locale; the Brazilian student gets strictly less than the English reader, and loses the
noun+の form, the past, and both negatives. This is the only ratio outlier of its kind in the slice (0.28;
next worst is F-02's 0.52).

**Fix:** translate the three missing sentences into `formation.pt-BR`.

### F-22 Parenthesis spans that swallow whole sentences (7 records)

An open parenthesis mid-sentence closes several sentences later, after a full stop. The shape is consistent
with an automated em-dash removal pass (project style forbids `—`) that substituted parentheses without
re-punctuating. Learner-facing prose in both locales.

| record | field | current text (excerpt) |
|---|---|---|
| `gram:gp-116` | nuance.pt-BR | "...significa "mas" de oposição **(**é um conector ... traduzir sempre por "mas" engana. É uma das ferramentas ... んですが é polido e んだけど é casual**)** não misture os dois na mesma fala." |
| `gram:gp-120` | nuance.pt-BR | "...no verbo **(**você ainda precisa de 〜たら/〜ば/〜なら/〜と no final da oração. Pense em もし ... de lusófonos.**)**" |
| `gram:gp-132` | nuance.pt-BR | "...e expositiva **(**soa mais impessoal ... não o objeto.**)**" |
| `gram:mitai-da` | nuance.pt-BR | "...não é o verbo 見たい ("querer ver") **(**a みたい de comparação ... "tipo" ou "feito".**)**" |
| `gram:gp-142` | nuance.pt-BR | "...soa mais natural e suave **(**útil para falar de mudanças de tempo, idade, profissão e estados**.)**" |
| `gram:gp-22` | nuance.en | "...is not an i-adjective **(**it's a na-adjective, so it doesn't conjugate like さむい/たかい. This confuses many beginners.**)**" |
| `gram:gp-48` | nuance.en | "...you can't say 'I ate nothing' **(**it has to be 'I didn't eat anything.' And here the double negative ... is usually dropped.**)**" |
| `gram:te-iru` | nuance.en | "...the particle before the verb stays を/が **(**it doesn't change because of ている.**)**" |

`gp-116.pt-BR` is the worst: the closing paren is followed by "não misture os dois na mesma fala" with no
punctuation at all. **Fix:** re-punctuate each with commas or semicolons and delete the stray parentheses;
`gp-116.en` shows the correct shape for its pt-BR counterpart.

### F-23 Missing diacritics in pt-BR (6 n3 records)

| record | field | current | should be |
|---|---|---|---|
| `gram:n3-mo` | formation | "(estes **ultimos** podem levar である)" | últimos |
| `gram:n3-mo` | nuance | "**Sinonimos proximos** com pequenas diferenças" / "a tradução 'não **so**... como também'" | Sinônimos próximos / não só |
| `gram:n3-to-iu` | formation | "para reportar **conteudo** ou reputação" | conteúdo |
| `gram:n3-to-iu` | nuance | "Quando o **conteudo e** algo ouvido"; "**ja** para simplesmente nomear" | conteúdo é / já |
| `gram:n3-to-iu-to` | nuance | "といえば **e** quase intercambiável"; "a associação **espontanea**" | é / espontânea |
| `gram:n3-tokoro-datta` | nuance | "estava na **iminencia**. **So** o ところだった"; "que **e** situação real" | iminência. Só / é |
| `gram:n3-toori` | nuance | "'conforme a regra' **e** 規則どおり"; "quando a instrução **ja** foi dada" | é / já |
| `gram:n3-no` | nuance | "**Atenção a ordem**"; "o **possuido** depois" | Atenção à ordem / possuído |

### F-24 `gram:kata` (n5) formation mixes full-width open with ASCII close

`formation.pt-BR` and `.en`: `食べ方（たべかた, jeito de comer)` ; `使い方（つかいかた, modo de usar)` ;
`書き方（かきかた, como escrever)`. Three parentheses open with `（` (U+FF08) and close with `)` (U+0029).
Renders inconsistently and trips any paren-balance validator. **Fix:** close with `）`.

### F-25 `gram:sore-ni` (n4) generated examples use a bare space where the record's own formation prescribes `。` and `、`

`formation` says: "Frase 1**。**それに**、**Frase 2." All four generated carriers instead separate the clauses
with an ASCII space: `彼は親切です それに頭もいいです`, `この店は安いです それに料理もおいしいです`,
`この部屋は広いです それに明るいです`, `今日は寒いです それに雨も降っています`. A space is not valid
Japanese sentence separation, and the style rule in `design/translation_style.md` §3 only bans the
*sentence-final* 。 in generated JP, so the clause-internal 。 and the 、 after それに are both permitted.
**Fix:** regenerate as `彼は親切です。それに、頭もいいです` (no trailing 。).

---

## Severity 4: missing data, duplication, graph integrity

### F-26 34 of 124 records have a `forms[]` entry with no meaning in either locale

`forms[0].meaning` is `{}`: no `pt-BR`, no `en`. Affected: `gp-98` plus every n3 record in the slice
(`n3-ba-yokatta`, `n3-da-mono-da`, `n3-donna-ni-koto-ka`, `n3-hodo`, `n3-kara-ni-kakete`, `n3-kiri`,
`n3-koto-da`, `n3-koto-wa-nai`, `n3-made`, `n3-mattaku-nai`, `n3-mo`, `n3-moshimo-nara`, `n3-nai-to`,
`n3-nda-mon`, `n3-ni-oite`, `n3-ni-totte`, `n3-no`, `n3-rareta`, `n3-saichuu-ni`, `n3-sono-kekka`,
`n3-sore-tomo`, `n3-tabi-ni`, `n3-te-hajimete`, `n3-te-miru`, `n3-to-iu`, `n3-to-iu-to`,
`n3-tokoro-datta`, `n3-toori`, `n3-uchi-ni`, `n3-wake-dewa-nai`, `n3-you-ni`, `n3-you-ni-natta`,
`n3-zu-ni`). Corpus-wide the count is 133. Any UI that renders the form list shows an empty gloss.
**Fix:** the `label` field of each record already contains the gloss and can seed the repair
(`n3-hodo` label "tanto quanto / na medida de" → form meaning).

### F-27 Sentence coverage gaps

Zero carriers: `gram:n3-kara-ni-kakete`, `gram:n3-kiri`, `gram:n3-koto-da`, `gram:n3-mattaku-nai`.
One or two carriers: `n3-nda-mon` (1), `n3-ni-oite` (1), `n3-uchi-ni` (1), `n3-mo` (2), `n3-nai-to` (2),
`n3-no` (2), `n3-to-iu-to` (2). `n3-no` covers の, one of the highest-frequency particles in the language,
with two sentences, both of which are the 〜のこと idiom.

### F-28 Four duplicate record pairs, both halves inside this slice

| pair | level | evidence |
|---|---|---|
| `gram:gp-151` / `gram:te-shimau-chau` | n4 / n4 | same point, near-identical explanations (both use 宿題をしてしまった and 財布をなくしてしまった as the two examples); 3 bank sentences carry BOTH keys |
| `gram:gp-33` / `gram:janai-dewa-nai` | n5 / n5 | "não é / não está (じゃない)" vs "não é (じゃない・ではない)"; disjoint example sets (see F-11) |
| `gram:gp-112` / `gram:itashimasu` | n4 / n4 | "いたす, fazer (humilde de する)" vs "いたします (forma humilde de する)" |
| `gram:n3-da-mono-da` / `gram:n3-nda-mon` | n3 / n3 | same point, and they contradict each other (F-04) |

`related` is `[]` on all eight, so nothing links them. `gram:gp-100`'s own `steps_unavailable` text already
names a fifth pair ("The duplicate record gram:gp-118 is steps_unavailable on the same argument").

### F-29 Five records for ように, with contradictory step decisions

`gram:gp-128`, `gram:you-ni-you-na` (both n4, both in this slice), `gram:n3-you-ni` (this slice),
`gram:n3-you-ni-2`, `gram:n3-you-ni-3`. The two n4 records disagree on the same rule:

- `gp-128.steps_unavailable`: refuses to encode dictionary-form + ように because "a to-dictionary rule would
  emit 書くように / 勉強するように as instances of this point, **which the record forbids**".
- `you-ni-you-na` encodes it anyway: `base=verb | to-dictionary > append[ように] | example=分かるように`.
- `n3-you-ni` encodes it too: `example=見えるように`.

Both encodings are safe only because their chosen examples happen to be non-volitional. A generator applying
the step to 書く / 勉強する produces exactly what `gp-128` says is wrong. **Fix:** consolidate to one ように
record with explicitly separated purpose / wish / simile branches, and settle the dictionary-form question
once.

### F-30 Seven grammar points registered at two different levels

| point | n5/n4 record | n3 record | in this slice |
|---|---|---|---|
| まで | `gram:made` n5, conf 1.0 | `gram:n3-made` n3, conf 0.34 | n3-made |
| ている | `gram:te-iru` n5, conf 1.0 | `gram:n3-te-iru` n3, conf 0.34 | te-iru |
| の | `gram:no` n5, conf 1.0 | `gram:n3-no` n3, conf 0.34 | n3-no |
| という | `gram:to-iu` n4, conf 1.0 | `gram:n3-to-iu` n3, conf 0.34 | n3-to-iu |
| てみる | `gram:te-miru` n4, conf 1.0 | `gram:n3-te-miru` n3, conf 0.34 | n3-te-miru |
| ないと | `gram:gp-117` n4, conf 1.0 | `gram:n3-nai-to` n3, conf 0.34 | n3-nai-to |
| ばよかった | `gram:gp-138` n4, conf 1.0 | `gram:n3-ba-yokatta` n3, conf 0.34 | n3-ba-yokatta |

I compared the explanations pairwise: these are the same point taught twice, not two senses. (I checked and
excluded `gram:ta-tokoro` / `gram:n3-ta-tokoro`, which genuinely split "acabar de fazer" from the たところ
discovery sense, and are correctly separate.) Left as is, the courseware will introduce まで, ている and の
a second time at N3. **Fix:** merge each pair into the lower-level record, or demote the n3 duplicate to an
`also_known_as` / advanced-sense note.

### F-31 `related[]` is empty on all 124 records, while the prose promises cross-references

Corpus-wide only 4 of 496 records have a non-empty `related`. The prose relies on links that do not exist:

- `gram:naide-kudasai` formation: "É a mesma base 〜ないで **do item anterior**, agora seguida de ください."
- `gram:nakute-wa-ikenai` formation: "〜なくては costuma virar 〜なくちゃ (**veja o item anterior**)."
- `gram:gp-58` nuance: "Diferencia-se de どんどん ... (**ver próximo ponto**)."

In a registry addressed by stable ID with no guaranteed ordering (CLAUDE.md §1.7), "o item anterior" resolves
to nothing. Dozens more records name a sibling in prose (`gram:aida` → 間に, `gram:dasu` → 〜始める,
`gram:ni-suru` → 〜になる, `gram:gp-51` → 〜たほうがいい) without a machine-readable link.
**Fix:** replace the relative references with slugs and populate `related`.

### F-32 `gram:n3-zu-ni` formation_steps is an admitted authoring gap

`steps_unavailable`: "**NOT AUTHORED**: the roadmap-E campaign covered 495 of the 496 registered points
(33 batches of 15) and this one fell outside every batch range. This is a coverage gap, not a judgement that
the record is too vague to state." The rule is simple and encodable (`verb:to-nai-stem > replace-ending`
→ 飲まずに, with the する → せずに exception the record already documents).

### F-33 `gram:n3-mo` key names the wrong particle

`key`/`slug` = `n3-mo` / `gram:n3-mo`, but the point is ばかりか〜も (`structure_pattern: ～ばかりか～も`,
label "não só... como também"). The key is the graph address; `n3-mo` reads as the particle も and collides
conceptually with a real も entry. **Fix:** rename to `n3-bakari-ka` (with a slug alias if anything already
references the old id).

---

## Checked and clean

Points I read in full and found no defensible defect in: `darou`, `donna`, `ga-arimasu`, `gp-10`, `gp-15`,
`gp-19`, `gp-22`, `gp-26`, `gp-3`, `gp-33`, `gp-37`, `gp-40`, `gp-44`, `gp-48`, `gp-51`, `gp-55`, `gp-7`,
`kata` (content), `mada-te-imasen`, `mashou`, `na`, `naide-kudasai`, `nakute-wa-ikenai`, `ne`, `no-ga-suki`,
`o-kudasai`, `soshite`, `tari-tari`, `te-iru` (content), `temo-ii-desu`, `tsumori`, `wa-yori-desu`, `aida`,
`ba`, `dasu`, `ga-suru`, `gp-100`, `gp-104`, `gp-108`, `gp-112` (content), `gp-116` (content), `gp-120`
(content), `gp-124`, `gp-136`, `gp-147`, `gp-151` (content), `gp-58`, `gp-66`, `gp-70`, `gp-74`, `gp-78`,
`gp-82`, `gp-86`, `gp-90`, `gp-94`, `hazu-ga-nai`, `kai`, `koto-ga-dekiru`, `kyuu-ni`, `mitai-da` (content),
`nagara`, `nara`, `nowa-da`, `sakki`, `ta-tokoro`, `te-iku`, `te-kuru`, `teiru-tokoro`, `to-iu-koto`,
`zurai`, `n3-hodo`, `n3-kara-ni-kakete`, `n3-kiri`, `n3-koto-da`, `n3-made`, `n3-mattaku-nai`,
`n3-ni-oite`, `n3-ni-totte`, `n3-rareta`, `n3-saichuu-ni`, `n3-sore-tomo`, `n3-tabi-ni`, `n3-te-hajimete`,
`n3-te-miru`, `n3-toori`, `n3-uchi-ni`, `n3-wake-dewa-nai`, `n3-you-ni-natta`, `n3-zu-ni` (content).

Two things I looked at hard and decided **not** to flag, for the record:
- `gram:gp-82` formation calls 〜とよかった the past of 〜といい ("expressa arrependimento"). 〜ばよかった /
  〜たらよかった are the standard regret forms and 〜とよかった is marginal, but I could not establish it as
  outright wrong, so it stays unflagged. A native reviewer may want to look.
- `gram:ba` nuance adds "com o mesmo sujeito" to the restriction on ば before commands/requests. This is a
  narrower formulation than the usual textbook rule but appears in several Japanese-language references, and
  the record's practical rule underneath it is correct.

---

## Counts

| Class | Records checked | Records flagged | Findings |
|---|---|---|---|
| S1 Formation / factual error in the taught rule | 124 | 6 | 5 |
| S2 Example set contradicts the point (cross-check) | 124 | 18 | 15 |
| S3 Learner-facing text integrity (locale, punctuation, diacritics) | 124 | 17 | 5 |
| S4 Missing data, duplication, graph integrity | 124 | 43 | 8 |
| **Total** | **124** | **64 distinct records** | **33** |

Class totals overlap (a record can appear in more than one class); the total row is the deduplicated union.
F-31 (empty `related[]`) is excluded from the S4 count because it holds for all 124 records and would
otherwise swamp the table.

| Sub-count | Value |
|---|---|
| Records in slice | 124 (n5 37, n4 54, n3 33) |
| formation_steps variants traced by hand | 250 across 89 records (35 records are `steps_unavailable`) |
| formation_steps variants emitting a wrong surface form | **0** |
| `to-nai-stem` uses audited corpus-wide for op-semantics consistency | 496 records, 0 contradictions |
| Bank sentences cross-checked | 662 carriers across the 124 keys |
| Points whose entire example set contradicts the record | 8 (`owaru`, `gp-62`, `gp-98`, `gp-132`, `n3-koto-wa-nai`, `n3-da-mono-da`, `n3-donna-ni-koto-ka`, `n3-to-iu-to`) |
| Points with zero example sentences | 4 |
| `forms[].meaning` empty in both locales | 34 of 124 (133 corpus-wide) |
| Records with empty `related[]` | 124 of 124 (492 of 496 corpus-wide) |
| Duplicate pairs with both halves in this slice | 4 |
| Points registered at two levels | 7 |
