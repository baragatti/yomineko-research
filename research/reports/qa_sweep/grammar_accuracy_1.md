# QA sweep — grammar accuracy, part 1/4

**Slice:** `corpus/grammar/{n5,n4,n3}.json`, records at index `% 4 == 0` in concatenated n5→n4→n3 order.
**Records checked:** 124 (n5: 38, n4: 53, n3: 33) — every record read in full.
**Excluded by instruction:** sentence `structure_explanation` fields (being re-authored elsewhere).
**Method:** for each record, explanation (pt-BR + en) vs. the actual grammar point; `formation` /
`formation_steps` executed by hand against the declared bases; `forms` and `structure_pattern` checked as
Japanese; `nuance` checked against `explanation`; `related` / `refs` / `families` resolved; and each point
cross-checked against the sentences whose `grammar` array carries its key.

Findings are ordered by severity. Class A first: a wrong formation rule teaches learners to **produce**
wrong Japanese.

---

## A. Formation rules that generate incorrect Japanese

### A1 — `gram:gp-105`, `gram:gp-63`, `gram:saserareru`: the godan rule breaks on う-final verbs

Three records give the "swap the final syllable for the あ-row" rule and omit the う→わ exception.

`gram:gp-105` (causative), `formation.pt-BR`:
> Verbos do grupo 1 (godan, terminam em 〜う): troca-se a sílaba final pela linha 〜あ + せる. Ex.: 行(い)く→行かせる, 飲(の)む→飲ませる, 待(ま)つ→待たせる.

`gram:gp-63` (passive), `formation.pt-BR`:
> Grupo 1 (godan): troca-se a sílaba final em -u por -areru: 書く→書かれる, 読む→読まれる, 話す→話される.

`gram:saserareru` (causative-passive), `formation.pt-BR`:
> Grupo 1 (godan): troca-se a última sílaba pela linha あ + せられる (書く → 書かせられる)

**Why it is wrong.** For verbs whose dictionary form ends in う the あ-row slot is わ, not あ. A learner
applying the rule literally to 買う / 言う / 会う / 使う produces ×買あせる, ×買あれる, ×買あせられる instead of
買わせる, 買われる, 買わせられる. All three records pick examples (行く・飲む・待つ・書く・読む・話す) that
sidestep the one class where the rule fails, so nothing in the record exposes the gap. This is a
production error, not a comprehension one.

**The corpus already knows the exception**, which makes the omission an internal inconsistency:
`gram:gp-7` (`formation.pt-BR`) says *"exceção: verbos em -う viram -わ (買う kau → 買わない, não 買あない)"*,
and `gram:ukemi-kei` — the second, unlinked passive record — says
*"Atenção: verbos terminados em う viram わ: 言う→言われる (いわれる)"*.

**Proposed fix.** Add one clause to each of the three, mirroring `gram:ukemi-kei`'s wording:
`gp-105`: "… + せる. **Exceção: verbos terminados em う viram わ (買う → 買わせる, não ×買あせる).** Ex.: 行く→行かせる …"
`gp-63`: "… -areru … **Exceção: 買う → 買われる (não ×買あれる).**"
`saserareru`: "… + せられる … **Exceção: 買う → 買わせられる.**"
Also add a う-verb to each `formation_steps` example set so the case is visible.

---

### A2 — `gram:gp-101`: 一人 (ひとり) is the counter for **people**, not for animals

`formation.pt-BR`:
> Para pessoas ou animais, use 一人 (ひとり) no lugar de 一つ.

**Why it is wrong.** 一人 counts human beings only. Animals take 一匹 (small), 一頭 (large), 一羽 (birds and
rabbits). Telling a beginner to say 犬の一人 is a straightforward factual error, and it is also internally
inconsistent: the record's own `nuance.pt-BR` narrows it back to people only —
*"para pessoas, use 一人 (ひとり), não 一つ"* — so the two fields contradict each other.

The record's own linked sentence contradicts it a third time. `sent:gen-89350d9e81cf`
(`犬は人間の友達の一つだ` / "O cachorro é um dos amigos do ser humano") uses 一つ for an animal, exactly what
the formation rule forbids. (Independently, 友達の一つ is odd Japanese; 友達 takes 一人.)

**Proposed fix.** Replace with: *"Para pessoas, use 一人 (ひとり) no lugar de 一つ (山田さんは友達の一人だ). Para
animais o contador varia com o bicho (一匹 / 一頭 / 一羽), então 一つ não serve nesses casos."* And retag or
rewrite `sent:gen-89350d9e81cf`.

---

### A3 — `gram:gp-56` (くれる): the ます-form is not irregular

`formation.pt-BR`:
> Conjuga como る-verbo, mas com a forma ます um pouco irregular: くれる→くれます→くれない→くれて.

**Why it is wrong.** Every form the sentence lists is the fully regular ichidan output: くれ + ます, くれ + ない,
くれ + て. There is nothing irregular in that chain, so the record flags a difficulty that does not exist and
will make learners second-guess a regular verb. くれる *is* irregular, but in a place the record never
mentions: the imperative is くれ, not ×くれろ (cf. 見る → 見ろ), and the honorific counterpart is くださる →
くださいます (not ×くださります).

**Proposed fix.** *"Conjuga como る-verbo: くれる→くれます→くれない→くれて. A irregularidade fica no imperativo,
que é くれ (não ×くれろ): 'ちょっと待ってくれ'. A versão respeitosa くださる também é irregular no ます
(くださいます, não ×くださります)."*

---

