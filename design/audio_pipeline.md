# Audio pipeline: content-addressed TTS audio (v1 design, 2026-09-27)

> Owner decision D3 (2026-09-27): voice all Japanese, plus the pt-BR lesson text, **locally** with
> Chatterbox Multilingual V3 on the owner's RX 9070 XT. Audio is **hashed**: one file per unique
> utterance, found by its hash, generated incrementally, pruned when unused, never duplicated, and
> easy to host behind the future API. Research and sources:
> [`research/reports/audio_pipeline_research.md`](../research/reports/audio_pipeline_research.md). Counts:
> [`research/derived/pending/audio_inventory.json`](../research/derived/pending/audio_inventory.json).
> This document closes **W33** (audio schema) and specifies **W35** (assets). W36 (voice mode / ASR
> scoring) is out of scope.

## 1. Principles

1. **An utterance is identified by what is synthesised, not by who uses it.** The key hashes the
   exact synthesis request (§3). Two records that need the same audio get the same key and share one
   file, so duplicates cannot arise by construction.
2. **Selection over generation (spec 1.2) applies to audio too.** If a licence-cleared human
   recording exists (a Tatoeba clip, or an owner recording), it wins over TTS for that utterance.
3. **We send the model verified readings, not kanji.** Chatterbox converts kanji with pykakasi,
   which has no context. Sending our checked token readings in kana bypasses it (research §1.1).
4. **Audio is an asset and never corpus data.** Files stay out of git. The manifest, which maps key
   to spec, QA result and consumers, is tracked JSON, just as the corpus is.
5. **Coverage is a build metric, not a gate** (R63). A record with no passing audio exports
   `audio_ref: null`. Nothing blocks on audio, and the gate counts the gaps.

## 2. Voice units (what gets a key)

| Kind | Unit | Synthesis text source | Voice class |
|---|---|---|---|
| `sentence` | one bank sentence | verified `tokens[]` (§3.2) | sentence pool (§5) |
| `word` | one vocab reading | `vocab.kana` (dictionary reading, Layer A) | `ja-word` |
| (kanji example word) | resolves to the vocab record | same key as the vocab record (all 4,741 resolve) | — |
| `kana` | one glyph | the glyph | `ja-word` (or a human recording, §9) |
| `listen` | one listening turn / spoken question / spoken option | text + SudachiPy readings | speaker map M1 M2 F1 F2 N (§5) |
| `passage` | one reading-passage sentence | passage `tokens[]` (`r`) | sentence pool |
| `narration` | one pt-BR sentence of a lesson-body block | `<text>` runs, split at sentence ends | `pt-narrator` |
| (inline `<jp>` in narration) | a `word`/`sentence`-class unit | its `reading=` attribute, else SudachiPy | `ja-word` |

Printed options (listening task/point) and all non-listening exam families are **not** voiced.
Stitched listening items (the full item played in exam order, design/listening.md "Playback order")
are **derived renditions** with their own key (§3.4). Phase 1 does not need them, because the app
plays the segments in sequence.

## 3. The key

### 3.1 Normalisation (`norm` version `ja-1` / `pt-1`)

These steps are applied, in order, to the **synthesis text**. The text that is hashed is the text
that is spoken.

| Step | `ja-1` | `pt-1` |
|---|---|---|
| 1 | Unicode **NFKC** (full-width digits/Latin → ASCII, half-width kana → full-width, `？！` → `?!`) | NFKC |
| 2 | remove **all** whitespace (spaces carry no sound in Japanese) | collapse whitespace runs to one ASCII space; trim |
| 3 | drop quotes and brackets `「」『』（）()[]""''` and `・` | drop `""''«»()[]` |
| 4 | drop **one terminal** `。` `.` (a trailing full stop changes nothing audible; this merges `わかりました。`/`わかりました`) | drop one terminal `.` |
| 5 | keep `?` and `!` (they change intonation), keep `、` and internal `,` (pauses) | keep `? ! , ; :` |
| 6 | a unit that starts with `〜`/`~` (a pattern fragment such as 〜てください) is **not voiced** | — |
| 7 | reject a unit that is empty or, after §3.2, still contains a kanji or a digit (a build error, never silently spoken) | reject empty |

