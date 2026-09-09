# `layerb_out/` — where an authoring pass drops its results

`scripts/assemble_layerb.py` reads every `*.json` here (files whose name starts with `_` are skipped)
and merges them into the derived batches. One file per authoring batch; the file names mirror the work
lists (`rulings-03.json`, `particles-07.json`, `paragraphs-12.json`, `tokens-01.json`), and the `kind`
field is what actually decides how a file is read.

```json
{
  "kind": "rulings" | "tokens" | "particles" | "paragraphs",
  "rows": [ … ]
}
```

Row shapes, one per kind. Identity fields are **not optional** — they are how a row finds its slot:

| kind | identity | authored field | verifier's replacement |
|---|---|---|---|
| `rulings` | `lemma` + `pos` | `ruling` | `verifier_ruling` |
| `tokens` | `key` + `position` | `gloss_pt` | `verifier_gloss_pt` |
| `particles` | `key` + `position` | `explanation_pt` | `verifier_explanation_pt` |
| `paragraphs` | `key` | `structure_explanation_pt` | `verifier_structure_explanation_pt` |

`key` is `str(tatoeba_id)` for a real sentence and `gen-<sha1(jp)[:12]>` for a generated one.
`position` is the C-token position from the Dissector. Both come straight from the work list; copy
them, do not recompute them.

## Verdicts

Every row carries a `verdict` written by an independent verifier:

- `ok` — the authored text is merged as written.
- `fix` — the verifier's replacement is merged instead. The matching `verifier_<field>` must be
  present and non-empty, or the row is dropped and counted as `fix-without-replacement`.
- `reject` — the row is dropped; the slot stays exactly as the derivation left it.

**A missing, null or unrecognised verdict is not an acceptance.** The row is excluded and counted under
`unverified_excluded` in `research/derived/mined_layerb_n3/_summary.json`. Nothing reaches the corpus on
the strength of having been written down.

## What a ruling does

One `rulings` row is one decision about a `(lemma, pos)` pair, and the assembler applies it to *every*
token in the 4,223 sentences whose gloss came out `ambiguous-verify` with that key — 12,405 tokens over
1,563 pairs. Write the gloss the lemma takes in that part of speech, not a gloss tailored to one
sentence.
