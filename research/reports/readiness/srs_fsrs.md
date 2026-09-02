# Readiness — `srs_fsrs` (memorization: what the corpus gives an FSRS-6 scheduler)

Audited 2026-09-02 against the exported JSON under `corpus/` and `course/` (the source of truth),
`contracts/`, `design/`, and the validator suite. Every count below was produced by running a script
over the data, not read out of a document. `db/corpus.sqlite` was opened only to cross-check, and
where it disagrees with the export that is called out.

**Verdict.** The *filing* layer is done and genuinely well-guarded: 4,133 cards, one per taught item,
every one in a real deck, gated hard by `scripts/validate/validate_srs_decks.py` (0 failures). The
*card* layer is half-built. Of the 9,453 card instances those 4,133 rows imply, 4,824 can be rendered
today from stored content, 479 more can be rendered with a query, and 4,133 — every `production`
card — cannot, because no production answer key exists anywhere in the JLPT track and 883 of the
prompts would be ambiguous even if one did. No audio exists anywhere (311 `audio` fields, all the
literal string `pending`), so the `listening` card type in the enum has never been minted once.

---

## 1. What this capability needs from the data

An FSRS-6 scheduler is famously undemanding, and the demand is worth stating exactly so the gap
analysis is honest about which half is missing.

**What the algorithm needs — per card, and nothing else:**

1. A **stable card id** that names one memory fact and never moves.
2. A **review history**: `(rating in {1,2,3,4}, review_datetime)`, optionally `review_duration`.
   Stability/difficulty/due are *derived* from that history, not authored.

That is the complete list. FSRS has no notion of level, deck, frequency, prerequisite, or item
content. `design/fsrs_integration.md` states this correctly and the claim **verifies**: nothing in
`py-fsrs`'s `Card`/`ReviewLog` or `ts-fsrs`'s models reaches into corpus content.

**What the *app* needs, which is where the corpus actually earns its keep:**

3. A **card-derivation rule** — how a corpus item fans out into cards — that is deterministic and
   stored, so the same learner gets the same card ids across rebuilds.
4. **Renderable content per card kind**: recognition needs JP form + pt-BR meaning; production needs
   a pt-BR prompt *and an accepted-answer set*; handwriting needs stroke order; cloze needs a
   sentence plus the token to blank; listening needs an audio asset.
5. **Deck membership** for caps, ordering and the learner-facing "N4 kanji" surface.
6. **Interleaving signal** — which items are confusable with which (families).
7. **Introduction order** — which lesson seeds which card, so cards enter the queue on completion.
8. Per-card **tags** for filtering/suspension, and a per-card hook the app can hang leech
   remediation on.

Items 1, 3, 5, 7 are corpus/courseware obligations and are met. Item 6 is partly met. Item 4 is met
for two kinds out of five. Item 8 does not exist.

---

## 2. What exists today (verified)

### 2.1 The card rows

`course/*/topic-*/lesson-*.json` -> `srs.introduces_cards[]`. All 322 lessons carry the key (none
missing, none null). Every card object has exactly three fields: `deck`, `item`, `card_types`.

| measure | value |
|---|---|
| lessons | 322 (pre-n5 41, n5 84, n4 96, n3 101 — matches `course/manifest.json`) |
| cards | **4,133** |
| distinct items | 4,133 (**no item is enrolled twice, anywhere**) |
| card instances (`item#kind`) | **9,453**, all ids unique, 0 collisions |
| cards by lesson level | n3 2,072 · n4 1,042 · n5 938 · pre-n5 81 |

By deck:

| deck | cards | deck | cards |
|---|---:|---|---:|
| `deck:vocab-n3` | 1,596 | `deck:grammar-n4` | 213 |
| `deck:vocab-n5` | 708 | `deck:kanji-n4` | 187 |
| `deck:vocab-n4` | 642 | `deck:grammar-n5` | 151 |
| `deck:kanji-n3` | 344 | `deck:grammar-n3` | 132 |
| `deck:kanji-n5` | 103 | `deck:kana-katakana` | 29 |
| `deck:kana-hiragana` | 28 | **`deck:phrases`** | **0** |

