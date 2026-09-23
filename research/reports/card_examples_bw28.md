# B-W28: card example coverage under two wider admission rules (2026-09-23)

Measurement for the owner decision B-W28 (`research/reports/w28_card_examples_report.md` §4). Nothing
applied. Two pending tables, derived on a snapshot, each in the exact row shape of
`research/derived/repairs/card_examples.json`:

- `research/derived/pending/card_examples_option_a.json` (2,858 rows)
- `research/derived/pending/card_examples_option_b.json` (3,794 rows)

Authored 0. Every sentence is a bank row that already exists (spec §1.2 holds: selection only).

## 1. Method

Tree: `git archive HEAD` of `scripts/ course/ corpus/ contracts/ design/` into scratch (the working
tree is mid-write by another chain). A scratch copy of `scripts/derive_card_examples.py` gained a
`--rule {current,A,B}` flag. The cloze code (`vocab_span`, `gram_span`, `kanji_span`, `span_ok`) and
the candidate pools are untouched; only the admission test inside `ranked()` and the ranking key moved.

Control: `--rule current` reproduces the applied table row for row (2,242 rows, `rows` identical to
HEAD's `card_examples.json`). HEAD now has 211 kana cards against the W28 report's 57 (W29 split the
families into glyph cards); they get no example under any rule, by design.

The rules, at the card's lesson L:

| rule | a sentence L does not render is admitted when |
|---|---|
| current | graded at or below L's level, kanji + words outside L's `cumulative_known_set` <= BUDGET[level] (pre-N5 0, N5 1, N4 2, N3 2), no unlinked content token |
| A | graded at most **one** level above L's level; same budget; no unlinked content token |
| B | **any** grade; at most **2 content words** (split-mode-C vocab tokens, `fit`'s `new_v`) outside L's known set; kanji not counted; no unlinked content token |

All three keep: model-text register, a pt-BR translation, the card's item in the sentence, a cloze
span. B keeps the unlinked-token guard because an unlinked content token is a word the dissection
cannot gloss, so it cannot be counted either way. The card's own word is always in L's known set
(2,951 / 2,951 vocab cards checked), so it never counts against the budget.

Ranking: today's admitted set ranks exactly as W28 (rendered, i+0, load, real over generated,
shorter, hash); an option's extra sentences rank after all of them, fewest levels above L first.
Grammar keeps tagged before spelled inside each group. Consequence, checked: **every one of the 2,242
applied rows is byte-equal in both option tables**; an option only adds rows to cards that have none.

## 2. Coverage (cards with an example / cards)

| namespace | level | current | A | B | cards |
|---|---|---|---|---|---|
| vocab | pre-N5 | 0 | 0 | 14 | 24 |
| vocab | N5 | 163 | 272 | 635 | 688 |
| vocab | N4 | 230 | 420 | 611 | 643 |
| vocab | N3 | 863 | 1,118 | 1,458 | 1,596 |
| **vocab** | all | **1,256** | **1,810** | **2,718** | 2,951 |
| grammar | N5 | 99 | 125 | 135 | 150 |
| grammar | N4 | 180 | 182 | 182 | 212 |
| grammar | N3 | 125 | 125 | 126 | 132 |
| **grammar** | all | **404** | **432** | **443** | 494 |
| kanji | N5 | 76 | 91 | 103 | 103 |
| kanji | N4 | 174 | 184 | 187 | 187 |
| kanji | N3 | 332 | 341 | 343 | 344 |
| **kanji** | all | **582** | **616** | **633** | 634 |
| kana | pre-N5 | 0 | 0 | 0 | 211 |
| **total** | | **2,242** | **2,858** | **3,794** | 4,290 |

No example, by reason (current / A / B): none passes the display rule 1,603 / 977 / 46; no alignable
span 162 / 172 / 167; no bank sentence carries the item 72 / 72 / 72; kana glyph 211 / 211 / 211.

## 3. What the extra rows are

| | A (616 added) | B (1,552 added) |
|---|---|---|
| by namespace | vocab 554, kanji 34, grammar 28 | vocab 1,462, kanji 51, grammar 39 |
| sentence grade | N4 150, N3 202, N2 264 | N5 57, N4 321, N3 353, N2 424, N1 397 |
| levels above L | +1: 616 | +0: 70, +1: 833, +2: 517, +3: 104, +4: 28 |
| words outside the known set | 0: 509, 1: 104, 2: 3 | 0: 1,039, 1: 372, 2: 141 |
| kanji outside the known set | 0: 109, 1: 403, 2: 104 | 0: 128, 1: 811, 2: 480, 3: 104, 4: 20, 5: 6, 6: 3 |
| real (Tatoeba) / AI-generated | 503 / 113 | 1,206 / 346 |

By lesson level, B's additions: N5 cards 50 at +0, 311 at +1, 97 at +2, 50 at +3, 27 at +4 (N1
sentences on N5 cards); pre-N5 cards 14, from N4 to N1. The +0 rows (70) are at-level sentences
that only fail today's kanji half of the budget or have 2 unknown words where N5 allows 1.

