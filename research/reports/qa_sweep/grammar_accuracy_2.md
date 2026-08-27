# QA sweep — grammar accuracy, part 2/4

**Slice:** `corpus/grammar/*.json`, records at `index % 4 == 1` in concatenated **n5 + n4 + n3** order
(n5 = 151, n4 = 213, n3 = 132; total 496) → **124 records checked** (idx 1 … 493).

**What was checked, per record:** factual correctness of `explanation` (pt-BR + en); whether `formation` +
`formation_steps` actually produce the forms listed; whether those forms are correct Japanese for the point;
whether `nuance` contradicts `explanation`; whether `related` / `refs` / `families` are sensible; and a
cross-check of each point against the sentences that carry it (`sentence.grammar` arrays in
`corpus/sentences/bank.json`, 2–5 per point where available).

**Out of scope by instruction:** sentence `structure_explanation` fields (being re-authored elsewhere).
Nothing in this report touches them.

Severity key: **S1** = teaches learners to produce wrong Japanese · **S2** = factually wrong or
self-contradictory statement · **S3** = record identity / duplication · **S4** = the linked sentences do not
carry the point as described · **S5** = locale-parity or pt-BR text quality · **S6** = internal artifact
leaked into learner-facing text · **S7** = structural data gap.

---

## S1 — Formation rule produces wrong Japanese (highest severity)

### F01 — `gram:n3-nanka` (idx 417): formation licenses ×行くなんか / ×高いなんか

Current `formation.pt-BR`:

> "Anexa-se a substantivos (substantivo + なんか) e também a verbos e adjetivos na forma simples
> (informal): verbo-simples + なんか, adjetivo-い + なんか, adjetivo-な + なんか."

(en: "…and also to verbs and adjectives in plain (informal) form: plain-verb + なんか, い-adjective + なんか,
な-adjective + なんか.")

**Why it is wrong.** なんか does not attach to a plain-form verb or to the plain form of an い-adjective.
The particle that does that is **なんて** (行くなんて, 高いなんて) — which this record's own `nuance` tells the
learner to keep separate ("Não confunda com なんて"). With verbs, なんか attaches to the **て-form**
(びびってなんかない — which is one of this record's own linked sentences) or to the ます-stem before する
(行きなんかしない); with い-adjectives it attaches to the **adverbial く** form (高くなんかない). A learner
following the rule as written produces ×行くなんか and ×高いなんか.

**Proposed fix.** Replace the verb/adjective clause with: "Com verbo, usa-se a forma て + なんか,
tipicamente com negativa: 行ってなんかいない ('não fui, nada disso'). Com adjetivo-い, usa-se a forma
adverbial く + なんか: 高くなんかない ('caro? nem um pouco'). Para prender なんか direto a verbo ou adjetivo na
forma simples, o japonês usa なんて, não なんか." Also add the third, very common use the record omits
entirely and which 2 of its 3 linked sentences show — なんか as a sentence-initial filler adverb
("sei lá, tipo"): `sent:tatoeba-12304974` なんかフラフラする, `sent:tatoeba-3367124` なんかおかしくない？.

---

### F02 — `gram:n3-you-ni-3` (idx 489): な-adjective rule produces 静かに, which is not ように at all

Current `formation.pt-BR`: "Verbo na forma comum + ように; adjetivo-い + ように; **adjetivo-な + に (não leva
だ aqui)**; substantivo + のように." The `nuance` repeats it: "Atenção ao adjetivo-な: ele se liga com に, não
com だ."

**Why it is wrong.** 静か + に = 静かに, which is simply the adverbial form of the な-adjective and has no
ように in it. The point being taught is ように. With a な-adjective the correct attachment is the attributive
な + ように (元気なように, 静かなように). The rule as written conflates two different things and, followed
literally, deletes the pattern the record exists to teach. Corroborating signal from inside the record:
`formation_steps` emits only `verb`, `i-adjective` and `noun` variants — the encoder declined to encode the
na-adjective line, but the prose was left standing.

**Proposed fix.** "adjetivo-な + な + ように (元気なように, 静かなように)" and add the matching
`formation_steps` variant `{base: "na-adjective", steps: [to-attributive, append "ように"], example:
"静かなように"}`. Delete the sentence "ele se liga com に, não com だ" from `nuance`.

---

### F03 — `gram:n3-kesshite-nai` (idx 385): formation restricts 決して to verb negatives; its own five sentences are all adjective/copula negatives

Current `formation.pt-BR`: "決して abre a frase e exige um **verbo** no negativo depois: 決して + **verbo na
forma negativa** (決して遅刻しない …; 決して言わない …). Também combina com pedidos negativos:
決して～ないでください."

**Why it is wrong.** 決して requires a negative **predicate**, of any kind. All five sentences the corpus
links to this very record use non-verbal negatives: `sent:tatoeba-107857` 彼は決して親切ではない (な-adj),
`sent:tatoeba-107882` 彼は決して学者ではない (noun + copula), `sent:tatoeba-127122` 値段は決して高くない
(い-adj), `sent:tatoeba-157343` 私は決して頭が良くない (い-adj), `sent:tatoeba-205235` それは決して大きくない
(い-adj). Zero of five match the stated rule. A learner reading the record concludes 決して高くない is
ungrammatical.

**Proposed fix.** "決して abre a frase e exige um **predicado** no negativo: verbo-ない (決して言わない),
adjetivo-い → 〜くない (決して高くない), adjetivo-な / substantivo → 〜ではない (決して親切ではない,
決して学者ではない). Também combina com pedidos negativos: 決して〜ないでください."

---

### F04 — `gram:n3-ba-hodo` (idx 365): the な-adjective rule as written yields ×静かであれば静かほど

Current `formation.pt-BR`: "Com adjetivo-na: **であれば + な-adjetivo + ほど**, ou o padrão であればあるほど."

**Why it is a problem.** Everywhere else in this corpus "adjetivo-na" denotes the bare stem (e.g. `gram:naru`
"adjetivo-な + に + なる (静か → 静かになる)"; `gram:mama` spells the な out explicitly as "adjetivo-な + な").
Read the same way here, the rule composes 静かであれば + 静か + ほど = ×静かであれば静かほど. The correct shapes
are 静かであれば静かなほど or, far more common in speech, 静かなら静かなほど. The template であればあるほど is a
different, fixed frame (it repeats ある, not the adjective) and is presented as if interchangeable.

**Proposed fix.** "Com adjetivo-な: なら + な-adjetivo + な + ほど (静かなら静かなほど) — ou, em registro mais
escrito, であれば + な-adjetivo + な + ほど (静かであれば静かなほど). Existe ainda o molde fixo
〜であればあるほど, em que o que se repete é ある, não o adjetivo."

---

### F05 — `gram:n3-ni-shitemo` (idx 425): the な-adjective line is unresolvable, and the record knows it

`formation.pt-BR` reads only "adjetivo-な + にしても", with no statement of whether the な is kept. The
record's own `steps_unavailable` documents the consequence in full: "*both literal readings fail the
substitution test on 静か. Keeping the attributive な yields \*静かなにしても, ungrammatical. Dropping it
yields 静かにしても, a string that parses as the て-form of 静かにする plus も*". The encoder therefore withheld
the na-adjective variant — but the ambiguous prose is still what the learner reads, and it is the only place
the rule appears.

**Proposed fix.** Match the sibling record `gram:n3-ni-shite-wa`, which states it explicitly: "adjetivo-な
**sem o な** + にしても (静かにしても); quando houver risco de confusão com 静かにする, prefira a variante
だとしても (静かだとしても)."

---

### F06 — `gram:yatto` (idx 353): the pt-BR `formation` is truncated — the base rule is missing

Current `formation.pt-BR`, in full:

> "Também acompanha o presente para algo que dá só na medida: やっと間に合う (やっとまにあう) = 'chego bem em
> cima da hora'."

Current `formation.en`, in full:

> "It is an invariable adverb: you just place it before the verb or the clause, usually at the start or near
> the verb. やっと + clause, generally with the verb in the past (〜た) for something already achieved:
> やっと家に着いた … It also accompanies the present for something that just barely makes it: やっと間に合う …"

**Why it is wrong.** The pt-BR field opens with "Também" ("Also") and never states what it is adding to. The
entire base rule — invariable adverb, pre-posed, normally with a 〜た predicate — exists only in `en`. pt-BR is
the learner-facing locale, so the formation section for this point is effectively empty. The record's
`steps_unavailable` already flags it ("*The record's formation field is also incomplete — it opens with
'Também acompanha o presente…' and never states the base rule it is adding to*"), so this is a known,
unrepaired defect. Field-length ratio pt/en = 0.29, the worst in the slice.

**Proposed fix.** Restore the two missing sentences in pt-BR, mirroring `en`: "É um advérbio invariável:
basta colocá-lo antes do verbo ou da oração, em geral no começo da frase ou junto ao verbo. やっと + oração,
normalmente com o verbo no passado (〜た) para algo já conseguido: やっと家に着いた ('finalmente cheguei em
casa'). Também acompanha o presente …"

---

## S2 — Factually wrong or self-contradictory statements

### F07 — `gram:douyatte` (idx 9): やって is not the て-form of する

`formation.pt-BR`: "Literalmente é どう (como) + やって (**forma て de やる/する**, 'fazendo')."
(en: "…やって (the て-form of やる/する, 'doing')".)

する's て-form is **して**, never やって. やって is the て-form of やる only. **Fix:** "…+ やって (forma て de
やる, 'fazendo')" — drop `/する`.

### F08 — `gram:gp-126` (idx 193): the loanword ban is false, and the record's own sentence breaks it

`nuance.pt-BR`: "…não se diz 化する com palavras casuais ou **empréstimos do dia a dia** (para esses usa-se
〜になる/〜にする)."

化する combines freely with katakana loanwords: データ化, デジタル化, グローバル化, システム化, ブラック化 are
all ordinary Japanese. The corpus's own linked sentence for this record is `sent:gen-0b2679ac5ee0`
古い書類を**データ化**しています — a loanword, exactly the case the nuance calls impossible. **Fix:** replace with
"化する pede um substantivo que nomeie uma qualidade ou um estado; kango (機械化, 国際化) e empréstimos
estabelecidos (データ化, デジタル化) funcionam bem, mas não se usa com nomes concretos avulsos
(×コップ化)."

### F09 — `gram:gp-114` (idx 181): "たとえば almost always opens the sentence" is contradicted by the record's own Layer-A sentences

`nuance.pt-BR`: "…o japonês **quase sempre** coloca たとえば no começo da frase, antes do exemplo, e **não no
meio** como às vezes fazemos em português."

Two of the five sentences linked to this record are real Tatoeba sentences with たとえば mid-sentence:
`sent:tatoeba-157990` 私は花が好きで、**たとえば**ばらが好きだ and `sent:tatoeba-184830`
外国、**たとえば**アメリカへ行ったことがありますか。 The appositive 「X、たとえばY」 is a standard, very common
placement. **Fix:** "たとえば costuma abrir a frase do exemplo, mas também aparece encaixado logo depois do
termo geral, entre vírgulas: 外国、たとえばアメリカ… ('países estrangeiros, por exemplo os Estados Unidos')."

### F10 — `gram:gp-138` (idx 205): なければ is called a particle

`nuance.pt-BR`: "…são opostos (não confunda **a partícula** なければ.)" / en: "…don't confuse the なければ
**particle**."

なければ is the negative conditional form of a verb (〜ない → 〜なければ), not a particle. In a grammar
reference this mislabels the one item the sentence is about. **Fix:** "…são opostos: a diferença está na
negativa なければ, que inverte o sentido do arrependimento." (This also repairs the stray closing parenthesis;
see F27.)