### A4 — `gram:n3-ni-shite-wa`: a formation line the record itself declares broken and never fixed

`formation.pt-BR`:
> Liga-se à forma simples: verbo-simples + にしては, adjetivo-い + にしては, adjetivo-な (sem な) + にしては, substantivo + にしては.

The record's own `steps_unavailable` says, verbatim:
> The record's line 'adjetivo-な (sem な) + にしては' generates 静かにしては, a well-formed string whose live
> reading is 静かに + して + は (the て-form of 静かにする plus は […]), not the surprise-against-a-standard
> construction taught here […] **The record's な-adjective formation line needs human review.**

**Why it matters.** The defect was diagnosed at authoring time, the step list was suppressed to avoid
emitting it — but the learner-facing `formation` text still carries the bad rule. A learner following it
produces 静かにしては expecting "for something quiet…", and a reader parses "as for making it quiet…". The
`steps_unavailable` note is an engineering field; nothing the learner sees warns them.

**Proposed fix.** Drop the な-adjective branch from `formation` (にしては with a bare な-adjective is not a
usable teaching case at N3) and keep verb / い-adjective / noun. If the branch is kept, it must be
disambiguated in prose. This one needs the teacher, not a mechanical edit.

---

## B. Sentence links that contradict the record they are attached to

Every item below was checked against the full `grammar`-array membership, not a sample.

### B1 — `gram:gp-95` (ずっと ①, durative): 3 of 5 sentences are the sense the record explicitly excludes

`nuance.pt-BR`:
> Atenção: ずっと tem um segundo uso (não este) como intensificador de comparação, "muito mais" (ずっと高い, "bem mais caro"). Aqui, no sentido ①, é durativo ("o tempo todo")

All five sentences carrying `gp-95`:

| sentence | jp | pt | sense |
|---|---|---|---|
| `sent:tatoeba-158256` | 私は駅までずっと走った。 | Eu corri o caminho inteiro até a estação. | ① durative ✅ |
| `sent:tatoeba-191155` | 以来ずっと友人です。 | Somos amigos desde então. | ① durative ✅ |
| `sent:tatoeba-171774` | 今日はずっと気分がよい。 | Hoje estou me sentindo **muito melhor**. | ② comparative ❌ |
| `sent:tatoeba-173719` | 工場よりずっといいよ。 | É **bem melhor** que a fábrica. | ② comparative ❌ |
| `sent:tatoeba-179724` | 金は水よりずっと重い。 | O ouro é **muito mais** pesado que a água. | ② comparative ❌ |

The `translation_literal` fields of the last three even read *"muito mais"*, so the mis-tag is visible in
the corpus's own gloss. There is **no ② record to move them to**: the neighbouring `gram:gp-96` is
だいたい, and `ずっと` appears in only one other record (`gram:aida`, incidentally).

**Proposed fix.** Untag the three comparative sentences from `gp-95`, and open a `ずっと ②` record
(comparative intensifier, 〜より + ずっと + adjective) to receive them. Until that record exists, the point is
taught with 60% counter-examples.

### B2 — `gram:you-da` (〜ようだ): 5 of 6 sentences contain no ようだ at all

`nuance.pt-BR`:
> A grande armadilha para brasileiros: o 〜よう da forma volitiva (食べよう) se parece na grafia, mas prende-se ao verbo e propõe uma ação, enquanto 〜ようだ vem depois de uma oração inteira e comenta uma aparência.

The six sentences tagged `you-da`:

- `sent:tatoeba-74772` 明日雨のようだががんばろう。 — the real 〜ようだ ✅
- `sent:tatoeba-11801342` ここにいようと思う。 — volitional + と思う ❌
- `sent:tatoeba-193348` もっとお金をためようと思うんだ。 — volitional + と思う ❌
- `sent:tatoeba-235716` １度に２つの事をしようと思うな。 — volitional + と思う ❌
- `sent:tatoeba-79760` 夜が明けようとしている。 — 〜ようとしている ❌
- `sent:tatoeba-81579` 本題からそれないようにしましょう。 — 〜ようにしましょう ❌

The record is illustrated almost entirely by the exact confusable it warns against. The three
`ようと思う` sentences are already correctly tagged to `gram:you-to-omou`; the tag on `you-da` is a
surface `よう` match.

**Proposed fix.** Remove `you-da` from all five. Pull ようだ examples from the bank instead (the pattern
appears in 〜ようだ / 〜ようです sentences elsewhere).

### B3 — `gram:gp-63` (passive): 3 of 7 sentences are not passive

`nuance.pt-BR`:
> Pegadinha: as formas do Grupo 2 (〜られる) coincidem com o potencial ("poder fazer"); só o contexto e a partícula distinguem.

- `sent:tatoeba-161847` 手に入れられると思いますよ。 / "Acho que você **consegue**, viu." — potential ❌
- `sent:tatoeba-188098` 何かすぐ食べられるものある？ / "Tem alguma coisa que **dê pra** comer já?" — potential ❌
- `sent:tatoeba-84315` 父上、何をして**おられる**のか。 / "Pai, o que **o senhor** está fazendo?" — honorific おられる ❌

The remaining four (`gen-113cd2b42397`, `gen-41c59e916001`, `gen-b724a8178171`, `tatoeba-186610`) are
genuine passives. The Portuguese translations confirm the diagnosis in each failing case. Attaching
potential and honorific examples to the passive record makes the record's own warning unlearnable.

**Proposed fix.** Untag the three; move the two potential ones to `gram:rareru` (which teaches both senses)
and drop the おられる one from this point entirely.

