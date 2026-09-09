# W17 — exam-bank builder fixes (scratch prototype, ready for W18)

Written 2026-09-09. **The repo was not modified except by this file.** All development happened in a
scratch mirror; no `corpus/`, `course/`, `contracts/` or `db/corpus.sqlite` write, no git state change.

| artifact | path |
|---|---|
| **patch** (unified diff vs `scripts/export/` at HEAD; `git apply -p1` verified clean) | `…/scratchpad/w17/w17_builder.patch` |
| **regenerated banks** (all 40) | `…/scratchpad/w17/regen/` |
| scratch tree (mirror of `scripts/ corpus/ course/ design/ contracts/ research/derived/`, plus a DB copy) | `…/scratchpad/w17/` |
| per-item diff / change classification / gate output | `diff_report.txt`, `change_report.txt`, `bank_gate.txt`, `level_gate.txt` |
| the 129 withdrawn ids, grouped, each marked stays-out / returns | `keepout.md` |
| 20 sample regenerated items | `samples.md` (reproduced in §8) |

Scratch root: `C:/Users/WiseWolf/AppData/Local/Temp/claude/C--Users-WiseWolf-IdeaProjects-code-yomineko-research/6e155f88-55c0-4356-be9b-4194bf3d985d/scratchpad/w17/`

---

## 1. What the patch contains

Five files. Two are new modules, because three builders now have to answer the same questions the
same way or the level gate and the bank gate disagree about the same item.

