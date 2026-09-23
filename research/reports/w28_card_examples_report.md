# W28: an example sentence and a cloze span on SRS cards (C6-W28, 2026-09-23)

Mechanical unit. Derived 2,242 rows, authored 0. Not a checkpoint: gate plus quick replay.

## 1. What changed

| layer | change |
|---|---|
| design | `design/srs_design.md` §9: the slot, the selection rule, the span rules, why it is optional |
| contract | `lesson.srs.introduces_cards[].example` = `{sentence: "sent:...", cloze: {start, end, answer}}`, registered in `scripts/contracts/build_schemas.py`; `contracts/types.ts` gains the optional field; `contracts/user_state/card.schema.json` content_note points at it |
| derivation | `scripts/derive_card_examples.py` (reads the exported tree) -> `research/derived/repairs/card_examples.json` (2,242 rows + `no_example[]` 1,894 with a reason each) |
| index | migration `018_card_example.sql`; `scripts/apply_card_examples.py` (idempotent, second run 0 writes); rebuild manifest step 135, families renumbered 136-138 |
| export | `export_course._card_examples` joins `card_example` onto the card |
| gates | `validate_card_content.py` check F plus a no-example ratchet; `validate_repairs_applied.py` handler `card_examples.json` (exact match) |

Field names are neutral English; the slot carries no learner-facing text of its own (the sentence's
pt-BR translation lives on the sentence), so no i18n scope row.

## 2. The rule

At the card's own lesson L (the lesson that issues the card), a sentence qualifies when L renders it,
or when it passes the display test `validate_lesson_gating` check D applies to every sentence a lesson
shows (`derive_lesson_sentences.fit`, imported): model-text register, pt-BR translation, graded at or
below L's level, at most BUDGET[level] kanji + words outside L's `cumulative_known_set` (pre-N5 0,
N5 1, N4 2, N3 2), no unlinked content token. Ranked: rendered by L, i+0 (`sentence_ok`) before i+1,
fewer unknowns, real over generated, shorter, stable hash. The first ranked sentence with an
alignable span wins.

Why i+1 and not W14's i+0: W14 added body links, and check D ratchets the count of body links that
carry a new item. A card is not a body link. The strict i+0 version was measured first and reached
784 of 2,951 vocab cards.

Span: vocab = the card's own token (reading and sense fit), extended over its inflection
(`whole_form_end`); grammar = a probe segment of the point's forms aligned to token starts and ends
(`build_grammar_cloze`'s alignment); kanji = the whole word carrying the character. At least 2
Japanese letters stay outside the blank.

## 3. Numbers

| namespace | with example | cards |
|---|---|---|
| vocab | 1,256 | 2,951 |
| grammar | 404 | 494 |
| kanji | 582 | 634 |
| kana | 0 (by design: a family card is five glyphs) | 57 |
| **total** | **2,242** | **4,136** |

By level: N5 vocab 163 / 688, grammar 99 / 150, kanji 76 / 103; N4 vocab 230 / 643, grammar 180 / 212,
kanji 174 / 187; N3 vocab 863 / 1,596, grammar 125 / 132, kanji 332 / 344; pre-N5 vocab 0 / 24.

Source of the chosen sentence: rendered by the lesson 1,194; i+0 in the known set 465; i+1 in budget
583. AI-generated sentences 327 (real ones rank first).

No example (1,894): none passes the display rule 1,603; no alignable span 162; no bank sentence
carries the item 72; kana family 57.

## 4. The finding: 2,901 was not the number under the rule

W13's "2,901 / 2,951 cards CAN show an example" counted a vocab card as covered when the word is a
token in ANY bank sentence. Under the renderer's rule at the introducing lesson it is 1,256. The
binding constraint is the level test, not the known set: the bank grades 3,405 of its 10,209
sentences N2/N1 and only 473 N5. Measured: keeping the i+1 known-set budget and dropping only the
level test, 2,395 vocab cards would have a candidate (over budget 450, no token 72, register 34).

That is an owner decision, not a selector's: **B-W28**. Either (a) let a card example ignore the
sentence's graded level when the sentence is inside the known-set budget (the level grade also
reflects grammar, which the budget does not count, so this admits sentences with grammar the
learner has not met), or (b) grow the bank at N5/N4 (the W13 mining route), which fixes lessons and
exams too. The ratchet in check F holds today's counts and only moves down.

## 5. Cards before and after

`les:n3-estrutura-06` / `vocab:1502480` (`course/n3/topic-51-estrutura/lesson-06.json`)
- before: `{"deck": "deck:vocab-n3", "item": "vocab:1502480", "card_types": ["recognition", "production"]}` (+ production_key)
- after: `... "example": {"sentence": "sent:tatoeba-116193", "cloze": {"start": 2, "end": 4, "answer": "物語"}}`
- renders: 彼の＿＿はおもしろかった。 / A história dele era interessante.

`les:n4-condicionais-01` / `kanji:着` (`course/n4/topic-23-condicionais/lesson-01.json`)
- before: `{"deck": "deck:kanji-n4", "item": "kanji:着", "card_types": ["recognition", "production", "handwriting"]}`
- after: `... "example": {"sentence": "sent:gen-4f79637ba175", "cloze": {"start": 2, "end": 6, "answer": "着いたら"}}`
- renders: 駅に＿＿メールして / Quando chegar na estação, me manda uma mensagem.

`les:n4-suposicao-03` / `gram:mitai-na` (`course/n4/topic-31-suposicao/lesson-03.json`)
- before: `{"deck": "deck:grammar-n4", "item": "gram:mitai-na", "card_types": ["recognition", "cloze", "production"]}`
- after: `... "example": {"sentence": "sent:gen-7ec782cb2980", "cloze": {"start": 1, "end": 5, "answer": "みたいな"}}`
- renders: 夢＿＿話だね / Parece história de sonho, né?

## 6. Lessons do not degrade

Rendered diff of `course/` against HEAD: 269 lesson JSON files changed, 0 `.md` files (and
`validate_md_views` 322 / 322 byte-identical). Stripping `srs.introduces_cards[].example` from every
changed file leaves it byte-for-byte equal to HEAD (2,242 examples stripped, 0 files differing beyond
the field). No body, unlock, exercise or production key moved.

## 7. Gate

`validate_all.py`: ALL HARD VALIDATORS PASS, including the quick replay, `validate_card_content`
(`[OK] 4136 card(s) ... 2242 example(s) checked`) and `validate_repairs_applied` (the new table
replayed exact). Plant proof of check F on copied fixtures (validator copied into each), control
exit 0 and 9 / 9 plants caught: missing example (ratchet), ghost sentence, drifted answer, span
cutting a token, span on another token, kanji span without the character, grammar span that is no
form of an untagged sentence, above-level sentence the lesson does not render, kana card with an
example. Verbatim lines in the validator docstring. Full replay not run (not a checkpoint unit);
step 135 skips-and-reports off the live index exactly as step 119 does.

## 8. Open

- B-W28 (above).
- Per-card tags and the leech hook from the W28 row: not done here.
- 162 cards have admissible sentences but no alignable span (mostly reading or sense guards on the
  vocab token, which refuse homographs on purpose).
- Renderer: the prototype review route still picks its own sentence; switching it to
  `card.example` is app work.
