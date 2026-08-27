# Homograph recommendations — advisory only

**Layer C (pedagogical). Prepared for teacher review. Generated 2026-08-27.**
**Nothing in the corpus, the courseware, or the working index was changed to produce this
document. Every item below is a recommendation with its evidence; the decision belongs to
the reviewing teacher.**

This covers the two open homograph question sets:

- `course/vocab_disambiguation_review.json` — 14 `(headword, lesson)` rows (10 `unresolved`,
  4 `frequency`) where a lesson addressed a word by headword and the headword names more
  than one record.
- `course/coverage_exemptions.json` — 9 taught-level vocab records that no lesson unlocks,
  each held open because it is the homograph sibling of a record the course does teach.

## Method

For each row the lesson's own `body` was read at the point where the reference occurs, plus
the lesson `title`, `description` and `objectives`, and both candidate records in
`corpus/vocab/*.json`. Two further signals were used:

1. **The introducing lesson.** Most of these records are first unlocked in a bulk vocabulary
   lesson (`les:n3-conectores-05`, `les:n3-tempo-05`, `les:n3-perspectiva-06`), and that
   lesson states the reading and gloss explicitly. Where a later lesson's prose echoes that
   wording, the match is decisive.
2. **The sentence bank.** `corpus/sentences/bank.json` tokens carry both a `vocab` slug and a
   `reading`, so per-record and per-reading counts are exact.

Confidence is rated **certain** (the lesson's own prose names the reading or a gloss unique to
one record), **probable** (converging indirect evidence, no contradiction), or
**genuinely ambiguous** (a curriculum choice, not a lookup).

---

# Part 1 — `vocab_disambiguation_review.json`

## Summary

| # | Headword | Lesson | Currently chosen | Recommendation | Confidence |
|---|---|---|---|---|---|
| 1 | 上 | `les:n3-perspectiva-01` | `vocab:1352150` かみ | **Keep** | certain |
| 2 | 上 | `les:n3-relato-04` | `vocab:1352150` かみ | **Change → `vocab:1352170` じょう** | certain |
| 3 | 何方 | `les:n5-passado-05` | `vocab:1189360` どちら | **Keep** (and see Part 2 §1) | certain |
| 4 | 得る | `les:n3-perspectiva-01` | `vocab:1454500` うる | **Keep** | probable |
| 5 | 得る | `les:n3-perspectiva-02` | `vocab:1454500` うる | **Keep** | probable |
| 6 | 数 | `les:n3-estado-03` | `vocab:1580820` かず | **Keep** | certain |
| 7 | 柄 | `les:n3-intencao-03` | `vocab:1508290` え | **Change → `vocab:1508300` がら** | certain |
| 8 | 柄 | `les:n3-perspectiva-02` | `vocab:1508290` え | **Keep** | certain |
| 9 | 注ぐ | `les:n3-desejos-05` | `vocab:1581730` そそぐ | **Keep** | certain |
| 10 | 額 | `les:n3-estado-01` | `vocab:1207500` がく | **Keep** | certain |
| 11 | 品 | `les:n3-conjectura-03` | `vocab:2648780` ひん | **Change → `vocab:1583470` しな** | certain |
| 12 | 後 | `les:n3-limites-04` | `vocab:2147630` ご | **Keep** | certain |
| 13 | 金 | `les:n3-deveres-03` | `vocab:1242590` かね | **Change → `vocab:1242600` きん** | certain |
| 14 | 金 | `les:n3-estado-04` | `vocab:1242590` かね | **Keep** | certain |

**Four of fourteen resolved onto the wrong record.** All four are body-display references, not
unlock references, so gating is unaffected; the learner simply sees a card whose reading and
meaning contradict the sentence next to it. In every one of the four the correct sibling is
already unlocked in the course, so the correction is a pure reference swap with no coverage
consequence.

Note also that in three of the four the picked record and the correct record are unlocked by
**the same** lesson (柄, 品, 金 all pair up inside one bulk vocabulary lesson), which is why
neither the sibling-ref nor the lesson-level heuristic could separate them. The one signal
that would have separated them — the reading the lesson's own prose prints inside `<jp>` —
was not consulted by the exporter. That is a reusable finding, noted at the end.

---

## 1. 上 in `les:n3-perspectiva-01` — keep `vocab:1352150` (かみ)

**Question.** 上 names both `vocab:1352150` (かみ, "upper reaches of a river / upper part") and
`vocab:1352170` (じょう, "from the standpoint of"). Which does this lesson teach?

**Evidence.** The lesson is *"Escopo e tema: において, について, に関して"*. The reference sits in a
vocabulary list and is glossed:

> `<vocab ref="vocab:1352150"/>: curso superior de um rio`

That gloss belongs only to かみ; じょう has no river sense. It is also a near-verbatim echo of
the introducing lesson `les:n3-conectores-05`, which unlocks this record and says:

> «上/かみ» (かみ) - curso superior de um rio, a parte de cima, a nascente. Diferente do 上
> (うえ, 'em cima') que você já conhece.

and illustrates it with `この川の上には小さな村がある`.

**Recommendation.** Keep `vocab:1352150`.

**Confidence.** Certain.

