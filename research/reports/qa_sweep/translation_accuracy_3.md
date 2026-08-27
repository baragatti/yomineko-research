# QA sweep — translation accuracy, part 3/6

**Scope:** `corpus/sentences/bank.json`, records where `index % 6 == 2` — **982 records** (indices 2, 8, 14 … 5888).
**Checked:** `translation.pt-BR`, `translation_literal.pt-BR`, token `gloss` / `role` / `conjugation_note` (pt-BR),
particle `function` / `explanation` (pt-BR), against `jp` / `kana` / `tokens` / `particles`.
**Excluded by instruction:** `structure_explanation` (being re-authored elsewhere). Not reviewed.
**Style authority:** `design/translation_style.md`.

Every record in the slice was read in full. Findings below are only defects I can defend from the record's own
data; where a finding is systemic I also ran a script over the whole slice so the counts are exact, not sampled.

## Summary

The slice is in good shape at the sentence level: the natural pt-BR reads well, register generally tracks the
Japanese, and mechanical style checks come back clean — **zero** pt-PT leakage, **zero** em dashes, **zero**
`"Quanto a mim"` crutches in a `translation` field, **zero** empty pt-BR translations, **zero** generated
sentences carrying a stray `。`.

The defects that do exist are concentrated in **`translation_literal.pt-BR`**, not in the natural translation.
The literal field is being used inconsistently as a *teaching* field: the "Quanto a X" scaffolding that
`design/translation_style.md` §1 reserves for the topic particle は is applied to が, を, に and even to
conditional clauses, which destroys exactly the contrast the field exists to teach. That is finding F1 and it is
the highest-value item here.

Secondary clusters: the こ/そ/あ demonstrative system is mapped inconsistently into pt-BR (F3/F4), and 61 records
(6.2%) have an empty `translation.en`, so their pt-BR has no reference gloss to be checked against (F9).

---

## F1 — `translation_literal` applies the topic gloss "Quanto a X" to non-topic elements (34 records)

**Severity: high — this is the field's whole job, and it currently teaches the wrong thing.**

`design/translation_style.md` §1 makes "quanto a X" the designated literal rendering **for は**: *"Keep 'quanto a X'
for `translation_literal` and `structure_explanation` only, where the literal structure is the teaching point."*
In 34 records of this slice it is applied to elements marked by が, を or に, or to no particle at all. A learner
comparing 猫**が** and 猫**は** sees the same Portuguese scaffolding in both, so the literal field stops
distinguishing them.

Script result over the slice: 349 records use "Quanto a…" in `translation_literal.pt-BR`; 45 of those contain no
は particle at all. Of those 45, 34 are genuine misapplications (excluded as legitimate: `って` as colloquial
topic — [2492], [2498]; `に関して` — [4142]; explicitly bracketed/parenthesised hedges — [2654], [3026], [2888],
[3164]; `も`-topic — [3338], [2216]; comparative "quanto a" — [2864]; and [1046], where the literal is correct and
only the tokenizer lost the は).

### F1a — self-contradictory: the gloss names the particle as が/に and still calls it a topic (6 records)

| id | jp | current `translation_literal.pt-BR` |
|---|---|---|
| 32 `sent:gen-03a661610691` | 猫が尾を動かしている | `Quanto ao gato (が marca o sujeito), o rabo (を objeto), está mexendo.` |
| 470 `sent:gen-331aadac9315` | 犬が大きい声で鳴いた | `Quanto ao cachorro (が), com (で) voz grande/alta, latiu (passado).` |
| 1172 `sent:gen-860fa53a2427` | 子供たちが教室で騒いでいる | `Quanto às crianças (が = sujeito), na sala de aula (で = lugar da ação) elas estão fazendo barulho…` |
| 2264 `sent:jec-1144` | 彼が世界にひとつだけの人形を作る | `Quanto a ele (が), no mundo (に) só um (だけ の) boneco (を) faz.` |
| 650 `sent:gen-47deb23d74b8` | 母に早く元気になってほしい | `Quanto à mãe (に), cedo/logo (早く), saudável-tornar-se-e (なってほしい): quero que (ela) fique.` |
| 698 `sent:gen-4de483834275` | 正月に神社へお参りに行く | `Quanto ao Ano Novo (に), em direção ao santuário (へ), para a visita/oração (に), vou.` |

