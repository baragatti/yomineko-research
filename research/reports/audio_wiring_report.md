# Audio wiring report (W47 / W33): N5 keys exported, generator runnable, prototype plays clips

> 2026-09-28. No GPU work was done in this unit: no model load, no generation, no benchmark. The real
> store (`C:\Users\WiseWolf\yomineko-audio\store\`) is still empty. Design:
> [`design/audio_pipeline.md`](../../design/audio_pipeline.md) (§6 "As built"). Setup:
> [`audio_setup_report.md`](audio_setup_report.md).

## 1. How to run the prototype so it plays clips

```powershell
cd prototype
$env:NODE_OPTIONS = "--max-old-space-size=12288"   # tsc/vite need it for the data imports
npm run build
# optional: YOMINEKO_AUDIO_STORE defaults to C:/Users/WiseWolf/yomineko-audio/store
$env:YOMINEKO_AUDIO_STORE = "C:/Users/WiseWolf/yomineko-audio/store"
npm start                                          # http://localhost:3000
```

`npm run dev` works the same way. The server reads the store on every request, so **buttons appear as
clips land, with no rebuild and no restart**: start the N5 run from the "Yomineko Audio" desktop icon,
reload a lesson page, and every clip written so far has its button. A rebuild is only needed when the
export changes (new keys), not when clips are added.

## 2. Generator: runnable without a benchmark

- **Config pinned in `scripts/audio/plan.py`** (moved from `generate.py`, so the repo's Python computes
  the generator's keys, torch-free): bf16 T3, fp16 flow, fp16 HiFiGAN, MIOpen off, static KV cache,
  batch 8. Evidence: the finished benchmark rows (`yomineko-audio/bench.json`), where every variant passed
  the same 23/30 QA clips as stock fp32 and batch 8 ran at RTF 0.35 (fp32: 1.66; batch 16/30: 0.80).
  bf16 is safe on ROCm 7.2.1 by that measurement. No torch.compile: no Triton for ROCm on Windows.
- **Voices:** the model vendor's own per-language female conditioning prompts, marked `pilot`
  (`ja-pilot-f1@1`; `pt-pilot-f1@1` from the pt-BR Language Pack). Nothing downloaded or cloned in this unit.
- **The store's `config.json` / `voices.json` are now a written record**, rewritten from plan.py every run
  and never read back, so an edited store copy cannot fork the keys.
- **`aliases.json`** (new, written by `Store.save()`): take-1 key → the passing retake's key. The export
  carries the take-1 key; the app follows the alias, so a clip that passed on take 2 or 3 still shows.
- **Checked without the GPU:** in the TTS venv, `generate.py --tier n5 --status` (temp store) plans
  **11,942 N5 keys**, done 0, pending 11,942. `plan.py --tier n5 --out F` writes the same 11,942 keys with
  their specs, byte-identical from the TTS venv (py 3.12) and the repo's 3.13 (both SudachiPy 0.6.11 +
  sudachidict_full 20260428). All 11,125 exported keys are in that run. The desktop shortcut runs
  `app\yomineko_audio_app.py` (identical to `scripts/audio/app.py`), whose Start launches the repo's
  `generate.py --tier n5`.

## 3. Keys in the export

`scripts/audio/build_audio_keys.py` → tracked table `research/derived/audio/audio_keys.json` → read by
the exporters (never edited by hand):

| Where | Field | N5 count | Exporter |
|---|---|---:|---|
| `corpus/sentences/bank.json` | `audio_key`, `audio_lang` | 704 | export_corpus.py |
| `corpus/vocab/n5.json` | `audio_key`, `audio_lang` | 709 | export_corpus.py |
| `corpus/kana/{hiragana,katakana}.json` | `audio_key`, `audio_lang` | 208 (っ ッ ー are silent) | build_kana.py |
| `corpus/exam_banks/n5_listening_*.json` | `script[].audio_key`, `audio_lang` | 227 turns | build_listening_bank.py |
| `course/{pre-n5,n5}/…/lesson-*.json` | `narration[]` = `{span, audio_lang, audio_key}` | 17,481 units / 125 lessons | export_course.py |

- A sentence is keyed when its unit is in the N5 run (it takes its lowest consumer's tier); everything
  else goes by the record's own tier, so no N4 lesson carries a partial list.
- `span` is the element path of the body block the unit voices ("3", "5.1"; "" = body root, i.e. a
  top-level `<sentence>`/`<reading>`, which has its own button). plan.py and the renderer number elements
  the same way; the test below found the heading narration on the right block.
- Contracts regenerated: `audio_key` (`^[a-z2-7]{26}$`), `audio_lang` (BCP-47 shape) and `span` are
  declared by name in `build_schemas.py`, never measured; `lesson.narration[]` items require all three.
- **Workflow when voiced text changes:** `python scripts/audio/build_audio_keys.py`, then the exporters,
  contracts, `npm run sync-data`. The gate fails until that is done.

### Gates (both in `validate_all.py`)

- `test_audio_key.py`: same request → same key (dict order irrelevant); each of the 8 top-level fields
  and each of the 7 params changes the key; a retake changes the key but not `base_of`; `^[a-z2-7]{26}$`
  and URL-quote-stable; a pinned vector (cross-checked by an independent Node implementation); no
  collision over the whole plan (37,458 units, 37,240 distinct specs → 37,240 keys); the collision abort
  fires when forced.
- `validate_audio_keys.py`: A1 table == plan on the current export; A2 every sentence/vocab/kana/listening
  key equals the plan's, none missing, none extra, lang `ja`; A3 every lesson `narration[]` equals the
  plan's list; A4 key shape; A5 collisions. **Plant-proved** (`--selftest`, copied tree including the
  validator and plan.py): 13/13 caught (flipped, removed, extra key; wrong lang; upper-cased key; listening
  text drift; narration order, span, dropped; lesson prose edited; token reading drift; stale table;
  changed config param), control green.

## 4. Prototype

- `GET /audio/:key` (`app/routes/audio.ts`, `app/lib/audio.server.ts`): key checked against
  `^[a-z2-7]{26}$` before any path is built (malformed → 400, so no traversal); looks for
  `<store>/opus/<k[:2]>/<k>.opus` (the generator's layout), then `<store>/<k>.opus`, then the FLAC master
  in both layouts, then the same via `aliases.json`; `Content-Type: audio/ogg; codecs=opus` (or
  `audio/flac`), `Cache-Control: public, max-age=31536000, immutable`, `ETag` = key; absent → 404
  `no-store`. Store path from `YOMINEKO_AUDIO_STORE`, default `C:/Users/WiseWolf/yomineko-audio/store`.
- `<PlayButton audioKey lang>` (`app/ui/PlayButton.tsx`, typed, no `any`) and `playButtonHtml()` for the
  server-rendered lesson body emit the same button; one delegated listener (`<AudioClicks/>` in root)
  plays the keys in order, a second click stops.
- Loaders call `playable(key)` server-side and pass a key only when its file exists. Buttons: every
  lesson `<sentence>` (Japanese line) and its "Palavra por palavra" header; bank sentences on the
  kanji/vocab/grammar detail pages (`SentenceCards`, same two places); the vocab detail header; the
  selected glyph on `/kana`; and each lesson block whose narration is complete (see §5).
- `sync-data.mjs` carries `audio_key` on slim sentences and joins each kana chart member to its glyph's
  key; `validate_prototype_sync.py` mirrors both. Typecheck, build, no-client-leak and sync are green.

### Verified with one test clip (then removed)

A temp store (`…/scratchpad/TEST-audio-store-NOT-PRODUCT`, with a README saying so) held one benchmark wav
(`work/out/eng_bf16_0.wav`) converted to Ogg Opus with ffmpeg and filed under the key of
`sent:tatoeba-5332` (いくらですか？, `b3dlptszdcvhde2htgyexvazfz`). With `YOMINEKO_AUDIO_STORE` pointing at it
(production build on :3917):

- `/licao/les:n5-desu-wa-01`: exactly two buttons, both that sentence's (its line and its word-by-word
  header); the other sentence on the page (おいくつですか？) has none; no narration buttons. Screenshot
  (headless Chrome, since the preview pane was hidden) confirmed the speaker icon beside いくらですか？ only.
- Clicking it in the browser pane: `GET /audio/b3dlptszdcvhde2htgyexvazfz → 200`.
- curl: that key 200 with the headers above (10,379 bytes); an unknown valid key 404 `no-store`; a
  traversal attempt and an upper-case key 400.
- Adding the same file under a vocab key, a kana key and the three units of one lesson heading made the
  vocab header, the あ stage and that heading (span "3", "A partícula は: …") show buttons, each holding
  the expected keys.

The temp store, the status-test store and the browser profile were deleted; the real store was never
written.

## 5. For the owner

1. **Start the N5 run** from the desktop icon when the GPU is free (11,942 clips: about 3.8k Japanese
   units and 8.2k pt-BR sentences). Buttons appear as clips land.
2. **Narration buttons are all-or-nothing per block**: a paragraph gets its button when every unit in it
   (pt-BR text and inline Japanese) has passed QA. A needs_human unit hides its paragraph until a retake
   passes (`generate.py --retry-failed`).
3. **Inline particle chips** (`<jp>は</jp>`, へ, を in the prose, 118 of 3,832 N5 narration blocks) are
   voiced as their kana. For は and へ the TTS says the letter ("ha", "he") while the QA expects the
   particle ("wa", "e"), so they will likely end needs_human and hide those 118 paragraph buttons. Fix
   when it bites: voice a lone は/へ chip as わ/え (a plan.py rule, which re-keys only those units).
4. Voices are pilot (V1): a consented voice is a new voice id, so new keys; re-run
   `build_audio_keys.py` + exporters, and the old clips are pruned by `generate.py --prune`.

## 6. Gate and replay

`validate_all.py` is green. Three existing gates needed a W47 touch: `validate_repairs_applied.py` (the
listening re-author rows compare the authored turn, ignoring the new `audio_key`/`audio_lang`),
`validate_prototype_sync.py` (mirrors the slim-sentence key and the kana join), and the review views
(re-rendered). The date-only INDEX.md / `generated` stamps the exporters rewrote were restored, so the
held rebuild baseline stays as recorded.

**Found, not caused here:** the full replay (`validate_index_rebuildable.py`, not in the suite) stops at
step 157, `apply_particle_usage.py`: 13,167 guard failures (the W46 sha/position guards against the
replayed index), nothing written. W47 touches no particle or sentence writer (only `build_kana.py`'s JSON
and four exporters), and W46 recorded that its full replay had not been run. The next checkpoint's
replay has to fix that step.
