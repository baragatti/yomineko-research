# Sentence replacements - part 3/3

Adversarial re-selection pass over the lesson→sentence links queued in
`research/reports/lesson_sentence_review.json`. For every violating slot in my slice I looked for a
**real** (Tatoeba, `provenance.ai_generated = false`) replacement that (a) carries the teaching point
the lesson itself unlocks, (b) fits inside the lesson's `cumulative_known_set` under the validator's
own i+1 arithmetic, and (c) matches register. Where no such sentence exists I say so and name the
exact blocker.

`structure_explanation` fields were **not** reviewed (being re-authored by another process).

---

## 1. Scope and method

**Split rule (stable, reproducible).** `int(sha256(lesson_id.encode()).hexdigest(), 16) % 3 == 2`.
That selects **43 of the 123 lessons** in the queue, carrying **88 of the 247 slots**
(86 distinct sentences: `sent:tatoeba-125387` and `sent:tatoeba-85522` each appear in two of my
lessons).

**Gate arithmetic.** I re-implemented check D of `scripts/validate/validate_lesson_gating.py`
exactly - same kanji registry, same `split_mode == "C"` token→vocab resolution, same
`BUDGET = {pre-n5:0, n5:1, n4:2, n3:2}`, same `LEVEL_ORDER` comparison - so every "fits" / "does not
fit" claim below is the number the validator would produce, not an estimate. Nothing in the repo was
modified; the working scripts live under the session scratchpad.

**"Same teaching point" is defined strictly.** A candidate qualifies only if it carries a grammar key
that **the lesson's own `unlocks` list contains**. A shared bare-particle tag (`to`, `de`, `ga`, `mo`)
is not a teaching point, and I reject those matches explicitly in §5. Target-vocab-only matches are
reported separately, because swapping a grammar demo for a vocab demo silently deletes the
demonstration the lesson was built around.

**Slice profile.** 36 slots violate on level alone (load already within budget), 52 exceed the i+1
budget, 25 do both. 30 of the 88 slots point at an AI-generated sentence. Above-level buckets in my
slice: `n5<-n3` 15, `n5<-n4` 9, `n5<-n2` 5, `n5<-n1` 5, `n4<-n3` 21, `n4<-n2` 2, `n3<-n1` 3,
`n3<-n2` 1.

---

## 2. Headline verdict

| Outcome | Slots |
|---|---|
| A compliant replacement carrying a point the lesson unlocks exists | **32** |
| …of which a **real** (non-AI) one exists | **25** |
| …surviving semantic vetting (§5 rejects 3 as spurious tag matches) | **22** |
| …AI-generated only, no real option | **7** |
| No compliant same-point sentence of any kind exists | **56** |

Breakdown of the 56 dead slots:

| Reason | Slots |
|---|---|
| Every other sentence for that point is graded **above the lesson's level** | 28 |
| Sentences exist at level but **all exceed the i+1 budget** | 25 |
| The slot itself demonstrates **nothing the lesson unlocks** | 3 |

**The dominant cause is not sentence choice.** Two upstream data defects (§3, §4) make most of these
slots unfixable by re-selection. Fixing them first converts a large share of the backlog for free;
re-selecting sentences before fixing them will churn the queue and change nothing.

---

## 3. Defect S1 - a lesson unlocks a grammar point but never unlocks the word that *is* the point

**19 of my 43 lessons, 30 grammar points.** The lesson adds e.g. `gram:gp-43` (たくさん) to
`cumulative_known_set.grammar`, but never adds `vocab:1415870` (沢山/たくさん) to
`cumulative_known_set.vocab`. Because the validator counts unknown **vocab** as well as unknown
kanji, every sentence that demonstrates the point therefore carries a permanent cost of ≥1 - which at
the N5 budget of 1 consumes the entire allowance before the sentence has said anything. The lesson is
structurally incapable of showing its own teaching point.

