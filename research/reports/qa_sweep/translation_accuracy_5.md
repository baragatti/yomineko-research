# QA sweep — translation accuracy, slice 5/6

**Scope:** `corpus/sentences/bank.json`, records where `index % 6 == 4` (981 records, index 4 → 5884).
**Checked:** `translation["pt-BR"]` against `jp` (meaning, register, tense, polarity, counters, who-does-what);
`translation_literal["pt-BR"]` as a literal gloss; token `gloss`/`role`/`conjugation_note` and particle
`function` in pt-BR as supporting evidence.
**Explicitly excluded:** `structure_explanation` (being re-authored elsewhere).
**Authority:** `design/translation_style.md`.

Every record in the slice was read in full. Findings below are only defects I can defend against the
Japanese, the record's own `en` sibling fields, or a sibling record in the same slice that handles the
same construction differently. Where a fix is proposed it is a concrete replacement string.

---

## A. Meaning defects in `translation["pt-BR"]`

### A1 — `[1390] sent:gen-9f80f08cc644` — 辛い on miso mistranslated as "picante"
- JP: `この味噌はちょっと辛いです`
- pt-BR: **"Esse missô é um pouco picante."**
- Why wrong: applied to 味噌, 辛い is the "salty / sharp" sense, not the chilli sense. The record contradicts
  itself: `translation_literal["en"]` says **"it is a little salty"** while `translation["en"]` and the pt-BR
  say "spicy / picante". The `辛い` token note itself hedges ("picante, apimentado/salgado").
- Fix: `translation["pt-BR"]` → **"Esse missô é um pouco salgado."** (and align `translation["en"]` to "salty").

### A2 — `[694] sent:gen-4d34ac970423` — 丁寧な日本語 → "um japonês cuidadoso" is ambiguous and off-sense
- JP: `先生は丁寧な日本語を話します`
- pt-BR: **"O professor fala um japonês cuidadoso."**
- Why wrong: in pt-BR "um japonês cuidadoso" reads first as *a careful Japanese man*, not *careful Japanese
  language*. 丁寧な日本語 means polite/formal register Japanese; the record's own `translation_literal["en"]`
  says **"polite Japanese"**.
- Fix: **"O professor fala um japonês bem educado (formal)."**

### A3 — `[3784] sent:tatoeba-188422` — silent unit substitution マイル → "quilômetros"
- JP: `屋上からは、何マイルも見渡せる。`
- pt-BR: **"Do terraço dá para ver a quilômetros de distância."**
- Why wrong: the JP says miles; `translation["en"]` says "for miles"; `translation_literal["pt-BR"]` says
  "milhas e milhas"; the token gloss says "milha(s)". The natural translation converts the unit and so
  contradicts three sibling fields. It is also inconsistent within this slice: `[3730]` ("meia milha") and
  `[5596]` ("dez milhas") both keep the unit.
- Fix: **"Do terraço dá para enxergar a milhas de distância."**

### A4 — `[3718] sent:tatoeba-184376` — subject flipped relative to the aligned English
- JP: `学校へ行くところでした。`
- pt-BR: **"Eu estava a caminho da escola."** / en: **"He was going to school."**
- Why wrong: the JP is subject-less, but the paired Tatoeba English (the Layer-A source for this record)
  names a third-person subject. The corpus resolves it as first person in pt and third person in en, so the
  two locales tell the learner different things. Compare `[3664] sent:tatoeba-179594`, where the same
  subject-less shape is correctly resolved as "(Ele) trabalha em um banco" to match its en.
- Fix: **"Ele estava a caminho da escola."**

### A5 — `[1216] sent:gen-8bb700989955` — お兄さん rendered as "meu irmão", against the slice's own convention
- JP: `お兄さんは大学生です`
- pt-BR: **"Meu irmão mais velho é universitário."**
- Why wrong: the お〜さん honorific normally points at the listener's / a third party's relative; one's own
  older brother in a statement to someone else is 兄 (as in `[334]`, `[646]`, `[1666]`, all rendered
  "meu irmão mais velho"). This slice already treats the parallel お嬢さん as second person: `[1054]`
  → "A sua filha é universitária?" and `[1336]` → "Quantos anos a sua filha tem?".
- Fix: **"O seu irmão mais velho é universitário."** (or change the JP to `兄は大学生です` if the first-person
  reading is what the lesson wants). Teacher decision, but the two readings must not both be in the corpus.

