# QA sweep — reading-practice boxes, quality

**Scope:** `corpus/readings/n5.json` (43), `n4.json` (91), `n3.json` (152) — **all 286 boxes**, read in full.
**Checked per box:** does the assembled `jp` read as coherent connected text; is the `title` apt; is
`translation["pt-BR"]` faithful to the `jp` and natural pt-BR; is `translation["en"]` faithful; is every token
`r` the correct reading for its `s` **in context** (furigana); is every token `ro` consistent with its `r`.
**Method:** full manual read of all 286 `jp` / `pt-BR` / `en` / `title`; mechanical audits over all 12,618
tokens (kana→romaji round-trip with the project's own `ー`/`っ`/`は→わ` conventions, numeral-plus-counter
table, kanji-surface reading table); every box diffed against its `source_slugs` in
`corpus/sentences/bank.json` for jp integrity, reading drift, translation drift, redundancy and junction
punctuation.
**Authority:** `design/translation_style.md`, `design/reading_practice.md`, `corpus/readings/INDEX.md`.

**Renderer context (severity calibration).** `prototype/app/lib/render-body.server.ts:211` `tokenRuby`
emits `<ruby>` **only when the surface contains kanji**; `renderReading` (`:226`) hard-codes the header label
`"Leia em japonês"` and **never reads `title`**, emits the romaji line only when `show="romaji"|"both"`, and
reveals only the **pt-BR**. Every `<reading>` tag in `course/` is bare `<reading ref="…"/>`. So today the
learner sees exactly: **`jp`, the `r` of kanji-bearing tokens as furigana, and `translation["pt-BR"]`.**
`title`, `en`, `ro`, `length_band` and `ai_generated` are exported-corpus-only. Section A is what reaches the
learner; section B is wrong only in the data. Both are wrong in the source of truth.

**Clean on:** `source_slugs` resolution (286/286 resolve in the bank), `"".join(t.s) == jp` (286/286),
`strip_punct(concat(source jp)) == strip_punct(jp)` (286/286), `needs_review: true` and `layer: "B"`
(286/286), `translation` present in both locales (286/286), no em-dash anywhere in title or translation
(0 occurrences — `translation_style.md` §4 holds).

> **Caveat on the `bank:` cross-references.** `corpus/readings/*.json` was unmodified in the working tree
> throughout this sweep, so every finding about the boxes themselves is stable. `corpus/sentences/bank.json`
> was being edited concurrently (an `en`-anchor backfill is in flight), so the "bank has X" columns are
> corroborating evidence read at one point in time, not a claim about the bank's final state. Every reading
> and translation verdict below is argued from the Japanese itself and stands on its own.

> **Note on this file.** It replaces an earlier report at this path (recoverable with
> `git show 6930f528:research/reports/qa_sweep/readings_quality.md`). That report is now partly stale: its
> reading defects (行っ→おこなっ, 上手→かみて, 分別→ぶんべつ, 通り in `n3-causa-06-01`, 金→きん, 何時→いつ,
> 言う→ゆう ×5, the digit-by-digit numerals, 28日, 一本/二本, 九時 …) have all been **fixed**, and 140 of the
> 286 titles have been authored. This sweep is against the current file and reports only what is wrong now.

---

## A. Learner-visible defects

### A1 — 146 of 286 boxes still ship the placeholder title `"Leitura"` / `"Reading"`; the authoring pass stopped half-way

`title` is `{"pt-BR": "Leitura", "en": "Reading"}` in **146 boxes** (45 N4, 101 N3). The other 140 carry real,
mostly apt titles (`"Um biscoito enquanto espera"`, `"Fresco demais para julho"`, `"A porta que se abriu
sozinha"`). The split is not random — it is an interrupted pass: **17 topics are 100% placeholder, 3 are
mixed, and every other topic is 100% authored.**

| fully placeholder (17 topics) | mixed |
|---|---|
| `n4-obrigacao` (5), `n4-oracoes-relativas` (7), `n4-passiva` (4), `n4-potencial` (4), `n4-revisao` (3), `n4-suposicao` (8), `n4-transitividade` (5), `n4-volitivo` (7), `n3-causa` (12), `n3-concessao` (10), `n3-conectores` (12), `n3-conjectura` (10), `n3-limites` (11), `n3-perspectiva` (11), `n3-relato` (11), `n3-revisao` (1), `n3-tempo` (13) | `n3-desejos` 7/10, `n3-intencao` 3/11, `n4-keigo` 2/6 |