### 3.2 Reading resolution (Japanese only; runs before §3.1)

- **Tokenised records** (bank sentences, passages): join the tokens in order. A token whose surface
  contains a **kanji (incl. 々) or a digit or Latin letter** is replaced by its `reading` converted
  to hiragana. Every other token keeps its **surface**, which means particle は stays は and
  katakana stays katakana, exactly the shape Chatterbox's own normaliser produces. Measured on HEAD:
  0 unresolvable kanji tokens across 10,271 sentences, and 384/384 digit tokens carry counter
  readings (`６日` → むいか).
- **Untokenised text** (listening scripts, inline `<jp>` without `reading=`): tokenise with the
  dissection's SudachiPy setup (SplitMode C, sudachidict-full) and apply the same rule. These units
  carry `reading_source: "sudachi"` in the manifest and get **priority ASR review** (§7), since
  their readings were never verified. 120 listening turns contain digits.
- **Vocab / kana:** the text is already kana. Nothing to resolve.

### 3.3 Spec, hash and filename

```json
{"v": 1, "kind": "tts", "lang": "ja", "norm": "ja-1",
 "text": "きょうはいちがついつかだ",
 "voice": "ja-f1@1",
 "model": "chatterbox-mtl-v3@<12-hex of the T3 checkpoint sha256>",
 "params": {"exaggeration": 0.5, "cfg_weight": 0.5, "temperature": 0.8, "take": 1},
 "post": "p1"}
```

- **Canonical bytes** = `json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.
- **Key** = `base32(sha256(canonical))` in lower case, `=` padding stripped, **first 26 characters**
  (130 bits). Example shape: `k3v7q2xw5mfr4ad6hn2ytc7peb`.
  - The alphabet is `a-z2-7`, which is URL-, path- and shell-safe. Because it is lower-case only, it
    is also safe on case-insensitive file systems (Windows NTFS, macOS). base64 would collide there.
  - At a million utterances the chance of a truncation collision is about 10⁻²⁷. It is still
    **checked**, never assumed (§4.3).
- **Seed** = the first 8 bytes of the same sha256, read as an unsigned integer. It is derived and
  never stored separately, so the same spec reproduces the same sampling.
- **`take`** starts at 1. The only way to get a different rendition of the same text is a QA
  rejection (§7) that bumps it. That produces a new key, and the rejected key is dropped.
- **`post`** names the post-processing recipe: `p1` = trim leading/trailing silence to 150 ms,
  loudness normalise to **−16 LUFS** integrated, true peak ≤ −1 dBTP, mono 24 kHz. If the recipe
  changes, the name changes, and so every key changes deliberately.
- **Human or Tatoeba audio** uses the same machinery with a different spec, for example
  `{"v":1,"kind":"tatoeba","audio_id":"<id>","post":"p1"}` or
  `{"v":1,"kind":"human","lang":"ja","text":"…","voice":"ja-f1@1","take":1,"post":"p1"}`.
  They are content-addressed in the same key space.
- **Files:** `<key>.flac` (master) and `<key>.opus` (delivery: Ogg Opus, 32 kbps mono). Further
  renditions (for example `<key>.m4a` for older Apple clients) are added at API time under the same
  key. **The key is the utterance and the extension is only the rendition.**

### 3.4 Derived renditions

A stitched listening item has the spec
`{"v":1,"kind":"stitch","parts":["<key>",…],"pauses_ms":[…],"post":"p1"}` and gets a key the same way.
If any part is re-taken, the stitch key changes automatically.

## 4. Manifest, store, build

### 4.1 Tracked files (`corpus/audio/`, new; exported like the rest of the corpus)

- `config.json`: the pins. The model id and HF revision for `ja` (V3 base) and `pt-BR` (Language
  Pack); the checkpoint sha256; the default `params`; the `norm` and `post` versions; the voice pool
  per class.
- `voices.json`: `voice id → {lang, role, gender, reference_clip_sha256, consent_ref, licence, created}`.
  The reference clip itself stays **out of git** because it is biometric personal data. A new clip
  means a new voice version (`ja-f1@2`), and so new keys.
- `manifest.json`: one entry per key, sorted by key, indent 1 (diff-friendly):

```json
"k3v7q2xw5mfr4ad6hn2ytc7peb": {
  "spec": {"…": "exactly the hashed spec"},
  "display": "今日は１月５日だ",
  "reading_source": "tokens",
  "duration_ms": 1840, "bytes_opus": 7412,
  "sha256_master": "…", "sha256_opus": "…",
  "qa": {"status": "pass", "asr_model": "whisper-large-v3", "mora_cer": 0.0, "checked": "2026-10-02"},
  "consumers": ["sent:gen-099cd0de9ac8"],
  "created": "2026-10-02"}
