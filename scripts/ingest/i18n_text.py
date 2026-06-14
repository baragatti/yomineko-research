#!/usr/bin/env python3
"""Locale-aware text helpers (i18n). localized_text is the single source for authored learner-facing
content; identifiers/fields are English+neutral. pt-BR is the default locale module (see design/i18n.md)."""
from __future__ import annotations

import json
import sqlite3

DEFAULT_LOCALE = "pt-BR"

# entity_type -> [(legacy_column, neutral_field, is_list)] — used by migrate_i18n.py and as the field registry.
FIELD_MAP: dict[str, list[tuple[str, str, bool]]] = {
    "kanji": [("meanings_pt", "meanings", True), ("notes_pt", "notes", False)],
    "vocab": [("notes_pt", "notes", False)],
    "vocab_sense": [("gloss_pt", "gloss", True)],
    "grammar_point": [("label_pt", "label", False), ("explanation_pt", "explanation", False),
                      ("formation_pt", "formation", False), ("nuance_pt", "nuance", False)],
    "sentence": [("pt", "translation", False), ("pt_literal", "translation_literal", False),
                 ("structure_explanation_pt", "structure_explanation", False)],
    "token": [("role_pt", "role", False), ("gloss_pt", "gloss", False),
              ("conjugation_note_pt", "conjugation_note", False)],
    "particle": [("function_pt", "function", False), ("explanation_pt", "explanation", False)],
    "family": [("label_pt", "label", False), ("description_pt", "description", False),
               ("governing_rule_pt", "governing_rule", False)],
    "course_module": [("title_pt", "title", False), ("overview_pt", "overview", False)],
    "topic": [("title_pt", "title", False), ("theme_pt", "theme", False), ("objectives_pt", "objectives", True)],
    "lesson": [("title_pt", "title", False), ("body_pt", "body", False), ("objectives_pt", "objectives", True)],
    "exercise": [("prompt_pt", "prompt", False), ("explanation_pt", "explanation", False)],
}


def set_text(con: sqlite3.Connection, etype: str, eid: int, field: str, value,
             locale: str = DEFAULT_LOCALE, layer: str | None = None) -> None:
    if value is None or value == "":
        return
    is_list = 1 if isinstance(value, (list, dict)) else 0
    v = json.dumps(value, ensure_ascii=False) if is_list else str(value)
    con.execute(
        "INSERT OR REPLACE INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
        "VALUES (?,?,?,?,?,?,?)", (etype, eid, field, locale, v, is_list, layer))


def get_text(con: sqlite3.Connection, etype: str, eid: int, field: str, locale: str = DEFAULT_LOCALE):
    r = con.execute("SELECT value,is_list FROM localized_text WHERE entity_type=? AND entity_id=? "
                    "AND field=? AND locale=?", (etype, eid, field, locale)).fetchone()
    if not r:
        return None
    return json.loads(r[0]) if r[1] else r[0]


def get_all(con: sqlite3.Connection, etype: str, locale: str = DEFAULT_LOCALE) -> dict:
    """Return {(entity_id, field): value} for an entity_type+locale (one query, for exporters)."""
    out: dict[tuple[int, str], object] = {}
    for eid, field, value, is_list in con.execute(
            "SELECT entity_id,field,value,is_list FROM localized_text WHERE entity_type=? AND locale=?",
            (etype, locale)):
        out[(eid, field)] = json.loads(value) if is_list else value
    return out
