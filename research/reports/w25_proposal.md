# W25 proposal: N3 pacing, the band gap, and the two missing reading sections (for owner decision D11)

_Status: PROPOSAL. Nothing applied, no course content authored. Plan rows: `APP_PLAN.md` W20, W25, §4 D11._
_Measured 2026-09-23 on a read-only snapshot of `db/corpus.sqlite` (post W13 apply, post W20 vocab apply)
and the course leaves at git HEAD `97550c2a` (post W21b). Scripts: session scratchpad `pauth/w25/measure*.py`
(read-only; re-runnable against any snapshot)._

## 0. The decision in one paragraph

N3 carries 1,596 new words in 101 lessons (median **17 per lesson**, N4: 7). The vocabulary was dealt to lessons
in **gojuon order**, not by theme or by grammar: 91 of 101 N3 lessons draw at least half their words from a single
initial kana, and the course walks あ, か, き, こ, さ, し... from the first N3 topic to the last. That one fact
explains most of what D11 complains about: the words of a real sentence sit a median **32 lessons apart**, so
only **304 of 1,596** N3 words have 3 readable examples at the lesson that teaches them, and 36 lessons never use
one of their own new words in the grammar explanation. The per-deck cap (`new_per_day` = 10) already throttles
N3 to at least 160 days of new vocabulary whatever the lesson count says. **Recommendation: option B** (grammar
lessons keep at most 8 words they actually use; the other ~1,170 words are regrouped by theme into vocabulary
lessons of at most 10), and **do not close the ~750-word band gap wholesale**: close only the targeted subset the
情報検索 section needs, and send the rest back to D12 (level evidence).

## 1. Re-measured baseline

Practice counts come from the DB snapshot (the W20 drills live there and in `corpus/exercises`; the lesson leaves
still list the 2,463 pre-W20 exercises). "Examples" = distinct `<sentence ref>` in the body plus `sentence_refs`.

| level | lessons | new vocab / lesson: median (p90, max) | new items / lesson (vocab+kanji+grammar) | cards / lesson (card faces) | practice items / lesson (per new item) | lessons with 4+ examples | with 0 |
|---|---|---|---|---|---|---|---|
| pre-N5 | 41 | 0 (0, 8) | 0 | 1 (3) | 4 (n/a) | 0 | 41 |
| N5 | 84 | 7.5 (16, 20) | 10 | 10 (23) | 12.5 (1.18) | 30 | 15 |
| N4 | 96 | 7 (12, 19) | 11 | 11 (24.5) | 14 (1.27) | 82 | 12 |
| **N3** | **101** | **17 (18, 21)** | **20** (p90 25, max 31) | **20 (45)** | **20 (1.04)** | **0** | **48** |

What moved since the plan row was written:
- "Median 18" is now **17**: W21b moved 140 vocab unlocks to their first user. 82 of 101 N3 lessons still carry 13 to 18 words.
- **Practice is no longer the problem.** W20 took N3 from 956 to 2,145 exercises (507 authored + 1,638 generated
  drills): 1.04 per new item, close to N5 (1.18) and N4 (1.27). Cloze is 575 of 2,145.
- **Examples are now a selection job, not an authoring one.** The W13 bank (10,209 sentences, 4,076 at level N3)
  gives **100 of 101** N3 lessons at least 4 readable bank sentences carrying one of their own new items
  (median 22 candidates per lesson). The rendered count is still 0 lessons with 4+, because W14 (re-selection)
  has not run. That fix is W14's, and every option below needs it.
- Heaviest lessons by new items: `les:n3-deveres-03` (18 vocab + 10 kanji + 3 grammar), `n3-perspectiva-01`
  (18+9+3), `n3-perspectiva-02` (16+10+3), `n3-deveres-02` (18+7+3).

### 1.1 Why the vocabulary does not stick: the gojuon dealing

| measure | value |
|---|---|
| N3 lessons where one initial kana covers ≥50% of the new words | **91 of 101** |
| a bank sentence's N3 words, distance between the first and last teaching lesson | median **32 lessons** (p25 15); only 235 of 1,497 such sentences fit inside 8 lessons |
| N3 words with ≥3 readable bank examples at their own lesson | **304 of 1,596** |
| ... by the end of N3 (the ceiling any reordering can reach) | 606 |
| ... never within N3 | 990 |
| N3 words the lesson's grammar sections actually use | median 9 per lesson; **36 lessons use none** |

The ceiling of 606 is set by **kanji**, not by order: of the 2,716 bank sentences with an N3 word that stay
unreadable at the end of N3, **2,496 are blocked by kanji alone**, and 1,882 by exactly one untaught kanji.
The top single blockers are 誰 (no level), 結, 僕, 価, 故, 弁, 態, 離 (tagged N1) and 温, 机, 油, 恋, 仲 (tagged N2);
teaching the top 50 would unblock 455 sentences, the top 100 would unblock 731. Most of these are N3 or N4 kanji
in other lists, so this is a **D12 level-evidence finding**, not a W25 one. It is recorded here because it caps
what any rebalance can do for examples.

