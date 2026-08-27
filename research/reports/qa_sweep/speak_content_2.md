# QA sweep: `course/speak` content, batch 2

**Slice:** the 36 unit files of stages `about_you`, `time_plans`, `past_stories`, `politeness`,
`opinions`, `real_talk` (`course/speak/<stage>/unit-01..06.json`).
**Date:** 2026-08-27. **Mode:** read-only; nothing outside this file was touched.
**Out of scope by instruction:** sentence `structure_explanation` fields (being re-authored concurrently).

Every quotation below is verbatim from the committed JSON. Sentence IDs resolve against
`corpus/sentences/bank.json`; grammar forms against `corpus/grammar/n{3,4,5}.json`; the design
contract is `design/speaking_path.md`; pt-BR authoring rules are `design/translation_style.md`.
Where a defect also occurs outside the slice I say so, but the unit IDs I cite are mine.

---

## What passed

Verified by script over all 36 units, zero defects:

| Check | Result |
|---|---|
| Referential integrity of every `sent:` reference (`say_now`, `chunk_phrases`, `shadowing`, `drills[].examples`, `production[].sentence`, `fluency.items`) | 1,289 references, 0 dangling |
| `production[].prompt_pt` byte-identical to the bank record's `translation["pt-BR"]` | 108/108 |
| `production[].answer_key` byte-identical to the bank record's `jp` | 108/108 |
| `accepted_variants` == `{jp, jp minus final punctuation, kana, kana minus final punctuation}` | 108/108 sets derive correctly |
| Every `production[].sentence` was met earlier as a `say_now` item | 108/108 |
| `shadowing` mirrors `say_now` | 36/36 |
| `real_phrases` equals the count of `ai_generated == false` in `say_now` | 36/36 |
| `cumulative_known_vocab` equals the running union of `words` across the whole 72-unit path | 36/36 |
| `fluency.zero_new_tokens: true` holds against the cumulative known vocab set | 36/36 |
| Duplicate distractors inside one checkpoint item | none in 450 distractors |
| Authored pt-BR (`title`, `fluency.prompt_pt`, `production[].prompt_pt`): em dash, "Quanto a" crutch, pt-PT lexicon | none found |
| Field discipline (`layer: "C"`, `needs_review: true`, `schema_version`, `audio: "pending"`, `untranslated: []`) | uniform, 36/36 |

The defects are all in the assembly layer: which sentence landed in which slot, how often, and what
the grader will accept back.

---

## Findings

### 1. In 12 of the 36 units the `fluency` task cannot be performed with the items given

**Severity: high.**

`fluency.prompt_pt` is a single constant per stage (verified: 1 distinct string per stage, all six
stages). The items under it are drawn from the *previous* stage's pool in unit-01 and are still
majority-previous-stage in unit-02. Measured by tracing each item back to the stage whose `say_now`
introduced it:

| Unit | production items from own stage | fluency items from own stage |
|---|---|---|
| `speak:about_you-01` | 0/3 (all `lodging`) | 0/6 (all `lodging`) |
| `speak:about_you-02` | 3/3 | 3/6 |
| `speak:time_plans-01` | 0/3 (all `about_you`) | 0/6 |
| `speak:time_plans-02` | 3/3 | 2/6 |
| `speak:past_stories-01` | 0/3 (all `health`) | 0/6 |
| `speak:past_stories-02` | 3/3 | 1/6 |
| `speak:politeness-01` | 0/3 (all `past_stories`) | 0/6 |
| `speak:politeness-02` | 3/3 | 2/6 |
| `speak:opinions-01` | 0/3 (all `politeness`) | 0/6 |
| `speak:opinions-02` | 3/3 | 2/6 |
| `speak:real_talk-01` | 0/3 (all `opinions`) | 0/6 |
| `speak:real_talk-02` | 3/3 | 1/6 |

Rolling recall across a stage boundary is a defensible design. The defect is that the prompt is not
rolled with it, so the learner is told to do one thing and handed the material for another.

`speak:about_you-01`:

> `"prompt_pt": "Alguém puxou assunto com você. Diga quem você é, de onde vem e do que gosta."`

and the six items are `部屋の大きさは、これで十分ですか。` / `部屋をいそいでかたづけてほしいの。` /
`部屋を出るときは必ず明かりを消してね。` / `これはその箱をあける鍵です。` / `部屋を出た後はドアを閉めなさい。` /
`料金の手ごろなホテルを見つけて下さい。` Five of six are about a hotel room. Nothing supports "quem você é,
de onde vem, do que gosta".

`speak:politeness-01`:

> `"prompt_pt": "Você precisa pedir um favor a alguém mais velho. Peça com jeito."`

items: `カレーを初めて作りました。` / `「この店は初めて？」「ええ、初めてです」` / `昨日動物園に行った。` /
`旅行の目的は何ですか。` / `旅行は期待通りでしたか。` / `春は楽しい季節だ。` Not one is a request.

