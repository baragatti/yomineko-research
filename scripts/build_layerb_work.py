#!/usr/bin/env python3
"""W13b — turn the derived Layer-B into the four work lists an authoring pass consumes.

Input is `research/derived/n3_mined/layerb_derived/batch-*.json` (scripts/derive_layerb.py) plus the
mined rows for pt / pt_literal / en, plus a READ-ONLY copy of the corpus DB for the evidence a reviewer
needs to decide: what other glosses the bank uses for a key, what senses the registry holds, and what a
bank structure paragraph of the same clause shape actually reads like.

Four lists, under `research/derived/n3_mined/layerb_work/`:

  rulings-NN.json      one entry per ambiguous (lemma, pos) pair, NOT per token. The derivation produced
                       a gloss for 12,405 tokens whose key had more than one candidate; those 12,405
                       tokens are 1,563 decisions, and the decision is a convention ("which gloss does
                       いる take as an auxiliary"), applied by script afterwards. Each entry carries the
                       derived candidate(s) with their occurrence counts, every competing gloss the bank
                       uses for the same key, the linked registry senses, and up to 6 example sentences.
  tokens-residue.json  the tokens the derivation could not gloss at all. All 154 of them: the 116 that
                       stay `author`, and the 38 a numeral rule resolved, kept in the list flagged
                       `resolved_by_rule` so the rule gets read by a human rather than trusted silently.
  particles-NN.json    every particle whose explanation is NOT templated (3,391 of 10,257), with the
                       sentence around it. Nothing here is a fill-in-the-blank: these are the pairs whose
                       meaning the corpus does not carry (に / で / と / の-nominalizer …), so the
                       function_pt label is offered as a starting point, not as an answer.
  paragraphs-NN.json   all 4,223 structure paragraphs, batched by predicted clause class so one
                       instruction covers a run of same-shaped sentences, each with three real bank
                       paragraphs of the same class as style anchors.

Read-only. Writes nothing but the work lists; the DB is opened for SELECT and must be a copy.

Usage: python scripts/build_layerb_work.py --db <copy.sqlite>
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
MINED = ROOT / "research" / "derived" / "n3_mined"
DERIVED = MINED / "layerb_derived"
OUT = MINED / "layerb_work"

RULINGS_PER_FILE = 150
PARTICLES_PER_FILE = 200
PARAGRAPHS_PER_FILE = 200
EXAMPLES_PER_RULING = 6
ANCHORS_PER_CLASS = 3


def chunk_write(items: list, per_file: int, stem: str, header: dict, field: str) -> list[str]:
    written = []
    for f in OUT.glob(f"{stem}-*.json"):
        f.unlink()
    for i in range(0, len(items), per_file):
        n = i // per_file + 1
        p = OUT / f"{stem}-{n:02d}.json"
        p.write_text(json.dumps({**header, "file": p.name, "part": n,
                                 "parts": (len(items) + per_file - 1) // per_file,
                                 "count": len(items[i:i + per_file]),
                                 field: items[i:i + per_file]},
                                ensure_ascii=False, indent=1), encoding="utf-8")
        written.append(p.name)
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True, help="READ-ONLY copy of db/corpus.sqlite")
    args = ap.parse_args()
    import sqlite3
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    OUT.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- inputs
    derived = []
    for f in sorted(DERIVED.glob("batch-*.json")):
        derived += json.loads(f.read_text(encoding="utf-8"))["sentences"]
    rows_by_jp = {}
    for name in ("accepted.json", "generated.json"):
        for r in json.loads((MINED / name).read_text(encoding="utf-8"))["rows"]:
            if not r.get("reject"):
                rows_by_jp[r["jp"]] = r
    residue = json.loads((MINED / "layerb_residue.json").read_text(encoding="utf-8"))
    res_by_jp = {s["jp"]: s for s in residue["sentences"]}
    print(f"{len(derived)} derived sentences, {len(rows_by_jp)} source rows")

    # bank gloss candidates per (lemma, pos_coarse) and per (surface, lemma, pos_coarse)
    bank_by_key: dict[tuple, Counter] = defaultdict(Counter)
    for lemma, pc, gloss in con.execute(
            "SELECT t.lemma,t.pos_coarse,lt.value FROM token t JOIN localized_text lt "
            "ON lt.entity_type='token' AND lt.entity_id=t.id AND lt.field='gloss' "
            "AND lt.locale='pt-BR' WHERE t.split_mode='C'"):
        if gloss:
            bank_by_key[(lemma, pc)][gloss] += 1

    # registry senses per vocab slug
    senses_by_vocab: dict[int, list] = defaultdict(list)
    for vid, order, gp in con.execute(
            "SELECT vocab_id,sense_order,gloss_pt FROM vocab_sense ORDER BY vocab_id,sense_order"):
        try:
            gl = json.loads(gp) if gp else []
        except json.JSONDecodeError:
            gl = [gp]
        senses_by_vocab[vid].append({"sense_order": order, "gloss_pt": gl})
    vocab_slug = {vid: slug for vid, slug in con.execute("SELECT id,slug FROM vocab")}

    # ---------------------------------------------------------------- rulings
    pairs: dict[tuple, dict] = {}
    tokens_residue = []
    for s in derived:
        row = rows_by_jp.get(s["jp"], {})
        res_tok = {t["position"]: t for t in res_by_jp.get(s["jp"], {}).get("tokens", [])}
        for t in s["tokens"]:
            rt = res_tok.get(t["position"], {})
            if t["gloss_status"] == "ambiguous-verify":
                k = (rt.get("lemma"), rt.get("pos"))
                e = pairs.setdefault(k, {
                    "lemma": k[0], "pos": k[1], "pos_coarse": rt.get("pos_coarse"),
                    "occurrences": 0, "surfaces": Counter(), "derived": Counter(),
                    "origins": Counter(), "vocab_ids": Counter(), "examples": [],
                })
                e["occurrences"] += 1
                e["surfaces"][rt.get("surface")] += 1
                e["derived"][t.get("gloss_pt")] += 1
                e["origins"][t["gloss_origin"]] += 1
                if rt.get("vocab_id"):
                    e["vocab_ids"][rt["vocab_id"]] += 1
                if len(e["examples"]) < EXAMPLES_PER_RULING:
                    e["examples"].append({
                        "key": s["key"], "position": t["position"], "surface": rt.get("surface"),
                        "jp": s["jp"], "pt": row.get("pt"),
                    })
            elif t["gloss_status"] == "author" or t["gloss_origin"] == "rule-numeral":
                tokens_residue.append({
                    "key": s["key"], "slug": s["slug"], "position": t["position"],
                    "surface": rt.get("surface"), "lemma": rt.get("lemma"), "pos": rt.get("pos"),
                    "pos_coarse": rt.get("pos_coarse"),
                    "vocab_id": rt.get("vocab_id"), "vocab_slug": rt.get("vocab_slug"),
                    "resolved_by_rule": t["gloss_origin"] == "rule-numeral",
                    "gloss_pt": t.get("gloss_pt"),
                    "role_pt_hint": rt.get("role_pt_hint"),
                    "jp": s["jp"], "pt": row.get("pt"), "pt_literal": row.get("pt_literal"),
                    "lesson": s.get("lesson"), "targets": s.get("targets"),
                })

    rulings = []
    for (lemma, pos), e in sorted(pairs.items(), key=lambda kv: -kv[1]["occurrences"]):
        vid = e["vocab_ids"].most_common(1)[0][0] if e["vocab_ids"] else None
        bank = bank_by_key.get((lemma, e["pos_coarse"]), Counter())
        derived_texts = set(e["derived"])
        rulings.append({
            "lemma": lemma, "pos": pos, "pos_coarse": e["pos_coarse"],
            "occurrences": e["occurrences"],
            "surfaces": dict(e["surfaces"].most_common()),
            "derived_candidates": [{"gloss_pt": g, "n": n, "origin": e["origins"].most_common(1)[0][0]}
                                   for g, n in e["derived"].most_common()],
            "bank_alternatives": [{"gloss_pt": g, "n_in_bank": n}
                                  for g, n in bank.most_common(8) if g not in derived_texts],
            "registry": {"vocab_id": vid, "vocab_slug": vocab_slug.get(vid),
                         "senses": senses_by_vocab.get(vid, [])[:5]} if vid else None,
            "examples": e["examples"],
            "ruling": None,          # <- the reviewer writes the gloss here
            "note": None,
        })

    # ---------------------------------------------------------------- particles
    particles = []
    for s in derived:
        row = rows_by_jp.get(s["jp"], {})
        for p in s["particles"]:
            if p["explanation_status"] == "template":
                continue
            particles.append({
                "key": s["key"], "slug": s["slug"], "position": p["position"],
                "surface": p["particle"], "function_type": p["function_type"],
                "function_pt": p["function_pt"], "function_status": p["function_status"],
                "jp": s["jp"], "pt": row.get("pt"), "pt_literal": row.get("pt_literal"),
                "clause_structure_predicted": s["clause_structure_predicted"],
                "explanation_pt": None,   # <- the reviewer writes it here
            })

    # ---------------------------------------------------------------- paragraphs
    anchors: dict[str, list] = {}
    for cls, in con.execute("SELECT DISTINCT clause_structure FROM sentence "
                            "WHERE clause_structure IS NOT NULL AND clause_structure<>''"):
        anchors[cls] = [{"jp": jp, "structure_explanation_pt": ex} for jp, ex in con.execute(
            "SELECT s.jp,lt.value FROM sentence s JOIN localized_text lt "
            "ON lt.entity_type='sentence' AND lt.entity_id=s.id AND lt.field='structure_explanation' "
            "AND lt.locale='pt-BR' WHERE s.clause_structure=? AND length(lt.value) BETWEEN 200 AND 400 "
            "ORDER BY s.id LIMIT ?", (cls, ANCHORS_PER_CLASS))]

    by_class: dict[str, list] = defaultdict(list)
    for s in derived:
        row = rows_by_jp.get(s["jp"], {})
        res_tok = {t["position"]: t for t in res_by_jp.get(s["jp"], {}).get("tokens", [])}
        by_class[s["clause_structure_predicted"]].append({
            "key": s["key"], "slug": s["slug"],
            "clause_structure_predicted": s["clause_structure_predicted"],
            "jp": s["jp"], "en": row.get("en"), "pt": row.get("pt"),
            "pt_literal": row.get("pt_literal"),
            "lesson": s.get("lesson"), "targets": s.get("targets"),
            "tokens": [{"position": t["position"],
                        "surface": res_tok.get(t["position"], {}).get("surface"),
                        "lemma": res_tok.get(t["position"], {}).get("lemma"),
                        "pos": res_tok.get(t["position"], {}).get("pos"),
                        "gloss_pt": t.get("gloss_pt"), "gloss_status": t["gloss_status"]}
                       for t in s["tokens"]],
            "particles": [{"position": p["position"], "surface": p["particle"],
                           "function_type": p["function_type"], "function_pt": p["function_pt"],
                           "explanation_pt": p["explanation_pt"],
                           "explanation_status": p["explanation_status"]}
                          for p in s["particles"]],
            "structure_explanation_pt": None,   # <- the reviewer writes it here
        })
    paragraphs = []
    for cls in sorted(by_class, key=lambda c: -len(by_class[c])):
        for item in by_class[cls]:
            item["style_anchors"] = anchors.get(cls, [])
            paragraphs.append(item)

    # ---------------------------------------------------------------- emit
    hdr = {"unit": "W13b", "generated_by": "scripts/build_layerb_work.py"}
    files = {}
    files["rulings"] = chunk_write(
        rulings, RULINGS_PER_FILE, "rulings",
        {**hdr, "kind": "ambiguous (lemma, pos) gloss rulings — one decision per pair, not per token",
         "instruction": "Write the pt-BR gloss this lemma takes in this POS into `ruling`. It is applied "
                        "to every occurrence listed under `occurrences`."},
        "rulings")
    files["particles"] = chunk_write(
        particles, PARTICLES_PER_FILE, "particles",
        {**hdr, "kind": "particle explanations the template does not cover",
         "instruction": "Write `explanation_pt` for this particle IN THIS SENTENCE. Name the tokens it "
                        "stands between, as the bank does. `function_pt` is the bank's modal label for "
                        "the pair and may be wrong for this occurrence."},
        "particles")
    files["paragraphs"] = chunk_write(
        paragraphs, PARAGRAPHS_PER_FILE, "paragraphs",
        {**hdr, "kind": "structure paragraphs, batched by predicted clause class",
         "instruction": "Write `structure_explanation_pt`: how this sentence is built. "
                        "`style_anchors` are real bank paragraphs of the same shape; match their level "
                        "of detail, not their words. `clause_structure_predicted` is a 72 %-accurate "
                        "batching key, not a claim about this sentence."},
        "paragraphs")
    (OUT / "tokens-residue.json").write_text(json.dumps(
        {**hdr, "kind": "tokens with no derived gloss (plus the numerals a rule resolved)",
         "instruction": "Write `gloss_pt`. Rows with `resolved_by_rule: true` already carry one from the "
                        "numeral rule and only need a check.",
         "count": len(tokens_residue),
         "unresolved": sum(1 for t in tokens_residue if not t["resolved_by_rule"]),
         "tokens": tokens_residue}, ensure_ascii=False, indent=1), encoding="utf-8")
    files["tokens"] = ["tokens-residue.json"]

    summary = {**hdr, "counts": {
        "ruling_pairs": len(rulings),
        "ruling_tokens_covered": sum(r["occurrences"] for r in rulings),
        "tokens_residue": len(tokens_residue),
        "tokens_residue_unresolved": sum(1 for t in tokens_residue if not t["resolved_by_rule"]),
        "particles_to_author": len(particles),
        "paragraphs": len(paragraphs),
    }, "files": files}
    (OUT / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    print(json.dumps(summary["counts"], ensure_ascii=False, indent=1))
    for k, v in files.items():
        print(f"{k}: {len(v)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
