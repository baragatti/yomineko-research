# W13b — how much of the mined N3 Layer-B is derivable, and what is left to author

Measurement only. Read-only against a **copy** of `db/corpus.sqlite` (the real DB was never opened for
write); no exporter, ingest or apply script was run against the tree. Two files were written:
this report and `research/derived/n3_mined/layerb_residue.json`.

Inputs: `research/derived/n3_mined/accepted.json` (4,197 real Tatoeba rows) + `generated.json` (26)
= **4,223 sentences**. Required Layer-B shape learned from `research/derived/mined_layerb/batch-*.json`
(324 sentences), from `scripts/ingest/persist_dissection.py::persist()` and from what
`scripts/validate/validate.py` enforces at `dissection_tier = "full"`.

## Headline

| field | required by the validator | derivable mechanically | to author |
|---|---|---|---|
| token `gloss_pt` (content tokens) | yes, all 17,057 | **16,903 — 99.10 %** | **154 (0.90 %)** |
| particle `function_pt` | no (optional) | 10,246 of 10,257 — 99.89 % | 11 |
| particle `explanation_pt` | yes, all 10,257 | **0 % as bank-quality text** | **10,257** |
| `structure_explanation_pt` | yes, one per sentence | 0 % | **4,223** |
| `role_pt`, `conjugation_note_pt` | no | partial (role hint on 8,466 particles) | — |

The W13b row's claim — "expected ≥ 80 % of tokens derived" — **holds for tokens and is beaten by a wide
margin (99.1 %)**. The row's companion claim — "every particle takes the templated explanation the bank
already uses for that `function_type`" — is **false**: no such templates exist in the bank. The cost of
this unit therefore moved: it is no longer 17,057 glosses, it is 10,257 particle explanations plus 4,223
paragraphs.

## 1. Dissector run

All 4,223 sentences dissected in ~1 s, **0 failures**. The two structural invariants the ingest re-checks
hold on every one: `concat(C surfaces) == jp` (I1) and `kana == concat(token readings)` (I2).

Pre-flight against the copy, using the ingest's own guards: **4,197 rows would ingest cleanly** — jp
matches `raw_tatoeba_sentence` byte-for-byte on every one, 0 slug collisions with the 5,889 already in
the bank, 0 duplicate slugs inside the input.

Volume: 36,282 C-tokens, of which **17,057 are content tokens** (the ones the validator demands a gloss
on) and 19,225 are not; **10,257 particles**.

## 2. Token glosses — 99.10 % derivable

Two rules, applied in this order:

1. **bank** — the modal pt-BR gloss the bank already uses for the same `(surface, lemma, pos_coarse)`
   (falling back to `(lemma, pos_coarse)`). This reuses the bank's own phrasing conventions rather than
   inventing new ones. Fires on **12,835 tokens (75.25 %)**.
2. **registry-sense0** — `"; ".join` of the first three pt-BR glosses of `vocab_sense[sense_order = 0]`
   for the linked vocab record. Fires on a further **4,068 (23.85 %)**.

**Total derived 16,903 / 17,057 = 99.10 %. Residue 154 tokens (0.90 %).**

### Linkage

| | n | % of content |
|---|---|---|
| linked to a vocab record | 16,811 | 98.56 % |
| …of which carry a pt-BR sense gloss | 16,811 | **100 %** |
| …linked but no pt-BR gloss | 0 | 0 % |
| unlinked (Dissector found no vocab) | 246 | 1.44 % |
| …of the unlinked, still glossable from the bank | 92 | — |
| **needs an author** | **154** | **0.90 %** |

Unlinked by POS: noun 213, verb 18, pronoun 9, adnominal 2, adverb 2, na-adjective 1, i-adjective 1.

Unlinked by cause:

