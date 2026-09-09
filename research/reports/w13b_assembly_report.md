# W13b — assembling the authored Layer-B for the mined N3 sentences

Regenerated 2026-09-09 by `scripts/assemble_layerb.py` after the reader was rewritten. The
previous run reported 7,823 "unverified" paragraph rows in a set that only holds 4,223, plus
5,973 particles and 3,126 rulings — more rows than were ever written. Nothing was wrong with the
authoring: the assembler was reading the verifiers' files as if they were the authors'.

## 1. What went wrong

Three separate faults, all in the reader:

1. **Verdict files were globbed as authored files.** `assemble_layerb.py` read every `*.json` in
   `layerb_out/`. A file named `paragraphs-01.json.verdict.json` has no `kind` the old `_kind()`
   recognised (`paragraphs-verdict`), so it fell back to the filename prefix and was read as 200
   more *authored* paragraph rows — rows that carry no `verdict` field and were therefore counted
   as `unverified_excluded`. Ten batches also carry the verdict under a second filename
   (`paragraphs-01.verdict.json`), so those were counted a third time. The arithmetic is exact:
   4,223 authored paragraph rows + 2,600 from the thirteen `paragraphs-*.json.verdict.json` that
   happen to use a `rows` list + 1,000 from five duplicate-pattern copies = **7,823**. Particles:
   3,391 + 2,791 + 191 = 6,373, reported as 5,973 unverified plus 395 empty-text plus 2
   fix-without-replacement plus 3 merged. Rulings: 1,563 + 1,563 = **3,126**.
2. **Verdicts were expected inside the authored row.** The old reader looked for `row['verdict']`.
   Every one of the 9,177 authored rows has `verdict: null` — the authors were told to leave it for
   an independent verifier, and the verifiers wrote a *sidecar file*. So under the old rule every
   authored row was unverified by construction, and only the three rows that happened to carry an
   inline verdict merged at all.
3. **Only one verdict container was parsed.** The verifiers used five: a `rows` list, a `verdicts`
   map, an `entries` map, a `checks` list, and a bare top-level map with no wrapper. Four of the
   files parsed as 0 rows under the old reader for that reason alone.

The new reader pairs each authored file with exactly one verdict file (stripping either filename
suffix; when both patterns exist they are compared byte-for-byte and read once), parses all five
containers, and joins rows to verdicts by stable identity — never by index. **All 9,177 verdict
entries now parse and all 9,177 pair with an authored row.**

## 2. Inventory of `research/derived/n3_mined/layerb_out/`

116 files: 55 author outputs, 61 verdict files (51 distinct verdicts, 10 of them present under
both filename patterns and byte-identical), and `_README.md`.

| author output | kind | identity | rows | container | verdict file | patterns | verdict container | entries | keyed by | ok | not ok | corrected (str/obj) | rows paired |
|---|---|---|---:|---|---|---:|---|---:|---|---:|---:|---|---:|
| `paragraphs-01.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-01.verdict.json` | 2 | rows (list) | 200 | entry fields | 197 | 3 | 0/3 | 200 |
| `paragraphs-02.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-02.json.verdict.json` | 2 | rows (list) | 200 | entry fields | 197 | 3 | 0/3 | 200 |
| `paragraphs-03.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-03.json.verdict.json` | 1 | bare map | 200 | map key | 187 | 13 | 13/0 | 200 |
| `paragraphs-04.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-04.verdict.json` | 2 | verdicts (map) | 200 | map key | 90 | 110 | 110/0 | 200 |
| `paragraphs-05.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-05.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 198 | 2 | 0/2 | 200 |
| `paragraphs-06.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-06.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 199 | 1 | 0/1 | 200 |
| `paragraphs-07.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-07.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 196 | 4 | 0/4 | 200 |
| `paragraphs-08.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-08.json.verdict.json` | 1 | verdicts (map) | 200 | map key | 168 | 32 | 32/0 | 200 |
| `paragraphs-09.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-09.json.verdict.json` | 1 | verdicts (map) | 200 | map key | 197 | 3 | 3/0 | 200 |
| `paragraphs-10.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-10.json.verdict.json` | 1 | bare map | 200 | map key | 200 | 0 | 0/0 | 200 |
| `paragraphs-11.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-11.json.verdict.json` | 1 | verdicts (map) | 200 | map key | 198 | 2 | 2/0 | 200 |
| `paragraphs-12.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-12.verdict.json` | 2 | rows (list) | 200 | entry fields | 195 | 5 | 0/5 | 200 |
| `paragraphs-13.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-13.verdict.json` | 2 | rows (list) | 200 | entry fields | 197 | 3 | 0/3 | 200 |
| `paragraphs-14.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-14.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 193 | 7 | 0/7 | 200 |
| `paragraphs-15.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-15.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 198 | 2 | 0/2 | 200 |
| `paragraphs-16.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-16.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 196 | 4 | 0/4 | 200 |
| `paragraphs-17.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-17.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 140 | 60 | 0/60 | 200 |
| `paragraphs-18.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-18.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 198 | 2 | 0/2 | 200 |
| `paragraphs-19.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-19.verdict.json` | 2 | rows (list) | 200 | entry fields | 198 | 2 | 0/2 | 200 |
| `paragraphs-20.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-20.json.verdict.json` | 1 | bare map | 200 | map key | 197 | 3 | 0/3 | 200 |
| `paragraphs-21.json` | paragraphs | (key) | 200 | `rows` | `paragraphs-21.json.verdict.json` | 1 | bare map | 200 | map key | 197 | 3 | 3/0 | 200 |
| `paragraphs-22.json` | paragraphs | (key) | 23 | `rows` | `paragraphs-22.verdict.json` | 2 | verdicts (map) | 23 | map key | 22 | 1 | 1/0 | 23 |
| `particles-01.json` | particles | (key, position) | 200 | `rows` | `particles-01.json.verdict.json` | 2 | entries (map) | 200 | map key | 188 | 12 | 0/12 | 200 |
| `particles-02.json` | particles | (key, position) | 200 | `rows` | `particles-02.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 197 | 3 | 0/3 | 200 |
| `particles-03.json` | particles | (key, position) | 200 | `rows` | `particles-03.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 198 | 2 | 0/2 | 200 |
| `particles-04.json` | particles | (key, position) | 200 | `rows` | `particles-04.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 195 | 5 | 0/5 | 200 |
| `particles-05.json` | particles | (key, position) | 200 | `rows` | `particles-05.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 195 | 5 | 0/5 | 200 |
| `particles-06.json` | particles | (key, position) | 200 | `rows` | `particles-06.json.verdict.json` | 2 | entries (map) | 200 | map key | 200 | 0 | 0/0 | 200 |
| `particles-07.json` | particles | (key, position) | 200 | `rows` | `particles-07.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 197 | 3 | 3/0 | 200 |
| `particles-08.json` | particles | (key, position) | 200 | `rows` | `particles-08.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 194 | 6 | 6/0 | 200 |
| `particles-09.json` | particles | (key, position) | 200 | `rows` | `particles-09.json.verdict.json` | 1 | verdicts (map) | 200 | map key | 197 | 3 | 0/3 | 200 |
| `particles-10.json` | particles | (key, position) | 200 | `rows` | `particles-10.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 196 | 4 | 0/4 | 200 |
| `particles-11.json` | particles | (key, position) | 200 | `rows` | `particles-11.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 195 | 5 | 5/0 | 200 |
| `particles-12.json` | particles | (key, position) | 200 | `rows` | `particles-12.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 195 | 5 | 5/0 | 200 |
| `particles-13.json` | particles | (key, position) | 200 | `rows` | `particles-13.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 195 | 5 | 0/5 | 200 |
| `particles-14.json` | particles | (key, position) | 200 | `rows` | `particles-14.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 196 | 4 | 0/4 | 200 |
| `particles-15.json` | particles | (key, position) | 200 | `rows` | `particles-15.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 197 | 3 | 0/3 | 200 |
| `particles-16.json` | particles | (key, position) | 200 | `particles` | `particles-16.json.verdict.json` | 1 | rows (list) | 200 | entry fields | 198 | 2 | 0/2 | 200 |
| `particles-17.json` | particles | (key, position) | 191 | `rows` | `particles-17.verdict.json` | 2 | rows (list) | 191 | entry fields | 185 | 6 | 0/6 | 191 |
| `rulings-01.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-01.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 148 | 2 | 2/0 | 150 |
| `rulings-02.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-02.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 149 | 1 | 1/0 | 150 |
| `rulings-03.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-03.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 149 | 1 | 1/0 | 150 |
| `rulings-04.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-04.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 128 | 22 | 22/0 | 150 |
| `rulings-05.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-05.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 149 | 1 | 0/1 | 150 |
| `rulings-06.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-06.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 145 | 5 | 5/0 | 150 |
| `rulings-07.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-07.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 130 | 20 | 20/0 | 150 |
| `rulings-08.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-08.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 150 | 0 | 0/0 | 150 |
| `rulings-09.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-09.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 150 | 0 | 0/0 | 150 |
| `rulings-10.json` | rulings | (lemma, pos) | 150 | `rows` | `rulings-10.json.verdict.json` | 1 | rows (list) | 150 | entry fields | 150 | 0 | 0/0 | 150 |
| `rulings-11.json` | rulings | (lemma, pos) | 63 | `rows` | `rulings-11.json.verdict.json` | 1 | rows (list) | 63 | entry fields | 62 | 1 | 1/0 | 63 |
| `tokens-from-rulings-02.json` | tokens | (key, position) | 59 | `rows` | `— none —` | - | - | 0 | entry fields | 0 | 0 | 0/0 | 0 |
| `tokens-from-rulings-03.json` | tokens | (key, position) | 67 | `rows` | `— none —` | - | - | 0 | entry fields | 0 | 0 | 0/0 | 0 |
| `tokens-from-rulings-05.json` | tokens | (key, position) | 66 | `rows` | `— none —` | - | - | 0 | entry fields | 0 | 0 | 0/0 | 0 |
| `tokens-from-rulings-06.json` | tokens | (key, position) | 84 | `rows` | `— none —` | - | - | 0 | entry fields | 0 | 0 | 0/0 | 0 |
| `tokens-from-rulings-08.json` | tokens | (key, position) | 26 | `rows` | `— none —` | - | - | 0 | entry fields | 0 | 0 | 0/0 | 0 |

Reading of that table:

- **identity** is what a row is joined on, and it is the same identity the work list, the author,
  the verifier and `persist_dissection.py` all use. `key` is `str(tatoeba_id)` for a real sentence
  and `gen-<sha1(jp)[:12]>` for a generated one; `position` is the Dissector's C-token position.
- **keyed by** says where the verifier put the identity: inside the entry (`key`/`position`/
  `lemma`/`pos`) or in the map key (`<key>` for paragraphs, `<key>#<position>` for particles).
  Both are read; entry fields win, the map key is the fallback.
