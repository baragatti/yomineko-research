# Curriculum — methodology synthesis & design rules (P3)

> Original synthesis (nothing copied) translating the verified Phase R2 research into **concrete, checkable
> design rules** the build obeys. Sources: [`curricula_sequencing`](../research/references/curricula_sequencing.md),
> [`sla_evidence`](../research/references/sla_evidence.md), [`brpt_pedagogy`](../research/references/brpt_pedagogy.md),
> [`brazil_market`](../research/references/brazil_market.md) (each carries its own citations). Decisions are
> fixed in [`PLAN_REVIEW`](PLAN_REVIEW.md) (D7–D11, Part 6). Learner-facing terminology is **pt-BR** (Appendix B
> glossary at the end). This file governs P4 (outline), P5 (sentence selection/i+1), and P6 (lesson authoring).

## 1. The learning engine (what the design is built on)
The strongest, most-replicated mechanisms come first; the SLA *hypotheses* are heuristics, not foundations.
1. **Retrieval practice** (very strong evidence) → reviews **test/produce**, never re-show. Each new item is
   retrieved ≥3–4× in week 1. Metacognition is unreliable → the system schedules, not the learner.
2. **Spacing** (very strong) → introduce → ~D1 → D3 → D7 → D16 → D35+ (gap ≈ 10–20% of the target horizon);
   guarantee a **prompt, successful first review**; don't fetishize aggressive expansion.
3. **Comprehensible input as a content constraint** (not a theory): every authored text ≥**95%** known tokens
   (ideally ~98%). This is how we operationalize "i+1" — measured against the cumulative-known-set (P4), not
   the loose Krashen formula.
4. **Pushed output** (moderate evidence, central to our speaking goal): ≥1 production task per lesson, supported
   + immediate feedback.
5. **Encoding boosters always wrapped in retrieval+spacing:** dual coding (one *relevant* image), pt-BR keyword
   mnemonics (on-ramp only), component-first kanji.
6. **Interleaving for discrimination:** introduce blocked, consolidate interleaved — for confusable Japanese
   sets (は/が, transitive/intransitive, look-alike kanji, counters, length minimal pairs).

## 2. Sequencing rules (P4 must satisfy all)
- **Register-explicit, ます-default + dictionary-form-early** (D8): from the first verb lesson show *both* the
  dictionary form (conjugation engine + lookup form) and ます (the polite register learners actually speak);
  teach politeness as a first-class early concept. Beats Minna's ~18-lesson plain-form delay and Tae Kim's
  casual-first bluntness.
- **Particle front-loading** across the first ~3 units: **は, も, の → を, が → で, に, へ, と, から/まで**
  (~8 particles ≈ 90% of usage).
- **て-form mid-N5** (it unlocks ~half of N4: てください, ている, てもいい, てはいけない) — not late.
- **Katakana right after hiragana** (loanwords/menus/signs are high-utility from day one in Japan).
- **Adjectives earlier**, time/date/money vocab **early** (fix Phase L gaps); **plain↔polite integrated** (not
  split into a separate product).
- **Dependency-correctness is a hard gate:** never teach a structure before its prerequisite (no て-clauses
  before て-form, no relative clauses before plain past, no comparatives before adjectives).
- **Families organize; i+1/frequency order introduction (D9):** a family enters incrementally — its core
  member when due by frequency, its governing rule when first needed, the rest spiral in later. **Conflict
  rule: i+1 wins for *introduction*, families win for *grouping/review*.**

## 3. Chunk sizes & the within-lesson ladder
- Per lesson: **3–5 new grammar / 15–25 new vocab / 5–10 new kanji** (cap nearer 15 vocab in the first units).
- **Ladder (every lesson):** recognition input (audio/reading of the target in context) → "porquê"
  explanation (Tae-Kim-style clarity) → controlled drill → substitution drill → semi-free mini-dialogue →
  **one can-do task** = the lesson's success criterion.
