# Rich lesson format — PLAN / draft spec (finalize in P6)

> Owner directives (2026-06-14): lessons are **always** in this rich, tagged format. **Hard rule: nothing is
> bare — every piece of content is wrapped in its own tag** (even plain text → `<text>`, bold → `<text
> weight="bold">`, an image → `<image>`, etc.). No `<html>`/`<body>` wrapper, but **zero untagged content**.
> This file is a **well-defined BASE**, *not* the final exhaustive list — P5/P6/P7 will analyze the real
> words/kanji/phrases/lessons and **refine the schema as needed** (see "Schema governance"). Lessons must be
> **nice, fun, direct, very self-explanatory (anyone can understand), and efficient but sufficient** (enough
> text + exercises to truly learn; the rest via SRS). A **voice play-mode** reads the lesson aloud;
> **AI-generated video** (narrator + slides) is a possible future, not MVP.

## 0. Schema governance (non-negotiable)
The element set below is a starting base; it evolves during authoring under these rules:
1. **One schema, all lessons.** Every lesson (pre-N5 → N5 → N4 → N3 …) conforms to the **same** versioned
   schema — no per-lesson or per-level variants. A renderer that supports the schema renders any lesson.
2. **Rigorously defined.** Each element and **each property** is documented: type, allowed values, required vs
   optional, default, and which children it accepts. The schema is machine-validatable (P7 enforces it).
3. **No dead properties.** Only properties that lessons **actually use** exist — prune anything unused. New
   needs found while authoring are *added deliberately* (and documented), never left as speculative cruft.
4. **Level-agnostic & complete.** It must contain everything needed to express any N5→N1 lesson (same
   future-proofing principle as the corpus schema, §1.6) — adding N3+ is new *content*, not a schema change.
5. **Refine → freeze → version.** Adjust freely during P6 as real content reveals needs; once stable, **freeze
   and version** it so every stored lesson states its `schema_version` and stays renderable.
>
> **Clean-room:** the local-course example was viewed only as a structural reference for the
> custom-elements idea — no content and no element names copied (§1.4). The vocabulary below is our own.
> **Status: plan.** Final element list/attributes are locked in P6; not implemented now.

