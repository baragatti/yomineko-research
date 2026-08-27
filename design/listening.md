# Listening (聴解) — text-script bank spec (v1, 2026-07-06)

> Deliverable of THIS run: **voice-ready TEXT scripts** in `corpus/exam_banks/{level}_listening_*.json`
> (`audio: "pending"`). The owner voices them later (likely a local Japanese TTS/voice LLM); the app plays
> audio and never shows the script during the exam (scripts double as transcripts for review mode). Real JLPT
> papers are © JEES — as with the other sections, only the (non-copyrightable) FORMAT is mirrored; every
> script is ours, authored + adversarially verified.

## Subsections (mirror the real exam)

| Subsection (type) | What is heard | Options | N5 | N4 | N3 |
|---|---|---|---|---|---|
| listening_task (課題理解) | setting → dialogue → question | 4, printed | 7 | 8 | 6 |
| listening_point (ポイント理解) | setting + question FIRST → dialogue → question again | 4, printed | 6 | 7 | 6 |
| listening_gist (概要理解) | monologue → question | 4, spoken | – | – | 3 |
| listening_say (発話表現) | narrated situation | 3, spoken (utterances) | 5 | 5 | 4 |
| listening_reply (即時応答) | one short utterance | 3, spoken (responses) | 6 | 8 | 9 |

Per-paper counts ≈ real exams (guideline; yearly variation exists). Listening timing: N5 ≈ 30 min,
N4 ≈ 35 min, N3 ≈ 40 min. **Bank size = 3× the paper count** per subsection (v1; expandable):
N5 72, N4 84, N3 84 → **240 scripts**.

## Item schema (uniform across subsections)

```json
{"id": "lt:n5:001", "level": "n5",
 "script": [{"speaker": "N", "text": "お店で男の人と女の人が話しています。"},
            {"speaker": "M1", "text": "…"}, {"speaker": "F1", "text": "…"}],
 "question": "男の人はこのあと何を買いますか。",
 "correct": "…", "distractors": ["…", "…", "…"],
 "sentence": "sent:… (listening_reply only — the REAL bank sentence used verbatim as the prompt)",
 "audio": "pending", "layer": "C", "needs_review": true, "ai_generated": true}
```

- `script` = ordered spoken turns. Speaker registry (locale-neutral): `M1 M2 F1 F2` (dialogue voices),
  `N` (narrator/announcer — settings, situations). The TTS pipeline maps speakers → voices per level/paper.
- ID prefixes: `lt:` task, `lp:` point, `lg:` gist, `ls:` say, `lr:` reply.
- `question` is empty for `ls:`/`lr:` (the format IS the question). Option count: 3 distractors for
  lt/lp/lg, 2 for ls/lr (matches the real exam's 4- vs 3-option subsections).

## Playback order (app + TTS stitching)

- **task**: N-setting → dialogue → question → *(printed options; question repeated once)*.
- **point**: N-setting + question → pause (read options) → dialogue → question again.
- **gist**: monologue → question → the 4 options SPOKEN (nothing printed).
- **say**: N-situation → the 3 utterance options SPOKEN.
- **reply**: prompt utterance → the 3 response options SPOKEN.

Every text field is a TTS unit; pauses live between fields, so no pause markup inside strings.

## Grounding + authoring rules (how we keep 1.2 honest)

1. **listening_reply prompts are REAL bank sentences** (utterance-like: question/appeal endings, 6–22 chars,
   `ai=0`), selected deterministically and used VERBATIM (assembly enforces byte-equality; item carries the
   `sentence` slug). Only the three responses are authored.
2. Dialogues/monologues are authored (they cannot be selected — the bank has no multi-turn material), but
   **seeded**: each item gets 2–3 seed words stride-sampled from the level's vocab registry; the scenario must
   use at least one. Keeps content in-level, diverse, and traceable.
3. **Level cap**: vocabulary and grammar at or below the item's level; spoken register (natural contractions
   fine at N4/N3: 〜てる、〜ちゃう; N5 stays textbook-polite).
4. **Distractor craft (the real exam's signature)**: for task/point, all four options should be things
   MENTIONED in the dialogue — three get rejected/changed mid-conversation, one is the final decision. Never
   options the audio never touches.
5. Standard framing formulas (男の人と女の人が話しています／〜はこのあと何をしますか) are generic exam
   conventions, not protected expression.
6. Verification: per-batch adversarial native-level review — natural spoken Japanese, level-appropriate,
   answerable from the script ALONE, correct entailed, distractors clearly wrong, options parallel, register
   sane, speaker turns coherent. Flagged items are fixed per the stated reason and re-checked (the
   reading_comp loop) or dropped.
7. Deterministic assembly guards (`build_listening_bank.py`): JP-only text (full-width Latin allowed),
   speaker ∈ registry, turn-count bounds, option counts per type, distinct options, correct ∉ distractors,
   no em dash, reply prompts byte-equal to their real sentence, refs resolve.

## Voice-over pipeline (owner, later)

- Any local Japanese TTS works off the schema directly: render each `script[]` turn with its speaker's voice,
  then question/options per the playback order. Suggested local options: VOICEVOX (free, per-voice licenses
  mostly allow commercial use with credit — check per character), Style-Bert-VITS2, or a local voice LLM.
- Deliver audio as one file per item id (stitched with the standard pauses) or per-segment files; the app
  only needs `id → audio` and flips `audio: "pending"` → file ref. Re-voicing never touches item data.
- Numbers/times are written in standard Japanese orthography (３時、５００円) — TTS-safe; no romaji anywhere.

## Simulator integration

The picker (design/exam_simulator.md) adds the five sections with the per-paper counts above; sampling,
no-repeat window, option shuffle, and scoring rules are unchanged. Study mode may SHOW the script after
answering (transcript reveal) — exam mode never does.
