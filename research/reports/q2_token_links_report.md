# Q2 — token-link repair applied, the course follows the relink (chain unit Q2-token-links, checkpoint)

Written 2026-09-23. The verified token-link audit is applied to the index and published, the level
evidence of five records moves off their same-reading siblings, the seven lessons that unlocked a
sibling now unlock the word they teach, and every downstream table and bank is rebuilt from that.
Plan: `research/reports/token_link_cascade_plan.md` §4 (scenario D) and §5 (run order). This is the
owner's A9 case, "records that do not match the intended word" (`research/reports/PENDING.md` A9b).

## 1. What ran, in order

| step | script | tracked table |
|---|---|---|
| manifest 131 | `scripts/apply_level_evidence.py --db-only --data …/level_transfer_repairs.json` (extended: a row may move `level` and `level_sources`) | `repairs/level_transfer_repairs.json` (5 rows, 1 refused) |
| manifest 132 | `scripts/apply_token_link_repairs.py` (new) | `repairs/token_link_repairs.json` (3,835 token rows, 305 reading-box rows, 62 re-levels), assembled by `scripts/assemble_token_link_repairs.py` (new) |
| manifest 133 | `scripts/apply_sibling_unlock_repoint.py` (new) | `repairs/sibling_unlock_repoint.json` (7 rows, 2 refused) |
| downstream | needs table + apply, item refs derive + apply, W20 drills (builder re-run on a stripped scratch tree, spliced by id), card examples derive + apply, families (3 manifest steps), exporters, conjugations, role exercises, all exam banks, topic tests, speaking path + checkpoints + practice, capabilities, item index, contracts, review views, `sync-data` | `practice_vocab_exercises.json`, `lesson_needs.json`, `item_refs.json`, `card_examples.json`, `card_production_keys.json` |

Steps 131-150 of the old numbering moved to 134-155 (families stay last); the notes of the moved
steps that cite a step at or after 131 were renumbered with them.

## 2. (a, b) The token links

`assemble_token_link_repairs.py` folds the pending files into one table, verdicts keyed by
`sentence#position`, never by batch:

| source | rows applied |
|---|---:|
| audit, mechanical relink | 3,224 |
| audit, mechanical unlink | 209 |
| sample `exclude_patterns` rerouted (`apply_instead`) | 30 (6 relink: 寄る ×3, 吐く ×2, 就く ×1; 24 unlink: そう ×21, どうして ×1, 蔓 ×1, 賽 ×1) |
| sample `exclude_patterns` dropped (old link kept) | 11 (罹る disease ×3, 身体/からだ ×3, census singletons ×5) |
| review rows, ruling (verifier ok) | 327 relink + 44 unlink (154 rulings keep the old link: no row) |
| review rows, verifier-corrected | 1 relink (開く ひらく -> あく); 4 corrections keep the old link |
| **total** | **3,835** |

The sample's `upgrade_candidates` (unlinks the sample reader thought a registry record could take)
were NOT taken: they were never put to a verifier. They stay unlinks (open item).

Apply: guard per row (the C token at the position must read `surface` and carry `old_vocab`; 0
refused on the live index), `token.vocab_id` written, `sentence_vocab` edge-exact: +2,938 new pairs,
−1,226 old pairs, 2,543 old pairs kept because another rule still produces them (mostly R2: every
literal する run keeps its 刷る edge while 刷る sits in the n5 registry, which is R2's documented
multi-valued design). Replay guard, idempotent (second run: 0/0/0).

**Reading boxes.** A W15 box's `uses` is a snapshot of what its own tokenisation resolved to, and it
resolved by written form too. 305 `reading_uses` rows re-decide every uses entry naming a record the
course repoint retires, from the passage's own SudachiPy split-C tokens: 刷る -> 為る 141, 生る -> 成る
93, 用 -> 様 32 (every one is the auxiliary よう stem), 報 -> 方 17, 罹る -> 掛かる 13 (all "take time /
cost", 電話がかかる included), 動 dropped 8 (どう has no record). No token in any box really is a
retired record. 300 rows also rewrite the W15 table's snapshot; the 5 on W15-held boxes are
index-only.

## 3. (d) Levels

`level_transfer_repairs.json`, through W10's `apply_level_evidence.py` path (extended to move
`level` and `level_sources` under the same exact-precondition rule):

