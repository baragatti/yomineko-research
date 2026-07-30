export const meta = {
  name: 'fable5-author-audit-objections',
  description: 'Author fixes for the audit objections whose suggestion was prose, not a value; adversarially verified',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}
// args: batch keys ["a00",...] -> research/derived/fable5_validation/phase3_author151/<key>.json holding
// {items:[{slug, gen, current (the PROJECTED post-patch record), objections:[{field, severity, objection,
// auditor_hint}]}]}. These 143 objections could not be auto-applied because the auditor phrased the fix as
// an instruction ("replace X with Y in both locales") rather than a value - writing prose into a data field
// is exactly the bug (I6) the guards catch. So they get authored here, as VALUES.
const DIR = 'research/derived/fable5_validation/phase3_author151/'

const SCHEMA = {
  type: 'object', additionalProperties: false, required: ['sentences'],
  properties: {
    sentences: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['slug', 'edits'],
        properties: {
          slug: { type: 'string' },
          edits: {
            type: 'array',
            description: 'One entry per field you are correcting. Omit an objection you judge unfounded.',
            items: {
              type: 'object', additionalProperties: false, required: ['path', 'new', 'why'],
              properties: {
                path: { type: 'string', description: 'Exact path: kana | romaji | translation.en | translation.pt-BR | translation_literal.en | translation_literal.pt-BR | structure_explanation.en | structure_explanation.pt-BR | tokens[i].reading | tokens[i].romaji | tokens[i].role.en | tokens[i].role.pt-BR | tokens[i].gloss.en | tokens[i].gloss.pt-BR | tokens[i].conjugation_note.en | tokens[i].conjugation_note.pt-BR' },
                new: { type: 'string', description: 'The COMPLETE new value for that field. A value, never an instruction.' },
                why: { type: 'string' },
              },
            },
          },
          refuted: {
            type: 'array',
            items: {
              type: 'object', additionalProperties: false, required: ['field', 'why'],
              properties: { field: { type: 'string' }, why: { type: 'string' } },
            },
          },
        },
      },
    },
  },
}

const VERIFY = {
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
HARD RULES (violating any of these is worse than leaving the defect):
- Emit VALUES, never instructions. Never write "replace X with Y", a path like tokens[0].r, an arrow, or
  any commentary INTO a field. The field's new content is exactly what a learner will read.
- NEVER edit jp. NEVER change a token's surface, and never add or remove tokens: the pipeline cannot
  retokenize, and concat(token surfaces) must keep equalling jp.
- kana: pure kana/punctuation only, NO Latin letters. Keep the phonetic particle convention (は->wa as わ,
  へ->え, を->お). romaji: Latin only, ASCII punctuation (, . ! ?), katakana長音 ー written as '-', NO
  apostrophes. If you change a reading, the sentence-level kana/romaji cascade is recomputed for you -
  fix the TOKEN reading, and only touch kana/romaji directly when the objection is about them.
- Fix a defect EVERYWHERE in the field, not just its first occurrence: if an explanation teaches a
  rejected verb sense in two clauses, rewrite both. That half-fix is why these objections exist.
- Locale parity: if the objection says one locale still contradicts the other, give BOTH corrected values
  (they are separate paths). en must be English, pt-BR natural Brazilian Portuguese (conectiva, not
  conetiva). No em dashes. No build metadata ("coverage"/"cobertura") in learner text.
- translation_literal.* stay literal structure mirrors; the "As for X / Quanto a X" device mirrors the
  topic particle は ONLY - use a bracketed [obj] style for を, and never topic-mark が or で.`

const BATCHES = Array.isArray(args) ? args : JSON.parse(args)
const results = await pipeline(
  BATCHES,
  (key) => agent(
    `You are a professional Japanese linguist and pt-BR translator finishing incomplete fixes in a ` +
    `dissected-sentence bank. Read ${DIR}${key}.json with the Read tool. Each item has "current" (the ` +
    `record as it will look AFTER the pending patch: jp, kana, romaji, texts, tokens) and "objections" ` +
    `raised by an adversarial auditor against that projected state, each with the auditor's prose hint.\n\n` +
    `For every objection either author the corrected field value(s), or refute it with a reason if the ` +
    `current value is actually fine.\n${RULES}\n\n` +
    `Return the structured object covering every sentence in the file.`,
    { label: `author:${key}`, phase: 'Author', schema: SCHEMA },
  ).then((r) => ({ key, res: r })),
  (prev) => {
    if (!prev.res) return { key: prev.key, res: null, bad: [{ slug: '*', reason: 'author-failed' }] }
    return agent(
      `You are a strict adversarial reviewer. Read ${DIR}${prev.key}.json for the projected records and the ` +
      `objections against them. Below is an author's proposed correction set:\n\n${JSON.stringify(prev.res)}\n\n` +
      `Reject any sentence whose corrections are not safe to ship. Check: (1) each edit is a VALUE, with no ` +
      `instruction text, path reference, arrow or commentary inside it; (2) the edit actually resolves the ` +
      `objection COMPLETELY - no rejected sense or reading left anywhere else in the same field; (3) kana ` +
      `has no Latin and keeps the wa/e/o convention, romaji has no kana/CJK and no apostrophes; (4) en is ` +
      `English and pt-BR is natural Brazilian Portuguese, with both locales consistent where the objection ` +
      `was about parity; (5) no jp edit, no token surface edit, no token added or removed; (6) Japanese ` +
      `readings are correct in context.\n${RULES}\n\n` +
      `Return {"bad":[{slug, reason}]} - empty array if every sentence is sound. Be strict.`,
      { label: `verify:${prev.key}`, phase: 'Verify', schema: VERIFY },
    ).then((v) => ({ key: prev.key, res: prev.res, bad: (v && v.bad) || [] }))
  },
)

const ok = results.filter(Boolean)
const bad = {}
const accepted = []
for (const r of ok) {
  if (r.bad.length) bad[r.key] = r.bad
  const reject = new Set(r.bad.map((b) => b.slug))
  for (const s of (r.res && r.res.sentences) || []) {
    if (!reject.has(s.slug) && !reject.has('*')) accepted.push(s)
  }
}
const edits = accepted.reduce((a, s) => a + (s.edits || []).length, 0)
const refuted = accepted.reduce((a, s) => a + (s.refuted || []).length, 0)
log(`author-151: ${accepted.length} sentences accepted, ${edits} edits, ${refuted} refuted; ${Object.keys(bad).length} batches flagged`)
return { summary: { sentences: accepted.length, edits, refuted }, bad, accepted }
