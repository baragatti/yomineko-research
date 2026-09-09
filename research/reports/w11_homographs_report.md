# W11a — A6 homographs: rulings, resolver rule, placements

**Unit:** APP_PLAN §6 step 1, first half. **Decision source:**
[`homograph_recommendations.md`](homograph_recommendations.md) (advisory doc, approved by the owner
2026-09-09, "yes to both"). **Gate: green** — `validate_all.py` exit 0, all hard validators pass.

Everything below is re-provable from tracked artifacts:
`research/derived/repairs/homograph_rulings.json` (27 rows, replayed against the export by
`validate_repairs_applied.py` on every run) and `scripts/apply_homograph_rulings.py` (idempotent).

---

## 1. What changed, in one table

| | before | after |
|---|---:|---:|
| `course/vocab_disambiguation_review.json` rows awaiting a teacher | 14 | **0** |
| body refs pointing at the wrong homograph, **of the four the owner enumerated** | 4 | **0** |
| the fifth wrong ref (§7.2, `les:n4-passiva-02` 様), out of scope here | 1 | 1 — **closed in W11c**, see `w11_fixup_report.md` §3 |
| `course/coverage_exemptions.json` vocab exemptions | 9 | **4** |
| `course/gating_exemptions.json` body-ref exemptions | 8 | **4** |
| lessons whose unlock ledger gained a record | — | 5 |
| lesson bodies whose rendered prose changed | — | 5 |
| exercises added (so no promoted unlock is undrilled) | — | 4 |
| practice-coverage debt (`absent`, all levels) | 2,937 | **2,937** = the frozen baseline, unmoved |

(The debt row said `2,941 -> 2,937`. 2,941 was a MID-UNIT number — the count after the five unlocks were promoted and before the four exercises were authored. The before column is the frozen baseline, **2,937**, and the honest statement is that the unit put it back where it found it. Corrected in W11c.)

Rendered diff over all 322 lessons — chips resolved to the kana the app actually prints, not a byte
diff of the JSON: **5 body-ref sets, 5 unlock sets, 5 SRS card sets, 4 added exercises** changed, in
8 lessons total (the 5 with a chip change plus the 4 that gained an exercise node, overlapping in
one). `cumulative_known_set` moved in 254 lessons and every single change is an ADDITION — no lesson
lost anything, checked mechanically over all 254. Nothing else in `course/` moved.

---

## 2. The four wrong refs (task 1)

All four were body-display refs, so no gating was ever affected; the learner simply saw a card whose
reading and gloss contradicted the sentence printed beside it. The rendered diff, chip text as the
app prints it (`v.kana`):

```
les:n3-conjectura-03   - «ひん» (しな) = "artigo, mercadoria"
                       + «しな» (しな) = "artigo, mercadoria"
les:n3-deveres-03      - «かね» (きん) = 'ouro (metal)'
                       + «きん» (きん) = 'ouro (metal)'
les:n3-intencao-03     - «え»  (がら): "estampa, padrão"
                       + «がら» (がら): "estampa, padrão"
les:n3-relato-04       - «かみ» (じょう) = "do ponto de vista de, em termos de"
                       + «じょう» (じょう) = "do ponto de vista de, em termos de"
```

None of the four needed a data edit: the resolver rule (§4) now reads the reading the lesson prints
and lands on the right record at export time. Two of them had been labelled *settled by frequency*
in the review file — the bank counts 作品/製品/商品 for 品 and お金 for 金, neither of which is the
word the lesson was teaching. **The `frequency` label meant less settled, not more.**

---

## 3. The fourteen rulings (task 2)

Every row of `vocab_disambiguation_review.json` is now decided and recorded with its evidence in
`homograph_rulings.json` (`kind: "ref"`). Seven carry a printed reading and are DERIVED by the
resolver; seven print none and are loaded from the table as an explicit ruling.

