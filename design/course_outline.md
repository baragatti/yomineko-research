# Course Outline (DRAFT) — Module → Topic → Lesson

> **Draft skeleton (Phase R / R6).** Finalized in **P4**, where *every* reconciled N5/N4 item is assigned to
> exactly one introducing lesson and the i+1 cumulative-known-set is computed. Sequencing applies the
> [`PLAN_REVIEW`](PLAN_REVIEW.md) decisions D8 (register-explicit, ます-default + dictionary-early; particles
> front-loaded; て-form mid-N5; katakana right after hiragana) and D9 (families organize; i+1/frequency drive
> introduction). It is built to be a **superset of the Phase L concept map** and to fix its
> [gaps](../research/local-course-insights/gaps_to_beat.md): pitch accent present, JLPT-mapped, katakana early,
> time/date vocab early, adjectives earlier, casual↔polite integrated, spiral review.
>
> Titles shown to learners are **pt-BR**; structural notes are English. Per-lesson chunk target: **3–5 grammar /
> 15–25 vocab / 5–10 kanji** (these caps are **per lesson**), wrapped in **recognição → drill → produção →
> can-do**. Two recurring callouts run throughout: **💡 Vantagem PT** and **⚠ Armadilha PT**.
>
> **Topic numbering (standardized):** the CANONICAL topic id/order is **GLOBAL** and continuous —
> pré-N5 = 1–6, N5 = 7–19, N4 = 20–35 (this is what `course/outline.json`, the `topic-NN-*` dirs,
> `grammar_placement.json`, and STATE use). The `TNN` labels in *this doc* are **within-module** for readability:
> **N5 T01 = global topic-07 … te-form T09 = topic-15; N4 T01 = topic-20 … T16 = topic-35**. When any doc says
> "topic 15" it means the GLOBAL number.
>
> **Data model + unlocks:** the courseware ships as a layered manifest (entry → course → topic → lesson) where
> each lesson declares `needs` (prerequisites) and `unlocks` (kana families, vocab, kanji, grammar, conjugation
> forms, phrases, app **features**, SRS decks) from a closed global enum — see
> [`courseware_architecture.md`](courseware_architecture.md) + `unlock_enums.json`. **Strict linearity:** a lesson
> uses only items unlocked earlier; the ONLY exception is the kana-bootstrap words (kana-only) in T02/T03
> ([`kana.md`](kana.md)). Completing a lesson enrolls its items' cards into FSRS (deck = skill type).

---

## MÓDULO 0 — Fundamentos (pré-N5) — *from absolute zero*
**Completion criteria (not dataset-listable, N):** reads/writes both kana fluently; produces the mora rhythm,
vowel length, ん, and devoiced です/ます; knows ~40 survival words/phrases; understands how to study (SRS habit).
**Production goal:** *Ao final, o aluno lê e escreve hiragana e katakana, pronuncia com ritmo de mora, e se
vira em saudações e apresentações básicas.*

- **T00 — Boas-vindas e como aprender** — orientation; the SRS/retrieval habit; "ler romaji ≠ português" one-pager; how kana/kanji will be weaned. *(2 lessons)*
- **T01 — Os sons do japonês e as vantagens do português** — 5 vowels (closely matching, not 1:1); mora as a beat; intro to pitch (awareness); 💡 the soft-r tap, ち/じ affrication. *(3 lessons)*
- **T02 — Hiragana** — **one gojūon FAMILY per lesson** ("Família do A/KA/SA/…", then vozeamento GA/ZA/DA/BA/PA,
  yōon, っ, vogais longas). Each lesson unlocks that `kana-family`; the first unlocks `feat:srs-reviews` +
  `deck:kana-hiragana`. From ~2 families on, 2–4 **SRS-bootstrap words** (kana-only, no grammar/sentences) — *PLANNED, not yet implemented (deferred)* — would seed
  the first reviews. Full plan: [`kana.md`](kana.md). *(~14–18 family lessons)*
- **T03 — Katakana** — *immediately after hiragana* (D8); same per-family structure, faster (system already
  known); loanword hook (パン/タバコ/コップ — 💡); ー long mark; ⚠ false friends + u-epenthesis. *(~12–15 lessons)*
- **T04 — Pronúncia e ritmo** — mora-clapping; vowel-length minimal pairs by meaning (おじさん/おじいさん); ん as its own mora (⚠ não nasalizar a vogal anterior); devoiced です/ます ("dess/mass"); っ timing. *(3 lessons)*
- **T05 — Saudações e sobrevivência** — greetings by time of day, ありがとう/すみません/ください, はい/いいえ, はじめまして self-intro; 💡 você→o senhor intuition previewing teineigo. *(3 lessons)*

