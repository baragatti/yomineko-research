export const meta = {
  name: 'fable5-conjugation-validation',
  description: 'Validate 1,157 conjugation tables — every form checked (surface, kana, romaji, class)',
  phases: [
    { title: 'Find', detail: '58 finder agents, 20 tables each' },
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
          field: { type: 'string', description: "Defective part: 'class' or the form name, e.g. 'te' | 'past' | 'potential' | 'polite_negative' (append .kana / .romaji when only that layer is wrong)" },
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

const finderPrompt = (path) => `You are a Japanese morphology expert doing final QA on the conjugation tables of a Japanese course for Brazilians. These tables are drilled in SRS, so ANY wrong form directly teaches an error — be thorough on every single form.

Read the JSON file at ${path} with the Read tool. It contains {"items": [...]} where each item is one conjugation table:
- hw: headword, kana: reading, kind: 'verb' | 'adjective', class: e.g. godan/ichidan/suru/kuru/i_adj/na_adj (UNDER REVIEW — verify it), level.
- forms: [{f: form name, s: surface (kanji+kana), k: kana, ro: romaji}] — ALL under review.

For EVERY item:
1. Verify the CLASS is correct for this lexeme. Classic traps: godan verbs that look ichidan (帰る, 入る, 走る, 要る, 切る, 知る, 減る, 限る, 喋る, 焦る, 参る, 滑る, 蹴る...), true ichidan (見る, 出る, 着る, 居る...), irregular する/来る and suru-compounds, いい/良い irregular adjective.
2. Verify EVERY form against the class: dictionary, negative, past, past_negative, te, masu/polite (+ polite variants), potential, volitional, conditional (ba/tara), imperative, passive, causative, adverbial, attributive — whichever appear. Check surface, kana, and that the kana matches the surface.
3. romaji should transliterate the kana. KNOWN ISSUE already recorded (do NOT re-report): katakana segments left unromanized (e.g. 'キャンプsuru') and Japanese punctuation in romaji. DO report other romaji mistakes (wrong syllables, missing sokuon doubling, wrong vowels).
4. Sanity: polite forms actually polite, negative forms actually negative, no form copied from a different verb, no ichidan-conjugated godan (e.g. 帰れる ok but 帰られる as potential of 帰る is a defect if labeled potential... careful: 帰られる IS valid as passive/honorific; judge by the form NAME).

Severity:
- critical: any wrong conjugated form (surface or kana) or wrong class
- major: romaji error (beyond the known systemic ones), form present under wrong name
- minor: inconsistent-but-unambiguous transliteration style

Do NOT flag: wapuro romaji style ('ou' for long o, 'tsu', 'shi', 'chi', 'fu'), missing forms (curation), the known katakana/punctuation romaji systemics, or valid alternative forms when the given one is also correct (e.g. 行ける potential; よくないです vs よくありません — both fine).

Be conservative but COMPLETE: every form of every item must actually be checked. Set checked to the number of items in the file. Answer only via the structured output.`

const verifyPrompt = (path, findings) => `You are an adversarial reviewer with expert Japanese morphology knowledge. A QA pass over conjugation tables produced the findings below. Try to REFUTE each one: is it a real conjugation/class/romaji error, or a false positive (a valid alternative form, correct after all, or covered by the known systemic romaji issues that should NOT be re-reported: katakana left unromanized, Japanese punctuation in romaji)?

Ground-truth data: read the batch file at ${path}.

Findings to judge (JSON):
${JSON.stringify(findings)}

Rules:
- Default to 'refuted' when the current form is actually correct or a valid variant.
- 'confirmed' only when the form/class/romaji is genuinely wrong.
- If a finding is real but its suggested fix is bad, return 'confirmed' with a corrected fixed_suggestion.
- Return EXACTLY one verdict per finding, in the SAME ORDER as given, echoing each finding's slug.
Answer only via the structured output.`

const pad = (n) => String(n).padStart(3, '0')
const BASE = 'research/derived/fable5_validation/batches/conjugations'
const COUNT = 58
const paths = Array.from({ length: COUNT }, (_, i) => `${BASE}/conjugations-${pad(i)}.json`)

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
log(`conjugation validation done: ${JSON.stringify(summary)}`)
return { summary, findings }
