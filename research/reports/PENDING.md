# Pending work — decisions, campaigns, mechanical items

Written 2026-09-01 after both QA waves completed (26 auditors, 20 reports under `qa_sweep/`) and six
repair campaigns landed. Gate green at 39 hard validators. **The bottleneck is no longer finding
defects; it is deciding on them.** Section A needs you. B and C are being run now.

How to read: each A item gives the question, the evidence, the options with a recommendation, and
what the decision unblocks. Detail lives in the report named at the end of each item.

---

## A. Decisions only you can make

### A1. Exam reading passages are not passages
**Question.** What should `text_grammar` and `reading_comp` sections be built from?
**Evidence.** The n5 and n3 banks (n5: 33 + 43 items; n3: 94 + 152) draw on "passages" that are
5–6 unrelated Tatoeba sentences concatenated (「ネズミでした。こんにちは。」). Neither section can test
what its JLPT counterpart tests. The *builder* concatenates, so regeneration reproduces the defect
and per-item repair cannot touch it.
**Options.** (a) Author real short passages as Layer C with `needs_review: true`, built from
known-set vocabulary per level — a content project, ~40–60 passages. (b) Drop both sections from the
paper until (a) exists; the paper spec in `design/exam_simulator.md` changes. (c) Keep as-is, label
them "sentence grammar" not "text grammar" — honest but weaker.
**Recommendation.** (b) now, (a) as the next authored campaign. Shipping a section that cannot
function as its type is worse than a shorter paper.
**Unblocks.** A2 — this must be settled before regeneration or it gets baked in.
Detail: `qa_sweep/exam_japanese_1.md`, `exam_japanese_3.md`.

### A2. Exam bank regeneration
**Question.** GO/NO-GO on regenerating all 40 banks, and with which builder fixes.
**Evidence.** Prototype measured: NO-GO as the builder stands (93 leak items return, provenance
stripped); GO after nine enumerated fixes — affix-solvable items 373→58, leaks 95→0, zero
unexplained diffs. The QA waves added builder defects the plan must absorb: the n3 linker matched
written form and ignored reading (空/から used for six *sky* sentences, 時/とき for the じ counter ×26,
金/きん for かね — 135 items, two broken keys); blanks that cut a word in half (44 n4 + 15 n3);
options that are not Japanese (grammar-point labels, leaked sense indices — 103 n4); sentence_order
on bare morphemes instead of bunsetsu (45 items accept a second ordering); 37 n5 orthography items
keyed three ways over identical option sets (あつい → 暑い/熱い/厚い).
**Options.** GO with the nine fixes + the linker-reading fix + bunsetsu chunking + homophone-set
dedupe; or hold and keep patching in place.
**Recommendation.** GO, after A1. ~1,700 flagged items ride on this; in-place patching does not scale.
**Unblocks.** The single largest repair queue.
Detail: `exam_bank_regen_review.md`, `qa_sweep/exam_japanese_*.md`.

### A3. Grammar identity merges
**Question.** Merge the two confirmed duplicate pairs?
**Evidence.** `gram:gp` is a strict subset of `gram:da-desu` (one lesson unlocks both and issues 6
SRS cards for one fact; 840 refs mapped). `gram:gp-152` duplicates `gram:te-hoshii` (same form,
meaning, topic, lesson; the loser also carries leaked build commentary; 591 refs mapped). Two other
pairs are genuinely distinct and stay. Three more collisions of the same class are untriaged.
**Recommendation.** Merge both, survivors as named. Mechanical once approved.
**Unblocks.** A5 (the family rebuild reads the grammar identity set).
Detail: `grammar_identity_merges.md`.

### A4. Level-confidence formula
**Question.** Which group is wrong: 132 grammar records pairing agreement `'1/1'` with confidence
0.34, or 207 pairing it with 1.0? And `vocab:1385390` pairs `'0'` with 0.5 against the sentinel rule.
**Evidence.** Only the original reconciliation history says which formula was intended.
**Recommendation.** Restate the formula in `design/schema_v2.md`; I recompute all 10,028 records.
**Unblocks.** Retires the L4–L6 ratchet (134+6+1 held).
Detail: `validate_level_consensus.py` output; STATE (af).

### A5. Family layer rebuild
**Question.** Approve the staged plan?
**Evidence.** 74.7% of grammar `function_set` memberships name the WRONG topic (stale snapshot);
`family_ids`/`related` were silently dropped from the published contracts; the builder's
skip-if-populated guard froze the layer at n5/n4. Plan: validator → mechanical rebuild
(514→1,166 conjugation memberships) → particle/topic families → `family_related` → authored Layer C.
**Recommendation.** Approve stages 0–3 (mechanical); stage 4 is content work for later.
**Blocked by.** A3.
Detail: `family_layer_rebuild.md`.

### A6. Homograph placements and the prose-reading resolver rule
**Question.** Accept the 14 judged placements, and let the resolver read the `<jp>reading</jp>`
printed beside a ref?
**Evidence.** 4 exported refs are provably wrong — the lesson prints the intended reading next to
the ref (上/じょう, 柄/がら, 品/しな, 金/きん). That one signal settles 12 of 14; corpus frequency was the
least reliable rule. 5 exemptions have certain placements needing no new content.
**Recommendation.** Yes to both. Mechanical once approved.
Detail: `homograph_recommendations.md`.

