# QA sweep: sentence replacements, part 2 of 3

Scope: the lesson/sentence pairs in `research/reports/lesson_sentence_review.json` whose **lesson** falls in
my third of the split. Read-only pass; nothing in `corpus/`, `course/`, `scripts/`, `contracts/`,
`prototype/` or `db/corpus.sqlite` was touched.

**Split rule (stable, reproducible):** `int(md5(lesson_id.encode()).hexdigest(), 16) % 3 == 1`.
That selects **39 lessons / 67 violating slots** out of the 123 lessons / 247 slots in the queue.

**Excluded by instruction:** sentence `structure_explanation` fields were not read or judged.

## Method

I re-implemented check D of `scripts/validate/validate_lesson_gating.py` so that every candidate is scored
exactly the way the validator scores the offender:

- `new_kanji` = characters of `jp` that exist in `corpus/kanji/*.json` and are **not** in the lesson's
  `cumulative_known_set.kanji`;
- `new_vocab` = `split_mode == "C"` tokens whose vocab slug is **not** in `cumulative_known_set.vocab`;
- `load = len(new_kanji) + len(new_vocab)`, budget = `{pre-n5: 0, n5: 1, n4: 2, n3: 2}`;
- level fit = `LEVEL_ORDER.index(sentence.level) <= LEVEL_ORDER.index(lesson.level)`.

A candidate is called **compliant** only when it clears both gates, carries the same teaching point, and is
not already displayed by the same lesson. Teaching-point match was taken first from the sentence's own
`grammar` key list, then widened by a surface-pattern search over all 5,889 bank records, because the
`grammar` field is populated on only **2,485 of 5,889** sentences and a tag-only search reports "no
candidate" where good ones exist. Every surviving candidate was then read by eye; a large share of the
machine-compliant hits are false matches and are called out below as traps.

Real (`provenance.ai_generated = false`) is preferred over generated throughout, per spec §1.2.

---

## Headline

**A sentence swap is the right fix for 37 of the 67 slots** (27 with a real human-written sentence, 10 with
an AI-generated one). For 19 the sentence is not the defect: the lesson displays the very word or kanji its
own grammar point is made of and has not unlocked it, so no sentence in any corpus can satisfy that gate.
For 7 more the only failing gate is the sentence's `level` tag and no lower-graded sentence for that point
exists anywhere in the bank, which makes the fix a re-grade rather than a re-selection. 4 slots have nothing
usable and need authoring.

Structural facts worth reading before working the queue top-down:

**(1) Ten of my 39 lessons teach a grammar point whose own written form uses a kanji the lesson has not
unlocked.** Machine-verified against each point's `structure_pattern` / `forms` versus the lesson's
`cumulative_known_set.kanji` (course position in parentheses, out of 322 lessons):

| Lesson (position) | Point | Kanji in the point's own pattern, not yet unlocked |
|---|---|---|
| `les:n5-adjetivos-08` (87) | `no-ga-heta` 〜のが下手 | 手 at `les:n5-kanji-exame-01` (+35) |
| `les:n5-adjetivos-06` (85) | `gp-21` 好き / `gp-22` きらい | 好 at `les:n4-kanji-exame-02` (+132); 嫌 **never unlocked** |
| `les:n4-condicionais-06` (144) | `baai-wa` 場合は | 合 at `les:n4-kanji-exame-01` (+72) |
| `les:n4-forma-simples-04` (128) | `koro-goro` 頃 | 頃 **never unlocked** |
| `les:n4-forma-simples-06` (130) | `gp-86` 〜代 / `gp-99` 真っ | 代 at +3; 真 at +33 |
| `les:n4-aspecto-02` (179) | `tsuzukeru` 続ける | 続 at `les:n3-tempo-03` (+52) |
| `les:n4-aspecto-04` (181) | `gp-65` 〜なおす (直す) | 直 at `les:n3-causa-03` (+65) |
| `les:n4-passiva-03` (195) | `zenzen-nai` 全然〜ない | 全 at +29; 然 at +65 |
| `les:n4-volitivo-04` (154) | `yotei-da` 予定だ | 予 at +83; 定 at +67 |
| `les:n3-causa-02` (245) | `n3-sono-kekka` その結果 | 果 at +1; 結 **never unlocked** |

The same holds on the vocab side: `les:n5-adjetivos-02` teaches `gp-5` いい but unlocks the vocab いい 32
lessons later; `les:n4-oracoes-relativas-01` teaches の中で while `vocab:1423310` 中 (なか) is **never
unlocked by any lesson**; `les:n5-te-form-01` teaches 〜てください while 下さる is unlocked 97 lessons later;
`les:n5-perguntas-04` is titled "Quem e por quê: 誰・…" and unlocks 誰 19 lessons later;
`les:n5-adjetivos-05` teaches `gram:naru` while `vocab:1611000` 生る (なる) is unlocked 8 lessons later.

**(2) The per-teaching-point selection pool is about five sentences by construction.** Across the bank, 233
of 479 grammar keys carry exactly 5 tagged sentences, the median is 5, and 290 keys (61 %) have 5 or fewer.
Three to five of those are usually already displayed by the lesson under review, so "find a compliant
replacement carrying the same point" often has a search space of two or three sentences, all of which
inherit the same missing-unlock problem as the one being replaced.

Two smaller cross-cutting artifacts inflate loads across the slice:

- `vocab:1157170` 為る (する) is unlocked only at `les:n4-conectores-01`, **course position 206 of 322**. Six
  of my 67 slots are pushed over budget by する alone, including slots in n5 lessons 90+ positions earlier.
- kanji 彼 is unlocked at `les:n3-limites-04` (position 283) while the vocab 彼 (かれ) is unlocked at
  `les:n4-oracoes-relativas-01` (position 132). 彼 appears as "new kanji" in **11** of my 67 slots, the
  earliest at position 87, while the word it writes is already taught. Kanji unlocks are not dragged by the
  vocab that uses them.