### B4 — `gram:gp-83` (〜まい): 2 of 5 sentences contain no まい

- `sent:gen-38247e47e14c` 彼女は天使**のように**やさしい / "Ela é gentil feito um anjo." ❌
- `sent:gen-c1a790a4c31e` 雪**のように**白い花が咲いた / "Floresceu uma flor branca como a neve." ❌

This is a **known, half-repaired defect**. The record's own `steps_unavailable` states:
> Separately, the 〜のように / 〜のような half of this record is deliberately not encoded here: the record's
> own structure_pattern identifies it as a concatenation bug and orders it stripped, and gram:gp-153 /
> gram:gp-154 / gram:gp-77 already carry those rules.

The prose and `structure_pattern` were cleaned of the のように contamination; the sentence links were not,
so the point labelled *"decerto não / recusa firme (〜まい)"* still ships two のように sentences.

**Proposed fix.** Retag `gen-38247e47e14c` and `gen-c1a790a4c31e` to `gp-153` / `gp-154` / `gp-77` as
appropriate, per the record's own note.

### B5 — `gram:cha-ikenai-ja-ikenai`: 4 of 5 sentences teach obligation, not prohibition

The record teaches ちゃいけない / じゃいけない = "não pode / é proibido", derived by て→ちゃ.

- `sent:tatoeba-174758` 言っちゃいけないんだけど。 — prohibition ✅
- `sent:tatoeba-3357795` 今日売ら**なくちゃ**いけないんだ。 / "**Tenho que** vender isso hoje." ❌
- `sent:tatoeba-8883784` 本当に行か**なくちゃ**いけないの？ / "Você realmente **tem que** ir?" ❌
- `sent:tatoeba-9101504` それをし**なくちゃ**いけないって… / "Você sabe que **precisa** fazer isso" ❌
- `sent:tatoeba-9781663` そこには俺が行か**なくちゃ**いけないんだ。 / "Sou eu que **tenho que** ir lá." ❌

**Why it is wrong.** 〜なくちゃいけない is not this record's pattern: it derives from なくては (negative +
ては), not from the て-form via て→ちゃ, and it means the opposite (obligation, not prohibition). The
corpus has dedicated records for it — `gram:gp-52`, `gram:nakucha`, `gram:gp-145`. Four of the five
examples for a prohibition point demonstrate obligation.

**Proposed fix.** Move the four to `gp-145` (なくちゃいけない) and source new ちゃいけない/じゃいけない
examples (行っちゃいけない, 食べちゃだめ, 触っちゃいけない).

### B6 — `gram:de` (particle で): at least 3 of 8 sentences contain no particle で

- `sent:tatoeba-1057336` **でも**なん**で**？ / "Mas por quê?" — でも "but" + なんで "why", neither is the particle ❌
- `sent:tatoeba-778974` なん**で**？ / "Por quê?" — same ❌
- `sent:tatoeba-125387` 諦め**ないで**。 / "Não desiste!" — ないで, the negative て-form ❌

`sent:gen-8129586afea1` (盾で体を守る) and `sent:tatoeba-78316` (陸路では…) are correct means-で. The rest
(また後で, それでいい, それで十分) are lexicalised. The tag was applied by substring match on `で`.

**Proposed fix.** Untag the three clear false positives. Since で is a core N5 particle, this record
deserves hand-picked examples for each of its four documented senses (place of action, means, material,
cause) rather than string matches.

### B7 — `gram:n3-you-ni-shimashou`: `sent:tatoeba-123214` is a different construction

`sent:tatoeba-123214` 内訳は**どのように**しましょう？ / "Como você gostaria do detalhamento?"

**Why it is wrong.** This is どのように ("in what way") + しましょう ("shall we do"), not 〜ようにしましょう
("let's make an effort to"). The pt translation confirms it asks *how*, not proposing a habit. Surface
match on `ようにしましょう`.

**Proposed fix.** Untag.

### B8 — `gram:n3-rashii`: one literal gloss teaches the opposite of the record

`sent:tatoeba-108153` 彼は金持ちらしい。 — `translation_literal.pt-BR`:
> Quanto a ele, parece (**pelo que se percebe**) uma pessoa rica.

**Why it is wrong.** The record's `nuance.pt-BR` draws the whole distinction on this axis:
*"Diferente de ようだ/みたいだ (impressão baseada no que você mesmo percebe)"* — らしい is precisely **not**
direct perception, it is indirect/hearsay. "pelo que se percebe" hands the learner the ようだ reading. The
other three sentences on the same record gloss it correctly as *"pelo que parece"* / *"pelo que dizem"*,
so it is also inconsistent within one set.

**Proposed fix.** `"Quanto a ele, pelo que dizem, (é) uma pessoa rica."`

---

## C. Structural and graph defects

### C1 — Family labels do not describe family membership

`families` on a grammar record points at a labelled `function_set` in `corpus/families/families.json`.
The labels are thematic; the membership is not. Three complete member lists, resolved to labels:

**`grp:gram-n5-passado` — "Gramática: Passado polido e nuances"** (6 members, **0** about the past):
あそこ (`gp-11`), どれ (`gp-38`), ここ (`gp-9`), partícula ね, partícula よ, より〜ほうが.

**`grp:gram-n5-te-form` — "Gramática: A forma て e seus usos"** (9 members, 5 unrelated to the て-form):
どうして, どうやって, たくさん (`gp-43`), って, そして — alongside the three real ones (`te-form`, `gp-26`,
`gp-144`) and `nakucha`.

