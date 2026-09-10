# W24 capability layer: kinds, can-do text and the exam link

_Derivation + small authoring, 2026-09-10. Every number below was produced by a script over the
committed export at `2626d20c` and a scratch copy of `db/corpus.sqlite`. **Nothing in the repo was
modified**: the proposal is `research/derived/pending/w24_capabilities.json` (397 KB) plus this
report. No exporter, builder, contract, lesson or validator was touched, and no git state changed._

## 0. The gap W24 closes

`contracts/manifest.json` calls a capability "Something a learner can DO once a set of lessons is
complete. The bridge between the syllabus and the exam." `contracts/capability.schema.json` gives it
four fields: `id`, `level`, `name`, `grammar_keys`. So the entity has **no can-do statement, no field
that reaches the exam, and no kind that can express vocabulary**: readiness gap G10.

Measured, not quoted:

| | lessons |
|---|---:|
| mapped by `corpus/capabilities/lesson_map.json` | 266 |
| unmapped, unlocks **vocabulary only** | 42 (n3 34, n5 5, pre-n5 3) |
| unmapped, unlocks **nothing** | 12 |
| unmapped, unlocks a **`feature` only** | 2 |
| **total unmapped, all carried in `exemptions.json`** | **56** |

`research/reports/readiness/jlpt_course_path.md` names "34 N3 lessons". That is the n3 slice of the
42 vocabulary-only rows. **A vocabulary kind alone fixes 42 of 56.** The other 14 need two more kinds,
because they unlock no corpus item at all and no unlock-derived rule can ever reach them:

- 6 phonology lessons (`top:pre-n5-sons` ×3, `top:pre-n5-pronuncia` ×3),
- 6 review lessons (`n5-revisao-01/02/03`, `n4-revisao-01/02/03`; two of them unlock only
  `feat:jlpt-sim-n5` / `feat:jlpt-sim-n4`),
- 2 orientation lessons (`les:pre-n5-orientacao-01`, `-02`).

## 1. What is proposed

**Six kinds** (neutral English, `x-vocabulary` owner = design):

| kind | caps | new | what it means |
|---|---:|---|---|
| `grammar` | 72 | 0 | the curated groups + topic-bucket fallback that ship today, unchanged |
| `script` | 3 | +1 | kana, kanji, and the new `cap:romaji-reading` |
| `vocabulary` | 44 | +44 | a lexical field the learner can name |
| `phonology` | 2 | +2 | a property of the sound system the learner can produce or hear |
| `exam-readiness` | 3 | +3 | the consolidated "you can sit this paper" claim of a review topic |
| `study-method` | 1 | +1 | how to use the course and its review engine |
| **total** | **125** | **+51** | 74 shipped rows keep their `id`, `level` and `grammar_keys` verbatim |

**Six mapping rules.** Only R-VOCAB is derived from data; the rest are curated the same way
`build_capabilities.CAPS` already is, and each is one line in the builder.

| rule | rule text | emits | lessons |
|---|---|---:|---:|
| **R-VOCAB** | every `vocab` unlock maps to `cap:vocab:<topic-slug>`, the topic of the **lesson that unlocks the word**; a lesson gets one vocabulary capability per distinct topic among its vocab unlocks | 44 | 253 |
| **R-PHON** | curated: `top:pre-n5-sons` + `top:pre-n5-pronuncia` + `les:pre-n5-orientacao-02`, split into `cap:phonology-segments` and `cap:phonology-mora` | 2 | 6 |
| **R-SCRIPT** | `cap:romaji-reading` → `les:pre-n5-orientacao-02` | 1 | 1 |
| **R-STUDY** | `cap:study-method` → `les:pre-n5-orientacao-01` | 1 | 1 |
| **R-EXAM** | every lesson whose topic slug matches `top:<level>-revisao` → `cap:exam-readiness-<level>` | 3 | 7 |
| **R-EXAMLINK** | see §3 | n/a | n/a |

