# Sentence replacements — part 1 of 3

Adversarial re-selection pass over the lesson→sentence display links queued in
`research/reports/lesson_sentence_review.json`. Read-only pass: nothing under `corpus/`, `course/`,
`scripts/`, `contracts/`, `prototype/` or `db/` was touched.

`structure_explanation` fields were **not** read or judged (being re-authored by another process).

---

## 1. Split, scope, method

**Split rule (stable, reproducible):** `int(md5(lesson_id.encode("utf-8")).hexdigest(), 16) % 3 == 0`.

That selects **43 lessons / 99 violating slots** out of the 123 lessons / 247 slots in the queue.
The three md5 buckets are 43/99, 39/67 and 41/81 lessons/slots, so this rule complements the
`md5 % 3 == 1` slice used by part 2. (Part 3 on disk declares a **sha256** rule, so parts 1+2 partition
cleanly against each other but part 3 does not align with either; the teacher should re-run one of the
three on a common rule if full coverage matters.)

**Gate re-implemented from `scripts/validate/validate_lesson_gating.py` (check D)**, against each lesson's
own exported `cumulative_known_set`:

* `new_kanji` = characters of `jp` present in `corpus/kanji/*.json` and absent from `cumulative_known_set.kanji`
* `new_vocab` = `vocab` slugs of `split_mode == "C"` tokens absent from `cumulative_known_set.vocab`
* `load = len(new_kanji) + len(new_vocab)`; budget = 0 / 1 / 2 / 2 for pre-n5 / n5 / n4 / n3
* `above` = sentence `level` later than lesson `level` in `pre-n5 < n5 < n4 < n3 < n2 < n1`

**Candidate search.** For every slot I scanned all 5 889 records in `corpus/sentences/bank.json` for
sentences that (a) carry the teaching point — tier 1 = a grammar key the **lesson itself unlocks**,
tier 2 = a grammar key of the sentence being replaced, tier 3 = a vocab item the lesson unlocks —
(b) sit at or below the lesson level, (c) come in at `load ≤ budget`, and (d) match register
(plain vs です／ます, judged on the surface form). Real (`provenance.ai_generated = false`) beats
generated. I also recorded, per candidate, which grammar keys it uses that the learner has **not** met
yet, because the validator does not budget grammar and a load-0 sentence can still be pedagogically
out of reach.

**Availability numbers quoted below** ("N at/below level, M within budget") are exhaustive counts over the
whole bank for that grammar key, not samples. Where I write *no compliant real sentence exists*, that is a
complete-scan result, and I re-checked it by raw substring search over `jp` as well.

---

## 2. Headline

| | slots |
|---|---|
| Slots in my slice | **99** |
| Over the i+1 budget | 65 |
| Graded above the lesson level | 66 |
| Flagged **only** for level (load already inside budget) | **34** |
| Over budget **only** because of a mislinked token, a function word, or the lesson's own teaching point | **20** |
| Genuinely over budget after those corrections | **45** |
| Slots with ≥1 tier-1 candidate that fits (level + budget) | 47 |
| …of which the best candidate is a **real** sentence | 45 |

**The single most important result of this pass is that replacing sentences is the wrong repair for
54 of the 99 slots.** Sections 3.1–3.4 give the four root causes, each verifiable in seconds; fixing them
retires more of the queue than any amount of re-selection, and re-selecting first would throw away
correct, human-written examples to work around a data bug.

---

## 3. Root causes that dissolve slots without any replacement

### 3.1 Kana-written words linked to a kanji homophone (Layer-B token defect)

`corpus/sentences/bank.json` resolves several kana surfaces onto a **kanji-headword homophone** through a
rare kana form in the JMdict entry's `forms` list. The `gloss` text is usually right; the `vocab` link is
wrong, so the learner's card, the cross-reference graph and the gating arithmetic all point at the wrong
word.

Confirmed by reading the tokens (counts are token occurrences across the bank):

| surface | linked to | should be | occurrences | evidence |
|---|---|---|---|---|
| `ここ` | `vocab:1578150` 九 (きゅう, "nove") | `vocab:1288810` 此処 | **59** | `sent:tatoeba-5055` 「ここから遠いの？」 token `ここ` → 九; gloss says "aqui" |
| `この` | `vocab:1578150` 九 | `vocab:1582920` 此の | 4 | `sent:tatoeba-74415` 「この部屋の本は私の物ではありません。」 |
| `よう` | `vocab:1546200` 用 (よう, "afazer, tarefa") | `vocab:1605840` 様 (よう, "jeito, modo") | **127** | `sent:tatoeba-78536` 「落ちないように注意しなさい。」 gloss says "modo / maneira" |
| `どう` | `vocab:1451160` 動 (どう, "movimento") | 如何 (どう): **no record exists**; only `vocab:2845606` 如何 (いかが) | **86** | `sent:tatoeba-201153` 「どうやって学校に来たの？」 |
| `ほう` | `vocab:1515620` 報 (ほう, "relatório, notícia") | `vocab:1516930` 方 (ほう, "lado, direção") | **39** | `sent:gen-dc17b084b7de` 「バスより電車のほうが速い」 gloss says "lado, opção" |
| `くれ` / `くれる` | `vocab:1514960` 暮れる ("escurecer, anoitecer") | `vocab:1269130` 呉れる ("dar a mim") | **68** | `sent:tatoeba-145739` 「信じてくれる？」 |
| `その` | `vocab:1176240` 園 (その, "jardim, parque") | 其の: **no record exists** (其処 and 此の do) | **150** | `sent:tatoeba-80099` 「木はその実で分かる。」 |
| `わけ` | `vocab:1550140` 理由 (りゆう) | `vocab:1538330` 訳 | 23 | `sent:tatoeba-10050266` 「彼女が嘘をつくわけがない。」 |
| `やつ` | `vocab:1583095` 八つ (やっつ) | `vocab:1445640` 奴 | 3 | `sent:tatoeba-111396` 「彼はなんて嫌なやつだ。」 |
| `あて` | `vocab:1497610` 父 (ちち) | `vocab:1448820` 当て | 2 | `sent:tatoeba-144802` 「親をあてにしてはいけない。」 |

The mechanism is visible in the vocab record itself: `vocab:1578150` 九 carries
`forms: [… {"form":"ここの"}, {"form":"この"}, {"form":"ここ", "is_kana":true, "is_common":false}]`
(archaic counting readings), and the linker took the rare form over the correct entry.

Why it matters here: **ここ, その, ほう, よう and くれる are exactly the words the lessons in this slice
teach.** `les:n5-perguntas-01` unlocks `vocab:1288810` 此処 correctly, then every ここ example in the
course points the learner at 九. `les:n5-comparacoes-01` is the ～のほうが lesson and 報 is charged against
its budget three times. Two records are missing outright (**其の (その)** and **如何 (どう)**), so those two
cannot be repaired by a swap — a record has to be added first.

**8 units of load across my 99 slots come from this defect alone.**

### 3.2 A sentence's `level` is `max(kanji level, vocab level)`, so one kanji character sets the grade

`scripts/ingest/persist_dissection.py::computed_level` takes the max over the levels of the sentence's
**vocab and kanji rows** and ignores grammar entirely. A word the lesson itself teaches therefore drags
its sentence above the lesson level whenever one of its characters is graded higher:

* `sent:tatoeba-190532` 「一緒に行かない？」: every vocab is n5, the grammar `issho-ni` is n5, the kanji
  一 and 行 are n5. Graded **n3** because 緒 is graded n3. Shown in `les:n5-convites-01`, the lesson whose
  title is *"Convidar com 一緒に e 〜ませんか"*.
* `sent:tatoeba-1006944` 「ナイフが必要だ。」: vocab 必要 is n4, grammar `ga-hitsuyou` is n4. Graded **n3**
  because 必 and 要 are graded n3. Shown in `les:n4-obrigacao-01`, *"Precisar de algo: が必要"*.
* `sent:gen-8bc9ce5df658` 「ドアに鍵がかけてある」: every vocab n5, grammar `te-aru` n5. Graded **n1**
  because 鍵 is graded n1.

**34 of my 99 slots are flagged for level alone with `load` already inside budget.** For these the sentence
is not too hard; the grade is. Either exempt them, or teach the character where the word is taught.

### 3.3 The lesson's own teaching point is charged against the lesson's own budget

38 units of load in my slice are the very item the lesson exists to teach, because the vocab or kanji
record unlocks in a **later** lesson (course positions in brackets):

| lesson | teaches | item charged as unknown | unlocked at |
|---|---|---|---|
| `les:n5-numeros-tempo-03` [54] "Pessoas e quantidade: たくさん" | `gram:gp-43` = たくさん | `vocab:1415870` 沢山 | `les:n5-comparacoes-01` [88] |
| `les:n5-comparacoes-01` [88] "より e ～ほうが" | ～のほうが | ほう (mislinked to 報, §3.1) | `les:n5-conectando-01` [112] |
| `les:n5-perguntas-01` [46] "ここ/そこ/あそこ/どこ" | `gp-9/10/11/39` | 其処 [68], 何処 [79]; only 此処 unlocks here | later |
| `les:n5-adjetivos-03` [82] "negativo dos adjetivos-い" | 〜くない | `vocab:1529520` 無い | `les:n5-comparacoes-03` [90] |
| `les:n4-obrigacao-01` [173] "が必要" | 必要 | kanji 必 [247], 要 [229] | far later |
| `les:n5-comparacoes-02` "一番" | 一番 | kanji 番 | `les:n3-intencao-02` [261] |
| `les:n5-convites-01` "一緒に" | 一緒に | kanji 緒 | `les:n3-relato-04` [311] |
| `les:n4-potencial-04` "なかなか〜ない" | なかなか | `vocab:1599420` 中々 | `les:n4-experiencia-02` |
| `les:n4-oracoes-relativas-07` "ように・ような" | ように | よう (mislinked to 用, §3.1) | `les:n4-transitividade-05` [162] |

A near-miss worth a single-line fix: `les:n4-obrigacao-01` [173] shows 「仕事が必要だ。」 and the kanji 仕
unlocks in `les:n4-obrigacao-02` [174], the *next* lesson.

