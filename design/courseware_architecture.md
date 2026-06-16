# Courseware architecture — the entry→course→topic→lesson model, unlocks, and FSRS (P6)

> Owner directives (2026-06-16). This is the master "explains everything" doc for the COURSEWARE layer: the
> layered manifest hierarchy the app loads, the per-lesson **needs/unlocks** metadata, the global
> **unlock/feature/need enums**, the **FSRS deck + card** model, and lesson **length/structure** targets.
> Companion docs: lesson body format = [`lesson_schema.md`](lesson_schema.md) (frozen v1); kana plan =
> [`kana.md`](kana.md); authoring rules = [`p6_authoring_spec.md`](p6_authoring_spec.md); sequencing =
> [`curriculum.md`](curriculum.md). Internals are language-neutral English; learner text is pt-BR
> ([`i18n.md`](i18n.md)). **Design references** (inspiration, re-expressed in our own model — no content copied):
> WaniKani levels/unlocks, Bunpro paths, Anki/FSRS scheduling, Duolingo skill tree, xAPI/cmi5 + Common
> Cartridge manifests. Web research was attempted (2026-06-16) but unavailable; this encodes established
> best-practice patterns as decisions, to be revisited if sources are later gathered.

## 1. Two-layer recap + where this fits
- **Corpus layer** (`corpus/`): reusable registries (kanji/vocab/grammar/kana) + the dissected sentence bank +
  families, addressed by stable id. Built/validated already.
- **Courseware layer** (`course/`): the linear Module→Topic→Lesson course. It **references corpus by id and
  never embeds it**. This doc defines its file/manifest shape and the unlock/SRS metadata.

## 2. The layered manifest hierarchy ("required layer first")
The app must build the whole course tree + the unlock/dependency graph **without** loading heavy lesson bodies.
So each level carries only the light "required layer" (ids, titles, order, needs, unlocks, paths); the lesson
**content** (rich body + exercises) lives in leaf files and is lazy-loaded. Four tiers:

```
course/manifest.json                         ← ENTRY (root). The minimal map of the whole product.
course/<level>/course.json                   ← COURSE index (one per module: pre-n5 / n5 / n4)
course/<level>/topic-NN-<slug>/topic.json    ← TOPIC index (metadata + ordered lesson stubs)
course/<level>/topic-NN-<slug>/lesson-NN.json← LESSON (full: metadata + needs/unlocks + tagged body + exercises)
course/<level>/topic-NN-<slug>/lesson-NN.md  ← LESSON (flattened human-review view)
```

### 2.1 `manifest.json` (entry / required layer)
```json
{
  "schema_version": "1.0",
  "generated": "<date>",
  "courses": [
    {"id": "mod:pre-n5", "level": "pre-n5", "order": 1, "title": {"pt-BR": "Fundamentos"},
     "path": "pre-n5/course.json", "topic_count": 6, "lesson_count": 0}
  ],
  "enums_ref": "design/courseware_architecture.md#5-global-enums"
}
```
Only what a launcher needs: the ordered course list + where to find each course index. Counts let the UI show
progress without loading deeper.

### 2.2 `course.json` (course / module index)
```json
{
  "id": "mod:n5", "level": "n5", "order": 2, "title": {"pt-BR": "N5"},
  "overview": {"pt-BR": "…"},
  "topics": [
    {"id": "top:n5-desu-wa", "order": 7, "title": {"pt-BR": "Frases básicas…"}, "theme": "identificação",
     "path": "topic-07-desu-wa/topic.json", "lesson_count": 4,
     "unlocks_summary": {"grammar": 12, "vocab": 60, "kanji": 0}}
  ]
}
```