R-VOCAB mirrors what the builder already does for kanji (`cap:kanji-recognition` is attached to every
lesson with a kanji unlock, alongside its grammar capability), so a word taught inside a grammar
lesson gets a vocabulary capability too, not only the 42 vocabulary-only lessons. That is why 220
already-mapped lessons gain a capability and 56 gain their first.

**Why the unlocking lesson and not `vocab.introducing_topic_id`:** that column is **NULL for 2,912 of
the 2,945 unlocked words**. On the 33 where it is set it agrees with the unlocking lesson's topic in
every case (0 disagreements). The column cannot carry the rule; the unlock ledger can.

**R-EXAM is what makes N3 reachable.** It keys off the topic slug, so the moment W22 grows
`top:n3-revisao` from 1 lesson to 3, `cap:exam-readiness-n3` picks them up with no edit.

## 2. Result

| | before | after |
|---|---:|---:|
| capabilities | 74 | **125** |
| lessons mapped | 266 / 322 | **322 / 322** |
| lessons mapped to nothing | 56 | **0** |
| `exemptions.json` entries | 56 (42 `pending-capability-design`) | **0** |
| capabilities with `can_do` | 0 | **125** |
| lesson objectives quoted as can-do provenance | 0 | **225** |
| capabilities with an `exam_link` | 0 | **118 / 125** |
| `exam_link` rows | 0 | **851** |

Capabilities per lesson after: min 1, median 3, max 6.

`corpus/capabilities/exemptions.json` must be **emptied in the same commit**. Its own `why` says a
stale entry is a hard failure, and `validate_graph_edges.check_capability_coverage` enforces exactly
that: an exemption whose lesson "is now mapped to" a capability is reported as a stale entry.

## 3. The exam link

Derived per item from the provenance the bank builder already wrote, never asserted:

1. `item.grammar` → the capability that owns that grammar key.
2. `item.vocab` → `cap:vocab:<topic of the unlocking lesson>`, **plus** `cap:kanji-recognition` when
   the section is `kanji_reading` or `orthography` (there the kanji *is* the question).
3. `item.reading` → `reading.gated_to_lesson` → every capability of that lesson.
4. fallback `item.sentence` → `sentence_grammar` keys → their capabilities.
5. an `exam-readiness` capability instead links to **every section its level's paper draws from**
   (`design/exam_simulator.md` paper table), tagged `via: "paper"`.

Rows aggregate to `(level, section, bank, items, via)`: exactly what an exporter emits.

### 3.1 The link is also a level-gate probe, and it fails the 文字・語彙 half of the paper

**3,619 of the 6,081 bank items reach no capability at all.** The breakdown is not uniform, and one
row of it is a finding, not noise:

| section | items whose `vocab` ref is a word the course teaches |
|---|---|
| `n5_kanji_reading` | 3 / 398 |
| `n5_orthography` | 3 / 377 |
| `n4_kanji_reading` | 0 / 398 |
| `n4_orthography` | 0 / 398 |
| `n3_kanji_reading` | 10 / 400 |
| `n3_orthography` | 10 / 400 |
| **all four kanji/orthography banks** | **26 / 2,373 = 1.1%** |

Every one of those 2,373 items carries a `vocab:` slug, so the provenance is intact; the slug simply
names a word **no lesson ever unlocks**. This is G3 measured from a different direction, and it is
sharper than the character-level measurement in the readiness report: 98.9% of the 漢字・語彙 bank is
not merely above level, it is **unattributable to anything the course claims to teach**. `n4` is the
extreme: not one of its 796 kanji/orthography items tests a taught word.

The other unlinked mass is benign or already known: 213 listening items carry no ref by design
(`listening_task` / `_point` / `_say` / `_gist` have no source slug), and `sentence_order` loses items
whose sentence has no `sentence_grammar` row.

### 3.2 Seven capabilities the corpus assesses nowhere