The parenthetical says "が marca o sujeito" and the prose says "Quanto ao…". One of the two is wrong, in the same
sentence.

**Fix:** use the pattern the corpus already uses correctly elsewhere — [1886] `sent:gen-d79e87cce16e` renders
お金がなかなか貯まらない as `Dinheiro (が, sujeito), não se acumula facilmente.` So: `O gato (が, sujeito), o rabo
(を, objeto), está mexendo.`; `À mãe (に), logo, ficar bem: quero que (ela) fique.`

### F1b — ungrammatical Portuguese produced by the misapplication (1 record)

- **[2324] `sent:jec-4456`** — jp `そこに僕がボールを投げる`
  current: `Ali (に), quanto a eu (が), a bola (を) jogar.`
  `"quanto a eu"` is not Portuguese; the preposition requires the oblique pronoun. Even if the topic gloss were
  correct here (it is not — 僕 is が-marked), it would have to be *"quanto a mim"*.
  **Fix:** `Ali (に), eu (が, sujeito), a bola (を), jogo.`

### F1c — を-marked objects glossed as topics (6 records)

| id | jp | current `translation_literal.pt-BR` | proposed |
|---|---|---|---|
| 632 `sent:gen-4590c1e65a70` | 電車を待っている間に本を読んだ | `…quanto ao livro, (eu) li.` | `…o livro (を, objeto), (eu) li.` |
| 644 `sent:gen-472a24c8a8b4` | 部屋を片付けてください | `Quanto ao quarto, faça o favor de arrumá-lo.` | `O quarto (を, objeto), arrume, faça o favor.` |
| 740 `sent:gen-52a2e8482686` | この本を読んだことがない | `Quanto a este livro, não existe a experiência de tê-lo lido.` | `Este livro (を, objeto), não existe a experiência de tê-lo lido.` |
| 746 `sent:gen-52f4094d4cf4` | この本を全部読んだ | `Quanto a este livro, li tudo.` | `Este livro (を, objeto), li tudo.` |
| 884 `sent:gen-61b2e6e51629` | お釣りを忘れないでください | `Quanto ao troco, não esquecendo, faça o favor.` | `O troco (を, objeto), não esquecendo, faça o favor.` |
| 5804 `sent:tatoeba-9628228` | 布団をしまいなさい。 | `Quanto ao futon, guarde-o (ordem com なさい).` | `O futon (を, objeto), guarde (ordem com なさい).` |

### F1d — remaining misapplications (21 records)

が-marked: **338**, **428**, **752**, **908**, **914**, **968**, **998**, **1334**, **1538**, **1796**, **2228**,
**2240**, **2252**, **2282**, **2288**, **2330**, **5792**.
に-marked: **5798**.
Bare adverbial / no particle: **1004**, **1238**.
Conditional clause: **716** — jp `急げば間に合うよ`, current `Quanto a (se) apressar-se, dá pra chegar a tempo, viu`
(a ば-conditional is not a topic; proposed: `Se (você) se apressar, dá pra chegar a tempo, viu`).

Note [5792] `sent:tatoeba-95724` uses the hyphenated variant — `Ela quanto-a daquele jeito mudou…` for 彼女**が** —
so any cleanup regex must catch `quanto-a` too.

---

## F2 — には rendered as ungrammatical `"Quanto a n…"` (3 records)

**Severity: medium — output is not grammatical Portuguese.**

