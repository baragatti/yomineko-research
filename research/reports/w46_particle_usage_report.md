# V2-W46: particle usage ids applied, explanations rendered from the enum

**Date:** 2026-09-27. **Unit:** chain v5, V2-W46-particles (not a checkpoint: gate + quick replay).
**Plan row:** research/reports/APP_PLAN.md Lane E, W46. **Design:** design/particle_functions.json/.md,
design/token_roles.json/.md. **Research:** research/reports/particle_taxonomy_research.md.

## 1. Result

| measure | value |
|---|---|
| particle occurrences in the bank | 24,771 in 10,271 sentences |
| carry a verified usage id | **24,741** (99.88%): 5,406 `auto` (derived), 19,026 `verified` (ruled + verifier ok), 309 `ruled` (the verifier's correction applied) |
| held (usage null, `usage_status: held`, authored text kept as the explanation) | **30**: 13 verifier-rejected, 17 surface mismatch (§4) |
| distinct usage ids used | 119 of 123 (unused: `made.even`, `na.soft-command`, `ni.parallel`, `tatte.concessive`) |
| by class | case 11,631 · binding 5,613 · conjunctive 2,764 · sentence-final 1,844 · lexicalized 1,232 · adverbial 755 · nominalizer 599 · copula-form 169 · parallel 134 |
| explanations rendered from the templates | 24,741, pt-BR **and** en; the authored text moved verbatim to `note` (pt-BR 24,741, en 13,429) |
| token role enums on C tokens | 76,852 tokens in 10,271 sentences carry `function` / `aux_function` / `chunk_role`; `chunk_role` on 34,614 (the derivation had 21,632: +12,982 from the verified usage of the closing particle, 76 changed by it) |
| course/ rendered diff vs HEAD | **0 files** |

Counts per usage (§7) are per particle ROW: a compound (までに, ので, について ...) counts once per
token it spans.

## 2. What was applied, and how

**Row identity.** Every occurrence is `slug#position` (the C token position; W45 exports it as
`token_position`). `research/derived/repairs/particle_usage/derived.json` holds the 5,418 rows the
mechanical tier decided; `ruled-work-01..67.json` the 19,353 ruled rows. The verdicts
(`research/derived/pending/particle_usage/ruled-0..66.verdict.json`, which stay in pending/) are joined
to the ruled rows **by row identity**, never by file number (the files happen to be offset by one; the
join does not rely on it). Every ruled identity has exactly one verdict and vice versa, and the union
of derived and ruled identities equals the DB's 24,771 particle rows.

**Decision per row** (`scripts/assemble_particle_usage.py`):

| case | rows | result |
|---|---:|---|
| derived (auto) | 5,418 | applied as `auto` (12 held on the surface rule) |
| ruled, verdict ok | 19,029 | applied as `verified` (3 held on the surface rule) |
| ruled, verdict corrected to an enum id | 311 | the correction applied as `ruled` (2 held on the surface rule) |
| ruled, verdict rejected with no id | 13 | held (`verifier-rejected`) |

**Surface rule.** A usage is spelled by its canonical particle or an allomorph; a multi-token spelling
(ては = て + は, compounds like までに, なんか = なん + か) matches when a contiguous C-token span
containing the particle spells it; `lex.fixed` matches any surface. One enum fix was needed:
`teha.condition` lacked the voiced では (読んではいけない; じゃ is its contraction), added as an
allomorph (design changelog, 1.0 W46).

**Rendering** (`scripts/particle_usage_render.py`, shared by the assembler, the applier and the gate).
`explanation[locale] = templates[usage.template][locale]` filled with the usage's `desc` and slots:
`chunk` (chunk_head() of the W13b fix; after another particle, the first particle's chunk plus the
particles between, 学校に; after a closing bracket, the quoted text, 「博士」), `left` (the predicate a
conjunctive or nominalizer closes, through the te-form て/で), `expression` (a compound's span; for
`lex.fixed`, the Japanese that the ruling, the verifier or the authored label/explanation quoted, the
longest one grounded in the sentence whose kanji the sentence shows: 1,211 rows; else the particle with
its neighbours: 21 rows). Two `chunk` slots found nothing and render the neutral phrase "a parte
anterior". Slots are stored per occurrence (`particle.usage_slots`) and exported, so the text
re-renders from the bank alone.

**Nothing lost.** The apply moves each authored explanation (pt-BR and en, with its layer) to
`localized_text (particle, note)` under a guard: sha256[:16] of the text it moves must equal the
table's `legacy` value. `validate_repairs_applied.py` re-proves `note` against the same hashes on every
run, and every older table that asserts an authored particle explanation (W13 template fixes, the U1
second table, the W32 Layer-B ingest, the W40 en backfill) now reads it from `note`
(`authored_explanation()`): all green.

**Token roles** (`research/derived/repairs/token_roles.json`, 10,271 sentence rows). `function` and
`aux_function` as derived (design/token_roles.json); `chunk_role` re-derived from the FINAL usage of the
particle closing the chunk (the derivation could only use auto usages). `lex.fixed` and held closers
keep the derived value. The free-text token `role` is untouched (rendering it is M8, open).

## 3. Files

| file | change |
|---|---|
| `scripts/ingest/migrations/020_particle_usage.sql` | particle.usage / usage_status / usage_slots; token.function / aux_function / chunk_role |
| `scripts/particle_usage_render.py` | the renderer and slot rules; `python scripts/particle_usage_render.py` runs its asserts |
| `scripts/assemble_particle_usage.py` | builds `repairs/particle_usage.json` (24,741 rows + 30 held) and `repairs/token_roles.json`; deterministic, byte-identical on re-run, also after the apply (it reads the legacy text from `note`) |
| `scripts/apply_particle_usage.py` | manifest step **157** (families renumbered 158-160); idempotent and guarded; a re-run writes nothing |
| `scripts/derive_particle_usage.py` | landed from pending/ (logic unchanged; the docstring says where the applied run is frozen); `--selftest` passes |
| `research/derived/repairs/particle_usage/` | the applied inputs moved out of pending/: derived.json, ruled-work-01..67.json, token_roles_derived.json |
| `scripts/export/export_corpus.py` | particles: `usage`, `class`, `usage_status`, `usage_label`, slots, `positions` (compounds), `note`; tokens: `function`, `aux_function`, `chunk_role` |
| `scripts/validate/validate_particle_usage.py` | **new hard gate** U0-U7 (§5), registered in validate_all.py |
| `scripts/validate/validate_repairs_applied.py` | handlers for the two tables; `authored_explanation()` for the older particle tables |
| `scripts/validate/validate_display_consistency.py` | checks `note` too (the panel shows it); the 10 triaged particle entries re-keyed `particle-note` (same texts, same reasons) |
| `scripts/contracts/build_schemas.py` + contracts/ | design-owned vocabularies for usage / class / usage_status and the three token enums; `usage` + `usage_status` required on particles |
| `design/i18n.md`, `research/reports/locale_parity_baseline.json` | `particles[].note` and `usage_label` declared; the en gap moved with the text (explanation 11,320 -> 8, note 11,312) |
| `prototype/` (sync-data, SentenceCards, render-body, lesson.css) + `validate_prototype_sync.py` | the word panel shows the usage label as the tag, the rendered explanation, and the authored note under it |
| design docs | status lines, では allomorph, `held` status, changelog |

## 4. Held rows (30)

**Verifier-rejected (13):** no enum id fits. Role/occasion に, "as a gift / as a snack" (祝いに, お土産に,
夜食に: 7 rows), V-dict には "in order to" (1), the permission て of 〜て(も)構わない (2), 〜ておいて損は
ない (1), neutral linking が (1), 予報では "according to" (1), and a source typo (そこの for そこに, 1).
They need an enum decision (a role/occasion `ni.*`, a permission `te.*`) or a text fix.

**Surface mismatch (17):** かなあ (6 sentences x 2 rows; the compound `kana.wondering` is spelled かな),
たって fused by the tokenizer for た + って (2), ばかり of approximation ruled `kurai.approximation` (2),
と言う spelled in kanji for `toiu.naming` (1). Each needs an enum spelling decision or a tokenization
ruling.

| sentence | particle | reason | ruled |
|---|---|---|---|
| `sent:gen-238f14601cdc` @4 | たって | surface-mismatch | tte.quotative |
| `sent:gen-5b980fff719c` @3 | に | verifier-rejected | ni.purpose |
| `sent:gen-a56521c061da` @2 | に | verifier-rejected | ni.purpose |
| `sent:tatoeba-1063425` @3 | か | surface-mismatch | kana.wondering |
| `sent:tatoeba-1063425` @4 | なあ | surface-mismatch | kana.wondering |
| `sent:tatoeba-11016226` @3 | か | surface-mismatch | kana.wondering |
| `sent:tatoeba-11016226` @4 | なあ | surface-mismatch | kana.wondering |
| `sent:tatoeba-11029475` @5 | たって | surface-mismatch | tte.quotative |
| `sent:tatoeba-115333` @4 | ばかり | surface-mismatch | kurai.approximation |
| `sent:tatoeba-125105` @3 | か | surface-mismatch | kana.wondering |
| `sent:tatoeba-125105` @4 | なあ | surface-mismatch | kana.wondering |
| `sent:tatoeba-12576982` @3 | て | verifier-rejected | lex.fixed |
| `sent:tatoeba-148479` @5 | に | verifier-rejected | unclassified |
| `sent:tatoeba-163756` @4 | に | verifier-rejected | unclassified |
| `sent:tatoeba-166614` @4 | の | verifier-rejected | unclassified |
| `sent:tatoeba-1689554` @6 | て | verifier-rejected | unclassified |
| `sent:tatoeba-170284` @4 | て | verifier-rejected | lex.fixed |
| `sent:tatoeba-175757` @3 | に | verifier-rejected | ni.purpose |
| `sent:tatoeba-182254` @5 | が | verifier-rejected | ga.preface |
| `sent:tatoeba-189637` @7 | か | surface-mismatch | kana.wondering |
| `sent:tatoeba-189637` @8 | なあ | surface-mismatch | kana.wondering |
| `sent:tatoeba-235190` @2 | ばかり | surface-mismatch | kurai.approximation |
| `sent:tatoeba-3316580` @4 | か | surface-mismatch | kana.wondering |
| `sent:tatoeba-3316580` @5 | なあ | surface-mismatch | kana.wondering |
| `sent:tatoeba-3836789` @5 | か | surface-mismatch | kana.wondering |
| `sent:tatoeba-3836789` @6 | なあ | surface-mismatch | kana.wondering |
| `sent:tatoeba-78998` @1 | で | verifier-rejected | de.means |
| `sent:tatoeba-79687` @1 | に | verifier-rejected | unclassified |
| `sent:tatoeba-80587` @1 | と | surface-mismatch | toiu.naming |
| `sent:tatoeba-84420` @5 | に | verifier-rejected | unclassified |

## 5. Checks

- `validate_particle_usage.py` (hard): U0 floors; U1 usage in the enum or a named held row; U2 class,
  label and status agree with the enum; U3 the particle spells the usage; U4 compound positions; U5
  slots re-derive from the tokens (lex expressions grounded); U6 explanation == the rendered template in
  pt-BR and en; U7 token enums. **Plant-proved on a copied tree** (validator + renderer +
  derive_layerb_templates_v2 + the inputs): **13 plants, 13 caught, control green**.
- `validate_repairs_applied.py`: particle_usage.json 24,741/24,741 PASS, token_roles.json 10,271/10,271
  PASS; every older table still passes (118,743 rows, 0 FAIL).
- `validate_all.py`: ALL HARD VALIDATORS PASS (the quick replay included).
- Idempotence: the apply re-run writes nothing; the assembler re-run is byte-identical.
- Prototype: `typecheck` and `build` pass (NODE_OPTIONS=--max-old-space-size=12288); served
  `/licao/les:n5-desu-wa-01` and read the panel back from the DOM: tag "pergunta", explanation
  "か no fim da frase transforma a frase em pergunta.", the authored note beneath.
- Rendered diff of `course/` against HEAD: 0 files. Review views re-rendered (sentences/n5.md records and
  the build lines).
- Not a checkpoint: no full replay. The next checkpoint re-pins corpus/sentences/bank.json and the
  sentence review view (the replay applies migration 020 at step 1 and this apply at step 157).

## 6. Open

- Enum decisions for the 30 held rows (§4); then re-assemble and re-apply (both idempotent).
- 3 compound spans whose component rows disagree (でも: `demo.even` on one token, `de.copula` or
  `mo.concessive` on the other): sent:tatoeba-10661542, sent:tatoeba-159765, sent:tatoeba-199507. Both
  rows are verified; a ruling picks one.
- M8: render the token `role` text from the enums (the 24,399 content tokens without a role gain one).
- M9: `build_sentence_patterns.role_of()` and the role drills read usages instead of the
  (particle, function_type) table; then `function_type` can become `usages[usage].class`.
- The STATIVE lemma list is still local to derive_particle_usage.py (publish it as
  `cue_lexicons.STATIVE`).
- Rendered explanations are template-true but terse; the notes carry the nuance and stay under review
  with their sentences.

## 7. Twenty samples (seeded random over the applied rows)

| # | sentence | jp | particle | usage (status) | rendered explanation (pt-BR) | note (authored, first 90 chars) |
|---|---|---|---|---|---|---|
| 1 | `sent:gen-7dbd1394d801` n2 | 母の病気が早く治るように祈った | の @1 | `no.noun-modifier` (auto) | の marca 母 como o modificador do substantivo seguinte. | の liga 母 a 病気 ('doença DA mãe'), indicando que a doença pertence à mãe. |
| 2 | `sent:tatoeba-168195` n3 | 支払いをお願いします。 | を @1 | `wo.object` (verified) | を marca 支払い como o objeto direto. | を marca 支払い como o objeto direto de 願う, ou seja, aquilo sobre o que a ação recai. |
| 3 | `sent:gen-3d833e6acb8e` n3 | 彼女と別れて悲しい | と @1 | `to.comitative` (auto) | と marca 彼女 como quem faz a ação junto. | と marca 彼女 como a pessoa COM quem ocorreu a separação; com 別れる, o parceiro da ação leva と … |
| 4 | `sent:tatoeba-3468845` n3 | 月に大気はない。 | は @3 | `ha.contrast` (verified) | は destaca 大気: um elemento em contraste com outro. | は apresenta 大気 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação … |
| 5 | `sent:tatoeba-3385029` n2 | 警官みたいですね。 | ね @3 | `ne.confirmation` (auto) | ね no fim da frase busca a concordância do ouvinte ('né?'). | ね no fim suaviza a afirmação e pede a concordância de quem ouve, como o nosso 'né?'. |
| 6 | `sent:tatoeba-11045343` n1 | アイス買ってきてよ、カップ系のやつ。 | て @4 | `te.request` (auto) | て liga アイス買ってき ao que vem depois, com sentido de um pedido informal. | Este て fecha きて (くる na forma -て). Sozinho no fim, um verbo em -て funciona como pedido info… |
| 7 | `sent:tatoeba-78156` n3 | 旅行は期待通りでしたか。 | は @1 | `ha.topic` (verified) | は destaca 旅行: o tópico da frase (o assunto do qual se fala). | は apresenta 旅行 como assunto: é sobre a viagem que a pergunta quer saber alguma coisa. |
| 8 | `sent:tatoeba-212013` n1 | その果物は腐った。 | は @2 | `ha.topic` (verified) | は destaca その果物: o tópico da frase (o assunto do qual se fala). | は apresenta その果物 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmaçã… |
| 9 | `sent:jec-0052` n3 | 中学校の２年生が職場体験をしました | の @1 | `no.noun-modifier` (auto) | の marca 中学校 como o modificador do substantivo seguinte. | の conecta 中学校 (a escola) a ２年生 (o 2º ano), indicando 'o 2º ano do ginásio'. |
| 10 | `sent:tatoeba-2976538` n3 | 私が責任を取ります。 | を @3 | `wo.object` (verified) | を marca 責任 como o objeto direto. | を marca 責任 como o objeto direto de 取る, ou seja, aquilo sobre o que a ação recai. |
| 11 | `sent:tatoeba-220804` n5 | この川は何というのですか。 | と @4 | `to.quotative` (auto) | と marca 何 como o conteúdo do que se diz ou pensa. | と liga 何 a いう no sentido de 'chamar-se de quê': é o と citacional usado para nomes ('何という' … |
| 12 | `sent:gen-32d8debc75a0` n3 | 電車に忘れ物をしました | を @3 | `wo.object` (verified) | を marca 忘れ物 como o objeto direto. | を liga 忘れ物 ao verbo する. Na expressão 忘れ物をする, o 'esquecimento' funciona como objeto da ação… |
| 13 | `sent:gen-309d9d1e8ae7` n4 | この店はいつもうるさい | は @2 | `ha.topic` (verified) | は destaca この店: o tópico da frase (o assunto do qual se fala). | は marca この店 (esta loja) como o tema. O resto da frase é o comentário sobre ela: 'sempre é … |
| 14 | `sent:gen-6de90943b937` n3 | 毎月の電話代を払う | の @1 | `no.noun-modifier` (auto) | の marca 毎月 como o modificador do substantivo seguinte. | の liga 毎月 ('todo mês') a 電話代, formando 'a conta de telefone de todo mês'. |
| 15 | `sent:tatoeba-141549` n3 | 先生は生徒に気づいてにっこりと答えた。 | に @3 | `ni.target` (verified) | に marca 生徒 como o alvo da atitude ou da ação. | に marca 生徒 como aquilo a que a professora se dirige/percebe (気づく rege に: 'notar/perceber a… |
| 16 | `sent:tatoeba-77960` n3 | 料金は部屋につけておいていただけますか。 | は @1 | `ha.topic` (verified) | は destaca 料金: o tópico da frase (o assunto do qual se fala). | は destaca 料金 (a taxa) como o assunto: é dela que a frase inteira vai tratar. |
| 17 | `sent:gen-56f5b076dd7c` n1 | コーヒーに砂糖を入れますか | に @1 | `ni.goal` (auto) | に marca コーヒー como o destino do movimento. | に indica o lugar para onde algo vai: o açúcar entra no café. |
| 18 | `sent:gen-31015e9acf3d` n3 | この美術館は入場が無料だ | が @4 | `ga.subject` (verified) | が marca 入場 como o sujeito. | が marca 入場 (a entrada) como o sujeito específico que é gratuito, dentro do tópico maior es… |
| 19 | `sent:gen-e2b899655850` n4 | 近くにガソリンスタンドがありますか | か @6 | `ka.question` (verified) | か no fim da frase transforma a frase em pergunta. | か no fim transforma a afirmação em pergunta: 'existe...?' |
| 20 | `sent:tatoeba-223458` n1 | このところ物価が安定している。 | が @3 | `ga.subject` (verified) | が marca このところ物価 como o sujeito. | が marca 物価 como o sujeito de する, isto é, quem faz ou de quem se diz o que o predicado expr… |

## 8. Counts per usage (particle rows)

| usage | class | label (pt-BR) | total | n5 | n4 | n3 | n2 | n1 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `ha.topic` | binding | tópico | 4901 | 21 | 873 | 2110 | 868 | 1029 |
| `wo.object` | case | objeto direto | 2724 | 61 | 467 | 1069 | 511 | 616 |
| `no.noun-modifier` | case | liga substantivos (posse, pertença, atributo) | 2228 | 34 | 294 | 895 | 480 | 525 |
| `ga.subject` | case | sujeito | 2025 | 72 | 346 | 830 | 396 | 381 |
| `te.subsidiary` | conjunctive | ligação a um verbo auxiliar (〜ている, 〜てください, 〜てみる) | 1618 | 35 | 393 | 604 | 275 | 311 |
| `lex.fixed` | lexicalized | parte de uma palavra ou expressão fixa | 1232 | 85 | 307 | 511 | 158 | 171 |
| `ka.question` | sentence-final | pergunta | 665 | 68 | 191 | 237 | 78 | 91 |
| `ni.location-existence` | case | lugar onde algo está | 527 | 22 | 73 | 189 | 134 | 109 |
| `ni.goal` | case | destino (aonde se vai ou chega) | 522 | 20 | 77 | 210 | 118 | 97 |
| `yo.assertion` | sentence-final | informa ou afirma ao ouvinte | 434 | 10 | 163 | 154 | 46 | 61 |
| `no.explanatory` | nominalizer | explicativo (のだ / んです) | 378 | 41 | 119 | 124 | 39 | 55 |
| `ga.stative-object` | case | objeto de predicado de estado (gostar, saber, querer, entender) | 343 | 11 | 98 | 149 | 41 | 44 |
| `ha.contrast` | binding | contraste | 332 | 4 | 70 | 162 | 34 | 62 |
| `de.location-action` | case | lugar onde a ação acontece | 311 | 7 | 72 | 120 | 55 | 57 |
| `to.quotative` | case | citação: o que se diz ou pensa | 295 | 8 | 69 | 157 | 23 | 38 |
| `ni.result` | case | resultado de uma mudança (なる, する) | 290 | 7 | 85 | 120 | 39 | 39 |
| `ni.time-point` | case | momento (quando) | 259 | 11 | 61 | 114 | 32 | 41 |
| `ni.target` | case | alvo de uma atitude ou ação (慣れる, 気をつける, 反対する) | 247 | 5 | 23 | 107 | 41 | 71 |
| `ni.recipient` | case | destinatário (quem recebe, ouve ou é encontrado) | 209 | 5 | 32 | 107 | 25 | 40 |
| `de.means` | case | meio, instrumento ou língua | 205 | 12 | 42 | 68 | 37 | 46 |
| `no.nominalizer` | nominalizer | transforma a oração em substantivo (〜のが好き) | 195 | 2 | 42 | 84 | 18 | 49 |
| `ne.confirmation` | sentence-final | busca concordância ou confirmação | 177 | 16 | 38 | 63 | 25 | 35 |
| `kara.starting-point` | case | ponto de partida no espaço ou no tempo (de, a partir de) | 158 | 10 | 37 | 52 | 31 | 28 |
| `no.final-question` | sentence-final | pergunta informal | 154 | 17 | 39 | 56 | 15 | 27 |
| `ba.conditional` | conjunctive | se (condição) | 141 | 13 | 36 | 65 | 17 | 10 |
| `te.request` | conjunctive | pedido informal (〜て no fim) | 129 | 5 | 27 | 54 | 14 | 29 |
| `ni.adverbial` | copula-form | に que forma advérbio depois de adjetivo-na | 126 | 3 | 31 | 54 | 16 | 22 |
| `he.direction` | case | direção (rumo a) | 124 | 7 | 40 | 53 | 13 | 11 |
| `mo.concessive` | binding | mesmo que (〜ても) | 117 | 8 | 35 | 54 | 10 | 10 |
| `to.conditional` | conjunctive | quando / sempre que (consequência natural) | 115 | 4 | 29 | 41 | 20 | 21 |
| `teha.condition` | conjunctive | se (com avaliação negativa: 〜てはいけない) | 109 | 1 | 59 | 17 | 11 | 21 |
| `te.cause` | conjunctive | porque (causa de sentimento ou estado) | 105 | 2 | 27 | 32 | 17 | 27 |
| `te.manner` | conjunctive | modo ou meio (fazendo, no estado de) | 101 | 1 | 5 | 58 | 18 | 19 |
| `mo.also` | binding | também | 93 | 3 | 28 | 47 | 5 | 10 |
| `mo.total-negation` | binding | negação total (nada, ninguém) | 93 | 7 | 30 | 33 | 9 | 14 |
| `de.cause` | case | causa ou motivo | 90 | 1 | 10 | 26 | 23 | 30 |
| `yori.comparison` | case | (do) que (termo de comparação) | 90 | 4 | 23 | 42 | 11 | 10 |
| `ka.indefinite` | adverbial | algum (何か, 誰か, どこか) | 89 | 16 | 26 | 30 | 2 | 15 |
| `ni.purpose` | case | finalidade de ir ou vir | 89 | 8 | 19 | 50 | 4 | 8 |
| `te.sequence` | conjunctive | e depois (sequência) | 87 | 1 | 15 | 45 | 16 | 10 |
| `to.comitative` | case | companhia ou parceiro de uma ação mútua | 85 | 5 | 6 | 46 | 14 | 14 |
| `na.emotive` | sentence-final | exclamação ou reflexão | 84 | 13 | 32 | 21 | 5 | 13 |
| `to.parallel` | parallel | e (lista completa) | 83 | 0 | 20 | 29 | 21 | 13 |
| `ka.embedded-question` | adverbial | pergunta indireta (se, o que) | 82 | 11 | 29 | 26 | 6 | 10 |
| `na.prohibition` | sentence-final | não (proibição direta) | 80 | 5 | 22 | 31 | 10 | 12 |
| `kara.reason` | conjunctive | porque (motivo) | 79 | 5 | 27 | 28 | 7 | 12 |
| `ni.standard` | case | ponto de referência de um estado ou avaliação (近い, いい, 似る) | 79 | 0 | 11 | 34 | 10 | 24 |
| `ni.agent` | case | quem pratica a ação na voz passiva ou em 〜てもらう | 73 | 3 | 20 | 22 | 10 | 18 |
| `kurai.approximation` | adverbial | cerca de, mais ou menos; a ponto de | 71 | 15 | 25 | 23 | 8 | 0 |
| `de.manner` | case | modo ou estado de quem age (sozinho, todos juntos) | 64 | 2 | 13 | 27 | 7 | 15 |
| `made.as-far-as` | adverbial | até (limite no espaço ou num intervalo) | 61 | 4 | 12 | 28 | 11 | 6 |
| `wo.path` | case | percurso (por onde se passa) | 60 | 1 | 6 | 30 | 17 | 6 |
| `de.scope` | case | âmbito (em, entre) | 59 | 0 | 5 | 34 | 6 | 14 |
| `nitsuite.about` | case | sobre, a respeito de | 58 | 0 | 20 | 26 | 2 | 10 |
| `yo.urging` | sentence-final | insistência (vamos!, faça!) | 57 | 0 | 18 | 25 | 5 | 9 |
| `dake.only` | adverbial | só, apenas | 54 | 11 | 23 | 12 | 3 | 5 |
| `no.subject-in-modifier` | case | sujeito dentro de oração que modifica um substantivo (が → の) | 54 | 1 | 15 | 19 | 5 | 14 |
| `noni.concessive` | conjunctive | apesar de (com surpresa ou frustração) | 54 | 8 | 24 | 18 | 0 | 4 |
| `mo.both` | binding | tanto … quanto / nem … nem | 51 | 5 | 6 | 26 | 8 | 6 |
| `ga.contrast` | conjunctive | mas (contraste entre orações) | 50 | 1 | 14 | 17 | 12 | 6 |
| `node.reason` | conjunctive | porque (mais suave, explicativo) | 48 | 0 | 13 | 19 | 4 | 12 |
| `demo.even` | adverbial | até (mesmo) | 47 | 2 | 20 | 17 | 8 | 0 |
| `madeni.deadline` | adverbial | até (prazo) | 46 | 0 | 20 | 18 | 6 | 2 |
| `de.copula` | copula-form | forma contínua da cópula (ではない, 学生で、…) | 43 | 2 | 7 | 25 | 3 | 6 |
| `de.limit` | case | limite de tempo ou quantidade (em, por) | 42 | 0 | 9 | 22 | 6 | 5 |
| `tte.topic` | adverbial | tópico informal (= は / というのは) | 41 | 6 | 10 | 13 | 3 | 9 |
| `made.until` | adverbial | até (limite no tempo) | 40 | 2 | 16 | 14 | 2 | 6 |
| `hodo.degree` | adverbial | tanto quanto; (não) tão … quanto | 37 | 0 | 14 | 18 | 2 | 3 |
| `de.material` | case | material de que algo é feito | 34 | 0 | 6 | 16 | 10 | 2 |
| `ka.invitation` | sentence-final | convite (〜ませんか) | 34 | 8 | 11 | 13 | 1 | 1 |
| `kana.wondering` | sentence-final | será que | 34 | 6 | 16 | 10 | 0 | 2 |
| `shika.only-negative` | adverbial | só (com verbo negativo) | 34 | 6 | 15 | 8 | 1 | 4 |
| `ni.cause` | case | causa de um sentimento ou estado | 33 | 0 | 1 | 14 | 3 | 15 |
| `to.adverbial` | case | marca de advérbio (ゆっくりと, 高々と) | 32 | 1 | 9 | 15 | 2 | 5 |
| `nado.examples` | adverbial | coisas como, entre outros | 31 | 4 | 16 | 7 | 1 | 3 |
| `wo.departure` | case | ponto de onde se sai | 31 | 2 | 5 | 12 | 7 | 5 |
| `tte.quotative` | adverbial | citação ou boato informal (= と / そうだ) | 30 | 1 | 10 | 13 | 3 | 3 |
| `kara.source` | case | de quem ou de onde algo vem | 29 | 0 | 5 | 10 | 8 | 6 |
| `kedo.softening` | conjunctive | mas… (suaviza a frase, deixando-a em aberto) | 29 | 7 | 20 | 1 | 1 | 0 |
| `no.final-explanation` | sentence-final | explicação ou ênfase informal | 29 | 2 | 9 | 12 | 4 | 2 |
| `kedo.contrast` | conjunctive | mas, embora | 28 | 1 | 7 | 13 | 0 | 7 |
| `noni.purpose` | case | para (finalidade: 〜のに使う/いい) | 28 | 2 | 4 | 16 | 2 | 4 |
| `no.pronoun` | nominalizer | o/a (substitui um substantivo) | 26 | 0 | 11 | 6 | 4 | 5 |
| `wa.emphasis` | sentence-final | ênfase suave (feminina ou de Kansai) | 26 | 2 | 11 | 6 | 5 | 2 |
| `kara.material` | case | matéria-prima (feito de) | 25 | 0 | 6 | 8 | 9 | 2 |
| `ni.frequency` | case | proporção (por) | 25 | 0 | 11 | 8 | 4 | 2 |
| `tari.representative` | adverbial | fazer coisas como … e … | 25 | 0 | 13 | 11 | 0 | 1 |
| `te.parallel` | conjunctive | e (juntando adjetivos ou orações) | 25 | 0 | 7 | 10 | 3 | 5 |
| `bakari.only` | adverbial | só, sempre (em excesso) | 23 | 0 | 5 | 10 | 2 | 6 |
| `ka.alternative` | parallel | ou (escolha entre itens) | 23 | 2 | 7 | 8 | 2 | 4 |
| `ya.partial-list` | parallel | e (lista parcial, entre outros) | 23 | 1 | 5 | 8 | 3 | 6 |
| `kai.question` | sentence-final | pergunta informal (かい) | 22 | 0 | 16 | 6 | 0 | 0 |
| `to.comparison` | case | referência de comparação (同じ, 違う, 比べる) | 22 | 0 | 0 | 10 | 6 | 6 |
| `mo.emphasis-quantity` | binding | nada menos que (quantidade vista como grande) | 20 | 2 | 4 | 7 | 5 | 2 |
| `shi.listing-reasons` | conjunctive | e além disso (lista de motivos) | 17 | 0 | 6 | 10 | 0 | 1 |
| `ga.preface` | conjunctive | introdução que suaviza um pedido ou pergunta | 16 | 2 | 2 | 11 | 1 | 0 |
| `kara.after` | case | depois de fazer (〜てから) | 16 | 1 | 7 | 5 | 1 | 2 |
| `zo.emphasis` | sentence-final | afirmação forte (masculina, informal) | 13 | 0 | 4 | 4 | 2 | 3 |
| `kashira.wondering` | sentence-final | será que (suave) | 12 | 3 | 7 | 2 | 0 | 0 |
| `bakari.just-done` | adverbial | acabar de fazer | 11 | 0 | 9 | 2 | 0 | 0 |
| `demo.example` | adverbial | … ou algo assim (sugestão suave) | 11 | 2 | 8 | 1 | 0 | 0 |
| `to.result` | case | resultado de mudança (escrito, となる) | 11 | 0 | 2 | 4 | 3 | 2 |
| `nagara.simultaneous` | conjunctive | enquanto (duas ações ao mesmo tempo) | 10 | 0 | 6 | 3 | 0 | 1 |
| `zutsu.distributive` | adverbial | cada, de … em … | 10 | 1 | 3 | 4 | 1 | 1 |
| `sae.even` | adverbial | até (mesmo) | 9 | 1 | 1 | 4 | 0 | 3 |
| `toiu.naming` | case | chamado (N という N) | 9 | 0 | 3 | 3 | 0 | 3 |
| `wo.causee` | case | pessoa levada a agir (causativo de verbo intransitivo) | 9 | 0 | 4 | 2 | 1 | 2 |
| `kke.recall` | sentence-final | tentando lembrar (como era mesmo?) | 8 | 1 | 3 | 4 | 0 | 0 |
| `ni.source` | case | pessoa de quem se recebe (もらう, 借りる, 習う) | 8 | 0 | 2 | 4 | 1 | 1 |
| `ni.causee` | case | pessoa levada ou autorizada a fazer algo (causativo) | 7 | 0 | 4 | 3 | 0 | 0 |
| `sa.assertion` | sentence-final | afirmação leve (informal) | 7 | 1 | 2 | 3 | 1 | 0 |
| `koso.emphasis` | binding | justamente, é que (ênfase) | 6 | 1 | 1 | 4 | 0 | 0 |
| `mono.justification` | sentence-final | é que… (justificativa) | 5 | 0 | 3 | 1 | 0 | 1 |
| `yara.listing` | parallel | e … e tal (lista incerta) | 5 | 0 | 2 | 1 | 0 | 2 |
| `nomi.only` | adverbial | somente (formal) | 3 | 0 | 0 | 1 | 2 | 0 |
| `tsutsu.simultaneous` | conjunctive | enquanto (escrito); embora | 3 | 0 | 0 | 1 | 1 | 1 |
| `ka.acknowledgment` | sentence-final | recebe uma informação nova (そうですか) | 2 | 0 | 2 | 0 | 0 | 0 |
| `yori.starting-point` | case | a partir de (formal) | 2 | 0 | 0 | 0 | 1 | 1 |
| `jan.confirmation` | sentence-final | não é? (confirmação informal) | 1 | 0 | 0 | 1 | 0 | 0 |
