#!/usr/bin/env python3
"""Split the resolved manual queue into APPLY-READY vs RE-DISSECTION, and fold the ready set into the patch.

Why the split: the resolver's edit vocabulary deliberately excludes `tokens[i].s`, because changing a
token surface is a re-tokenization, not a field edit. So any resolution that rewrites `jp` cannot also
repair the token array, and applying it would break the HARD invariant concat(C-token surfaces) == jp and
leave every token position, role and gloss describing text that is no longer there. Adversarial verifiers
caught several of these; this script catches ALL of them mechanically, and quarantines the WHOLE sentence
(not just the jp edit) because the resolver rewrote that sentence's explanations to describe the new jp.

Outputs (research/derived/fable5_validation/):
  phase3_manual_apply.json      — apply-ready sentences, ops in the same shape as the auto patch
  phase3_redissect_queue.json   — jp re-authors + verifier-rejected, for a later SudachiPy re-dissection pass
Usage: fable5_manual_finalize.py
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"

TOKEN_PATH = re.compile(r"^tokens\[(\d+)\]\.(r|romaji|role|gloss|note)(?:\.(en|pt-BR))?$")
SENT_PATH = re.compile(r"^(jp|kana|romaji)$")
TEXT_PATH = re.compile(r"^(translation|translation_literal|structure_explanation)\.(en|pt-BR)$")


# resolver attr name -> DB/auto-patch attr name (the auto patch is the canonical op vocabulary)
TOKEN_ATTR = {"r": "reading", "romaji": "romaji", "role": "role",
              "gloss": "gloss", "note": "conjugation_note"}


def to_op(path: str, new: str):
    """Translate a resolver path string into an op in the AUTO-PATCH path vocabulary, or None."""
    m = SENT_PATH.match(path)
    if m:
        return {"mode": "replace", "path": [m.group(1)], "fix": new, "field": path}
    m = TEXT_PATH.match(path)
    if m:
        return {"mode": "replace", "path": [m.group(1), m.group(2)], "fix": new, "field": path}
    m = TOKEN_PATH.match(path)
    if m:
        idx, attr, loc = int(m.group(1)), TOKEN_ATTR[m.group(2)], m.group(3)
        if attr in ("reading", "romaji"):
            return {"mode": "replace", "path": ["tokens", idx, attr], "fix": new, "field": path}
        if not loc:
            return None  # localized attrs must name a locale
        return {"mode": "replace", "path": ["tokens", idx, attr, loc], "fix": new, "field": path}
    return None


def main() -> int:
    data = json.loads((FD / "phase3_manual_resolutions.json").read_text(encoding="utf-8"))
    accepted = data["accepted"]
    rejected = {s["slug"]: b["reason"]
                for k, v in data["verifier_rejected"].items() for b in v for s in [{"slug": b["slug"]}]}

    apply_ready, redissect, unsupported = [], [], []
    for s in accepted:
        paths = [e["path"] for e in s["edits"]]
        if any(p == "jp" for p in paths):
            redissect.append({"slug": s["slug"], "why": "jp re-author: needs re-dissection (token surfaces "
                                                        "are not field-editable)",
                              "decisions": s["decisions"], "proposed_edits": s["edits"]})
            continue
        ops, bad = [], []
        for e in s["edits"]:
            op = to_op(e["path"], e["new"])
            (ops if op else bad).append(op or e)
        if bad:
            unsupported.append({"slug": s["slug"], "paths": [b["path"] for b in bad]})
            continue
        if ops:
            apply_ready.append({"slug": s["slug"], "ops": ops, "source": "manual_resolution",
                                "decisions": s["decisions"]})

    for slug, reason in rejected.items():
        redissect.append({"slug": slug, "why": f"verifier rejected: {reason[:300]}"})

    (FD / "phase3_manual_apply.json").write_text(
        json.dumps({"note": "Verifier-clean manual resolutions with no jp change; ops match the auto-patch "
                            "shape and are safe to apply as field edits.",
                    "sentences": apply_ready}, ensure_ascii=False, indent=1), encoding="utf-8")
    (FD / "phase3_redissect_queue.json").write_text(
        json.dumps({"note": "Sentences that CANNOT be fixed by field edits: a jp re-author requires a new "
                            "token array (re-run the SudachiPy dissection), and verifier-rejected "
                            "resolutions need a fresh pass. Deferred - not part of this apply.",
                    "sentences": redissect}, ensure_ascii=False, indent=1), encoding="utf-8")

    n_ops = sum(len(s["ops"]) for s in apply_ready)
    n_jp = sum(1 for r in redissect if r["why"].startswith("jp re-author"))
    print(f"apply-ready: {len(apply_ready)} sentences / {n_ops} ops")
    print(f"re-dissection queue: {len(redissect)} sentences "
          f"({n_jp} jp re-authors, {len(rejected)} verifier-rejected)")
    if unsupported:
        print(f"UNSUPPORTED paths (dropped): {unsupported}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
