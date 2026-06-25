# Dataset manifest — jlpt

_Fetched 2026-06-13. Raw files are git-ignored; this manifest + checksums are tracked._

## Original 2 lists

| file | bytes | sha256 | url | license |
|------|------:|--------|-----|---------|
| kanji.json | 5,508,152 | `561b72ea9df703c5…` | https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji.json | MIT |
| n5.csv | 55,931 | `8863a96442adeadf…` | https://raw.githubusercontent.com/elzup/jlpt-word-list/master/src/n5.csv | (elzup/jlpt-word-list) |
| n4.csv | 42,190 | `10377b5d9a028999…` | https://raw.githubusercontent.com/elzup/jlpt-word-list/master/src/n4.csv | (elzup/jlpt-word-list) |

## Additional independent lists (added 2026-06-13 for ≥3-list reconciliation)

VOCAB sources (3 added, independent of elzup):

| file | bytes | sha256 | url | level field | headword field | rows | license |
|------|------:|--------|-----|-------------|----------------|-----:|---------|
| jlptvocabapi_n5.json | 60,065 | `e4df18a5f233f770…` | https://jlpt-vocab-api.vercel.app/api/words/all?level=5 | `level` (5) | `word` (reading `furigana`) | 662 | MIT (wkjagt/jlpt-vocab-api) |
| jlptvocabapi_n4.json | 60,241 | `5199bff200f70cea…` | https://jlpt-vocab-api.vercel.app/api/words/all?level=4 | `level` (4) | `word` (reading `furigana`) | 632 | MIT (wkjagt/jlpt-vocab-api) |
| openanki_vocab_n5.csv | 63,965 | `f89abc86b391c4f2…` | https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n5.csv | `tags` col contains `JLPT_N5` | `expression` (reading `reading`) | 718 | MIT (jamsinclair/open-anki-jlpt-decks) |
| openanki_vocab_n4.csv | 49,627 | `0e835f40a8d2a1f1…` | https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n4.csv | `tags` col contains `JLPT_N4` | `expression` (reading `reading`) | 668 | MIT (jamsinclair/open-anki-jlpt-decks) |
| bluskyo_vocab_n5.csv | 13,556 | `bf8590ae8d34110e…` | https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/vocab/parsedData/n5_vocab_cleaned.csv | filename (n5) | `Kanji` (reading `Reading`) | 700 | MIT (Bluskyo; data from tanos.co.uk / J. Waller) |
| bluskyo_vocab_n4.csv | 13,758 | `c0c96e4a048e2619…` | https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/vocab/parsedData/n4_vocab_cleaned.csv | filename (n4) | `Kanji` (reading `Reading`) | 649 | MIT (Bluskyo; data from tanos.co.uk / J. Waller) |

KANJI sources (3 added, independent of davidluzgouveia):

| file | bytes | sha256 | url | level field | character field | rows | license |
|------|------:|--------|-----|-------------|-----------------|-----:|---------|
| kanjiapi_kanji_n5.json | 475 | `08e9c6f3b9336745…` | https://kanjiapi.dev/v1/kanji/jlpt-5 | endpoint (jlpt-5) | array elements (chars) | 79 | CC-BY-SA-4.0 (kanjiapi.dev, JMdict/KANJIDIC) |
| kanjiapi_kanji_n4.json | 997 | `f5c59d82264c8648…` | https://kanjiapi.dev/v1/kanji/jlpt-4 | endpoint (jlpt-4) | array elements (chars) | 166 | CC-BY-SA-4.0 (kanjiapi.dev, JMdict/KANJIDIC) |
| anchori_kanji.json | 736,315 | `ea3ca8865ea56dcb…` | https://raw.githubusercontent.com/AnchorI/jlpt-kanji-dictionary/main/jlpt-kanji.json | `jlpt` ("N5"/"N4"/…) | `kanji` | N5=80, N4=170 (total 2136) | MIT (AnchorI/jlpt-kanji-dictionary) |
| bluskyo_kanji_n5.csv | 402 | `eb0b1f3c077f62b3…` | https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/kanji/parsedData/n5_kanji.csv | filename (n5) | `Kanji` | 79 | MIT (Bluskyo; data from tanos.co.uk / J. Waller) |
| bluskyo_kanji_n4.csv | 837 | `42a8993084e741d6…` | https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/kanji/parsedData/n4_kanji.csv | filename (n4) | `Kanji` | 166 | MIT (Bluskyo; data from tanos.co.uk / J. Waller) |

_Counts: vocab lists now = elzup + wkjagt + open-anki + Bluskyo = 4 independent. kanji lists now = davidluzgouveia + kanjiapi.dev + AnchorI + Bluskyo = 4 independent._

## N3 lists (added for the N3 extension; raw files git-ignored)

VOCAB (single open lineage = Tanos/Waller; relaxed spec 1.5 -> needs_review):

| file | url | headword field | license |
|------|-----|----------------|---------|
| bluskyo_vocab_n3.csv | https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/vocab/parsedData/n3_vocab_cleaned.csv | `Kanji` (reading `Reading`) | MIT (Bluskyo; data tanos.co.uk / J. Waller) |
| n3.csv (elzup) | https://raw.githubusercontent.com/elzup/jlpt-word-list/master/src/n3.csv | `expression` | elzup (old-level tags; not used as canonical) |
| openanki_vocab_n3.csv | https://raw.githubusercontent.com/jamsinclair/open-anki-jlpt-decks/main/src/n3.csv | `expression` | MIT (old-test split; not used as canonical) |

KANJI (2 genuinely-independent lineages agree at 367):

| file | url | license |
|------|-----|---------|
| kanji.json (jlpt_new=3) | (already present) davidluzgouveia/kanji-data | MIT |
| kanjiapi_kanji_n3.json | https://kanjiapi.dev/v1/kanji/jlpt-3 | CC-BY-SA-4.0 (kanjiapi.dev) |
| bluskyo_kanji_n3.csv | https://raw.githubusercontent.com/Bluskyo/JLPT_Vocabulary/main/data/kanji/parsedData/n3_kanji.csv | MIT (Bluskyo; tanos.co.uk) |

GRAMMAR (single open lineage):

| file | url | license |
|------|-----|---------|
| n3_grammar_hanabira.json | https://raw.githubusercontent.com/tristcoil/hanabira.org/main/backend/express/json_data/grammar_ja_JLPT_N3_0001.json | MIT (tristcoil/hanabira.org) |
