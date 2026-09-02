#!/usr/bin/env python3
"""State the う→わ exception in the four formation rules that omit it.

A godan verb forms its causative/passive on the あ-row of its final kana, and four records say so —
but verbs ending in う are the exception: 買う goes to 買わ, not to a non-existent 買あ. Without the
exception the rule as written produces ×買あせる, ×買あれる, ×買あせられる. That is the worst defect class
this corpus has, because the learner is not misinformed about a fact, they are taught to PRODUCE
something wrong.

It is also a provable internal inconsistency rather than a judgement call: `gram:gp-7` already states
the exception in the corpus's own words ("exceção: verbos em -う viram -わ (買う kau → 買わない, não
買あない)"), and scripts/ingest/conjugate.py has always had it right — its godan table maps
"う" -> ("わ", ...). So the drill DATA a learner practises against is correct and only the prose they
read is wrong; the two disagreed and nothing checked.

The wording added here mirrors gp-7's, so the house phrasing stays consistent.

Both layers are written: the DB (localized_text, which the exporter reads) is the source, and
corpus/grammar/*.json is regenerated afterwards by scripts/export/export_corpus.py.
Idempotent, exact-match, loud skips. Usage: apply_godan_u_exception.py [--check]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")

# (grammar key, exact substring to find, replacement carrying the exception)
FIXES = [
    ("gp-105",
     "troca-se a sílaba final pela linha 〜あ + せる. Ex.: 行(い)く→行かせる, 飲(の)む→飲ませる, "
     "待(ま)つ→待たせる.",
     "troca-se a sílaba final pela linha 〜あ + せる. Ex.: 行(い)く→行かせる, 飲(の)む→飲ませる, "
     "待(ま)つ→待たせる. Exceção: verbos terminados em -う viram -わ (買(か)う→買わせる, não 買あせる)."),
    ("gp-63",
     "troca-se a sílaba final em -u por -areru: 書く→書かれる, 読む→読まれる, 話す→話される.",
     "troca-se a sílaba final em -u por -areru: 書く→書かれる, 読む→読まれる, 話す→話される. "
     "Exceção: verbos terminados em -う viram -わ (買う→買われる, não 買あれる)."),
    ("saserareru",
     "troca-se a última sílaba pela linha あ + せられる (書く → 書かせられる)",
     "troca-se a última sílaba pela linha あ + せられる (書く → 書かせられる; exceção: verbos em -う "
     "viram -わ, 買う → 買わせられる)"),
    ("saseru",
     "última sílaba para a linha あ + せる (飲む → 飲ませる, 書く → 書かせる).",
     "última sílaba para a linha あ + せる (飲む → 飲ませる, 書く → 書かせる); exceção: verbos "
     "terminados em -う viram -わ (買う → 買わせる, não 買あせる)."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")

    changed, done, skipped = 0, 0, []
    for key, old, new in FIXES:
        row = con.execute("SELECT id FROM grammar_point WHERE key=?", (key,)).fetchone()
        if not row:
            skipped.append(f"{key}: no such grammar point")
            continue
        gid = row[0]
        r = con.execute("SELECT value FROM localized_text WHERE entity_type='grammar_point' "
                        "AND entity_id=? AND field='formation' AND locale='pt-BR'", (gid,)).fetchone()
        if not r:
            skipped.append(f"{key}: no pt-BR formation row")
            continue
        cur = r[0]
        if new in cur:
            done += 1
            continue
        if old not in cur:
            skipped.append(f"{key}: the expected rule text is not present — not touching it")
            continue
        print(f"  {key}: + う→わ exception")
        if not args.check:
            con.execute("UPDATE localized_text SET value=? WHERE entity_type='grammar_point' "
                        "AND entity_id=? AND field='formation' AND locale='pt-BR'",
                        (cur.replace(old, new), gid))
        changed += 1

    if not args.check:
        con.commit()
    con.close()
    verb = "would state" if args.check else "stated"
    print(f"\n{verb} the exception in {changed} rule(s); {done} already correct")
    for s in skipped:
        print(f"  ! {s}")
    return 1 if (args.check and changed) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
