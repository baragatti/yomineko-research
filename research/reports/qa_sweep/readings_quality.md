# QA sweep — reading-practice boxes, quality

**Scope:** `corpus/readings/n5.json` (43), `n4.json` (91), `n3.json` (152) — **all 286 boxes**, read in full.
**Checked per box:** does the assembled passage read as coherent connected text; is the `title` apt; is
`translation["pt-BR"]` faithful to the `jp` and natural; is `translation["en"]` faithful; is every token `r`
the correct reading for its `s` **in context** (furigana); is every token `ro` consistent with its `r`.
**Method:** full manual read of all 286 `jp` + `pt-BR`; mechanical audits of all 12,618 tokens
(kana↔romaji conversion, kanji-token reading table, single-kanji readings vs `corpus/kanji/*.json`); every
box diffed against its `source_slugs` in `corpus/sentences/bank.json` (jp integrity, translation drift,
reading drift, redundancy, junction punctuation).
**Authority:** `design/translation_style.md`, `design/reading_practice.md`, `corpus/readings/INDEX.md`.
**Renderer context (severity calibration):** `prototype/app/lib/render-body.server.ts` renders ruby **only
for kanji-bearing surfaces** (`tokenRuby` returns plain text when `!KANJI_RE.test(s)`), and the romaji line is
emitted only when `show="romaji"|"both"`. All 286 `<reading>` tags in `course/` are bare `<reading ref="…"/>`,
so **`r` on a kanji surface reaches the learner as furigana today; `ro` and `r` on kana/digit surfaces are
data-only (latent)**. Findings are ordered by what the learner actually sees.

Zero integrity problems found: every `source_slugs` entry resolves in the bank, and `"".join(t.s) == jp` and
`strip_punct(concat(source jp)) == strip_punct(jp)` hold for all 286 boxes.

*Caveat on the `bank:` citations:* `corpus/readings/*.json` was unmodified in the working tree during this
sweep, so every finding about the boxes themselves is stable. `corpus/sentences/bank.json` was being edited
concurrently, so the `bank: …` columns are corroborating evidence read at one point in time, not a claim
about the bank's final state.

---

## A. Learner-visible defects

### A1 — `read:n4-causativa-03-01` — an English reviewer's note is shipped as the pt-BR translation
- `translation["pt-BR"]` ends with:
  > `… Acho que você deveria ser examinado por um médico. **"Estou indo fazer compras agora." The proposed
  > 'Estou saindo para fazer compras' shifts 行っているところ toward 出かけるところ; the record's own literal en
  > is 'I'm on my way to go shopping.'**`
- Why wrong: this is editorial meta-commentary, in English, inside the field the learner reveals with
  "Ver tradução". Nothing in the passage corresponds to it. It is also the only box out of 286 whose pt-BR
  contains English prose, so it is a leak, not a convention.
- Fix: replace the trailing fragment with the bank's own string for `sent:…買い物に行っているところです`, i.e. end
  the field at **"… Acho que você deveria ser examinado por um médico. Estou indo fazer compras agora."**

### A2 — 33 tokens in 30 boxes carry a reading that is wrong for the surface **in context**, and all of them render as furigana

Every row below has a kanji surface, so `tokenRuby` emits `<ruby>` — the learner is shown the wrong reading.
Where the box disagrees with the same sentence in `corpus/sentences/bank.json`, that is noted (`bank:`).

