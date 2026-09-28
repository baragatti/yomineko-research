#!/usr/bin/env python3
"""Hard gate (W46): every published particle carries a valid usage id, and its explanation is the template.

WHY
---
Particle meaning used to be free text only (4,970 distinct pt-BR labels; に alone had 833 English
ones), so no exercise could ask "every に of time" and no validator could check an explanation.
W46 attached a usage id from the closed enum of design/particle_functions.json to every occurrence
and RENDERED the explanation from the usage's template (the authored text moved to `note`). This gate
re-proves that on the export, with the same renderer that wrote it (scripts/particle_usage_render.py).

CHECKS (corpus/sentences/bank.json)
-----------------------------------
U0  floors: >= 5,000 sentences and >= 20,000 particles (a truncated bank must not pass by being small)
U1  every particle has `usage` in the enum, or is HELD: usage null, usage_status "held", and its
    (slug, token_position) is in research/derived/repairs/particle_usage.json `held`; the bank's held
    count equals the table's
U2  class == usages[usage].class, usage_label == usages[usage].label, usage_status in auto|verified|ruled
U3  the usage is spelled by the particle: its surface, or a contiguous token span containing it
    (ては = て + は; lex.fixed matches any surface)
U4  compounds: `positions` is the token span that spells the compound and contains the particle
U5  slots re-derive from the tokens: chunk, left, a compound's expression; a lex.fixed expression is
    grounded in the sentence (a prefix of it covers the particle in jp)
U6  explanation == the template rendered from usage + slots, in every locale (pt-BR, en)
U7  tokens: function / aux_function / chunk_role are null or ids of design/token_roles.json
Reads the export, the two design files and the repair table. Usage: validate_particle_usage.py [--root PATH] [--list N]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from particle_usage_render import (LOCALES, TEMPLATE_SLOTS, chunk_slot, expression_grounded, forms,  # noqa: E402
                                   left_slot, load_enum, render, span_spelling, surface_matches)

REPO_ROOT = Path(__file__).resolve().parents[2]
FLOOR_SENTENCES = 5000
FLOOR_PARTICLES = 20000
STATUSES = {"auto", "verified", "ruled"}


def check(root: Path) -> tuple[list[tuple[str, str, str]], Counter]:
    enum = load_enum(root)
    U = enum["usages"]
    tr = json.loads((root / "design" / "token_roles.json").read_text(encoding="utf-8"))
    tenum = {"function": {x["id"] for x in tr["token_functions"]}, "aux_function": {x["id"] for x in tr["aux_functions"]},
             "chunk_role": {x["id"] for x in tr["chunk_roles"]}}
    table = json.loads((root / "research" / "derived" / "repairs" / "particle_usage.json").read_text(encoding="utf-8"))
    held_rows = {(h["slug"], h["position"]) for h in table["held"]}
    bank = json.loads((root / "corpus" / "sentences" / "bank.json").read_text(encoding="utf-8"))
    recs = bank["records"] if isinstance(bank, dict) else bank
    fails: list[tuple[str, str, str]] = []
    n: Counter = Counter()
    if len(recs) < FLOOR_SENTENCES:
        fails.append(("U0", "bank", f"{len(recs)} sentences < floor {FLOOR_SENTENCES}"))
    for s in recs:
        slug = s.get("slug", "?")
        toks = s.get("tokens") or []
        for t in toks:
            for f, ids in tenum.items():
                if t.get(f) is not None and t[f] not in ids:
                    fails.append(("U7", slug, f"token {t.get('position')} {f} {t[f]!r} not in design/token_roles.json"))
            n["tokens:chunk_role"] += t.get("chunk_role") is not None
        for k, p in enumerate(s.get("particles") or []):
            n["particles"] += 1
            i, usage, surf = p.get("token_position"), p.get("usage"), p.get("particle")
            addr = f"particles[{k}] {surf!r} @{i}"
            if not isinstance(i, int) or not 0 <= i < len(toks) or toks[i].get("surface") != surf:
                fails.append(("U1", slug, f"{addr}: not anchored to its token"))
                continue
            if usage is None:
                n["held"] += 1
                if p.get("usage_status") != "held" or (slug, i) not in held_rows:
                    fails.append(("U1", slug, f"{addr}: no usage and not a held row of the table"))
                continue
            if usage not in U:
                fails.append(("U1", slug, f"{addr}: usage {usage!r} is not in the enum"))
                continue
            u = U[usage]
            n[f"usage:{usage}"] += 1
            if p.get("class") != u["class"] or p.get("usage_label") != u["label"] or p.get("usage_status") not in STATUSES:
                fails.append(("U2", slug, f"{addr}: class/label/status {p.get('class')!r}/{p.get('usage_label')!r}/"
                                          f"{p.get('usage_status')!r} disagree with {usage}"))
            if not surface_matches(toks, i, u):
                fails.append(("U3", slug, f"{addr}: {usage} is not spelled by the particle"))
                continue
            if u["compound"]:
                span = span_spelling(toks, i, forms(u))
                if p.get("positions") != span:
                    fails.append(("U4", slug, f"{addr}: positions {p.get('positions')!r}, the compound spans {span!r}"))
            elif "positions" in p:
                fails.append(("U4", slug, f"{addr}: positions on a non-compound usage"))
            need = set(enum["templates"][u["template"]]["slots"]) & TEMPLATE_SLOTS
            if set(p) & TEMPLATE_SLOTS != need:
                fails.append(("U5", slug, f"{addr}: slots {sorted(set(p) & TEMPLATE_SLOTS)}, template needs {sorted(need)}"))
                continue
            want = {"chunk": chunk_slot(toks, i) if "chunk" in need else None,
                    "left": left_slot(toks, i) if "left" in need else None}
            for slot in ("chunk", "left"):
                if slot in need and p[slot] != want[slot]:
                    fails.append(("U5", slug, f"{addr}: {slot} {p[slot]!r}, the tokens give {want[slot]!r}"))
            if "expression" in need:
                e = p["expression"]
                if u["compound"]:
                    span = span_spelling(toks, i, forms(u)) or []
                    if e != "".join(toks[j]["surface"] for j in span):
                        fails.append(("U5", slug, f"{addr}: expression {e!r} is not the compound's span"))
                elif not isinstance(e, str) or not expression_grounded(toks, i, e):
                    fails.append(("U5", slug, f"{addr}: expression {e!r} is not grounded in the sentence"))
            rendered = render(enum, usage, surf, {k: p[k] for k in need})
            ex = p.get("explanation") or {}
            for loc in LOCALES:
                if ex.get(loc) != rendered[loc]:
                    fails.append(("U6", slug, f"{addr}: explanation[{loc}] {ex.get(loc)!r} != {rendered[loc]!r}"))
    if n["particles"] < FLOOR_PARTICLES:
        fails.append(("U0", "bank", f"{n['particles']} particles < floor {FLOOR_PARTICLES}"))
    if n["held"] != len(table["held"]):
        fails.append(("U1", "bank", f"{n['held']} held particles in the bank, the table holds {len(table['held'])}"))
    return fails, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--list", type=int, default=10)
    a = ap.parse_args()
    fails, n = check(a.root)
    usages = sum(v for k, v in n.items() if k.startswith("usage:"))
    print(f"validate_particle_usage: {n['particles']} particles, {usages} with a usage "
          f"({sum(1 for k in n if k.startswith('usage:'))} distinct ids), {n['held']} held; "
          f"{n['tokens:chunk_role']} tokens with a chunk_role")
    by: Counter = Counter(c for c, _, _ in fails)
    for c in sorted(by):
        print(f"  [FAIL] {c}: {by[c]}")
    for c, slug, m in fails[:a.list]:
        print(f"    {c} {slug}: {m}")
    if fails:
        return 1
    print("  [OK ] U0-U7: every particle carries a valid usage id and its explanation is the rendered template")
    return 0


if __name__ == "__main__":
    sys.exit(main())
