# QA sweep — exam banks, Japanese slice 2/2 (N4)

**Slice:** `corpus/exam_banks/n4_context_fill.json` (368) · `n4_grammar_form.json` (299) ·
`n4_sentence_order.json` (300) · `n4_text_grammar.json` (62) · `n4_paraphrase.json` (60) ·
`n4_usage.json` (60) → **1 149 items checked** (every item in all six banks, not a sample).

**What was checked, per item:** whether exactly one option is defensible; whether each distractor is wrong
*and* plausible; whether the stem is natural Japanese and gives enough context to select the key; whether the
blank falls on a real word/morpheme boundary; and, for `sentence_order`, whether an alternative ordering of
the *given pieces* also yields a grammatical sentence.

**Method.** Manual reading of all 1 149 items, plus four mechanical cross-checks whose output is quoted
below: (a) blank offsets re-aligned against the token boundaries in `corpus/sentences/bank.json` and
`corpus/readings/n4.json`, (b) every option string checked against the project's own kanji registry
`corpus/kanji/n{1..5}.json` (2 131 characters), (c) duplicate stems / duplicate targets within a bank,
(d) option-shape asymmetry (length, sentence-final punctuation) that survives the spec's per-attempt shuffle.

**Assumed item semantics** (from `design/exam_simulator.md` §"Sampling rules" 3): the app shuffles
`[correct + 3 distractors]` per attempt, so any property that singles the key out by *shape* is a
give-away, and `sentence_order` is scored against the single `answer` string.

**Out of scope by instruction:** sentence `structure_explanation` fields. Nothing here touches them.

Severity key: **S1** = the item cannot be answered as posed (blank splits a word, or the key is not a
Japanese unit) · **S2** = more than one option is defensible · **S3** = the option is not Japanese —
internal metadata leaked into learner-facing text · **S4** = `sentence_order` ambiguity / duplication ·
**S5** = orthography or register no N4 learner can meet · **S6** = authoring defects in the Layer-C
`paraphrase` / `usage` banks · **S7** = the key is identifiable by shape alone · **S8** = stale metadata.

---

## S1 — The blank cuts a word in half (highest severity)

The item is unanswerable as a language task: the visible stem is not Japanese, and the "correct answer" is an
arbitrary slice of characters rather than a grammar form.

### F01 — `n4_text_grammar`: 21 of 62 items (34 %) blank a non-morpheme

Re-aligning each stem's blank against the token array of its source passage in `corpus/readings/n4.json`:
41 items land on token boundaries, **21 do not**. Worst cases, with the source string and the blanked slice
in brackets:

| id | stem as the learner sees it | key | what was actually cut |
|---|---|---|---|
| `tg:n4:n4-obrigacao-02-01` | `…私を見て！父はと（　）元気でやっています。` | `ても` | `と[ても]元気` — the key is the middle of the adverb **とても** |
| `tg:n4:n4-conectores-04-01` | `…あの先生はやさしいしお（　）ろい…` | `もし` | `お[もし]ろい` — the middle of **おもしろい** |
| `tg:n4:n4-suposicao-01-01` | `…買い物に行（　）ければならない。` | `かな` | `行[かな]ければ` — splits the ない-stem; the teachable unit is なければならない |
| `tg:n4:n4-oracoes-relativas-07-01` | `2月は28日までし（　）い。` | `かな` | `し[かな]い` — splits **しか…ない** |
| `tg:n4:n4-obrigacao-01-01` | `質問は書い（　）だけませんか。` | `ていた` | `書い[ていた]だけません` — splits **ていただけません**; the key ていた is a *different* form (past progressive) |
| `tg:n4:n4-dar-receber-04-01` | `分けて出し（　）らえますか。` | `ても` | `出し[ても]らえます` — splits **てもらえます**; the key ても is the concessive |
| `tg:n4:n4-condicionais-03-01` | `…しかし、人間はち（　）。` | `がっている` | `ち[がっている]` — splits **ちがっている** |
| `tg:n4:n4-potencial-02-01` | `新しいクラスは（　）がですか。` | `いか` | `[いか]が` — splits **いかが** |

The single most frequent key in this bank is the two-character string **いか** — 11 items, of which 10 are
misaligned (`condicionais-07`, `conectores-03`, `forma-simples-01`, `obrigacao-04`, `potencial-02`,
`potencial-04`, `suposicao-04`, `suposicao-07`, `volitivo-01`, `volitivo-05`; only `causativa-01`
「わけには（　）ない」 is a genuine morpheme boundary). In four of them it is the slice
`どれくら[いか]かります` / `どのくら[いか]かります` — the tail of くらい plus the head of かかる. That is not a
grammar point; it is a substring.

