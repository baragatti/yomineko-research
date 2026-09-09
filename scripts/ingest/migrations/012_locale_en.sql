-- W11b — register `en` as a locale, because 30k+ rows have been claiming it for months.
--
-- 004_i18n.sql created `locale` and seeded exactly one row, 'pt-BR', while `localized_text.locale`
-- declares `REFERENCES locale(code)`. Every `en` row ever written -- the Layer-A source glosses,
-- the en family labels, the en governing rules -- violates that foreign key. Nothing noticed
-- because the writers ran without `PRAGMA foreign_keys = ON`; the constraint only fires for a
-- script that turns enforcement on, which is how W11b's family builder found it: the first
-- `set_text(..., locale="en")` under enforcement failed with FOREIGN KEY constraint failed while
-- 322 identical rows already sat in the table.
--
-- design/i18n.md makes `en` a real locale module -- the Layer-A source text the pt-BR content is
-- derived from and cross-checked against -- so the row belongs here. This is a declaration
-- catching up with the data, not a new capability: it adds no column, changes no value, and makes
-- exactly zero difference to any export.
--
-- `is_default` stays 0: pt-BR is the learner-facing locale (CLAUDE.md), en is the source.
-- INSERT OR IGNORE, so re-running is a no-op on a database that already has it.

INSERT OR IGNORE INTO locale (code, name, is_default) VALUES ('en', 'English (source)', 0);
