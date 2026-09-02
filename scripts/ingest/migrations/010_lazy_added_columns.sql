-- W01 — the other columns that only existed if some earlier script happened to have run.
--
-- Four columns were added by ALTER TABLE inside the script that first needed them, which made the
-- schema a function of run order rather than of the migrations. `unihan_radical.py` adds
-- kanji.radical_char / kanji.radical_source, and `export_corpus.py` selects both — so exporting a
-- database that had not been through unihan_radical.py failed with "no such column: radical_char"
-- rather than exporting a kanji record with no radical. `build_sentence_vocab.py` does the same for
-- sentence_vocab.link_rule / reading_verified, which the exam banks depend on.
--
-- Declaring them here makes the schema the migrations' job and the values the scripts' job. Both
-- scripts already guard their ALTER with a PRAGMA table_info check, so they keep working untouched.
--
-- init_db.py treats "duplicate column name" as already-applied, so this is safe on the existing DB.

ALTER TABLE kanji ADD COLUMN radical_char TEXT;
ALTER TABLE kanji ADD COLUMN radical_source TEXT;
ALTER TABLE sentence_vocab ADD COLUMN link_rule TEXT;
ALTER TABLE sentence_vocab ADD COLUMN reading_verified INTEGER;
