# W18b — reading_comp re-authoring (PREPARE stage output)

Work files for the 読解・短文 questions over the **real** (W15-applied) passages. This directory is
**pending**: nothing here is applied to `corpus/` or to the DB. Prepare only — no questions are
authored in this stage.

Passages come from `corpus/readings/{n5,n4,n3}.json`; every one of the 286 records there resolves to
a gating lesson that exists in `course/` and is referenced by that lesson (checked while building —
including the four W15 held-back passages, which are live again under `selection:sentence-bank`).

## How many questions per passage

`design/exam_simulator.md` "Paper structure" gives the reading_comp need **per paper**: N5 3, N4 4,
N3 4. Divided by the passages available at that level, floored, clamped to [1, 3]:

| level | need per paper | passages | need ÷ passages | questions per passage | questions at this level |
|---|---|---|---|---|---|
| N5 | 3 | 43 | 0.070 | **1** (minimum) | 43 |
| N4 | 4 | 91 | 0.044 | **1** (minimum) | 91 |
| N3 | 4 | 152 | 0.026 | **1** (minimum) | 152 |
| | | **286** | | | **286** |

The minimum binds at every level, so the rule is **one 内容一致 question per passage**, which is also
what the bank was designed as ("one 内容一致 question per verified passage", exam_simulator.md) and
what the builder assumes: item id is derived from the passage slug (`rc:<level>:<slug-without-prefix>`),
so a second question on the same passage would collide. The simulator's own rule — one item per
passage per attempt — means depth comes from passage count, not from questions per passage.

## Work files

Grouped by level, ≤ 30 passages each, sizes balanced within a level.

| file | level | passages | questions |
|---|---|---|---|
| `work-01.json` | n5 | 22 | 22 |
| `work-02.json` | n5 | 21 | 21 |
| `work-03.json` | n4 | 23 | 23 |
| `work-04.json` | n4 | 23 | 23 |
| `work-05.json` | n4 | 23 | 23 |
| `work-06.json` | n4 | 22 | 22 |
| `work-07.json` | n3 | 26 | 26 |
| `work-08.json` | n3 | 26 | 26 |
| `work-09.json` | n3 | 26 | 26 |
| `work-10.json` | n3 | 26 | 26 |
| `work-11.json` | n3 | 26 | 26 |
| `work-12.json` | n3 | 22 | 22 |

### What a work file contains

```jsonc
{
  "work_file": "work-03.json",
  "level": "n4",
  "batch": { "index": 1, "of": 4 },
  "questions_per_passage": 1,
  "passage_count": 23,
  "questions_in_this_file": 23,
  "level_kanji_allowed": {          // the LAST lesson of the level's cumulative_known_set kanji
    "source_lesson": "les:n4-kanji-exame-05",
    "rule": "every kanji printed in a stem or an option must appear in this list",
    "kanji": ["一", "二"]           // bare characters: n5 103, n4 290, n3 634
  },
  "known_sets": {                   // one entry per gating lesson used in this file (deduped)
    "les:n4-...": { "lesson_title": "...", "vocab": ["vocab:…"], "kanji": ["kanji:…"], "grammar": ["gram:…"] }
  },
  "lexicon": {                      // surfaces for the slugs above, so the author can read them
    "vocab":   { "vocab:1213400": { "headword": "…", "kana": "…" } },
    "grammar": { "gram:…": "rótulo pt-BR" }
  },
  "passages": [{
    "slug": "read:n4-…-01", "level": "n4", "title": { "pt-BR": "…", "en": "…" },
    "gating_lesson": "les:n4-…", "cumulative_known_set_ref": "les:n4-…",   // key into known_sets
    "jp": "…",                                   // the passage as printed
    "sentences": [{ "index": 0, "jp": "…" }],    // `about` indices refer to THIS index
    "jp_with_readings": "見[み]ました…",           // surface[reading] for every kanji-bearing token
    "tokens": [{ "s": "…", "r": "…", "pos": "…" }],
    "translation_pt": "…",                       // the pt-BR ground truth to author against
    "uses": { "kanji": [], "vocab": [] },
    "questions_required": 1
  }]
}
```

## The row an author must produce

One row per required question, written to `authored-NN.json` beside the work file it answers
(`{"work_file": "work-03.json", "rows": [ … ]}`):

