# W42 — Attribution reconciliation: Kanji Alive + strokesvg (and the two open D9 rulings)

_Executed 2026-09-02. Scope: the non-blocked half of `research/reports/APP_PLAN.md` W42, closing the
`ATTRIBUTION.md` / `design/sources.md` half of readiness finding **G7** ("attribution record is behind the
shipped data"). The two **D9** rulings are the owner's and stay open — §3 records exactly what evidence each
one now has._

**Method:** every figure below was measured on disk in this run. Licence facts come only from files present in
the tree; where an upstream licence text is absent, this report says so rather than asserting a licence.

---

## 1. Licences established (and one that could not be)

### 1.1 strokesvg / Klee One — licence text **present**, fully established

`research/datasets/strokesvg/LICENSE` (5,799 bytes, SHA256
`034fbffd797849ae2717ae2f167315a59b0fc65b5c8339771e100341223fb881`) is a real, bundled licence. It opens with a
NOTICE that splits the repo in two:

- the **hiragana/katakana SVG files** are derived from the **Klee One** font under the **SIL Open Font License**
  — the full **OFL 1.1** text is included in the file, under `Copyright 2020 The Klee Project Authors`
  (https://github.com/fontworks-fonts/Klee);
- **all other files** are **MIT**, `Copyright (c) 2024 Kyle` (MIT text also included in full).

**The half we ingested is exactly the SVG half**, so **OFL 1.1 governs our kana stroke data**; MIT covers only
build tooling we never used. **No Reserved Font Name is declared** in the bundled copyright line.

**Commercial-use terms, read off the bundled text:**

| OFL clause | What it means for us |
|---|---|
| §2 — may be bundled, redistributed and **sold with any software** | A paid app is fine. |
| §2 — *provided each copy contains the copyright notice and this license* | The shipped app must carry the **full OFL 1.1 text + both copyright lines**. A one-line credits bullet does **not** satisfy this. |
| §1 — may **not** be sold by itself | We don't sell stroke data standalone. |
| §5 — Modified Versions stay under OFL, and *"the requirement for fonts to remain under this license does not apply to any document created using the Font Software"* | OFL's copyleft is **font-scoped, not app-scoped** — it never reaches our courseware, UI or lessons. |

**The one judgement call:** our records are a re-expression of Klee-One-derived glyph outlines, so the
conservative reading is that they are a *Modified Version of the Font Software* and therefore must stay under
OFL and carry the notice. That is cheap to comply with either way, so `ATTRIBUTION.md` now states the
notice-carrying obligation as a requirement rather than leaving it to a later ruling.

**Upstream inconsistency found:** `research/datasets/strokesvg/package.json` declares `"license": "ISC"`, which
contradicts the repo's own `LICENSE`. The NOTICE is the specific, file-scoped statement about the SVGs and is
what we rely on; the `ISC` field is recorded in `design/sources.md` as a known upstream error.

### 1.2 Kanji Alive — licence text **absent from the repo**; recorded, not verified

**There is no upstream licence text anywhere in this tree.** Measured:

- no `LICENSE` / `COPYING` / `NOTICE` file under `research/datasets/kanjialive/` (the directory holds exactly
  `kanji_strokes.zip`, `ka_data.csv`, `MANIFEST.md`, plus a 2-file `_peek/` sample);
- **zero licence-named entries among the 11,933 members** of `kanji_strokes.zip`;
- a repo-wide sweep for licence-named files returns only `research/datasets/glyphwiki/LICENSE.txt`,
  `research/datasets/strokesvg/LICENSE`, `design/license_audit.md` and unrelated `.venv` package licences.

So **CC BY 4.0 is not asserted here as a verified fact.** It is what three *second-hand, in-repo* records say:

1. `research/datasets/kanjialive/MANIFEST.md` — "**CC BY 4.0** … Verified from repo `LICENSE.md` (2026-06-26)";
2. `scripts/ingest/kanjialive_strokes.py` — stamps `license = "CC-BY-4.0"` on every ingested row;
3. `design/license_audit.md` D-LIC-2 — "STROKE ORDER → Kanji Alive (CC BY 4.0) … Attribution-only, NO ShareAlike".

All three trace back to one 2026-06-26 reading of a file that was never archived. The claim is very likely
correct and consistent across the project, but it has **no primary evidence on disk**, and this is the stroke
layer's entire proprietary-safety argument.

**To close (one command's worth of work):** archive the upstream `LICENSE.md` beside the dump and record its
SHA256 in `research/datasets/kanjialive/MANIFEST.md`. Recorded as a ⚠ caveat in both `ATTRIBUTION.md` and
`design/sources.md` until then.

Terms as recorded: **CC BY 4.0** — commercial use and redistribution permitted, **no ShareAlike**, attribution
required, and (because our records are an adaptation of the raw step SVGs) an **indication that changes were
made** is required alongside the credit.

---

## 2. What was written

### 2.1 `ATTRIBUTION.md` — two new sections

Inserted in the file's existing style (`### Name` → What / Ships / Owner / License / Attribution text /
Commercial note), placed immediately before the GlyphWiki section, since GlyphWiki's own entry already refers to
"Kanji Alive outlines" as the static fallback. The footer's `_Last updated_` line was moved from P0 to W42.

- **`### Kanji Alive — kanji stroke order (static step outlines)`** — with the ⚠ evidence caveat above spelled
  out, the CC BY "indicate changes" obligation, and re-verified checksums.
- **`### strokesvg / Klee One — kana stroke order`** — with the OFL/MIT split, both copyright holders, the
  "carry the full OFL text, not just a credit line" obligation, and the `package.json` ISC discrepancy.

**Record counts, measured over `corpus/strokes/` (not taken from any manifest):**

| Source | Records | Breakdown | Stamped licence |
|---|---:|---|---|
| `kanjialive` | **1,233** | n5 103 · n4 177 · n3 350 · n2 357 · n1 246 | `CC-BY-4.0` |
| `strokesvg` | **162** | 160 parsed from the 160 dist SVGs (79 hiragana + 81 katakana) + **2 derived** (っ, ッ — reusing the つ/ツ glyph, with the derivation recorded in `source`) | `OFL-1.1+MIT` |

Both match G7's stated 1,233 / 162 exactly. For completeness, the third stroke source in the same directory is
`glyphwiki` at 2,098 records (`GlyphWiki-free`), which was already attributed.

### 2.2 `design/sources.md` — two table rows + a checksum block

Two rows added to the main provenance table after the JEC row, in the existing five-column shape
(Source / Used for / Version fetched / License / Commercial-use note), each carrying the shipped record count.

Because that table has no checksum column, a new **"Stroke-order sources — URLs, dates, SHA256"** block was
added beneath it (mirroring how the N2/N1 block extends the table in prose), carrying source URLs, fetch dates
and the SHA256 figures below, plus the Kanji Alive evidence gap and a pointer to the open D9 block.

**Version / date / SHA256 of the ingested dumps — measured 2026-09-02:**

| Dataset | File | Bytes | SHA256 |
|---|---|---:|---|
| Kanji Alive (fetched 2026-06-26) | `kanji_strokes.zip` | 12,977,338 | `ad1327b57ded0db7a4d325b83d63bbd4f5af6379f22db5e2b020ea869b1deb71` |
| | `ka_data.csv` | 765,855 | `7e7f7098609bff4c26c01772157ea507c9bc09669ce777dbd62bc21d3e135d80` |
| | `MANIFEST.md` | 1,719 | `2d3d6e3ae373a9f795c3f3444235d7dc96477676e6727b298772b0ebfd5a74bc` |
| strokesvg (fetched 2026-06-26) | `dist/**/*.svg` (160 files) | — | `7d1deb8f32d8f4b3856bbab6f10a073293f223b3bebfe9e29096a25eef78b27c` (aggregate over sorted `relpath + bytes`) |
| | `LICENSE` | 5,799 | `034fbffd797849ae2717ae2f167315a59b0fc65b5c8339771e100341223fb881` |
| | `README.md` | 6,228 | `108d3b423118519768f9e0a83bb4243ce5d0ec6115fdb595fa7870a80be37cbd` |
| | `MANIFEST.md` | 1,384 | `db61b8b10efd9e56e83352d3cbd03206a8a09117b0713a1123fd88fe066d65ce` |

Two gaps worth naming: the `kanji_strokes.zip` hash matches its manifest, but **`ka_data.csv` had no recorded
checksum before today**, and **strokesvg has never had any checksum recorded at all** — its manifest lists none.
Neither dataset pins an upstream commit or tag; both are dated only by fetch date (strokesvg's `package.json`
says `version: 1.0.0`, which upstream does not bump).

---

## 3. OPEN — the two D9 rulings (owner's call; **not** decided here)

Both remain blocking for the rest of W42. Each is stated with the evidence it now has and the evidence it still
needs.

### D9-a — "KanjiVG CC BY-SA flag closable now that only `kanjivg_ref` ships?"

**Measurement (2026-09-02).** Scanned `corpus/`, `course/` and `yomineko-prototype/app/data/` byte-for-byte for
`kanjivg` (case-insensitive). **7 files hit, and every hit is the same field:**

| Location | Occurrences | Shape |
|---|---:|---|
| `corpus/kanji/n1..n5.json` | 2,131 | `kanjivg_ref` |
| `yomineko-prototype/app/data/kanji.json` | 2,131 | `kanjivg_ref` |
| `corpus/strokes/exemptions.json` | 2 | prose inside a `reason` string |

**What `kanjivg_ref` actually contains:** all 2,131 records are non-null and **100% of them are a 5-digit
lowercase hex string that equals the Unicode codepoint of the kanji itself** — zero mismatches. Example: 木 →
`06728`. It carries **no KanjiVG content**: no path data, no stroke grouping, no component tree. It is
mechanically derivable from the character with `format(ord(ch), '05x')` and is a filename convention, not data
taken from the project.

**Cross-check — where the shipped stroke geometry actually comes from.** Every record in `corpus/` carrying
stroke geometry (`steps` / `strokes` / `lines` / `shadows`), by stamped source:

| Source | Records | Licence stamped |
|---|---:|---|
| `glyphwiki` | 2,098 | `GlyphWiki-free` |
| `kanjialive` | 1,233 | `CC-BY-4.0` |
| `strokesvg` (incl. 2 derived) | 162 | `OFL-1.1+MIT` |
| KanjiVG | **0** | — |

**Not shipped but still on disk:** `research/datasets/kanjivg/kanjivg-20250816.xml.gz` (3,608,178 bytes) is
still in the working tree as a raw dataset. Raw downloads are git-ignored, so it is not redistributed, but it
is the reason a "KanjiVG is fully gone" claim needs a sentence of nuance rather than a flat yes.

**Evidence the ruling still needs — and only the owner can supply it:**
1. A legal judgement that a **Unicode codepoint rendered as hex** is not a protectable expression of the KanjiVG
   database (measurement says it is fully derivable from the character; that is a fact, not a ruling).
2. A decision on **whether to keep the field at all.** If it is dropped or renamed to something source-neutral
   (`unicode_hex`, say), the question disappears without needing a legal opinion — the value would be identical.
   The prototype build output `build/server/index.js` still contains the literal string `kanjivg`, so the name
   is user-reachable, which is the only reason the field's name matters.
3. Confirmation that **retaining the raw `kanjivg-20250816.xml.gz` locally** (git-ignored, never shipped) is
   acceptable, or an instruction to delete it.
4. If the answer is "closable": the `### KanjiVG` section of `ATTRIBUTION.md` and the KanjiVG row of
   `design/sources.md` should be **retained but restated** — from "we use this" to "historically used, now
   replaced by Kanji Alive + GlyphWiki; only a codepoint-derived id remains" — rather than deleted, since
   deleting a credit is the riskier edit.

### D9-b — "bulk vs per-sentence Tatoeba credit?"

**Measurement (2026-09-02).**

**Were contributor usernames ever stored? No — and they never entered the DB.**

- **The dumps we fetched:** `jpn_sentences.tsv.bz2` (and eng/por) have **3 fields — `id`, `lang`, `text`**.
  Tatoeba's `users_sentences.csv`, the only export carrying a per-sentence author, **was never downloaded**
  (`research/datasets/tatoeba/` holds only the three `*_sentences.tsv.bz2`, `links.tar.bz2` and
  `sentences_with_audio.tar.bz2`).
- **The one dump that does carry a username:** `sentences_with_audio.csv` inside
  `sentences_with_audio.tar.bz2` has 5 fields and field 3 **is** a username (e.g. `LeviHighway`). But
  `scripts/ingest/ingest_all.py` (≈L183–194) reads only the **sentence id** into a set and persists a
  **`has_audio` 0/1 flag**. The username is read and discarded.
- **The DB (54 tables):** `raw_tatoeba_sentence` is `(id, text, has_audio)`; `raw_tatoeba_translation` is
  `(jp_id, lang, trans_id, text)`. **No table anywhere has a contributor/username column.** The only
  person-shaped column is `created_by`, whose value is `'ai'` for all 5,889 sentences. `audio_source` is `NULL`
  for all 5,889 — **no Tatoeba audio ships at all**, so the "audio licences vary by contributor" caveat is
  currently moot.
- **Shipped records:** `corpus/sentences/*.json` records have **no username-shaped key** (keys are `slug`, `jp`,
  `kana`, `romaji`, `translation`, `translation_literal`, `tokens`, `particles`, `grammar`, `pattern`,
  `provenance`, …). Same in `yomineko-prototype/app/data/`: the only `"author"`/`"owner"` byte-matches in
  `kanji.json` / `vocab.json` are **English glosses** (著者 → "author", 主 → "owner"), not fields.

**What the shipped data *does* preserve — the per-sentence id.**

| Fact | Measured |
|---|---:|
| Shipped sentences total | 5,889 |
| `jp_source = tatoeba` | **3,549** |
| `jp_source = ai-generated` / `generated` | 2,207 / 6 |
| `jp_source = jec` | 127 |
| Distinct Tatoeba ids in the shipped app data | **3,549** |
| Field carrying them | `slug`, shaped `sent:tatoeba-<id>` |

So every one of the 3,549 Tatoeba sentences is individually addressable: `sent:tatoeba-10006818` resolves to
`https://tatoeba.org/sentences/show/10006818`. **Per-sentence *linking* is already possible today with no data
change; per-sentence *author naming* is not, and would require fetching `users_sentences.csv` and a re-ingest.**

**Evidence the ruling still needs — and only the owner can supply it:**
1. **Which of three credit levels ships**, given CC BY 2.0 FR requires attribution "in the manner specified by
   the author or licensor":
   - **(a) bulk only** — today's one-line credit on `/creditos`. Zero work. The weakest reading of CC BY.
   - **(b) bulk + per-sentence link** — additionally render each sentence's `tatoeba.org/sentences/show/<id>`
     link in the UI. **Costs no data work** (the ids already ship); it is a UI decision only. This is the option
     the measurement unlocks.
   - **(c) bulk + per-sentence author name** — requires fetching `users_sentences.csv`, joining on 3,549 ids,
     a re-ingest and an export. Note the standing tension: `ATTRIBUTION.md` already promises *"per-sentence
     author credit … should be preserved where feasible"*, and it currently is **not** preserved. Either the
     data changes or that sentence does.
2. A ruling on **whether AI-generated pt-BR translations of a CC BY sentence** need the same credit treatment as
   the Japanese source line (spec calls the Japanese Layer A and our pt-BR Layer B; CC BY's adaptation clause is
   the question).
3. Nothing blocks (b) or (c) technically — this is purely the owner's call on how much credit to show.

---

## 4. Residual G7 items NOT covered by this unit

W42's scope was the two sections plus the two rows. G7 also lists, and these remain open:

- `dataset_source` rows for **Unihan, GlyphWiki, Kanji Alive, strokesvg, SudachiDict, jaconv** and the six
  unlisted JLPT lists — and the fact that the machine-readable record **lives only in the git-ignored SQLite**,
  which contradicts the canonical-is-JSON directive in `CLAUDE.md`. It needs a committed home under `design/`
  or `contracts/`.
- Licences + SHA256 for the four `'verify'` rows in `design/sources.md` (`kanji.json`/davidluzgouveia and
  `elzup/jlpt-word-list` still read "repo license — **verify**" in the table, though the N2/N1 block below it
  already calls both MIT — an internal contradiction worth resolving in one edit).
- `STATE.md`'s empty dataset-manifest table.
- **The validator G7 asks for:** a gate that fails when a `source` value on a shipped record has no
  `ATTRIBUTION.md` entry. With `kanjialive` and `strokesvg` now present, the six distinct `source` values in
  `corpus/strokes/` would all pass — this is the moment such a gate is cheapest to add.
- The two-line **credits-screen** consequence of §1.1: `app/routes/creditos.tsx` names strokesvg and Klee One,
  but OFL §2 wants the **full licence text** shipped, not a mention.
