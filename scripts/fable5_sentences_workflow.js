export const meta = {
  name: 'fable5-sentence-validation',
  description: 'Validate 5,565 sentences: JP, kana/romaji, EN + pt-BR translations, literal translations, structure explanations, token glosses',
  phases: [
    { title: 'Find', detail: '371 finder agents, 15 sentences each' },
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
          field: { type: 'string', description: "Defective part: 'jp' | 'kana' | 'romaji' | 'en' | 'pt' | 'lit_en' | 'lit_pt' | 'expl_en' | 'expl_pt' | 'tokens[i].r' | 'tokens[i].en' | 'tokens[i].pt' | 'tokens[i].role'" },
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

const finderPrompt = (path) => `You are a professional Japanese linguist and Japanese-English-Brazilian Portuguese translator doing final QA on the dissected sentence bank of a JLPT-oriented Japanese course for Brazilians.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} where each item is one sentence:
- jp: the Japanese sentence. gen: true = AI-GENERATED Japanese (validate the Japanese itself); gen: false = real human sentence from Tatoeba/JEC (the Japanese is authoritative, do NOT flag its style or punctuation).
- kana: PHONETIC transcription. CONVENTION (intentional, do NOT flag): particles are written as pronounced (は→わ, へ→え, を→お). DO flag actually-wrong readings (wrong kanji reading in context, e.g. 行った as おこなった where context says いった; missing/extra syllables).
- romaji: phonetic romanization. KNOWN ISSUE already recorded (do NOT re-report): Japanese punctuation 。！？ left in romaji, and katakana segments left unromanized.
- en / pt: natural translations (pt = Brazilian Portuguese). lit_en / lit_pt: LITERAL structural translations — their job is to mirror JP structure (do NOT flag literalness there; DO flag inaccuracy).
- expl_en / expl_pt: a beginner-friendly structure explanation. Both language versions must be factually correct about the grammar and consistent with each other.
- tokens: [{s: surface, r: reading, en/pt: contextual gloss, role: grammatical role in pt-BR, note: conjugation note}].
- level: claimed JLPT difficulty (context only).

For EVERY item, check in this order of importance:
1. GRAMMAR FACTS in expl_en/expl_pt: form names, particle functions, conjugation identifications must be correct. A wrong grammar claim is critical (it teaches something false).
2. TRANSLATION ACCURACY: en faithful to jp; pt faithful to jp AND natural Brazilian Portuguese (register mirrors the JP: casual JP may use "cê/tá/né" sparingly, polite JP → neutral-polite pt). Literal fields must be accurate mirrors.
3. TOKEN DATA: reading r correct IN CONTEXT; gloss en/pt correct IN CONTEXT (a gloss that fits another sense of the word but not this sentence is a defect); role correct.
4. kana: correct phonetic reading of the full sentence (respecting the わ/え/お particle convention).
5. If gen=true: the Japanese is grammatical, natural (something a native would say), and uses vocabulary/grammar plausible for its level. Unnatural or wrong generated JP is critical.

Severity:
- critical: wrong grammar fact, wrong reading, sense-changing mistranslation, ungrammatical/unnatural generated JP
- major: misleading translation nuance, wrong register, wrong token role, European-Portuguese wording
- minor: typo, accent error, awkward-but-correct phrasing

Do NOT flag: the phonetic kana/romaji particle convention, JP punctuation inside romaji (known), literalness of lit_* fields, style of real (gen=false) Japanese, translation choices that are defensibly equivalent, or "Quanto a..." phrasing inside lit_* and expl_* fields (it is the intended teaching device there).

Be conservative: report ONLY defects a professional reviewer would definitely fix. If unsure, do not report. Set checked to the number of items in the file. Answer only via the structured output.`

const verifyPrompt = (path, findings) => `You are an adversarial reviewer. A QA pass over a dissected-sentence batch produced the findings below. Your job is to try to REFUTE each one: decide whether it is a real defect that must be fixed, or a false positive (over-picky, purely stylistic, content actually correct, or the finding itself wrong about the Japanese or the Portuguese).

Ground-truth data: read the batch file at ${path}. Remember the intentional conventions: phonetic kana/romaji (は→わ, へ→え, を→お); lit_en/lit_pt are deliberately literal; gen=false sentences are real human Japanese (authoritative); Japanese punctuation inside romaji is a KNOWN systemic issue (findings about it should be refuted as duplicates).

Findings to judge (JSON):
${JSON.stringify(findings)}

Rules:
- Default to 'refuted' when the current content is defensible.
- 'confirmed' only when the current content is genuinely wrong or clearly below professional quality.
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, in the SAME ORDER as given, echoing each finding's slug.
Answer only via the structured output.`

const pad = (n) => String(n).padStart(3, '0')
const BASE = 'research/derived/fable5_validation/batches/sentences'
const COUNT = 371
// args (optional): array of batch indices to run, e.g. [0,1,...,61] — for resuming in waves.
const IDX = args ? (Array.isArray(args) ? args : JSON.parse(args)) : Array.from({ length: COUNT }, (_, i) => i)
const paths = IDX.map((i) => `${BASE}/sentences-${pad(i)}.json`)
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
log(`sentence validation done: ${JSON.stringify(summary)}`)
return { summary, findings }
