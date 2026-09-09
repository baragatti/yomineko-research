# W21 apply — `needs[]` written, the linearity gate made real, furigana derived

Unit W21 of [`APP_PLAN.md`](APP_PLAN.md) §6 step 3. The derivation half landed in an earlier session
(`scripts/derive_needs.py` -> `research/derived/needs_edges.json`, report
[`w21_needs_report.md`](w21_needs_report.md)). This is the APPLY half: write the edges into both
layers, turn the advisory linearity notice into four hard checks, and put a reading on every
lesson-body `<jp>` span a script can derive one for.

**The constraint that shapes everything below:** lesson PROSE does not change. This unit adds
structure (`needs[]`) and one attribute (`reading` on `<jp>`) and nothing else, and it proves it by
rendering every lesson to text before and after and diffing (§5).

**Result: the full gate is green.** 322 of 322 lessons render byte-identical text against
`git HEAD`; 319 changed structurally.

---

## 1. What was measured before anything was written

| measurement | number |
|---|---:|
| lessons | 322 |
| prerequisite edges derived on the CURRENT tree (transitive reduction) | 696 |
| ... on the tree the committed artifact was derived from | 700 |
| lessons that derive as roots | 60 |
| ... of which pre-N5 (the kana strand references only its own family) | 41 |
| ... of which review / kanji-exame lessons past course position 100 | 11 |
| `<jp>` spans in lesson bodies | 10,496 |
| ... already carrying a `reading` | 3,971 |
| ... carrying kanji and NO reading (the A7 defect) | **875** |
| ... of those, spans inside a `<vocab ref>` chip | **0** (structurally impossible: `<vocab>` is an empty element) |

**The committed derivation was four edges stale.** `derive_needs.py` re-run on the current tree
gives 696 reduced edges, not the 700 the committed `needs_edges.json` recorded: W11 and W12 landed
between the two runs. The artifact and its report are regenerated here, and the number the gate now
enforces is the one the tree produces today, which is the entire point of check C4 below.

---

## 2. `needs[]`

### 2.1 What was written

747 edges over 313 lessons, in both layers, through one idempotent apply script and one exact-match
tracked table.

| origin | edges | where they come from |
|---|---:|---|
| `derived` | 696 | `scripts/derive_needs.py`'s transitive reduction, copied unchanged |
| `kana-chain` | 40 | rule (below) |
| `review-chain` | 11 | rule (below) |

- table: `research/derived/repairs/lesson_needs.json` (`scripts/build_needs_table.py`)
- apply: `scripts/apply_lesson_needs.py` — DB `lesson_needs` + `research/derived/lessons/<slug>.json`
- schema: migration `013_lesson_needs_note.sql` gives `lesson_needs` the `note` column
  `design/lesson_schema.md` has specified since the P6 freeze; `load_lessons.py` was silently
  dropping the field on ingest and `export_course.py` could not publish it. Both now carry it.
- manifest: step **115**, after 114 (`apply_orthographic_relinks`) and before the family builders,
  which moved from 115-117 to **117-119**. The one prose cross-reference to those numbers
  (`w11_families_report.md`) is renumbered.

### 2.2 The kana chain (40 edges, by rule, no authoring)

**The rule.** *Every pre-N5 lesson needs the pre-N5 lesson immediately before it in course order.*
The course opener, `les:pre-n5-orientacao-01`, is the one lesson with nothing before it.

The pre-N5 strand runs `orientacao 01-02 · sons 01-03 · hiragana 01-15 · katakana 01-15 ·
pronuncia 01-03 · saudacoes 01-03`, consecutively, so that one rule delivers both halves of the
brief's statement: inside a strand it IS "the previous lesson of the strand" (hiragana-08 needs
hiragana-07), and at the boundary it is "the first katakana lesson needs the last hiragana lesson"
(katakana-01 needs hiragana-15 — 1 edge). 28 edges are within a kana strand, 11 join the
non-kana pre-N5 lessons in the same way.