### F11 — `gram:n3-ni-kawatte` (idx 421): the nuance warns against confusing the point with itself

`nuance.pt-BR`: "Não confunda também com **にかわって (substituir alguém)** e にかわり no sentido de
revezamento." (en identical in structure.)

にかわって "to substitute for someone" **is** this record's own point. The sentence instructs the learner not
to confuse 〜にかわって with 〜にかわって. The intended contrast was almost certainly with the homophonous
に**変**わって ("to change into"), which the preceding sentence already covers. **Fix:** delete the clause, or
rewrite as "Não confunda também com にかわり, que em alguns contextos indica revezamento/alternância em vez de
substituição."

### F12 — `gram:ga-imasu` (idx 13): "robots normally take あります" contradicts the record's own criterion

`explanation.pt-BR` defines the います class as "seres vivos **com vontade própria**"; `nuance.pt-BR` then
says "plantas e **robôs** normalmente vão com あります."

Plants → ある is correct. Robots are the standard counter-example in the other direction: ロボットがいる is
normal Japanese precisely because a robot moves and acts under its own apparent volition, which is the
criterion the record itself states two paragraphs earlier. Asserting あります for robots teaches a rule the
record has already contradicted. **Fix:** "plantas vão com あります; para robôs e personagens que se movem
sozinhos, o japonês real costuma usar います, justamente pelo critério da vontade própria."

### F13 — `gram:gp-24` (idx 37): the stated rule and its illustration are about different things

`nuance.pt-BR`: "Outro reflexo a evitar: **não coloque です antes do negativo** (高くないです está certo, mas
高いじゃない está errado)."

Neither example contains です before a negative. The correct example (高くないです) has です *after* the
negative; the wrong example (高いじゃない) has no です at all — its error is negating an い-adjective with
じゃない. The rule as stated is a non sequitur that a learner cannot map onto either example. **Fix:** "Outro
reflexo a evitar: negar um adjetivo-い com じゃない (×高いじゃない). O です entra depois do negativo, nunca
antes: 高くないです, nunca ×高いですない."

