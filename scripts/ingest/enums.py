#!/usr/bin/env python3
"""Load design/unlock_enums.json — the single source of truth for the courseware needs/unlocks taxonomy.

Imported by load_lessons.py + validate_lessons.py + export_course.py so the closed enums live in ONE place.
Exposes the value sets, the ref-namespace map, deck metadata, and helpers (normalize a ref, pick an item's
SRS deck, card types for a deck).
"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_ENUMS = json.loads((_ROOT / "design" / "unlock_enums.json").read_text(encoding="utf-8"))

UNLOCK_TYPE: set[str] = set(_ENUMS["unlock_type"])
NEED_TYPE: set[str] = set(_ENUMS["need_type"])
FEATURE: set[str] = set(_ENUMS["feature"])
CARD_TYPE: set[str] = set(_ENUMS["card_type"])
DECK: set[str] = set(_ENUMS["deck"])
DECK_REGISTRY: dict = _ENUMS["deck_registry"]
DECK_DEFAULTS: dict = _ENUMS["_deck_defaults"]
CONJ_FORM: set[str] = set(_ENUMS["conjugation_form"])
REF_NS: dict[str, str] = _ENUMS["ref_namespace"]  # type -> prefix


def parse_ref(ref: str) -> tuple[str | None, str | None]:
    """'vocab:乗る' -> ('vocab', '乗る'); 'kana:hiragana-sa' -> ('kana','hiragana-sa')."""
    if not isinstance(ref, str) or ":" not in ref:
        return None, None
    pre, ident = ref.split(":", 1)
    return pre, ident


def expected_prefix(typ: str) -> str | None:
    return REF_NS.get(typ)


def deck_for(unlock_type: str, ref: str, level: str | None) -> str | None:
    """The SRS deck an unlocked item enrolls into (None if the item produces no cards)."""
    if unlock_type == "kana-family":
        _, ident = parse_ref(ref)
        script = (ident or "").split("-", 1)[0]  # hiragana / katakana
        return f"deck:kana-{script}" if script in ("hiragana", "katakana") else None
    if unlock_type in ("vocab", "kanji", "grammar"):
        lv = level if level in ("n5", "n4") else "n5"
        return f"deck:{unlock_type}-{lv}"
    if unlock_type == "phrase":
        return "deck:phrases"
    return None  # conjugation-form / kanji-family / feature / srs-deck -> no auto cards
