#!/usr/bin/env python3
"""Capability-registry gate: ids unique; every grammar key mapped to EXACTLY ONE capability; every capability
key exists in grammar_point; lesson_map lessons + capability refs resolve. Exit 1 on failure.

W24 checks (plant-proved in research/reports/w24_apply_report.md):
  (a) `kind` present and in the design enum (build_capabilities.KINDS, design/courseware_architecture.md)
  (b) `can_do['pt-BR']` non-empty with no em dash, `can_do_evidence` in {recognition, production}
  (c) every `can_do_derived_from` lesson resolves, is one of the capability's own `lessons`, and its
      `objective` is VERBATIM one of that lesson's pt-BR objectives
  (d) EVERY lesson is a key of lesson_map.json (what retired corpus/capabilities/exemptions.json), and
      `lessons` is exactly the inverse of lesson_map
  (e) each `exam_link` row names an existing bank file for its (level, section), a section the paper
      table of design/exam_simulator.md knows, `via: paper` only on exam-readiness with a non-zero
      paper count, and items > 0"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402
_sys.path.append(str(Path(__file__).resolve().parents[1] / "export"))
from build_capabilities import EVIDENCE, KINDS, lesson_objectives, paper_spec  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAPD = ROOT / "corpus" / "capabilities"


def w24_checks(reg: list, lmap: dict, lslugs: set, objectives: dict, paper: dict) -> list[str]:
    fails = []
    inverse: dict[str, set] = {}
    for slug, caps in lmap.items():
        for cp in caps:
            inverse.setdefault(cp, set()).add(slug)
    for c in reg:
        cid = c["id"]
        if c.get("kind") not in KINDS:                                              # (a)
            fails.append(f"{cid}: kind {c.get('kind')!r} not in {list(KINDS)}")
        text = (c.get("can_do") or {}).get("pt-BR")                                 # (b)
        if not isinstance(text, str) or not text.strip() or "—" in text:
            fails.append(f"{cid}: can_do['pt-BR'] missing, blank or carrying an em dash")
        if c.get("can_do_evidence") not in EVIDENCE:
            fails.append(f"{cid}: can_do_evidence {c.get('can_do_evidence')!r} not in {list(EVIDENCE)}")
        own = set(c.get("lessons") or [])
        for q in c.get("can_do_derived_from") or []:                                # (c)
            les = q.get("lesson")
            if les not in lslugs:
                fails.append(f"{cid}: can_do quotes unknown lesson {les}")
            elif les not in own:
                fails.append(f"{cid}: can_do quotes {les}, which the capability does not claim")
            elif q.get("objective") not in objectives.get(les, []):
                fails.append(f"{cid}: {les} has no objective {q.get('objective')!r} (not verbatim)")
        if own != inverse.get(cid, set()):                                          # (d)
            fails.append(f"{cid}: lessons[] is not the inverse of lesson_map")
        for e in c.get("exam_link") or []:                                          # (e)
            lvl, sec = e.get("level"), e.get("section")
            bank = f"corpus/exam_banks/{lvl}_{sec}.json"
            if sec not in paper:
                fails.append(f"{cid}: exam_link section {sec!r} is not in the paper table")
            elif e.get("bank") != bank or not (ROOT / bank).exists():
                fails.append(f"{cid}: exam_link bank {e.get('bank')!r} does not exist for {lvl} {sec}")
            elif e.get("via") == "paper" and (c.get("kind") != "exam-readiness"
                                              or paper[sec].get(lvl, 0) <= 0):
                fails.append(f"{cid}: via=paper on {lvl} {sec} but not an exam-readiness paper section")
            elif e.get("via") not in ("paper", "item-provenance") or not (e.get("items") or 0) > 0:
                fails.append(f"{cid}: exam_link row {lvl} {sec} has via {e.get('via')!r} / items "
                             f"{e.get('items')!r}")
    missing = sorted(lslugs - set(lmap))                                            # (d)
    if missing:
        fails.append(f"{len(missing)} lesson(s) map to no capability: {missing[:5]}")
    return fails


def main() -> int:
    if not (CAPD / "registry.json").exists():
        print("validate_capabilities: no registry (skip)")
        return 0
    reg = json.loads((CAPD / "registry.json").read_text(encoding="utf-8"))
    lmap = json.loads((CAPD / "lesson_map.json").read_text(encoding="utf-8"))
    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    # A merged loser keeps its row as a redirect (deprecated_by = survivor, W08) and is not
    # an active point: no capability should map it, and the survivor carries its coverage.
    cols = {r[1] for r in con.execute("PRAGMA table_info(grammar_point)")}
    where = " WHERE deprecated_by IS NULL" if "deprecated_by" in cols else ""
    gkeys = {r[0] for r in con.execute("SELECT key FROM grammar_point" + where)}
    lslugs = {r[0] for r in con.execute("SELECT slug FROM lesson")}
    fails = []
    ids = [c["id"] for c in reg]
    if len(ids) != len(set(ids)):
        fails.append("duplicate capability ids")
    seen: dict = {}
    for c in reg:
        for k in c["grammar_keys"]:
            if k not in gkeys:
                fails.append(f"{c['id']}: unknown grammar key {k}")
            if k in seen:
                fails.append(f"grammar key {k} in two capabilities: {seen[k]} + {c['id']}")
            seen[k] = c["id"]
    unmapped = gkeys - set(seen)
    if unmapped:
        fails.append(f"{len(unmapped)} grammar keys unmapped: {sorted(unmapped)[:6]}")
    idset = set(ids)
    for slug, caps in lmap.items():
        if slug not in lslugs:
            fails.append(f"lesson_map: unknown lesson {slug}")
        for cp in caps:
            if cp not in idset:
                fails.append(f"lesson_map {slug}: unknown capability {cp}")
    fails += w24_checks(reg, lmap, lslugs, lesson_objectives(con),
                        paper_spec(ROOT / "design" / "exam_simulator.md"))
    con.close()
    for f in fails[:10]:
        print("  FAIL", f)
    print(f"\nvalidate_capabilities: {len(reg)} caps, {len(lmap)} lessons, "
          f"{'FAIL ' + str(len(fails)) if fails else 'ALL OK'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
