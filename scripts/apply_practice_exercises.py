#!/usr/bin/env python3
"""W20 — put the authored kanji practice exercises into the lessons that teach the kanji, both layers.

WHAT WAS WRONG
--------------
`validate_practice_coverage.py` asks, per item, "was THIS item asked by the lesson that unlocks it?".
The answer for kanji was: almost never. 581 (lesson, kanji) pairs across 178 lessons unlocked a
character, enrolled an SRS card for it, and never put it in a single answer key — 92 at N5, 173 at
N4, 316 at N3, frozen as debt in `scripts/validate/practice_coverage_baseline.json`. APP_PLAN W20 is
the fix, and the kanji half was authored and verified before this script existed.

WHAT THIS APPLIES
-----------------
`research/derived/repairs/practice_kanji_exercises.json` — 899 exercises over those same 178 lessons,
each row `{lesson, targets, exercise, why}` where `exercise` is a complete
`contracts/lesson.schema.json` exercise object. THE CONTENT IS IN THE TABLE and this script only
places it: nothing here writes, rewrites or repairs a prompt, an answer key or an explanation. A row
that cannot be placed against the current tree is reported and SKIPPED, never adapted.

IDS
---
Ids continue each lesson's own numbering, in the lesson's own prefix pattern. The table carries two
id decision blocks and both are data, not inference:
  * `id_fixes` — realignments made when the campaign was assembled (`ex:n3-limites-04-6` ->
    `ex:n3limites-04-6`, the prefix that lesson actually uses). Already folded into `rows`.
  * `apply_id_remap` — the collisions this APPLY found. Three lessons gained an exercise between
    authoring and apply (W11a's homograph practice items: `ex:n5-passado-05-7`,
    `ex:n5-particulas-lugar-02-6`, `ex:n4-condicionais-01-6`), so six authored ids named a slug that
    now exists. The block shifts those six by one, which is what "continue the lesson's numbering"
    means on today's tree. Nothing else moves.

BOTH LAYERS
-----------
The authoring layer is the tracked table (the decision, exact-match, replayed by
`validate_repairs_applied.py`) plus `research/derived/lessons/<slug>.json` (the source the ingest
chain reads); this script writes those and the index `db/corpus.sqlite`, and
`scripts/export/export_course.py` republishes `course/*/topic-*/lesson-*.json`, which is canonical.

THE BODY
--------
The app renders exercises ONLY from `<exercise ref="…"/>` nodes
(`prototype/app/lib/render-body.server.ts`), and `validate_exercise_contracts.py` gates the
id<->body bijection in both directions, so every inserted exercise needs a node. That node is the
ONLY body change this script makes: it is appended after the lesson's last existing `<exercise ref>`,
in the separator style that lesson already uses. The eight `*-kanji-exame-*` lessons have no practice
block at all — for them the nodes go immediately before the closing `<checklist>`, which is where
their practice would have been. No heading is added and no prose is touched: a rendered-text diff of
every lesson against git HEAD must show zero differences, and that is checked separately.

PROVENANCE
----------
Every inserted exercise is Layer C, `ai_generated`, `needs_review`. The `exercise` entity has no
provenance columns and the exported exercise object has no provenance fields — `validate_provenance_json`
rule (e)/(g) makes provenance all-or-nothing per entity, so stamping 899 of 2,463 exercises would
fail the gate and stamping all of them is a different unit (a backfill over content this campaign did
not author). What this script does write is `needs_review = 1` on every row it inserts, which is the
one provenance column `exercise` has; the layer/source/ai_generated claim for these 899 lives in the
tracked table's header, beside the rows it describes.

IDEMPOTENT. An exercise whose slug is already there is re-asserted from the table (type, answer,
prompt, explanation) and its body node is left alone; a second run reports 0 changes.

Run `scripts/export/export_course.py` afterwards.
Usage: apply_practice_exercises.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
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
# The table is a committed INPUT to the rebuild, so it is read from the repo, never from --out-root.
TABLE = ROOT / "research" / "derived" / "repairs" / "practice_kanji_exercises.json"
EXEMPTIONS = OUT / "course" / "practice_exemptions.json"
LOC = "pt-BR"

NODE_RX = re.compile(r'<exercise\s+ref="[^"]+"\s*/>')
CHECKLIST_RX = re.compile(r"<checklist[\s>]")


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc


def _lesson_body(con, lid: int) -> str:
    r = con.execute("SELECT value FROM localized_text WHERE entity_type='lesson' AND entity_id=? "
                    "AND field='body' AND locale='pt-BR'", (lid,)).fetchone()
    return r[0] if r else ""


def node_separator(body: str) -> str:
    """The string this body already puts between two consecutive `<exercise ref>` nodes.

    322 lessons use two styles — 1,175 gaps are a newline, 75 are nothing, and the split is per
    lesson, not per level. Matching the lesson rather than picking a house style is what keeps the
    diff of an already-formatted body to the inserted node itself.
    """
    ms = list(NODE_RX.finditer(body))
    if len(ms) >= 2:
        return body[ms[-2].end():ms[-1].start()]
    return "\n" if "\n" in body else ""


def insert_node(body: str, node: str) -> tuple[str, str] | None:
    """Return (new body, where) with `node` placed in this lesson's practice block, or None."""
    sep = node_separator(body)
    ms = list(NODE_RX.finditer(body))
    if ms:
        cut = ms[-1].end()
        return body[:cut] + sep + node + body[cut:], "after the last <exercise ref>"
    m = CHECKLIST_RX.search(body)
    if m:
        cut = m.start()
        return body[:cut] + node + sep + body[cut:], "before the closing <checklist>"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    args = ap.parse_args()

    sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
    from i18n_text import set_text                                          # noqa: E402

    doc = load_table()
    remap = {(r["lesson"], r["from"]): r["to"] for r in doc.get("apply_id_remap") or []}
    rows = doc["rows"]

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    changed = 0
    problems: list[str] = []
    inserted = reasserted = nodes = 0
    lessons_touched: set[str] = set()

    for r in rows:
        lslug = r["lesson"]
        ex = r["exercise"]
        exslug = remap.get((lslug, ex["id"]), ex["id"])
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (lslug,)).fetchone()
        if not lr:
            problems.append(f"{lslug}: no such lesson in the index")
            continue
        lid = lr[0]
        lessons_touched.add(lslug)
        answer = json.dumps(ex.get("answer"), ensure_ascii=False)
        prompt = (ex.get("prompt") or {}).get(LOC)
        explanation = (ex.get("explanation") or {}).get(LOC)

        have = con.execute("SELECT id FROM exercise WHERE slug=?", (exslug,)).fetchone()
        if not have:
            other = con.execute(
                "SELECT l.slug FROM exercise e JOIN lesson l ON l.id=e.lesson_id "
                "WHERE e.lesson_id=? AND e.type=? AND e.answer=?", (lid, ex["type"], answer)).fetchone()
            if other:
                problems.append(f"{lslug}: {exslug} is new but an exercise with the same type and "
                                f"answer key is already in this lesson — refusing to duplicate it")
                continue
            nxt = con.execute("SELECT COALESCE(MAX(ord), -1) + 1 FROM exercise WHERE lesson_id=?",
                              (lid,)).fetchone()[0]
            print(f"  {lslug}: +exercise {exslug} ({ex['type']}, targets {' '.join(r['targets'])}) (db)")
            changed += 1
            inserted += 1
            if not args.check:
                con.execute("INSERT INTO exercise (slug, lesson_id, ord, type, answer, needs_review) "
                            "VALUES (?,?,?,?,?,1)", (exslug, lid, nxt, ex["type"], answer))
                eid = con.execute("SELECT id FROM exercise WHERE slug=?", (exslug,)).fetchone()[0]
                set_text(con, "exercise", eid, "prompt", prompt, layer="C")
                set_text(con, "exercise", eid, "explanation", explanation, layer="C")
        else:
            # Already placed. The TABLE owns the content, so a difference is rewritten from the row —
            # a correction to a verified exercise must reach the export, not die in the table.
            eid = have[0]
            cur_type, cur_ans, cur_lesson = con.execute(
                "SELECT type, answer, lesson_id FROM exercise WHERE id=?", (eid,)).fetchone()
            if cur_lesson != lid:
                problems.append(f"{lslug}: {exslug} belongs to another lesson in the index")
                continue
            if cur_type != ex["type"] or (json.loads(cur_ans) if cur_ans else None) != ex.get("answer"):
                print(f"  {lslug}: {exslug} type/answer rewritten from the table (db)")
                changed += 1
                reasserted += 1
                if not args.check:
                    con.execute("UPDATE exercise SET type=?, answer=? WHERE id=?",
                                (ex["type"], answer, eid))
            for field, want in (("prompt", prompt), ("explanation", explanation)):
                got = con.execute(
                    "SELECT value FROM localized_text WHERE entity_type='exercise' AND entity_id=? "
                    "AND field=? AND locale=?", (eid, field, LOC)).fetchone()
                if (got[0] if got else None) != want:
                    print(f"  {lslug}: {exslug} {field} rewritten from the table (db)")
                    changed += 1
                    reasserted += 1
                    if not args.check:
                        set_text(con, "exercise", eid, field, want, layer="C")

        # ---- the body node, in both layers -------------------------------------------------
        node = f'<exercise ref="{exslug}"/>'
        body = _lesson_body(con, lid)
        if node not in body:
            placed = insert_node(body, node)
            if placed is None:
                problems.append(f"{lslug}: body has neither an <exercise ref> node nor a <checklist> "
                                f"to place {exslug} against")
                continue
            print(f"  {lslug}: +{node} {placed[1]} (db)")
            changed += 1
            nodes += 1
            if not args.check:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND "
                            "entity_id=? AND field='body' AND locale=?", (placed[0], lid, LOC))

        f = SRC / f"{lslug.split(':', 1)[1]}.json"
        if not f.exists():
            problems.append(f"{lslug}: authoring source {f.name} missing")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        dirty = False
        src_ex = next((e for e in d.get("exercises", []) if e.get("slug") == exslug), None)
        if src_ex is None:
            print(f"  {lslug}: +exercise {exslug} (source)")
            changed += 1
            dirty = True
            d.setdefault("exercises", []).append({
                "slug": exslug, "type": ex["type"], "prompt": prompt, "answer": ex.get("answer"),
                "explanation": explanation, "sentence_refs": list(ex.get("sentence_refs") or []),
                "item_refs": []})
        else:
            for field, want in (("type", ex["type"]), ("prompt", prompt),
                                ("answer", ex.get("answer")), ("explanation", explanation)):
                if src_ex.get(field) != want:
                    print(f"  {lslug}: {exslug} {field} rewritten from the table (source)")
                    changed += 1
                    dirty = True
                    src_ex[field] = want
        src_body = d.get("body") or ""
        if node not in src_body:
            placed = insert_node(src_body, node)
            if placed is None:
                problems.append(f"{lslug}: authoring source body has no place for {exslug}")
                continue
            print(f"  {lslug}: +{node} {placed[1]} (source)")
            changed += 1
            dirty = True
            d["body"] = placed[0]
        if dirty and not args.check:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    changed += prune_exemptions(doc, args.check, problems)

    if not args.check:
        con.commit()
    con.close()
    print(f"apply_practice_exercises: {len(rows)} rows over {len(lessons_touched)} lessons — "
          f"{inserted} exercises inserted, {reasserted} field(s) re-asserted, {nodes} body nodes; "
          f"{changed} change(s){' (check only)' if args.check else ''}")
    if problems:
        print(f"=== {len(problems)} PROBLEM(S) — nothing was written for these rows ===")
        for p in problems[:40]:
            print(f"  {p}")
        return 1
    return 0