`speak:opinions-01`:

> `"prompt_pt": "Perguntaram sua opinião. Diga o que você acha e por quê."`

items: `サラダはご自由にお召し上がりください。` / `サラダをお召し上がりください。` / `コップ１杯の水をください。` /
`明日お宅に伺います。` / `ステーキは中位で焼いてください。` / `この電報をすぐに打っていただきたい。` Six polite
requests, zero opinions.

`speak:time_plans-01`:

> `"prompt_pt": "Um amigo quer marcar alguma coisa. Combine dia e horário."`

items include `私の趣味はピアノを弾くことです。`, `彼はそのために仕事を失った。`, `姉さんタイプの女の人が好きだ`.
Nothing about a day or a time.

The same production slots are equally off-brief: `speak:about_you-01` asks the learner to produce
`部屋には家具が４点あった。` ("Havia quatro móveis no quarto.") in the stage titled *Falar de você*, and
`speak:time_plans-01` asks for `悲しいことに多くの日本人が亡くなりました。` ("Infelizmente, muitos japoneses
morreram.") in the stage about arranging to meet a friend.

**Fix:** either give `fluency` a per-unit prompt authored from that unit's actual items, or hold
unit-01's carry-forward items under the *previous* stage's prompt string until the stage's own pool
is available (unit-02 onward already is). The cheapest correct fix is per-unit prompts, since the
mismatch is partial in unit-02 as well.

---

### 2. Two units teach the same phrase twice in the same six-slot `say_now`

**Severity: high.**

`speak:politeness-01` `say_now`:

> `"sent:tatoeba-4854"` → `おめでとうございます。` / "Parabéns!"
> `"sent:tatoeba-8467948"` → `おめでとうございます！` / "Parabéns!"

Identical Japanese, identical pt-BR, differing only in the final `。` versus `！`. Both are also
listed in `chunk_phrases`. The unit therefore delivers five distinct phrases in six slots while
declaring `"real_phrases": 6`, and both copies reappear together in `speak:politeness-02.fluency`
and `speak:politeness-03.fluency`.

`speak:real_talk-06` `say_now`:

> `"sent:tatoeba-77972"` → `両方とも好きなわけではない。` / "Não é que eu goste dos dois."
> `"sent:tatoeba-77973"` → `両方とも好きというわけではない。` / "Não é que eu goste dos dois."

Two bank records with the same pt-BR string, teaching the same idea in the same unit.

The same collision shows up inside drill blocks. `speak:politeness-02` and `speak:politeness-05`,
`gram:gozaimasu`:

> `sent:tatoeba-335372` → `おはようございます。`
> `sent:tatoeba-1576172` → `おはようございます！`
> `sent:tatoeba-8467948` → `おめでとうございます！`

A three-example drill with two identical examples.

**Fix:** dedupe on `strip_punctuation(jp)` (and on `translation["pt-BR"]` as a second pass) before
filling `say_now`, `chunk_phrases` and `drills[].examples`; back-fill the freed slot from the next
qualifying candidate. `real_phrases` should be recomputed after the dedupe.

---

### 3. `私は明日死ぬかもしれない` ("Eu talvez morra amanhã") is used nine times across the slice

**Severity: high.**

`sent:tatoeba-152614` appears as:

- `speak:time_plans-02` → `say_now` (a phrase presented as something to say today, in the stage about arranging to meet a friend)
- `speak:time_plans-03`, `-04`, `-05` → `fluency.items`, under `"Um amigo quer marcar alguma coisa. Combine dia e horário."`
- `speak:opinions-01`, `-03`, `-04`, `-05`, `-06` → `drills[gram:kamo-shirenai].examples`, the identical three-example block in five of the stage's six units

So a learner working through `time_plans` and `opinions` rehearses "I might die tomorrow" out loud
nine times, four of them while being told to schedule a meeting with a friend. The `kamo-shirenai`
point has plenty of neutral bank support: the same block already carries `明日は雨かもしれない。` and
`何か起きたかもしれない。`, and `speak:time_plans-02` uses `雨になるかもしれないな。` in the third slot instead.

**Fix:** drop `sent:tatoeba-152614` from `say_now` and from the `kamo-shirenai` block; replace with
`sent:tatoeba-189633` (`雨になるかもしれないな。`) or `sent:tatoeba-79047` (`夕方には雪がふるかもしれないよ。`),
both already in the slice. Add a content filter for death/illness/self-harm predicates in
`say_now` and `fluency` selection.

---

### 4. An ungrammatical sentence is promoted all the way to `production`

**Severity: high.**

`sent:tatoeba-214558`:

> `"jp": "すばらしい食事を経験下さい。"`, `"translation": {"pt-BR": "Por favor, tenha uma refeição maravilhosa.", "en": "Have a wonderful eating experience."}`, `"provenance": {"ai_generated": false, "needs_review": true, ...}`

`経験下さい` is not a well-formed request: `経験する` takes `ご経験ください` in the honorific pattern, and
`食事を経験する` is not idiomatic Japanese in any register. This is a low-quality Tatoeba record that
the path uses four times:

- `speak:past_stories-03` → `say_now`
- `speak:past_stories-04` → `production` (the learner must type it back exactly)
- `speak:past_stories-05`, `-06` → `fluency.items`

`production` is the one slot where the corpus asks the learner to *generate* the string, so this is
the worst possible placement for a sentence nobody should reproduce.

The same unit stacks two more near-duplicates on one idiom. `speak:past_stories-03` `say_now`:

> `sent:tatoeba-225041` → `こういう場合には経験が物を言う。`
> `sent:jec-0319` → `やはり経験がものを言います`
> `sent:jec-0071` → `誰もが経験をする`

Two of six slots are `経験が物を言う` written twice (once `物`, once `もの`), and both go on to become
`production` items in `speak:past_stories-04`.

**Fix:** remove `sent:tatoeba-214558` from the path entirely and flag the bank record for review
(`corpus/sentences/bank.json`). Collapse `sent:tatoeba-225041` / `sent:jec-0319` to one, and free
the slot for a past-tense narration sentence, which is what the stage is for.

---

### 5. Drill blocks are verbatim repeats, and the strand accounting counts them as new work

**Severity: high.**

A "block" here is a `(pattern, exact example list)` pair. Share of each stage's drill slots that
repeat a block already used earlier in the path:

| Stage | repeated drill slots |
|---|---|
| `real_talk` | 72/99 (73%) |
| `opinions` | 57/90 (63%) |
| `past_stories` | 51/105 (49%) |
| `politeness` | 33/78 (42%) |
| `time_plans` | 24/84 (29%) |
| `about_you` | 9/75 (12%) |

Worst offenders inside the slice:

- `gram:te-kudasai` `[乗ってください。, 電話に出てください。, もっとゆっくり話してください！]`: identical in `politeness-03`, `-04`, `-05`, `-06`, four consecutive units, and `politeness-06` has only two drill patterns total, so half its language-focused work is this repeat.
- `gram:kamo-shirenai`: identical in `opinions-01`, `-03`, `-04`, `-05`, `-06`.
- `gram:to-iu` `[明日と言う日は来ない。, 聞こえる音は時計のカチカチという音だけだった。, 明日という日もある。]`: identical in `real_talk-03`, `-04`, `-05`, `-06`. `という` is one of `real_talk`'s headline patterns, and it gets the same three aphorisms four times.
- `gram:janai-dewa-nai`: identical in `real_talk-02`, `-04`, `-05`, `-06`.
- `gram:bakari`: identical in `real_talk-01`, `-02`, `-03`, `-06`.
- `gram:koto`: identical block across `about_you-05`, `-06`, `time_plans-01`, `past_stories-03`, `-04`, `-05`, `-06` (seven units).
- `gram:da-desu`: same block in ten units path-wide, six of them in this slice.

Each repeat is still counted in `strand_counts["language-focused"]` and therefore in the `strands`
percentages, so a unit that is 73% re-run reports the same balance as one that is fresh. Example:
`speak:real_talk-06` declares `"language-focused": 59` percent while four of its five drill blocks
are verbatim repeats of earlier units.

**Fix:** in the builder, keep a used-block set and require at least one unseen example per block
(or rotate the example list). Failing that, split `strand_counts` into new versus review so the
declared balance stops overstating novel work.

---

### 6. `accepted_variants` accepts a misspelling of the kana answer and rejects the correct one

**Severity: high.**

The kana branch of `accepted_variants` comes from the bank's `kana` field, which is a phonetic
transcription, not modern kana orthography (現代仮名遣い). Topic `は` is written `わ` and directional
`へ` is written `え`. In 46 of the slice's 108 production items the kana variants therefore contain a
spelling that is wrong in written Japanese, while the spelling a learner would actually type is not
in the accepted set.

Sharpest case, `speak:time_plans-06`, `sent:tatoeba-174391`:

> `"answer_key": "午後は外へ出たくない。"`
> `"accepted_variants": ["ごごわそとえでたくない", "ごごわそとえでたくない。", "午後は外へ出たくない", "午後は外へ出たくない。"]`

Both particles are misspelled: `は` → `わ` and `へ` → `え`. A learner who types the correct
`ごごはそとへでたくない` is marked wrong; one who types the incorrect `ごごわそとえでたくない` is marked right.

Further instances in the slice (all 46 listed in the appendix pattern, a sample):

| Unit | Sentence | Accepted kana |
|---|---|---|
| `speak:about_you-01` | `部屋には家具が４点あった。` | `へやにわかぐがよんてんあった` |
| `speak:opinions-02` | `列車はあと５分で出発するはずです。` | `れっしゃわあとごふんでしゅっぱつするはずです` |
| `speak:real_talk-05` | `事件は終わったわけではない。` | `じけんわおわったわけでわない` |
| `speak:past_stories-06` | `父は昨日入院しました。` | `ちちわきのうにゅういんしました` |

The reading choice is also locked to one variant with no alternative accepted: `明日` is fixed to
`あす` in `speak:time_plans-02` (`あすわあめかしら`), `speak:about_you-05` (`あすまでにわ…`) and
`speak:time_plans-05` (`あすまでにしゅくだいを…`), so `あしたはあめかしら` fails; `日本` is fixed to
`にっぽん` in `speak:real_talk-02` (`まぁ、にっぽんもさこくしていたわけだしなあ`), so `にほん` fails.

**Fix:** derive the kana variant from orthographic kana (particle `は`/`へ`/`を` preserved), and add
the phonetic form as an *additional* accepted variant rather than the only one. For readings with a
common alternative (`明日` あす/あした, `日本` にほん/にっぽん), emit both.

---

### 7. Fourteen answer keys require characters a learner cannot reasonably type

**Severity: medium-high.**

`production[].accepted_variants` holds exactly four strings, so an answer that differs by one
character fails. Fourteen of the 108 answer keys in the slice contain a full-width Latin letter,
full-width digit, or a CJK compatibility ligature, and the half-width equivalent is not accepted:

| Unit | Sentence | Character | Answer key |
|---|---|---|---|
| `speak:politeness-05` | `sent:tatoeba-1490062` | `㌔` U+3314 | `肉を半㌔ください。` |
| `speak:real_talk-06` | `sent:tatoeba-234789` | `Ｕ` U+FF35 | `ＵＮというのは何を表わしていますか。` |
| `speak:about_you-03` | `sent:jec-4753` | `Ｓ` U+FF33 | `ＳＰの仕事の様子が今日テレビで放送されました` |
| `speak:about_you-01` | `sent:tatoeba-84223` | `４` U+FF14 | `部屋には家具が４点あった。` |
| `speak:opinions-02` | `sent:tatoeba-77522` | `５` U+FF15 | `列車はあと５分で出発するはずです。` |
| `speak:opinions-02` | `sent:tatoeba-77523` | `６` U+FF16 | `列車は６時到着のはずだった。` |
| `speak:opinions-06` | `sent:tatoeba-235244` | `４` U+FF14 | `４０近いはずだ。` |
| `speak:time_plans-01` | `sent:tatoeba-10050538` | `８` U+FF18 | `夫は大抵８時には仕事に出かけます。` |

plus five full-width `？`/`！` cases (`speak:time_plans-03`, `-06`, `speak:past_stories-03`,
`speak:politeness-02`, `-03`, `speak:about_you-04`).

`㌔` is the worst: it is a single-codepoint ligature for キロ that essentially no IME produces, and
`半キロ`, `半きろ`, `半キログラム` all fail.

**Fix:** normalise full-width Latin and digits to half-width and expand CJK compatibility ligatures
(NFKC) when generating variants, and add both forms to `accepted_variants`. Consider dropping
`sent:tatoeba-1490062` from `production` regardless, since `㌔` is also poor reading material.

---

### 8. Three production prompts do not determine the answer they grade

**Severity: medium-high.**

`speak:time_plans-06`, `sent:tatoeba-1699768`:

> `"prompt_pt": "Será que vai melhorar à tarde?"` → `"answer_key": "午後には上がるだろうか？"`

`上がる` here is the rain-specific "let up" idiom, and `melhorar` gives the learner no route to it,
nor to `には` over `は`. The English gloss in the bank is `"Will it clear up this afternoon?"`, which
carries the weather framing that the pt-BR prompt dropped.

`speak:about_you-01`, `sent:tatoeba-84223`:

> `"prompt_pt": "Havia quatro móveis no quarto."` → `"answer_key": "部屋には家具が４点あった。"`

Nothing in "quatro móveis" signals the counter `点` rather than `つ` or `個`.

`speak:past_stories-04`, `sent:tatoeba-214558`:

> `"prompt_pt": "Por favor, tenha uma refeição maravilhosa."` → `"answer_key": "すばらしい食事を経験下さい。"`

Compounding finding 4: the prompt reads like `よい食事を`, and the only accepted answer is the
ungrammatical original.

**Fix:** for `production`, prefer sentences whose pt-BR translation is a tight round trip. A cheap
screen: reject a candidate when its answer key contains a counter, an idiom, or a proper noun that
the prompt does not name. Where the sentence is worth keeping, add a short disambiguating hint field
rather than widening `accepted_variants`.

---

### 9. Off-register model sentences, repeated across many units

**Severity: medium.**

These are drilled aloud, so tone matters more than in reading material.

- `sent:tatoeba-150175` → `痔があります。` / "Tenho hemorroidas." Used **seven times** path-wide, four inside this slice: `speak:about_you-06` and `speak:opinions-02` (`gram:gp-8`, registered form `ます`, "terminação polida do verbo"), `speak:politeness-01` (`gram:gp-8`), `speak:politeness-02` (`gram:ga-arimasu`). The same blocks already carry `兄がいます。`, `時間がありますか。`, `どこに行きますか？`; the hemorrhoid sentence adds nothing the others do not.
- `sent:tatoeba-74723` → `「どいてください」「やんのか？あんちゃん」` / "Saia da frente, por favor." "Quer brigar, garotão?" Used four times, three in the slice: `speak:past_stories-02`, `speak:politeness-01`, `speak:politeness-02`, all as a `gram:te-kudasai` example. A street-fight exchange is a poor model for the polite-request pattern, and `politeness` is precisely the stage titled *Pedir, oferecer, agradecer com jeito*.
- `sent:tatoeba-5074` → `彼はとてもセクシーだ。` Five uses, three in the slice (`speak:about_you-02`, `speak:past_stories-01`, `speak:past_stories-04`, `gram:totemo`), sitting next to two neutral generated examples that already carry the pattern.
- `sent:tatoeba-4947` → `ドイツ人はとてもずる賢い。` / "Os alemães são muito astutos." A national stereotype as a `gram:totemo` model in `speak:about_you-02`.
- `sent:tatoeba-95365` → `彼女が自殺したというのは本当か。` / "Será que é verdade que ela se suicidou?" In `speak:real_talk-06` `say_now`, that is, presented as a phrase to use today.
- `sent:tatoeba-789591` → `悲しいことに多くの日本人が亡くなりました。` In `speak:about_you-06` `say_now` and `speak:time_plans-01` `production`.

**Fix:** a register/content screen over `say_now`, `production` and `drills[].examples` covering
medical-private, violence, ethnicity generalisations, sexual content and death. Every one of these
has a same-pattern replacement already inside the slice, so the fix costs no new authoring.

---

### 10. A classical-Japanese Bible verse is in a fluency set

**Severity: medium.**

`speak:past_stories-01` `fluency.items` includes `sent:tatoeba-145552`:

> `"jp": "心熱けれど肉体は弱し。"`, `"kana": "こころあつけれどにくたいわよわし。"`, `"translation": {"pt-BR": "O espírito está pronto, mas a carne é fraca.", "en": "The spirit is willing, but the flesh is weak."}`, `"level": "n3"`

`〜けれど…し` in that shape is 文語 (classical), not modern spoken Japanese, and the whole point of the
fluency slot is 48 seconds of speaking under a scenario prompt (`"Alguém perguntou como foi seu fim
de semana. Conte, no passado."`). Also note the `kana` field reads `心熱けれど` as `こころあつけれど`, which
is itself doubtful. The record is also used as `say_now` and `production` in `health-04`/`-05`
(outside my slice) so the fix has wider reach.

**Fix:** drop from all four slots and flag the bank record: classical forms should not carry an `n3`
level tag on a speaking path.

---

### 11. `about_you` is labelled band `n5` and contains no `n5` sentences at all

**Severity: medium.**

`course/speak/course.json` and `course/speak/INDEX.md` both give stage 6 (`about_you`) the band
`n5`. Level distribution of its 36 `say_now` sentences, from the bank records:

`{n4: 9, n3: 21, n2: 2, n1: 4}` — zero `n5`.

`design/speaking_path.md` §5 says bands are "for orientation only" and the path never gates on them,
which is fine, but an orientation label that is off by two bands for the whole stage misleads rather
than orients. Twenty-seven of the 36 sentences are two or more bands above the label, including
`sent:jec-1094` (`先輩がまだ会社にいました`, n1), `sent:tatoeba-163367` (`私の趣味は小説を読むことです。`, n1),
`sent:tatoeba-10050538` (`夫は大抵８時には仕事に出かけます。`, n1).

Same class elsewhere in the slice: `politeness` is labelled `n4` and carries 9 `n2` sentences,
including all four of `speak:politeness-06`'s non-`n4` `say_now` entries.

**Fix:** recompute `approx_band` from the stage's actual level histogram (for example, the median of
`say_now` levels) and regenerate the `INDEX.md` table, rather than hand-assigning it.

