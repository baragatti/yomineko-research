#!/usr/bin/env python3
"""Turn the derived prerequisite DAG into the tracked table `apply_lesson_needs.py` writes.

WHY A SECOND SCRIPT. `derive_needs.py` answers one question — which lesson does lesson L depend
on, and why — and it answers it from references alone. Two groups of lessons are invisible to that
question and always will be:

  * the 41 pre-N5 lessons. The kana strand references nothing but its own kana family, so every one
    of them derives as a root. They are not independent: hiragana-07 is unteachable before
    hiragana-06. There is no reference to harvest, so the edge comes from a RULE (below), not from
    an author's judgement.
  * 11 review / kanji-exame lessons sitting at positions 119-124 and 216-220. Each one re-drills
    what it teaches itself, so it too derives as a root — a lesson with no ancestors 216 lessons
    into the course, which is a placement problem, not a prerequisite one (see the report).

Everything else is copied from the derivation unchanged, so this file adds edges and never invents
one: `validate_lesson_gating.py` check C4 re-runs `derive_needs.build()` on the current tree and
fails if the stored edges are not exactly its output plus these two rule sets.

THE TWO RULES, stated so they can be checked rather than trusted
---------------------------------------------------------------
  kana-chain    every pre-N5 lesson needs the pre-N5 lesson immediately before it in course order.
                Inside a strand that IS "the previous lesson of the strand" (hiragana-08 -> -07);
                at the strand boundary it is "the first katakana lesson needs the last hiragana
                lesson" (katakana-01 -> hiragana-15), because the strands run consecutively. The
                course opener, pre-n5-orientacao-01, is the one lesson with nothing before it.
  review-chain  each of the 11 deep roots needs the lesson immediately before it in course order,
                which is the last lesson of the block it reviews (n5-revisao-01 -> n5-conectando-07)
                or the previous lesson of its own review sequence (n5-revisao-02 -> n5-revisao-01).

THE NOTE IS LEARNER-FACING. The derivation's own note is bookkeeping — "introduces vocab:1241450;
seen via body-reading" — and this table is rendered in a "antes desta lição" box. Each note is
therefore produced by a FIXED pt-BR template per reason class (never free prose): the driving refs
are resolved to what a learner reads (a kanji character, a vocabulary headword, a grammar pattern)
and dropped into one of a handful of sentences. The mapping is in `pt_note()` and is total.

Deterministic: re-running rewrites the same bytes. Writes nothing but the table.
Usage: build_needs_table.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import derive_needs  # noqa: E402

TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_needs.json"
NOTE_RX = re.compile(r"^introduces (.+?)(?: \(\+\d+ more\))?; seen via (.+)$")

# --- the fixed pt-BR templates -------------------------------------------------------------
KANA_SAME = ("Vem logo antes na mesma sequência do silabário; esta lição continua "
             "de onde ela parou.")
KANA_CROSS = ("Fecha o hiragana. O katakana só começa depois que todo o hiragana está aprendido.")
PRE_N5_SEQ = ("É a lição imediatamente anterior da trilha inicial; esta lição continua "
              "de onde ela parou.")
REVIEW_BLOCK = "É a última lição do bloco que esta revisão cobre."
REVIEW_SAME = ("Vem logo antes nesta mesma sequência de revisão; esta lição continua "
               "de onde ela parou.")

KIND_WORD = {
    "kanji": ("o kanji", "os kanji"),
    "vocab": ("a palavra", "as palavras"),
    "gram": ("o ponto de gramática", "os pontos de gramática"),
}
KIND_ORDER = ("kanji", "vocab", "gram")


def join_pt(items: list[str]) -> str:
    """pt-BR list: 'a', 'a e b', 'a, b e c'."""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " e " + items[-1]


def labels(root: Path) -> dict[str, str]:
    """ref -> what a learner reads. Layer A for kanji and vocab, the grammar point's own pattern
    for grammar (its `label` is a pt-BR sentence and is far too long for a one-line note)."""
    out: dict[str, str] = {}
    for f in sorted((root / "corpus" / "kanji").glob("*.json")):
        for k in json.loads(f.read_text(encoding="utf-8")):
            out[f"kanji:{k['character']}"] = k["character"]
    for f in sorted((root / "corpus" / "vocab").glob("*.json")):
        for v in json.loads(f.read_text(encoding="utf-8")):
            # the kana rides along whenever the headword is written in kanji: the reader of a
            # "antes desta lição" box is by definition someone who has not met that lesson yet.
            hw, kana = v["headword"], (v.get("kana") or "")
            out[v["slug"]] = f"{hw} ({kana})" if kana and kana != hw else hw
    for f in sorted((root / "corpus" / "grammar").glob("*.json")):
        for g in json.loads(f.read_text(encoding="utf-8")):
            lab = (g.get("structure_pattern") or "").strip()
            if not lab:
                lab = ((g.get("label") or {}).get("pt-BR") or g.get("key") or "").strip()
            out[g["slug"]] = lab or g["slug"]
    return out


def pt_note(refs: list[str], lab: dict[str, str]) -> str:
    """The derivation's reason, rendered by template. One sentence, no free prose."""
    groups = []
    total = 0
    for kind in KIND_ORDER:
        got = [lab.get(r, r.split(":", 1)[-1]) for r in refs if r.split(":", 1)[0] == kind]
        if not got:
            continue
        total += len(got)
        sing, plur = KIND_WORD[kind]
        groups.append(f"{sing if len(got) == 1 else plur} {join_pt(got)}")
    if not groups:                                        # unreachable with today's namespaces
        return "Ensina conteúdo que esta lição já usa."
    tail = "que aparece nesta lição" if total == 1 else "que aparecem nesta lição"
    if len(groups) > 1 and any(" e " in g for g in groups):
        # "as palavras A e B e o ponto de gramática C" reads as one four-item list; the comma
        # before the last "e" is what separates the groups.
        phrase = ", ".join(groups[:-1]) + ", e " + groups[-1]
    else:
        phrase = join_pt(groups)
    return f"Apresenta {phrase}, {tail}."


