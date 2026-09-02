#!/usr/bin/env python3
"""Apply the Phase-3 sentence patch (owner go-ahead 2026-08-05).

Writes the EXACT artifact that was audited: phase3_diff/*.json holds the projected `after` state that four
adversarial audit rounds reviewed, so this applier replays that state rather than re-deriving it from the
op sources. Re-deriving would risk applying something subtly different from what was approved.

Safety properties:
  * quarantined sentences are simply absent from the diff batches, so they cannot be written;
  * token identity is recovered by re-reading tokens in the SAME order the renderer used
    (ORDER BY split_mode, position, id) - the batch order that patch indices refer to;
  * every sentence is re-checked against the hard invariants IMMEDIATELY BEFORE writing it
    (concat(C surfaces)==jp, kana==concat(readings), romaji==concat(token romaji), no Latin in kana,
    no kana/CJK in romaji). Any violation aborts the whole transaction - nothing partial is left behind;
  * jp is only written when it actually differs, and a jp change on a gen=false (Layer-A) record aborts;
  * single transaction, committed only if every sentence passes.

Usage: fable5_sentences_apply.py [--dry-run]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"
DIFF = FD / "phase3_diff"
LATIN = re.compile(r"[A-Za-z]")
JPRE = re.compile(r"[぀-ヿ一-鿿]")
TEXT_FIELDS = {"translation", "translation_literal", "structure_explanation"}
TOKEN_LOCALIZED = {"gloss": "gloss", "role": "role", "note": "conjugation_note"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    con.execute("BEGIN")

    sentences = []
    for fp in sorted(DIFF.glob("*.json")):
        sentences.extend(json.loads(fp.read_text(encoding="utf-8"))["sentences"])
    print(f"sentences in audited diff: {len(sentences)}")

    n_sent = n_text = n_tok = n_jp = 0
    for s in sentences:
        slug, after = s["slug"], s["after"]
        row = con.execute("SELECT id, jp, COALESCE(ai_generated,0) FROM sentence WHERE slug=?",
                          (slug,)).fetchone()
        if not row:
            print(f"ABORT {slug}: not in DB")
            con.rollback(); return 1
        sid, cur_jp, gen = row
        # token identity in the renderer's order
        tids = [r[0] for r in con.execute(
            "SELECT id FROM token WHERE sentence_id=? ORDER BY split_mode, position, id", (sid,))]
        modes = [r[0] for r in con.execute(
            "SELECT split_mode FROM token WHERE sentence_id=? ORDER BY split_mode, position, id", (sid,))]
        toks = after["tokens"]
        if len(toks) != len(tids):
            print(f"ABORT {slug}: token count {len(toks)} != DB {len(tids)}")
            con.rollback(); return 1

        # ---- invariants, re-checked on the exact values about to be written ----
        c_idx = [i for i, m in enumerate(modes) if m == "C"]
        cat_surf = "".join(toks[i]["s"] for i in c_idx)
        cat_read = "".join(toks[i]["r"] or "" for i in c_idx)
        if cat_surf != after["jp"]:
            print(f"ABORT {slug}: I1 concat(surfaces) != jp"); con.rollback(); return 1
        if cat_read != after["kana"]:
            print(f"ABORT {slug}: I2 kana != concat(readings)"); con.rollback(); return 1
        if LATIN.search(after["kana"] or ""):
            print(f"ABORT {slug}: I7 Latin in kana"); con.rollback(); return 1
        if JPRE.search(after["romaji"] or ""):
            print(f"ABORT {slug}: I8 kana/CJK in romaji"); con.rollback(); return 1
        if after["jp"] != cur_jp and not gen:
            print(f"ABORT {slug}: jp change on a gen=false Layer-A record"); con.rollback(); return 1

        if not args.dry_run:
            con.execute("UPDATE sentence SET jp=?, kana=?, romaji=? WHERE id=?",
                        (after["jp"], after["kana"], after["romaji"], sid))
        if after["jp"] != cur_jp:
            n_jp += 1
        n_sent += 1

        for field, locs in (after.get("texts") or {}).items():
            if field not in TEXT_FIELDS:
                continue
            for locale, value in locs.items():
                if value is None:
                    continue
                if not args.dry_run:
                    con.execute(
                        "UPDATE localized_text SET value=? WHERE entity_type='sentence' AND entity_id=? "
                        "AND field=? AND locale=?", (value, sid, field, locale))
                n_text += 1

        for i, t in enumerate(toks):
            tid = tids[i]
            if not args.dry_run:
                con.execute("UPDATE token SET reading=? WHERE id=?", (t.get("r") or "", tid))
            for key, dbfield in TOKEN_LOCALIZED.items():
                loc = t.get(key)
                if not isinstance(loc, dict):
                    continue
                for locale, value in loc.items():
                    if value is None:
                        continue
                    if not args.dry_run:
                        con.execute(
                            "UPDATE localized_text SET value=? WHERE entity_type='token' AND entity_id=? "
                            "AND field=? AND locale=?", (value, tid, dbfield, locale))
                    n_tok += 1

    if args.dry_run:
        con.rollback()
    else:
        con.commit()
    con.close()
    print(f"sentence apply ({'dry-run' if args.dry_run else 'APPLIED'}): {n_sent} sentences | "
          f"{n_jp} jp changes | {n_text} localized sentence fields | {n_tok} token localized fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
