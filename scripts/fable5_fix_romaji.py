#!/usr/bin/env python3
"""Mechanical romaji/kana cleanup (fable5 validation, phase 0 systemics).

1. sentence.romaji + token.romaji: replace Japanese punctuation kept by the romanizer
   (。、「」・) with ASCII equivalents.
2. sent:tatoeba-3576174: the kanji 人 leaked into the phonetic kana/romaji — fix to ひと/hito
   (sentence.kana, sentence.romaji, and its token reading/romaji).
3. reading.tokens (JSON column): same punctuation map on each token's `ro`, plus
   katakana→romaji conversion (jaconv.kata2hira first — same fix as conjugate.py).

Idempotent. Run with the project venv (needs jaconv). Re-export corpus + readings afterwards.
Usage: fable5_fix_romaji.py [--dry-run]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path

import jaconv

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"

PUNCT = {"。": ".", "、": ",", "「": '"', "」": '"', "・": " "}


def ascii_punct(s: str) -> str:
    for jp, asc in PUNCT.items():
        s = s.replace(jp, asc)
    return s


def romanize_kana(s: str) -> str:
    return jaconv.kana2alphabet(jaconv.kata2hira(s)).replace("xtsu", "")


def fix_ro(ro: str) -> str:
    ro = ascii_punct(ro)
    if any(0x3040 <= ord(c) <= 0x30FF for c in ro):  # kana leftovers
        ro = romanize_kana(ro)
    return ro


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    n_sent = n_tok = n_read = 0

    # --- 1+2: sentences and tokens ---
    for sid, slug, kana, romaji in con.execute(
            "SELECT id, slug, kana, romaji FROM sentence WHERE romaji IS NOT NULL"):
        new_kana, new_ro = kana, fix_ro(romaji)
        if slug == "sent:tatoeba-3576174" and kana and "人" in kana:
            new_kana = kana.replace("人", "ひと")
            new_ro = new_ro.replace("人", "hito")
        if "人" in new_ro:
            new_ro = new_ro.replace("人", "hito")
        if (new_kana, new_ro) != (kana, romaji):
            n_sent += 1
            if not args.dry_run:
                con.execute("UPDATE sentence SET kana=?, romaji=? WHERE id=?", (new_kana, new_ro, sid))

    # token.reading is G2-gated analyzer truth (validate.py §7.2) — never touch it here.
    # Only the derived romaji is corrected.
    for tid, romaji in con.execute(
            "SELECT id, romaji FROM token WHERE romaji IS NOT NULL"):
        new_ro = fix_ro(romaji).replace("人", "hito")
        if new_ro != romaji:
            n_tok += 1
            if not args.dry_run:
                con.execute("UPDATE token SET romaji=? WHERE id=?", (new_ro, tid))

    # --- 3: reading-practice token JSON ---
    for slug, toks in con.execute("SELECT slug, tokens FROM reading"):
        arr = json.loads(toks)
        changed = False
        for t in arr:
            ro = t.get("ro")
            if ro:
                new = fix_ro(ro)
                if new != ro:
                    t["ro"] = new
                    changed = True
        if changed:
            n_read += 1
            if not args.dry_run:
                con.execute("UPDATE reading SET tokens=? WHERE slug=?",
                            (json.dumps(arr, ensure_ascii=False), slug))

    if not args.dry_run:
        con.commit()
    con.close()
    print(f"fable5 romaji fix ({'dry-run' if args.dry_run else 'applied'}): "
          f"{n_sent} sentences, {n_tok} tokens, {n_read} readings updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
