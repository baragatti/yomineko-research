export const meta = {
  name: 'reauthor-kanji-meanings',
  description: 'Independently author kanji meaning glosses (en + pt-BR) from facts only, then self-verify — D-LIC-1 SA removal',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}
const NBATCH = 36
const DIR = `C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/reauthor/kanji/`
const GEN_SCHEMA = {
  type: 'object', required: ['items'], additionalProperties: false,
  properties: {
    items: { type: 'array', items: {
      type: 'object', required: ['id', 'en', 'pt'], additionalProperties: false,
      properties: {
        id: { type: 'integer' },
        en: { type: 'array', items: { type: 'string' }, minItems: 1 },
        pt: { type: 'array', items: { type: 'string' }, minItems: 1 },
      } } },
  },
}
const VERIFY_SCHEMA = {
  type: 'object', required: ['flagged'], additionalProperties: false,
  properties: {
    flagged: { type: 'array', items: {
      type: 'object', required: ['id', 'issue', 'en', 'pt'], additionalProperties: false,
      properties: {
        id: { type: 'integer' }, issue: { type: 'string' },
        en: { type: 'array', items: { type: 'string' } },
        pt: { type: 'array', items: { type: 'string' } },
      } } },
  },
}
// pipeline: author each batch, then a DIFFERENT-prompt verifier fact-checks the same batch and corrects wrong glosses
const out = await pipeline(
  Array.from({ length: NBATCH }, (_, b) => b),
  (b) => agent(
    `You are a Japanese-to-(English + Brazilian-Portuguese) lexicographer writing ORIGINAL, concise core meaning ` +
    `glosses for kanji, FROM YOUR OWN KNOWLEDGE. Read the JSON array at ${DIR}batch_${String(b).padStart(4,'0')}.json; ` +
    `each item is {id, character, level, strokes, radical, on (on'yomi), kun (kun'yomi), examples (words that use ` +
    `the kanji, headword+kana, NO definitions)}. You are given ONLY these facts — NOT any dictionary's definition.\n\n` +
    `For EACH kanji write your OWN concise meaning list: 1-5 short core English glosses (en) and their natural ` +
    `Brazilian-Portuguese equivalents (pt), ordered most-important first. Keep them short and learner-facing ` +
    `(e.g. en ["water"], pt ["água"]; en ["say","speak"], pt ["dizer","falar"]). Use the readings + example words ` +
    `to pick the right senses. Natural pt-BR (never pt-PT). Do not invent fanciful meanings; give the standard ` +
    `core senses a learner needs. pt and en lists should correspond.\n\n` +
    `Return {"items":[{"id","en":[...],"pt":[...]}, …]} for ALL items in the batch.`,
    { label: `author:${b}`, phase: 'Author', schema: GEN_SCHEMA }
  ).then(r => ({ b, items: (r && r.items) ? r.items : [] })),
  // VERIFY (different prompt, error-seeking): fact-check correctness; return only CORRECTED entries
  (gen) => {
    if (!gen.items.length) return { b: gen.b, items: [], flagged: [] }
    const compact = gen.items.map(i => `${i.id}:${i.en.join('/')} | ${i.pt.join('/')}`).join('\n')
    return agent(
      `You are a strict kanji-meaning fact-checker. Below are proposed (id : English glosses | pt-BR glosses) for ` +
      `Japanese kanji. The kanji facts (character, readings, examples) are in ${DIR}batch_${String(gen.b).padStart(4,'0')}.json ` +
      `(match by id). For EACH, check: are the English glosses CORRECT core meanings of that kanji? Is the pt-BR a ` +
      `faithful, natural Brazilian-Portuguese rendering of the English (not pt-PT, not wrong, not missing the main ` +
      `sense)? Flag ONLY entries that are WRONG, misleading, or have a bad/missing main sense, and give the ` +
      `corrected en + pt. Entries that are fine: omit.\n\nPROPOSED:\n${compact}\n\n` +
      `Return {"flagged":[{"id","issue","en":[...],"pt":[...]}]}.`,
      { label: `verify:${gen.b}`, phase: 'Verify', schema: VERIFY_SCHEMA }
    ).then(v => ({ b: gen.b, items: gen.items, flagged: (v && v.flagged) ? v.flagged : [] }))
  }
)
// merge: apply verifier corrections over the authored set
const merged = []
for (const r of out.filter(Boolean)) {
  const fix = new Map((r.flagged || []).map(f => [f.id, f]))
  for (const it of r.items) {
    const f = fix.get(it.id)
    merged.push(f ? { id: it.id, en: f.en, pt: f.pt, corrected: true } : { ...it, corrected: false })
  }
}
const nfix = merged.filter(m => m.corrected).length
log(`reauthor-kanji: authored ${merged.length} kanji; verifier corrected ${nfix}`)
return { count: merged.length, corrected: nfix, items: merged }