- Why it matters: `design/reading_practice.md` §4 specifies a themed title, and `INDEX.md` documents `title`
  as a per-box field. Half the registry now holds a value that carries no information, and the two halves are
  inconsistent with each other — a reviewer cannot tell "not yet titled" from "deliberately untitled".
- Honest severity: `renderReading` never reads `title`, so nothing is visibly broken in the prototype today.
- Fix: finish the pass over the 17 topics + 3 mixed topics listed above, using the same naming convention the
  first 140 already use (name the shared topic of the chosen sentences). The three mixed topics show the pass
  died mid-topic, so start there.

### A2 — 6 furigana readings are wrong for the surface in context, and every one contradicts its own source sentence

All 6 surfaces contain kanji, so `tokenRuby` renders them and the learner is shown the wrong reading. All
2,797 kanji-bearing tokens were checked against the reading the bank assigns the same surface in the same
source sentence; these 6 are the only disagreements where the box is the wrong side.

| box | fragment (ruby shown to learner) | box `r` | should be | why |
|---|---|---|---|---|
| `read:n4-volitivo-07-01` | 気に**入っ**てくれるといいな | はいっ | **いっ** | 気に入る is きにいる, never きにはいる. The bank has いっ; the box's own pt is "Tomara que ele goste". |
| `read:n3-conjectura-04-01` | **何**も浮かばない | なん | **なに** | 何も is なにも. Bank: なに. pt: "não me ocorre nada". |
| `read:n3-conjectura-06-02` | もしもし、**何**か手伝うことが | なん | **なに** | 何か is always なにか. Bank: なに. |
| `read:n3-revisao-01-01` | この世のことは、**何**もかも知る | なん | **なに** | 何もかも is なにもかも. Bank: なに. |
| `read:n3-conjectura-07-02` | **二**日分の日記を書く | ふた | **ふつ** | 二日分 = ふつかぶん. The box already reads 日 as か, so it currently spells **ふたか**. Bank: ふつ. |
| `read:n3-deveres-03-01` | 何事も思い**通り**にするわけには | とおり | **どおり** | 思い通り rendakus: おもいどおり. Bank: どおり. `read:n3-causa-06-01` gets the identical compound right (どおり). |

- Fix: copy the bank's reading for these 6 tokens, and add the rule the earlier round evidently applied by
  hand as a validator in `scripts/validate/validate_readings.py`: **a box token's `r` must equal the reading
  the bank assigns to the same surface in the same source sentence.** That single rule would have caught all
  6 (and would have caught the whole previous round mechanically).
- Corroborating, out of my scope: 5 tokens drift the *other* way — the box correctly reads 言う as いう where
  the bank still has ゆう (`read:n4-revisao-01-01`, `n3-enfase-07-02`, `n3-limites-03-01`,
  `n3-perspectiva-03-01`, `n3-revisao-01-01`). The bank is the side that needs fixing there.

### A3 — 7 English translations were invented, and all 7 are wrong; they occur exactly where the bank has no `en`

`design/reading_practice.md` §5b makes the human Tatoeba English the anchor the pt-BR is cross-checked
against. Only 3 boxes' `en` differ from `concat(bank en)` at all — but 7 source sentences have **no `en` in
the bank**, and for every one of them the box has supplied English of its own. Every one is a mistranslation,
and in 5 of 7 the box's own pt-BR is correct and contradicts it.

