# QA sweep — translation accuracy, slice 4/6

**Scope:** `corpus/sentences/bank.json`, records where `index % 6 == 3` (981 records, index 3 → 5883).
**Checked:** `translation["pt-BR"]` against `jp` (meaning, register, tense, polarity, counters, who-does-what);
`translation_literal["pt-BR"]` as a literal gloss; token `gloss` / `role` and particle `function` in pt-BR as
supporting evidence.
**Explicitly excluded:** `structure_explanation` (being re-authored elsewhere) — not read, not reported on.
**Authority:** `design/translation_style.md`.

Every record in the slice was read in full. Findings below are only defects I can defend against the
Japanese, against the record's own `en` sibling fields, or against a sibling record in the same slice that
handles the same construction differently. Every proposed fix is a concrete replacement string.

The slice is broadly healthy: **852 of 981 records (87%) carry no defect I can defend.** The single largest
problem is not the natural translations but the literal scaffolding (§C1), which misteaches the topic marker
in 39 records.

---

## A. Meaning defects in `translation["pt-BR"]`

### A1 — `[5019] sent:tatoeba-78159` — tense and voice both flipped
- JP: `旅行はやめにすると言った。`
- pt-BR: **"Ele disse que a viagem foi cancelada."**
- Why wrong: `やめにする` is non-past active ("will call it off"); the reported speech is a decision, not a
  completed passive event. The record contradicts itself — `translation_literal["pt-BR"]` reads
  **"Disse que, quanto à viagem, vai cancelar."** The pt-BR translation tells the learner the trip is
  already cancelled by an unnamed agent; the Japanese says someone announced they will cancel it.
- Fix: **"Ele disse que vai cancelar a viagem."**

