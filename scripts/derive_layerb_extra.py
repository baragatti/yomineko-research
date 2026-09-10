#!/usr/bin/env python3
"""W13b extra — run the W13b mechanical derivation over ONE extra input file, as one extra batch.

`scripts/derive_layerb.py` derives the mined-N3 Layer-B from `accepted.json` + `generated.json`, but it
reads its per-token gloss candidates out of `research/derived/n3_mined/layerb_residue.json`, a
measurement artifact that only covers those 4,223 sentences. The 97 sentences written later for the
uncovered N3 targets (`generated_uncovered_final.json`) have no residue record, so this wrapper
re-derives that half from the same DB the residue was measured on, then reuses every decision rule in
`derive_layerb` unchanged: the numeral rule, the particle template, the clause-structure predictor, the
sentence key and the slug.

The gloss derivation is not re-invented here. It is the residue's own rule, restated and then CHECKED:
running it over the 4,223 residue records reproduces all 17,057 `gloss_pt` / `gloss_source` /
`confidence` triples and all 10,257 `function_pt` labels exactly (`--selfcheck`).

    bank            the modal pt-BR gloss the bank already uses for the same (surface, lemma,
                    pos_coarse); when that surface is not in the bank, for the same (lemma, pos_coarse)
    registry-sense0 '; '.join of the first three pt-BR glosses of the linked vocab's sense[0]
    confidence      `unique-accept` when the key carries exactly one gloss (or the vocab one sense),
                    `ambiguous-verify` otherwise — a reviewer then rules once per (lemma, pos) pair
    rule-numeral    derive_layerb.numeral_gloss, for a bare arabic numeral
    author          nothing fired

Ties are broken the way the residue broke them: `Counter.most_common`, fed in `token.id` order.

Outputs, both NEW files, neither of which touches the existing batches 01-29:

    research/derived/n3_mined/layerb_derived/batch-30.json     the derived batch, same shape as 01-29
    research/derived/n3_mined/layerb_residue_extra.json        the residue record for these 97, so the
                                                               work list has surface / pos_coarse /
                                                               vocab_id / role_pt_hint to show

Read-only with respect to the corpus: the DB is opened `mode=ro` and must be a COPY (the Dissector
needs it for vocab linkage). Nothing under `corpus/`, `db/` or `research/derived/mined_layerb_n3/` is
written.

Usage:
    python scripts/derive_layerb_extra.py --db <copy.sqlite> \
        [--extra research/derived/n3_mined/generated_uncovered_final.json] [--batch 30] [--selfcheck]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
MINED = ROOT / "research" / "derived" / "n3_mined"
OUT_DIR = MINED / "layerb_derived"

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))

from derive_layerb import (  # noqa: E402
    ORIGIN, numeral_gloss, particle_template, predict_clause_structure, sentence_key, sentence_slug,
)

CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞", "代名詞", "連体詞", "接続詞", "感動詞"}


# ------------------------------------------------------------------------------------ bank tables
class Bank:
    """The three modal lookups the residue was built from, read once out of a DB copy."""

    def __init__(self, con: sqlite3.Connection) -> None:
        self.gloss_surface: dict[tuple, Counter] = defaultdict(Counter)
        self.gloss_lemma: dict[tuple, Counter] = defaultdict(Counter)
        self.role: dict[tuple, Counter] = defaultdict(Counter)
        for surf, lemma, pc, field, value in con.execute(
                "SELECT t.surface,t.lemma,t.pos_coarse,lt.field,lt.value FROM token t "
                "JOIN localized_text lt ON lt.entity_type='token' AND lt.entity_id=t.id "
                "AND lt.field IN ('gloss','role') AND lt.locale='pt-BR' "
                "WHERE t.split_mode='C' ORDER BY t.id"):
            if not value:
                continue
            if field == "gloss":
                self.gloss_surface[(surf, lemma, pc)][value] += 1
                self.gloss_lemma[(lemma, pc)][value] += 1
            else:
                self.role[(surf, lemma, pc)][value] += 1

        self.senses: dict[int, list] = defaultdict(list)
        for vid, order, gp in con.execute(
                "SELECT vocab_id,sense_order,gloss_pt FROM vocab_sense ORDER BY vocab_id,sense_order"):
            try:
                gl = json.loads(gp) if gp else []
            except json.JSONDecodeError:
                gl = [gp]
            self.senses[vid].append({"sense_order": order, "gloss_pt": gl})

        self.function: dict[tuple, Counter] = defaultdict(Counter)
        for particle, ft, value in con.execute(
                "SELECT p.particle,p.function_type,lt.value FROM particle p JOIN localized_text lt "
                "ON lt.entity_type='particle' AND lt.entity_id=p.id AND lt.field='function' "
                "AND lt.locale='pt-BR' ORDER BY p.id"):
            if value:
                self.function[(particle, ft)][value] += 1

    def gloss(self, surface: str, lemma: str, pc: str, vocab_id: int | None) -> tuple:
        """(gloss_pt, gloss_source, confidence) — the residue's rule, unchanged."""
        c = self.gloss_surface.get((surface, lemma, pc)) or self.gloss_lemma.get((lemma, pc))
        if c:
            return (c.most_common(1)[0][0], "bank",
                    "unique-accept" if len(c) == 1 else "ambiguous-verify")
        senses = self.senses.get(vocab_id) if vocab_id else None
        if senses and senses[0]["gloss_pt"]:
            return ("; ".join(senses[0]["gloss_pt"][:3]), "registry-sense0",
                    "unique-accept" if len(senses) == 1 else "ambiguous-verify")
        return (None, None, None)

    def role_hint(self, surface: str, lemma: str, pc: str) -> str | None:
        c = self.role.get((surface, lemma, pc))
        return c.most_common(1)[0][0] if c else None

    def function_pt(self, particle: str, ft: str | None) -> str | None:
        c = self.function.get((particle, ft))
        return c.most_common(1)[0][0] if c else None