- Kanji displayed in my slice that **no lesson ever unlocks**: 頃, 鼻, 授, 囲, 雰, 結, 泣, 換, 荷, 嵐, 訳, 僕,
  星, 孫 (14 characters).

**(3) A defect the queue cannot show: くれる is linked to 暮れる in 68 bank sentences.** In
`corpus/sentences/bank.json`, the benefactive くれる is linked to `vocab:1514960` = **暮れる** ("escurecer,
anoitecer") instead of `vocab:1269130` 呉れる. Both てくれる examples of the lesson that *teaches* てくれる
carry it:

```
les:n4-dar-receber-02  (unlocks gram:te-kureru)
  sent:tatoeba-1680856  教えてくれるか？      token くれる -> vocab:1514960  暮れる "escurecer"
  sent:tatoeba-994516   私に教えてくれる？    token くれる -> vocab:1514960  暮れる "escurecer"
  cumulative_known_set: 暮れる present, 呉れる (vocab:1269130) absent
```

Because the wrong slug happens to be in that lesson's known set, the gate passes and **these two pairs never
entered the review queue at all**, while any UI that renders a vocab chip shows the learner "escurecer" on
the lesson's own teaching point. Blast radius: 68 sentences, e.g. `sent:tatoeba-10355885` 聞いてくれてありがとう,
`sent:tatoeba-11735124` 運転の仕方は、親が教えてくれたんだ, `sent:gen-472669116bc6` 母がお茶をいれてくれた.
Fix: re-link the benefactive くれる to `vocab:1269130` and unlock that word in `les:n4-dar-receber-02`.

---

## Per-slot findings

Notation: `load/budget`, `mode` = how the lesson renders the slot. A `featured` slot (40 of the 67) is
dissected word by word by the prose immediately around it, so a swap there is **never a drop-in**: the
paragraph has to be rewritten too. `card` slots (27) are usually safe to swap in place.

### Group A. Swap available, real sentence, same teaching point (27 slots)

**`les:n4-oracoes-relativas-01` / `sent:tatoeba-155677`** (n3, load 5/2, card)
`私は人ごみのなかで彼女を見つけた。` Slot teaches the physical "no meio de" sense of の中で.
1. `sent:tatoeba-125820` n4, load 1 (鳥) `鳥が木々の中でさえずっている。` "Os pássaros estão cantando entre as árvores."
2. `sent:tatoeba-80121` n4, load 1 `木の中でさえずっている鳥を見てごらん。` "Olha o passarinho cantando na árvore."
3. `sent:tatoeba-201917` n4, load 0 `テントの中ではなくて外で食べよう。` "Vamos comer lá fora em vez de dentro da barraca."
All plain register, matching the current plain 見つけた. Caveat: they write 中 in kanji while the slot uses the
kana spelling のなかで; the body already says the two spellings are the same thing, so one line of prose
absorbs it. Also unlock `vocab:1423310` 中, or candidates 1 and 2 stay at load 1 for a reason that has
nothing to do with the sentence.

**`les:n5-adjetivos-02` / `sent:tatoeba-77189`** (n5, load 3/1, card)
`話してもいいですか。` The body admits the problem itself: "O verbo 話す, que ainda não estudamos".
1. `sent:tatoeba-13158601` n5, load 1 (いい) `出てもいいですか。` "Posso sair?"
Same 〜てもいい permission pattern, same です register, 出る already known. Clean drop-in that also removes the
body's apology. Only one compliant candidate exists; the runner-up `sent:tatoeba-79201` 遊びに行ってもいい？
is graded n3 and casual.

**`les:n5-adjetivos-02` / `sent:tatoeba-5126`** (n5, load 3/1, card)
`10ヶ国語を話せたらどんなにかっこいいだろう！` Beyond the gate, this pick is wrong on its own terms: it needs
たら **and** the potential 話せる, neither taught at position 81, in a lesson whose objective is "qualidades
do dia a dia".
1. `sent:tatoeba-3488338` n5, load 1 `いいなあ。` "Que inveja!"
2. `sent:tatoeba-195847` n5, load 1 `まあ、いいけど。` "Bem, por mim tudo bem..."
3. `sent:tatoeba-202862` n5, load 1 `ちょっといいですか。` "Você tem um minuto?"
All three are いい as the bare adjective, which is the lesson's point. Their load of 1 **is** いい itself, so
all three go to load 0 once the lesson unlocks the word it teaches (see Group C).

**`les:n5-passado-01` / `sent:tatoeba-78700`** (n5, load 3/1, featured)
`来る日も来る日も雨だった。` Slot teaches [substantivo] + だった. The 来る日も来る日も framing is not the point and
carries 来 / 雨 / 日.
1. `sent:tatoeba-198603` n5, load 0 `ネズミでした。` "Era um rato." (noun + でした, the polite half the body
   introduces two lines later)
2. `sent:tatoeba-11016226` n5, load 0 `そうだったかなあ。` "Será que era assim mesmo?"
3. `sent:tatoeba-78728` n5, load 1 (来) `来たのはメアリーだけだった。` "Só a Mary veio."
Trap avoided: `sent:tatoeba-79755` 夜だった is load 2 (夜 as both kanji and vocab) and fails.

**`les:n4-aspecto-01` / `sent:gen-1f6fd836c289`** (n1, load 3/2, featured)
`赤ちゃんが急に泣き出した` (泣 never unlocked; 急 at +28).
1. `sent:tatoeba-10880163` **real**, n5, load 0 `何を言い出すかな？` Genuine 言い出す, but the "suddenness" the
   body teaches is weak here (言い出す reads as "bring up a topic").
2. `sent:gen-8593e9bbdbc5` AI, n4, load 2 `犬が大きな声で吠え出した` Better sense fit, same shape as the current
   sentence.
Traps: `sent:tatoeba-193048` やぶへびを出すな and `sent:tatoeba-227750` おくびにも出すな are load 0 and
machine-compliant but are opaque idioms, unusable at N4. `sent:tatoeba-171717` 今日はむしろ外出したくない matches
the string 出した but is 外出する. The 思い出す family (`218501`, `9131020`, `222763`) is the lexicalised verb
"lembrar", not the aspectual auxiliary.

**`les:n4-aspecto-02` / `sent:tatoeba-12462035`** (n3, load 3/2, featured) `勉強を続けることにしました。`
The tag search reports zero compliant candidates because every *tagged* 続ける sentence writes 続 in kanji and
続 is not unlocked until +52. The surface search finds two real ones written in kana:
1. `sent:tatoeba-141672` **real**, n4, load 0 `先生はどんどん話しつづけた。` "O professor continuou falando sem parar."
   Tokens: `話し:話す / つづけ:つづける`, so it is the genuine compound, not a homograph. Its `grammar` key is
   `gp-59`, which is why the tag search missed it.
2. `sent:tatoeba-78150` **real**, n4, load 1 (為る is not involved; load is 旅行) `旅行をつづけてもいいですか。`
   "Posso continuar minha viagem?"
Candidate 1 is a strict improvement: same point, zero unknown items, and it drops the ことにする that the
current sentence drags in two topics early. This slot does **not** need the 続 unlock to be repaired.

**`les:n4-aspecto-02` / `sent:gen-fd3b6a8cb10e`** (n3, load 1/2, featured) `朝から雨が降っていた`
Level-only failure (降 is +103, but load 1 is inside budget).
1. `sent:tatoeba-79053` n4, load 1 (夕) `夕方から雨だっていっていたよ。` Keeps the rain scene the prose uses.
2. `sent:tatoeba-79051` n4, load 1 (夕) `夕方が近づいていた。` "O entardecer estava se aproximando."
3. `sent:tatoeba-74957` n4, load 1 (為る) `今までいったい何をしていたんだ！` Strong ていた, but the tone is a
   reprimand; use as a card, not as the featured dissection.
Trap: the 〜ていただけませんか family (`146797`, `149514`, `80735`) matches the string ていた at load 0 but is
て + いただく, a different point.

**`les:n4-aspecto-02` / `sent:tatoeba-7298759`** (n3, load 1/2, featured) `歩いていくよ。` Level-only.
1. `sent:tatoeba-226220` n4, load 0 `カメラは持っていくのですか。` Physical 〜ていく, not yet used in the lesson.
2. `sent:tatoeba-205366` n4, load 0 `それはもっていくつもりはなかったんだ。` Same physical sense, casual.
3. `sent:tatoeba-184877` n4, load 0 `外はだんだん明るくなっていく。` The change-over-time sense; already quoted in
   the prose, so it would duplicate.

**`les:n4-forma-simples-06` / `sent:gen-6de90943b937`** (n3, load 3/2, featured) `毎月の電話代を払う`
1. `sent:tatoeba-12049630` **real**, n4, load 2 `毎年の服代っていくら？` The only real 〜代 sentence in the bank
   that fits. Register is casual (って / いくら？) against the current plain 払う, so the "conta paga todo mês"
   line needs rewording.
2. `sent:gen-f4c05abf2f88` AI, n4, load 1 `今月の電気代が高かった`
3. `sent:gen-9f252c76d0fd` AI, n4, load 1 `タクシー代は二千円でした`
All three still carry 代 as unknown kanji, which is the lesson's own teaching target (Group C).

**`les:n4-aspecto-04` / `sent:gen-509ae5ead73c`** (n3, load 2/2, featured) `間違えたので名前を書きなおす`
Level-only failure.
1. `sent:tatoeba-161942` **real**, n4, load 1 `私は４時に電話をかけなおすつもりです。` "Eu pretendo ligar de novo às 4 horas."
2. `sent:gen-5dd4e7c0e137` AI, n4, load 1 `この作文をもう一度書きなおす` Closest to the current sentence.

**`les:n4-dar-receber-02` / `sent:tatoeba-9178394`** (n3, load 2/2, card) `明日このラジオ直してもらうよ。` and
**`les:n4-dar-receber-02` / `sent:tatoeba-118469`** (n3, load 1/2, featured) `彼に来てもらう。`
Both are level-only failures. Shared pool:
1. `sent:tatoeba-9076386` n4, load 1 (貸) `いとこに千円貸してもらったんだ。` "Peguei mil ienes emprestados com meu
   primo." The most natural everyday てもらう in the bank; found only by surface search (no `grammar` key).
2. `sent:tatoeba-190894` n4, load 1 (医) `医者に見てもらうべきだと思う。` The textbook てもらう; べき is N3, flag it.
3. `sent:tatoeba-4562518` n4, load 0 `これは父に気に入ってもらう。` Grammatically clean, semantically strained pt.
Rejected: `sent:tatoeba-215911` じゃあ、言わせてもらうけど。is causative + てもらう, harder than the point itself.
Honest read: candidate 1 is a genuine improvement on `9178394`; for `118469` (a two-word featured slot that
the prose dissects particle by particle) the current sentence is fine and a re-grade is cheaper.

**`les:n4-forma-simples-01` / `sent:gen-a57fa0b2f6c3`** (n3, load 2/2, card) `彼はもう来たかな` and
**`les:n4-forma-simples-01` / `sent:gen-f626c3374153`** (n3, load 2/2, featured) `明日は晴れるかな`
Both level-only. (明 is unlocked at +10, 晴 at +185.) The tag search reports one AI candidate because these
sentences are untagged; the surface search finds ten real ones:
1. `sent:tatoeba-11016226` n5, load 0 `そうだったかなあ。` Also demonstrates the かなあ lengthening the body describes.
2. `sent:tatoeba-10780343` n5, load 0 `車で来るんじゃないかな。` "Acho que eles vêm de carro, não é?"
3. `sent:tatoeba-189637` n5, load 0 `雨になっちゃうんじゃないかなあ。` Keeps the weather scene of the current featured slot.
Also `sent:tatoeba-3316580` トム早く来ないかなあ (load 1), `sent:tatoeba-190376` 一千万円くらいかな？ (load 0).
Register: all casual plain form, exactly what the body specifies. The lesson's かしら and かい halves also have
real compliant material that is not being used (`11510681` 見たいのかしら？, `12296518` 一言いいかしら？,
`188171` 何かあったかい。, all load 0).
Trap: a naive substring search for かな returns 今しかない / やるしかない / 行かなくちゃ, all load 0 and irrelevant.

**`les:n4-keigo-01` / `sent:tatoeba-174190`** (n2, load 2/2, featured) `交換台でございます。` (換 never unlocked.)
Level-only, and the retail-politeness register is exactly right for the body's "linguagem do atendimento".
1. `sent:tatoeba-1336459` n4, load 0 `こちらはサービスでございます。` "Isto é cortesia da casa."
2. `sent:tatoeba-347297` n4, load 1 `これはなんでございますか。` "O que é isto?"
3. `sent:gen-8c01f644ede3` AI, n4, load 0 `本日は休みでございます`
Candidate 1 is strictly better: same register, same point, zero unknown items, and it keeps the shop-counter
scene the paragraph builds.

**`les:n4-keigo-05` / `sent:gen-59401317dba3`** (n2, load 2/2, featured) `私が荷物をお持ちします` (荷 never unlocked.)
1. `sent:tatoeba-214606` **real**, n4, load 1 (為る) `すでにお話ししました。` "Eu já te falei isso." A genuine
   お〜する humble, human-written, found only by surface search.
2. `sent:gen-e6f956627466` AI, n4, load 1 `道をお教えします`
3. `sent:gen-d58ab4004378` AI, n4, load 1 `後で先生にお電話します`
Caveat on candidate 1: the body's dissection is built on the が of 私が and on a service-counter scene, so the
paragraph needs rewriting; candidate 3 preserves the scene at the cost of being AI-generated.

**`les:n5-adjetivos-05` / `sent:tatoeba-78454`** (n1, load 2/1, card) `嵐になるだろう。` (嵐 never unlocked.)
The tag search's "compliant" hits here are でしょう sentences, which would drop the slot's actual point.
Real になる candidates:
1. `sent:tatoeba-147804` n5, load 1 `出かける時間になった。` "Chegou a hora de sair." (noun + になる)
2. `sent:tatoeba-167591` n5, load 1 `大学を出てから10年になります。` "Já faz dez anos desde que me formei."
Both are the [substantivo] になる molde the checklist names. Their load of 1 is `vocab:1611000` 生る itself,
unlocked 8 lessons after the lesson that teaches なる.

**`les:n5-conectando-04` / `sent:gen-d354f1465606`** (n3, load 2/1, featured) `頭が痛いんです` (頭 +105, 痛 +189.)
1. `sent:tatoeba-137685` n5, load 0 `大雨で外出できなかったんです。` "É que não pude sair por causa da chuva forte."
2. `sent:tatoeba-1874351` n5, load 0 `ごめんなさい。時間があまりないんです。` "Desculpe. É que não tenho muito tempo."
3. `sent:tatoeba-201017` n5, load 0 `どこから出るんですか。` The んですか question the body moves to next.
Candidate 1 carries the "explicar / justificar" nuance the paragraph teaches better than the current sentence
does, at zero cost. The dissection paragraph has to be rewritten around it.

**`les:n5-te-form-01` / `sent:tatoeba-85522`** (n2, load 2/1, card) and
**`les:n5-te-form-02` / `sent:tatoeba-85522`** (n2, load 2/1, card) `鼻がつまっています。`
(鼻 is never unlocked as kanji; the vocab 鼻 arrives at +3.) The same sentence is displayed by two lessons,
so it produces two queue rows. Cheapest repair: **drop it from `les:n5-te-form-02`** (that lesson already
shows `167591` and `74924` for `gp-26`, so nothing is lost) and replace it in `les:n5-te-form-01`:
1. `sent:tatoeba-202782` n5, load 0 `ちょっと見ているだけです。` "Só estou dando uma olhada."
2. `sent:tatoeba-203622` n5, load 0 `ただ見ているだけです。` "Estou só olhando."
3. `sent:tatoeba-193803` n5, load 0 `もしもし、来ていますか。` Keeps a telephone scene, but the pt "Alô, você está
   aí?" is a loose reading of 来ていますか; flag for the translation queue if used.
Note: `167591` and `74924` carry `gp-26`, which `les:n5-te-form-01` has not unlocked yet (it is unlocked by
the next lesson), so they are not valid fillers for te-form-01.

**`les:n3-intencao-04` / `sent:tatoeba-123214`** (n1, load 1/2, card) `内訳はどのようにしましょう？` (訳 never unlocked.)
Level-only. Also weak on its own terms: the pt "Como você gostaria do detalhamento?" is a business-invoice
reading of どのように, not the "vamos procurar" effort sense the lesson teaches.
1. `sent:tatoeba-79798` n3, load 0 `問題点からそれないようにしましょう。` "Vamos procurar não fugir do assunto."
2. `sent:tatoeba-81579` n4, load 0 `本題からそれないようにしましょう。` "Não vamos nos desviar do assunto principal."
3. `sent:tatoeba-85431` n3, load 0 `必要以上にお金を使わないようにしなさい。` The なさい variant, negative habit.
Candidate 1 is the exact ようにしましょう of the objective, at zero cost.

**`les:n4-condicionais-05` / `sent:gen-acbd1be494f0`** (n3, load 1/2, featured) `明日晴れるといいです` (晴 +167.)
Level-only.
1. `sent:tatoeba-1323453` n5, load 0 `お会いできるといいですね。` "Tomara que eu possa vê-lo, né?"
2. `sent:tatoeba-183265` n4, load 1 `気に入ってくれるといいな。` "Tomara que você goste." (This sentence is itself
   an instance of the 暮れる mis-link in finding (3); its load of 1 is that wrong slug.)
Trap: `sent:tatoeba-192500` リムジンを使うといいですよ is tagged `gp-82` but is the **advice** sense of といい
("é melhor você usar"), not the "tomara que" sense `gram:gp-82` defines. Do not use it here.
Caveat: `sent:tatoeba-10365237` また会えるといいですね is already displayed in this lesson, so candidate 1 would
sit next to a near-twin, and the body's dissection is built on 晴れる. Re-grading is defensible here.

**`les:n4-conectores-04` / `sent:tatoeba-225929`** (n1, load 1/2, featured) `きみだけでなく僕も悪い。` (僕 never unlocked.)
Level-only.
1. `sent:tatoeba-182118` n4, load 0 `魚だけでなく、肉も食べなさい。` "Coma não só peixe, mas também carne."
2. `sent:tatoeba-219715` n4, load 0 `この本はおもしろいだけでなく、ためにもなる。` The adjective-first variant the body
   describes (寒いだけでなく) but never shows.
3. `sent:tatoeba-153017` n4, load 0 `私は父だけでなくむすこも知っている。`
All keep the X だけでなく Y も molde with the も the body highlights.

**`les:n4-suposicao-07` / `sent:tatoeba-127148`** (n3, load 1/2, card) `男性は男らしく見せたがる。` and
**`les:n4-suposicao-07` / `sent:tatoeba-148753`** (n3, load 1/2, featured) `若者は、外国に行きたがる。`
Both level-only. Shared pool, enough real material for both slots:
1. `sent:tatoeba-4117192` n4, load 0 `子どもは同じ話を何度でも聞きたがるものです。` Third-person たがる, tendency reading.
2. `sent:tatoeba-168859` n4, load 0 `子どもは大人のようにふるまいたがる。` Tokens `ふるまい:ふるまう / たがる:たがる`, clean.
Trap: `sent:tatoeba-84479` 父は私を医者にしたがっている is machine-compliant and tagged `garu-gatteiru`, but its
token layer parses したがっ as **したがう (従う, "obedecer")**, which contradicts its own pt "quer fazer de mim um
médico". Fact layer and meaning layer disagree; do not ship it until the parse is resolved.
Trap: a substring search for がって / がり returns 上がって, ふさがっている, ちがっている, all irrelevant.

**`les:n4-suposicao-01` / `sent:gen-aaabebd8cac1`** (n3, load 1/2, featured) `明日は雨が降ると聞いた` (降 +97.)
Level-only.
1. `sent:tatoeba-85318` **real**, n4, load 0 `病気だときいたので。` "Soube que você estava doente." Genuine
   reportive と聞いた written in kana; its `grammar` key is `node`, which is why the tag search missed it.
   Caveat: it is a fragment ending in ので, so it works as a card, not as the featured dissection.
2. `sent:gen-2ee7a48d3f5d` AI, n4, load 0 `先生は来週休むと聞いた`
3. `sent:gen-34386829da8e` AI, n4, load 0 `あの店のラーメンはおいしいと聞いた`
Trap: `sent:tatoeba-229897` ある外国人が私に駅がどこにあるかと聞いた is tagged `to-kiita` but is 聞く = "perguntou",
the opposite of the reportive sense the lesson teaches.

**`les:n4-volitivo-04` / `sent:tatoeba-11669238`** (n3, load 2/2, card) `寝ることにするよ。くたくたなんだ。` (寝 +156.)
Level-only.
1. `sent:tatoeba-12655912` **real**, n4, load 2 (始 / 為る) `それでは、さっそく始めることにしましょう。` "Então, vamos
   começar logo." The only real ことにする in reach; exactly at budget.
2. `sent:gen-20a639cf6fd7` AI, n4, load 1 `今年は車を買わないことにした` Also demonstrates the negative ことにする the
   body describes and never shows.
3. `sent:gen-cf75fafa538c` AI, n4, load 2 `毎日日本語を勉強することにします`

### Group B. Swap available, but only AI-generated (10 slots)

Each has a compliant same-point candidate, none of it human-written. Per spec §1.2 these are a last resort;
all carry `ai_generated: true` and `needs_review: true`.

| Lesson | Slot | Best AI candidate | Note |
|---|---|---|---|
| `les:n4-oracoes-relativas-03` | `sent:gen-aab58020a36f` (n1, 4/2) | `sent:gen-8e0c7b9e8f05` n4 load 2 `夏休みの間ずっと国にいた` | Correct 間 + ずっと pattern the body teaches. Only candidate in the bank. |
| `les:n4-conectores-02` | `sent:gen-04b97adbf861` (n3, 2/2) | `sent:gen-0ab0c59d39db` n4 load 0 `この店は安いです それに料理もおいしいです` | **Trap:** all 7 "real" それに hits (`205638` それに近づくな, `12020382` それについて教えて, `10124175` すべてはそれによるね, `9819095`, `3588637`, `225975`, `9086385`) are the demonstrative それ + に, not the additive conjunction. |
| `les:n4-conectores-02` | `sent:gen-9e22bc1d7301` (n3, 2/2) | `sent:gen-184103a3a456` n4 load 0 `この店は安いです それに近いです`; `sent:gen-b2484d35484c` n4 load 0 | Same trap. Two distinct AI sentences exist, so both それに slots can be filled without repeating one. |
| `les:n4-passiva-04` | `sent:gen-d3bba30db3a5` (n3, 2/2) | `sent:gen-079400c974bb` n4 load 1 `そのことは少しも気にしていない` | Level-only. |
| `les:n4-passiva-04` | `sent:gen-2be04a058c05` (n3, 1/2) | `sent:gen-04494a7c911c` n4 load 0 `この町には外国人が少なくない` | Level-only. |
| `les:n4-passiva-04` | `sent:gen-9054c26d99b8` (n3, 1/2) | `sent:gen-db5ebe4f0057` n4 load 0 `母が作れない料理はない`; `sent:gen-7e1666c42c97` n4 load 0 | Level-only. The whole すこしも / すくなくない / ない〜はない family has **zero** real sentences. **Trap:** `sent:tatoeba-199501` 学べないことはない is tagged `n3-nai-koto-wa-nai`, a different point. |
| `les:n4-suposicao-05` | `sent:gen-f1b038704e1c` (n3, 2/2) | `sent:gen-36ca3f1e0ef9` n4 load 1 `外は寒いとみえて、みんなコートを着ている` | Level-only. Only とみえて sentence besides the offender. |
| `les:n4-conectores-04` | `sent:gen-1bce6041e175` (n3, 1/2) | `sent:gen-7586c0111a3c` n4 load 0 `あの店は安いしおいしい` | **Trap:** the one "real" hit `sent:tatoeba-148197` 秋はいつしか冬となった is tokenised `いつ / し / か`, i.e. いつしか, not the connective し. Its `grammar: ["shi"]` key is a false positive of surface matching. |
| `les:n4-suposicao-06` | `sent:gen-3c81102a6182` (n2, 1/2) | `sent:gen-643252b8067c` n4 load 0 `山の上から海が見られる` | **Trap:** `sent:tatoeba-144648` 人に足下を見られるなよ is the passive 見られる, not "pode ser observado". |
| `les:n4-suposicao-06` | `sent:gen-f2f39d1b820e` (n3, 1/2) | `sent:gen-55fcc9eb04bd` n4 load 0 `このレストランはイタリア風の料理を出す` | **Trap:** every real 風の hit is 風 = "vento" (`1772006`, `4930`, `11483540`, `180453`, `11980988`), not the 〜ふう style suffix. |

### Group C. The unlock model is the defect, not the sentence (19 slots)

Replacing the sentence cannot help: the item that fails the gate **is** the thing the lesson teaches. The
repair is an edit to `unlocks` (and in some cases the lesson's course position), after which the current
sentence or a named alternative becomes legal.

| Lesson | Slot(s) | Missing item the lesson itself teaches | After the unlock |
|---|---|---|---|
| `les:n5-adjetivos-08` | `sent:tatoeba-99645` | `vocab:1185200` 下手 (+18); kanji 手 (+35), 覚 (never), 彼 (+196) | Best real 〜のが下手 is `sent:tatoeba-9851557` あいつは教えるのが下手だよ, load 3 → 1, but graded n4 and rough-casual (あいつ). **Every** のが下手 sentence in the bank is n4+, so an n5 lesson can never satisfy the level gate for this point. |
| `les:n5-perguntas-04` | `sent:gen-0fdafb9f86e8` | `vocab:1416830` 誰 (+19) | The lesson sits at position 49 with **zero** kanji unlocked, so any sentence containing kanji fails by construction. `sent:gen-fd13c46e11a7` これは誰のかさですか drops to load 1 = budget but stays graded n4. A kana-only 誰 example has to be authored or the 誰 unlock moved here. |
| `les:n4-condicionais-06` | `sent:tatoeba-189516`, `sent:tatoeba-2349428` | `vocab:1355810` 場合 (+4); kanji 合 (+72) | `sent:tatoeba-2349428` (the card) drops to load 2 = budget and becomes legal as-is. For the featured slot, `sent:tatoeba-81179` 万一の場合はここへ電話をください drops to load 2 and matches the "aviso real" framing better than the current 雨天/運動会/中止 (load 4 even after the unlock). |
| `les:n5-adjetivos-02` | `sent:tatoeba-81558` | vocab いい (+32) | No compliant いい + substantivo sentence exists even after the unlock. Closest is `sent:tatoeba-229345` いい人だけどイマイチね (n5, load 1), which does show いい + 人 but ends in the slangy イマイチ. Authoring is the honest answer for this featured slot. |
| `les:n5-adjetivos-04` | `sent:tatoeba-230319` | `vocab:1584930` 余り (+2) and `vocab:1529520` 無い (+7), both used by the body's own explanation | The only other 〜くなかった sentence, `sent:tatoeba-11117435` とにかく行きたくなかったの (load 1 = budget), is **already displayed in this same lesson**. Pool exhausted: either unlock the two words, or simply drop this slot and keep `11117435`. |
| `les:n5-adjetivos-06` | `sent:tatoeba-4852` | kanji 好 (+132), 嫌 (never), vocab ない (+5) | Zero compliant 好き / きらい sentences at any load. All 好き sentences are n4+. |
| `les:n5-conectando-06` | `sent:tatoeba-137646`, `sent:tatoeba-3460693` | `vocab:1382980` 積もり (+13); `vocab:1313580` 事 (+30) | Zero compliant つもり or たことがある sentences; every one in the bank is n4 and carries the same word. |
| `les:n5-te-form-01` | `sent:tatoeba-124708`, `sent:tatoeba-146189` | `vocab:1184280` 下さる (+97) | Zero compliant てください sentences at n5. `sent:tatoeba-140998` 前に行ってください and `sent:tatoeba-150641` 時間があったら来てください both go to load 0 after the unlock but stay graded n4. |
| `les:n5-particulas-lugar-04` | `sent:gen-b61f5e94a2f1` | `vocab:1414170` 大人 (+14); `vocab:1611000` 生る (+22) | The lesson teaches に + なる 22 lessons before なる is unlocked. Zero compliant になる sentences. The lesson's destination sense has plenty (`sent:tatoeba-197681` ビーチに行きましょう, `sent:tatoeba-193955` モールに行きましょうか, both load 0), so the cheapest repair is to move the になる section out of this lesson. |
| `les:n4-oracoes-relativas-03` | `sent:tatoeba-79723` | `vocab:1215230` 間 あいだ (+45, `les:n4-aspecto-02`) | Kanji 間 is already known; only the word is not. No real temporal 間に candidate exists either way (Group D). |
| `les:n4-forma-simples-04` | `sent:gen-86b281bbdbef`, `sent:gen-e00af1726629` | kanji 頃, **never unlocked by any lesson** | Both violating slots are precisely the two 頃-in-kanji examples, which is the lesson's whole point. After unlocking 頃: `sent:gen-b7992e71a26e` 三時頃に駅で会いましょう and `sent:gen-5462fa2cb22f` 学生の頃はお金がなかった both hit load 0 (both AI, both graded n2). The ごろ-in-kana half is fine and has real material (`1751944` 何時ごろ来たの？, `187461` 何時ごろ？, both load 0 real). **Trap:** a substring search for ころ returns 37 compliant hits, all of them ところ. |
| `les:n4-passiva-03` | `sent:tatoeba-9478237` | kanji 全 (+29), 然 (+65); `vocab:1395620` 全然 (+5) | This slot exists specifically to show the kanji spelling ("Esta usa a escrita em kanji: 全然"), so the kana alternatives (`159061` 私はビールはぜんぜん飲みません, `176432` 計画は雨でぜんぜんだめになった, both load 1 real) defeat its purpose. After the unlock, `sent:tatoeba-213988` センスが全然ないわ goes to load 0 but stays n3. |
| `les:n4-volitivo-04` | `sent:tatoeba-84326`, `sent:tatoeba-9489164` | `vocab:1543240` 予定 (+8); kanji 予 (+83), 定 (+67) | All eight 予定 sentences carry the same three items, so zero are compliant. Because 予 and 定 are N3 kanji, an N4 lesson can never show 予定 in kanji under the current model; this needs either a kanji-unlock pull or a documented exemption. |
| `les:n3-causa-02` | `sent:tatoeba-211124` | kanji 結 (**never unlocked**), 果 (+1, the very next lesson); `vocab:1254690` 結果 (+35) | Zero compliant その結果; the only two siblings (`211110`, `211125`) are graded n1 with the same load 3. A single reorder (果 is unlocked one lesson later) plus a 結 unlock fixes it. **Trap:** the による search returns `sent:tatoeba-202786` 銀行によってくる and `sent:tatoeba-202824` その店によって行きませんか, both 寄る ("dar uma passada"), not the agentive による. |

### Group D. Nothing exists; needs authoring (4 slots)

**`les:n4-oracoes-relativas-01` / `sent:gen-82ddc26749ff`** (n3, load 4/2, featured) `果物のなかでりんごが好きです`
The slot teaches の中で as "dentre um conjunto" (the comparison/superlative use). Every other sentence with
that sense is worse: `sent:tatoeba-115590` 彼は、英語がクラスのなかでかなり遅れている (load 5),
`sent:gen-e550b112cef4` クラスのなかで彼が一番背が高いです (load 5), `sent:gen-341f2978c261` (load 6). The only
near miss is `sent:gen-4e9dec6558f5` この中でどれが好きですか (AI, load 1) which is the right sense but is already
displayed by `les:n5-perguntas-03`. Author one `[grupo] の中で [item] が一番 …` frame from the lesson's known
set, and unlock `vocab:1423310` 中 in the same edit.

**`les:n4-oracoes-relativas-04` / `sent:gen-b2c4b3ced962`** (n3, load 5/2, card) `子供が遊んでいる間に夕食を作った`
(供 +118, 遊 +168, 夕 +58, 作 +6.) The only compliant ているあいだに sentence in the bank,
`sent:gen-4590c1e65a70` 電車を待っている間に本を読んだ, is **already the featured example in this same lesson**.
The 後で half has real compliant material and is fine. Needs one authored ているあいだに sentence.

**`les:n4-oracoes-relativas-03` / `sent:gen-c5f31a4dfcad`** (n3, load 4/2, card) `母が出かけている間に宿題を終えた`
(宿 +155, 終 +24, 題 +9.) Zero compliant temporal 間に. **Trap:** the compliant 間に hits are
`sent:tatoeba-147804` 出かける時間になった (時間), `sent:tatoeba-143754` 水は人間にとって大切だ (人間) and
`sent:tatoeba-80125` 木の間に家が見える (spatial "entre as árvores"). None teaches the point.

**`les:n5-passado-01` / `sent:tatoeba-83696`** (n1, load 4/1, featured) `雰囲気がいやだった。`
(雰 and 囲 are never unlocked; the sentence is graded n1 inside an n5 lesson.) The slot teaches
[adjetivo-な] + だった. No real な-adjective + だった sentence exists at n5 with load ≤ 1; the nearest,
`sent:tatoeba-85319` 病気だったんだよ, is load 3. This is the worst single pair in my slice. Author one from the
lesson's own な-adjectives (the noun half is already covered by `198603` ネズミでした, proposed in Group A).

### Group E. Re-grade the sentence, do not replace it (7 slots)

The load is inside budget and the teaching point is correct; the only failing gate is the sentence's `level`
tag, and no lower-graded sentence for the point exists. Replacing them trades a correct example for a worse one.

| Lesson | Slot | Grade | Why re-grade |
|---|---|---|---|
| `les:n5-adjetivos-02` | `sent:tatoeba-77848` `良かったですね。` | n3, 1/1 | A four-mora fixed reaction, the exact 良かった the body teaches. Zero other 良かった sentences exist. Swapping to 大きいね / バナナおいしい (both load 0) deletes the past-tense point. Load 1 is kanji 良 (+186); rendering it as よかったですね also clears the gate. |
| `les:n4-conectores-02` | `sent:gen-2983acf2a91a` `彼は親切で、また元気だ` | n3, 1/2 | The additive また the body needs. All 19 real また hits are the adverbial "de novo" (`また明日`, `また来週！`, `また始まった`, `じゃ、またね`), a different sense. Load 1 is kanji 彼. |
| `les:n4-keigo-05` | `sent:gen-6c6ce0d2199b` `よろしくお願いいたします` | n3, 1/2 | A fixed formula the body explicitly says to memorise whole. Load 1 is kanji 願 (+97). Real いたします material does exist for the *other* half of the point (`10982402` お知らせいたします, `9226991` 事前にお知らせいたします, `80525` 明日の朝に電話をいたします, `126195` 朝食は何時にいたしますか, all n4 load 0) and should be added as extra cards, but none of them can replace the greeting formula itself. |
| `les:n4-suposicao-01` | `sent:tatoeba-104331`, `sent:tatoeba-106462` | n3, 1/2 each | Load 1 is kanji 彼 in both, unlocked at +98, although the word 彼 was taught 53 lessons **before** this one. Every と言われている sentence in the bank is n3+ and carries 彼 or 徳 (`87034` 彼女は病気だと言われている, `123545` 道徳家であると言われている, `163538` 私の姉は美人だと言われている). Fixing the 彼 kanji unlock clears the load; the level gate needs a grading decision. |
| `les:n5-comparacoes-06` | `sent:tatoeba-3073523` `高すぎる！` | n4, 1/1 | Inside budget. All すぎる sentences are graded n4 because 過ぎる is an n4 word, so an n5 lesson teaching すぎる can never show a compliant example. Either accept the n4 grade or move the lesson into N4. Load 1 is `vocab:1195970` 過ぎる, unlocked at +39. |
| `les:n5-verbos-05` | `sent:tatoeba-11795596` `8人孫がいます。` | n2, 1/1 | Inside budget (孫, a kanji no lesson unlocks). The only untaken alternative, `sent:tatoeba-198311` ハウスダストにアレルギーがあります (n5, load 0), is an あります sentence, not いますone, and its pt "Ele tem alergia..." invents a subject the Japanese does not have. Every other がいます sentence is already displayed by this lesson. |

---

## What I would ask the teacher to decide first

1. **Should `unlocks` be required to cover the lexemes of the grammar point the lesson teaches?** If yes, 19
   of my 67 slots resolve by an `unlocks` edit and the sentence bank never has to be touched. A validator
   rule ("every kanji and content word appearing in an unlocked grammar point's `structure_pattern` must be
   in that lesson's `cumulative_known_set`") would catch all ten lessons in the table at the top of this
   report, plus the vocab cases.
2. **Should kanji unlocks be dragged by vocab unlocks?** 彼 alone accounts for 11 of my 67 loads.
3. **Is `level` on a sentence allowed to exceed the level of the lesson that teaches its point?** Today every
   すぎる, てください, つもり, 場合は and 予定 sentence is graded above the n5/n4 lesson that introduces it, because
   the sentence inherits the level of the word being taught. Under the current rule those lessons are
   permanently unfixable by selection.
4. **`vocab:1157170` 為る (する) at course position 206** and **`vocab:1423310` 中 (なか) never unlocked** look
   like plain omissions rather than pedagogical choices.
5. **The benefactive くれる must be re-linked from `vocab:1514960` 暮れる to `vocab:1269130` 呉れる** (68
   sentences). This one is not a queue item: it passes the gate today and would ship silently.

---

## Counts

Every slot is assigned to exactly one recommended action, so groups A to E partition the 67.

| Recommended action | Lessons | Slots |
|---|---|---|
| Assigned and checked (md5 bucket 1) | 39 | 67 |
| **A.** Swap: real sentence, same teaching point, proposed | 21 | **27** |
| **B.** Swap: AI-generated candidate only | 6 | **10** |
| **C.** Fix the `unlocks`, not the sentence | 14 | **19** |
| **D.** Nothing exists; author a new sentence | 4 | **4** |
| **E.** Re-grade the sentence, keep it in place | 6 | **7** |
| | | **67** |

| Cross-cutting tallies | Count |
|---|---|
| Slots with zero compliant same-point candidate of any provenance (C + D + E) | 30 of 67 |
| Slots whose only failing gate is the `level` tag (load within budget) | 33 of 67, across 20 lessons |
| Slots failing budget only (level fits) | 9 of 67 |
| Slots failing both gates | 25 of 67 |
| Offending sentences that are real / AI-generated | 38 / 29 |
| Lessons teaching a point whose own **kanji** they have not unlocked | 10 of 39 |
| Lessons teaching a point whose own **vocab** they have not unlocked | 17 of 39 |
| Slots inflated by `vocab:1157170` 為る (する), unlocked at course position 206 | 6 |
| Slots inflated by kanji 彼, unlocked ~150 positions after the word 彼 | 11 |
| Distinct kanji displayed in this slice that no lesson ever unlocks | 14 |
| Vocab displayed in this slice that no lesson ever unlocks | 1 (`vocab:1423310` 中) |
| Candidate traps found by machine matching and rejected by hand | 17 |
| Slots the tag-only search wrongly reported as hopeless (real candidate found by surface search) | 4 |
| Bank sentences with くれる mis-linked to 暮れる (outside the queue) | 68 |
| `featured` slots (a swap also requires rewriting the surrounding prose) | 40 of 67 |
| `card` slots (a swap is usually a drop-in) | 27 of 67 |

Nothing in this report was written to `corpus/`, `course/`, `scripts/`, `contracts/`, `prototype/` or
`db/corpus.sqlite`. Sentence `structure_explanation` fields were not reviewed, per instruction.
