export const meta = {
  name: 'yomineko-grammar-enrich',
  description: 'Enrich grammar points: register enum + caution + per-form pt meaning + humanized prose',
  phases: [{ title: 'Enrich', detail: 'one agent per group classifies register/caution + humanizes prose' }],
}

const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const DIR = A.dir
const N = A.count || 1
log('grammar-enrich: groups=' + N + ' DIR=' + DIR)

const REGISTER = ['plain', 'casual', 'polite', 'formal', 'written', 'honorific', 'humble',
  'colloquial', 'vulgar', 'literary', 'dated', 'feminine', 'masculine', 'slang', 'childish']

const POINT = {
  type: 'object',
  properties: {
    key: { type: 'string' },
    register: { type: 'array', items: { type: 'string', enum: REGISTER } },
    caution: { type: 'string', enum: ['none', 'rough', 'offensive', 'sensitive'] },
    forms: {
      type: 'array',
      items: {
        type: 'object',
        properties: { form: { type: 'string' }, meaning: { type: 'string' } },
        required: ['form', 'meaning'],
      },
    },
    explanation: { type: 'string' },
    formation: { type: 'string' },
    nuance: { type: 'string' },
  },
  required: ['key', 'register', 'caution', 'forms', 'explanation', 'formation', 'nuance'],
}
const SCHEMA = { type: 'object', properties: { results: { type: 'array', items: POINT } }, required: ['results'] }
const pad = (i) => String(i).padStart(4, '0')

const groups = await parallel(
  Array.from({ length: N }, (_, i) => i).map((i) => () =>
    agent(
      `You are enriching Japanese grammar points for a paid-grade Brazilian-Portuguese (pt-BR) course.
Use the Read tool on \`${DIR}/group_${pad(i)}.json\` — a JSON ARRAY of grammar points, each with: key,
level, structure_pattern, forms[] (Japanese surface forms), current_register (a coarse hint), and existing
pt-BR label/explanation/formation/nuance.

Return { results: [ ... ] } with ONE object per input point, keyed by its key (ECHO key EXACTLY). For each:
- register: ARRAY of applicable values from this fixed set ONLY: ${REGISTER.join(', ')}. Be precise:
  keigo points (お〜になる, いらっしゃる) -> 'honorific'; 〜いたします/お〜する -> 'humble'; です・ます -> 'polite';
  plain/dictionary forms -> 'plain'; ちゃう/なきゃ/〜じゃん -> 'casual' (+'colloquial'); rough/blunt -> add
  'vulgar' only if truly coarse; written-only -> 'written'/'literary'; old-fashioned -> 'dated'. Usually 1-2 values.
- caution: 'offensive' if it can offend/insult, 'rough' if blunt/impolite, 'sensitive' if context-risky,
  else 'none'. Most grammar = 'none'.
- forms: echo each input form with a SHORT natural pt-BR meaning (e.g. {form:'です', meaning:'ser/estar (educado)'}).
- explanation / formation / nuance: REWRITE the existing pt-BR text to be natural, direct and human — apply
  the humanizer principles: no "Quanto a mim", no "vale ressaltar/destacar", no rule-of-three filler, no
  inflated adjectives. NEVER use the — (em dash) character anywhere — use parentheses or commas instead. Keep it beginner-clear, accurate, friendly, pt-BR (você, not pt-PT).
  Preserve the real teaching content (incl. any "armadilha para brasileiros" / L1 pitfalls). Keep Japanese
  examples in Japanese. If the existing text is already clean, return it lightly polished, not padded.
Return ONLY the structured object; every input point must appear once.`,
      { label: `gram-enrich:${pad(i)}`, phase: 'Enrich', schema: SCHEMA, agentType: 'general-purpose' },
    ),
  ),
)

const flat = []
for (const g of groups) if (g && Array.isArray(g.results)) flat.push(...g.results)
log('grammar-enrich done: ' + flat.length + ' points')
return flat
