#!/usr/bin/env python3
"""Apply W11a's homograph rulings: five unlocks the prose already teaches, in BOTH layers.

The table is research/derived/repairs/homograph_rulings.json (owner decision, 2026-09-09, on
research/reports/homograph_recommendations.md). It carries three kinds of row and only one of them
writes anything:

  ref     14 (headword, lesson) disambiguation rulings. Nothing to write: seven are derived at export
          time by scripts/export/vocab_identity.py's `reading` tier (the lesson prints the kana beside
          the chip) and seven are read from this table by its `ruling` tier. This script VERIFIES both
          — it runs the real resolver over the real bodies and fails if any row's `new` is not what
          the resolver produces, and fails if a row marked `reading` needed the ruling table to get
          there. That is the guard that keeps the rule load-bearing: a table that silently covered for
          a broken rule would be a lookup table wearing a rule's costume.

  unlock  5 rows. THIS is the write. Each names a record at a taught level that no lesson unlocked,
          held open in course/coverage_exemptions.json, whose lesson already teaches the word in its
          own body. The unlock goes into the DB (lesson_unlocks) AND into the authoring source
          (research/derived/lessons/<slug>.json), because the source is what a rebuild replays.
          Four of the five need nothing else: their body already renders a chip that resolves to the
          record (which is why course/gating_exemptions.json had to hold them). The fifth,
          何方/どなた, is the one lesson that must unlock BOTH siblings of one headword, so it gets an
          explicit slug ref (a row-id ref until W11c rewrote it through
          research/derived/repairs/lesson_ref_addresses.json) and one re-cut sentence that
          gives どなた its own chip.

  practice 4 rows. The exercise each promoted unlock needs so its lesson actually asks about it.
          Written to both layers as well: `exercise` + its localized prompt/explanation here, the
          same record in the authoring source, and the `<exercise ref=…/>` node the app renders from
          appended to the lesson's practice block. Without them validate_practice_coverage's
          (n5, vocab) and (n4, vocab) debt would GROW by four, and it would be right to fail: an
          unlock the lesson never asks about is a card the SRS schedules and nobody rehearsed.
          中/なか needed none, its lesson already drills it through 〜の中で.

  hold    4 rows. Nothing to write, by design: these stay in course/coverage_exemptions.json. The
          script asserts they are still exempt and still unlocked by nothing, so a hold cannot rot
          into a silent hole.

Exemption files can only shrink (scripts/validate/README.md), so the five promoted records are
removed from course/coverage_exemptions.json and the four whose body chips they cover are removed
from course/gating_exemptions.json — both are edited here rather than by hand, so the table and the
files can never drift.

Idempotent: re-running finds every write already present and reports 0 changes. Run
scripts/export/export_course.py afterwards.

Usage: apply_homograph_rulings.py [--check] [--db PATH] [--out-root PATH]
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
TABLE = ROOT / "research" / "derived" / "repairs" / "homograph_rulings.json"
COVERAGE_EXEMPT = OUT / "course" / "coverage_exemptions.json"
GATING_EXEMPT = OUT / "course" / "gating_exemptions.json"

sys.path.insert(0, str(ROOT / "scripts" / "export"))
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))

# The one prose edit in this unit, quoted in full so the diff lives beside the decision that caused
# it. les:n5-passado-05 taught どなた in a trailing clause of どちら's own list item, so the word
# reached the learner with no chip, no card and no way into the SRS. The re-cut gives it a chip and
# says why the two readings share a kanji; both halves keep their original glosses.
DONATA_OLD = ('<item><vocab ref="vocab:何方"/><text>: qual direção, para onde; é também a forma '
              "educada de 'qual (dos dois)' e até de 'quem'. Lido como どなた, vira uma maneira "
              "polida de perguntar 'quem é?'.</text></item>")
DONATA_NEW = ('<item><vocab ref="vocab:何方"/><text>: qual direção, para onde; é também a forma '
              'educada de \'qual (dos dois)\'. </text><vocab ref="vocab:1189370"/><text>, o mesmo kanji '
              "lido de outro jeito, é a maneira polida de perguntar 'quem é?'.</text></item>")
BODY_EDITS = {"les:n5-passado-05": (DONATA_OLD, DONATA_NEW)}


def load_table() -> dict:
    doc = json.loads(TABLE.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{TABLE.name}: row_count {doc.get('row_count')} != {len(doc['rows'])} rows")
    return doc


def _lesson_body(con, lid: int) -> str:
    r = con.execute("SELECT value FROM localized_text WHERE entity_type='lesson' AND entity_id=? "
                    "AND field='body' AND locale='pt-BR'", (lid,)).fetchone()
    return r[0] if r else ""


def verify_refs(con, rows: list[dict], problems: list[str]) -> int:
    """Run the real resolver over the real bodies; every `ref` row must land on its own `new`."""
    from vocab_identity import VocabIdentity
    from export_course import _READING_HINT  # the one definition of "a reading printed beside a chip"

    with_rulings = VocabIdentity(con)                      # production configuration
    without = VocabIdentity(con, rulings={})               # rulings tier disabled, to prove the rule
    checked = 0
    for r in rows:
        if r["kind"] != "ref":
            continue
        checked += 1
        hw, lslug = r["headword"], r["lesson"]
        lr = con.execute("SELECT l.id, m.level FROM lesson l JOIN topic t ON t.id=l.topic_id "
                         "JOIN course_module m ON m.id=t.module_id WHERE l.slug=?", (lslug,)).fetchone()
        if not lr:
            problems.append(f"{hw} @ {lslug}: no such lesson")
            continue
        lid, level = lr
        body = _lesson_body(con, lid)
        # Every reading this body prints beside a chip naming THIS headword. More than one distinct
        # value means the lesson annotates the same headword two ways and a per-lesson row cannot
        # describe it — say so rather than silently taking the last one.
        printed_all = {m.group("reading") for m in _READING_HINT.finditer(body)
                       if m.group("ref") == f"vocab:{hw}"}
        if len(printed_all) > 1:
            problems.append(f"{hw} @ {lslug}: the body prints {sorted(printed_all)} beside chips for "
                            f"one headword — this row cannot describe both occurrences")
            continue
        printed = next(iter(printed_all), None)
        if printed != r.get("printed_reading"):
            problems.append(f"{hw} @ {lslug}: table says the lesson prints "
                            f"{r.get('printed_reading')!r}, the body prints {printed!r}")
        got, how = with_rulings.resolve(hw, level, lslug, "body", printed)
        if got != r["new"]:
            problems.append(f"{hw} @ {lslug}: resolver produces {got} ({how}), the ruling says {r['new']}")
        elif how != r["how"]:
            problems.append(f"{hw} @ {lslug}: resolved by {how!r}, the table says {r['how']!r}")
        if r["how"] == "reading":
            # The load-bearing check: with the rulings tier switched off, the reading tier alone
            # must still produce this row. Otherwise the table is covering for a rule that stopped
            # working and nothing would ever say so.
            got2, how2 = without.resolve(hw, level, lslug, "body", printed)
            if (got2, how2) != (r["new"], "reading"):
                problems.append(f"{hw} @ {lslug}: marked `reading` but without the ruling table the "
                                f"resolver gives {got2} ({how2}) — the rule is not what settles it")
    return checked


def apply_unlocks(con, rows: list[dict], check: bool, problems: list[str]) -> int:
    changed = 0
    for r in rows:
        if r["kind"] != "unlock":
            continue
        lslug, ref, want = r["lesson"], r["ref_written"], r["new"]
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (lslug,)).fetchone()
        if not lr:
            problems.append(f"{lslug}: no such lesson")
            continue
        lid = lr[0]
        # Pre-verify the ref really names the record the row claims, before writing it anywhere.
        # Three forms, in the order they rank as addresses: the published slug (W11c), a row number
        # (still accepted, still checked), and a headword the resolver has to settle.
        ident = ref.split(":", 1)[1]
        if con.execute("SELECT 1 FROM vocab WHERE slug=?", (ref,)).fetchone():
            if ref != want:
                problems.append(f"{lslug}: slug ref {ref} is not the record the row names ({want})")
                continue
        elif ident.isascii() and ident.isdigit():
            got = con.execute("SELECT slug FROM vocab WHERE id=?", (int(ident),)).fetchone()
            if not got or got[0] != want:
                problems.append(f"{lslug}: row-id ref {ref} names {got and got[0]}, not {want}")
                continue
        else:
            cands = [c[0] for c in con.execute("SELECT slug FROM vocab WHERE headword=?", (ident,))]
            if want not in cands:
                problems.append(f"{lslug}: headword ref {ref} has no candidate {want} ({cands})")
                continue

        have = con.execute("SELECT 1 FROM lesson_unlocks WHERE lesson_id=? AND unlock_type='vocab' "
                           "AND ref=?", (lid, ref)).fetchone()
        if not have:
            print(f"  {lslug}: +unlock {ref} -> {want} (db)")
            if not check:
                con.execute("INSERT OR IGNORE INTO lesson_unlocks (lesson_id, unlock_type, ref) "
                            "VALUES (?, 'vocab', ?)", (lid, ref))
            changed += 1

        f = SRC / f"{lslug.split(':', 1)[1]}.json"
        if not f.exists():
            problems.append(f"{lslug}: authoring source {f.name} missing")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if not any(u.get("type") == "vocab" and u.get("ref") == ref for u in d.get("unlocks", [])):
            print(f"  {lslug}: +unlock {ref} (source)")
            changed += 1
            if not check:
                d.setdefault("unlocks", []).append({"type": "vocab", "ref": ref})
                f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def apply_body_edits(con, check: bool, problems: list[str]) -> int:
    """The one prose re-cut, written to the DB and to the authoring source or to neither."""
    changed = 0
    for lslug, (old, new) in BODY_EDITS.items():
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (lslug,)).fetchone()
        if not lr:
            problems.append(f"{lslug}: no such lesson")
            continue
        lid = lr[0]
        body = _lesson_body(con, lid)
        if new in body:
            pass  # already applied
        elif old not in body:
            problems.append(f"{lslug}: the body carries neither the old sentence nor the new one — "
                            f"it was edited by something else and this ruling must be re-derived")
            continue
        else:
            print(f"  {lslug}: body re-cut so どなた carries its own chip (db)")
            changed += 1
            if not check:
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND "
                            "entity_id=? AND field='body' AND locale='pt-BR'",
                            (body.replace(old, new), lid))

        f = SRC / f"{lslug.split(':', 1)[1]}.json"
        if not f.exists():
            problems.append(f"{lslug}: authoring source {f.name} missing")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        src_body = d.get("body") or ""
        if new in src_body:
            continue
        if old not in src_body:
            problems.append(f"{lslug}: authoring source carries neither sentence")
            continue
        print(f"  {lslug}: body re-cut (source)")
        changed += 1
        if not check:
            d["body"] = src_body.replace(old, new)
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def apply_practice(con, rows: list[dict], check: bool, problems: list[str]) -> int:
    """Author the four exercises the promoted unlocks require, in both layers.

    An unlock nobody asks about is the hole this unit is closing, not a new one to open:
    validate_practice_coverage.py freezes the count of unlocked items no exercise targets and fails
    when it grows, and promoting five records would have grown it by four. The exercise content is
    IN THE TABLE, so this function only places it — the row is the authored artifact and the gate
    replays it. The app renders exercises only from `<exercise ref=…/>` nodes, so the body gains
    that node too, appended after the lesson's last one.

    W11c: it also RE-ASSERTS the content of an exercise that already exists. It used to write the
    prompt, answer and explanation on creation only, which made "the table holds the content" true
    for exactly one run: the review found the ex:n5-conectando-01-6 explanation stating that 何
    reads なん before か (何か is なにか), and correcting it in the table would have changed nothing
    anywhere. Now a difference between the row and either layer is rewritten from the row, so the
    table is the source of truth on every run and the correction reaches the DB, the authoring
    source and — through the exporter — the published lesson.
    """
    sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
    from i18n_text import set_text

    changed = 0
    for r in rows:
        if r["kind"] != "practice":
            continue
        lslug, exslug = r["lesson"], r["exercise"]
        lr = con.execute("SELECT id FROM lesson WHERE slug=?", (lslug,)).fetchone()
        if not lr:
            problems.append(f"{lslug}: no such lesson")
            continue
        lid = lr[0]
        have = con.execute("SELECT id FROM exercise WHERE slug=?", (exslug,)).fetchone()
        if not have:
            nxt = con.execute("SELECT COALESCE(MAX(ord), -1) + 1 FROM exercise WHERE lesson_id=?",
                              (lid,)).fetchone()[0]
            print(f"  {lslug}: +exercise {exslug} ({r['type']}, practises {r['new']}) (db)")
            changed += 1
            if not check:
                con.execute("INSERT INTO exercise (slug, lesson_id, ord, type, answer, needs_review) "
                            "VALUES (?,?,?,?,?,1)",
                            (exslug, lid, nxt, r["type"], json.dumps(r["answer"], ensure_ascii=False)))
                eid = con.execute("SELECT id FROM exercise WHERE slug=?", (exslug,)).fetchone()[0]
                set_text(con, "exercise", eid, "prompt", r["prompt"], layer="C")
                set_text(con, "exercise", eid, "explanation", r["explanation"], layer="C")
        else:
            # Already there — the table still owns what it says. Re-assert type, answer, prompt and
            # explanation so a correction in the row lands instead of being silently ignored.
            eid = have[0]
            cur_type, cur_ans = con.execute(
                "SELECT type, answer FROM exercise WHERE id=?", (eid,)).fetchone()
            want_ans = json.dumps(r["answer"], ensure_ascii=False)
            if cur_type != r["type"] or (json.loads(cur_ans) if cur_ans else None) != r["answer"]:
                print(f"  {lslug}: {exslug} type/answer rewritten from the ruling table (db)")
                changed += 1
                if not check:
                    con.execute("UPDATE exercise SET type=?, answer=? WHERE id=?",
                                (r["type"], want_ans, eid))
            for field in ("prompt", "explanation"):
                got = con.execute(
                    "SELECT value FROM localized_text WHERE entity_type='exercise' AND entity_id=? "
                    "AND field=? AND locale='pt-BR'", (eid, field)).fetchone()
                if (got[0] if got else None) != r[field]:
                    print(f"  {lslug}: {exslug} {field} rewritten from the ruling table (db)")
                    changed += 1
                    if not check:
                        set_text(con, "exercise", eid, field, r[field], layer="C")

        node = f'<exercise ref="{exslug}"/>'
        body = _lesson_body(con, lid)
        if node not in body:
            anchor = body.rfind("<exercise ref=")
            end = body.find("/>", anchor)
            if anchor < 0 or end < 0:
                problems.append(f"{lslug}: body has no <exercise ref=…/> node to append after")
                continue
            print(f"  {lslug}: +<exercise ref=\"{exslug}\"/> in the practice block (db)")
            changed += 1
            if not check:
                cut = end + 2
                con.execute("UPDATE localized_text SET value=? WHERE entity_type='lesson' AND "
                            "entity_id=? AND field='body' AND locale='pt-BR'",
                            (body[:cut] + "\n" + node + body[cut:], lid))

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
                "slug": exslug, "type": r["type"], "prompt": r["prompt"], "answer": r["answer"],
                "explanation": r["explanation"], "sentence_refs": [], "item_refs": []})
        else:
            for field in ("type", "prompt", "answer", "explanation"):
                if src_ex.get(field) != r[field]:
                    print(f"  {lslug}: {exslug} {field} rewritten from the ruling table (source)")
                    changed += 1
                    dirty = True
                    src_ex[field] = r[field]
        src_body = d.get("body") or ""
        if node not in src_body:
            anchor = src_body.rfind("<exercise ref=")
            end = src_body.find("/>", anchor)
            if anchor < 0 or end < 0:
                problems.append(f"{lslug}: authoring source body has no <exercise ref=…/> node")
                continue
            print(f"  {lslug}: +<exercise ref=\"{exslug}\"/> (source)")
            changed += 1
            dirty = True
            cut = end + 2
            d["body"] = src_body[:cut] + "\n" + node + src_body[cut:]
        if dirty and not check:
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def prune_exemptions(doc_table: dict, rows: list[dict], check: bool, problems: list[str]) -> int:
    """Drop the promoted records from the two exemption files, restate the reasons of the ones that
    stay, and assert the holds are still there.

    The reasons matter as much as the membership. Every one of the nine coverage entries pointed the
    reader at course/vocab_disambiguation_review.json for a decision — and W11a empties that file, so
    leaving the prose alone would have left four exemptions citing an empty queue as the reason they
    exist. The replacement text lives in the ruling table, beside the decision it describes, and is
    rewritten from there on every run so the two cannot drift.
    """
    promoted = {r["new"] for r in rows if r["kind"] == "unlock"}
    held = {r["new"]: r for r in rows if r["kind"] == "hold"}
    # W11c: a `ref` ruling with verdict `change` means the body stops rendering `old` in that lesson,
    # so a gating exemption written for (lesson, old) is stale the moment the ruling lands. Dropping
    # it here rather than by hand is the same rule as the reasons below: the table decides, the file
    # follows. 様 @ les:n4-passiva-02 is the case that needed it — the chip moves to vocab:1545790,
    # which the course unlocks a topic earlier, so there is nothing left to hold open.
    repointed = {(r["lesson"], r["old"]) for r in rows
                 if r["kind"] == "ref" and r.get("verdict") == "change"}
    headers = doc_table.get("exemption_headers", {})
    greasons = {(g["lesson"], g["ref"]): g["reason"] for g in doc_table.get("gating_reasons", [])}
    changed = 0

    # W11c: a manifest replay redirects OUT to a work root seeded with the lesson authoring layer
    # only (scripts/rebuild_index.py), so course/ is not there. The manifest note already said this
    # part is "a no-op re-proof on a rebuild" — the code did not, and crashed with FileNotFoundError,
    # which is where the full replay died after the merge steps were fixed. These two files are a
    # repo-side edit, not an export, so there is nothing to write in a work root.
    if not COVERAGE_EXEMPT.is_file() or not GATING_EXEMPT.is_file():
        print(f"  [rebuild] {COVERAGE_EXEMPT.parent} carries no exemption files — they are a "
              f"repo-side edit, not an export, so the prune is skipped for this run")
        return 0

    doc = json.loads(COVERAGE_EXEMPT.read_text(encoding="utf-8"))
    keep = [e for e in doc["vocab"] if e["id"] not in promoted]
    still = {e["id"] for e in keep}
    for slug in sorted(held):
        if slug not in still:
            problems.append(f"coverage_exemptions.json: hold row {slug} is not in the file")
    for e in keep:
        row = held.get(e["id"])
        if row and row.get("exemption_reason"):
            e["reason"] = row["exemption_reason"]
    new_doc = {**doc, "why": headers.get("coverage", doc.get("why")), "vocab": keep}
    if new_doc != doc:
        print(f"  coverage_exemptions.json: {len(doc['vocab'])} -> {len(keep)} vocab exemptions "
              f"(+ reasons restated from the ruling table)")
        changed += 1
        if not check:
            COVERAGE_EXEMPT.write_text(json.dumps(new_doc, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")

    gdoc = json.loads(GATING_EXEMPT.read_text(encoding="utf-8"))
    gkeep = [dict(e) for e in gdoc["item_refs"]
             if e["ref"] not in promoted and (e.get("lesson"), e.get("ref")) not in repointed]
    for e in gkeep:
        reason = greasons.get((e.get("lesson"), e.get("ref")))
        if reason:
            e["reason"] = reason
    new_gdoc = {**gdoc, "why": headers.get("gating", gdoc.get("why")), "item_refs": gkeep}
    if new_gdoc != gdoc:
        print(f"  gating_exemptions.json: {len(gdoc['item_refs'])} -> {len(gkeep)} body-ref exemptions "
              f"(+ reasons restated from the ruling table)")
        changed += 1
        if not check:
            GATING_EXEMPT.write_text(json.dumps(new_gdoc, ensure_ascii=False, indent=2) + "\n",
                                     encoding="utf-8")
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

    nref = verify_refs(con, rows, problems)
    changed = apply_unlocks(con, rows, args.check, problems)
    changed += apply_body_edits(con, args.check, problems)
    changed += apply_practice(con, rows, args.check, problems)
    changed += prune_exemptions(table, rows, args.check, problems)

    if changed and not args.check and not problems:
        # lesson.cumulative_known_set is a stored derivation of lesson_unlocks. The exporter
        # recomputes it (export_course._cumulative), but scripts/ingest/build_readings.py and
        # mine_n3_targets.py read the COLUMN, so an incremental apply that left it stale would make
        # a manifest rebuild disagree with this machine. Recomputed with the ingest's own routine so
        # there is one definition of "cumulative".
        from load_lessons import recompute_cumulative
        print(f"  recomputed cumulative_known_set for {recompute_cumulative(con)} lessons (db)")

    if not args.check and not problems:
        con.commit()
    con.close()

    verb = "would change" if args.check else "changed"
    print(f"\nverified {nref} disambiguation rulings against the live resolver; {verb} {changed} thing(s)")
    for p in problems:
        print(f"  ! {p}")
    if problems:
        print("\nNOTHING WAS COMMITTED — a ruling that does not reproduce is not applied.")
        return 2
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
