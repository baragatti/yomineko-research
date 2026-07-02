export const meta = {
  name: 'fable5-kanji-validation',
  description: 'Validate 2,131 kanji meanings (EN + pt-BR) — finders + adversarial verify',
  phases: [
    { title: 'Find', detail: '61 finder agents, 35 kanji each' },
    { title: 'Verify', detail: '2 adversarial skeptics per findings batch' },
  ],
}

const FINDINGS = {
  type: 'object',
  additionalProperties: false,
  required: ['checked', 'findings'],
  properties: {
    checked: { type: 'integer', description: 'How many items you actually validated' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['slug', 'field', 'severity', 'issue', 'current', 'suggested', 'confidence'],
        properties: {
          slug: { type: 'string', description: 'The exact slug of the defective record, copied from the batch file' },
          field: { type: 'string', description: "Defective part: 'en' | 'pt' | 'notes'" },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          issue: { type: 'string', description: 'Concise English description of the defect, max 280 chars' },
          current: { type: 'string', description: 'The defective current text, max 140 chars' },
          suggested: { type: 'string', description: 'Corrected text, max 140 chars' },
          confidence: { type: 'number', minimum: 0, maximum: 1 },
        },
      },
    },
  },
}

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
        required: ['slug', 'verdict'],
        properties: {
          slug: { type: 'string' },
          verdict: { type: 'string', enum: ['confirmed', 'refuted'] },
          note: { type: 'string', description: 'One-line reason, max 200 chars' },
          fixed_suggestion: { type: 'string', description: 'Only when confirmed but the proposed fix itself needs correction' },
        },
      },
    },
  },
}

const finderPrompt = (path) => `You are a professional Japanese-English-Brazilian Portuguese lexicographer doing final QA on the kanji dictionary of a JLPT-oriented Japanese course for Brazilians.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} where each item is one kanji:
- ch: the kanji character. level, strokes, radical, readings_fact: authoritative facts from KANJIDIC2/Unihan given as CONTEXT ONLY (do not validate them).
- en: curated English core meanings (AI-authored, UNDER REVIEW)
- pt: Brazilian Portuguese meanings (AI-authored, UNDER REVIEW)
- notes: optional note (under review when present)

For EVERY item, check:
1. EN meanings are correct for this exact character. Watch for: meanings that belong to a visually similar kanji (like 千/干, 未/末, 士/土, 徴/微), meanings of a compound word instead of the character itself, a missing PRIMARY meaning a learner must know, or a wrong/marginal meaning presented as core.
2. pt-BR meanings are faithful renderings of the same core senses AND natural Brazilian Portuguese (NEVER European Portuguese: no "telemóvel", "autocarro", "rapariga", "ecrã", "pequeno-almoço"). Correct spelling and accents. No false cognates.
3. EN-pt alignment: the pt list must cover the same core sense set. Word-for-word symmetry is NOT required; curated conciseness is intended.

Severity:
- critical: teaches something FALSE (wrong meaning, another character's meaning, a mistranslation that changes the sense)
- major: a must-know primary sense is missing, or a misleading/marginal sense is presented as core, or pt-PT vocabulary
- minor: typo, accent error, clearly-awkward-but-correct wording

Do NOT flag: sense ordering, curation choices (fewer senses than an exhaustive dictionary is intentional), synonyms you would merely have chosen instead, readings/strokes/radical (facts, not under review), or established conventions like 'Japan' as a meaning of 日.

Be conservative: report ONLY defects a professional reviewer would definitely fix. If unsure, do not report. Set checked to the number of items in the file. Answer only via the structured output.`

const verifyPrompt = (path, findings) => `You are an adversarial reviewer. A QA pass over a kanji-dictionary batch produced the findings below. Your job is to try to REFUTE each one: decide whether it is a real defect that must be fixed, or a false positive (over-picky, purely stylistic, content actually correct, or the finding itself wrong about the Japanese or the Portuguese).

Ground-truth data: read the batch file at ${path} (fields: ch = the kanji; en / pt = the meanings under review; readings_fact = authoritative readings for context).

Findings to judge (JSON):
${JSON.stringify(findings)}

Rules:
- Default to 'refuted' when the current content is defensible for a learner dictionary.
- 'confirmed' only when the current content is genuinely wrong or clearly below professional quality.
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, in the SAME ORDER as given, echoing each finding's slug.
Answer only via the structured output.`

const pad = (n) => String(n).padStart(3, '0')
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
const BASE = A.base || 'research/derived/fable5_validation/batches/kanji'
const COUNT = A.count || 61
const paths = Array.from({ length: COUNT }, (_, i) => `${BASE}/kanji-${pad(i)}.json`)
if (paths.length === 0) throw new Error('no batch paths resolved')

const results = await pipeline(
  paths,
  (path, _o, i) => agent(finderPrompt(path), { label: `find:${pad(i)}`, phase: 'Find', schema: FINDINGS }),
  (found, path, i) => {
    if (!found) return { path, checked: 0, findings: [], failed: true }
    if (!found.findings || found.findings.length === 0) return { path, checked: found.checked, findings: [] }
    return parallel([0, 1].map((k) =>
      () => agent(verifyPrompt(path, found.findings), { label: `verify${k}:${pad(i)}`, phase: 'Verify', schema: VERDICTS })
    )).then((vs) => {
      const merged = found.findings.map((f, idx) => {
        const v0 = vs[0] && vs[0].verdicts && vs[0].verdicts[idx]
        const v1 = vs[1] && vs[1].verdicts && vs[1].verdicts[idx]
        const avail = [v0, v1].filter(Boolean).length
        const confirms = [v0, v1].filter((v) => v && v.verdict === 'confirmed').length
        const verdict = avail === 0 ? 'unverified' : (confirms === avail ? 'confirmed' : (confirms === 0 ? 'rejected' : 'disputed'))
        const fix = (v0 && v0.fixed_suggestion) || (v1 && v1.fixed_suggestion) || f.suggested
        const notes = [v0, v1].filter(Boolean).map((v) => v.note).filter(Boolean)
        return { ...f, verdict, fix, notes }
      })
      return { path, checked: found.checked, findings: merged }
    })
  }
)

const ok = results.filter(Boolean)
const findings = ok.flatMap((x) => x.findings || [])
const summary = {
  batches: paths.length,
  batches_done: ok.filter((x) => !x.failed).length,
  checked: ok.reduce((a, x) => a + (x.checked || 0), 0),
  total_findings: findings.length,
  confirmed: findings.filter((f) => f.verdict === 'confirmed').length,
  disputed: findings.filter((f) => f.verdict === 'disputed').length,
  rejected: findings.filter((f) => f.verdict === 'rejected').length,
}
log(`kanji validation done: ${JSON.stringify(summary)}`)
return { summary, findings }