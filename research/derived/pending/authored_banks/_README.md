# W18b: paraphrase (言い換え類義) and usage (用法) re-authoring: PREPARE stage output

Work files for the two AUTHORED exam families that the W17 builder **cannot fix by dropping**. This
directory is **pending**: nothing here is applied to `corpus/`, to `course/` or to the DB, and no
item is authored at this stage. Selection material only.

W17 measured the problem (`research/reports/w17_builder_report.md` §3): every deterministic bank
reaches ceiling 0 on the level gate, but `paraphrase` keeps 2 / 1 / 28 level-appropriate items of
52 / 59 / 71 and `usage` keeps 1 / 0 / 33. Each of those items is a real bank sentence an author
chose for a specific word, so the builder can only drop them, and dropping empties the N5 and N4
banks. The repair is an authoring campaign that re-selects inside the level-clean pool. That is what
these files feed.

## What was run to produce this directory

* `research/derived/patches/w17_builder.patch` applied in a **scratch copy of `scripts/`**
  (`…/scratchpad/w18b_pu/scratch_repo/`, `git apply -p1` clean). The real tree was not patched, no
  exporter or builder ran against it, `db/corpus.sqlite` was not opened for writing, and no git
  command changed any state.
* The level rule comes from the patch's own `scripts/export/exam_rules.py` (`TaughtSets`), which is
  the single implementation `scripts/validate/validate_exam_level_gate.py` measures: every kanji of
  the learner-visible Japanese, the item's own `vocab`, the source sentence's `tokens[].vocab`, and
  the item's plus the sentence's grammar, all inside the `cumulative_known_set` of the **last lesson
  of that level's module**.
* "What the regenerated banks already keep" was recomputed from `…/scratchpad/w17/regen/` rather
  than quoted, and it reproduces W17 exactly: 2 / 1 / 28 and 1 / 0 / 33.

### One caveat, recorded rather than hidden

A parallel unit was rewriting `corpus/sentences/bank.json` in the working tree throughout this
prepare: 5,889 records committed at `HEAD`, 10,112 uncommitted in the working tree, and the N5 pool
read 524 at generation time and 528 twelve minutes later. **Pool sizes below are therefore a
snapshot; the deficits are not**, because a deficit depends only on the paper table and on what the
regenerated banks keep, and both were stable (2 / 1 / 28 and 1 / 0 / 33 under either tree).

Every sentence these work files offer was then checked against both trees: **138 distinct slugs,
286 stem offers, all present in the committed bank at `HEAD` and level-clean under the committed
tree AND under the working tree**. Nothing here depends on that unit landing or being reverted. Re-run
the check at assembly time anyway (`why_not_clean` in `…/scratchpad/w18b_pu/drift2.py`, 40 lines);
a re-dissection that adds an untaught token link to an existing sentence is exactly what moved the
N5 pool from 563 to 524.

## The level-clean pool