### A6 — `[1576] sent:gen-b52a7720dd00` — 食堂 near a station rendered "refeitório"
- JP: `駅の近くに食堂がある`
- pt-BR: **"Perto da estação tem um refeitório."**
- Why wrong: in pt-BR a "refeitório" is an in-house canteen (school/company), not a public eatery. A 食堂
  near a station is a cheap restaurant. The paired `translation["en"]` says "cafeteria", which fits the
  school context of `[2548]` ("Eu já almocei no refeitório", correct there) but not this one.
- Fix: **"Perto da estação tem um restaurante simples."**

### A7 — `[58] sent:gen-063c2aa13494` — 店 rendered "loja" in a sentence about food
- JP: `この店は高いけれども おいしい`
- pt-BR: **"Essa loja é cara, mas a comida é gostosa."**
- Why wrong: "loja" plus "a comida" is internally incoherent in pt-BR (a loja does not serve comida). The
  record's own `translation["en"]` says **"This restaurant..."**, and the sibling `[496] sent:gen-3612bfffc506`
  (`この店は安いしおいしい`) correctly renders 店 as **"Esse restaurante"**.
- Fix: **"Esse restaurante é caro, mas a comida é gostosa."**

### A8 — `[2224] sent:jec-0240` — アルバイト → "bico": register drop and semantic shift
- JP: `多くの学生が、アルバイトをします` (neutral-polite ます)
- pt-BR: **"Muitos estudantes fazem bico."**
- Why wrong: "fazer bico" is colloquial pt-BR for an irregular odd job; アルバイト is a regular part-time job,
  and the source register is neutral-polite. `translation["en"]` says "have part-time jobs"; the token gloss
  itself lists "trabalho de meio período" first. Per `translation_style.md` §2 the pt tone should mirror the
  JP politeness.
- Fix: **"Muitos estudantes trabalham meio período."**

---

## B. Unnatural pt-BR / register in `translation["pt-BR"]`

### B1 — `[3658] sent:tatoeba-179257` — ungrammatical contraction, calque word order
- pt-BR: **"O sapato estar apertado é por causa de o pé estar inchado, né."**
- Why wrong: `de o` must contract to `do`; and the fronted infinitive clause is a calque of のは. This is the
  only `de o` / `em a` failure in the natural-translation field in the whole slice.
- Fix: **"O sapato está apertado porque o seu pé inchou, né."**

### B2 — `[370] sent:gen-281142d1729a` — self-contradicting phrase
- pt-BR: **"Desculpa por chegar atrasado na hora marcada."**
- Why wrong: one does not arrive late *at* the appointed time; in pt-BR the reference point takes "para" or
  is dropped altogether.
- Fix: **"Desculpa pelo atraso, cheguei depois da hora combinada."**

### B3 — `[64] sent:gen-072d9927b41d` — "escrever letras"
- pt-BR: **"Meu pai é ruim em escrever letras."**
- Why wrong: 字を書くのが下手 is about handwriting. "escrever letras" is not idiomatic pt-BR and loses the point.
- Fix: **"Meu pai é ruim de escrever à mão (a letra dele é feia)."**

### B4 — `[1672] sent:gen-c058146d69ad` — calque of 〜たいと思っている
- pt-BR: **"Estou pensando que quero ser enfermeira."**
- Why wrong: 〜たいと思う is a softener, not a report of an inner thought; the pt-BR calque is clunky.
- Fix: **"Estou pensando em ser enfermeira."**

### B5 — `[1282] sent:gen-930f360c27d7` — "estrada de neve"
- pt-BR: **"Escorreguei na estrada de neve e caí."**
- Why wrong: "estrada de neve" reads as a road *made of* snow. 雪の道 is a snow-covered path.
- Fix: **"Escorreguei no caminho coberto de neve e caí."**

### B6 — `[826] sent:gen-5b980fff719c` — "como parabéns"
- pt-BR: **"Ganhei flores como parabéns pela aprovação."**
- Why wrong: flowers are not given "as congratulations" in pt-BR; お祝いに is an occasion/purpose marker.
- Fix: **"Ganhei flores para comemorar a aprovação."**

### B7 — `[838] sent:gen-5cae43f7a7c5` — tautology
- pt-BR: **"Esse doce é muito doce."**
- Why wrong: 菓子 / 甘い collapse onto the same pt-BR word; the sentence reads as a joke rather than a model
  sentence. The token gloss already offers "guloseima".