Reading the numbers:

- **A** stays inside check D's arithmetic (same budget, unknown kanji + words <= 2) and moves the
  grade limit by one step. The cost is the grammar the grade reflects and the budget does not count:
  a one-level-up sentence may carry a form taught one level later. Vocab N5 moves 163 -> 272 (40%).
- **B** reaches almost every vocab card (2,718 / 2,951; N5 635 / 688) but drops two guards at once:
  the grade (so N1 grammar can reach an N5 or pre-N5 card) and the kanji count (up to 6 unknown kanji
  in a sentence). The "2 words" bound is the only thing between a beginner and the sentence.
- Both lean on the bank's AI-generated rows (18% and 22% of the additions); those rows are already
  `ai_generated` + `needs_review` in the bank, and real sentences still rank first.

## 4. Samples (20 per option, from the added rows)

Stratified: 10 vocab, 5 grammar, 5 kanji, rotating pre-N5 / N5 / N4 / N3, stable hash order.
`＿＿` is the stored cloze; the pt-BR line is the bank's translation (Layer B, as stored).

### Option A

| # | card (lesson) | sentence | grade | cloze | pt-BR | words out |
|---|---|---|---|---|---|---|
| 1 | `vocab:1310730` (les:n5-verbos-04) | `sent:tatoeba-208758` | n4 (+1) | その人は＿＿かけていた。 | Aquela pessoa estava morrendo. | 0 |
| 2 | `vocab:1596930` (les:n4-volitivo-02) | `sent:tatoeba-8725904` | n3 (+1) | 誰もけがをしてないって、＿＿なの？ | Tem certeza de que ninguém se machucou? | 1 |
| 3 | `vocab:1214540` (les:n3-intencao-03) | `sent:tatoeba-1522677` | n2 (+1) | この＿＿は空だ。 | Esta lata está vazia. | 0 |
| 4 | `vocab:1341000` (les:n5-te-form-03) | `sent:tatoeba-147608` | n4 (+1) | ＿＿はまもなくやってくる。 | A primavera chegará em breve. | 0 |
| 5 | `vocab:1145130` (les:n4-obrigacao-05) | `sent:tatoeba-233659` | n3 (+1) | あなたに払うのか、＿＿で払うのか。 | Eu pago a você ou pago no caixa? | 0 |
| 6 | `vocab:1437960` (les:n3-causa-06) | `sent:tatoeba-11323647` | n2 (+1) | 父は＿＿関係の仕事をしています。 | Meu pai trabalha no ramo ferroviário. | 0 |
| 7 | `vocab:1096420` (les:n5-te-form-04) | `sent:tatoeba-223305` | n4 (+1) | この＿＿は紙でできているんです。 | Este lenço é feito de papel. | 0 |
| 8 | `vocab:1451490` (les:n4-condicionais-03) | `sent:tatoeba-5217` | n3 (+1) | 昨日＿＿に行った。 | Ontem eu fui ao zoológico. | 0 |
| 9 | `vocab:1212210` (les:n3-intencao-04) | `sent:tatoeba-231218` | n2 (+1) | あの医者は＿＿に優しい。 | Aquele médico é gentil com os pacientes. | 0 |
| 10 | `vocab:1008190` (les:n5-comparacoes-01) | `sent:gen-52e853b5eb16` (gen.) | n4 (+1) | ＿＿話はもう聞きたくない | Não quero mais ouvir conversa chata. | 1 |
| 11 | `gram:te-wa-ikenai` (les:n5-te-form-05) | `sent:tatoeba-184859` | n4 (+1) | 外へ出＿＿。 | Não pode sair. | 1 |
| 12 | `gram:gp-75` (les:n4-suposicao-07) | `sent:gen-317371c921a3` (gen.) | n3 (+1) | 父はいつも忙し＿＿ | Meu pai vive dizendo que está ocupado. | 0 |
| 13 | `gram:o-kudasai` (les:n5-verbos-06) | `sent:tatoeba-150556` | n4 (+1) | 時間＿＿。 | Me dê um tempo, por favor. | 1 |
| 14 | `gram:gp-91` (les:n4-condicionais-08) | `sent:tatoeba-175592` | n3 (+1) | 月曜日は日曜日＿＿くる。 | A segunda-feira vem depois do domingo. | 0 |
| 15 | `gram:gp-22` (les:n5-adjetivos-06) | `sent:gen-6a1cc4754f5d` (gen.) | n4 (+1) | 犬は雨の日が＿＿です | Cachorro não gosta de dia de chuva. | 0 |
| 16 | `kanji:火` (les:n5-conectando-07) | `sent:tatoeba-186754` | n4 (+1) | ＿＿にあたりながらすわっていた。 | Ficávamos sentados nos aquecendo perto do fogo. | 1 |
| 17 | `kanji:通` (les:n4-oracoes-relativas-01) | `sent:gen-0834a2b2f7a1` (gen.) | n3 (+1) | この道はもう＿＿まいと思った | Pensei que nunca mais passaria por este caminho. | 0 |
| 18 | `kanji:城` (les:n3-estrutura-01) | `sent:tatoeba-229712` | n2 (+1) | あれは古いお＿＿です。 | Aquilo é um castelo antigo. | 0 |
| 19 | `kanji:道` (les:n5-kanji-exame-03) | `sent:tatoeba-123591` | n4 (+1) | ＿＿はずっとのぼりだ。 | A estrada é só subida o caminho todo. | 0 |
| 20 | `kanji:業` (les:n4-forma-simples-05) | `sent:tatoeba-217120` | n3 (+1) | ご＿＿は何ですか。 | Qual é a sua profissão? | 1 |