| box | jp | box `en` | why it is wrong | correct |
|---|---|---|---|---|
| `read:n4-dar-receber-01-01` | `こらしめてやる。` | **"I'm gonna shoot him."** | こらしめる = punish / teach a lesson. Nothing about shooting. | "I'll teach him a lesson." (pt: "Vou dar uma lição nele!") |
| `read:n4-condicionais-02-01` | `あなたに会ってほしいのですが。` | **"I'd like for you to go."** | 会う = meet, not go. | "I'd like you to meet me." (pt: "Eu gostaria que você me encontrasse") |
| `read:n3-causa-01-01` | `おかげで元気にしております。` | **"They're all fine, thank you."** | 〜しております is 1st-person humble; the box turns it into 3rd-person plural. | "I'm doing well, thanks to you." (pt: "Graças a você, vou indo bem.") |
| `read:n3-conjectura-02-01` | `両方とも好きというわけではない。` | **"I do not like either of them."** | Total negation where the box's own grammar point (`n3-wake-dewa-nai`) is *partial* negation. | "It's not that I like both of them." (pt is right) |
| `read:n3-conjectura-02-01` | `両方とも好きなわけではない。` | **"I don't like either of them."** | Same, same box, 4 sentences later. | same |
| `read:n3-deveres-03-01` | `負け犬になるわけにはいかない。` | **"I can't stand getting beaten."** | 負け犬になる = become a loser; わけにはいかない = can't let oneself. | "I can't let myself become a loser." (pt: "Não dá para eu virar um fracassado.") |
| `read:n3-limites-06-02` | `この問題に関しては三つの問題がある。` | **"…there are three opinions."** | 問題 = problems. The box copied the *next* sentence's `en` verbatim, producing the identical-`en` pair in A5. | "…there are three problems." (pt distinguishes them correctly) |

- Fix: for these 7, translate from the JP with the pt-BR as the cross-check (it is right in 5 of 7), or leave
  `en` absent rather than fabricating it. Better: make the assembler **refuse to invent `en`** — if a source
  sentence has no trusted English, either omit that segment from `en` or disqualify the sentence, per §5b.
- The 3 remaining `en` divergences from the bank: `read:n5-te-form-06-01` ships **"Are you kidding?"** for
  `人をからかわないで。` while the bank now has the correct "Don't make fun of people." (the box is stale —
  re-export); `read:n4-volitivo-05-01` and `read:n4-passiva-04-01` differ only cosmetically and are fine.

### A4 — 53 junctions in 32 boxes glue sentences together with no punctuation, and several genuinely misparse

When a selected sentence does not end in `。！？」`, the assembler concatenates the next one directly onto it.
Cause: 34 junctions come from `jp_source: ai-generated` bank sentences (house rule drops `。` on generated JP,
`translation_style.md` §3) and 19 from JEC sentences that ship without a final `。`. Either way the **box** is
where they become a run-on the learner has to parse.

Cases where the glue creates a false constituent, not just a missing pause:

- `read:n3-conjectura-06-01` — `…社会のルールを守る` + `３６人が１８日と１９日の会議に出席する` →
  `…しっかり社会のルールを守る３６人が１８日と…`. Reads as one relative clause, "the 36 people who firmly
  observe the rules of society", which is not what either sentence says. The pt reveal shows them as two.
- `read:n3-relato-06-02` — two junctions: `…４０度近くまで熱が出た` + `二人の生徒が…` → "the two students who
  ran a 40-degree fever"; then `…１台のコンピュータを使う` + `話してる最中に…` → "while talking about using
  one computer".
- `read:n4-obrigacao-04-01` — `あした早く起きないと` + `おれの言うとおりではないか。` →
  `…起きないとおれの言うとおりではないか`, a single conditional ("if I don't get up early, it's just as I said").
- `read:n4-conectores-03-01` — `…たとえばこの漢字` + `スポーツをします…` → `…たとえばこの漢字スポーツをします…`,
  i.e. "this kanji sport".
- `read:n3-conjectura-07-02` — **five** sentences, zero internal punctuation across 4 junctions:
  `…値段が上がります親はすぐにこどもを病院に連れてくる私が今こうして、二日分の日記を書く中学校の２年生が…`
- `read:n4-experiencia-04-01` — 4 sentences, 60 characters, **no punctuation at all**.
- Also 3 junctions each in `read:n4-passiva-04-01` and `read:n4-keigo-04-01`; 2 each in
  `n4-volitivo-07-01`, `n4-transitividade-01-01`, `n4-suposicao-06-01`, `n4-suposicao-01-01`,
  `n4-potencial-01-01`, `n4-conectores-07-01`, `n4-conectores-04-01`, `n4-conectores-02-01`,
  `n4-condicionais-08-01`.
- **Two of them additionally contain a half-width space inside the Japanese**, the only whitespace in all 286
  boxes: `read:n4-conectores-02-01` (`この店は安いです␣それに料理も…`) and `read:n4-conectores-03-01` (×2).
  See B3 for the token those spaces carry.
- Fix: in the assembler, append `。` when a selected sentence does not already end in a sentence-final mark,
  and re-tokenise so the added `。` is a token. One rule fixes all 53. Normalise the 3 stray spaces away at the
  same time.