**What the teacher should check.** A separate authoring nit, not a disambiguation problem: the
list this word sits in is otherwise a run of う-initial readings (うつ, うなる, うがい, うし, うま,
うさぎ, ウイスキー). かみ is the odd one out. Worth deciding whether 上/かみ belongs in that
batch at all, or whether the slot was meant for a う-reading word.

---

## 2. 上 in `les:n3-relato-04` — change to `vocab:1352170` (じょう)

**Question.** Same pair, different lesson.

**Evidence.** The lesson is *"Papéis e lembranças: ～として e ～っけ"*. The body prints the reading:

> `<vocab ref="vocab:1352150"/> (<jp>じょう</jp>) = "do ponto de vista de, em termos de".`
> `Sufixo formal, como em <jp reading="ほうりつじょう">法律上</jp> ("do ponto de vista legal").`

The prose states the reading じょう, gives a suffix gloss, and gives a 〜上 compound. That is
`vocab:1352170` in every particular. The introducing lesson for じょう, `les:n3-tempo-05`, uses
almost the same sentence:

> «上/じょう» (じょう) - do ponto de vista de, em termos de, no que diz respeito a. Vem grudado
> a um substantivo, como em 安全上 ('em termos de segurança').

The surrounding list in `les:n3-relato-04` is a しょう/じょう homophone run (章 しょう, 賞 しょう,
小 しょう), which confirms the intent.

**Recommendation.** Change to `vocab:1352170`. That record is already unlocked at
`les:n3-tempo-05` (topic 39), which precedes `les:n3-relato-04` (topic 50), so the swap is
gating-clean.

**Confidence.** Certain.

**What the teacher should check.** Nothing blocking. Confirm the 法律上 example is the one
you want beside 安全上 from the earlier lesson, or vary it.

---

## 3. 何方 in `les:n5-passado-05` — keep `vocab:1189360` (どちら)

**Question.** 何方 names `vocab:1189360` (どちら, "which of two / which way / where, polite")
and `vocab:1189370` (どなた, "who, polite"). This row affects both an unlock and a body
reference.

**Evidence.** The lesson is *"Proibição e ênfase masculina: な"*. Its interrogative list says:

> `<vocab ref="vocab:1189360"/>: qual direção, para onde; é também a forma educada de 'qual
> (dos dois)' e até de 'quem'. Lido como どなた, vira uma maneira polida de perguntar 'quem é?'.`

The head gloss ("qual direção, para onde", "qual dos dois") is どちら. どなた is named, but as a
secondary reading of the same kanji, introduced in a subordinate clause.

Sentence bank: `vocab:1189360` has 17 tokens, `vocab:1189370` has 3.

**Recommendation.** Keep `vocab:1189360` for both the unlock and the body reference.

**Confidence.** Certain.

**What the teacher should check.** This same sentence is the strongest argument for unlocking
どなた here too — see Part 2 §1. The prose already teaches it; only the ledger does not know.

---

## 4. 得る in `les:n3-perspectiva-01` — keep `vocab:1454500` (うる)

**Question.** 得る names `vocab:1454500` (うる, classical-inflection suffix "can / be able to",
literary "obtain") and `vocab:1588760` (える, ichidan transitive "obtain, get, gain").

**Evidence.** The reference is inside the kanji-mnemonic block for `kanji:得`:

> `<kanji ref="kanji:得"/> (obter, ganhar, adquirir). Aparece direto no verbo`
> `<vocab ref="vocab:1454500"/> (える / うる, obter; poder fazer).`

The prose names **both** readings, so the lesson text alone does not decide. The introducing
lesson does. `les:n3-conectores-05` unlocks both records in the same lesson but writes prose
for one only:

> «得る/うる» (うる) - poder, conseguir (fazer). Forma um pouco literária de 'ser capaz de'.

`vocab:1588760` (える) is unlocked there and never mentioned in any lesson body anywhere in the
course. So うる is the record the course actually teaches, and pointing the mnemonic at it is
consistent.

Sentence bank: both records have 0 tokens, so frequency cannot help.

**Recommendation.** Keep `vocab:1454500`, on consistency grounds.

**Confidence.** Probable.

**What the teacher should check.** The real issue is upstream of this row: **える is unlocked
but never taught.** For a Brazilian learner the everyday word is える ("obter, conseguir"), and
うる is the literary/suffix variant met in 〜し得る and ありうる. If the intent is to teach the
common verb, the pair should be flipped at `les:n3-conectores-05` — える gets the prose and the
card, うる becomes the footnote — and this reference should then point at `vocab:1588760`.
That is a curriculum decision, not a lookup, and it would settle rows 4 and 5 together.

---

## 5. 得る in `les:n3-perspectiva-02` — keep `vocab:1454500` (うる)

**Question.** Same pair as row 4.

**Evidence.** The lesson is *"Perspectiva e fonte: にとって, によれば, に対して"*. The reference sits
in a plain vocabulary list with no reading printed:

> `<vocab ref="vocab:1454500"/>: obter; poder fazer`

The gloss is a blend of both records ("obter" is える's gloss, "poder fazer" is うる's). The
surrounding list mixes え- and う-initial readings (エネルギー, えさ, 柄/え, 梅/うめ, 生まれ/うまれ,
描く/えがく, 売れる/うれる, 裏切る/うらぎる), so position does not separate them either.

