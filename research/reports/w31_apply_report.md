# W31 — sentence `register` APPLIED (A8, owner decision D7)

Run 2026-09-10, DB-writer unit. Companion to `research/reports/w31_derive_report.md`, which derived
the values and applied nothing. **Gate green** (`validate_all.py`, 64 entries / 62 hard, four of them
new here). NOT COMMITTED — this run was told to touch no git state.

The field the speaking path needed exists, is populated for all 5,889 bank sentences, is re-derived
and compared on every gate run so it cannot drift, and the filter A8 asked for is live on all three
selection surfaces. **心熱けれど肉体は弱し is out of the production prompts**, and it is out because a
rule says `archaic` is not something a learner says, not because someone listed it.

---

## 1. What landed

| # | thing | where |
|---|---|---|
| 1 | schema: nullable `register` + `register_rule` on `sentence` | `design/schema_v2.md`, migration `017_sentence_register.sql`, `scripts/export/export_corpus.py`, `contracts/sentence.schema.json` |
| 2 | 5,889 bank sentences populated, residue NULL + `needs_review` | `scripts/apply_sentence_register.py`, table `research/derived/repairs/sentence_register.json` |
| 3 | 8 grammar-registry `register` errors repaired, 5 held with reasons | `scripts/apply_grammar_register_repairs.py`, table `research/derived/repairs/grammar_register.json` |
| 4 | the derivation-equality gate | `scripts/validate/validate_sentence_register.py` (+ `sentence_register_baseline.json`) |
| 5 | the speak content filter + the owner's blocklist mechanism | `scripts/export/speak_filter.py`, `design/speak_blocklist.json` (EMPTY), both builders, `validate_speaking_path.py`, `scripts/validate/test_speak_filter.py` |
| 6 | the two W38 suite entries + W38's pending-path correction | `scripts/validate/validate_review_views.py`, `test_review_apply.py` registered, `scripts/review_apply.py` |

Manifest steps **119** (`apply_grammar_register_repairs.py`, joined the `--quick` grammar family) and
**120** (`apply_sentence_register.py`); furigana moved to 121 and the family builders to 122-124,
still last. Both tables registered in `validate_repairs_applied.py`.

---

## 2. Counts

### 2.1 Sentences by register, per level (the export, `corpus/sentences/bank.json`)

| level | neutral | polite | casual | formal | archaic | slang | vulgar | dialect | epistolary | null | total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n5 | 142 | 161 | 120 | 0 | 1 | 0 | 1 | 1 | 0 | 19 | 445 |
| n4 | 965 | 728 | 442 | 38 | 0 | 2 | 0 | 0 | 0 | 29 | 2,204 |
| n3 | 1,112 | 633 | 190 | 40 | 3 | 1 | 0 | 0 | 0 | 18 | 1,997 |
| n2 | 382 | 261 | 51 | 19 | 2 | 1 | 0 | 0 | 0 | 6 | 722 |
| n1 | 275 | 192 | 45 | 5 | 0 | 0 | 0 | 0 | 0 | 4 | 521 |
| **total** | **2,876** | **1,975** | **848** | **102** | **6** | **4** | **1** | **1** | **0** | **76** | **5,889** |

The `epistolary` zero is a **measured absence**, not an unrecordable one. That distinction is the
whole reason the value stays in the set: the filter can reject one on arrival.

**By rule:** `plain-predicate` 2,876 · `polite-predicate` 1,731 · `soft-final` 439 · `casual-marker`
351 · `polite-request` 171 · `keigo` 80 · `no-signal` 76 · `polite-request-nasai` 60 ·
`grammar-register` 58 · `written-copula` 22 · `polite-set-phrase` 10 · `bungo-inflection` 5 ·
`polite-nonfinal` 3 · `slang-lexeme` 3 · `vulgar-lexeme` 1 · `classical-final` 1 · `jmdict-slang` 1 ·
`dialect-marker` 1.

