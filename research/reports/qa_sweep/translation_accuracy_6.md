# QA sweep — translation accuracy, slice 6/6

**Scope.** `corpus/sentences/bank.json`, records where `index % 6 == 5` — **981 records**, indices 5 … 5885
(bank total 5889). Every record in the slice was read in full: `jp` / `kana` / `translation.pt-BR` /
`translation.en` / `translation_literal.*` / `tokens[].gloss.pt-BR` / `tokens[].role` /
`tokens[].conjugation_note` / `particles[].function`.

**Explicitly excluded per assignment:** `structure_explanation` (being re-authored elsewhere). Not read, not judged.

**Style authority:** `design/translation_style.md`. The rules that carry weight below are §1 (natural
translation, *not* a literal mirror; "quanto a X" belongs in `translation_literal`, never in `translation`),
§2 (register mirrors the JP), §4 (pt-BR only), §5 (field discipline — `translation` = natural pt-BR,
explanation lives elsewhere).

**Headline.** The natural pt-BR in `translation.pt-BR` is in good shape. Across 981 sentences I could
defend **14 individual meaning/naturalness defects** — a ~1.4% rate. The real problems in this slice are
in the *supporting* fields: `translation_literal.pt-BR` has a systematic mis-teaching of the topic marker
(43 records), 62 records are missing their `en` half entirely, and 13 records leak explanatory
parentheses into the natural-translation field.

---

## A. Mistranslation / added or dropped meaning in `translation.pt-BR`

### A1 — `[5093] sent:tatoeba-78906` — invented third-person subject
- **jp:** 容易に試験に通ると思う。
- **current pt:** `Acho que ela vai passar na prova fácil.`
- **why wrong:** the Japanese has no subject anywhere. The record's own `translation_literal.pt-BR`
  ("Facilmente na prova passar, eu acho.") has no subject either, and there is no `彼女` / `かのじょ` token.
  "ela" is invented, and it is the *only* place in the record where a third person appears.
- **fix:** `Acho que vou passar na prova fácil.` (or, if a generic reading is wanted,
  `Acho que dá para passar na prova fácil.`)

### A2 — `[1805] sent:gen-ceb6657fc2af` — 紹介する rendered as "recomendar"
- **jp:** 先生が新しい本を紹介した
- **current pt:** `O professor recomendou um livro novo.`
- **why wrong:** 紹介する is *apresentar / indicar*; *recomendar* is 勧める and adds an endorsement the JP
  does not make. The record contradicts itself: its own `translation_literal.pt-BR` says
  "O professor (が) um livro novo **apresentou**", and two other records in this same slice translate
  紹介 correctly — `[521] gen-3863bc182f37` ("Apresentei meu amigo…") and `[2261] jec-1064`
  ("Vou apresentar o Top 20.").
- **fix:** `O professor apresentou um livro novo.`

### A3 — `[1517] sent:gen-adff42166044` — Ｙシャツ flattened to "camisa"
- **jp:** 新しいＹシャツを買った
- **current pt:** `Comprei uma camisa nova.`
- **why wrong:** Ｙシャツ is specifically a *camisa social*. The record's own token gloss says
  "camisa social (camisa de colarinho)", its `translation_literal.pt-BR` says "Camisa-Y nova", and its
  `translation_literal.en` says "A new dress shirt". `[1607] gen-b874afd1c17d` in this same slice, same
  word, translates it correctly as "camisa social branca". The distinction is the whole point of the
  vocabulary item (686).
- **fix:** `Comprei uma camisa social nova.`

### A4 — `[2315] sent:jec-3829` — explanatory clause appended + person conflicts with `en`
- **jp:** 心臓に毛がビッシリ生えている
- **current pt:** `Ele tem sangue de barata, nada o abala.`
- **current en:** `You have nerves of steel.`
- **why wrong:** two problems. (1) ", nada o abala" is a gloss of the idiom, not part of the sentence —
  §5 puts explanation outside `translation`. (2) The pt is 3rd-person masculine while the `en` half of the
  same locale-object is 2nd person; a reviewer reading the pair cannot tell who the sentence is about.