| file | change |
|---|---|
| `scripts/export/exam_rules.py` | **new.** `TaughtSets` (the W03 level rule, one implementation), `reading_link_ok` (lemma AND reading, W12's rule), `option_ok` (what may be printed as a choice), the kanji character class |
| `scripts/export/bunsetsu.py` | **new.** `chunk()` — bunsetsu tiles from the stored Layer-A analysis; `scramble()` — every meaning-preserving reordering as `accepted[]`, and a refusal for the meaning-changing ones |
| `scripts/export/build_exam_banks.py` | the six deterministic families, rewritten around those rules |
| `scripts/export/build_authored_banks.py` | `vocab` slug + `ai_generated`, the flagged table by default, a target↔headword guard, `--out` |
| `scripts/export/build_listening_bank.py` | `source` (the one provenance field it never wrote), `--out` |
| `scripts/validate/test_exam_builders_w17.py` | **new.** 28 unit checks, one per way a rule can break |

### The nine A2 fixes (`exam_bank_regen_review.md` §5.1)

| # | fix | measured effect |
|---|---|---|
| 1 | leak guard — `cf` skips a candidate occurring twice (`continue`, not drop); `gf`/`tg` need `count == 1` | 20 cf candidates skipped, 172 gf sentences with no single-occurrence form; **0 check-C failures** |
| 2 | provenance `layer` / `ai_generated` / `needs_review` per family, exactly as `migrate_exam_banks_p7.py` derived them | on all 5,169 items |
| 3 | `vocab: vocab:<jmdict_id>` beside every `vocab_id` | 2,517 deterministic + 260 pp/us items |
| 4 | `reading_verified DESC` preference on the `cf` candidate order (preference, never filter) | folded into the `sentence_vocab` ORDER BY |
| 5 | okurigana penalty on `kanji_reading` distractors | advisory `okurigana_giveaway` **373 → 58** |
| 6 | `orthography` ranked on `len(headword)` + shape bonus + longshot penalty | `orthography_shape_solvable` **304 → 3**, `orthography_longshot_distractors` **241 → 1** |
| 7 | explicit `ORDER BY` on the `sentence_vocab` scan | the 223-item latent order dependence is gone |
| 8 | BOTH tildes rejected (U+FF5E **and** U+301C) | `なん〜か` never printed |
| 9 | `removed_items.json` excluded from the INDEX glob | no phantom "3 items" bank row |

### The QA-wave fixes

| fix | what it does | measured |
|---|---|---|
| **n3 linker on READING** | a `cf` candidate must be proved by a token — or a contiguous run — that spells the headword AND reads the record's kana (`reading_link_ok`) | **44 candidates refused** at selection; the 空/から, 時/とき, 金/きん, 分/ぶん, 上/じょう, 間/ま clusters are gone |
| **bunsetsu tiles + `accepted[]`** | tiles are bunsetsu, and every meaning-preserving reordering ships in `accepted[]`; a tile set that admits a MEANING-CHANGING reordering refuses the item | 660 items, **0** with a bound-morpheme tile; **68 refused** as `same-particle-ambiguous`; advisory `sentence_order_ambiguous` **1 → 0** |
| **homophone/homograph dedupe** | one `orthography` item per (level, kana), one `kanji_reading` item per (level, headword); the group is walked best-first (own level → common → freq → JMdict id) so a bad representative never loses the group | 85 orthography + 45 kanji_reading groups collapsed; あつい / 背 / 君 no longer key the same printed question two or three ways |
| **four real options** | `option_ok` rejects a space, a circled numeral, a slot marker, grammar metalanguage and an exact doubling (`かか`, `とかとか`); a grammar option must also be ATTESTED in the level's own corpus and may not come from the SAME grammar point as the key | 0 non-Japanese options; 33 committed gf/tg items dropped for printing one |
| **explanations** | every auto-graded item carries a pt-BR `explanation` built by a fixed template over record fields | **4,529 of 4,529**, none empty, none a bare restatement of the key |
| **provenance everywhere** | `vocab` slug on pp/us, `ai_generated` from the stem sentence, `source` on the 239 listening items | the three fields no live builder wrote |

**Where the explanation text comes from — and a defect found on the way.** The pt-BR content is in
`localized_text` (the locale module), not in the legacy `*_pt` columns: `sentence.pt` is NULL on all
5,889 rows and `grammar_point.label_pt` on all 496. A first pass reading the columns produced 660
empty and 952 bare-restatement explanations. The builder now reads `localized_text`:
`vocab_sense.gloss` (kr/or/cf), `grammar_point.form_meanings` — a form → meaning map, present on 364
of 496 points — falling back to `grammar_point.label` (gf/tg), and `sentence.translation` (so).
A grammar point's Layer-C `explanation` is deliberately NOT copied into a Layer-B item: the item
carries the `grammar` key and the app renders the point from the registry (spec 1.3).

---

## 2. The level rule (W03), and the one dependency it adds

Implemented once, in `exam_rules.TaughtSets`, as the definition `validate_exam_level_gate.py`
measures: every kanji of the learner-visible Japanese, the item's own `vocab`, the source sentence's
`tokens[].vocab`, and the item's + the sentence's grammar, all inside the `cumulative_known_set` of
the **last lesson of that level's module**.

**It reads the exported `course/` tree, not the DB.** That is not a preference: the DB's
`lesson.cumulative_known_set` stores `vocab:<headword>` refs (`vocab:さあ`) that only the exporter
resolves to `vocab:<jmdict_id>`, so a builder reading the DB would compare slugs against headwords
and find an empty intersection — measured: 0 / 1 / 29 level-clean words instead of 178 / 532 / 1,719.
**W18 must run `export_course.py` before `build_exam_banks.py`.**

Two further corrections the rule forced:

* the kanji class is now the gate's own (`[㐀-䶿一-鿿豈-﫿]`). The builder tested `"一" <= ch <= "鿿"`,
  which misses Extension A and the compatibility block entirely — invisible to the builder, visible
  to the gate.
* an item's own grammar point must be TAUGHT, not merely at the level. `gram:gp-152` (the A3
  duplicate of `gram:te-hoshii`, which no lesson unlocks) owns a form that put an untaught grammar
  key on a live N4 item.

### The pool, per level

| level | level-clean kanji-written taught words | distinct headwords (kr keys) | distinct kana (or keys) | level-clean sentences |
|---|---:|---:|---:|---:|
| N5 | 178 | 176 | 177 | 563 |
| N4 | 532 | 524 | 523 | 2,470 |
| N3 | 1,719 | 1,682 | 1,631 | 4,561 |

W03's claim holds: **N5 orthography is buildable** — 177 keys against a floor of 15.

### Ruby: measured, and not needed

The design point W17 was to settle rather than assume. Measured over the 286 W15 passages: **0 carry
a kanji outside their level's end-of-level `cumulative_known_set`** (N5 43, N4 91, N3 152, all clean).
So the default — *level-clean where the pool allows, ruby only for reading_comp passages* — is
satisfied with the ruby branch unused, and W17 does **not** add a `passage_ruby` field or the gate
clause that would police it. Dead code with no live case is worse than a recorded measurement. If a
future passage needs it, the rule is: emit the ruby form on the ITEM and make the gate accept an
untaught kanji only when it is ruby-covered.

---

## 3. Level gate on the regenerated banks

`validate_exam_level_gate.py --root <scratch>`: **5,169 items in 40 banks, ALL OK.**

