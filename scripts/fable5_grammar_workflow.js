export const meta = {
  name: 'fable5-grammar-validation',
  description: 'Validate 496 grammar points: labels, forms, explanations (EN + pt-BR)',
  phases: [
    { title: 'Find', detail: '50 finder agents, 10 grammar points each' },
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
          field: { type: 'string', description: "Defective part: 'label_en' | 'label_pt' | 'pattern' | 'register' | 'caution' | 'forms[i].en' | 'forms[i].pt' | 'expl_en' | 'expl_pt'" },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          issue: { type: 'string', description: 'Concise English description of the defect, max 280 chars' },
          current: { type: 'string', description: 'The defective current text, max 160 chars' },
          suggested: { type: 'string', description: 'Corrected text, max 160 chars' },
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

const finderPrompt = (path) => `You are a professional Japanese grammarian and Japanese-teaching expert (JLPT specialist) doing final QA on the grammar registry of a Japanese course for Brazilians.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} where each item is one grammar point:
- label_en / label_pt: short display labels. pattern: the structural pattern. register: register tags. caution: optional warning text.
- forms: [{form, en, pt}] — each surface form with its meaning in both languages.
- expl_en / expl_pt: the didactic explanation (Brazilian Portuguese for pt) — AI-authored, UNDER REVIEW.

For EVERY item, check:
1. GRAMMAR-FACTUAL CORRECTNESS (most important): does the explanation correctly describe what the pattern means, what it attaches to (verb form, noun, na-adjective...), its register, and how it differs from near-synonyms? Wrong formation rules, wrong attachment, wrong nuance direction, or mixing up two similar patterns (e.g. 〜そうだ hearsay vs appearance; は vs が claims; 〜たら vs 〜ば overreach) are critical.
2. Labels and form meanings: label_en/label_pt and each forms[i].en/pt must accurately name the pattern's meaning.
3. pt text is natural Brazilian Portuguese (never European Portuguese), clear for a beginner, and consistent with the en version (they should teach the same facts).
4. caution/register: correct and not misleading.

Severity:
- critical: a wrong grammar fact (formation, meaning, attachment, register class) that would teach something false
- major: misleading nuance, incomplete-to-the-point-of-confusing rule, wrong example claim, pt-PT wording
- minor: typo, accent error, awkward-but-correct phrasing

Do NOT flag: brevity (short explanations are intended; completeness lives in lessons), teaching-order choices, informal didactic tone ("você", "a gente", contractions are the house style), or simplifications that are pedagogically standard for the level as long as they are not false.

Be conservative: report ONLY defects a professional reviewer would definitely fix. If unsure, do not report. Set checked to the number of items in the file. Answer only via the structured output.`

const verifyPrompt = (path, findings) => `You are an adversarial reviewer with deep Japanese-grammar expertise. A QA pass over a grammar-registry batch produced the findings below. Your job is to try to REFUTE each one: decide whether it is a real defect that must be fixed, or a false positive (over-picky, purely stylistic, a defensible pedagogical simplification, or the finding itself wrong about the grammar).

Ground-truth data: read the batch file at ${path}.

Findings to judge (JSON):
${JSON.stringify(findings)}

Rules:
- Default to 'refuted' when the current content is defensible for a beginner course (standard pedagogical simplifications are NOT defects unless false).
- 'confirmed' only when the content states something genuinely wrong or clearly below professional quality.
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, in the SAME ORDER as given, echoing each finding's slug.
Answer only via the structured output.`

const pad = (n) => String(n).padStart(3, '0')
const BASE = 'research/derived/fable5_validation/batches/grammar'
const COUNT = 50
const paths = Array.from({ length: COUNT }, (_, i) => `${BASE}/grammar-${pad(i)}.json`)

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
log(`grammar validation done: ${JSON.stringify(summary)}`)
return { summary, findings }