**`grp:gram-n5-perguntas` — "Gramática: Perguntas e demonstrativos"**: contains きらい (`gp-22`,
"não gostar de") and くれる (`gp-56`, the giving verb) — neither a question nor a demonstrative.

From my slice alone, the same mismatch on: なぜ → *"Verbos: dicionário + ます; を e が"*; 一番 and
たり → *"Comparações, desejos e preferências"*; になる, ないといけない, すぎる, てある → *"Lugar, tempo e
direção: で/に/へ/と"*; 〜し (`shi`) and 〜てすみません (`gp-148`) → *"Voz passiva"*; ほかに → *"Dar e receber"*;
〜くなる (`gp-79`), ずっと, 頃/ごろ, と言われている → *"Keigo"*; the passive `gp-63` → *"Potencial"*;
間に → *"Orações relativas"*; たり〜たりする → *"Adjetivos い e な"*.

**Why it matters.** The pattern looks like round-robin bucket-filling by record id (family 59 receives ids
1,2,3,4,6,15,20,21…; family 60 receives 8,33,36,43,44,54,55,73; family 61 receives 11,12,14,45,75,77,125),
with the labels authored separately. Any lesson, exercise set, or review queue built on `families` will
group unrelated points under a promise it does not keep, and CLAUDE.md §1.7 treats these links as design
tests the corpus must answer.

**Proposed fix.** Re-derive membership from `nuance_tags` + `structure_pattern` semantics, or drop the
thematic labels and rename the sets neutrally until membership is authored. Do not ship both.

### C2 — `related` is populated on 4 of 496 records, while the prose leans on cross-references

Corpus-wide, only `gram:de` (`["ni"]`) and `gram:ni` (`["de"]`) have a non-empty `related`. Everything else
is `[]`. Meanwhile the learner-facing prose points at other records by prose, not by id:

- `gram:gp-143`, `explanation.pt-BR`: *"…e fecha com する no fim da frase **(detalhado no próximo item)**."*
  There is no "next item": `gp-143` is id 25 and the たりする record is `gp-41`, id 57.
- `gram:te-kara`, `formation.pt-BR`: *"**A formação da forma-て está no ponto 〜ている.**"* — no link.
- `gram:mitai-na`, `formation.pt-BR`: *"…antes de verbo/adjetivo use みたいに **(ver item seguinte)**."*
- `gram:n3-tokoro-ga`, `nuance.pt-BR`: *"Para o sentido de 'estive a ponto de', **veja ところだった (gid 428)**."*

**Why it matters.** "Próximo item" and "item seguinte" are ordering-dependent in a corpus addressed by
stable id, so they are already wrong on the page; "(gid 428)" exposes an internal numeric id to the learner
and still is not a link.

**Proposed fix.** Populate `related` for each of these and rewrite the prose to name the point, not its
position: `gp-143` → `related: ["gp-41","gp-144"]` and *"…fecha com する (veja 〜たりする)"*; `te-kara` →
`related: ["te-form"]`; `mitai-na` → `related` to the みたいに record; `n3-tokoro-ga` → `related` to
ところだった and *"veja ところだった"* with the gid removed.

### C3 — Duplicate grammar records, unlinked, sometimes contradicting each other

Grouping the corpus by normalised `structure_pattern`, 14 duplicate groups touch my slice. None of the
duplicates cross-links to its twin (see C2).

| pattern | records | note |
|---|---|---|
| てほしい | `gp-152` (n4/212), `te-hoshii` (n4/326), `n3-te-hoshii` (n3/415) | three records, two levels |
| ように | `gp-128` (n4), `n3-you-ni`, `n3-you-ni-2`, `n3-you-ni-3` | four records |
| めったにない | `n3-metta-ni-nai` (468), `n3-metta-ni-nai-2` (469) | **adjacent ids, same file, same point** |
| てすみません | `gp-148` (n4/208), `te-sumimasen` (n4/336) | same level; families "passiva" vs "experiencia" |
| すこしもない | `gp-103` (n4/170), `n3-sukoshimo-nai` (n3/388) | |
| ても | `temo` (n4/340), `n3-temo` (n3/416) | same point, two levels |
| ないで | `naide` (n5/103), `n3-naide` (n3/371) | n5 vs n3 |
| まで | `made` (n5/93), `n3-made` (n3/463) | n5 vs n3 |
| の | `no` (n5/117), `n3-no` (n3/450) | n5 vs n3 |
| ばかり / まま / らしい / てみる / ないと | n4 + n3 pairs | |

Plus a same-point pair the pattern key does not catch: **`gram:gp-63` and `gram:ukemi-kei` are both the
passive**, and they disagree — `ukemi-kei` carries the う→わ exception (A1), `gp-63` does not; `gp-63` sits
in `grp:gram-n4-potencial`, `ukemi-kei` in `grp:gram-n4-passiva`. Similarly `gram:gp-45` (n5, になる/くなる)
and `gram:gp-79` (n4, くなる/になる) are the same point at two levels, and `gram:gp-121` / `gram:shi` are both
the 〜し particle at n4, in different families.

**Why it matters.** A learner meeting てほしい three times at two levels, or ても at n4 and again at n3, has
no way to know it is the same point; a validator cannot tell which record is canonical; and where the twins
disagree (`gp-63` vs `ukemi-kei`) one of them is teaching a defective rule that the other has already fixed.

**Proposed fix.** Pick a canonical record per pattern, merge the useful content into it, and either delete
the twin or convert it to an alias with `related` pointing at the canonical id. `n3-metta-ni-nai-2` (469)
looks like a straight ingestion duplicate and can go.

