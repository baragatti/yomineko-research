# corpus/exercises/roles - which part plays which grammatical role

Built by `scripts/export/build_role_exercises.py` from the mechanical sentence patterns (roadmap F). Every answer is DERIVED from the particle that closes the chunk, so the bank is Layer B: no AI, no judgement.

**Why this and not a word-order drill.** Japanese word order is flexible, so an auto-graded reassembly item cannot tell the learner which of several correct orders it wanted - a defect the existing `sentence_order` bank has. Role identification has exactly one answer, and it teaches the idea the ordering drill only gestures at: Japanese marks grammatical role with a PARTICLE, not with position, which is the hardest single adjustment for a Portuguese speaker whose L1 marks role by position.

**5358 items** across N3 2710, N4 2409, N5 239.

A role is only asked about when it occurs EXACTLY ONCE in the sentence; two を chunks would mean two defensible answers.

`ni-phrase`, `de-phrase` and `to-phrase` are never targets - they exist because に, で and と are ambiguous, so asking for them would test reading the particle off the page rather than understanding a role. They remain as distractors, where they are honest.

Roles come from the (particle, function_type) PAIR, never the particle surface: から/case is an origin but から/conjunctive means 'porque', の/case links nouns but の/nominalizer modifies nothing, and が/conjunctive is 'mas' rather than a subject. An earlier build read the surface alone and shipped 319 items calling every と 'companhia ou par', quotatives and conditionals included.
