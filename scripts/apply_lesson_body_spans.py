#!/usr/bin/env python3
"""C13. Apply a verified lesson-body span table to both layers.

THE TABLES (research/derived/repairs/, each moved out of pending/ with its verifier's verdict folded
in: ok rows keep the authored text, corrected rows carry the verifier's text, rejected rows sit under
`held` and are never applied)

  w08b_lesson_bodies.json  the eight W08b lessons that unlocked both records of a merge pair taught
                           them as two points; each row rewrites one span so the lesson teaches one.
  w21b_rewrites.json       the same-topic / same-level forward references no unlock move could fix: a
                           `<sentence>` card becomes a glossed plain line, or a decorative card goes.
                           `exercise_edits` empty the exercise cites of the same sentence.
  furigana_residue.json    the `reading` attribute on the <jp> spans build_furigana_table.py refused
                           (W21 residue). An attribute only: the rendered text does not move.
  comparacoes_fixes.json   P2-gp153: n4-suposicao-04 after the D5b merge (one のよう point, one checklist
                           row) and the two false claims in n5-comparacoes-01.

A row carrying `superseded_by: {table, row}` is skipped: the named later row consumed its `to`
(validate_repairs_applied.py proves the chain against the export).

Every row is {lesson, spans: [{from, to, count}], ...}. Per lesson, in table order, per span: `from`
must occur exactly `count` times, then body = body.replace(from, to). A span whose `from` is gone and
whose `to` is present (or empty) is already applied. A span in neither state is DRIFT: refused on the
live index (nothing written, in either layer); off it (a manifest replay, where build_exam_kanji_lessons
regenerates the kanji-exame sources) it is reported and skipped.

BOTH LAYERS
-----------
`research/derived/lessons/<slug>.json` (body, the lesson's own `sentence_refs` and the exercise field an
edit names) and `db/corpus.sqlite` (`localized_text` lesson body pt-BR, `lesson_sentence`,
`exercise_sentence`). A `<sentence>` a span removes leaves the lesson's staging list only when the new
body no longer renders it. The exporter derives the published `sentence_refs` from the body.

Idempotent. Run scripts/export/export_course.py afterwards, then re-derive needs[] (check C4):
build_needs_table.py -> apply_lesson_needs.py --replace.
Usage: apply_lesson_body_spans.py --table NAME.json [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.path.append(str(next(p for p in Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "db" / "corpus.sqlite"
DB = db_target(LIVE)
SRC = out_root(ROOT) / "research" / "derived" / "lessons"
REPAIRS = ROOT / "research" / "derived" / "repairs"
TABLES = ("w08b_lesson_bodies.json", "w21b_rewrites.json", "furigana_residue.json", "comparacoes_fixes.json",
          "n3_review_furigana.json")
SENT_REF = re.compile(r'<sentence\s+ref="([^"]+)"')
BODY_WHERE = ("WHERE entity_type='lesson' AND entity_id=? AND field='body' AND locale='pt-BR'")


def load_rows(name: str) -> list[dict]:
    doc = json.loads((REPAIRS / name).read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc["rows"]


def edit(body: str, group: list[dict], where: str, drift: list[str]) -> tuple[str, int, set[str]]:
    """(new body, spans changed, sentence refs the changed spans removed)."""
    changed, dropped = 0, set()
    for r in group:
        if r.get("superseded_by"):
            continue                                       # a later table's row consumed its `to`
        for s in r["spans"]:
            frm, to, count = s["from"], s["to"], s["count"]
            n = body.count(frm)
            if n == 0 and (not to or to in body):
                continue                                   # already applied
            if n != count:
                drift.append(f"{r['lesson']} {where}: {n} x {frm[:70]!r}, the row says {count}")
                continue
            body = body.replace(frm, to)
            changed += count
            dropped |= set(SENT_REF.findall(frm)) - set(SENT_REF.findall(to))
    return body, changed, dropped


def by_lesson(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r["lesson"], []).append(r)
    return out


def apply_sources(groups, check: bool, drift: list[str]) -> int:
    changed = 0
    for lesson, group in groups.items():
        f = SRC / (lesson.split(":", 1)[1] + ".json")
        if not f.exists():
            drift.append(f"{lesson}: authoring source {f.name} missing")
            continue
        raw = f.read_text(encoding="utf-8")
        d = json.loads(raw)
        body, n, dropped = edit(d.get("body") or "", group, f.name, drift)
        shown = set(SENT_REF.findall(body))
        refs = [s for s in d.get("sentence_refs") or [] if s not in dropped or s in shown]
        dirty = bool(n) or refs != (d.get("sentence_refs") or [])
        for r in group:
            for e in r.get("exercise_edits") or []:
                ex = next((x for x in d.get("exercises") or [] if x.get("slug") == e["exercise"]), None)
                if ex is None:
                    drift.append(f"{lesson}: exercise {e['exercise']} not in {f.name}")
                elif ex.get(e["field"]) != e["new"]:
                    if ex.get(e["field"]) != e["old"]:
                        drift.append(f"{lesson}: {e['exercise']}.{e['field']} = {ex.get(e['field'])}, "
                                     f"the row's old is {e['old']}")
                        continue
                    ex[e["field"]] = e["new"]
                    dirty = True
                    n += 1
        if dirty and not check:
            d["body"], d["sentence_refs"] = body, refs
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else ""),
                         encoding="utf-8")
        changed += n
    return changed


def apply_db(con, groups, check: bool, drift: list[str]) -> int:
    changed = 0
    for lesson, group in groups.items():
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (lesson,)).fetchone()
        row = lr and con.execute(f"SELECT value FROM localized_text {BODY_WHERE}", (lr[0],)).fetchone()
        if not row:
            drift.append(f"{lesson}: no lesson / pt-BR body in the index")
            continue
        lid = lr[0]
        body, n, dropped = edit(row[0], group, "index body", drift)
        if n and not check:
            con.execute(f"UPDATE localized_text SET value=? {BODY_WHERE}", (body, lid))
        shown = set(SENT_REF.findall(body))
        for s in dropped - shown:
            if not check:
                con.execute("DELETE FROM lesson_sentence WHERE lesson_id=? AND sentence_id="
                            "(SELECT id FROM sentence WHERE slug=?)", (lid, s))
        for r in group:
            for e in r.get("exercise_edits") or []:
                if e["field"] != "sentence_refs":
                    drift.append(f"{lesson}: exercise field {e['field']} is not supported")
                    continue
                ex = con.execute("SELECT id FROM exercise WHERE slug=?", (e["exercise"],)).fetchone()
                if ex is None:
                    drift.append(f"{lesson}: exercise {e['exercise']} not in the index")
                    continue
                cur = sorted(s for (s,) in con.execute(
                    "SELECT s.slug FROM exercise_sentence es JOIN sentence s ON s.id=es.sentence_id "
                    "WHERE es.exercise_id=?", (ex[0],)))
                if cur == sorted(e["new"]):
                    continue
                if cur != sorted(e["old"]):
                    drift.append(f"{lesson}: index {e['exercise']} cites {cur}, the row's old is {e['old']}")
                    continue
                n += 1
                if not check:
                    for s in set(e["old"]) - set(e["new"]):
                        con.execute("DELETE FROM exercise_sentence WHERE exercise_id=? AND sentence_id="
                                    "(SELECT id FROM sentence WHERE slug=?)", (ex[0], s))
                    for s in set(e["new"]) - set(e["old"]):
                        con.execute("INSERT OR IGNORE INTO exercise_sentence (exercise_id, sentence_id) "
                                    "SELECT ?, id FROM sentence WHERE slug=?", (ex[0], s))
        changed += n
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True, choices=TABLES)
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    live = Path(DB).resolve() == LIVE.resolve()
    groups = by_lesson(load_rows(args.table))
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    drift: list[str] = []
    # dry pass over both layers first: drift anywhere writes nothing anywhere (on the live index)
    src = apply_sources(groups, True, drift)
    db = apply_db(con, groups, True, drift)
    if drift and not live:
        for d in drift:
            print(f"  [replay] DRIFT, skipped: {d}")
        drift = []
    if not drift and not args.check:
        skip: list[str] = []
        apply_sources(groups, False, skip)
        apply_db(con, groups, False, skip)
        con.commit()
    con.close()
    verb = "would change" if args.check else "changed"
    print(f"apply_lesson_body_spans --table {args.table}: {sum(map(len, groups.values()))} row(s) over "
          f"{len(groups)} lesson(s); {verb} {src} in the authoring sources and {db} in the index")
    for d in drift[:20]:
        print(f"  REFUSED {d}")
    if drift:
        print("\nNOTHING WAS WRITTEN, in either layer.")
        return 2
    return 1 if (args.check and (src or db)) else 0


if __name__ == "__main__":
    sys.exit(main())
