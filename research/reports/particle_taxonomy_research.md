# Particle taxonomy: research, measurement, migration plan

**Date:** 2026-09-27. **Unit:** particle_taxonomy (research only; no corpus data changed).
**Deliverables:** [`design/particle_functions.json`](../../design/particle_functions.json) +
[`.md`](../../design/particle_functions.md), [`design/token_roles.json`](../../design/token_roles.json) +
[`.md`](../../design/token_roles.md), and this report.
**Measured on:** `corpus/sentences/bank.json` at git HEAD (529131bf) and a backup of `db/corpus.sqlite`
taken the same day. They agree: 10,271 sentences, 24,771 particle rows.

## 1. Summary

- The corpus has **no usage-level data for particles**. `function_type` is a copy of Sudachi's POS
  subclass in 24,756 of 24,771 rows (99.94%). The meaning sits only in free text: 4,970 distinct pt-BR
  labels, and 833 distinct English labels for に/case alone.
- The proposal adds one field per particle row, `usage`, drawn from a closed enum of **123 usages** in
  **9 classes**. The explanation text is **rendered from a template** (9 templates) instead of authored.
  45 usages are N5 and 58 are N4. N3/N2 rows exist only where the bank already has such sentences, and
  more are added as rows, never as a schema change.
- The same treatment applies to the other word-by-word items: a **chunk role** (37 values), a **token
  function** (15) and an **auxiliary function** (14). The role text is rendered from these, and
  inflection reuses the existing `conjugation_form` enum.
- **Mapping coverage** of today's 24,771 rows onto the enum: **57.5% high confidence** (25.4% where two
  signals agree or the particle has only one usage, plus 32.1% pair default), **33.4% single-signal**
  (needs a verifier), **2.4% lexicalized**, and **6.7% needs a ruling**. に/case is the hard part: 912 of
  its 2,907 rows need a ruling.
- **Recommendation:** adopt the enum; publish the particle's token `position` in the export first (a
  pure export fix); then derive usages mechanically, verify the single-signal tiers with an
  enum-constrained Opus author/verifier pass, rule the 6.7%, and render the explanations. Old text is
  kept as `note`, so nothing is lost.

## 2. Sources

All accessed 2026-09-27.

| # | source | used for |
|---|---|---|
| S1 | Tokyo University of Foreign Studies, 言語モジュール 日本語 文法「格助詞：解説」. <https://www.coelang.tufs.ac.jp/mt/ja/gmod/contents/explanation/053.html> | the case-particle inventory (が を に へ まで から より で の と や) and the headline usages of each: を as object, departure point and route; に as recipient, destination, location, result of change, causative/passive agent and time; で as place, scope, means, material, reason, state and quantity |
| S2 | 小林隆「格助詞」, chapter of the dialect-grammar survey guide hosted by NINJAL (PDF dated 2003-03-28, pp. 109-132). <https://www2.ninjal.ac.jp/takoni/DGG/08_kakujoshi.pdf> | the **17 standard-language usages of に** it uses as survey items: 移動の目標, 移動の帰着点 (person / thing), 授与の相手, 移動の目的 (noun / verb), 出現・発生の場所, 存在の場所, 状態の基準, 使役の相手, 心的態度の相手, 原因・理由, 並列・添加の対象, 変化の結果, 受身の相手 (「〜てもらう」 type and plain), 時. The `ni.*` rows follow this list, with the two 移動 subtypes merged into `ni.goal` and 授与の相手 into `ni.recipient` |
| S3 | 日本語教育ナビ「格助詞とは？ガ格・ニ格…の用法を一覧で解説」. <https://japanese-language-education.com/kakujoshi/>. It cites 日本語記述文法研究会『現代日本語文法2 第3部 格と構文 第4部 ヴォイス』(くろしお出版) | the full per-case usage lists of the descriptive-grammar tradition: ガ格 主体/対象; ヲ格 対象/起点/経過域; ニ格 着点/相手/場所/起因・根拠/主体/対象/手段/時/領域/目的/役割/割合; ト格 相手/着点/内容; カラ格 起点/主体/起因・根拠/経過域/手段; デ格 場所/手段/起因・根拠/主体/限界/領域/目的/様態; マデ格 着点; ヨリ格 起点 |
| S4 | 「とりたて助詞とは？格助詞との違いについて」, nihongo-appliedlinguistics.net. <https://www.nihongo-appliedlinguistics.net/wp/archives/8911>. It cites 庵功雄 (2001) | the とりたて (focus) particle group and its meanings: は 主題・対比; も 並立・付加; だけ/ばかり/しか 限定; こそ 際立ち; など/なんて 評価・例示; さえ/すら/まで 意外・添加; でも/だって 例示; くらい/ほど 概量. This is the basis of the `focus` role and of the `binding`/`adverbial` split |
| S5 | Makino, S. & Tsutsui, M. *A Dictionary of Basic Japanese Grammar*. The Japan Times, 1986. Bibliographic reference; **not re-checked online in this unit** | the learner-facing way of splitting meanings (one entry per sense, with the contrast notes), which `contrasts` and `interchangeable` imitate |
| S6 | The corpus itself: Sudachi/UniDic `pos_fine` on the 24,771 particle tokens | the classes the tokenizer actually emits: 格助詞, 係助詞, 副助詞, 接続助詞, 終助詞, 準体助詞. There is no 並立助詞, so parallel と comes out as 格助詞 and や / か as 副助詞 |

