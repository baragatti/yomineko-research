# Grammar record repairs — what was NOT applied

**Campaign:** `scripts/apply_grammar_record_repairs.py` +
`research/derived/repairs/grammar_record_repairs.json` (255 findings landed: 170 `text`, 8 `forms`,
77 `unlink`).
**Sources:** `grammar_accuracy_1.md` .. `_4.md`.
**Scope of the campaign:** per-record corrections expressible as one of three actions — a
`localized_text` field on a grammar point (`formation` / `explanation` / `nuance` / `meaning` /
`form_meanings`, pt-BR or en), `grammar_point.forms_json`, or deleting a `sentence_grammar` row.

Everything below was read, judged, and deliberately left alone. Each entry says why. The four
formation rules missing the う→わ exception in **pt-BR** were already landed by
`scripts/apply_godan_u_exception.py` and are not repeated here; the **en** rows that script never
wrote (gp-105, gp-63, saserareru) WERE repaired by this campaign.

---

## 0. Two things this run itself introduced or corrected — read these first

**`gram:gp-34` formation.en — the table's `old` was mis-transcribed and I corrected it.** The
authored row quoted `"は では (ではなかった). Remember"`; the live DB reads `"is では (ではなかった).
Remember"` — the English word *is*, not the kana は. The finding is real (the field stops dead on the
word "Remember" and the pt-BR counterpart completes the thought), the `new` text already begins
`"is では"`, so the slip was in the `old` snapshot alone. I changed `old` to the byte-exact live value
and the edit applied. Nothing else in the table was altered.

**62 sentences now carry zero grammar tags.** The `unlink` action can only delete a link; it cannot
move one. Several findings say a sentence "belongs with `gram:X`", and re-tagging is not in this
action set, so those sentences are now in the bank with no grammar point attached. `validate.py`
does not check grammar coverage, so no gate caught it — it is a real coverage debt, not a passing
grade. The list is reproducible with:

```
SELECT s.slug FROM sentence s LEFT JOIN sentence_grammar sg ON sg.sentence_id = s.id
WHERE sg.grammar_id IS NULL
```

Named destinations from the reports, for the retag pass: `gram:rareru` (tatoeba-161847,
tatoeba-188098), `gram:naide` (tatoeba-125387, already tagged there before this run),
`gram:you-ni-you-na` (tatoeba-4930, tatoeba-180353), `gram:gp-124` (tatoeba-82971, tatoeba-84691),
`gram:nara` (the four あなたなら carriers), `gram:ta-tokoro` (the six 〜たところだ carriers),
`gram:nakute-wa-ikenai` (tatoeba-173416), `gram:teiru-tokoro` (the three 〜ているところ carriers).

---

## 1. Records where every carrier is off-point — unlinking would empty the record

The hard rule of this campaign is that a record is never left with zero sentences: an unillustrated
point is worse than a mis-illustrated one, because nothing then shows the reader what the rule looks
like. In each of these the diagnosis is accepted and nothing was emitted. They need authored or
re-tagged carriers first, and only then the unlink.

- **`gram:no-naka-de`** (X-1) — 5/5 carriers are spatial 〜の中に/で, not the comparison scope. Real
  repair: re-link the comparison sentences that already exist under `gram:gp-46`
  (スポーツの中でサッカーが一番人気です, 一年の中で夏が一番暑い, クラスの中で彼が一番背が高い), then release
  the five spatial ones. Its corrupted nuance (T-4) WAS fixed.
- **`gram:n3-ta-tokoro`** (X-2) — 6/6 are 〜たところだ "just did", which belongs to `gram:ta-tokoro`
  (n4). This is a change of link owner, not an unlink, and it also needs discovery-reading examples
  (調べたところ、〜が分かった) authored.
- **`gram:n3-to-iu-no`** (X-3) — 0/5 show というのだ. Three are というのは and should migrate to the
  record its own nuance names; というのです examples still have to be authored. The nuance WAS fixed
  (diacritics + the `gid 422` leak).
- **`gram:n3-ppai`** (X-4) — 2/2 are the adverb いっぱい that the nuance excludes. Needs 〜でいっぱい
  carriers first.
