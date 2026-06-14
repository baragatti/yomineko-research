> De-identified clean-room abstraction (Phase L+). Contains NO copied text, examples, explanations, exercises, or names from the source material — abstract structure/ideas/coverage only, re-expressed in our own words.

# Local Course — Topic / Sequence Map (Phase L+, deep pass)

## What this is

A de-identified structural reading of a third-party paid Japanese program found on local disk. It ships as a **library of 11 distinct courses** (one top-level manifest names them; their names are stripped here and replaced with functional descriptors). Every concept label below is a *universal* Japanese-learning fact (script names, particle names, verb-form names) inferred from per-lesson structural metadata and re-expressed in our own words. No instructor/brand/product/creative title has been transcribed; no body text, example, or exercise was read into this abstraction. All counts (modules, lessons, media-asset types) are objective data points derived programmatically from the file tree.

**What is new vs. the shallow pass:** the prior read treated the intermediate/advanced courses as "reading-only with sparse grammar." That was wrong. Reading the actual lesson sequence shows they are **densely grammar-pointed** — roughly **one discrete grammar construction per lesson**, then one applied situational reading, then one guided text-analysis lesson, repeated module after module. This pass also reconstructs the kanji-batch cadence, the counter inventory, the keigo sub-system, the reading-library difficulty gradient, and the per-stage media model.

## High-level shape (data points)

| Course (function) | Modules | Lessons (content) | Media profile (derived) |
|---|---|---|---|
| Core A — **Beginner foundation** | 17 (incl. a module 0 onboarding) | 178 | very heavy per-sentence audio (~2,276 clips) + a video in ~93% of lessons; longest course |
| Core B — **Intermediate grammar belt** | 13 | 94 | ~98% lessons have audio (808 clips) + video ~85%; grammar-point + reading hybrid |
| Core C — **Advanced grammar belt** | 12 | 85 | 100% lessons have audio (860 clips) + video ~86%; densest prose bodies |
| **Kanji track** | 16 | 50 | video-led + **141 images** (glyph/stroke), no audio; fixed 3-unit batches |
| **Express / survival fast-track** | 6 | 58 | one video + one **downloadable PDF** per lesson; no per-sentence audio |
| **Thematic vocabulary** | 1 | 36 | one video per theme |
| **Counters** | 1 | 32 | one video per counter |
| **Onomatopoeia** | 1 | 20 | one video per set |
| **Keigo (honorific language)** | 1 | 13 | one video per lesson |
| **Manga / authentic-sentence reading** | 1 | 6 (+2 intro) | one video per lesson |
| **Graded reading library** | 4 series | 41 | **100% audio** (478 clips, per-sentence narration) + video ~54% |
| **TOTAL** | — | **~621 content lessons** | ~4,400 audio + ~960 video + ~158 image assets |

Cores A→B→C form a single beginner→intermediate→advanced spine. The other eight are standalone supplements usable in any order.

## Overall taxonomy (de-identified)

The course exposes a manifest naming each sub-course. Stripped to function: **(1)** beginner core, **(2)** kanji track, **(3)** intermediate core, **(4)** advanced core, **(5)** manga-reading track, **(6)** thematic vocabulary, **(7)** keigo, **(8)** counters, **(9)** onomatopoeia, **(10)** express survival track, **(11)** graded reading library. A separate global `assets` manifest (~1.3 MB) backs all media.

---

## Core A — Beginner foundation: full ordered concept progression

Module names in the core courses are *generic placeholders* ("Topic N"), so the real signal lives at the lesson level. The spine threads grammar, both kana scripts, and an interleaved kanji-vocabulary stream. A recurring lesson type opens most mid/late modules: a **kanji-vocabulary batch** ("words written in kanji"), and another recurring type is a **Japanese-titled applied audio-reading** lesson that re-uses the grammar just taught in a short narrated text.

