#!/usr/bin/env python3
"""P5-n3-review (APP_PLAN W22 §3): the three N3 review lessons, in both layers.

WHAT
----
`research/derived/repairs/n3_review_lessons.json` (folded by `scripts/assemble_n3_review_lessons.py`
from the authored lessons and their independent verdict: verified rows only) holds one row per
lesson of top:n3-revisao — les:n3-revisao-01 rewritten, -02 and -03 new — plus the topic objective.
That puts N3's review topic in the shape of top:n5-revisao / top:n4-revisao: 3 lessons, one block
each, recap prose, 6 exercises typed rec/rec/cloze/cloze/sentence_build/production, and
feat:jlpt-sim-n3 on the LAST lesson (-03), which is why -01 no longer lists it.

WHAT THIS SCRIPT OWNS, AND WHAT IT DOES NOT
-------------------------------------------
Owned (re-asserted from the table on every run): order, title, description, objectives, body,
unlocks + feature_unlocks, the lesson-level `sentence_refs`, `reading_refs`, and the exercise list
(type, prompt, answer, explanation, sentence_refs; an exercise whose content is new takes the
table's authored item_refs anchor). Exercises of these lessons that the table does not list are
removed.

Not owned, and placed afterwards by their own tables, which is why this step runs BEFORE them in
the rebuild manifest:
  * `needs`                derived: build_needs_table.py -> repairs/lesson_needs.json (step 118
                           writes it; this script leaves an existing lesson's needs alone and a new
                           lesson starts with none)
  * the W20 vocab drills   repairs/practice_vocab_exercises.json (ex:n3-revisao-01-7/-8/-9 and
                           their body nodes), step 134
  * the W14 sentence cards repairs/lesson_sentences.json (the "Mais exemplos" block on -01), 136
  * item_refs              derive_item_refs.py -> repairs/item_refs.json, step 142

BOTH LAYERS
-----------
`research/derived/lessons/<slug>.json` (canonical `json.dumps(indent=2)`, as apply_lesson_needs
writes it) and `db/corpus.sqlite`. An existing lesson is updated IN PLACE (its `lesson.id` is
referenced by card_production_key / card_example / reading, so it is never deleted); a missing one
is inserted with the ingest's own `persist_lesson`. Then `cumulative_known_set` is recomputed with
the ingest's routine. The topic objective is `localized_text(topic, objectives)`.

Idempotent as a chain: this step re-asserts the table (dropping the drills' body nodes and the W14
block from -01), and steps 134 / 136 put them back byte for byte, so the state after the chain is
the same on every run and `--check` straight after the chain reports only those re-additions on -01.
Run the exporter afterwards.
Usage: apply_n3_review_lessons.py [--check]
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

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
SRC = out_root(ROOT) / "research" / "derived" / "lessons"
# The table is a committed INPUT to the rebuild, so it is read from the repo, never from --out-root.
TABLE = ROOT / "research" / "derived" / "repairs" / "n3_review_lessons.json"
LOC = "pt-BR"
KEY_ORDER = ("slug", "topic", "order", "schema_version", "title", "description", "objectives",
             "needs", "unlocks", "feature_unlocks", "sentence_refs", "body", "exercises",
             "reading_refs")
EX_CONTENT = ("type", "prompt", "answer", "explanation", "sentence_refs")

sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
from i18n_text import set_text  # noqa: E402
from load_lessons import (_MEMBER, _member_id, _unlocks_from_rec, persist_lesson,  # noqa: E402
                          recompute_cumulative)
import enums  # noqa: E402


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    return doc


def source_record(row: dict, cur: dict | None) -> dict:
    """The authoring-source object this row makes, keeping what the row does not own."""
    have = {e["slug"]: e for e in (cur or {}).get("exercises") or []}
    exs = []
    for ex in row["exercises"]:
        old = have.get(ex["slug"])
        same = old is not None and all(old.get(k) == ex.get(k) for k in EX_CONTENT)
        e = {k: ex[k] for k in ("slug",) + EX_CONTENT}
        e["item_refs"] = old.get("item_refs", []) if same else list(ex.get("item_refs") or [])
        exs.append(e)
    rec = {k: row[k] for k in KEY_ORDER if k in row and k != "exercises"}
    rec["needs"] = list((cur or {}).get("needs") or [])
    rec["exercises"] = exs
    return {k: rec[k] for k in KEY_ORDER}


def apply_db_existing(con, lid: int, rec: dict, check: bool) -> int:
    n = 0
    topic_id = con.execute("SELECT id FROM topic WHERE slug=?", (rec["topic"],)).fetchone()[0]
    if con.execute("SELECT topic_id, ord FROM lesson WHERE id=?", (lid,)).fetchone() != (
            topic_id, int(rec["order"])):
        n += 1
        if not check:
            con.execute("UPDATE lesson SET topic_id=?, ord=? WHERE id=?", (topic_id, int(rec["order"]), lid))
    for field in ("title", "description", "objectives", "body"):
        want = rec[field]
        v = json.dumps(want, ensure_ascii=False) if isinstance(want, list) else want
        got = con.execute("SELECT value FROM localized_text WHERE entity_type='lesson' AND entity_id=? "
                          "AND field=? AND locale=?", (lid, field, LOC)).fetchone()
        if (got[0] if got else None) != v:
            n += 1
            if not check:
                set_text(con, "lesson", lid, field, want, layer="C")

    # unlocks: exactly the row's (features included); lesson_introduces follows the member ones
    want_u = {(u["type"], u["ref"]) for u in _unlocks_from_rec(rec)}
    have_u = set(con.execute("SELECT unlock_type, ref FROM lesson_unlocks WHERE lesson_id=?", (lid,)))
    for typ, ref in have_u - want_u:
        n += 1
        if not check:
            con.execute("DELETE FROM lesson_unlocks WHERE lesson_id=? AND unlock_type=? AND ref=?",
                        (lid, typ, ref))
            if typ in _MEMBER:
                mid = _member_id(con, typ, enums.parse_ref(ref)[1])
                con.execute("DELETE FROM lesson_introduces WHERE lesson_id=? AND member_type=? "
                            "AND member_id=?", (lid, typ, mid))
    for typ, ref in want_u - have_u:
        n += 1
        if not check:
            con.execute("INSERT INTO lesson_unlocks (lesson_id, unlock_type, ref) VALUES (?,?,?)",
                        (lid, typ, ref))
            if typ in _MEMBER:
                mid = _member_id(con, typ, enums.parse_ref(ref)[1])
                if mid is not None:
                    con.execute("INSERT OR IGNORE INTO lesson_introduces (lesson_id, member_type, "
                                "member_id) VALUES (?,?,?)", (lid, typ, mid))

    # lesson-level sentence cards
    want_s = set(rec["sentence_refs"])
    have_s = {s: sid for s, sid in con.execute(
        "SELECT s.slug, s.id FROM lesson_sentence ls JOIN sentence s ON s.id=ls.sentence_id "
        "WHERE ls.lesson_id=?", (lid,))}
    for s in have_s.keys() - want_s:
        n += 1
        if not check:
            con.execute("DELETE FROM lesson_sentence WHERE lesson_id=? AND sentence_id=?", (lid, have_s[s]))
    for s in want_s - have_s.keys():
        sid = con.execute("SELECT id FROM sentence WHERE slug=?", (s,)).fetchone()
        n += 1
        if not check and sid:
            con.execute("INSERT OR IGNORE INTO lesson_sentence (lesson_id, sentence_id) VALUES (?,?)",
                        (lid, sid[0]))

    # exercises: drop the ones the row does not list, upsert the rest in order
    want_e = {e["slug"]: e for e in rec["exercises"]}
    for eid, slug in con.execute("SELECT id, slug FROM exercise WHERE lesson_id=?", (lid,)).fetchall():
        if slug in want_e:
            continue
        n += 1
        if not check:
            for t in ("exercise_sentence", "exercise_item"):
                con.execute(f"DELETE FROM {t} WHERE exercise_id=?", (eid,))
            con.execute("DELETE FROM localized_text WHERE entity_type='exercise' AND entity_id=?", (eid,))
            con.execute("DELETE FROM exercise_item_ref WHERE exercise=?", (slug,))
            con.execute("DELETE FROM exercise WHERE id=?", (eid,))
    for i, ex in enumerate(rec["exercises"]):
        answer = json.dumps(ex.get("answer"), ensure_ascii=False)
        row = con.execute("SELECT id, lesson_id, ord, type, answer FROM exercise WHERE slug=?",
                          (ex["slug"],)).fetchone()
        if row is not None and row[1] != lid:
            raise SystemExit(f"{ex['slug']} belongs to another lesson in the index")
        if row is None or row[2:] != (i, ex["type"], answer):
            n += 1
            if not check:
                if row is None:
                    con.execute("INSERT INTO exercise (slug, lesson_id, ord, type, answer, needs_review) "
                                "VALUES (?,?,?,?,?,1)", (ex["slug"], lid, i, ex["type"], answer))
                else:
                    con.execute("UPDATE exercise SET ord=?, type=?, answer=?, needs_review=1 WHERE id=?",
                                (i, ex["type"], answer, row[0]))
        if check and row is None:
            continue
        eid = con.execute("SELECT id FROM exercise WHERE slug=?", (ex["slug"],)).fetchone()[0]
        for field in ("prompt", "explanation"):
            got = con.execute("SELECT value FROM localized_text WHERE entity_type='exercise' AND "
                              "entity_id=? AND field=? AND locale=?", (eid, field, LOC)).fetchone()
            if (got[0] if got else None) != ex.get(field):
                n += 1
                if not check:
                    set_text(con, "exercise", eid, field, ex.get(field), layer="C")
        want_es = set(ex.get("sentence_refs") or [])
        have_es = {s: sid for s, sid in con.execute(
            "SELECT s.slug, s.id FROM exercise_sentence es JOIN sentence s ON s.id=es.sentence_id "
            "WHERE es.exercise_id=?", (eid,))}
        for s in have_es.keys() - want_es:
            n += 1
            if not check:
                con.execute("DELETE FROM exercise_sentence WHERE exercise_id=? AND sentence_id=?",
                            (eid, have_es[s]))
        for s in want_es - have_es.keys():
            sid = con.execute("SELECT id FROM sentence WHERE slug=?", (s,)).fetchone()
            if sid is None:
                raise SystemExit(f"{ex['slug']} cites {s}, which is not in the index")
            n += 1
            if not check:
                con.execute("INSERT INTO exercise_sentence (exercise_id, sentence_id) VALUES (?,?)",
                            (eid, sid[0]))
        want_ei = set()
        for it in ex.get("item_refs") or []:
            if it["type"] in _MEMBER:
                mid = _member_id(con, it["type"], enums.parse_ref(it["ref"])[1])
                if mid is not None:
                    want_ei.add((it["type"], mid))
        have_ei = set(con.execute("SELECT member_type, member_id FROM exercise_item WHERE exercise_id=?",
                                  (eid,)))
        if want_ei != have_ei:
            n += 1
            if not check:
                con.execute("DELETE FROM exercise_item WHERE exercise_id=?", (eid,))
                con.executemany("INSERT INTO exercise_item (exercise_id, member_type, member_id) "
                                "VALUES (?,?,?)", [(eid, t, m) for t, m in sorted(want_ei)])
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()
    doc = load_table()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    src_changed = db_changed = 0

    # introduce-once: nothing outside this topic may unlock what these rows unlock
    ours = {r["slug"] for r in doc["rows"]}
    for r in doc["rows"]:
        for u in _unlocks_from_rec(r):
            others = [s for (s,) in con.execute(
                "SELECT l.slug FROM lesson_unlocks u JOIN lesson l ON l.id=u.lesson_id "
                "WHERE u.unlock_type=? AND u.ref=?", (u["type"], u["ref"])) if s not in ours]
            if others:
                raise SystemExit(f"{u['ref']}: already unlocked by {others} (introduce-once); "
                                 f"NOTHING WAS WRITTEN")

    for row in doc["rows"]:
        slug = row["slug"]
        f = SRC / (slug.split(":", 1)[1] + ".json")
        raw = f.read_text(encoding="utf-8").replace("\r\n", "\n") if f.exists() else None
        rec = source_record(row, json.loads(raw) if raw else None)
        text = json.dumps(rec, ensure_ascii=False, indent=2) + "\n"
        if text != raw:
            src_changed += 1
            print(f"  {slug}: authoring source {'rewritten' if raw else 'created'}")
            if not args.check:
                f.write_text(text, encoding="utf-8")

        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (slug,)).fetchone()
        if lr is None:
            db_changed += 1
            print(f"  {slug}: inserted into the index")
            if not args.check:
                warns: list[str] = []
                persist_lesson(con, rec, warns)
                for w in warns:
                    print(f"    warn {w}")
        else:
            n = apply_db_existing(con, lr[0], rec, args.check)
            if n:
                print(f"  {slug}: {n} index change(s)")
            db_changed += n

    t = doc.get("topic")
    if t:
        tid = con.execute("SELECT id FROM topic WHERE slug=?", (t["id"],)).fetchone()[0]
        got = con.execute("SELECT value FROM localized_text WHERE entity_type='topic' AND entity_id=? "
                          "AND field='objectives' AND locale=?", (tid, LOC)).fetchone()
        if (got[0] if got else None) != json.dumps(t["objectives"], ensure_ascii=False):
            db_changed += 1
            print(f"  {t['id']}: objectives set")
            if not args.check:
                set_text(con, "topic", tid, "objectives", t["objectives"], layer="C")

    if not args.check:
        recompute_cumulative(con)
        con.commit()
    con.close()
    verb = "would change" if args.check else "changed"
    print(f"apply_n3_review_lessons: {len(doc['rows'])} lessons; {verb} {src_changed} authoring "
          f"source(s) and {db_changed} index field(s)")
    return 1 if (args.check and (src_changed or db_changed)) else 0


if __name__ == "__main__":
    sys.exit(main())
