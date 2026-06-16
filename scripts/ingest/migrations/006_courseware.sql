-- 006_courseware.sql — P6b: generalize lesson metadata to the needs/unlocks model.
-- The closed taxonomy (unlock_type / need_type / feature / deck / card_type / conjugation_form) lives in
-- design/unlock_enums.json (single source of truth; loader+validator import it). Feature/deck "registries"
-- ARE that enum — no DB tables needed for them. Lesson `description` is stored via localized_text
-- (entity_type='lesson', field='description'); no column added. SRS cards are DERIVED from item unlocks.

-- Generalized unlocks (supersedes lesson_introduces, which is still written as a grammar/vocab/kanji subset
-- for back-compat with the placement/⊆-topic checks + the existing export `introduces` block).
CREATE TABLE IF NOT EXISTS lesson_unlocks (
  lesson_id   INTEGER NOT NULL,
  unlock_type TEXT    NOT NULL,   -- unlock_type enum
  ref         TEXT    NOT NULL,   -- normalized namespaced id, e.g. vocab:乗る, gram:te-form, kana:hiragana-sa
  PRIMARY KEY (lesson_id, unlock_type, ref),
  FOREIGN KEY (lesson_id) REFERENCES lesson(id)
);

-- Explicit prerequisite edges (most are auto-satisfied by linear order; recorded for cross-strand + feature gates).
CREATE TABLE IF NOT EXISTS lesson_needs (
  lesson_id INTEGER NOT NULL,
  need_type TEXT    NOT NULL,     -- need_type enum (incl. `lesson`)
  ref       TEXT    NOT NULL,
  PRIMARY KEY (lesson_id, need_type, ref),
  FOREIGN KEY (lesson_id) REFERENCES lesson(id)
);

CREATE INDEX IF NOT EXISTS idx_lesson_unlocks_ref ON lesson_unlocks(unlock_type, ref);
CREATE INDEX IF NOT EXISTS idx_lesson_needs_ref   ON lesson_needs(need_type, ref);
