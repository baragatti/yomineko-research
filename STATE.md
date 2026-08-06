# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE

> **2026-08-06 (w) — QA QUEUES WORKED. All four remaining backlogs now have staged, byte-anchored
> findings, and TWO LIVE CORRUPTIONS were found and fixed.**
>
> - **FIXED AND SHIPPED** (`scripts/fix_instruction_leak_grammar.py`, applied, gate green): two grammar
>   explanations were shipping broken text TO LEARNERS, both survivors of earlier applier rounds.
>   `gram:teiru-tokoro` ended with the literal order `Substituir a frase final por: "..."`, escaped
>   quotes and all. `gram:cha-ikenai-ja-ikenai` carried the corrected sentence appended AFTER the false
>   one it was meant to replace, so it stated both — and the false clause licenses *飲んちゃいけない.
>   **The instruction-as-value guard exists precisely for this and these two got past it.**
> - **STAGED, NOT APPLIED** — `research/derived/qa_queues/`, all with byte-exact anchors:
>   - `furigana.json` — **all 49** validator failures, 0 needing a human. 32 empty readings (22 are
>     kana-only spans where ruby carries nothing → bare `<jp>`, matching the corpus's own 5,629-to-465
>     convention; 10 have kanji → real readings rebuilt from vocab) and 17 truncated (13 drop the
>     okurigana tail, 4 are genuine slips). Apply at `research/derived/lessons/`, NOT the DB —
>     `load_lessons.py` re-authors from those files.
>   - `phase4_grammar.json` — 44 rows (36 fix / 8 needs-human). **Four more false formation rules**, the
>     worst being `gram:you-da`, whose forms, formation and nuance all teach the VOLITIONAL 行こう under
>     an entry labelled "parece que". Register findings correctly land in `register_json` as arrays, and
>     nothing was written into `caution` (a closed neutral-English enum).
>   - `redissect.json` — 39 rows. **Two of the queue's own complaints do not survive contact with the
>     files** and are marked no-change. The dominant real defect is wrong lemma links, not boundaries.
>   - `layer_a_pairing.json` — unlink/re-link diagnoses only, no authored English, as required.
> - **THE HOMOPHONE MISLINK IS CORPUS-WIDE and now quantified:** する/し → 刷る in **716** tokens,
>   この → 九 in **367**, かれ → 彼(あれ) in **297**, なか → 内 57, せ → 背 12. Cause: the form-table lookup
>   in `dissect.py` keys on the written form alone and keeps whichever entry registered first, so reading
>   and POS never enter the decision. The speaking path works around it (see entry (t)); **the corpus
>   still carries it.** Fixing it moves n5/n4 level counts, so it is its own task with its own re-export.
> - Also reported: token romaji stale in **336 of 5,565** sentences.
> - **STILL RUNNING at session end:** the 61-agent Phase-6 re-authoring workflow over the 399 skipped
>   lesson findings, writing durable partials to `research/derived/phase6_reauthored/`. Check that
>   directory first next session.
>
> ---
>
> **2026-08-06 (v) — THIN-STAGE FIX IS HALF DONE: 360 real Tatoeba sentences mined and 324 authored
> into pt-BR with two-reviewer verification. NOT INGESTED — that is the next task.**
>
> - **Mined** (`scripts/ingest/mine_tatoeba_stages.py`): 120 candidates each for `lodging`,
>   `past_stories`, `opinions` from the 248,705 raw CC-BY rows — stage seed present, not already banked,
>   has an English pairing, ≤34 chars, ≤6 kanji, every kanji taught at N5–N3.
> - **Authored + verified** (72 agents, 3.84M tokens): **324 accepted** (casual 182 / polite 129 /
>   formal 13), 36 self-rejected by the authors for the right reasons (である expository register, a rude
>   superior-to-subordinate order, a dictionary definition, one row whose Layer-A Japanese is corrupted).
>   **69 problems raised, ZERO critical.** Nothing altered the Japanese, nothing drifted to pt-PT in the
>   learner-facing `pt`. Agreed-by-both problems sit almost entirely in `pt_literal`: missing crase,
>   "consultar com" anglicism, 聞こえていた glossed as passive when 聞こえる is intransitive, a を object
>   glossed with the は formula "Quanto ao quarto".
> - **A FULL TRIAL INGEST WAS RUN AND REVERTED** (`scripts/ingest/ingest_mined_stages.py`). It proved
>   two things:
>   1. **The data is sound.** All 324 persisted with **0 invariant violations** (I1/I2/I3), **0** rows
>      whose Japanese had drifted from its raw Tatoeba source, pt-BR on every one. The rebuilt path
>      filled all three thin stages: **lodging/past_stories/opinions reached 6 units each, 72 units and
>      432 phrases, still 100% real, 585 vocab.**
>   2. **It is not ingestable yet, and the gate caught it: 2,756 errors.** Every one of the bank's 5,565
>      sentences is `dissection_tier = "full"`, which `validate.py` reads as a promise of a Layer-B gloss
>      on EVERY content token, an explanation on every particle, and translation + translation_literal +
>      **structure_explanation**. We authored only the two translations, so each new sentence arrived
>      owing roughly eight more fields. Reverted: sentences back to 5,565, path back to 66 units, gate
>      green.
> - **THE ONE REMAINING BLOCKER for the thin stages** is therefore an authoring pass over the 324 staged
>   rows for: per-token `gloss` (content tokens only), per-particle `explanation`, and
>   `structure_explanation_pt`. `persist_dissection.persist()` already accepts all three in its `rec`
>   (`tokens` keyed by position, `particles`, `structure_explanation_pt`) — nothing new to build, only
>   content to author. Then re-run `ingest_mined_stages.py --apply`.
> - **TRAP in that script, fixed but worth knowing:** `persist()` COMMITS internally, so a BEGIN/rollback
>   wrapper does nothing. Its first "dry run" wrote all 324 rows. Without `--apply` it is now a
>   pre-flight that never calls `persist()`. The rollback was never what protected the corpus.
> - **Also still open** (unchanged): the three staged patches turn out to have GENERATORS but no
>   appliers (`fable5_strip_build_metadata.py` / `fable5_fix_ptbr_accents.py` take `--show`, not
>   `--dry-run`); 399 Phase-6 + 25 Phase-4 authoring skips; 49 furigana gaps; 23-sentence re-dissection
>   queue; 54-sentence Layer-A pairing queue; R58 controlled read-aloud (blocked on audio); R78 strand
>   budget not enforced because our histogram counts ITEMS and Nation's split is a TIME budget.
>
> ---
>
> **2026-08-06 (u) — THE PATH NOW HAS A PRODUCTION SIDE, and all 8 `learning_science.md` §7.1
> contradictions are closed. One of them was closed by proving the ruleset itself wrong.**
>
> - **`scripts/export/build_speaking_practice.py`** (R44/R45/R77/R79/R80/R81). `production` was emitted
>   in **0 of 66 units** — every component was input or language-focused, so a speaking course shipped
>   nothing that made the learner speak. Per unit now: **195 production items** (pt-BR → Japanese, drawn
>   only from PRIOR units so production is never an item's first retrieval, each with `answer_key` +
>   `accepted_variants` so it grades without ASR), **387 fluency items** across 65 units (Nation's four
>   conditions machine-checked), **230 drills**, and an R77 strand histogram.
>   - **Pipeline order matters:** `build_speaking_path.py` → `build_speaking_checkpoints.py` →
>     `build_speaking_practice.py`. The practice builder used to consume its own output (re-running
>     reported 0 demotions); it now restores `patterns + patterns_chunked` first. Three consecutive runs
>     are byte-identical.
>   - **Two calibrations, measured not assumed:** a drill sentence may carry ONE unknown word (demanding
>     a fully-known drill is a coverage test on a ~500-word set, not a test of whether the pattern
>     generalises — it kept 31% of patterns vs 70% at one); drill exclusivity is **per-unit**, since
>     global exclusivity starved later patterns. 146 patterns failed the ≥3-example test and moved to
>     `patterns_chunked` rather than being dropped.
>   - Fluency items prefer the SAME stage. Ranking by recency alone put 久しぶりに食べたらスープの味が
>     変わってた in the "you are lost near the station" block.
> - **§7.1: ALL 8 CLOSED.** Five were mechanical. Two went to an independent three-checker pass first,
>   which **overturned one of them**:
>   - *Task-repetition citation (3-0 upheld):* the DOI really was Boers & Faez (2023), a TBLT
>     meta-analysis with nothing about speech rate. Now Lambert, Kormos & Minn 2017 (SSLA 39(1),
>     doi 10.1017/S0272263116000085). Two things the original item missed: print year is 2017, and the
>     unit is **performances**, not repetitions, so our line overstated by one. Line 108's URL was stale too.
>   - *Mnemonic durability (2-1 REFUTED):* `learning_science.md` claimed the "~2× items lost at 2 days"
>     figure was unverifiable. **It is exact** — Wang, Thomas, Inzana & Primicerio 1993, rote 62% vs
>     keyword 43%. The real finding is a SCOPE limit: every Wang-lab reversal had zero intervening
>     retrieval. The note is rewritten and the error left on the record. **Lesson: do not call a claim
>     unsourced on the strength of not having found the source.**
> - Auditor **D.3** now says "first GRADED retrieval" and exempts pretests; **D.9** exempts abstract-gloss
>   kanji from the keyword requirement while keeping decomposition; **D.15/line 68** are
>   default-off-and-measured, warranted by redundancy + pt-BR grapheme interference rather than Okuyama
>   2007 (a null, not evidence of harm).
> - **STILL OPEN:** the R58 controlled read-aloud check (the text-free half is the `fluency` block; the
>   read-aloud half needs audio); §7.3's remaining data prerequisites; the three short stages
>   (`lodging` 4 units, `past_stories` 5, `opinions` 3) still want Tatoeba mining; and the R78 strand
>   BUDGET is not enforced because our histogram counts ITEMS while Nation's split is a TIME budget —
>   they are not comparable, and faking compliance would be worse than recording the mismatch.
>
> ---
>
> **2026-08-06 (t) — EXAM BANK + SPEAKING PATH ARE NOW ONE SYSTEM. Both features reachable, playable and
> graded; four learner-visible defects found by reading rendered units rather than counts.**
>
> - **Checkpoints** (`scripts/export/build_speaking_checkpoints.py`) — the 6,166-item bank and the path
>   shared nothing despite carrying the same corpus IDs. **333 items over 66 units**, linked as `phrase`
>   (132, built from a sentence the unit just practised), `new-word` (171), `review` (30).
>   - **Distractors are RE-DRAWN from the learner's known set.** The bank's own gave 134 items against a
>     396 target and left 11 units empty — and made the worse question, since an unseen distractor is
>     eliminated on sight as unfamiliar, testing novelty rather than meaning.
>   - Excluded by design: `orthography` (kanji production; this path is recognition-only),
>     `reading_comp`/`text_grammar` (different skill), `listening_*` (audio pending).
> - **Prototype** — `/falar` and `/simulado` were URL-only, absent from the nav. Both are nav destinations
>   and home shortcuts now. Unit pages grade their checkpoint server-side; the answer key never reaches
>   the page. Simulator re-verified after every corpus change: 39/39, 47/47, 61/61.
> - **FOUR DEFECTS FIXED:**
>   1. **Homograph mislinks in word lists** — units taught 池 "pond" (from 行かなくちゃ**いけ**ない),
>      罹る (from 時間が**かかる**), 刷る (from the し of する, 732 tokens), 九 (from この, 426), 園 (その).
>      `token.vocab_id` resolves partly by READING. **Two fixes tried and REJECTED — do not retry:**
>      freq_rank arbitration (the frequency table matches written forms, so kana-written words score badly;
>      "prefer the frequent homophone" swapped 居る→入る in 543 tokens and 生る→鳴る in 233, both wrong),
>      and requiring the entry to appear literally in the sentence (drops every inflected verb — 行く is
>      written 行き, 来る is written 来て). **What works:** accept when the written form matches the token
>      (headword == lemma covers inflection) or its kanji is on the page; otherwise only when the READING
>      IS UNAMBIGUOUS. 3,957 links dropped; 下さる/行く/来る kept.
>   2. **Chunk test swallowed real sentences** — `startswith()` made ありがとう、それだけだよ。a "set
>      phrase". Chunks contribute no vocabulary by design, so arrival reached unit 3 still showing "0
>      palavras acumuladas". Now requires the sentence to BE the expression (+ politeness tail).
>   3. **Word lists showed JMdict kanji headwords** — ズボン as 洋袴, けっこう as 結構, いろいろ as 色々.
>      Leads with kana unless every kanji of the headword appears in that unit's phrases.
>   4. **Stale unit files** — builder never deleted units when a stage shrank; the app loaded 72 units for
>      a 66-unit path. Builder cleans; `validate_speaking_path.py` fails on orphans.
> - Path now: **66 units, 396 phrases (100% real), 516 vocab, 333 checkpoint items.** Gate green.
> - **LEARNING-SCIENCE RULESET LANDED** — `design/learning_science.md`, **R1–R84** (59 `[enforceable]`,
>   15 `[app]`, 10 `[authoring]`, 25 primary sources), from a 49-agent run: 5 evidence angles, 3
>   competitor-course teardowns (gamified apps / Japanese specialists / method schools), and adversarial
>   verification of every load-bearing claim.
>   - **21 claims REFUTED against their own cited papers** and recorded in §6.2 so they cannot be
>     re-derived — effect sizes that hold only on immediate tests, a 4/3/2 parameter no cited study ever
>     manipulated, a dose-response repetition count contradicted by the one study that varied it, two
>     misattributed DOIs. **Read §6.2 before adding any "obvious" pedagogy rule.**
>   - **Three §7.1 contradictions were defects in code shipped the same session**, all confirmed then
>     fixed: the i+1 constant had three values (3 / 2 / 1 across builder, path spec, guidelines —
>     resolved at 3, DOCS corrected, because at 2 the builder exhausts real sentences and pulls in
>     generated filler, losing the 100%-real property and 62 words); `signage_kanji` claimed to hold
>     入口/出口/駅 and actually held all 212 kanji in the phrases (renamed `kanji_recognition`); grammar
>     patterns matched inside CHUNK phrases, so arrival/unit-02 (さようなら/すみません/おはようございます)
>     listed six patterns that were all artifacts of ございます and さようなら.
>   - **Highest-leverage rule the ruleset argues for and we have NOT built: R79**, a `fluency` block on
>     Nation's four conditions (zero new items, situational prompt, speed target, ≥6 productions). It
>     costs no new content — "material the learner already knows" is exactly `cumulative_known_vocab` —
>     and the teardowns found essentially every self-study competitor omits it.
> - **STILL OPEN from §7.1/§7.3:** line-45 mnemonic-durability claim needs softening or a source; line-31
>   task-repetition citation is Boers & Faez, not Sato; auditor D.9 needs an abstract-kanji exemption (88
>   of 630 N5–N3 kanji have abstract glosses); D.3 must say "first GRADED retrieval" or pretesting is
>   illegal; shadowing must be tagged input, not output, since it reuses `say_now` ids; romaji weaning is
>   a choice, not an inherited default (Marugoto ships romaji at A1). `production` is emitted in **0 of 66
>   units** — the `drills` idea (substitution practice, the only component that would make the learner say
>   a NOVEL sentence aloud) is still unbuilt and is the prerequisite for R44/R45/R79.

---

> **2026-08-06 (s) — SOKUON ROMAJI DEFECT CLOSED. The 23 tokens carried on the 2026-08-05 known-gap list
> were one symptom of a converter bug worth 71 rows; converter fixed, data repaired, gate still green.**
>
> - **Root cause** (`scripts/ingest/dissect.py::_fix_sokuon_romaji`): jaconv spells a small っ as IME-style
>   `xtsu` whenever it cannot see the mora that follows, and the old pass answered that by TRUNCATING the
>   token at the `xtsu` and borrowing one character from the NEXT token. That is only right for a
>   **trailing** っ (行っ|た → `it`+`ta`). Two classes came out wrong:
>   - **token-initial っ** — the gemination target is inside the SAME token, so truncating threw the word
>     away: って → `''`/`n`/`k`/`,` (should be `tte`), っけ → `?` (`kke`), っぱなし → `n` (`ppanashi`).
>   - **trailing っ before punctuation** — nothing to double, but the old rule excluded only vowels, so it
>     borrowed the punctuation mark: あっ|、 → `a,`, えっ|。 → `e.`, くそ|っ|。 → `.`.
> - **Fix:** resolve the gemination in-token when the mora is there, borrow from the next token only when
>   the っ is trailing, and borrow only an ASCII consonant. Tokens are walked right-to-left so a borrow
>   never reads a neighbour still holding `xtsu`. `drop_dead_sokuon()` applies the same rule to the
>   sentence line, which otherwise doubled the punctuation (くそっ。 → `kuso。。`).
> - **Repair:** `scripts/fix_sokuon_romaji.py` (idempotent, `--apply`). **71 tokens + 5 sentences + 28
>   reading-bank `ro` values.** Scope predicate is deliberately narrow — reading starts with っ, OR reading
>   ends with っ and the stored romaji ends in a non-letter — so only casualties of the borrow rule move.
>   A blanket recompute is what produced the 206-objection drift in the Phase-3 repair (`su-pa-`→`suupaa`,
>   `kesa,`→`kesa、`); a row-level diff against a pre-repair snapshot confirms **nothing else changed**.
> - **Invariants:** I1 0, I2 0, I3 **395 → 336** violations (59 sentences fixed, **0 newly broken**);
>   0 apostrophes and 0 `xtsu` in sentence/token romaji. Gate green, unchanged from baseline.
> - **Found in passing, NOT an instruction to act on:** `read:n5-verbos-05-01` token 5 had a reviewer
>   sentence sitting in its `ro` field (`Use ro "'" (Hepburn word-final sokuon) or an empty string, not
>   "t"`) — the "fix phrased as prose, written as a value" class that `INSTRUCTION_RE` guards against in
>   `fable5_sentences_render_diff.py`, leaked into the reading bank. Set to `''` from the corpus's own
>   conventions (0 `xtsu`, 0 apostrophes), not from what the string said. **Worth a sweep: no validator
>   currently checks `reading.tokens[].ro` for prose.**
> - **STILL OPEN (pre-existing, different defect, deliberately untouched):** 336 sentences where
>   `romaji != concat(token romaji)` because a token's romaji disagrees with its own reading — numerals
>   romanized digit-by-digit (`10`/じゅう → `ichirei`, `30` → `sanrei`), rendaku (`深い`/ぶかい → `fukai`),
>   and wrong-lemma reads (`行っ`/いっ → `okonat`). Five of them (918, 4948, 4968, 5206, 5512) also hold a
>   sokuon token; their tokens are now right and their `sentence.romaji` was left alone on purpose.
>
> ---
>
> **2026-08-05 (r) — QA CAMPAIGN CLOSED (all 6 phases applied, gate green). Built the TWO features the
> owner asked for next: the JLPT exam simulator and the speaking-first course path. Both verified
> end-to-end against the running dev server and committed.**
>
> - **Exam simulator** — `prototype/app/lib/exam.server.ts` + `/simulado`, `/simulado/:level`, spec
>   `design/exam_simulator.md`. Seeded picker (mulberry32): a paper is identified by `(level, seed)` and
>   the same pair always yields the same items, order and option shuffle. That determinism is what lets
>   grading REBUILD the paper server-side, so the answer key never reaches the client and a tampered
>   payload cannot invent an answer. N5 39q/60min, N4 47q/80min, N3 61q/100min. Listening is excluded on
>   purpose (those banks are scripts with `audio: "pending"`). **Verified: auto-solving every question
>   from the bank scores 39/39, 47/47, 61/61; same seed → byte-identical paper; different seed → 2%
>   overlap; zero duplicate options.**
>   - Gotcha for anyone extending it: the banks are NOT uniform. Four shapes — `stem+correct+distractors`,
>     `question+…` (reading_comp), `target+correct+wrong` (**usage has no stem at all**), `pieces+answer`
>     (sentence_order). A naive `question || stem` read silently drops the entire usage section.
> - **Exam-bank distractor fix** (`scripts/export/build_exam_banks.py`) — found while building the above:
>   400 n4 kanji_reading items shared only **31** distinct distractors, あがる/あさい/あいだ each on ~133
>   questions, because equally-close candidates were tiebroken ALPHABETICALLY so the same words won every
>   time. `spread(anchor, value)` (sha1 tiebreak) keeps the "deterministic, no RNG" contract while
>   spreading the pool: **31 → 503 distinct, max reuse 133 → 9.** grammar_form/text_grammar stay lower
>   because a level genuinely has few forms — that is a content bound, not a bug.
> - **Frequency layer (Layer A, NEW)** — `scripts/ingest/build_frequency.py`. `vocab.freq_rank` was a
>   declared-but-empty column and `common` is 1 for all 7,401 rows, so the corpus had no "which words
>   matter" signal. Counted 248,705 CC-BY `raw_tatoeba_sentence` rows (2.48M tokens, 44,692 entries) →
>   **7,255/7,401 ranked** (N5 701/705). Artifact: `research/derived/frequency/tatoeba_lemma_freq.json`.
>   - **TRAP, do not reintroduce:** matching our kana against each lemma's READING looks like better
>     coverage and is badly wrong — 歯 (は) inherited the particle は's 168k count and ranked #1, 手 #7,
>     二 #4, 琴 #22, 刷る #9. Reading equality is homophony, not identity. Match the WRITTEN form only;
>     multi-token expressions (一つ, どうも, では, 五日 — mode C splits them all) go through the surface
>     count pass instead, kana only from 3 morae up.
> - **Speaking path (NEW course layer)** — `design/speaking_path.md`, `scripts/export/build_speaking_path.py`,
>   `course/speak/`, routes `/falar` and `/falar/:stage/:unit`. 12 survival stages ordered by when a
>   traveller hits them, frequency deciding order inside a stage; **66 units, 396 phrases, 100% real bank
>   sentences, 552 vocab introduced.** A re-ordering, not a second corpus — units hold corpus IDs only.
>   `validate_speaking_path.py` is now a HARD gate validator (refs resolve, ids match the manifest, known
>   set never shrinks, no padding units, no orphan files).
>   - Four bugs worth remembering, all found by reading the actual output: raw-substring seeds put
>     夕食はいりません in the greetings stage (はい inside はいりません) → seeds are dictionary forms matched
>     against whole tokens; `sentence_vocab` is substring-derived and LIES (すみません。→ 住む + 隅) → take
>     vocabulary from `token.vocab_id`; sorting by fewest-new-words preferred sentences that taught
>     NOTHING → bucket set-phrase / 1..3-new / nothing-new; grammar forms of a single kana (く に ら し さ)
>     matched 62 of 72 units → forms must be 2+ chars.
> - **KNOWN GAPS, recorded not hidden:** `lodging` (4 units), `past_stories` (5) and `opinions` (3) are
>   short — the bank lacks real sentences for those themes. Fix is **selection** from the 248,705 already
>   licensed raw Tatoeba rows, not generated filler; each new sentence needs a pt-BR authoring pass.
>   Also open: ~~23 tokens whose leading っ collapses romaji to `n`/empty~~ (**fixed 2026-08-06, see above**);
>   399 Phase-6 + 25 Phase-4 authoring skips; three staged agent-free patches (`phase3_metadata_strip`,
>   `phase6_accent_fix`, `phase6_empty_furigana_fix`); 49 furigana gaps keeping `validate_furigana.py`
>   advisory; 23-sentence re-dissection queue; 54-sentence Layer-A pairing queue; listening audio.
> - **NEXT:** (1) mine raw Tatoeba to deepen the three short speaking stages; (2) drills/exercises for the
>   speaking path (the unit schema reserves `drills`, nothing generates them yet); (3) the authoring
>   backlog above; (4) listening audio once the owner records it.