- **rows paired** is the count of authored identities that found a verdict entry. It equals the
  row count on every batch that has a verdict file — no drift, no renumbering, no strays.
- The five `tokens-from-rulings-*.json` files have **no verdict file of their own** (see §4).

### Verdict entry shapes actually present

| shape | count | how it is read |
|---|---:|---|
| `{key, ok}` / `{lemma, pos, ok}` / `{key, position, surface, ok}` | 8,786 `ok: true` | accept the authored text, status `verified` |
| the same plus `problem` + `corrected` | 391 `ok: false` | merge the replacement, status `corrected` |
| `corrected` as a plain string | 235 | the replacement text itself |
| `corrected` as an object (`{structure_explanation_pt: …}`, `{explanation_pt, function_pt}`, `{ruling, per_context}`, …) | 156 | the replacement is read out by field name |
| `corrected_function_pt` alongside `ok: true` | 89 | the explanation stands; only the modal label is replaced |
| `verifier_explanation_pt` + `verdict: "fix"` | 5 | the `fix` path of the original contract |

Fifteen particle entries read `ok: false` with a `corrected` object holding **only** `function_pt`,
and their `problem` text explicitly endorses the authored explanation ("A explicação já diz…").
Those are a rejection of the bank's modal *label*, not of the learner-facing explanation. Dropping
the row would have emptied fifteen required slots over a complaint about a different field, so the
assembler accepts the explanation, applies the label fix, and counts them separately as
`particles:accepted_with_side_fix`.

## 3. Result

| kind | slots | derived, carried | filled verified | filled corrected | still empty |
|---|---:|---:|---:|---:|---:|
| token gloss | 17,057 | 4,536 | 12,166 | 239 | 116 |
| particle explanation | 10,257 | 6,866 | 3,333 | 58 | 0 |
| structure paragraph | 4,223 | 0 | 3,958 | 265 | 0 |

Merge counts, by authored kind:

```json
{
 "paragraphs:corrected": 265,
 "paragraphs:verified": 3958,
 "particles:accepted_with_side_fix": 15,
 "particles:corrected": 58,
 "particles:function_pt_corrected": 126,
 "particles:verified": 3333,
 "rulings:context_splits": 480,
 "rulings:corrected": 53,
 "rulings:verified": 1510,
 "tokens:excluded_and_said_nowhere_else": 59,
 "tokens:excluded_but_redundant_with_verified_ruling_split": 243,
 "tokens:unverified_excluded": 302
}
```

`ingest_ready`: **false** — 116 required slot(s) still empty.

`ingest_ready` is computed against what the ingest actually needs, read out of
`scripts/ingest/ingest_mined_stages.py` and `scripts/validate/validate.py`: every bank sentence is
`dissection_tier: "full"`, and the validator reads that as a hard promise of **a gloss on every
content token, an explanation on every particle, and a structure paragraph on the sentence**. Those
three are the required slots. `function_pt` is carried but the validator does not require it, so it
does not gate.

## 4. What is still empty, and why

