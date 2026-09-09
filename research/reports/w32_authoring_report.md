# W32: R87 survival cores for the eleven stages that had none (authoring report)

**Authored 2026-09-09. Nothing is applied.** The artifact is
[`research/derived/pending/speak_survival_cores.json`](../derived/pending/speak_survival_cores.json)
(71 rows). The apply is a separate DB-writer unit; `db/corpus.sqlite`, `course/speak/`,
`scripts/export/build_speaking_path.py` and `design/` are untouched by this run.

Closes readiness [`speak_fast_path.md`](readiness/speak_fast_path.md) **G2** (eleven stages with no
survival core), most of **G5** (the canonical utterances the corpus was said not to have) and the
authoring half of **G4** (`arrival` and `health` mined to parity). APP_PLAN row W32.

---

## 1. The headline: the frames were not missing, they were not ingested

The readiness audit measured 36 canonical survival utterances against `corpus/sentences/bank.json`
and found **4 taught, 16 absent from the corpus entirely**, and concluded that the sixteen needed
authoring under D10. Re-measured here against the **licensed raw pool** the bank was built from
(`raw_tatoeba_sentence`, 248,705 CC-BY rows, plus 285,215 English translations, both already
ingested and attributed):

| the 36 canonical frames | readiness G5 (bank only) | this run (bank + raw pool) |
|---|---|---|
| closed by a real human-written sentence | 4 taught, 16 more present in the bank | **26** (25 mined or selected here, 1 already taught) |
| closed by a generated sentence | 0, 16 proposed for authoring | **1** |
| generation cannot fix either | not separated | **8** |
| covered by a sibling frame in the same act | not separated | **1** (`お会計お願いします`, same act as `お勘定お願いします`) |

**Sixteen frames were called absent from the corpus. Eight of them close here with real Tatoeba
sentences that were simply never mined; seven turned out to be blocked by a missing vocabulary
record rather than by a missing sentence; one (試着, trying clothes on) was not audited.** Across
the full list of 36, the sentences that closed the gap are ordinary human-written Tatoeba lines with
a stored English pair: はじめまして, よろしくお願いします, お名前は何ですか, 助けてください, 駅はどこですか,
トイレはどこですか, お勘定お願いします, メニューをください, 予約してあります, パスポートをなくしました,
警察を呼んで下さい and 荷物を預かって欲しいのですが are all real, all short enough, all polite enough,
and none of them had ever been mined.

G5 framed the remainder as an owner decision about whether an authored sentence may lead a stage
("the central tension in the area"). It is not one. Spec §1.2 answers it: **70 of the 71 rows are
real** and the tension does not arise.

The one generated row is `health / ask-for-medicine` → **薬をください**. The only real sentence
carrying that frame (`tatoeba-183175`, 気分が悪いので薬をください) bundles two speech acts, which
breaks the one-function rule this table runs under. D10 allows one generated phrase per unit of six;
the table uses one in the whole path.

**Eight frames are blocked by something generation cannot fix**: the word itself has no
`corpus/vocab` record, so a generated sentence would put a word on screen that cannot be
introduced, glossed, unlocked or turned into an SRS card.

| frame | stage | short real sentences in the raw pool | missing vocab record |
|---|---|---|---|
| `おすすめは何ですか` | eating | 28 | `おすすめ` |
| `ベジタリアンです` | eating | 30 | `ベジタリアン` |
| `道に迷いました` | getting_around | 97 | `迷う` |
| `チェックインお願いします` | lodging | 22 | `チェックイン` |
| `Wi-Fiのパスワードは何ですか` | lodging | 5 | `Wi-Fi`, `パスワード` |
| `救急車を呼んでください` | health | 30 | `救急車` |
| `アレルギーがあります` | health | 72 | `アレルギー` |
| `日本語で何と言いますか` | arrival | 18 | `日本語` |

That is a **vocabulary gap, not a sentence gap**, and it is the real remainder of G5. The sentences
are sitting there; `corpus/vocab` (7,401 records, JLPT-levelled) has no entry for the words. Six of
the eight resolve to a JMdict entry in the ingested snapshot and would be added the way any vocab
record is: 救急車 `1229100`, チェックイン `1077570`, アレルギー `1019740`, 日本語 `1464530`,
迷う `1532710`, パスワード `1101520`, all checked against `raw_jmdict_form`. The other two,
`おすすめ` and `ベジタリアン`, do not appear in `raw_jmdict_form` under any of their usual
spellings, so they need a source decision rather than a promotion.
Until they exist, the eight frames stay unteachable in either direction, and the sensible substitutes
already in the table are 医者を呼んで下さい for 救急車, 何がおいしいですか for おすすめ,
お肉は食べられません for ベジタリアン and 予約してあります for チェックイン.