### 3.4 Function words unlocked long after first use

19 units of load in my slice are する / いる / ある / ない:

| record | unlocked at | first needed |
|---|---|---|
| `vocab:1157170` 為る (する) | `les:n4-conectores-01` [206] | throughout N5 |
| `vocab:1577980` 居る (いる) | `les:n5-verbos-05` [65] | `les:n5-perguntas-01` [46] 「どこにいますか？」 |
| `vocab:1296400` 有る (ある) | `les:n5-verbos-05` [65] | `les:n5-perguntas-06` [< 65] |
| `vocab:1529520` 無い (ない) | `les:n5-comparacoes-03` [90] | `les:n5-adjetivos-03` [82], the negation lesson |

Ten slots in my slice carry する as their only or main overage. Deciding once whether these four are
"vocabulary" or grammar-carried auxiliaries retires them all.

---

## 4. Per-lesson verdicts and proposed replacements

Verdict codes: **REPLACE** (a compliant candidate exists, proposed below) · **KEEP/UNLOCK** (the link is
fine; fix an unlock or a level grade) · **AUTHOR** (nothing compliant exists in the bank) ·
**ACCEPT** (least-bad; keep with a written exemption).

### les:n3-intencao-01: Intenção e tentativa (n3, budget 2)

* `sent:tatoeba-4959` 「まず新しいサイトの概説をしようと思う。」 (n1, load 1/2, above): **ACCEPT**.
  Flagged only for level; the single new kanji is 概. Availability: `n3-you-to-omou` has real fits.
  * `sent:tatoeba-170918` 「左手で書いてみようとした。」 = "Eu tentei escrever com a mão esquerda." REAL, n5, load 0, `n3-uto-shita`.
  * `sent:tatoeba-160132` 「私はその子をなだめようとした。」 = "Eu tentei acalmar aquela criança." REAL, n4, load 0.
  * `sent:tatoeba-184891` 「外に出ようとしない。」 = "Ele não dá sinal de querer sair." REAL, n5, load 0, `n3-you-to-shinai`.
  Caveat: all three carry a *different* one of the lesson's three points than 4959 does (which is the
  と思う one). If the と思う slot must stay と思う, this is **ACCEPT** — 概 is one character over an
  otherwise clean sentence.

### les:n3-intencao-03: ように: finalidade, modo e comparação (n3, budget 2)

* `sent:tatoeba-83924` 「風邪引かないようにコートを着た。」 (n1, load 1/2, above): **KEEP/UNLOCK**. §3.2: the
  only thing above level is the kanji 邪, which the course never unlocks. Load 1 is inside budget.
* `sent:tatoeba-84519` 「父は私に改心するように言った。」 (n2, load 1/2, above): **KEEP/UNLOCK** (kanji 改), or
  **REPLACE** with `sent:tatoeba-84512` 「父は私に車を洗うように言いました。」 = "Meu pai me disse para lavar o
  carro." REAL, n4, load 0, `n3-you-ni-3`, same speaker/frame, polite register. This is a strict
  improvement and I recommend it.
  Also available at load 0: `sent:tatoeba-78711` 「来なさいと言わない限り来ないように。」 and
  `sent:tatoeba-85431` 「必要以上にお金を使わないようにしなさい。」

### les:n3-tempo-03: たとたん / たところ / てはじめて (n3, budget 2)

* `sent:tatoeba-187075` 「家に着いたとたん嵐になった。」 (n1, load 2/2, above): **REPLACE**. Graded n1 by the
  kanji 嵐 alone; load is exactly at budget. Three real `n3-ta-totan` sentences fit at load 2:
  * `sent:tatoeba-167241` 「私たちが出かけたとたん雨が降り始めた。」 = "Assim que saímos, começou a chover." REAL, n3, load 2 (降, 途端).
  * `sent:tatoeba-186986` 「家を出たとたんに大雨が降り出した。」 = "Assim que saí de casa, começou a chover forte." REAL, n3, load 2.
  * `sent:tatoeba-124657` 「電話を切ったとたんにまた鳴り出した。」 = "Assim que desliguei o telefone, ele começou a tocar de novo." REAL, n3, load 2 (鳴, 途端).
  All three keep the plain register and the abrupt-instant reading. 186986 is closest to the original
  frame (家 + weather turn) and is my first choice. Note `vocab:1610870` 途端 unlocks at
  `les:n3-deveres-05`, later than this lesson (§3.3), so all four candidates including the incumbent carry
  the same +1; that part is an unlock fix, not a selection fix.

### les:n4-conectores-01: それで e まず (n4, budget 2)

* `sent:gen-b01569f986d3` 「まず席に座りましょう」 (n3, load 2/2, above): **KEEP/UNLOCK** (§3.2: 席, 座 set
  the grade; load is at budget), or **REPLACE** with a real それで sentence if the まず slot can move.
* `sent:gen-375933b32579` 「電車が止まった　それで遅れた」 (n3, load 1/2, above): **KEEP/UNLOCK**, after
  rejecting the three candidates the gate prefers:
  * `sent:tatoeba-8687007` 「それでいい？」 = "Assim está bom?" REAL, n4, load 0.
  * `sent:tatoeba-3488181` 「それでいいよ。」 = "Assim está bom." REAL, n4, load 0.
  * `sent:tatoeba-8719362` 「それで十分？」 = "Assim é suficiente?" REAL, n4, load 0.
  All three use それで in its *"that's fine / with that"* sense, **not** the cause→consequence connector
  the lesson teaches. They fit the gate and fail the teaching point, so none of them may be adopted. The
  incumbent is one kanji (遅) over an otherwise clean sentence and stays.

### les:n4-conectores-07: ように: para que, pedir e torcer (n4, budget 2)

* `sent:gen-e41bdeadc5f1` 「明日晴れるように祈っています」 (n2, load 2/2, above): **KEEP/UNLOCK**. Load is at
  budget; 晴 and 祈 set the grade. It is the only ～ように祈る example the lesson has, and `gp-125` has no
  other sentence in the bank.
* `sent:tatoeba-80880` 「無理をしないように。」 (n3, load **0**/2, above): **KEEP**. Zero load, real, correct
  register. Pure §3.2 artifact (無 graded n3). Nothing to repair beyond the level grade.
  Clean alternatives exist at load 0 if variety is wanted: `sent:tatoeba-82971`
  「母は私に外出しないようにいった。」, `sent:tatoeba-84691` 「父はついてくるように私をせきたてた。」,
  `sent:tatoeba-4930` 「またいつか風のように走るんだ。」 (all REAL, n4, `gp-128`).

### les:n4-experiencia-01: Ficar e tornar-se (n4, budget 2)

* `sent:gen-b76ff6005aca` 「音を小さくしてください」 (n4, load 4/2): **REPLACE**.
  * `sent:gen-c5c1f79d1694` 「電気を明るくしてください」 = "Deixa a luz mais clara, por favor." generated, n4,
    load 2 (する, 下さる), `gp-80`. Same didactic shape (くする + てください), same register, half the load.
  * `sent:tatoeba-215746` 「シャワーにするわ。」 = "Vou tomar um banho." REAL, n4, load 1, `gp-80`. Natural
    にする, but casual わ and no くする.
  * `sent:tatoeba-213768` 「そう水くさくするな。」 = REAL, n4, load 1, `ku-suru`. **Do not use**: 水くさい is
    idiomatic ("ser distante com alguém"), so it teaches くする through a frozen idiom.
  Availability: `ku-suru` has 2 sentences at/below n4, 1 within budget. If the lesson must show
  くする specifically and cannot use the idiom, this is **AUTHOR**.
* `sent:gen-f1534c9baa43` 「部屋を明るくする」 (n3, load 3/2, above): **KEEP/UNLOCK**. After granting する
  (§3.4) the load is 2 = budget; 屋 and 部 set the n3 grade.

### les:n4-experiencia-04: De que é feito (n4, budget 2)

* `sent:gen-83a69c5a49f1` 「豆腐は大豆から作る」 (n1, load 2/2, above): **REPLACE** with `gen-9f8746831ba5`. Graded n1 by 腐/豆.
  * `sent:gen-ea821f307e43` 「ワインはぶどうから作ります」 = "O vinho é feito a partir da uva." generated, n4,
    load 0, `kara-tsukuru`. Caveat: the lesson already shows 「ワインはぶどうからできる」, so this duplicates
    the pair's content; use it only if the できる example moves.
  * `sent:gen-9f8746831ba5` 「このかばんは紙でできている」 — generated, n4, load 1, `gp-122`.
  Availability: `kara-tsukuru` has 4 at/below n4, all generated. **No real sentence exists for this point.**
* `sent:gen-585a1fd61d9e` 「日本酒は米から作る」 (n3, load 1/2, above): **KEEP**. Load 1 inside budget; 酒
  alone sets the grade, and 米 is unlocked by this very lesson. This is a good example; leave it.

### les:n4-experiencia-05: かかる, ごとに, おきに, 化する (n4, budget 2)

* `sent:gen-2d1dcf054c6b` 「この町は急に都市化した」 (n3, load 5/2, above): **AUTHOR**. `gp-126` (化する) has
  **0 sentences at or below n4** in the whole bank. After granting する and 化 the residual is still 3
  (急 — unlocked only at `les:n4-conectores-01`, plus 市, 都). An authored replacement must build 〜化する
  on already-known kanji.
  The lesson's other three points are richly served if the teacher prefers to drop 化する here:
  `oki-ni` 7 at level / 7 within budget, `gp-87` 5/5, `gp-70` 5/5, e.g. `sent:tatoeba-198139`
  「バスは１５分ごとにでます。」 (REAL, n4, load 0), `sent:tatoeba-11390339` 「手間がかかる作業です。」 (REAL,
  n4, load 0), `sent:tatoeba-235706` 「１日おきに買い物に行く。」 (REAL, n4, load 0).

### les:n4-forma-simples-02: じゃないか / って感じ (n4, budget 2)