---

## S3 — Record identity and duplication

### F14 — `gram:n3-ppai` (idx 433): the key names 〜っぽい, the content is 〜でいっぱい, and 〜っぽい is absent from the whole corpus

`key`/`slug` = `n3-ppai` / `gram:n3-ppai`. `structure_pattern` = `～でいっぱい`. `label.en` = "full of / packed
with (〜でいっぱい)". `explanation` even glosses the reading: "A leitura é 'ippai'".

`ppai` is the romanisation of **っぽい** ("-ish, tends to", 子供っぽい / 忘れっぽい / 白っぽい), a core N3 point.
A grep over all three grammar files finds **zero** occurrences of っぽい anywhere: no record covers it. The
most likely history is that a source-list entry 〜っぽい was authored as 〜でいっぱい, leaving both a
misidentified record and a coverage hole.

Compounding it, **both** sentences linked to this record lack the で the pattern requires:
`sent:tatoeba-11924443` 車がいっぱいでした and `sent:tatoeba-449155` こっちはいっぱいです — the bare adverb/
predicate いっぱい that this record's own nuance says to keep apart from 〜でいっぱい.

**Proposed fix.** Rename the record's key/slug to something that matches its content (`n3-de-ippai`), and
open a separate gap item for the missing 〜っぽい point. Retag or replace the two sentences.

### F15 — Duplicate grammar points, several at the same level, none cross-linked

Detected by normalising `structure_pattern` and `label.en` across all 496 records. Slice members first:

| in slice | duplicate of | level(s) | pattern |
|---|---|---|---|
| `gp-53` (idx 69) **and** `no-ga-heta` (idx 117) | each other — **both in this slice** | n5 / n5 | 〜のがへた(です) / 〜のが下手 |
| `gp-60` (idx 217) | `tara` | n4 / **n4** | 〜たら |
| `gp-64` (idx 221) | `tadoushi-jidoushi` | n4 / **n4** | 他動詞・自動詞 |
| `no-naka-de` (idx 297) | `gp-97` | n4 / **n4** | の中で / のなかで |
| `naru` (idx 109) | `gp-142` | n5 / **n5** | なる / 〜になる |
| `n3-metta-ni-nai-2` (idx 405) | `n3-metta-ni-nai` | n3 / **n3** | めったに〜ない |
| `n3-you-ni-3` (idx 489) | `n3-you-ni`, `n3-you-ni-2`, `gp-128` | n3 ×3 + n4 | 〜ように — **four records** |
| `gp-76` (idx 233) **and** `mitai-ni` (idx 285) | each other — **both in this slice** | n4 / n4 | みたいに・みたいな |
| `n3-sa` (idx 437) | `sa` | **n3 vs n4** | 〜さ |
| `n3-te-iru` (idx 457) | `te-iru` | **n3 vs n5** | 〜ている |
| `n3-nado` (idx 413) | `nado` | **n3 vs n4** | 〜など |
| `n3-mama`* | `mama` (idx 281) | **n3 vs n4** | まま |
| `n3-kanaa` (idx 381) | `kana` (idx 269), which already documents かなあ as its own variant | **n3 vs n4** | かな / かなあ |
| `n3-koto-ni-shite-iru` (idx 393) | `koto-ni-suru` (idx 277), whose `formation_steps` already emit `走ることにしている` | **n3 vs n4** | ことにしている |
| `gp-118` (idx 185) | `n3-shika-nai` | n4 / n3 | しか〜ない |
| `gp-138` (idx 205) | `n3-ba-yokatta` | n4 / n3 | ばよかった |
| `bakari` (idx 157) | `n3-bakari` | n4 / n3 | ばかり |
| `rashii` (idx 305) | `n3-rashii` | n4 / n3 | らしい |
| `koto` (idx 273) | `n3-koto` | n4 / n3 | こと |

\* `n3-mama` is not itself in this slice; listed because its twin `mama` is.

The same-level pairs are straight duplicates. The cross-level pairs are worse for the courseware layer:
`sa`/`n3-sa`, `te-iru`/`n3-te-iru`, `nado`/`n3-nado`, `kana`/`n3-kanaa` assign one point two different
`level` values with two different `level_confidence` values (1.0 vs 0.34) from two different source sets, so
any sequencing pass reading `level` gets contradictory answers, and the same construction is scheduled twice.

**Proposed fix.** Merge each pair/cluster into one record, keeping the higher-confidence level tag, and
migrate the losing record's `sentence.grammar` tags onto the survivor. Where the split is deliberate (e.g.
if `ta-tokoro` "just did" vs `n3-ta-tokoro` "upon doing" is meant to stay), say so in `related` rather than
leaving it implicit — see F16.

### F16 — `related` is empty for all 124 records in the slice (and 492 of 496 corpus-wide) — *slice-wide*

Only 4 records in the entire grammar corpus have a non-empty `related`: `de`, `ga`, `ni`, `wa-topic-marker`.
Every record in this slice has `related: []`, including pairs the prose explicitly contrasts and that the
project's own §1.7 requires to be reachable by stable ID:

- `gp-53` ↔ `no-ga-heta` (same point, no link)
- `naku-temo-ii` (idx 105) nuance contrasts 〜なくてはいけない — no link
- `gp-72` (idx 229) explanation names the three-member ところ family — no links to `ta-tokoro` / `n3-ta-tokoro`
- `te-ageru` (idx 325) ↔ `te-morau` (idx 333) ↔ `te-yaru` (idx 337) — the giving/receiving family, all three in this slice, mutually unlinked
- `gp-153` (idx 213) contrasts のような with のように — no link
- `n3-metta-ni-nai-2` (idx 405) nuance contrasts あまり〜ない (`amari-nai`, idx 153) — no link

The cross-referenceable graph the spec calls for cannot be built for grammar from the current data.

### F17 — `gram:te-ageru` (idx 325) and `gram:te-yaru` (idx 337) share an identical `label.en`

Both read `"do something for someone"`. They are distinct points with opposite register implications
(〜てあげる neutral/outward, 〜てやる casual-to-inferior with a possible threatening tone, `caution: rough`).
In any index or picker rendered from `label.en` they are indistinguishable. **Fix:** differentiate, e.g.
`te-ageru` → "do something for someone (〜てあげる)" and `te-yaru` → "do something for someone below you
(〜てやる)". The pt-BR labels already differ correctly.

### F18 — `gram:garu-gatteiru` (idx 165) and `gram:tagaru` (idx 321) have identical machine-readable formations