**Recommendation.** Keep `vocab:1454500`, for the same consistency reason as row 4, and resolve
both rows the same way whichever the teacher chooses.

**Confidence.** Probable.

**What the teacher should check.** Whatever is decided for row 4 applies verbatim here. If
える wins, this gloss should be trimmed to "obter, conseguir" and the "poder fazer" sense moved
to a note about 〜し得る.

---

## 6. 数 in `les:n3-estado-03` — keep `vocab:1580820` (かず)

**Question.** 数 names `vocab:1580820` (かず, noun "number, quantity") and `vocab:1580825`
(すう, prefix "several, a few").

**Evidence.** The body prints the reading:

> `<vocab ref="vocab:1580820"/>(<jp>かず</jp>) = "número, quantidade".`

It sits in a か-reading run (菓子 かし, 貸し かし, 賢い かしこい, 歌手 かしゅ, **数 かず**,
数える かぞえる, 稼ぐ かせぐ) — alphabetically exactly where かず belongs. すう would not.

**Recommendation.** Keep `vocab:1580820`.

**Confidence.** Certain.

**What the teacher should check.** Nothing. The reading is printed and the ordering corroborates.

---

## 7. 柄 in `les:n3-intencao-03` — change to `vocab:1508300` (がら)

**Question.** 柄 names `vocab:1508290` (え, "handle, haft") and `vocab:1508300` (がら, "pattern
on cloth / build / disposition").

**Evidence.** The lesson is *"ように: finalidade, modo e comparação"*. The body prints the
reading and the gloss:

> `<vocab ref="vocab:1508290"/> (<jp>がら</jp>): "estampa, padrão".`

Reading がら, gloss "estampa, padrão" — both belong to `vocab:1508300`, neither to
`vocab:1508290`. The introducing lesson `les:n3-conectores-05` writes:

> «柄/がら» (がら) - estampa, padrão, desenho de um tecido.

which is the same wording, so the intent is unambiguous.

**Recommendation.** Change to `vocab:1508300`. Both records are unlocked at
`les:n3-conectores-05` (topic 38), well before `les:n3-intencao-03` (topic 43), so the swap is
gating-clean.

**Confidence.** Certain.

**What the teacher should check.** Nothing blocking. Note the neighbouring pair in the same
list (皮/かわ vs 革/かわ, "mesma leitura, kanji diferente") — the list is deliberately about
look-alikes, which makes a mis-pointed card there especially confusing.

---

## 8. 柄 in `les:n3-perspectiva-02` — keep `vocab:1508290` (え)

**Question.** Same pair as row 7.

**Evidence.** The body glosses it:

> `<vocab ref="vocab:1508290"/>: cabo, punho`

"Cabo, punho" is `vocab:1508290`'s only sense; がら has no handle sense. The list is the え/う
run described in row 5, and 柄/え belongs in it.

**Recommendation.** Keep `vocab:1508290`.

**Confidence.** Certain.

**What the teacher should check.** Worth being aware that rows 7 and 8 pull in opposite
directions on purpose: the course teaches both readings of 柄 in different places. That is
fine, but the two lessons should not be "fixed" to agree with each other.

---

## 9. 注ぐ in `les:n3-desejos-05` — keep `vocab:1581730` (そそぐ)

**Question.** 注ぐ names `vocab:1581730` (そそぐ, "pour / flow into / devote") and
`vocab:2145240` (つぐ, "pour, fill a glass").

**Evidence.** The body prints the reading:

> `<vocab ref="vocab:1581730"/> (そそぐ) - despejar, servir um líquido.`

It sits under the heading *"Cuidar, servir e crescer"* in a そ-reading run (**そそぐ**, 育つ
そだつ, 備える そなえる).

**Recommendation.** Keep `vocab:1581730`.

**Confidence.** Certain.

**What the teacher should check.** Nothing. If you want the つぐ contrast taught, it already has
its own home at `les:n3-tempo-06`.

---

## 10. 額 in `les:n3-estado-01` — keep `vocab:1207500` (がく)

**Question.** 額 names `vocab:1207500` (がく, "amount, sum / picture frame") and `vocab:1207510`
(ひたい, "forehead").

**Evidence.** The body prints the reading:

> `<vocab ref="vocab:1207500"/>(<jp>がく</jp>) = "moldura, quadro emoldurado".`

がく matches, and "moldura" is がく's second sense. It sits in a がく run (化学 かがく, 学 がく,
学習 がくしゅう, 学者 がくしゃ, **額 がく**, 覚悟 かくご) — a deliberate homophone drill.

**Recommendation.** Keep `vocab:1207500`.

**Confidence.** Certain.

**What the teacher should check.** The lesson teaches only the "frame" sense. `vocab:1207500`'s
*first* sense is "quantia, montante", which is the more frequent one in real text (金額, 総額).
Consider whether the card should lead with "quantia" and mention "moldura" second, so the
registry and the lesson agree on what the word primarily means.

---

## 11. 品 in `les:n3-conjectura-03` — change to `vocab:1583470` (しな)