- Fix: **"Essa guloseima é muito doce."**

### B8 — `[4924] sent:tatoeba-76720` — "tenho meio período" does not parse
- pt-BR: **"Desculpa. Amanhã eu tenho meio período logo de manhã, viu."**
- Why wrong: "meio período" is a work *schedule*, not a thing one "has" on a given morning.
- Fix: **"Desculpa. Amanhã eu trabalho logo de manhã (é o meu meio período), viu."**

### B9 — `[1138] sent:gen-82262f543d42` — bureaucratic register
- pt-BR: **"Meu irmão mais novo cresceu em relação ao ano passado."**
- Why wrong: "em relação a" is administrative pt-BR; `translation["en"]` says "since last year".
- Fix: **"Meu irmão mais novo cresceu desde o ano passado."**

### B10 — `[442] sent:gen-309e4c467821` — 便利 → "conveniente" for a town
- pt-BR: **"Esta cidade é tranquila e ainda é bem conveniente."**
- Why wrong: pt-BR "conveniente" means *appropriate/expedient*, not *handy/well-served*. Note `[1006]` renders
  the same 便利 correctly as "prática".
- Fix: **"Esta cidade é tranquila e ainda por cima bem prática."**

### B11 — `[1768] sent:gen-cb6474f5cede` — participle agreement, inconsistent with sibling
- pt-BR: **"Peguei emprestado três livros."**
- Why wrong: "emprestado" must agree ("emprestados"), and the natural order puts the object first. The sibling
  `[1834] sent:gen-d106c508d77a` (`辞書を一冊借りました`) gets it right: "Peguei um dicionário emprestado."
- Fix: **"Peguei três livros emprestados."**

### B12 — `[5854] sent:tatoeba-99201` — slash alternative inside a learner-facing translation
- pt-BR: **"Ele estudou/preparou a matéria com antecedência."**
- Why wrong: the natural-translation field should commit to one rendering; alternatives belong in
  `translation_literal` or the vocab gloss. This is the only `/` in the natural field across all 981 records
  in the slice, so it is a one-off, not a house style.
- Fix: **"Ele preparou a matéria com antecedência."**

---

## C. `translation_literal["pt-BR"]` defects

The literal field is the learner's scaffolding for particle structure, so a broken or misleading literal
teaches the wrong mapping. Items C1 to C6 are outright ungrammatical or garbled Portuguese.

### C1 — `[2164] sent:gen-fa090f27e750` — missing contraction
- lit: **"Em a sala de aula, quanto a cadeiras, em número de nove, existem."**
- Fix: **"Na sala de aula, cadeiras, em número de nove, existem."** (see also C12 on the "quanto a" here)

### C2 — `[2950] sent:tatoeba-1249725` — two missing contractions, word salad
- lit: **"Dentro-da-fábrica de o incêndio de a notícia, o mundo/público fez alvoroçar."**
- Fix: **"A notícia do incêndio dentro da fábrica pôs o público em alvoroço."**

### C3 — `[1594] sent:gen-b733c5be99cb` — 背 mis-glossed as "costas" inside 背が高い
- lit: **"Dentro da turma, quanto a ele, a altura das costas é a mais alta."**
- Why wrong: in 背が高い, 背 is stature, not the back. "altura das costas" is meaningless in pt-BR. The same
  word is correctly glossed "estatura" in `[334]` and `[1138]` in this slice.
- Fix: **"Dentro da turma, quanto a ele, a estatura é a mais alta."**

### C4 — `[2350] sent:tatoeba-10050538` — garbled
- lit: **"Marido quanto-a, geralmente às 8 horas no(-é-que) ao-trabalho a sai (educado)."**
- Fix: **"Quanto ao marido, geralmente às 8 horas (é que) sai para o trabalho."**

### C5 — `[2422] sent:tatoeba-10342236` — ungrammatical and reverses the experiencer
- lit: **"Quanto a uma pessoa não acostumada de ver, ela está rondando ao redor da casa, viu."**
- Why wrong: `acostumada de ver` is ungrammatical (needs `a ver`), and 見慣れない人 is a person *one is not used
  to seeing*, not a person who is not used to seeing.
- Fix: **"Uma pessoa que não se está acostumado a ver está rondando ao redor da casa, viu."**