| record | level | agreement | evidence |
|---|---|---|---|
| 為る/する | n4 -> **n5** | 1/1 -> 4/4 | all four lists: する "to do" N5 |
| 成る/なる | n3 -> **n5** | 1/3 -> 4/4 | all four: なる "to become" N5 |
| 呉れる/くれる | n1 -> **n4** | 1/3 -> 4/4 | all four: くれる "to give" N4 |
| 掛かる/かかる | n3 -> **n5** | 1/3 -> 4/4 | all four: かかる "to take (time, money)" N5 (not in the plan's four; same fault, same evidence) |
| 方/ほう | n3 -> **n5** | 1/3 -> 1/4 | bluskyo N5 "ほう" (filed on 報); the other three say N3; earliest-level rule, agreement recorded honestly |
| 彼/かれ | **refused** | stays n4 4/4 | the plan's variant C proposed n5; all four lists put かれ "he" at N4. The N5 entry on 彼/あれ is the demonstrative, which that record is |

The siblings (刷る, 生る, 罹る, 報) keep the N5 tally the lists gave the kana entry. Lowering them now
would re-level every sentence whose する/なる/かかる/ほう run still carries a sibling edge through R2.
Open item.

## 4. (e) Re-levels

A touched sentence's stored level moves only where THIS repair moves its computed level:
`computed_level` over the pre-relink edges vs the post-relink edges, both over the corrected
registry. **62 sentences** (`sentence_levels` in the table, each written only over its `from`):
n3 -> n2 21, n4 -> n2 10, n3 -> n1 8, n4 -> n3 7, n2 -> n1 4, n2 -> n3 4, n4 -> n1 3, n5 -> n2 2,
n5 -> n3 1, n5 -> n4 1, n1 -> n3 1. Drivers: 依る (よる, n2) 20, 振り 5, 行けない 5, …

The first apply re-levelled all 3,153 touched sentences (245 moves) and was withdrawn: 58 of those
moves came from the n3 record of the particle で (every で carries an R3 lemma edge), i.e. the
pre-existing stored-vs-component gap that `integrity_audit`'s shrink-only ceiling holds, not from
this repair. With the level transfer the plan's 271 edge-driven changes (variant B) fall to 62.

## 5. (c) The course follows the relink

`sibling_unlock_repoint.json`, both layers (authoring sources + index), cumulative known sets
recomputed, SRS cards follow the unlock:

| lesson | before | after | evidence |
|---|---|---|---|
| n5-verbos-02 | 刷る "imprimir" | **為る** "fazer" (moved from n4-oracoes-relativas-07 with its W27 key) | 932 する tokens; no prose uses 刷る |
| n5-verbos-03 | 生る "dar fruto" | **成る** "tornar-se" (moved from n3-limites-06 with its key) | 397 なる tokens; no prose means "bear fruit" |
| n5-verbos-03 | 罹る | 罹る **kept** + **掛かる** added (moved from n3-estado-01 with its key) | the prose teaches 罹る ("Você vai ouvir também os verbos 罹る (contrair uma doença)…"), so this is an addition |
| n4-oracoes-relativas-07 | 用 "afazer" | **様** (new derived key) | the lesson teaches ように/ような; 173 auxiliary よう tokens |
| n5-comparacoes-01 | 報 "informação" | **方/ほう** (moved from n3-deveres-06 with its key) | the lesson teaches より / ～のほうが |
| n5-perguntas-05 | 動 "movimento" | nothing (どう has no record) | the lesson teaches どんな / どうやって |
| n5-particulas-lugar-07 | — | **呉れる** added (new derived key) | the lesson that teaches くれる (gp-56); no lesson unlocked 呉れる |

Where W21b had placed the sibling at a lesson by its mislinked first use and the lesson it came from
teaches the sibling in prose, the sibling goes back there with its card and key (the W21b rows are
marked `retired_by` and `apply_forward_refs.py` skips them): 生る -> n5-comparacoes-05 (実が生る, the
l1-pitfall note), 報 -> n5-conectando-01 ("informação, notícia"), 用 -> n4-transitividade-05
(用がある), 動 -> n5-passado-04 ("movimento"). 刷る is the one record no lesson teaches any more: it
joins `course/coverage_exemptions.json` with its reason, and `audit_jlpt_coverage.py` now honours that
file (by slug, so a sibling that shares the headword is still required).

**Refused from the plan's list**, because the lesson's own body teaches the sibling: 池 at
n5-desu-wa-02 (chip "lago, lagoa", "indicar o 池 e o 海") and 暮れる at n4-volitivo-01 (chip
"anoitecer" among verbs to conjugate). Their mislinked いけません / くれ drill was regenerated.

**Released hold.** W11a held 様/よう back from any card pending a policy on grammar-bearing formal
nouns. The repoint unlocks it in the slot that already carried a card for the wrong record (用); the
row is marked `released_by` and the general policy question (こと, もの, ところ) stays open.

**Card keys.** Moved cards keep their W27 key verbatim. Two cards had none; keys derived by the W27
residue template, `verified: derived`, **for teacher review**:

| lesson | card | prompt (pt-BR) | accept | sense |
|---|---|---|---|---|
| les:n4-oracoes-relativas-07 | 様/よう vocab:1605840 | como, igual a (a raiz よう de ～ように e ～ような) | 様, よう | 2 |
| les:n5-particulas-lugar-07 | 呉れる/くれる vocab:1269130 | dar (a mim ou ao meu grupo) | 呉れる, くれる | 0 |

Card table 2,951 -> 2,952 rows (刷る retired into `retired_by_q2`; 様 and 呉れる added). Card examples
re-derived: vocab cards with an example 1,255 -> 1,268, kanji 581, grammar 395.

**W20 drills.** 15 of the W20 rows no longer held (target left, cloze token relinked away, or a
distractor/explanation named 刷る "imprimir", 生る "dar fruto", 報, 動 or 用). They were stripped from a
scratch copy of the export and `build_vocab_exercises.py` re-run: 14 keep their exercise id and take
the builder's content (ex:n5-verbos-02-7 now asks "fazer" = する); 1 is retired (ex:n5-verbos-03-20,
生る: 成る is already practised there), 4 are appended for the returned siblings. `apply_practice_exercises.py`
gained the table-driven retire (`retired_by_q2`) and exact `sentence_refs` for regenerated rows.
Three drills of the moved records stay in their old lessons as review (n3-deveres-06-5, n3-estado-01-27,
n3-limites-06-11), the W21b ruling.