Where the traditions disagree, the design takes these positions:

- **School grammar vs Japanese-teaching grammar.** School grammar (学校文法, the 橋本 line, which UniDic
  follows) has 係助詞 は/も/こそ and 副助詞 だけ/しか/まで .... Japanese-teaching grammar groups them as
  とりたて助詞 (S4). The class stays with UniDic, so it can be checked against `pos_fine`. The とりたて
  meaning is a role (`focus`), which is what exercises need.
- **Class belongs to the usage, not the particle.** と is 格助詞 (comitative, quotative), 並立 (AとB) and
  接続助詞 (conditional). S1 and S3 list these as usages of one form, so `class` sits on the usage record.
- **Non-particles get an id.** The に of 静かに and the で of ではない are the copula だ in school grammar.
  The bank files them as particles, so they get `copula-form` usages with `is_particle: false` and are not
  silently dropped.

## 3. What the project has today

### 3.1 Particle rows (HEAD bank = DB snapshot)

| measure | value |
|---|---|
| particle rows | 24,771 in 10,271 sentences (N5 834 · N4 5,230 · N3 10,003 · N2 4,032 · N1 4,672) |
| distinct surfaces / (surface, function_type) pairs | 67 / 81 |
| `function_type` values | case 12,498 · binding 5,934 · conjunctive 2,967 · sentence-final 1,897 · adverbial 790 · nominalizer 685 |
| `function_type` identical to the token's Sudachi `pos_fine` | 24,756 (99.94%); the 15 exceptions are の/nominalizer on 格助詞 (6), に/conjunctive on 格助詞 (8), が/conjunctive on 格助詞 (1) |
| distinct `function` labels | 4,970 pt-BR · 3,701 en (に/case: 833 en) |
| en `function` label equals its pair's most frequent label | 12,297 (49.6%); these restate the pair default and say nothing about the occurrence (the W13b template audit found the same) |
| en label specific to the occurrence | 10,660 (43.0%) |
| no en label | 1,814 (7.3%); 5 rows also lack pt-BR |
| particle rows bound to their token | DB: all 24,771 (`particle.token_id`). **Export: none.** `particles[]` has no position, and in 966 sentences a surface repeats, leaving 2,149 rows ambiguous |
| particle **tokens** that carry a token `role` | 2 (correct: the particle is explained in `particles[]`) |

### 3.2 Token and chunk roles

| measure | value |
|---|---|
| C-mode content tokens (not particle or punctuation) | 52,031 |
| with no `role` | 24,363 (46.8%) |
| distinct en `role` strings | 7,496, of which 5,415 occur once |
| most frequent roles | main verb 3,423 · topic 1,332 · politeness auxiliary 887 · negation auxiliary 756 · past auxiliary 733 · subject 682 · object 680 · direct object 563 · adverb 522 |
| auxiliaries whose function follows from the lemma | 10,017 of 10,205 (98.2%) |
| `pattern[]` chunks | 17,333; non-committal roles (`phrase` 2,943, `ni-phrase` 1,609, `de-phrase` 595, `to-phrase` 391) = 5,538 (32.0%) |