### A5 — 22 boxes repeat themselves; in 17 the learner is shown the identical sentence twice

The reveal panel literally prints the same sentence twice, which reads as a stutter, not as connected text.

**Identical string in `translation["pt-BR"]` (6 boxes — learner-visible):**
`read:n4-dar-receber-02-01` "Você me ensina?" ×2 · `read:n4-volitivo-06-01` "Abra os olhos." ×2 ·
`read:n3-conjectura-01-01` "Será que o tempo vai aguentar?" ×2 · `read:n3-conjectura-02-01` "Não é que eu
goste dos dois." (sentences 1 and 5) · `read:n3-estrutura-05-01` "Você não pode esquecer o livro de matemática
de novo." ×2 · `read:n3-limites-02-01` "Eu só sei isto." ×2.

**Identical string in `translation["en"]` (11 boxes — data-only today):** `n5-numeros-tempo-06-01`,
`n5-numeros-tempo-07-01`, `n4-experiencia-04-01`, `n4-keigo-02-01`, `n4-volitivo-06-01`, `n3-conjectura-01-01`,
`n3-desejos-01-01`, `n3-estrutura-05-01`, `n3-estrutura-06-01`, `n3-limites-06-02`, `n3-tempo-03-01`.
Four of these are worse than redundancy — they erase the distinction the lesson is teaching:

- `read:n4-keigo-02-01` — `お茶を飲みながら話しませんか。` and `…話しましょう。` both get
  "Let's talk over a cup of tea, shall we?", flattening ませんか vs ましょう.
- `read:n3-desejos-01-01` — `新年もよい年でありますように。` and `今年もよい年でありますように。` both get
  "May the new year bring you happiness!", though 新年 ≠ 今年 and the pt correctly distinguishes them.
- `read:n3-estrutura-05-01` — `…忘れてはなりません。` / `…忘れてはいけません。` collapse in both locales.
- `read:n3-limites-06-02` — the A3 copy-paste (問題 vs 意見).

**Near-duplicate pairs (≥0.85 pt similarity), 19 boxes:** `n5-passado-04-01` (0.97 "que durão"/"que duro"),
`n5-numeros-tempo-06-01`, `n5-numeros-tempo-07-01`, `n4-dar-receber-04-01`, `n4-transitividade-01-01`,
`n3-concessao-01-01`, `n3-concessao-04-01`, `n3-deveres-03-01`, `n3-desejos-01-01`, `n3-estrutura-06-01`,
`n3-relato-06-01`, plus the 6 identical ones above.

Two boxes are *entirely* a repetition: `read:n5-numeros-tempo-06-01` is `おはよう。おはよう！` → "Bom dia. Bom
dia!" and `read:n5-numeros-tempo-07-01` is `もしもし。ようこそ！ようこそ。` → "Alô. Bem-vindo! Bem-vindo."
Those are not reading practice.

- Fix: add a dedupe step to the selector — reject a candidate whose normalised pt-BR is ≥0.80 similar to one
  already chosen for the box (Tatoeba stores minimal-pair variants under adjacent IDs, e.g. `tatoeba-77972`
  and `-77973`, `-123026` and `-123027`, `-219421` and `-219422`, which is exactly why they cluster), and
  separately reject a candidate whose `en` is byte-identical to one already chosen.

### A6 — 14 boxes pair sentences that fight each other

`design/reading_practice.md` §5 accepts "a themed set of true sentences, not a flowing story". These go past
that: a shared referent or a greeting implies continuity the content then contradicts.

- `read:n5-numeros-tempo-04-01` — `あなたのせいです。おやすみなさい。` → "A culpa é sua. Boa noite." An
  accusation, then a bedtime farewell. That is the whole box.
- `read:n5-perguntas-04-01` — `ネズミでした。こんにちは。` → "Era um rato. Boa tarde." The greeting lands last.
- `read:n5-perguntas-05-01` — `さようなら。わがままね。` → "Até logo. Você é egoísta, né."
- `read:n5-adjetivos-04-01` — "Aonde você está indo? Muito obrigado(a)!"
- `read:n5-verbos-06-01` — "Vamos! Estou em casa. Há pessoas." — sentence 1 says let's go, sentence 2 says I'm
  home, sentence 3 is a bare fragment. The box's own title is "Estou em casa".
