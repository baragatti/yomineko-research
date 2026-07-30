export const meta = {
  name: 'fable5-lesson-validation',
  description: 'Validate 314 lesson bodies + exercises, 286 reading boxes, 50 topic metadata entries',
  phases: [
    { title: 'Find', detail: '157 lesson + 15 reading + 5 topic finder agents' },
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
          field: { type: 'string', description: "Defective part: 'title' | 'description' | 'objectives[i]' | 'body' | 'exercises[i].prompt' | 'exercises[i].answer' | 'exercises[i].explanation' | 'tokens[i].r' | 'en' | 'pt'" },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          issue: { type: 'string', description: 'Concise English description of the defect, max 300 chars' },
          current: { type: 'string', description: 'The defective current text (short excerpt for body defects), max 200 chars' },
          suggested: { type: 'string', description: 'Corrected text, max 200 chars' },
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

const lessonPrompt = (path) => `You are a professional Japanese teacher and Brazilian-Portuguese pedagogy editor doing final QA on course lessons for Brazilians learning Japanese.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} with 2 lessons, each with:
- title, description, objectives (pt-BR, learner-facing)
- body: lesson prose in a custom XML-like markup. <jp reading="...">JP text</jp> shows furigana; <grammar ref>/<vocab ref>/<sent ref>/<reading> reference by ID (structural integrity is machine-gated separately — do NOT validate refs or markup structure).
- exercises: [{id, type, prompt, answer: {choices, correct}, explanation}].

For EVERY lesson, check:
1. EXERCISES first (drilled directly): answer.correct must be genuinely correct; EVERY distractor in choices must be genuinely wrong (a second acceptable choice is critical); explanation must be factually right and consistent with the correct answer.
2. JAPANESE in the body: every JP example is grammatical and natural; every <jp reading="..."> attribute is the correct ORTHOGRAPHIC kana reading of the enclosed text (here は stays は — this is furigana, unlike the corpus phonetic fields); romanization and pronunciation/mora claims are correct.
3. GRAMMAR CLAIMS in the prose: formation rules, particle functions, politeness claims, kanji facts — all must be true.
4. pt-BR QUALITY: natural Brazilian Portuguese (never European Portuguese), beginner-clear, no sense-changing errors in translations of the JP examples.

Severity:
- critical: wrong exercise answer/valid distractor, false grammar/kanji fact, wrong furigana reading, ungrammatical JP example
- major: misleading explanation, sense-changing translation, pt-PT wording
- minor: typo, accent error, awkward-but-correct phrasing

Do NOT flag: markup/refs, didactic tone ("você", contractions), teaching-order choices, simplifications that are pedagogically standard AND true, bracketed molds like "[lugar] に [coisa] が あります" (house convention), or missing content (coverage is gated elsewhere).

Be conservative: report ONLY defects a professional reviewer would definitely fix. If unsure, do not report. Set checked to the number of lessons. For body defects, quote a SHORT excerpt in 'current'. Answer only via the structured output.`

const readingPrompt = (path) => `You are a professional Japanese linguist and JP-to-Brazilian-Portuguese translator doing final QA on in-lesson reading-practice boxes.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} where each item is one reading passage:
- jp: the Japanese text (SELECTED from verified real sentences — do not flag its style).
- tokens: [{s: surface, r: kana reading, ro: romaji}]. CONVENTION (intentional, do NOT flag): readings are PHONETIC (particle は→わ, へ→え, を→お). KNOWN ISSUE (do NOT re-report): Japanese punctuation left in ro.
- en / pt: translations (pt = Brazilian Portuguese), UNDER REVIEW.

For EVERY item check: (1) each token reading r is correct IN CONTEXT (wrong kanji reading = critical); (2) ro transliterates r (beyond the known punctuation issue); (3) pt is faithful AND natural Brazilian Portuguese; (4) en is faithful.

Severity: critical = wrong reading or sense-changing mistranslation; major = misleading nuance, pt-PT wording; minor = typo/awkward.

Be conservative: report ONLY defects a professional reviewer would definitely fix. Set checked to the number of items. Answer only via the structured output.`

const topicPrompt = (path) => `You are a Brazilian-Portuguese editor doing final QA on course topic metadata for a Japanese course.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} with topic titles + descriptions (pt-BR, learner-facing).

For EVERY item check: natural Brazilian Portuguese (never European Portuguese), no factual errors about Japanese in the description, no typos/accent errors, clear and inviting for a beginner.

Severity: critical = false claim about Japanese; major = pt-PT wording or confusing description; minor = typo/awkward.

Be conservative: report ONLY defects a professional reviewer would definitely fix. Set checked to the number of items. Answer only via the structured output.`

const verifyPrompt = (kind, path, findings) => `You are an adversarial reviewer (expert in Japanese and Brazilian Portuguese). A QA pass over course ${kind} content produced the findings below. Try to REFUTE each one: real must-fix defect, or false positive (over-picky, stylistic, actually correct, or itself wrong)?

Ground-truth data: read the batch file at ${path}. Conventions that must NOT be treated as defects: reading-box token readings are phonetic (は→わ); Japanese punctuation inside romaji is a known systemic issue; lesson furigana (<jp reading>) is orthographic; markup/ref IDs are machine-gated elsewhere; informal didactic tone is house style.

Findings to judge (JSON):
${JSON.stringify(findings)}

Rules:
- Default to 'refuted' when the current content is defensible.
- 'confirmed' only when genuinely wrong or clearly below professional quality.
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, in the SAME ORDER as given, echoing each finding's slug.
Answer only via the structured output.`

const pad = (n) => String(n).padStart(3, '0')
const B = 'research/derived/fable5_validation/batches'
const items = []
for (let i = 0; i < 257; i++) items.push({ kind: 'lesson', path: `${B}/lessons/lessons-${pad(i)}.json` })
for (let i = 0; i < 15; i++) items.push({ kind: 'reading', path: `${B}/readings/readings-${pad(i)}.json` })
for (let i = 0; i < 9; i++) items.push({ kind: 'topic', path: `${B}/topics/topics-${pad(i)}.json` })

const promptFor = (it) => it.kind === 'lesson' ? lessonPrompt(it.path) : it.kind === 'reading' ? readingPrompt(it.path) : topicPrompt(it.path)

const IDX = args ? (Array.isArray(args) ? args : JSON.parse(args)) : null
const picked = IDX ? IDX.map((i) => items[i]).filter(Boolean) : items
const results = await pipeline(
  picked,
  (it, _o, i) => agent(promptFor(it), { label: `find:${it.kind}:${pad(i)}`, phase: 'Find', schema: FINDINGS }),
  (found, it, i) => {
    if (!found) return { path: it.path, kind: it.kind, checked: 0, findings: [], failed: true }
    if (!found.findings || found.findings.length === 0) return { path: it.path, kind: it.kind, checked: found.checked, findings: [] }
    return parallel([0, 1].map((k) =>
      () => agent(verifyPrompt(it.kind, it.path, found.findings), { label: `verify${k}:${it.kind}:${pad(i)}`, phase: 'Verify', schema: VERDICTS })
    )).then((vs) => {
      const merged = found.findings.map((f, idx) => {
        const v0 = vs[0] && vs[0].verdicts && vs[0].verdicts[idx]
        const v1 = vs[1] && vs[1].verdicts && vs[1].verdicts[idx]
        const avail = [v0, v1].filter(Boolean).length
        const confirms = [v0, v1].filter((v) => v && v.verdict === 'confirmed').length
        const verdict = avail === 0 ? 'unverified' : (confirms === avail ? 'confirmed' : (confirms === 0 ? 'rejected' : 'disputed'))
        const fix = (v0 && v0.fixed_suggestion) || (v1 && v1.fixed_suggestion) || f.suggested
        const notes = [v0, v1].filter(Boolean).map((v) => v.note).filter(Boolean)
        return { ...f, kind: it.kind, verdict, fix, notes }
      })
      return { path: it.path, kind: it.kind, checked: found.checked, findings: merged }
    })
  }
)

const ok = results.filter(Boolean)
const findings = ok.flatMap((x) => x.findings || [])
const summary = {
  batches: items.length,
  batches_done: ok.filter((x) => !x.failed).length,
  checked: ok.reduce((a, x) => a + (x.checked || 0), 0),
  total_findings: findings.length,
  confirmed: findings.filter((f) => f.verdict === 'confirmed').length,
  disputed: findings.filter((f) => f.verdict === 'disputed').length,
  rejected: findings.filter((f) => f.verdict === 'rejected').length,
}
log(`lesson/reading/topic validation done: ${JSON.stringify(summary)}`)
return { summary, findings }
