export const meta = {
  name: 'descaffold-prose',
  description: 'Strip internal generation scaffolding (gp-NN codes, candidate/target meta, bare sentence IDs) from learner-facing pt+en prose, grounded-edit',
  phases: [{ title: 'Rewrite', detail: 'one agent per batch; grounded de-scaffolding edit' }],
}
const NBATCH = 28
const DIR = `C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/descaffold/`
const SCHEMA = {
  type: 'object', required: ['items'], additionalProperties: false,
  properties: {
    items: {
      type: 'array',
      items: {
        type: 'object', required: ['id', 'pt', 'en'], additionalProperties: false,
        properties: {
          id: { type: 'integer' },
          pt: { type: 'string' },
          en: { type: 'string' },
        },
      },
    },
  },
}
phase('Rewrite')
const results = await parallel(Array.from({ length: NBATCH }, (_, b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `You clean learner-facing grammar-dissection prose in a Japanese course (Brazilian-Portuguese + English). ` +
    `The prose is CORRECT but leaked INTERNAL generation scaffolding that must never reach a learner. Read the ` +
    `JSON array at ${path}; each item is {id, entity_type, entity_id, anchor (the Japanese being explained), ` +
    `grammar (map of internal grammar code -> its real human name, may be empty), pt (pt-BR prose), en (English prose)}.\n\n` +
    `For EACH item, return a cleaned pt and en that:\n` +
    `1. REMOVE every internal artifact: codes like "gp-44"/"gp-135", "(target gp-NN)"/"(gp-NN)" annotations, the ` +
    `words "candidato/candidate/target/alvo-candidato" used as a SELECTION/process reference, "tari-tari"/"cand-…" ` +
    `slugs, BARE 5-6 digit sentence IDs (e.g. "em relação à 187243", "à frase 80338"), and any orphan/stray kana ` +
    `fragment (e.g. a lone "っ"). Also remove meta-commentary that talks about the explanation's own process ` +
    `(e.g. "nenhum candidato se aplica genuinamente", "o foco/alvo desta ficha é …" framed as a pipeline note).\n` +
    `2. If a code named a grammar point, use its real name from the grammar map (or just describe it naturally). ` +
    `If the original (correctly) observed that the sentence does NOT actually use a given grammar pattern, KEEP ` +
    `that idea phrased naturally and concretely from the anchor (e.g. "Aqui たり é só parte da palavra あたりさわり, ` +
    `não o padrão 〜たり〜たり"), WITHOUT any code or the word "candidato".\n` +
    `3. PRESERVE every genuine linguistic fact (readings, glosses, particle roles, conjugation logic, the teaching ` +
    `point). Do NOT invent new claims, do NOT drop real content, keep length similar.\n` +
    `4. Natural register: idiomatic pt-BR (never a literal "Quanto a mim" calque) and natural English; no AI-tells ` +
    `("vale ressaltar", "é importante notar", em-dash sprinkling). Use correct pt-BR diacritics (é, país, núcleo, ` +
    `matemática, tópico, partícula, função).\n` +
    `5. Ground every word in the anchor (the Japanese). Drop 。 if present in generated Japanese.\n\n` +
    `Return {"items":[{"id", "pt", "en"}, …]} for ALL items in the batch, in order.`,
    { label: `descaffold:${b}`, phase: 'Rewrite', schema: SCHEMA }
  ).then(r => (r && r.items) ? r.items : [])
}))
const flat = results.filter(Boolean).flat()
// deterministic post-guard: any artifact still present? (locale-aware: target/candidate legit in en)
const PT_LEAK = /gp-\d+|candidat[oae]s?\b|candidate\b|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])|\btarget\b|\bjec\b|位置\s*\d|posi[çc][ãa]o\s*\d/i
const EN_LEAK = /gp-\d+|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])|\bjec\b|位置\s*\d/i
const dirty = flat.filter(it => PT_LEAK.test(it.pt || '') || EN_LEAK.test(it.en || ''))
log(`descaffold: rewrote ${flat.length} items; ${dirty.length} still contain an artifact (need 2nd pass)`)
return { count: flat.length, dirtyIds: dirty.map(d => d.id), items: flat }
