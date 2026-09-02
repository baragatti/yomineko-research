# Translation-defect repair campaign — what was NOT repaired

_Companion to `research/derived/repairs/translation_defect_repairs.json` and
`scripts/apply_translation_defect_repairs.py` (231 fields applied, DB only, `db/corpus.sqlite`
`localized_text`). This file records every finding from the six auditors' reports
(`translation_accuracy_1.md` … `_6.md`) that the campaign deliberately did **not** rewrite, and why._

The applied campaign covered the individually named defects only: meaning shifts in
`translation` [pt-BR], scaffolding and explanatory parentheses left inside the natural-speech field,
unnatural pt-BR, orthography slips, register, person/agent disagreement between the two translation
layers, the individually named `translation_literal` defects, the token-gloss errors, and the editor
comments that leaked into token `conjugation_note`.

---

## 1. Systematic classes excluded by the campaign brief (already repaired elsewhere)

| Class | Scope in the reports | Status |
|---|---|---|
| **A** — "Quanto a …" topic scaffold applied to が/を/に/で/bare chunks | 39 + 59 + 43 + 39 + 34 records named across reports 1, 2, 4, 5, 6 (incl. F1 `32, 338, 428, 470, 632, 644, 650, 698, 716, 740, 746, 752, 884, 908, 914, 968, 998, 1004, 1172, 1238, 1334, 1538, 1796, 2228, 2240, 2252, 2264, 2282, 2288, 2324, 2330, 5792, 5798, 5804` and F2 `44, 1256, 2168`) | Already repaired. Spot-checked live on `sent:gen-633db27a84d8`, `sent:gen-d4a16635f7bd`, `sent:gen-273cffc1f6f8`, `sent:jec-4753`, `sent:gen-ff855e0b043c`, `sent:jec-3567`, `sent:gen-bfd8d9f015bb` `[1667]`, `sent:jec-0240`, `[1899]` — all now carry case scaffolds (`(が, sujeito)` / `(を, objeto)`) instead of "Quanto a". |
| **B** — こ/そ/あ demonstrative mis-mapping | 13 records, plus F3 `2414, 3074, 3428, 3830, 4118, 4124, 4160, 4166, 4922, 5840` (その → aquele/aquela) and F4 `92, 266, 566, 878, 1220, 1592, 1910, 2252, 2372, 2576, 2594, 2606, 4286, 4490, 5030, 5276` (この/これ → esse/essa/isso) | Already repaired. |
| **E** — missing `translation.en` | 59 / 61 / 62 / 53 records across reports (same underlying set) | Already repaired. |
| `structure_explanation` findings | all reports | Repaired by a separate campaign, excluded by instruction. |

**Class-A residue still open.** Two records survived the class-A pass and were only partly
addressed here, because this campaign is not the owner of that scaffold:

- `sent:gen-fa090f27e750` — the `Em a` → `Na` contraction is fixed; the `quanto a cadeiras` scaffold
  on a **が**-marked subject (いすが) is still there. Left for the class-A owner.
- `sent:tatoeba-2211172` — the 1階 floor contradiction is fixed (`no térreo (1階)`); the その →
  "àquele" demonstrative slip is class B. Note the live string now ends `…no térreo (1階) existe.`,
  so the class-B pass must match the new text.

---

## 2. Findings outside this campaign's storage scope

The rewrite table addresses `localized_text` for `entity_type` **sentence** (`translation`,
`translation_literal`) and **token** (`gloss`, `role`, `conjugation_note`). These real defects live
in fields it cannot reach and need their own pass.

**Particle fields** (`localized_text` `entity_type='particle'`, fields `function` / `explanation`):

- `sent:gen-4cace4963888` — `から` note contains "desde de manhã" (the doubled preposition fixed in
  the sentence translation).
- `[1628]` and `[410]` — same "desde de manhã" slip in `particles[から].explanation.pt-BR`.
  `[410]`'s own translation is already correct ("desde cedo"); only its particle note is wrong.
- `sent:gen-3ecabce0d070` and `sent:gen-f1b038704e1c` — "prática" used where the verb "pratica" is
  meant. The same slip inside `sent:gen-12a28127409c`'s particle explanation ("prática-se 'o quê?'")
  is likewise unreachable; that record's **sentence-level** twin was repaired.
- `[1556]` — `particles[から].explanation.pt-BR` describes それから in a 外国から sentence
  (車を外国から輸入する会社です). The finding is real; the field is out of scope.

**Non-`localized_text` fields:**

- `sent:gen-9f80f08cc644` `kana` reads `このみそわつらいです` — 辛い is transcribed つらい instead of
  からい. The reading is wrong under either sense of 辛い. `kana` is a `sentence` column, not a
  localized field.
- `sent:tatoeba-79687` token 夜食 `role`["pt-BR"] = "função do que se comeu" — vague; the report
  itself leaves the role alone, and only the `gloss` was named.

---

## 3. Layer-A source strings — refused on provenance grounds