| cause | n | fixable how |
|---|---|---|
| linker gap — the registry holds the same reading under another orthography | 26 | mechanically, by widening `Dissector._vocab_by_form` with a kana-normalised index |
| absent — in JMdict, not in our registry | 134 | a vocab-registry insert (Layer A), then it links itself |
| absent — not in JMdict at all (numerals, place names, fragments: `50`, `30`, `20`, `2020`, `この世`, `大阪`) | 86 | a numeral rule covers most; the rest are a gloss each |

The 154-token residue is **39 bare numerals** (`50`, `12`, `30万`, `500万`, …), which a number-formatting
rule would finish without an author, plus **115 real words** over 137 distinct `(lemma, pos)` pairs —
`ついばむ`, `洗い流す`, `溢れかえる`, `商店街`, `乗組員`, `水球`, `ハイウェー`, `私たち` (9 occurrences, a
straight linker gap), and so on. Note `0` of the 246 unlinked tokens resolve through "same JMdict entry
already in the registry", so the mechanical linker fix is small — 26 rows, not hundreds.

### Which sense — the fallback fires on everything

**Lessons do not reference senses.** `lesson_introduces` stores `(lesson_id, member_type='vocab',
member_id)` and `lesson_unlocks` stores a namespaced ref (`vocab:乗る`); neither carries a
`sense_order`. There is no sense pointer anywhere in the courseware schema, so **the sense[0] fallback
fires on 100 % of linked tokens by construction** — it is the same convention
`scripts/ingest/build_n3_lesson_inputs.py` already uses (`ORDER BY sense_order LIMIT 1`).

It is *consequential* on **8,001 of 16,811 linked tokens (47.6 %)**, where the vocab record has more than
one sense; the other 8,810 (52.4 %) are single-sense and the choice is vacuous.

### How good are the derived glosses? (leave-one-out on the bank's own 23,144 authored glosses)

Running the same rule over the bank, with each token excluded from its own evidence:

| | n | share |
|---|---|---|
| rule fires | 21,362 | 92.3 % |
| …exactly the text the author wrote | 9,285 | 43.5 % of fires |
| …overlapping (one is a substring of the other) | 4,124 | 19.3 % |
| …different text | 7,953 | 37.2 % |

Reading the mismatches: most are **stylistic variants of the same meaning** — `ください` glossed
"(faça) por favor" vs "por favor (faça)", `外出` "saída / ato de sair de casa" vs "sair (de casa)". A
minority are **genuinely the wrong sense**, and they concentrate on polysemous surfaces: `前`
"frente" vs "antes (de)", `かぎ` "chave" vs "gancho (de pendurar)", `かけ` "trancar" vs "estar prestes a".

The same picture from the other side: across the bank's 20,482 linked-and-glossed content tokens, the
author's gloss is **exactly the sense[0] join in 23.2 %**, one of the sense[0] glosses in a further
14.1 %, a substring overlap in 40.7 %, and shares nothing with the registry in **18.5 %**.

**Conclusion: the derivation should be produced everywhere and accepted selectively.** The residue file
therefore carries a per-token `confidence`:

| | n | % of content tokens |
|---|---|---|
| `unique-accept` — one gloss in the bank / one sense in the registry | 4,498 | 26.4 % |
| `ambiguous-verify` — more than one; a reviewer must pick | 12,405 | 72.7 % |
| `author` — no derivation at all | 154 | 0.9 % |

The verify set is **not** 12,405 decisions: it spans 1,563 distinct `(lemma, pos)` pairs, and the top 50
lemmas (`する` 859, `彼` 728, `いる` 481, `私` 408, `その` 297, `ある` 284, `この` 256 …) cover 45.9 % of it.
It is a per-lemma convention ruling — "which gloss does `いる` take as an auxiliary" — applied by script.

## 3. Particles — the explanation is not templated anywhere in the bank

10,257 particles. **10,246 (99.89 %)** use a `(particle, function_type)` pair the bank has already seen;
60 pairs are covered, and only **11 particles across 8 pairs** are new:

`もの`/sentence-final (2) · `や`/sentence-final (2) · `っきり`/adverbial (2) · `ねえ`/sentence-final (1) ·
`しも`/adverbial (1) · `ったら`/adverbial (1) · `すら`/adverbial (1) · `かしら`/adverbial (1)

