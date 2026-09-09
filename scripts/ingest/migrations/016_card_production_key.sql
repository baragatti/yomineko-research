-- W27 — a production card carries its answer key.
--
-- `lesson.srs.introduces_cards[]` is DERIVED at export from `lesson_unlocks` (deck by skill, card
-- kinds by deck), so it says which memory facts a lesson enrols and nothing about what the learner
-- is asked or what counts as right. For a `recognition` card that is enough: the app shows the
-- record. For a `production` card it is not — 2,951 vocabulary cards ask the learner to write
-- Japanese from a pt-BR cue, and neither the cue nor the accepted answers existed anywhere. G1 of
-- research/reports/readiness/srs_fsrs.md; APP_PLAN W27.
--
-- The key is AUTHORED content and cannot be derived: 883 of the prompts needed a disambiguator
-- because their first gloss is shared with a sibling or a homograph, and the accepted answers are
-- the record's forms minus the rare/archaic/search-only ones JMdict tags (a learner typing み for
-- "mar" was being marked right). So it needs a home of its own, keyed on the CARD — (lesson, item) —
-- and not on the vocabulary record: the same record unlocked by a different lesson would be a
-- different card, and the sense a lesson teaches is a property of the lesson, not of the entry.
--
-- `prompt_pt` is pt-BR prose; the exporter publishes it as the locale object `prompt`, because
-- design/i18n.md already names a bare `prompt_pt` in the export as a contract violation (speak_unit).
-- `accept_json` is a JSON array of Japanese surfaces and is locale-invariant by nature.
-- `sense_index` points into the vocab record's `senses[]` — which sense the introducing lesson
-- teaches — so a reviewer can check the prompt against the gloss it claims to be.
-- `verified` is a claim about the TABLE, not the row: 'sampled' means one verifier at authoring time
-- plus the 100-row Fable sample in research/reports/w27_sample_report.md.
--
-- init_db.py treats "table already exists" / "duplicate column name" as already-applied, so this is
-- safe to re-run on the existing DB.

CREATE TABLE IF NOT EXISTS card_production_key (
    lesson_id    INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    item         TEXT    NOT NULL,
    prompt_pt    TEXT    NOT NULL,
    accept_json  TEXT    NOT NULL,
    sense_index  INTEGER,
    verified     TEXT,
    verified_by  TEXT,
    why          TEXT,
    PRIMARY KEY (lesson_id, item)
);