| Module | Ordered concept coverage (our labels) | Lessons | Pacing note |
|---|---|---|---|
| 0 | Orientation: welcome, study-portal tour, support, the method, **spaced-repetition system (SRS)** | 5 | Pure onboarding; no language content |
| 1 | **Hiragana**, taught one kana-row at a time (vowels → K/G → S/Z → T/D → small-tsu/gemination → N-row → syllabic ん → H → B/P → M → Y → R → W) + full hiragana review | 15 | Very fine-grained; an entire module just for hiragana, with voiced/semi-voiced and small-tsu handled explicitly |
| 2 | Copula **です** and plain **だ**; basic greetings; how to study audio-texts; first applied text; simple **questions**; apology/attention opener; **demonstratives これ/それ/あれ**; **topic particle は**; **なに (what) questions**; applied text | 11 | Phrase-first: usable sentences before deep machinery; first reading practice arrives in module 2 |
| 3 | **Katakana**, again row-by-row, including **contracted/combination sounds** (in two passes) + full katakana review | 13 | Second script deliberately deferred until learner has spoken/grammar footing |
| 4 | **Negative sentences**; **place demonstratives (ko-so-a-do of location)**; **particle の (possessive/modifier)**; adnominal **この/その/あの/どの**; applied text; **numbers 0–99**; number suffixes; **particles から / まで**; applied text | 10 | Pronouns + negation + numbers + range particles clustered |
| 5 | **Verbs** (intro); **polite ます-form**; **object particle を**; **particle も**; applied text; **particle で**; applied text; **particle と**; **adverbs**; applied text | 10 | Polite verb register taught first as the default; object/means/accompaniment particles grouped |
| 6 | **Kanji onboarding**: what kanji is, form/meaning/reading, "how to learn kanji" within the method, extra deepening note, plus **special katakana sounds** | 7 | Kanji *method* introduced here (~module 6); special-katakana mop-up appended |
| 7 | Reading kanji with an SRS app; **particle に**; applied time text; **existence verbs ある/いる**; **subject particle が** (+ an example-sentence lesson); sentence connectives; applied text; **て-form** of verbs; applied text; **sentence-final particles** | 11 | て-form is the hinge; existence + subject-が introduced together |
| 8 | Kanji-vocab batch; **〜ている (progressive/state)**; **〜てください (requests)**; **〜てもいい (permission)**; applied text; **negative verb form**; negative questions; negation adverbs; **〜ていない**; applied text; **motion verbs + particle へ**; applied text; **〜ないでください / 〜なくてもいい** | 13 | Dense て-/ない-form cluster; permission/prohibition pairs taught adjacently |
| 9 | Kanji-vocab batch; **adjectives** intro; **negative adjectives**; **degree adverbs**; applied shopping text; **plain/conclusive form**; plain-form verbs; applied past text; **〜けれど / 〜が (contrast)**; applied text; **word-class review** | 11 | Adjectives enter here (relatively late); plain form introduced after polite |
| 10 | Kanji-vocab batch; **plain negative**; applied text; **desire: ほしい**; **desire: 〜たい**; **need: いる**; **〜てほしい**; **〜ないでほしい**; applied text; **〜から / 〜ので (reason)**; **〜と思う**; **〜という**; applied text; **full conjugation table** | 15 | Desire-expression suite + reason connectives; capstone conjugation reference |
| 11 | Kanji-vocab batch; **uses of て-form**; **noun + て**; applied disaster text; applied text; **giving/receiving verbs**; **〜てあげる/〜てもらう/〜てくれる**; **adjectival (relative) clauses**; applied text | 9 | Benefactive give/receive system + relative clauses |
| 12 | Kanji-vocab batch; **potential form**; **particle や (examples)**; **〜たり**; applied text; **imperative**; **negative imperative**; applied caution-sign text; **〜てから**; **〜前 (before)**; **〜後 (after)**; **〜ながら (simultaneous)**; applied text | 13 | Potential/imperative + temporal-sequence connectives clustered |
| 13 | Kanji-vocab batch; **〜たら (conditional/supposition)**; **〜ても (concessive)**; applied speech-contest text; **〜ば (conditional)**; **〜と (automatic/natural consequence)**; applied text; **〜なければ/〜なくては/〜ないと (obligation)**; **〜てしまう (completion/regret)**; applied text | 10 | The full **conditional family (たら/ば/と/なら)** + obligation cluster |
| 14 | Kanji-vocab batch; **volitional/intentional form**; **つもり / 予定 (plans)**; applied text; **〜すぎる (excess)**; **〜やすい/〜にくい (easy/hard to)**; applied text; **より (comparison)**; **〜ほうが + adjective**; **〜なら (option)**; applied text | 11 | Comparison + tendency suffixes; volitional and plan expressions |
| 15 | Kanji-vocab batch; **passive voice**; applied text; **causative voice**; applied text; **transitive/intransitive verb pairs**; applied text | 7 | The advanced voice transforms + transitivity pairs land at the end |
| 16 | Learner reflection; bridge into the intermediate course; how to remove furigana; collecting sentences independently; where to find native content; tools/dictionaries; closing | 7 | Independence/learner-autonomy closer; no new grammar |

**Granularity:** extremely fine — ~178 lessons for the N5→low-N4 band, with each kana script and pronunciation given multi-lesson runways and grammar parceled one point per lesson.

