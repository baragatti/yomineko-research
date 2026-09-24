# P4-w32-ingest: the 62 W32 survival sentences banked, all 12 speak cores live

**Unit P4-w32-ingest, 2026-09-23, checkpoint.** Follows C9-W32W30 (`w32_w30_apply_report.md`), which
derived the Layer-B of the 62 unbanked W32 rows and stopped on the residue. The residue was authored and
independently verified since (`research/derived/pending/w32_layerb_authored.verdict.json`: 157 rows,
151 ok, 6 corrected, 0 rejected). This unit folds it, ingests, and switches the remaining survival terms
on.

| | before (HEAD) | after |
|---|---|---|
| bank sentences | 10,209 | **10,271** (+61 Tatoeba, +1 generated) |
| stages with a live survival core (R87) | 9 | **12** |
| `SURVIVAL_CORE_PENDING` | arrival, lodging, past_stories | **empty** |
| W32 rows on the path, in their own stage | 9 of 71 | **71 of 71** (60 in unit 01) |
| lesson files changed under `course/` | | **0** |

## 1. The fold: one table, verified values only

`scripts/assemble_w32_layerb.py` reads the derived file, the kind-tagged authored file and the verdict,
and writes `research/derived/repairs/w32_layerb.json`: one row per sentence carrying the ingest's source
fields (`tatoeba_id`, `jp`, `en`, `pt`, `pt_literal`, `generated`) and its Layer-B inline (tokens,
particles, structure paragraph), every value with an `origin`. The two pending inputs were removed
(folded; git history keeps them), the verdict stays in `pending/`.

Rules: an authored value lands only under a verdict (ok as written, ok false as the verifier's
`corrected` field; a missing verdict refuses the run); rulings reach exactly the tokens they list, lemma
and pos re-checked; afterwards every residue slot must be filled, every content token glossed, every
particle carry a function and an explanation, no em or en dash. Nothing was rejected, so nothing is held.

| slot | derived | authored (ok) | verifier-corrected | verifier outside_scope |
|---|---|---|---|---|
| translation_literal (62) | 0 | 60 | 2 (10647294 一番, 226989 に) | |
| structure paragraph (62) | 0 | 59 | 3 (237476, gen-1c83f478ab11, 1271480) | |
| particle explanation (96) | 69 template | 24 | 1 (172526 か: 分かる takes no object) | 2 |
| particle function (96) | 90 | 6 overrides | | |
| token gloss (158) | 146 | 9 (8 rulings) | | 3 |

The five outside_scope fixes, on DERIVED slots the authored file never held, each guarded by its old
value:

- `1171888` @0 何時: `quando` -> **`que horas`** (何時まで開いてますか; same as 172526 / 189309).
- `122877` @0 日光: `luz do sol; raios de sol` -> **`Nikko (cidade)`** (the bank's place-name style,
  京都 `Kyoto (cidade)`).
- `11870768` @1 方: `lado, direção` -> **`opção`** (その方がいい).
- `235430` @2 は: the template named the head noun 部屋; now **`は apresenta ２人部屋 como o tópico…`**.
- `3549484` @3 は: likewise **`英語のメニュー`** for メニュー.

Not changed, listed for review: the verifier's fifth note (154700 が framed as "sujeito de 好き" by the
template, "alvo de 好き" by the literal; both defensible, a reviewer picks one), and the analyzer
READINGS of 何時 (`なんどき` in 1171888, `いつ` in 172526 / 189309, where the sentence means なんじ). A
reading is a Layer-A analyzer column with its own override mechanism
(`verified_reading_overrides.json`), not a Layer-B slot; the bank already carries 7 `いつ`-read
何時 tokens glossed `que horas`, so it is one class for one reading unit.

## 2. The ingest

`scripts/ingest/ingest_mined_stages.py` gained one thing: a source row that carries
`structure_explanation_pt` is its own Layer-B, and its batch (the unit of atomicity) is the source file.
Everything else is the W13 path unchanged: jp byte-exact against `raw_tatoeba_sentence` (61/61), the
generated row keyed `gen-1c83f478ab11`, I1-I3 invariants, one transaction, `ai_generated` on the one
generated row, `needs_review` on all, tags `["mined", "w32-survival-core"]`, provenance source
`w32:survival-core`.

