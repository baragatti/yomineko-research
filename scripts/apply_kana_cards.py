#!/usr/bin/env python3
"""W29 — kana cards one glyph per card (decision D6): write the 211 glyph answer keys into the index.

Applies `research/derived/repairs/kana_cards.json` (derived in W29 by template substitution over the
Layer-A kana records; nothing authored). The CARD SET is not written here: `export_course._srs_cards`
fans every `kana-family` unlock out to its member glyphs, with `handwriting` only where
`kana_stroke` holds the glyph. What this script places is the part the ledger cannot give, the
production key, into `card_production_key` (migration 016) keyed (lesson, glyph id). A kana record
has no senses[], so `sense_index` stays NULL; `why` carries the template name.

Before writing, every row is checked against what the exporter will build on this index: the glyph
belongs to a family the row's lesson unlocks, and the row's `card_types` equal the fan-out's. A
disagreement means the table and the index describe different card sets, and the run refuses.

The retirement map (`migration[]`) is the review_log instruction for the runtime (no FSRS state
carried; the family card ids stop existing). It needs no index write: the family card simply stops
being derived.

IDEMPOTENT: a key already in the index is left alone; a different value is refused unless --replace.
Kana keys that the table does not carry are orphans (reported; --replace deletes them).
Usage: apply_kana_cards.py [--check] [--replace]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
_SCRIPTS = next(p for p in Path(__file__).resolve().parents if p.name == "scripts")
sys.path.append(str(_SCRIPTS))
sys.path.append(str(_SCRIPTS / "ingest"))
from dbtarget import db_target  # noqa: E402
import enums  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
TABLE = ROOT / "research" / "derived" / "repairs" / "kana_cards.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--replace", action="store_true", help="overwrite a key that differs, drop orphans")
    args = ap.parse_args()

    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT name FROM sqlite_master WHERE name='card_production_key'").fetchone():
        raise SystemExit("card_production_key is absent — run scripts/ingest/init_db.py (migration 016) first")
    if not con.execute("SELECT COUNT(*) FROM lesson").fetchone()[0]:
        print("apply_kana_cards: partial index (no lessons) — out of scope, nothing to do")
        return 0

    lid_by_slug = {s: i for i, s in con.execute("SELECT id,slug FROM lesson")}
    # (lesson_id, glyph id) -> card kinds, exactly as export_course._srs_cards derives them
    issued: dict[tuple[int, str], list[str]] = {}
    for lid, fam, script in con.execute(
            "SELECT u.lesson_id, u.ref, f.script FROM lesson_unlocks u JOIN kana_family f ON f.id=u.ref "
            "WHERE u.unlock_type='kana-family'").fetchall():
        kinds = enums.DECK_REGISTRY[f"deck:kana-{script}"]["card_types"]
        for gid, has_strokes in con.execute(
                "SELECT k.id, s.char IS NOT NULL FROM kana k LEFT JOIN kana_stroke s ON s.char=k.char "
                "WHERE k.family_id=? ORDER BY k.ord", (fam,)):
            issued[(lid, gid)] = [k for k in kinds if k != "handwriting" or has_strokes]

    problems: list[str] = []
    written = rewritten = 0
    want_keys: set[tuple[int, str]] = set()
    for r in doc["rows"]:
        lid = lid_by_slug.get(r["lesson"])
        kinds = issued.get((lid, r["item"])) if lid is not None else None
        if kinds is None:
            problems.append(f"{r['lesson']} / {r['item']}: the lesson unlocks no family holding this glyph")
            continue
        if kinds != r["card_types"]:
            problems.append(f"{r['lesson']} / {r['item']}: the export derives {kinds}, the table says "
                            f"{r['card_types']}")
            continue
        want_keys.add((lid, r["item"]))
        k = r["production_key"]
        want = (k["prompt"]["pt-BR"], json.dumps(k["accept"], ensure_ascii=False), None,
                k["verified"], k["verified_by"], k["template"])
        have = con.execute(
            "SELECT prompt_pt, accept_json, sense_index, verified, verified_by, why "
            "FROM card_production_key WHERE lesson_id=? AND item=?", (lid, r["item"])).fetchone()
        if have is not None and tuple(have) == want:
            continue
        if have is not None and not args.replace:
            problems.append(f"{r['lesson']} / {r['item']}: index carries {have[0]!r}, table says "
                            f"{want[0]!r}; pass --replace")
            continue
        written += have is None
        rewritten += have is not None
        if not args.check:
            con.execute(
                "INSERT INTO card_production_key "
                "(lesson_id,item,prompt_pt,accept_json,sense_index,verified,verified_by,why) "
                "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(lesson_id,item) DO UPDATE SET "
                "prompt_pt=excluded.prompt_pt, accept_json=excluded.accept_json, "
                "sense_index=excluded.sense_index, verified=excluded.verified, "
                "verified_by=excluded.verified_by, why=excluded.why",
                (lid, r["item"], *want))

    missing = sorted(set(issued) - want_keys)
    for lid, gid in missing[:5]:
        problems.append(f"lesson id {lid} / {gid}: the export issues this glyph card but the table has no row")
    orphans = sorted({(lid, it) for lid, it in con.execute(
        "SELECT lesson_id, item FROM card_production_key WHERE item LIKE 'kana:%'")} - want_keys)
    for lid, item in orphans:
        if args.replace and not args.check:
            con.execute("DELETE FROM card_production_key WHERE lesson_id=? AND item=?", (lid, item))
        elif not args.replace:
            problems.append(f"lesson id {lid} / {item}: the index carries a kana key the table does not")

    if not args.check and not problems:
        con.commit()
    con.close()
    verb = "would write" if args.check else "wrote"
    print(f"table: {doc['counts']['glyph_cards_after']} glyph cards, "
          f"{doc['counts']['production_keys']} keys, {len(doc['migration'])} family cards retired")
    print(f"{verb} {written} new key(s), {rewritten} rewrite(s) over {len(doc['rows'])} row(s); "
          f"{len(issued)} glyph card(s) issued; {len(orphans)} orphan(s)")
    for p in problems[:15]:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS COMMITTED.")
        return 2
    return 1 if (args.check and (written or rewritten)) else 0


if __name__ == "__main__":
    sys.exit(main())