### C4 — The n3 tier is structurally a different schema from n5/n4

Across all 132 n3 records (33 in my slice), every one of the following holds — and holds for **zero** of the
364 n5/n4 records:

| field | n5/n4 | n3 |
|---|---|---|
| `refs` | populated (0 null) | `null` — 132/132 |
| `families` | populated (0 empty) | `[]` — 132/132 |
| `forms[].meaning` | `{"pt-BR": …, "en": …}` | `{"pt-BR": null, "en": null}` — 133 forms corpus-wide |
| `register` | plain / polite / casual / colloquial / written / formal / humble / honorific / literary / masculine / feminine | **`neutral`** (123 uses) — a value used nowhere in n5/n4 |
| `level_sources` | up to 3 (jlptsensei / bunpro / tanos) | one only: `{"hanabira": "n3"}`, `level_confidence: 0.34` |

Concretely: `gram:n3-ageru`'s only `form` is `～上げる` with `meaning: {"pt-BR": null, "en": null}`; a
consumer rendering the forms table for any n3 point gets a blank gloss column.

**Why it matters.** Three separate contract violations. `families: []` on the entire n3 tier means a third
of the grammar corpus is outside the cross-reference graph CLAUDE.md §1.7 requires. `register: ["neutral"]`
is an enum value the rest of the corpus does not use, so any consumer switching on register has an
unhandled case. And §1.5 requires ≥3 independent community lists per level tag — every n3 record rests on
one, which `level_confidence: 0.34` records honestly but does not repair. (n3 is outside the spec's
N5/N4 scope, so this is flagged as scope/consistency, not as a broken promise.)

**Proposed fix.** Either bring n3 up to the n5/n4 contract (populate `forms[].meaning`, assign families,
map `neutral` onto the existing register enum, add ≥2 more level sources), or mark the whole tier
explicitly as a lower-tier import in the schema so consumers and validators can branch on it. Silent
divergence is the worst of the three.

### C5 — 17 grammar points have no example sentence at all

Corpus-wide 17 of 496 points have an empty `grammar` back-reference; all 17 are n3. Three are in my slice:
`gram:n3-moshi-tanara`, `gram:n3-sukoshimo-nai`, `gram:n3-tokoro-ga`. My slice's distribution is otherwise
healthy (median 5 sentences per point), so this is a tail, not a systemic gap.

**Proposed fix.** Source or generate at least two sentences per orphaned point; `n3-sukoshimo-nai` can
borrow from its n4 twin `gp-103` (see C3) once they are merged.

---

## D. Learner-facing text defects

### D1 — `gram:gp-34`: `formation.en` is truncated mid-sentence

Current `formation.en` ends:
> …the version a bit more formal than じゃ is では (ではなかった). **Remember**

Nothing follows. The pt-BR counterpart completes the thought: *"Lembre que じゃ é a contração coloquial de
では."*

**Proposed fix.** `… (ではなかった). Remember that じゃ is the colloquial contraction of では.`

### D2 — Misplaced closing parenthesis swallowing one or more sentences (9 instances in slice)

A `(` opens mid-sentence and the matching `)` lands at the very end of the field, pulling unrelated
sentences inside the parenthetical. Parenthesis counts balance, so a bracket-matching validator misses it.

| record | field | current tail |
|---|---|---|
| `gp-143` | `formation.pt-BR` | …seguem as regras da forma た **(**読んだ → 読んだり … Padrão típico: AたりBたり + する.**)** |
| `gp-143` | `formation.en` | same shape |
| `gp-8` | `nuance.en` | …don't use 'you' constantly **(**Japanese prefers to omit the subject.**)** |
| `ya` | `nuance.en` | や only links nouns **(**don't use it to link clauses or verbs. It's a neutral register, fitting speech and writing.**)** |
| `gp-148` | `nuance.pt-BR` | …não tente colocar o verbo no passado antes do て. Em situações sérias… prefira 申し訳ありません.**)** |
| `gp-63` | `nuance.en` | …don't translate it literally **(**capture the sense of 'to suffer/be harmed by.' Remember that the agent takes に, not を.**)** |
| `gp-67` | `formation.pt-BR` / `.en` | …geralmente seguido de vírgula **(**〜。また、〜。 É comum em texto escrito e formal para encadear ideias.**)** |
| `o-kudasai-2` | `nuance.pt-BR` | …Lembre da regra お vs ご **(**errar isso chama atenção. Não confunda com a forma humilde お〜する… Registro polido/formal.**)** |

The pt-BR of `ya` and the en of `o-kudasai-2` are punctuated correctly, which shows the intended shape in
each case.

**Proposed fix.** Close each parenthetical at its real end. `ya.en` → *"…or verbs). It's a neutral
register, fitting speech and writing."*; `gp-8.en` → *"…(Japanese prefers to omit the subject)."*; and so on.

### D3 — Authoring-pipeline residue exposed to learners

`gram:gp-152`, `forms[0].meaning.pt-BR` (the string a forms table renders):
> querer que alguém faça (na verdade 〜てほしい; **a grafia tem erro de digitação**)

and `explanation.pt-BR` closes with:
> A grafia **"のようてほしい" do material** tem um erro de digitação; o ponto real é 〜てほしい.

`gram:n3-tokoro-ga`, `nuance.pt-BR` opens:
> **Atenção ao seed:** ところが encabeça uma nova frase…

