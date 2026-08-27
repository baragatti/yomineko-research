# QA sweep — grammar accuracy, slice 3/4

**Assignment:** `corpus/grammar/*.json`, records where `index % 4 == 2` over the concatenated n5 + n4 + n3
order. **124 records checked** (n5 38, n4 53, n3 33), every field read in full: `label`, `forms`,
`structure_pattern`, `explanation` (pt-BR + en), `formation` (pt-BR + en), `formation_steps`,
`steps_unavailable`, `nuance`, `caution`, `related`, `refs`, `families`, `level_*`. Each point was
cross-checked against up to 4 sentences in `corpus/sentences/bank.json` carrying its `key`.

Sentence `structure_explanation` fields were **not** reviewed (excluded by instruction).

**Headline:** the highest-severity class — a formation rule that would teach learners to *produce* wrong
Japanese — came back almost clean. I traced every `formation_steps` variant in the slice by hand
(`to-nai-stem`, `to-te-form`, `to-potential`, `to-passive`, `to-causative`, `to-volitional`,
`to-conditional-ba`, `to-ta-form`, `to-masu-stem`, `replace-ending`) and **all of them produce the correct
surface form**; the `to-nai-stem` convention (= ない-form minus final い) is applied consistently across all
13 records that use it. Two records fail on the prose side: one has the pt-BR formation of a *different
grammar point* pasted into it (F1), and one carries a noun rule that generates ungrammatical Japanese (F2).

---

## F1 — CRITICAL — `gram:naide`: the pt-BR formation belongs to a different grammar point

- **Record:** `gram:naide` (id 103, n5, key `naide`) — "fazer algo sem fazer outra coisa / em vez de (〜ないで)"
- **Field:** `formation["pt-BR"]`
- **Exact current text:**
  > Basta acrescentar なあ ao fim de uma frase ou palavra: いいなあ ("ah, que bom... / que inveja..."), 寒いなあ ("nossa, que frio"), 食べたいなあ ("ah, como eu queria comer..."), 来ればいいなあ ("tomara que venha"). É a partícula な esticada para soar mais emotiva; na escrita aparece como なあ ou só な.

- **Why it is wrong:** this is the formation of `gram:naa` (n5, key `naa`, the emphatic sentence-final
  particle なあ), copied verbatim except for one added ellipsis. It has nothing to do with 〜ないで. A pt-BR
  learner opening this point is told that 〜ないで is built by appending なあ. Everything else in the record is
  correct — the `explanation`, the `nuance` (the ないで/なくて contrast), the `formation_steps`
  (`to-nai-stem` + `いで` → 食べないで), and the `formation["en"]`:
  > Take the verb in the short negative form (the ない-form) and add で: 食べる→食べない→食べないで; 行く→行かない→行かないで; する→しない→しないで; くる→こない→こないで. The structure is: Verb[ない] + で + (main clause).

  So the defect is an isolated field-level paste, and pt-BR is the only locale affected — i.e. the *only*
  locale the course actually ships.
- **Proposed fix** — mirror the (correct) EN field:
  > Pegue a forma negativa curta do verbo (forma ない) e acrescente で: 食べる→食べない→食べないで; 行く→行かない→行かないで; する→しない→しないで; くる→こない→こないで. A estrutura é: Verbo[ない] + で + (oração principal).
- **Detection note for the pipeline:** comparing the set of Japanese substrings in `formation["pt-BR"]` vs
  `formation["en"]` gives Jaccard 0.00 here, against ≥ 0.42 for every other record in the slice. That check is
  cheap and would catch this class registry-wide.

## F2 — HIGH — `gram:n3-koto-wa-ga`: the noun rule generates ungrammatical Japanese

- **Record:** `gram:n3-koto-wa-ga` (id 383, n3) — "até que é..., mas (ことは…が)"
- **Field:** `formation` (both locales)
- **Exact current text (pt-BR):**
  > Repete-se o predicado em volta de ことは: verbo casual + ことは + verbo + が; adjetivo-い + ことは + adjetivo-い + が; adjetivo-な + な + ことは + adjetivo-な + だが; substantivo + ことは + substantivo + だが.

- **Why it is wrong:** the last clause instructs `substantivo + ことは + substantivo + だが`, which yields
  ×学生ことは学生だが. A noun cannot sit directly before こと here; it needs である (or the copular
  paraphrase). The verb, い-adjective and な-adjective lines are all correct — only the noun line is broken.
