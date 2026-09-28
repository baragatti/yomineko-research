#!/usr/bin/env python3
"""Q4: fold the verified small-residues table into the tables its three parts are applied from.

Input: `research/derived/repairs/small_residues/small_residues.json` (authored, Layer C) + its verdict
`research/derived/pending/small_residues.verdict.json` (41 checked: 33 ok, 8 corrected, 0 rejected).
Only verified rows are folded, and a corrected row takes the verifier's value (the row fields it
names, or the whole `exercise`). Outputs, each the input of an existing apply step:

  drills     -> research/derived/repairs/practice_grammar_residue.json, applied by
                `apply_practice_exercises.py --table` (the W20 row shape; the exercise carries its
                AUTHORED item_refs, which the applier writes with it)
  item_refs  -> rows of research/derived/repairs/item_refs.json (`derived_by: authored`, rule 0b of
                derive_item_refs.py, which reads them back from the authoring source), plus the one
                exemption in course/item_ref_exemptions.json (`derived_by: authored`, kept by the
                derivation). A row whose exercise already carries a DIFFERENT target on this tree is
                stale (the exercise was rewritten since) and is held, not forced.
  rc         -> one row of research/derived/reauthor/exam_authored/rc_questions_w18b.json (the W18b
                journal build_reading_comp_bank.py reads), and the reading box's pointer restored in
                research/derived/repairs/reading_comprehension.json (row amended, `amended.was_new`).

Idempotent: a second run changes nothing. Usage: assemble_small_residues.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
REPAIRS = ROOT / "research" / "derived" / "repairs"
SRC = REPAIRS / "small_residues" / "small_residues.json"
VERDICT = ROOT / "research" / "derived" / "pending" / "small_residues.verdict.json"
DRILLS = REPAIRS / "practice_grammar_residue.json"
ITEM_REFS = REPAIRS / "item_refs.json"
EXEMPT = ROOT / "course" / "item_ref_exemptions.json"
RC_JOURNAL = ROOT / "research" / "derived" / "reauthor" / "exam_authored" / "rc_questions_w18b.json"
RC_BOXES = REPAIRS / "reading_comprehension.json"
DRILL_KEYS = ("lesson", "targets", "exercise", "basis", "ai_generated", "jp_authored_here",
              "known_set_evidence", "residue_reason")


# Verified drills HELD because applying them would GROW validate_lesson_gating C5 (forward references,
# shrink-only): the bank sentence each one cites is linked, token by token, to a record a LATER lesson
# unlocks, and derive_needs reads cited sentences as a reference channel. Measured on the tree of
# 2026-09-27 (same-level 10 -> 12, cross-level 146 -> 148 with them). Two of the four links look wrong
# rather than early (し inside どうして, いけない as the N3 行けない) and belong to the token-link unit.
HOLD = {
    "ex:n5-perguntas-04-16": "cites sent:tatoeba-201561, whose し (inside どうして) is linked to 為る "
                             "vocab:1157170, unlocked later in les:n5-verbos-02 (same-level forward use)",
    "ex:n5-particulas-lugar-07-9": "cites sent:gen-382544683343, whose もらい is linked to 貰う "
                                   "vocab:1535910, unlocked in les:n4-volitivo-05 (cross-level forward use)",
    "ex:n5-te-form-05-13": "cites sent:tatoeba-184859, whose いけない is linked to 行けない vocab:1000730, "
                           "unlocked in les:n3-conectores-04 (cross-level forward use)",
    "ex:n4-condicionais-08-10": "cites sent:gen-b249a5f48dc6, whose いか is linked to 以下 vocab:1155060, "
                                "unlocked later in les:n4-volitivo-04 (same-level forward use)",
}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def verified(verdicts: dict, key: str, row: dict) -> dict | None:
    v = verdicts.get(key)
    if v is None:
        return None                                   # no verdict: excluded, never passed
    if v.get("ok"):
        return row
    if v.get("corrected"):
        return {**row, **v["corrected"]}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    src, verdicts = load(SRC), load(VERDICT)["verdicts"]
    held: list[str] = []
    writes: dict[Path, tuple[object, int | None, str]] = {}

    # ---- drills ------------------------------------------------------------------------------
    rows, held_rows = [], []
    for d in src["drills"]:
        f = verified(verdicts, d["exercise"]["id"], d)
        if f is None:
            held.append(f"drill {d['exercise']['id']}: not verified")
            continue
        if d["exercise"]["id"] in HOLD:
            held_rows.append({"exercise": d["exercise"]["id"], "lesson": d["lesson"],
                              "targets": d["targets"], "why": HOLD[d["exercise"]["id"]]})
            held.append(f"drill {d['exercise']['id']}: {HOLD[d['exercise']['id']]}")
            continue
        row = {k: f[k] for k in DRILL_KEYS if k in f}
        row["verdict"] = "ok" if verdicts[d["exercise"]["id"]].get("ok") else "corrected"
        row["why"] = (f"Q4 small residue ({f['residue_reason']}): {f['basis']}, authored + verified "
                      f"({row['verdict']})")
        rows.append(row)
    doc = {"why": "The 19 (lesson, grammar) pairs the W20 generator left without a drill "
                  "(research/derived/pending/practice_vocab_residue.json), one authored exercise each "
                  "(15 applied, 4 held below), "
                  "verified by an independent verifier (research/derived/pending/small_residues.verdict"
                  ".json); the verifier's corrected exercise where the verdict is not ok.",
           "definition": "One row per exercise: {lesson, targets, exercise, why, ...}, the W20 row shape. "
                         "`exercise` is a lesson.schema.json exercise that ALSO carries its authored "
                         "item_refs (apply_practice_exercises.py writes them with the exercise). Ids "
                         "continue each lesson's numbering on the tree of 2026-09-27 (checked free).",
           "generated_by": "scripts/assemble_small_residues.py from research/derived/repairs/small_residues/small_residues.json",
           "applied_by": "scripts/apply_practice_exercises.py --table research/derived/repairs/practice_grammar_residue.json",
           "provenance": {"layer": "C", "source": "authored:q4-small-residues", "needs_review": True,
                          "note": "Per-row ai_generated: false where the Japanese is a real bank sentence."},
           "held_why": "Verified, not applied: each would grow validate_lesson_gating C5 (forward "
                       "references, shrink-only) through the token links of the sentence it cites.",
           "held": held_rows,
           "row_count": len(rows), "rows": rows}
    writes[DRILLS] = (doc, 1, "\n")

    # ---- item_refs -----------------------------------------------------------------------------
    ir = load(ITEM_REFS)
    by_ex = {r["exercise"]: r for r in ir["rows"]}
    ex_doc = load(EXEMPT)
    exempt_ids = {e["id"] for e in ex_doc["exercises"]}
    for r in src["item_refs"]:
        f = verified(verdicts, r["id"], r)
        if f is None:
            held.append(f"item_refs {r['id']}: not verified")
            continue
        cur = by_ex.get(r["id"])
        if f["disposition"] == "exempt":
            if cur:
                held.append(f"item_refs {r['id']}: exempt row, but the exercise carries a target now")
            elif r["id"] not in exempt_ids:
                ex_doc["exercises"].append({**f["exemption"], "derived_by": "authored"})
            continue
        if cur and cur["item_refs"] != f["item_refs"]:
            held.append(f"item_refs {r['id']}: stale, the exercise carries {[e['ref'] for e in cur['item_refs']]} "
                        f"on this tree (rewritten since the residue was listed)")
            continue
        if not cur:
            ir["rows"].append({"exercise": r["id"], "lesson": r["lesson"], "item_refs": f["item_refs"]})
    for d in rows:
        eid = d["exercise"]["id"]
        want = {"exercise": eid, "lesson": d["lesson"], "item_refs": d["exercise"]["item_refs"]}
        if by_ex.get(eid) not in (None, want):
            held.append(f"drill item_refs {eid}: the table already carries a different row")
        elif eid not in by_ex:
            ir["rows"].append(want)
    ir["rows"] = [x for x in ir["rows"] if x["exercise"] not in HOLD]
    ir["rows"].sort(key=lambda x: x["exercise"])
    ir["row_count"] = len(ir["rows"])
    writes[ITEM_REFS] = (ir, 1, "\n")
    writes[EXEMPT] = (ex_doc, 2, "\n")

    # ---- rc ------------------------------------------------------------------------------------
    rcj = load(RC_JOURNAL)
    for q in src["rc"]:
        key = f"{q['passage']}|{q['question_index']}"
        f = verified(verdicts, key, q)
        if f is None:
            held.append(f"rc {key}: not verified")
            continue
        if not any(x["passage"] == q["passage"] for x in rcj["rows"]):
            rcj["rows"].append(f)
            rcj["counts"]["final"] = len(rcj["rows"])
            rcj["counts"]["q4_authored"] = rcj["counts"].get("q4_authored", 0) + 1
        rcj["q4"] = ("Q4-listening-residues: the one passage W18b left without a question "
                     f"({q['passage']}) gets its question from research/derived/repairs/small_residues/"
                     "small_residues.json, verifier-corrected (research/derived/pending/"
                     "small_residues.verdict.json).")
        boxes = load(RC_BOXES)
        item = f"rc:{q['passage'].split(':', 1)[1].split('-', 1)[0]}:{q['passage'].split(':', 1)[1]}"
        for b in boxes["rows"]:
            want = {"item": item, "about_current_text": True}
            if b["slug"] == q["passage"] and b["new"] != want:
                b["amended"] = {"by": "Q4-listening-residues", "was_new": b["new"],
                                "why": "the box's question is back in the rc bank (small residues rc row)"}
                b["new"] = want
        writes[RC_BOXES] = (boxes, 1, "\n")
    writes[RC_JOURNAL] = (rcj, 1, "")

    for p, (d, ind, tail) in writes.items():
        text = json.dumps(d, ensure_ascii=False, indent=ind) + tail
        same = p.exists() and p.read_text(encoding="utf-8") == text
        print(f"{'=' if same else '~'} {p.relative_to(ROOT)}")
        if not args.check and not same:
            p.write_text(text, encoding="utf-8")
    print(f"drills {len(rows)}; item_refs rows {ir['row_count']}; held {len(held)}")
    for h in held:
        print(f"  HELD {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
