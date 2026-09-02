# Schema v2 — pressure-tested data model (Phase R4)

> Supersedes the **draft** schemas in spec §5. P0 writes the SQLite migrations from THIS file. Every change
> from §5 is justified, mostly by Phase R3 findings ([`reports/source_coverage.md`](../reports/source_coverage.md))
> and the hard-example stress tests in §C below. Design invariants from spec §1 are preserved:
> provenance layers (A/B/C), level-agnostic (§1.6), one cross-referenceable graph by stable ID (§1.7).

---

## A. What changed from spec §5, and why

| # | Change | Why (evidence) |
|---|--------|----------------|
| 1 | **`kanji_reading` is its own table** (not an array inside `kanji`) with `introduced_at_level` per row. | §5.1 requires per-reading tiering; R3 confirms the level lists give kanji-level JLPT only, never per-reading — so the tier must be *derived from the vocab that uses each reading* and stored as a first-class, queryable row (§1.7 asks for "the kun-reading た.べる of 食"). |
| 2 | **`vocab_form` table** for surface variants (kanji form, kana form, okurigana variants, `足/脚`). | R3: ~8% of vocab "missing" was list-formatting variants joined with `;`. Variants must be modeled, not dropped. |
| 3 | **`vocab.lexeme_type` + `base_vocab_id` + affix/counter handling.** | R3: counters (`～本`), prefixes (`お～`), and する-verbs (`コピーする`) are stored differently in JMdict; normalize and link instead of treating as gaps. |
| 4 | **`vocab_sense` table** (pt-BR meaning tied to a specific JMdict sense). | §1.3 separate fact/explanation; JMdict words have multiple senses, each needing its own gloss + POS. |
| 5 | **Sentence provenance split into THREE axes:** `jp_source`, `pt_source`, `audio_source` (+ `pt_validated_against`, `translation_confidence`). | R3 headline: only 1.8% of JP sentences have PT. We **select the Japanese** (Layer A) but **generate the pt-BR** (Layer B) — the translation's provenance is independent of the sentence's, and audio is mostly TTS (2.5% Tatoeba). The single `source` field of §5.4 can't express this. |
| 6 | **`token` stores BOTH split modes** (`split_mode` A/C) with `parent_token_id` linking mode-A subunits to their mode-C word. | §3.6 wants A+C; the "one word built from these parts" teaching needs the parent link. |
| 7 | **Level reconciliation fields standardized**: `level`, `level_confidence` (0–1), `level_agreement` (`"2/3"`), `level_sources[]` on every leveled entity. | §1.5 consensus-based leveling across ≥3 lists. |
| 8 | **Explicit link tables** for every graph edge (sentence↔vocab/kanji/grammar with per-link notes, kanji-component graph, grammar contrasts, group membership, lesson/exercise refs). | §1.7 graph + the by-ID rule (§5.5 hard rule: courseware holds IDs only). |
| 9 | **`pitch_accent` modeled per reading** (array of accent positions), not a scalar. | Words can have multiple accepted accents; speaking focus (§3.7). |

**Unchanged in spirit:** the three courseware entities (`course_module → topic → lesson`), the `group`
(family) model, and the dissection standard (§6) — all carried over, now with concrete relational backing.

---

## B. Entity catalogue (v2)

Conventions: every row has `id` (stable, text, prefixed: `kanji:食`, `vocab:1234`, `gram:te-form`,
`sent:tatoeba-7421`, `grp:godan`, `mod:n5`, `top:n5-particles`, `les:...`, `ex:...`). Every content row has
`source` (provenance string), `created_by` (`dataset`|`ai`|`human`), `layer` (`A`|`B`|`C`), `needs_review`
(bool). Leveled rows add `level`, `level_confidence`, `level_agreement`, `level_sources` (json array).

### kanji
```
id, character, strokes, grade, freq_rank,
unicode_cp, kanjivg_ref, kangxi_radical,
meanings_pt[]            # Layer B (from KANJIDIC2 EN)
meanings_en[]            # Layer A cross-check
level, level_confidence, level_agreement, level_sources
notes_pt                 # Layer C, optional
+ standard provenance fields
```

