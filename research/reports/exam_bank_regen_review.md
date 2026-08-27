# Exam-bank regeneration review — decision packet

> **Generated 2026-08-27. Read-only analysis; decision pending owner.**
> Nothing in the repository was modified to produce this report. The builder was copied to a scratch
> directory, its `OUT`/`ROOT` constants repointed at scratch, and run from the repo root against the
> live (repaired) `db/corpus.sqlite`. `git status --porcelain` was captured before and after the run
> and is identical. `scripts/export/build_exam_banks.py` was never executed against the repo.

Scratch artifacts (not committed):
`.../scratchpad/regen_review/` — `build_exam_banks_scratch.py` (verbatim copy, `OUT` repointed),
`regen_out/` (raw regeneration), `regen_out2/` (determinism re-run), `regen_out3/` (row-order
experiment), `regen_safe/` + `regen_fixed/` (fixed-builder prototypes), `diff1..13.py`.

---

## 1. Headline: per-bank counts, committed vs regenerated

The builder emits only the six **deterministic** families. The 22 **authored** bank files
(`paraphrase`, `usage`, `reading_comp`, `listening_*` — 891 items) are never written by it and stay
on disk untouched.

| bank | committed | regenerated | delta |
|---|---:|---:|---:|
| n5_kanji_reading | 400 | 400 | +0 |
| n5_orthography | 400 | 400 | +0 |
| n5_context_fill | 235 | 245 | **+10** |
| n5_grammar_form | 129 | 129 | +0 |
| n5_sentence_order | 273 | 276 | **+3** |
| n5_text_grammar | 33 | 37 | **+4** |
| n4_kanji_reading | 400 | 400 | +0 |
| n4_orthography | 400 | 400 | +0 |
| n4_context_fill | 368 | 386 | **+18** |
| n4_grammar_form | 299 | 300 | **+1** |
| n4_sentence_order | 300 | 300 | +0 |
| n4_text_grammar | 62 | 88 | **+26** |
| n3_kanji_reading | 400 | 400 | +0 |
| n3_orthography | 400 | 400 | +0 |
| n3_context_fill | 389 | 400 | **+11** |
| n3_grammar_form | 300 | 300 | +0 |
| n3_sentence_order | 300 | 300 | +0 |
| n3_text_grammar | 94 | 137 | **+43** |
| **deterministic total** | **5,182** | **5,298** | **+116** |
| authored (untouched) | 891 | 891 | +0 |
| **grand total** | **6,073** | **6,189** | **+116** |

`n3_context_fill` reaches the 400 cap exactly, so it is cap-bound in the regeneration; `n5`/`n4`
context_fill and every `text_grammar` bank are supply-bound, not cap-bound.

**The sentence_vocab repair worked.** The collapse the earlier audit predicted against the damaged
index (n3_context_fill 400 → 97) does not occur: n3_context_fill regenerates to a full 400.

---

## 2. Item-level diff and classification

Set arithmetic over item `id`, then a field-by-field comparison restricted to keys the builder
actually emits (comparing all committed keys would have counted every migration-added field as a
"change" — that artifact accounts for the misleading 2,656 figure a naive diff produces).

| | count |
|---|---:|
| present in both | 5,082 |
| — identical on builder-emitted keys | 4,997 |
| — content changed | **85** |
| lost (committed → absent) | **100** |
| gained (absent → regenerated) | **216** |
| **unexplained** | **0** |

### 2.1 Lost — 100 items

| n | bank | cause | class |
|---:|---|---|---|
| 62 | n3_context_fill | displaced past the 400 cap by newly eligible sentences | (b) |
| 32 | n3_context_fill | the sentence survives but a **different `vocab_id` won the `break`** | (b) |
| 4 | n3_grammar_form | `gf:n3:5121–5124`, correct `だものだ` — form no longer exists | (a) |
| 2 | n3_grammar_form | `gf:n3:5169–5170`, correct `っぱい` — form no longer exists | (a) |