- **fix:** `Ele tem sangue de barata.` — and align `translation.en` to "He has nerves of steel."

### A5 — `[2495] sent:tatoeba-10661542` — くせに's concessive force dropped, "nosso" added
- **jp:** 友達でもないくせに。
- **current pt:** `Você nem é nosso amigo.`
- **why wrong:** くせに is a reproachful concessive ("e olha que…", "sendo que…"); the current pt is a
  flat assertion and loses it entirely. The record's own literal keeps it
  ("Apesar de não ser nem amigo…"), so the natural translation is the outlier. Separately, "nosso" has
  no support in the JP (no 私たちの / うちの) — `translation_literal.en` even says "he", so the record
  disagrees with itself on person as well.
- **fix:** `E olha que você nem é meu amigo.` (or `Sendo que você nem é amigo…`)

---

## B. Unnatural pt-BR in `translation.pt-BR`

### B1 — `[107] sent:gen-0ba1c8db394e`
- **jp:** テーブルにいすが五つある · **current pt:** `Tem cinco cadeiras na mesa.`
- **why wrong:** in pt-BR "cadeiras **na** mesa" reads as chairs placed *on top of* the table. The
  record's own `en` says "There are five chairs **at** the table".
- **fix:** `Tem cinco cadeiras em volta da mesa.` (or `…à mesa.`)

### B2 — `[1403] sent:gen-a0f74dfe5889`
- **jp:** 再来月までに引っ越したいです · **current pt:** `Quero me mudar até o mês depois do que vem.`
- **why wrong:** "o mês depois do que vem" is a word-for-word calque, not something a Brazilian says.
  The same 再来〜 construction is rendered naturally twice elsewhere in this slice:
  `[17] gen-025585248523` → "até daqui a duas semanas", `[1889] gen-d7ecbc3ceb36` → "daqui a dois meses".
- **fix:** `Quero me mudar até daqui a dois meses.`

### B3 — `[1715] sent:gen-c5a812d1b02f`
- **jp:** この机は狭くて使いにくい · **current pt:** `Esta mesa é apertada e difícil de usar.`
- **why wrong:** in pt-BR *apertado* describes a space you fit **into** (um quarto apertado), not a work
  surface. 狭い of a 机 means the writing area is small/cramped.
- **fix:** `Esta mesa é pequena e difícil de usar.`

### B4 — `[2609] sent:tatoeba-11001318`
- **jp:** 今月あのスーパーは水曜日が休みです。· **current pt:** `Este mês, aquele supermercado folga às quartas-feiras.`
- **why wrong:** *folgar* takes a human subject in pt-BR; a store doesn't "folgar". The record's own `en`
  says "is closed on Wednesdays".
- **fix:** `Este mês, aquele supermercado fecha às quartas-feiras.` (or `…não abre às quartas.`)

### B5 — `[2759] sent:tatoeba-115629` — literal scaffolding leaked into the natural field
- **jp:** 彼は、どちらかというと、分別のある人だ。
- **current pt:** `Ele, se for para escolher um lado, é um homem sensato.`
- **why wrong:** "se for para escolher um lado" is a word-by-word unpacking of どちらかというと — exactly the
  kind of mirror §1 says belongs in `translation_literal`, not `translation`. Secondarily, 人 is
  gender-neutral and becomes "homem".
- **fix:** `Ele até que é uma pessoa sensata.` (or `No fim das contas, ele é uma pessoa sensata.`)

### B6 — `[2645] sent:tatoeba-11029885`
- **jp:** こういう人は節約を楽しんでるタイプね。· **current pt:** `Esse tipo de pessoa é do tipo que curte economizar, né.`
- **why wrong:** "tipo … do tipo" in one short sentence; こういう人 is not "esse tipo de pessoa" + タイプ again.
- **fix:** `Gente assim é do tipo que curte economizar, né.`