### kanji_reading   ← NEW table
```
id, kanji_id (FK), reading, reading_type (on|kun|nanori),
okurigana,               # e.g. "べる" for た.べる
introduced_at_level,     # n5|n4|n3|... derived from example vocab
level_confidence, level_sources,
example_vocab_ids[]      # vocab using THIS reading at THAT level
```

### kanji_component   ← NEW link (kanji↔radical/kanji graph, from Kradfile)
```
kanji_id (FK), component (char/radical), component_kanji_id (FK nullable)
```

### vocab
```
id, headword,            # primary written form (kanji if any, else kana)
kana, romaji,
lexeme_type,             # word | suru_verb | counter | prefix | suffix | expression | aux
base_vocab_id,           # for suru_verb -> the noun; for derived -> base (nullable)
verb_class,              # ichidan | godan | suru_irregular | kuru_irregular | null
adj_class,               # i_adj | na_adj | null
common, freq_rank,
jmdict_ref,              # JMdict ent_seq
level, level_confidence, level_agreement, level_sources,
notes_pt,                # Layer C optional
+ provenance
```

### vocab_form   ← NEW (surface variants + counter phonetics)
```
id, vocab_id (FK), form, is_kana (bool), is_common (bool), is_primary (bool),
applies_to_reading,      # which kana reading this written form maps to
variant_condition        # json, e.g. counters: {"after_numbers":[1,6,8,10],"reading":"ぽん"}
```

### vocab_sense   ← NEW
```
id, vocab_id (FK), sense_order,
pos[],                   # JMdict POS for this sense
field_tags[], misc_tags[],
gloss_en[],              # Layer A
gloss_pt[]               # Layer B (validated against EN)
```

### vocab_pitch   ← NEW (optional, speaking focus)
```
id, vocab_id (FK), reading, accent_positions[]   # mora index(es) of the drop
```

### grammar_point
```
id, key, label_pt,
structure_pattern,       # formal pattern, e.g. "Vて + います"
register,                # neutral | polite | casual | formal(keigo)
explanation_pt,          # Layer C, original
formation_pt,            # Layer C
nuance_pt,               # Layer C — when/why + pitfalls for PT speakers
level, level_confidence, level_agreement, level_sources,
references[],            # consulted (NOT copied)
needs_review (default true),
+ provenance (layer=C)
```

### grammar_related   ← link (contrasts/links)
```
grammar_id (FK), related_grammar_id (FK), relation   # contrast | builds_on | variant
```

### sentence
```
id, jp, kana, romaji,
pt,                      # Layer B (generated, natural pt-BR)
pt_literal,              # Layer B (gloss-level)
en,                      # Layer A cross-check (Tatoeba EN if linked)
level,                   # = max(level of component items)
intro_topic_id,          # where first used (nullable until P6)
jp_source,               # tatoeba:<id> | ai_generated      (provenance of the Japanese)
pt_source,               # ai | tatoeba | human             (provenance of the translation)
pt_validated_against,    # en | dict | both | none
translation_confidence,  # 0..1
audio_ref, audio_source, # tatoeba:<audioId> | tts:<voice> | none
structure_explanation_pt,# Layer C
difficulty,              # numeric (length, rare items, grammar load)
tags[],                  # greetings|shopping|work|...
register,                # ONE value from the set below (§B.register) — Layer B
register_flags[],        # orthogonal content warnings, 0..n — Layer B
register_confidence,     # 0..1
register_evidence,       # one line: the token / JMdict tag / ending that decided it
flags: ai_generated, needs_review, verified
+ provenance
```

#### sentence.register — the D7 value set (A8, added 2026-09-02 for W31)

**Why the field exists.** Selection into the speaking path is mechanical (seed lemma + known set),
so nothing could tell a polite request from a Bible verse: `course/speak/` shipped 心熱けれど肉体は弱し
as a production prompt, お前は脳の半分があったら，危ない! as a drill, and 痔があります in `health`.
`vocab.register` is a word-level JMdict tag and exports null; grammar points carry a multi-value
`register`, which is a property of the *point*, not of a sentence. This is the sentence-level one.

