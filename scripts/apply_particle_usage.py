#!/usr/bin/env python3
"""W46 — apply the verified particle usage ids and the token role enums; render every explanation.

WHAT THIS WRITES (db/corpus.sqlite; the exporters republish corpus/)
  1. particle.usage / usage_status / usage_slots for the 24,741 rows of
     research/derived/repairs/particle_usage.json (built by scripts/assemble_particle_usage.py from
     the derived rows, the ruled rows and the verifier's verdicts). The 30 `held` rows get
     usage_status 'held' and keep their authored explanation.
  2. localized_text (particle, explanation, pt-BR|en) := the text rendered from the usage's template
     (scripts/particle_usage_render.py), and (particle, note, <locale>) := the explanation it replaces,
     verbatim, with its original layer. Nothing is lost: the legacy text is the note.
  3. token.function / aux_function / chunk_role from research/derived/repairs/token_roles.json.

GUARDS (refuse, write nothing): the C token at the row's position must carry the row's particle
surface; before the move, sha256[:16] of the current explanation must equal the row's `legacy` per
locale (absent == null); after it, the note must. Re-running re-renders and finds everything applied.

Layer: the authored explanations came from the dissection sources (Layer-B batches, Layer-C prose);
those sources are unchanged, so a replay ingests the legacy text and this step moves it again. It runs
AFTER every sentence and particle writer (manifest: after the last lesson-sentence step, families last).
Usage: apply_particle_usage.py [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402
from particle_usage_render import LOCALES, TEMPLATE_SLOTS, load_enum, render  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
USAGE = ROOT / "research" / "derived" / "repairs" / "particle_usage.json"
ROLES = ROOT / "research" / "derived" / "repairs" / "token_roles.json"


def sha(text: str | None) -> str | None:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text is not None else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    doc = json.loads(USAGE.read_text(encoding="utf-8"))
    roles = json.loads(ROLES.read_text(encoding="utf-8"))
    if doc["row_count"] != len(doc["rows"]) or doc["held_count"] != len(doc["held"]):
        raise SystemExit(f"{USAGE.name}: row_count/held_count disagree with the rows")
    enum = load_enum(ROOT)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT 1 FROM sentence LIMIT 1").fetchone():
        print(f"apply_particle_usage: {len(doc['rows'])} rows out of scope (empty sentence table)")
        return 0
    sid_of = dict(con.execute("SELECT slug, id FROM sentence"))
    errors: list[str] = []
    n = {"usage": 0, "moved": 0, "rerendered": 0, "held": 0, "tokens": 0}

    def particle_at(slug: str, pos: int, surface: str) -> int | None:
        sid = sid_of.get(slug)
        got = sid and con.execute(
            "SELECT p.id, p.particle, t.surface FROM particle p JOIN token t ON t.id = p.token_id "
            "WHERE p.sentence_id = ? AND t.split_mode = 'C' AND t.position = ?", (sid, pos)).fetchall()
        if not got or len(got) != 1 or got[0][1] != surface or got[0][2] != surface:
            errors.append(f"{slug}@{pos} {surface}: particle row not found ({got!r})")
            return None
        return got[0][0]

    def text(pid: int, field: str, loc: str) -> tuple[str, str] | None:
        return con.execute("SELECT value, layer FROM localized_text WHERE entity_type = 'particle' "
                           "AND entity_id = ? AND field = ? AND locale = ?", (pid, field, loc)).fetchone()

    def put(pid: int, field: str, loc: str, value: str, layer: str | None) -> None:
        con.execute("INSERT INTO localized_text(entity_type, entity_id, field, locale, value, is_list, layer) "
                    "VALUES ('particle', ?, ?, ?, ?, 0, ?) ON CONFLICT(entity_type, entity_id, field, locale) "
                    "DO UPDATE SET value = excluded.value, layer = excluded.layer", (pid, field, loc, value, layer))

    for r in doc["rows"]:
        addr = f"{r['slug']}@{r['position']} {r['particle']} {r['usage']}"
        pid = particle_at(r["slug"], r["position"], r["particle"])
        if pid is None:
            continue
        slots = {k: r[k] for k in TEMPLATE_SLOTS if k in r}
        stored = {**({"positions": r["positions"]} if "positions" in r else {}), **slots}
        rendered = render(enum, r["usage"], r["particle"], slots)
        cur = {loc: text(pid, "explanation", loc) for loc in LOCALES}
        note = {loc: text(pid, "note", loc) for loc in LOCALES}
        if any(note.values()):
            if any(sha(note[loc][0] if note[loc] else None) != r["legacy"][loc] for loc in LOCALES):
                errors.append(f"{addr}: note does not hold the legacy explanation")
                continue
            if any((cur[loc] or (None,))[0] != rendered[loc] for loc in LOCALES):
                n["rerendered"] += 1
        elif all(r["legacy"][loc] is None for loc in LOCALES):
            # nothing was authored, so nothing moves: absent before, the rendered text after
            if any(cur[loc] and cur[loc][0] != rendered[loc] for loc in LOCALES):
                errors.append(f"{addr}: the table records no explanation, the index has one")
                continue
        else:
            if any(sha(cur[loc][0] if cur[loc] else None) != r["legacy"][loc] for loc in LOCALES):
                errors.append(f"{addr}: explanation is not the legacy text the table was built on")
                continue
            for loc in LOCALES:
                if cur[loc]:
                    put(pid, "note", loc, cur[loc][0], cur[loc][1])
            n["moved"] += 1
        for loc in LOCALES:
            put(pid, "explanation", loc, rendered[loc], "B")
        con.execute("UPDATE particle SET usage = ?, usage_status = ?, usage_slots = ? WHERE id = ?",
                    (r["usage"], r["usage_status"], json.dumps(stored, ensure_ascii=False, sort_keys=True), pid))
        n["usage"] += 1

    for h in doc["held"]:
        pid = particle_at(h["slug"], h["position"], h["particle"])
        if pid is not None:
            con.execute("UPDATE particle SET usage = NULL, usage_status = 'held', usage_slots = NULL WHERE id = ?",
                        (pid,))
            n["held"] += 1

    for row in roles["rows"]:
        slug = row["slug"]
        sid = sid_of.get(slug)
        for pos, surface, fn, ax, cr in row["tokens"]:
            got = sid and con.execute("SELECT id, surface FROM token WHERE sentence_id = ? AND split_mode = 'C' "
                                      "AND position = ?", (sid, pos)).fetchone()
            if not got or got[1] != surface:
                errors.append(f"{slug}@{pos} {surface}: no C token with that surface ({got!r})")
                continue
            con.execute("UPDATE token SET function = ?, aux_function = ?, chunk_role = ? WHERE id = ?",
                        (fn, ax, cr, got[0]))
            n["tokens"] += 1

    if errors:
        con.rollback()
        for e in errors[:30]:
            print(f"  REFUSE {e}")
        print(f"apply_particle_usage: {len(errors)} guard failure(s); nothing written")
        return 1
    if args.check:
        con.rollback()
    else:
        con.commit()
    print(f"apply_particle_usage ({'check' if args.check else 'applied'}): {n['usage']} usages "
          f"({n['moved']} explanations moved to note, {n['rerendered']} re-rendered), {n['held']} held, "
          f"{n['tokens']} token role rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