`export_corpus.py` renders `translation.en` as `sentence.en or localized_text`, so for mined
sentences the English shown is the **immutable Layer-A pair**, not authored text. Spec §1.1 and
style §3 forbid editing a selected source sentence. In every case below the pt-BR is correct and
stays; the divergence, if it must be recorded, belongs in a note rather than an edit.

- `[2234]` `sent:jec-0453` — source en "He looked at the sea through the curtains." (僕 is first
  person; "Olhei o mar" is right).
- `[4610]` `sent:tatoeba-373351` — source en "Welcome." for こんにちは; the record's own structure note
  already documents the mismatch.
- `[4622]` `sent:tatoeba-4216208` — source en "I feel like a fool." (バカみたい as impersonal
  "Que ridículo" is fine).
- `[2315]` `sent:jec-3829`, `[2951]` `sent:tatoeba-124978`, `[2987]` `sent:tatoeba-126322`,
  `[3485]` `sent:tatoeba-165585` — no `('sentence', id, 'translation', 'en')` row exists; the bank's
  en comes from `sentence.en` ("You have nerves of steel.", "The clerk said, \"What can I do for
  you, sir?\"", "Even worms are bought for medical research.", "We should not depend on your
  parents.").
- `sent:tatoeba-78906` `[5093]` — the report calls "ela" an invented third person. It is not: the
  Layer-A pair reads "I expect her to pass the examination easily." The pt-BR is validated against
  that source, and the report's proposed "Acho que vou passar" would contradict Layer A.
- `sent:tatoeba-10661542` `[2495]` — the くせに concessive loss **was** repaired ("E olha que você nem
  é nosso amigo"); "nosso" was kept, because the Layer-A en is "You are not our friend."

---

## 4. `en` twins left untouched (pt-BR-scoped findings)

`design/translation_style.md` is a pt-BR authoring contract, so an `en` string was only rewritten
when the defect is wrong in any language (a factual sense error, a person contradiction inside one
record, or a leaked editor comment). These `en` siblings repeat a pt-BR defect the reports named for
pt-BR only:

- `sent:gen-537ce93c20eb` `translation.en` "(and it upset me)" and `sent:gen-8adf6d2b2a1f`
  "(and brought it)" — the parenthesis rule is a pt-BR style rule.
- `sent:tatoeba-3179644` `translation_literal.en` "It would have been good if I'd brought a coat" —
  same brought/worn slip as the pt-BR natural field; the report excludes en mismatches.
- The five class-D records now rendered as 1st-person present in pt-BR (`sent:gen-30b970cffa4a`,
  `gen-56d495bbcf16`, `gen-7ea63d9fd0ad`, `gen-c19dfc37c744`, `gen-db21e4d29aa3`) still read as an
  imperative or a gerund in `en`. **Worth a follow-up pass** so the en anchors match the plain
  non-past.
- `[579]` `sent:gen-3de9af165938` `translation.en` "The teacher called me by name." repeats the
  名前を呼ぶ misreading fixed in pt-BR.
- `[507]` `sent:gen-3728d8e6f993` `translation.en` "I ate too many sweets." also drops 少し. Left
  because the obvious repair ("a few too many sweets") would make `translation.en` identical to
  `translation_literal.en`, introducing the duplicate-field defect the report separately certifies
  as zero across the slice.
- `[86]` `sent:gen-09a0580e98f9` `translation.en` "Come down slowly." carries the same 滑降 loss.
- `[296]` `sent:gen-2044754669fc` `translation.en` "\"Coffee\" is written in katakana." — quoting the
  English word inside an English gloss is not misleading the way it was in pt-BR.
- `[1715]` `sent:gen-c5a812d1b02f` `translation.en` "This desk is cramped and hard to use." —
  "cramped" is a defensible rendering of 狭い; only the pt-BR "apertada" was wrong.
- `sent:gen-5cae43f7a7c5` `translation.en` "This sweet is very sweet." — the same tautology as the
  pt-BR finding, but "sweet" as a noun is idiomatic English.

## 4b. Same-record pt-BR siblings the reports did not name

Real, but the reports' fix lines cover only one field of the record. Flagged so the two layers do
not stay in disagreement:

- `[2169]` `sent:gen-fb07d83b3e0c` `translation_literal`["pt-BR"] "A orelha (が, sujeito) dói um
  pouco." — carries the orelha/ouvido slip repaired in the natural field.
- `[1071]` `sent:gen-790b6cf52284` `translation_literal`["pt-BR"] "Quanto a hoje, tendo aberto o
  tempo, está quente." — the same 暖かい → "quente" collapse.
- `[2361]` `sent:tatoeba-10083431` `translation_literal`["pt-BR"] "Quanto a isso, de uva o ramo é,
  viu." — still says "ramo" for つる; それは is a genuine topic は, so the scaffold itself is fine.

---

## 5. Findings I disagree with, or that need a human ruling

- **Gender-inclusive parentheses** in `translation`["pt-BR"] — `sent:gen-c63e16ea70fa` "o(a)
  cliente", `sent:gen-f59f9d5195cc`, `sent:tatoeba-174355`, `sent:tatoeba-4971` "obrigado(a)",
  `sent:tatoeba-79103`, plus `[2951] [4529] [5357] [5735]`. The reports themselves file these as a
  house-style ruling. A teacher decides, not a repair campaign.
- **Subject-less Japanese where pt and en chose different persons** — F10 soft cases `2372, 3254,
  3314, 3560, 3932`. Neither locale is wrong; this needs a project-wide policy, not per-record
  rewrites.
- **Tokenizer-warning `conjugation_note`s** — `sent:gen-52e853b5eb16`, `sent:tatoeba-1057336`,
  `sent:tatoeba-74743`, `sent:tatoeba-74954`. They genuinely warn the learner about a split; "o
  tokenizador" vs "a segmentação automática" is a wording preference, not a defect.
- `sent:tatoeba-74693` "Num trabalho como esse" — the report itself calls the change optional;
  "como esse" is the natural pt-BR fixed phrase and このような does not force "este".
- `sent:jec-0980` "Ele sempre confere tudo direitinho" for 必ずチェックを入れます — idiomatic expansion
  within the latitude the style guide grants the natural field.
- `[1982]` `sent:gen-e481d334d6c3`, the report's second option (rewriting the jp to
  白い靴下を二足買いました) — rejected. Editing the Japanese would force re-deriving tokens, kana and
  the counter gloss; correcting the pt/en translations to match the existing 二つ is the smaller,
  safer fix, and that is what was applied.
- `sent:gen-41d4b4ca8de4` — no change needed. It already uses the house term for 県 ("província" /
  "in the prefecture"); the divergence was entirely on the `sent:gen-e1c01b4c8791` side, which was
  repaired.
- **Borderline items the reports inspected and cleared** — `2216, 3338, 2888, 3164, 2654, 3026,
  1046, 848, 1196, 212, 506, 20, 1598, 2636, 3062, 5426, 3098, 1826, 2348, 4868`. Re-read; agreed
  with not flagging them.
- **Already repaired before this campaign, verified live** — C8 `sent:jec-4666`, C9
  `sent:gen-e550b112cef4`, C10 `sent:gen-edd547874d80`, D6 `[1667]` `sent:gen-bfd8d9f015bb`
  (the "Quanto a panela" string no longer exists), C12 `gen-0b2679ac5ee0, gen-2fef8f85a304,
  gen-5db83dd74419, gen-30f6535979a3, gen-b5e592aada0f, jec-0240`, and the A.1 sub-findings for
  `gen-f4c05abf2f88, jec-3567, gen-47c527ecd4fb, gen-5b0f0ae6501d, gen-a31db51cb8d5`. Of that last
  group only `sent:gen-7f47e7897633` still carried "está estando", and it is fixed in this campaign.

---

## 6. Defects in the campaign's own input table

- **`sent:gen-960d7cee0887` `translation`["pt-BR"] — EXCLUDED, still open.** The table entry gave
  `new` identical to `old` ("Pelo visto ele está ocupado, porque não responde."), so it could not
  apply anything. The finding is real: 〜とみえて states an inference and then its consequence (he
  must be busy, **so** no reply comes), while "porque" inverts the direction and turns the missing
  reply into the evidence; the record's own particle note reads "e por isso". The corrected string
  was not invented here — this record needs a replacement written by the campaign owner. The
  loader rejects an `old == new` row outright rather than counting a silent no-op as a repair.
- **`sent:gen-a5d68ff4012f` `translation_literal`["pt-BR"] — applied after a transcription fix.**
  The table's `old` read `entrei (入っ た)` with a stray space inside 入った; the live DB value has no
  space. Only the `old` snapshot was corrected, so the applied change is exactly the number
  agreement the finding asked for (`com a criança` → `com as crianças`).
- **The "one editor comment leaked into a token `conjugation_note`"** named in the campaign brief
  does **not** appear in reports 4 or 6. It belongs to `sent:tatoeba-11733143`, named in an earlier
  report, and all four of its leaked notes (positions 3 and 6, both locales) were repaired.
- Report 3 names **no** token-gloss error and no leaked editor comment; the つ counter gloss it
  cites ("contador genérico de unidades") is correct and was in fact the evidence against the
  "pares" translation. Report 5 likewise reports zero token-level findings.

---

## 7. Storage note

The legacy mirror columns (`sentence.pt`, `sentence.pt_literal`, `sentence.structure_explanation_pt`,
`token.gloss_pt`, `token.role_pt`, `token.conjugation_note_pt`) are **entirely NULL** across the DB —
drained by the i18n migration — so `localized_text` is the sole store and these repairs cannot drift
against a second copy. `export_corpus.py` reads `localized_text` for every field touched here, with
one exception: `translation`/`en` is rendered as `sentence.en or localized_text`. Every `en`
translation row rewritten in this campaign belongs to a `gen-` record whose `sentence.en` is NULL, so
none of them is shadowed by a Layer-A pair; the script checks this on each run and would print a
`~ … sentence.en (Layer A) is set` warning if that ever changed.