- `read:n5-particulas-lugar-06-01` — "Você tem um tempo? Não cutuque a onça com vara curta."
- `read:n3-relato-04-01` — "Ele é famoso como médico." immediately followed by "Ele é **incompetente** como
  médico." about the same 彼 (and the first two sentences are a near-duplicate pair about a singer).
- `read:n3-tempo-04-01` — `スプーンとフォークとナイフが要る。どうも。` → "…uma faca. **Obrigado.**" `どうも。` is a
  whole source sentence dropped in as a two-word fragment.
- `read:n3-deveres-05-01` — `一、二、三、四、五、六、七、八、九、十。` → "Um, dois, três, quatro, cinco, seis,
  sete, oito, nove, dez." — a bare counting list wedged between "our university has eight faculties" and
  "I bought a calendar at the department store".
- `read:n3-estrutura-03-01` — five disconnected passive clauses about "ele": pension, mistaken for his
  brother, given a task, she was laughed at, caught by his own words. A conjugation drill, not a passage.
- `read:n4-aspecto-04-01` — four ways to say the same thing: "Pretendo experimentar fazer. Vou tentar mais uma
  vez. Vou tentar. Vou tentar fazer." (`en` is "I'm going to try. I will try again. I try. I try.")
- `read:n4-causativa-01-01` — can't allow it / father wants me to be a doctor / the bathroom is occupied /
  he speaks German. The title names only sentence 2.
- `read:n4-keigo-02-01` — phone hold / keep your undershirt on / two identical tea invitations.
- Fix: selection-time. Two cheap mechanical rules: forbid a greeting or leave-taking (`おはよう`, `こんにちは`,
  `さようなら`, `ようこそ`, `おやすみ`, `どうも` alone) in any position but the first; and require ≥2 of the
  chosen sentences to share the lesson's `theme_topic` tag rather than merely passing the i+0 gate.

### A7 — 9 boxes carry content unsuitable for a graded reading box

- `read:n3-desejos-07-01` — `ああ、ひょっとしたら今夜は・・・。` … `性病にかかっているかもしれません。` →
  "Ah… talvez esta noite… … **Pode ser que eu esteja com uma doença sexualmente transmissível.**" The
  adjacency manufactures an implication present in neither source sentence.
- `read:n3-causa-05-02` — `私よりもっとエッチな人もいて安心しました。` → "…também há gente **mais safada** do
  que eu." — dropped between "we're short of money" and "a foreigner asked me where the station was".
- `read:n3-tempo-05-02` — `女の子みたいにメソメソするのはやめろ。` → "Para de choramingar **feito menininha**."
- `read:n3-intencao-07-02` — `どいつもこいつもばかばっかりだ。` ships `en` = **"I'm surrounded by fuckwits!"**
  (inherited from Tatoeba). The pt is the far milder "Não tem um que preste, é tudo idiota", so the two
  locales of the same record disagree on register as well.
- `read:n5-verbos-05-01` (`クソっ` → "Droga!") and `read:n4-forma-simples-04-01` (`ちくしょう！` → "Droga!")
  put expletives in N5/N4 boxes; neither source sentence carries a `register` tag, so
  `translation_style.md` §2 ("flag genuinely offensive/vulgar items so the UI can warn") cannot fire.
- `read:n5-perguntas-06-01` — `おおきに！` is **Kansai dialect** for "thanks", rendered as the plain "Muito
  obrigado!" with no dialect marker, in an N5 greetings box. (Its bank record is also mis-tagged
  `grammar:oki-ni` / `おきに`, i.e. confused with the 〜おきに "every other" pattern.) A beginner reading this
  box learns おおきに as standard Japanese.