The 32 flips are the sentence_vocab repair working as designed. The builder loops
`for vid in svocab[sid]` and `break`s after the first *eligible* vocab; the repair restored
lower-numbered `vocab_id`s onto those sentences, and the restored link now wins. **All 32 flips move
to a lower `vocab_id` (32 lower / 0 higher)** — the winner is simply the smallest `vocab_id` linked
to the sentence, which is an arbitrary tiebreak, not a pedagogical choice. Every one of the 32 is a
`link_rule='lemma'` row on both sides.

The 6 grammar_form losses are the August grammar-forms work. Both were malformed citations that have
since been corrected in `grammar_point.forms_json`:

- `n3-da-mono-da`: `だものだ` → now `["～(ん)だもの"]`, i.e. `(ん)だもの`
- `n3-ppai`: `っぱい` → now `["～でいっぱい"]`, i.e. `でいっぱい`

`だものだ` and `っぱい` are the **only** two `correct` values in any committed grammar_form bank that
no longer exist in the level's form pool. These 6 items are correctly dropped: they blanked a string
that was never a real grammar point.

### 2.2 Gained — 216 items

| n | cause | class |
|---:|---|---|
| **93** | the removed leak items reappearing — the builder has no guard | **(c)** |
| 84 | sentences added to the bank since the banks were last built | new corpus content |
| 33 | restored `sentence_vocab` links (21 lemma/unverified, 11 lemma/verified, 1 run/verified) | (b) |
| 6 | grammar-forms work: a corrected form now matches its sentence (`わりには` ×1, `かなあ` ×5) | (a) |

**(c) confirmed exactly.** All **93/93** items that `migrate_exam_banks_p7.py` removed into
`corpus/exam_banks/removed_items.json` come back, in the same per-file distribution
(n3_text_grammar 43, n4_text_grammar 26, n3_context_fill 11, n5_context_fill 6, n5_text_grammar 4,
n4_context_fill 2, n4_grammar_form 1). 92 return byte-identical on builder-emitted keys; the odd one
out is `tg:n4:n4-aspecto-04-01`, whose distractors shift with the grammar pool. Regenerating today
silently re-introduces every leak the migration removed.

The 84 "new sentence" gains are straightforward: the highest sentence id referenced anywhere in the
committed banks is **5,550**, while the DB now holds **5,889** sentences (346 with id > 5,550). This
also fully explains the otherwise-puzzling `n5_sentence_order +3` — `so:n5:5729`, `so:n5:5757`,
`so:n5:5829` are all sentences that did not exist at the last build, are `n5` in both
`corpus/sentences/bank.json` and the DB, and carry 8–9 `split_mode='C'` tokens. That bank is not
cap-bound (276 of 300), so nothing was displaced to make room.

### 2.3 Content changed — 85 items, all class (a)

| bank | changed | fields |
|---|---:|---|
| n3_grammar_form | 39 | `distractors` |
| n4_grammar_form | 28 | `distractors` |
| n4_text_grammar | 12 | `distractors` |
| n3_text_grammar | 6 | `distractors` (2 also `stem` + `correct`) |

Every one is downstream of the grammar-forms work changing the level's form pool. The dropped
distractors are the malformed strings that pass no longer emits — `ことはが`, `っぱい`, `だものだ`,
`まいのように`, `のようてほしい`, `よう` — and the added ones are their corrected replacements.

Two of these are outright **repairs**, not churn:

```
tg:n3:n3-estado-04-01   correct 'っぱい' -> 'っぱなし'
  old stem: ドアを開けっぱなしにするな。… (blanked っぱい out of いっぱい elsewhere in the passage)
  new stem: ドアを開け（　）にするな。…
tg:n3:n3-estado-04-02   correct 'っぱい' -> 'っぱなし'
```

The old items blanked `っぱい` out of the middle of `いっぱい`, leaving `い（　）`. The regenerated
items blank the real `っぱなし` grammar point. This is the regeneration fixing a defect the in-place
migration could not see.

### 2.4 Class (d) — nondeterminism / order-dependence: **refuted for the repaired table**

Two experiments:

1. **Run-to-run.** Built twice into separate directories: **18/18 banks byte-identical** (SHA-256).
2. **Row order.** Copied the DB, deleted and re-inserted all 41,360 `sentence_vocab` rows with the
   *same row set* but reversed intra-sentence order, re-ran the builder: **0 items changed.**