| Lesson | Point (pattern) | Lemma missing from `cumulative_known_set.vocab` |
|---|---|---|
| `les:n5-verbos-04` | `gram:gp-19` する | `vocab:1157170` 為る/する |
| `les:n5-desu-wa-02` | `gram:gp-2` これ | `vocab:1628530` 此れ/これ |
| `les:n5-desu-wa-02` | `gram:gp-3` それ | `vocab:1006970` 其れ/それ |
| `les:n5-numeros-tempo-03` | `gram:gp-43` たくさん | `vocab:1415870` 沢山/たくさん |
| `les:n5-perguntas-03` | `gram:gp-38` どれ | `vocab:1009290` 何れ/どれ |
| `les:n5-perguntas-03` | `gram:gp-40` どの | `vocab:1920240` 何の/どの |
| `les:n5-perguntas-04` | `gram:gp-29` 誰 | `vocab:1416830` 誰/だれ |
| `les:n5-perguntas-04` | `gram:gp-30` なぜ | `vocab:1577120` 何故/なぜ |
| `les:n5-perguntas-04` | `gram:gp-31` なんで | `vocab:2846738` 何/なん |
| `les:n5-perguntas-04` | `gram:doushite` どうして | `vocab:1451160` 動/どう, `vocab:1157170` 為る/する |
| `les:n5-perguntas-05` | `gram:donna` どんな | `vocab:1009330` どんな |
| `les:n5-perguntas-05` | `gram:douyatte` どうやって | `vocab:1451160` 動/どう, `vocab:1012980` 遣る/やる |
| `les:n5-perguntas-06` | `gram:gp-48` なにか・なにも | `vocab:1577100` 何/なに |
| `les:n5-perguntas-06` | `gram:gp-49` 誰か・どこか | `vocab:1577140` 何処/どこ |
| `les:n5-adjetivos-02` | `gram:gp-5` いい | `vocab:2820690` いい |
| `les:n5-adjetivos-05` | `gram:gp-142` / `gp-45` / `naru` なる | `vocab:1611000` 生る/なる |
| `les:n5-comparacoes-04` | `gram:ga-hoshii` 〜がほしい | `vocab:1547330` 欲しい/ほしい |
| `les:n5-conectando-06` | `gram:tsumori` つもり | `vocab:1382980` 積もり/つもり |
| `les:n5-conectando-06` | `gram:ta-koto-ga-aru` たことがある | `vocab:1313580` 事/こと |
| `les:n5-te-form-01` | `gram:te-kudasai` てください | `vocab:1184280` 下さる/くださる |
| `les:n5-te-form-06` | `gram:naide-kudasai` ないでください | `vocab:1184280` 下さる/くださる |
| `les:n5-verbos-06` | `gram:o-kudasai` をください | `vocab:1184280` 下さる/くださる |
| `les:n4-condicionais-01` | `gram:gp-60` / `gram:tara` 〜たら | `vocab:1157170` 為る/する |
| `les:n4-volitivo-07` | `gram:zehi` ぜひ | `vocab:1374530` 是非/ぜひ |
| `les:n4-aspecto-04` | `gram:gp-65` なおす | `vocab:1599390` 直す/なおす |
| `les:n3-tempo-03` | `gram:n3-ta-totan` たとたん | `vocab:1610870` 途端/とたん |
| `les:n3-causa-02` | `gram:n3-sono-kekka` その結果 | `vocab:1254690` 結果/けっか |

Worked example: `les:n5-verbos-06` teaches **をください**. Four real sentences in the bank demonstrate
it (`tatoeba-197657` ビールをください, `tatoeba-150556` 時間をください, `tatoeba-9930561` それをください,
`tatoeba-227004` お水をください). All four are blocked, and the blocker in all four is the same single
item: `vocab:1184280` 下さる/くださる. Unlock the lemma the lesson teaches and `tatoeba-197657`
ビールをください drops to load 0 - an exact, real, register-matched demo.

Recommended fix (teacher decision, not mine to apply): for each row above, add the lemma to the
lesson's `unlocks` as `{"type": "vocab", "ref": …}`. Check A of the validator recomputes
`cumulative_known_set` from `unlocks`, so no hand-editing of the known set is needed.

---

## 4. Defect S2 - sentence `level` grades that contradict the corpus's own vocab and grammar levels

**22 sentences in my slice** are graded above N5 although **every content word resolved to the vocab
registry is `level: n5` and every grammar key they carry resolves to `level: n5`.** These grades are
what produce the `above_lesson_level` half of the backlog; for several slots the grade is the *only*
violation, so no sentence swap is warranted at all.

| Sentence | Graded | JP | Every resolved vocab / grammar level |
|---|---|---|---|
| `sent:tatoeba-190532` | n3 | 一緒に行かない？ | 一緒 n5, 行く n5; `issho-ni` n5 |
| `sent:tatoeba-190548` | n3 | 一緒に行きます。 | 一緒 n5, 行く n5; `issho-ni` n5 |
| `sent:tatoeba-774809` | n3 | 一緒に来るの？ | 一緒 n5, 来る n5; `issho-ni` n5 |
| `sent:tatoeba-203016` | n3 | チェスを一番どうですか。 | 一番 n5; `ichiban` n5 |
| `sent:tatoeba-223501` | n3 | このテレビがすべてのうちで一番よい。 | テレビ/一番/内/此の/良い all n5; `ichiban` n5 |
| `sent:tatoeba-77848` | n3 | 良かったですね。 | 良い n5; `i-adjectives` n5 |
| `sent:tatoeba-4852` | n4 | もう好きじゃない。 | もう/好き/無い n5; `gp-21` n5 |
| `sent:tatoeba-81558` | n3 | 本当にいい天気だ。 | 天気/本当/いい n5; `gp-5` n5 |
| `sent:tatoeba-82538` | n3 | 忙しいので行けないの。 | 忙しい n5; `node` n5 |
| `sent:tatoeba-78454` | **n1** | 嵐になるだろう。 | 生る n5; `naru`/`gp-45`/`gp-142`/`deshou` all n5 |
| `sent:tatoeba-83696` | **n1** | 雰囲気がいやだった。 | 嫌 n5; `gp-32` n5 |
| `sent:tatoeba-85522` | n2 | 鼻がつまっています。 | 鼻/居る n5; `te-form`/`gp-26` n5 |
| `sent:tatoeba-11795596` | n2 | 8人孫がいます。 | 居る n5; `ga`/`ga-imasu`/`gp-8` n5 |
| `sent:tatoeba-84964` | n3 | 婦長と話したいのですが。 | 話す n5; `tai` n5 |
| `sent:gen-8bc9ce5df658` | **n1** | ドアに鍵がかけてある | ドア/掛ける/鍵/有る n5; `te-aru` n5 |
| `sent:gen-47206ec62227` | n2 | 冷蔵庫にビールが冷やしてある | 有る/冷蔵庫 n5; `te-aru` n5 |
| `sent:gen-2293f3cce26e` | n2 | 机の上に本やペンがある | ペン/机/有る/上/本 n5; `ya` n5 |
| `sent:gen-f1c08a8693dc` | n3 | 電気を消さないで寝ました | 消す/寝る/電気 n5; `naide` n5 |
| `sent:gen-40220286d0b2` | n4 | どの電車に乗りますか | 乗る/電車/何の n5; `gp-40` n5 |
| `sent:gen-4e9dec6558f5` | n4 | この中でどれが好きですか | 何れ/好き/内/此の n5; `gp-38` n5 |
| `sent:gen-f7cec4b420ec` | n3 | くだものの中でりんごが一番好きです | 一番/果物/好き/内 n5; `gp-46` n5 |
| `sent:gen-c94b958f1ed1` | n3 | スポーツの中でサッカーが一番人気です | スポーツ/一番/内 n5; `gp-46` n5 |