| box | fragment | shown | should be | why |
|---|---|---|---|---|
| `read:n3-conectores-03-01` | この道を**行っ**てもダメですよ | おこなっ | **いっ** (bank: いっ) | 行く "go along this road" mis-lemmatised as 行う "conduct". Its own pt-BR is "Por essa rua não dá". |
| `read:n3-limites-07-02` | 話**上手**もいれば、聞き**上手**もいる | かみて ×2 | **じょうず** (bank: じょうず) | かみて = stage-left/upper part. pt-BR: "Há quem fale bem… quem saiba ouvir bem." |
| `read:n3-relato-01-01` | **分別**のある人だ | ぶんべつ | **ふんべつ** (bank: ふんべつ) | ぶんべつ = waste-sorting; ふんべつ = good sense. pt-BR: "um homem sensato". |
| `read:n3-deveres-02-01` | 昨日**来る**べきだったのに | きたる | **くる** (bank: くる) | きたる is the adnominal/archaic "forthcoming"; here it is plain 来る. |
| `read:n4-dar-receber-02-01` | これは父に気に**入っ**てもらう | はいっ | **いっ** (bank: いっ) | 気に入る is きにいる, never きにはいる. |
| `read:n3-conjectura-04-01` | ふりをするのは**止め**なさい | とめ | **やめ** (bank: やめ) | "stop pretending" = やめる. pt-BR: "Pare de fingir". |
| `read:n3-causa-06-01` | 自分の思い**通り**にしたがる | とおり | **どおり** (bank: どおり) | 思い通り rendakus: おもいどおり. |
| `read:n3-concessao-05-02` | 会社**帰り**に寄る | かえり | **がえり** (bank: がえり) | 会社帰り = かいしゃがえり. |
| `read:n3-enfase-06-02` | 映画**作り**は…仕事だ | つくり | **づくり** (bank: づくり) | 映画作り = えいがづくり. |
| `read:n3-limites-05-01` | 注意**深く**選ばなければ | ふかく | **ぶかく** (bank: ぶかく) | 注意深い = ちゅういぶかい. |
| `read:n3-causa-05-02` | 私たちが金**不足**である | ふそく | **ぶそく** (bank: ぶそく) | 〜不足 rendakus in compounds (寝不足 ねぶそく); かねぶそく. |
| `read:n3-desejos-06-02` | **金**は安全な場所にしまっておきなさい | きん | **かね** (bank: かね) | Its own pt-BR is "Guarde o **dinheiro**…", not gold. |
| `read:n3-concessao-04-01` | **年**のわりには若く見える ×3 | ねん ×3 | **とし** (bank: とし) | 年のわりに = としのわりに. |
| `read:n3-conectores-07-02` | 料理について**何**か質問が | なん | **なに** (bank: なに) | 何か is always なにか. |
| `read:n3-conectores-08-01` | 電話を**一**本かけなくては | いち | **いっ** (bank: いっ) | 一本 = いっぽん; the box already reads 本 as ぽん, so it currently spells いちぽん. |
| `read:n3-conectores-08-02` | 二**本**の道はそこでクロス | ぽん | **ほん** (bank: ほん) | 二本 = にほん (no gemination after に). |
| `read:n3-estrutura-06-01` | コーヒーをスプーン１**杯**入れます | ばい | **ぱい** (bank: ぱい) | 一杯 = いっぱい; いちばい means "one-fold". |
| `read:n3-perspectiva-05-02` | 図書館は午前**九**時から | きゅう | **く** (bank: く) | 九時 is くじ. |
| `read:n4-conectores-03-01` | 一日または**二**日ください | ふた | **ふつ** (bank: ふつ) | 二日 = ふつか; the box currently spells ふたか. |
| `read:n4-forma-simples-03-01` | あと**1日**しかない | ついたち | **いちにち** (bank: いちにち) | ついたち = the 1st of the month; here "one more day". |
| `read:n4-oracoes-relativas-07-01` | 2月は28**日**までしかない | か | **にち** (bank: にち) | 28日 = にじゅうはちにち. (The `28` token is also broken — see A3.) |
| `read:n3-relato-07-02` | 着の身**着**のままで | ぎ | **き** (bank: き) | The set phrase is きのみきのまま; the box reads the first 着 as き and the second as ぎ. |
| `read:n3-causa-01-01` | 風が強いのはビル**風**のせいです | ふう | **かぜ** (bank: かぜ) | ビル風 = ビルかぜ; the same box reads the bare 風 two tokens earlier as かぜ. |
| `read:n4-keigo-04-01` | **何時**にお出かけになりますか | いつ | **なんじ** (bank: なんじ) | Its own pt-BR is "**A que horas** o senhor vai sair?"; いつに is not idiomatic. |
| `read:n4-keigo-05-01` | 朝食は**何時**にいたしますか | いつ | **なんじ** (bank: なんじ) | Same; pt-BR "A que horas". 3 other boxes read 何時に as なんじ. |
| `read:n4-revisao-01-01`, `read:n3-enfase-07-02`, `read:n3-limites-03-01`, `read:n3-perspectiva-03-01`, `read:n3-revisao-01-01` | 母に**言う**べき / 経験が物を**言う** / 目は口ほどに物を**言う** / …と**言う** ×2 | ゆう ×5 | **いう** | ゆう is the spoken elision, not a furigana form; the same corpus reads 言う as いう in 9 other tokens. Shipping 言(ゆ)う teaches a spelling that does not exist. |