---

## MÓDULO 1 — N5
**Production goal:** *Ao final, o aluno se apresenta, fala de rotina/tempo/dinheiro/compras/comida, faz pedidos
e perguntas simples no registro polido (です/ます), e lê 80 kanji.* Covers the reconciled N5 set (80
kanji, ~700+ vocab, ~name the N5 grammar points), frequency-ordered, i+1-paced.

> Topic order is dependency-correct (D8). Families (D9) are noted per topic; their governing rule is taught when
> first needed. Particles front-load across T01–T05.

### T01 — Frases básicas: o tópico は e o copula です
Families: `particle_set` (は,も,の), `contrast_pair` (は↔が, seeded). Key: X は Y です / ですか / じゃ ないです;
これ/それ/あれ; の (posse); も. ⚠ ausência de artigos; ⚠ partícula vem *depois* do substantivo. Kanji: 一二三…日本.
**Can-do:** *dizer quem é, o que é algo, e fazer perguntas sim/não.* *(3–4 lessons)*

### T02 — Perguntas e demonstrativos
Key: 何/誰/どこ/いつ; この/その/あの + N; ここ/そこ/あそこ; か (ou). Family: `function_set` (interrogativos).
**Can-do:** *perguntar "o que/quem/onde/quando".* *(2–3 lessons)*

### T03 — Números, horas e datas  *(moved early — fixes Phase L gap)*
Key: 0–9999, 〜時/〜分/〜曜日, 今日/明日/昨日, ～円 (dinheiro), counter intro ひとつ–とお + 〜人/〜枚. Families:
`semantic_field` (tempo), `function_set` (contadores; 💡 fallback ひとつ/ふたつ; ⚠ contador escolhido pela forma).
Kanji: 月火水木金土日, 時, 円, 百千万. **Can-do:** *dizer horas, datas, preços e contar objetos básicos.* *(4 lessons)*

### T04 — Verbos: forma de dicionário + ます; partículas を e が
Families: `conjugation_class` (godan, ichidan, irregular する/来る — governing rule taught here), `particle_set`.
Key: 3 verb groups; **dict form AND ます together** (D8); non-past polite +/−; を (objeto direto); が; SOV order
(⚠ verbo no fim — drill reordenando frases PT). Kanji: 行く/来る/見る/食べる/飲む/する radicals. **Can-do:** *descrever
ações no presente polido.* *(4–5 lessons)*

### T05 — Lugar, tempo e direção: で / に / へ / と; existência ある・いる
Key: ある/いる; に (lugar de existência / tempo / destino), へ (direção), で (lugar da ação / meio), と (com / e).
Completes the "~8 particles ≈ 90% usage" cluster. **Can-do:** *dizer onde algo está, para onde vai e com quem.*
*(4 lessons)*

### T06 — Passado polido e nuances
Key: でした / 〜ました / 〜ませんでした; から〜まで; sentence-final ね / よ. **Can-do:** *falar do passado e marcar
ênfase/confirmação.* *(3 lessons)*

### T07 — Adjetivos い e な
Families: `conjugation_class` (i-adj, na-adj). Key: present/past, affirm/neg; adj+N; 好き/嫌い/上手/下手 + が
(⚠ "objeto" marcado por が). Kanji: 大小高安新古. **Can-do:** *descrever pessoas, coisas e gostos.* *(4 lessons)*

### T08 — Comparações, desejos e preferências
Key: 〜より, 一番, 〜のほうが, どちら; 〜たい (querer fazer); 〜が ほしい (querer ter). **Can-do:** *comparar e dizer
o que quer.* *(3 lessons)*

### T09 — A forma て e seus usos  *(the hinge — mid-N5, not late)*
Family: `grammar` cluster around て. Key: て-form formation (all groups); 〜てください; 〜ています (progressivo/estado);
〜てもいいです; 〜ては いけません. ⚠ contrações casuais como preview. **Can-do:** *pedir, descrever ações em curso e
falar de permissão/proibição.* *(4–5 lessons)*

### T10 — Convites, sugestões e habilidade
Key: 〜ましょう / ましょうか / ませんか; 〜ことが できる (habilidade); 〜から (razão). **Can-do:** *convidar, sugerir e
dizer o que consegue fazer.* *(3 lessons)*