By card kind: `recognition` 4,133 · `production` 4,133 · `handwriting` 691 · `cloze` 496 ·
`listening` **0**.

### 2.2 The derivation is complete and mechanical

Every content unlock becomes exactly one card. Across all 322 lessons the unlock ledger holds
2,946 `vocab` + 634 `kanji` + 496 `grammar` + 57 `kana-family` + 4 `feature`; **the only uncarded
unlocks are the 4 `feature` ones**, which are not memorizable items. There is no drift between what
a lesson teaches and what it schedules.

Corpus coverage of the taught levels:

| entity | level | corpus | carded | coverage |
|---|---|---:|---:|---:|
| grammar | n5 / n4 / n3 | 151 / 213 / 132 | 151 / 213 / 132 | **100%** |
| kanji | n5 / n4 / n3 | 103 / 177 / 350 | 103 / 177 / 350 | **100%** |
| vocab | n5 / n4 / n3 | 705 / 653 / 1,596 | 699 / 650 / 1,596 | 99.1 / 99.5 / 100% |

The nine uncarded N5/N4 vocab are homograph siblings the course resolved to the other record
(`vocab:1189370` 何方, `vocab:2846738` 何, `vocab:1423310` 中, `vocab:1403830` 側, `vocab:2084840` 年,
`vocab:2147990` 背, `vocab:1247260` 君, `vocab:1310670` 止める, `vocab:1605840` 様) — related to the
14 rows in `course/vocab_disambiguation_review.json`, all `needs_review: true`.

### 2.3 Deck filing, and what "level" on a deck means

`design/unlock_enums.json` holds `deck` (12), `card_type` (5) and `deck_registry` (skill / level /
card_types per deck). Filing follows the **lesson's** level, not the item's: pre-n5 lessons enrol into
the n5 decks, and **23 cards sit in a deck whose level differs from the item's own corpus level**
(1×n1->n3, 3×n2->n3, 10×n3->n4, 1×n1->n5, 8×n4->n5) — e.g. `kanji:通` (n3) in `deck:kanji-n4`. This is
deliberate and documented in the validator's docstring; `course/srs_deck_exemptions.json` is not
seeded because rule 6 was rewritten to compare against the lesson. Correct as an engineering choice,
but it means a deck's `level` is a **curriculum position, not a JLPT claim about its contents** — see
risk 4.3.

### 2.4 What a card can actually show

The card row carries no content; everything is resolved by stable id. What resolves:

| kind | instances | what it needs | what exists | renderable |
|---|---:|---|---|---|
| `recognition` | 4,133 | JP form + pt-BR meaning | vocab `headword`/`kana`/`romaji` + `senses[].gloss["pt-BR"]` (0 carded vocab lack a gloss); kanji `character` + `meanings["pt-BR"]` + `readings[]`; grammar `structure_pattern` + `label` + `explanation`; kana `char` + `romaji` | **100%** |
| `handwriting` | 691 | stroke order | `corpus/strokes/n*.json` covers **634/634** carded kanji; `corpus/strokes/kana.json` covers 145/211 glyphs — all 57 kana cards are family-level so all resolve, but the 66 missing are the yoon digraphs | **100%** at card level |
| `cloze` | 496 (grammar only) | a sentence + a token to blank | `sentence.grammar[]` links **479/496** carded grammar points to at least one bank sentence (398 have 5+) | **96.6%** |
| `production` | 4,133 | pt-BR prompt -> JP answer + accepted variants | **nothing**. `accepted_variants` exists only in `course/speak/*/unit-*.json`; `answer.accept` only on 308 lesson exercises, none of which name a card | **~0%** |
| `listening` | 0 | audio | 311 `audio` fields repo-wide, **every one is the string `pending`** | **0%** |

