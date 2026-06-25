export const meta = {
  name: 'audit-translations',
  description: 'Adversarial faithfulness audit of a stratified sample of corpus translations',
  phases: [{ title: 'Audit', detail: 'one agent per sample batch' }],
}
const DIR = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/audit/'
const NBATCH = 8

const SCHEMA = {
  type: 'object', required: ['verdicts'], additionalProperties: false,
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', required: ['id', 'ok', 'severity'], additionalProperties: false,
        properties: {
          id: { type: 'integer' },
          ok: { type: 'boolean' },
          severity: { type: 'string', enum: ['ok', 'minor', 'major'] },
          issue: { type: 'string' },
        },
      },
    },
  },
}

phase('Audit')
const results = await parallel(Array.from({ length: NBATCH }, (_, b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `You are an ADVERSARIAL bilingual reviewer (Brazilian Portuguese + English) auditing machine translations ` +
    `in a Japanese-learning corpus. Read the JSON array at ${path}. Each item: {id, dim, src_lang, src (source ` +
    `text), tgt_lang, tgt (the translation under review), ctx (Japanese/headword context)}.\n\n` +
    `For EACH item, judge whether "tgt" is a FAITHFUL and NATURAL translation of "src" (grounded in ctx). ` +
    `Actively hunt for problems: wrong/inverted meaning, dropped or invented content, untranslated text (still ` +
    `in the source language), wrong register, garbled grammar, mojibake. Cognates that are legitimately ` +
    `identical (banana=banana) are OK. Minor wording/style differences are "minor", not failures. Only real ` +
    `meaning errors are "major".\n\n` +
    `Return {"verdicts":[{"id", "ok" (true if acceptable), "severity":"ok|minor|major", "issue" (short, only ` +
    `if not ok)}]} for ALL items in the file.`,
    { label: `audit:${b}`, phase: 'Audit', schema: SCHEMA }
  ).then(r => (r && r.verdicts) ? r.verdicts : [])
}))

const flat = results.filter(Boolean).flat()
const major = flat.filter(v => v.severity === 'major')
const minor = flat.filter(v => v.severity === 'minor')
log(`audited ${flat.length}: ${major.length} major, ${minor.length} minor, ${flat.length - major.length - minor.length} ok`)
return { total: flat.length, major, minor }
