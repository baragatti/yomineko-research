#!/usr/bin/env python3
"""Apply the round-3 romaji-dispute fixes. Closes the last 9 I3 violations in the bank.

fix_stale_token_romaji.py repaired 327 of 336 I3-violating sentences by recomputing token romaji and
accepting only where the recompute reproduced the audited sentence romaji byte for byte. The remaining 9
were deliberately left alone because the sentence and its tokens disagreed about a READING, not about
romanization, and rewriting romaji there would have hidden a reading error.

A dedicated pass settled each of those nine. Its core finding: the token READING field is already
correct in all nine and the ROMAJI field is the stale one. All nine already satisfy I1 (token surfaces
concatenate to jp) and I2 (token readings concatenate to kana), so the reading questions were already
answered by fields the records hold; only the derived romaji line was wrong.

Readings decided, for the record:
  jec-4408      17日 is a DATE, read as one number: じゅうなな, and 日 is にち above 十日 (was ichinana/ka)
  8938683       the sentence exists to contrast 13 with 30, so じゅうさん and さんじゅう, not per-digit
  74887         結 inside 結納品 is ゆい, not ketsu
  11727272      辛い here is からい (taste), not つらい (hardship) — vocab_id 173 is already the からい entry
  11248814      入れる is はいれる, the POTENTIAL of 入る, licensed by が and by the Layer-A English "enter"
  three others  何 before を / 言おう / 考え is なに, not なん

Five of the nine also need the SENTENCE romaji corrected alongside their tokens: two drop the particle
っけ and double the trailing punctuation, two drop って, one carries a spurious comma. Corpus-wide counts
prove these are artifacts rather than conventions: 15 of 17 っけ sentences spell kke, 510 of 512 って
sentences spell tte, and the only four sentences in the whole bank with doubled ASCII punctuation are
all in this dispute set.

Every edit is resolved on the PARSED row by (slug, split_mode='C', position) — never by text
replacement, since values like 'nan' occur throughout the bank.

Usage: apply_romaji_disputes.py [--apply]
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "derived" / "qa_queues" / "round3" / "romaji_disputes.json"
DB = ROOT / "db" / "corpus.sqlite"
TOKEN_FIELD = re.compile(r"^tokens\[position=(\d+)\]\.(romaji|reading)$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = [r for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"] if r["verdict"] == "fix"]
    con = sqlite3.connect(DB)
    sid_of = {s: i for s, i in con.execute("SELECT slug,id FROM sentence")}
    applied, skipped = Counter(), []

    for r in rows:
        slug = r["id"].split("#", 1)[0]
        field, cur, fix = r.get("field") or "", r.get("current") or "", r.get("fix") or ""
        sid = sid_of.get(slug)
        if not sid:
            skipped.append((r["id"], "unknown sentence")); continue

        m = TOKEN_FIELD.match(field)
        if m:
            pos, col = int(m.group(1)), m.group(2)
            row = con.execute(f"SELECT id,{col},surface FROM token WHERE sentence_id=? AND "
                              f"split_mode='C' AND position=?", (sid, pos)).fetchone()
            if not row:
                skipped.append((r["id"], f"no C token at position {pos}")); continue
            tid, stored, surf = row
            if (stored or "") != cur:
                skipped.append((r["id"], f"holds {stored!r}, expected {cur!r}")); continue
            if args.apply:
                con.execute(f"UPDATE token SET {col}=? WHERE id=?", (fix, tid))
            applied.update([f"token.{col}"])
        elif field == "romaji":
            stored = con.execute("SELECT romaji FROM sentence WHERE id=?", (sid,)).fetchone()[0] or ""
            if stored != cur:
                skipped.append((r["id"], "sentence romaji does not match the anchor")); continue
            if args.apply:
                con.execute("UPDATE sentence SET romaji=? WHERE id=?", (fix, sid))
            applied.update(["sentence.romaji"])
        else:
            skipped.append((r["id"], f"unmapped field {field}"))

    if args.apply:
        con.commit()

    # The point of the whole exercise: report I3 across the bank afterwards.
    bad = 0
    for sid, ro in con.execute("SELECT id,romaji FROM sentence"):
        cat = "".join(x[0] or "" for x in con.execute(
            "SELECT romaji FROM token WHERE sentence_id=? AND split_mode='C' ORDER BY position", (sid,)))
        if cat != (ro or ""):
            bad += 1
    print(f"romaji disputes ({'APPLIED' if args.apply else 'dry-run'}): "
          f"{sum(applied.values())}/{len(rows)} {dict(applied)}")
    print(f"I3 violations in the bank: {bad}")
    for k, w in skipped:
        print(f"   skip {k}: {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
