# Yomineko — Japanese N5 & N4 Corpus (pt-BR)

A curated, verifiable, LLM-ready knowledge base ("corpus") + courseware for a Brazilian-Portuguese Japanese
course covering **zero → full N5 → full N4**, aimed at speaking / living / working in Japan.

This repository is **data and reference material** — no app, no backend (the future app is Flutter/Dart; the
corpus is framework-neutral).

## Start here
1. [`YOMINEKO_CORPUS_BUILD_SPEC.md`](YOMINEKO_CORPUS_BUILD_SPEC.md) — the master specification.
2. [`STATE.md`](STATE.md) — current progress and the `RESUME HERE` marker.
3. [`INDEX.md`](INDEX.md) — map of every folder/file.
4. [`CLAUDE.md`](CLAUDE.md) — the non-negotiable operating rules.

## The two layers
- **Corpus layer** (`corpus/`, `db/corpus.sqlite`): reusable, by-ID registries (kanji, vocab, grammar), the
  dissected-sentence bank, and families. Each sentence lives once, fully dissected.
- **Courseware layer** (`course/`): the linear Module → Topic → Lesson course. References the corpus **by ID
  only** — never embeds sentences or dissections.

## Provenance model (trust levels)
- **Layer A** — authoritative, zero-AI (open datasets: JMdict, KANJIDIC2, KanjiVG, Tatoeba…).
- **Layer B** — AI-derived, machine-validated against Layer A (pt-BR translations, token glosses, dissections).
- **Layer C** — pedagogy (explanations, sequencing); research-grounded, flagged for human teacher review.

## Status
Bootstrapping (Phase P-pre complete). See [`STATE.md`](STATE.md).

## Attribution
Built on open datasets (EDRDG JMdict/KANJIDIC2, KanjiVG, Tatoeba, community JLPT lists). Full attributions and
commercial-use notes will live in `ATTRIBUTION.md`.