and closes:
> Para o sentido de 'estive a ponto de', veja ところだった **(gid 428)**.

**Why it is wrong.** These reference an upstream ingestion artefact ("o material", "の ようてほしい"), the
pipeline's own vocabulary ("seed"), and an internal numeric id ("gid 428"), none of which the learner can
see or act on. The `gp-152` note also occupies the `forms[].meaning` slot, so the confusion appears in the
compact forms table, not just in prose.

**Proposed fix.** `gp-152` `forms[0].meaning.pt-BR` → *"querer que alguém faça (algo)"*; strip the last
sentence of its `explanation`. `n3-tokoro-ga` → *"Atenção: ところが encabeça uma nova frase…"* and
*"…veja ところだった"*, with a real `related` entry (C2).

### D4 — `forms[].form` mangled where the pattern has a medial placeholder

`forms[].form` appears to be `structure_pattern` with `～` / `〜` / `[A]` stripped. Stripping a **leading**
`～` is harmless (`～たり` → `たり`). Stripping a **medial** one concatenates two halves into a string that
is not the form:

| record | `structure_pattern` | `forms[].form` | problem |
|---|---|---|---|
| `gp-148` | `～てすみません` | **`てすみ`** | truncated to a non-word |
| `o-kudasai-2` | `お～ください` | **`おください`** | circumfix collapsed; ×おください is not a form |
| `gp-101` | `～は～の一つだ` | **`はの一つだ`** | ×はの一つだ |
| `gp-121` | `し～し` | **`しし`** | ×しし |
| `gp-41` | `たり～たりする` | **`たりたりする`** | ×たりたりする |
| `no-naka-de-a-ga-ichiban` | `の中で[A]が一番` | **`の中でが一番`** | ×の中でが一番 |
| `gp-133` | `〜でも 〜でも` | `でも でも` | stray space |
| `n3-sukoshimo-nai` | `すこしもない` | `すこしもない` | the *pattern itself* lost its medial `～` (cf. `n3-metta-ni-nai`, which correctly keeps `めったに～ない`) |

`gp-148`'s `refs.label_en` is likewise `"てすみ"`.

**Why it matters.** These are the strings a forms table, a flashcard front, or an exercise stem renders as
"the form". Six of them are not Japanese.

**Proposed fix.** Keep the placeholder in `forms[].form` (`〜は〜の一つだ`, `お〜ください`, `し〜し`,
`たり〜たりする`, `の中で[A]が一番`, `〜てすみません`), and repair `n3-sukoshimo-nai`'s
`structure_pattern` to `すこしも～ない`.

### D5 — pt-BR missing diacritics: 13 occurrences across 6 records, all n3

Zero occurrences in the 91 n5/n4 records of my slice.

| record | field | current | should be |
|---|---|---|---|
| `n3-bakari` | `formation` | "ばかりだ **apos** forma-ta" | após |
| `n3-bakari` | `formation` | "ばかりに = '**so** por causa de'" | só |
| `n3-bakari` | `nuance` | "parecido com o '**so** faz'" | só |
| `n3-bakari` | `nuance` | "que também **e** '**so**/apenas' mas **e** neutro" | é … só … é |
| `n3-bakari` | `nuance` | "repetição **incomoda** ou **predominancia**" | incômoda … predominância |
| `n3-ni-kanshite` | `formation` | "quase **sinonima**: について" | sinônima |
| `n3-ni-kanshite` | `nuance` | "posição **fisica**"; "o sentido **e** exclusivamente" | física … é |
| `n3-temo` | `nuance` | "o **nucleo** **e** a ideia de contrariedade" | núcleo … é |
| `n3-to-iu-koto-da` | `nuance` | "boato **e** mais formal"; "comum em **noticias**"; "'**ja** que **e** assim'" | é … notícias … já que é |
| `n3-to-iu-yori` | `nuance` | "não **e** uma comparação"; "qual **rotulo**"; "não qual **e** maior" | é … rótulo … é |
| `n3-tokoro-ga` | `formation` | "**E** uma conjunção no **inicio** de oração" | É … início |

**Why it matters.** `design/translation_style.md` makes pt-BR the product locale; unaccented `e` for `é`
and `so` for `só` change the word, not just the look ("e" = and, "é" = is; "so" is not Portuguese).

**Proposed fix.** Mechanical, listed above. Worth adding a diacritic check to the validator suite since the
defect is confined to one ingestion tier and will recur.

### D6 — `gram:gp-105`: pt-BR is missing the opening sentence the en has

`nuance.en`:
> **It catches Brazilians: the choice between に and を changes the tone.** を can sound more like 'to force,'…

`nuance.pt-BR`:
> を pode soar mais como "forçar", enquanto に tende a "mandar" ou "deixar"; …

**Why it matters.** pt-BR is the locale learners read. Without the lead, the field opens on a contrast whose
subject has never been introduced — the reader has no antecedent for what "を pode soar mais como 'forçar'"
is being contrasted against or why it matters.

**Proposed fix.** Prepend: *"Pega os brasileiros: a escolha entre に e を muda o tom."*

### D7 — `gram:n3-sono-tame-ni`: `structure_pattern` claims an attachment the record denies

`structure_pattern`: `～そのために`. The record's `formation.pt-BR` says it is used *"entre duas orações
independentes: Frase 1 … + ponto final + そのために + Frase 2"*, and its `steps_unavailable` calls it an
*"Invariable sentence-initial connective"*. The leading `～` says something attaches in front of it, which
is exactly what the record rules out (and it is what distinguishes そのために from the 〜ために that does
attach to a verb — a contrast the record itself draws).

