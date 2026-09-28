-- W46 (research/reports/APP_PLAN.md Lane E) — particle usage ids and token role enums.
--
-- `particle.usage` is one id of the closed enum in design/particle_functions.json (class + usage by
-- Japanese grammar: ni.time-point, ni.goal, ni.agent ...). `usage_status` says how it was assigned
-- (auto | verified | ruled; NULL while held). `usage_slots` is the JSON of the template slots the
-- explanation is rendered from ({chunk | left | expression, positions for a compound}); the rendered
-- text itself lives in localized_text (particle, explanation) and the legacy authored text moves to
-- (particle, note). Written by scripts/apply_particle_usage.py from
-- research/derived/repairs/particle_usage.json; re-rendered and checked on every gate run by
-- scripts/validate/validate_particle_usage.py.
--
-- `token.function` / `aux_function` / `chunk_role` are the enums of design/token_roles.json
-- (research/derived/repairs/token_roles.json). The free-text `role` stays in localized_text.
--
-- All six columns are Layer B (mechanical or verified against the enum). init_db.py treats
-- "duplicate column name" as already-applied, so this is safe on the existing DB.

ALTER TABLE particle ADD COLUMN usage TEXT;
ALTER TABLE particle ADD COLUMN usage_status TEXT;
ALTER TABLE particle ADD COLUMN usage_slots TEXT;
ALTER TABLE token ADD COLUMN function TEXT;
ALTER TABLE token ADD COLUMN aux_function TEXT;
ALTER TABLE token ADD COLUMN chunk_role TEXT;
