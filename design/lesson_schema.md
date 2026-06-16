# Lesson rich-format schema — FROZEN v1 (P6)

> Machine-validatable freeze of [`lesson_format.md`](lesson_format.md) (owner directives 2026-06-14).
> `scripts/validate/validate_lessons.py` enforces THIS file. The design rationale/tone lives in
> `lesson_format.md`; this file is the exact contract. **`schema_version = "1.0"`** is stamped on every lesson.
> Refine → re-freeze → bump version (governance: lesson_format.md §0). Language-agnostic: element + attribute
> names and enum values are English/neutral; only rendered text is pt-BR ([`i18n.md`](i18n.md)).

## Serialization
- A lesson's `body` (DB `lesson.body_pt`, exported as `body`) is a **tagged HTML-like string**: a bare ordered
  sequence of **block** elements. No root wrapper (`<lesson>`/`<html>`/`<body>`). Parsed by our own renderer
  (Flutter), not a browser — simple tag names are fine.
- Lesson metadata (id/slug, level, topic, title, objectives, prerequisites, `schema_version`,
  `cumulative_known_set`) lives in the **lesson record**, never in the body tree.

## Lesson record metadata — needs / unlocks / SRS (see [`courseware_architecture.md`](courseware_architecture.md))
Beyond title/objectives, every lesson record carries:
- **`description`** — one-line pt-BR summary (shown in the topic index / required layer).
- **`needs`** — `[{type, ref, note?}]` prerequisites (`need_type` enum). Linearity: every ref must be unlocked by
  a strictly-earlier lesson (kana-bootstrap words excepted — kana-only deps; see [`kana.md`](kana.md)).
- **`unlocks`** — `[{type, ref}]` what this lesson FIRST teaches (`unlock_type` enum). Generalizes the old
  `lesson_introduces` (kanji/vocab/grammar) to also include `kana-family`, `conjugation-form`, `phrase`,
  `kanji-family`, `feature`, `srs-deck`. Introduce-once: each ref unlocked by exactly one lesson.
- **`feature_unlocks`** — `feat:*` app features turned on here (subset of `unlocks`, surfaced for the app).
- **`srs.introduces_cards`** — `[{deck, item, card_types}]` derived from `unlocks`: the cards enrolled into FSRS
  when this lesson is completed (deck created on its first card). See courseware_architecture.md §6.
The closed taxonomy is `design/unlock_enums.json` (`unlock_type` / `need_type` / `feature` / `card_type` / `deck`
/ `ref_namespace`). The four-tier manifest (manifest→course→topic→lesson) is the required-layer surface; this
record is the lesson leaf.

## Hard rules (validator-enforced)
1. **No bare text.** Raw non-whitespace character data may appear ONLY directly inside a *text-bearing leaf*:
   `text`, `jp`, `romaji`, `term`, `emphasis`. Everywhere else, text must be wrapped (whitespace/newlines
   between tags are insignificant). Parse fails otherwise.
2. **Whitelist only.** Unknown element OR unknown attribute → error.
3. **All `ref` ids resolve** to an existing corpus entity (no dangling refs). Namespaces below.
4. **Children rules.** Each element accepts only its declared child kinds (block / inline / specific).
5. **Learner text is pt-BR.** (`jp`/`ruby`/`romaji` content is Japanese/romaji; everything narrated is pt-BR.)
6. **Required structure.** Body is ≥1 block; the LAST block is a `<checklist>`. The lesson must have ≥1
   `recognition`-family (retrieval) exercise AND ≥1 `production`/`handwriting` exercise.

## `ref` id namespaces (rule 3)
> **Two ref surfaces, by design.** This table is the **lesson-BODY chip** surface (what `<sentence>`/`<kanji>`/
> `<vocab>`/`<grammar>` etc. can point at): a subset of the global namespaces **plus** the deferred asset
> prefixes. The **needs/unlocks METADATA** surface (record fields, not body) is the full closed taxonomy in
> [`unlock_enums.json`](unlock_enums.json) `ref_namespace` (adds `kana:` `conj:` `fam:` `feat:` `deck:` `les:`);
> see the metadata table below + [`courseware_architecture.md`](courseware_architecture.md) §4–5.

| prefix | resolves against | example |
|--------|------------------|---------|
| `sent:` | `sentence.slug` | `sent:tatoeba-124708` |
| `kanji:` | `kanji.character` | `kanji:食` |
| `vocab:` | `vocab.headword` (or numeric id) | `vocab:食べる` |
| `gram:` | `grammar_point.key` | `gram:te-kudasai` |
| `img:` `aud:` `vid:` | `asset.id` (registry) | `img:te-form-chart` |

**Metadata refs** (in `needs`/`unlocks`/`srs`, resolved by the loader/validator against the closed enum):
`kana:<script>-<row>`→`kana_family` · `conj:<form>`→conjugation form · `fam:<slug>`→kanji family ·
`feat:<key>`→`feature` registry · `deck:<key>`→`deck` registry · `les:<id>`→`lesson` (+ vocab/kanji/gram/sent
as above). Source of truth: `unlock_enums.json`.