### 2.3 `topic.json` (topic index)
Topic metadata + **lesson stubs** (the required layer for each lesson — enough to render the tree, gate, and
build the unlock graph, WITHOUT the body):
```json
{
  "id": "top:n5-te-form", "order": 15, "level": "n5", "title": {"pt-BR": "A forma て e seus usos"},
  "theme": "conectar ações", "objectives": [{"pt-BR": "…"}],
  "lessons": [
    {"id": "les:n5-te-form-01", "order": 1, "title": {"pt-BR": "Pedidos educados…"},
     "description": {"pt-BR": "Forma a forma て e faz pedidos com てください."},
     "path": "lesson-01.json",
     "needs":   [{"type": "grammar", "ref": "gram:te-form-prereqs…"}, {"type": "lesson", "ref": "les:…"}],
     "unlocks": [{"type": "grammar", "ref": "gram:te-form"}, {"type": "grammar", "ref": "gram:te-kudasai"},
                 {"type": "vocab", "ref": "vocab:乗る"}, {"type": "feature", "ref": "feat:conjugation-drill"},
                 {"type": "srs-deck", "ref": "deck:grammar-n5"}]}
  ]
}
```

### 2.4 `lesson-NN.json` (leaf — full content)
The existing lesson export (`export_course.py`) plus the new metadata block:
```json
{
  "id": "les:n5-te-form-01", "schema_version": "1.0", "level": "n5", "topic": "top:n5-te-form", "order": 1,
  "title": {"pt-BR": "…"}, "description": {"pt-BR": "…"}, "objectives": [{"pt-BR": "…"}],
  "needs": [...], "unlocks": [...], "feature_unlocks": ["feat:…"],
  "cumulative_known_set": {"grammar": [...], "vocab": [...], "kanji": [...], "kana_family": [...]},
  "sentence_refs": ["sent:…"], "body": "<heading>…</heading>…", "exercises": [...],
  "srs": {"introduces_cards": [{"deck": "deck:grammar-n5", "item": "gram:te-kudasai", "card_types": ["recognition","production"]}]},
  "needs_review": true
}
```
> The DB stays the build source; `export_course.py` emits all four tiers. `manifest.json`/`course.json`/
> `topic.json` are the **required layer**; lesson files are lazy. A from-scratch app only needs `manifest.json`
> to start.

## 3. Linearity + the dependency/unlock DAG
- **Hard rule (curriculum.md §2):** a lesson may only use items already unlocked by an EARLIER lesson (its
  `cumulative_known_set`). Nothing is taught before its prerequisite. The course is a linear sequence, but the
  **unlock graph is a DAG** (a later lesson may depend on several earlier ones).
- **`needs`** = the explicit prerequisite edges. Most are auto-satisfied by linear order (everything in
  `cumulative_known_set` is available); we record `needs` explicitly for: (a) cross-strand deps (a kanji lesson
  needs the kana to render furigana; a grammar lesson needs a form taught in another strand), (b) feature gates.
  P7 verifies every `needs` ref is unlocked by some strictly-earlier lesson.
- **Kana bootstrap exception (owner):** the **first kana lessons** may introduce a few very simple whole WORDS
  (no sentences, no grammar) purely to seed the first SRS reviews — e.g. after the あ/か families, the learner
  can already review あお (azul), かお (rosto). These words `need` only the kana families already taught. This is
  the ONLY allowed "content ahead of grammar," and it is words-only (see [`kana.md`](kana.md)).
- **`unlocks`** = what completing the lesson makes available (introduce-once: each item is unlocked by exactly
  ONE lesson; later lessons reuse by reference). `unlocks` drives FSRS enrollment (§6).
- _External validation (recovered research): the `needs`/`unlocks` split mirrors **LRMI's Require/Teach/Assess**
  competency model, and the manifest layering mirrors **IMS Common Cartridge**; the linear-sequence-over-DAG
  matches the curriculum-prerequisite-graph literature + Duolingo's 2022 pivot from a branching tree to a linear
  path. See `research/deep-research-courseware.md`._

## 4. Lesson `needs` / `unlocks` shape
Both are arrays of `{type, ref, note?}` where `type` ∈ the **unlock/need enums** (§5) and `ref` is the stable id
of the target (`kana:…`, `vocab:…`, `kanji:…`, `gram:…`, `sent:…`, `conj:…`, `fam:…`, `feat:…`, `deck:…`,
`les:…`). `unlocks` is the generalization of the current `lesson_introduces` table (widened `member_type`).

