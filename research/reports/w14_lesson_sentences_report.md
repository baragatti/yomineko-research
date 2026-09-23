# W14 lesson sentence re-selection (C3-W14, 2026-09-23)

Unit C3-W14 of the writer chain. Not a checkpoint: gate plus quick replay only. Mechanical: every
sentence comes from the bank (10,209), no sentence and no prose was authored.

## 1. What ran

1. `scripts/derive_lesson_sentences.py` (new) reads the exported tree and writes
   `research/derived/repairs/lesson_sentences.json` (123 rows + 154 residue entries). It refuses to
   overwrite that table once it exists (after the apply the tree derives almost nothing).
2. `scripts/apply_lesson_sentences.py` (new) applies the rows to both layers: the pt-BR body in
   `localized_text` plus `lesson_sentence`, and `research/derived/lessons/<slug>.json` (body and its
   `sentence_refs`). Dry pass over both layers first; a problem anywhere writes nothing. Second run:
   0 changes.
3. `export_course.py`, then `build_needs_table.py` -> `apply_lesson_needs.py --replace` (check C4:
   the new sentence references change the derived DAG), then the exporters, `validate_lesson_gating
   --write-baseline` (every counter went down), contracts, review views, `sync-data`.
4. Replay: `HANDLERS["lesson_sentences.json"] = handle_lesson_sentences` in
   `validate_repairs_applied.py`; manifest step **133** (families renumbered 134-136).

## 2. The rule

One rule, the one the gates already use (`derive_lesson_sentences.py` docstring):

