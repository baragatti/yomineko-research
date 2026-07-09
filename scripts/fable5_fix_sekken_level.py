#!/usr/bin/env python3
"""Fix the 接見/石鹸 kana-collision level defect (Phase 2 confirmed finding, vocab:1385390).
接見 (せっけん, 'audience; legal visit') was tagged N5 because two community lists' せっけん rows (which mean
石鹸 'soap' — already in the corpus as vocab:1382590, n5) were matched to the wrong JMdict entry by kana.
No ingested list contains 接見 at any level, so it gets the conservative advanced tag (n1) with the
collision recorded in level_sources. Its 6 linked sentences are already n1/n2 (levels came from other
items), so no sentence recompute is needed. Exam banks must be regenerated after this (the n5
kanji_reading/orthography items for 接見 drop out — that leak was the harm). Idempotent.
Usage: fable5_fix_sekken_level.py"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")
    row = con.execute("SELECT id, level FROM vocab WHERE slug='vocab:1385390'").fetchone()
    if not row:
        print("vocab:1385390 not found"); return 1
    if row[1] == "n1":
        print("already n1 (idempotent skip)"); con.close(); return 0
    sources = {"correction": "2026-07-09 kana-collision fix: bluskyo/jlptvocabapi せっけん n5 rows mean "
                             "石鹸 (soap, vocab:1382590); 接見 is unlisted in every ingested JLPT list -> "
                             "conservative n1 (advanced formal/legal term)"}
    con.execute("UPDATE vocab SET level='n1', level_confidence=0.5, level_agreement=0, level_sources=? "
                "WHERE id=?", (json.dumps(sources, ensure_ascii=False), row[0]))
    con.commit()
    con.close()
    print("接見 vocab:1385390 re-tagged n5 -> n1 (kana collision with 石鹸 corrected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
