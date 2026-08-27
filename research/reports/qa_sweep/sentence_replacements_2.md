# QA sweep: sentence replacements, part 2 of 3

Scope: the lesson/sentence pairs in `research/reports/lesson_sentence_review.json` whose **lesson** falls in
my third of the split. Read-only pass; nothing in `corpus/`, `course/`, `scripts/`, `db/` was touched.

**Split rule (stable, reproducible):** `int(md5(lesson_id.encode()).hexdigest(), 16) % 3 == 1`.
That selects **39 lessons / 67 violating slots** out of the 123 lessons / 247 slots in the queue
(the other two thirds are buckets 0 and 2).

**Excluded by instruction:** sentence `structure_explanation` fields were not read or judged.

## Method

I re-implemented the gate from `scripts/validate/validate_lesson_gating.py` (check D) so that every
candidate is scored the same way the validator scores the offender:

- `new_kanji` = characters of `jp` that exist in `corpus/kanji/*.json` and are **not** in the lesson's
  `cumulative_known_set.kanji`;
- `new_vocab` = `split_mode == "C"` tokens whose vocab slug is **not** in `cumulative_known_set.vocab`;
- `load = len(new_kanji) + len(new_vocab)`, budget = `{pre-n5:0, n5:1, n4:2, n3:2}`;
- level fit = `LEVEL_ORDER.index(sentence.level) <= LEVEL_ORDER.index(lesson.level)`.

A candidate had to clear **both** gates to be listed as compliant. Teaching-point match was taken first
from the sentence's own `grammar` key list, then widened by a hand-verified string search over the whole
5,889-sentence bank (because the `grammar` field is populated on only 2,485 of 5,889 records, a
tag-only search reports "no candidate" where perfectly good ones exist). Every candidate below was then
read by eye: several machine-compliant hits are **false matches** and are called out as traps.

Real (`provenance.ai_generated = false`) is preferred over generated throughout, per spec §1.2.

---

## Headline

**A sentence swap is the right fix for only 36 of the 67 slots** (23 with a real sentence, 13 with an
AI-generated one). For 20 of them the sentence is not the
defect: the lesson displays the very word or kanji its own grammar point is made of, and has not unlocked
it. No sentence in any corpus can satisfy that gate, because every well-formed example of the point
contains the missing item. For 7 more the only failing gate is the sentence's `level` tag, and no
lower-graded sentence for that point exists anywhere in the bank, so the fix is a re-grade, not a
re-selection. 4 slots have nothing at all and need authoring.

Two structural facts drive most of this and are worth the teacher's attention before any per-slot work:

**(1) Ten of my 39 lessons teach a grammar point whose own written form uses a kanji the lesson has not
unlocked.** Machine-verified against each point's `structure_pattern` / `forms` versus the lesson's
`cumulative_known_set.kanji`:

| Lesson (course position) | Point | Kanji in the point's own pattern, not yet unlocked |
|---|---|---|
| `les:n5-adjetivos-08` (87) | `no-ga-heta` 〜のが下手 | 手 → unlocked at `les:n5-kanji-exame-01` (+35) |
| `les:n5-adjetivos-06` (85) | `gp-21` 好き / `gp-22` きらい | 好 → `les:n4-kanji-exame-02` (+132); 嫌 → **never unlocked** |
| `les:n4-condicionais-06` (144) | `baai-wa` 場合は | 合 → `les:n4-kanji-exame-01` (+72) |
| `les:n4-forma-simples-04` (128) | `koro-goro` 頃 | 頃 → **never unlocked** |
| `les:n4-forma-simples-06` (130) | `gp-86` 〜代 / `gp-99` 真っ | 代 → +3; 真 → +33 |
| `les:n4-aspecto-02` (179) | `tsuzukeru` 続ける | 続 → `les:n3-tempo-03` (+52) |
| `les:n4-aspecto-04` (181) | `gp-65` 〜なおす (直す) | 直 → `les:n3-causa-03` (+65) |
| `les:n4-passiva-03` (195) | `zenzen-nai` 全然〜ない | 全 → +29; 然 → +65 |
| `les:n4-volitivo-04` (154) | `yotei-da` 予定だ | 予 → +83; 定 → +67 |
| `les:n3-causa-02` (245) | `n3-sono-kekka` その結果 | 果 → +1; 結 → **never unlocked** |

The same holds on the vocab side: `les:n5-adjetivos-02` teaches `gp-5` いい but unlocks the vocab いい 32
lessons later; `les:n4-oracoes-relativas-01` teaches の中で but `vocab:1423310` 中 (なか) is **never
unlocked by any lesson in the course**; `les:n5-te-form-01` teaches 〜てください but 下さる is unlocked 97
lessons later; `les:n5-perguntas-04` is titled "Quem e por quê: 誰・…" and unlocks 誰 19 lessons later.

**(2) The per-teaching-point selection pool is ~5 sentences by construction.** Across the bank, 233 of
479 grammar keys carry exactly 5 tagged sentences and the median is 5; 290 keys (61 %) have 5 or fewer.
Three to five of those are usually already displayed in the lesson under review. So "find a compliant
replacement carrying the same point" often has a search space of two or three sentences, all of which
inherit the same unlocked-vocab problem as the one being replaced.

