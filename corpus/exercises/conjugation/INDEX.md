# corpus/exercises/conjugation - form-discrimination drills

Roadmap item C. Built by `scripts/export/build_conjugation_exercises.py` from the DETERMINISTIC conjugation bank (`corpus/conjugations`), so every answer key is derived rather than authored: zero AI, Layer B.

An item gives a dictionary form plus a target form name and asks for the conjugated surface. **Distractors are other forms of the SAME word**, which is what makes the item test form discrimination; a distractor from a different verb would be eliminable from the stem alone.

**18524 items** across N3 10599, N4 4853, N5 3072. **1320** carry an `example` slug, a real bank sentence that actually contains the answer surface. The rest do not, and that is the honest state of the roadmap's mining step: only 1,765 of 19,784 possible (word, form) pairs are attested in the sentence bank.

Item: `{id, level, vocab_id, slug, headword, kind, class, prompt, form, form_label, correct, kana, romaji, distractors, example}`.