### 2.2 Residue — 76 bank sentences (1.3%)

`register: null`, rule `no-signal`, `needs_review` (already 1 on all 5,889, so no export churn).
n4 29 · n5 19 · n3 18 · n2 6 · n1 4. Ratcheted per level in
`scripts/validate/sentence_register_baseline.json`, **shrink-only**. Every one is a fragment with no
predicate on its final bunsetsu and no lexical or grammatical marker — 妹さんは元気？ · やっと！ ·
中サイズのコーヒーを一つ · 調子はどう。 This is the authoring queue and it is one batch. **Nothing was
authored here**; the residue is excluded from the speaking path rather than guessed at.

The derive report counted 75 at n5-n1 and 129 overall; both moved by one (76 / 130) because the
grammar-register repair below withdrew a wrong promotion from one sentence, which correctly became
residue.

### 2.3 W13 rows — 4,223 deferred, not lost

The table holds all 10,112 derived rows. The 5,889 with `set: "bank"` are applied; the 4,223 with
`set: "w13"` address sentences the bank does not carry yet, keyed `tatoeba-<id>` / `gen-<sha1(jp)[:12]>`
— and `sent:` + that key is the slug they will have, because the hash scheme is the one
`scripts/ingest/prepare_generated.py` already uses. The applier accepts **both key kinds** and applies
whatever resolves today, so it is already correct on the day W13 lands. In the replay gate they are a
MARKED SKIP that is asserted rather than trusted: the key must be W13-shaped, and **the moment that
slug appears in the export the row is asserted like any other**. A W13 ingest that arrives without
this table's value therefore fails the gate — which is how W13 is made to read the table instead of
re-deriving a value of its own.

### 2.4 Grammar registry — 8 repaired, 5 held

The derivation compared each sentence's derived register against the register tagged on the grammar
points it illustrates. 746 rows disagreed; **701 are not defects** (a point tagged `plain` describes
the FORM the point attaches to, not the politeness of the sentence built on it — て-form, から, なら,
ても all live inside です／ます sentences). The other 27 rows come from 13 points. The rule applied,
stated once: *`grammar_point.register` states the register the point's OWN FORMS impose; a form with
no politeness morphology imposes none, and a stylistic axis is not a politeness level.*

| key | was | now | why |
|---|---|---|---|
| `no-ga-jouzu` | `polite` | `neutral` | the form is のが上手; 4 bank sentences, all plain (マイクは日本語を話すのが上手だ) |
| `no-ga-suki` | `polite` | `neutral` | のが好き; 3 plain (ゴルフをするのが好き。) |
| `no-ga-heta` | `polite` | `neutral` | のが下手; 2, one of them casual (あいつは教えるのが下手だよ。) |
| `gp-125` | `polite` | `neutral` | ようにいのる; both sentences plain (母の病気が早く治るように祈った) |
| `hazu-da` | `polite` | `neutral` | はず + copula — the politeness is the speaker's. The tag came from the pattern being spelled ～はずです; the bank ends plain (４０近いはずだ。). Its sibling `hazu-ga-nai` was already `plain` |
| `zehi` | `polite` | `neutral` | ぜひ is an adverb (ぜひそうしよう。). Also repairs a self-contradiction: the scalar column already said `neutral` while `register_json` said `polite` |
| `gp-42` | `casual`/`colloquial` | `neutral` | けっこう — its own forms include けっこうです and all three bank sentences are polite refusals (いいえ、けっこうです。) |
| `sakki` | `casual`/`colloquial` | `neutral`/`colloquial` | さっき is a time adverb; `colloquial` is a STYLE axis (against 先ほど) and is KEPT, the politeness claim `casual` is dropped. It occurs freely in です／ます speech (私は仕事でさっきつきました。) |

