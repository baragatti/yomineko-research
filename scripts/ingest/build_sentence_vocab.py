#!/usr/bin/env python3
"""Rebuild `sentence_vocab` as the UNION of the THREE rules that actually built it. Never deletes.

WHY THIS SCRIPT EXISTS
----------------------
`sentence_vocab` was never a projection of `token.vocab_id`. It was the union of three passes:

  R1  token links      — DISTINCT (sentence_id, token.vocab_id) for split_mode='C' (the dissector).
  R2  token runs       — scripts/ingest/relink_vocab.py, 2026-06-15 (commit 64a5218, "+5604 edges"):
                         every contiguous run of 1..5 C-token surfaces that equals a vocab headword /
                         kana / vocab_form, linking EVERY vocab record that owns that form.
  R3  lemma tagger     — the N3 link-enrichment pass of 2026-07-05 (commit 9cd6ab7, "+1582 links"),
                         whose script was NEVER COMMITTED: `token.lemma == vocab.headword`, Sudachi
                         dictionary forms, exact match, no fuzzy matching. Reconstructed here.

On 2026-08-19 two scripts — scripts/fix_homophone_vocab_links.py (294fe90) and
scripts/apply_redissect_round2.py (c9d54f0) — each ran `DELETE FROM sentence_vocab` followed by a
rebuild from `token.vocab_id` alone, believing the table was a derived projection of R1. That thinned
it from the ~31.8k rows reports/stats.md recorded to exactly the 20,357-row R1 subset and destroyed
R2's and R3's output. 436 (sentence_id, vocab_id) pairs that the COMMITTED exam banks depend on went
missing (n3 361 / n4 58 / n5 17), and a rebuild of build_exam_banks.py collapses n3_context_fill from
400 items to 97. The committed corpus JSON is the source of truth; the index had regressed.

THE HISTORICAL GATES ARE PART OF THE RULE, NOT AN OPTIMISATION
--------------------------------------------------------------
R2 is gated to `vocab.level IN ('n5','n4')` and R3 to `vocab.level='n3'` because that is the registry
each pass actually ran against. In June 2026 the vocab registry held 1,358 n5+n4 entries; it now holds
7,401 across n5..n1. Running R2's rule ungated against today's registry yields ~70,960 links, two
thirds of them to N2/N1 words the corpus explicitly does not teach in sentences. The gates reproduce
the historical link set; they are not a tuning knob.

FORBIDDEN SIDE EFFECT — THIS SCRIPT MUST NEVER RECOMPUTE SENTENCE LEVELS
------------------------------------------------------------------------
`persist_dissection.recompute_all_levels()` derives `sentence.level` from `sentence_vocab` ∪
`sentence_kanji`. It is DELIBERATELY NOT CALLED HERE, and must never be added. Recomputing levels
after this repair moves 589 sentences away from the committed corpus/sentences/bank.json (478 n4→n3,
69 n5→n3, 33 n5→n4), because the restored n3 links raise sentences the course currently teaches at
n4 — and export_corpus.py would then write those levels straight into the source-of-truth JSON.
Re-deriving sentence levels is a separate, reviewed decision with its own export diff, never a side
effect of repairing an index. (This is also why relink_vocab.py — which ends in recompute_all_levels
against the whole ungated registry — must not be re-run as it stands.)

PROVENANCE COLUMNS
------------------
  link_rule        'token' | 'run' | 'lemma' — which rule first produced the row. Rows that predate
                   this script are backfilled 'token' (the table today IS exactly R1, verified by a
                   set-difference of 0 in both directions).
  reading_verified 1 when the anchoring token's realized reading agrees exactly with vocab.kana or a
                   kana vocab_form of that record (katakana normalised to hiragana), else 0. The
                   anchor is the token carrying the id (R1), the concatenated run (R2), or the token
                   whose lemma matched (R3); a link is verified if ANY of its anchors agrees.

                   MEASURED, NOT ASSUMED: pre-existing token-rule rows are NOT reading-verified by
                   construction. Of the 20,357, only 14,933 (73.4%) agree exactly; 1,210 (5.9%) are
                   inflected anchors whose realized reading is a prefix of the dictionary reading
                   (食べ/たべ for 食べる/たべる) and 4,214 (20.7%) genuinely disagree (年 read ねん
                   linked to 年/とし, 深い read ぶかい by rendaku, 止める read とめる linked to やめる).
                   So the flag is computed for every row rather than hardcoded, and
                   reading_verified=0 means "not confirmed", NOT "wrong": inflection and rendaku land
                   there too. ~177 of the RESTORED links are reading-blind attributions that the
                   committed banks rest on; restoring them is deliberate.

Idempotent: INSERT OR IGNORE only, so a second run inserts 0 rows.
Usage: build_sentence_vocab.py [--db PATH]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = db_target(ROOT / "db" / "corpus.sqlite")

MAXW = 5           # longest vocab span in tokens (お祖父さん etc.) — relink_vocab.py's window
R2_LEVELS = ("n5", "n4")   # the registry relink_vocab.py ran against on 2026-06-15
R3_LEVEL = "n3"            # the July 2026 lemma tagger's gate

KATA_A, KATA_Z = 0x30A1, 0x30F6


def hira(s: str) -> str:
    """Katakana -> hiragana. token.reading is stored in hiragana; vocab.kana keeps katakana for
    loanwords (544 records), so the two are only comparable after normalisation."""
    if not s:
        return ""
    return "".join(chr(ord(c) - 0x60) if KATA_A <= ord(c) <= KATA_Z else c for c in s)


def kana_only(s: str) -> bool:
    return bool(s) and all("ぁ" <= c <= "ゟ" or "ァ" <= c <= "ヿ" or c == "ー"
                           for c in s)


def ensure_columns(con: sqlite3.Connection) -> None:
    """Add the provenance columns if absent and backfill pre-existing rows as the token rule."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(sentence_vocab)")}
    if "link_rule" not in cols:
        con.execute("ALTER TABLE sentence_vocab ADD COLUMN link_rule TEXT")
        print("  schema: added sentence_vocab.link_rule")
    if "reading_verified" not in cols:
        con.execute("ALTER TABLE sentence_vocab ADD COLUMN reading_verified INTEGER")
        print("  schema: added sentence_vocab.reading_verified")
    n = con.execute("UPDATE sentence_vocab SET link_rule='token' WHERE link_rule IS NULL").rowcount
    if n:
        print(f"  schema: backfilled link_rule='token' on {n} pre-existing rows")