**Question.** 品 names `vocab:1583470` (しな, "goods, article, item / quality") and
`vocab:2648780` (ひん, "article / elegance, refinement"). This row was settled by the frequency
heuristic (ひん 5× vs しな 0× in the bank).

**Evidence.** The frequency heuristic was overridden by explicit prose. The body prints the
reading:

> `<vocab ref="vocab:2648780"/> (<jp>しな</jp>) = "artigo, mercadoria";`

Reading しな, gloss "artigo, mercadoria" — that is `vocab:1583470`. The list is a し-reading run
(しきりに, しばしば, じっと, しげき, **しな**, しまった), which corroborates. And the introducing
lesson for ひん, `les:n3-perspectiva-06`, teaches a completely different sense in a ひ-run:

> «品/ひん» (ひん) - elegância, classe, aquele requinte que uma pessoa tem.

So the two lessons already divide the work: ひん = "elegance" at `les:n3-perspectiva-06`,
しな = "goods" here.

**Recommendation.** Change to `vocab:1583470`. That record is already unlocked at
`les:n3-perspectiva-06` (topic 40), before `les:n3-conjectura-03` (topic 49), so the swap is
gating-clean. It would also give しな its only body appearance in the whole course — at present
the record is unlocked and never shown.

**Confidence.** Certain.

**What the teacher should check.** This is the clearest case of the frequency heuristic being
wrong. The bank counted ひん more often, but the bank counts compounds (作品, 製品, 商品), not
the standalone noun the lesson is teaching. Treat the "frequency" evidence in the other three
`frequency` rows with the same suspicion.

---

## 12. 後 in `les:n3-limites-04` — keep `vocab:2147630` (ご)

**Question.** 後 names `vocab:1269330` (のち, noun/adverb "later, afterwards") and
`vocab:2147630` (ご, noun-suffix "after"). Settled by frequency (ご 6× vs のち 1×).

**Evidence.** The frequency call happens to be right, and prose confirms it. The body glosses:

> `<vocab ref="vocab:2147630"/> depois, após.`

which is a verbatim echo of the introducing lesson `les:n3-conectores-05`:

> «後/ご» (ご) - depois, após. Leitura on'yomi, comum em palavras compostas.

Position corroborates: the list runs 憲法 けんぽう → 権利 けんり → **後** → 恋 こい → 濃い こい →
恋人 こいびと → 幸運 こううん → 講演 こうえん → 効果 こうか. That slot is the こ/ご row; のち
would sort under の, far away. Meanwhile のち has its own home at `les:n3-conjectura-06`.

**Recommendation.** Keep `vocab:2147630`.

**Confidence.** Certain (upgraded from the frequency-only evidence in the review file).

**What the teacher should check.** ご is a bound suffix. A bare card reading 後 = "depois, após"
invites a learner to say ×後行きます. Consider presenting it as 〜後（ご） with 三日後 / 食後 so
the bound status is visible on the card itself.

---

## 13. 金 in `les:n3-deveres-03` — change to `vocab:1242600` (きん)

**Question.** 金 names `vocab:1242590` (かね, "money / metal") and `vocab:1242600` (きん,
"gold / money"). Settled by frequency (かね 46× vs きん 1×).

**Evidence.** The frequency heuristic is wrong here, and prose says so plainly:

> `<vocab ref="vocab:1242590"/> (<jp>きん</jp>) = 'ouro (metal)'.`

Reading きん, gloss "ouro (metal)" — that is `vocab:1242600`, whose first sense is exactly
"ouro". The introducing lesson `les:n3-conectores-05` uses the same wording:

> «金/きん» (きん) - ouro (o metal). O mesmo kanji de dinheiro, lido きん quando é o metal precioso.

The list is a き-reading run (級 きゅう, 霧 きり, 切れ きれ, 切れる きれる, **金 きん**), and the
whole block is explicitly about reading-alike traps.

**Recommendation.** Change to `vocab:1242600`. Both records are unlocked at
`les:n3-conectores-05` (topic 38), before `les:n3-deveres-03` (topic 44), so the swap is
gating-clean.

**Confidence.** Certain.

**What the teacher should check.** Nothing blocking. This row and row 11 are both frequency
misfires in the same direction: the bank's 46 かね hits come from お金, which is not what this
lesson is teaching.

---

## 14. 金 in `les:n3-estado-04` — keep `vocab:1242590` (かね)

**Question.** Same pair as row 13.

**Evidence.** The body prints the reading:

> `<vocab ref="vocab:1242590"/>(<jp>かね</jp>) = "dinheiro".`

It sits in a か-reading run (悲しむ かなしむ, 必ずしも かならずしも, かなり, 可能 かのう,
**金 かね**, 株 かぶ, 紙 かみ). Correct on both reading and ordering.

**Recommendation.** Keep `vocab:1242590`.

**Confidence.** Certain.

**What the teacher should check.** Nothing. Note that rows 13 and 14 disagree deliberately —
the course teaches both readings of 金 in different lessons, as with 柄.

---

# Part 2 — `coverage_exemptions.json`

Nine records sit at a taught level with no lesson unlocking them, each the homograph sibling of
a record the course does teach. The current list was verified against the file and is complete
and accurate: 何方/どなた, 君/くん, 止める/とめる, 側/そば, 中/なか, 様/よう, 年/ねん, 背/せ,
何/なん.

