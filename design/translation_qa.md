# Translation accuracy + naturalness + final validation (PLAN — not executed; start when tokens refresh)

> **Owner directive (2026-06-25):** AI makes translation mistakes often; minimize them everywhere — Japanese
> phrases, kanji explanations, particles, verb conjugations, and especially JP → pt-BR. Add a **final
> validation step** that checks the translations AND the way lessons are written: catch "AI-like"/non-human
> prose and **over-literal** renderings (e.g. 「私は学生です」 → "Quanto a mim, sou estudante" instead of the
> natural "Eu sou estudante" — the literal mirror belongs in `translation_literal`, never in the natural
> field). Use **real, daily-life** Japanese with **real, daily-life** EN + pt-BR (no slang). **No ShareAlike,
> no copyright-infringing material.** Validate the whole course well.
>
> This is the plan + how to start. **Nothing here is executed yet.** Spec for tone: [`translation_style.md`].

## 0. Principle
Three layers of defense, cheapest first: **prevent** errors (ground in facts) → **detect** them (automated
checks) → **route survivors to human review** (the mandatory teacher loop, §1.8). Most of the tooling already
exists; this plan mostly *assembles, scales, and adds 3 detectors + a final gate*.

### 0.1 Aim: "review confirms, it does not correct" (target 100% correct)
**Guiding principle (owner, 2026-06-25):** `needs_review` does NOT mean "rough AI draft a human will fix." It
means **"content we believe is already correct, awaiting a human's confirming signature."** We aim for *100%
correctness before review* — whether that's fully reachable or not, every decision optimizes toward it, so the
teacher pass is, in the normal case, a **confirmation, not a repair**. Consequences that bind the whole plan:

- **Raise the bar, don't defer to the reviewer.** A borderline/low-confidence item is **regenerated or
  re-selected from real text**, never shipped with "the reviewer will catch it." Below the trust threshold ⇒
  it does not enter the review queue as accepted content; it goes back to the pipeline.
- **Ground everything so review is easy to confirm.** Each item carries its **evidence** alongside it — the
  real source it came from (Tatoeba/JEC id), the trusted EN it was cross-checked against, the dictionary
  senses it matches, the checks it passed — so a reviewer verifies *against shown evidence* in seconds rather
  than re-deriving correctness. (Surface this in the review queue.)
- **Every correction is a pipeline bug, fixed upstream (the feedback loop).** When review *does* find an
  error, we don't just edit that item — we ask "what automated check would have caught this?", add it (a new
  detector / guardrail / golden case), and re-run it across the corpus. Each human correction permanently
  closes a *class* of error, so the correction rate trends toward zero over time.
- **Track the correction rate as the health metric.** Measure: of reviewed items, what fraction needed an
  edit? The goal is to drive this low (review = confirmation). A rising correction rate blocks shipping and
  triggers a pipeline fix. The golden set (§9.5) and a periodic human-sampled audit (§9.4) keep this honest.
- **Determinism + real sources first** precisely *because* they need no correction: a Sudachi reading or a
  selected Tatoeba sentence with its human EN is confirm-only by construction; generated prose is where
  correction risk concentrates, so it gets the heaviest gate (§9).

## 1. Error taxonomy (what we are hunting, by content type)
| Content | Layer | Typical AI error | Anchor we can check against |
|---|---|---|---|
| Sentence JP | A (Tatoeba/JEC) / gen | unnatural/wrong if generated | Sudachi re-parse; real-source provenance |
| `translation` (pt-BR) | B | **over-literal mirror**, meaning drift, register | trusted EN + back-translation |
| `translation_literal` | B | should BE literal — error if natural | contrast vs `translation` |
| token `gloss`/`role`, particle `function`/`explanation` | B | wrong sense, wrong role label | JMdict gloss; neutral `function_type`/`pos` enums |
| kanji `meanings` (pt) | B | drift from KANJIDIC | KANJIDIC `meanings_en` |
| vocab `gloss` (pt) | B | drift from JMdict | JMdict `gloss_en` |
| grammar `label`/`explanation`/`nuance` | C | AI-like prose, subtle inaccuracy | EN parallel + multi-vote |
| verb/adj conjugation forms | deterministic | low risk; pt label mismatch | the deterministic rule itself |
| lesson body + exercises | C | AI-tells, literalism, register | style contract + humanizer |
| EN parallel (all of the above) | B | drift from pt/JP | pt↔en cross-check |