- Fix: re-derive these 33 readings from the bank tokens (which are correct in 24 of the 26 comparable cases),
  and add a validator rule to `validate_readings.py`: **a box token's `r` must equal the `reading` the bank
  assigns to the same surface in the same source sentence.**

### A3 — Numbers are read digit-by-digit, and `0` is read れい: 29 tokens in 23 boxes

The reading builder walks numerals character by character and maps `0` → れい, so place value is destroyed.

| box | surface (context) | shown | should be |
|---|---|---|---|
| `read:n3-desejos-07-02` | ５００００円 | ごれいれいれいれい | **ごまん** |
| `read:n4-transitividade-04-01` | ５０００円 | ごれいれいれい | **ごせん** |
| `read:n3-concessao-07-01` | ４０００以上 | よんれいれいれい | **よんせん** |
| `read:n3-enfase-02-01` | １００ドル | いちれいれい | **ひゃく** |
| `read:n3-perspectiva-02-01` | 200ドル | にれいれい | **にひゃく** |
| `read:n4-causativa-02-01` / `n4-oracoes-relativas-02-01` | ３０分 / ３０？ | さんれい | **さんじゅっ** / **さんじゅう** |
| `read:n4-experiencia-05-01` ×1, `read:n3-relato-01-01`, `read:n3-tempo-05-01` | ２０分 / ２０歳 | にれい | **にじゅっ** / **にじゅっ** |
| `read:n4-revisao-03-01`, `read:n3-concessao-07-01`, `read:n3-perspectiva-03-01`, `read:n3-tempo-01-01` | １０分 / 10点 / 10ヶ国 / １０マイル | いちれい | **じゅっ** / **じゅっ** / **じゅっ** / **じゅう** |
| `read:n3-desejos-05-02` | ６０点 | ろくれい | **ろくじゅっ** |
| `read:n3-relato-06-02` | ４０度 | よんれい | **よんじゅう** |
| `read:n4-experiencia-05-01` ×2 | １５分 | いちご | **じゅうご** |
| `read:n4-oracoes-relativas-02-01`, `read:n4-suposicao-07-01`, `read:n3-concessao-04-01` | １３って / １３人 / 13にして | いちさん | **じゅうさん** |
| `read:n3-conjectura-06-01` | ３６人 / １８日 / １９日 | さんろく / いちはち / いちきゅう | **さんじゅうろく** / **じゅうはち** / **じゅうく** |
| `read:n4-oracoes-relativas-07-01` | 28日 | によう | **にじゅうはち** |
| `read:n3-deveres-05-01` | ８つの学部 | よう | **やっ** |
| `read:n3-causa-06-02`, `read:n3-perspectiva-05-01` | ２つ | ふつ | **ふた** |
| `read:n3-tempo-05-02` | ４時 | よん | **よ** |

- Learner impact: bare-digit surfaces do not get ruby, so these are **data-only today** — except `1日`
  (A2) and `28日`, whose 日 token does render. They will surface the moment `show="romaji"` is used, and they
  are already wrong in the exported corpus.
- Note the builder gets `１７日→じゅうしち`, `３万→さんまん`, `５千→ごせん`, `２人→ふたり`, `１度→いちど`,
  `１１９→いちいちきゅう` right, so the fix is a numeral-reading pass, not a rewrite.
- Fix: read the numeral as a whole (with the following counter for gemination/rendaku), or copy the bank's
  reading for the same token — the bank is correct in all 20 comparable cases.

### A4 — 32 boxes glue sentences together with no punctuation, producing run-ons that misparse