### C6 — `[2086] sent:gen-f09d275f2a19` — glossed the verb twice, "Quanto a (=existe)" is nonsense
- lit: **"Quanto a (=existe) alojamento para o bem de estudante de intercâmbio, existe."**
- Fix: **"Alojamento para o bem de estudante de intercâmbio (が) existe."**

### C7 — `[1246] sent:gen-8ee16ccc288c` — slash-fragment format, one fragment broken
- lit: **"Quanto a isto / eu (de) / bolsa / não é."**
- Why wrong: no other literal in the slice uses slash-separated fragments, and "eu (de)" is not readable.
- Fix: **"Quanto a isto, bolsa de mim não é."**

### C8 — `[2326] sent:jec-4666` — invented topic plus a duplicated copula
- lit: **"Quanto a (isto), o sabor profundo (が) é a característica (é)."**
- Fix: **"O sabor profundo (が) é a característica."**

### C9 — `[1990] sent:gen-e550b112cef4` — "Quanto a dentro da turma" is not Portuguese
- lit: **"Quanto a dentro da turma, ele (sujeito) número um de altura é alto."**
- Fix: **"Dentro da turma (で), ele (が) é o número um em altura."**

### C10 — `[2062] sent:gen-edd547874d80` — pt-PT-flavoured verb government
- lit: **"Quanto a [se] pegar no expresso, chega cedo/rápido."**
- Why wrong: pt-BR is "pegar o expresso"; "pegar no" for boarding is pt-PT. (`design/i18n.md` / `translation_style.md`
  §4 forbid pt-PT.) The natural translation of this same record already says "pegar o expresso" correctly.
- Fix: **"Se pegar o expresso (に), chega mais cedo."**

### C11 — `[2890] sent:tatoeba-123027` — 二度と mis-glossed as "duas vezes mais"
- lit: **"Duas-vezes-mais matemática-de livro (objeto) esquecer-quanto-a não-pode."**
- Why wrong: 二度と with a negative means "never again"; "duas vezes mais" means the opposite ("twice more").
  The record's own particle note for と already says "('nunca mais')".
- Fix: **"Nunca mais, o livro de matemática (を), esquecer não pode."**

### C12 — topic scaffolding "Quanto a X" applied to non-topic phrases (6 records)
`translation_style.md` reserves the "quanto a X" mirror for the topic structure. In these six records it is
attached to an を-marked object, a が-marked subject, or to a topic that does not exist in the JP at all,
which teaches the learner the wrong particle mapping. (Records where "quanto a" glosses a real は or a
colloquial って topic are correct and are **not** listed.)

| idx | slug | jp | current literal fragment | problem |
|---|---|---|---|---|
| 100 | gen-0b2679ac5ee0 | 古い書類をデータ化しています | "Quanto a documentos antigos (objeto), ..." | を marked, yet labelled both "quanto a" and "(objeto)" |
| 436 | gen-2fef8f85a304 | 卵を七つ買いました | "Quanto a ovos (objeto), sete unidades, comprei." | same contradiction |
| 850 | gen-5db83dd74419 | 作業を自動化したい | "Quanto ao trabalho (objeto), ..." | same contradiction |
| 448 | gen-30f6535979a3 | 飛行場で友達を待っている | "No aeroporto, quanto a (eu), o amigo, ..." | invents a topic "(eu)" absent from the JP |
| 1582 | gen-b5e592aada0f | 明日の天気をネットで調べた | "Quanto a [eu], o tempo de amanhã, ..." | invents a topic "[eu]" absent from the JP |
| 2224 | jec-0240 | 多くの学生が、アルバイトをします | "Quanto a (isto), muitos (の) estudantes (が), ..." | invents a topic "(isto)" absent from the JP |

Fix pattern: drop the "quanto a" frame and keep the case label only, e.g. `[436]` →
**"Ovos (を), sete unidades, comprei."**; `[448]` → **"No aeroporto (で), o amigo (を), estou esperando."**

---

## D. Locale-parity gap (data completeness)

### D1 — 59 records in this slice have an empty `translation["en"]`
`translation["en"]` is `None` in 59 of the 981 records, and `translation_literal["en"]` is `None` in 57 of
those. The gap is concentrated in the tail (index ≥ 4660, all `tatoeba` sourced) plus one generated record.
Since `en` is the Layer-A source locale per `CLAUDE.md`, these records lose their cross-check anchor and any
future locale added has nothing to validate against.

