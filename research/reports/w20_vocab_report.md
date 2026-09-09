# W20 — vocab + grammar practice, MECHANICAL GENERATION report

**Unit:** APP_PLAN §6 step 11 — "W20 vocab + grammar: builder-generated items, authored residue".
**Sibling:** the kanji half, applied 2026-09-09 (`research/reports/w20_apply_report.md`).
**Result:** 2,338 absent pairs re-derived, **2,311 exercises generated**, **27 pairs to residue**
(all grammar). Simulated on a copy: vocab absent **0 at every level**, grammar 35 → 26, practised
overall **42.7% → 99.4%**. Nothing applied, nothing committed, no git state changed by this run.

## Ground rules this run held itself to

- **Files only.** `db/corpus.sqlite` was copied to scratch and never written. No exporter and no
  apply script ran against the real tree. No git command changed state.
- **No Japanese was authored.** Every Japanese string in every generated item is a bank sentence
  verbatim, a token surface cut from that sentence's own Layer-A dissection, or a registry form.
- **No pt-BR prose was authored per item.** Four fixed templates, filled with registry glosses,
  grammar labels and bank translations. No em dash anywhere (`design/translation_style.md` §4).
- The generator writes tables under `research/derived/pending/`; the tree is untouched.

## 1. The work list, re-derived (not trusted from the plan)

The plan row says ≈2,321 vocab + 35 grammar. That number predates W11a and the W20 kanji apply, so
it was recomputed from the gate's own predicate — `scripts/build_vocab_exercises.py` imports
`validate_practice_coverage`'s `answer_surfaces`, `make_tiler`, `load_grammar`, `load_sentences`,
`fold_sentence` and `TARGET_REF_RX` rather than reimplementing them, so the two cannot drift.

| level | kind | unlocked | practised | **absent (the work list)** |
|---|---|---:|---:|---:|
| pre-n5 | vocab | 24 | 20 | **4** |
| n5 | vocab | 688 | 160 | **528** |
| n5 | grammar | 150 | 133 | **17** |
| n4 | vocab | 643 | 57 | **586** |
| n4 | grammar | 212 | 200 | **12** |
| n3 | vocab | 1,596 | 411 | **1,185** |
| n3 | grammar | 132 | 126 | **6** |
| **total** | | 4,079 | 1,741 | **2,338** over 262 lessons |

2,303 vocab + 35 grammar. It matches the frozen baseline exactly, which is the check that the
re-derivation reproduces the gate rather than approximating it.

## 2. The generator — `scripts/build_vocab_exercises.py`

