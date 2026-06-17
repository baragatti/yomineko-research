# Course Volume & Depth Comparison — ours vs. the local reference (P7, de-identified)

> **Clean-room note.** This is the P7 concept/volume comparison mandated by the spec (§1.4 / §1.8). It records
> ONLY aggregate metrics and method-level observations computed by script over the local material — **no text,
> examples, titles, names, or phrasing were copied or read into the corpus.** The local material is named
> nowhere. Nothing here is a generation source; it is an audit of whether *our* course is thin anywhere.

## Method
A metrics-only script stripped tags from every lesson body on both sides and counted Latin-script chars (proxy
for pt-BR prose), CJK chars (proxy for embedded Japanese), examples, notes, exercises, and media assets. Only the
numbers below left the sandbox.

## Headline numbers

| Metric | Local reference | Ours | Verdict |
|---|---|---|---|
| Lessons (with body) | 41 (4 modules) | **213** (35 topics, 3 modules) | ours far more granular |
| Total pt-BR prose (chars) | ~206k | **~554k (2.7×)** | ours much larger overall |
| pt-BR prose / lesson — **median** | 1,580 | **2,072** | ours richer per typical lesson |
| pt-BR prose / lesson — **mean** | 5,029 | 2,602 | local mean inflated by deep-dives |
| pt-BR prose / lesson — **p75 / p90 / max** | **11,688 / 14,289 / 21,730** | 2,323 / 2,537 / 2,914 | **local has ~12 very deep lessons; we have none** |
| Embedded Japanese (CJK chars) | ~129k (~3,140/lesson) | ~53k (~250/lesson) | **local embeds far more Japanese per lesson** |
| Featured real sentences | n/a | 441 of 4,959 bank = **8.9%** | **we under-use our own sentence bank** |
| Notes / exercises | — | 807 notes / 1,053 exercises | strong (ours) |
| Audio assets | **478** | 0 | feature gap (out of data-only scope) |
| Image assets | 0 | 0 | par |

## Reading of the data
- **We are NOT lacking in total text** — 2.7× the local prose volume, and our *typical* lesson (median 2,072)
  is denser than the local *typical* lesson (median 1,580). Our 213 micro-lessons vs their 41 is a deliberate
  SRS-unlock design choice.
- The local mean (5,029) ≫ its median (1,580): the distribution is **bimodal** — many short lessons + ~12 (29%)
  **very deep "reference" chapters** (4k–21k chars) that give one comprehensive single-page treatment of a big
  topic. **Our distribution is flat (everything ~2k, max 2,914): we have no deep-dive reference treatment.**
- **Biggest concrete gap = embedded Japanese density.** Local lessons carry ~3,140 CJK chars each (long examples,
  likely dialogues + furigana); ours ~250. We hold a **4,959-sentence dissected bank but feature only 8.9%.**

## Improvement backlog (added to STATE plan — "P8 enrichment")
1. **Feature more real example sentences per lesson.** Raise from ~2 to ~4–6, prioritising conversational
   register, pulled from our existing 4,959-sentence dissected bank (real, human-written, already licensed). This
   directly closes the embedded-Japanese-density gap **using our own data — no copying.** Biggest bang for buck.
2. **Add per-topic "deep-dive / referência" depth for ~12 high-leverage topics** (kana系, は vs が, particles,
   て-form, 〜たい/potential, condicionais, keigo, transitivity). Either a longer flagship lesson per topic or a
   `referência` summary card consolidating the topic — to match the reference's deep chapters in our own words.
3. **Enrich the 12 thin lessons (<1,200 chars).** Identify and expand (cross-reference the quality-review flags).
4. **Add short dialogues (2–4 turns)** per topic, assembled from real sentence pairs in the bank, for
   conversational exposure (the reference leans conversational; ours is single-sentence).
5. **Audio (product roadmap, not this data run):** we already store sentences + readings → TTS pass can generate
   audio over the dissected bank, reaching parity with the reference's audio-per-line model.

_None of the above requires the local material; items 1, 3, 4 use only our own corpus, and items 2, 5 are
method-level ideas re-expressed in our own design._
