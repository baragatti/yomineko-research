# QA sweep: `corpus/exam_banks` N3 (all sections)

**Slice:** every `corpus/exam_banks/n3_*.json` file (14 files, 2 261 items), including the five
`listening_*` script banks and `reading_comp`.
**Method:** full read of the five listening banks, `paraphrase`, `usage`, `text_grammar` and
`reading_comp`; full dump-and-read of `context_fill` (389) and `grammar_form` (300); scripted
cross-checks of all 2 261 items against `corpus/vocab`, `corpus/sentences/bank.json` and
`corpus/readings` (stem reconstruction, answer reconstruction, distractor collision, reading
match, form commonness, duplicate-key detection), plus targeted sampling of `kanji_reading`,
`orthography` and `sentence_order`.
**Read-only.** No file outside this report was modified.
**Excluded per brief:** sentence `structure_explanation` fields.

Verified clean, for the record: no duplicate item ids; no item where `correct` appears in its own
`distractors`; no duplicate distractors; no empty options; all `sentence` / `reading` / `vocab`
refs resolve; all 389 `context_fill` and 300 `grammar_form` stems reconstruct their source sentence
exactly when the blank is filled with `correct`; all 300 `sentence_order` answers reconstruct their
source sentence; all 27 `listening_reply` prompts are byte-identical to their `sentence` ref and
within the 6 to 22 character bound; listening bank sizes match `design/listening.md` exactly
(task 18, point 18, gist 9, say 12, reply 27 = 84 = 3x the paper counts); no `kanji_reading`
distractor is a real reading of its stem and no `orthography` distractor can be read as its stem
kana, anywhere in the N1 to N5 vocab registry.

---

## F1. `text_grammar`: all 94 items are built on a text that is not a text (blocking)

The JLPT 文章の文法 section exists to test cohesion *across* sentences. Every one of the 94 N3
items instead concatenates five or six unrelated Tatoeba sentences and drops a blank into one of
them.

`tg:n3:n3-causa-02-01`:

> 引力によって物体が重さを持つようになる。フランス語は多くの人々によって話される。ドアはジムによって開けられます。とりあえず、あたりさわりのない話をしておいたよ。外国、たとえばアメリカへ行った（　）がありますか。

Gravity, the French language, Jim's door, small talk, and travelling abroad. There is no topic, no
referent chain, no connective logic. The blank (`こと`) is solved from its own clause alone, so the
preceding 60 characters are pure noise, and a learner who tries to read them for context is
actively misled.

`tg:n3:n3-causa-04-01` is the same shape:

> 私たちはよく映画に行って楽しんだものだ。私はあんたのお姉ちゃんだもん。いつかこんな（　）になるって、ずっと思ってたよ。…

**Why it matters:** as built, this section duplicates `grammar_form` (single-sentence blanks) while
claiming to be a different skill, and `INDEX.md` states real papers were used as a FORMAT reference.
This is the format that was not reproduced. The items are also flagged `layer: B`,
`needs_review: false`, so nothing routes them to the human reviewer.

**Fix:** the section needs authored short texts (a notice, a diary entry, an email, 150 to 200 ji)
with 4 to 5 blanks each, where at least two blanks require the preceding sentence (connectives,
そこで / それなら, anaphora, tense agreement). Until then, mark all 94 `needs_review: true` and exclude
`text_grammar` from the simulator rather than shipping a section that tests nothing new.

## F2. `reading_comp`: all 152 items rest on the same non-passages (blocking)

Identical root cause, separate bank. Every one of the 152 `read:` slugs is a concatenation of
unrelated sentences, and every question targets exactly one of them.

`rc:n3:n3-conectores-06-01` asks 「この人は相手に何をお願いしていますか。」 over a "passage" whose six
sentences have six different speakers and no shared situation. `rc:n3:n3-causa-02-01` asks
「この文章の内容と合っているものはどれか。」 when there is no 文章. `rc:n3:n3-tempo-08-02` asks how
long until summer holidays over: 黒に黒をたしても白にはならぬ。夏休みまであとわずか一週間だ。おじは学校の近くに住んでいる。…

The answers are all technically correct, which is exactly the problem: the item is a
single-sentence comprehension check wearing a reading-comprehension label. Nothing here tests
inference, referent tracking, paragraph gist, or author stance, which is what 読解 measures.