**Held, with the reason recorded in the table's `held` block** — 5 points, 9 conflict rows:
`o-go` (お／ご genuinely raises register; the one conflict is お金, a lexicalisation),
`temo-ii-desu` (its own form IS てもいいです — the conflicting 遊びに行ってもいい？ is a LINK defect),
`gp-109` (forms are the plain てくれない・てもらえない; the three conflicts use てもらえますか, a form the
record does not carry — a forms/link defect), `tte` and `yo` (って and よ stay colloquial even inside a
です frame; the sentence-level field now carries the frame). **The two link/forms defects are a work
item this unit did not take** — §6.

Downstream effect, measured: the repair moved 6 sentence registers (casual 1,342 → 1,339 combined,
`grammar-register` rule 61 → 58) and produced the +1 residue. The table is applied and exported
BEFORE the derivation is re-run, because `derive_sentence_register_v2.py` reads
`corpus/grammar/*.json` — and `validate_sentence_register.py` now enforces exactly that coupling
(§4).

### 2.5 Speak items excluded by rule

| surface | before | after | note |
|---|---|---|---|
| `say_now` | 432 | 432 | 29 phrases replaced; every one of the 72 units still full at 6 |
| `production` | 213 | 213 | R44 order unchanged |
| `drills[].examples` | 765 | 753 | 251 patterns kept (was 251), 171 demoted (was 171) |

**Candidate pool:** 250 of 5,889 bank sentences excluded before selection — `formal` 102, residue 76,
rule `polite-request-nasai` 60, `archaic` 6, `slang` 4, `vulgar` 1, `dialect` 1, blocklist 0.
A further 25 were refused inside the practice builder (residue 19, `formal` 9, なさい 29 across the
two selectors).

**The A8 census closes.** It counted **645 `say_now`/`production` items, 383 of them with no register
signal at all**. Today, over the same 645:

| | neutral | polite | casual | formal | archaic | none |
|---|---|---|---|---|---|---|
| before the filter (register field only) | 276 | 258 | 91 | 15 | 2 | 3 |
| **after the filter** | **288** | **258** | **99** | **0** | **0** | **0** |

The 20 inadmissible items were replaced by admissible ones, not dropped. What left, by name:
心熱けれど肉体は弱し and 新しい市の病院を建てる計画が進行中である (health), 初めてこちらのＨＰを拝見しました
and パスポートは旅行中大切である (past_stories), five keigo utterances out of `politeness`
(キッチン用品は、地下一階でございます / 特別料理がございますが / 遠慮なく気持ちをおっしゃってください /
サラダはご自由にお召し上がりください / お名前とご住所を伺ってもよろしいでしょうか？), two 〜なさい
imperatives, and four predicate-less fragments. `politeness` still holds 41 polite and 5 neutral items
and still teaches keigo **through its grammar points**, which this filter does not touch.

### 2.6 Ratchets moved, with the cause

One cause for all three: **the content filter changed the candidate pool, so the selection moved.**
29 `say_now` phrases and 12 drill examples are different sentences, and every downstream count that
is computed from the shipped units moved with them. All three baselines re-recorded; the movement is
small and two-directional.

