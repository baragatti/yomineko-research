# W21b: forward references, derivation

Status: **derived, 2026-09-23.** This is a derivation only. Nothing in `course/`, `corpus/`, `contracts/`,
`db/` or `research/derived/lessons/` was written, no exporter or apply ran, and git state is unchanged.
Table (pending): `research/derived/pending/w21b_forward_refs.json` (670 rows, 219 moves, simulation block).

## 0. Which tree

The fixture was extracted from **git HEAD `c6071386`** with `git archive` (course/, corpus registries,
bank.json, the validators and derive scripts), not from the working tree. A concurrent agent was
mid-export while this ran: `bank.json` had 97 uncommitted new sentences (10,112 → 10,209) and one read
of it failed mid-write. The lesson JSONs in the working tree matched HEAD byte for byte (only INDEX
date lines differed), so the ledger itself is unaffected. The script is deterministic, so a re-run
after that export commits reproduces this table on the new tree. The DB was read only through
`sqlite3.backup` into the scratch dir.

## 1. The ledger, re-measured

A forward use is (lesson L, item I) where L references I through any of `derive_needs.py`'s five
channels (body chip, body sentence, lesson `sentence_refs`, exercise `sentence_refs`, body-reading
`uses`), and the lesson that unlocks I comes LATER in course order. Rows are one per (L, I), and each
row carries up to 3 spans (channel + sentence/reading pointer + jp).

| | W21 (2026-09-09) | today (HEAD) |
|---|---:|---:|
| lesson→lesson forward edges | 607 | **619** |
| … same topic / same level / across levels | 28 / 431 / 148 | 28 / 431 / **160** |
| (lesson, item) forward uses | (plan row: "601") | **656** |
| … kanji / vocab / grammar | 360 / 251 / 27 | 360 / 269 / 27 |
| … same topic / same level / across levels | — | 35 / 461 / 160 |

The plan row's "601 (kanji 360, vocab 251, grammar 27)" is internally inconsistent (those three sum to
638). 656 is today's (L, I) count. The 12 extra cross-level edges come from sentences that landed after
W21 (W13/W14-era selections).

## 2. The decision rule

Rows are grouped by item. For item I, taught at M, with users U before M:

- **(c) HOLD** — the user is at a different (earlier) level than M. All 160 cross-level rows fall here,
  and in **every one** the item's own registry level is above the using lesson's level. So this is the
  real i+1 backlog (check D territory, W14 re-selection), not a mis-placed N5 word.
- **(a) MOVE** — the target T is the **first same-level user**. The unlock moves M → T, the SRS card moves
  with it, and so does any exercise of M whose only M-target is I (so no exercise of M loses its
  target). M keeps its explanation. "Target" uses exactly `validate_practice_coverage.py`'s definition
  (answer surfaces, prompt markup, cited-sentence dissection), imported from the gate itself. The move
  is feasible only if all of these hold on the working state:
  - **R1**: T is not a review lesson (W22 review shape: zero item unlocks).
  - **R2**: I is not M's only item unlock.
  - **R3**: if M practises I, then T already practises it or an exercise travels. Otherwise M's shared
    exercise would strip other items, or I would go unpractised and the practice ratchet would grow.
  - **R4**: a travelling exercise asks about nothing T does not know yet, unless T already uses that item.
    This means a move never creates a new forward pair.
  - **R5**: M keeps a rendered retrieval + production pair.
  - **R6**: T renders a retrieval + production pair once it teaches.
- **Fallback (A-move-partial)**: if the first user fails, try the next same-level user. Homes only
  move earlier, and passes repeat until nothing changes (3 passes, 3 multi-hop items, 7 partial moves).
- **(b) REWRITE**: a same-level use left before the final home. The row names the rule that blocked it
  and the span that must be re-authored or re-selected.

## 3. Counts per decision

| source | move | rewrite | hold | rows |
|---|---:|---:|---:|---:|
| ledger, same topic | 20 | 15 | — | 35 |
| ledger, same level | 354 | 107 | — | 461 |
| ledger, across levels | — | — | 160 | 160 |
| W15 holds | 3 | — | 1 | 4 |
| W22 base forms + ました | 9 | 1 | — | 10 |
| **total** | **386** | **123** | **161** | **670** |

By rule: A-move 374, A-move-partial 12, B-rewrite/R4 102, B-rewrite/R3 20, B-rewrite/no-earlier-use 1,
C-hold 161. By kind (ledger): vocab 221 / 21 / 27, kanji 145 / 88 / 127, grammar 8 / 13 / 6
(move / rewrite / hold).

Moves: **219 items**, all 219 with their SRS card. 66 of them carry exercises, 80 exercises in total.
209 of the 219 cross a topic boundary.

**R4 is the binding constraint:** 102 rows, 88 of them kanji. A kanji counts as practised when any
answer contains the character, so the exercise that must travel with a kanji is usually a sentence
exercise about vocabulary the earlier lesson lacks. One lever is an owner call, not taken here: let such
an exercise stay behind as review, relaxing "no exercise loses its target" to "practice never regresses".
That would lift most R4 rows.

