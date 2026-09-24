# corpus/exam_banks — JLPT-style question banks (our format)

Per-level, per-type item banks DERIVED from verified corpus facts (vocab readings, real bank sentences, grammar forms) — deterministic types have no AI-generated Japanese; distractors are rule-built (same level/lexeme class, similar length, wrong by construction). Real JLPT papers are © JEES and were used only as FORMAT reference; zero copied text. The app's exam simulator randomly samples these per attempt — picker spec: `design/exam_simulator.md`. Item: {id, level, stem, correct, distractors|pieces, source refs}. Deterministic types are Layer B; the AUTHORED types (`paraphrase`, `usage`, `reading_comp`, `listening_*`) are Layer C (authored + adversarially verified, needs_review). `reading_comp` items reference their passage by `read:` slug — the app renders the passage from `corpus/readings` (single source of truth). `listening_*` items are voice-ready TEXT scripts (speaker-tagged turns, `audio: "pending"` — spec: `design/listening.md`); `listening_reply` prompts are REAL bank sentences verbatim (`sentence` ref).

Every deterministic item is selected against its level's taught set (the `cumulative_known_set` of the last lesson of that level's module): every kanji it prints, its own vocabulary record, and the source sentence's token vocabulary and grammar tags are inside it — the rule `scripts/validate/validate_exam_level_gate.py` measures. `sentence_order` tiles are BUNSETSU and the item carries `accepted[]`, every reordering that means the same thing; the app grades against that list, not against one string. Auto-graded items carry a pt-BR `explanation` assembled from the record (gloss + reading, or the grammar point's label), never free prose.

`removed_items.json` is a withdrawal ledger, not a bank, and is deliberately absent below.

- `n3_context_fill.json` — 337 items
- `n3_grammar_form.json` — 292 items
- `n3_kanji_reading.json` — 400 items
- `n3_listening_gist.json` — 9 items
- `n3_listening_point.json` — 18 items
- `n3_listening_reply.json` — 27 items
- `n3_listening_say.json` — 12 items
- `n3_listening_task.json` — 18 items
- `n3_orthography.json` — 400 items
- `n3_paraphrase.json` — 28 items
- `n3_reading_comp.json` — 152 items
- `n3_sentence_order.json` — 300 items
- `n3_text_grammar.json` — 122 items
- `n3_usage.json` — 33 items
- `n4_context_fill.json` — 318 items
- `n4_grammar_form.json` — 288 items
- `n4_kanji_reading.json` — 400 items
- `n4_listening_point.json` — 21 items
- `n4_listening_reply.json` — 24 items
- `n4_listening_say.json` — 15 items
- `n4_listening_task.json` — 24 items
- `n4_orthography.json` — 400 items
- `n4_paraphrase.json` — 15 items
- `n4_reading_comp.json` — 90 items
- `n4_sentence_order.json` — 300 items
- `n4_text_grammar.json` — 75 items
- `n4_usage.json` — 14 items
- `n5_context_fill.json` — 91 items
- `n5_grammar_form.json` — 71 items
- `n5_kanji_reading.json` — 176 items
- `n5_listening_point.json` — 18 items
- `n5_listening_reply.json` — 17 items
- `n5_listening_say.json` — 15 items
- `n5_listening_task.json` — 21 items
- `n5_orthography.json` — 177 items
- `n5_paraphrase.json` — 9 items
- `n5_reading_comp.json` — 43 items
- `n5_sentence_order.json` — 55 items
- `n5_text_grammar.json` — 34 items
- `n5_usage.json` — 8 items
