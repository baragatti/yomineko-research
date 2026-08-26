#!/usr/bin/env python3
"""Generate one JSON Schema per entity from the measured shapes, wired to the shared patterns.

Why generate rather than hand-write: twenty-three entities with 500+ field paths between them cannot
be hand-maintained against a corpus that is still being built, and a schema that has drifted from the
data is worse than none — it teaches you to ignore the gate. So the field inventory comes from
contracts/_shapes.json (what the data actually is) and the SEMANTICS come from the tables below (what
a field means, which is a judgement no measurement can make).

The two are deliberately separated. `required` is measured: a field on 100% of records is required,
one on 97% is not. `$ref: common#/$defs/StableId` is decided: `slug` is the public address on a
registry, and no amount of counting reveals that.

`additionalProperties: false` is set only where the inventory enumerates keys exhaustively — the
record root and one level in. Deeper than that the walker samples rather than enumerates, so the
schema stays open and says so, instead of failing valid data.

Reads:  contracts/_shapes.json  (run infer_shapes.py first)
Writes: contracts/<entity>.schema.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SHAPES = ROOT / "contracts" / "_shapes.json"
OUT = ROOT / "contracts"
COMMON = "common.schema.json"

# --- semantics: what a field NAME means wherever it appears -------------------------------------
REF_BY_NAME = {
    "level": "Level",
    "layer": "Layer",
    "level_confidence": "LevelTag/properties/level_confidence",
    "level_agreement": "LevelTag/properties/level_agreement",
    "level_sources": "LevelTag/properties/level_sources",
    "needs_review": "Provenance/properties/needs_review",
    "ai_generated": "Provenance/properties/ai_generated",
    "source": "Provenance/properties/source",
}
# Fields whose value is the record's own public address.
ID_FIELDS = {"slug", "id"}

# One-line purpose per entity. Measurement cannot produce these.
ABOUT = {
    "kanji": "One kanji character: readings, meanings, radical decomposition and the level it is taught at. Layer A apart from the pt-BR meanings.",
    "vocab": "One dictionary word, keyed by its JMdict entry. Carries senses, pitch, inflection class and the consensus level.",
    "grammar": "One grammar point: its forms, how it is formed, what it contrasts with, and the pedagogy around it.",
    "sentence": "One fully dissected example sentence — the unit the whole corpus is built on. A sentence lives here ONCE and everything else references it by id.",
    "family": "A group of items that behave alike (a conjugation class, a particle set, a semantic field), with the rule that governs the group.",
    "conjugation": "The full inflection table for one verb or adjective, keyed by the vocab entry it belongs to.",
    "kana": "One hiragana or katakana character and the family it belongs to.",
    "kana_family": "The kana chart, as ordered groups (base, dakuten, yoon...). Keyed by script.",
    "reading": "A short reading passage gated to a lesson, with its tokens and translation.",
    "stroke_order": "Ordered stroke steps for one kanji, for animating how it is written.",
    "stroke_lines": "Raw stroke path geometry for one kanji.",
    "stroke_kana": "Stroke data for one kana character, including the shadow guides used when tracing.",
    "capability": "Something a learner can DO once a set of lessons is complete. The bridge between the syllabus and the exam.",
    "capability_lesson_map": "Which capabilities each lesson contributes to. Keyed by lesson id.",
    "exam_item": "One JLPT-style practice question, drawn from the corpus so every item is also findable in a lesson.",
    "exercise_conjugation": "One generated conjugation drill: a prompt form, the correct inflection, and three distractors.",
    "exercise_role": "One generated particle-role drill, derived mechanically from a sentence's own particles.",
    "course": "A course root for one level: its ordered topics and the overview shown before the first lesson.",
    "topic": "A block of lessons that closes one theme, and the items it unlocks.",
    "lesson": "The leaf unit a learner sits down to. Holds objectives, explanation, exercises and the items it introduces — all corpus content by REFERENCE, never embedded.",
    "speak_path": "The root of the situation-ordered path (Fala Primeiro): its stages and totals.",
    "speak_unit": "One unit of the speaking path: phrases, drills and a checkpoint for a single situation.",
    "course_manifest": "The index an API reads first: every course, where its root lives, and how much is in it.",
}


def ref(name: str) -> dict:
    return {"$ref": f"{COMMON}#/$defs/{name}"}


def type_schema(types: list[str]) -> dict:
    """Turn the observed JSON types into a type constraint, keeping null optional-but-allowed."""
    ts = [t for t in types if t != "null"]
    node: dict = {}
    if not ts:
        return {"type": "null"}
    # An integer-only field stays integer; a field seen as both int and float is a number.
    if set(ts) == {"integer", "number"}:
        ts = ["number"]
    node["type"] = ts[0] if len(ts) == 1 else ts
    if "null" in types:
        node["type"] = ([node["type"]] if isinstance(node["type"], str) else node["type"]) + ["null"]
    return node


class Node:
    """A point in the reconstructed record tree."""

    def __init__(self) -> None:
        self.info: dict | None = None
        self.children: dict[str, "Node"] = {}
        self.item: "Node | None" = None      # for arrays: the shape of one element


def parse_path(path: str) -> list[tuple[str, bool]]:
    """'example_words[].gloss.en' -> [('example_words', True), ('gloss', False), ('en', False)]"""
    out = []
    for seg in path.split("."):
        is_array = seg.endswith("[]")
        out.append((seg[:-2] if is_array else seg, is_array))
    return out


def build_tree(fields: dict) -> Node:
    """Rebuild the record tree from the flat dotted paths.

    The subtlety is that `distractors` and `distractors[]` are two facts about the same field — the
    first says it is an array, the second says its elements are strings — and they must land on
    different nodes. A trailing `[]` always means "descend into the element", so both facts survive;
    letting them share a node makes the element type silently overwrite the array type.
    """
    root = Node()
    for path, info in fields.items():
        cur = root
        for name, is_array in parse_path(path):
            if name:
                cur.children.setdefault(name, Node())
                cur = cur.children[name]
            if is_array:
                cur.item = cur.item or Node()
                cur = cur.item
        cur.info = info
    return root


def is_locale(node: Node) -> str | None:
    """A locale object is any object with a pt-BR key. String values -> LocaleText, arrays -> list."""
    pt = node.children.get("pt-BR")
    if pt is None or pt.info is None:
        return None
    return "LocaleTextList" if "array" in pt.info["types"] else "LocaleText"


def nullable(schema: dict, info: dict | None) -> dict:
    """A $ref cannot be relaxed by adding `type: null` beside it — the ref wins. Wrap it instead."""
    if info and "null" in info.get("types", []):
        return {"anyOf": [schema, {"type": "null"}]}
    return schema


def emit(node: Node, name: str, depth: int, records: int) -> dict:
    loc = is_locale(node)
    if loc:
        return nullable(ref(loc), node.info)

    if name in REF_BY_NAME and node.info and not node.children:
        target = REF_BY_NAME[name]
        return nullable({"$ref": f"{COMMON}#/$defs/{target}"}, node.info)

    if name in ID_FIELDS and node.info and "string" in node.info["types"] and not node.children:
        return nullable(ref("StableId"), node.info)

    info = node.info or {"types": ["object"]}
    schema = type_schema(info["types"])

    # A closed value set becomes an enum. Booleans are already constrained by their type.
    vals = info.get("values")
    if vals and schema.get("type") not in ("boolean", ["boolean"]) and len(vals) <= 24:
        if not (isinstance(vals[0], bool)):
            schema["enum"] = vals + ([None] if "null" in info["types"] else [])

    if node.children:
        props, required = {}, []
        for k, child in sorted(node.children.items()):
            props[k] = emit(child, k, depth + 1, records)
            if child.info and child.info.get("required"):
                required.append(k)
        # Keep whatever type_schema worked out — an object field that is sometimes null must stay
        # ["object", "null"]. Hard-coding "object" here silently dropped the null and failed 568 valid
        # records whose optional sub-object is absent.
        if "type" not in schema:
            schema["type"] = "object"
        schema["properties"] = props
        if required:
            schema["required"] = required
        # Keys are enumerated exhaustively only for the first two levels (see module docstring).
        if depth <= 1:
            schema["additionalProperties"] = False

    if node.item is not None:
        schema["items"] = emit(node.item, name, depth + 1, records)

    return schema


def main() -> int:
    if not SHAPES.exists():
        print("run scripts/contracts/infer_shapes.py first", file=sys.stderr)
        return 2
    shapes = json.loads(SHAPES.read_text(encoding="utf-8"))["entities"]

    written = []
    for entity, v in shapes.items():
        if not v["records"]:
            continue
        # Map-packed files are keyed collections, not record lists: the contract there is about the KEYS
        # and the value shape, which is a different schema idiom (propertyNames/additionalProperties).
        # There are two of them and they disagree with each other, so they are hand-authored.
        if v["kind"] == "map":
            continue
        tree = build_tree(v["fields"])
        props, required = {}, []
        for k, child in sorted(tree.children.items()):
            props[k] = emit(child, k, 0, v["records"])
            if child.info and child.info.get("required"):
                required.append(k)

        # Which field holds this record's OWN address? `id` when it is a prefixed string — on
        # exercise_conjugation the `slug` is the vocab the drill is about, a foreign key, and treating
        # it as the primary key reports 17,368 "duplicates" that are nothing of the sort. Fall back to
        # `slug` for the registries, where `id` is an integer storage row number.
        id_field = None
        if "id" in tree.children and "string" in v["fields"]["id"]["types"]:
            id_field = "id"
        elif "slug" in tree.children and "string" in v["fields"]["slug"]["types"]:
            id_field = "slug"

        doc = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://yomineko.dev/contracts/{entity}.schema.json",
            "title": entity,
            "description": ABOUT.get(entity, ""),
            "x-yomineko": {
                "entity": entity,
                "records": v["records"],
                "packing": v["kind"],
                "glob": v["glob"],
                "stable_id_field": id_field,
                "generated_by": "scripts/contracts/build_schemas.py from contracts/_shapes.json",
            },
            "type": "object",
            "properties": props,
            "additionalProperties": False,
        }
        if required:
            doc["required"] = required
        path = OUT / f"{entity}.schema.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append((entity, len(props), len(required)))

    for e, p, r in written:
        print(f"  {e:22} {p:>3} properties, {r:>3} required")
    print(f"\n{len(written)} schemas -> contracts/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
