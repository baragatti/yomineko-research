#!/usr/bin/env python3
"""Prep the needs_human manual items for resolution agents (STATE runbook step 5).

Emits research/derived/fable5_validation/phase3_manual_resolve/<key>.json batches, each item carrying the
FULL current DB record of its sentence (jp, kana, romaji, en/pt, literals, explanations, C-mode tokens with
readings/glosses/roles/notes) plus every pending finding for that sentence. Agents resolve per SENTENCE,
not per field, because reading fixes cascade (kana/romaji/expl/tokens must stay consistent).

Only `needs_human` items from phase3_manual_triage.json are included; the 145 split_mode false positives
are excluded (no action) and the 42 whitespace-token defects are handled mechanically elsewhere.

Usage: fable5_manual_prep.py [--per-batch 6]
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from collections import defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FD = ROOT / "research" / "derived" / "fable5_validation"
OUT = FD / "phase3_manual_resolve"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-batch", type=int, default=6)
    args = ap.parse_args()

    triage = json.loads((FD / "phase3_manual_triage.json").read_text(encoding="utf-8"))["items"]
    want = {(t["slug"], t["field"]) for t in triage if t["verdict"] == "needs_human"}
    patch = json.loads((FD / "phase3_sentences_patch.json").read_text(encoding="utf-8"))
    manual = [m for m in patch["manual"] if (m["slug"], m["field"]) in want]

    con = sqlite3.connect(db_target(ROOT / "db" / "corpus.sqlite"))
    by_slug = defaultdict(list)
    for m in manual:
        by_slug[m["slug"]].append(m)

    items = []
    for slug, ms in sorted(by_slug.items()):
        row = con.execute(
            "SELECT id, jp, kana, romaji, level, COALESCE(ai_generated,0) FROM sentence WHERE slug=?",
            (slug,)).fetchone()
        if not row:
            continue
        sid, jp, kana, romaji, level, gen = row
        texts = {}
        for field, locale, value in con.execute(
                "SELECT field, locale, value FROM localized_text WHERE entity_type='sentence' AND entity_id=?",
                (sid,)):
            texts.setdefault(field, {})[locale] = value
        toks = []
        for i, (tid, surf, read, rom, role, gloss, note) in enumerate(con.execute(
                "SELECT id, surface, reading, romaji, role_pt, gloss_pt, conjugation_note_pt FROM token "
                "WHERE sentence_id=? AND split_mode='C' ORDER BY position, id", (sid,))):
            loc = {}
            for field, locale, value in con.execute(
                    "SELECT field, locale, value FROM localized_text WHERE entity_type='token' AND "
                    "entity_id=?", (tid,)):
                loc.setdefault(field, {})[locale] = value
            toks.append({"i": i, "s": surf, "r": read, "romaji": rom, "role_pt": role,
                         "gloss_pt": gloss, "note_pt": note, "localized": loc})
        items.append({
            "slug": slug, "jp": jp, "kana": kana, "romaji": romaji, "level": level,
            "gen": bool(gen), "texts": texts, "tokens_C": toks,
            "findings": [{"field": m["field"], "reason": m["reason"],
                          "severity": m["finding"].get("severity"),
                          "issue": m["finding"].get("issue"),
                          "current": m["finding"].get("current"),
                          "proposed": m.get("fix") or m["finding"].get("fix")
                          or m["finding"].get("suggested"),
                          "detail": m.get("detail")} for m in ms],
        })
    con.close()

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()
    keys = []
    for n in range(0, len(items), args.per_batch):
        key = f"m{n // args.per_batch:02d}"
        (OUT / f"{key}.json").write_text(
            json.dumps({"items": items[n:n + args.per_batch]}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        keys.append(key)
    print(f"needs_human findings: {len(manual)} over {len(items)} sentences -> {len(keys)} batches")
    print(json.dumps(keys))
    return 0


if __name__ == "__main__":
    sys.exit(main())