`en` is the W32 table's, which is a Tatoeba pairing in every real row; 349070 uses its third linked
translation ("I don't understand.", the sentence's meaning) where the first by id is "I don't know.".

**Register, W31 rules.** `derive_sentence_register_v2.py --w13-source research/derived/repairs/w32_layerb.json`
before the ingest (62 `set: w13` rows), the ingest READ them, then `--skip-w13` after the export (10,271
bank rows). 62 / 62 agree with the W32 table and the pre/post values are identical: polite 58
(polite-predicate 52, polite-request 6), neutral 4 (plain-predicate). The regeneration also refreshed
the `signals` / `conflicts` text of 60 older rows (W08b / gp-153 re-keyed their grammar points);
register and rule are unchanged on all 10,209.

Levels of the new rows (computed by persist): n5 8, n4 18, n3 25, n2 7, n1 4.

**Replay.** Manifest step **147** (`quick_family: sentences`), after every other sentence writer so the
rows take the ids they took live; families move to 148-150 (no step number is cross-referenced in
scripts). `validate_repairs_applied.py` registers `w32_layerb.json` with `handle_w32_layerb`: the slug
exists with the row's jp; translation, literal and paragraph [pt-BR] equal; every C token at a row
position has the row's surface and gloss; `particles[]` matches the row's particle, function and
explanation index by index and in count. Plants 6 / 6 caught on a copied tree (gloss reverted, literal
changed, paragraph dropped, particle explanation changed, particle dropped, sentence removed); clean and
restored fixtures pass.

## 3. The speak path

`scripts/export/build_speaking_path.py`:

- **All 71 W32 terms live** in `SURVIVAL_SEEDS` (shopping keeps its 8). `今何時` -> `今何時か` and
  `お勘定` -> the lemma `勘定`, the two spellings C9 recorded this matcher cannot reach.
- **16 seed extensions** (the rows the W32 table marks `seed_extension_required` that C9 had not
  added): お名前は, 分かりません, ゆっくり話し, 勘定, お湯が出ません, をなくしました, 警察を呼ん, 今何時か,
  何時からですか, 何時まで開い, 外国に行った, 行ったことがありますか, お先に失礼, どう思いますか,
  そう思います, 忙しそうですね.
- **A term's own W32 row ranks first in the survival bucket** (`CORE_ROWS`, read from
  `speak_survival_cores.json`). Without it, shortest-first put 勘定を頼むよ ahead of お勘定お願いします,
  遅れて申し訳ない ahead of 遅れて申し訳ありません, 入場は何時からですか ahead of 映画は何時からですか and
  私は今着いたばかりだ ahead of 列車は今着いたばかりです: 4 cores never reached the path (measured, 66 / 71).
  An own row also sets aside real-over-generated, which is D10's default (an authored sentence may lead
  a stage): 薬をください, the only generated core, now opens health-01. With the rule: 71 / 71.

`validate_speaking_path.py`: `SURVIVAL_CORE_PENDING` is now empty. Quoted, before:
`SURVIVAL_CORE_PENDING = {"arrival", "lodging", "past_stories"}`; after:
`SURVIVAL_CORE_PENDING: set[str] = set()`. The gate reports "R87: 12/12 stages open on a survival
phrase; core pending its W32 ingest: none".

Opening units, before -> after (rendered): lodging-01 swaps six "the room" descriptions
(父は部屋にいます, 部屋は真っ暗だった, 部屋には家具がない…) for お湯が出ません, 予約してあります,
警察を呼んで下さい, ２人部屋はありますか, 部屋を見てみたいです, パスポートをなくしました; health-01 swaps
five 医者 descriptions (彼は医者として無能だ…) for 薬をください, 気分が悪いです, お腹が痛いです,
医者を呼んで下さい, とても熱があります; past_stories-01 opens on 楽しかった, 旅行どうでしたか,
日本は初めてですか, 外国に行ったことがあります; arrival-01 gains はじめまして. Full list in section 5's
diff command.

## 4. Speak ratchets, quoted, re-recorded with cause

Measured apart, the same way C9 did (C9 builder on the grown index = "ingest only"):

| gate | HEAD export | ingest only (C9 builder) | this unit |
|---|---|---|---|
| near-duplicate pairs | 21 | 18, 0 FAIL | **18, 4 FAIL** |
| spiral R83 FAILs | 0 | 1 (shopping fluency 20 -> 18) | **8** |
| strand R78 FAILs | 0 | 13 | **16** |
| speak_path FAILs | 0 | 0 | **0** |
| checkpoint items | 329 | 330 | 322 |
| vocab introduced | 700 | 691 | 641 |
| phrases, real / generated | 432 / 0 | 432 / 0 | 431 / 1 |
| deck:phrases cards | 432 | 432 | 432 |

