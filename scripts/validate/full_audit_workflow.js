export const meta = {
  name: 'full-sentence-audit',
  description: 'Audit every sentence: natural pt (faithful+natural) + literal pt (literal-correct). Returns only problems.',
  phases: [{ title: 'Audit', detail: 'one agent per batch of 60' }],
}
const DIR = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/full/'
const NBATCH = 93
const SCHEMA = {
  type: 'object', required: ['flagged'], additionalProperties: false,
  properties: {
    flagged: {
      type: 'array',
      items: {
        type: 'object', required: ['id', 'field', 'severity'], additionalProperties: false,
        properties: {
          id: { type: 'integer' },
          field: { type: 'string', enum: ['natural', 'literal'] },
          severity: { type: 'string', enum: ['minor', 'major'] },
          issue: { type: 'string' },
          suggestion: { type: 'string' },   // a corrected value for that field
        },
      },
    },
  },
}
phase('Audit')
const results = await parallel(Array.from({ length: NBATCH }, (_, b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `You are a STRICT bilingual (Brazilian Portuguese + English) reviewer who reads Japanese, auditing a ` +
    `Japanese-course corpus. Read the JSON array at ${path}; each item is {id, jp (Japanese), en (trusted ` +
    `human English = meaning rail), nat (the NATURAL pt-BR translation), lit (the LITERAL/word-for-word pt-BR ` +
    `mirror, may be null)}.\n\n` +
    `Judge TWO fields by DIFFERENT criteria:\n` +
    `- "natural" (nat): must be FAITHFUL to jp (use en) AND read like natural daily-life pt-BR. Flag inverted/` +
    `dropped/added meaning, stiff/over-literal renderings, Japanese particle calques (は as "quanto a mim", ` +
    `mirrored を/が, JP word order), translationese, AI-like phrasing, or leftover "X / Y" alternatives. ` +
    `(Explicit JP topic phrases について/に関して = "sobre/a respeito de" are NOT calques. Natural != slang.)\n` +
    `- "literal" (lit): must be an ACCURATE word-for-word/structural mirror of the jp (correct morpheme senses, ` +
    `particle labels, nothing mistranslated). It is ALLOWED to read un-natural; only flag it if it is WRONG ` +
    `(a real mistranslation/structural error). If lit is null, skip it.\n\n` +
    `Output ONLY problems. severity "major" = real meaning error or clearly unnatural (natural field) / real ` +
    `mistranslation (literal field); "minor" = stylistic nit. For each problem give "suggestion" = the ` +
    `corrected value for that field. Items that are fine produce NO entry.\n\n` +
    `Return {"flagged":[{"id", "field":"natural|literal", "severity":"minor|major", "issue", "suggestion"}]}.`,
    { label: `full:${b}`, phase: 'Audit', schema: SCHEMA }
  ).then(r => (r && r.flagged) ? r.flagged.map(f => ({ ...f, batch: b })) : [])
}))
const flat = results.filter(Boolean).flat()
const major = flat.filter(v => v.severity === 'major')
log(`audited ${NBATCH} batches; flagged ${flat.length} (${major.length} major, ${flat.length - major.length} minor)`)
return { flaggedTotal: flat.length, major: major.length, flagged: flat }
