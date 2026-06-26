export const meta = {
  name: 'gt-field-audit',
  description: 'Ground-truth pt↔en audit of a corpus field-class; returns only problems with corrections',
  phases: [{ title: 'Audit', detail: 'one agent per batch' }],
}
// ── set per run ──
const KEY = 'sentence.structure_explanation'
const NBATCH = 47
// ─────────────────
const DIR = `C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/gt-${KEY.replace('.', '_')}/`
const SCHEMA = {
  type: 'object', required: ['flagged'], additionalProperties: false,
  properties: {
    flagged: {
      type: 'array',
      items: {
        type: 'object', required: ['id', 'severity'], additionalProperties: false,
        properties: {
          id: { type: 'integer' },
          severity: { type: 'string', enum: ['minor', 'major'] },
          issue: { type: 'string' },
          suggestion: { anyOf: [{ type: 'string' }, { type: 'array', items: { type: 'string' } }] },
        },
      },
    },
  },
}
phase('Audit')
const results = await parallel(Array.from({ length: NBATCH }, (_, b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `You audit Brazilian-Portuguese corpus content against its authoritative ENGLISH source in a Japanese ` +
    `course. Read the JSON array at ${path}; each item is {id, anchor (the Japanese kanji/word/grammar/sentence ` +
    `context), pt (the pt-BR under review), en (the authoritative English: a dictionary gloss list, or the ` +
    `source meaning), is_list (true if pt/en are lists of glosses)}.\n\n` +
    `For each, decide if pt is a FAITHFUL, CORRECT, and natural rendering of en for that anchor:\n` +
    `- faithful/correct: same meaning as en; for gloss LISTS, the pt must cover the en senses without inventing ` +
    `or dropping a key sense or mistranslating one (e.g. en "wild" rendered "campo/field" is WRONG).\n` +
    `- natural: standard pt-BR dictionary/explanation wording (for prose, also flag stiff calques, AI-tells, ` +
    `leftover "X / Y" alternatives). Do NOT require slang.\n` +
    `Ground every judgment in the anchor (the Japanese), not just the en.\n\n` +
    `Output ONLY problems. "major" = wrong/inverted/missing meaning; "minor" = stylistic/incomplete nit. Give ` +
    `"suggestion" = the corrected pt (a STRING, or an ARRAY of glosses if is_list). Items that are fine = no entry.\n\n` +
    `Return {"flagged":[{"id","severity":"minor|major","issue","suggestion"}]}.`,
    { label: `gt:${KEY}:${b}`, phase: 'Audit', schema: SCHEMA }
  ).then(r => (r && r.flagged) ? r.flagged : [])
}))
const flat = results.filter(Boolean).flat()
const major = flat.filter(v => v.severity === 'major')
log(`${KEY}: flagged ${flat.length} (${major.length} major, ${flat.length - major.length} minor)`)
return { key: KEY, flaggedTotal: flat.length, major: major.length, flagged: flat }