**Fix.** Re-generate this bank with a builder that only accepts blanks whose start *and* end offsets are
token boundaries in the source passage's `tokens` array, and additionally requires the blanked span to equal
the `formation` string of the grammar point the item claims to test. Until then these 21 items should be
moved to `removed_items.json` rather than shipped: the bank drops to 41, below the 3-per-paper draw, which is
still workable with the no-repeat window.

### F02 — `n4_grammar_form`: 16 items blank a non-morpheme

Same check against `corpus/sentences/bank.json` tokens. Confirmed (tokenizer artifacts from the duplicated
long-unit entries in the sentence bank's `tokens` arrays were excluded by hand):

- `gf:n4:3414` — `何があなたにそう考えさ（　）のですか。` key `せる`. Source `考えさせる`, token `させる`. The stem
  ends in `考えさ`, which is not a form of 考える; and 考える is ichidan, so the causative is **させる**, never せる.
- `gf:n4:3444` — `二週間ほど借りら（　）かい。` key `れる`. Source `借りられる`, token `られる`. `借りら` is not a word.
- `gf:n4:3567` / `gf:n4:3569` — `手に入れら（　）と思いますよ。` / `何かすぐ食べら（　）ものある？` key `れる`. Same
  ichidan られる cut in half.
- `gf:n4:3604 / 3605 / 3606 / 3607 / 3608` (all of grammar point `gp-72`) — key `るところだ`, which is not a
  unit in any of them. `gf:n4:3608` is the clearest: `バスは発車す（　）った。` — the blank takes る from **する**
  *and* だ from **だった**, leaving the learner with `発車す` … `った`.
- `gf:n4:3528 / 3529 / 3530` (`gp-150`) — key `れば` cut out of `してや|れば`, `くださ|れば`, `来なけ|れば`. The
  visible stems `親切にしてや`, `来てくださ`, `明日は来なけ` are not Japanese. (`gf:n4:3531` 話上手もい（　） is
  fine — いる + れば is a legitimate ichidan split.)
- `gf:n4:3540` — `私はそ（　）考えた。` key `のように`. Source `そのように`; the blank eats the の of **その**. The
  correct blanking is `私はその（　）考えた。` / key ように.
- `gf:n4:3643` — `そう悪（　）ない。` key `くは`. Splits **悪く**; `悪` is not a standalone word.
- `gf:n4:3798` — `そう水くさ（　）な。` key `くする`. Splits **水くさく**.
- `gf:n4:3402` — `父は私を医者にした（　）。` key `がっている`. Source `したがっている` = し+たがっ+ている; がっている is
  not a morpheme. Worse, the stem *without* the blank (`父は私を医者にした。`) is already a complete sentence.

**Fix.** Same builder constraint as F01, plus an assertion that the blanked span equals the grammar record's
own `formation` / surface pattern (which would have caught `るところだ` vs `ているところだ` and `せる` vs `させる`).

### F03 — `n4_grammar_form` `gp-148`: the key `てすみ` is a truncated label, not a word

`gf:n4:3517`, `3518`, `3519`, `3520` all key the string **てすみ**:

> `長い事お待たせし（　）ません。` → key `てすみ`

The intended sentence is 「長い事お待たせしてすみません」. The pattern is 〜てすみません; blanking `てすみ` leaves
`ません` stranded outside the blank and makes the key a fragment that appears in no dictionary and no lesson.
**Fix:** blank `てすみません` (and drop `ません` from the stem), or blank `すみません`.

### F04 — `n4_context_fill`: 3 items blank one kanji out of a two-kanji compound

- `cf:n4:3793:887` — `そうなるとかなりきつい仕（　）ということになる。` key `事`. The visible `仕` makes 事 the only
  completion (distractors 侯 / 枝 / 間 give 仕侯 / 仕枝 / 仕間, all non-words), so the item tests nothing; and
  the vocab it claims to test (`vocab:1313580` 事) is not what 仕事 means.
- `cf:n4:3806:736` — `急に天（　）が悪くなってきた。` key `気`. Same: 天 forces 気, and the targeted lexeme
  `vocab:1221520` 気 "feeling / mood" is not the 気 of 天気.
- `cf:n4:2061:1094` — `（　）民の声を大切にしたい` key `市`. Splits 市民; the trailing 民 forces the answer.

**Fix.** Reject candidate blanks whose adjacent character belongs to the same token. (The same 25 kanji-adjacent
blanks were reviewed; the other 22 are legitimate — e.g. `cf:n4:3717:902`「（　）前に仕事の計画を立てなさい。」
key 始める, where 前 starts a new token.)

---

## S2 — More than one option is defensible

### F05 — Two items in the same bank give the *same* stem two different keys

| stem | item A | item B |
|---|---|---|
| `モロに（　）。` | `gf:n4:3656` key **聞こえる** | `gf:n4:3658` key **見える** |
| `仕事は（　）終わった。` | `gf:n4:3669` key **ほとんど** | `gf:n4:3703` key **だいたい** |
| `何か（　）？` | `cf:n4:3653:715` key **聞こえる** | `cf:n4:4799:1098` key **見える** |
| `モロに（　）。` | `cf:n4:3656:715` key **聞こえる** | `cf:n4:3658:1098` key **見える** |

Neither member of a pair currently lists the other's key among its distractors, so no *single* item is
self-contradicting today — but the bank asserts two different unique answers for one prompt, which is proof
that these stems do not determine their key. Any regeneration that reshuffles the distractor pool will turn
one of each pair into a two-answer item. **Fix:** delete one of each pair, or extend both stems until the
context selects (`足音がモロに（　）。` vs `姿がモロに（　）。`).

### F06 — 18 items where a distractor also produces natural Japanese

(Two of them, `cf:n4:4799:1098` and `cf:n4:3653:715`, are also counted under F05.)

These are not "odd but grammatical" distractors (which are legitimate); in each case the distractor yields a
sentence a native speaker would accept and, in several, one that is *more* idiomatic than the key.

| id | stem | key | distractor that also works | resulting sentence |
|---|---|---|---|---|
| `cf:n4:3681:1118` | `（　）ですか？` | 以上 | 用事 / 寝坊 / 輸出 | **all four** fit — the frame `Ｎですか？` accepts any noun (`用事ですか？` "Is it business?") |
| `cf:n4:3686:958` | `（　）はいいかい。` | 用意 | 暖房 | `暖房はいいかい。` "Is the heating all right?" |
| `cf:n4:3697:1253` | `（　）よりずっといいよ。` | 工場 | 数学 | `数学よりずっといいよ。` |
| `cf:n4:3687:1006` | `（　）はいかがですか。` | 味 | 夫 | `夫はいかがですか。` |
| `cf:n4:4800:811` | `（　）が見える。` | 家 | 形 | `形が見える。` |
| `cf:n4:4801:1098` | `よく（　）？` | 見える | 考える | `よく考える？` |
| `cf:n4:4799:1098` | `何か（　）？` | 見える | 決める | `何か決める？` |
| `cf:n4:3653:715` | `何か（　）？` | 聞こえる | 可笑しい / 片付ける | `何かおかしい？` is the most natural reading of this frame |
| `cf:n4:4790:902` | `新たに（　）。` | 始める | 建てる | `新たに建てる。` |
| `cf:n4:3623:1300` | `午後には（　）だろうか？` | 上がる | 増える | `午後には増えるだろうか？` |
| `cf:n4:5408:1033` | `めったに（　）には行かない。` | 教会 | 遊び | `めったに遊びには行かない。` |
| `cf:n4:1345:1195` | `新しい仕事が（　）といいです` | 見つかる | 役に立つ | `新しい仕事が役に立つといいです` |
| `cf:n4:3638:736` | `（　）にするな。` | 気 | 急 | `急にするな。` "don't rush it" |
| `cf:n4:1730:964` | `これは母への（　）です` | お土産 | **贈り物** | the distractor is a near-synonym of the key — and `corpus/exam_banks/n4_paraphrase.json` `pp:n4:762` itself glosses 贈り物 as プレゼント, i.e. exactly this slot |
| `gf:n4:3555` | `私（　）。` | ですが | がする | `私がする。` "I'll do it" — a complete, natural sentence, arguably better than the fragment `私ですが。` |
| `gf:n4:3547` | `（　）分かってきたよ。` | だんだん | どんどん | `どんどん分かってきたよ。` |
| `gf:n4:3548` | `（　）思い出してきたぞ。` | だんだん | とうとう | `とうとう思い出してきたぞ。` |
| `gf:n4:3614` | `（　）気にしない。` | ぜんぜん | それでも | `それでも気にしない。` |

Root cause: the stem carries too little context. 44 `grammar_form` stems and 23 `context_fill` stems have
**five characters or fewer** outside the blank (`私（　）。`, `（　）こと。`, `今（　）。`, `トム（　）。`,
`やる（　）。`, `（　）ですか？`, `よく（　）？` …). A five-character frame cannot single out one of four options.

**Fix.** Require a minimum stem length (the real N4 文脈規定 stem is a full clause) and add a build-time
adversarial pass that substitutes each distractor and rejects the item if the result parses as well-formed.
The 18 items above should be re-stemmed from a longer source sentence or dropped.

---

## S3 — Internal metadata leaked into the learner-facing options

### F07 — 103 items (87 `grammar_form` + 16 `text_grammar`) carry an option that is not Japanese

108 option slots. Three distinct leak mechanisms:

**(a) grammar-point *titles* used as fill-in-the-blank options** — 21 slots in `grammar_form`, 3 in
`text_grammar`: `自動詞`, `他動詞`, `命令形`, `意向形`, `受身形`. e.g. `gf:n4:3360` 「その（　）どうすればいい
でしょう？」 offers **命令形** ("imperative form") as a choice. No learner would ever pick a metalinguistic label,
so the item silently becomes 3-option.

**(b) disambiguation indices carried into the string** — 12 slots: `ずっと ①` (7) and `以上 ①` (5), e.g.
`gf:n4:3380` distractor `ずっと ①`. The circled numeral is an internal sense index; it also puts a space in
the middle of a Japanese option.

**(c) pattern placeholders stripped, leaving a non-word** — 72 slots. The distractor pool was built from
grammar-pattern strings with the `〜` slot markers removed, producing: `でも でも` (8, from 〜でも〜でも),
`とかとか` (7, 〜とか〜とか), `おになる` (7, お〜になる), `おする` (5, お〜する), `おください` (3, お〜ください),
`しし` (7, 〜し、〜し), `とと` (6, 〜と〜と), `はの一つだ` (4, 〜は〜の一つだ), `のはだ` (5, 〜のは〜だ),
`ないはない` (4), `まいのように` (7), `のようてほしい`, `ようにてほしい`.

**Fix.** Build distractors from the *surface form* field of the grammar records, never from the title/label
field, and add a validator that rejects any option containing a space, a `[①-⑳]`, or a known
grammar-terminology string. This is one bug in the builder, not 103 authoring mistakes.

---

## S4 — `sentence_order`: the given pieces admit a second grammatical ordering

Japanese pre-verbal arguments and adverbials scramble freely, and these items are shuffled at
**morpheme** level (piece counts 5–9; the real 文の組み立て uses 4 chunks), which multiplies the openings.
Scored against a single `answer` string, each of the following marks a correct learner answer wrong.

### F08 — 15 confirmed ambiguous items

| id | keyed `answer` | equally grammatical alternative from the same pieces |
|---|---|---|
| `so:n4:805` | ラジオで今朝ニュースを聞きましたか | **今朝ラジオで**ニュースを聞きましたか |
| `so:n4:3465` | 同じ話を何度もします | **何度も同じ話を**します |
| `so:n4:3604` | 上着を今着ているところだ | **今上着を**着ているところだ |
| `so:n4:930` | 去年トマトを作ったがとてもおいしかった | **トマトを去年**作ったが… |
| `so:n4:947` | 母は午前中病院に行きます | **午前中母は**病院に行きます |
| `so:n4:642` | 私はデパートでオーバーをあつらえた | **デパートで私は**オーバーをあつらえた |
| `so:n4:3436` | ほかに何かお持ちしましょうか | **何かほかに**お持ちしましょうか |
| `so:n4:3591` | 私はとうとうタバコをやめた | **とうとう私は**タバコをやめた |
| `so:n4:3495` | 自分でもそれをやってみます | **それを自分でも**やってみます |
| `so:n4:3618` | 計画は雨でぜんぜんだめになった | **雨で計画は**ぜんぜんだめになった |
| `so:n4:3541` | 私はいつものように早く起きた | **いつものように私は**早く起きた |
| `so:n4:988` | 近くでバスケットが作られている | **バスケットが近くで**作られている |
| `so:n4:476` | 来週ぜひ夕食をご馳走させてください | **ぜひ来週**夕食をご馳走させてください |
| `so:n4:844` | 来年の冬またここに来たいな | **また来年の冬**ここに来たいな |
| `so:n4:223` | たまにパソコンが急に切れるんですよ | **パソコンがたまに**急に切れるんですよ |

**Fix (structural).** Move to the real JLPT format: fix the first and last chunk, shuffle only the middle,
and score the starred position rather than the whole string. Failing that, the scorer must accept a set of
answers, generated by permuting the item's phrase-level constituents and keeping every permutation that a
parser accepts. Merging pieces into ~4 bunsetsu chunks (`ラジオで` / `今朝` / `ニュースを` / `聞きましたか`) would
also cut, but not remove, the exposure.

### F09 — 4 items are two exact duplicate pairs

- `so:n4:808` and `so:n4:809`: identical `pieces` and `answer` (`今月あのスーパーは水曜日が休みです`), different
  source sentences (`sent:tatoeba-10996698` / `sent:tatoeba-11001318`).
- `so:n4:3419` and `so:n4:3421`: identical (`聞いてくれてありがとう`), from `tatoeba-10355885` / `tatoeba-11858059`.

Sampling is without replacement *by id*, so one paper can draw both and ask the same question twice out of
its 4 `sentence_order` slots. **Fix:** de-duplicate on `answer`, keeping one `sentence` ref.

### F10 — 5 items whose pieces cannot be assembled by a learner

- `so:n4:3423` — pieces `['少し','お','金貸','し','て','もらえ','ない']`. **金貸** is a mis-segmentation of
  お金＋貸して; the piece is a different word (moneylender). The learner is asked to build a word that isn't there.
- `so:n4:422` — pieces include bare `「` and `」` as two shufflable items.
- `so:n4:1052` — same, plus the Latin-script proper name `Muiriel` (`パスワードは「Muiriel」です`).
- `so:n4:832` — `肉を半㌔ください`, piece `㌔` is the CJK compatibility ligature U+3314, not `キロ`. Normalize.
- `so:n4:933` — pieces `['お','いで',…]` split おいで in half; the target
  `木曜日よりむしろ金曜日においでいただきたい` is keigo well above N4 in any case.

---

## S5 — Orthography and register no N4 learner can meet

### F11 — 69 option slots in `n4_context_fill` use kanji outside the project's own registry

Checked against `corpus/kanji/n{1..5}.json` (2 131 characters — everything the corpus teaches at any level).
24 distinct characters appear in options that the corpus never teaches: 儘 (8) · 髭 (7) · 嘘 (7) · 筈 (5) ·
葡萄 (3) · 噛 (3) · 濡 (3) · 味噌 (3) · 掏摸 (2) · 馳 (2) · 殆 (2) · 阿弗利加 (2) · 嬉 (2) · 勿論 (2) ·
吃驚 (2) · 此れから (2) · 叱 (2) · 尤も (2) · 貰 · 瓦斯 · 塵. Plus in-registry but rare-orthography forms:
亜米利加, 亜細亜, 許り, 為さる, 御座います, 矢っ張り, 又は, 漸と, 成るべく, 確り, 中々, 偶に, 若し.

**15 of these are in the `correct` slot**, i.e. the keyed answer is a form the learner cannot read:

`cf:n4:2300:1320`「あの町は（　）が多い」key **掏摸** (すり) · `cf:n4:3322:1356` and `cf:n4:3324:1356` key
**尤も** · `cf:n4:381:856`, `1609:856`, `1610:856` key **葡萄** · `cf:n4:475:1010`, `476:1010` key **ご馳走** ·
`cf:n4:1744:971`, `2005:971` key **味噌** · `cf:n4:2197:1251`, `2198:1251` key **髭** · `cf:n4:1891:1071`
key **叱る** · `cf:n4:5004:800`, `1893:800` key **嘘**.

**Fix.** Render every option from the vocab record's `is_primary` / `is_common` form (`corpus/vocab/n4.json`
`forms[]`) rather than from an arbitrary JMdict kanji form, and add a validator rejecting any option
containing a character absent from `corpus/kanji/*`. 掏摸 → すり, 尤も → もっとも, 葡萄 → ぶどう, 阿弗利加 →
アフリカ, 亜米利加 → アメリカ, 瓦斯 → ガス.