---

## Core B — Intermediate grammar belt: per-module template

Every module follows a near-rigid **template**: a run of **single-grammar-point lessons** (one construction each) → one **Japanese-titled applied situational reading** → one **"text study" (guided breakdown of that reading)**. Module names are generic ("Topic N").

| Module | Discrete grammar points taught (our labels) | Applied reading theme | Lessons |
|---|---|---|---|
| 1 | 〜て (gratitude/apology), 〜てみる (try), 〜ても (concession), 〜になる (transformation), 〜ため (purpose), 〜よう (manner), 〜の adjectival nominalization | a tour itinerary | 9 |
| 2 | 〜ます-sequencing, 〜なさい (command), 〜という (naming), 〜だろう (high probability), 〜かもしれない (medium probability), 〜そう (impression), 可能性がある / 恐れがある (risk) | weather forecast | 9 |
| 3 | 〜にする (intentional change), 〜ことがある (experience), 〜にする (choice), 〜ことにする / 〜ことになる (decisions), 〜みたい / 〜よう (comparison), 〜への (direction) | travel-agency info | 10 |
| 4 | nominalizing with の, 〜だけ (only), 〜し (listing reasons), 〜ておく (preparation), 〜てある (resultative) | restaurant ordering | 7 |
| 5 | 〜ず (negative), informal variations, 〜ということ, 〜わけ, 〜しかない (restriction), 〜なっていく/〜なってくる (trend) | feeling unwell | 8 |
| 6 | 〜かどうか (doubt), 〜ことができる (ability), 〜なし(に) (absence), 〜のに (counter-expectation), 〜うちに (time limit) | a public-holiday week | 7 |
| 7 | 〜のに (function), 〜によると (according to), 〜らしい (hearsay/likeness), 〜っぽい (resemblance) | a city travel experience | 6 |
| 8 | 〜場合 (case/condition), 〜際 (occasion), 〜ようになる, 〜なくなる, 〜ば/〜たら suggestions, 〜じゃない (seeking agreement) | wanting to work in Japan | 8 |
| 9 | 〜はず (expectation), 〜ほど (extent), 〜限り (limit), 〜には (necessary condition), 〜もの (informal justification), 〜ものか (emphatic negation) | emergency-call info | 8 |
| 10 | 〜おかげ (positive cause), 〜せい (blame), 〜に関する (concerning), compound verbs 始める/続ける/忘れる, 〜べき (should) | banking terms for foreigners | 7 |
| 11 | 〜こそ (emphasis), 〜っけ (trying to recall), 〜ところ (situation), 〜ばかり (only), 〜くせ (despite), 〜代わりに (instead) | how to use a library | 8 |
| 12 | 〜めったに (rarely), 〜ないことはない, 〜向け (aimed at) | exchange-student experience | 5 |
| 13 | course wrap-up + closing | — | 2 |

**Net:** ~70 distinct intermediate grammar constructions (N4→N3 band), each isolated to a lesson, all anchored by a recurring situational-reading + breakdown ritual.

---

## Core C — Advanced grammar belt: per-module template

Same template (grammar-point run → applied reading → text study), but the constructions are higher-register, idiomatic, and nuance-heavy (N3→N2/N1 band). Module names generic.

| Module | Discrete grammar points (our labels) | Applied reading theme | Lessons |
|---|---|---|---|
| 1 | 〜ていく/〜てくる, もちろん, 以下/以上/以内, verb→noun nominalization, させられる (causative-passive), 〜に比べて | hospital consultation | 8 |
| 2 | 〜によって, 〜にとって, 〜にしては, 〜にしても, 〜につれて, 〜に加えて | embassy / visa info | 8 |
| 3 | 〜に基づいて, やっぱり, 〜てごらん, 〜に違いない, 〜にほかならない, 〜に対して | foreign-resident registration | 8 |
| 4 | 一方で, 〜に限らず, 〜ようにする, ほとんど/ほぼ, 〜がたい, 〜たびに | a management philosophy ("continuous improvement") | 8 |
| 5 | なかなか〜ない, 〜かな/〜かしら, 〜なんか/〜なんて, 〜ばよかった (regret) | phoning for delivery | 6 |
| 6 | 〜というのは, 〜といい, まるで, 〜とおり, せめて, さすが, ところで, 〜まま | opening a bank account | 10 |
| 7 | 〜さえ, まさか, あまり(にも), 〜として, せっかく, 〜わけにはいかない | office supplies | 8 |
| 8 | 〜かける, 〜ような気がする, 〜たとたん, 〜きる/〜きれない, 〜てたまらない | asking directions in the street | 7 |
| 9 | 〜風に, 〜そうもない, 〜なさそう, 〜がち (tendency) | a fireworks festival | 6 |
| 10 | 〜っぱなし, ついでに, 〜ごとに, 〜おきに (intervals) | "my way of learning Japanese" | 6 |
| 11 | 〜を除いて, 〜とは限らない, 〜を中心に | a job interview | 5 |
| 12 | 〜てもかまわない, やがて, 〜かねる/〜かねない | a seasonal/cultural essay | 5 |

