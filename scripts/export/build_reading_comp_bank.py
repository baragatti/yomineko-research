#!/usr/bin/env python3
"""Assemble the reading-comprehension bank (読解) — DERIVED FROM THE PASSAGE, not merely beside it.

WHAT WAS WRONG (W16)
--------------------
This builder never read a passage. It took the authored 内容一致 items, checked that the `read:`
slug RESOLVED, checked the shape of the question and the options, and shipped. Nothing tied the
question to the text the learner is shown: an item could ask about a passage that had since been
rewritten, print a kanji the gating lesson has not taught, or offer three distractors the learner
cannot read, and every guard here would still pass it.

W15 made that concrete. All 286 boxes now hold a different passage from the one these questions were
written against (the old boxes were concatenations of unrelated bank sentences), so "the slug
resolves" is exactly as true as it was and exactly as meaningless.

WHAT THE GUARDS ARE NOW
-----------------------
Every item is checked AGAINST ITS PASSAGE and against the passage's gating lesson:

  P1  ABOUT THE PASSAGE. At least one content word of the question occurs in the passage. A
      question with no lexical footing in the text it is printed under is not a question about it.
  P2  LEVEL-GATED. Every kanji in the question, the correct answer and each distractor is in the
      gating lesson's `cumulative_known_set` — the same rule W03 measured and W17 makes the exam
      rule. A learner who cannot read an option cannot choose it.
  P3  DISTRACTORS FROM THE PASSAGE'S OWN KNOWN SET. Every content word of every option resolves,
      through `scripts/ingest/known_set.py`, inside that same set (kana words, numerals and words
      no registry record answers are the §3 carve-out, as in every other reading gate).
  P4  NOT SCANNABLE. Reject an item whose correct answer appears verbatim in the passage while no
      distractor does: that is answerable by string search, without reading.

plus the shape guards this file always had (Japanese-only, question form, three distinct
distractors, no em dash, reading resolves).

The passage itself stays a REFERENCE (`read:` slug) — the app renders it from `corpus/readings`,
which is its single source.

PROTOTYPE MODE
--------------
`--out DIR` writes the banks to DIR instead of `corpus/exam_banks` and prints a diff against the
committed banks: how many items would survive, how many each guard would drop, and which passages
would be left with no item. That is what W18 consumes; this script never regenerates the shipped
banks as a side effect of being run.

Usage: build_reading_comp_bank.py [--flagged '{"rc_n5_b1":[{"slug":...}]}'] [--out DIR]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
_sys.path.append(str(_pl.Path(__file__).resolve().parents[1] / "ingest"))
from dbtarget import db_target  # noqa: E402
from known_set import PassageGate, load_known_sets, is_kana_only  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
OUT = ROOT / "corpus" / "exam_banks"
# full-width Latin (Ａ-ｚ) allowed: real bank sentences contain initialisms like ＦＡＱ/ＯＫ
JP_OK = re.compile(r"^[ぁ-んァ-ヶー一-鿿々〆0-9０-９Ａ-Ｚａ-ｚ、。！？!?（）()・「」\s]+$")
KANJI = re.compile(r"[一-鿿]")
CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞"}



def option_problems(strings: list[str], ks, gate) -> str:
    """P2 + P3. "" when every string is readable inside `ks`, else the first reason.

    P2 is the kanji gate (a learner who cannot read an option cannot choose it); P3 runs the same
    known-set resolver the reading gate uses, so kana words, numerals and words no registry record
    answers are the design/reading_practice.md §3 carve-out here too.
    """
    for s in strings:
        bad_k = [c for c in s if KANJI.match(c) and c not in ks.kanji]
        if bad_k:
            return f"untaught kanji {''.join(sorted(set(bad_k)))}"
        res = gate.analyse(s, ks)
        if res.unknown_vocab:
            u = res.unknown_vocab[0]
            return f"untaught word {u['surface']} ({u['slug']}, {u['level']})"
    return ""


def question_is_about(question: str, passage: str, gate) -> list[str]:
    """P1. The content words of the question that actually occur in the passage. Empty means the
    question has no lexical footing in the text it is printed under."""
    return [m.surface() for m in gate.d.tok.tokenize(question, gate.d.C)
            if m.part_of_speech()[0] in CONTENT_POS and len(m.surface()) > 1
            and m.surface() in passage]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--flagged", default="{}")
    ap.add_argument("--out", default=None,
                    help="write the banks here instead of corpus/exam_banks and print a diff "
                         "against the committed banks (prototype mode; writes nothing to corpus/)")
    args = ap.parse_args()
    out_dir = Path(args.out) if args.out else OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    flagged: set = set()
    for _, v in json.loads(args.flagged).items():
        flagged.update(b["slug"] if isinstance(b, dict) else b for b in v)

    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    readings = {slug: {"level": lvl, "jp": jp, "lesson": lesson} for slug, lvl, jp, lesson
                in con.execute("SELECT slug,level,jp,gated_to_lesson FROM reading")}
    con.close()
    known = load_known_sets(ROOT)
    gate = PassageGate()
    # P2/P3 are gated to THE PASSAGE'S OWN known set (its gating lesson's cumulative set), which is
    # the task's rule and the stricter of the two available: the same item is also shown inside that
    # lesson's reading box, where nothing above the lesson may appear. W17's exam-level rule is
    # looser -- the LAST lesson of the level. The looser gate is measured alongside, so W18 can see
    # exactly what the strict choice costs instead of guessing.
    level_end = {}
    for lid, ks in known.items():
        lvl = lid.split(":", 1)[1].split("-", 1)[0]
        if lvl in ("n5", "n4", "n3") and len(ks.vocab) >= len(
                level_end.get(lvl, ks).vocab if lvl in level_end else set()):
            level_end[lvl] = ks

    banks: dict = {"n5": [], "n4": [], "n3": []}
    skipped: list = []
    why = Counter()

    for bf in sorted(SRC.glob("authored_rc_*.json")):
        d = json.loads(bf.read_text(encoding="utf-8"))
        for it in (d.get("items", []) if isinstance(d, dict) else d):
            slug = it.get("slug", "")
            rd = readings.get(slug)
            lvl = rd["level"] if rd else None
            q = (it.get("question") or "").strip()
            corr = (it.get("correct") or "").strip()
            dis = [x.strip() for x in (it.get("distractors") or [])]
            probs = []
            if slug in flagged or not lvl:
                probs.append("flagged/unknown-reading")
            if not q or not q.endswith(("か。", "か", "？", "。")) or not JP_OK.match(q):
                probs.append("question invalid")
            if not corr or corr in dis or len(set(dis)) != 3 or not all(JP_OK.match(x) for x in [corr] + dis):
                probs.append("option set invalid")
            if any("—" in x for x in [q, corr] + dis):
                probs.append("em dash")
            if rd and not probs:
                passage = rd["jp"]
                ks = known.get(rd["lesson"])
                if ks is None:
                    probs.append(f"gating lesson {rd['lesson']} is not exported")
                else:
                    # P1 — the question has to be about THIS text
                    if not question_is_about(q, passage, gate):
                        probs.append("P1 no content word of the question occurs in the passage")
                    # P2 + P3 — every option readable at this point in the course
                    bad = option_problems([q, corr, *dis], ks, gate)
                    if bad:
                        probs.append(f"P2/P3 {bad}")
                        if lvl in level_end and not option_problems([q, corr, *dis], level_end[lvl], gate):
                            why["P2/P3 would pass under W17 level-end cks"] += 1
                    # P4 — not answerable by string search
                    if corr in passage and not any(x in passage for x in dis):
                        probs.append("P4 the correct answer is the only option printed in the passage")
            if probs:
                why.update(p.split(" ")[0] for p in probs if not p.startswith("P2/P3 would"))
                skipped.append((slug, ";".join(probs)))
                continue
            banks[lvl].append({"id": f"rc:{lvl}:{slug.split(':', 1)[1]}", "level": lvl, "reading": slug,
                               "question": q, "correct": corr, "distractors": dis,
                               "layer": "C", "needs_review": True, "source": "authored+verified",
                               # `ai_generated` on an exam item means "the JAPANESE the learner
                               # reads was model-generated". A reading_comp question is authored
                               # from a human-written passage, so it is false — the derivation
                               # table validate_provenance_json.py enforces (rc -> false). It used
                               # to be stamped afterwards by migrate_exam_banks_p7.py, which is
                               # disabled in the rebuild manifest, so the builder emits it.
                               "ai_generated": False})
    counts = {}
    for lvl, items in banks.items():
        if items:
            (out_dir / f"{lvl}_reading_comp.json").write_text(json.dumps(items, ensure_ascii=False),
                                                              encoding="utf-8")
        counts[lvl] = len(items)
    print("reading_comp banks:", counts, "| skipped:", len(skipped))
    print("  dropped by guard:", dict(why))
    if args.out:
        committed = {}
        for f in sorted(OUT.glob("*_reading_comp.json")):
            for old in json.loads(f.read_text(encoding="utf-8")):
                committed[old["id"]] = old
        built = {i["id"]: i for its in banks.values() for i in its}
        gone = sorted(set(committed) - set(built))
        added = sorted(set(built) - set(committed))
        changed = sorted(i for i in set(built) & set(committed) if built[i] != committed[i])
        print(f"\nPROTOTYPE DIFF vs corpus/exam_banks ({len(committed)} committed items):")
        print(f"  survive unchanged {len(set(built) & set(committed)) - len(changed)}"
              f" | changed {len(changed)} | dropped {len(gone)} | new {len(added)}")
        drop_reason = dict(skipped)
        for i in gone[:12]:
            print(f"  DROP {i}: {drop_reason.get(committed[i]['reading'], 'unknown')}")
        if len(gone) > 12:
            print(f"  … and {len(gone) - 12} more drops")
        left = sorted(set(readings) - {b["reading"] for b in built.values()})
        print(f"  passages left with no item: {len(left)} (W18 authors these over the new text)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