The reason is structural. `sentence_vocab` is declared `PRIMARY KEY (sentence_id, vocab_id)`, and
`EXPLAIN QUERY PLAN` shows the builder's scan resolves to
`SCAN sentence_vocab USING COVERING INDEX sqlite_autoindex_sentence_vocab_1` — the query is answered
from the PK index, so rows arrive in PK order no matter how they were inserted. The audit's
"insertion-order dependent" flag does **not** hold against the repaired table.

It is nonetheless **fragile, and should still be fixed**: the stability depends on the index covering
the query. Adding one non-PK column reverts it —
`SELECT sentence_id,vocab_id,link_rule FROM sentence_vocab` plans as a bare `SCAN sentence_vocab`.
Any future edit that reads `link_rule` or `reading_verified` in that loop silently reintroduces
order-dependence on 223 items.

### 2.5 Class (b), reading-blind links — should the builder prefer `reading_verified`?

**Yes, but it is a small and separable change.** Measured against the repaired table:

- 180 of the 1,031 regenerated context_fill items rest on a `reading_verified=0` link
  (n5 26, n4 39, n3 115).
- Of the 32 answer-word flips, **10 replace an unverified link with a verified one** and only
  **1 goes the other way** (20 stay unverified→unverified, 1 verified→verified). The repair
  therefore already improves reading fidelity on net, by accident rather than by rule.
- Adding an explicit `ORDER BY reading_verified DESC, vocab_id` preference changes the answer word on
  **35 of 1,031** context_fill items.

`reading_verified=0` means "not confirmed", not "wrong" — inflected and rendaku anchors land there
too — so this should be a *ranking preference*, never a filter. Filtering would discard 180 items for
no defect.

---

## 3. What regeneration would DESTROY

`migrate_exam_banks_p7.py` added provenance and published slugs in place. **The builder emits none of
it.** Regenerating today silently strips these fields from all 5,182 deterministic items:

| family | items | fields the builder does **not** emit |
|---|---:|---|
| `kr` (kanji_reading) | 1,200 | `vocab`, `layer`, `ai_generated`, `needs_review` |
| `or` (orthography) | 1,200 | `vocab`, `layer`, `ai_generated`, `needs_review` |
| `cf` (context_fill) | 992 | `vocab`, `layer`, `needs_review` |
| `so` (sentence_order) | 873 | `layer`, `needs_review` |
| `gf` (grammar_form) | 728 | `layer`, `needs_review` |
| `tg` (text_grammar) | 189 | `layer`, `ai_generated`, `needs_review` |

Totals lost: **`layer` on all 5,182**, **`needs_review` on all 5,182**, **`vocab` slug on 3,392**,
**`ai_generated` on 2,589**. There are no partially-populated fields — each is either emitted for a
whole family or for none of it.

Consequences: `contracts/exam_item.schema.json` provenance requirements break; the exam picker's
real-first rule loses the explicit `ai_generated` it now keys on; and 3,392 items revert to
addressing vocabulary by `vocab_id` row number, which `contracts/README.md` forbids as an address.

**Two further losses beyond item fields:**

1. **`INDEX.md` is rewritten from the builder's own prose** (44 lines → 22), discarding the
   migration's edits.
2. **`removed_items.json` gets listed as a bank.** The INDEX glob is `OUT.glob("*_*.json")`, and
   `removed_items.json` matches it. Its top level is a dict of `{why, count, items}`, so `len()`
   returns 3 and INDEX.md would gain the line ``- `removed_items.json` — 3 items``.
   `migrate_exam_banks_p7.py` explicitly skips that file; `build_exam_banks.py` does not.

---

## 4. A defect the regeneration would INTRODUCE

`form_strs()` filters citation placeholders with `"～" not in fm` — that is U+FF5E FULLWIDTH TILDE
only. The corrected grammar forms also use **U+301C WAVE DASH (`〜`)**, which the filter misses:
`lstrip("～〜")` strips both from the *start*, but a dash in the *middle* survives.