| id | jp | current `translation_literal.pt-BR` |
|---|---|---|
| 44 `sent:gen-04494a7c911c` | この町には外国人が少なくない | `Quanto a nesta cidade, estrangeiros não são poucos.` |
| 1256 `sent:gen-909448ed583a` | 都には大きなお寺があります | `Quanto a na capital, grande templo (sujeito) existe.` |
| 2168 `sent:gen-fab58f2dfc37` | この市には大きい公園があります | `Quanto a nesta cidade, parque grande existe.` |

`"quanto a nesta"` / `"quanto a na"` stacks two prepositions. Portuguese does not allow it.

**Fix:** `Nesta cidade (には, tópico + lugar), estrangeiros não são poucos.` — or, if the topic framing must be
kept: `Quanto a esta cidade, nela os estrangeiros não são poucos.`

---

## F3 — その rendered as "aquele/aquela" (= あの), collapsing the こ/そ/あ contrast (10 records)

**Severity: medium — こそあど is an explicit N5 teaching point and these records contradict their own glosses.**

The corpus defines the three-way system in its own token glosses: at [68] その = `esse / essa (perto de você/do
ouvinte)`; at [260] / [2054] あの = `aquele/aquela (longe dos dois falantes)`. Ten records in this slice render
その as *aquele/aquela*, which is the あの slot. In eight of them `translation_literal` repeats the error, so both
layers agree on the wrong mapping.

| id | jp | current `translation.pt-BR` |
|---|---|---|
| 2414 `sent:tatoeba-103062` | 彼は先週そのお寺をたずねるつもりだった。 | `…visitar **aquele** templo na semana passada.` |
| 3074 `sent:tatoeba-13902229` | その子は早くから話せるようになった。 | `**Aquela** criança começou a falar cedo.` |
| 3428 `sent:tatoeba-159903` | 私はその悲しい知らせを受けて… | `…ao receber **aquela** notícia triste.` |
| 3830 `sent:tatoeba-190560` | 一週間後にそのＣＤを返すよ。 | `Eu te devolvo **aquele** CD daqui a uma semana.` |
| 4118 `sent:tatoeba-208173` | その男とつきあってはいけないよ。 | `…se envolver com **aquele** homem.` |
| 4124 `sent:tatoeba-208758` | その人は死にかけていた。 | `**Aquela** pessoa estava morrendo.` |
| 4160 `sent:tatoeba-212666` | そのふるい橋をわたるのは危ない。 | `Atravessar **aquela** ponte velha é perigoso.` |
| 4166 `sent:tatoeba-213031` | そのスーツは彼によく合います。 | `**Aquele** terno fica bem nele.` |
| 4922 `sent:tatoeba-76619` | その女の子は木登りが大好きだった。 | `**Aquela** menina adorava subir em árvore.` |
| 5840 `sent:tatoeba-98277` | 彼らは２日でその古い建物を壊すでしょう。 | `…demolir **aquele** prédio velho…` |

Contrast: [488] `sent:gen-353c01dbf76e` renders その店 correctly as `Essa loja é muito barata.`

**Fix:** その → *esse/essa*; reserve *aquele/aquela* for あの. Update the matching `translation_literal` in the eight
records where it repeats the error.

---

## F4 — この/これ rendered "esse/essa/isso" while the same record's literal and gloss say "este/esta/isto" (16 records)

**Severity: low — defensible colloquially, but it is an internal contradiction inside each record.**

In pt-BR speech *esse* routinely covers *este*, so the natural translation is not wrong on its own. The problem is
that in all 16 records the same record's `translation_literal` and its この token gloss say *este/esta*, so the two
layers a learner reads side by side disagree.

Records: **92**, **266**, **566**, **878**, **1220**, **1592**, **1910**, **2252**, **2372**, **2576**, **2594**,
**2606**, **4286**, **4490**, **5030**, **5276**.

Example — [92] `sent:gen-0a34fc285d38`, jp `このお酒はアルコールが強い`:
`translation` = `Essa bebida tem um teor alcoólico alto.` / `translation_literal` = `Quanto a **esta** bebida (お酒)…`