def prune_exemptions(doc: dict, check: bool, problems: list[str]) -> int:
    """Drop the practice exemptions this campaign made stale, by the rule the file itself states.

    `course/practice_exemptions.json` says an entry "whose lesson has since gained practice" is
    itself a failure, and `validate_exercise_contracts.py` enforces exactly that: an exempt lesson
    that now renders BOTH a retrieval and a production exercise fails. The five lessons this table
    gives both to therefore lose their entry; the three it deliberately gives retrieval only keep
    theirs, because dropping those would trip the opposite rule. The membership is not inferred
    here — it is the `exemptions` block of the table, checked against what the rows actually do.
    """
    decision = doc.get("exemptions") or {}
    drop, keep = set(decision.get("drop") or []), set(decision.get("keep") or [])
    if not drop and not keep:
        return 0
    if not EXEMPTIONS.is_file():
        # A replay into a work root that carries no exported course tier yet: there is no exemption
        # file to prune. Say so rather than crashing — the file is course output, not a rebuild input.
        print(f"  practice_exemptions.json not present under {EXEMPTIONS.parent} — nothing to prune")
        return 0
    RETRIEVAL = {"recognition", "reading", "listening", "cloze", "particle_choice", "matching", "ordering"}
    PRODUCTION = {"production", "handwriting"}
    per: dict[str, set[str]] = {}
    for r in doc["rows"]:
        per.setdefault(r["lesson"], set()).add(r["exercise"]["type"])
    for lid in drop:
        types = per.get(lid, set())
        if not (types & RETRIEVAL and types & PRODUCTION):
            problems.append(f"practice_exemptions: {lid} is marked drop but this table gives it "
                            f"{sorted(types)} — it would still fail the retrieval+production rule")
    for lid in keep:
        types = per.get(lid, set())
        if types & PRODUCTION:
            problems.append(f"practice_exemptions: {lid} is marked keep but this table gives it a "
                            f"production item, so the exemption would be stale")
    data = json.loads(EXEMPTIONS.read_text(encoding="utf-8"))
    before = [e["id"] for e in data["lessons"]]
    # A `drop` entry that is already gone is this script's own previous run, not a stale name — only
    # a `keep` the file does not carry is a table that has lost touch with the tree.
    unknown = keep - set(before)
    if unknown:
        problems.append(f"practice_exemptions: {sorted(unknown)} is marked keep by the table but is "
                        f"not in course/practice_exemptions.json")
    after = [e for e in data["lessons"] if e["id"] not in drop]
    if len(after) == len(before):
        return 0
    print(f"  practice_exemptions.json: dropping {sorted(drop & set(before))} "
          f"(keeping {sorted(keep & set(before))})")
    if not check:
        data["lessons"] = after
        EXEMPTIONS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(before) - len(after)


if __name__ == "__main__":
    sys.exit(main())