**116 token glosses — the residue that was never authored.** `build_layerb_work.py` wrote a work
list `layerb_work/tokens-residue.json` holding the 154 content tokens no registry or bank lookup
could gloss; 38 of them were resolved by the numeral rule and carry a gloss already, leaving 116
for an author. **There is no output file for that work list anywhere in the repo** — the tokens
campaign was never run. These are the only slots blocking the ingest. They are proper nouns and
low-frequency words (大阪, 乗組員, 木の葉, ついばむ, 商店街, 近いうちに, …), one short authoring
batch.

**0 particle explanations and 0 structure paragraphs empty.**

**302 token rows excluded for want of a verdict, costing nothing.** The five
`tokens-from-rulings-*.json` files are a flattening of context splits the rulings authors had
already written inside their ruling rows. They have no verdict file of their own, so under the
standing rule (a row with no verdict is excluded, never passed) they do not merge. 243 of the 302
restate a split that is already present in a **verified** ruling row, with zero disagreements, so
nothing is lost. The remaining 59 — all of them in `tokens-from-rulings-02.json`, whose sibling
`rulings-02.json` recorded no context fields — are said nowhere else; those tokens fall back to the
verified pair-level ruling, which is a correct if less precise gloss. They are named here rather
than silently merged.

**480 context splits did land**, from ruling rows that carry `context_overrides` / `per_context` /
`context_glosses` and are covered by the ruling's own verdict. They show in the merged batches as
`gloss_origin: "ruling-context"`.

## 5. Thirty random sentences, full Layer-B

Seed 1313 over the 4,223 assembled sentences. `[v]` = verified as authored, `[c]` = the verifier's
replacement, `[d]` = carried from the mechanical derivation, `[—]` = empty.

### 1. `74130` — ここの下りも手掛かりがないので危険だ。

*les:n3-desejos-03 · targets: vocab:1184370 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | ここ | aqui | `[v]` | ruling |
| 2 | 下り | descida | `[v]` | ruling |
| 4 | 手掛かり | pista; indício; ponto de apoio | `[d]` | registry |
| 6 | ない | não (negação) | `[v]` | ruling |
| 9 | 危険 | perigo, perigoso | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | の | partícula de ligação/posse | の liga ここ a 下り e junta os dois num bloco só, em que 下り é o núcleo e ここ o modificador. | `[d]` |
| 3 | も | partícula de inclusão ('também') | も vem depois de ここの下り e soma essa descida às outras já tidas como perigosas: não é a única com esse problema. | `[v]` |
| 5 | が | partícula de sujeito | が marca 手掛かり como o sujeito de ない, isto é, quem faz ou de quem se diz o que o predicado exprime. | `[d]` |
| 7 | の | の da conjunção ので (porque) | の se apoia em 手掛かりがない e, com o で logo depois, forma ので: a falta de apoio para as mãos entra como o motivo do perigo. | `[v]` |

**Estrutura** `[v]` — Duas orações ligadas por ので, que apresenta a primeira como causa da segunda num tom mais explicativo que から. A causa é 手掛かりがない ('não há onde se segurar'), e o tema da frase, ここの下り, vem com も somando essa descida a outra já mencionada; 危険だ fecha com a cópula casual.

### 2. `157960` — 私は会合に出席します。

*les:n3-causa-04 · targets: vocab:1198530 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 私 | eu | `[v]` | ruling |
| 2 | 会合 | reunião, encontro | `[v]` | ruling |
| 4 | 出席 | presença, comparecimento | `[v]` | ruling |
| 5 | する | fazer | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 私 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 3 | に | partícula que marca o evento a que se comparece | に marca 会合 como aquilo a que a pessoa vai comparecer. Com 出席する, o encontro vem sempre com に. | `[v]` |

**Estrutura** `[v]` — 私 é o tópico com は e o predicado é 出席します, o substantivo 出席 mais する na forma polida. に marca 会合 como o evento a que se comparece, já que esse verbo pede に.

### 3. `222882` — この音楽はバッハによって作曲された。

*les:n3-concessao-03 · targets: vocab:1297650 · clause: coordinate*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | この | este, esse | `[v]` | ruling |
| 1 | 音楽 | música | `[v]` | ruling |
| 3 | バッハ | **(empty)** | `[—]` | — |
| 5 | よる | por, por meio de | `[v]` | ruling |
| 7 | 作曲 | composição musical; compor (música) | `[d]` | registry |
| 8 | する | fazer | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | は | partícula de tópico | は apresenta この音楽 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 4 | に | partícula fixa da locução ～によって (agente da passiva) | に abre バッハによって e aponta quem compôs. Em frase passiva, によって é o jeito comum de apresentar o autor da ação. | `[v]` |
| 6 | て | partícula conectiva (forma て) | て liga よる ao que vem depois (作曲) e encadeia os dois dentro da mesma frase. | `[d]` |

**Estrutura** `[v]` — は marca この音楽 como tópico e o predicado é a passiva 作曲された (作曲する mais され no passado). バッハによって usa によって para apontar quem compôs, a forma que se usa para o autor de uma obra.

### 4. `1795640` — その猫は可愛らしい。

*les:n3-intencao-04 · targets: vocab:1190740 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | その | esse, aquele | `[v]` | ruling |
| 1 | 猫 | gato | `[v]` | ruling |
| 3 | 可愛らしい | fofo; encantador; adorável | `[d]` | registry |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | は | partícula de tópico | は apresenta その猫 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |

**Estrutura** `[v]` — Frase de duas peças: その猫 é o tópico com は e 可愛らしい, adjetivo い, fecha sozinho, sem precisar de verbo.

### 5. `195802` — まあ無理ですな。

*les:n3-limites-07 · targets: vocab:1012050 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | まあ | bem, sei lá | `[v]` | ruling |
| 1 | 無理 | impossível, sem condições | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 3 | な | partícula final de constatação (equivale a ね) | Este な não proíbe nada: preso a です, ele arremata a constatação com ar resignado, como faria o ね, 'não vai dar mesmo'. | `[v]` |

**Estrutura** `[v]` — まあ abre a frase com hesitação, e 無理 é o predicado nominal ('não dá, é impossível') fechado pela cópula polida です. O な do fim não é proibição: é a partícula de quem comenta em voz alta, num tom resignado.

### 6. `224405` — ここに傷があるので安くしてください。

*les:n3-intencao-04 · targets: vocab:1580260 · clause: imperative*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | ここ | aqui | `[v]` | ruling |
| 2 | 傷 | arranhão; defeito | `[c]` | ruling-context |
| 4 | ある | existir, haver | `[v]` | ruling |
| 7 | 安い | barato | `[v]` | ruling |
| 8 | する | fazer | `[v]` | ruling |
| 10 | くださる | por favor (faça) | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | に | partícula de lugar de existência | に marca ここ como o lugar onde está o arranhão: com ある, に aponta onde a coisa se encontra. | `[v]` |
| 3 | が | partícula de sujeito | が marca 傷 como o sujeito de ある, isto é, quem faz ou de quem se diz o que o predicado exprime. | `[d]` |
| 5 | の | partícula que forma a conjunção de causa ので | の se junta a で e forma ので: apresenta o arranhão como o motivo do pedido de desconto. | `[v]` |
| 9 | て | partícula conectiva (forma て) | て liga する ao que vem depois (くださる) e encadeia os dois dentro da mesma frase. | `[d]` |