Two smaller cross-cutting artifacts inflate loads across the slice:

- `vocab:1157170` 為る (する) is unlocked only at `les:n4-conectores-01`, **course position 206 of 322**.
  Six of my 67 slots are pushed over budget by する alone, including slots in n5 lessons 90+ positions
  earlier. Any sentence with a する verb is over budget for most of the course.
- kanji 彼 is unlocked at `les:n3-limites-04`, but the vocab 彼 (かれ) is unlocked at
  `les:n4-oracoes-relativas-01`, ~180 lessons earlier. 彼 appears as "new kanji" in **11** of my 67 slots
  while the word it writes is already taught. Kanji unlocks are not dragged by the vocab that uses them.
- Kanji displayed in my slice that **no lesson ever unlocks**: 頃, 鼻, 授, 囲, 雰, 結, 泣, 換, 荷, 嵐, 訳, 僕,
  星, 孫 (14 characters).

---

## Per-slot findings

Notation: `load/budget`, `mode` = how the lesson renders the slot. A `featured` slot (40 of the 67) is
dissected word-by-word by the prose immediately around it, so a swap there is **never a drop-in**: the
paragraph has to be rewritten too. `card` slots (27) are usually safe to swap in place.

### Group A. Swap available, real sentence, same teaching point (23 slots)

**`les:n4-oracoes-relativas-01` / `sent:tatoeba-155677`** (n3, load 5/2, card)
`私は人ごみのなかで彼女を見つけた。` Slot teaches the physical "no meio de" sense of の中で.
Compliant real candidates, same sense and same point:
1. `sent:tatoeba-125820` n4, load 1 (鳥) `鳥が木々の中でさえずっている。` "Os pássaros estão cantando entre as árvores."
2. `sent:tatoeba-80121` n4, load 1 `木の中でさえずっている鳥を見てごらん。` "Olha o passarinho cantando na árvore."
3. `sent:tatoeba-189575` n4, load 2 (歌 / 気分) `雨の中で歌いたい気分だ。` "Estou com vontade de cantar na chuva."
Register: all plain, matching the current plain 見つけた. Caveat: all three write 中 in kanji while the
body's slot is the kana spelling のなかで, and the body itself says the two spellings are the same thing,
so the prose survives with a one-line tweak. **Also unlock `vocab:1423310` 中 in this lesson**, or these
candidates stay at load 1 for a reason that has nothing to do with the sentence.

**`les:n5-adjetivos-02` / `sent:tatoeba-77189`** (n5, load 3/1, card)
`話してもいいですか。` The body admits the problem itself: "O verbo 話す, que ainda não estudamos".
1. `sent:tatoeba-13158601` n5, load 1 (いい) `出てもいいですか。` "Posso sair?"
Same 〜てもいい permission pattern, same です register, verb 出る already known. This is a clean
drop-in and removes the body's own apology. (Only one compliant candidate exists; the second-best,
`sent:tatoeba-79201` 遊びに行ってもいい？, is graded n3 and casual.)

**`les:n5-adjetivos-02` / `sent:tatoeba-5126`** (n5, load 3/1, card)
`10ヶ国語を話せたらどんなにかっこいいだろう！` Beyond the gate, this pick is wrong on its own terms: it
needs たら **and** the potential 話せる, neither taught at position 81, in a lesson whose objective is
"qualidades do dia a dia".
1. `sent:tatoeba-3488338` n5, load 1 `いいなあ。` "Que inveja!"
2. `sent:tatoeba-195847` n5, load 1 `まあ、いいけど。` "Bem, por mim tudo bem..."
3. `sent:tatoeba-202862` n5, load 1 `ちょっといいですか。` "Você tem um minuto?"
All three are いい used as the bare adjective, which is the lesson's point. The load of 1 is いい itself,
so all three go to load 0 once the lesson unlocks the word it teaches.

**`les:n5-passado-01` / `sent:tatoeba-78700`** (n5, load 3/1, featured)
`来る日も来る日も雨だった。` Slot teaches [substantivo] + だった. The 来る日も来る日も framing is not the point
and carries 来/雨/日.
1. `sent:tatoeba-78728` n5, load 1 (来) `来たのはメアリーだけだった。` "Só a Mary veio."
2. `sent:tatoeba-198603` n5, load 0 `ネズミでした。` "Era um rato." (noun + でした, the polite half the body
   introduces two lines later)
Trap avoided: `sent:tatoeba-79755` 夜だった is load 2 (夜 as both kanji and vocab) and fails.

**`les:n4-aspecto-01` / `sent:gen-1f6fd836c289`** (n1, load 3/2, featured)
`赤ちゃんが急に泣き出した` (泣 is never unlocked anywhere; 急 is +28).
1. `sent:tatoeba-10880163` **real**, n5, load 0 `何を言い出すかな？` "O que será que vão dizer?"
   Genuine 言い出す, but the "suddenness" the body teaches is weak here.