### T11 — Rotina, frequência e advérbios
Families: `semantic_field` (rotina diária), `function_set` (advérbios de frequência). Key: 毎日/毎週, よく/ときどき/
たまに/あまり/ぜんぜん; sequência (それから, つぎに). **Can-do:** *descrever a própria rotina.* *(3 lessons)*

### T12 — Conectando ideias e opiniões
Key: 〜から / 〜ので (razão); 〜が / 〜けど (contraste); 〜と 思います; 〜と 言います (citar). **Can-do:** *justificar,
contrastar e dar opinião simples.* *(3 lessons)*

### T13 — Revisão N5 e consolidação can-do
Interleaved review (は/が, transitivos, kanji parecidos, contadores), mock can-dos, JLPT-N5-style check. *(2 lessons)*

---

## MÓDULO 2 — N4
**Production goal:** *Ao final, o aluno usa a forma simples e o registro casual, forma orações relativas e
condicionais, fala de habilidade/intenção/experiência, dar-e-receber, voz passiva/causativa e keigo básico —
suficiente para situações de trabalho e vida cotidiana no Japão.* *(Lesson-level breakdown finalized in P4.)*

| # | Tópico | Famílias / foco | Pontos-chave | Can-do |
|---|--------|-----------------|--------------|--------|
| T01 | Forma simples e registro casual | conjugation classes (plain) | plain não-passado/passado/neg; casual ↔ polido (integra o que o curso-base separava) | alternar registro conscientemente |
| T02 | Orações relativas | clause-embedding | [oração simples] + N | descrever substantivos com frases |
| T03 | Condicionais | contrast set たら/ば/と/なら | quatro condicionais e contrastes | falar de hipóteses e condições |
| T04 | Potencial | conjugation (potential) | 〜られる/〜える "conseguir" | dizer o que é capaz/possível |
| T05 | Volitivo e intenção | volitional family | 〜よう/おう; つもり; 〜ようと 思う | expressar intenção e planos |
| T06 | Transitivos × intransitivos | derivational pairs (あく/あける…) | pares + partículas | escolher o verbo/partícula certos |
| T07 | Dar e receber | giving/receiving set | あげる/くれる/もらう; 〜てあげる/くれる/もらう | falar de favores e trocas |
| T08 | Experiência e mudança | aspect/change | 〜た ことが ある; なる; 〜ように なる | falar de experiências e mudanças |
| T09 | Obrigação e permissão | obligation set | 〜なければ ならない / 〜なくても いい; 〜なくちゃ | falar de deveres e permissões |
| T10 | Tentar, preparar, completar | てみる/ておく/てしまう | aspecto e nuance | nuançar ações |
| T11 | Aparência e suposição | evidential set | 〜そう/よう/らしい/みたい; でしょう/だろう | inferir e supor |
| T12 | Voz passiva | passive | 〜れる/られる passiva | descrever do ponto de vista do paciente |
| T13 | Causativa e causativa-passiva | causative | 〜させる; 〜させられる | fazer/deixar alguém fazer |
| T14 | Keigo básico | politeness layers | teineigo review; sonkeigo/kenjōgo intro (💡 você/o senhor → camada nova honesta) | registro formal de trabalho |
| T15 | Conectores avançados | connective set | のに, 〜ても, 〜ば〜ほど, 〜ように | encadear ideias complexas |
| T16 | Revisão N4 e can-do | interleaved | revisão geral + mock JLPT N4 | consolidação |

---

## Functional contexts woven across N5–N4 (for living/working in Japan)
self-introduction · numbers/time/dates · **money & shopping** · **food & restaurants** · directions & transport
· daily routine · family · **work basics & registers** · health/emergency · **forms, signs & typing** (the
literacy tasks Marugoto drops). Each becomes the *theme* of one or more topics and the source of can-do tasks.

## Parallel literacy strand (kanji)
Runs from N5 T03 onward (D8/D11): **component-first, semantic-radical-led**, frequency-ordered, pt-BR mnemonics,
each new kanji recombining known components; bound to vocab the learner is already meeting; KanjiVG stroke order
for handwriting exercises. 80 kanji by end of N5, 250 (N5+N4) by end of N4.

## Pronunciation strand (pt-BR specific)
The phonology priority list (D10) threads through every module: mora+length → even moras → u-epenthesis/[ɯ] →
ん-as-mora → です/ます devoicing → っ; pitch present in audio from day 1, systematic pitch at N4+.

> **DRAFT status:** topic counts and lesson splits are indicative; P4 binds every reconciled item to an
> introducing lesson, computes the cumulative-known-set, and validates i+1 (≤1 new grammar/lesson where feasible).