**Estrutura** `[v]` — A primeira parte é a razão: ここに marca o lugar com に, 傷が é o sujeito de ある, e ので no fim apresenta tudo isso como o motivo, num tom mais suave que から. Depois vem o pedido, 安くしてください, com o adjetivo 安い na forma 安く antes de する.

### 7. `213618` — そこは何の特徴もない町だ。

*les:n3-intencao-06 · targets: vocab:1455170 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | そこ | aí, lá | `[v]` | ruling |
| 2 | 何 | o que | `[v]` | ruling |
| 4 | 特徴 | característica, marca registrada, traço distintivo | `[d]` | bank-modal |
| 6 | ない | não (negação) | `[v]` | ruling |
| 7 | 町 | cidade, vila | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta そこ como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 3 | の | partícula de ligação/posse | の liga 何 a 特徴 e junta os dois num bloco só, em que 特徴 é o núcleo e 何 o modificador. | `[d]` |
| 5 | も | も de negação total (何の〜もない) | Este も vem depois de 何の特徴 e, com a negação ない, zera a lista: nenhuma característica, nem uma. | `[v]` |

**Estrutura** `[v]` — そこ é o tópico com は e o predicado é 町だ. Antes de 町 vem a oração 何の特徴もない, que qualifica a cidade: 何の junto de も e de uma negativa dá o sentido de 'nenhum', e ない fecha a ideia de uma cidade sem traço nenhum.

### 8. `141363` — 川は山から下って湾に注いでいる。

*les:n3-estado-08 · targets: vocab:1562800 · clause: coordinate*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 川 | rio | `[v]` | ruling |
| 2 | 山 | montanha | `[v]` | ruling |
| 4 | 下る | descer | `[d]` | bank-modal |
| 6 | 湾 | baía; golfo | `[d]` | registry |
| 8 | 注ぐ | desaguar em | `[v]` | ruling-context |
| 10 | いる | estar | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 川 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 3 | から | partícula de origem/ponto de partida | から marca 山 como o ponto de onde o rio desce. | `[v]` |
| 5 | て | partícula conectiva (forma て) | て liga 下る ao que vem depois (湾) e encadeia os dois dentro da mesma frase. | `[d]` |
| 7 | に | partícula de destino/direção | に marca 湾 como o ponto de chegada da água: é ali que o rio desemboca. | `[v]` |
| 9 | で | partícula conectiva (forma て) | Este で é o て sonorizado de 注ぐ: liga 注い a いる e forma 注いでいる, o estado contínuo do rio que deságua na baía. | `[v]` |

**Estrutura** `[v]` — は marca 川 como tópico. A primeira oração 山から下って usa から para a origem e 下る na forma て, encadeando com a segunda, 湾に注いでいる, onde に marca o destino e 注ぐ vem na forma ている, descrevendo o curso permanente do rio.

### 9. `142980` — 正にそれが私の考えです。

*les:n3-limites-07 · targets: vocab:1376640 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 正に | exatamente, precisamente | `[v]` | ruling |
| 1 | それ | isso | `[v]` | ruling |
| 3 | 私 | eu | `[v]` | ruling |
| 5 | 考え | ideia; jeito de pensar | `[d]` | bank-modal |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | が | partícula de sujeito | が marca 正にそれ como o sujeito daquilo que se afirma em seguida. | `[d]` |
| 4 | の | partícula de ligação/posse | の liga 私 a 考え e junta os dois num bloco só, em que 考え é o núcleo e 私 o modificador. | `[d]` |

**Estrutura** `[v]` — 正に é advérbio e reforça o que vem depois. それ leva が porque a frase identifica qual é o pensamento, e o predicado é 私の考えです, com の ligando 私 a 考え.

### 10. `8916462` — よく気付いたね！

*les:n3-deveres-01 · targets: vocab:1591330 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | よく | bem, frequentemente | `[v]` | ruling |
| 1 | 気付く | perceber; notar; dar-se conta | `[d]` | registry |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 3 | ね | partícula final de concordância | ね no fim suaviza a afirmação e pede a concordância de quem ouve, como o nosso 'né?'. | `[d]` |

**Estrutura** `[v]` — よく é o advérbio de よい e, colado a um verbo no passado, vira elogio: 'fez bem em notar'. 気付いた é o passado casual de 気付く, e o ね busca a cumplicidade de quem ouve.

### 11. `152201` — 私もまた、議員の一人です。

*les:n3-intencao-02 · targets: vocab:1226020 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 私 | eu | `[v]` | ruling |
| 2 | また | também, além disso | `[c]` | ruling-context |
| 4 | 議員 | parlamentar; deputado; vereador | `[d]` | registry |
| 6 | 一人 | uma pessoa, sozinho | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | も | partícula de inclusão ('também') | も entra no lugar de は depois de 私 e acrescenta quem fala ao grupo dos parlamentares: ele é mais um entre eles. | `[v]` |
| 5 | の | partícula de ligação/posse | の liga 議員 a 一人 e junta os dois num bloco só, em que 一人 é o núcleo e 議員 o modificador. | `[d]` |

**Estrutura** `[v]` — も e また se reforçam um ao outro ('eu também, do mesmo jeito'), e a vírgula dá a pausa antes do predicado. 議員の一人 usa の para dizer 'um dos parlamentares', e o です fecha em forma polida.

### 12. `11524876` — どのチームが一番好き？

*les:n3-relato-05 · targets: vocab:1077360 · clause: question*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | どの | qual | `[v]` | ruling |
| 1 | チーム | time, equipe | `[d]` | bank-modal |
| 3 | 一番 | o mais, número um | `[v]` | ruling |
| 4 | 好き | gostar de, preferido | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | が | partícula de sujeito | が marca どのチーム como o sujeito de 好き, isto é, quem faz ou de quem se diz o que o predicado exprime. | `[d]` |

**Estrutura** `[v]` — どの qualifica チーム e が marca esse bloco como aquilo que agrada, porque 好き é adjetivo な e pede が, não を. 一番 dá o grau ('mais que todos') e a pergunta fica na entonação.

### 13. `177159` — 君は手先が器用だね。

*les:n3-deveres-01 · targets: vocab:1218960 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 君 | você (informal) | `[v]` | ruling |
| 2 | 手先 | **(empty)** | `[—]` | — |
| 4 | 器用 | habilidoso; jeitoso | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 君 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 3 | が | partícula de sujeito | が marca 手先 como o sujeito de 器用, isto é, quem faz ou de quem se diz o que o predicado exprime. | `[d]` |
| 6 | ね | partícula final de concordância | ね no fim suaviza a afirmação e pede a concordância de quem ouve, como o nosso 'né?'. | `[d]` |

**Estrutura** `[v]` — Dois marcadores: は abre com 君 como assunto e が aponta 手先 como a parte que recebe o elogio. 器用だ é o predicado, e o ね final busca a concordância de quem ouve.

### 14. `178837` — 君こそ私が探していた人だ。

