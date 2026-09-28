# Audio setup report (D3 / W35): local Chatterbox V3 on the RX 9070 XT

> Status: **in progress** (2026-09-27). This file is updated as each step lands, so a session limit
> leaves it current. Design: [`design/audio_pipeline.md`](../../design/audio_pipeline.md). Research:
> [`audio_pipeline_research.md`](audio_pipeline_research.md).

## 1. Stack (installed, outside the repo)

| Part | Value |
|---|---|
| Env root | `C:\Users\WiseWolf\yomineko-audio\` (venv `.venv`, HF cache `hf\`, voices `voices\`, store `store\`, logs `logs\`) |
| GPU / driver | AMD Radeon RX 9070 XT (gfx1201, 15.9 GiB visible) · Adrenalin **26.8.1** (driver 32.0.31041.1004) ≥ 26.2.2 required: OK. The iGPU is not enumerated by HIP (1 device), so no `HIP_VISIBLE_DEVICES` pin was needed. |
| Python | CPython 3.12.9 (uv-managed), venv created with `uv venv --python 3.12` |
| ROCm / torch | AMD release wheels from `repo.radeon.com/rocm/windows/rocm-rel-7.2.1/`: rocm_sdk_core/devel/libraries_custom 7.2.1, torch **2.9.1+rocm7.2.1** (HIP 7.2.53211), torchaudio 2.9.1, torchvision 0.24.1. The 7.14 preview was not used. |
| Chatterbox | `chatterbox-tts` 0.1.7 from git `resemble-ai/chatterbox@5de7a54a` (master, has `t3_model="v3"`), installed `--no-deps`; deps pinned per its pyproject (transformers 5.2.0, diffusers 0.29.0, librosa 0.11.0, s3tokenizer 0.3.0, conformer 0.3.2, safetensors 0.5.3, pykakasi 2.3.0, numpy 1.26.4, resemble-perth 1.1.0 @ff1c8ac5, pyloudnorm, omegaconf, spacy-pkuseg). torch stayed the ROCm build (uv constraint file). |
| QA | SudachiPy 0.6.11 + sudachidict_full 20260428 (SplitMode C; the repo's pins, checked 2026-09-28: the TTS venv, the system 3.13 and `.venv` agree, and plan.py emits byte-identical N5 keys in all of them); Whisper via transformers on the same torch |
| Weights (HF, pinned) | `ResembleAI/chatterbox@5bb1f6ee`: `t3_mtl23ls_v3.safetensors` (sha256 `5abca8321ede…`), `s3gen.pt` (`9b9ff07e60b2…`), `s3gen_v3.pt` (`f7abce4b196d…`), `ve.pt`, `conds.pt`, tokenizer. `ResembleAI/Chatterbox-Multilingual-pt-br@b3952f18`: `t3_pt_br.safetensors` (`074aaf65255e…`). `openai/whisper-large-v3@06f233fe`, `openai/whisper-large-v3-turbo@41f01f3f`. |

### GPU smoke test (`smoke_gpu.py`, log `logs/smoke_gpu.log`)

- `torch.cuda.is_available()` True, 1 device: `AMD Radeon RX 9070 XT`, arch `gfx1201`.
- `ones(1024).sum() == 1024` (no silent zeros); 4096² matmul vs CPU: max abs error 0.001.
- 8192³ matmul: **fp32 1.8 TFLOPS** (slow fp32 GEMM path), **fp16 77.1 / bf16 76.9 TFLOPS**. Half precision
  is where this card is fast.
- SDPA works (flash / mem-efficient / math backends all enabled).

## 2. Benchmark

Stopped mid-run at the owner's request (2026-09-27); the finished rows are in
`yomineko-audio/bench.json` (30 fixed clips, 15 ja + 15 pt). Every variant passed the same 23/30 QA clips
as the stock fp32 path, so precision is chosen on speed:

| Variant (cumulative) | RTF (wall s / audio s) | VRAM |
|---|---|---|
| stock fp32, one clip at a time | 1.66 | 13.0 GiB |
| + bf16 T3 + fp16 flow decoder | 1.20 | 10.8 GiB |
| + MIOpen off (native conv) | 0.71 | 10.8 GiB |
| + HiFiGAN fp16 | 0.61 | 10.8 GiB |
| + static KV cache | 0.61 | 10.8 GiB |
| **+ batch 8** | **0.35** | 10.8 GiB |
| + batch 16 / 30 | 0.80 / 0.81 | 13.6 GiB |
| variant: fp16 T3 / fp32 T3 | 0.85 / 1.90 | 12.9 / 17.9 GiB |

**Pinned (2026-09-28, `scripts/audio/plan.py` CONFIG_DEFAULTS):** bf16 T3, fp16 flow, fp16 HiFiGAN, MIOpen
off, static KV, batch 8. bf16 is safe on this stack by measurement (same QA passes as fp32; fp32 GEMM runs
at 1.8 TFLOPS on gfx1201, bf16 at 77). No torch.compile: there is no Triton for ROCm on Windows
(TritonMissing), so it cannot be used or benchmarked here. The precision is part of every key.

## 3. Voices (pilot)

The model vendor's own per-language conditioning prompts, female, marked `pilot` in `voices.json`:
`ja-pilot-f1@1` (Chatterbox Multilingual demo ja prompt) for every ja class, `pt-pilot-f1@1` (the pt-BR
Language Pack's own demo prompt) for the pt-BR narrator. No third-party recording, no clone. Both carry
"PILOT ONLY, replace before shipping"; a consented voice is a new voice id and so a new set of keys.

## 4. Generator (`scripts/audio/`, runs in the TTS venv; reads the export, never writes the repo)

| File | Role |
|---|---|
| `plan.py` | Holds the pinned config, the voices and the key functions (torch-free, so the repo computes the generator's keys; `--tier n5 --out F` writes the 11,942 N5 keys with their specs). Reads the export read-only and builds every voice unit (design §2): bank sentences from the **verified `split_mode: "C"` tokens** (kanji/digit/Latin surface → its `reading` in hiragana, every other token keeps its surface, sub-tokens ignored), vocab + kanji example words from `vocab.kana`, 208 kana glyphs (っ ッ ー alone are skipped: no sound), listening turns / questions / spoken options (verified tokens when the text is a bank sentence, else SudachiPy SplitMode C + sudachidict_full 20260428, the repo's pinned setup), reading-passage sentences from their tokens, pt-BR lesson narration (`<text>`/`<term>`/`<emphasis>` runs split at sentence ends, interleaved with the inline `<jp>`/`<ruby>`/`<vocab>`/`<grammar>` chips voiced as Japanese). Normalisation `ja-1` / `pt-1` exactly as §3.1; units starting with 〜 are not voiced; a unit that still holds a kanji or digit is a plan error (40, all N3 radical glyphs such as 扌 in narration). Tiers follow the consumer: **n5** (pre-N5 + N5), n4, speak, n3. |
| `tts_engine.py` | Batched Chatterbox inference (see §2 for why). Numerically the same model as the library: first-step logits of the batched, left-padded path match the stock path to **1.6e-5** in fp32 (`selfcheck()`). |
| `qa.py` | Post-processing `p1` (edge silence trimmed to 150 ms, −16 LUFS integrated, true peak ≤ −1 dBTP by 4× oversampling, mono 24 kHz) and the §7 checks: Whisper transcript → SudachiPy phonetic hiragana → canonical folding (katakana→hiragana, ー→vowel, おう→おお, えい→ええ, を→お, particle は/へ→わ/え) → `mora_cer`; pt: lower-cased, punctuation-free WER. Signal checks: duration window, internal silence > 1.2 s, clipping, loudness. |
| `generate.py` | Spec → key → files → manifest, incremental, pruning, graceful stop, pilot. |
| `bench.py` | The benchmark of §2. |
| `app.py` | The control app (installed copy: `C:\Users\WiseWolf\yomineko-audio\app\yomineko_audio_app.py`). |

Key and files, exactly as design §3.3: spec `{"v":1,"kind":"tts","lang","norm","text","voice","model","params":{…,"take"},"post":"p1"}`
→ canonical JSON (sorted keys, no spaces, UTF-8) → `base32(sha256)` lower-case, 26 chars. Seed = first 8 bytes
of the same hash. Two deliberate additions: `model` carries the T3 **and** the S3Gen checkpoint hash
(`chatterbox-mtl-v3@5abca8321ede.9b9ff07e60b2`, `chatterbox-mtl-v3-pt-br@074aaf65255e.f7abce4b196d`) because V3
ships two decoders; `params` carries `precision` (e.g. `t3bf16.flowfp16.hiftfp16`) because precision changes the
waveform. Collisions are checked, not assumed: a plan key with two different canonical specs, or a manifest
key whose stored spec hashes to something else, aborts the run.

Store (`YOMINEKO_AUDIO_STORE`, default `C:\Users\WiseWolf\yomineko-audio\store\`): `masters/<k[:2]>/<k>.flac`
(24-bit master), `opus/<k[:2]>/<k>.opus` (Ogg Opus 32 kbps mono, ffmpeg/libopus), `manifest.json` (key → spec,
display, kind, reading_source, duration, bytes, sha256 of both files, QA result with the ASR text, consumers,
created), `results.jsonl` (append-only, fsync'd per clip, replayed at start so a hard kill loses nothing),
`failures.json` (needs_human units with every take's ASR text), `review/<base>.flac` (the last take of each
needs_human unit, for the owner's ear), `config.json` + `voices.json` (a record of the pins, rewritten from
plan.py every run and never read back, so an edited copy cannot fork the keys), `aliases.json` (take-1 key →
the passing retake's key, so the web app finds a retaken clip under the key the export carries), `status.json`
(for the app).
Files are written to `*.tmp` and renamed. Consumers are recomputed from the export on every run; entries
nobody uses leave the manifest, and only `--prune` deletes files. Retakes: a failed clip gets `take+1` (a new
key and seed), at most 3 takes; then the unit is `needs_human`, exported as no audio, never shipped as is.

## 5. Pilot

(pending)

## 6. Operating it

- **Desktop icon "Yomineko Audio"** (`C:\Users\WiseWolf\Desktop\Yomineko Audio.lnk` → venv `pythonw.exe`
  `C:\Users\WiseWolf\yomineko-audio\app\yomineko_audio_app.py`, icon `app\yomineko_audio.ico`). The window has a
  tier selector (default **n5**), **Start**, **Stop**, a progress bar, done / total / failed / pending, rate and
  ETA (from the measured rate), and the last log lines. It shows a run started elsewhere too (it reads
  `store\status.json` and checks the generator's pid).
- **Start** launches `generate.py --tier <tier>` in the venv as its own process (no console window; output in
  `logs\generate_stdout.log`, log in `logs\generate.log`). Closing the window does **not** stop generation.
- **Stop** writes `store\STOP`; the generator finishes, checks and writes the batch in flight (seconds to about
  a minute for long pt batches) and exits. Ctrl+C / Ctrl+Break do the same from a console.
- **Resume** = Start again. Keys whose manifest entry passed and whose two files are present are skipped;
  nothing is generated twice. A hard kill (power loss) loses at most the batch in flight; `results.jsonl` is
  replayed on start.
- Command line (same venv): `C:\Users\WiseWolf\yomineko-audio\.venv\Scripts\python.exe <repo>\scripts\audio\generate.py`
  `--tier n5` · `--pilot 200` · `--status` · `--prune` (deletes store files whose key left the manifest; never
  runs implicitly) · `--retry-failed` (gives needs_human units three fresh takes).
- The GPU is shared: while generation runs, games or other GPU work will be slow and vice versa. Stop first.

## 7. For the owner to decide

(pending)
