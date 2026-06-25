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
