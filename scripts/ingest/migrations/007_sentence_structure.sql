-- 007_sentence_structure.sql — roadmap F: machine-readable sentence structure on the sentence record.
--
-- The bank already carries a prose `structure_explanation` that tells a HUMAN what shape a sentence has.
-- Nothing told a PROGRAM, so no construction drill could be built from the bank without re-deriving the
-- shape at read time. These two columns close that.
--
-- pattern_json   Layer B, wholly mechanical, zero AI. The chunk/role array derived by
--                scripts/export/build_sentence_patterns.py from the token array and the
--                (particle, function_type) pair that closes each chunk. Regenerable at any time.
--
-- clause_structure  Layer C, one value from a closed, language-neutral enum:
--                simple / topic-comment / relative-clause / conditional / quote / cause /
--                coordinate / subordinate-time / question / imperative / fragment.
--                Judged from the Japanese, so it carries needs_review like all Layer C.
--
-- Both are DERIVED and rebuildable; neither is ground truth. They live on the sentence rather than in a
-- side table because they are one-to-one with it and every consumer wants them alongside jp.
ALTER TABLE sentence ADD COLUMN pattern_json TEXT;
ALTER TABLE sentence ADD COLUMN clause_structure TEXT;
CREATE INDEX IF NOT EXISTS ix_sentence_clause ON sentence(clause_structure);