- **`gram:n3-nanka`** (X-12) — 3/3 sit outside what the record documented. Instead of unlinking, the
  **formation was rewritten**: it no longer licenses ×行くなんか and now documents 〜てなんかない and the
  hesitation なんか, which are exactly the two uses those three sentences show.
- **`gram:owaru`** (F-06) — 5/5 use 終わる as an independent intransitive verb, none is the masu-stem
  compound. Needs 読み終わる / 食べ終わる / 話し終わる.
- **`gram:gp-62`** (F-07) — 5/5 are 〜なくてもいい / 〜なくていい (permission not to); none shows the causal
  linking negative て-form. Needs お金がなくて… / 時間がなくて… .
- **`gram:gp-98`** (F-08) — 5/5 are sentence-final or embedded interrogative か, which the record's own
  nuance says not to confuse with the vague-quantity か. Needs 何人か来ました / 何回か行ったことがあります.
- **`gram:gp-132`** (F-10) — 5/5 generated carriers are the "someone can see" reading the nuance
  explicitly excludes, and all are in the wrong register for a record tagged formal/written. Needs
  expository carriers (この傾向が見られる). Its nuance parenthesis defect (F-22) WAS fixed.
- **`gram:janai-dewa-nai`** (F-11) — 5/5 are idiomatic derivatives (じゃないか, んじゃない, ものじゃない);
  none shows the basic 学生じゃない an N5 learner needs. The report's remedy is to borrow `gram:gp-33`'s
  sentences, which depends on the gp-33 / janai-dewa-nai merge (owner decision).
- **`gram:n3-da-mono-da`** (F-12) — 4/4 are past-habitual or nominal ものだ, not the whiny reason marker
  だもの; the key looks assigned by surface match on 〜んだものだ. The one correct bank sentence
  (`sent:tatoeba-10107238` 私はあんたのお姉ちゃんだもん) sits on `gram:n3-nda-mon`, and moving it is bound up
  with the merge. Its contradictory gender-register nuance (F-04) WAS fixed.
- **`gram:n3-to-iu-to`** (F-17) — both carriers are the frozen idiom どちらかというと, not the "speaking of
  X" topic use. Needs 日本料理というと寿司 type carriers. Its diacritics WERE fixed.
- **`gram:n3-koto-wa-nai`** (F-09, remainder) — only 見たことはないよ。 was unlinked, as the flat
  contradiction of the record's own nuance. The other four (止まることはない。 / 何も言うことはないの？ /
  何かすることはないの？ / もはや言うことはない。) are existential `[clause こと] + は + ない` rather than the
  modal "no need to"; unlinking them too would empty the record. They need replacing with
  心配することはない / 急ぐことはない / わざわざ行くことはない.

## 2. Findings I disagree with, in whole or in part

