-- P1 raw staging tables for the authoritative datasets.
-- The curated corpus tables (001_init.sql) are populated/leveled in P2/P5 from these
-- (and KANJIDIC2/Krad/KanjiVG are loaded straight into the curated `kanji` inventory in P1).

-- JMdict (common) — kept raw for lookup; promoted to `vocab` for the N5/N4 set in P2.
CREATE TABLE IF NOT EXISTS raw_jmdict_entry (
  ent_seq INTEGER PRIMARY KEY,
  common  INTEGER NOT NULL DEFAULT 0,
  data    TEXT NOT NULL                 -- full JSON of the word entry
);
CREATE TABLE IF NOT EXISTS raw_jmdict_form (
  ent_seq   INTEGER NOT NULL,
  form      TEXT NOT NULL,
  is_kana   INTEGER NOT NULL DEFAULT 0,
  is_common INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_rjf_form ON raw_jmdict_form(form);
CREATE INDEX IF NOT EXISTS ix_rjf_seq  ON raw_jmdict_form(ent_seq);

-- Tatoeba Japanese sentences (+ audio flag) and their EN/PT translations (text included).
CREATE TABLE IF NOT EXISTS raw_tatoeba_sentence (
  id        INTEGER PRIMARY KEY,
  text      TEXT NOT NULL,
  has_audio INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS raw_tatoeba_translation (
  jp_id    INTEGER NOT NULL,
  lang     TEXT NOT NULL,               -- eng | por
  trans_id INTEGER NOT NULL,
  text     TEXT NOT NULL,
  PRIMARY KEY (jp_id, trans_id)
);
CREATE INDEX IF NOT EXISTS ix_rtt_jp   ON raw_tatoeba_translation(jp_id);
CREATE INDEX IF NOT EXISTS ix_rtt_lang ON raw_tatoeba_translation(lang);

-- FTS over Japanese sentence text. trigram tokenizer => substring MATCH works on Japanese
-- (default unicode61 would treat a whole JP sentence as one token). First-pass filter for P5;
-- SudachiPy confirms the lemma. External-content table backed by raw_tatoeba_sentence.
CREATE VIRTUAL TABLE IF NOT EXISTS raw_tatoeba_fts USING fts5(
  text,
  content='raw_tatoeba_sentence',
  content_rowid='id',
  tokenize='trigram'
);
