#!/usr/bin/env python3
"""Apply the verified Layer-A pairing decisions: unlink or re-link a sentence's English.

Origin of this queue. A reviewer wanted to CREATE or change English translations on records whose
Japanese came from Tatoeba or JEC. Those ops were blocked, correctly: writing fluent English into a
Layer-A source slot launders AI output as authoritative data, which is the worst defect class this
project has. The real underlying defect is a MISMATCHED PAIRING — the wrong upstream translation row got
linked to the Japanese.

Two rounds of verification then established something worth stating plainly: **ingestion linked nothing
wrong**. All 54 stored `jp` are byte-exact upstream, all 54 stored `en` are byte-exact with an English
row genuinely linked to that same source row. The drift is in the UPSTREAM Tatoeba and JEC translation
quality, not in anything we did. That is why most of these are flags rather than repairs.

NO ENGLISH IS AUTHORED HERE. There are exactly three actions:
  unlink-en           the stored English does not correspond to the Japanese and no better row exists,
                      so the pairing is removed. A sentence with no English is not a defect.
  relink-en:<id>      an existing upstream row is a genuine match; its VERBATIM text replaces the
                      current one. The row id comes from the queue and this script re-verifies that the
                      row exists AND is linked to the same Japanese source id before using it. Relinking
                      to a row that belongs to a different sentence would be worse than the defect.
  flag-link-quality   the pairing is authentic but loose. Recorded, never edited: a loose Tatoeba
                      pairing is not a defect, and rewriting it would be exactly the blocked op.

Usage: apply_layer_a_pairing.py [--apply]
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
# W01: honour --db / $YOMINEKO_DB so a rebuild can target a scratch DB (scripts/dbtarget.py).
import sys as _sys, pathlib as _pl  # noqa: E402
_sys.path.append(str(next(p for p in _pl.Path(__file__).resolve().parents if p.name == "scripts")))
from dbtarget import db_target  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "research" / "derived" / "qa_queues" / "round3" / "layer_a_pairing_verified.json"
DB = db_target(ROOT / "db" / "corpus.sqlite")
REPORT = ROOT / "research" / "derived" / "layer_a_link_quality.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    rows = [r for r in json.loads(SRC.read_text(encoding="utf-8"))["rows"] if r["verdict"] == "fix"]
    con = sqlite3.connect(DB)
    applied, skipped, flagged = Counter(), [], []

    for r in rows:
        slug = r["id"]
        action = r.get("endorsed_action") or ""
        row = con.execute("SELECT id,en FROM sentence WHERE slug=?", (slug,)).fetchone()
        if not row:
            skipped.append((slug, "unknown sentence")); continue
        sid, stored_en = row
        if (stored_en or "") != (r.get("current_en") or ""):
            skipped.append((slug, "stored en does not match the anchor")); continue

        if action == "unlink-en":
            if args.apply:
                con.execute("UPDATE sentence SET en=NULL, pt_validated_against='dict' WHERE id=?", (sid,))
            applied.update(["unlink"])

        elif action.startswith("relink-en:"):
            tid = action.split(":", 1)[1].strip()
            # The Japanese source id is embedded in the slug: sent:tatoeba-<jp_id>.
            jp_id = slug.rsplit("-", 1)[1]
            hit = con.execute("SELECT text FROM raw_tatoeba_translation WHERE trans_id=? AND jp_id=? "
                              "AND lang='eng'", (tid, jp_id)).fetchone()
            if not hit:
                # Guard: relinking to a row that belongs to another sentence is worse than the defect.
                skipped.append((slug, f"translation {tid} is not linked to jp_id {jp_id}")); continue
            if args.apply:
                con.execute("UPDATE sentence SET en=? WHERE id=?", (hit[0], sid))
            applied.update(["relink"])

        elif action == "flag-link-quality":
            flagged.append({"slug": slug, "jp": r.get("jp"), "en": r.get("current_en"),
                            "pt": r.get("current_pt"), "why": r.get("why")})
            applied.update(["flagged"])
        else:
            skipped.append((slug, f"unmapped action {action!r}"))

    if args.apply:
        con.commit()
    REPORT.write_text(json.dumps(
        {"note": "Pairings that are AUTHENTIC but loose. Verified byte-exact against the upstream "
                 "dataset: ingestion linked nothing wrong, the drift is upstream Tatoeba/JEC "
                 "translation quality. Recorded, never edited - rewriting the English here would be "
                 "the very op that was blocked.",
         "count": len(flagged), "sentences": flagged}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"layer-A pairing ({'APPLIED' if args.apply else 'dry-run'}): {dict(applied)}")
    print(f"link-quality flags recorded: {len(flagged)} -> {REPORT.relative_to(ROOT)}")
    for k, w in skipped:
        print(f"   skip {k}: {w}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