### B7 — `[2339] sent:jec-5277`
- **jp:** 公衆トイレで必ず用を足しておきましょう · **current pt:** `Vamos sem falta usar o banheiro público antes.`
- **why wrong:** adverb placement between "Vamos" and the infinitive is not natural pt-BR word order.
- **fix:** `Vamos usar o banheiro público antes, sem falta.`

### B8 — `[2525] sent:tatoeba-10782616` — orthographic error
- **jp:** お米１合って何グラム？ · **current pt:** `Um 'go' de arroz da quantos gramas?`
- **why wrong:** `da` is the contraction *de + a*; the verb *dar* in the 3rd person is **dá**. As written
  the sentence has no verb. This is learner-facing text.
- **fix:** `Um 'go' de arroz **dá** quantos gramas?`

### B9 — `[1967] sent:gen-e1c01b4c8791` — 県 rendered inconsistently inside the same record
- **jp:** 県下で一番大きい病院です · **current pt:** `É o maior hospital do estado.`
- **why wrong:** the record's own `translation_literal.pt-BR` says "Dentro da **província**…", and
  `[605] gen-41d4b4ca8de4` — same vocab id 842, same 県下 — says "famoso na **província**". One of the two
  has to change; a learner meeting 県 twice should not get two different pt words.
- **fix:** pick one house term (suggest **província**) and apply it to both records.

---

## C. Field discipline — explanatory parentheses inside `translation.pt-BR` (13 records)

`design/translation_style.md` §5 reserves `translation` for natural pt-BR; the gloss belongs in
`translation_literal` / token fields. 13 records in the slice carry a parenthetical inside the natural
translation. Two sub-groups:

**C1 — explanatory glosses (9 records) — should move out:**

| idx | slug | current `translation.pt-BR` | suggested |
|---|---|---|---|
| 1877 | gen-d58ab4004378 | `Eu ligo para você (professor) mais tarde.` | `Depois eu ligo para o senhor, professor.` |
| 1991 | gen-e552be802fd5 | `A cerveja acabou esquentando (perdeu o gelado).` | `A cerveja acabou esquentando.` |
| 2579 | tatoeba-10926432 | `Há um calendário (colocado) em cima da mesa.` | `Tem um calendário em cima da mesa.` |
| 3293 | tatoeba-149534 | `Eu tenho uma pergunta, mas... (posso fazê-la?)` | `Eu tenho uma pergunta…` |
| 3317 | tatoeba-150564 | `Não vou conseguir chegar em casa a tempo (dentro do prazo).` | `Não vou conseguir chegar em casa a tempo.` |
| 3833 | tatoeba-190636 | `Escreva pulando uma linha (em linhas alternadas).` | `Escreva pulando uma linha.` |
| 4685 | tatoeba-4852 | `Não gosto mais (de você).` | `Não gosto mais de você.` |
| 4727 | tatoeba-5052 | `Gosto muito (disso)!` | `Gosto muito disso!` |
| 5657 | tatoeba-8736596 | `Vou sair para comer (e já volto).` | `Vou sair para comer e já volto.` |

**C2 — gender-inclusive parentheses (4 records) — house-style decision, not an error per se:**
`[2951]` "Seja bem-vindo(a)!" (inside quoted speech, where a real shop clerk would say one form),
`[4529]` "o(a) senhor(a)", `[5357]` "ocupado(a)", `[5735]` "O senhor (a senhora) tem filhos?".
Flagging so the teacher can rule once; `[5735]` in particular reads oddly with two separate noun phrases.

---

## D. `translation_literal.pt-BR` defects

### D1 — `[4691] sent:tatoeba-4864` — **polarity reversed** (most serious literal defect in the slice)
- **jp:** 君には何が起こるか分かるんじゃないかと思うけどね。
- **`translation.pt-BR`:** `Acho que você já deve imaginar o que vai acontecer, né.` ✅ correct
- **`translation_literal.pt-BR`:** `Para você, penso que **não seria o caso de entender** o que vai acontecer, mas enfim.` ❌
- **why wrong:** 〜んじゃないかと思う is a *positive* supposition delivered through a negative question
  ("I think you probably do understand"). The literal reads it as flat negation and contradicts the
  natural translation sitting right above it. A learner comparing the two fields learns the pattern backwards.