def readings_by_vocab(con: sqlite3.Connection) -> dict[int, set[str]]:
    """vocab_id -> {normalised dictionary readings} = vocab.kana + every all-kana vocab_form."""
    out: dict[int, set[str]] = defaultdict(set)
    for vid, kana in con.execute("SELECT id,kana FROM vocab"):
        if kana:
            out[vid].add(hira(kana))
    for vid, form in con.execute("SELECT vocab_id,form FROM vocab_form"):
        if kana_only(form or ""):
            out[vid].add(hira(form))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DB), help="database to repair (default: db/corpus.sqlite)")
    args = ap.parse_args()

    con = sqlite3.connect(args.db, isolation_level=None)
    con.execute("PRAGMA busy_timeout=60000")   # another process may write other tables concurrently
    con.execute("BEGIN IMMEDIATE")
    try:
        ensure_columns(con)

        read = readings_by_vocab(con)
        # form -> {vocab_id}: MULTI-VALUED, exactly as relink_vocab.py builds it. Every vocab sharing a
        # written form links (此処 & ここ both carry ここ). Gated to the n5/n4 registry of 2026-06-15.
        gate = ",".join("?" * len(R2_LEVELS))
        by_form: dict[str, set[int]] = defaultdict(set)
        for q in (f"SELECT f.form, f.vocab_id FROM vocab_form f JOIN vocab v ON v.id=f.vocab_id "
                  f"WHERE v.level IN ({gate})",
                  f"SELECT headword, id FROM vocab WHERE level IN ({gate})",
                  f"SELECT kana, id FROM vocab WHERE level IN ({gate})"):
            for form, vid in con.execute(q, R2_LEVELS):
                if form:
                    by_form[form].add(vid)
        # headword -> {vocab_id} for the n3 lemma tagger (exact match, no fuzz)
        by_head_n3: dict[str, set[int]] = defaultdict(set)
        for hw, vid in con.execute("SELECT headword, id FROM vocab WHERE level=?", (R3_LEVEL,)):
            if hw:
                by_head_n3[hw].add(vid)

        toks: dict[int, list[tuple[str, str, str]]] = defaultdict(list)
        for sid, surf, lemma, rdg in con.execute(
                "SELECT sentence_id,surface,lemma,reading FROM token "
                "WHERE split_mode='C' ORDER BY sentence_id,position"):
            toks[sid].append((surf or "", lemma or "", rdg or ""))

        # ---- R1: the dissector's own token links ------------------------------------------------
        r1: dict[tuple[int, int], bool] = {}
        for sid, vid, rdg in con.execute(
                "SELECT DISTINCT sentence_id,vocab_id,reading FROM token "
                "WHERE split_mode='C' AND vocab_id IS NOT NULL"):
            ok = hira(rdg or "") in read.get(vid, ())
            r1[(sid, vid)] = r1.get((sid, vid), False) or ok

        # ---- R2: contiguous 1..5-token runs matching a known form (n5/n4 registry) ---------------
        r2: dict[tuple[int, int], bool] = {}
        for sid, tl in toks.items():
            n = len(tl)
            for i in range(n):
                run = rd = ""
                for w in range(MAXW):
                    if i + w >= n:
                        break
                    run += tl[i + w][0]
                    rd += tl[i + w][2]
                    for vid in by_form.get(run, ()):
                        ok = hira(rd) in read.get(vid, ())
                        r2[(sid, vid)] = r2.get((sid, vid), False) or ok

        # ---- R3: token.lemma == n3 vocab.headword ------------------------------------------------
        r3: dict[tuple[int, int], bool] = {}
        for sid, tl in toks.items():
            for _surf, lemma, rdg in tl:
                for vid in by_head_n3.get(lemma, ()):
                    ok = hira(rdg) in read.get(vid, ())
                    r3[(sid, vid)] = r3.get((sid, vid), False) or ok

        # a link is reading-verified if ANY rule that produces it has an agreeing anchor
        verified: dict[tuple[int, int], bool] = {}
        for d in (r1, r2, r3):
            for k, v in d.items():
                verified[k] = verified.get(k, False) or v

        before = con.execute("SELECT count(*) FROM sentence_vocab").fetchone()[0]
        cur = con.cursor()
        stats: dict[str, dict[str, int]] = {}
        for rule, pairs in (("token", r1), ("run", r2), ("lemma", r3)):
            ins = skip = 0
            for (sid, vid) in pairs:
                cur.execute(
                    "INSERT OR IGNORE INTO sentence_vocab (sentence_id,vocab_id,link_rule,reading_verified) "
                    "VALUES (?,?,?,?)", (sid, vid, rule, 1 if verified[(sid, vid)] else 0))
                if cur.rowcount == 1:
                    ins += 1
                else:
                    skip += 1
            stats[rule] = {"computed": len(pairs), "inserted": ins, "skipped": skip}

        # pre-existing rows carry no reading_verified yet — compute it the same way, never hardcode
        back = 0
        for sid, vid in con.execute(
                "SELECT sentence_id,vocab_id FROM sentence_vocab WHERE reading_verified IS NULL").fetchall():
            cur.execute("UPDATE sentence_vocab SET reading_verified=? WHERE sentence_id=? AND vocab_id=?",
                        (1 if verified.get((sid, vid), False) else 0, sid, vid))
            back += 1
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise

    after = con.execute("SELECT count(*) FROM sentence_vocab").fetchone()[0]
    print(f"build_sentence_vocab: {before} -> {after} rows (+{after - before})")
    for rule in ("token", "run", "lemma"):
        s = stats[rule]
        print(f"  R-{rule:<5s} computed {s['computed']:6d}  inserted {s['inserted']:6d}  "
              f"already present {s['skipped']:6d}")
    if back:
        print(f"  reading_verified backfilled on {back} pre-existing rows")
    for rule, rv, n in con.execute(
            "SELECT link_rule,reading_verified,count(*) FROM sentence_vocab "
            "GROUP BY link_rule,reading_verified ORDER BY link_rule,reading_verified"):
        print(f"  link_rule={rule:<6s} reading_verified={rv}  {n:6d}")
    tot1 = con.execute("SELECT count(*) FROM sentence_vocab WHERE reading_verified=1").fetchone()[0]
    print(f"  reading_verified: {tot1} verified / {after - tot1} unverified "
          f"(unverified includes inflected and rendaku anchors — not an error flag)")
    print("  NOTE: sentence levels were NOT recomputed (see this file's docstring).")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
