# W27 apply — production answer keys on every card

Unit W27 of `research/reports/APP_PLAN.md`. The apply rules are binding from
`research/reports/w27_sample_report.md` (Fable 100-row sample, verdict pass at 2/100).

Status: DONE. Gate green (`scripts/validate/validate_all.py`), full replay green and re-recorded.

## 0. Replay fix — DONE

### The abort

Full-mode `python scripts/validate/validate_index_rebuildable.py` stopped the chain at step 116:

```
  [OK ] 115 scripts/apply_lesson_needs.py       0.1s  wrote 8 need(s) into the authoring sources ...
  [FAIL] 116 scripts/apply_reading_passages.py  0.2s  NOTHING WAS COMMITTED — a box that does not match the table is not rewritten.

rebuild finished in 1.4 min — 80 step(s) run, 1 failed
[FAIL] the rebuild itself did not run clean; nothing to diff
```

Re-run in isolation against the replay database, the step prints 114 of these and exits 2:

```
  ! read:n3-causa-01-01: the box holds neither the table's `old` nor its `new` jp — it drifted
    after the table was built; SKIPPED
```

### The diagnosis

The precondition assumes today's reading table. `research/derived/repairs/reading_passages.json`
carries, per row, the `old.jp` that `build_readings.py` concatenated **on this machine** from the
whole 5,890-sentence bank when W15 built the table. A from-scratch replay does not have that bank at
step 41: it builds **116 boxes where the live index carries 286**, and for a slug it does build, the
i+0 sentences it picks are a different, thinner selection. Measured on the replay database:

| | |
|---|---|
| reading boxes the replay builds | 116 |
| of those, addressed by the table | 114 |
| of those, holding either `old.jp` or `new.jp` | **0** |

So the refusal was not detecting drift; it was detecting that a replay's selection is not this
machine's selection, which it never can be. Ids were fine and the lesson bodies were fine — the
`<reading ref>` nodes address the box by slug and no slug moves.

### The fix

`old.jp` is a drift check **on the live index and only there** — the idiom
`scripts/migrate_grammar_merge.py` already uses for its `expect` block. `scripts/apply_reading_passages.py`
now computes `LIVE_INDEX = Path(DB).resolve() == (ROOT / "db" / "corpus.sqlite").resolve()`:

- **live index**: unchanged. A box holding neither `old` nor `new` is refused, nothing is committed,
  exit 2.
- **any other target**: the mismatch is printed per box (`[replay] read:… box built 94 char(s) of a
  different selection; the table's `old` is 119 — precondition NOT ENFORCED …`) and the authored
  passage is applied over whatever the replay built. The row does not depend on `old.jp`: it is keyed
  by the box SLUG and carries its own `jp`, `jp_sentences`, `uses`, titles and translations. What
  checks a replay is the byte diff in `validate_index_rebuildable.py`, which is strictly stronger
  than a row-level precondition.

Proofs:

- **replay, run 1**: `wrote 114 rewritten box(es) (114 whose jp moved this run) and 2
  provenance-only stamp(s); 4 held` — the same 4 W21b holds as on the live tree.
- **replay, run 2 (idempotency)**: `wrote 0 rewritten box(es) … and 0 provenance-only stamp(s)`.
- **live index**: `--check` reports 0 changes, exit 0.
- **plant proof of the guard**: a copy of `db/corpus.sqlite` with `read:n5-adjetivos-04-01.jp`
  overwritten, run with `LIVE_INDEX` forced true, still prints
  `! read:n5-adjetivos-04-01: the box holds neither the table's `old` nor its `new` jp` and exits 2.
  The fix did not widen the guard.

### The baseline

Full mode now runs to the end (all 121 steps, 87 s of diff) and the ratchet was re-recorded.

| | before (recorded 2026-09-09, pre-fix) | after |
|---|---|---|
| exported files compared | 790 | 790 |
| **byte-identical** | **147** | **222** |
| held by `rebuild_baseline.json` | 643 | 568 |