## 5. Global enums (machine-readable mirror: `design/unlock_enums.json`)
**`unlock_type`** — what a lesson can unlock (and, mirrored, what a `need` can require):
| value | ref namespace | meaning |
|-------|---------------|---------|
| `kana-family` | `kana:hiragana-sa` … | a syllabary family (5-ish kana) becomes known + reviewable |
| `vocab` | `vocab:<headword>` | a vocabulary item |
| `kanji` | `kanji:<char>` | a kanji (reading/meaning/writing) |
| `grammar` | `gram:<key>` | a grammar point |
| `conjugation-form` | `conj:<form>` (te-form, masu, nai, ta, potential…) | a drillable inflection form |
| `phrase` | `sent:<slug>` | a model dissected sentence made a study item |
| `kanji-family` | `fam:<slug>` | a kanji component family |
| `feature` | `feat:<key>` | an app feature (below) |
| `srs-deck` | `deck:<key>` | an FSRS deck becomes available (created on its first card) |

> SRS **cards are NOT an unlock type** — a lesson's cards are *derived* from its item unlocks
> (`srs.introduces_cards`, §6). There is no `card:` ref; `card_type` (the per-skill kinds) lives in the enum only.
> The `kana:` namespace holds BOTH family ids `kana:<script>-<row>` (the `kana-family` unlock target) and
> per-glyph ids `kana:<script>-<char>` (members of a family, **not** independently unlockable).

**`feature`** — app capabilities unlocked progressively (gated behind the lesson that first needs them):
`feat:srs-reviews` · `feat:kana-input` · `feat:furigana-toggle` · `feat:romaji-toggle` · `feat:kanji-lookup` ·
`feat:handwriting-input` · `feat:conjugation-drill` · `feat:particle-drill` · `feat:phrase-builder` ·
`feat:listening` · `feat:voice-mode` · `feat:jlpt-sim-n5` · `feat:jlpt-sim-n4` · `feat:find-correct-kanji` ·
`feat:find-correct-particle` · `feat:visual-novel`. (Each feature corresponds to a product-vision capability in
[`product_roadmap.md`](product_roadmap.md) — some roadmap deliverable rows bundle several features — and turns
on at the first lesson that uses it.)

**`need_type`** = `unlock_type` **minus** `srs-deck`, **plus** `lesson` (`les:<id>`). You depend on
items / features / prior-lessons, never on a deck.

> The enum is **closed + versioned**: adding a value is a deliberate, documented change (like the corpus
> schema). The validator rejects unknown `type`/`feature`/`ref`-namespace values.

## 6. FSRS decks + cards (data-only; the app runs the scheduler)
Spec §0 keeps SRS *logic* out of this corpus run, but the data contract must make enrollment trivial.

- **Decks separated by SKILL TYPE** (so the app can tune new-cards/day + parameters per skill, and so review
  load is legible): `deck:kana-hiragana`, `deck:kana-katakana`, `deck:vocab-n5`, `deck:vocab-n4`,
  `deck:kanji-n5`, `deck:kanji-n4`, `deck:grammar-n5`, `deck:grammar-n4`, `deck:phrases` (sentence/listening).
  (Level-splitting vocab/kanji/grammar lets N4 start a fresh pace.) A `deck` registry lists id, title, skill,
  level, and default FSRS knobs. **Defaults (evidence-backed, recovered research):** desired retention **0.90**
  (sane band 0.80–0.95; **>0.97 discouraged** — review cost explodes). FSRS parameters are **per-deck-preset**
  (each deck can carry its own); only the scheduler enable/disable is truly global. (Skill-separation vs a
  combined deck is a deliberate choice — Bunpro famously combines grammar+vocab; we keep skill-separated decks
  for legible load + per-skill pacing. Alternative gating worth noting: WaniKani advances by **mastery**
  (~90% pass) rather than lesson-completion; we gate by lesson completion now, mastery-gating is a future option.)
- **Cards:** each registry item yields one or more cards by **type**: `recognition` (see JP → meaning),
  `production` (meaning → JP / type it), `listening` (audio → meaning; post-audio), `handwriting` (draw the
  kanji/kana). Card type set per skill: kana → recognition+production(+handwriting); kanji →
  recognition+production+handwriting; vocab → recognition+production(+listening); grammar →
  recognition(cloze)+production; phrase → listening+production.
