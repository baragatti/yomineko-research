#!/usr/bin/env python3
"""W09 / owner decision A9 — re-point vocab records that resolve to the WRONG JMdict entry.

`research/reports/qa_sweep/vocab_identity_queue.md` found 22 records (plus 尾/お at lower
confidence) whose slug names a JMdict entry that is NOT the word the JLPT list slot meant. The
ingest chose the entry by READING alone, so a kana-keyed list row (`はい,はい,"yes"`) resolved to
the homophone the reading also fits (肺 "lung"). The reading consensus was sound, which is why
`level_confidence: 1.0 / 4/4` sits on records whose lemma is wrong.

`vocab:<jmdict_id>` IS the published address (contracts/README.md), so this is a migration and not
a field edit. The owner chose option (a), re-point in place, redirect kept.

WHAT THIS SCRIPT DOES **NOT** DO, AND WHY THAT MATTERS
-----------------------------------------------------
PENDING.md's A9 states: "Collateral checked: none of the intended targets already exists as a
duplicate record." **That premise is false for 13 of the 22.** Re-derived here against the same
JMdict 3.6.2 and the same three consensus lists, thirteen of the intended entries are ALREADY the
published address of another vocab record — the queue's own `collateral` column names them
(「成る sits at n3 (id 2517)」…). A re-point onto a taken slug is not a re-point: it is a MERGE, and
by the W08 precedent a merge that spans two lessons or two levels is refused, not guessed. Those
thirteen, plus one whose intended headword collides, are in REFUSED below, each with the number
that decides it. The eight this script applies are the ones where the target entry is held by
nobody and the change is an address + content correction with no course consequence.

WHAT "RE-POINT IN PLACE" COSTS, STATED PLAINLY
----------------------------------------------
The vocab ROW survives (so every `vocab_id` foreign key, family membership, lesson slot and SRS
card survives) but its IDENTITY is replaced: slug, headword, kana, romaji, forms, senses and
JMdict provenance all become the target entry's. The old lexeme therefore LEAVES the corpus — 肺
"pulmão", 園 "jardim", 総, 立ち, 侯, 等々, 運 "sorte" and 杯/さかずき are not retired to an archive
row, they are overwritten. That is inherent to option (a); option (b) is what keeps both. So this
script writes the COMPLETE pre-migration record (row, forms, senses, both locales, pitch, kanji
edges, level evidence) into `research/derived/vocab_repoint_ledger.json` before touching anything,
and the old address stays resolvable through `vocab.repointed_from` → `corpus/vocab_redirects.json`.
Two of the overwritten lexemes are attested by the lists at another level (運/うん at n3 in all
four; 園/その at n1 in bluskyo) and should be re-ingested there; the ledger says so per record.

EVERY REFERENCE FOLLOWS, AND EACH ONE IS RE-VERIFIED RATHER THAN ASSUMED
-----------------------------------------------------------------------
* `sentence_vocab` / `token.vocab_id` — the links were made by surface/reading matching, so most of
  them are links to the word the record was MEANT to be. Most, not all: each link is re-checked
  against the target entry's own forms and reading here, and a link that only fits the retired
  lexeme is dropped (`杯` read さかずき is not the counter read はい; `運悪く` is not うん).
* `lesson_unlocks.ref` — the courseware addresses vocabulary by `vocab:<headword>`, so a changed
  headword changes the ref. The rewrite refuses if the target ref is already claimed in that lesson.
* `lesson.cumulative_known_set` — stored as headword refs too; ~1,700 lesson rows carry them.
* lesson `body` in `localized_text` — `<vocab ref="vocab:肺"/>` chips, every locale.
* `family_member` — a `word_family` is keyed on a kanji (`grp:word-52d5` = 動). A membership whose
  key kanji is absent from the new headword is dropped; `semantic_field` theme families are kept.
* `reading.uses.vocab` — row numbers, so structurally intact, but a passage that does not contain
  the new word no longer uses it; those ids are dropped.
* `corpus/exam_banks/*.json` — the ONE reference site the exporters do not regenerate (W17/W18
  still owe that). `kanji_reading` and `orthography` items are stem/answer projections of the
  record, so they are re-derived from it; an item whose Japanese was picked for the retired lexeme
  (context_fill, paraphrase, usage) or that goes degenerate (a kanji-reading item on a kana-only
  headword) is quarantined into `corpus/exam_banks/removed_items.json`, the ledger that already
  exists for exactly this.
* `research/derived/lessons/*.json` — the authoring source, so the next loader+export cycle cannot
  reintroduce the old address.
* `course/speak/**/*.json` — builder output none of the three exporters regenerates, so its `vocab:`
  refs (and the bare surfaces a re-drawn distractor embeds) are moved here or they name a record that
  no longer exists.
* the redirect map `corpus/vocab_redirects.json`, emitted by `export_corpus.py` from the new
  `vocab.repointed_from` column (registered in `design/generated_artifacts.json`).

Three reference sites need NOTHING and are listed so the silence is deliberate rather than an
oversight: `lesson_introduces` and `exercise_item` address a word by `member_id` (the row id, which
this migration keeps), and `corpus/conjugations/*.json` is exporter output derived from
`verb_class` / `adj_class` — none of the eight is a verb or an adjective before or after, so the
conjugation slugs the export emits are unchanged. `vocab.freq_rank` is the one Layer-A field that is
neither kept nor dropped but RE-DERIVED (see `freq_rank_for`).

pt-BR glosses are re-authored here from the target entry's own JMdict senses (Layer B,
`needs_review: 1`) because carrying "pulmão" onto はい would be worse than an empty field, and an
empty field is not publishable: `contracts/vocab.schema.json` requires the locale object.

Usage:  migrate_vocab_repoint.py [--apply] [--check] [--db PATH] [--root PATH]
Default is a dry run that prints the whole plan and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

_sys_scripts = Path(__file__).resolve().parent
sys.path.append(str(_sys_scripts))
from dbtarget import db_target, take_flag  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

try:
    import jaconv
except ImportError:  # pragma: no cover - jaconv is a hard dependency of the ingest chain
    jaconv = None


# ==================================================================================================
# The table. One row per re-point; everything else in this file is generic machinery over it.
# `expect` is an EXACT precondition measured on the pre-migration index and re-measured before any
# write: if the graph is not the shape the queue described, this script refuses rather than guessing.
# `list_says` quotes the source list row that produced the level tag, verbatim.
# ==================================================================================================
REPOINTS: list[dict] = [
    {
        "vocab_id": 502, "old_slug": "vocab:1472870", "new_slug": "vocab:1010080",
        "old_jmdict_id": "1472870", "new_jmdict_id": "1010080",
        "old_headword": "肺", "old_kana": "はい",
        "list_says": "n5.csv / openanki_vocab_n5.csv line 386: `はい,はい,yes` (Genki Ln.1)",
        "evidence": ("Every n5 list row keyed はい is the interjection; 肺 is carried only at n1 "
                     "(jlptvocabapi_n1, bluskyo_kanji_n1) and n3 (openanki_vocab_n3 肺 'lung'). The "
                     "4/4 n5 agreement is agreement about はい, not about 肺. はい 'sim' is absent "
                     "from all 7,401 records and is week-1 material."),
        "retired_lexeme_belongs_at": "n3 (openanki_vocab_n3 / jlptvocabapi_n1 both carry 肺)",
        "expect": {"sentence_vocab": 11, "sentence_vocab_dropped": 1, "token": 4, "token_dropped": 1,
                   "lesson_unlocks": 1, "lesson_bodies": 1, "cks": 224, "family_dropped": 0,
                   "reading_uses_dropped": 0, "exam_rewritten": 0,
                   "exam_quarantined": 0, "kanji_examples_dropped": 0},
    },
    {
        "vocab_id": 355, "old_slug": "vocab:1176240", "new_slug": "vocab:1006830",
        "old_jmdict_id": "1176240", "new_jmdict_id": "1006830",
        "old_headword": "園", "old_kana": "その",
        "list_says": "n5.csv / openanki_vocab_n5.csv: `その,その,that`",
        "evidence": ("The demonstrative その is absent from the corpus while この (257) and あの (31) "
                     "are present. 園 read その is an n1 word (bluskyo_vocab_n1 `園,その`), and 園/えん "
                     "is n1 in jlptvocabapi. The n5 4/4 agreement is agreement about その."),
        "retired_lexeme_belongs_at": "n1 (bluskyo_vocab_n1 `園,その`; jlptvocabapi_n1 園/えん)",
        "expect": {"sentence_vocab": 150, "sentence_vocab_dropped": 0, "token": 150,
                   "token_dropped": 0, "lesson_unlocks": 1, "lesson_bodies": 1, "cks": 254,
                   "family_dropped": 0, "reading_uses_dropped": 0, "exam_rewritten": 0,
                   "exam_quarantined": 2, "kanji_examples_dropped": 1},
    },
    {
        "vocab_id": 349, "old_slug": "vocab:1401470", "new_slug": "vocab:2137720",
        "old_jmdict_id": "1401470", "new_jmdict_id": "2137720",
        "old_headword": "総", "old_kana": "そう",
        "list_says": ("n5.csv line 359 `そう; そうです,そう; そうです,\"yes; appears, to be the case\"` "
                      "and n4.csv line 78 `そう,そう,\"really, (is that) so; yes, right\"`"),
        "evidence": ("Both n5 votes and both n4 votes are rows for the adverb そう; 総/そう is n1 "
                     "(jlptvocabapi_n1, bluskyo_vocab_n1) and 総 is an n2 kanji. The record is "
                     "already level-split n5/n4 at 2/4 — that split is a split about そう."),
        "retired_lexeme_belongs_at": "n1 (jlptvocabapi_n1 総/そう; bluskyo_vocab_n1 総/そう)",
        "expect": {"sentence_vocab": 77, "sentence_vocab_dropped": 0, "token": 77,
                   "token_dropped": 0, "lesson_unlocks": 1, "lesson_bodies": 0, "cks": 249,
                   "family_dropped": 0, "reading_uses_dropped": 0, "exam_rewritten": 0,
                   "exam_quarantined": 2, "kanji_examples_dropped": 0},
    },
    {
        "vocab_id": 374, "old_slug": "vocab:1551240", "new_slug": "vocab:1416220",
        "old_jmdict_id": "1551240", "new_jmdict_id": "1416220",
        "old_headword": "立ち", "old_kana": "たち",
        "list_says": "n5.csv / openanki_vocab_n5.csv line 385: `～たち,～たち,plural suffix`",
        "evidence": ("The row is the pluralising suffix, written with a leading ～ that the ingest's "
                     "own norm_candidates strips; the bare たち then matched 立ち by reading. 達 does "
                     "not exist in any of the 7,401 records, so 私たち is unbuildable. JMdict 1416220 "
                     "is `達 / たち / suf / pluralizing suffix` — the row exactly."),
        "retired_lexeme_belongs_at": "unattested at n5/n4 in any list carried in the repo",
        "expect": {"sentence_vocab": 15, "sentence_vocab_dropped": 2, "token": 0, "token_dropped": 0,
                   "lesson_unlocks": 1, "lesson_bodies": 1, "cks": 253, "family_dropped": 1,
                   "reading_uses_dropped": 1, "exam_rewritten": 2,
                   "exam_quarantined": 0, "kanji_examples_dropped": 1},
    },
    {
        "vocab_id": 503, "old_slug": "vocab:1472630", "new_slug": "vocab:2019640",
        "old_jmdict_id": "1472630", "new_jmdict_id": "2019640",
        "old_headword": "杯", "old_kana": "さかずき",
        "list_says": "n5.csv / openanki_vocab_n5.csv line 521: `～杯,～はい,counter for cupfuls`",
        "evidence": ("The n5 slot is the COUNTER 杯/はい, not the sake cup 杯/さかずき — which the same "
                     "lists carry at n1 (openanki_vocab_n1 `杯,さかずき,wine cup`; jlptvocabapi_n1). "
                     "JMdict separates them: 1472630 is さかずき (12 forms, no counter sense) and "
                     "2019640 is 杯・盃/はい with three `ctr` senses."),
        "retired_lexeme_belongs_at": "n1 (openanki_vocab_n1 / jlptvocabapi_n1 杯/さかずき)",
        "note": ("2019640 is NOT in `raw_jmdict_entry`: the raw table is built from "
                 "jmdict-eng-common-*.tgz (22,603 entries) and this entry is not flagged common. "
                 "The payload is carried in JMDICT_EXTRA below, verbatim from the tracked full "
                 "dictionary, and inserted so the record's `source: jmdict:2019640` stays verifiable "
                 "against the corpus's own Layer-A table rather than against a file a replay may "
                 "not have."),
        "expect": {"sentence_vocab": 6, "sentence_vocab_dropped": 3, "token": 6, "token_dropped": 3,
                   "lesson_unlocks": 0, "lesson_bodies": 0, "cks": 0, "family_dropped": 0,
                   "reading_uses_dropped": 0, "exam_rewritten": 2,
                   "exam_quarantined": 0, "kanji_examples_dropped": 1},
    },
    {
        "vocab_id": 1086, "old_slug": "vocab:1272630", "new_slug": "vocab:1004310",
        "old_jmdict_id": "1272630", "new_jmdict_id": "1004310",
        "old_headword": "侯", "old_kana": "こう",
        "list_says": "n4.csv / openanki_vocab_n4.csv: `こう,こう,\"like this, this way\"`",
        "evidence": ("All four n4 votes are rows for the adverb こう; 侯 is an n1 kanji and appears in "
                     "no vocabulary list at n4. こう is absent from the corpus."),
        "retired_lexeme_belongs_at": "n1 (bluskyo_kanji_n1 / kanjiapi_kanji_n1 侯)",
        "expect": {"sentence_vocab": 6, "sentence_vocab_dropped": 0, "token": 6, "token_dropped": 0,
                   "lesson_unlocks": 1, "lesson_bodies": 1, "cks": 145, "family_dropped": 0,
                   "reading_uses_dropped": 0, "exam_rewritten": 0,
                   "exam_quarantined": 2, "kanji_examples_dropped": 0},
    },
    {
        "vocab_id": 699, "old_slug": "vocab:1855690", "new_slug": "vocab:1449890",
        "old_jmdict_id": "1855690", "new_jmdict_id": "1449890",
        "old_headword": "等々", "old_kana": "とうとう",
        "list_says": "n4.csv / openanki_vocab_n4.csv: `とうとう,とうとう,\"finally, at last\"`",
        "evidence": ("All four n4 votes are rows for 到頭/とうとう 'finally'; 等々 'and so on' is a "
                     "different word and the only other とうとう in the lists is 丁々 at n1. 到頭 is "
                     "absent from the corpus."),
        "retired_lexeme_belongs_at": "unattested at n5/n4 in any list carried in the repo",
        "expect": {"sentence_vocab": 5, "sentence_vocab_dropped": 0, "token": 5, "token_dropped": 0,
                   "lesson_unlocks": 1, "lesson_bodies": 1, "cks": 195, "family_dropped": 1,
                   "reading_uses_dropped": 0, "exam_rewritten": 2,
                   "exam_quarantined": 0, "kanji_examples_dropped": 1},
    },
    {
        "vocab_id": 745, "old_slug": "vocab:1172610", "new_slug": "vocab:1001090",
        "old_jmdict_id": "1172610", "new_jmdict_id": "1001090",
        "old_headword": "運", "old_kana": "うん",
        "list_says": ("n4.csv / openanki_vocab_n4.csv: `うん,うん,\"yes (informal), all right (ok)\"` "
                      "(Genki Ln.8); bluskyo_vocab_n4 `うん,うん`; jlptvocabapi_n4 `うん (informal) yes`"),
        "evidence": ("The queue records 運 as defensible vocabulary whose SLOT was うん, and the lists "
                     "settle it: every list that carries 運/うん puts it at n3 (n3.csv, "
                     "openanki_vocab_n3, jlptvocabapi_n3, bluskyo_vocab_n3), and every n4 row keyed "
                     "うん is the interjection. So the record's n4 4/4 was never evidence for 運. "
                     "うん is absent from the corpus."),
        "retired_lexeme_belongs_at": "n3 — all four lists carry 運/うん there (it is NOT at n3 today)",
        "expect": {"sentence_vocab": 5, "sentence_vocab_dropped": 4, "token": 5, "token_dropped": 4,
                   "lesson_unlocks": 1, "lesson_bodies": 1, "cks": 196, "family_dropped": 1,
                   "reading_uses_dropped": 0, "exam_rewritten": 0,
                   "exam_quarantined": 5, "kanji_examples_dropped": 1},
    },
]

# Records the queue lists that this script deliberately does NOT touch. Printed on every run so the
# residue stays visible, with the measured number that decides each one.
REFUSED: list[tuple[str, str]] = [
    ("479 vocab:1611000 生る/なる  →  成る (1375610)",
     "MERGE, NOT A RE-POINT — 1375610 is already `vocab:1375610` = record 2517 成る at n3, unlocked "
     "by les:n3-limites-06 while 479 is unlocked by les:n5-comparacoes-05. Merging would put an n5 "
     "lesson's unlock on an n3 record (or move that record's level) and leave two lessons unlocking "
     "one word: the two conditions W08 refused (U2 cross-level, D1 two lessons). 253 sentence_vocab "
     "and 263 token links ride on it — 516 edges, the largest link burden of the thirteen."),
    ("334 vocab:1298670 刷る/する  →  為る (1157170)",
     "MERGE — 1157170 is record 1358 為る at n4, unlocked by les:n4-conectores-01, with 729 "
     "sentence_vocab and 738 token links of its own. Cross-level (n5 slot onto an n4 record)."),
    ("148 vocab:1609500 罹る/かかる  →  掛かる (1207590)",
     "MERGE — 1207590 is record 1584 掛かる at n3 (les:n3-estado-01). The n5 evidence is real, so the "
     "fix is a level move on 1584 plus dropping the n3 unlock: a course-placement decision."),
    ("154 vocab:1570710 翔る/かける  →  掛ける (1207610)",
     "MERGE — 1207610 is record 153 掛ける, already at n5 with 29 sentences, but unlocked by "
     "les:n5-verbos-01 while 154 is unlocked by les:n5-verbos-03. Two lessons, one word."),
    ("507 vocab:1474240 伯/はく  →  履く (1607260)",
     "MERGE — 1607260 is record 2581 履く at n3 (穿く is a form of the same entry, not a free one)."),
    ("376 vocab:1341840 盾/たて  →  縦 (1335640)",
     "MERGE — 1335640 is record 2306 縦 at n3."),
    ("1347 vocab:1515620 報/ほう  →  方 (1516930)",
     "MERGE — 1516930 is record 2731 方, level n3 but ALREADY unlocked by les:n5-perguntas-01, so "
     "the n5 course already teaches it through another ref. A second n5 unlock is a duplicate card."),
    ("1343 vocab:1523040 本島/ほんとう  →  本当 (1523060)",
     "MERGE — 1523060 is record 593 本当, already at n5, unlocked by les:n5-convites-06 while 1343 is "
     "unlocked by les:n5-conectando-04. Two lessons, one word."),
    ("1223 vocab:1208680 滑降/かっこう  →  格好 (1590480)",
     "MERGE — 1590480 is record 1334 格好, already at n4 (les:n4-conectores-01)."),
    ("1350 vocab:1241450 琴/こと  →  事 (1313580)",
     "MERGE — 1313580 is record 887 事, already at n4 with 206 sentence links. 1350 carries 268 "
     "sentence_vocab links of its own that were made on こと, so the merge is also the largest link "
     "reconciliation of the thirteen."),
    ("1359 vocab:1630770 献花/けんか  →  喧嘩 (1257040)",
     "MERGE — 1257040 is record 1825 喧嘩 at n3."),
    ("842 vocab:1258830 県下/けんか  →  喧嘩 (1257040)",
     "MERGE, AND A COLLISION WITH 1359 — both records were resolved out of the same けんか list slot "
     "and both name the same target, so at most one could ever be re-pointed onto it."),
    ("94 vocab:1485770 尾/お  →  御 (2826528)  [the queue's lower-confidence 23rd]",
     "REFUSED ON THE EVIDENCE, AND MERGE ANYWAY — no list row carried in the repo is keyed by a bare "
     "お (2/4 agreement, from elzup + openanki), so there is no slot to re-point INTO; and 2826528 is "
     "already record 1512 御 at n3. The queue asked for a decision with evidence: the evidence is "
     "absent, so 尾 stays."),
    ("434 vocab:1451160 動/どう  →  如何 (1008910)",
     "REFUSED ON THE LESSON-DEGRADATION CONDITION — the target slug is free, but under the corpus's "
     "own ingest rule (headword = first kanji form) its headword is 如何, which is already the "
     "published headword of record 46 (如何/いかが, n5). The courseware addresses vocabulary by "
     "`vocab:<headword>`, and 239 lessons carry BOTH `vocab:動` and `vocab:如何` in their stored "
     "cumulative_known_set: after the rewrite those 239 lists would hold one ref twice and lose the "
     "other word. That is a measured degradation of 239 lessons, which A9's condition forbids. It "
     "needs a headword-shape decision first (a kana headword beside kanji forms is a shape 0 of "
     "7,401 records have today) or the row-id ref form."),
]

# ------------------------------------------------------------------------------------------------
# Layer-A payload for a target entry that `raw_jmdict_entry` does not carry (see 503's note).
# Verbatim from research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip
#   inner file jmdict-eng-3.6.2.json, sha256 5fd4dd96bb2ef2795ffa3cb42e067cb624d67659ead9b0aa99f8425bacc98ecb,
#   version 3.6.2, dictDate 2026-06-08 — the same fetch design/sources.md records for the common set.
# ------------------------------------------------------------------------------------------------
JMDICT_EXTRA: dict[str, dict] = {
    "2019640": {
        "id": "2019640",
        "kanji": [{"common": False, "text": "杯", "tags": []},
                  {"common": False, "text": "盃", "tags": []}],
        "kana": [{"common": False, "text": "はい", "tags": [], "appliesToKanji": ["*"]}],
        "sense": [
            {"partOfSpeech": ["n"], "appliesToKanji": ["*"], "appliesToKana": ["*"],
             "related": [["杯", "さかずき・1", 1]], "antonym": [], "field": [], "dialect": [],
             "misc": [], "info": [], "languageSource": [],
             "gloss": [{"lang": "eng", "gender": None, "type": None, "text": "sake cup"},
                       {"lang": "eng", "gender": None, "type": None,
                        "text": "cup for alcoholic beverages"}]},
            {"partOfSpeech": ["ctr"], "appliesToKanji": ["*"], "appliesToKana": ["*"],
             "related": [], "antonym": [], "field": [], "dialect": [], "misc": [], "info": [],
             "languageSource": [],
             "gloss": [{"lang": "eng", "gender": None, "type": None,
                        "text": "counter for cupfuls, bowlfuls, spoonfuls, etc."}]},
            {"partOfSpeech": ["ctr"], "appliesToKanji": ["*"], "appliesToKana": ["*"],
             "related": [], "antonym": [], "field": [], "dialect": [], "misc": [], "info": [],
             "languageSource": [],
             "gloss": [{"lang": "eng", "gender": None, "type": None, "text": "counter for boats"}]},
            {"partOfSpeech": ["ctr"], "appliesToKanji": ["*"], "appliesToKana": ["*"],
             "related": [], "antonym": [], "field": [], "dialect": [], "misc": [], "info": [],
             "languageSource": [],
             "gloss": [{"lang": "eng", "gender": None, "type": None,
                        "text": "counter for octopuses and squid"}]},
            {"partOfSpeech": ["n-suf"], "appliesToKanji": ["*"], "appliesToKana": ["*"],
             "related": [["アジア杯"]], "antonym": [], "field": ["sports"], "dialect": [],
             "misc": [], "info": [], "languageSource": [],
             "gloss": [{"lang": "eng", "gender": None, "type": None, "text": "cup"},
                       {"lang": "eng", "gender": None, "type": None, "text": "championship"}]},
        ],
    },
}

# ------------------------------------------------------------------------------------------------
# pt-BR glosses for the target senses. Layer B, needs_review=1 — derived from the target entry's own
# JMdict `en` beside them, in the register design/translation_style.md asks for (natural pt-BR, not a
# literal mirror). Keyed (new_jmdict_id, sense_order); every sense of every target must be present or
# the migration refuses, because a half-translated record is not publishable.
# ------------------------------------------------------------------------------------------------
GLOSS_PT: dict[tuple[str, int], list[str]] = {
    ("1010080", 0): ["sim", "isso mesmo"],
    ("1010080", 1): ["entendi", "certo", "tá bom"],
    ("1010080", 2): ["presente", "aqui"],
    ("1010080", 3): ["como?", "oi?", "repete?"],
    ("1010080", 4): ["aqui está", "toma", "pronto"],
    ("1010080", 5): ["eia", "vamos (a um cavalo)"],
    ("1006830", 0): ["esse", "essa", "aquele de que você falou"],
    ("1006830", 1): ["parte (parte dois)"],
    ("1006830", 2): ["hum...", "é...", "então..."],
    ("2137720", 0): ["assim", "desse jeito"],
    ("2137720", 1): ["isso", "é isso mesmo"],
    ("2137720", 2): ["é mesmo?"],
    ("1416220", 0): ["sufixo de plural (pessoas e animais)"],
    ("1004310", 0): ["assim", "deste jeito"],
    ("1004310", 1): ["tanto assim", "assim"],
    ("1004310", 2): ["hã...", "é...", "bem..."],
    ("1449890", 0): ["finalmente", "afinal", "no fim das contas"],
    ("1001090", 0): ["sim", "é", "aham"],
    ("1001090", 1): ["hum", "hmm", "sei..."],
    ("1001090", 2): ["ai", "ui"],
    ("2019640", 0): ["cálice de saquê", "taça para bebidas alcoólicas"],
    ("2019640", 1): ["contador de copos, tigelas, colheradas etc."],
    ("2019640", 2): ["contador de barcos"],
    ("2019640", 3): ["contador de polvos e lulas"],
    ("2019640", 4): ["copa", "campeonato"],
}

# ------------------------------------------------------------------------------------------------
# The prose the chip rewrite does NOT reach, and why this table has to exist.
#
# A lesson body stores `<vocab ref="vocab:肺"/><text>: pulmão</text>`: the chip is an ADDRESS and the
# gloss beside it is AUTHORED pt-BR. Moving the address alone renders as 「はい: pulmão」 — a true
# address carrying a false sentence, which is exactly the degradation owner decision A9 forbids, and
# it is invisible to a JSON diff of the body (the only thing that changed there is the ref). It shows
# up in the RENDERED `course/**/lesson-NN.md`, which is where it was caught.
#
# Six bodies carry such a line. Each fix below is an EXACT substring: it must match once, or the
# migration refuses rather than guessing at prose. The lessons it touches get `needs_review = 1` —
# this is Layer-C text and a teacher signs it off. `research/derived/lessons/*.json` gets the same
# edit where its body still matches; for `n4-forma-simples-06` it does not, because that authoring
# file diverged from the DB body long before W09 (a pre-existing drift this migration does not own).
# ------------------------------------------------------------------------------------------------
BODY_FIXES: list[dict] = [
    {"lesson": "les:n5-te-form-05",
     "why": "the はいる/はい/さかずき homophone list — 502 is no longer 肺 and 503 is no longer さかずき",
     "old": "Não confunda o verbo com estes dois substantivos:",
     "new": "Não confunda o verbo com estas duas palavras, que se leem só はい:"},
    {"lesson": "les:n5-te-form-05",
     "why": "502 now holds the interjection はい, not 肺 'pulmão'",
     "old": '<vocab ref="vocab:はい"/><text>: pulmão</text>',
     "new": '<vocab ref="vocab:はい"/><text>: sim, isso mesmo (a resposta)</text>'},
    {"lesson": "les:n5-te-form-05",
     "why": "503 now holds the counter 杯/はい, not the sake cup 杯/さかずき",
     "old": '<vocab ref="vocab:杯"/><text>: taça de saquê</text>',
     "new": '<vocab ref="vocab:杯"/><text>: contador de copos e tigelas (一杯, 二杯…)</text>'},
    {"lesson": "les:n5-particulas-lugar-02",
     "why": "355 now holds the demonstrative その, not 園 'jardim'; the list is the そ-series already",
     "old": '<vocab ref="vocab:其の"/><text>: jardim, parque</text>',
     "new": '<vocab ref="vocab:其の"/><text>: esse, essa (aquilo que está perto de quem ouve)</text>'},
    {"lesson": "les:n5-particulas-lugar-03",
     "why": ("374 now holds the pluralising suffix たち, which does NOT derive from 立つ — the "
             "sentence claiming it did is false about the new word"),
     "old": ('= "ficar de pé na estação". O substantivo </text><vocab ref="vocab:達"/><text> '
             '("partida, início") vem do mesmo verbo.</text>'),
     "new": ('= "ficar de pé na estação". Não confunda com o sufixo </text><vocab ref="vocab:達"/>'
             '<text>, que marca plural de pessoas ("nós", "vocês") e não vem desse verbo.</text>')},
    {"lesson": "les:n4-obrigacao-05",
     "why": "1086 now holds the adverb こう, not 侯 'marquês'",
     "old": '<vocab ref="vocab:斯う"/><text>(こう) = "marquês" (título de nobreza).</text>',
     "new": '<vocab ref="vocab:斯う"/><text>(こう) = "assim, deste jeito".</text>'},
    {"lesson": "les:n4-forma-simples-03",
     "why": "699 now holds とうとう 'finally', not 等々 'and so on'; the list is adverbs already",
     "old": ('<vocab ref="vocab:到頭"/><text>: etc., e assim por diante (serve para encerrar '
             'listas)</text>'),
     "new": '<vocab ref="vocab:到頭"/><text>: finalmente, afinal (depois de muita espera)</text>'},
    {"lesson": "les:n4-forma-simples-06",
     "why": "745 now holds the interjection うん, so the list is no longer about 'sorte'",
     "old": "junte algumas palavras de movimento, sorte e ações:",
     "new": "junte algumas palavras de movimento, conversa e ações:"},
    {"lesson": "les:n4-forma-simples-06",
     "why": "745 now holds the interjection うん 'yeah', not 運 'sorte'",
     "old": '<vocab ref="vocab:うん"/><text>(</text><jp>うん</jp><text>): sorte, fortuna.</text>',
     "new": ('<vocab ref="vocab:うん"/><text>(</text><jp>うん</jp><text>): sim, é (resposta '
             'informal, entre amigos).</text>')},
]

KEX_RULE = ("A record demonstrates a kanji reading only if the new headword contains the kanji AND, "
            "for a one-kanji word, the record's kana IS that reading. Containment alone kept 503 on "
            "杯's kun reading さかずき after the record started reading はい.")


def ledger_prose() -> list[dict]:
    """The prose declaration, recorded whole so the ledger is auditable without reading the script."""
    return [{"lesson": f["lesson"], "why": f["why"], "old": f["old"], "new": f["new"]}
            for f in BODY_FIXES]


LEDGER = "research/derived/vocab_repoint_ledger.json"
FREQ_TABLE = "research/derived/frequency/tatoeba_lemma_freq.json"
POS_VERB = {"v1": "ichidan", "v5": "godan", "vs": "suru_irregular", "vk": "kuru_irregular"}
LOCALES = ("pt-BR", "en")
JP_KANJI = re.compile(r"[一-鿿]")


# ==================================================================================================
# helpers
# ==================================================================================================
def die(msg: str) -> None:
    print(f"REFUSED: {msg}")
    raise SystemExit(1)


def jloads(s, default=None):
    if s in (None, ""):
        return default
    try:
        return json.loads(s)
    except (TypeError, ValueError):
        return default


def jdumps(o) -> str:
    return json.dumps(o, ensure_ascii=False)


def hira(s: str) -> str:
    return jaconv.kata2hira(s or "") if jaconv else (s or "")


def romaji_of(kana: str) -> str:
    if not kana:
        return ""
    if not jaconv:
        die("jaconv is not installed; romaji must be produced by the same function the ingest uses")
    return jaconv.kana2alphabet(hira(kana))


def has_column(con: sqlite3.Connection, table: str, col: str) -> bool:
    return any(r[1] == col for r in con.execute(f"PRAGMA table_info({table})"))


def file_indent(raw: str, default: int = 2) -> int:
    for line in raw.split("\n")[1:]:
        stripped = line.lstrip(" ")
        if stripped and stripped != line:
            return len(line) - len(stripped)
    return default


def rendaku_variants(kana: str) -> set:
    """は→ば/ぱ etc. A counter's realised reading is the rendaku'd one (三杯 = さんばい)."""
    out = {kana}
    if not kana:
        return out
    table = {"は": "ばぱ", "ひ": "びぴ", "ふ": "ぶぷ", "へ": "べぺ", "ほ": "ぼぽ",
             "か": "が", "き": "ぎ", "く": "ぐ", "け": "げ", "こ": "ご",
             "さ": "ざ", "し": "じ", "す": "ず", "せ": "ぜ", "そ": "ぞ",
             "た": "だ", "ち": "ぢ", "つ": "づ", "て": "で", "と": "ど"}
    for alt in table.get(kana[0], ""):
        out.add(alt + kana[1:])
    return out


_FREQ_CACHE: dict = {}


def freq_rank_for(root: Path, headword: str, kana: str):
    """`vocab.freq_rank` re-derived for the NEW identity, by the rule build_frequency.py applies.

    Carrying the number over would be a stale Layer-A fact of exactly the kind this migration exists
    to remove: 8158 is the rank of the WRITTEN FORM 肺 in the Tatoeba count, and the record that
    holds it is about to stop being 肺. The rule is copied verbatim from
    `scripts/ingest/build_frequency.py` (a record takes a rank from its own headword, or from its
    kana only when the headword IS kana — reading equality is homophony, not identity), and it reads
    the same committed table, so a rebuild — where build_frequency runs long before this step and
    ranks the OLD headword — lands on the same number here.
    """
    if "rank" not in _FREQ_CACHE:
        p = root / FREQ_TABLE
        if not p.exists():
            die(f"{FREQ_TABLE} is missing; freq_rank cannot be re-derived and carrying the retired "
                f"lexeme's rank onto another word is not an option")
        doc = json.loads(p.read_text(encoding="utf-8"))
        _FREQ_CACHE["rank"] = {r["lemma"]: r["rank"] for r in doc["lemmas"]}
    rank = _FREQ_CACHE["rank"]
    return rank.get(headword) or (rank.get(kana) if not JP_KANJI.search(headword) else None)


def target_entry(con: sqlite3.Connection, seq: str) -> dict:
    r = con.execute("SELECT data FROM raw_jmdict_entry WHERE ent_seq=?", (int(seq),)).fetchone()
    if r:
        e = json.loads(r[0])
        extra = JMDICT_EXTRA.get(seq)
        if extra is not None and jdumps(extra) != jdumps(e):
            die(f"JMDICT_EXTRA[{seq}] disagrees with the entry already in raw_jmdict_entry — one of "
                f"the two is stale; fix the source of truth, do not migrate onto a guess")
        return e
    e = JMDICT_EXTRA.get(seq)
    if e is None:
        die(f"JMdict entry {seq} is in neither raw_jmdict_entry nor JMDICT_EXTRA")
    return e


def derive_record(e: dict) -> dict:
    """Build the vocab row EXACTLY as scripts/ingest/reconcile_levels.py would from this entry."""
    kanji_forms = [k["text"] for k in (e.get("kanji") or []) if k.get("text")]
    kana_forms = [k["text"] for k in (e.get("kana") or []) if k.get("text")]
    kana = kana_forms[0] if kana_forms else ""
    headword = kanji_forms[0] if kanji_forms else kana
    common = 1 if any(x.get("common") for x in (e.get("kanji") or []) + (e.get("kana") or [])) else 0
    senses = e.get("sense") or []
    pos_all = senses[0].get("partOfSpeech", []) if senses else []
    verb_class = next((cls for tag in pos_all for pre, cls in POS_VERB.items()
                       if tag.startswith(pre)), None)
    adj_class = ("i_adj" if any(t.startswith("adj-i") for t in pos_all)
                 else "na_adj" if any(t.startswith("adj-na") for t in pos_all) else None)
    lexeme_type = ("counter" if "ctr" in pos_all else
                   "suru_verb" if (verb_class == "suru_irregular" and headword.endswith("する"))
                   else "word")
    return {"headword": headword, "kana": kana, "romaji": romaji_of(kana), "common": common,
            "lexeme_type": lexeme_type, "verb_class": verb_class, "adj_class": adj_class,
            "kanji_forms": kanji_forms, "kana_forms": kana_forms, "senses": senses,
            "all_forms": kanji_forms + kana_forms}


# ==================================================================================================
# planning — every reference site, measured, nothing assumed
# ==================================================================================================
def plan_links(con: sqlite3.Connection, vid: int, new: dict) -> dict:
    """Re-verify every sentence_vocab / token link against the TARGET entry, one at a time."""
    forms = set(new["all_forms"])
    readings = set()
    for k in new["kana_forms"]:
        readings |= rendaku_variants(hira(k))

    def token_ok(surface: str, lemma: str, reading: str) -> bool:
        if (surface or "") not in forms and (lemma or "") not in forms:
            return False
        return not reading or hira(reading) in readings

    tokens = con.execute("SELECT id, sentence_id, surface, lemma, reading FROM token "
                         "WHERE vocab_id=?", (vid,)).fetchall()
    tok_keep, tok_drop, ok_sentences = [], [], set()
    for t in tokens:
        if token_ok(t["surface"], t["lemma"], t["reading"]):
            tok_keep.append(t["id"])
            ok_sentences.add(t["sentence_id"])
        else:
            tok_drop.append((t["id"], t["sentence_id"], t["surface"], t["lemma"], t["reading"]))
    tokened = {t["sentence_id"] for t in tokens}

    sv_keep, sv_drop = [], []
    for r in con.execute("SELECT sv.sentence_id, s.jp, sv.link_rule FROM sentence_vocab sv "
                         "JOIN sentence s ON s.id=sv.sentence_id WHERE sv.vocab_id=? "
                         "ORDER BY sv.sentence_id", (vid,)):
        sid = r["sentence_id"]
        if sid in tokened:
            # Token evidence outranks a bare surface hit: 杯 read さかずき is in the sentence but is
            # not the counter, and that is exactly the link this migration must not keep.
            (sv_keep if sid in ok_sentences else sv_drop).append(
                (sid, r["jp"], r["link_rule"], "token"))
        elif any(f in (r["jp"] or "") for f in forms):
            sv_keep.append((sid, r["jp"], r["link_rule"], "surface"))
        else:
            sv_drop.append((sid, r["jp"], r["link_rule"], "surface"))
    return {"token_keep": tok_keep, "token_drop": tok_drop, "sv_keep": sv_keep, "sv_drop": sv_drop}


def plan_families(con: sqlite3.Connection, vid: int, new_headword: str) -> dict:
    keep, drop = [], []
    for r in con.execute("SELECT f.id, f.slug, f.type FROM family_member fm JOIN family f "
                         "ON f.id=fm.family_id WHERE fm.member_type='vocab' AND fm.member_id=?",
                         (vid,)):
        m = re.fullmatch(r"grp:word-([0-9a-f]{4,6})", r["slug"] or "")
        if r["type"] == "word_family" and m:
            key = chr(int(m.group(1), 16))
            (keep if key in new_headword else drop).append((r["id"], r["slug"], r["type"]))
        else:
            keep.append((r["id"], r["slug"], r["type"]))
    return {"keep": keep, "drop": drop}


def plan_refs(con: sqlite3.Connection, old_ref: str, new_ref: str) -> dict:
    """lesson_unlocks rows, lesson bodies and stored cumulative_known_set carrying the headword ref."""
    unlocks, unlock_conflicts = [], []
    for r in con.execute("SELECT lesson_id, unlock_type FROM lesson_unlocks WHERE ref=?", (old_ref,)):
        taken = con.execute("SELECT 1 FROM lesson_unlocks WHERE lesson_id=? AND unlock_type=? AND "
                            "ref=?", (r["lesson_id"], r["unlock_type"], new_ref)).fetchone()
        (unlock_conflicts if taken else unlocks).append((r["lesson_id"], r["unlock_type"]))

    needs = [(r["lesson_id"], r["need_type"]) for r in
             con.execute("SELECT lesson_id, need_type FROM lesson_needs WHERE ref=?", (old_ref,))]

    bodies = []
    needle = f'ref="{old_ref}"'
    for r in con.execute("SELECT entity_type, entity_id, field, locale, value FROM localized_text "
                         "WHERE value LIKE ?", (f"%{needle}%",)):
        hits = r["value"].count(needle)
        bodies.append((r["entity_type"], r["entity_id"], r["field"], r["locale"],
                       r["value"].replace(needle, f'ref="{new_ref}"'), hits))

    cks, cks_dup = [], []
    for r in con.execute("SELECT id, cumulative_known_set FROM lesson "
                         "WHERE cumulative_known_set LIKE ?", (f'%"{old_ref}"%',)):
        doc = jloads(r["cumulative_known_set"], {}) or {}
        changed = False
        dup = False
        for key, arr in doc.items():
            if not isinstance(arr, list) or old_ref not in arr:
                continue
            if new_ref in arr:
                dup = True
            doc[key] = [new_ref if x == old_ref else x for x in arr]
            changed = True
        if changed:
            (cks_dup if dup else cks).append((r["id"], jdumps(doc)))
    return {"unlocks": unlocks, "unlock_conflicts": unlock_conflicts, "needs": needs,
            "bodies": bodies, "cks": cks, "cks_dup": cks_dup}


def plan_reading_uses(con: sqlite3.Connection, vid: int, new: dict) -> list:
    forms = set(new["all_forms"])
    out = []
    for r in con.execute("SELECT slug, jp, uses FROM reading"):
        u = jloads(r["uses"], {}) or {}
        ids = u.get("vocab")
        if not isinstance(ids, list) or vid not in ids:
            continue
        if any(f in (r["jp"] or "") for f in forms):
            continue
        u["vocab"] = [x for x in ids if x != vid]
        out.append((r["slug"], jdumps(u)))
    return out


def reading_fits(reading: str, headword: str, kana: str) -> bool:
    """Does this record still DEMONSTRATE that reading?

    Containment is not enough. 503 keeps the headword 杯, so the kanji test passes, but the record
    now reads はい and the edge it sits on is 杯's kun reading さかずき — it would tell a learner that
    杯 read さかずき is exemplified by a word read はい. For a one-kanji word the reading IS the word's
    reading, so the two can be compared directly; for a compound, containment is the only claim the
    edge makes and this returns True rather than inventing a stricter rule.
    """
    if len(headword) != 1:
        return True
    r = hira((reading or "").split(".")[0].replace("-", "").replace("－", ""))
    return not r or r == hira(kana)


def plan_kanji_examples(con: sqlite3.Connection, vid: int, new_headword: str,
                        new_kana: str = "") -> list:
    """`kanji_reading.example_vocab_ids` names the words that DEMONSTRATE a reading. A word that no
    longer contains the kanji — or no longer has that reading — cannot demonstrate it."""
    out = []
    for r in con.execute("SELECT kr.id, k.character, kr.reading, kr.example_vocab_ids "
                         "FROM kanji_reading kr JOIN kanji k ON k.id=kr.kanji_id "
                         "WHERE kr.example_vocab_ids LIKE ?", (f"%{vid}%",)):
        ids = jloads(r["example_vocab_ids"], []) or []
        if vid not in ids:
            continue
        if r["character"] in new_headword and reading_fits(r["reading"], new_headword, new_kana):
            continue
        out.append((r["id"], r["character"], r["reading"], jdumps([x for x in ids if x != vid])))
    return out


def reconcile_kanji_examples(con: sqlite3.Connection, apply: bool) -> list[str]:
    """The same rule, re-run over every ALREADY re-pointed record on every invocation.

    `plan_kanji_examples` only sees the records this run migrates, so a rule tightened after a
    migration landed would never reach the rows it landed on. This pass is a no-op re-proof on a
    fresh rebuild and the actual fix on an index that was migrated by an earlier version.
    """
    acts: list[str] = []
    if not has_column(con, "vocab", "repointed_from"):
        return acts
    for v in con.execute("SELECT id, headword, kana FROM vocab WHERE repointed_from IS NOT NULL"):
        for krid, ch, reading, value in plan_kanji_examples(con, v["id"], v["headword"], v["kana"]):
            acts.append(f"kanji_reading {ch}/{reading}: dropped example {v['headword']}/{v['kana']} "
                        f"(id {v['id']}) — it no longer has that reading")
            if apply:
                con.execute("UPDATE kanji_reading SET example_vocab_ids=? WHERE id=?", (value, krid))
    return acts


def apply_body_fixes(con: sqlite3.Connection, root: Path, apply: bool) -> dict:
    """Move the AUTHORED prose that sits beside a moved chip (see BODY_FIXES).

    Runs on every invocation, keyed on the exact text rather than on `repointed_from`, so it is
    idempotent by construction and reaches an index an earlier version of this script migrated.
    """
    done, todo_, missing = [], [], []
    for fx in BODY_FIXES:
        lid = con.execute("SELECT id FROM lesson WHERE slug=?", (fx["lesson"],)).fetchone()
        if lid is None:
            missing.append(f"{fx['lesson']}: no such lesson (partial index?)")
            continue
        rows = list(con.execute("SELECT rowid, locale, value FROM localized_text WHERE "
                                "entity_type='lesson' AND entity_id=? AND field='body'", (lid[0],)))
        hit = False
        for r in rows:
            v = r["value"] or ""
            n = v.count(fx["old"])
            if n > 1:
                die(f"{fx['lesson']} [{r['locale']}]: the anchor text appears {n} times; a prose "
                    f"fix must address exactly one place")
            if n == 1:
                hit = True
                todo_.append(f"{fx['lesson']} [{r['locale']}]: {fx['why']}")
                if apply:
                    con.execute("UPDATE localized_text SET value=? WHERE rowid=?",
                                (v.replace(fx["old"], fx["new"]), r["rowid"]))
                    con.execute("UPDATE lesson SET needs_review=1 WHERE id=?", (lid[0],))
            elif fx["new"] in v:
                done.append(f"{fx['lesson']} [{r['locale']}]")
        if not hit and not any(fx["new"] in (r["value"] or "") for r in rows):
            missing.append(f"{fx['lesson']}: neither the old nor the new text is in the body")

        # the authoring source, where it has not drifted away from the DB body
        p = root / "research" / "derived" / "lessons" / (fx["lesson"].replace("les:", "") + ".json")
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8")
        doc = json.loads(raw)
        body = doc.get("body")
        if not isinstance(body, str) or fx["old"] not in body:
            continue
        todo_.append(f"{p.name} (authoring source)")
        if apply:
            doc["body"] = body.replace(fx["old"], fx["new"])
            p.write_text(json.dumps(doc, ensure_ascii=False, indent=file_indent(raw)) + "\n",
                         encoding="utf-8", newline="\n")
    return {"applied": todo_, "already": done, "missing": missing}


def plan_speak_files(root: Path, rows: list[dict], plans: dict) -> list:
    """course/speak/**/*.json is builder output the three exporters do not regenerate, so the refs
    and the surfaces it embeds have to be moved here or they name a record that no longer exists."""
    slugmap = {r["old_slug"]: r["new_slug"] for r in rows}
    surfmap = {}
    for r in rows:
        n = plans[r["vocab_id"]]["new"]
        if r["old_headword"] != n["headword"]:
            surfmap[r["old_headword"]] = n["headword"]
        if r["old_kana"] != n["kana"]:
            surfmap[r["old_kana"]] = n["kana"]
    acts = []
    speak = root / "course" / "speak"
    if not speak.is_dir():
        return acts
    for path in sorted(speak.rglob("*.json")):
        raw = path.read_text(encoding="utf-8")
        doc = jloads(raw, None)
        if doc is None:
            continue
        changed: list[str] = []

        def walk(node, where):
            if isinstance(node, dict):
                for k, v in node.items():
                    node[k] = walk(v, f"{where}.{k}")
                return node
            if isinstance(node, list):
                return [walk(v, f"{where}[]") for v in node]
            if isinstance(node, str):
                if node in slugmap:
                    changed.append(f"{where}: {node} -> {slugmap[node]}")
                    return slugmap[node]
                # Only a re-drawn distractor embeds a bare surface; every other embedded string is
                # sentence text, where replacing a substring would rewrite the Japanese.
                if where.endswith("distractors[]") and node in surfmap:
                    changed.append(f"{where}: {node!r} -> {surfmap[node]!r}")
                    return surfmap[node]
            return node

        doc = walk(doc, "")
        if changed:
            acts.append({"file": path.relative_to(root).as_posix(), "actions": changed,
                         "_doc": doc, "_path": path, "_indent": file_indent(raw)})
    return acts


def apply_speak_files(acts: list, apply: bool) -> list[dict]:
    out = []
    for a in acts:
        out.append({"file": a["file"], "actions": a["actions"]})
        if apply:
            a["_path"].write_text(json.dumps(a["_doc"], ensure_ascii=False,
                                             indent=a["_indent"]) + "\n",
                                  encoding="utf-8", newline="\n")
    return out


def plan_exam_banks(root: Path, rows: list[dict], plans: dict) -> dict:
    """The one reference site the exporters do not regenerate (W17/W18 still owe that)."""
    by_old = {r["old_slug"]: r for r in rows}
    # Bank items carry BOTH addresses — `vocab` (the slug, which this migration moves) and `vocab_id`
    # (the row id, which it does not). Matching on either means an item that names only the numeric
    # one is still found, and the slug an item already carries is never trusted over the row it
    # actually points at.
    by_vid = {r["vocab_id"]: r for r in rows}
    rewrite, quarantine = [], []
    banks = root / "corpus" / "exam_banks"
    if not banks.is_dir():
        return {"rewrite": rewrite, "quarantine": quarantine}
    for path in sorted(banks.glob("*.json")):
        if path.name == "removed_items.json":
            continue
        doc = jloads(path.read_text(encoding="utf-8"), None)
        if not isinstance(doc, list):
            continue
        for it in doc:
            row = by_old.get(it.get("vocab")) or by_vid.get(it.get("vocab_id"))
            if row is None:
                continue
            new = plans[row["vocab_id"]]["new"]
            iid = it.get("id")
            kind = "kanji_reading" if str(iid).startswith("kr:") else \
                   "orthography" if str(iid).startswith("or:") else "other"
            if kind == "kanji_reading":
                if not any("一" <= ch <= "鿿" for ch in new["headword"]):
                    quarantine.append((path.name, iid, it,
                                       f"kanji_reading item on {row['new_slug']}, whose headword "
                                       f"{new['headword']} carries no kanji after the re-point"))
                elif "ぁ" <= new["headword"][-1] <= "ゖ":
                    # The bank's own okurigana_giveaway rule: a stem ending in okurigana gives the
                    # answer away unless the distractors share the same tail, and these were drawn
                    # for a word with no okurigana at all. 其の/然う/斯う all would.
                    quarantine.append((path.name, iid, it,
                                       f"kanji_reading item on {row['new_slug']}: the stem "
                                       f"{new['headword']} ends in okurigana that only the correct "
                                       f"answer {new['kana']} carries, which the bank's own "
                                       f"okurigana_giveaway rule counts as solvable by shape"))
                else:
                    rewrite.append((path.name, iid, {"vocab": row["new_slug"],
                                                     "stem": new["headword"],
                                                     "correct": new["kana"]}))
            elif kind == "orthography":
                if new["headword"] == new["kana"]:
                    quarantine.append((path.name, iid, it,
                                       f"orthography item on {row['new_slug']}, whose headword and "
                                       f"kana are both {new['kana']} after the re-point"))
                elif "ぁ" <= new["headword"][-1] <= "ゖ":
                    # The bank's own quality rule (okurigana_giveaway): a stem that already prints
                    # the answer's okurigana gives the answer away. 其の/然う/斯う all would.
                    quarantine.append((path.name, iid, it,
                                       f"orthography item on {row['new_slug']}: the stem "
                                       f"{new['kana']} prints the okurigana of the answer "
                                       f"{new['headword']}, which the bank's own okurigana_giveaway "
                                       f"rule counts as solvable without knowing the word"))
                else:
                    rewrite.append((path.name, iid, {"vocab": row["new_slug"],
                                                     "stem": new["kana"],
                                                     "correct": new["headword"]}))
            else:
                quarantine.append((path.name, iid, it,
                                   f"the item's Japanese was selected for {row['old_headword']}, "
                                   f"the lexeme {row['old_slug']} retired in the re-point to "
                                   f"{row['new_slug']}"))
    return {"rewrite": rewrite, "quarantine": quarantine}


def content_loss(old: dict, new: dict, new_freq) -> dict:
    """What LEAVES the corpus with the old lexeme, said out loud rather than discovered later.

    A re-point in place has no survivor to append to — option (b) is the one that keeps both records
    — so nothing here can be salvaged INTO the new identity: 「pulmão」 is not a meaning of はい and
    carrying it would be worse than dropping it. What this function does is make the loss explicit
    and route every dropped fact into the ledger, which is the only place it survives.
    """
    lost, kept = [], []
    for s in old["senses"]:
        en = jloads(s["gloss_en"], []) or []
        pt = jloads(s["gloss_pt"], []) or []
        lost.append(f"sense {s['sense_order']} {s['pos']}: en={en} pt={pt or '(locale row)'}")
    for lt in old["sense_localized"]:
        lost.append(f"localized_text {lt['field']}/{lt['locale']}: {str(lt['value'])[:70]}")
    if (old["row"].get("notes_pt") or "").strip():
        lost.append(f"notes_pt: {old['row']['notes_pt'][:80]}")
    for p in old["pitch"]:
        if hira(p["reading"]) != hira(new["kana"]):
            lost.append(f"vocab_pitch {p['reading']} {p['accent_positions']} ({p['source']}) — the "
                        f"accent of a reading the record no longer has")
    if old["kanji"]:
        gone = [c for c in old["kanji"] if c not in new["headword"]]
        if gone:
            lost.append(f"vocab_kanji {gone} — kanji the new headword does not contain")
    if old["row"].get("freq_rank") != new_freq:
        lost.append(f"freq_rank {old['row'].get('freq_rank')} -> {new_freq} (re-derived for the new "
                    f"written form from {FREQ_TABLE}; the old number ranked the retired form)")
    for f in ("level", "level_confidence", "level_agreement", "level_sources", "introducing_topic_id"):
        kept.append(f"{f} = {old['row'].get(f)}")
    return {"lost": lost, "kept": kept}


def build_plan(con: sqlite3.Connection, row: dict, root: Path) -> dict:
    vid = row["vocab_id"]
    cur = con.execute("SELECT * FROM vocab WHERE id=?", (vid,)).fetchone()
    if cur is None:
        die(f"vocab row {vid} does not exist")
    if cur["slug"] != row["old_slug"] or cur["headword"] != row["old_headword"] \
            or cur["kana"] != row["old_kana"] or (cur["jmdict_ref"] or "") != row["old_jmdict_id"]:
        die(f"{row['old_slug']}: the record on disk is "
            f"{cur['slug']} {cur['headword']}/{cur['kana']} ref={cur['jmdict_ref']}, not the record "
            f"this migration was written against")
    clash = con.execute("SELECT id FROM vocab WHERE slug=? AND id!=?", (row["new_slug"], vid)).fetchone()
    if clash:
        die(f"{row['new_slug']} is already record {clash[0]} — that is a MERGE, not a re-point")

    e = target_entry(con, row["new_jmdict_id"])
    new = derive_record(e)
    hw_clash = con.execute("SELECT id, slug, level FROM vocab WHERE headword=? AND id!=?",
                           (new["headword"], vid)).fetchall()
    for s_i in range(len(new["senses"])):
        if (row["new_jmdict_id"], s_i) not in GLOSS_PT:
            die(f"{row['new_slug']}: no pt-BR gloss for sense {s_i}; a record cannot be published "
                f"with a locale object the contract requires and the data lacks")

    old_snapshot = {
        "row": {k: cur[k] for k in cur.keys()},
        "forms": [dict(r) for r in con.execute("SELECT * FROM vocab_form WHERE vocab_id=?", (vid,))],
        "senses": [dict(r) for r in con.execute(
            "SELECT * FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order", (vid,))],
        "sense_localized": [dict(r) for r in con.execute(
            "SELECT lt.* FROM localized_text lt JOIN vocab_sense vs ON vs.id=lt.entity_id "
            "WHERE lt.entity_type='vocab_sense' AND vs.vocab_id=?", (vid,))],
        "vocab_localized": [dict(r) for r in con.execute(
            "SELECT * FROM localized_text WHERE entity_type='vocab' AND entity_id=?", (vid,))],
        "pitch": [dict(r) for r in con.execute("SELECT * FROM vocab_pitch WHERE vocab_id=?", (vid,))],
        "kanji": [r[0] for r in con.execute(
            "SELECT k.character FROM vocab_kanji vk JOIN kanji k ON k.id=vk.kanji_id "
            "WHERE vk.vocab_id=? ORDER BY vk.position", (vid,))],
    }

    links = plan_links(con, vid, new)
    fams = plan_families(con, vid, new["headword"])
    old_ref, new_ref = f"vocab:{row['old_headword']}", f"vocab:{new['headword']}"
    refs = plan_refs(con, old_ref, new_ref) if old_ref != new_ref else \
        {"unlocks": [], "unlock_conflicts": [], "needs": [], "bodies": [], "cks": [], "cks_dup": []}
    uses = plan_reading_uses(con, vid, new)
    pitch_drop = [p["id"] for p in old_snapshot["pitch"] if hira(p["reading"]) != hira(new["kana"])]
    kanji_links = [(pos, ch) for pos, ch in enumerate(new["headword"])
                   if con.execute("SELECT 1 FROM kanji WHERE character=?", (ch,)).fetchone()]
    new_freq = freq_rank_for(root, new["headword"], new["kana"])
    return {"row": row, "cur": cur, "entry": e, "new": new, "old": old_snapshot, "links": links,
            "families": fams, "refs": refs, "reading_uses": uses, "pitch_drop": pitch_drop,
            "kanji_links": kanji_links, "old_ref": old_ref, "new_ref": new_ref, "freq": new_freq,
            "kanji_examples": plan_kanji_examples(con, vid, new["headword"], new["kana"]),
            "headword_clash": [dict(r) for r in hw_clash],
            "content_loss": content_loss(old_snapshot, new, new_freq)}


def check_preconditions(row: dict, plan: dict, exam: dict) -> list[str]:
    got = {
        "sentence_vocab": len(plan["links"]["sv_keep"]) + len(plan["links"]["sv_drop"]),
        "sentence_vocab_dropped": len(plan["links"]["sv_drop"]),
        "token": len(plan["links"]["token_keep"]) + len(plan["links"]["token_drop"]),
        "token_dropped": len(plan["links"]["token_drop"]),
        "lesson_unlocks": len(plan["refs"]["unlocks"]) + len(plan["refs"]["unlock_conflicts"]),
        "lesson_bodies": len(plan["refs"]["bodies"]),
        "cks": len(plan["refs"]["cks"]) + len(plan["refs"]["cks_dup"]),
        "family_dropped": len(plan["families"]["drop"]),
        "reading_uses_dropped": len(plan["reading_uses"]),
        "kanji_examples_dropped": len(plan["kanji_examples"]),
        "exam_rewritten": sum(1 for _f, _i, _c in exam["rewrite"]
                              if _c["vocab"] == row["new_slug"]),
        "exam_quarantined": sum(1 for _f, _i, it, _r in exam["quarantine"]
                                if it.get("vocab") == row["old_slug"]
                                or it.get("vocab_id") == row["vocab_id"]),
    }
    bad = [f"{row['old_slug']}: {k} is {got[k]}, the migration was written against {v}"
           for k, v in row["expect"].items() if got.get(k) != v]
    if plan["refs"]["unlock_conflicts"]:
        bad.append(f"{row['old_slug']}: {len(plan['refs']['unlock_conflicts'])} lesson(s) already "
                   f"unlock {plan['new_ref']} — that is a duplicate card, not a re-point")
    if plan["refs"]["cks_dup"]:
        bad.append(f"{row['old_slug']}: {len(plan['refs']['cks_dup'])} lesson(s) already carry "
                   f"{plan['new_ref']} in cumulative_known_set — the rewrite would collapse two "
                   f"words into one and shorten those known sets")
    if plan["headword_clash"]:
        bad.append(f"{row['old_slug']}: headword {plan['new']['headword']} is already the published "
                   f"headword of {plan['headword_clash']}")
    return bad


# ==================================================================================================
# applying
# ==================================================================================================
def apply_row(con: sqlite3.Connection, plan: dict) -> None:
    row, new, e = plan["row"], plan["new"], plan["entry"]
    vid, seq = row["vocab_id"], row["new_jmdict_id"]

    if not con.execute("SELECT 1 FROM raw_jmdict_entry WHERE ent_seq=?", (int(seq),)).fetchone():
        con.execute("INSERT INTO raw_jmdict_entry (ent_seq, common, data) VALUES (?,?,?)",
                    (int(seq), new["common"], jdumps(e)))
        for k in (e.get("kanji") or []):
            con.execute("INSERT INTO raw_jmdict_form (ent_seq, form, is_kana, is_common) "
                        "VALUES (?,?,?,?)", (int(seq), k["text"], 0, 1 if k.get("common") else 0))
        for k in (e.get("kana") or []):
            con.execute("INSERT INTO raw_jmdict_form (ent_seq, form, is_kana, is_common) "
                        "VALUES (?,?,?,?)", (int(seq), k["text"], 1, 1 if k.get("common") else 0))

    prev = jloads(plan["cur"]["repointed_from"] if "repointed_from" in plan["cur"].keys() else None,
                  []) or []
    con.execute(
        "UPDATE vocab SET slug=?, headword=?, kana=?, romaji=?, lexeme_type=?, verb_class=?, "
        "adj_class=?, common=?, freq_rank=?, jmdict_ref=?, source=?, notes_pt=NULL, needs_review=1, "
        "repointed_from=? WHERE id=?",
        (row["new_slug"], new["headword"], new["kana"], new["romaji"], new["lexeme_type"],
         new["verb_class"], new["adj_class"], new["common"], plan["freq"], seq, f"jmdict:{seq}",
         jdumps(prev + [row["old_slug"]]), vid))

    con.execute("DELETE FROM vocab_form WHERE vocab_id=?", (vid,))
    for k in (e.get("kanji") or []):
        con.execute("INSERT INTO vocab_form (vocab_id,form,is_kana,is_common,is_primary) "
                    "VALUES (?,?,?,?,?)", (vid, k["text"], 0, 1 if k.get("common") else 0,
                                           1 if k["text"] == new["headword"] else 0))
    for k in (e.get("kana") or []):
        con.execute("INSERT INTO vocab_form (vocab_id,form,is_kana,is_common,is_primary) "
                    "VALUES (?,?,?,?,?)",
                    (vid, k["text"], 1, 1 if k.get("common") else 0,
                     1 if (not new["kanji_forms"] and k["text"] == new["headword"]) else 0))

    old_sense_ids = [s["id"] for s in plan["old"]["senses"]]
    if old_sense_ids:
        qs = ",".join("?" * len(old_sense_ids))
        con.execute(f"DELETE FROM localized_text WHERE entity_type='vocab_sense' AND entity_id "
                    f"IN ({qs})", old_sense_ids)
    con.execute("DELETE FROM vocab_sense WHERE vocab_id=?", (vid,))
    for i, s in enumerate(new["senses"]):
        gloss_en = [g["text"] for g in s.get("gloss", []) if g.get("text")]
        # `misc_tags` and `field_tags` are written EMPTY, matching all 10,592 senses in the corpus
        # (exactly one carries anything). That is the queue's deferred finding F4, and it is not
        # W09's to close: `register` is derived from misc by export_corpus.REGISTER_MAP, and the
        # values these entries would produce (uk -> "usually-kana") are not in the design-owned
        # vocabulary contracts/vocab.schema.json publishes — "widening it is an edit there, never a
        # side effect". Storing them here would make these eight the only records with misc AND fail
        # the contract. The target's own tags are recorded in the ledger so nothing is lost.
        con.execute("INSERT INTO vocab_sense (vocab_id,sense_order,pos,field_tags,misc_tags,"
                    "gloss_en,gloss_pt,needs_review) VALUES (?,?,?,?,?,?,?,?)",
                    (vid, i, jdumps(s.get("partOfSpeech", [])), jdumps([]), jdumps([]),
                     jdumps(gloss_en), None, 1))
        sense_id = con.execute("SELECT id FROM vocab_sense WHERE vocab_id=? AND sense_order=?",
                               (vid, i)).fetchone()[0]
        con.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,"
                    "layer) VALUES ('vocab_sense',?,'gloss','pt-BR',?,1,'B')",
                    (sense_id, jdumps(GLOSS_PT[(seq, i)])))

    con.execute("DELETE FROM vocab_kanji WHERE vocab_id=?", (vid,))
    for pos, ch in plan["kanji_links"]:
        kid = con.execute("SELECT id FROM kanji WHERE character=?", (ch,)).fetchone()[0]
        con.execute("INSERT OR IGNORE INTO vocab_kanji (vocab_id,kanji_id,position) VALUES (?,?,?)",
                    (vid, kid, pos))

    for pid in plan["pitch_drop"]:
        con.execute("DELETE FROM vocab_pitch WHERE id=?", (pid,))

    for sid, _jp, _rule, _how in plan["links"]["sv_drop"]:
        con.execute("DELETE FROM sentence_vocab WHERE vocab_id=? AND sentence_id=?", (vid, sid))
    for tid, *_rest in plan["links"]["token_drop"]:
        con.execute("UPDATE token SET vocab_id=NULL WHERE id=?", (tid,))

    for fid, _slug, _type in plan["families"]["drop"]:
        con.execute("DELETE FROM family_member WHERE family_id=? AND member_type='vocab' AND "
                    "member_id=?", (fid, vid))

    for lesson_id, unlock_type in plan["refs"]["unlocks"]:
        con.execute("UPDATE lesson_unlocks SET ref=? WHERE lesson_id=? AND unlock_type=? AND ref=?",
                    (plan["new_ref"], lesson_id, unlock_type, plan["old_ref"]))
    for lesson_id, need_type in plan["refs"]["needs"]:
        con.execute("UPDATE lesson_needs SET ref=? WHERE lesson_id=? AND need_type=? AND ref=?",
                    (plan["new_ref"], lesson_id, need_type, plan["old_ref"]))
    for etype, eid, field, locale, value, _hits in plan["refs"]["bodies"]:
        con.execute("UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND "
                    "field=? AND locale=?", (value, etype, eid, field, locale))
    for lesson_id, value in plan["refs"]["cks"]:
        con.execute("UPDATE lesson SET cumulative_known_set=? WHERE id=?", (value, lesson_id))
    for slug, value in plan["reading_uses"]:
        con.execute("UPDATE reading SET uses=? WHERE slug=?", (value, slug))
    for krid, _ch, _reading, value in plan["kanji_examples"]:
        con.execute("UPDATE kanji_reading SET example_vocab_ids=? WHERE id=?", (value, krid))


def apply_exam_banks(root: Path, exam: dict, apply: bool) -> list[dict]:
    """Rewrite the projections, quarantine the rest into the ledger that already exists for it."""
    acts: list[dict] = []
    banks = root / "corpus" / "exam_banks"
    rewrite_by_file: dict[str, dict] = {}
    for fname, iid, changes in exam["rewrite"]:
        rewrite_by_file.setdefault(fname, {})[iid] = changes
    drop_by_file: dict[str, dict] = {}
    for fname, iid, item, reason in exam["quarantine"]:
        drop_by_file.setdefault(fname, {})[iid] = reason

    removed_path = banks / "removed_items.json"
    removed = jloads(removed_path.read_text(encoding="utf-8"), None) if removed_path.exists() else None
    if removed is None or "items" not in removed:
        die("corpus/exam_banks/removed_items.json is missing or not the {why,count,items} ledger")
    already = {json.dumps(x.get("item", {}).get("id")) for x in removed["items"]}

    for fname in sorted(set(rewrite_by_file) | set(drop_by_file)):
        path = banks / fname
        raw = path.read_text(encoding="utf-8")
        doc = json.loads(raw)
        kept, changed = [], []
        for it in doc:
            iid = it.get("id")
            if iid in drop_by_file.get(fname, {}):
                reason = drop_by_file[fname][iid]
                changed.append(f"quarantined {iid}: {reason}")
                if json.dumps(iid) not in already:
                    removed["items"].append({"file": fname, "reason": reason, "item": it})
                continue
            if iid in rewrite_by_file.get(fname, {}):
                ch = rewrite_by_file[fname][iid]
                before = {k: it.get(k) for k in ch}
                it.update(ch)
                changed.append(f"{iid}: {before} -> {ch}")
            kept.append(it)
        if changed:
            acts.append({"file": f"corpus/exam_banks/{fname}", "actions": changed})
            if apply:
                path.write_text(json.dumps(kept, ensure_ascii=False,
                                           indent=file_indent(raw)) + "\n",
                                encoding="utf-8", newline="\n")
    if apply and acts:
        removed["count"] = len(removed["items"])
        rraw = removed_path.read_text(encoding="utf-8")
        removed_path.write_text(json.dumps(removed, ensure_ascii=False,
                                           indent=file_indent(rraw)) + "\n",
                                encoding="utf-8", newline="\n")
    return acts


def rewrite_authoring(root: Path, rows: list[dict], plans: dict, apply: bool) -> list[dict]:
    """Re-point the loader's own inputs, so the next loader+export cycle cannot reintroduce them."""
    changes: list[dict] = []
    lessons = root / "research" / "derived" / "lessons"
    if not lessons.is_dir():
        print(f"  ! no {lessons} — authoring source not rewritten")
        return changes
    refmap = {plans[r["vocab_id"]]["old_ref"]: plans[r["vocab_id"]]["new_ref"]
              for r in rows if plans[r["vocab_id"]]["old_ref"] != plans[r["vocab_id"]]["new_ref"]}
    if not refmap:
        return changes
    for path in sorted(lessons.glob("*.json")):
        raw = path.read_text(encoding="utf-8")
        if not any(f'"{o}"' in raw or f'ref="{o}"' in raw for o in refmap):
            continue
        doc = json.loads(raw)
        acts: list[str] = []

        for old, new in refmap.items():
            for listname in ("unlocks", "needs", "feature_unlocks", "introduces"):
                items = doc.get(listname)
                if not isinstance(items, list):
                    continue
                has_new = any(isinstance(i, dict) and i.get("ref") == new for i in items)
                kept = []
                for i in items:
                    if isinstance(i, dict) and i.get("ref") == old:
                        if has_new:
                            acts.append(f"{listname}: dropped duplicate {old} ({new} already there)")
                            continue
                        i = {**i, "ref": new}
                        has_new = True
                        acts.append(f"{listname}: {old} -> {new}")
                    kept.append(i)
                doc[listname] = kept
            body = doc.get("body")
            if isinstance(body, str):
                for attr in ("ref", "item-ref"):
                    needle = f'{attr}="{old}"'
                    n = body.count(needle)
                    if n:
                        body = body.replace(needle, f'{attr}="{new}"')
                        acts.append(f'body: {n}x {attr}="{old}" -> "{new}"')
                doc["body"] = body

        after = json.dumps(doc, ensure_ascii=False)
        for old in refmap:
            for stray in (f'"{old}"', f'ref="{old}"'):
                if stray in after:
                    die(f"{path.name} still carries {stray} after the rewrite — an address shape "
                        f"this script does not know about. Fix the rewrite, do not ship half.")
        if acts:
            changes.append({"file": path.relative_to(root).as_posix(), "actions": acts})
            if apply:
                path.write_text(json.dumps(doc, ensure_ascii=False, indent=file_indent(raw)) + "\n",
                                encoding="utf-8", newline="\n")
    return changes


