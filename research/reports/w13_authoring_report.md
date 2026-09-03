# W13 — N3 exemplification, authoring phase (artifact only)

Workflow `wf_9fb826eb-0d1` (2026-09-03): 1 target/miner agent, 33 Opus authors, 33 independent Opus
verifiers, 5.1 M tokens. The workflow's own Assemble stage died on the session limit after every
verifier had finished, so the assembly was re-done as a deterministic script (session scratchpad
`assemble_w13.py`) that reads the workflow journal and the agents' transcripts. Verdicts were paired to
rows **by row content** (each verifier's prompt embeds the exact rows it judged), never by batch index —
the failure mode that made W27's table unusable.

Nothing here writes the DB. Outputs under `research/derived/n3_mined/`:

| file | content |
|---|---|
| `accepted.json` | 4,197 real Tatoeba sentences in the row shape `ingest_mined_stages.py` reads (`rows[]` with `tatoeba_id`, `jp`, `en`, `pt`, `pt_literal`, `register`, `target`/`targets`, `lesson`, `reject`), plus a `counts` summary |
| `generated.json` | 26 AI-generated sentences for targets with no real candidate (`ai_generated: true`, `needs_review: true`, trailing 。 stripped) — a separate ingest path, never `ingest_mined_stages.py` (it requires a raw Tatoeba row) |
| `residue.json` | 170 rows the verifiers rejected (with the problem), 5 rows no verifier reached, 101 uncovered targets, 26 targets served only by a generated sentence |
| `summary.json` | the counts below |

## Counts

| | |
|---|---|
| targets (N3 vocab under 3 sentences + grammar under 5) | 1,638 |
| authored rows | 4,431 |
| verified ok / corrected by the verifier (pt only) / rejected | 4,118 / 138 / 170 |
| unverified (excluded, not passed through) | 5 |
| real sentences accepted after Layer-A re-check | 4,197 (0 altered jp, 0 missing English pair, 0 already banked) |
| generated sentences accepted | 26 |
| targets covered by ≥1 real sentence / at the floor | 1,511 / 1,387 |
| targets covered only by a generated sentence | 26 (15 vocab, 11 grammar) |
| targets still uncovered | 101 (97 vocab, 4 grammar) |
| lessons whose known set bounded the selection | 101 |
| sentence length | 6–38 characters, median 3 sentences per covered target |

Every accepted real row was re-checked against `raw_tatoeba_sentence` (jp byte-exact) and
`raw_tatoeba_translation` (en is a directly linked English pair). All 4,197 passed with no
correction — the authors did not tidy Layer-A Japanese. 33 rows were merged because one sentence
serves two targets (`targets[]` keeps both).

## Fable sample (30 accepted rows, seed 13)

Read against the Japanese: translation faithful and natural pt-BR in all 30; the literal scaffold
carries particle roles as the style guide asks; no pt-PT, no em dash (0 in the whole table). One
loose spot, not an error: 加わりたい → "Quero entrar também" adds *também*; acceptable for 加わる (join
in). Verdict: pass, commit.

## What the verifiers rejected (170)

Almost all fail criterion (a): the target is not a SudachiPy token of the sentence — 男の人 split into
three tokens, 不 absorbed into 不便/不安, 空 read as a different lemma. Correct rejections: a sentence
that contains the string but not the word does not teach the word.

## Findings that need a decision or a follow-up

1. **Register values.** The authors used seven values — neutral 834, polite 1,005, casual 2,109,
   formal 137, plain 91, colloquial 19, honorific 2 — against a four-value vocabulary (neutral / polite /
   casual / formal) on grammar records. Also "casual" was applied to plain-form written narrative
   (彼は実験を続けた, 我々は博物館へ行った), which is *neutral*, not casual. The sentence-level `register`
   field does not exist yet (A8 / W31): normalize at apply time to whatever W31 fixes, and treat
   plain-form narrative as neutral.
2. **Layer-B content is missing, and the ingest requires it.** `ingest_mined_stages.py` reads
   `research/derived/mined_layerb/batch-*.json` for per-token glosses, particle explanations and the
   structure paragraph; every bank sentence is `dissection_tier: full`, and ingesting without that
   content produced 2,756 validator errors the first time it was tried. W13 authored `pt` and
   `pt_literal` only. **The apply therefore needs a Layer-B dissection campaign over 4,223 sentences
   first** — the same authoring + two-reviewer shape that produced the 324 speak-stage sentences.
3. **Tags.** The ingest stamps `stage:<x>`; these rows are not speak-path stages. The apply must pass
   a unit tag (`n3-exemplification`) instead — a small flag on the ingest script.
4. **101 uncovered targets** (97 vocab, 4 grammar) had no real candidate in 229,173 Tatoeba rows
   and no generation in this run (the authors generated for 26 of the 99 zero-candidate targets).
   Spec §1.2 last resort: generate inside the known set, `ai_generated` + `needs_review`.
5. **Grammar coverage** is the weaker half: 11 grammar targets are served only by a generated
   sentence and 4 by nothing; the sentence→grammar link is made by the relinker (W12), not by the
   ingest, so the W05 grammar floor moves only after W12 runs on the new rows.
