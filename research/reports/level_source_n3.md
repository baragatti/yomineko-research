# A third, independent JLPT level source for N3 and above (owner item D12)

> Unit `level_source_n3`, 2026-09-27. Research only: nothing in the corpus changed. Numbers come from a
> snapshot of `db/corpus.sqlite` taken today and from the raw list files already under
> `research/datasets/`. Script: scratchpad `res0927/level_source_n3/measure.py`. Machine-readable
> candidate table: `research/derived/pending/level_source_n3_candidates.json`.

## 1. Answer first

D12 is not a giant task, but it is a different task from the one the question assumes. The corpus does
not have "two lists at N3 and needs a third". Measured on the files, **every JLPT list we use at N3,
for kanji as well as vocab, is the same lineage: Jonathan Waller's tanos.co.uk lists.** The three-list
N3 kanji consensus (`3/3`, confidence 1.0 on 340 records) is three copies of one list.

So the useful work is:

1. **Count lineages, not repos.** Write down which list descends from which upstream, and compute
   agreement over lineages. This is documentation plus one recompute, about half a day.
2. **Add one genuinely independent lineage per dimension.** The best candidates are academic
   Japanese-teaching lists that were graded by experienced teachers against corpora, with no Tanos
   ancestry:
   - vocab: **日本語教育語彙表 (JEV)**, 17,908 words in 6 levels;
   - grammar: **はごろも (Hagoromo)**, 1,848 function-word items in 6 levels;
   - kanji: no licensable independent *new*-JLPT list was found. **KANJIDIC2's pre-2010 JLPT field**
     (the old official test specification, already on disk) works as an upper/lower bound check, not
     as a vote.
3. **The licence is the blocker, not the engineering.** JEV and Hagoromo permit research and
   education use only. This repo is research, so we can ingest and measure them as *audit-only*
   evidence today. Before their votes reach the exported `level_sources` that the product ships,
   they need written permission from the authors. That's an owner action (one email each).

Effort: about 3 to 4 agent-days in total, plus however long the permission replies take (§6).

## 2. What the corpus holds today (snapshot 2026-09-27)

| entity, level | records | `level_agreement` | `level_sources` |
|---|---:|---|---|
| kanji N3 | 340 | `3/3` | `{davidluzgouveia, kanjiapi, bluskyo}: n3` |
| kanji N3 | 8 + 2 | `anchor` / `0` | editorial placements |
| kanji N2 | 355 / 13 | `4/4` / `1/4` | four repos |
| kanji N1 | 984 / 149 | `4/4` / `1/4` | four repos |
| vocab N3 | 1,593 | `1/3` | `{"bluskyo": "n3"}` |
| vocab N2 / N1 | 1,768 / 2,677 | `1/3` | collapsed `jlpt-lists` key (gap G5) |
| grammar N3 | 132 | `1/3` | `{"hanabira": "n3"}` |

## 3. Lineage audit: the lists we use are not independent

### 3.1 Kanji N3: three repos, one list

Pairwise overlap of the N3 kanji sets on disk:

| pair | sizes | shared | Jaccard |
|---|---|---:|---:|
| davidluzgouveia (`jlpt_new=3`) ~ kanjiapi (`jlpt-3`) | 367 / 367 | 367 | **1.000** |
| davidluzgouveia ~ bluskyo | 367 / 367 | 367 | **1.000** |
| kanjiapi ~ bluskyo | 367 / 367 | 367 | **1.000** |
| any of them ~ anchori | 367 / 370 | 367 | 0.992 |

The sets are identical to the character. The provenance agrees with the numbers:

- davidluzgouveia/kanji-data credits its updated levels to "Jonathan Waller's JLPT Resources page"
  (README, <https://github.com/davidluzgouveia/kanji-data>, read 2026-09-27).
- Bluskyo/JLPT_Vocabulary is a parse of tanos.co.uk (already recorded in `research/datasets/jlpt/MANIFEST.md`).
- kanjiapi.dev documents no source for its JLPT field. KANJIDIC2 only carries the *old* 4-level
  field, so kanjiapi's new 5-level field has to come from somewhere else, and it matches Waller's
  list exactly. I infer that it is Waller too. Not confirmed by the maintainer.
- AnchorI documents no source. It is a superset of the same 367 plus 3 characters.

`design/n3_extension_assessment.md` said N3 kanji had "2 genuinely-independent lineages" (Tanos and
"KANJIDIC2/kanjiapi re-leveling"). The davidluzgouveia README contradicts that. **The 340 `3/3` @ 1.0
records overstate their evidence.** Under a lineage count they are `1/1`, one lineage and no
dissent.

### 3.2 Vocab N3: every open list is Tanos

| pair (headword+reading) | sizes | shared | Jaccard |
|---|---|---:|---:|
| bluskyo ~ jlptvocabapi | 1,835 / 1,797 | 1,566 | 0.758 |
| bluskyo ~ elzup | 1,835 / 2,139 | 1,627 | 0.693 |
| elzup ~ openanki | 2,139 / 2,140 | 2,139 | 0.9995 |

- elzup and open-anki are the same file. Their tags (`JLPT JLPT_2 JLPT_3` on 1,646 rows,
  `JLPT_1 JLPT JLPT_3` on 218) show they were split from Tanos's *old*-test lists.
- jlptvocabapi and bluskyo are both new-test Tanos. They differ at the edges because of
  parsing and orthography, not because anyone judged the words differently.
- 1,592 of the 1,593 corpus N3 vocab records also appear, by form, in jlptvocabapi N3, and 1,575 in
  the old-split N3 file. The `1/3` agreement string says "the other two lists were silent", and
  that's wrong in both directions. They weren't silent, and they wouldn't count as independent
  votes even if we recorded them.
- Jisho's JLPT tags are Waller's too: "Information about what word and kanji belong to which JLPT
  level comes from Jonathan Waller's JLPT Resources page" (<https://jisho.org/about>, read
  2026-09-27). Jisho cannot serve as a separate source.

