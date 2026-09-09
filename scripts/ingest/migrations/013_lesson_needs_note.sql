-- W21 — a prerequisite edge carries its REASON, and the reason is learner-facing.
--
-- `design/lesson_schema.md` has specified `needs` as `[{type, ref, note?}]` since the P6 freeze, but
-- `lesson_needs` only ever had (lesson_id, need_type, ref): the note had nowhere to live, so
-- `load_lessons.py` dropped it on ingest and `export_course.py` could not publish it. The field is
-- not decoration — the app renders a "antes desta lição" box, and "les:n5-desu-wa-02" on its own
-- tells a learner nothing about WHY that lesson comes first.
--
-- The value is pt-BR prose produced by a fixed template per reason class
-- (`scripts/build_needs_table.py`), never free-form, so it stays reproducible from the derivation.
-- NULL means "no reason recorded", which is what every pre-W21 row would have been.
--
-- init_db.py treats "duplicate column name" as already-applied, so this is safe on the existing DB.

ALTER TABLE lesson_needs ADD COLUMN note TEXT;
