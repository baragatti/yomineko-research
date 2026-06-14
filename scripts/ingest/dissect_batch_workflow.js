export const meta = {
  name: 'yomineko-dissect-grp',
  description: 'Dissect sentences (Layer-B pt-BR) in GROUPS of K per agent — slug-keyed, ~Kx cheaper than 1/agent',
  phases: [{ title: 'Dissect', detail: 'one agent per group authors translation + glosses + particles for K sentences' }],
}

const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const DIR = A.dir
const N = A.count || 1
log('dissect-grp: groups=' + N + ' DIR=' + DIR)

const SENTENCE = {
  type: 'object',
  properties: {
    slug: { type: 'string' },
    grammar_keys: { type: 'array', items: { type: 'string' } },
    pt: { type: 'string' },
    pt_literal: { type: 'string' },
    structure_explanation_pt: { type: 'string' },
    tokens: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          position: { type: 'integer' },
          gloss_pt: { type: 'string' },
          role_pt: { type: 'string' },
          conjugation_note_pt: { type: ['string', 'null'] },
        },
        required: ['position', 'gloss_pt'],
      },
    },
    particles: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          position: { type: 'integer' },
          function_pt: { type: 'string' },
          explanation_pt: { type: 'string' },
        },
        required: ['position', 'function_pt', 'explanation_pt'],
      },
    },
  },
  required: ['slug', 'grammar_keys', 'pt', 'pt_literal', 'structure_explanation_pt', 'tokens', 'particles'],
}
const SCHEMA = {
  type: 'object',
  properties: { results: { type: 'array', items: SENTENCE } },
  required: ['results'],
}

const pad = (i) => String(i).padStart(4, '0')

const groups = await parallel(
  Array.from({ length: N }, (_, i) => i).map((i) => () =>
    agent(
      `Dissect a GROUP of Japanese sentences into Brazilian Portuguese (pt-BR) for a paid-grade course.
Use the Read tool on \`${DIR}/group_${pad(i)}.json\` — it is a JSON ARRAY of sentence objects. Each has:
jp, en (a NOISY hint), target (grammar focus, a hint), grammar_candidates[] ({key, pattern, label} — the
grammar points to check against), tokens[] (position, surface, lemma, reading, pos_coarse, pos_fine,
is_particle, gloss_en — a NOISY hint, may be wrong; trust your own Japanese), particles[] (position,
particle), and slug.

Return { results: [ ... ] } with ONE object PER input sentence, each keyed by its own slug (ECHO the slug
EXACTLY from the input — this is how results are matched; never guess or reorder). For each sentence author
IN pt-BR, accurate + natural:
- slug: copy the input sentence's slug verbatim.
- grammar_keys: the KEYS (from this item's grammar_candidates) whose grammar pattern the sentence GENUINELY
  uses. Be strict and judge by MEANING/STRUCTURE, not substring: e.g. only return the 〜たい key if it is the
  desiderative on a verb stem (聞きたい) — NOT the adjective 冷たい/痛い; only the 〜たり key for the 〜たり〜たり
  construction — NOT 当たり前/ぴったり; pick the AFFIRMATIVE vs NEGATIVE variant (e.g. たほうがいい vs ないほうがいい)
  that actually appears. Return [] if NO candidate genuinely applies. You may return MULTIPLE keys if the
  sentence uses more than one candidate pattern.
- pt: natural pt-BR translation.
- pt_literal: literal/gloss-style pt-BR mirroring the Japanese structure.
- structure_explanation_pt: 2-4 sentences on how the sentence is built and why (beginner-clear; mention target).
- tokens: for EACH CONTENT token (pos_coarse 名詞/動詞/形容詞/形状詞/副詞/代名詞/連体詞/接続詞/感動詞,
  INCLUDING auxiliary adjectives/verbs like ない・いる・ある・くださる) return {position, gloss_pt (meaning IN
  CONTEXT), role_pt (e.g. 'verbo principal','objeto','tópico','adjetivo','auxiliar de negação'),
  conjugation_note_pt (form for verbs/adjectives e.g. 'forma negativa de 高い'; else null)}. Skip pure
  particles and punctuation only.
- particles: for EACH token with is_particle=true return {position, function_pt, explanation_pt (por que ESTA
  partícula AQUI, em pt-BR)}.
Keep Japanese in Japanese; define terms; precise + friendly. Return ONLY the structured object — every input
sentence must appear exactly once in results.`,
      { label: `grp:${pad(i)}`, phase: 'Dissect', schema: SCHEMA, agentType: 'general-purpose' },
    ),
  ),
)

const flat = []
let nulls = 0
for (const g of groups) {
  if (g && Array.isArray(g.results)) {
    for (const lb of g.results) flat.push({ layerB: lb, verdict: { faithful: true } })
  } else {
    nulls += 1
  }
}
log('dissect-grp done: ' + flat.length + ' sentences from ' + (N - nulls) + '/' + N + ' groups')
return flat