- `read:n3-intencao-03-01` opens on `正規表現で空白はどのように表されるのでしょうか？` ("How is whitespace
  represented in regular expressions?") and `read:n3-intencao-05-01` opens on
  `ヘッドライン開放システムを利用しています` → "Eu uso o sistema de manchete aberta", which is not meaningful
  Portuguese. Both are i+0 by vocabulary and untranslatable by topic.
- Fix: exclude `register: vulgar|slang` and dialect-marked items from the selector, exclude sexual-health
  content, and re-select these nine. None of them needs the offending sentence to satisfy its i+0 gate.

### A8 — 2 boxes' pt-BR contradicts the very grammar point the box is gated to

- `read:n3-intencao-02-01` (gated to the ことになっている lesson) — `何をすることになっているかわからない。` →
  **"Não sei o que devo fazer."** That is べき ("should"), not ことになっている ("what has been arranged"). The
  same box renders the pattern correctly twice ("Está combinado que…"), and its own `en` has it right ("what
  I'm supposed to do"). Fix: **"Não sei o que ficou combinado que eu faça."**
- `read:n3-limites-04-01` (gated to the とは限らない lesson) — `彼は毎日ここへくるとは限らない。` →
  **"Ele não vem aqui todos os dias."** A flat assertion where the pattern means "not necessarily"; the next
  two sentences in the same box use "nem sempre" for the identical pattern. Fix: **"Não é sempre que ele vem
  aqui todo dia."**
- Both strings are inherited verbatim from the bank records (`tatoeba-7927727`, `tatoeba-99803`), so the fix
  belongs in both places — but the reading box is where a learner meets the wrong gloss immediately below the
  grammar explanation that just taught the opposite.

### A9 — 7 boxes carry pt-BR that mirrors the Japanese structure instead of reading as Portuguese

`translation_style.md` §1 is a hard rule: the structural mirror goes in `translation_literal`, never in
`translation`.

| box | jp | shipped pt-BR | fix |
|---|---|---|---|
| `read:n3-causa-07-02` | `ぬくもりなどどこにも見つからない。` | "Calor humano (aconchego), **coisa nenhuma**, não se encontra em lugar algum." | "Calor humano é coisa que não se encontra em lugar nenhum." |
| `read:n3-causa-01-01` | `風が強いのはビル風のせいです。` | "**O vento estar forte é** por causa do efeito de túnel entre os prédios." (the のは nominalisation mirrored) | "O vento está forte por causa do efeito de túnel entre os prédios." |
| `read:n3-causa-05-01` | `あなたが今あるのはだれのおかげなのですか。` | "**Você deve a quem o que é hoje?**" — scrambled word order | "A quem você deve o que é hoje?" |
| `read:n3-causa-05-01` | `どうしても見えるところに目がいってしまう。` | "**Faça o que fizer**, meus olhos acabam indo para onde dá para ver." — addresses *you* while the clause is about *my* eyes | "Por mais que eu tente, meus olhos acabam indo para a parte que está à mostra." |
| `read:n3-tempo-08-01` | `この町は西も東も分かりません。` | "Nesta cidade, não sei nem onde é o oeste nem onde é o leste (estou completamente perdido)." — mirror plus a parenthetical explaining the mirror | "Não conheço nada desta cidade." |
| `read:n3-relato-01-01` | `彼が正しいというのは私の意見です。` | "**Que ele tem razão é a minha opinião.**" — fronted subject clause | "Na minha opinião, ele tem razão." |
| `read:n4-forma-simples-03-01` | `やるしかない。` | "**Não temos escolha a não ser fazer.**" — objectless calque; the same box renders しかない two other, better ways ("Só resta…", "só tenho…") | "Não tem jeito, tem que fazer." |
| `read:n3-concessao-05-02` | `店の下調べのため会社帰りに寄ることにした。` | "Decidi passar (na loja) na volta do trabalho para fazer um reconhecimento prévio **da loja**." — "loja" twice, one of them parenthetical | "Decidi passar na loja na volta do trabalho para dar uma olhada antes." |

### A10 — ungrammatical Japanese shipped as model reading text

`read:n3-tempo-02-01` contains two malformed sentences and one unreadable one:

- `少女はそんな**人な**ことは聞いたこともないと言った。` — should be そんな人のこと or そんなこと.
- `私たちはいつ**そこの**たどり着くことになるだろうか。` — should be そこに / そこへ.
- `ドルペッグの意味は、強い国につけということです。` → "O significado de 'dollar peg' é: atrele-se aos países
  fortes." — currency-peg jargon in an N3 reading box.

The errors are inherited from Tatoeba (`tatoeba-146717`, `tatoeba-166614`), but a reading box is precisely the
place they must not appear: the whole premise of §1 is that the learner reads *real, correct* Japanese.
Fix: drop all three from the box, re-select, and correct or retire the two bank records.

### A11 — 37 pt-BR sentences in 34 boxes carry a translator's parenthetical inside `translation`

`translation_style.md` §5 puts the natural rendering in `translation` and the structural/explanatory gloss
elsewhere (`translation_literal`, `structure_explanation`). These leak the gloss into the string the learner
reveals. They fall into three kinds:

- **Disambiguation the learner did not ask for** (17): `"Boa noite (ao se despedir para dormir)."` ×2,
  `"Tem clipe (de papel)?"`, `"De onde (ele/isso) parte?"`, `"Diga qual (dos dois) você quer."`,
  `"Meu pai logo vai melhorar (ficar bom de saúde)."`, `"Meu pai está indo muito bem (de saúde)."`,
  `"Por favor, aguarde na linha (sem desligar)."`, `"Depois que você comer (todo) o bolo…"`,
  `"Algum dia preciso aprender (isso)."`, `"Da próxima vez, traga a sua irmã (mais nova)."`,
  `"O senhor (presidente) vai ler este livro?"`, `"Nós temos um prato especial (para o senhor)…"`,
  `"Ele finalmente perdeu a paciência (explodiu)."`, `"…o trabalho dos seguranças (SP)."`,
  `"Vou amanhã, então já fique sabendo (conte com isso)."`, `"Pode ficar com a camiseta de baixo (sem tirar), viu?"`
- **Slash-gender forms** (9 boxes): `"Muito obrigado(a)!"`, `"o(a) senhor(a)"`, `"Fiquei aliviado(a)"`,
  `"Fiquei encantado(a)"`, `"Seja bem-vindo(a)!"`, `"É que estou meio preocupado(a)…"`. Fine in a UI label,
  wrong in a sentence a learner is meant to read as natural speech.
- **The gloss pushed into `en` as well** (2): `read:n3-desejos-06-02` "…separates work from leisure (knows
  when to switch on and off)" and `read:n3-perspectiva-05-02` "…remove the stems (getting them ready)". The
  `en` field is supposed to be the *trusted human* English (§5b); re-authoring it with a pt-BR translator's
  note destroys its value as an independent cross-check.
- Two are worse than clunky and are listed in A9 instead (`n3-tempo-08-01`, `n3-concessao-05-02`).
- Fix: pick one rendering and commit to it; if the ambiguity genuinely needs teaching, it belongs in the
  sentence's `structure_explanation`, not in the reading box's reveal.

### A12 — the same Japanese noun rendered two different ways inside one box

`read:n4-conectores-04-01` — `この店は安いしおいしい` → "Esse **restaurante** é barato e ainda por cima é
gostoso." then, immediately after, `あの店は安いしおいしい` → "Aquela **loja** é barata e ainda por cima a
comida é gostosa." Identical JP frames, adjacent, two different pt nouns. (`read:n4-conectores-02-01` renders
a third instance of `この店` as "loja".) Fix: use "restaurante" in all three — the sentences are about food.