# ------------------------------------------------------------------------------------- self-check
def selfcheck(bank: Bank) -> int:
    """Replay the derivation over the 4,223 residue records; every triple must come back identical."""
    path = MINED / "layerb_residue.json"
    if not path.exists():
        print("no layerb_residue.json — self-check skipped")
        return 0
    res = json.loads(path.read_text(encoding="utf-8"))
    n = Counter()
    for s in res["sentences"]:
        for t in s["tokens"]:
            got = bank.gloss(t["surface"], t["lemma"], t["pos_coarse"], t.get("vocab_id"))
            want = (t.get("gloss_pt"), t.get("gloss_source"), t.get("confidence"))
            n["gloss_ok" if got == want else "gloss_DIFF"] += 1
            hint = bank.role_hint(t["surface"], t["lemma"], t["pos_coarse"])
            n["role_ok" if hint == t.get("role_pt_hint") else "role_DIFF"] += 1
        for p in s["particles"]:
            got = bank.function_pt(p["particle"], p.get("function_type"))
            n["function_ok" if got == p.get("function_pt") else "function_DIFF"] += 1
    print("self-check:", json.dumps(dict(sorted(n.items())), ensure_ascii=False))
    return 1 if any(k.endswith("DIFF") and v for k, v in n.items()) else 0


