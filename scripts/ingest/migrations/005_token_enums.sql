-- 005: mechanical Layer-A enums on tokens + particles (Sudachi/UniDic derived, language-neutral).
-- pos: neutral POS enum (noun/verb/i-adjective/...). inflection: neutral 活用形 enum
-- (continuative/irrealis/imperative/...). inflection_type: raw Sudachi 活用型 (五段-カ行...) for trace.
-- particle.function_type: neutral joshi class (case/binding/conjunctive/sentence-final/adverbial/nominalizer).
ALTER TABLE token ADD COLUMN pos TEXT;
ALTER TABLE token ADD COLUMN inflection TEXT;
ALTER TABLE token ADD COLUMN inflection_type TEXT;
ALTER TABLE particle ADD COLUMN function_type TEXT;
