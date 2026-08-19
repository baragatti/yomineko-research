#!/usr/bin/env python3
"""Repoint homophone-mislinked token.vocab_id values corpus-wide.

scripts/ingest/dissect.py resolves a token to a vocab entry through a form-table lookup that keys on the
WRITTEN FORM alone and keeps whichever entry registered first. Reading and part of speech never enter the
decision, so wherever several entries share a spelling the dissector can land on the rare one — and it
does, at scale. Quantified by the QA-queues re-dissection pass:

    し / する      -> 刷る "to print"      instead of 為る (する, "to do")
    この           -> 九                   instead of 此の
    かれ           -> 彼 read あれ         instead of 彼 read かれ
    せ             -> 背 read せい         instead of 背 read せ
    よう           -> 様 read さま         instead of 様 read よう
    尤も           -> 最も                 instead of 尤も

A learner-facing word list built from these teaches nonsense: the speaking path was offering 刷る
"to print" as vocabulary from the し of する.

EACH REPOINT IS CONDITIONAL ON THE TOKEN'S LEMMA OR SURFACE, never on the vocab id alone. 刷る, 最も and
背(せい) are all real words with real uses; moving every link would corrupt the genuine ones. The
condition is what separates "this token was mislabelled" from "this token is that word".

Repointing 334 and 41 crosses an n5/n4 boundary, so level-coverage counts move with them. Re-export and
re-run the gate after this; the speaking path must be rebuilt too.

Usage: fix_homophone_vocab_links.py [--apply]
"""
from __future__ import annotations
import argparse, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"

# (wrong_id, right_id, human label, SQL predicate over the token row that identifies a MISLINK)
REPOINTS = [
    (334, 1358, "刷る -> 為る (する)",
     "lemma='する' AND surface NOT LIKE '%刷%'"),
    (196, 257, "九 -> 此の (この)",
     "(lemma='この' OR surface='この') AND surface NOT LIKE '%九%'"),
    # NB: token.reading is stored in HIRAGANA here, not katakana. Predicates written against カレ/セ/ヨウ
    # matched nothing and silently reported "0 to repoint", which looks identical to "already clean".
    (41, 758, "彼(あれ) -> 彼(かれ)", "reading='かれ'"),
    (336, 1338, "背(せい) -> 背(せ)", "reading='せ'"),
    (1176, 1199, "様(さま) -> 様(よう)", "reading='よう'"),
    (1184, 1356, "最も -> 尤も",
     "surface LIKE '%尤%'"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    name = {i: f"{h}({k})" for i, h, k in con.execute("SELECT id,headword,kana FROM vocab")}
    total = 0

    for wrong, right, label, pred in REPOINTS:
        n = con.execute(f"SELECT COUNT(*) FROM token WHERE vocab_id=? AND ({pred})",
                        (wrong,)).fetchone()[0]
        keep = con.execute(f"SELECT COUNT(*) FROM token WHERE vocab_id=? AND NOT ({pred})",
                           (wrong,)).fetchone()[0]
        print(f"  {label:26s} repoint {n:4d}  leave {keep:4d} genuine "
              f"[{name.get(wrong)} -> {name.get(right)}]")
        if args.apply and n:
            con.execute(f"UPDATE token SET vocab_id=? WHERE vocab_id=? AND ({pred})", (right, wrong))
        total += n

    if args.apply:
        # sentence_vocab is a derived edge table; rebuild the rows these tokens back.
        con.execute("DELETE FROM sentence_vocab")
        con.execute("INSERT OR IGNORE INTO sentence_vocab (sentence_id,vocab_id) "
                    "SELECT DISTINCT sentence_id,vocab_id FROM token "
                    "WHERE vocab_id IS NOT NULL AND split_mode='C'")
        con.commit()
        print("  rebuilt sentence_vocab from the corrected token links")
    print(f"homophone repoint ({'APPLIED' if args.apply else 'dry-run'}): {total} tokens")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
