# design/authoring_failure_modes.md — how AI-authored pedagogy actually fails here

> Distilled from the QA campaigns in this repo, not from theory. Every class below was found by two
> independent checkers reading real output against the record it describes. Companion to
> `learning_science.md` (what to teach) and `translation_style.md` (how it should read); this file is
> about the specific ways an authoring pass produces confident, fluent, wrong content.
>
> Use it as the checklist in any authoring or verification prompt. Naming a failure mode up front
> measurably reduces it: the passes that were told about false formation rules produced far fewer.

## F1. A general rule the entry's own examples contradict

**The single most common defect.** An author writes a tidy generalisation, then lists examples, and one
of the examples breaks the rule they just stated. Fluency hides it: both halves read well separately.

Real instances, all caught in one pass over 630 kanji:

| Record | Rule asserted | Its own example that breaks it |
|---|---|---|
| 口 くち | "costuma sonorizar e virar ぐち no fim" | 早口 (はやくち), 無口 (むくち) keep くち |
| 万 バン | "aparece com o sentido de todos/tudo" | 万歳 = ten thousand years, not "all" |
| 発 ハツ | "…e no fim da palavra em 爆発" (singling it out) | 開発 is also word-final |
| 計 ケイ | splits into "opens (設計)" vs "closes" | 設計 is せっけい: 計 CLOSES it |
| 物 もの | "é a que fecha o vocabulário do dia a dia" | 物語 has 物 at the START |
| 元 もと | "é a que fecha compostos" | 元々 is reduplicated, so it also opens |

**Test:** for every general claim, walk the record's own list and check each item against it. If any item
is an exception, either name the exception in the note or drop the generalisation. Do not average.

## F2. Citing something outside the record's own scope

An author reaches for a word that is not in the field they are describing — usually a genuinely related
word, which is what makes it feel safe. It teaches vocabulary the surrounding data does not carry, and
it breaks any consumer that joins on that field.

  * 立 た.てる cited 立つ, which belongs to a different reading group.
  * 行 -い+き presented 行き as its worked example while its own compounds list was EMPTY and 行き sat in
    `irregular`.
  * A structure paragraph in the sentence bank referred to "a frase com ね" — a DIFFERENT record. Each
    sentence is stored once and displayed alone, so a cross-reference to a batch neighbour is
    unresolvable by construction.

**Test:** every noun phrase in the note must appear in the record's own arrays. Self-containment is not
a style preference; a batch neighbour is invisible to the learner.

## F3. Laundering an upstream error instead of flagging it

Given a wrong input and a slot for prose, an author will write prose that makes the wrong input sound
correct, rather than saying the input is wrong.

  * 画 カイ: the grouping had put 絵画 under カイ. 絵画 is かいが — the かい is 絵 and 画 is ガ. Instead of
    flagging the grouping, the note explained that 画 is カイ "in this word", teaching a false reading.

**Test:** always give the author an explicit escape hatch field (`grouping_problem`, `verdict:
no-change`, `needs-human`) AND say in the prompt that using it is a good outcome. Passes told this used
it: one flagged 142 real alignment errors that became the fix.

## F4. Empty-slot confabulation

A slot with no data still gets confident content. A reading with zero compounds gets a note describing
"its" compounds; a form with no examples gets a usage claim.

**Test:** state the empty case explicitly in the prompt ("a reading with no compounds still gets a note,
but the note must not pretend to have examples") and check it in verification.

## F5. False formation rules

The highest-severity class, because it makes the learner PRODUCE something wrong rather than merely
misunderstand something.

  * ちゃいけない described as coming from "action verbs" and じゃいけない from nouns. じゃ is the voiced
    て-form variant, so the rule produces *読んちゃいけない.
  * れる called the godan POTENTIAL. On a godan verb れる is the PASSIVE (書かれる); the potential is -eru.
  * ようだ whose forms, formation and nuance all taught the VOLITIONAL under a "parece que" label.
  * のぞいて called "sonorizada". のぞく is k-final: no voicing. The same batch used "sonorizada"
    correctly for いそぐ → いそいで two sentences later, so a learner comparing them derives *のぞいで.
  * が described as marking "quem realiza a ação" in 火が消えた, where 消える is intransitive.

**Test:** take the rule literally and apply it to a godan verb, an ichidan verb, する/くる, a な-adjective
and a noun. If it generates anything ungrammatical, the rule is wrong. Ask verifiers to actually run
this, not to judge plausibility.

## F6. Instruction-as-value

The fix field receives "replace X with Y" instead of Y. Two grammar explanations SHIPPED to learners
carrying edit orders (`Substituir a frase final por: "…"`), and one had the corrected sentence appended
after the false one it was meant to replace, so the entry stated both.

**Test:** a regex guard in every applier, plus verification. Never rely on the authoring prompt alone.

## F7. Confident refutation of a claim the author did not find

Verification has its own failure mode: an agent that cannot locate a source concludes the source does
not exist.

  * A research pass asserted the "keyword mnemonics forget ~2× faster at 2 days" figure was
    unverifiable. It is exact and traceable (Wang, Thomas, Inzana & Primicerio 1993: rote 62% vs keyword
    43%). Two of three independent checkers refuted the refutation.

**Test:** "I could not find it" and "it does not exist" are different verdicts and must be different
enum values.

## How to use this file

Paste the relevant classes into the authoring prompt AND the verification prompt. Require two
independent checkers and act only on what both raise: single-checker findings in this repo have run
heavily to false positives, which is why the exam-bank prompts tell verifiers that overturning is
frequently the correct answer.
