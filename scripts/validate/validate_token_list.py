#!/usr/bin/env python3
"""Hard gate (W45): the published token list IS the sentence.

WHY
---
`corpus/sentences/bank.json` used to flatten the dissector's mode-A sub-units into `tokens[]` ahead of
the mode-C tokens, so the word-by-word panel showed いく / つ / お / いくつ / です / か for おいくつですか？
(903 of 10,271 sentences). validate_display_consistency.py check 1 proved concat(C surfaces) == jp in
the DB, which always held; nothing checked the list consumers actually read. This does, on the export.
Research and plant design: research/reports/token_list_integrity.md §5.

CHECKS (every sentence of the bank)
-----------------------------------
T0  floor: >= 5,000 sentences (a truncated bank must not pass by being small)
T1  every sentence has >= 1 token
T2  tokens[i].position == i (swaps, drops, duplicates, interleaved sub-units)
T3  offsets tile jp: begin[0] == 0, end[i] == begin[i+1], end[last] == len(jp), jp[begin:end] == surface
    (code points; a non-BMP jp fails until a consumer needs one, because JS indexes UTF-16)
T4  every top-level token has split_mode == "C"
T5  parts[] (optional): >= 2, contiguous, cover the parent exactly, Layer-A keys only
T6  every particle has token_position in range and tokens[token_position].surface == particle

Reads the export only. Usage: validate_token_list.py [--root PATH] [--list N]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
REPO_ROOT = Path(__file__).resolve().parents[2]
FLOOR = 5000
PART_KEYS = {"surface", "lemma", "reading", "pos_coarse", "pos_fine", "begin", "end"}


def check_sentence(s: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    jp = s.get("jp") or ""
    toks = s.get("tokens") or []
    if not toks:
        return [("T1", "no tokens")]
    if any(ord(ch) > 0xFFFF for ch in jp):
        out.append(("T3", "jp has a character outside the BMP"))
    at = 0
    for i, t in enumerate(toks):
        if t.get("position") != i:
            out.append(("T2", f"tokens[{i}].position == {t.get('position')!r}"))
        if t.get("split_mode") != "C":
            out.append(("T4", f"tokens[{i}] split_mode {t.get('split_mode')!r}"))
        b, e, surf = t.get("begin"), t.get("end"), t.get("surface")
        if b != at or not isinstance(e, int) or not surf or jp[b:e] != surf:
            out.append(("T3", f"tokens[{i}] {surf!r} [{b},{e}) expected from {at}"))
        at = e if isinstance(e, int) else at
        if "parts" in t:
            parts = t["parts"] or []
            if len(parts) < 2:
                out.append(("T5", f"tokens[{i}] has {len(parts)} part(s)"))
            p_at = b
            for j, p in enumerate(parts):
                extra = set(p) - PART_KEYS
                if extra:
                    out.append(("T5", f"tokens[{i}].parts[{j}] carries {sorted(extra)}"))
                pb, pe, ps = p.get("begin"), p.get("end"), p.get("surface")
                if pb != p_at or not isinstance(pe, int) or not ps or jp[pb:pe] != ps:
                    out.append(("T5", f"tokens[{i}].parts[{j}] {ps!r} [{pb},{pe}) expected from {p_at}"))
                p_at = pe if isinstance(pe, int) else p_at
            if parts and p_at != e:
                out.append(("T5", f"tokens[{i}] parts end at {p_at}, parent at {e}"))
    if at != len(jp):
        out.append(("T3", f"tokens end at {at}, jp has {len(jp)}"))
    for k, p in enumerate(s.get("particles") or []):
        tp = p.get("token_position")
        if not isinstance(tp, int) or not 0 <= tp < len(toks):
            out.append(("T6", f"particles[{k}] {p.get('particle')!r} token_position {tp!r}"))
        elif toks[tp].get("surface") != p.get("particle"):
            out.append(("T6", f"particles[{k}] {p.get('particle')!r} anchored to {toks[tp].get('surface')!r}"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--list", type=int, default=10)
    a = ap.parse_args()
    bank = json.loads((a.root / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))
    recs = bank["records"] if isinstance(bank, dict) else bank
    fails: list[tuple[str, str, str]] = []
    if len(recs) < FLOOR:
        fails.append(("T0", "bank", f"{len(recs)} sentences < floor {FLOOR}"))
    for s in recs:
        fails += [(c, s.get("slug", "?"), m) for c, m in check_sentence(s)]
    by_check: dict[str, int] = {}
    for c, _, _ in fails:
        by_check[c] = by_check.get(c, 0) + 1
    print(f"validate_token_list: {len(recs)} sentences, {sum(len(s.get('tokens') or []) for s in recs)} tokens")
    for c in sorted(by_check):
        print(f"  [FAIL] {c}: {by_check[c]}")
    for c, slug, m in fails[:a.list]:
        print(f"    {c} {slug}: {m}")
    if fails:
        return 1
    print("  [OK ] T0-T6: every published token list reproduces its sentence exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