### 2.3 The 11 deep review roots (11 edges, by rule)

`n5-revisao-01..03` (positions 119-121), `n5-kanji-exame-01..03` (122-124) and
`n4-kanji-exame-01..05` (216-220) re-drill only what they unlock themselves, so the derivation
sees no dependency at all — a lesson with zero ancestors 216 lessons into the course.

**The rule.** *Each needs the lesson immediately before it in course order.* For the first lesson of
each block that IS the last lesson of the topic it reviews (`n5-revisao-01` -> `n5-conectando-07`,
the last N5 teaching lesson; `n4-kanji-exame-01` -> `n4-revisao-03`); inside a block it chains the
review sequence itself. Mechanical, strictly backwards, no judgement.

**`placement: "unplaceable"` was NOT written.** No such field exists — not in
`design/lesson_schema.md`, not in `design/unlock_enums.json`, not in `contracts/lesson.schema.json` —
and the brief is explicit that a missing field must not be invented. **Recorded here for owner
decision D2** (completion / placement policy): these eleven lessons now have a prerequisite edge, so
they are reachable, but a placement test that drops a learner *into* one of them still skips the
whole course. They are review, not teaching; a placement policy has to say whether a review lesson
is a legal entry point at all.

### 2.4 The 9 lessons that keep no prerequisite

`course/needs_root_exemptions.json`, ratcheted at 8 (the course opener is excluded by the rule
itself, not by the file):

| lesson | pos | why |
|---|---:|---|
| `les:pre-n5-orientacao-01` | 0 | the course opener — nothing precedes it |
| `les:n5-desu-wa-01` | 41 | forward-only: every dependency points at a LATER lesson |
| `les:n5-desu-wa-02` | 42 | forward-only |
| `les:n5-perguntas-02` | 47 | forward-only (10 forward edges) |
| `les:n5-numeros-tempo-01` | 52 | self-contained: all 9 referenced taught items are its own unlocks |
| `les:n5-numeros-tempo-03` | 54 | forward-only (10 forward edges) |
| `les:n5-numeros-tempo-06` | 57 | self-contained |
| `les:n5-numeros-tempo-08` | 59 | self-contained |
| `les:n5-numeros-tempo-09` | 60 | self-contained |

The four `forward-only` roots are course-order debt, not model debt: they are the head of the
607-edge forward-reference ledger that **W21b** owns. The list can only shrink.

### 2.5 The note is learner-facing, and it is a template