def build(root: Path) -> dict:
    payload, _ = derive_needs.build(root)
    lessons = payload["lessons"]
    order = [x["id"] for x in lessons]
    pos = {lid: i for i, lid in enumerate(order)}
    by_id = {x["id"]: x for x in lessons}
    lab = labels(root)

    # topic per lesson, straight off the export (the derivation carries level, not topic)
    topic: dict[str, str] = {}
    for f in sorted((root / "course").rglob("lesson-*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        topic[d["id"]] = d.get("topic", "")

    rows: list[dict] = []
    for x in lessons:
        for n in x["needs"]:
            m = NOTE_RX.match(n["note"] or "")
            refs = [r.strip() for r in m.group(1).split(",")] if m else []
            chan = m.group(2) if m else ""
            rows.append({"lesson": x["id"], "ref": n["ref"], "origin": "derived",
                         "note": pt_note(refs, lab), "driving_refs": refs, "channels": chan})

    # --- rule 1: the pre-N5 chain ----------------------------------------------------------
    pre = [x["id"] for x in lessons if x["level"] == "pre-n5"]
    for i, lid in enumerate(pre):
        if i == 0:
            continue                                       # the course opener has nothing before it
        prev = pre[i - 1]
        same_topic = bool(topic.get(lid)) and topic.get(lid) == topic.get(prev)
        kana_strand = ("hiragana" in lid or "katakana" in lid)
        if same_topic and kana_strand:
            note = KANA_SAME
        elif "katakana" in lid and "hiragana" in prev:
            note = KANA_CROSS
        else:
            note = PRE_N5_SEQ
        rows.append({"lesson": lid, "ref": prev, "origin": "kana-chain", "note": note,
                     "driving_refs": [], "channels": ""})

    # --- rule 2: the 11 deep review / kanji-exame roots -------------------------------------
    deep = [x["id"] for x in lessons
            if not x["needs"] and x["position"] > 100 and x["level"] != "pre-n5"]
    for lid in deep:
        prev = order[pos[lid] - 1]
        note = REVIEW_SAME if topic.get(lid) == topic.get(prev) else REVIEW_BLOCK
        rows.append({"lesson": lid, "ref": prev, "origin": "review-chain", "note": note,
                     "driving_refs": [], "channels": ""})

    # every row must point strictly backwards, or the gate it feeds would fail on our own table
    bad = [r for r in rows if pos.get(r["ref"], 10 ** 9) >= pos.get(r["lesson"], -1)]
    if bad:
        raise SystemExit(f"{len(bad)} row(s) do not point strictly backwards: {bad[:3]}")

    rows.sort(key=lambda r: (pos[r["lesson"]], pos[r["ref"]]))
    roots = sorted(l for l in order if not any(r["lesson"] == l for r in rows))
    return {
        "generated_by": "scripts/build_needs_table.py",
        "what_this_is": (
            "Every `needs[]` entry the courseware carries, as {lesson, ref, origin, note}. "
            "`origin` derived = copied from scripts/derive_needs.py on the current tree; "
            "kana-chain / review-chain = added by the two rules stated in this script's docstring, "
            "because those lessons reference nothing a derivation could see. `note` is learner-"
            "facing pt-BR produced by a fixed template per reason class, never free prose."),
        "applied_by": "scripts/apply_lesson_needs.py",
        "counts": {"rows": len(rows),
                   "derived": sum(1 for r in rows if r["origin"] == "derived"),
                   "kana_chain": sum(1 for r in rows if r["origin"] == "kana-chain"),
                   "review_chain": sum(1 for r in rows if r["origin"] == "review-chain"),
                   "lessons_with_needs": len({r["lesson"] for r in rows}),
                   "roots": len(roots)},
        "roots": roots,
        "row_count": len(rows),
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare with the tracked table; write nothing")
    args = ap.parse_args()
    doc = build(ROOT)
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    same = TABLE.exists() and TABLE.read_text(encoding="utf-8") == text
    print(f"{doc['counts']}")
    if args.check:
        print("table is current" if same else "TABLE IS STALE — re-run without --check")
        return 0 if same else 1
    if not same:
        TABLE.write_text(text, encoding="utf-8")
    print(f"wrote {TABLE.relative_to(ROOT)}" if not same else "table unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