Honest caveat: several of these contain words the vocab registry does not resolve (婦長, 雰囲気, 孫,
嵐, つまる), which is the plausible source of the high grade. That is exactly the point - the grade is
being driven by material the i+1 budget check cannot see, so the two numbers disagree and the teacher
gets a violation that no re-selection can clear. The `一緒に` and `一番` sets have no such excuse:
every token in them is registered N5, and all five `issho-ni` sentences and all five `ichiban`
sentences in the bank are graded n3, so `les:n5-convites-01` and `les:n5-comparacoes-02` can never
show their own teaching point at N5 no matter which sentence is picked.

**Least-bad-option verdict.** For these 22, keep the sentence and fix the grade (or add a
`gating_exemptions` entry with the reason). Swapping them out trades a correct, level-appropriate
example for a worse one.

### 4b. The corpus disagrees with itself about six word/point pairs

Checking each S1 point against its own lemma turns up six places where a grammar point is graded
**easier than the word it is made of**. Any sentence demonstrating the point inherits the harder
grade, so it is simultaneously over budget *and* above level - both halves of the violation, from one
inconsistency.

| Grammar point | Point level | Lemma | Lemma level |
|---|---|---|---|
| `gram:gp-19` する | n5 | `vocab:1157170` 為る/する | **n4** |
| `gram:te-kudasai` 〜てください | n5 | `vocab:1184280` 下さる/くださる | **n4** |
| `gram:naide-kudasai` 〜ないでください | n5 | `vocab:1184280` 下さる/くださる | **n4** |
| `gram:o-kudasai` 〜をください | n5 | `vocab:1184280` 下さる/くださる | **n4** |
| `gram:tsumori` つもり | n5 | `vocab:1382980` 積もり/つもり | **n4** |
| `gram:ta-koto-ga-aru` 〜たことがある | n5 | `vocab:1313580` 事/こと | **n4** |

This accounts for 8 of my dead slots on its own (`les:n5-verbos-04`, `les:n5-verbos-06`,
`les:n5-te-form-01` ×2, `les:n5-te-form-06`, `les:n5-conectando-06` ×2, and the する half of
`les:n4-condicionais-01`). Per spec §1.5 every level tag carries `level_confidence` and
`level_sources`; these six pairs should be reconciled from those sources before any sentence in them
is touched.

---

## 5. Rejected candidates - mechanically compliant, semantically wrong

Three slots pass the tag test but the match does not survive reading. I am **not** proposing these.

- **`les:n5-perguntas-03` / `sent:gen-4e9dec6558f5`** (この中でどれが好きですか). The only compliant
  `gp-38` candidates are `sent:tatoeba-225517` グリーンまでどれくらい？ and `sent:tatoeba-5675047`
  どれくらい？. `gram:gp-38` is labelled *"どれ (qual?, entre três ou mais coisas)"*, but both
  candidates use **どれくらい** ("quanto / quanto tempo") - a different lexical item where どれ is not
  the "which one of three or more" pronoun at all. Using either would teach the wrong thing. The tag
  on those two sentences is itself a defect. **No compliant sentence demonstrates the taught sense of
  どれ.**
- **`les:n5-particulas-lugar-03` / `sent:tatoeba-195443`** (また後で。) and **/ `sent:tatoeba-125387`**
  (諦めないで。). The only compliant `de` candidates are `sent:tatoeba-1057336` でもなんで？ and
  `sent:tatoeba-778974` なんで？. Their `de` tag is the で buried inside **なんで**, not the particle
  で of place/means/instrument that the lesson teaches ("Onde a ação acontece: a partícula で").
  **No compliant sentence demonstrates the taught particle.**

---

## 6. Proposed replacements - slots with a real, vetted candidate (22)

Format: slot → up to three candidates, each with slug, level, computed load against that lesson's
known set, register (pol/pln), and the evidence. `ld=0` means the sentence adds nothing new at all.