### 3.3 Grammar N3

`hanabira` is the only list. Its README cites the Nihongo Sō-matome series as literature
(<https://github.com/tristcoil/hanabira.org>, read 2026-09-27), so it probably descends from a
textbook rather than Tanos. That makes it a real lineage, but only one.

### 3.4 Beyond N3 (flagged, not measured here)

The same repos supply N5/N4 and N2/N1. The kanji evidence at every level is very likely one Waller
lineage wearing four names, and the N5/N4 "4 independent vocab lists" in the manifest include at
least three Tanos derivatives. This unit did not measure N5/N4. The lineage map in §5 step 1 would
apply to every level at once.

## 4. Candidates for an independent source

Full table with licences, URLs and coverage: `research/derived/pending/level_source_n3_candidates.json`.
Summary:

| candidate | dims | independent of Tanos? | N3+ coverage | licence for use as evidence | verdict |
|---|---|---|---|---|---|
| **日本語教育語彙表 JEV** (Sunakawa et al., KAKENHI 2011–14) | vocab | **yes**. Graded by experienced teachers against BCCWJ and a 100-textbook corpus | 17,908 words, 6 levels, 中級前半 ≈ N3 | research/education only; no commercial use; no redistribution; citation required | **best vocab candidate**; audit-only until permission |
| **はごろも Hagoromo** (Hori, Lee, Hasebe; Ver.4, 2024-03) | grammar | **yes**. Five raters assigned 6 levels; items drawn from 5 sources including the old test spec | 1,848 items | research/education only (per the J-STAGE paper summary); the site states no terms; download needs a form | **best grammar candidate**; confirm terms by email |
| KANJIDIC2 `jlptLevel` (old 1–4, EDRDG, CC BY-SA 4.0) | kanji | partly. It is the pre-2010 official spec, which is the *ancestor* of Tanos's new levels, not a sibling | all 350 N3 kanji have a value | fine; already ingested | use as a **bound check**, not a vote (§5 step 2) |
| Marugoto word lists (Japan Foundation, A1–B1) | vocab | yes | small; CEFR, not JLPT; B1 ≈ N3 at best | JF copyright | weak; skip |
| JLPT Sensei | vocab, kanji, grammar | unknown lineage | full N5–N1 | all rights reserved; the terms page returned 404 | not usable without a licence |
| Bunpro | grammar | yes (editorial) | full | general "protected by copyright" ToS | not usable without a licence |
| Nihongo-Pro, Kanshudo | all | unknown | full | proprietary | not usable without a licence |
| Shin Kanzen Master / Sō-matome / TRY! N3 | vocab, grammar | yes (publisher editorial) | partial (book TOCs, indexes) | copyrighted; membership-as-fact is arguable; manual transcription | expensive; last resort |
| JLPT Tango N3 Anki decks | vocab | yes (publisher) | full | the decks reproduce a copyrighted book | reject |
| Jisho tags, elzup, open-anki, jlptvocabapi, AnchorI | all | **no**. Tanos, or identical to it | full | fine | already counted as the Tanos lineage |
| Official 公式問題集 (JEES) | vocab, grammar | yes, and authoritative | a few hundred items per level | copyrighted | too thin to vote; could spot-check |

Sources for the JEV and Hagoromo rows:
- JEV site and terms: <https://jhlee.sakura.ne.jp/JEV/> and <https://jreadability.net/jev/>, read
  2026-09-27. The terms say 「研究・教育のための利用に限定します」 and 「二次配布はご遠慮ください」.
- Hagoromo: <https://hgrm.jpn.org/> and the J-STAGE paper
  <https://www.jstage.jst.go.jp/article/mathling/30/5/30_275/_article/-char/ja/>, read 2026-09-27.
- Tanos licence, CC BY, commercial use allowed with credit: <https://www.tanos.co.uk/jlpt/sharing/>,
  read 2026-09-27.

## 5. What the change would look like

### Step 1: lineage map, over current data (no new source, about 0.5 day)

Add a `list → lineage` table to `design/schema_v2.md`, for example tanos = {bluskyo, elzup,
openanki, jlptvocabapi, davidluzgouveia, kanjiapi (inferred), anchori (inferred)}, hanabira =
{hanabira}. Compute the agreement denominator over **lineages consulted**, not repos. `level_sources`
keeps the per-repo keys (they are still true history). Only the agreement string and confidence
change, and that goes through the `apply_level_evidence.py` exact-precondition path.

**Owner decision needed on direction.** A one-lineage N3 record is honestly `1/1`. Raising 1,593
vocab records from 0.34 to 1.0 would repeat the trap A4 avoided. The proposed rule: with fewer than 2
lineages consulted, confidence is capped at 0.5 and `needs_review` stays. Under that rule the 340 N3
kanji records fall from 1.0 to 0.5. That is the honest number, but it is a visible downgrade.

### Step 2: KANJIDIC2 old-level bound check (data on disk, about 0.5 day, advisory validator)

The old test mapped to the new one as follows: old 4 → N5, old 3 → N4, old 2 → N3 or N2, old 1 → N1.
On today's data:

| corpus level | KANJIDIC2 old level distribution |
|---|---|
| N5 (103) | 4: 103 |
| N4 (177) | 3: 177 |
| N3 (350) | **2: 344**, 3: 4, 1: 2 |
| N2 (368) | 2: 350, 1: 9, none: 9 |
| N1 (1,133) | 1: 945, 2: 45, none: 143 |

The check flags **6 N3 kanji**: 回 (old 3, list `3/3`), 掛 and 幾 (old 1, list `3/3`), and 正, 通, 歩
(old 3, editorial `anchor`). It also flags 45 N1 kanji that were old level 2 and 9 N2 kanji that were
old level 1. This bound is the only non-Tanos kanji evidence on disk. It can't pick N3 over N2, but it
catches cliffs.

### Step 3: JEV vocab vote (about 1 day after the file is in hand)

- Mapping: 初級前半 → n5, 初級後半 → n4, **中級前半 → n3**, 中級後半 → n2, 上級前半/後半 → n1.
  JEV bands are pedagogical, not JLPT. Record the mapping in the manifest and treat a vote one band
  away as *dissent*, never as agreement.
- Matching: reuse `norm_candidates` + `match_entry` from `scripts/ingest/ingest_n3.py` (JMdict form
  plus reading) unchanged.
- Storage: while the licence is unresolved, the votes live in `research/derived/pending/` as an
  audit table and are **not** merged into the exported `level_sources`. Once permission arrives, they
  merge as `"jev": "<level>"` and the N3 vocab panel becomes {tanos, jev}.
- Projected effect on the 1,593 N3 vocab records: each goes to `2/2` (JEV agrees), `1/2` (JEV
  silent, or the word is outside its 17,908 headwords), or `1/2` + conflict (JEV places it elsewhere,
  so it goes to a review queue). **The split was not measured.** Measuring it needs the JEV .xlsx, and
  this unit was not allowed to download files. It's about 10 minutes once the file is present.
  Earliest-level-wins means a JEV 初級 vote could pull a word down into N4. Those words must be queued
  for review, not moved automatically, because the N5/N4 course is frozen.

### Step 4: Hagoromo grammar vote (about 1.5–2 days)

Matching 132 N3 grammar keys to Hagoromo headwords is fuzzy (〜ばかりか vs ばかりでなく), so it needs a
proposal table, an Opus verifier and an exclusion rule for null verdicts (memory: *pending tables and
dead verifiers*). Hagoromo has six levels (初級, 初中級, 中級, 中上級, 上級, 超級). 中級 ≈ N3 is the
weakest mapping of the three steps and has to be documented as such.

## 6. Effort and recommendation

| step | effort | blocked on | lifts |
|---|---|---|---|
| 1 lineage map + recompute | 0.5 day | owner: confidence-cap rule | honesty of all level evidence, all levels |
| 2 KANJIDIC2 bound check | 0.5 day | nothing | 6 N3 + 54 N2/N1 kanji flagged |
| 3 JEV vocab | 1 day (+ download) | download approval now; author permission before export | 1,593 N3 + 4,445 N2/N1 vocab get a second lineage |
| 4 Hagoromo grammar | 1.5–2 days | terms confirmation; form download | 132 N3 grammar get a second lineage |

**Recommendation.** Do steps 1 and 2 now. Neither needs a new source, and both correct a claim the
corpus currently overstates. In parallel, the owner emails the JEV group (日本語学習辞書支援グループ,
via the JEV site) and Hagoromo (contact on hgrm.jpn.org) asking permission to use level
*assignments* as evidence in a commercial learning product, with citation and without redistributing
their content. Then ingest JEV as audit-only evidence. The measurement and the conflict queue are
research use, which the terms allow, and they don't have to wait for the reply.

That gives two independent lineages for N3 vocab and grammar, not three. No third open, licensable,
non-Tanos JLPT list exists for N3 that I could find. Paying for one (JLPT Sensei, Bunpro, Nihongo-Pro)
buys a vote of unknown lineage. Spec §1.5's "≥3 independent lists" should be restated as
"≥2 independent lineages where they exist, with lineage recorded", which is what the data can
actually support.
