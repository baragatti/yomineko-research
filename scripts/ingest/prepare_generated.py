#!/usr/bin/env python3
"""P5 GENERATION step 3 — validate generated sentences and build a dissection batch.

Takes the generation workflow result, tokenizes each generated JP (Layer-A skeleton), and KEEPS only
sentences that (a) genuinely use the target (vocab id present in the tokenization; grammar trusted +
confirmed later by the dissection agent), (b) stay within the level's known-set (≤--max-new new items),
(c) aren't duplicates. Emits a batch (ai_generated=1) consumed by split_groups → dissect workflow →
persist_batch like any other. Usage:
  prepare_generated.py --level n5 --kind vocab --result <gen_result.json> --out research/derived/batch_gen_n5v.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
from dissect import Dissector  # noqa: E402
from i18n_text import get_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
LEVEL_ORDER = {"pre-n5": 1, "n5": 2, "n4": 3, "n3": 4, "n2": 5, "n1": 6}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True)
    ap.add_argument("--kind", choices=["vocab", "grammar"], required=True)
    ap.add_argument("--result", required=True)
    ap.add_argument("--max-new", dest="max_new", type=int, default=3)
    ap.add_argument("--cap", type=int, default=3, help="max kept sentences per target (enough to reach ≥3)")
    ap.add_argument("--maxlen", type=int, default=30)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    con = sqlite3.connect(DB)
    diss = Dissector()
    existing = {r[0] for r in con.execute("SELECT jp FROM sentence")}
    maxlvl = LEVEL_ORDER[args.level]
    keep = [lv for lv, o in LEVEL_ORDER.items() if o <= maxlvl]
    q = ",".join("?" * len(keep))
    kv = {r[0] for r in con.execute(f"SELECT id FROM vocab WHERE level IN ({q})", keep)}
    kk = {r[0] for r in con.execute(f"SELECT id FROM kanji WHERE level IN ({q})", keep)}
    results = json.loads(Path(args.result).read_text(encoding="utf-8"))

    batch, seen = [], set()
    per_ref: dict[str, int] = {}
    kept = dropped_target = dropped_new = dropped_dup = dropped_cap = 0
    for r in results:
        ref = str(r.get("ref"))
        gcand = []
        if args.kind == "grammar":
            row = con.execute("SELECT id,key,structure_pattern,forms_json FROM grammar_point WHERE key=?",
                              (ref,)).fetchone()
            if row:
                gcand = [{"key": row[1], "pattern": row[2] or "",
                          "label": get_text(con, "grammar_point", row[0], "label") or ""}]
            target_vid = None
            target_strs = []
        else:
            target_vid = int(ref) if ref.isdigit() else None
            tv = con.execute("SELECT headword,kana FROM vocab WHERE id=?", (target_vid,)).fetchone() \
                if target_vid else None
            target_strs = [x for x in (tv or []) if x]
        for s in r.get("sentences", []):
            if per_ref.get(ref, 0) >= args.cap:
                dropped_cap += 1
                continue
            jp = (s.get("jp") or "").strip().rstrip("。、")  # generated: ensure no trailing punctuation
            if not jp or len(jp) > args.maxlen:
                continue
            if jp in existing or jp in seen:
                dropped_dup += 1
                continue
            sk = diss.skeleton(jp)
            if any(t["pos_fine"] == "固有名詞" and len(t["surface"]) >= 2 and t["vocab_id"] is None
                   for t in sk["tokens"]):
                continue
            if args.kind == "vocab" and target_vid is not None:
                # genuine use = vocab_id linked OR the word's surface/kana appears (Sudachi may split it)
                if target_vid not in sk["vocab_ids"] and not any(t in jp for t in target_strs):
                    dropped_target += 1
                    continue
            newc = len([v for v in sk["vocab_ids"] if v not in kv]) + \
                len([k for k in sk["kanji_ids"] if k not in kk])
            if newc > args.max_new:
                dropped_new += 1
                continue
            seen.add(jp)
            per_ref[ref] = per_ref.get(ref, 0) + 1
            kept += 1
            slug = "sent:gen-" + hashlib.sha1(jp.encode("utf-8")).hexdigest()[:12]
            batch.append({
                "slug": slug, "jp": jp, "jp_source": "ai-generated", "en": None,
                "target": ref, "topic": f"generated:{args.kind}", "level": args.level, "ai_generated": 1,
                "tokens": [{"position": t["position"], "surface": t["surface"], "lemma": t["lemma"],
                            "reading": t["reading"], "pos_coarse": t["pos_coarse"], "pos_fine": t["pos_fine"],
                            "is_particle": t["is_particle"], "gloss_en": None} for t in sk["tokens"]],
                "particles": [{"position": p["position"], "particle": p["particle"]} for p in sk["particles"]],
                "grammar_candidates": gcand,
            })
    Path(ROOT / args.out).write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated batch: kept {kept} -> {args.out} (dropped: target={dropped_target} "
          f"new={dropped_new} dup={dropped_dup} cap={dropped_cap})")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
