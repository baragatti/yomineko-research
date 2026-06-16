# Kana plan — registry + family lessons + SRS bootstrap (pré-N5, P6b)

> Owner directive (2026-06-16): Hiragana and Katakana are each a **topic**; each gojūon **family** ("Família do
> A", "Família do KA", "Família do SA", "Família do ZA"…) is a **lesson** that unlocks that family's kana. The
> first kana lessons may also introduce a few very simple whole **words** (no sentences, no grammar) to bootstrap
> the first SRS reviews. Sequencing/pitfalls follow [`curriculum.md`](curriculum.md) §5; data/unlock model follow
> [`courseware_architecture.md`](courseware_architecture.md). Clean-room: structure inspired by common kana
> pedagogy (and abstractly by the Phase-L course's idea of family grouping); no content copied.

## 1. Kana registry (NEW corpus registry — Layer A, deterministic)
Create `corpus/kana/hiragana.json` + `corpus/kana/katakana.json` from a deterministic generator
(`scripts/ingest/build_kana.py`); these are facts, no AI. Per kana:
```json
{"id": "kana:hiragana-さ", "char": "さ", "script": "hiragana", "romaji": "sa",
 "family": "kana:hiragana-sa", "family_label": {"pt-BR": "Família do SA"},
 "type": "base", "row": "sa", "column": "a", "stroke_count": 3,
 "dakuten_of": null, "base_of": ["kana:hiragana-ざ"]}
```
`type` ∈ {base, dakuten, handakuten, yoon, sokuon, long-vowel, n}. Families are addressed by id `kana:<script>-<row>`
(e.g. `kana:hiragana-sa`) — this is the `kana-family` unlock ref. A `kana_family` view lists each family's members
+ pt-BR label + order. (Stroke-order SVGs from KanjiVG are kanji-only; kana stroke data is a later add — handwriting
practice can start from static stroke diagrams.)

## 2. Family taxonomy (the lesson units)
**Base gojūon (10 families):** A (あいうえお) · KA (かきくけこ) · SA (さしすせそ) · TA (たちつてと) · NA (なにぬねの) ·
HA (はひふへほ) · MA (まみむめも) · YA (やゆよ) · RA (らりるれろ) · WA (わを + ん).
**Vozeamento — dakuten/handakuten (5 families):** GA (がぎぐげご) · ZA (ざじずぜぞ) · DA (だぢづでど) · BA (ばびぶべぼ) ·
PA (ぱぴぷぺぽ, handakuten).
**Yōon (contraídos):** きゃ/きゅ/きょ, しゃ…, ちゃ…, にゃ…, ひゃ…, みゃ…, りゃ…, ぎゃ…, じゃ…, びゃ…, ぴゃ… (group into 1–2 lessons).
**Especiais:** っ (sokuon, pausa de uma mora) · vogais longas / ー · consolidation review.

## 3. Lesson structure (one family = one lesson; default)
- **Topic T02 Hiragana** → ~14–18 lessons: 10 base-family lessons, then the 5 vozeamento families (lighter —
  "kana já conhecido + marca"), 1–2 yōon lessons, 1 especiais (っ + vogais longas), 1 review. Dakuten families may
  pair if a single-family lesson is too thin, but default to one family per lesson (clean SRS unlock unit).
- **Topic T03 Katakana** → faster (~12–15 lessons): same family order; the learner already knows the *system*, so
  lessons emphasize shape-vs-hiragana contrasts, the long mark ー, and the loanword hook (パン/タバコ/コップ from
  Portuguese — 💡 Vantagem PT), ⚠ katakana false friends + u-epenthesis preview.
- **Each kana lesson body (rich format):** intro (the family's sound pattern) → the 5 kana with pt-BR
  shape/sound mnemonics + (later) stroke order → recognition exercises (kana→som, som→kana) → a production/
  handwriting exercise → `<checklist>`. Length is at the SHORT end of the §7 band (kana lessons are light).
- **`unlocks`:** `{type:"kana-family", ref:"kana:hiragana-sa"}` (+ any bootstrap words as `vocab`). The **first**
  hiragana lesson also unlocks `feat:srs-reviews` (the SRS habit starts here) and `deck:kana-hiragana`; the first
  katakana lesson unlocks `deck:kana-katakana`. `needs`: each lesson needs the previously-taught families only.

## 4. SRS bootstrap words (the linearity exception)
After enough families are known, a lesson may introduce **2–4 very simple words** to seed SRS. Rules:
- **Only already-taught kana** (no kanji), **2–3 mora**, concrete/high-frequency, **no grammar, no sentences**.
- Tagged as **kana-bootstrap** vocab (a flagged subset of the vocab registry; `register`/provenance recorded) so
  P7 knows these are the sanctioned "content slightly ahead of grammar." They unlock as `vocab` + enroll into
  `deck:vocab-n5` (kana-reading cards only, no kanji).
- **Examples by availability** (illustrative): after A+KA → あお (azul), あか (vermelho), かお (rosto), いか (lula);
  after +SA → あさ (manhã), かさ (guarda-chuva), さけ (saquê); after +TA+NA → なに (o quê), たな (prateleira), なつ
  (verão); after +YA/RA/WA → やま (montanha), そら (céu), とり (pássaro). Katakana bootstrap = the loanwords
  (パン pão, バス ônibus, テレビ TV). The exact list is finalized in P6b against the actual N5 vocab registry
  (prefer words that are real N5 vocab so they're not throwaway).

## 5. pt-BR pitfalls woven in (curriculum.md §5)
- ⚠ romaji ≠ português when reading kana: じゃ ≠ "já" (PT [ʒ]); ち/つ affrication; the soft-r tap (ら row); /e/ not
  → [i]; no final-vowel raising. 💡 the 5 vowels closely match PT.
- ん as its own mora (don't nasalize the preceding vowel); っ as a one-mora pause (mora-clapping); vowel length
  (おばさん/おばあさん) — introduced with the long-vowel lesson.

## 6. Build / validation
- `build_kana.py` → `corpus/kana/*.json` + a `kana` + `kana_family` registry in the DB (so `kana-family` unlock
  refs resolve). `export_corpus.py` adds a `kana` row to the master INDEX.
- `validate_lessons.py` resolves `kana:` refs; P7 checks every kana family is unlocked by exactly one lesson and
  that bootstrap words use only already-unlocked kana (the only allowed ahead-of-grammar content).
