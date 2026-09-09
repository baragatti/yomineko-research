# W20 — kanji practice APPLY report

**Unit:** APP_PLAN §6 step 5 — "W20 kanji apply: 899 exercises into DB + lessons + bodies".
**Input:** `research/derived/pending/practice_kanji_exercises.json` (899 rows / 178 lessons), authored
and verified by the W20 kanji campaign (`research/reports/w20_kanji_authoring_report.md`).
**Result:** all 899 applied, 0 held. Full gate green. Nothing committed (this run changed no git state).

## Ground rules this run held itself to

- Exercise CONTENT is verified and was never edited. A row that could not be applied against today's
  tree would have been **HELD** and listed; none was.
- Lesson PROSE does not move. The only body change is one `<exercise ref="…"/>` node per row.
- Both layers through one idempotent applier; the table moved `pending/` → `repairs/` and is
  registered in `validate_repairs_applied.py`.

## 1. Pre-flight against today's tree — 899 APPLY, 0 HELD

W09 / W11 / W12 / W15 / W21 all landed after this table was authored, so every row was re-checked
against the CURRENT export before anything was written. Per row:

| check | result |
|---|---|
| the lesson still exists in `course/` and in `research/derived/lessons/` | 899 / 899 |
| every kanji the row targets still resolves to an exported kanji record | 969 target refs, all resolve |
| at least one targeted kanji is still **unlocked by that lesson** | 899 / 899 (0 rows lost their unlock) |
| every Japanese run in the answer key — **distractors included** — is inside the lesson's `cumulative_known_set` | 0 violations |
| every kanji mentioned in a prompt is one the lesson has taught | 0 violations |
| answer-key shape against `validate_exercise_contracts` (choices unique + `correct` among them, production `text` in `accept`, cloze filler not the blanked sentence, matching left column unique) | 0 violations |
| prompt / explanation are non-blank `{"pt-BR": …}` with balanced brackets | 0 violations |
| prose fields lacking terminal punctuation (`NO_TERMINAL_CEILING = 171`, a ratchet) | **0 added** |
| per **(lesson, kanji)**: the block puts the character on an answer surface | 0 gaps |

Two corrections I made to my own pre-flight rules rather than to the rows, both recorded because a
naive reading of them produces false holds:

- **Coverage is per (lesson, kanji), not per row.** A reading MCQ (answer いち) and its production
  twin (answer 一) are one pair; only the pair has to put the character on an answer surface, which
  is exactly how `validate_practice_coverage` measures it. Measuring per row reported 218 phantom
  failures.
- **A single-character Japanese run is a MENTION of a kanji, not a word.** Feeding 学 to
  `PassageGate` asks "is 学 a known WORD here", which is false for nearly every kanji quoted in a
  prompt. Single-character runs are checked against the lesson's cks *kanji* set instead. The naive
  rule reported 370 phantom failures.

Three findings that are real and are handled as bookkeeping, not as content edits:

1. **Six ids collided.** Three lessons gained an exercise after this table was authored — W11a's
   homograph practice items `ex:n5-passado-05-7` (どなた), `ex:n5-particulas-lugar-02-6` (側) and
   `ex:n4-condicionais-01-6` (止める). The six authored ids in those lessons are shifted by one so
   they still continue the lesson's own numbering. The mapping is data, in the table's new
   `apply_id_remap` block, with the reason on each entry. No other id moved; the 8 `*-kanji-exame-*`
   lessons have no exercises at all, so their `-1…-n` numbering is already correct.
2. **46 rows name their target as a bare character** (`"間"`) instead of `"kanji:間"`. Normalised on
   read; the table is left as authored.
3. **14 rows carry a passenger target** — a kanji the answer also credits but that this lesson does
   not unlock (it is taught elsewhere). Expected: the authoring report lists 15 co-credited
   passengers. They are credited where they are unlocked, not here.

## 2. Apply — 899 exercises, 178 lessons, both layers

`scripts/apply_practice_exercises.py` (new). One run, one write path:

- **DB** `exercise` rows with the lesson's own `ex:<lesson>-<n>` scheme continuing its numbering
  (`ord` = max + 1), `needs_review = 1`, prompt and explanation into `localized_text` with
  `layer = "C"`.
- **Authoring layer** `research/derived/lessons/<slug>.json` — the same record appended to
  `exercises[]` in the shape those files already use (`slug, type, prompt, answer, explanation,
  sentence_refs, item_refs`).
- **Body** one `<exercise ref="…"/>` node per exercise, appended after the lesson's LAST existing
  node, in the separator style that lesson already uses (measured across 322 lessons: 1,175 gaps are
  a newline, 75 are nothing, and the split is per lesson — so the style is read off the lesson, not
  imposed). The eight `*-kanji-exame-*` lessons have no practice block at all; for them the nodes go
  immediately before the closing `<checklist>`, which is where their practice would have been. **No
  heading and no prose was added**, deliberately.