### `les:n5-verbos-01` - slot `sent:tatoeba-11795596` (n2, ld 2/1) 8人孫がいます。
Point: `gram:gp-8` ます. Blocked by kanji 孫 + `vocab:1577980` 居る/いる.
1. **`sent:tatoeba-11561754`** n5 ld=1 pol - ポーチにスカンクがいます。 / "Tem um cangambá na varanda."
   Same `gp-8`+`ga-imasu`, same polite register, real.
2. `sent:tatoeba-198311` n5 ld=1 pol - ハウスダストにアレルギーがあります。 / "Ele tem alergia a poeira
   doméstica." *Caveat: the pt asserts a subject ("Ele") the Japanese does not contain; the pt was
   validated against the English, not the JP. Fix the translation before using it as a display pair.*
3. ~~`sent:tatoeba-150175`~~ 痔があります。 / "Tenho hemorroidas." - passes the gate; **do not use**.
   Unsuitable content for a first-lesson display sentence.

### `les:n4-condicionais-03` - slot `sent:tatoeba-80881` (n3, ld 1/2) 無理も通れば道理となる。
Point: `gram:gp-150` 〜ば. The current sentence is a proverb; the lesson objective is "condições
lógicas, relações naturais de causa e efeito e conselhos".
1. **`sent:tatoeba-78723`** n4 ld=2 pln - 来てくださればとてもうれしい。 / "Eu ficaria muito feliz se
   você viesse." A genuine ば conditional with a natural consequence.
2. `sent:tatoeba-80396` n4 ld=0 pol - 明日は来なければいけませんよ。 / "Amanhã você tem que vir, viu?"
   *Caveat: this is なければいけない, a fixed obligation idiom - it shows the ば form but not the
   conditional meaning the lesson is teaching.*
3. `sent:tatoeba-77141` n5 ld=0 pln - 話上手もいれば、聞き上手もいる。 *Caveat: aphoristic/written
   register, and it is the 〜も〜ば〜も enumerative pattern, not a plain conditional.*

### `les:n4-aspecto-02` - slot `sent:gen-fd3b6a8cb10e` (n3, ld 1/2) 朝から雨が降っていた
Point: `gram:te-ita`. All three below are real and load-1.
1. **`sent:tatoeba-79051`** n4 ld=1 pln - 夕方が近づいていた。 / "O entardecer estava se aproximando."
2. **`sent:tatoeba-79053`** n4 ld=1 pln - 夕方から雨だっていっていたよ。 / "Estava dizendo que vai
   chover a partir do fim da tarde, viu." Keeps the weather topic of the sentence being replaced.
3. `sent:tatoeba-74957` n4 ld=1 pln - 今までいったい何をしていたんだ！ *Caveat: confrontational
   register (いったい + んだ！); fine grammatically, harsh as a display example.*

### `les:n4-aspecto-02` - slot `sent:tatoeba-7298759` (n3, ld 1/2) 歩いていくよ。
Point: `gram:te-iku`. Eleven compliant real candidates; best three:
1. **`sent:tatoeba-184877`** n4 ld=0 pln - 外はだんだん明るくなっていく。 / "Lá fora vai ficando cada
   vez mais claro." Textbook "mudança que avança rumo ao futuro", which is objective 2 verbatim.
2. **`sent:tatoeba-12642529`** n4 ld=0 pln - 試していく。 / "Vou continuar tentando."
3. `sent:tatoeba-226220` n4 ld=0 pol - カメラは持っていくのですか。 / "Você vai levar a câmera?"
   (the "levar/ir fazendo" sense, polite).

### `les:n4-aspecto-04` - slot `sent:gen-509ae5ead73c` (n3, ld 2/2) 間違えたので名前を書きなおす
Point: `gram:gp-65` なおす.
1. **`sent:tatoeba-161942`** n4 ld=1 pol - 私は４時に電話をかけなおすつもりです。 / "Eu pretendo ligar
   de novo às 4 horas." The only **real** なおす sentence that fits; register is polite whereas the
   slot is plain, which is an improvement for an N4 display sentence.
   (AI fallbacks if the teacher prefers plain: `sent:gen-72606cd984a7` ld=0, `sent:gen-5dd4e7c0e137`
   ld=1 - both already `ai_generated`, so no provenance gain over the incumbent.)

### `les:n4-conectores-07` - slot `sent:tatoeba-80880` (n3, ld 0/2) 無理をしないように。
Point: `gram:gp-128` ように. Note the slot's load is already 0 - this is a **level-grade violation
only**, so replacing it is optional.
1. **`sent:tatoeba-84691`** n4 ld=0 pln - 父はついてくるように私をせきたてた。 / "Meu pai insistiu para
   que eu fosse junto com ele." Matches objective 1 ("para que / de modo que").
2. **`sent:tatoeba-82971`** n4 ld=0 pln - 母は私に外出しないようにいった。 / "Minha mãe me disse para
   não sair." Matches objective 2 (`ように言う`, indirect command).
3. `sent:tatoeba-4930` n4 ld=0 pln - またいつか風のように走るんだ。 *Caveat: this is ように in the
   simile sense ("como o vento"), which this lesson does not teach.*