`garu-gatteiru`'s `steps_unavailable` explains that the adjective bases were deliberately excluded, so the
only `formation_steps` it emits are `[verb → to-masu-stem → append たがる]` (ex. 食べたがる) and the same plus
ている. `tagaru` emits exactly the same two variants (ex. 行きたがる, 食べたがっている). Any generator or drill
builder reading `formation_steps` will produce the same exercises for both records, and nothing in the
machine-readable layer distinguishes the がる point (its adjective half) from the たがる point.
**Fix:** either merge, or move the たがる half out of `garu-gatteiru` entirely and leave that record to state
the adjective rule in prose with `steps_unavailable` covering it.

---

## S4 — Linked sentences do not carry the point as the record describes it

Cross-check method: for each record, pull every sentence whose `grammar` array contains the record's `key`,
and read the first five. The following are cases where a **majority** of the linked sentences illustrate a
construction the record explicitly excludes, so the sentence bank actively teaches against the record.

### F19 — `gram:n3-ta-tokoro` (idx 449): 6 of 6 sentences are 〜たところだ, the sense the record excludes

The record teaches 〜たところ = "upon doing X, discovered Y", and its `nuance` says: "*Cuidado para não
confundir com outros usos de ところ: ～ているところ … e **～たところだ (acabar de fazer)** têm sentidos
diferentes.*" Every linked sentence is 〜たところだ:

- `sent:tatoeba-172554` 今やっと始めたところです。— "Acabei de começar agora mesmo."
- `sent:tatoeba-179557` 銀行へ行ってきたところです。— "Acabei de ir ao banco."
- `sent:tatoeba-188870` 駅へ行って来たところだ。— "Acabei de ir até a estação."
- `sent:tatoeba-198112` バスは今出発したところだ。— "O ônibus acabou de sair agora."
- `sent:tatoeba-203585` たった今帰ったところだよ。— "Acabei de chegar em casa agora mesmo."

All five belong to the separate record `gram:ta-tokoro` (n4, "to have just done"). The point this record
actually teaches has **zero** example sentences. **Fix:** retag all six onto `ta-tokoro`, and source new
sentences of the discovery type (聞いたところ、〜だった／調べたところ、〜が分かった).

### F20 — `gram:n3-to-iu-no` (idx 465): 5 of 5 sentences are というのは / というのに, not というのだ

The record teaches というのだ ("the thing is that…", reporting a reason) and its `nuance` says: "*não confunda
com というのは (que define um termo)*". Every linked sentence is the excluded というのは, or a third pattern
(というのに):

- `sent:tatoeba-214502` スペシャル**というのは**どんな味ですか。
- `sent:tatoeba-220804` この川は何**というの**ですか。("what is it called")
- `sent:tatoeba-234151` あなたがやった**というのは**本当か。
- `sent:tatoeba-234789` ＵＮ**というのは**何を表わしていますか。
- `sent:tatoeba-138773` 朝の5時だ**というのに**明るい。(concessive というのに)

**Fix:** retag to the というのは record if one exists (create one otherwise), and source sentences ending in
というのだ／というのです.

### F21 — `gram:n3-dakedo` (idx 373): 5 of 5 sentences are the trailing softener けど, the use the nuance excludes

`nuance.pt-BR`: "*não confunda esse けど com a partícula que apenas suaviza um pedido …; aqui o sentido é
sempre de oposição real entre as duas partes.*" All five linked sentences are exactly that softener — a
dangling 〜んだけど with no second clause, and the pt translations all end in "…":

- `sent:tatoeba-171648` 今日は休めと言われたんだけど。— "É que me disseram para eu folgar hoje…"
- `sent:tatoeba-198643` ねえ、元気がないみたいだけど。— "Ei, você parece meio sem energia, hein…"
- `sent:tatoeba-3366905` 知ってたらよかったんだけど。— "Ah, se eu soubesse…"
- `sent:tatoeba-4900248` ちょっとよく知らないんだけど。— "É que eu não conheço muito bem isso…"
- `sent:tatoeba-8575497` 今日は歌いたくないんだけど。— "É que hoje eu não estou a fim de cantar…"

**Fix:** source contrastive examples (安いけど、おいしくない／難しいけど、楽しい), and either retag these five to a
softening-けど record or add that use to this record's `forms` and `explanation`.

### F22 — `gram:no-naka-de` (idx 297): 5 of 5 sentences are the spatial 〜の中で, the sense the nuance excludes

`nuance.pt-BR`: "*Aqui で marca o escopo da comparação, **não 'dentro de' no sentido espacial**.*" Every
linked sentence is spatial:

- `sent:tatoeba-125820` 鳥が木々の中でさえずっている。— "entre as árvores"
- `sent:tatoeba-143872` 図書館の中で話をしてはいけない。— "dentro da biblioteca"
- `sent:tatoeba-154919` 私は電車の中で読む本がほしい。— "no trem"
- `sent:tatoeba-163785` 私の兄は電車の中でスリにあった。— "dentro do trem"
- `sent:tatoeba-189575` 雨の中で歌いたい気分だ。— "na chuva"

None shows the superlative/scope use (スポーツの中でサッカーが一番好きです) that the record teaches. Note that the
sibling record `gram:gp-46` (idx 61, 〜のなかで〜がいちばん〜) *does* have five correct sentences — which is
further evidence these two records should be merged (F15). **Fix:** retag the five spatial ones off this
record; reuse `gp-46`'s set.

### F23 — `gram:gp-92` (idx 249): 4 of 5 sentences are not the numeric 以上 the record teaches

The record is explicitly 以上 ① "X or more (includes X)", and its `nuance` even flags that a second 以上
exists. The linked set:

- `sent:tatoeba-154767` 私は二時間以上も待った。 ✓ numeric
- `sent:tatoeba-191216` 以上ですか？ — "É só isso?" — the discourse-closing 以上, a third use, not in the record
- `sent:tatoeba-194455` もうこれ以上歩けないよ。 — これ以上 "any further", not numeric
- `sent:tatoeba-217592` これ以上は言えない。 — これ以上
- `sent:tatoeba-217598` これ以上のものはない。 — これ以上

**Fix:** move the これ以上 / 以上です sentences to their own record (or add these senses to `forms`), and add
numeric examples (18歳以上, 1000円以上).

### F24 — `gram:to-kiita` (idx 345): 2 of 5 sentences are 聞く "to ask", which the nuance excludes

`nuance.pt-BR`: "*聞く tem dois sentidos (ouvir e perguntar); **aqui é 'ouvir'**.*" Two linked sentences are
the "ask" sense, and their own pt translations say so:

- `sent:tatoeba-1395419` 「花が咲いているか」と聞いた。— pt "**Perguntei** se as flores estavam florescendo."
- `sent:tatoeba-229897` ある外国人が私に駅がどこにあるかと聞いた。— pt "Um estrangeiro me **perguntou** onde…"

**Fix:** retag both to a quotative-question record; the three generated sentences already cover the hearsay
sense correctly.

### F25 — `gram:mo` (idx 97): 3 of 5 sentences do not contain the particle も at all