### F12 — `n4_text_grammar` stems have no sentence boundaries (inherited defect)

Every stem in this bank is four unrelated sentences concatenated, and in most of them the sentence-final 。
is missing, so the learner sees one run-on string:

> `tg:n4:n4-conectores-02-01` — `また始まった。この店は安いです （　）料理もおいしいですこのカフェはまた来たいまた明日会いましょう`

This is **inherited from the passage layer**, not introduced here: `read:n4-conectores-02-01`'s `jp` is
already `…この店は安いです それに料理もおいしいですこのカフェはまた来たいまた明日会いましょう` (verified — 0 of 62
stems drop a 。 the source passage has). Flagging it because the exam bank is where it reaches a learner;
the fix belongs in `corpus/readings`. Same pattern in `read:n4-condicionais-04-01`,
`read:n4-conectores-04-01`, `read:n4-experiencia-04-01`, and in `so:n4:1055` / `so:n4:1056`
(`トピずれですすみません` / `ミスタイプですすみません`, two sentences run together).

### F13 — Register outliers (noted, not individually itemised)

Selected N4 stems that no N4 learner can parse: `so:n4:315`「世に真の大事なし」(classical なし) ·
`so:n4:3538`「雨後のたけのこのような安アパート」(N1 idiom, and a noun phrase rather than a sentence) ·
`so:n4:1073`「不時にそなえなくてはいけない」 · `so:n4:956`「今日は魚の食いが悪い」 ·
`so:n4:3442`「人に足下を見られるなよ」 · `so:n4:3398`「お茶の質は下がりつつある」(N2 つつある) ·
`tg:n4:n4-condicionais-06-01`「これはさすがにヤバすぎる」 · `pp/us:n4:710`「虫でさえも医学研究のために購入される」
(でさえ + 購入 + passive) · `pp/us:n4:770`「レポート点の上限を10点とします」(上限). These are Tatoeba-selection
problems, not translation problems — the selector needs a level gate on the *whole* sentence, not just on the
target lexeme.