- **The corpus already knows.** This record's own `steps_unavailable` says, verbatim:
  > "Separately, the record's noun line omits である and would license *学生ことは学生だが; it needs human repair before any encoding is attempted."

  The machine-readable side was correctly withheld; the learner-facing `formation` was never repaired. That
  gap is the actual finding — a note in `steps_unavailable` is not visible to a learner or a teacher reviewing
  the point.
- **Aggravating:** this record has **zero** example sentences in the bank (see F13), so nothing in the corpus
  contradicts the bad rule.
- **Proposed fix:** replace the noun line with
  `substantivo + であることは + substantivo + だが (ex.: 学生であることは学生だが)`, and add the common
  colloquial alternative `学生は学生だが`. Mirror in `en`.

## F3 — HIGH — `gram:gp-6`: 帰る and 走る filed under the "-aru/-uru/-oru" rule they contradict

- **Record:** `gram:gp-6` (id 75, n5) — "verbos る (ichidan): formas básicas"
- **Field:** `nuance` (both locales)
- **Exact current text (pt-BR):**
  > Nem todo verbo terminado em る é る-verbo. Vários terminam em -aru/-uru/-oru e são う-verbos (ある, 分かる, 帰る, 走る, este último uma exceção "disfarçada"). A regra do som -i/-e antes de る ajuda, mas há exceções que você aprende com o tempo.

- **Why it is wrong:** 帰る is *kaeru* (-eru) and 走る is *hashiru* (-iru). Neither ends in -aru/-uru/-oru, so
  both are counterexamples to the rule they are listed as examples of. Only 走る gets the "disguised
  exception" caveat; **帰る is listed unqualified**, so a learner concludes 帰る ends in -aru/-uru/-oru — and
  then mis-applies the very heuristic this record is teaching (an -i/-e sound before る ⇒ ichidan), which
  would make 帰る an ichidan verb and produce ×帰ない / ×帰て.
- **Proposed fix** — split the one list into the two distinct groups:
  > Nem todo verbo terminado em る é る-verbo. (1) Os que terminam em -aru/-uru/-oru são sempre う-verbos: ある, 分かる, 作る, 乗る. (2) Há ainda as "exceções disfarçadas", que terminam em -iru/-eru mas conjugam como う-verbos: 帰る, 走る, 入る, 切る, 知る. A regra do som -i/-e antes de る ajuda, mas essas exceções você aprende uma a uma.

## F4 — MEDIUM — `gram:itsumo`: the nuance contradicts itself in the same sentence

- **Record:** `gram:itsumo` (id 83, n5) — "sempre (いつも)"
- **Field:** `nuance` (both locales)
- **Exact current text (pt-BR):**
  > Diferente do português, いつも não precisa de negação para significar "nunca": quem dá esse sentido é o verbo no negativo; sozinho, いつも é positivo.

  (EN carries the same contradiction: *"Unlike Portuguese, いつも doesn't need negation to mean 'never': that sense comes from the verb being negative"*.)
- **Why it is wrong:** the first half says no negation is needed to reach "nunca"; the second half says the
  negation on the verb is precisely what produces it. Both cannot hold. The contrast with Portuguese is also
  drawn backwards: pt-BR has a *dedicated negative adverb* ("nunca vem"), which is exactly what Japanese
  lacks — the languages differ in the opposite direction from what the sentence claims. `formation` in the
  same record gets it right ("Com verbo negativo, ganha o sentido de 'nunca / nem sempre'"), so the record is
  self-inconsistent as well.
- **Proposed fix:**
  > いつも sozinho é sempre positivo ("sempre"). O sentido de "nunca" só aparece quando o VERBO está no negativo: いつも来ない ("nunca vem"). Em português temos um advérbio próprio para isso ("nunca"); em japonês quem nega é o verbo, e いつも só marca a frequência.

## F5 — MEDIUM — example sentences that do not instantiate the point they are tagged with

Five records in the slice carry sentences that teach a *different* structure. This matters twice over: a
teacher reviewing the point sees a contradicting example, and any exercise/SRS builder that pulls "sentences
for grammar X" from `sentence.grammar` will ship them.

