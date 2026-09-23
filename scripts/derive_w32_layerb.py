#!/usr/bin/env python3
"""W32 apply, step 1: the mechanical Layer-B for the survival-core sentences the bank does not hold yet.

Input is `research/derived/pending/speak_survival_cores.json` (W32, 71 rows). Rows whose slug is already
banked are skipped (7 bank selections, plus 2 mined rows the W13 N3 ingest banked after W32 was
authored). The rest go through the SAME mechanical-first derivation the W13b scripts use, and nothing is
authored here:

  token gloss_pt       derive_layerb_extra.Bank (bank modal for the (surface, lemma, pos_coarse), then the
                       registry's sense 0), numeral rule, then the W13b verified RULINGS reused by
                       (lemma, pos) out of research/derived/mined_layerb_n3/ (a pair an independent
                       verifier already ruled is not re-ruled, build_layerb_work_extra.py's subtraction)
  particle function_pt bank modal, then derive_layerb_templates_v2.function_pt_fix
  particle explanation derive_layerb_templates_v2.particle_template (v2, the repaired rules)
  structure paragraph  NEVER derived (derive_layerb.py's rule): listed as residue
  translation_literal  not in the W32 table: listed as residue

Every bank sentence is dissection_tier "full", which validate.py reads as a hard promise of all of the
above, so a row with any residue cannot be ingested. The output says `ingest_ready` per row and in
total, and lists the residue a later authoring pass needs; it never invents a value.

Also re-checks the register of every row against TODAY's speak filter (scripts/export/speak_filter.py):
banked rows by their stored register/rule, unbanked rows by the W31 derivation run over them
(`--register-table`, a derive_sentence_register_v2.py output with these rows as `--w13-source`).

Read-only with respect to the corpus: the DB is opened read-only and should be a COPY.
Writes research/derived/pending/w32_layerb_derived.json.

Usage: python scripts/derive_w32_layerb.py --db <copy.sqlite> --register-table <derived.json>
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
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "ingest"))
sys.path.insert(0, str(ROOT / "scripts" / "export"))

from derive_layerb_extra import CONTENT_POS, Bank  # noqa: E402
from derive_layerb_templates_v2 import (  # noqa: E402
    ORIGIN, enrich_pos_fine3, function_pt_fix, numeral_gloss, particle_template,
    predict_clause_structure, sentence_key, sentence_slug,
)
from speak_filter import SpeakFilter  # noqa: E402

TABLE = ROOT / "research" / "derived" / "pending" / "speak_survival_cores.json"
OUT = ROOT / "research" / "derived" / "pending" / "w32_layerb_derived.json"
ASSEMBLED = ROOT / "research" / "derived" / "mined_layerb_n3"


def verified_rulings() -> dict[tuple, str]:
    """(lemma, pos) -> gloss, from the W13b assembled batches, where exactly one ruled gloss exists."""
    seen: dict[tuple, set] = defaultdict(set)
    for f in sorted(ASSEMBLED.glob("batch-*.json")):
        for s in json.loads(f.read_text(encoding="utf-8")).get("sentences", []):
            for t in s.get("tokens", []):
                if t.get("gloss_origin") == "ruling" and t.get("gloss_pt"):
                    seen[(t.get("lemma"), t.get("pos"))].add(t["gloss_pt"])
    return {k: next(iter(v)) for k, v in seen.items() if len(v) == 1}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, required=True, help="a COPY of corpus.sqlite (read-only)")
    ap.add_argument("--register-table", type=Path, required=True,
                    help="derive_sentence_register_v2.py output run with these rows as --w13-source")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    table = json.loads(TABLE.read_text(encoding="utf-8"))
    con = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    banked = {slug: (reg, rule) for slug, reg, rule in
              con.execute("SELECT slug, register, register_rule FROM sentence")}
    texts = {slug: jp for slug, jp in con.execute("SELECT slug, jp FROM sentence")}

    # ---- register re-check against today's filter -------------------------------------------------
    derived = {}
    for r in json.loads(args.register_table.read_text(encoding="utf-8"))["rows"]:
        if r["set"] == "w13":
            derived["sent:" + (r["key"] if r["key"].startswith("gen-")
                               else "tatoeba-" + r["key"].split("-", 1)[1])] = (r["register"], r["rule"])
    regs, rtexts = dict(banked), dict(texts)
    for row in table["rows"]:
        if row["sentence_slug"] not in banked:
            regs[row["sentence_slug"]] = derived.get(row["sentence_slug"], (None, None))
            rtexts[row["sentence_slug"]] = row["jp"]
    filt = SpeakFilter(regs, rtexts)
    register_check = []
    for row in table["rows"]:
        slug = row["sentence_slug"]
        reg, rule = regs[slug]
        register_check.append({
            "slug": slug, "stage": row["stage"], "banked": slug in banked,
            "table": [row["register"], row["register_rule"]], "today": [reg, rule],
            "agrees": [reg, rule] == [row["register"], row["register_rule"]],
            "filter": filt.reject_reason(slug) or "allowed"})

    # ---- mechanical Layer-B for the unbanked rows -------------------------------------------------
    bank = Bank(con)
    rulings = verified_rulings()
    from dissect import Dissector  # noqa: PLC0415
    diss = Dissector(args.db)

    stats: Counter = Counter()
    out = []
    for row in table["rows"]:
        if row["sentence_slug"] in banked:
            stats["skipped:already-banked"] += 1
            continue
        r = {"tatoeba_id": row["tatoeba_id"], "jp": row["jp"], "generated": row["ai_generated"]}
        key = sentence_key(r)
        assert sentence_slug(key) == row["sentence_slug"], (key, row["sentence_slug"])
        sk = diss.skeleton(row["jp"])
        toks = enrich_pos_fine3(sk["tokens"], row["jp"])

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
            tokens_out.append({"position": t["position"], "surface": t["surface"],
                               "lemma": t["lemma"], "pos": t["pos"], "gloss_status": status,
                               "gloss_origin": origin, **({"gloss_pt": gloss} if gloss else {})})

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
                      if p["explanation_status"] == "author"])
        stats["sentences"] += 1
        out.append({"key": key, "slug": row["sentence_slug"], "stage": row["stage"],
                    "function": row["function"], "jp": row["jp"], "en": row["en"], "pt": row["pt"],
                    "tatoeba_id": row["tatoeba_id"] or None, "generated": row["ai_generated"],
                    "clause_structure_predicted": predict_clause_structure(toks),
                    "tokens": tokens_out, "particles": particles_out,
                    "translation_literal": None, "structure_explanation_pt": None,
                    "structure_status": "author", "residue": residue,
                    "ingest_ready": not residue})

    residue_counts = Counter(x.split("#")[0] + (":" + x.split(":")[1] if "#" in x else "")
                             for s in out for x in s["residue"])
    doc = {
        "unit": "W32",
        "kind": "derived (mechanical) Layer-B for the unbanked survival-core rows + register re-check",
        "generated_by": "scripts/derive_w32_layerb.py",
        "inputs": ["research/derived/pending/speak_survival_cores.json",
                   "research/derived/mined_layerb_n3/batch-*.json (verified rulings, reused)"],
        "status": "NOT ingestable: every row carries residue (structure paragraph + translation_literal "
                  "are never derived); the authoring pass fills `residue`, then "
                  "scripts/ingest/ingest_mined_stages.py ingests",
        "counts": dict(sorted(stats.items())),
        "residue_counts": dict(sorted(residue_counts.items())),
        "ingest_ready": sum(1 for s in out if s["ingest_ready"]),
        "register_check": {
            "rows": len(register_check),
            "agrees_with_table": sum(1 for x in register_check if x["agrees"]),
            "allowed_by_today_filter": sum(1 for x in register_check if x["filter"] == "allowed"),
            "disagreements": [x for x in register_check if not x["agrees"]],
            "rejected": [x for x in register_check if x["filter"] != "allowed"],
        },
        "sentences": out,
    }
    args.out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("counts", "residue_counts", "ingest_ready")},
                     ensure_ascii=False, indent=1))
    rc = doc["register_check"]
    print(f"register: {rc['agrees_with_table']}/{rc['rows']} agree with the table, "
          f"{rc['allowed_by_today_filter']}/{rc['rows']} allowed by today's filter")
    for x in rc["disagreements"] + rc["rejected"]:
        print("  ", json.dumps(x, ensure_ascii=False))
    print(f"wrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