1. sentence level at or below the lesson level (check D's above-level test);
2. `build_vocab_exercises.sentence_ok`, imported: i+0 over both registries and every item
   `derive_needs` expands from the sentence (grammar tags included) taught at or before the lesson
   (check C5). **i+0, not i+1, on purpose:** check D ratchets the COUNT of links carrying any new
   kanji or word, so an i+1 addition would grow `pairs_with_new_kanji`;
3. carries an item the lesson itself unlocks;
4. not already shown by the lesson or cited by its exercises (a cloze answer must not be on screen),
   and each sentence picked once;
5. bank register is model text (neutral, polite, casual, formal).

Ranking: most uncovered unlocks first, then a sentence nothing else references (orphan sweep), then
real over generated, then length >= 5, then shorter, then a seeded hash.

Existing links that pass are never touched. A flagged link (above level or over budget) is only
swapped or removed when it sits in a pure example block: nothing but sentence tags between it and an
example heading (`Mais exemplos`, `Exemplos do banco`, `Exemplos reais`, `Frases reais`) and no prose
right after it. A replacement must carry what the old sentence was there to show (a lesson unlock
the old one carried, else the lesson's grammar, else any unlock). A removal never empties a lesson.

## 3. What changed

| op | rows | notes |
|---|---:|---|
| add | 61 lessons, 170 sentences | `Mais exemplos` block, mode="card", before `Hora de praticar`; 150 of 170 real (Tatoeba/JEC); n3 137, n4 23, n5 10 |
| replace | 8 | in place, show/mode kept, all 8 carry an item the old sentence carried |
| remove | 22 | no in-rule sentence carries what the old one showed |
| drop-heading | 8 | example headings the removals left empty |
| chip | 24 | the 24 pre-N5 survival words of `top:pre-n5-saudacoes`, `<item><jp>KANA</jp>` -> `<item><vocab ref="vocab:SLUG"/>` |
| **residue** (not applied) | 154 | 138 flagged links that the surrounding prose introduces or discusses, 16 whose removal would empty the lesson (n4 95, n5 57, n3 2) |

The first attempt swapped links embedded in explanatory prose ("Nesta primeira, o adjetivo いや
recebe だった:" followed by an unrelated sentence) and replaced example-block sentences with ones
unrelated to the grammar being taught. Both were reverted (DB restored from the pre-apply copy,
sources from HEAD, re-export verified `course/` equal to HEAD) and the rule tightened to what §2 says.

Sample of the additions (seeded draw of 12):

| lição | frase | tradução |
|---|---|---|
| les:n4-kanji-exame-04 | ここから遠いの？ | É longe daqui? |
| les:n3-relato-07 | この文字は何と読む？ | Como se lê este caractere? |
| les:n3-estrutura-06 | 早い者勝ちですよ。 | Quem chega primeiro leva. |
| les:n3-concessao-05 | 私の立場になってくれ。 | Se põe no meu lugar. |
| les:n3-perspectiva-07 | 理解できません。 | Não consigo entender. |
| les:n3-causa-06 | 手品が大好きなんだ。 | Eu adoro mágica. |
| les:n3-perspectiva-07 | 楽にしてください。 | Fique à vontade. |
| les:n3-causa-08 | 料金は部屋につけておいていただけますか。 | Poderia colocar na conta do quarto? |
| les:n4-kanji-exame-01 | 思わず大きな声が出た | Sem querer, saiu um grito. |
| les:n3-revisao-01 | どの便に乗ってたの？ | Você veio em qual voo? |
| les:n3-limites-05 | 大したことじゃないよ。 | Não é nada de mais. |
| les:n3-estado-05 | 食べ物は生物にとって必要なものです。 | A comida é necessária para os seres vivos. |

The 8 replacements: 木はその実で分かる。 -> そのうち分かるよ (n5-perguntas-02), 冷たいなあ。 -> キツイなあ。
(n5-passado-04, gram:naa), 無理も通れば道理となる。 -> 話上手もいれば、聞き上手もいる。 (n4-condicionais-03),
最近は仕事がなかなかないんだよ。 -> この店はとても近い (n4-potencial-04, kanji:近), 病気が全快なさるように。 ->
もし来られたら来なさい。 (n4-keigo-03, gram:nasaru), その結果はどうなのか。 -> 毎朝果物を食べます
(n3-causa-02, kanji:果), 風邪引かないようにコートを着た。 -> 働き過ぎないように。 (n3-intencao-03),
先生は私たちに毎日教室を掃除するように言う。 -> 弟に早く帰るように言う (n3-relato-02).

## 4. Gating ratchets (all shrink; baseline re-frozen with `--write-baseline`)

| counter | before | after |
|---|---:|---:|
| sentence links (pairs_total) | 624 | **772** |
| pairs_above_level | 178 | **152** |
| pairs_over_budget | 25 | **20** |
| pairs_with_new_kanji | 164 | **140** |
| pairs_with_new_vocab | 39 | **34** |
| C5 forward uses / edges, same-topic | 1 / 1 | 1 / 1 |
| C5 same-level | 14 / 14 | **13 / 13** |
| C5 cross-level | 160 / 160 | **151 / 151** |

(The readiness audit's "147 over budget" is the pre-W21b figure; the frozen baseline at HEAD was 25.)

## 5. Lessons rendering zero sentences

| level | before | after |
|---|---:|---:|
| pre-n5 | 41 | 41 (kana strand + the 3 greetings lessons: no i+0 sentence exists at that known set) |
| n5 | 15 | **11** |
| n4 | 12 | **3** |
| n3 | 48 | **0** |
| **total** | **116** | **55** |

Left at zero with unlocks (the rule found nothing): the three `pre-n5-saudacoes` lessons,
`n5-numeros-tempo-01/04/06/07/08/09`, `n5-convites-06`, `n5-conectando-07` (the table's
`zero_left`). The other 44 have no vocab/kanji/grammar unlock (kana, phonetics, orientation).

## 6. Orphan sweep

Measured as "referenced by no exported record under `course/` or `corpus/` outside the bank" (a
wider bank than the audit's 5,889, so not the audit's 503): **2,471 -> 2,324** (148 newly wired, 1
newly orphaned: `sent:tatoeba-112055`, a removed over-budget link nothing else cites). By level after:
n3 1,261, n4 371, n2 327, n1 297, n5 68. The ranking prefers orphans, so every addition that could
use one did; the rest of the orphans are above the course's levels or fail i+0 everywhere.

## 7. Lessons did not degrade (rendered diff against HEAD)

Over every changed file under `course/`: 101 lesson JSONs, 91 `.md` views, 26 `topic.json`.
- lesson bodies with sentence tags, the four example headings and the 24 chip substitutions
  normalised away: **0 differences**;
- lesson fields changed: `body` 91, `sentence_refs` 88 (derived from the body), `needs` 53; nothing
  else (unlocks, cks, exercises, srs, title: 0);
- `topic.json`: only the lesson stubs' `needs` mirror;
- rendered `.md`: 149 lines removed = 30 sentence lines + 8 example headings + 8 blank + 88 sentence-ID
  manifest lines + 15 chip list items; 403 added.

The 15 chip lines differ only in the `.md` review view, which prints a chip as its headword
(`下さい`, `御座います`, `一寸`) where the bare text printed the kana. The app chip renders the
record's kana (`render-body.server.ts` `chip()`: `text = v.kana`), so what a learner sees is the
same word, now with a modal.

`needs` changed on 53 lessons: derive_needs reads rendered sentences as references, so check C4
required the stored DAG to be re-derived (741 -> 736 rows: derived 697 -> 693, review chain 4 -> 3 because `n5-kanji-exame-03` now derives a
real need from its new sentences; roots 4). Record
metadata, not prose.

## 8. Gate

`validate_all.py`: ALL HARD VALIDATORS PASS, including the quick replay
(`validate_index_rebuildable --quick`: 4 files, 4 held at the recorded bytes).
`validate_repairs_applied`: 21,504 rows replayed clean + 21 checked skips, 0 FAIL; the new table
123/123. `validate_lesson_gating`: 0 FAIL, 772 links. Not a checkpoint: the full replay was not run.
The step-33 regeneration of the kanji-exame sources (5 of the 61 blocks land there) is therefore
exercised only by the next checkpoint's full replay.

## 9. Open

- **Residue 154** (in the table): 138 flagged links that prose introduces or discusses and 16 whose
  removal would empty the lesson. Needs a pass that may rewrite the sentence and its prose together
  (authoring), lesson list in the table.
- **11 lessons still render no sentence** with unlocks (list in §5): nothing in the bank is i+0 at
  their known set; an authored sentence per lesson, or i+1 once the new-kanji ratchet has room.
- **Fable sample of 30** on the applied rows (APP_PLAN §1 step 5) still owed.
- `lesson_sentence` (DB staging table) was already out of step with the bodies on 54 lessons before
  this unit; the exporter ignores it. The rows this unit touches are kept in step; the rest is not
  fixed here.