2. `sent:gen-8593e9bbdbc5` AI, n4, load 2 `犬が大きな声で吠え出した` "O cachorro começou a latir bem alto."
   Better sense fit (sudden onset), same structure as the current sentence.
Trap: `sent:tatoeba-193048` やぶへびを出すな and `sent:tatoeba-227750` おくびにも出すな are load 0 and
machine-compliant but are opaque idioms, unusable at N4. `sent:tatoeba-171717` 外出したくない matches the
string 出した but is 外出する, not the auxiliary.

**`les:n4-aspecto-02` / `sent:gen-fd3b6a8cb10e`** (n3, load 1/2, featured) `朝から雨が降っていた`
Level-only failure (降 is +103 but load 1 is within budget).
1. `sent:tatoeba-79053` n4, load 1 (夕) `夕方から雨だっていっていたよ。` Keeps the rain scene the prose uses.
2. `sent:tatoeba-79051` n4, load 1 (夕) `夕方が近づいていた。` "O entardecer estava se aproximando."
3. `sent:tatoeba-186754` n4, load 0 `火にあたりながらすわっていた。` (ながら is above the lesson, flag it)
Trap: the 〜ていただけませんか family (`146797`, `149514`, `80771`) matches the string ていた and is load 0,
but it is て+いただく, a different point entirely.

**`les:n4-aspecto-02` / `sent:tatoeba-7298759`** (n3, load 1/2, featured) `歩いていくよ。` Level-only.
1. `sent:tatoeba-226220` n4, load 0 `カメラは持っていくのですか。` physical 〜ていく, not yet used in the lesson
2. `sent:tatoeba-184877` n4, load 0 `外はだんだん明るくなっていく。` (already quoted in the prose as the
   change-over-time sense, so it would duplicate)

**`les:n4-forma-simples-06` / `sent:gen-6de90943b937`** (n3, load 3/2, featured) `毎月の電話代を払う`
1. `sent:tatoeba-12049630` **real**, n4, load 2 `毎年の服代っていくら？` "Quanto você gasta com roupa por ano?"
   The only real 〜代 sentence in the bank that fits. Register is casual (って / いくら？) against the
   current plain 払う; the body's "conta paga todo mês" line needs rewording.
2. `sent:gen-f4c05abf2f88` AI, n4, load 1 `今月の電気代が高かった`
3. `sent:gen-9f252c76d0fd` AI, n4, load 1 `タクシー代は二千円でした`
All three still carry 代 as unknown kanji, which is the lesson's own teaching target (see Group C).

**`les:n4-aspecto-04` / `sent:gen-509ae5ead73c`** (n3, load 2/2, featured) `間違えたので名前を書きなおす`
Level-only failure.
1. `sent:tatoeba-161942` **real**, n4, load 1 `私は４時に電話をかけなおすつもりです。` "Eu pretendo ligar de novo às 4 horas."
2. `sent:gen-5dd4e7c0e137` AI, n4, load 1 `この作文をもう一度書きなおす` (closest to the current sentence)

**`les:n4-dar-receber-02` / `sent:tatoeba-9178394`** (n3, load 2/2, card) `明日このラジオ直してもらうよ。` and
**`les:n4-dar-receber-02` / `sent:tatoeba-118469`** (n3, load 1/2, featured) `彼に来てもらう。`
Both are level-only failures. Shared candidate pool:
1. `sent:tatoeba-190894` n4, load 1 (医) `医者に見てもらうべきだと思う。` The textbook てもらう. べき is N3, flag it.
2. `sent:tatoeba-4562518` n4, load 0 `これは父に気に入ってもらう。` Grammatically clean, semantically strained pt.
3. `sent:tatoeba-215911` n4, load 0 `じゃあ、言わせてもらうけど。` Causative + てもらう, harder than the point.
Honest read: none of the three is better than what is already there. Both current sentences fit the
budget; the only complaint is the `n3` grade. Recommend re-grading over swapping.

**`les:n4-forma-simples-01` / `sent:gen-a57fa0b2f6c3`** (n3, load 2/2, card) `彼はもう来たかな` and
**`les:n4-forma-simples-01` / `sent:gen-f626c3374153`** (n3, load 2/2, featured) `明日は晴れるかな`
Both level-only. The tag search reports zero because these are untagged; by hand:
1. `sent:tatoeba-11016226` n5, load 0 `そうだったかなあ。` "Será que era assim mesmo?" (also demonstrates the
   かなあ lengthening the body describes)
2. `sent:tatoeba-10880163` n5, load 0 `何を言い出すかな？` "O que será que vão dizer?"
3. `sent:tatoeba-4732` n4, load 0 `みんなもそうなのかな、と思うことくらいしかできない。` (long, use only as a card)
Register: all casual plain form, exactly what the body specifies. The lesson's かしら and かい halves also
have real compliant material (`11510681` 見たいのかしら？, `12296518` 一言いいかしら？, `188171` 何かあったかい。 all load 0)
that is not being used.
Trap: a naive substring search for かな returns 今しかない / やるしかない / 行かなくちゃ / もう行かなきゃ, all load 0
and all irrelevant.