- **Unlock contract (owner):** completing a lesson **enrolls its `unlocks` items' cards** into the scheduler;
  **the first card of a deck unlocks (creates) that deck** for the user. So a lesson's `srs.introduces_cards`
  is derived directly from its `unlocks` (item → its skill's card types → its deck). No card is scheduled before
  its introducing lesson is done → review load tracks lesson progress, never overwhelming a linear learner.
- **Pacing:** because new cards are gated by lesson completion (not a fixed daily faucet), the classic SRS
  "new-card flood" is avoided; the per-deck new/day cap is a safety ceiling, not the primary throttle.
- **New-vs-review ordering (block-then-interleave):** a freshly-unlocked card gets an initial blocked exposure
  (study the new batch first) before being interleaved into the spaced review backlog — Anki's "new cards last"
  + SLA interleaving evidence. (Single-study support for the exact ordering — medium confidence.)
- _Sources/confidence for §6 + the deck defaults: `research/deep-research-courseware.md` (FSRS docs, Anki manual,
  WaniKani API, Bunpro). The adversarial Verify phase did not run — treat numbers as well-sourced defaults, not
  verified results._

## 7. Lesson length + internal structure (the "fast but complete" balance)
- **Target size (DESIGN HEURISTIC, not evidence-backed):** ~**300–700 words** of pt-BR explanatory reading per
  lesson + **4–8** referenced examples (`<sentence>`/chips) + **4–8** exercises + a `<checklist>`; rough
  time-on-task **8–15 min**. ⚠ Provenance honesty: a 2024 systematic review finds **no consensus** on optimal
  micro-lesson duration, and microlearning practice often targets **2–5 min**. Our band deliberately runs
  **longer** because these are *worked-example teaching* lessons (explain the *why* + guided practice), not
  flashcards — the SRS owns long-tail review. Treat the band as a tunable target, not a law; if a lesson exceeds
  the upper band or carries >1 core new grammar, **SPLIT** it.
- **Worked-example mechanics (well-sourced):** use **faded / completion problems** as the efficient middle rung
  between fully-worked examples and free production (worked → faded → free). Apply the **expertise-reversal**
  shift: early lessons lean on worked dissections; as items mature, retrieval/production (and the SRS) take over.
  Explanation:practice **order and ratio are tunable by content type** (an RCT found order isn't decisive) — don't
  over-prescribe the rubric. Sources/confidence: `research/deep-research-courseware.md` (Mayer segmenting, CLT
  worked-example + faded-guidance research).
- **Chunking:** ≤1 core new grammar point/lesson (curriculum.md §3 caps are **per lesson**: 3–5 grammar /
  15–25 vocab / 5–10 kanji, fewer in early lessons; a topic splits into as many lessons as its placed-item count
  needs — e.g. a 27-grammar topic → ~6 lessons); spiral the previous 2–3 lessons' items into examples/exercises.
- **Shape (rubric):** hook/intro → clear "porquê" explanation with referenced examples → guided examples →
  exercises (recognition → production) → `<checklist>` (the can-do recap = success criterion). ≥1 retrieval +
  ≥1 production exercise (validate_lessons enforces).

## 8. What P7 validates (additions)
- All four manifest tiers exist and cross-link (manifest→course→topic→lesson paths resolve).
- Every `needs` ref is unlocked by a strictly-earlier lesson (linearity), except kana-bootstrap words (kana-only
  deps). Every `unlocks` item is introduce-once. `type`/`feature`/`ref`-namespace ∈ the closed enums.
- Each `feature` is unlocked before any lesson/exercise that uses it. Each `srs.introduces_cards` deck+item
  resolves; deck registry complete. (Format/ref/structure checks already in `validate_lessons.py`.)

## 9. Build/export
`export_course.py` emits all four tiers from the DB (extends current outline/lesson export). New DB needs (P6b):
widen `lesson_introduces.member_type` to the `unlock_type` enum (or add `lesson_unlocks`), add `lesson_needs`,
a `feature`/`deck`/`card` registry, and a `kana` registry (see kana.md). `design/unlock_enums.json` is the
machine-readable enum the loader + validator import.