But **"the pair exists" is not "the text is reusable."** The bank holds 14,184 particle explanations and
they are sentence-specific prose:

- the modal text per `(particle, function_type)` reproduces only **142 of 14,184 = 1.0 %**;
- **9,610 (67.8 %)** literally quote a Japanese token from their own sentence
  ("`の` liga `この部屋` a `本` e diz de que lugar são os livros");
- **1,640 (11.6 %)** mention no Japanese beyond the particle itself, and of those only
  **474 (3.3 %)** also contain no quoted phrase or digit — yet reading the largest of those shows most
  still name the sentence's own referent in Portuguese ("indica de onde a gaiola fica suspensa: a partir
  do beiral", "marca o conjunto dentro do qual se faz a comparação: dentro da turma").

Genuinely context-free texts exist for a handful of pairs only — `か`/sentence-final
("`か` no fim marca a frase como pergunta."), `て`/conjunctive ("`て` liga o verbo ao elemento seguinte…"),
`ね`/sentence-final, `わ`/sentence-final. **There is no template layer to inherit.**

So: **`explanation_pt` is 0 % derivable at bank quality; 10,257 units of work.** What *is* derivable:

- **`function_pt`** — the short label ("partícula de tópico", "marcador de objeto direto") — from the
  bank's modal label per pair: **10,246 / 10,257 = 99.89 %**. Optional to the validator, but present on
  14,182 of 14,184 bank particles, so parity wants it.
- **a role for the chunk the particle closes** — `scripts/export/build_sentence_patterns.py::role_of()`
  already exists and returns a role for **8,466 of 10,257 (82.5 %)**; the 1,791 without one are almost
  entirely sentence-final and conjunctive particles, which are exactly the ones whose bank texts *are*
  reusable.

**Recommendation (a decision for the owner, not made here):** a *parameterised* template —
`"{particle} marca {left-chunk} como {role} de {right-chunk}"`, filled from the dissection — reproduces
the bank's actual habit (naming the neighbours) mechanically for the 8,466 role-bearing particles, and
the ~10 context-free bank texts cover most of the rest. That converts 10,257 authored paragraphs into a
template pass plus a verification sample. A flat per-`function_type` template would pass `validate.py`
and would be a measurable quality regression against every one of the 5,889 sentences already banked.

## 4. Structure paragraphs — 4,223, no template available

**`clause_structure` does not exist for these sentences.** It is Layer C — judged from the Japanese by an
AI classification pass and carried on the sentence row (`merge_sentence_structure.py`), populated for
5,825 of the 5,889 already-banked sentences. Un-ingested sentences have none, so the literal question
("how many distinct values do the 4,223 have") has no stored answer. Two substitutes were measured.

**(a) A mechanical predictor, scored against the bank's 5,825 labels.** Surface rules (sentence-final か
→ question, 命令形/ください → imperative, と言/と思 → quote, たら/なら/れば → conditional, から/ので/ため →
cause, とき/あと/前 → subordinate-time, any 接続助詞 → coordinate, any 係助詞 は → topic-comment, no
predicate → fragment, else simple) score **70.6 % overall**: question 94.1 %, cause 87.2 %,
topic-comment 73.9 %, imperative 73.1 %, coordinate 67.5 %, simple 67.5 %, quote 54.8 %, fragment 53.3 %,
conditional 46.9 %, subordinate-time 32.1 %, **relative-clause 0 %**. Useful as a batching key,
not as data.

Predicted over the 4,223 — **10 distinct values**, top 10 by frequency (that is all of them):

| clause_structure | n |
|---|---|
| topic-comment | 1,701 |
| simple | 763 |
| coordinate | 714 |
| question | 415 |
| imperative | 254 |
| cause | 147 |
| subordinate-time | 90 |
| conditional | 71 |
| quote | 39 |
| fragment | 29 |

(`relative-clause` is never predicted; it is 87 of 5,825 in the bank.)