Supporting material that exists and is real: `corpus/families/families.json` (396 families, 2,572
member edges, bidirectional back-pointers, 50 of them confusable-type — the interleaving signal);
`corpus/capabilities/registry.json` (74 capabilities, 266 lessons mapped) for the secondary skill
track; pitch data on 1,212 of 2,946 carded vocab; 5,889 fully dissected sentences with 49,756
tokens carrying `vocab`, `reading`, `romaji`, `gloss`, `inflection` and `position`.

### 2.5 Which validator guards what

| guarded | by |
|---|---|
| deck exists, is in the registry, skill matches namespace, item resolves, item is one of the lesson's own unlocks, deck level == lesson level, no double enrolment | `scripts/validate/validate_srs_decks.py` — 7 rules, HARD gate, currently **0 FAIL over 4,133 cards** |
| `srs.introduces_cards` names exactly the lesson's item unlocks, each once | `scripts/validate/validate_unlock_ledger.py` check F |
| the card object's shape | `contracts/lesson.schema.json` -> `srs.introduces_cards` — **weakly**: `card_types` is `{"type": "array"}` with no item schema, `item` is a bare `string` with no pattern, and the array items carry **no `required` list** |
| every cross-entity edge resolves and is true about its target | `scripts/validate/validate_graph_edges.py` — 554,912 edges, all OK |

`scripts/validate/validate_all.py` runs 42 entries, **40 of them hard-gating** (`PENDING.md` says
"39 hard validators"; the file is the authority and it is 40). Cards are touched by exactly **two**
validators, and neither of them asks whether a card can be rendered.

---

## 3. Gaps

### G1 — No production answer key, and 30% of production prompts are ambiguous · **L** · AI can author, teacher must sign off
Every one of the 4,133 cards declares `production`, so 4,133 of the 9,453 instances (44%) are
scheduled by the contract and unrenderable by the data. Worse than absent: **883 of the 2,946 carded
vocab share their first pt-BR gloss with another carded vocab**, across 375 colliding keys —
`trabalho` names 勤め, 作業, 仕事, 手間, 働き, 面倒 all at once; `então` names じゃあ, すると, それで, では,
それでは. A pt->JP card built on the first gloss is unanswerable for 30% of the deck.
*Why it matters:* production is where retrieval strength actually gets built, and a card the learner
cannot answer correctly turns into a lapse, which FSRS reads as a memory failure and reschedules
aggressively — the learner is punished for the corpus's ambiguity.
*Depends on:* the `answer.accept` pattern already proven on 308 lesson exercises and on
`accepted_variants` in all 72 speak units. The mechanism exists; it has never been pointed at a card.

### G2 — Zero audio · **L** · owner-blocked (TTS), not AI-authorable
311 `audio` fields, all `pending`. `design/listening.md` states the owner voices the scripts later.
Vocab, kanji, kana and sentence records have **no audio field at all**, so audio is not merely
unproduced, it is unmodelled outside listening exam items and speak units.
*Why it matters:* `listening` is a declared card type with zero cards; `deck:phrases` (skill
`phrase`, card types `listening` + `production`) is declared in the enum, in the registry, in
`lesson.schema.json`'s enum — and holds **0 cards**. The prototype's "Ouvir" button
(`prototype/app/routes/review.tsx`) is hard-disabled. A Japanese SRS with no audio is not
Anki-grade.