### `les:n4-dar-receber-02` - slots `sent:tatoeba-9178394` (n3, ld 2/2) and `sent:tatoeba-118469` (n3, ld 1/2)
Point: `gram:te-morau`. Same candidate set for both.
1. **`sent:tatoeba-190894`** n4 ld=1 pln - 医者に見てもらうべきだと思う。 / "Acho que você deveria ser
   examinado por um médico." Canonical 〜に…てもらう with the に-marked agent the lesson's objective 3
   asks for.
2. **`sent:tatoeba-4562518`** n4 ld=0 pln - これは父に気に入ってもらう。 / "Vou fazer com que meu pai
   goste disto." Also に-marked agent, load 0.
3. `sent:tatoeba-215911` n4 ld=0 pln - じゃあ、言わせてもらうけど。 *Caveat: causative + てもらう
   (させてもらう), one step past the lesson's scope.*

### `les:n4-volitivo-03` - slots `sent:tatoeba-3313205`, `sent:tatoeba-146821`, `sent:tatoeba-5049`
Point: `gram:you-to-omou` / `gram:gp-78`. Same candidate set.
1. **`sent:tatoeba-193348`** n4 ld=0 pln - もっとお金をためようと思うんだ。 / "Estou pensando em juntar
   mais dinheiro." Godan verb → 〜おうと思う, which is objective 2's contrast case.
2. **`sent:tatoeba-11801342`** n4 ld=0 pln - ここにいようと思う。 / "Acho que vou ficar aqui."
   Ichidan verb → 〜ようと思う, the other half of objective 2.
3. `sent:tatoeba-11045111` n4 ld=1 pln - 新しく始めてみようと思う。 / "Acho que vou tentar começar de
   novo (do zero)."

### `les:n4-suposicao-07` - slots `sent:tatoeba-127148` (n3, ld 1/2) and `sent:tatoeba-148753` (n3, ld 1/2)
Point: `gram:tagaru`.
1. **`sent:tatoeba-4117192`** n4 ld=0 pol - 子どもは同じ話を何度でも聞きたがるものです。 / "As crianças
   costumam querer ouvir a mesma história várias e várias vezes." The **only** compliant たがる
   sentence in the bank. *Register note: polite ものです against two plain slots; if both slots are
   replaced they would carry the same sentence, so replace at most one and regrade the other (§4).*

### `les:n4-suposicao-08` - slot `sent:tatoeba-11692639` (n3, ld 0/2) 正しいはずがないよ。
Point: `gram:hazu-ga-nai`. Load already 0 - **level-grade violation only**, replacement optional.
1. **`sent:tatoeba-81586`** n4 ld=0 pln - 本気のはずがないわ。 / "Não tem como você estar falando sério."
2. **`sent:tatoeba-141784`** n4 ld=0 pln - 先生がそんなことを言ったはずがない。 / "Não tem como o
   professor ter dito uma coisa dessas."
3. **`sent:tatoeba-218084`** n4 ld=0 pln - これは本物のダイヤであるはずがない。 / "Isto não pode ser um
   diamante de verdade." (Also `195794`, `209394`, both ld=1.)

### `les:n3-tempo-03` - slot `sent:tatoeba-187075` (n1, ld 2/2) 家に着いたとたん嵐になった。
Point: `gram:n3-ta-totan`.
1. **`sent:tatoeba-167241`** n3 ld=2 pln - 私たちが出かけたとたん雨が降り始めた。 / "Assim que saímos,
   começou a chover." Same abrupt-onset semantics, at level.
2. **`sent:tatoeba-186986`** n3 ld=2 pln - 家を出たとたんに大雨が降り出した。 / "Assim que saí de casa,
   começou a chover forte."
3. `sent:tatoeba-124657` n3 ld=2 pln - 電話を切ったとたんにまた鳴り出した。 / "Assim que desliguei o
   telefone, ele começou a tocar de novo."
All three still cost `vocab:1610870` 途端/とたん - see §3; fixing that unlock drops them to ld≤1.

### `les:n3-intencao-01` - slot `sent:tatoeba-4959` (n1, ld 1/2) まず新しいサイトの概説をしようと思う。
Point: `gram:n3-you-to-omou`.
1. **`sent:tatoeba-10243657`** n3 ld=1 pln - 今回はテストを受けてみようと思うんだ。 / "Desta vez estou
   pensando em fazer a prova."
2. **`sent:tatoeba-13059182`** n3 ld=1 pln - 最近あまり寝ていないので今日は早く寝ようと思う。 / "Como
   ando dormindo pouco ultimamente, hoje pretendo dormir cedo."

### `les:n5-comparacoes-04` - slot `sent:tatoeba-149136` (n5, ld 2/1) 車がほしいですか。
Point: `gram:ga-hoshii`.
1. **`sent:tatoeba-1213043`** n5 ld=1 pol - ワインがほしいですか。 / "Você quer vinho?" が present,
   polite, same interrogative frame as the slot.