**(b) Can same-clause_structure precedent serve as a template? No.** The bank's **5,889
`structure_explanation` texts are 5,889 distinct strings** — zero reuse, at any level. Inside each class
the distinct count equals the row count exactly: simple 2,009/2,009, topic-comment 1,847/1,847,
question 665/665, imperative 417/417, coordinate 209/209, conditional 196/196, quote 168/168,
relative-clause 87/87, cause 86/86, subordinate-time 81/81, fragment 60/60. Only **3 of 5,889** contain
no Japanese at all. Median length 308 characters, p90 393, max 647.

**4,223 paragraphs, authored, no shortcut.** The clause prediction is still worth carrying: it batches
sentences of one shape together so an authoring pass writes 1,701 topic-comment paragraphs in a row
with one instruction, instead of context-switching every sentence.

## 5. The exact field shape the derivation must emit

One file per batch at `research/derived/mined_layerb/batch-NN.json`:

```json
{
  "batch": 1,
  "sentences": [
    {
      "tatoeba_id": 74415,
      "tokens": [
        {"position": 0, "gloss_pt": "este; deste", "role_pt": "determinante (modifica 部屋)"},
        {"position": 10, "gloss_pt": "…", "role_pt": "…", "conjugation_note_pt": "連用形 de ある"}
      ],
      "particles": [
        {"position": 2, "function_pt": "marca de posse/pertencimento",
         "explanation_pt": "の liga この部屋 a 本 e diz de que lugar são os livros: …"}
      ],
      "structure_explanation_pt": "A frase segue o molde 'A não é B'. …"
    }
  ]
}
```

Binding facts, from `persist()` and `validate.py`:

- **`position` is the C-token position from `dissect.Dissector.skeleton()`** and nothing else.
  `persist()` re-runs the Dissector itself and keys Layer-B by position
  (`{t["position"]: t for t in lb["tokens"]}`), so a position that does not exist is silently dropped —
  it does not error. Emit positions straight from the same skeleton.
- **Tokens and particles share one position space.** A particle at position 2 is *also* token 2; the
  authored batches give it a `role_pt` in `tokens` and its `function_pt`/`explanation_pt` in `particles`.
- **`gloss_pt` is required on every token whose `pos_coarse` is in
  `{名詞, 動詞, 形容詞, 形状詞, 副詞, 代名詞, 連体詞, 接続詞, 感動詞}`** — 17,057 of the 36,282 tokens here.
  A missing one is a hard `validate.py` error, not a warning. `role_pt` and `conjugation_note_pt` are
  optional (the bank has role on 23,113 of 23,144 content tokens, conjugation_note on 9,077).
- **`explanation_pt` is required on every particle** (10,257). `function_pt` is optional.
- **`structure_explanation_pt` is required on every sentence**, alongside `pt` and `pt_literal`, which
  W13 already produced.
- Storage is `localized_text`, not the legacy columns: token `gloss`/`role`/`conjugation_note` at layer
  **B**, particle `function` at **B** and `explanation` at **C**, sentence `translation`/
  `translation_literal` at **B** and `structure_explanation` at **C**, all `locale = 'pt-BR'`.
- Empty string and `None` are both dropped by `set_text()` — an empty gloss is the same as no gloss and
  will fail the validator.

## 6. Dissector failures

**None.** 0 of 4,223 raised; I1 and I2 hold on all 4,223.

## 7. Blockers found while measuring (for the W13 apply, not for W13b authoring)

1. **The 26 generated rows have `tatoeba_id: ""`.** `ingest_mined_stages.py` indexes Layer-B as
   `layerb[s2["tatoeba_id"]]`, so all 26 would collapse onto the single key `""`, and the slug it builds
   (`f"sent:tatoeba-{tid}"`) would be `sent:tatoeba-` for all of them. They would in any case be dropped
   by the jp-vs-raw guard, since `raw.get("")` is `None`. They need their own slug scheme — the bank
   already uses `gen-<hash>` — and their own Layer-B key.
