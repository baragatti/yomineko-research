# Fable 5 full-corpus translation validation (2026-07-01)

**What this is.** A one-time, full-corpus QA sweep of every AI-authored or AI-touched text
(JP → EN → pt-BR), run on Claude Fable 5 (a more capable model than the Opus 4.8 that authored the
content), per the owner's directive and the plan in [`design/translation_qa.md`](../design/translation_qa.md).
Method per phase: deterministic pre-pass first, then batched **finder** agents with a strict rubric, then
**2 independent adversarial verifiers** per finding (verdicts: `confirmed` = both uphold, `disputed` = split,
`rejected` = both refute). Only confirmed/disputed findings are actionable; rejected ones are kept in the
JSON for audit. Raw findings: [`research/derived/fable5_validation/`](../research/derived/fable5_validation/).

Scope (validation order set by owner):

| phase | content | records | status |
|---|---|---:|---|
| 0 | deterministic style/QA pre-pass (whole repo) | all JSON | done |
| 1 | kanji meanings EN + pt-BR (N5→N1) | 2,131 | running |
| 2 | vocab glosses EN + pt-BR (N5→N1) | 7,401 | pending |
| 3 | sentence bank: JP, kana/romaji, translations, structure explanations, token glosses | 5,565 | pending |
| 4 | grammar points: labels, forms, explanations | 496 | pending |
| 5 | conjugation tables: every form, every table | 1,157 | pending |
| 6 | lesson bodies + reading boxes + topic metadata | 314 lessons / 286 readings | pending |

---

## Phase 0 — deterministic pre-pass (`scripts/fable5_prepass.py`)

8,528 raw hits, which reduce to **2 systemic mechanical defects**, **1 real data defect**, and noise:

### SYSTEMIC-1 — Japanese punctuation left inside romaji strings (~7,790 hits)
Sentence-level `romaji` and token-level `ro` fields keep raw `。！？` etc. instead of ASCII
punctuation (e.g. `konomizuumiwaasainoyo。`). Affects `corpus/sentences/bank.json` (6.4k),
`corpus/readings/*.json` (1.4k). **Fix:** mechanical map `。→.`, `！→!`, `？→?`, `、→,` (+ decide
bracket convention) in the romaji generator + regenerate. No model needed.

### SYSTEMIC-2 — katakana segments never romanized (458 hits, 421 in conjugations)
The romanizer skipped katakana: `キャンプsuru`, `キャンプshimasu`… instead of `kyanpu suru`.
Affects `corpus/conjugations/{n5:38, n4:87, n3:296}` (katakana-stem suru-verbs) plus some readings/bank
tokens. **Fix:** extend the romanizer to katakana + regenerate; this also feeds Phase 5.

### Real data defect (1)
- `sent:tatoeba-3576174` — phonetic `kana` field contains the kanji 人: `さあ、ぴざがいる人ー!`
  (should be ひと).

### Noise / accepted (details in `prepass.json`)
- `locale-missing-en` (269): 268 are kana-chart UI labels (`corpus/kana/*`) that are pt-BR-only by
  design; 1 is `vocab:1928100` `notes` (Layer C note, pt-only acceptable).
- `quanto-a-in-natural` (6): 5 are the legitimate comparative "tanto … quanto"; 1
  (`sent:tatoeba-2233640` "Quanto a isso, não posso concordar.") is defensible natural pt-BR.
- `uk-english` (2): Tatoeba EN originals — Layer A, never edited.
- `kana-impurity` (1 more): `sent:tatoeba-4708` contains Latin "muiriel" (proper name) — fine.
- `bad-token` (1): uppercase Portuguese "durante TODO o tempo" — false positive.
- **Zero hits** for: em-dash in authored text, pt-PT lexicon, generated-JP ending in 。 — the three
  existing style gates hold.

---