`[OK] 790 exported file(s) checked, 568 held by rebuild_baseline.json at the recorded bytes`.
Quick mode unchanged and green (4/4 held).

**What moved, and why.** All **75** newly byte-identical files are N3 lesson `.md` renders, spread
over the fifteen N3 topics 38-52. They are exactly the lessons whose reading box the replay now
fills with the authored W15 passage instead of the thin replay-era concatenation, so the `> 📖`
line in the rendered view finally matches the committed one. No file moved the other way: the
`[ratchet] … now matches the committed export` list is the whole of the change, and every one of
the 568 entries that stayed keeps the cause it already carried.

The 568 recorded entries also absorb the byte changes W15, W20 and W21 legitimately made to the
committed export since the baseline was last written (reading passages in 232 lessons, 899 kanji
exercises in 178 lessons, `needs[]` in 314) — those files differ from their old recorded bytes
because the committed side moved, not because the rebuild regressed.

### The baseline again, after the W27 apply

Adding step 118 changes what the replay exports, so the ratchet was re-recorded a second time at the
end of the unit. The byte-identical count did **not** move: `[OK] 790 exported file(s) checked, 568
held by rebuild_baseline.json at the recorded bytes`, i.e. **222 of 790** either way. 245 of the 568
held entries carry new bytes (the lessons that gained `production_key` and were already baselined);
nothing healed and nothing regressed. Quick mode: 4/4 held, unchanged.

| | 2026-09-09, pre-fix | after the replay fix | after the W27 apply |
|---|---|---|---|
| rebuild runs to the end | **no** (abort at step 116) | yes (81 steps) | yes (82 steps) |
| byte-identical | 147 / 790 | **222 / 790** | 222 / 790 |
| held by the ratchet | 643 | 568 | 568 |

## 1. W27 apply — DONE

### What landed

| | |
|---|---|
| production cards on vocabulary records in the export | 2,951 |
| **cards keyed** | **2,951 / 2,951 (100%)** |
| rows from the W27 campaign, applied as authored | 2,937 |
| rows from the campaign with a one-word hygiene repair | 1 |
| rows dropped because W09 re-pointed the record, and re-authored | 8 |
| rows authored for a W11a unlock that had none | 5 |
| rows in the campaign table that address no live card | 0 |
| live cards with no row | 0 |
| prompt collisions across all 2,951 | 0 |

The reconciliation is exact and is asserted by the builder: 2,946 authored minus 8 re-pointed plus 13
residue = 2,951 = the production cards the course issues, with no row left over and no card left
uncovered.

### (a) Redirect resolution, and the 13 authored rows

Every row's `vocab` was resolved through `corpus/vocab_redirects.json`. Eight rows addressed a record
W09 re-pointed after the campaign was authored; their prompts describe the RETIRED lexeme, so they
were dropped rather than re-pointed, and the card's new record was keyed from scratch. Five
production cards created by W11a had no row at all. Those 13 are the only authoring in this unit and
they live in `research/derived/card_key_residue.json`, in full, with the evidence per row.

`accept` is **not** authored in any of the 13: it is the record's own `forms[]` put through exactly
the same JMdict strip as the other 2,938, and the residue file states the expected result so the
builder refuses if the two disagree.

**The 8 re-pointed rows, re-authored**