---

## 2. What was selected, per stage

Selection order per §1.2: (1) a real sentence already in the bank; (2) otherwise a real Tatoeba
sentence mined from the raw pool that the bank does not yet hold; (3) only if neither exists, author
the frame.

| stage | rows | bank | mined | generated | polite/neutral | seed extensions | new words 0/1/2/3 |
|---|---|---|---|---|---|---|---|
| `arrival` | 6 | 0 | 6 | 0 | 6/0 | 3 | 0/2/1/3 |
| `eating` | 7 | 1 | 6 | 0 | 7/0 | 1 | 0/4/2/1 |
| `getting_around` | 7 | 1 | 6 | 0 | 7/0 | 0 | 0/0/6/1 |
| `lodging` | 8 | 0 | 8 | 0 | 8/0 | 3 | 0/3/3/2 |
| `about_you` | 6 | 0 | 6 | 0 | 6/0 | 0 | 1/1/4/0 |
| `time_plans` | 6 | 1 | 5 | 0 | 6/0 | 4 | 4/1/1/0 |
| `health` | 7 | 0 | 6 | 1 | 7/0 | 0 | 0/7/0/0 |
| `past_stories` | 6 | 0 | 6 | 0 | 4/2 | 2 | 0/4/2/0 |
| `politeness` | 6 | 1 | 5 | 0 | 6/0 | 2 | 1/2/3/0 |
| `opinions` | 6 | 1 | 5 | 0 | 4/2 | 3 | 3/3/0/0 |
| `real_talk` | 6 | 2 | 4 | 0 | 5/1 | 2 | 3/1/2/0 |
| **total** | **71** | **7** | **63** | **1** | **66/5** | **20** | **12/28/24/7** |

`shopping` is the twelfth stage and already had a core, so it is not in the table. One thing found
while checking it: three of its eight declared survival terms (これをください / それをください /
あれをください) were assumed dead, but それをください does have a real sentence
(`sent:tatoeba-9930561`) and it is already shipped in `speak:shopping-01`. A generated これをください
was authored, verified and then **dropped** as redundant with it (0.741 on the §6b near-duplicate
rule). The stage needs nothing.

**Why the seven bank rows were still there.** Each is real, polite, short, unused and, in five of the
seven cases, costs zero or one new word at the point its stage opens. They lost their slots to the
frequency sort, which is exactly what R87 was written to stop: お水をください, バスでどのくらいかかりますか,
明後日は火曜日です, 予約をお願いできますか, 彼は来ないと思います, 歩きながら話しましょう,
電話すればよかったのに. No mining was needed for any of them.

