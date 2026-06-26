# License audit — ShareAlike exposure & the permissive/SA split (2026-06-26)

> **Owner ask:** "Audit stuff. As far as I know we don't have SA stuff (we only use it to check our stuff)."
> **Short answer:** Half right. The **sentence layer is SA-free**. The **dictionary-derived linguistic layer is
> NOT** — our kanji meanings are *verbatim KANJIDIC2* and vocab glosses come from *JMdict*, both **CC BY-SA**.
> This is the normal, low-risk way these sources are used; it is fully contained by the two-layer architecture +
> attribution. It does **not** contaminate the courseware. Two owner decisions at the bottom.
> _License interpretation is the owner's call (per `sources.md`); this lays out the facts to decide on._

## What I checked
- `ATTRIBUTION.md`, `design/sources.md`, `research/datasets/*` (KanjiVG + kradfile present).
- Empirically inspected the **shipped** data in `db/corpus.sqlite` / `corpus/*.json` to see whether each field is
  a non-copyrightable **fact** or copied **expression**.

## The two-axis test
Copyright protects **expression**, not **facts**. So for each shipped field:
1. **Fact** (reading, stroke count, radical, frequency, Unicode, JLPT level, which parts a kanji contains) →
   no copyright, **no license obligation**, safe from any source incl. SA.
2. **Expression** (a written English gloss, a curated definition, an SVG drawing, prose) → copyrightable; if it
   was copied/translated from a **CC BY-SA** source it is an **adaptation** and inherits **ShareAlike**.

## Per-source license (condensed from `sources.md`)
| Source | Feeds | License | ShareAlike? |
|---|---|---|---|
| Tatoeba | example sentences (ja) | CC BY 2.0 FR | **No** |
| JEC Basic | example sentences (ja+en) | CC BY 3.0 | **No** |
| JMdict (EDRDG) | vocab glosses, readings, POS | CC BY-SA 4.0 | **Yes** |
| KANJIDIC2 (EDRDG) | kanji meanings, readings | CC BY-SA 4.0 | **Yes** |
| KRADFILE/RADKFILE (EDRDG) | radical decomposition / components | CC BY-SA 4.0 | **Yes** |
| KanjiVG | stroke order + component grouping | CC BY-SA 3.0 | **Yes** |
| kanjium | pitch accent (mora index) | CC BY-SA 4.0 | **Yes** |
| JLPT level lists | consensus level tags | mostly MIT (+ kanjiapi.dev BY-SA) | levels are facts |

## Per-shipped-field verdict (the actual exposure)
| Shipped field | Origin | Fact / expression | SA-bound? |
|---|---|---|---|
| kanji **readings** (音/訓), **stroke count**, **radical**, **grade**, **freq**, **Unicode** | KANJIDIC2 | fact | **No** |
| kanji **`meanings_en`** | KANJIDIC2 — **verbatim** (e.g. 日 = "day, sun, Japan, counter for days") | expression | **Yes** |
| kanji **`meanings_pt`** | translation of the KANJIDIC English | adaptation | **Yes** |
| vocab **`gloss_en`** | JMdict English glosses | expression | **Yes** |
| vocab **`gloss_pt`** | translation of the JMdict English | adaptation | **Yes** |
| kanji **`components`** / radical decomposition | KRADFILE / KanjiVG `kvg:element` | curated dataset | **Yes (treat as)** |
| **`kanjivg_ref`** (an id number) | KanjiVG | fact (a pointer) | **No** |
| **pitch accent** (mora index) | kanjium | fact-ish, curated dataset | **Yes (treat as)** |
| **stroke-order paths** (the proposed new feature) | KanjiVG SVG | creative drawing | **Yes** |
| **example sentences** (ja) | Tatoeba / JEC | — | No (CC BY) |
| **sentence pt-BR translations** | our own, from CC BY ja+en | our expression | No (our work) |
| **lessons, topics, exercises, sequencing, dissection prose** | **authored by us** | our expression | **No — proprietary** |

**Bottom line:** SA touches a **narrow, well-isolated set of fields** — the dictionary *definitions* + the
*decomposition / pitch / stroke* data. Everything that is genuinely *our product* (the course, exercises,
sequencing, all the pedagogical pt-BR prose, the sentence translations) is **not** SA-bound.

## Why SA does NOT contaminate the courseware (the key nuance)
CC BY-SA's ShareAlike binds **adaptations** of the licensed work — not a **Collection** that merely *aggregates*
it (CC BY-SA 4.0 §1: "Adapted Material" vs "Collection"). Our lessons **reference** dictionary entries by stable
ID; they are not adaptations of the dictionary. So:
- The **corpus registry meaning/gloss/decomposition/pitch/stroke fields** = CC BY-SA, attributed, kept shareable.
- The **courseware layer** (`course/`, lessons, exercises, sequencing, UI, our prose) = **your proprietary
  product**, sold normally.
This is exactly what the two-layer architecture (`corpus/` vs `course/`) already separates — the split is
**structural, not just legal**, which is what makes it clean.