```

`consumers[]` is **recomputed on every build** from the export and never edited by hand. It lists
record ids, with a JSON-path suffix for sub-parts (`lt:n5:001#script[2]`, `lr:n5:…#distractors[1]`,
`les:n5-te-form-01#narration[14]`).

### 4.2 Store (not in git)

`$YOMINEKO_AUDIO_STORE` defaults to the sibling folder `../yomineko-audio/`:
`masters/<key[:2]>/<key>.flac` and `opus/<key[:2]>/<key>.opus`. The two-character shard keeps
directory listings small. The URL path the API serves can stay flat (`/audio/<key>.opus`). The
store is backed up by syncing it to object storage later, and the key needs no rewrite for that.

### 4.3 Build (`scripts/audio/…`, idempotent; runs on the repo's Python 3.13 with no torch)

1. **Plan:** read the export and compute every desired spec and key → `desired{key: spec, consumers}`.
2. **Check collisions:** if a key already in the manifest has a different canonical spec → **abort**.
   If two desired specs produce the same key but differ in bytes → abort.
3. **Diff:** `todo = desired − {keys with qa.status = pass and both files present with matching sha256}`.
   Write `todo` as a JSONL job file, ordered by tier (t1 → t2 → t3, research §3).
4. **Synthesise:** run the worker in the separate TTS venv (§8). It reads jobs and writes the
   master to `*.tmp`, then renames it, so a crash can never leave a half-written file under a key.
   Results go to a JSONL file. The worker never touches the manifest.
5. **QA** (§7) → `pass`, or `retake` (take+1, back to step 3, at most 3 takes), or `needs_human`.
6. **Commit to the manifest:** add passing entries, recompute `consumers[]` for all entries, and
   **drop entries with no consumers** unless a key is pinned in `retain.json` (keys a published API
   release still serves; empty until the API exists).
7. **Prune** (explicit `--prune` flag): delete store files whose key is not in the manifest. Deletion
   only happens on this explicit command, never as a side effect.
8. **Export link:** the exporter sets `audio_ref` (§6) only for keys whose manifest entry passes.

### 4.4 Invariants (a `validate_audio_manifest.py` gate, advisory until the first asset lands)

- key == hash(spec) for every entry;
- no two entries with equal canonical specs (this follows from the first, and the check proves it);
- every exported `audio_ref` resolves to a `pass` entry;
- every entry has at least one consumer or is retained;
- when the store is present: file ↔ entry bijection and sha256 match;
- no voice id without a consent record in `voices.json`.

## 5. Voices

- **Japanese:** `ja-f1` and `ja-m1` form the sentence pool. The voice for a sentence is
  `pool[seed_of(text) % 2]`. The choice depends on the text, so identical texts still share one
  file, and the learner hears two talkers, which is the first rung of the R23 multi-talker ladder.
  Words and kana use `ja-word` (= `ja-f1`) so every headword sounds consistent. Listening maps
  `M1→ja-m1, M2→ja-m2, F1→ja-f1, F2→ja-f2, N→ja-n`.
- **pt-BR:** `pt-narrator`, synthesised with the pt-BR Language Pack.
- A reference clip must match the voice's language tag (model card). Every clip needs a
  **native speaker with signed consent** covering synthetic reuse in a paid app (research §4).

