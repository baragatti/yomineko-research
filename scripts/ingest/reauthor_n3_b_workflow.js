export const meta = {
  name: 'reauthor-n3-b-accents',
  description: 'Re-author the 12 accent-stripped N3 Tranche-3 lessons with a hard pt-BR accent mandate',
  phases: [{ title: 'Reauthor', detail: 'one agent per contaminated lesson' }],
}

const FILE = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/_n3_lesson_inputs_b.json'
// spec indices of the 12 contaminated lessons (chunk2 [12,18) + chunk4 [24,30))
const INDICES = [12, 13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29]

const CONTRACT = `You are RE-AUTHORING one intermediate (JLPT N3) Japanese lesson for a Brazilian-Portuguese course.
A previous draft of this lesson was rejected because it stripped Portuguese accents. Your output MUST use
flawless, natural Brazilian Portuguese (pt-BR, never pt-PT) with EVERY diacritic in place.

INPUT: Read the JSON array at ${FILE}. Author ONLY the spec at the index given to you. Each spec has:
slug, topic, order, title_pt, theme_pt, review_grammar (grammar ALREADY taught - for example sentences only),
vocab[] ({hw, kana, gloss[]}), kanji[] ({k, meaning[]}). This is a VOCABULARY-EXPANSION lesson: it teaches a
themed batch of new N3 words + a couple kanji, with example sentences and exercises. No NEW grammar.

>>> ACCENT MANDATE (the reason for this re-author) <<<
Write real Brazilian Portuguese. Words that take an accent MUST have it. Watch especially:
- é (verb "ser", e.g. "俳優 é ator") vs e (conjunction "and"). NEVER write "e" when you mean "é".
- está/estão (estar) not "esta/estao"; têm (plural) not "tem" when plural; vêm not "vem" when plural.
- ção/ções/são/sões: função, então, tradução, expressão, profissões, decisão, versão, situação.
- você(s), não, também, já, à, há, três, português, japonês, número, próprio, último, série, área,
  fácil/difícil, útil/úteis, possível, história, memória, período, símbolo, código, vários, espaço,
  esperança, mudança, diferença, começar, conheço, reconheço.
- Demonstrative "esta lição" (this) is correct without accent; "está" (is) needs it. Use each correctly.
Before returning, RE-READ every Portuguese sentence and confirm the accents. This is the acceptance gate.

BODY RULES (strict mini-markup):
- ALL prose inside <text>...</text>. Never put raw text directly under <p>/<item>/<note>/<heading>. Bold = <text weight="bold">...</text>. Italic = <emphasis>...</emphasis>. Do NOT nest <emphasis> inside <text>; make them siblings: <text>antes </text><emphasis>palavra</emphasis><text> depois</text>.
- EVERY example sentence and EVERY stray inline element must live inside a block. Wrap example sentences as <p><jp reading="KANA_COMPLETA">漢字文</jp><text> (tradução pt-BR)</text></p>. Never leave <jp>/<text>/<term> at the body root.
- Structure: <heading level="2"><text>...</text></heading>, an intro <p>, then 2-4 clusters each under <heading level="3"><text>...</text></heading> with a <list ordered="false"> of items.
- Introduce EVERY vocab in spec.vocab EXACTLY ONCE as <vocab ref="vocab:HW"/> (HW = spec.vocab[i].hw verbatim), inside an <item>, followed by its reading + pt-BR meaning: <item><vocab ref="vocab:市"/><text> (いち) - feira, mercado.</text></item>. Each <item> opens and closes cleanly: <item>...</item>.
- Introduce EVERY kanji in spec.kanji EXACTLY ONCE as <kanji ref="kanji:K"/> with its pt-BR meaning.
- Use <vocab ref>/<kanji ref> ONLY for items in THIS spec. No <grammar ref> tags (mention review_grammar patterns as plain <jp> in examples if useful).
- EVERY <jp> containing kanji MUST carry reading="..." with the complete hiragana reading.
- Optional: ONE <note type="..."> (type: l1-pitfall|l1-advantage|tip|culture|note) with <p><text>...</text></p>.
- End with <heading level="3"><text>Hora de praticar</text></heading>, one <exercise ref="EXSLUG"/> per exercise in order, then <checklist> with one <check><text>...</text></check> per objective.
- FORBIDDEN: emoji, the em dash character, backslashes, pt-PT spellings. Use a hyphen "-" or parentheses, never an em dash.

EXERCISES: 4-5 per lesson, MUST include >=1 "recognition" AND >=1 "production". Also use matching/cloze.
- slug = "ex:" + spec.slug-without-"les:" + "-" + n  (e.g. "ex:n3-relato-05-1").
- answer shapes: recognition {"choices":[..],"correct":".."}; matching {"pairs":[["日本語","pt"]]};
  cloze {"text":"peca","full":"完全な文。"}; production {"text":"模範文","accept":["変1","変2"]}.

Return {"lessons":[ ONE lesson object ]} with fields: slug (verbatim), title (pt-BR string), description
(pt-BR string), objectives (array of pt-BR strings), body (string), exercises (array).`

const LESSON_SCHEMA = {
  type: 'object', required: ['lessons'], additionalProperties: false,
  properties: {
    lessons: {
      type: 'array',
      items: {
        type: 'object',
        required: ['slug', 'title', 'description', 'objectives', 'body', 'exercises'],
        additionalProperties: false,
        properties: {
          slug: { type: 'string' }, title: { type: 'string' }, description: { type: 'string' },
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
                prompt: { type: 'string' }, answer: { type: 'object', additionalProperties: true },
                explanation: { type: 'string' },
              },
            },
          },
        },
      },
    },
  },
}

phase('Reauthor')
const results = await parallel(INDICES.map((idx) => () =>
  agent(
    `${CONTRACT}\n\nYour assigned spec index: ${idx}. Read ${FILE}, take specs[${idx}], and author that one ` +
    `lesson with flawless accented pt-BR. Return {"lessons":[<the one lesson>]}.`,
    { label: `reauthor:${idx}`, phase: 'Reauthor', schema: LESSON_SCHEMA }
  ).then(r => (r && r.lessons) ? r.lessons : [])
))

const lessons = results.filter(Boolean).flat()
log(`re-authored ${lessons.length} lessons (target ${INDICES.length})`)
return { lessons }
