#!/usr/bin/env python3
"""W31 — repair `grammar_point.register` where the tag claims a politeness the point does not impose.

WHAT WAS WRONG
--------------
`research/reports/w31_derive_report.md` §3.2. The sentence-register derivation reads each sentence's
predicate off its last bunsetsu, and it also reads the `register` tagged on the grammar points that
sentence illustrates. 746 sentences disagreed with their points. 701 of those are NOT defects: a
point tagged `plain` describes the FORM the point attaches to (te-form, から, なら, ても), and those
forms sit happily inside です／ます sentences. The other 27 rows come from 13 grammar points whose
own tag is the thing that is wrong — `no-ga-suki` and `hazu-da` marked `polite` although のが好き and
はず carry no politeness morphology at all, `けっこう` marked `casual` although every bank sentence
that uses it is a polite refusal.

THE RULE
--------
`grammar_point.register` states the register the point's OWN FORMS impose. A form with no politeness
morphology imposes none -> `neutral`. A stylistic axis (`colloquial` against `literary`) is not a
politeness level, so it is kept BESIDE `neutral` instead of replacing it — which is exactly what
`scripts/derive_sentence_register_v2.py` needs, because it promotes a sentence only when a point's
register maps to EXACTLY ONE D7 value.

WHAT THIS APPLIES
-----------------
`research/derived/repairs/grammar_register.json` — 8 rows `{key, field, old, new, old_scalar,
new_scalar, why}`, plus a `held` block naming the 5 points this campaign deliberately did NOT change
and why (お／ご is genuinely honorific; ～てもいいです really does carry です; て くれない・てもらえない,
って and よ are correctly tagged and their conflicts are link/forms defects for another unit).

BOTH LAYERS
-----------
The tracked table is the authoring layer (the decision, exact-match, replayed by
`validate_repairs_applied.py`); this script writes the index `db/corpus.sqlite`
(`grammar_point.register` and `grammar_point.register_json` — the exporter prefers the JSON and falls
back to the scalar, so leaving either behind publishes the old value), and
`scripts/export/export_corpus.py` republishes `corpus/grammar/*.json`, which is canonical.

ORDER MATTERS. `derive_sentence_register_v2.py` reads `corpus/grammar/*.json`, so the sentence
register table is re-derived only after this script has run AND the corpus has been re-exported.

IDEMPOTENT. A row already carrying `new` is reported as already-applied; a second run reports 0
changes. A row whose stored value is neither `old` nor `new` is a DRIFT failure and is refused
(exit 2) when the target is the live index — the `migrate_grammar_merge.py` idiom, so a from-scratch
replay against a partially-built index reports the mismatch and applies the repair instead of
aborting the manifest.

Usage: apply_grammar_register_repairs.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "db" / "corpus.sqlite"
DB = db_target(LIVE)
# The table is a committed INPUT to the rebuild, so it is read from the repo, never from --out-root.
TABLE = ROOT / "research" / "derived" / "repairs" / "grammar_register.json"


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    doc = load_table()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    live = Path(DB).resolve() == LIVE.resolve()

    changed = already = missing = 0
    drift: list[str] = []
    for r in doc["rows"]:
        key = r["key"]
        got = con.execute("SELECT id, register, register_json FROM grammar_point WHERE key=?",
                          (key,)).fetchone()
        if not got:
            missing += 1
            print(f"  {key}: no such grammar point in this index — skipped")
            continue
        gid, scalar, rjson = got
        cur = json.loads(rjson) if rjson else ([scalar] if scalar else None)
        if cur == r["new"] and scalar == r["new_scalar"]:
            already += 1
            continue
        if cur != r["old"] or scalar != r["old_scalar"]:
            note = (f"{key}: stored register is {scalar!r}/{cur!r}, the row's `old` is "
                    f"{r['old_scalar']!r}/{r['old']!r}")
            if live:
                drift.append(note)
                continue
            print(f"  DRIFT (non-live index, applying anyway) {note}")
        print(f"  {key}: register {scalar!r}/{cur!r} -> {r['new_scalar']!r}/{r['new']!r} (db)")
        changed += 1
        if not args.check:
            con.execute("UPDATE grammar_point SET register=?, register_json=? WHERE id=?",
                        (r["new_scalar"], json.dumps(r["new"], ensure_ascii=False), gid))

    if drift:
        for d in drift:
            print(f"  DRIFT {d}")
        print(f"[FAIL] {len(drift)} row(s) address a register this index does not carry; refusing "
              f"to overwrite an unexpected value on the live index")
        con.close()
        return 2

    if args.check:
        con.rollback()
    else:
        con.commit()
    con.close()
    print(f"grammar register: {changed} changed, {already} already applied, {missing} missing "
          f"({len(doc['held'])} points deliberately held — see the table's `held` block)"
          + (" [CHECK, nothing written]" if args.check else ""))
    print("Run scripts/export/export_corpus.py afterwards, then re-derive the sentence register.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
