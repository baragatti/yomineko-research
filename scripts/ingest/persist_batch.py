#!/usr/bin/env python3
"""P5 scaling step 3 — persist a workflow-authored dissection batch + validate.

Reads the batch (skeletons/provenance/grammar_keys) and the workflow result (Layer-B pt-BR keyed
by slug + verify verdicts), merges them, and persists each via persist_dissection (which re-derives
the authoritative skeleton and computes level). Unfaithful items (verify) are kept but logged.
Usage: persist_batch.py --batch <batch.json> --result <result.json>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from persist_dissection import persist  # noqa: E402

DB = Path(__file__).resolve().parents[2] / "db" / "corpus.sqlite"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--result", required=True)
    args = ap.parse_args()
    batch = {b["slug"]: b for b in json.loads(Path(args.batch).read_text(encoding="utf-8"))}
    results = json.loads(Path(args.result).read_text(encoding="utf-8"))

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON;")
    diss = Dissector()
    persisted, unfaithful, missing = 0, [], 0
    for r in results:
        lb = r.get("layerB") or r.get("layer_b")
        if not lb:
            missing += 1
            continue
        slug = lb.get("slug")
        item = batch.get(slug)
        if not item:
            missing += 1
            continue
        verdict = r.get("verdict") or {}
        if verdict.get("faithful") is False:
            unfaithful.append(slug)
        rec = {
            "slug": slug, "jp": item["jp"], "jp_source": item["jp_source"], "en": item.get("en"),
            "level": "n5", "tier": "full", "ai_generated": 0,
            "translation_confidence": 0.85 if verdict.get("faithful") else 0.6,
            "tags": ["te-form", item.get("target")],
            "grammar_keys": item.get("grammar_keys", ["te-form"]),
            "pt": lb.get("pt"), "pt_literal": lb.get("pt_literal"),
            "structure_explanation_pt": lb.get("structure_explanation_pt"),
            "tokens": {int(t["position"]): {"role_pt": t.get("role_pt"), "gloss_pt": t.get("gloss_pt"),
                                            "conjugation_note_pt": t.get("conjugation_note_pt")}
                       for t in lb.get("tokens", [])},
            "particles": {int(p["position"]): {"function_pt": p.get("function_pt"),
                                               "explanation_pt": p.get("explanation_pt")}
                          for p in lb.get("particles", [])},
        }
        persist(con, diss, rec)
        persisted += 1
    print(f"persisted {persisted} batch dissections; unfaithful(flagged)={len(unfaithful)} {unfaithful}; "
          f"missing={missing}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