**Fix:** same as F1. These need authored passages. Note that `design/listening.md` already
specifies real authored monologues for `listening_gist`, and those are good (see the clean list
below), so the capability exists; it was simply not applied to `readings`.

## F3. 25 items render a passage with two sentences fused into a run-on (high)

Passage assembly is a naive `''.join()` of `source_slugs`, and the sentence bank correctly stores
GENERATED Japanese without a final 。 (per `design/translation_style.md` §3). The result is
ungrammatical text on screen.

`rc:n3:n3-conectores-06-01` / `tg:n3:n3-conectores-06-01`:

> もっと社会全体の問題に関心を持つべきだ**手をきれいに**しておかなければならない。

Two sentences welded at 「べきだ手を」. Worst case, `rc:n3:n3-conjectura-07-02`: six source
sentences, **one** terminator, an 80-character run-on:

> 今のところ別にやめる気は全然ない。どんどんガソリンの値段が上がります親はすぐにこどもを病院に連れてくる私が今こうして、二日分の日記を書く中学校の２年生が職場体験をしました子どもを連れ去る所を近所の人が見た

Full affected set (15 passages, 25 items): `rc:n3:n3-concessao-05-01`, `-concessao-06-02`,
`-conectores-06-01`, `-conectores-08-02`, `-conjectura-06-01`, `-conjectura-07-02`, `-desejos-05-01`,
`-desejos-07-01`, `-estado-08-01`, `-estrutura-01-01`, `-estrutura-06-01`, `-intencao-05-01`,
`-relato-05-01`, `-relato-06-02`, `-tempo-04-02`, plus the `tg:` twins of ten of those.

**Fix:** the joiner must append 。 when a segment does not already end in 。／？／！. Cheap and
mechanical; worth doing even if F1/F2 are deferred.

## F4. 135 items are cross-linked to the wrong lexeme (high)

`context_fill`, `paraphrase` and `usage` carry `vocab_id` / `vocab` pointing at the dictionary entry
the item supposedly tests. For 135 items (129 of 389 in `context_fill` alone, 33%) the linked
entry's reading does not occur in the sentence, because the generator matched on written **form**
and ignored reading and sense. The sentence bank's own `kana` field proves each case.

Worst clusters:

| linked entry | items | what the sentence actually uses |
|---|---|---|
| `空` / から, vocab:1245280, glossed "vazio, oco (garrafa vazia)" | 6 | そら (sky), every single one: 「なぜ空は青いのか？」kana `そらわあおいのか` |
| `下` / もと, vocab:2004390, "sob a orientação de" | 5 | した: 「木の下でちょっと休もうよ」kana `きのした…`; and か in 「県下で」 |
| `分` / ぶん, vocab:1502860, "parte, porção, quinhão" | 9 | ふん, the minute counter: 「駅までタクシーで２０分かかるでしょう」kana `にじゅっぷん` |
| `音` / おん, vocab:2859161 | 8 | おと: 「ベルの鳴る音が聞こえた」kana `…なるおとが…` |
| `金` / きん, vocab:1242600, "ouro" | 7 | かね (money): 「おじは気前よく金を出す」kana `かねをだす` |
| `上` / じょう, vocab:1352170, suffix "em termos de …" | 13 | うえ: 「鳥が木の上で歌っている」kana `きのうえで` |
| `時` / とき, vocab:1315840 | 26 | じ, the o'clock counter: 「学校は午前８時１０分から始まる」kana `はちじ` |
| `間` / ま, vocab:1215240 | 17 | あいだ: 「木立の間に家が見える」kana `こだちのあいだに` |
| `後` / のち, vocab:1269330 | 12 | あと and ご: 「後で話そうね」kana `あとで`; 「百年後には」kana `ひゃくねんご` |
| `度` / たび, vocab:1445150, "vez, ocasião" | 10 | ど, including **degrees Celsius**: 「あっという間に４０度近くまで熱が出た」 |

Two items are outright unanswerable as a result:

- **`cf:n3:944:2173`** 「（　）はやさしい声をしている。」 correct `正`, linked to vocab:1376590
  `正` / せい "correto, positivo (número)". The source sentence `sent:tatoeba-83722`-adjacent kana is
  `ただしわやさしいこえをしている`: 正 here is the **given name Tadashi**. No learner can deduce a
  proper name from context, none of the distractors (雷 / 紐 / 稍) is a name, and the linked gloss is
  unrelated. Drop the item.
- **`pp:n3:1744`** 「金は少ししかない。」 target `金`, **correct answer `黄金`**. The sentence's own kana
  is `かねわすこししかない` and its pt-BR translation reads as money. The answer key says "gold". This
  is a wrong answer, not just a wrong link. `pp:n3:1629` handles the same word correctly
  (`金` → `金銭`). Change the key to `金銭` / `お金` or drop.

**Fix:** the linker must match on reading, not surface form. Re-derive `vocab_id` from the
sentence's token reading at the blank position (the `readings` records already carry per-token `r`
fields, so the data exists), then re-check. Until fixed, any app UI that shows "the word this item
teaches" will show learners the wrong dictionary entry a third of the time, and the §1.7 graph
links are wrong.

## F5. 15 `grammar_form` stems are cut mid-word (high)

The blank was placed by string offset, not at a morpheme boundary, so the displayed stem is not
Japanese.

Tail cut (the option swallows the following mora):

- `gf:n3:5100` 「あなたの（　）す。」 correct `おかげで`. The learner is shown 「…の（　）す。」 and must
  reconstruct 「あなたのおかげです。」 by mentally splitting です. Same shape:
  `gf:n3:5102` 「私がいるのは父の（　）す。」, `gf:n3:5105` 「あなたの（　）す。」 (`せいで`),
  `gf:n3:5106` 「ごめんなさい。私の（　）す。」, `gf:n3:5108` 「風が強いのはビル風の（　）す。」
- `gf:n3:5280` 「昨日来る（　）ったのに。」 correct `べきだ` → 「昨日来るべきだったのに。」 Also
  `gf:n3:5281`, `gf:n3:5282`.

Head cut (the stem ends inside a word):

- `gf:n3:5140` 「私はあんたのお姉ちゃ（　）。」 correct `んだもん`. 「お姉ちゃ」 is not a word; the ん of
  お姉ちゃん was eaten by the option.
- `gf:n3:5169` 「車がい（　）でした。」 and `gf:n3:5170` 「こっちはい（　）です。」 correct `っぱい`.
  いっぱい was split into い + っぱい.
- `gf:n3:5202` 「ダイエットしよ（　）。」 and `gf:n3:5206` 「あれ、私何言お（　）んだっけ？」 correct
  `うとした`. 「言お」 is a fragment.
- `gf:n3:5195` / `gf:n3:5196` 「明日までに仕（　）必要はありません。」 correct `上げる`: the blank cuts
  the lexicalized verb 仕上げる in half.

**Fix:** constrain blank placement to Sudachi token boundaries and require the blanked span to equal
one whole grammar-point surface form. For the `おかげ` / `せい` family, blank `おかげ` (not `おかげで`)
so the stem reads 「あなたの（　）です。」.

## F6. 8 `grammar_form` items are tagged with a grammar point they do not contain (medium)

- `gf:n3:5195` / `gf:n3:5196` tagged `n3-ageru`, but 上げる here is the second half of the compound
  verb 仕上げる, not the benefactive 〜てあげる.