| # | headword | lesson | ruling | how | evidence in one line |
|--:|---|---|---|---|---|
| 1 | 上 | `les:n3-perspectiva-01` | keep `vocab:1352150` かみ | ruling | glossed "curso superior de um rio" — a sense only かみ has |
| 2 | 上 | `les:n3-relato-04` | **→ `vocab:1352170` じょう** | reading | prints `<jp>じょう</jp>`, suffix gloss, 法律上 |
| 3 | 何方 | `les:n5-passado-05` | keep `vocab:1189360` どちら | ruling | head gloss is どちら's; どなた now has its own chip and card (§5) |
| 4 | 得る | `les:n3-perspectiva-01` | keep `vocab:1454500` うる | ruling | prose names both readings; the introducing lesson writes prose for うる only |
| 5 | 得る | `les:n3-perspectiva-02` | keep `vocab:1454500` うる | ruling | same pair, resolved the same way on purpose |
| 6 | 数 | `les:n3-estado-03` | keep `vocab:1580820` かず | reading | prints `<jp>かず</jp>`; sits where かず sorts, not すう |
| 7 | 柄 | `les:n3-intencao-03` | **→ `vocab:1508300` がら** | reading | prints `<jp>がら</jp>` + "estampa, padrão" |
| 8 | 柄 | `les:n3-perspectiva-02` | keep `vocab:1508290` え | ruling | "cabo, punho" is え's only sense |
| 9 | 注ぐ | `les:n3-desejos-05` | keep `vocab:1581730` そそぐ | ruling | reading printed as plain text, not `<jp>` — see §4 |
| 10 | 額 | `les:n3-estado-01` | keep `vocab:1207500` がく | reading | prints `<jp>がく</jp>` inside a がく homophone drill |
| 11 | 品 | `les:n3-conjectura-03` | **→ `vocab:1583470` しな** | reading | prints `<jp>しな</jp>` + "artigo, mercadoria" |
| 12 | 後 | `les:n3-limites-04` | keep `vocab:2147630` ご | ruling | verbatim echo of the introducing lesson; sits in the こ/ご slot |
| 13 | 金 | `les:n3-deveres-03` | **→ `vocab:1242600` きん** | reading | prints `<jp>きん</jp>` + 'ouro (metal)' |
| 14 | 金 | `les:n3-estado-04` | keep `vocab:1242590` かね | reading | prints `<jp>かね</jp>` + "dinheiro" |

Rows 7/8 and 13/14 disagree **deliberately** — the course teaches both readings of 柄 and of 金, in
different lessons, and neither pair should ever be "fixed" to agree.

Rows 4 and 5 are the two `probable` ones and they carry a live curriculum question, recorded in the
table rather than silently closed: **える is unlocked at `les:n3-conectores-05` and taught nowhere.**
If the teacher decides the everyday える should own the 得る card, both rows flip together.

---

## 4. The resolver rule (task 3)

**Where a lesson prints `<jp>かな</jp>` immediately after a `<vocab ref>` chip, that kana is the
lesson's own statement of which record it means, and it wins.**

- Code: `scripts/export/vocab_identity.py` — new `reading` tier. Full order is now
  `unique → ruling → reading → sibling filter → level → introducing topic → frequency → unresolved`.
- Extractor: `_READING_HINT` in `scripts/export/export_course.py`. Chip, then at most one
  punctuation-only `<text>` node, then a **bare** `<jp>` whose content is kana. It is keyed by the
  offset of the ref attribute, so a hint can never drift onto a neighbouring occurrence.
- Test: `scripts/validate/test_vocab_identity_reading.py`, 13 checks, in `validate_all.py`.
- Docs: `design/lesson_schema.md` § *Which record an ambiguous `vocab:<headword>` means* — the doc
  that owns lesson refs.

**Measured before it was written**, over all 322 lesson bodies: 643 chips carry such an annotation,
17 of them on an ambiguous headword, 16 identify exactly one record, **12 confirm the previous pick
and 4 contradict it** — and the 4 are exactly the 4 known-wrong refs. Zero unintended changes.

Three properties are load-bearing and each is a test:

- **Per occurrence, ahead of the per-(headword, lesson) cache.** 柄 is え in one lesson and がら in
  another and may be both inside one body.
- **Abstains unless exactly one candidate reads that way.** 位 names three records, two of which
  read くらい; the rule must not pick the lower JMdict entry and call it evidence.
- **A ruling that contradicts a printed reading is a hard error**, never a silent override.

The rule stays load-bearing rather than decorative: `apply_homograph_rulings.py` re-resolves every
`reading` row **with the ruling table switched off** and fails if the rule alone no longer produces
it. A table that quietly covered for a broken rule would be a lookup table wearing a rule's costume.

**What the rule cannot see, stated honestly.** Row 9 (注ぐ) prints its reading as plain text —
`(そそぐ)` — not inside `<jp>`, so the rule abstains and the row is an explicit ruling. Widening the
extractor to bare parenthesised kana was NOT done: `<text>` nodes carry prose, and matching kana
inside prose would start reading glosses as readings. Also measured: loosening `<jp>` to `<jp …>`
produces zero extra hits on an ambiguous headword today, so refusing attributes is a margin, not a
live constraint — recorded in the test's docstring rather than claimed as a check.

