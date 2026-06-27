export const meta = {
  name: 'reauthor-lesson-format',
  description: 'Reformat + lightly enrich lesson bodies (vocab dumps -> lists, clean moldes, fix glued text), preserving all refs',
  phases: [{ title: 'Rewrite' }, { title: 'Verify' }],
}
// args = [{slug, file, issues:[...]}, ...]  (subset of research/_lesson_format_issues.json)
// ABSOLUTE paths: some workflow agents resolved relative paths under prototype/ (wrong CWD) and failed.
const ROOT = 'C:/Users/WiseWolf/IdeaProjects/code/yomineko-research/'
const DIR = ROOT + 'research/derived/lessons/'
const OUT = ROOT + 'research/derived/reauthor/lesson_format/'

const RULES =
  `You improve ONE pt-BR (Brazilian Portuguese) Japanese-lesson body for READABILITY + light enrichment, ` +
  `WITHOUT changing meaning, facts, readings, or translations. The body uses a small XML-like tag language.\n\n` +
  `HARD RULES (never violate):\n` +
  `1. Keep EVERY <sentence ref="sent:..."/>, <exercise ref="ex:..."/> and <reading ref="read:..."/> tag ` +
  `EXACTLY (same ref, same place in the flow). Never add, remove, reorder, or edit them.\n` +
  `2. Keep the final <checklist>...</checklist> block EXACTLY as-is (including each <check item-ref=...>).\n` +
  `3. Use ONLY these tags: heading (level="2"|"3"), p, list (ordered="false"), item, note ` +
  `(type="l1-advantage"|"l1-pitfall"|"tip"|"warning"|"culture"|"example"), text (optional weight="bold"), ` +
  `emphasis, jp (optional reading="<kana>"), ruby (base,reading), grammar|vocab|kanji (ref="..."), ` +
  `sentence|reading|exercise (ref="..."), break, checklist, check (optional item-ref). NO other tags, NO ` +
  `markdown, NO raw HTML.\n` +
  `4. ALL visible text must sit inside a <text>/<jp>/<emphasis>/<ruby> element. Never put bare text directly ` +
  `inside <p>/<item>/<heading>. Japanese characters must be inside <jp>...</jp> (add reading="<kana>" when the ` +
  `word has kanji); the ONLY exceptions are the <sentence>/<reading> tags (which you never touch). NEVER nest ` +
  `a <text> inside another <text> (e.g. <text><text weight="bold">X</text></text> is INVALID) — a <text> holds ` +
  `ONLY plain characters; for bold, use a separate sibling <text weight="bold">...</text>.\n` +
  `5. Do NOT invent new grammar/vocab/kanji refs. Only reuse refs that already appear in THIS body (you may ` +
  `drop a redundant one, but prefer keeping them). Refs must stay byte-identical (e.g. ref="vocab:建物").\n` +
  `6. pt-BR only. Natural, warm, didactic. NEVER use the em dash "—" (use comma, colon, or parentheses). No ` +
  `English, no "esp.", no slang.\n\n` +
  `WHAT TO FIX:\n` +
  `A. Run-on vocabulary "dumps" (a single <p> cramming many <vocab ref/>(reading, gloss) entries) -> convert ` +
  `into a <list ordered="false"> with ONE <item> per word: <item><vocab ref="vocab:X"/><text>: GLOSS</text>` +
  `</item>. The vocab chip already shows the reading, so DON'T repeat the kana in parentheses; just give the ` +
  `pt-BR meaning after ": ". Keep useful grouping (e.g. inanimate things that take あります vs living beings ` +
  `that take います) as a short intro <p> before each <list>.\n` +
  `B. "Molde"/pattern lines written with glued plus signs ("coisa +が+あります") -> rewrite as a clean ` +
  `pattern with bracketed placeholders and spaced particles, NO plus signs. Portuguese placeholder words ` +
  `(lugar, coisa, pessoa, ...) MUST be wrapped in [brackets] so they read as slots, not as Japanese. Example: ` +
  `<p><text weight="bold">Molde: </text><text>[lugar] </text><jp>に</jp><text> [coisa] </text><jp>が</jp>` +
  `<text> </text><jp>あります</jp></p>.\n` +
  `C. Glued Portuguese (e.g. significa"acima"e) -> add the missing spaces around bold/quotes.\n\n` +
  `ENRICH (lightly): where an explanation is too terse or assumes too much, ADD 1-2 short clarifying ` +
  `sentences in natural pt-BR. KEEP the existing good explanations; do not pad, do not shorten, do not change ` +
  `any factual claim, reading, or translation. The goal is "more explicative", not "rewritten".\n`