### A7. Three design gaps
- `needs[]` prerequisite model is empty everywhere; the linearity gate prints an unconditional
  notice. Populate it (from cumulative-known-set deltas?) or remove the field.
- 875 lesson-body `<jp>` spans contain kanji and carry no reading — furigana coverage policy:
  every span, or only the first occurrence per lesson?
- `bank.json` exposes one `translation.en` but 3,529 are Layer-A anchors and 2,342 are Layer-B
  *derived* English; a consumer cannot tell them apart. Add an `en_layer` field to the contract?
Detail: `en_anchor_backfill.md` (third item); STATE (af).

### A8. Content policy for the speaking path
**Question.** Should a register filter and blocklist gate speak-path selection?
**Evidence.** Drill and production items include insults, a national stereotype, 痔があります, and
classical or business-letter register (心熱けれど肉体は弱し as a production prompt). Selection is
mechanical (seed + known set), so nothing filters register or content.
**Recommendation.** A register filter plus a small reviewed blocklist. I build the mechanism; the
list is yours.
**Update (speak builder campaign, 2026-09-01).** The filter cannot be built yet: there is NO
sentence-level register field in the corpus (`vocab.register` is not a DB column and exports null;
the only register vocabulary is on grammar points, neutral/polite/casual/formal). The builder now
prints a census — 645 say_now/production items, 383 with no register signal at all — so the zero it
reports for archaic/epistolary/vulgar means *unrecordable*, not *absent*. First decision is
therefore schema: add `register` to `sentence` (values to be fixed in `design/schema_v2.md`), then
populate it (JMdict misc tags cover part of it; the rest is authored), then the filter. Also left
open by that campaign: idiom-frame misfires lemma matching cannot catch (いくら…ても still lands in
the shopping stage) — a per-stage idiom stoplist is the suggested mechanism.
Detail: `qa_sweep/speak_content_1.md`, `speak_content_2.md`.

### A9. 22 vocab records point at the wrong JMdict entry
**Question.** Re-point in place, or deprecate-and-add?
**Evidence.** The gloss audit's critical finding, re-derived independently against JMdict 3.6.2 and
the three consensus lists: 21 n5/n4 records (plus 尾/お at lower confidence) resolve to a different
JMdict entry than their headword and reading name. Because `vocab:<jmdict_id>` IS the published
address, fixing them is a migration, not an edit: 5,955 slug occurrences across the 543 committed
export files, 1,415 sentence_vocab rows, 766 token links, 22 lesson unlocks, 24 family memberships.
Collateral checked: none of the intended targets already exists as a duplicate record.
**Options.** (a) Re-point in place — the slug changes, every reference rewritten in one migration,
old slug kept as an alias in a redirect table. (b) Deprecate-and-add — old record marked
`deprecated_by`, new record inserted, references migrated lazily. (a) is cleaner for a corpus this
young; (b) is what you do once external consumers hold the old ids.
**Recommendation.** (a), as one migration script with a plant-proved validator, before any external
consumer exists.
Detail: `qa_sweep/vocab_identity_queue.md` (per-record evidence and reference counts). The same
file records four SYSTEMIC gloss findings deferred with reasons: `headword` is itself an address
(unlock refs use it), `register` is derived from a JMdict sense alignment the corpus does not have
(451 of 1,947 senses unresolvable), `vocab_form` has no tag column, and the romaji convention for
ー and final っ is the corpus's own stated rule.

### A10. Should a speaking-path stage's patterns be capped at its level band?
**Question.** A unit's `patterns` are the grammar points whose forms occur in the unit's own
phrases. The builder has never filtered them by the stage's `approx_band`; the phrases are gated by
the vocabulary known set, so a pattern label names grammar the learner has just produced. Today's
placeholder-aware form matcher (135 of 536 forms carry ～ — every N3 record — and none of them had
ever matched) made this visible: N3 points now appear where their forms genuinely occur.
**Evidence (patterns by level per stage, after the fix).** arrival (pre-n5): n5 6, n4 5 — the n4
were already there at HEAD. eating (n5): n5 6, n4 6, n3 1. getting_around (n5): n5 6, n4 6, n3 7.
health (n4): n4 11, n5 8, n3 3. real_talk (n3): n3 23, n4 4, n5 2. The practice builder already
demotes any pattern with fewer than three known-set example sentences, which is itself evidence the
survivors are within reach.
**Options.** (a) No cap — a pattern describes the phrase; keep, and let the label carry the level so
the learner sees it. (b) Cap at the band's upper level (pre-n5 counts as n5) — removes ~1/3 of
today's patterns, including N4 points in N5 stages that predate this session. (c) Cap at band+1.
**Recommendation.** (a), with the level shown on the label. A pattern the learner just said aloud
is not "above their level".
Detail: scripts/export/pattern_forms.py (the matcher and its runnable proof); this census.