## 2. Prevention (reduce errors before they exist)
- **Ground in real text** (see [`reading_practice.md`] §5 + §"complementary sources" below): real human JP with
  trusted human EN beats generated JP. Generation is last resort, anchored + flagged.
- **Deterministic where possible**: conjugations are rule-generated (not AI); tokenization/readings from
  Sudachi (Layer A). Keep it that way; never let AI overwrite a deterministic field.
- **Style contract in every generation prompt**: [`translation_style.md`] — natural pt-BR in `translation`,
  the は=「quanto a」 literal mirror ONLY in `translation_literal`; register-aware; daily-life; no slang; drop
  。 in generated JP; run `humanizer` on prose.

## 3. Detection tool suite (existing → extend → add)
**Already built (use/scale):**
- `validate.py` — §7 sentence integrity: tokenization re-derivation (§7.2), kanji-inventory, lemma existence,
  Layer-B completeness. (Hard gate.)
- `tr_audit_sample.py` (+ `--random`) + `tr_audit_workflow.js` — adversarial faithfulness audit (pt/en pairs).
  **Scale up:** raise coverage from a 240 sample toward full coverage of high-risk fields; keep multi-vote.
- `detect_ai_tells.py` — AI-tell detector. **Extend** with the pt-BR literalism patterns below.
- `validate_all.py` — the structural gate (8 hard validators).
- `humanizer` skill — rewrite flagged non-human prose.

