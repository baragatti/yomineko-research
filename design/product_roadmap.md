# Product roadmap — what the finished corpus must power, and the data it needs

The corpus is the data layer behind a Brazilian-Portuguese N5→N4 Japanese app. This maps each end-product
deliverable to the data artifacts it requires, marks status (✅ have / 🟡 partial / ⬜ gap), and plans the
remaining enrichment passes. Provenance + confidence are tracked on every generated artifact (Layer A facts,
Layer B derived-verified, Layer C pedagogy; `ai_generated` + `*_confidence` + `source`).

## A. Product deliverables → data needed

| Deliverable | Needs | Status |
|---|---|---|
| **N5 + N4 courses**, Module→Topic→Lesson | `course/` tree; topics placed | ✅ outline (35 topics) · ⬜ lessons (P6) |
| **Lessons**: medium text + rich examples + explanations + exercises | rich tagged-HTML lessons referencing corpus IDs | ⬜ P6 (schema drafted `design/lesson_format.md`) |
| **Verb-conjugation training** (drag-drop pieces) + explanation | conjugation bank ✅ + **per-conjugation example sentences** + exercises | ✅ bank (508) · ⬜ examples+exercises (§C below) |
| **Particle training** (drag-drop) + explanation | particle `function_type` ✅ + per-particle example sentences + exercises | 🟡 (functions ✅; drill items ⬜) |
| **All kanji super-explained + example phrases** | kanji readings ✅ + meanings ✅ + example_words/sentences ✅ + **per-reading compounds & notes** | 🟡 (§D below) |
| **JLPT N5/N4 exam simulation** (no audio/img yet) | item bank: 文字語彙 / 文法 / 読解 question types | ⬜ (§E below) |
| **Sentence-construction games** | dissected sentence bank ✅ (tokens/order/particles) | ✅ data; ⬜ game item shaping |
| **"Find the right kanji/particle" games, visual-novel** | distractor sets + answer keys derivable from corpus graph | 🟡 (graph ✅; distractor gen ⬜) |

## B. Open schema questions (answered from data + sources)

- **Vocab `forms` — per-form meaning?** No. `forms` are **orthographic variants** (573 vocab have >1 kanji
  form), i.e. spellings of the same word; **meaning lives in `senses`** (842/1359 vocab have >1 sense, each
  already glossed `{pt-BR,en}`). The rare case where a *specific kanji spelling* changes nuance (見る/観る/診る)
  is modeled in JMdict as per-sense kanji restrictions (`stagk`) — **planned**: surface `applies_to_forms` on a
  sense when JMdict restricts it. So: keep meaning on senses; do not add per-form meaning.
- **Vocab `pitch` — per-form meaning?** No. Pitch is **phonetic accent**, single per vocab (0 vocab have >1
  pitch reading in our set). Words whose different readings carry different meanings are separate JMdict
  entries. Pitch needs no meaning field.

## C. Verb/adjective conjugation EXERCISE bank (plan — build when P5 resumes)
Goal: ≥5 example sentences per conjugation form per verb, for drag-drop drills + JLPT.
1. **Mine first (SELECTION, high confidence):** every bank sentence already has tokens with `inflection`
   enum + `vocab_id`. Index `(vocab_id, inflection/form) → [sentence_ids]` straight from the bank → real
   Tatoeba examples per verb-form, provenance `tatoeba`, confidence high. (Spec §1.2: selection over generation.)
2. **Fill gaps (GENERATION):** for `(verb, form)` pairs with <5 mined examples, AI-generate i+1 sentences
   using that exact form (flagged `ai_generated:true`, `needs_review:true`, confidence recorded), then dissect
   through the normal engine (so they also enrich the bank).
3. **Exercise items:** from each example, build drag-drop items (scramble the conjugation pieces; answer key =
   the correct form from the deterministic conjugation bank; distractors = other forms of the same verb).
   Store in `corpus/exercises/conjugation/`. Same pattern for adjectives.

## D. Kanji per-reading enrichment (plan)
Have ✅: readings (on/kun/nanori, faithful to KANJIDIC2), meanings `{pt-BR,en}`, `example_words`,
`example_sentences`. Gap 🟡: Jisho-style **per-reading** grouping + pt notes.
- **Reading alignment (mechanical-ish):** align each `example_word`'s kana to the kanji's readings (match
  on/kun reading against the word's reading segment) → group compounds under the reading they use
  (On-compounds vs Kun-compounds). Heuristic; AI-verify ambiguous ones.
- **Per-reading pt note (AI, Layer C):** short pt-BR gloss of what each reading means/when it's used (kun ひ =
  "dia/sol, leitura nativa"; on ニチ = "leitura sino-japonesa, em compostos"). Flag `needs_review`.
- Surface on each `readings[]` entry: `meaning:{pt-BR}`, `compounds:[{word,kana,gloss}]`.