### G3 — 1,545 vocab cards have no example sentence · **M** · AI-authorable
From the canonical export, only **1,401 of 2,946 carded vocab (47.6%)** appear as a token in any bank
sentence. 1,545 have none, so those cards can show no usage example and **no vocab cloze card can be
minted for them at all**.
*Cross-check:* `db/corpus.sqlite`'s `sentence_vocab` table holds 41,360 edges over 1,793 distinct
vocab and would cover **1,744/2,946 (59.2%)**. **The exporter drops that edge** — `bank.json`
sentences carry `tokens[].vocab` but no sentence-level vocab list, and the `new_items` field is an
empty array on all 5,889 sentences. So 343 vocab lose their example links purely in the export. The
DB is regenerable and the JSON is the source of truth, which makes this an export bug, not a data
one: fix the exporter first, then author for the remaining ~1,200.

### G4 — `card_types` carries zero information · **S** · AI-authorable
`validate_srs_decks` rule 2 requires `card_types` to equal the deck registry's list *exactly*. It
therefore repeats the same constant 4,133 times and can never say anything about the card it is on:
it cannot record "this grammar point has no sentence, so no cloze", "this vocab's gloss is ambiguous,
so no production", or "this item has audio". The 17 N3 grammar points with no bank sentence
(`gram:n3-kiri`, `gram:n3-sa`, `gram:n3-tatoe-temo`, `gram:n3-koto-da`, ...) all declare `cloze` anyway.
*Why it matters:* the app has no stored way to know which of the 9,453 instances it may actually mint,
so it will either mint broken cards or reimplement the check at runtime.

### G5 — No per-card tags, no leech hook, no card entity in the contract · **M** · AI-authorable
`contracts/manifest.json` catalogues 23 entities; **card and deck are not among them**. Decks live
only in `design/unlock_enums.json`, which is not a contract, and cards live as an untyped sub-array
of `lesson`. There is no field anywhere to tag a card (`confusable`, `irregular-reading`,
`homophone`, `counter`), which is what Anki users filter, suspend and bury by. Nothing links a card
to remediation material: **0 of 1,560 lesson exercises name a corpus item id**, so a leech cannot be
routed to a drill. (The 6,048 exam-bank items are better: 3,737 name a vocab.)

### G6 — Kana cards conflate five glyphs each · **M** · AI-authorable, pedagogy call for the teacher
The 57 kana cards are filed at **family** granularity (`kana:hiragana-a` = あいうえお), covering 211
glyphs. `design/fsrs_integration.md` itself cites the minimum information principle and warns that
conflating facts corrupts the per-card D/S estimate. Per-glyph ids exist
(`kana:hiragana-あ`) and `validate_srs_decks` already accepts them as legal card targets — the lessons
just never use them.
*Compounding contradiction:* `design/srs_design.md` §1 says "Kana handled by the skill track, **not
FSRS cards**" and §6 says production is "phase 2 ... recognition-only at launch";
`design/learning_science.md` R75 repeats both. The data ships 57 kana FSRS cards and mandates
production on all 4,133. **The data is right** (it is exported and hard-gated); the two design docs
are stale and must be reconciled or they will mislead the app build.

### G7 — Duplicate grammar identities mint duplicate cards · **S** · owner already decided, mechanical
Verified in the data: `les:n5-desu-wa-01` mints cards for both `gram:da-desu` and `gram:gp`
(a strict subset), and `les:n4-dar-receber-03` mints both `gram:te-hoshii` and `gram:gp-152`
(same form, meaning, topic, lesson). Each pair is 2 cards × 3 card_types = **6 card instances for one
fact**. Owner approved the merge on 2026-09-01 (`research/reports/PENDING.md` A3); it has not landed.

### G8 — The speaking path has no cards at all · **M** · AI-authorable, depends on G1/G2
72 speak units under `course/speak/`, **none carries an `srs` key**, and `course/speak` is not in
`course/manifest.json`'s course list. The units hold 581 distinct vocab, 752 sentence refs and 213
production prompts *with* `accepted_variants` — the richest production material in the repo. 568 of
those 581 vocab are already carded by the JLPT track; **13 are carded nowhere**. A learner who takes
only the speaking path — one of the owner's two declared paths — gets zero spaced repetition.