| lesson | card (new record) | was (dropped) | prompt | accept | sense |
|---|---|---|---|---|---|
| `les:n5-particulas-lugar-02` | `vocab:1006830` 其の/その | `vocab:1176240` 園 "jardim, parque (termo literário)" | esse, essa (vem antes de um substantivo: esse livro) | 其の · その · そん | 0 of 3 |
| `les:n5-particulas-lugar-03` | `vocab:1416220` 達/たち | `vocab:1551240` 立ち "partida, saída (substantivo derivado do verbo たつ)" | sufixo que forma o plural de pessoas e animais (nós, vocês) | 達 · たち | 0 of 1 |
| `les:n5-particulas-lugar-07` | `vocab:2137720` 然う/そう | `vocab:1401470` 総 "total, geral (prefixo que se junta a um substantivo)" | é isso mesmo, exato (confirma o que a outra pessoa acabou de dizer) | 然う · そう | 1 of 3 |
| `les:n5-te-form-05` | `vocab:2019640` 杯/はい | `vocab:1472630` 杯/さかずき "cálice de saquê, a taça de bebida alcoólica" | contador de copos, xícaras e tigelas cheias | 杯 · 盃 · はい | 1 of 5 |
| `les:n5-te-form-05` | `vocab:1010080` はい/はい | `vocab:1472870` 肺 "pulmão, o órgão da respiração" | sim, isso mesmo (a resposta afirmativa formal: professor, cliente, chamada) | はい | 0 of 6 |
| `les:n4-forma-simples-02` | `vocab:1001090` うん/うん | `vocab:1172610` 運 "sorte, boa ou má (o acaso que decide as coisas)" | sim, aham (a resposta afirmativa informal, entre amigos) | うん · ウン · うむ · ううむ | 0 of 3 |
| `les:n4-forma-simples-03` | `vocab:1449890` 到頭/とうとう | `vocab:1855690` 等々 "e assim por diante, etc. (o sufixo que fecha uma lista)" | finalmente, no fim das contas (o desfecho que veio depois de todo um processo, bom ou ruim) | 到頭 · とうとう | 0 of 1 |
| `les:n4-obrigacao-05` | `vocab:1004310` 斯う/こう | `vocab:1272630` 侯 "marquês, senhor feudal" | assim, deste jeito (o modo que está aqui, do lado de quem fala) | 斯う · こう | 0 of 3 |

**The 5 W11a unlock cards, keyed**

| lesson | card | prompt | accept | sense |
|---|---|---|---|---|
| `les:n4-condicionais-01` | `vocab:1310670` 止める/とめる | parar alguma coisa, estacionar, desligar (verbo transitivo, lê-se とめる) | 止める · 留める · 停める · とめる | 0 of 2 |
| `les:n5-comparacoes-02` | `vocab:1423310` 中/なか | dentro, o interior de alguma coisa (lê-se なか) | 中 · なか | 0 of 2 |
| `les:n5-conectando-01` | `vocab:2846738` 何/なん | o quê (o interrogativo na leitura なん) | 何 · なん | 0 of 2 |
| `les:n5-particulas-lugar-02` | `vocab:1403830` 側/そば | ao lado, pertinho de (lê-se そば) | 側 · 傍 · そば | 0 of 1 |
| `les:n5-passado-05` | `vocab:1189370` 何方/どなた | quem (a forma educada de perguntar, lê-se どなた) | 何方 · どなた | 0 of 1 |

**How the sense was chosen.** From the lesson's own prose wherever the lesson names it: 杯 is
"contador de copos e tigelas (一杯, 二杯…)" in `les:n5-te-form-05`, 達 is "o sufixo que marca plural
de pessoas" in `les:n5-particulas-lugar-03`, 斯う is "assim, deste jeito" in `les:n4-obrigacao-05`,
中 is "A peça 中 (なか) quer dizer dentro/interior" in `les:n5-comparacoes-02`, 何方 is "a maneira
polida de perguntar quem é?" in `les:n5-passado-05`.

**One exception, and it is an open item, not a guess.** `les:n5-particulas-lugar-07`'s body still
describes 総 ("total / geral"), the lexeme W09 retired; the lesson never mentions そう as a word. The
sense there is taken from the two JLPT list rows the re-point itself was made on
(`そう; そうです — "yes; appears, to be the case"` and `そう — "really, (is that) so; yes, right"`),
both of which name the interjection, so the card is keyed to sense 1. **The stale prose is a W09
residue of the same class as W21b's forward references and belongs to a course-data unit; nothing
here touches lesson prose.**

**Homograph pressure was real and is handled in the prompt.** Four of the five W11a cards sit beside
a homograph the course teaches separately (中 なか vs 中 ちゅう, 何 なん vs 何 なに, 側 そば vs 側
がわ, 何方 どなた vs 何方 どちら, the last two in the SAME lesson), which is why each carries its
reading, matching the style the Fable sample approved (上 "curso superior de um rio (lê-se かみ)").
止める carries "(verbo transitivo, lê-se とめる)" because 止める is also read やめる and because
止まる and 止む are taught elsewhere.

