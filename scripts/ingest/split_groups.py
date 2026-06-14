#!/usr/bin/env python3
"""P5 scaling step 2 (batched engine) — split a batch JSON into GROUP files of K sentences each.

Each group file holds an array of K sentence skeletons; one dissection agent processes one group and
returns an array of results keyed by `slug` (slug-keying, not array index, avoids cross-contamination).
This amortizes per-agent overhead ~Kx vs one-agent-per-sentence while staying small enough to read
reliably. Usage: split_groups.py <batch.json> <out_dir> [K=5]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    batch_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    items = json.loads(batch_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("group_*.json"):
        f.unlink()
    n = 0
    for i in range(0, len(items), k):
        group = items[i:i + k]
        (out_dir / f"group_{n:04d}.json").write_text(
            json.dumps(group, ensure_ascii=False, indent=2), encoding="utf-8")
        n += 1
    print(f"split {len(items)} sentences -> {n} group files (K={k}) in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
