#!/usr/bin/env python3
"""P6 — load authored lesson JSON (research/derived/lessons/*.json) into the DB. Generic + idempotent.

The durable AUTHORING SOURCE is research/derived/lessons/<slug>.json (Layer-C, AI-authored, like the
dissection *_result.json). This loader persists each into lesson/exercise + the lesson_introduces /
lesson_sentence / exercise_* link tables, RE-AUTHORING by slug (delete-then-insert so edits propagate).
After loading all, it computes each lesson's cumulative_known_set (union of introduces up to and including it,
in topic.ord then lesson order). The bank/lessons are wiped by reset_sentences, so this runs after replay_all
to restore lessons. Validate with validate_lessons.py; export with export_course.py. Run with venv python.

Lesson JSON shape:
  {"slug","topic","order","title","objectives":[…],"prerequisites":[…],"schema_version":"1.0",
   "introduces":{"grammar":[key…],"vocab":[headword…],"kanji":[char…]},
   "sentence_refs":["sent:…"], "body":"<heading>…</heading>…",
   "exercises":[{"slug","type","prompt","answer":{…},"explanation","sentence_refs":[…],"item_refs":[{type,ref}…]}]}
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSON_DIR = ROOT / "research" / "derived" / "lessons"


def _member_id(con, mt: str, ident: str):
    col = {"grammar": ("grammar_point", "key"), "vocab": ("vocab", "headword"),
           "kanji": ("kanji", "character")}[mt]
    r = con.execute(f"SELECT id FROM {col[0]} WHERE {col[1]}=?", (ident,)).fetchone()
    return r[0] if r else None


def _sid(con, slug: str):
    r = con.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
    return r[0] if r else None


def _delete_lesson(con, lid: int) -> None:
    exids = [r[0] for r in con.execute("SELECT id FROM exercise WHERE lesson_id=?", (lid,))]
    for eid in exids:
        con.execute("DELETE FROM exercise_sentence WHERE exercise_id=?", (eid,))
        con.execute("DELETE FROM exercise_item WHERE exercise_id=?", (eid,))
        con.execute("DELETE FROM localized_text WHERE entity_type='exercise' AND entity_id=?", (eid,))
    con.execute("DELETE FROM exercise WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM lesson_sentence WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM lesson_introduces WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM localized_text WHERE entity_type='lesson' AND entity_id=?", (lid,))
    con.execute("DELETE FROM lesson WHERE id=?", (lid,))


def persist_lesson(con, rec: dict, warns: list) -> int | None:
    slug = rec["slug"]
    trow = con.execute("SELECT id FROM topic WHERE slug=?", (rec["topic"],)).fetchone()
    if not trow:
        warns.append(f"{slug}: unknown topic {rec['topic']} — skipped")
        return None
    topic_id = trow[0]
    existing = con.execute("SELECT id FROM lesson WHERE slug=?", (slug,)).fetchone()
    if existing:
        _delete_lesson(con, existing[0])
    con.execute(
        "INSERT INTO lesson (slug,topic_id,ord,prerequisites,source,created_by,layer,needs_review) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (slug, topic_id, int(rec.get("order", 1)),
         json.dumps(rec.get("prerequisites", []), ensure_ascii=False), "ai", "ai", "C", 1))
    lid = con.execute("SELECT id FROM lesson WHERE slug=?", (slug,)).fetchone()[0]
    set_text(con, "lesson", lid, "title", rec.get("title"), layer="C")
    set_text(con, "lesson", lid, "objectives", rec.get("objectives", []), layer="C")
    set_text(con, "lesson", lid, "body", rec.get("body"), layer="C")
    for mt in ("grammar", "vocab", "kanji"):
        for ident in rec.get("introduces", {}).get(mt, []):
            mid = _member_id(con, mt, ident)
            if mid is None:
                warns.append(f"{slug}: introduces {mt} '{ident}' not found")
                continue
            con.execute("INSERT OR IGNORE INTO lesson_introduces (lesson_id,member_type,member_id) "
                        "VALUES (?,?,?)", (lid, mt, mid))
    for sl in rec.get("sentence_refs", []):
        s = _sid(con, sl)
        if s is None:
            warns.append(f"{slug}: sentence_ref {sl} not found")
            continue
        con.execute("INSERT OR IGNORE INTO lesson_sentence (lesson_id,sentence_id) VALUES (?,?)", (lid, s))
    for i, ex in enumerate(rec.get("exercises", [])):
        con.execute("INSERT INTO exercise (slug,lesson_id,ord,type,answer,needs_review) VALUES (?,?,?,?,?,?)",
                    (ex["slug"], lid, i, ex["type"],
                     json.dumps(ex.get("answer"), ensure_ascii=False), 1))
        eid = con.execute("SELECT id FROM exercise WHERE slug=?", (ex["slug"],)).fetchone()[0]
        set_text(con, "exercise", eid, "prompt", ex.get("prompt"), layer="C")
        set_text(con, "exercise", eid, "explanation", ex.get("explanation"), layer="C")
        for sl in ex.get("sentence_refs", []):
            s = _sid(con, sl)
            if s is not None:
                con.execute("INSERT OR IGNORE INTO exercise_sentence (exercise_id,sentence_id) VALUES (?,?)",
                            (eid, s))
        for it in ex.get("item_refs", []):
            mid = _member_id(con, it["type"], it["ref"])
            if mid is not None:
                con.execute("INSERT OR IGNORE INTO exercise_item (exercise_id,member_type,member_id) "
                            "VALUES (?,?,?)", (eid, it["type"], mid))
    return lid


def recompute_cumulative(con) -> int:
    """cumulative_known_set per lesson = union of all introduces up to and including it (course order)."""
    acc = {"grammar": [], "vocab": [], "kanji": []}
    seen = {"grammar": set(), "vocab": set(), "kanji": set()}
    n = 0
    for L in con.execute("SELECT l.id FROM lesson l JOIN topic t ON t.id=l.topic_id ORDER BY t.ord, l.ord"):
        lid = L[0]
        for mt, mid in con.execute(
                "SELECT member_type, member_id FROM lesson_introduces WHERE lesson_id=?", (lid,)):
            col = {"grammar": ("grammar_point", "key"), "vocab": ("vocab", "headword"),
                   "kanji": ("kanji", "character")}[mt]
            r = con.execute(f"SELECT {col[1]} FROM {col[0]} WHERE id=?", (mid,)).fetchone()
            if r and r[0] not in seen[mt]:
                seen[mt].add(r[0])
                acc[mt].append(r[0])
        con.execute("UPDATE lesson SET cumulative_known_set=? WHERE id=?",
                    (json.dumps({k: list(v) for k, v in acc.items()}, ensure_ascii=False), lid))
        n += 1
    return n


def main() -> int:
    if not LESSON_DIR.exists():
        print(f"no lesson dir {LESSON_DIR} — nothing to load")
        return 0
    files = sorted(LESSON_DIR.glob("*.json"))
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    warns: list = []
    loaded = 0
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        if persist_lesson(con, rec, warns) is not None:
            loaded += 1
    con.commit()
    nc = recompute_cumulative(con)
    con.commit()
    print(f"loaded {loaded}/{len(files)} lessons; recomputed cumulative_known_set for {nc}; "
          f"warnings={len(warns)}")
    for w in warns[:30]:
        print(f"  warn {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