---

### 12. The i+1 budget in the design contract is exceeded by 20 `say_now` sentences

**Severity: medium.**

`design/speaking_path.md` §3.3 fixes `MAX_NEW = 3`: "A sentence qualifies only if the number of its
words *not* in the cumulative known set is ≤ 3", and the doc explicitly resolves an earlier
three-way inconsistency in favour of 3. Measuring each `say_now` sentence against the cumulative
known vocab as of the *previous* unit, 20 sentences in this slice exceed it. Worst:

| Unit | Sentence | New vocab |
|---|---|---|
| `speak:about_you-03` | `このような仕事で怖い顔をしたら、お客さんはいらっしゃらないでしょう。` | 6 |
| `speak:time_plans-01` | `数学を１時間ほど勉強していたら、眠くなった。` | 6 |
| `speak:time_plans-03` | `何でうまくいかないか君に説明するにはずいぶん時間がかかりそうだ。` | 6 |
| `speak:opinions-04` | `彼は、たぶん、招待してくれるように仕向けているでしょう。` | 5 |
| `speak:about_you-01` | `先生は生徒みんなを名前で呼んだ。` | 4 |
| `speak:politeness-03` | `来週、ぜひ夕食をご馳走させてください。` | 4 |

(Full list of 20 reproducible with the same measurement; 52 across all 72 units.)

