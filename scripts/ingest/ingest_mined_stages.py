#!/usr/bin/env python3
"""Ingest the verified mined Tatoeba sentences into the bank. Step 3 of the thin-stage fix.

Pipeline recap, so this script's place is unambiguous:
  1. scripts/ingest/mine_tatoeba_stages.py   selected 360 real candidates (Layer A, verbatim)
  2. an authoring + two-reviewer workflow    produced pt-BR for them -> research/derived/mined_pt/
  3. THIS SCRIPT                             dissects and persists the accepted ones
  4. build_speaking_path -> build_speaking_checkpoints -> build_speaking_practice, then re-export

Nothing here authors Japanese or English. The `jp` is copied byte-for-byte from raw_tatoeba_sentence and
the `en` is Tatoeba's own pairing, both Layer A. Only the pt-BR is ours, and it is Layer B.

Persistence goes through persist_dissection.persist(), which already runs the Dissector, writes the
token/particle/graph rows, honours the content blocklist and is idempotent by slug. That matters: this
script must be safe to re-run after a partial failure, and it must not become a second, divergent way of
writing sentences into the corpus.

Guards before anything is written, because a bad ingest is expensive to unpick:
  * the jp must match the raw Tatoeba row for that id EXACTLY (catches an authoring agent having
    "tidied" Layer-A Japanese, which the reviewers were told to treat as critical);
  * the slug must not already exist (idempotency is persist()'s job, but a collision is worth reporting);
  * rows the authors rejected are skipped;
  * after each insert the three structural invariants are re-checked against what was actually stored --
    I1 concat(C-token surfaces) == jp, I2 kana == concat(token readings), I3 romaji == concat(token
    romaji) -- and ANY violation rolls the whole transaction back. The Phase-3 repair learned this the
    hard way: a partially-applied batch is worse than none.

Usage: ingest_mined_stages.py [--apply]   (default is a dry run)

DRY-RUN CAVEAT, found the hard way on the first run: persist_dissection.persist() COMMITS internally, so
wrapping it in BEGIN/rollback here does not undo anything. The first "dry run" of this script wrote all
324 rows. The check below is therefore a PRE-FLIGHT: without --apply it validates every record and
reports what would happen, and refuses to call persist() at all. The invariant re-check still runs on
--apply and still aborts the remainder of the batch, but it cannot un-write rows already committed by an
earlier persist() call, so the pre-flight is what protects the corpus, not the rollback.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "db" / "corpus.sqlite"
SRC = ROOT / "research" / "derived" / "mined_pt" / "_accepted.json"


def invariants(con: sqlite3.Connection, sid: int) -> list[str]:
    """Re-read what was stored and check it against itself. Phrasing-proof: these are structural."""
    row = con.execute("SELECT jp,kana,romaji FROM sentence WHERE id=?", (sid,)).fetchone()
    if not row:
        return ["sentence row missing after insert"]
    jp, kana, romaji = row
    toks = con.execute("SELECT surface,reading,romaji FROM token WHERE sentence_id=? AND "
                       "split_mode='C' ORDER BY position", (sid,)).fetchall()
    bad = []
    if "".join(t[0] or "" for t in toks) != jp:
        bad.append("I1 concat(C surfaces) != jp")
    if "".join(t[1] or "" for t in toks) != (kana or ""):
        bad.append("I2 kana != concat(readings)")
    if "".join(t[2] or "" for t in toks) != (romaji or ""):
        bad.append("I3 romaji != concat(token romaji)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write; default is dry-run")
    args = ap.parse_args()
    if not SRC.exists():
        print(f"missing {SRC.relative_to(ROOT)} — run the authoring workflow first")
        return 1
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if not r.get("reject")]
    print(f"{len(rows)} accepted rows to ingest")

    from dissect import Dissector
    from persist_dissection import persist

    # Layer-B dissection content, authored and reviewed separately. Every bank sentence is
    # dissection_tier "full", which validate.py reads as a promise of a gloss on every content token, an
    # explanation on every particle, and a structure paragraph. Ingesting without these is what produced
    # 2,756 validator errors on the first trial run.
    layerb: dict[int, dict] = {}
    for f in sorted((ROOT / "research" / "derived" / "mined_layerb").glob("batch-*.json")):
        for s2 in json.loads(f.read_text(encoding="utf-8")).get("sentences", []):
            layerb[s2["tatoeba_id"]] = s2
    print(f"{len(layerb)} sentences carry authored Layer-B dissection content")
    con = sqlite3.connect(DB)
    raw = {i: t for i, t in con.execute("SELECT id,text FROM raw_tatoeba_sentence")}
    have = {s for s, in con.execute("SELECT slug FROM sentence")}
    diss = Dissector(DB)

    stats, problems = Counter(), []
    con.execute("BEGIN")
    for r in rows:
        tid, jp = r["tatoeba_id"], r["jp"]
        slug = f"sent:tatoeba-{tid}"
        if raw.get(tid) != jp:
            # The Japanese is Layer A. If it does not match the source row byte-for-byte, someone
            # edited it, and we drop rather than ingest a silently-altered original.
            problems.append((slug, "jp does not match the raw Tatoeba row"))
            stats["jp-altered"] += 1
            continue
        if slug in have:
            stats["already-banked"] += 1
            continue
        lb = layerb.get(tid, {})
        # The English anchor is Layer A and belongs to the jp id, so read it from the source of truth
        # rather than trusting it to survive the authoring round-trip. The pt-BR authoring schema
        # ({tatoeba_id, jp, pt, pt_literal, register, reject, reject_reason}) has no `en` key, so
        # `r.get("en")` silently returned None for all 324 rows of the first run and every one landed
        # with no anchor -- see research/reports/en_anchor_backfill.md.
        anchor = r.get("en") or (con.execute(
            "SELECT text FROM raw_tatoeba_translation WHERE jp_id=? AND lang='eng' "
            "ORDER BY trans_id LIMIT 1", (tid,)).fetchone() or (None,))[0]
        rec = {
            "slug": slug, "jp": jp, "en": anchor,
            "pt": r.get("pt"), "pt_literal": r.get("pt_literal"),
            "structure_explanation_pt": lb.get("structure_explanation_pt"),
            # persist() keys these by token/particle POSITION, so they must be dicts, not lists.
            "tokens": {t["position"]: t for t in lb.get("tokens", [])},
            "particles": {q["position"]: q for q in lb.get("particles", [])},
            "jp_source": "tatoeba", "ai_generated": 0,
            "tags": ["mined", f"stage:{r.get('stage', '')}"],
            "translation_confidence": 0.8,
        }
        if not args.apply:
            # Pre-flight only. persist() commits internally, so calling it here would WRITE — which is
            # exactly what the first run of this script did while claiming to be a dry run.
            stats["would-ingest"] += 1
            continue
        try:
            sid = persist(con, diss, rec)
        except Exception as e:                       # noqa: BLE001 - one bad row must not kill the run
            problems.append((slug, f"persist failed: {e}"))
            stats["persist-error"] += 1
            continue
        if sid == -1:
            stats["content-blocklisted"] += 1
            continue
        bad = invariants(con, sid)
        if bad:
            problems.append((slug, "; ".join(bad)))
            stats["invariant-violation"] += 1
            continue
        stats["ingested"] += 1

    if stats["invariant-violation"] or stats["jp-altered"]:
        con.rollback()
        print("ROLLED BACK — refusing a partial ingest:")
        for s, w in problems[:20]:
            print(f"   {s}: {w}")
        print(f"   totals {dict(stats)}")
        return 1
    if args.apply:
        con.commit()
    else:
        con.rollback()
    print(f"ingest ({'APPLIED' if args.apply else 'dry-run, rolled back'}): {dict(stats)}")
    for s, w in problems[:10]:
        print(f"   note {s}: {w}")
    print("next: export_corpus.py, then build_speaking_path -> _checkpoints -> _practice, then "
          "validate_all.py")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
