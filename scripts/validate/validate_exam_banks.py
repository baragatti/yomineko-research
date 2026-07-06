#!/usr/bin/env python3
"""Exam-bank gate: every item must be answerable and wrong-by-construction elsewhere.
- correct answer present, never among the distractors; exactly 3 unique distractors (choice types)
- cloze stems contain the blank （　）; sentence_order pieces reassemble to the answer
- GROUND TRUTH: kanji_reading correct == vocab.kana and stem == vocab.headword; orthography correct ==
  vocab.headword, stem == vocab.kana, and NO distractor is a homophone of the stem (its kana != stem)
- refs resolve (vocab_id / sentence slug)
Exit 1 on any failure. Usage: validate_exam_banks.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
BANKS = ROOT / "corpus" / "exam_banks"
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    if not BANKS.exists():
        print("validate_exam_banks: no banks (skip)")
        return 0
    con = sqlite3.connect(DB)
    vk = {vid: (hw, kana) for vid, hw, kana in con.execute("SELECT id,headword,kana FROM vocab")}
    kana_by_hw = {hw: kana for _, (hw, kana) in vk.items()}
    slugs = {r[0] for r in con.execute("SELECT slug FROM sentence")}
    rslugs = ({r[0] for r in con.execute("SELECT slug FROM reading")}
              if con.execute("SELECT name FROM sqlite_master WHERE name='reading'").fetchone() else set())
    fails = 0
    tot = 0
    for f in sorted(BANKS.glob("*_*.json")):
        items = json.loads(f.read_text(encoding="utf-8"))
        bad = []
        for it in items:
            tot += 1
            iid = it["id"]
            if "distractors" in it:
                d = it["distractors"]
                if len(d) != 3 or len(set(d)) != 3 or it["correct"] in d:
                    bad.append((iid, "distractor set invalid")); continue
            if it["id"].startswith(("cf:", "gf:")) and "（　）" not in it["stem"]:
                bad.append((iid, "no blank in stem")); continue
            if it["id"].startswith("so:") and "".join(it["pieces"]) != it["answer"]:
                bad.append((iid, "pieces != answer")); continue
            if it["id"].startswith("kr:"):
                hw, kana = vk.get(it["vocab_id"], (None, None))
                if it["stem"] != hw or it["correct"] != kana:
                    bad.append((iid, "kanji_reading mismatch vs vocab")); continue
            if it["id"].startswith("or:"):
                hw, kana = vk.get(it["vocab_id"], (None, None))
                if it["stem"] != kana or it["correct"] != hw:
                    bad.append((iid, "orthography mismatch vs vocab")); continue
                if any(kana_by_hw.get(x) == it["stem"] for x in it["distractors"]):
                    bad.append((iid, "homophone distractor (also a right answer)")); continue
            if it["id"].startswith("pp:"):
                if it["target"] not in it["stem"] or it["correct"] == it["target"]:
                    bad.append((iid, "paraphrase target/stem invalid")); continue
            if it["id"].startswith("us:"):
                w = it["wrong"]
                if len(set(w)) != 3 or it["correct"] in w or any(it["target"] not in s for s in w) \
                        or it["target"] not in it["correct"]:
                    bad.append((iid, "usage option set invalid")); continue
            if it["id"].startswith("rc:"):
                if not it.get("question", "").strip() or it["correct"] in it["distractors"]:
                    bad.append((iid, "reading_comp invalid")); continue
                if it.get("reading") and it["reading"] not in rslugs:
                    bad.append((iid, "reading ref unresolved")); continue
            if it["id"].startswith("tg:") and it.get("reading") and it["reading"] not in rslugs:
                bad.append((iid, "reading ref unresolved")); continue
            if it.get("sentence") and it["sentence"] not in slugs:
                bad.append((iid, "sentence ref unresolved")); continue
        if bad:
            fails += len(bad)
            print(f"  FAIL {f.name}: {len(bad)}  e.g. {bad[:3]}")
        else:
            print(f"  ok   {f.name}: {len(items)}")
    con.close()
    print(f"\nvalidate_exam_banks: {tot} items, {'FAIL ' + str(fails) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
