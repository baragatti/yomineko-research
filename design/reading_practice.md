# Reading-practice boxes — progressive in-lesson Japanese reading (PLAN, not yet executed)

> **Owner directive (2026-06-25):** progressively add Japanese reading text *into the lessons* as **extra,
> optional content** — a new boxed UI element holding a full Japanese passage + a button to reveal the
> translation below. **Pre-N5 unchanged.** N5 slowly gains a few short boxes; N4 has more; N3 has more still
> and ramps up from its midpoint. Each box must contain **only what the learner can already fully read** at
> that point (everything taught up to and including that lesson), is **related to the lesson but not required**
> (the learner never needs it to pass), is **additive** (nothing existing is removed), and **always carries a
> translation** to check against.
>
> This file is the design + rollout plan. **Nothing here is built yet.**

## 1. Why this works (pedagogy)

This is textbook **extensive reading (ER / 多読 tadoku)** and **comprehensible input**: fluency comes from
reading a LARGE volume of EASY text (at or slightly *below* current level, ~98% of words already known), for
pleasure, skipping the rare unknown — NOT from grinding short hard texts with a dictionary. Graded readers
start kana-dominant + short and raise kanji density and length as the learner advances. ([tofugu graded
readers](https://www.tofugu.com/japanese/japanese-graded-readers/) ·
[Tadoku/extensive reading](https://nihongoknow.com/tadoku-extensive-reading-japanese-tips/) ·
[comprehensible input science](https://katarineko.com/blog/learn-japanese-comprehensible-input-science)).
Furigana: keep it ON early to maximize reading volume, then make it optional/selective as kanji become
familiar (JLPT reading passages have none) ([furigana use](https://www.utterance.com/why-furigana-might-be-the-most-powerful-tool-for-learning-japanese-kanji/) ·
[hide-furigana toggle](https://www.renshuu.org/forums/topics/12696/A_little_button_to_hide_furigana_in_quizzes)).

**Design consequences:**
1. The box text must be **i+0** (fully known), not i+1 — the opposite of the sentence-bank selector's default.
   This is the single most important rule and it is **machine-enforceable** (see §3).
2. A **bilingual reveal** (JP first, button to show translation) turns each box into a tiny self-test:
   attempt → check. Good for retrieval, and it keeps the box "optional" (no pressure).
3. **Furigana ON by default early, with a toggle**; default off later. Length and kanji density ramp by level.

## 2. The new element

A new lesson-body block tag that references a stored reading passage by stable ID (consistent with §1.7 and
the existing `<sentence ref>` — lessons reference the corpus, never embed it):

```
<reading ref="read:n5-cafe-01" show="furigana"/>
```

Rendered (server-side → opaque HTML, the established no-leak pattern):

```
┌─ Leitura · conteúdo extra ──────────────────── [あ|A furigana toggle] ┐
│  毎朝、私はコーヒーを飲みます。今日は友だちと…        (JP, ruby furigana)  │
│                                                                        │
│  ▸ Mostrar tradução            ← native <details>, reveal-on-click     │
│  (revealed) Toda manhã eu tomo café. Hoje, com um amigo…   (pt-BR)     │
└────────────────────────────────────────────────────────────────────────┘
```

- Header badge makes clear it is **optional extra** ("conteúdo extra / não é cobrado").
- JP shown with furigana (ruby) by default; a small **furigana toggle** hides `<rt>` (client JS toggling a
  class, same delegation pattern as `CorpusRefLayer`).
- Translation hidden behind a **native `<details>`** ("Mostrar tradução") — reveal works with zero JS and is
  accessible; the pt-BR sits below when opened.
- Placement: near the end of the lesson body, after the teaching + before/around the checklist, as its own
  `<heading level="3">Leitura</heading>` + one or more `<reading>` boxes. Never inside the exercise/checklist
  flow (it is not graded).

## 3. The readability guarantee (the technical heart)

Every lesson already stores `cumulative_known_set = {kana-family, vocab, kanji, grammar, conjugation-form,
phrase}` — the union of everything unlocked up to and including it (`load_lessons.recompute_cumulative`). A
reading passage attached to lesson L is **valid only if**, after Sudachi dissection:

- **every kanji** in the passage ∈ `L.cumulative_known_set.kanji` (HARD gate), and
- **every content vocab** (the dissection's `vocab_ids`) ∈ `L.cumulative_known_set.vocab` (HARD gate), and
- **grammar** uses only patterns in `L.cumulative_known_set.grammar` (SOFT gate: prompt-constrained +
  human review — grammar isn't reliably detectable from raw text), and
- allowed-anyway: kana-only words, numbers, punctuation, and (flagged) proper nouns.

This is the **same machinery** as the sentence-bank i+1 selector (`prepare_n3_sentence_batch.py`: Sudachi
skeleton → `vocab_ids`/`kanji_ids` → count "new" vs known) but with **`max_new = 0`** instead of 3. A new
validator `scripts/validate/validate_readings.py` re-derives the skeleton and **rejects any passage with an
out-of-known-set kanji or vocab**, so "only stuff they can already fully read" is provably true, not assumed.

## 4. Data model

New corpus registry `corpus/readings/<level>.json` (regenerable from the DB like every other registry):

```json
{
  "slug": "read:n5-cafe-01",
  "level": "n5",
  "gated_to_lesson": "les:n5-rotina-04",      // its known-set is this lesson's cumulative set
  "theme_topic": "top:n5-rotina",             // related lesson topic (relevance, not requirement)
  "title": {"pt-BR": "No café", "en": "At the café"},
  "jp": "毎朝、私はコーヒーを飲みます。…",
  "tokens": [ { "surface","reading","romaji","vocab_id","kanji_ids" } ],   // for furigana + the gate
  "translation": {"pt-BR": "…", "en": "…"},
  "uses": { "vocab": [...], "kanji": [...], "grammar": [...] },             // resolved, for audit
  "length_band": "short|paragraph|long",
  "provenance": { "ai_generated": true, "needs_review": true, "tier": "reading",
                  "gate_verified": true, "locale": "pt-BR" }
}
```

- Lessons gain `reading_refs: ["read:…"]` (mirrors `sentence_refs`) + `<reading ref>` in the body.
- **i18n / English-preservation**: `title` and `translation` are locale-objects `{pt-BR, en}` (the `en`
  preserved per [`i18n.md`](i18n.md); generated bilingual from the start so we don't backfill later).
- **No-leak**: the box ships rendered JP + the pt-BR translation (hidden until revealed) — both are content the
  learner is meant to see, exactly like exercise answers. The `en`, the token stream, and the structured
  registry stay **server-side** (the prototype ships only the rendered box + the pt-BR reveal). Re-verify with
  the existing client-bundle grep.

## 5. Sourcing — GROUND IN REAL TEXT FIRST; generate only as a last resort

> **⚑ RESEARCH + IMPLEMENTATION NOTE (owner directive 2026-06-25).** Japanese is hard and AI **fabricates
> subtly-wrong Japanese** when it writes from zero (wrong particle nuance, unnatural collocations, a kanji
> reading that doesn't fit, register slips). So these reading passages must be **grounded in real, openly-
> licensed, human-written Japanese that comes WITH a trusted human English translation**, as much as possible.
> The trusted English is doubly useful: (a) it tells us the *correct* meaning to base the pt-BR on, and (b) it
> lets us **cross-check** that our pt-BR actually matches (and flags a bad JP→meaning reading). Pure
> generation is the **last resort**, only to fill a slot no real text can, and then with the heaviest review.
> This is just spec §1.2 ("prefer SELECTION over GENERATION") applied to reading.

**Source priority (highest trust first):**

1. **Our existing dissected bank (best).** The 5,565-sentence bank is already built from **Tatoeba (CC BY)** +
   **JEC Basic Sentences (CC BY 3.0)** — real human Japanese, each with a **human English** translation, plus
   our pt-BR, full dissection, level tag, and known-set linkage. Select the i+0 sentences for a lesson
   (`max_new = 0` against its `cumulative_known_set`) and assemble 1–N into a short themed passage. This is the
   most trustworthy path: real JP, trusted EN, already-verified pt-BR, furigana from Layer-A readings.
2. **More raw Tatoeba / JEC (same provenance)** not yet in the bank — dissect, gate to known-set, keep the
   human EN, derive + cross-checked pt-BR. CC BY / CC BY 3.0, commercial-OK with attribution.
3. **Open graded readers — INVESTIGATE in Phase 0, use only if the license truly permits bundling.** Genuine
   graded *passages* (cohesive, level-controlled) would be ideal for longer N3 boxes. Candidates to vet:
   読み物いっぱい ("copyright-free" beginner/intermediate books), NPO 多読 Tadoku readers, KC よむよむ (Japan
   Foundation). **Caution:** "free to read / download" ≠ CC-redistributable — verify each license before any
   use; most are *not* bundleable. KFTT (Kyoto-Wikipedia, CC BY) is parallel ja-en but **encyclopedic
   register** (already rejected for our use). Anything non-commercial / murky (JESC, OpenSubtitles, JParaCrawl)
   stays rejected (see `design/sources.md` / `ATTRIBUTION.md`).
4. **Generation — LAST RESORT only.** When no real sentence fits a needed slot, generate a *minimal* passage
   anchored to a real model sentence, constrained to the known-set, `ai_generated:true` + `needs_review:true`,
   machine-gated (§3) **and** flagged for native-level human review (it has no trusted EN to anchor, so it is
   the riskiest content in the corpus). Keep these rare and visibly marked.

**Cohesion vs. trust — an honest trade-off.** Real bank sentences are independent, so a passage stitched from
them reads as a *themed set of true sentences*, not a flowing story. We accept slightly less narrative flow in
exchange for trustworthy Japanese, and avoid AI "connective glue" except minimal known-grammar connectors
(それから, でも…) drawn from the learner's known set, clearly bounded. Flowing narratives wait on a
license-cleared graded-reader source (item 3) rather than on generation.

### 5b. Trusted-English cross-check (the QA the owner asked for)

Every real source sentence carries a human EN translation. Use it as the anchor:
- **Base** the pt-BR on the JP, cross-referenced against the trusted EN (not on the EN alone — pt-BR is from
  the Japanese, EN is the sanity rail).
- **Verify** with a `pt-BR ↔ EN consistency` check (the `tr_audit_*` tooling already does exactly this): if the
  pt-BR and the trusted EN diverge in meaning, flag it — usually a pt-BR error, occasionally a bad JP→EN that
  disqualifies the sentence. Only sentences that **pass** the cross-check are eligible for a reading box.
- **Bonus, runnable now:** because the whole bank is already bilingual (pt-BR + en), this same pt↔en check can
  be run over the entire sentence bank as a standalone QA pass — it both raises bank quality and pre-qualifies
  the pool of reading-ready sentences. (The §"sanity check" audits were a lightweight version of this.)

Furigana always comes from the dissection's Layer-A readings (reliable), never invented.

## 6. Progressive density schedule (the ramp the owner asked for)

Counts are targets, not hard rules; the generator skips a lesson if its known-set can't yet support a natural
passage. "Boxes/lesson" is approximate.

| Level | When it starts | Boxes/lesson | Length | Furigana | Content gate |
|---|---|---|---|---|---|
| **pre-N5** (41 lessons) | — | **0 (unchanged)** | — | — | — |
| **N5** (81) | only after kana done + a base of vocab (≈ topic 5 on); 0 before | 0 → ~0.5 → ~1 by the last topics | 1–3 sentences | **ON** (toggle present) | N5-so-far vocab + kanji |
| **N4** (91) | from lesson 1 (full N5 known) | ~1 (a few with 2) | short paragraph / mini-dialogue (3–6 sentences) | toggle, default **on for newest kanji only** | N5 + N4-so-far |
| **N3** (101) | from lesson 1 | first half ~1; **from the midpoint (≈ topic 8/15) on: 1–2** | paragraph → multi-paragraph / longer dialogue | toggle, default **off** | N4 + N3-so-far |

Net ≈ 250–280 passages. Across all four levels the difficulty curve is: none → short+furigana → paragraphs →
multi-paragraph with furigana off — i.e. graded-reader progression, always inside the learner's known-set.

## 7. Pipeline (reuses existing infrastructure)

1. `build_reading_inputs.py` — per eligible lesson: pull `cumulative_known_set` (vocab/kanji/grammar) + theme
   + target length/density from §6; emit authoring inputs. (Mirrors `build_n3_lesson_inputs.py`.)
2. **Generation workflow** (one agent per N lessons, like the dissection/lesson workflows) — produce
   passage(s) + pt-BR + en, strictly inside the supplied known-set, themed to the lesson.
3. **Dissect + gate** — run the Sudachi skeleton; attach readings (furigana); **`validate_readings.py` rejects
   any passage with out-of-known-set kanji/vocab** → regenerate the rejects (loop until clean) or drop.
4. **Persist** to the readings registry; wire `<reading ref>` + `reading_refs` into the lesson (additive — the
   existing body is untouched; the box is appended under a new "Leitura" heading).
5. Export (`export_corpus` adds `export_readings()`; `export_course` resolves `read:` refs like `sent:`),
   re-sync prototype, build, **no-leak check**, validate, commit, copy-back, push — the standard loop.

## 8. Validators & schema touch-points (small, well-scoped)

- `validate_lessons.py`: add `reading` to the tag whitelist (block element; attrs `ref` (req) + `show`;
  self-closing) and `reading.ref → {read}` to `REF_NS`. The "ends with checklist" rule still holds (the
  reading section sits before it).
- `validate_readings.py` (NEW): the readability gate (§3) + hygiene (no emoji/em-dash, accents kept) +
  translation present (pt+en) + `needs_review:true`.
- `audit_export_refs.py`: resolve `read:` refs in exported bodies.
- `audit_coverage` / `validate.py`: unaffected (readings aren't "introduced" items — they unlock nothing).

## 9. Renderer & UI (prototype)

- `render-body.server.ts`: add `case "reading"` → `renderReading(ref, readingById)` producing the box: title,
  ruby-furigana JP (reuse the existing `ruby()` helper), a furigana-toggle button, and a `<details>` holding
  the pt-BR translation. Pass a `readingData` map into the lesson route (like `refData`).
- Furigana toggle: one small client handler (extend `CorpusRefLayer` delegation) toggling a `furigana-off`
  class that hides `rt`. Per-box or a single lesson-level toggle.
- CSS: a `.ym-reading` card style (distinct, "extra/optional" look) consistent with the note/sentence cards.
- Mobile: box is full-width; furigana wraps; `<details>` reveal works touch-first.

## 10. Phased rollout (each phase = generate → gate → human-review → export → build → no-leak → commit)

- **Phase 0 — plumbing + proof:** schema, tag, renderer, CSS, `validate_readings`, and **one hand-authored
  box** in a late-N5 lesson, end-to-end (proves the box, the gate, the reveal, the furigana toggle, no-leak).
- **Phase 1 — N5 (light):** generate per §6, gate, review a sample, ship.
- **Phase 2 — N4.**
- **Phase 3 — N3** (with the mid-level ramp).

Each phase is independently shippable and reviewable; pre-N5 is never touched.

## 11. Risks & open questions

- **AI fabricating subtly-wrong Japanese** (the owner's central concern) → mitigated *primarily by grounding*
  in real, human-written, human-translated text (§5), and *secondarily* by the hard known-set gate (§3) +
  the pt↔en cross-check (§5b). Generation is the rare last resort, native-reviewed.
- **Readability drift outside the known-set** → fully caught by the hard `validate_readings` gate (reject +
  regenerate/drop) — the safety net that makes "only what they can read" a guarantee.
- **Grammar gate is soft** (prompt + review), unlike the kanji/vocab hard gate — acceptable since unknown
  grammar in otherwise-known words is still decodable, and everything is `needs_review`.
- **Genuinely easy vs. cramming** — keep `max_new = 0`; the box is for *consolidation*, not new material.
- **Tone/quality** — run the `humanizer` pass on the pt-BR; passages should read like natural mini-texts
  (a note, a diary line, a short dialogue), not exercise sentences.
- **Volume/cost** — ~250–280 passages ≈ one sentence-bank-tranche of effort; do it per-level.
- **§1.2 posture** — grounding-first (real Tatoeba/JEC text with trusted EN) is the rule; generation is the
  documented last resort, always known-set-gated + cross-checked + flagged. Fully consistent with §1.2.

## 12. Open choice for the owner
- **Tag holds a ref (recommended, above)** vs. **inline content** (`<reading><jp>…</jp><pt>…</pt></reading>`).
  Ref keeps it reusable, centrally gate-validatable, bilingual, and furigana-capable; inline is simpler but
  duplicates content and weakens the readability audit. Plan assumes the ref model.
- Audio narration of passages (play-mode) is a natural later add-on, out of scope here.
