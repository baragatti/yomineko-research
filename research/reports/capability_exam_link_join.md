# Capability exam_link join: resolve unlock refs the way the exporter does

Status: **APPLIED 2026-09-23 by Q1-exam-fixes-3** (`research/reports/q1_exam_fixes_3_report.md`:
3,079 -> 634 unlinked on the 4,871-item banks). Originally: pending, nothing applied. Patch `research/derived/patches/capability_exam_link_join.patch`
touches only `scripts/export/build_capabilities.py` (`git apply --check` passes on the current tree; that
file is unchanged from HEAD). Measured 2026-09-23 on a `git archive HEAD` tree (7ffdd6d0) and an sqlite
backup of `db/corpus.sqlite`. The unpatched build on that snapshot reproduces HEAD's
`corpus/capabilities/registry.json` and `lesson_map.json` exactly, so every delta below comes from
the patch.

## The defect and the fix

`build_capabilities.py` read `lesson_unlocks.ref` raw and joined it to the banks' `vocab:<jmdict_id>`.
In the DB, 2,897 of 2,951 vocab unlock refs are still in authoring form (`vocab:<headword>`). Only the
54 already-slug refs could ever match.

The fix is one line plus the import. Each unlock ref now goes through `export_course._deref(con, ref,
lesson_id)`, the function the exporter uses to write `unlocks` into the course JSON. It calls
`VocabIdentity.resolve` with the same lesson level and slug. `apply_card_examples.py` and
`apply_card_production_keys.py` already import `_deref` the same way. With no printed-reading hint on an
unlock, the resolver goes through ruling, then the per-lesson cache, then its tiers. The cache only holds
results computed from the same inputs, so the answer does not depend on call order.

Cross-check: for all 313 lessons that have unlocks, the resolved unlock list equals the `unlocks` in
HEAD's `course/**/lesson-*.json` (0 mismatches).

## Other namespaces: none has the split

| namespace | DB unlock refs | rewritten by `_deref` | bank side |
|---|---|---|---|
| vocab | 2,951 (2,897 headword, 54 slug) | 2,897 | `vocab` 3,015 items, all published slugs |
| kanji | 634, all `kanji:<character>` | 0 (already the published address) | banks carry no kanji ref |
| grammar | 486, all live keys (no deprecated) | 0 | `grammar` 944 items, all live keys |
| kana-family / conjugation-form / feature | 57 / 25 / 14 | 0 | not referenced by items |
| sentence | n/a | n/a | every bank `sentence` slug exists in the DB |
| reading | n/a | n/a | every `reading` has a `gated_to_lesson` that is a lesson in `lesson_map` |

## exam_link before / after, per capability kind

Item-provenance links, counted as (item, capability) pairs. Exam-readiness uses `via: paper` and is
byte-identical before and after.

| kind | caps | caps with exam_link before | after | rows before | after | item-links before | after |
|---|---|---|---|---|---|---|---|
| grammar | 72 | 72 | 72 | 570 | 430 | 2,128 | 1,756 |
| script | 3 | 1 | 1 | 12 | 12 | 388 | 2,269 |
| vocabulary | 44 | 42 | **43** | 147 | 335 | 646 | 3,516 |
| phonology | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| study-method | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **all (INDEX.md)** | 125 | 118 | **119** | 768 | **816** | | |

The newly linked capability is `cap:vocab:pre-n5-saudacoes`, one of W24's two "real gaps". The other
one, `cap:vocab:n4-kanji-exame`, is still unlinked. Its single vocab unlock (in `les:n4-kanji-exame-05`)
is not the `vocab` of any bank item, so this gap is real, not a join artifact.

## Per exam family

Items whose `vocab` reaches a `cap:vocab:*`, all levels combined:

| family | items | with `vocab` | vocab-linked before | after |
|---|---|---|---|---|
| context_fill | 955 | 955 | 64 | 955 |
| kanji_reading | 976 | 976 | 31 | 976 |
| orthography | 977 | 977 | 41 | 977 |
| paraphrase | 52 | 52 | 2 | 52 |
| usage | 55 | 55 | 2 | 55 |

exam_link item-links per family, summed over capabilities, with the change by kind:

| family | before | after | change by kind |
|---|---|---|---|
| context_fill | 374 | 955 | vocabulary 64 -> 955, grammar 310 -> 0 |
| kanji_reading | 62 | 1,952 | vocabulary 31 -> 976, kanji-recognition 31 -> 976 |
| orthography | 82 | 1,954 | vocabulary 41 -> 977, kanji-recognition 41 -> 977 |
| paraphrase | 33 | 52 | vocabulary 2 -> 52, grammar 31 -> 0 |
| usage | 33 | 55 | vocabulary 2 -> 55, grammar 31 -> 0 |
| reading_comp | 761 | 757 | vocabulary 282 -> 278 |
| text_grammar | 798 | 797 | vocabulary 224 -> 223 |
| grammar_form / sentence_order / listening_reply | 714 / 241 / 64 | same | none |

