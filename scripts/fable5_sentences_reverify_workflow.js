export const meta = {
  name: 'fable5-sentences-reverify',
  description: 'Verify-only pass for pending sentence findings (finder step already done; verifiers lost to a session limit)',
  phases: [{ title: 'Verify' }],
}
// args: group keys like ["001","014",...] — each key K names a file
// research/derived/fable5_validation/phase3_reverify/<wave>/K.json holding {path: batch file, findings: [...]}
// (written by the wave-save step). Same 2-independent-verifier merge as fable5_sentences_workflow.js,
// verdicts matched BY (slug, field) so reordering can't misalign. Optionally pass {wave, keys} as args.
const ROOT = ''  // repo-relative: agents run with the repo as cwd (machine-portable)
const A = args ? (Array.isArray(args) ? { wave: 'wave1', keys: args } : (typeof args === 'string' ? JSON.parse(args) : args)) : null
const WAVE = (A && A.wave) || 'wave1'
const KEYS = A ? (Array.isArray(A) ? A : A.keys) : []
const GDIR = ROOT + 'research/derived/fable5_validation/phase3_reverify/' + WAVE + '/'

const VERDICTS = {
  type: 'object',
  additionalProperties: false,
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['slug', 'field', 'verdict'],
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

const verifyPrompt = (key) => `You are an adversarial reviewer. A QA pass over a dissected-sentence batch produced findings that still need verification. Read ${GDIR}${key}.json with the Read tool — it holds {path, findings}: 'path' is the batch file (read it too for ground truth), 'findings' are the claims to judge.

Your job is to try to REFUTE each finding: decide whether it is a real defect that must be fixed, or a false positive (over-picky, purely stylistic, content actually correct, or the finding itself wrong about the Japanese or the Portuguese).

Remember the batch conventions: phonetic kana/romaji (は→わ, へ→え, を→お is INTENTIONAL — do not confirm findings that flag it); lit_en/lit_pt are deliberately literal; gen=false sentences are real human Japanese (authoritative); Japanese punctuation inside romaji is a KNOWN systemic issue (findings about it = refute as duplicates).

Rules:
- Default to 'refuted' when the current content is defensible.
- 'confirmed' only when the current content is genuinely wrong or clearly below professional quality (wrong grammar fact, wrong in-context reading, sense-changing mistranslation, ungrammatical generated JP, European-Portuguese wording).
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, echoing each finding's slug AND field exactly as given.
Answer only via the structured output.`

const results = await pipeline(
  KEYS,
  (key) => parallel([0, 1].map((k) =>
    () => agent(verifyPrompt(key), { label: `verify${k}:${key}`, phase: 'Verify', schema: VERDICTS })
  )).then((vs) => ({ key, votes: vs })),
  async (prev) => {
    // findings themselves come back to the orchestrator via a tiny reader agent-free trick:
    // we re-emit only verdict merges keyed by slug+field; the save step joins them to the wave file.
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
  }
)

const ok = results.filter(Boolean)
const all = ok.flatMap((x) => x.verdicts || [])
const summary = {
  groups: KEYS.length, groups_done: ok.length, verdicts: all.length,
  confirmed: all.filter((f) => f.verdict === 'confirmed').length,
  disputed: all.filter((f) => f.verdict === 'disputed').length,
  rejected: all.filter((f) => f.verdict === 'rejected').length,
}
log(`sentences re-verify done: ${JSON.stringify(summary)}`)
return { summary, verdicts: all }
