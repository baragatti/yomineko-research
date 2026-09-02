-- W01 — columns the live database had but no tracked script ever created.
--
-- `grammar_point.register_json` and `grammar_point.caution` are read and written by four scripts
-- (persist_grammar_enrich.py, apply_phase4_grammar.py, fable5_grammar_apply.py, export_corpus.py) and
-- created by none of them: they were added to db/corpus.sqlite by hand and the ALTER was never written
-- down. A rebuild from migrations therefore stopped dead at "no such column: register_json", and the
-- grammar register/caution content was unrecoverable. This migration is that missing ALTER.
--
-- `forms_json` is here for a different reason: build_grammar_forms.py adds it lazily, which made the
-- schema depend on run order (ingest_n3_grammar.py writes the column and legitimately runs earlier).
-- Declaring it as schema removes the ordering trap; build_grammar_forms.py still fills it and its own
-- guard now finds the column already present.
--
-- init_db.py treats "duplicate column name" as already-applied, so this is safe on the existing DB.

ALTER TABLE grammar_point ADD COLUMN register_json TEXT;
ALTER TABLE grammar_point ADD COLUMN caution TEXT;
ALTER TABLE grammar_point ADD COLUMN forms_json TEXT;