**Why `arrival` and `health` needed mining rather than selection.** Both stages are exhausted at the
bank level, and the readiness numbers (48 and 50 real candidates for 36 slots) hide it. Excluding the
36 phrases each stage already spent, filtering to register neutral/polite, length ≤ 20 and zero
unknown vocabulary, `arrival` has **8 candidates left, and 5 of the 8 are R86 duplicates of
greetings the path already teaches** (こんにちは！ against こんにちは。, すみません！ against
すみません。, plus おはようございます！, さようなら。, ありがとうございます。). The other three are
トピずれです。すみません。 ("that's off topic, sorry"), ミスタイプです。すみません。 ("it's a typo,
sorry") and お手数をおかけしてすみません。: two forum apologies and one office formula, in the stage a
traveller meets on day one. `health` has **5 candidates**, none of them a first-person symptom
report: three are about doctors in the third person or as advice, one is 今とてもゆったりした気分だ
("I feel relaxed right now"), one is an instruction to somebody else. Selection cannot fix either
stage. Mining produced 6 rows for `arrival` and 6 for `health` from the raw pool, all real.

---

## 3. The known-set proof, per row

Every row carries a `known_set` block a verifier can recompute from the committed export alone.
`KNOWN(stage)` is the cumulative `words` of `course/speak` stages 1..N as shipped
(`start` = through N-1, `end` = through N). Three counters, all published per row:

| counter | meaning | gate | measured |
|---|---|---|---|
| `unknown_vocab` | content lemmas with **no** `corpus/vocab` record | must be 0 | **0 of 71 rows**, 0 lemmas total |
| `new_at_stage_start` | vocab records not yet known when the stage opens | ≤ `MAX_NEW` = 3, the builder's i+1 budget | max **3**; distribution 0/1/2/3 = **12 / 28 / 24 / 7** |
| `outside_stage_known_set` | words the stage must additionally introduce once the row leads it | reported, not gated | 0 for 27 rows, 1–3 for the other 44 |

`unknown_vocab = 0` is the hard gate and it is the one that did real work: it refused
救急車を呼んでください, チェックインお願いします, ありがとうございます (`ござる` has no record) and six
other frames outright, and it is why the eight blocked frames in §1 are a vocab task rather than an
authoring task.

Vocabulary resolution differs by source and each row says which it used. Bank rows use the committed
export dissection (`token.vocab`). Mined and authored rows use **SudachiPy (dict=full, split mode C)**
and resolve a content lemma against `corpus/vocab` by `headword`, any `forms[].form`, or `kana`;
particles, auxiliaries, numerals and punctuation are not content and are not required to resolve.
This mirrors the builder's own `link_ok`, which is reproduced verbatim for the bank side.

**Other hard gates, all passing at 71 of 71.** Register ∈ {`neutral`, `polite`}; punctuation-stripped
length ≤ 20 (max measured **15**, median 9); not already a `say_now` phrase; **R86**, i.e. the
punctuation-normalised Japanese is unique against all 432 shipped phrases and inside the table; mined
ids not already in the bank; generated Japanese does not end in 。; **§6b near-duplicates**, 0 pairs
at or above 0.72 against the stage's shipped phrases or against sibling rows. Four rows were rewritten
because of that last check and one (the shopping generated row) was deleted by it; each replacement
records the rejected candidate and its score in its own `why`.

**Refusals are recorded, not silently dropped.** The `refused` array is empty in the final artifact
because every refusal was re-authored, and the reason survives in the surviving row's `why`:
明日きっと伺います was refused for `register: formal` (every 伺う sentence has that problem under the
W31 predicate); ありがとうございます was refused twice over (`ござる` unresolvable, plus an R86
collision); 私も賛成です, とても楽しかったです and とてもおいしいですね were refused as near-duplicates
of phrases the path already ships.

---

## 4. Register

Reused from `research/derived/pending/sentence_register_derived.json` (W31) for bank rows;
**recomputed** for mined and authored rows by importing
`scripts/derive_sentence_register_v2.py::decide` (same SudachiPy predicate on the last bunsetsu,
same precedence, same D7 value set), so every value in this table is comparable with W31's.

| register | rows | share |
|---|---|---|
| `polite` | 66 | 93.0% |
| `neutral` | 5 | 7.0% |
| `casual` / `formal` / anything else | 0 | 0% |

Path-wide today the mix is **62.5% plain-casual, 155 polite of 432** (readiness R1). These 71 rows
are 93% polite and, because R87 sorts them ahead of the frequency ranking, they land at the front of
each stage: the first thing a learner meets in eleven of twelve stages becomes a polite utterance
addressed to a stranger. The five `neutral` rows are deliberate: 楽しかった, 昨日は暑かった,
その方がいいと思う, たぶん遅れる, 電話すればよかったのに are plain-form by nature, and their stages
(`past_stories`, `opinions`, `real_talk`) are where plain form is correct.

11 of the 71 sentences (`tatoeba-1039551` 助けてください among them) carry `has_audio` in the raw
table, which is the first real input the G7 voice-over pass has.

---

## 5. Twenty sample rows for a human read

| stage | function | jp | en | pt-BR | reg | new |
|---|---|---|---|---|---|---|
| `arrival` | greet-on-first-meeting | はじめまして。 | Nice to meet you. | Muito prazer. | polite | 1 |
| `arrival` | signal-non-comprehension | 分かりません。 | I don't understand. | Não entendi. | polite | 1 |
| `arrival` | ask-for-slower-speech | ゆっくり話してください。 | Please speak slowly. | Fale devagar, por favor. | polite | 3 |
| `eating` | ask-for-the-bill | お勘定お願いします。 | Check, please. | A conta, por favor. | polite | 2 |
| `eating` | state-a-dietary-restriction | お肉は食べられません。 | I can't eat meat. | Eu não como carne. | polite | 1 |
| `eating` | ask-for-an-english-menu | 英語のメニューはありますか？ | Do you have a menu in English? | Vocês têm cardápio em inglês? | polite | 3 |
| `getting_around` | ask-where-something-is | 駅はどこですか。 | Where is the railroad station? | Onde fica a estação? | polite | 2 |
| `getting_around` | ask-where-to-change-trains | どこで乗り換えるのでしょうか。 | Where do I have to change trains? | Onde eu troco de trem? | polite | 2 |
| `lodging` | report-a-room-problem | お湯が出ません。 | The hot water isn't running. | Não está saindo água quente. | polite | 1 |
| `lodging` | report-a-lost-document | パスポートをなくしました。 | I've lost my passport. | Eu perdi meu passaporte. | polite | 2 |
| `lodging` | call-the-police | 警察を呼んで下さい。 | Please call the police. | Chame a polícia, por favor. | polite | 1 |
| `about_you` | ask-what-someone-does | お仕事は何ですか。 | What do you do? | Você trabalha com o quê? | polite | 0 |
| `time_plans` | ask-the-time | 今何時か分かりますか。 | Have you got the time? | Você sabe que horas são? | polite | 0 |
| `time_plans` | propose-a-meeting | 明日駅で会いましょう。 | I'll meet you down at the station tomorrow. | Amanhã a gente se encontra na estação. | polite | 0 |
| `health` | call-for-help | 助けてください。 | Please help me. | Me ajuda, por favor. | polite | 1 |
| `health` | say-where-it-hurts | お腹が痛いです。 | My stomach hurts. | Está doendo a barriga. | polite | 1 |
| `health` | ask-for-medicine **(generated)** | 薬をください | Some medicine, please. | Um remédio, por favor. | polite | 1 |
| `past_stories` | ask-if-it-is-a-first-time | 日本は初めてですか。 | Is this your first visit to Japan? | É a sua primeira vez no Japão? | polite | 1 |
| `politeness` | apologise-for-being-late | 遅れて申し訳ありません。 | Please pardon me for coming late. | Desculpe pelo atraso. | polite | 2 |
| `real_talk` | say-something-just-happened | 列車は今着いたばかりです。 | The train has just arrived here. | O trem acabou de chegar. | polite | 0 |

Japanese and English on the mined rows are byte-identical to `raw_tatoeba_sentence.text` and
`raw_tatoeba_translation.text` for the id in `tatoeba_id`; a row whose English was not byte-identical
to a stored translation was refused rather than paraphrased. The pt-BR is authored here (Layer B) and
follows `design/translation_style.md`: natural pt-BR rather than a structural mirror, register
matched to the Japanese, no em dash anywhere in the artifact, and the generated Japanese drops its
final 。.

---

## 6. How to refute a row

Nothing here should be taken on this run's word. Per row:

1. Re-run the three known-set counters from the export: tokenise `jp` with SudachiPy (dict=full,
   mode C), resolve each content lemma against `corpus/vocab`, and compare with the cumulative
   `words` of `course/speak` stages 1..N. `unknown_vocab` must be empty and
   `new_at_stage_start` must be ≤ 3.
2. Re-derive `register` with `scripts/derive_sentence_register_v2.py::decide` and compare with
   `register` / `register_rule` / `register_confidence`.
3. Check `jp` and `en` against `raw_tatoeba_sentence` / `raw_tatoeba_translation` by `tatoeba_id`,
   byte for byte.
4. Check the R86 normalisation of `jp` against all 432 shipped `say_now` phrases and against the
   other 70 rows.
5. Check that `survival_term` is a substring of `jp` (or one of its token lemmas) and that
   `survival_term_promotes_in_bank` is what a fresh count gives; the cap is 20.
6. Read the pt-BR against the Japanese and against `function`: one speech act per row, and the pt-BR
   must be the one the `function` names.

The `survival_term` values are **authored, not derived**, and that is deliberate: deriving them
mechanically as the sentence's own suffix was tried first and produced grammatical tails
(`こですか`, `思います`, `いですね`, `れません`) that select by inflection rather than by act, which is
precisely the failure R87 exists to stop, and precisely what §3.9 records about bare `いくら` and bare
`円`. Each term is checked to select its own row and to promote at most 20 bank sentences.

---

## 7. What the apply must do

The apply is a DB-writer unit and is **not** part of this run. In dependency order:

**7.1 Ingest the 63 mined sentences.** `scripts/ingest/ingest_mined_stages.py` is the proven path
(it produced the 324 lodging/past_stories/opinions sentences). Each row needs a bank record with
`jp` and `en` copied byte for byte from the raw tables, `pt` from this table, `ai_generated: false`,
`needs_review: true`, provenance `jp_source: tatoeba:<id>`, a `stage:<slug>` plus a
`survival-core` tag, and then the Dissector for tokens, kana, romaji, `translation_literal`,
`structure_explanation` and the `sentence_kanji` / `sentence_vocab` links. **Re-check
`unknown_vocab = 0` against the real dissection after ingest**, not against this table's SudachiPy
approximation. The two agree on every row today, but the dissection is the authority and the
`link_ok` rule drops links this table's resolver keeps.

**7.2 Ingest the one generated sentence.** `sent:gen-1c83f478ab11` (薬をください), `ai_generated: true`,
`needs_review: true`, `layer: C`, no `tatoeba_id`, jp without the final 。.

**7.3 Fill `SURVIVAL_SEEDS` in `scripts/export/build_speaking_path.py`.** Today it holds one entry.
After the apply it holds twelve: `shopping` unchanged, plus the 71 rows' `survival_term` values
grouped by stage. **20 rows also need a `seeds` extension**, because their sentence hits no existing stage
seed, so the builder would never even consider it as a candidate, and R87 only re-ranks candidates:

| stage | terms to add to `seeds` as well |
|---|---|
| `arrival` | `お名前は`, `分かりません`, `ゆっくり話し` |
| `eating` | `お勘定` |
| `lodging` | `お湯が出ません`, `をなくしました`, `警察を呼ん` |
| `time_plans` | `今何時`, `何時からですか`, `何時まで開い`, `は火曜日です` |
| `past_stories` | `外国に行った`, `行ったことがありますか` |
| `politeness` | `お先に失礼`, `お願いできますか` |
| `opinions` | `どう思いますか`, `そう思います`, `ないと思います` |
| `real_talk` | `忙しそうですね`, `ばよかったのに` |

The remaining 51 rows hit a seed the stage already declares and need only the `SURVIVAL_SEEDS` entry.

**7.4 Rebuild and re-gate.** `build_speaking_path.py` → `build_speaking_practice.py` →
`build_speaking_checkpoints.py`, then the whole speak gate: `validate_speaking_path.py`,
`validate_speak_duplicates.py` (R86 and the §6b ratchet; this table adds 0 pairs at 0.72, so the
ratchet must not move), `validate_speak_spiral.py` (R83 should **improve**: `arrival`'s survival
terms are `はじめまして` / `よろしくお願い` / `もう一度お願い`, which the late stages can now retrieve),
`validate_speak_strands.py` (R78; more prior-known material per stage is what lets
`build_speaking_practice.py` emit more than 3 production items, so the ratchet should shrink, never
grow). Expect churn: R87 re-sorts every stage, so units will change composition and
`cumulative_known_vocab` will move.

**7.5 Flip the R87 check.** `design/speaking_path.md` §5 and readiness G2 both record that
`SURVIVAL_SEEDS` holds exactly one entry and that reading §5 as "each stage declares its core" is
wrong. Once twelve entries exist, update §5, and add the gate that was never written: a validator
asserting **every stage declares a non-empty survival core, and every stage's opening unit contains
at least one phrase matching one of its own survival terms.** Without that second half the seeds can
be present and still lose (they sort ahead of frequency but stay under the i+1 budget, so a term with
no affordable sentence silently does nothing). Land it as a hard check, not a ratchet: after this
apply it passes at 12 of 12.

**7.6 W30 deck emission.** These 71 rows are the natural first content for `deck:phrases`, which is
declared in the registry and holds 0 cards (readiness G9). Each row is one phrase card keyed by
`sentence_slug`, filed by the unit that introduces it, with `function` as the card's prompt axis and
`register` on the card so the app can warn. W30 owns the deck; W32 owns the content.

**7.7 W31 interaction.** The register filter W31's apply installs on the speak builder must not
reject these rows: they are 66 `polite` and 5 `neutral`, all inside D7. Order the two applies so W31
lands first, then this table's ingest carries a `register` field per row from the same derivation and
needs no second pass.

---

## 8. Known limits of this run

- **The pt-BR is one author's, unreviewed.** Every row is `needs_review: true` and the human teacher
  loop is still mandatory (CLAUDE.md §1.8). The functions most worth a second reading are the ones
  where the English source is idiomatic rather than literal: `もう一度お願いします` / "I beg your
  pardon?", `申し訳ありません` / "Please forgive me", `何がおいしいですか` / "What do you suggest?".
- **`survival_term` is authored.** §6 says why, but it means a reviewer should read the twenty
  `seed_extension_required` terms for over-breadth in particular, since those become stage seeds and
  a bad stage seed is the failure mode §3.2 and §5 both record (bare `ください`, bare `行く`).
- **`new_at_stage_start` is measured against today's build.** After the apply the known set itself
  moves, so seven rows sitting exactly at `MAX_NEW = 3` may need re-checking rather than assuming
  they still qualify.
- **Eight frames remain unteachable** until `corpus/vocab` gains the eight records in §1. That is the
  honest remainder of G5 and it is not authoring work.
- **`お会計お願いします` is the one frame left uncovered that is not blocked** (6 short real sentences
  in the pool). `お勘定お願いします` teaches the same act and was preferred as the restaurant word; a
  reviewer may want both.