A pool sentence is one whose every kanji, every `tokens[].vocab` and every `grammar[]` tag is inside
the level's taught set. A word is "proved in the pool" when a token, or a contiguous run of tokens,
spells its headword AND reads its kana (`exam_rules.reading_link_ok`, W12's rule), so a target is
never attached to a homograph.

| level | taught set (last lesson) | vocab | kanji | grammar | pool sentences | words proved in the pool | qualified targets |
|---|---|---:|---:|---:|---:|---:|---:|
| N5 | `les:n5-kanji-exame-03` | 712 | 103 | 150 | 524 | 153 | **22** |
| N4 | `les:n4-kanji-exame-05` | 1,355 | 290 | 362 | 2,315 | 534 | **204** |
| N3 | `les:n3-revisao-01` | 2,951 | 634 | 494 | 6,583 | 1,660 | 400+ (list truncated) |

Measured on the working tree at 2026-09-10 06:09Z, which is what each work file's `level_pool`
header carries. The same measurement on the committed tree at `HEAD` gives 563 / 2,470 / 4,561 pool
sentences and 156 / 537 / 1,109 words proved, the figures the W17 report quotes. The taught sets are
read from `course/`, which no in-flight unit touched.

A **qualified target** is a word that is in the level's allowed set, is proved in at least one pool
sentence, is a noun / verb / adjective / adverb, carries at least two gloss-similar equivalents from
inside the same allowed set, keys no numeral form (W17 §9 F2: `５日` rather than `五日` is a registry
defect, not exam material), and is not the `vocab_id` of any item the regenerated bank already
holds, so no authored id can collide with a surviving one.

## How many items are needed

`design/exam_simulator.md` gives the per-paper draw. The number that actually gates is
`validate_exam_banks.py` check O: a bank must hold **`MIN_RATIO` = 3×** the per-paper draw, or the
section is reported SHORT (below the draw) or THIN (below 3×), which becomes a hard failure once the
family's level ceiling is set to 0.

| family | level | paper draws | gate floor (3×) | regen bank | level-clean kept | **deficit** |
|---|---|---:|---:|---:|---:|---:|
| paraphrase | n5 | 3 | 9 | 52 | 2 | **7** |
| paraphrase | n4 | 4 | 12 | 59 | 1 | **11** |
| paraphrase | n3 | 5 | 15 | 71 | 28 | **0** |
| usage | n5 | 0\* | 0 | 52 | 1 | **0**\* |
| usage | n4 | 4 | 12 | 59 | 0 | **12** |
| usage | n3 | 5 | 15 | 71 | 33 | **0** |

\* The real N5 paper has no 用法 section, so check O skips `n5_usage` entirely and its formal deficit
is 0. At ceiling 0 the bank would nonetheless hold **one** item, which is useless for study mode. A
n5 usage file is provided anyway because it costs the campaign nothing: see the next paragraph.

**N3 needs nothing.** Both N3 banks clear the floor on their own (28 and 33 against 15). No N3 work
file is written; `_candidate_pool.json` carries the N3 candidates if depth is ever wanted.

**One journal row emits BOTH families.** `build_authored_banks.py` appends a `pp:` and a `us:` item
for every authored vid, so 25 shared N4 targets cover the 11-item paraphrase deficit and the 12-item
usage deficit at once, and the N5 paraphrase work also fills the N5 usage bank for free. That is why
`work-paraphrase-n4-01.json` and `work-usage-n4-01.json` carry the same 25 targets (and the two N5
files the same 22). It also means a row that fails the usage guard loses its paraphrase twin: both
halves have to be right, or neither ships.

## Work files

| file | family | level | candidates | deficit it covers | headroom |
|---|---|---|---:|---:|---:|
| `work-paraphrase-n5-01.json` | paraphrase | n5 | 22 | 7 | 3.1× |
| `work-usage-n5-01.json` | usage | n5 | 22 | 0 (depth only) | n/a |
| `work-paraphrase-n4-01.json` | paraphrase | n4 | 25 | 11 | 2.3× |
| `work-usage-n4-01.json` | usage | n4 | 25 | 12 | 2.1× |

`_candidate_pool.json` holds the full ranked candidate list per level (22 / 204 / 400) with the same
ranking, so a second batch extends from it without re-running the prepare.

Headroom is deliberate. The first authoring pass lost 45 vids to the verifier (20 N5, 10 N4, 15 N3,
in `_flagged.json`), which is 45 paraphrase items and 45 usage items that never reached a bank, and
at N5 the equivalents are thin (below). The campaign should expect to lose candidates.

### What a work file contains

```jsonc
{
  "work_file": "work-paraphrase-n4-01.json",
  "family": "paraphrase", "level": "n4",
  "stage": "W18b prepare (selection material only; nothing authored here)",
  "sources": { "pool": "…", "kept_bank": "…", "patch": "…" },
  "level_pool": { "level_clean_sentences": 2315, "allowed_words_proved_in_pool": 534,
                  "qualified_targets_available": 204 },
  "need": { "paper_draw_per_attempt": 4, "gate_floor_3x": 12, "regen_bank_total": 59,
            "kept_level_clean": 1, "deficit_to_floor": 11 },
  "level_allowed": {
    "source_lesson": "les:n4-kanji-exame-05",
    "rule": "…",
    "kanji": ["一", "二"],              // bare characters: n5 103, n4 290
    "words": [["会う", "あう"]]          // [headword, kana]: n5 712, n4 1355
  },
  "items": [{
    "work_id": "wpa:n4:03",
    "family": "paraphrase", "level": "n4",
    "id_if_authored": "pp:n4:1234",     // the id the builder will mint: <prefix>:<level>:<vid>
    "vid": 1234, "vocab": "vocab:1307500",
    "hw": "始める", "kana": "はじめる", "pos_class": "verb", "pos": ["v1", "vt"],
    "common": true,
    "introduced_at_this_level": true,   // taught inside THIS level's module, not inherited
    "already_in_journal": false,        // a row for this vid exists in input_<level>.json
    "flagged_in_journal": null,         // the verifier's reason string, if this vid was rejected once
    "gloss_pt": ["começar"], "gloss_en": ["to begin"],
    "pool_sentence_count": 8,

    // paraphrase only
    "stem_candidates": [{               // ranked: real before generated, headword verbatim, shorter
      "sentence": "sent:tatoeba-945909", "jp": "…", "pt": "…", "en": "…",
      "register": "neutral", "ai_generated": false, "headword_verbatim": true,
      "target_gloss_in_sentence": "…"   // the dissection's own gloss for THIS token, so the author
    }],                                 //   paraphrases the sense the sentence uses
    "equivalent_candidates": [{         // 2–3, by pt-BR/en gloss similarity inside the same pool
      "vocab": "vocab:1307500", "surface": "始まる", "kana": "はじまる",
      "gloss_pt": [], "gloss_en": [],
      "shared_gloss": ["começar", "start"],
      "exact_gloss_match": true         // a whole pt-BR gloss string is shared, not just a word
    }],
    "phrase_answer_recommended": false, // true when no candidate is an exact gloss match: write a
                                        //   PHRASE from allowed words instead of a single word
    "distractor_candidates": [],        // same class, common, no gloss in common, similar length

    // usage only
    "pool_sentences": [],               // same shape as stem_candidates
    "headword_verbatim_required_in_wrong": true
  }]
}
```

`level_allowed` is the whole constraint for anything the author writes: **every kanji printed
anywhere in the item must be in `kanji`**, and every word printed should come from `words`. The
gate measures kanji on the printed strings and vocab/grammar on the source sentence, so an option
built from an untaught word that happens to be written in taught kanji passes the gate and still
fails the learner. Stay inside `words`.

## The row an author must produce

One row per authored item, written to `authored-<family>-<level>-NN.json` beside the work file it
answers:

```jsonc
{ "work_file": "work-paraphrase-n4-01.json", "rows": [ … ] }
```

**paraphrase**, matching `corpus/exam_banks/<level>_paraphrase.json` field for field, plus
`provenance`:

```jsonc
{
  "id": "pp:n4:1234",                   // exactly the work row's id_if_authored
  "level": "n4",
  "stem": "去年ピアノを習い始めた。",       // the chosen stem candidate's `jp`, verbatim, unedited
  "target": "始める",                    // exactly the work row's hw (the vocab record's headword)
  "correct": "スタートする",              // the equivalent; must not equal hw or kana
  "distractors": ["…", "…", "…"],        // exactly 3, all distinct, none equal to correct
  "vocab": "vocab:1307500",             // the work row's vocab slug
  "vocab_id": 1234,                     // the work row's vid
  "sentence": "sent:tatoeba-945909",    // the chosen stem candidate's slug
  "layer": "C",
  "needs_review": true,
  "ai_generated": false,                // the STEM's provenance.ai_generated, copied, not guessed
  "source": "authored+verified",
  "provenance": {
    "work_id": "wpa:n4:03",
    "stem_sentence": "sent:tatoeba-945909",
    "sentences_used": ["sent:tatoeba-945909"],   // every bank slug this row reads from
    "options": [                                  // one entry per printed option, key first
      { "text": "スタートする", "role": "correct",    "generated": true },
      { "text": "終わる",      "role": "distractor", "generated": false, "from": "vocab:1339480" },
      { "text": "…",          "role": "distractor", "generated": true },
      { "text": "…",          "role": "distractor", "generated": true }
    ],
    "equivalent_source": "equivalent_candidates[0]" // or "authored" when the author wrote the phrase
  }
}
```

**usage**, matching `corpus/exam_banks/<level>_usage.json` field for field, plus `provenance`:

```jsonc
{
  "id": "us:n4:1234", "level": "n4",
  "target": "始める",
  "correct": "去年ピアノを習い始めた。",   // the REAL pool sentence, verbatim (spec §1.2: select)
  "wrong": ["…", "…", "…"],              // exactly 3 authored misuse sentences, all distinct
  "vocab": "vocab:1307500", "vocab_id": 1234,
  "sentence": "sent:tatoeba-945909",     // the slug of `correct`
  "layer": "C", "needs_review": true,
  "ai_generated": false,                 // the correct sentence's provenance, copied
  "source": "authored+verified(real-correct)",
  "provenance": {
    "work_id": "wus:n4:03",
    "stem_sentence": "sent:tatoeba-945909",
    "sentences_used": ["sent:tatoeba-945909"],
    "options": [
      { "text": "去年ピアノを習い始めた。", "role": "correct",    "generated": false,
        "from": "sent:tatoeba-945909" },
      { "text": "…", "role": "wrong", "generated": true },
      { "text": "…", "role": "wrong", "generated": true },
      { "text": "…", "role": "wrong", "generated": true }
    ]
  }
}
```

`generated` is per option and it is a fact, not a judgement: **`false` only when the string is taken
verbatim from a corpus record** (a bank sentence's `jp`, or a vocab record's headword / kana form,
named in `from`); `true` when the author wrote it. The picker's real-first rule (`ai_generated`) and
the provenance validators read these, so a wrong value is worse than a missing item.

## Field rules the builder enforces

An author who breaks one of these loses the item at build time, silently.
`scripts/export/build_authored_banks.py`:

* **Japanese only** in every answer field. The shape guard admits kana, kanji, 々, 〆, 0-9 / ０-９ and
  `、。！？!?（）()・` plus whitespace. No pt-BR inside a stem, a target, an option or a wrong sentence.
* **No em dash** anywhere (U+2014). Explicit guard, explicit skip.
* **paraphrase**: `correct` non-empty, not equal to the headword or to the kana, not equal to any
  distractor; exactly 3 distinct distractors.
* **usage**: exactly 3 distinct wrong sentences, none equal to the real example, and **every wrong
  sentence must contain the headword string verbatim**. For a verb or an い-adjective that means the
  dictionary form has to appear as written (`始める`, not only `始めた`), so build the misuse around a
  plain-form or a compound context. Nouns and な-adjectives are easier, which is why the ranking puts
  them first.
* **target = headword**: the row's `target` must be the current headword of its `vocab` record. This
  is the rule that replaced the hand-pulled `pp:n4:745` / `us:n4:745` (`運` vs `うん` after the A9
  re-point). Copy `hw` from the work row; never retype it.
* **the flagged table is now the default** (W17 §6(b)): a vid listed in
  `research/derived/reauthor/exam_authored/_flagged.json` is skipped even if it is re-authored well.
  `flagged_in_journal` in the work row carries the original reason. Re-authoring such a vid requires
  removing its entry in the same commit, with the new text answering the recorded reason.

And from the level gate (`validate_exam_level_gate.py`), the ceiling this campaign exists to reach:

* every kanji in `stem`, `target`, `correct`, every distractor and every wrong sentence must be in
  `level_allowed.kanji`;
* the item's `vocab` and every `tokens[].vocab` of the source sentence must be taught (guaranteed by
  choosing a stem from the work file, broken the moment a stem is edited);
