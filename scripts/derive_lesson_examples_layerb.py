#!/usr/bin/env python3
"""Q5-lesson-examples: the mechanical Layer-B for the verified lesson-example picks the bank lacks.

Input is the `needs-ingest` residue of research/derived/repairs/lesson_examples.json (written by
scripts/assemble_lesson_examples.py): raw-Tatoeba and generated sentences the verifier accepted for the
lessons that render none. They go through the SAME mechanical-first derivation as W32
(scripts/derive_w32_layerb.py), and nothing is authored here:

  token gloss_pt       derive_layerb_extra.Bank (bank modal, then the registry's sense 0), numeral
                       rule, then the W13b verified rulings reused by (lemma, pos)
  particle function_pt bank modal, then derive_layerb_templates_v2.function_pt_fix
  particle explanation derive_layerb_templates_v2.particle_template
  structure paragraph  never derived: residue
  translation_literal  never derived: residue

Every bank sentence is dissection_tier "full" (validate.py), so a row with any residue cannot be
ingested; `ingest_ready` says so per row. Also records, per content token, the vocab record the
Dissector links, next to the link the verified pick's known-set proof assumed, so a link the ingest
must correct (ください -> 下さい, ２ -> 二, へん -> 辺) is visible before anyone ingests.

Read-only: open a COPY of the DB. Writes research/derived/pending/lesson_examples_layerb_derived.json.
Usage: python scripts/derive_lesson_examples_layerb.py --db <copy.sqlite>
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))

from derive_layerb_extra import CONTENT_POS, Bank  # noqa: E402
from derive_layerb_templates_v2 import (  # noqa: E402
    ORIGIN, enrich_pos_fine3, function_pt_fix, numeral_gloss, particle_template,
    predict_clause_structure,
)
from derive_w32_layerb import verified_rulings  # noqa: E402

TABLE = ROOT / "research" / "derived" / "repairs" / "lesson_examples.json"
GAP = ROOT / "research" / "derived" / "pending" / "lesson_examples_gap.json"
OUT = ROOT / "research" / "derived" / "pending" / "lesson_examples_layerb_derived.json"


def proof_links(lesson: str, slug: str) -> dict[str, str]:
    """surface -> vocab slug the pick's known-set proof assumed (original picks only)."""
    gap = json.loads(GAP.read_text(encoding="utf-8"))
    for L in gap["lessons"]:
        if L["lesson"] != lesson:
            continue
        for p in L["picks"]:
            s = p.get("generated_key") or p.get("slug_after_ingest") or p.get("slug")
            if s == slug:
                return {t["surface"]: t["vocab"] for t in
                        (p.get("known_set_proof") or {}).get("content_tokens") or []
                        if isinstance(t.get("vocab"), str)}
    return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True, help="a COPY of corpus.sqlite (read-only)")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    todo = [r for r in json.loads(TABLE.read_text(encoding="utf-8"))["residue"]
            if r["kind"] == "needs-ingest"]
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    vslug = {i: s for i, s in con.execute("SELECT id, slug FROM vocab")}
    raw = {i: t for i, t in con.execute("SELECT id, text FROM raw_tatoeba_sentence")}
    bank = Bank(con)
    rulings = verified_rulings()
    from dissect import Dissector  # noqa: PLC0415
    diss = Dissector(args.db)

    stats: Counter = Counter()
    out = []
    for r in todo:
        repl = r.get("replacement") or {}
        jp = r.get("jp") if r.get("source_kind") else repl.get("jp")
        slug = r["sentence"] if r.get("source_kind") else "(new replacement, key to assign)"
        if r.get("source_kind") == "tatoeba-raw":
            tid = int(slug.rsplit("-", 1)[1])
            if raw.get(tid) != jp:
                raise SystemExit(f"{slug}: jp differs from raw_tatoeba_sentence {tid}")
        expect = proof_links(r["lesson"], slug)
        sk = diss.skeleton(jp)
        toks = enrich_pos_fine3(sk["tokens"], jp)
        tokens_out = []
        for t in toks:
            if t["pos_coarse"] not in CONTENT_POS:
                continue
            gloss, source, conf = bank.gloss(t["surface"], t["lemma"], t["pos_coarse"],
                                             t.get("vocab_id"))
            origin, status = ORIGIN.get(source), conf or "ambiguous-verify"
            if not gloss:
                num = numeral_gloss(t["surface"])
                gloss, origin, status = (num, "rule-numeral", "unique-accept") if num else \
                    (None, None, "author")
            if status == "ambiguous-verify" and (t["lemma"], t["pos"]) in rulings:
                gloss, origin, status = rulings[(t["lemma"], t["pos"])], "ruling", "verified"
            stats[f"token:{status}"] += 1
            linked = vslug.get(t.get("vocab_id"))
            want = expect.get(t["surface"])
            if want and linked != want:
                stats["link:differs-from-proof"] += 1
            tokens_out.append({"position": t["position"], "surface": t["surface"],
                               "lemma": t["lemma"], "pos": t["pos"], "vocab": linked,
                               **({"proof_vocab": want} if want and want != linked else {}),
                               "gloss_status": status, "gloss_origin": origin,
                               **({"gloss_pt": gloss} if gloss else {})})
        particles_out = []
        for p in sk["particles"]:
            i = next((n for n, t in enumerate(toks) if t["position"] == p["position"]), None)
            ft = p.get("function_type")
            fn = bank.function_pt(p["particle"], ft)
            fn_status = "bank-modal" if fn else "author"
            fix = function_pt_fix(toks, i, p["particle"], ft, fn) if i is not None else None
            if fix:
                fn, fn_status = fix[0], "occurrence-rule"
            expl = particle_template(toks, i, p["particle"], ft) if i is not None else None
            stats["particle:template" if expl else "particle:author"] += 1
            particles_out.append({"position": p["position"], "particle": p["particle"],
                                  "function_type": ft, "function_pt": fn,
                                  "function_status": fn_status, "explanation_pt": expl,
                                  "explanation_status": "template" if expl else "author"})
        residue = (["structure_explanation_pt", "translation_literal"]
                   + [f"token#{t['position']}:{t['gloss_status']}" for t in tokens_out
                      if t["gloss_status"] in ("author", "ambiguous-verify")]
                   + [f"particle#{p['position']}:explanation" for p in particles_out
                      if p["explanation_status"] == "author"]
                   + [f"link#{t['position']}:{t['vocab']}->{t['proof_vocab']}" for t in tokens_out
                      if t.get("proof_vocab")])
        stats["sentences"] += 1
        out.append({"lesson": r["lesson"], "slug": slug, "jp": jp,
                    "pt": r.get("pt-BR") or repl.get("pt"), "source_kind": r.get("source_kind")
                    or "generated-replacement", "ai_generated": bool(r.get("ai_generated")
                                                                     or repl.get("ai_generated")),
                    "needs_review": True, "held_link": None if r.get("source_kind") else r["sentence"],
                    "ingest_note": r.get("ingest_note"),
                    "clause_structure_predicted": predict_clause_structure(toks),
                    "tokens": tokens_out, "particles": particles_out,
                    "translation_literal": None, "structure_explanation_pt": None,
                    "residue": residue, "ingest_ready": not residue})
    residue_counts = Counter(x.split("#")[0] + (":" + x.split(":")[1] if "#" in x and
                                                 not x.startswith("link") else "")
                             for s in out for x in s["residue"])
    doc = {
        "unit": "Q5-lesson-examples",
        "kind": "derived (mechanical) Layer-B for the verified lesson-example sentences the bank "
                "lacks; nothing authored",
        "generated_by": "scripts/derive_lesson_examples_layerb.py",
        "inputs": ["research/derived/repairs/lesson_examples.json (residue kind needs-ingest)",
                   "research/derived/mined_layerb_n3/batch-*.json (verified rulings, reused)"],
        "status": "NOT ingestable: the structure paragraph and translation_literal are never derived; "
                  "an authoring pass fills `residue` (plus the link corrections listed there), then "
                  "the W32 path ingests (assemble -> derive_sentence_register_v2 --w13-source -> "
                  "ingest_mined_stages.py) and assemble_lesson_examples.py re-runs",
        "counts": dict(sorted(stats.items())),
        "residue_counts": dict(sorted(residue_counts.items())),
        "ingest_ready": sum(1 for s in out if s["ingest_ready"]),
        "sentences": out,
    }
    args.out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("counts", "residue_counts", "ingest_ready")},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