`cap:kana-reading`, `cap:romaji-reading`, `cap:phonology-segments`, `cap:phonology-mora`,
`cap:study-method` are correct and expected: the JLPT has no section for them, and the empty array says
so honestly. Two are real gaps: **`cap:vocab:pre-n5-saudacoes`** (the 24 survival words, tested by
nothing) and **`cap:vocab:n4-kanji-exame`** (a lesson whose whole purpose is the exam, linked to no
exam item).

## 4. The can-do text

125 statements, pt-BR, first person, one sentence, Layer C / `ai_generated` / `needs_review`. Each
carries `can_do_derived_from`: the lesson objectives it was written from, **quoted verbatim**. The
build refuses to emit a row whose quote is not an exact objective of a lesson that capability actually
claims, so the Layer-C claim is auditable without re-reading the lessons.

This is what `design/learning_science.md` **R66** asks for ("Either add a `can_do: {"pt-BR": …}` field
per capability … or point at `speaking_path.md` stages"), and it unblocks R65. **R67** ("DON'T surface
an unqualified 'você já consegue…' unless backed by ≥1 PRODUCTION event") needs a field to read, so
each capability also carries `can_do_evidence: recognition | production`: `recognition` on the
script, vocabulary and study-method kinds, `production` elsewhere. The app phrases "você já reconhece"
where the value is `recognition`.

## 5. Twenty sample rows

| capability | kind | lvl | lessons | can_do (pt-BR) | exam_link |
|---|---|---|---:|---|---|
| `cap:vocab:n3-causa` | vocabulary | n3 | 8 | Consigo falar de causa e consequência com o vocabulário N3 do tema, incluindo as famílias 適 e 不/無 e palavras como 伝統. | n3 reading_comp (12), n3 text_grammar (9) |
| `cap:vocab:n3-tempo` | vocabulary | n3 | 8 | Consigo reconhecer e usar o vocabulário N3 de confiança, conexão e sequência que aparece nas frases de tempo e simultaneidade. | n3 context_fill (13), n3 reading_comp (13), n3 text_grammar (11) |
| `cap:vocab:n3-estrutura` | vocabulary | n3 | 6 | Consigo reconhecer e usar o vocabulário N3 de lugar, conhecimento e descoberta que preenche as frases nominalizadas e passivas. | n3 reading_comp (9), n3 text_grammar (6) |
| `cap:vocab:n5-convites` | vocabulary | n5 | 6 | Consigo falar de rotina, datas e clima com a família 毎, os primeiros contadores e verbos como 降る e 曲がる. | n5 reading_comp (3), n5 text_grammar (2) |
| `cap:vocab:n5-numeros-tempo` | vocabulary | n5 | 9 | Consigo contar objetos, pessoas, andares e idades com os contadores básicos e falar de durações. | n5 context_fill (2), n5 kanji_reading (1), n5 orthography (1) +2 |
| `cap:vocab:pre-n5-saudacoes` | vocabulary | pre-n5 | 3 | Consigo cumprimentar, agradecer, recusar com jeito e encerrar uma conversa com as palavras de sobrevivência do dia a dia. | none |
| `cap:vocab:n4-kanji-exame` | vocabulary | n4 | 1 | Consigo reconhecer as palavras de partes do corpo e de acesso que os kanji de reforço do N4 escrevem. | none |
| `cap:phonology-segments` | phonology | pre-n5 | 3 | Consigo pronunciar as cinco vogais japonesas cheias e sem nasalizar, e deixar i e u quase mudos onde o japonês os desvozeia. | none |
| `cap:phonology-mora` | phonology | pre-n5 | 4 | Consigo contar as moras de uma palavra e dar o tempo certo à vogal longa, ao っ e ao ん em vez de acentuar como no português. | none |
| `cap:romaji-reading` | script | pre-n5 | 1 | Consigo ler romaji com os valores do japonês, sem aplicar a ele a fonética do português. | none |
| `cap:study-method` | study-method | pre-n5 | 1 | Consigo explicar com minhas palavras como a revisão espaçada funciona e deixar o app decidir o que revisar em cada dia. | none |
| `cap:exam-readiness-n5` | exam-readiness | n5 | 3 | Consigo montar e entender frases com tudo o que o N5 cobra e encarar um simulado completo do exame. | n5 context_fill (6), n5 grammar_form (9), n5 kanji_reading (7) +9 |
| `cap:exam-readiness-n4` | exam-readiness | n4 | 3 | Consigo transitar entre a forma polida e a simples e usar potencial, passiva, causativa e keigo com a segurança que o N4 exige. | n4 context_fill (8), n4 grammar_form (8), n4 kanji_reading (7) +10 |
| `cap:exam-readiness-n3` | exam-readiness | n3 | 1 | Consigo escolher o conector ou o padrão N3 certo para cada intenção e avaliar sozinho onde ainda preciso reforçar. | n3 context_fill (11), n3 grammar_form (13), n3 kanji_reading (8) +11 |
| `cap:te-form` | grammar | n5 | 4 | Consigo formar a forma て de qualquer verbo e usá-la para pedir, permitir, proibir e encadear ações. | n3 context_fill (5), n3 grammar_form (11), n3 listening_reply (1) +12 |
| `cap:conditionals` | grammar | n4 | 9 | Consigo montar hipóteses e condições com と, ば, たら e なら, e lamentar o que não fiz com 〜ばよかった. | n3 context_fill (7), n3 grammar_form (7), n3 reading_comp (4) +9 |
| `cap:keigo` | grammar | n4 | 6 | Consigo elevar as ações do outro com o honorífico e rebaixar as minhas com o humilde ao falar com clientes, chefes e pessoas mais velhas. | n3 context_fill (1), n3 grammar_form (5), n3 reading_comp (1) +10 |
| `cap:kanji-recognition` | script | n5 | 187 | Consigo reconhecer os kanji do meu nível dentro de palavras e escolher a leitura certa pelo contexto. | n3 kanji_reading (10), n3 orthography (10), n3 reading_comp (85) +7 |
| `cap:kana-reading` | script | pre-n5 | 30 | Consigo ler e escrever qualquer palavra em hiragana e katakana, com o som cheio de cada mora. | none |
| `cap:permission` | grammar | n5 | 1 | Consigo suavizar uma afirmação forte com と言ってもいい, no sentido de 'dá para dizer que'. | n3 context_fill (1), n4 reading_comp (1), n4 text_grammar (1) |

Provenance, as it appears in the pending file:

```
cap:phonology-mora  "Consigo contar as moras de uma palavra e dar o tempo certo à vogal longa,
                     ao っ e ao ん em vez de acentuar como no português."
  from [les:pre-n5-sons-02]      "Contar quantas moras tem uma palavra, incluindo o n final,
                                  a consoante dobrada e as vogais longas"
  from [les:pre-n5-pronuncia-02] "Contar corretamente as moras de palavras com ん,
                                  como ほん (2) e にほん (3)"
```

## 6. Schema fragment

Additive; `id`, `level`, `name`, `grammar_keys` keep their shape and stay required. Full JSON in the
pending file under `schema_fragment`.

| new property | type | note |
|---|---|---|
| `kind` | enum `grammar \| script \| vocabulary \| phonology \| exam-readiness \| study-method` | `x-vocabulary.owner: design`, source `design/courseware_architecture.md` |
| `can_do` | `LocaleText` | one first-person pt-BR sentence; Layer C, needs_review |
| `can_do_evidence` | enum `recognition \| production` | what R67's `assert_can_do` reads |
| `can_do_derived_from` | `[{lesson: IdRef, objective: string}]` | verbatim quotes, so the C claim is auditable |
| `lessons` | `IdRefList` | inverse of `lesson_map.json`, stored so a consumer need not load the map |
| `exam_link` | `[{level, section, bank, items, via}]` | `via ∈ {item-provenance, paper}` |

`required` after: `grammar_keys, id, kind, level, name, can_do, can_do_evidence`.

Validator changes proposed for `scripts/validate/validate_capabilities.py`: (a) `kind` in the enum;
(b) `can_do['pt-BR']` non-empty and `can_do_evidence` in the enum; (c) every
`can_do_derived_from.lesson` resolves, belongs to the capability's own `lessons`, and quotes a
verbatim objective; (d) **every lesson is a key of `lesson_map.json`**, which is what retires the
exemptions file; (e) each `exam_link` row names a bank file that exists and a section the paper spec
knows. `validate_graph_edges.check_capability_coverage` keeps its unmapped-lesson check and reads it
against 0 exemptions instead of 56.

## 7. Simulation

Fixture tree at `…/scratchpad/w24/sim/`, carrying **its own copies** of the validator and
`scripts/dbtarget.py`, pointed at the scratch DB with `--db`, so a plant cannot be answered by the
real repo (the plant-proof-root rule).

```
(A) SHIPPED scripts/validate/validate_capabilities.py, unmodified,
    on the proposed registry + lesson_map        ->  125 caps, 322 lessons, ALL OK   (rc 0)
(B) PROPOSED validator (checks a-e)              ->  125 caps, 322 lessons, ALL OK   (rc 0)
(C) 8 planted violations                         ->  8 / 8 caught (rc 1 each)
      kind missing · kind not in enum · can_do blank · can_do_evidence not in enum
      can_do sourced from a lesson the capability does not claim
      quoted objective not verbatim · a lesson maps to nothing
      exam_link names a bank that does not exist
```

The shipped gate passing unmodified matters: the 51 new rows and the six new fields are additive, so
the kinds can land before the validator is extended without a red suite in between.

## 8. Two defects found on the way (out of W24's scope to fix)

**8.1 `cap:permission` is named for a grammar point it does not own.** `build_capabilities.CAPS`
assigns keys with `setdefault`, and `temo-ii-desu` is listed in **both** `te-form` and `permission`.
`te-form` is declared first, so it wins, and `cap:permission` ships holding a single key -
`to-ittemo-ii` (と言ってもいい, "dá para dizer que") under the name "Permissão 〜てもいい". The
permission grammar the name promises lives inside `cap:te-form`. The pending file proposes the
minimal fix (rename to "Atenuação com と言ってもいい"); the alternative is to move `temo-ii-desu` out of
`te-form`, which changes `grammar_keys` on two shipped capabilities and should be an owner call.

**8.2 `corpus/exam_banks/INDEX.md` is stale by 11 items.** Its per-file lines sum to 6,092; the files
on disk hold **6,081**, differing in 7 files (`n4_kanji_reading` 400→398, `n4_orthography` 400→398,
`n5_kanji_reading` 400→398, `n5_orthography` 379→377, `n4_context_fill` 368→367, `n4_paraphrase` and
`n4_usage` 60→59). One line in the bank exporter's INDEX writer.

## 9. Apply order

1. Land the schema fragment in `contracts/_shapes.json` + `design/courseware_architecture.md`, and
   name the kind enum's owner there.
2. Teach `scripts/export/build_capabilities.py` the five emit rules and the exam-link derivation;
   re-run it; commit the regenerated `corpus/capabilities/*`.
3. **Empty `corpus/capabilities/exemptions.json` in the same commit** (a stale entry is a hard fail).
4. Extend `validate_capabilities.py` with checks (a)-(e) behind a plant proof, and drop
   `validate_graph_edges`'s 56-exemption expectation to 0.
5. Feed §3.1 into the exam-bank level gate work (APP_PLAN W18 / readiness G3): "1.1% of the
   kanji/orthography bank tests a word the course teaches" is a cheaper, harder assertion for that
   validator than the character-level measurement, and it comes for free from this link.