## 6. Downstream, measured

| consumer | before (HEAD) | after |
|---|---|---|
| sentence edges | — | +2,938 / −1,226 |
| exam banks | 4,871 items | 4,867 (n5 cf 93 -> 91, n5 so 58 -> 55, n4 cf 317 -> 318; ~40 items swapped, all on touched sentences) |
| exam level gate, ceilings | ALL OK | ALL OK |
| authored banks (pp, us) | n5 9/8 | 9/8 (no S shortfall; the plan's 3 came from untaught targets, which the repoint teaches) |
| placement floor | 4,700 | 4,696 (re-recorded with cause, unplaced 171) |
| role exercises | — | re-filed by level (62 re-levels) |
| speaking path | — | 66/73 unit files; HEAD builders on the pre-Q2 index reproduce HEAD exactly, so all of it is this repair |
| lesson needs | 743 rows | 743 (87 notes/edges re-derived; "刷る (する)" -> "為る (する)") |
| item_refs | 4,717 | 4,720 |

**Ratchets re-recorded with a written cause** (`q2_cause` in each baseline; earlier causes restored
after `--record` dropped them): lesson gating D (pairs_with_new_vocab 25 -> 39: 行けない, 年/ねん,
依る, 前, 中, 付く, 詩, 何/なん, 吐く, 振り now correctly named; over_budget 19 -> 21; above_level
150 -> 160) and C5 same-level 4 -> 10 (中, 前, 何/なに, 付く, 間/ま) — W14 re-selection work; sentence
coverage n4|vocab below 19 -> 20 (暮れる 101 -> 0 sentences, 家内 3 -> 1, 用 back with its 2 real
sentences; everything else shrank); sentence register residue per level (total unchanged 132);
speak strands (23 cells further, 0.1 to 2.4 points), spiral (shopping drills 47 -> 39 and seven
smaller), near-duplicates (18 -> 17, politeness 0 -> 1).

## 7. Rendered lessons against HEAD

20 lesson `.md` files change (71 lines in, 56 out). Every change is one of: the "Introduz" list (the
unlock swaps above; at n5-perguntas-01 only the order, from the 方 address rewrite), a W20 drill regenerated in place (same id and position: "する significa
imprimir" -> "する significa fazer"; distractor glosses "(imprimir)", "(dar fruto, frutificar)",
"(movimento)", "(afazer, tarefa)" gone), the one retired drill (n5-verbos-03 renumbers 22-27 -> 21-26 in
the render), and four appended drills. No prose line changed. Lesson JSON: 274 cumulative known sets,
14 unlock lists, 9 + 8 cards, 61 card examples, 19 needs lists, 17 exercise lists, 5 bodies (exercise
nodes only).

## 8. 30 before/after samples (seeded 20260923, read against the shipped bank)

| # | sentence | jp | token | before | after | origin | level |
|---|---|---|---|---|---|---|---|
| 1 | `sent:tatoeba-146996` | 小さな村が大きな都市に成長した。 | し | 刷る/する (n5) 'imprimir' | 為る/する (n5) 'fazer' | audit:mechanical (wrong_homograph) | n3 -> n3 |
| 2 | `sent:tatoeba-115990` | 彼の目はめがねの奥で笑っていた。 | 彼 | 彼/あれ (n5) 'aquilo' | 彼/かれ (n4) 'ele' | audit:mechanical (wrong_reading) | n2 -> n2 |
| 3 | `sent:tatoeba-1226326` | 私は今夜講演する予定だ。 | する | 刷る/する 'imprimir' | 為る/する 'fazer' | audit:mechanical | n2 -> n2 |
| 4 | `sent:tatoeba-154338` | 私は彼と共同して仕事をやるつもりだ。 | し | 刷る/する | 為る/する | audit:mechanical | n3 -> n3 |
| 5 | `sent:tatoeba-9964946` | 一円玉を作るのに３円かかります。 | かかり | 罹る 'pegar (uma doença)' | 掛かる 'levar (tempo), custar' | audit:mechanical | n2 -> n2 |
| 6 | `sent:tatoeba-115952` | 彼の勇気に感動した。 | 彼 | 彼/あれ | 彼/かれ 'ele' | audit:mechanical | n2 -> n2 |
| 7 | `sent:tatoeba-174578` | 呼吸がしにくいのです。 | し | 刷る/する | 為る/する | audit:mechanical | n3 -> n3 |
| 8 | `sent:tatoeba-206450` | その問題はまもなく処理されるだろう。 | さ | 刷る/する | 為る/する | audit:mechanical | n3 -> n3 |
| 9 | `sent:tatoeba-11056158` | あごに手をあて考えるふりをするが何も浮かばない。 | ふり | 不利 (n3) 'desvantagem' | 振り (n2) 'balanço, aceno' | audit:mechanical | n3 -> n2 |
| 10 | `sent:gen-79838fe22b3c` | 薬を飲んで元気になった | なっ | 生る 'dar fruto' | 成る 'tornar-se' | audit:mechanical | n4 -> n4 |
| 11 | `sent:tatoeba-74693` | このような仕事で怖い顔をしたら、お客さんはいらっしゃらないでしょう。 | し | 刷る/する | 為る/する | audit:mechanical | n3 -> n3 |
| 12 | `sent:gen-915bf8562dee` | 弟は科学者になりたいです | なり | 生る | 成る | audit:mechanical | n3 -> n3 |
| 13 | `sent:tatoeba-219030` | これ、両替してくれますか。 | くれ | 暮れる 'escurecer' | 呉れる 'dar (a mim/nós)' | audit:mechanical | n2 -> n2 |
| 14 | `sent:tatoeba-111315` | 彼はパイロットになる夢をあきらめた。 | なる | 生る | 成る | audit:mechanical | n3 -> n3 |
| 15 | `sent:tatoeba-2173972` | いいかげんにして。 | し | 刷る/する | 為る/する | audit:mechanical | n3 -> n3 |
| 16 | `sent:tatoeba-224505` | ここにいくつかのバッグがあります。 | ここ | 九/きゅう 'nove' | 此処/ここ 'aqui' | audit:mechanical (wrong_pos) | n5 -> n5 |
| 17 | `sent:gen-5f5d86caed9b` | 数学は私の苦手な科目の一つだ | 一 | 一/いち 'um' | (none; 一つ is the run) | audit:mechanical unlink | n3 -> n3 |
| 18 | `sent:tatoeba-200872` | ところが実はどうすることもできないのです。 | どう | 動 'movimento' | (none) | audit:mechanical unlink | n3 -> n1 (another row relinks 実) |
| 19 | `sent:tatoeba-2702337` | 勉強のしすぎで頭が爆発しそう！ | そう | 琴/こと 'koto' | (none) | reroute aux-sou-to-然う | n2 -> n2 |
| 20 | `sent:tatoeba-3496943` | クッキーをお一つどうぞ。 | お | 尾 'cauda' | (none; honorific お) | audit:mechanical unlink | n5 -> n5 |
| 21 | `sent:gen-c7ea5c7b3772` | この国は米を輸出している | 米 | 米/メートル 'metro' | 米/こめ 'arroz' | ruling | n2 -> n2 |
| 22 | `sent:gen-875dd33dcc55` | 梅を一年漬けると美味しくなる | 年 | 年/とし | 年/ねん | ruling | n1 -> n1 |
| 23 | `sent:tatoeba-168040` | 私がここへ来てから二年になる。 | 年 | 年/とし | 年/ねん | ruling | n4 -> n4 |
| 24 | `sent:tatoeba-120672` | 彼から何の便りもない。 | 何 | 何/なに | 何/なん | ruling | n3 -> n3 |
| 25 | `sent:gen-411cd4996768` | 店で米を五キロ買いました | 米 | 米/メートル | 米/こめ 'arroz' | ruling | n3 -> n3 |
| 26 | `sent:tatoeba-77329` | 老いも若きも戦争にいった。 | 若き | 若し/もし 'se' | 若い 'jovem' | ruling | n3 -> n3 |
| 27 | `sent:tatoeba-185295` | 会合は来週木曜に開かれるはずです。 | 開か | 開く/あく | 開く/ひらく | ruling | n3 -> n3 |
| 28 | `sent:tatoeba-175722` | 結論を下すのは君の義務です。 | 下す | 下ろす/おろす 'baixar' | (none; no 下す record) | ruling unlink | n1 -> n1 |
| 29 | `sent:gen-099cd0de9ac8` | 今日は１月５日だ | 月 | 月/つき 'lua' | (none; no がつ record) | ruling unlink | n4 -> n4 |
| 30 | `sent:tatoeba-115273` | 彼は１９７０年６月５日の朝７時に生まれた。 | 月 | 月/つき | (none) | ruling unlink | n3 -> n3 |

Read against the Japanese: 30/30 correct. Row 18's jump to n1 comes from another row of the same
sentence (実 relinked by ruling) and the registry level of that record, not from どう.

## 9. Gate and replay

`python scripts/validate/validate_all.py`: ALL HARD VALIDATORS PASS (quick replay included). New
handlers in `validate_repairs_applied.py`: `token_link_repairs.json` (token carries `new_vocab` at the
re-proved surface), `level_transfer_repairs.json` (level evidence + `level_sources`),
`sibling_unlock_repoint.json` (unlock, card, introduce-once, `returns_to`, `keeps`, sibling
unlocked nowhere else), W21b `retired_by`, W11a `released_by`.

**Full replay (checkpoint)**: `validate_index_rebuildable.py` → `--record`, then a clean run: 794
files compared, **579 held** (was 571): **0 healed, 348 re-pinned, 8 new**, every one with its cause
in `rebuild_baseline.json`. The 348 re-pins are this repair's bytes, which the replay reproduces
(steps 131-133). The 8 new: six n3 lessons whose reading box a single replay of `build_readings.py`
no longer selects after the known sets changed (`readings-accumulated`), and the two n3 review
lessons whose union known set picks up a replay-only headword resolution (`course-identity`). Two
things the first replay caught and this unit fixed rather than pinned: (1) the replay's dissector
lands some surfaces on another sibling than it did live (いけ on 生ける, ため on 溜める), so off the
live index `apply_token_link_repairs.py` applies the row's decision to the address and reports it
(on the live index it still refuses); (2) moving 方/ほう to N5 made `vocab:方` at les:n5-perguntas-01
ambiguous at the level tier and the replay resolved it to ほう, so the lesson now names its record,
vocab:1516925 (かた), through a new row of W11c's `lesson_ref_addresses.json` (both layers).

## 10. Open items

- **P1 (resolver) not done.** `dissect.py` still resolves by written form; the 62 W32 sentences
  ingested at step 152 are dissected after this table and were not audited. The next re-dissection
  reproduces the fault unless the resolver is fixed first (plan §5 P1).
- **Sibling tallies.** 刷る, 生る, 罹る, 報 keep list evidence that belongs to 為る, 成る, 掛かる, 方
  (duplicated claims). Correcting them needs the R2 edge question settled first.
- **Unlinked where a record exists** (sample `upgrade_candidates`, not verified): 伯 -> 履く ×8,
  池 -> 行けない ×15 (+1 行く), 家内 -> 叶う ×2, 為 -> 溜める, 君 -> 組む, いいえ -> 言う, いらっしゃい.
- **Taught records now short of sentences** (real, not lost links): n5 池 2, 動 2, 生る 1, 報 0,
  伯 0, 八つ 0, 杯 0; n4 暮れる 0, 家内 1, 用 2.
- **Teacher review:** the two derived card keys (§5); 為る/成る/掛かる are unlocked in the lesson slot
  of their sibling (n5-verbos-02 godan verbs, n5-verbos-03 motion verbs) while the course's prose
  teaches する at n5-verbos-04, なる at n5-adjetivos-05 and かかる at n4-experiencia-05 (moving them
  there would open forward references); 掛かる has no drill of its own at n5-verbos-03 (the 罹る drill's
  kana answer credits it); 様/さま at n4-suposicao-03 (みたい lesson) may be the same fault.
- **W14 re-selection** for the 14 new-vocab and 2 over-budget pairs and the 6 new forward uses (§6).
- **Speak spiral** lost reach (shopping drills 47 -> 39): worth a look in the speak review.
- The applied inputs (audit, mechanical sample, six ruling tables) moved from
  `research/derived/pending/` to `research/derived/token_links/`; the six `.verdict.json` files stay
  in pending.