- **Exemptions** pruned in the same run (§3).

Counts: **899 inserted, 899 body nodes, 0 re-asserted, 0 problems.** Second run: **0 changes**
(idempotent). Exit 0 both times.

**Prose proof.** Every one of the 322 exported lesson records was compared with its pre-apply state:
with `<exercise ref>` nodes stripped from both sides, **0 bodies differ**; **0 lessons' rendered `.md`
prose differs** above the `## Exercícios` section; **no lesson field other than `body` and
`exercises[]` changed**; net nodes added **899**. The comparison is against the pre-apply working
tree rather than `git HEAD` because HEAD does not yet carry the uncommitted W15/W21 work this tree
already holds — a HEAD diff would attribute their reading lines and `needs` edges to this unit.

### Provenance — one deviation, stated

The rows are Layer C, `ai_generated`, `needs_review`. The claim is recorded in the table's
`provenance` header and as `needs_review = 1` on every inserted DB row — **not** as per-exercise
fields in the export. Reason: the `exercise` entity has no provenance columns and the exported
exercise object has no provenance fields at all today, and `validate_provenance_json` rule (e)/(g) is
all-or-nothing per entity — a field on ANY sub-record of `lesson.exercises` is expected on ALL of
them. Stamping these 899 and not the 1,564 that predate them fails the gate; stamping all 2,463 is a
backfill over content this campaign did not author, i.e. a different unit. Flagged for the plan.

## 3. Practice exemptions — 5 dropped, 3 kept

`course/practice_exemptions.json` states its own rule: it documents the
"at least one retrieval and one production" rule of `validate_exercise_contracts`, and "an entry that
matches no lesson, or **whose lesson has since gained practice**, is itself a failure". So an exempt
lesson this table gives BOTH kinds to loses its entry; one it deliberately gives retrieval only keeps
it, because dropping that one trips the same rule from the other side. The membership is in the table
(`exemptions.drop` / `.keep`) and the applier re-derives it from the rows before touching the file.

| lesson | rows applied | retrieval | production | decision |
|---|---:|---:|---:|---|
| `les:n5-kanji-exame-01` | 16 | 8 | 8 | **drop** |
| `les:n5-kanji-exame-02` | 9 | 9 | 0 | keep |
| `les:n5-kanji-exame-03` | 10 | 7 | 3 | **drop** |
| `les:n4-kanji-exame-01` | 16 | 8 | 8 | **drop** |
| `les:n4-kanji-exame-02` | 9 | 9 | 0 | keep |
| `les:n4-kanji-exame-03` | 11 | 8 | 3 | **drop** |
| `les:n4-kanji-exame-04` | 16 | 8 | 8 | **drop** |
| `les:n4-kanji-exame-05` | 4 | 4 | 0 | keep |

File goes 8 entries → 3. The three that stay now render retrieval practice where they rendered none,
so their reason ("the learner is scheduled for review on material this lesson never tests") is
narrower than it was; the text was left as written, because rewriting it is a teacher's call.

## 4. `validate_practice_coverage` — the ratchet, before and after

Before is the tree as this unit found it, and it matches the frozen baseline exactly.

| level | kind | absent BEFORE | absent AFTER | delta |
|---|---|---:|---:|---|
| pre-n5 | vocab | 4 | 4 | — |
| n5 | vocab | 535 | 528 | −7 |
| n5 | **kanji** | **92** | **0** | **−92** |
| n5 | grammar | 17 | 17 | — |
| n4 | vocab | 591 | 586 | −5 |
| n4 | **kanji** | **173** | **0** | **−173** |
| n4 | grammar | 12 | 12 | — |
| n3 | vocab | 1191 | 1185 | −6 |
| n3 | **kanji** | **316** | **0** | **−316** |
| n3 | grammar | 6 | 6 | — |
| **TOTAL** | | **2937 absent / 1142 practised — 28.0%** | **2338 absent / 1741 practised — 42.7%** | **+14.7 pp** |

Kanji absent falls to the simulated **0 at every level** (92 / 173 / 316 → 0) and practised overall
goes 28.0% → **42.7%** (the plan predicted ~42.6%). **No cell grew.** The 18 vocab items that also
moved are words the new answer keys happen to ask for in the lesson that unlocks them — a side
effect of kanji practice, not a vocab campaign. Exercises counted by the gate: 1,564 → 2,463.

The baseline was re-frozen (`--write-baseline`) only after the rest of the gate was green, and the
suite was re-run against it: still green.

## 5. Replay and the rebuild manifest

