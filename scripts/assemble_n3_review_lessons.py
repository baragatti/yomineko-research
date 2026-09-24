#!/usr/bin/env python3
"""P5-n3-review, step 1: fold the authored N3 review lessons and their verdict into ONE tracked table.

INPUTS (research/derived/pending/; the verdict stays there as the audit trail)
  n3_review_lessons.json          W22 §3 authoring: les:n3-revisao-01 rewritten, -02 and -03 created,
                                  the top:n3-revisao objective. Layer C, needs_review.
  n3_review_topic.verdict.json    the independent verifier, keyed by stable identity (top: / les: /
                                  ex: slug) -> {ok, problem?, corrected?}.

MERGE RULES (none of them a judgement made here)
  * a lesson or exercise lands only under a verdict: ok -> as authored; ok false -> the verifier's
    `corrected` value. A key with no verdict, or a rejected row (ok false, nothing corrected), is
    listed in `rejected` and never applied.
  * a lesson's corrected `body` is the full body. It is re-derived here from the authored body plus
    the verdict's `body_edits` (each `find` must match exactly once) and must equal the verifier's
    body byte for byte, or the assembler refuses.
  * a corrected exercise replaces the authored one whole (same slug).
  * `needs` is NOT carried: it is derived (scripts/build_needs_table.py, review-chain rule) and owned
    by research/derived/repairs/lesson_needs.json.
  * les:n3-revisao-01 keeps its 4 vocab unlocks (the brief's keep_existing_unlocks; owner decision
    still open). They are carried in the form the authoring source already writes them (headword
    refs, like 2,897 of the 2,951 vocab unlocks) after checking they name the same 4 records as the
    authored `vocab:<jmdict>` refs, so the unlock ledger does not churn on notation.
  * the three W20 vocab practice drills that already sit on les:n3-revisao-01 used ids -5/-6/-7, and
    the authored exercises take -1..-6. The verifier flagged the collision as an apply blocker. The
    drills keep their content and move to -7/-8/-9 (`practice_id_remap`, written into
    research/derived/repairs/practice_vocab_exercises.json by `retarget_tables()` below).

OUTPUT: research/derived/repairs/n3_review_lessons.json. The pending lessons file is removed once the
table is written (git history keeps it). Deterministic.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "research" / "derived" / "pending"
SRC = PENDING / "n3_review_lessons.json"
VERDICT = PENDING / "n3_review_topic.verdict.json"
OUT = ROOT / "research" / "derived" / "repairs" / "n3_review_lessons.json"
LESSONS = ROOT / "research" / "derived" / "lessons"
DB = ROOT / "db" / "corpus.sqlite"

LESSON_KEYS = ("slug", "topic", "order", "schema_version", "title", "description", "objectives",
               "unlocks", "feature_unlocks", "sentence_refs", "body", "exercises", "reading_refs")
PRACTICE_REMAP = [
    {"lesson": "les:n3-revisao-01", "from": "ex:n3-revisao-01-5", "to": "ex:n3-revisao-01-7"},
    {"lesson": "les:n3-revisao-01", "from": "ex:n3-revisao-01-6", "to": "ex:n3-revisao-01-8"},
    {"lesson": "les:n3-revisao-01", "from": "ex:n3-revisao-01-7", "to": "ex:n3-revisao-01-9"},
]


def apply_edits(body: str, edits: list[dict], slug: str) -> str:
    for e in edits:
        n = body.count(e["find"])
        if n != 1:
            raise SystemExit(f"{slug}: body_edit find matches {n} times: {e['find'][:80]!r}")
        body = body.replace(e["find"], e["replace"])
    return body


def retarget_tables() -> None:
    """The two tracked tables whose rows name what this unit moves. Idempotent.

    * practice_vocab_exercises.json: the 3 drills on les:n3-revisao-01 are renumbered in the rows
      themselves (not via `apply_id_remap`, which scripts/derive_item_refs.py does not read: it keys
      rule 0 on the row's own id, so a remap would hand the drills' vocab targets to the authored
      -5/-6). Each renumber is recorded in `id_fixes`, the table's own ledger for that.
    * w22_n3_dead_end.json rows[0]: feat:jlpt-sim-n3 moves to the row's `target_when_authored`.
    """
    pv = ROOT / "research" / "derived" / "repairs" / "practice_vocab_exercises.json"
    doc = json.loads(pv.read_text(encoding="utf-8"))
    n = 0
    done = {(f["lesson"], f["from"]) for f in doc["id_fixes"]}
    # resolve every row against the ORIGINAL ids first: -7 is both a source and a target here
    hits = [(m, r) for m in PRACTICE_REMAP if (m["lesson"], m["from"]) not in done
            for r in doc["rows"] if r["lesson"] == m["lesson"] and r["exercise"]["id"] == m["from"]]
    for m, r in hits:
        r["exercise"]["id"] = m["to"]
        doc["id_fixes"].append({
            "lesson": m["lesson"], "from": m["from"], "to": m["to"],
            "reason": ("P5-n3-review: the rewritten review lesson's authored exercises take "
                       "-1..-6, so the lesson's three vocab drills continue its numbering "
                       "after them (research/derived/repairs/n3_review_lessons.json)")})
        n += 1
    if n:
        pv.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    w22 = ROOT / "research" / "derived" / "repairs" / "w22_n3_dead_end.json"
    wd = json.loads(w22.read_text(encoding="utf-8"))
    row = wd["rows"][0]
    moved = 0
    if row["ref"] == "feat:jlpt-sim-n3" and row["lesson"] != row["target_when_authored"]:
        row["moved_from"] = row["lesson"]
        row["lesson"] = row["target_when_authored"]
        row["course_index"] = row["course_index"] + 2
        row["moved_by"] = ("P5-n3-review: les:n3-revisao-02/-03 authored, so the last lesson of "
                           "top:n3-revisao is -03 (rule R1, as the n5/n4 siblings)")
        wd["features"]["applied_to_today"] = row["lesson"]
        moved = 1
        w22.write_text(json.dumps(wd, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # w24_capabilities.json: two can-do rows quote objectives of the OLD les:n3-revisao-01, which the
    # rewrite replaced. build_capabilities.py refuses a quote the lesson no longer carries, so the
    # quotes are re-pointed the way C5-W24 / C12-W08b did it (a dated `rederived_*` block, no prose
    # authored): a quote whose meaning an objective of the new lesson carries is replaced by that
    # objective verbatim, a quote with no counterpart is dropped.
    wp = ROOT / "research" / "derived" / "repairs" / "w24_capabilities.json"
    wc = json.loads(wp.read_text(encoding="utf-8"))
    old_conn = "Reconhecer e escolher o conector ou padrão N3 certo para cada intenção"
    old_self = "Autoavaliar o domínio dos blocos de gramática do N3"
    new_conn = "Escolher o conector certo para somar, contrastar, reformular, mudar de assunto ou justificar"
    want = {
        "cap:vocab:n3-revisao": [],
        "cap:exam-readiness-n3": [{"lesson": "les:n3-revisao-01", "objective": new_conn}],
    }
    requoted = 0
    for r in wc["rows"]:
        if r["id"] in want and r["can_do_derived_from"] != want[r["id"]]:
            if any(q["objective"] not in (old_conn, old_self) for q in r["can_do_derived_from"]):
                raise SystemExit(f"{r['id']}: quotes are not the ones this re-point expects")
            r["can_do_derived_from"] = want[r["id"]]
            requoted += 1
    if requoted:
        wc["rederived_p5_n3_review"] = {
            "date": "2026-09-23", "by": "P5-n3-review",
            "why": ("les:n3-revisao-01 was rewritten to review block 1 (conectores, tempo, perspectiva, "
                    "causa), so its two old objectives are gone. cap:exam-readiness-n3: the quote '"
                    + old_conn + "' is replaced by the new -01 objective '" + new_conn + "'; the quote '"
                    + old_self + "' is dropped (no objective of the three review lessons is about "
                    "self-assessment; the can_do text is unchanged and its second half is now "
                    "unquoted, owner review). cap:vocab:n3-revisao: its one quote is dropped, left "
                    "with none like cap:i-adjectives: no objective of the new -01 is about the 4 "
                    "vocab it unlocks (the open owner decision on those unlocks).")}
        wp.write_text(json.dumps(wc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"retarget: {n} practice drill id(s) renumbered, {moved} feature row moved, "
          f"{requoted} capability row(s) re-quoted")


def main() -> int:
    retarget_tables()
    if not SRC.exists():
        if OUT.exists():
            print(f"{SRC.name} already folded into {OUT.relative_to(ROOT)}; nothing to do")
            return 0
        raise SystemExit(f"{SRC} missing")
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    ver = json.loads(VERDICT.read_text(encoding="utf-8"))["verdicts"]

    counts = {"ok": 0, "corrected": 0, "rejected": 0}
    rejected: list[dict] = []
    corrections: list[dict] = []

    def verdict(key: str) -> dict | None:
        v = ver.get(key)
        if v is None:
            rejected.append({"key": key, "why": "no verdict"})
            counts["rejected"] += 1
            return None
        if v.get("ok"):
            counts["ok"] += 1
            return v
        if not v.get("corrected"):
            rejected.append({"key": key, "why": v.get("problem", "rejected")})
            counts["rejected"] += 1
            return None
        counts["corrected"] += 1
        corrections.append({"key": key, "problem": v.get("problem", "")})
        return v

    tv = verdict("top:n3-revisao")
    topic = None if tv is None else {"id": doc["topic_patch"]["id"],
                                     "objectives": doc["topic_patch"]["objectives"]}

    con = sqlite3.connect(DB)
    rows: list[dict] = []
    owner_open: list[str] = []
    per_lesson_sources = doc["sources"]["per_lesson"]
    for les in doc["lessons"]:
        slug = les["slug"]
        v = verdict(slug)
        if v is None:
            continue
        rec = {k: les[k] for k in LESSON_KEYS}
        meta = dict(per_lesson_sources.get(slug, {}))
        if not v.get("ok"):
            c = v["corrected"]
            body = apply_edits(les["body"], c.get("body_edits") or [], slug)
            if "body" in c and c["body"] != body:
                raise SystemExit(f"{slug}: verifier body != authored body + body_edits")
            rec["body"] = body
            if "sources.per_lesson.body_sentences" in c:
                meta["body_sentences"] = c["sources.per_lesson.body_sentences"]
            owner_open += [f"{slug}: {u}" for u in c.get("unresolved") or []]
        exs = []
        for ex in les["exercises"]:
            ev = verdict(ex["slug"])
            if ev is None:
                continue
            exs.append(ex if ev.get("ok") else ev["corrected"])
        rec["exercises"] = exs
        if slug == "les:n3-revisao-01":
            cur = json.loads((LESSONS / "n3-revisao-01.json").read_text(encoding="utf-8"))
            cur_v = [u for u in cur["unlocks"] if u["type"] == "vocab"]
            want = set()
            for u in rec["unlocks"]:
                hw = con.execute("SELECT headword FROM vocab WHERE slug=?", (u["ref"],)).fetchone()
                want.add(f"vocab:{hw[0]}" if hw else u["ref"])
            if want != {u["ref"] for u in cur_v}:
                raise SystemExit(f"{slug}: authored unlocks {sorted(want)} are not the source's "
                                 f"{[u['ref'] for u in cur_v]}")
            rec["unlocks"] = cur_v
            meta["unlocks_note"] = ("the 4 vocab unlocks are carried as the source already writes "
                                    "them; same records as " + ", ".join(u["ref"] for u in les["unlocks"]))
        rec["provenance"] = {"layer": "C", "created_by": "ai", "needs_review": True, **meta}
        rows.append(rec)
    con.close()

    table = {
        "what_this_is": (
            "The three N3 review lessons (top:n3-revisao) and the topic objective, as the verified "
            "table scripts/apply_n3_review_lessons.py writes into both layers (the authoring source "
            "research/derived/lessons/<slug>.json and the index). One row per lesson: every content "
            "field the apply owns. `needs` is derived and lives in lesson_needs.json; item_refs "
            "beyond each exercise's authored anchor are derived by derive_item_refs.py; the W20 "
            "vocab drills on -01 and the W14 sentence cards are placed by their own tables."),
        "unit": "P5-n3-review (APP_PLAN W22 §3)",
        "generated_by": "scripts/assemble_n3_review_lessons.py",
        "applied_by": "scripts/apply_n3_review_lessons.py",
        "inputs": {"authored": "research/derived/pending/n3_review_lessons.json (folded, removed)",
                   "verdict": "research/derived/pending/n3_review_topic.verdict.json (kept)"},
        "verdict_counts": counts,
        "corrections": corrections,
        "rejected": rejected,
        "topic": topic,
        "feature_move": {"ref": "feat:jlpt-sim-n3", "from": "les:n3-revisao-01",
                         "to": "les:n3-revisao-03",
                         "table_row": "research/derived/repairs/w22_n3_dead_end.json rows[0]"},
        "practice_id_remap": PRACTICE_REMAP,
        "owner_open": owner_open,
        "row_count": len(rows),
        "rows": rows,
    }
    OUT.write_text(json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    SRC.unlink()
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} lessons; verdicts {counts}; "
          f"rejected {len(rejected)}; owner_open {len(owner_open)}; removed {SRC.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
