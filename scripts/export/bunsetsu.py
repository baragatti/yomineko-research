#!/usr/bin/env python3
"""Bunsetsu chunking and scramble analysis for 並べ替え (sentence_order) items — W17.

WHY (qa_sweep/exam_japanese_1.md F15, _2.md S4, _3.md F8)
---------------------------------------------------------
The builder shipped the sentence's bare SudachiPy mode-C morphemes as draggable tiles: 271 of 273
N5 items expose bound morphemes (`まし`, `た`, `ん`, `が`, `を`, `ませ`, `でし`), `so:n5:2448` opens
with the tile `ははは` (母は), and `so:n3:208` is nine tiles for a seven-word sentence. Pulling まし
away from た is a morphology drill, not the syntax task 文の組み立て is. Real papers give
phrase-level chunks.

Morpheme tiles also multiply the ambiguity: because every particle is its own tile, 45 items across
the three levels assemble into a SECOND grammatical sentence from the same tiles, and the app scores
one string, so a correct learner answer is marked wrong.

WHAT THIS MODULE DOES
---------------------
`chunk()` merges the analyzer's tokens into bunsetsu: one content word plus everything that leans on
it (particles, auxiliaries, suffixes), with prefixes attaching forward. Chunking is done from the
STORED Layer-A analysis (`token.pos`, the locale-neutral column) — it is not a second guess at the
Japanese, it is a regrouping of the dissection the corpus already holds.

`scramble()` then answers the two questions the ambiguity finding raises, and answers them
differently, which is the point:

  * **Meaning-preserving reorderings become `accepted[]`.** Japanese marks roles with case
    particles, not with position, so permuting chunks that carry DISTINCT case/topic particles
    yields the same sentence with different information structure — 「いすの上にねこがいます」 and
    「ねこがいすの上にいます」. Grading one and rejecting the other is a scoring defect, not a
    Japanese fact. Erring toward MORE accepted strings is safe: it can only make grading lenient,
    never mark a correct answer wrong.

  * **Meaning-CHANGING reorderings drop the item.** When two movable chunks carry the SAME particle
    the swap exchanges their roles: 「これはあっちのより安いよ」 vs 「あっちのはこれより安いよ」 means
    the opposite, and nothing in the prompt says which is wanted. Those items are ill-posed and are
    refused at selection instead of being shipped with a coin-flip key.

A chunk ending in の modifies the chunk after it, so the two travel together as one unit — the
reordering that matters moves 「いすの上に」 whole, never 「上に」 away from 「いすの」. The final unit is
the predicate and is always fixed.
"""
from __future__ import annotations

from itertools import permutations

# `token.pos` is the locale-neutral English enum (CLAUDE.md: mechanical enums are English), written
# beside the Japanese `pos_coarse` by the dissector. Using it keeps this module readable and keeps
# the rule in one vocabulary.
HEAD_POS = {"noun", "pronoun", "verb", "i-adjective", "na-adjective", "adverb", "adnominal",
            "conjunction", "interjection", "numeral"}
CLITIC_POS = {"particle", "auxiliary", "suffix"}
PREFIX_POS = {"prefix"}
DROP_POS = {"whitespace"}

# Sentence-final punctuation is not a tile: it is not reorderable and printing it would mark the
# last chunk. Internal punctuation (、) STAYS, attached to the chunk it closes — without it
# 「二、三デメリット」 reassembles as 二三 and reads にさん (F13).
FINAL_PUNCT = "。！？!?…"
INTERNAL_PUNCT = "、，,・「」『』（）()"

# Particles that mark a chunk's ROLE, so the chunk may sit anywhere before the predicate.
CASE_P = {"が", "を", "に", "へ", "で", "と", "から", "まで", "より"}
TOPIC_P = {"は", "も"}
MOVABLE_TAILS = CASE_P | TOPIC_P | {c + t for c in CASE_P for t in ("は", "も")}
# の attaches the chunk to the NEXT one; a chunk ending in の is never movable and pins its head.
BINDING_TAILS = {"の"}