* the source sentence's grammar tags must be taught (same guarantee, same way to break it).

**Do not edit a stem.** Adding or removing a single word re-opens all three dimensions, and the
sentence is Layer A / B evidence, not draft text.

## Traps measured while building this material

* **A shared pt-BR gloss is not a Japanese synonym.** `時間` and `天気` share the gloss "tempo" and
  score as an exact match; they are unrelated words. The verifier judges the Japanese, never the
  gloss, and `exact_gloss_match: true` is a hint to look, not a verdict.
* **N5 synonymy is genuinely thin.** With 712 taught words and 153 proved in the pool, most N5 rows
  come back `phrase_answer_recommended: true`, meaning no single allowed word paraphrases the
  target. Write a short phrase from allowed words instead (the shipped `pp:n3:1365` does exactly
  this: 相手 → 読む人). Do not stretch a near-miss word into the key.
* **22 is the whole N5 supply**, not a sample. If the campaign loses more than 15 of the 22, the N5
  paraphrase deficit of 7 cannot be met from this material and the fallback is generation under
  spec §1.2 (`ai_generated: true` AND `needs_review: true`), which should be reported, not done
  quietly.
* **`already_in_journal: true` with an empty bank slot** means the builder skipped that vid for a
  reason that still applies (a guard, or the flagged table). Fix the cause, not just the text.