## 6. Consumer links (W33 schema fields)

The corpus DB already has `sentence.audio_ref` and `sentence.audio_source` (schema_v2.md, all NULL
today). The exported fields:

| Record | New field(s) | Value |
|---|---|---|
| sentence | `audio_ref`, `audio_source` | `aud:<key>` or `null`; `tts` \| `tatoeba` \| `human` \| `null` |
| vocab | `audio_ref`, `audio_source` | the reading of the primary form |
| kanji `example_words[]` | `audio_ref` | same key as its vocab record |
| kana | `audio_ref`, `audio_source` | per glyph |
| reading passage | `sentence_audio_refs[]` | parallel to `sentences[]` |
| listening item | `script[].audio_ref`, `question_audio_ref`, `correct_audio_ref`, `distractor_audio_refs[]` (spoken types only) | per segment |
| listening item / speak unit `audio` | pattern widened to `^(pending|aud:[a-z2-7]{26})$` | stitched item key; speak units stay `pending` until every `say_now` sentence has audio, then drop the field (its sentences carry the refs) |
| lesson | `narration[]` = ordered `{block, lang, audio_ref}` | pt runs + inline jp runs, played in order (lesson_format.md §6) |

**As built (W47 wiring, 2026-09-28; owner directive).** The export publishes the key itself, not a
QA-gated `audio_ref`: `audio_key` (the 26-char key) + `audio_lang` on every voiceable N5 item the plan
covers, whether or not the clip exists yet. Fields: sentence, vocab and kana records; listening
`script[]` turns; lesson `narration[]` = ordered `{span, audio_lang, audio_key}`, where `span` is the
element path of the body block the unit voices ("3", "5.1"; "" = the body root). The keys come from a
tracked table (`research/derived/audio/audio_keys.json`, `scripts/audio/build_audio_keys.py`), and
`validate_audio_keys.py` proves every exported key equals `plan.py`'s. The app decides playability at
request time: a key is shown only when its file is in the store (`<store>/opus/<k[:2]>/<k>.opus`, or the
passing retake via `aliases.json`), so buttons appear as clips land and a failed unit simply never
shows. `audio_ref`/`audio_source` below remain the target once human or Tatoeba recordings exist.

- `aud:` matches the `ref="aud:…"` prefix that lesson_format.md already reserves.
- Voice, model, duration and QA live **only in the manifest**. Records never copy them, so there is
  nothing to drift.
- `audio_source` is the provenance layer in short form: `tatoeba`/`human` = Layer A recordings;
  `tts` = generated from Layer A/B text.
- The ids are locale-neutral (i18n rule). A future `en` narration is just `lang: "en"` units.

## 7. QA (the teacher does not review the MVP, so the machine check has to carry it)

- **ASR round trip, per clip:** transcribe with whisper-large-v3 (the ASR Resemble used, so numbers
  compare), then convert the transcript to **phonetic hiragana** with the same SudachiPy setup, and
  compare it with the unit's phonetic reading (the bank's `kana` field for sentences; the Sudachi
  reading otherwise). Normalise `ー` to the preceding vowel, and ignore punctuation.
  - `mora_cer = edit_distance / morae`.
  - Pass: **0** for `word`/`kana`; **≤ 0.05** for other `ja` units; for `pt`, word error rate
    **≤ 0.05** on lower-cased, punctuation-free text.
- **Signal checks:** duration within [0.5×, 2.5×] of `morae / 6 s` (ja) or `chars / 14 s` (pt); no
  internal silence over 1.2 s; no clipping; loudness within ±1 LU of the target.
- A failure means take+1 (a new key). After 3 failed takes the unit is `needs_human`: it is listed,
  it exports `null`, and it is **never shipped as is**.
- **Human spot checks,** until the teacher arrives (owner D4): the owner listens to a fixed random
  1% per tier plus every `reading_source: sudachi` unit that passed with `mora_cer > 0`.

## 8. Runtime (recommended path; no install done in this unit)