| ratchet | movement | note |
|---|---|---|
| `speak_strand_baseline.json` | 48 (stage, strand) ceilings re-recorded; largest single move `time_plans\|language-focused` 28.3 → 29.7 points off band, largest improvement `eating\|language-focused` 30.5 → 29.3 | 12/12 stages still out of R78's band, unchanged as a fact; `stale_histograms` 0 |
| `speak_spiral_baseline.json` | 17 floors re-recorded. **Down:** `arrival\|drills` 11 → 8, `eating\|drills` 22 → 20, `getting_around\|drills` 12 → 10, `lodging\|fluency` 2 → 1. **Up:** `shopping\|drills` 31 → 39, `getting_around\|fluency` 1 → 5, `arrival\|say_now` 0 → 1 | an inverted (floor) ratchet, so the four decreases are a real cost, stated. Net reach is up |
| `speak_duplicate_baseline.json` | `arrival` 13 → **14**, `health` 2 → 1; total 24 → 24 | the only genuine quality regression here: replacing はい、お兄ちゃん、半分こ。(residue) with 本当にありがとうございます put one more near-duplicate of an existing thanks phrase into `arrival`. `arrival`'s 13 pairs were already the G4 work list; this makes it 14 |
| `rebuild_baseline.json` (quick) | 3 of 4 hashes | `corpus/grammar/n4.json` + `n5.json` because step 119 now runs in `--quick`; `corpus/grammar/INDEX.md` for the recurring calendar reason in §6 |
| `rebuild_baseline.json` (full) | 16 of 568 held entries | the manifest gained two steps, so the FULL replay was run (README: "whenever a step is added"). It ran clean to the end — **790 files compared, 568 held, 222 byte-identical, unchanged from W27's re-record** — and 16 held entries' rebuild bytes moved: `corpus/sentences/bank.json` (the new field, so the rebuild DOES reproduce it), `corpus/grammar/n4.json` + `n5.json` (the register repairs), and 13 INDEX/manifest files for the calendar reason in §6 |