- **Worked → faded → free (recovered research):** within the drill rung, progress from fully-worked examples →
  **faded / completion problems** (partially-filled, learner completes the rest) → free production. Apply
  **expertise reversal**: early lessons lean on worked dissections; mature items shift to retrieval/production +
  SRS. Explanation:practice order/ratio is **tunable by content type** (an RCT found order isn't decisive) — don't
  over-prescribe. Cited: `research/deep-research-courseware.md`.
- **Daily SRS micro-review:** ~5–15 spaced items, separate from new-lesson load.
- **Spiral:** every lesson re-surfaces vocab/grammar from the previous 2–3 lessons in its examples/tasks.

## 4. Kanji strand (component-first, semantic-led)
- Order: **component/radical → kanji → vocabulary**; each new kanji mostly recombines known components.
- **Lead with semantic radicals** (most reliable inferential value); phonetic components as a *secondary* aid
  (useful for our phonographic-L1 learners, but unreliable — not the primary lever).
- pt-BR mnemonic + one relevant image per kanji; KanjiVG stroke order enables handwriting practice (a market
  gap — incumbents drop handwriting).
- Bind kanji to vocab the learner is already meeting in the communication strand; ~100 kanji by end of N5,
  245 by end of N4.

## 5. Brazilian-Portuguese pedagogy (named feature: "Vantagens / Armadilhas do português")
**Phonology priority sequence** (the pronunciation thread, in order):
1. **Mora + vowel length** (highest leverage): mora = a clapped beat; long vowel ≈ 2× (drill minimal pairs by
   meaning: おじさん/おじいさん).
2. **Even moras / no Portuguese stress-hammer** (pitch ≠ loudness).
3. **u-epenthesis + compressed [ɯ]/[ʉ]** (insert *u* not *i*; don't round/protrude lips).
4. **ん as its own mora** (don't nasalize the preceding vowel BP-style).
5. **Devoiced です/ます** ("dess/mass") as the default from lesson 1 (keep the timing slot).
6. **っ** folded into mora-clapping.
- **💡 Vantagem PT** callouts: 5-ish matching vowels, the soft-r tap (の of *caro*, not English R), ち/じ
  affrication (dialect-variable — freebie for many), você/o senhor → teineigo on-ramp.
- **⚠ Armadilha PT** callouts: vowel length, stress, /i/-epenthesis, nasal vowels, romaji misreading
  (já=[ʒ]≠じ, -e not→[i], soft-r, no final-vowel raising), false-friend loanwords (マンション≠mansion).
- **Loanword hook lesson** early (pan/tabako/koppu/kappa/tenpura/karuta — Portuguese-origin gairaigo).
- **Counters** as spaced-repetition vocabulary (not grammar); explicit early permission to fall back on
  ひとつ/ふたつ for 1–9.
- **Keigo:** map teineigo (です/ます) to the *você/o senhor* intuition; defer sonkeigo/kenjōgo to N4+ honestly.

## 6. Romaji & pitch policy (owner decisions)
- **Romaji: store BOTH** kana and romaji everywhere so the app can toggle, or run **romaji-first until the
  learner can drop it** (even showing romaji on lookup). A "ler romaji ≠ português" one-pager precedes kana.
- **Pitch accent: gather the data** (annotate vocab where available); **present in audio later** (audio
  deferred). At N5, teach pitch *selectively* (high-frequency minimal pairs + awareness); systematic pitch at
  N4+ — framed around **intelligibility, not native perfection**.

## 7. Production goals per module
- **pré-N5:** lê/escreve kana; ritmo de mora + comprimento vocálico + ん + devozeamento; ~40 palavras/frases de
  sobrevivência; sabe estudar (hábito de revisão espaçada).
- **N5:** apresenta-se; fala de rotina/tempo/dinheiro/compras/comida; faz pedidos e perguntas no registro
  polido (です/ます); lê ~100 kanji; produz frases SOV simples corretas.
- **N4:** usa forma simples + registro casual; orações relativas, condicionais, potencial, intenção,
  experiência, dar-e-receber, passiva/causativa, keigo básico — suficiente para trabalho/vida no Japão.

---

## Appendix — Glossário pt-BR de termos gramaticais (uso consistente em todo o corpus)
> Cada termo é introduzido na primeira vez que aparece numa lição; este é o vocabulário-padrão do curso.

| Termo (pt-BR) | Significado | Japonês / exemplo |
|---|---|---|
| **partícula** | palavra curta que marca a função de outra na frase; vem **depois** dela | は, を, が, に, で |
| **tópico** | "quanto a / falando de" — o tema já conhecido da frase | marcado por は |
| **sujeito** | quem pratica a ação (info nova) | marcado por が |
| **objeto direto** | o que recebe a ação | marcado por を |
| **transitivo / intransitivo** | verbo que pede objeto / que não pede | 開ける (abrir) / 開く (abrir-se) |
| **forma de dicionário** | forma base do verbo (a que se procura no dicionário) | 食べる, 飲む |
| **forma ます (polida)** | registro educado padrão | 食べます |
| **forma て** | forma conectiva (liga ações, pedidos, estado) | 食べて |
| **forma simples / casual** | registro informal | 食べる / 食べた |
| **verbo godan (う) / ichidan (る) / irregular** | classes de conjugação | 飲む / 食べる / する・来る |
| **adjetivo い / な** | duas classes de adjetivos | 高い / 静かな |
| **contador** | sufixo de contagem escolhido pela forma/categoria | 〜本, 〜人, 〜枚 |
| **oração relativa** | frase que descreve um substantivo, **antes** dele | 私が食べたパン |
| **condicional** | "se / quando" | 〜たら, 〜ば, 〜と, 〜なら |
| **potencial** | "conseguir / poder fazer" | 食べられる |
| **volitivo** | "vamos / vou (intenção)" | 食べよう |
| **voz passiva / causativa** | "ser feito" / "fazer alguém fazer" | 〜られる / 〜させる |
| **keigo (teineigo / sonkeigo / kenjōgo)** | linguagem honorífica (polida / respeitosa / humilde) | です・ます / なさる / いたす |
| **mora** | unidade rítmica (um "tempo"); cada kana + ー, っ, ん | か・ん・じ = 3 moras |
| **acento de altura (pitch)** | proeminência por **altura** (não por força) | 箸 vs 橋 |
| **on'yomi / kun'yomi** | leitura sino-japonesa / leitura japonesa | ショク / た.べる |
| **okurigana** | kana que acompanha o kanji na conjugação | 食**べる** |
| **furigana** | leitura em kana escrita sobre/ao lado do kanji | 食(た)べる |
| **rendaku** | sonorização da consoante inicial em compostos | ほん→ぼん (三本) |
| **radical / componente** | parte recorrente que forma um kanji | 言 em 話/語/読 |
