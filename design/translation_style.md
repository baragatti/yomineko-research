# Translation & authoring style (pt-BR) — enforced in every AI authoring prompt

All learner-facing content is **Brazilian Portuguese (pt-BR)**. This guide is the contract every
dissection/generation/lesson prompt must follow, and the standard the humanizer + spot-checks enforce.

## 1. Natural translation, NOT a literal mirror (hard rule)
The `translation` field must read like something a Brazilian would actually say. The structural mirror goes
in `translation_literal` — never in `translation`.

- わたしは がくせい です。 → translation **"Eu sou estudante."** (NOT "Quanto a mim, sou estudante.")
- 今日は寒いね。 → **"Hoje está frio, né?"** (NOT "Quanto a hoje, está frio.")
- The topic particle は almost never becomes "quanto a / falando de" in the natural translation — render the
  topic as the natural subject. Keep "quanto a X" for `translation_literal` and `structure_explanation` only,
  where the literal structure is the teaching point.

## 2. Register / tone mirrors the Japanese
Reflect the JP politeness in the pt tone when it's natural: plain/casual JP → casual pt ("cê", "tá", "né"
sparingly); polite/keigo JP → neutral-polite pt. Don't invent archaic or stiff pt. Use the vocab/grammar
`register` enum (colloquial/slang/vulgar/honorific/humble/polite…) to gauge tone; flag genuinely
offensive/vulgar items so the UI can warn.

## 3. Punctuation
- **Generated Japanese** sentences must NOT end with 。 (or 、 dangling). Keep them clean.
- **Selected** real sentences (Tatoeba, Layer A) keep their original punctuation — never edit the source.
- pt text uses normal Portuguese punctuation.

## 4. No "AI tells" (run the `humanizer` skill on authored prose)
Avoid: "Quanto a mim/isso" as a crutch, "Vale ressaltar/destacar", "Por assim dizer",
rule-of-three padding, vague hedging, inflated/promotional adjectives, superficial "-ndo" analyses. **Never
use the — (em dash) character** anywhere in authored text — it reads as an AI tell; use parentheses or commas.
Write
direct, concrete, friendly, beginner-clear. pt-BR only (never pt-PT): "você", "celular", "ônibus", "trem".

## 5. Field discipline (where each kind of text lives)
- `translation` — natural pt-BR. `translation_literal` — structural gloss (topic markers, particle-by-particle).
- `structure_explanation` — friendly beginner explanation; may use literal glosses to teach は/が/を etc.
- token `gloss` — meaning in context; `role` — grammatical role; `conjugation_note` — the form.
- particle `function` (text) complements the mechanical `function_type` enum; explain *why this particle here*.

## 6. Mechanical vs authored (don't duplicate)
Mechanical Layer-A fields (`pos`, `inflection`, particle `function_type`, vocab `register`, conjugations) are
derived from Sudachi/JMdict — never hand-write them. AI authors only the pt-BR meaning/explanation layer.
