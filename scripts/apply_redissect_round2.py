#!/usr/bin/env python3
"""Apply the FOUR re-dissection fixes that survived adversarial verification.

!!! APPLIED ONE-SHOT — DO NOT RE-RUN WITH --apply. !!!
================================================================================================
The four fixes below were APPLIED to db/corpus.sqlite on 2026-08-19 (commit c9d54f0) and each is
guarded by an expected-current-value check, so a re-run would only SKIP them. What must NEVER run
again is the `DELETE FROM sentence_vocab` + rebuild block at the bottom of main(). It rebuilds the
table as a projection of token.vocab_id, which it never was: sentence_vocab was the UNION of three
rules (token links, relink_vocab.py's contiguous-token runs, and the July-2026 n3 lemma tagger).
That DELETE — here and in scripts/fix_homophone_vocab_links.py — thinned it from ~31,789 rows to
exactly the 20,357-row token subset and destroyed 436 (sentence_id, vocab_id) pairs the COMMITTED
exam banks depend on; n3_context_fill collapses from 400 items to 97 on a rebuild.

Repaired 2026-08-26 by scripts/ingest/build_sentence_vocab.py, which is now the ONLY writer of
sentence_vocab (INSERT OR IGNORE, all three rules, per-row link_rule/reading_verified provenance).
If token.vocab_id ever moves again, run THAT after the edit — never this DELETE.
================================================================================================


The re-dissection queue proposed 28 fixes. Independent verification kept 4. What killed the rest is
worth recording, because the same reasoning applies to any future queue of this shape:

  TEN were already landed. scripts/fix_homophone_vocab_links.py repointed all six of their vocab classes
  corpus-wide earlier in this session, so their anchors no longer exist. An applier treating a missing
  anchor as a failure would have reported ten false errors.

  TEN rewrite the Japanese, and are refused. The appliers in this project do byte-exact FIELD
  replacement, not re-dissection. Writing `jp` alone leaves the stored kana, romaji, token array,
  particles and structure paragraph describing a sentence that no longer exists. Four of those ten were
  also mere orthography preference (此処 vs ここ, 様 vs よう) with no stated convention behind them, and
  the verifier measured that re-dissecting from the proposed spellings would STRIP the target link the
  sentence was generated to teach: dissect.py registers ここ under entry 196 and よう under entry 955,
  and all 58 ここ-spelled and 119 よう-spelled tokens in the bank carry those ids.

  SIX name a real defect but need a coordinated re-author of one whole sentence (jp, kana, romaji, the
  affected token, both translations, the prose) and three of them change WHO the sentence is about,
  leaving the stored pt-BR describing the old referent. Those are escalated, not applied.

The four kept here each touch exactly one derived or mechanical field and no Layer-A string.

Anchors in this queue are NOT globally unique ("inflection": "attributive" occurs 1,549 times, and
"vocab_id": 79 prefix-matches ids like 790), so every edit is resolved on the PARSED row by
(sentence slug, split_mode='C', position) and column. Never by text replacement.

Usage: apply_redissect_round2.py [--apply]
"""
from __future__ import annotations
import argparse, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")

# (slug, C-token position, column, expected current value, new value, why)
FIXES = [
    ("sent:gen-986d061ae368", 2, "inflection", "attributive", "terminal",
     "正しい closes its clause before 、 and a conjunction; its sibling 厳しい is already terminal"),
    ("sent:tatoeba-141147", 5, "vocab_id", 1178, 4419,
     "surface 下っ lemma 下る linked to 下がる; not covered by the corpus-wide repoint"),
    ("sent:tatoeba-223377", 8, "romaji", "chuu", "naka",
     "position 8 is 中 read なか but romaji still holds the analyzer's original ちゅう"),
    ("sent:tatoeba-223377", 8, "vocab_id", 79, 464,
     "中 read なか pointed at entry 79, which is 内 (うち)"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    ok = 0
    for slug, pos, col, want, new, why in FIXES:
        row = con.execute(
            f"SELECT t.id, t.{col}, t.surface, t.reading FROM token t JOIN sentence s ON s.id=t.sentence_id "
            f"WHERE s.slug=? AND t.split_mode='C' AND t.position=?", (slug, pos)).fetchone()
        if not row:
            print(f"  SKIP {slug}@{pos}.{col}: no C token at that position"); continue
        tid, cur, surf, read = row
        if str(cur) != str(want):
            print(f"  SKIP {slug}@{pos}.{col}: holds {cur!r}, expected {want!r} (already changed?)")
            continue
        print(f"  {slug}@{pos} ({surf}/{read}) {col}: {cur!r} -> {new!r}  [{why}]")
        if args.apply:
            con.execute(f"UPDATE token SET {col}=? WHERE id=?", (new, tid))
        ok += 1
    if args.apply:
        # vocab_id moved, so the derived edge table must follow.
        con.execute("DELETE FROM sentence_vocab")
        con.execute("INSERT OR IGNORE INTO sentence_vocab (sentence_id,vocab_id) "
                    "SELECT DISTINCT sentence_id,vocab_id FROM token "
                    "WHERE vocab_id IS NOT NULL AND split_mode='C'")
        con.commit()
    print(f"redissect round2 ({'APPLIED' if args.apply else 'dry-run'}): {ok}/{len(FIXES)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
