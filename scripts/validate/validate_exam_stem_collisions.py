#!/usr/bin/env python3
"""Two exam items may not print the SAME stem and key DIFFERENT answers.

WHY THIS EXISTS (readiness finding G12, research/reports/readiness/exams_simulations.md)
----------------------------------------------------------------------------------------
`validate_exam_banks.py` checks that an item's options are distinct *within* that item. Nothing
checked contradiction *across* items, and the banks ship it: `n3_orthography` asks いし and keys
医師 in one item, 意志 in another and 意思 in a third; n4 asks たずねる and keys both 尋ねる and
訪ねる; n5 asks 得る and keys both うる and える. Each such pair is unanswerable in principle, and
when two members of a group land in one paper the learner is marked wrong on an answer that is
right. The readiness audit called it "92 items ... would have been caught at build time by a
five-line check".

WHAT IS COMPARED
----------------
Scope is the **bank file** — one (level, section) pair, which is the pool a single paper draws from,
and the scope the readiness audit measured. Items are grouped by their normalized `stem`; a group
holding two or more distinct normalized `correct` values is a collision, and every item in it counts.

  normalize = NFKC  ->  the answer blank （　） collapses to one sentinel ␣ (so a blank in a
              different POSITION stays a different printed stem — this is a stem-identity check, not
              a bag-of-characters check)  ->  strip every Unicode punctuation / separator / control
              character (categories P*, Z*, C*), which is what "same printed stem" means once
              spacing and 、。（） are normalized away.

Only items that carry both `stem` and `correct` are in scope: 4,469 of the 6,048 items, i.e. every
kanji_reading / orthography / context_fill / grammar_form / paraphrase / usage item. `reading_comp`
and `text_grammar` carry a `question` instead, and that field is deliberately NOT compared — the
same question text ("この人は何をしましたか") over two different passages is not a contradiction,
because the question is not self-contained the way a stem is. `sentence_order` and the listening
types carry `pieces`/`script`, likewise not a printed stem. Bank files with no in-scope item are
reported, so the scope is visible rather than assumed.

MEASURED COUNT vs THE AUDIT'S 92
--------------------------------
This validator measures **94** collision items in 46 groups over the 2026-09-02 export. The
readiness audit prints 92, but its own per-bank breakdown in that row sums to 88, and the two
figures cannot both be right; the per-bank table below is reproducible from the files, so the
baseline is frozen at what the files actually hold, not at the prose figure.

RATCHET
-------
Known content debt, held without hiding it (`scripts/validate/README.md`): the per-bank counts are
frozen in research/reports/exam_stem_collision_baseline.json. **Any bank growing past its frozen
count FAILS**, so the debt cannot move sideways from one bank to another; a bank that shrinks is
printed with the new number so the baseline gets lowered. W17/W18 (bank regeneration) is the work
that retires it: the rebuild has to beat this number rather than re-argue it.

Empty input fails: no bank directory, fewer bank files than the floor, or fewer in-scope items than
the floor is a FAIL, not a pass over nothing.

Usage: validate_exam_stem_collisions.py [--root PATH] [--list] [--write-baseline]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BANK_GLOB = "corpus/exam_banks/*.json"
# a dict of withdrawn items, not a bank; validate_exam_banks.py owns it
NOT_A_BANK = {"removed_items.json"}
BASELINE_REL = "research/reports/exam_stem_collision_baseline.json"
MAX_SHOWN = 12
# Floors far below the live counts (40 banks / 4,469 in-scope items) — growth never trips them, a
# vanished, renamed or sidecar-shadowed directory does.
MIN_BANKS = 30
MIN_ITEMS = 3000
BLANK = "␣"  # ␣ — the sentinel the answer blank collapses to


def normalize(text: str) -> str:
    """NFKC, answer blank -> one sentinel, then drop punctuation / separators / controls."""
    s = unicodedata.normalize("NFKC", str(text))
    out: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == "(":  # NFKC has already folded （ to ( and 　 to a space
            j = i + 1
            while j < len(s) and s[j] in " _　  \t":
                j += 1
            if j < len(s) and s[j] == ")" and j > i + 1:
                out.append(BLANK)
                i = j + 1
                continue
        out.append(s[i])
        i += 1
    return "".join(c for c in out
                   if c == BLANK or not unicodedata.category(c)[0] in "PZC")


def load_banks(root: Path) -> tuple[list[Path], dict[str, list[dict]]]:
    """bank file -> its in-scope items (those printing a stem and keying an answer)."""
    banks = [p for p in sorted(root.glob(BANK_GLOB)) if p.name not in NOT_A_BANK]
    scoped: dict[str, list[dict]] = {}
    for path in banks:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else []
        scoped[path.name] = [r for r in rows if r.get("stem") and r.get("correct") is not None]
    return banks, scoped


def collisions(scoped: dict[str, list[dict]]) -> dict[str, list[tuple[str, list[tuple[str, str]]]]]:
    """bank -> [(normalized stem, [(item id, normalized key)…])] for every contradictory group."""
    out: dict[str, list[tuple[str, list[tuple[str, str]]]]] = {}
    for bank, rows in scoped.items():
        groups: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
        for r in rows:
            groups[normalize(r["stem"])].append((r.get("id", "<no id>"), normalize(r["correct"])))
        bad = [(stem, members) for stem, members in sorted(groups.items())
               if len({key for _, key in members}) > 1]
        if bad:
            out[bank] = bad
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="tree to validate (default: repo root)")
    ap.add_argument("--list", action="store_true", help="print every colliding group, not the first 12")
    ap.add_argument("--write-baseline", action="store_true",
                    help=f"re-freeze {BASELINE_REL} from this tree")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    fails: list[str] = []

    banks, scoped = load_banks(root)
    n_items = sum(len(v) for v in scoped.values())
    if len(banks) < MIN_BANKS:
        print(f"FAIL: {len(banks)} exam bank files under {root}/corpus/exam_banks "
              f"(floor {MIN_BANKS}) — the banks are missing, moved or shadowed")
        return 1
    if n_items < MIN_ITEMS:
        print(f"FAIL: {n_items} items carry a stem and a key (floor {MIN_ITEMS}) — "
              "nothing to compare, so nothing would ever be caught")
        return 1
    empty = sorted(b for b, v in scoped.items() if not v)
    print(f"exam stem collisions: {len(banks)} banks, {n_items} items with a printed stem and a key "
          f"({len(empty)} banks carry no stem-shaped item: "
          f"{', '.join(b.replace('.json', '') for b in empty) or 'none'})")

    found = collisions(scoped)
    per_bank = {bank: sum(len(m) for _, m in groups) for bank, groups in sorted(found.items())}
    total = sum(per_bank.values())
    n_groups = sum(len(g) for g in found.values())
    print(f"  {total} items in {n_groups} contradictory groups over {len(per_bank)} banks")

    shown = 0
    for bank, groups in sorted(found.items()):
        for stem, members in groups:
            if not args.list and shown >= MAX_SHOWN:
                break
            keys = ", ".join(f"{i}->{k}" for i, k in sorted(members))
            print(f"    {bank.replace('.json', ''):22} «{stem}» :: {keys}")
            shown += 1
    if not args.list and n_groups > shown:
        print(f"    … {n_groups - shown} more groups (--list for all)")

    # ---- ratchet ---------------------------------------------------------------------------------
    bp = root / BASELINE_REL
    if args.write_baseline:
        bp.parent.mkdir(parents=True, exist_ok=True)
        bp.write_text(json.dumps({
            "why": "Frozen ceiling for exam items that print the same stem and key different answers "
                   "(readiness finding G12). These are known CONTENT defects awaiting the bank "
                   "regeneration (APP_PLAN W17/W18), not passing checks: "
                   "validate_exam_stem_collisions.py fails when any bank exceeds its count here, and "
                   "prints the new number when one drops so the baseline can be lowered. Scope is one "
                   "bank file = one (level, section); normalization is NFKC + answer-blank sentinel + "
                   "punctuation/separator/control stripping.",
            "total": total, "per_bank": per_bank,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {BASELINE_REL} (frozen at {total} items over {len(per_bank)} banks)")
        return 0
    if not bp.exists():
        print(f"FAIL: {BASELINE_REL} missing — re-freeze it with --write-baseline")
        return 1
    base = json.loads(bp.read_text(encoding="utf-8"))
    frozen: dict[str, int] = base.get("per_bank", {})
    if not frozen and base.get("total"):
        fails.append(f"{BASELINE_REL}: per_bank is empty but total={base.get('total')} — stale baseline")
    for bank, n in sorted(per_bank.items()):
        was = frozen.get(bank)
        if was is None:
            fails.append(f"{bank}: {n} colliding items and no frozen count — a NEW contradicting bank")
        elif n > was:
            fails.append(f"{bank}: {n} colliding items, frozen at {was} — the ratchet may only shrink")
    drops = [f"{b} {frozen[b]}->{per_bank.get(b, 0)}" for b in sorted(frozen)
             if per_bank.get(b, 0) < frozen[b]]
    if base.get("total") is not None and total != base["total"]:
        print(f"  baseline total {base['total']} -> measured {total}")
    if drops:
        print(f"  RATCHET SHRANK: {'; '.join(drops)} — lower it with --write-baseline")

    for f in fails:
        print(f"  FAIL {f}")
    print(f"=== exam stem collisions: {len(fails)} FAIL "
          f"({total} held at the baseline's {base.get('total')}) ===")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