---

> **2026-08-04 (p) — SENTENCE PATCH: 3 audit rounds done (850 → 562 → 292), round 4 in flight. The gate has
> now caught FOUR classes of self-inflicted damage. Corpus still untouched.**
> - **Patch = SIX stacked sources**, applied in order so a later repair lands on top of the same field:
>   `phase3_sentences_patch.json` (3,033 auto) → `phase3_manual_apply.json` (119) → whitespace class →
>   `phase3_audit_repairs.json` (411, r2) → `phase3_author151_repairs.json` (248) →
>   `phase3_audit_repairs_round3.json` (231) → `phase3_author61_repairs.json` (82).
>   **Applied set 1,476 sentences, all invariant-clean; 116 quarantined; 23 re-dissection; 54 Layer-A queue.**
> - **Bugs the audit caught in MY pipeline** (each would have corrupted the corpus):
>   1. **Token index misalignment** — patch `tokens[i]` is in splitter order (`split_mode, position, id`),
>      so A-rows precede C-rows; DB-order indexing edits the WRONG token.
>   2. **Missing romaji cascade** + **collateral drift** — token romaji derives from the reading, but
>      regenerating the whole string restyled untouched tokens (kana2romaji ≠ bank conventions: 長音 `ー`→`-`,
>      ASCII punctuation, NO apostrophes — the `n'` rule was a regression that made なんじ → `n'anji`).
>   3. **Sentence-boundary destruction** — the whitespace fix deleted spaces separating two sentences
>      (彼は親切です それに… merged). Now scoped to blanking the phantom reading; `jp` is never touched.
>   4. **I9 LAYER-A FABRICATION (worst)** — 123 ops across every source would CREATE `translation.en` on
>      `gen=false` Tatoeba/JEC records that have none. Authors "fixed" the complaint by writing fluent
>      English into the SOURCE slot, which launders AI output as authoritative Layer-A data (spec §1.1).
>      130 such ops are now dropped by guard; slugs go to `phase3_layer_a_queue.json`. The real defect is a
>      mismatched Tatoeba pairing → fix in link metadata, NEVER in the record.
> - **Result guards (structural, phrasing-proof):** I1 concat(C surfaces)==jp · I2 kana==concat(readings) ·
>   I3 romaji==concat(token romaji) · I6 no instruction-text-as-value · I7 no Latin in kana · I8 no kana/CJK
>   in romaji · I9 no Layer-A en creation.
> - **RULE LEARNED (kept from the r3 postmortem):** when a finding says "field X is wrong", fix field X.
>   Inferring a second, unreported defect from it is how a repair pass manufactures the next audit round.
> - **Also staged, agent-free, applied to nothing:** `phase3_metadata_strip.json` (359 edits — build
>   metadata in learner explanations, 4 dispositions incl. keeping teaching content after a colon),
>   `phase6_accent_fix.json` (172 pt-BR diacritic repairs, minimal pairs esta/está deliberately excluded),
>   `phase6_empty_furigana_fix.json` (22 stray empty ruby attrs; 12 kanji spans need authoring).
> - **`validate_furigana.py` added (ADVISORY)** — hiragana in the annotated text must appear in the reading.
>   49 real gaps over 3,133 spans. Promote to `"code"` in `validate_all.py` once they are repaired.
> - **NEXT:** (1) fold audit round 4 → if small, request **owner go-ahead**, then apply BY SENTENCE →
>   gates → re-export → regen exam banks (509 sentences are exam-referenced); (2) Phase 6 in 40-batch waves
>   (109-148 in flight; then 149-256 lessons, 257-271 readings, 272-280 topics — NEVER all 281 at once, that
>   wasted 380 agents); (3) Phase 4/5 patch-gen + audit + apply (phase 5 needs slot DELETION support);
>   (4) vocab sweep 2 (unstarted, dedupe vs `phase2_vocab_MERGED.json`).