- **fix:** `Para você, quanto ao que vai acontecer, "não é que (você) entenda?", é o que eu penso, mas enfim.`

### D2 — `[1367] sent:gen-9cce99320afa` — wrong aspect
- **jp:** 何を食べるかまだ決めていない
- **current literal:** `Vou comer o quê-か, ainda **não estou decidindo**.`
- **why wrong:** 決めていない here is the resultant-state negative ("haven't decided"), not the progressive
  ("am not deciding"). The natural translation gets it right ("Ainda não decidi…"), so the literal teaches
  the opposite reading of 〜ている. The hybrid "o quê-か" is also not Portuguese.
- **fix:** `"O que vou comer?" — ainda não (o) tenho decidido.`

### D3 — `[455] sent:gen-3186ec3a3f3d` — literal is a formula, not a gloss
- **jp:** 今日は疲れたって感じ
- **current literal (pt):** `Quanto a hoje (今日は), "cansei" (疲れた) + って + 感じ (sensação).`
- **current literal (en):** `As for today (kyou wa), it's a "I'm tired" (tsukareta) + tte + kanji (feeling).`
- **why wrong:** every other record in the slice gives a running pt gloss; this one gives a `+`-joined
  formula with unglossed Japanese in the middle. Worse, the `en` half romanizes 感じ as **"kanji"**, which
  collides with 漢字 — for a beginner reading the en column, that is actively misleading.
- **fix (pt):** `Quanto a hoje, é aquela sensação de "cansei".`  **fix (en):** romanize as *kanji* → *kanji (feeling)* is unrecoverable; use `…+ kanji [感じ, "feeling"]` or drop the romaji.

### D4 — literals that do not parse as Portuguese (4 records)
These are learner-facing and currently unreadable even as scaffolding:

| idx | slug | current `translation_literal.pt-BR` | problem / fix |
|---|---|---|---|
| 1997 | gen-e5bc8ecc1fc4 | `Quanto a hoje, (não) está, no que toca a ser frio, muito (não).` | double negation scattered across the clause; nothing parses. → `Quanto a hoje, no que toca a ser frio, não é muito.` |
| 2447 | tatoeba-10496134 | `Caro-parecer -mente quanto-a ver-não, viu.` | "-mente" floating as a bare suffix. → `Quanto a parecer caro, não parece, viu.` |
| 3701 | tatoeba-183269 | `Ânimo, à (isso) faça (não, viu.)` | mismatched parentheses, "à (isso)" ungrammatical. → `Quanto a isso, não ponha o ânimo (não se importe), viu.` |
| 5765 | tatoeba-93463 | `Ela foi zombada.` | *zombar* is intransitive in pt (zombar **de**); "foi zombada" is ungrammatical. → `Zombaram dela.` / `Ela foi alvo de zombaria.` |

### D5 — **systematic:** the topic formula "Quanto a…" used for sentences with no は (43 records)
`design/translation_style.md` §1 assigns "quanto a X" to the topic marker は specifically, and keeps it in
`translation_literal` precisely because the literal structure *is* the teaching point. In **43 records of
this slice the literal opens with "Quanto a…" although the sentence contains no は token at all** — so the
formula gets attached to が, を, に or の instead, teaching the wrong particle→gloss mapping.

Clearest offenders (the fronted noun is explicitly が- or を-marked in the JP):

