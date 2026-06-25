export const meta = {
  name: 'translate-corpus',
  description: 'Translate distinct corpus strings (one agent per batch file) for a tr_extract task',
  phases: [{ title: 'Translate', detail: 'one agent per batch' }],
}

// ── set per run ──
const TASK = 'sent_trans_en'   // 'n2n1_pt' | 'grammar_en' | 'sentence_en' | 'form_meanings' | 'sent_trans_en'
const NBATCH = 8
// ─────────────────

const DIR = `C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/research/derived/tr/${TASK}/`

const PROMPTS = {
  n2n1_pt: `You translate Japanese-learning dictionary glosses from ENGLISH into natural Brazilian Portuguese
(pt-BR, never pt-PT). Each item's "t" is either a short list of English glosses (a kanji's meanings or a
vocabulary sense's glosses) or a single string. Produce the pt-BR equivalent:
- Keep it concise and dictionary-style (these are flash-card meanings), natural pt-BR, standard linguistic
  terminology. For a list, return a list of the pt-BR glosses (you may drop near-duplicate English synonyms;
  keep 1-4 good pt-BR glosses). For a string, return a string.
- Do not transliterate or leave English; translate the meaning. No notes, no quotes around the whole thing.`,
  grammar_en: `You translate Brazilian-Portuguese Japanese-grammar explanations into natural, concise ENGLISH.
Each item's "t" is a grammar label, explanation, formation rule, nuance note, a list of per-form meanings, or
a grammar-family label/rule. Return faithful English that preserves the meaning and any structure (list -> list,
string -> string). Keep linguistic terms standard (topic, transitive, plain form, etc.). No notes.`,
  sent_trans_en: `You translate the Brazilian-Portuguese translation of a Japanese sentence into natural,
fluent ENGLISH. Each item's "t" is one sentence translation. Return a natural English translation conveying
the same meaning and register (string -> string). No notes, no quotes around the value.`,
  form_meanings: `You translate Brazilian-Portuguese meanings of Japanese grammar FORMS into natural, concise
ENGLISH. Each item's "t" is a short meaning for a conjugated/grammatical form. Return faithful English
(string -> string). Keep grammar terminology standard. No notes.`,
  sentence_en: `You translate Brazilian-Portuguese Japanese-sentence-analysis strings into natural, concise
ENGLISH. Each item's "t" is one of: a sentence's structure explanation, a literal translation, a per-token
gloss, a per-token grammatical role (e.g. "verbo principal" -> "main verb", "tópico" -> "topic"), a token
conjugation note, a particle function (e.g. "marca de objeto direto" -> "direct-object marker"), or a particle
explanation. Return faithful English preserving meaning and structure (string -> string). Keep grammar
terminology standard and consistent. No notes, no quotes around the whole value.`,
}

const SCHEMA = {
  type: 'object', required: ['results'], additionalProperties: false,
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object', required: ['i', 'o'], additionalProperties: false,
        properties: {
          i: { type: 'integer' },
          o: { anyOf: [{ type: 'string' }, { type: 'array', items: { type: 'string' } }] },
        },
      },
    },
  },
}

phase('Translate')
const idxs = Array.from({ length: NBATCH }, (_, b) => b)
const results = await parallel(idxs.map((b) => () => {
  const path = `${DIR}batch_${String(b).padStart(4, '0')}.json`
  return agent(
    `${PROMPTS[TASK]}\n\nRead the JSON array at ${path}. It is a list of {i, t} items. Translate every item's ` +
    `"t" and return {"results":[{"i": <same i>, "o": <translation>}]} covering ALL items in the file, same "i".`,
    { label: `tr:${TASK}:${b}`, phase: 'Translate', schema: SCHEMA }
  ).then(r => (r && r.results) ? r.results : [])
}))

const flat = results.filter(Boolean).flat()
log(`translated ${flat.length} items across ${NBATCH} batches for ${TASK}`)
return { results: flat }
