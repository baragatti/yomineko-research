export const meta = {
  name: 'author-reading-comp',
  description: 'Author reading-comprehension questions (読解) over the verified reading passages, adversarially verified',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}
// args: batch keys like ["rc_n5_b1",...] — passages come from corpus/readings (real bank sentences,
// verified pt translation = ground truth of meaning). One author+verify chain per ~25-passage batch.
const ROOT = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/'
const DIR = ROOT + 'research/derived/reauthor/exam_authored/'

const ACK = { type: 'object', additionalProperties: false, required: ['done'],
  properties: { done: { type: 'boolean' }, note: { type: 'string' } } }
const VERIFY_SCHEMA = { type: 'object', additionalProperties: false, required: ['bad'],
  properties: { bad: { type: 'array', items: { type: 'object', additionalProperties: false,
    required: ['slug', 'reason'], properties: { slug: { type: 'string' }, reason: { type: 'string' } } } } } }

const BATCHES = Array.isArray(args) ? args : JSON.parse(args)
const results = await pipeline(
  BATCHES,
  (key) => {
    const lvl = key.split('_')[1].toUpperCase()
    return agent(
      `You are a JLPT reading-section item writer (native-level Japanese). Read ${DIR}input_${key}.json — ` +
      `an array of {slug, level, jp (a short passage of REAL Japanese sentences), pt (its verified ` +
      `Brazilian-Portuguese translation = ground truth of meaning)}.\n\n` +
      `For EACH passage write ONE comprehension question in JAPANESE at ${lvl} level:\n` +
      `- "question": a short 内容一致 question answerable ONLY from the passage (e.g. どうして…か。/ ` +
      `…はいつですか。/ 正しいものはどれか。). Keep the question's vocabulary AT or BELOW ${lvl}.\n` +
      `- "correct": the right answer (short Japanese phrase/sentence, <=20 chars where possible).\n` +
      `- "distractors": [3 short Japanese options of the same shape that are clearly WRONG per the passage ` +
      `(contradicted or not stated) yet plausible-looking].\n\n` +
      `Rules: Japanese only in question/options; no romaji/Portuguese; no em dash; do not copy option text ` +
      `verbatim from the passage for the correct answer when a light rephrase works (tests understanding, ` +
      `not string matching), but keep it unambiguous.\n` +
      `Write ALL results to ${DIR}authored_${key}.json with the Write tool as ` +
      `{"items":[{"slug":"read:…","question":"…","correct":"…","distractors":["…","…","…"]}, …]} covering ` +
      `every passage. Then return {"done": true}.`,
      { label: `author:${key}`, phase: 'Author', schema: ACK }
    ).then((r) => ({ key, ok: !!(r && r.done) }))
  },
  (prev) => {
    if (!prev.ok) return { key: prev.key, bad: [{ slug: '*', reason: 'author-failed' }] }
    const key = prev.key
    return agent(
      `You are a strict native-level JLPT reading reviewer. Compare ${DIR}input_${key}.json (passages + ` +
      `verified pt meaning) with ${DIR}authored_${key}.json. For EACH item check: (1) the question is ` +
      `natural Japanese, level-appropriate, and answerable from the passage ALONE; (2) "correct" is truly ` +
      `correct per the passage (cross-check against the pt translation); (3) every distractor is clearly ` +
      `wrong per the passage (contradicted or absent) — a distractor that could also be right = FAIL; ` +
      `(4) options are parallel in form; no romaji/Portuguese/em dash.\n` +
      `Return {"bad":[{slug, reason}]} for failing items only. Be strict.`,
      { label: `verify:${key}`, phase: 'Verify', schema: VERIFY_SCHEMA }
    ).then((v) => ({ key, bad: (v && v.bad) || [] }))
  }
)
const flagged = {}
for (const r of results.filter(Boolean)) flagged[r.key] = r.bad
log('author-reading-comp: ' + results.filter(Boolean).map((r) => `${r.key}:${r.bad.length}`).join(' '))
return { flagged }
