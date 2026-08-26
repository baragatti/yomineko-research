#!/usr/bin/env python3
"""Assemble the AUTHORED reading-comprehension bank (読解) from the workflow output
(authored_rc_{lvl}_b{n}.json), excluding verifier-flagged slugs, with deterministic HARD guards:
Japanese-only question/options, question ends with か/。/？, 3 distinct distractors none equal to the correct
answer, reading slug resolves, no em dash. Items are Layer C, needs_review; the passage stays a REFERENCE
(read: slug) — the app renders the passage from corpus/readings (single source of truth).
Usage: build_reading_comp_bank.py [--flagged '{"rc_n5_b1":[{"slug":...}]}']"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
OUT = ROOT / "corpus" / "exam_banks"
# full-width Latin (Ａ-ｚ) allowed: real bank sentences contain initialisms like ＦＡＱ/ＯＫ
JP_OK = re.compile(r"^[ぁ-んァ-ヶー一-鿿々〆0-9０-９Ａ-Ｚａ-ｚ、。！？!?（）()・「」\s]+$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--flagged", default="{}")
    args = ap.parse_args()
    flagged: set = set()
    for _, v in json.loads(args.flagged).items():
        flagged.update(b["slug"] if isinstance(b, dict) else b for b in v)
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
    rlvl = dict(con.execute("SELECT slug,level FROM reading"))
    con.close()
    banks: dict = {"n5": [], "n4": [], "n3": []}
    skipped = []
    for bf in sorted(SRC.glob("authored_rc_*.json")):
        d = json.loads(bf.read_text(encoding="utf-8"))
        for it in (d.get("items", []) if isinstance(d, dict) else d):
            slug = it.get("slug", "")
            lvl = rlvl.get(slug)
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
            if probs:
                skipped.append((slug, ";".join(probs)))
                continue
            banks[lvl].append({"id": f"rc:{lvl}:{slug.split(':', 1)[1]}", "level": lvl, "reading": slug,
                               "question": q, "correct": corr, "distractors": dis,
                               "layer": "C", "needs_review": True, "source": "authored+verified"})
    counts = {}
    for lvl, items in banks.items():
        if items:
            (OUT / f"{lvl}_reading_comp.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
        counts[lvl] = len(items)
    print("reading_comp banks:", counts, "| skipped:", len(skipped), skipped[:3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
