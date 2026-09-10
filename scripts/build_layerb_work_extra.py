#!/usr/bin/env python3
"""W13b extra — the work list for batch-30, i.e. only what the derivation could NOT settle.

`scripts/build_layerb_work.py` builds the four W13b work lists for batches 01-29. This wrapper builds
the same four kinds for the single extra batch (the 97 sentences written for the uncovered N3 targets)
and writes them into ONE file, `research/derived/n3_mined/layerb_work/extra-30.json`, because at this
size four files would be four almost-empty files.

THE POINT OF THIS SCRIPT IS THE SUBTRACTION. A ruling is a decision about a `(lemma, pos)` pair and the
assembler applies it to every `ambiguous-verify` token carrying that pair, in EVERY derived batch —
batch-30 included. So a pair that batches 01-29 already ruled is already answered here: re-ruling it
would either duplicate the identity (two rows, one slot) or, worse, quietly contradict a decision an
independent verifier already signed. Those pairs go into `reused_rulings` with the text that will reach
them, and never into `rulings`. Only pairs that appear nowhere in `layerb_out/rulings-*.json` with an
effective, verified decision are put up for authoring.

"Effective" is computed with the assembler's own reader (`pair_files`, `_kind`, `_rows`, `_ident`,
`decide`), so this script and `scripts/assemble_layerb.py` cannot drift: a ruling that the assembler
would drop (rejected, or with no verdict of its own) counts as NOT ruled, and the pair is put up for
authoring rather than silently inheriting a decision that will never be merged.

Read-only. Opens a COPY of the DB for the style anchors, the bank's competing glosses and the registry
senses; writes exactly one new file.

Usage: python scripts/build_layerb_work_extra.py --db <copy.sqlite> [--batch 30]
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
DERIVED = MINED / "layerb_derived"
OUTPUTS = MINED / "layerb_out"
OUT = MINED / "layerb_work"

sys.path.insert(0, str(ROOT / "scripts"))
from assemble_layerb import _ident, _kind, _rows, _verdict_entries, decide, pair_files  # noqa: E402

ANCHORS_PER_CLASS = 3
EXAMPLES_PER_RULING = 6


def effective_rulings(batch: int) -> dict[tuple, dict]:
    """(lemma, pos) -> {ruling, decision, source} for every pair batches 01-29 have already settled."""
    warnings: list[str] = []
    authored, verdicts = pair_files(OUTPUTS, warnings)
    out: dict[tuple, dict] = {}
    for f in authored:
        if f.stem.endswith(f"-{batch:02d}"):
            continue                                   # never read this unit's own output
        doc = json.loads(f.read_text(encoding="utf-8"))
        if _kind(f, doc) != "rulings":
            continue
        ventries: dict[tuple, dict] = {}
        vf = verdicts.get(f.name)
        if vf is not None:
            for mk, e in _verdict_entries(json.loads(vf.read_text(encoding="utf-8"))):
                ident = _ident("rulings", e, mk)
                if ident is not None:
                    ventries[ident] = e
        for r in _rows(doc):
            ident = _ident("rulings", r, None)
            if ident is None:
                continue
            if not r.get("ruling") and r.get("gloss_pt"):
                r = {**r, "ruling": r["gloss_pt"]}
            decision, repl = decide(ventries.get(ident), "ruling")
            if decision in ("accept", "accept_side_fix") and r.get("ruling"):
                out[ident] = {"ruling": r["ruling"], "decision": "verified", "source": f.name}
            elif decision == "correct" and repl:
                out[ident] = {"ruling": repl, "decision": "corrected", "source": f.name}
    for w in warnings:
        print("  warn:", w)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True, help="READ-ONLY copy of db/corpus.sqlite")
    ap.add_argument("--batch", type=int, default=30)
    args = ap.parse_args()
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    OUT.mkdir(parents=True, exist_ok=True)

    derived = json.loads((DERIVED / f"batch-{args.batch:02d}.json").read_text(
        encoding="utf-8"))["sentences"]
    res = json.loads((MINED / "layerb_residue_extra.json").read_text(encoding="utf-8"))
    res_by_key = {s["key"]: s for s in res["sentences"]}
    rows_by_jp = {r["jp"]: r for r in json.loads(
        (MINED / "generated_uncovered_final.json").read_text(encoding="utf-8"))["rows"]}
    already = effective_rulings(args.batch)
    print(f"{len(derived)} sentences in batch-{args.batch:02d}; "
          f"{len(already)} (lemma, pos) pairs already ruled in batches 01-29")

    # bank alternatives + registry senses, the evidence a ruling is written against
    bank_by_key: dict[tuple, Counter] = defaultdict(Counter)
    for lemma, pc, gloss in con.execute(
            "SELECT t.lemma,t.pos_coarse,lt.value FROM token t JOIN localized_text lt "
            "ON lt.entity_type='token' AND lt.entity_id=t.id AND lt.field='gloss' "
            "AND lt.locale='pt-BR' WHERE t.split_mode='C' ORDER BY t.id"):
        if gloss:
            bank_by_key[(lemma, pc)][gloss] += 1
    senses_by_vocab: dict[int, list] = defaultdict(list)
    for vid, order, gp in con.execute(
            "SELECT vocab_id,sense_order,gloss_pt FROM vocab_sense ORDER BY vocab_id,sense_order"):
        try:
            gl = json.loads(gp) if gp else []
        except json.JSONDecodeError:
            gl = [gp]
        senses_by_vocab[vid].append({"sense_order": order, "gloss_pt": gl})
    vocab_slug = {vid: slug for vid, slug in con.execute("SELECT id,slug FROM vocab")}

    # ------------------------------------------------------------------ rulings / tokens residue
    pairs: dict[tuple, dict] = {}
    reused: dict[tuple, dict] = {}
    tokens_residue = []
    for s in derived:
        row = rows_by_jp.get(s["jp"], {})
        res_tok = {t["position"]: t for t in res_by_key.get(s["key"], {}).get("tokens", [])}
        for t in s["tokens"]:
            rt = res_tok.get(t["position"], {})
            k = (rt.get("lemma"), rt.get("pos"))
            if t["gloss_status"] == "ambiguous-verify":
                if k in already:
                    e = reused.setdefault(k, {"lemma": k[0], "pos": k[1], "occurrences": 0,
                                              **already[k]})
                    e["occurrences"] += 1
                    continue
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
                    e["examples"].append({"key": s["key"], "position": t["position"],
                                          "surface": rt.get("surface"), "jp": s["jp"],
                                          "pt": row.get("pt")})
            elif t["gloss_status"] == "author" or t["gloss_origin"] == "rule-numeral":
                tokens_residue.append({
                    "key": s["key"], "slug": s["slug"], "position": t["position"],
                    "surface": rt.get("surface"), "lemma": rt.get("lemma"), "pos": rt.get("pos"),
                    "pos_coarse": rt.get("pos_coarse"), "vocab_id": rt.get("vocab_id"),
                    "vocab_slug": vocab_slug.get(rt.get("vocab_id")),
                    "resolved_by_rule": t["gloss_origin"] == "rule-numeral",
                    "gloss_pt": t.get("gloss_pt"), "role_pt_hint": rt.get("role_pt_hint"),
                    "jp": s["jp"], "pt": row.get("pt"), "pt_literal": row.get("pt_literal"),
                    "lesson": s.get("lesson"), "targets": s.get("targets"),
                })

    rulings = []
    for (lemma, pos), e in sorted(pairs.items(), key=lambda kv: (-kv[1]["occurrences"],
                                                                 str(kv[0][0]), str(kv[0][1]))):
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
            "ruling": None,
            "note": None,
        })

    # ------------------------------------------------------------------ particles
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
                "explanation_pt": None,
            })

    # ------------------------------------------------------------------ paragraphs
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
        res_tok = {t["position"]: t for t in res_by_key.get(s["key"], {}).get("tokens", [])}
        by_class[s["clause_structure_predicted"]].append({
            "key": s["key"], "slug": s["slug"],
            "clause_structure_predicted": s["clause_structure_predicted"],
            "jp": s["jp"], "en": row.get("en"), "pt": row.get("pt"),
            "pt_literal": row.get("pt_literal"),
            "lesson": s.get("lesson"), "targets": s.get("targets"),
            "generated": s.get("generated"),
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
            "style_anchors": anchors.get(s["clause_structure_predicted"], []),
            "structure_explanation_pt": None,
        })
    paragraphs = []
    for cls in sorted(by_class, key=lambda c: (-len(by_class[c]), c)):
        paragraphs += by_class[cls]

    doc = {
        "unit": "W13b",
        "generated_by": "scripts/build_layerb_work_extra.py",
        "batch": args.batch,
        "kind": "extra work list — the residue of the derivation for the 97 uncovered-target sentences",
        "instruction": {
            "rulings": "Write the pt-BR gloss this lemma takes in this POS into `ruling` (1-4 words, "
                       "lowercase, no article). It is applied to every occurrence listed under "
                       "`occurrences`. Pairs already settled by batches 01-29 are NOT here; they are "
                       "listed under `reused_rulings` for audit only.",
            "tokens": "Write `gloss_pt`. Rows with `resolved_by_rule: true` already carry one from the "
                      "numeral rule and only need a check.",
            "particles": "Write `explanation_pt` for this particle IN THIS SENTENCE. Name the tokens it "
                         "stands between. `function_pt` is the bank's modal label for the pair and may "
                         "be wrong for this occurrence.",
            "paragraphs": "Write `structure_explanation_pt`: how this sentence is built, in 1-2 "
                          "sentences. `style_anchors` are real bank paragraphs of the same shape; match "
                          "their level of detail, not their words.",
        },
        "counts": {
            "sentences": len(derived),
            "ruling_pairs_new": len(rulings),
            "ruling_tokens_covered_new": sum(r["occurrences"] for r in rulings),
            "ruling_pairs_reused": len(reused),
            "ruling_tokens_covered_reused": sum(e["occurrences"] for e in reused.values()),
            "tokens_residue": len(tokens_residue),
            "tokens_residue_unresolved": sum(1 for t in tokens_residue if not t["resolved_by_rule"]),
            "particles_to_author": len(particles),
            "paragraphs": len(paragraphs),
        },
        "reused_rulings": sorted(reused.values(), key=lambda e: (-e["occurrences"], str(e["lemma"]))),
        "rulings": rulings,
        "tokens": tokens_residue,
        "particles": particles,
        "paragraphs": paragraphs,
    }
    path = OUT / f"extra-{args.batch:02d}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(doc["counts"], ensure_ascii=False, indent=1))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