### Option B

| # | card (lesson) | sentence | grade | cloze | pt-BR | words out |
|---|---|---|---|---|---|---|
| 1 | `vocab:1583250` (les:pre-n5-saudacoes-02) | `sent:tatoeba-229460` | n3 (+3) | ＿＿、あまり降りません。 | Não, não chove muito. | 2 |
| 2 | `vocab:1294940` (les:n5-numeros-tempo-04) | `sent:gen-14c8e2a895a3` (gen.) | n3 (+2) | 妹は十＿＿になりました | Minha irmã mais nova fez dez anos. | 1 |
| 3 | `vocab:1538820` (les:n4-conectores-03) | `sent:gen-c7ea5c7b3772` (gen.) | n2 (+2) | この国は米を＿＿している | Este país exporta arroz. | 0 |
| 4 | `vocab:1214540` (les:n3-intencao-03) | `sent:tatoeba-1522677` | n2 (+1) | この＿＿は空だ。 | Esta lata está vazia. | 0 |
| 5 | `vocab:1527040` (les:pre-n5-saudacoes-03) | `sent:gen-9f80f08cc644` (gen.) | n2 (+4) | この＿＿はちょっと辛いです | Esse missô é um pouco salgado. | 2 |
| 6 | `vocab:1579840` (les:n5-numeros-tempo-01) | `sent:tatoeba-148071` | n5 (+0) | ＿＿時ごろですか。 | É por volta das dez horas? | 2 |
| 7 | `vocab:1309650` (les:n4-conectores-01) | `sent:tatoeba-168243` | n2 (+2) | ＿＿を切るとすぐ血が出る。 | Quando corto o dedo, logo sai sangue. | 0 |
| 8 | `vocab:1386990` (les:n3-intencao-05) | `sent:tatoeba-146306` | n1 (+2) | 象は＿＿する危険がある。 | O elefante corre risco de extinção. | 1 |
| 9 | `vocab:2005860` (les:pre-n5-saudacoes-01) | `sent:tatoeba-3583355` | n4 (+2) | ＿＿やってみる。 | Vou tentar mais uma vez. | 2 |
| 10 | `vocab:1165970` (les:n5-adjetivos-04) | `sent:tatoeba-143461` | n4 (+1) | 世界で＿＿いい仕事だものね。 | É o melhor trabalho do mundo, afinal. | 1 |
| 11 | `gram:te-de` (les:n5-te-form-02) | `sent:gen-a521e722ba56` (gen.) | n4 (+1) | 兄は学生＿＿妹は先生だ | Meu irmão mais velho é estudante e minha irmã mais nova é professora. | 0 |
| 12 | `gram:gp-75` (les:n4-suposicao-07) | `sent:gen-317371c921a3` (gen.) | n3 (+1) | 父はいつも忙し＿＿ | Meu pai vive dizendo que está ocupado. | 0 |
| 13 | `gram:n3-sono-kekka` (les:n3-causa-02) | `sent:tatoeba-211110` | n1 (+2) | ＿＿何が起こったのか。 | E, como resultado, o que aconteceu? | 0 |
| 14 | `gram:te-wa-ikenai` (les:n5-te-form-05) | `sent:tatoeba-184859` | n4 (+1) | 外へ出＿＿。 | Não pode sair. | 1 |
| 15 | `gram:gp-91` (les:n4-condicionais-08) | `sent:tatoeba-175592` | n3 (+1) | 月曜日は日曜日＿＿くる。 | A segunda-feira vem depois do domingo. | 0 |
| 16 | `kanji:火` (les:n5-conectando-07) | `sent:tatoeba-186754` | n4 (+1) | ＿＿にあたりながらすわっていた。 | Ficávamos sentados nos aquecendo perto do fogo. | 1 |
| 17 | `kanji:京` (les:n4-oracoes-relativas-05) | `sent:tatoeba-115217` | n3 (+1) | 彼は１年に１度＿＿する。 | Ele vai a Tóquio uma vez por ano. | 1 |
| 18 | `kanji:城` (les:n3-estrutura-01) | `sent:tatoeba-229712` | n2 (+1) | あれは古いお＿＿です。 | Aquilo é um castelo antigo. | 0 |
| 19 | `kanji:右` (les:n5-conectando-05) | `sent:tatoeba-209586` | n3 (+2) | その車はあそこで＿＿に曲がった。 | O carro virou à direita ali. | 0 |
| 20 | `kanji:通` (les:n4-oracoes-relativas-01) | `sent:gen-0834a2b2f7a1` (gen.) | n3 (+1) | この道はもう＿＿まいと思った | Pensei que nunca mais passaria por este caminho. | 0 |

