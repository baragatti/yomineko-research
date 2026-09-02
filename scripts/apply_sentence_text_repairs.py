#!/usr/bin/env python3
"""Strip corpus bookkeeping and mis-taught particle scaffolds out of learner-facing sentence text.

Two defects, both in `localized_text` rows hanging off `sentence`, both found by a deterministic
detector and then rewritten field by field:

  * `structure_explanation` (159 fields) leaked PRODUCTION BOOKKEEPING into the one field whose job
    is to explain how the sentence works -- "O alvo aqui é cobertura de vocabulário N4", "the focus
    of the N4 coverage target", "a coverage sentence, with no specific grammar point". Which words
    the corpus still needed to cover is a fact about our build queue, not about Japanese, and a
    learner cannot act on it. Worse, several of those clauses were the only closing sentence in the
    field, so the field ended by telling the reader there was nothing here to learn.

  * `translation_literal` (337 fields) is a SCAFFOLD: it mirrors the Japanese chunk by chunk so the
    reader can see which particle does what. "Quanto a X" is the gloss design/translation_style.md
    reserves for the topic marker は -- so putting it on a chunk the sentence actually marks with
    が/を/に misteaches the very particle the field exists to explain. Some rows contradicted
    themselves inside one string ("Quanto ao gato (が marca o sujeito)"); some invented a topic for
    a sentence that has none; a further group rendered the そ-series demonstrative その as "aquele",
    which belongs to あの.

Each rewrite removes ONLY the defect. Real pedagogy already in the field is kept, and where deleting
a bookkeeping clause left the field thin, the replacement is drawn from that same record's own
particle/token dissection -- never invented. A few rows are detector false positives (Sudachi fused
今晩 + は into one token, って and the zero-particle topic are genuine topics that are not は); those
keep the topic reading and simply name the particle that licenses it.

DB ONLY. This writes `db/corpus.sqlite` and nothing else. `corpus/sentences/bank.json` is exported
from the DB by the orchestrator afterwards -- do not run an exporter from here.

Idempotent: every edit is matched on its EXACT current DB value, so a second run reports 0 changes
and `--check` after an apply exits clean. A row whose stored text is neither the expected defective
value nor the finished rewrite is SKIPPED and reported; it is never overwritten.

Usage: apply_sentence_text_repairs.py [--check] [--data PATH]
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
DB = db_target(ROOT / "db" / "corpus.sqlite")

# The verified rewrite table: [{slug, field, locale, old, new, why}, ...]. `old` is the detector's
# snapshot of the DB, re-checked against the live rows when the file was assembled.
# The rewrite table is TRACKED, not session-scoped: the first version of this script pointed at a
# temp directory that disappears with the session, which would have left a committed script that
# could never be re-run or audited. --data PATH still overrides.
DATA = ROOT / "research" / "derived" / "repairs" / "sentence_text_repairs.json"

FIELDS = {"structure_explanation", "translation_literal"}
LOCALES = {"pt-BR", "en"}


def load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    seen: set[tuple[str, str, str]] = set()
    for i, r in enumerate(rows):
        missing = {"slug", "field", "locale", "old", "new"} - set(r)
        if missing:
            raise SystemExit(f"row {i}: missing key(s) {sorted(missing)}")
        if r["field"] not in FIELDS:
            raise SystemExit(f"row {i} ({r['slug']}): unexpected field {r['field']!r}")
        if r["locale"] not in LOCALES:
            raise SystemExit(f"row {i} ({r['slug']}): unexpected locale {r['locale']!r}")
        if r["old"] == r["new"]:
            raise SystemExit(f"row {i} ({r['slug']}): `new` is identical to `old`")
        key = (r["slug"], r["field"], r["locale"])
        if key in seen:
            raise SystemExit(f"row {i}: duplicate target {key}")
        seen.add(key)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report what would change; write nothing")
    ap.add_argument("--data", type=Path, default=DATA,
                    help="path to the verified rewrite table (JSON)")
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(f"rewrite table not found: {args.data}")
    rows = load(args.data)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed = 0
    already = 0
    skipped: list[str] = []

    for r in rows:
        slug, field, locale = r["slug"], r["field"], r["locale"]
        label = f"{slug}.{field} [{locale}]"

        hit = con.execute(
            "SELECT lt.entity_id, lt.value, lt.is_list "
            "FROM localized_text lt JOIN sentence s ON s.id = lt.entity_id "
            "WHERE lt.entity_type='sentence' AND s.slug=? AND lt.field=? AND lt.locale=?",
            (slug, field, locale)).fetchall()
        if not hit:
            skipped.append(f"{label}: no localized_text row")
            continue
        if len(hit) > 1:
            skipped.append(f"{label}: {len(hit)} rows match this slug -- not touching it")
            continue
        entity_id, value, is_list = hit[0]
        if is_list:
            skipped.append(f"{label}: stored as a list, expected scalar text")
            continue

        if value == r["new"]:
            already += 1                                   # already repaired; nothing to do
            continue
        if value != r["old"]:
            skipped.append(f"{label}: current value matches neither the expected defective text "
                           f"nor the rewrite -- not touching it")
            continue

        print(f"  {label}")
        if r.get("why"):
            print(f"     why: {r['why']}")
        if not args.check:
            con.execute(
                "UPDATE localized_text SET value=? WHERE entity_type='sentence' AND entity_id=? "
                "AND field=? AND locale=?", (r["new"], entity_id, field, locale))
        changed += 1

    if not args.check:
        con.commit()
    con.close()

    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} field(s) of {len(rows)}; {already} already carried the rewrite")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