*les:n3-enfase-01 · targets: gram:n3-koso · clause: coordinate*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 君 | você (informal) | `[v]` | ruling |
| 2 | 私 | eu | `[v]` | ruling |
| 4 | 探す | procurar | `[v]` | ruling |
| 6 | いる | estar | `[v]` | ruling |
| 8 | 人 | pessoa | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | こそ | partícula de ênfase | こそ realça 君: é você e não outra pessoa. | `[v]` |
| 3 | が | partícula de sujeito | が marca 私 como o sujeito de 探す, isto é, quem faz ou de quem se diz o que o predicado exprime. | `[d]` |
| 5 | て | partícula conectiva (forma て) | て liga 探す ao que vem depois (いる) e encadeia os dois dentro da mesma frase. | `[d]` |

**Estrutura** `[v]` — こそ vem depois de 君 e destaca justamente essa pessoa. 私が探していた é uma oração que qualifica 人, e dentro dela 私 leva が, já que は fica reservado ao assunto principal; だ fecha o predicado nominal.

### 15. `221140` — この小包は君宛てだ。

*les:n3-enfase-03 · targets: vocab:1593290 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | この | este, esse | `[v]` | ruling |
| 1 | 小包 | encomenda; pacote (postal) | `[d]` | registry |
| 3 | 君 | você (informal) | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | は | partícula de tópico | は apresenta この小包 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |

**Estrutura** `[v]` — この小包 é o tópico com は e o predicado é 君宛て mais だ, em que o sufixo 宛て (endereçado a) se cola ao pronome 君. Não há verbo: だ liga o pacote ao destinatário.

### 16. `231127` — あの絵を見て何を想像しますか。

*les:n3-deveres-04 · targets: vocab:1399610 · clause: question*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | あの | aquele | `[v]` | ruling |
| 1 | 絵 | quadro, desenho | `[v]` | ruling |
| 3 | 見る | ver, olhar | `[v]` | ruling |
| 5 | 何 | o que | `[v]` | ruling |
| 7 | 想像 | imaginação | `[v]` | ruling |
| 8 | する | fazer | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | を | marcador de objeto direto | を marca あの絵 como o objeto direto de 見る, ou seja, aquilo sobre o que a ação recai. | `[d]` |
| 4 | て | partícula conectiva (forma て) | て liga 見る ao que vem depois (何) e encadeia os dois dentro da mesma frase. | `[d]` |
| 6 | を | marcador de objeto direto | を marca 何 como o objeto direto de する, ou seja, aquilo sobre o que a ação recai. | `[d]` |
| 10 | か | partícula interrogativa | か no fim transforma a frase em pergunta. | `[d]` |

**Estrutura** `[v]` — A primeira parte, あの絵を見て, usa a forma て de 見る para dizer 'ao ver aquele quadro' e prepara o que vem depois. Na segunda, 何 leva を como objeto de 想像する, e ますか fecha a pergunta em tom polido.

### 17. `8754824` — 日曜日は営業してますか？

*les:n3-perspectiva-02 · targets: vocab:1173430 · clause: question*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 日曜日 | domingo | `[d]` | bank-modal |
| 2 | 営業 | funcionamento; expediente | `[v]` | ruling |
| 3 | する | fazer | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 日曜日 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 6 | か | partícula interrogativa | か no fim transforma a frase em pergunta. | `[d]` |

**Estrutura** `[v]` — は destaca 日曜日 e o põe em contraste com os outros dias da semana. O predicado é 営業してます, contração polida de 営業しています, que descreve o estabelecimento em funcionamento, e か fecha a pergunta.

### 18. `8596638` — 離婚したくないんだ。

*les:n3-perspectiva-07 · targets: vocab:1550880 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 離婚 | divórcio | `[v]` | ruling |
| 1 | する | fazer | `[v]` | ruling |
| 3 | ない | não (negação) | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 4 | ん | nominalizador explicativo (ん = の) | ん dá tom de explicação a 離婚したくない: quem fala está justificando a própria posição. | `[v]` |

**Estrutura** `[v]` — 離婚したい é 離婚する com o sufixo たい e, como たい se comporta como adjetivo-i, a negativa troca い por くない: 離婚したくない. んだ no fim dá o tom de explicação, de quem se posiciona.

### 19. `202080` — でも素敵だわ。

*les:n3-causa-05 · targets: vocab:1397350 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 2 | 素敵 | lindo; maravilhoso; ótimo | `[d]` | registry |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 0 | で | で da conjunção inicial でも ('mas') | で abre a frase e, junto de も, forma でも: o que vem depois contraria o que se disse antes. | `[v]` |
| 1 | も | も da conjunção でも ('mas') | も fecha でも e completa a virada: apesar de tudo, a coisa é linda. | `[v]` |
| 4 | わ | partícula final expressiva | わ no fim suaviza a afirmação e dá um tom expressivo, tradicionalmente associado à fala feminina, sem mudar o sentido literal. | `[d]` |

**Estrutura** `[v]` — でも aqui é a conjunção 'mas', que abre a frase marcando o contraste com o que veio antes. 素敵だ é o adjetivo nominal com a cópula, e わ no fim é a partícula expressiva que suaviza a afirmação.

### 20. `98819` — 彼は贅沢な生活を送った。

*les:n3-estado-05 · targets: vocab:1573150 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 彼 | ele | `[v]` | ruling |
| 2 | 贅沢 | luxo, extravagância | `[v]` | ruling |
| 4 | 生活 | vida, cotidiano | `[v]` | ruling |
| 6 | 送る | levar (a vida) | `[v]` | ruling-context |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 彼 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 5 | を | marcador de objeto direto | を marca 贅沢な生活 como o objeto direto de 送る, ou seja, aquilo sobre o que a ação recai. | `[d]` |

**Estrutura** `[v]` — 彼 é o tópico com は e o objeto é 贅沢な生活, marcado por を, com 贅沢 recebendo な por ser adjetivo な. 送る aqui não é enviar: junto de 生活 quer dizer levar a vida de certo jeito, e está no passado 送った.

### 21. `140271` — 霜が作物に大きな損害を与えた。

*les:n3-relato-03 · targets: vocab:1402930 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 霜 | geada | `[d]` | registry |
| 2 | 作物 | plantação; cultura agrícola; colheita | `[d]` | registry |
| 4 | 大きな | grande | `[v]` | ruling |
| 5 | 損害 | dano; prejuízo; perda | `[d]` | registry |
| 7 | 与える | dar, causar | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | が | partícula de sujeito | が marca 霜 como o sujeito de 与える, isto é, quem faz ou de quem se diz o que o predicado exprime. | `[d]` |
| 3 | に | partícula de destino/direção | に marca 作物 como quem recebe o prejuízo; 与える pede に para o destinatário. | `[v]` |
| 6 | を | marcador de objeto direto | を marca 大きな損害 como o objeto direto de 与える, ou seja, aquilo sobre o que a ação recai. | `[d]` |

**Estrutura** `[v]` — A frase traz os três papéis explícitos: 霜 é quem age, com が; 作物 é quem recebe, com に; e 損害 é o que se dá, com を. O verbo é 与えた, passado de 与える, e 大きな qualifica 損害 direto, sem precisar de nada no meio.

