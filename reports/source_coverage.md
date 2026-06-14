# Source Coverage Report (Phase R3 — empirical)

> **Empirical, not assumed.** Every number below was produced by probing the actual downloaded datasets
> with [`scripts/validate/r3_coverage_probe.py`](../scripts/validate/r3_coverage_probe.py). Raw results:
> [`research/coverage/r3_probe_results.json`](../research/coverage/r3_probe_results.json). Dataset versions +
> checksums: `research/datasets/*/MANIFEST.md`. Probe date: 2026-06-13.

## TL;DR (decisions this forces)
1. **Kanji backbone is 100% complete** for N5+N4 — no gaps in readings, strokes, stroke-order, or radicals.
2. **Vocab coverage is effectively ~99%** once a normalization layer is added; the apparent gap is list
   formatting and affix/する handling, **not** missing dictionary data.
3. **Tatoeba Portuguese translations are far too sparse to rely on (1.8% of JP sentences).** → We **select**
   the *Japanese* sentence (the part that must be natural/correct) but **generate the pt-BR translation**
   ourselves as Layer B, cross-checked against the abundant English (93.5%). The spec's implicit
   "prefer sentences that already have PT" must be relaxed to "prefer sentences with PT *or* EN; generate PT."
4. **Audio from Tatoeba is thin (2.5%)** → plan TTS as the primary audio source; treat Tatoeba audio as bonus.
5. **The ≥3 sentences/vocab and ≥5/grammar thresholds are realistic** for *Japanese supply* (85% / 100% of
   samples already clear them). The real cost driver is **pt-BR generation + true i+1 filtering**, not finding
   Japanese sentences. For the long tail (~15% of vocab, more in low-frequency N4) **AI generation** will be
   needed — the per-topic AI-generation cap must be set per-item, higher for sparse items.
6. **We currently have only 2 community level lists** (kanji + vocab); the spec requires **≥3**. P2 must add
   ≥1 more vocab list and ≥1 more kanji list before reconciling.

---

## 1. Candidate level sets (provisional, 2 lists)
| Set | Source list | Count |
|-----|-------------|------:|
| Kanji N5 | `kanji.json` `jlpt_new` (davidluzgouveia) | 79 |
| Kanji N4 | `kanji.json` `jlpt_new` | 166 |
| **Kanji N5+N4** | | **245** |
| Vocab N5 | elzup `n5.csv` | 718 |
| Vocab N4 | elzup `n4.csv` | 668 |

> These are *provisional* — single-list, so confidence is low until ≥3 lists are reconciled (P2). Community
> N5 kanji counts famously range ~78–103, so 79 is at the low end and will likely grow on reconciliation. The
> spec's §1.5 warning is confirmed in the data: this single list is not authoritative.

## 2. Dictionary completeness — Kanji (245 N5+N4)
| Property | Coverage |
|----------|---------:|
| Present in KANJIDIC2 | **245 / 245 (100%)** |
| Stroke count | 245 / 245 |
| On- *or* kun-reading | 245 / 245 |
| English meanings (→ pt-BR in Layer B) | 245 / 245 |
| KanjiVG stroke-order SVG | **245 / 245 (100%)** |
| Kradfile radical decomposition | **245 / 245 (100%)** |

**Conclusion:** the kanji layer can be built to acceptance-criterion #1 with zero source gaps. (Reference
totals: KANJIDIC2 = 10,384 chars; KanjiVG = 6,702 chars; Kradfile = 12,156 chars — all comfortably superset
the N5/N4 set, and the full Jōyō/N3–N1 range too, so the schema's level-agnostic promise is source-backed.)

## 3. Dictionary completeness — Vocab
| | N5 (718) | N4 (668) |
|--|--------:|---------:|
| Exact surface match in JMdict-common | 659 (91.8%) | 616 (92.2%) |
| …of which marked `common` | 653 | 611 |
| Recovered by reading match | +4 | +3 |
| Apparent "still missing" | 55 | 49 |

**The "missing" are not real gaps.** Inspecting them, they fall into:
- **List-formatting variants** joined with `;` in the source list — e.g. `足; 脚`, `いい; よい`,
  `やはり; やっぱり`, `川; 河`. Splitting on `;`/`/` resolves these.
- **Affixes / counters** stored without the `～` placeholder in JMdict — e.g. `～円`, `～回`, `～階`,
  `～か月`, `～個`, `～歳`, `～冊`, `～語`, `～さん`, `お～`. Stripping the tilde and looking up the base
  (円, 回, 個…) resolves these; counters get a dedicated `counter` family anyway.
- **する-compound verbs** — e.g. `コピーする`, `けんかする`, `あいさつする`, `チェックする`. JMdict stores
  the noun (+`vs` POS); map `Xする` → noun `X` + する.
