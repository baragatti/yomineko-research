#!/usr/bin/env python3
"""Capability-registry gate: ids unique; every grammar key mapped to EXACTLY ONE capability; every capability
key exists in grammar_point; lesson_map lessons + capability refs resolve. Exit 1 on failure."""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAPD = ROOT / "corpus" / "capabilities"


def main() -> int:
    if not (CAPD / "registry.json").exists():
        print("validate_capabilities: no registry (skip)")
        return 0
    reg = json.loads((CAPD / "registry.json").read_text(encoding="utf-8"))
    lmap = json.loads((CAPD / "lesson_map.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    # A merged loser keeps its row as a redirect (deprecated_by = survivor, W08) and is not
    # an active point: no capability should map it, and the survivor carries its coverage.
    cols = {r[1] for r in con.execute("PRAGMA table_info(grammar_point)")}
    where = " WHERE deprecated_by IS NULL" if "deprecated_by" in cols else ""
    gkeys = {r[0] for r in con.execute("SELECT key FROM grammar_point" + where)}
    lslugs = {r[0] for r in con.execute("SELECT slug FROM lesson")}
    fails = []
    ids = [c["id"] for c in reg]
    if len(ids) != len(set(ids)):
        fails.append("duplicate capability ids")
    seen: dict = {}
    for c in reg:
        for k in c["grammar_keys"]:
            if k not in gkeys:
                fails.append(f"{c['id']}: unknown grammar key {k}")
            if k in seen:
                fails.append(f"grammar key {k} in two capabilities: {seen[k]} + {c['id']}")
            seen[k] = c["id"]
    unmapped = gkeys - set(seen)
    if unmapped:
        fails.append(f"{len(unmapped)} grammar keys unmapped: {sorted(unmapped)[:6]}")
    idset = set(ids)
    for slug, caps in lmap.items():
        if slug not in lslugs:
            fails.append(f"lesson_map: unknown lesson {slug}")
        for cp in caps:
            if cp not in idset:
                fails.append(f"lesson_map {slug}: unknown capability {cp}")
    con.close()
    for f in fails[:10]:
        print("  FAIL", f)
    print(f"\nvalidate_capabilities: {len(reg)} caps, {len(lmap)} lessons, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