**Proposed fix.** `structure_pattern: "そのために"` (no tilde).

---

## E. Machine-consumption defects in `formation_steps`

### E1 — `replace-ending` uses two incompatible token grammars

The op appears 21 times corpus-wide. Most records encode the token as *from→to*:

- `cha-ikenai-ja-ikenai`: `て→ちゃ`, `で→じゃ` · `gp-151`/`te-shimau-chau`: `て→ちゃう` · `sa`/`n3-sa`: `い→さ`
- `sou-ni-sou-na`: `い→そう` · `te-oku`/`n3-toku`: `て→とく`, `で→どく` · `n3-chatta`: `て→ちゃった`

Three encode only the *replacement*:

- `gram:sugiru`: `{"op":"replace-ending","token":"すぎる"}` → `高すぎる`
- `gram:gp-26` and `gram:te-de`: `{"op":"replace-ending","token":"くて"}` → `高くて`

**Why it matters.** An executor that reads the token as `from→to` cannot process `すぎる`; one that reads it
as "replace the final kana with this" mis-executes `て→ちゃ`. The field is the machine-readable half of the
formation contract, so it has to have one grammar. Both variants happen to yield the right surface today
only because the examples are hard-coded alongside them.

**Proposed fix.** Normalise the three outliers to arrow form: `sugiru` → `い→すぎる`; `gp-26` / `te-de` →
`い→くて`. Then a single executor handles all 21.

### E2 — `gram:n3-okagede`: a step variant emits a form the record never teaches and that is not idiomatic

`formation_steps` variant 2: `base=verb, to-dictionary → append おかげで`, `example: 勉強するおかげで`.

**Why it is wrong.** The record's own `formation.pt-BR` gives only *"verbo na forma comum (casual) +
おかげで"* with the example 勉強した**おかげで** (past). おかげで attributes a result to a completed cause or a
standing state, so the natural forms are 勉強したおかげで / 勉強しているおかげで; the bare dictionary form
勉強するおかげで is not something a speaker produces. The example is generated by the step list, not drawn
from the record's prose. (Its sibling `gram:n3-sei-de` has the same dictionary-form variant with 遅れるせいで,
which is more tolerable because せいで accepts habitual causes, but the same review applies.)

**Proposed fix.** Either drop the `to-dictionary` variant from `n3-okagede`, or change its example to a
form the record vouches for and extend the prose to license it (e.g. `to-te-form → append いるおかげで`,
`勉強しているおかげで`).

---

## F. Level assignment

### F1 — Two records take the minority level against their own sources

| record | stored `level` | `level_sources` | `level_confidence` |
|---|---|---|---|
| `gram:ga-hoshii` | **n5** | jlptsensei n5, bunpro **n4**, tanos **n4** | 0.333 |
| `gram:te-aru` | **n5** | jlptsensei n5, bunpro **n4**, tanos **n4** | 0.333 |

CLAUDE.md §1.5 makes level assignment consensus-based across ≥3 lists. Both records have three sources,
two of which say n4, and both store n5. `level_confidence: 0.333` records the disagreement honestly, so
this is visible rather than hidden — but the stored value is the one lessons and sequencing read.

**Proposed fix.** Either flip both to n4 (matching 2/3) or document the rule that resolves ties in favour of
one source, in `design/`, so the choice is auditable. Right now the tiebreak is unstated.

### F2 — The same point carries two different levels across duplicate records

Consequence of C3, listed separately because it affects sequencing rather than content:
てほしい is n4 (`gp-152`, `te-hoshii`) **and** n3 (`n3-te-hoshii`); ても is n4 (`temo`) and n3 (`n3-temo`);
ないで is n5 (`naide`) and n3 (`n3-naide`); まで is n5 (`made`) and n3 (`n3-made`); の is n5 (`no`) and n3
(`n3-no`); らしい, まま, ばかり, てみる, ないと each appear at n4 and again at n3. A learner following the
level sequence meets the same point twice, at two tiers, with no signal that it is a repeat.

**Proposed fix.** Resolve with the C3 merge; the surviving record keeps the lower (earlier) level.

---

## Clean by class

To be explicit about what did **not** fail: of the 124 records, the explanation/formation/nuance content of
these was checked in full and found correct — including hand-executing every `formation_steps` variant:
`de`, `doushite`, `gp-11`, `gp-14`, `gp-143`, `gp-16`, `gp-2`, `gp-23`, `gp-27`, `gp-30`, `gp-38`, `gp-41`,
`gp-45`, `gp-49`, `gp-52`, `gp-8`, `ichiban`, `ka`, `kedo`, `made`, `mashouka`, `na-adjectives`,
`naito-ikenai`, `nakute-wa-naranai`, `ni`, `no`, `no-naka-de-a-ga-ichiban`, `o-wo`, `sugiru`, `te-aru`,
`te-kara`, `to`, `tte`, `ya`, `aida-ni`, `baai-wa`, `de-gozaimasu`, `gari`, `gp-109`, `gp-113`, `gp-117`,
`gp-121`, `gp-125`, `gp-129`, `gp-133`, `gp-137`, `gp-59`, `gp-67`, `gp-71`, `gp-75`, `gp-79`, `gp-87`,
`gp-91`, `gp-99`, `hitsuyou-ga-aru`, `janai-ka`, `kamo-shirenai`, `koro-goro`, `koto-ni-naru`, `made-ni`,
`mitai-na`, `nakanaka-nai`, `nasai`, `nikui`, `rareru`, `shi`, `sou-da-1`, `tadoushi-jidoushi`,
`tara-ii-desu-ka`, `te-ita`, `te-miru`, `te-sumimasen`, `temo`, `to-iwarete-iru`, `tokoro`, `yasui`,
`you-to-omou`, and the n3 set `n3-bakari`, `n3-dake-shika`, `n3-donna-ni-temo`, `n3-kake`, `n3-kawari-ni`,
`n3-kke`, `n3-koto-ni-natte-iru`, `n3-kurai`, `n3-mama`, `n3-metta-ni-nai`, `n3-moshi-tanara`,
`n3-n-datte`, `n3-naide`, `n3-ni-kanshite`, `n3-ni-tsuite`, `n3-okagede`, `n3-rashii`, `n3-sei-de`,
`n3-sono-tame-ni`, `n3-tate`, `n3-te-hoshii`, `n3-temo`, `n3-to-iu-koto-da`, `n3-to-iu-yori`,
`n3-tsuide-ni`, `n3-uto-shita`, `n3-wake-ga-nai`, `n3-you-ni-shimashou`.

