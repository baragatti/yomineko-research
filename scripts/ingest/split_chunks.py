#!/usr/bin/env python3
"""Split a chunks JSON (array of chunks) into per-chunk files chunk_0000.json … in a directory.
Per-chunk files give each Workflow agent an unambiguous unique input (avoids index mis-reads).
Usage: split_chunks.py <chunks.json> <outdir>"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    chunks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outdir = ROOT / sys.argv[2]
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("chunk_*.json"):
        f.unlink()
    for i, ch in enumerate(chunks):
        (outdir / f"chunk_{i:04d}.json").write_text(json.dumps(ch, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(chunks)} chunk files to {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
