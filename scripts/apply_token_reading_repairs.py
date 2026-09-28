#!/usr/bin/env python3
"""Q3 — apply the mechanical rows of the token reading audit and rebuild each touched sentence's kana/romaji.

WHAT WAS WRONG
--------------
A C token's `reading` is Sudachi's context-free guess, and the same field builds sentence.kana (I2:
kana == concat of the C readings) and, through token romaji, sentence.romaji (I3). The audit
(research/derived/repairs/token_reading_audit.json, scripts of commit 4f4a4a38) found 310 tokens whose
stored reading contradicts the context: 何 stored なん before か/も/が/を (なに), numerals read digit
by digit or without the counter's sound change (２０年 にれい, 一分 いちふん, ２切れ に), 〜中 'all over'
read ちゅう, and readings that disagree with a verified token link (米 べい -> こめ, 開く ひらく -> あく).

WHAT THIS WRITES (db/corpus.sqlite; the exporters republish corpus/ and course/)
  1. token.reading + token.romaji of the 295 `class: mechanical` rows, addressed by (sentence slug,
     C position) under the table's replay guard: the token must read `surface` and hold the row's old
     reading/romaji (or already the new ones: idempotent). The 15 `review` rows are NOT applied.
  2. the split_mode='A' sub-tokens at the same position for rows carrying `a_tokens` (一回 いち|かい ->
     いっ|かい), guarded the same way.
  3. sentence.kana / sentence.romaji of every sentence a mechanical row touches, rebuilt as the concat
     of its C readings / C romaji. Guard: the stored value is the table's `kana_old`/`romaji_old` (or
     already the rebuilt one). Where every row of the sentence is mechanical the rebuilt value must
     equal the table's `kana_new`/`romaji_new`, so the rebuild is re-proved against the audit.

Layer A has no authoring file for these readings (the dissector produces them on every replay), so the
index is the only home and this step re-asserts them after every sentence writer. Token links are not
touched: the 16 rows whose record no longer reads the new way are link work (see the Q3 report).

Refuses (exit 1, nothing committed) on any guard failure. Out of scope on an empty sentence table.
Usage: apply_token_reading_repairs.py [--check] [--table PATH]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
TABLE = ROOT / "research" / "derived" / "repairs" / "token_reading_audit.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="report what would change; write nothing")
    ap.add_argument("--table", type=Path, default=TABLE)
    args = ap.parse_args()
    doc = json.loads(args.table.read_text(encoding="utf-8"))
    if doc.get("row_count") != len(doc["rows"]):
        raise SystemExit(f"{args.table.name}: row_count {doc.get('row_count')} != {len(doc['rows'])}")
    mech = [r for r in doc["rows"] if r["class"] == "mechanical"]
    classes_of: dict[str, set[str]] = defaultdict(set)
    for r in doc["rows"]:
        classes_of[r["sentence"]].add(r["class"])

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    if not con.execute("SELECT 1 FROM sentence LIMIT 1").fetchone():
        print(f"apply_token_reading_repairs: {len(mech)} rows out of scope (empty sentence table)")
        return 0
    sid_of = dict(con.execute("SELECT slug, id FROM sentence"))
    errors: list[str] = []
    wrote_tok = wrote_a = wrote_sent = 0

    def concat(sid: int) -> tuple[str, str]:
        toks = con.execute("SELECT reading, romaji FROM token WHERE sentence_id=? AND split_mode='C' "
                           "ORDER BY position", (sid,)).fetchall()
        return "".join(t[0] or "" for t in toks), "".join(t[1] or "" for t in toks)

    # Q6 checkpoint (full replay). Two replay-only differences the live index does not show: (a) the
    # romaji of a punctuation token is '.'/',' on a replay and '。'/'、' on 4,361 live tokens (the live
    # index is mixed), so romaji is compared modulo punctuation; (b) a live sentence row could already
    # carry the repaired kana while its token did not (sent:gen-9f80f08cc644: I2 false before Q3), and
    # a replay's sentence row agrees with its pre-repair tokens instead. Both old states are accepted.
    def pn(romaji: str) -> str:
        return unicodedata.normalize("NFKC", romaji or "").replace("。", ".").replace("、", ",")

    pre = {slug: concat(sid_of[slug]) for slug in {r["sentence"] for r in mech} if slug in sid_of}

    for r in mech:
        addr = f"{r['sentence']} @{r['position']} {r['surface']}"
        sid = sid_of.get(r["sentence"])
        row = sid and con.execute(
            "SELECT id, surface, reading, romaji FROM token WHERE sentence_id=? AND split_mode='C' "
            "AND position=?", (sid, r["position"])).fetchone()
        if not row or row[1] != r["surface"]:
            errors.append(f"{addr}: no C token with that surface ({row and row[1]!r})")
            continue
        tid, _, rdg, ro = row
        if (rdg, ro) == (r["new_reading"], r["new_romaji"]):
            pass
        elif (rdg, ro) == (r["old_reading"], r["old_romaji"]):
            con.execute("UPDATE token SET reading=?, romaji=? WHERE id=?", (r["new_reading"], r["new_romaji"], tid))
            wrote_tok += 1
        else:
            errors.append(f"{addr}: holds {rdg!r}/{ro!r}, expected {r['old_reading']!r}/{r['old_romaji']!r}")
            continue
        if r.get("a_tokens"):
            subs = con.execute("SELECT id, surface, reading FROM token WHERE sentence_id=? AND split_mode='A' "
                               "AND position=? ORDER BY id", (sid, r["position"])).fetchall()
            if [s[1] for s in subs] != [a["surface"] for a in r["a_tokens"]]:
                errors.append(f"{addr}: A sub-tokens {[s[1] for s in subs]} differ from the table")
                continue
            for (aid, _, ardg), a in zip(subs, r["a_tokens"]):
                if ardg == a["new_reading"]:
                    continue
                if ardg != a["old_reading"]:
                    errors.append(f"{addr}: A token {a['surface']} holds {ardg!r}")
                    continue
                con.execute("UPDATE token SET reading=? WHERE id=?", (a["new_reading"], aid))
                wrote_a += 1

    for slug in sorted({r["sentence"] for r in mech}):
        s = doc["sentences"][slug]
        sid = sid_of[slug]
        kana, romaji = concat(sid)
        if classes_of[slug] == {"mechanical"} and (kana, pn(romaji)) != (s["kana_new"], pn(s["romaji_new"])):
            errors.append(f"{slug}: rebuilt {kana!r}/{romaji!r} != table {s['kana_new']!r}/{s['romaji_new']!r}")
            continue
        cur = con.execute("SELECT kana, romaji FROM sentence WHERE id=?", (sid,)).fetchone()
        if cur == (kana, romaji):
            continue
        if (cur[0], pn(cur[1])) not in {(s["kana_old"], pn(s["romaji_old"])), (pre[slug][0], pn(pre[slug][1]))}:
            errors.append(f"{slug}: sentence holds {cur!r}, expected the table's kana_old/romaji_old")
            continue
        con.execute("UPDATE sentence SET kana=?, romaji=? WHERE id=?", (kana, romaji, sid))
        wrote_sent += 1

    if errors:
        con.rollback()
        for e in errors[:30]:
            print(f"  REFUSE {e}")
        print(f"apply_token_reading_repairs: {len(errors)} guard failure(s); nothing written")
        return 1
    if args.check:
        con.rollback()
    else:
        con.commit()
    print(f"apply_token_reading_repairs ({'check' if args.check else 'applied'}): {len(mech)} mechanical rows "
          f"({len(doc['rows']) - len(mech)} review rows held): tokens {wrote_tok}, A sub-tokens {wrote_a}, "
          f"sentences {wrote_sent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