def chunk(tokens: list[dict]) -> list[str] | None:
    """[{surface, pos}] in analyzer order -> bunsetsu strings, or None if the sentence is unchunkable.

    None (rather than a best effort) whenever the analysis cannot support the format: a sentence
    that starts with a clitic, or that produces a chunk with no content word, is not a sentence this
    item type can be cut from.
    """
    chunks: list[str] = []
    pending_prefix = ""
    started = False
    for t in tokens:
        surf, pos = t["surface"], t["pos"]
        if pos in DROP_POS or not surf.strip():
            continue
        if pos == "punctuation":
            if surf in FINAL_PUNCT:
                continue                       # dropped: not a tile
            if surf in INTERNAL_PUNCT and chunks:
                chunks[-1] += surf
                continue
            return None                        # a bracket or a symbol we will not guess about
        if pos in PREFIX_POS:
            pending_prefix += surf
            continue
        if pos in CLITIC_POS:
            if not started:
                return None                    # a sentence cannot open with a clitic
            chunks[-1] += pending_prefix + surf
            pending_prefix = ""
            continue
        if pos in HEAD_POS:
            chunks.append(pending_prefix + surf)
            pending_prefix = ""
            started = True
            continue
        return None                            # an unknown POS is a reason to abstain
    if pending_prefix or not chunks:
        return None
    return chunks


def _tail_particle(c: str) -> str:
    """The longest MOVABLE_TAILS / BINDING_TAILS particle string this chunk ends with ("" if none)."""
    c = c.rstrip(INTERNAL_PUNCT)
    for cand in sorted(MOVABLE_TAILS | BINDING_TAILS, key=len, reverse=True):
        if c.endswith(cand) and len(c) > len(cand):
            return cand
    return ""


def _units(chunks: list[str]) -> list[list[int]]:
    """Group chunks into movable UNITS.

    A chunk ending in の modifies the chunk after it — 「いすの」「上に」 is one phrase, and the
    reordering that matters (「ねこがいすの上にいます」) moves the whole phrase, not its head. So the
    の-chunk and what it modifies form one unit; everything else is a unit of its own.
    """
    units: list[list[int]] = []
    i = 0
    while i < len(chunks):
        unit = [i]
        while _tail_particle(chunks[unit[-1]]) in BINDING_TAILS and unit[-1] + 1 < len(chunks):
            unit.append(unit[-1] + 1)
        units.append(unit)
        i = unit[-1] + 1
    return units


def scramble(chunks: list[str], max_movable: int = 4) -> tuple[list[str] | None, str]:
    """(accepted orderings, reason) — `None` means REFUSE the item.

    `accepted[0]` is always the canonical order. `reason` is a short machine-readable tag recorded
    in the diff classification so every dropped item can be explained.
    """
    if len(chunks) < 3:
        return None, "too-few-chunks"
    units = _units(chunks)
    canon = "".join(chunks)
    if len(units) < 3:
        return [canon], "fixed-order"
    tails = [_tail_particle(chunks[u[-1]]) for u in units]
    movable = [i for i in range(len(units) - 1) if tails[i] in MOVABLE_TAILS]
    if not movable:
        return [canon], "fixed-order"
    seen = [tails[i] for i in movable]
    if len(set(seen)) != len(seen):
        # Two units marked the same way: swapping them exchanges their roles and changes the
        # meaning. Nothing in the prompt says which meaning is wanted, so the item is ill-posed.
        return None, "same-particle-ambiguous"
    if len(movable) > max_movable:
        return None, "too-many-movable"
    texts = ["".join(chunks[j] for j in u) for u in units]
    out: list[str] = []
    for perm in permutations(movable):
        arr = list(texts)
        for slot, src in zip(movable, perm):
            arr[slot] = texts[src]
        s = "".join(arr)
        if s not in out:
            out.append(s)
    out.remove(canon)
    return [canon] + sorted(out), "scrambled"
