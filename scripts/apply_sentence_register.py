#!/usr/bin/env python3
"""W31 (A8 / owner decision D7) — write `register` and `register_rule` onto every bank sentence.

WHAT WAS MISSING
----------------
Selection into the speaking path is mechanical — a seed lemma plus the known set — so nothing in the
pipeline could tell a polite request from a Bible verse. `course/speak/` shipped 心熱けれど肉体は弱し
as a production prompt, お前は脳の半分があったら，危ない! as a drill and 痔があります in `health`
(PENDING.md A8). The 2026-09-01 speak-builder campaign could not build the filter the decision asks
for, because the corpus had no sentence-level register at all: `vocab.register` is a word-level
JMdict tag that exports null, and `grammar_point.register` is a property of the POINT, not of an
utterance. Its census reported 645 say_now/production items of which 383 carried no register signal
of any kind, and printed the zeros for archaic/epistolary/vulgar as *unrecordable* rather than
*absent*.

WHAT THIS APPLIES
-----------------
`research/derived/repairs/sentence_register.json` — the exact-match table
`scripts/derive_sentence_register_v2.py` writes, 10,112 rows `{key, set, level, jp, register, rule,
signals, confidence, conflicts, needs_review}`. THE VALUE IS IN THE TABLE and this script only
places it: nothing here decides a register, and a row that does not resolve against the current tree
is reported and skipped, never adapted.

TWO KEY KINDS, ON PURPOSE
-------------------------
  * `set == "bank"` — the key IS the bank slug (`sent:tatoeba-…` / `sent:gen-…`), 5,889 rows. These
    are what this run applies.
  * `set == "w13"` — `tatoeba-<id>` for a mined row and `gen-<sha1(jp)[:12]>` for a generated one,
    4,223 rows addressing sentences that are NOT in the bank yet. The hash scheme is the one
    `scripts/ingest/prepare_generated.py` already uses for `sent:gen-…`, so the slug those rows will
    have after the W13 ingest is settled and stable: `sent:` + the key.

    This script accepts both kinds and applies whatever resolves TODAY. A W13 key that already names
    a bank sentence is applied like any other row (that is what makes this script correct on the day
    W13 lands); a key that names nothing is counted as deferred and left for the W13 ingest, which
    reads this table for the value instead of re-deriving one. `validate_repairs_applied.py` asserts
    the deferral rather than trusting it — the moment such a slug appears in the export without the
    row's value, the marking stops being true and the gate fails.

RESIDUE IS NULL, NEVER `neutral`
--------------------------------
130 rows (76 in the bank) carry `register: null`, rule `no-signal`: a fragment with no predicate on
its final bunsetsu and no lexical or grammatical marker (中サイズのコーヒーを一つ, 調子はどう？). They
are written as NULL and stamped `needs_review`. Rounding them up to `neutral` would be the one
mistake this field cannot afford: a defaulted neutral passes the speaking-path filter silently,
which is exactly the failure the field exists to prevent.

BOTH LAYERS
-----------
The tracked table is the authoring layer (the decision, exact-match, replayed by
`validate_repairs_applied.py`, regenerable by the derivation); this script writes the index
`db/corpus.sqlite`, and `scripts/export/export_corpus.py` republishes `corpus/sentences/bank.json`,
which is canonical.

LESSONS DO NOT MOVE. `register` is consumed by `course/speak/` only (design/schema_v2.md,
A8: "yes; must not impact the lessons"), and this script touches no lesson, exercise or exam row.

IDEMPOTENT. A sentence already carrying the row's value is left alone; a second run reports 0
changes.

Run `scripts/export/export_corpus.py` afterwards.
Usage: apply_sentence_register.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
# The table is a committed INPUT to the rebuild, so it is read from the repo, never from --out-root.
TABLE = ROOT / "research" / "derived" / "repairs" / "sentence_register.json"

D7 = ("neutral", "polite", "casual", "formal", "vulgar", "archaic", "epistolary", "dialect", "slang")


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    rows = doc["rows"]
    n = (doc.get("counts") or {}).get("rows")
    if n is not None and n != len(rows):
        raise SystemExit(f"{TABLE.name}: counts.rows {n} != {len(rows)} rows")
    bad = [r["key"] for r in rows if r["register"] is not None and r["register"] not in D7]
    if bad:
        raise SystemExit(f"{TABLE.name}: {len(bad)} row(s) carry a value outside the D7 set: "
                         f"{bad[:5]}")
    unruled = [r["key"] for r in rows if not r.get("rule")]
    if unruled:
        raise SystemExit(f"{TABLE.name}: {len(unruled)} row(s) carry no rule: {unruled[:5]}")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    doc = load_table()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    cols = {d[1] for d in con.execute("PRAGMA table_info(sentence)")}
    if not {"register", "register_rule"} <= cols:
        print("[FAIL] sentence has no register/register_rule column — run "
              "scripts/ingest/init_db.py (migration 017) first")
        return 2

    ids = {slug: sid for slug, sid in con.execute("SELECT slug, id FROM sentence")}
    changed = already = deferred = 0
    by_register: Counter = Counter()
    by_level: Counter = Counter()
    residue_written = 0

    for r in doc["rows"]:
        key = r["key"]
        sid = ids.get(key)
        if sid is None and not key.startswith("sent:"):
            # The W13 key kind. `sent:` + key is the slug that row will have once the W13 ingest
            # runs; applying it the day it exists is what keeps this script correct then.
            sid = ids.get("sent:" + key)
        if sid is None:
            deferred += 1
            continue
        reg, rule = r["register"], r["rule"]
        cur = con.execute("SELECT register, register_rule, needs_review FROM sentence WHERE id=?",
                          (sid,)).fetchone()
        want_nr = 1 if reg is None else cur[2]
        if cur[0] == reg and cur[1] == rule and cur[2] == want_nr:
            already += 1
        else:
            changed += 1
            if not args.check:
                con.execute("UPDATE sentence SET register=?, register_rule=?, needs_review=? "
                            "WHERE id=?", (reg, rule, want_nr, sid))
        by_register[reg or "null"] += 1
        by_level[(r.get("level") or "?", reg or "null")] += 1
        if reg is None:
            residue_written += 1

    if args.check:
        con.rollback()
    else:
        con.commit()
    con.close()

    print(f"sentence register: {changed} written, {already} already applied, {deferred} deferred "
          f"(W13 rows whose sentence is not in the bank yet)"
          + (" [CHECK, nothing written]" if args.check else ""))
    print("  by register: " + ", ".join(f"{k}={v}" for k, v in by_register.most_common()))
    print(f"  residue (register NULL, needs_review): {residue_written}")
    levels = sorted({lv for lv, _ in by_level})
    for lv in levels:
        row = {reg: n for (l2, reg), n in by_level.items() if l2 == lv}
        print(f"  {lv}: " + ", ".join(f"{k}={v}" for k, v in sorted(row.items())))
    print("Run scripts/export/export_corpus.py afterwards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