Verified against the raw `grammar` arrays in `bank.json`:

- `sent:gen-50ec2f620020` 先日はどうも — tagged `["mo","wa-topic-marker"]`. The も here is inside the fixed
  lexical item どうも; there is no additive particle も.
- `sent:tatoeba-1057336` でもなんで？ — tagged `["de","gp-31","mo"]`. Contains **no** も. The tag appears to be
  a decomposition of でも into で + も, but でも here is the conjunction "but".
- `sent:gen-f4bf90e98fad` 雨でも行きます — tagged `["mo"]`. This is the concessive 〜でも, not the additive も.

Only `sent:tatoeba-125417` 弟もそうです and `sent:tatoeba-152214` 私もそうです illustrate the point.
**Fix:** drop the `mo` tag from those three; the concessive one belongs on `temo`/`n3-temo`.

### F26 — `gram:gp-102` (idx 169): a linked sentence produces the exact form the record's own note calls wrong

`sent:gen-a1650baf4ac0` **この問題が解けない学生はない** (AI-generated, `ai_generated: true`).

This record's own `steps_unavailable` states the constraint verbatim: "*The noun half is also
animacy-restricted: はない is the negative of ある, so **an animate head noun takes はいない (学生はいない, not
the 学生はない these steps emit)**.*" The corpus refused to encode the rule for this reason, then shipped a
generated sentence that violates it. In modern Japanese the head noun 学生 requires いない.

**Fix:** change the sentence to この問題が解けない学生は**いない**, updating `kana` accordingly. Worth a
corpus-wide grep for other generated 〜ない[animate noun]はない sentences.

### F27 — `gram:gp-134` (idx 201): 2 of 5 sentences are それ + で, not the conjunction それで

- `sent:tatoeba-205726` それで十分だよ。— "Assim já é suficiente" (それ + instrumental で)
- `sent:tatoeba-3488181` それでいいよ。— "Assim está bom" (same; also tagged `yo`)

Both are tagged `gp-134`. The record explicitly says それで "não conecta partes dentro de uma mesma oração; é
um conector entre sentenças". **Fix:** drop the `gp-134` tag from both.

### F28 — Further single-sentence mismatches (lower volume, same class)

| record | sentence | why it does not fit |
|---|---|---|
| `gram:te-de` (idx 133) | `sent:gen-790b6cf52284` 今日は晴れて暖かい | 晴れて is the て-form of the **verb** 晴れる; the record's formation says this point "não tem a ver com a forma て dos verbos" |
| `gram:gp-118` (idx 185) | `sent:tatoeba-11752934` 自分でやるしかないよ | dictionary-form **verb** + しかない; the record's formation is "[substantivo/quantidade] + しか + [verbo no negativo]" (this is the separate `n3-shika-nai` point) |
| `gram:gp-72` (idx 229) | `sent:tatoeba-10774565`, `-10906796`, `-146207` | all three are 〜ているところ, which the record's own explanation lists as a *different* member of the ところ family; only 2 of 5 show 〜るところだ |
| `gram:gp-42` (idx 57) | `sent:tatoeba-191983`, `-227007`, `-229458` | 3 of 5 are the けっこうです polite-refusal sense; `forms[]` lists only the degree adverb, so that sense has no entry to attach to |
| `gram:n3-sete-kudasai` (idx 441) | `sent:tatoeba-127098` 知らせてください | 知らせる is a lexical transitive ("to inform"); this is 〜てください asking the *other* person to act — precisely the 見せてください／見させてください confusion this record's `nuance` warns about |
| `gram:n3-sono-ue` (idx 445) | `sent:tatoeba-103918` 彼は食べ物と、その上にお金もくれた | mid-sentence その上に, not the sentence-initial connector the record's formation defines |
| `gram:demo` (idx 5) | `sent:tatoeba-74951` 万人の友は誰の友でもない / `sent:tatoeba-85538` 美人でもある | both are copula で + も (でもない / でもある), neither of the two roles the record documents |
| `gram:tsuzukeru` (idx 349) | 4 of 5 (`-11013726`, `-11888716`, `-12462035`, `-203508`) | standalone 続ける, not the 〜続ける compound the `label` and `structure_pattern` define; only `-140284` 走り続ける is the compound |

---

## S5 — Locale parity and pt-BR text quality

### F29 — `gram:gp-28` (idx 41): the en `explanation` carries two sentences the pt-BR one is missing

en has, and pt-BR does not: "*Before に the verb goes in the ます-stem (the ます form minus ます): 食べに行く 'go
eat'; never 食べるに行く. A noun that names an activity also works: 買い物に行く 'go shopping'.*" Length ratio
pt/en = 0.64. pt-BR is the learner-facing locale, so the "never 食べるに行く" warning — the record's single
most useful line — reaches nobody. (The `formation` and `nuance` fields do cover it, so this is a parity
defect rather than an outright hole.) **Fix:** add the two sentences to `explanation.pt-BR`.

### F30 — `gram:mae-ni` (idx 93): the pt-BR `explanation` is garbled, and the same content is missing from en

Current `explanation.pt-BR`, verbatim:

> "Pode se referir a um verbo na forma de dicionário; sempre no dicionário, mesmo que a oração principal
> esteja no passado (食べる前に手を洗いました = lavei as mãos antes de comer) **;,** a um substantivo de tempo
> com の (授業の前に, 昼ごはんの前に) **ou a uma quantidade de tempo, aí sem の (三年前に = três anos atrás) ou a
> uma quantidade de tempo ("três anos atrás")**."

Two defects: a stray `) ;,` sequence, and the clause "ou a uma quantidade de tempo" appears **twice**, the
second time with no content. Meanwhile `explanation.en` reads "*It can refer to a verb ('before eating'), to
a time noun …, or to a quantity of time*" and omits the "always dictionary form, even in the past" point
entirely. **Fix:** rewrite pt-BR as a clean three-item list and add the dictionary-form note to en.

### F31 — `gram:gp-134` (idx 201): mismatched brackets in the pt-BR `formation`

Current: `"[Frase 1 (causa]。それで、[Frase 2) resultado]."` — the parenthesis opens inside the first bracket
and closes inside the second. en is correct: `"[Sentence 1 (cause)]。それで、[Sentence 2 (result)]."`
**Fix:** `"[Frase 1 (causa)]。それで、[Frase 2 (resultado)]."`

### F32 — Missing diacritics in learner-facing pt-BR

| record | field | current text | should be |
|---|---|---|---|
| `gram:gp-72` (idx 229) | `explanation.pt-BR` | "Faz parte de uma **familia** de **tres**" | "família de três" |
| `gram:n3-ni-yoreba` (idx 429) | `nuance.pt-BR` | "Como a informação **e** de segunda mão, **e** natural fechar a frase" | "é de segunda mão, é natural" |
| `gram:n3-to-ii-naa` (idx 461) | `nuance.pt-BR` | "**E** coloquial e cheio de sentimento; … usa-se **so** といい"; "o と aqui não **e** o 'e'" | "É coloquial"; "só"; "não é o 'e'" |
| `gram:n3-to-iu-no` (idx 465) | `nuance.pt-BR` | "levemente **enfatico**"; "aqui o foco **e** justificar" | "enfático"; "é justificar" |