**`les:n4-keigo-01` / `sent:tatoeba-174190`** (n2, load 2/2, featured) `交換台でございます。`
(換 is never unlocked.) Level-only failure, and the retail-politeness register is exactly right for the
body's "linguagem do atendimento".
1. `sent:tatoeba-1336459` n4, load 0 `こちらはサービスでございます。` "Isto é cortesia da casa."
2. `sent:tatoeba-347297` n4, load 1 `これはなんでございますか。` "O que é isto?"
3. `sent:gen-8c01f644ede3` AI, n4, load 0 `本日は休みでございます`
Candidate 1 is a strictly better slot filler: same register, same point, zero unknown items, and it keeps
the shop-counter scene the paragraph builds.

**`les:n5-adjetivos-05` / `sent:tatoeba-78454`** (n1, load 2/1, card) `嵐になるだろう。`
(嵐 is never unlocked.) The tier matcher's "compliant" hit here is a でしょう sentence, not a になる one;
that would drop the slot's actual point. Real になる candidates:
1. `sent:tatoeba-147804` n5, load 1 `出かける時間になった。` "Chegou a hora de sair." (noun + になる)
2. `sent:tatoeba-167591` n5, load 1 `大学を出てから10年になります。` "Já faz dez anos desde que me formei."
Both are the [substantivo] になる molde the "Leitura" checklist names. Note the lesson still has to unlock
なる: `vocab:2820690` 生る is unlocked at `les:n5-comparacoes-05`, 8 lessons after the lesson that teaches it.

