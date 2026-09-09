# W31 — sentence `register`, derived (A8)

Run 2026-09-09. **Derivation only:** no DB write, no exporter, no ingest, no `design/` edit, no
`course/` touch, no git state change. One data file and one script were added:

| artifact | what |
|---|---|
| `research/derived/pending/sentence_register_derived.json` | the table: 10,112 rows + residue + conflicts + the comparison against the first attempt |
| `scripts/derive_sentence_register_v2.py` | the generator, so the table is reproducible (the first attempt, `scripts/derive_sentence_register.py`, is untouched and still imports cleanly — v2 reuses its JMdict misc map) |

Scope: **5,889** bank sentences (`corpus/sentences/bank.json`) + **4,223** W13 rows
(`research/derived/n3_mined/accepted.json` 4,197 + `generated.json` 26) = **10,112**.

Key for the bank is the sentence slug (`sent:tatoeba-…` / `sent:gen-…`); for W13 it is
`tatoeba-<id>`, and for the 26 generated rows `gen-<sha1(jp)[:12]>` — the same hash scheme
`scripts/ingest/prepare_generated.py:109` already uses for `sent:gen-…`, so the key W13b needs for
those rows is settled here and is stable.

---

## 1. Signals and precedence

**The predicate is read with SudachiPy (`dict="full"`, split mode C), never by a suffix match.**
The token stream is cut into sentence units at every `補助記号|句点`; inside a unit the **last
bunsetsu** is found by walking back from the end over function words (`助詞 / 助動詞 / 接尾辞 /
補助記号`) to the first content head, then extending left across て-linked auxiliary verbs so
`〜ております`, `〜ていらっしゃる` and `〜てる` stay inside one chain. Politeness is read off that
chain only. This is what separates 「彼は明日来ますと言った」 (plain final bunsetsu → `neutral`) from
「明日来ます」 — a suffix match cannot.

**Precedence** (first bucket that fires wins; it is the D7 order already in `design/schema_v2.md`):

| # | value | fires on | why it sits here |
|---|---|---|---|
| 1 | `epistolary` | 拝啓／敬具／前略／草々／取り急ぎ／貴社ますます, and `〜の候` **anchored to a clause end** | a letter formula reframes the whole sentence; its です／ます are convention, not stance. Narrowest and least ambiguous marker, so it goes first |
| 2 | `archaic` | a Sudachi **文語 inflection class** from a whitelist, `〜候` / `〜たまえ` clause-final, JMdict `arch`/`obs` on an **id-linked** token | classical grammar re-frames the sentence; reading its politeness morphology as modern would be wrong |
| 3 | `vulgar` | JMdict `vulg`/`X`, rough address (てめえ／貴様), a closed vulgar lexeme list | the one value with a content-safety consequence — this is what A8's filter exists for. A vulgar Kansai sentence must not be filed as `dialect` |
| 4 | `dialect` | JMdict `ksb`/`osb`/`kyu`… on a decisive token, あかん／おおきに／ほんま clause-anchored, 〜やねん／〜だべ finals, the Kansai copula や (`助動詞-ヤ`) | a variety of the language outranks a lexical layer inside it |
| 5 | `slang` | JMdict `sl`, a closed surface list (めっちゃ, きもい, やばい…) | |
| 6 | `formal` | keigo predicate: いらっしゃる／おっしゃる／召し上がる, 伺う／申す／いたす／存ずる／参る／拝見, ございます outside a fixed greeting, `お/ご + 連用形 + になる`, `〜ております`; plus the written copula である | formal is polite-and-more: a keigo sentence almost always also carries ます, so it must be tested first |
| 7 | `polite` | です／ます **on the final bunsetsu**; then 〜ください; then 〜なさい; then です／ます present with no final predicate (〜ますように); then a polite set phrase | the です／ます frame sets the relationship |
| 8 | `casual` | plain predicate **plus** a marker: 終助詞 ぞ／ぜ／さ／かしら／っけ／じゃん／もん／かい (hard) or よ／ね／な／の／かな／わ (soft), contraction auxiliaries てる／でる／とく／とる／ちゃう／じゃう／ちまう, なきゃ／なくちゃ, explanatory **んだ**, contracted copula じゃ, colloquial quotative って, colloquial negative 〜ん, casual address お前／あんた, JMdict `col` on a **代名詞**, a casual greeting, a bare imperative; last, an unambiguously `casual` tagged grammar point | |
| 9 | `neutral` | a plain predicate on the final bunsetsu and **no** marker | **written narrative is neutral, not casual** |
| — | `null` | none of the above and no predicate at all | residue: an author's queue, never defaulted to `neutral` |

