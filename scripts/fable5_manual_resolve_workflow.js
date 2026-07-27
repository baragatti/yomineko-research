export const meta = {
  name: 'fable5-manual-resolve',
  description: 'Resolve the Phase-3 needs_human manual queue per sentence, adversarially verified',
  phases: [{ title: 'Resolve' }, { title: 'Verify' }],
}
// args: batch keys like ["m00","m01",...] -> reads research/derived/fable5_validation/phase3_manual_resolve/
// <key>.json ({items:[{slug, jp, kana, romaji, level, gen, texts, tokens_C, findings}]}) and writes
// resolved_<key>.json. Resolution is PER SENTENCE (reading fixes cascade across kana/romaji/expl/tokens).
const DIR = 'research/derived/fable5_validation/phase3_manual_resolve/'

const PATHS = [
  '"jp" (only when gen=true; NEVER edit jp of a gen=false record - that is real human Tatoeba text, Layer A)',
  '"kana", "romaji"',
  '"translation.en", "translation.pt-BR"',
  '"translation_literal.en", "translation_literal.pt-BR"',
  '"structure_explanation.en", "structure_explanation.pt-BR"',
  '"tokens[i].r", "tokens[i].romaji", "tokens[i].role.pt-BR", "tokens[i].gloss.pt-BR", "tokens[i].gloss.en", "tokens[i].note.pt-BR", "tokens[i].note.en"',
]

const RESOLVE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['sentences'],
  properties: {
    sentences: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['slug', 'decisions', 'edits'],
        properties: {
          slug: { type: 'string' },
          decisions: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false, required: ['field', 'action', 'why'],
              properties: {
                field: { type: 'string', description: "Echo the finding's field exactly" },
                action: { type: 'string', enum: ['apply', 'refute'] },
                why: { type: 'string', description: 'One or two sentences' },
              },
            },
          },
          edits: {
            type: 'array',
            description: 'Concrete field edits implementing every "apply" decision. Empty if all refuted.',
            items: {
              type: 'object', additionalProperties: false, required: ['path', 'new'],
              properties: {
                path: { type: 'string', description: 'One of the allowed path strings' },
                new: { type: 'string', description: 'Full new value for that field' },
              },
            },
          },
        },
      },
    },
  },
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['bad'],
  properties: {
    bad: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['slug', 'reason'],
        properties: { slug: { type: 'string' }, reason: { type: 'string' } },
      },
    },
  },
}

const RULES = `
HARD RULES:
- gen=false records are REAL human Japanese (Tatoeba/Tanaka, Layer A): never edit their "jp", and never
  "improve" their en translation - it is source data. Only our derived fields (kana, romaji, literals,
  explanations, tokens, pt translation) may be corrected.
- Resolve PER SENTENCE: if a reading changes, kana AND romaji AND the token's r/romaji AND any explanation
  quoting that reading must all be updated in the same edit set, so the record stays internally consistent.
- kana is a PHONETIC transcription with intentional particle conventions: wa for は, e for へ, o for を.
  Keep them. romaji mirrors kana (no spaces in this corpus; long vowels as in the existing values).
- pt-BR only, never pt-PT (conectiva not conetiva, etc.). No em dashes. No corpus-build metadata
  ("coverage"/"cobertura", QA notes) in learner-facing text.
- translation_literal.* deliberately mirror Japanese structure; do NOT smooth them into natural prose.
  But the "As for X / Quanto a X" device mirrors the topic particle は ONLY - never use it for が, を or で.
- If the finding is wrong, or the current value is defensible, choose action "refute" and emit no edit.`

const BATCHES = Array.isArray(args) ? args : JSON.parse(args)
const results = await pipeline(
  BATCHES,
  (key) => agent(
    `You are a professional Japanese linguist and pt-BR translator resolving flagged defects in a ` +
    `dissected-sentence bank for a Brazilian Japanese course. Read ${DIR}${key}.json with the Read tool. ` +
    `It holds {items:[{slug, jp, kana, romaji, level, gen, texts, tokens_C, findings}]} - "texts" holds ` +
    `the sentence's localized fields, "tokens_C" the display tokens (index i = the [i] in field names), ` +
    `and "findings" the flagged issues that a QA pass confirmed but that could not be auto-applied.\n\n` +
    `For EACH sentence, decide EACH finding: "apply" (real defect - fix it) or "refute" (finding is wrong ` +
    `or current value is defensible). Then emit the concrete edits implementing every "apply".\n\n` +
    `Allowed edit paths (use these exact strings):\n- ${PATHS.join('\n- ')}\n${RULES}\n\n` +
    `Return the structured object covering every sentence in the file.`,
    { label: `resolve:${key}`, phase: 'Resolve', schema: RESOLVE_SCHEMA },
  ).then((r) => ({ key, res: r })),
  (prev) => {
    if (!prev.res) return { key: prev.key, res: null, bad: [{ slug: '*', reason: 'resolver-failed' }] }
    return agent(
      `You are a strict adversarial reviewer. Read ${DIR}${prev.key}.json (the sentences, their current ` +
      `field values and the flagged findings). Below is a resolver's proposed resolution:\n\n` +
      `${JSON.stringify(prev.res)}\n\n` +
      `For EACH sentence check: (1) every "apply" decision is a real defect and every "refute" is ` +
      `genuinely defensible; (2) the edits actually implement the applies and touch nothing else; ` +
      `(3) INTERNAL CONSISTENCY - a changed reading is reflected in kana, romaji, the token's r/romaji and ` +
      `any explanation that quotes it; (4) the edited Japanese/kana/romaji are correct and the kana keeps ` +
      `the wa/e/o particle convention; (5) pt-BR is natural Brazilian Portuguese (never pt-PT), en is ` +
      `English, no metadata leaks, no em dashes; (6) no edit to a gen=false record's jp or en.\n` +
      `${RULES}\n\nReturn {"bad":[{slug, reason}]} for sentences whose resolution must NOT be accepted ` +
      `(empty array if all are sound). Be strict.`,
      { label: `verify:${prev.key}`, phase: 'Verify', schema: VERIFY_SCHEMA },
    ).then((v) => ({ key: prev.key, res: prev.res, bad: (v && v.bad) || [] }))
  },
)

const ok = results.filter(Boolean)
const bad = {}
const resolutions = []
for (const r of ok) {
  if (r.bad.length) bad[r.key] = r.bad
  const reject = new Set(r.bad.map((b) => b.slug))
  for (const s of (r.res && r.res.sentences) || []) {
    if (!reject.has(s.slug) && !reject.has('*')) resolutions.push(s)
  }
}
const applies = resolutions.reduce((a, s) => a + s.decisions.filter((d) => d.action === 'apply').length, 0)
const refutes = resolutions.reduce((a, s) => a + s.decisions.filter((d) => d.action === 'refute').length, 0)
const edits = resolutions.reduce((a, s) => a + s.edits.length, 0)
log(`manual resolve: ${resolutions.length} sentences accepted, ${applies} apply / ${refutes} refute, ${edits} edits; flagged ${Object.keys(bad).length} batches`)
return { summary: { sentences: resolutions.length, applies, refutes, edits }, bad, resolutions }
