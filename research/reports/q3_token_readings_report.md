# Q3: stored token readings applied (chain v4, gate + quick replay)

> Input: `research/derived/pending/token_reading_audit.json` (commit 4f4a4a38, measurement only), moved to
> `research/derived/repairs/token_reading_audit.json`. Only the `class: mechanical` rows are applied; the 15
> `review` rows stay in the same table, held, and the gate asserts they have not moved.

## 1. What landed

| | count |
|---|---:|
| mechanical rows applied (token `reading` + `romaji`) | **295** |
| A-mode sub-tokens rewritten (一回 いち\|かい -> いっ\|かい, twice) | 2 |
| sentences whose `kana` / `romaji` were rebuilt from their C tokens | **272** |
| sentence already carrying the right kana (token was the stale half): `sent:gen-9f80f08cc644` 辛い つらい -> からい | 1 |
| review rows held | 15 |
| I2/I3 violations in the whole bank after the apply (kana == concat C readings, romaji == concat C romaji) | **0** (was 1) |

By rule (mechanical): counter 131, 何 rule 85, verified link 61, 何時 -> なんじ 5, digit-wise numerals 5,
〜中 じゅう 5, ruling text 3.

Samples: 何も無い なんも -> なにも, 何か なんか -> なにか (32 of the 85), ２０年 にれい -> にじゅう, 一分 いちふん ->
いっぷん, ２切れ にきれ -> ふたきれ, 九時 きゅうじ -> くじ, 体中 たいちゅう -> からだじゅう, 米 べい -> こめ,
種 しゅ -> たね, 金次第 きん -> かね, 開く ひらく -> あく (door opens), 直に ちょく -> じか.

## 2. How

- `scripts/apply_token_reading_repairs.py` (manifest step **153**, after every sentence writer incl. the W32
  ingest at 152): per row, the C token at (slug, position) must spell `surface` and hold the old
  reading/romaji (or already the new: idempotent); then each touched sentence's kana/romaji is the concat of
  its C tokens, and where every row of the sentence is mechanical that concat must equal the table's
  `kana_new`/`romaji_new` (272/272 did). The one mixed sentence (`sent:tatoeba-79393`, review row 他 た -> ほか
  held) gets its mechanical tokens and a rebuilt line that still reads た. Second run: 0 writes.
- Layer A has no authoring file for these readings (the dissector writes them on every replay), so the index
  is their only home and step 153 re-asserts them. Token links are not touched.
- `validate.py` §7.2 re-runs SudachiPy and allows a reading that differs from the analyzer only when it is
  registered in `research/derived/fable5_validation/verified_reading_overrides.json`. The 295 readings are
  registered there, append only (410 -> 682 sentences, 508 -> 803 tokens; the note names the table). Without
  that the gate failed with exactly 295 `unregistered reading override` errors.
- Exporters: the corpus was re-exported with `YOMINEKO_BUILD_DATE` pinned to the committed stamp (2026-09-23)
  and the course to its own (2026-09-24), so the INDEX headers do not move. A 2026-09-27 stamp on
  `corpus/grammar/INDEX.md` alone fails the quick replay, whose baseline pins the rebuilt bytes under the
  committed date.
- `validate_repairs_applied.py`: `token_reading_audit.json` registered (mechanical: token carries the new
  reading/romaji and the sentence holds I2/I3; review: checked skip, token still reads the old value).

## 3. Consumers (quoted)

**Lesson-body furigana that had copied the old kana.** Three `<jp reading>` attributes, derived from the bank
kana by earlier tables, now contradicted the sentence card beside them. Fixed in both layers through
`research/derived/repairs/q3_reading_furigana.json` (`apply_lesson_body_spans.py`, step **154**) and the rows
that first wrote them were amended (`amended` field) so a replay writes the corrected value directly:

| lesson | span | before | after | first written by |
|---|---|---|---|---|
| les:n3-revisao-01 | ９時になってはじめて彼は帰ってきた。 | きゅうじに… | くじに… | n3_review_furigana.json |
| les:n4-suposicao-05 | 開きそうにない | ひらきそうにない | あきそうにない | furigana_residue.json |
| les:n4-suposicao-05 | 開く ("abrir") | ひらく | あく | furigana_residue.json |

Attribute only: the rendered text of both lessons is unchanged. A sweep of every `<jp reading>` span in
`course/` that covers a re-read token on token boundaries found no other disagreement (4 hits were
katakana/punctuation normalization, not readings).