**21 of 40 families reach 0 inappropriate items** — every deterministic bank at every level, plus all
three `reading_comp` banks. Per level:

| family | N5 | N4 | N3 |
|---|---|---|---|
| kanji_reading | 0 / 176 | 0 / 400 | 0 / 400 |
| orthography | 0 / 177 | 0 / 400 | 0 / 400 |
| context_fill | 0 / 164 | 0 / 400 | 0 / 400 |
| grammar_form | 0 / 122 | 0 / 300 | 0 / 300 |
| sentence_order | 0 / 60 | 0 / 300 | 0 / 300 |
| text_grammar | 0 / 34 | 0 / 74 | 0 / 122 |
| reading_comp | 0 / 2 | 0 / 8 | 0 / 26 |

(previous ceilings, for the same seven rows: N5 292/376/229/35/90/6/21 · N4 261/393/357/50/7/8/25 ·
N3 182/360/332/32/11/1/18.)

### The families that cannot reach 0, and why

**They are all AUTHORED banks. A builder can only drop from them, and dropping empties them.**

| family | level-appropriate / total | paper draws | if the ceiling went to 0 |
|---|---|---:|---|
| paraphrase | 2/52 · 1/59 · 28/71 | 3 · 4 · 5 | N5 and N4 SHORT — the bank would hold 2 and 1 item |
| usage | 1/52 · 0/59 · 33/71 | 0 · 4 · 5 | N4 would hold **zero** items |
| listening ×13 | 0–25 of 9–27 | not gated (audio pending) | every N5/N4 task/point bank would empty |

Every one of these items is a REAL bank sentence chosen by an author for a specific word; the builder
cannot substitute a level-clean sentence without re-authoring the item. **The fix is an authoring
campaign, not a builder change** — re-select the 366 pp/us target sentences from the level-clean
sentence pool (563 / 2,470 / 4,561 sentences are available) and re-author the 239 listening scripts
inside the level's known set. Their ceilings shrink to the measured values in the meantime
(n4_paraphrase 59→58, n4_usage 60→59, n5_listening_reply 9→7, n3_listening_reply 3→2).

### reading_comp reaches 0 but cannot ship at 0

All 36 surviving rc items are level-appropriate, but the bank is **SHORT at N5 (2 usable vs 3 per
paper) and THIN at N4 (8 vs 4, 2.0× against a 3× floor)**. Setting its ceiling to 0 turns check S
into a hard failure. The cause is not the level rule: 250 of the 286 questions were authored against
the passages **W15 replaced**, and the rc builder's own P1 (aboutness) guard drops them —
`w15_apply_report.md` §7 already names this as W18's work list. **W18 must either re-author those 250
questions before setting the rc ceilings to 0, or keep the committed rc bank and its current
ceilings (21/25/18) for this pass.**

---

## 4. Diff against the committed banks — zero unexplained differences

`diff_banks.py` + `classify_changes.py` over all 40 banks.

| | items |
|---|---:|
| committed | 6,081 |
| regenerated | 5,169 |
| identical on every field | 641 |
| changed | 2,296 |
| dropped | 3,144 |
| added | 2,232 |
| **unexplained (drop or change)** | **0** |

### Every drop class

| n | family | cause |
|---:|---|---|
| 750 | orthography | level: an untaught kanji in the stem or an option |
| 731 | kanji_reading | level: untaught kanji |
| 666 | context_fill | level: untaught kanji |
| 376 | sentence_order | bunsetsu re-chunk retired the morpheme-tile item |
| 186 | reading_comp | W16 rc guard P1/P2-P3/P4 — the question was authored against the pre-W15 passage |
| 72 | context_fill | level: grammar + kanji |
| 66 | sentence_order | level: an untaught grammar tag on the source sentence |
| 64 | reading_comp | level: untaught kanji |
| 57 | context_fill | displaced past the 400 cap (the level-clean pool is deeper than the cap) |
| 41 | kanji_reading | displaced past the 400 cap |
| 30 | grammar_form | an option was not a Japanese form (`option_ok`) |
| 22 | sentence_order | level: untaught kanji |
| 18 | grammar_form | grammar pool narrowed: attested + taught point + single occurrence |
| **12** | **context_fill** | **reading does not agree — the n3 linker fix** |
| 11 | grammar_form | level: untaught kanji |
| 5 | orthography | displaced past the cap |
| 3+1 | kanji_reading / orthography | homophone / homograph group deduped, a sibling key survives |
| 3 | text_grammar | an option was not a Japanese form |
| 1 | text_grammar | a withdrawn ledger item stays out |
| 25 | (various) | level: mixed vocab / grammar / kanji dimensions |

