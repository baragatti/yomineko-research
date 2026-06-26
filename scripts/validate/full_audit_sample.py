#!/usr/bin/env python3
"""Full-corpus sentence audit sample: EVERY sentence with its jp, trusted en, natural pt, and literal pt, so
one agent pass can judge (a) the natural translation's faithfulness+naturalness and (b) the literal
translation's literal-correctness (translation_qa.md §3.3/§3.4). Writes research/derived/tr/full/batch_*.json.
Usage: full_audit_sample.py [--batch 60]"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from i18n_text import get_text  # noqa: E402
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=60)
    args = ap.parse_args()
    c = sqlite3.connect(DB)
    sample = []
    for sid, slug, jp, en_col in c.execute("SELECT id, slug, jp, en FROM sentence ORDER BY id"):
        nat = get_text(c, "sentence", sid, "translation")
        lit = get_text(c, "sentence", sid, "translation_literal")
        en = en_col or get_text(c, "sentence", sid, "translation", "en")
        if not nat:
            continue
        sample.append({"id": len(sample), "slug": slug, "jp": jp, "en": en, "nat": nat, "lit": lit})
    outdir = ROOT / "research" / "derived" / "tr" / "full"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_sample.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    print(f"full sentence audit: {len(sample)} sentences -> {nb} batches (batch={args.batch})")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
