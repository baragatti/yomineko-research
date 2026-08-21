-- 008_grammar_formation.sql — roadmap E: machine-usable formation on the grammar point.
--
-- `formation_pt` is prose. A human reads "Verb in te-form + ください" and knows what to do; a program
-- cannot build a conjugation drill from it. These columns state the same thing to code.
--
-- formation_steps_json  ordered build steps per accepting base, as {"variants":[{base, steps:[...]}]}.
--                       Each step is {base?, op, token?} over a CLOSED op enum (to-te-form,
--                       to-masu-stem, to-nai-stem, to-ta-form, to-dictionary, to-volitional,
--                       to-potential, to-passive, to-causative, to-conditional-ba, to-adverbial,
--                       to-attributive, nominalize, append, replace-ending, drop-final-ru, none).
--                       One list PER BASE, never flattened: a flattened sequence that is right for
--                       verbs and wrong for na-adjectives is how ちゃいけない acquired a rule licensing
--                       *読んちゃいけない.
-- nuance_tags_json      closed enum, zero or more (emphasis, obligation, prohibition, hearsay, ...).
-- usage_contexts_json   closed enum (spoken, written, business, casual-friends, formal-email, ...).
-- steps_unavailable     free text. Set INSTEAD of steps when the record is too vague to give them.
--                       This is a good outcome and deliberately not nullable-by-omission: a point with
--                       neither steps nor a reason is a gap, and the validator says so.
--
-- Layer C, needs_review, like every authored pedagogical field.
ALTER TABLE grammar_point ADD COLUMN formation_steps_json TEXT;
ALTER TABLE grammar_point ADD COLUMN nuance_tags_json TEXT;
ALTER TABLE grammar_point ADD COLUMN usage_contexts_json TEXT;
ALTER TABLE grammar_point ADD COLUMN steps_unavailable TEXT;
