#!/usr/bin/env python3
"""Apply the reviewer-agreed corrections to the authored Layer-B batches before ingest.

The 99-agent authoring pass produced 1,549 glosses, 986 particle entries and 324 structure paragraphs
with ZERO critical problems: no invented token positions, no missing required fields, no altered Layer A,
no English or pt-PT in pt-BR fields. What the two independent checkers did agree on is 45 quality
defects, and two of them are the false-formation-rule class this project keeps rediscovering:

  84127  conjugation_note called のぞいて "sonorizada". のぞく is k-final: its て-form is an euphonic
         change with NO voicing. The same batch correctly uses "sonorizada" for いそぐ -> いそいで two
         sentences later, so a learner comparing the two derives that k-verbs voice as well, i.e.
         *のぞいで. The note even spells out "のぞい + て" while calling it voiced.
  84152  the が explanation said が marks 火 as "quem realiza a ação" in 火が消えた. 消える is
         intransitive: the fire does not act, it undergoes. That is precisely the confusion the
         消える/消す pair exists to resolve.

The rest are self-containment failures (a structure paragraph referring to "a frase com ね", which is a
DIFFERENT record the learner cannot see), a claim that Japanese has no passive voice, contentless
particle notes that state a general rule instead of describing this sentence, and voice drift.

Only problems BOTH checkers raised for the same (sentence, position) are applied; a single dissenting
reviewer is noise. Edits the batch JSON in place, so it is idempotent by value.

Usage: apply_layerb_review.py --from <task-output.json> [--apply]
"""
from __future__ import annotations
import argparse, json, glob, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "research" / "derived" / "mined_layerb"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    raw = json.loads(Path(args.src).read_text(encoding="utf-8"))
    agreed = raw.get("agreed") or raw.get("result", {}).get("agreed") or []
    print(f"{len(agreed)} reviewer-agreed corrections")

    files = {p: json.loads(p.read_text(encoding="utf-8")) for p in sorted(BATCHES.glob("batch-*.json"))}
    index = {}
    for p, d in files.items():
        for s in d["sentences"]:
            index[s["tatoeba_id"]] = (p, s)

    applied, skipped = Counter(), []
    for a in agreed:
        tid, pos, sug = a.get("tatoeba_id"), a.get("position"), (a.get("suggested") or "").strip()
        if not sug:
            skipped.append((tid, pos, "no suggested text")); continue
        hit = index.get(tid)
        if not hit:
            skipped.append((tid, pos, "sentence not in any batch")); continue
        _, s = hit
        # The reviewers write suggestions two ways: bare replacement text, or "field: \"value\"".
        field, val = None, sug
        for pre in ("gloss_pt:", "role_pt:", "conjugation_note_pt:", "explanation_pt:", "function_pt:"):
            if sug.startswith(pre):
                field, val = pre[:-1], sug[len(pre):].strip().strip('"').strip()
                break
        if pos == -1:
            s["structure_explanation_pt"] = val
            applied.update(["structure"]); continue
        tok = next((t for t in s.get("tokens", []) if t["position"] == pos), None)
        par = next((q for q in s.get("particles", []) if q["position"] == pos), None)
        if field in ("gloss_pt", "role_pt", "conjugation_note_pt"):
            if not tok:
                skipped.append((tid, pos, "no token at that position")); continue
            tok[field] = val; applied.update([field]); continue
        if field in ("explanation_pt", "function_pt"):
            if not par:
                skipped.append((tid, pos, "no particle at that position")); continue
            par[field] = val; applied.update([field]); continue
        # Unlabelled: particles carry the longer prose, so prefer the particle when one exists there.
        if par:
            par["explanation_pt"] = val; applied.update(["explanation_pt"])
        elif tok:
            tok["conjugation_note_pt" if "forma" in val or "eufônica" in val else "gloss_pt"] = val
            applied.update(["token(unlabelled)"])
        else:
            skipped.append((tid, pos, "no token or particle at that position"))

    if args.apply:
        for p, d in files.items():
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"review apply ({'APPLIED' if args.apply else 'dry-run'}): {sum(applied.values())} "
          f"{dict(applied)}")
    for t, p, w in skipped[:8]:
        print(f"   skip {t}@{p}: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
