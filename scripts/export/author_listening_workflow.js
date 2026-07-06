export const meta = {
  name: 'author-listening',
  description: 'Author JLPT listening (聴解) text scripts per design/listening.md, adversarially verified',
  phases: [{ title: 'Author' }, { title: 'Verify' }],
}
// args: batch keys like ["n5_task",...] -> reads input_listen_<key>.json, writes authored_listen_<key>.json.
// Same batched author+verify pattern as author_reading_comp_workflow.js ({done} ack; {bad:[{n|slug,reason}]}).
const ROOT = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/'
const DIR = ROOT + 'research/derived/reauthor/exam_authored/'

const ACK = { type: 'object', additionalProperties: false, required: ['done'],
  properties: { done: { type: 'boolean' }, note: { type: 'string' } } }
const VERIFY_SCHEMA = { type: 'object', additionalProperties: false, required: ['bad'],
  properties: { bad: { type: 'array', items: { type: 'object', additionalProperties: false,
    required: ['ref', 'reason'], properties: { ref: { type: 'string' }, reason: { type: 'string' } } } } } }

const COMMON =
  'COMMON RULES: Japanese only (no romaji/Portuguese; full-width Latin like ＦＡＱ ok); no em dash. ' +
  'Vocabulary and grammar AT or BELOW the level (N5 = textbook-polite です/ます; N4/N3 may use natural ' +
  'spoken contractions 〜てる/〜ちゃう where fitting). Speakers ONLY from M1 M2 F1 F2 (dialogue voices; M=male, ' +
  'F=female — must match any 男の人/女の人 in setting/question) and N (narrator). Times/prices in standard ' +
  'orthography (３時、５００円). Each script text field is one TTS unit — no stage directions, no markup.'

const FORMATS = {
  task:
    'FORMAT listening_task (課題理解). Output item {n, script, question, correct, distractors[3]}. ' +
    'script[0] = {"speaker":"N","text": setting line like お店で男の人と女の人が話しています。}; then ' +
    'dialogue turns alternating two voices (N5: 2-4 short turns; N4: 3-5; N3: 4-7). question = a standard ' +
    'task formula about ONE speaker (…はこのあと何をしますか。／…は何を買いますか。). THE CRAFT: all 4 ' +
    'options (correct + 3 distractors) must be MENTIONED in the dialogue — three get rejected or changed ' +
    'mid-conversation, exactly one is the final decision. Options = short parallel noun/verb phrases. ' +
    'Build each scenario around at least ONE of the item\'s seed words.',
  point:
    'FORMAT listening_point (ポイント理解). Output item {n, script, question, correct, distractors[3]}. ' +
    'Same script shape as task (N-setting + dialogue). question targets ONE specific point (いつ／どこ／だれ／' +
    'いくら／どうして…). The dialogue must mention several candidate values (times, prices, places, reasons) ' +
    'with corrections/changes so only one is right; the 4 options are those mentioned candidates, short and ' +
    'parallel. Build each scenario around at least ONE seed word.',
  gist:
    'FORMAT listening_gist (概要理解, N3). Output item {n, script, question, correct, distractors[3]}. ' +
    'script[0] = N-setting (テレビで女の人が話しています。 etc.); then ONE speaker\'s monologue of 3-6 ' +
    'sentences (an announcement, opinion, or explanation). question = gist formula (何について話していますか。' +
    '／…が一番言いたいことは何ですか。). Options = 4 short parallel topic/claim phrases; only one matches ' +
    'the monologue\'s main point (distractors = side details or plausible-but-absent topics). Use >=1 seed word.',
  say:
    'FORMAT listening_say (発話表現). Output item {n, script, correct, distractors[2]} (NO question field). ' +
    'script = exactly one turn {"speaker":"N","text": situation of 1-2 sentences ending with 何と言いますか。}. ' +
    'correct = the natural utterance for that situation; the 2 distractors = pragmatically WRONG utterances ' +
    '(wrong direction of giving/receiving あげる／くれる, wrong politeness target, wrong verb/aspect) that a ' +
    'learner might confuse. All 3 options parallel in shape. Use >=1 seed word per situation.',
  reply:
    'FORMAT listening_reply (即時応答). Input items are {slug, jp} — jp is a REAL sentence. Output item ' +
    '{slug, script, correct, distractors[2]}. script = exactly one turn {"speaker":"M1" or "F1","text": jp ' +
    'VERBATIM — copy it byte-for-byte, do not alter ANY character}. correct = a natural short response ' +
    '(usually <=12 chars); the 2 distractors = pragmatically wrong responses (echo confusion, wrong ' +
    'tense/polarity, off-topic politeness formula). All 3 responses parallel in register.',
}

const BATCHES = Array.isArray(args) ? args : JSON.parse(args)
const results = await pipeline(
  BATCHES,
  (key) => {
    const [lvl, sub] = key.split('_')
    return agent(
      `You are a JLPT listening-script writer (native-level, natural SPOKEN Japanese). Read ` +
      `${DIR}input_listen_${key}.json ({sub, level, count, items}). Write ONE ${lvl.toUpperCase()} item per ` +
      `input item.\n\n${FORMATS[sub]}\n\n${COMMON}\n\n` +
      `Write ALL items to ${DIR}authored_listen_${key}.json with the Write tool as {"items":[…]} (carry over ` +
      `each input item's ${sub === 'reply' ? '"slug"' : '"n"'}). Then return {"done": true}.`,
      { label: `author:${key}`, phase: 'Author', schema: ACK }
    ).then((r) => ({ key, ok: !!(r && r.done) }))
  },
  (prev) => {
    if (!prev.ok) return { key: prev.key, bad: [{ ref: '*', reason: 'author-failed' }] }
    const key = prev.key
    const sub = key.split('_')[1]
    return agent(
      `You are a strict native-level JLPT listening reviewer. Compare ${DIR}input_listen_${key}.json with ` +
      `${DIR}authored_listen_${key}.json. The items must follow:\n${FORMATS[sub]}\n${COMMON}\n\n` +
      `For EACH item check: (1) natural SPOKEN Japanese at or below the level; (2) the question/situation is ` +
      `answerable from the script ALONE and the keyed answer is truly entailed; (3) every distractor is ` +
      `clearly wrong (for task/point: mentioned-then-rejected, never also-right; a distractor that could ` +
      `also be correct = FAIL); (4) options parallel in form — the key must not be pickable by shape alone; ` +
      `(5) speaker tags coherent (genders match 男/女 mentions; turns alternate sensibly)` +
      (sub === 'reply' ? `; (6) script text is byte-identical to the input jp` : '') + `.\n` +
      `Return {"bad":[{ref, reason}]} for failing items only — ref = the item's ` +
      `${sub === 'reply' ? 'slug' : 'n (as a string)'}. Empty array if all pass. Be strict.`,
      { label: `verify:${key}`, phase: 'Verify', schema: VERIFY_SCHEMA }
    ).then((v) => ({ key, bad: (v && v.bad) || [] }))
  }
)
const flagged = {}
for (const r of results.filter(Boolean)) flagged[r.key] = r.bad
log('author-listening: ' + results.filter(Boolean).map((r) => `${r.key}:${r.bad.length}`).join(' '))
return { flagged }