### G9 — No renderability validator · **M** · AI-authorable
Nothing checks that a declared card kind has the content it needs. A gate that passes on 496 cloze
cards when 17 of them have no sentence, and on 4,133 production cards when none has an answer key,
is not testing the thing that would break the app. Related hole: `deck:phrases` is declared with 0
cards and the gate is silent — an empty declared deck is invisible to all 7 rules.

### G10 — Review-log / card-state schema is prose only · **S** · AI-authorable
`design/fsrs_integration.md` and `design/srs_design.md` both sketch `CARD` + `REVIEW_LOG` and they
**disagree** (`srs_card(user, item_ref, ...)` vs `card_id ... corpus_ref ... card_kind ...
fsrs_version`). Neither is a contract file, neither is validated, and neither carries
leech/suspend/tag state. Proposal in §5.

---

## 4. Quality risks against the near-100% goal

**4.1 — Ambiguous card faces will be graded as memory failures.** Beyond the 883 production
collisions: **70 carded vocab share a headword** with another carded vocab (後 ×3, 上 ×3, 彼, 先, 米,
何れ ...) and **370 share a kana reading** (きゅう names 急/球/旧/九/級; せい names 性/正/製/背/所為).
A recognition card showing 後 alone, or a listening card saying きゅう, has more than one right
answer. `validate_graph_edges` already reports "93 ambiguous headwords in registry" as information;
nothing turns that into a card-level constraint.

**4.2 — Cards inherit `needs_review` from content that was never reviewed.** All 496 grammar records
carry `needs_review: true`, and the sentence bank is largely `ai_generated: true` /
`needs_review: true` (spot-checked: `provenance.pt_source: "ai"`,
`translation_confidence: 0.85`). Those records are the *back* of 496 grammar cards and the cloze
source for 479 of them. FSRS will faithfully drill a mistranslation for months.

**4.3 — Deck names make a JLPT claim the contents do not honour.** `deck:kanji-n4` contains 10 N3
kanji and `deck:vocab-n5` contains 8 N4 vocab plus 1 N1 (`vocab:1385390` 接見 — the same record
`PENDING.md` A4 flags for a broken `level_agreement: '0'` / confidence 0.5 pair). For the JLPT-prep
path specifically, a learner filtering "my N5 vocabulary" gets material that is not N5. The fix is a
label, not a refiling: show the deck as a course stage, and expose the item's own `level` on the card.

**4.4 — 66 yoon glyphs have no stroke data.** きゃ/きゅ/きょ ... ぴょ. Invisible today because kana
cards are family-level; it becomes a visible hole the moment G6 is fixed and cards go per-glyph.

**4.5 — The prototype proves nothing about this data.** `prototype/app/routes/review.tsx` hardcodes
one word (学生), hardcodes four intervals ("~ 7 dias"), finds its example sentence by
`s.jp.includes(headword)` substring match (`prototype/app/lib/corpus.server.ts:167`), and never reads
`srs.introduces_cards`. There is no end-to-end evidence that the deck data drives a review session.

**4.6 — 132/496 grammar, 384/634 kanji and 1,596/2,946 vocab cards have no family**, so the
interleaving strategy `fsrs_integration.md` prescribes is unavailable for roughly half the deck.
Note also that `PENDING.md` A5 reports 74.7% of grammar `function_set` memberships name the wrong
topic — the family layer is under repair, so today's coverage figure is an upper bound on the
*usable* signal.

**4.7 — A design-doc claim that does not verify.** `fsrs_integration.md` says the corpus exposes
"`freq_rank` ... for introduction order". Kanji records carry `freq_rank`; **vocab records do not** —
the field appears in none of the 7,401 exported vocab records (only in the ingest scripts). Vocab
introduction order is baked into lesson placement and cannot be re-derived from the export.

---

## 5. Proposed review-log schema (app-side; the corpus owes none of it)