---

## B. Repair campaigns — running now (per-item judgement, workflow-shaped)

| campaign | scope | source |
|---|---|---|
| Grammar records | formation prose errors beyond the 4 fixed (n3-nanka, n3-you-ni-3, n3-kesshite-nai, n3-ba-hodo, n3-ni-shitemo, yatto, gp-101 一人, gp-56 くれる, n3-ni-shite-wa); nuance/explanation errors; `forms[]` on gp-36; sentence links that illustrate the sense the record EXCLUDES (n3-ta-tokoro 6/6, ようだ ×5, gp-63 passive shown by potentials, ちゃいけない by なくちゃいけない). Merges and re-keys (n3-ppai) go to A. | `grammar_accuracy_1..4.md` |
| Translation individual defects | ~100 named: meaning shifts, explanatory parentheses in the natural field (~45), orthography slips, register (さようなら as "Adeus"), 2 token-gloss errors, 1 leaked conjugation_note, person disagreement | `translation_accuracy_1..6.md` |
| Readings | 146 remaining titles (resumed); 32 run-on boxes (punctuation between glued sentences); 25 duplicate-sentence boxes | `readings_quality.md` |
| Kanji selection | example selector prefers N1/N2 over owned N5 words (48 records); `introduced_at_level` seeding contradicts its documented rule (44); 2 duplicate example words; 屋 telhado; 少 alignment; 台 "p/"; 文 note; nanori ordering | `kanji_records_1.md` |
| Speak selection | stage-opening production and fluency drawn from the previous stage (builder cold start); seed matching はい to 履く; shopping never asks a price; lodging 25/36 from one block; fluency lists repeated verbatim; おめでとう twice in one unit | `speak_content_1..2.md` |
| Vocab glosses | 15 findings | `vocab_glosses.md` |

### B-followups raised BY the campaigns (small, well-defined; next pass)

- **Translation campaign** (`qa_sweep/translation_repairs_skipped.md`): 3 same-record literal
  siblings now disagree with the repaired natural field (gen-fb07d83b3e0c "A orelha",
  gen-790b6cf52284 "está quente" for 暖かい, tatoeba-10083431 "ramo" for つる); 5 generated records
  whose pt-BR is now 1st-person present while the en anchor still reads imperative/gerund; 7 defects
  living in `particles[].explanation` (unreachable by the sentence/token repair schema — needs a
  particle-scoped pass); 1 kana defect (gen-9f80f08cc644 reads 辛い as つらい); 1 table row that
  arrived with new == old (gen-960d7cee0887, 〜とみえて direction) and needs a corrected string.
- **Reading-override ledger:** `research/derived/fable5_validation/verified_reading_overrides.json`
  is the sanctioned escape hatch when the analyzer's reading is wrong in context, and it already
  registers 辛い→からい for two food sentences (tatoeba-10901867, tatoeba-11727272). gen-9f80f08cc644
  (このみそはちょっと辛いです) now has からい in kana and romaji but its token still carries the
  analyzer's つらい — the only 辛い food sentence whose token disagrees. The ledger's own note
  certifies every entry as 2-vote verified, so the follow-up pass refused to add a row on its own
  authority. Needs the same verification, then one row. The 言う→ゆう case (14 tokens) is the same
  mechanism if a display override is ever wanted there.
- **Human rulings, not repairs:** gender-inclusive parentheses "(a)" in 9 natural translations —
  house style says natural speech, but the alternative is choosing a gender the Japanese does not
  state; and 5 subject-less sentences where pt and en chose different persons.
- **Readings composition:** `reading.uses` is a build-time snapshot — recomputing it from today's
  sentence links would push 149/286 boxes out of their lesson's known set. Either freeze it as the
  documented contract or re-select those boxes; not both.
- **Kanji:** 京 has no at-or-below-level example because 東京/京都 are absent from the vocab registry
  entirely — vocab authoring, not selection. The report's K1–K4, K7, K10, K12 were out of the
  campaign's scope and remain open.
- **Speak:** `getting_around-01` has zero on-topic prior material at its opening (structural until
  a mining pass); idiom-frame misfires need the per-stage stoplist.

## C. Mechanical items — done by hand today

- bank `言う` stored as ゆう on 5 source tokens (checked against the re-dissection gate first)
- empty `stage:` tag on 324 records (the same dropped-key bug as the English anchors)
- 3 stale n4 exam INDEX.md counts; 2 exact duplicate pairs in `n4_sentence_order`
- 37 n5 orthography items keyed ambiguously over identical option sets, removed with reason
- listening: `lt:n5:004` (a student says お兄さん of his own brother to a teacher), `lp:n3:008`
  (contradicts its own showtimes), `lr:n3:tatoeba-11510681` (key answers a question not asked)
- `pt_validated_against` still `'dict'` on the 324 backfilled records — re-validate against the
  restored anchors (separate campaign; listed so it is not forgotten)

## D. Deferred on purpose

Further broad QA sweeps. Two waves produced more confirmed findings than the decision queue can
absorb; a third now would be the wasteful kind of token use.
