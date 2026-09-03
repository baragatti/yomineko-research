#!/usr/bin/env python3
"""Apply the level-evidence repairs owner decision A4 asked for (W10).

WHAT IS BROKEN. `level_confidence` is derived from `level_agreement`, never asserted on its own
(contracts/common.schema.json -> LevelTag). Where the two disagree, exactly one of them is the record
of what actually happened and the other is a typo with a decimal point in it. This script lands the
cases where the AGREEMENT STRING is the wrong one, and never the other way round:

  * 132 N3 grammar records (`gram:n3-*`) say `level_agreement "1/1"` beside `level_confidence 0.34`.
    0.34 is one list out of the three N3 lineages the campaign consulted -- the same evidence their
    1,596 N3 vocab siblings already write as "1/3" (scripts/ingest/ingest_n3.py:186 against
    scripts/ingest/ingest_n3_grammar.py:71, which typed the denominator as the number of lists that
    had an OPINION). Reading "1/1" as 1.0 instead would convert the weakest level evidence in the
    corpus into a claim of certainty, so the STRING moves to "1/3" and the confidence is untouched.
  * 67 kanji carry a list ratio ("4/4", "3/3", "1/1") at confidence 1.0 on a record that NOT ONE of
    the cited lists places at that level -- the tally is for the level the lists chose, left behind
    when the JLPT re-tag moved the record. Every one of them already carries `level_sources.anchor`
    (`jlpt_anchor:n5` / `:n4` / `:not-in-n5n4`), which is the contract's own name for a deliberate
    course placement with no list to cite. They move to the `anchor` sentinel, whose documented
    confidence is 1.0 -- which is what they already store, so again nothing moves but the string.
  * `vocab:1385390` (接見) pairs the `0` sentinel with confidence 0.5. `0` means "author-added, we are
    guessing" and the contract fixes its confidence at 0.0; 0.5 is the midpoint of a scale nobody
    consulted. The sentinel is right, the number beside it is not.

WHAT IS NOT TOUCHED. No `level` changes. No confidence is RECOMPUTED -- the class the audit calls
(b), "confidence wrong / string right", is reported by the recompute and deliberately left alone;
there are zero of them in the corpus today. The collapsed `jlpt-lists` key on 4,446 N2/N1 vocab and
the single-list N3 evidence itself are gap G5, a different decision.

THE TABLE. research/derived/repairs/level_evidence_repairs.json -- tracked, one row per record, each
carrying the recomputed values AND the `level_sources` the recompute read, so the run is auditable
without this script. It also states the formula it was derived from (design/schema_v2.md section on
level evidence, from scripts/ingest/reconcile_levels.py :: assign()).

WHAT IT WRITES. Both halves of the same fact: `db/corpus.sqlite` (the regenerable index) and the
exported `corpus/{kanji,vocab,grammar}/*.json` (canonical, CLAUDE.md). The JSON write is a
field-level edit -- it re-serialises with the exporter's own `json.dumps(..., ensure_ascii=False,
indent=2) + "\n"`, so a subsequent `export_corpus.py` reproduces the file byte for byte (verified on
a copied tree in W10). `--db-only` suppresses the JSON half, which is how the rebuild manifest runs
it: there the exporter produces the tree afterwards.

Idempotent, exact-precondition: a row applies only when the stored pair equals `old_*`; a row already
holding `new_*` is a no-op; ANY other value is SKIPPED, reported and exits 1 -- it is never guessed at
or overwritten. So a second run reports 0 changes and `--check` after an apply exits clean.

Usage: apply_level_evidence.py [--check] [--db-only] [--group NAME ...] [--data PATH] [--root PATH]
                               [--db PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
DATA = ROOT / "research" / "derived" / "repairs" / "level_evidence_repairs.json"

# entity -> the table that holds it. All three address rows by `slug`.
TABLES = {"kanji": "kanji", "vocab": "vocab", "grammar": "grammar_point"}
EPS = 1e-9  # level_confidence survives a JSON/SQLite round trip exactly; this only guards the compare


def same(a, b) -> bool:
    """Stored value equals the expected one. Numbers compare numerically, everything else by value."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) <= EPS
    return a == b


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report, write nothing")
    ap.add_argument("--db-only", action="store_true",
                    help="write the index only; the exporter produces the JSON afterwards (rebuild path)")
    ap.add_argument("--json-only", action="store_true", help="write the exported JSON only")
    ap.add_argument("--group", action="append", default=[],
                    help="restrict to a named group (repeatable); default: every group in the table")
    ap.add_argument("--data", default=str(DATA), help="the repair table")
    ap.add_argument("--root", default=str(ROOT), help="repo root holding corpus/ (default: this checkout)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    doc = json.loads(Path(args.data).read_text(encoding="utf-8"))
    rows = doc["rows"]
    if args.group:
        rows = [r for r in rows if r["group"] in set(args.group)]
    if not rows:
        print("apply_level_evidence: no rows selected — FAIL")
        return 1
    print(f"apply_level_evidence: {len(rows)} rows from {Path(args.data).name}"
          f"{' [check]' if args.check else ''}")

    stats: dict[tuple[str, str], int] = defaultdict(int)
    skipped: list[str] = []

    # ---------------------------------------------------------------- the exported JSON (canonical)
    if not args.db_only:
        by_file: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for r in rows:
            by_file[(r["entity"], r["file"])].append(r)
        for (ent, fname), group in sorted(by_file.items()):
            path = root / "corpus" / ent / fname
            if not path.exists():
                skipped.append(f"{ent}/{fname}: file missing under {root}")
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            index = {str(rec.get("slug") or rec.get("id")): rec for rec in data}
            dirty = False
            for r in group:
                rec = index.get(r["address"])
                if rec is None:
                    skipped.append(f"json {r['entity']} {r['address']}: not in {fname}")
                    continue
                agr, conf = rec.get("level_agreement"), rec.get("level_confidence")
                if same(agr, r["new_agreement"]) and same(conf, r["new_confidence"]):
                    stats[(r["group"], "json already")] += 1
                elif same(agr, r["old_agreement"]) and same(conf, r["old_confidence"]):
                    rec["level_agreement"] = r["new_agreement"]
                    rec["level_confidence"] = r["new_confidence"]
                    stats[(r["group"], "json applied")] += 1
                    dirty = True
                else:
                    skipped.append(f"json {r['entity']} {r['address']}: holds "
                                   f"({agr!r}, {conf!r}), expected ({r['old_agreement']!r}, "
                                   f"{r['old_confidence']!r}) — not overwritten")
            if dirty and not args.check:
                # the exporter's own writer (scripts/export/export_corpus.py :: jw)
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # -------------------------------------------------------------------- the index (regenerable)
    if not args.json_only:
        if not DB.exists():
            skipped.append(f"db: {DB} does not exist")
        else:
            con = sqlite3.connect(DB)
            con.execute("PRAGMA busy_timeout=60000")
            con.execute("PRAGMA foreign_keys = ON")
            # A rebuild in --quick mode (validate_index_rebuildable.py) reconstructs ONE entity
            # family; the other tables exist but are empty. Rows addressing an empty table are out
            # of this index's scope, not missing — counted, never a failure. In a full rebuild every
            # table is populated, so a row that is genuinely absent still lands in `skipped`.
            populated = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] > 0
                         for t in set(TABLES.values())}
            for r in rows:
                tbl = TABLES[r["entity"]]
                if not populated[tbl]:
                    stats[(r["group"], "db out-of-scope")] += 1
                    continue
                got = con.execute(f"SELECT level_agreement, level_confidence FROM {tbl} WHERE slug=?",
                                  (r["address"],)).fetchone()
                if got is None:
                    skipped.append(f"db {r['entity']} {r['address']}: no such row in {tbl}")
                    continue
                agr, conf = got
                if same(agr, r["new_agreement"]) and same(conf, r["new_confidence"]):
                    stats[(r["group"], "db already")] += 1
                elif same(agr, r["old_agreement"]) and same(conf, r["old_confidence"]):
                    if not args.check:
                        con.execute(f"UPDATE {tbl} SET level_agreement=?, level_confidence=? WHERE slug=?",
                                    (r["new_agreement"], r["new_confidence"], r["address"]))
                    stats[(r["group"], "db applied")] += 1
                else:
                    skipped.append(f"db {r['entity']} {r['address']}: holds ({agr!r}, {conf!r}), "
                                   f"expected ({r['old_agreement']!r}, {r['old_confidence']!r}) — not overwritten")
            if args.check:
                con.rollback()
            else:
                con.commit()
            con.close()

    for k in sorted(stats):
        print(f"  {k[0]:22} {k[1]:14} {stats[k]:5}")
    if skipped:
        print(f"  SKIPPED {len(skipped)} (stored value is neither the defect nor the repair):")
        for s in skipped[:20]:
            print("    -", s)
        if len(skipped) > 20:
            print(f"    ... {len(skipped) - 20} more")
    print(f"apply_level_evidence: {'DRY RUN' if args.check else 'written'} — "
          f"{sum(stats.values())} row-halves accounted, {len(skipped)} skipped")
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