## Summary

| Record | Word | Verdict | Natural placement | Confidence |
|---|---|---|---|---|
| `vocab:1189370` | 何方 どなた | **Teach** | `les:n5-passado-05` | certain |
| `vocab:1247260` | 君 くん | **Teach** | `les:n4-passiva-02` | probable |
| `vocab:1310670` | 止める とめる | **Teach** | `les:n4-condicionais-01` | certain |
| `vocab:1403830` | 側 そば | **Teach** | `les:n5-particulas-lugar-02` | certain |
| `vocab:1423310` | 中 なか | **Teach** | `les:n5-comparacoes-02` | certain |
| `vocab:1605840` | 様 よう | **Curriculum call** | `les:n4-suposicao-04`, or keep exempt | genuinely ambiguous |
| `vocab:2084840` | 年 ねん | **Teach** | `les:n5-numeros-tempo-05` | probable |
| `vocab:2147990` | 背 せ | **Teach** | `les:n5-conectando-04` | probable |
| `vocab:2846738` | 何 なん | **Teach** | early — see §9 | certain (placement: probable) |

**Eight of nine should be taught. None should be dropped.** Every one is a `common: true`
record with `level_confidence: 1.0`, and in five cases the lesson prose already introduces the
word — only the unlock ledger does not know. Six of the nine also expose a problem with the
*sibling that was taught*, flagged in each section and gathered at the end.

---

## 1. `vocab:1189370` — 何方 / どなた ("who", polite)

**Question.** Is どなた worth teaching at N5, and where?

**Evidence.** `level_confidence: 1.0`, `level_agreement: 4/4`, `common: true`. Sentence bank:
3 tokens (vs 17 for どちら). どなた is the polite counterpart of 誰 and appears in the first
service-encounter exchanges a learner meets (どなたですか / どちら様ですか).

The placement writes itself. `les:n5-passado-05` already teaches it in prose:

> ...é também a forma educada de 'qual (dos dois)' e até de 'quem'. **Lido como どなた, vira uma
> maneira polida de perguntar 'quem é?'.**

**Recommendation.** Unlock `vocab:1189370` at `les:n5-passado-05`, alongside `vocab:1189360`.
No new content is needed — the sentence explaining どなた is already written. Remove the
exemption entry.

**Confidence.** Certain.

**What the teacher should check.** Whether both readings on one line is too much for that point
in N5, given the lesson's actual subject is the prohibitive な. If it is, the alternative is to
move the どなた half-sentence to a politeness lesson and unlock it there. Do not leave it
unlocked-and-taught, which is the current state.

---

## 2. `vocab:1247260` — 君 / くん (name suffix)

**Question.** Is the くん suffix worth teaching at N4, and where?

**Evidence.** `level_confidence: 1.0`, `level_agreement: 3/3`, `common: true`. Sentence bank:
1 token for the suffix record, 17 for きみ by reading. The bank undercounts it badly — name suffixes attach to
proper nouns, which the bank has few of — but real-world exposure is enormous: any learner
watching or reading anything meets 〜くん in the first hour.