- `gf:n3:5197` 「彼女の事が思い（　）。」 tagged `n3-kirenai`: 思い切る is a lexicalized verb ("give up
  on"), not 〜きれない "cannot finish". `gf:n3:5201` 「いくらお礼を言っても言い切れない。」 is the real
  pattern; 5197 teaches the opposite lesson.
- `gf:n3:5123` 「彼らは死ん（　）とあきらめた。」 and `gf:n3:5124` 「人々は彼女が死ん（　）と思った。」
  tagged `n3-da-mono-da`. These are 死んだ + ものだと思う ("assumed that"), not the nostalgic
  〜たものだ "used to" that 5121/5122 correctly show.
- `gf:n3:5249` 「教育のおかげで私は今日の（　）。」 tagged `n3-you-ni-natta`. It parses as
  [今日のよう]になった ("became like today"), i.e. 名詞＋のように, not the potential-acquisition
  〜ようになった of 5246 to 5248.
- `gf:n3:5256` 「見た（　）よ。」 tagged `n3-koto-wa-nai`. This is 〜たことはない (experience), a
  different point from the 「止まることはない」 "no need to" of 5257.
- **`gf:n3:4998`** 「（　）彼らはちょうどテレビを見ている。」 correct `なぜなら`. なぜなら requires a
  からだ／のだ close; the sentence ends 「見ている。」 so the keyed answer produces broken Japanese.
  Every sibling (4995, 4996, 4997, 4999) correctly ends in からさ／からです／からだ. Drop 4998 or
  replace its source sentence.

**Fix:** validate that the blanked span plus its licensing environment actually instantiates the
tagged pattern before emitting the item.

## F7. 12 `context_fill` stems have no context, so a distractor is equally correct (high)

These stems are 4 to 12 characters of pure frame. Any noun of the right class fits, and at least
one distractor does.

| id | stem | keyed | also correct |
|---|---|---|---|
| `cf:n3:4260:2932` | 「（　）が入ってくるよ。」 | 列車 | **犯人** ("the culprit is coming in") |
| `cf:n3:4154:2639` | 「（　）でもある。」 | 美人 | **利口** ("she is also clever") |
| `cf:n3:3411:1744` | 「（　）は少ししかない。」 | 金 | **粉** ("there's only a little flour") |
| `cf:n3:5534:1868` | 「（　）というのは何ですか。」 | 幸福 | **評価** ("what does 'evaluation' mean?") |
| `cf:n3:5513:1966` | 「（　）って何だっけ？」 | 幸せ | **家賃** ("what was 'rent' again?") |
| `cf:n3:1148:2533` | 「すしは（　）のある料理の一つだ」 | 人気 | **栄養** (栄養のある料理 is a fixed collocation) |
| `cf:n3:678:2065` | 「テーブルの（　）にはまだたくさんの料理がある。」 | 上 | **方** (「テーブルの方には…」) |
| `cf:n3:3431:2453` | 「彼女はその（　）持っていたすべてのお金を彼にあげた。」 | 時 | **上** (「その上、持っていた…」) |
| `cf:n3:3401:2534` | 「しかし、（　）はちがっている。」 | 人間 | **女優**, **日常** |
| `cf:n3:3936:2534` | 「それでも、おまえは（　）だ。」 | 人間 | **完全** |
| `cf:n3:3395:1553` | 「（　）が上がり下がりする。」 | 音 | **量** |
| `cf:n3:944:2173` | 「（　）はやさしい声をしている。」 | 正 (a name) | see F4 |

**Fix:** require a minimum stem length and at least one disambiguating content word besides the
blank, or filter the distractor pool by semantic class against the surviving frame.

## F8. `sentence_order`: wrong format, and at least 7 items accept a second correct ordering (high)

**Format.** Real 文の組み立て gives four **phrase-level** chunks inside a fixed frame with a starred
slot. All 300 N3 items instead give 5 to 9 bare Sudachi morphemes, splitting inflection off its
stem: `so:n3:208` pieces are `ステーキ / と / サラダ / の / 食事 / を / し / まし / た`; `so:n3:69` is
`一人 / で / 行か / なく / ちゃ`. Reassembling し＋まし＋た is a morphology drill, not a syntax one,
and fragments like 「行っ」 or 「ほめ」 are not things a learner should be shown as tiles.

**Ambiguity.** Because whole particles are separate tiles, several items can be reordered into a
different grammatical sentence using exactly the same multiset of pieces. The app scores one string,
so a correct answer is marked wrong:

- `so:n3:847` keyed 「これはあっちのより安いよ」; the same pieces build 「**あっちのはこれより安いよ**」,
  which is natural and means the **opposite**.
- `so:n3:684` keyed 「こっちの方があっちのより安いよ」 vs 「**あっちの方がこっちのより安いよ**」, again
  the opposite.
- `so:n3:794` 「兄はギターがとても上手です」 vs 「**ギターは兄がとても上手です**」.
- `so:n3:122` 「彼女は字がすごくうまい」 vs 「**字は彼女がすごくうまい**」.
- `so:n3:745` 「今年は秋が遅いね」 vs 「**秋は今年が遅いね**」.
- `so:n3:800` 「黒い服の女をみた」 vs 「**服の黒い女をみた**」.
- `so:n3:760` 「左の足が痛いです」 vs 「**足の左が痛いです**」.

18 items carry both は and が as separate tiles and are the main risk pool; 4 more carry two の tiles.

**Fix:** chunk at bunsetsu level (noun+particle, verb+auxiliary as one tile), cap at 4 tiles, and
add a uniqueness guard that rejects any item whose tiles admit a second parse the grammar accepts.

## F9. 22 `kanji_reading` / `orthography` items teach a spelling the corpus itself flags as not common (medium)

`corpus/vocab` marks the target form `is_common: false`, and the generator used it anyway. The
`orthography` direction is the harmful one: it asks the learner to *write* おめでとう as 御目出度う.

`kr:n3:1381` / `or:n3:1381` 彼方此方 (あちこち) · `1392` 凡ゆる (あらゆる) · `1396` 有難う (ありがとう) ·
`1397` 或る (ある) · `1413` 行けない (いけない) · `1421` 何れ (いずれ) · `1445` 何時までも (いつまでも) ·
`1456` 否 (いや) · `1474` 嗽 (うがい) · `1545` 御目出度う (おめでとう) · `1628` 可也 (かなり).

None of these is written in kanji in modern Japanese, and 此 / 或 / 謂 / 嗽 / 喋 are not even in
`corpus/kanji` at any level. The same rare spellings also leak into distractor pools across
`context_fill` (偖, 稍, 只, 兎に角, 仮令, 態と, 然も, 丸で, 所為, 凝乎と, 嗽 appear as options).

Root cause: JMdict's `misc` tags were not ingested. `misc` is essentially empty corpus-wide (one
`hum` across all five levels), so the "usually written in kana" (`uk`) flag that would have filtered
these is simply absent.