`validate_speaking_path.py` stayed green throughout (0 FAIL, the same 1 pre-existing warn about
`speak:arrival-02`'s 3-item fluency block).

---

## 3. Lessons did not move — the proof

`course/` re-exported after every change. Excluding `course/speak/` (which this unit deliberately
rebuilds), the diff against `git HEAD` is **7 files, 1 line each, and every changed line is a
generated-date stamp**:

```
$ git diff --numstat course/ | grep -v course/speak
1  1  course/INDEX.md
1  1  course/manifest.json
1  1  course/n3/INDEX.md
1  1  course/n4/INDEX.md
1  1  course/n5/INDEX.md
1  1  course/pre-n5/INDEX.md
1  1  course/vocab_disambiguation_review.json

$ git diff -- course/ ':(exclude)course/speak' | grep '^[+-]' | grep -v '^[+-][+-]' | sort -u
+  "generated": "2026-09-10",
-  "generated": "2026-09-09",
+_Generated 2026-09-10. `course/outline.json` is the machine-readable …
-_Generated 2026-09-09. `course/outline.json` is the machine-readable …
+_Gerado 2026-09-10. Colocação P4 (1ª passada) …
-_Gerado 2026-09-09. Colocação P4 (1ª passada) …
```

**0 lesson leaves changed. 0 topic files changed.** `validate_md_views.py` reports 322/322 lesson
`.md` byte-identical to a fresh render. `register` lives on sentences and is read by `course/speak/`
alone (design/schema_v2.md; A8, owner: *"yes; must not impact the lessons"*).

---

## 4. The gates

### `scripts/validate/validate_sentence_register.py` (new, hard)

**A — enum.** Every sentence carries a `register_rule` from the closed set in `design/schema_v2.md`
and a `register` that is NULL or one of the nine D7 values, and NULL holds **iff** the rule is
`no-signal`. A value with no rule, or a rule with no value, means one of the two writers ran and the
other did not.

**B — derivation.** The whole bank is re-derived with
`derive_sentence_register_v2.py --root <the tree being validated>` and every stored pair must equal
what comes back. This is the contract `validate_lesson_gating.py` check C4 puts on `needs[]`: the
field cannot drift from the rule it came from, so it can never become hand-edited data. It costs
about a second (SudachiPy over 5,889 sentences, deterministic — a re-run of the derivation moves
nothing but its own timestamp). Because the derivation reads `corpus/grammar/*.json`, this also
catches **a grammar point re-tagged without re-deriving**, which is the exact coupling §2.4 had to
sequence by hand.

**C — residue ratchet.** NULL count per level, shrink-only, `sentence_register_baseline.json`.

Floor 5,000 sentences; a bank carrying no register at all fails.

**Plant proof** on a copied tree carrying copies of the validator AND both `derive_*` scripts
(a validator left importing the real repo reads the real tree and passes falsely): **8 plants, 8
caught, control green both ways** — a casual sentence re-labelled neutral, a value outside D7, a rule
outside the enum, residue rounded up to `neutral`, a value blanked, the field dropped from every
record, the bank cut to 10, and grammar point `n3-da-mono-da` re-tagged without re-deriving. The
grammar plant is picked from the table's own `grammar-register` rows, because re-tagging a point that
decides nothing proves nothing — the first attempt at this plant used `tte` and was correctly missed.

### `scripts/validate/test_speak_filter.py` (new, hard)

20 behaviour cases over a hand-built fixture plus 5 end-to-end plants. The blocklist is tested in
every state it can be in — **absent, empty**, one entry by slug, one entry by substring, an entry
with no `why`, malformed — because the file ships empty and a mechanism that only works once someone
fills it in is not a mechanism. The end-to-end half copies `corpus/`, `course/speak`, all of
`scripts/export/` and the validator into a fixture and proves: control passes; ONE blocklist entry
naming a shipped `say_now` phrase is caught; ONE substring entry matching one is caught; control
passes again; and a shipped phrase hand-re-labelled `vulgar` is caught.

### `validate_speaking_path.py` (extended)

The filter lives in the builders and works on the candidate pool, which is where it belongs — an
excluded sentence never takes a slot. This is the other half: a gate over the SHIPPED units, on
exactly the three surfaces A8 names, so the filter cannot be bypassed by a hand edit, a stale
rebuild, or a future selector that forgets to call it. It imports the builders' own filter rather
than restating the rule.

### `validate_repairs_applied.py` (extended)

`grammar_register.json` (8 rows, exact list match on the published `register`, retired-point redirect
honoured like every other grammar handler) and `sentence_register.json` (10,112 rows: 5,889 asserted,
4,223 checked skips). Suite total **17,749 rows, 13,505 replayed clean, 4,244 checked skips, 0 FAIL**.

---

## 5. W38 — the two suite entries and the path correction

`research/reports/w38_tooling_report.md` §3 asked for both and could not register them because
`validate_all.py` was being edited by another unit at the time.

* **`test_review_apply.py` registered** — it already existed and passed. 9 cases, 0 FAIL.
* **`scripts/validate/validate_review_views.py` written and registered.** (A) every
  `research/review/<registry>/<level>.md` re-renders byte-identical; levels come from the files
  present so N4/N3 join the gate the day they are generated, while REGISTRIES come from the
  generator's own list — deriving those from the directories on disk would mean *deleting a view
  deletes the check for it*, and the first draft did exactly that and missed the plant. (B) no filled
  sheet is stranded: every `approve`/`reject` address of a sheet carrying verdicts is in the ledger
  and every `edit` address is in a table under `pending/` or `repairs/`. A blank `--template` sheet is
  not a sheet and is reported as skipped. Plant-proved on a copied tree carrying the validator and the
  whole of `scripts/` (the import chain `build_review_views → review_ledger → review_queue → …` makes
  a hand-listed closure rot): **9 plants, 9 caught**, including the two that keep the gate
  *clearable* — the same sheet PASSES once the ledger carries its verdict and the views are rebuilt,
  and the edit stops being stranded once the pending table exists.
* **The path convention moved** `research/derived/repairs/pending/` → `research/derived/pending/` in
  `scripts/review_apply.py`, `scripts/validate/test_review_apply.py` and the pt-BR teacher README.
  The replay gate owns `repairs/` and fails on any unregistered table there, so an unapplied table
  under it would have broken the suite the moment a teacher wrote one.

**Finding, on the way in:** the eight committed review views were **already stale against `git HEAD`**
before this unit touched anything — they carried build `c73aa9ed9308`. Every hash a view prints is
the ledger's live anchor, so a teacher building a sheet from one of those would have got anchors that
no longer resolve and `review_apply.py` would have refused the whole sheet. Regenerated; the new gate
is what stops it recurring. (Views must be regenerated AFTER `contracts/build_manifest.py`, because
they print the build id.)

---

## 6. Open, and not done

1. **The blocklist is empty and stays the owner's.** One candidate the register rules cannot catch,
   surfaced by this rebuild: `sent:tatoeba-74723` 「どいてください」「やんのか？あんちゃん」 now sits in
   `politeness` — it is `polite`/`polite-request` by its final bunsetsu and is a street confrontation.
   Nothing was added to the list.
2. **The residue (76) is an authoring queue** — one batch, listed in the table under `residue`.
   Excluded from the speaking path meanwhile, never defaulted.
3. **Two grammar defects this unit found and deliberately did not fix**, because they are not register
   defects: `temo-ii-desu` is tagged on 遊びに行ってもいい？ (a plain sentence under a です-form point),
   and `gp-109`'s three conflicts use てもらえますか, a polite form its `forms[]` does not carry. Both
   are link/forms work, the same class as the W08b queue.
4. **`register_signals[]`, `register_confidence`, `register_evidence`, `register_flags[]` are
   specified and NOT stored.** The derivation produces signals and a confidence and the table carries
   both per row; nothing consumes them, and an unread exported field is a contract cost with no
   reader. Marked `[design only]` in `design/schema_v2.md`; promoting one is an exporter change, not
   a re-derivation. `register_flags[]` in particular (insult / sexual / violence / stereotype /
   medical-intimate / proper-name) is the orthogonal content axis A8 also wants and is a unit of its
   own — the blocklist is the interim mechanism for it.
5. **`arrival` near-duplicates 13 → 14.** Named above; it belongs to the existing G4 work list rather
   than to this unit.
6. **A recurring gate artefact, diagnosed but not fixed here.** `validate_index_rebuildable --quick`
   fails on a calendar rollover: it pins the rebuild's date to the date stamped in the committed
   export, but `rebuild_baseline.json` stores a hash of a rebuild made on an earlier day, so every
   re-export on a new date makes `corpus/grammar/INDEX.md` "wrong" for one line of prose. STATE (an)
   already recorded this — *"only the grammar index's generated-date line moved — the validator should
   ignore that line"* — and it has now cost a second re-record. The fix is to normalise the
   `_Generated <date>` line out of the bytes compared for held files; it is a validator change with
   its own plant proof and it did not belong inside a DB-writer unit. Re-recorded meanwhile.
7. **Fable 30-row sample not drawn.** The plan row asks for one before commit; §7 below is the
   30-row read for it, and nothing here is committed.

---

## 7. Thirty-four sample sentences for a human read

Drawn with a fixed seed across every rule that fires, weighted to the big classes.

| jp | register | rule | level | slug |
|---|---|---|---|---|
| 強い風で木が倒れた | `neutral` | `plain-predicate` | n3 | `sent:gen-095fe997fb34` |
| 絵を書くのはとても面白いし、リラックスする。 | `neutral` | `plain-predicate` | n3 | `sent:tatoeba-184938` |
| 学校の入り口で会おう | `neutral` | `plain-predicate` | n5 | `sent:gen-5c864f44379e` |
| 人口は過去五年で二倍になった。 | `neutral` | `plain-predicate` | n2 | `sent:tatoeba-144217` |
| 多くの市民が会議に集まった | `neutral` | `plain-predicate` | n3 | `sent:gen-74762640fb10` |
| このノートパソコンは薄くて軽いです。 | `polite` | `polite-predicate` | n2 | `sent:tatoeba-4394082` |
| 試験に合格するといいですね | `polite` | `polite-predicate` | n3 | `sent:gen-1d5a2872c1a1` |
| 何か食べたいです | `polite` | `polite-predicate` | n5 | `sent:gen-54dd1d1ebf25` |
| となりの区まで歩いて行きました | `polite` | `polite-predicate` | n3 | `sent:gen-43cf9e17c4a0` |
| このあたりはよく知りません。 | `polite` | `polite-predicate` | n4 | `sent:tatoeba-161025` |
| 「踊りに行くの？」「もちろん！」 | `casual` | `soft-final` | n2 | `sent:tatoeba-11627604` |
| 明日も大学へ行くつもりだよ。 | `casual` | `soft-final` | n4 | `sent:tatoeba-80364` |
| 何を買ってきてほしいの？ | `casual` | `soft-final` | n4 | `sent:tatoeba-8609914` |
| 最近は仕事がなかなかないんだよ。 | `casual` | `casual-marker` | n3 | `sent:tatoeba-10808987` |
| 何考えてたっけ。 | `casual` | `casual-marker` | n4 | `sent:tatoeba-10913720` |
| 大きな怪我じゃなくてよかった | `casual` | `casual-marker` | n1 | `sent:gen-b1e5b5b52e6e` |
| 来週、ぜひ夕食をご馳走させてください。 | `polite` | `polite-request` | n4 | `sent:tatoeba-8989567` |
| 受付でお名前を書いてください | `polite` | `polite-request` | n3 | `sent:gen-23b4f904b8d2` |
| ただいま準備いたします | `formal` | `keigo` | n2 | `sent:gen-c75f0e6a75dd` |
| 番号違いにおかけになっているようですよ。 | `formal` | `keigo` | n3 | `sent:tatoeba-121168` |
| 妹さんは元気？ | `null` | `no-signal` | n4 | `sent:tatoeba-81415` |
| やっと！ | `null` | `no-signal` | n4 | `sent:tatoeba-7577179` |
| 落ちないように注意しなさい。 | `polite` | `polite-request-nasai` | n3 | `sent:tatoeba-78536` |
| ご馳走が出るからおなかをすかせておきなさい。 | `polite` | `polite-request-nasai` | n4 | `sent:tatoeba-217072` |
| 毎日れんしゅうしないと上手にならない | `casual` | `grammar-register` | n4 | `sent:gen-cee4d4243144` |
| 服は赤、ピンク、青色などであった。 | `formal` | `written-copula` | n4 | `sent:tatoeba-83890` |
| 皆さん、おはようございます | `polite` | `polite-set-phrase` | n3 | `sent:gen-c044861b9e68` |
| 心熱けれど肉体は弱し。 | `archaic` | `bungo-inflection` | n3 | `sent:tatoeba-145552` |
| スポーツをします たとえばサッカーやテニス | `polite` | `polite-nonfinal` | n4 | `sent:gen-12a28127409c` |
| 警察はそれがやばい品物なのを知ってたんだよ。 | `slang` | `slang-lexeme` | n3 | `sent:tatoeba-176220` |
| ちくしょう！わるくないなあ！ | `vulgar` | `vulgar-lexeme` | n5 | `sent:tatoeba-135763` |
| おおきに！ | `dialect` | `dialect-marker` | n5 | `sent:tatoeba-9462381` |
| さあ話したまえ。 | `archaic` | `classical-final` | n5 | `sent:tatoeba-216863` |
| 手がいっぱいできもい。 | `slang` | `jmdict-slang` | n4 | `sent:tatoeba-861186` |

Two worth a second look. 服は赤、ピンク、青色などであった。 is filed `formal` under `written-copula`,
which is the D7 table's ruling on である and the owner call this unit was told to keep — it reads as
plain narrative, and if the owner would rather `formal` meant *keigo only*, the 22 bank rows carrying
that rule move with a one-line change to the derivation. 毎日れんしゅうしないと上手にならない is the
`grammar-register` class: the predicate said nothing and the tagged point decided, at confidence 0.60
— that whole class is `needs_review` by construction and it is where §2.4's registry repairs came
from.
