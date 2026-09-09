-- W11b (A5) — a family address can now be RETIRED, and the retirement is published.
--
-- `family.slug` is a stable, published address (contracts/manifest.json id_namespace `grp`). Two
-- things in the family rebuild retire one: owner decision D14 drops the 51 materialized
-- `kanji_component` families in favour of answering the same query from `kanji.components`, and a
-- topic-derived bucket disappears whenever the course stops leaving it any residue. Deleting the
-- row would leave a published address resolving to nothing, so the family layer gets the same
-- redirect column grammar_point and vocab already carry: NULL means live, non-NULL means retired
-- and names where the answer moved to.
--
-- Unlike the grammar merge, a retired family does not always have another family as its successor —
-- D14's answer is a QUERY, not a group. So the value is "where to go", not "which family": either a
-- surviving family slug (`grp:...`) or the store that now answers the question, written as the
-- exported field path it lives at (`kanji.components`). Both forms are published in
-- corpus/families_deprecated.json, and scripts/validate/validate_contracts.py sees the same map.
--
-- init_db.py treats "duplicate column name" as already-applied, so this is safe on the existing DB.

ALTER TABLE family ADD COLUMN deprecated_by TEXT;