**Fix:** ingest `misc`, then exclude `uk` senses and `is_common: false` forms from both banks and
from distractor pools.

## F10. 50 `orthography` / `kanji_reading` items are ill-posed because the stem carries no sentence (medium)

Real 表記 and 漢字読み items embed the word in a carrier sentence precisely because a bare string is
ambiguous. Here the stem is a bare kana word (orthography) or a bare kanji word (reading), and 21
kana stems have two or three different keyed answers across the bank:

`いし` → 医師 / 意志 / 意思 · `かんしん` → 感心 / 関心 · `かんじょう` → 勘定 / 感情 ·
`きょうりょく` → 協力 / 強力 · `きかん` → 期間 / 機関 · `きじ` → 生地 / 記事 · `かた` → 型 / 肩 ·
`かち` → 価値 / 勝ち · `かみ` → 上 / 神 · `かげ` → 影 / 陰 · `いらい` → 以来 / 依頼 · `きゅう` → 旧 / 球 / 級 ·
plus いき, いち, おう, おん, か, かし, かわ, かん, がく. On the reading side: `金` → かね / きん,
`柄` → え / がら, `得る` → うる / える.

The bank currently gets away with it (I verified zero collisions between any item's `correct` and its
own distractors), so nothing scores wrong today. But the item is unanswerable in principle: shown
「かんしん」 and four kanji words, the learner has no way to know which homophone is intended, and one
change to the distractor pool turns this into scoring bugs. It also makes the section a vocabulary
recognition test rather than an orthography test, since the three distractors are unrelated words
(`or:n3:1673` きおん → 気温, distractors 流れ / 何処か / 銃) instead of competing spellings of the same
reading.

**Fix:** attach a carrier sentence to every orthography and kanji-reading item (the sentence bank
already links most of these vocab ids), and build distractors as near-miss spellings or near-miss
readings rather than random other words. Some `kanji_reading` distractors are currently
non-competitive to the point of being free marks: `kr:n3:1717` 吸収 offers 「いただきます」;
`kr:n3:1666` 感動 offers 「おおいに」 and 「たいした」; `kr:n3:1401` 合わせる offers the noun 「ものおと」.

## F11. 266 authored Layer-C items are flagged `ai_generated: false` (medium)

| file | items with `layer: C`, `ai_generated: false` |
|---|---|
| `n3_reading_comp.json` | 152 |
| `n3_paraphrase.json` | 57 |
| `n3_usage.json` | 57 |