| idx | slug | jp | current literal opening |
|---|---|---|---|
| 41 | gen-042f49f87296 | 猫**が**外で鳴いている | `Quanto ao gato, (ele) em fora está miando.` |
| 353 | gen-26336d038665 | 道**が**分からなくて困りました | `Quanto ao caminho, não entendendo, fiquei em apuros.` |
| 713 | gen-4ef337183d6c | 新しい棚**を**部屋に置いた | `Quanto à prateleira nova, no quarto (eu) coloquei.` |
| 869 | gen-5ff3594c3568 | 薬**を**飲んだら… | `Quanto a remédio **(objeto)**, quando bebi, logo fiquei bom.` |
| 917 | gen-665001523d69 | …車**が**好きです | `Quanto a carros de fabricação-alemã **(sujeito が)**, é gostado…` |
| 1061 | gen-769512251f0a | みかん**を**九つ買った | `Quanto a tangerinas **(objeto)**, nove (unidades) comprei.` |
| 1445 | gen-a638a3021e2b | 子供**が**先にお風呂に入った | `Quanto às crianças **(sujeito)**, antes/primeiro, no banho entraram.` |
| 1637 | gen-bc320ff08905 | 子供**が**おもちゃを片付けない | `Quanto à criança **(sujeito)**, os brinquedos, (ela) não os guarda.` |
| 1667 | gen-bfd8d9f015bb | なべ**が**とても熱くなった | `Quanto a panela, (ela) muito quente ficou.` |
| 1673 | gen-c07050372e38 | 白い猫**が**好きです | `Quanto a gato branco, é objeto de gostar.` |
| 2213 | jec-0048 | 妻**が**買い物をする | `Quanto à esposa, ela faz a compra.` |
| 2285 | jec-2051 | 男性**が**なにやら話を始めた | `Quanto ao homem **(が)**, … o assunto (を), começou.` |
| 2327 | jec-4674 | 彼**が**すぐにおなかを壊す | `Quanto a ele, logo estraga a barriga.` |
| 5843 | tatoeba-98485 | 彼らの時間の多く**が**… | `Quanto a muito do tempo deles, … é usado.` |

Six of these are internally self-contradictory: they write "Quanto a X **(sujeito が)**" or
"Quanto a X **(objeto)**" in the same breath — the annotation says が/を while the wording says は.

- **fix:** reserve "Quanto a…" for は. For が use the record's own vocabulary — "X (が: sujeito) …",
  the pattern already used correctly at `[275] gen-1e8c789f54af` ("A professora (が: sujeito/informação
  nova), …") and `[1157] gen-83f74d460da8` ("A mãe (が, sujeito) a janela (を) fechou"). For を front the
  object without the topic formula, as `[911] gen-65a764e62fe3` already does ("No papel, comprida linha, tracei.").
- Full index list of the 43: 41, 179, 227, 353, 419, 437, 683, 713, 731, 773, 785, 869, 917, 923, 1031,
  1043, 1061, 1445, 1493, 1541, 1589, 1595, 1637, 1667, 1673, 1709, 1817, 1853, 1931, 1961, 2039, 2213,
  2237, 2285, 2315, 2327, 2369, 2633, 3449, 4313, 5213, 5843, 5861.
  (A handful of these — e.g. 683, 773 fronting a nominalized clause — are defensible as a generic
  fronting device; the が/を ones above are not.)

### D6 — `[1667] sent:gen-bfd8d9f015bb` — missing crase
- **current:** `Quanto a panela, (ela) muito quente ficou.` → **fix:** `Quanto **à** panela, …`
  (Same record as D5; listed separately because it is a plain pt-BR grammar error independent of the scaffolding issue.)

### D7 — `[2099] sent:gen-f29ebd3055ef` — literal contradicts its own token gloss
- **jp:** 夕日で空が赤く焼ける
- **current literal:** `Com o sol poente, quanto ao céu, ele **assa/arde** de vermelho.`
- **why wrong:** "o céu assa" is not Portuguese, and the record's own token gloss for 焼ける already gives
  the right sense: "avermelhar, tingir-se de vermelho (do céu ao entardecer)".
- **fix:** `Com o sol poente, quanto ao céu, ele se tinge de vermelho.`

---

## E. Token `role` errors (2 records — both in the `reauthored` group)

### E1 — `[1229] sent:gen-8cc2f196d1e9`
- **jp:** 猫の毛はとてもきれいだ — token `猫` carries `role.pt-BR = "sujeito"`.
- **why wrong:** 猫 is the の-marked possessor/modifier of 毛; the sujeito/tópico is 毛 (which the record
  labels "tópico" correctly). Every parallel record in the slice labels the の-possessor as
  "modificador (posse)" — e.g. `[1043] gen-746983bc35bf` 川 → "modificador (posse)",
  `[2207] gen-ff68b04925e4` うち → "modificador (dono)".