- **Multi-word / grammar entries** — e.g. `～(て)しまう`, `いくら～ても`, `～ばかり`, `～だす`,
  `～続ける`. These belong to the **grammar** registry, not vocab.

**Conclusion:** with a normalization step (split variants, strip `～`, split `する`, route grammar-like
entries to the grammar registry), real JMdict coverage is **~99%+**. Acceptance criterion #2 is achievable.
Action: build `scripts/ingest/normalize_vocab.py` in P1.

## 4. Tatoeba supply — the decisive finding
Corpus probed: **248,705 Japanese sentences.**
| Metric | Count | % of JP |
|--------|------:|--------:|
| JP sentences with a **Portuguese** translation | 4,533 | **1.8%** |
| JP sentences with an **English** translation | 232,587 | **93.5%** |
| JP sentences with **audio** | 6,332 | **2.5%** |
| Cross-language links scanned | 28,193,526 | — |

**Implications:**
- **PT is not a usable selection filter.** Requiring an existing PT translation would discard ~98% of natural
  Japanese. → Policy change: select the Japanese sentence on its own merits (naturalness, in-level vocab,
  contains the target), then **author the pt-BR translation as Layer B**, validating against (a) the English
  translation when present (93.5% of the time) and (b) the JMdict/KANJIDIC2 token glosses. Existing PT, when
  it exists, becomes a free cross-check, not a prerequisite.
- **English is the reliable pivot**, exactly as the spec's §3.1 anticipated — good.
- **Audio:** Tatoeba covers only 2.5% of JP. For a speaking-focused course, audio must come primarily from
  **TTS** (the prototype already uses mp3+TTS), with Tatoeba native audio used where available and flagged.

## 5. Per-target sentence supply (does each item get enough sentences?)
Sample = 60 N5 vocab spread across the list; **substring** matching (proxy — P5 uses SudachiPy lemmas).
"Simple" = length ≤ 24 chars **and** ≤ 6 distinct kanji (a loose i+1-feasibility proxy).

| Metric (N5 vocab sample, n=60) | Value |
|--------------------------------|------:|
| Words with ≥1 sentence | 86.7% |
| Words with **≥3** sentences (the threshold) | **85.0%** |
| Words with ≥3 **simple** sentences | **85.0%** |
| Words with ≥3 sentences **that already have PT** | 48.3% |
| Median sentences per word | 116 |
| Median **simple** sentences per word | 68 |

Grammar markers (20 core particles/forms): **100%** clear ≥5 sentences, and **100%** clear ≥5 *simple*
sentences (e.g. は ≈ 154k, を ≈ 85k, て ≈ 89k, た ≈ 114k, ます ≈ 19k, たい ≈ 5.8k, なければ ≈ 2.6k).

**Reading:**
- Japanese supply is abundant and the ≥3/≥5 thresholds are realistic. The binding constraint is **PT
  availability** (only ~48% of words have ≥3 PT-bearing sentences) — reinforcing the "generate PT" decision.
- ~13–15% of sampled N5 words have <3 sentences (and the tail is worse for low-frequency N4). Those need
  **AI-generated** sentences. Recommendation: **per-item** generation backfill (generate up to the threshold
  for items below it) rather than a flat per-topic %; cap and flag all generated sentences (`ai_generated`,
  `needs_review`). Expect generation to be a **minority** for N5, **more significant** for low-freq N4.
- The "simple" proxy is generous; true i+1 (cumulative-known-set) filtering in P5 will shrink usable counts,
  so the abundant raw supply (median 68 simple/word) is healthy headroom, not slack.

## 6. Limitations of this probe (honest)
- **Substring matching** overcounts (e.g. a kana word inside a longer word) and can't do lemma-accurate counts;
  P5's SudachiPy pass will replace it. Magnitudes, not exact per-word counts, are what R3 relies on.
- **"Simple" ≠ true i+1.** Real i+1 needs the cumulative known set from the finished outline (P4); this proxy
  only shows that short, low-kanji sentences exist in quantity.
- **Level sets are single-list/provisional.** Counts (esp. 79 N5 kanji) will move on ≥3-list reconciliation.
- `お～` etc. show `n=0` because the literal tilde isn't in sentences — an artifact of probing affixes as
  surface strings, not a coverage gap.

## 7. Net verdict on the sources
The open datasets **can** deliver a paid-grade N5+N4 corpus:
- **Kanji:** fully covered. ✔
- **Vocab:** ~99% after normalization. ✔ (build normalizer)
- **Sentences (Japanese):** abundant; thresholds realistic. ✔
- **pt-BR translations:** must be **generated** (Layer B), not selected — the single biggest plan adjustment. ⚠→plan
- **Audio:** TTS-primary; Tatoeba audio is a 2.5% bonus. ⚠→plan
- **Level lists:** need ≥3 (have 2). ⚠→P2 action