| Record | Bad tag | Why |
|---|---|---|
| `gram:gp-13` (がいる, existence of animates) | `sent:tatoeba-3576174` 「さあ、ピザがいる人ー！」 | The いる here is 要る *"to need"*, not the existence verb (the PT gloss itself says "pessoa que precisa de (quer) pizza"). ピザ is inanimate, which this record says is impossible with いる. **The record's own `steps_unavailable` names this exact trap:** *"a homophone trap, since 本がいる reads as 本が要る (\"needs a book\")."* |
| `gram:ni-iku` (purpose, masu-stem + に行く) | `sent:tatoeba-162318` 「私は、バスで学校に行く。」, `sent:tatoeba-182675` 「休暇はどこに行くの？」, `sent:tatoeba-187532` 「何駅に行くのですか。」 | All three are destination に + 行く (noun + に), not the purpose construction. The record explicitly teaches "é a raiz-ます …, NUNCA a forma de dicionário" and that this に "só vale com verbos de movimento" as a *purpose* marker. **3 of the 5 tagged sentences are off-point**; only 友だちに会いに行く and ハイキングに行く belong. The corpus has `gram:ni` / `gram:gp-27` for the destination use. |
| `gram:koto-ga-aru` | `sent:tatoeba-11960481` 「やることがあるんだ。」, `sent:tatoeba-2197773` 「何か言いたいことがあるの？」 | Plain noun こと ("there are things to do / to say"), not the experiential 〜たことがある nor the occasional 〜ることがある. 2 of 7. |
| `gram:n3-koto` (nominalizer) | `sent:tatoeba-5008` 「いつか私のことは忘れちゃうわ。」, `sent:tatoeba-5324` 「彼のことを知らない。」 | The 〜のこと "about (a person)" idiom. No verb is nominalized, which is the entire point of the record. 2 of 5. |
| `gram:deshou` | `sent:tatoeba-5347` 「あなたって、なんてきれいなんでしょう！」 | Exclamatory なんて〜でしょう, a third use the record does not cover (it lists only probability and confirmation-seeking). Lower confidence, but the learner meets an unexplained pattern as example #1. Also `sent:tatoeba-78454` 「嵐になるだろう。」 is だろう while this record's `register` is `["polite"]` only. |

- **Proposed fix:** drop the listed keys from those sentences' `grammar` arrays (re-tagging `ピザがいる` to a
  要る entry, and the three ni-iku sentences to the destination-に point). For `gram:deshou`, either add the
  exclamatory use to the explanation or retag.

## F6 — MEDIUM — `gram:gp-93` (以下): every generated example writes 以下 in hiragana

- **Record:** `gram:gp-93` (id 250, n4) — 以下 (ika)
- **Sentences:** all 4 in the bank
  - `sent:gen-0877b1b2f764` 今日の気温は十度**いか**です
  - `sent:gen-a81f2084ea99` 五十点**いか**は合格できません
  - `sent:gen-b249a5f48dc6` 千円**いか**の本を買いました
  - `sent:gen-e1c2cfd5e350` 三歳**いか**の子供は無料です
- **Why it is wrong:** numeral + いか in kana is not how this is written — 十度以下, 千円以下, 三歳以下 are the
  standard forms, and the kana spelling collides with いか = 烏賊 / 医科, forcing a garden-path read
  (千円いかの本 parses as "a squid book of 1000 yen" before it parses correctly). It also contradicts the
  record itself, which writes 以下 in kanji throughout and gives 18歳以下 / 1000円以下 as its own examples.
  Every other kanji in those sentences (千円, 本, 買, 三歳, 子供, 無料, 気温, 合格) is written normally, so
  this is not a deliberate kana-only policy.
- **Likely root cause:** `structure_pattern` for this record is `"いか"` (kana) while `label` and `forms` use
  以下 — the generator most likely keyed off `structure_pattern`.
- **Proposed fix:** rewrite the four sentences with 以下, and set `structure_pattern` to `以下（いか）` to stop
  the leak. (Same shape to check on any other record whose `structure_pattern` is kana for a kanji word.)

## F7 — MEDIUM — same-level duplicate records, never cross-linked, splitting the example bank

`related` is empty on **122 of my 124 records** (only `gram:ga` ↔ `gram:wa-topic-marker` are linked), so
nothing in the data says these pairs are the same point:

| Pair (same level) | Overlap |
|---|---|
| `gram:gp-50` 「たほうがいい」 (n5, id 67) ↔ `gram:hou-ga-ii` 「～ほうがいい」 (n5, id 79) | Same point; `hou-ga-ii` is the strict superset (adds ないほうがいい, adjectives, nouns). 7 sentences hang off each, and **`sent:tatoeba-216787` and `sent:tatoeba-232073` are tagged with both keys** — the bank already admits the collision. |
| `gram:gp-54` 「～のがじょうずです」 (n5, id 71) ↔ `gram:no-ga-jouzu` 「のが上手」 (n5, id 119) | Identical construction, one spelled in kana, one in kanji. 6 sentences each, disjoint. |
| `gram:gp-145` 「～なくちゃいけない」 (n5, id 27) ↔ `gram:nakucha` 「なくちゃ」 (n5, id 107) | The second is the truncated form of the first; both n5, 7 sentences each. |
| `gram:gp-47` 「より～のほうが」 (n5, id 63) ↔ `gram:yori-hou-ga` 「より～ほうが」 (n5, id 150) | Same pattern, same level, near-identical explanations. |
| `gram:gp-77` 「のように・のような」 (n4) ↔ `gram:gp-154` 「～のように」 (n4) | Same construction split only by a `register` label (`formal/written` vs `plain`). |

Cross-level pairs in the slice that are plausibly an intentional N4→N3 spiral but are still uncross-linked,
so nothing marks them as a re-teach rather than a new point: `hazu-da`/`n3-hazu-da`, `nado`/`n3-nado`,
`sa`/`n3-sa`, `koto`/`n3-koto`, `naide`/`n3-naide`, `tara`/`gp-60`.

- **Consequence:** a learner meets the same N5 point twice under two names; a lesson builder can schedule both;
  and the sentence bank's examples for one construction are split across two keys, so "show me sentences for
  ほうがいい" returns half the corpus's actual coverage.
- **Proposed fix:** merge each same-level pair (keep the superset record, repoint the loser's key in
  `sentence.grammar`), or at minimum populate `related` on both sides of every pair above.

## F8 — MEDIUM-LOW — `gram:naide` is filed at n5 against a 2-of-3 majority for n4

- `level: "n5"`, `level_sources: {"jlptsensei": "n5", "bunpro": "n4", "tanos": "n4"}`,
  `level_confidence: 0.333`, `level_agreement: "1/3"`.
- Two of three community lists say n4; the record takes the single dissenting source. `CLAUDE.md` §1.5 makes
  level assignment consensus-based across ≥3 lists — this is the one record in the slice where the stored
  level loses its own vote. (`gram:te-form` also mismatches, but it is a deliberate course anchor with
  `agree: "anchor"`, not a defect.)
- **Proposed fix:** move to n4, or record the rationale for the minority pick in the record.

## F9 — LOW-MEDIUM — `gram:gp-61` (だが・ですが): formation is under-specified and licenses bad Japanese

- **Field:** `formation` (both locales). **Exact text (pt-BR):**
  > Usados no início de uma nova frase (です/だ + が como conector) ou anexados ao fim de uma oração: [oração 1]+ですが、[oração 2]. Versões: です/だ + が.
- **Why it is wrong:** "Versões: です/だ + が" read literally gives ×行くだが and ×高いだが. だ attaches to nouns
  and な-adjectives only; verbs and い-adjectives take が directly (行くが, 高いが) or the polite ますが/ですが.
  The record's own `steps_unavailable` states this defect ("*taken literally that licenses \*行くだが and
  \*高いだが, all ungrammatical … The record does not carry that split*") but the learner-facing field was left
  as is — same pattern as F2.
- **Proposed fix:** state the split: "だ só depois de substantivo ou adjetivo-な (学生だが, 静かだが); com verbo e
  adjetivo-い o が vem direto (行くが, 高いが), ou use ますが / ですが no registro polido."

## F10 — LOW — internal row ids leaked into learner-facing text

- `gram:n3-to-ittemo`, `nuance` (pt-BR **and** en): *"Diferente de ところが **(gid 427)**, que apresenta um resultado inesperado…"*
- `gram:n3-to-iu-no-wa`, `nuance` (pt-BR **and** en): *"Diferente de というの **(gid 421)**, que justifica um motivo em vez de definir."*
- 6 occurrences registry-wide. A learner reading the nuance card sees a raw database id.
- **Proposed fix:** drop the parenthetical and express the link as data — both records have `related: []`, which
  is exactly the field this belongs in.

## F11 — LOW — pt-BR orthography: a cluster of n3 records lost their diacritics

All in `explanation` / `formation` / `nuance`, all learner-facing, all in `n3.json`:

| Record | Current | Should be |
|---|---|---|
| `gram:n3-ni-kurabete` | "…o ponto de referência (o 'do que' da comparação) **e** quem leva に比べて, ordem inversa **a** do português"; "diz que o inverno **e** frio" | "**é** quem leva"; "**à** do português"; "**é** frio" |
| `gram:n3-ni-taishite` | "Não confunda com に対する, que **e** a forma usada…"; "'a resposta **a** pergunta'" | "que **é** a forma"; "a resposta **à** pergunta" |
| `gram:n3-ni-yotte` | "a forma adjetiva (que modifica substantivo) **e** による"; "comum em **noticias**, textos **academicos** e **relatorios**" | "**é** による"; "**notícias**, **acadêmicos**, **relatórios**" |
| `gram:n3-to-ittemo` | "**Tipico** para suavizar"; "mas **so** faço o básico"; "não **e** um 'embora' qualquer" | "**Típico**"; "**só**"; "não **é**" |
| `gram:n3-to-iu-no-wa` | "**e** comum 'Substantivo + とは'"; "Tom **didatico** e expositivo, **otimo** para…" | "**é** comum"; "**didático**", "**ótimo**" |
| `gram:n3-toku` | "**So** para fala casual"; "preste atenção **a** forma -te" | "**Só**"; "**à** forma" |

The same class continues outside my slice (e.g. `gram:n3-to-iu-koto-da`, "noticias"), so a diacritics sweep of
the whole `n3.json` is warranted rather than six point fixes. `design/translation_style.md` governs this text.

## F12 — LOW (systemic) — the n3 layer is not at field parity with n5/n4

Measured across the whole registry, not just the slice:

- **132 of 132** n3 records have every `forms[].meaning` set to `null` — against **1 of 364** for n5+n4.
  The forms table therefore renders a bare pattern string with no gloss for **every** N3 point (all 33 in my
  slice: `～ば～のに`, `～切れない`, `～わけだ`, … each with `meaning: None`).
- **132 of 132** have `refs: null` and `families: []`. No N3 point belongs to any family, so §1.7's
  "everything is one cross-referenceable graph" has no family edges at all above N4.
- **132 of 132** have a single level source, `{"hanabira": "n3"}`, `level_confidence: 0.34`,
  `level_agreement: "1/1"` — i.e. the whole N3 level fails §1.5's "cross-reference ≥3 independent community
  lists" rule, uniformly.
- **Proposed fix:** treat N3 as an unfinished layer with a tracked backfill (form glosses, level cross-refs,
  family membership), rather than as complete records with empty fields.

## F13 — LOW — example coverage gaps in the slice

- **Zero sentences in the bank:** `gram:n3-koto-wa-ga`, `gram:n3-moshikasuru-to-kamoshirenai`, `gram:n3-sore-to`.
  (`n3-koto-wa-ga` is the same record as F2 — a wrong rule with no examples to correct it.)
- **1–2 sentences:** `gram:n3-sae` (1), `gram:n3-tsumori-deshita` (1), `gram:n3-nai-koto-wa-nai` (2),
  `gram:n3-you-ni-iu` (2).
- Note on `gram:n3-sae`: its single sentence (`sent:tatoeba-194622`) covers only the さえ…すれば "basta que"
  branch. The "até mesmo" branch, which the explanation presents *first*, has no example at all.

## F14 — LOW — dangling cross-references in prose ("the previous one", "as in へた")

- `gram:nakereba-naranai`, `formation` opens: *"**Igual à anterior**: forma negativa 〜ない do verbo → troca 〜ない por 〜なければ + ならない."* (EN: *"Same as the previous one"*.) There is no "previous one" — records are addressed by stable ID and rendered standalone. It presumably means 〜なければいけない, which is a separate record.
- `gram:gp-54`, `explanation` opens: *"**Como em へた**, o の nominaliza o verbo…"* — a sibling point referenced by bare name, at a moment the learner has not met it, with `related: []` so there is no link to follow.
- **Proposed fix:** name the target explicitly and add it to `related`.

## F15 — LOW — `gram:o-go`: ご飯 attributed to the お prefix

- **Field:** `nuance` (both locales). **Exact text (pt-BR):**
  > Algumas palavras já "colaram" com o **お** e quase sempre aparecem com ele (**ご飯**（はん）, お茶（ちゃ）, お金（かね）).
- ご飯 takes ご, not お — and it is the *first* item in a list explicitly introduced as words fused "com o お",
  inside the very record whose job is teaching the お/ご split.
- **Proposed fix:** "…já 'colaram' com o prefixo e quase sempre aparecem com ele (ご飯, お茶, お金)."

## F16 — LOW (scope-adjacent, flagged once) — family membership contradicts the family's own label