### A2 — `[2169] sent:gen-fb07d83b3e0c` — 耳が痛い rendered with the wrong body part in pt-BR
- JP: `耳が少し痛いです`
- pt-BR: **"Minha orelha está doendo um pouco."**
- Why wrong: in pt-BR "orelha" is the outer ear (the flap); ear *pain* is always "ouvido" ("estou com dor de
  ouvido"). "Minha orelha está doendo" reads as an injury to the pinna. The token gloss itself offers both
  ("orelha/ouvido") and the wrong half was chosen for the pain reading.
- Fix: **"Meu ouvido está doendo um pouco."**

### A3 — `[2301] sent:jec-2798` — adjective misattachment produces "wireless music"
- JP: `簡単にワイヤレスで音楽を楽しめます`
- pt-BR: **"Dá pra curtir música sem fio facilmente."**
- Why wrong: `ワイヤレスで` is the *means* of listening, not a property of the music. In pt-BR "música sem
  fio" attaches "sem fio" to "música" and reads as *wireless music*, which is meaningless. The record's own
  `translation_literal["pt-BR"]` gets it right: "por (meio) sem fio".
- Fix: **"Dá para ouvir música sem fio com facilidade."**

### A4 — `[2361] sent:tatoeba-10083431` — つる (vine) rendered as "galho" (branch)
- JP: `それは葡萄のつるだよ。`
- pt-BR: **"Isso é um galho de videira, viu."**
- Why wrong: `つる` is a vine / tendril / creeper, not a woody branch; "galho" is the wrong lexical item. It
  also changes the referent: `葡萄のつる` *is* the grapevine (as `translation["en"]` says, "That's a
  grapevine"), whereas "um galho de videira" points at a part of one. The token gloss says "gavinha, ramo
  trepador (aqui: videira/parreira)" — the translation ignores its own gloss.
- Fix: **"Isso é uma parreira, viu."**

### A5 — `[1989] sent:gen-e54f1196ddcd` — と ("e") rendered as "com", collapsing two items into one dish
- JP: `朝ごはんはパンとたまごだ`
- pt-BR: **"O café da manhã é pão com ovo."**
- Why wrong: `と` enumerates two things. "Pão com ovo" in pt-BR names a single composed dish (bread *with*
  egg on it), not a list. The record's own particle note says **"と=partícula de ligação (e)"** and
  `translation_literal["pt-BR"]` says "pão e ovo". A learner mapping と → "com" here learns the wrong
  particle value; this is an N4 sentence where と-enumeration is the point.
- Fix: **"O café da manhã é pão e ovo."**

### A6 — `[1071] sent:gen-790b6cf52284` — 暖かい collapsed onto 暑い
- JP: `今日は晴れて暖かい`
- pt-BR: **"Hoje o tempo abriu e está quente."**
- Why wrong: `暖かい` is *pleasantly warm / mild*, explicitly opposed to `暑い` (hot). The slice renders `暑い`
  as "quente" too (`[4737] 今日はとても暑い` → "Hoje está muito quente"; `[1317] 今日は非常に暑いです` →
  "Hoje está extremamente quente"), so the 暖かい/暑い contrast — a core beginner distinction — is erased.
  This record's own token gloss says "quente / morno (agradável)". Compare `[3237]`, which handles
  `暖かくなる` correctly as "vai esquentando aos poucos".
- Fix: **"Hoje o tempo abriu e está quentinho."** (or "…e está ameno.")

### A7 — `[3663] sent:tatoeba-179557` — 行ってきた loses the return leg
- JP: `銀行へ行ってきたところです。`
- pt-BR: **"Acabei de ir ao banco."**
- Why wrong: `行ってくる` is go-*and-come-back*. "Acabei de ir ao banco" says the speaker just set off / just
  went; the Japanese says they are back. Both sibling fields keep the round trip:
  `translation["en"]` = "I've been to the bank", `translation_literal["pt-BR"]` = "fui e voltei do banco".
- Fix: **"Acabei de voltar do banco."**

### A8 — `[579] sent:gen-3de9af165938` — "chamar pelo nome" is a different act from 名前を呼ぶ
- JP: `先生に名前を呼ばれた`
- pt-BR: **"O professor me chamou pelo nome."**
- Why wrong: in pt-BR "chamar alguém *pelo* nome" means *to address someone by their first name* (rather
  than by title) — a statement about register. `名前を呼ぶ` is to *call out someone's name* (roll call, a
  waiting room). "Chamar o nome de alguém" is the pt-BR for that. `translation_literal["pt-BR"]` has it
  right ("o (meu) nome foi chamado").
- Fix: **"O professor chamou o meu nome."**

### A9 — `[2085] sent:gen-f07c27f794eb` — the sayer is dropped, and the two locales disagree on who it is
- JP: `先生はもう帰ったって言った`
- pt-BR: **"Disse que o professor já foi embora."**
- Why wrong: bare "Disse que…" in pt-BR defaults to first person or to a subject carried over from a
  previous sentence; as a standalone corpus entry it reads as "*I* said that…". `translation["en"]` names an
  agent ("**They** said the teacher has already left"), and `translation_literal["en"]` disagrees with both
  ("As for the teacher, **he** said that he has already come back" — the teacher as sayer, plus 帰った
  mis-glossed as "come back"). Three fields, three readings of who spoke.
- Fix: pt-BR → **"Disseram que o professor já foi embora."**, and correct `translation_literal["en"]` to
  match ("As for the teacher, (they) said he has already gone home").

### A10 — `[1449] sent:gen-a66bb37730f5` — superlative added that is not in the Japanese
- JP: `すしは人気のある料理の一つだ`
- pt-BR: **"O sushi é um dos pratos mais populares."**
- Why wrong: `人気のある料理の一つ` = "one of the dishes that are popular". There is no 最も / 一番. The
  record's own literal gets it right ("um dos pratos que têm popularidade"); `translation["en"]` repeats the
  same over-reach ("one of the most popular dishes"), so both locales need the same fix.
- Fix: pt-BR → **"O sushi é um dos pratos que fazem sucesso."** ; en → "Sushi is one of the popular dishes."

### A11 — `[507] sent:gen-3728d8e6f993` — 少し (the softener) dropped
- JP: `お菓子を少し食べすぎた`
- pt-BR: **"Comi doce demais."**
- Why wrong: `少し食べすぎた` is "ate a *little* too much" — a self-deprecating hedge, not a confession of
  excess. `translation_literal["pt-BR"]` keeps it ("um pouco comi-em-excesso") and `translation_literal["en"]`
  keeps it ("a few too many"); only the natural pt-BR (and its en twin) drop it.
- Fix: **"Comi um pouquinho de doce demais."**

---

## B. Unnatural pt-BR in `translation["pt-BR"]`

### B1 — `[1455] sent:gen-a6c6104da5a4` — "fora aos domingos" is not a licensed construction
- JP: `日曜日いがいは忙しいです`
- pt-BR: **"Fora aos domingos, eu fico ocupado."**
- Why wrong: as a preposition of exception, "fora" takes a bare complement ("fora domingo", "fora isso",
  "fora ele"). "Fora **aos** domingos" blends it with the "aos domingos" adverbial and comes out
  ungrammatical.
- Fix: **"Tirando os domingos, eu fico ocupado."** (or "Menos aos domingos, eu fico ocupado.")

### B2 — `[2415] sent:tatoeba-10307857` and `[5679] sent:tatoeba-8849610` — "isso e isto" contrasts two words Brazilians do not contrast
- JP: `それとこれとは別だと思うよ。` / `それとこれとは話が別でしょ。`
- pt-BR: **"Acho que isso e isto são coisas separadas."** / **"Isso e isto são coisas diferentes, não é?"**
- Why wrong: pt-BR has largely collapsed *isto* into *isso* in speech; putting them side by side to mark two
  distinct referents gives the reader no contrast at all and reads as a typo. The Japanese pair それ/これ needs
  the pt-BR pair that still carries deixis (*isso* / *aquilo*), or the set idiom.
- Fix: `[2415]` → **"Acho que uma coisa não tem nada a ver com a outra."**
  `[5679]` → **"Uma coisa é uma coisa, outra coisa é outra, não é?"**

### B3 — `[2661] sent:tatoeba-11056106` — "para onde dá para ver" is opaque
- JP: `どうしても見えるところに目がいってしまう。`
- pt-BR: **"Faça o que fizer, meus olhos acabam indo para onde dá para ver."**
- Why wrong: "para onde dá para ver" carries no meaning in pt-BR — it is a word-for-word transfer of
  見えるところ. It also mixes persons: the concessive is second person ("faça o que fizer") while the clause
  it governs is first person ("meus olhos"). `translation["en"]` resolves both ("No matter what **I** do, my
  eyes end up drifting to **whatever I can see**").
- Fix: **"Por mais que eu tente, meus olhos acabam indo para o que está à vista."**

### B4 — `[2817] sent:tatoeba-1192382` — "um cheiro bom de algo" misparses 何か
- JP: `水道の水おかしいよ。何かいい匂いがする。`
- pt-BR: **"A água da torneira está estranha. Tem um cheiro bom de algo."**
- Why wrong: `何か` here is adverbial ("somehow / sort of"), modifying the impression, not a genitive
  complement of 匂い. "Cheiro bom **de algo**" reads as *the smell of some thing* and is not idiomatic pt-BR
  under any reading. The token analysis encodes the same misparse (`何` role = "modificador de 匂い").
- Fix: **"A água da torneira está estranha. Tem um cheiro meio bom, sei lá de quê."**

### B5 — `[4941] sent:tatoeba-77149` — you do not "resolve a conversation" in pt-BR
- JP: `話をつけようじゃないか。`
- pt-BR: **"Vamos resolver essa conversa, que tal?"**
- Why wrong: `話をつける` = settle the matter. In pt-BR you resolve an *assunto* / *questão*; "resolver uma
  conversa" is not said. The record's own token gloss for 話 already offers "conversa, **assunto**".
- Fix: **"Vamos acertar esse assunto de uma vez, que tal?"**

### B6 — `[5811] sent:tatoeba-9701072` — the calque is glued onto the natural translation
- JP: `ほんの挨拶代わりです。`
- pt-BR: **"É só uma lembrancinha, em vez de um cumprimento."**
- Why wrong: `挨拶代わり` is a set phrase used when handing over a small gift; the "in place of a greeting"
  part is the Japanese idiom's internal logic, not something a Brazilian would say — "em vez de um
  cumprimento" makes the sentence read as if the gift *replaced* a greeting, which is confusing. That
  structural mirror belongs in `translation_literal`, where it already is ("É apenas em lugar de uma
  saudação"). `translation["en"]` handles it correctly ("Here's a little gift for you").
- Fix: **"É só uma lembrancinha, nada demais."**

### B7 — `[3657] sent:tatoeba-179074` — "a minha porção" for 僕の分 (a drink)
- JP: `君が飲むついでに、僕の分も入れてくれないかな。`
- pt-BR: **"Quando você for tomar, será que aproveita e faz a minha porção também?"**
- Why wrong: "porção" in pt-BR is a serving *of food* (a side dish); it does not collocate with pouring a
  drink. "Fazer a minha porção" is a literal transfer of 分.
- Fix: **"Já que você vai tomar, será que faz uma pra mim também?"**

### B8 — `[489] sent:gen-3549fd2ad4ef` — 再来年 rendered by a stacked relative clause
- JP: `そのお祭りは再来年も開かれる`
- pt-BR: **"Esse festival vai acontecer no ano depois do que vem também."**
- Why wrong: "no ano depois do que vem" is a clumsy chain, and the trailing "também" (rendering も) lands so
  far from what it scopes over that it reads as an afterthought. The slice already has the idiomatic pt-BR
  for this shape at `[237]` (`再来週` → "Daqui a duas semanas").
- Fix: **"Esse festival também vai acontecer daqui a dois anos."**

### B9 — `[2613] sent:tatoeba-11005020` — "loja" stated twice in one sentence
- JP: `店の下調べのため会社帰りに寄ることにした。`
- pt-BR: **"Decidi passar (na loja) na volta do trabalho para fazer um reconhecimento prévio da loja."**
- Why wrong: the same noun appears in a parenthesis and again in the purpose clause, so the sentence trips
  over itself; "reconhecimento prévio" is also register-mismatched (military/technical) for 下調べ.
- Fix: **"Decidi dar uma passada na loja na volta do trabalho para dar uma olhada antes."**

### B10 — `[3303] sent:tatoeba-149931` — *tu* possessive in a corpus that uses *você*
- JP: `自分のことだけかまってろよ。`
- pt-BR: **"Cuida só dos teus assuntos, viu."**
- Why wrong: `design/translation_style.md` fixes the second person as "você"; "teus" is the *tu* paradigm and
  is not the corpus norm. The record contradicts itself — `translation_literal["pt-BR"]` says
  **"dos seus próprios assuntos"**. Every other second-person record in the slice uses seu/sua
  (`[3579]` "a sua irmã", `[5289]` "o seu nome", `[195]` "o seu marido").
- Fix: **"Cuida só dos seus assuntos, viu."**

---

## C. Defective `translation_literal["pt-BR"]`

### C1 — topic scaffolding ("Quanto a X") applied to elements the Japanese marks with を / が / に / で — **39 records**

`design/translation_style.md` §1 reserves "quanto a X" for the topic marker `は`, precisely so the learner
can read the literal gloss as a map of the particles. In 39 records of this slice the phrase is instead
attached to a noun the sentence marks with a *different* particle, so the literal gloss teaches the wrong
particle value. Several records contradict themselves inside the same string.

Worst instances (the string names the particle it is misdescribing):

- `[1485] sent:gen-a9d2894fca14` — JP `私が説明いたします` — **"Quanto a eu (sujeito enfático), faço a
  explicação (humildemente)."** Two defects: `が` scaffolded as a topic, and "Quanto a **eu**" is not
  Portuguese (the preposition requires *mim*).
  Fix: **"Eu (が, sujeito enfático) é que faço a explicação (humildemente)."**
- `[1089] sent:gen-7c1c56b2c8fd` — JP `プレゼントをどうも` — **"Quanto ao presente (objeto), valeu/obrigado
  (どうも)."** The string labels the noun "(objeto)" and scaffolds it as a topic in the same breath.
  Fix: **"O presente (を, objeto), valeu/obrigado (どうも)."**
- `[1251] sent:gen-8fed7a630227` — JP `ボタンを押しました すると音が鳴りました` — **"Quanto ao botão (を),
  apertei; e então (すると), o som (が, sujeito) soou."** Same self-contradiction.
  Fix: **"O botão (を, objeto), apertei; e então (すると), o som (が, sujeito) soou."**
- `[2223] sent:jec-0231` — JP `私が車の運転をしない` — **"Quanto a mim (が, sujeito), a direção do carro (を)
  não faço."**
  Fix: **"Eu (が, sujeito), a direção do carro (を), não faço."**
- `[429] sent:gen-2f567fe6462d` — JP `部屋を明るくした` — **"Quanto ao quarto, clara-mente fiz."** `を` given
  topic scaffolding, *and* the resultative `明るく` rendered as a manner adverb: "clara-mente fiz" is not
  Portuguese and says *I did it clearly*, which is the opposite analysis. The record's own token role for
  `明るく` is correct ("advérbio (resultado da ação)").
  Fix: **"O quarto (を, objeto), tornei-o claro."**
- `[105] sent:gen-0b93f1f1f3f7` — JP `どれが一番安いですか` — **"Quanto a qual, é o número um (mais)
  barato?"** — the record's own particle note says "が marca どれ como sujeito; usa-se が (não は)".
  Fix: **"Qual (が, sujeito) é o número um (mais) barato?"**
- `[1143] sent:gen-82ddc26749ff` — JP `果物のなかでりんごが好きです` — **"Quanto a dentro das frutas, a maçã
  (sujeito) é gostada."** — "Quanto a dentro de" is not a Portuguese constituent; `で` here delimits scope.
  Fix: **"Dentro das frutas (で, âmbito), a maçã (が, sujeito) é gostada."**

Full list of the 39 records (id → the particle the phrase is misdescribing):

| ids | particle mis-scaffolded |
|---|---|
| 39, 69, 105, 345, 471, 591, 897, 963, 1191, 1617, 1899, 2115, 2169, 2211, 2223, 2229, 2265, 2271, 2283, 2289, 2313, 2349, 3123, 1485 | `が` (subject) |
| 429, 1089, 1173, 1251, 1497, 1923, 2259, 5205 | `を` (object / path) |
| 231, 951, 1353, 1797, 1941, 2175 | `に` (target / agent / time) |
| 1143 | `で` (scope) |

Not counted as defects (checked and cleared): `[159]`, `[273]`, `[3945]` also open with "Quanto a…", but
there the phrase restores an *elided* topic (`[273]` and `[3945]` even bracket it, "[Quanto a mim,]"), which
is legitimate scaffolding.

### C2 — `translation_literal["pt-BR"]` strings that are not parseable Portuguese — 5 records

These are not terse-but-readable glosses; a reviewer cannot recover a meaning from them.

- `[1227] sent:gen-8c9693e204f9` — JP `鳥が空を翔る` — **"Pássaro (que) o céu, voa (planando)."** The
  parenthetical "(que)" corresponds to nothing; it appears to be a corrupted particle label for `が`.
  Fix: **"O pássaro (が, sujeito), o céu (を, percurso), voa (planando)."**
- `[1899] sent:gen-d911309f7c89` — JP `電車が止まっているんです` — **"Quanto ao trem, é o caso de que ele está
  estando parado."** "Está estando" is not Portuguese; `止まっている` is a resultant state.
  Fix: **"O trem (が, sujeito), é o caso de que ele está (no estado de) parado."**
- `[4683] sent:tatoeba-4839` — JP `誰にも分からないよ` — **"Quem a também entende-não [enfático]."**
  Unrecoverable; `誰にも` + negative is the fixed "ninguém".
  Fix: **"Nem a quem quer que seja (誰にも) isso se entende, viu."**
- `[1983] sent:gen-e4c675e9ca2d` — JP `彼はもう二度と来るまい` — **"Quanto a ele, mais duas-vezes-e não-virá"**
  (also missing its final period). `二度と` is the fixed adverb "nunca mais", as the record's own particle
  note states ("と compõe a expressão fixa 二度と ('nunca mais')").
  Fix: **"Quanto a ele, nunca mais (もう二度と) virá, com certeza (まい)."**
- `[2889] sent:tatoeba-123026` — JP `二度と数学のテキストを忘れてはなりません` — **"Duas-vezes-mais
  matemática-de livro (objeto) esquecer-quanto-a não-deve."** Same `二度と` error, plus "esquecer-quanto-a"
  for `てはならない`.
  Fix: **"Nunca mais (二度と), o livro de matemática (を, objeto), esquecer não se deve (てはなりません)."**

### C3 — literal glosses that assert the wrong meaning — 2 records

- `[1281] sent:gen-92d901e97465` — JP `どうぞ遠慮しないでください` — **"Por favor, não se reserve."** In pt-BR
  *reservar-se* means to hold oneself back for later / to abstain; it does not carry 遠慮's "don't stand on
  ceremony" sense, so the literal points at the wrong idea. The natural translation is fine.
  Fix: **"Por favor, não faça cerimônia (遠慮しないで)."**
- `[5337] sent:tatoeba-81566` — JP `本当さ。信じた方がいいぜ。` — **"É verdade. É melhor você ter
  acreditado."** `〜た方がいい` is a fixed advice pattern about what to do *now*; the `た` is not a past tense.
  "É melhor você ter acreditado" in pt-BR means *you should have believed* — a reproach about the past, the
  opposite orientation. (Same pattern, milder, at `[4653]`: "O lado de ter dormido é bom, viu.")
  Fix: **"É verdade. O lado de acreditar é o melhor (信じた方がいい), viu."**

---

## D. Field discipline — scaffolding left inside `translation["pt-BR"]`

`design/translation_style.md` §5 assigns natural pt-BR to `translation` and structural/explanatory material
to `translation_literal` and `structure_explanation`. These 9 records keep explanatory material in the
natural field, where a learner reads it as part of the sentence.

### D1 — `[3537] sent:tatoeba-170417` — two unresolved alternatives left in the field
- JP: `最上のものは後から出てくる。`
- pt-BR: **"As melhores coisas vêm/aparecem depois."**
- Why wrong: a slash-separated pair of candidate verbs is an authoring note, not a translation. This is the
  only record in the slice with an unresolved alternation in `translation["pt-BR"]`.
- Fix: **"As melhores coisas vêm depois."**

### D2 — explanatory parentheticals in the natural translation — 8 records

| id | current `translation["pt-BR"]` | proposed fix |
|---|---|---|
| `[3723]` | "Vou tirar uma cópia ampliada **(e já volto)**, tá?" | "Vou ali tirar uma cópia ampliada, tá?" |
| `[4233]` | "…então deixe a barriga vazia **(não coma agora, guarde o apetite)**." | "Vai ter um banquete, então guarde o apetite." |
| `[4281]` | "Este par de luvas não está completo **(falta uma)**." | "Estas luvas não formam um par." |
| `[5223]` | "Amanhã vou buscar **(a pessoa)** em casa." | "Amanhã vou buscar você em casa." |
| `[5049]` | "Eu queria que **(você)** cozinhasse o ovo **(na água)**." | "Eu queria que você cozinhasse o ovo." |
| `[5553]` | "Meu pai está indo muito bem **(de saúde)**." | "Meu pai está muito bem de saúde." |
| `[4461]` | "Ele finalmente perdeu a paciência **(explodiu)**." | "Ele finalmente perdeu a paciência." |
| `[4869]` | "É **off-topic (fora do assunto)**. Desculpe." | "Isso é fora do assunto. Desculpe." |

Note: parentheses that gloss a *Japanese cultural term* on first use are a different, defensible convention
and are **not** flagged here (`[753]` "hanami (contemplação das flores de cerejeira)", `[1341]` "onigiri
(bolinho de arroz)"). The eight above gloss Portuguese, aspect, or an omitted argument.

---

## E. `translation` and `translation_literal` disagree on who is acting — 2 records

The Japanese is subject-less in both; the two pt-BR fields resolve it differently, so the record tells the
learner two things.

- `[1161] sent:gen-8457e05a188e` — JP `どの乗り物で行きますか`
  - `translation["pt-BR"]` = **"Com qual veículo a gente vai?"** (1st person plural)
  - `translation_literal["pt-BR"]` = **"Por meio de qual veículo (você) vai?"** (2nd person)
  - `〜ますか` addressed to someone defaults to second person; the literal is right.
  - Fix: **"De qual transporte você vai?"** (also more idiomatic than "com qual veículo").
- `[3099] sent:tatoeba-141381` — JP `川の近くにテントを張った。` — three-way split:
  `translation["pt-BR"]` = **"Armamos"** (1pl), `translation["en"]` = "We set up",
  `translation_literal["pt-BR"]` = **"armou"** (3sg), `translation_literal["en"]` = "they pitched" (3pl).
  - Fix: align the literal to the chosen reading — `translation_literal["pt-BR"]` →
    **"Do rio, no perto, barraca (を, objeto), armamos."** (and en → "we pitched").

---

## F. Token `gloss` / `role` errors in pt-BR — 2 records

- `[933] sent:gen-686faf1ec51d` — JP `狭い駅に人がたくさんいる`
  - The `に` token carries `gloss["pt-BR"]` = **"(elemento que forma o advérbio)"** and
    `role["pt-BR"]` = **"auxiliar adverbial"**; the particle entry says **"に=partícula de destino/direção"**.
  - Why wrong: with `いる`, `に` marks the *place of existence*, not direction and not an adverb-former. The
    slice glosses this exact construction correctly everywhere else — `[4395]` `いすの上にねこがいます`
    ("に=partícula de lugar de existência"), `[4803]` `学校に人がいる` (same), `[1035]` `玄関に大きな花がある`
    ("に=local de existência").
  - Fix: token gloss → `null` (particles elsewhere in this record carry none); token role →
    **"partícula de lugar de existência"**; particle function → **"marca o lugar onde algo/alguém existe"**.
- `[561] sent:gen-3c5ba89233cd` — JP `わたしは まいあさ パンを 食べる`
  - Tokens: `まい` → `gloss["pt-BR"]` = **"toda manhã (毎朝)"**, `あさ` → **"manhã"**.
  - Why wrong: the whole meaning "toda manhã" is loaded onto `まい`, which alone is only the distributive
    prefix 毎- ("cada / todo"); the reader is told that `まい` means "toda manhã" and then that `あさ` means
    "manhã", i.e. that the word says "toda manhã manhã". Where the slice keeps a compound whole it glosses
    the compound and leaves the pieces empty (`[237]` 再来週, `[1137]` 八百屋).
  - Fix: `まい` → **"todo / cada (prefixo 毎-)"**, `あさ` → **"manhã"**; or merge into one `まいあさ` token
    glossed **"toda manhã"**.

---

## G. Missing `en` anchor — 53 records (aggregate)

`translation["en"]` (and, in most of these, `translation_literal["en"]`) is `null`. Per the spec the English
is the Layer-A source the pt-BR is validated against, so for these 53 records the pt-BR has nothing to be
checked against and the human reviewer has no second reading to compare. Reported here because it directly
limits translation-accuracy review, not as a style issue.

`933, 4653, 4767, 4845, 4875, 4899, 4905, 4911, 4923, 4953, 4965, 4989, 4995, 5007, 5013, 5019, 5025, 5031,
5037, 5043, 5055, 5061, 5085, 5097, 5103, 5109, 5121, 5145, 5181, 5187, 5241, 5247, 5259, 5271, 5277, 5307,
5337, 5349, 5361, 5451, 5457, 5463, 5469, 5475, 5481, 5487, 5493, 5499, 5505, 5511, 5517, 5523, 5541`

They cluster hard at the tail of the file (52 of the 53 sit above index 4650; the lone outlier is `[933]`,
which is also the slice's only record with `provenance.jp_source == "generated"` rather than
`"ai-generated"` or a Tatoeba/JEC id). That pattern suggests a truncated backfill run rather than 53
independent omissions.

---

## Checked and clean

Mechanically screened across all 981 records, then confirmed by reading:

- **pt-PT leakage:** 0. Every hit of the pt-PT wordlist (autocarro, comboio, telemóvel, rapariga, ecrã,
  "estar a + infinitivo", casa de banho, morada, sumo, …) came back empty. The one lexical hit, `[1275]`
  "O focinho do cachorro é gelado", is the pt-BR *cold-to-the-touch* sense, not the pt-PT *ice cream* sense.
- **Em dash (—) in `translation` / `translation_literal` / token glosses:** 0.
- **Topic mirror leaking into the natural `translation`:** 0. The three "quanto a" hits are all legitimate:
  `[2553]` "o quanto antes", `[4263]` "tão fácil quanto", `[4311]` "Quanto a isso" (which renders an actual
  `〜に関しては`, not a bare `は`).
- **Empty `translation["pt-BR"]` / `translation_literal["pt-BR"]`:** 0. **Identical** translation and
  literal: 0.
- **Japanese characters or stray square brackets left in `translation["pt-BR"]`:** 0.
- **Counters and numerals:** all correct. Spot-verified the error-prone magnitudes — `一億円` → "cem milhões
  de ienes" (`[1113]`, `[1263]`, `[2187]`), `一万人` → "dez mil pessoas" (`[771]`), `五万円` → "cinquenta mil
  ienes" (`[1167]`), `三百グラム` → "trezentos gramas" (`[1581]`), plus 二個/三冊/三匹/二枚/七つ/五つ/二倍 —
  no off-by-one and no magnitude slip.
- **Polarity:** all correct, including the hard shapes — `[33]` 少なくない → "Não são poucos os alunos…",
  `[3273]` 一度しかない → "A juventude só vem uma vez.", `[5487]` 一つの家具も残っていない → "Não sobrou
  nenhum móvel…", `[2331]` わけではない → "Isso não quer dizer que…", `[3159]` ばかりではない → "nem tudo são
  coisas boas".
- **Register mirroring:** broadly right. Casual JP lands casual (`[183]` 出かけたくない → "não tô a fim de
  sair"; `[825]` じゃないか → "Nossa, essa comida tá uma delícia, né?"; `[243]` めんどうがる → "acha o dever
  de casa um saco") and keigo lands neutral-polite (`[1221]` でございます → "Hoje estamos fechados";
  `[2979]` お待たせしてすみませんでした → "Desculpe por tê-lo feito esperar tanto tempo"; `[5283]` 参ります →
  "virei sem falta"). No case rose to a defensible defect.

---

## Count table

| Class | What | Records checked | Records flagged |
|---|---|---:|---:|
| A | Meaning defect in `translation["pt-BR"]` (mistranslation, tense/voice, wrong referent, added/dropped meaning) | 981 | 11 |
| B | Unnatural pt-BR in `translation["pt-BR"]` | 981 | 11 (10 findings; B2 covers 2) |
| C | Defective `translation_literal["pt-BR"]` | 981 | 45 (C1 = 39, C2 = 5, C3 = 2; `[429]` and `[1899]` counted once) |
| D | Scaffolding left inside `translation["pt-BR"]` | 981 | 9 (1 + 8) |
| E | `translation` vs `translation_literal` disagree on the agent | 981 | 2 |
| F | Token `gloss` / `role` error in pt-BR | 981 | 2 |
| G | Missing `en` anchor (`translation["en"]` null) | 981 | 53 (1 aggregate finding) |
| — | pt-PT leakage | 981 | 0 |
| — | Em dash in translation fields or glosses | 981 | 0 |
| — | Topic mirror ("quanto a") in the natural `translation` | 981 | 0 |
| — | Empty / duplicated pt-BR translation or literal | 981 | 0 |
| — | Counter / numeral errors | 981 | 0 |
| — | Polarity errors | 981 | 0 |
| — | Register mismatch rising to a defect | 981 | 0 |

**Totals:** 981 records checked; **32 findings** touching **129 distinct records** (11 + 11 + 45 + 9 + 2 + 2
+ 53, less 4 records that appear in two classes: `[2169]` in A and C1, `[933]` in F and G, `[5019]` in A and
G, `[5337]` in C3 and G). **852 records (87%) carry no defect.**

Priority for the teacher queue:

1. **A1–A5** — the pt-BR says something the Japanese does not, and in each case a sibling field in the same
   record already says the right thing, so these are decidable without a judgement call.
2. **C1** — 39 records, one mechanical rule ("quanto a X" belongs to `は` only). Cheapest large win; can be
   worked as a batch against the id table above.
3. **C2, C3** — literal strings that are broken or point at the wrong meaning.
4. **A6–A11, E, F** — nuance, agent, and gloss corrections.
5. **D, B** — field hygiene and naturalness.
6. **G** — batch backfill of the 53 missing English anchors.
