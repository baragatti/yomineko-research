export const meta = {
  name: 'yomineko-generate',
  description: 'Generate i+1 example sentences for undercovered vocab/grammar targets (ai_generated)',
  phases: [{ title: 'Generate', detail: 'one agent per group writes natural beginner sentences per target' }],
}

const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const DIR = A.dir
const N = A.count || 1
log('generate: groups=' + N + ' DIR=' + DIR)

const SENT = {
  type: 'object',
  properties: {
    ref: { type: 'string' },            // echo: vocab_id (as string) or grammar key
    sentences: {
      type: 'array',
      items: {
        type: 'object',
        properties: { jp: { type: 'string' }, pt: { type: 'string' } },
        required: ['jp', 'pt'],
      },
    },
  },
  required: ['ref', 'sentences'],
}
const SCHEMA = { type: 'object', properties: { results: { type: 'array', items: SENT } }, required: ['results'] }
const pad = (i) => String(i).padStart(4, '0')

const groups = await parallel(
  Array.from({ length: N }, (_, i) => i).map((i) => () =>
    agent(
      `Write natural example sentences in Japanese for a Brazilian-Portuguese N5/N4 course. Use the Read tool
on \`${DIR}/group_${pad(i)}.json\` — a JSON array of TARGETS. Each is either a vocab word (kind:"vocab", with
word/kana/meaning/verb_class) or a grammar point (kind:"grammar", with key/pattern/forms/label), plus "need"
(how many sentences are still missing).

For EACH target return { ref, sentences:[{jp,pt}] } where ref = the vocab_id (as a string) for vocab targets,
or the grammar key for grammar targets. Produce (need + 2) sentences per target. Rules:
- Each sentence must GENUINELY use the target (the vocab word, or the grammar pattern) in a correct, natural way.
- Beginner-appropriate (i+1): use only common N5/N4 vocabulary around the target; keep sentences SHORT
  (roughly 4-12 words). Vary the sentences (different subjects/contexts), don't just template.
- Japanese: natural, correct, and **do NOT end with 。 or any other punctuation** (generated sentences are
  clean). Keep names/loanwords minimal.
- pt: a NATURAL Brazilian-Portuguese translation — what a Brazilian would actually say, NOT a literal mirror
  ("Eu sou estudante", never "Quanto a mim, sou estudante"). NEVER use the — (em dash) character; use commas
  or parentheses. No AI tells.
Return ONLY the structured object; every target must appear once with its sentences.`,
      { label: `gen:${pad(i)}`, phase: 'Generate', schema: SCHEMA, agentType: 'general-purpose' },
    ),
  ),
)

const flat = []
for (const g of groups) if (g && Array.isArray(g.results)) flat.push(...g.results)
const total = flat.reduce((a, r) => a + (r.sentences ? r.sentences.length : 0), 0)
log('generate done: ' + total + ' sentences for ' + flat.length + ' targets')
return flat