**Fix:** pick one convention and apply it. Recommendation: この → *este/esta* in both layers, so the three-way
contrast with F3 stays visible; the colloquial *esse* is what should be reserved for その.

---

## F5 — English word left untranslated inside the pt-BR fields (1 record)

**Severity: medium.** This is the only English leakage in the whole slice.

**[296] `sent:gen-2044754669fc`** — jp `コーヒーは片仮名で書きます`
- `translation.pt-BR` = `"Coffee" a gente escreve em katakana.`
- `translation_literal.pt-BR` = `Quanto a 'coffee', em katakana se escreve.`

The topic is the Japanese loanword コーヒー. Quoting the **English** word inside a Brazilian-Portuguese sentence
leaves the learner with a false premise (that the word being written in katakana is English "coffee" rather than
the loanword itself), and it is a straight copy from the `en` field.

**Fix:** `translation` → `A palavra "café" (コーヒー) a gente escreve em katakana.`;
`translation_literal` → `Quanto a コーヒー ("café"), em katakana se escreve.`

---

## F6 — particle explanation describes a different sentence (1 record)

**Severity: medium — the explanation is simply about another sentence.**

**[1556] `sent:gen-b2ed6e8bb267`** — jp `車を外国から輸入する会社です`
`particles[から].explanation.pt-BR` =
`から em それから marca o ponto a partir do qual segue a próxima ação ('depois disso, em seguida').`

There is no それから in this sentence. The から here is 外国**から** = source/origin ("from abroad"), which is what
the sentence's own `translation_literal` says (`Carro (objeto) do exterior importar empresa é.`). The explanation
appears to have been carried over from a それから record (cf. [2702], [4106], [4742], which legitimately explain
それから).

**Fix:** `から marca 外国 como a origem: os carros vêm de fora. É o から de procedência, o mesmo de 東から (a partir
de).`
This record also has empty `translation.en` and `translation_literal.en` (see F9).

---

## F7 — counter over-translated: 〜つ rendered as "pares" (1 record)

**Severity: medium — counters are a graded teaching point and this one is taught wrong.**

**[1982] `sent:gen-e481d334d6c3`** — jp `白い靴下を二つ買いました`
`translation.pt-BR` = `Comprei **dois pares** de meias brancas.`

二つ is the generic 〜つ counter. The record's own data contradicts the translation: the つ token gloss reads
`(contador genérico de unidades)` and `translation_literal.pt-BR` reads `Meias brancas (objeto を), dois (contador
つ), comprei (passado polido).` "Pares" would require 二**足** (にそく). As written, a learner is taught that
二つ = "dois pares".

**Fix (pick one):**
- keep the jp, change the pt: `Comprei duas meias brancas.`; or
- if "pares" is the intended meaning, change the jp to `白い靴下を二足買いました` and re-derive the tokens/counter gloss.

---

## F8 — one record contradicts itself twice (1 record)

**Severity: medium.**

**[4280] `sent:tatoeba-2211172`** — jp `そのレストランは1階にある`
- `translation.pt-BR` = `**Esse** restaurante fica no **térreo**.`
- `translation_literal.pt-BR` = `Quanto **àquele** restaurante, no **1º andar** existe.`

Two independent mismatches inside one record:
1. その is *Esse* in the translation and *àquele* in the literal (the F3/F4 problem, both directions at once).
2. 1階 is *térreo* in the translation and *1º andar* in the literal. For a Brazilian reader these are **different
   floors** — "1º andar" is the level above the térreo. The translation is the correct one; the literal actively
   teaches the wrong floor.

**Fix:** `translation_literal` → `Quanto a esse restaurante, no térreo (1階) existe.`

---

## F9 — 61 records have an empty `translation.en` (6.2% of the slice)

**Severity: medium (data completeness, not a pt-BR error).**

`design/i18n.md` treats `en` as the Layer-A source alongside pt-BR. In 61 of 982 records `translation.en` is an
empty string, and in 57 of those `translation_literal.en` is empty too — so the pt-BR text in those records has no
reference gloss for a reviewer (or a validator) to check it against.

