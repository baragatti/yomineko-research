#!/usr/bin/env python3
"""Rebuild the entire sentence bank from saved AI results — NO new agent calls.

The durable AI output is the set of `research/derived/*_result.json` files (Layer-B authored by the
dissection workflows). The skeleton (tokens/romaji/kana/pos/inflection/particle-function — all Layer A)
is RE-DERIVED by dissect.py at persist time. So after any mechanical change to the skeleton (e.g. the
sokuon-romaji fix, new neutral enums), this script wipes the bank and re-persists every saved
(batch, result) pair, then re-applies the deterministic particle-link + gloss repair, validates, and
exports. Result: the bank reflects the new schema with the original AI content intact, at zero token cost.

Usage: replay_all.py
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from persist_batch import persist_pair  # noqa: E402
from reset_sentences import main as reset_main  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
DERIVED = ROOT / "derived" if (ROOT / "derived").exists() else ROOT / "research" / "derived"


def main() -> int:
    reset_main()  # clear sentence bank + dependent tables
    pairs = []
    for batch in sorted(DERIVED.glob("batch_*.json")):
        if batch.name.endswith("_result.json"):
            continue
        result = batch.with_name(batch.stem + "_result.json")
        if result.exists():
            pairs.append((batch, result))
    print(f"replaying {len(pairs)} saved (batch, result) pairs from {DERIVED}")
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    diss = Dissector()
    tot = 0
    for batch, result in pairs:
        p, unf, miss = persist_pair(con, diss, batch, result)
        tot += p
        print(f"  {batch.stem}: +{p} (unfaithful={len(unf)} missing={miss})")
    con.close()
    print(f"replay complete: {tot} sentences persisted")
    # deterministic post-steps (not in saved results)
    py = sys.executable
    here = str(Path(__file__).resolve().parent)
    subprocess.run([py, f"{here}/relink_vocab.py"], check=False)       # multi-token vocab links
    subprocess.run([py, f"{here}/particle_link.py", "--target", "8"], check=False)
    subprocess.run([py, f"{here}/repair_glosses.py"], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