The most frequent role strings show the structure: a function ("main verb", "auxiliary") or a function
plus a chunk role ("head of the topic"). Both halves are enumerable, which is what token_roles.json
does.

### 3.3 Side finding for the word-by-word sweep (not this unit's fix)

903 sentences export split-mode **A** tokens next to the C tokens in `tokens[]`. The A tokens reuse the
C positions. In `sent:tatoeba-5078` (おいくつですか？) the list holds いく (A, position 1) and つ (A,
position 1) as well as いくつ (C, position 1). A word-by-word view that renders `tokens[]` without
filtering on `split_mode == "C"` shows text that is not in the sentence, which matches the owner's
report. The C tokens themselves concatenate to `jp` in all 10,271 sentences. The bank also holds N1/N2
sentences (8,704 particle rows) although D1 puts N1/N2 out of scope. The taxonomy does not depend on
them.

## 4. Mapping today's rows onto the enum

### 4.1 Method

Every particle row was classified against the enum from two independent signals. The code sits in the
unit's scratch directory. Migration step M3 turns it into a repo script.

- **cue:** a context rule over the C tokens (lemma, POS, inflection, neighbours), for example
  `next.naru-suru` → `ni.result`. It uses no free text. The 59 cues and their lemma lexicons are
  published in particle_functions.json.
- **label:** keyword rules over the current English `function` text. This is a one-off migration signal.
  It is weak when the text is the pair's modal label (§3.1).

Tiers:

| tier | rule |
|---|---|
| `auto` | the (surface, class) admits one usage, or cue and label independently agree |
| `default` | no specific signal; the pair's default usage applies by exclusion (は → topic, を → object, が → subject, で → place of action, て → sequence ...) |
| `cue-only` | a cue fired; the label is silent or only the modal |
| `label-only` | an occurrence-specific label maps to a usage; no cue fired |
| `lexicalized` | the label says the particle is part of a fixed expression (それから, かもしれない ...) → `lex.fixed` |
| `ruling` | a cue and a specific label disagree, or there is no signal and no default |

### 4.2 Result

| tier | rows | share | N5 | N4 |
|---|---|---|---|---|
| auto | 6,288 | 25.4% | 44.7% | 29.4% |
| default | 7,952 | 32.1% | 13.3% | 17.7% |
| cue-only | 3,936 | 15.9% | 10.6% | 11.9% |
| label-only | 4,331 | 17.5% | 16.3% | 27.9% |
| lexicalized | 606 | 2.4% | 7.0% | 4.9% |
| ruling | 1,658 | 6.7% | 8.2% | 8.3% |

114 of the 123 usages get at least one row. Of the nine without rows, four are absent from the bank:
`ni.parallel`, `made.even`, `yori.starting-point` and `na.soft-command` (`ka.acknowledgment` has one
row). They stay because the course teaches them or because they are the contrast of a usage that does
occur. The other five are compounds the measurement did not model as units: `demo.*`, `node.reason`,
`noni.concessive` and `nitsuite.about`. Their tokens were counted under `lexicalized` or under the
component particle's usage, so the compound counts are an M3 task, not a finding.

By pair (largest):

| pair | n | auto | default | cue-only | label-only | lex | ruling |
|---|---|---|---|---|---|---|---|
| は/binding | 5,346 | 169 | 3,254 | 334 | 1,465 | 35 | 89 |
| に/case | 2,907 | 808 | 0 | 654 | 430 | 103 | **912** |
| を/case | 2,831 | 19 | 1,987 | 58 | 746 | 0 | 21 |
| が/case | 2,381 | 47 | 1,303 | 132 | 817 | 10 | 72 |
| の/case | 2,297 | 2,104 | 12 | 118 | 11 | 11 | 41 |
| て/conjunctive | 2,256 | 83 | 398 | 1,707 | 14 | 28 | 26 |
| で/case | 991 | 107 | 388 | 108 | 274 | 84 | 30 |
| か/sentence-final | 776 | 631 | 20 | 70 | 12 | 8 | 35 |
| と/case | 635 | 210 | 0 | 168 | 50 | 50 | 157 |
| も/binding | 581 | 101 | 146 | 110 | 102 | 96 | 26 |