All 61 are `translation_confidence: 0.8` records: 60 Tatoeba-mined ones (`tags: mined,stage:`, `jp_source: tatoeba`
without an id) plus **[1556]** (`tags: reauthored`, `jp_source: generated`).

Ids: 1556, 4256, 4448, 4652, 4658, 4748, 4766, 4820, 4826, 4832, 4880, 4922, 4928, 4940, 4970, 4988, 5012, 5018,
5030, 5054, 5066, 5102, 5108, 5114, 5144, 5162, 5192, 5198, 5222, 5228, 5240, 5246, 5270, 5306, 5312, 5330, 5354,
5366, 5378, 5390, 5450, 5456, 5462, 5474, 5480, 5486, 5492, 5498, 5504, 5510, 5522, 5528, 5540, 5546, 5552, 5564,
5570, 5582, 5594, 5774.
(4256, 4448, 4658, 5774 have `translation.en` empty but `translation_literal.en` filled.)

**Fix:** backfill `en` for the mined batch before the human review pass, or mark these records so a reviewer knows
the pt-BR is unverified against a source gloss.

---

## F10 — pt-BR and en disagree about *who* is speaking, inside the same record

**Severity: medium for the three hard cases, low for the rest.**

### Hard — the `en` is wrong or unrelated (3 records)

- **[2234] `sent:jec-0453`** — jp `僕はカーテン越しに海を見た`
  `pt-BR` = `Olhei o mar através da cortina.` (correct: 僕 = *I*)
  `en` = `He looked at the sea through the curtains.` — 僕 is first person; the `en` is a person error.
- **[4610] `sent:tatoeba-373351`** — jp `こんにちは。`
  `pt-BR` = `Boa tarde.` / `en` = `Welcome.` — but the same record's `translation_literal.en` reads
  `Good afternoon. / Hello.` The `en` field contradicts its own literal.
- **[4622] `sent:tatoeba-4216208`** — jp `バカみたい。`
  `pt-BR` = `Que ridículo.` (impersonal) / `en` = `I feel like a fool.` (1st person) /
  `translation_literal.en` = `[He] seems an idiot.` (3rd person). Three different subjects in one record.

### Soft — subject-less Japanese, pt and en simply chose differently (5 records)

[2372] *eu* vs *you*; [3254] *Eu devia* vs *You should*; [3314] *Precisamos* vs *You must*; [3560] *brincamos* vs
*I played*; [3932] *Tenho que ir* vs *We have to go*. Each is individually defensible, but a reviewer reading both
locales side by side gets contradictory information.

**Fix:** fix the three hard cases; for the soft ones, agree one policy (e.g. pt-BR follows the `en` subject when
the `en` came from Tatoeba) and apply it.

---

## F11 — evidential/semblance marker dropped from the natural translation (2 records)

**Severity: medium for [938] — it changes what the sentence asserts.**

- **[938] `sent:gen-68e272881a09`** — jp `彼女は嬉しそうに笑いました`, tag `generated:grammar,sou-ni-sou-na`
  `translation.pt-BR` = `Ela riu feliz.`
  〜そうに asserts *appearance*, not the internal state — that is precisely why Japanese requires そう for a third
  person's emotion. `Ela riu feliz` asserts that she *was* happy. The record's own literal keeps it
  (`de modo parecendo-feliz`), and the corpus keeps it elsewhere: [1220] `Esse bolo **parece** delicioso, né?`,
  [326] `Mãos frias que **parecem** gelo.`
  **Fix:** `Ela riu com um ar contente.` / `Ela riu parecendo feliz.`
- **[1118] `sent:gen-7ec782cb2980`** — jp `夢みたいな話だね`, tag `generated:grammar,mitai-na`
  `translation.pt-BR` = `É uma história de sonho, né?` — flattens みたい ("parece / tipo") into a fixed phrase, and
  in pt-BR "história de sonho" reads as *wonderful*, not *unreal*. Literal keeps it (`Sonho-parecida história`).
  **Fix:** `Parece história de sonho, né?`