### (b) The accept strip

Tags read from the archived dictionary itself,
`research/datasets/jmdict/jmdict-eng-3.6.2+20260608153333.json.zip` (`kanji[].tags` plus
`kana[].tags`), matched case-insensitively: JMdict spells the kanji side and the kana side of the
same idea differently and the sample report cites members of both (其の is `rK`, あぢぃ is `sk`).

**1,396 forms removed over 831 of 2,951 rows** (28.2% of rows; no accept set emptied, none left
without its headword or kana):

| tag | meaning | removed |
|---|---|---:|
| `sK` | search-only kanji form | 508 |
| `rK` | rarely used kanji form | 484 |
| `sk` | search-only kana form | 205 |
| `ok` | out-dated or obsolete kana usage | 102 |
| `oK` | out-dated kanji | 56 |
| `ik` | irregular kana usage | 21 |
| `iK` | irregular kanji usage | 14 |
| `rk` | rarely used kana form | 4 |
| (none) | **not a form of this record at all** | **2** |
| | **total** | **1,396** |

- **`arch` removes nothing, and that is correct.** In JMdict `arch` is a SENSE-level misc, not a form
  tag; it names no surface. The archaic forms the sample complained about (海 accepting み/わた/わだ,
  職 accepting そく) carry `ok`, and they are gone.
- **`ateji` (67), `gikun` (38) and `io` (43) were deliberately NOT stripped.** The report does not
  name them and they are how people write those words: 珈琲 for coffee, きょう for 今日, 隣り and
  話し. Stripping them would have marked correct answers wrong.
- **96 tagged forms were kept because they are the record's own headword** (87 `rK`, 9 `sK`), per the
  report's "keep the headword, its common kanji variants and the kana". 其の, 然う, 到頭, 斯う and
  何方 are all `rK` headwords. Measured both ways: with or without that guard, 0 accept sets are
  emptied and 0 lose their name, so the guard costs nothing and guarantees check C is satisfiable.
- **The 2 "not a form" removals** are `それでわ` (`vocab:1406050` それでは) and `じつわ`
  (`vocab:1320830` 実は): net-slang respellings of the topic particle that no JMdict tag covers and
  that `validate_card_content.py` check C would refuse. 54 other accept forms are absent from
  `forms[]` and were KEPT, because NFKC folds them onto a form the record does carry: `5日` for
  `５日`, `FAX` for `ＦＡＸ`, `Yシャツ` for `Ｙシャツ`, `タヒぬ` for the halfwidth `ﾀﾋぬ`. Those are
  the same surface typed on a different keyboard.
- Every removal is logged per row in `accept_removed`, with its tags.

Resulting accept sets: min 1, median 2, max 10 forms.

### (c) Where the key went, in both layers

`design/srs_design.md` had no per-card content field of any kind, so this unit made the schema edit
the W27 row implies, in the design and in the contract, with neutral English field names:

```json
{"deck": "deck:vocab-n5", "item": "vocab:1423310", "card_types": ["recognition", "production"],
 "production_key": {"prompt": {"pt-BR": "dentro, o interior de alguma coisa (lê-se なか)"},
                    "accept": ["中", "なか"], "sense_index": 0,
                    "verified": "sampled", "verified_by": "research/reports/w27_sample_report.md"}}
```

- `design/srs_design.md` **§8** is the new section: the field table, why the key belongs to the CARD
  (lesson, item) and not to the vocabulary record, why it is optional, and what it deliberately does
  not settle (how a grader normalises typed input is the app's rule, not the corpus's).
- `contracts/lesson.schema.json` carries it, generated: `scripts/contracts/build_schemas.py`
  registers the whole `production_key` object under
  `lesson.srs.introduces_cards[].production_key`. Registered as one object rather than four leaf
  paths because `infer_shapes.py` walks two levels and stops exactly there, so leaf rules under it
  would have been dead entries nothing looks up.