The course already teaches the rest of the family and has a lesson that is visibly the
honorific-register lesson. `les:n4-passiva-02` (*"Diz-se que... (とされている) e o registro
respeitoso"*) teaches 召し上がる, 拝見, the honorific prefix ご, and a 様 suffix card, and it
already contrasts きみ explicitly:

> «君/きみ» (きみ) é um "você" casual, nada respeitoso, oposto ao tom desta lição.

ちゃん is taught separately at `les:n4-experiencia-03`. さま at `les:n4-suposicao-03`.

**Recommendation.** Unlock `vocab:1247260` at `les:n4-passiva-02`, as part of the suffix ladder
さん / 様 / くん / ちゃん. One added line of prose is needed. Remove the exemption entry.

**Confidence.** Probable — the record clearly deserves teaching; the placement is the strongest
of several reasonable ones.

**What the teacher should check.** Whether the suffix ladder is better collected in one place
(it is currently spread over three lessons in two topics) — and whether the pt-BR framing warns
that 〜くん is not simply "male ちゃん": it is used to juniors of either gender in workplaces and
schools, which surprises learners.

---

## 3. `vocab:1310670` — 止める / とめる ("stop something, park, switch off")

**Question.** Worth teaching at N4, and where?

**Evidence.** `level_confidence: 1.0`, `4/4`, `common: true`. Bank: 3 tokens on the slug, and
by reading, 止め-forms outnumber やめ-forms 7 to 1. とめる is the transitive "bring to a halt"
that pairs with 止まる (とまる) — a canonical N4 transitivity pair — and it carries 車を止める,
音を止める, 息を止める.

The lesson already teaches it. `les:n4-condicionais-01` (*"Condicional たら"*) glosses it and
conjugates it:

> «止める/とめる» (parar, desligar) → `<jp reading="とめたら">止めたら</jp>` ("se/quando parar")

**Recommendation.** Unlock `vocab:1310670` at `les:n4-condicionais-01` (topic 23), which
precedes nothing that needs it earlier. Remove the exemption entry. No new content needed.

**Confidence.** Certain.

**What the teacher should check.** The やめる sibling is taught later, at
`les:n4-oracoes-relativas-01` (topic 22 — actually *earlier* in sequence), glossed "parar uma
atividade". Having both is right; consider whether one of the two lessons should carry an
explicit とめる vs やめる contrast, since the identical kanji with opposite argument structure
is a classic N4 trap.

---

## 4. `vocab:1403830` — 側 / そば ("beside, near")

**Question.** Worth teaching at N5, and where?

**Evidence.** `level_confidence: 1.0`, `4/4`, `common: true`. Bank: そば 5 tokens vs がわ 3 — the
**exempted** sibling outscores the taught one. そば is a core N5 position noun, taught in every
standard syllabus alongside 上・下・前・後ろ・となり.

The lesson already teaches it, in the ideal spot. `les:n5-particulas-lugar-02` (*"Existência na
fala casual: ある e いる"*) lists it inside a そ-reading run:

> «其処/そこ»: aí ... «其方/そちら»: por aí ... **«側/そば»: ao lado, pertinho** ... «外/そと»:
> fora ... «園/その»: jardim ... «空/そら»: céu

with the existence sentences (そこにネコがいる, 外に犬がいる) right underneath — exactly the frame
そば needs (〜のそばにある/いる).

**Recommendation.** Unlock `vocab:1403830` at `les:n5-particulas-lugar-02`. Remove the exemption
entry. No new content needed.

**Confidence.** Certain.

**What the teacher should check.** **The taught sibling looks like the wrong priority.**
`vocab:1581310` (側/がわ, "side") is unlocked at `les:n5-perguntas-01` (topic 08) inside an
orientation list (角 かど, 側 がわ, 北 きた, 方 かた), while そば — more frequent in our own bank
and far more useful to a beginner — waits until topic 11 and is never unlocked. Consider whether
がわ needs to be at topic 08 at all, or whether it would sit better later as the 〜側 suffix
(右側, 向こう側).

---

## 5. `vocab:1423310` — 中 / なか ("inside, middle")

**Question.** Worth teaching at N5, and where?

**Evidence.** This is the most lopsided pair in the set. `level_confidence: 1.0`, `4/4`,
`common: true`. Bank by reading: **なか 70, ちゅう 29**. Bank by slug: the なか record has 11
tokens; the taught ちゅう record has **0**.

And the lesson already teaches it, by name, as the load-bearing piece of its grammar point.
`les:n5-comparacoes-02` (*"O superlativo: 一番 e ～の中で"*):

> A peça `<vocab ref="vocab:1423310"/>`(なか) quer dizer "dentro/interior", e 〜の中で delimita o
> conjunto comparado: "entre/dentre...".

**Recommendation.** Unlock `vocab:1423310` at `les:n5-comparacoes-02`. Remove the exemption
entry. No new content needed. Note this is also the record `les:n4-oracoes-relativas-01`
("こと e の中で") depends on later.

**Confidence.** Certain.

**What the teacher should check.** **The taught sibling is the questionable one.**
`vocab:1620400` (中/ちゅう) is unlocked at `les:n5-numeros-tempo-04`, where it is taught not as
the "in progress" suffix (勉強中, 工事中) but as a *size*:

> Num cardápio ou numa loja você vê 大 para a porção grande e 中 para a média.

That is a legitimate but marginal use of a record whose registry gloss is "durante, no meio de,
em processo de". Two things to decide: (a) whether the size sense deserves the N5 card at all,
and (b) whether 中/ちゅう should instead be introduced as 〜中 ("durante"), which is what its own
gloss describes and what learners actually meet. Either way, なか must be unlocked — a course
that teaches 中 the size before 中 the "inside" has its priorities inverted.

---

## 6. `vocab:1605840` — 様 / よう ("appearance, seeming; like")

**Question.** Worth teaching at N4, and where? This one is a curriculum call, and the premise
behind the question needs correcting first.

**Evidence.** `level_confidence: 1.0`, `2/2`, `common: true`. Bank: よう 7 tokens, さま 7 — even.

The natural first guess is that `les:n4-suposicao-03` (the み-family lesson) must really be
teaching よう, not the honorific さま. **The lesson prose says otherwise, explicitly:**

> «様/さま»: **lido さま**, é o "primo formal" que dá origem a のよう, a versão de registro mais
> sério que você vê na próxima lição.

So the さま unlock at `les:n4-suposicao-03` is deliberate and correct: さま is introduced as the
etymological source of のよう, and the lesson hands off to `les:n4-suposicao-04`
(*"のよう: comparar de modo formal (〜のような・のように)"*).

**However, there is a genuine defect next door.** `vocab:1605840` (よう) has exactly one
reference in the entire course, in `les:n4-passiva-02`, and the prose there describes the
honorific:

> «様/よう»: sufixo de respeito, usado depois de nomes de pessoas para soar bem cortês.

"Sufixo de respeito, usado depois de nomes de pessoas" is `vocab:1545790` (さま). That reference
is pointing at the wrong record. It is a body-only reference, so gating is unaffected — but the
learner is shown a よう card captioned as an honorific.

**Recommendation.** Two steps, in order.

1. **Fix first:** repoint the `les:n4-passiva-02` body reference from `vocab:1605840` to
   `vocab:1545790`. `vocab:1545790` is unlocked at `les:n4-suposicao-03` (topic 31), before
   `les:n4-passiva-02` (topic 32), so this is gating-clean. After this, `vocab:1605840` has zero
   references anywhere.
2. **Then decide:** either unlock `vocab:1605840` at `les:n4-suposicao-04`, where のよう is
   taught and where the record is the actual word behind the pattern; or keep the exemption and
   restate its reason — the よう of のよう reaches the learner as grammar (`gram:gp-77`), written
   in kana throughout `les:n4-suposicao-04`, so a separate vocab card would duplicate it.

There is a real argument on both sides, which is why this is the one item here that is not a
lookup. The tie-breaker is a policy question the teacher owns: **does every grammar-bearing
noun get a vocab card, or only the ones a learner meets standalone?** Whatever is decided
should be applied consistently to こと, もの, ところ and the rest of the formal-noun family.

**Confidence.** Genuinely ambiguous on the placement. Certain on step 1.

**What would settle it.** A stated policy on formal nouns delivered as grammar. Absent that, the
narrower question — "would a learner ever need to recognise 様 written in kanji and read it
よう?" — resolves it: if yes (様子, ご様子, 〜のような in written text), unlock it at
`les:n4-suposicao-04`; if no, keep it exempt with the corrected reason.

---

## 7. `vocab:2084840` — 年 / ねん ("year")

**Question.** Worth teaching at N5, and where?

**Evidence.** `level_confidence: 1.0`, `2/2`, `common: true`. Bank by reading: **ねん 23, とし 11**.
ねん is the year counter — 2026年, 何年, 一年, 来年 — which is unavoidable N5 material.

The course's handling of this pair is currently upside down in a small way. The taught sibling
`vocab:1468060` (年/とし) is unlocked at `les:n5-passado-02` and appears in **no lesson body at
all** — an unlock with no teaching. Meanwhile ねん appears in the body of `les:n5-comparacoes-04`
(topic 14), in a な/に-reading run:

> «夏/なつ»: verão ... «夏休み/なつやすみ» ... «日曜日/にちようび» ... «日/ひ»: dia ...
> **«年/ねん»: ano** ... «西/にし»: oeste

but is unlocked nowhere.

A better home exists. `les:n5-numeros-tempo-05` (*"Tempo, dias e datas"*, topic 09) is the
lesson that teaches durations and the calendar and introduces `kanji:年` directly:

> vamos contar tempo: horas, semanas, meses, anos e os dias do calendário ... dois kanji que
> aparecem o tempo todo (日 e 年)

**Recommendation.** Unlock `vocab:2084840` at `les:n5-numeros-tempo-05`, where the kanji and the
counter frame are already being taught, rather than at `les:n5-comparacoes-04` where it is a
loose list item. Remove the exemption entry. Requires one line of prose at numeros-tempo-05 and
leaves the comparacoes-04 mention as a legitimate re-encounter.

**Confidence.** Probable — certain that it must be taught, probable on which of the two lessons.

**What the teacher should check.** The other half of the pair: とし is unlocked at
`les:n5-passado-02` with no prose anywhere. Either give it a teaching moment (年を取る,
今年, 年上/年下 — all high-value) or move its unlock. An unlock nobody teaches is a silent
hole in the SRS deck.

---

## 8. `vocab:2147990` — 背 / せ ("height; back")

**Question.** Worth teaching at N5, and where?

**Evidence.** `level_confidence: 1.0`, `2/2`, `common: true`. Bank: 11 tokens on the せ record.

The decisive number is on the other side. `vocab:1472650` (背/せい), the *taught* sibling, has 9
bank tokens — and **every one of those tokens carries the reading せ, not せい.** Across the
entire bank, the lemma 背 appears with reading せ 12 times and with reading せい zero times. The
tokenizer attached せ-pronounced tokens to the せい record.

The prose is split across two lessons. `les:n5-numeros-tempo-03` teaches the せい record as the
height word:

> «背/せい»: altura, estatura (da pessoa).

and `les:n5-conectando-04` lists the せ record as the body part:

> «背/せ»: costas

**Recommendation.** Unlock `vocab:2147990` at `les:n5-conectando-04`, where it is already
listed. Remove the exemption entry. No new content needed for that step.

**Confidence.** Probable.

**What the teacher should check.** **The taught sibling looks wrong.** 背が高い / 背が低い — the
sentence pattern `les:n5-numeros-tempo-03` is building toward — is normally read せがたかい. せい
exists and is not an error, but it is the less common variant, and our own bank never produces
it. Two options: (a) repoint the "altura, estatura" card at `les:n5-numeros-tempo-03` to
`vocab:2147990` (せ) and let `les:n5-conectando-04` re-encounter it as "costas", which would make
this exemption disappear entirely and is probably the right answer; or (b) keep both and add a
note that せい is the formal variant. Option (a) also fixes the tokenizer/registry mismatch.

---

## 9. `vocab:2846738` — 何 / なん ("what; how many")

**Question.** Worth teaching at N5, and where?

**Evidence.** The strongest case in the set. `common: true`, `level_confidence: 1.0` (though
`level_agreement` is only `1/1` — see below). Bank by reading: **なん 87, なに 60.** The
exempted reading is the *more frequent* one.

なん is not an optional variant. It is the reading in 何ですか, 何時, 何人, 何回, 何歳 — the
question forms a beginner uses from week one. And the course already relies on it from its
first topic, long before either 何 record is unlocked:

- `les:n5-desu-wa-02` (topic 07): "A versão completa e polida seria
  `<jp reading="あれはなんですか">あれは何ですか</jp>`"
- `les:n5-desu-wa-03` (topic 07): "`<jp reading="なんじですか">何時ですか</jp>` ('que horas são?')"

The taught sibling `vocab:1577100` (何/なに) is not unlocked until `les:n5-comparacoes-02`
(topic 14), where the prose itself annotates the card with both readings — "«何/なに»(**なに/なん**):
'o quê'" — quietly admitting that one record is doing two jobs. なん is separately listed in
`les:n5-conectando-01` (topic 18) as "o quê / que, para perguntar 'por quê?'" but unlocked
nowhere.

**Recommendation.** Teach it, and teach it early. The mechanically cheapest fix is to unlock
`vocab:2846738` at `les:n5-conectando-01`, where it is already listed. The pedagogically correct
fix is to move **both** 何 records forward to topic 07–08, where the course already uses them,
and introduce them as a pair: なに standalone, なん before です and before counters. Remove the
exemption entry either way.

**Confidence.** Certain that it must be taught. Probable on placement — the topic 07–08 move is
better teaching but a larger edit that touches the gating ledger.

**What the teacher should check.** Two things. First, `vocab:2846738` carries
`level_agreement: 1/1` — a single community list — against `4/4` for なに. Under the project's
own consensus rule (CLAUDE.md §1.5) that is a thin level assignment, even though
`level_confidence` reads 1.0. Worth confirming the N5 tag is not an artefact of one source.
Second, the deeper issue this exposes: 何 is used in lesson prose from topic 07 but not unlocked
until topic 14. That is a gating question rather than a homograph question, and it is
`validate_lesson_gating`'s territory, but it is the reason this exemption looks so strange.

---

# Cross-cutting findings

Three patterns worth acting on beyond the individual rows.

**1. The exporter's disambiguation heuristics ignored the one signal that works.** Every lesson
body that mentions a homograph prints the reading inside `<jp>…</jp>` right next to the
reference, or gives a gloss unique to one record. That signal resolved 12 of 14 rows outright
and contradicted the stored choice in 4 of them. Neither the sibling-ref heuristic nor the
lesson-level heuristic nor the bank-frequency heuristic looks at it. If the resolver is ever
re-run, reading the adjacent `<jp>` annotation should come first, ahead of frequency.

**2. The `frequency` verdicts are the least reliable, not the most.** Two of the four
frequency-settled rows (品, 金) picked the wrong record, because bank counts are dominated by
compounds (作品/製品 for ひん, お金 for かね) while the lessons were teaching the standalone noun
in its other reading. The two that happened to be right (後, and the second 金 row) are right for
reasons the prose confirms independently. The label "settled by frequency" in
`vocab_disambiguation_review.json` should not be read as more settled than "unresolved".

**3. Six of the nine exemptions expose a problem with the sibling that *was* taught**, not just
with the one that was not:

| Pair | The problem with the taught sibling |
|---|---|
| 中 なか / ちゅう | ちゅう taught (0 bank tokens) as a menu *size*; なか (70 by reading) untaught |
| 背 せ / せい | all 9 bank tokens on the せい record actually read せ |
| 側 そば / がわ | がわ taught at topic 08; そば (more frequent, core position noun) untaught |
| 年 ねん / とし | とし unlocked at `les:n5-passado-02` with no prose anywhere in the course |
| 何 なん / なに | なに unlocked at topic 14 though 何 is used in prose from topic 07 |
| 様 よう / さま | さま is correct where it is, but the *よう* reference at `les:n4-passiva-02` describes さま |

These are not homograph-resolution bugs. They are sequencing and card-design decisions that the
homograph audit happened to surface, and each needs the teacher's judgement rather than a
script.

---

# Suggested order of work for the reviewer

1. **Four certain reference corrections** (Part 1 rows 2, 7, 11, 13) — all body-only, all
   gating-clean, all pointing at records already unlocked. Lowest risk, highest clarity gain.
2. **One certain reference correction in Part 2** (§6 step 1, `les:n4-passiva-02` 様 → さま).
3. **Five no-new-content unlocks** (Part 2 §§1, 3, 4, 5, 8) — the prose already teaches these
   words; only the ledger disagrees.
4. **Two placement decisions needing a line of prose** (Part 2 §§2, 7 — くん, ねん).
5. **Two curriculum decisions** (Part 2 §6 step 2 — 様/よう policy on formal nouns; §9 — whether
   to move 何 forward to topic 07–08).
6. **One deferred question** (Part 1 rows 4–5 — whether うる or える should own the 得る card at
   `les:n3-conectores-05`), which then settles both perspectiva references.

After any of these are applied, re-run the exporter and the validators so
`vocab_disambiguation_review.json` and `coverage_exemptions.json` shrink to match — per
CLAUDE.md, an exemption that matches nothing is itself a validation failure, so stale entries
cannot be left behind.
