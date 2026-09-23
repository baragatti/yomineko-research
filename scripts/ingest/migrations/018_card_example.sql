-- W28 — every SRS card carries an example sentence and a cloze span over it.
--
-- `lesson.srs.introduces_cards[]` is DERIVED at export from `lesson_unlocks`, so it names a deck, an
-- item and the card kinds and, since W27, a production key. Nothing said which sentence shows the
-- item in use or which part of that sentence a `cloze` card blanks. The example is SELECTED, not
-- authored: `scripts/derive_card_examples.py` picks it from the bank with the lesson renderer's own
-- display rule (check D of validate_lesson_gating at the card's lesson) and aligns the blank to Sudachi
-- token boundaries. It is keyed on the CARD, (lesson, item), for the same reason W27's key is: the
-- known set a sentence is judged against is the introducing lesson's.
-- `sentence` is the bank slug (`sent:...`); `cloze_start`/`cloze_end` are code-point offsets into
-- that sentence's `jp`; `cloze_answer` is `jp[cloze_start:cloze_end]`, stored so a drifted sentence
-- text is caught rather than silently blanking the wrong characters. No locale text lives here.
-- init_db.py treats "table already exists" as already-applied, so this is safe to re-run.
CREATE TABLE IF NOT EXISTS card_example (
    lesson_id     INTEGER NOT NULL REFERENCES lesson(id) ON DELETE CASCADE,
    item          TEXT    NOT NULL,
    sentence      TEXT    NOT NULL,
    cloze_start   INTEGER NOT NULL,
    cloze_end     INTEGER NOT NULL,
    cloze_answer  TEXT    NOT NULL,
    why           TEXT,
    PRIMARY KEY (lesson_id, item)
);