### F33 — Parentheses that swallow one or more following sentences

A recurring authoring artifact: a `(` opens mid-sentence and the matching `)` lands at the end of the field,
turning two or three independent sentences into one unreadable parenthetical. Instances in this slice, with
the locale that is broken (the other locale is usually clean, which pins the defect):

| record | field / locale | opens at | swallows |
|---|---|---|---|
| `gram:gp-5` (idx 65) | `nuance.en` | "(every inflection uses the stem よ-." | 2 further sentences to end of field |
| `gram:naa` (idx 101) | `nuance.en` | "(it's the sentence's 'sigh.'" | 2 further sentences |
| `gram:toki` (idx 141) | `nuance.en` | "(don't use a 'bare' とき as in Portuguese." | 1 further sentence |
| `gram:gp-122` (idx 189) | `nuance.pt-BR` | "(em português dizemos 'de' nos dois casos…" | 1 further sentence |
| `gram:no-naka-de` (idx 297) | `nuance.pt-BR` | "(fique atento a isso." | 2 further sentences |
| `gram:koto` (idx 273) | `nuance.pt-BR` | "(a nominalização com こと faz esse papel.)" | period inside paren |
| `gram:gp-118` (idx 185) | `nuance.pt-BR` | "(está errado; tem que ser 千円しかない.)" | period inside paren; en is correct |
| `gram:gp-138` (idx 205) | `nuance.pt-BR` | "(não confunda a partícula なければ.)" | period inside paren; see F10 |
| `gram:nakereba-ikenai` (idx 289) | `nuance.pt-BR` | "(evite em contexto formal.)" | period inside paren |
| `gram:gp-140` (idx 21) | `formation` pt+en | "(como em 'mais rápido') (a comparação está toda…" | double parenthesis, period inside |
| `gram:toki` (idx 141) | `formation` pt+en | "(note o の.)" | period inside paren |
| `gram:mitai-ni` (idx 285) | `formation` pt+en | "(é a mesma diferença de に vs な…)" | period inside paren |

**Fix:** close each parenthetical at its own sentence boundary and move the period outside.

### F34 — `gram:n3-tatoe-temo` (idx 453): the en `nuance` gives the same English for the right and the wrong version

Current `nuance.en`: "*in pt-BR we use 'mesmo que' with the subjunctive (**'even if it rains'**); be careful
not to translate it mechanically as **'even if it rains'** with the indicative, which sounds wrong.*"

The pt-BR original contrasts 'mesmo que chova' (correct) with 'mesmo se chove' (wrong); the en translator
rendered both as the same string, so the warning is empty. **Fix:** keep the Portuguese forms untranslated in
en: "…with the subjunctive ('mesmo que chova'); don't produce the indicative 'mesmo se chove', which is
wrong."

---

## S6 — Internal artifacts leaked into learner-facing text

### F35 — `gram:n3-to-iu-no` (idx 465): a raw database id appears in both locales

`nuance.pt-BR`: "*não confunda com というのは (que define um termo, **gid 422**)*"
`nuance.en`: "*don't confuse it with というのは (which defines a term, **gid 422**)*"

"gid 422" is an internal identifier; there is no `gid` field in `contracts/grammar.schema.json`, and `related`
is empty, so the reference is both meaningless to a reader and unresolvable by a consumer. **Fix:** delete
"gid 422" from both locales and put the target's `key` in `related`.

### F36 — `gram:n3-kanaa` (idx 381): pipeline vocabulary in the en `nuance`

`nuance.en`: "*PT trap: **the seed formation** that suggests だかなあ sounds forced in real speech…*"

"seed formation" is a generation-pipeline term describing where the draft came from; pt-BR correctly says
only "a construção だかなあ soa forçada na fala real". **Fix:** "PT trap: だかなあ sounds forced in real
speech; with nouns and な-adjectives, drop the だ in most cases."

### F37 — `gram:n3-nado` (idx 413): a positional cross-reference that resolves to the wrong record

`nuance.pt-BR`: "*a versão coloquial e mais informal é なんか (**veja o ponto seguinte**)*" / en: "*(see the
next point)*".

In the concatenated corpus order `n3-nado` is index 413; index 414 is `n3-nai-koto-wa-nai`
(〜ないことはない). `n3-nanka` is index **417**, four records later. The reference is broken as written, and it
would break again on any reordering. (`gram:gp-153`, idx 213, has the same "ver próximo ponto" construction;
that one happens to resolve correctly to `gp-154` today, but it is equally fragile.) **Fix:** name the target
("a versão coloquial é なんか") and put `n3-nanka` in `related`.

### F38 — Two `steps_unavailable` notes carry stale corruption claims that no longer match the data

- `gram:n3-kurai-wa-nai` (idx 397): "*Note also that this record's structure_pattern and forms[0].form are
  **corrupted with an editing instruction** in place of the pattern (failure mode F6)*" — current values are
  clean: `structure_pattern` = `～くらいは～ない`, `forms[0].form` = `～くらいは～ない`.
- `gram:n3-tatoe-temo` (idx 453): "*(Record defect noted separately: this point's structure_pattern field
  contains an editing instruction instead of a value.)*" — current value is clean: `たとえ～ても`.

These are the only two such notes in the whole corpus (grepped `corrupt|editing instruction|F6` across all
496). The underlying defect was evidently repaired without updating the note, so `steps_unavailable` now
reports a defect that does not exist. **Fix:** delete both trailing claims.

---

## S7 — Structural data gaps

### F39 — Every n3 record in the slice has `forms[].meaning = null`, `refs = null`, `families = []`

All **33** n3 records in the slice, without exception. Corpus-wide the split is exact: n5 = 0 forms with a
missing locale half, n4 = 1, **n3 = 132 of 132**. So the entire n3 tier ships `forms` entries whose `form`
string is present but whose pt-BR/en meaning is `null` — the learner-facing gloss of the form itself is
absent for every N3 point. Same story for `refs` (no `label_en`, no `also_known_as`, no `level_sources`
mirror) and `families` (no group membership, so no n3 point appears in any family view).

This looks like an n3 ingestion pass that never ran the enrichment step the n5/n4 tiers got. It is systemic,
not per-record, and should be one backlog item rather than 33.

### F40 — `level_confidence` = 0.34 with `level_agreement` "1/1" on every n3 record