---

## F12 — mistranslations / meaning shifts (6 records)

- **[200] `sent:gen-165aa62de165`** — jp `私はコーヒーが弱いです`
  `translation.pt-BR` = `Eu não aguento café.`
  In pt-BR *"não aguento X"* reads first as *dislike* ("I can't stand X"), not as low physical tolerance. The
  record's own `translation_literal.en` spells out the intended sense: `I am sensitive (it affects me strongly)`.
  **Fix:** `Eu sou fraco pra café.` or `Café me faz mal.`

- **[560] `sent:gen-3c3ee014e7ed`** — jp `道を交番で聞いた`
  `translation.pt-BR` = `Perguntei o caminho na **delegacia**.`
  交番 is a neighbourhood police box, not a police station (警察署). The record's own token gloss hedges
  (`posto policial (delegacia de bairro)`), and elsewhere in this same slice [2204] `sent:gen-ff5971e6a7c2`
  renders 交番 correctly as `posto policial`. As written the vocab item is taught with the wrong referent.
  **Fix:** `Perguntei o caminho no posto policial.`
  Related, lower severity — **[1112] `sent:gen-7e663ffa89a0`**, jp `お巡りさんに道を聞いた`: `translation` says
  `para o **guarda**` while `translation_literal` says `Ao **policial**`. In pt-BR *guarda* reads as a
  municipal/traffic guard. Align both on *policial*.

- **[86] `sent:gen-09a0580e98f9`** — jp `ゆっくり滑降してください`, tag `generated:vocab,1223`
  `translation.pt-BR` = `Desça devagar.`
  Two losses: (a) the vocab focus 滑降 (downhill ski descent) disappears entirely — the same vocab id 1223 is
  rendered properly in the other two sentences of this slice, [530] `Esquiar na descida é muito divertido` and
  [674] `gosto de descer esquiando na montanha`; (b) 〜てください becomes a bare imperative, while every other
  〜てください in the slice keeps the politeness ([56] `Espere uns trinta minutos, **por favor**`, [182]
  `Feche a janela, **por favor**`, [788] `Cole o papel na porta, **por favor**`).
  **Fix:** `Desça a encosta devagar, por favor.`

- **[2090] `sent:gen-f15f45a64b4a`** — jp `雨の日は本当につまらない`
  `translation.pt-BR` = `Em dias de chuva fico entediado de verdade.`
  つまらない predicates *the days*, not the speaker; the sentence has no experiencer. The record's own literal is
  right: `Quanto aos dias de chuva, são realmente sem graça.` pt-BR has the identical construction available, so
  the shift is unforced.
  **Fix:** `Dia de chuva é muito chato mesmo.`

- **[452] `sent:gen-316308c1849e`** — jp `お店で好きなレコードを買った`
  `translation.pt-BR` = `Comprei na loja um disco de vinil que eu gostava.`
  Two problems: 好きな is non-past (an ongoing preference), rendered here as an imperfect past *gostava*; and
  *gostar* is regido by *de* — "um disco **que** eu gostava" drops the preposition (colloquially frequent, but
  non-standard, and this is learner-facing model text).
  **Fix:** `Comprei na loja um disco de vinil de que eu gosto.` or `…um disco de vinil que eu curto.`

---

## F13 — 店 translated as "loja" but predicated with "a comida" (2 records)

**Severity: low.**

- **[932] `sent:gen-68448be6940b`** — jp `あの店は安くはないが おいしい`
  `pt-BR` = `Aquela **loja** não é barata, mas **a comida** é gostosa.` (`en` says *restaurant*)
- **[1052] `sent:gen-7586c0111a3c`** — jp `あの店は安いしおいしい`
  `pt-BR` = `Aquela **loja** é barata e ainda por cima **a comida** é gostosa.` (`en` says *shop* + *the food*)

