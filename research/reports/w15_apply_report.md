# W15 apply — real reading passages in both layers, plus the W16 builder rules

Plan rows: `research/reports/APP_PLAN.md` **W15** (apply) and **W16** (scoped here to code + lessons;
the bank items themselves are produced by W18's regeneration and are deliberately not produced twice).

Baseline before any change: `python scripts/validate/validate_all.py` **green**. (Run the gate with the
system interpreter. The project venv has SudachiPy but not `jsonschema`, so `validate_contracts` fails
under it; `validate_all.py` already routes the two Sudachi-only validators to the venv itself.)

---

## 1. The dissector rule — a known surface must not resolve to an unknown lemma

SudachiPy's `dictionary_form()` is a **lemma**, and a lemma can name a different registry record, at a
different JLPT level, than the surface in front of the learner:

```
surface ください   lemma くださる   ->  vocab:1184280  下さる  N4
surface ください   surface itself   ->  vocab:1184270  下さい  N5   <- what N5 lessons unlock
```

The known-set check resolved lemma-first, so every N5 passage containing てください — the ordinary
polite request at N5 — was reported as introducing an N4 word its lesson never unlocks. That is not a
fact about the passage; it is an artefact of the resolver.

**Fixed in `scripts/ingest/known_set.py`** (new; the single implementation of the gate, shared by the
apply script, the coherence validator and the exam builders) on top of
`Dissector.vocab_candidates()` (new; `scripts/ingest/dissect.py`). `_vocab_id` is untouched — the
sentence bank's lexeme linkage is correct as it stands — so the rule can only change *which tier
answers*, never which record a tier names. Three rules, all exact form lookups:

| rule | what it does | why it is safe |
|---|---|---|
| **surface tier** | candidates are lemma → surface → kana-normalised surface, first-wins per tier; the resolver takes the first candidate the known set already contains | a same-reading neighbour is never a candidate (箸 is not reachable from 橋), and when no candidate is known the word is still NEW and the passage is still held |
| **§3 numeral carve-out** | a token Sudachi tags 名詞/数詞 is not charged as a new word | `design/reading_practice.md` §3 already waived it in writing ("kana-only words, **numbers**, punctuation …"); the numbers lesson was being held for its own 二かい |
| **run rule** | when a token's own candidates are all untaught, a contiguous run of ≤4 tokens containing it that spells an exact registry form **already in the known set** credits that record instead | お\|茶 → お茶 (N5, taught) rather than 茶 (N3); 要する\|に → 要するに (N3, taught) rather than 要する (N1). The run may not cross punctuation, and it can only ever say "this longer word is one you were taught" |

Deliberately NOT done: taking *every* owner of a form. It unheld nothing and it would have credited
same-spelling records the token does not mean (間 is owned by three records, ここ/そう by several) —
`uses` is what W16 draws exam distractors from, so a missed credit is safe and a wrong credit is not.

**Test:** `scripts/validate/test_known_set_surface.py`, in `validate_all`. 12 groups, both directions:
the rescue (T1, T2), the refusal to launder when nothing is taught (T3), lemma-first order preserved
when the lemma is the taught record (T4), the same-reading plant 橋/箸 (T5), the kanji gate staying
independent (T6), no tier inventing a record (T7), the numeral carve-out (T9), the run rule (T10) and
its two refusals (T11 nothing taught, T12 a "word" spelled across a 。).

### Re-measured: which passages still fail max_new = 0

`scripts/build_reading_passage_table.py` re-derives the gate over all 286 authored passages
(`research/derived/passages/`) against the **exported** `cumulative_known_set`.

| | count |
|---|---|
| passages on disk | 286 (298 files: 12 slugs also have a superseded `read-*.json` pilot copy from the campaign's first batch, named in the table) |
| **applicable** | **282** |
| **held** | **4** |
| lessons touched | 232 |
| tokens rescued by the surface rule | 11 in 7 passages |
| tokens rescued by the run rule | 16 in 9 passages |
| §3 carve-out tokens (kana-only / numeral) | 69 |

The plan row predicted ~13 holds. The campaign's verifiers had already re-authored around most of
them (なる in `n5-adjetivos-05`, こと in `n4-oracoes-relativas-02`, なかなか in `n4-potencial-04`,
これ/それ in `n5-desu-wa-04` all pass on the current text); the ください trap is fixed by the rule;
お茶 / 要するに / 二 are fixed by the carve-out and the run rule. **Four remain, every one a
course-data gap — the gating lesson's own grammar target is built on a word the lesson never
unlocks.** They are HELD, not rewritten, and listed here for **W21b**:

| held passage | gating lesson | missing unlock | the lesson's own point |
|---|---|---|---|
| `read:n4-oracoes-relativas-03-01` | `les:n4-oracoes-relativas-03` | `vocab:1215230` 間 (N4), 4 occurrences | the lesson teaches 〜間 / 〜間に and never unlocks 間 |
| `read:n3-perspectiva-01-01` | `les:n3-perspectiva-01` | `vocab:1215790` 関する (N3), seen as 関し | the lesson teaches 〜に関して |
| `read:n3-limites-05-02` | `les:n3-limites-05` | `vocab:1610160` 対する (N3), seen as 対し | the lesson teaches 〜に対して |
| `read:n4-keigo-04-01` | `les:n4-keigo-04` | `vocab:1456130` 読み (N3), seen as 読み | お読みになる: Sudachi analyses お読み as prefix + the **noun** 読み; the lesson teaches the verb 読む (N5, in its cks) but not the nominal the lesson's own お〜になる pattern produces. Either unlock it there or the box stays selection-era |

---

## 2. The apply

`scripts/apply_reading_passages.py` (new, idempotent, `--check`), driven by the exact-match tracked
table `research/derived/repairs/reading_passages.json` and registered in the replay gate.

* **Both layers.** Authoring layer = `research/derived/passages/*.json` (the verified text) + the
  tracked table (the decision); index = `db/corpus.sqlite`; `export_readings.py` republishes
  `corpus/readings/*.json`, which is canonical.
* **Exact match.** Each row carries the `old.jp` it replaces. A box holding neither `old` nor `new` is
  skipped **loudly** and nothing is written for it; a second run reports 0 changes.
* **Tokens** are re-derived from the new `jp` through `dissect.Dissector` (the same mode-C path every
  other token stream uses) and asserted to re-concatenate to `jp`. They are *not* carried in the
  table: a derived value in a repair table is a second source of truth waiting to drift.
* **`uses` is documented as a SNAPSHOT** (W16 asked for this) — in the module docstring, in the
  applier, in the table, and in `corpus/readings/INDEX.md`. It records what *this passage's own*
  tokenisation resolved to at apply time; it is **not** a recompute from `sentence_kanji` /
  `sentence_vocab`, which grow with every later dissection pass and would push already-gated boxes out
  of their lesson's known set (the failure `apply_readings_composition_repairs.py` records). Only
  records the gating lesson already teaches are credited, so `uses` is inside the known set by
  construction and `validate_readings.py` compares like with like.
* **Layer-C provenance**: `layer: "C"`, `ai_generated: true`, `needs_review: true`,
  `source: "authored:w15-passages"`. Every box that was *not* replaced gets
  `source: "selection:sentence-bank"` in the same run — `validate_provenance_json` rule (e) expects a
  provenance field on all records of an entity once any record carries it.
* **`sentences`** (new): the box's own segmentation. Stored rather than re-derived because a quoted
  dialogue terminates every line inside 「…。」 (a plain split on 。 makes a six-line exchange look
  like one sentence) and `design/translation_style.md` §3 drops the final 。 on generated Japanese.
* **Schema**: migrations `014_reading_provenance.sql` (declares the `reading` table itself — it used
  to be created inline by `build_readings.py`, so the schema was a function of run order — plus
  `source` and `comprehension`) and `015_reading_sentences.sql`.
* **Manifest**: inserted as **step 116**, after 115 `apply_lesson_needs.py`; `apply_lesson_furigana.py`
  moved to 117 and the three family builders to 118-120 (last, as they must be). 120 steps, 84 enabled.
  The one cross-reference inside a step note was renumbered; `scripts/validate/README.md` updated.

**Lessons were not edited at all.** The `<reading ref>` tags and `reading_refs` that
`build_readings.py` wired into 235 lessons address these boxes by slug and no slug moved.

> **Rendered-text diff vs `git HEAD`: 232 lesson `.md` views changed, 282 lines, and every single
> changed line is a `> 📖` reading line** — `git diff -U0 -- 'course/**/*.md'` filtered to lines that
> are not reading lines returns nothing. The lesson prose is byte-identical; only the passage inside
> the box moved, which is the whole point of the unit.

### The one knock-on: `needs[]` had to be re-derived

`derive_needs.py` expands `<reading ref>` through the reading record's own `uses`, and its own report
says `body-reading` dominates the graph. Replacing 282 passages therefore moved the prerequisite
graph, and `validate_lesson_gating` check C4 — which re-derives the whole model on the tree being
validated — caught it immediately (461 stored-but-underived, 472 derived-but-unstored). That check
earning its keep on the first unit after it landed is the system working.

`scripts/build_needs_table.py` was re-run over the current tree and `apply_lesson_needs.py` re-applied
it: **747 → 758 edges** (derived 696 → 707), 314 lessons, graph still acyclic, re-derivation now
agrees. `apply_lesson_needs.py` gained **`--replace`** (and manifest step 115 now passes it): `needs`
is 100% derived and C4 proves it, so a disagreement is a stale table and never hand-authored work —
and without the flag a rebuild replay could not apply a changed table at all, because the authoring
sources already carry the previous run's needs.

The C2 root ratchet **shrank 8 → 7**: `les:n5-numeros-tempo-06` used to have no prerequisites because
its reading box was a concatenation of sentences drawn from its own unlocks; the authored passage that
replaced it uses words earlier lessons teach, so the lesson now has real prerequisites and its
exemption entry is deleted.

Side effect worth recording: the 11 `needs` notes that named 琴 where the lesson means こと (the
homograph W21's report left open) are **down to 4**, because seven of them came from the old
concatenated passages.

**What changed in the course tier, exactly:** 233 lesson `.json` files, and the ONLY field that
differs in any of them is `needs`; 44 `topic.json` / index files, which carry the same needs as a
derived summary; 232 `.md` views, reading lines only. No `body`, no exercise, no prose.

---

## 3. The coherence check became a validator

`scripts/validate/validate_reading_coherence.py`, in `validate_all`. Coherence is not decidable from
text, so the validator is explicit about which side of that line each check falls on.

**HARD — string equality and set containment only.** H1 an authored passage has 3-6 sentences and its
`sentences` re-concatenate to `jp`; H2 the token stream re-concatenates to `jp`; H3 `uses` is inside
the gating lesson's `cumulative_known_set`; H4 a **non-dialogue** passage does not mix first-person
pronouns.

**ADVISORY — heuristics over surface morphology, ratcheted, never gating.** A1 topic drift (a sentence
sharing no content word and no kanji with anything before it); A2 tense drift (>1 past/non-past
switch); A3 register drift (mixed です・ます and plain endings); A4 a dialogue mixing pronouns. Each is
a review signal: Japanese drops the subject once it is established, so a perfectly coherent line like
「また後で電話するね。」 shares nothing lexically with its own paragraph; a passage that narrates
yesterday and comments on today legitimately switches tense; a quotation inside a polite text
legitimately mixes endings. The reasons are written into the baseline file, not just here.

**Plant proof** (`--selftest`): a throwaway tree carrying a **copy of the validator** and its own
corpus + course, one plant per check. 7 plants, 7 caught, control green. The copy is the point — a
validator that resolves ROOT from `__file__` and runs from the repo reads the repo's data and reports
green whatever the fixture says.

**Measured with the same validator, before and after** (before = `git HEAD`'s readings in a scratch
tree):

| | hard FAIL | topic drift | tense drift | register drift |
|---|---|---|---|---|
| the concatenations (HEAD) | 3 | 814 | 86 | 201 |
| **after the apply** | **0** | **670** | 102 | **11** |

Register drift falls by 95%: the concatenations glued a polite sentence to a plain one 201 times.
Tense drift rises by 16 because the authored passages tell small stories that move between narration
and comment — which is exactly why A2 is advisory. Baseline frozen at the post-apply numbers in
`scripts/validate/reading_coherence_baseline.json` (shrink-only).

---

## 4. Pointers: nothing dangles

`reading_comp` (286 items) and `text_grammar` reference their passage by `read:` slug, and every slug
still exists — the passages were **replaced in place**, not renumbered — so **no pointer dangles** and
no reference had to be repaired.

What went stale is the **content** those items copied out of the old passages. The two types are not
in the same position, and the difference decides what this unit did:

* **`reading_comp` is AUTHORED.** Its question is a claim about a text, and nothing mechanical can
  rewrite it. Every one of the 286 was written about a concatenation that is gone. Left untouched;
  it is W18's, and §5.3 hands it the exact list.
* **`text_grammar` is DERIVED.** Its stem IS its passage with one form blanked, and
  `validate_exam_banks` check I ("filled stem is not the passage") is a HARD gate that 184 items
  failed the moment the passages changed. A deterministic projection of changed data has to be
  recomputed — the same class as `reading.tokens`. Regenerated; see §5.3 for the deviation and the
  two extra rules it forced.

---

## 5. W16, scoped to code + lessons

### 5.1 `text_grammar` blanks are cut at Sudachi token boundaries

`build_exam_banks.py` blanked a grammar form with `jp.replace(form, "（　）", 1)`, which cuts wherever
the characters happen to line up. **Measured on the 286 current passages, the old rule would cut inside
a word in 59 of them**: `ても` out of とても (「子どもはと（　）よろこんでくれた」), `せいで` out of
れいせいで, `こと` out of ことば, `かけ` out of 出かけた. A stem blanked mid-word is not a grammar
question — the learner is repairing a typo, and no whole-form distractor can fit the hole.

`token_spans()` + `boundary_occurrence()` now require the form to **begin at a token start and end at
a token end**; the blank replaces exactly that span. `build_exam_banks.py` also gained `--out DIR`
(prototype mode) and now emits the `layer` / `ai_generated` / `needs_review` provenance for
`text_grammar` that the **disabled** `migrate_exam_banks_p7.py` used to stamp after the fact — a
regenerated bank has to carry it, because that migration cannot run in a rebuild.

### 5.2 `reading_comp` is derived from the real passage

The old builder **never read a passage**: it checked that the `read:` slug resolved, checked the shape
of the options, and shipped. Four guards now read the passage and its gating lesson:

* **P1 about the passage** — a content word of the question occurs in the passage.
* **P2 level-gated** — every kanji in question, correct and distractors is in the gating lesson's cks.
* **P3 distractors from the passage's own known set** — every content word of every option resolves,
  through the same `known_set` gate, inside that set (kana, numerals and unlinked words are the §3
  carve-out here too).
* **P4 not scannable** — reject an item whose correct answer is the only option printed verbatim in
  the passage.

P2/P3 are gated to the passage's **own** known set, which is stricter than W17's exam rule (the last
lesson of the level) and is the task's rule; the same item is also shown inside that lesson's reading
box, where nothing above the lesson may appear. The looser gate is **measured alongside** so W17 can
see what the strict choice costs: **87** of the 157 P2/P3 drops would pass under the level-end cks.

### 5.3 Prototype run, and the one thing that had to be regenerated

Two runs into scratch directories. Comparing against the committed banks is not conclusive on its
own — those banks are stale against the current corpus for reasons that predate this unit (grammar
merges, level repairs, and the `vocab` slug + provenance keys the **disabled**
`migrate_exam_banks_p7.py` stamped in afterwards). So the builders were also run at **`git HEAD`
against the same database**, which isolates the W16 change exactly:

| comparison | result |
|---|---|
| old vs new builder, all deterministic banks **except** `text_grammar` | **identical, every file** — the W16 change touches `text_grammar` only |
| old vs new `text_grammar` | 277 → 231 items: **137 stems re-cut**, 46 dropped (no form that is level-readable, token-aligned and printed exactly once), 0 added |
| old vs new `reading_comp` | 286 → 36: **250 dropped by the new guards** (P1 204, P2/P3 157, P4 3 — an item can fail more than one), 0 added, **0 surviving items whose fields changed** |

**The deviation, stated plainly.** `text_grammar` had to be regenerated in place, and the three
`corpus/exam_banks/*_text_grammar.json` files are the only bank files this unit wrote. Not by choice:
a `tg` stem is a **copy** of its passage with one form blanked, and `validate_exam_banks` check I
("filled stem is not the passage") is a HARD gate — 184 items failed it the moment the passages
changed. That type is a deterministic projection of the passage, the same class of artefact as
`reading.tokens`, not authored content; leaving it would have left the gate red, and deleting the
items would have thrown away content the builder can recompute exactly. `reading_comp` — which IS
authored — was **not** touched, and the other 36 bank files were not written.

Two further rules the regeneration forced, both real defects the old concatenations hid:

* **the form must appear exactly once.** A W15 passage is *about* its lesson's grammar target and
  therefore repeats it, so blanking the first occurrence left the answer printed two lines down.
  15 items failed check C ("stem prints its own answer outside the blank").
* **every printed form must be readable at the level.** `grammar_point.forms_json` carries grammar
  METALANGUAGE (自動詞, 命令形, 受身形, が必要), which became distractors printing 詞 / 形 / 受 / 必
  in an N4 paper — `validate_exam_level_gate`'s n4 ceiling went 8 → 15. They are also poor
  distractors on their own terms: a grammar-term label never fits a sentence blank. Filtering the
  form pool to level-readable forms put the gate back at **ALL OK, ceiling untouched**.

Bank counts after: `text_grammar` n5 37 / n4 72 / n3 122 (was 43 / 87 / 138 before the two rules,
277 in total before the unit); every other bank file byte-identical. `validate_exam_banks`
**6,081 items in 40 banks, ALL OK**; `validate_exam_level_gate` ALL OK; stem collisions held at 94.

**Tests:** `scripts/validate/test_exam_builders.py`, in `validate_all` — 9 checks over
`boundary_occurrence` (ても inside とても, かけ inside 出かけた, こと inside ことば all refused; a real
token-aligned form found at the right offset and blanked exactly) and over the rc guards
(`question_is_about`, `option_problems` for an untaught kanji and an untaught word).

### 5.4 The in-lesson box asks its comprehension question

The authored question lives **once**, in `corpus/exam_banks/<level>_reading_comp.json`, one item per
`read:` slug. `reading.comprehension` holds the **pointer** plus `about_current_text`; the exporter
resolves the question, the correct answer and the sorted options into `corpus/readings/*.json` **only
when that flag is true**, and `renderReading` in `prototype/app/lib/render-body.server.ts` renders a
question block (stem, options, `<details>` "Ver resposta") only when it is present.

`about_current_text` is **false for the 282 boxes this apply rewrote**, because their question was
written about the concatenation that is gone. So **4 boxes ask a question today and 282 are wired and
inert** — that is the honest state, and it is deliberate: shipping a question about a passage the
learner is not reading is a content defect, not a feature. Because the reading record stores the
pointer and not the string, **W18 regenerating the bank over the new passages turns all of them on
with no second apply and no duplicated content.**

---

## 6. Counts

| | |
|---|---|
| passages applied | **282** of 286 |
| passages held (course-data; listed in §1 for W21b) | **4** |
| lessons whose reading box changed | **232** (282 boxes) |
| lesson `.json` files changed | 233, and `needs` is the ONLY field that differs in any of them |
| lesson prose changed | **none** — 232 `.md` views moved, every changed line a `> 📖` reading line |
| tokens written | **20,010** across the 282 boxes, re-derived mode C, each stream asserted to re-concatenate to its `jp` |
| sentences recorded | 1,534 authored segments (3-6 per passage) |
| `uses` credited | 7,091 vocab + 5,100 kanji references, all inside the gating lesson's cks |
| tokens the surface rule rescued / the run rule rescued / §3 carved out | 11 / 16 / 69 |
| coherence, hard failures | 3 → **0** |
| coherence, advisory flags | topic 814 → 670, tense 86 → 102, register 201 → **11** |
| `needs[]` edges | 747 → **758**; root exemptions 8 → **7**; notes naming 琴 wrongly 11 → **4** |
| rc questions live in a lesson box | **4** (282 wired, inert until W18) |
| exam banks written | 3 files (`*_text_grammar.json`), forced by a hard gate — see §5.3. The other 37 untouched |
| `text_grammar` | 277 → **231** items: 137 stems re-cut at a token boundary, 46 dropped |
| gate | **`validate_all.py` green** — 59 validators, 57 hard, **3 of them new** (`validate_reading_coherence`, `test_known_set_surface`, `test_exam_builders`) |

### 15 applied passages, for a human read

| # | gating lesson | first sentence | pt-BR (first) | comprehension question |
|---|---|---|---|---|
| 1 | `les:n3-causa-01` | 昨日は朝から雨が強くて、電車がおくれました。 | Ontem choveu forte desde cedo e o trem atrasou | `rc:n3:n3-causa-01-01` pending W18 (asks about the replaced text: “どうして雨にぬれなかったのか。”) |
| 2 | `les:n3-concessao-06` | 先週、山の近くの村へ行った。 | Semana passada fui até um vilarejo perto da montanha | `rc:n3:n3-concessao-06-01` pending W18 (asks about the replaced text: “ストーブが消えたとき、この人はどうしたか。”) |
| 3 | `les:n3-conjectura-03` | あの二人は姉妹みたいだ。 | Aquelas duas parecem irmãs | `rc:n3:n3-conjectura-03-01` pending W18 (asks about the replaced text: “外の様子について、何と言っていますか。”) |
| 4 | `les:n3-deveres-01` | テーブルの上に、新しいおかしを買っといたよ。 | Comprei um doce novo e deixei em cima da mesa | `rc:n3:n3-deveres-01-01` pending W18 (asks about the replaced text: “この人は何語で言ってみると言っているか。”) |
| 5 | `les:n3-estado-01` | 今、台所でパンをやいています。 | Agora estou assando pão na cozinha | `rc:n3:n3-estado-01-01` pending W18 (asks about the replaced text: “この人はお昼ご飯をどのぐらい作っているか。”) |
| 6 | `les:n3-estrutura-05` | 先月、新しい薬が発見されたと発表された。 | No mês passado anunciaram que um remédio novo foi descoberto | `rc:n3:n3-estrutura-05-01` pending W18 (asks about the replaced text: “少年は何をしたか。”) |
| 7 | `les:n3-limites-04` | 合格したと聞いて、どんなにうれしかったことか。 | Quando ouvi que tinha passado, como fiquei feliz! Até este dia, quanto tempo eu esperei! Mas, mesmo estudando bastante, nem sempre o resultado aparece | `rc:n3:n3-limites-04-01` pending W18 (asks about the replaced text: “「彼」について、正しいものはどれか。”) |
| 8 | `les:n3-relato-02` | 姉から電話があった。 | Minha irmã ligou | `rc:n3:n3-relato-02-01` pending W18 (asks about the replaced text: “姉は「私」に何を頼んだか。”) |
| 9 | `les:n3-tempo-06` | 新しい仕事についてから、毎日がつぎつぎにすぎていく。 | Desde que entrei no emprego novo, os dias passam um atrás do outro | `rc:n3:n3-tempo-06-01` pending W18 (asks about the replaced text: “この文章で、してはいけないと言っていることは何か。”) |
| 10 | `les:n4-condicionais-03` | 毎日少しべんきょうすれば、はやく上手になります。 | Se você estudar um pouquinho todo dia, logo fica bom nisso | `rc:n4:n4-condicionais-03-01` pending W18 (asks about the replaced text: “「私」は何になりたいと言っていますか。”) |
| 11 | `les:n4-experiencia-02` | 毎日、かんじのれんしゅうをしています。 | Todo dia eu treino kanji | `rc:n4:n4-experiencia-02-01` pending W18 (asks about the replaced text: “先生はどうしましたか。”) |
| 12 | `les:n4-obrigacao-02` | 来週、学校で試験があります。 | Semana que vem tem prova na escola | `rc:n4:n4-obrigacao-02-01` pending W18 (asks about the replaced text: “この人は、話しているとき、何をしてほしいと言っていますか。”) |
| 13 | `les:n4-revisao-01` | 母が作ったカレーはとてもおいしい。 | O curry que a minha mãe fez é muito bom | `rc:n4:n4-revisao-01-01` pending W18 (asks about the replaced text: “食べ物について、何と言っているか。”) |
| 14 | `les:n4-volitivo-03` | 今年のなつは海へ行こうと思っています。 | Neste verão estou pensando em ir para o mar | `rc:n4:n4-volitivo-03-01` pending W18 (asks about the replaced text: “二つの本について、正しいものはどれか。”) |
| 15 | `les:n5-convites-05` | まいあさ七時におきます。 | Todo dia acordo às sete da manhã | `rc:n5:n5-convites-05-01` pending W18 (asks about the replaced text: “この人はどこへ行くところでしたか。”) |

## 7. Not done, and why

* **The 4 held passages** need an unlock moved or added in their gating lesson — **W21b**. A passage
  is verified Layer C and is never rewritten to fit a gap in the course data.
* **`reading_comp` was not regenerated.** 250 of the 286 questions no longer describe the text they
  are printed under, and §5.3 is W18's exact work list. The 36 that survive every guard are the only
  ones the builder would keep today.
* **282 reading boxes are wired for their question and inert**, because `about_current_text` is false
  for every box this apply rewrote. W18 flips them with no second apply.
* **The other deterministic banks still lack the `vocab` slug beside `vocab_id` and the p7 provenance
  keys** — the committed banks carry them only because a now-disabled migration stamped them in
  afterwards, so a regenerated bank would lose them. **W17.** Named here because the prototype diff
  surfaced it; W16 fixed it for `text_grammar` only, the type it owns.
* **8 rows of `corpus/exam_banks/INDEX.md` were already stale at HEAD** (n4_context_fill,
  n4_kanji_reading, n4_orthography, n4_paraphrase, n4_usage, n5_kanji_reading, n5_orthography,
  removed_items). Left alone: only the three `text_grammar` rows this unit changed were updated, so
  the pre-existing drift stays visible for W18 rather than being silently absorbed.
* **A1 topic drift (670) is noisy by construction** (Japanese drops the subject once it is
  established). It is a teacher-review signal with a shrink-only ratchet, not a quality claim.
* **`read:n4-keigo-04-01`'s hold is partly a design question**, not only a missing unlock: お読み is
  prefix + the **noun** 読み, and whether a keigo lesson should unlock that nominal is a course call.
  Recorded as such rather than silently resolved.
* **One projection contract moved with the feature:** `slimReading` in both
  `prototype/scripts/sync-data.mjs` and `scripts/validate/validate_prototype_sync.py` now carries
  `comprehension`, and only in its resolved form — a box that holds the pointer alone does not ship
  its `item`/flag to the app. The two are edited together on purpose: the validator re-derives the
  projection rather than trusting it, which is exactly why it failed the first time and had to.
* **Nothing was committed.** The unit ran under an explicit no-git-state instruction; the working tree
  carries the change and the gate is green on it.