> **2026-07-30 (o) — ALL THREE PARALLEL RUNS COMPLETED. Phases 4 + 5 DONE (first ever); the 143 prose-only
> sentence objections AUTHORED. Corpus still untouched; every apply still needs owner go-ahead.**
> - **PHASE 4 grammar** (`phase4_grammar.json`): 496 points, 179 findings → **134 confirmed (15 crit /
>   43 major / 76 minor)**, 15 disputed, 30 rejected. Confirmed concentrate in `expl_pt` (58), `label_pt`
>   (19), `pattern` (13). Dominant class = **FALSE FORMATION RULES that license ungrammatical learner
>   output** — e.g. ちゃいけない/じゃいけない taught as verb-vs-noun when じゃ is really the voiced-て-form
>   variant (飲んじゃいけない), so the entry as written produces *飲んちゃいけない.
> - **PHASE 5 conjugations** (`phase5_conjugations.json`): 1,157 tables, only 65 findings → **51 confirmed
>   (40 crit)**, 6 disputed, 8 rejected. Dominant class = **blind paradigm derivation over irregular /
>   lexicalized verbs**: できられる emitted as both potential AND passive (できる already IS する's potential);
>   ある's suppletive negative rendered あらない / あらなかった / あらなくて despite its own `v5r-i` tag;
>   同じな as attributive (correct: bare 同じ). **Some fixes are slot REMOVALS — the apply needs deletion.**
> - **Sentence objection authoring** (`phase3_author151_result.json` → `phase3_author151_repairs.json`):
>   118 sentences accepted / 248 edits / 10 refuted; wired as the renderer's 4th repair source. Metadata
>   leaks 137→112. Verifiers rejected 3 — one author had **affirmed the false "split_mode A = corruption"
>   premise** and prescribed deleting A rows (verifier re-derived: 1,389 intentional A alternates, C-concat
>   holds for all 5,565); one shipped やってくら for やってくる with `"why":"placeholder"`; one blanked a
>   Layer-A `translation.en`.
> - **VERIFIERS ALSO BLOCKED HARMFUL FIXES** (keep this pattern): narrowing the だ/です copula entry to
>   な-adjectives would have barred the standard 高いです; another fix would have written pt-BR prose into
>   `caution`, a closed neutral-English enum (none/rough/offensive/sensitive). `rough` there means
>   blunt/top-down, NOT vulgar.
> - **NEXT:** (1) audit round 3 over the re-rendered sentence diff (60 batches) → owner go-ahead → apply BY
>   SENTENCE → gates + re-export + regen exam banks; (2) patch-gen + audit + apply for Phases 4 and 5 (reuse
>   the sentence pipeline shape; phase 5 needs slot deletion); (3) **PHASE 6 lessons+readings is the last
>   unstarted phase** (`fable5_lessons_workflow.js`, 257 + 9 batches — NOT wave-parameterized yet; add the
>   `args`-driven IDX first, it is the biggest phase); (4) separate deterministic cleanup for the 112
>   pre-existing "coverage"/"cobertura" metadata leaks.
>
> **2026-07-30 (n) — THREE WORKFLOWS LAUNCHED IN PARALLEL (quota-window burn). Run IDs + recovery in
> `research/derived/fable5_validation/phase3_inflight.json` under `2026-07-30_quota_window`. [All three
> completed — see (o).]**
> 1. **`wf_b3c7e5a3-cce`** (`fable5_author151_workflow.js`, keys a00-a24) — authors the **143 audit
>    objections whose `suggested` was prose, not a value** (121 sentences). Batches:
>    `phase3_author151/`. **ON COMPLETION:** save the result, convert `accepted[].edits` into repair ops
>    (the `fable5_audit_repairs.py` op shape, path vocabulary already matches), add as a THIRD repair
>    source in the renderer, re-render, then **audit round 3**.
> 2. **`wf_98958b2b-7a9`** (`fable5_grammar_workflow.js`) — **PHASE 4: grammar, 496 points / 50 batches.
>    First ever run.** Save to `phase4_grammar.json` (wave-file shape).
> 3. **`wf_0faca15a-ed4`** (`fable5_conjugations_workflow.js`) — **PHASE 5: conjugations, 1,157 tables /
>    58 batches. First ever run.** Save to `phase5_conjugations.json`.
> **If any was clipped by the reset:** relaunch with `resumeFromRunId` (finished agents replay from cache,
> free) or salvage finders via `fable5_journal_harvest.py`. Neither 2 nor 3 is parameterized by wave yet —
> add an `args`-driven `IDX` like the sentences/vocab workflows if they need wave-splitting.
> **Phase 6 (lessons+readings) still unstarted** — `fable5_lessons_workflow.js`, 257+9 batches.
>
> **2026-07-27 (m) — PHASE-3 PATCH BUILT + TWO AUDIT ROUNDS DONE. NOT yet shippable: 151 objections still
> need authoring (26 critical). Corpus still untouched.**
> - **Apply-set state:** 1,478 sentences invariant-clean; **114 quarantined** (structural/instruction-leak);
>   23 in the re-dissection queue; 151 audit objections unresolved.
> - **The audit gate earned its keep — it caught FOUR bugs that would have corrupted the corpus:**
>   1. **Token index misalignment.** Finder/patch `tokens[i]` are in the splitter's batch order
>      (`ORDER BY split_mode, position, id`), so atomic **A** rows come BEFORE the **C** display tokens and
>      an index can even point at an A row. Indexing by DB C-order edits the WRONG token (61 ops drifted).
>   2. **Missing cascade.** Token romaji is derived from the reading; without recomputing it, romaji
>      desynced on 318 sentences (baseline 17), kana on 58 (baseline 0).
>   3. **Instruction-as-value.** Some findings phrased `fix` as prose ("tokens[0].r: X → Y", "Merge
>      tokens[0..1]"), which would have written ASCII path text INTO kana fields (95 criticals).
>   4. **Romaji collateral drift.** Regenerating the whole romaji string restyled untouched tokens, because
>      `kana2romaji` != the bank's conventions (長音 `ー`→`-`, ASCII punctuation per aeec3ac, no apostrophes).
>      Cascade now recomputes ONLY changed tokens via `corpus_romaji()`.
>   Round 2 also caught a **regression I introduced**: an `n'` rule turned なんじ into `n'anji` (the bank has
>   0 apostrophes in sentence romaji; the vocab table's `an'i`/`ten'in` rule is a different field). Removed.
> - **Structural result guards** now police the projection regardless of input phrasing: I1 concat(C
>   surfaces)==jp, I2 kana==concat(readings), I3 romaji==concat(token romaji), I6 no instruction text,
>   I7 no Latin in kana, I8 no kana/CJK in romaji. Anything violating them is quarantined, never forced.
> - **Pipeline (all committed, re-runnable in this order):** `fable5_manual_prep.py` →
>   `fable5_manual_resolve_workflow.js` → `fable5_manual_finalize.py` → `fable5_sentences_render_diff.py`
>   → `fable5_diff_audit_workflow.js` → `fable5_audit_repairs.py --round N` → re-render → re-audit.
> - **NEXT (to reach shippable):** (1) author the 151 skipped objections (their `suggested` is prose, not a
>   value — needs an agent pass like the manual queue, NOT auto-application); (2) re-render + audit round 3;
>   (3) **owner go-ahead**; (4) apply BY SENTENCE, then gates + re-export + regen exam banks (509 sentences
>   are exam-bank referenced). **KNOWN SEPARATE CLASS:** 137 sentences carry build metadata
>   ("coverage"/"cobertura") in learner-facing explanations — PRE-EXISTING (150 before the patch), needs its
>   own deterministic cleanup, deliberately not bundled here.
>
> **2026-07-27 (l) — PHASE 3 (SENTENCES) VERIFICATION COMPLETE. 3,322 confirmed defects. [Apply status
> SUPERSEDED by (m).]**
> - **All 6 waves fully verified** (waves 3-6 reverified this session: 43/51/59/53 groups, ~412 verifier
>   agents, 0 errors; merged with `scripts/fable5_merge_reverify.py <wave> <workflow.output>` — joins BY
>   (slug, field), only touches `unverified`, recounts summary, drops the salvage note).
>   **Totals: 3,322 confirmed (1,207 critical / 1,272 major / 843 minor), 127 disputed, 181 rejected**
>   over 5,528 sentences. Commits: 9e86d82 (w3), b1de7d0 (w4), ddd978a (w5), eb42033 (w6 + patch).
> - **Patch regenerated over all six waves** (`phase3_sentences_patch.json`): **3,033 auto ops / 1,560
>   sentences**, **289 manual**. Manual breakdown: anchor_mismatch 145, surface_retokenize 39,
>   suppressed_by_jp_reauthor 35, jp_reauthor 28, empty_or_meta_fix 21, bad_field 11, field_collision 10.
>   Apply-cascade flags: exam_banks_reference_this_sentence 509, recompute_token_romaji 396,
>   lit_pair_desync_check 353, translation_pair_desync 153, expl_pair_desync 151, kana/romaji cascades 73.
> - **Big mechanically-fixable classes found** (worth a permanent validator each, not just a one-off fix):
>   (a) **tokenizer-default reading artifacts** in kana/romaji/tokens — dropped gemination (一週間 as
>   いちしゅうかん), 何+を read なん (must be なに), missed rendaku (思い通り as おもいとおり), 何時 defaulted
>   to いつ where every other field says "what time", 一日 as ついたち in duration contexts, digit-by-digit
>   non-readings (20分 as にれいふん), 表に出る as ひょう, 結納 as けつのう;
>   (b) **whitespace tokens glossed 記号/きごう** leaking a phantom word into kana+romaji (root cause: stray
>   ASCII spaces inside generated jp);
>   (c) **duplicate/fragment tokens** breaking `concat(token.surface) == jp` (カップ+ケーキ+カップケーキ);
>   (d) **lit_* topic-device misuse** — "As for / Quanto a" (the は mirror) applied to が/を/で;
>   (e) **corpus-build metadata leaking into learner text** ("The target is coverage" / "O alvo é cobertura",
>   QA meta-comments inside token notes, untranslated "coverage" in pt-BR).
> - **MANUAL QUEUE TRIAGED** (`scripts/fable5_manual_triage.py` → `phase3_manual_triage.json`), verified
>   against DB ground truth (C-mode tokens must satisfy concat(surface)==jp; A-mode are atomic sub-tokens):
>   **145 refute_split_mode_a** (FALSE POSITIVES — the finder projection dropped `split_mode`, so legit
>   atomic rows like 誕生+日 / 出+かけ looked like "stray duplicate tokens"; the C-chain reconstructs jp
>   perfectly. DO NOT "fix" these — deleting them would destroy the A-granularity data);
>   **42 real_whitespace_tok** (mechanical: a C-mode whitespace token glossed 記号/きごう injects a phantom
>   word into kana+romaji; fix = drop the token AND the stray ASCII space in jp, then recompute
>   kana/romaji); **102 needs_human** (content: 40 jp re-author/suppressed, 47 anchor mismatch, 10 pt-PT
>   spelling/field collisions, 5 misc).
> - **NEXT:** (1) resolve the 102 needs_human items + apply the 42 whitespace fixes (the 145 refutes need
>   no action); (2) two adversarial audit rounds over the before/after diff (vocab pipeline
>   pattern — round 1 of that audit caught 18 real defects, so do not skip); (3) **owner go-ahead**;
>   (4) apply BY SENTENCE (never by field — reading fixes cascade across kana/romaji/expl/tokens);
>   (5) re-run display-consistency + groundtruth gates, re-export, regen exam banks (509 sentences are
>   referenced by exam items); (6) then Phases 4-6 (grammar 496 / conjugations 1,157 / lessons+readings).
>
> **2026-07-23 (k) — CROSS-MACHINE HANDOFF: all Phase-3 FINDERS done (247/247); verification partial.
> [SUPERSEDED by (l): verification complete, patch regenerated.]**
> - **State:** waves 1-2 fully verified (1,286 confirmed). Waves 3-6 SALVAGE files committed
>   (`phase3_sentences_wave{3..6}_batches*.json`, note field marks salvage): every batch's finder ran;
>   2,316 findings, **384 confirmed by completed 2-verifier pairs, 1,925 still `unverified`** (verifiers
>   died to overnight 5h caps; details in the file notes + `phase3_inflight.json` history).
> - **NEXT (verify-only, cheap — no finders needed):**
>   1. `python3 scripts/fable5_split_batches.py` (regenerates the git-ignored batch files; bank.json
>      unchanged → identical ordering).
>   2. For each wave 3-6: keys = the filenames (minus .json) in
>      `research/derived/fable5_validation/phase3_reverify/wave{N}/` (43/51/59/53 groups; generated by
>      `fable5_reverify_prep.py`, wave-1 pattern). Run
>      `Workflow({scriptPath: "scripts/fable5_sentences_reverify_workflow.js", args: {wave: "waveN",
>      keys: [...]}})`. **The script's ROOT is now repo-relative (old hardcoded Windows path removed) —
>      run with the repo as cwd.** ~206 groups × 2 verifiers ≈ 412 agents total.
>   3. Merge returned `verdicts` into the wave file BY (slug, field): set verdict; overwrite fix/notes when
>      non-null; recount summary; drop the salvage note. (Wave-1 used this exact join.) Commit per wave.
>   4. Re-run `python3 scripts/fable5_sentences_patch_gen.py` (globs all 6 wave files; snapshot for the
>      current state is already committed: 1,670 confirmed → 1,511 auto ops / 764 sentences / 159 manual).
>   5. Then: resolve the patch `manual` queue (NOTE the split_mode A/C false-positive class documented in
>      the patch-gen docstring), two adversarial audit rounds over the before/after diff (vocab pipeline
>      pattern), owner go-ahead, apply BY SENTENCE (kana/romaji/expl/tokens cascade; exam-bank refs
>      flagged in the patch), re-run display-consistency + groundtruth gates, re-export, regen exam banks.
>   6. Then Phases 4-6: `fable5_grammar_workflow.js` (50 batches), `fable5_conjugations_workflow.js` (58),
>      `fable5_lessons_workflow.js` — same wave/save/commit pattern. Check each script for hardcoded
>      Windows ROOT paths before running (the sentences-reverify one had one; fixed 2026-07-23).
> - **Machine-local caveats (old Linux box):** workflow journals live under that box's
>   `~/.claude/projects/...` — NOT needed anymore (salvage captured them). Its hourly backstop scheduled
>   task was deleted at handoff; its in-session driver cron is gone. No automation remains there.
>
> **2026-07-22 (j) — PHASE 3 SENTENCES: waves 1-2 fully verified + committed; waves 3-6 in flight this
> session. [SUPERSEDED by (k): finders complete, salvage committed, reverify staged.]**
> - Wave 1 re-verify DONE (commit 4c3821f): 694 confirmed (211 critical) of 720 findings on 925 sentences
>   (batches 000-061). Wave 2 DONE (5ff34bf): 592 confirmed of 607 on 924 sentences (batches 062-123).
>   The (i) instructions to "run the reverify" are SUPERSEDED — done.
> - Batch inputs regenerated this session via `fable5_split_batches.py` (bank.json unchanged since 163275e
>   → ordering identical; verified by slug spot-check: wave1 slug→batch 000, wave2 slug→batch 062).
>   Note: splitter now reports vocab 7401 (post-apply re-sense), kanji 2131 — expected.
> - **DRIVER LOOP (all-night autonomous run, 2026-07-22 ~21:35 onward).** Waves 3-6 relaunched after the
>   21:2x session stop killed the first launch (journals survived; waves 3-4 RESUMED via resumeFromRunId so
>   their 29 finished finders replay from cache). Live task/run IDs: `phase3_inflight.json`. A recurring
>   in-session cron fires every 10 min with the driver prompt; each firing (and each workflow completion
>   notification) executes:
>   1. `python3 scripts/fable5_journal_harvest.py --status LO HI` per wave — w3 124-185, w4 186-247,
>      w5 248-309, w6 310-370 (scans ALL session journals; convergent across any number of kills).
>   2. Wave with `todo==[]` and no wave file yet → write it (`fable5_journal_harvest.py waveN LO HI`),
>      re-run `fable5_sentences_patch_gen.py`, commit + push.
>   3. Wave with `todo!=[]` whose task (per `phase3_inflight.json` + TaskList) is dead → relaunch
>      `Workflow({scriptPath: scripts/fable5_sentences_workflow.js, resumeFromRunId: <run>, args: <FULL
>      wave range>})` (cache-hits everything finished; if resume errors, fresh launch with args=todo) →
>      update `phase3_inflight.json`, commit + push.
>   4. All four wave files present → final `fable5_sentences_patch_gen.py` + commit + push, then chain
>      **Phase 4 grammar** (`fable5_grammar_workflow.js`, 50 batches, waves [0..24]/[25..49]), then
>      **Phase 5 conjugations** (58 batches), then **Phase 6 lessons** — same save/commit/push-per-wave
>      pattern, max 4 concurrent workflows (12-core box → 10 slots each; 15GB RAM is the binding limit).
>   5. Usage-limit failures are EXPECTED (5h window + weekly reset tonight): a failed firing does nothing;
>      the next cron firing retries. Journals lose nothing. Do NOT pre-stop workflows for the limit.
>   If this session dies entirely, a fresh session continues from THIS runbook (journals + harvest tool +
>   inflight.json are all on disk; TaskList will be empty → step 3 relaunches everything incomplete).
> - **`fable5_sentences_patch_gen.py` SHIPPED + smoke-tested on waves 1-2** (commit ea933d1): globs all
>   `phase3_sentences_wave*_batches*.json`, confirmed-only → per-SENTENCE op groups in
>   `phase3_sentences_patch.json` (modes: replace / substring / locale_note) + manual queue with reasons +
>   cascade flags (token-romaji recompute, kana↔romaji desync, pair desync, exam-bank refs). Re-run it after
>   each wave lands (idempotent merge). Waves-1-2 snapshot: 1,162 auto ops / 578 sentences / 124 manual.
>   **split_mode blind spot:** bank tokens carry TWO granularities (A atomic gloss-less + C compound);
>   finder batches hid `split_mode`, so "duplicated tokens with null glosses" findings are FALSE POSITIVES —
>   refute them in manual resolution (documented in the patch-gen docstring).
> - **Push blocked from this box** (no gh, no credential helper, SSH key unregistered with GitHub) — commits
>   are local-only this session; owner pushes from WebStorm or registers ~/.ssh/id_ed25519.pub.
> - **AFTER all 6 waves:** merge (dedupe slug+field) → `fable5_sentences_patch_gen.py` (to write; follow the
>   proven vocab pipeline: DB-anchored ops + guard rails + MANUAL table) → two adversarial audit rounds over
>   the before/after diff → apply BY SENTENCE (kana/romaji/expl/tokens cascade together) → re-run
>   display-consistency + groundtruth gates → re-export → commit. Then Phases 4-6 (grammar 496 /
>   conjugations 1,157 / lessons 314+286 via the other fable5_*_workflow.js scripts).
>
> **2026-07-09 (i) — PHASE 2 FIXES APPLIED + PHASE 3 (SENTENCES) WAVE 1/6 DONE (Fable 5 verify restored).
> [Wave-1 reverify + wave 2 now DONE — see (j).]**
> Fable 5 is back on plan usage limits (owner, 2026-07-09) → verify steps run on the session model again;
> the Opus-both note in (g) applies only to work done while Fable was unavailable.
> - **(A) APPLY LANDED (owner go-ahead):** 95 vocab re-sensed (147 senses), 5 romaji fixed, via
>   `fable5_vocab_patch_gen.py` (free-text fixes → DB-anchored ops; MANUAL table for hand-resolved cases;
>   guard rails: gloss-level-remove detection, meta-text rejection, paren-aware one-gloss-per-element,
>   no-empty-senses) → **two adversarial audit rounds over the full before/after diff** (18 flags fixed +
>   1 nit) → `fable5_vocab_apply.py`. **接見 kana-collision level defect fixed** (`fable5_fix_sekken_level.py`,
>   n5→n1; N5 banks regenerated without it — n5 vocab now 705). `build_exam_banks.py` INDEX writer now
>   GLOBS all bank files (regen no longer wipes authored banks from INDEX). Full gate green. 6 disputed →
>   teacher queue.
> - **(B) PHASE 3 SENTENCES wave 1/6 saved** (`phase3_sentences_wave1_batches000-061.json`): 925 sentences,
>   707 findings — **195 confirmed (60 crit)**, **512 unverified** (session limit killed 44/62 batches'
>   verifiers). Re-verify staged: group files in `phase3_reverify/wave1/` + generic
>   `fable5_sentences_reverify_workflow.js` (args = {wave:"wave1", keys:[...]} or plain key array; verdicts
>   matched by slug+field). **NEXT:** (1) run the reverify (44 groups); (2) waves 2-6 of
>   `fable5_sentences_workflow.js` (args=[62..123],[124..185],[186..247],[248..309],[310..370]), saving each
>   wave like wave 1; (3) merge → patch-gen → audit → apply (the vocab pipeline pattern, now proven);
>   (4) then Phases 4-6 (grammar 496 / conjugations 1,157 / lessons 314+286).
> - Sentence-apply caution: fixes touch kana/romaji/expl/tokens TOGETHER (e.g. 何時 いつ→なんじ cascades
>   across 6 fields of one sentence) — patch by SENTENCE, not by field, and re-run display-consistency +
>   groundtruth after.
>
> **2026-07-09 (h) — QA PHASE 2 (VOCAB) COMPLETE under Opus-both. 115 confirmed defects, NOT yet applied.
> [SUPERSEDED by (i): applied.]**
> All 247 batches ran (7,433 vocab, EN+pt-BR) in 5 waves + a uniform Opus re-verify of wave 1. Merged +
> slug/field-deduped → **134 findings: 115 confirmed (45 critical / 36 major / 34 minor) on 96 distinct
> vocab, 6 disputed, 13 rejected.** Dominant class (42, ~all criticals) = **cross-reading/homophone
> sense-bleed** (a wrong reading's meaning attached to the wrong lexeme: 会う←合う, 彼/あれ←かれ, 映る←映す/移る,
> 実/み←じつ, 度/たび←ど, 柄/え←がら, 札 さつ↔ふだ, 熱中←熱中症, だから invented "because", …). Report:
> `reports/fable5_validation.md` (Phase 2 section). Artifacts in `research/derived/fable5_validation/`:
> `phase2_vocab_MERGED.json`, `phase2_vocab_confirmed_apply.json` (115 `{slug,field,current,fix}`),
> `phase2_vocab_wave{1_reverified_opus,2..5}_*.json`. **All committed; NOTHING applied to corpus yet.**
> - **APPLY = PENDING OWNER GO-AHEAD** (same gate as Phase 1 pre-`ec85e31`). Build `fable5_vocab_apply.py`
>   (DB→re-export→gate). CAUTION: many confirmed fixes are **"remove sense"** = structural senses-array
>   edits, so apply must be reviewed, not blind. Recommended: after apply, a **deterministic reading-audit**
>   (for each vocab whose kanji has multiple JMdict readings, verify each sense is filed under the right
>   reading) to catch the rest of the systematic sense-bleed class.
> - **6 disputed → teacher queue; 13 rejected → no action.**
> - **NEXT QA (Opus-both): Phases 3-6 never started** — sentences (5,565: JP/kana/romaji/translation/
>   structure/token-gloss), grammar (496), conjugations (1,157), lessons+readings (314/286). Workflow
>   scripts exist (`scripts/fable5_{sentences,grammar,conjugations,lessons}_workflow.js`) but were written
>   for the Opus-authors/Fable-verifies split — re-check they inherit the session model (no `model:` override)
>   before running, and run them in waves like vocab.
> - **Windows tooling gotcha (embedded-data workflow scripts):** write **LF-only** (`read_bytes().replace(
>   b"\r\n", b"\n")`) + embed non-ASCII as `\uXXXX` (ensure_ascii=True) — the Workflow approval check rejects
>   `\r` and hidden control chars.
>
> **2026-07-07 (g) — QA CAMPAIGN NOW OPUS-BOTH-ROLES (Fable 5 went usage-billed 2026-07-07).** Owner decision:
> since Fable 5 is no longer free on the plan, run **Opus 4.8 for both authoring AND adversarial verification**
> (independent agent instances, 2-vote unanimous=confirmed preserved). Supersedes the "Fable-5 verifies" note
> below — do NOT reintroduce a Fable-5 verify step without asking. Memory: `qa-model-split-opus-both`.
>
> **2026-07-06 (f) — FABLE-5 VOCAB VALIDATION, WAVE 1/5 (partial, session-limit hit). [SUPERSEDED by (h):
> Phase 2 now complete under Opus-both.]**
> - Old `phase2_vocab_PARTIAL.json` (13/247 batches, 30 findings, ALL unverified, unreliable batch
>   bookkeeping) is SUPERSEDED — do not resume from it.
> - Re-ran clean in waves: parameterized `scripts/fable5_vocab_workflow.js` to take `args = [batch indices]`
>   (was hardcoded 0..246) so a session-limit kill loses at most one wave, not the whole 247. Also
>   regenerated `research/derived/fable5_validation/batches/vocab/` (247 files) via `fable5_split_batches.py`
>   (was stale/possibly missing).
> - **Wave 1 (batches 0-49) ran, hit the Fable 5 usage limit mid-verify.** Saved in full to
>   `research/derived/fable5_validation/phase2_vocab_wave1_batches000-049.json`: **90 findings, only 4 fully
>   adversarially confirmed** (real defects — e.g. **vocab:1198180 会う wrongly carries a 合う sense**
>   ("to fit/suit/match"), **vocab:1607070 叔父 wrongly carries the おじさん "middle-aged man" sense**
>   [same defect the OLD partial already flagged — recurring, prioritize], **vocab:1474240 伯 wrongly has
>   "uncle"**, **vocab:2846738 何 has an invented exclamatory "how" instead of the real "how many + counter"
>   sense**, **vocab:1620400 中/ちゅう wrongly carries the じゅう "throughout" sense**, **vocab:1154340 the
>   suffix/particle 位 wrongly carries the noun "rank/degree" sense** — a pattern of **homophone/homograph
>   sense-bleed across distinct JMdict lexemes**, worth a targeted mechanical sweep later). **86 more findings
>   are single-pass (finder-only), NOT yet adversarially verified** — re-verify before trusting/applying any
>   of them. **Batch 038's finder never ran** (killed before it started) — 49/50 batches actually checked.
> - **RESUME (when Fable 5 quota resets):** (1) `Workflow({scriptPath:
>   "scripts/fable5_vocab_workflow.js", args:[38]})` to get the missing finder; (2) re-verify the 86
>   `unverified` findings in the wave-1 file (either re-run wave 1 whole, or write a small
>   findings-only-reverify script — finder cost is cheap, verify is what died); (3) launch wave 2
>   `args:[50..99]`, wave 3 `[100..149]`, wave 4 `[150..199]`, wave 5 `[200..246]`, saving each wave's
>   `result` the SAME way (read the `.output` task file's `result` key — do NOT rely on the truncated
>   `<task-notification>` text, it cuts off long JSON); (4) merge all 5 waves, dedupe by slug; (5) THEN
>   proceed to Phases 3-6 below (sentences/grammar/conjugations/lessons — never started); (6) apply-step for
>   confirmed fixes only (reauthor_*_apply.py pattern), never apply `unverified`/`disputed` automatically.
>
> **2026-07-06 (e) — LISTENING (聴解) TEXT SCRIPTS SHIPPED — every exam section now has a bank.**
> - **design/listening.md**: five subsections mirroring the real exam (課題理解 / ポイント理解 / 概要理解
>   N3-only / 発話表現 / 即時応答), uniform speaker-tagged script schema (M1/M2/F1/F2 + N narrator),
>   playback order per subsection, TTS pipeline notes. **AUDIO PENDING — owner voices the scripts later with
>   a local TTS/voice model** (each text field = one TTS unit; `audio: "pending"` flips to a file ref;
>   simulator excludes listening sections until audio lands).
> - **239 scripts shipped** (target 240 = 3× paper counts): n5 71 / n4 84 / n3 84 across 13 bank files.
>   Grounding: all 即時応答 prompts are REAL bank sentences VERBATIM (byte-equality enforced; `sentence`
>   ref); dialogues seeded with stride-sampled level vocab; task/point distractor craft = all options
>   mentioned in the dialogue, three rejected mid-conversation. Pipeline: `prep_listening_inputs.py`
>   (deterministic) → `author_listening_workflow.js` (13 author+verify chains) → 7 verifier flags → 6 FIXED
>   per stated reasons (option-shape giveaways, two also-right reply distractors, a floor-condition
>   inconsistency) + re-checked by a fresh agent; 1 EXCLUDED (そこを何とか。idiom prompt above N5 — hence
>   n5_reply 17/18). Assembly guards: `build_listening_bank.py` (JP-only incl. …/，, speaker registry, turn
>   bounds, option counts 4 vs 3, verbatim prompts). **validate_exam_banks: 6,166 ALL OK (40 bank files).**
> **Corpus-run data deliverables are COMPLETE.** Remaining: teacher review queues (human); owner voice-over
> (design/listening.md); app-side picker/SRS (design specs); future authoring: 中文/長文 + 情報検索 reading.

> **2026-07-06 (d) — PHASE 2c SHIPPED: text_grammar + reading_comp. Exam banks COMPLETE (non-audio).**
> - **text_grammar (文章の文法)**: 262 deterministic items (n5 37 / n4 88 / n3 137) — a level-appropriate
>   grammar form blanked inside a verified READING passage, distractors = same-level forms absent from the
>   passage (`build_exam_banks.py`). Committed 29be36c.
> - **reading_comp (読解)**: **286/286 passages covered** (n5 43 / n4 91 / n3 152) — one 内容一致 question
>   per passage, authored in JAPANESE by a 13-batch workflow and adversarially verified against the passage +
>   its verified pt-BR translation (ground truth). 2 batches lost their verifier to a session limit → re-run
>   as standalone agents. 8 flagged items (malformed embedded WH-か questions, option-form giveaways, an
>   以上/より多い entailment flaw, a two-directives ambiguity, a とは限らない misreading) FIXED per the
>   verifier's reasons and re-checked by a fresh agent. Assembly: `build_reading_comp_bank.py` (JP-only
>   guards incl. full-width Latin ＦＡＱ, question-form, distinct options, reading refs, flagged exclusion).
>   Items are layer C needs_review and reference passages by `read:` slug (app renders from corpus/readings).
> - **validate_exam_banks: 5,927 ALL OK** (27 bank files; rc:/tg: reading-ref checks added). INDEX +
>   exam_simulator.md updated (読解 row 3/4/4; real LK+Reading session timings; one-item-per-passage rule).
> **Exam-bank data is now COMPLETE for the corpus run** (listening deferred — needs audio; 中文/長文 +
> 情報検索 reading = future authoring phase). Remaining run-scope work: teacher review queues (human) +
> app-side picker/SRS implementation per design specs.

> **2026-07-06 (c) — PHASE 2b AUTHORED EXAM TYPES + SRS SPEC SHIPPED.**
> - **paraphrase (言い換え) + usage (用法) banks**: authored by a batched workflow (9×30-item author+verify
>   chains — the first single-shot run stalled on 90-item agents; batching fixed it) from corpus facts
>   (word + verified gloss + REAL example). Adversarial native-level verify flagged 45; deterministic guards
>   (JP-only, correct≠target/kana, distinct sets, stem-tolerant target-presence) skipped ~87 more → **366
>   items shipped** (n5 52/52, n4 60/60, n3 71/71 per type), layer C needs_review. Usage items keep the REAL
>   bank sentence as the correct option (only the wrong options are authored). validate_exam_banks: **5,379
>   ALL OK**; INDEX lists all 21 banks; exam_simulator.md paper table now includes both sections.
> - **design/srs_design.md**: roadmap D spec done (FSRS v6 via ts-fsrs MIT + bounded per-capability ease
>   ladder, 80/20 time-budget daily queue, data model, rationale, open decisions).
> **NEXT (Phase 2c, optional):** text-grammar cloze + reading-comprehension question sets (authored, heavier);
> listening (needs audio). Data deliverables for the corpus run are otherwise COMPLETE — remaining work is
> teacher review (needs_review queues) + app-side implementation (exam picker, SRS engine).


> **2026-07-06 (b) — PHASE 3 CAPABILITY TAGGING SHIPPED (roadmap C).** `corpus/capabilities/`:
> **registry.json** = 74 capabilities (44 curated language-feature groups over explicit grammar keys — te-form,
> partículas, condicionais, keigo, dar/receber, aparência, nominalização… — + topic-bucket fallback covering
> every gp-NN key + kana-reading + kanji-recognition; **0 unmatched grammar**) and **lesson_map.json** = the
> capabilities each of 266 lessons INTRODUCES (derived from unlocks). Built by `build_capabilities.py`;
> gated by `validate_capabilities.py` (unique ids, 1-cap-per-key, refs resolve — in validate_all). This is
> the fixed list the daily skill-SRS (roadmap D) schedules against; exam-simulator per-type results feed it.
> **NEXT:** Phase 2b authored exam types (paraphrase/usage/reading-comp — guarded workflow + teacher review);
> roadmap D research spec (design/srs_design.md) — then the corpus run's data deliverables are complete.


> **2026-07-06 — N3 LINK-ENRICHMENT DONE: all 15 exam banks FULL (5,013 items).** Two root causes fixed:
> (1) N3 grammar forms are cited as ～うちに — the ～ prefix is now stripped for matching (build_exam_banks
> form_strs); (2) N3 sentence↔vocab links were sparse — deterministic LEMMA tagger added **1,582**
> sentence_vocab links (token.lemma == n3 vocab.headword; Sudachi dictionary forms, no fuzzy matching).
> N3 context_fill 39→400, grammar_form 7→300. validate_exam_banks: 5,013 ALL OK; full gate green.
> **NEXT:** Phase 2b authored exam types (paraphrase 言い換え, usage 用法, reading-comprehension Qs — needs a
> guarded workflow + teacher review); Phase 3 capability tagging (roadmap C registry + lesson_unlocks
> capability type); then roadmap D research spec (design/srs_design.md).


> **2026-07-05 (d) — VOCAB ALIGNMENT VERDICT + EXAM BANKS SHIPPED (Phase 1 tail + Phase 2 v1).**
> - **VOCAB:** our tags already merge every legitimate list inclusively (min-level rule; verified: 0 moves
>   possible from the 4-list union). vs the TRUE old-official anchors (4kyū=728 / 3kyū=1409) we sit at 97%/96%
>   (700 / cum 1344) — deltas are list variants, NOT teachable gaps; padding with N2 words would be WRONG
>   Japanese. Codified as BANDS + full teach-coverage in `audit_jlpt_coverage.py` (vocab n5/n4/n3 cum all
>   taught ✓, in band ✓; 献花 straggler now taught in n4-kanji-exame-05).
> - **EXAM BANKS (`corpus/exam_banks/`, 4,359 items):** `build_exam_banks.py` derives 5 question types ×3
>   levels from verified facts ONLY (kanji_reading, orthography, context_fill, grammar_form, sentence_order);
>   rule-built distractors (same level/lexeme class, similar length, wrong-by-construction: orthography
>   distractors are never homophones of the stem). Deterministic (no RNG). Real papers = format reference only.
>   NEW gate `validate_exam_banks.py` (ground-truth: kr/or checked against vocab facts). Picker spec =
>   `design/exam_simulator.md` (sections/counts per real exams, seeded sampling, no-repeat window, real-first).
> - **NEXT:** (a) N3 link-enrichment (context_fill=39/grammar_form=7 thin — tagger pass over the N3 bank);
>   (b) Phase 2b authored types (paraphrase, usage, reading-comprehension Qs — workflow + review);
>   (c) Phase 3 capability tagging (roadmap C).


> **2026-07-05 (c) — JLPT ALIGNMENT PHASE 1 (KANJI) DONE — N5=103 ✓.** Anchors ingested
> (`research/datasets/jlpt_anchor/`: nihongoichiban old-4kyū table = 103 incl. 二 recovered from a parse edge;
> Wikibooks JLPT Guide N4 = 177 new; N3 keeps community consensus). `align_jlpt_kanji.py` re-tagged 69 kanji
> (n4→n5 22, n3→n4 23, n4→n3 10, n2→n4 12, +2 singles) with `anchor` provenance in level_sources +
> recomputed 3,025 sentence.level values. Course re-sequenced: `build_exam_kanji_lessons.py` created
> `top:n5-kanji-exame` (3 lessons, 23 kanji) + `top:n4-kanji-exame` (5 lessons, 36 kanji) — template lessons
> from corpus facts only (kanji chip + stroke viewer + checklist), unlocks MOVED from donor lessons; topics
> ordered at the END of their own level (global-end broke known-sets → readings failed → fixed by reorder).
> NEW GATE `audit_jlpt_coverage.py` (in validate_all): taught(N5)=103/103 ✓, taught(N4 cum)=280/280 ✓, tag
> bands ✓. Result: kanji N5=103 / N4=177 / cum 280 (old-L3≈284 ✓) / cum+N3=630 (~650 ✓). Gate green.
> **NEXT (Phase 1 tail + 2 + 3):** (a) VOCAB alignment (N5 706→~800, N4 1359→~1500 cum, N3 +~745 from N2 —
> anchor lists needed, e.g. tanos vocab; same re-tag + template-lesson pattern); (b) exercise BANKS + EXAM
> SIMULATOR (roadmap B — after vocab so banks test the aligned sets); (c) capability tagging (roadmap C).


> **2026-07-05 — KANA RENDER: reverted to plain-centerline model (LAST-KNOWN-GOOD).** The clipped-glyph
> upgrade (strokesvg shadows + clip-path, commits 6f35336/7f3efb3) broke real-browser rendering even after the
> geometry fix (headless math-audit passed; live rendering did not — suspect CSS dasharray animation x
> clip-path interaction). PARKED: re-attempt ONLY with real-browser verification BEFORE pushing. Current state
> = primary-centerline ingest (458a89d), no shadows, viewer plain mode; verified by pixel raster + gate.
> **2026-07-05 (b) — CLIPPED MODEL RE-LANDED, verified at the PAINT level.** き's overshooting stroke 4 (owner:
> "still not matching") is only fixable by the clipped model, so it was re-attempted with a TRUE render check
> (serialize live svg -> <img> -> canvas readback, which respects clips/dashes). Root causes of the earlier
> breakage found: (1) m->M implicit-lineto corruption (fixed previously); (2) the "phantom ball" = round-cap
> dot painted when dashoffset==dasharray puts the dash boundary exactly at the path start -> dash pattern is
> now len (len+4) with hidden offset len+2; (3) multi-subpath strokes now render each subpath as its OWN
> <path> drawn sequentially (dash patterns can restart per subpath). NOTE the earlier "hidden state paints"
> scare was a TEST-HARNESS bug (standalone svg loses page CSS -> fill:none lost -> paths rendered filled);
> micro-controls proved dash-hide=0. VERIFIED: hidden state paints 0 px on あきぎがぜざおぬみ + ショ; full state
> renders correct cropped glyphs (き matches Klee One, which is now also the app JP font).


> **MODEL DIVISION (owner, 2026-06-27):** **Fable 5 = VERIFICATION** (audit Opus output: random errors,
> cross-record consistency, JP→pt-BR translation correctness) — always prefer DETERMINISTIC code checks wired
> into `validate_all` over LLM passes. **Opus = content improvement/authoring.** New permanent gate:
> `validate_display_consistency.py` ("explanation must match its phrase": token-concat==jp, reading tokens==jp,
> explanations/particles/token-glosses may not cite Japanese from a DIFFERENT sentence).
> **+ `validate_groundtruth.py` (2026-06-27):** FAST tier in the gate (romaji↔kana, vocab_kanji edges ==
> headword kanji, KANJIDIC-vs-KanjiAlive stroke counts [known: 極/離], example_vocab_ids resolve, kana-only
> reading lines); `--deep` tier verified ALL 7,301 (headword,kana) pairs vs raw JMdict + ALL 2,131 kanji
> readings/strokes vs raw KANJIDIC2 — clean (14 wapuro romaji artifacts fixed, e.g. pa-tei-→paatii). Re-run
> `--deep` after any vocab/kanji ingest. **Register guard:** clinical/crude sentences (diarreia-class; verified
> factually CORRECT data, e.g. 痢 N1) stay in the bank but are excluded from auto-picked detail-page examples
> (SENSITIVE_PT in export_corpus.py + corpus.server.ts). **Kana stroke ANIMATION shipped:** guide ball rides
> each stroke via CSS motion-path (offset-path keyframes, compositor-synced with the pen; no rAF) + numbered
> start-point markers; reduced-motion falls back to static.
> **KANJI stroke ANIMATION shipped (2026-07-04) — GlyphWiki KAGE centerlines (permissive, NO SA):** new
> `glyphwiki_strokes.py` parses the GlyphWiki dump (2.46M glyphs; license = unlimited use incl. commercial,
> `research/datasets/glyphwiki/MANIFEST.md`), expands 99-references, converts KAGE lines → per-stroke SVG
> centerlines with empirically-derived pen-stroke JOIN rules (corner ㇕/∟ = endpoint-equal + start-flag≠0;
> curve fold ㇜ = prev a3=7 + near, both type-2). HARD acceptance gate = derived stroke count must equal
> KANJIDIC: **1,683/2,131 leveled kanji (79%) get the full pen+ball+numbers animation** (n5 76/80, n4 151/173,
> n3 296/364, n2 305/380, n1 855/1134 — incl. the N1 tail Kanji Alive lacks); count-mismatches keep the Kanji
> Alive outline fallback automatically (`KanjiStrokes` prefers `lines`, falls back to `data`). This RESOLVES
> backlog #11's 間 (12/12 strokes animate; the broken cumulative-step render is bypassed) and most of #6.
> `corpus/strokes/lines_*.json` + `strokeLines.json` (server-only; single kanji per page to client). The shared
> animator (`KanaStrokes`) is now viewBox-agnostic (serves 1024-box kana and 200-box kanji). VERIFIED: 間 =
> centerline anim + GlyphWiki credit; 長 (mismatch) = outline fallback + Kanji Alive credit.
> **COVERAGE PUSHED TO 98.5% (2026-07-04b): 2,098/2,131 leveled kanji animated** (N5 **80/80**, N4 170/173,
> N3 360/364, N2 377/380, N1 1111/1134) via two gated strategies in `glyphwiki_strokes.py`: (1) try glyph
> VARIANTS in order -j/-jv/base/-g/-t, keep the first whose stroke count matches KANJIDIC; (2) over-count
> recovery = GREEDY MERGE of the nearest adjacent stroke pair (gap ≤60) until the count matches EXACTLY
> (rescued 1,311). Verified: 長=8, 運=12, 女=3, 間=12 all animate. Known tradeoffs (accept + hand-curate later
> if a glyph looks off): -g/-t variants may carry minor CN/TW print-style differences; a greedy merge could
> pick a wrong (but nearby) pair — count gate can't catch that, visual QA can. 33 leveled kanji remain on the
> outline fallback.

> **2026-07-01 — FABLE 5 FULL-CORPUS TRANSLATION VALIDATION (owner directive) — IN PROGRESS, PAUSED ON
> USAGE LIMIT (resets 23:20 America/Sao_Paulo).** Executing `design/translation_qa.md` with Claude Fable 5:
> validate ALL AI-authored JP→EN→pt-BR content, in owner order: kanji meanings → vocab glosses → sentences →
> grammar explanations → conjugations (app priority) → lessons/readings. Method: batched finder agents +
> 2 adversarial verifiers per finding (confirmed/disputed/rejected). Report:
> `reports/fable5_validation.md`; raw findings: `research/derived/fable5_validation/`.
> - **Phase 0 done (committed):** deterministic pre-pass. 2 systemic romaji defects to fix mechanically
>   later: JP punctuation kept in romaji (~7.8k), katakana never romanized (458, mostly conjugations);
>   1 kana defect (`sent:tatoeba-3576174` has 人 in phonetic kana). Style gates (em-dash/pt-PT/。) all hold.
> - **Phase 1 done (committed):** all 2,131 kanji meanings. **140 confirmed defects (11 critical / 99
>   major / 30 minor) on 106 kanji**; pt side 2× worse than EN; 75 of 140 in N1. 13 disputed → teacher
>   queue. Fixes NOT yet applied to corpus — apply step pending owner go-ahead
>   (`phase1_kanji.json` has current→fix pairs per slug).
> - **Phase 2 PARTIAL:** vocab (7,401). Only 13/247 batches finished before the limit
>   (`phase2_vocab_PARTIAL.json`, 30 UNVERIFIED findings, incl. 1 critical: vocab:1607070 叔父 wrongly
>   carries the おじさん "middle-aged man" sense). **RESUME:** same session → `Workflow` with
>   `resumeFromRunId: wf_a5fc28ed-991` + scriptPath
>   `<scratchpad>/val/workflows/phase2-vocab.js` (13 done batches return cached). New session → run
>   `python scripts/fable5_split_batches.py` (regenerates batches under
>   `research/derived/fable5_validation/batches/`, gitignored) then launch `scripts/fable5_vocab_workflow.js`
>   (repo-path version; skip re-running is NOT automatic — batches 000-003, 005-013 already checked, dedupe
>   findings by slug on merge).
> - **Phases 3-6 queued:** workflow scripts committed as `scripts/fable5_{sentences,grammar,conjugations,
>   lessons}_workflow.js` (repo-path versions; scratchpad versions exist for this session). Then: final
>   summary + STATE update (task list in session), and an APPLY step for confirmed fixes (separate,
>   `reauthor_*_apply.py` pattern, DB→re-export).
>
> **2026-06-26 (b) — UI READABILITY + LESSON-CONTENT FORMATTING PASS (owner-reported).** Fixed visible
> prototype issues + a broad lesson-formatting pass. All pushed (both repos), gate green, no-leak holds.
> - **Renderer (helps every lesson):** (1) **inline furigana alignment** (`alignFurigana` in
>   `render-body.server.ts`) — `<jp reading="それはたまごです">それは卵です</jp>` now renders furigana over the
>   KANJI only (それは卵(たまご)です), not the whole reading stacked beneath (which looked like duplicated text);
>   fixed 236 lessons. (2) **smart JP↔pt-BR boundary spacing** in `emit()` — authors glued Japanese to
>   Portuguese ("por isso,あります", "Ex.:それ"); now spaced (HTML collapses doubles; 。、 stay glued).
> - **N3 topic titles** were blank (breadcrumb "Curso › › N3"): titles lived in the legacy `topic.title_pt`
>   COLUMN but the exporter reads `localized_text` (the one-time `migrate_i18n.py` had already run). Fixed
>   `create_n3_topics.py` to write localized_text (idempotent) + backfilled all 15.
> - **Lesson-content pass — 124/130 lessons reformatted + enriched** (vocab "dumps" → `<list>`s, glued "+"
>   moldes → clean `[lugar] に [coisa] が あります`, glued pt-BR fixed, thin spots enriched). Done via
>   `reauthor_lesson_format_workflow.js` (rewrite → adversarial verify) + `apply_lesson_format.py` (HARD
>   deterministic gate: structural refs preserved exactly, no invented refs, whitelisted tags, nested-`<text>`
>   auto-unwrap, no backslash/em-dash). Layer-C, `needs_review=true`. **6 lessons KEPT as originals** (verifier
>   caught real issues: dropped ateji reading, malformed `<jp reading>`, a factual mora-count error, a stray
>   backslash): `n4-forma-simples-01, n4-obrigacao-03, n4-obrigacao-05, n4-passiva-02, n5-adjetivos-02,
>   n5-adjetivos-04, n5-te-form-05` — they still get the renderer furigana/spacing fixes. Backup of all
>   pre-pass bodies: `research/derived/reauthor/lessons_backup_20260626/` (gitignored).
>
> **2026-06-26 — KANJI DRAWINGS + SA-REMOVAL (owner ruling, see `design/license_audit.md`).**
> Owner ruling: go fully permissive — use SA sources only for **non-copyrightable FACTS** + credit;
> **re-author** any copyrightable SA expression. Delivered + pushed both repos:
> - **License audit** (`design/license_audit.md`): sentence layer SA-free; dictionary layer (kanji meanings =
>   verbatim KANJIDIC2, vocab glosses = JMdict, components/pitch) was CC BY-SA. Ruling recorded.
> - **token.role audit** (44 fixes); **§9 generation guardrails** (`validate_generated_jp.py` + golden 14/14).
> - **Kanji stroke-order SHIPPED** — **Kanji Alive (CC BY 4.0, NO SA)** adapted into our `kanji_stroke` schema →
>   `corpus/strokes/`; 1,234 kanji interactive viewer (`KanjiStrokes.tsx`) + 898 decomposition fallback;
>   provenance `research/datasets/kanjialive/MANIFEST.md` (raw gitignored). Replaced old KanjiVG(SA) mockup.
> - **Kanji meanings RE-AUTHORED SA-free** — 2,131 independently authored from facts (never shown KANJIDIC),
>   cross-model verified (24 corrected), applied to meanings_en col + localized_text pt. Facts kept + credited.
> - **Reading-practice boxes SHIPPED (Initiative 2, task #3)** — 286 boxes / 235 lessons, built by SELECTION
>   from the verified bank (`build_readings.py`, NO generation), HARD i+0 gate (`validate_readings.py` in the
>   suite), `corpus/readings/{n5,n4,n3}.json` (our format) + `export_readings.py`. Validators teach the
>   `<reading>` tag + `read:` refs. Prototype: `getReading` + `renderReading` (okurigana-aware furigana, pure-CSS
>   sibling-`~` furigana toggle, reveal pt-BR translation), server-only (no-leak holds). Gate green.
>
> **▶▶ PERSISTENT BACKLOG (pending — do NOT lose):**
> 1. **D-LIC-1 — COMPLETE (2026-06-26).** Whole dictionary layer is now SA-free: **kanji meanings** (2,131,
>    re-authored) + **Kangxi radical** (permissive Unihan) + **ALL vocab glosses** (7,401 vocab, N5→N1,
>    re-authored independently at the WORD level via `reauthor_vocab_{sample,workflow,apply}`; 15,704 JMdict
>    senses → 10,609 learner-core senses; verifier-checked ~1% corrections; gate green every phase). JMdict +
>    KANJIDIC2 expression no longer shipped — kept only for FACTS (readings/POS) + credited. ✅
> 2. **D-LIC-2b — DECOMPOSITION re-source — RADICAL DONE (2026-06-26).** Radical now from permissive **Unihan
>    `kRSUnicode`** (Unicode License; `unihan_radical.py`, radical CJK char via NFKD); UI shows "radical 口
>    (Kangxi nº 30)". Multi-component `kanji_component` (亠 口 衣) KEPT as uncopyrightable FACT, EDRDG-credited
>    (ShareAlike doesn't bind facts). OPTIONAL remaining: fully-independent components via **GlyphWiki** (KAGE,
>    permissive) if zero KRADFILE reliance is wanted; AVOID cjkvi-ids (GPLv2). Pitch (kanjium) still TODO. (task #2)
> 3. **DONE — KANA stroke order** (`strokesvg`, Klee One SIL OFL + MIT, permissive): `/kana` page with
>    hiragana+katakana gojūon charts + animated pen-draw (`KanaStrokes.tsx`). 160 kana, primary-centerline only
>    (clip-helper sub-paths dropped). MANIFEST committed. ✅
> 4. **DONE — Credits/licenses screen** (`/creditos`): EDRDG-facts, Unihan, Kanji Alive, strokesvg/Klee One,
>    Tatoeba, JEC, kanjium, JLPT lists, tooling. ✅
>
> **▶▶ REMAINING (content + optional polish):**
> 5. **DONE — Initiative 2 in-lesson reading-practice boxes** (`design/reading_practice.md`): 286 boxes /
>    235 lessons by SELECTION (i+0 HARD gate), `corpus/readings/`, furigana toggle + reveal translation in the
>    prototype, gate green, no-leak holds. ✅ (task #3)
> 6. **DEFERRED (D-LIC-3, 2026-06-26) — Kanji stroke TAIL = 898 kanji without Kanji Alive.** Measured: **N5
>    80/80, N4 173/173, N3 364/364 = 100% stroke coverage.** The 898 gaps are entirely **N2 (11) + N1 (887)**,
>    OUTSIDE the N5→N4 course scope, and already served by the decomposition fallback. GlyphWiki KAGE→ordered
>    strokes is heavy engineering for advanced kanji beyond the deliverable — revisit only if the course extends
>    to N2/N1. (task #6)
> 8. **TODO — JLPT EXAM-ALIGNMENT (N5/N4/N3): full plan written → [`design/jlpt_alignment_plan.md`] (2026-06-27,
>    research-grounded, NO implementation yet).** Re-tag classifications + re-org course to exam expectations
>    (kanji cum 103/300/650, vocab 800/1500/3700; grammar already OK). It's redistribution by RE-TAGGING (we own
>    2,131 kanji / 7,301 vocab — plenty) + the hard part = course RE-SEQUENCING to keep i+1. Anchor: tanos
>    old-official Level-4/3 lists + a modern N3 list; new `audit_jlpt_coverage.py` is the acceptance gate. See
>    the doc for the cascade, acceptance criteria, and owner decisions. Original diagnosis below kept for context:
>    **— N5 kanji count is 80, JLPT N5 is widely cited as ~100-103.**
>    DIAGNOSIS (not a reconciliation bug): all **4** of our kanji-level sources (davidluzgouveia, kanjiapi=79,
>    anchori, bluskyo=79) AGREE on the strict ~79-80 N5 set — **0** N4 kanji carry even one N5 vote
>    (`reconcile_levels.py`). The ~100-103 figure comes from MORE INCLUSIVE lists we did not ingest (the old
>    JLPT **level-4** list ≈103; Fluent-in-3-Months 100; Kanjidon 103; Hirakan 112; Yomikko ~120). FIX (per
>    §1.5, ≥3-list consensus): add 1-2 inclusive sources (e.g. tanos.co.uk/Jonathan Waller FULL old-level-4
>    list, jonsay, or an explicit 103-list) to `research/datasets/jlpt/` (+ MANIFEST + `dataset_source`),
>    re-run `reconcile_levels.py`, which promotes ~20-23 kanji **N4→N5**. CASCADE to re-do after: kanji export,
>    N5/N4 course re-sequencing (the promoted kanji must be taught earlier), known-set re-gating of lessons +
>    readings, full gate.
>    **TARGET LOCKED (owner, 2026-06-27): match JLPT expectations.** JLPT has NO official post-2010 lists, so
>    anchor to the pre-2010 OFFICIAL lists (which were published): **N5 ≈ old JLPT Level 4 = 103 kanji / ~800
>    vocab**; N4 cumulative ≈ old Level 3 ≈ 300 kanji / ~1,500 vocab. Source the old Level-4/Level-3 official
>    kanji lists (hosted at tanos.co.uk / J. Waller) as the authoritative anchor + keep our 4 community lists as
>    cross-check. Expectation table (cumulative, consensus): N5 ~100-103 kanji / ~800 vocab; N4 ~300 / ~1,500;
>    N3 ~650 / ~3,700; N2 ~1,000 / ~6,000; N1 ~2,000 / ~10,000. CURRENT corpus: kanji N5=80 (short ~23), N5+N4=
>    253 (short ~47 vs 300); vocab N5=706 (≈on-target), N5+N4=1,359 (slightly under 1,500). So the gap is
>    concentrated in KANJI level-tagging; vocab is roughly on-target but re-check N4 while here.
>    **COURSE-COMPLETENESS CHECK PASSED (2026-06-27):** the pre-n5+n5 course teaches 100% of the N5 corpus
>    (kanji 80/80, vocab 700/700, grammar 151/151, 0 untaught) — so finishing N5 = knowing our whole N5 set;
>    the ONLY blocker to "pass the real N5 exam" is the ~23 kanji gap. Those ~23 are already in the corpus
>    (tagged N4), so the fix is **re-tag (N4→N5) + re-sequence the N5 course**, NOT new authoring.
> 9. **POST-ALIGNMENT roadmap → [`design/study_system_roadmap.md`] (2026-06-27, PLAN ONLY).** Do AFTER #8
>    (alignment) is done + checked. Four workstreams: **(A) stroke-order ANIMATION** for kana+kanji — moving
>    guide "ball"/dot tracing each stroke + start-point/number "symbols" (data + static viewers already exist;
>    only the animation is pending; client island, no-leak unaffected). **(B) exercise BANKS + EXAM SIMULATOR**
>    (N5/N4/N3) — per-question-type banks whose templates POINT to corpus IDs; randomized every attempt, ≥2-3
>    variations + rule-based distractors so it teaches (not memorize-the-answers); real JLPT section structure;
>    **IP-HARD: clean-room authored, real papers are © — format reference only**, ingest content only if
>    PD/permissive. **(C) lesson CAPABILITY tagging** — a fixed versioned registry of "language features"
>    (masu/te-form/particles/counters/conditionals/keigo/transitivity…), `lesson_unlocks` gains a `capability`
>    type; feeds D. **(D) DAILY STUDY SYSTEM (research agenda, do later → `design/srs_design.md` before impl):**
>    primary **FSRS** memory track (words+kanji) + secondary **capability-SRS** skill track (short, time-boxed,
>    per-capability right/wrong ease, show-more-the-weak-ones, never-zero) drawing simple exercises from existing
>    banks to keep reading/phrase-forming sharp; daily queue built fast at first login + refreshed after lessons;
>    research FSRS(+SM-2/HLR/Leitner) balance + time-budget; main focus stays battle-tested FSRS. D is app
>    runtime logic → this corpus run only provides the capability registry + typed banks + stable IDs.
> 10. **TODO (owner-flagged 2026-06-27) — investigate why N3 doesn't show on the prototype render.** Cheap
>    static check already done: the DATA is correct (manifest + `prototype/app/data/courses.json` both list all
>    4 courses incl. **n3** = 101 lessons / 15 topics; `course.tsx` maps every course with NO N3-dropping
>    filter; N3 lessons/topics fetched 200 in tests). MOST LIKELY already-cause = N3 **topic titles were blank**
>    (rendered empty tiles → "not showing"), FIXED 2026-06-26 (commit 6ac00ce, create_n3_topics i18n backfill)
>    — so FIRST verify the **deployed (Coolify)** prototype has redeployed since that commit. If it STILL doesn't
>    show: check `FilterableList.tsx` default-tab / `levelOf` behavior (N3 topics may be hidden until the N3
>    segmented tab is selected — `LEVEL_ORDER` includes n3) and the `courses.map` grouping in `course.tsx`
>    (`ts = filtered.filter(t.courseId===c.id)` could render an empty N3 group). Reproduce in `preview` first.
> 11. **TODO (owner-flagged 2026-06-27) — some kanji stroke-draw orders are BROKEN; fix + audit all.**
>    Repro: **間** renders the outer 門 but NOT the inner/bottom **日** ("doesn't render bottom part, acts
>    weird"). Diagnosis so far: `kanji_stroke.steps` for 間 has `total_strokes=12`, `#steps=12` (count OK) but
>    the step path-lengths plateau — steps 8-12 share the SAME length (783), i.e. the last strokes (inner 日)
>    add no distinct geometry. NOTE the step lengths are **non-monotonic** (e.g. 724→507), so `steps` is NOT a
>    simple growing cumulative outline as the `export_strokes.py` comment claims — the real format/semantics must
>    be re-derived first. A naive "consecutive-identical-step" scan flagged 1099/1234 but it **over-flags** (it
>    flags 三, which renders fine), so it is NOT a valid detector. ACTIONS: (1) re-derive what `steps` actually
>    holds (per-stroke path vs cumulative) by reading `scripts/ingest/kanjialive_strokes.py` (ingest) +
>    `prototype/app/ui/KanjiStrokes.tsx` (renderer); (2) root-cause 間 (likely the ingest dropping/duplicating
>    inner-component stroke geometry, or the renderer mis-compositing); (3) build a RENDER-ACCURATE integrity
>    check (e.g. each stroke must contribute new geometry / final frame must equal the glyph) and run it over all
>    **1,234** kanji to find every affected one; (4) fix the ingest and/or renderer, re-export `corpus/strokes/`,
>    re-sync, rebuild, verify a sample (incl. 間) in preview. Source = Kanji Alive (CC BY 4.0); a fix may need
>    re-ingesting their per-stroke SVGs more faithfully.
> 7. **RESOLVED / DEFERRED (D-LIC-3):** (a) **pitch-accent (kanjium)** — mora index is a FACT → **keep + credit**
>    (no re-source; no permissive bulk source exists). ✅ (b) fully-independent **GlyphWiki** component
>    decomposition — DEFERRED (current `kanji_component` is uncopyrightable fact, EDRDG-credited; marginal
>    benefit). See `design/license_audit.md` D-LIC-3.

> **2026-06-25 (d) — QA PHASE 3 + SANITY CHECK: de-scaffolded learner-facing prose; closed the 6
> never-ground-truth-audited field-classes.** Sanity check of (c) was clean (0 empty / 0 mojibake; fixes
> persisted; gate green) BUT found a real gap: 6 pt-BR field-classes had only been accent/tells-scanned.
> Auditing them surfaced a **systematic generation artifact** — internal scaffolding leaked into learner-facing
> prose (in BOTH pt + en): grammar-point codes `gp-NN`, the meta words `candidato`/`candidate`/`target`,
> `tari-tari`/`cand-…` slugs, bare 5-6 digit sentence-IDs (`em relação à 187243`), `posição N`, `(target jec)`.
> (`lesson.body` `gram:gp-NN` are LEGIT `ref=` attributes — left alone; vocab gloss `candidato`=候補 is real pt.)
> - **Audited:** `sentence.structure_explanation` (102 flagged/12 major → applied), `family.label` (2 minor),
>   `family.governing_rule` (0 — clean). Plus a deterministic corruption sweep.
> - **Two-tier de-scaffold (new tooling):** `descaffold_strip.py` deterministically removed parenthetical
>   metadata + pt `target`→`alvo` (**1,855 field-values**, leaving natural prose); `descaffold_workflow.js`
>   grounded-rewrote the **330 woven residuals** (pt+en) with a locale-aware post-guard (en keeps legit
>   "target"); 3 `posição N` particle refs + 1 ai-tell fixed by hand.
> - **Corruption class fixed** (romaji-bleed): `ほod→ほど`, `のni→のに`, `つまri→つまり`, `こso→こそ`, `こto→こと`,
>   `ばakari→ばかり`, `用いada→usada`, doubled `「よよ」→「よ」`, + 8 exercise-prose sentence-ID leaks (lesson JSON).
> - **End state (verified):** leak class **0**, latin-fused-kana **0**, doubled-kana **0**, em-dash **0**,
>   ai-tells **0**. Counts unchanged (kanji 2131 / vocab 7301 / grammar 496 / sentences 5565 / lessons 314).
>   Gate GREEN (8/8 hard); no-leak holds (client bundle: 0 corpus sentinels). Exported corpus+course, synced
>   + rebuilt prototype. **Checked the gate result BEFORE committing this time.**
> - New scripts: `descaffold_sample/strip/workflow/apply`; `gt_audit_*` extended with the 6 field-classes.
> - **Remaining audits DONE (owner: "particles + conjugations only"):** full SEMANTIC pt↔en audit of
>   `particle.explanation` (65 batches → 145 fixed, 17 major incl. fabricated term 沿音便→"mudança eufônica",
>   つる "grapevine"≠"ramo de uva", context-ambiguous accents é/força/faça) and `token.conjugation_note`
>   (56 batches → 98 rows, 9 major incl. 鳴らす "rasaru"→"narasu", non-existent ございる→ござる, 一行おき "every
>   other line" inversion, gemination mislabeled "sonorização", garbled "decshite"→"kesshite", duplicated-verb
>   artifacts ありある→ある, untranslated "polite", raíz→raiz typos). Plus a deterministic raíz/cópua typo sweep
>   (11) + 1 em-dash + 29 accents. Gate GREEN; detect_ai_tells 0; no-leak holds; both repos pushed.
> - **STILL OPEN (deliberately skipped per owner):** `token.role` (65 batches) — grammatical role labels,
>   mostly controlled vocabulary, lowest yield; already leak/accent/corruption-CLEAN. Re-run `gt_audit_*
>   token.role` anytime (CONFIG has it).

> **2026-06-25 (c) — TRANSLATION-QA EXECUTED (translation_qa.md): every corpus translation field-class
> audited pt↔en + fixed.** Adversarial in-context audits (jp + pt + trusted en) across the whole corpus:
> - **Sentence layer:** all 5,565 × {natural, literal} (11,130 judgments) → 187 flagged → 199 fixes.
> - **Field-classes (ground-truth, dedup by distinct pt↔en):** grammar label/explanation/formation/nuance
>   (26), kanji.meanings (14 majors; sense-completeness minors left for human review), particle.function
>   (40 incl 2 majors), token.gloss (252 rows), vocab.gloss (290 rows). Rate-limited batches were resumed →
>   all classes COMPLETE.
> - **Biggest deterministic win:** `accent_sweep_localized.py` restored **~1,150 stripped diacritics**
>   corpus-wide (você/ação/partícula/relação/tópico…) — the dominant error CLASS, fixed in one pass.
> - Net **~1,900 corrections**. Error rates ~0.2–0.25% major per class → corpus is genuinely solid.
> - New QA tooling (committed): `detect_ai_tells.py` (hardened: literal-mirror + artifact tells),
>   `nat_audit_*`, `full_audit_*`, `gt_audit_*` (+ apply), `accent_sweep_localized.py`. Gate GREEN throughout;
>   no-leak holds; everything pushed to both repos.
> - **Residue for human review (curation, not errors):** kanji/vocab "missing-sense" minors (deliberately
>   concise card subsets); ~39 context-ambiguous pais/esta (parents/this vs país/está). Everything carries
>   `needs_review` for the teacher pass (§0.1 "review confirms, not corrects").
> - **Lesson learned (for next runs):** check the validate gate result BEFORE committing (grep in an && chain
>   masks the exit code); two transient gate fails (lesson-body sweep, 1 em-dash) were caught + fixed.

> **▶▶ TWO PLANNED initiatives — ✅ BOTH NOW EXECUTED (kept for provenance):**
> _(1) Translation-QA + license audit + §9 guardrails — DONE (2026-06-25/26, see the dated entries above).
> (2) In-lesson reading-practice boxes — DONE (2026-06-26, `design/reading_practice.md`; 286 boxes/235 lessons)._
> 1. **Translation accuracy + naturalness + FINAL validation** → [`design/translation_qa.md`]. Minimize AI
>    translation errors everywhere (JP phrases, kanji/particle/conjugation explanations, JP→pt-BR) + a final
>    gate that catches over-literal renderings ("Quanto a mim, sou estudante" vs natural "Eu sou estudante")
>    and AI-like prose; daily-life register, no slang. **Start order in §7** (cheap wins first: extend
>    `detect_ai_tells` with anti-literalism patterns + full pt↔EN cross-check). Includes a **license audit —
>    owner ruling needed on the CC BY-SA backbone (JMdict/KANJIDIC/KanjiVG); enforce permissive-only (no SA,
>    no copyright) on all NEW material**. **§9 = guardrails for GENERATED content** (deterministic JP battery:
>    Sudachi parse + JMdict/KANJIDIC existence + valid readings + known-set + corpus-attestation naturalness;
>    cross-model adversarial multi-vote; round-trip back-translation; trust score + quarantine + human-review
>    floor + golden regression set) so even last-resort generation is as trustworthy as possible.
>    **Guiding aim (§0.1): "review confirms, not corrects"** — target 100% correct BEFORE review; raise the
>    bar (regenerate/re-select instead of deferring to the reviewer), attach evidence to each item, and treat
>    every review-found correction as a pipeline bug fixed upstream (feedback loop); track correction-rate.
> 2. **In-lesson reading-practice boxes** → [`design/reading_practice.md`]. Optional `<reading>` boxes,
>    pre-N5 none → N5 light → N4 more → N3 more (ramping mid-N3); hard-gated to each lesson's known-set;
>    **grounded in real CC-licensed text (Tatoeba CC BY/CC0 + JEC CC BY) with trusted EN**, generation last
>    resort. Can reuse the QA tooling from (1).
> Complementary permissive sources re-checked (no SA): Tatoeba (CC BY/CC0) + JEC stay primary; Aozora (PD) +
> Wikidata Lexemes (CC0) optional; KFTT/Wikipedia/Tanaka (CC BY-SA) now EXCLUDED by the no-SA rule.

> **2026-06-25 (b) — corpus fully BILINGUAL (pt-BR + en) + N2/N1 banks given pt-BR.** Owner: "N2/N1 should
> also have pt-BR; the rest also have English." Built a reusable distinct-string translation pipeline
> (`tr_extract.py` → `tr_workflow.js` → `tr_load.py`, + `tr_form_meanings.py`):
> - **N2/N1 pt-BR:** generated pt-BR `meanings`/`gloss` for 1,514 kanji + 7,955 vocab senses (EN→pt-BR).
> - **English for the rest (corpus layer):** generated `en` for every derived pt-BR field — grammar
>   (label/explanation/formation/nuance/form_meanings) + families + sentences (translation/literal/
>   structure_explanation) + tokens (gloss/role/conjugation_note) + particles (function/explanation).
>   Sentences missing the Tatoeba `en` got a pt→en translation too. Coverage: sentence-level 5,565/5,565,
>   tokens/particles 100% of non-empty. ~107k `en` localized_text rows.
> - Exporters (`export_corpus.py`) now emit both locales from `localized_text`; corpus JSON is
>   `{"pt-BR":…,"en":…}` throughout. **Course/topic/lesson stay pt-BR-only** as specified. Re-synced; build
>   clean; **no-leak holds** (client 441KB unchanged — en doubling is server-side only). Spec marked DONE in
>   `design/i18n.md` + `design/product_roadmap.md`.

> **2026-06-25 — N3 completed to parity + N2/N1 bank-only extension + English-preservation plan.**
> - **N3 Tranche 3:** authored 47 vocab-expansion lessons → N3 now **100% vocab (1,596), 100% kanji (364),
>   100% grammar (132) placed**, **101 lessons** (was 54), **607-sentence dissected bank** wired into lessons.
>   Re-authored 12 accent-stripped lessons; added durable **numeric-id ref resolution** (homographs) to
>   `load_lessons.py` + `audit_coverage.py`, with `export_course.py` dereffing id→headword for the display
>   layer. Course = **314 lessons**. validate_lessons 0 err · coverage 0 FAIL/0 WARN · hygiene 0 FAIL · no-leak OK.
> - **N2/N1 banks (kanji + vocab ONLY; no sentences/grammar/lessons/pedagogy)** — owner directive: minimum for
>   FSRS, modern/used only. `scripts/ingest/ingest_n2_n1.py` (additive, **Jōyō grade 1–8 gate** + 4-lineage
>   consensus; archaic vocab dropped) → **+1,514 kanji (380 N2, 1,134 N1), +4,446 vocab (1,768 N2, 2,678 N1)**.
>   Kanji total ≈ full Jōyō (2,131). Layer-A **English** meanings populated (pt-BR deferred). Exported as
>   **bank-only levels** (`export_corpus.py` `BANK_LEVELS`); prototype browse shows N2/N1 filters (verified).
>   Methodology: [`design/n2_n1_bank.md`]; sources in `research/datasets/jlpt/MANIFEST.md`.
> - **PLAN (not built):** preserve English alongside the original for the **corpus layer** (kanji/vocab/grammar/
>   sentences), NOT course/topic/lesson — Layer-A English already in the `en` key; Layer-B/C `en` parallel is a
>   future pass. Spec: [`design/i18n.md`] "Roadmap — preserve English"; backlog in `design/product_roadmap.md`.
> - **NEXT options (not started):** N3 vocab-anchored sentence bank toward N4 volume (~+4k); N2/N1 pt-BR glosses;
>   English Layer-B parallel pass.

> **2026-06-17 (round 5) — validator completeness: closed the two real gaps.** Asked "are all required validators
> there?" — they weren't. Fixed:
> - **No single gate** → `scripts/validate/validate_all.py` runs the whole suite (8 HARD validators + 2 advisory)
>   and exits non-zero if any hard check fails. **One command = the build gate.**
> - **Standing P8 hygiene rules had no committed guard** (emoji/backslash/em-dash/accent-stripping/empty-tags/
>   run-together/meta-leak/non-ASCII-identifiers were only one-off scans) → `scripts/validate/audit_lesson_hygiene.py`
>   now enforces them (key-aware: learner text only, not identifiers). 0 FAIL.
> - **Ran 4 validators I'd been ignoring:** `graph_queries` (§1.7 design tests — all 4 PASS), `completeness_audit`
>   (info markers only, no hard fail), `detect_ai_tells` (flagged 15 → fixed the 2 real "vale notar/lembrar"
>   fillers; the other 13 are false positives — they explain the "não só A, mas também B" grammar pattern),
>   `r3_coverage_probe` (one-off dataset probe, not a gate).
> **GATE GREEN:** validate_lessons · integrity_audit · audit_coverage · audit_manifest · audit_export_refs ·
> audit_lesson_hygiene · graph_queries · validate.py → all HARD PASS (run `validate_all.py`).
>
> **2026-06-17 (round 4) — ALPHA-READINESS audit: caught + fixed EXPORT-layer gaps the DB validators missed.**
> Pushed back on "all green" and audited the EXPORT (not just the DB). Found + fixed real Alpha-blockers:
> - **Phantom kanji refs:** 米/港/市 were taught + referenced in lesson bodies but, being level-NULL, were
>   dropped from `corpus/kanji/n4.json` → dangling refs in the export. Gave them an honest **low-confidence
>   level=n4 + level_sources** ("author-added; outside consensus lists", §1.5-compliant) so they export, with
>   pt meanings in `localized_text`.
> - **Leaf schema non-conformance:** `export_course.py` emitted lesson leaves with `slug` + plain-string
>   title/description/objectives, but the documented schema (courseware_architecture §2.4) + all other tiers use
>   `id` + locale-objects `{"pt-BR":…}`. Fixed the exporter (leaf + exercises now `id` + locale-objects).
> - **New validator `scripts/validate/audit_export_refs.py`** (closes the gap): checks every lesson leaf is
>   schema-conformant AND every unlock + inline body ref (`<kanji|vocab|grammar|sentence ref>`) resolves against
>   the EXPORTED corpus. Now **0 FAIL**.
> - **Doc drift fixed** (from the eval): kanji counts 100→80 (N5), 245→250 (N5+N4); grammar 363→364; families
>   58→396; manifest `enums_ref` path; **kana SRS-bootstrap-words marked DEFERRED/not-implemented** (0 vocab
>   unlocks in kana lessons — docs had overclaimed it).
> **Full 6-validator suite GREEN:** validate_lessons 213/213 · integrity_audit 0/0 · coverage 0/0 · manifest
> 0 FAIL · **audit_export_refs 0 FAIL** · validate.py 4958 0 errors.
>
> **2026-06-17 (round 3) — project-evaluation fixes (corpus content).** 7-agent eval (sentences/grammar/vocab/
> kanji + docs + schema). Fixed: gp-60 pattern `～ら`→`～たら`; stripped KANJIDIC radical-name leak from 6 kanji
> meanings (+ durable filter in `prepare_meanings.py`); 休 "dormir"→descanso/folga; deleted 1 unused broken AI
> sentence + fixed 1 pt. Caveats from before fully cleared (kanji placement via loader backfill; pl-08 痔 removed;
> 13 real cards added to no-card lessons).
>
> **2026-06-17 (round 2) — validation re-review fixes + a spacing regression caught & repaired.** Ran a fresh
> full validation (18 reviewers): dist 132×5 / 47×4 / 7×3 / 6×2. Fixed every flag: accent-stripped
> description/objectives/exercise fields across the corpus (`fix_accents_lessons.py`, 454+10 words, now
> KEY-AWARE so it never touches slug/topic/ref); meta-leaked descriptions (passiva-02, conectando-02, verbos-05/06,
> hiragana-06, adjetivos-05); editing scars / pt-in-`<jp>` / reading mismatches (potencial-01, oracoes-relativas-05,
> katakana-09, particulas-lugar-07, suposicao-04/05/07). **Caught my own regression:** the emoji stripper had
> trimmed single spaces at `<text>` boundaries, running ~10.6k words together — fixed the stripper and re-inserted
> the spaces (`fix_boundary_spaces.py`). **Caught a second self-inflicted bug pre-load:** the accent fixer had
> accented IDENTIFIERS (numeros→números, suposicao→suposição, experiencia→experiência, particulas→partículas,
> saudacoes→saudações) in slug/topic/exercise-slugs/body-refs of 37 files + spawned a duplicate accented filename;
> reverse-fixed all (`fix_identifier_accents.py`) and reconciled filenames. Added 8 more real cards via
> `enrich_examples_surface.py` (surface-match fallback, flagged lower-confidence).
> **Final state ALL GREEN:** validate_lessons 213/213 0/0 · integrity_audit 0/0 · coverage 0 FAIL/1 cosmetic WARN ·
> manifest 0 FAIL · validate.py 0 errors · scans: 0 emoji / 0 backslash / 0 accent-stripped / 0 run-together /
> 0 bad-identifier. New scripts: fix_boundary_spaces, fix_identifier_accents, fix_accents_lessons,
> enrich_examples_surface. **Lesson learned (recorded in quality_rubric §P8): mechanical text fixers must be
> key-aware — never rewrite identifier fields (slug/topic/ref) or trim word-separating spaces at tag boundaries.**
>
> **2026-06-17 — P8 QUALITY PASS COMPLETE (pushed) + standing rules recorded.** Full per-lesson quality review
> (18 reviewers over 213 lessons) + corpus audits → fixed everything found and encoded the rules in
> [`design/quality_rubric.md`](design/quality_rubric.md) §P8 + [`research/local-course-insights/course_volume_comparison.md`](research/local-course-insights/course_volume_comparison.md).
> - **Fixed:** 3,072 over-escaped `\"` artifacts across 65 lessons (`fix_escape_artifacts.py`); 7 accent-stripped
>   lessons restored; 3 lessons where a polish agent returned meta-text as body (restored from git + re-polished);
>   ~10 editing-scar / corrupted-heading / wrong-gloss / garbled-token / confusing-example fixes; 6 meta-leaked
>   `description` fields rewritten. **Emoji removed from ALL learner text** (347 fields; `strip_emoji_lessons.py`) —
>   cues now come from `<note type>` blocks only (owner directive).
> - **Bank usage:** diagnosed (linkage-bound: only ~2,007 of 4,959 sentences are grammar-linked; ~2,952 unlinked).
>   `enrich_examples.py` added 63 REAL (Tatoeba-first) example cards to 51 grammar lessons → 511 featured (~2.4/lesson,
>   ~68% real). Standing rule: prefer real over AI in examples/exercises.
> - **Kanji coverage VERIFIED correct + balanced:** all 80 N5 kanji in the N5 course, all 170 N4 kanji in N4, 0
>   level/module mismatches, max 6/lesson. **Exercises** ~5/lesson (1,053 total) — good, not heavy.
> - **All green:** validate_lessons 213/213 0/0 · integrity_audit 0/0 · audit_coverage 0 FAIL/1 cosmetic WARN ·
>   audit_manifest 0 FAIL · validate.py 4959 0 errors · 0 emoji · 0 backslash · 0 meta-leak · 0 accent-stripped.
> - New durable scripts: `fix_escape_artifacts.py`, `strip_emoji_lessons.py`, `enrich_examples.py`,
>   `audit_coverage.py`, `audit_manifest.py`. **A fresh validation workflow was launched after these changes.**
>
> **▶ NEXT (P8 enrichment backlog, optional): ** (a) tagger pass to link more bank sentences to N4 grammar +
> surface vocab-example sentences (raise bank usage past linkage limit); (b) deep-dive depth on ~12 flagship
> topics; (c) durably place kanji 米/港/市; (d) audio (product roadmap, TTS over the bank). See quality_rubric §P8.
>
> **2026-06-16 — 🎉 FULL COURSE AUTHORED: pré-N5 → N5 → N4 COMPLETE (213 lessons, 35 topics).**
> pré-N5 41 · N5 81 · N4 91. All content topics (07–18 N5, 20–34 N4) + te-form + both revisão topics done.
> N4 authored in 5 batches via `author-n5-batch` (LEVEL='n4'); te-form via `author-teform-rest`; revisão
> (n5-19 + n4-35, 3 lessons each, 0 item unlocks) via `author-revisao` — the final lesson of each level unlocks
> `feat:jlpt-sim-n5` / `feat:jlpt-sim-n4`. **All green: validate_lessons 213/213 0/0 · integrity_audit 0 FAIL/0
> WARN · validate.py 4959 sentences 0 errors.** The self-healing pipeline (normalize_lesson_refs → dedupe_unlocks
> → repair_lesson_bodies → clean_emdash_lessons) made batch authoring near-hands-free: the repairer alone
> auto-fixed 100+ tag issues across N4 (stray closes, inline-nesting, bare text in heading/check, self-closing
> inline in text). One transient author failure (or-05) re-authored standalone.
>
> **2026-06-16 (cont.) — P7 STRUCTURAL AUDIT DONE (green).** Built two read-only P7 auditors:
> `scripts/validate/audit_coverage.py` (placed-vs-unlocked per kind + introduce-once over the whole graph) and
> `scripts/validate/audit_manifest.py` (4-tier manifest cross-links + counts + leaf body/cumulative + sentence_ref
> resolution). Fixed 8 coverage gaps (`patch_coverage_gaps.py`): now **vocab/kanji/grammar 0 gap, 0 dup**.
> audit_manifest **0 FAIL** (35 topics / 213 lessons, all paths + counts consistent). Remaining: 1 cosmetic WARN
> — kanji 市/港/米 are taught by lessons but have `introducing_topic_id` NULL (P4 never placed them; lesson_unlocks
> is the source of truth, so they ARE covered). FULL validator suite green: validate_lessons 213/213 0/0 ·
> integrity_audit 0/0 · audit_coverage 0 FAIL · audit_manifest 0 FAIL · validate.py 4959 sentences 0 errors.
>
> **▶ NEXT (optional polish): ** (a) durably place kanji 市/港/米 in P4 placement data to clear the last WARN;
> (b) humanizer/prose spot-check pass over a sample of lessons; (c) L-phase concept-level coverage comparison
> (confirm ours ⊇ the local course, naming nothing); (d) bootstrap-words pass (re-place a few N5 vocab into
> pré-N5 kana lessons for early SRS). **NOTE: pushes still pending — all work since e914575 is committed locally
> only; awaiting an explicit "push".**
>
> _Earlier 2026-06-16 progress (chronological):_
>
> **N5 topics 09–14 AUTHORED (42 lessons) + pipeline made self-healing.** Built a multi-topic
> `author-n5-batch` workflow (one planner→authors per topic, several topics per run) and authored, validated +
> committed: **numeros-tempo (9), verbos (6), particulas-lugar (8), passado (5), adjetivos (8), comparacoes (6)**.
> **N5 = 53 lessons (topics 07–14 + te-form pilot); corpus = 95 lessons total.** validate_lessons 95/95 0/0 ·
> integrity_audit 0 FAIL/0 WARN · validate.py 4959 sentences 0 errors.
> - **New durable post-author pipeline steps** (run in this order after `write_authored_lessons.py`, before
>   `load_lessons.py`): `normalize_lesson_refs.py` (rewrites `vocab:<kana>` → canonical `vocab:<headword>` via
>   exact-kana→unique-headword; reports ambiguous/unresolved) · `dedupe_unlocks.py` (introduce-once: drops a
>   duplicate unlock from the LATER lesson — safe because cumulative_known_set is cumulative; also collapses
>   intra-lesson dups) · `repair_lesson_bodies.py` (conservative stack-based tag repair: fixes the recurring
>   typo `</jp>`-for-`</text>`, drops truly-stray closes, closes missing end tags — ONE such typo used to
>   cascade into dozens of "<text> may not contain <text>" errors) · `clean_emdash_lessons.py` (strips banned
>   em dash U+2014 from ALL string fields, not just body; chōon ー U+30FC untouched).
> - **Batch-workflow caveats encoded:** author agents (a) sometimes WRITE files directly to
>   `research/derived/lessons/` (they have Write + infer the path) → prompt now says "do NOT write any file;
>   return structured output only", and I clear a topic's files before writing its canonical `.output`; (b)
>   occasionally return `body:"placeholder"` → prompt now forbids stubs; (c) still occasionally typo tags →
>   `repair_lesson_bodies.py` fixes mechanically; structural re-author is the fallback.
> - **Full per-batch recipe:** edit `author-n5-batch` `TAILS` → run via scriptPath → `write_authored_lessons`
>   → `normalize_lesson_refs` → `dedupe_unlocks` → `repair_lesson_bodies` → `clean_emdash_lessons` →
>   `load_lessons` → `validate_lessons` (re-author any lesson with residual tag-nesting/placeholder) →
>   `export_course` → commit.
>
> **2026-06-16 (cont.) — N5 topics 16–18 AUTHORED (17 lessons): convites (6), rotina (?), conectando (?).**
> Processed via the full recipe; repairer enhanced to also split balanced inline-nesting
> (`<text>A<emphasis>B</emphasis>C</text>` → siblings) + drop empty `<text></text>`. **N5 content topics 07–18
> COMPLETE; corpus = 112 lessons.** validate_lessons 112/112 0/0 · integrity_audit 0/0.
>
> **2026-06-16 (cont.) — topic-15 te-form COMPLETE (pilot 01 + lessons 02–08 = 8).** `author-teform-rest`
> workflow excluded the pilot's items (gram:te-form/te-kudasai, vocab:乗る) and authored 02–08 (て-chaining,
> ています/てある, orações relativas, permissão/proibição, obrigação + contractions). repairer further enhanced
> to split self-closing inline (`<vocab/>`/`<grammar/>`/`<kanji/>`) out of `<text>`. **N5 content COMPLETE
> (topics 07–18 + te-form); corpus = 119 lessons.** All N4 content topics (20–34) PREPPED. validate 119/119 0/0.
>
> **2026-06-16 (cont.) — N4 topics 20–25 AUTHORED (38 lessons):** forma-simples (7), oracoes-relativas (7),
> condicionais (8), potencial (4), volitivo (7), transitividade (5). Corpus = 157 lessons. validate 157/157 0/0 ·
> integrity_audit 0/0. **repair_lesson_bodies.py further enhanced** to (a) split self-closing inline `<vocab/>`
> out of `<text>` and (b) WRAP bare text in `<text>` when it sits in a non-inline context (`<heading>X</heading>`,
> `<check>X</check>`) — the agents frequently forget the wrapper at N4 scale; the repairer now auto-fixes it, so
> almost no manual re-authoring is needed. One transient author failure (socket close) left an empty stub file on
> disk → deleted + re-authored standalone (`author-or-05`); recipe note: a failed author may still leave a stub
> file, so delete + re-author rather than trust on-disk files for failures.
>
> **▶ NEXT = N4 topics 26–34** (batch 3 = dar-receber, experiencia, obrigacao RUNNING as wf wy2qbuzl4; then
> aspecto/suposicao/passiva; then causativa/keigo/conectores), **then revisão lessons (n5-19 + n4-35, 0 placed
> items = consolidation only), bootstrap-words pass, P7.**
>
> **2026-06-16 — P6b FOUNDATION built + plans standardized (consistency-reviewed). Authoring unblocked.**
> Ran a 3-agent adversarial consistency review of the plans+code; it confirmed the design but found the
> needs/unlocks/srs model was documented-but-unimplemented + several doc inconsistencies. **Fixed all, then made
> the structure REAL end-to-end:**
> - **Standardization (docs):** `need_type` = unlock_type − {srs-deck} + lesson (enum+prose agree); **dropped
>   `srs-card`** (cards are always DERIVED from item unlocks); reconciled the two ref-namespace surfaces
>   (body chips vs needs/unlocks metadata); **topic numbering = GLOBAL** is canonical (course_outline TNN are
>   within-module labels w/ mapping); chunk caps are **per-lesson**; kana **11 base families** (WA + N separate,
>   matches registry) + explicit family→lesson grouping table; softened the feature "1:1" claim.
> - **Implemented (code):** migration `006_courseware.sql` (`lesson_unlocks`, `lesson_needs`); `enums.py`
>   (loads `unlock_enums.json`, the single source of truth) imported by loader+validator+exporter; enriched
>   `unlock_enums.json` (deck_registry + card-types + conjugation_form). `load_lessons.py` persists
>   needs/unlocks/feature_unlocks/description (back-compat w/ old `introduces`). `validate_lessons.py` enforces
>   enum membership + ref resolution + **needs-linearity** (every need unlocked by a strictly-earlier lesson) +
>   introduce-once over unlocks. `export_course.py` emits the **4-tier manifest** (manifest.json → course.json →
>   topic.json → lesson leaf) with needs/unlocks/feature_unlocks/**derived srs.introduces_cards**/
>   cumulative_known_set/description.
> - **Pilot re-authored** to the new shape (the reference authors copy). load 0 warn · validate_lessons 0/0 ·
>   validate.py 0 errors · integrity_audit 0 FAIL/0 WARN.
>
> **KANA STRAND DONE (2026-06-16):** full hiragana (15 lessons, `les:pre-n5-hiragana-01..15`) + katakana
> (15 lessons, `les:pre-n5-katakana-01..15`) authored via `author-{hiragana,katakana}-lessons` workflows →
> `write_authored_lessons.py` → load → validate (31/31 lessons 0/0) → export. All 28 hiragana + 29 katakana
> families have an introducing lesson (introduce-once held); lesson 1 unlocks `feat:srs-reviews`. Rich pt-BR
> bodies: per-kana mnemonics, 💡/⚠ pt pitfalls (し=shi, つ, ふ, ら-tap, vowel-closing; katakana シ/ツ/ソ/ン
> look-alikes, ー long mark, loanword hook), recognition/matching/production exercises. pré-N5 = 30 lessons.
> (Bootstrap-word SRS unlocks deferred — need introduce-once coordination with N5 vocab placement.)
>
> **MÉTODO/FONOLOGIA DONE (2026-06-16):** orientação (2) + sons (3) + pronúncia (3) = 8 concept lessons
> authored (no item unlocks; validator updated so production is required only for item-teaching lessons).
> **pré-N5 MÓDULO COMPLETO: 41 lessons** (orientação 2 + sons 3 + hiragana 15 + katakana 15 + pronúncia 3 +
> saudações 3). saudações introduces the 24 placed survival vocab (kana display, unlocked by headword; 2 lessons
> re-run after transient API 500s via resume-from-runId). validate_lessons 42/42 0/0 (incl. te-form pilot).
> Note for future authoring: include the "<text> is a leaf — never nest <text>/inline tags inside <text>" rule
> in the workflow prompts (one lesson failed it + was re-authored).
>
> **N5 PATTERN ESTABLISHED + topic-07 DONE (2026-06-16):** built the N5 plan→author pipeline —
> `prep_topic_authoring.py <topic>` dumps placed grammar/vocab/kanji + candidate dissected sentences →
> `author-n5-topic` workflow (1 planner splits the topic into lessons; author agents fan out, one per lesson,
> referencing sentences by ID) → `write_authored_lessons.py` (handles {plan,lessons}) → load → validate →
> export. **topic-07 (desu-wa) = 5 lessons** (は/です/だ · これそれあれ · か/じゃない · の/も · お/ご),
> each unlocking its grammar+vocab, featuring real Tatoeba sentences, with cloze/particle/production exercises.
> (1 lesson re-run after a transient 500 via resume-from-runId.)
>
> **topic-08 (perguntas) DONE = 6 lessons** (ここ/そこ/あそこ/どこ · この/その/あの · どれ/どの · 誰/どうして ·
> どんな/どうやって · なにか/か〜か). N5 = 11 lessons (+ te-form pilot = 12). validate_lessons 53/53 0/0 ·
> integrity_audit 0/0. **Hard-won workflow caveats (encoded):** (a) the Workflow `args` global does NOT reach
> this runtime — set TOPIC by HAND in the author-n5-topic script per topic (don't pass args). (b) author-n5-topic
> RULES now carry an explicit WRONG/RIGHT no-nested-`<text>` example (agents occasionally violate it → re-author
> the offenders). (c) `load_lessons.py` now PRUNES DB lessons whose authoring file was removed (files are
> authoritative) — fixed a stale-lesson introduce-once bug. (d) `prep_topic_authoring.py` + author-n5-topic now
> handle KANJI (planner assigns ≤6/lesson; lessons unlock kanji:CHAR). All N5 content topics already prepped to
> `research/derived/topic_authoring/`.
>
> **▶ NEXT = N5 topics 09–18 (then 19 revisão), then N4.** Per topic (atomic unit): edit author-n5-topic
> `TOPIC` const → run via scriptPath → write → load → validate → export → commit. (topic-15 te-form already has
> the pilot lesson — author the REMAINING te-form items as lessons 02+, keeping the pilot as lesson 01.) Then N4
> (topic-20→35), bootstrap-words pass, P7. Per topic (atomic unit, workflow fan-out):
> split the topic's PLACED grammar/vocab/kanji into lessons (≤5 grammar / 15–25 vocab / ≤10 kanji per lesson),
> author rich bodies referencing the **dissected sentence bank by ID** (`sent:…`) for examples + typed exercises
> (cloze/particle_choice/sentence_build + production) + `<checklist>`. unlocks = the topic's placed items
> (namespaced refs); needs = prior-lesson items (linearity). Then the bootstrap-words pass, then P7. Each lesson: rich body
> (les-n5-te-form-01 = reference) + needs/unlocks (namespaced refs, unlock_enums.json) + typed exercises +
> `<checklist>`. Recipe per topic: author JSON → `load_lessons` → `validate_lessons` → `export_course` → commit.
> Then P7 (coverage + unlock-graph linearity + manifest cross-links). NOTE: a from-scratch rebuild must run
> `init_db` (migrations incl. 006) + `build_kana` before `load_lessons`.
>
> ---
>
> **2026-06-16 — COURSEWARE ARCHITECTURE planned (owner directives). Plans updated; ready for P6b build.**
> Designed the courseware data model + unlock/SRS/kana plans before bulk lesson authoring:
> - **`design/courseware_architecture.md`** (master "explains everything"): layered manifest **entry
>   (`manifest.json`) → course (`<level>/course.json`) → topic (`topic.json` w/ lesson stubs) → lesson
>   (`lesson-NN.json` full)**; the app builds the tree + unlock DAG from the light "required layer", lazy-loads
>   bodies. Per-lesson **`needs`/`unlocks`** + **FSRS deck/card** model + **lesson length** targets (300–700 words
>   reading + 4–8 examples + 4–8 exercises, 8–15 min; split if bigger).
> - **`design/unlock_enums.json`** — closed global taxonomy: `unlock_type`/`need_type` (kana-family, vocab, kanji,
>   grammar, conjugation-form, phrase, kanji-family, feature, srs-deck), `feature` (srs-reviews, conjugation-drill,
>   particle-drill, handwriting, jlpt-sim, visual-novel…), `card_type`, `deck`, `ref_namespace`. Validator/loader
>   import it.
> - **`design/kana.md`** — Hiragana/Katakana = topics; **one gojūon FAMILY per lesson** ("Família do A/KA/SA…"
>   + vozeamento GA/ZA/DA/BA/PA + yōon + っ/long); needs a NEW **kana registry** (`build_kana.py` →
>   `corpus/kana/*.json`); **SRS-bootstrap words** (kana-only, no grammar) are the SOLE linearity exception.
> - **FSRS:** decks by skill type; completing a lesson enrolls its items' cards (deck created on first card).
>   Build the registries/`srs.introduces_cards` now so authoring fills them.
> - Updated: `lesson_schema.md` (record metadata), `course_outline.md` (kana families + linearity), `product_roadmap.md` (§A rows + §H).
> - **Deep research RECOVERED (2026-06-16):** the workflow was killed mid-Fetch (1 stuck WebFetch), but 33/34
>   agents had completed — recovered **116 claims from 35 sources** from the journal
>   (`research/derived/deep_research_recovered.json`) and synthesized `research/deep-research-courseware.md`.
>   **Verdict: the research OVERWHELMINGLY CONFIRMS the plan** (4-tier manifest, closed needs/unlocks enum,
>   DAG-over-linear, per-skill FSRS decks w/ unlock-on-completion, family-per-lesson kana, worked-example ladder
>   each independently sourced). Applied 6 evidence-backed refinements: lesson-length reframed as a heuristic
>   (microlearning has NO consensus; ours runs longer for worked-example pedagogy); FSRS defaults (retention 0.90,
>   band 0.80–0.95, per-deck-preset) + block-then-interleave; worked→faded→free + expertise-reversal; stroke-order
>   static-over-animation caution; LRMI/Common-Cartridge provenance for needs/unlocks. (Verify phase didn't run →
>   confidences are conservative source-quality estimates; 1 source lost.)
>
> **▶ NEXT = P6b build, in order:** (1) `unlock_enums.json` loader/validator + widen `lesson_introduces`→`unlocks`
> + `lesson_needs` + `feature`/`deck`/`card` registries (DB migration); **(2) ✅ DONE — `build_kana.py` →
> kana registry: 211 kana / 57 families (28 hiragana + 29 katakana) in `corpus/kana/` + DB (`kana`,
> `kana_family`); `kana-family` refs = `kana:<script>-<row>`;** (3) author pré-N5 kana family lessons
> (+bootstrap words) → load → validate → export → commit per topic; (4) topic-by-topic (N5→N4) authoring;
> (5) `export_course.py` emits the 4 manifest tiers; (6) P7 audit (coverage, unlock-graph linearity, manifest
> cross-links). Reference lesson: `les-n5-te-form-01`.
>
> ---
>
> **2026-06-15 — P6a DONE: grammar placement re-sequenced (dependency-correct, no dumps). Authoring unblocked.**
> The P4 grammar placement was broken (keyword heuristic dumped 64 points into topic 7 via loose substrings —
> "da" in "kudasai" etc., violating dependencies). Replaced with a durable, AI-classified + adversarially
> verified map:
> - **Workflows:** classify 364 grammar → themed topics (13 batch agents + 2 per-level verifiers), then a
>   rebalance pass over 91 catch-all members. Output assembled + deterministically validated
>   (`build_grammar_placement.py`: full coverage, same-level, て-form gate ≥topic 15, balance) into
>   **`design/grammar_placement.json`** (reviewable source of truth, 364 entries).
> - **`place_items.py` now consumes the map** (exact key match) instead of the keyword heuristic; the broken
>   `GRAMMAR_MAP` constant is removed. Re-placement: **max grammar/topic 64 → 27**; all 16 て-form
>   constructions cluster in topic 15; dependency scan clean (the 1 flag = false positive たくさん).
>   vocab/kanji placement was already sound (frequency-based) and is unchanged.
> - **Pilot** trimmed to a clean topic-15 lesson-1 (te-form + てください + 乗る; 出る/来る are pre-taught
>   examples, not introduced; てから deferred to its topic-17 placement). Em dashes removed; **validate_lessons
>   hardened to ban "—"**. validate_lessons = 0 errors/0 warnings; integrity_audit 0 FAIL/0 WARN; §10 held.
> - New scripts: `prep_grammar_placement_data.py`, `build_grammar_placement.py`. Provenance in
>   `research/derived/grammar_{to_place,assign_v1,rebalance_keys}.json` + `topics_ref.json`.
>
> **▶ NEXT = P6b (lesson authoring, per topic) → P7.** Placement is now correct, so author lessons: for each
> topic, split its placed items (grammar ≤5/lesson, vocab ≤15-25, kanji ≤10) into lessons; author rich bodies
> (les-n5-te-form-01 is the reference) referencing dissected sentences i+1 within cumulative_known_set + typed
> exercises + ending `<checklist>`; load_lessons → validate_lessons → export_course → commit per topic. Then
> per-kanji strand + conjugation/particle/JLPT exercise banks (roadmap §C/§G), then P7.
> **NOTE:** `place_items.py` now requires `design/grammar_placement.json`; a from-scratch rebuild must run it
> after ingest (placement persists across `replay_all`, which only rebuilds sentences).
>
> ---
>
> **2026-06-15 — P6 STARTED: rich-lesson FOUNDATION frozen + validated (atomic unit complete).**
> The lesson layer now has a durable, scalable, validated pipeline mirroring the corpus one
> (authored JSON → load → DB → export):
> - **Frozen schema** [`design/lesson_schema.md`](design/lesson_schema.md) v1 — machine-validatable freeze of
>   `lesson_format.md`: tagged HTML-like body (NO bare text; every piece wrapped), element/attr whitelist,
>   `ref=` namespaces (sent:/kanji:/vocab:/gram:/ex: + deferred img:/aud:/vid:), required structure (ends with
>   `<checklist>`; ≥1 retrieval + ≥1 production exercise), exercise answer-key shapes.
> - **Validator** `scripts/validate/validate_lessons.py` — enforces the above + ref resolution + introduce-once
>   + answer shapes. (Placement consistency = WARNING, see P6a.)
> - **Loader** `scripts/ingest/load_lessons.py` — generic/idempotent: `research/derived/lessons/*.json`
>   (durable authoring source, like dissection `*_result.json`) → DB (delete-then-insert by slug), computes
>   `cumulative_known_set`. Wired into `replay_all` (reset_sentences wipes lessons → reload on rebuild).
> - **Exporter** `export_course.py` now FLATTENS the tagged body → readable Markdown for the teacher-review
>   `.md` (refs resolved); `.json` keeps the app-ready tagged body.
> - **Pilot re-authored in rich format** (`author_pilot_lesson.py` → `research/derived/lessons/
>   les-n5-te-form-01.json`): the reference lesson bulk authoring mimics. **validate_lessons = 0 errors.**
>   Retired the obsolete markdown `add_pilot_lesson.py`.
>
> **▶ NEXT = P6a (placement re-sequencing) → P6b (lesson authoring) → P7.**
> - **P6a — fix the P4 grammar placement (BLOCKS authoring).** The first-pass placement has catch-all DUMPS
>   and dependency violations: topic 7 (desu-wa) holds **64** grammar incl. て-form-dependent points
>   (てください/てから) placed BEFORE て-form (topic 15) — violates curriculum.md §2 "no て-clauses before
>   て-form". Also topic 11 (31), topic 24 (30), topics 22/30 heavy. Re-distribute the 364 grammar (and
>   re-check vocab/kanji) across the 35 topics by **dependency + theme**, so each topic splits into
>   ~3–5-grammar lessons (chunk sizes curriculum.md §3). Lessons' `lesson_introduces` must ⊆ their topic's
>   placement (the validator warns when not). Likely a workflow (linguistic reasoning) + re-export outline.
> - **P6b — author lessons per topic** (one topic = atomic unit; workflow fan-out): split each topic's placed
>   items into lessons, author rich bodies referencing dissected sentences (i+1 within cumulative_known_set),
>   typed exercises, ending `<checklist>`. load_lessons → validate_lessons → export_course → commit per topic.
>   Add a per-kanji literacy strand (p6_authoring_spec §5) + conjugation/particle/JLPT exercise banks
>   (product_roadmap §C/§G). Use `les-n5-te-form-01.json` as the format reference.
> - **P7** — coverage audit (every reconciled item has exactly one introducing lesson; 0 kanji unused),
>   HTML-integrity, teacher-review queue.
>
> ---
>
> **2026-06-15 — ADVERSARIAL SANITY CHECK (5-auditor workflow) + fixes. DONE & validated.**
> Read-only multi-agent audit of repo/plan/data/validation/compliance, then a refutation pass. Verdicts:
> git hygiene PASS, validation PASS, IP/PII compliance PASS (no §1.4 leak; only Tatoeba+JEC+ai sources;
> push verified HEAD==origin/main). 3 confirmed findings (0 refuted) fixed, plus 2 latent reproducibility
> bugs the rebuild surfaced:
> - **Content blocklist** (`research/derived/content_blocklist.json` + gate in `persist()`, the single
>   chokepoint): removed 3 inappropriate sentences that predate the JEC filter (condom `sent:tatoeba-5019`;
>   AI "white underwear" `sent:gen-6189075543d7`; mild "kiss me" `sent:tatoeba-1284178`). Can never re-enter.
> - **Reproducibility bug #1**: `persist_batch.main()` kept ungrammatical AI (verdict.faithful=False) that the
>   replay path (`persist_pair`) correctly drops → 26 unfaithful AI had leaked into the bank. Fixed: `main()`
>   now delegates to `persist_pair` (one source of truth). Those 26 are now dropped (§10 held: only ±1 counts).
> - **Reproducibility bug #2**: `replay_all` didn't re-run `clean_emdash`, so a rebuild reintroduced 592 em
>   dashes (the cleaner edits the DB, not the saved `*_result.json`). Fixed: `clean_emdash --apply` is now a
>   replay post-step. **`replay_all` is now a FAITHFUL rebuild.**
> - Doc fixes: conjugation 408→508 (was stale in 2 docs); ATTRIBUTION enumerates all 6 JLPT lists;
>   corpus/INDEX.md gains the conjugations row; integrity_audit % now rounds (44.6→45).
> - **Bank = 4959, validate 0 errors, integrity_audit 0 FAIL/0 WARN. Real:AI = 2745 (55%) / 2214 (44%).**
>   §10: N5 vocab 99% grammar 94%; N4 vocab 99% grammar 99%. conjugation 508/508. Re-exported.
>
> **▶ NEXT = P6 (lessons) + roadmap enrichments + P7** (unchanged — see the P5 COMPLETE block below).
>
> ---
>
> **2026-06-15 — SECOND REAL SOURCE ADDED: JEC Basic (CC BY 3.0). DONE & validated.**
> Deep-research workflow (`research/second-source-deep-research.md`, 21 sources, 25 claims verified) compared
> JESC / JEC Basic / JParaCrawl / OpenSubtitles / KFTT / Tanaka. **Owner decision:** add **JEC Basic**
> (CC BY 3.0 Unported — commercial + redistribute, NO share-alike; clean) and **reject JESC** (CC BY-SA 4.0 +
> fan-subtitle upstream-copyright risk) and all copyright-murky/non-commercial corpora. **Licensing policy
> locked** (ATTRIBUTION.md → SOURCE LICENSING POLICY): bundle only CC-BY/CC0 real text (Tatoeba + JEC); never
> bundle CC BY-SA / copyright-murky prose AND never use it as an AI generation seed → AI sentences are
> clean-room from our own known-set only.
> - Ingested 4,729 JEC sentences (`ingest_jec.py` → `raw_jec`+`raw_jec_fts`); mined 129 real i+1 sentences
>   (`prepare_jec.py`), dissected (Layer-B pt-BR, all faithful), **content-filtered out 2 inappropriate**
>   (voyeurism/creepy — `extract_workflow_result.py` scan) → **127 persisted** (real, ai_generated=0).
> - Bank = 4988, 0 errors _(snapshot at JEC time — superseded by the sanity-check block above: 4959 after
>   removing 3 blocklisted + 26 ungrammatical AI)_. §10: N5 vocab 99% / grammar 94%; N4 vocab 99% / grammar
>   99%. **Real:AI ratio improved to over half human-written, the owner's goal.** Exported + docs updated
>   (ATTRIBUTION, sources.md, research/datasets/jec/MANIFEST.md, research/second-source-deep-research.md).
>
> **▶ NEXT = P6 (lessons) + roadmap enrichments + P7** (unchanged — see the P5 COMPLETE block below).
>
> ---
>
> **2026-06-15 — SCHEMA v2 OVERHAUL (owner-requested, before resuming P5). Phase 1 (local/mechanical,
> zero quota) DONE & committed:**
> - **Romaji sokuon fix** (行っ "ixtsu"→"it"; 0 'x' tokens). `replay_all.py` rebuilds the bank from saved AI
>   results at zero token cost (used to propagate skeleton changes).
> - **Mechanical Layer-A enums**: tokens get `pos` + `inflection` (+ raw `inflection_type`) from Sudachi;
>   particles get `function_type` (case/binding/conjunctive/sentence-final/adverbial/nominalizer); vocab gets
>   `register` enum from JMdict misc (colloquial/slang/vulgar/honorific/humble/polite…). All in export.
> - **i18n locale-objects everywhere**: `{"pt-BR":…,"en":…}` (en = Layer-A source) for kanji meanings, vocab
>   gloss, sentence translation, token/particle/grammar/family text. Kanji nanori `common:false` (data is
>   faithful to KANJIDIC2 — verified vs kanjiapi; just de-emphasized).
> - **Conjugation bank** `corpus/conjugations/{n5,n4}.json` (508 verbs/adjectives after the suru-noun fix, deterministic
>   `conjugate.py`) for the conjugation exercise bank.
> - **Grammar `forms[]`** parsed from structure_pattern (build_grammar_forms.py). **translation_style.md** =
>   authoring contract (natural pt-BR not literal mirror; no "Quanto a mim"; drop 。 in GENERATED jp; humanizer).
>   Dissect prompt hardened. Spot-check: translations already natural/accurate (1/2465 "Quanto a").
> - Migrations 005 (token/particle enums), grammar_point.forms_json. Bank rebuilt = **2465, 0 errors**.
>
> **SCHEMA v2 Phase 2 DONE (2026-06-15):** grammar enriched (all 364) — `register[]` multi-enum
> (plain/casual/polite/formal/written/honorific/humble/colloquial/literary/masc/fem), `caution` (14
> flagged), per-form pt `meaning`, humanized explanation/formation/nuance. Sentence prose audited CLEAN
> (`detect_ai_tells.py`: 33/2465, mostly false positives; 1 fixed); humanizer enforced going forward via
> `translation_style.md` + dissect prompt. **SCHEMA v2 COMPLETE.**
>
> **Review round 2 (2026-06-15) — owner re-review fixes:** em dash (—) purged from ALL pt text (767→0,
> `clean_emdash.py`, banned in prompts/style-guide; fixed a JSON-corruption it caused in 13 form_meanings);
> kanji `example_words` + `example_sentences` added (247/250, 245/250). Answered: vocab `forms` = orthographic
> (meaning lives in `senses`, already glossed), `pitch` = phonetic (no meaning needed). **Deeper enrichments
> the owner wants are PLANNED in [`design/product_roadmap.md`](design/product_roadmap.md)** — kanji per-reading
> compounds+notes (§D), grammar formation/nuance tokenization into enums (§E), sentence machine `pattern[]`
> (§F), verb-conjugation EXERCISE bank ≥5 ex/form (mine bank by token `inflection`, AI-fill gaps) (§C), JLPT
> item bank (§G). Product vision → data map in that doc.
>
> _(ARCHIVED snapshot — superseded by the sanity-check + JEC blocks above; live bank = 4959.)_
> **▶ P5 COMPLETE (2026-06-15). Bank = 4861, 0 errors, fully validated (validate §7 + integrity_audit 0/0 +
> §1.7 graph PASS). 2620 real Tatoeba (53%) + 2241 AI (46%, grammaticality-gated).**
> **§10: N5 vocab ≥3 99% / grammar ≥5 94%; N4 vocab ≥3 99% / grammar ≥5 99%.** Irreducible residual ~18
> (in the needs_review queue, justified): orthographic variants (此処/居る/為る = kanji for ここ/いる/する;
> ９日/８日/４日 irregular day-counters) whose CONCEPTS are fully covered via the normal form, + abstract
> grammar categories (く-adverbial, na-adjectives) that appear throughout but resist a single key-match.
> Sentence sources answered: Tatoeba is best for beginner i+1; most gaps were LINKING (relink_vocab,
> multi-valued forms, +15k edges) + over-filtering, not real shortage (see product_roadmap.md). Real>AI order
> enforced: link → mine Tatoeba (tighten→relax) → generate only the genuine tail.
>
> **▶ NEXT PHASE = P6 (lessons) + roadmap enrichments + P7.** Recommended order:
> 1. **P6 lessons** — rich tagged-HTML lessons per topic referencing corpus IDs (`design/lesson_format.md`,
>    `design/p6_authoring_spec.md`): by-ID, FSRS enroll, 100% kanji, per-kanji option, one schema.
> 2. **Roadmap enrichments** (`design/product_roadmap.md`): kanji per-reading compounds (§D), grammar
>    formation/nuance tokenization (§E), sentence `pattern[]` (§F), **conjugation + particle + JLPT exercise
>    banks** (§C/§G — mine the bank via token `inflection`/`function_type`, AI-fill gaps).
> 3. **P7** QA: full validate, stats, L+ superset compare, teacher-review queue (acceptance §10).
> **Recipes (run ONE workflow at a time; every batch: persist_batch → repair_glosses → `clean_emdash --apply`
> → validate → export → commit):**
> - **Selection coverage:** `prepare_coverage.py --level n5|n4 --target 3` (vocab) / `prepare_grammar_coverage.py`
>   (grammar) → split_groups → `dissect_batch_workflow.js` → persist `--batch …`.
> - **Generation (tail):** `prepare_generation.py --level L --kind vocab|grammar --min N --out-dir gen_X` →
>   `generation_workflow.js {dir,count}` → `prepare_generated.py --level L --kind K --result … --out batch_gen_X.json`
>   (gates: uses target + ≤max-new i+1 + dedup) → split_groups → `dissect_batch_workflow.js` → persist. Flags
>   `ai_generated`+`needs_review`. **Staged & ready:** gen_n4_vocab(150), gen_n5_grammar(62), gen_n4_grammar(95).
> - `replay_all.py` rebuilds whole bank from saved `*_result.json` at zero token cost (all batch_*/gen_* auto-join).
> **Remaining to §10:** finish N4 vocab gen + N5/N4 grammar gen + top-up selection → then **P6 lessons** +
> the roadmap enrichments (kanji per-reading, grammar tokenization, conjugation/JLPT exercise banks) + **P7**.

> **2026-06-14 (P5 DEEPENING — owner chose "fully deepen to §10"). SESSION LIMIT hit, resets 8:30pm
> America/Sao_Paulo.** **Sentence bank = 1576, 0 validation errors.** Coverage:
> `n5: vocab ≥1 78% ≥3 60% | grammar ≥1 76% ≥5 51%` · `n4: vocab ≥1 67% ≥3 41% | grammar ≥1 30% ≥5 0%`.
> Vocab coverage (prepare_coverage rounds a–d both levels) + N5 grammar coverage (chunks 0–3 done, **chunk 4
> partial** 11/20) DONE. **N4 grammar chunks NOT yet run** (partitioned + ready).
>
> **RESUME QUEUE (ONE workflow at a time; recipe = split_groups→Workflow `scripts/ingest/dissect_batch_workflow.js`
> {dir,count}→read .output `.result`→`persist_batch --batch <batchfile>`→`repair_glosses`→`validate`→
> `export_corpus`→commit):**
> 1. **Re-run N5 grammar chunk 4** (fills 9 failed): `{dir:".../research/derived/gram_n5_4_groups",count:20}`,
>    persist `--batch batch_gram_n5_4.json` (idempotent).
> 2. **N4 grammar chunks 0–7** (ALL split + ready): each `{dir:".../research/derived/gram_n4_<i>_groups",
>    count:20}`, persist `--batch batch_gram_n4_<i>.json`. This is the biggest remaining lift (N4 grammar ≥5 = 0%).
> 3. ~~Deterministic particle-link~~ **DONE** (`particle_link.py`, +91 edges; fundamental particles ~8 ex;
>    N5 grammar ≥5 now 59%). Re-run after more sentences land to top up や/さ/し (currently <8).
> 4. **More vocab deepening** rounds (`prepare_coverage.py --level n5|n4 --target 3 …`) until ≥3 plateaus,
>    then RAISE to `--target 5` where wanted.
> 5. **GENERATION** for residual tail selection can't reach (build: agent writes i+1 sentences from a topic's
>    known-set, flagged `ai_generated`; tokenize → dissect same engine). Spec §1.2: selection first.
> 6. Then **P6 lessons** + **P7** QA. Coverage snippet: see prior turns (`Counter(sentence_vocab.vocab_id)` /
>    `sentence_grammar.grammar_id`, % ≥1/≥3/≥5 per level).
>
> **(milestone) P5 first-pass seeding COMPLETE.** All 35 content topics seeded via the precise batched engine
> (v2). Engine, coverage selector, self-heal all built and proven (see recipe block below).
>
> **Coverage vs §10 (≥3 sent/vocab, ≥5/grammar) — the remaining heavy lift:**
> `n5: vocab 706 → ≥1:186 (26%) ≥3:70 (9%) | grammar 151 → ≥5:10`
> `n4: vocab 653 → ≥1:36 (5%)  ≥3:15 (2%) | grammar 213 → ≥5:1`
> First-pass seeded each topic's grammar + key vocab; the long tail is thin. **Deepening** (engine below):
> `prepare_coverage.py` greedily selects Tatoeba covering the most undercovered vocab — BUT each batch advances
> ~1 vocab/sentence because rare vocab seldom occur in known-set-pure Tatoeba (max-new≤2). **CONCLUSION: the
> rare tail needs the GENERATION path (still TODO)**, not just more selection. Full §10 is many more workflows.
>
> **Strategic fork for the next session (owner may choose):**
> 1. **Deepen P5 coverage** to §10 — many selection batches (mid-freq vocab) + build & run a GENERATION
>    workflow for the rare tail (agent writes i+1 sentences from a topic's known-set, flagged `ai_generated`).
> 2. **Start P6 lessons now** — every topic already has seed examples; author rich-format lessons
>    (`design/lesson_format.md`) referencing existing sentence IDs, deepen the bank lazily as lessons demand.
> 3. Hybrid: ensure **≥1 sentence for every taught item** first (cheaper than ≥3), then P6.
>
> **✅ Done earlier:** foundation+content (meanings 100%, grammar 364/364, families, pitch 89.8%); P7 groundwork
> (§1.7 graph queries PASS, review queue, L+ superset, objectives/overviews); **PRE-P5 i18n** (localized_text
> live, 6,937 rows → pt-BR, neutral fields). **Run ONE workflow at a time** (concurrency → rate-limits).

**Plan (revised after 2026-06-14 gaps audit — see `reports/gaps_audit.md`):** content layers were
missing from the plan. Execute the ADDED steps in dependency order, THEN resume topic dissection:
1. **P5b — Layer-B pt-BR meanings (FOUNDATIONAL, do first):** translate `vocab_sense.gloss_en→gloss_pt`
   (4,061) + `kanji.meanings_en→meanings_pt` (250) via batch→Workflow→validate; populate
   `kanji_reading.example_vocab_ids`. Everything (lessons, glosses) depends on this.
2. **P6-grammar — Layer-C grammar explanations:** author `label_pt`+`explanation_pt`+`formation_pt`+
   `nuance_pt` per taught grammar point (Workflow, needs_review). ← owner flag.
3. **P4b — full families:** semantic_field / word_family / particle_set / contrast_pair so every item ∈ ≥1 family.
4. **P2b — pitch accent data:** source kanjium/OJAD-derived → `vocab_pitch` (data only; audio deferred).
5. **Then resume** mass dissection + lesson authoring topic-by-topic (recipe below), then **P7** QA.

### P5 status (engine v2 — batched + precise grammar linking): rebuilding bank from saved results.
**Engine v2 (current; run ONE workflow at a time):**
1. `prepare_batch.py --topic <slug> --targets <term:count …> --out research/derived/batch_<t>.json` — selects
   real Tatoeba within the i+1 known-set AND attaches the topic's `grammar_candidates` (key/pattern/label) to
   each item. (FTS5 is **trigram** → it can't match <3-char terms; prepare auto-falls back to LIKE for short
   targets like たい/一番/たり.)
2. (multi-topic) concat batches → `batch_all.json` (dedup by slug).
3. `split_groups.py <batch.json> <out_dir> 5` — K=5 sentences per GROUP file (slug-keyed, ~5× cheaper than
   1/agent, dodges the array-index bug).
4. Workflow **`scripts/ingest/dissect_batch_workflow.js`** (`yomineko-dissect-grp`), args
   `{dir, count=<#groups>}` → returns flat `[{layerB,verdict}]`. Each agent authors translation + literal +
   structure + per-token gloss/role/conjugation + particle function/explanation, AND returns
   **`grammar_keys`** = the candidate keys the sentence GENUINELY uses (strict, by meaning not substring →
   no 冷たい≠〜たい false-positives; picks affirmative/negative variant; multi-key OK).
5. Result envelope is `{summary,…,result:[…]}` — locate the `result` list (it has `layerB`), write bare array
   to `..._result.json`. `persist_batch.py --batch … --result …` (links grammar via agent keys; vocab/kanji
   from Layer-A tokenization).
6. `repair_glosses.py` (auto-fills any content token the agent skipped: from its vocab pt-gloss, else a
   closed-class dict; reports unresolved). Then `validate.py` (must be 0 errors), `export_corpus.py`, commit.
**Rebuild-from-results property:** the durable AI output is the saved `*_result.json` files. After any
persist/linking-logic change, `reset_sentences.py` + re-`persist_batch` from saved results rebuilds the bank
deterministically with NO new agent calls (only re-run the workflow if the agent's *output schema* changed).
**Still TODO in P5:** (a) raise per-topic counts to acceptance (≥3 sent/vocab, ≥5/grammar) — current batches
are seed-sized; (b) **sentence GENERATION path** for cold-start early topics (greetings/desu-wa/numbers: tiny
known-set → few Tatoeba hits) — generate i+1 JP flagged `ai_generated` then dissect same way; (c) P6
rich-lesson schema (`design/lesson_format.md`) finalized from real authored content.
Then **P7**: full validation, `reports/stats.md`, coverage comparison vs L+ `concept_inventory.md` (superset),
§1.7 cross-cutting query tests, assemble needs_review queue.
**Pipeline scripts:** dissect / select_candidates / prepare_batch / persist_dissection / persist_batch /
validate / add_pilot_lesson / export_corpus / export_course. Kana caveat は→わ,へ→え,を→o; pt-BR generated
Layer-B (EN-pivot); generous AI backfill all flagged; store kana+romaji; pitch data only (audio deferred).
**Scale reminder:** this is the multi-session bulk (~all topics × dissection + lessons).
Recommend pilot = **`top:n5-te-form`** (mid-N5; rich Tatoeba supply; known-set = items introduced in topics
order≤15). Steps: (1) **build the §7 validation suite first** (`scripts/validate/`); (2) write the SudachiPy
A+C **dissection pipeline** (kana caveat: は→わ, へ→え, を→お) emitting the §6 shape uniformly; (3) **select**
Tatoeba sentences via `raw_tatoeba_fts` whose tokens are within the topic's cumulative-known-set (i+1),
preferring those with EN/audio; (4) **Layer-B pt-BR**: generate translation + pt_literal + per-token gloss +
particle explanation, validate readings/lemmas vs KANJIDIC2/JMdict; persist to `sentence`/`token`/`particle`;
(5) author the topic's **lessons** (dense pt-BR + structured exercises, sentence refs BY ID); (6) export
`corpus/sentences/` + `course/n5/top-...`; **score vs `design/quality_rubric.md`** (all dims ≥3, gates pass);
fix; commit. Cumulative-known-set helper: items with `introducing_topic_id` whose topic.ord ≤ pilot topic.ord.
**DONE:** P-pre,L(+L+),R(approved),P0,P1,P2,P3,P4(1st-pass placement). Corpus (kanji 250 / vocab 1,359 /
grammar 364 / families 396) + course outline (35 topics) all exported to `corpus/`+`course/` as canonical
LLM-readable JSON+MD; SQLite is a regenerable index.
**Reminder:** real Tatoeba PT is 1.8% → generate pt-BR (Layer B, EN-pivot 93.5%); generous AI backfill (all
flagged); store kana+romaji; pitch data only (audio deferred). `sudachidict-full` installed.
**P5 dissection notes (verified):** `sudachidict-full` installed + SudachiPy A+C tokenization works. CAVEAT —
Sudachi `reading_form()` returns the *dictionary* reading, so override contextual particle kana in the
dissection: は→わ, へ→え, を→お (topic/direction/object particles). Build the §7 validation suite first; the
single dissection function must emit the §6 shape uniformly.

---

## Gate
**P0 → P7 do NOT begin until the owner approves the Phase R output.** L and R gate the build.

---

## Phase plan & status

| Phase | What | Status | Output |
|------|------|--------|--------|
| **P-pre** | git init, folder tree, `CLAUDE.md`, `STATE.md`, `INDEX.md` stub, commit | `done` | scaffold |
| **L** | Clean-room local course analysis (isolated, de-identified) | `done` | `research/local-course-insights/{topic_sequence,ideas_to_adapt,gaps_to_beat}.md` |
| **R** | Research, audit & self-improvement (MAX thinking) — **gate** | `done` | see R1–R6 |
| ↳ R1 | Critically audit this spec vs the goal | `done` | `design/PLAN_REVIEW.md` Part 1 |
| ↳ R2 | Research quality bar + methods (curricula, BR market, SLA, BR-PT) | `done` | 4 `research/references/` notes (adversarially verified + corrected) |
| ↳ R3 | Empirically measure source coverage (real numbers) | `done` | `reports/source_coverage.md` + `research/coverage/r3_probe_results.json` |
| ↳ R4 | Pressure-test & improve schemas | `done` | `design/schema_v2.md` |
| ↳ R5 | Define quality rubric | `done` | `design/quality_rubric.md` |
| ↳ R6 | Self-improve plan + draft outline | `done` | `design/PLAN_REVIEW.md` + draft `design/course_outline.md` |
| **— OWNER APPROVAL GATE —** | summarize & wait | ✅ `done` | **approved 2026-06-13** (decisions: PLAN_REVIEW Part 6) |
| **P0** | Finalize scaffold; write SQLite schema from `schema_v2.md` | `done` | venv, `001_init.sql` (29 tables), `init_db.py`, `ATTRIBUTION.md`, `sources.md` |
| **P1** | Ingest authoritative datasets → SQLite raw tables | `done` | `db/corpus.sqlite` (kanji inventory, JMdict raw, Tatoeba raw+FTS), `reports/stats.md` |
| **P2** | Level reconciliation (≥3 lists) + per-reading tiering | `done` | 250 kanji + 1,359 vocab leveled; `reports/validation.md` |
| **P3** | Methodology & curriculum research synthesis | `done` | `design/curriculum.md` (rules + pt-BR glossary) |
| **P4** | Course outline: Module → Topic → Lesson (family-driven) | `done (1st pass)` | 3 modules, 35 topics; all 1,359 vocab + 250 kanji + 364 grammar placed at an introducing topic; `course/` exported. Refine in P6: N4 grammar residual (146) + N4 kanji cap. |
| **P2b** | Pitch accent ingestion (data only; audio deferred) | `done` | kanjium → `vocab_pitch` 1,221/1,359 (89.8%) |
| **P4b** | Full family coverage (semantic/word/particle/contrast) | `done` | every item ∈ ≥1 family (vocab 1359/kanji 250/grammar 364); 395 families (#9) |
| **P5b** | Layer-B pt-BR meanings (vocab senses + kanji) | `done` | kanji 250/250, vocab 4061/4061 senses ✓ (#1,#2) — _example_vocab_ids still TODO_ |
| **P6-g** | Layer-C grammar explanations (label/expl/formation/nuance) | `done` | 364/364 (#3) — owner flag resolved |
| **P5** | Sentence corpus: mining + dissection (SudachiPy A+C) | `in_progress` | pipeline PROVEN incl. Workflow scaling (author+verify); **19 te-form sentences** dissected, 0 errors → `corpus/sentences/`. Remaining: run batches across all topics. |
| ↳ P5-pilot | ONE complete topic end-to-end, checked vs rubric (gate) | `✅ gate PASSED` | `reports/pilot_review.md` (gates pass; D2/D6=4); punch-list before scaling |
| **P6** | Courseware authoring: lessons (rich HTML + exercises) | `in_progress` | pilot lesson done. **Follow [`design/p6_authoring_spec.md`](design/p6_authoring_spec.md)** + **rich format [`design/lesson_format.md`](design/lesson_format.md)** (custom-element HTML, refs by ID, phrase/kanji modals, inline exercises): by-ID no-dup, introduce-once → FSRS-enroll, 100% coverage, optional per-kanji lessons |
| **P7** | Validation & QA gates (+ coverage comparison vs Phase L) | `pending` | `reports/validation.md`, `reports/stats.md` |

---

## Dataset manifest (versions + checksums)
_Populated in P1; provenance also recorded in `design/sources.md`. (R3 may pull samples earlier for coverage probing.)_

| Dataset | Version/date | SHA256 | License | Commercial-OK? |
|---------|-------------|--------|---------|----------------|
| jmdict-simplified (JMdict) | — | — | — | — |
| Kanjidic2 (jmdict-simplified) | — | — | — | — |
| Kradfile/Radkfile | — | — | — | — |
| KanjiVG | — | — | — | — |
| Tatoeba (jpn/eng/por + links + audio) | — | — | — | — |
| JLPT lists (≥3, community) | — | — | — | — |
| Frequency list | — | — | — | — |
| Pitch accent (optional) | — | — | — | — |

---

## Validation thresholds (working defaults; may be revised in R3)
- Dissected sentences: **≥3 per vocab**, **≥5 per grammar point**; rich per-topic bank (hundreds where sources allow).
- AI-generated sentences: capped as a % per topic (cap set in R3), always `needs_review`.
- Zero unresolved reading/lemma mismatches against KANJIDIC2 / JMdict.

---

## Session log
- _(P-pre)_ Created dedicated git repo, folder tree, `CLAUDE.md`, `STATE.md`, `.gitignore`, `INDEX.md` stub.
- _(L)_ Clean-room analysis via isolated subagent (raw material never entered main context). Found a library
  of 11 courses / 73 modules / 621 lessons (beginner→intermediate→advanced spine + 8 supplements). Output:
  3 de-identified abstraction files, verified clean (no names, no verbatim/reworded text). Key gaps to beat:
  no pitch accent, no JLPT scaffolding, katakana/adjectives/time-vocab mis-sequenced, hard difficulty cliff.
- _(R3)_ Probed real datasets: kanji 100% covered (245), vocab ~99% after normalization, Tatoeba PT only 1.8%
  (→ generate pt-BR Layer B, EN-pivot 93.5%), audio 2.5% (→ TTS), ≥3/vocab & ≥5/grammar thresholds realistic.
- _(R2)_ Workflow: 4 cited research notes + adversarial verify (8 agents). Curricula/SLA/BR-market = solid;
  BR-PT = minor issues → 4 factual overstatements corrected at source (vowel "1:1", length 2.5–3x, /u/ "spread",
  ち/じ dialect) + SLA phonetic-component softening. Verification traces added to the notes.
- _(R1/R4/R5/R6)_ Wrote PLAN_REVIEW (audit + 14 decisions + improved-spec addendum), schema_v2 (6 hard examples
  pass), quality_rubric (6 dims + hard gates + pilot gate), course_outline draft (pre-N5/N5/N4), sources.md.
  **STOPPED at the approval gate per the kickoff instruction.**