**Net:** ~60 advanced grammar constructions, all with the same isolate-then-apply ritual. Reading themes shift from medical/bureaucratic survival toward cultural/expository essays.

---

## Kanji track: structure

- 16 modules, each a **uniform 3-unit batch**: *(a) new kanji set → (b) vocabulary written with those kanji → (c) practice guide / printable material* (the first and last modules add one extra unit).
- **Video-led + image-heavy** (141 glyph/stroke images), **no per-sentence audio** — recognition-and-production oriented.
- Runs **in parallel** to the grammar spine, while the spine *also* threads its own lighter kanji-vocab batches from module 8 on. So kanji is taught on **two coordinated tracks** (a deep dedicated stream + a light contextual stream).

## Express / survival fast-track: structure

- A **second, function-first beginner path** that re-covers N5 ground but ordered by *communicative task* rather than by script/grammar: asking location/price/time, indicating possession, making requests, splitting greetings across many short parts.
- Teaches the **ます-form conjugation matrix** systematically (affirmative / past / negative / past-negative / volitional / 〜たい) in one module.
- Every lesson = one video + one **downloadable PDF**; no per-sentence audio. Built for fast spoken output, not deep literacy.

## Supplements: internal structure

| Supplement | Internal coverage & ordering (our labels) | Shape |
|---|---|---|
| Thematic vocabulary | 36 real-world **categories** (see concept_inventory.md), ordered loosely by life-domain; one video each | flat list |
| Counters | **32 individual counters** taught one-per-lesson, ordered time-units first (秒→分→時→日→晩→泊→週→月→年), then generic つ/個, then object/animal/people/event/flat/bound/multiplier/age/ordinal counters | flat list, deep |
| Onomatopoeia | 20 numbered sets of **giongo/gitaigo** (sound-symbolic vocabulary), grouped by sound family | flat list |
| Keigo | full honorific system in order: intro → **teineigo (polite)** → **sonkeigo (respect)** → **kenjougo/teichougo (humble, 2 parts)** → **bikago (beautification)** → specific honorific constructions (3 parts) → honorific vocabulary → **double-keigo (over-honorific error)** → reference verb/expression table | flat, systematic |
| Manga reading | intro + tools + **6 authentic-sentence analysis** lessons (sentence-mining from comics) | single module |
| Reading library | 4 difficulty **series**, 41 narrated texts (see gradient below) | series-graded |

## Reading library: difficulty gradient

| Series | Genre/abstraction level | Examples of content type (our description) |
|---|---|---|
| 1 (11 texts) | concrete, personal, present-tense | self-descriptions (one's apartment, being a student/teacher/doctor), days of the week, a letter to a grandparent, a children's-style animal story, colors |
| 2 (13 texts) | places + expository/abstract | a major city, travel destinations, national currency, money habits, cryptocurrency, an aging population, a management philosophy, a popular-science essay |
| 3 (6 texts) | cultural / lifestyle | high-school life, pop-music stars, a sport rivalry, national eating habits, karaoke venues, a classic folktale |
| 4 (11 texts) | essay / expository on society | origins of manga & anime, convenience stores, video games, IoT, a famous loyal-dog story, politics, the education system (2 parts), disaster prevention, politeness in the language (2 parts) |

Difficulty climbs from concrete-personal → expository-abstract → cultural-essay; every text is fully narrated.

## Inferred overall scope

- **Starts from absolute zero** (kana onboarding precedes all grammar; module 0 is pure method/SRS).
- The beginner spine alone covers all of **N5** and most of **N4** (potential, passive, causative, conditionals, comparison, benefactives, transitivity pairs).
- Cores B and C are an **explicit grammar-pattern belt** carrying ~130 additional constructions across the N4→N2/N1 range — each isolated to one lesson and reinforced by situational reading.
- No JLPT level label appears anywhere; level is implicit in ordering.
- Supplements add breadth most single syllabi skip: a 32-counter deep dive, a full keigo register system, onomatopoeia, modern thematic vocabulary, authentic-media reading, and a graded narrated reading library.
