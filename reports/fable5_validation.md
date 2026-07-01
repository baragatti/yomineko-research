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
| 1 | kanji meanings EN + pt-BR (N5→N1) | 2,131 | done |
| 2 | vocab glosses EN + pt-BR (N5→N1) | 7,401 | running |
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

## Phase 1 — kanji meanings (2,131 records, all levels)

**Run:** 61 finder agents (35 kanji each) + 2 adversarial verifiers per findings batch; 171 agents,
~8.0M tokens, 17.6 min. Raw: [`phase1_kanji.json`](../research/derived/fable5_validation/phase1_kanji.json).

**Result: 162 raw findings → 140 confirmed (11 critical / 99 major / 30 minor), 13 disputed, 9 rejected.**
106 distinct kanji (~5% of the corpus) carry a confirmed defect. pt-BR side has ~2× the defects of the
EN side (110 vs 52), and defects concentrate in N1 (75) — the levels farthest from the course got the
least prior scrutiny (N5: 2, N4: 16, N3: 24, N2: 23, N1: 75).

### All 11 confirmed CRITICALS (teach something false)
| kanji | field | current | fix | why |
|---|---|---|---|---|
| 小 | pt | pequeno, **pouco** | pequeno | "pouco" is quantity = 少, not 小 (size) — direct 小/少 collision |
| 強 | en | strong, **study** | strong, coerce | "study" is 勉強's meaning, not the character's |
| 強 | pt | forte, **estudar** | forte, coagir | same compound-derived error |
| 仕 | en | serve, do, **matter** | serve, do | "matter" belongs to 仕方/仕事 compound semantics |
| 仕 | pt | servir, fazer, **assunto** | servir, fazer | mirror of the above |
| 株 | pt | ação, **tronco**, cepa | ação, toco, cepa | 株 = stump (toco), not trunk (tronco) |
| 脚 | en | leg, **script** | leg, lower part, base | "script" is 脚本's meaning, not the character's |
| 脚 | pt | perna, **roteiro** | perna, parte inferior, base | mirror of the above |
| 鶴 | pt | grou, **garça** | grou | garça = heron (鷺), a different bird |
| 廷 | en | court, **courtyard**, tribunal | court, imperial court, tribunal | 廷 is the imperial/law court, never a yard |
| 煮 | pt | **refogar** | cozinhar em fogo brando | 煮る = simmer/boil; refogar = sauté (wrong technique) |

### Notable confirmed majors (pattern: compound meanings leaking onto single characters)
学 "school" (=学校), 切 "important" (=大切), 発 "sound (a sound)" (not a sense; pt "disparar" was right),
通 pt missing "frequentar" (通う), 送 pt "despedir" (= to fire someone; needs "despedir-se"),
的 pt "-tico" (nonexistent suffix; correct is "-ico"), 意 pt "ânimo" (should be "mente").

### Disputed (split verdict — route to human review)
陸(en), 普(en+pt), 患(en+pt), 銅(en+pt), 誘(pt), 酸(en+pt), 寧(en+pt), 傍(pt) — 13 findings on 8 kanji.

**Recommended fix path:** apply the 140 confirmed fixes via a `reauthor_kanji_apply.py`-style script into
the DB + re-export (they are meaning-list string replacements), keep `needs_review: true`, and send the 13
disputed to the teacher queue.