def is_applied(con: sqlite3.Connection, row: dict) -> bool:
    if not has_column(con, "vocab", "repointed_from"):
        return False
    r = con.execute("SELECT slug, repointed_from FROM vocab WHERE id=?", (row["vocab_id"],)).fetchone()
    return bool(r and r[0] == row["new_slug"] and row["old_slug"] in (jloads(r[1], []) or []))


# ==================================================================================================
def main() -> int:
    dbpath = db_target(ROOT / "db" / "corpus.sqlite")
    root_override = take_flag("--root")
    root = Path(root_override) if root_override else ROOT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write the migration (default: dry run)")
    ap.add_argument("--check", action="store_true", help="verify it is applied; exit 1 if not")
    args = ap.parse_args()

    con = sqlite3.connect(dbpath)
    con.execute("PRAGMA busy_timeout=60000")
    con.row_factory = sqlite3.Row

    print(f"db   : {dbpath}")
    print(f"root : {root}")
    print(f"mode : {'--check' if args.check else ('--apply' if args.apply else 'dry run')}")
    print()
    print("NOT RE-POINTED (the queue lists them; each is refused for the measured reason below):")
    for what, why in REFUSED:
        print(f"  - {what}\n      {why}")
    print()

    if args.apply and not has_column(con, "vocab", "repointed_from"):
        con.execute("ALTER TABLE vocab ADD COLUMN repointed_from TEXT")
        con.commit()

    if args.check:
        bad = [f"{r['old_slug']} -> {r['new_slug']}: not applied" for r in REPOINTS
               if not is_applied(con, r)]
        for r in REPOINTS:
            if con.execute("SELECT 1 FROM vocab WHERE slug=?", (r["old_slug"],)).fetchone():
                bad.append(f"{r['old_slug']} still resolves to a record")
        body = apply_body_fixes(con, root, False)
        bad += [f"prose still describes the retired lexeme: {x}" for x in body["applied"]]
        bad += [f"kanji example edge still wrong: {x}" for x in reconcile_kanji_examples(con, False)]
        for line in bad:
            print(f"  FAIL {line}")
        print("OK: every re-point is applied" if not bad else f"{len(bad)} problem(s)")
        return 1 if bad else 0

    def after_passes() -> dict:
        """The two passes that follow the re-points and are keyed on the DATA, not on `todo`.

        They run on every invocation and AFTER the addresses have moved, which is the only order
        that works in both directions: on a fresh rebuild the chips move first and these then find
        their anchors, and on an index an earlier version of this script already migrated they are
        the fix rather than a re-proof.
        """
        b = apply_body_fixes(con, root, args.apply)
        k = reconcile_kanji_examples(con, args.apply)
        print(f"\nprose beside a moved chip: {len(b['applied'])} to fix, "
              f"{len(b['already'])} already correct"
              + (f", {len(b['missing'])} not found" if b["missing"] else ""))
        for line in b["applied"]:
            print(f"   FIX  {line}")
        if b["missing"] and not args.apply and todo:
            print("   (a dry run measures the PRE-migration body, where a fix keyed on the moved "
                  "chip cannot match yet; --apply moves the chips first and then applies these)")
        for line in b["missing"]:
            print(f"   ?    {line}")
        for line in k:
            print(f"   FIX  {line}")
        if args.apply:
            con.commit()
        return {"prose_fixes": b, "kanji_example_edges_dropped": k}

    todo = [r for r in REPOINTS if not is_applied(con, r)]
    for r in REPOINTS:
        if r not in todo:
            print(f"SKIP {r['old_slug']} -> {r['new_slug']}: already applied")
    if not todo:
        post = after_passes()
        # Keep the durable ledger honest even when the re-points themselves are already applied:
        # these two passes can land on a later run than the addresses did.
        lp = root / LEDGER
        if args.apply and lp.exists():
            led = jloads(lp.read_text(encoding="utf-8"), {}) or {}
            led["prose_fixes"] = ledger_prose()
            led["kanji_example_rule"] = KEX_RULE
            led["kanji_example_edges_dropped_this_run"] = post["kanji_example_edges_dropped"]
            lp.write_text(json.dumps(led, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
            print(f"ledger refreshed -> {LEDGER}")
        print("\nnothing else to do")
        return 0

    plans = {}
    for r in todo:
        plans[r["vocab_id"]] = build_plan(con, r, root)
    exam = plan_exam_banks(root, todo, plans)

    # A PARTIAL index (validate_index_rebuildable --quick reconstructs one family only) has empty
    # lesson / sentence / exam tables, so every row-count expectation written against the real index
    # is out of scope there — the plan functions simply find no rows to move. Preconditions are a
    # drift check for the REAL index and the full rebuild, both of which populate every table; a
    # partial index is recognised by its empty lesson table, the same way W08 recognises it.
    partial = con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0] == 0
    if partial:
        print("partial index (no lessons) — preconditions out of scope for this run\n")

    problems = []
    for r in todo:
        if partial:
            continue
        problems += check_preconditions(r, plans[r["vocab_id"]], exam)
    for line in problems:
        print(f"  PRECONDITION {line}")
    if problems:
        die(f"{len(problems)} precondition(s) do not hold; nothing was written")

    ledger = {"why": ("W09 / owner decision A9. Every record re-pointed to the JMdict entry its "
                      "JLPT list slot names, with the complete pre-migration record kept here "
                      "because a re-point IN PLACE overwrites the old lexeme rather than retiring "
                      "it to a row of its own."),
              "generated_by": "scripts/migrate_vocab_repoint.py",
              "repointed": [], "refused": [{"record": w, "why": y} for w, y in REFUSED]}

    for r in todo:
        p = plans[r["vocab_id"]]
        ledger["repointed"].append({
            "vocab_id": r["vocab_id"], "old_slug": r["old_slug"], "new_slug": r["new_slug"],
            "old": f"{r['old_headword']}/{r['old_kana']}",
            "new": f"{p['new']['headword']}/{p['new']['kana']}",
            "list_says": r["list_says"], "evidence": r["evidence"],
            "retired_lexeme_belongs_at": r["retired_lexeme_belongs_at"],
            "retired_record": p["old"],
            "content_loss": p["content_loss"]["lost"],
            "carried_unchanged": p["content_loss"]["kept"],
            "freq_rank": {"old": p["old"]["row"].get("freq_rank"), "new": p["freq"],
                          "rule": f"re-derived from {FREQ_TABLE} by build_frequency.py's own rule"},
            "target_tags_not_stored": [
                {"sense": i, "misc": s.get("misc", []), "field": s.get("field", []),
                 "info": s.get("info", [])}
                for i, s in enumerate(p["new"]["senses"])
                if s.get("misc") or s.get("field") or s.get("info")],
            "references": {
                "sentence_vocab_kept": len(p["links"]["sv_keep"]),
                "sentence_vocab_dropped": [
                    {"sentence_id": s, "jp": jp, "link_rule": lr, "evidence": how}
                    for s, jp, lr, how in p["links"]["sv_drop"]],
                "token_kept": len(p["links"]["token_keep"]),
                "token_dropped": [{"token_id": t, "sentence_id": s, "surface": su, "lemma": le,
                                   "reading": re_} for t, s, su, le, re_ in p["links"]["token_drop"]],
                "lesson_unlocks": p["refs"]["unlocks"],
                "lesson_needs": p["refs"]["needs"],
                "lesson_bodies": [(e, i, f, lo, h) for e, i, f, lo, _v, h in p["refs"]["bodies"]],
                "cumulative_known_set": len(p["refs"]["cks"]),
                "family_kept": p["families"]["keep"], "family_dropped": p["families"]["drop"],
                "reading_uses_dropped": [s for s, _v in p["reading_uses"]],
                "kanji_reading_examples_dropped": [f"{c} / {r}" for _i, c, r, _v in p["kanji_examples"]],
                "pitch_dropped": p["pitch_drop"],
                "old_ref": p["old_ref"], "new_ref": p["new_ref"],
            },
        })
        print(f"\n{r['old_slug']} {r['old_headword']}/{r['old_kana']}  ->  {r['new_slug']} "
              f"{p['new']['headword']}/{p['new']['kana']}")
        print(f"   list says   : {r['list_says']}")
        print(f"   refs        : sentence_vocab {len(p['links']['sv_keep'])} kept / "
              f"{len(p['links']['sv_drop'])} dropped; token {len(p['links']['token_keep'])} kept / "
              f"{len(p['links']['token_drop'])} dropped; unlocks {len(p['refs']['unlocks'])}; "
              f"bodies {len(p['refs']['bodies'])}; cks {len(p['refs']['cks'])}; "
              f"families {len(p['families']['keep'])} kept / {len(p['families']['drop'])} dropped; "
              f"reading.uses -{len(p['reading_uses'])}; kanji examples "
              f"-{len(p['kanji_examples'])}; pitch -{len(p['pitch_drop'])}")
        print(f"   senses      : {len(p['old']['senses'])} retired -> {len(p['new']['senses'])} "
              f"from JMdict {r['new_jmdict_id']} (pt-BR re-authored, needs_review=1)")
        print("   content lost with the retired lexeme (kept only in the ledger):")
        for line in p["content_loss"]["lost"]:
            print(f"       - {line}")
        print(f"   carried unchanged: {'; '.join(p['content_loss']['kept'])}")

    exam_acts = apply_exam_banks(root, exam, args.apply)
    speak_acts = apply_speak_files(plan_speak_files(root, todo, plans), args.apply)
    auth_acts = rewrite_authoring(root, todo, plans, args.apply)
    ledger["exam_banks"] = exam_acts
    ledger["speak_units"] = speak_acts
    ledger["authoring_source"] = auth_acts
    print(f"\nexam banks : {sum(len(a['actions']) for a in exam_acts)} item action(s) across "
          f"{len(exam_acts)} file(s)")
    print(f"speak units: {sum(len(a['actions']) for a in speak_acts)} ref/surface action(s) across "
          f"{len(speak_acts)} file(s)")
    print(f"authoring  : {sum(len(a['actions']) for a in auth_acts)} action(s) across "
          f"{len(auth_acts)} file(s)")

    if not args.apply:
        after_passes()
        print("\ndry run — nothing written. Re-run with --apply.")
        return 0

    for r in todo:
        apply_row(con, plans[r["vocab_id"]])
    con.commit()
    post = after_passes()
    ledger["prose_fixes"] = ledger_prose()
    ledger["prose_fixes_applied_this_run"] = post["prose_fixes"]["applied"]
    ledger["kanji_example_rule"] = KEX_RULE
    ledger["kanji_example_edges_dropped_this_run"] = post["kanji_example_edges_dropped"]

    left = [r["old_slug"] for r in todo
            if con.execute("SELECT 1 FROM vocab WHERE slug=?", (r["old_slug"],)).fetchone()]
    if left:
        die(f"old slugs still resolve after the write: {left}")

    lp = root / LEDGER
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8", newline="\n")
    print(f"\napplied {len(todo)} re-point(s); ledger -> {LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