---

## B. Data-only defects (invisible in the prototype today, wrong in the exported corpus)

### B1 — 7 tokens' `ro` contradicts their own `r`
The kana→romaji round-trip over all 11,125 pure-kana readings (allowing the project's `ー`→`-`, `っ`→next
consonant, `は`→`wa`, `を`→`o`, `へ`→`e` conventions) leaves exactly these:

| box | surface | `r` | `ro` | correct `ro` |
|---|---|---|---|---|
| `read:n3-estrutura-02-01` | 何 (何も言うことがない) | なに | **nan** | `nani` |
| `read:n3-intencao-01-01` | 何 (私何言おうとした) | なに | **nan** | `nani` |
| `read:n3-intencao-02-01` | 何 (何をすることに) | なに | **nan** | `nani` |
| `read:n3-intencao-04-02` | 入れる (指が入れるか) | はいれる | **ireru** | `haireru` (`r` is right — this is the potential of 入る) |
| `read:n3-intencao-04-02` | １日 (１日でどれくらい) | いちにち | **tsuitachi** | `ichinichi` |
| `read:n3-intencao-06-02` | 七 (七時だ) | しち | **nana** | `shichi` |
| `read:n3-intencao-06-02` | ４ (４年間) | よ | **yon** | `yo` |

In every case the `r` is correct and the `ro` was not regenerated from it. Fix: regenerate `ro` from `r` for
the whole file.
*(Numerals are otherwise now correct — all 62 digit tokens read as whole numbers with the right
gemination/rendaku: ごまん, ごせん, ひゃく, にじゅっ+ぷん, いっ+ぱい, ふつ+か, にじゅうはち+にち, やっ+つ. The
digit-by-digit れい bug is gone.)*