## 4. W15 and W22 rows

| row | decision |
|---|---|
| W15 間 `vocab:1215230` @ n4-oracoes-relativas-03 | **move** (+45 lessons gain it); the held passage becomes applicable |
| W15 関する `vocab:1215790` @ n3-perspectiva-01 | **move** (+24) |
| W15 対する `vocab:1610160` @ n3-limites-05 | **move** (+7) |
| W15 読み `vocab:1456130` @ n4-keigo-04 | **hold**: an N3 item (taught at n3-perspectiva-07) needed at N4. This stays a course call, as W15 said |
| W22 `conj:dictionary/nai/ta/te/attributive/adverbial/potential` | **move** = keep W22's `gate-sound` home on the requiring lesson (no card, no exercise targets a form). `teach-true` mode is therefore not needed |
| W22 `conj:mashita`, `conj:polite-past` | **move** to n5-perguntas-04, the first N5 display (誰がこの本を読みましたか). This takes the unlock out of the review lesson and restores the zero-unlock review shape. **Authoring debt remains**: no lesson explains the verb past |
| W22 `conj:masendeshita` | **rewrite**: no lesson before n5-revisao-02 displays it, so there is no user to move to. A non-review N5 lesson must teach it (owner/W25) |

The conj rows are analytic. No `conj:` unlock is in the tree yet (the W22 apply is queued), and checks
C/D do not read conjugation forms. `cks_delta` on those rows is measured against the teach-true home.

## 5. Simulation (fixture = HEAD copy with the 219 moves replayed hop by hop)

Every lesson's `cumulative_known_set` was recomputed as a running union. `needs[]` was re-derived with
`build_needs_table.build()`, which is what the apply does and what C4 checks. The five gates then ran
on both copies.

| | before | after |
|---|---:|---:|
| cks keys that shrink (322 lessons × 6 kinds) | — | **0** |
| cks memberships gained (vocab / kanji / grammar) | — | 3,478 / 2,615 / 73 |
| DB snapshot, running union of `lesson_unlocks` shrinks | — | **0** (219 rows moved, 0 unmapped) |
| forward uses, **same topic** | 35 | **17** |
| forward uses, **same level** | 461 | **105** |
| forward uses, across levels | 160 | 160 |
| forward edges, same topic / same level / across levels | 28 / 431 / 160 | **16 / 105 / 160** |
| forward uses created by a move | — | **0** |
| move rows still forward after the replay | — | **0** |
| `needs[]` rows (derived + kana + review chain) | 758 | 737 (692 + 40 + 5) |
| prerequisite-less lessons held (C2) | 7 | 4 (drop n5-numeros-tempo-01, -03, n5-perguntas-02) |
| `validate_lesson_gating` A / B / C / D | 0/0/0/0 FAIL | **0/0/0/0 FAIL** (after dropping 1 gating exemption) |
| D: over-budget / with new kanji / with new vocab | 148 / 304 / 227 | **47 / 224 / 51** (above-level 178 unchanged) |
| `validate_unlock_ledger` | ALL OK | ALL OK |
| `validate_practice_coverage` absent | 2,338 | 2,265 (0 FAIL) |
| `validate_exercise_contracts`, `validate_srs_decks` | 0 FAIL | 0 FAIL |

The ratchets **do not reach 0**. Same topic falls 35 → 17 uses (28 → 16 edges) and same level
461 → 105. The residue is exactly the 122 ledger rewrite rows: two same-level rows became same-topic
after a partial move (`tier_after` on the row). The DB's stored cks already differs from its own
unlock union in the `vocab` key for 267 lessons (the documented authoring-ref vs published-slug split,
W22 §4.4), so the DB check compares the unions before and after rather than the stored column.

## 6. What the apply must carry (not done here)

1. Both layers: the unlock plus `lesson_introduces` / `lesson_unlocks` rows, `srs.introduces_cards`,
   the exercise record plus its `<exercise ref>` tag moved into T's body before the `<checklist>`. The
   simulation kept the old `ex:` ids and every gate accepted them, so re-slugging is optional.
2. 209 moves change the introducing topic. That means `vocab/kanji/grammar_point.introducing_topic_id`
   and the topic `introduces` counts. **16 of those vocab items have ambiguous headwords**, and
   `vocab_identity`'s `introducing_topic` tier could flip them, so re-run disambiguation and diff
   `course/vocab_disambiguation_review.json`.
3. Delete `course/gating_exemptions.json` entry `les:n4-dar-receber-02 / vocab:1228690` (the move
   resolves it). Drop the 3 root exemptions and set their count to 4. Lower
   `lesson_sentence_baseline.json` and `practice_coverage_baseline.json`.
4. **Owner eyes on the 8 grammar move rows** (`review_flag`): the grammar card now comes before its
   explanation. Most are 1–6 lessons, but `gram:nasaru` (n4-keigo-03 → n4-condicionais-04) is **60
   lessons early** and drags `ex:n4-keigo-03-3` into a conditionals lesson. That is a legal move, and a
   poor one. Two kanji-exame moves are also long, legal and worth a glance: 合 at +75 and 好 at +85.
