#!/usr/bin/env python3
"""Repair the sokuon (っ) romanization defect left in the bank by the old dissect.py gemination pass.

DEFECT. jaconv spells a small っ as IME-style 'xtsu' whenever it cannot see the mora that follows it,
and dissect.Dissector._fix_sokuon_romaji used to answer that by TRUNCATING the token at the 'xtsu' and
borrowing one character from the NEXT token. That is only ever right for a TRAILING っ (行っ|た → 'it'
+ 'ta'). Two classes came out wrong:

  A  token-initial っ — the gemination target sits inside the SAME token, so truncating threw the rest
     of the word away and pasted on an unrelated letter:
         って       -> '' / 'n' / 'k' / ','     (should be 'tte')
         っけ       -> '?' / '.'                (should be 'kke')
         っぱなし   -> 'n' / 'd' / '.'          (should be 'ppanashi')
  B  trailing っ before PUNCTUATION — there is no consonant to double, but the old rule only excluded
     vowels, so it borrowed the punctuation mark itself:
         あっ|、    -> 'a,'                     (should be 'a')
         えっ|。    -> 'e.'                     (should be 'e')
         くそ|っ|。 -> '.'                      (should be '')

SCOPE. Deliberately narrow: a token is touched only if its reading starts with っ, or its reading ends
with っ AND its stored romaji ends in a non-letter — i.e. only rows whose value is a casualty of the
borrow rule. Everything else keeps the value it has. (A blanket recompute of all 44,893 C tokens is what
produced the 206-objection drift in a previous repair: su-pa- -> suupaa, kesa, -> kesa、.) The replacement
values come from the FIXED converter in dissect.py, so the bank matches what a rebuild now produces.

sentence.romaji is rewritten only where it already equalled concat(token romaji) — keeping I3 true where
it was true. Sentences that violate I3 for unrelated reasons (numeral tokens romanized digit-by-digit,
readings that disagree with their own romaji) are reported and left alone; they are a different defect.

reading.tokens[].ro carries the same per-token romaji into the in-lesson reading boxes and is repaired
under the same predicate.

Idempotent. Run with the project venv, then re-export the corpus.
Usage: fix_sokuon_romaji.py [--apply]   (default is a dry run)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import jaconv

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
from dissect import PARTICLE_ROMAJI, Dissector  # noqa: E402  (the fixed converter, single source)

fix_sokuon = Dissector._fix_sokuon_romaji


def in_scope(reading: str, romaji: str) -> bool:
    """True for the two casualty classes above, and ONLY those."""
    if reading.startswith("っ"):
        return True
    return reading.endswith("っ") and bool(romaji) and not romaji[-1].isalpha()


def rebuilt_romaji(readings: list[str]) -> list[str]:
    """The romaji a rebuild produces across a whole token sequence: jaconv per reading, then the fixed
    in-token/boundary gemination pass."""
    toks = [{"romaji": jaconv.kana2alphabet(r)} for r in readings]
    fix_sokuon(toks)
    return [t["romaji"] for t in toks]


def checked(new: str, what: str) -> str:
    if "xtsu" in new or "'" in new or any(ord(ch) > 127 for ch in new):
        raise SystemExit(f"ABORT: {what} would get {new!r}")
    return new


def repair_tokens(con, apply: bool) -> tuple[int, dict[int, str], dict[int, str]]:
    """Returns (rows changed, concat(token romaji) before, concat after) keyed by sentence id."""
    rows: dict[int, list[dict]] = defaultdict(list)
    for tid, sid, surf, read, rom in con.execute(
            "SELECT id, sentence_id, surface, reading, romaji FROM token WHERE split_mode='C' "
            "ORDER BY sentence_id, position, id"):
        rows[sid].append({"id": tid, "surface": surf, "reading": read or "", "romaji": rom or ""})

    before = {sid: "".join(t["romaji"] for t in toks) for sid, toks in rows.items()}
    changed = 0
    for sid, toks in rows.items():
        idx = [i for i, t in enumerate(toks) if in_scope(t["reading"], t["romaji"])]
        if not idx:
            continue
        # A sokuon token followed by は/へ/を would need _tok_romaji's particle override to decide the
        # borrow (を is 'o', not 'wo'). None exist; fail loudly rather than guess if that ever changes.
        for i in idx:
            nxt = toks[i + 1]["surface"] if i + 1 < len(toks) else ""
            if nxt in PARTICLE_ROMAJI:
                raise SystemExit(f"ABORT: sokuon token {toks[i]['id']} is followed by particle {nxt}; "
                                 "the borrow needs the particle override — handle it explicitly")
        want = rebuilt_romaji([t["reading"] for t in toks])
        for i in idx:
            new = checked(want[i], f"token {toks[i]['id']}")
            if new == toks[i]["romaji"]:
                continue
            print(f"  token {toks[i]['id']:>6}  sid={sid:<5} {toks[i]['surface']}  {toks[i]['reading']}"
                  f"  {toks[i]['romaji']!r} -> {new!r}")
            if apply:
                con.execute("UPDATE token SET romaji=? WHERE id=?", (new, toks[i]["id"]))
            toks[i]["romaji"] = new
            changed += 1
    after = {sid: "".join(t["romaji"] for t in toks) for sid, toks in rows.items()}
    return changed, before, after


def repair_reading_bank(con, apply: bool) -> int:
    changed = 0
    for slug, blob in con.execute("SELECT slug, tokens FROM reading"):
        arr = json.loads(blob)
        idx = [i for i, t in enumerate(arr) if in_scope(t.get("r") or "", t.get("ro") or "")]
        if not idx:
            continue
        want = rebuilt_romaji([t.get("r") or "" for t in arr])
        dirty = False
        for i in idx:
            new = checked(want[i], f"{slug} token {i}")
            if new == (arr[i].get("ro") or ""):
                continue
            print(f"  reading {slug} [{i}] {arr[i].get('s')}  {arr[i].get('r')}  "
                  f"{arr[i].get('ro')!r} -> {new!r}")
            arr[i]["ro"] = new
            dirty = True
            changed += 1
        if dirty and apply:
            con.execute("UPDATE reading SET tokens=? WHERE slug=?",
                        (json.dumps(arr, ensure_ascii=False), slug))
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write to the DB (default: dry run)")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    sent = {sid: (ro or "") for sid, ro in con.execute("SELECT id, romaji FROM sentence")}

    print("token rows:")
    n_tok, before, after = repair_tokens(con, args.apply)

    print("\nsentence rows (rewritten only where I3 held before and the token repair moved the concat):")
    n_sent, left = 0, []
    for sid, new_concat in after.items():
        if before[sid] == new_concat or sent[sid] == new_concat:
            continue                                # untouched, or already equal to the new concat
        if sent[sid] != before[sid]:
            left.append(sid)                        # I3 was already broken for an unrelated reason
            continue
        print(f"  sentence {sid:<5} {sent[sid]!r} -> {new_concat!r}")
        if args.apply:
            con.execute("UPDATE sentence SET romaji=? WHERE id=?", (new_concat, sid))
        n_sent += 1

    print("\nreading-bank tokens:")
    n_read = repair_reading_bank(con, args.apply)

    con.commit() if args.apply else con.rollback()
    print(f"\nsokuon romaji fix ({'applied' if args.apply else 'dry-run'}): "
          f"{n_tok} tokens, {n_sent} sentences, {n_read} reading-bank tokens")
    if left:
        print(f"left alone — sentence.romaji already violated I3 for an unrelated reason "
              f"({len(left)}): {sorted(left)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
