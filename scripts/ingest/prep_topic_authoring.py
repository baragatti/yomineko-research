#!/usr/bin/env python3
"""P6b — dump a topic's placed items + candidate example sentences for the N5/N4 lesson-authoring workflow.

For a topic slug, emits research/derived/topic_authoring/<topic>.json with: topic meta, the placed grammar
(key, pattern, label, explanation, + up to N candidate dissected sentences that USE it, by id, with jp + pt),
the placed vocab (headword, kana, pt/en gloss), and the placed kanji (char, meanings, readings). The authoring
workflow reads this to split the topic into lessons and reference sentences BY ID. Candidate sentences are
real-first, short-first, level≤topic. Usage: prep_topic_authoring.py <topic_slug> [--cand 6]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
OUTDIR = ROOT / "research" / "derived" / "topic_authoring"
LV = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    ap.add_argument("--cand", type=int, default=6)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    t = con.execute("SELECT t.*, m.level FROM topic t JOIN course_module m ON m.id=t.module_id "
                    "WHERE t.slug=?", (args.topic,)).fetchone()
    if not t:
        print(f"unknown topic {args.topic}", file=sys.stderr)
        return 1
    tid, level = t["id"], t["level"]
    maxlv = LV[level]

    def cand_sentences(gid):
        rows = con.execute(
            "SELECT s.id, s.slug, s.jp, s.level, s.ai_generated FROM sentence_grammar sg "
            "JOIN sentence s ON s.id=sg.sentence_id WHERE sg.grammar_id=?", (gid,)).fetchall()
        ok = [r for r in rows if LV.get(r["level"], 9) <= maxlv]
        ok.sort(key=lambda r: (r["ai_generated"], len(r["jp"])))  # real first, short first
        out = []
        for r in ok[:args.cand]:
            out.append({"slug": r["slug"], "jp": r["jp"],
                        "pt": get_text(con, "sentence", r["id"], "translation")})
        return out

    grammar = []
    for g in con.execute("SELECT id, key, structure_pattern FROM grammar_point WHERE introducing_topic_id=? "
                         "ORDER BY key", (tid,)):
        expl = get_text(con, "grammar_point", g["id"], "explanation") or ""
        grammar.append({"key": g["key"], "pattern": g["structure_pattern"] or "",
                        "label": get_text(con, "grammar_point", g["id"], "label") or "",
                        "explanation": (expl[:240] + "…") if len(expl) > 240 else expl,
                        "candidate_sentences": cand_sentences(g["id"])})
    vocab = []
    for v in con.execute("SELECT id, headword, kana FROM vocab WHERE introducing_topic_id=? "
                         "ORDER BY freq_rank IS NULL, freq_rank", (tid,)):
        sense = con.execute("SELECT gloss_en FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1",
                            (v["id"],)).fetchone()
        gloss = get_text(con, "vocab_sense",
                         con.execute("SELECT id FROM vocab_sense WHERE vocab_id=? ORDER BY sense_order LIMIT 1",
                                     (v["id"],)).fetchone()[0], "gloss") if sense else None
        vocab.append({"headword": v["headword"], "kana": v["kana"],
                      "gloss_pt": gloss, "gloss_en": json.loads(sense["gloss_en"]) if sense and sense["gloss_en"] else None})
    kanji = []
    for k in con.execute("SELECT id, character FROM kanji WHERE introducing_topic_id=? "
                         "ORDER BY freq_rank IS NULL, freq_rank", (tid,)):
        kanji.append({"char": k["character"],
                      "meanings": get_text(con, "kanji", k["id"], "meanings")})
    rec = {"topic": args.topic, "level": level, "order": t["ord"],
           "title": get_text(con, "topic", tid, "title"), "theme": get_text(con, "topic", tid, "theme"),
           "objectives": get_text(con, "topic", tid, "objectives") or [],
           "counts": {"grammar": len(grammar), "vocab": len(vocab), "kanji": len(kanji)},
           "grammar": grammar, "vocab": vocab, "kanji": kanji}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / (args.topic.split(":", 1)[1] + ".json")
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{args.topic}: grammar={len(grammar)} vocab={len(vocab)} kanji={len(kanji)} -> {out.relative_to(ROOT)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
