#!/usr/bin/env python3
"""W21b: move each forward-referenced item's unlock to the first same-level lesson that uses it.

WHAT WAS WRONG
--------------
656 (lesson, item) pairs showed the learner an item the course taught LATER (35 inside one topic,
461 inside one level, 160 across levels). `validate_lesson_gating.py` check C keeps such edges out of
`needs[]`, so nothing counted them. `scripts/derive_forward_refs.py` decides each one and writes
`research/derived/repairs/w21b_forward_refs.json`; its `rows` are the MOVES this script applies.

WHAT A MOVE WRITES (item I, from its teaching lesson M to the first same-level user T)
-------------------------------------------------------------------------------------
  unlock      `lesson_unlocks` (M, kind, db_ref) -> (T, kind, ref_at_new_home), and the same entry
              in the authoring sources `research/derived/lessons/<slug>.json`. The ref string is the
              one M stored unless its headword is AMBIGUOUS: then T gets the published slug, because
              a headword ref is re-resolved at T and the resolver's introducing_topic tier reads a
              placement a rebuild does not reproduce. T's body has no chip for the item (gating
              check B), so the sibling filter the slug feeds cannot re-point one of T's chips.
  card        nothing to write: `export_course._srs_cards` derives the card from the unlock. The
              authored production key IS written: `card_production_key` (M, I) -> T, and the row of
              the tracked table `card_production_keys.json` is re-homed, since that table is
              lesson-addressed and a rebuild replays it against sources that already carry the move.
  introduces  `lesson_introduces` (M, member) -> T (the back-compat mirror load_lessons writes from
              the unlocks), and `introducing_topic_id` of the record -> T's topic where it named M's.
  exercise    an exercise of M whose only M-target is I travels when the derivation allowed it
              (`exercises_moved`): `exercise.lesson_id` and its `<exercise ref>` node move in both
              layers, and a W20 row (`practice_kanji_exercises.json`) naming it is re-homed. Every
              other exercise stays in M as review (owner ruling 2026-09-23).
Exemption files shrink by the table's own simulation: `course/gating_exemptions.json` loses the
entries the moves resolve, `course/needs_root_exemptions.json` the lessons that gain prerequisites.
`lesson.cumulative_known_set` is recomputed with the ingest's own routine.

IDEMPOTENT: an item already at T, an exercise already in T, a node already moved, a table row already
re-homed are all recognised and left alone; a second run reports 0 changes.

TWO MANIFEST STEPS. On a rebuild replay the authoring sources already carry every move, so the only
thing left to write is `introducing_topic_id`, and it must land BEFORE the first vocab resolver of
the chain runs: the resolver's introducing_topic tier reads it (å¹´ at les:n5-numeros-tempo-02 went to
its sibling and the card-key step dropped its key when it ran late). `--placement-only` is that early
step (112); the full run (130) comes after the practice and card-key applies whose rows it moves.
Run `scripts/build_needs_table.py`, `scripts/apply_lesson_needs.py --replace` and
`scripts/export/export_course.py` afterwards.
Usage: apply_forward_refs.py [--check] [--placement-only]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target, out_root  # noqa: E402
from apply_practice_exercises import insert_node, node_separator  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
OUT = out_root(ROOT)
SRC = OUT / "research" / "derived" / "lessons"
REPAIRS = ROOT / "research" / "derived" / "repairs"
TABLE = REPAIRS / "w21b_forward_refs.json"
CARD_TABLE = REPAIRS / "card_production_keys.json"
W20_TABLE = REPAIRS / "practice_kanji_exercises.json"
GATING_EXEMPT = OUT / "course" / "gating_exemptions.json"
ROOT_EXEMPT = OUT / "course" / "needs_root_exemptions.json"
LOC = "pt-BR"
MEMBER = {"vocab": ("vocab", "slug"), "kanji": ("kanji", "character"), "grammar": ("grammar_point", "key")}


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc


def remove_node(body: str, node: str) -> str:
    """`body` without `node` and the one separator that joined it to its neighbour."""
    sep = node_separator(body)
    i = body.find(node)
    if i < 0:
        return body
    j = i + len(node)
    if sep and body[i - len(sep):i] == sep:
        i -= len(sep)
    elif sep and body[j:j + len(sep)] == sep:
        j += len(sep)
    return body[:i] + body[j:]


def move_node(bm: str, bt: str, node: str) -> tuple[str, str, bool] | None:
    """(new M body, new T body, changed) or None when T's body has nowhere to put the node."""
    changed = False
    if node in bm:
        bm = remove_node(bm, node)
        changed = True
    if node not in bt:
        placed = insert_node(bt, node)
        if placed is None:
            return None
        bt = placed[0]
        changed = True
    return bm, bt, changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--placement-only", action="store_true",
                    help="write only introducing_topic_id (the early rebuild step, before any resolver runs)")
    args = ap.parse_args()
    doc = load_table()
    rows = doc["rows"]

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    problems: list[str] = []
    n = {"unlock": 0, "introduces": 0, "topic": 0, "card_key": 0, "exercise": 0, "node": 0, "source": 0,
         "table_rows": 0, "exemptions": 0}
    les = {s: (i, t) for i, s, t in con.execute("SELECT id, slug, topic_id FROM lesson")}
    tid = {s: i for s, i in con.execute("SELECT slug, id FROM topic")}

    def body_of(lid: int) -> str:
        r = con.execute("SELECT value FROM localized_text WHERE entity_type='lesson' AND entity_id=? "
                        "AND field='body' AND locale=?", (lid, LOC)).fetchone()
        return r[0] if r else ""

    def set_body(lid: int, text: str) -> None:
        if not args.check:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND entity_id=? "
                        "AND field='body' AND locale=?", (text, lid, LOC))

    def w(sql: str, params: tuple) -> None:
        if not args.check:
            con.execute(sql, params)

    for r in rows:
        I, kind, M, T, ref = r["item"], r["kind"], r["from"], r["to"], r["db_ref"]
        if M not in les or T not in les:
            problems.append(f"{I}: {M} or {T} is not a lesson in the index")
            continue
        (mid, mtop), (tlid, ttop) = les[M], les[T]
        if tid.get(r["topic_from"]) != mtop or tid.get(r["topic_to"]) != ttop:
            problems.append(f"{I}: the table's topics ({r['topic_from']} -> {r['topic_to']}) are not the index's")
            continue

        # ---- placement (db): FIRST, because the vocab resolver reads it -----------------------
        tbl, col = MEMBER[kind]
        key = I if kind == "vocab" else I.split(":", 1)[1]
        rec = con.execute(f"SELECT id, introducing_topic_id FROM {tbl} WHERE {col}=?", (key,)).fetchone()
        if rec is None:
            problems.append(f"{I}: no {tbl} record {key!r}")
            continue
        if rec[1] == mtop and mtop != ttop:
            n["topic"] += 1
            w(f"UPDATE {tbl} SET introducing_topic_id=? WHERE id=?", (ttop, rec[0]))
        if args.placement_only:
            continue

        # ---- unlock (db) ------------------------------------------------------------------
        # `ref_at_new_home` is the published slug for an ambiguous headword (see the derivation),
        # otherwise the ref string M stored.
        ref_to = r.get("ref_at_new_home") or ref
        q = "SELECT 1 FROM lesson_unlocks WHERE lesson_id=? AND unlock_type=? AND ref=?"
        at_m = con.execute(q, (mid, kind, ref)).fetchone()
        at_t = con.execute(q, (tlid, kind, ref_to)).fetchone()
        if at_m:
            # present at both = a rebuild step re-wrote M's unlock from an older input: the table's
            # decision is that the item lives at T, so M's copy is the one that goes
            n["unlock"] += 1
            w("DELETE FROM lesson_unlocks WHERE lesson_id=? AND unlock_type=? AND ref=?", (mid, kind, ref))
            if not at_t:
                w("INSERT INTO lesson_unlocks (lesson_id, unlock_type, ref) VALUES (?,?,?)", (tlid, kind, ref_to))
        elif not at_t:
            problems.append(f"{I}: {ref} is unlocked by neither {M} nor {T} ({ref_to}) - the table is stale")
            continue

        # ---- introduces (db) ----------------------------------------------------------------
        if con.execute("SELECT 1 FROM lesson_introduces WHERE lesson_id=? AND member_type=? AND member_id=?",
                       (mid, kind, rec[0])).fetchone():
            n["introduces"] += 1
            w("DELETE FROM lesson_introduces WHERE lesson_id=? AND member_type=? AND member_id=?",
              (mid, kind, rec[0]))
            w("INSERT OR IGNORE INTO lesson_introduces (lesson_id, member_type, member_id) VALUES (?,?,?)",
              (tlid, kind, rec[0]))

        # ---- authored production key (db) --------------------------------------------------
        if con.execute("SELECT 1 FROM card_production_key WHERE lesson_id=? AND item=?", (mid, I)).fetchone():
            n["card_key"] += 1
            w("UPDATE card_production_key SET lesson_id=? WHERE lesson_id=? AND item=?", (tlid, mid, I))

        # ---- exercises (db) -------------------------------------------------------------------
        bm, bt = body_of(mid), body_of(tlid)
        for eid in r["exercises_moved"]:
            e = con.execute("SELECT id, lesson_id FROM exercise WHERE slug=?", (eid,)).fetchone()
            if e is None:
                problems.append(f"{I}: exercise {eid} is not in the index")
                continue
            if e[1] == mid:
                n["exercise"] += 1
                nxt = con.execute("SELECT COALESCE(MAX(ord), -1) + 1 FROM exercise WHERE lesson_id=?",
                                  (tlid,)).fetchone()[0]
                w("UPDATE exercise SET lesson_id=?, ord=? WHERE id=?", (tlid, nxt, e[0]))
            elif e[1] != tlid:
                problems.append(f"{I}: exercise {eid} belongs to neither {M} nor {T}")
                continue
            moved = move_node(bm, bt, f'<exercise ref="{eid}"/>')
            if moved is None:
                problems.append(f"{T}: body has no practice block or <checklist> to receive {eid}")
                continue
            bm, bt, ch = moved
            n["node"] += ch
        if bm != body_of(mid):
            set_body(mid, bm)
        if bt != body_of(tlid):
            set_body(tlid, bt)

        # ---- authoring sources ------------------------------------------------------------
        fm, ft = SRC / f"{M.split(':', 1)[1]}.json", SRC / f"{T.split(':', 1)[1]}.json"
        if not (fm.exists() and ft.exists()):
            problems.append(f"{I}: authoring source {fm.name} or {ft.name} missing")
            continue
        sm, st = (json.loads(f.read_text(encoding="utf-8")) for f in (fm, ft))
        dirty = False
        ent, ent_to = {"type": kind, "ref": ref}, {"type": kind, "ref": ref_to}
        if ent in (sm.get("unlocks") or []):
            sm["unlocks"].remove(ent)
            dirty = True
        if ent_to not in (st.get("unlocks") or []):
            st.setdefault("unlocks", []).append(ent_to)
            dirty = True
        for eid in r["exercises_moved"]:
            ex = next((x for x in sm.get("exercises") or [] if x.get("slug") == eid), None)
            if ex is not None:
                sm["exercises"].remove(ex)
                dirty = True
                if not any(x.get("slug") == eid for x in st.get("exercises") or []):
                    st.setdefault("exercises", []).append(ex)
            elif not any(x.get("slug") == eid for x in st.get("exercises") or []):
                problems.append(f"{I}: exercise {eid} is in neither authoring source")
                continue
            moved = move_node(sm.get("body") or "", st.get("body") or "", f'<exercise ref="{eid}"/>')
            if moved is None:
                problems.append(f"{T}: source body has nowhere to receive {eid}")
                continue
            sm["body"], st["body"], ch = moved
            dirty = dirty or ch
        if dirty:
            n["source"] += 1
            if not args.check:
                for f, d in ((fm, sm), (ft, st)):
                    f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.placement_only:
        if not args.check and not problems:
            con.commit()
        con.close()
        print(f"apply_forward_refs --placement-only: {len(rows)} moves; re-placed {n['topic']} record(s)")
        for p in problems[:30]:
            print(f"  ! {p}")
        return 2 if problems else 0

    # ---- lesson-addressed tables a rebuild replays against the moved sources --------------
    moved_item = {(r["from"], r["item"]): r["to"] for r in rows}
    moved_ex = {(r["from"], e): r["to"] for r in rows for e in r["exercises_moved"]}
    for path, key in ((CARD_TABLE, lambda x: (x["lesson"], x["item"])),
                      (W20_TABLE, lambda x: (x["lesson"], x["exercise"]["id"]))):
        tdoc = json.loads(path.read_text(encoding="utf-8"))
        hit = 0
        for x in tdoc["rows"]:
            to = (moved_item if path == CARD_TABLE else moved_ex).get(key(x))
            if to:
                x["lesson"] = to
                hit += 1
        if path == W20_TABLE:
            remapped = {(m["lesson"], m["from"]) for m in tdoc.get("apply_id_remap") or []}
            clash = sorted(k for k in moved_ex if k in remapped)
            if clash:
                problems.append(f"{path.name}: moved exercise(s) {clash} carry an apply_id_remap entry")
        if hit:
            n["table_rows"] += hit
            if not args.check:
                # each table round-trips byte for byte at its own indent (measured: 1 and 2)
                path.write_text(json.dumps(tdoc, ensure_ascii=False, indent=1 if path == CARD_TABLE
                                           else 2) + "\n", encoding="utf-8")

    # ---- exemption files shrink by the table's simulation ---------------------------------
    sim = doc["simulation"]
    drop_g = set(sim.get("gating_exemptions_dropped") or [])
    if GATING_EXEMPT.is_file() and drop_g:
        g = json.loads(GATING_EXEMPT.read_text(encoding="utf-8"))
        keep = [e for e in g["item_refs"] if f"{e['lesson']} / {e['ref']}" not in drop_g]
        if len(keep) != len(g["item_refs"]):
            n["exemptions"] += len(g["item_refs"]) - len(keep)
            g["item_refs"] = keep
            if not args.check:
                GATING_EXEMPT.write_text(json.dumps(g, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    drop_r = set(sim.get("root_exemptions_dropped") or [])
    if ROOT_EXEMPT.is_file() and drop_r:
        rx = json.loads(ROOT_EXEMPT.read_text(encoding="utf-8"))
        keep = [e for e in rx["lessons"] if e["lesson"] not in drop_r]
        if len(keep) != len(rx["lessons"]):
            n["exemptions"] += len(rx["lessons"]) - len(keep)
            rx["lessons"], rx["count"] = keep, len(keep)
            if not args.check:
                ROOT_EXEMPT.write_text(json.dumps(rx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not args.check and not problems:
        sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
        from load_lessons import recompute_cumulative  # noqa: PLC0415
        print(f"  recomputed cumulative_known_set for {recompute_cumulative(con)} lessons (db)")
        con.commit()
    con.close()

    verb = "would write" if args.check else "wrote"
    print(f"apply_forward_refs: {len(rows)} moves; {verb} " + ", ".join(f"{k} {v}" for k, v in n.items()))
    for p in problems[:30]:
        print(f"  ! {p}")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S) - NOTHING WAS COMMITTED to the index")
        return 2
    return 1 if (args.check and any(n.values())) else 0


if __name__ == "__main__":
    sys.exit(main())