**Exactly one primary register per sentence** — the register a learner would hear the whole
utterance in. Values are neutral English enums (locale-agnostic, spec §1 "internals are
language-AGNOSTIC"); the pt-BR label lives in the UI locale module, never here.

| value | definition (one line) | example from the bank |
|---|---|---|
| `neutral` | plain form, unmarked for politeness or intimacy: expository or narrative, no stance toward a listener | 兄は背が高いが弟は低い (`sent:gen-43ac7e47316c`) |
| `polite` | です／ます (or a fixed polite set phrase) addressed to a listener, no keigo | あれはキジです (`sent:tatoeba-229742`) |
| `casual` | plain form **plus** a marker of informal speech: 〜ぜ／ぞ／な／わ／かしら, soft よ／ね／の, 〜てる／〜ちゃう contractions, お前／あんた, colloquial って | 学校は何時に終わるの？ (`sent:tatoeba-10206436`) |
| `formal` | keigo or written-formal: 伺う／申す／いたす／拝見, ご〜になる, ございます outside a fixed greeting, である | 係の者がご案内いたします (`sent:gen-64fec9fcc687`) |
| `vulgar` | carries a JMdict `vulg`/`X` lexeme or a coarse address form (てめえ／貴様) | ちくしょう！わるくないなあ！ (`sent:tatoeba-135763`) |
| `archaic` | classical morphology no longer productive: clause-final 〜し／〜べし／〜けり, 〜たまえ, 候 | 心熱けれど肉体は弱し (`sent:tatoeba-145552`) |
| `epistolary` | letter or formal-notice formulae: 拝啓／敬具／前略／草々／取り急ぎ／〜の候 | none in the bank today — the value is defined so the filter can reject one on arrival |
| `dialect` | non-standard regional forms: JMdict `ksb`/`osb`/`kyu`…, あかん／おおきに／ほんま, clause-final 〜やねん／〜だべ | おおきに！ (`sent:tatoeba-9462381`) |
| `slang` | current in-group vocabulary, JMdict `sl`: めっちゃ, やばい, きもい | これ触ってみて。めっちゃ柔らかいよ。 (`sent:tatoeba-3718388`) |

**Precedence when several fire** (a single value must come out): `epistolary` → `archaic` →
`vulgar` → `dialect` → `slang` → `formal` → `polite` → `casual` → `neutral`. A vulgar lexeme
outranks です／ます because it is what the listener reacts to; `polite` outranks `casual` because
the です／ます frame sets the relationship.

**`register_flags[]` — orthogonal content warnings**, independent of the register and of each
other. A sentence may carry none or several. They describe *content*, never politeness:

`insult` (JMdict `derog` or an abusive lexeme: 無能, ばか, あいつ) · `sexual` (JMdict `X`/`vulg`
or explicit vocabulary) · `violence` (殺す, 殴る, 戦争, 自殺) · `stereotype` (a demonym
topicalised or generalised — 日本人は…, ドイツ人はとてもずる賢い) · `medical-intimate` (痔, 生理,
性病) · `proper-name` (a 固有名詞 token: a person, place or brand a learner has no reason to drill).

**Layer and review.** `register` is **Layer B** — derived from Layer-A material (JMdict misc tags,
Sudachi morphology) and machine-validated, never free authoring. The deterministic first pass is
`scripts/derive_sentence_register.py`; anything it decides on absence of evidence, or on a
grammar point's authored register, carries `register_confidence < 0.8` and `needs_review: true`
for the LLM pass and the teacher queue. `register_evidence` must name the deciding token, tag or
ending, so a reviewer can check the call without re-reading the sentence.

**The lessons never filter on it (A8, owner: "yes; must not impact the lessons").** `register` is
consumed by the **speaking path only** — `scripts/export/build_speaking_path.py` and the drill,
production and fluency selectors under it, including `drills[].examples`. `course/` lesson
selection, exercise generation and the exam banks must produce byte-identical output with the
field present and absent; that is the gate on W31. Corpus consumers may read it; no courseware
builder outside `course/speak/` may branch on it.

### token   ← (skeleton from SudachiPy; glosses from LLM)
```
id, sentence_id (FK), position, split_mode (A|C),
parent_token_id,         # mode-A subunit -> its mode-C word (nullable)
surface, lemma, reading, romaji,
pos_coarse, pos_fine,    # SudachiPy POS (immutable, Layer A)
role_pt,                 # topic marker | subject | direct object | main verb | ...
gloss_pt,                # in-context meaning, Layer B
conjugation_note_pt,     # e.g. "forma ます de 食べる"; for 来る: realized reading き/こ
vocab_id (FK, nullable), # null for pure inflection/particle
kanji_ids[]
```
> **Immutability rule (§7.2):** `surface/lemma/reading/pos_*/split_mode/position` come from the analyzer and
> may NOT be altered by the LLM; only `role_pt/gloss_pt/conjugation_note_pt` are LLM-authored (Layer B).

### particle   ← (per-sentence, the raw material for particle drills)
```
id, sentence_id (FK), token_id (FK), particle,
function_pt,             # Layer B/C
explanation_pt           # Layer C — why THIS particle HERE
```

### group  (family / cluster)  +  group_member
```
group:  id, type, label_pt, description_pt, importance_rank,
        governing_rule_pt, spans_levels[], primary_module_id,
        + provenance (layer=C)
group_related:  group_id, related_group_id, relation   # contrast_pair | sub_family
group_member:   group_id (FK), member_type (kanji|vocab|grammar), member_id,
                intra_order, is_core (bool), note_pt
```

### Courseware: course_module → topic → lesson → exercise
```
course_module: id, level (pre-n5|n5|n4|...), order, title_pt, overview_pt, + provenance(C)
topic:         id, module_id (FK), order, title_pt, theme_pt, family_ids[],
               objectives_pt[], prerequisites[] (topic ids), + provenance(C)
lesson:        id, topic_id (FK), order, title_pt, objectives_pt[],
               prerequisites[] (lesson ids), body_pt (DENSE Layer C),
               cumulative_known_set (computed json), needs_review(default true), + provenance(C)
exercise:      id, lesson_id (FK), order, type, prompt_pt, answer (json), explanation_pt
               # type ∈ recognition|cloze|particle_choice|sentence_build|reading|listening|production|matching
```
Link tables (enforce the by-ID rule — courseware NEVER embeds corpus content):
```
lesson_introduces(lesson_id, member_type[kanji|vocab|grammar], member_id)
lesson_sentence(lesson_id, sentence_id)            # sentence_refs[] BY ID
exercise_sentence(exercise_id, sentence_id)
exercise_item(exercise_id, member_type, member_id)
```

### The graph edges (link tables powering §1.7)
```
sentence_vocab(sentence_id, vocab_id, usage_note_pt)
sentence_kanji(sentence_id, kanji_id)
sentence_grammar(sentence_id, grammar_id, usage_note_pt)
vocab_kanji(vocab_id, kanji_id, position)
# plus kanji_component, grammar_related, group_member, group_related, lesson_*, exercise_* above
```

---

## C. Hard-example stress tests (does the schema hold?)

### C1. Kanji with readings split across N5/N4 — 生
```
kanji: {id:"kanji:生", character:"生", strokes:5, grade:1, level:"n5", level_agreement:"3/3"}
kanji_reading:
  {kanji_id:"kanji:生", reading:"せい", type:"on",  introduced_at_level:"n5",
     example_vocab_ids:["vocab:学生","vocab:先生"]}
  {kanji_id:"kanji:生", reading:"なま", type:"kun", introduced_at_level:"n4",
     example_vocab_ids:["vocab:生"]}
  {kanji_id:"kanji:生", reading:"い", type:"kun", okurigana:"きる", introduced_at_level:"n4",
     example_vocab_ids:["vocab:生きる"]}
  {kanji_id:"kanji:生", reading:"う", type:"kun", okurigana:"まれる", introduced_at_level:"n4",
     example_vocab_ids:["vocab:生まれる"]}
```
✔ Same character, four readings, three different intro tiers — each independently queryable. The kanji's own
`level` (n5) is the *earliest* of its readings.

### C2. Stacked particles + contracted verb form (illustrative)
`学校へは歩いて行かなくちゃ。` ("[I] have to walk to school.") — `へは` (stacked へ+は), te-form `歩いて`,
contraction `行かなくちゃ` ← `行かなくては` ← `行かなければ`.
```
tokens (mode C): 学校 | へ | は | 歩い(=歩く,te) | て | 行か(=行く) | なくちゃ | 。
particles: {へ, function_pt:"direção/destino"} ; {は, function_pt:"tópico/contraste — realça 'à escola'"}
   -> two particle rows on the SAME nominal slot (stacked) — allowed, both link distinct token_ids.
grammar: {gram:te-form on 歩いて}, {gram:~なければならない, usage_note_pt:"contração casual なくちゃ"}
token(行か).conjugation_note_pt: "base negativa de 行く + なくちゃ (contração de なければ)"
sentence.structure_explanation_pt: walks topic+direction+te-linking+obligation-contraction.
```
✔ Stacked particles = multiple `particle` rows; contraction captured in `conjugation_note_pt` +
`grammar_related(relation:variant)` from なくちゃ → なければならない. (Stored illustratively; real corpus rows
come from Tatoeba selection.)

### C3. Contrast pair は vs が as a family
```
group: {id:"grp:wa-vs-ga", type:"contrast_pair", label_pt:"は (tópico) vs が (sujeito)",
        governing_rule_pt:"は marca o tópico/o já conhecido; が marca o sujeito/o novo ...",
        importance_rank: 3, spans_levels:["n5","n4"], primary_module_id:"mod:n5"}
group_member: {grp:wa-vs-ga, grammar, gram:wa-topic, intra_order:1, is_core:true}
group_member: {grp:wa-vs-ga, grammar, gram:ga-subject, intra_order:2, is_core:false}
group_related: {grp:wa-vs-ga, grp:particles-core, relation:"sub_family"}
```
✔ A contrast pair is a `group` of type `contrast_pair` whose members are grammar points.

### C4. Derivational word family 食べる → 食べ物 → 食事 (+ multi-membership)
```
group: {id:"grp:taberu-family", type:"word_family", label_pt:"Família de 食べる (comer)", importance_rank:12}
group_member: {grp:taberu-family, vocab, vocab:食べる, intra_order:1, is_core:true,
               note_pt:"verbo base (ichidan)"}
group_member: {grp:taberu-family, vocab, vocab:食べ物, intra_order:2, is_core:false, note_pt:"nominalização 'comida'"}
group_member: {grp:taberu-family, vocab, vocab:食事,   intra_order:3, is_core:false, note_pt:"composto on'yomi 'refeição'"}
# 食べる ALSO belongs to the conjugation class family:
group_member: {grp:ichidan-verbs, vocab, vocab:食べる, intra_order:1, is_core:true}
```
✔ `食べる` is a member of TWO groups (word_family + conjugation_class) — exactly the multi-membership §5.6 wants.

### C5. Counter ～本 (rendaku phonetic variants)
```
vocab: {id:"vocab:counter-hon", headword:"本", kana:"ほん", lexeme_type:"counter",
        level:"n5", notes_pt:"contador de objetos longos e cilíndricos"}
vocab_form (phonetic conditions):
  {form:"ほん", variant_condition:{after_numbers:[2,3,4,5,7,9],   reading:"ほん"}}
  {form:"ぼん", variant_condition:{after_numbers:[3],            reading:"ぼん"}}   # 3本 さんぼん
  {form:"ぽん", variant_condition:{after_numbers:[1,6,8,10],      reading:"ぽん"}}   # 1本 いっぽん
group: {id:"grp:counters", type:"function_set", label_pt:"Contadores (助数詞)", governing_rule_pt:"rendaku ..."}
group_member: {grp:counters, vocab, vocab:counter-hon, ...}
```
✔ `variant_condition` on `vocab_form` captures number-conditioned rendaku — a case the flat §5.2 array
couldn't express.

### C6. Irregular verbs する / 来る (reading shifts on conjugation)
```
vocab: {id:"vocab:する", headword:"する", kana:"する", verb_class:"suru_irregular", lexeme_type:"word"}
vocab: {id:"vocab:勉強する", headword:"勉強する", lexeme_type:"suru_verb", base_vocab_id:"vocab:勉強",
        verb_class:"suru_irregular"}     # normalization: 勉強する = 勉強(noun) + する
vocab: {id:"vocab:来る", headword:"来る", kana:"くる", verb_class:"kuru_irregular"}
kanji_reading (来): {reading:"く", type:"kun", note:"realizada como き/こ na conjugação"} introduced_at_level:"n5"
# realized reading lives on the TOKEN, not the inventory:
token(来ます).reading:"きます", conjugation_note_pt:"来る → 来(き)ます (a leitura muda na flexão)"
token(来ない).reading:"こない", conjugation_note_pt:"来る → 来(こ)ない"
group: {id:"grp:irregular-verbs", type:"conjugation_class", governing_rule_pt:"する e 来る ...", importance_rank:6}
```
✔ Irregular reading shift is captured by separating **reading inventory** (`kanji_reading`) from **realized
reading** (`token.reading` + `conjugation_note_pt`). する-compounds normalized via `base_vocab_id`.

---

## D. SQLite realization notes (for P0)
- One migration file per logical group under `scripts/ingest/migrations/` (`001_kanji.sql`, …), idempotent
  (`CREATE TABLE IF NOT EXISTS`), each table with the standard provenance columns.
- Array fields (`*_pt[]`, `*_sources`, `tags[]`) stored as **JSON text** columns (SQLite `json1`); link tables
  used for anything that must be *queried/joined* (the graph edges), JSON only for display-only lists.
- **Indexes** (so the §1.7 sample queries are O(log n)): `sentence_vocab(vocab_id)`,
  `sentence_grammar(grammar_id)`, `sentence(level)`, `token(lemma)`, `token(vocab_id)`,
  `kanji_reading(kanji_id)`, `vocab_kanji(kanji_id)`, `group_member(group_id, member_type)`,
  `group_member(member_id)`.
- **FTS5** virtual table over `sentence.jp` (and a `token_lemma` index) per §7 so "sentences containing lemma X"
  is fast during P5 selection.
- `cumulative_known_set` per lesson = a computed/materialized table rebuilt by an export script (not hand-kept).

### §1.7 query feasibility check (all expressible)
- *"All N5 sentences with a godan verb from daily-routine family AND を"* →
  `sentence JOIN sentence_grammar(を) JOIN sentence_vocab JOIN group_member(grp:godan) JOIN group_member(grp:daily-routine) WHERE sentence.level='n5'`. ✔
- *"Every vocab using kun-reading た.べる of 食, with dissected sentences"* →
  `kanji_reading(reading=た, okurigana=べる, kanji:食) -> example_vocab_ids -> sentence_vocab -> sentence`. ✔
- *"All members of the 言-component family across N5–N4 by frequency"* →
  `kanji_component(component=言) JOIN kanji ORDER BY freq_rank`. ✔
- *"Every grammar point that contrasts with は, with examples"* →
  `grammar_related(relation=contrast, related=gram:wa-topic) JOIN sentence_grammar`. ✔

## E. Open schema questions — RESOLVED by owner (2026-06-13)
1. **ID style:** ✅ **surrogate `id` + unique `slug`** (avoids homograph collisions like はし=橋/箸). The
   readable composite forms shown in §B/§C are illustrative slugs; the canonical key is an opaque surrogate.
2. **Pitch accent:** ✅ **include the data** for N5/N4 — populate `vocab_pitch` from a pitch-accent dataset
   (source + license recorded in P1). **Audio is deferred** (`audio_ref`/`audio_source` stay empty for now).
3. **Romaji:** ✅ **store it** — `romaji` is a **populated** column on `vocab`, `sentence`, and `token`
   (Hepburn, derived from kana at ingestion via a romanizer, e.g. cutlet/pykakasi). Kana stays canonical; both
   travel together so the app can toggle or run a romaji-first wean.

---

## As-built addendum (2026-06-15) — final exported shapes

The corpus export (`scripts/export/export_corpus.py`) reflects these final conventions. **All localized text is
a locale-object** `{"pt-BR": <content>, "en": <Layer-A source where it exists>}`; mechanical fields are
neutral-English enums derived from Sudachi/JMdict (Layer A).

**Sentence tokens** carry mechanical grammar (no AI): `pos` (noun/verb/i-adjective/na-adjective/adverb/
particle/auxiliary/pronoun/…), `inflection` (continuative/irrealis/terminal/attributive/conditional/
imperative/volitional/stem), raw `inflection_type` (Sudachi 活用型), plus authored locale-objects `gloss`/
`role`/`conjugation_note`. **Particles** carry `function_type` (case/binding/conjunctive/sentence-final/
adverbial/nominalizer) + authored `function`/`explanation`.

**Vocab**: `gloss` = `{pt-BR,en}` per sense; `register` = neutral enum array from JMdict misc
(colloquial/slang/vulgar/honorific/humble/polite/familiar/archaic/…); `forms` are orthographic variants
(meaning lives on senses, not per-form); `pitch` is phonetic (no meaning).

**Kanji**: `meanings` = `{pt-BR,en}`; `readings[]` carry `common` (nanori=false); `example_words[]`
(vocab using the kanji, kana+gloss) and `example_sentences[]` (slugs).

**Grammar**: `label`/`explanation`/`formation`/`nuance` are locale-objects (humanized, Layer C); `register`
is a multi-value enum array (plain/casual/polite/formal/written/honorific/humble/colloquial/literary/dated/
masculine/feminine/slang); `caution` (none/rough/offensive/sensitive); `forms[]` = `{form, meaning:{pt-BR}}`.

**Conjugation bank** `corpus/conjugations/{n5,n4}.json` (deterministic, Layer A): per verb/adjective, each
form `{form, surface, kana, romaji}`; neutral form-key enums (VERB_FORMS / ADJ_FORMS in `conjugate.py`).

**Provenance**: every sentence has `jp_source` + `provenance{ai_generated, needs_review, tier, locale,
translation_confidence}`. Generated sentences are `ai_generated:true` + `needs_review:true` and pass a
grammaticality gate (dissection agent `faithful`; ungrammatical AI dropped). No em dash in any authored text.

**Pipeline (replay-safe):** durable AI output = `research/derived/*_result.json`; `replay_all.py` rebuilds the
whole bank from them at zero token cost (re-derives skeleton + relink_vocab + particle_link + repair_glosses).
Validators: `validate.py` (§7), `integrity_audit.py` (full-stack cross-checks), `graph_queries.py` (§1.7).

## W40 addendum (2026-09-02) — `translation_layer` on `sentence`

One field is added to the sentence record. It carries no content: it says which **provenance layer** the
English in `translation` came from, because the exporter coalesces two storage locations into one key and the
distinction is lost on the way out.

```jsonc
"translation":       { "pt-BR": "…", "en": "…" },   // unchanged
"translation_layer": { "en": "A" }                  // NEW, optional, sibling
```

- **Type:** `LocaleLayerMap` — a new `$defs` entry in `contracts/common.schema.json`, an object keyed by
  locale whose values `$ref` the existing `Layer` enum. **No new enum.**
- **Emitted iff** `translation` has an `en` key. `"A"` when the `sentence.en` column holds it (Tatoeba/JEC
  verbatim, 3,529 records); `"B"` when it comes from a `localized_text` row (derived English, 2,342);
  absent for the 18 anchorless records.
- **`pt-BR` gets no key.** Its layer is a constant `B` for this field, and constants live in the scope table,
  not in 5,889 copies.
- **`sentence.translation` is the only field in the corpus that mixes layers.** Every `localized_text` row
  with `locale='en'` is `layer='B'` without exception (109,976 rows, 15 field pairs), and the three Layer-A
  registry fields (`kanji.meanings`, `vocab.senses[].gloss`, `kanji.example_words[].gloss`) read a dedicated
  column with no derived fallback. So no other entity gets a `*_layer` sibling, and none should until a
  measurement says a second field has started mixing.

The full shape rationale, the exporter rule, the locale scope table it belongs to, and the
`validate_locale_parity.py` spec are in [`i18n.md`](i18n.md) (W40 sections). This entry exists so the data
model catalogue is not silently behind the contract.
