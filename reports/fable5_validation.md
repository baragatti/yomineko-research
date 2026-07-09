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
| 2 | vocab glosses EN + pt-BR (N5→N1) | 7,401 | **done (Opus-both)** |
| 3 | sentence bank: JP, kana/romaji, translations, structure explanations, token glosses | 5,565 | pending |
| 4 | grammar points: labels, forms, explanations | 496 | pending |
| 5 | conjugation tables: every form, every table | 1,157 | pending |
| 6 | lesson bodies + reading boxes + topic metadata | 314 lessons / 286 readings | pending |

---

## Phase 0 — deterministic pre-pass (`scripts/fable5_prepass.py`)

8,528 raw hits, which reduce to **2 systemic mechanical defects**, **1 real data defect**, and noise:

> **STATUS 2026-07-02: both systemics + the kana defect FIXED and committed** (`aeec3ac`):
> punctuation ASCII-ized in all sentence/token/reading romaji, `conjugate.py` romanizer now
> converts katakana (kata2hira pre-pass), 人 leak fixed in derived fields (token.reading kept as
> analyzer truth per gate G2). Pre-pass residual: 8,528 → 279, all by-design noise. Gate green.

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

> **STATUS 2026-07-02: all confirmed fixes APPLIED and committed** (`ec85e31`): 142 field-edits on
> 106 kanji via `scripts/fable5_kanji_patch_gen.py` (+3 prose fixes hand-resolved, +2 post-review
> corrections on 措/架) → `scripts/fable5_kanji_apply.py` (DB) → re-export. Verified 1:1 against the
> patch with zero unexpected record changes. Gate green. The 13 disputed stay for teacher review.

---

## Phase 2 — vocab glosses (7,433 records, all levels) — **Opus-both-roles**

**Model change (2026-07-07).** Fable 5 moved to usage-based billing on the plan mid-phase, so — per the
owner's decision — the campaign switched from *Opus-authors / Fable-5-verifies* to **Opus 4.8 for both
roles**: Opus finders, then **2 independent Opus verifiers** per findings batch (same
`confirmed`/`disputed`/`rejected` merge). Cross-model diversity is traded for cost; the 2-vote adversarial
gate is preserved. See memory `qa-model-split-opus-both`.

**Run.** 247 finder batches (30 vocab each) executed in **5 waves** of ~50 (wave-splitting added after an
earlier Fable-5 run died on a session limit at batch 13 — a limit hit now costs one wave, not the whole
job; `scripts/fable5_vocab_workflow.js` takes explicit batch indices). Wave 1's findings were re-verified
uniformly under Opus (`<scratchpad>/fable5_vocab_reverify_opus.js`). Raw per-wave + merged:
[`phase2_vocab_*.json`](../research/derived/fable5_validation/); apply-ready confirmed slice:
[`phase2_vocab_confirmed_apply.json`](../research/derived/fable5_validation/phase2_vocab_confirmed_apply.json).

**Result: 134 merged findings → 115 confirmed (45 critical / 36 major / 34 minor), 6 disputed, 13 rejected**,
touching **96 distinct vocab** (~1.3% of the 7,433 checked). Confirmed defects split **pt 58 / en 51 /
romaji 5** — unlike Phase 1's 2× pt skew, the EN side carries nearly half here because the dominant defect
class is reading-based (below), which corrupts EN and pt symmetrically.

### The dominant defect class — cross-reading / homophone sense-bleed (42 of 115, ~all criticals)
A gloss that belongs to a **different reading of the same kanji** (or a true homophone) got attached to the
wrong reading's lexeme — teaching a false meaning. This is systematic, not random, and concentrated in the
critical tier. Representative confirmed criticals:

| headword (reading) | wrong sense it carried | belongs to | 
|---|---|---|
| 会う (あう) | "to fit / suit / match" | 合う |
| 彼 (あれ) | "he / boyfriend" (ele / namorado) | 彼 (かれ) |
| 映る (うつる) | "to reflect/project" + "to infect (a cold)" | 映す / 移る |
| 尋ねる (たずねる) | "to visit" | 訪ねる |
| 実 (み) | "truth / reality" | 実 (じつ) |
| 度 (たび) | "degree (temperature/angle)" | 度 (ど) |
| 柄 (え) | "pattern/design" + "nature/character" | 柄 (がら) |
| 札 (さつ) / 札 (ふだ) | "tag/label" ↔ "banknote" (swapped) | the other reading |
| 熱中 (ねっちゅう) | "heatstroke" | 熱中症 (fabricated from the compound) |
| だから | invented conjunction sense "because" | — (not a JMdict sense) |