`scripts/apply_practice_exercises.py` is manifest step **117**, inserted after W15's
`apply_reading_passages.py` (116) and before the family builders (now 119-121); every later step was
renumbered and the two prose cross-references to old step numbers were updated
(`rebuild_manifest.json` step 112's note, `scripts/validate/README.md` "Steps 112-118").
`step_count` 120 → 121, `enabled_count` 84 → 85.

- `validate_index_rebuildable.py --quick` — **[OK]**, 4 files checked, 4 held at the recorded bytes.
- `validate_index_rebuildable.py` (full) — **cannot run on this tree, and not because of W20.** The
  replay aborts at step **116**, `apply_reading_passages.py`: in a rebuild `build_readings.py`
  produces 130 of the 286 boxes, so most W15 rows exact-match nothing, and that applier reports a
  non-zero problem count by design ("a box that does not match the table is not rewritten").
  Reproduced with a **control manifest that does not contain the W20 step at all** — identical
  failure, same step, same message. So no byte-identical count can be quoted against the recorded
  147/790; that number is unobtainable until the step-116 replay behaviour is decided (a W15/W16
  follow-up, not this unit's to change).
- What *can* be said about step 117: with 116 disabled in a throwaway diagnostic manifest, the chain
  runs clean through the W20 step to the three exporters and compares all 790 files — the new step
  replays without error.
- **`scripts/validate/rebuild_baseline.json` is now stale for 337 of its 643 entries** — the exported
  `.json` / `.md` of the 178 lessons this unit touched. Those entries record the bytes a rebuild used
  to produce, and the rebuild now produces them with the exercises in. Re-recording needs `--record`,
  which needs a clean rebuild, which is blocked by the step-116 failure above. Left as an open item
  rather than papered over.

## 6. Full gate

`python scripts/validate/validate_all.py` → **ALL HARD VALIDATORS PASS**. Notable lines:

- `validate_exercise_contracts` — 0 FAIL, every exercise binds to its body and grades as rendered.
- `validate_practice_coverage` — 322 lessons, 2,463 exercises, 0 FAIL.
- `validate_repairs_applied` — PASS, **4,657 rows replayed clean**, 0 FAIL (899 of them this table's).
- `validate_md_views` — 322/322 lesson `.md` byte-identical to a fresh render.
- `validate_prototype_sync`, `validate_schema_generation_is_current`, `validate_unlock_ledger`,
  `validate_srs_decks`, `validate_provenance_json` — all OK.

Order run: apply → `export_course.py` → `contracts/infer_shapes.py` → `build_schemas.py` →
`build_manifest.py` → `(cd prototype && npm run sync-data)` → `validate_all.py`. `export_corpus.py`
was not needed: `git status corpus/` is clean, nothing corpus-side moved.

One environment note: `.venv` has no `jsonschema`, so running the suite with the venv interpreter
fails `validate_contracts.py` on an import. The suite is green under the system interpreter (which
`validate_all.py` uses by default; it routes only the two Sudachi gates to the venv). Pre-existing.

## 7. Replay addressing

The table is registered in `validate_repairs_applied.py` as `practice_kanji_exercises.json` →
`handle_practice_exercises`, addressed **by content, not by id**: prompt + answer is unique within a
lesson (`validate_exercise_contracts` check 4), so a row matches exactly one exported exercise or it
fails. Content addressing is deliberate — a replay keyed on the authored id would fail on the six
renumbers of §1, which are correct. Four claims per row: the lesson holds an exercise with this type,
prompt and answer; the match is unique; its `explanation` and `sentence_refs` are the row's; and the
lesson BODY references it exactly once, because an exercise no `<exercise ref>` node names is
practice the learner never sees.

## 8. Twenty applied exercises, for a human read

Stratified by (level, type), then a seeded draw.

| # | lesson / id | kanji | type | prompt (pt-BR) | answer | distractors |
|---|---|---|---|---|---|---|
| 1 | `les:n5-adjetivos-05` / `ex:n5-adjetivos-05-7` | 下 外 来 気 | matching | Ligue cada kanji novo desta lição ao seu significado. | 下=embaixo ; 外=fora ; 来=vir ; 気=espírito | — |
| 2 | `les:n4-experiencia-02` / `ex:n4-experiencia-02-7` | 楽 | production | Escreva em japonês o adjetivo que significa divertido, agradável. | 楽しい (accept: 楽しい, たのしい) | — |
| 3 | `les:n4-experiencia-02` / `ex:n4-experiencia-02-10` | 究 | production | Escreva o kanji que significa investigar até o fim, dominar um assunto. | 究 (accept: 究, きゅう) | — |
| 4 | `les:n3-causa-05` / `ex:n3-causa-05-7` | 内 | production | Escreva em japonês a expressão que significa dentro de, em até certo limite de tempo, distância ou quantidade. | 以内 (accept: 以内, いない) | — |
| 5 | `les:n5-numeros-tempo-05` / `ex:n5-numeros-tempo-05-9` | 日 | cloze | Qual é o kanji que falta na data 'dia 9' (ここのか), escrita ９＿? | 日 — ９日 | — |
| 6 | `les:n5-rotina-02` / `ex:n5-rotina-02-9` | 毎 | cloze | Qual é o kanji que falta em 'todo dia' (まいにち), escrito ＿日? | 毎 — 毎日 | — |
| 7 | `les:n4-experiencia-03` / `ex:n4-experiencia-03-7` | 病 | cloze | Qual é o kanji que falta em 'doença' (びょうき), escrita ＿気? | 病 — 病気 | — |
| 8 | `les:n4-passiva-01` / `ex:n4-passiva-01-9` | 夕 | cloze | Qual é o kanji que falta em 'fim de tarde' (ゆうがた), escrito ＿方? | 夕 — 夕方 | — |
| 9 | `les:n3-estado-01` / `ex:n3-estado-01-17` | 置 | cloze | Qual é o kanji que falta no verbo 'colocar, deixar' (おく), escrito ＿く? | 置 — 置く | — |
| 10 | `les:n3-concessao-04` / `ex:n3-concessao-04-9` | 幸 | recognition | Em 幸福 (felicidade) e 不幸 (infelicidade), o que o kanji 幸 traz? | felicidade | transportar / sofrimento / belo |
| 11 | `les:n4-volitivo-01` / `ex:n4-volitivo-01-7` | 元 別 知 考 | matching | Relacione cada kanji novo desta lição ao seu significado. | 元=origem, fonte ; 別=separado, diferente ; 知=saber, conhecer ; 考=pensar, considerar | — |
| 12 | `les:n3-estado-04` / `ex:n3-estado-04-14` | 断 + vocab:1478620 | production | Escreva 'julgamento, decisão' em japonês, com kanji. | 判断 (accept: 判断, はんだん) | — |
| 13 | `les:n3-conjectura-04` / `ex:n3-conjectura-04-11` | 束 | cloze | Complete com o kanji que falta: 約___ (やくそく) é 'promessa'. | 束 — 約束 | — |
| 14 | `les:n5-conectando-06` / `ex:n5-conectando-06-7` | 父 | recognition | O kanji 父 aparece em 父 e em お父さん. O que ele significa? | pai | mãe / amigo / filho |
| 15 | `les:n5-te-form-04` / `ex:n5-te-form-04-7` | 名 | production | Escreva em japonês a palavra que significa "nome" (leitura なまえ). | 名前 (accept: 名前, なまえ) | — |
| 16 | `les:n5-te-form-06` / `ex:n5-te-form-06-7` | 半 | production | Escreva em japonês a palavra que significa 'metade, meio', formada pelo kanji novo desta lição mais 分 ('parte'). | 半分 (accept: 半分, はんぶん) | — |
| 17 | `les:n5-kanji-exame-01` / `ex:n5-kanji-exame-01-1` | 会 | recognition | O kanji 会 significa: | encontrar, reunião | ver, olhar / ouvir, escutar / sair, aparecer |
| 18 | `les:n4-kanji-exame-01` / `ex:n4-kanji-exame-01-7` | 働 | recognition | Como se lê o verbo 働く, que significa 'trabalhar'? | はたらく | うごく / つくる / つかう |
| 19 | `les:n5-kanji-exame-02` / `ex:n5-kanji-exame-02-9` | 空 立 耳 花 | matching | Associe cada palavra ao seu significado em pt-BR. | 空=céu ; 立つ=ficar de pé, levantar-se ; 耳=orelha, ouvido ; 花=flor | — |
| 20 | `les:n3-enfase-02` / `ex:n3-enfase-02-6` | 余 王 類 返 | matching | Associe cada palavra ao seu significado em pt-BR. | 余分=extra, excedente ; 王子=príncipe ; 人類=humanidade, gênero humano ; 返事=resposta | — |

## 9. Not done / open

1. **Full-mode `validate_index_rebuildable`** — blocked at step 116 by W15's applier in a replay,
   pre-existing, proved with a control manifest. No byte-identical count quoted.
2. **`rebuild_baseline.json`** — 337 of 643 entries are stale after this apply; `--record` is blocked
   by (1).
3. **Per-exercise provenance in the export** — deliberately not added; see §2. Closing it means
   backfilling all 2,463 exercises, which is its own unit.
4. **Nothing was committed.** No git state was changed by this run.
5. The three kept exemption reasons still describe a lesson that "never tests" its kanji; that is no
   longer literally true (they now render retrieval practice). Rewriting a reason is a teacher call,
   so the text was left alone and is flagged here instead.
6. A stray untracked file named `50` sits at the repo root (76 KB, written 17:11). Not created by
   this unit; noted so it is not mistaken for W20 output.