No pt-BR style violations of `design/translation_style.md` were found in the grammar records themselves: no
em dash (—) appears in any learner-facing field in this slice (the 8 occurrences found are all inside
`steps_unavailable`, an engineering field), no pt-PT forms, and no "Quanto a mim" crutch outside
`translation_literal` where it belongs.

Two records I deliberately did **not** flag despite hesitation, recorded here so the reviewer can overrule:
`gram:gp-49` simplifies どこも/だれも to "always with a negative verb" (どこも混んでいる is affirmative and
common) — this is a standard N5 simplification and the record is explicit that it is teaching the negative
pattern; and `gram:gp-83`'s こまい as an alternate まい form of 来る is attested in Japanese dictionaries
even though it is rare.

---

## Counts

| Class | Finding | Records affected | Severity |
|---|---|---|---|
| **A. Wrong formation rule (produces bad Japanese)** | | **6** | |
| A1 | godan rule breaks on う-verbs, no exception | 3 (`gp-105`, `gp-63`, `saserareru`) | critical |
| A2 | 一人 given as the counter for animals | 1 (`gp-101`) | critical |
| A3 | くれる's ます-form falsely called irregular | 1 (`gp-56`) | high |
| A4 | な-adjective + にしては, flagged by the record, unfixed | 1 (`n3-ni-shite-wa`) | high |
| **B. Sentence links contradict the record** | | **8 records, 22 sentences** | |
| B1 | ずっと① illustrated by ずっと② | 1 rec / 3 sent | high |
| B2 | ようだ illustrated by ようと思う etc. | 1 rec / 5 sent | high |
| B3 | passive illustrated by potential + honorific | 1 rec / 3 sent | high |
| B4 | まい illustrated by のように (known bug, half-fixed) | 1 rec / 2 sent | high |
| B5 | ちゃいけない illustrated by なくちゃいけない | 1 rec / 4 sent | high |
| B6 | particle で illustrated by でも / なんで / ないで | 1 rec / 3 sent | medium |
| B7 | ようにしましょう illustrated by どのように + しましょう | 1 rec / 1 sent | medium |
| B8 | らしい glossed as direct perception | 1 rec / 1 sent | medium |
| **C. Structural / graph** | | **5** | |
| C1 | family labels ≠ family membership | ~20 in slice, systemic | high |
| C2 | `related` empty on 492/496; 4 dangling prose refs | 4 in slice, systemic | medium |
| C3 | duplicate records, unlinked, sometimes contradictory | 14 groups touching slice | high |
| C4 | n3 tier diverges from the n5/n4 schema on 5 fields | 33 in slice / 132 corpus | high |
| C5 | grammar points with zero example sentences | 3 in slice / 17 corpus | medium |
| **D. Learner-facing text** | | **7** | |
| D1 | `formation.en` truncated mid-sentence | 1 (`gp-34`) | medium |
| D2 | misplaced closing parenthesis | 8 fields / 7 records | low |
| D3 | pipeline residue ("o material", "seed", "gid 428") | 2 (`gp-152`, `n3-tokoro-ga`) | medium |
| D4 | `forms[].form` mangled by placeholder stripping | 8 | medium |
| D5 | pt-BR missing diacritics (13 occurrences) | 6, all n3 | medium |
| D6 | pt-BR missing the lead sentence en has | 1 (`gp-105`) | low |
| D7 | `structure_pattern` tilde contradicts the record | 1 (`n3-sono-tame-ni`) | low |
| **E. Machine-consumption** | | **2** | |
| E1 | `replace-ending` token has two incompatible grammars | 3 (`sugiru`, `gp-26`, `te-de`) | medium |
| E2 | step variant emits a non-idiomatic form | 1 (`n3-okagede`) | low |
| **F. Level assignment** | | **2** | |
| F1 | stored level contradicts 2 of 3 sources | 2 (`ga-hoshii`, `te-aru`) | medium |
| F2 | same point at two levels via duplicates | 10 pairs | medium |

**Totals — records checked: 124. Distinct findings: 30. Distinct records carrying ≥1 finding: 47.**

Severity roll-up: **critical 2 · high 9 · medium 13 · low 6.**

Priority for the teacher queue: **A1 first** (three records, one-line fix each, and the correct wording
already exists elsewhere in the corpus), then **A2 / A3**, then **B1–B5** (each is an untag plus a
replacement example), then **C3 / C4** (schema decisions that need a human call, not an edit).
