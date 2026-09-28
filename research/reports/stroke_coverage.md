# Stroke coverage for kana and kanji (D9 follow-up)

_Unit `stroke_coverage`, 2026-09-27. Measured on git HEAD `529131bf` (tracked JSON read with `git show`), with the
raw datasets already on disk under `research/datasets/` (KanjiVG r20250816, Kanji alive fetched 2026-06-26,
GlyphWiki dump 2026-07-04, strokesvg 2026-06-26). Read-only: no repo code or data was changed. The per-kanji work
table is `research/derived/pending/stroke_coverage.json`. The measurement scripts are in the session scratchpad
(`res0927/stroke_coverage/`: `measure.py`, `ka_trunc.py`, `ka_voter.py`, `extra.py`, `build_pending.py`)._

## 1. Answer

- **Kana: done.** All 211 registry kana (hiragana and katakana, including dakuten, handakuten, yoon, sokuon and ー)
  have a stroke record: 228 rows, of which 160 come from strokesvg and 68 are derived composites. Every strokesvg
  kana that KanjiVG also has (158) matches KanjiVG's stroke count and stroke order, with no strokes drawn backwards.
  What's left is the 17 orphan rows (small ぁ…ョ and ヴ) that have strokes but no registry record. The G14 note
  in `exemptions.json` saying "66 kana carry no stroke data" is out of date: the yoon composites filled that gap.
- **Kanji: every course kanji has some stroke data, but much of it is broken.** All 634 kanji the course unlocks
  (N5 103, N4 187, N3 344 by lesson level) have a Kanji alive outline record, and 627 have a GlyphWiki centreline
  record. KanjiVG covers all 2,131 registry kanji and agrees with KANJIDIC on the stroke count of every course
  kanji. The problems are quality, not coverage:
  1. **The Kanji alive ingest drops ink (new finding, Layer-A defect).** `scripts/ingest/kanjialive_strokes.py`
     keeps only the first `<path>` of each step SVG. Each step SVG has one `<path>` per disconnected blob of ink.
     So **1,141 of the 1,233 shipped records have truncated steps, and in 1,065 the final drawing is incomplete**.
     That includes 570 of the 634 course kanji. Example: 安's six steps ship as 宀 only, and 女 never appears.
     A JSON-only check catches most of these, since 1,098 records contain two identical consecutive steps.
  2. **GlyphWiki's stroke order is wrong for about a quarter of the course kanji.** KAGE line order is the order of
     the glyph's parts, not the order a person writes them in, but the ingest assumes the two are the same
     ("Stroke order = line order"). Checked against KanjiVG, **151 of 627 course kanji (24%)** have a different
     order. Examples: 国 closes the box before drawing 玉, 八 draws ㇏ before ノ, 安 draws 一 before く/ノ, and every
     辶 kanji (道 週 進 運 送 近) draws 辶 first. Across the whole registry the figure is 601 of 2,089. Six course
     kanji also have strokes drawn backwards (飯 漢 法 限 渡 盗).
  3. **The stroke-count gate lets bad segmentation through.** In 好, GlyphWiki splits the く of 女 into two
     strokes and drops the ㇇ of 子. The total is still 6, so the record passes the count gate.
  4. **7 course kanji have no centreline** (建 質 銀 庭 御 段 解). This is G12, and its exemption is still open.
     GlyphWiki has glyphs for all seven, but they fail the count gate. 建 would also come out in the wrong order,
     because KAGE draws 廴 first.
- **Recommendation.** Keep the shipped stroke data fully permissive, as owner ruling D-LIC-1 requires, and use
  KanjiVG only as an audit oracle that never ships. The fix is in five steps, cheapest first:
  (1) re-ingest Kanji alive with every path kept;
  (2) re-sequence GlyphWiki strokes where KanjiVG and Kanji alive agree on the fix, and adjudicate the rest;
  (3) write centrelines for the 7 gaps from Kanji alive per-stroke masks;
  (4) emit kanji records in the **same shape as `kana.json`** (`strokes` = centrelines, `shadows` = per-stroke
  outlines);
  (5) gate it all with a JSON-only validator plus a slow audit stamped with content hashes.
  Once this is done, course kanji reach 634/634 with order checked against two independent sources.

## 2. What exists on HEAD