### 22. `995147` — 君に任せるよ。

*les:n3-limites-07 · targets: vocab:1467150 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 君 | você (informal) | `[v]` | ruling |
| 2 | 任せる | confiar (a alguém); deixar (uma tarefa) a cargo de | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | に | partícula de destino/direção | に marca 君 como a pessoa em quem se confia a decisão; 君に任せる é 'deixo por sua conta'. | `[v]` |
| 3 | よ | partícula final de ênfase | よ no fim passa a informação ao ouvinte com ênfase, como quem diz 'olha' ou 'viu'. | `[d]` |

**Estrutura** `[v]` — に marca 君 como a pessoa a quem a coisa é entregue, uso comum com verbos de confiar e de dar. 任せる vem na forma de dicionário, que aqui vale como decisão tomada na hora, e よ comunica isso ao outro.

### 23. `1218431` — 笑いは移る。

*les:n3-estado-08 · targets: vocab:1351280 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 笑い | riso; risada | `[d]` | bank-modal |
| 2 | 移る | contagiar, transmitir-se | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 笑い como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |

**Estrutura** `[v]` — 笑い, o substantivo tirado de 笑う, é o tópico com は, e o verbo é 移る no presente, que aqui vale como fato geral: o riso passa de um para outro.

### 24. `9842044` — 私には影響ないと思う。

*les:n3-perspectiva-02 · targets: vocab:1173660 · clause: quote*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 私 | eu | `[v]` | ruling |
| 3 | 影響 | influência, efeito | `[v]` | ruling |
| 4 | ない | não (negação) | `[v]` | ruling |
| 6 | 思う | achar, pensar | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | に | marca de quem recebe | に marca 私 como a pessoa sobre quem a influência recairia. | `[v]` |
| 2 | は | partícula de tópico | は vem depois de に e põe 私 como tema, com contraste: comigo, pelo menos, não pega. | `[v]` |
| 5 | と | partícula de citação | と marca 私には影響ない como o conteúdo do pensamento. | `[v]` |

**Estrutura** `[v]` — 私には marca com に a quem a coisa chegaria, e は destaca essa pessoa em contraste com as demais. O conteúdo do juízo é 影響ない ('não há efeito', com o が de 影響 omitido, como se faz na fala), fechado por と antes do verbo 思う.

### 25. `103900` — 彼は食品会社に就職した。

*les:n3-estrutura-03 · targets: vocab:1358600 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 彼 | ele | `[v]` | ruling |
| 2 | 食品 | alimento; produto alimentício; gêneros alimentícios | `[d]` | registry |
| 3 | 会社 | empresa | `[v]` | ruling |
| 5 | 就職 | conseguir emprego; obtenção de emprego | `[d]` | registry |
| 6 | する | fazer | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 彼 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 4 | に | partícula de destino/direção | に marca 食品会社 como o lugar onde ele se empregou; 就職する pede に. | `[v]` |

**Estrutura** `[v]` — 彼 é o tópico com は e o comentário é 就職した, passado de 就職する (conseguir emprego). に marca 食品会社 como o ponto de chegada, a empresa em que ele entrou para trabalhar; 食品会社 é um composto de 食品 (alimentos) e 会社 (empresa).

### 26. `151213` — 紙に自分の名を記入した。

*les:n3-desejos-06 · targets: vocab:1531330 · clause: simple*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 紙 | papel | `[d]` | bank-modal |
| 2 | 自分 | si mesmo, próprio | `[v]` | ruling |
| 4 | 名 | nome | `[v]` | ruling |
| 6 | 記入 | preencher; anotar; registrar | `[d]` | registry |
| 7 | する | fazer | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | に | partícula de lugar | に marca 紙 como a superfície onde o nome foi escrito; 記入する pede に para o suporte preenchido. | `[v]` |
| 3 | の | partícula de ligação/posse | の liga 自分 a 名 e junta os dois num bloco só, em que 名 é o núcleo e 自分 o modificador. | `[d]` |
| 5 | を | marcador de objeto direto | を marca 名 como o objeto direto de する, ou seja, aquilo sobre o que a ação recai. | `[d]` |

**Estrutura** `[v]` — に marca 紙 como a superfície onde se escreve e を marca 自分の名 como aquilo que se escreve, com の ligando 自分 a 名. 記入した é o passado de 記入する, 'preencher'.

### 27. `208189` — その団体は全部で５０名の学生から成っている。

*les:n3-relato-05 · targets: vocab:1419270 · clause: coordinate*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | その | esse, aquele | `[v]` | ruling |
| 1 | 団体 | grupo; organização; associação | `[d]` | registry |
| 3 | 全部 | no total | `[v]` | ruling-context |
| 5 | 50 | 50 | `[d]` | rule-numeral |
| 6 | 名 | pessoas (contador) | `[v]` | ruling-context |
| 8 | 学生 | estudante, aluno | `[v]` | ruling |
| 10 | 成る | ser composto de, consistir em | `[d]` | bank-modal |
| 12 | いる | estar | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | は | partícula de tópico | は apresenta その団体 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 4 | で | で de totalização (全部で) | で fecha 全部 e forma 全部で, que apresenta o número como a soma: cinquenta alunos ao todo. | `[v]` |
| 7 | の | partícula de ligação/posse | の liga ５０名 a 学生 e junta os dois num bloco só, em que 学生 é o núcleo e ５０名 o modificador. | `[d]` |
| 9 | から | から de composição (〜から成る) | Em 〜から成る, から marca 学生 como aquilo de que o grupo é feito, e não um ponto de partida no espaço. | `[v]` |
| 11 | て | partícula conectiva (forma て) | て liga 成る ao que vem depois (いる) e encadeia os dois dentro da mesma frase. | `[d]` |

**Estrutura** `[c]` — O tópico é その団体, com は, e 全部で dá o total; ５０名の学生から marca com から aquilo de que o grupo é feito, com 名 contando pessoas e の prendendo o número a 学生. 成っている, na forma ている, apresenta a composição como algo que vale sempre.

### 28. `199281` — なぜあなたは私を疑うのですか。

*les:n3-perspectiva-01 · targets: vocab:1225510 · clause: question*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | なぜ | por que | `[v]` | ruling |
| 1 | あなた | você | `[v]` | ruling |
| 3 | 私 | eu | `[v]` | ruling |
| 5 | 疑う | desconfiar; suspeitar | `[v]` | ruling-context |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 2 | は | partícula de tópico | は apresenta なぜあなた como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 4 | を | marcador de objeto direto | を marca 私 como o objeto direto de 疑う, ou seja, aquilo sobre o que a ação recai. | `[d]` |
| 6 | の | nominalizador explicativo (のです) | の recolhe あなたは私を疑う e transforma o fato em algo a explicar: a pergunta cobra o motivo da desconfiança, não a desconfiança em si. | `[v]` |
| 8 | か | partícula interrogativa | か no fim transforma a frase em pergunta. | `[d]` |