The `speak:time_plans-03` case is also the unit's `production` item in `-04`, so the learner is asked
to reproduce a 6-new-word sentence one unit after meeting it.

**Fix:** either enforce the budget in the builder and let short units happen (§3.6 already allows
that: "If a stage cannot be filled to target from the bank, the builder emits a short unit"), or
amend §3.3 to the number the builder actually uses. Right now the contract and the data disagree,
which is the same failure §3.3 was written to close.

---

### 13. Checkpoint distractors are drawn as rare ateji the learner has never seen

**Severity: medium.**

`design/speaking_path.md` §7 is explicit about why distractors are redrawn from the known set: "a
distractor the learner has never seen is eliminated on sight as unfamiliar, so the item ends up
testing novelty detection rather than meaning." Sixteen distractors in this slice are rare kanji
spellings of words normally written in kana or katakana, which reintroduces exactly that failure:

| Unit | Item | Distractor | Normal spelling |
|---|---|---|---|
| `speak:time_plans-04` | `cf:n5:4163:426` | `洋袴` | ズボン |
| `speak:real_talk-02` | `cf:n3:5550:1966` | `珈琲` | コーヒー |
| `speak:real_talk-02` | `cf:n3:1277:1966` | `咖哩` | カレー |
| `speak:real_talk-03` | `cf:n3:5538:1980` | `洋杯` | コップ |
| `speak:time_plans-06` | `cf:n4:3700:848` | `漸と` | やっと |
| `speak:politeness-02` | `pp:n4:717` | `為さる` | なさる |
| `speak:opinions-05` | `cf:n3:36:1571` | `致す` | いたす |
| `speak:opinions-04` | `cf:n3:13:1571` | `貰う` | もらう |
| `speak:about_you-01` | `cf:n4:153:754` | `何処` | どこ |
| `speak:about_you-04` | `cf:n5:3595:307` | `此の` | この |
| `speak:past_stories-03` | `cf:n4:4843:896` | `貴方` | あなた |
| `speak:time_plans-02`, `speak:past_stories-01` | `cf:n3:891:2453`, `cf:n3:3701:2453` | `為` | ため |