What the samples show:

- A's rows read as ordinary beginner sentences; the risk shows as grammar one step ahead (A1
  `死にかけていた`, A17 `通るまい` on an N4 kanji card, A13 `時間をください` fine but N4-graded).
- B's pre-N5 rows are the weak end: B1 puts `降りません` on a greetings-lesson card for `いいえ`, B5
  an N2-graded generated sentence on the `味噌` card, both with 2 words the learner has not met.
  B8 and B13 hang N1-graded sentences on N3 cards.
- `sent:tatoeba-115217` (B17) spells numbers full-width (`１年に１度`) and blanks `上京`, a word, on a
  kanji card; that is W28's kanji span rule, unchanged by either option.

## 5. Applying either one

1. Copy the chosen pending file over `research/derived/repairs/card_examples.json` and run
   `scripts/apply_card_examples.py --replace`, then the exporter. Proved on two snapshots of
   `db/corpus.sqlite`: A wrote 616 new examples, B 1,551, 0 rewrites each; a second run wrote 0.
   On the live snapshot 7 rows (8 for B) address no card, all `gram:gp-*` items the writer chain
   is changing; the applied table has the same 7 today, so re-derive once that chain lands.
2. Land the `--rule` flag in `scripts/derive_card_examples.py` (a 93-line diff in the scratch copy:
   the admission test, `gap()`, `unknown_words()`, the ranking key, the grammar group order) so the
   table stays re-derivable, and move `design/srs_design.md` §9 with it.
3. `validate_card_content.py` check F refuses an above-level sentence the lesson does not render
   (plant F8): A needs it to allow +1 within the budget, B needs it replaced by the 2-word test.
   `NO_EXAMPLE_RATCHET` (vocab 1695, gram 90, kanji 52) only moves down, so it tightens to A's or
   B's counts in the same unit.

## 6. Open

- The owner picks A, B or neither (the W13 mining route, growing N5/N4 sentences, which also fixes
  lessons and exams). Not measured: a middle rule (B plus a grade cap of +2 and the kanji half of the
  budget) would drop B's N1-on-N5 and 6-kanji rows; the gap and kanji rows in §3 bound its size.
- No sample was reviewed by a teacher; the 20 + 20 rows above are the review sample for the decision.