---

## S6 — `paraphrase` / `usage` authoring defects (Layer C)

### F14 — `pp:n4:775` and `us:n4:775` test a word that is not in the sentence

Both items target `vocab:1006280` **すると** — a conjunction, glossed in the corpus as
`["então","aí (então)","e então"]` / `["and then","thereupon","whereupon"]`. Both use
`sent:tatoeba-184350`:

> 学校を卒業する**と**彼はアフリカへ行った。

The string すると occurs here only because 卒業する happens to end in する; the morphology is 卒業-する-と, and と
is the conditional/temporal particle. The paraphrase key confirms the mis-analysis — it offers **したら**,
i.e. it paraphrases する+と, not the conjunction.

`us:n4:775` is worse: its keyed *correct usage* sentence does not contain the conjunction at all, while all
three "wrong" options do (`眠い。すると早く寝なさい。` etc.). The item asserts that the sentence without the word
is the one that uses it correctly. **Fix:** re-source both from a sentence with sentence-initial すると
(`…。すると、雨が降り出した。`), or drop the pair.

### F15 — `us:n4:745`: the "wrong" option uses 運 correctly

> key: 本当に運が良かった
> wrong: **明日は運が悪いので、会議に出られません。**

運が悪い is the standard collocation, the exact mirror of the key's 運が良かった. The intended error is
運↔都合, but a 用法 item asks whether the *word* is used correctly, and here it is. A learner who knows 運 has
two defensible answers. **Fix:** replace with a sentence where 運 fills a slot it cannot take, e.g.
×「車の運がうまい」 (→ 運転) or ×「運を運んでください」.