All 33 n3 records in the slice carry `level_confidence: 0.34`, `level_agreement: "1/1"`,
`level_sources: {"hanabira": "n3"}` — a single community source. Spec §1.5 requires cross-referencing
**≥3 independent lists**. The n5/n4 records in the slice mostly reach 2/2 or 3/3 (jlptsensei, bunpro, tanos).
The n3 tier as shipped does not meet the level-tagging bar the project set for itself, which is worth
surfacing to the human reviewer explicitly rather than letting a 0.34 pass unnoticed.

### F41 — Sentence coverage is thin or absent for 14 of the 33 n3 records in the slice

**Zero linked sentences:** `n3-kurai-wa-nai`, `n3-moshi-temo`, `n3-ni-kawatte`, `n3-ni-shitemo`, `n3-sa`,
`n3-tatoe-temo`, `n3-tokorode` (7 records).
**Fewer than three:** `n3-ba-hodo` (1), `n3-koso` (2), `n3-maru-de-you` (2), `n3-ppai` (2), `n3-sono-ue` (2),
`n3-to-ii-naa` (1), `n3-to-shitara` (1).

Every n5/n4 record in the slice has ≥4. A point with no sentence cannot be exercised, reviewed against usage,
or validated per spec §7.

### F42 — `gram:n3-kurai-wa-nai` (idx 397): the pattern name asserts a 〜ない its own formation contradicts

