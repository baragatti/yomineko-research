#!/usr/bin/env python3
"""Put the derived `reading` on the lesson-body `<jp>` spans that had none, in both layers.

WHY
---
PENDING.md A7: 875 `<jp>` spans in the lesson bodies carry kanji and no `reading`. In this schema
`<jp reading="…">` is the ONLY pronunciation a learner is given for Japanese printed in prose (a
`<vocab>`/`<kanji>` chip opens a registry modal; a bare span opens nothing), so each of those 875 is
a word shown to someone who may not be able to read it. `validate_lesson_bodies.py` could not see
them: `JPTAG` requires `reading="…"` to be present before it checks anything, so an EMPTY reading
was a hard failure and a MISSING one was invisible.

WHAT IT WRITES
--------------
`research/derived/repairs/lesson_furigana.json`, produced by `scripts/build_furigana_table.py`,
which derives and refuses under the rules in that script's docstring. Only the `rows` are applied;
the `residue` is carried in the same file with both candidates and the reason it was refused, and
`validate_lesson_bodies.py` ratchets on its size so it can only shrink.

The table is keyed by (lesson, surface): inside one lesson a surface gets one reading, so the write
is a literal `<jp>X</jp>` -> `<jp reading="…">X</jp>` substitution and re-running it is a no-op.
Every one of the 875 spans is exactly `<jp>` with no other attribute and no inner markup (measured),
which is what makes a literal substitution safe here rather than a regex over the body.

BOTH LAYERS, and the prose must not move
----------------------------------------
`research/derived/lessons/<slug>.json` (what a manifest replay reads; the body is a JSON string
there, so the attribute quotes are backslash-escaped) and `db/corpus.sqlite`
(`localized_text` field `body`, where the body is the decoded string). The exporter republishes
`course/**/lesson-*.json`. Rendering a lesson to plain text before and after this script must give
byte-identical output: an attribute is added, no text node changes.

Idempotent. Run `scripts/export/export_course.py` afterwards.
Usage: apply_lesson_furigana.py [--check]
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
TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_furigana.json"


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc


def forms(surface: str, reading: str, escaped: bool) -> tuple[str, str]:
    """(old, new) as the literals appear in that layer. In the authoring JSON the body is a string,
    so the attribute's quotes are written `\\"`; in the index the body is decoded text."""
    q = '\\"' if escaped else '"'
    return f"<jp>{surface}</jp>", f"<jp reading={q}{reading}{q}>{surface}</jp>"


def apply_sources(rows: list[dict], check: bool, problems: list[str], absent: list[str]) -> int:
    changed = 0
    for lesson, group in group_by_lesson(rows).items():
        f = SRC / (lesson.split(":", 1)[1] + ".json")
        if not f.exists():
            problems.append(f"{lesson}: authoring source {f.name} missing")
            continue
        raw = f.read_text(encoding="utf-8")
        before = raw
        for r in group:
            old, new = forms(r["surface"], r["reading"], escaped=True)
            n = raw.count(old)
            if n == 0:
                if new not in raw:
                    # The span is not in this body at all. On the repo tree that means the row is
                    # stale; inside a manifest replay it means an earlier step REGENERATED the file
                    # (build_exam_kanji_lessons.py re-chunks the eight *-kanji-exame-* sources and
                    # its output is not the committed one), and a row with nothing to apply is not a
                    # failure. Recorded and reported, and it is a hard failure only if EVERY row is
                    # absent, which is the one shape that would make this script a silent no-op.
                    absent.append(f"{lesson}: <jp>{r['surface']}</jp>")
                continue                                   # already applied
            if n != r["occurrences"]:
                problems.append(f"{lesson}: {f.name} carries {n} <jp>{r['surface']}</jp>, the table "
                                f"says {r['occurrences']}")
                continue
            raw = raw.replace(old, new)
            changed += n
        if raw != before and not check:
            f.write_text(raw, encoding="utf-8")
    return changed


def apply_db(con, rows: list[dict], check: bool, problems: list[str], absent: list[str]) -> int:
    changed = 0
    for lesson, group in group_by_lesson(rows).items():
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (lesson,)).fetchone()
        if not lr:
            problems.append(f"{lesson}: no such lesson in the index")
            continue
        lid = lr[0]
        row = con.execute("SELECT value FROM localized_text WHERE entity_type='lesson' AND "
                          "entity_id=? AND field='body' AND locale='pt-BR'", (lid,)).fetchone()
        if not row:
            problems.append(f"{lesson}: no pt-BR body in the index")
            continue
        body = before = row[0]
        for r in group:
            old, new = forms(r["surface"], r["reading"], escaped=False)
            n = body.count(old)
            if n == 0:
                if new not in body:
                    absent.append(f"{lesson}: index <jp>{r['surface']}</jp>")   # see apply_sources
                continue
            if n != r["occurrences"]:
                problems.append(f"{lesson}: the index body carries {n} <jp>{r['surface']}</jp>, the "
                                f"table says {r['occurrences']}")
                continue
            body = body.replace(old, new)
            changed += n
        if body != before and not check:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND "
                        "entity_id=? AND field='body' AND locale='pt-BR'", (body, lid))
    return changed


def group_by_lesson(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r["lesson"], []).append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    doc = load_table()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    problems: list[str] = []
    absent: list[str] = []
    src = apply_sources(doc["rows"], args.check, problems, absent)
    db = apply_db(con, doc["rows"], args.check, problems, absent)
    if len(absent) >= 2 * len(doc["rows"]):
        problems.append("every row is absent from both layers — this table matches nothing")
    if not args.check and not problems:
        con.commit()
    con.close()

    verb = "would annotate" if args.check else "annotated"
    print(json.dumps(doc["counts"], ensure_ascii=False))
    print(f"{verb} {src} span(s) in the authoring sources and {db} in the index; "
          f"{doc['counts']['residue']} span(s) left as residue, unwritten")
    if absent:
        lessons = sorted({a.split(":", 2)[0] + ":" + a.split(":", 2)[1] for a in absent})
        print(f"  advisory: {len(absent)} row-half(s) address a span that is not in the body at all, "
              f"over {len(lessons)} lesson(s) — {', '.join(lessons[:8])}"
              + (" …" if len(lessons) > 8 else ""))
    for p in problems[:15]:
        print(f"  ! {p}")
    if len(problems) > 15:
        print(f"  … and {len(problems) - 15} more")
    if problems:
        print("\nNOTHING WAS COMMITTED — a reading no registry confirms is not written.")
        return 2
    return 1 if (args.check and (src or db)) else 0


if __name__ == "__main__":
    sys.exit(main())
