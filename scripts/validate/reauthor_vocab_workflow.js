export const meta = {
  name: 'reauthor-vocab-glosses',
  description: 'Independently author vocab core meanings (senses, en+pt) from facts only, then verify — D-LIC-1 SA removal',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}
const NBATCH = 67
const DIR = `C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/reauthor/vocab/`
const SENSE = { type: 'object', required: ['en', 'pt'], additionalProperties: false, properties: {
  en: { type: 'array', items: { type: 'string' }, minItems: 1 },
  pt: { type: 'array', items: { type: 'string' }, minItems: 1 } } }
const GEN_SCHEMA = { type: 'object', required: ['items'], additionalProperties: false, properties: {
  items: { type: 'array', items: { type: 'object', required: ['id', 'senses'], additionalProperties: false,
    properties: { id: { type: 'integer' }, senses: { type: 'array', items: SENSE, minItems: 1 } } } } } }
const VERIFY_SCHEMA = { type: 'object', required: ['flagged'], additionalProperties: false, properties: {
  flagged: { type: 'array', items: { type: 'object', required: ['id', 'issue', 'senses'], additionalProperties: false,
    properties: { id: { type: 'integer' }, issue: { type: 'string' }, senses: { type: 'array', items: SENSE } } } } } }

const out = await pipeline(
  Array.from({ length: NBATCH }, (_, b) => b),
  (b) => agent(
    `You are a Japanese→(English + Brazilian-Portuguese) lexicographer writing ORIGINAL, concise, ` +
    `learner-appropriate meanings for Japanese vocabulary, FROM YOUR OWN KNOWLEDGE. Read the JSON array at ` +
    `${DIR}batch_${String(b).padStart(4, '0')}.json; each item is {id, headword, kana, pos (JMdict POS tags ` +
    `like "v5k"=godan verb, "v1"=ichidan, "adj-i"=i-adjective, "adj-na", "n"=noun, "adv", "exp"…), lexeme, ` +
    `verb_class, adj_class, examples (real sentences USING the word — for sense disambiguation), kanji_hints ` +
    `(our meanings of the kanji in the word)}. You are given ONLY these facts — NOT any dictionary's glosses.\n\n` +
    `For EACH word, write its OWN core meaning(s) as a SHORT list of senses a learner needs (usually 1–4; do ` +
    `NOT reproduce a dictionary's exhaustive 10–20 sense split). Each sense = {en:[short glosses], pt:[natural ` +
    `Brazilian-Portuguese equivalents]}. Match the POS (a verb → "to …"/"…ar/er/ir"; an i/na-adjective → an ` +
    `adjective; a noun → a noun). Use the example sentences + kanji hints to pick the right senses. Order most ` +
    `common first. Natural pt-BR (never pt-PT), no slang. en and pt within a sense should correspond.\n\n` +
    `Return {"items":[{"id","senses":[{"en":[…],"pt":[…]}, …]}, …]} for ALL items in the batch.`,
    { label: `author:${b}`, phase: 'Author', schema: GEN_SCHEMA }
  ).then(r => ({ b, items: (r && r.items) ? r.items : [] })),
  (gen) => {
    if (!gen.items.length) return { b: gen.b, items: [], flagged: [] }
    const compact = gen.items.map(i => `${i.id}: ` + i.senses.map(s => `[${s.en.join('/')} | ${s.pt.join('/')}]`).join(' ; ')).join('\n')
    return agent(
      `You are a strict Japanese-vocabulary fact-checker. Below are proposed core meanings (id: senses as ` +
      `[en | pt-BR]) for Japanese words. The word facts (headword, kana, pos, examples) are in ` +
      `${DIR}batch_${String(gen.b).padStart(4, '0')}.json (match by id). For EACH, check: are the English ` +
      `glosses CORRECT core meanings of that word for that POS? Is the pt-BR a faithful, natural Brazilian-` +
      `Portuguese rendering (not pt-PT, not wrong, not missing the main sense, right part of speech)? Flag ONLY ` +
      `words that are WRONG, mis-POS'd, or missing the main meaning, and give the corrected full senses list. ` +
      `Words that are fine: omit.\n\nPROPOSED:\n${compact}\n\n` +
      `Return {"flagged":[{"id","issue","senses":[{"en":[…],"pt":[…]}]}]}.`,
      { label: `verify:${gen.b}`, phase: 'Verify', schema: VERIFY_SCHEMA }
    ).then(v => ({ b: gen.b, items: gen.items, flagged: (v && v.flagged) ? v.flagged : [] }))
  }
)
const merged = []
for (const r of out.filter(Boolean)) {
  const fix = new Map((r.flagged || []).map(f => [f.id, f]))
  for (const it of r.items) {
    const f = fix.get(it.id)
    merged.push(f ? { id: it.id, senses: f.senses, corrected: true } : { ...it, corrected: false })
  }
}
const nfix = merged.filter(m => m.corrected).length
log(`reauthor-vocab: authored ${merged.length} vocab; verifier corrected ${nfix}`)
return { count: merged.length, corrected: nfix, items: merged }