Reconciling the two conflicting sketches, and adding what an Anki-grade product needs. `REVIEW_LOG`
is the durable truth; `SRS_CARD` is a version-tagged derived cache so FSRS-6 -> 7 is a re-optimize,
not a migration.

```
SRS_CARD                                   -- one row per (user, memory fact)
  card_id        TEXT PK   -- "<corpus_ref>#<kind>", e.g. "vocab:1304970#production"
  user_id        TEXT
  corpus_ref     TEXT      -- stable corpus id: vocab:/kanji:/gram:/kana:/sent:
  card_kind      TEXT      -- recognition|production|listening|handwriting|cloze
  cloze_target   TEXT NULL -- "<sentence_slug>#<token position>"; required when kind='cloze'
  deck           TEXT      -- deck:vocab-n4 ... (curriculum stage, NOT a JLPT claim)
  state          INTEGER   -- 1 Learning, 2 Review, 3 Relearning (New = absent)
  step           INTEGER NULL
  stability      REAL NULL -- S, days
  difficulty     REAL NULL -- D in [1,10]
  due            TIMESTAMP
  last_review    TIMESTAMP NULL
  reps           INTEGER   -- UX only
  lapses         INTEGER   -- UX only; also drives the R33 furigana fade
  suspended_at   TIMESTAMP NULL
  buried_until   TIMESTAMP NULL
  leech_state    TEXT NULL -- none|flagged|suspended
  tags           TEXT[]    -- from corpus card tags (G5) + learner-added
  fsrs_version   TEXT      -- "fsrs-6"
  params_version TEXT      -- which weight vector produced this cache

REVIEW_LOG                                 -- append-only; never mutated, never deleted
  log_id          TEXT PK
  user_id         TEXT
  card_id         TEXT FK
  rating          INTEGER   -- 1 Again, 2 Hard, 3 Good, 4 Easy
  review_datetime TIMESTAMP -- UTC
  review_duration INTEGER NULL -- ms
  review_state    INTEGER NULL -- card state at review time; lets you replay exactly
  source          TEXT      -- daily_queue|lesson_drill|exam_sim|manual_cram

USER_SCHEDULER                             -- one row per user
  user_id, desired_retention (default 0.90, clamp 0.70-0.97),
  params JSON (21 FSRS-6 weights; NULL = ship defaults),
  params_trained_at, reviews_at_training,
  daily_new_cap (default 15), daily_review_cap (default 120), learning_steps
```

Four notes on the deltas from `design/fsrs_integration.md`:

- **`cloze_target` is required**, not optional. Without it a cloze card is not a stable memory fact —
  re-picking the sentence at review time silently changes what is being tested, which corrupts D/S.
- **`review_state` and `source`** cost nothing to store and are the difference between "we can debug
  a scheduling complaint" and "we cannot". Same-day lesson drills must be distinguishable from queue
  reviews, because FSRS-6 models same-day reviews crudely and you will want to exclude them when
  training.
- **`leech_state` / `suspended_at` / `buried_until`** are the entire Anki-grade retention story and
  appear in neither design doc. `srs_design.md` §6 leaves "leeches" as an open owner question; the
  schema should hold the field regardless of the policy chosen.
- **`params_version` on the card** so a re-optimize can invalidate caches without touching the log.

**Confirming the headline claim:** FSRS-6 needs nothing from the corpus beyond `card_id` and the
review history — verified against the `Card`/`ReviewLog` shapes both ports expose. The corpus's job
is upstream (which cards exist, what they show, what order they enter) and downstream (nothing). So
every gap in §3 is a *content and contract* gap, never an algorithm gap. That is good news: none of
them blocks starting the scheduler.

---

## 6. Recommended sequence

Ordered so each step unblocks the next and nothing is authored twice.