`families` is not strictly my assignment, but the mismatches are learner-visible (`type: function_set`, pt-BR
labels) and consistent enough to look like a bulk assignment:

- `gram:yori-hou-ga` (comparison) → `grp:gram-n5-passado`, labeled *"Gramática: Passado polido e nuances"*
- `gram:ato-de`, `gram:oki-ni` → `grp:gram-n4-potencial`, *"Gramática: Potencial"*
- `gram:gp-43` (たくさん), `gram:nakucha` → `grp:gram-n5-te-form`, *"A forma て e seus usos"*
- `gram:gp-36` (relative clauses), `gram:naide`, `gram:ni-iku` → `grp:gram-n5-particulas-lugar`, *"Lugar, tempo e direção: で/に/へ/と"*
- `gram:o-go` → `grp:gram-n5-convites`, *"Convites, sugestões e habilidade"*

A learner opening "Passado polido e nuances" finds より〜ほうが in it. Worth one systematic pass over grammar
family membership rather than record-by-record fixes.

---

## What came back clean

Stated explicitly, since precision is the point of this sweep:

- **All `formation_steps` in the slice produce correct Japanese.** I traced every variant by hand. The
  `to-nai-stem` convention (ない-form minus final い) is applied consistently across all 14 records that use it
  (`gp-6`, `gp-145`, `nakucha`, `hou-ga-ii`, `naide`, `gp-150`, `tara`, `te-yokatta`, `koto-ga-aru`,
  `you-ni-suru`, `nakereba-naranai`, `n3-you-ni-iu`, `n3-tsumori-deshita`, `n3-nai-koto-wa-nai`) and every
  worked example is right.
- **The morphology-heavy records are correct in full:** て-form (godan onbin table + いく→いって), potential
  (godan -eru / ichidan られる / する→できる, plus the が-object shift and ら抜き note), passive (う→わ, agent に,
  the 〜られる potential/passive ambiguity), imperative (-e column / ろ・よ / しろ・せよ / 来い, and 〜な for the
  negative), ば-conditional, たら, causative + てください, さ-nominalization, くする/くなる, くはない.
- **The `steps_unavailable` notes are excellent** — honest, specific, and several of them (`gp-13`, `n3-shika-nai`,
  `gp-127`, `oki-ni`, `irassharu`) correctly refuse to encode a rule rather than emit one that would
  over-generate. Two of my findings (F2, F9) exist precisely because that same rigor was not applied back to
  the learner-facing `formation` field; the diagnosis was already written down.
- **No nuance field contradicts its own explanation**, except `gram:itsumo` (F4).
- 80 of 124 records carry no record-specific finding at all.

---

## Counts

| Class | Findings | Records affected (in slice) |
|---|---:|---:|
| Wrong content in a learner-facing field (wrong point pasted in) | 1 | 1 |
| Formation rule that produces ungrammatical Japanese | 2 (F2, F9) | 2 |
| Factually wrong statement in explanation/nuance | 3 (F3, F4, F15) | 3 |
| Sentence tagged with a point it does not instantiate | 1 (F5, 5 records / 10 sentences) | 5 |
| Unnatural Japanese in generated examples (kana 以下) | 1 (F6, 4 sentences) | 1 |
| Duplicate / uncross-linked records | 1 (F7, 5 same-level pairs + 6 cross-level) | 17 |
| Level assignment against source majority | 1 (F8) | 1 |
| Internal ids / dangling refs in learner text | 2 (F10, F14) | 4 |
| pt-BR orthography | 1 (F11, 6 records) | 6 |
| Field-completeness (n3 layer parity) | 1 (F12) | 33 |
| Example coverage gaps | 1 (F13) | 7 |
| Family membership vs family label (scope-adjacent) | 1 (F16) | 8 |
| **Total** | **16** | **44 records with a record-specific finding; 80 clean** |

| Scope | Count |
|---|---:|
| Records assigned | 124 |
| Records read in full | 124 |
| n5 / n4 / n3 | 38 / 53 / 33 |
| Sentences cross-checked | 470 (up to 4 per record; full set read for the 8 records under F5/F7 — 671 sentences carry a key from this slice) |
| `formation_steps` variants traced by hand | 254 (across 96 records; the other 32 carry a `steps_unavailable` note instead, all 32 read) |

**Priority for the teacher review queue:** F1 first (a pt-BR learner is currently taught the wrong formation
for 〜ないで), then F2 and F9 (rules that generate ungrammatical Japanese, both already diagnosed in
`steps_unavailable` and awaiting a prose fix), then F3.
