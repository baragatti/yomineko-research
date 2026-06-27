# STATE.md — Yomineko Corpus Build (progress + resume)

> **Status legend:** `pending` · `in_progress` · `done` · `needs_review` · `blocked`
> Spec: [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md). Rules: [`CLAUDE.md`](CLAUDE.md).

---

## ▶ RESUME HERE

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
> 8. **TODO (owner-flagged 2026-06-26) — N5 kanji count is 80, JLPT N5 is widely cited as ~100-103.**
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
