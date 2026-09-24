#!/usr/bin/env python3
"""W08b (owner decision A3) — the record repairs and the prose that land around the eight grammar merges.

`scripts/migrate_grammar_merge.py` merges the eight duplicate pairs (its MERGES rows 3-10). Two things
cannot live inside that generic machinery, and both are rows of the tracked, exact-match table
`research/derived/repairs/w08b_merges.json`:

  --phase pre    the `pre-merge` rows (R1, R2), BEFORE the merge. A defect on a loser is repaired
                 first, never inherited: gp-60's forms[0] is the broken 'ら' (merged as is, the
                 survivor `tara` would gain the form ら, a gloss keyed ら and also_known_as 'ら'), and
                 gp-54 baked the copula into its form (のがじょうずです) and so carries `polite`, which
                 the merge would append to `no-ga-jouzu.register` — exactly what W31's
                 grammar_register.json row 0 removed. Afterwards both rows retire with their loser.
  --phase prose  the `prose` rows, AFTER the merge: the ONE pt-BR explanation / formation / nuance per
                 survivor that replaces the two independently authored texts (24 rows, 9 of them the
                 verifier's corrected text). The migration itself only salvages prose; choosing and
                 reconciling it is authoring, which is why it is a separate, reviewed table. The
                 loser's texts stay on its kept row, and the survivor keeps needs_review = 1.

Both layers: the table is the authoring layer (replayed by validate_repairs_applied.py); this script
writes the index (`grammar_point` columns and `localized_text`), and export_corpus.py republishes
corpus/grammar/*.json.

IDEMPOTENT. A row already at `new` is counted and left alone. A row at neither `old` nor `new` is a
DRIFT: refused (exit 2, nothing written) on the live index, applied anyway on a replay target, the
`apply_grammar_register_repairs.py` idiom — a from-scratch replay is a different graph by construction
and validate_index_rebuildable.py's byte diff is what checks it.

P2-gp153 (D5b, gp-153 -> gp-77) is a second table of the same shape, `gp153_merge.json`: its prose rows
replace D5's gp-77 texts (their `old` is D5's `new`, and D5's rows carry `superseded_by`), so it runs as
its own step AFTER the w08b prose step.

Usage: apply_w08b_merges.py --phase pre|prose [--table w08b_merges.json|gp153_merge.json] [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.path.append(str(next(p for p in Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "db" / "corpus.sqlite"
DB = db_target(LIVE)
REPAIRS = ROOT / "research" / "derived" / "repairs"
TABLES = ("w08b_merges.json", "gp153_merge.json")
TABLE = REPAIRS / TABLES[0]
JSON_COLUMNS = {"forms_json", "register_json", "formation_steps_json"}


def load_rows(kind: str) -> list[dict]:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return [r for r in doc["rows"] if r["kind"] == kind]


def jdumps(o) -> str:
    return json.dumps(o, ensure_ascii=False)


def read_value(con: sqlite3.Connection, gid: int, r: dict):
    """(present, current value) of the field a row addresses, decoded the way the row states it."""
    if "column" in r:
        col = r["column"]
        if col == "references_json.label_en":
            raw = con.execute("SELECT references_json FROM grammar_point WHERE id=?", (gid,)).fetchone()[0]
            return True, (json.loads(raw) if raw else {}).get("label_en")
        raw = con.execute(f"SELECT {col} FROM grammar_point WHERE id=?", (gid,)).fetchone()[0]
        return True, (json.loads(raw) if raw else None) if col in JSON_COLUMNS else raw
    got = con.execute("SELECT value FROM localized_text WHERE entity_type='grammar_point' AND entity_id=? "
                      "AND field=? AND locale=?", (gid, r["field"], r["locale"])).fetchone()
    if got is None:
        return False, None
    return True, (json.loads(got[0]) if r["field"] == "form_meanings" and got[0] else got[0])


def write_value(con: sqlite3.Connection, gid: int, r: dict) -> None:
    new = r["new"]
    if "column" in r:
        col = r["column"]
        if col == "references_json.label_en":
            raw = con.execute("SELECT references_json FROM grammar_point WHERE id=?", (gid,)).fetchone()[0]
            refs = json.loads(raw) if raw else {}
            refs["label_en"] = new
            con.execute("UPDATE grammar_point SET references_json=? WHERE id=?", (jdumps(refs), gid))
        else:
            con.execute(f"UPDATE grammar_point SET {col}=? WHERE id=?",
                        (jdumps(new) if col in JSON_COLUMNS else new, gid))
        return
    val = jdumps(new) if r["field"] == "form_meanings" else new
    con.execute(
        "INSERT INTO localized_text(entity_type, entity_id, field, locale, value, is_list, layer) "
        "VALUES ('grammar_point',?,?,?,?,?,'C') "
        "ON CONFLICT(entity_type, entity_id, field, locale) DO UPDATE SET value=excluded.value",
        (gid, r["field"], r["locale"], val, 1 if r["field"] == "form_meanings" else 0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("pre", "prose"), required=True)
    ap.add_argument("--table", choices=TABLES, default=TABLES[0])
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    global TABLE
    TABLE = REPAIRS / args.table
    live = Path(DB).resolve() == LIVE.resolve()
    rows = load_rows("pre-merge" if args.phase == "pre" else "prose")
    merges = {r["winner"]: r["loser"] for r in load_rows("merge")}

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    changed = already = 0
    drift: list[str] = []
    missing: list[str] = []
    for r in rows:
        if r.get("superseded_by") and live:
            # a later table's row consumed this one (its `old` is this `new`); on a replay the chain
            # runs in order, so only the live index skips it
            already += 1
            continue
        # (no deprecated_by here: on a replay the pre phase runs before the merge adds that column)
        g = con.execute("SELECT id FROM grammar_point WHERE key=?", (r["key"],)).fetchone()
        what = f"{r['key']}.{r.get('column') or r['field'] + '/' + r['locale']}"
        if g is None:
            missing.append(f"{what}: no grammar point {r['key']!r} in this index")
            continue
        gid = g[0]
        if args.phase == "prose" and live:
            dep = con.execute("SELECT deprecated_by FROM grammar_point WHERE key=?",
                              (merges[r["key"]],)).fetchone()
            if not dep or dep[0] != f"gram:{r['key']}":
                missing.append(f"{what}: loser {merges[r['key']]!r} is not merged into it yet "
                               f"(deprecated_by={dep and dep[0]!r}); run migrate_grammar_merge.py first")
                continue
        present, cur = read_value(con, gid, r)
        if present and cur == r["new"]:
            already += 1
            continue
        if not present or cur != r["old"]:
            note = f"{what}: stored {cur!r:.120}, the row's `old` is {r['old']!r:.120}"
            if live:
                drift.append(note)
                continue
            print(f"  DRIFT (non-live index, applying anyway) {note}")
        changed += 1
        if not args.check:
            write_value(con, gid, r)
            if args.phase == "prose":
                con.execute("UPDATE grammar_point SET needs_review=1 WHERE id=?", (gid,))
    problems = drift + (missing if live else [])
    for m in missing if not live else []:
        print(f"  [replay] {m}")
    if problems:
        for p in problems:
            print(f"  REFUSED {p}")
        con.rollback()
        print(f"[FAIL] {len(problems)} row(s) do not match the live index; nothing written")
        return 2
    if not args.check:
        con.commit()
    con.close()
    verb = "would change" if args.check else "changed"
    print(f"apply_w08b_merges --phase {args.phase} --table {args.table}: {len(rows)} row(s); {verb} {changed}, "
          f"already applied {already}")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