- **fix:** `role.pt-BR = "modificador (posse)"`.

### E2 — `[1769] sent:gen-cb6562f41e17`
- **jp:** 友達のお兄さんは背が高い — token `友達` carries `role.pt-BR = "objeto direto"`.
- **why wrong:** there is no verb and no を in the sentence; 友達 is the の-possessor of お兄さん.
- **fix:** `role.pt-BR = "modificador (posse)"`.

Both E1 and E2 are `provenance.tags = ["reauthored"]` records — worth checking the whole `reauthored`
cohort, not just this slice.

---

## F. Data completeness — 62 records missing the `en` half of the locale-object

62 of the 981 records have `translation.en` and/or `translation_literal.en` set to **null** while the
pt-BR side is populated. This breaks the `{"pt-BR": …, "en": …}` locale-object contract and removes the
en cross-check a reviewer would otherwise use.

Breakdown:
- **60 records missing both** `translation.en` and `translation_literal.en` — 57 tagged `mined,stage:`
  and 3 tagged `reauthored` (`[1229]`, `[1601]`, `[1769]`). The mined ones cluster in the tail of the
  bank (index ≥ 4679), which suggests an ingestion pass that stopped populating the en column.
- **2 records missing `translation.en` only** (literal en present): `[3635] tatoeba-175272`
  (`coverage:n5`) and `[4997] tatoeba-77972` (`top:n3-conjectura`). These two are separate from the
  mined cluster and look like individual omissions.
- 0 records missing `translation_literal.en` alone.

Full index list: 1229, 1601, 1769, 3635, 4679, 4691, 4775, 4823, 4829, 4835, 4847, 4859, 4865, 4895,
4919, 4967, 4979, 4997, 5009, 5021, 5027, 5033, 5045, 5057, 5063, 5087, 5093, 5099, 5105, 5111, 5117,
5135, 5141, 5153, 5165, 5189, 5219, 5237, 5255, 5279, 5291, 5297, 5333, 5381, 5441, 5447, 5453, 5459,
5465, 5471, 5477, 5483, 5489, 5495, 5501, 5507, 5513, 5519, 5537, 5549, 5561, 5585.

---

## G. Secondary — `en` half diverges from the pt-BR half (9 records)

Reported at lower priority: `en` is the Layer-A source column, so where the two halves disagree one of
them is wrong and a reviewer trusting the pair gets no signal. In all nine the **pt-BR is the correct half**.

