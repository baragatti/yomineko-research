#!/usr/bin/env python3
"""Assemble the AUTHORED listening (聴解) script banks from the workflow output
(authored_listen_{level}_{sub}.json) per design/listening.md, excluding verifier-flagged refs, with
deterministic HARD guards: JP-only text (full-width Latin ok), speaker registry, per-sub turn bounds and
option counts, distinct options, correct not among distractors, no em dash, reply prompts BYTE-EQUAL to
their real bank sentence. Items are Layer C needs_review, audio "pending" (voiced later; scripts double as
review-mode transcripts). Usage: build_listening_bank.py [--flagged '{"n5_task":[{"ref":"3",...}]}']"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "research" / "derived" / "reauthor" / "exam_authored"
OUT = ROOT / "corpus" / "exam_banks"
# … = trailing-off speech (言いさし, a real listening cue); ，= thousands separator (３，５００円)
JP_OK = re.compile(r"^[ぁ-んァ-ヶー一-鿿々〆0-9０-９Ａ-Ｚａ-ｚ、。！？!?（）()・「」…，\s]+$")
SPEAKERS = {"M1", "M2", "F1", "F2", "N"}
PREFIX = {"task": "lt", "point": "lp", "gist": "lg", "say": "ls", "reply": "lr"}
TURNS = {"task": (3, 8), "point": (3, 8), "gist": (2, 7), "say": (1, 1), "reply": (1, 1)}
N_DIS = {"task": 3, "point": 3, "gist": 3, "say": 2, "reply": 2}
BATCHES = [("n5", s) for s in ("task", "point", "say", "reply")] + \
          [("n4", s) for s in ("task", "point", "say", "reply")] + \
          [("n3", s) for s in ("task", "point", "gist", "say", "reply")]


def check(it, sub, prompt_jp):
    script = it.get("script") or []
    q = (it.get("question") or "").strip()
    corr = (it.get("correct") or "").strip()
    dis = [x.strip() for x in (it.get("distractors") or [])]
    texts = [t.get("text", "") for t in script] + [corr] + dis + ([q] if q else [])
    lo, hi = TURNS[sub]
    if not (lo <= len(script) <= hi) or any(t.get("speaker") not in SPEAKERS or not t.get("text", "").strip()
                                            for t in script):
        return "script shape invalid"
    if sub in ("task", "point", "gist") and (not q or not q.endswith(("か。", "か", "？"))):
        return "question invalid"
    if sub in ("say", "reply") and q:
        return "unexpected question"
    if sub == "say" and (script[0]["speaker"] != "N" or not script[0]["text"].endswith("何と言いますか。")):
        return "say situation invalid"
    if sub == "reply":
        if script[0]["speaker"] not in ("M1", "F1"):
            return "reply speaker invalid"
        if prompt_jp is None or script[0]["text"] != prompt_jp:
            return "reply prompt not verbatim"
    if not corr or corr in dis or len(set(dis)) != N_DIS[sub] or len(dis) != N_DIS[sub]:
        return "option set invalid"
    if any(not JP_OK.match(x) for x in texts):
        return "non-JP text"
    if any("—" in x for x in texts):
        return "em dash"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--flagged", default="{}")
    args = ap.parse_args()
    flagged: dict = {}
    for key, v in json.loads(args.flagged).items():
        flagged[key] = {str(b["ref"]) if isinstance(b, dict) else str(b) for b in v}
    counts, skipped = {}, []
    for lvl, sub in BATCHES:
        key = f"{lvl}_{sub}"
        fp = SRC / f"authored_listen_{key}.json"
        if not fp.exists():
            skipped.append((key, "batch file missing")); continue
        prompts = ({x["slug"]: x["jp"] for x in json.loads(
            (SRC / f"input_listen_{key}.json").read_text(encoding="utf-8"))["items"]}
            if sub == "reply" else {})
        items = []
        for it in json.loads(fp.read_text(encoding="utf-8"))["items"]:
            ref = str(it.get("slug") if sub == "reply" else it.get("n"))
            if ref in flagged.get(key, set()) or "*" in flagged.get(key, set()):
                skipped.append((f"{key}:{ref}", "flagged")); continue
            prob = check(it, sub, prompts.get(it.get("slug")) if sub == "reply" else None)
            if prob:
                skipped.append((f"{key}:{ref}", prob)); continue
            iid = (f"lr:{lvl}:{it['slug'].split(':', 1)[1]}" if sub == "reply"
                   else f"{PREFIX[sub]}:{lvl}:{int(it['n']):03d}")
            rec = {"id": iid, "level": lvl, "script": it["script"], "question": (it.get("question") or ""),
                   "correct": it["correct"].strip(), "distractors": [x.strip() for x in it["distractors"]],
                   "audio": "pending", "layer": "C", "needs_review": True, "ai_generated": True}
            if sub == "reply":
                rec["sentence"] = it["slug"]
            items.append(rec)
        if items:
            (OUT / f"{lvl}_listening_{sub}.json").write_text(
                json.dumps(items, ensure_ascii=False), encoding="utf-8")
        counts[key] = len(items)
    print("listening banks:", counts)
    print("skipped:", len(skipped), skipped[:6])
    return 0


if __name__ == "__main__":
    sys.exit(main())