Deterministic (fixed `SEED`, every tiebreak a BLAKE2b hash of the row's identity, never `random`),
idempotent (a second run reports both files "unchanged"), and a pure function of the exported tree.
It reads `course/` + `corpus/` JSON, which CLAUDE.md names the source of truth; the SQLite copy was
kept for spot checks and never needed, because the bank's token dissection already carries the
Sudachi boundaries, the vocab links and the readings.

### The four templates, in preference order

| id | type | fires when | fired |
|---|---|---|---:|
| **V-CLOZE** | `cloze` | a bank sentence carries the target and is renderable by that lesson | 185 |
| **V-RECOG** | `recognition` | three usable distractors exist in the lesson's known set | 2,111 |
| **V-PROD** | `production` | recognition impossible; the gloss is unambiguous or the record disambiguates it | 15 |
| **G-CLOZE** | `cloze` | a bank sentence tagged with the grammar point is renderable, and a form span aligns | 8 |

**V-CLOZE.** A candidate sentence qualifies when the lesson already renders it (`sentence_refs`,
body `<sentence ref>` or an existing exercise's refs) or when it is **entirely inside the lesson's
`cumulative_known_set`**: every kanji of the sentence is a known kanji, every token vocab slug and
every run-linked vocab slug is a known word, and no content token is an unlinked kanji word (i+0).
Ranking is: rendered here first, then a **real** sentence over a generated one (spec §1.2), then
shortest, then hashed. The target's own token is blanked at its Sudachi boundary; the prompt is the
blanked sentence plus the bank's pt-BR translation; `answer.full` is the sentence verbatim, so the
coverage gate reads it through the sentence's own Layer-A dissection instead of through its tiler
(rule (a) of that gate's docstring). Of the 185: **142 over a real Tatoeba/JEC sentence**, 43 over a
generated one; 3 over a sentence the lesson already shows.

**V-RECOG.** Stem is the record's pt-BR gloss (up to two glosses of its first glossed sense), key is
its written form, distractors are three records from the same lesson's known set with the same
coarse POS and a different gloss, never a homograph sibling, never a record sharing one of the key's
written forms, never a homophone.

**V-PROD.** Free production from the gloss, reached only when the distractor pool is smaller than
three. Ambiguity is measured, not assumed.

**G-CLOZE.** A bank sentence tagged with the point (the tag is the grammar `key`, which is exactly
how the gate credits it), with a probe segment of the record's `forms[].form` / `structure_pattern`
blanked, and the span required to align to token boundaries on **both** sides.

### Three rules the first run forced, each with the defect that produced it

1. **The answer key is not `headword`.** JMdict's headword for あの is 彼の, for ああ is 嗚呼, for
   五日 is ５日. Keying on it asks a beginner to write a spelling nobody uses, and ５日 is not even
   one Japanese run, so the coverage gate refused to credit it (the first smoke run produced exactly
   that failure, caught by the generator's own credit check). `key_form()` now picks by three
   mechanical signals in order: the spelling **this project's own bank actually uses** for that
   record, then the lesson's **kanji known set** (a form carrying an untaught kanji is not an answer
   this learner can write, the same rule the kanji half's pre-flight held itself to), then JMdict
   `is_common` and a kanji spelling over a kana one. Distractors obey the same rule.
2. **A token's `vocab` link can name a homograph with a different reading.** 何時ですか。("Que horas
   são?") tokenises 何時 with `reading` なんじ but links to `vocab:1188760`, whose kana is いつ,
   because 何時 is one of that record's written forms. The first run produced a cloze whose answer
   key was right and whose explanation named the wrong word. `reading_fits()` now requires an
   uninflected token to read exactly as the record's kana, and an inflected one only to share a stem
   with it, which is what 食べ (たべ) does with 食べる and what なんじ does not do with いつ.
3. **Orthographic parity in the options.** The first full run put the key as the ONLY option written
   with kanji in **136 items**, which hands the answer over on shape alone. Options that match the
   key's kanji-ness are now preferred, and the pool is widened only when fewer than three exist:
   136 → **5**.

Also enforced: a cloze blank may not swallow the sentence (at least two Japanese letters must
remain outside it) and may not be one kana wide (8人孫が＿ます。asking for い is not vocabulary
practice; 2 such items were removed this way).

### What the generator refuses to emit

Every candidate is run through the coverage gate's own predicate **before** it is written: an item
that would not move its target from absent to practised is rejected and the next template is tried.
It also refuses an item whose prompt or explanation fails the prose contract (bracket balance,
terminal punctuation, no em dash) or whose prompt+answer already exists in that lesson.

## 3. What was generated

| level | cloze | recognition | production | total |
|---|---:|---:|---:|---:|
| pre-n5 | 0 | 2 | 2 | 4 |
| n5 | 41 | 478 | 10 | 529 |
| n4 | 101 | 488 | 2 | 591 |
| n3 | 43 | 1,143 | 1 | 1,187 |
| **total** | **185** | **2,111** | **15** | **2,311** |

260 lessons touched. Items added per lesson: min 1, **median 10**, p90 14, **max 19**
(`les:n3-desejos-01`). 47 items carry a disambiguating hint derived from the record itself.

**Output:** `research/derived/pending/practice_vocab_exercises.json` (2,311 rows, 2.6 MB) and
`research/derived/pending/practice_vocab_residue.json` (27 pairs).

### The table shape, and the apply extension it needs

The rows are in the kanji table's shape exactly — `{lesson, targets, exercise, why}` with the same
top-level `why / definition / generated_by / applied_by / row_count / provenance / id_fixes /
apply_id_remap / exemptions / rows` header — so `scripts/apply_practice_exercises.py` can apply it
with **one change**:

- **`--table PATH`.** `TABLE` is currently a module constant pointing at
  `research/derived/repairs/practice_kanji_exercises.json`. Make it an argument (default unchanged)
  and the applier is table-agnostic; nothing else in it is kanji-specific. `r["targets"]` is only
  used in a log line, and it already accepts any exercise `type`.
- Registering the table for replay is a **one-line** addition to `validate_repairs_applied.py`:
  `"practice_vocab_exercises.json": handle_practice_exercises` in `HANDLERS`. That handler is
  already generic and content-addressed.
- `apply_id_remap` and `id_fixes` are **empty on purpose**: ids were allocated against today's tree,
  continuing each lesson's own prefix pattern and numbering (read off the data, because
  `les:n3-causa-04` numbers its items `ex:causa-04-*`). If the tree gains exercises before the
  apply, re-run the generator rather than remapping; it is idempotent and cheap (12 seconds).
- `exemptions` is `{"drop": [], "keep": []}`, so `prune_exemptions` is a no-op. Checked, not
  assumed: only one work-list pair falls in an exempt lesson (`les:n4-kanji-exame-05`,
  `vocab:1630770`) and it receives a **retrieval** item, so no exemption becomes stale.

## 4. The residue — 27 pairs, all grammar

Vocab residue is **zero**: every one of the 2,303 vocab pairs got an item. The residue is the
grammar half.

| reason class | n | what it means |
|---|---:|---|
| `no_cks_clean_sentence` | 20 | no bank sentence tagged with the point is renderable by that lesson (i+0) |
| `no_alignable_form_span` | 4 | a tagged sentence exists, but no probe segment aligns to its token boundaries |
| `no_probe_segment` | 3 | the record has no multi-character form or `structure_pattern` to blank |

`gram:doushite`, `gram:gp-20`, `gram:gp-57`, `gram:na-adjectives`, `gram:gp-23`,
`gram:no-naka-de-a-ga-ichiban`, `gram:te-iru`, `gram:gp-36`, `gram:gp-37`, `gram:te-wa-ikenai`,
`gram:nakute-wa-naranai`, `gram:gp-144`, `gram:keredo-mo`, `gram:gp-41`, `gram:kata`, `gram:gp-91`,
`gram:gp-93`, `gram:you-da`, `gram:koto-ni-naru`, `gram:tadoushi-jidoushi`, `gram:ni-ki-ga-tsuku`,
`gram:sonna-ni`, `gram:n3-ni-kanshite`, `gram:n3-ageru`, `gram:n3-kurai-wa-nai`,
`gram:n3-you-ni-iu`, and `gram:gp-83`'s lesson-mate. Full rows, with the lesson each belongs to, in
`practice_vocab_residue.json`. These 27 are the authored residue: **1.2% of the work list**, small
enough for a single agent rather than a campaign.

One of the 27 lands practised anyway after the apply (26 absent, not 27): a vocab cloze in the same
lesson cites a sentence that carries that point's tag, and the gate credits cited sentences'
grammar tags. Reported rather than hidden, because it is the gate's generosity, not this unit's work.

## 5. Simulated apply and the ratchet

The simulation copies `corpus/` + `course/` + `design/` + `research/reports/` to scratch, inserts
each row into its lesson's `exercises[]`, and places one `<exercise ref>` node per row using the
**applier's own** `insert_node` (imported, not copied), so the body placement is the one the real
apply would make. A pristine control copy of the same tree is kept for before/after and for
attributing failures. Result: **2,311 exercises inserted, 2,311 body nodes, 0 problems**.

### `validate_practice_coverage` — before and after

| level | kind | absent BEFORE | absent AFTER | delta |
|---|---|---:|---:|---|
| pre-n5 | vocab | 4 | **0** | −4 |
| n5 | vocab | 528 | **0** | **−528** |
| n5 | grammar | 17 | 15 | −2 |
| n5 | kanji | 0 | 0 | — |
| n4 | vocab | 586 | **0** | **−586** |
| n4 | grammar | 12 | 7 | −5 |
| n4 | kanji | 0 | 0 | — |
| n3 | vocab | 1,185 | **0** | **−1,185** |
| n3 | grammar | 6 | 4 | −2 |
| n3 | kanji | 0 | 0 | — |
| **TOTAL** | | **2,338 absent / 1,741 practised — 42.7%** | **26 absent / 4,053 practised — 99.4%** | **+56.7 pp** |

**No cell grew.** Vocab absent is 0 at every level; grammar 35 → 26. Exercises counted by the gate:
2,463 → 4,774. Lessons with an absent item: 262 → 22. The baseline was **not** re-frozen (this run
applies nothing); `--write-baseline` belongs in the commit that applies the table.

### The exercise contract, and the neighbours

| check | before | after |
|---|---|---|
| `validate_exercise_contracts` | 0 FAIL | **0 FAIL** |
| production mismatches (substantive / punctuation) | 0 / 0 | **0 / 0** |
| cloze `text` not in `full` | 0 | **0** |
| prose fields without terminal punctuation (ceiling 171) | 171 | **171 — 0 added** |
| cross-lesson duplicate prompt+answer pairs | 2 | **2 — 0 added** |
| `contracts/lesson.schema.json` exercise object, per row | — | **2,311 checked, 0 failures** |
| `validate_lesson_gating` | A 0, B 0, C 1, D 0 | **identical on the control copy** |
| `validate_unlock_ledger` | ALL OK | **ALL OK** |
| `validate_srs_decks` | 0 FAIL | **0 FAIL** |

The single `validate_lesson_gating` C failure (C4, the `needs[]` re-derivation disagreeing with the
stored edges) is **reproduced identically on the untouched control copy**, so it is pre-existing
W21 business and not this table's. `validate_contracts.py` has no `--root`, so it could not be
pointed at the copy; the per-row `jsonschema` check above uses the same schema and covers it.

## 6. Quality gate for the human read

### 6.1 Forty sample items, stratified by (type, level), seeded draw

The production stratum is exhausted at 10 of 15; cloze and recognition are drawn per level.

| # | nível | lição / id | tipo | alvo | prompt (pt-BR) | resposta | distratores |
|---|---|---|---|---|---|---|---|
| 1 | n5 | `les:n5-desu-wa-04 / ex:n5-desu-wa-04-10` | production | `vocab:1412890` | Escreva em japonês a palavra que significa "grande, imenso". | おおきな (accept: おおきな) | — |
| 2 | n4 | `les:n4-passiva-02 / ex:n4-passiva-02-14` | production | `vocab:1270190` | Escreva em japonês a palavra que significa "prefixo honorífico (antes de substantivos)". | ご (accept: ご) | — |
| 3 | n5 | `les:n5-comparacoes-02 / ex:n5-comparacoes-02-14` | production | `vocab:1582300` | Escreva em japonês a palavra que significa "e coisas assim, etc.". | など (accept: など) | — |
| 4 | n5 | `les:n5-perguntas-05 / ex:n5-perguntas-05-6` | production | `vocab:1154340` | Escreva em japonês a palavra que significa "cerca de, mais ou menos". | くらい (accept: くらい) | — |
| 5 | n5 | `les:n5-convites-06 / ex:n5-convites-06-7` | production | `vocab:1370760` | Escreva em japonês a palavra que significa "soprar (vento)". | ふく (accept: ふく) | — |
| 6 | n5 | `les:n5-passado-05 / ex:n5-passado-05-14` | production | `vocab:1240825` | Escreva em japonês a palavra que significa "trabalhar (em emprego), ser empregado em". | つとめる (accept: つとめる) | — |
| 7 | n5 | `les:n5-passado-02 / ex:n5-passado-02-15` | production | `vocab:1468060` | Escreva em japonês a palavra que significa "ano". | 年 (accept: 年, とし) | — |
| 8 | n5 | `les:n5-desu-wa-02 / ex:n5-desu-wa-02-13` | production | `vocab:1000420` | Escreva em japonês a palavra que significa "aquele, aquela". | あの (accept: あの) | — |
| 9 | n5 | `les:n5-verbos-04 / ex:n5-verbos-04-10` | production | `vocab:1631750` | Escreva em japonês a palavra que significa "mostrar sinais de, demonstrar (sufixo que transforma adjetivo em verbo)". | がる (accept: がる) | — |
| 10 | n5 | `les:n5-verbos-05 / ex:n5-verbos-05-11` | production | `vocab:1586270` | Escreva em japonês a palavra que significa "abrir, abrir-se". | あく (accept: あく) | — |
| 11 | n5 | `les:n5-rotina-03 / ex:n5-rotina-03-20` | cloze | `vocab:1012980` | Complete a frase: ＿＿てみる。 (Vou tentar fazer.) | やっ — やってみる。 | — |
| 12 | n5 | `les:n5-rotina-01 / ex:n5-rotina-01-11` | cloze | `vocab:1302680` | Complete a frase: あの＿＿を見てごらん。 (Olha aquela montanha.) | 山 — あの山を見てごらん。 | — |
| 13 | n5 | `les:n5-passado-05 / ex:n5-passado-05-13` | cloze | `vocab:1340450` | Complete a frase: それ＿＿？ (Você consegue fazer isso?) | できる — それできる？ | — |
| 14 | n5 | `les:n5-comparacoes-05 / ex:n5-comparacoes-05-10` | cloze | `vocab:1611000` | Complete a frase: 行かなければ＿＿ませんか。 (Eu preciso ir?) | なり — 行かなければなりませんか。 | — |
| 15 | n4 | `les:n4-keigo-02 / ex:n4-keigo-02-13` | cloze | `vocab:1215260` | Complete a frase: もう行かないと電車に＿＿ない (Se eu não for agora, não vou pegar o trem.) | まにあわ — もう行かないと電車にまにあわない | — |
| 16 | n4 | `les:n4-keigo-04 / ex:n4-keigo-04-7` | cloze | `vocab:1047860` | Complete a frase: ＿＿を五つ作った (Fiz cinco bolos.) | ケーキ — ケーキを五つ作った | — |
| 17 | n4 | `les:n4-causativa-02 / ex:n4-causativa-02-12` | cloze | `vocab:1051970` | Complete a frase: ＿＿の会場まで歩きました (Fui a pé até o local do show.) | コンサート — コンサートの会場まで歩きました | — |
| 18 | n3 | `les:n3-concessao-03 / ex:n3-concessao-03-20` | cloze | `vocab:1206070` | Complete a frase: 目が＿＿たら夜が明けるところだった。 (Quando acordei, o dia estava começando a clarear.) | 覚め — 目が覚めたら夜が明けるところだった。 | — |
| 19 | n3 | `les:n3-intencao-04 / ex:n3-intencao-04-17` | cloze | `vocab:1220550` | Complete a frase: ＿＿はどのくらい？ (Por quanto tempo?) | 期間 — 期間はどのくらい？ | — |
| 20 | n3 | `les:n3-concessao-03 / ex:n3-concessao-03-15` | cloze | `vocab:1579210` | Complete a frase: お話の＿＿にすみません。 (Desculpe interromper a conversa de vocês.) | 最中 — お話の最中にすみません。 | — |
| 21 | n3 | `les:n3-intencao-06 / ex:n3-intencao-06-6` | cloze | `vocab:1315840` | Complete a frase: 部屋を出る＿＿は必ず明かりを消してね。 (Quando sair do quarto, não esquece de apagar a luz, tá?) | とき — 部屋を出るときは必ず明かりを消してね。 | — |
| 22 | pre-n5 | `les:pre-n5-saudacoes-03 / ex:pre-n5-saudacoes-03-5` | recognition | `vocab:1854750` | Qual destas palavras significa "sobre, a respeito de"? | ついて | おんなのこ / これから / もういちど |
| 23 | n5 | `les:n5-perguntas-01 / ex:n5-perguntas-01-12` | recognition | `vocab:1390020` | Qual destas palavras significa "rio, riacho"? | かわ | おくさん / くに / こうさてん |
| 24 | n5 | `les:n5-passado-01 / ex:n5-passado-01-12` | recognition | `vocab:1087820` | Qual destas palavras significa "porta"? | ドア | さらいねん / しんぶん / トイレ |
| 25 | n5 | `les:n5-verbos-04 / ex:n5-verbos-04-12` | recognition | `vocab:1289590` | Qual destas palavras significa "ter problemas, ficar em apuros"? | こまる | はしる / しめる / くもる |
| 26 | n5 | `les:n5-verbos-02 / ex:n5-verbos-02-16` | recognition | `vocab:1587040` | Qual destas palavras significa "dizer, falar"? | いう | する / きく / うる |
| 27 | n5 | `les:n5-perguntas-05 / ex:n5-perguntas-05-12` | recognition | `vocab:1046810` | Qual destas palavras significa "grama"? | グラム | おじ / かんじ / くつした |
| 28 | n5 | `les:n5-desu-wa-05 / ex:n5-desu-wa-05-6` | recognition | `vocab:1002330` | Qual destas palavras significa "avó, vovó"? | おばあさん | おじいさん / あたま / おふろ |
| 29 | n4 | `les:n4-potencial-03 / ex:n4-potencial-03-16` | recognition | `vocab:1499230` | Qual destas palavras significa "uva, uvas"? | ぶどう | ゆうはん / アフリカ / サンドイッチ |
| 30 | n4 | `les:n4-potencial-02 / ex:n4-potencial-02-19` | recognition | `vocab:1226630` | Qual destas palavras significa "cliente, convidado"? | きゃく | はい / くろ / きかい |
| 31 | n4 | `les:n4-keigo-02 / ex:n4-keigo-02-9` | recognition | `vocab:1535880` | Qual destas palavras significa "voltar, retornar"? | もどる | すべる / まちがえる / ゆれる |
| 32 | n4 | `les:n4-dar-receber-04 / ex:n4-dar-receber-04-9` | recognition | `vocab:1480670` | Qual destas palavras significa "oposição, ser contra"? | はんたい | ぎじゅつ / オーバー / おどり |
| 33 | n4 | `les:n4-passiva-01 / ex:n4-passiva-01-17` | recognition | `vocab:1441400` | Qual destas palavras significa "pegar fogo, acender-se"? | つく | ふる / ならぶ / ぬる |
| 34 | n3 | `les:n3-concessao-07 / ex:n3-concessao-07-9` | recognition | `vocab:1277100` | Qual destas palavras significa "virar (algo) para, apontar (para)"? | 向ける | 取れる / 備える / 回す |
| 35 | n3 | `les:n3-tempo-05 / ex:n3-tempo-05-8` | recognition | `vocab:1352170` | Qual destas palavras significa "do ponto de vista de …, em termos de …"? | 上 | さま / 家 / 時 |
| 36 | n3 | `les:n3-conjectura-03 / ex:n3-conjectura-03-14` | recognition | `vocab:1005600` | Qual destas palavras significa "droga!, ah, não!"? | しまった | ノー / まさか / いいえ |
| 37 | n3 | `les:n3-intencao-04 / ex:n3-intencao-04-12` | recognition | `vocab:1590740` | Qual destas palavras significa "coitado, digno de pena"? | かわいそう | わがまま / てきせつ / かいてき |
| 38 | n3 | `les:n3-estrutura-03 / ex:n3-estrutura-03-25` | recognition | `vocab:1362730` | Qual destas palavras significa "sério, grave"? | 深刻 | 重大 / 見事 / 単なる |
| 39 | n3 | `les:n3-causa-01 / ex:causa-01-25` | recognition | `vocab:1179040` | Qual destas palavras significa "poluição, contaminação"? | おせん | おい / ひよう / よろこび |
| 40 | n3 | `les:n3-tempo-01 / ex:tempo-01-20` | recognition | `vocab:1155150` | Qual destas palavras significa "antes, anteriormente"? | 以前 | 相手 / 母親 / 金 |

### 6.2 The twenty most reused distractors

2,771 distinct distractor strings fill 6,333 slots, so the average word is a wrong answer 2.3 times
across the whole course and the worst is 10. The load-balancing pass is what keeps it there: of the
24 best-hashed candidates the generator takes the three used least so far, which is deterministic
and still spreads them. (Before balancing, a handful of early-N5 words were the default wrong
answer for every item in their topic.)

| distrator | vezes usado |
|---|---|
| つく | 10 |
| あつい | 9 |
| かわ | 8 |
| しめる | 8 |
| かける | 8 |
| おく | 8 |
| くらい | 8 |
| けんか | 8 |
| かた | 7 |
| せい | 7 |
| ひく | 7 |
| れい | 7 |
| お | 6 |
| あめ | 6 |
| ここ | 6 |
| かみ | 6 |
| かぜ | 6 |
| ご | 6 |
| かい | 6 |
| きる | 6 |

### 6.3 Templates that produced an unnatural prompt

Every one of these is small, measured and listed so a reviewer can go straight to it.

| smell | n | example |
|---|---:|---|
| **cloze blank covers more than half the sentence** | 11 | `ex:n5-passado-05-13` — "Complete a frase: それ＿＿？ (Você consegue fazer isso?)". Answerable from the translation, but it is closer to production than to a cloze. |
| **nested parentheses in the prompt** | 5 | `ex:n5-desu-wa-02-15` — 'Qual destas palavras significa "ali, lá" (no sentido de aquele lado (formal))?'. The inner parentheses come from the gloss itself; balanced, just cluttered. |
| **key is the only option written with kanji** | 5 | `ex:n5-comparacoes-02-13` — 時々 among たぶん / なぜ / たいへん. Down from 136 after the parity rule; these five are lessons whose known set has no three same-shape alternatives. |
| **all four options are one character** | 4 | `ex:n3-causa-07-5` — "não-, in- (prefixo negativo)". Prefix and suffix records read badly as standalone MCQ options. |
| **prompt over 120 characters** | 1 | `ex:n3-causa-05-8`, a long conversational bank sentence plus its translation. |
| **two items in one lesson with an identical stem** | 2 | `les:n3-desejos-03` — 軍 and 軍隊 both gloss as "exército, forças armadas" and nothing in either record separates them. Each MCQ is still answerable (same-gloss records are never options), but a learner meets the same question twice. |

Related and worth a reviewer's eye: **64 recognition stems** collide with another word the learner
already knows and no hint could be derived from the record. They are answerable for the same reason,
but the stem does not uniquely identify the answer. Down from 111 before the disambiguation pass
(37 resolved by a gloss of the record's own sense past the stem, 10 by part of speech).

### 6.4 The finding that outranks the smells

**91% of the generated items are one template.** 2,111 of 2,311 are pt→jp four-option recognition,
because that is the only template the data supports at scale: **1,096 of the 2,303 target words have
no bank sentence at all**, and of the ~1,200 that do, only 193 appear in a sentence a lesson can
render at i+0. The gate goes to 99.4% and the learner gets a course whose new-vocabulary practice is
overwhelmingly multiple choice. That is a real pedagogical limit of a mechanical pass, and it is the
argument for the levers below rather than for another authoring campaign.

Two measured levers, both cheap:

1. **Relax the cloze gate from i+0 to the course's own i+1 budget** (`validate_lesson_gating`
   `BUDGET`: n5=1, n4=2, n3=2 unknown items in a displayed sentence). Measured on today's tree:
   cloze-capable vocab pairs go **200 → 469** at i+1 and **765** at i+2, and grammar **15 → 20 → 25**.
   Nothing in the suite counts an exercise's `sentence_refs` against that budget (check D counts body
   `<sentence ref>` links only), so this is a content decision, not a gate change.
2. **Apply W13 first.** 4,197 authored N3 sentences are verified and unapplied. N3 is where 1,187 of
   these 2,311 items live and where 1,143 of them are MCQs; the same generator re-run after that
   apply would convert a large share of them to cloze with no new authoring. The generator is
   idempotent, so re-running it is free.

## 7. Not done / open

1. **Nothing was applied and nothing was committed.** The tables sit in
   `research/derived/pending/`. The apply needs the `--table` argument in
   `scripts/apply_practice_exercises.py` and the one-line handler registration in
   `validate_repairs_applied.py` (§3), then `export_course.py`, then `--write-baseline`.
2. **A Fable random sample of 30 is still owed** before the apply commit (APP_PLAN §1 step 5). The
   40 items in §6.1 are a stratified read, not that sample.
3. **The 27-pair grammar residue** is the authored work left in this unit. It is small enough for a
   single agent; it does not need a campaign.
4. **Per-exercise provenance in the export** is still all-or-nothing (2,463 → 4,774 exercises now).
   The kanji half flagged it; this table inherits the same deviation, and the claim lives in the
   table's `provenance` header plus `needs_review = 1` on every inserted row.
5. **Median 10 new exercises per lesson, max 19.** A lesson that had five items now has fifteen. No
   gate limits exercises per lesson and none should invent one, but whether a 19-item quiz is the
   right shape for `les:n3-desejos-01` is a teacher's call, not a script's.
6. `research/derived/pending/card_production_keys.json` disappeared from `pending/` during this run
   (it is in `repairs/`). Not this unit's doing; noted so it is not attributed here.