`structure_pattern` and `forms[0].form` are both `～くらいは～ない`, and the record is titled "pelo menos (o
mínimo de)". But the only example the `formation` gives is 週に一度くらいはジムに**行かないと** — 〜ないと, an
*obligation* ("I have to go"), which is semantically affirmative. The canonical uses of this pattern are also
affirmative: 電話くらいはしてよ, 掃除ぐらいはしてほしい. The `explanation` hedges ("em geral, fecha-se com uma
negativa **ou com a forma que cobra/critica esse mínimo**"), which concedes that 〜ない is not obligatory.

Naming the point `～くらいは～ない` teaches learners that the negative is part of the pattern.
**Fix:** rename to `～くらいは` and describe the closing clause as "um pedido, uma cobrança ou uma negativa",
with at least one affirmative example.

### F43 — `gram:n3-tsumari` (idx 477): `forms[0].form` marks a prefix slot that cannot exist

`structure_pattern` = `つまり` (correct). `forms[0].form` = `**～**つまり`. The leading `～` is the corpus's
convention for "something attaches before this", but this record's own `formation` says つまり "aparece
tipicamente no início da segunda oração" and its `steps_unavailable` says it "attaches to no base". The `～`
is wrong and contradicts two other fields in the same record. **Fix:** `forms[0].form` = `つまり`.

### F44 — `gram:gp-57` (idx 73): `formation_steps` encodes only the *other* point

`gram:gp-57` is もらう "to receive (an object)". Its `formation` correctly describes
`[receptor]は/が + [doador]に/から + [coisa]を + もらう`, and all five linked sentences are that pattern
(せんせいから ほんを もらいました etc.). But its single `formation_steps` variant is
`[verb → to-te-form → append もらう]`, example `教えてもらう` — which is `gram:te-morau` (idx 333), a separate
record in this same slice with the identical variant. Any consumer generating practice from `gp-57`'s steps
produces 〜てもらう forms and never the receiving-an-object pattern the record teaches.
**Fix:** drop the てもらう variant from `gp-57` (it is fully covered by `te-morau`) and add
`steps_unavailable` explaining that もらう is a lexical verb plus a particle frame, not a suffixation rule —
the same treatment `gram:ga-imasu` and `gram:gp-12` already receive.

### F45 — `replace-ending` tokens use two incompatible conventions

Corpus-wide, the `replace-ending` op carries a token in two different formats:

- **arrow form** (17 variants): `て→ちゃ`, `で→じゃ`, `い→さ`, `い→そう`, `て→とく`, `て→ちゃった` …
- **bare form** (3 variants): `gram:te-de` (idx 133, in this slice) → token `くて`; `gram:gp-26` → `くて`;
  `gram:sugiru` → `すぎる`

Both are used on the same base (`i-adjective`) for the same kind of operation, so a consumer must implement
two parsers, and the bare form leaves *how much of the ending to strip* unstated. `gram:n3-sa` (idx 437, also
in this slice) uses the arrow form `い→さ` for the exact same class of rewrite that `te-de` writes bare.
**Fix:** normalise the three bare tokens to arrow form — `te-de`/`gp-26` → `い→くて`, `sugiru` → `い→すぎる` —
and state the convention in `scripts/validate/validate_grammar_formation.py`.

### F46 — Family membership is not semantic; the labels claim groupings the members do not honour

`families` on n5/n4 records points at groups whose `label` describes a topic the member has nothing to do
with. Members appear to have been bucketed by key order, not by content. Concrete instances from this slice
(family labels read from `corpus/families/families.json`):

| record | assigned family | family label | member's actual topic |
|---|---|---|---|
| `gram:gp-9` (idx 77) | `grp:gram-n5-passado` | "Passado polido e nuances" | ここ, a place demonstrative |
| `gram:yo` (idx 149) | `grp:gram-n5-passado` | "Passado polido e nuances" | sentence-final よ |
| `gram:gp-31` (idx 45) | `grp:gram-n5-particulas-lugar` | "Lugar, tempo e direção: で/に/へ/と" | なんで "why" |
| `gram:naru` (idx 109) | `grp:gram-n5-particulas-lugar` | same | なる "to become" |
| `gram:gp-46` (idx 61) | `grp:gram-n5-desu-wa` | "Frases básicas: o tópico は e a cópula です" | superlative 〜のなかで〜がいちばん |
| `gram:gp-122` (idx 189) | `grp:gram-n4-keigo` | "Keigo básico" | でできる "made of" |
| `gram:gp-114` (idx 181) | `grp:gram-n4-condicionais` | "Condicionais (たら/ば/と/なら)" | たとえば "for example" |
| `gram:bakari` (idx 157) | `grp:gram-n4-condicionais` | same | ばかり |
| `gram:yatto` (idx 353) | `grp:gram-n4-dar-receber` | "Dar e receber" | やっと "finally" |
| `gram:gp-88` (idx 245) | `grp:gram-n4-dar-receber` | same | ほとんど |
| `gram:sa` | `grp:gram-n4-dar-receber` | same | nominalising さ |
| `gram:te-itadakemasen-ka` (idx 329) | `grp:gram-n4-transitividade` | "Transitividade" | polite request 〜ていただけませんか |
| `gram:mama` (idx 281) | `grp:gram-n4-transitividade` | same | まま |
| `gram:gp-149` (idx 209) | `grp:gram-n4-causativa` | "Causativa" | polite negative 〜ません |
| `gram:sonna-ni` (idx 313) | `grp:gram-n4-causativa` | same | そんなに |
| `gram:gp-84` (idx 241) | `grp:gram-n4-condicionais` | "Condicionais" | 聞こえる |
| `gram:nasaru` (idx 293) | `grp:gram-n4-passiva` | "Passiva" | honorific なさる |
| `gram:gp-130` (idx 197) | `grp:gram-n4-potencial` | "Potencial" | とみえる "apparently" |

This is not a scattering of misfiles — it is the general case across the slice, and it means any UI or lesson
built from families presents unrelated points under a topical heading. Combined with F39 (all n3 records have
`families: []`), the family layer is unusable for grammar as it stands. Worth one backlog item, not 18.

### F47 — Four sentences linked from this slice have `translation.en = null`

`sent:tatoeba-187583` 何をなさるつもりですか (from `nasaru`), `sent:tatoeba-203508`
たとえ家を出る事になっても事業は続ける (`tsuzukeru`), `sent:tatoeba-84279` 負け犬になるわけにはいかない
(`n3-wake-ni-wa-ikanai`), `sent:tatoeba-4766` こらしめてやる (`te-yaru`). pt-BR is present in all four; only
the en (Layer-A source) half is missing.

### F48 — Generated sentences run two independent sentences together with a space, contradicting the record that tags them

Three records in this slice explicitly teach that their connective **opens a new sentence**, and the
generated sentences tagged to them join two clauses with a full-width or half-width space instead of 。/、:

| record | rule the record states | offending sentence |
|---|---|---|
| `gram:shikashi` (idx 125) | "[Frase 1]。 しかし、[Frase 2]。 … しかし separa em duas frases independentes" | `sent:gen-1cd3eb2cb7ec` 彼は若い しかしとても強い; `sent:gen-7932827a6b98` 勉強した しかしテストは難しかった |
| `gram:gp-134` (idx 201) | "Vem no início da segunda frase, depois de um ponto ou pausa" | `sent:gen-0702631e0a28` おなかがすいた　それでパンを買った; `sent:gen-375933b32579`; `sent:gen-c3c08b4ac390` |
| `gram:gp-114` (idx 181) | "Geralmente aparece no início da frase" | `sent:gen-12a28127409c` スポーツをします たとえばサッカーやテニス; `sent:gen-63960c1a9b9f`; `sent:gen-ea0e2f9ed5e4` |

Their own `translation_literal` fields render these as two sentences ("Estudei. Porém, quanto à prova…"), so
the boundary is intended but not written. `design/translation_style.md` §3 bans a trailing 。 on generated
sentences; it does not ban sentence-internal punctuation, and a space is not Japanese punctuation. **Fix:**
use 。 at the internal boundary and 、 after the connective (彼は若い。しかし、とても強い), keeping the final 。
off per the style rule.

---

## Clean records

**39 of the 124** carry no record-specific finding — their explanation, formation, formation_steps and nuance
are factually correct and mutually consistent, their linked sentences carry the point as described, and their
pt-BR/en halves match:

`da-desu` (1), `gp-12` (17), `gp-144` (25), `gp-17` (29), `gp-20` (33), `gp-35` (49), `gp-39` (53),
`issho-ni` (81), `ka-ka` (85), `keredo-mo` (89), `naku-temo-ii` (105), `ni-e` (113), `node` (121),
`ta-koto-ga-aru` (129), `te-kudasai` (137), `wa-dou-desu-ka` (145), `amari-nai` (153), `dewa-nai-ka` (161),
`gp-106` (173), `gp-110` (177), `gp-68` (225), `gp-80` (237), `gp-96` (253), `hajimeru` (257),
`ikou-kei-volitional-form` (261), `ka-dou-ka` (265), `kana` (269), `koto-ni-suru` (277), `o-ni-naru` (301),
`saseru` (309), `sou-ni-sou-na` (317), `te-morau` (333), `to-ittemo-ii` (341), `you-ni-naru` (357),
`zehi` (361), `n3-beki-da` (369), `n3-furi-wo-suru` (377), `n3-wa-mochiron-mo` (481), `n3-you-to-omou` (493).

The 33 n3 records among the whole slice are still subject to the tier-wide findings F16 (`related` empty),
F39 (`forms[].meaning` / `refs` / `families` all null or empty) and F40 (single-source level tag), which are
properties of the ingestion tier rather than of any record's authoring, and so are not counted against
individual records above.

Two observations recorded for the reviewer but **not** raised as findings, because neither is a defect:

- `gram:gp-106` (idx 173, ように〜てほしい): all five linked sentences are the narrower 〜ようにしてほしい
  composition (子供にもっと本を読む**ようにしてほしい** etc.). That is a valid instance of the pattern, but a
  reviewer may want at least one example of the record's own headline shape
  (早く元気になるように、ゆっくり休んでほしい).
- `gram:sou-ni-sou-na` (idx 317): its `steps_unavailable` is the strongest one in the slice — it correctly
  isolates both the いい → よさそう lexeme exception and the かわいい/かっこいい surface collision. Worth using as
  the model when repairing the notes flagged in F38.

---

## Count table

### Records

| | count |
|---|---|
| Records in slice (index % 4 == 1 over n5+n4+n3) | **124** |
| — n5 | 38 |
| — n4 | 53 |
| — n3 | 33 |
| Records read in full | **124** |
| Records carrying at least one record-specific finding | **85** |
| Records with no record-specific finding | **39** |

### Findings by severity class

Findings F16, F39 and F40 are slice- or tier-wide (they hold for every record, or for all 33 n3 records) and
are counted separately so they do not inflate the per-record column.

| class | meaning | findings | records touched |
|---|---|---|---|
| **S1** | formation rule produces wrong Japanese | 6 | 6 |
| **S2** | factually wrong / self-contradictory statement | 7 | 7 |
| **S3** | record identity, duplication | 4 | 26 |
| **S4** | linked sentences do not carry the point | 10 | 17 |
| **S5** | locale parity / pt-BR text quality | 6 | 19 |
| **S6** | internal artifact in learner-facing text | 4 | 6 |
| **S7** | structural data gap (record-specific) | 8 | 39 |
| record-specific subtotal | | **45** | **85** (union) |
| **T** | slice-/tier-wide: F16, F39, F40 | 3 | 124 / 33 / 33 |
| **Total findings** | | **48** | |

### Findings by kind of evidence

| evidence | findings |
|---|---|
| Wrong Japanese would be produced by following the record | 6 (F01–F06) |
| Record contradicted by its own other field | 9 (F02, F03, F05, F11, F12, F13, F26, F42, F43) |
| Record contradicted by its own linked sentences | 9 (F03, F08, F09, F14, F19, F20, F21, F22, F23) |
| Corpus-wide / tier-wide systemic | 6 (F15, F16, F39, F40, F41, F46) |
| Text-quality only (no factual error) | 8 (F29–F34, F37, F47) |

### Not flagged

`structure_explanation` on any sentence — excluded by instruction, not read.
Vocabulary, kanji, exercise and course-layer records — out of slice.