| idx | slug | jp | pt-BR (correct) | en (wrong) |
|---|---|---|---|---|
| 47 | gen-04b66ca1ccac | この紙の裏は白いです | "é branco" | "is **blank**" (白い = white; the record's own `translation_literal.en` says "white") |
| 1979 | gen-e429a7a204c9 | 行きたいけれど、… | "Eu queria ir" (present desire) | "I **wanted** to go" (past) |
| 2315 | jec-3829 | 心臓に毛が… | "Ele…" | "**You** have nerves of steel" |
| 2951 | tatoeba-124978 | 店員が「いらっしゃいませ」と言った。 | «Seja bem-vindo!» | "What can I do for you, sir?" — a different line from the record's own `translation_literal.en` ("Welcome") |
| 2987 | tatoeba-126322 | 虫でさえも… | "insetos" | "**worms**" |
| 3485 | tatoeba-165585 | 私たちは親を… | "nossos pais" | "**your** parents" (with "We should not") |
| 4697 | tatoeba-4888 | 外国人って面白いなあ。 | "Estrangeiros" | `translation_literal.en`: "As for **foreign countries**" |
| 4913 | tatoeba-76498 | なんだってずらからねえんだ！ | "não dá no pé" | `translation_literal.en`: "it won't **come off**" |
| 5687 | tatoeba-8883784 | 本当に行かなくちゃいけないの？ | "Você… tem que ir?" | `translation_literal.en`: "Do **I** really have to go" |

---

## Count table

| Class | Records flagged | Notes |
|---|---:|---|
| **A** — mistranslation / added-dropped meaning in `translation.pt-BR` | 5 | A1–A5 |
| **B** — unnatural pt-BR in `translation.pt-BR` | 9 | B1–B9; B8 is an orthographic error (`da` → `dá`) |
| **C1** — explanatory parentheses in `translation.pt-BR` | 9 | §5 field discipline |
| **C2** — gender-inclusive parentheses (house-style call) | 4 | not errors; ruling requested |
| **D1–D4, D6, D7** — individual `translation_literal.pt-BR` defects | 8 | polarity, aspect, unparseable pt, crase, self-contradiction |
| **D5** — systematic "Quanto a…" applied to non-は sentences | 43 | ~14 clearly wrong (が/を-marked); rest borderline |
| **E** — token `role` errors | 2 | both in the `reauthored` cohort |
| **F** — missing `en` half of locale-object | 62 | data completeness |
| **G** — `en` half diverges from pt-BR (secondary) | 9 | pt-BR is correct in all nine |
| **Distinct records flagged** | **144** | of 981 |
| **Distinct records flagged, excluding systematic classes D5 + F** | **41** | of 981 (~4.2%) |
| **Records checked** | **981** | index % 6 == 5 |

### Checks that came back clean
- **pt-PT leakage:** 0. A regex sweep for autocarro / comboio / telemóvel / pequeno-almoço / casa de banho /
  rapariga / ecrã / frigorífico / "estar a + infinitivo" over all `translation.pt-BR` and
  `translation_literal.pt-BR` in the slice returned one candidate — `[5171] tatoeba-79760`
  "está a ponto de amanhecer" — which is standard pt-BR ("a ponto de"), not a pt-PT gerund periphrasis.
  **No pt-PT leakage in this slice.**
- **Em dash (—) in pt fields:** 0 occurrences in `translation.pt-BR`, `translation_literal.pt-BR`, or any
  `tokens[].gloss.pt-BR`. §4 respected.
- **Register:** no case found of casual JP rendered formal or keigo rendered casual. Honorific/humble
  sentences (`[179]` 差し上げてください, `[845]` 御注文はお決まりですか, `[1319]` お待ちください,
  `[1757]` お出かけになりますか, `[2753]` おっしゃいますね, `[5711]` ご馳走させてください) all land on
  neutral-polite or "o senhor" pt-BR; casual/slang sentences (`[755]` "A mana tá no quarto, viu",
  `[2657]` "Compra um sorvete pra mim", `[3017]` "Vocês são egoístas, hein", `[4907]` "Não fica postando
  repetido, idiota") keep the casual register. Clean.
- **Token glosses (`tokens[].gloss.pt-BR`):** read for all 981 records; no gloss found that contradicts
  the token's meaning in context. The two defects located in the token layer are `role` values (class E),
  not glosses.
- **Counters, tense, polarity in `translation.pt-BR`:** clean. Counter sentences (`[23]` 二つずつ,
  `[107]` 五つ, `[359]` 四つ, `[1061]` 九つ, `[1133]` 三枚, `[1223]` 二百グラム, `[2015]` 三つずつ,
  `[4109]` １ページおきに, `[1451]` 一日おきに, `[3833]` 一行おきに, `[4973]` ２ポンド, `[5507]` ４点)
  all render the number, the counter class and the distributive/interval sense correctly.

---

## Suggested triage order

1. **D1** (`[4691]`) — polarity reversal; the literal teaches the opposite of the pattern.
2. **B8** (`[2525]`) — `da` → `dá`; one-character orthographic fix in learner-facing text.
3. **D5** — one scaffolding rule, mechanically applicable to 43 records; the biggest single source of
   mis-teaching in the slice.
4. **F** — 62 null `en` halves; mechanical, and it restores the reviewer's cross-check.
5. **A1–A5, B1–B7, B9** — individual judgment calls, one edit each.
6. **C, D2–D4, D6, D7, E, G** — cleanup.
