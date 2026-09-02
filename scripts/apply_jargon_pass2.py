#!/usr/bin/env python3
"""Second pass over `structure_explanation`: strip the corpus bookkeeping the first pass missed.

`structure_explanation` is learner-facing — it explains how the sentence works. Which words the CORPUS
needed to cover is production bookkeeping and means nothing to a learner, so lines like

    "O alvo é cobertura N4; o ponto central é ために expressando propósito."
    "Target (coverage) is general N4 vocabulary/usage, no specific grammar point."

do not belong in the field at all.

A first pass (`research/derived/repairs/sentence_text_repairs.json`, 496 fields) already removed the
long form of this leak, but its detector required the full phrase "cobertura de vocabulário" and so
walked past the bare "cobertura N4" / "coverage" / "alvo lexical" variants. 221 fields were left. 92 of
them are the OTHER-LOCALE TWIN of a field the first pass repaired, which is worse than a uniform
defect: the sentence reads clean in one language and still announces its corpus target in the other,
so the two locales of one record disagree about what the sentence teaches.

The repairs are NOT blind deletions. Every piece of real pedagogy in the field is kept; only the
bookkeeping goes. Where the bookkeeping clause was also *carrying* a teaching point ("o ponto-chave é
〜なさい"), that point is restated as plain grammar, and where cutting it would leave the field thin the
explanation is extended from the record's own dissection (its tokens and particle notes) or from the
already-repaired twin in the other locale, so both locales of a record end on the same point.

The table lives at `research/derived/repairs/jargon_pass2_repairs.json` — tracked, so the repair
survives the session that produced it and can be re-run or audited later. (The first pass left its
working table in a session-scoped temp directory; this one does not.)

DB only. `corpus/sentences/bank.json` is regenerated from the DB by the exporter afterwards, so this
script must not touch it — running an exporter here would be the orchestrator's job, not this one's.

Idempotent: every edit is matched on its EXACT current DB value, so a second run reports 0 changes.
A row whose value is neither the expected `old` nor the finished `new` is reported loudly and left
untouched — never overwritten on a guess.

Usage: apply_jargon_pass2.py [--check] [--data PATH]
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
DATA = ROOT / "research" / "derived" / "repairs" / "jargon_pass2_repairs.json"

ENTITY_TYPE = "sentence"
FIELD = "structure_explanation"
REQUIRED = ("slug", "field", "locale", "old", "new", "why")


def load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit(f"{path}: expected a JSON list of repairs")
    seen: set[tuple[str, str]] = set()
    for i, r in enumerate(rows):
        missing = [k for k in REQUIRED if k not in r]
        if missing:
            raise SystemExit(f"{path}[{i}]: missing key(s) {', '.join(missing)}")
        if r["field"] != FIELD:
            raise SystemExit(f"{path}[{i}]: field is {r['field']!r}, expected {FIELD!r}")
        key = (r["slug"], r["locale"])
        if key in seen:
            raise SystemExit(f"{path}[{i}]: duplicate edit for {key[0]} / {key[1]}")
        seen.add(key)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--data", type=Path, default=DATA, help="repair table (default: the tracked one)")
    args = ap.parse_args()

    rows = load(args.data)
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed, already, skipped = 0, 0, []

    for r in rows:
        slug, locale, old, new, why = r["slug"], r["locale"], r["old"], r["new"], r["why"]
        label = f"{slug} [{locale}]"

        hit = con.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
        if hit is None:
            skipped.append(f"{label}: no such sentence")
            continue
        sid = hit[0]

        got = con.execute(
            "SELECT value, is_list FROM localized_text WHERE entity_type=? AND entity_id=? "
            "AND field=? AND locale=?", (ENTITY_TYPE, sid, FIELD, locale)).fetchone()
        if got is None:
            skipped.append(f"{label}: no localized_text row for {FIELD}")
            continue
        value, is_list = got
        if is_list:
            skipped.append(f"{label}: row is a list, not scalar text — not touching it")
            continue
        if value == new:
            already += 1
            continue
        if value != old:
            skipped.append(f"{label}: current value does not match the expected text — not touching it")
            continue

        print(f"  {label}\n     why: {why}")
        if not args.check:
            con.execute(
                "UPDATE localized_text SET value=? WHERE entity_type=? AND entity_id=? AND field=? "
                "AND locale=?", (new, ENTITY_TYPE, sid, FIELD, locale))
        changed += 1

    if not args.check:
        con.commit()
    con.close()

    verb = "would repair" if args.check else "repaired"
    print(f"\n{verb} {changed} field(s) of {len(rows)}; {already} already carried the repaired text")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
