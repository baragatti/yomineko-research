#!/usr/bin/env python3
"""Apply the staged furigana repairs to research/derived/lessons/<slug>.json.

validate_furigana.py enforces that hiragana inside an annotated ruby span also appears in that span's
reading, in order. It reported 49 failures in two shapes:
  * 32 spans with reading="" — 22 of those annotate KANA-ONLY text (しまう, を, ます, やすい...), where
    ruby carries no information at all and the empty attribute is a stray. Those become a bare <jp> tag,
    which is the corpus's own convention (5,629 kana-only bare spans vs 465 that repeat the kana).
    The other 10 contain kanji and get a real reading rebuilt from corpus/vocab.
  * 17 truncated readings — 13 stop after the kanji and drop the okurigana tail (reading="た" over
    食べてみて), 4 are genuine transcription slips (北だから lost its copula だ).

Applied HERE and not in the DB: load_lessons.py re-authors every lesson from these JSON files, so a DB
edit is wiped on the next load. The earlier Phase-6 round learned that the hard way.

Guards: the anchor must be byte-exact and UNIQUE in the field (several of these tags repeat verbatim
within one body, so a non-unique anchor would edit the wrong occurrence); the visible TEXT between the
tags must be unchanged, since that text is Layer A; and the tag multiset must not move.

Usage: apply_furigana_fixes.py [--apply]
"""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "derived" / "qa_queues" / "furigana.json"
LESSONS = ROOT / "research" / "derived" / "lessons"
TAGS = re.compile(r"</?([a-zA-Z][\w-]*)[^>]*>")
STRIP = re.compile(r"<[^>]*>")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = [r for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"] if r["verdict"] == "fix"]
    print(f"{len(rows)} furigana fixes staged")

    by_file: dict[str, list] = {}
    for r in rows:
        by_file.setdefault(r["id"].split("#")[0], []).append(r)

    applied, skipped = 0, []
    for path, items in sorted(by_file.items()):
        fp = ROOT / path
        if not fp.exists():
            skipped += [(r["id"], "file not found") for r in items]
            continue
        rec = json.loads(fp.read_text(encoding="utf-8"))
        body = rec.get("body") or ""
        dirty = False
        for r in items:
            cur, fix = r["current"], r["fix"]
            n = body.count(cur)
            if n == 0:
                skipped.append((r["id"], "anchor not found")); continue
            if n > 1:
                # These tags repeat verbatim; without a unique anchor we would edit the wrong one.
                skipped.append((r["id"], f"anchor occurs {n} times, not unique")); continue
            new = body.replace(cur, fix, 1)
            if STRIP.sub("", new) != STRIP.sub("", body):
                skipped.append((r["id"], "would change the visible Layer-A text")); continue
            if Counter(TAGS.findall(new)) != Counter(TAGS.findall(body)):
                skipped.append((r["id"], "would change the tag multiset")); continue
            body = new
            applied += 1
            dirty = True
        if dirty:
            rec["body"] = body
            if args.apply:
                fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"furigana apply ({'APPLIED' if args.apply else 'dry-run'}): {applied} spans")
    if skipped:
        print(f"skipped {len(skipped)}: {dict(Counter(w for _, w in skipped).most_common(5))}")
        for i, w in skipped[:6]:
            print(f"   {i[:78]}: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
