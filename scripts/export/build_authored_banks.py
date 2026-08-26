#!/usr/bin/env python3
"""Assemble the AUTHORED exam banks (paraphrase 言い換え + usage 用法) from the workflow output
(research/derived/reauthor/exam_authored/authored_{lvl}.json), excluding verifier-flagged vids, with
deterministic HARD guards: Japanese-only answer fields, correct != distractors (paraphrase correct must not
equal the headword/kana), usage keeps the REAL example as the correct option + 3 authored wrong-usage
sentences (all distinct, none equal to the real one), no em dash. Items are Layer C, needs_review (teacher
sign-off) and carry provenance. Usage: build_authored_banks.py [--flagged '{"n5":[vids...]}']"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
OUT = ROOT / "corpus" / "exam_banks"
JP_OK = re.compile(r"^[ぁ-んァ-ヶー一-鿿々〆0-9０-９、。！？!?（）()・\s]+$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--flagged", default="{}")
    args = ap.parse_args()
    flagged: dict = {}
    for key, v in json.loads(args.flagged).items():
        lvl = key.split("_")[0]  # accepts level keys or batch keys (n5_b1)
        flagged.setdefault(lvl, set()).update(b["vid"] if isinstance(b, dict) else b for b in v)
    counts, skipped = {}, {}
    for lvl in ("n5", "n4", "n3"):
        facts = {i["vid"]: i for i in json.loads((SRC / f"input_{lvl}.json").read_text(encoding="utf-8"))}
        authored = []
        for bf in sorted(SRC.glob(f"authored_{lvl}_b*.json")):
            d = json.loads(bf.read_text(encoding="utf-8"))
            authored += (d.get("items", []) if isinstance(d, dict) else d)
        if not authored:
            print(f"{lvl}: no authored batches (skip)")
            continue
        para, usage, skip = [], [], []
        for it in authored:
            vid = it.get("vid")
            f = facts.get(vid)
            if not f or vid in flagged.get(lvl, set()):
                skip.append((vid, "flagged/unknown")); continue
            p = it.get("paraphrase") or {}
            pc, pd = (p.get("correct") or "").strip(), [d.strip() for d in (p.get("distractors") or [])]
            uw = [s.strip() for s in (it.get("usage_wrong") or [])]
            probs = []
            if not pc or pc in (f["hw"], f["kana"]) or pc in pd or len(set(pd)) != 3:
                probs.append("paraphrase set invalid")
            if any(not JP_OK.match(x) for x in [pc] + pd if x):
                probs.append("non-JP in paraphrase")
            if len(set(uw)) != 3 or any(not JP_OK.match(s) for s in uw) or f["example"] in uw \
                    or any(f["hw"] not in s for s in uw):
                probs.append("usage set invalid")
            if any("—" in x for x in [pc] + pd + uw):
                probs.append("em dash")
            if probs:
                skip.append((vid, ";".join(probs))); continue
            para.append({"id": f"pp:{lvl}:{vid}", "level": lvl, "stem": f["example"], "target": f["hw"],
                         "correct": pc, "distractors": pd, "vocab_id": vid, "sentence": f["ex_slug"],
                         "layer": "C", "needs_review": True, "source": "authored+verified"})
            usage.append({"id": f"us:{lvl}:{vid}", "level": lvl, "target": f["hw"],
                          "correct": f["example"], "wrong": uw, "vocab_id": vid, "sentence": f["ex_slug"],
                          "layer": "C", "needs_review": True, "source": "authored+verified(real-correct)"})
        (OUT / f"{lvl}_paraphrase.json").write_text(json.dumps(para, ensure_ascii=False), encoding="utf-8")
        (OUT / f"{lvl}_usage.json").write_text(json.dumps(usage, ensure_ascii=False), encoding="utf-8")
        counts[lvl] = (len(para), len(usage))
        skipped[lvl] = len(skip)
        if skip[:3]:
            print(f"  {lvl} sample skips:", skip[:3])
    print("authored banks (paraphrase, usage):", counts, "| skipped:", skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