## 1. Core model
- A lesson body is an **ordered tree of typed tags** parsed by **our own renderer** (the app is Flutter/Dart;
  this is *not* browser DOM, so simple tag names are fine and won't collide with HTML).
- **No text node may exist outside a tag.** Whitespace/newlines between tags are insignificant.
- Two element kinds: **block** (stack vertically) and **inline** (flow inside a block). Inline content is
  itself always tagged.
- Every element that points at corpus content/media does so by **stable ID** (`ref="sent:…|kanji:…|vocab:…|
  gram:…|img:…|aud:…|vid:…"`) — never embeds it. Edit the source once → every lesson updates.

## 2. Block elements
| Tag | Purpose | Key attributes | Children |
|-----|---------|----------------|----------|
| `<lesson>` | optional root wrapper | `id`, `level`, `topic` | blocks |
| `<heading>` | section title | `level="1|2|3"` | inline |
| `<p>` | paragraph | `align`, `speak` | inline |
| `<note>` | callout box | `type="vantagem-pt|armadilha-pt|cultura|dica|aviso|exemplo"` | blocks/inline |
| `<list>` | bullet/numbered list | `ordered="true|false"` | `<item>` |
| `<item>` | list entry | — | inline/blocks |
| `<table>` | grid (kana tables, contrasts) | `caption` | `<row>` |
| `<row>` | table row | — | `<cell>` |
| `<cell>` | table cell | `header="true|false"`, `align`, `colspan` | inline |
| `<image>` | picture/diagram | `ref="img:…"`, `width`, `height`, `align`, `caption`, `alt` | — |
| `<video>` | video | `ref="vid:…"`, `caption`, `poster` | — |
| `<audio>` | play control (also inline) | `ref="aud:…"`, `label`, `autoplay="false"` | — |
| `<sentence>` | a dissected phrase (interactive) | `ref="sent:…"`, `show="furigana|romaji|both|none"`, `mode="inline|card|featured"`, `audio="true"` | — |
| `<stroke>` | animated stroke order | `ref="kanji:…"`, `autoplay` | — |
| `<exercise>` | interactive, auto-gradable | `ref="ex:…"` or inline `type=…` (see §5) | (exercise-specific) |
| `<flashcard>` | reveal card | `ref="vocab:…|kanji:…"` (or custom) | `<front>`, `<back>` |
| `<checklist>` | can-do / "vitórias" recap | — | `<check>` |
| `<check>` | one checklist line | `item-ref` (optional) | inline |
| `<divider>` | visual separator | — | — |
| `<columns>` / `<column>` | side-by-side layout | `column: width` | blocks |
| `<callout-figure>` | image+caption combo | `ref`, `caption` | — |

## 3. Inline elements (only inside inline-accepting blocks)
| Tag | Purpose | Key attributes |
|-----|---------|----------------|
| `<text>` | the **only** way to write plain text | `weight="normal|bold"`, `italic="true"`, `underline="true"`, `color`, `size="sm|md|lg"`, `speak="true|false"` |
| `<jp>` | inline Japanese (correct font; optional reading) | `reading`, `pitch` |
| `<ruby>` | furigana | `base`, `reading` |
| `<romaji>` | romaji support text | — |
| `<term>` | glossary term (first-use highlight → modal) | `define` |
| `<kanji>` | kanji chip → hover/click modal | `ref="kanji:…"`, `furigana="true"` |
| `<vocab>` | vocab chip → modal | `ref="vocab:…"` |
| `<grammar>` | grammar chip → modal/expand | `ref="gram:…"` |
| `<audio>` | small inline play button | `ref="aud:…"` |
| `<break>` | line break | — |
| `<emphasis>` | semantic emphasis (vs visual `<text italic>`) | — |

## 4. Common attribute conventions
- `ref` — stable corpus/asset id (required on all reference elements; **P7 verifies it resolves**).
- `speak` — `true` (default for text/headings/p) | `false` to skip in voice mode (decorative content).
- `id` — optional local anchor for in-lesson links.
- Booleans are `"true"/"false"` strings; unknown attributes are rejected by the validator.

## 5. Exercise types (the `type` attribute / `exercise` table)
`recognition` · `cloze` · `particle_choice` · `sentence_build` · `reading` · `listening` · `production` ·
`handwriting` · `matching` · `ordering`. Each pulls its prompt, structured answer key, and referenced
sentences/items **by ID** from the `exercise` table; renders inline and auto-grades.

## 6. Voice play-mode (TTS)
- The renderer reads block elements in **document order**; `<text>`/`<heading>`/`<p>`/`<item>`/`<check>` are
  narrated; `<sentence>` plays its own (native or TTS) audio; `<image>`/`<video>` are skipped (use `alt`/
  `caption` if narration is wanted).
- `speak="false"` opts a block out; an optional `narration="…"` attribute can supply a cleaner spoken version
  of a visually-formatted block.
- This same ordered, narratable structure is what a future **AI video** (narrator voice + generated slides)
  would consume — so authoring for voice now keeps that door open (non-MVP).

## 7. Lesson pedagogy & UX (how lessons must *feel*)
- **Tone:** warm, encouraging, conversational pt-BR ("pequenas vitórias"); never dry.
- **Very explanatory:** assume zero prior knowledge; define every new term on first use (`<term>`); explain the
  *why*, not just the *what*. Anyone, ever, should be able to follow.
- **Direct & efficient, but sufficient:** no filler, but **not artificially short** — give enough explanation,
  worked examples, and exercises to genuinely learn the lesson; long-tail reinforcement is the SRS's job.
- **Shape (per `design/curriculum.md` ladder):** hook/intro → clear explanation with referenced examples →
  guided examples → exercises (recognition → production) → **can-do checklist** recap.
- **Dual coding:** images/diagrams and `<note>` callouts (💡 Vantagem PT / ⚠ Armadilha PT) where they help.
- **Engagement:** variety of blocks (sentences with modals, tappable kanji, inline audio, flashcards,
  exercises) so the page is interactive and fun, not a wall of text.

## 8. Validation (P7)
- **No bare text** — every text is inside a tag (parse fails otherwise).
- **Allowed elements + attributes only** (whitelist from §2–§5); unknown tag/attr → error.
- **All `ref` ids resolve** to existing corpus/asset entities (no dangling refs).
- Learner-facing text is **pt-BR**; required structure present (e.g. each lesson ends with a `<checklist>`).

## 9. Storage & export (P6)
- `lesson.body` stores the tagged tree (serialized). `.json` export = app-ready (tree + a resolved `refs`
  manifest for prefetch); `.md` export = flattened human-review view.
- `asset` registry table (`id`, `type` image/video/audio, `path`, `license`) — media referenced by id.

## 10. Deferred to P6 (decide then)
- Final, frozen element/attribute list + a formal validatable schema (e.g. a RelaxNG/JSON-schema-style spec).
- Canonical serialization: tagged-HTML-string vs typed block-tree JSON rendered to the tags (owner prefers
  HTML-like; a JSON tree may be the internal form, emitting the tags).
- Optional light didactic research on rich/interactive lesson design.
- Audio elements activate after the (deferred) audio-production pass; video/AI-slides are post-MVP.