## The verdict a verifier must produce

One verdict file per authored file, `verdict-<family>-<level>-NN.json`, one entry per authored row,
keyed by `id` (never by array index; an index-keyed verdict has already been lost once, see
`research/derived/pending/w27_sample_rows.json`):

```jsonc
{
  "file": "authored-paraphrase-n4-01.json",
  "work_file": "work-paraphrase-n4-01.json",
  "reviewed": 25,
  "verdicts": [{
    "id": "pp:n4:1234",
    "work_id": "wpa:n4:03",
    "verdict": "pass",                 // "pass" | "fix" | "reject", no other value, never null
    "rules_checked": ["japanese-only", "no-em-dash", "correct!=hw", "distinct-options",
                      "single-key", "level-kanji", "known-words", "target=headword",
                      "hw-verbatim-in-wrong", "stem-unedited", "pt-BR"],
    "failed": [],                      // rule ids that failed; non-empty ⇒ verdict != "pass"
    "reason": "…",                     // required unless verdict == "pass"
    "suggested_fix": { "correct": "…", "distractors": ["…"] }   // optional, only with "fix"
  }],
  "summary": "…"
}
```

`single-key` is the one that needs a human eye on this family: an option that is also a valid
paraphrase of the target, or a wrong-usage sentence that admits an acceptable reading, makes two
correct answers. That is what most of the recorded rejects are. 「土曜日にパーティーを開けます」 was
thrown out because 開けます also reads ひらけます, the potential of 開く, which makes the "wrong" usage
a perfectly good sentence; 「このかばんは明るくて便利です」 because 明るい does describe the colour of a
bag. Read every wrong-usage sentence a second time looking for the reading that rescues it.