### Every change class

| n | class |
|---:|---|
| 662 | grammar_form: distractors rebuilt |
| 419 | kanji_reading: distractors rebuilt (EB-02 shape ranking) |
| 417 | orthography: distractors rebuilt (EB-06 ranking) |
| 390 | sentence_order: bunsetsu re-chunk (tiles + assembled answer) |
| 225 | text_grammar: distractors rebuilt |
| 174 | context_fill: distractors rebuilt |
| 12 + 2 | grammar_form / text_grammar: a different form was selected (single-occurrence + attested + taught point) |
| 5 | field added only (`explanation`) |
| 3 | **listening: the committed item carries an in-place repair the authoring journal does not** — see §6 |

`explanation`, `accepted` and `grammar` (new on `tg`) are counted as field ADDITIONS, not content
changes, since the committed items had no such field. **`contracts/exam_item.schema.json` is
`additionalProperties: false`, so W18 must re-run `scripts/contracts/build_schemas.py` in the same
commit** or every regenerated item fails the contract.

### The cap, named rather than hidden

98 drops are "displaced past the cap". The level-clean pool at N4/N3 is deeper than the 400/300 caps,
and the pool is ordered by kana, so the N3 `kanji_reading` bank now covers あ…きって only. **This is
pre-existing** — the old builder sorted by kana and capped identically — but the new cut points are
different, so it shows up in the diff. Not fixed here (out of scope); a frequency-ordered cap would
be strictly better and is a one-line decision for the owner.

---

## 5. Bank gate and advisories

`validate_exam_banks.py --root <scratch>`: **5,169 items in 40 banks, 4 failures**, all expected:

* `O n5_reading_comp` SHORT, `O n4_reading_comp` THIN — §3, the rc re-authoring.
* `P baseline reading_comp_string_match` and `P sentence_order_ambiguous` are now **stale at 0** — the
  ratchet's own "a baseline that matches nothing is a stale entry" rule. W18 lowers them.

Checks A–N (identity, option set, blank integrity, reference resolution, per-type derivation) pass on
every item, including the two that used to fail — `pp:n4:745` / `us:n4:745`, `target '運' != vocab 'うん'`
— now refused by a rule instead of a ledger entry (§6).

| advisory | baseline | now |
|---|---:|---:|
| okurigana_giveaway | 373 | **58** |
| orthography_longshot_distractors | 241 | **1** |
| orthography_shape_solvable | 304 | **3** |
| reading_comp_string_match | 32 | **0** |
| sentence_order_ambiguous | 1 | **0** |

Unit tests: `test_exam_builders_w17.py` 28/28, and W16's `test_exam_builders.py` still 9/9.

---

## 6. Three things W18 must decide, not inherit

**(a) Three committed items carry an in-place repair the authoring journal does not.** Regenerating
the authored banks from the journal silently reverts them:

| id | what the committed bank has that the journal does not |
|---|---|
| `lp:n3:008` | the showtime contradiction repaired (qa_sweep/exam_japanese_3.md F12) |
| `lr:n3:tatoeba-11510681` | the reply re-keyed to answer the prompt (F13) |
| `lt:n5:004` | 兄 → お兄さん throughout the script and its options |

Back-port them into `research/derived/reauthor/exam_authored/authored_listen_*.json` **before**
regenerating, or do not regenerate those three banks. One source of truth is the point.

**(b) The verifier's rejects were a command-line argument.** `build_authored_banks.py` took
`--flagged` and nothing else, so a regeneration that forgot the flag re-admitted every item a
verifier had thrown out — measured, **12 N5 + 8 N4 + 4 N3** paraphrase/usage items came back. The
patch makes `research/derived/reauthor/exam_authored/_flagged.json` the default. The listening
builder has no flagged table at all and one item, `lr:n5:tatoeba-213565` (「そこを何とか。」), was
withdrawn by hand for being "above level" — it is in no ledger, the level gate finds nothing wrong
with it, and a rebuild re-admits it. **W18: accept it, or record the reason in a tracked table.**

**(c) `design/exam_simulator.md` says 118 withdrawn items. The file holds 129.** It also says "6,048
items across 40 bank files"; the committed banks hold 6,081. Both numbers need correcting in the same
commit.

---

## 7. The withdrawal ledger — what W18 must keep out

