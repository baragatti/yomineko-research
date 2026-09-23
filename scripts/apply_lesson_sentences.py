#!/usr/bin/env python3
"""W14. Apply the lesson sentence re-selection table to both layers.

WHAT IT WRITES
--------------
`research/derived/repairs/lesson_sentences.json`, derived by `scripts/derive_lesson_sentences.py`
(the rule is in that script's docstring; nothing in the table is authored). Every row is a literal
substitution on one lesson body, applied in table order within the lesson:

  add           `from` = the anchor the block goes before, `to` = block + anchor
  replace       `from` = the old `<sentence …/>` tag, `to` = the same tag on the new sentence
  remove        `from` = the tag (and its newline), `to` = ""
  drop-heading  `from` = an example heading left empty by the removals, `to` = ""
  chip          `from` = `<item><jp>KANA</jp>`, `to` = `<item><vocab ref="vocab:SLUG"/>`

A row is already applied when its `to` is in the body (or, for an empty `to`, when its `from` is
gone); otherwise `from` must occur exactly once, or nothing is committed.

BOTH LAYERS
-----------
`research/derived/lessons/<slug>.json` (body + its `sentence_refs` list, which `load_lessons.py`
turns into `lesson_sentence` on a replay) and `db/corpus.sqlite` (the pt-BR body in
`localized_text`, plus the `lesson_sentence` rows). The exporter derives the published
`sentence_refs` from the body. On a replay the committed sources already carry every row except
where an earlier step regenerates a source (build_exam_kanji_lessons.py re-chunks the eight
kanji-exame lessons), and there this step writes it again.

Idempotent. Run `scripts/export/export_course.py` afterwards, then re-derive `needs` (check C4):
`build_needs_table.py` -> `apply_lesson_needs.py --replace`.
Usage: apply_lesson_sentences.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
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
TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_sentences.json"
SENT_REF = re.compile(r'<sentence\s+ref="([^"]+)"')


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc


def by_lesson(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r["lesson"], []).append(r)
    return out


def edit(body: str, group: list[dict], where: str, problems: list[str]) -> tuple[str, int]:
    changed = 0
    for r in group:
        to, frm = r["to"], r["from"]
        if (to and to in body) or (not to and frm not in body):
            continue                                   # already applied
        n = body.count(frm)
        if n != 1:
            problems.append(f"{r['lesson']} {r['op']}: {where} carries {n} of {frm[:70]!r}")
            continue
        body = body.replace(frm, to)
        changed += 1
    return body, changed


def fix_refs(refs: list[str], group: list[dict], body: str) -> list[str]:
    """The source's own `sentence_refs` list, moved the way the rows move the body."""
    out = list(refs)
    shown = set(SENT_REF.findall(body))
    for r in group:
        if r["op"] == "replace":
            out = [r["sentence_in"] if s == r["sentence_out"] else s for s in out]
            if r["sentence_in"] not in out:
                out.append(r["sentence_in"])
        elif r["op"] == "remove":
            out = [s for s in out if s != r["sentence_out"] or s in shown]
        elif r["op"] == "add":
            out += [s for s in r["sentences"] if s not in out]
    return list(dict.fromkeys(out))


def apply_sources(groups, check, problems) -> int:
    changed = 0
    for lesson, group in groups.items():
        f = SRC / (lesson.split(":", 1)[1] + ".json")
        if not f.exists():
            problems.append(f"{lesson}: authoring source {f.name} missing")
            continue
        raw = f.read_text(encoding="utf-8")
        d = json.loads(raw)
        body, n = edit(d.get("body") or "", group, f.name, problems)
        refs = fix_refs(d.get("sentence_refs") or [], group, body)
        if (n or refs != (d.get("sentence_refs") or [])) and not check:
            d["body"] = body
            d["sentence_refs"] = refs
            out = json.dumps(d, ensure_ascii=False, indent=2)
            f.write_text(out + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
        changed += n
    return changed


def apply_db(con, groups, check, problems) -> int:
    changed = 0
    for lesson, group in groups.items():
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
        body, n = edit(row[0], group, "the index body", problems)
        if check:
            changed += n
            continue
        if n:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND "
                        "entity_id=? AND field='body' AND locale='pt-BR'", (body, lid))
        shown = set(SENT_REF.findall(body))
        for r in group:
            outs = [r.get("sentence_out")] if r["op"] in ("replace", "remove") else []
            ins = [r["sentence_in"]] if r["op"] == "replace" else r.get("sentences") or []
            for s in outs:
                if s and s not in shown:
                    con.execute("DELETE FROM lesson_sentence WHERE lesson_id=? AND sentence_id="
                                "(SELECT id FROM sentence WHERE slug=?)", (lid, s))
            for s in ins:
                sid = con.execute("SELECT id FROM sentence WHERE slug=?", (s,)).fetchone()
                if not sid:
                    problems.append(f"{lesson}: sentence {s} not in the index")
                    continue
                con.execute("INSERT OR IGNORE INTO lesson_sentence (lesson_id, sentence_id) "
                            "VALUES (?,?)", (lid, sid[0]))
        changed += n
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    doc = load_table()
    groups = by_lesson(doc["rows"])
    problems: list[str] = []
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    # dry pass over both layers first: a problem anywhere writes nothing anywhere
    src = apply_sources(groups, True, problems)
    db = apply_db(con, groups, True, problems)
    if not problems and not args.check:
        apply_sources(groups, False, problems)
        apply_db(con, groups, False, problems)
        con.commit()
    con.close()
    verb = "would apply" if args.check else "applied"
    print(json.dumps(doc["counts"], ensure_ascii=False))
    print(f"{verb} {src} row(s) in the authoring sources and {db} in the index over "
          f"{len(groups)} lesson(s); {len(doc.get('residue') or [])} breaching link(s) "
          f"held as residue")
    for p in problems[:15]:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS WRITTEN, in either layer.")
        return 2
    return 1 if (args.check and (src or db)) else 0


if __name__ == "__main__":
    sys.exit(main())