**To ADD:**
1. **Ground-truth consistency checker** (deterministic, cheap, high-value): for every vocab/kanji, verify the
   pt-BR `gloss`/`meanings` is a faithful rendering of the JMdict/KANJIDIC `en` (e.g. an AI judge: "does the
   pt list cover the en senses? any invented/missing sense?"). For particles, check the pt `function` is
   consistent with the neutral `function_type` enum; for tokens, the `role` vs `pos`. Flags drift from the
   authoritative dictionary.
2. **Back-translation check** (automated signal): translate each pt-BR `translation` back to EN (cheap model),
   compare to the trusted EN; large divergence → flag. Same for JP→pt where a trusted EN exists. Catches
   meaning inversions/drops without human review.
3. **Anti-literalism / "AI-like" detector** (the owner's core ask): scan the NATURAL fields (`translation`,
   lesson prose) for literal-mirror + AI tells and flag for rewrite:
   - literal-mirror calques: leading "Quanto a mim/a você/a …", topic-marker calques, "É … que" clefts that
     mirror は/が, over-faithful particle renderings, JP word-order in pt;
   - AI-tells: rule-of-three, "não só … mas também" overuse, hedging fillers ("vale notar/lembrar"),
     inflated/promotional language, em dash (already gated), stiff/non-conversational register;
   - register: not-too-formal, not slangy, daily-life. Output a ranked fix list; auto-run `humanizer` on the
     worst, re-validate.
4. **License-compliance audit** (see §5).

### 3.4 The literal-translation field (`translation_literal`) — model + both-fields-pass-guards (owner 2026-06-25)
- **Per-language — already built.** `translation_literal` is a locale-object `{pt-BR, en}`: each target
  language has its own literal rendering (the bilingual pass populated both). The model the owner described —
  natural meaning in `translation`, the word-for-word/structural mirror in `translation_literal` — already
  exists; the natural field is the "correct" daily-life one, the literal field shows the JP structure.
- **Nullable policy (NEW).** Keep `translation_literal` populated ONLY when it adds teaching value — i.e. when
  the literal/structural rendering meaningfully **diverges** from the natural one (the interesting JP→target
  cases: は-topic fronting, double negatives, 〜てしまう regret, idioms…). When the natural translation already
  *is* the literal (no divergence worth showing), leave it **null** — no redundant duplicate. (localized_text
  already supports absence = null; only ~11/5565 are exact-text duplicates, so deciding "is the divergence
  pedagogically interesting?" needs a light semantic pass, default keep-where-divergent.)
- **Feature: explain the JP→target thinking.** Surface `translation_literal` together with the per-token
  `gloss`/`role` and `structure_explanation` as a "how the Japanese actually maps" explainer in the UI
  (sentence dissection + the reading boxes), so the learner sees *why* the natural translation differs from
  word-for-word. The literal field becomes a teaching aid, not just data. (Cross-ref `reading_practice.md`.)
- **BOTH fields must be correct and pass the guards (NEW, owner requirement).** Different criteria per field:
  - `translation` (natural) → faithfulness + **naturalness** (§3.3): must read like daily-life pt-BR/en.
  - `translation_literal` → **literal-correctness**: it must be an *accurate* word-for-word/structural mapping
    of the JP (right morpheme senses, particle labels, no mistranslation) — it is allowed (expected) to be
    un-natural, but it may NOT be *wrong*. Add a `literal-correctness` check to the audit (an agent verifies
    the literal faithfully mirrors the JP given the tokens). The detector exempts the literal field from the
    *naturalness/literalism* tells (those are by design) but NOT from correctness — neither field ships with
    an error.

## 4. The FINAL validation step (the end gate — run before "production")
Order of operations, each producing a report; the gate passes only when there are **0 unresolved major
translation errors** and every flagged item is fixed or queued for human review:
1. `validate_all.py` (structure/integrity) → must be green.
2. **Full** pt↔EN cross-check + back-translation over ALL translated fields (not sampled) → major/minor report.
3. Ground-truth consistency (gloss/meaning vs dictionary; role/function vs enum) → drift report.
4. Anti-literalism + AI-tell + register pass over ALL natural fields → rewrite list → `humanizer` → re-check.
5. Adversarial multi-vote faithfulness audit at scale → confirmed-error list.
6. License-compliance gate (§5) → must be clean.
7. Compile a **prioritized human-review queue** (everything still `needs_review`, ranked by risk) — the
   mandatory teacher sign-off (§1.8). The corpus is "review-ready" when 1–6 pass and 7 is produced.

## 5. License compliance — no ShareAlike, no copyright (NEW constraint; needs an owner decision)
**For NEW / complementary material: permissive only** — CC0 / CC BY / public-domain / MIT. **No CC BY-SA**,
no scraped/copyrighted text. Add a check to the source manifest pipeline that rejects any non-permissive source.

**Honest flag — the existing backbone is CC BY-SA.** The directive conflicts with current foundations:
- **CC BY-SA (ShareAlike) today:** JMdict, KANJIDIC2, Kradfile/Radkfile (EDRDG), KanjiVG, kanjiapi.dev — these
  are the kanji/vocab dictionary + radical + stroke backbone. Tatoeba's *Tanaka-lineage* subset is also CC BY-SA.
- **Already permissive (keep):** Tatoeba core (CC BY / CC0), JEC Basic Sentences (CC BY 3.0), and the MIT JLPT
  lists (davidluzgouveia, AnchorI, bluskyo, jlptvocabapi, open-anki, elzup, hanabira).

This needs an **owner ruling**, because "no SA at all" would require replacing the EDRDG/KanjiVG backbone
(hard — they are the de-facto open JP dictionaries; permissive equivalents are scarce). Options to weigh:
(a) scope "no SA" to **new/added** material only (easy; the directive as applied going forward); (b) keep the
SA *database* but treat the **courseware/app as the product** (the strategy already noted in `ATTRIBUTION.md`);
(c) invest in replacing SA sources with permissive ones (large, uncertain). **Recommend (a)+(b) now, with a
documented license-review task; enforce permissive-only on everything new.** Also: within Tatoeba, **filter out
the CC BY-SA Tanaka-lineage** sentences and keep only CC BY / CC0.

## 6. Complementary free, validated Japanese material (re-checked; permissive only)
Re-searched for permissive, human-validated JP material with trustworthy translations:
- **Tatoeba** (CC BY, some CC0) — already our main source; real human JP + human EN, learner-oriented. Keep;
  filter to CC BY/CC0 (drop SA Tanaka lineage). ([downloads](https://tatoeba.org/en/downloads))
- **JEC Basic Sentences** (CC BY 3.0) — already used; permissive, daily-register, ja+en.
- **Aozora Bunko** (public domain) — classic literature; PD so license-clean, but **archaic register** → only
  for optional advanced reading, not beginner/daily-life. Use sparingly if at all.
- **Wikidata Lexemes** (CC0) — usage examples; sparse but fully permissive; possible enrichment.
- **Kokoro-Speech / public-domain speech sets** (PD) — for a future audio/play-mode, not text.
- **EXCLUDED by the no-SA rule now:** KFTT (CC BY-SA, encyclopedic), Tanaka corpus (CC BY-SA), Japanese
  Wikipedia/Wikibooks (CC BY-SA), JESC/OpenSubtitles/JParaCrawl (non-commercial / murky). 
**Verdict:** Tatoeba (CC BY/CC0) + JEC remain the trustworthy permissive backbone for daily-life sentences;
Aozora (PD) + Wikidata Lexemes (CC0) are optional permissive complements. No new SA dependency is needed.

## 7. How to start (when tokens refresh) — suggested order
1. **Cheap wins first:** extend `detect_ai_tells.py` with the anti-literalism patterns (§3.3) + run the
   full pt↔EN cross-check (tooling exists) → first error report. Low token cost, high signal.
2. Add the **ground-truth consistency checker** (§3.1) — deterministic-ish, catches dictionary drift.
3. Add the **back-translation check** (§3.2).
4. Scale the **adversarial audit** to full coverage of high-risk fields.
5. Run the **final gate** (§4); fix majors; auto-`humanizer` the prose; re-run.
6. Do the **license audit** (§5) + get the owner ruling on the SA backbone.
7. Produce the **human-review queue** (§4.7).
(Reading-practice boxes in [`reading_practice.md`] can proceed in parallel and reuse the same checks.)

## 8. Effort / cost
Detectors 1–3 are mostly deterministic or single-pass (cheap). The full audit + back-translation over ~135k
pt-BR + ~107k en fields is the main spend — comparable to one translation tranche; do it field-class by
field-class, fixing as we go. License audit is a day of analysis + an owner decision.

## 9. Guardrails for GENERATED content — make even last-resort generation trustworthy
Generation is the last resort (selection-first, §2/§5), but when it must happen, NOTHING ships on the model's
word alone. Every generated item runs a fixed **generation gate**: it is only accepted if it passes the whole
battery; otherwise it is regenerated (bounded retries) or dropped and **escalated to human review** — never
auto-shipped on a failure. Failures and the "why selection wasn't possible" reason are logged.

### 9.0 Hard preconditions (before any model call)
- **Selection genuinely failed** — a tool confirms no real Tatoeba/JEC sentence fits the slot+known-set, and
  logs it. Generation without this log entry is rejected.
- **Deterministic fields are never generated** — readings, romaji, conjugation forms, tokenization, POS/
  `function_type` enums come from Sudachi/KANJIDIC/the conjugation rules, full stop. The model may only
  produce the *prose* (translation, explanation), never the facts.
- **Anchor to a real model** — generated JP must be a minimal, constrained variation grounded in a real
  attested sentence + the lesson's known set, not invented from zero.

### 9.1 Deterministic gate for generated JAPANESE (catches fabricated JP — the biggest risk)
Run on every generated JP string; any failure ⇒ reject:
1. **Parses cleanly** — Sudachi re-tokenizes with no unknown/`UNK` tokens.
2. **Every content word exists in JMdict** (no hallucinated vocab); **every kanji exists in KANJIDIC** (no
   invented characters).
3. **Readings are valid** — each kanji's Sudachi contextual reading is an attested KANJIDIC reading for that
   kanji (no invented furigana). Reuse `validate.py` §7.1/§7.2 machinery.
4. **Known-set gate** — every kanji/vocab ∈ the lesson's `cumulative_known_set` (§3); particles/grammar within
   the known set.
5. **Corpus-attestation (naturalness, deterministic)** — the sentence's key content-word **collocations /
   bigrams are attested in the real Tatoeba/JEC corpus** (FTS lookup). A collocation that appears *nowhere* in
   millions of real sentences is a naturalness red flag ⇒ reject or down-score. Grounds "sounds native" in
   real data, not vibes.

### 9.2 Adversarial + cross-model verification (catches what rules can't: nuance, naturalness, correctness)
- **Multi-vote, error-seeking** — N independent verifier agents are told to *find the mistake* (default to
  "reject if unsure"); accept only on consensus (e.g. ≥⌈2/3⌉ pass). Reuse/extend `tr_audit_workflow.js`.
- **Cross-model** — generate with one model, verify with a **different** model/prompt family, so verifier and
  generator don't share the same blind spot.
- **Perspective-diverse lenses** — separate checks for: grammatical correctness, particle correctness,
  naturalness/register (daily-life, no slang, not stiff), and meaning-vs-intended. A lens failing ⇒ reject.

### 9.3 Round-trip / back-translation consistency
- Generated JP → an **independent** agent translates JP→EN and JP→pt-BR → compare against the *intended*
  meaning and against each other. Divergence ⇒ the JP is ambiguous/wrong ⇒ reject.
- Generated translation → back-translate to the source language → compare to source (the §3.2 check), applied
  to generated items at 100% (not sampled).

### 9.4 Composite trust score, quarantine, and the review floor
- Each generated item gets a **trust score** = weighted pass-rate across 9.1–9.3. Below threshold ⇒ **never
  auto-ship**; route to the human-review queue. At/above ⇒ ship but still `ai_generated:true`,
  `needs_review:true`, lowest `confidence`, and **quarantine-tagged** (a reviewer/UI can filter to "AI-
  generated only" and it is never visually conflated with Layer-A real content).
- **Human-review floor:** a fixed % of passing generated items (and 100% of the borderline band) are sampled
  into the teacher queue regardless of score, so the automated gate is itself continuously audited.

### 9.5 Golden regression set (keep the pipeline honest over time)
- A small **human-verified golden set** (good + deliberately-bad JP/translation examples) that the gate must
  score correctly. Re-run on every prompt/model change so generation+validation can't silently regress; a drop
  in golden accuracy blocks a pipeline change.

### 9.6 New tools to build for this (concrete)
- `validate_generated_jp.py` — the §9.1 deterministic battery (parse + dict-exist + reading + known-set +
  corpus-attestation), reusing Sudachi + JMdict/KANJIDIC + the Tatoeba FTS index.
- `gen_gate_workflow.js` — orchestrates generate → 9.1 → cross-model multi-vote (9.2) → round-trip (9.3) →
  trust score (9.4); emits accepted / rejected / escalated with reasons.
- extend `tr_audit_workflow.js` with the error-seeking + perspective-diverse lenses (9.2).
- `golden_set.json` + `run_golden.py` (9.5).
- a `selection_failed.log` requirement enforced before generation (9.0).

**Net:** real text first; if generation is unavoidable, it must survive a deterministic JP-correctness battery,
corpus-grounded naturalness, cross-model adversarial verification, and round-trip consistency, carry a trust
score, stay quarantined + `needs_review`, and a slice always reaches a human. That is the most trustworthy a
generated item can be without a native author.