| File(s) | Content | Source / licence | Records |
|---|---|---|---:|
| `corpus/strokes/kana.json` | per-stroke centreline `strokes[]` + per-stroke outline `shadows[][]`, `viewbox` 1024 | strokesvg (Klee One) OFL-1.1 + MIT | 228 |
| `corpus/strokes/n1..n5.json` (`stroke_order`) | cumulative filled outline `steps[k]` after k+1 strokes | Kanji alive CC BY 4.0 | 1,233 |
| `corpus/strokes/lines_n1..n5.json` (`stroke_lines`) | per-stroke centreline `strokes[]`, implicit 0..200 box, no viewbox field | GlyphWiki (free) | 2,098 |
| `corpus/kanji/*.json` `kanjivg_ref` | the codepoint in hex, not KanjiVG content (W42) | n/a | 2,131 |
| `research/datasets/kanjivg/kanjivg-20250816.xml.gz` | **raw KanjiVG XML is present** (git-ignored, not shipped) | CC BY-SA 3.0 | 6,702 entries (6,424 CJK, 184 kana) |

(`corpus/strokes/INDEX.md` calls `kana.json` "228 kanji". The generator wording is wrong but the counts are right.)

### Coverage by registry level (kanji)

| level | kanji | Kanji alive outline | GlyphWiki centreline | neither | KanjiVG | GW order = KanjiVG / compared |
|---|---:|---:|---:|---:|---:|---:|
| N5 | 103 | 103 | 103 | 0 | 103 | 91 / 103 |
| N4 | 177 | 177 | 174 | 0 | 177 | 132 / 174 |
| N3 | 350 | 350 | 346 | 0 | 350 | 251 / 346 |
| N2 | 368 | 357 | 365 | 0 | 368 | 267 / 365 |
| N1 | 1,133 | 246 | 1,110 | **18** | 1,133 | 747 / 1,101 |
| **course (634)** | 634 | **634** | 627 | 0 | 634 | **476 / 627** |
| **registry** | 2,131 | 1,233 | 2,098 | 18 | 2,131 | 1,488 / 2,089 |

Stroke counts: KanjiVG equals KANJIDIC for all 634 course kanji and for 2,122 of the 2,131 registry kanji. The 9
differences are all N1 kanji whose shape changed in 2010 (葛 賭 謎 牙 餅 餌 僅 遡 遜), where KANJIDIC counts the older
form. Kanji alive's count differs from KANJIDIC only for 極 and 離, the two G13 exemptions. The 18 N1 kanji with no
data at all are listed in the pending table. N1 is not supported now (D1), and the table only records them.

## 3. Method and how far to trust it

- **GlyphWiki vs KanjiVG order.** Both sets of strokes are normalised to a unit box. The cost of matching a
  GlyphWiki stroke to a KanjiVG stroke is the start-point distance plus the end-point distance, taking the lower of
  the forward and reversed readings. The Hungarian assignment then gives a permutation, and a record "differs" when
  that permutation is not the identity. **Control:** the same comparator run on the 158 strokesvg kana reports
  158/158 identical and 0 reversed, so it does not produce false positives on clean data. Three course kanji were
  checked by hand (八 国 安) and all three are real order errors. The mean endpoint cost mostly measures proportion
  (GlyphWiki glyphs fill the box, KanjiVG leaves a margin), so it is **not** a segmentation detector on its own. The
  production audit should normalise each glyph to its bounding box first.
- **Kanji alive as a second, permissive order source (probe).** Rasterise the full cumulative steps, label each
  pixel with the step that first inked it, place the GlyphWiki centrelines on that ink, and assign each centreline
  to a labelled stroke (Hungarian). Alignment in this probe was a crude bounding-box fit, and its limits are
  visible: the median share of centreline samples that land on ink was 0.51. Even so, the Kanji alive vote equals
  KanjiVG's permutation for **413 of 627** course kanji, and for **81/81** of the votes made with confidence ≥ 0.2.
  Of the 151 kanji where GlyphWiki's order differs, Kanji alive independently reproduces KanjiVG's exact fix for
  **87**. It sides with GlyphWiki for only 3 (判 疑 状), and those need adjudication. Better per-stroke registration
  is needed before Kanji alive can serve as a gate. It already works as a second vote.