const REWRITE_SCHEMA = { type: 'object', required: ['done'], additionalProperties: false,
  properties: { done: { type: 'boolean' }, note: { type: 'string' } } }
const VERIFY_SCHEMA = { type: 'object', required: ['ok'], additionalProperties: false, properties: {
  ok: { type: 'boolean' },
  issues: { type: 'array', items: { type: 'string' } } } }

// already done + verified in the pilot — skip on the full run
const DONE = new Set(['les:n5-particulas-lugar-01', 'les:n4-aspecto-02', 'les:n4-aspecto-07', 'les:n3-perspectiva-01'])
const LISTFILE = args === 'todo' ? ROOT + 'research/_lesson_format_todo.json'
  : ROOT + 'research/_lesson_format_issues.json'
let LESSONS = Array.isArray(args) ? args : (args && args !== 'all' && args !== 'todo' ? JSON.parse(args) : null)
if (!LESSONS) {
  // the workflow runtime can't read files; an agent fetches the affected-lesson list for us.
  const LIST_SCHEMA = { type: 'object', required: ['items'], additionalProperties: false, properties: {
    items: { type: 'array', items: { type: 'object', required: ['slug', 'file'], additionalProperties: true,
      properties: { slug: { type: 'string' }, file: { type: 'string' },
        issues: { type: 'array', items: { type: 'string' } } } } } } }
  const r = await agent(
    `Read the JSON file ${LISTFILE} and return its entire contents as {"items":[{slug,file,issues}, ...]} ` +
    'exactly as stored (do not filter or alter anything).',
    { label: 'load-list', phase: 'Rewrite', schema: LIST_SCHEMA })
  LESSONS = (r && r.items ? r.items : []).filter((x) => args === 'todo' || !DONE.has(x.slug))
  log(`loaded ${LESSONS.length} lessons to process from ${LISTFILE}`)
}
const results = await pipeline(
  LESSONS,
  (L) => agent(
    `${RULES}\n\nTASK: Read the lesson JSON at \`${DIR}${L.file}\` and take its \`body\` field. Detected ` +
    `problems: ${JSON.stringify(L.issues)}. Apply the rules above to produce an improved body. Then WRITE the ` +
    `improved body (the RAW body string only, NOT wrapped in JSON, NO code fence) to \`${OUT}${L.slug.replace(/[^a-zA-Z0-9]+/g, '_')}.body.txt\` ` +
    `using the Write tool. Double-check before writing: every <sentence>/<exercise>/<reading> ref and the ` +
    `<checklist> are intact, and you introduced no new refs. Return {done:true}.`,
    { label: `rewrite:${L.slug.slice(4)}`, phase: 'Rewrite', schema: REWRITE_SCHEMA }
  ).then((r) => ({ L, rewritten: !!(r && r.done) })),
  (prev) => {
    if (!prev.rewritten) return { ...prev, verifyOk: false, issues: ['rewrite-failed'] }
    const L = prev.L
    return agent(
      `You are a strict reviewer of a reformatted pt-BR Japanese lesson. Read the ORIGINAL lesson at ` +
      `\`${DIR}${L.file}\` (its \`body\` field) and the IMPROVED body at ` +
      `\`${OUT}${L.slug.replace(/[^a-zA-Z0-9]+/g, '_')}.body.txt\`. Confirm the improved body: (1) keeps every ` +
      `<sentence>/<exercise>/<reading> ref and the full <checklist> from the original; (2) changed NO fact, ` +
      `reading, kana, or translation; (3) has all Japanese inside <jp> tags and all of it CORRECT (no garbled ` +
      `or invented kana/kanji); (4) removed no important explanation (only reformatted / lightly enriched); ` +
      `(5) introduced no new grammar/vocab/kanji ref that was not in the original; (6) is natural pt-BR with ` +
      `no em dash and only the allowed tags. Return {ok:true} if ALL hold, else {ok:false, issues:[...]}.`,
      { label: `verify:${L.slug.slice(4)}`, phase: 'Verify', schema: VERIFY_SCHEMA }
    ).then((v) => ({ ...prev, verifyOk: !!(v && v.ok), issues: (v && v.issues) || [] }))
  }
)

const ok = results.filter(Boolean).filter((r) => r.rewritten && r.verifyOk)
const bad = results.filter(Boolean).filter((r) => !(r.rewritten && r.verifyOk))
log(`reauthor-lesson-format: ${ok.length}/${results.length} passed verify; ${bad.length} flagged`)
return {
  passed: ok.map((r) => r.L.slug),
  flagged: bad.map((r) => ({ slug: r.L.slug, issues: r.issues })),
}