The Japanese in these fields is authored, not selected. `us:n3:1365`'s three `wrong` sentences
(「クラスの相手はみんな親切だ。」「店の相手に道を聞いた。」「電車で相手に席をゆずった。」) exist nowhere in
the sentence bank; `pp:n3:1365`'s distractors and every `reading_comp` question and option are
likewise written for the item. The flag appears to track the provenance of the *source* sentence
rather than the item, which is why the 14 items in each file whose source sentence was itself
AI-generated are the only ones marked `true`.

Spec §1.2 is explicit that every generated sentence carries `ai_generated: true`. As it stands, a
reviewer filtering on `ai_generated` will skip 266 items of AI-written Japanese.

**Fix:** set `ai_generated: true` on any item containing authored Japanese, and if the source
sentence's provenance is worth keeping, give it its own field (`source_ai_generated`).

## F12. `lp:n3:008` contradicts itself on the showtimes (medium)

> M1: それが、６時のはもう満席で、席がないんだって。さっき窓口で聞いたんだ。
> F1: じゃあ、次は何時？
> M1: **次は７時半。** …
> M1: あ、待って、**７時からの回**ならまだ席が空いてるって。これにしよう。

The man states, from the box office, that the next screening after 18:00 is 19:30, then discovers a
19:00 screening of the same film. Both cannot be true of one schedule, and the listener is asked to
track exactly these times. `design/listening.md` rule 6 requires items be "answerable from the
script ALONE" with coherent turns; the keyed answer (７時) is only reachable by ignoring an earlier
factual statement rather than by hearing it revised.

Minor, same item: the closing line 「どんなに混んでても、始まる前に中に入っておこうね。」 does not fit a
screening they just confirmed has open seats.

**Fix:** change 「次は７時半」 to 「その次は７時半」 with the 7:00 screening introduced as newly checked,
or move the discovered screening to a time that does not contradict "next".

## F13. `lr:n3:tatoeba-11510681`: the keyed reply answers a question the prompt does not ask (medium)

Prompt (real bank sentence, verbatim): 「見たいのかしら？」
Keyed response: 「うん、見たいな。」

The corpus's own translation of that sentence is **"Será que ele quer ver?" / "Does he want to see
it?"**, a third-person musing, not a question addressed to the listener. 〜のかしら is soliloquy;
answering it in the first person is not the natural response, and the item's own Layer-A data says
so. The two distractors (「見た目はいいね。」「もう見せたよ。」) are wrong, so the item is still
*passable*, but the key is not defensible.

**Fix:** swap the prompt for a bank sentence that is genuinely addressed to the listener
(「見たいの？」-shaped), or drop the item. The selection filter for `listening_reply` should exclude
〜かしら / 〜のか soliloquy endings, which reach the listener as questions about a third party.

## F14. `INDEX.md` item counts are stale for two N3 files (low)

`n3_context_fill.json` is declared 400, actual **389**. `n3_text_grammar.json` is declared 137,
actual **94** (31% off). The same drift affects `n4_context_fill` (370/368), `n4_grammar_form`
(300/299), `n4_text_grammar` (88/62), `n5_context_fill` (241/235), `n5_text_grammar` (37/33), which
is outside this slice but the same cause: `removed_items.json` deletions were applied without
regenerating `INDEX.md`.

**Fix:** regenerate `INDEX.md` from the files as part of the export step.

---

## What is clean

- **`listening_task` (18) and `listening_point` (18)** are the strongest part of this slice. Every
  item is internally consistent, the keyed answer is uniquely entailed, and `design/listening.md`
  rule 4 is honoured throughout: every option is something the dialogue actually mentions and then
  rejects. `lp:n3:002` (deadline corrected 25日 → 15日 → 20日), `lt:n3:014` (four apartments filtered
  by rent, floor, noise and distance) and `lt:n3:016` (scholarship paperwork reordered by the clerk)
  are textbook-quality misdirection. The one exception is F12.
- **`listening_gist` (9)** reads as genuine spoken Japanese for the level: broadcast and
  announcement register is right (「発車いたします」「ご来店の皆様にお知らせいたします」), the monologues
  have a real argumentative shape, and the 一番言いたいこと items (004, 007, 008) turn on the speaker's
  stance rather than a keyword. Vocabulary stays at or under N3.