## E. Grammar pedagogy tokenization (plan)
Have ✅: `register[]`, `caution`, `forms[]`+meaning, humanized explanation/formation/nuance (locale-objects).
Gap 🟡: **structured/tokenized** formation + nuance (the user wants machine-usable structure, not only prose).
- `formation_steps[]` (Layer A/B, enum-tagged): ordered build steps, e.g.
  `[{base:"verb", op:"to-te-form"},{op:"append", token:"ください"}]` with an `op` enum
  (to-te-form/to-masu-stem/to-nai-stem/to-dictionary/append/replace-ending/nominalize…). Mechanical for regular
  patterns, AI for irregulars; verify against the conjugation engine.
- `nuance_tags[]` (enum): function tags like emphasis/softening/conjecture/obligation/permission/prohibition/
  hearsay/comparison/cause/condition — complements the prose `nuance`.
- `usage_contexts[]` (enum): spoken/written/business/casual-friends/formal-email…

## F. Sentence structured data (plan)
Have ✅: per-token `pos`/`inflection`/`role`/`gloss`, particle `function_type`, `grammar[]` links, prose
`structure_explanation`. Gap 🟡: a **machine pattern** for construction games/UX:
- `pattern[]` (mechanical from tokens): ordered chunks `[{chunk, role, particle?}]` e.g.
  `[{chunk:"私", role:"topic", particle:"は"},{chunk:"本", role:"object", particle:"を"},{chunk:"読む", role:"verb"}]`
  — derivable from tokens + particle links; drives sentence-construction drag-drop + distractors.
- `clause_structure` (enum): simple / topic-comment / relative-clause / conditional / quote … (AI-light).

## G. JLPT exam-simulation item bank (plan)
- Question archetypes (N5/N4): 漢字読み (kanji→reading), 表記 (word→kanji), 文脈規定 (fill-in vocab), 言い換え
  (paraphrase), 文法選択 (grammar choice), 文の組み立て (sentence ordering), 読解 (short reading).
- Generatable from the graph: stems from the sentence bank; correct answer from corpus; **distractors** from
  same-level siblings (same POS/reading-confusable kanji/related grammar). Store `corpus/exercises/jlpt/` with
  `type`, `level`, `stem_sentence_id`, `answer`, `distractors[]`, `explanation`, provenance+confidence.

## Sentence sources & real:AI balance (researched 2026-06-15; deep-research → `research/second-source-deep-research.md`)
Owner preference: maximize REAL sourced sentences over AI. Findings + decisions:
- **Two REAL sources bundled, both clean-permissive:** **Tatoeba** (CC BY 2.0 FR, biggest, best beginner i+1
  fit) + **JEC Basic** (CC BY 3.0, 4,729 human sentences w/ manual en cross-check — second source added
  2026-06-15). Both allow commercial use + redistribution; neither is share-alike.
- **Rejected after deep research:** **JESC** (subtitles, casual register) is CC BY-SA 4.0 **and** built from
  fan-subtitle crawl → copyleft + upstream-copyright risk; **JParaCrawl** is non-commercial; **OpenSubtitles**
  grants no text rights; **KFTT/NICT-Kyoto** are CC BY-SA + encyclopedic register; **Tanaka** = Tatoeba's
  ancestor (redundant). **LICENSING POLICY (locked, ATTRIBUTION.md):** bundle only CC-BY/CC0 real text; never
  bundle CC BY-SA / copyright-murky prose, and **never use it as an AI generation seed** (a close paraphrase is
  still a derivative) → AI sentences are **clean-room** from our own known-set only.
- **Most "missing" coverage was NOT a real-sentence shortage** — it was (a) a **linking gap** (relink_vocab
  fixed +5604 edges: 青 had 508 raw hits, 2 linked) and (b) **over-filtering** (maxlen 22 / max-new 2). A
  relaxed pass (maxlen 40, max-new 4) over Tatoeba + JEC recovers more REAL sentences for the residual.
- **Order of preference (enforced):** 1) link what we have (relink); 2) mine REAL (Tatoeba then JEC,
  tighten→relax); 3) only then GENERATE clean-room, for the genuine rare tail real sources lack within the
  known-set. AI is flagged `ai_generated`+`needs_review`. **Content filter:** real sources are scanned for
  inappropriate content before persist (`extract_workflow_result.py` keyword scan; 2 JEC sentences dropped).
- **Current balance:** 55% real (2745) / 44% AI (2214) of 4959 — back over half human-written. A content
  blocklist (`research/derived/content_blocklist.json`, gated in `persist()`) permanently drops sentences
  unfit for a learner product; the grammaticality gate drops ungrammatical AI (verdict.faithful=False).

## Provenance & confidence (all generated artifacts)
Every mined item: `source:"tatoeba:<id>"`, confidence high. Every generated item: `ai_generated:true`,
`needs_review:true`, `*_confidence` recorded, `created_by:"ai"`. Distractors/answer-keys derived from Layer-A
facts are marked `derived`. Nothing ships without the teacher-review queue (acceptance #8).

## Sequencing (when work resumes)
P5 deepening (coverage→§10 + generation tail) → conjugation example mining+gaps (§C) → P6 lessons (rich
format) → kanji per-reading (§D) + grammar tokenization (§E) + sentence pattern (§F) → exercise/JLPT/game
item banks (§C/§E/§G) → P7 QA + teacher-review queue.