2. **`ingest_mined_stages.py` reads `research/derived/mined_pt/_accepted.json`**, not
   `research/derived/n3_mined/accepted.json`, and hardcodes `tags: ["mined", "stage:…"]`. The W13 row
   already flags the `--tag` change; the source path has to move with it.
3. The 4,197 real rows are otherwise clean for ingest today (jp byte-identical to Layer A, no collisions).

## 8. Twenty derived glosses, for a human read

| token | lemma / POS | source | derived gloss |
|---|---|---|---|
| この | この · adnominal | bank | este |
| カナダ | カナダ · noun | bank | Canadá |
| 喧嘩 | 喧嘩 · noun | registry-sense0 | briga; discussão |
| コンピューター | コンピューター · noun | bank | computador |
| 人類 | 人類 · noun | registry-sense0 | humanidade; gênero humano |
| 毎月 | 毎月 · noun | bank | todo mês |
| 月曜日 | 月曜日 · noun | bank | segunda-feira |
| 有名 | 有名 · na-adjective | bank | famoso |
| 記録 | 記録 · noun | registry-sense0 | registro; anotação; ata |
| 伸ばし | 伸ばす · verb | bank | estender, esticar |
| その | その · adnominal | bank | aquele |
| 成功 | 成功 · noun | registry-sense0 | sucesso; êxito |
| 授業 | 授業 · noun | bank | aula |
| 事務 | 事務 · noun | registry-sense0 | trabalho de escritório; trabalho administrativo; expediente |
| 高い | 高い · i-adjective | bank | caro |
| 毎日 | 毎日 · noun | bank | todo dia |
| どれ | どれ · pronoun | bank | qual (entre vários) |
| 単語 | 単語 · noun | registry-sense0 | palavra; vocábulo |
| つなが | つなぐ · verb | bank | ser amarrado/preso (raiz) |
| 日本人 | 日本人 · noun | bank | japonês (pessoa) |

`つなが → "ser amarrado/preso (raiz)"` is the shape of the risk: the bank's modal gloss for that surface
came from a passive context and is carried into a new one unchecked. It is flagged `ambiguous-verify`.

## 9. Residue work list

| item | size | note |
|---|---|---|
| token glosses to author | **154** | 115 words over 137 `(lemma, pos)` pairs + 39 numerals a rule finishes |
| vocab-linker fixes (mechanical) | **26** | kana-normalised index in `Dissector._vocab_by_form` |
| vocab records to add (Layer A) | **134** | in JMdict, absent from our registry; they self-link afterwards |
| derived glosses to verify | **12,405** over 1,563 `(lemma, pos)` | a per-lemma ruling, not per-token; top 50 lemmas = 45.9 % |
| derived glosses to accept as-is | **4,498** | unambiguous key |
| particle `function_pt` | 10,246 derived / 11 to author | mechanical |
| particle `explanation_pt` to author | **10,257** | no template exists; see §3 for the parameterised option |
| structure paragraphs to author | **4,223** | no template exists; batch by predicted clause_structure |

## 10. Machine output

`research/derived/n3_mined/layerb_residue.json` — 4,223 sentences, each with:

- `tokens[]`: `position`, `surface`, `lemma`, `pos`, `pos_coarse`, `vocab_id`, `vocab_slug`,
  `gloss_pt` (derived or `null`), `gloss_source` (`bank` | `registry-sense0` | `null`),
  `role_pt_hint` (the bank's modal role for the same surface, where one exists),
  `author` (true = residue), `confidence` (`unique-accept` | `ambiguous-verify` | `null`);
- `particles[]`: `position`, `particle`, `function_type`, `function_pt` (derived),
  `explanation_pt` (always `null`), `explanation_precedent_n`, `explanation_distinct_in_bank`,
  `author` (always true);
- `structure_author: true`, plus `lesson`, `targets`, `generated` and a per-sentence `counts` block.

4,073 of 4,223 sentences need **no** authored token at all; 150 need at least one.