In pt-BR a *loja* does not serve comida, so the sentence pictures something incoherent. Also note both add
"a comida", which the Japanese does not have (おいしい predicates 店 directly).

**Fix:** `Aquele restaurante não é barato, mas a comida é boa.` / `Aquele restaurante é barato e ainda por cima a
comida é gostosa.` — or drop "a comida" and keep "loja".

---

## F14 — nonstandard `"desde de manhã"` (2 records, 3 fields)

**Severity: low.**

- **[1628] `sent:gen-bb1b606982b5`** — jp `朝から首がとても痛い`
  `translation.pt-BR` = `Meu pescoço está doendo muito **desde de manhã**.`
  `particles[から].explanation.pt-BR` = `から indica desde quando a dor existe (**desde de manhã**).`
- **[410] `sent:gen-2d194443db15`** — `particles[から].explanation.pt-BR` = `…'a partir da manhã / **desde de manhã**'.`

*"desde de"* stacks two prepositions and is a stigmatised error in written pt-BR. The same record [410] gets the
translation right (`Não comi nada **desde cedo**.`), so the corpus already has the correct form.

**Fix:** `desde cedo` or `desde a manhã` (`desde de manhã` → `desde a manhã`).

---

## F15 — number disagreement between `translation` and `translation_literal` (4 records)

**Severity: low.** Japanese is number-neutral, so neither reading is wrong — but the two pt-BR layers of the same
record should not disagree.

| id | `translation.pt-BR` | `translation_literal.pt-BR` |
|---|---|---|
| 326 `sent:gen-23bdff9ed0ca` | `**Mãos** frias que parecem gelo.` | `**Mão** fria tipo gelo…` |
| 590 `sent:gen-3f09454ea7ac` | `**Os pássaros** vão voando para o sul.` | `**O pássaro** (sujeito)…` |
| 596 `sent:gen-406d0d8f43f5` | `Espero **meus amigos** na frente da escola…` | `…espero **o amigo**.` |
| 1436 `sent:gen-a5d68ff4012f` | `Tomei banho com **as crianças**.` | `Com **a criança** (子どもと)…` |

---

## F16 — literal contradicts its own token gloss (1 record)

**Severity: low.**

**[668] `sent:gen-4a22c783f8ef`** — jp `どうもありがとうございました`
`translation_literal.pt-BR` = `**De algum modo** (どうも), obrigado (foi) (forma passada polida).`

The record's own どう token gloss reads `muito, de verdade (intensificador de agradecimento)`, and the も particle
explanation says どうも `dá o sentido de 'realmente, muito'`. "De algum modo" is an etymological reading that is
wrong in this context and contradicts both.

**Fix:** `Muito (どうも) obrigado (forma passada polida).`

---

## Borderline — inspected and *not* flagged

Recorded so the human reviewer does not re-litigate them:

- **[2216] `sent:jec-0071`** 誰もが → `Quanto a todos (sem exceção)…`; **[3338]** 私も → `Quanto a mim também`.
  も is topic-like; the gloss is acceptable.
- **[2888]**, **[3164]**, **[2654]**, **[3026]** — "Quanto a" appears but is explicitly bracketed or marked as an
  implicit/alternative reading. Acceptable.
- **[1046] `sent:gen-74ea68439313`** お釣りはいりません — flagged by my script only because Sudachi merged は+要り
  into はいる (a Layer-A tokenisation defect, out of scope here). The literal `Quanto ao troco, não (é) necessário.`
  is **correct**.
- **[848]** `perrengue`, **[1196]** `Mande um abraço`, **[212]/[506]** keigo → neutral-polite pt: register
  compression is sanctioned by `translation_style.md` §2. Not flagged.
- **[20]**, **[1598]**, **[2636]** and similar — an invented third-person subject where the Japanese has none. In
  most cases the `en` (Tatoeba source) licenses it; not flagged individually, but it is the same root cause as F10.
- **[3062]** 大きすぎるわ → `É alto demais.` — ambiguous between *tall* and *loud* without context; pt and en agree
  on *loud*, so accepted.
