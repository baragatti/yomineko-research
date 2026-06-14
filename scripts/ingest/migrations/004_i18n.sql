-- Pre-P5 i18n: locale-aware content model. Internals stay English/neutral; learner-facing
-- content moves to localized_text keyed by locale. pt-BR is the first locale module (expandable).
-- The legacy *_pt columns become vestigial after migrate_i18n.py (NULLed); localized_text is the
-- single source of truth for authored content. Upstream English source fields (*_en) stay as-is.

CREATE TABLE IF NOT EXISTS locale (
  code       TEXT PRIMARY KEY,   -- BCP-47-ish, e.g. 'pt-BR', 'es-LA', 'en-US'
  name       TEXT,
  is_default INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO locale (code, name, is_default) VALUES ('pt-BR', 'Português (Brasil)', 1);

CREATE TABLE IF NOT EXISTS localized_text (
  entity_type TEXT NOT NULL,     -- 'kanji' | 'vocab_sense' | 'grammar_point' | 'sentence' | 'token' | ...
  entity_id   INTEGER NOT NULL,
  field       TEXT NOT NULL,      -- NEUTRAL field name, e.g. 'meanings','gloss','explanation','translation','body'
  locale      TEXT NOT NULL REFERENCES locale(code),
  value       TEXT,               -- scalar text, or JSON array/object when is_list=1
  is_list     INTEGER NOT NULL DEFAULT 0,
  layer       TEXT,               -- B|C provenance of this localized content (optional)
  PRIMARY KEY (entity_type, entity_id, field, locale)
);
CREATE INDEX IF NOT EXISTS ix_loctext_entity ON localized_text(entity_type, entity_id, locale);
CREATE INDEX IF NOT EXISTS ix_loctext_field  ON localized_text(entity_type, field, locale);
