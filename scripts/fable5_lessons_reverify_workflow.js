export const meta = {
  name: 'fable5-lessons-reverify',
  description: 'Verify-only pass for Phase-6 lesson findings whose verifiers died to a session cap',
  phases: [{ title: 'Verify' }],
}
// args: group keys like ["L008","L009",...] -> research/derived/fable5_validation/phase6_reverify/<wave>/
// <key>.json holding {path: the lesson batch file, findings: [...]}. Wave 1's finders completed but its
// verifiers were killed by the 5h cap, leaving 321 single-pass findings that must not be treated as real
// until adversarially judged. Same 2-independent-verifier merge as the sentences pass, verdicts matched by
// (slug, field). Deliberately NOT the sentence prompt: lesson records are authored courseware (body HTML,
// exercises, objectives), so the conventions that matter are different.
const A = args ? (Array.isArray(args) ? { wave: 'wave1', keys: args }
  : (typeof args === 'string' ? JSON.parse(args) : args)) : null
const WAVE = (A && A.wave) || 'wave1'
const KEYS = A ? (Array.isArray(A) ? A : A.keys) : []
const GDIR = 'research/derived/fable5_validation/phase6_reverify/' + WAVE + '/'

const VERDICTS = {
  type: 'object', additionalProperties: false, required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['slug', 'field', 'verdict'],
        properties: {
          slug: { type: 'string' },
          field: { type: 'string', description: "Echo the finding's field exactly" },
          verdict: { type: 'string', enum: ['confirmed', 'refuted'] },
          note: { type: 'string', description: 'One-line reason, max 200 chars' },
          fixed_suggestion: { type: 'string', description: 'Only when confirmed but the proposed fix itself needs correction' },
        },
      },
    },
  },
}

const prompt = (key) => `You are a strict adversarial reviewer of Brazilian-Portuguese Japanese courseware.
Read ${GDIR}${key}.json — it holds {path, findings}. Read the batch file at "path" too: it is the ground
truth for every claim. Judge each finding: is it a real defect a professional reviewer would fix, or a
false positive?

What these records are: authored lessons — "body" is custom-element HTML (<jp>, <vocab ref=...>, <kanji>,
<note>, <check>), plus title/description/objectives and exercises with prompt/answer/explanation. All
learner-facing text is pt-BR (never pt-PT); Japanese appears inside tags.

CONFIRM when the content is genuinely wrong or below professional quality:
- a false grammar claim, or a rule contradicted by the lesson's own example (these are the valuable ones);
- a wrong or truncated furigana reading in <jp reading="...">, or a reading that inserts/drops characters;
- an exercise whose prompt, answer and explanation disagree, so a learner following the prompt is graded
  wrong (e.g. the prompt demands kana but the answer is kanji with no accept list);
- a mistranslation that flips the form-meaning map being taught (tense, register, transitivity);
- pt-PT wording, English left in pt-BR text, missing accents/cedillas, or corpus-build metadata leaking
  into learner-facing prose.

REFUTE when the current content is defensible:
- house conventions (check the batch and siblings before calling something wrong — e.g. katakana is kept
  inside reading=, and 「forma ます」 is the established term);
- deliberate simplification appropriate to the level, or a gloss that is loose but not wrong;
- style preferences, and anything where the finding itself misstates the Japanese or the Portuguese.
If a finding is real but its suggested fix is wrong or incomplete, return 'confirmed' with a corrected
fixed_suggestion.

Return EXACTLY one verdict per finding, echoing each slug AND field exactly. Answer only via the
structured output.`

const results = await pipeline(
  KEYS,
  (key) => parallel([0, 1].map((k) =>
    () => agent(prompt(key), { label: `verify${k}:${key}`, phase: 'Verify', schema: VERDICTS })
  )).then((vs) => ({ key, votes: vs })),
  (prev) => {
    const maps = prev.votes.map((v) => {
      const m = {}
      if (v && v.verdicts) for (const x of v.verdicts) m[x.slug + '|' + x.field] = x
      return m
    })
    const keys = new Set([...Object.keys(maps[0] || {}), ...Object.keys(maps[1] || {})])
    const merged = []
    for (const kf of keys) {
      const picks = maps.map((m) => m[kf]).filter(Boolean)
      const confirms = picks.filter((p) => p.verdict === 'confirmed').length
      const verdict = picks.length === 0 ? 'unverified'
        : (confirms === picks.length ? 'confirmed' : (confirms === 0 ? 'rejected' : 'disputed'))
      const [slug, field] = kf.split('|')
      merged.push({ slug, field, verdict,
        fix: picks.map((p) => p.fixed_suggestion).find(Boolean) || null,
        notes: picks.map((p) => p.note).filter(Boolean) })
    }
    return { key: prev.key, verdicts: merged }
  },
)

const ok = results.filter(Boolean)
const all = ok.flatMap((x) => x.verdicts || [])
const summary = {
  groups: KEYS.length, groups_done: ok.length, verdicts: all.length,
  confirmed: all.filter((f) => f.verdict === 'confirmed').length,
  disputed: all.filter((f) => f.verdict === 'disputed').length,
  rejected: all.filter((f) => f.verdict === 'rejected').length,
}
log(`lessons re-verify done: ${JSON.stringify(summary)}`)
return { summary, verdicts: all }