* `sent:gen-238f14601cdc` 「もう春が来たって感じだ」 (n3, load 2/2, above): **KEEP/UNLOCK**. Load at budget;
  感 and 春 set the grade. It is the lesson's only って感じ example and `gp-129` has no alternative at level.
  (For the じゃないか half, real load-0 options exist: `sent:tatoeba-3507456` 「さあ飲もうじゃないか。」,
  `sent:tatoeba-10780343` 「車で来るんじゃないかな。」)

### les:n4-forma-simples-05: より, さ, 以外 (n4, budget 2)

* `sent:tatoeba-105626` 「彼は私より年少だ。」 (n3, load 3/2, above): **REPLACE**.
  * `sent:tatoeba-79991` 「目が口よりものを言う時がある。」 = "Às vezes os olhos falam mais do que a boca."
    REAL, n5, load 0, `yori`, plain register. Only real `yori` sentence that fits; slightly proverbial,
    but the より comparison is transparent.
  Availability: `yori` has 4 at/below n4, 1 within budget. 彼 is the blocker on the incumbent
  (`vocab:1483070` and kanji 彼 both unlock far later, at n3 positions), which is a §3.3/§3.4-shaped
  scheduling problem in its own right — 彼 is unavoidable N4 vocabulary.
* `sent:tatoeba-76098` 「思ったより安くあがった。」 (n4, load 3/2): **ACCEPT**: 思う and 上がる are ordinary N4 words whose records unlock later
  (`les:n4-condicionais-01`, `les:n4-keigo-03`). Re-ordering those two unlocks is cheaper than losing
  a natural より example.
* `sent:gen-2cb2ddc513fb` 「この山の高さに驚いた」 (n1, load 2/2, above): **KEEP/UNLOCK**. Load at budget;
  驚 sets the n1 grade. It is the lesson's only さ-nominalisation example on a concrete adjective; the two
  real `sa` alternatives (`sent:tatoeba-76460` 「ふふ・・・いわくがあるのさ、あそこには。」,
  `sent:tatoeba-144038` 「人生とはそんなものさ。」, both REAL n4 load 0) are the **sentence-final さ particle**,
  a different point entirely, and must not be swapped in.

### les:n4-keigo-02: 〜てすみません (n4, budget 2)

All three slots are §3.2 artifacts (one kanji each: 数, 遅, 晩) with load ≤ 2.

* `sent:tatoeba-236843` 「お手数をおかけしてすみません。」 (n3, load 2/2): **KEEP** (after granting する, load 1).
* `sent:tatoeba-126710` 「遅れてすみません。」 (n3, load 1/2): **KEEP**. Canonical, short, correct register.
* `sent:tatoeba-171272` 「今晩お会いできなくてすみません。」 (n3, load 1/2): **KEEP**.
  If variety is wanted, `sent:tatoeba-231454` 「こんなに長い間待たせてすみません。」 (REAL, n4, load 0) fits.

### les:n4-keigo-03: Sonkeigo I: いらっしゃる e なさる (n4, budget 2)

* `sent:tatoeba-85325` 「病気が全快なさるように。」 (n2, load 2/2, above): **REPLACE**. Graded n2 by 全/快;
  it is also a set well-wishing formula rather than a なさる-as-honorific-of-する demonstration.
  * `sent:tatoeba-3563138` 「そうなさるのもごもっともです。」 = "É perfeitamente compreensível que o senhor
    faça isso." REAL, n4, load 0, `nasaru`, polite register.
  * `sent:tatoeba-11582498` 「フランス語を話していらっしゃるのよ。」 = "Ela está falando francês, sabe." REAL,
    n4, load 0, `irassharu`.
  * `sent:tatoeba-125914` 「長くいらっしゃるつもりですか。」 = "O senhor pretende ficar por muito tempo?" REAL,
    n4, load 0, `irassharu`.
  Availability: `nasaru` 4 at level / 4 within budget, `irassharu` 5/5. This slot has the healthiest
  candidate pool in the slice; 3563138 is the direct replacement (same point, same register).

### les:n4-obrigacao-01: Precisar de algo: が必要 (n4, budget 2)

`ga-hitsuyou` has **0 sentences at or below n4** in the bank. All four displayed sentences are graded n3
**solely because 必 and 要 are graded n3** (§3.2) and unlock at `les:n3-tempo-01` [229] / `les:n3-causa-04`
[247], 56 and 74 lessons after this one [173].

* `sent:tatoeba-1006944` 「ナイフが必要だ。」 (load 2/2): **KEEP/UNLOCK**.
* `sent:tatoeba-187898` 「何が必要ですか。」 (load 2/2): **KEEP/UNLOCK**. This is the lesson's own stated
  objective sentence ("perguntar 'do que você precisa?' com 何が必要ですか").
* `sent:tatoeba-1046077` 「仕事が必要だ。」 (load 3/2): **KEEP/UNLOCK**. The one unit over budget is the
  kanji 仕, unlocked in `les:n4-obrigacao-02` — the very next lesson. Moving that single unlock one
  position earlier clears it.
* `sent:tatoeba-1272425` 「紙が必要だ。」 (load 3/2): **KEEP/UNLOCK** (紙) or drop as redundant with 1006944.

Recommended repair for the whole lesson: unlock kanji 必 and 要 here (the lesson teaches the word 必要),
and move 仕 one lesson earlier. No sentence should be replaced.

### les:n4-oracoes-relativas-07: ように・ような e 各 (n4, budget 2)

* `sent:tatoeba-78536` 「落ちないように注意しなさい。」 (n3, load 6/2, above): **ACCEPT** (see the verdict below).
  * `sent:tatoeba-81111` 「万事うまくいくように私が気をつけます。」 = "Eu vou cuidar para que tudo corra bem."
    REAL, n4, load 3 (私, 上手い, よう) — one over budget, but it is the *purpose* ように the lesson teaches,
    and one of its three units is the §3.1 よう mislink.
  * `sent:tatoeba-81309` 「毎日どのようにして学校へ行くのですか。」 = REAL, n4, load 2, fits. **Weak**: this is
    どのように ("de que modo"), not のように/ような comparison nor purpose ように; it teaches a third thing.
  Availability: `you-ni-you-na` 3 at/below n4, 1 within budget. Verdict: **ACCEPT 81111 at load 3** once
  the よう→様 link is fixed (load drops to 2 = budget), otherwise **AUTHOR**.
* `sent:tatoeba-83950` 「風邪をひきませんように。」 (n1, load 3/2, above): **KEEP/UNLOCK**. Fixing the よう
  mislink drops it to 2 = budget; 邪 and 風 set the n1 grade and 邪 is never unlocked.
* `sent:gen-344b2dbc4a13` 「各駅で電車が止まる」 (n2, load 2/2, above): **AUTHOR or ACCEPT**. `gp-90` (各)
  has **0 sentences at or below n4**, and the kanji 各 is never unlocked by any lesson. Load is at
  budget; the n2 grade comes from 各 itself. Since the lesson exists to teach 各, this is a
  **KEEP/UNLOCK** in substance: unlock kanji 各 here.
* `sent:gen-71eeebb22ba7` 「各階にトイレがあります」 (n2, load 2/2, above) — same verdict; the second unit is 階.

### les:n4-passiva-02: とされている (n4, budget 2)

`gp-137` has **0 sentences at or below n4**. Every candidate is n3+ and every one costs する (§3.4).

* `sent:tatoeba-112448` 「彼はその発明者とされている。」 (n3, load 2/2): **KEEP**. Best of the four: shortest,
  clearest, load at budget, and after granting する it is load 1.
* `sent:gen-552e95412e88` 「白い猫は幸せのしるしとされている」 (n3, load 3/2): **KEEP/UNLOCK** (幸, 猫; load 2
  after する). Good cultural example, matches the lesson's 文化/習慣 vocabulary aim.
* `sent:tatoeba-221717` 「この詩は彼の作とされている。」 (n1, load 3/2): **ACCEPT or drop**. 詩 sets the n1 grade
  and is not needed by the lesson; redundant with 112448 (both are attribution).
* `sent:tatoeba-994752` 「真夜中が幽霊のうろつく時間だとされている。」 (n1, load 3/2): **ACCEPT or drop**. 幽/霊
  are n1 and never unlocked; the sentence is also the longest and syntactically heaviest of the four for a
  point that is being introduced.

Recommendation: keep 112448 and 552e95412e88, drop the two n1 ones rather than replace them (nothing
compliant exists), and settle the する question from §3.4.

### les:n4-potencial-04: なかなか〜ない (n4, budget 2)

