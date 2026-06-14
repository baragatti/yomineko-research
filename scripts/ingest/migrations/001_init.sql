-- Yomineko corpus — canonical SQLite schema (from design/schema_v2.md).
-- Idempotent (CREATE ... IF NOT EXISTS). Applied by scripts/ingest/init_db.py.
-- Conventions (schema_v2 §B): surrogate INTEGER PK `id` + unique TEXT `slug`.
--   Provenance on content rows: source, created_by(dataset|ai|human), layer(A|B|C), needs_review(0/1).
--   Leveled rows add: level, level_confidence(0..1), level_agreement('2/3'), level_sources(JSON).
--   Array/display-only fields = JSON text; anything queried/joined = a link table.
-- group/family: SQL-reserved word avoided -> table named `family` (== spec §5.6 `group`).

PRAGMA foreign_keys = ON;

-- ───────────────────────── KANJI ─────────────────────────
CREATE TABLE IF NOT EXISTS kanji (
  id              INTEGER PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,          -- e.g. 'kanji:食'
  character       TEXT UNIQUE NOT NULL,
  strokes         INTEGER,
  grade           INTEGER,
  freq_rank       INTEGER,
  unicode_cp      TEXT,
  kanjivg_ref     TEXT,
  kangxi_radical  INTEGER,
  meanings_pt     TEXT,                          -- JSON [] (Layer B)
  meanings_en     TEXT,                          -- JSON [] (Layer A cross-check)
  notes_pt        TEXT,                          -- Layer C (optional)
  level           TEXT,
  level_confidence REAL,
  level_agreement TEXT,
  level_sources   TEXT,                          -- JSON []
  source          TEXT NOT NULL,
  created_by      TEXT NOT NULL DEFAULT 'dataset',
  layer           TEXT NOT NULL DEFAULT 'A',
  needs_review    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS kanji_reading (
  id                  INTEGER PRIMARY KEY,
  kanji_id            INTEGER NOT NULL REFERENCES kanji(id),
  reading             TEXT NOT NULL,             -- kana (e.g. た for た.べる)
  reading_type        TEXT NOT NULL,             -- on | kun | nanori
  okurigana           TEXT,                      -- e.g. 'べる'
  introduced_at_level TEXT,                      -- n5 | n4 | n3 | ...
  level_confidence    REAL,
  level_sources       TEXT,                      -- JSON []
  example_vocab_ids   TEXT,                      -- JSON [] of vocab ids using THIS reading at THAT level
  source              TEXT NOT NULL,
  created_by          TEXT NOT NULL DEFAULT 'dataset',
  layer               TEXT NOT NULL DEFAULT 'A',
  needs_review        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_kanji_reading_kanji ON kanji_reading(kanji_id);
CREATE INDEX IF NOT EXISTS ix_kanji_reading_read  ON kanji_reading(reading);

CREATE TABLE IF NOT EXISTS kanji_component (
  kanji_id           INTEGER NOT NULL REFERENCES kanji(id),
  component          TEXT NOT NULL,              -- radical/component char
  component_kanji_id INTEGER REFERENCES kanji(id),
  PRIMARY KEY (kanji_id, component)
);
CREATE INDEX IF NOT EXISTS ix_kanji_component_comp ON kanji_component(component);

-- ───────────────────────── VOCAB ─────────────────────────
CREATE TABLE IF NOT EXISTS vocab (
  id              INTEGER PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,          -- e.g. 'vocab:taberu'
  headword        TEXT NOT NULL,                 -- primary written form
  kana            TEXT NOT NULL,
  romaji          TEXT,                          -- POPULATED (Hepburn from kana) — owner decision
  lexeme_type     TEXT NOT NULL DEFAULT 'word',  -- word|suru_verb|counter|prefix|suffix|expression|aux
  base_vocab_id   INTEGER REFERENCES vocab(id),  -- suru_verb -> noun; derived -> base
  verb_class      TEXT,                          -- ichidan|godan|suru_irregular|kuru_irregular|null
  adj_class       TEXT,                          -- i_adj|na_adj|null
  common          INTEGER,                       -- 0/1 (JMdict common)
  freq_rank       INTEGER,
  jmdict_ref      TEXT,                          -- JMdict ent_seq
  notes_pt        TEXT,                          -- Layer C (optional)
  level           TEXT,
  level_confidence REAL,
  level_agreement TEXT,
  level_sources   TEXT,                          -- JSON []
  source          TEXT NOT NULL,
  created_by      TEXT NOT NULL DEFAULT 'dataset',
  layer           TEXT NOT NULL DEFAULT 'A',
  needs_review    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_vocab_headword ON vocab(headword);
CREATE INDEX IF NOT EXISTS ix_vocab_kana     ON vocab(kana);
CREATE INDEX IF NOT EXISTS ix_vocab_level    ON vocab(level);

CREATE TABLE IF NOT EXISTS vocab_form (
  id                 INTEGER PRIMARY KEY,
  vocab_id           INTEGER NOT NULL REFERENCES vocab(id),
  form               TEXT NOT NULL,
  is_kana            INTEGER NOT NULL DEFAULT 0,
  is_common          INTEGER NOT NULL DEFAULT 0,
  is_primary         INTEGER NOT NULL DEFAULT 0,
  applies_to_reading TEXT,
  variant_condition  TEXT                        -- JSON (e.g. counter rendaku conditions)
);
CREATE INDEX IF NOT EXISTS ix_vocab_form_vocab ON vocab_form(vocab_id);
CREATE INDEX IF NOT EXISTS ix_vocab_form_form  ON vocab_form(form);

CREATE TABLE IF NOT EXISTS vocab_sense (
  id           INTEGER PRIMARY KEY,
  vocab_id     INTEGER NOT NULL REFERENCES vocab(id),
  sense_order  INTEGER NOT NULL,
  pos          TEXT,                             -- JSON []
  field_tags   TEXT,                             -- JSON []
  misc_tags    TEXT,                             -- JSON []
  gloss_en     TEXT,                             -- JSON [] (Layer A)
  gloss_pt     TEXT,                             -- JSON [] (Layer B)
  needs_review INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_vocab_sense_vocab ON vocab_sense(vocab_id);

CREATE TABLE IF NOT EXISTS vocab_pitch (
  id               INTEGER PRIMARY KEY,
  vocab_id         INTEGER NOT NULL REFERENCES vocab(id),
  reading          TEXT NOT NULL,
  accent_positions TEXT,                         -- JSON [] of mora drop indices
  source           TEXT
);
CREATE INDEX IF NOT EXISTS ix_vocab_pitch_vocab ON vocab_pitch(vocab_id);

CREATE TABLE IF NOT EXISTS vocab_kanji (
  vocab_id INTEGER NOT NULL REFERENCES vocab(id),
  kanji_id INTEGER NOT NULL REFERENCES kanji(id),
  position INTEGER,
  PRIMARY KEY (vocab_id, kanji_id, position)
);
CREATE INDEX IF NOT EXISTS ix_vocab_kanji_kanji ON vocab_kanji(kanji_id);

-- ───────────────────────── GRAMMAR ─────────────────────────
CREATE TABLE IF NOT EXISTS grammar_point (
  id               INTEGER PRIMARY KEY,
  slug             TEXT UNIQUE NOT NULL,         -- e.g. 'gram:te-form'
  key              TEXT NOT NULL,
  label_pt         TEXT,
  structure_pattern TEXT,                        -- e.g. 'Vて + います'
  register         TEXT,                         -- neutral|polite|casual|formal
  explanation_pt   TEXT,                         -- Layer C (original)
  formation_pt     TEXT,                         -- Layer C
  nuance_pt        TEXT,                         -- Layer C (pitfalls for PT speakers)
  references_json  TEXT,                         -- JSON [] (consulted, NOT copied)
  level            TEXT,
  level_confidence REAL,
  level_agreement  TEXT,
  level_sources    TEXT,                         -- JSON []
  source           TEXT NOT NULL,
  created_by       TEXT NOT NULL DEFAULT 'ai',
  layer            TEXT NOT NULL DEFAULT 'C',
  needs_review     INTEGER NOT NULL DEFAULT 1    -- grammar defaults to review
);
CREATE INDEX IF NOT EXISTS ix_grammar_level ON grammar_point(level);

CREATE TABLE IF NOT EXISTS grammar_related (
  grammar_id         INTEGER NOT NULL REFERENCES grammar_point(id),
  related_grammar_id INTEGER NOT NULL REFERENCES grammar_point(id),
  relation           TEXT NOT NULL,             -- contrast | builds_on | variant
  PRIMARY KEY (grammar_id, related_grammar_id, relation)
);

-- ───────────────────────── SENTENCE + dissection ─────────────────────────
CREATE TABLE IF NOT EXISTS sentence (
  id                    INTEGER PRIMARY KEY,
  slug                  TEXT UNIQUE NOT NULL,    -- e.g. 'sent:tatoeba-7421'
  jp                    TEXT NOT NULL,
  kana                  TEXT,
  romaji                TEXT,                    -- POPULATED (owner decision)
  pt                    TEXT,                    -- Layer B (generated)
  pt_literal            TEXT,                    -- Layer B
  en                    TEXT,                    -- Layer A cross-check (Tatoeba EN)
  level                 TEXT,                    -- = max(component levels)
  intro_topic_id        INTEGER REFERENCES topic(id),
  jp_source             TEXT NOT NULL,           -- tatoeba:<id> | ai_generated
  pt_source             TEXT,                    -- ai | tatoeba | human
  pt_validated_against  TEXT,                    -- en | dict | both | none
  translation_confidence REAL,
  audio_ref             TEXT,                    -- (deferred) tatoeba:<id> | tts:<voice>
  audio_source          TEXT,                    -- (deferred) tatoeba | tts | none
  structure_explanation_pt TEXT,                 -- Layer C
  difficulty            REAL,
  tags                  TEXT,                    -- JSON []
  new_items             TEXT,                    -- JSON [] (i+1 tracking)
  dissection_tier       TEXT NOT NULL DEFAULT 'lite', -- lite | full (schema_v2 D5)
  ai_generated          INTEGER NOT NULL DEFAULT 0,
  verified              INTEGER NOT NULL DEFAULT 0,
  source                TEXT NOT NULL,
  created_by            TEXT NOT NULL DEFAULT 'dataset',
  layer                 TEXT NOT NULL DEFAULT 'A',
  needs_review          INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_sentence_level ON sentence(level);
CREATE INDEX IF NOT EXISTS ix_sentence_jpsrc ON sentence(jp_source);

CREATE TABLE IF NOT EXISTS token (
  id                  INTEGER PRIMARY KEY,
  sentence_id         INTEGER NOT NULL REFERENCES sentence(id),
  position            INTEGER NOT NULL,
  split_mode          TEXT NOT NULL,             -- A | C
  parent_token_id     INTEGER REFERENCES token(id),
  surface             TEXT NOT NULL,             -- Layer A (analyzer, immutable)
  lemma               TEXT,                      -- Layer A
  reading             TEXT,                      -- Layer A (realized reading)
  romaji              TEXT,                      -- POPULATED
  pos_coarse          TEXT,                      -- Layer A
  pos_fine            TEXT,                      -- Layer A
  role_pt             TEXT,                      -- Layer B
  gloss_pt            TEXT,                      -- Layer B (in-context)
  conjugation_note_pt TEXT,                      -- Layer B
  vocab_id            INTEGER REFERENCES vocab(id),
  kanji_ids           TEXT                       -- JSON []
);
CREATE INDEX IF NOT EXISTS ix_token_sentence ON token(sentence_id);
CREATE INDEX IF NOT EXISTS ix_token_lemma    ON token(lemma);
CREATE INDEX IF NOT EXISTS ix_token_vocab    ON token(vocab_id);

CREATE TABLE IF NOT EXISTS particle (
  id             INTEGER PRIMARY KEY,
  sentence_id    INTEGER NOT NULL REFERENCES sentence(id),
  token_id       INTEGER REFERENCES token(id),
  particle       TEXT NOT NULL,
  function_pt    TEXT,                           -- Layer B/C
  explanation_pt TEXT                            -- Layer C
);
CREATE INDEX IF NOT EXISTS ix_particle_sentence ON particle(sentence_id);
CREATE INDEX IF NOT EXISTS ix_particle_particle ON particle(particle);

-- sentence ↔ registry graph edges
CREATE TABLE IF NOT EXISTS sentence_vocab (
  sentence_id   INTEGER NOT NULL REFERENCES sentence(id),
  vocab_id      INTEGER NOT NULL REFERENCES vocab(id),
  usage_note_pt TEXT,
  PRIMARY KEY (sentence_id, vocab_id)
);
CREATE INDEX IF NOT EXISTS ix_sv_vocab ON sentence_vocab(vocab_id);

CREATE TABLE IF NOT EXISTS sentence_kanji (
  sentence_id INTEGER NOT NULL REFERENCES sentence(id),
  kanji_id    INTEGER NOT NULL REFERENCES kanji(id),
  PRIMARY KEY (sentence_id, kanji_id)
);
CREATE INDEX IF NOT EXISTS ix_sk_kanji ON sentence_kanji(kanji_id);

CREATE TABLE IF NOT EXISTS sentence_grammar (
  sentence_id   INTEGER NOT NULL REFERENCES sentence(id),
  grammar_id    INTEGER NOT NULL REFERENCES grammar_point(id),
  usage_note_pt TEXT,
  PRIMARY KEY (sentence_id, grammar_id)
);
CREATE INDEX IF NOT EXISTS ix_sg_grammar ON sentence_grammar(grammar_id);

-- ───────────────────────── FAMILY (group, §5.6) ─────────────────────────
CREATE TABLE IF NOT EXISTS family (
  id                INTEGER PRIMARY KEY,
  slug              TEXT UNIQUE NOT NULL,        -- e.g. 'grp:godan'
  type              TEXT NOT NULL,               -- semantic_field|kanji_component|phonetic_series|
                                                 --   word_family|conjugation_class|particle_set|
                                                 --   contrast_pair|function_set
  label_pt          TEXT,
  description_pt    TEXT,                         -- Layer C
  importance_rank   INTEGER,
  governing_rule_pt TEXT,                         -- Layer C
  spans_levels      TEXT,                         -- JSON []
  primary_module_id INTEGER REFERENCES course_module(id),
  source            TEXT NOT NULL DEFAULT 'ai',
  created_by        TEXT NOT NULL DEFAULT 'ai',
  layer             TEXT NOT NULL DEFAULT 'C',
  needs_review      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS family_member (
  family_id   INTEGER NOT NULL REFERENCES family(id),
  member_type TEXT NOT NULL,                      -- kanji | vocab | grammar
  member_id   INTEGER NOT NULL,                   -- id in the respective table (polymorphic)
  intra_order INTEGER,
  is_core     INTEGER NOT NULL DEFAULT 0,
  note_pt     TEXT,
  PRIMARY KEY (family_id, member_type, member_id)
);
CREATE INDEX IF NOT EXISTS ix_fm_member ON family_member(member_type, member_id);

CREATE TABLE IF NOT EXISTS family_related (
  family_id         INTEGER NOT NULL REFERENCES family(id),
  related_family_id INTEGER NOT NULL REFERENCES family(id),
  relation          TEXT NOT NULL,                -- contrast_pair | sub_family
  PRIMARY KEY (family_id, related_family_id, relation)
);

-- ───────────────────────── COURSEWARE (module→topic→lesson→exercise) ─────────────────────────
CREATE TABLE IF NOT EXISTS course_module (
  id           INTEGER PRIMARY KEY,
  slug         TEXT UNIQUE NOT NULL,             -- e.g. 'mod:n5'
  level        TEXT NOT NULL,                    -- pre-n5 | n5 | n4 | ...
  ord          INTEGER NOT NULL,
  title_pt     TEXT,
  overview_pt  TEXT,                             -- Layer C
  source       TEXT NOT NULL DEFAULT 'ai',
  created_by   TEXT NOT NULL DEFAULT 'ai',
  layer        TEXT NOT NULL DEFAULT 'C',
  needs_review INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS topic (
  id            INTEGER PRIMARY KEY,
  slug          TEXT UNIQUE NOT NULL,            -- e.g. 'top:n5-particles'
  module_id     INTEGER NOT NULL REFERENCES course_module(id),
  ord           INTEGER NOT NULL,
  title_pt      TEXT,
  theme_pt      TEXT,
  family_ids    TEXT,                            -- JSON []
  objectives_pt TEXT,                            -- JSON []
  prerequisites TEXT,                            -- JSON [] of topic ids
  source        TEXT NOT NULL DEFAULT 'ai',
  created_by    TEXT NOT NULL DEFAULT 'ai',
  layer         TEXT NOT NULL DEFAULT 'C',
  needs_review  INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_topic_module ON topic(module_id);

CREATE TABLE IF NOT EXISTS lesson (
  id                   INTEGER PRIMARY KEY,
  slug                 TEXT UNIQUE NOT NULL,
  topic_id             INTEGER NOT NULL REFERENCES topic(id),
  ord                  INTEGER NOT NULL,
  title_pt             TEXT,
  objectives_pt        TEXT,                      -- JSON []
  prerequisites        TEXT,                      -- JSON [] of lesson ids
  body_pt              TEXT,                       -- DENSE Layer C teaching text
  cumulative_known_set TEXT,                       -- JSON (computed)
  source               TEXT NOT NULL DEFAULT 'ai',
  created_by           TEXT NOT NULL DEFAULT 'ai',
  layer                TEXT NOT NULL DEFAULT 'C',
  needs_review         INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_lesson_topic ON lesson(topic_id);

CREATE TABLE IF NOT EXISTS exercise (
  id             INTEGER PRIMARY KEY,
  slug           TEXT UNIQUE NOT NULL,
  lesson_id      INTEGER NOT NULL REFERENCES lesson(id),
  ord            INTEGER NOT NULL,
  type           TEXT NOT NULL,                   -- recognition|cloze|particle_choice|sentence_build|
                                                  --   reading|listening|production|matching|handwriting
  prompt_pt      TEXT,
  answer         TEXT,                            -- JSON (structured answer key)
  explanation_pt TEXT,                            -- Layer C
  needs_review   INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_exercise_lesson ON exercise(lesson_id);

-- courseware → corpus references (BY ID ONLY; never embed)
CREATE TABLE IF NOT EXISTS lesson_introduces (
  lesson_id   INTEGER NOT NULL REFERENCES lesson(id),
  member_type TEXT NOT NULL,                      -- kanji | vocab | grammar
  member_id   INTEGER NOT NULL,
  PRIMARY KEY (lesson_id, member_type, member_id)
);
CREATE INDEX IF NOT EXISTS ix_li_member ON lesson_introduces(member_type, member_id);

CREATE TABLE IF NOT EXISTS lesson_sentence (
  lesson_id   INTEGER NOT NULL REFERENCES lesson(id),
  sentence_id INTEGER NOT NULL REFERENCES sentence(id),
  PRIMARY KEY (lesson_id, sentence_id)
);

CREATE TABLE IF NOT EXISTS exercise_sentence (
  exercise_id INTEGER NOT NULL REFERENCES exercise(id),
  sentence_id INTEGER NOT NULL REFERENCES sentence(id),
  PRIMARY KEY (exercise_id, sentence_id)
);

CREATE TABLE IF NOT EXISTS exercise_item (
  exercise_id INTEGER NOT NULL REFERENCES exercise(id),
  member_type TEXT NOT NULL,                      -- kanji | vocab | grammar
  member_id   INTEGER NOT NULL,
  PRIMARY KEY (exercise_id, member_type, member_id)
);

-- ───────────────────────── PROVENANCE / META ─────────────────────────
CREATE TABLE IF NOT EXISTS dataset_source (
  id            INTEGER PRIMARY KEY,
  name          TEXT UNIQUE NOT NULL,
  version       TEXT,
  url           TEXT,
  license       TEXT,
  commercial_note TEXT,
  sha256        TEXT,
  fetched_at    TEXT
);

CREATE TABLE IF NOT EXISTS schema_migration (
  filename   TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);