Result: `なん〜か` is emitted as a learner-visible distractor on **9 items** (n4_grammar_form 7,
n4_text_grammar 2). Zero such items exist in the committed banks. This is a new regression, created
by the interaction of the grammar-forms work with an incomplete filter.

---

## 5. Migration plan

### 5.1 Builder changes required BEFORE regenerating

| # | change | evidence | effect |
|---|---|---|---|
| **1** | **Leak guard.** For `cf` skip a candidate when `jp.count(v["hw"]) > 1`; for `gf`/`tg` select the form with `jp.count(x) == 1`. Implement `cf` as `continue` (try the next vocab), not as dropping the sentence. | EB-05; `migrate_exam_banks_p7.py` docstring §3 | blocks all 93 leak reappearances |
| **2** | **Provenance emission.** Emit `layer`, `ai_generated`, `needs_review` per family exactly as the migration derived them (`kr`/`or`/`tg` → B/false/false; `cf`/`gf`/`so` → B, `ai_generated` from the sentence, `needs_review` = that same flag). | §3 above | restores 5,182 × 2–3 fields |
| **3** | **Slug emission.** Add `vocab: <vocab:jmdict_id>` wherever `vocab_id` is written; keep `vocab_id`. | §3 above | restores 3,392 slugs |
| **4** | **`reading_verified` preference.** Order the `cf` candidate loop `reading_verified DESC, vocab_id`. Preference only — never a filter. | §2.5 | 35 items get a better-anchored answer word |
| **5** | **EB-02 okurigana-matching distractors.** Add an affix penalty to the `kanji_reading` closeness key. | EB-02 | affix-solvable items **373 → 58** of 439 |
| **6** | **EB-06 ranking fix.** Rank `orthography` on `len(hw)` (the string actually shown), not `len(kana)`, plus the same affix bonus. | EB-06 | length-delta histogram `1977/1382/207/30/4` → **`3522/60/18`** |
| **7** | **Determinism hardening.** Add an explicit `ORDER BY` to the `sentence_vocab` scan so stability does not depend on the covering index surviving future edits. | §2.4 | removes a latent 223-item hazard |
| **8** | **Wave-dash filter.** Reject U+301C in `form_strs` alongside U+FF5E. | §4 | removes the 9 `なん〜か` items |
| **9** | **INDEX glob.** Exclude `removed_items.json` from `OUT.glob("*_*.json")`, and preserve the migration's INDEX prose. | §3 | stops a phantom bank row |

A working prototype of all nine lives at `.../scratchpad/regen_review/build_fixed.py` and runs clean.
Measured against the committed banks:

| | committed | regen | lost | gained | changed | **touched** |
|---|---:|---:|---:|---:|---:|---:|
| **as-is (no fixes)** | 5,182 | 5,298 (+116) | 100 | 216 | 85 | 401 |
| **Option A** — fixes 1,2,3,4,7,8,9 | 5,182 | 5,262 (+80) | 130 | 210 | **75** | **415** |
| **Option B** — Option A + fixes 5,6 | 5,182 | 5,262 (+80) | 130 | 210 | **1,623** | **1,963** |

Quality audit of the three outputs:

| | items | EB-05 leaks | wave-dash | EB-02 affix-solvable | EB-06 length-delta | provenance |
|---|---:|---:|---:|---:|---|---|
| committed | 5,182 | 0 | 0 | 373/439 | 1977/1382/207/30/4 | complete |
| raw regen | 5,298 | **95** | **9** | 373/439 | 1977/1382/207/30/4 | **stripped** |
| fixed regen | 5,262 | **0** | **0** | **58/439** | **3522/60/18** | complete |

Note on Option B's large `changed` count: it is *entirely* `kanji_reading` + `orthography`
distractor rewrites (1,548 of the 1,623), which is precisely what fixing EB-02/EB-06 means. No stem
and no `correct` value changes in those two banks — only the wrong answers get better.

Under the fixed builder, 42 of the 93 removed ids reappear — all `tg:`, whose id is per-passage. All
42 come back with a **different, non-leaking blank target** (0 return with the leaking stem), and the
EB-05 audit over the fixed output reports **0 leaks**. That is the guard working, not failing.