53 junctions across 32 boxes: the preceding source sentence has no `。！？」`, and the assembler concatenates
with no separator. Worst cases:

- `read:n3-conjectura-07-02` — **five** sentences, zero internal punctuation:
  > `どんどんガソリンの値段が上がります親はすぐにこどもを病院に連れてくる私が今こうして、二日分の日記を書く中学校の２年生が職場体験をしました子どもを連れ去る所を近所の人が見た`
  A learner parses `…病院に連れてくる私が今こうして…` as one relative clause ("I, who take children to
  hospital…"). The pt-BR reveal correctly shows five separate sentences, so the JP and its translation do
  not line up sentence-for-sentence.
- `read:n4-experiencia-04-01` — 60 characters, four sentences, no punctuation at all:
  > `そのおもちゃはプラスチックでできているワインはぶどうから作りますこのいすは木でできているワインはぶどうからできる`
- `read:n4-obrigacao-04-01` — `あした早く起きないと` + `おれの言うとおりではないか。` glue into
  `…起きないとおれの言うとおりではないか` , which reads as a single conditional ("if I don't get up early, it's
  just as I said").
- `read:n4-keigo-04-01` (3 junctions), `read:n4-passiva-04-01` (3), `read:n4-conectores-02-01` (2, and one of
  them is a stray half-width space, see B4), `read:n4-conectores-04-01` (2), `read:n4-condicionais-08-01` (2),
  `read:n4-conectores-07-01` (2), `read:n4-potencial-01-01` (2).
- Cause: 34 of the 53 junctions come from `jp_source: ai-generated` bank sentences (house rule drops `。` on
  generated JP) and 19 from JEC sentences that ship without a final `。`. Either way the **box** is where they
  become a run-on.
- Fix: in the assembler, append `。` when a selected sentence does not already end in a sentence-final mark
  (and re-run the token stream so the added `。` is a token). This is a one-line rule and it fixes all 53.

### A5 — 25 boxes select two source sentences that say the same thing; 10 of them show the learner the identical pt-BR twice

The reveal panel literally repeats a sentence, which reads as a stutter rather than as connected text.
Identical-pt-BR cases:

| box | the two JP sentences | repeated pt-BR |
|---|---|---|
| `read:n5-numeros-tempo-06-01` | `おはよう。` / `おはよう！` | "Bom dia. Bom dia!" — this is the **entire** box |
| `read:n5-numeros-tempo-07-01` | `ようこそ！` / `ようこそ。` | "Bem-vindo! Bem-vindo." |
| `read:n4-dar-receber-02-01` | `私に教えてくれる？` / `教えてくれるか？` | "Você me ensina? Você me ensina?" |
| `read:n4-dar-receber-04-01` | `聞いてくれてありがとう。` / `聞いてくれてありがとう！` | "Obrigado por me escutar. Obrigado por me escutar!" |
| `read:n4-volitivo-06-01` | `目を開けなさい。` / `目を開きなさい。` | "Abra os olhos. Abra os olhos." |
| `read:n3-conjectura-01-01` | `天気は持つかなあ。` / `天気が持つかなあ。` | "Será que o tempo vai aguentar? Será que o tempo vai aguentar?" |
| `read:n3-conjectura-02-01` | `両方とも好きというわけではない。` / `両方とも好きなわけではない。` | "Não é que eu goste dos dois." (sentences 1 and 5) |
| `read:n3-concessao-02-01` | `「何の話してるの？」「分かってるくせに」` / `「何を話してるの？」「知ってるくせに」` | the same two-line dialogue twice |
| `read:n3-estrutura-05-01` | `…忘れてはなりません。` / `…忘れてはいけません。` | "Você não pode esquecer o livro de matemática de novo." ×2 |
| `read:n3-limites-02-01` | `私はこれだけしか知りません。` / `ぼくはこれだけしか知らない。` | "Eu só sei isto. Eu só sei isto." |
| `read:n3-relato-06-01` | `カメラにフィルムを入れるのを忘れた。` / `カメラにフィルムを入れ忘れちゃった。` | "Esqueci de colocar o filme na câmera." (box softened the 2nd to "Acabei esquecendo…") |

15 more are ≥0.80-similar rather than identical (`read:n5-passado-04-01`, `read:n4-aspecto-05-01`,
`read:n4-condicionais-05-01`, `read:n4-experiencia-01-01`, `read:n4-keigo-02-01`, `read:n4-suposicao-02-01`,
`read:n4-transitividade-01-01`, `read:n3-concessao-01-01`, `read:n3-concessao-04-01`, `read:n3-desejos-01-01`,
`read:n3-deveres-03-01`, `read:n3-estado-02-01`, `read:n3-estrutura-06-01`, `read:n3-limites-06-02`,
`read:n4-dar-receber-04-01` 2nd pair).

- Fix: add a dedupe step to the selector — reject a candidate whose normalised pt-BR is ≥0.80 similar to a
  sentence already chosen for the box, and pull the next i+0 candidate instead.

### A6 — Pairings that read as contradiction or non-sequitur, not as a themed passage

`design/reading_practice.md` §5 accepts "a themed set of true sentences, not a flowing story". These go past
that: the sentences actively fight each other, usually because a shared referent (`彼`, a greeting) implies
continuity that the content contradicts.

- `read:n5-numeros-tempo-04-01` — `あなたのせいです。おやすみなさい。` → "A culpa é sua. Boa noite." An
  accusation followed by a bedtime farewell.
- `read:n5-perguntas-04-01` — `ネズミでした。こんにちは。` → "Era um rato. Boa tarde." The greeting lands last.
- `read:n5-perguntas-05-01` — `さようなら。わがままね。` → "Até logo. Você é egoísta, né."
- `read:n5-adjetivos-04-01` — `どこに行くところですか。ありがとうございます！` → "Aonde você está indo? Muito
  obrigado(a)!"
- `read:n5-verbos-05-01` — `クリップってある？クソっ。かかれ！` → "Tem clipe (de papel)? Droga! Vai logo!"
- `read:n3-relato-04-01` — "Ele é famoso como médico." immediately followed by "Ele é **incompetente** como
  médico." about the same 彼.
- `read:n3-tempo-04-01` — `スプーンとフォークとナイフが要る。どうも。` → "Preciso de uma colher, um garfo e uma
  faca. **Obrigado.**" — `どうも。` is a whole source sentence dropped in as a two-word fragment.
- `read:n3-estrutura-03-01` — five disconnected passive clauses about "ele": "Ele recebeu uma aposentadoria.
  Ele foi confundido com o irmão mais novo. Ele recebeu uma função. Zombaram dela. Ele foi pego pela própria
  palavra." This is a conjugation drill, not a passage.
- `read:n4-aspecto-04-01` — four ways to say "I'll try": "Pretendo experimentar fazer. Vou tentar mais uma
  vez. Vou tentar. Vou tentar fazer."
- Fix: these are selection-time problems. A cheap, mechanical improvement: forbid a greeting/leave-taking
  (`おはよう`, `こんにちは`, `さようなら`, `ようこそ`, `おやすみ`) in any position but the first, and prefer
  candidates that share a `theme_topic` tag with the lesson over ones that merely pass the i+0 gate.

### A7 — Content unsuitable for a course reading box

- `read:n3-desejos-07-01` — `ああ、ひょっとしたら今夜は・・・。` … `性病にかかっているかもしれません。` →
  "Ah… talvez esta noite… … **Pode ser que eu esteja com uma doença sexualmente transmissível.**" The
  adjacency manufactures an implication that is not in either source sentence.
- `read:n3-causa-05-02` — `私よりもっとエッチな人もいて安心しました。` → "Fiquei aliviado(a) ao ver que também há
  gente **mais safada** do que eu." — dropped between "we're out of money" and "a foreigner asked me where the
  station was".
- `read:n3-tempo-05-02` — `女の子みたいにメソメソするのはやめろ。` → "Para de choramingar **feito
  menininha**."
- `read:n5-verbos-05-01` (`クソっ` → "Droga!") and `read:n4-forma-simples-04-01` (`ちくしょう！` → "Droga!") put
  expletives in N5/N4 boxes with no register warning, though `design/translation_style.md` §2 asks that
  genuinely vulgar items be flagged so the UI can warn.
- Fix: add an exclusion list to the selector for `register: vulgar|slang` and for sexual-health/sexual-content
  tags, and re-select those five boxes. None of them needs these sentences to satisfy its i+0 gate.

### A8 — `translation["en"]` was re-authored away from the trusted English and is wrong in 5 boxes

The bank's `en` is the trusted human (Tatoeba) translation and is the cross-check anchor per
`design/reading_practice.md` §5b. 9 boxes diverge from `concat(bank en)`; in 5 the box's own English is wrong.
The pt-BR is correct in all five, so only `en` needs fixing.

| box | JP | box `en` | correct |
|---|---|---|---|
| `read:n4-dar-receber-01-01` | `こらしめてやる。` | **"I'm gonna shoot him."** | "I'll teach him a lesson." (pt-BR has "Vou dar uma lição nele!") |
| `read:n5-te-form-06-01` | `人をからかわないで。` | **"Are you kidding?"** | "Don't make fun of people." (bank had it right; pt-BR: "Não zoa as pessoas.") |
| `read:n3-limites-06-02` | `…三つの問題がある。` + `…３つの意見がある。` | **"…three opinions."** twice | first is "…there are three **problems**" (pt-BR distinguishes them correctly) |
| `read:n3-deveres-03-01` | `負け犬になるわけにはいかない。` | **"I can't stand getting beaten."** | "I can't let myself become a loser." (pt-BR: "Não dá para eu virar um fracassado.") |
| `read:n3-conjectura-02-01` | `両方とも好きというわけではない。` | **"I do not like either of them."** | "It's not that I like both of them." — total negation instead of the partial negation that is this lesson's grammar point (pt-BR: "Não é que eu goste dos dois."). |
- Fix: restore `concat(bank en)` where the bank has an `en`; for the 4 sentences where the bank's `en` is
  missing, translate from the JP and cross-check against the pt-BR (which is right in every case above).

### A9 — pt-BR that contradicts the box's own grammar point, inconsistently within one box

- `read:n3-intencao-02-01` (gated to the ことになっている lesson) — `何をすることになっているかわからない。` →
  **"Não sei o que devo fazer."** That is べき ("should"), not ことになっている ("what has been arranged").
  The same box renders the pattern correctly twice ("Está combinado que…").
  Fix: **"Não sei o que ficou combinado que eu faça."**
- `read:n3-limites-04-01` (gated to the とは限らない lesson) — `彼は毎日ここへくるとは限らない。` →
  **"Ele não vem aqui todos os dias."** — a flat assertion where the pattern means "not necessarily". The
  next two sentences in the same box use "nem sempre" for the same pattern.
  Fix: **"Não é sempre que ele vem aqui todo dia."**

### A10 — pt-BR naturalness regressions introduced on top of the bank

22 boxes edit the bank's pt-BR. Most edits are improvements (e.g. `read:n4-conectores-03-01` fixes
"Eu prático" → "Eu pratico"). These four go the other way, against `design/translation_style.md` §1
("natural translation, NOT a literal mirror"):

- `read:n3-causa-07-02` — `ぬくもりなどどこにも見つからない。` → box: **"Calor humano (aconchego), coisa
  nenhuma, não se encontra em lugar algum."** The bank had the natural "Calor humano é coisa que não se
  encontra em lugar nenhum." The box mirrors など+どこにも word-for-word and the result is not Portuguese.
  Fix: restore the bank string.
- `read:n3-causa-01-01` — `風が強いのはビル風のせいです。` → **"O vento estar forte é por causa do efeito de
  túnel entre os prédios."** The のは nominalisation is mirrored literally.
  Fix: **"O vento está forte por causa do efeito de túnel entre os prédios."**
- `read:n3-causa-05-01` — `あなたが今あるのはだれのおかげなのですか。` → **"Você deve a quem o que é hoje?"** —
  scrambled word order. Fix: **"A quem você deve o que é hoje?"**
- `read:n3-causa-05-01` — `どうしても見えるところに目がいってしまう。` → **"Faça o que fizer, meus olhos acabam
  indo para onde dá para ver."** "Faça o que fizer" addresses *you* while the clause is about *my* eyes.
  Fix: **"Por mais que eu tente, meus olhos acabam indo para a parte que está à mostra."**

### A11 — All 286 titles are the placeholder "Leitura" / "Reading"

- `title` is `{"pt-BR": "Leitura", "en": "Reading"}` in **286 of 286** records — one distinct value each.
  `design/reading_practice.md` §4 specifies a themed title (`{"pt-BR": "No café", "en": "At the café"}`) and
  `corpus/readings/INDEX.md` documents `title` as a per-box field.
- Honest severity note: `renderReading` hard-codes the label "Leia em japonês" and never reads `title`, so
  nothing is visibly wrong in the prototype today — but the field is exported, is part of the published
  record shape, and is dead weight in its current state. It also cannot be filled by a mechanical pass: a
  themed title only exists if the box is themed (see A6).
- Fix: either populate `title` when the selector is re-run (name it after the shared topic of the chosen
  sentences), or drop the field from the schema. Keeping 286 copies of "Leitura" is the worst of the three.

---

## B. Data-only defects (correct-looking today, wrong in the exported corpus)

### B1 — `ro` disagrees with its own `r` on 6 tokens
- `read:n3-estrutura-02-01` — `何` : `r: なに`, `ro: **nan**` (×3 tokens in the box).
- `read:n3-intencao-04-02` — `入れる` : `r: はいれる`, `ro: **ireru**`.
- `read:n3-intencao-04-02` — `１日` : `r: いちにち`, `ro: **tsuitachi**`.
- `read:n3-intencao-06-02` — `七` : `r: しち`, `ro: **nana**` ; `４` : `r: よ`, `ro: **yon**`.
- `read:n4-causativa-02-01` — `分` : `r: ぷん`, `ro: **fun**`.
- Fix: regenerate `ro` from `r` for the whole file; these are the only 6 that a kana→romaji round-trip cannot
  explain (the other 144 differences are the project-wide `ー`→`-` convention, which `corpus/vocab/*.json`
  also uses — `su-pa-`, `depa-to` — and the `っ`-assimilation convention, both consistent and out of scope).

### B2 — the same kana gets two different romaji
- `ぱーてぃー` → `pa-tei-` in `read:n3-concessao-06-01` and `read:n3-concessao-06-02`, but `pa-ti-` in
  `read:n3-tempo-05-01`. Same word (パーティー), same reading, two spellings.
- Fix: one converter, one pass.

### B3 — a whitespace token is given the reading きごう ("symbol")
- `read:n4-conectores-02-01` (1) and `read:n4-conectores-03-01` (2): `{"s": " ", "r": "きごう", "ro": "kigou",
  "pos": "whitespace"}`. The romaji line would read `… oishii desu **kigou** sore ni …`.
- Fix: emit `r: " "`, `ro: ""` for `pos: whitespace` (or drop the token and normalise the space away, which
  also helps A4).

### B4 — two more tokenisation artefacts in the romaji stream
- `read:n5-particulas-lugar-07-01` — `かっけー！` splits into `かっ`/`kak` + `けー`/`ke-`, so the romaji line
  reads `kak ke- !` instead of `kakkee`.
- `read:n5-verbos-05-01` — the `っ` of `クソっ` is tagged `pos: punctuation` with `ro: ""`, so the gemination
  disappears from the romaji line (`kuso .`).

### B5 — `ai_generated: false` on 21 boxes whose Japanese is partly AI-generated
- 42 of the 1,321 source sentences have `provenance.jp_source: "ai-generated"`. They appear in **21 boxes**,
  and **2 boxes are 100% generated JP** (`read:n4-experiencia-04-01`, `read:n4-condicionais-04-01`).
  All 286 boxes carry `ai_generated: false`, and `corpus/readings/INDEX.md` states the boxes are
  *"assembled by **SELECTION** … (no generation): real **Tatoeba (CC BY 2.0 FR)** / **JEC (CC BY 3.0)**
  Japanese, human EN"*.
- Why it matters: spec §1.2 makes `ai_generated: true` the flag that routes generated Japanese to the
  heaviest human review. These 21 boxes are currently indistinguishable from the 265 that really are
  human-written text.
- Fix: set `ai_generated: true` on boxes containing ≥1 `jp_source: ai-generated` sentence (or add
  `contains_generated: true`), and soften the INDEX.md sentence to "predominantly Tatoeba/JEC".

### B6 — three boxes wrap part of the pt-BR in quotation marks that exist nowhere in the JP
- `read:n5-verbos-05-01` — `クリップってある？クソっ。かかれ！` → `Tem clipe (de papel)? **"Droga! Vai logo!"**`
- `read:n4-condicionais-05-01` — → `**"Tomara que eu possa vê-lo, né?"** Tomara que a gente possa se ver…`
- `read:n4-causativa-03-01` — the A1 leak, which also opens with a stray quote.
- (`read:n3-causa-03-01`'s `"UN"` is legitimate — it quotes a term.)
- Fix: strip the quotes; none of the three JP passages contains `「」`.

### B7 — `length_band` encodes sentence count, not length
- `short` = exactly 2 sentences (10–24 chars), `paragraph` = 2–5 sentences (**14**–127 chars), `long` =
  6 sentences (56–139 chars). So `read:n5-particulas-lugar-07-01` (14 chars, `かっけー！おはようございます`) is
  `paragraph` while `read:n5-te-form-04-01` (24 chars) is `short` — the bands overlap and invert.
  `design/reading_practice.md` §6 defines the bands by length ("1–3 sentences" / "short paragraph (3–6)" /
  "paragraph → multi-paragraph").
- Fix: derive the band from character count with fixed thresholds, or rename the field `sentence_count`.

### B8 — ungrammatical Japanese shipped as model reading text
- `read:n3-tempo-02-01` contains two malformed source sentences:
  `少女はそんな**人な**ことは聞いたこともないと言った。` (should be そんな人のこと / そんなことは) and
  `私たちはいつ**そこの**たどり着くことになるだろうか。` (should be そこに).
  The same box also opens onto `ドルペッグの意味は、強い国につけということです。` → "O significado de 'dollar
  peg' é: atrele-se aos países fortes." — currency-peg jargon in an N3 reading box.
- Fix: drop these three sentences from the box and re-select; the errors are inherited from Tatoeba and
  should be corrected in the bank as well.

### B9 — the same word rendered two ways inside one box
- `read:n4-conectores-04-01` — `この店は安いしおいしい` → "Esse **restaurante** é barato e ainda por cima é
  gostoso." then `あの店は安いしおいしい` → "Aquela **loja** é barata e ainda por cima a comida é gostosa."
  Identical JP frames, two different pt-BR nouns, adjacent in one passage.
- Fix: use "restaurante" in both (the sentence is about food).

---

## Counts

| unit | checked | flagged |
|---|---|---|
| reading boxes (`corpus/readings/*.json`) | 286 | **121** distinct boxes carry ≥1 finding |
| box `title` (locale-object) | 286 | 286 (A11 — all placeholder) |
| box `translation["pt-BR"]` | 286 | 9 (A1 ×1, A9 ×2, A10 ×3 boxes, B6 ×3 — overlaps counted once) |
| box `translation["en"]` | 286 | 5 (A8) |
| passage coherence (`jp` as connected text) | 286 | 66 (A4 ×32 + A5 ×25, 1 box in both; A6 ×10, of which 8 are new) |
| tokens — furigana `r` on kanji surfaces | 2,797 | 33 (A2) |
| tokens — readings on numeral surfaces | 69 | 29 (A3) |
| tokens — `ro` vs `r` consistency | 11,113 (tokens with a pure-kana `r`) | 6 (B1) + 2 artefacts (B4) + 3 whitespace (B3) |
| tokens — total in the three files | 12,618 | 73 |
| provenance flag `ai_generated` | 286 | 21 (B5) |
| `length_band` | 286 | 286 (B7 — systemic mis-definition) |

**Findings: 20** (A1–A11, B1–B9). Clean on: `source_slugs` resolution (286/286), `jp` ↔ token-stream
integrity (286/286), `jp` ↔ `concat(source jp)` integrity (286/286), single-kanji readings vs the kanji
registry (0 illegal readings), and `needs_review: true` / `layer: "B"` on all 286.
