# Sentence replacement review, part 1/3

Input queue: `research/reports/lesson_sentence_review.json` (247 offending lesson→sentence pairs, 123 lessons).
Deliverable scope: replacement candidates for every offending slot in my third of the lessons.

## Split (stable, reproducible)

`bucket(lesson_id) = int(sha256(lesson_id.encode("utf-8")).hexdigest(), 16) % 3`, and I take `bucket == 0`.
That yields **42 lessons / 79 slots** (the other buckets hold 80 and 88 slots).

## Method

For each offending slot I computed, against that lesson's own `cumulative_known_set`, the exact figure the
validator computes (`scripts/validate/validate_lesson_gating.py` check D):

* `new_kanji` = characters of `jp` that exist in `corpus/kanji/n?.json` and are not in `cumulative_known_set.kanji`
* `new_vocab` = `vocab` slugs of `split_mode == "C"` tokens not in `cumulative_known_set.vocab`
* `load = len(new_kanji) + len(new_vocab)`, budget = 0 / 1 / 2 / 2 for pre-n5 / n5 / n4 / n3
* `above` = sentence `level` is later than lesson `level` in `pre-n5 < n5 < n4 < n3 < n2 < n1`

A candidate is called **compliant** only when it satisfies both gates (`load <= budget` AND not `above`),
carries the same teaching point (same `grammar` key as the slot, or the lesson's target vocab), and is not
already displayed by the same lesson. `real` = `provenance.ai_generated == false`.

Working scripts: `.../scratchpad/wfqa/sr1/{lib,dossier,cands,samekey,hard}.py` (read-only over the repo).

I did not review `structure_explanation` on any sentence (excluded by the assignment).

---

## Part A. Four systemic defects that distort this queue

These are not per-slot judgments; they change what many of the 79 rows mean, so the teacher should read
them before working the queue top-down. Each is verifiable from the exported JSON.

### A1. `ほう` in `〜ほうがいい` is linked to the wrong dictionary entry (報, "relatório")

`corpus/sentences/bank.json`, `sent:tatoeba-216787` token 3:

```
surface "ほう"  lemma "ほう"  vocab "vocab:1515620"  pos noun
gloss pt-BR: "lado, opção, alternativa"
```

`vocab:1515620` is **報 (ほう)**, whose own registry sense is `["relatório", "notícia", "informação"]`
(`corpus/vocab/n5.json`). The Layer-B gloss on the token ("lado, opção") describes **方 (ほう)**, which
exists in the registry as `vocab:1516930` with the sense `["direção", "lado"]`. So the token's fact layer
and its meaning layer contradict each other, and any UI that renders a vocab chip for this token shows the
learner 報 = "relatório" inside a lesson about "é melhor fazer".

Scope: **39 bank sentences** carry `ほう → vocab:1515620`. Four are in my slice
(`sent:tatoeba-216787`, `sent:tatoeba-3366998`, `sent:tatoeba-1484928`, `sent:tatoeba-214854`).

Fix: re-link `ほう` in the `ほうがいい` frame to `vocab:1516930` (方), or mark it a grammar-internal token
that does not count as content vocab.

### A2. `よう` in `〜ように / 〜ようにする` is linked to the wrong dictionary entry (用, "afazer")

Same defect, larger blast radius. `sent:tatoeba-78536` token 2 and `sent:tatoeba-10465367` token 2:

```
surface "よう"  vocab "vocab:1546200"  gloss pt-BR: "modo / maneira (forma o padrão ように)"
```

`vocab:1546200` is **用 (よう)** = `["afazer", "tarefa", "compromisso"]`. The よう of ように is **様**,
present in the registry as `vocab:1605840` = `["aparência", "jeito", "modo"]`. The gloss again describes
様 while pointing at 用.

Scope: **127 bank sentences**. Nine are in my slice (`tatoeba-78536`, `-83950`, `-10465367`, `-366809`,
`-8939546`, `-995566`, `-85325`, `-123214`, `-141613`).

Consequence for this queue: all four `les:n4-volitivo-05` slots sit at `load 3` against `budget 2`, and
the third unit of that load is this artifact. **Fixing A2 alone makes that entire lesson compliant with
its current, real, Tatoeba-sourced sentences.** Re-selecting there would be wasted work.

### A3. Elementary items are unlocked long after the lesson that already uses them

`vocab:1157170 為る (する)` is first unlocked at **`les:n4-conectores-01` (course position 206 of 322)**.
Every `〜する`, `〜される`, `〜してください` sentence before that position therefore carries `+1` unknown
vocab, even though the learner has been producing します since the N5 verb topic. The same pattern:

| slug | word | first unlocked at | lessons in my slice already using it |
|---|---|---|---|
| `vocab:1157170` | 為る する | `les:n4-conectores-01` (pos 206) | n4-passiva-02, n4-experiencia-01/03, n4-keigo-03/05, n4-volitivo-04/05, n4-condicionais-04 |
| `vocab:2820690` | いい | `les:n5-conectando-02` (pos 113) | **`les:n5-convites-04`**, whose entire objective is 〜たほうがいい |
| `vocab:1529520` | 無い ない | `les:n5-comparacoes-03` (pos 90) | **`les:n5-adjetivos-04`** (〜くなかった) and **`les:n5-passado-02`** (じゃなかった) |
| `vocab:1522150` | 本 ほん | `les:n5-convites-03` (pos 104) | **`les:n5-verbos-02`**, which unlocks the *kanji* 本 in the same lesson |
| `vocab:1543240` | 予定 よてい | `les:n4-transitividade-05` (pos 162) | **`les:n4-volitivo-04`**, whose objective is 〜予定だ |
| `vocab:1008630` | 迚も とても | `les:n5-passado-04` (pos 78) | `les:n5-passado-03`, the immediately preceding lesson |

The `les:n5-verbos-02` case is the sharpest: that lesson's `unlocks` contains
`{"type":"kanji","ref":"kanji:本"}`, its body renders `<kanji ref="kanji:本"/>`, and its featured sentence
is `あした 本を かう`, yet the *word* 本 counts as unknown for another 42 lessons.

Consequence: several slots below are marked "no compliant real sentence exists" **not** because the bank
is thin but because the pattern being taught contains a word the course unlocks later. Re-selection cannot
fix those; moving the unlock can.

### A4. Two vocab items are never unlocked by any lesson, so slots containing them can never reach load 0

`vocab:1423310 中 (なか)` and `vocab:2846738 何 (なん)` appear in no lesson's `unlocks` anywhere in
`course/`. In my slice they inflate `les:n4-oracoes-relativas-01` (both `の中で` slots, permanent `+1`)
and `les:n5-desu-wa-04` (`なんで聞くの？`). Any の中で sentence carries an unpayable `+1`, which is why
that lesson has no zero-load option in Part B.

### A5 (collateral, outside my slice but it blocks regenerating this queue)

`validate_lesson_gating.py` globs `corpus/kanji/*.json`, which now matches
`corpus/kanji/unregistered_chars.json`. That file is a JSON **object** (`{"why": ..., "characters": [...]}`),
so `for k in json.loads(...): kanji_chars.add(k["character"])` iterates its keys and raises
`TypeError: string indices must be integers`. I reproduced the same failure in my own loader before
narrowing the glob to `corpus/kanji/n?.json`. Until that glob is narrowed, the queue file cannot be
regenerated. I did not run or modify the script.

---

## Part B. Slot-by-slot replacement proposals

Notation per slot: `load X/B` = computed load over budget; `lv` = the sentence's own graded level;
`ABOVE` = graded above the lesson. Candidates are ordered best first.

### les:n4-oracoes-relativas-07 (n4, budget 2, 122 kanji known)

All four displayed sentences violate.

**SLOT `sent:tatoeba-78536`** 落ちないように注意しなさい。/ "Tome cuidado para não cair." — load 6/2, lv n3 ABOVE.
New: 意 注 落 + なさる, する, 用(A2). Note 落ちる is a known *word* (`vocab:1548550`, unlocked by
`les:n4-oracoes-relativas-01`) while the *kanji* 落 is not, a mismatch worth a separate look.
- C1 `sent:tatoeba-81111` (n4, real, load 3) 万事うまくいくように私が気をつけます。/ "Eu vou cuidar para que tudo corra bem."
  This is the only real sentence in the bank carrying the **purpose** 〜ように that the section teaches.
  Over budget by 1 (私 + うまい, minus the 用 artifact it also carries).
- C2 `sent:tatoeba-81309` (n4, real, load 2) 毎日どのようにして学校へ行くのですか。 — **compliant on both gates but wrong point**:
  this is interrogative どのように ("de que modo"), not purpose ように. Do not use it here.
- **Verdict: no compliant real sentence carries this teaching point.** Either pre-teach 私 and accept C1
  at load 3, or author.

**SLOT `sent:tatoeba-83950`** 風邪をひきませんように。/ "Tomara que você não pegue um resfriado." — load 3/2, lv n1 ABOVE.
New: 邪 風 + 用(A2). This is the wish/prayer ように, the rarest of the three uses.
- The whole `you-ni-you-na` pool is 3 sentences; neither of the other two is a wish.
- **Verdict: no compliant candidate.** Without the 用 artifact this slot is load 2 = budget and only the
  n1 level grade fails; 風邪 is the sole real obstacle. Cheapest fix is to unlock 風/邪 or re-grade.

**SLOT `sent:gen-344b2dbc4a13`** 各駅で電車が止まる — load 2/2 (at budget), lv n2 ABOVE. New: 各 止.
**SLOT `sent:gen-71eeebb22ba7`** 各階にトイレがあります — load 2/2, lv n2 ABOVE. New: 各 階.
- The entire `gp-90` (各) pool is 5 sentences, **all AI-generated and all graded n2**, and every one of
  them necessarily contains 各, which the lesson teaching 各 does not unlock.
- **Verdict for both: no compliant sentence of any kind exists.** The real defect is upstream: `gp-90` is
  graded `n4` in `corpus/grammar/n4.json` while its own kanji 各 sits outside the N4 syllabus. Either add
  `kanji:各` to this lesson's unlocks (which makes both slots compliant at load 1 and 1) or move the point.

### les:n5-desu-wa-05 (n5, budget 1, **0 kanji known**)

**SLOT `sent:gen-08415ea48aef`** お金を財布に入れた / "Coloquei o dinheiro na carteira." — load 6/1, lv n2 ABOVE.
New: 入 布 財 金 + 財布, 入れる. This sits under the heading "Cortesia que já virou parte da palavra",
i.e. the section about お fused into everyday words. Four kanji in a lesson whose known-kanji set is empty.
- **C1 `sent:tatoeba-426899` (n5, real, load 0)** おやすみなさい。/ "Boa noite (ao se despedir para dormir)."
  Kana-only, and お休み is exactly a word where the prefix has fused, which is the section's point.
- **C2 `sent:tatoeba-4760435` (n5, real, load 0)** あなたのおかげです。/ "É tudo graças a você." (お陰, same fusion.)
- **C3 `sent:tatoeba-1474639` (n5, real, load 0)** おやすみ。/ "Boa noite." (casual pair of C1.)
- Both C1 and C2 need `grammar: ["o-go"]` added to their `grammar` array so the graph link exists.
- Explicitly **not** `sent:tatoeba-9462381` おおきに (Kansai dialect, wrong register for a first
  politeness lesson) and not `sent:tatoeba-12976232` お前ら (お前 is not honorific お).
- Note the `o-go` pool itself is 5 sentences, all AI-generated; the three above are real but currently
  untagged for this grammar point.

### les:n4-experiencia-05 (n4, budget 2, 194 kanji known)

**SLOT `sent:gen-2d1dcf054c6b`** この町は急に都市化した — load 5/2, lv n3 ABOVE. New: 化 市 都 + する, 急.
- C1 `sent:gen-5db83dd74419` (n3 ABOVE, AI, load 2) 作業を自動化したい / "Quero automatizar o trabalho."
  Matches the lesson body verbatim, which uses 自動化する as its worked example.
- **Verdict: no level-compliant candidate.** All six `gp-126` sentences are n3 or worse because 化 is
  outside the N4 kanji set while the lesson teaches 化する. Adding `kanji:化` to this lesson's unlocks
  makes C1 load 1 and would be the smallest fix.

### les:n4-oracoes-relativas-01 (n4, budget 2, 115 kanji known)

**SLOT `sent:tatoeba-155677`** 私は人ごみのなかで彼女を見つけた。 — load 5/2, lv n3 ABOVE.
New: 彼 私 + 中(A4), 彼女, 見つける. Slot role: the **physical** "no meio de" sense.
- **C1 `sent:tatoeba-125820` (n4, real, load 1)** 鳥が木々の中でさえずっている。/ "Os pássaros estão cantando entre as árvores."
  Compliant on both gates, same physical sense, tagged `no-naka-de`.
- **C2 `sent:tatoeba-189575` (n4, real, load 2)** 雨の中で歌いたい気分だ。/ "Estou com vontade de cantar na chuva."
  Compliant, same sense.
- C3 `sent:tatoeba-191623` (n3 ABOVE, real, load 2) われわれは人ごみのなかでその男を見失った。 — keeps the
  人ごみ image of the original but is above level.

**SLOT `sent:gen-82ddc26749ff`** 果物のなかでりんごが好きです — load 4/2, lv n3 ABOVE. New: 好 果 物 + 中(A4).
Slot role: the **selection / superlative** sense ("dentre as frutas").
- All five `gp-97` sentences are n3-graded, and every one carries the never-unlocked `vocab:1423310 中`.
- **Verdict: no compliant real sentence for the selection sense.** Fix A4 (unlock 中) and
  `sent:tatoeba-191623` drops to load 1; without it this slot cannot be repaired by selection.
- Side note: `gp-97` ("のなかで") and `no-naka-de` ("の中で") are two grammar records for one pattern, both
  unlocked by this same lesson. Worth merging before a teacher re-selects against them.

### les:n4-oracoes-relativas-04 (n4, budget 2, 121 kanji known)

**SLOT `sent:gen-b2c4b3ced962`** 子供が遊んでいる間に夕食を作った — load 5/2, lv n3 ABOVE. New: 作 供 夕 遊 + 間(あいだ).
- The `gp-107` pool is 3 sentences; the other two are n3 AI at load 4.
- **Verdict: no compliant candidate.** The lesson's featured slot `sent:gen-4590c1e65a70`
  (電車を待っている間に本を読んだ, load 2) already carries the point. Recommend **dropping this second
  card** rather than replacing it, and separately unlocking `vocab:1215230 間` in the lesson that teaches
  〜ているあいだに.

### les:n5-convites-04 (n5, budget 1, 64 kanji known)

Both displayed sentences violate; this lesson is the cleanest illustration of A1 + A3.

**SLOT `sent:tatoeba-3366998`** もっと休みをとったほうがいい。 — load 5/1. New: 休 + もっと, 休み, 報(A1), いい(A3).
**SLOT `sent:tatoeba-216787`** さっさと行ったほうがいい。 — load 2/1, **new kanji: none**. New vocab: 報(A1), いい(A3) only.
- Bank-wide search for `ほうがいい` at level ≤ n5 and load ≤ 1: **0 hits.** Every sentence of this pattern
  contains ほう and いい, and at this point in the course both count as unknown.
- **Verdict: no compliant real sentence can exist for this lesson until A1/A3 are fixed.**
  `sent:tatoeba-216787` is *already* a perfect slot (real, N5, zero new kanji); repairing the ほう link and
  moving the `vocab:2820690 いい` unlock ahead of `les:n5-convites-04` takes it to load 0. Do that instead
  of re-selecting. For `-3366998`, `sent:tatoeba-232073` (あなたは行ったほうがいい。, n4, real) would be
  load 0 after the same fixes.

### les:n4-experiencia-01 (n4, budget 2, 186 kanji known)

**SLOT `sent:gen-b76ff6005aca`** 音を小さくしてください / "Abaixa o volume, por favor." — load 4/2. New: 音 + する, くださる, 音(おと).
- **C1 `sent:gen-c5c1f79d1694` (n4, AI, load 2)** 電気を明るくしてください / "Deixa a luz mais clara, por favor."
  Compliant on both gates, identical request frame, and the lesson already discusses 明るい.
- C2 `sent:tatoeba-213768` (n4, real, load 1) そう水くさくするな。 — compliant and real, **but** 水くさい is
  the idiom "ser distante/reservado com alguém"; it does not demonstrate "deixar X mais ~". Using it here
  would mis-teach. Flagging it so the next reviewer does not pick it off a load ranking.
- **Verdict: one compliant candidate (C1), AI-generated.** No real `ku-suru` sentence in the bank both fits
  the gates and shows the pattern's core meaning.

**SLOT `sent:gen-f1534c9baa43`** 部屋を明るくする — load 3/2, lv n3 ABOVE. New: 屋 部 + する.
- C1 `sent:gen-c5c1f79d1694` (as above) — but it is the natural replacement for the *other* slot too, and
  the lesson only needs one.
- **Verdict:** 明 and 明るい are already known here; the only blocker is 部屋. Swapping the noun for a known
  one (authoring) is a one-word fix and cheaper than selection. Otherwise drop one of the two slots.

### les:n5-verbos-02 (n5, budget 1, **11 kanji known**: 一二人出十国大年日本見)

All four displayed sentences violate.

**SLOT `sent:gen-867d5c2e8dc3`** 電気を消した — load 4/1, lv n3 ABOVE. New: 気 消 電 + 電気.
Also carries `grammar: ["gp-64"]` = 他動詞・自動詞, an **N4** point this N5 lesson does not teach.
- **Verdict: no compliant candidate** (bank-wide `を` search at level ≤ n5, load ≤ 1 returns 5 sentences,
  none in the dictionary-form frame this lesson uses).

**SLOT `sent:tatoeba-174533`** 戸を閉めろ。/ "Fecha a porta!" — load 3/1, lv n2 ABOVE. New: 戸 閉 + 戸.
Token 2 is `inflection: imperative` (閉めろ). **Register defect on top of the gating one**: this is the
second verb lesson of the course, and 命令形 is not taught anywhere near it; the lesson body itself
concedes the tone is "bem ríspido". Per `design/translation_style.md` §2 the register should mirror what
the learner can produce.
- **Verdict: no compliant candidate; recommend removal rather than replacement.**

**SLOT `sent:gen-66857872d764`** ともだちと コーヒーを のむ — load 2/1, no new kanji. New vocab: 飲む, 友達.
**SLOT `sent:gen-a6201c731653`** あした 本を かう — load 2/1, no new kanji. New vocab: 本 (see A3), 明日.
- Both are kana-first, level-appropriate, and their only failure is that four elementary N5 words (飲む,
  友達, 本, 明日) are unlocked later in the course than the lesson that displays them.
- **Verdict: keep both; fix the unlock order (A3).** Re-selection here would replace correct material.

### les:n5-verbos-03 (n5, budget 1, 14 kanji known)

**SLOT `sent:tatoeba-122195`** 日毎に寒くなってくる。 — load 4/1, lv n4 ABOVE. New: 寒 毎 + 寒い, なる.
The body itself says "Por enquanto não precisa produzir essa estrutura", i.e. it admits 〜てくる is above level.
- Best same-key option `sent:tatoeba-235143` (５月は４月のあとにくる。, n4 ABOVE, real, load 2) is still
  above level and over budget.
- **Verdict: no compliant candidate.** Recommend dropping the card; the lesson's other slot
  (`sent:tatoeba-5320` どこに行きますか？, load 1) already covers the movement-verb objective.

### les:n4-condicionais-04 (n4, budget 2, 129 kanji known)

**SLOT `sent:tatoeba-80898`** 無茶しなければよかった。 — load 3/2, lv n3 ABOVE. New: 無 茶 + する.
Slot role is specifically the **negative** 〜なければよかった (it sits directly under the `l1-pitfall` note
about that form).
- C1 `sent:tatoeba-5651760` (n5, real, load 0) きのう来ればよかったのに。 — compliant, but **affirmative**;
  the lesson already shows two affirmative examples.
- C2 `sent:tatoeba-11213861` (n4, real, load 1) メモしとけばよかったね。 — compliant, also affirmative.
- **Verdict: no compliant real sentence exists for the negative variant.** The whole `gp-138` pool is
  3 sentences and only this one is negative. Needs authoring.

### les:n4-experiencia-03 (n4, budget 2, 193 kanji known)

**SLOT `sent:gen-9bc0cee86eab`** 間違いに気がついて直した — load 3/2, lv n3 ABOVE. New: 直 違 + 直す.
- **C1 `sent:gen-6c26b28328bc` (n3 ABOVE, AI, load 1)** 電車を間違えたことに気がついた / "Percebi que tinha pegado o trem errado."
  Same 〜に気がつく frame, drops 直す, halves the load.
- C2 `sent:gen-9aa5ef9c9efc` (n3 ABOVE, AI, load 1) 雨が降っていることに気がつかなかった.
- **Verdict: no level-compliant candidate** (all four `ni-ki-ga-tsuku` sentences are AI and n3+). C1 is the
  least-bad; the residual violation is the level tag only.

### les:n4-forma-simples-07 (n4, budget 2, 113 kanji known)

**SLOT `sent:tatoeba-182469`** 急にやせだしました。 — load 3/2. New: 急 + 急(きゅう), 痩せる. Polite ました in a
lesson whose theme is casual speech, so the register is also slightly off.
- **C1 `sent:tatoeba-11024990` (n4, real, load 2)** 急にダメになったな。/ "De repente as coisas ficaram ruins, né."
  Compliant on both gates, casual, matches the lesson's casual-adverb theme.
- **C2 `sent:tatoeba-182471` (n4, real, load 2)** 急にブレーキをかけるな。/ "Não freie de repente."
  Compliant; the negative-imperative な is blunter than the lesson's tone.
- C3 `sent:tatoeba-10962344` (n4, real, load 3) 急に天気が悪くなってきた。 — over budget by 1.
- **Verdict: two compliant real candidates; recommend C1.** Note every 急に sentence costs the 急 kanji,
  which the lesson teaching `kyuu-ni` does not unlock; unlocking it would take C1/C2 to load 1.

### les:n4-passiva-02 (n4, budget 2, 237 kanji known)

All four displayed sentences violate.

| slot | jp | load/2 | lv | new |
|---|---|---|---|---|
| `sent:gen-552e95412e88` | 白い猫は幸せのしるしとされている | 3 | n3 ABOVE | 幸 猫 + する |
| `sent:tatoeba-112448` | 彼はその発明者とされている。 | 2 | n3 ABOVE | 彼 + する |
| `sent:tatoeba-221717` | この詩は彼の作とされている。 | 3 | n1 ABOVE | 彼 詩 + する |
| `sent:tatoeba-994752` | 真夜中が幽霊のうろつく時間だとされている。 | 3 | n1 ABOVE | 幽 霊 + する |

- Bank-wide `とされている` search at level ≤ n4 and load ≤ 2: **0 hits.** Structural reason: every
  `とされている` contains される → する, which is the A3 artifact, and every natural example about a person
  needs 彼, which this lesson does not have.
- **Verdict: no compliant sentence of any kind exists.** Recommendation: keep **`sent:tatoeba-112448`**
  (already at load 2 = budget; only the n3 grade fails) and drop the two N1 items, which put 幽霊
  ("fantasmas") and 詩 in front of an N4 learner for no pedagogical gain. Fixing A3 plus unlocking 彼
  takes `-112448` to load 0.

### les:n4-volitivo-04 (n4, budget 2, 156 kanji known)

**SLOT `sent:tatoeba-84326`** 父は来週海外へ行く予定だ。 — load 3/2, lv n3 ABOVE. New: 予 定 + 予定.
**SLOT `sent:tatoeba-9489164`** 明日の予定は？ — load 3/2, lv n3 ABOVE. New: 予 定 + 予定.
- All five `yotei-da` sentences in the bank are n3-graded and carry 予, 定 and `vocab:1543240 予定`
  (best of them is load 3).
- **Verdict for both: no compliant candidate, and re-selection cannot help.** The lesson whose stated
  objective is "Anunciar um plano já agendado com 〜予定だ" does not unlock the word 予定 or its two kanji;
  `vocab:1543240` is unlocked at `les:n4-transitividade-05`, later in course order. Add
  `kanji:予`, `kanji:定` and `vocab:1543240` to this lesson's unlocks and both slots go to load 0.

**SLOT `sent:tatoeba-11669238`** 寝ることにするよ。くたくたなんだ。 — load 2/2 (**at budget**), lv n3 ABOVE. New: 寝 + する.
- **C1 `sent:gen-20a639cf6fd7` (n4, AI, load 1)** 今年は車を買わないことにした / "Este ano decidi não comprar carro."
  Compliant on both gates and shows the negative variant the body discusses.
- **Verdict: the only failing gate here is the level tag.** Either accept via exemption or take C1.

### les:n4-volitivo-05 (n4, budget 2, 158 kanji known)

All four displayed sentences violate, all at exactly **load 3/2**, and in all four the third unit of load
is the A2 artifact (`vocab:1546200 用`).

| slot | jp | new |
|---|---|---|
| `sent:tatoeba-10465367` | 忘れないようにするよ。 | 忘 + する, 用(A2) |
| `sent:tatoeba-366809` | 毎日運動するようにする。 | 運 + する, 用(A2) |
| `sent:tatoeba-8939546` | もっと気を付けるようにするよ。 | 付 + する, 用(A2) |
| `sent:tatoeba-995566` | 出来るだけ手紙書くようにするよ。 | 紙 + する, 用(A2) |

- Compliant same-key candidates that exist today (all n4, all real, all load 2):
  **C1 `sent:tatoeba-11268120`** これからは、思ったことを言うようにするよ。 (casual よ, best tonal match)
  **C2 `sent:tatoeba-81579`** 本題からそれないようにしましょう。 (covers the **negative** variant, so it is the
  natural swap for `-10465367`)
  **C3 `sent:tatoeba-83762`** 物事はありのままに見るようにしなさい。 (なさい is instructional; weakest of the three)
- **Verdict: do not re-select.** All four current sentences are real Tatoeba material at the right level
  or one step off, and **fixing A2 alone brings every one of them to load 2 = budget**. Only
  `sent:tatoeba-10465367` and `-8939546` would still carry an above-level tag (n3), which is a re-grading
  question, not a selection one. C1 to C3 are recorded here only as fallbacks.

### les:n5-desu-wa-03 (n5, budget 1, **0 kanji known**)

**SLOT `sent:tatoeba-536769`** 大したものじゃない。 — load 3/1. New: 大 + 物, ない(A3).
- Best same-key option `sent:tatoeba-144679` (人ごとじゃないだろ。, n5, real) is still load 2.
- **Verdict: no compliant candidate.** With `vocab:1529520 ない` unlocked at `les:n5-comparacoes-03`, every
  じゃない sentence costs `+1` at this point in the course, and this lesson has zero kanji budget on top.

**SLOT `sent:tatoeba-229628`** あれ何？ — load 2/1. New: 何 + 何(なに). Slot role: casual question with
neither です nor か.
- The four other `gp-4` (あれ) sentences are all n4-graded.
- **Verdict: no compliant candidate for the "casual, no か" point.** `sent:tatoeba-229723` (あれは何ですか。)
  is the polite counterpart the body already spells out in prose, so it would be redundant.

**SLOT `sent:tatoeba-5059`** 何時ですか。 — load 2/1. New: 何 時.
- **C1 `sent:tatoeba-5332` (n5, real, load 1)** いくらですか？ / "Quanto custa?" — compliant, kana-only,
  pure ですか. Caveat: already displayed by `les:n5-desu-wa-01`.
- **C2 `sent:tatoeba-5078` (n5, real, load 1)** おいくつですか？ — compliant, same caveat.
- **Verdict: two compliant real candidates, both already used elsewhere in the same topic.** If duplicate
  display is unacceptable, this slot needs authoring; a two-kanji sentence cannot fit a 0-kanji known set.

### les:n5-desu-wa-04 (n5, budget 1, **0 kanji known**)

**SLOT `sent:tatoeba-1596597`** なぜ聞くの？ — load 3/1. New: 聞 + なぜ, 聞く.
**SLOT `sent:tatoeba-4789`** なんで聞くの？ — load 3/1. New: 聞 + 聞く, なん(A4).
Slot role for both: sentence-final の.
- The only load ≤ 1 same-key candidates (`sent:tatoeba-778976` なぜ？, `-199219` なぜなんだろう。,
  `-778974` なんで？) all **drop the final の**, which is the teaching point.
- **Verdict: no compliant candidate carries sentence-final の at a 0-kanji known set.** Cheapest real fix:
  unlock `vocab:1591110 聞く` (this lesson sits after `les:n5-verbos-02`, which does unlock it) and
  `kanji:聞`, at which point `-1596597` is load 1 = budget.

**SLOT `sent:tatoeba-85538`** 美人でもある。/ "Ela também é bonita." — load 3/1, lv n3 ABOVE. New: 人 美 + ある.
- No same-key candidate is compliant.
- **Also a tagging defect** (see the `les:n5-conectando-03` entry below): the tokens show
  `で` = "forma de ligação da cópula だ (forma て)" plus `も` = "acrescenta o sentido de 'também'". This is
   〜でもある, not the conjunction でも, yet the sentence carries `grammar: ["demo", "mo"]`.
- **Verdict: no compliant candidate; recommend removal from both lessons that show it.**

### les:n5-passado-03 (n5, budget 1, 29 kanji known)

**SLOT `sent:tatoeba-8608115`** 後で話そうね。 — load 3/1. New: 話 + 後(あと), 話す.
Two further problems: token 2 is `inflection: volitional` (話そう), and 後で is the N4 grammar `ato-de`,
neither of which is taught by this N5 lesson (its grammar known-set has 62 entries and no volitional).
- **C1 `sent:tatoeba-10906687` (real, load 0)** そうですね。/ "Pois é, né." — zero load, the single most
  canonical ね sentence. Caveat: graded n4, which for a two-word kana sentence looks like an over-grade
  worth re-checking.
- **C2 `sent:tatoeba-123182` (n5, real, load 1)** 二、三デメリットがありますね。 — compliant on both gates.
- C3 `sent:tatoeba-5219` (n5, real, load 1) あれ？あなたまだここにいたのね！ — compliant, livelier register.
- **Verdict: C2 is fully compliant; C1 is better pedagogically if the level grade is corrected.**

**SLOT `sent:tatoeba-200577`** とても大きいね。 — load 2/1. New vocab only: とても, 大きい. No new kanji.
- `vocab:1008630 とても` is unlocked by `les:n5-passado-04`, the **immediately following** lesson, and
  `vocab:1588880 大きい` by `les:n5-adjetivos-01`.
- **Verdict: an off-by-one unlock, not a content problem. Keep the sentence and move the とても unlock one
  lesson earlier.** C1/C2 above apply if a swap is preferred.

### les:n5-passado-04 (n5, budget 1, 31 kanji known)

**SLOT `sent:tatoeba-229334`** いい天気だなあ。 — load 3/1. New: 天 気 + いい(A3). Note `vocab:1438690 天気`
*is* unlocked by this very lesson; the cost is its two kanji plus the いい artifact.
- **C1 `sent:tatoeba-226045` (n5, real, load 0)** キツイなあ。/ "Nossa, que duro..." — fully compliant,
  kana-only, casual introspective tone that matches the lesson's なあ objective exactly.
- C2 `sent:tatoeba-1202184` (n5, real, load 1) 車があればなあ。 — compliant on the gates, but the ば
  conditional is N4 and unknown here.
- **Verdict: keep the sentence and unlock 天/気 with it** (the lesson already teaches the word 天気), or
  take C1.

**SLOT `sent:tatoeba-77673`** 冷たいなあ。 — load 2/1, lv n3 ABOVE. New: 冷 + 冷たい.
- **C1 `sent:tatoeba-226045` (n5, real, load 0)** — same as above, and there is only one of it.
- **Verdict: the `naa` pool holds 3 usable sentences for 2 slots.** Assign C1 to whichever slot the
  teacher keeps and drop the other, or author a second kana-only なあ line.

### les:n4-conectores-01 (n4, budget 2, 254 kanji known)

**SLOT `sent:gen-b01569f986d3`** まず席に座りましょう — load 2/2 (at budget), lv n3 ABOVE. New: 席 座.
- **C1 `sent:tatoeba-9106843` (n4, real, load 0)** まずは食べよう。/ "Primeiro, vamos comer." — fully
  compliant, real, same "first step of a sequence" reading, same volitional register.
- **C2 `sent:gen-dde63f5a5cb2` (n4, AI, load 0)** 朝はまずコーヒーを飲む / "De manhã, a primeira coisa que faço é tomar um café."
- **C3 `sent:gen-3eab96687528` (n4, AI, load 1)** 料理はまず野菜を切る — closest to the lesson's
  "instructions step by step" framing.
- Do **not** take `sent:tatoeba-213828` (そうとはまず思えない。, load 0): that まず means "dificilmente",
  a different sense entirely.
- **Verdict: clean fix available. Recommend C1.**

**SLOT `sent:gen-375933b32579`** 電車が止まった　それで遅れた — load 1/2 (**within budget**), lv n3 ABOVE. New: 遅.
- The four load-0 real それで sentences (`-8687007` それでいい？, `-8719362` それで十分？, `-3488181`
  それでいいよ。, `-205726` それで十分だよ。) all use それで as "that is fine / that is enough", **not** as
  the causal connector the lesson teaches. Picking any of them off a load ranking would mis-teach.
- **C1 `sent:gen-0702631e0a28` (n4, AI, load 0)** おなかがすいた　それでパンを買った / "Eu estava com fome, então comprei pão."
  The only compliant sentence with the causal reading.
- **Verdict: the current sentence's only failing gate is its level tag; 遅 is its sole unknown kanji.**
  Keep it and re-grade, or take C1. No compliant *real* causal それで sentence exists.

### les:n4-forma-simples-01 (n4, budget 2, 106 kanji known)

**SLOT `sent:gen-a57fa0b2f6c3`** 彼はもう来たかな — load 2/2 (at budget), lv n3 ABOVE. New: 彼 + 彼(かれ).
**SLOT `sent:gen-f626c3374153`** 明日は晴れるかな — load 2/2 (at budget), lv n3 ABOVE. New: 明 晴.
- **C1 `sent:gen-de8495dcadfb` (n4, AI, load 2)** 電車に間に合うかな / "Será que vou conseguir pegar o trem a tempo?"
  The only candidate compliant on both gates.
- The `kana` pool is **3 sentences, all AI-generated**: there is no real Tatoeba かな sentence in the bank
  at all, which is worth recording since 1.2 of the spec prefers selection over generation.
- **Verdict: one compliant candidate for two slots.** Recommend C1 for one slot; the other needs either a
  level re-grade (both current sentences are already at budget) or authoring.

### les:n4-keigo-01 (n4, budget 2, 254 kanji known)

**SLOT `sent:tatoeba-174190`** 交換台でございます。/ "Aqui é a telefonista." — load 2/2 (at budget), lv n2 ABOVE. New: 交 換.
- **C1 `sent:tatoeba-1336459` (n4, real, load 0)** こちらはサービスでございます。/ "Isto é cortesia da casa."
  Fully compliant, real, and the service-counter register is exactly what the body describes ("lojas,
  hotéis, anúncios").
- **C2 `sent:tatoeba-347297` (n4, real, load 1)** これはなんでございますか。 — compliant; adds the question form.
- C3 `sent:gen-8c01f644ede3` (n4, AI, load 0) 本日は休みでございます.
- **Verdict: clean fix. Recommend C1.**

### les:n4-keigo-02 (n4, budget 2, 254 kanji known)

**SLOT `sent:tatoeba-236843`** お手数をおかけしてすみません。 — load 2/2 (at budget), lv n3 ABOVE. New: 数 + する.
**SLOT `sent:tatoeba-126710`** 遅れてすみません。 — load 1/2 (**within budget**), lv n3 ABOVE. New: 遅.
**SLOT `sent:tatoeba-171272`** 今晩お会いできなくてすみません。 — load 1/2 (**within budget**), lv n3 ABOVE. New: 晩.
- **C1 `sent:tatoeba-231454` (n4, real, load 0)** こんなに長い間待たせてすみません。/ "Desculpe por tê-lo feito esperar por tanto tempo."
  The only load-0 candidate, and only one of the three slots can take it.
- C2 `sent:tatoeba-125913` (n4, real, load 1) 長くお待たせしてすみませんでした。 — compliant, shows the
  past form すみませんでした that the lesson objectives name.
- **Verdict: all three slots fail only on the level tag** (two are already inside budget).
  `sent:tatoeba-126710` (遅れてすみません) is the single most useful phrase in the lesson and its only cost
  is the 遅 kanji. Recommend re-grading rather than replacing; use C1/C2 only if the teacher wants to
  retire `-236843`, whose お手数 register is the most advanced of the three.

### les:n4-keigo-03 (n4, budget 2, 254 kanji known)

**SLOT `sent:tatoeba-85325`** 病気が全快なさるように。 — load 2/2 (at budget), lv n2 ABOVE. New: 全 快.
- **C1 `sent:tatoeba-223947` (n4, real, load 1)** このお金をどうしようとなさるのですか。/ "O que o senhor pretende fazer com este dinheiro?"
  Compliant, real, なさる as the honorific of する in a natural customer-facing question.
- **C2 `sent:tatoeba-3563138` (n4, real, load 0)** そうなさるのもごもっともです。 — compliant, but ごもっとも is
  a heavier register than the lesson's level.
- Do not take `sent:tatoeba-193408` (もし来られたら来なさい。): that is なさい (imperative), not なさる, and
  it is already displayed by `les:n4-condicionais-04`.
- **Verdict: two compliant real candidates. Recommend C1.**

### les:n4-keigo-05 (n4, budget 2, 254 kanji known)

**SLOT `sent:gen-59401317dba3`** 私が荷物をお持ちします — load 2/2 (at budget), lv n2 ABOVE. New: 荷 + する.
- **C1 `sent:gen-d58ab4004378` (n4, AI, load 1)** 後で先生にお電話します / "Eu ligo para você (professor) mais tarde."
  Compliant on both gates, same お〜する frame, and it keeps the superior-facing context.
- **C2 `sent:gen-e6f956627466` (n4, AI, load 1)** 道をお教えします.
- No real `gp-111` sentence exists in the bank.
- **Verdict: recommend C1**; the residual violation of the current sentence is 荷 plus the level tag.

**SLOT `sent:gen-6c6ce0d2199b`** よろしくお願いいたします — load 1/2 (**within budget**), lv n3 ABOVE. New: 願.
- All three other `gp-112` sentences are n2/n1 AI at load 2 to 3, i.e. strictly worse.
- **Verdict: keep.** The body explicitly instructs the learner to memorize this as a block
  ("Guarde-a inteira, como um bloco"), the load is inside budget, and the only failing gate is the level
  tag on a fixed courtesy formula. Recommend a `course/gating_exemptions.json` entry over a swap.

### les:n4-passiva-04 (n4, budget 2, 241 kanji known)

**SLOT `sent:gen-d3bba30db3a5`** 彼は少しも怒っていない — load 2/2 (at budget), lv n3 ABOVE. New: 彼 怒.
- **C1 `sent:gen-079400c974bb` (n4, AI, load 1)** そのことは少しも気にしていない / "Eu não estou nem um pouco preocupado com isso."

**SLOT `sent:gen-2be04a058c05`** 今日は宿題が少なくない — load 1/2 (within budget), lv n3 ABOVE. New: 宿.
- **C1 `sent:gen-04494a7c911c` (n4, AI, load 0)** この町には外国人が少なくない / "Nesta cidade não são poucos os estrangeiros."

**SLOT `sent:gen-9054c26d99b8`** 彼が知らない歌はない — load 1/2 (within budget), lv n3 ABOVE. New: 彼.
- **C1 `sent:gen-db5ebe4f0057` (n4, AI, load 0)** 母が作れない料理はない / "Não existe prato que minha mãe não consiga fazer."
- **C2 `sent:gen-7e1666c42c97` (n4, AI, load 0)** この店に売っていない物はない.

- **Verdict for the lesson: three compliant candidates, all AI-generated.** The `gp-102 / gp-103 / gp-104`
  pools contain **zero real sentences**, so 1.2 of the spec cannot be satisfied here by selection at all.
  All three current slots are already inside budget; only the level tags fail. Recommend re-grading and
  keeping, and flagging the three grammar points as needing real-sentence mining.

### les:n4-suposicao-03 (n4, budget 2, 225 kanji known)

**SLOT `sent:tatoeba-9846192`** 君みたいに強ければなあ。 — load 2/2 (at budget), lv n3 ABOVE. New: 君 + 君(きみ).
- **C1 `sent:tatoeba-11264620` (n5, real, load 0)** お父さんみたいに、パイロットになりたい。/ "Quero virar piloto, igual ao meu pai."
  Fully compliant, real, and it matches the body's stated molde `[substantivo] みたいに [verbo/adjetivo]` exactly.
- **C2 `sent:tatoeba-11516169` (n4, real, load 1)** 明日は、いつもみたいに早起きしなくていいの。 — compliant.
- C3 `sent:tatoeba-11044901` (n4, real, load 0) やってることがストーカーみたいになってきた。 — compliant but the
  "stalker" framing is off-register for a beginner course.
- **Verdict: clean fix. Recommend C1.**

**SLOT `sent:gen-7ec782cb2980`** 夢みたいな話だね — load 1/2 (within budget), lv n3 ABOVE. New: 夢.
- **C1 `sent:gen-16b664dbac91` (n4, AI, load 1)** お母さんみたいな先生が好きだ / "Eu gosto de professores que são como uma mãe."
  The only compliant candidate; the `mitai-na` pool holds **no real sentences**.
- **Verdict: current sentence is inside budget and only the level tag fails.** Recommend keeping it.

### les:n5-adjetivos-04 (n5, budget 1, 32 kanji known)

**SLOT `sent:tatoeba-230319`** あまり出かけたくなかった。 — load 2/1, no new kanji. New vocab: ない(A3), あまり.
- Bank-wide `くなかった` search at level ≤ n5, load ≤ 1: **0 hits.**
- **Verdict: no compliant candidate, and none can exist while `vocab:1529520 ない` is unlocked at
  `les:n5-comparacoes-03`, one topic after the lesson that teaches 〜くなかった.** The lesson's other slot
  (`sent:tatoeba-11117435`, load 1) already covers the objective; recommend dropping this card or moving
  the ない unlock.

### les:n5-conectando-04 (n5, budget 1, 75 kanji known)

**SLOT `sent:gen-d354f1465606`** 頭が痛いんです — load 2/1, lv n3 ABOVE. New: 痛 頭.
- **C1 `sent:tatoeba-137685` (n5, real, load 0)** 大雨で外出できなかったんです。/ "É que não pude sair por causa da chuva forte."
  Fully compliant and real, and the "explaining why" reading is exactly the んです the body teaches.
  Caveat: できる is a potential form, which this N5 lesson has not taught, so it should be glossed as a block.
- C2 `sent:gen-d911309f7c89` (n4 ABOVE, AI, load 1) 電車が止まっているんです.
- **Verdict: one fully compliant real candidate. Recommend C1.**

### les:n5-conectando-05 (n5, budget 1, 77 kanji known)

**SLOT `sent:tatoeba-1484928`** それより、本を読んだほうがいい。 — load 2/1. New: 読 + 読む.
- **C1 `sent:tatoeba-3495506` (n5, real, load 1)** 少し休んだほうがいい。/ "É melhor você descansar um pouco."
  Compliant on both gates.
- C2 `sent:tatoeba-232073` (n4 ABOVE, real, load 0) あなたは行ったほうがいい。
- C3 `sent:tatoeba-1656249` (n4 ABOVE, real, load 0) ちょっと休んだほうがいいよ。

**SLOT `sent:tatoeba-214854`** すぐに寝たほうがいい。 — load 1/1 (**at budget**), lv n3 ABOVE. New: 寝.
- Same candidate set. **Only the level tag fails**; recommend keeping and re-grading, since 寝る is the sole cost.

**SLOT `sent:tatoeba-4888`** 外国人って面白いなあ。 — load 1/1 (at budget), lv n3 ABOVE. New: 面.
- **C1 `sent:gen-5412a2ccf468` (n5, AI, load 0)** すしって何ですか / "O que é sushi?" — fully compliant, and
  the lesson body already quotes this exact string in prose as its worked example of topic-introducing って.
- No real って sentence in the bank is compliant.
- **Verdict: C1 is the strongest single swap in my slice** (load 1 → 0, level n3 → n5, and it removes a
  redundancy between prose and card).

Cross-lesson note: this lesson unlocks `gram:hou-ga-ii` while `les:n5-convites-04`, two topics **earlier**,
already teaches `gram:gp-50` (たほうがいい). Two grammar records for one pattern, taught out of order.

### les:n5-passado-02 (n5, budget 1, 28 kanji known)

**SLOT `sent:tatoeba-10515932`** 聞くんじゃなかった。 — load 2/1. New: 聞 + ない(A3).
- Bank-wide `じゃなかった` at level ≤ n5, load ≤ 1: **0 hits.**
- **Verdict: no compliant candidate.** Same root cause as `les:n5-adjetivos-04`: the ない unlock sits two
  topics after the lesson that teaches じゃなかった. Unlock ない (and 聞, already unlocked as a word by
  `les:n5-verbos-02`) and this slot is compliant as written.

### les:n5-te-form-02 (n5, budget 1, 49 kanji known)

**SLOT `sent:tatoeba-85522`** 鼻がつまっています。 — load 2/1, lv n2 ABOVE. New: 鼻 + 鼻(はな).
- **C1 `sent:tatoeba-202782` (n5, real, load 0)** ちょっと見ているだけです。/ "Só estou dando uma olhada."
  Fully compliant, real, kana + known kanji only, clean ている.
- **C2 `sent:tatoeba-193803` (n5, real, load 0)** もしもし、来ていますか。/ "Alô, você está aí?"
- **C3 `sent:tatoeba-5271` (n5, real, load 1)** 何を話しているの？/ "Do que você está falando?" — compliant,
  and 話す is a vocab unlock of this very lesson.
- **Verdict: clean fix, three compliant real candidates. Recommend C1.**

### les:n5-te-form-05 (n5, budget 1, 53 kanji known)

**SLOT `sent:tatoeba-2242416`** 食べてもいいですか？ — load 2/1. New: 食 + いい(A3).
- **C1 `sent:tatoeba-77189` (n5, real, load 1)** 話してもいいですか。/ "Posso falar (com você)?"
  Compliant on both gates (話 is already in the known kanji set); identical permission-question frame.
- C2 `sent:tatoeba-8861912` (n4 ABOVE, real, load 1) いつきてもいいですか？
- **Verdict: one compliant real candidate. Recommend C1.**

### les:n3-intencao-04 (n3, budget 2, 433 kanji known)

**SLOT `sent:tatoeba-123214`** 内訳はどのようにしましょう？/ "Como você gostaria do detalhamento?" — load 1/2
(within budget), lv n1 ABOVE. New: 訳.
**Also a tagging defect**: this is どのように + しましょう ("de que modo devemos fazer o detalhamento"), not
the 〜ようにしましょう construction (verb + ように + しましょう = "vamos procurar fazer") that
`gram:n3-you-ni-shimashou` names and that the lesson objective states. It teaches the wrong thing.
- **C1 `sent:tatoeba-79798` (n3, real, load 0)** 問題点からそれないようにしましょう。/ "Vamos procurar não fugir do assunto."
  Fully compliant, real, and it is the genuine construction, negative variant included.
- **C2 `sent:tatoeba-83568` (n3, real, load 1)** 平易英語で書くようにしなさい。/ "Procure escrever em inglês simples."
- **C3 `sent:tatoeba-172440` (n3, real, load 2)** 今後、あなたの仕事を手伝うようにしましょう。 — compliant, and the
  closest to the lesson's "esforço contínuo" framing.
- **Verdict: replace, not because of the gate but because of the mis-tag. Recommend C1.**

### les:n3-relato-02 (n3, budget 2, 599 kanji known)

**SLOT `sent:tatoeba-141613`** 先生は私たちに毎日教室を掃除するように言う。 — load 1/2 (within budget), lv n2 ABOVE. New: 掃.
- The `n3-you-ni-iu` pool holds exactly **two** sentences; the alternative
  `sent:tatoeba-190909` (医者なら誰でも君に禁煙するように言うだろう。, load 0) is **also** n2-graded and adds だろう.
- **Verdict: keep the current sentence.** It is a textbook ように言う example, inside budget, and its only
  unknown character is 掃. Recommend unlocking `kanji:掃` with this lesson or re-grading.

### les:n4-condicionais-02 (n4, budget 2, 125 kanji known)

**SLOT `sent:tatoeba-200926`** どこに座ったらいいですか。 — load 1/2 (within budget), lv n3 ABOVE. New: 座.
- **C1 `sent:tatoeba-10587976` (n4, real, load 1)** トレーはどこに下げたらいいですか。/ "Onde eu devo deixar a bandeja?"
  Compliant, real, keeps the どこに frame the body walks through.
- **C2 `sent:tatoeba-4860` (n4, real, load 1)** もう何をしたらいいか分からない。 — compliant; interrogative 何 variant.
- C3 `sent:tatoeba-4713` (n5, real, load 0) 何と言ったらいいか・・・。 — compliant but already displayed by
  `les:n4-condicionais-01`.
- **Verdict: two compliant real candidates. The current sentence is inside budget and fails only the level
  tag; 座 is its sole cost.** Recommend re-grading, or C1 if a swap is wanted.

### les:n4-condicionais-05 (n4, budget 2, 131 kanji known)

**SLOT `sent:gen-acbd1be494f0`** 明日晴れるといいです — load 1/2 (within budget), lv n3 ABOVE. New: 晴.
- **C1 `sent:tatoeba-1323453` (n5, real, load 0)** お会いできるといいですね。/ "Tomara que eu possa vê-lo (de novo), né?"
  Fully compliant, real, and it carries the ね the body says usually accompanies といいです.
- C2 `sent:tatoeba-192500` (n4, real, load 1) リムジンを使うといいですよ。 — compliant on the gates but the
  reading is advisory ("é melhor você usar"), not the "tomara que" the lesson teaches. Do not swap it in blind.
- **Verdict: clean fix, and it upgrades a generated sentence to a real one. Recommend C1.**

### les:n4-conectores-04 (n4, budget 2, 254 kanji known)

**SLOT `sent:gen-1bce6041e175`** この部屋は広いし明るい — load 1/2 (within budget), lv n3 ABOVE. New: 部.
- `sent:gen-7586c0111a3c` (あの店は安いしおいしい, n4, AI, load 0) is compliant but is a near-duplicate of
  `sent:gen-3612bfffc506` (この店は安いしおいしい), already displayed by this lesson.
- `sent:tatoeba-148197` (秋はいつしか冬となった。, n4, real, load 0) is tagged `shi` but contains **no し
  particle at all**: いつしか is a single adverb ("sem que se percebesse"). Another mis-tag; do not select it.
- **Verdict: no usable compliant candidate.** The current sentence is inside budget and its only cost is
  the 部 kanji. Recommend keeping and re-grading.

**SLOT `sent:tatoeba-225929`** きみだけでなく僕も悪い。 — load 1/2 (within budget), lv n1 ABOVE. New: 僕.
- **C1 `sent:tatoeba-153017` (n4, real, load 0)** 私は父だけでなくむすこも知っている。/ "Eu conheço não só o pai, mas também o filho."
  Fully compliant, real, and it is the `X だけでなく Y も` molde the body spells out.
- **C2 `sent:tatoeba-182118` (n4, real, load 0)** 魚だけでなく、肉も食べなさい。
- **C3 `sent:tatoeba-219715` (n4, real, load 0)** この本はおもしろいだけでなく、ためにもなる。
- **Verdict: clean fix, three real load-0 options. Recommend C1.**

### les:n4-suposicao-01 (n4, budget 2, 219 kanji known)

**SLOT `sent:gen-aaabebd8cac1`** 明日は雨が降ると聞いた — load 1/2 (within budget), lv n3 ABOVE. New: 降.
- **C1 `sent:gen-2ee7a48d3f5d` (n4, AI, load 0)** 先生は来週休むと聞いた / "Ouvi dizer que o professor vai faltar semana que vem."
- **C2 `sent:gen-34386829da8e` (n4, AI, load 0)** あの店のラーメンはおいしいと聞いた.
- `sent:tatoeba-229897` (ある外国人が私に駅がどこにあるかと聞いた。, n4, real, load 0) is the only **real**
  compliant hit, but its と聞いた means "perguntou", not "ouvi dizer que". Mis-tagged for `to-kiita`; do not
  select it for this slot.
- **Verdict: the current sentence is inside budget; only the level tag fails.** Keep, or take C1.

**SLOT `sent:tatoeba-104331`** 彼は重病だと言われている。 — load 1/2 (within budget), lv n3 ABOVE. New: 彼.
**SLOT `sent:tatoeba-106462`** 彼は死んだと言われている。 — load 1/2 (within budget), lv n3 ABOVE. New: 彼.
- Every `to-iwarete-iru` sentence in the bank needs 彼 or 彼女 (or worse: `sent:tatoeba-123545` needs 徳).
- **Verdict: no candidate improves on the current pair.** Both are inside budget; the cost is the single
  kanji 彼, which the course has still not unlocked at this point. Recommend unlocking `kanji:彼` here.
  Separately, the two are near-duplicates of each other; recommend keeping `-104331` (illness) and dropping
  `-106462` (death) on register grounds for a general-audience course.

### les:n5-conectando-03 (n5, budget 1, 75 kanji known)

**SLOT `sent:tatoeba-2469096`** それから10年が経った。 — load 1/1 (**at budget**), lv n3 ABOVE. New: 経.
- `sent:tatoeba-205916` (それから先の話を聞きたい。, real, load 0) is the only load-0 option but is n4-graded.
- **Verdict: only the level tag fails.** Keep and re-grade, or unlock `kanji:経`.

**SLOT `sent:tatoeba-85538`** 美人でもある。 — load 1/1 (at budget), lv n3 ABOVE. New: 美.
- **Mis-placement, not a load problem.** The lesson teaches sentence-initial contrastive でも ("mas");
  this sentence's でも is the copula て-form で plus binding も ("é bonita **também**"), confirmed by its own
  particle records: `で` → "forma de ligação da cópula だ (forma て)", `も` → "acrescenta o sentido de 'também'".
  A learner meeting it under a でも-contrast checklist will mis-parse it.
- No real bank sentence demonstrates sentence-initial contrastive でも at load ≤ 1; the lesson's other card
  `sent:tatoeba-1057336` (でもなんで？) already does.
- **Verdict: remove from this lesson** (and from `les:n5-desu-wa-04`, where it is the も slot). Its
  `grammar: ["demo"]` tag should be dropped in `corpus/sentences/bank.json`.

### les:n5-verbos-05 (n5, budget 1, 16 kanji known)

**SLOT `sent:tatoeba-11795596`** 8人孫がいます。 — load 1/1 (**at budget**), lv n2 ABOVE. New: 孫 (an N2 kanji).
- **C1 `sent:tatoeba-176635` (n4 ABOVE, real, load 1)** 兄がいます。/ "Eu tenho um irmão mais velho."
  Same います + animate-subject point, one step less above level, and 兄 is far more useful to an N5
  learner than 孫. Still above level and at budget.
- C2 `sent:tatoeba-198311` (n5, real, load 0) ハウスダストにアレルギーがあります。 — fully compliant, **but it is
  あります**, so it cannot carry the animate-subject contrast this slot exists to show.
- **Verdict: no candidate is both level-compliant and animate.** Recommend C1 as the least-bad, or accept
  the current slot and re-grade (孫 is the only thing pushing it to n2).

### les:n4-conectores-06 (n4, budget 2, 254 kanji known)

**SLOT `sent:tatoeba-83211`** 歩きながら本を読んだ。/ "Li um livro enquanto caminhava." — **load 0/2**, lv n3 ABOVE.
- Every kanji (歩 本 読) and every content word is already in this lesson's known set. The **only** failing
  gate is the sentence's own level grade of n3, and 歩きながら本を読んだ is a canonical N4 ながら sentence.
- **Verdict: no replacement needed.** This row is a level-grading artifact, not a content defect. Fix by
  re-checking the sentence's `level` (or by a `gating_exemptions.json` entry), not by re-selection.
- If a swap is nevertheless wanted, five n4-graded load-0 alternatives exist, e.g.
  `sent:tatoeba-226844` お茶を飲みながら話しませんか。 or `sent:tatoeba-11009755` 食べながら話しちゃダメだよ。

---

## Count table

**Slots checked: 79** across 42 lessons (bucket `sha256(lesson_id) % 3 == 0`).

### Outcome per slot

| Outcome | Slots |
|---|---|
| At least one **fully compliant real** candidate proposed (level ≤ lesson, load ≤ budget, correct teaching point) | 16 |
| Only **AI-generated** compliant candidates exist (spec 1.2 preference for selection cannot be met) | 9 |
| **No compliant candidate**; slot needs authoring or an upstream unlock/level fix | 42 |
| **No replacement needed**: the only failing gate is the sentence's own level grade while load ≤ budget | 11 |
| **Recommend removal** rather than replacement (mis-teaches, duplicate, or off-register) | 1 |
| **Total** | **79** |

### Defect class per slot (a slot can carry more than one)

| Class | Slots |
|---|---|
| Over the i+1 budget | 44 |
| Graded above the lesson level | 60 |
| Load inflated by a wrong vocab link (A1 `ほう→報`, A2 `よう→用`) | 13 |
| Load inflated by a late or missing unlock of an elementary item (A3, A4) | 31 |
| Sentence carries grammar the lesson has not taught (imperative, volitional, potential, N4 point in an N5 lesson) | 6 |
| Sentence is **mis-tagged** for the grammar point it is filed under | 6 |
| Register mismatch with the lesson | 3 |
| Teaching point served by **zero real sentences** anywhere in the bank | 9 |

### Systemic findings (Part A)

| # | Finding | Bank-wide scope | In my slice |
|---|---|---|---|
| A1 | `ほう` of `ほうがいい` linked to 報 (`vocab:1515620`) instead of 方 (`vocab:1516930`); token gloss contradicts the linked headword | 39 sentences | 4 |
| A2 | `よう` of `ように` linked to 用 (`vocab:1546200`) instead of 様 (`vocab:1605840`); same gloss/headword contradiction | 127 sentences | 9 |
| A3 | Elementary items (する, いい, ない, 本, 予定, とても) unlocked after lessons that already teach patterns containing them | 6 items verified | 12 lessons |
| A4 | `vocab:1423310 中` and `vocab:2846738 何` are never unlocked by any lesson, so slots containing them can never reach load 0 | 2 items | 3 slots |
| A5 | `validate_lesson_gating.py` globs `corpus/kanji/*.json` and crashes on `unregistered_chars.json` (a JSON object, not a list), so this queue cannot currently be regenerated | 1 script | blocks the whole queue |

### Highest-value single actions, in order

1. Fix **A2** (`よう → 様`). It alone clears all four `les:n4-volitivo-05` slots, which are already real
   Tatoeba sentences at the right level.
2. Fix **A1** (`ほう → 方`) and move the `vocab:2820690 いい` unlock ahead of `les:n5-convites-04`. That
   clears `sent:tatoeba-216787` outright and unblocks the whole ほうがいい family.
3. Move the `vocab:1529520 ない` unlock ahead of `top:n5-passado` / `top:n5-adjetivos`. That is the sole
   blocker on `les:n5-passado-02` and `les:n5-adjetivos-04`, and on `les:n5-desu-wa-03`.
4. Add the missing self-unlocks: `kanji:各` (n4-oracoes-relativas-07), `kanji:化` (n4-experiencia-05),
   `vocab:1543240 予定` + `kanji:予` + `kanji:定` (n4-volitivo-04), `kanji:急` (n4-forma-simples-07),
   `kanji:彼` (n4-suposicao-01, n4-passiva-02). Each is a lesson that teaches a pattern without unlocking
   the characters the pattern is written with.
5. Apply the 16 clean real-sentence swaps in Part B. The strongest are
   `les:n5-conectando-05` → `sent:gen-5412a2ccf468`, `les:n4-keigo-01` → `sent:tatoeba-1336459`,
   `les:n4-conectores-01` → `sent:tatoeba-9106843`, `les:n4-conectores-04` → `sent:tatoeba-153017`,
   `les:n5-te-form-02` → `sent:tatoeba-202782`, `les:n5-desu-wa-05` → `sent:tatoeba-426899`.