### 1.2 The deck cap is already the real throttle

`design/unlock_enums.json` `_deck_defaults.new_per_day` = **10 per deck** (`design/srs_design.md` §6 settles
the 15 vs 10 conflict in favour of 10). `courseware_architecture.md` calls the cap "a safety ceiling, not the
primary throttle". At N5/N4 that holds (median 7 words). At N3, **95 of 101 lessons unlock more vocab cards than
one day's cap**, and the 1,596 vocab cards need at least 160 days at the cap. A learner who does one N3 lesson a
day builds a queue of about 7 unseen cards a day. The lesson count is not what paces N3 today. The deck cap is.

### 1.3 The band gap (~750 words)

`design/jlpt_alignment_plan.md` targets about 3,700 cumulative words at N3; the course teaches **2,951**
(712 at N5, 1,355 by N4). **All 1,596 N3 registry records are already taught**, so closing the gap means adding
N2/N1-tagged records (no N2/N1 record carries an N3 tag from any source we hold; 318 N2 records rank inside the
top 5,000 by frequency; N3 median rank 2,590, N2 median 8,378). The level evidence is one list (`bluskyo`) for
N3 vocab: that is D12, and adding 745 words on the same evidence doubles down on it.

## 2. The options

All three keep the same words, kanji and grammar and the same end-of-N3 known set. Practice follows its item:
a W20 drill moves with the record in its `targets` (the tables in `research/derived/repairs/practice_*_exercises.json`);
authored exercises stay with the grammar lesson. Drill counts are per target (64 multi-target drills counted twice).

| | **C. keep, raise the cap** | **A. split heavy lessons by rule** (cap 10 vocab) | **B. vocabulary lessons by theme** (keep ≤8, cap 10) |
|---|---|---|---|
| rule | accept ~17 words/lesson; fix examples via W14 only | a lesson with v > 10 new words becomes ⌈v/10⌉ lessons; grammar, kanji, authored exercises stay in part 1; parts 2..n are vocab-only companions placed right after | the grammar lesson keeps the ≤8 words its grammar sections use (highest frequency first); the rest are regrouped **by theme** into vocab-only lessons of ≤10 inside the same topic |
| N3 lessons | 101 (+0) | **197 (+96)**; 95 lessons split | **227 (+126)**: 101 grammar + 126 vocabulary |
| new items / lesson | median 20, p90 25, max 31 | median 9, p90 16, max 22 | median 9, p90 10, max 18 (grammar lessons median 8) |
| new vocab / lesson | median 17, max 21 | median 9, max 10 | median 9, max 10 |
| cards / lesson (faces ≈ ×2.2) | median 20 | median 9 | median 9 |
| practice items / lesson | median 20 (p90 30) | median 9 (p90 22) | median 9 (p90 15); vocab lessons median 8 drills |
| practice per new item | 1.07 | 1.07 | 1.07 |
| lessons over the daily deck cap | **95** | 0 | 0 |
| words kept with grammar that uses them | as today (median 9 used of 17) | as today, split arbitrarily | yes, by rule (902 items stay, 1,170 words move) |
| fixes the gojuon dealing | no | **no**: companions are the same alphabetical chunks | yes |
| N3 passages to re-gate (a passage uses a word that moves later) | 0 | 84 of 152 | 84 of 152 |
| effect of closing the full band gap (+745) | +7.4 words per lesson, median ~27 new items | +75 companion lessons | +75 vocabulary lessons |

Variants measured and not preferred: A at cap 12 = 190 lessons (+89), 7 lessons over the cap. B at cap 12 = 204
lessons (+103) but 98 lessons over the cap. B keeping ≤6 = 232 lessons (+131). **The cap should equal the deck
cap (10)**: then one lesson a day never builds a backlog, and "lesson complete" and "cards introduced" stay in step,
which is what `courseware_architecture.md` §6 promises.

On examples, B helps only if the regroup follows co-occurrence as well as theme. Moving words to the end of their
topic without regrouping lifts the "≥3 readable examples" count from 87 to 96 of the moved words. The kanji blockers
in §1.1 cap the gain either way.

### 2.1 Exam sections 中文・長文 / 情報検索

The simulator's N3 paper has `reading_comp` 4 items (短文 only) and `text_grammar` 4. The real N3 読解 also has
内容理解（中文） 6 items, 内容理解（長文） 4 items and 情報検索 2 items: **12 items per paper that do not exist**.
These counts are from the JLPT format and are not yet in `design/exam_simulator.md`; re-verify them under the
timing table's two-source standard before a builder hard-codes them. The passage lengths below (about 350 / 550 /
600 characters) are the usual descriptions of the format, not an official figure.