Plus 伯←伯父, 位(suf/prt)←位(noun), 何←何と, 叔父←小父さん, 杯(さかずき, sake cup)→generic cup, 課程←過程,
種(たね)←品種, 罹る←掛かる, 経つ↔立つ, 達(name-suffix)←達(tachi), 生る←成る, and more (full list in the
apply file). **Recommended follow-up (post-apply): a targeted deterministic audit** — for every vocab whose
kanji has multiple JMdict readings, cross-check each sense against the reading it's actually filed under.

### Other confirmed classes
- **EN meaning/nuance errors (24):** missing must-know noun sense (規制 "regulation"), false-nuance adds
  (久しい "long-awaited" — an anticipation nuance it lacks), wrong counter scope (通 "phone calls").
- **pt-BR false friends (10):** 口紅→"rouge" (=blush, not lipstick), 印刷→"imprensa" (=the press), 模倣→
  "mímica" (=mime/charades), ビジネス→"empresa" (=company), 対談→"entrevista" (=interview).
- **pt-PT / non-BR register leaks (7):** algures, apoiante, saldo (=sale, EP), recolha, "a passear"/"a
  ferver" (EP *estar a + inf* progressive), "cursada" (Rioplatense Spanish).
- **Orthography / romaji (5):** cardapio→cardápio, auto-estudo→autoestudo (Acordo), an'i/kon'ya apostrophe.
- **Register landmines / other pt wording (27):** 角→"corno" (cuckold slang), previdência-vs-bem-estar, etc.

### Disputed (6 — split verdict, teacher queue)
中/ちゅう "throughout" (genuine reading-overlap question), すると sense 2 (inferential vs conditional; en+pt),
こんや romaji apostrophe convention, 楽しみ pt "ansiar por", プロ pt "profissa" register.

### Rejected (13 — false positives, dropped; kept in JSON for audit)
Mostly the finder over-flagging defensible pt-BR wording ("sem graça" for まずい, "palhaçar", "brinde") and
one register nitpick ("tu"). Verifiers correctly upheld the originals.

> **STATUS 2026-07-09 (later): all confirmed fixes APPLIED (owner go-ahead) — 95 vocab re-sensed (147
> senses), 5 romaji corrected, gate green.** Pipeline: `fable5_vocab_patch_gen.py` converted the 115
> free-text fixes into explicit DB-anchored edits (auto ops + a MANUAL table for ~30 hand-resolved cases —
> pt-only verifier fixes got authored EN mirrors, gloss-level removes were separated from sense-level,
> pasted fix-text was rejected by guard rails) → the before/after diff was **adversarially audited twice**
> (round 1: 18 flags, all fixed + turned into generator guards; round 2: 1 shape nit, fixed;
> diff-verified minimal between rounds) → `fable5_vocab_apply.py` (DB + localized_text mirrors) →
> exam banks + full corpus re-exported → 16-validator gate green. The 96th confirmed defect
> (vocab:1385390 **接見**, a LEVEL defect: tagged N5 via kana collision with 石鹸/soap) was fixed by
> `fable5_fix_sekken_level.py` (→ n1, collision documented; its items dropped out of the N5 exam banks on
> regen). The 6 disputed → teacher review; the 13 rejected → no action.

---

## Phase 3 — sentence bank (5,565 records) — IN PROGRESS (wave 1/6 done)

**Run:** 371 batches (15 sentences each) in 6 waves; session model (Fable 5 verify restored 2026-07-09).
**Wave 1 (batches 000–061, 925 sentences): 707 field-level findings — 195 confirmed (60 critical / 80
major / 55 minor); 512 pending re-verification** (the session limit killed the verifiers of 44/62 batches;
finder results saved, verify-only re-run staged via `fable5_sentences_reverify_workflow.js` +
`phase3_reverify/wave1/` group files). Raw: `phase3_sentences_wave1_batches000-061.json`. Early confirmed
patterns: wrong in-context readings cascading across kana/romaji/expl/tokens (何時 いつ vs なんじ),
explanations citing words absent from the sentence (看護婦 vs 看護師), wrong grammar-form alternatives
(ても offered in なくてはならない), collocation-sense mistranslations (ネクタイを締める "tightens" vs
"puts on"). Waves 2–6 + the apply step follow.
