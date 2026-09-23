# Exam builder fixes 2: token-bounded gf blanks, context-sufficient distractors

Status: **APPLIED 2026-09-23 by P1-exam-fixes** (`research/reports/p1_exam_fixes_report.md`). Patch `research/derived/patches/exam_builder_fixes_2.patch`
applies on top of `research/derived/patches/exam_equivalence_filter.patch` (patch 1) and touches one
file, `scripts/export/build_exam_banks.py`. Measured 2026-09-23 in a scratch tree (`git archive HEAD`)
over an sqlite backup of `db/corpus.sqlite`. Findings being closed:
`research/derived/pending/exam_equivalent_distractors.json`.

Applying: `git apply` patch 1, then patch 2, then rebuild the banks in W18 order (authored, listening,
reading_comp, `build_exam_banks.py` last) and re-run the bank gates. The apply chain was checked on a
fresh `git archive HEAD scripts design`: both patches apply cleanly, the result is byte-identical to the
measured builder, it compiles, and `exam_rules.py`'s self-check passes.

## What the patch does

| Fix | Rule | Where |
|---|---|---|
| 18a | `grammar_form` blanks only at SudachiPy mode-C token boundaries, reusing W16's `token_spans` + `boundary_occurrence` (as `text_grammar` already did). The first form of the point that occurs once *and* is token-aligned is keyed. If none is, the builder records drop `blank-cuts-a-word` and the sentence tries its next grammar point. | gf |
| 18b | A distractor is admissible only if it does **not** (a) turn the stem into a bank sentence (`stem_key` of the filled stem is not a bank sentence) and (b) appear in the corpus in the same slot: token-aligned, after a word with the same POS and conjugation form as the word before the blank (`slot_shape`). A rejected distractor is replaced from the level pool in the existing order. If fewer than 3 remain, the item is dropped (`no-admissible-distractor`). | gf, tg |
| 18c | `x not in pre + post`: validate_exam_banks check C. Without it, the slot rule picked がいます for 「…が（　）います。」 (tg:n5:n5-convites-04-01), since the blank splits the distractor and `x not in jp` misses it. | gf, tg |
| 19 | A `grammar_form` stem needs `MIN_STEM_CONTENT = 2` content tokens outside the blank (not 助詞 / 助動詞 / punctuation / whitespace), else drop `stem-too-short`. | gf |

`slot_shape` classes. SudachiPy tags a conjugated word by what follows it, but the learner reads the
string, so a string that can be several forms counts as all of them: 終止形 = 連体形 (言う before べき or
ように); 未然形 = 連用形 for ichidan, カ変, サ変 and the レル/ラレル/セル/サセル auxiliaries (入れ before
られる or ていた; し before なければ or たら); all 連用形 variants are one class (帰り, 帰っ); 動詞 = 助動詞.
Punctuation or the text edge is `|`. Every merge makes the rule refuse more distractors, never fewer.
The slot is the left side only. A variant that also matched "sentence ends here / continues" missed
gf:n5:4206 (ネコ + だけど) and gf:n4:3522 (出 + ちゃう), because those forms were only attested with the
other right edge.

## Measuring N (`MIN_STEM_CONTENT`)

The paper draws 9 / 8 / 13 `grammar_form` items (N5 / N4 / N3), so the 3x floor is 27 / 24 / 39.

| N | n5 gf | n4 gf | n3 gf | 51 high: replaced / dropped / unresolved | what the survivors look like |
|---|---|---|---|---|---|
| 0 | 114 (12.7x) | 300 | 300 | 51 / 0 / 0 | 7 stems have no content at all and still take the new distractors: 「（　）？」 with なあ or まで, 「（　）！」 with 終わる |
| 1 | 109 (12.1x) | 300 | 300 | 48 / 3 / 0 | 94 one-content stems. Roughly 1 in 10 still admits a colloquial fit: 「キツイ（　）。」 with これ (inversion), 「りんご（　）ですか？」 with たくさん (particle drop), 「ネコ（　）。」 with あそこ. Three of these are among the 51 (gf:n5:60, 4206, 4294). |
| **2** | **75 (8.3x)** | **300 (37.5x)** | **300 (23.1x)** | **34 / 17 / 0** | I read all 246 two-content stems. 2 real fits are left (gf:n3:5179 次の（とおり） with はずだ, gf:n3:5426 友達でもない（くせに） with わけだ; see Limits 1) and 3 marginal ones (たくさん by particle drop twice, びびって上げない). None of them is among the 51. |
| 3 | 32 (3.6x) | 300 | 273 | 20 / 31 / 0 | n5 falls to just above the floor, and n3 no longer fills its cap |