# ------------------------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True, help="a COPY of corpus.sqlite, opened read-only")
    ap.add_argument("--extra", type=Path, default=MINED / "generated_uncovered_final.json")
    ap.add_argument("--batch", type=int, default=30)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    bank = Bank(con)
    if args.selfcheck and selfcheck(bank):
        print("SELF-CHECK FAILED — the derivation no longer reproduces the residue")
        return 2

    doc = json.loads(args.extra.read_text(encoding="utf-8"))
    rows = [r for r in doc["rows"] if not r.get("reject")]
    print(f"{len(rows)} extra sentences from {args.extra.name}")

    from dissect import Dissector  # noqa: PLC0415
    diss = Dissector(args.db)

    stats: Counter = Counter()
    template_by_pair: Counter = Counter()
    author_by_pair: Counter = Counter()
    out_sentences, residue_sentences = [], []

    for r in sorted(rows, key=lambda x: (bool(x.get("generated")), str(x.get("tatoeba_id") or ""),
                                         x["jp"])):
        key = sentence_key(r)
        sk = diss.skeleton(r["jp"])
        toks = sk["tokens"]

        tokens_out, residue_tokens = [], []
        for t in toks:
            if t["pos_coarse"] not in CONTENT_POS:
                continue
            gloss, source, conf = bank.gloss(t["surface"], t["lemma"], t["pos_coarse"],
                                             t.get("vocab_id"))
            origin = ORIGIN.get(source)
            if gloss:
                status = conf or "ambiguous-verify"
            else:
                num = numeral_gloss(t["surface"])
                if num is not None:
                    gloss, origin, status = num, "rule-numeral", "unique-accept"
                else:
                    origin, status = None, "author"
            stats[f"token:{status}"] += 1
            if origin:
                stats[f"origin:{origin}"] += 1
            row = {"position": t["position"], "lemma": t["lemma"], "pos": t["pos"],
                   "gloss_status": status, "gloss_origin": origin}
            if gloss:
                row["gloss_pt"] = gloss
            tokens_out.append(row)
            residue_tokens.append({
                "position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                "pos": t["pos"], "pos_coarse": t["pos_coarse"], "vocab_id": t.get("vocab_id"),
                "gloss_pt": gloss if source else None, "gloss_source": source,
                "role_pt_hint": bank.role_hint(t["surface"], t["lemma"], t["pos_coarse"]),
                "author": not source, "confidence": conf,
            })

        particles_out, residue_particles = [], []
        for p in sk["particles"]:
            pos = p["position"]
            i = next((n for n, t in enumerate(toks) if t["position"] == pos), None)
            ft = p.get("function_type")
            fpt = bank.function_pt(p["particle"], ft)
            expl = particle_template(toks, i, p["particle"], ft) if i is not None else None
            pair = f"{p['particle']}/{ft}"
            if expl:
                template_by_pair[pair] += 1
                stats["particle:template"] += 1
            else:
                author_by_pair[pair] += 1
                stats["particle:author"] += 1
            if not fpt:
                stats["particle:function_author"] += 1
            particles_out.append({
                "position": pos, "particle": p["particle"], "function_type": ft,
                "function_pt": fpt, "function_status": "bank-modal" if fpt else "author",
                "explanation_pt": expl, "explanation_status": "template" if expl else "author",
            })
            residue_particles.append({
                "position": pos, "particle": p["particle"], "function_type": ft,
                "function_pt": fpt, "explanation_pt": None, "author": True,
            })

        cs = predict_clause_structure(toks)
        stats[f"clause:{cs}"] += 1
        out_sentences.append({
            "key": key,
            "tatoeba_id": r.get("tatoeba_id") if not key.startswith("gen-") else None,
            "slug": sentence_slug(key),
            "generated": bool(r.get("generated")),
            "jp": r["jp"],
            "lesson": r.get("lesson"),
            "targets": r.get("targets") or ([r["target"]] if r.get("target") else []),
            "clause_structure_predicted": cs,
            "tokens": tokens_out,
            "particles": particles_out,
            "structure_explanation_pt": None,
            "structure_status": "author",
        })
        residue_sentences.append({
            "key": key, "tatoeba_id": r.get("tatoeba_id") or None, "jp": r["jp"],
            "lesson": r.get("lesson"), "targets": r.get("targets") or [r["target"]],
            "generated": bool(r.get("generated")),
            "tokens": residue_tokens, "particles": residue_particles,
        })
        stats["sentences"] += 1

    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"batch-{args.batch:02d}.json"
    path.write_text(json.dumps({"batch": args.batch, "unit": "W13b",
                                "kind": "derived (mechanical) mined Layer-B",
                                "source": str(args.extra.relative_to(ROOT)).replace("\\", "/"),
                                "sentences": out_sentences}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    (MINED / "layerb_residue_extra.json").write_text(json.dumps({
        "unit": "W13b",
        "kind": "machine-derived Layer-B candidates for the 97 uncovered-target sentences",
        "generated_by": "scripts/derive_layerb_extra.py",
        "inputs": [str(args.extra.relative_to(ROOT)).replace("\\", "/")],
        "counts": {"sentences": len(residue_sentences),
                   "tokens_content": sum(len(s["tokens"]) for s in residue_sentences),
                   "particles": sum(len(s["particles"]) for s in residue_sentences)},
        "sentences": residue_sentences}, ensure_ascii=False, indent=1), encoding="utf-8")

    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=1))
    print("particle template pairs:", json.dumps(dict(template_by_pair.most_common()),
                                                 ensure_ascii=False))
    print("particle author pairs:", json.dumps(dict(author_by_pair.most_common(20)),
                                               ensure_ascii=False))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
