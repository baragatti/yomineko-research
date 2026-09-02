#!/usr/bin/env python3
"""Repair two grammar explanations that earlier applier rounds corrupted. Found by the QA-queues pass.

Both are the SAME failure class this project has guarded against since Phase 3 — a fix phrased as an
INSTRUCTION reaching a data field — except these two got past the guard and shipped, so a learner reads
them.

  gram:teiru-tokoro   explanation.pt-BR ends with the literal edit order
                      'Substituir a frase final por: "..."', escaped quotes and all. The instruction is
                      wrapped around the very sentence it is asking for, so the repair is to keep the
                      quoted value and drop the order around it.

  gram:cha-ikenai-ja-ikenai   explanation.pt-BR has the CORRECTED sentence appended while the false one
                      it was meant to replace is still in front of it, so the entry states both:
                      "ちゃいけない vem de verbos de ação" immediately followed by
                      "ちゃいけない vem de verbos cuja forma-て termina em て". The false clause is a
                      formation rule that licenses *飲んちゃいけない, so it is the one to delete.

Anchored, idempotent and narrow: each edit matches a byte-exact substring and does nothing if the
substring is absent, so re-running after a rebuild is safe. Writes the DB; run export_corpus.py after.

Usage: fix_instruction_leak_grammar.py [--apply]
"""
from __future__ import annotations
import argparse, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = db_target(ROOT / "db" / "corpus.sqlite")
# The order wraps its own replacement text; capture it and keep only that.
ORDER = re.compile(r'\s*Substituir a frase final por:\s*"(.+)"\s*$', re.S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    changed = []

    for slug in ("gram:teiru-tokoro", "gram:cha-ikenai-ja-ikenai"):
        row = con.execute(
            "SELECT g.id,l.value FROM localized_text l JOIN grammar_point g ON g.id=l.entity_id "
            "WHERE l.entity_type='grammar_point' AND l.field='explanation' AND l.locale='pt-BR' "
            "AND g.slug=?", (slug,)).fetchone()
        if not row:
            print(f"  {slug}: no pt-BR explanation")
            continue
        gid, val = row
        new = val

        m = ORDER.search(new)
        if m:
            kept = m.group(1).replace('\\"', '"').strip()
            new = new[:m.start()].rstrip() + " " + kept
            changed.append((slug, "dropped the edit order, kept its replacement sentence"))

        # The false formation clause, deleted only when the corrected one is present to replace it.
        false_clause = "ちゃいけない vem de verbos de ação"
        true_clause = "forma-て termina em て"
        if false_clause in new and true_clause in new:
            for sep in ("。", ". ", "; "):
                i = new.find(false_clause)
                j = new.find(sep, i)
                if j != -1:
                    new = (new[:i] + new[j + len(sep):]).strip()
                    changed.append((slug, "deleted the stale false formation clause"))
                    break

        if new != val:
            if args.apply:
                con.execute(
                    "UPDATE localized_text SET value=? WHERE entity_type='grammar_point' AND "
                    "entity_id=? AND field='explanation' AND locale='pt-BR'", (new, gid))
            print(f"  {slug}: {len(val)} -> {len(new)} chars")
            print(f"     now ends: ...{new[-110:]}")
        else:
            print(f"  {slug}: nothing to do (already clean)")

    if args.apply:
        con.commit()
    print(f"instruction-leak repair ({'APPLIED' if args.apply else 'dry-run'}): {len(changed)} edits")
    for s, w in changed:
        print(f"   {s}: {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