The TTS environment lives **outside the repo** (`C:\Users\WiseWolf\tts\`), with its own venv on
Python 3.12. The repo's scripts only write jobs and read results (§4.3), so the corpus venv never
imports torch.

1. Install the AMD Adrenalin driver **≥ 26.2.2**. Plug the monitor into the **RX 9070 XT**, not the
   motherboard (ROCm #6458). If an iGPU is enabled, pin `HIP_VISIBLE_DEVICES` to the dGPU (#8379).
2. `uv python install 3.12` and `uv venv C:\Users\WiseWolf\tts\.venv --python 3.12`.
3. ROCm SDK + PyTorch **7.2.1 release** wheels (the AMD Windows page): `uv pip install --no-cache`
   `rocm_sdk_core-7.2.1`, `rocm_sdk_devel-7.2.1`, `rocm_sdk_libraries_custom-7.2.1`, `rocm-7.2.1.tar.gz`,
   then `torch-2.9.1+rocm7.2.1`, `torchaudio-2.9.1+rocm7.2.1`, `torchvision-0.24.1+rocm7.2.1` (cp312)
   from `https://repo.radeon.com/rocm/windows/rocm-rel-7.2.1/`. **Do not** use the 7.14 multi-arch
   preview for batch work (#8379).
4. Chatterbox **pinned to a commit** that has `t3_model="v3"` (master, package 0.1.7), installed with
   `--no-deps`, because it pins `torch==2.6.0`. Then install its other dependencies explicitly:
   `transformers==5.2.0 diffusers==0.29.0 librosa==0.11.0 s3tokenizer conformer==0.3.2
   safetensors==0.5.3 pykakasi==2.3.0 spacy-pkuseg pyloudnorm omegaconf "numpy<2"` and
   `resemble-perth` from git. Skip gradio.
5. **Smoke test** (this gates every batch run): `torch.cuda.is_available()`, the device name, and
   `torch.ones(1024, device="cuda").sum() == 1024` plus a matmul compared against the CPU result
   (this catches #8379's silent zeros). Then synthesise one fixed ja and one fixed pt sentence and
   run them through the §7 QA.
6. Weights: download (an owner-approved step) the V3 base and `ResembleAI/Chatterbox-Multilingual-pt-br`.
   Record each HF revision and checkpoint sha256 in `config.json`.
7. **Fallback** if step 5 fails: a **new WSL2 Ubuntu 24.04** distro (Debian is not in AMD's WSL
   matrix), Adrenalin for WSL2, ROCm 7.2.1 and torch 2.9.1 per AMD's WSL guide, with the store on
   `/mnt/c`. DirectML (end of life) and ZLUDA (unofficial, unneeded) are not options.

## 9. Pilot, then the run

**Pilot:** 200 t1 units, stratified: 50 words (incl. 10 homophone pairs), 20 kana, 50 short
sentences, 40 long sentences (20 with digits), 20 listening turns, 20 pt narration sentences.

It measures:
- wall-seconds per audio-second in fp32 vs bf16 (then set the schedule);
- VRAM;
- QA pass rate per kind;
- the owner's ear on 50 clips.

**Go:** ≥ 95% pass within 3 takes per kind.

**No-go for a kind** moves that kind to its fallback:
- kana → a human recording (211 short clips, a few minutes of a native speaker);
- words → an accent-controllable engine, researched then;
- sentences → a decision for the owner.

**Run:** t1, then t2, then t3 (research §3 has the volumes), in overnight batches. The coverage per
tier is printed in the audio gate after each batch.

## 10. Open for the owner

1. **Speakers:** who records the reference clips (JP F1, M1, F2, M2, N; pt-BR narrator), and the
   signed consent form. **This blocks the first real clip.**
2. **Tatoeba clips:** fetch the per-clip licences for the 107 t1 sentences with native audio, and
   use the ones cleared for commercial use.
3. **Pitch:** Chatterbox cannot follow accent data. Do we accept TTS accent for general audio and
   keep pitch teaching on human or controllable audio (recommended)?
4. **Store location and backup** (default `../yomineko-audio/`).