- **X-6 `gram:mo`** — I kept 誰も来なかった (the record's own formation documents "small number + も in a
  negative clause", 一人も来なかった; this is the same indefinite + も + negative mechanism) and I kept
  美人でもある on `mo`, whose translation ("Ela também é bonita") is precisely the additive も in the
  label. Only the three that are not the documented particle were unlinked.
- **X-15 `gram:hajimeru` / `gram:tsuzukeru`** — the bare-verb use is not an excluded sense (both
  records mention it), so this is coverage rebalancing, an owner decision, not an unlink.
- **T-5 `gram:gp-92`** — not the same defect. `(Este 以上 ① é o numérico; há outro 以上 que significa
  "já que / uma vez que", de uso diferente.)` is a well-formed parenthesis around a complete sentence
  in both locales; nothing was swallowed.
- **T-7 `gram:n3-koso`** — obsolete finding. The current explanation has no parenthesis in either
  locale, so there is no missing space to fix.
- **F5 `gram:deshou` / `sent:tatoeba-78454`** (「嵐になるだろう。」 against a `register: ["polite"]` record) —
  link kept. The record's own explanation opens by defining でしょう as the polite form of だろう, so the
  sentence shows the same construction in the plain register. The defect here is the register tag,
  which is record-level metadata, not a link error.
- **F5 `gram:n3-koto` / `sent:tatoeba-4901`** (「最近考えることが多過ぎる。」) — link kept. The report's count
  ("4 of 5 off-point") implies it, but no verbatim rationale is given, 考えること reads as the nominalized
  activity as well as a relative-clause head, and unlinking it would drop the record to one example.
- **`gram:gp-82`** (〜とよかった as the past of 〜といい) and **`gram:ba`** ("com o mesmo sujeito") — the
  report itself declined to flag these and I agree; both are defensible and need a native reviewer,
  not a mechanical repair.

## 3. Owner decisions, named out of scope by the assignment

Identity merges and duplicate pairs, re-keying, populating `related`, family membership, and level
tags. Specifically: C1–C5, F1–F2 (the report's own numbering), the six same-level duplicate pairs
(gp-50/hou-ga-ii, gp-54/no-ga-jouzu, gp-145/nakucha, gp-47/yori-hou-ga, gp-77/gp-154, tara/gp-60) and
six cross-level pairs (F7); F-28's four pairs (gp-151/te-shimau-chau, gp-33/janai-dewa-nai,
gp-112/itashimasu, n3-da-mono-da/n3-nda-mon); F8 (`gram:naide` filed n5 against a 2-of-3 source
majority for n4); F-30 (seven points registered at two levels); F16 and F-29 (family membership
contradicting the family's own label, 16 records; the five ように records); F-33 (re-keying `gram:n3-mo`
to `n3-bakari-ka` — the key genuinely misnames the point, ばかりか〜も, not the particle も; its diacritics
WERE fixed); **F-02 partial** (splitting `gram:wa-ga-wa` into two points — I scoped the record to the
contrastive frame in prose instead; its `structure_pattern` `は〜が… は` and `forms_json` `["はが… は"]`
still encode the sub-subject reading and should be revisited with the split).

## 4. Right fix, wrong action set — needs a column or a layer this campaign cannot touch

**`structure_pattern` / `references_json` (grammar_point columns).**
- D4 `gram:n3-sukoshimo-nai` — `forms` is `["すこしもない"]` because `structure_pattern` itself lost its
  medial placeholder (contrast `n3-metta-ni-nai`, which correctly keeps めったに〜ない). The real repair is
  `structure_pattern` → `"すこしも～ない"`; fixing `forms` alone would leave the two disagreeing, which is
  worse than the current consistent-but-wrong state.
- D7 `gram:n3-sono-tame-ni` — `structure_pattern` `"～そのために"` carries a leading tilde the record
  explicitly rules out (its formation puts it between two independent sentences; its
  `steps_unavailable` calls it an invariable sentence-initial connective).
- `gp-148` `refs.label_en = "てすみ"` and `gp-101` `refs.label_en = "はの一つ"` — the same
  placeholder-stripping damage as D4, in `references_json`. Fold into whichever pass fixes
  `structure_pattern`.

**`formation_steps_json` (grammar_point column).**
- E1 — replace-ending token grammar on `sugiru` / `gp-26` / `te-de` (one executor cannot read both
  `て→ちゃ` and `すぎる`).
- E2 — `n3-okagede`'s to-dictionary variant emits 勉強するおかげで, which is not something a speaker
  produces.
- F-32 — `gram:n3-zu-ni` has NO authored step chain; adding one is authoring, not correction.
- F-29 note — `gp-128`'s own `steps_unavailable` argues that a to-dictionary rule would emit
  書くように as an instance of a sense it forbids; that argument stays live against `you-ni-you-na` and
  `n3-you-ni`, whose step encodings I did not touch.

**`steps_unavailable` (grammar_point column).** L-5: obsolete "corrupted record" notes on
`n3-kurai-wa-nai` and `n3-tatoe-temo`. I confirmed the values they refer to are clean today; the two
parenthetical sentences still need removing in another pass.

**Sentence layer (`sentence.jp`, or `localized_text` with `entity_type='sentence'`).**
- B8 — `sent:tatoeba-108153` `translation_literal.pt-BR` reads "pelo que se percebe", teaching the
  ようだ reading on a らしい record; the other three carriers on `n3-rashii` gloss it "pelo que
  parece"/"pelo que dizem". Proposed value: *"Quanto a ele, pelo que dizem, (é) uma pessoa rica."*
- F-2, second half — `sent:gen-a1650baf4ac0` この問題が解けない学生はない must become 〜学生はいない. It was
  unlinked from `gp-102` so the ungrammatical model is not on display, and can return once rewritten.
- F6 `gram:gp-93` (以下) — four generated sentences write 十度いか / 五十点いか / 千円いか / 三歳いか in kana,
  colliding with いか = 烏賊/医科 and contradicting the record, which writes 以下 in kanji throughout.
  Needs a sentence rewrite plus a `structure_pattern` change.
- F-25 `gram:sore-ni` — four generated carriers separate their clauses with an ASCII space
  (彼は親切です それに頭もいいです) where the record's own formation prescribes 。 and 、.
- `sent:gen-89350d9e81cf` 犬は人間の友達の一つだ on `gp-101` — NOT unlinked: it does instantiate
  〜は〜の一つだ, so it is not the "different point entirely" class. But with the A2 formation fix landed
  it now visibly contradicts the record (友達 takes 一人, not 一つ), and 友達の一つ is odd Japanese anyway.
  It needs a sentence rewrite.

**`forms_json` + `form_meanings` together.** X-9 `gram:gp-42` — 3/5 carriers are the polite refusal
けっこうです. The indicated repair is a second `forms` entry with its own gloss, but `forms_json` holds
only the form list (`["けっこう"]`) and the gloss lives in a separate `localized_text` row (`form_meanings`,
a form→text map). The `forms` action here carries only the list, so adding the form without its gloss
would recreate defect S-2. Unlinking the three instead would discard correct real sentences and leave
the point with two.

## 5. Systemic / bulk work, not per-record corrections

- S-1 .. S-7 and F12 — points with no sentence, `forms[].meaning` null across the whole n3 block,
  empty `related`, null `refs`, duplicates, the n3-ppai re-key, missing `steps_unavailable`.
- F-26 — `forms[].meaning` empty in both locales on 34 slice records (133 corpus-wide). The `label`
  field can seed the backfill. The assignment limited `forms[]` work to the placeholder-stripping
  cases.
- F11 — the report recommends a diacritics sweep of all of `n3.json` rather than point fixes. I
  repaired every record it named verbatim (and `gram:n3-to-iu-koto-da`, which it named only as an
  out-of-slice example); the registry-wide sweep is still owed.
- F13 / F-27 — sentence coverage gaps: zero carriers on `n3-koto-wa-ga`, `n3-moshikasuru-to-kamoshirenai`,
  `n3-sore-to`, `n3-kara-ni-kakete`, `n3-kiri`, `n3-koto-da`, `n3-mattaku-nai`; one or two on eleven
  more. Note that **`n3-koto-wa-ga` is now a repaired rule with no example to confirm it.**
- F-31 — `related[]` is empty on all 124 slice records, and prose leans on it (`naide-kudasai` "do item
  anterior", `nakute-wa-ikenai` "veja o item anterior", `gp-58` "ver próximo ponto"). Where a target
  was nameable I rewrote the prose to name it (`nakereba-naranai`, `gp-54`, `te-kudasai`, `n3-nado`,
  `n3-to-ittemo`, `n3-to-iu-no-wa`, `n3-tokoro-ga`); the rest wait on `related` existing.
- F-01 note — the to-nai-stem observation (it means the ない-form minus its final い, not the mizenkei)
  belongs in the step-op contract documentation, not in a record.

## 6. Small things noticed while editing, left alone on purpose

- `gram:gp-142` nuance.pt-BR "mudanças de tempo" is ambiguous between weather and time where
  nuance.en says "weather". Not named by any report; left while fixing that field's parenthesis.
- `gram:n3-mo` formation.pt-BR "na+adjetivo" reads as a typo for "adjetivo-na". Not a diacritic, not
  named; left while fixing that field's diacritics.
- `gram:gp-143` explanation "(detalhado no próximo item)" and the `te-kara` / `mitai-na` prose
  cross-references — the C2 dangling-reference half. Rewriting them only makes sense together with
  populating `related`.
