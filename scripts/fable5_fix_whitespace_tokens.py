#!/usr/bin/env python3
"""Fix the whitespace-token / phantom-きごう defect corpus-wide (Phase-3 confirmed class).

Defect: a token whose surface is whitespace carries reading 記号/きごう ("symbol"), because the tokenizer
read a stray ASCII space as a word. Since kana == concat(C-token readings) and romaji == concat(C-token
romaji) (verified 20/20 on the QA-flagged sample), that phantom word leaks into both phonetic fields:
  jp:     彼は親切です それに頭もいいです
  kana:   かれわしんせつです**きごう**それにあたまもいいです
  romaji: karewashinsetsudesu**kigou**soreniatamamoiidesu

QA flagged 20 sentences; the same defect exists in 69. Both are fixed here - the class is deterministic.

Repair, preserving the HARD invariant concat(C-token surfaces) == jp:
  * gen=true  (AI-authored): the stray space is itself unnatural Japanese, so drop it from jp AND delete
    the whitespace token.
  * gen=false (real Tatoeba/Tanaka, Layer A): jp is authoritative and untouchable, so KEEP the token (the
    space must stay in the surface chain) but blank its reading/romaji - a space has no pronunciation.
Then recompute kana/romaji from the surviving token readings. Idempotent. No token is vocab-linked, so
deleting cannot orphan a reference. Usage: fable5_fix_whitespace_tokens.py [--dry-run]
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

    sids = [r[0] for r in con.execute(
        "SELECT DISTINCT sentence_id FROM token WHERE TRIM(surface)='' AND split_mode='C' ORDER BY 1")]
    if not sids:
        print("no whitespace tokens (idempotent skip)")
        return 0
    linked = con.execute("SELECT COUNT(*) FROM token WHERE TRIM(surface)='' AND vocab_id IS NOT NULL").fetchone()[0]
    if linked:
        print(f"ABORT: {linked} whitespace tokens are vocab-linked; refusing to delete")
        return 1

    deleted = blanked = jp_fixed = kana_fixed = romaji_fixed = 0
    for sid in sids:
        slug, jp, kana, romaji, gen = con.execute(
            "SELECT slug, jp, kana, romaji, COALESCE(ai_generated,0) FROM sentence WHERE id=?", (sid,)).fetchone()
        ws = [r[0] for r in con.execute(
            "SELECT id FROM token WHERE sentence_id=? AND TRIM(surface)='' AND split_mode='C'", (sid,))]
        if gen:
            if not args.dry_run:
                for tid in ws:
                    con.execute("DELETE FROM localized_text WHERE entity_type='token' AND entity_id=?", (tid,))
                    con.execute("DELETE FROM token WHERE id=?", (tid,))
            deleted += len(ws)
            new_jp = "".join(jp.split(" ")) if " " in jp else jp
        else:
            if not args.dry_run:
                con.executemany("UPDATE token SET reading='', romaji='' WHERE id=?", [(t,) for t in ws])
            blanked += len(ws)
            new_jp = jp

        rows = con.execute(
            "SELECT id, surface, reading, romaji FROM token WHERE sentence_id=? AND split_mode='C' "
            "ORDER BY position, id", (sid,)).fetchall()
        rows = [r for r in rows if not (gen and r[0] in ws)]
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
