#!/usr/bin/env python3
"""Gate: every <jp reading="..."> furigana must actually cover the Japanese it annotates.

Phase-6 QA found readings that silently drop the tail of their own sentence — e.g.
  <jp reading="つまりかいぎはちゅうし">つまり、会議は中止だ</jp>      (だ missing)
  <jp reading="きたからさむいわけだ">北だから寒いわけだ</jp>          (北だ… -> きた… loses だ)
A learner sees furigana that stops short of the word, so this is worth a hard check rather than a
one-off fix.

Deterministic rule, no dictionary needed: the HIRAGANA that appears literally in the annotated text must
appear in the reading, in the same order (subsequence). Kanji may read as anything, but okurigana and
particles cannot vanish.

Two conventions are honoured so they are not false positives:
  * katakana is skipped entirely — a reading may spell ケーキ as けえき, so its ー and katakana are not
    required to appear literally;
  * ー inside hiragana runs is likewise not required.
Anything still failing is a genuine coverage gap.

Exit 1 on any failure. Usage: validate_furigana.py [--list]
"""
from __future__ import annotations
import argparse, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
JPTAG = re.compile(r'<jp\s+reading="([^"]*)"\s*>(.*?)</jp>', re.S)
HIRA = re.compile(r"[ぁ-ん]")          # deliberately excludes ー and katakana
TAGS = re.compile(r"<[^>]+>")


def missing_kana(reading: str, text: str) -> str:
    """Return the first hiragana of `text` that the reading fails to cover, or ''."""
    required = HIRA.findall(TAGS.sub("", text))
    it = iter(reading)
    for ch in required:
        if ch not in it:
            return ch
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
    checked = fails = 0
    bad = []
    for etype in ("lesson", "topic"):
        for eid, field, value in con.execute(
                "SELECT entity_id, field, value FROM localized_text WHERE entity_type=? AND locale='pt-BR'",
                (etype,)):
            if not value:
                continue
            for reading, text in JPTAG.findall(value):
                plain = TAGS.sub("", text)
                if not HIRA.search(plain):
                    continue
                checked += 1
                miss = missing_kana(reading, text)
                if miss:
                    fails += 1
                    bad.append((etype, eid, field, reading, plain, miss))
    con.close()
    if bad and args.list:
        for etype, eid, field, r, t, m in bad:
            print(f"  {etype}:{eid} [{field}] missing '{m}'\n     reading: {r}\n     text   : {t}")
    print(f"validate_furigana: {checked} annotated spans, "
          f"{'FAIL ' + str(fails) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