**The grammar point's own register** is consulted only where the predicate said nothing: it may
promote `neutral → casual` when the point's registry `register[]` maps to exactly one D7 value and
that value is `casual` (61 rows, confidence 0.60). It never overrides a predicate; a disagreement
is recorded as a conflict instead. Mapping used (registry vocabulary → D7):
`plain|neutral|written|literary → neutral`, `polite → polite`, `formal|honorific|humble → formal`,
`casual|colloquial → casual`; `masculine|feminine` ignored (not a register axis in D7).

**W13's authored value** is normalized (`plain → neutral`, `colloquial → casual`,
`honorific → formal`) and used **only as a cross-check**, never as a deciding signal — §3.

### Defects found in the first pass and fixed here (each was measured, not guessed)

| defect | measured | fix |
|---|---|---|
| `〜たい` in the dialect final list | **95** false `dialect` (水が飲みたい, 床は冷たい) | 〜たい/〜ばい/〜けん removed — every surviving marker has no standard homograph |
| Sudachi's 文語 classes taken as archaic | **47** 〜べきだ + 6 〜すべき + 〜における + じ(字) called `archaic` | whitelist of genuinely classical classes; ベシ only in べし／べから |
| `〜なさい` counted as keigo | **145** instructional imperatives called `formal` | なさる counts as keigo only with a ます behind it; otherwise `polite` under its own rule name |
| `お + 名詞 + に + なる` | お金持ちになりたいです called honorific | the middle noun must re-tokenise as a verb 連用形 (`お読み+ます → 動詞+助動詞-マス`); お金持ち does not |
| JMdict `col`/`fam` as casual evidence | やる 61 rows, みたい 27, パパ, お巡りさん | `col` only on a **代名詞** (あいつ／こいつ／お前) — a colloquial noun is not a sentence register |
| `のだ` / `なので` read as explanatory んだ | 〜のである and 〜なので called casual | ん + だ only, and the だ token must actually start with だ (`で` is だ's 連用形) |
| `であります` read as the written copula である | 「よい年でありますように」 called `formal` | negative lookahead; those rows are `polite` |
| `の候` and `よっ` matched as substrings | 「后の候補は6名いた」 `epistolary`, 「国によって」 `casual` | clause-anchored regex / dropped |
| アホ (JMdict `ksb`) taken as regional | 「マルチするなアホ。」 called `dialect` | excluded — it is a nationwide insult, a content flag, not a variety |

After the fixes, agreement with the first attempt is **90.52 %** (§5).

---

## 2. Distribution

**Bank (5,889), per level**

| register | n5 | n4 | n3 | n2 | n1 | total |
|---|---|---|---|---|---|---|
| `neutral` | 142 | 963 | 1112 | 382 | 275 | **2,874** |
| `polite` | 161 | 728 | 633 | 261 | 192 | **1,975** |
| `casual` | 120 | 445 | 190 | 51 | 45 | **851** |
| `formal` | 0 | 38 | 40 | 19 | 5 | **102** |
| `archaic` | 1 | 0 | 3 | 2 | 0 | **6** |
| `slang` | 0 | 2 | 1 | 1 | 0 | **4** |
| `vulgar` | 1 | 0 | 0 | 0 | 0 | **1** |
| `dialect` | 1 | 0 | 0 | 0 | 0 | **1** |
| `epistolary` | 0 | 0 | 0 | 0 | 0 | **0** |
| `null` (residue) | 19 | 28 | 18 | 6 | 4 | **75** |
| **total** | 445 | 2,204 | 1,997 | 722 | 521 | **5,889** |

**W13 (4,223, all n3):** `neutral` 2,538 · `polite` 1,069 · `casual` 491 · `formal` 70 ·
`archaic` 1 · residue 54.

**Combined (10,112):** `neutral` 5,412 (53.5 %) · `polite` 3,044 (30.1 %) · `casual` 1,342 (13.3 %)
· `formal` 172 · `archaic` 7 · `slang` 4 · `vulgar` 1 · `dialect` 1 · `epistolary` 0 · residue 129.

**By rule** — `plain-predicate` 5,412 · `polite-predicate` 2,630 · `soft-final` 741 ·
`casual-marker` 540 · `polite-request` 263 · `polite-request-nasai` 134 · `no-signal` 129 ·
`keigo` 88 · `written-copula` 84 · `grammar-register` 61 · `polite-set-phrase` 12 ·
`bungo-inflection` 6 · `polite-nonfinal` 5 · `slang-lexeme` 3 · `vulgar-lexeme` 1 ·
`classical-final` 1 · `jmdict-slang` 1 · `dialect-marker` 1.

`needs_review: true` on 3,374 rows (confidence < 0.80, or a conflict, or residue).

**The A8 census closes.** Of the 645 `say_now` + `production` speak items the census counted,
**642 now carry a register** (neutral 276, polite 258, casual 91, formal 15, archaic 2) and **3**
are residue — against the 383 the census reported as having no signal at all. `drills[].examples`:
765 refs, 6 residue. The zeros for `vulgar`/`archaic`/`epistolary` the speak builder prints are now
**measured absences**, not "unrecordable": the whole 10,112-row corpus holds 1 vulgar, 7 archaic,
4 slang, 1 dialect and 0 epistolary sentences.

---

## 3. Conflicts

**3.1 W13 authored vs derived — 1,731 of 4,223 (agreement 57.7 %).**
The authors used seven values (casual 2,121, polite 1,012, neutral 840, formal 138, plain 91,
colloquial 19, honorific 2); after normalization to D7:

| authored (normalized) | derived | n | reading |
|---|---|---|---|
| casual | **neutral** | **1,591** | the systematic defect the plan predicted: plain-form written narrative marked casual (彼は彼らに食べ物と金を支給した。 / その男は悪魔に魂を売った。) |
| polite | polite | 997 | agree |
| neutral | neutral | 893 | agree |
| casual | casual | 485 | agree |
| formal | formal | 63 | agree |
| formal | **neutral** | 49 | passive/written prose read as formal (思想は言葉で表現される。 / 社会は個人より成る。) |
| casual | **null** | 40 | residue |
| neutral | **polite** | 29 | authors missed a です／ます |
| casual | **polite** | 22 | ditto |
| formal | **polite** | 21 | です／ます with no keigo |
| — | others | 30 | each < 10 |

**1,591 of the 1,731 conflicts (92 %) are the single `casual → neutral` class**, exactly as APP_PLAN
row W13 predicted ("plain-form narrative marked casual"). The derived value is the one to apply;
the authored value should not be carried into the ingest.

**3.2 Grammar point vs predicate — 746 rows.**

| the tagged point says | the predicate says | n |
|---|---|---|
| neutral (`plain`) | polite | 422 |
| neutral (`plain`) | casual | 279 |
| polite | neutral | 15 |
| casual | polite | 10 |
| neutral | formal | 10 |
| formal | polite | 8 |
| polite | formal / casual | 2 |

The first two classes (701 of 746) are **not defects**: a point tagged `plain` describes the *form*
the point attaches to, not the politeness of the sentence built on it (te-form, から, なら, ても all
appear in です／ます sentences). The 15 `polite → neutral` and 10 `casual → polite` rows are the ones
worth a look — several are registry errors, not sentence errors (`hazu-da=polite`,
`no-ga-suki=polite`, `no-ga-heta=polite` are marked polite but are plain-form points;
`sakki=casual/colloquial`, `yo=colloquial` are lexical tags on points that appear in polite
sentences). **Recommendation: this list is a work item against `corpus/grammar/*.json`, not against
the sentences** — it is in the table under `conflicts[].kind == "grammar-vs-predicate"` with the
point names.

**3.3 Mixed 敬体/常体 inside one utterance — 2 rows.** Only 69 of 10,112 rows carry more than one
sentence terminator at all; where units disagree the polite reading wins and the conflict is
recorded.

---

## 4. Residue — 129 rows (1.3 %)

`register: null`, `rule: "no-signal"`, listed separately in the table with `jp`, `set` and `level`.
Split: W13 n3 **54** · bank n4 28 · bank n5 19 · bank n3 18 · bank n2 6 · bank n1 4.

Every one is a fragment with no predicate on its final bunsetsu and no lexical or grammatical
marker — noun-final utterances, bare questions, greeting fragments:

> 中サイズのコーヒーを一つ · 先日はどうも · あの青いシャツはだれの · こちらこそ。 · 現実へようこそ！ ·
> 何時ごろ？ · 期間はどのくらい？ · 奥さんはお元気？ · また来週！ · そこを何とか。 · かっけー！ ·
> 時の過ぎゆくままに。 · リストは次のとおり。 · 音楽に国境なし。 · 彼女、文句ばっかり。 · 調子はどう？

This is the authoring queue and it is small enough to be one batch. Nothing was authored here.

---

## 5. Agreement with the first attempt

`research/derived/pending/sentence_register.json` (5,889 bank rows, kept as input and not
restarted): **5,331 agree / 558 disagree = 90.52 %.**

| first attempt | derived | n | who is right |
|---|---|---|---|
| neutral | **polite** | 221 | derived — 〜ください (263 rows) and 〜なさい (134) were left `neutral` by the first pass |
| casual | **neutral** | 145 | derived — plain narrative (彼は暇なときにそれをやった。 / 時間はいくらでも作れる。) |
| neutral | **casual** | 80 | derived — explanatory んだ, また明日, おやすみ |
| neutral | **null** | 70 | derived — the first pass defaulted predicate-less fragments to `neutral` at confidence 0.5; they are residue, and a defaulted `neutral` would silently pass the speak filter |
| casual | polite | 8 | derived |
| polite | formal | 7 | derived — keigo now beats です／ます |
| formal | polite | 6 | derived — 〜なさい / であります |
| casual | null | 5 | derived |
| formal | neutral | 5 | derived — である narrowed |
| polite | neutral | 4 | **mixed** — です／ます not on the final bunsetsu and the sentence ends plain |
| neutral | formal | 3 | derived |
| polite | casual | 2 | derived |
| archaic | neutral | 1 | derived — 〜べきだ |
| formal | archaic | 1 | derived |

Full row-level list (`jp`, both values, the rule and the signals) is in the table under
`first_attempt_comparison.disagreements`.

---

## 6. Thirty sample rows for a human read

| jp | register | rule | deciding signal |
|---|---|---|---|
| 背がいたいので病院に行く | `neutral` | `plain-predicate` | plain predicate 行く on the final bunsetsu |
| 世界の人口は増加する傾向にある。 | `neutral` | `plain-predicate` | plain predicate ある |
| 卵に醤油をかけて食べる | `neutral` | `plain-predicate` | plain predicate 食べる (chain かけて食べる) |
| 彼は世間知らずだ。 | `neutral` | `plain-predicate` | plain predicate 知らずだ |
| 家の中ではスリッパをはく | `neutral` | `plain-predicate` | plain predicate はく |
| 弟は体が弱いです | `polite` | `polite-predicate` | です on the final bunsetsu (弱いです) |
| チーズを三百グラム買いました | `polite` | `polite-predicate` | まし on the final bunsetsu (買いました) |
| あの試験は非常に難しかったです | `polite` | `polite-predicate` | です (難しかったです) |
| 男の子は溺れるところでした。 | `polite` | `polite-predicate` | でし (ところでした) |
| どこかに出かけるの？ | `casual` | `soft-final` | soft sentence-final の |
| でも、わたしには恋人がいるの。 | `casual` | `soft-final` | soft sentence-final の |
| 今、着いたところよ。 | `casual` | `soft-final` | soft sentence-final よ |
| 最初から最後までうっとりしてた。 | `casual` | `casual-marker` | contraction 〜てる |
| この事ばかりに時間をかけてるわけにはいかないんだ。 | `casual` | `casual-marker` | contraction 〜てる + explanatory んだ |
| あいつが言うことって、分かりづらいよなぁ。 | `casual` | `casual-marker` | colloquial quotative って |
| おやすみ。 | `casual` | `casual-marker` | casual greeting おやすみ (no なさい) |
| 少しステレオの音を小さくしてください。 | `polite` | `polite-request` | 〜ください |
| ボーイさん、紅茶を一杯ください。 | `polite` | `polite-request` | 〜ください |
| １から１０まで数えなさい。 | `polite` | `polite-request-nasai` | instructional 〜なさい (なさる, no ます) |
| 部屋をそのままにしておきなさい。 | `polite` | `polite-request-nasai` | instructional 〜なさい |
| お子さんはいらっしゃるの？ | `formal` | `keigo` | keigo predicate いらっしゃる |
| 部長は会議室にお入りになった | `formal` | `keigo` | お + 入り(連用形) + に + なる |
| 理由は以下のとおりである。 | `formal` | `written-copula` | written copula である |
| お母さんみたいな先生が好きだ | `casual` | `grammar-register` | tagged point `mitai-da` = casual/colloquial |
| さようなら！ | `polite` | `polite-set-phrase` | polite set phrase さようなら |
| ここにゴミ捨てるべからず。 | `archaic` | `bungo-inflection` | べから (文語助動詞-ベシ) |
| 果物がすきです たとえばりんごやみかん | `polite` | `polite-nonfinal` | です present, sentence does not end on a predicate |
| この青のセーター、めっちゃかわいいよ。 | `slang` | `slang-lexeme` | slang lexeme めっちゃ |
| ちくしょう！わるくないなあ！ | `vulgar` | `vulgar-lexeme` | vulgar lexeme ちくしょう |
| さあ話したまえ。 | `archaic` | `classical-final` | 〜たまえ |
| 手がいっぱいできもい。 | `slang` | `jmdict-slang` | JMdict `sl` on きもい |
| おおきに！ | `dialect` | `dialect-marker` | dialect marker おおきに |
| ちょっと、そこのきみ！ | `null` | `no-signal` | — residue |
| ようこそ。 | `null` | `no-signal` | — residue |

---

## 7. Proposed schema delta — NOT applied

`design/schema_v2.md` already carries §`sentence.register` with the D7 value set, the precedence
chain and `register_flags[]` / `register_confidence` / `register_evidence`. **The value set needs
no change.** Three deltas are proposed; none of them was written into the file.

**7.1 Column block** (replacing the four `register*` lines in the `### sentence` block):

```
register,                # ONE value from the D7 set below, or NULL — Layer B
                         # neutral|polite|casual|formal|vulgar|archaic|epistolary|dialect|slang
                         # NULL = no mechanical signal (129 of 10,112). NEVER defaulted to
                         # `neutral`: a defaulted neutral passes the speak filter silently.
register_rule,           # locale-neutral enum naming the rule that decided it:
                         #   plain-predicate | polite-predicate | polite-request |
                         #   polite-request-nasai | polite-nonfinal | polite-set-phrase |
                         #   soft-final | casual-marker | grammar-register | keigo |
                         #   written-copula | bungo-inflection | classical-final |
                         #   jmdict-arch | jmdict-vulg | vulgar-lexeme | rough-address |
                         #   jmdict-dialect | dialect-marker | jmdict-slang | slang-lexeme |
                         #   epistolary-formula | no-signal
register_signals[],      # every signal seen, ordered; [0] is the deciding one
register_confidence,     # 0..1; exactly 0.0 iff register IS NULL
register_evidence,       # kept — the one-line human string, == register_signals[0]
register_flags[],        # unchanged (orthogonal content warnings)
```

`register_rule` exists because `register_evidence` is prose: a validator, a ratchet and the speak
filter all need to branch on *how* a value was reached (e.g. accept `polite-predicate` at face
value, hold every `grammar-register` row for review) and cannot parse a sentence to do it.

**7.2 One line to add under "Precedence when several fire":**

> **The predicate is read off the LAST BUNSETSU** of each sentence unit, with SudachiPy
> (`dict="full"`, split mode C) — never by a suffix match on the string. です／ます anywhere other
> than the final bunsetsu is not politeness of the sentence (「彼は明日来ますと言った」 is `neutral`);
> the one exception is a sentence with no final predicate at all (〜ますように), rule
> `polite-nonfinal`.

**7.3 Two owner calls the derivation surfaced (both left as they stand today):**

- **`〜なさい` has no home in D7.** 134 rows (立ちなさい / １から１０まで数えなさい) are an
  *instructional* imperative: derived from the honorific なさる, so not `casual`; addressed
  downward to a child or student, so not `polite` in any useful sense; not keigo, so not `formal`.
  They are filed `polite` at confidence 0.60 under their own rule name so one grep moves them.
  Options: leave them `polite`; add a tenth value (`instructional`); or exclude them from the speak
  path by rule rather than by register. **Recommendation: exclude by rule, leave the value set at
  nine** — a tenth value costs every consumer, and only the speak filter cares.
- **`である` is filed `formal`** (84 rows) because the committed D7 table lists it there. That sits
  awkwardly next to this unit's own rule that *written narrative is neutral*: 「犬は利口な動物である。」
  is expository prose, not deference. If the owner would rather have the D7 `formal` row mean
  *keigo only*, である moves to `neutral` and the change is one line in the derivation — 84 rows,
  all identified by `register_rule == "written-copula"`.

---

## 8. What this unit did not do

Authored nothing. Did not write the field to `db/corpus.sqlite`, did not run any exporter, ingest
or apply script, did not edit `design/schema_v2.md` or any contract, did not touch `course/`, did
not run a git command that changes state. The residue (129), the `nasai` question, the `である`
question and the 25 real grammar-registry disagreements from §3.2 are the only things left that
need a person.