に has no default on purpose. Its modal label is "destination/direction particle" (496 rows), and picking
that as a default would repeat the error the W13b audit found: a modal label pasted onto every に.

### 4.3 Hand check

Random 2% samples, 25 rows per tier, checked by reading the sentence:

| tier | correct | wrong |
|---|---|---|
| auto | 24/25 | 来たって感じ: the tokenizer produced one たって token for た + って, and the pair-unique rule trusted it |
| default | 25/25 | none |
| label-only | 23/25 | 親切にも ("kindly") labelled as quantity emphasis; a lengthened よ～し counted as the particle よ |
| cue-only | 21/25 | うるさくていらいらする is cause, not the parallel て; 悪いけど is a preface, not contrast; 一行おきに is an interval, not a goal; 気を持たせる is an object, not a causee |

With 25 rows per tier these are rough numbers. The 95% interval for 21/25 is about 65-94%. They are
enough to rank the tiers, and not enough to skip verification of the single-signal tiers.

### 4.4 Where the disagreements are

The most frequent disagreements between a cue and a specific label:

| pair | cue says | label says | rows |
|---|---|---|---|
| は | `ha.contrast` (は after another particle: には, では) | topic | 89 |
| が | `ga.stative-object` (好き, 分かる, できる, V-たい) | subject | 72 |
| の | `no.subject-in-modifier` (私の好きな本) | noun modifier | 35 |
| に | `ni.goal` | purpose | 23 |
| て/で | `te.request` (sentence-final て) | subsidiary | 41 |
| と | `to.parallel` | comitative | 22 |
| を | `wo.causee` | object | 17 |
| か | `ka.invitation` (〜ませんか) | question | 17 |

Most of these are the cue refining a coarse label (が with 好き *is* the object of liking), not real
disagreements. They go to the verifier, not straight to a ruling.

## 5. The design (short; the two design docs have the detail)

- **Usage** `<key>.<usage>`, key = Hepburn romaji of the kana spelling (は = `ha`, を = `wo`), so keys
  are injective. Every record has `ja_term` (the reference-grammar term), pt-BR/en label, `desc`, role,
  level, pattern hint, cues, `contrasts`, `interchangeable`, template and example.
- **Compounds** (までに, ので, のに, かな, について, という, でも, かい) are usages that span several tokens.
  The annotation carries `positions`.
- **Explanation** = template(usage) with slots `particle`, `chunk`, `left`, `expression`, plus an optional
  `note`. The chunk slot reuses `chunk_head()`, which the W13b audit already fixed.
- **Token items:** `function` (from POS), `aux_function` (from the lemma), `chunk_role` (from the usage
  that closes the chunk), `form` (existing `conjugation_form` ids). `role` text is rendered, `gloss`
  stays Layer-B text, `note` is optional.
- **Extended `function_type`:** after migration it equals `usages[usage].class`, which adds three values:
  `parallel`, `copula-form` and `lexicalized`. The token keeps `pos_fine`, and
  `classes[].unidic_pos_fine` states which subclasses each class may sit on, which gives the validator a
  cross-check the six-value enum could never provide.

## 6. Migration plan

Each step is one atomic unit (finish, validate, export, commit, STATE.md), and the single-DB-writer rule
applies. Steps M1 and M2 change no meaning.