1. **Fix the exporter's sentence-to-vocab edge (S).** `sentence_vocab` exists in the index with 1,793
   distinct vocab; the export publishes only `tokens[].vocab` (1,449). Recovering it moves vocab
   example coverage 47.6% -> 59.2% for free and shrinks G3's authoring bill by ~343 items. Do this
   before authoring anything, or you will author examples that already exist.
2. **Land the approved grammar merges (S, decided).** `gram:gp` -> `gram:da-desu`,
   `gram:gp-152` -> `gram:te-hoshii`. Removes 6 duplicate card instances and stops two lessons
   teaching one fact twice. Cheap, already approved, and it changes the card set — so do it before
   any per-card authoring.
3. **Promote card + deck to first-class contracts (M).** Add a `deck` entity to
   `contracts/manifest.json` sourced from `design/unlock_enums.json`, and tighten
   `lesson.schema.json`'s `srs.introduces_cards` items: `required: [deck, item, card_types]`,
   `card_types` items constrained to the `card_type` enum, `item` given a namespace pattern. Then
   make `card_types` **per-card** rather than a copied constant, and relax `validate_srs_decks`
   rule 2 from "equals the registry" to "is a non-empty subset of the registry". Everything after
   this depends on being able to *say* what a card supports.
4. **Add `validate_srs_cards_renderable.py` (M).** One rule per kind: cloze needs at least one linked
   sentence; handwriting needs a stroke record; production needs an answer key with at least one
   accepted variant; listening needs a non-`pending` audio ref; recognition needs a non-empty pt-BR
   gloss/meaning. Plus: fail on a declared deck holding 0 cards. Write it *before* the authoring
   campaigns so it measures them, and seed it with the 17 cloze-less grammar points as its planted
   violation.
5. **Author the production answer keys (L, the big one).** Reuse the two proven shapes:
   `answer.accept[]` from the 308 lesson exercises and `accepted_variants[]` from the 72 speak
   units. Resolve the 883 ambiguous prompts by disambiguating the *prompt*, not the answer set —
   the prompt needs a sense hint (`trabalho (emprego, 仕事)`) or a POS/collocation cue. AI can draft
   all of it; the 883 collisions and the 70 shared headwords need a teacher pass, and they overlap
   the 14 rows already queued in `course/vocab_disambiguation_review.json`.
6. **Add per-card tags (S-M) once step 3 lands.** Derive mechanically first — `homophone` from the
   165 shared-reading sets, `homograph` from the 34 shared headwords, `confusable` from the 50
   confusable-type families, `irregular-reading` from the `reading_irregular` flag
   `learning_science.md` R32 defines. Free filtering, free leech triage, no authoring.
7. **Split kana to per-glyph cards (M).** 57 -> 211, gated on the teacher's call about whether kana
   belongs in FSRS at all (the design docs say no; the data says yes — reconcile
   `design/srs_design.md` §1/§6 and `design/learning_science.md` R75 with the export either way).
   If it goes ahead, backfill the 66 missing yoon stroke records at the same time.
8. **File the speaking path (M).** Add `srs` to the 72 speak units and populate `deck:phrases` from
   the 752 sentence refs and 213 production prompts. This is the cheapest way to give
   `deck:phrases` and the `listening` card type a reason to exist, and 568/581 of its vocab is
   already carded so the marginal card count is small.
9. **Author the vocab example/cloze backfill (L).** After step 1, roughly 1,200 carded vocab still
   have no sentence. Prefer selection from Tatoeba/JEC over generation per spec §1.2; every generated
   one is `ai_generated: true` + `needs_review: true`.
10. **Audio last (L, owner-blocked).** It is the only gap AI cannot close and the only one that needs
    a pipeline rather than a campaign. Model the field first — add `audio` to vocab, kanji, kana and
    sentence records with the same `pending`-or-filename pattern `contracts/speak_unit.schema.json`
    already uses — so the 311 existing `pending` markers and the future ones validate identically and
    the renderability gate in step 4 can start counting the debt.
