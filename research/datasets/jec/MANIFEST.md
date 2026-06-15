# Dataset manifest — jec (JEC Basic Sentence Data)

_Fetched 2026-06-15. Raw file is git-ignored; this manifest + checksum are tracked._

**Source:** Kyoto University Kurohashi-Kawahara Lab (Japanese) + NICT MASTAR Project (English/Chinese).
**License:** CC BY 3.0 Unported — commercial use + redistribution OK with attribution, **no share-alike**.
**Landing page:** https://nlp.ist.i.kyoto-u.ac.jp/EN/index.php?JEC%20Basic%20Sentence%20Data

| file | bytes | sha256 | url |
|------|------:|--------|-----|
| JEC_basic_sentence_v1-2.xls | 1,075,712 | `040601b765841b71…` | https://nlp.ist.i.kyoto-u.ac.jp/EN/index.php?plugin=attach&refer=JEC%20Basic%20Sentence%20Data&openfile=JEC_basic_sentence_v1-2.xls |

5,304 basic sentences (ja + manual en + zh). We load ja+en, dropping 575 rows containing latin/`〜`
placeholder template variables → **4,729 usable** in `raw_jec` + `raw_jec_fts`. Ingested by
`scripts/ingest/ingest_jec.py`; mined into the sentence bank by `scripts/ingest/prepare_jec.py`.