- **`listening_say` (12)** gets the hard part right: every distractor is a *direction-of-benefit* or
  *register* error (〜てあげましょうか vs 〜てもらえますか, 〜させていただく vs 〜ていただく, お飲みしますか
  applied to a customer, こちらこそ used as a first greeting), which is exactly what 発話表現 tests.
- **`listening_reply` (27)**: 26 of 27 are natural, and the distractor craft (homophone traps
  用/曜, 信じる/閉じる, 来る/着る) matches the real section. Register matches between prompt and response
  throughout.
- **`usage` (71)** is the best-built non-listening bank. The three `wrong` sentences per item are
  targeted confusions rather than nonsense: homophone substitutions (神 for 髪/紙 in `us:n3:1633`,
  意外 for 以外 in `us:n3:1408`, 感じ for 漢字 in `us:n3:1655`), near-synonym boundaries (気温 vs 体温
  vs 温度 in `us:n3:1673`, 休暇 vs 休憩 in 1714/1715), and real-world facts (東京県 / 北海道県 /
  大阪県 in `us:n3:1824`). I found no wrong key.
- Mechanically, everything listed at the top of this report passed, including the two checks most
  likely to hide silent scoring bugs: no `kanji_reading` distractor is a real reading of its stem,
  and no `orthography` distractor can be read as its stem kana.

## One paraphrase key worth a second opinion (not counted below)

`pp:n3:1661` 「彼女の日本語と英語力にはいつも感心させられるよ。」 keys 感心 → **感動**. 感心 is admiration
for someone's skill or effort; 感動 is being emotionally moved. The bank itself treats them as
distinct: `pp:n3:1662` uses 感心 as a *distractor* for 関心 → 興味, and `us:n3:1661` marks
「事故のニュースに感心した。」 wrong precisely because that slot wants 感動. Keying 感心 = 感動 in the
paraphrase bank teaches the confusion the usage bank punishes. Suggested key: 「すごいと思う」 or
「えらいと思う」. I am leaving this out of the count because 感心/感動 do overlap in loose speech, but a
native reviewer should settle it.

---

## Counts

| # | Finding | Severity | Items |
|---|---|---|---|
| F1 | `text_grammar` built on non-passages | blocking | 94 |
| F2 | `reading_comp` built on non-passages | blocking | 152 |
| F3 | Fused sentence boundaries in rendered passages | high | 25 |
| F4 | Wrong lexeme cross-link (2 unanswerable / wrong-key) | high | 135 |
| F5 | Stem cut mid-word | high | 15 |
| F6 | Grammar tag does not match the item | medium | 8 |
| F7 | Context-free stem, distractor equally correct | high | 12 |
| F8 | `sentence_order` format + multiple valid orderings | high | 300 (7 proven ambiguous) |
| F9 | Non-common spelling used as target | medium | 22 |
| F10 | Bare stem with no carrier sentence, homophone-ambiguous | medium | 50 |
| F11 | Authored Layer-C items flagged `ai_generated: false` | medium | 266 |
| F12 | `lp:n3:008` self-contradictory showtimes | medium | 1 |
| F13 | `lr:n3:tatoeba-11510681` key does not answer the prompt | medium | 1 |
| F14 | `INDEX.md` counts stale (2 N3 files) | low | n/a |

| | |
|---|---|
| **Items checked** | **2 261** (14 files) |
| **Distinct items flagged** | **892** (39%) |
| Clean, no finding | 1 369 |

Per-file breakdown of items checked: `context_fill` 389 · `grammar_form` 300 · `kanji_reading` 400 ·
`listening_gist` 9 · `listening_point` 18 · `listening_reply` 27 · `listening_say` 12 ·
`listening_task` 18 · `orthography` 400 · `paraphrase` 71 · `reading_comp` 152 · `sentence_order` 300 ·
`text_grammar` 94 · `usage` 71.

Read in the same pass but not part of the slice, and named only as upstream causes:
`corpus/readings/n3.json` (F1, F2, F3), `corpus/vocab/n?.json` (F4, F9), `corpus/sentences/bank.json`
(F4, F8), `corpus/exam_banks/INDEX.md` (F14).
