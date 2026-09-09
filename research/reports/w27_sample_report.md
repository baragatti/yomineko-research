# W27 — production answer keys: Fable 100-row sample (2026-09-09)

Table: `research/derived/pending/card_production_keys.json` (2,946 rows, authored-only after the
index-keyed verifier verdicts could not be paired). Plan v3 replaced the 30-agent re-verification
with this sample (APP_PLAN §1 "verify once"). Sample: seed 27, 100 rows, saved as
`research/derived/pending/w27_sample_rows.json`. Each row read against the record in
`corpus/vocab/` and the lesson that issues the card.

## Verdict: pass (2 failures of 100, both one mechanical class) → apply with `verified: "sampled"`

What was checked per row: the prompt names the sense the lesson teaches and disambiguates it from
homographs and siblings; the accept set contains only forms of THAT record; pt-BR natural, no
pt-PT, no em dash.

**Quality.** Prompts are short, natural and disambiguating (方々 かたがた "plural cortês de 方" vs
方々 ほうぼう "por toda parte"; 上 かみ "curso superior de um rio (lê-se かみ)" matches the W11 ruling;
開く あく vs the transitive; 中 ちゅう "(lê-se ちゅう)"). No prompt in the 100 names a sense the lesson
does not teach.

**Failures (2).** Rows still address records W09 re-pointed after this table was authored:
- `vocab:1551240` 立ち "partida, saída" in les:n5-particulas-lugar-03 — the record is now
  `vocab:1416220` 達/たち (plural suffix); prompt and key are wrong for the card the lesson issues.
- `vocab:1172610` 運 "sorte" in les:n4-forma-simples-02 — now `vocab:1001090` うん ("sim", informal).
All 8 W09 re-points are of this class (2 landed in the sample by chance), plus the 5 cards W11a
created (unlocks) that have no row at all.

**A leniency, not an error (rule for the apply).** Accept sets carry every JMdict form, including
rare, archaic and colloquial ones: 海 accepts み/わた/わだ, 暑い accepts あぢぃ/あぢい/あぢー/アツい,
昼間 accepts ちゅうかん, 職 accepts そく, 戸 accepts 門. A learner typing み for "mar" would be marked
right. Strip forms JMdict tags `rK`, `sK`, `ok`, `ik`, `oK`, `arch` from accept sets mechanically;
keep the headword, its common kanji variants and the kana.

## Rules for the W27 apply script (both mechanical, no authoring beyond 13 rows)

1. Resolve every `vocab` through `corpus/vocab_redirects.json`; the 8 re-pointed rows are dropped
   from the table and re-authored for the new record (prompt + accept), together with keys for the 5
   W11a unlock cards — a 13-row authoring residue, one verifier.
2. Strip rare/archaic/colloquial forms from `accept` by JMdict tag; log per-row what was removed.
3. Every applied row gets `verified: "sampled"` with a pointer to this report; the table moves from
   `pending/` to `repairs/` with the apply script (W02 replays it).
