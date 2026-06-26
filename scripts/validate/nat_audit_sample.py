#!/usr/bin/env python3
"""Random sample of sentence translations for an AI NATURALNESS + faithfulness audit (translation_qa.md §3.3):
is the pt-BR a faithful AND natural, daily-life rendering of the Japanese (grounded by the trusted EN), or is
it stiff / literal / a particle-calque / AI-like? Writes research/derived/tr/nat/batch_*.json as
[{id, slug, jp, pt, en}]. Usage: nat_audit_sample.py [--n 400] [--batch 50]"""
from __future__ import annotations
import argparse, json, random, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--batch", type=int, default=50)
    args = ap.parse_args()
    c = sqlite3.connect(DB)
    rows = c.execute("SELECT id, slug, jp, en FROM sentence").fetchall()
    pick = random.sample(rows, min(args.n, len(rows)))
    sample = []
    for sid, slug, jp, en_col in pick:
        pt = get_text(c, "sentence", sid, "translation")
        en = en_col or get_text(c, "sentence", sid, "translation", "en")
        if pt:
            sample.append({"id": len(sample), "slug": slug, "jp": jp, "pt": pt, "en": en})
    outdir = ROOT / "research" / "derived" / "tr" / "nat"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_sample.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    print(f"naturalness sample: {len(sample)} sentences -> {nb} batches")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