### F16 — `us:n4:780`: the "wrong" option is the textbook collocation

> key: エスカレーターはどこですか？
> wrong: **エスカレーターに乗って学校に通う。**

エスカレーターに乗る is *the* collocation for the word; only the pragmatics (commuting by escalator) are odd,
and the key itself uses the word in a way that demonstrates nothing. The other two distractors
(`ボタンを押した`, `ドアが開いた`) are good — they are エレベーター slots. **Fix:** replace the third with a
third エレベーター/階段 confusion, e.g. ×「エスカレーターで五階まで上がるボタンを押した」.

### F17 — `pp:n4:709` / `us:n4:709`: ステレオ is a device, and the key says it is music

`pp:n4:709` stem 「ステレオをかけても構わないかい。」 keys **音楽**, against distractors 電話 / めがね / かぎ — all
physical objects. The corpus's own gloss for `vocab:1070650` is `["aparelho de som","som estéreo"]` /
`["stereo","stereo system"]`, and the bank sentence's pt translation is "Tudo bem se eu **ligar o som**?".
音楽 is what the device plays, not what the word means, and it is also the only option in the set that is not
an object — so the key is identifiable by category alone. This bank glosses other devices correctly
(`pp:n4:780` エスカレーター → 動く階段), so it is an outlier. **Fix:** key `音楽を聞く機械` / `オーディオ`.

