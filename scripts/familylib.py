#!/usr/bin/env python3
"""W11b — the shared spine of the family builders: RECOMPUTE, and retire what stops being derived.

WHY THIS MODULE EXISTS
----------------------
`research/reports/family_layer_rebuild.md` measured the family layer as a write-only leaf frozen at
a pre-N3 snapshot: 272 of 364 grammar memberships named the wrong topic, 0 of 51 kanji-component
families still equalled the store they duplicated, and both vocab builders filtered
`level IN ('n5','n4')` as a literal. The cause was one shape shared by every builder — they were
"idempotent" by refusing to run, or by skipping a slug that already existed:

    if con.execute("SELECT COUNT(*) FROM family").fetchone()[0] > 0: return 0   # build_families.py
    row = cur.execute("SELECT id FROM family WHERE slug=?", ...);  if row: return row[0]  # _full.py

Both of those make a second run a no-op, which is the opposite of idempotent for a DERIVED layer:
the derivation stops tracking its source the moment the source moves. `recompute()` below is the
replacement — running it twice gives the same answer, and running it after the course moves gives
the NEW answer.

The second half is `retire_unbuilt()`. `family.slug` is a published address (`contracts/manifest.json`
id_namespace `grp`), so a slug a builder stops deriving cannot simply vanish: it is marked
`deprecated_by` — the same redirect column `grammar_point` and `vocab` already carry — and published
in `corpus/families_deprecated.json`. A redirect target is either a surviving `grp:` slug or, when
the answer moved out of the family layer entirely, the exported field path that now answers the
question (`kanji.components` for owner decision D14).

THE TOPIC LEDGER
----------------
`unlock_topic_map()` is the other half of the fix. The builders used to read
`grammar_point.introducing_topic_id`, a column written by a P4 placement pass and never updated
again. The course's live answer to "where is this taught?" is `lesson_unlocks`, which is what
`validate_unlock_ledger.py` gates and what `course/**/lesson-*.json` publishes. Deriving the
topic-bound families from the ledger is what makes `validate_families.py`'s F1/F2 provable rather
than hopeful.

It dereferences through `export_course._deref` on purpose. Lesson refs are stored in two forms that
are storage artefacts rather than addresses (`vocab:1421` is a row number, `vocab:人` a headword
three records answer to), and the export rewrites both to the published slug. A family layer that
dereferenced them differently would bind members the validator could not match, so the two share one
implementation instead of two that agree until they do not.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS / "export") not in sys.path:
    sys.path.append(str(_SCRIPTS / "export"))
if str(_SCRIPTS / "ingest") not in sys.path:
    sys.path.append(str(_SCRIPTS / "ingest"))

from i18n_text import set_text  # noqa: E402

LEVEL_SEQ = ["pre-n5", "n5", "n4", "n3", "n2", "n1"]

_MEMBER_TABLE = {"kanji": "kanji", "vocab": "vocab", "grammar": "grammar_point"}


def taught_levels(con: sqlite3.Connection) -> list[str]:
    """The levels the project actually TEACHES, read from the course modules.

    CLAUDE.md §1.6: level is data, not structure. Every builder scopes itself with this, so the day
    an N2 course exists the derived families widen to it with no edit in any builder — which is
    precisely the edit that was missing when `level IN ('n5','n4')` sat hardcoded in
    build_families_full.py while the N3 registries landed.
    """
    got = {r[0] for r in con.execute(
        "SELECT DISTINCT level FROM course_module WHERE level IS NOT NULL")}
    return [lv for lv in LEVEL_SEQ if lv in got]


def member_levels(con: sqlite3.Connection, members) -> list[str]:
    """The levels a member set actually occupies, in teaching order.

    `spans_levels` was stored at authoring time and went stale on 16 families. It is derived at
    export time now; storing the derived value here too keeps the column from lying to anyone who
    reads the index directly.
    """
    found = set()
    for mtype, mid, *_ in members:
        tbl = _MEMBER_TABLE.get(mtype)
        if not tbl:
            continue
        r = con.execute(f"SELECT level FROM {tbl} WHERE id=?", (mid,)).fetchone()
        if r and r[0]:
            found.add(r[0])
    return [lv for lv in LEVEL_SEQ if lv in found]


def recompute(con, cur, slug: str, ftype: str, rank: int, members, spans,
              label_pt: str, label_en: str,
              rule_pt: str | None = None, rule_en: str | None = None) -> int:
    """Rewrite one derived family in place: members re-derived, template text re-applied.

    `members` is [(member_type, member_id, sort_key)]; the sort key orders `intra_order` and picks
    `is_core` (the first member). A None sort key sorts last, then by member id, so the ordering is
    total and a rebuild reproduces the export byte for byte.

    label/governing_rule are TEMPLATE text this builder owns and overwrites in both locales;
    `description` is the authored Layer-C field and is never touched here. A derived family whose
    label a teacher wants to change is an authored family (W39), not an edit to a template — if the
    builder preserved arbitrary prior values, a fresh rebuild could not reproduce the committed
    export, which is exactly what `validate_index_rebuildable.py` asserts.

    Writes the text to `localized_text` (the single source the exporters read, see
    scripts/ingest/i18n_text.py) AND to the legacy `*_pt` columns, because `migrate_i18n.py` runs at
    manifest step 30 and these builders run at 37-39: a family built after the migration would
    otherwise export with a null label on a from-scratch rebuild.
    """
    row = cur.execute("SELECT id FROM family WHERE slug=?", (slug,)).fetchone()
    spans_json = json.dumps(spans)
    if row:
        fid = row[0]
        cur.execute("DELETE FROM family_member WHERE family_id=?", (fid,))
        cur.execute(
            "UPDATE family SET type=?, label_pt=?, importance_rank=?, governing_rule_pt=?, "
            "spans_levels=?, source='derived', created_by='ai', layer='C', needs_review=1, "
            "deprecated_by=NULL WHERE id=?",
            (ftype, label_pt, rank, rule_pt, spans_json, fid))
    else:
        cur.execute(
            "INSERT INTO family (slug,type,label_pt,description_pt,importance_rank,"
            "governing_rule_pt,spans_levels,source,created_by,layer,needs_review) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (slug, ftype, label_pt, None, rank, rule_pt, spans_json, "derived", "ai", "C", 1))
        fid = cur.lastrowid

    set_text(con, "family", fid, "label", label_pt, "pt-BR")
    set_text(con, "family", fid, "label", label_en, "en", layer="B")
    if rule_pt:
        set_text(con, "family", fid, "governing_rule", rule_pt, "pt-BR")
        set_text(con, "family", fid, "governing_rule", rule_en, "en", layer="B")

    ordered = sorted(members, key=lambda m: (m[2] is None, m[2] if m[2] is not None else 0, m[1]))
    for i, (mtype, mid, _k) in enumerate(ordered):
        cur.execute(
            "INSERT OR IGNORE INTO family_member (family_id,member_type,member_id,intra_order,"
            "is_core,note_pt) VALUES (?,?,?,?,?,?)", (fid, mtype, mid, i, 1 if i == 0 else 0, None))
    return fid


def retire(cur, slug: str, successor: str) -> bool:
    """Mark one published family address retired, naming where the answer moved to.

    The members go with it — a retired family groups nothing — but the row and its slug stay, so a
    consumer holding the old address gets a redirect instead of a 404.
    """
    row = cur.execute("SELECT id, deprecated_by FROM family WHERE slug=?", (slug,)).fetchone()
    if row is None:
        return False
    fid, already = row
    cur.execute("DELETE FROM family_member WHERE family_id=?", (fid,))
    cur.execute("DELETE FROM family_related WHERE family_id=? OR related_family_id=?", (fid, fid))
    if already == successor:
        return False
    cur.execute("UPDATE family SET deprecated_by=? WHERE id=?", (successor, fid))
    return True


def retire_unbuilt(cur, exact: set, prefixes: tuple, built: set, successor: str) -> int:
    """Retire every slug this builder OWNS (an exact name or one of its prefixes) that it no longer
    derives. This is what turns "the builder stopped emitting X" from a silent orphan into a
    published redirect, and it is why a shrinking course cannot leave a family behind.
    """
    owned = []
    for (slug,) in cur.execute("SELECT slug FROM family").fetchall():
        if slug in built:
            continue
        if slug in exact or any(slug.startswith(p) for p in prefixes):
            owned.append(slug)
    return sum(1 for s in sorted(owned) if retire(cur, s, successor))


def _published(con: sqlite3.Connection) -> dict:
    """member_type -> {published slug: row id}. `kanji` is addressed `kanji:<character>` in the
    courseware and `kanji:<character>` in the registry, so one map serves both."""
    return {
        "vocab": {s: i for i, s in con.execute("SELECT id, slug FROM vocab")},
        "kanji": {s: i for i, s in con.execute("SELECT id, slug FROM kanji")},
        "grammar": {s: i for i, s in con.execute("SELECT id, slug FROM grammar_point")},
    }


def _is_live_index(con: sqlite3.Connection) -> bool:
    """True when this connection is the repo's own db/corpus.sqlite, not a scratch rebuild."""
    live = Path(__file__).resolve().parents[1] / "db" / "corpus.sqlite"
    for _seq, name, file in con.execute("PRAGMA database_list"):
        if name == "main" and file:
            try:
                return Path(file).resolve() == live.resolve()
            except OSError:
                return False
    return False


