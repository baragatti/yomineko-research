#!/usr/bin/env python3
"""Derive the ACTUAL shape of every corpus/course artifact, as ground truth for the contracts.

The data model is described in prose in `design/schema_v2.md` and summarised per directory in the
INDEX.md files, but nothing machine-readable states what a record looks like. That gap is why the
exported JSON drifted: `audit_export_refs.py` hand-checks a handful of fields on lesson leaves and
nothing checks the other seventeen artifact families at all.

This does not invent a schema. It reads what is on disk and reports, per entity and per field:
frequency (how many records carry it), the JSON types seen, whether it is always present, and the
observed value set when it looks closed (few distinct scalar values). An authoring pass turns that into
a JSON Schema; a field present on 100% of records is `required`, one present on 3% is not, and a field
with six distinct string values across 5,889 records is an enum rather than a free string.

Nested objects and arrays-of-objects are walked one level deep under a dotted path (`tokens[].pos`),
which is where the real variation lives — a token array is uniform, a sentence record is not.

Output: contracts/_shapes.json. Regenerate whenever the exporter changes.
Usage: infer_shapes.py [--max-enum N]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "contracts" / "_shapes.json"

# One entry per artifact FAMILY. `kind` says how records come out of the file:
#   "list"     - the file IS a list of records (the common case)
#   "single"   - the whole file is ONE record (course roots, manifests)
#   "map"      - the file is id -> value; the VALUES are profiled under a synthetic "[value]" path
# Globs are deliberately narrow. `course/*/course.json` would fold the JLPT course root and the
# Fala-Primeiro path root into one entity, and they share almost no fields — the union would then be
# a schema that accepts either and enforces neither, which is worse than having no schema.
FAMILIES: list[dict] = [
    {"entity": "kanji", "glob": "corpus/kanji/*.json", "kind": "list"},
    {"entity": "vocab", "glob": "corpus/vocab/*.json", "kind": "list"},
    {"entity": "grammar", "glob": "corpus/grammar/*.json", "kind": "list"},
    {"entity": "sentence", "glob": "corpus/sentences/bank.json", "kind": "list"},
    {"entity": "family", "glob": "corpus/families/families.json", "kind": "list"},
    {"entity": "conjugation", "glob": "corpus/conjugations/*.json", "kind": "list"},
    {"entity": "kana", "glob": "corpus/kana/[hk]*.json", "kind": "list"},
    {"entity": "kana_family", "glob": "corpus/kana/families.json", "kind": "map"},
    {"entity": "reading", "glob": "corpus/readings/*.json", "kind": "list"},
    # Three different record shapes share corpus/strokes/. Kanji stroke ORDER (steps + transform) and
    # kanji stroke LINES (raw path data) are separate artifacts, and the kana set carries its own
    # `shadows` field. Globbing the directory would union all three.
    {"entity": "stroke_order", "glob": "corpus/strokes/n[0-9].json", "kind": "list"},
    {"entity": "stroke_lines", "glob": "corpus/strokes/lines_n[0-9].json", "kind": "list"},
    {"entity": "stroke_kana", "glob": "corpus/strokes/kana.json", "kind": "list"},
    {"entity": "capability", "glob": "corpus/capabilities/registry.json", "kind": "list"},
    {"entity": "capability_lesson_map", "glob": "corpus/capabilities/lesson_map.json", "kind": "map"},
    {"entity": "exam_item", "glob": "corpus/exam_banks/*.json", "kind": "list"},
    {"entity": "exercise_conjugation", "glob": "corpus/exercises/conjugation/*.json", "kind": "list"},
    {"entity": "exercise_role", "glob": "corpus/exercises/roles/*.json", "kind": "list"},
    {"entity": "course", "glob": "course/[!s]*/course.json", "kind": "single"},
    {"entity": "topic", "glob": "course/*/topic-*/topic.json", "kind": "single"},
    {"entity": "lesson", "glob": "course/*/topic-*/lesson-*.json", "kind": "single"},
    {"entity": "speak_path", "glob": "course/speak/course.json", "kind": "single"},
    {"entity": "speak_unit", "glob": "course/speak/*/unit-*.json", "kind": "single"},
    {"entity": "course_manifest", "glob": "course/manifest.json", "kind": "single"},
]


def jtype(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    return "object"


class FieldStat:
    __slots__ = ("count", "types", "values", "too_many")

    def __init__(self) -> None:
        self.count = 0
        self.types: Counter = Counter()
        self.values: set = set()
        self.too_many = False


def note(stats: dict[str, FieldStat], path: str, value: object, max_enum: int, depth: int) -> None:
    fs = stats.setdefault(path, FieldStat())
    fs.count += 1
    fs.types[jtype(value)] += 1
    if isinstance(value, (str, bool, int)) and not isinstance(value, float):
        if not fs.too_many:
            fs.values.add(value)
            # A closed set stays small. Past the cap it is free text and the samples are noise.
            if len(fs.values) > max_enum:
                fs.too_many = True
                fs.values = set()
    if depth <= 0:
        return
    if isinstance(value, dict):
        for k, v in value.items():
            note(stats, f"{path}.{k}", v, max_enum, depth - 1)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                for k, v in item.items():
                    note(stats, f"{path}[].{k}", v, max_enum, depth - 1)
            else:
                note(stats, f"{path}[]", item, max_enum, depth - 1)


def records_of(path: Path, kind: str) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    if kind == "single":
        return [data] if isinstance(data, dict) else []
    if kind == "map":
        # id -> value. The keys are IDs (profiled separately by the caller); the values are the shape
        # that matters, and they are usually not objects, so wrap them to reuse the same walker.
        return [{"[value]": v} for v in data.values()] if isinstance(data, dict) else []
    return data if isinstance(data, list) else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-enum", type=int, default=24)
    args = ap.parse_args()

    out: dict[str, dict] = {}
    problems: list[str] = []
    for fam in FAMILIES:
        files = sorted(ROOT.glob(fam["glob"]))
        stats: dict[str, FieldStat] = {}
        n = 0
        keys: list[str] = []
        for f in files:
            rel = str(f.relative_to(ROOT)).replace("\\", "/")
            try:
                recs = records_of(f, fam["kind"])
            except Exception as exc:  # unreadable JSON is a finding, not something to skip quietly
                problems.append(f"{rel}: {exc}")
                continue
            if fam["kind"] == "map":
                keys += list(json.loads(f.read_text(encoding="utf-8")))
            for rec in recs:
                if not isinstance(rec, dict):
                    continue
                n += 1
                for k, v in rec.items():
                    note(stats, k, v, args.max_enum, depth=2)
        if not n:
            problems.append(f"{fam['entity']}: glob {fam['glob']!r} matched {len(files)} file(s), "
                            f"0 records — the glob or the kind is wrong")
            out[fam["entity"]] = {"glob": fam["glob"], "kind": fam["kind"],
                                  "files": [], "records": 0, "fields": {}}
            continue
        fields = {}
        for path, fs in sorted(stats.items()):
            entry = {
                "present": fs.count,
                "pct": round(100 * fs.count / n, 1),
                "required": fs.count == n,
                "types": sorted(fs.types),
            }
            if fs.values and not fs.too_many:
                entry["values"] = sorted(fs.values, key=lambda x: str(x))
            fields[path] = entry
        entry: dict = {
            "glob": fam["glob"],
            "kind": fam["kind"],
            "files": [str(f.relative_to(ROOT)).replace("\\", "/") for f in files],
            "records": n,
            "fields": fields,
        }
        if keys:
            entry["key_sample"] = sorted(keys)[:5]
            entry["key_prefixes"] = sorted({k.split(":", 1)[0] for k in keys if ":" in k})
        out[fam["entity"]] = entry

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"note": __doc__.strip().split("\n\n")[0], "entities": out},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(out)} entity families")
    for e, d in out.items():
        print(f"  {e:22} {d['records']:>6} rec  {len(d['fields']):>3} paths  {len(d['files'])} file(s)")
    for p in problems:
        print(f"  ! {p}")
    print(f"-> {OUT.relative_to(ROOT)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