### F18 — `pp:n4:793` / `us:n4:793`: the keyed sentence is not usable Japanese

Both use `sent:tatoeba-103178` 「彼は盛んにしている。」 as the *correct* exemplar of 盛ん. 盛んに is an adverb that
must modify a specified activity (盛んに手を振る, 研究が盛んだ); with a bare している and no activity the sentence
is incomplete. `pp:n4:793` compounds it by keying 盛ん → **元気**, which is neither of the corpus's own senses
(`popular / thriving` · `energetic / vigorous`). **Fix:** re-source from a 〜が盛んだ sentence
(この町はサッカーが盛んだ) and key 盛ん → さかんに行われている / 人気がある.

### F19 — `pp:n4:736`: the keyed paraphrase does not substitute

> stem `気にするな。` target `気` key **心配** (distractors 病気 / 元気 / 空気)

Substituting gives ×`心配にするな`. The unit being paraphrased is 気にする, not 気; and the three distractors are
all 〜気 compounds, i.e. an orthographic trap rather than a meaning trap — none of them substitutes either.
**Fix:** set `target` to 気にする and key 心配する.

### F20 — `pp:n4:771`: the keyed gloss is awkward Japanese

> 葉 → **木や草の緑のうすいもの**

Reads as "the thin thing of green of trees and grass"; 緑のうすい also parses as "pale green", inverting the
sense. **Fix:** `木や草についている緑のもの`.

