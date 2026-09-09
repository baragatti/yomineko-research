#!/usr/bin/env python3
"""Rewrite lesson authoring refs to the record's PUBLISHED address, in both layers.

WHY
---
`contracts/manifest.json` states the rule in its own `id_convention` and
`scripts/validate/validate_stable_addresses.py` restates it: "Some registries also carry an integer
`id`; that is a storage row number, it is NOT stable across a rebuild, and it must never be used as
an API key." The committed export obeyed it — `scripts/export/export_course.py` `_deref` rewrites
`vocab:1421` (a row number) and `vocab:人` (a headword up to three records answer to) to the
published `vocab:<jmdict_id>` on the way out, and two gates check the result. The AUTHORING layer
did not: `research/derived/lessons/*.json` still carried 31 row-number refs across 19 lessons, so
the identity of those chips lived only inside `db/corpus.sqlite` — the one artefact CLAUDE.md
declares regenerable and non-authoritative. Renumber the table and the lesson silently teaches a
different word.

WHAT IT WRITES
--------------
`research/derived/repairs/lesson_ref_addresses.json`, two kinds of row:

  row_id              31 rows. `vocab:<row number>` -> that row's `vocab.slug`. Mechanical: the
                      mapping is re-derived from the registry on every run and the script refuses to
                      write if the row now names a different record than the table says, so a stale
                      table cannot re-point a chip behind your back.
  ambiguous_headword  2 rows, and they are NOT a general headword sweep — 322 lessons still address
                      by headword and `vocab_identity.py` settles them on evidence. These two
                      (`vocab:側` in les:n5-perguntas-01 and in les:n5-particulas-lugar-02) are the
                      pair the resolver can only settle from `vocab.introducing_topic_id`, a stored
                      placement column `scripts/ingest/place_items.py` recomputes differently on a
                      from-scratch replay: it bin-packs by `freq_rank` and both 側 records carry
                      1521, so a replay puts both in one topic, both unlocks resolve to one record,
                      and `familylib.unlock_topic_map()` aborts the whole rebuild on a ledger that
                      contradicts itself. Writing the address the lesson means deletes the guess.

BOTH LAYERS, and the export must not move
-----------------------------------------
The authoring source (what a manifest replay reads) and `db/corpus.sqlite` (`lesson_unlocks.ref` and
the lesson body in `localized_text`). The exported `course/` tree is expected to be BYTE-IDENTICAL
afterwards, because `_deref` returns a published slug unchanged — that is the acceptance test, not a
hope. Two code paths had to learn the slug form for it to hold:

  * `scripts/ingest/load_lessons.py` `_member_id()` / `backfill_introducing_topic()` resolved a
    numeric ident as a ROW ID, so `vocab:1189370` would have looked for row 1,189,370 and found
    nothing — the unlock would have loaded with a warning and no `lesson_introduces` row.
  * `scripts/export/vocab_identity.py`'s sibling filter built its `_claimed` set from NUMERIC unlock
    refs only. Converting the refs would have emptied it and silently changed how every remaining
    headword ref in those lessons resolves.

Idempotent: a second run finds every `old` gone and every `new` in place and reports 0 changes.
Run `scripts/export/export_course.py` afterwards.

Usage: apply_lesson_ref_addresses.py [--check]
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
from dbtarget import db_target, out_root  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = out_root(ROOT)
SRC = OUT / "research" / "derived" / "lessons"
TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_ref_addresses.json"


def literal_forms(ref: str) -> list[str]:
    """The two shapes a lesson ref takes in the raw authoring JSON, and the only two.

    A structured field is `"ref": "vocab:449"` — the ref sits between real quotes. A body chip is
    `<vocab ref=\\"vocab:449\\"/>` INSIDE a JSON string, so its quotes are backslash-escaped in the
    file. Replacing these two literals rather than regex-matching the bare id is what keeps
    `vocab:449` from also rewriting `vocab:4490`, and rewriting the raw text rather than
    re-serialising the parsed JSON is what keeps the other 76 lesson files' formatting out of the
    diff (they do not round-trip through `json.dumps(indent=2)`).
    """
    return ['\\"' + ref + '\\"', '"' + ref + '"']


def rewrite(text: str, old: str, new: str) -> tuple[str, int]:
    n = 0
    for a, b in zip(literal_forms(old), literal_forms(new)):
        n += text.count(a)
        text = text.replace(a, b)
    return text, n


def count(text: str, ref: str) -> int:
    return sum(text.count(f) for f in literal_forms(ref))


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc


def verify_identity(con, rows: list[dict], problems: list[str]) -> int:
    """`new` must name the record the table says, and for a row-id row it must be the SAME record
    the row number names TODAY. A table asserting an identity the registry no longer agrees with is
    the one way this script could quietly teach a different word."""
    checked = 0
    for r in rows:
        checked += 1
        got = con.execute("SELECT headword, kana FROM vocab WHERE slug=?", (r["new"],)).fetchone()
        if not got:
            problems.append(f"{r['lesson']}: {r['new']} is not a record in the vocab registry")
            continue
        if (got[0], got[1]) != (r["headword"], r["kana"]):
            problems.append(f"{r['lesson']}: {r['new']} is {got[0]}/{got[1]}, the table says "
                            f"{r['headword']}/{r['kana']}")
            continue
        if r["kind"] == "row_id":
            rid = r["old"].split(":", 1)[1]
            by_row = con.execute("SELECT slug FROM vocab WHERE id=?", (int(rid),)).fetchone()
            if not by_row or by_row[0] != r["new"]:
                problems.append(f"{r['lesson']}: row {rid} is {by_row and by_row[0]}, not {r['new']} "
                                f"— the index was renumbered and this table is stale")
        elif r["kind"] == "ambiguous_headword":
            hw = r["old"].split(":", 1)[1]
            cands = [c[0] for c in con.execute("SELECT slug FROM vocab WHERE headword=?", (hw,))]
            if r["new"] not in cands:
                problems.append(f"{r['lesson']}: {r['new']} is not one of the records spelled "
                                f"{hw} ({cands})")
    # The two ambiguous rows must PARTITION their headword's candidates, or the pair is still a guess.
    amb = [r for r in rows if r["kind"] == "ambiguous_headword"]
    for hw in {r["old"] for r in amb}:
        group = [r for r in amb if r["old"] == hw]
        chosen = {r["new"] for r in group}
        if len(chosen) != len(group):
            problems.append(f"{hw}: {len(group)} lessons but {len(chosen)} distinct records — the "
                            f"rows do not partition the siblings")
    return checked


def apply_sources(rows: list[dict], check: bool, problems: list[str]) -> int:
    changed = 0
    for r in rows:
        f = SRC / r["file"]
        if not f.exists():
            problems.append(f"{r['lesson']}: authoring source {r['file']} missing")
            continue
        raw = f.read_text(encoding="utf-8")
        if count(raw, r["old"]) == 0:
            if count(raw, r["new"]) < r["occurrences"]:
                problems.append(f"{r['lesson']}: neither {r['old']} nor {r['occurrences']} "
                                f"occurrence(s) of {r['new']} are in {r['file']}")
            continue                                    # already applied
        new_raw, n = rewrite(raw, r["old"], r["new"])
        if n != r["occurrences"]:
            problems.append(f"{r['lesson']}: {r['file']} carries {n} occurrence(s) of {r['old']}, "
                            f"the table says {r['occurrences']}")
            continue
        print(f"  {r['file']}: {r['old']} -> {r['new']} x{n} (source)")
        changed += n
        if not check:
            f.write_text(new_raw, encoding="utf-8")
    return changed


def apply_db(con, rows: list[dict], check: bool, problems: list[str]) -> int:
    changed = 0
    for r in rows:
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (r["lesson"],)).fetchone()
        if not lr:
            problems.append(f"{r['lesson']}: no such lesson in the index")
            continue
        lid = lr[0]
        n = con.execute("SELECT COUNT(*) FROM lesson_unlocks WHERE lesson_id=? AND "
                        "unlock_type='vocab' AND ref=?", (lid, r["old"])).fetchone()[0]
        if n:
            print(f"  {r['lesson']}: unlock {r['old']} -> {r['new']} (db)")
            changed += 1
            if not check:
                con.execute("UPDATE lesson_unlocks SET ref=? WHERE lesson_id=? AND "
                            "unlock_type='vocab' AND ref=?", (r["new"], lid, r["old"]))
        row = con.execute("SELECT value FROM localized_text WHERE entity_type='lesson' AND "
                          "entity_id=? AND field='body' AND locale='pt-BR'", (lid,)).fetchone()
        if not row:
            problems.append(f"{r['lesson']}: no pt-BR body in the index")
            continue
        # In the DB the body is the decoded string, so a chip's quotes are real quotes.
        body = row[0]
        old_attr, new_attr = f'"{r["old"]}"', f'"{r["new"]}"'
        if old_attr in body:
            k = body.count(old_attr)
            print(f"  {r['lesson']}: body chip {r['old']} -> {r['new']} x{k} (db)")
            changed += k
            if not check:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND "
                            "entity_id=? AND field='body' AND locale='pt-BR'",
                            (body.replace(old_attr, new_attr), lid))
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    table = load_table()
    rows = table["rows"]
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    problems: list[str] = []

    n = verify_identity(con, rows, problems)
    changed = apply_sources(rows, args.check, problems)
    changed += apply_db(con, rows, args.check, problems)

    if not args.check and not problems:
        con.commit()
    con.close()

    verb = "would change" if args.check else "changed"
    print(f"\nverified {n} address(es) against the vocab registry; {verb} {changed} ref(s)")
    for p in problems:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS COMMITTED — an address that does not re-derive is not written.")
        return 2
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
