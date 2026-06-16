#!/usr/bin/env python3
"""P6 — load authored lesson JSON (research/derived/lessons/*.json) into the DB. Generic + idempotent.

The durable AUTHORING SOURCE is research/derived/lessons/<slug>.json (Layer-C, AI-authored). This loader
persists each into lesson/exercise + the link tables, RE-AUTHORING by slug (delete-then-insert so edits
propagate). After loading all, it computes each lesson's cumulative_known_set. Lessons are wiped by
reset_sentences, so this runs after replay_all to restore them. Validate with validate_lessons.py; export with
export_course.py.

Canonical lesson JSON shape (P6b):
  {"slug","topic","order","title","description","objectives":[…],"schema_version":"1.0",
   "needs":   [{"type","ref","note"?}…],                         # need_type enum (design/unlock_enums.json)
   "unlocks": [{"type","ref"}…],                                  # unlock_type enum; replaces old `introduces`
   "feature_unlocks": ["feat:…"],                                 # convenience; merged into unlocks
   "sentence_refs": ["sent:…"], "body": "<heading>…",
   "exercises": [{"slug","type","prompt","answer":{…},"explanation","sentence_refs":[…],"item_refs":[{type,ref}…]}]}
Back-compat: a lesson with the OLD `introduces:{grammar,vocab,kanji}` (bare ids) is auto-converted to `unlocks`.
SRS cards are DERIVED from unlocks at export time (not stored). `description` -> localized_text.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import set_text  # noqa: E402
import enums  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LESSON_DIR = ROOT / "research" / "derived" / "lessons"
_MEMBER = {"grammar": ("grammar_point", "key"), "vocab": ("vocab", "headword"), "kanji": ("kanji", "character")}


def _member_id(con, mt: str, ident: str):
    tbl, col = _MEMBER[mt]
    r = con.execute(f"SELECT id FROM {tbl} WHERE {col}=?", (ident,)).fetchone()
    return r[0] if r else None


def _sid(con, slug: str):
    r = con.execute("SELECT id FROM sentence WHERE slug=?", (slug,)).fetchone()
    return r[0] if r else None


def _norm_ref(typ: str, ref: str) -> str:
    """Ensure a ref is namespaced (back-compat for bare ids in old `introduces`)."""
    if ":" in ref:
        return ref
    pre = enums.REF_NS.get(typ)
    return f"{pre}:{ref}" if pre else ref


def _unlocks_from_rec(rec: dict) -> list[dict]:
    """Canonical `unlocks`, or convert the legacy `introduces:{grammar,vocab,kanji}` + merge feature_unlocks."""
    out: list[dict] = []
    if rec.get("unlocks"):
        for u in rec["unlocks"]:
            out.append({"type": u["type"], "ref": _norm_ref(u["type"], u["ref"])})
    else:  # legacy
        for mt in ("grammar", "vocab", "kanji"):
            for ident in (rec.get("introduces", {}) or {}).get(mt, []):
                out.append({"type": mt, "ref": _norm_ref(mt, ident)})
    for feat in rec.get("feature_unlocks", []):
        ref = feat if ":" in feat else f"feat:{feat}"
        if not any(u["type"] == "feature" and u["ref"] == ref for u in out):
            out.append({"type": "feature", "ref": ref})
    return out


def _delete_lesson(con, lid: int) -> None:
    exids = [r[0] for r in con.execute("SELECT id FROM exercise WHERE lesson_id=?", (lid,))]
    for eid in exids:
        con.execute("DELETE FROM exercise_sentence WHERE exercise_id=?", (eid,))
        con.execute("DELETE FROM exercise_item WHERE exercise_id=?", (eid,))
        con.execute("DELETE FROM localized_text WHERE entity_type='exercise' AND entity_id=?", (eid,))
    con.execute("DELETE FROM exercise WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM lesson_sentence WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM lesson_introduces WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM lesson_unlocks WHERE lesson_id=?", (lid,))
    con.execute("DELETE FROM lesson_needs WHERE lesson_id=?", (lid,))
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
        (slug, topic_id, int(rec.get("order", 1)), json.dumps([], ensure_ascii=False), "ai", "ai", "C", 1))
    lid = con.execute("SELECT id FROM lesson WHERE slug=?", (slug,)).fetchone()[0]
    set_text(con, "lesson", lid, "title", rec.get("title"), layer="C")
    set_text(con, "lesson", lid, "description", rec.get("description"), layer="C")
    set_text(con, "lesson", lid, "objectives", rec.get("objectives", []), layer="C")
    set_text(con, "lesson", lid, "body", rec.get("body"), layer="C")

    # unlocks (canonical) -> lesson_unlocks; grammar/vocab/kanji subset also -> lesson_introduces (back-compat)
    for u in _unlocks_from_rec(rec):
        typ, ref = u["type"], u["ref"]
        con.execute("INSERT OR IGNORE INTO lesson_unlocks (lesson_id,unlock_type,ref) VALUES (?,?,?)",
                    (lid, typ, ref))
        if typ in _MEMBER:
            _, ident = enums.parse_ref(ref)
            mid = _member_id(con, typ, ident)
            if mid is None:
                warns.append(f"{slug}: unlock {typ} '{ident}' not found in registry")
            else:
                con.execute("INSERT OR IGNORE INTO lesson_introduces (lesson_id,member_type,member_id) "
                            "VALUES (?,?,?)", (lid, typ, mid))
    # needs (+ legacy prerequisites list -> lesson needs)
    needs = list(rec.get("needs", []))
    for pre in rec.get("prerequisites", []):
        needs.append({"type": "lesson", "ref": pre if ":" in str(pre) else f"les:{pre}"})
    for n in needs:
        con.execute("INSERT OR IGNORE INTO lesson_needs (lesson_id,need_type,ref) VALUES (?,?,?)",
                    (lid, n["type"], _norm_ref(n["type"], n["ref"])))
    for sl in rec.get("sentence_refs", []):
        s = _sid(con, sl)
        if s is None:
            warns.append(f"{slug}: sentence_ref {sl} not found")
        else:
            con.execute("INSERT OR IGNORE INTO lesson_sentence (lesson_id,sentence_id) VALUES (?,?)", (lid, s))
    for i, ex in enumerate(rec.get("exercises", [])):
        con.execute("INSERT INTO exercise (slug,lesson_id,ord,type,answer,needs_review) VALUES (?,?,?,?,?,?)",
                    (ex["slug"], lid, i, ex["type"], json.dumps(ex.get("answer"), ensure_ascii=False), 1))
        eid = con.execute("SELECT id FROM exercise WHERE slug=?", (ex["slug"],)).fetchone()[0]
        set_text(con, "exercise", eid, "prompt", ex.get("prompt"), layer="C")
        set_text(con, "exercise", eid, "explanation", ex.get("explanation"), layer="C")
        for sl in ex.get("sentence_refs", []):
            s = _sid(con, sl)
            if s is not None:
                con.execute("INSERT OR IGNORE INTO exercise_sentence (exercise_id,sentence_id) VALUES (?,?)",
                            (eid, s))
        for it in ex.get("item_refs", []):
            typ = it["type"]
            if typ in _MEMBER:
                _, ident = enums.parse_ref(_norm_ref(typ, it["ref"]))
                mid = _member_id(con, typ, ident)
                if mid is not None:
                    con.execute("INSERT OR IGNORE INTO exercise_item (exercise_id,member_type,member_id) "
                                "VALUES (?,?,?)", (eid, typ, mid))
    return lid


def recompute_cumulative(con) -> int:
    """cumulative_known_set per lesson = union of all unlocks up to + including it (course order)."""
    keys = ("kana-family", "vocab", "kanji", "grammar", "conjugation-form", "phrase")
    acc = {k: [] for k in keys}
    seen = {k: set() for k in keys}
    n = 0
    for (lid,) in con.execute(
            "SELECT l.id FROM lesson l JOIN topic t ON t.id=l.topic_id ORDER BY t.ord, l.ord"):
        for typ, ref in con.execute("SELECT unlock_type, ref FROM lesson_unlocks WHERE lesson_id=?", (lid,)):
            if typ in acc and ref not in seen[typ]:
                seen[typ].add(ref)
                acc[typ].append(ref)
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
    print(f"loaded {loaded}/{len(files)} lessons; recomputed cumulative_known_set for {nc}; warnings={len(warns)}")
    for w in warns[:30]:
        print(f"  warn {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
