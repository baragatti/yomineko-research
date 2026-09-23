-- W23 — what each lesson exercise TESTS (design/assessment.md §2).
--
-- `lesson.exercises[].item_refs[]` is derived by `scripts/derive_item_refs.py` (the rule of §2.2) and
-- written here by `scripts/apply_item_refs.py`; `export_course.py` joins it onto every exercise.
--
-- Why a new table and not the two columns §2.5 proposed on `exercise_item`: that table keys a member by
-- registry ROW id (member_type in kanji | vocab | grammar), so it cannot hold a `kana:` glyph ref, and
-- `load_lessons.py` deletes and re-inserts every exercise row on a reload, which renumbers
-- `exercise.id`. This table keys on the published exercise slug and the published item ref, the same
-- way `card_example` / `card_production_key` key on published addresses, so a lesson reload cannot
-- orphan it. `exercise_item` keeps being filled from the authoring source as before.
-- init_db.py treats "table already exists" as already-applied, so this is safe to re-run.
CREATE TABLE IF NOT EXISTS exercise_item_ref (
    exercise    TEXT NOT NULL,                 -- ex:... (published exercise slug)
    item_type   TEXT NOT NULL,                 -- design/unlock_enums.json#item_ref_type
    ref         TEXT NOT NULL,                 -- published item id (vocab:<jmdict>, kanji:字, gram:key, kana:...)
    role        TEXT NOT NULL DEFAULT 'target',
    derived_by  TEXT NOT NULL,
    PRIMARY KEY (exercise, item_type, ref)
);