### Plant proof (copied tree, 2026-09-09)

`scripts/{validate,export,ingest,dbtarget.py}` + `design/unlock_enums.json` +
`research/derived/repairs/` copied to a fixture; `--root` pointed at the copy. Control: 13 PASS.

| plant | caught |
|---|---|
| A — reading tier disabled (`if by_reading:` → `if False:`) | 4 FAIL (1, 1b, 5, 5b) |
| B — uniqueness guard removed (`len(hit) == 1` → `hit`) | 1 FAIL (3 abstain-on-ambiguous-reading) |
| C — decision cache consulted before the ruling/reading tiers | 1 FAIL (5b reading-beats-the-cache) |
| D — contradiction guard removed | 1 FAIL (7 contradicting-ruling-is-loud) |
| E — `<jp>` loosened to `<jp[^>]*>` | **not caught**, and documented: the kana-only content class already refuses 法律上, and the loosening changes no resolution on today's corpus |

Plant C is why check 5b exists: check 5 alone passes under it, because nothing has cached anything
yet when it runs.

The new `homograph_rulings.json` handler inside `validate_repairs_applied.py` was plant-proved
separately on a full copied tree (corpus/ + course/ + scripts/ + repairs/), six plants, six caught,
each on the right row: a reverted body ref, a removed unlock, a promoted record put back into
`coverage_exemptions.json`, a `hold` that quietly gained an unlock, a practice exercise whose answer
stopped containing its record's surface, and a practice exercise the body stopped rendering.

---

## 5. The nine exemptions (task 4)

**Five promoted to real unlocks.** Each was already taught in its lesson's own body; only the ledger
did not know, which is why four of them also needed a `gating_exemptions.json` entry to stop the
gate failing on a chip pointing outside its own `cumulative_known_set`.

| record | lesson | ref written | what else changed |
|---|---|---|---|
| `vocab:1189370` 何方 どなた | `les:n5-passado-05` | `vocab:449` (row id) | one sentence re-cut so どなた gets its own chip |
| `vocab:1310670` 止める とめる | `les:n4-condicionais-01` | `vocab:止める` | chip already there (the たら list conjugates 止めたら) |
| `vocab:1403830` 側 そば | `les:n5-particulas-lugar-02` | `vocab:側` | chip already there |
| `vocab:1423310` 中 なか | `les:n5-comparacoes-02` | `vocab:中` | chip already there (it IS the 〜の中で pattern) |
| `vocab:2846738` 何 なん | `les:n5-conectando-01` | `vocab:何` | chip already there |

Only `les:n5-passado-05` needed a row-id ref: it is the one lesson that must unlock **both** siblings
of one headword, which a headword ref cannot express. It is also the only prose edit in the unit:

```
- «どちら»: qual direção, para onde; é também a forma educada de 'qual (dos dois)' e até de
  'quem'. Lido como どなた, vira uma maneira polida de perguntar 'quem é?'.
+ «どちら»: qual direção, para onde; é também a forma educada de 'qual (dos dois)'. «どなた», o
  mesmo kanji lido de outro jeito, é a maneira polida de perguntar 'quem é?'.
```

Adding that row-id unlock also lets the resolver's sibling filter settle the どちら chip beside it on
evidence instead of on a tie-break.

**Four held, with the reason restated.** 君/くん (placement + a line of prose), 様/よう (waiting on a
policy about formal nouns delivered as grammar), 年/ねん (must be taught; which lesson is undecided),
背/せ (the honest fix is probably to repoint the せい card instead). Their reasons all pointed the
reader at `vocab_disambiguation_review.json` — which this unit empties — so the prose in **both**
exemption files was rewritten from the ruling table, and the apply script rewrites it on every run so
the two cannot drift. Each hold is now an assertion the gate re-proves: still exempt, still unlocked
by nothing.

---

## 6. The four exercises, and why they were not optional

Promoting five unlocks grew `validate_practice_coverage`'s frozen debt by four — (n5, vocab)
535 → 538, (n4, vocab) 591 → 592 — and that ratchet fails on growth for a stated reason: *an unlock
that gains no question is a card the SRS schedules and the lesson never rehearsed.* Raising the
ceiling is exactly what its own header forbids. So each promoted record that its lesson did not
already drill got one exercise, authored from the lesson's own frame and vocabulary, tracked as
`kind: "practice"` rows in the ruling table (the table holds the content; the apply script only
places it) and asserted by `validate_repairs_applied.py`:

| lesson | exercise | type | drills |
|---|---|---|---|
| `les:n5-particulas-lugar-02` | `ex:n5-particulas-lugar-02-6` | production | 私の側に犬がいる。(そば) |
| `les:n5-passado-05` | `ex:n5-passado-05-7` | cloze | ＿＿ですか。→ どなた |
| `les:n5-conectando-01` | `ex:n5-conectando-01-6` | cloze | ＿＿で来なかったの？ → 何 (なんで, the question から answers) |
| `les:n4-condicionais-01` | `ex:n4-condicionais-01-6` | recognition | 止めたら ← 止める, against 止まる / 止む |

`vocab:1423310` 中/なか needed none: `les:n5-comparacoes-02` already drills it through 〜の中で.
Debt is back at the baseline exactly (2,937) and no ceiling moved.

**These four items are Layer C and are `needs_review: true`, like every lesson exercise.** They were
not put through a Fable random sample (APP_PLAN §1 step 5) because this unit ran as a single agent;
they are four items and they are quoted in full in §6's table plus the ruling table, so a reviewer
can read them without opening the corpus.

---

## 7. Two things a reader should push back on

**1. The practice ratchet has no way to say "the denominator grew honestly."** Before this unit,
そば was taught in a lesson body, unlocked nowhere, in no SRS deck, and drilled by nothing — and the
counter could not see it, because it only counts *unlocked* items. Making the bookkeeping honest made
the number worse while making the learner's situation better. The gate's premise (an unlock is new
teaching) does not hold when an unlock is a *correction*. It was satisfied here by authoring the
practice, which is the right outcome anyway, but the next unit that regularises an exemption will hit
the same wall. Worth a `denominator_note` or an explicit "promotion" class in the baseline.

**2. There is a fifth provably wrong ref, and it was left alone.** *(Closed in W11c — `research/reports/w11_fixup_report.md` §3. The paragraph below stands as written at the time.)* `les:n4-passiva-02` renders
`vocab:1605840` (様/よう) captioned "sufixo de respeito, usado depois de nomes de pessoas" — which
describes `vocab:1545790` (さま). It is body-only, so gating is unaffected; `vocab:1545790` is
unlocked at topic 31 and this lesson is topic 32, so the swap would be gating-clean. It is **not**
one of the four the owner enumerated, and it is not in `vocab_disambiguation_review.json` (only one
record spells 様/よう there, so no queue row existed), so it was deliberately left out of scope
rather than folded in. It is recorded in the 様 hold row and in `gating_exemptions.json`, and it is
the obvious first item of W11b.

---

## 8. Artifacts

| path | what |
|---|---|
| `research/derived/repairs/homograph_rulings.json` | the tracked table — 27 rows: 14 `ref`, 5 `unlock`, 4 `practice`, 4 `hold` |
| `scripts/apply_homograph_rulings.py` | the idempotent apply (both layers), registered as step **112** of `research/derived/rebuild_manifest.json` — this table said 115, which was the last step number in the manifest, not this script's. W11c inserted `apply_lesson_ref_addresses.py` at 112 and this script is now **113**. What replays it is `validate_index_rebuildable.py` in FULL mode (no `--quick`), which since W11c runs to the end; `--quick` reconstructs the grammar family only and cannot reach it — see `w11_fixup_report.md` §5 for the measurement |
| `scripts/export/vocab_identity.py` | `ruling` + `reading` tiers |
| `scripts/export/export_course.py` | `_READING_HINT`; the review file is now written even when it is empty (it used to be left stale) |
| `scripts/validate/test_vocab_identity_reading.py` | 13 checks, in the suite, plant-proved |
| `scripts/validate/validate_repairs_applied.py` | `homograph_rulings.json` registered with its own four-kind addressing |
| `scripts/validate/README.md` | both new entries |
| `design/lesson_schema.md` | the reading rule, in the doc that owns lesson refs |
| `course/coverage_exemptions.json`, `course/gating_exemptions.json` | 9 → 4 and 8 → 4, reasons restated |

Chain run in order: apply → `export_course.py` → `infer_shapes` → `build_schemas` →
`build_manifest` → `npm run sync-data` → `validate_all.py` (**exit 0**). Re-running the exporter
afterwards reproduces `course/` byte for byte, and re-running the apply script reports 0 changes.
No git state was touched.