**`les:n5-conectando-04` / `sent:gen-d354f1465606`** (n3, load 2/1, featured) `頭が痛いんです`
(頭 +105, 痛 +189.)
1. `sent:tatoeba-137685` n5, load 0 `大雨で外出できなかったんです。` "É que não pude sair por causa da chuva forte."
2. `sent:tatoeba-201017` n5, load 0 `どこから出るんですか。` (the んですか question the body moves to next)
3. `sent:tatoeba-2154943` n5, load 0 `これなんです。` "É isto."
Candidate 1 carries the "explicar / justificar" nuance the paragraph teaches better than the current
sentence does, at zero cost. The dissection paragraph ("estou com dor de cabeça" versus "é que estou com
dor de cabeça") has to be rewritten around it.

**`les:n5-te-form-01` / `sent:tatoeba-85522`** and **`les:n5-te-form-02` / `sent:tatoeba-85522`**
(n2, load 2/1, card in both) `鼻がつまっています。` (鼻 is never unlocked, as kanji or as vocab before +3.)
The same sentence is displayed by two lessons, so one fix serves both.
1. `sent:tatoeba-193803` n5, load 0 `もしもし、来ていますか。` "Alô, você está aí?" Same ています, keeps the
   telephone scene `les:n5-te-form-01` is built on.
2. `sent:tatoeba-167591` n5, load 0 `大学を出てから10年になります。` (already used by `les:n5-te-form-02`)

**`les:n3-intencao-04` / `sent:tatoeba-123214`** (n1, load 1/2, card) `内訳はどのようにしましょう？`
(訳 is never unlocked.) Level-only. Also worth noting the current pt "Como você gostaria do
detalhamento?" is a business-invoice reading of どのように, not the "vamos procurar" effort sense the lesson
teaches; it is a weak illustration on top of being over-level.
1. `sent:tatoeba-79798` n3, load 0 `問題点からそれないようにしましょう。` "Vamos procurar não fugir do assunto."
2. `sent:tatoeba-83568` n3, load 1 (易) `平易英語で書くようにしなさい。`
3. `sent:tatoeba-172440` n3, load 2 `今後、あなたの仕事を手伝うようにしましょう。`
Candidate 1 is the exact ようにしましょう of the objective, at zero cost.

**`les:n4-condicionais-05` / `sent:gen-acbd1be494f0`** (n3, load 1/2, featured) `明日晴れるといいです`
(晴 +167.) Level-only.
1. `sent:tatoeba-1323453` n5, load 0 `お会いできるといいですね。` "Tomara que eu possa vê-lo, né?"
2. `sent:tatoeba-192500` n4, load 1 (使) `リムジンを使うといいですよ。` (this is the advice sense of といい, a
   different nuance from "tomara"; flag if used)
Caveat: `sent:tatoeba-10365237` また会えるといいですね is already displayed in this lesson, so candidate 1 would
sit next to a near-twin. The body's dissection is built on 晴れる; consider keeping the sentence and
re-grading instead.

**`les:n4-conectores-04` / `sent:tatoeba-225929`** (n1, load 1/2, featured) `きみだけでなく僕も悪い。`
(僕 is never unlocked.) Level-only.
1. `sent:tatoeba-182118` n4, load 0 `魚だけでなく、肉も食べなさい。` "Coma não só peixe, mas também carne."
2. `sent:tatoeba-219715` n4, load 0 `この本はおもしろいだけでなく、ためにもなる。` (the adjective-first variant the body
   describes: 寒いだけでなく)
3. `sent:tatoeba-153017` n4, load 0 `私は父だけでなくむすこも知っている。`
All three keep the X だけでなく Y も molde with the も the body highlights. Candidates 1 and 3 are the
noun-entry case; candidate 2 covers the adjective case the paragraph mentions but never shows.

**`les:n4-suposicao-07` / `sent:tatoeba-127148`** (n3, load 1/2, card) `男性は男らしく見せたがる。` and
**`les:n4-suposicao-07` / `sent:tatoeba-148753`** (n3, load 1/2, featured) `若者は、外国に行きたがる。`
Both level-only. Shared pool:
1. `sent:tatoeba-4117192` n4, load 0 `子どもは同じ話を何度でも聞きたがるものです。` third-person たがる, tendency reading
2. `sent:tatoeba-168859` n4, load 0 `子どもは大人のようにふるまいたがる。`
3. `sent:tatoeba-84479` n4, load 0 `父は私を医者にしたがっている。` (the がっている variant the body contrasts)
Trap: a substring search for がって / がり returns 上がって, ふさがっている, ちがっている, 色の上がり, all irrelevant.

### Group B. Swap available, but only AI-generated (13 slots)

Each of these has a compliant same-point candidate, none of it human-written. Per spec §1.2 these are a
last resort; they all carry `ai_generated: true` and `needs_review: true`.

| Lesson | Slot | Best AI candidate | Note |
|---|---|---|---|
| `les:n4-oracoes-relativas-03` | `sent:gen-aab58020a36f` (n1, 4/2) | `sent:gen-8e0c7b9e8f05` n4 load 2 `夏休みの間ずっと国にいた` | Correct 間+ずっと pattern the body teaches. Only candidate in the bank. |
| `les:n4-volitivo-04` | `sent:tatoeba-11669238` (n3, 2/2) | `sent:gen-20a639cf6fd7` n4 load 1 `今年は車を買わないことにした`; `sent:gen-cf75fafa538c` n4 load 2 `毎日日本語を勉強することにします` | Level-only failure. The first also demonstrates the negative ことにする the body describes and never shows. |
| `les:n4-conectores-02` | `sent:gen-04b97adbf861` (n3, 2/2) | `sent:gen-0ab0c59d39db` n4 load 0 `この店は安いです それに料理もおいしいです` | **Trap:** all 7 "real" それに hits (`205638` それに近づくな, `12020382` それについて教えて, `10124175` すべてはそれによるね …) are the demonstrative それ + に, not the additive conjunction. Do not accept them. |
| `les:n4-conectores-02` | `sent:gen-9e22bc1d7301` (n3, 2/2) | same as above; also `sent:gen-184103a3a456` n4 load 0 `この店は安いです それに近いです` | Same trap. |
| `les:n4-keigo-05` | `sent:gen-59401317dba3` (n2, 2/2) | `sent:gen-e6f956627466` n4 load 1 `道をお教えします`; `sent:gen-d58ab4004378` n4 load 1 `後で先生にお電話します` | The bank has no real お〜する sentence. The real material (`174355` 後でお電話いたします, `10982402` お知らせいたします) is the お〜いたす variant, which the body treats as the next step up. |
| `les:n4-passiva-04` | `sent:gen-d3bba30db3a5` (n3, 2/2) | `sent:gen-e9bb12279da1` n4 load 1 `今日は少しも寒くない` (already in this lesson); `sent:gen-079400c974bb` n4 load 1 `そのことは少しも気にしていない` | Level-only. |
| `les:n4-passiva-04` | `sent:gen-2be04a058c05` (n3, 1/2) | `sent:gen-04494a7c911c` n4 load 0 `この町には外国人が少なくない` | Level-only. |
| `les:n4-passiva-04` | `sent:gen-9054c26d99b8` (n3, 1/2) | `sent:gen-db5ebe4f0057` n4 load 0 `母が作れない料理はない`; `sent:gen-7e1666c42c97` n4 load 0 `この店に売っていない物はない` | Level-only. The whole すこしも / すくなくない / ない〜はない family has **zero** real sentences in the bank. |
| `les:n4-suposicao-05` | `sent:gen-f1b038704e1c` (n3, 2/2) | `sent:gen-36ca3f1e0ef9` n4 load 1 `外は寒いとみえて、みんなコートを着ている` | Level-only. Only とみえて sentence besides the offender. |
| `les:n4-conectores-04` | `sent:gen-1bce6041e175` (n3, 1/2) | `sent:gen-7586c0111a3c` n4 load 0 `あの店は安いしおいしい` | **Trap:** the one "real" hit `sent:tatoeba-148197` 秋はいつしか冬となった is いつしか, not the connective し. |
| `les:n4-suposicao-01` | `sent:gen-aaabebd8cac1` (n3, 1/2) | `sent:gen-2ee7a48d3f5d` n4 load 0 `先生は来週休むと聞いた`; `sent:gen-34386829da8e` n4 load 0 `あの店のラーメンはおいしいと聞いた` | **Trap:** `sent:tatoeba-229897` ある外国人が私に…かと聞いた is 聞く = "asked", the opposite of the reportive と聞いた the lesson teaches. |
| `les:n4-suposicao-06` | `sent:gen-3c81102a6182` (n2, 1/2) | `sent:gen-643252b8067c` n4 load 0 `山の上から海が見られる` | **Trap:** `sent:tatoeba-144648` 人に足下を見られるなよ is the passive 見られる, not "can be observed". |
| `les:n4-suposicao-06` | `sent:gen-f2f39d1b820e` (n3, 1/2) | `sent:gen-55fcc9eb04bd` n4 load 0 `このレストランはイタリア風の料理を出す` | **Trap:** every real 風の hit is 風 = "vento" (`1772006`, `4930`, `11483540`), not the 〜ふう style suffix. |

### Group C. The unlock model is the defect, not the sentence (20 slots)

For these, replacing the sentence cannot help: the item that fails the gate **is** the thing the lesson
teaches. The repair is an edit to `unlocks` (and in some cases the lesson's course position), after which
the current sentence or a named alternative becomes legal.

| Lesson | Slot(s) | Missing item the lesson itself teaches | After the unlock |
|---|---|---|---|
| `les:n5-adjetivos-08` | `sent:tatoeba-99645` | `vocab:1185200` 下手 (+18, `les:n5-convites-04`); kanji 手 (+35) | Best real 〜のが下手 is `sent:tatoeba-9851557` あいつは教えるのが下手だよ, load 3 → 1, but graded n4 and rough-casual (あいつ). **Every** のが下手 sentence in the bank is n4+, so an n5 lesson can never satisfy the level gate for this point. |
| `les:n5-perguntas-04` | `sent:gen-0fdafb9f86e8` | `vocab:1416830` 誰 (+19, `les:n5-particulas-lugar-02`) | `sent:gen-fd13c46e11a7` これは誰のかさですか load 2 → 1 = budget, n4. Still above n5. |
| `les:n4-condicionais-06` | `sent:tatoeba-189516`, `sent:tatoeba-2349428` | `vocab:1355810` 場合 (+4, `les:n4-potencial-02`); kanji 合 (+72) | `sent:tatoeba-2349428` (the card) drops to load 1 and becomes legal as-is. For the featured slot, `sent:tatoeba-81179` 万一の場合はここへ電話をください drops to load 1 and matches the "aviso real" framing better than the current 雨天/運動会/中止. |
| `les:n5-adjetivos-02` | `sent:tatoeba-81558` | vocab いい (+32, `les:n5-conectando-02`) | No compliant いい + substantivo sentence exists even after the unlock. Closest is `sent:tatoeba-229345` いい人だけどイマイチね (n5, load 1), which does show いい + 人 but ends in the slangy イマイチ. Authoring is the honest answer for this featured slot. |
| `les:n5-adjetivos-04` | `sent:tatoeba-230319` | `vocab:1584930` 余り あまり (+2) and `vocab:1529520` 無い ない (+7), both used by the body's own explanation | The only other 〜くなかった sentence in the bank, `sent:tatoeba-11117435` とにかく行きたくなかったの, is already displayed in this same lesson. Pool exhausted. |
| `les:n5-adjetivos-06` | `sent:tatoeba-4852` | kanji 好 (+132), kanji 嫌 (never), vocab ない (+5) | Zero compliant 好き / きらい sentences at any load. All 好き sentences are n4+. |
| `les:n5-conectando-06` | `sent:tatoeba-137646`, `sent:tatoeba-3460693` | `vocab:1382980` 積もり つもり (+13); `vocab:1313580` 事 こと (+30) | Zero compliant つもり or たことがある sentences; every one in the bank is n4. |
| `les:n5-comparacoes-06` * | `sent:tatoeba-3073523` | `vocab:1195970` 過ぎる (+39, `les:n4-oracoes-relativas-01`) | All 14 すぎる sentences are n4. `高すぎる！` is already at load 1 = budget; only the level tag fails. |
| `les:n5-te-form-01` | `sent:tatoeba-124708`, `sent:tatoeba-146189` | `vocab:1184280` 下さる (+97, `les:n4-suposicao-07`) | Zero compliant てください sentences at n5. `sent:tatoeba-140998` 前に行ってください and `sent:tatoeba-150641` 時間があったら来てください both go to load 0 after the unlock but stay graded n4. |
| `les:n5-particulas-lugar-04` | `sent:gen-b61f5e94a2f1` | `vocab:1414170` 大人 (+14); `vocab:1611000` 生る なる (+22) | Zero compliant に + なる sentences. The lesson's other に senses (destination) have plenty: `sent:tatoeba-197681` ビーチに行きましょう, `sent:tatoeba-193955` モールに行きましょうか, both load 0. |
| `les:n4-oracoes-relativas-03` | `sent:tatoeba-79723` | `vocab:1215230` 間 あいだ (+45, `les:n4-aspecto-02`) | Kanji 間 is already known; only the word is not. No real temporal 間に candidate exists either way (see Group D). |
| `les:n4-aspecto-02` | `sent:tatoeba-12462035` | kanji 続 (+52) | All five 続ける sentences carry 続 and are graded n3. Zero compliant. |
| `les:n4-forma-simples-04` | `sent:gen-86b281bbdbef`, `sent:gen-e00af1726629` | kanji 頃, **never unlocked by any lesson** | Both violating slots are precisely the two 頃-in-kanji examples. After unlocking 頃: `sent:gen-b7992e71a26e` 三時頃に駅で会いましょう and `sent:gen-5462fa2cb22f` 学生の頃はお金がなかった both hit load 0 (both AI, both graded n2). The ごろ half of the lesson has 8 real compliant sentences and is fine. **Trap:** a substring search for ころ returns 37 compliant hits, all of them ところ. |
| `les:n4-passiva-03` | `sent:tatoeba-9478237` | kanji 全 (+29), 然 (+65); `vocab:1395620` 全然 (+5) | This slot exists specifically to show the kanji spelling ("Esta usa a escrita em kanji: 全然"), so the kana alternatives (`2140068` バナナはぜんぜんほしくない, `159061` 私はビールはぜんぜん飲みません, both load 1 real) defeat its purpose. After the unlock, `sent:tatoeba-213988` センスが全然ないわ goes to load 0 but stays n3. |
| `les:n4-volitivo-04` | `sent:tatoeba-84326`, `sent:tatoeba-9489164` | `vocab:1543240` 予定 (+8); kanji 予 (+83), 定 (+67) | All eight 予定 sentences carry the same three items. Zero compliant. The ことになる half has 7 real compliant sentences. |
| `les:n3-causa-02` | `sent:tatoeba-211124` | kanji 結 (**never unlocked**), 果 (+1, the very next lesson); `vocab:1254690` 結果 (+35) | Zero compliant その結果. Note 果 is unlocked one lesson later, so a single reorder plus a 結 unlock fixes half of it. **Trap:** the による search returns `sent:tatoeba-202786` 銀行によってくる and `sent:tatoeba-202824` その店によって行きませんか, both 寄る (to drop by), not the agentive による. |
| `les:n4-oracoes-relativas-01` * | `sent:gen-82ddc26749ff` | `vocab:1423310` 中 なか, **never unlocked by any lesson in the course** | See Group D: no compliant set-comparison example exists even after the unlock. |

\* These two rows are listed here for their root cause but their primary recommended action sits in
Group E and Group D respectively, so they are not counted twice in the tally below.

### Group D. Nothing exists; needs authoring (4 slots)

**`les:n4-oracoes-relativas-01` / `sent:gen-82ddc26749ff`** (n3, load 4/2, featured) `果物のなかでりんごが好きです`
The slot teaches の中で as "dentre um conjunto" (the superlative/comparison use). Every other sentence in
the bank with that sense is worse: `sent:tatoeba-115590` 彼は、英語がクラスのなかでかなり遅れている (load 5),
`sent:gen-e550b112cef4` クラスのなかで彼が一番背が高いです (load 5). The physical-sense sentences in Group A do
not cover this reading. Author one from the lesson's known set, e.g. a `[grupo] の中で [item] が一番 …` frame
using vocabulary already unlocked, and unlock `vocab:1423310` 中 in the same edit.

**`les:n4-oracoes-relativas-04` / `sent:gen-b2c4b3ced962`** (n3, load 5/2, card) `子供が遊んでいる間に夕食を作った`
(供 +118, 遊 +168, 夕 +58, 作 +6.) The only compliant ているあいだに sentence in the bank,
`sent:gen-4590c1e65a70` 電車を待っている間に本を読んだ, is **already the featured example in this same lesson**.
The 後で half has 10 real compliant sentences and is fine. Needs one authored ているあいだに sentence.

**`les:n4-oracoes-relativas-03` / `sent:gen-c5f31a4dfcad`** (n3, load 4/2, card) `母が出かけている間に宿題を終えた`
(宿 +155, 終 +24, 題 +9.) Zero compliant 間に in the temporal sense. **Trap:** the compliant 間に hits are
`sent:tatoeba-147804` 出かける時間になった (時間), `sent:tatoeba-143754` 水は人間にとって大切だ (人間) and
`sent:tatoeba-80125` 木の間に家が見える (spatial "between the trees", not temporal). None of them teaches the point.

**`les:n5-passado-01` / `sent:tatoeba-83696`** (n1, load 4/1, featured) `雰囲気がいやだった。`
(雰 and 囲 are never unlocked anywhere; the sentence is graded n1 inside an n5 lesson.) The slot teaches
[adjetivo-な] + だった. No real な-adjective + だった sentence exists at n5 with load ≤ 1. The nearest,
`sent:tatoeba-85319` 病気だったんだよ, is load 3. This is the worst single pair in my slice and should be
authored from the lesson's own な-adjectives.

### Group E. Re-grade the sentence, do not replace it (7 slots)

For these the load is inside budget and the teaching point is correct; the only failing gate is the
sentence's `level` tag, and no lower-graded sentence for the point exists in the bank. Replacing them
would trade a correct example for a worse one.

| Lesson | Slot | Current grade | Why re-grade |
|---|---|---|---|
| `les:n5-adjetivos-02` | `sent:tatoeba-77848` `良かったですね。` | n3 | A four-mora fixed reaction, the exact 良かった the body teaches. Zero other 良かった sentences exist. Swapping to 大きいね / バナナおいしい (both load 0) would delete the past-tense point. |
| `les:n4-conectores-02` | `sent:gen-2983acf2a91a` `彼は親切で、また元気だ` | n3, load 1/2 | The additive また the body needs. All 15 real また sentences are the adverbial "de novo" (`また明日`, `また来週！`, `また始まった`), a different sense. |
| `les:n4-keigo-05` | `sent:gen-6c6ce0d2199b` `よろしくお願いいたします` | n3, load 1/2 | A fixed formula the body explicitly says to memorise whole. Load 1 is kanji 願, unlocked +97. |
| `les:n4-suposicao-01` | `sent:tatoeba-104331`, `sent:tatoeba-106462` | n3, load 1/2 each | Load 1 is kanji 彼 in both, unlocked at `les:n3-limites-04` (+98) although the word 彼 is taught at +7. Every と言われている sentence in the bank is n3+. Fixing the 彼 kanji unlock clears the load; the level gate needs a grading decision. |
| `les:n5-comparacoes-06` | `sent:tatoeba-3073523` `高すぎる！` | n4, load 1/1 | Inside budget. All 14 すぎる sentences are n4 because 過ぎる is an n4 word, so an n5 lesson teaching すぎる can never show a compliant example. Either accept the n4 grade here or move the lesson into N4. |
| `les:n5-verbos-05` | `sent:tatoeba-11795596` `8人孫がいます。` | n2, load 1/1 | Inside budget (孫, a kanji no lesson ever unlocks). The only other がいます sentence in the bank, `sent:tatoeba-11561754` ポーチにスカンクがいます, is already displayed in this lesson. |

---

## What I would ask the teacher to decide first

1. **Should `unlocks` be required to cover the lexemes of the grammar point the lesson teaches?** If yes,
   20 of my 67 slots resolve by an unlocks edit and the sentence bank never has to be touched. A
   validator rule ("every kanji and content word appearing in an unlocked grammar point's
   `structure_pattern` must be in that lesson's `cumulative_known_set`") would catch all ten lessons in
   the table at the top of this report, plus the vocab cases.
2. **Should kanji unlocks be dragged by vocab unlocks?** 彼 alone accounts for 11 of my 67 loads.
3. **Is `level` on a sentence allowed to exceed the level of the lesson that teaches its point?** Today
   every すぎる, てください, つもり, 場合は and 予定 sentence is graded above the n5/n4 lesson that introduces
   it, because the sentence inherits the level of the word being taught. Under the current rule those
   lessons are permanently unfixable by selection.
4. **`vocab:1157170` 為る (する) at course position 206** and **`vocab:1423310` 中 (なか) never unlocked** look
   like plain omissions rather than pedagogical choices.

---

## Counts

Every slot is assigned to exactly one recommended action, so groups A to E partition the 67.

| Recommended action | Lessons | Slots |
|---|---|---|
| Assigned and checked (md5 bucket 1) | 39 | 67 |
| **A.** Swap: real sentence, same teaching point, proposed | 18 | **23** |
| **B.** Swap: AI-generated candidate only | 9 | **13** |
| **C.** Fix the `unlocks`, not the sentence | 15 | **20** |
| **D.** Nothing exists; author a new sentence | 4 | **4** |
| **E.** Re-grade the sentence, keep it in place | 6 | **7** |
| | | **67** |

| Cross-cutting tallies | Count |
|---|---|
| Slots with zero compliant same-point candidate of any provenance | 30 of 67 |
| Slots whose only failing gate is the `level` tag (load within budget) | 33 of 67, across 20 lessons |
| Slots failing budget only (level fits) | 9 of 67 |
| Slots failing both gates | 25 of 67 |
| Lessons teaching a point whose own **kanji** they have not unlocked | 10 of 39 |
| Lessons teaching a point whose own **vocab** they have not unlocked | 17 of 39 |
| Slots inflated by `vocab:1157170` 為る (する), unlocked at course position 206 | 6 |
| Slots inflated by kanji 彼, unlocked ~180 lessons after the word 彼 | 11 |
| Distinct kanji displayed in this slice that no lesson ever unlocks | 14 |
| Vocab displayed in this slice that no lesson ever unlocks | 1 (`vocab:1423310` 中) |
| Candidate traps found by machine matching and rejected by hand | 15 |
| `featured` slots (a swap also requires rewriting the surrounding prose) | 40 of 67 |
| `card` slots (a swap is usually a drop-in) | 27 of 67 |

Nothing in this report was written to `corpus/`, `course/`, `scripts/`, `contracts/`, `prototype/` or
`db/corpus.sqlite`. Sentence `structure_explanation` fields were not reviewed, per instruction.