5. Proposals (not written): land the scratch script as `scripts/derive_forward_refs.py`, and add a
   **C5 ratchet** to `validate_lesson_gating.py` counting forward edges by tier, frozen post-apply at
   16 / 105 / 160. Today C excludes forward edges by construction and cannot see them.

## 7. 20 sample rows (seeded draw: 10 move, 5 rewrite, 5 hold)

| lesson | item | tier | span | decision | rule | detail |
|---|---|---|---|---|---|---|
| n5-verbos-02 | vocab:1266970 | same-level | body-sentence: tatoeba-174533 戸を閉めろ。 | move | A-move | → n5-verbos-02, card, +13 |
| n5-desu-wa-05 | vocab:1465610 | same-level | body-sentence: gen-08415ea48aef お金を財布に入れた | move | A-move | → n5-desu-wa-05, card, +16 |
| n5-adjetivos-02 | vocab:2820690 | same-level | body-sentence: tatoeba-81558 本当にいい天気だ。 | move | A-move | → n5-perguntas-06 (first user), card, +62 |
| n4-forma-simples-05 | vocab:1589350 | same-level | body-sentence: tatoeba-76098 思ったより安くあがった。 | move | A-move | → n4-forma-simples-05, card, +10 |
| n3-perspectiva-02 | kanji:雪 | same-level | body-sentence: tatoeba-125083 天気予報によればあすは雪だ。 | move | A-move | → n3-perspectiva-02, card, 2 exercises, +73 |
| n5-desu-wa-04 | gram:gp-30 | same-level | body-sentence: tatoeba-1596597 なぜ聞くの？ | move | A-move | → n5-desu-wa-03, card, +6 (review_flag) |
| n5-convites-04 | vocab:1012620 | same-level | body-sentence: tatoeba-3366998 もっと休みをとったほうがいい。 | move | A-move | → n5-convites-04, card, +4 |
| n5-particulas-lugar-06 | vocab:1426250 | same-level | body-sentence: gen-59bccb81087b ひるごはんを食べにいきます | move | A-move | → n5-particulas-lugar-06, card, +30 |
| n4-oracoes-relativas-03 | vocab:1193950 | same-level | body-sentence: tatoeba-79723 夜の間に火事が起こった。 | move | A-move | → n4-oracoes-relativas-03, card, +35 |
| n4-causativa-01 | vocab:1157170 | same-level | body-sentence: tatoeba-157461 それをさせるわけにはいかない。 | move | A-move | → n4-oracoes-relativas-07 (first user), card, +68 |
| n5-perguntas-02 | kanji:分 | same-level | body-sentence: tatoeba-80099 木はその実で分かる。 | rewrite | R4 | ex:n5-particulas-lugar-04-6 must travel and asks about vocab the target lacks |
| n4-potencial-03 | kanji:音 | same-level | body-sentence: tatoeba-188299 音楽が聞こえる。 | rewrite | R4 | ex:n4-aspecto-01-7 asks about vocab the target lacks |
| n5-desu-wa-02 | kanji:分 | same-level | body-sentence: tatoeba-4802 それがどこから来たのか分からなかった。 | rewrite | R4 | as above |
| n5-perguntas-04 | kanji:読 | same-level | body-sentence: gen-0fdafb9f86e8 誰がこの本を読みましたか | rewrite | R4 | ex:n5-conectando-07-2 asks about gram/kanji the target lacks |
| n3-causa-03 | kanji:君 | same-level | body-sentence: tatoeba-123542 道理で、君が喜ぶわけだ。 | rewrite | R3 | practice rides on ex:n3-conjectura-04-8, which is shared with other items |
| n5-perguntas-06 | vocab:1188270 | cross-level | body-sentence: gen-54dd1d1ebf25 何か食べたいです | hold | C-hold | taught at n3-limites-06 |
| n5-conectando-06 | vocab:1157170 | cross-level | body-sentence: tatoeba-137646 大学で何をするつもりですか。 | hold | C-hold | taught at n4-conectores-01 |
| n5-numeros-tempo-03 | vocab:1483070 | cross-level | body-sentence: tatoeba-112055 彼はたくさん食べる。 | hold | C-hold | taught at n4-oracoes-relativas-01 |
| n5-te-form-03 | kanji:冷 | cross-level | body-sentence: gen-47206ec62227 冷蔵庫にビールが冷やしてある | hold | C-hold | taught at n3-enfase-01 |
| n5-particulas-lugar-07 | vocab:1514960 | cross-level | body-sentence: tatoeba-145739 信じてくれる？ | hold | C-hold | taught at n4-volitivo-01 |

## 8. Reproduce

`python <scratch>/w21b/w21b_derive.py`, where scratch is
`C:/Users/WiseWolf/AppData/Local/Temp/claude/C--Users-WiseWolf-IdeaProjects-code-yomineko-research/6e155f88-55c0-4356-be9b-4194bf3d985d/scratchpad/w21b/`.
It extracts HEAD into `fx_before/`, replays the moves into `fx_after/`, writes the gate outputs as
`val_*.txt` and rewrites only the pending table. Run time is about 20 s.
