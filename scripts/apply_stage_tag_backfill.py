#!/usr/bin/env python3
"""Fill the empty `stage:` tag on the 324 mined sentences that lost it.

Same root cause as the missing English anchors (scripts/apply_en_anchor_backfill.py, commit
c7048fe6): the pt-BR authoring pass re-emitted mined rows in a narrower shape, and
ingest_mined_stages.py wrote f"stage:{r.get('stage','')}" from that artifact — so every one of the
324 records carries the literal tag "stage:" with nothing after it. The miner's own artifact
(research/derived/tatoeba_mined_stages.json, `candidates`) still records the stage each sentence
was mined for, keyed by Tatoeba id, so the value is recovered rather than guessed.

DB only (sentence.tags, a JSON list); the exporter republishes it. A record whose id is not in the
artifact is skipped loudly, never given a default. Idempotent.
Usage: apply_stage_tag_backfill.py [--check]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "db" / "corpus.sqlite"
ARTIFACT = ROOT / "research" / "derived" / "tatoeba_mined_stages.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    art = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    cands_raw = art["candidates"]
    # The artifact groups candidates BY STAGE: {"<stage>": [ {tatoeba_id, jp, en, ...}, ... ]}. A
    # record's stage is the key it sits under (its own `stage` field, when present, must agree).
    cands = []
    if isinstance(cands_raw, dict):
        for stage, lst in cands_raw.items():
            for r in lst:
                if r.get("stage") not in (None, "", stage):
                    raise SystemExit(f"artifact disagrees with itself: {r.get('tatoeba_id')} sits "
                                     f"under {stage!r} but says {r.get('stage')!r}")
                cands.append(dict(r, stage=stage))
    else:
        cands = list(cands_raw)
    stage_of = {str(c.get("tatoeba_id")): c.get("stage") for c in cands if c.get("stage") not in (None, "")}
    print(f"artifact: {len(cands)} candidates, {len(stage_of)} with a stage")

    con = sqlite3.connect(DB)
    con.execute("PRAGMA busy_timeout=60000")
    rows = con.execute("SELECT id, slug, tags FROM sentence WHERE tags LIKE '%\"stage:\"%'").fetchall()
    filled, skipped = 0, []
    for sid, slug, tags in rows:
        tid = slug.rsplit("-", 1)[-1]
        stage = stage_of.get(tid)
        if not stage:
            skipped.append(f"{slug}: not in the miner artifact — left as is")
            continue
        lst = json.loads(tags)
        new = [f"stage:{stage}" if t == "stage:" else t for t in lst]
        if not args.check:
            con.execute("UPDATE sentence SET tags=? WHERE id=?", (json.dumps(new, ensure_ascii=False), sid))
        filled += 1
    if not args.check:
        con.commit()
    left = con.execute("SELECT COUNT(*) FROM sentence WHERE tags LIKE '%\"stage:\"%'").fetchone()[0]
    con.close()
    verb = "would fill" if args.check else "filled"
    print(f"{verb} {filled} of {len(rows)}; empty stage tags remaining: {left if not args.check else len(rows)}")
    for s in skipped[:10]:
        print(f"  ! {s}")
    if len(skipped) > 10:
        print(f"  ! ... {len(skipped) - 10} more")
    return 1 if (args.check and filled) else (2 if skipped else 0)


if __name__ == "__main__":
    sys.exit(main())
