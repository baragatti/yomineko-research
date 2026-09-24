# corpus/capabilities — language-feature registry (our format)

The FIXED capability list the daily skill-SRS schedules against (roadmap C/D). Each capability has a `kind` (design/courseware_architecture.md): grammar groups map explicit grammar keys (curated groups; topic-bucket fallback so every grammar point is covered); script, vocabulary, phonology, exam-readiness and study-method capabilities carry none. `can_do` is the first-person pt-BR statement (Layer C, needs_review) with the lesson objectives it was written from quoted in `can_do_derived_from`; `exam_link` says where the exam banks assess it. `lesson_map.json` = capabilities each lesson INTRODUCES (derived from its unlocks plus the W24 rules), and every lesson is in it.

- registry: 125 capabilities (grammar 72, script 3, vocabulary 44, phonology 2, exam-readiness 3, study-method 1)
- lesson_map: 324 lessons
- exam_link: 119 capabilities, 816 rows