- `contracts/user_state/card.schema.json` gains a `content_note` instead of a field: the runtime card
  is scheduling state and must not carry a second copy of a corpus string, or a repaired prompt
  becomes a migration across every learner's rows. It reads the key through
  (`introduced_by`, `item`).
- `design/i18n.md` gains the scope row. `prompt` is a `LocaleText`, never a bare `prompt_pt`: that
  exact shape is already recorded there as a contract violation on `speak_unit`. `accept` stays a
  bare array, because Japanese here is the material under test, the same ruling the file gives
  `exam_item.answer`.
- **Both layers.** Authoring layer: `research/derived/repairs/card_production_keys.json` (the
  exact-match decision table, built by `scripts/build_card_key_table.py`) plus
  `research/derived/card_key_residue.json` (the 13 authored rows) and
  `research/derived/card_keys_authored.json` (the campaign artifact, moved out of
  `research/derived/pending/` because pending means authored-and-not-applied). Index layer:
  `card_production_key` (migration **016**), written by `scripts/apply_card_production_keys.py` and
  joined onto the derived card by `scripts/export/export_course.py`.
- **Every row carries `verified: "sampled"` and `verified_by: "research/reports/w27_sample_report.md"`.**
  That is a claim about the table (one verifier per batch at authoring time, then the 100-row Fable
  sample), never about the row, and the contract's own description says so. The teacher queue still
  owns these 2,951 prompts.
- Registered in `validate_repairs_applied.py` (`handle_card_production_keys`, six claims per row:
  **2,951 / 2,951 PASS, 0 FAIL**) and in the rebuild manifest at **step 118**, after the practice
  apply and before the family builders. Furigana moved 118 to 119 and the three family builders
  119-121 to 120-122; `scripts/validate/README.md` was updated with them.

**Lesson prose did not move, and this was measured rather than asserted.** The course tree was
re-exported from a copy of the index with `card_production_key` emptied and diffed against the
shipped export, file by file: **708 files, 0 `.md` files differ, 0 files differ in anything other
than `production_key`, 2,951 `production_key` objects added.** No lesson body, unlock, exercise or
`needs` entry was touched.

### One repair the gate forced, and it is not authoring

`audit_hygiene_all_locales.py` failed the first apply on a single campaign prompt: `les:n3-causa-08`
/ `vocab:1558370` 列車 read "trem, composição ferroviária (o **comboio** inteiro …)". `comboio` is
pt-PT for a train and means a convoy in pt-BR. One word, same sense, same accept set. The rewrite is
recorded as a `prompt_overrides` entry in `research/derived/card_key_residue.json` rather than as an
edit to the campaign artifact, so the artifact stays the record of what W27 authored; the builder
refuses if the override's `was` no longer matches the authored prompt, so a stale override cannot
become a silent no-op. It is one more sampling miss of the same kind the Fable 100 found two of.

### The applier is replay-safe too, and the guard is proved

Three of the 2,951 rows address no card in a from-scratch replay: `vocab:背` resolves to
`vocab:2147990` there instead of `vocab:1472650` and `vocab:年` to `vocab:2084840` instead of
`vocab:1468060` (headword refs, resolved through the identity resolver, which reads index state a
replay does not reproduce), and `les:n4-kanji-exame-05` does not unlock 献花 at all because
`build_exam_kanji_lessons.py` re-chunks the eight `*-kanji-exame-*` lessons — the same cause
`apply_lesson_furigana.py` already records. Off the live index those three are printed and skipped
and the other 2,948 are written; on `db/corpus.sqlite` a row with no card is still a refusal with
nothing committed, proved by deleting one unlock from a copy of the live index and forcing the live
branch: `! les:n5-comparacoes-02 / vocab:1423310: the lesson does not unlock this item … exit 2`.
Idempotent in both modes (second run: 0 new, 0 rewrites).

## 2. `validate_card_content.py` — the gate W26 left pending