`corpus/exam_banks/removed_items.json`: **129 ids** (full list, grouped by reason, each marked, in
`keepout.md`). Under the W17 builder **63 stay out on their own and 66 return**:

| n | reason | stays out | returns |
|---:|---|---:|---:|
| 93 | stem prints its own answer outside the blank | 31 | **62** |
| 21 | bare-word stem, same option set, homophone keys | 19 | **2** |
| 3 | Japanese selected for 運, lexeme retired in the A9 re-point | 3 | 0 |
| 2 | text_grammar passage changed; the answer is no longer in it | 1 | **1** |
| 2 | exact duplicate of another sentence_order item | 1 | **1** |
| 8 | okurigana giveaway / re-point casualties (kr, or) | 8 | 0 |

**Every return is a repair, not a regression**, and the ledger's own `why` anticipates it ("eligible
to return when the banks are regenerated with the fixed builder"):

* the 62 are all `tg:` / `cf:` ids, whose id is per-passage or per-(sentence, vocab). They come back
  with a **different, non-leaking blank** — check C passes on all 5,169 items.
* the 2 homophone returns are the surviving representative of a group that was withdrawn whole.
* the duplicate return is the survivor of the new answer-dedupe guard (`so:n4:808`'s twin).
* the 3 運 items no longer return at all: the new target↔headword guard refuses them by rule, which a
  ledger entry could not do for future rebuilds.

**W18 should rewrite the ledger's `why` for the 66 returning ids** (they returned repaired) and keep
the 63 out — the builder already does, without needing the file.

## 7b. The 8 stale `corpus/exam_banks/INDEX.md` rows (W15 §7)

`n4_context_fill`, `n4_kanji_reading`, `n4_orthography`, `n4_paraphrase`, `n4_usage`,
`n5_kanji_reading`, `n5_orthography`, and the phantom `removed_items` row. All eight are fixed by the
regeneration: the builder rewrites INDEX.md from a glob over the actual files with
`removed_items.json` excluded (fix 9). The patch also extends the INDEX prose with the level rule,
`accepted[]` and the explanation field, so the file describes what the banks now are.

---

## 8. Twenty regenerated items, for a human read

| # | bank | id | stem / tiles | options (key first) | key | explanation (pt-BR) |
|---|---|---|---|---|---|---|
| 1 | n5_kanji_reading | `kr:n5:163` | 学校 | がっこう · まいとし · じょうず · うまれる | **がっこう** | 学校（がっこう）— escola |
| 2 | n5_kanji_reading | `kr:n5:214` | 口 | くち · あし · いう · のむ | **くち** | 口（くち）— boca |
| 3 | n4_kanji_reading | `kr:n4:116` | 男の子 | おとこのこ · もくようび · ごしゅじん · かんがえる | **おとこのこ** | 男の子（おとこのこ）— menino |
| 4 | n3_kanji_reading | `kr:n3:1185` | 合う | あう · ほう · そう · いう | **あう** | 合う（あう）— combinar |
| 5 | n5_orthography | `or:n5:80` | うまれる | 生まれる · 入り口 · 入れる · 出来る | **生まれる** | うまれる escreve-se 生まれる — nascer |
| 6 | n5_orthography | `or:n5:424` | でる | 出る · ２日 · 生る · 先週 | **出る** | でる escreve-se 出る — sair |
| 7 | n4_orthography | `or:n4:238` | ご | 語 · 山 · 月 · 男 | **語** | ご escreve-se 語 — língua |
| 8 | n3_orthography | `or:n3:31` | あの | 彼の · 商売 · 頂上 · 水道 | **彼の** | あの escreve-se 彼の — aquele |
| 9 | n5_context_fill | `cf:n5:3823:649` | （　）たいですか。 | 休み · 学生 · 後ろ · ３日 | **休み** | 休み（やすみ）— descanso |
| 10 | n5_context_fill | `cf:n5:4207:163` | （　）に人がいる。 | 学校 · 買う · 読む · ６日 | **学校** | 学校（がっこう）— escola |
| 11 | n4_context_fill | `cf:n4:847:648` | これはあっちのより（　）よ。 | 安い · 校長 · 病気 · 習う | **安い** | 安い（やすい）— barato |
| 12 | n3_context_fill | `cf:n3:148:746` | あなたのフランス語の（　）って、ひどすぎるわ。 | 発音 · 転ぶ · 若し · 実際 | **発音** | 発音（はつおん）— pronúncia |
| 13 | n5_grammar_form | `gf:n5:4278` | ちょっと話があるんだ（　）。 | けど · どこ · たい · でも | **けど** | けど — mas / só que (após verbo ou adjetivo-い) |
| 14 | n4_grammar_form | `gf:n4:3758` | 明日は天気（　）。 | かしら · 始める · ように · という | **かしら** | かしら — será que...? (suave, tradicionalmente feminino) |
| 15 | n3_grammar_form | `gf:n3:5213` | ５時に駅で会う（　）。 | ことになっている · わけにはいかない · ようにしましょう · ないことはない | **ことになっている** | ことになっている — ficou combinado que / é regra que |
| 16 | n5_sentence_order | `so:n5:4429` | いい / 人 / みたいじゃ / ないか | (accepted: 1) | **いい人みたいじゃないか** | Ele parece ser uma boa pessoa, não acha? |
| 17 | n5_sentence_order | `so:n5:3202` | テーブルに / コップが / 六つ / あります | (accepted: 2) | **テーブルにコップが六つあります** | Tem seis copos na mesa. |
| 18 | n3_sentence_order | `so:n3:552` | ケーキを / 食べて / しまったら / 手に / 残らない | (accepted: 2) | **ケーキを食べてしまったら手に残らない** | Depois que você comer todo o bolo, não sobra nada nas mãos. |
| 19 | n5_text_grammar | `tg:n5:n5-desu-wa-04-01` | あのかぎはあなたのですか。いいえ、（　）はあにのかぎです。… | あれ · まで · する · なぜ | **あれ** | あれ — aquilo / aquele lá |
| 20 | n4_text_grammar | `tg:n4:n4-conectores-01-01` | 今朝は電車が止まりました。…（　）、駅の前で水を買いました。… | まず · 出す · せる · こと | **まず** | まず — primeiro / antes de tudo |

---

## 9. What is NOT fixed, measured rather than claimed

These are the QA findings outside the W17 fix list. Each is measured on the regenerated banks so W18
inherits a number, not an impression.

| finding | residue after W17 | why it is not a W17 fix |
|---|---:|---|
| **F3 rare orthography** (答え is an rK/ateji form: あの → 彼の) | **44 items** (kr 22, or 22) key a form JMdict flags not-common | needs a `vocab_form.is_common` filter on the ANSWER, which changes which word each item tests — a content decision. Was in the hundreds; the level rule removed most of it |
| **F2 numeral answers/distractors** (`５日`, `２日`) | 137 orthography + 47 context_fill items print a digit in some option | the underlying vocab records key `５日` rather than `五日`; the repair is in the vocab registry, not the builder |
| **F10 context_fill with no context** (`（　）たいですか。`) | 129 cf items have a stem under 8 characters after the blank | needs a fit check on the distractor, not just a difference check — a semantic judgement, not a rule |
| **`so` chunk granularity** | 食べて / しまったら are two tiles where a purist wants one | mode-C keeps 補助動詞 separate; merging them needs a dependency parser, not the stored analysis |
| **grammar distractor strength** (`出す`, `せる` beside `まず`) | not counted | attestation is a substring test, so a form attested only INSIDE another word passes. Tightening it to token-aligned attestation is a follow-up |
| **the alphabetic cap** | 98 displaced items; N3 kanji_reading covers あ…きって | pre-existing; a frequency-ordered cap is an owner decision (§4) |

---

## 10. W18's checklist, in order

1. `git apply -p1 w17_builder.patch` (verified clean against HEAD).
2. Decide §6(a) — back-port the three listening repairs into the journal, or skip regenerating those
   three banks.
3. Decide §6(b) — accept `lr:n5:tatoeba-213565` or record its exclusion.
4. Decide §3 — re-author the 250 rc questions, or keep the committed rc bank this pass.
5. `export_course.py` **before** `build_exam_banks.py` (§2).
6. Regenerate; re-run `scripts/contracts/build_schemas.py` (new fields, `additionalProperties: false`).
7. Lower every ceiling in `exam_level_baseline.json` — 21 families to **0**, plus n4_paraphrase 58,
   n4_usage 59, n5_listening_reply 7, n3_listening_reply 2. Lower the five advisories in
   `exam_banks_baseline.json` to 58 / 1 / 3 / 0 / 0.
8. Rewrite `removed_items.json`'s `why` for the 66 returning ids; correct
   `design/exam_simulator.md` (118 → 129, 6,048 → the new total).
9. Re-export `prototype/app/data/examBanks.json` and assert corpus/prototype parity.