`洋袴`, `珈琲`, `咖哩` and `洋杯` are the clearest: this is a **recognition-only** path (§4,
"RECOGNITION ONLY, this path never asks the learner to write kanji"), so a distractor written in a
form the learner will never encounter is free to eliminate.

**Fix:** when re-drawing a distractor, use the vocab record's primary display form (the one the path
teaches) rather than the JMdict headword, and blacklist forms flagged rare/ateji in the vocab
registry.

---

### 14. Two generated drill sentences contain spaces between words

**Severity: medium.**

`speak:time_plans-06`, `drills[gram:kara].examples`:

> `sent:gen-061ed9aa1785` → `あたまが いたいから かえります`
> `sent:gen-5b9e3ecfbcaf` → `さむいから まどを しめてください`

These are the only two of the 467 distinct sentences in the slice that contain whitespace. Japanese
does not use inter-word spaces, and both sit in the same block as `sent:tatoeba-76156`
(`今のはノーカンだからね。`), which is spaced normally, so the unit shows the learner two contradictory
conventions side by side. Both are also all-kana where the rest of the corpus uses kanji.

**Fix:** re-author both without spaces and with the normal kanji/kana mix (`頭が痛いから帰ります` /
`寒いから窓を閉めてください`), or replace with real bank sentences. Add a whitespace assertion to the
generated-sentence validator.