Near-duplicates per stage, after: arrival 13 (was 16), shopping 2 (1), getting_around 1 (0), lodging 1
(0), time_plans 1 (0), health / opinions / politeness / real_talk 0 (1 each). The four that grew are
look-alikes in LATE units (電車のなかに傘を忘れてきた / きのう電車に傘を忘れました, 部屋の中に入ってください /
部屋の中に一人づつ入ってください, 明日は雨かしら / 明日は雨だろうか, それでいい？ / それでいいよ。), not
the cores. Spiral FAILs: about_you say_now 6 -> 4 and fluency 18 -> 17, eating say_now 2 -> 1 and
fluency 5 -> 2, getting_around drills 10 -> 7, lodging say_now 2 -> 1 and drills / late units down,
shopping fluency 20 -> 15; arrival rose to 25 drills / 17 late units. Strand FAILs are all within 1.3
points (arrival meaning-input 15.1 -> 16.4 the largest); 12 / 12 stages were and stay out of band
(W34's rebalance). All three baselines were re-recorded with a `p4w32_cause` key; the earlier
`w32_cause`, `w18_cause` and `w08b_cause` keys, which `--record` drops, were restored from HEAD.

The cost is the trade R87 states: the opening units now teach the survival acts, so fewer seed-bearing
phrases are left to spiral into the late stages. The cores stay; the rebalance is W34's.

## 5. Checks

- Rendered diff of `course/` against HEAD: **74 files, all under `course/speak/`**; 0 lesson files, 0
  `.md` outside speak. Say_now: 313 per-unit phrase moves; every opening unit's in/out listed by
  `git diff HEAD -- course/speak` (sections 3 and 4 quote them).
- Locale parity: the 62 rows arrived with pt-BR Layer-B only; the ratchet rose by exactly their slots
  (literal +62, structure +62, gloss +158, function +96, explanation +96) and carries a `p4w32_cause`.
  Same class as the W40 residue (owner decision B-W40).
- Review views re-rendered (`build_review_views.py --level n5,speak`).
- Exporters, contracts (infer_shapes -> build_schemas -> build_manifest), prototype sync
  (sentences=10271, speakPath=72), `validate_all.py` green with the quick replay.
- Full replay: section 6 (0 new, 0 healed, 171 re-pinned, causes unchanged).

## 6. Full replay (checkpoint)

`validate_index_rebuildable.py` (full, 790 files): the rebuild ran clean through step 147 and the family
steps after it. Result before re-recording: **0 new, 0 healed, 171 re-pinned** (held files whose rebuilt
bytes moved), no break from an earlier unit. By cause key: course-identity 138, not-committed 18,
rollup 8, reauthor-untracked 4, tr-untracked 2, families-order 1; by place: course/n3 101, course/n4
55, corpus 11 (bank, sentences INDEX, 4 kanji levels, families, grammar n4 + INDEX, corpus INDEX),
course INDEX / outline / one n5 and one pre-N5 lesson.

Why lesson files move in the REBUILD when none moves live: the re-pinned lessons differ from the
committed ones in `cumulative_known_set.vocab` (135 files; 11 also in `body`, 5 in unlocks / cards /
objectives), which is the course-identity cause (a
headword resolves to a different vocab id because the rebuild cannot run the re-authoring steps);
where the resolver has to pick, it breaks ties by corpus frequency, and 62 more sentences shift those
counts. No W32 slug appears in any rebuilt lesson file (checked, 0 of 62). Every entry keeps its
existing cause; `--record` rewrote the 171 sha pins only (`rebuild_baseline.json`: 171 lines in,
171 out, 0 cause lines touched).

## 7. Open

- `en` for the 62 rows (B-W40 class); the gloss and function halves are derivable by the W40 rules.
- 何時 readings (なんどき / いつ where the sentence says なんじ) in 1171888, 172526, 189309: a reading
  override unit, with the 7 older bank tokens of the same class.
- 154700: が as "sujeito de 好き" (template) vs "alvo de 好き" (literal); reviewer picks one framing.
- The 8 blocked frames (救急車, チェックイン, アレルギー, 日本語, 迷う, パスワード, おすすめ, ベジタリアン) still
  need vocab records.
- Speak strand rebalance (W34) and the spiral cost above; Fable sample 30 of the 62 rows not drawn.
