export const meta = {
  name: 'fable5-vocab-validation',
  description: 'Validate 7,401 vocab glosses (EN + pt-BR) — finders + adversarial verify',
  phases: [
    { title: 'Find', detail: '247 finder agents, 30 vocab each' },
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
          field: { type: 'string', description: "Defective part, e.g. 'senses[0].en' | 'senses[1].pt' | 'romaji'" },
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

const finderPrompt = (path) => `You are a professional Japanese-English-Brazilian Portuguese lexicographer doing final QA on the vocabulary dictionary of a JLPT-oriented Japanese course for Brazilians.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} where each item is one vocabulary entry:
- hw: headword (kanji or kana form), kana: reading, romaji, level, class: verb/adjective class — hw/kana/pos come from JMdict facts, given as CONTEXT (do not validate hw/kana).
- senses: array of {pos, misc, register, en, pt} — the 'en' gloss list and 'pt' (Brazilian Portuguese) gloss list are AI-authored and UNDER REVIEW.

For EVERY item and EVERY sense, check:
1. EN glosses are correct for THIS lexeme (the exact hw+kana pair) and match the sense's pos. Watch for: glosses of a homophone or near-synonym lexeme (暑い vs 熱い vs 厚い), glosses that fit a different sense of the word than the pos indicates, invented meanings, a missing must-know core meaning.
2. pt glosses are faithful renderings of the same sense AND natural Brazilian Portuguese (NEVER European Portuguese). Watch for false friends (e.g. Japanese 大丈夫 is not "daijoubu = ótimo"), wrong gender/number, wrong register (a vulgar/slang word glossed neutrally or vice versa; the register/misc tags tell you the expected tone), accent/spelling errors.
3. EN-pt alignment per sense: same core meaning set; word-for-word symmetry NOT required. Curated conciseness is intended (rare/archaic senses are deliberately omitted; do not flag that).
4. romaji matches the kana (wapuro style, e.g. 'ou' for おう, is accepted; do not flag style).

Severity:
- critical: teaches something FALSE (wrong meaning, another word's gloss, sense-changing mistranslation)
- major: must-know core sense missing or misleading; register mismatch that could embarrass a learner; pt-PT vocabulary
- minor: typo, accent error, clearly-awkward-but-correct wording

Do NOT flag: sense ordering, curation choices, synonyms you would merely have preferred, hw/kana/pos facts, romaji transliteration style.

Be conservative: report ONLY defects a professional reviewer would definitely fix. If unsure, do not report. Set checked to the number of items in the file. Answer only via the structured output.`

const verifyPrompt = (path, findings) => `You are an adversarial reviewer. A QA pass over a vocabulary-dictionary batch produced the findings below. Your job is to try to REFUTE each one: decide whether it is a real defect that must be fixed, or a false positive (over-picky, purely stylistic, content actually correct, or the finding itself wrong about the Japanese or the Portuguese).

Ground-truth data: read the batch file at ${path} (hw/kana/pos are JMdict facts; en/pt glosses are under review).

Findings to judge (JSON):
${JSON.stringify(findings)}

Rules:
- Default to 'refuted' when the current content is defensible for a learner dictionary.
- 'confirmed' only when the current content is genuinely wrong or clearly below professional quality.
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, in the SAME ORDER as given, echoing each finding's slug.
Answer only via the structured output.`

const pad = (n) => String(n).padStart(3, '0')
const BASE = 'research/derived/fable5_validation/batches/vocab'
const COUNT = 247
// args (optional): array of batch indices to run, e.g. [4, 14, 15, ...] — for resuming in waves.
const IDX = args ? (Array.isArray(args) ? args : JSON.parse(args)) : Array.from({ length: COUNT }, (_, i) => i)
const paths = IDX.map((i) => `${BASE}/vocab-${pad(i)}.json`)
const idOf = (path) => path.slice(-8, -5)

const results = await pipeline(
  paths,
  (path) => agent(finderPrompt(path), { label: `find:${idOf(path)}`, phase: 'Find', schema: FINDINGS }),
  (found, path) => {
    if (!found) return { path, checked: 0, findings: [], failed: true }
    if (!found.findings || found.findings.length === 0) return { path, checked: found.checked, findings: [] }
    return parallel([0, 1].map((k) =>
      () => agent(verifyPrompt(path, found.findings), { label: `verify${k}:${idOf(path)}`, phase: 'Verify', schema: VERDICTS })
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
log(`vocab validation done: ${JSON.stringify(summary)}`)
return { summary, findings }
