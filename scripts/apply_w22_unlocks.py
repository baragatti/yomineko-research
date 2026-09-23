#!/usr/bin/env python3
"""W22 apply: the never-unlocked app features and the conjugation-form unlocks, in both layers.

WHAT
----
`research/derived/repairs/w22_n3_dead_end.json` (derived by `scripts/derive_w22_unlocks.py`) holds
one row per lesson unlock, in three sections:

  features       feat:jlpt-sim-n3 on the last lesson of top:n3-revisao (the siblings' rule R1)
  home_lessons   9 features homed at the first lesson whose own JSON uses them (rule H1)
  form_unlocks   25 `conj:<form>` unlocks at the earliest of four channels (rule F, gate-sound)

Every row is an ADDITIVE unlock: nothing is moved or removed, so no cumulative_known_set can shrink.
Features and conjugation forms enrol no SRS card (design/unlock_enums.json#item_to_deck maps
neither) and add no `needs` edge (nothing references a feat:/conj: ref).

BOTH LAYERS
-----------
`research/derived/lessons/<slug>.json` (feature refs go into `feature_unlocks`, which the loader
merges into unlocks; conj refs into `unlocks`) and `db/corpus.sqlite` (`lesson_unlocks`, then
`lesson.cumulative_known_set` recomputed with the ingest's own routine). The exporter republishes
`course/`. Lesson bodies are not touched.

Refuses (writes nothing) when a ref is not in design/unlock_enums.json or another lesson already
unlocks it (introduce-once). Idempotent: a second run reports 0 changes.

Usage: apply_w22_unlocks.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
SRC = out_root(ROOT) / "research" / "derived" / "lessons"
TABLE = ROOT / "research" / "derived" / "repairs" / "w22_n3_dead_end.json"
ENUMS = json.loads((ROOT / "design" / "unlock_enums.json").read_text(encoding="utf-8"))
ENUM_OF = {"feature": ("feat:", set(ENUMS["feature"])),
           "conjugation-form": ("conj:", set(ENUMS["conjugation_form"]))}


def load_rows() -> list[dict]:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc["rows"]


def has(obj: dict, typ: str, ref: str) -> bool:
    if any(u.get("type") == typ and u.get("ref") == ref for u in obj.get("unlocks") or []):
        return True
    return typ == "feature" and ref in (obj.get("feature_unlocks") or [])


def apply_sources(rows: list[dict], check: bool, problems: list[str]) -> int:
    changed = 0
    by_lesson: dict[str, list[dict]] = {}
    for r in rows:
        by_lesson.setdefault(r["lesson"], []).append(r)
    for lesson, rs in by_lesson.items():
        f = SRC / (lesson.split(":", 1)[1] + ".json")
        if not f.exists():
            problems.append(f"{lesson}: authoring source {f.name} missing")
            continue
        raw = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        obj = json.loads(raw)
        n = 0
        for r in rs:
            if has(obj, r["type"], r["ref"]):
                continue
            if r["type"] == "feature":
                obj["feature_unlocks"] = list(obj.get("feature_unlocks") or []) + [r["ref"]]
            else:
                obj["unlocks"] = list(obj.get("unlocks") or []) + [{"type": r["type"], "ref": r["ref"]}]
            n += 1
        if n:
            changed += n
            if not check:   # canonical serialisation, see apply_lesson_needs.serialize
                f.write_text(json.dumps(obj, ensure_ascii=False, indent=2)
                             + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    rows = load_rows()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    problems: list[str] = []

    lid = dict(con.execute("SELECT slug, id FROM lesson"))
    for r in rows:
        prefix, members = ENUM_OF[r["type"]]
        if not r["ref"].startswith(prefix) or r["ref"][len(prefix):] not in members:
            problems.append(f"{r['ref']}: not a value of design/unlock_enums.json ({r['type']})")
        if r["lesson"] not in lid:
            problems.append(f"{r['lesson']}: no such lesson in the index")
            continue
        others = [s for (s,) in con.execute(
            "SELECT l.slug FROM lesson_unlocks u JOIN lesson l ON l.id=u.lesson_id "
            "WHERE u.unlock_type=? AND u.ref=? AND l.slug<>?", (r["type"], r["ref"], r["lesson"]))]
        if others:
            problems.append(f"{r['ref']}: already unlocked by {others} (introduce-once)")
    if problems:
        for p in problems[:20]:
            print(f"  ! {p}")
        print("\nNOTHING WAS WRITTEN.")
        return 2

    src = apply_sources(rows, args.check, problems)
    db = 0
    for r in rows:
        if con.execute("SELECT 1 FROM lesson_unlocks WHERE lesson_id=? AND unlock_type=? AND ref=?",
                       (lid[r["lesson"]], r["type"], r["ref"])).fetchone():
            continue
        db += 1
        if not args.check:
            con.execute("INSERT INTO lesson_unlocks (lesson_id, unlock_type, ref) VALUES (?,?,?)",
                        (lid[r["lesson"]], r["type"], r["ref"]))
    if not args.check:
        sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
        from load_lessons import recompute_cumulative  # noqa: PLC0415
        print(f"  recomputed cumulative_known_set for {recompute_cumulative(con)} lessons (db)")
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"{len(rows)} rows: {verb} {src} unlock(s) into the authoring sources and {db} into the index")
    return 1 if (args.check and (src or db)) else 0


if __name__ == "__main__":
    sys.exit(main())