```jsonc
{
  "passage": "read:n4-oracoes-relativas-03-01",  // the work file's passage slug
  "question_index": 0,                           // 0-based; only 0 exists while q/passage = 1
  "stem": "この人はどうして駅まで歩きましたか。",     // Japanese only; ends in か。/か/？/。
  "options": ["…", "…", "…", "…"],               // exactly 4, Japanese only, all distinct
  "key": 2,                                      // index into options of the correct answer
  "explanation": "…",                            // pt-BR: why the key is right and the others are not
  "about": [1, 2],                               // passage sentence indices the question relies on
  "ai_generated": false,                         // the Japanese the learner READS is the human passage
  "needs_review": true                           // layer C, always
}
```

Field rules:

- **`stem` / `options` are Japanese only** — the shape guard allows kana, kanji, 0-9/０-９, Ａ-ｚ and
  `、。！？!?（）()・「」`. No em dash anywhere. No pt-BR inside a stem or an option.
- **`key`** is an index, not a string. The assembler maps the row to the builder's shape:
  `correct = options[key]`, `distractors` = the other three in order.
- **`about`** must be non-empty and every index must exist in that passage's `sentences`. It is the
  author's evidence that the question is answerable from the text, and the verifier reads exactly
  those sentences first.
- **`explanation`** in natural pt-BR (`design/translation_style.md`); never pt-PT, never a literal
  gloss of the Japanese, and it must say why each distractor fails.
- **`ai_generated: false`** on every row (the reading is human-written; the provenance derivation
  `validate_provenance_json.py` enforces rc → false). `needs_review: true` on every row.

### The four question rules the builder enforces (`scripts/export/build_reading_comp_bank.py`)

An author who breaks one of these loses the item at build time, silently, exactly as 250 of the old
questions were lost:

- **P1 aboutness** — at least one content word (≥ 2 chars, 名詞/動詞/形容詞/形状詞/副詞/代名詞) of the
  stem occurs verbatim in the passage. A question with no lexical footing in the text is not a
  question about it.
- **P2 known-set kanji** — every kanji in the stem and in all four options is in the *gating lesson's*
  `cumulative_known_set` (the strict gate: the item is also printed in that lesson's reading box).
- **P3 known-set words** — every content word of every option resolves inside that same known set
  (kana-only words, numerals and words no registry record answers are the carve-out).
- **P4 not scannable** — reject if the correct answer appears verbatim in the passage and no
  distractor does; that item is answerable by string search without reading.

### The level rule (W17)

Independently of P2, the **exam** gate is the level rule: every kanji printed in a stem or an option
must be inside `level_kanji_allowed.kanji` — the last lesson of that level's cumulative known set.
The gating-lesson set (P2) is the stricter of the two and is always a subset, so authoring against
`known_sets[cumulative_known_set_ref]` satisfies both. Ceiling is **0** violations.

Also inherited from W17: no okurigana or orthography giveaway (the key must not be the only option
whose surface shape matches the passage), no longshot distractor (an option impossible on length or
register alone), and one key only — options that are homophones or paraphrases of each other collapse
into a second correct answer and are rejected.

## The verdict a verifier must produce

One verdict file per authored file, `verdict-NN.json`, one entry per authored row, keyed by
`passage` + `question_index` (never by array index — an index-keyed verdict has already been lost
once, see `research/derived/pending/w27_sample_rows.json`):

```jsonc
{
  "file": "authored-03.json",
  "work_file": "work-03.json",
  "reviewed": 23,
  "verdicts": [{
    "passage": "read:n4-oracoes-relativas-03-01",
    "question_index": 0,
    "verdict": "pass",              // "pass" | "fix" | "reject" — no other value, never null
    "rules_checked": ["P1", "P2", "P3", "P4", "level", "single-key", "pt-BR"],
    "failed": [],                   // rule ids that failed; non-empty ⇒ verdict != "pass"
    "reason": "…",                  // required unless verdict == "pass"
    "suggested_fix": { "stem": "…", "options": ["…"], "key": 1 }   // optional, only with "fix"
  }],
  "summary": "…"
}
```

Assembly rule: a row enters the ingest batch only on an explicit `"pass"` (or on `"fix"` after the
suggested fix is applied and re-verified). **A missing or null verdict excludes the row — it never
passes it.** Rows that never reach `pass` stay here with a `drop_reason` and are reported, not
silently dropped.

### Where a passing row goes next (W18, not this stage)

Assembled rows become `research/derived/reauthor/exam_authored/authored_rc_<level>_b<N>.json` in the
builder's own shape — `{"items": [{"slug", "question", "correct", "distractors"[3]}]}` — and
`build_reading_comp_bank.py` writes `corpus/exam_banks/{level}_reading_comp.json`. `explanation`,
`about` and the provenance flags are carried alongside for the schema fields W18 adds
(`build_schemas.py`) and for the review views; the builder stamps `layer: "C"`, `needs_review: true`,
`source: "authored+verified"`, `ai_generated: false` itself.