### B2 — small kana are romanised as a separate mora, and one word gets two spellings
The converter maps `てぃ`/`でぃ` as `te`+`i` / `de`+`i`:
`アイディア` → **`aideia`** (should be `aidia`), `ディナー` → **`deina-`** (`dina-`), `オリジナリティ` →
**`orijinaritei`** (`orijinariti`), `パーティー` → **`pa-tei-`**.
That it is a bug and not a convention is proved by `read:n3-tempo-05-01`, which spells the same
`ぱーてぃー` as **`pa-ti-`** while `read:n3-concessao-06-01` and `read:n3-limites-07-02` spell it `pa-tei-`.
Fix: add the small-kana digraphs to the converter and re-run over the file.

### B3 — 3 whitespace tokens carry the reading きごう ("symbol")
`read:n4-conectores-02-01` (1) and `read:n4-conectores-03-01` (2):
`{"s": " ", "r": "きごう", "ro": "kigou", "pos": "whitespace"}`. With `show="romaji"` the line would read
`… oishii desu **kigou** sore ni …`. These are the only 3 `pos: whitespace` tokens in the corpus, and they
exist only because of the stray half-width spaces in A4. Fix: normalise the spaces away (which also fixes two
A4 junctions) or emit `r: " "`, `ro: ""`.

### B4 — `ai_generated: false` on 21 boxes whose Japanese is partly or wholly AI-generated
21 boxes contain at least one source sentence with `provenance.jp_source: "ai-generated"`, and **2 are 100%
generated Japanese** — `read:n4-experiencia-04-01` and `read:n4-keigo-04-01`. All 286 boxes carry
`ai_generated: false`, and `corpus/readings/INDEX.md` states the boxes are *"assembled by **SELECTION** …
(no generation): real Tatoeba / JEC Japanese, human EN"*.
Spec §1.2 makes `ai_generated: true` the flag that routes generated Japanese to the heaviest human review, so
these 21 are currently indistinguishable from the 265 that really are human-written. Fix: set
`ai_generated: true` (or add `contains_generated: true`) on boxes with ≥1 generated source sentence, and
soften the INDEX.md sentence to "predominantly Tatoeba/JEC".

### B5 — `length_band` encodes sentence count, not length
`short` = exactly 2 sentences (10–24 chars) · `paragraph` = 2–5 sentences (**14**–127 chars) · `long` =
exactly 6 sentences (56–139 chars). The bands overlap and invert: `read:n5-particulas-lugar-07-01`
(14 chars, `かっけー！おはようございます`) is `paragraph` while `read:n5-te-form-04-01` (24 chars) is `short`.
`design/reading_practice.md` §6 defines the bands by length. Fix: derive the band from character count with
fixed thresholds, or rename the field `sentence_count`.

---

## Counts

| unit | checked | flagged |
|---|---|---|
| reading boxes | 286 | **200** carry ≥1 finding (86 fully clean) |
| box `title` (locale-object) | 286 | 146 (A1 — placeholder) |
| box `translation["pt-BR"]` | 286 | 45 (A5 ×6, A8 ×2, A9 ×7, A11 ×34, A12 ×1 — overlaps counted once) |
| box `translation["en"]` | 286 | 19 (A3 ×6 boxes, A5-en ×11, A7-en ×1, A11-en ×2 — overlaps once) |
| passage coherence (`jp` as connected text) | 286 | 62 (A4 ×32, A5 ×22, A6 ×14, A10 ×1 — overlaps once) |
| content suitability | 286 | 9 (A7) |
| tokens — furigana `r` on kanji surfaces | 2,797 | 6 (A2) |
| tokens — readings on numeral surfaces | 62 | 0 |
| tokens — `ro` vs `r` round-trip | 11,125 | 7 (B1) + 4 (B2) + 3 (B3) |
| tokens — total | 12,618 | 20 |
| `source_slugs` resolution / `jp` integrity | 286 | 0 |
| `needs_review` / `layer` | 286 | 0 |
| provenance flag `ai_generated` | 286 | 21 (B4) |
| `length_band` | 286 | 286 (B5 — systemic mis-definition) |

**Findings: 17** (A1–A12, B1–B5). The single highest-leverage fixes are (1) finish the title pass over the
17 untouched topics, (2) the one-line `。` rule in the assembler, which clears all 53 A4 junctions and both
half-width spaces, and (3) forbid the assembler from inventing `en` — 7 for 7 of the invented ones are wrong.