## Required attribution (must be wired into the app)
A single in-app **credits/licenses screen** (and the data files' headers) carrying:
- EDRDG: *"This product uses the JMdict, KANJIDIC2 and KRADFILE/RADKFILE dictionary files… used in conformance
  with the Group's licence."* (https://www.edrdg.org/edrdg/licence.html)
- KanjiVG: *"Stroke order data from the KanjiVG project © Ulrich Apel, CC BY-SA 3.0."*
- kanjium: *"Pitch-accent data from the kanjium project, CC BY-SA 4.0."*
- Tatoeba (CC BY 2.0 FR) + JEC Basic (Kurohashi-Kawahara Lab / NICT MASTAR, CC BY 3.0).
> **Status: NOT yet present in the prototype.** Action item — add a `/creditos` route. (Tracked below.)

## Kanji stroke-order drawings (the new request) — license analysis
You want KanjiVG-style per-kanji stroke order + shared components. The data is already vendored
(`research/datasets/kanjivg/`), and the schema already has `kanjivg_ref` + `components`.
- **KanjiVG is the standard and best source for *Japanese* stroke order** (Chinese-oriented sets like Make Me a
  Hanzi / Hanzi Writer differ in stroke forms/counts for many kanji and carry their own copyleft via Arphic).
- It is **CC BY-SA 3.0**. Shipping the stroke paths = shipping an SA dataset → must be **attributed + that
  layer kept shareable**. It sits in the **corpus (SA) layer**, same as meanings — so it does **not** force the
  courseware open. This is how jisho.org, Tangorin, Tagaini Jisho, etc. ship it.
- A fully-permissive stroke source for Japanese does **not** meaningfully exist; insisting on permissive-only
  would mean **no stroke-order feature** (or hand-drawing 5,000+ kanji — infeasible).

## OWNER RULING (2026-06-26)
- **D-LIC-1 — REJECT the SA split. Go fully permissive.** Owner: *"Anything that could make me make the app
  'free' or that could be a legal threat should be re-authored. If it's not copyrightable we use it and give
  credits, just like CC BY."* → Policy:
  - **Facts** (readings 音/訓, stroke count, radical, grade, freq, Unicode, JLPT level, kanjivg_ref id) — **keep
    + credit** the source (attribution screen). No copyleft attaches to facts.
  - **Copyrightable SA expression** (kanji `meanings` verbatim from KANJIDIC2; vocab `gloss` from JMdict; any
    SA-curated compilation) — **RE-AUTHOR independently** so our text is our own work, not a derivative of an
    SA dictionary. Short factual overlaps ("water" for 水) are fine (merger/facts); what we remove is the copied
    *selection + wording + ordering* of the SA source. The re-authored content must pass the §9 guardrails.
  - **Net:** corpus becomes fully proprietary-safe; SA sources survive only as *fact* inputs + credits.
- **D-LIC-2 — RESOLVED by research (2026-06-26).** Permissive (no-SA, commercial-OK) winners found:
  - **STROKE ORDER → Kanji Alive (CC BY 4.0)** — native-hand-drawn, Japanese-correct, ships per-stroke SVGs +
    timing; **1,235 kanji** (covers ~all N5–N2 + top ~240 N1). Attribution-only, NO ShareAlike. (Radicals font
    = Apache 2.0, also permissive.) The N1 tail (~900 rarer kanji) → derive from **GlyphWiki** (permissive) or
    defer. REJECTED: KanjiVG (CC BY-SA), animCJK + Make-Me-a-Hanzi (Arphic Public License = copyleft/SA on the
    glyph data; reshaping outlines into stroke paths triggers its share-alike; MMH is also PRC stroke forms).
  - **DECOMPOSITION → GlyphWiki (public-domain-like: free commercial use, redistribute even after modification,
    NO SA, NO attribution) for full component breakdown + Unicode Unihan `kRSUnicode` (Unicode License v3,
    MIT-style, no SA) for the canonical radical.** REPLACES the CC BY-SA KRADFILE/KanjiVG components currently
    used. REJECTED: cjkvi-ids/CHISE (GPLv2 strong copyleft), KRADFILE (CC BY-SA).
  - **Net:** both layers can be fully permissive — no CC BY-SA anywhere. Engineering caveat: GlyphWiki gives
    glyph/component compositions (KAGE), not pre-ordered per-stroke animations, so the stroke-order *tail* needs
    extraction work; Kanji Alive is drop-in for its 1,235.

## Action items
1. [done] License audit + owner ruling (this doc).
2. [in-progress] Research permissive stroke-order + decomposition sources (deep-research) → pick for D-LIC-2.
3. [todo] **Re-author** kanji `meanings` + vocab `gloss` (en + pt-BR) independently of KANJIDIC2/JMdict
   expression, guarded by §9, to remove SA dependence (D-LIC-1).
4. [done — radical] **Radical re-sourced to permissive Unicode Unihan `kRSUnicode`** (Unicode License; 2026-06-26,
   `unihan_radical.py`), with the radical's CJK char derived via NFKD — replaces reliance on CC BY-SA KRADFILE
   for the radical. The multi-component **decomposition** (`kanji_component`) is kept as uncopyrightable FACT
   (which parts a character contains), credited to EDRDG — ShareAlike does not bind facts (owner ruling). A
   fully-independent component set (GlyphWiki/IDS, permissive) is an OPTIONAL enhancement (STATE backlog). Pitch
   (kanjium, CC BY-SA): mora-index is fact; keep + credit, or re-source — still TODO.
5. [todo] Add an in-app **credits/licenses screen** (facts kept under attribution: EDRDG/KanjiVG-as-fact/
   kanjium/Tatoeba/JEC).
6. [todo] Extract per-kanji **stroke order + components** from the chosen permissive source into the corpus.
7. [build] **§9 generation guardrails** (`validate_generated_jp.py` + gen-gate + golden set) — prerequisite for
   trustworthy re-authoring; building now.