> Audio/video/images are **deferred** (no asset registry yet). Using `img:`/`aud:`/`vid:` is allowed by the
> grammar but the validator emits a **warning** (not error) until the `asset` table exists. Lessons authored
> now should not depend on them.

## Block elements
| tag | attributes (all optional unless noted) | children |
|-----|----------------------------------------|----------|
| `heading` | `level` ∈ {1,2,3}; `speak` | inline |
| `p` | `align` ∈ {start,center,end}; `speak`; `narration` | inline |
| `note` | `type` ∈ {l1-advantage,l1-pitfall,culture,tip,warning,example} **(required)** | blocks or inline |
| `list` | `ordered` ∈ {true,false} | `item`+ |
| `item` | — | inline or blocks |
| `image` | `ref="img:…"` **(required)**; `width`; `height`; `align`; `caption`; `alt` | empty |
| `video` | `ref="vid:…"` **(required)**; `caption`; `poster` | empty |
| `audio` | `ref="aud:…"` **(required)**; `label`; `autoplay` ∈ {true,false} | empty |
| `sentence` | `ref="sent:…"` **(required)**; `show` ∈ {furigana,romaji,both,none}; `mode` ∈ {inline,card,featured}; `audio` ∈ {true,false} | empty |
| `stroke` | `ref="kanji:…"` **(required)**; `autoplay` ∈ {true,false} | empty |
| `exercise` | `ref="ex:…"` **(required)** — points at an `exercise` row | empty |
| `flashcard` | `ref="vocab:…\|kanji:…"` (optional) | `front`,`back` |
| `front` / `back` | — | inline or blocks |
| `checklist` | — | `check`+ |
| `check` | `item-ref` (optional `vocab:/kanji:/gram:`) | inline |
| `divider` | — | empty |

**No generic layout primitives** (`table`/`cell`/`columns`/fixed widths). A structured display gets a
purpose-built responsive component added only when a real lesson needs it (none in v1).

## Inline elements
| tag | attributes | text-bearing |
|-----|------------|:------------:|
| `text` | `weight` ∈ {normal,bold}; `italic` ∈ {true,false}; `underline` ∈ {true,false}; `color`; `size` ∈ {sm,md,lg}; `speak` ∈ {true,false} | ✅ |
| `jp` | `reading`; `pitch` | ✅ |
| `ruby` | `base` **(required)**; `reading` **(required)** | empty |
| `romaji` | — | ✅ |
| `term` | `define` **(required)** | ✅ |
| `emphasis` | — | ✅ |
| `kanji` | `ref="kanji:…"` **(required)**; `furigana` ∈ {true,false} | empty |
| `vocab` | `ref="vocab:…"` **(required)** | empty |
| `grammar` | `ref="gram:…"` **(required)** | empty |
| `audio` | `ref="aud:…"` **(required)**; `label` | empty (also usable inline) |
| `break` | — | empty |

Inline elements may appear only inside inline-accepting blocks/inlines. `kanji`/`vocab`/`grammar` chips render
as tappable modals pulling from the registries by id (rule: never embed content).

## Exercise records (`exercise` table; referenced from body by `ref="ex:…"`)
- `type` ∈ {recognition, cloze, particle_choice, sentence_build, reading, listening, production, handwriting,
  matching, ordering}. `prompt` (pt-BR), `explanation` (pt-BR), `answer` (typed JSON), sentence/item refs by id.
- **answer-key shapes** (validator checks the shape per type):
  - recognition / particle_choice / reading / listening: `{choices:[…], correct:"…"}` (`correct` ∈ `choices`)
  - cloze: `{text:"…", full:"…"}`
  - sentence_build / ordering: `{order:[…], text:"…"}`
  - production / handwriting: `{text:"…", accept:[…]?}`
  - matching: `{pairs:[[a,b],…]}`
- **Per lesson:** ≥1 retrieval (recognition/reading/listening/cloze/particle_choice/matching) AND ≥1 production
  (production/handwriting). (rule 6)

## Pedagogy shape (authoring guide; rubric-checked, not parser-checked)
hook/intro → clear "porquê" explanation with referenced examples (`<sentence>`/chips) → guided examples →
exercises (recognition → production) → `<checklist>` recap. Warm pt-BR tone; define each new `<term>` on first
use; `l1-advantage`/`l1-pitfall` notes where they help; introduce-once (every reconciled item enters in exactly
one lesson's `lesson_introduces` = its FSRS enrollment set).

## Validation (P7) — `validate_lessons.py`
Parses every lesson body and checks rules 1–6 + answer-key shapes + introduce-once + `lesson_introduces ⊆
topic.introduces` + every introduced item also referenced by ≥1 body/exercise sentence where applicable.
Emits errors (block) / warnings (deferred assets, soft pedagogy). Coverage (100% of reconciled items get an
introducing lesson) is checked by the P7 coverage audit.
