#!/usr/bin/env python3
"""Write the prerequisite DAG into `needs[]`, in both layers.

WHY
---
`design/lesson_schema.md` has specified `needs` — `[{type, ref, note?}]`, "every ref must be
unlocked by a strictly-earlier lesson" — since the P6 freeze, and 322 of 322 lessons carried
`"needs": []`. `validate_lesson_gating.py` check C therefore proved nothing and said so out loud:
"0 `needs` entries across 322 lessons — the prerequisite model is empty". Every consumer that wants
to know what a lesson depends on (placement, the "antes desta lição" box, a mistake index) had to
re-derive it, and nothing stopped a later edit from breaking linearity.

WHAT IT WRITES
--------------
`research/derived/repairs/lesson_needs.json`, produced by `scripts/build_needs_table.py`:

  origin `derived`       707 rows copied from `scripts/derive_needs.py` on the current tree — the
                         transitive reduction of "lesson L references an item lesson M unlocks".
  origin `kana-chain`     40 rows. The pre-N5 strand references nothing but its own kana family, so
                         every one of its 41 lessons derives as a root. Chained by rule: each needs
                         the pre-N5 lesson immediately before it in course order.
  origin `review-chain`   11 rows. The review and kanji-exame lessons at positions 119-124 and
                         216-220 re-drill what they unlock themselves, so they too derive as roots.
                         Each needs the lesson immediately before it in course order.

8 lessons keep no `needs` and are listed in the table's `roots`: the course opener plus seven early
N5 lessons whose every dependency points FORWARD (the W21b ledger) or that are genuinely
self-contained. `validate_lesson_gating.py` check C2 holds them in
`course/needs_root_exemptions.json` and the count may only shrink.

BOTH LAYERS
-----------
`research/derived/lessons/<slug>.json` (what a manifest replay reads) and `db/corpus.sqlite`
(`lesson_needs`, which migration 013 gave a `note` column so the reason survives ingest). The
exporter republishes `course/**/lesson-*.json` afterwards. The lesson BODY is not touched by this
script at all — `needs` is record metadata, never body text.

Idempotent: a second run finds every row present with the same note and reports 0 changes.
Run `scripts/export/export_course.py` afterwards.

Usage: apply_lesson_needs.py [--check] [--replace]
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
TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_needs.json"

def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc


def serialize(obj: dict, trailing: bool) -> str:
    """The authoring sources are canonical `json.dumps(ensure_ascii=False, indent=2)` — all 322 of
    them reproduce byte for byte from their own parse, and step 89 of the rebuild manifest
    (`apply_qa_instruction_leaks.py`) REFUSES to touch a file that does not, so a compact one-line
    `needs` entry would silently disable that repair on every lesson it edits. Writing through the
    parse is what keeps the invariant instead of hoping a hand-built string matches it."""
    return json.dumps(obj, ensure_ascii=False, indent=2) + ("\n" if trailing else "")


def by_lesson(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:                                        # the table is already in course order
        out.setdefault(r["lesson"], []).append(
            {"type": "lesson", "ref": r["ref"], "note": r["note"]})
    return out


def apply_sources(groups: dict[str, list[dict]], check: bool, problems: list[str],
                  replace: bool = False) -> int:
    changed = 0
    for lesson, needs in groups.items():
        f = SRC / (lesson.split(":", 1)[1] + ".json")
        if not f.exists():
            problems.append(f"{lesson}: authoring source {f.name} missing")
            continue
        raw = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as e:                  # noqa: PERF203
            problems.append(f"{lesson}: {f.name} is not valid JSON ({e})")
            continue
        had = obj.get("needs") or []
        if had and had != needs and not replace:
            problems.append(f"{lesson}: {f.name} already declares {len(had)} need(s) that are not "
                            f"the {len(needs)} this table says it should")
            continue
        obj["needs"] = needs
        text = serialize(obj, raw.endswith("\n"))
        if text == raw:
            continue                                      # already applied, canonically
        if not had:
            changed += len(needs)
        if not check:
            f.write_text(text, encoding="utf-8")
    return changed


def apply_db(con, groups: dict[str, list[dict]], check: bool, problems: list[str],
             replace: bool = False) -> int:
    changed = 0
    for lesson, needs in groups.items():
        row = con.execute("SELECT id FROM lesson WHERE slug=?", (lesson,)).fetchone()
        if not row:
            problems.append(f"{lesson}: no such lesson in the index")
            continue
        lid = row[0]
        have = {(t, r): n for t, r, n in con.execute(
            "SELECT need_type, ref, note FROM lesson_needs WHERE lesson_id=?", (lid,))}
        want = {("lesson", n["ref"]): n["note"] for n in needs}
        for key in have.keys() - want.keys():
            if not replace:
                problems.append(f"{lesson}: index carries a need {key[1]} this table does not")
                continue
            changed += 1
            if not check:
                con.execute("DELETE FROM lesson_needs WHERE lesson_id=? AND need_type=? AND ref=?",
                            (lid, key[0], key[1]))
        for key, note in want.items():
            if have.get(key) == note:
                continue
            changed += 1
            if check:
                continue
            if key in have:
                con.execute("UPDATE lesson_needs SET note=? WHERE lesson_id=? AND need_type=? "
                            "AND ref=?", (note, lid, key[0], key[1]))
            else:
                con.execute("INSERT INTO lesson_needs (lesson_id,need_type,ref,note) "
                            "VALUES (?,?,?,?)", (lid, key[0], key[1], note))
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--replace", action="store_true",
                    help="rewrite `needs` that disagree with the table instead of refusing. "
                         "`needs` is 100%% derived (validate_lesson_gating check C4 re-derives it on "
                         "the tree being validated and fails on any difference), so a disagreement "
                         "is a stale table, never hand-authored work to protect. W15 made that "
                         "concrete: `body-reading` edges come from a reading record's `uses`, so "
                         "replacing 282 passages moved ~470 edges, and without this flag the "
                         "applier refused every one of them — including in a rebuild replay, where "
                         "the authoring sources already carry the previous run's needs.")
    args = ap.parse_args()

    doc = load_table()
    groups = by_lesson(doc["rows"])
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    problems: list[str] = []

    # the table's own invariant, re-checked here so a hand-edited table cannot ship a cycle
    order = [r[0] for r in con.execute(
        "SELECT l.slug FROM lesson l JOIN topic t ON t.id=l.topic_id "
        "JOIN course_module m ON m.id=t.module_id ORDER BY m.ord, t.ord, l.ord")]
    pos = {s: i for i, s in enumerate(order)}
    for lesson, needs in groups.items():
        for n in needs:
            if n["ref"] not in pos:
                problems.append(f"{lesson}: needs {n['ref']}, which is not a lesson")
            elif pos[n["ref"]] >= pos.get(lesson, -1):
                problems.append(f"{lesson}: needs {n['ref']}, which is not strictly earlier")

    src = apply_sources(groups, args.check, problems, args.replace)
    db = apply_db(con, groups, args.check, problems, args.replace)
    if not args.check and not problems:
        con.commit()
    con.close()

    verb = "would write" if args.check else "wrote"
    print(f"{doc['counts']}")
    print(f"{verb} {src} need(s) into the authoring sources and {db} into the index "
          f"({len(groups)} lessons, {len(doc['roots'])} roots left with none)")
    for p in problems[:15]:
        print(f"  ! {p}")
    if len(problems) > 15:
        print(f"  … and {len(problems) - 15} more")
    if problems:
        print("\nNOTHING WAS COMMITTED — an edge that does not re-derive is not written.")
        return 2
    return 1 if (args.check and (src or db)) else 0


if __name__ == "__main__":
    sys.exit(main())