Bank items that reach no capability: **3,185 -> 634** of 5,141. What is left:

- 171 listening items (gist 9, point 57, say 42, task 63), which carry no ref by design.
- 13 listening_reply and 447 sentence_order items whose sentence has no `sentence_grammar` rows.
  That is a data gap in the dissection, not a join defect.
- 3 n4 reading_comp items (`rc:n4:n4-revisao-0{1,2,3}-01`), gated to revisão lessons whose only
  capability is exam-readiness, which the item rule excludes.

On the current working-tree banks (5,103 items, uncommitted), the same patch gives the same unlinked
count, 3,185 -> 634, and rows go 772 -> 820.

### Grammar links lost: 372 (context_fill, paraphrase, usage)

The W24 item rule falls back to the sentence's `sentence_grammar` keys only when nothing else links.
Before the fix, the vocab leg failed on these items, so the fallback credited grammar capabilities
with 372 links. Once the word resolves, the fallback no longer fires. These items test a word, so
the new attribution is the intended one. No grammar capability loses its last link (72 of 72 are still
linked). If the owner wants grammar credit for these families as well, the sentence leg would have to
become additive. That is a rule change and it is not in this patch.

## W24 probe: kanji_reading + orthography test a taught word

Taught means the item's `vocab` is unlocked by a lesson at or below the bank's level.

| bank | items | taught, raw DB refs (W24's join) | taught, resolved |
|---|---|---|---|
| n5_kanji_reading | 176 | 11 | 176 |
| n5_orthography | 177 | 13 | 177 |
| n4_kanji_reading | 400 | 12 | 400 |
| n4_orthography | 400 | 15 | 400 |
| n3_kanji_reading | 400 | 8 | 400 |
| n3_orthography | 400 | 13 | 400 |
| **total** | **1,953** | **72 (3.7%)** | **1,953 (100%)** |

W24's 3.7% reproduces exactly under the raw join and becomes 100% under the fixed one. This agrees with
`exam_taught_word_rule.md`. `cap:kanji-recognition` goes from 388 to 2,269 item-links: all 1,953
kanji/orthography items, plus the 316 it already had through reading items.

## Registry fields other than exam_link

They are **not all byte-identical**, and the difference is a correction. Put the before values of
`exam_link` and `lessons` back into the patched registry and the file is byte-identical to the
unpatched output. Capability ids, their order, `kind`, `name`, `level`, `grammar_keys`, `can_do*` and
provenance fields do not change. Swapping back `exam_link` alone is not enough, because three `lessons`
arrays shrink:

| capability | lesson removed | ref | before, keyed by headword | after, keyed by record |
|---|---|---|---|---|
| cap:vocab:n5-verbos | les:n4-condicionais-01 | 開く -> vocab:1202440 ひらく (n4) | n5 あく's topic | n4-condicionais |
| cap:vocab:n5-desu-wa | les:n4-condicionais-07 | 家 -> vocab:1191750 け (n4) | n5 いえ's topic | n4-condicionais |
| cap:vocab:n5-desu-wa | les:n4-oracoes-relativas-01 | 彼 -> vocab:1483070 かれ (n4) | n5 あれ's topic | n4-oracoes-relativas |
| cap:vocab:n5-rotina | les:n4-experiencia-04 | 米 -> vocab:1508750 こめ (n4) | n5 メートル's topic | n4-experiencia |

Keying `vocab_topic` by headword merged each homograph pair. The n4 lesson that teaches the second
record was then said to introduce the n5 capability of the first. `lesson_map.json` changes in the
same four entries: each loses one `cap:vocab:n5-*` and gains nothing, because the lesson already had
its own topic's vocab capability. None of the four is quoted in a `can_do_derived_from`, so the build
reports no failures. Which record each ref names is the exporter's decision and matches the course
export. If 家 -> け in n4-condicionais-07 is the wrong sense, the fix belongs in
`homograph_rulings.json`, not in this build.

`corpus/capabilities/INDEX.md` changes on one line: `exam_link: 119 capabilities, 816 rows`.

## Checks run

- `validate_capabilities.py --db <snapshot>` on the patched output: ALL OK (125 caps, 322 lessons).
  It imports `build_capabilities`, so it now pulls in `export_course` too; the import resolves.
- Applying the patch to HEAD's file gives exactly the script that was measured.
- The writer chain runs `build_capabilities.py` on the live DB. After applying, re-run it and commit
  `corpus/capabilities/*` together with the patch.