2. **`sent:tatoeba-13126479`** n5 ld=1 pol - りんごがほしいですか？ / "Você quer maçã?"
3. `sent:tatoeba-13126478` n5 ld=1 pln - りんごがほしい? (plain variant).
   ~~`sent:tatoeba-1484951`~~ いくらほしい？ - **avoid**: no が, so it cannot carry objective 2
   ("marcar o desejado com が, e não com を").

### `les:n5-comparacoes-05` - slot `sent:tatoeba-84964` (n3, ld 2/1) 婦長と話したいのですが。
Point: `gram:tai`.
1. **`sent:tatoeba-83633`** n5 ld=1 pln - 聞きたい？ / "Quer ouvir?" The only compliant たい sentence.
   Directly serves objective 2 ("perguntar pelo desejo de quem você fala"). *Register note: plain,
   whereas the slot is polite-hedged (のですが); the lesson has no other polite たい option at level.*

### `les:n5-convites-01` - slot `sent:gen-24bb23e4256e` (n5, ld 2/1) ちょっと休みませんか
Point: `gram:masen-ka`.
1. **`sent:tatoeba-172871`** n5 ld=**0** pol - 今からドライブに行きませんか。 / "Que tal a gente dar uma
   volta de carro agora?" Real, polite, costs the learner nothing, and it is a genuine invitation.
   The strongest single swap in the whole slice.

### `les:n5-te-form-01` - slot `sent:tatoeba-85522` (n2, ld 2/1) 鼻がつまっています。
Point: `gram:te-form`.
1. **`sent:tatoeba-167591`** n5 ld=0 pol - 大学を出てから10年になります。 / "Já faz dez anos desde que
   me formei na faculdade." Real て-form connective (てから), polite, load 0.
2. ~~`sent:tatoeba-74924`~~ よし、かかってこい！ - **avoid**: tagged `te-form`, but the verb is the
   imperative 来い in a fight-challenge idiom; a misleading demo for a lesson about polite requests.
   (This slot is also a §4 regrade candidate - 鼻 and 居る are both N5.)