### F21 — `pp:n4:770`: the paraphrase does not substitute into the stem

> stem `レポート点の上限を10点とします。` target `レポート` key **報告書**

レポート here is bound inside the compound レポート点; substituting yields ×報告書点. **Fix:** re-source from a
free-standing use (`来週までにレポートを出してください`).

---

## S7 — The key is identifiable by shape after the shuffle

The spec shuffles `[correct + 3 distractors]` per attempt, so these survive shuffling.

### F22 — `n4_usage`: 9 items where only the key lacks sentence-final punctuation

`us:n4:695`, `696`, `700`, `706`, `731`, `740`, `745`, `784`, `801`. In each, the three fabricated wrong
options all end in `。` and the real bank sentence used as the key does not:

> `us:n4:706` — key `厳しい意見が多い` · wrong `この言葉の意見が分かりません。` / `今日は意見が悪いので休みます。` /
> `先生に意見を借りました。`

A learner can score these without reading Japanese. **Fix:** normalise terminal punctuation across all four
options at export time.

### F23 — `n4_usage`: the key is the shortest option in 26 of 60 items

The fabricated distractors cluster at 12–15 characters; the real bank sentences vary and are often much
shorter — `us:n4:725` key `表か裏か。` (5 chars) against 16/13/14; `us:n4:728` key `彼は予習した。` (7) against
13/14/14; `us:n4:736` key `気にするな。` (6) against 15/12/13. 26/60 is well above the 25 % expected by chance
and, combined with F22, makes the pattern learnable across attempts. **Fix:** length-match the distractors to
the drawn key (the `context_fill` and `grammar_form` builders already do this correctly — verified, their
options are length-matched).

### F24 — `n4_paraphrase`: 17 items where the key is a definition and the distractors are single words

`pp:n4:698, 710, 726, 728, 740, 748, 752, 762, 767, 771, 774, 784, 790, 794, 798, 800, 804`. Worst:
`pp:n4:771` key `木や草の緑のうすいもの` (11 chars) against 花 / 枝 / 根 (1 char each); `pp:n4:767` key `屋根の端`
against 窓 / 壁 / 門; `pp:n4:752` key `ポイント` against 回 / 個 / 番. The key is the only multi-word
descriptive phrase in the set. **Fix:** either gloss all four options descriptively, or key a single-word
near-synonym (葉 → 木の緑の部分 with 花びら / 木の枝 / 木の根 as distractors).

Items where this is done right, for contrast: `pp:n4:781` 人口 → 人の数 vs 車の数 / 家の数 / 店の数;
`pp:n4:745` 運 → ついていた vs 困っていた / 疲れていた / 怒っていた.

---

## S8 — Stale metadata

### F25 — `corpus/exam_banks/INDEX.md` item counts are wrong for 3 of the 6 files in this slice

| file | INDEX.md claims | actual |
|---|---|---|
| `n4_context_fill.json` | 370 | **368** |
| `n4_grammar_form.json` | 300 | **299** |
| `n4_text_grammar.json` | 88 | **62** |