- **[5426]**, **[3098]**, **[1826]**, **[2348]**, **[4868]** — inspected, judged within tolerance.

---

## Mechanical checks (whole slice, scripted)

| check | result |
|---|---|
| pt-PT lexical leakage (autocarro, comboio, telemóvel, rapariga, ecrã, casa de banho, frigorífico, …) | **0** |
| pt-PT progressive `estar a + infinitivo` | **0** |
| em dash `—` in any pt-BR field | **0** |
| `"Quanto a mim"` inside a `translation` field (banned by style §1/§4) | **0** |
| empty `translation.pt-BR` | **0** |
| `translation` identical to `translation_literal` | **0** |
| generated (`jp_source: ai-generated`) sentences ending in `。` (banned by style §3) | **0** |
| English words inside `translation.pt-BR` / `translation_literal.pt-BR` | **1** (F5, id 296) |

Slice composition, for context: 368 `ai-generated`, 21 `jec:#*`, ~592 `tatoeba*`, 1 `generated` (reauthored).
Levels: n4 384, n3 332, n2 97, n1 89, n5 80.

---

## Count table

| class | severity | records flagged | ids |
|---|---|---|---|
| F1 topic gloss "Quanto a X" on non-topic (が/を/に/bare/conditional) | high | **34** | 32, 338, 428, 470, 632, 644, 650, 698, 716, 740, 746, 752, 884, 908, 914, 968, 998, 1004, 1172, 1238, 1334, 1538, 1796, 2228, 2240, 2252, 2264, 2282, 2288, 2324, 2330, 5792, 5798, 5804 |
| F2 には → ungrammatical "Quanto a n…" | medium | **3** | 44, 1256, 2168 |
| F3 その → "aquele/aquela" (should be あの) | medium | **10** | 2414, 3074, 3428, 3830, 4118, 4124, 4160, 4166, 4922, 5840 |
| F4 この/これ → "esse/essa/isso" vs own literal/gloss | low | **16** | 92, 266, 566, 878, 1220, 1592, 1910, 2252, 2372, 2576, 2594, 2606, 4286, 4490, 5030, 5276 |
| F5 English left in pt-BR | medium | **1** | 296 |
| F6 particle explanation for a different sentence | medium | **1** | 1556 |
| F7 counter 〜つ over-translated as "pares" | medium | **1** | 1982 |
| F8 record self-contradictory (demonstrative + floor) | medium | **1** | 4280 |
| F9 empty `translation.en` (no reference gloss) | medium | **61** | see F9 list |
| F10 pt/en subject disagreement (3 hard, 5 soft) | medium / low | **8** | 2234, 4610, 4622 / 2372, 3254, 3314, 3560, 3932 |
| F11 そう/みたい evidential dropped | medium / low | **2** | 938, 1118 |
| F12 mistranslation / meaning shift | medium | **6** | 86, 200, 452, 560, 1112, 2090 |
| F13 店 "loja" predicated with "a comida" | low | **2** | 932, 1052 |
| F14 `"desde de manhã"` | low | **2** | 410, 1628 |
| F15 number disagreement translation vs literal | low | **4** | 326, 590, 596, 1436 |
| F16 literal contradicts own token gloss | low | **1** | 668 |

| total | |
|---|---|
| records checked | **982** |
| distinct records flagged (any class) | **148** |
| — of which, translation-layer defects | **90** |
| — of which, `translation.en` completeness only | **58** (61 minus 3 that also carry a translation defect) |
| clean records | **834** |

Overlaps counted once in the totals: 1556 (F6+F9); 2252 (F1+F4); 2372 (F4+F10); 4922, 5030 (F3/F4 + F9).

**Highest-value single fix:** F1. It is 34 records, mechanically detectable, and it is the one defect that makes
the corpus teach the wrong grammar rather than merely reading awkwardly. F3 is the second: it is small, and it
protects an N5 teaching point the corpus already documents correctly in its own token glosses.
