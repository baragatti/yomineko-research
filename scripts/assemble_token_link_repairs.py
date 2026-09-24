#!/usr/bin/env python3
"""Q2 — fold the verified token-link audit into ONE tracked repair table.

INPUTS (research/derived/token_links/, moved out of pending/ when applied; the verdicts stay in
pending/; all already verified, nothing here is authored)
  token_link_audit.json               4,004 rows: relink 3,262 / unlink 212 / review 530
  token_link_mechanical_sample.json   the 250-row sample of the mechanical rows; its
                                      `exclude_patterns` name every row the census found wrong and
                                      say what to do instead (`apply_instead`)
  token_link_rulings-{0..5}.json      the 530 review rows ruled from the sentence's meaning
  token_link_rulings-{0..5}.verdict.json  one independent verifier per batch; `corrected` wins

WHAT A ROW BECOMES
  mechanical relink/unlink  -> applied as the audit wrote it, unless its key is in an
                               exclude pattern; then the pattern's `apply_instead` decides
                               (drop, unlink, or relink to the named record)
  review                    -> the ruling's `new_vocab`, or the verifier's corrected value.
                               A ruling equal to the old link is a KEEP and emits no row; null is
                               an unlink.
  The sample's `upgrade_candidates` (unlinks the registry could relink) are NOT taken: they were
  named by the sample reader but never put to a verifier, so they stay unlinks (listed in the
  report as open).

Verdicts are keyed by the row's stable identity (`sentence#position`), never by batch index. A
ruling with no verdict is EXCLUDED (a dead verifier never passes a row).

OUTPUT research/derived/repairs/token_link_repairs.json, applied by
scripts/apply_token_link_repairs.py. Deterministic; re-running rewrites the same bytes.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parents[1]
PEND = ROOT / "research" / "derived" / "pending"          # the verdict files stay here
SRC = ROOT / "research" / "derived" / "token_links"      # the applied inputs, moved out of pending/
OUT = ROOT / "research" / "derived" / "repairs" / "token_link_repairs.json"

# apply_instead of research/derived/token_links/token_link_mechanical_sample.json, as data.
# key -> None (drop the row: keep the old link) | "unlink" | "vocab:<id>" (relink there)
REROUTE_BY_PATTERN = {
    "aux-sou-to-然う": "unlink",
    "yoru-drop-by": "vocab:1219680",
    "kakaru-disease": None,
    "karada-written-身体": None,
    "doushite-progressive": "unlink",
}
REROUTE_BY_KEY = {
    "sent:tatoeba-189506#3": "vocab:1444150",
    "sent:tatoeba-3507342#2": "vocab:1444150",
    "sent:tatoeba-229052#6": "vocab:1331530",
    "sent:tatoeba-10083431#4": "unlink",
    "sent:tatoeba-10917216#0": "unlink",
}


def key_of(r: dict) -> str:
    return f"{r['sentence']}#{r['position']}"


def main() -> int:
    audit = json.loads((SRC / "token_link_audit.json").read_text(encoding="utf-8"))
    sample = json.loads((SRC / "token_link_mechanical_sample.json").read_text(encoding="utf-8"))
    rows_in = audit["rows"]
    by_key = {key_of(r): r for r in rows_in}
    if len(by_key) != len(rows_in):
        raise SystemExit("audit: duplicate (sentence, position) keys")

    excluded: dict[str, str] = {}
    for pat in sample["exclude_patterns"]:
        for k in pat["keys"]:
            if k not in by_key:
                raise SystemExit(f"exclude pattern {pat['id']}: {k} is not an audit row")
            excluded[k] = pat["id"]

    rulings: dict[str, dict] = {}
    verdicts: dict[str, dict] = {}
    for i in range(6):
        rulings.update(json.loads((SRC / f"token_link_rulings-{i}.json").read_text(encoding="utf-8")))
        verdicts.update(json.loads((PEND / f"token_link_rulings-{i}.verdict.json").read_text(encoding="utf-8")))

    stats: Counter = Counter()
    rows: list[dict] = []
    for r in rows_in:
        k = key_of(r)
        base = {"sentence": r["sentence"], "position": r["position"], "surface": r["surface"],
                "old_vocab": r["old_vocab"], "class": r["class"]}
        ev = r.get("evidence") or {}
        if r["action"] in ("relink", "unlink"):
            new = r["new_vocab"] if r["action"] == "relink" else None
            origin = "audit:mechanical"
            if k in excluded:
                pat = excluded[k]
                inst = REROUTE_BY_KEY.get(k, REROUTE_BY_PATTERN.get(pat)) if pat != "census-singletons" \
                    else REROUTE_BY_KEY.get(k)
                if inst is None:
                    stats[f"dropped:{pat}"] += 1
                    continue
                new = None if inst == "unlink" else inst
                origin = f"audit:reroute:{pat}"
            stats[origin.split(":")[1] + (":" + ("unlink" if new is None else "relink"))] += 1
        else:
            ru = rulings.get(k)
            if ru is None:
                raise SystemExit(f"review row {k} has no ruling")
            vd = verdicts.get(k)
            if vd is None:
                stats["excluded:no-verdict"] += 1
                continue
            if vd.get("ok") is True:
                new, origin = ru["new_vocab"], "ruling"
            elif isinstance(vd.get("corrected"), dict) and "new_vocab" in vd["corrected"]:
                new, origin = vd["corrected"]["new_vocab"], "ruling:verifier-corrected"
            else:
                stats["excluded:rejected-no-correction"] += 1
                continue
            if new == r["old_vocab"]:
                stats[f"{origin}:keep"] += 1
                continue
            stats[f"{origin}:{'unlink' if new is None else 'relink'}"] += 1
        old_rec = ev.get("old_record") or {}
        rows.append(dict(base, new_vocab=new, action="unlink" if new is None else "relink",
                         origin=origin, old_headword=old_rec.get("headword"),
                         old_kana=old_rec.get("kana")))

    rows.sort(key=lambda x: (x["sentence"], x["position"]))
    doc = {
        "unit": "Q2-token-links",
        "what_this_is": "Every token link the token-link audit found contradicted by the sentence, with "
                        "the verified decision. One row per C-mode token, addressed by sentence SLUG "
                        "and token POSITION. Assembled by scripts/assemble_token_link_repairs.py from "
                        "research/derived/token_links/token_link_{audit,mechanical_sample,rulings-*}.json; "
                        "applied by scripts/apply_token_link_repairs.py.",
        "sources": {
            "audit": "research/derived/token_links/token_link_audit.json",
            "sample": "research/derived/token_links/token_link_mechanical_sample.json (exclude_patterns + apply_instead)",
            "rulings": "research/derived/token_links/token_link_rulings-{0..5}.json + research/derived/pending/token_link_rulings-{0..5}.verdict.json",
        },
        "rules": {
            "guard": "the token at (sentence, position) in split mode C must still carry old_vocab and "
                     "read `surface`, else the row is refused",
            "edges": "edge-exact: the new (sentence, vocab) pair is inserted; the old pair is deleted only "
                     "when no C token, no R2 run (n5/n4 registry), no R3 lemma (n3 headword) and no "
                     "ortho row still produces it",
            "levels": "`sentence_levels`: the touched sentences whose computed level the relink moves "
                      "(persist_dissection.computed_level, pre- vs post-relink edges over the corrected "
                      "registry) get the new level; scoped, never corpus-wide",
        },
        "counts": dict(sorted(stats.items())),
        "row_count": len(rows),
        "rows": rows,
    }
    # The reading-box half (`reading_uses`) and the re-level half (`sentence_levels`) were derived
    # once, from the passages' own SudachiPy tokens and from the index before and after the relink;
    # neither can be re-derived from the applied tree, so a re-assembly carries them forward verbatim.
    if OUT.is_file():
        prior = json.loads(OUT.read_text(encoding="utf-8"))
        for k in ("reading_uses_rule", "reading_uses", "sentence_levels_rule", "sentence_levels"):
            if k in prior:
                doc[k] = prior[k]
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"assemble_token_link_repairs: {len(rows)} rows -> {OUT.relative_to(ROOT)}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
