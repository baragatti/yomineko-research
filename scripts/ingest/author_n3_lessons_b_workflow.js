export const meta = {
  name: 'author-n3-lessons-b',
  description: 'Author 47 N3 vocabulary-expansion lessons (Tranche 3) from _n3_lesson_inputs_b.json',
  phases: [{ title: 'Author', detail: 'one agent per ~6 lesson specs' }],
}

const FILE = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/_n3_lesson_inputs_b.json'
const TOTAL = 47
const CHUNK = 6

const CONTRACT = `You are authoring intermediate (JLPT N3) Japanese lessons for a Brazilian-Portuguese course.
Learner-facing text is ALWAYS natural Brazilian Portuguese (pt-BR, never pt-PT), warm and clear, for an adult
who already finished N5+N4. These are VOCABULARY-EXPANSION lessons: each teaches a themed batch of new N3
words (and a couple of kanji), with example sentences and exercises. No NEW grammar is introduced.

INPUT: Read the JSON array at ${FILE}. It is a list of lesson specs. You author ONLY the specs in your
assigned index range. Each spec has: slug, topic, order, title_pt (parent theme), theme_pt, review_grammar
(grammar ALREADY taught in this topic, for example sentences only), vocab[] ({hw, kana, gloss[]}), kanji[]
({k, meaning[]}).

For EACH assigned spec output one lesson object with these fields:
- slug: copy the spec.slug VERBATIM (e.g. "les:n3-conectores-05").
- title: a SPECIFIC pt-BR title for THIS lesson's word-set (NOT just the topic name). Plain string.
- description: 1 sentence, pt-BR, what words this lesson teaches. Plain string.
- objectives: array of 2-3 short pt-BR strings ("Reconhecer e usar ...").
- body: an XML-ish string (rules below).
- exercises: array of 4-5 exercise objects (rules below).

BODY RULES (this exact mini-markup; the renderer is strict):
- ALL prose lives inside <text>...</text>. Never put raw text directly under <p>/<item>/<note>/<heading> without a <text> (or other inline tag) wrapper. Bold = <text weight="bold">...</text>. Italic = <emphasis>...</emphasis>.
- Structure: open with <heading level="2"><text>...</text></heading> then an intro <p>. Group the words into 2-4 semantic clusters, each under <heading level="3"><text>...</text></heading>.
- Introduce EVERY vocab in spec.vocab EXACTLY ONCE using <vocab ref="vocab:HW"/> where HW is the spec.vocab[i].hw string EXACTLY (e.g. <vocab ref="vocab:何れ"/>). Around it, give the reading and the pt-BR meaning in your own words, e.g.: <item><vocab ref="vocab:市"/><text> (いち) - feira, mercado de rua.</text></item>. Put words in <list ordered="false"> clusters.
- Introduce EVERY kanji in spec.kanji EXACTLY ONCE using <kanji ref="kanji:K"/> where K is spec.kanji[i].k (e.g. <kanji ref="kanji:政"/>), with its meaning in pt-BR.
- Use <vocab ref> / <kanji ref> ONLY for items in THIS spec's lists. Do NOT reference vocab/kanji/grammar that are not in this spec.
- Example sentences: write them as <jp reading="FULL_KANA">漢字かな文</jp> followed by <text>(tradução pt-BR)</text>. EVERY <jp> that contains any kanji MUST carry reading="..." with the COMPLETE hiragana reading of the whole string. You MAY use review_grammar patterns in example sentences (plain, inside <jp>), but do NOT add <grammar ref> tags.
- You MAY add ONE short <note type="..."> with type one of: l1-pitfall, l1-advantage, tip, culture, note. Inside it use <p><text>...</text></p>.
- A <term define="definição curta em pt-BR">palavra</term> may wrap a tricky term once.
- End the teaching part with <heading level="3"><text>Hora de praticar</text></heading> then one <exercise ref="EXSLUG"/> per exercise (in order), then a final <checklist> with one <check><text>...</text></check> per objective.
- FORBIDDEN: emoji, the em dash character, backslashes, pt-PT spellings. Keep ALL Portuguese accents (ç, ã, õ, á, é, í, ó, ú, â, ê, ô). Use a normal hyphen "-" or parentheses instead of em dashes.

EXERCISE RULES:
- 4 to 5 per lesson. MUST include >=1 of type "recognition" (a multiple-choice retrieval check) AND >=1 of type "production". Recommended mix: recognition, matching, cloze, production.
- slug: "ex:" + spec.slug-without-"les:" + "-" + n, e.g. for les:n3-conectores-05 use "ex:n3-conectores-05-1", "...-2", etc.
- prompt: pt-BR string (may embed <jp>漢字</jp> inline, with ＿＿ for blanks in cloze).
- explanation: 1 short pt-BR string.
- answer by type (exact shapes):
  - recognition: {"choices":["...","...","..."],"correct":"..."}  (correct MUST be one of choices)
  - matching: {"pairs":[["日本語","pt"],["日本語","pt"]]}  (2-5 pairs)
  - cloze: {"text":"missing_piece","full":"完全な文。"}
  - production: {"text":"模範解答の文", "accept":["変form1","変form2"]}
- Exercises should drill the words THIS lesson taught (use the new vocab/kanji), not grammar theory.

Return your assigned lessons. Be rigorous: valid markup, every assigned vocab+kanji introduced exactly once, every <jp> with kanji has a full reading, natural pt-BR throughout.`

const LESSON_SCHEMA = {
  type: 'object',
  required: ['lessons'],
  additionalProperties: false,
  properties: {
    lessons: {
      type: 'array',
      items: {
        type: 'object',
        required: ['slug', 'title', 'description', 'objectives', 'body', 'exercises'],
        additionalProperties: false,
        properties: {
          slug: { type: 'string' },
          title: { type: 'string' },
          description: { type: 'string' },
          objectives: { type: 'array', items: { type: 'string' } },
          body: { type: 'string' },
          exercises: {
            type: 'array',
            items: {
              type: 'object',
              required: ['slug', 'type', 'prompt', 'answer', 'explanation'],
              additionalProperties: false,
              properties: {
                slug: { type: 'string' },
                type: { type: 'string', enum: ['recognition', 'matching', 'cloze', 'production', 'particle_choice'] },
                prompt: { type: 'string' },
                answer: { type: 'object', additionalProperties: true },
                explanation: { type: 'string' },
              },
            },
          },
        },
      },
    },
  },
}

phase('Author')
const ranges = []
for (let start = 0; start < TOTAL; start += CHUNK) {
  ranges.push([start, Math.min(start + CHUNK, TOTAL)])
}

const results = await parallel(ranges.map(([start, end]) => () =>
  agent(
    `${CONTRACT}\n\nYour assigned index range: author specs[${start}] through specs[${end - 1}] (inclusive). ` +
    `Read ${FILE}, take exactly those ${end - start} specs in order, and author one lesson each. ` +
    `Return {"lessons":[...]} with the lessons in the same order as the specs.`,
    { label: `author:${start}-${end - 1}`, phase: 'Author', schema: LESSON_SCHEMA }
  ).then(r => (r && r.lessons) ? r.lessons : [])
))

const lessons = results.filter(Boolean).flat()
log(`authored ${lessons.length} lessons (target ${TOTAL})`)
return { lessons }