The derivation's own note is bookkeeping — `introduces vocab:1241450; seen via body-reading` — and
the field is rendered in an "antes desta lição" box. Every note is therefore produced by a **fixed
pt-BR template per reason class**, never free prose (`pt_note()` in `build_needs_table.py`): the
driving refs are resolved to what a learner actually reads (a kanji character, a vocabulary headword
with its kana, a grammar point's `structure_pattern`) and dropped into one sentence. Singular and
plural agree; a mixed-kind note separates the groups with a comma before the last "e" so it does not
read as one flat list. Of the 696 derived edges, 618 name one item, 68 name two and 10 name three;
the 51 by-rule edges take a fixed sentence of their own.

Ten notes exactly as the learner sees them:

| lesson | needs | note |
|---|---|---|
| `les:n5-perguntas-03` | `les:n5-desu-wa-01` | Apresenta a palavra 貴方 (あなた), que aparece nesta lição. |
| `les:n3-enfase-05` | `les:n3-desejos-02` | Apresenta o kanji 値, que aparece nesta lição. |
| `les:n5-comparacoes-02` | `les:n5-numeros-tempo-09` | Apresenta as palavras スポーツ e 此の (この), que aparecem nesta lição. |
| `les:n4-oracoes-relativas-03` | `les:n4-forma-simples-02` | Apresenta os kanji 事 e 自, e a palavra 鳴る (なる), que aparecem nesta lição. |
| `les:n3-concessao-01` | `les:n4-conectores-04` | Apresenta a palavra 付く (つく), que aparece nesta lição. |
| `les:n5-convites-03` | `les:n5-convites-01` | Apresenta o ponto de gramática ～ませんか, que aparece nesta lição. |
| `les:pre-n5-hiragana-02` | `les:pre-n5-hiragana-01` | Vem logo antes na mesma sequência do silabário; esta lição continua de onde ela parou. |
| `les:pre-n5-katakana-01` | `les:pre-n5-hiragana-15` | Fecha o hiragana. O katakana só começa depois que todo o hiragana está aprendido. |
| `les:n5-revisao-01` | `les:n5-conectando-07` | É a última lição do bloco que esta revisão cobre. |
| `les:n4-kanji-exame-03` | `les:n4-kanji-exame-02` | Vem logo antes nesta mesma sequência de revisão; esta lição continua de onde ela parou. |

**One thing a reader should distrust.** Eleven notes, over eleven lessons, read *"Apresenta a
palavra 琴 (こと)"*. That is
faithful to the corpus and wrong as pedagogy: those lessons use こと the formal noun, and the
reference resolves to `vocab:1241450`, the musical instrument. The note did not create the defect —
it made it visible, which is what a learner-facing rendering of a derived edge is for. It belongs to
the same homograph class W11/W12 have been closing and is listed in §6.

---

## 3. The linearity gate

`validate_lesson_gating.py` check C used to be one rule plus an apology: *"0 `needs` entries across
322 lessons — the prerequisite model is empty, so check C proves nothing about linearity."* It is
now four hard checks.

| check | what it proves | today |
|---|---|---|
| **C1** | every `needs[].ref` resolves to an exported lesson AND is strictly earlier in course order | 747 edges, 0 FAIL |
| **C2** | every lesson except the course opener declares a prerequisite, unless held in `course/needs_root_exemptions.json` with a reason; an entry whose lesson now HAS needs is a failure; the count is ratcheted | 8/8 held, shrink-only |
| **C3** | the graph is ACYCLIC, by Kahn topological sort over the STORED edges | 322/322 drained |
| **C4** | the stored edges are EXACTLY `scripts/build_needs_table.py`'s output on the tree being validated — the derivation plus the two documented rules, note included | re-derivation agrees |

C4 is the one that matters most and the one that did not exist before. Without it the model is a
snapshot: a lesson could gain a chip whose introducer is not among its prerequisites, or a note could
be hand-edited, and every other check would stay green. With it, `needs[]` is data — it cannot drift
from the references it was derived from.

Gate line: `needs: 747 edge(s) over 313 lessons; 8/8 prerequisite-less and held, 1 course opener,
graph acyclic (322/322 drained), re-derivation agrees`.

### Plant proof

On a copied tree carrying the validators **and the scripts they import** (`derive_needs.py`,
`build_needs_table.py`) — copying only the validator makes it read the real repo and pass falsely.
Control run first: both validators exit 0 on the unmutated fixture. **11 plants, 11 caught.**

| plant | caught by |
|---|---|
| a need pointing forward (`n5-desu-wa-03` -> `n3-relato-04`) | C1 `not strictly earlier (position 311 vs 43)` |
| a need on a lesson id that does not exist | C1 `not an exported lesson` |
| a lesson loses its `needs` and is not held | C2 `declares no prerequisite and is not held` |
| an exemption entry for a lesson that HAS needs | C2 `now declares prerequisites — delete the entry` |
| two lessons emptied and both added to the exemption file | C2 `prerequisite-less lessons GREW: 8 -> 10` |
| a two-lesson cycle | C3 `has a CYCLE: the topological sort drained 59 of 322` |
| an extra, backwards, resolvable edge nothing derives | C4 `stores a need ... the derivation does not produce` |
| a derived edge deleted from the record | C4 `does not store the derived need on ...` |
| a hand-edited note | C4 `the stored note is not the derived one` |
| **the DATA moving under a stored model** — the single `body-chip` that is the only reason `n5-passado-03` needs `n5-passado-01`, deleted | C4 `stores a need ... the derivation does not produce` |
| a `<jp reading>` stripped back to a bare span | bodies `NO reading attribute GREW: 264 -> 266` |

The last-but-one is the case C4 was built for: C1 still resolves, the graph is still acyclic, the
lesson still declares prerequisites, and only C4 sees that the reason for the edge is gone.

---

## 4. A7 furigana

### 4.1 The split, measured before writing

| | spans | distinct (lesson, surface) |
|---|---:|---:|
| kanji-bearing `<jp>` spans with no `reading` | 875 | 727 |
| **written** | **611** (69.8%) | 510 |
| — rule (i): the lesson's own vocabulary record | 315 | 256 |
| — rule (ii): SudachiPy, verified against the registries | 296 | 254 |
| **residue, listed with both candidates and NOT written** | **264** (30.2%) | 217 |

161 lessons gained a reading. Both layers agree at 611 (the apply reports the same count for the
authoring sources and for the index, which is itself a check that the two had not drifted).

### 4.2 The rules

- **(i)** the span text is a vocabulary headword (or alternate form) the lesson's own
  `cumulative_known_set` already contains, and exactly one such record exists -> that record's
  `kana`. The lesson taught that word, so that is the word it is printing.
- **(ii)** otherwise SudachiPy (mode C), assembled **token by token**, katakana-to-hiragana, then
  verified:
  - a token with no kanji contributes its **surface**, not its reading — which is what keeps
    アメリカ人 at アメリカじん instead of あめりかじん, and keeps the placeholder 〜 in
    `全然〜ない` a 〜 instead of きごう;
  - a kanji-bearing token whose surface names registry records must name exactly ONE reading among
    them and Sudachi must agree with it;
  - a lone kanji naming no record at all is accepted only when its dictionary form names one.
- **whatever the rule**, the reading must be kana-only by the gate's own `READING_OK`, must cover the
  hiragana literally written in the base, and must **align against the Layer-A kanji registry**
  through `scripts/export/kanji_align.py` — the same whole-word alignment that regrouped 4,591
  compounds, so a reading that credits a kanji with a sound it does not make is refused.

The two rules cross-check each other: where (i) and (ii) disagree, neither is written.

### 4.3 Residue, by cause (264 spans, 217 distinct)

| spans | cause | example |
|---:|---|---|
| 98 | the surface names ≥2 registry records with different readings — a homograph Sudachi is guessing at | `間に` (間 = あいだ / ま / かん), `後で`, `その上`, `の中で` |
| 74 | a character the Layer-A **kanji registry does not carry**: in this corpus that is a radical or component printed inside a decomposition, not a word | `亻` `氵` `宀` `辶` `艹` `扌` `罒` `刂` `礻` `冫` `頁` |
| 51 | a lone kanji with >1 registry reading and no vocabulary record to settle it | `言` (4 readings), `立` (6), `安`, `夕`, `運`, `里` |
| 19 | the LESSON itself knows two records spelled that way | `日` (にち/ひ), `何` (なに/なん), `門` (と/もん), `米` (こめ/メートル) |
| 13 | Sudachi and the registry disagree outright | `直` Sudachi じか / registry じき; `ように言う` Sudachi ゆう / registry いう |
| 9 | the reading does not align against the kanji registry | `下手` へた (a 熟字訓 the aligner correctly refuses) |

Every residue row carries `candidate_registry` and `candidate_sudachi` in the table, so a teacher
sees both candidates and picks. **`validate_lesson_bodies.py` is ratcheted at 264** and fails on
growth, so the residue can only shrink.

The 74-span radical class deserves its own line, because it is the one place the mechanical answer
and the pedagogical answer differ: `亻` genuinely reads にんべん and Sudachi says so, but the corpus
has no Layer-A record for it, and a reading nothing can verify is not one this pipeline writes.
Naming the component readings is a small authoring pass (about 20 distinct characters), not a
derivation.

### 4.4 Twenty samples, for a human read

| span | reading | rule | lesson |
|---|---|---|---|
| 作る | つくる | i | `les:n4-condicionais-03` |
| 一番 | いちばん | i | `les:n5-comparacoes-02` |
| 拝見 | はいけん | i | `les:n4-passiva-02` |
| 口 | くち | i | `les:n5-kanji-exame-01` |
| 気持ち | きもち | i | `les:n4-dar-receber-01` |
| 言う | いう | i | `les:n5-conectando-05` |
| 戦争 | せんそう | i | `les:n4-potencial-02` |
| 始める | はじめる | i | `les:n4-aspecto-01` |
| 目 | め | i | `les:n3-conectores-01` |
| 程度 | ていど | i | `les:n3-perspectiva-05` |
| 予定です | よていです | ii | `les:n4-volitivo-04` |
| 友 | とも | ii | `les:n5-conectando-02` |
| 旅 | たび | ii | `les:n4-passiva-03` |
| 出ます | でます | ii | `les:n4-experiencia-05` |
| 食べたて | たべたて | ii | `les:n3-estado-01` |
| 全然〜ない | ぜんぜん〜ない | ii | `les:n3-enfase-03` |
| 火 | ひ | ii | `les:n5-particulas-lugar-06` |
| アメリカ人 | アメリカじん | ii | `les:n5-numeros-tempo-03` |
| 分かった | わかった | ii | `les:n4-oracoes-relativas-02` |
| 見た | みた | ii | `les:n5-rotina-04` |

**Two I would flag to a teacher**, both derived legitimately and both worth a second opinion:
`未` -> ひつじ (the zodiac reading; in a decomposition the learner probably wants み) and `門` -> と
in the one lesson whose known set holds only 門/と (elsewhere 門 is correctly residue). Both are
single spans.

### 4.5 The regex

`validate_lesson_bodies.py`'s `JPTAG` required the attribute to be present before checking anything,
so `<jp reading="">合</jp>` was a hard failure and `<jp>合</jp>` was invisible — the exact blind spot
that let 875 spans ship silent. A second pattern, `JPANY`, now sees **every** span, and the rule is
kanji-implies-reading-**attribute**, held by `FURIGANA_RESIDUE_RATCHET`.

---

## 5. Proof that no prose moved

Every lesson was rendered to text at `git HEAD` and in the working tree and diffed. "Rendered text"
= every text node of the body plus every learner-readable string in the record (title, description,
objectives, exercise prompt / explanation / answer), whitespace normalized, **tags and attributes
erased** — which is the whole point: an added attribute must be invisible to it.

```
lessons compared 322  |  rendered text IDENTICAL 322  |  text MOVED 0  |  not at HEAD 0
lessons whose STRUCTURE changed (needs[] and/or <jp reading>): 319
```

`needs` is excluded from that comparison on purpose: it is the structure this unit adds and its
notes are new learner-facing text by design (§2.5 shows them).

The three lessons that did not change structurally are `les:pre-n5-orientacao-01`,
`les:n5-desu-wa-01` and `les:n5-perguntas-02` — held roots that also had no bare kanji span.

**Gate output, verbatim:**

```
validate_lesson_gating: 322 lessons, 5291 item refs, 624 sentence links |
  A 0 FAIL, B 0 FAIL (3 exempt), C 0 FAIL, D 0 FAIL | 0 FAIL total
  needs: 747 edge(s) over 313 lessons; 8/8 prerequisite-less and held, 1 course opener,
  graph acyclic (322/322 drained), re-derivation agrees

lesson bodies: 322 lessons, 7765 refs, 4582 furigana spans, 11821 plain-text fields,
  372114 vocab ids — 0 FAIL {} , 0 warn
  furigana: 264/264 kanji-bearing <jp> spans still carry no `reading`

validate_repairs_applied: lesson_needs.json rows=747 PASS=747 FAIL=0;
  lesson_furigana.json rows=510 PASS=510 FAIL=0; TOTAL rows=3486 PASS=3465 SKIP=21 FAIL=0

RESULT: ALL HARD VALIDATORS PASS
```

Pipeline run in the required order: both applies -> `export_course.py` -> `infer_shapes.py` ->
`build_schemas.py` -> `build_manifest.py` -> `npm run sync-data` -> `validate_all.py`. No corpus
field moved, so `export_corpus.py` was not re-run.

### Both tables re-derive from the applied tree

`build_needs_table.py --check` and `build_furigana_table.py --check` both report **"table is
current"** *after* the apply and the export. That is not free for the furigana table: applying it
removes its own input (an annotated span is no longer a bare one), so `prior_scope()` remembers the
(lesson, surface) pairs the table already records and unions them with what is bare now. A pair can
only enter that memo by having been bare once, which git history proves, and the derivation itself
never reads the current attribute — so the memo widens the scope by exactly nothing.

### The manifest replay, and the regression it caught

Both applies are manifest steps, so the whole chain was replayed: **83 steps, 0 failed**, then the
exporters run against the scratch database and every file diffed against the committed one —
**790 files, 643 held by `rebuild_baseline.json` at their recorded bytes, 147 byte-identical**, the
same 147 as before this unit. The baseline's file SET did not change (0 added, 0 removed); 306
entries' pinned bytes moved because the data legitimately moved, and each kept the cause it already
carried.

Two things only the full replay could find, both fixed:

1. **The compact `needs` block silently disabled a repair step.** The first version of
   `apply_lesson_needs.py` spliced `needs` in as one-line objects. All 322 authoring sources are
   canonical `json.dumps(ensure_ascii=False, indent=2)` and 313 of them stopped being so — and
   `apply_qa_instruction_leaks.py` (manifest step 89) REFUSES to edit a file it cannot reproduce
   byte for byte, so the replay failed there with *"les:n3-estado-07.body (source): source file
   missing or not byte-reproducible"*. The repair would have been quietly skipped on every lesson it
   touches. The apply now writes through the parse; all 322 round-trip again, and the diff against
   `HEAD` for the authoring layer is exactly `needs` (313 files) and `body` (161 files), with zero
   body-text changes.
2. **A row can address a span the tree does not have.** `build_exam_kanji_lessons.py` regenerates
   the eight `*-kanji-exame-*` authoring sources during a replay, and its output is not the committed
   one, so 68 furigana row-halves address `<jp>` spans that are simply not there. That is not a
   half-applied write, so it is now an advisory naming the lessons rather than a refusal — and it
   becomes a hard failure if EVERY row is absent, which is the one shape that would turn the script
   into a silent no-op.

---

## 6. Not done, and handed on

- **`placement: "unplaceable"`** — the field does not exist and was not invented. The 11 review /
  kanji-exame lessons now carry a prerequisite edge by rule (§2.3); whether a review lesson is a
  legal placement target is **owner decision D2**.
- **The 8 held roots** are W21b's forward-reference ledger (607 edges). C2's ratchet is the meter
  for that work: it drops as W21b moves unlocks earlier.
- **The 264-span furigana residue** is a teacher pass, not a derivation. The cheapest slice is the
  74 radical/component spans (about 20 distinct characters, one authored name each); the 98
  homograph spans need the lesson's own context and are the same class as the W11 reading rule.
- **Eleven notes name 琴 where the lesson means こと** (§2.5) — `les:n3-causa-02/-04`,
  `n3-conectores-04/-05`, `n3-estado-05/-06`, `n3-intencao-06`, `n3-tempo-06`, `n4-conectores-07`,
  `n4-revisao-01/-02`. A vocab re-point, not a note fix.
- **`item_refs` on exercises is still empty everywhere** (W21b) — untouched here.
- **STATE.md and the commit** are the caller's: no git command that changes state was run.