* `sent:tatoeba-10808987` 「最近は仕事がなかなかないんだよ。」 (n3, load 5/2, above): **ACCEPT** (see below).
  Availability: `nakanaka-nai` has 2 at/below n4, both within budget, both generated:
  * `sent:gen-9958167b70aa` 「バスがなかなか来ない」 = "O ônibus custa a chegar." generated, n4, load 1.
  * `sent:gen-b8b898fb9c68` 「子どもがなかなか起きない」 = "A criança custa a acordar." generated, n4, load 2.
  Both are **already displayed in this lesson**, so there is no unused compliant candidate:
  **no compliant replacement exists**. 10808987 is the lesson's only real, natural なかなか〜ない example and
  its overage is 最近 (a word this lesson's neighbour `les:n4-experiencia-01` unlocks) plus 仕/最/近.
  Verdict: **ACCEPT**, or **AUTHOR** a third generated example if the real one must go.
* `sent:gen-b347563062a8` 「夜なかなか眠れない」 (n3, load 3/2, above): **KEEP/UNLOCK**. Granting 中々 (the
  lesson's own point, §3.3) drops it to 2 = budget; 夜 and 眠 set the grade.

### les:n4-suposicao-08: かもしれない, はずです, はずがない, きっと (n4, budget 2)

* `sent:tatoeba-11692639` 「正しいはずがないよ。」 (n3, load **0**/2, above): **KEEP**. Zero load, real,
  correct point and register; flagged purely by §3.2 (正 graded n3). Nothing to repair.
  This lesson has 19 tier-1 candidates within budget if variety is ever wanted, e.g.
  `sent:tatoeba-81586` 「本気のはずがないわ。」 (REAL, n4, load 0).

### les:n5-adjetivos-03: Negativo dos adjetivos-い (n5, budget 1)

Two of the three displayed sentences do not teach the lesson's point. `gram:gp-24` is
*"adjetivos-い no negativo (〜くない)"*, but:

* `sent:tatoeba-158129` 「何も食べたくない。」 (n5, load 4/1): **REPLACE / mis-tagged**. This is 〜たくない,
  the negative of the たい desiderative, not the negative of an い-adjective. Tagging it `gp-24` teaches the
  wrong generalisation ("食べ is an adjective") at the exact moment the rule is introduced.
* `sent:tatoeba-5210` 「学校へ行きたくない。」 (n5, load 2/1): **same defect**, same verdict.
* `sent:tatoeba-135763` 「ちくしょう！わるくないなあ！」 (n5, load 2/1): **KEEP**. This is the only genuine
  い-adjective negative in the lesson (悪くない). Its overage is 悪い (`vocab:1151260`, unlocked at
  `les:n5-conectando-02`) plus ない (§3.4). Register note: ちくしょう is coarse ("Droga!"); acceptable in a
  colloquial example but worth a UI register flag.

Availability, exhaustive: `gp-24` has **3 sentences at or below n5 in the entire bank — the three already
shown — and 0 within budget.** A substring scan for 〜くない at n5 and load ≤ 2 returns only those three plus
`sent:tatoeba-173403` 「行きたくないのなら、行くな。」 (also 〜たくない). A scan for 〜くありません returns 0.

**Verdict: AUTHOR.** The i-adjective negative has no usable real example in the corpus. Two clean
authored sentences using only this lesson's own adjectives (暗い, 汚い, 危ない, 狭い, 少ない, 多い, 遅い,
痛い, 煩い, 忙しい, 明るい) would fix both the gate and the teaching point, e.g. on the shape
「この へやは あかるくない」. Separately, retag 158129 / 5210 / 173403 off `gp-24`.

### les:n5-adjetivos-07: のが好き / のが上手・下手 (n5, budget 1)

* `sent:tatoeba-10883885` 「本を読むのが好きです。」 (n4, load 4/1, above): **AUTHOR**.
* `sent:tatoeba-1128926` 「ハトにえさをやるのが好きです。」 (n4, load 2/1, above): **AUTHOR**.

Availability, exhaustive: `no-ga-suki` 0 at/below n5, `no-ga-jouzu` 0, `gp-23` 0; `gp-54` has exactly 1,
the generated 「ははは りょうりを つくるのが じょうずです」 already shown. A substring scan for のが好き at
n5 with load ≤ 1 returns **0**. The blocker on both incumbents is the kanji 好, which does not unlock until
`les:n4-kanji-exame-02` [217] even though 好き is core N5 vocabulary — that is the §3.3 pattern again and
the cheapest fix: unlock 好 here (or write it in kana as the sibling 「じょうずです」 example already does).

### les:n5-comparacoes-01: より e ～ほうが (n5, budget 1)

* `sent:gen-dc17b084b7de` 「バスより電車のほうが速い」 (n3, load 6/1, above): **AUTHOR**.
* `sent:gen-ead8371d038a` 「電車のほうがバスより速い」 (n3, load 6/1, above): **AUTHOR**.
* `sent:gen-326ea97de1a1` 「今日のほうが昨日より暑い」 (n3, load 3/1, above): **AUTHOR** (load 2 after the
  ほう→方 fix; 昨 and 暑 remain).

Availability, exhaustive: `yori-hou-ga` 0 at/below n5, `wa-yori-desu` 0, `gp-140` 1 (load 5),
`gp-47` 1 (load 6). **No compliant sentence exists for any of this lesson's four points.**

Two structural obstacles must be cleared before authoring, or the new sentences will be flagged too:
1. ほう is linked to 報 (§3.1) in all 39 ～ほうが sentences; the correct record `vocab:1516930` 方 does not
   unlock until `les:n3-deveres-06` [272]. This lesson [88] must unlock 方 itself.
2. The obvious minimal-pair vocabulary (バス, 電車, 車) all carry kanji or records that unlock later. An
   authored pair should be built from this lesson's own adjectives (高い, 近い, 遠い, 長い, 強い, 冷たい)
   over already-known nouns.

### les:n5-comparacoes-02: O superlativo: 一番 e ～の中で (n5, budget 1)

All four slots are flagged for level, and three of them have load ≤ 1 already.

* `sent:tatoeba-203016` 「チェスを一番どうですか。」 (n3, load 1/1): **DROP, do not replace**. The Japanese is
  defective: 「チェスを一番どうですか」 is not a well-formed superlative sentence, and the pt-BR
  "Que tal uma partida de xadrez?" is a translation of a *different* sentence (「チェスをどうですか」).
  It teaches nothing about 一番 and should not be shown at all.
* `sent:tatoeba-223501` 「このテレビがすべてのうちで一番よい。」 (n3, load 1/1): **KEEP/UNLOCK** (kanji 番).
  Good ～のうちで…一番 model.
* `sent:gen-c94b958f1ed1` 「スポーツの中でサッカーが一番人気です」 (n3, load 1/1): **KEEP/UNLOCK** (kanji 番).
* `sent:gen-f7cec4b420ec` 「くだものの中でりんごが一番好きです」 (n3, load 2/1): **KEEP/UNLOCK** (kanji 番 + 好,
  §3.3 again).

Availability: `ichiban`, `gp-46` and `no-naka-de-a-ga-ichiban` all have **0 sentences at or below n5**; a
substring scan for 一番 at n5 load ≤ 1 returns 0. Unlocking the kanji 番 in the lesson named
*"O superlativo: 一番"* clears three of the four; the fourth (203016) should be removed on quality grounds.

### les:n5-comparacoes-04: ～がほしい (n5, budget 1)

* `sent:tatoeba-149136` 「車がほしいですか。」 (n5, load 2/1): **KEEP/UNLOCK**. The two units are 欲しい (the
  lesson's own point, unlocked at `les:n5-convites-06`) and the kanji 車. Candidates considered:
  * `sent:tatoeba-13126479` 「りんごがほしいですか？」 = "Você quer maçã?" REAL, n5, load 1, `ga-hoshii`,
    polite, identical frame. Caveat: near-duplicate of the already-shown
    `sent:tatoeba-13126478` 「りんごがほしい?」 — adopting it makes the lesson show the same noun twice.
  * `sent:tatoeba-11045064` 「もっと本気さがほしい。」 — REAL, n5, load 2, plain. Abstract noun; weaker for a
    first ほしい lesson.
  Availability: `ga-hoshii` 7 at level / 4 within budget, but three of the four fits are already shown.
  Unlocking 欲しい in the lesson that teaches ～がほしい drops 149136 to load 1 and keeps the noun variety,
  which beats swapping in a duplicate noun.

### les:n5-comparacoes-05: ～たい (n5, budget 1)

* `sent:tatoeba-84964` 「婦長と話したいのですが。」 (n3, load 2/1, above): **AUTHOR**. Availability: `tai` has
  1 sentence at/below n5 within budget and it is the other one already shown
  (`sent:tatoeba-83633` 「聞きたい？」). 婦 is never unlocked and 話す unlocks later. The lesson's own verb
  list (上る, 寝る, 脱ぐ, 並ぶ, 並べる, 鳴く) is the right source for an authored second example.

### les:n5-conectando-01: から e ので (n5, budget 1)

* `sent:tatoeba-82538` 「忙しいので行けないの。」 (n3, load 1/1, above): **KEEP**. Load is inside budget; the
  n3 grade comes from the single kanji 忙. `node` has **0** other sentences at or below n5, so there is
  nothing to replace it with and nothing wrong with it.

### les:n5-convites-01: 一緒に e 〜ませんか (n5, budget 1)

* `sent:gen-24bb23e4256e` 「ちょっと休みませんか」 (n5, load 2/1): **REPLACE**, and it trades generated for real:
  * `sent:tatoeba-172871` 「今からドライブに行きませんか。」 = "Que tal a gente dar uma volta de carro agora?"
    REAL, n5, **load 0**, `masen-ka`, polite-invitation register, matches the lesson objective exactly.
    This is the cleanest single win in the slice.
* `sent:tatoeba-190532` 「一緒に行かない？」 (n3, load 1/1): **KEEP/UNLOCK**.
* `sent:tatoeba-190548` 「一緒に行きます。」 (n3, load 1/1): **KEEP/UNLOCK**.
* `sent:tatoeba-774809` 「一緒に来るの？」 (n3, load 1/1): **KEEP/UNLOCK**.
  All three are §3.2 pure: every vocab and every other kanji is n5; only 緒 (graded n3, unlocked at
  `les:n3-relato-04` [311]) raises the grade. `issho-ni` has 0 other sentences at or below n5, so replacing
  them is impossible as well as unnecessary. Unlock 緒 here, or render 一緒 with furigana.

### les:n5-numeros-tempo-03: Pessoas e quantidade: たくさん (n5, budget 1)

* `sent:tatoeba-122326` 「日本語を話せるアメリカ人がたくさんいる。」 (n5, load 6/1): **AUTHOR**. Also carries a
  potential-form relative clause (話せる) far beyond this lesson.
* `sent:tatoeba-112055` 「彼はたくさん食べる。」 (n3, load 5/1, above): **AUTHOR**.

Availability, exhaustive: `gp-43` has **2 sentences at or below n5, 0 within budget** — the two already
shown, plus `sent:tatoeba-81631` 「本をたくさん買ったんだ。」 at load 5. A substring scan for たくさん at n5
load ≤ 1 returns **0**.

Root cause first (§3.3): this lesson [54] teaches たくさん as `gram:gp-43`, but `vocab:1415870` 沢山 only
unlocks at `les:n5-comparacoes-01` [88], so *every* たくさん example is permanently +1 over budget. Move
that unlock here and 112055 drops to 4, 122326 to 4 — still over, so an authored example on this lesson's
own nouns (人, 子供, 生徒) remains necessary.

### les:n5-particulas-lugar-01: あります e います (n5, budget 1)

* `sent:tatoeba-80128` 「木の下にベンチがあります。」 (n5, load 3/1): **REPLACE**.
  * `sent:tatoeba-122353` 「日本語のガイドがありますか。」 = "Tem guia em japonês?" REAL, n5, load 1
    (kanji 語), `ga-arimasu`, polite. Best fit: natural, useful, correct point.
  * `sent:tatoeba-198311` 「ハウスダストにアレルギーがあります。」 REAL, n5, load 0. Caveat: the pt-BR reads
    "**Ele** tem alergia a poeira doméstica" although the Japanese has no subject — fix the translation to
    "Tenho alergia a poeira doméstica" / "Tem alergia a poeira doméstica" before adopting.
  * `sent:tatoeba-123182` 「二、三デメリットがありますね。」 REAL, n5, load 1. Weaker: デメリット is business
    jargon and the sentence is not about physical location.
* `sent:tatoeba-229125` 「いすの上にねこがいます。」 (n5, load 2/1): **REPLACE**.
  * `sent:tatoeba-11561754` 「ポーチにスカンクがいます。」 = "Tem um cangambá na varanda." REAL, n5, **load 0**,
    `ga-imasu`, polite, animate subject in a place. Exact match for the teaching point.
  Availability: `ga-imasu` 5 at level, only this 1 within budget. Note the incumbent's overage is 上 and
  猫 — both are excellent N5 words whose records unlock later; **KEEP/UNLOCK** is defensible here too, and
  「いすの上にねこがいます」 is the better beginner picture.
* `sent:tatoeba-6828196` 「学校に人がいる。」 (n5, load 2/1): **DROP from this lesson**. It is tagged `gp-13`
  (casual いる) while this lesson teaches the polite います, and it is displayed again in
  `les:n5-particulas-lugar-02`, where it belongs. Removing it here fixes the register mismatch and the
  duplicate display at once; no replacement is needed, since the lesson keeps three other examples.

### les:n5-particulas-lugar-02: ある e いる casual (n5, budget 1)

* `sent:tatoeba-6828196` 「学校に人がいる。」 (n5, load 2/1): **KEEP/UNLOCK** (kanji 学, 校). Right lesson for
  this sentence.
* `sent:tatoeba-78451` 「嵐のきざしがある。」 (n1, load 1/1): **KEEP**. Load inside budget; 嵐 (never unlocked)
  sets the n1 grade. `gp-12` has no alternative at level.
  **Warning:** the top automated candidate for this lesson, `sent:tatoeba-3576174` 「さあ、ピザがいる人ー！」
  (load 0, real, tagged `gp-13`), must **not** be used , see §5.

### les:n5-particulas-lugar-06: 〜に行く (n5, budget 1)

* `sent:tatoeba-125175` 「天気がよければハイキングに行くのだが。」 (n5, load 4/1): **ACCEPT** (see below). It also carries
  a ば-conditional and a counterfactual のだが far outside an N5 に行く lesson.
  * `sent:tatoeba-1510008` 「パンを買いにいく。」 = "Vou comprar pão." REAL, n5, load 2 (kanji 買 + パン),
    `gp-28`. One over budget but the cleanest real 〜に行く in the bank.
  * `sent:gen-d82f2dd80e15` 「友だちに会いに行く」 — generated, n5, load 3.
  Availability: `gp-28` 3 at level / 0 within budget; `ni-iku` 3 / 0. **No sentence fits budget 1.**
  Verdict: **ACCEPT 1510008 at load 2** (a strict improvement from 4, real instead of generated, and both
  extra units are this lesson's neighbours), or **AUTHOR** on kana-only vocabulary.
* `sent:gen-59bccb81087b` 「ひるごはんを食べにいきます」 (n5, load 2/1): **KEEP/UNLOCK**. One unit is the kanji
  食 of a word already known; the other is 昼 (`vocab:1426250`, unlocked in `les:n5-convites-01`).

### les:n5-particulas-lugar-07: あげる, くれる, もらう (n5, budget 1)

* `sent:tatoeba-145739` 「信じてくれる？」 (n3, load 2/1, above): **KEEP/UNLOCK, and fix the link first**.
  The 2 units are the kanji 信 and `vocab:1514960` **暮れる ("escurecer")** — the §3.1 mislink. In the one
  lesson in the entire course that teaches the giving verb くれる, the token points at "anoitecer". The
  correct record `vocab:1269130` 呉れる exists, is graded n1, and is unlocked by no lesson at all.
  Fix: link to 呉れる, regrade it to n5/n4, and unlock it here.
* `sent:tatoeba-11059892` 「してあげる。」 (n4, load 1/1, above): **KEEP**. Load inside budget; the only unit
  is する (§3.4).
  Availability: `gp-55`, `gp-56` and `gp-57` have **0 sentences at or below n5** each. Nothing to replace
  either slot with; this lesson is entirely blocked on the くれる record, not on selection.

### les:n5-passado-02: じゃなかった (n5, budget 1)

* `sent:tatoeba-10515932` 「聞くんじゃなかった。」 (n5, load 2/1): **AUTHOR** (and keep this one alongside).
  Units are ない (§3.4) and
  the kanji 聞. Availability: `gp-34` has 1 sentence at/below n5 — this one — and 0 within budget.
  Nothing to replace it with.
  Teaching-point note: 「聞くんじゃなかった」 is the regret construction *"eu não devia ter perguntado"*,
  built on んじゃなかった, whereas the lesson objective is the copula past negative on **nouns and
  な-adjectives** ("B じゃなかった"). The lesson's own objective explicitly says じゃなかった does not apply to
  verbs, and this example applies it to a verb. Recommend **AUTHOR** a noun example
  (e.g. on this lesson's 土曜日 / 年) alongside it.

### les:n5-passado-04: a partícula なあ (n5, budget 1)

* `sent:tatoeba-229334` 「いい天気だなあ。」 (n5, load 3/1): **KEEP/UNLOCK**; candidates considered:
  * `sent:tatoeba-226045` 「キツイなあ。」 = "Nossa, que duro..." REAL, n5, **load 0**, `naa`, plain.
    Caveat: near-synonym of the already-shown 「タフだなあ。」; adopting both gives the lesson two
    "that's tough" examples.
  * `sent:tatoeba-1202184` 「車があればなあ。」 = "Ah, se eu tivesse um carro..." REAL, n5, load 1 (kanji 車).
    Adds the wistful counterfactual なあ, which is a genuinely different and useful use. Caveat: carries a
    ば-conditional the learner has not met.
  Availability: `naa` 5 at level / 4 within budget — one of the healthier pools. The incumbent's overage is
  entirely 天気 (`vocab:1438690`) plus its two kanji, all unlocked in this same topic block, and
  「いい天気だなあ」 is the better first example of an emotive なあ than either candidate, so the unlock fix
  wins. Add `sent:tatoeba-1202184` as a *second* example if the wistful counterfactual なあ is wanted.
* `sent:tatoeba-77673` 「冷たいなあ。」 (n3, load 2/1, above): **KEEP/UNLOCK**. Units are 冷たい
  (`vocab:1415000`, unlocked at `les:n5-comparacoes-01`) and the kanji 冷.
  Translation note for the teacher: the pt-BR is "Que frieza..." (the metaphorical reading, about a
  person being cold). 冷たいなあ is ambiguous out of context; if the lesson wants the literal reading,
  the translation should say so, and if it wants the metaphor, the gloss should flag it.

### les:n5-perguntas-01: ここ・そこ・あそこ・どこ (n5, budget 1)

The lesson unlocks only 此処 (ここ). 其処 unlocks 22 lessons later, 何処 33 lessons later, and the ここ
tokens themselves point at 九 (§3.1). All four slots follow from that.

* `sent:tatoeba-141432` 「千人もの人がそこにいた。」 (n5, load 6/1): **REPLACE**. Also carries 〜もの
  ("nada menos que"), an emphatic counter construction far above this lesson.
  Availability: `gp-10` (そこ) has 3 sentences at/below n5, **0 within budget** (next best is load 5).
  Verdict: **AUTHOR** a そこ example on kana-only vocabulary, after unlocking 其処 here.
* `sent:tatoeba-5055` 「ここから遠いの？」 (n4, load 3/1, above): **KEEP/UNLOCK**. Two of the three units
  dissolve: 九 is the §3.1 ここ mislink, and 遠い (`vocab:1177800`) is unlocked at `les:n5-comparacoes-01`.
  `gp-9` has 2 sentences at/below n5 and 0 within budget, so there is nothing better.
* `sent:tatoeba-5319` 「どこにいますか？」 (n5, load 2/1): **KEEP/UNLOCK**. Both units are the lesson's own
  content: 何処 (the word being taught) and いる (§3.4). `gp-39` has exactly 1 sentence in the bank — this
  one. Nothing to replace it with, and nothing wrong with it.
* `sent:tatoeba-5933519` 「あそこを見て。」 (n5, load 2/1): **KEEP/UNLOCK**. Its whole overage is 見る/見,
  taught in `les:n5-verbos-01`, and it is the better *pointing* example.
  `sent:tatoeba-234396` 「あそこのカウンターです。」 = "É naquele balcão ali." REAL, n5, **load 0**, `gp-11`,
  polite — is the only load-0 demonstrative available to this lesson and is worth adding as a *second*
  あそこ example rather than as a replacement.

### les:n5-perguntas-02: この・その・あの + substantivo (n5, budget 1)

* `sent:tatoeba-80099` 「木はその実で分かる。」 (n3, load 6/1, above): **AUTHOR**. It is also a proverb
  ("a árvore se reconhece pelo fruto"), i.e. a frozen idiom used to introduce a basic demonstrative,
  and its その is linked to 園 "jardim" (§3.1).
* `sent:tatoeba-74036` 「この新聞はロハだ。」 (n4, load 4/1, above): **AUTHOR**. ロハ is dated slang for
  "de graça" (from 只 split into ロ+ハ); it is a poor first この example and the pt-BR "Este jornal é de
  graça" gives no hint that the register is archaic-jocular.

Availability, exhaustive: `gp-14`, `gp-15` and `gp-16` have **0 sentences at or below n5** each. A
substring scan for この at n5 with load ≤ 1 returns exactly one sentence, and it is
`sent:tatoeba-234396` 「あそこのカウンターです。」 — which contains あそこ, not この.

**This lesson has no usable material in the bank and needs two authored sentences.** Two blockers to clear
first: the record **其の (その) does not exist** (§3.1), and `vocab:1582920` 此の unlocks at
`les:n5-numeros-tempo-09`, later than this lesson.

### les:n5-perguntas-05: どんな・どうやって (n5, budget 1)

Every どう token in the course is linked to 動 "movimento" (§3.1); every どんな costs a unit because
`vocab:1009330` どんな unlocks at `les:n5-comparacoes-02`, later.

* `sent:tatoeba-201153` 「どうやって学校に来たの？」 (n5, load 6/1): **ACCEPT** (see below).
  * `sent:tatoeba-4561431` 「どうやってできましたか。」 = "Como isso foi feito?" REAL, n5, load 3, polite.
  * `sent:tatoeba-201147` 「どうやって時間をつぶそう？」 — REAL, n5, load 5. Worse.
  Availability: `douyatte` 4 at level, **0 within budget**. Best available is load 3, of which 2 units are
  the どう mislink and 遣る. Verdict: **ACCEPT 4561431** as a strict improvement (6 → 3), or **AUTHOR**.
* `sent:tatoeba-199382` 「どんな天気ですか。」 (n5, load 4/1): **REPLACE**.
  * `sent:tatoeba-199477` 「どんなワインがありますか。」 = "Que tipos de vinho vocês têm?" REAL, n5, load 2,
    `donna`, polite. Both units are どんな (the lesson's own point) and ある (§3.4), so after §3.3/§3.4 it
    is load 0. **Recommended.**
* `sent:tatoeba-199569` 「どんなテストですか。」 (n5, load 2/1): **KEEP/UNLOCK**. Units are どんな (own point)
  and テスト.
* `sent:tatoeba-9611533` 「どうやってやるの？」 (n5, load 2/1): **KEEP/UNLOCK**. Units are the どう mislink and
  遣る; both dissolve under §3.1/§3.3.

### les:n5-perguntas-06: なにか・なにも e か〜か (n5, budget 1)

* `sent:gen-532623825322` 「かばんの中に何かありますか」 (n5, load 4/1): **AUTHOR**, or **KEEP/UNLOCK**: the
  4 units are ある (§3.4), 何 (`vocab:1577100`, unlocked at `les:n5-comparacoes-02` — the lesson teaching
  なにか does not unlock 何) and the kanji 中/何. Writing なにか in kana, as the lesson title does, removes
  two of them.
* `sent:gen-54dd1d1ebf25` 「何か食べたいです」 (n5, load 4/1) — same verdict. Note it also uses 〜たい, taught
  later in `les:n5-comparacoes-05`.
* `sent:tatoeba-201028` 「どこかに出かけるの？」 (n5, load 3/1): **KEEP/UNLOCK**. Units are 何処, 出かける, 出.
* `sent:gen-c737b9f8b9da` 「コーヒーか おちゃか どちらが いいですか」 (n5, load 2/1): **KEEP/UNLOCK**. Units are
  何方 (どちら) and いい, both function-shaped and both unlocked later.

Availability, exhaustive: `gp-48` 2 at level / 0 within budget (both already shown), `gp-49` 1 / 0 (shown),
`ka-ka` 2 / 0 (one shown, the other `sent:gen-d338f63d2a25` at load 5). **No compliant replacement exists
for any of the four slots**; the whole lesson is gated by kana-vs-kanji spelling of 何 and by the unlock
positions of 何 / 何処 / 何方.

### les:n5-te-form-03: 〜ています / 〜てある (n5, budget 1)

* `sent:gen-47206ec62227` 「冷蔵庫にビールが冷やしてある」 (n2, load 4/1, above): **AUTHOR or drop**.
  冷蔵庫 (`vocab:1557110`) plus its three kanji are the whole overage; it is also an alcohol reference in a
  beginner lesson, which the teacher may want to weigh.
* `sent:gen-6d412e5af5e1` 「ノートに名前が書いてある」 (n5, load 2/1): **KEEP/UNLOCK**. Both units are kanji
  (名, 書) of known words. Best てある example the lesson has.
* `sent:tatoeba-85522` 「鼻がつまっています。」 (n2, load 2/1, above): **KEEP/UNLOCK** (鼻 is unlocked in
  `les:n5-te-form-04`, the next lesson). Already displayed in `les:n5-te-form-01` and `les:n5-te-form-02`
  as well — a triple display of the same sentence across three consecutive lessons, which is worth
  breaking up on variety grounds alone.
* `sent:gen-8bc9ce5df658` 「ドアに鍵がかけてある」 (n1, load 1/1): **KEEP**. Load inside budget; graded n1 by
  the single kanji 鍵 (never unlocked, §3.2) although every vocab and the grammar are n5.

Availability: `te-aru` 1 at/below n5 (the one shown, load 2), `te-iru` 0. Nothing to select.

### les:n5-te-form-04: orações relativas (n5, budget 1)

* `sent:tatoeba-5107` 「疲れているんだ。」 (n3, load 1/1, above): **KEEP/UNLOCK** (kanji 疲), **but it does not
  teach the lesson's point**: it carries no relative clause at all, and its `grammar` array is empty. It is
  the lesson's only displayed sentence. `gp-36` and `gp-37` have **0 sentences at or below n5**.
  Verdict: **AUTHOR** at least one real relative-clause example (verb directly before a noun) on this
  lesson's own vocabulary (橋, 箱, 番号, パーティー).

### les:n5-te-form-06: proibir e 〜ないで (n5, budget 1)

* `sent:gen-f1c08a8693dc` 「電気を消さないで寝ました」 (n3, load 3/1, above): **AUTHOR** (see below).
  * `sent:tatoeba-174758` 「言っちゃいけないんだけど。」 = "É que eu não posso contar..." REAL, n5, load 1
    (kanji 言), `cha-ikenai-ja-ikenai`. Carries a different one of the lesson's three points (the
    ちゃいけない prohibition rather than ないで), so it complements rather than replaces the ないで slot.
  Availability: `naide` 1 at/below n5 (already shown), `naide-kudasai` **0**, `cha-ikenai-ja-ikenai` 1.
  Verdict for the ないで slot itself: **AUTHOR**. Note the lesson's third point (〜ないでください) has no
  example at all in the bank at any level within reach.
* `sent:tatoeba-125387` 「諦めないで。」 (n1, load 1/1, above): **KEEP**. Load inside budget; graded n1 by 諦
  alone (never unlocked). Natural, short, correct register. It is also displayed in
  `les:n5-particulas-lugar-03`; the duplicate is worth resolving.

### les:n5-te-form-07: obrigação (n5, budget 1)

* `sent:tatoeba-2431512` 「何で学校に行かないといけないの？」 (n5, load 2/1): **KEEP/UNLOCK**. Both units are
  kanji (何, 校) of words the learner already knows.
  Availability: `naito-ikenai` 2 at level / 1 within budget, and that one
  (`sent:tatoeba-10510923` 「行かないといけないの？」, load 0) is already shown.
  `nakute-wa-ikenai` and `nakute-wa-naranai` have **0 sentences each** — two of the lesson's three
  objectives have no example anywhere in the corpus. That is an authoring gap worth escalating.

### les:n5-verbos-01: ます e verbos ichidan (n5, budget 1)

* `sent:gen-e8f19f968193` 「あさ 六時に おきる」 (n5, load 5/1): **AUTHOR**. Five units for a six-word kana
  sentence: 朝, 六, 時 as vocab plus 六 and 時 as kanji, none unlocked yet. Writing the time in kana
  (「あさ ろくじに おきる」) removes the two kanji at zero cost, since the sentence is already kana-first.
* `sent:gen-97a9a63e32d1` 「まいにち テレビを 見る」 (n5, load 2/1): **KEEP/UNLOCK**. Units are テレビ and
  毎日, both ordinary N5 words unlocked later.
* `sent:tatoeba-11795596` 「8人孫がいます。」 (n2, load 2/1, above): **REPLACE**. Graded n2 by 孫; also
  displayed in `les:n5-verbos-05`.
  * `sent:tatoeba-11561754` 「ポーチにスカンクがいます。」 — REAL, n5, load 1 (いる only), `ga-imasu`/`gp-8`,
    polite. **Recommended.**
  * `sent:tatoeba-198311` 「ハウスダストにアレルギーがあります。」 — REAL, n5, load 1 (ある only). Fix the
    pt-BR subject first (see `les:n5-particulas-lugar-01`).
  Availability: `gp-8` 5 at level / 3 within budget.
  Caveat on both: they teach the ある/います existence pattern, whereas this lesson's point is the ます
  ending on ichidan verbs. `gp-6` itself has 2 sentences at level and **0** within budget, both already
  shown, so a fully on-point compliant example does not exist and would have to be authored from the
  lesson's own 16 ichidan verbs.

### les:n5-verbos-02: verbos godan e a partícula を (n5, budget 1)

* `sent:gen-867d5c2e8dc3` 「電気を消した」 (n3, load 4/1, above): **AUTHOR**. Also uses the past た form,
  which this lesson (dictionary form + を) has not introduced. Also displayed in
  `les:n4-transitividade-01`, where it belongs.
* `sent:tatoeba-174533` 「戸を閉めろ。」 (n2, load 3/1, above): **AUTHOR or drop**. The imperative 閉めろ is a
  blunt command form far outside N5 and jars against the polite register the topic is building.
* `sent:gen-66857872d764` 「ともだちと コーヒーを のむ」 (n5, load 2/1): **KEEP/UNLOCK**. Units are 飲む and
  友達, both unlocked later. Good kana-first example of を.
* `sent:gen-a6201c731653` 「あした 本を かう」 (n5, load 2/1): **KEEP/UNLOCK**. Units are 本 and 明日.

Availability: `gp-7` 2 at level / 0 within budget (both shown); `o-wo` 1 / 0, and that one is
`sent:tatoeba-173912` 「口を出すな。」 (REAL, n5, load 2) — an idiom meaning "não se meta", plus a な
prohibition, so **not** usable. **No compliant replacement exists for either of the two AUTHOR slots.**
The lesson's own verb list (押す, 吸う, 書く, 消す, 切る, 洗う, 貸す, 置く, 買う, 売る, 返す, 言う, 歌う, 聞く)
is the right source.

### les:n5-verbos-06: 〜をください e números (n5, budget 1)

* `sent:tatoeba-143718` 「水をください。」 (n4, load 3/1, above): **AUTHOR**. `o-kudasai` has **0 sentences at
  or below n5**, and a substring scan for ください at n5 with load ≤ 2 returns **0** across the whole bank.
  The three units are 下さる, 水 (vocab) and 水 (kanji). Since the lesson's own unlocks are 会う, 千 and ゼロ,
  an authored request on an already-known katakana noun (e.g. コーヒー) is the clean fix; it is also the
  lesson's only displayed sentence, so it currently has no compliant example at all.

---

## 5. Candidates the automation ranks high that must NOT be used

Anything re-running this selection automatically will surface these; they are wrong for reasons the
gate cannot see.

1. **`sent:tatoeba-3576174` 「さあ、ピザがいる人ー！」** — load 0, real, tagged `gram:gp-13` (existential いる),
   and it is the top-ranked candidate for both ある/いる lessons in this slice. The いる here is **要る**
   ("precisar/querer"), and the record's own gloss says so: *"precisar, querer (要る)"*. The token is
   nevertheless linked to `vocab:1577980` 居る and the sentence is tagged as an existence example. Used in
   `les:n5-particulas-lugar-01/02` it would teach the exact opposite of the lesson.
2. **`sent:tatoeba-81309` 「毎日どのようにして学校へ行くのですか。」** — the only `you-ni-you-na` sentence that
   fits `les:n4-oracoes-relativas-07`, but どのように is "de que modo", not the のように comparison or the
   purpose ように the lesson teaches.
3. **`sent:tatoeba-213768` 「そう水くさくするな。」**: the only real `ku-suru` fit for `les:n4-experiencia-01`;
   水くさい is a frozen idiom, so it teaches くする through a word whose parts mean nothing here.
4. **`sent:tatoeba-173912` 「口を出すな。」**: the only real `o-wo` fit for `les:n5-verbos-02`; idiomatic
   ("não se meta") plus an unlearned な prohibition.
5. **`sent:tatoeba-76460` / `sent:tatoeba-144038`** (`sa`) — load-0 fits for `les:n4-forma-simples-05`, but
   they are the sentence-final assertive さ particle, not the さ nominaliser the lesson teaches.
6. **`sent:tatoeba-8687007` / `3488181` / `8719362`** (`gp-134`) — load-0 fits for `les:n4-conectores-01`,
   but それで there means "with that / that's fine", not the causal connector.
7. **`sent:tatoeba-203016` 「チェスを一番どうですか。」** — currently *displayed* in `les:n5-comparacoes-02`.
   The Japanese is not well-formed and the pt-BR translates a different sentence. Remove rather than reuse.

---

## 6. Verdict per slot (all 99)

`R` = REPLACE (a named compliant candidate, adopt it) · `K` = KEEP/UNLOCK (sentence is fine; fix an unlock,
a token link or a level grade) · `A` = AUTHOR (nothing compliant exists in the bank) ·
`X` = ACCEPT (least-bad; keep, or take the strict improvement, with a written exemption) ·
`D` = DROP (remove the display; no replacement warranted)

| # | lesson | sentence | load/budget | verdict | action |
|---|---|---|---|---|---|
| 1 | les:n3-intencao-01 | tatoeba-4959 | 1/2 | X | 概 is one character over an otherwise clean と思う example |
| 2 | les:n3-intencao-03 | tatoeba-83924 | 1/2 | K | kanji 邪, never unlocked |
| 3 | les:n3-intencao-03 | tatoeba-84519 | 1/2 | **R** | to `sent:tatoeba-84512` (REAL, n4, load 0) |
| 4 | les:n3-tempo-03 | tatoeba-187075 | 2/2 | **R** | to `sent:tatoeba-186986` (REAL, n3, load 2) |
| 5 | les:n4-conectores-01 | gen-b01569f986d3 | 2/2 | K | 席, 座 set the grade; load at budget |
| 6 | les:n4-conectores-01 | gen-375933b32579 | 1/2 | K | every gate-fitting candidate carries the wrong それで sense |
| 7 | les:n4-conectores-07 | gen-e41bdeadc5f1 | 2/2 | K | only ように祈る example in the bank |
| 8 | les:n4-conectores-07 | tatoeba-80880 | 0/2 | K | zero load; pure level artifact |
| 9 | les:n4-experiencia-01 | gen-b76ff6005aca | 4/2 | **R** | to `sent:gen-c5c1f79d1694` (load 2) |
| 10 | les:n4-experiencia-01 | gen-f1534c9baa43 | 3/2 | K | load 2 after granting する |
| 11 | les:n4-experiencia-04 | gen-83a69c5a49f1 | 2/2 | **R** | to `sent:gen-9f8746831ba5` (load 1) |
| 12 | les:n4-experiencia-04 | gen-585a1fd61d9e | 1/2 | K | inside budget; 酒 sets the grade |
| 13 | les:n4-experiencia-05 | gen-2d1dcf054c6b | 5/2 | **A** | `gp-126` has 0 sentences at or below n4 |
| 14 | les:n4-forma-simples-02 | gen-238f14601cdc | 2/2 | K | only って感じ example; load at budget |
| 15 | les:n4-forma-simples-05 | tatoeba-105626 | 3/2 | **R** | to `sent:tatoeba-79991` (REAL, n5, load 0) |
| 16 | les:n4-forma-simples-05 | tatoeba-76098 | 3/2 | X | 思う / 上がる unlock later; re-ordering beats losing it |
| 17 | les:n4-forma-simples-05 | gen-2cb2ddc513fb | 2/2 | K | 驚 sets n1; the two `sa` fits are a different さ |
| 18 | les:n4-keigo-02 | tatoeba-236843 | 2/2 | K | 数 plus する |
| 19 | les:n4-keigo-02 | tatoeba-126710 | 1/2 | K | canonical; 遅 sets the grade |
| 20 | les:n4-keigo-02 | tatoeba-171272 | 1/2 | K | 晩 sets the grade |
| 21 | les:n4-keigo-03 | tatoeba-85325 | 2/2 | **R** | to `sent:tatoeba-3563138` (REAL, n4, load 0) |
| 22 | les:n4-obrigacao-01 | tatoeba-1046077 | 3/2 | K | 仕 unlocks in the very next lesson |
| 23 | les:n4-obrigacao-01 | tatoeba-1272425 | 3/2 | K | 必 / 要 plus 紙 |
| 24 | les:n4-obrigacao-01 | tatoeba-1006944 | 2/2 | K | unlock 必 and 要 here |
| 25 | les:n4-obrigacao-01 | tatoeba-187898 | 2/2 | K | the lesson's own objective sentence |
| 26 | les:n4-oracoes-relativas-07 | tatoeba-78536 | 6/2 | X | to `sent:tatoeba-81111` (load 3, load 2 after the よう fix) |
| 27 | les:n4-oracoes-relativas-07 | tatoeba-83950 | 3/2 | K | load 2 after the よう to 様 fix |
| 28 | les:n4-oracoes-relativas-07 | gen-344b2dbc4a13 | 2/2 | K | unlock kanji 各 here; `gp-90` has 0 alternatives |
| 29 | les:n4-oracoes-relativas-07 | gen-71eeebb22ba7 | 2/2 | K | same |
| 30 | les:n4-passiva-02 | gen-552e95412e88 | 3/2 | K | load 2 after する; good cultural example |
| 31 | les:n4-passiva-02 | tatoeba-221717 | 3/2 | **D** | 詩 is n1 and unneeded; redundant with row 33 |
| 32 | les:n4-passiva-02 | tatoeba-994752 | 3/2 | **D** | 幽 / 霊 are n1, never unlocked; heaviest of the four |
| 33 | les:n4-passiva-02 | tatoeba-112448 | 2/2 | K | best of the four |
| 34 | les:n4-potencial-04 | tatoeba-10808987 | 5/2 | X | only real なかなか〜ない example; both fits are already shown |
| 35 | les:n4-potencial-04 | gen-b347563062a8 | 3/2 | K | load 2 after granting 中々 |
| 36 | les:n4-suposicao-08 | tatoeba-11692639 | 0/2 | K | zero load; pure level artifact |
| 37 | les:n5-adjetivos-03 | tatoeba-158129 | 4/1 | **A** | 〜たくない, not an i-adjective negative; retag off `gp-24` |
| 38 | les:n5-adjetivos-03 | tatoeba-135763 | 2/1 | K | the only real i-adjective negative; flag ちくしょう register |
| 39 | les:n5-adjetivos-03 | tatoeba-5210 | 2/1 | **A** | same mis-tag as row 37 |
| 40 | les:n5-adjetivos-07 | tatoeba-10883885 | 4/1 | **A** | `no-ga-suki` has 0 at or below n5 |
| 41 | les:n5-adjetivos-07 | tatoeba-1128926 | 2/1 | **A** | same; unlock kanji 好 here |
| 42 | les:n5-comparacoes-01 | gen-dc17b084b7de | 6/1 | **A** | all four points have 0 compliant sentences |
| 43 | les:n5-comparacoes-01 | gen-ead8371d038a | 6/1 | **A** | same |
| 44 | les:n5-comparacoes-01 | gen-326ea97de1a1 | 3/1 | **A** | load 2 after the ほう to 方 fix; still over |
| 45 | les:n5-comparacoes-02 | gen-f7cec4b420ec | 2/1 | K | kanji 番 plus 好 |
| 46 | les:n5-comparacoes-02 | gen-c94b958f1ed1 | 1/1 | K | kanji 番 only |
| 47 | les:n5-comparacoes-02 | tatoeba-203016 | 1/1 | **D** | malformed JP; the pt-BR translates a different sentence |
| 48 | les:n5-comparacoes-02 | tatoeba-223501 | 1/1 | K | good のうちで…一番 model |
| 49 | les:n5-comparacoes-04 | tatoeba-149136 | 2/1 | K | unlock 欲しい here; the one fit is a duplicate noun |
| 50 | les:n5-comparacoes-05 | tatoeba-84964 | 2/1 | **A** | the only other `tai` fit is already shown |
| 51 | les:n5-conectando-01 | tatoeba-82538 | 1/1 | K | inside budget; `node` has 0 alternatives |
| 52 | les:n5-convites-01 | gen-24bb23e4256e | 2/1 | **R** | to `sent:tatoeba-172871` (REAL, n5, load 0) |
| 53 | les:n5-convites-01 | tatoeba-190532 | 1/1 | K | kanji 緒 only |
| 54 | les:n5-convites-01 | tatoeba-190548 | 1/1 | K | kanji 緒 only |
| 55 | les:n5-convites-01 | tatoeba-774809 | 1/1 | K | kanji 緒 only |
| 56 | les:n5-numeros-tempo-03 | tatoeba-122326 | 6/1 | **A** | `gp-43` has 0 within budget; also a potential-form relative clause |
| 57 | les:n5-numeros-tempo-03 | tatoeba-112055 | 5/1 | **A** | same |
| 58 | les:n5-particulas-lugar-01 | tatoeba-80128 | 3/1 | **R** | to `sent:tatoeba-122353` (REAL, n5, load 1) |
| 59 | les:n5-particulas-lugar-01 | tatoeba-229125 | 2/1 | **R** | to `sent:tatoeba-11561754` (REAL, n5, load 0) |
| 60 | les:n5-particulas-lugar-01 | tatoeba-6828196 | 2/1 | **D** | casual `gp-13` in a polite います lesson; duplicate of row 61 |
| 61 | les:n5-particulas-lugar-02 | tatoeba-6828196 | 2/1 | K | right lesson; kanji 学, 校 |
| 62 | les:n5-particulas-lugar-02 | tatoeba-78451 | 1/1 | K | inside budget; 嵐 sets n1 |
| 63 | les:n5-particulas-lugar-06 | tatoeba-125175 | 4/1 | X | to `sent:tatoeba-1510008` (REAL, load 2); nothing fits budget 1 |
| 64 | les:n5-particulas-lugar-06 | gen-59bccb81087b | 2/1 | K | kanji 食 plus 昼 |
| 65 | les:n5-particulas-lugar-07 | tatoeba-145739 | 2/1 | K | fix くれる to 呉れる first; `gp-56` has 0 alternatives |
| 66 | les:n5-particulas-lugar-07 | tatoeba-11059892 | 1/1 | K | inside budget; する only |
| 67 | les:n5-passado-02 | tatoeba-10515932 | 2/1 | **A** | んじゃなかった on a verb; the lesson teaches the noun copula |
| 68 | les:n5-passado-04 | tatoeba-229334 | 3/1 | K | 天気 unlocks in the same topic block |
| 69 | les:n5-passado-04 | tatoeba-77673 | 2/1 | K | 冷たい unlocks at comparacoes-01; check the pt-BR reading |
| 70 | les:n5-perguntas-01 | tatoeba-141432 | 6/1 | **A** | `gp-10` has 0 within budget; 〜もの is far above level |
| 71 | les:n5-perguntas-01 | tatoeba-5055 | 3/1 | K | ここ to 九 mislink plus the 遠い unlock |
| 72 | les:n5-perguntas-01 | tatoeba-5319 | 2/1 | K | both units are the lesson's own content; only `gp-39` sentence |
| 73 | les:n5-perguntas-01 | tatoeba-5933519 | 2/1 | K | overage is 見る / 見; add 234396 as a second example |
| 74 | les:n5-perguntas-02 | tatoeba-80099 | 6/1 | **A** | proverb; その to 園 mislink; `gp-15` has 0 at or below n5 |
| 75 | les:n5-perguntas-02 | tatoeba-74036 | 4/1 | **A** | ロハ is dated slang; `gp-14` has 0 at or below n5 |
| 76 | les:n5-perguntas-05 | tatoeba-201153 | 6/1 | X | to `sent:tatoeba-4561431` (load 3); nothing fits budget 1 |
| 77 | les:n5-perguntas-05 | tatoeba-199382 | 4/1 | **R** | to `sent:tatoeba-199477` (REAL, n5, load 2, load 0 after fixes) |
| 78 | les:n5-perguntas-05 | tatoeba-199569 | 2/1 | K | どんな (own point) plus テスト |
| 79 | les:n5-perguntas-05 | tatoeba-9611533 | 2/1 | K | どう mislink plus 遣る |
| 80 | les:n5-perguntas-06 | gen-532623825322 | 4/1 | K | write なにか in kana; ある and 何 unlock later |
| 81 | les:n5-perguntas-06 | gen-54dd1d1ebf25 | 4/1 | K | same; also uses 〜たい, taught later |
| 82 | les:n5-perguntas-06 | tatoeba-201028 | 3/1 | K | 何処, 出かける, 出 |
| 83 | les:n5-perguntas-06 | gen-c737b9f8b9da | 2/1 | K | 何方 plus いい |
| 84 | les:n5-te-form-03 | gen-47206ec62227 | 4/1 | **A** | 冷蔵庫 plus three kanji; also an alcohol reference |
| 85 | les:n5-te-form-03 | gen-6d412e5af5e1 | 2/1 | K | best てある example; two kanji of known words |
| 86 | les:n5-te-form-03 | tatoeba-85522 | 2/1 | K | 鼻 unlocks next lesson; shown in three consecutive lessons |
| 87 | les:n5-te-form-03 | gen-8bc9ce5df658 | 1/1 | K | inside budget; 鍵 alone sets n1 |
| 88 | les:n5-te-form-04 | tatoeba-5107 | 1/1 | **A** | carries no relative clause; `gp-36` / `gp-37` have 0 at or below n5 |
| 89 | les:n5-te-form-06 | gen-f1c08a8693dc | 3/1 | **A** | `naide` has 1 at level (already shown); `naide-kudasai` has 0 |
| 90 | les:n5-te-form-06 | tatoeba-125387 | 1/1 | K | inside budget; 諦 sets n1; duplicated in a lugar-03 display |
| 91 | les:n5-te-form-07 | tatoeba-2431512 | 2/1 | K | two kanji of known words |
| 92 | les:n5-verbos-01 | gen-e8f19f968193 | 5/1 | **A** | write the time in kana; 5 units on a kana-first sentence |
| 93 | les:n5-verbos-01 | gen-97a9a63e32d1 | 2/1 | K | テレビ and 毎日 unlock later |
| 94 | les:n5-verbos-01 | tatoeba-11795596 | 2/1 | **R** | to `sent:tatoeba-11561754` (REAL, n5, load 1) |
| 95 | les:n5-verbos-02 | gen-867d5c2e8dc3 | 4/1 | **A** | uses the past form, not yet taught; belongs to transitividade-01 |
| 96 | les:n5-verbos-02 | tatoeba-174533 | 3/1 | **A** | blunt imperative 閉めろ, far above level |
| 97 | les:n5-verbos-02 | gen-66857872d764 | 2/1 | K | 飲む and 友達 unlock later |
| 98 | les:n5-verbos-02 | gen-a6201c731653 | 2/1 | K | 本 and 明日 unlock later |
| 99 | les:n5-verbos-06 | tatoeba-143718 | 3/1 | **A** | `o-kudasai` has 0 at or below n5; the lesson's only sentence |

---

## 7. Counts

| Class | Checked | Flagged |
|---|---|---|
| Lessons in slice (`md5(lesson_id) % 3 == 0`) | 43 | 43 |
| Lesson to sentence slots in slice | 99 | 99 |
| **R** — replacement proposed, compliant and on point | 99 | **11** |
| **K** — keep; the repair is an unlock, a token link or a level grade | 99 | **56** |
| **A** — no compliant sentence exists; authoring required | 99 | **22** |
| **X** — accept least-bad, with a written exemption | 99 | **6** |
| **D** — drop the display, no replacement warranted | 99 | **4** |
| Teaching-point mismatches (sentence does not demonstrate its own tag) | 99 | 9 |
| Quality defects in displayed sentences (malformed JP, loose pt-BR, dated slang, idiom as first example, register clash) | 99 | 7 |
| Sentences displayed in more than one lesson inside this slice | 99 | 5 |
| Systemic root causes documented | — | 4 |
| Homograph token mislinks confirmed (distinct vocab records) | 10 | 10 (568 token occurrences) |
| Vocab records missing that the corpus needs | — | 2 (其の その, 如何 どう) |
| Grammar points with zero usable example at or below their lesson level | 78 points across 43 lessons | 21 |
| Candidates flagged as traps for any future automated pass | — | 7 |

Slots that leave the queue with **no sentence work at all** (K plus D): **60 of 99**.
Slots needing a human to write Japanese (A): **22**. Slots with a concrete drop-in replacement (R): **11**.

Zero-findings statement: no lesson in this slice came back clean, but that is by construction, since every
lesson in the slice is in the queue because at least one of its links already failed the gate.

---

## 8. Recommended order of work

1. Fix the ten token mislinks in section 3.1 and add the two missing records (其の その, 如何 どう). One
   data change, 568 tokens, and a prerequisite for authoring anything in `les:n5-comparacoes-01`,
   `les:n5-perguntas-02` and `les:n5-particulas-lugar-07`.
2. Decide section 3.4 once: are する / いる / ある / ない vocabulary items or grammar-carried auxiliaries?
3. Move the section 3.3 unlocks so each lesson owns the item it teaches: 沢山, 其処, 何処, 無い, 欲しい,
   中々, 方, and the kanji 必, 要, 番, 緒, 好, 各, plus 仕 by one position.
4. Re-run `scripts/validate/validate_lesson_gating.py` and re-freeze the baseline. My arithmetic says 60 of
   my 99 slots leave the queue at that point without a single sentence being swapped.
5. Apply the 11 replacements and the 4 drops in section 6, then commission the 22 authored sentences.
