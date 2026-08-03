#!/usr/bin/env python3
"""Fix the whitespace-token / phantom-きごう defect corpus-wide (Phase-3 confirmed class).

Defect: a token whose surface is whitespace carries reading 記号/きごう ("symbol"), because the tokenizer
read a stray ASCII space as a word. Since kana == concat(C-token readings) and romaji == concat(C-token
romaji) (verified 20/20 on the QA-flagged sample), that phantom word leaks into both phonetic fields:
  jp:     彼は親切です それに頭もいいです
  kana:   かれわしんせつです**きごう**それにあたまもいいです
  romaji: karewashinsetsudesu**kigou**soreniatamamoiidesu

QA flagged 20 sentences; the same defect exists in 69. Both are fixed here - the class is deterministic.

Repair (revised after diff-audit round 3): blank the token's reading/romaji, NEVER touch jp.

An earlier version also deleted the space from jp for gen=true records, reasoning that a stray space is
unnatural Japanese. Audit round 3 showed that is wrong when the space SEPARATES TWO SENTENCES:
  彼は親切です それに頭もいいです  ->  彼は親切ですそれに頭もいいです
merged two independent sentences with no boundary, while the record's own explanation still taught それに
as a sentence-initial connector. In one case the deleted character was U+3000, which is itself valid
Japanese punctuation. The confirmed defect was only ever the phantom きごう reading leaking into
kana/romaji, so the fix is scoped to exactly that: a space has no pronunciation, so its reading is blanked
and the phonetic fields are rebuilt. jp is left alone for every record, which also keeps
concat(C-token surfaces) == jp true by construction. Idempotent.
Usage: fable5_fix_whitespace_tokens.py [--dry-run]
"""
from __future__ import annotations
import argparse, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(ROOT / "db" / "corpus.sqlite")

    # NOTE: SQL TRIM() strips ASCII spaces only, so it MISSES the ideographic space U+3000 (9 tokens
    # in this corpus, all glossed きごう). Filter in Python, where str.strip() covers all Unicode spaces.
    sids = sorted({sid for sid, surf in con.execute(
        "SELECT sentence_id, surface FROM token WHERE split_mode='C'") if surf.strip() == ""})
    if not sids:
        print("no whitespace tokens (idempotent skip)")
        return 0
    linked = sum(1 for surf, v in con.execute("SELECT surface, vocab_id FROM token")
                 if surf.strip() == "" and v is not None)
    if linked:
        print(f"ABORT: {linked} whitespace tokens are vocab-linked; refusing to delete")
        return 1

    deleted = blanked = jp_fixed = kana_fixed = romaji_fixed = 0
    for sid in sids:
        slug, jp, kana, romaji, gen = con.execute(
            "SELECT slug, jp, kana, romaji, COALESCE(ai_generated,0) FROM sentence WHERE id=?", (sid,)).fetchone()
        ws = [tid for tid, surf in con.execute(
            "SELECT id, surface FROM token WHERE sentence_id=? AND split_mode='C'", (sid,))
            if surf.strip() == ""]
        if not args.dry_run:
            con.executemany("UPDATE token SET reading='', romaji='' WHERE id=?", [(t,) for t in ws])
        blanked += len(ws)
        new_jp = jp

        rows = con.execute(
            "SELECT id, surface, reading, romaji FROM token WHERE sentence_id=? AND split_mode='C' "
            "ORDER BY position, id", (sid,)).fetchall()
        new_kana = "".join((r[2] or "") for r in rows)
        new_romaji = "".join((r[3] or "") for r in rows)
        if new_jp != jp:
            jp_fixed += 1
        if new_kana != kana:
            kana_fixed += 1
        if new_romaji != romaji:
            romaji_fixed += 1
        if not args.dry_run:
            con.execute("UPDATE sentence SET jp=?, kana=?, romaji=? WHERE id=?",
                        (new_jp, new_kana, new_romaji, sid))
        # HARD invariant check
        if "".join(r[1] for r in rows) != new_jp:
            print(f"ABORT {slug}: token surfaces do not reconstruct jp after fix")
            con.rollback()
            return 1

    if not args.dry_run:
        con.commit()
    con.close()
    print(f"whitespace-token fix ({'dry-run' if args.dry_run else 'applied'}): {len(sids)} sentences | "
          f"tokens deleted {deleted}, blanked {blanked} | jp {jp_fixed}, kana {kana_fixed}, romaji {romaji_fixed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