Assembly rule: a row enters the ingest batch only on an explicit `"pass"`, or on `"fix"` after the
suggested fix is applied and re-verified. **A missing or null verdict excludes the row; it never
passes it.** Rows that never reach `pass` stay here with a `drop_reason` and are reported.

## Where a passing row goes next (W18, not this stage)

The builder is the source of truth for these banks, so a passing row is back-ported into the
authoring journal rather than pasted into `corpus/`:

| authored field | journal destination |
|---|---|
| `vocab_id`, `target`, `kana`, `stem` / `correct`, `sentence` | a new row in `research/derived/reauthor/exam_authored/input_<level>.json` as `{vid, hw, kana, gloss_pt, gloss_en, example, ex_slug}` |
| `correct` + `distractors` (paraphrase) | `authored_<level>_b<N>.json` → `items[].paraphrase = {correct, distractors}` |
| `wrong` (usage) | the same row's `items[].usage_wrong` |
| a cleared reject | delete that vid's entry from `_flagged.json`, same commit |

`build_authored_banks.py` then mints `id`, `layer`, `needs_review`, `source`, the `vocab` slug and
`ai_generated` itself, and W18 re-runs `scripts/contracts/build_schemas.py` in the same commit.
Keep `provenance` here in `research/derived/` (the journal has no field for it) unless W18 decides
to carry it onto the item, which is a schema change.

**Open for W18, stated rather than assumed:** the deterministic banks all carry a pt-BR
`explanation` after W17 (4,529 of 4,529 auto-graded items); the authored `paraphrase` and `usage`
banks carry none, and neither the journal nor the builder has a field for one. Adding it is a
one-line builder change plus the schema rebuild W18 already runs. It is deliberately **not** part of
the row shape above, because inventing a field the pipeline drops is how the last three listening
repairs got lost.
