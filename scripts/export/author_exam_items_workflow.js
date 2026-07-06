export const meta = {
  name: 'author-exam-items',
  description: 'Author paraphrase (言い換え) + usage (用法) exam items from corpus facts, adversarially verified',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}
// args: batch keys like ["n5_b1",...] — one author+verify chain per 30-item batch (file in, file out).
const ROOT = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/'
const DIR = ROOT + 'research/derived/reauthor/exam_authored/'

const ACK = { type: 'object', additionalProperties: false, required: ['done'],
  properties: { done: { type: 'boolean' }, note: { type: 'string' } } }
const VERIFY_SCHEMA = { type: 'object', additionalProperties: false, required: ['bad'],
  properties: { bad: { type: 'array', items: { type: 'object', additionalProperties: false,
    required: ['vid', 'reason'], properties: { vid: { type: 'integer' }, reason: { type: 'string' } } } } } }

const BATCHES = Array.isArray(args) ? args : JSON.parse(args)
const results = await pipeline(
  BATCHES,
  (key) => {
    const lvl = key.split('_')[0].toUpperCase()
    return agent(
      `You are a JLPT item writer (native-level Japanese). Read ${DIR}input_${key}.json — 30 entries of ` +
      `{vid, hw (headword), kana, gloss_pt, gloss_en, example (a REAL sentence using the word)}.\n\n` +
      `For EACH entry produce, in JAPANESE appropriate for JLPT ${lvl}:\n` +
      `1. "paraphrase": {"correct": a short Japanese word/phrase that could REPLACE hw in the example keeping ` +
      `the meaning (a true synonym/paraphrase; NEVER hw itself or its kana), "distractors": [3 plausible ` +
      `same-part-of-speech Japanese words that would clearly CHANGE the meaning]}.\n` +
      `2. "usage_wrong": [3 SHORT well-formed Japanese sentences (<=22 chars) that each use hw INCORRECTLY ` +
      `(wrong collocation/context — classic 用法 wrong options), vocabulary kept around ${lvl}].\n\n` +
      `Rules: Japanese only (no romaji/Portuguese), no em dash, exam-like brevity.\n` +
      `Write the FULL result to ${DIR}authored_${key}.json with the Write tool as ` +
      `{"items":[{"vid":123,"paraphrase":{"correct":"…","distractors":["…","…","…"]},"usage_wrong":["…","…","…"]}, …]} ` +
      `covering ALL 30 vids. Then return {"done": true}.`,
      { label: `author:${key}`, phase: 'Author', schema: ACK }
    ).then((r) => ({ key, ok: !!(r && r.done) }))
  },
  (prev) => {
    if (!prev.ok) return { key: prev.key, bad: [{ vid: -1, reason: 'author-failed' }] }
    const key = prev.key
    return agent(
      `You are a strict native-level JLPT reviewer. Compare ${DIR}input_${key}.json (facts) with ` +
      `${DIR}authored_${key}.json (proposed items). For EACH item check: (1) paraphrase.correct is a REAL ` +
      `synonym/paraphrase fitting the example sentence; (2) each paraphrase distractor clearly changes the ` +
      `meaning yet is plausible; (3) each usage_wrong sentence is well-formed Japanese but a clearly INCORRECT ` +
      `use of the word (an acceptable use = FAIL); (4) natural Japanese, right level, no romaji/pt/em dash.\n` +
      `Return {"bad":[{vid, reason}]} for failing items only (empty if all pass). Be strict.`,
      { label: `verify:${key}`, phase: 'Verify', schema: VERIFY_SCHEMA }
    ).then((v) => ({ key, bad: (v && v.bad) || [] }))
  }
)
const flagged = {}
for (const r of results.filter(Boolean)) flagged[r.key] = r.bad
log('author-exam-items: ' + results.filter(Boolean).map((r) => `${r.key}:${r.bad.length} flagged`).join(' '))
return { flagged }