The mechanical count reaches 0 unresolved at N=0, but that only means the flagged distractor is gone:
with no context, the replacements fit too. N=2 is the smallest N at which none of the 51 is left with a
replacement that fits, and every family and level stays at least 3x its paper. N is not applied to
`text_grammar`, whose stems are whole passages.

## Scratch run

- **Parity.** The unpatched HEAD builder over the snapshot reproduces all 18 HEAD auto-built banks item
  for item. Patch 1 alone changes exactly the 16 flagged items, as its report says.
- **Per bank, HEAD → patch 1 + patch 2.** The other 12 deterministic banks are identical, apart from
  patch 1's 2 items (n4_context_fill 1, n3_orthography 1).

| bank | before → after | changed | dropped | added | unchanged | patch 1 → 2, by cause |
|---|---|---|---|---|---|---|
| n5_grammar_form | 114 → 75 | 50 | 39 | 0 | 25 | 49 distractors replaced, 1 re-keyed (first point's stem too short), 39 dropped as too short |
| n4_grammar_form | 300 → 300 | 167 | 53 | 53 | 80 | 164 replaced, 2 re-keyed (old blank cut a word), 22 dropped for a cut blank, 31 dropped as too short, 53 backfilled to the cap |
| n3_grammar_form | 300 → 300 | 175 | 48 | 48 | 77 | 175 replaced, 25 dropped for a cut blank, 23 dropped as too short, 48 backfilled |
| n5_text_grammar | 34 → 34 | 28 | 0 | 0 | 6 | 28 replaced |
| n4_text_grammar | 74 → 74 | 53 | 0 | 0 | 21 | 53 replaced |
| n3_text_grammar | 122 → 122 | 78 | 0 | 0 | 44 | 78 replaced |

"Changed" counts HEAD → both patches; "by cause" is patch 1 → patch 2. Patch 2 changes or drops again
every one of patch 1's 14 grammar_form items except gf:n4:3535, which is why n4 shows 167 changed here
but 164 + 2 = 166 in the cause column.

- **Every patch-2 change is explained (0 unexplained).** The eval script
  (`scratchpad/distr2/eval.py`, not committed) re-derives each difference from the rules:
  - A replaced distractor fails 18b (all 856 removed distractors across 547 items fail it by slot).
  - A dropped item has a blank that cuts a word, or a stem under 2 content tokens.
  - A re-keyed item had one of those two defects on its old key.
  - An added item is backfill into a capped bank, with no more added than dropped.
- **The 16** (patch 1): 13 still replaced, 3 now dropped as too short (gf:n4:3845 待た（　）。, gf:n5:63
  行き（　）。, gf:n5:4328 （　）くらい？). None regress.
- **The 51 high-confidence:** 34 replaced, 17 dropped, **0 unresolved**. The 27 low-confidence: 22 / 5 / 0.
  The case patch 1 itself created, gf:n4:3853 (たらどうですか after 大切にし), is fixed.
- **The 10 cut blanks:** all 10 dropped; no other form of their points is token-aligned. The 39
  "starts mid-token" items listed beside them fall under the same W16 rule: 37 dropped, and 2 re-keyed
  to the whole form (gf:n4:3414 考えさ（せる） → 考え（させる）, gf:n4:3444 借りら（れる） → 借り（られる）).
- **Whole-bank checks on the output:** 0 gf/tg blanks off a token boundary, 0 distractors that 18b
  would refuse, 0 gf stems under N.
- **Gates** (scratch tree = HEAD `corpus/` and `course/` + the new banks):
  - `validate_exam_level_gate.py`: ALL OK. All 18 deterministic family-levels have 0 inappropriate
    items at ceiling 0; the lowest is n5_grammar_form at 8.3x.
  - `validate_exam_banks.py`: ALL OK, advisory counts unchanged.
  - `validate_exam_stem_collisions.py`: 0.
- **Rule hits:** the slot rule removed 856 distractors. The bank-sentence rule removed none that the
  slot rule had not already removed: a bank sentence with x in the slot is itself an attestation. It is
  kept because it is one set lookup and states the rule directly. On `context_fill`, the same
  bank-sentence check finds 0 hits over all 955 items, so it was not extended there.

## Twelve items, before (HEAD + patch 1) and after

| id | stem = key | before | after | why |
|---|---|---|---|---|
| gf:n4:3509 | もう帰っ（　）。 = たらどうですか | たらいいですか / と言ってもいい / させてください | と言ってもいい / でございます / かもしれない | たらいいですか, させてください attested after a 連用形 verb |
| gf:n4:3852 | 少し買い物をし（　）。 = なければならない | たらどうですか / たらいいですか / と言ってもいい | と言ってもいい / とされている / でございます | サ変 し is both 未然形 and 連用形 |
| gf:n4:3853 | 時間を大切にし（　）。 = なければならない | させてください / と言ってもいい / たらどうですか | と言ってもいい / ことができる / かもしれない | the residual patch 1 created |
| gf:n5:4595 | 外に出（　）か？ = てもいいです | たほうがいい / けっこうです / なくてもいい | けっこうです / じゃなかった / があります | ichidan 出: 出たほうがいい and 出なくてもいい both fit |
| gf:n3:5213 | ５時に駅で会う（　）。 = ことになっている | わけにはいかない / ようにしましょう / ないことはない | ないことはない / めったにない / ようとしない | 終止形 = 連体形 |
| gf:n3:4963 | （　）雨が降り出している。 = その上 | はずだ / という / なんか | はずだ / べきだ / とおり | なんか attested sentence-initially |
| gf:n4:3567 | 手に入れ（　）と思いますよ。 = られる | かかる / くする / ていた | かかる / くする / あんな | 入れ is 未然形 and 連用形 |
| tg:n5:n5-perguntas-04-01 | …（　）かたはおじです。… = あの | たり / もう / その | たり / とき / だけ | その attested sentence-initially |
| gf:n4:3444 | 二週間ほど借りら（　）かい。 = れる | がり / など / また | 借り（　）かい。 = られる: おきに / のはだ / きっと | old blank started inside 借りられる; re-keyed to the whole form |
| gf:n3:5100 | あなたの（　）す。 = おかげで | たところ / うとした / について | dropped | the blank cut おかげです; no other token-aligned form |
| gf:n5:4292 | （　）？ = なぜ | する / もう / まだ | dropped | 0 content tokens: nothing can rule a distractor out |
| gf:n5:60 | キツイ（　）。 = なあ | です / あれ / ので | dropped | 1 content token; at N=1 it would have become あれ / これ / もう, and キツイ、これ。 is a natural inversion |

## Limits, and what the teacher loop still sees

1. **Forms attested only in another conjugation are missed.** Attestation is by literal string, so
   終わる after a 連用形 is never seen when the corpus only has 読み終わった. I probed a lemma-matching
   variant on the output. It flags 90 of the 905 gf/tg items. Reading them, about 6 are real fits:
   - 答え（にくい）な with 終わる
   - 目を開け（なさい） with 終わる
   - リストは次の（とおり） with はずだ
   - あなたが正しい（ということだ） with わけではない
   - （後で）電話します with なら
   - 一人で行く（しかない） with みたいな

   The rest is homograph noise (たて, 上げる, いらっしゃる via でいらっしゃる). A second miss comes from
   tagging: in でもない, ない is tagged 形容詞, which stays outside the 動詞 = 助動詞 class, so わけだ
   survives on gf:n3:5426. With that one the residual is about 7 items, under 1% of gf/tg. I left them
   for review rather than buy them with 80 wrong refusals. Upgrade path: lemma-match only the form's
   last token, with a homograph guard, and fold 形容詞 into the same class at 終止形/連体形.
2. **Distractors now tend to be wrong by form.** What survives 18b does not attach to the word before
   the blank, so more items can be solved by grammar shape alone than by meaning. That is the
   admissibility rule as specified: mechanically, only "ungrammatical" can be certified. Distractor
   concentration rose a little. n3_grammar_form's top distractor went from 最中に ×20 to ようとしない
   ×33 of 300; n5_text_grammar's top share went from 18% to 26%.
3. **Coarse classes over-refuse.** 動詞 = 助動詞 lets でいらっしゃる attest いらっしゃる after any 連用形.
   This costs pool, never correctness. No item was dropped as `no-admissible-distractor`.
4. **The snapshot was taken while a writer chain was changing the DB.** Parity with HEAD held on this
   snapshot. After applying, rebuild on the live DB and re-run the three gates. `MIN_STEM_CONTENT` should
   be re-measured only if n5_grammar_form drops below 27.