Examples: `[1522] sent:gen-aef805c4840d`, `[4660] sent:tatoeba-4770`, `[4744] sent:tatoeba-5118`,
`[5236] sent:tatoeba-80376`, `[5548] sent:tatoeba-84639`.

Full index list (59): 1522, 3766, 4378, 4660, 4702, 4744, 4756, 4846, 4870, 4876, 4894, 4930, 4966, 4972,
4978, 4996, 5002, 5008, 5020, 5032, 5044, 5074, 5080, 5092, 5098, 5104, 5134, 5140, 5146, 5152, 5158, 5188,
5224, 5236, 5242, 5248, 5254, 5260, 5272, 5302, 5332, 5380, 5392, 5440, 5452, 5458, 5464, 5470, 5476, 5482,
5488, 5494, 5500, 5506, 5512, 5518, 5530, 5542, 5548.

(`[3766]` and `[4378]` have an `en` literal but no `en` natural translation, so they are half-populated
rather than empty.)

---

## Clean areas (stated explicitly)

The following checks came back with **zero** findings across all 981 records, and I am recording that as a
result rather than silence:

- **pt-PT leakage in `translation["pt-BR"]`:** none. A 41-pattern scan (comboio, autocarro, telemóvel, casa de
  banho, rapariga, ecrã, frigorífico, facto, registo, "estar a + infinitivo", vosotros-style forms, etc.)
  returned only false positives ("apanhar do chão" for 拾う, "miúdo" for 細かい, "giro-giro" for ぐるぐる,
  "pegou no sono" for 寝つく, all valid pt-BR). The single pt-PT-flavoured item found is C10, and it is in the
  literal field, not the natural translation.
- **Em dash (—) in `translation` or `translation_literal`:** zero occurrences, per `translation_style.md` §4.
- **"Quanto a / falando de" leaking into the natural `translation` field:** zero. The one regex hit (`[4264]`,
  "não é tão interessante quanto aquele livro") is the comparative "tão... quanto", not the topic mirror.
- **`translation` identical to `translation_literal`:** zero, so the two fields are genuinely doing different
  jobs everywhere in the slice.
- **Empty pt-BR `translation` / `translation_literal`:** zero.
- **Empty pt-BR token `gloss` on a content-bearing POS** (noun/verb/i-adj/na-adj/adverb/pronoun): zero.
- **Counters and numerals:** every counter sentence checked rendered the count correctly (七つ→sete, 五冊→cinco,
  三台→três, 二匹→dois, 三億円→trezentos milhões de ienes, 一千万円→dez milhões de ienes, ３０分おき→a cada 30
  minutos). No off-by-one or magnitude error found.
- **Polarity:** every negative, double-negative and restrictive construction checked came out with the right
  sign, including the harder ones (`[3922]` 違えないことはめったにない → "É raro o Bill chegar na hora.",
  `[1726]` 彼いがい誰も知りません → "Ninguém sabe, só ele.", `[3436]` これだけしか知りません → "Eu só sei isto.").

---

## Count table

| Class | What | Records checked | Records flagged |
|---|---|---:|---:|
| A | Meaning defect in `translation["pt-BR"]` (mistranslation, dropped/added meaning, wrong referent, unit swap) | 981 | 8 |
| B | Unnatural pt-BR / wrong register in `translation["pt-BR"]` | 981 | 12 |
| C | Defective `translation_literal["pt-BR"]` (broken pt, wrong gloss, wrong particle scaffolding) | 981 | 17 (12 findings; C12 covers 6 records) |
| D | Locale-parity gap (`translation["en"]` empty) | 981 | 59 (1 aggregate finding) |
| — | pt-PT leakage in `translation["pt-BR"]` | 981 | 0 |
| — | Em dash in translation fields | 981 | 0 |
| — | Topic mirror ("quanto a") leaking into natural `translation` | 981 | 0 |
| — | Empty pt-BR translation / literal / content-token gloss | 981 | 0 |
| — | Counter / numeral errors | 981 | 0 |
| — | Polarity errors | 981 | 0 |

**Totals:** 981 records checked; **33 distinct findings** touching **90 records** (8 + 12 + 17 + 59, with
`[2224]` counted once in A and once in C12).

Priority for the teacher queue: A1, A3, A4, A5, A7 first (they make the corpus say two different things in
two places, so they cannot be resolved by taste), then C1 to C6 and C11 (broken or actively wrong
scaffolding), then B and the rest of C, then D as a batch backfill.