### `les:n5-te-form-06` - slots `sent:gen-f1c08a8693dc` (n3, ld 3/1) and `sent:tatoeba-125387` (n1, ld 1/1)
Point: `gram:naide`.
1. **`sent:tatoeba-144418`** n5 ld=**0** pln - 人をからかわないで。 / "Não zoa as pessoas." The only
   compliant ないで sentence, and it is free. *Semantic note: this is the prohibitive ないで ("não
   faça"), which serves the lesson's third objective; it does **not** demonstrate the "sem fazer /
   em vez de" sense that `gen-f1c08a8693dc` (電気を消さないで寝ました) currently carries. If only one
   slot is replaced, replace `tatoeba-125387` (which is also prohibitive) and keep a "sem fazer"
   example - see §7.*

---

## 7. Slots with no compliant replacement - the honest answer

For these the queue cannot be cleared by re-selection. Each row names the point, how many other
sentences in the bank carry it, and the single item that blocks them all.

### 7a. Blocked by the §3 lemma gap (fix the unlock, and real sentences appear)

| Lesson | Slot | Point | Pool | Blocker in every candidate |
|---|---|---|---|---|
| `les:n5-verbos-04` | `tatoeba-81225` | `gp-19` する | 4 | 為る/する (4/4) |
| `les:n5-desu-wa-02` | `tatoeba-4802` | `gp-3` それ | 4 | 其れ/それ (4/4) |
| `les:n5-numeros-tempo-03` | `tatoeba-122326`, `tatoeba-112055` | `gp-43` たくさん | 4 | 沢山/たくさん (4/4) |
| `les:n5-perguntas-03` | `gen-2f1c4475a858`, `gen-40220286d0b2` | `gp-40` どの | 6 | 何の/どの (6/6) |
| `les:n5-perguntas-04` | `gen-0fdafb9f86e8` | `gp-29` 誰 | 4 | 誰/だれ (4/4) |
| `les:n5-perguntas-05` | `tatoeba-201153`, `tatoeba-9611533` | `douyatte` | 4 | 動/どう + 遣る/やる (4/4) |
| `les:n5-perguntas-05` | `tatoeba-199382`, `tatoeba-199569` | `donna` | 5 | どんな (5/5) |
| `les:n5-perguntas-06` | `gen-532623825322`, `gen-54dd1d1ebf25` | `gp-48` なにか | 6 | 何/なに (6/6) |
| `les:n5-adjetivos-02` | `tatoeba-81558`, `tatoeba-5126`, `tatoeba-77189` | `gp-5` いい | 6 | いい (5–6/6) |
| `les:n5-adjetivos-05` | `tatoeba-78454` | `naru`/`gp-45`/`gp-142` | 13 | 生る/なる (13/13) |
| `les:n5-verbos-06` | `tatoeba-143718` | `o-kudasai` | 4 | 下さる/くださる (4/4) |
| `les:n5-te-form-01` | `tatoeba-124708`, `tatoeba-146189` | `te-kudasai` | 4 | 下さる/くださる (4/4) |
| `les:n5-conectando-06` | `tatoeba-137646` | `tsumori` | 4 | 積もり/つもり (4/4) |
| `les:n5-conectando-06` | `tatoeba-3460693` | `ta-koto-ga-aru` | 5 | 事/こと (5/5) |
| `les:n3-causa-02` | `tatoeba-211124` | `n3-sono-kekka` | 2 | 結果/けっか (2/2) |

The ください family needs one extra decision. `gram:te-kudasai` and `gram:o-kudasai` are both graded
**n5**, but `vocab:1184280` 下さる/くださる is graded **n4** - the corpus contradicts itself about the
same word. That is why every ください sentence in the bank is graded n4 and why the four slots in
`les:n5-verbos-06` and `les:n5-te-form-01` are unfixable: adding the vocab unlock clears the budget
(`tatoeba-197657` ビールをください and `tatoeba-140998` 前に行ってください both drop to ld 0) but the
n4 sentence grade still trips `above_lesson_level` against an n5 lesson. Resolve the vocab/grammar
level disagreement first; the four slots then clear on their own.

### 7b. Blocked by a single unknown **kanji** shared by the whole pool

| Lesson | Slot(s) | Point | Pool | Blocking kanji |
|---|---|---|---|---|
| `les:n5-convites-01` | `tatoeba-190532`, `tatoeba-190548`, `tatoeba-774809` | `issho-ni` | 4 | 緒 (4/4) |
| `les:n5-comparacoes-02` | `tatoeba-203016`, `tatoeba-223501` | `ichiban` | 5 | 番 (5/5) |
| `les:n5-comparacoes-02` | `gen-f7cec4b420ec`, `gen-c94b958f1ed1` | `gp-46` | 4 | 番 (4/4) |
| `les:n5-adjetivos-06` | `tatoeba-4852` | `gp-21` 好き | 4 | 好 (4/4) |
| `les:n4-aspecto-02` | `tatoeba-12462035` | `tsuzukeru` | 6 | 続 (6/6) |
| `les:n4-forma-simples-02` | `gen-238f14601cdc` | `gp-129` って感じ | 5 | 感 (5/5) |
| `les:n4-conectores-07` | `gen-e41bdeadc5f1` | `gp-125` ように祈る | 4 | 祈 (4/4) |
| `les:n3-perspectiva-03` | `tatoeba-11013866` | `n3-ni-kurabete` | 4 | 比 (4/4) |

These are the cleanest cases in the whole report: the lesson teaches a point whose written form
requires one kanji the course has not introduced. Either the lesson should unlock that kanji, or the
display should be forced to kana (`show="furigana"` is already used elsewhere in the bodies), or the
pair belongs in `gating_exemptions.json` with that reason. `一緒に` and `一番` are both registered N5
vocabulary, so gating them out of their own N5 lessons is indefensible either way.

### 7c. Genuinely thin coverage - authoring needed

| Lesson | Slot(s) | Point | Situation |
|---|---|---|---|
| `les:n5-desu-wa-02` | `tatoeba-229628` | `gp-4` あれ | 4 candidates, all graded n4 (あれはキジです。 ld=0). Regrade or author. |
| `les:n5-perguntas-06` | `tatoeba-201028` | `gp-49` どこか | 5 candidates, all above level and all ≥ld 4. Author a kana-only どこか sentence. |
| `les:n5-perguntas-06` | `gen-c737b9f8b9da` | `ka-ka` | 4 candidates, all AI, all ≥ld 3. Author. |
| `les:n5-particulas-lugar-05` | `tatoeba-182700` | `gp-18` へ行く | 6 candidates, cheapest is AI `gen-145d7fcd0d32` at ld 3. Author. |
| `les:n5-particulas-lugar-06` | `tatoeba-125175`, `gen-59bccb81087b` | `ni-iku` / `gp-28` | Cheapest real is `tatoeba-1510008` パンを買いにいく。 at ld 2 (needs kanji 買 + パン). One unlock away. |
| `les:n5-particulas-lugar-08` | `tatoeba-139686`, `tatoeba-187788` | `to` | Both slots are 何とか idioms tagged `to`; neither demonstrates と as "e / com". Author a と-listing sentence. |
| `les:n5-passado-01` | `tatoeba-83696`, `tatoeba-78700` | `gp-32` だった | 4 candidates, cheapest `tatoeba-4714` at ld 2 (n4). Regrade `78700` (§4-adjacent) or author. |
| `les:n5-te-form-03` | `gen-47206ec62227`, `gen-6d412e5af5e1`, `gen-8bc9ce5df658` | `te-aru` | 5 candidates, all AI or ld≥3; the only real one is `tatoeba-10286281` at ld 3. Author. |
| `les:n5-verbos-01` | `gen-e8f19f968193`, `gen-97a9a63e32d1` | `gp-6` ichidan | 4 candidates, all AI. Author a real-sourced ichidan example. |
| `les:n5-conectando-01` | `tatoeba-82538` | `node` ので | 4 candidates, cheapest `tatoeba-85318` at ld 1 but graded n4. Regrade or author. |
| `les:n4-volitivo-07` | `gen-c1a790a4c31e`, `gen-e4c675e9ca2d` | `gp-83` まい | 4 candidates, all AI, all above level. Author - 〜まい is `['formal','literary']`, so a real source matters more here, not less. |

### 7d. The slot demonstrates nothing the lesson unlocks (3)

- `les:n5-adjetivos-02` / `sent:tatoeba-77848` 良かったですね。 - tagged `i-adjectives`, but the lesson
  only unlocks `gram:gp-5` (いい). The sentence is in fact a **perfect** demo of objective 2 (the
  irregular past 良かった). The defect is the tag, not the link: add `gp-5` to the sentence's `grammar`
  and regrade it from n3 (§4).
- `les:n5-te-form-03` / `sent:tatoeba-85522` 鼻がつまっています。 - tagged `gp-26`/`te-form`; the lesson
  unlocks `te-iru`/`te-aru`. ています **is** 〜ている + ます, so again the tag is the problem.
- `les:n5-te-form-04` / `sent:tatoeba-5107` 疲れているんだ。 - `grammar: []`, no tags at all, so nothing
  links it to `gp-36`/`gp-37`. Its only violation is the n3 grade against an n5 lesson while its
  resolved vocab (疲れる, 居る) is all n5. Tag it and regrade it; do not replace it.

---

## 8. Candidates that pass the gate but must not be used

Flagged so the teacher does not pick them up from a mechanical query later. All are gate-compliant in
at least one of my lessons.

| Sentence | Why not |
|---|---|
| `sent:tatoeba-150175` 痔があります。 / "Tenho hemorroidas." | Medical/embarrassing content in a first-contact N5 lesson. |
| `sent:tatoeba-74924` よし、かかってこい！ | Tagged `te-form`, but it is imperative 来い in a fight-challenge idiom. |
| `sent:tatoeba-76536` でももヘチマもないわ。 | Opaque idiom; compliant in `les:n5-desu-wa-02` (lesson 2 of the course). |
| `sent:tatoeba-230591` あの男ももう上がったりだ。 | Opaque idiom (上がったり); compliant in four of my lessons. |
| `sent:tatoeba-227750` おくびにも出すな。 / `sent:tatoeba-193048` やぶへびを出すな。 | Both idioms, both compliant in `les:n5-particulas-lugar-03` (N5 lesson 3 of that topic). |
| `sent:tatoeba-3567598` 生まれてこなければよかった。 / "Eu queria nunca ter nascido." | Compliant in `les:n5-adjetivos-02`; dark content for a lesson about weather and flavour adjectives. |
| `sent:tatoeba-1484951` いくらほしい？ | Lacks が, so it contradicts objective 2 of `les:n5-comparacoes-04`. |
| `sent:tatoeba-225517` / `sent:tatoeba-5675047` どれくらい | Mis-tagged `gp-38`; どれくらい is not どれ "which of three or more". |
| `sent:tatoeba-1057336` / `sent:tatoeba-778974` なんで | Mis-tagged `de`; the で is inside なんで, not the particle で. |

---

## 9. Count table

| Class | Checked | Flagged |
|---|---|---|
| Lessons in slice (`sha256(lesson_id) % 3 == 2`) | 43 | 43 (all carry ≥1 violating slot by construction) |
| Lesson→sentence slots | 88 | 88 |
| Distinct sentences behind those slots | 86 | 86 |
| **Slots with a proposed real, vetted replacement** | 88 | **22** |
| Slots with a compliant candidate rejected as a spurious tag match | 88 | 3 |
| Slots where only AI-generated candidates fit (no provenance gain) | 88 | 7 |
| Slots with no compliant same-point sentence at all | 88 | 56 |
| - blocked by the §3 missing-lemma unlock (§7a) | 56 | 23 |
| - blocked by one shared unknown kanji (§7b) | 56 | 12 |
| - thin coverage, authoring required (§7c) | 56 | 18 |
| - slot demonstrates nothing the lesson unlocks (§7d) | 56 | 3 |
| **S1** lessons where a taught grammar point's own lemma is not in `cumulative_known_set` | 43 | **19** (30 points) |
| **S2** sentences graded above N5 with all resolved vocab **and** grammar at N5 | 86 | **22** |
| **S2b** grammar points graded easier than their own lemma vocab (§4b) | 27 pairs checked | **6** |
| Sentence-level grades recommended for review (§4 + `tatoeba-5107` from §7d) | 86 | 23 |
| Mis-tagged `grammar` keys found (`gp-38` on どれくらい, `de` on なんで, missing tags on 77848 / 85522 / 5107) | 86 | 7 |
| Translation defect found in passing (`tatoeba-198311`: pt asserts a subject absent from the JP) | 47 vetted | 1 |
| pt-BR style violations in the 47 candidates I vetted against `design/translation_style.md` (em dash, pt-PT, literal "Quanto a", AI tells) | 47 | **0** |

**Reading of the numbers.** Only 22 of 88 slots (25%) are fixable today by picking a different real
sentence. 23 more become fixable the moment the §3 unlocks land, and 12 more once the §7b kanji
question is settled - so **57 of 88 are reachable without authoring a single new sentence**, provided
the two upstream defects are fixed first. Of the rest: 3 need re-tagging rather than anything else
(§7d), 7 can only be swapped for other AI-generated sentences (no provenance gain, so leave them),
and 21 genuinely need authoring - the 18 in §7c plus the 3 whose only mechanical matches I rejected
in §5. Re-selecting sentences before §3 and §4 are addressed would move the frozen baseline numbers
without improving a single lesson.
