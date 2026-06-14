-- P4: introducing-topic placement. Each leveled item is introduced at exactly one topic
-- (lesson-level split is refined during P6 authoring). cumulative-known-set is computed from
-- topic order at query time. SQLite ADD COLUMN is idempotent-guarded by the migration runner.
ALTER TABLE kanji         ADD COLUMN introducing_topic_id INTEGER REFERENCES topic(id);
ALTER TABLE vocab         ADD COLUMN introducing_topic_id INTEGER REFERENCES topic(id);
ALTER TABLE grammar_point ADD COLUMN introducing_topic_id INTEGER REFERENCES topic(id);
CREATE INDEX IF NOT EXISTS ix_kanji_introtopic   ON kanji(introducing_topic_id);
CREATE INDEX IF NOT EXISTS ix_vocab_introtopic   ON vocab(introducing_topic_id);
CREATE INDEX IF NOT EXISTS ix_grammar_introtopic ON grammar_point(introducing_topic_id);