- **Why two voters.** Japan's only official stroke-order reference, the Ministry of Education's 1958 *Hitsujun
  shidō no tebiki*, covers the 881 education kanji of its time and has not been cited in textbook standards since
  1977 ([Wikipedia: Stroke order](https://en.wikipedia.org/wiki/Stroke_order), read 2026-09-27;
  [NDL record](https://ndlsearch.ndl.go.jp/en/books/R100000002-I000000984674)). Beyond that list, stroke order is a
  convention that different sources resolve differently. A 2-of-3 vote (GlyphWiki, Kanji alive, KanjiVG) with
  owner adjudication of the remainder is how the error margin stays small without a human pass on all 634 kanji.

## 4. Licences

| Source | Licence | What it permits for a paid app | Status here |
|---|---|---|---|
| **KanjiVG** | CC BY-SA 3.0, © Ulrich Apel ([repo](https://github.com/KanjiVG/kanjivg), read 2026-09-27) | Shipping its stroke paths, or anything adapted from them, counts as an **Adaptation**. §4(b) then requires the adapted stroke file to be distributed under BY-SA 3.0 or a compatible later version, with the licence URI included, and with nothing that restricts recipients' rights ([legal code](https://creativecommons.org/licenses/by-sa/3.0/legalcode), read 2026-09-27). The app code and courseware would sit next to it as a separate work, not an Adaptation, but the **stroke data file itself would have to stay openly re-licensable**. BY-SA 3.0 says nothing explicit about sui generis database rights. | **Rejected as a shipped source** by owner ruling D-LIC-1 (2026-06-26, `design/license_audit.md`). Allowed use here: an audit oracle whose output is only a verdict. |
| **Kanji alive** | CC BY 4.0 (archived `research/datasets/kanjialive/LICENSE.md`) | Commercial use and adaptation allowed. Requires attribution and a note that changes were made. No share-alike. | Already shipped (1,233). Stays the order-correct, hand-drawn base. |
| **GlyphWiki** | "Unlimited permission … commercially or non-commercially" (bundled `LICENSE.txt`) | Anything. | Already shipped (2,098 centrelines). |
| **strokesvg / Klee One** | OFL 1.1 + MIT | Bundling allowed. OFL §2 requires the full licence text and the copyright lines (W42 finding). | Kana, done. |

**Using KanjiVG as an audit oracle.** The proposed use takes only a *verdict* from KanjiVG ("GlyphWiki stroke i is
written as stroke j" / "agrees") and stores its hash. The permutation that gets applied is also produced by Kanji
alive, which is permissive, whenever the two agree. The shipped geometry then comes entirely from GlyphWiki and
Kanji alive. D-LIC-1 already treats stroke count and the `kanjivg_ref` id as facts that can be kept with credit, and
stroke order belongs in the same category of fact. **The owner should confirm** that KanjiVG verdicts may decide the
64 kanji where Kanji alive is inconclusive. If not, those 64 go to human adjudication instead (§5, step 2).

## 5. Proposed ingest to reach 100% of course kanji in the `kana.json` shape

**Target record** (new `corpus/strokes/kanji_<level>.json`, same properties as `stroke_kana`, with `kind` widened to
`"kanji"` as a curated vocabulary edit in `build_schemas.py`):

```json
{"char": "安", "kind": "kanji", "viewbox": "0 0 1024 1024",
 "strokes": ["M… (centreline, pen direction, writing order)", "…"],
 "shadows": [["M… (outline of stroke 1 only)"], ["…"]],
 "source": "glyphwiki+kanjialive", "license": "GlyphWiki-free AND CC-BY-4.0",
 "order_check": {"voters": ["kanjialive", "kanjivg"], "verdict": "agree", "content_sha256": "…"}}
```

`strokes` gives the pen and ball animation, and `shadows` gives the clip and trace guide, exactly as for kana. The
cumulative `steps` view becomes derivable as the union of `shadows[0..k]`, and the centreline files become redundant.
Both old files can retire once the new ones are in parity, which removes the coordinate-frame mismatch between them.

Steps, cheapest and highest-value first:

1. **Fix the Kanji alive ingest (a one-line root cause).** In `kanjialive_strokes.py`, replace
   `PATH_RE.search(svg)` with all `PATH_RE.findall(svg)` joined together. Re-export and delete the
   identical-consecutive-steps pattern. This repairs 1,141 records, 570 of them course kanji. It stands alone and
   should ship before anything else.
2. **Correct the GlyphWiki order.** Apply the consensus permutation to the centrelines in 87 course kanji where
   Kanji alive and KanjiVG agree. Flip direction where KanjiVG reads the stroke reversed (6 course kanji; check
   each, because a flip on a hooked stroke is not always correct). Adjudicate the 64 remaining disagreements in a
   short owner/reviewer queue with an overlay image per kanji. After better registration, most of them should
   resolve to a 2-of-3 vote.
3. **Fill the 7 gaps (and anything quarantined) from Kanji alive.** Label each stroke's pixels from the fixed
   steps, fill the gaps a later stroke leaves where it crosses an earlier one, skeletonise (Zhang-Suen in numpy,
   or `cv2.ximgproc` if available), and orient each stroke by the KanjiVG start-point verdict. This is CC BY 4.0
   only, so there is no licence question. It also covers kanji that fail geometry checks, such as 好.
4. **Shadows.** Build per-stroke outlines from the same Kanji alive label map with `cv2.findContours`. Register
   the GlyphWiki centrelines into the Kanji alive frame with a per-kanji affine fit that maximises the share of
   centreline samples on the stroke's own shadow, then scale both to a 1024 viewbox, matching kana.
5. **Exemptions shrink.** G12 (7 entries) and G13 (極 離; KanjiVG and GlyphWiki both side with KANJIDIC) close in
   the same commit that lands the data, as `exemptions.json` requires.

Dependencies already installed in the system `python` (3.13): numpy, scipy, cv2, PIL. Nothing new is needed.
Scale: roughly one unit for steps 1 and 5, one for steps 2 and 4, and one for step 3 plus the adjudication queue.

## 6. Proposed validator

**Fast gate** (extend `scripts/validate/validate_stroke_integrity.py`; reads JSON only, no raw datasets, so it
runs in CI):

- **S1 coverage.** Every kanji in any lesson's `unlocks` of type `kanji` has a `kanji_<level>` record, and so does
  every kana in the registry. Exemptions need a reason and fail once they match nothing (current rule).
- **S2 counts.** `len(strokes) == len(shadows) == kanji.strokes` (KANJIDIC).
- **S3 steps grow.** In any cumulative representation, step k is not equal to step k−1 and inks at least as much.
  This rule would have caught the truncation bug.
- **S4 geometry.** Rasterise each record (cv2). At least 90% of the samples on centreline i must fall inside
  shadow i. This catches segmentation errors like 好 and moves the "centreline inside its clip" check out of the
  manual browser pass. Also require no empty shadow except dots, and coordinates inside the viewbox.
- **S5 order stamp.** Each record's `order_check.content_sha256` equals the sha256 of its current
  `strokes` + `shadows`, and `verdict ∈ {agree, adjudicated}`. A stale or missing stamp fails. This is the same
  pattern as `review_ledger`.
- **S6 kana orphans.** Each of the 17 orphan rows is either registered or dropped. The G14 exemption text is
  updated to match the data.

**Slow audit** (new `scripts/audit/audit_stroke_order.py`; needs `research/datasets/`; run after any stroke
ingest): re-derive the Kanji alive vote and the KanjiVG verdict per kanji, using bounding-box-normalised endpoints
and Hungarian assignment. Write `research/derived/stroke_order_audit.json` containing only verdicts and hashes,
never KanjiVG coordinates. The fast gate's S5 reads the hashes from that file. Include a plant test that
mis-orders one kanji (swap two strokes of 八) and reverses one stroke, and check that both fail. Per the
validator plant-proof note, the validator runs from inside the fixture tree.

## 7. Open points for the owner

1. Confirm that KanjiVG may be used as a **non-shipped audit oracle** whose order verdicts can settle
   disagreements (§4). The alternative is human adjudication of up to 64 course kanji.
2. Confirm the retirement plan: once parity is reached, the new `kanji_<level>.json` files replace `n*.json` and
   `lines_*.json`.
3. Decide the 17 kana orphans: register the small kana and ヴ (recommended, since they occur in real text, e.g.
   ティ, ヴァ), or drop the rows.

## Sources

- KanjiVG repository and licence statement: https://github.com/KanjiVG/kanjivg (read 2026-09-27)
- CC BY-SA 3.0 Unported legal code: https://creativecommons.org/licenses/by-sa/3.0/legalcode (read 2026-09-27)
- Kanji alive licence, archived: `research/datasets/kanjialive/LICENSE.md` (SHA in `design/sources.md`); upstream
  https://github.com/kanjialive/kanji-data-media
- GlyphWiki licence, bundled: `research/datasets/glyphwiki/LICENSE.txt`; https://glyphwiki.org/dump.tar.gz
- Stroke-order standard: https://en.wikipedia.org/wiki/Stroke_order and
  https://ndlsearch.ndl.go.jp/en/books/R100000002-I000000984674 (read 2026-09-27)
- Owner rulings D-LIC-1/2: `design/license_audit.md`; W42 evidence: `research/reports/w42_attribution_report.md`