Reads the exported course tree, never the DB. Five checks:

| | |
|---|---|
| **A** | every card's `item` resolves in the registry its namespace names (kana at both granularities, family form and glyph form, exactly as `validate_srs_decks` accepts them) and is not a key of `corpus/vocab_redirects.json`, `corpus/grammar_deprecated.json` or `corpus/families_deprecated.json` |
| **B** | every `production` card carries a `production_key` with a non-empty `prompt["pt-BR"]` and a non-empty `accept`; ratcheted per namespace |
| **C** | `accept` contains the record's headword or its kana, **and** nothing outside that record's `forms[]` (NFKC twins count as the form they fold to) |
| **D** | a `production_key` only on a card whose `card_types` carries `production` |
| **E** | `prompt` is a locale object with `pt-BR` and no undeclared locale; `sense_index` names a real sense; `accept` has no blank and no duplicate |

Result today: `[OK] 4136 card(s) over 322 lesson(s); 2951 production key(s) checked`.

Ratchet (`UNKEYED_RATCHET`, shrink-only): **vocab 0**, gram 494, kanji 634, kana 57. Vocabulary is
finished and a new unkeyed vocabulary card fails; the other three namespaces are W28-and-later work
and are held at today's counts with a written reason.

Empty input fails: floors of 300 lessons, 3,500 cards and 2,500 keys, plus hard refusals when the
vocab registry or the kana ids are missing.

**Plant-proved on a copied tree** (the validator copied into the fixture beside its own `corpus/` and
`course/`, because it resolves ROOT from its own path): **11 plants, 11 caught, control green** —
missing key, blank prompt, an accept set stripped of both headword and kana, an alien form (月), a
ghost item, a retired item, a key on a recognition-only card, an out-of-range `sense_index`, a
duplicate accept entry, a bare-string prompt, and an emptied course tree. Verbatim output is in the
validator's docstring. Registered in `scripts/validate/validate_all.py` as a hard `code` entry and
documented in `scripts/validate/README.md`.

## 3. Final state

- `python scripts/validate/validate_all.py` -> **ALL HARD VALIDATORS PASS**.
- `python scripts/validate/validate_index_rebuildable.py` -> `[OK] 790 exported file(s) checked, 568
  held`; `--quick` -> `[OK] 4 … 4 held`.
- `validate_repairs_applied.py` -> 7,608 rows replayed clean over 15 tables, 0 FAIL (the new table
  contributes 2,951/2,951).
- Exporters, then contracts (`infer_shapes` -> `build_schemas` -> `build_manifest`), then
  `npm run sync-data`, in that order.
- **Nothing was committed** (the run was told to touch no git state).

## 4. Open, and named

1. **`les:n5-particulas-lugar-07`'s body still teaches 総**, the lexeme W09 retired, while the card
   it issues is そう. Course-data repair, same class as W21b's forward references. The card is keyed
   from the list evidence in the meantime.
2. **Three rows have no card in a from-scratch replay**, held by the rebuild ratchet (背, 年, 献花 —
   see above). Writing those unlock refs as published slugs, the way W11c did for 39 lesson refs,
   would retire all three.
3. **`vocab:1457730` 内/うち accepts 中**, so its accept set overlaps `vocab:1423310` 中/なか. Both
   prompts disambiguate by reading, which is the design, but a grader that ignores the prompt would
   take 中 for either. Pre-existing, straight from JMdict's own forms; noted, not touched.
4. **`vocab:1001090` うん accepts うむ and ううむ** (untagged in JMdict, so the strip keeps them)
   while the prompt says "sim, aham". Same class as the leniency the sample flagged, but no tag
   covers it; a teacher pass or a sense-scoped accept rule would settle it.
5. **1,185 production cards still carry no key**: grammar 494, kanji 634, kana 57. Held by the
   ratchet; they are W28/W29/W30 work.
6. **`verified: "sampled"` is not row-level verification.** 2,951 prompts are Layer C awaiting the
   teacher queue; the sample's own failure rate was 2/100, and both failures were the mechanical
   class this apply fixed.