**Estrutura** `[v]` — なぜ abre a frase pedindo o motivo, あなた é o tópico com は e 私 é o objeto de 疑う com を. No fim, のです dá o tom de quem cobra uma explicação e か faz a pergunta.

### 29. `90364` — 彼女は靴のひもを締めた。

*les:n3-perspectiva-06 · targets: vocab:1487970 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 彼女 | ela | `[v]` | ruling |
| 2 | 靴 | sapato | `[v]` | ruling |
| 4 | ひも | cordão, cadarço | `[d]` | bank-modal |
| 6 | 締める | amarrar, apertar, atar | `[v]` | ruling |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 彼女 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 3 | の | partícula de ligação/posse | の liga 靴 a ひも e junta os dois num bloco só, em que ひも é o núcleo e 靴 o modificador. | `[d]` |
| 5 | を | marcador de objeto direto | を marca ひも como o objeto direto de 締める, ou seja, aquilo sobre o que a ação recai. | `[d]` |

**Estrutura** `[v]` — 彼女 vem marcado por は na função de tópico e 締めた é o verbo. を marca 靴のひも como objeto, com の ligando 靴 a ひも para dizer de que cordão se trata.

### 30. `176153` — 警察は調査を続けた。

*les:n3-conectores-06 · targets: vocab:1429120 · clause: topic-comment*

| pos | lemma | gloss pt-BR | | origin |
|---:|---|---|---|---|
| 0 | 警察 | polícia | `[d]` | bank-modal |
| 2 | 調査 | pesquisa, investigação | `[v]` | ruling |
| 4 | 続ける | continuar | `[d]` | bank-modal |

| pos | partícula | função | explicação | |
|---:|---|---|---|---|
| 1 | は | partícula de tópico | は apresenta 警察 como o tópico da frase, ou seja, o assunto sobre o qual se faz a afirmação seguinte. | `[d]` |
| 3 | を | marcador de objeto direto | を marca 調査 como o objeto direto de 続ける, ou seja, aquilo sobre o que a ação recai. | `[d]` |

**Estrutura** `[v]` — 警察 é o tópico com は e 調査 é o objeto marcado por を. 続ける aparece no passado 続けた e é o verbo transitivo do par, ou seja, alguém continua alguma coisa.

## 6. Twenty rulings and the contexts they reached

A ruling is one decision about a `(lemma, pos)` pair, applied to every `ambiguous-verify` token
carrying that pair. The first eight below are pairs the author split by context; the rest are
drawn at random from the pairs that were applied.

### 1. 酒 · noun → **bebida alcoólica; saquê**  `[v]`

*rulings-07.json · reaches 3 token(s)*

> One occurrence is specifically saquê (酒は米で作ります).

Context splits declared in the ruling row (inherit its verdict):

- `148447` → **saquê** — 酒は米で作ります。

Where it landed:

- `148447`#0 *ruling-context* → saquê — 酒は米で作ります。
- `227035`#1 *ruling* → bebida alcoólica; saquê — お酒を飲もうよ。
- `11926656`#1 *ruling* → bebida alcoólica; saquê — お酒は苦手です。

### 2. 明るい · i-adjective → **claro, iluminado**  `[v]`

*rulings-03.json · reaches 5 token(s)*

> 83763 is 明るい面 = 'o lado bom'.

Context splits declared in the ruling row (inherit its verdict):

- `83763` → **bom, positivo** — 物事の明るい面を見なさい。

Where it landed:

- `144433`#2 *ruling* → claro, iluminado — 人は明るい日の光を好む。
- `83763`#2 *ruling-context* → bom, positivo — 物事の明るい面を見なさい。
- `117841`#6 *ruling* → claro, iluminado — 彼の顔は喜びで明るくなった。
- `85361`#2 *ruling* → claro, iluminado — 表情が明るくなった。
- … and 1 more

### 3. 昼 · noun → **almoço, meio-dia; dia (período diurno)**  `[c]`

*rulings-04.json · reaches 4 token(s)*

> derived candidate described a compound (昼ごはん) instead of glossing the lemma

Context splits declared in the ruling row (inherit its verdict):

- `126412` → **dia (período diurno)** — 昼も夜も、たくさんの車がこのハイウェーを高速で通過する。

Where it landed:

- `126412`#0 *ruling-context* → dia (período diurno) — 昼も夜も、たくさんの車がこのハイウェーを高速で通過する。
- `216769`#3 *ruling* → almoço, meio-dia; dia (período diurno) — さて、お昼にしましょう。
- `98124`#4 *ruling* → almoço, meio-dia; dia (período diurno) — 彼らはお昼をすませてから出かけた。
- `1483518`#3 *ruling* → almoço, meio-dia; dia (período diurno) — 私は毎日昼に弁当を食べます。

### 4. 着る · verb → **vestir, usar (roupa)**  `[v]`

*rulings-03.json · reaches 5 token(s)*

> 10704622 is 恩に着る.

Context splits declared in the ruling row (inherit its verdict):

- `10704622` → **ser grato** — 恩に着るよ。

Where it landed:

- `92152`#5 *ruling* → vestir, usar (roupa) — 彼女はたとえ何を着てもかわいらしい。
- `126603`#0 *ruling* → vestir, usar (roupa) — 着るものを作るのに我々は、布を使う。
- `10704622`#2 *ruling-context* → ser grato — 恩に着るよ。
- `90081`#8 *ruling* → vestir, usar (roupa) — 彼女は豪華な絹の服を着ていた。
- … and 1 more

### 5. 欠ける · verb → **faltar, carecer de**  `[v]`

*rulings-03.json · reaches 5 token(s)*

> four of five are 〜に欠けている ('faltar'); the derived registry sense[0] ('estar lascado') fits only 11041835.

Context splits declared in the ruling row (inherit its verdict):

- `11041835` → **lascar-se** — 歯が欠けました。

Where it landed:

- `118779`#6 *ruling* → faltar, carecer de — 彼には道徳観念が欠けている。
- `88630`#4 *ruling* → faltar, carecer de — 彼女は常識に欠けている。
- `11041835`#2 *ruling-context* → lascar-se — 歯が欠けました。
- `118735`#5 *ruling* → faltar, carecer de — 彼には勇気が欠けている。
- … and 1 more

### 6. 点 · noun → **ponto, aspecto**  `[v]`

*rulings-03.json · reaches 5 token(s)*

> no context here is the 'nota' sense the derived gloss carried; 75844 (何点か) is the counter for items.

Context splits declared in the ruling row (inherit its verdict):

- `75844` → **itens (contador)** — 同じような品がまだ何点かありますよ。

Where it landed:

- `218643`#6 *ruling* → ponto, aspecto — これはあれより有利な点がたくさんある。
- `220404`#1 *ruling* → ponto, aspecto — この点で私は彼に劣る。
- `75844`#7 *ruling-context* → itens (contador) — 同じような品がまだ何点かありますよ。
- `170482`#5 *ruling* → ponto, aspecto — 最初に議論すべき点は、この地域に差別が存在したかどうかということである。
- … and 1 more

### 7. 面倒 · noun → **incômodo; complicação; (～をみる) cuidar de**  `[c]`

