export const meta = {
  name: 'nat-audit',
  description: 'Naturalness + faithfulness audit of pt-BR sentence translations (grounded by jp + trusted en)',
  phases: [{ title: 'Audit', detail: 'one agent per batch' }],
}
const DIR = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/nat/'
const NBATCH = 8

const SCHEMA = {
  type: 'object', required: ['verdicts'], additionalProperties: false,
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', required: ['id', 'faithful', 'natural', 'severity'], additionalProperties: false,
        properties: {
          id: { type: 'integer' },
          faithful: { type: 'boolean' },          // conveys the jp meaning (en is the rail)
          natural: { type: 'boolean' },            // natural daily-life pt-BR, not stiff/literal/calque/AI-like
          severity: { type: 'string', enum: ['ok', 'minor', 'major'] },
          issue: { type: 'string' },               // short, only if not ok
          suggestion: { type: 'string' },          // a better pt-BR, only if not ok
        },
      },
    },
  },
}

phase('Audit')
const results = await parallel(Array.from({ length: NBATCH }, (_, b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `You are a STRICT native Brazilian-Portuguese reviewer who also reads Japanese, auditing a Japanese-course ` +
    `corpus. Read the JSON array at ${path}; each item is {id, jp (Japanese), pt (the pt-BR translation under ` +
    `review), en (a trusted human English translation, your meaning rail)}.\n\n` +
    `Judge each on TWO axes:\n` +
    `1) faithful — does pt convey the jp's meaning (use en to confirm)? Inverted/dropped/added meaning = not faithful.\n` +
    `2) natural — is pt how a Brazilian would ACTUALLY say it in daily life? Flag stiff/over-literal renderings, ` +
    `Japanese particle calques (は as "quanto a mim/você", を/が mirrored, JP word order), translationese, and ` +
    `AI-like phrasing. NOTE: explicit Japanese topic phrases (について/に関して = "sobre/a respeito de") are NOT ` +
    `calques. Do NOT demand slang; natural ≠ slangy. Minor stylistic nits = "minor"; real meaning or clearly ` +
    `unnatural phrasing = "major".\n\n` +
    `Return {"verdicts":[{"id", "faithful", "natural", "severity":"ok|minor|major", "issue", "suggestion" (a ` +
    `better pt-BR)}]} for ALL items.`,
    { label: `nat:${b}`, phase: 'Audit', schema: SCHEMA }
  ).then(r => (r && r.verdicts) ? r.verdicts : [])
}))

const flat = results.filter(Boolean).flat()
const major = flat.filter(v => v.severity === 'major')
const unfaithful = flat.filter(v => v.faithful === false)
const unnatural = flat.filter(v => v.natural === false)
log(`audited ${flat.length}: ${major.length} major, ${unfaithful.length} unfaithful, ${unnatural.length} unnatural`)
return { total: flat.length, major, unfaithful: unfaithful.filter(v => v.severity !== 'minor'), unnatural }