def unlock_topic_map(con: sqlite3.Connection) -> dict:
    """(member_type, member_row_id) -> topic row id, from the LIVE unlock ledger.

    A duplicate unlock is a contradiction: `validate_unlock_ledger.py` gates introduce-once, so a
    second lesson unlocking the same item means the course changed under an invariant this
    derivation depends on, and guessing which topic wins is how the layer went stale the first time.

    Against `db/corpus.sqlite` that stays a hard refusal. Against a SCRATCH REBUILD it is a warning
    and the earliest lesson in course order wins — the same rule
    `load_lessons.backfill_introducing_topic()` already uses for "which topic introduces this", and
    the iteration below is already in course order, so `setdefault` implements it. The reason is
    that a from-scratch replay is known not to reproduce the course exactly yet: step 33
    (`build_exam_kanji_lessons.py`) re-chunks the kanji exam lessons from scratch and produces 221
    kanji that two lessons unlock, which `scripts/validate/rebuild_baseline.json` already records as
    a rebuild-fidelity gap with its cause. Aborting the whole rebuild on a gap the baseline is
    designed to hold made the full mode unrunnable — and the assertion is not lost, because
    `validate_unlock_ledger.py` is hard, runs on every gate, and reads the export.
    """
    import export_course as _ec  # heavy, and only this function needs it

    strict = _is_live_index(con)
    maps = _published(con)
    topic_of = {lid: tid for lid, tid in con.execute("SELECT id, topic_id FROM lesson")}
    out: dict = {}
    clashes = 0
    for lid, utype, ref in con.execute(
            "SELECT lu.lesson_id, lu.unlock_type, lu.ref FROM lesson_unlocks lu "
            "JOIN lesson l ON l.id = lu.lesson_id JOIN topic t ON t.id = l.topic_id "
            "JOIN course_module m ON m.id = t.module_id "
            "ORDER BY m.ord, t.ord, l.ord, lu.unlock_type, lu.ref"):
        if utype not in maps:
            continue                      # feature / kana-family unlocks are not registry records
        pub = _ec._deref(con, ref, lid)
        mid = maps[utype].get(pub)
        if mid is None:
            raise SystemExit(f"familylib: lesson unlock {utype} {ref!r} dereferenced to {pub!r}, "
                             f"which is no live {utype} record")
        key = (utype, mid)
        if key in out and out[key] != topic_of[lid]:
            msg = (f"familylib: {utype} {pub} is unlocked under two topics "
                   f"({out[key]} and {topic_of[lid]}); introduce-once is broken and the "
                   f"topic-derived families cannot be derived from a ledger that contradicts itself")
            if strict:
                raise SystemExit(msg)
            clashes += 1
            if clashes <= 3:
                print(f"  WARN (scratch rebuild, not the live index) {msg}")
        out.setdefault(key, topic_of[lid])
    if clashes:
        print(f"  WARN {clashes} item(s) unlocked under more than one topic; the EARLIEST lesson in "
              f"course order was taken. Not possible against db/corpus.sqlite, where this is a hard "
              f"refusal — see scripts/validate/rebuild_baseline.json for why a replay differs.")
    return out


def unlock_order(con: sqlite3.Connection) -> dict:
    """(member_type, member_row_id) -> the position of its unlocking lesson in course order.

    Used as the sort key inside a topic-derived family so `intra_order` follows the sequence the
    learner meets the items in, and `is_core` is the one the topic opens with.
    """
    import export_course as _ec

    maps = _published(con)
    out: dict = {}
    for n, (lid, utype, ref) in enumerate(con.execute(
            "SELECT lu.lesson_id, lu.unlock_type, lu.ref FROM lesson_unlocks lu "
            "JOIN lesson l ON l.id = lu.lesson_id JOIN topic t ON t.id = l.topic_id "
            "JOIN course_module m ON m.id = t.module_id "
            "ORDER BY m.ord, t.ord, l.ord, lu.unlock_type, lu.ref")):
        if utype not in maps:
            continue
        mid = maps[utype].get(_ec._deref(con, ref, lid))
        if mid is not None:
            out.setdefault((utype, mid), n)
    return out