| step | what | writes | gate |
|---|---|---|---|
| M0 | Owner accepts or amends the enum (this report + the two design docs) | none | owner |
| M1 | **Export the binding.** `export_corpus.py` publishes `position` on every `particles[]` row from `particle.token_id` | export only | every row's token surface == `particle` |
| M2 | Schema: add `particle.usage`, `particle.usage_status`, `particle.positions` (JSON, compounds), `particle.note_origin`; token gets `function`, `aux_function`, `chunk_role` | DB migration | integrity_audit |
| M3 | `scripts/derive/particle_usage.py`: the classifier from this unit, made deterministic, with a `--selftest` built from the §4.3 misses and the W13b 91 assertions. It writes `research/derived/pending/particle_usage.json` with tier + evidence per row | pending table (files only) | selftest; tier counts reproduce §4.2 |
| M4 | Fix the four cue weaknesses in §4.3 before trusting `cue-only`: adjective-て before an emotion or state is `te.cause`; `けど` after 悪い/すみません is a preface; に after おき/ごと is an interval (new usage `ni.interval`, or a ruling); `wo.causee` only when the causative verb is intransitive | code | selftest |
| M5 | **Verify** `cue-only`, `label-only`, and the two risky defaults (は topic vs contrast, が subject vs stative object) with Opus as author and as verifier (memory: QA model split). The prompt is **enum-constrained**: the answer must be one id from that particle's candidate list, or `ruling`. A null or failed verdict excludes the row and never passes it | pending verdict files | agreement rate reported; disagreements → M6 |
| M6 | **Rulings** for the 1,658 `ruling` rows plus the M5 disagreements, same enum-constrained format; に/case first (912) | pending table | every row has a usage or `tokenization-error` |
| M7 | Apply: write `usage`, `usage_status`, `function_type = class`. **Render** `explanation`. The current explanation text moves to `note` with `note_origin: legacy`, so nothing is lost; a later pass trims notes that only repeat the rendered sentence | DB + export | validator (below) |
| M8 | Token items: derive `function` / `aux_function` / `chunk_role`, render `role`, and move the old role text to `note` the same way. This fills the 46.8% of content tokens that have no role today | DB + export | validator |
| M9 | Consumers: `build_sentence_patterns.role_of()` reads `usages[usage].role` in place of the `(particle, function_type)` table, which retires `ni-phrase` / `de-phrase` / `to-phrase`; `build_role_exercises` can then ask destination/time/means questions | code + derived | role drills rebuilt |

New validator checks (M7/M8): `usage` in the enum; `function_type == usages[usage].class`; the token at
`position` has `surface == particle` (or an allomorph); for compounds, `positions` spell the compound;
`classes[class].unidic_pos_fine` contains the token's `pos_fine` unless the usage is `copula-form`,
`lexicalized` or a compound; `explanation` equals the rendered template; the rendered `role` equals the
template output.

Estimated load: M5 covers about 8,300 single-signal rows plus about 4,500 risky defaults. At the batch
sizes used for Layer-B work, that is a few dozen agent batches, which runs in parallel on files. Only M7
and M8 touch the DB.

## 7. How exercises use it

| exercise | built from | why the enum is needed |
|---|---|---|
| Choose the particle (cloze) | sentences with `usage = X` at the learner's level | the answer key is `particle`; distractors are the particles of `contrasts` **minus** `interchangeable` (に/へ with 行く are both right) |
| What does this particle mean here? | one sentence, one particle | the options are the labels of that particle's other usages at or below the level; the key is an id, never prose |
| Same particle, two meanings | two sentences whose particle has different usages (七時に起きる / 駅に行く) | a join on `usage` |
| Minimal pairs | `ni.location-existence` vs `de.location-action`, `ha.topic` vs `ga.subject`, `made.until` vs `madeni.deadline` | the `contrasts` edges are the pair list |
| Which part is the X? (role drill) | `chunk_role` of the chunk the particle closes | today 32% of chunks carry a non-committal role that cannot be asked about |
| Build the sentence | `pattern[]` chunks with roles and a usage per particle | the usage pattern hint (`N[time] に V`) gives the slot order |
| Coverage and search | "all N5 usages of で", "every `wo.path` sentence", "usages taught but never practised" | a closed enum can be counted; free text cannot |
| SRS | a usage can become an item reference later (a `particle-usage` item type next to `grammar`) | the id is stable across sentences |

## 8. Open points for the owner

1. **Granularity of に.** Following S2, `ni.goal` merges 移動の目標 and 移動の帰着点, and `ni.recipient`
   merges 授与の相手 with the addressee of 言う/会う. Splitting them later is a data change. Merging is
   the simpler default for N5/N4.
2. **`copula-form` rows.** The proposal keeps them visible with `is_particle: false`. The alternative is
   to re-tag those tokens as 助動詞, which is more correct but changes Layer-A tokenizer output.
3. **Default rows.** 7,952 rows (32.1%) get their usage by exclusion. The hand check found no errors in
   25, but は/が defaults are where the topic/contrast and subject/stative-object distinctions hide, so
   M5 re-verifies those two pairs even though they are "default".