The gaps match exactly the items pulled by `scripts/contracts/migrate_exam_banks_p7.py` into
`removed_items.json` (2 + 1 + 26 for these three files); INDEX.md was simply not regenerated afterwards. The
same is true outside this slice (`n3_context_fill` 400→389, `n3_text_grammar` 137→94, `n5_context_fill`
241→235, `n5_text_grammar` 37→33), and `design/exam_simulator.md` still says "4,359 items" where the banks
now hold 4 266. **Fix:** re-run the INDEX generator and update the one figure in the spec.

---

## Checked and cleared (not flagged)

Worth recording so the next pass does not re-litigate these:

- **`context_fill` / `grammar_form` option length-matching** — verified correct; options within an item are
  consistently the same length, so no length give-away in those two banks (contrast F23).
- **Answer leakage into the stem** — 0 items in either bank have the `correct` string also present elsewhere
  in the stem. The `removed_items.json` migration that fixed this held.
- **`sentence_order` integrity** — `''.join(pieces) == answer` for all 300; no item reuses a `sentence` ref.
- **`text_grammar` passage refs** — all 62 `reading` slugs resolve in `corpus/readings/n4.json`, and every
  filled stem reconstructs its passage exactly.
- **`paraphrase` semantic accuracy** — 51 of 60 keys are clean, well-chosen near-synonyms with genuinely
  wrong distractors (床屋 → 髪を切る店 vs 八百屋/本屋/肉屋; 機会 → チャンス with the 機械 homophone trap;
  地震 → 地面がゆれること; 郊外 → 町の中心から離れた所 with the 都心 antonym).
- **`usage` distractor craft** — the homophone/near-miss distractors are the strongest work in the slice:
  地震/自信 (`us:n4:774`), 注意/注射 (`765`), 台風/風邪 (`766`), 泥棒/泥 (`763`), 人口/人工 (`781`),
  アルバイト/アルバム (`794`), 機会/機械 (`755`). Only F15/F16 fail.
- **`us:n4:726`** (`五歳の妹は大学生です。`) was considered and **not** flagged: it is well-formed but
  world-knowledge-false, which is an accepted 用法 distractor type — unlike F15/F16, where the word's own
  collocation is respected.

---

## Counts

| bank | items checked | items flagged | % |
|---|---:|---:|---:|
| `n4_context_fill.json` | 368 | 34 | 9.2 % |
| `n4_grammar_form.json` | 299 | 105 | 35.1 % |
| `n4_sentence_order.json` | 300 | 24 | 8.0 % |
| `n4_text_grammar.json` | 62 | 32 | 51.6 % |
| `n4_paraphrase.json` | 60 | 22 | 36.7 % |
| `n4_usage.json` | 60 | 13 | 21.7 % |
| **total** | **1 149** | **230** | **20.0 %** |

| finding | severity | items |
|---|---|---:|
| F01 `text_grammar` blank splits a word | S1 | 21 |
| F02 `grammar_form` blank splits a morpheme | S1 | 16 |
| F03 key `てすみ` is a truncated label | S1 | 4 |
| F04 `context_fill` blank splits a kanji compound | S1 | 3 |
| F05 same stem, two different keys | S2 | 8 |
| F06 a distractor also produces natural Japanese | S2 | 18 |
| F07 metadata / non-word options | S3 | 103 |
| F08 `sentence_order` alternative ordering | S4 | 15 |
| F09 `sentence_order` duplicate items | S4 | 4 |
| F10 `sentence_order` unassemblable pieces | S4 | 5 |
| F11 keyed answer in untaught orthography | S5 | 15 |
| F12 run-on stems (inherited from `corpus/readings`) | S5 | 62 (bank-wide) |
| F14–F21 `paraphrase` / `usage` authoring | S6 | 11 |
| F22 only the key lacks final punctuation | S7 | 9 |
| F23 key is the shortest option | S7 | 26 |
| F24 key is the only descriptive phrase | S7 | 17 |
| F25 stale `INDEX.md` counts | S8 | 3 files |

Findings overlap (F07 covers many items also hit by F02/F03), so the per-finding column sums to more than the
230 distinct items in the table above.

**Highest-leverage fixes, in order:** (1) the blank-boundary constraint in the builder — it alone accounts for
F01–F04, 44 items, and every one of them is currently unanswerable; (2) the distractor-pool source fix in
F07, one bug behind 103 items; (3) the option-orthography fix in F11; (4) the `sentence_order` format change
in F08, which is the only finding here that needs a scoring-side decision rather than a data fix.
