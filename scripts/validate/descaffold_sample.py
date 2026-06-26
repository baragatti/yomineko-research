#!/usr/bin/env python3
"""De-scaffolding sampler (translation_qa.md §9 grounded-edit). Finds learner-facing PROSE fields whose pt-BR or
en value leaked internal generation scaffolding — grammar-point slugs (gp-NN), "candidato/candidate <code>" meta
references, bare 5-6 digit sentence IDs, or orphan kana fragments — and gathers each with its Japanese anchor +
the human name of any referenced grammar point, so a rewrite agent can strip the artifacts WITHOUT losing any
linguistic fact. One record per affected entity (prose is unique, so NO distinct-dedup here).
Writes research/derived/tr/descaffold/batch_*.json as [{id, entity_type, entity_id, anchor, grammar, pt, en}].
Usage: descaffold_sample.py [--batch 12]"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingest"))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"

# leak signatures, LOCALE-AWARE: in pt-BR prose "target"/"candidato" are pipeline-speak leaks; in the en
# parallel "target"/"candidate" are legitimate English, so en flags only the hard codes.
PT_LEAK = re.compile(r"gp-\d+|candidat[oae]s?\b|candidate\b|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])"
                     r"|\btarget\b|\bjec\b|位置\s*\d|posi[çc][ãa]o\s*\d", re.I)
EN_LEAK = re.compile(r"gp-\d+|tari-tari|cand-\w+|(?<![0-9])\d{5,6}(?![0-9])|\bjec\b|位置\s*\d", re.I)
GP = re.compile(r"gp-\d+", re.I)
# (entity_type, field, anchor_sql -> {entity_id: anchor_text})
FIELDS = [
    ("sentence", "structure_explanation", "SELECT id, jp FROM sentence"),
    ("particle", "explanation",
     "SELECT p.id, p.particle||'  «'||s.jp||'»' FROM particle p JOIN sentence s ON s.id=p.sentence_id"),
    ("token", "role",
     "SELECT t.id, t.surface||'  «'||s.jp||'»' FROM token t JOIN sentence s ON s.id=t.sentence_id"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=12)
    args = ap.parse_args()
    c = sqlite3.connect(DB)
    # gp-NN -> human name: grammar_point.key + pt label
    gpmap: dict = {}
    try:
        keys = {r[0]: r[1] for r in c.execute("SELECT id, key FROM grammar_point")}
    except sqlite3.OperationalError:
        keys = {}
    labels = {eid: v for eid, v in c.execute(
        "SELECT entity_id, value FROM localized_text WHERE entity_type='grammar_point' AND field='label' AND locale='pt-BR'")}
    for gid in keys:
        nm = keys.get(gid) or ""
        lab = labels.get(gid)
        gpmap[gid] = (nm + (f" — {lab}" if lab else "")).strip() or gid

    sample = []
    for et, field, anchor_sql in FIELDS:
        anchor = {r[0]: r[1] for r in c.execute(anchor_sql)}
        pt = {eid: v for eid, v in c.execute(
            "SELECT entity_id, value FROM localized_text WHERE entity_type=? AND field=? AND locale='pt-BR'", (et, field))}
        en = {eid: v for eid, v in c.execute(
            "SELECT entity_id, value FROM localized_text WHERE entity_type=? AND field=? AND locale='en'", (et, field))}
        for eid, ptv in pt.items():
            env = en.get(eid, "")
            if not (PT_LEAK.search(ptv) or (env and EN_LEAK.search(env))):
                continue
            gids = sorted(set(m.group(0).lower() for m in GP.finditer(ptv + " " + env)))
            gnames = {g: gpmap.get(g, g) for g in gids}
            sample.append({"id": len(sample), "entity_type": et, "entity_id": eid,
                           "anchor": anchor.get(eid, ""), "grammar": gnames, "pt": ptv, "en": env})
    outdir = ROOT / "research" / "derived" / "tr" / "descaffold"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("batch_*.json"):
        old.unlink()
    nb = (len(sample) + args.batch - 1) // args.batch
    for b in range(nb):
        (outdir / f"batch_{b:04d}.json").write_text(
            json.dumps(sample[b * args.batch:(b + 1) * args.batch], ensure_ascii=False), encoding="utf-8")
    (outdir / "_sample.json").write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    by = {}
    for s in sample:
        by[s["entity_type"] + "." + ("structure_explanation" if s["entity_type"] == "sentence" else
                                     "explanation" if s["entity_type"] == "particle" else "role")] = by.get(
            s["entity_type"], 0) + 1
    print(f"descaffold: {len(sample)} affected entities -> {nb} batches (batch={args.batch})")
    from collections import Counter
    print("  by field:", dict(Counter(s["entity_type"] for s in sample)))
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
