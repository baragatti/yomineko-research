export const meta = {
  name: 'fable5-diff-audit',
  description: 'Adversarial audit of the Phase-3 sentence before/after diff (the pre-apply gate)',
  phases: [{ title: 'Audit' }],
}
// args: batch keys like ["d000","d001",...] -> research/derived/fable5_validation/phase3_diff/<key>.json
// holding {sentences:[{slug, gen, sources, ops, before, after, violations}]}. Same gate that caught 18
// real defects in the vocab apply. Structural invariants are already machine-checked upstream; this pass
// judges MEANING and PEDAGOGY, which no invariant can.
const DIR = 'research/derived/fable5_validation/phase3_diff/'

const AUDIT_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['bad'],
  properties: {
    bad: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['slug', 'field', 'severity', 'reason'],
        properties: {
          slug: { type: 'string' },
          field: { type: 'string', description: 'The after-field that is wrong' },
          severity: { type: 'string', enum: ['critical', 'major', 'minor'] },
          reason: { type: 'string' },
          suggested: { type: 'string', description: 'Corrected value, when you are confident' },
        },
      },
    },
  },
}

const BATCHES = Array.isArray(args) ? args : JSON.parse(args)
const results = await pipeline(
  BATCHES,
  (key) => agent(
    `You are a strict adversarial auditor reviewing a proposed patch to a dissected Japanese sentence bank ` +
    `for a Brazilian-Portuguese course, BEFORE it is applied. Read ${DIR}${key}.json with the Read tool: ` +
    `each entry has {slug, gen, sources, ops (the confirmed defects being fixed), before, after}.\n\n` +
    `Compare "before" and "after" for EVERY sentence and report anything that must NOT ship:\n` +
    `1. The change does not actually fix the defect the op describes, or fixes it wrongly.\n` +
    `2. COLLATERAL DAMAGE: something correct in "before" became wrong or was dropped in "after".\n` +
    `3. JAPANESE CORRECTNESS: a reading that is wrong in context (rendaku, gemination, on/kun, counters, ` +
    `何 as なに vs なん, 一日 as ついたち vs いちにち); kana must keep the PHONETIC particle convention ` +
    `(は->わ, へ->え, を->お) - flag it if a fix broke that; romaji must mirror kana.\n` +
    `4. INTERNAL CONSISTENCY: after the change, do jp / kana / romaji / token readings / both explanations ` +
    `/ both literal translations still describe the SAME sentence? A fixed reading that is not reflected ` +
    `in an explanation quoting it is a defect.\n` +
    `5. pt-BR must be natural Brazilian Portuguese (never pt-PT: conectiva not conetiva, ` +
    `time not comboio, etc.); en must be English. No em dashes. No corpus-build metadata ` +
    `("coverage"/"cobertura", QA notes) newly introduced into learner-facing text.\n` +
    `6. LAYER A: for gen=false records (real Tatoeba Japanese) the "jp" and the source "en" must be ` +
    `UNCHANGED between before and after. Flag any such change as critical.\n` +
    `7. translation_literal.* must stay literal structure mirrors, and the "As for X / Quanto a X" device ` +
    `mirrors the topic particle は ONLY - never が, を or で.\n\n` +
    `Report ONLY problems a professional reviewer would insist on fixing; do not flag style preferences ` +
    `or the deliberate literalness of the lit_* fields. Return {"bad":[...]} - empty array if the whole ` +
    `batch is safe to ship.`,
    { label: `audit:${key}`, phase: 'Audit', schema: AUDIT_SCHEMA },
  ).then((r) => ({ key, bad: (r && r.bad) || [] })),
)

const ok = results.filter(Boolean)
const bad = ok.flatMap((r) => r.bad)
const bySeverity = {}
for (const b of bad) bySeverity[b.severity] = (bySeverity[b.severity] || 0) + 1
log(`diff audit: ${ok.length}/${BATCHES.length} batches, ${bad.length} objections ${JSON.stringify(bySeverity)}`)
return { summary: { batches: ok.length, objections: bad.length, bySeverity }, bad }