**Sentence furigana in lessons** (rendered from the bank tokens, no file edit): 12 `<sentence show="furigana">`
display pairs in 9 lessons now show the corrected reading (the audit's 13th, les:n3-causa-05 on
`sent:tatoeba-142966`, is a held review row and still shows いつ), e.g. les:n5-kanji-exame-03 `sent:tatoeba-2633467`
何飲みたい？ なん -> なに; les:n4-potencial-03 `sent:tatoeba-9979575` 何か聞こえる？ なんか -> なにか;
les:n4-suposicao-05 `sent:tatoeba-3496750` 開きそうにないわ ひらき -> あき. 42 SRS card examples sit on
re-read sentences; none teaches the old reading's record.

**Listening scripts.** 3 `listening_reply` items speak a re-read sentence (lr:n3:tatoeba-9979575,
lr:n4:tatoeba-2552450, lr:n5:tatoeba-2633467), all `audio: pending`. The banks carry no kana copy (the rebuild
changed no exam file); W47's hashed TTS must key on the corrected kana, which it will since the bank is now
right. 27 speak units cite re-read sentences, also `audio: pending`.

**Speak production keys.** `build_speaking_path.py` re-run: 18 `accepted_variants` strings in 4 units now
accept the right answer (からだじゅうのきんにくがいたいです, このへやにごじゅうにんは…, ふへいをいうりゆうはなにもない,
わたしのぱそこんはなにかのやくにたつはずだ, each with its は/わ and 。 variants). The audit counted 28 in 7 units
on an older tree; the other three units no longer cite those sentences. No old kana survives anywhere under
`corpus/` or `course/` (sweep of every JSON except the bank).

**kanji_reading items.** 12 items have a re-read stem (下, 体, 市場, 年, 数, 方, 米, 金, 鳥). Their keys come from
the vocab record: all 12 already equal the corrected reading (いちば, かず, かね, からだ, かた, こめ, した, とし,
とり), none cites a re-read sentence. The rebuilt banks are byte-identical: nothing moved.

**Items citing the old record.** `cf:n5:3820:1341` (何[なん]) is not in the bank at HEAD any more (the builder
had already dropped it). `cj:n4:820:masu` now takes its example elsewhere. `cj:n3:2400:polite` drills
辛い[つらい] with the example `sent:gen-9f80f08cc644` この味噌はちょっと辛いです, which is からい (spicy): a
pre-existing mismatch (that sentence's kana was already からい), left for the conjugation example rule.

## 4. Rendered lessons against HEAD

Lesson `.md` renders: 0 files change. Lesson JSON: 2 bodies, one reading attribute each span (3 spans).
Speak units: 4 files, 18 variant strings. Bank: 295 tokens, 272 sentence lines. No prose line changed.

## 5. Not applied (open)

**15 review rows** (unchanged, asserted by the gate):

| sentence#pos | surface | stored -> proposed | why review |
|---|---|---|---|
| tatoeba-11709247#0 | 308 | さんれいはち -> さんびゃくはち | flight number, may be read digit by digit |
| tatoeba-1171888#0 | 何時 | なんどき -> なんじ | 'how late are you open' |
| tatoeba-1171888#2 | 開い | ひらい -> あい | same pattern as the verified 開く[あく] rulings |
| tatoeba-123906#2 | 何時 | いつ -> なんじ | 'when does it arrive' |
| tatoeba-142966#3 | 何時 | いつ -> なんじ | 'what is the right time' |
| tatoeba-146221#2 | 綿 | わた -> めん | ruling says めん, also possible |
| tatoeba-172526#1 | 何時 | いつ -> なんじ | 'have you got the time' |
| tatoeba-183844#0 | 管 | かん -> くだ | ruling says くだ, also possible |
| tatoeba-186679#4, 186687#4, 186715#5 | １１９ | いちいちきゅう -> ひゃくじゅうきゅう | emergency number is read いちいちきゅう |
| tatoeba-189309#2 | 何時 | いつ -> なんじ | 'when does the movie start' |
| tatoeba-210733#3 | 玩具 | がんぐ -> おもちゃ | ruling says おもちゃ, also possible |
| tatoeba-78961#3 | １００３ | いちれいれいさん -> せんさん | booking code |
| tatoeba-79393#3 | 他 | た -> ほか | ruling says ほか |

Note on the three １１９ rows: 119 as the Japanese emergency number is conventionally read ひゃくとおばん or
いちいちきゅう; neither is the proposed ひゃくじゅうきゅう, so these need a human value, not a yes/no.

**16 token links the new reading no longer fits** (11 on applied rows, 5 on held ones; link work, not
reading work): 何時[いつ] x10 (5 applied
なんじ rows; the 5 review ones would join), 一[いち] x4 (一 ひと), 日[にち] x1 (一日 ついたち), 日中[にっちゅう]
x1 (一日中 にちじゅう). No sibling record reads the new way (no 何時[なんじ], 一日中 record): registry follow-up
for the v5 link unit, together with `pending/link_suspects.json`.

**Reading boxes** hold their own Layer-C tokens (0 re-read sentences among their sources); not audited here.
