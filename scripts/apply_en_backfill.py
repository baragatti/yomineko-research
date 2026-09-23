#!/usr/bin/env python3
"""W40 — apply the derivable half of the `en` backfill (nothing authored).

Reads `research/derived/repairs/en_backfill_derived.json` (derived by the W40 derivation, see
research/reports/w40_derive_report.md: translation memory over the index's own en for the identical
pt-BR string, plus JMdict sense joins for token glosses) and writes one `localized_text` row
(entity_type, entity_id, field, 'en', layer 'B') per sentence-side row.

Rows are addressed by the export's stable address (sentence slug + `tokens[i]` / `particles[i]` in the
exporter's own order), never by the storage row id, and the pt-BR the row was derived from must still
be the index's pt-BR: a row whose source text moved is refused, not re-applied onto new text.
Kana rows (`db: null`) are builder literals: scripts/ingest/build_kana.py emits them from the same
template, and scripts/validate/validate_repairs_applied.py asserts both halves against the export.

IDEMPOTENT: an identical en already present is left alone; a different en refuses.
Usage: apply_en_backfill.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_SCRIPTS = next(p for p in Path(__file__).resolve().parents if p.name == "scripts")
sys.path.append(str(_SCRIPTS))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
TABLE = ROOT / "research" / "derived" / "repairs" / "en_backfill_derived.json"
LOCATOR = re.compile(r"^(tokens|particles)\[(\d+)\]$")
# the exporter's orders (scripts/export/export_corpus.py export_sentences)
ORDER = {"tokens": ("token", "SELECT id FROM token WHERE sentence_id=? ORDER BY split_mode, position"),
         "particles": ("particle", "SELECT id FROM particle WHERE sentence_id=? ORDER BY id")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    rows = json.loads(TABLE.read_text(encoding="utf-8"))["rows"]
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    sid_of = dict(con.execute("SELECT slug, id FROM sentence"))
    if not sid_of:
        print("apply_en_backfill: partial index (no sentences) - out of scope, nothing to do")
        return 0

    ids_cache: dict[tuple[int, str], list[int]] = {}
    problems: list[str] = []
    written = done = builder = 0
    for r in rows:
        if r["db"] is None:
            builder += 1
            continue
        addr = f"{r['id']} {r['locator']}.{r['field']}"
        m = LOCATOR.match(r["locator"] or "")
        sid = sid_of.get(r["id"])
        if not m or sid is None:
            problems.append(f"{addr}: no such sentence / unsupported locator")
            continue
        coll, i = m.group(1), int(m.group(2))
        etype, q = ORDER[coll]
        ids = ids_cache.setdefault((sid, coll), [x for (x,) in con.execute(q, (sid,))])
        if i >= len(ids) or etype != r["db"]["entity_type"]:
            problems.append(f"{addr}: locator does not resolve")
            continue
        eid, field = ids[i], r["db"]["field"]
        pt = con.execute("SELECT value, is_list FROM localized_text WHERE entity_type=? AND entity_id=? "
                         "AND field=? AND locale='pt-BR'", (etype, eid, field)).fetchone()
        if pt is None or pt[0] != r["pt"]:
            problems.append(f"{addr}: pt-BR moved ({pt[0] if pt else None!r} vs {r['pt']!r})")
            continue
        en = con.execute("SELECT value FROM localized_text WHERE entity_type=? AND entity_id=? "
                         "AND field=? AND locale='en'", (etype, eid, field)).fetchone()
        if en is not None:
            if en[0] == r["en"]:
                done += 1
            else:
                problems.append(f"{addr}: index already holds en {en[0]!r}, table says {r['en']!r}")
            continue
        written += 1
        if not args.check:
            con.execute("INSERT INTO localized_text (entity_type,entity_id,field,locale,value,is_list,layer) "
                        "VALUES (?,?,?,'en',?,?,'B')", (etype, eid, field, r["en"], pt[1]))

    if not args.check and not problems:
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"apply_en_backfill: {len(rows)} row(s): {verb} {written}, {done} already applied, "
          f"{builder} builder-literal (kana)")
    for p in problems[:15]:
        print(f"  ! {p}")
    if problems:
        print(f"\n{len(problems)} problem(s). NOTHING WAS COMMITTED.")
        return 2
    return 1 if (args.check and written) else 0


if __name__ == "__main__":
    sys.exit(main())