*rulings-07.json · reaches 3 token(s)*

> One occurrence is 面倒をみる = 'cuidar de'.

Context splits declared in the ruling row (inherit its verdict):

- `88110` → **cuidado; zelo** — 彼女は息子の面倒をみた。

Where it landed:

- `88110`#4 *ruling-context* → cuidado; zelo — 彼女は息子の面倒をみた。
- `80195`#0 *ruling* → incômodo; complicação; (～をみる) cuidar de — 面倒なことになるよ。
- `117697`#6 *ruling* → incômodo; complicação; (～をみる) cuidar de — 彼の欠席で事が面倒になる。

### 8. 除く · verb → **remover, tirar**  `[v]`

*rulings-08.json · reaches 2 token(s)*

> 苦痛を除く é remover; 日曜を除いて é a exceção.

Context splits declared in the ruling row (inherit its verdict):

- `101435` → **exceto, fora** — 彼は日曜を除いて毎日働く。

Where it landed:

- `101435`#4 *ruling-context* → exceto, fora — 彼は日曜を除いて毎日働く。
- `190768`#6 *ruling* → remover, tirar — 医者は彼の苦痛を除いてやった。

### 9. 降る · verb → **cair (chuva, neve)**  `[v]`

*rulings-02.json · reaches 8 token(s)*

Where it landed:

- `191278`#16 *ruling* → cair (chuva, neve) — 暗くなりかけてきた、その上悪い事には、雨が降り出した。
- `203526`#3 *ruling* → cair (chuva, neve) — たとえ雨が降っても、私は出発する。
- `193931`#4 *ruling* → cair (chuva, neve) — もしあした雨が降ったとしてもピクニックに行きますか。
- `235264`#7 *ruling* → cair (chuva, neve) — ３日連続して雨が降った。
- … and 4 more

### 10. 誘う · verb → **convidar; chamar (para sair)**  `[v]`

*rulings-05.json · reaches 4 token(s)*

Where it landed:

- `119258`#13 *ruling* → convidar; chamar (para sair) — 彼とその連れはいっしょに来ないかと私を誘った。
- `10553304`#2 *ruling* → convidar; chamar (para sair) — 彼女を誘ったよ。
- `172084`#2 *ruling* → convidar; chamar (para sair) — 今度また誘ってよ。
- `12702883`#2 *ruling* → convidar; chamar (para sair) — トランプに誘われた。

### 11. 承認 · noun → **aprovar; reconhecer**  `[v]`

*rulings-07.json · reaches 3 token(s)*

Context splits declared in the ruling row (inherit its verdict):

- `122506` → **reconhecer; admitir** — 日本はその国の新しい政府を承認した。

Where it landed:

- `1483686`#3 *ruling* → aprovar; reconhecer — その提案を承認します。
- `176435`#3 *ruling* → aprovar; reconhecer — 計画はそっくり承認された。
- `122506`#8 *ruling-context* → reconhecer; admitir — 日本はその国の新しい政府を承認した。

### 12. 倒す · verb → **derrubar**  `[v]`

*rulings-08.json · reaches 2 token(s)*

> 政府が倒された é derrubar; 背を倒す é reclinar.

Context splits declared in the ruling row (inherit its verdict):

- `170837` → **reclinar, abaixar** — 座席の背を倒してもいいですか。

Where it landed:

- `143078`#2 *ruling* → derrubar — 政府は倒された。
- `170837`#4 *ruling-context* → reclinar, abaixar — 座席の背を倒してもいいですか。

### 13. 休み · noun → **folga, descanso**  `[v]`

*rulings-09.json · reaches 1 token(s)*

Where it landed:

- `2085672`#0 *ruling* → folga, descanso — 休みを取ることをお薦めします。

### 14. コーチ · noun → **treinador; técnico**  `[v]`

*rulings-04.json · reaches 4 token(s)*

Where it landed:

- `192923`#1 *ruling* → treinador; técnico — よいコーチがこのチームを指導している。
- `213215`#1 *ruling* → treinador; técnico — そのコーチが彼を名選手にした。
- `92068`#9 *ruling* → treinador; técnico — 彼女はテニスが好きで、テニスのコーチになった。
- `139428`#7 *ruling* → treinador; técnico — そして、私があなた達のコーチです。

### 15. 一人 · noun → **uma pessoa, sozinho**  `[v]`

*rulings-02.json · reaches 7 token(s)*

Where it landed:

- `152201`#6 *ruling* → uma pessoa, sozinho — 私もまた、議員の一人です。
- `109980`#2 *ruling* → uma pessoa, sozinho — 彼は一人っきりである。
- `149092`#3 *ruling* → uma pessoa, sozinho — 車には一人分の空きがあった。
- `109964`#2 *ruling* → uma pessoa, sozinho — 彼は一人で暮らしている。
- … and 3 more

### 16. せい · noun → **culpa, causa**  `[v]`

*rulings-08.json · reaches 2 token(s)*

> O registro trouxe 背 (estatura). Nas duas frases é 〜せいで e 〜せいか, causa negativa.

Where it landed:

- `426898`#3 *ruling* → culpa, causa — 道路混雑のせいで私は遅れました。
- `144889`#4 *ruling* → culpa, causa — 神経を使ったせいか胃が痛いです。

### 17. 不注意 · noun → **descuido, falta de atenção**  `[v]`

*rulings-09.json · reaches 1 token(s)*

Where it landed:

- `150815`#2 *ruling* → descuido, falta de atenção — 事故は不注意から生じる。

### 18. 冷える · verb → **esfriar, ficar frio**  `[v]`

*rulings-10.json · reaches 1 token(s)*

Where it landed:

- `170869`#10 *ruling* → esfriar, ficar frio — 砂漠の砂は夜になると急速に冷える。

### 19. 仏 · noun → **Buda**  `[v]`

*rulings-07.json · reaches 3 token(s)*

> Proper noun; capital kept on purpose.

Where it landed:

- `230707`#3 *ruling* → Buda — あの人は仏のような人だ。
- `127077`#3 *ruling* → Buda — 知らぬが仏。
- `194047`#3 *ruling* → Buda — もう神も仏もない。

### 20. その · adnominal → **esse, aquele**  `[v]`

*rulings-01.json · reaches 297 token(s)*

> A derivação fixou só 'aquele', mas os exemplos alternam entre referência a algo do contexto ('essa criança', 210186) e algo distante. A dupla cobre os dois; o banco já usa esse par.

Where it landed:

- `222251`#8 *ruling* → esse, aquele — この靴は値段が高いし、その上、小さすぎる。
- `209336`#0 *ruling* → esse, aquele — その女性は悲しげで、その上疲れているようだった。
- `209336`#7 *ruling* → esse, aquele — その女性は悲しげで、その上疲れているようだった。
- `191278`#7 *ruling* → esse, aquele — 暗くなりかけてきた、その上悪い事には、雨が降り出した。
- … and 293 more

---

Artifact: `research/derived/mined_layerb_n3/batch-01..29.json` + `_summary.json`.
Nothing under `corpus/`, `course/` or `db/` was written; no ingest was run.
