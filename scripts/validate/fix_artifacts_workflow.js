export const meta = {
  name: 'fix-translation-artifacts',
  description: 'Commit slash-alternative / parenthetical-gloss pt-BR translations to one faithful natural rendering',
  phases: [{ title: 'Fix', detail: 'one agent for the batch' }],
}
const DIR = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/fix/'
const NBATCH = 1
const SCHEMA = {
  type: 'object', required: ['fixes'], additionalProperties: false,
  properties: {
    fixes: {
      type: 'array',
      items: {
        type: 'object', required: ['id', 'pt'], additionalProperties: false,
        properties: { id: { type: 'integer' }, pt: { type: 'string' } },
      },
    },
  },
}
phase('Fix')
const results = await parallel(Array.from({ length: NBATCH }, (_, b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `You are a native Brazilian-Portuguese editor fixing a Japanese course. Read the JSON array at ${path}; ` +
    `each item is {id, jp (Japanese), en (trusted human English), pt (current pt-BR that wrongly contains TWO ` +
    `alternatives — a "X / Y" slash or an editorial "(...)" — or a dictionary-style parenthetical)}.\n\n` +
    `For each, return ONE clean, finished pt-BR translation: pick or merge into the single most natural, ` +
    `daily-life rendering that is FAITHFUL to the jp (use en as the meaning rail). No slashes, no editorial ` +
    `parentheses, no alternatives, no slang, no notes — just the sentence a Brazilian would actually say.\n\n` +
    `Return {"fixes":[{"id", "pt"}]} for ALL items.`,
    { label: `fix:${b}`, phase: 'Fix', schema: SCHEMA }
  ).then(r => (r && r.fixes) ? r.fixes : [])
}))
const flat = results.filter(Boolean).flat()
log(`fixed ${flat.length} artifact translations`)
return { fixes: flat }