---

### 15. Three drill sentences teach `以下` written as `いか`

**Severity: medium.**

`speak:time_plans-03`, `drills[gram:gp-93].examples`, all three AI-generated:

> `sent:gen-a81f2084ea99` → `五十点いかは合格できません`
> `sent:gen-e1c2cfd5e350` → `三歳いかの子供は無料です`
> `sent:gen-0877b1b2f764` → `今日の気温は十度いかです`

`gram:gp-93`'s registered form is literally `"いか"` with meaning `"X ou menos / até X (inclui X)
(以下)"`, so the generator faithfully reproduced a form entry that is itself wrong: `以下` after a
quantity is always written in kanji, and bare `いか` in that slot is ambiguous with `烏賊`. The same
unit's own checkpoint uses the kanji form (`cf:n4:1180:1113` distractor `以下`), so the unit is
internally inconsistent.

**Fix:** correct the `forms[].form` entry in `corpus/grammar/` to `以下` and regenerate these three
sentences. Until then they should not be shown as models.

---

### 16. Two grammar points split one construction, and one unit drills both senses under the wrong labels

**Severity: medium.**

`speak:past_stories-05` carries both `gram:gp-80` and `gram:ni-suru` as drill patterns.

`gram:gp-80` registered meaning: `"deixar/tornar algo [tal] (adjetivo-な e substantivo)"`. Its
examples in this unit:

> `sent:tatoeba-141431` → `千切りにする。` (fits: turn it into julienne)
> `sent:tatoeba-189474` → `運まかせにするな。` (fits)
> `sent:tatoeba-215746` → `シャワーにするわ。` / "Vou tomar um banho." (does **not** fit: this is the *choice* sense, "I'll go with a shower")

`gram:ni-suru` in the same unit:

> `sent:tatoeba-223815` → `このコートにするわ。` / "Vou ficar com este casaco."
> `sent:tatoeba-232235` → `あなたは何にするの。`
> `sent:gen-6bab4422cee3` → `私はコーヒーにします`

`シャワーにするわ` and `このコートにするわ` are the same construction in the same sense, and this unit files
them under two different patterns, one of which explicitly means something else. A learner drilling
both blocks in one sitting gets contradictory teaching.

**Fix:** move `sent:tatoeba-215746` from the `gram:gp-80` block to the `gram:ni-suru` block, and
back-fill `gp-80` with a "make it [such]" example (`静かにしてください` class).

---

### 17. The `という` drill's first example writes the pattern in kanji

**Severity: low-medium.**

`gram:to-iu`'s registered form is `"という"`. The block repeated in five units of the slice leads with:

> `sent:tatoeba-80587` → `明日と言う日は来ない。` ("O dia chamado 'amanhã' nunca chega.")

so example 1 shows `と言う` while examples 2 and 3 show `という`, and the pattern header says `という`.
`と言う` in this quotative/naming use is unusual in modern writing. Both `明日と言う日は来ない` and
`明日という日もある` are also aphorisms rather than usable conversational models, in a stage
(`real_talk`) whose whole brief is `"Conversa de verdade"`.

**Fix:** replace `sent:tatoeba-80587` with a `という` example in the naming sense that a traveller
would use. `sent:tatoeba-80068` (`木村さんという人にパーティーで会ったよ。`) is already in the slice
(`speak:time_plans-02`) and fits exactly.

---

### 18. `past_stories-01` and `-02` spend six of twelve teachable slots on one trivial frame, none of it past tense

**Severity: low-medium.**

`speak:past_stories-01` `say_now` contains:

> `sent:tatoeba-143986` → `人生は楽しい。` / "A vida é divertida."
> `sent:tatoeba-13537670` → `とても楽しい。` / "É muito divertido."
> `sent:tatoeba-78158` → `旅行は楽しい。` / "Viajar é divertido."

Three of six slots on `X は楽しい`. All three then become the entire `production` set of
`speak:past_stories-02`, and all three reappear in `speak:past_stories-03.fluency` and
`speak:past_stories-04.fluency`.

The stage is `Contar o que aconteceu` ("tell what happened"). All three are present tense. Only two
of `speak:past_stories-01`'s six `say_now` sentences are in the past at all
(`病気のせいで私は旅行に行けなかった。`, `昔の思い出が急に心に浮かんだ。`), and `speak:past_stories-02`'s
production set contains no past-tense sentence whatsoever.

**Fix:** keep one of the three, and require the `past_stories` selector to filter `say_now` and
`production` on past-tense predicates (the token-level `inflection` field already carries this).

---

### 19. `production` and `fluency` re-use a sentence the same unit just drilled

**Severity: low.**

Within-unit duplicates, excluding the `say_now`/`chunk_phrases` overlap that §4 of the design doc
sanctions:

| Unit | Sentence | Slots |
|---|---|---|
| `speak:politeness-02` | `sent:tatoeba-5109` (`もっとゆっくり話してください！`) | `drills[gram:te-kudasai]` and `production` |
| `speak:politeness-02` | `sent:tatoeba-8467948` | `drills[gram:gozaimasu]` and `fluency` |
| `speak:politeness-03` | `sent:tatoeba-146189`, `sent:tatoeba-5109` | `drills[gram:te-kudasai]` and `fluency` |
| `speak:politeness-04` | `sent:tatoeba-146189`, `sent:tatoeba-5109` | `drills[gram:te-kudasai]` and `fluency` |
| `speak:opinions-03` | `sent:tatoeba-11692639` | `drills[gram:hazu-ga-nai]` and `fluency` |
| `speak:opinions-04` | `sent:tatoeba-11692639` | `drills[gram:hazu-ga-nai]` and `fluency` |
| `speak:opinions-06` | `sent:tatoeba-235244` | `drills[gram:hazu-da]` and `production` |

`production` is meant to test recall from a previous unit (finding 1 confirms every production
sentence was met earlier as `say_now`). When the same sentence is also on screen in this unit's drill
block, the item measures copying rather than recall.

**Fix:** exclude the unit's own drill examples from its `production` and `fluency` candidate pools.

---

### 20. `strands` percentages do not sum to 100 in nine units

**Severity: low.**

Rounding each `strand_counts` share independently leaves a 1-point gap:

- sum 99: `speak:about_you-05`, `speak:time_plans-06`, `speak:politeness-02`, `speak:politeness-03`
- sum 101: `speak:about_you-06`, `speak:time_plans-04`, `speak:politeness-01`, `speak:politeness-06`, `speak:opinions-04`

Example, `speak:politeness-01`: `{"meaning-input": 32, "meaning-output": 8, "language-focused": 45, "fluency": 16}` = 101.

Harmless as data, visible as a defect the moment a UI renders it as a stacked bar or a set of
percentages that should total 100.

**Fix:** largest-remainder rounding so the four shares sum to exactly 100.

---

### 21. The unit schema in `design/speaking_path.md` §4 no longer describes the data

**Severity: low, but it disarms every future audit.**

The committed units carry `drills`, `production`, `fluency`, `strands`, `strand_counts`,
`real_phrases`, `cumulative_known_vocab`, `patterns_chunked` and `untranslated`. None of these appear
in §4's unit shape. Worse, §4 says of `drills` specifically:

> "An earlier draft of this section specified a `drills` field... Nothing generated it, and
> `checkpoint` now covers the retrieval role using audited bank items instead of synthesised ones."

`drills` exists in all 36 units and holds 531 example slots, the single largest component of the
`language-focused` strand. An auditor working from the contract would conclude the field should not
be there at all, which is how findings 5, 16 and 17 stayed invisible.

**Fix:** update §4 to the real schema, and state the intended contract for `drills` (how many
examples, may they repeat, must they be unseen) and for `fluency` (is `prompt_pt` per stage or per
unit, which is the crux of finding 1).

---

## Counts

| Item | Checked | Flagged |
|---|---|---|
| Unit files | 36 | 30 (units named in at least one finding) |
| `sent:` references resolved | 1,289 | 0 dangling |
| Distinct sentences reached by the slice | 467 | 13 named as unfit for their slot |
| `say_now` slots | 216 | 9 (duplicate pairs, off-register, ungrammatical) |
| `say_now` i+1 budget (`MAX_NEW = 3`) | 216 | 20 over budget |
| `chunk_phrases` slots | 2 | 2 (both duplicate `say_now` in `politeness-01`) |
| `drills[].examples` slots | 531 | 246 verbatim repeats of an earlier block |
| `production` items | 108 | 46 kana-orthography, 14 untypeable characters, 3 under-determined prompts |
| `accepted_variants` strings | 418 | 0 malformed, but 46 items accept only a misspelt kana form |
| `fluency` item sets | 36 | 12 whose prompt no item supports |
| `fluency.prompt_pt` strings | 36 (6 distinct) | 6 (stage-constant, see finding 1) |
| `checkpoint` items | 177 | 16 distractors (rare-ateji), across 12 items |
| `checkpoint` distractors | 450 | 16 |
| `strands` / `strand_counts` pairs | 36 | 9 (rounding), 36 (count repeats as new work) |
| Authored pt-BR strings (`title`, `fluency.prompt_pt`) | 72 | 0 style violations |
| Stage band labels | 6 | 2 (`about_you`, `politeness`) |
| **Findings** | | **21** (5 high, 3 medium-high, 8 medium, 5 low / low-medium) |

## What I would fix first

1. Finding 6 (kana orthography in `accepted_variants`) and finding 7 (untypeable characters): these
   two mark correct learner answers wrong, and both are one normalisation pass in the exporter.
2. Finding 1 (per-unit `fluency` prompts): 12 units currently give an instruction they do not
   support.
3. Findings 3, 4, 9, 10 (unfit sentences): a content screen plus removing six specific bank records
   from the path. Every replacement is already in the slice.
4. Finding 5 (drill-block repetition): the largest volume defect, 246 of 531 slots.