### 5.2 Verification protocol

Run in order; regeneration is not accepted until all pass.

1. **Pre-flight, repo untouched.** `git status --porcelain` before and after the scratch build must be
   byte-identical. Never run the real `build_exam_banks.py` until step 7.
2. **Determinism.** Build twice into separate directories; assert all 18 banks SHA-256 identical.
   Then rebuild `sentence_vocab` in a scratch DB copy with reversed intra-sentence order and assert
   the output is unchanged.
3. **Leak gate.** `validate_exam_blank_integrity` (proposed EB-V2) over the regenerated tree —
   exactly one blank marker, and `correct` must not appear in `stem.replace(marker,"")`. Expect 0.
4. **Okurigana gate.** `validate_kanji_reading_okurigana` (EB-V3) — land advisory, confirm the count
   falls from 373 to ≤ 60, then flip hard at "≥ 2 of 3 distractors affix-compatible".
5. **Provenance gate.** Assert every item carries `source`, `layer`, `ai_generated`, `needs_review`,
   and that every item with `vocab_id` also carries `vocab`. Diff the field census against the
   committed banks: expect zero fields lost.
6. **Sufficiency.** Re-run the paper simulation: every `(level, type)` with a nonzero SECTIONS count
   must still hold ≥ 14× its paper requirement. The counts only grow here, so this should be free —
   but `n5_text_grammar` (33) and `n5_grammar_form` (129) are the thin ones to watch.
7. **Ledger reconciliation.** For every id in `removed_items.json` that reappears, assert it is
   non-leaking. Then clear the ledger, or rewrite its `why` to record that the items returned
   repaired.
8. **Existing suite.** `validate_exam_banks.py` + the 28-entry `validate_all.py` SUITE, then re-export
   `prototype/app/data/examBanks.json` and assert corpus/prototype parity item-for-item.
9. **Spot review.** The 130 lost and 210 gained items are small enough to eyeball; the 35 answer-word
   changes from fix 4 and the 2 `っぱなし` repairs deserve a teacher's eye specifically.

---

## 6. Recommendation

**NO-GO on regenerating as the builder stands today.** It is not a close call: the run strips
provenance from all 5,182 deterministic items, drops 3,392 vocab slugs, re-introduces all 93 answer
leaks the migration removed, and adds 9 new items with a citation placeholder printed as a
distractor. Every one of those is a regression against the committed tree.

**GO after the nine builder changes in §5.1, on Option B.** The regeneration's own content changes
are overwhelmingly *good news*: the sentence_vocab repair is confirmed working (n3_context_fill
restores to a full 400, not 97), the grammar-forms work removes two malformed forms and repairs two
`っぱなし` items the in-place migration could not reach, and 84 genuinely new sentences enter the
pool. Every single difference is accounted for — **0 unexplained**.

Option B over Option A: EB-02 and EB-06 are *entirely unaffected* by regeneration on its own
(373/439 and the identical length histogram survive untouched, since `kanji_reading` and
`orthography` derive from vocab alone, which did not change). They will never be fixed by data
movement — only by the ranking change. Since a regeneration is being paid for anyway, folding in
fixes 5 and 6 closes both known solvability defects at the cost of rewriting distractors on ~1,548
`kr`/`or` items, with no stem and no answer altered. Doing it later means paying for a second full
bank churn.

**Expected diff after the fixes (Option B):** 5,182 → 5,262 items (**+80**); 130 lost, 210 gained,
1,623 changed — **1,963 of 5,182 items touched (38%)**, of which 1,548 are `kr`/`or` distractor-only
rewrites. Net learner-visible improvement: 93 answer leaks stay gone, 315 fewer affix-solvable
kanji-reading items, orthography distractors go from 55% length-mismatched to 2%, and 9 placeholder
distractors never ship.

**Sequencing.** Land the builder changes and the four validators first, with EB-V3 advisory; confirm
the scratch build passes §5.2 steps 1–6; then regenerate, re-export the prototype bank, and commit
the builder change and the regenerated data as one atomic unit so the diff is reviewable against a
single before/after.
