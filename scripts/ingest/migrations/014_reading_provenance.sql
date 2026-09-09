-- W15 — a reading box says where its Japanese came from, and which comprehension question is its own.
--
-- THE TABLE ITSELF. `reading` was created by an inline CREATE TABLE inside build_readings.py, so
-- the schema was a function of run order — exactly the defect migration 010 was written to end
-- ("declaring them here makes the schema the migrations' job and the values the scripts' job").
-- It is declared here, with the two new columns; build_readings.py keeps its own
-- CREATE TABLE IF NOT EXISTS, which is now a no-op.
--
-- `source`. Spec §1.1: every record carries a `source`. Every box used to come from the same place
-- — build_readings.py concatenating i+0 sentences out of the verified bank — so nothing recorded
-- it. W15 replaces most of that text with authored, verified, known-set-gated Layer-C passages, so
-- two provenances now coexist in one table and the record has to say which it is:
--   'selection:sentence-bank'  the historical assembly (Layer B, ai_generated 0)
--   'authored:w15-passages'    a W15 passage (Layer C, ai_generated 1, needs_review 1)
-- validate_provenance_json.py rule (e) expects a provenance field present on ANY record of an
-- entity to be present on ALL of them, so the applier fills BOTH values, never only one.
--
-- `comprehension`. Every box already has an authored 内容一致 question — it lives in
-- corpus/exam_banks/<level>_reading_comp.json, one item per `read:` slug, and the in-lesson box has
-- never shown it. This column holds the POINTER plus the flag that says whether that question was
-- authored against the text the box currently prints:
--   {"item": "rc:n5:n5-adjetivos-04-01", "about_current_text": false}
-- The question STRING is not copied here: the exam bank stays its single source, the exporter
-- resolves it, and W18's regeneration therefore reaches the lesson box with no second apply.
-- `about_current_text` is false for every box whose passage W15 replaced — that question is about a
-- concatenation that no longer exists — and the renderer asks a question only when it is true.
--
-- init_db.py treats "duplicate column name" as already-applied, so both halves are safe on both a
-- fresh database (the CREATE lands, the ALTERs are swallowed) and the live one (the CREATE is a
-- no-op, the ALTERs land).

CREATE TABLE IF NOT EXISTS reading (
    slug TEXT PRIMARY KEY, level TEXT, gated_to_lesson TEXT, theme_topic TEXT, title_pt TEXT,
    title_en TEXT, jp TEXT, tokens TEXT, translation_pt TEXT, translation_en TEXT, uses TEXT,
    length_band TEXT, source_slugs TEXT, ai_generated INT DEFAULT 0, needs_review INT DEFAULT 1,
    layer TEXT DEFAULT 'B', source TEXT, comprehension TEXT);

ALTER TABLE reading ADD COLUMN source TEXT;
ALTER TABLE reading ADD COLUMN comprehension TEXT;