| | measured today | what the section needs |
|---|---|---|
| passage length | 152 N3 passages, median 122 characters, max 192, **0 of 152 ≥ 300** | 中文 ~350, 長文 ~550, 情報検索 ~600 (a notice, timetable or form) |
| known set to write in | end of N3: 2,951 words, 634 kanji; 6,493 of 10,209 bank sentences fully readable (mid-N3 at `les:n3-deveres-05`: 4,041) | enough for 中文/長文 gated to the N3 end or the revisão topic |
| picker rule | "one item per passage per attempt" (`exam_simulator.md`) | a passage's **question set travels together** (中文 2 passages × 3, 長文 1 × 4, 情報検索 1 × 2) |
| structured material | lesson schema has no table primitive; exam items have no `material` field | 情報検索 needs a purpose-built component + a `material` shape (design first) |
| notice vocabulary | of 30 common notice words, 13 untaught: 締め切り, 定員, 募集, 割引, 有料, 日時, 終了 (N2 in our registry), 申し込み, 詳細 (N1), 持ち物 (absent) | a targeted set of about 15–30 words, which is the part of the band gap worth closing now |
| bank depth for ~15 distinct papers (the depth of today's thinner banks) | 0 | about 30 中文 + 15 長文 + 15 情報検索 = **60 passages, 180 questions** |

Feasibility per option: 中文 and 長文 are equally feasible under A, B and C, because all three end N3 with the
same known set and the sections gate to the level end. B adds two things: each thematic vocabulary lesson can gate
one 150–350 character passage on its theme, which gives the course a staircase towards 中文 length (today every
passage stops under 200 characters), and the notice words become one theme lesson ("avisos, inscrições e prazos",
wording illustrative only) that 情報検索 can gate to. Under A and C those words would be appended to whichever
alphabetical lesson has room.

## 3. Estimated work

Cost tags as in `APP_PLAN.md` §6 (S < 0.2 M tokens; M ≈ 1–2 M, ≤ 15 agents; L = a 30–40 agent campaign).

| unit | C | A | B |
|---|---|---|---|
| structure | none | splitter script: unlocks by rule, drills by `targets`, the vocabulary block moved, new slugs, `needs` chained (S) | co-occurrence and theme clustering script over the 1,170 words, then Opus theme labels + verifier (M) |
| lesson bodies | none | 96 companion bodies from a template (list + 4 selected examples + drills + one pt-BR line), 101 lists removed (M, mostly mechanical; Fable sample) | 126 vocabulary bodies (template + one short Layer-C intro each), 101 bodies trimmed (M) |
| re-derivations (exporter, W21 needs, W22 revisão partition, W23 `item_lesson_index`, W21b forward ratchet re-frozen, practice baseline) | none | S + S | S + S |
| passages re-gated | 0 | 84 (S, script) | 84 (S, script) + optional one passage per vocab lesson (M) |
| W14 example selection for N3 | S (needed anyway) | S | S |
| **subtotal** | **S** | **M + S** | **L−** (M + M + S) |
| exam sections (any option) | 60 passages + 180 questions, verifier, picker rule, `material` shape + component, builder + validator: **L** (for scale: the 286 single `reading_comp` questions cost about 4.1 M tokens) |||
| band gap, targeted (notice pack, 15–30 words) | S if appended | S | S (one theme lesson) |
| band gap, full (+745) | M, and median new items ~27 | M + 75 lessons | M + 75 lessons; blocked on D12 in every column |

## 4. Recommendation

**B, with the cap at 10 and at most 8 words kept per grammar lesson, and the band gap closed only for the 情報検索
notice pack.** Reasons, all from the numbers above:

1. The defect behind "18 words per lesson" is the **gojuon dealing**, not the count. A fixes the count and keeps
   the dealing: its 96 companion lessons would be alphabetical word lists with nothing to hang them on.
   C fixes neither and leaves 95 lessons over the deck cap.
2. B's extra lessons are cheap: a vocabulary lesson is a list, 4 selected bank examples and the W20 drills that
   already exist. The only Layer-C authoring is the theme grouping and one intro line per lesson.
3. Cap 10 = the deck cap, so the lesson count becomes the honest pace (N3 then needs about 2.3× N4's lessons for
   2.5× its words), instead of a hidden card backlog.
4. B gives 中文 a staircase and 情報検索 a gating lesson. The full band gap would add 75 lessons on single-list
   evidence, so it waits for D12.

**Sequencing if B is chosen:** B runs before W14's N3 re-selection and before W22's revisão partition and W23's
`item_lesson_index` are applied, so none of them is done twice. The exam sections follow B, because their notice
pack and gating lessons come from it. D12 should see §1.1's kanji list: the single biggest lever on N3 examples is
50–100 kanji that other lists put at N3/N4.

**Owner questions (D11):** (1) B / A / C? (2) the cap: 10 (the deck cap) or higher? (3) the band gap: targeted
notice pack only (recommended), or the full ~745 after D12? (4) confirm the N3 読解 item counts (短文 4, 中文 6,
長文 4, 情報検索 2) under the two-source standard before the builder hard-codes them.
