# corpus/readings — in-lesson reading-practice boxes (our format)

Short reading passages attached to lessons. Two provenances live here and every record says which it is in `source`:

- **`authored:w15-passages`** (Layer **C**, `ai_generated: true`, `needs_review: true`) — a 3–6 sentence passage written for that lesson, independently verified, gated to the lesson's known set, and coherent as a text. APP_PLAN W15. These replaced the assembled boxes, which read as a pile of unrelated true sentences rather than a text.
- **`selection:sentence-bank`** (Layer **B**) — the historical assembly by SELECTION from the verified bank (real **Tatoeba (CC BY 2.0 FR)** / **JEC (CC BY 3.0)** Japanese, human EN, our re-authored pt-BR, fully dissected). A box still carrying this is one W15 HELD: its authored passage needs an unlock its gating lesson does not have yet (W21b).

Every box is **i+0** for the lesson it is gated to — every kanji and content word it uses is already in that lesson's `cumulative_known_set` (HARD gate, `scripts/validate/validate_readings.py`); `scripts/validate/validate_reading_coherence.py` adds the coherence checks (one topic, tense / pronoun / register continuity). See `design/reading_practice.md`.

Per box: `{slug, level, gated_to_lesson, title, jp, sentences:[…], tokens:[{s,r,ro,pos}], translation:{pt-BR,en}, length_band, uses:{kanji,vocab}, source_slugs:[sent:…], source, comprehension?}`.

`sentences` is the box's own segmentation, concatenating exactly to `jp` — stored rather than re-derived because a quoted dialogue terminates every line inside 「…。」 (a plain split on 。 yields one unit for a six-line exchange) and `design/translation_style.md` §3 drops the final 。 on generated Japanese. An authored box carries the segmentation its author wrote; a selection-era box carries the split of its own `jp`.

`uses` is a **SNAPSHOT**, not a live projection: it records what this passage's own SudachiPy mode-C tokenisation resolved to at the moment it was applied, in published slug space (`vocab:<jmdict_id>`, never headwords — 93 headwords name more than one record). It is deliberately NOT recomputed from `sentence_kanji` / `sentence_vocab`: those link tables grow with every later dissection pass, and a recompute would push already-gated boxes out of their lesson's known set. Only records the gating lesson already teaches are credited, so `uses` is inside the known set by construction.

`comprehension` names the box's own 内容一致 question in `corpus/exam_banks/<level>_reading_comp.json` (`item`). The question STRING is not copied here — the bank is its single source. `about_current_text` says whether that question was authored against the text this box prints now; the question and its options are resolved into this file only when it is true, and W18 regenerating the bank over the new passages flips the rest with no second apply.

`source_slugs` credit the underlying bank sentences of a selection-era box (provenance).

- `n3.json` — 152 boxes
- `n4.json` — 91 boxes
- `n5.json` — 43 boxes
