# Rich lesson format — PLAN (finalize in P6)

> Owner directive (2026-06-14): lessons must be **visually rich, interactive** — stored as **rich HTML with
> custom elements** that the front-end renders (rich modals for phrases, hover/click modals for kanji,
> inline exercises, media, etc.). **This is a plan**: the full component schema + exact attributes are decided
> when we author lessons (P6), with light didactic research then if needed. Not implemented now.
>
> **Clean-room note:** an example lesson from the local course was viewed *only* as a structural reference for
> the "custom-elements-rendered-by-frontend" idea. We copy **no content and no element names** from it (§1.4);
> the namespace and components below are our own.

## Principles (must hold)
1. **Ref-by-ID, never embed** — every interactive block references a corpus entity by **stable ID**
   (`sent:…`, `kanji:…`, `vocab:…`, `gram:…`, asset ids). The front-end resolves the full record at render.
   Editing a sentence/kanji/meaning once updates every lesson that references it (the single-source rule).
2. **Constrained, documented element set** — lessons use only the allowed custom elements (below) + a small
   whitelist of plain HTML (h2/h3, p, strong, em, ul/ol/li, table). P7 validates: only allowed elements; all
   `ref` ids resolve to existing corpus entities (no dangling refs); learner text is pt-BR.
3. **FSRS / SRS** — enrollment is driven by `lesson_introduces` (not the HTML); rich elements may *mark* the
   items but the authoritative "what enters FSRS on completion" is the DB link (see `p6_authoring_spec.md`).
4. **Namespace** = `yk-` (Yomineko). All custom elements are lowercase, hyphenated, self-describing.

## Initial component vocabulary (DRAFT — extend/finalize in P6)
### Structure & text
- `yk-lesson` (root; attrs: `id`, `topic`, `level`) · headings `h2`/`h3` · `p` · `strong`/`em` · lists · `table`
- `yk-note type="vantagem-pt|armadilha-pt|cultura|dica"` — the recurring pedagogical callouts
- `yk-checklist` / `yk-checklist-item` — the lesson's can-do / "vitórias" recap

### Corpus references (the interactive core — all by ID)
- `yk-sentence ref="sent:…"` — renders the dissected sentence; **click → rich modal** (furigana, per-token
  glosses, particle explanations, pt translation, audio). Attrs: `show="furigana|romaji|both"`, `mode="inline|card"`.
- `yk-kanji ref="kanji:…"` (or `char`) — kanji chip; **hover/click → modal** (meanings_pt, readings tagged by
  tier, KanjiVG stroke order, components/family, example words).
- `yk-vocab ref="vocab:…"` — vocab chip; click → modal (reading, meaning, pitch, example sentences).
- `yk-grammar ref="gram:…"` — grammar chip; click/expand → explanation/formation/nuance.
- `yk-token ref="…"` / inline `ruby` — fine-grained furigana/gloss highlight when needed.

### Media (by asset id; audio deferred per owner)
- `yk-image ref="img:…"` (attrs: `width`,`height`,`align`,`caption`)
- `yk-video ref="vid:…"`
- `yk-audio ref="aud:…"` — play button (renders once audio assets exist; audio is deferred now)
- `yk-stroke ref="kanji:…"` — animated stroke-order (from KanjiVG)

### Interactive exercises (typed, auto-gradable — by ID)
- `yk-exercise ref="ex:…"` — renders the structured exercise (type from the `exercise` table:
  recognition/cloze/particle_choice/sentence_build/reading/listening/production/handwriting/matching);
  pulls prompt, answer key, and referenced sentences/items by ID.
- `yk-flashcard` (`yk-flashcard-front`/`yk-flashcard-back`) — optional reveal card for vocab/kanji.

## Storage & export (P6)
- Add `lesson.body_html` (the rich HTML) alongside/instead of the current Markdown `body_pt`; keep the `.md`
  export as a **flattened human-review** view and the `.json` export as **app-ready** (rich HTML + a resolved
  `refs` manifest listing every entity the lesson references, for prefetch + integrity checks).
- An **asset registry** (`asset` table: id, type image/video/audio, path, license) for lesson media —
  referenced by id like everything else.

## Deferred decisions (do at P6)
- Final element list + exact attributes + a formal schema (e.g. an allowed-elements + attributes spec the
  validator enforces).
- Whether the canonical store is rich-HTML-string or a typed **block-tree JSON** rendered to HTML (HTML is the
  owner's stated preference; a block-tree may be added if it proves easier for AI authoring/validation).
- Optional didactic research on rich/interactive lesson design.
- Audio components activate once the audio-production pass runs (currently deferred).
